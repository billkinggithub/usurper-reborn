#!/usr/bin/env python3
"""A window for editing a single-player save, with no build step and no dependencies.

    python Tests/Tools/save-editor-en.py            # normal use
    python Tests/Tools/save-editor-en.py --check    # list saves and field counts, open no window
    python Tests/Tools/save-editor-en.py --saves <dir>

The window covers more than the player object: every scalar in the save is reachable, with
first-class views for the player, the NPC roster, the companions and dungeon party, the world
state, the story systems and the settings. The section bar follows the in-game G editor's
categories (character, stats, economy, inventory, spells, companions, quests, story, family,
status, appearance, training, team, settings and world), and each section carries the same kind
of quick operation the G editor offers: clear inventory, learn or master spells, complete or
clear quests, grant seals or artifacts, cure diseases, reset daily counters and so on. Every
field carries an English label and a note
(curated, the game's own C# comment, or a direct gloss). A field keeps the type it already had,
so a level cannot become 5.5 and a gold total cannot lose its digits; a list can gain or lose an
element, and the companion and dungeon-party managers keep the flags and the id lists in step.

Saving copies the file it replaces to a timestamped backup first and renames its own temporary
file into place, so nothing is written halfway.

Close the game before saving: it holds the save open and rewrites it on autosave.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

GAME_PROJECT = "usurper-reloaded.csproj"

# Story companions are stored by numeric id in storySystems.companions and activeCompanionIds.
COMPANION_NAMES = {0: "Lyris", 1: "Aldric", 2: "Mira", 3: "Vex", 4: "Melodia"}
MAX_ACTIVE_COMPANIONS = 4
MAX_DUNGEON_PARTY = 4
ACTIVE_COMPANIONS_PATH = ("storySystems", "activeCompanionIds")
DUNGEON_PARTY_PATH = ("storySystems", "dungeonPartyNPCIds")

# Empty lists whose element type the schema pins down. Other empty lists may hold objects,
# so the editor will not offer to add a scalar to them.
EMPTY_SCALAR_LISTS = {
    ACTIVE_COMPANIONS_PATH: "int",
    DUNGEON_PARTY_PATH: "str",
    ("storySystems", "dungeonPartyPlayerNames"): "str",
    ("storySystems", "collectedFragments"): "int",
    ("storySystems", "experiencedMoments"): "int",
    ("storySystems", "oceanInsightIds"): "str",
    ("storySystems", "completedParadoxIds"): "str",
    ("storySystems", "collectedSeals"): "int",
    ("storySystems", "collectedArtifacts"): "int",
    ("storySystems", "completedEndings"): "int",
    ("storySystems", "oldGodsEncountered"): "int",
    ("player", "visitedSettlements"): "str",
    ("player", "settlementLoreRead"): "str",
    ("player", "wildernessDiscoveries"): "str",
    ("player", "discoveredFeatureIds"): "str",
    ("player", "mutedChannels"): "str",
}

# Fixed-size lists: an element cannot be added or removed without breaking the game's layout.
FIXED_LISTS = {
    ("player", "quickbar"),
    ("player", "teamXPPercent"),
    ("player", "phrases"),
    ("player", "description"),
}

# Lists that must keep the same length and order: an edit on one side has to be mirrored on the other.
PAIRED_LISTS = {
    ("player", "items"): ("player", "itemTypes"),
    ("player", "itemTypes"): ("player", "items"),
}

# The player fields worth reaching quickly. Everything is still searchable in "Player · All".
PLAYER_GROUPS: list[tuple[str, list[str]]] = [
    ("Basic", ["name1", "name2", "realName", "level", "experience", "class", "race", "sex",
              "age", "difficulty", "specialization"]),
    ("Attributes", ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma",
              "defence", "agility", "stamina", "baseStrength", "baseDexterity",
              "baseConstitution", "baseIntelligence", "baseWisdom", "baseCharisma",
              "baseDefence", "baseAgility", "baseStamina"]),
    ("Health & Mana", ["hp", "maxHP", "baseMaxHP", "mana", "maxMana", "baseMaxMana", "healing",
                    "healingPotions", "manaPotions", "antidotes", "poisonVials", "smokeBombs",
                    "poison", "poisonTurns", "fatigue"]),
    ("Money & Bank", ["gold", "bankGold", "bankLoan", "bankWage", "bankInterest",
                    "royalLoanAmount", "royalLoanDueDay", "loanAmount", "loanDaysRemaining",
                    "loanInterestAccrued"]),
    ("Combat", ["weapPow", "armPow", "bonusWeapPow", "bonusArmPow", "fights", "pFights",
              "tFights", "mKills", "mDefeats", "pKills", "pDefeats", "combatSpeed",
              "autoCombatHealPercent", "resurrections", "maxResurrections",
              "resurrectionsUsed", "playthroughDeaths"]),
    ("Fame & Alignment", ["fame", "chivalry", "darkness", "mental", "wantedLvl", "murderWeight",
                    "darkAlleyReputation", "loyalty", "haunt", "karma"]),
    ("Quests & Progress", ["quests", "royQuests", "turnsRemaining", "turnCount", "trainingPoints",
                    "currentLocation", "daysInPrison", "innerSanctumLastDay", "currentDay"]),
    ("Home", ["homeLevel", "chestLevel", "trainingRoomLevel", "gardenLevel", "bedLevel",
              "hearthLevel", "homeRestsToday", "herbsGatheredToday"]),
    ("Settings", ["language", "autoHeal", "screenReaderMode", "compactMode", "autoLook",
              "dungeonAutoMap", "autoLevelUp", "autoEquipDisabled", "colorTheme",
              "dateFormatPreference", "menuKeysNeedEnter", "webMenuKeysNeedEnter"]),
]

PLAYER_SETTING_KEYS = {key for _, keys in PLAYER_GROUPS for key in keys if key in {
    "language", "autoHeal", "screenReaderMode", "compactMode", "autoLook", "dungeonAutoMap",
    "autoLevelUp", "autoEquipDisabled", "colorTheme", "dateFormatPreference",
    "menuKeysNeedEnter", "webMenuKeysNeedEnter", "combatSpeed", "autoCombatHealPercent",
}}

PLAYER_PARTY_KEYS = {"team", "teamPassword", "isTeamLeader", "teamRec", "teammateStances",
                     "teammateDisabledAbilities", "teammateDisabledSpells",
                     "sharedPotionBelt", "autoRedistributeXP", "teamXPPercent",
                     "teamXPIsExplicit", "teamXPEvenSplit"}

# The sections follow the in-game G editor's category menu. Each is a filtered view over the
# same complete leaf list, so no field becomes unreachable; "All Fields" still lists everything.
CHAR_INFO_KEYS = {
    "name1", "name2", "realName", "class", "race", "sex", "age", "difficulty", "specialization",
    "chivalry", "darkness", "fame", "knighted", "isKnighted", "nobleTitle", "king", "isKing", "immortal",
    "isImmortal", "mental", "mentalSchema", "godFavor", "godFavorGod", "currentLocation",
}
STAT_KEYS = {
    "level", "experience", "strength", "dexterity", "constitution", "intelligence", "wisdom",
    "charisma", "defence", "agility", "stamina", "baseStrength", "baseDexterity",
    "baseConstitution", "baseIntelligence", "baseWisdom", "baseCharisma", "baseDefence",
    "baseAgility", "baseStamina", "hp", "maxHP", "baseMaxHP", "mana", "maxMana", "baseMaxMana",
    "resurrections", "maxResurrections", "resurrectionsUsed", "playthroughDeaths", "trains",
    "trainingPoints", "weapPow", "armPow", "bonusWeapPow", "bonusArmPow",
}
ECONOMY_KEYS = {
    "gold", "bankGold", "bankLoan", "bankWage", "bankInterest", "royalLoanAmount",
    "royalLoanDueDay", "loanAmount", "loanDaysRemaining", "loanInterestAccrued",
}
APPEARANCE_KEYS = {
    "height", "weight", "eyes", "hair", "skin", "phrases", "description",
}
TEAM_KEYS = {
    "team", "teamPassword", "isTeamLeader", "teamRec", "teammateStances",
    "teammateDisabledAbilities", "teammateDisabledSpells", "sharedPotionBelt",
    "autoRedistributeXP", "teamXPPercent", "teamXPIsExplicit", "teamXPEvenSplit",
}
STATUS_KEYS = {
    "hp", "maxHP", "mania", "mental", "blind", "plague", "smallpox", "measles", "leprosy",
    "loversBane", "poison", "poisonTurns", "gnollP", "addict", "steroidDays", "drugEffectDays",
    "activeDrug", "wantedLvl", "murderWeight", "daysInPrison", "isMurderConvict",
    "cellDoorOpen", "prisonEscapes", "divineWrathLevel", "divineWrathPending",
    "divineWrathTurnsRemaining", "angeredGodName", "betrayedForGodName", "fatigue",
    "groggoShadowBlessingDex", "artifactStatsApplied", "cycleStatBonusApplied",
    "voidreaverConstitutionApplied",
}
TRAINING_KEYS = {"trainingPoints", "trains"}
FAMILY_KEYS = {"kids", "divineWrathLevel", "kidsCount"}

SECTIONS = [
    ("Character Info", "char_info"),
    ("Stats & Progression", "stats"),
    ("Gold & Economy", "economy"),
    ("Inventory & Equipment", "inventory"),
    ("Spells & Abilities", "spells"),
    ("Companions", "companions"),
    ("Quests", "quests"),
    ("Story & Old Gods", "story"),
    ("Relationships & Family", "relationships"),
    ("Status & Cleanup", "status"),
    ("Appearance & Flavor", "appearance"),
    ("Skills & Training", "training"),
    ("Team & Guild", "team"),
    ("Settings", "settings"),
    ("World State", "world"),
    ("Player · All", "player_all"),
    ("All Fields", "all"),
]

# One English label per key name. The path is always shown too, so an unknown key stays usable.
LABELS = {
    'name': "Name",
    'name1': "Internal name",
    'name2': "Display name",
    'realName': "Real name",
    'level': "Level",
    'experience': "Experience",
    'class': "Class",
    'race': "Race",
    'sex': "Sex",
    'age': "Age",
    'difficulty': "Difficulty",
    'specialization': "Specialization",
    'archetype': "Archetype",
    'location': "Location",
    'team': "Team",
    'isTeamLeader': "Team leader",
    'teamPassword': "Team password",
    'gold': "Gold",
    'bankGold': "Bank gold",
    'bankLoan': "Bank loan",
    'bankWage': "Bank wage",
    'bankInterest': "Bank interest",
    'bankInterestRate': "Bank interest rate",
    'bankVaultReserve': "Bank vault reserve",
    'hp': "HP",
    'maxHP': "Max HP",
    'baseMaxHP': "Base max HP",
    'mana': "Mana",
    'maxMana': "Max mana",
    'baseMaxMana': "Base max mana",
    'strength': "Strength",
    'defence': "Defence",
    'agility': "Agility",
    'dexterity': "Dexterity",
    'charisma': "Charisma",
    'intelligence': "Intelligence",
    'wisdom': "Wisdom",
    'constitution': "Constitution",
    'stamina': "Stamina",
    'baseStrength': "Base strength",
    'baseDefence': "Base defence",
    'baseAgility': "Base agility",
    'baseDexterity': "Base dexterity",
    'baseConstitution': "Base constitution",
    'baseIntelligence': "Base intelligence",
    'baseWisdom': "Base wisdom",
    'baseCharisma': "Base charisma",
    'baseStamina': "Base stamina",
    'weapPow': "Weapon power",
    'armPow': "Armor power",
    'baseWeapPow': "Base weapon power",
    'baseArmPow': "Base armor power",
    'fame': "Fame",
    'chivalry': "Chivalry",
    'darkness': "Darkness",
    'mental': "Mental",
    'karma': "Karma",
    'loyalty': "Loyalty",
    'haunt': "Haunt",
    'wantedLvl': "Wanted level",
    'murderWeight': "Murder weight",
    'healing': "Healing",
    'healingPotions': "Healing potions",
    'manaPotions': "Mana potions",
    'antidotes': "Antidotes",
    'poisonVials': "Poison vials",
    'smokeBombs': "Smoke bombs",
    'poison': "Poison",
    'poisonTurns': "Poison turns",
    'fatigue': "Fatigue",
    'resurrections': "Resurrections",
    'maxResurrections': "Max resurrections",
    'resurrectionsUsed': "Resurrections used",
    'playthroughDeaths': "Deaths this playthrough",
    'trainingPoints': "Training points",
    'quests': "Quests",
    'royQuests': "Royal quests",
    'turnsRemaining': "Turns remaining",
    'turnCount': "Turn count",
    'daysInPrison': "Days in prison",
    'currentLocation': "Current location",
    'day': "Day",
    'currentDay': "Current day",
    'homeLevel': "Home level",
    'chestLevel': "Chest level",
    'trainingRoomLevel': "Training room level",
    'gardenLevel': "Garden level",
    'bedLevel': "Bed level",
    'hearthLevel': "Hearth level",
    'fights': "Fights",
    'pFights': "Player fights",
    'tFights': "Team fights",
    'mKills': "Monster kills",
    'mDefeats': "Monster defeats",
    'pKills': "Player kills",
    'pDefeats': "Player defeats",
    'combatSpeed': "Combat speed",
    'autoCombatHealPercent': "Auto-heal threshold",
    'language': "Language",
    'autoHeal': "Auto-heal",
    'screenReaderMode': "Screen reader",
    'compactMode': "Compact mode",
    'autoLook': "Auto-look",
    'dungeonAutoMap': "Dungeon automap",
    'autoLevelUp': "Auto level-up",
    'autoEquipDisabled': "Disable auto-equip",
    'colorTheme': "Color theme",
    'dateFormatPreference': "Date format",
    'menuKeysNeedEnter': "Menu keys need Enter",
    'webMenuKeysNeedEnter': "Web menu keys need Enter",
    'items': "Items",
    'inventory': "Inventory",
    'equippedItems': "Equipped items",
    'dynamicEquipment': "Dynamic equipment",
    'spells': "Spells",
    'skills': "Skills",
    'learnedAbilities': "Learned abilities",
    'quickbar': "Quickbar",
    'activeQuests': "Active quests",
    'achievements': "Achievements",
    'statistics': "Statistics",
    'personalityProfile': "Personality",
    'memories': "Memories",
    'relationships': "Relationships",
    'emotionalState': "Emotional state",
    'currentGoals': "Current goals",
    'enemies': "Enemies",
    'marketInventory': "Shop inventory",
    'skillProficiencies': "Skill proficiencies",
    'skillTrainingProgress': "Skill training progress",
    'craftingMaterials': "Crafting materials",
    'id': "ID",
    'characterID': "Character ID",
    'isDead': "Dead",
    'isPermaDead': "Permanently dead",
    'isMarried': "Married",
    'married': "Married",
    'spouseName': "Spouse",
    'npcFaction': "NPC faction",
    'worshippedGod': "Worshipped god",
    'isHostile': "Hostile",
    'isAIDriven': "AI-driven",
    'gangId': "Gang ID",
    'recentDialogueIds': "Recent dialogue",
    'knownCharacters': "Known characters",
    'motherName': "Mother",
    'fatherName': "Father",
    'isKing': "King",
    'isRecruited': "Recruited",
    'isActive': "Active",
    'loyaltyLevel': "Loyalty",
    'trustLevel': "Trust",
    'romanceLevel': "Romance",
    'personalQuestStarted': "Personal quest started",
    'personalQuestCompleted': "Personal quest completed",
    'recruitedDay': "Recruited on day",
    'companions': "Companions",
    'activeCompanionIds': "Active companion IDs",
    'fallenCompanions': "Fallen companions",
    'dungeonPartyNPCIds': "Dungeon party NPC IDs",
    'dungeonPartyPlayerNames': "Dungeon party player names",
    'activeGriefs': "Active griefs",
    'griefMemories': "Grief memories",
    'companionId': "Companion ID",
    'townPotValue': "Town pot",
    'currentRuler': "Current ruler",
    'activeEvents': "Active events",
    'shopInventories': "Shop inventories",
    'recentNews': "Recent news",
    'marketplaceListings': "Marketplace listings",
    'settlement': "Settlement",
    'usedNPCNames': "Used NPC names",
    'bankRobberiesToday': "Bank robberies today",
    'bankRobberiesDate': "Bank robbery date",
    'awakeningLevel': "Awakening level",
    'collectedFragments': "Collected fragments",
    'collectedSeals': "Collected seals",
    'collectedArtifacts': "Collected artifacts",
    'currentCycle': "Current cycle",
    'currentChapter': "Current chapter",
    'griefStage': "Grief stage",
    'griefDaysRemaining': "Grief days remaining",
    'griefCompanionName': "Grief companion",
    'oldGodStates': "Old God states",
    'oldGodsEncountered': "Old Gods encountered",
    'majorChoices': "Major choices",
    'playerGods': "Player gods",
    'children': "Children",
    'archetypeTracker': "Archetype tracker",
    'royalCourt': "Royal court",
    'factions': "Factions",
    'townNPCStories': "Town NPC stories",
    'dreams': "Dreams",
    'amnesia': "Amnesia",
    'betrayal': "Betrayal",
    'culturalMemes': "Cultural memes",
    'storyFlags': "Story flags",
    'storyFlagBits': "Story flag bits",
    'completedEndings': "Completed endings",
    'npcMarriages': "NPC marriages",
    'affairs': "Affairs",
    'kingName': "King name",
    'throneVacant': "Throne vacant",
    'treasury': "Treasury",
    'taxRate': "Tax rate",
    'kingTaxPercent': "King tax %",
    'cityTaxPercent': "City tax %",
    'courtMembers': "Court members",
    'heirs': "Heirs",
    'guards': "Guards",
    'prisoners': "Prisoners",
    'orphans': "Orphans",
    'activePlots': "Active plots",
    'coronationDate': "Coronation date",
    'founded': "Founded",
    'settlerNames': "Settlers",
    'communalTreasury': "Communal treasury",
    'playerContributions': "Player contributions",
    'buildingTiers': "Building tiers",
    'mode': "Mode",
    'lastResetTime': "Last reset",
    'autoSaveEnabled': "Autosave enabled",
    'autoSaveInterval': "Autosave interval",
    'version': "Save version",
    'saveTime': "Save time",
    'lastDailyReset': "Last daily reset",
    'dailyCycleMode': "Daily cycle mode",
    'player': "Player",
    'npCs': "NPC roster",
    'worldState': "World state",
    'settings': "Settings",
    'storySystems': "Story systems",
    'npcStates': "NPC states",
    'npcId': "NPC ID",
    'currentStage': "Current stage",
    'completedStages': "Completed stages",
    'choicesMade': "Choices made",
    'stageCompletedOnDay': "Stage completed on day",
    'accountCreated': "Account created",
    'lastLogin': "Last login",
    'lastLoginDate': "Last login date",
    'loginStreak': "Login streak",
    'longestLoginStreak': "Longest login streak",
    'gameTimeMinutes': "Game time (min)",
    'presentDays': "Present days",
    'agePlus': "Extra age",
    'bankGuard': "Bank guard",
    'bankRobberyAttempts': "Bank robbery attempts",
    'marryActions': "Marriage proposals",
    'wolfFeed': "Wolf feeds",
    'royalAdoptions': "Royal adoptions",
    'wrestlings': "Wrestlings",
    'gymSessions': "Gym sessions",
    'pickPocketAttempts': "Pickpocket attempts",
    'massage': "Massages",
    'umanBearTries': "Uman bear tries",
    'templeResurrectionsUsed': "Temple resurrections",
    'blessingsReceived': "Blessings received",
    'churchDonations': "Church donations",
    'sacrificesMade': "Sacrifices made",
    'healingsReceived': "Healings received",
    'hasHolyWater': "Has holy water",
    'bardSongsLeft': "Bard songs left",
    'daysInPower': "Days in power",
    'thievery': "Thievery",
    'taxRelief': "Tax relief",
    'royTaxPaid': "Royal tax paid",
    'kingVotePoll': "King vote poll",
    'kingLastVote': "Last king vote",
    'throneChallengedToday': "Throne challenged today",
    'totalExecutions': "Total executions",
    'executionsToday': "Executions today",
    'playerImprisonedToday': "Player imprisoned today",
    'npCsImprisonedToday': "NPCs imprisoned today",
    'kids': "Kid count",
    'disRes': "Dispute resolution",
    'weaponCursed': "Weapon cursed",
    'armorCursed': "Armor cursed",
    'shieldCursed': "Shield cursed",
    'king': "King",
    'teamRec': "Team record",
    'bGuard': "Door guard type",
    'bGuardNr': "Door guard count",
    'cityTaxEarnedThisWeek': "City tax this week",
    'cityTaxEarnedLifetime': "Lifetime city tax",
    'activeStatuses': "Active statuses",
    'gnollP': "Gnoll points",
    'addict': "Addiction",
    'steroidDays': "Steroid days",
    'drugEffectDays': "Drug effect days",
    'activeDrug': "Active drug",
    'mercy': "Mercy",
    'blind': "Blind",
    'plague': "Plague",
    'smallpox': "Smallpox",
    'measles': "Measles",
    'leprosy': "Leprosy",
    'loversBane': "Lover's Bane",
    'divineWrathLevel': "Divine wrath level",
    'angeredGodName': "Angered god",
    'betrayedForGodName': "Betrayed for god",
    'divineWrathPending': "Divine wrath pending",
    'divineWrathTurnsRemaining': "Divine wrath turns remaining",
    'royalLoanAmount': "Royal loan amount",
    'royalLoanDueDay': "Royal loan due day",
    'royalLoanBountyPosted': "Royal loan bounty posted",
    'nobleTitle': "Noble title",
    'isKnighted': "Knighted",
    'familySurname': "Family surname",
    'permakillLog': "Permakill log",
    'lastMurderWeightDecay': "Last murder-weight decay",
    'devMenuUsed': "Dev menu used",
    'skipIntimateScenes': "Skip intimate scenes",
    'disableCharacterMonsterArt': "Disable character/monster art",
    'classicMainStreet': "Classic Main Street",
    'districtsMainStreet': "Districts Main Street",
    'classicTipDraws': "Classic tip draws",
    'autoRedistributeXP': "Auto-redistribute XP",
    'teamXPPercent': "Team XP percent",
    'teamXPIsExplicit': "Explicit team XP",
    'teamXPEvenSplit': "Even team XP split",
    'master': "Master",
    'wellWish': "Well wish",
    'height': "Height",
    'weight': "Weight",
    'eyes': "Eyes",
    'hair': "Hair",
    'skin': "Skin",
    'phrases': "Phrases",
    'description': "Description",
    'romanceData': "Romance data",
    'achievementsData': "Achievement data",
    'trains': "Training sessions",
    'statTrainingCounts': "Stat training counts",
    'unpaidWageDays': "Unpaid wage days",
    'lHand': "Left hand",
    'rHand': "Right hand",
    'head': "Head",
    'body': "Body",
    'arms': "Arms",
    'lFinger': "Left finger",
    'rFinger': "Right finger",
    'legs': "Legs",
    'feet': "Feet",
    'waist': "Waist",
    'neck': "Neck",
    'neck2': "Neck 2",
    'face': "Face",
    'shield': "Shield",
    'hands': "Hands",
    'aBody': "Alternate body",
    'immortal': "Immortal",
    'battleCry': "Battle cry",
    'hasTrophyRoom': "Trophy room",
    'hasTeleportCircle': "Teleport circle",
    'hasLegendaryArmory': "Legendary armory",
    'hasVitalityFountain': "Vitality fountain",
    'hasStudy': "Study",
    'hasServants': "Servants",
    'hasReinforcedDoor': "Reinforced door",
    'homeRestsToday': "Home rests today",
    'herbsGatheredToday': "Herbs gathered today",
    'wellRestedCombats': "Well-rested combats",
    'wellRestedBonus': "Well-rested bonus",
    'loversBlissCombats': "Lover's bliss combats",
    'loversBlissBonus': "Lover's bliss bonus",
    'cycleExpMultiplier': "Cycle XP multiplier",
    'herbHealing': "Healing herb",
    'herbIronbark': "Ironbark",
    'herbFirebloom': "Firebloom",
    'herbSwiftthistle': "Swiftthistle",
    'herbStarbloom': "Starbloom",
    'herbBuffType': "Herb buff type",
    'herbBuffCombats': "Herb buff combats",
    'herbBuffValue': "Herb buff value",
    'herbExtraAttacks': "Herb extra attacks",
    'godSlayerCombats': "Godslayer combats",
    'godSlayerDamageBonus': "Godslayer damage bonus",
    'godSlayerDefenseBonus': "Godslayer defence bonus",
    'songBuffType': "Song buff type",
    'songBuffCombats': "Song buff combats",
    'songBuffValue': "Song buff value",
    'songBuffValue2': "Song buff value 2",
    'heardLoreSongs': "Lore songs heard",
    'foodBuffType': "Food buff type",
    'foodBuffCombats': "Food buff combats",
    'foodBuffValue': "Food buff value",
    'mealsToday': "Meals today",
    'innDuelsToday': "Inn duels today",
    'tavernStrangerTalkedToday': "Tavern stranger talked today",
    'visitedSettlements': "Visited settlements",
    'settlementLoreRead': "Settlement lore read",
    'wildernessExplorationsToday': "Wilderness explorations today",
    'wildernessRevisitsToday': "Wilderness revisits today",
    'wildernessDiscoveries': "Wilderness discoveries",
    'darkPactCombats': "Dark pact combats",
    'darkPactDamageBonus': "Dark pact damage bonus",
    'hasShatteredSealFragment': "Has shattered seal fragment",
    'hasTouchedTheVoid': "Has touched the Void",
    'settlementBuffType': "Settlement buff type",
    'settlementBuffCombats': "Settlement buff combats",
    'settlementBuffValue': "Settlement buff value",
    'smugglersCachePurchases': "Smuggler's cache purchases",
    'settlementGoldClaimedToday': "Settlement gold claimed today",
    'settlementHerbClaimedToday': "Settlement herb claimed today",
    'settlementShrineUsedToday': "Settlement shrine used today",
    'jailbreakAttemptedToday': "Jailbreak attempted today",
    'settlementCircleUsedToday': "Settlement circle used today",
    'settlementWorkshopUsedToday': "Settlement workshop used today",
    'workshopBuffCombats': "Workshop buff combats",
    'poisonCoatingCombats': "Poison coating combats",
    'activePoisonType': "Active poison type",
    'innerSanctumLastDay': "Last inner sanctum day",
    'lastDailyResetBoundary': "Last daily reset boundary",
    'lastPrayerRealDate': "Last prayer real date",
    'lastInnerSanctumRealDate': "Last inner sanctum real date",
    'lastBindingOfSoulsRealDate': "Last Binding of Souls real date",
    'sethFightsToday': "Seth fights today",
    'armWrestlesToday': "Arm wrestles today",
    'sethDefeatsTotal': "Seth defeats total",
    'royQuestsToday': "Royal quests today",
    'groggoShadowBlessingDex': "Groggo shadow blessing DEX",
    'timedStatBuffs': "Timed stat buffs",
    'artifactStatsApplied': "Artifact stats applied",
    'cycleStatBonusApplied': "Cycle stat bonus applied",
    'voidreaverConstitutionApplied': "Voidreaver constitution applied",
    'steroidShopPurchases': "Steroid shop purchases",
    'alchemistINTBoosts': "Alchemist INT boosts",
    'gamblingRoundsToday': "Gambling rounds today",
    'pitFightsToday': "Pit fights today",
    'desecrationsToday': "Desecrations today",
    'confessionsToday': "Confessions today",
    'murdersToday': "Murders today",
    'reforgesToday': "Reforges today",
    'sparesToday': "Spares today",
    'teamWarsToday': "Team wars today",
    'drinkingGamesToday': "Drinking games today",
    'loveStreetVisitsToday': "Love Street visits today",
    'intimateEncountersToday': "Intimate encounters today",
    'gauntletRunsToday': "Gauntlet runs today",
    'marshToadAntidoteClaimedToday': "Marsh toad antidote claimed today",
    'tributeDemandsToday': "Tribute demands today",
    'freeBlessingClaimedToday': "Free blessing claimed today",
    'mercContractsCompleted': "Merc contracts completed",
    'mercContractsClaimedToday': "Merc contracts claimed today",
    'lastMercBoardRefreshUtc': "Last merc board refresh",
    'dailyMercStandingGain': "Daily merc standing gain",
    'blackMarketStockSeed': "Black market stock seed",
    'lastBlackMarketRefreshUtc': "Last black market refresh",
    'blackMarketStock': "Black market stock",
    'almsGivenToday': "Alms given today",
    'orphanageGiftsToday': "Orphanage gifts today",
    'hospiceTithesToday': "Hospice tithes today",
    'lifetimeCharityGoldDonated': "Lifetime charity gold donated",
    'attunedShrineId': "Attuned shrine ID",
    'attunedShrineExpiresUtc': "Attuned shrine expires",
    'attunedShrineExpiresGameDay': "Attuned shrine expires game day",
    'shrineFavor': "Shrine favor",
    'discoveredFeatureIds': "Discovered features",
    'recognizedChildren': "Recognized children",
    'permadeathInheritanceClaimed': "Permadeath inheritance claimed",
    'completedFamilyArcs': "Completed family arcs",
    'completedArcChildNames': "Completed arc child names",
    'petRoster': "Pet roster",
    'activePetId': "Active pet ID",
    'lastPartnerBondingUtc': "Last partner bonding",
    'lastRiteOfReturnUtc': "Last Rite of Return",
    'dyingMessages': "Dying messages",
    'loanAmount': "Loan amount",
    'loanDaysRemaining': "Loan days remaining",
    'loanInterestAccrued': "Loan interest accrued",
    'darkAlleyReputation': "Dark alley reputation",
    'drugTolerance': "Drug tolerance",
    'safeHouseResting': "Safe house resting",
    'bloodMoonDay': "Blood moon day",
    'baseStatsHP': "Base HP",
    'baseStatsAttack': "Base attack",
    'baseStatsDefense': "Base defense",
    'baseStatsMagicPower': "Base magic power",
    'baseStatsSpeed': "Base speed",
    'baseStatsHealingPower': "Base healing power",
    'isAgedDeath': "Died of old age",
    'birthDate': "Birth date",
    'marriedTimes': "Marriages",
    'memoryTimesKept': "Memory times kept",
    'emergentRole': "Emergent role",
    'roleStabilityTicks': "Role stability ticks",
    'originalMotherName': "Original mother",
    'originalFatherName': "Original father",
    'soulAtGraduation': "Soul at graduation",
    'wasRaisedByPlayer': "Raised by player",
    'lastOnPlayerTeamAt': "Last on player team",
    'pregnancyDueDate': "Pregnancy due date",
    'pregnancyFatherName': "Pregnancy father",
    'equippedItemsSave': "Companion equipment",
    'disabledAbilities': "Disabled abilities",
    'disabledSpells': "Disabled spells",
    'personalQuestBeat': "Personal quest beat",
    'recruitedDate': "Recruited date",
    'experiencedMoments': "Experienced moments",
    'oceanInsightIds': "Ocean insight IDs",
    'completedParadoxIds': "Completed paradox IDs",
    'moralUtilitarianChoices': "Utilitarian choices",
    'moralDeontologicalChoices': "Deontological choices",
    'moralVirtueChoices': "Virtue choices",
    'moralNihilistChoices': "Nihilist choices",
    'activeNpcGriefs': "NPC griefs",
    'strangerEncounters': "Stranger encounters",
    'npcRelationship': "NPC relationship",
    'profiles': "Profiles",
    'records': "Records",
    'betrayalPoints': "Betrayal points",
    'isPendingBetrayal': "Pending betrayal",
    'triggerReason': "Trigger reason",
    'hasBetrayed': "Has betrayed",
    'wasForgiven': "Was forgiven",
    'betrayalDay': "Betrayal day",
    'warningShown': "Warning shown",
    'actsOfKindness': "Acts of kindness",
    'departedCompanionId': "Departed companion ID",
    'magicBudget': "Magic budget",
    'establishmentStatus': "Establishment status",
    'lastProclamation': "Last proclamation",
    'lastProclamationDate': "Last proclamation date",
    'monarchHistory': "Monarch history",
    'designatedHeir': "Designated heir",
    'kingAI': "King AI type",
    'kingSex': "King sex",
    'taxAlignment': "Tax alignment",
    'totalReign': "Total reign",
    'daysReigned': "Days reigned",
    'activeBuildingIndex': "Active building index",
    'buildingPools': "Building pools",
    'proposedBuildingTiers': "Proposed building tiers",
    'proposedBuildingPools': "Proposed building pools",
    'activeProposedBuildingId': "Active proposed building ID",
    'proposalCooldowns': "Proposal cooldowns",
    'contributionBoostTicks': "Contribution boost ticks",
    'activeProposalId': "Active proposal ID",
    'activeProposalProposer': "Proposer",
    'activeProposalTicksLeft': "Proposal ticks left",
    'activeProposalSupport': "Proposal support",
    'activeProposalOppose': "Proposal oppose",
    'activeProposalPlayerVotes': "Player votes",
    'experiencedDreams': "Experienced dreams",
    'seenDungeonVisions': "Seen dungeon visions",
    'restsSinceLastDream': "Rests since last dream",
    'recoveredMemories': "Recovered memories",
    'restCount': "Rest count",
    'truthRevealed': "Truth revealed",
    'activeMemes': "Active memes",
    'npcMemeAwareness': "NPC meme awareness",
    'locationMemeStrength': "Location meme strength",
    'unlockDates': "Unlock dates",
    'utcNow': "Current UTC time",
    'aggression': "Aggression",
    'greed': "Greed",
    'courage': "Courage",
    'vengefulness': "Vengefulness",
    'impulsiveness': "Impulsiveness",
    'sociability': "Sociability",
    'ambition': "Ambition",
    'trustworthiness': "Trustworthiness",
    'caution': "Caution",
    'mysticism': "Mysticism",
    'patience': "Patience",
    'romanticism': "Romanticism",
    'flirtatiousness': "Flirtatiousness",
    'passion': "Passion",
    'tenderness': "Tenderness",
    'happiness': "Happiness",
    'anger': "Anger",
    'fear': "Fear",
    'sadness': "Sadness",
    'joy': "Joy",
    'confidence': "Confidence",
    'loneliness': "Loneliness",
    'hope': "Hope",
    'peace': "Peace",
    'envy': "Envy",
    'pride': "Pride",
    'compassion': "Compassion",
    'honesty': "Honesty",
    'commitment': "Commitment",
    'receptivity': "Receptivity",
    'sensuality': "Sensuality",
    'adventurousness': "Adventurousness",
    'exhibitionism': "Exhibitionism",
    'voyeurism': "Voyeurism",
    'relationshipPref': "Relationship preference",
    'intimateStyle': "Intimate style",
    'handedness': "Handedness",
    'gender': "Gender",
    'currentLovers': "Current lovers",
    'exSpouses': "Ex-spouses",
    'exes': "Exes",
    'spouses': "Spouses",
    'family': "Family",
    'cuckArrangements': "Cuckold arrangements",
    'jealousyLevels': "Jealousy levels",
    'polyNetworks': "Poly networks",
    'currentProgress': "Current progress",
    'importance': "Importance",
    'emotionalImpact': "Emotional impact",
    'involvedCharacter': "Involved character",
    'targetCharacter': "Target character",
    'targetLocation': "Target location",
    'targetValue': "Target value",
    'createdTime': "Created time",
    'isCompleted': "Completed",
    'priority': "Priority",
    'recentGameEvents': "Recent game events",
    'conversationStates': "Conversation states",
    'responseHistory': "Response history",
    'topicsDiscussed': "Topics discussed",
    'lastConversationDate': "Last conversation date",
    'personalQuestionsAsked': "Personal questions asked",
    'flirtSuccessCount': "Flirt successes",
    'lastFlirtWasPositive': "Last flirt positive",
    'currentStreak': "Current streak",
    'longestStreak': "Longest streak",
    'longestSession': "Longest session",
    'totalPlayTime': "Total play time",
    'totalSessionsPlayed': "Total sessions played",
    'highestLevelReached': "Highest level reached",
    'highestGoldHeld': "Highest gold held",
    'deepestDungeonLevel': "Deepest dungeon level",
    'lastDungeonFloor': "Last dungeon floor",
    'totalDaysPlayed': "Total days played",
    'totalMonstersKilled': "Total monsters killed",
    'totalBossesKilled': "Total bosses killed",
    'totalCombatsWon': "Total combats won",
    'totalCombatsLost': "Total combats lost",
    'totalCombatsFled': "Total combats fled",
    'totalGoldEarned': "Total gold earned",
    'totalGoldSpent': "Total gold spent",
    'totalExperienceEarned': "Total experience earned",
    'totalDamageDealt': "Total damage dealt",
    'totalDamageTaken': "Total damage taken",
    'totalCriticalHits': "Total critical hits",
    'totalLevelUps': "Total level-ups",
    'totalItemsBought': "Total items bought",
    'totalItemsSold': "Total items sold",
    'totalHealingPotionsUsed': "Total healing potions used",
    'totalManaPotionsUsed': "Total mana potions used",
    'totalSpellsCast': "Total spells cast",
    'totalQuestsCompleted': "Total quests completed",
    'totalDeaths': "Total deaths",
    'totalTimesResurrected': "Total resurrections",
    'totalPlayerKills': "Total player kills",
    'totalRoomsExplored': "Total rooms explored",
    'totalChestsOpened': "Total chests opened",
    'totalTrapsDisarmed': "Total traps disarmed",
    'totalTrapsTriggered': "Total traps triggered",
    'totalSecretsFound': "Total secrets found",
    'totalNPCInteractions': "Total NPC interactions",
    'totalConversations': "Total conversations",
    'totalFriendsGained': "Total friends gained",
    'totalGiftsGiven': "Total gifts given",
    'totalRomances': "Total romances",
    'weaponPower': "Weapon power",
    'armorClass': "Armor class",
    'armorType': "Armor type",
    'weaponType': "Weapon type",
    'rarity': "Rarity",
    'isIdentified': "Identified",
    'isCursed': "Cursed",
    'isUnique': "Unique",
    'strengthRequired': "Strength required",
    'itemValue': "Item value",
    'itemName': "Item name",
    'itemType': "Item type",
    'slot': "Slot",
    'attack': "Attack",
    'defense': "Defense",
    'blockChance': "Block chance",
    'magicResistance': "Magic resistance",
    'hpRegen': "HP regen",
    'manaRegen': "Mana regen",
    'thorns': "Thorns",
    'lifeSteal': "Life steal",
    'manaSteal': "Mana steal",
    'armorPiercing': "Armor piercing",
    'criticalChanceBonus': "Critical chance bonus",
    'criticalDamageBonus': "Critical damage bonus",
    'bonusMaxHP': "Bonus max HP",
    'bonusWeapPow': "Bonus weapon power",
    'bonusArmPow': "Bonus armor power",
    'maxHPBonus': "Max HP bonus",
    'maxManaBonus': "Max mana bonus",
    'enchantBase': "Enchant base",
    'enchantMarkers': "Enchant markers",
    'hasFireEnchant': "Fire enchant",
    'hasFrostEnchant': "Frost enchant",
    'hasHolyEnchant': "Holy enchant",
    'hasLightningEnchant': "Lightning enchant",
    'hasPoisonEnchant': "Poison enchant",
    'hasShadowEnchant': "Shadow enchant",
    'hasTitanResolve': "Titan's Resolve",
    'status': "Status",
    'reward': "Reward",
    'rewardType': "Reward type",
    'penalty': "Penalty",
    'penaltyType': "Penalty type",
    'daysToComplete': "Days to complete",
    'minLevel': "Min level",
    'maxLevel': "Max level",
    'questType': "Quest type",
    'questTarget': "Quest target",
    'targetNPCName': "Target NPC",
    'isPlayerBounty': "Player bounty",
    'bountyGold': "Bounty gold",
    'objectives': "Objectives",
    'monsters': "Monsters",
    'isMercContract': "Merc contract",
    'issuingFaction': "Issuing faction",
    'mercContractTier': "Merc contract tier",
    'forced': "Forced",
    'offeredTo': "Offered to",
    'initiator': "Initiator",
    'occupier': "Occupier",
    'occupiedDays': "Occupied days",
    'startTime': "Start time",
    'endReason': "End reason",
    'createdOnGameDay': "Created on game day",
    'item': "Item",
    'seller': "Seller",
    'isNPCSeller': "NPC seller",
    'sellerNPCId': "Seller NPC ID",
    'price': "Price",
    'posted': "Posted",
    'titleKey': "Title key",
    'titleArgs': "Title args",
    'commentKey': "Comment key",
    'commentArgs': "Comment args",
    'descriptionKey': "Description key",
    'descriptionArgs': "Description args",
    'initiatorKey': "Initiator key",
    'actionsSinceLastEncounter': "Actions since last encounter",
    'agilityBonus': "Agility bonus",
    'ai': "AI",
    'arenaChampionTier': "Arena champion tier",
    'armHag': "Armor haggle",
    'armor': "Armor",
    'armorShopBarredUntilDay': "Armor shop barred until day",
    'artifactsCollected': "Artifacts collected",
    'ascensionDate': "Ascension date",
    'assa': "Assassinations",
    'bannedFromChurch': "Banned from church",
    'bannedMarry': "Banned from marriage",
    'betrayedFaction': "Betrayed faction",
    'bonusReward': "Bonus reward",
    'bossesDefeated': "Bosses defeated",
    'bountiesCompleted': "Bounties completed",
    'brawls': "Brawls",
    'cellDoorOpen': "Cell door open",
    'challengesCompleted': "Challenges completed",
    'characterCreated': "Character created",
    'charismaBonus': "Charisma bonus",
    'charitableActions': "Charitable actions",
    'chestContents': "Chest contents",
    'constitutionBonus': "Constitution bonus",
    'chivNr': "Chivalrous acts",
    'comment': "Comment",
    'companionsLost': "Companions lost",
    'companionsSaved': "Companions saved",
    'completionTime': "Completion time",
    'confessionAccepted': "Confession accepted",
    'count': "Count",
    'currentValue': "Current value",
    'cursed': "Cursed",
    'dailySalary': "Daily salary",
    'darkChoicesMade': "Dark choices made",
    'darkNr': "Dark acts",
    'daysAsRuler': "Days as ruler",
    'daysSinceDevotion': "Days since devotion",
    'daysSinceSpellCast': "Days since spell cast",
    'deathDate': "Death date",
    'deedsLeft': "Deeds left",
    'defenceBonus': "Defence bonus",
    'deleted': "Deleted",
    'dexterityBonus': "Dexterity bonus",
    'divineBlessingBonus': "Divine blessing bonus",
    'divineBlessingCombats': "Divine blessing combats",
    'divineBoonConfig': "Divine boon config",
    'divineDomain': "Divine domain",
    'divineName': "Divine name",
    'drinksLeft': "Drinks left",
    'dungeon': "Dungeon",
    'dungeonFloorsExplored': "Dungeon floors explored",
    'encountersHad': "Encounters had",
    'executeLeft': "Executions left",
    'experienceFromMonsters': "Experience from monsters",
    'experienceFromQuests': "Experience from quests",
    'experienceFromTraining': "Experience from training",
    'factionRank': "Faction rank",
    'factionReputation': "Faction reputation",
    'fatherID': "Father ID",
    'godAlignment': "God alignment",
    'godExperience': "God experience",
    'godFavor': "God favor",
    'godFavorGod': "Favor god",
    'godFavorSchema': "Favor schema",
    'godLevel': "God level",
    'godStandingPenaltyWeek': "God standing penalty week",
    'hasBetrayedFaction': "Betrayed faction before",
    'hasBossSlayer': "Has Boss Slayer",
    'hasConfessed': "Has confessed",
    'hasEarnedAltSlot': "Earned alt slot",
    'healingActionsTaken': "Healing actions",
    'highestSingleHit': "Highest single hit",
    'idTag1': "ID tag 1",
    'idTag2': "ID tag 2",
    'intelligenceBonus': "Intelligence bonus",
    'isBloodMoon': "Blood moon",
    'isImmortal': "Immortal",
    'isMurderConvict': "Murder convict",
    'isOptional': "Optional",
    'itemsCrafted': "Items crafted",
    'jealousy': "Jealousy",
    'jokesOrTricksMade': "Jokes or tricks",
    'killedBy1': "Killed by 1",
    'killedBy2': "Killed by 2",
    'knowledgeGained': "Knowledge gained",
    'lastDexterityTraining': "Last dexterity training",
    'lastGodSwitchDay': "Last god switch day",
    'lastPlayed': "Last played",
    'lastPlayerContactDay': "Last player contact day",
    'lastStrengthTraining': "Last strength training",
    'lastTugOfWar': "Last tug of war",
    'lastUpdated': "Last updated",
    'lastWrestling': "Last wrestling",
    'leadershipActions': "Leadership actions",
    'lootEffects': "Loot effects",
    'magicHag': "Magic haggle",
    'magicShopBarredUntilDay': "Magic shop barred until day",
    'marriagesFormed': "Marriages formed",
    'marriedDays': "Married days",
    'mentalBroken': "Mental collapse (Broken)",
    'mentalDrugBoost': "Mental drug boost",
    'mentalDrugUses': "Mental drug uses",
    'mentalHintShown': "Mental hint shown",
    'mentalLastDrugDay': "Last mental drug day",
    'mentalRecoveryUsedToday': "Mental recovery used today",
    'mentalSchema': "Mental schema",
    'mentalStrainRemainder': "Mental strain remainder",
    'mercifulChoices': "Merciful choices",
    'miracleUsedToday': "Miracle used today",
    'monsterName': "Monster name",
    'monsterType': "Monster type",
    'monstersKilled': "Monsters killed",
    'mostExpensivePurchase': "Most expensive purchase",
    'motherID': "Mother ID",
    'mudTitle': "MUD title",
    'neglectLetterSentDay': "Neglect letter sent day",
    'nightmareStartLevel': "Nightmare start level",
    'objectiveType': "Objective type",
    'orientation': "Orientation",
    'pendingGroupDeath': "Pending group death",
    'permanentDamageBonus': "Permanent damage bonus",
    'permanentDefenseBonus': "Permanent defense bonus",
    'personalQuestSuccess': "Personal quest success",
    'playerFaction': "Player faction",
    'playerKnowsTruth': "Player knows the truth",
    'playerSuspectsStranger': "Player suspects the stranger",
    'poisonDamage': "Poison damage",
    'previousWeeklyRank': "Previous weekly rank",
    'prisonActivitiesToday': "Prison activities today",
    'prisonEscapes': "Prison escapes",
    'prisonsLeft': "Prisons left",
    'progress': "Progress",
    'pvPDefeats': "PvP defeats",
    'pvPVictories': "PvP victories",
    'questsCompleted': "Quests completed",
    'questsLeft': "Quests left",
    'recurringDuelist': "Recurring duelist",
    'relation1': "Relation 1",
    'relation2': "Relation 2",
    'requiredProgress': "Required progress",
    'requiresEvil': "Requires evil",
    'requiresGood': "Requires good",
    'rescuedBy': "Rescued by",
    'rivalLevel': "Rival level",
    'rivalName': "Rival name",
    'romanceEncounters': "Romance encounters",
    'royalMercenaries': "Royal mercenaries",
    'rulesDefied': "Rules defied",
    'sealsCollected': "Seals collected",
    'secretsDiscovered': "Secrets discovered",
    'sharedPotionBelt': "Shared potion belt",
    'shieldBonus': "Shield bonus",
    'shop': "Shop",
    'spellsCast': "Spells cast",
    'spouse': "Spouse",
    'staminaBonus': "Stamina bonus",
    'strengthBonus': "Strength bonus",
    'targetFloor': "Target floor",
    'targetId': "Target ID",
    'targetName': "Target name",
    'teamActions': "Team actions",
    'thiefs': "Thefts",
    'timesRuler': "Times ruler",
    'timestamp': "Timestamp",
    'title': "Title",
    'totalAbilitiesUsed': "Total abilities used",
    'totalAccessoriesPurchased': "Total accessories purchased",
    'totalCursesBroken': "Total curses broken",
    'totalDeathSpellsCast': "Total death spells cast",
    'totalDiseasesContracted': "Total diseases contracted",
    'totalDiseasesCured': "Total diseases cured",
    'totalDungeonFloorsCovered': "Total dungeon floors covered",
    'totalEnchantmentsApplied': "Total enchantments applied",
    'totalEnemiesMade': "Total enemies made",
    'totalGamblingRounds': "Total gambling rounds",
    'totalGoldFromGambling': "Gold from gambling",
    'totalGoldFromMonsters': "Gold from monsters",
    'totalGoldFromQuests': "Gold from quests",
    'totalGoldFromSelling': "Gold from selling",
    'totalGoldLostGambling': "Gold lost gambling",
    'totalGoldLostToThieves': "Gold lost to thieves",
    'totalGoldStolen': "Gold stolen",
    'totalHealthRestored': "Total health restored",
    'totalLoveSpellsCast': "Total love spells cast",
    'totalMagicShopGoldSpent': "Magic shop gold spent",
    'totalManaRestored': "Total mana restored",
    'totalMonsterDeaths': "Total monster deaths",
    'totalMonstersEncountered': "Total monsters encountered",
    'totalPickpocketAttempts': "Total pickpocket attempts",
    'totalPickpocketSuccesses': "Total pickpocket successes",
    'totalPitFightsLost': "Pit fights lost",
    'totalPitFightsWon': "Pit fights won",
    'totalPlayerDeaths': "Total player deaths",
    'totalPoisonings': "Total poisonings",
    'totalTeamBattles': "Total team battles",
    'totalUniquesKilled': "Total uniques killed",
    'transformationsMade': "Transformations made",
    'trust': "Trust",
    'type': "Type",
    'value': "Value",
    'wealthAccumulated': "Wealth accumulated",
    'weapHag': "Weapon haggle",
    'weaponShopBarredUntilDay': "Weapon shop barred until day",
    'weeklyGod': "Weekly god",
    'weeklyGodWeek': "Weekly god week",
    'weeklyRank': "Weekly rank",
    'weightClass': "Weight class",
    'willowDraughts': "Willow Draughts",
    'wisdomBonus': "Wisdom bonus",
    'worldBossDamageDealt': "World boss damage dealt",
    'worldBossMVPCount': "World boss MVP count",
    'worldBossesKilled': "World bosses killed",
}

# A short English gloss for every field. Keys not listed here still get a generated
# "literal" note, and the C# save-model comments are added when available, so the editor
# never shows a field without an explanation.
TYPE_ZH = {"int": "Integer", "float": "Decimal", "bool": "Boolean", "str": "Text",
           "list": "List", "dict": "Object", "null": "Null"}

OLD_GOD_NAMES = {0: "Maelketh", 1: "Veloura", 2: "Thorgrim", 3: "Noctura",
                 4: "Aurelion", 5: "Terravok", 6: "Manwe"}

FIELD_NOTES = {
    'version': "Save format version; the game uses it to decide whether to migrate an old save. Usually leave it alone.",
    'saveTime': "When this save was written; used only for display and sorting.",
    'lastDailyReset': "Time of the last daily reset.",
    'currentDay': "Current game day; daily events, rent and bank interest are calculated from it.",
    'dailyCycleMode': "Enum value for the daily cycle mode.",
    'player': "The player object, holding the character's entire state.",
    'npCs': "The world's NPC roster; each entry is one NPC's complete save.",
    'worldState': "World state: bank, town pot, events, quests, marketplace and settlements.",
    'settings': "Autosave and daily-reset settings.",
    'storySystems': "Story and system state: awakening, seals, companions, Old Gods, factions, royal court, dreams and more.",
    'id': "Internal unique identifier referenced by teams, romance and family records; usually leave it alone.",
    'name1': "The player's internal name, usually the same as the display name.",
    'name2': "The player's display name; NPCs and the save list show this name.",
    'realName': "The true name used in the story; may be blank.",
    'level': "Current level. Raising it does not retroactively grant stat points, skills or equipment.",
    'experience': "Current experience; once enough for a level-up you can advance at the level master.",
    'class': "Class enum value; changing it does not recalculate stats already gained.",
    'race': "Race enum value.",
    'sex': "Sex text (M/F, etc.).",
    'age': "Character age.",
    'difficulty': "Difficulty (enum integer or level).",
    'specialization': "Class specialization enum value.",
    'currentLocation': "Current location code, for example Main Street.",
    'turnCount': "Game turns elapsed.",
    'turnsRemaining': "Action turns left today.",
    'gameTimeMinutes': "Minutes elapsed in game time.",
    'daysInPrison': "Remaining days in prison.",
    'resurrections': "Resurrections available.",
    'maxResurrections': "Maximum resurrections.",
    'resurrectionsUsed': "Resurrections already used.",
    'playthroughDeaths': "Deaths this playthrough.",
    'trainingPoints': "Available training points, spent at the level master.",
    'quests': "Number of quests completed.",
    'royQuests': "Number of royal quests completed.",
    'hp': "Current HP; on load it should not exceed max HP.",
    'maxHP': "Maximum HP; equipment, blessings and permanent bonuses add to it.",
    'mana': "Current mana.",
    'maxMana': "Maximum mana.",
    'stamina': "Stamina, used by some classes to cast abilities.",
    'healing': "Healing amount or a healing-related value.",
    'healingPotions': "Number of healing potions.",
    'manaPotions': "Number of mana potions.",
    'antidotes': "Number of antidotes.",
    'poisonVials': "Number of poison vials.",
    'smokeBombs': "Number of smoke bombs.",
    'gold': "Gold carried.",
    'bankGold': "Gold deposited in the bank.",
    'bankLoan': "Current bank loan.",
    'bankWage': "Bank wage/interest-related value.",
    'bankInterest': "Accumulated bank interest.",
    'bankGuard': "Whether a bank guard is hired.",
    'bankRobberyAttempts': "Number of attempted bank robberies.",
    'royalLoanAmount': "Amount owed to the crown.",
    'royalLoanDueDay': "Game day the royal loan is due.",
    'royalLoanBountyPosted': "Whether the crown has posted a bounty for this loan.",
    'loanAmount': "Small loan principal.",
    'loanDaysRemaining': "Days remaining on the small loan.",
    'loanInterestAccrued': "Accrued interest on the small loan.",
    'strength': "Strength: affects melee damage.",
    'defence': "Defence: affects damage taken.",
    'agility': "Agility: affects accuracy, evasion and turn order.",
    'dexterity': "Dexterity: affects accuracy, critical hits and some skills.",
    'charisma': "Charisma: affects dialogue, romance and shop prices.",
    'intelligence': "Intelligence: affects spells and some class abilities.",
    'wisdom': "Wisdom: affects mana and some class abilities.",
    'constitution': "Constitution: affects max HP and resistances.",
    'baseStrength': "Base strength, excluding equipment and temporary bonuses.",
    'baseDefence': "Base defence, excluding equipment and temporary bonuses.",
    'baseAgility': "Base agility, excluding equipment and temporary bonuses.",
    'baseDexterity': "Base dexterity, excluding equipment and temporary bonuses.",
    'baseCharisma': "Base charisma, excluding equipment and temporary bonuses.",
    'baseIntelligence': "Base intelligence, excluding equipment and temporary bonuses.",
    'baseWisdom': "Base wisdom, excluding equipment and temporary bonuses.",
    'baseConstitution': "Base constitution, excluding equipment and temporary bonuses.",
    'baseStamina': "Base stamina, excluding equipment and temporary bonuses.",
    'weapPow': "Total weapon power; derived from equipped weapons and bonuses.",
    'armPow': "Total armor power; derived from equipped armor and bonuses.",
    'fame': "Fame.",
    'chivalry': "Chivalrous/lawful tendency, opposed to darkness.",
    'darkness': "Dark/evil tendency, opposed to chivalry.",
    'mental': "Mental health; too low triggers mental-collapse states.",
    'combatSpeed': "Combat speed preference (instant/fast/normal).",
    'autoCombatHealPercent': "HP percentage threshold at which auto-combat drinks a healing potion.",
    'fights': "Normal fights.",
    'pFights': "Player-versus-player fights.",
    'tFights': "Team fights.",
    'mKills': "Monsters killed.",
    'mDefeats': "Times defeated by monsters.",
    'pKills': "Players killed.",
    'pDefeats': "Times defeated by players.",
    'murderWeight': "Accumulated murder guilt.",
    'wantedLvl': "Wanted level.",
    'poison': "Current poison stacks/value.",
    'poisonTurns': "Poison turns remaining.",
    'items': "Item ID list; paired one-to-one with itemTypes, and adding/removing affects both sides.",
    'itemTypes': "Item type list; paired one-to-one with items.",
    'inventory': "Item objects in the inventory.",
    'equippedItems': "Equipped items, stored by equipment slot.",
    'dynamicEquipment': "Dynamically generated equipment (enchanted or dropped items).",
    'quickbar': "Skill/spell bindings for quickbar slots 1-9; fixed length.",
    'spells': "Spell learning table; each row is usually [known, mastered].",
    'skills': "Skill list.",
    'learnedAbilities': "Class abilities learned.",
    'skillProficiencies': "Skill proficiencies.",
    'skillTrainingProgress': "Skill training progress.",
    'craftingMaterials': "Crafting materials.",
    'activeQuests': "Active quest list.",
    'achievements': "Unlocked achievements.",
    'achievementsData': "Achievement progress data.",
    'statistics': "Career statistics; mainly for UI display.",
    'phrases': "Character phrases/appearance lines; fixed length.",
    'description': "Description text for this entry; its meaning depends on the containing object.",
    'relationships': "Relationship data with NPCs.",
    'romanceData': "Romance, marriage and family data.",
    'teammateStances': "Each teammate's combat stance.",
    'teammateDisabledAbilities': "Disabled teammate abilities.",
    'teammateDisabledSpells': "Disabled teammate spells.",
    'team': "Team name.",
    'teamPassword': "Team password.",
    'isTeamLeader': "Whether the character leads the team.",
    'teamRec': "Team recruitment-related value.",
    'teamXPPercent': "Experience share for each teammate; fixed length.",
    'teamXPIsExplicit': "Whether team XP distribution was set manually.",
    'teamXPEvenSplit': "Whether experience is split evenly among the party.",
    'height': "Height.",
    'weight': "Weight.",
    'eyes': "Eye color.",
    'hair': "Hair color.",
    'skin': "Skin color.",
    'language': "UI language code.",
    'autoHeal': "Whether healing potions are used automatically.",
    'screenReaderMode': "Whether screen reader mode is enabled.",
    'compactMode': "Whether the compact UI is used.",
    'autoLook': "Whether to look around automatically when entering a location.",
    'dungeonAutoMap': "Whether the dungeon map is drawn automatically.",
    'autoLevelUp': "Whether to level up automatically.",
    'autoEquipDisabled': "Whether auto-equip is disabled.",
    'colorTheme': "UI color theme.",
    'dateFormatPreference': "Date display format.",
    'menuKeysNeedEnter': "Whether menu keys require Enter as well.",
    'webMenuKeysNeedEnter': "Whether web-client menu keys require Enter.",
    'classicMainStreet': "Whether the classic Main Street layout is used.",
    'districtsMainStreet': "Whether Main Street is shown by district.",
    'autoRedistributeXP': "Whether team XP is redistributed automatically.",
    'loginStreak': "Current consecutive login days.",
    'longestLoginStreak': "Longest consecutive login streak.",
    'lastLogin': "Last login time.",
    'lastLoginDate': "Last login date.",
    'accountCreated': "Account creation time.",
    'homeLevel': "Home level.",
    'chestLevel': "Chest level.",
    'trainingRoomLevel': "Training room level.",
    'gardenLevel': "Garden level.",
    'bedLevel': "Bed level.",
    'hearthLevel': "Hearth level.",
    'hasTrophyRoom': "Whether a trophy room is built.",
    'hasTeleportCircle': "Whether a teleport circle is built.",
    'hasLegendaryArmory': "Whether a legendary armory is built.",
    'hasVitalityFountain': "Whether a vitality fountain is built.",
    'hasStudy': "Whether a study is built.",
    'hasServants': "Whether servants are hired.",
    'hasReinforcedDoor': "Whether a reinforced door is installed.",
    'herbHealing': "Herb: Herb Healing count.",
    'herbIronbark': "Herb: Herb Ironbark count.",
    'herbFirebloom': "Herb: Herb Firebloom count.",
    'herbSwiftthistle': "Herb: Herb Swiftthistle count.",
    'herbStarbloom': "Herb: Herb Starbloom count.",
    'herbBuffType': "Herb Buff Type.",
    'herbBuffCombats': "Herb Buff Combats.",
    'herbBuffValue': "Herb Buff Value.",
    'foodBuffType': "Food Buff Type.",
    'foodBuffCombats': "Food Buff Combats.",
    'foodBuffValue': "Food Buff Value.",
    'songBuffType': "Song Buff Type.",
    'songBuffCombats': "Song Buff Combats.",
    'songBuffValue': "Song Buff Value.",
    'settlementBuffType': "Settlement Buff Type.",
    'settlementBuffCombats': "Settlement Buff Combats.",
    'settlementBuffValue': "Settlement Buff Value.",
    'archetype': "NPC archetype (guard, merchant and so on); affects behavior and dialogue.",
    'location': "NPC's current location.",
    'isDead': "Whether the NPC is dead.",
    'isPermaDead': "Whether the NPC is permanently dead; revival usually does not work.",
    'isMarried': "Whether married.",
    'married': "Whether married (legacy-compatible field).",
    'spouseName': "Spouse's name.",
    'isKing': "Whether this is the king.",
    'isHostile': "Whether hostile to the player.",
    'isAIDriven': "Whether driven by the world-simulation AI.",
    'worshippedGod': "Worshipped god.",
    'npcFaction': "NPC faction.",
    'gangId': "Gang ID; an empty string means no gang.",
    'personalityProfile': "NPC personality: aggression, greed, courage, sociability and more.",
    'memories': "NPC memories of the player and other characters.",
    'memoryTimesKept': "Whether real memory timestamps are kept.",
    'currentGoals': "NPC's current goals.",
    'emotionalState': "NPC's current emotional state.",
    'enemies': "NPC's enemies.",
    'knownCharacters': "Characters the NPC knows.",
    'marketInventory': "Merchant NPC's shop inventory.",
    'equippedItemsSave': "Items equipped by the companion.",
    'disabledAbilities': "Disabled abilities.",
    'disabledSpells': "Disabled spells.",
    'isRecruited': "Whether this companion has been recruited.",
    'isActive': "Whether in the active party; keep it in step with activeCompanionIds.",
    'loyaltyLevel': "Companion loyalty (0-100).",
    'trustLevel': "Companion trust (0-100).",
    'romanceLevel': "Companion romance (0-100).",
    'personalQuestStarted': "Whether the companion's personal quest has started.",
    'personalQuestCompleted': "Whether the companion's personal quest is complete.",
    'personalQuestSuccess': "Whether the companion's personal quest succeeded.",
    'recruitedDay': "Game day the companion was recruited.",
    'companions': "Complete saves for the five story companions.",
    'activeCompanionIds': "IDs of active companions; at most 4.",
    'fallenCompanions': "Records of fallen companions.",
    'dungeonPartyNPCIds': "NPC IDs brought along into the dungeon; at most 4.",
    'dungeonPartyPlayerNames': "Other player names in the dungeon party (online echoes).",
    'activeGriefs': "Ongoing grief states.",
    'griefMemories': "Memories related to grief.",
    'bankInterestRate': "Bank interest rate (integer percent or internal units).",
    'bankVaultReserve': "Bank vault reserve.",
    'bankRobberiesToday': "Bank robberies today.",
    'bankRobberiesDate': "Date matching the bank robbery count.",
    'townPotValue': "Town communal pot value.",
    'currentRuler': "Current ruler; blank means none.",
    'activeEvents': "Ongoing world events.",
    'shopInventories': "Inventories of the shops.",
    'recentNews': "Recent town news.",
    'marketplaceListings': "Marketplace listings.",
    'settlement': "Dungeon settlement state.",
    'usedNPCNames': "NPC names already used by the world, to avoid duplicates.",
    'awakeningLevel': "Ocean philosophy awakening level.",
    'collectedFragments': "Awakening fragments collected.",
    'experiencedMoments': "Awakening moments experienced.",
    'oceanInsightIds': "Ocean insight IDs gained.",
    'completedParadoxIds': "Moral paradox IDs answered.",
    'collectedSeals': "Seal IDs found.",
    'collectedArtifacts': "Artifact IDs collected.",
    'griefStage': "Grief stage (legacy field).",
    'griefDaysRemaining': "Grief days remaining (legacy field).",
    'griefCompanionName': "Grief target name (legacy field).",
    'activeNpcGriefs': "Grief states of NPC teammates.",
    'storyFlags': "Story flag dictionary; true means the flag is set.",
    'currentCycle': "New Game+ cycle number.",
    'completedEndings': "Completed ending IDs.",
    'oldGodStates': "Old God state dictionary: keys are Old God numbers.",
    'oldGodsEncountered': "Old Gods already encountered.",
    'currentChapter': "Current story chapter number.",
    'storyFlagBits': "Story flag bits (flags packed into integers).",
    'majorChoices': "Record of major story choices.",
    'playerGods': "Dictionary of gods the player worships.",
    'children': "The player's children.",
    'archetypeTracker': "Jungian archetype tracking data.",
    'royalCourt': "Royal court state: king, tax rates, court members, plots and more.",
    'factions': "Faction reputation and relations.",
    'townNPCStories': "Progress of town NPC storylines.",
    'dreams': "Dream system state.",
    'amnesia': "Amnesia system state.",
    'betrayal': "Betrayal system state.",
    'culturalMemes': "Cultural meme state.",
    'npcMarriages': "Marriages between NPCs.",
    'affairs': "NPC affair records.",
    'mode': "Daily cycle mode.",
    'lastResetTime': "Last daily reset time.",
    'autoSaveEnabled': "Whether autosave is enabled.",
    'autoSaveInterval': "Autosave interval (text).",
    'npcStates': "State of each NPC in the town NPC storylines.",
    'npcId': "NPC identifier used by town stories.",
    'currentStage': "Current story stage.",
    'completedStages': "Completed story stages.",
    'choicesMade': "Choices made at each stage.",
    'stageCompletedOnDay': "Game day each stage was completed.",
    'npcRelationship': "Relationship value with a town-story NPC.",
    'aggression': "Aggression (about 0-1); higher values strengthen this trait or emotion.",
    'greed': "Greed (about 0-1); higher values strengthen this trait or emotion.",
    'courage': "Courage (about 0-1); higher values strengthen this trait or emotion.",
    'vengefulness': "Vengefulness (about 0-1); higher values strengthen this trait or emotion.",
    'impulsiveness': "Impulsiveness (about 0-1); higher values strengthen this trait or emotion.",
    'sociability': "Sociability (about 0-1); higher values strengthen this trait or emotion.",
    'ambition': "Ambition (about 0-1); higher values strengthen this trait or emotion.",
    'trustworthiness': "Trustworthiness (about 0-1); higher values strengthen this trait or emotion.",
    'caution': "Caution (about 0-1); higher values strengthen this trait or emotion.",
    'mysticism': "Mysticism (about 0-1); higher values strengthen this trait or emotion.",
    'patience': "Patience (about 0-1); higher values strengthen this trait or emotion.",
    'romanticism': "Romanticism (about 0-1); higher values strengthen this trait or emotion.",
    'flirtatiousness': "Flirtatiousness (about 0-1); higher values strengthen this trait or emotion.",
    'passion': "Passion (about 0-1); higher values strengthen this trait or emotion.",
    'tenderness': "Tenderness (about 0-1); higher values strengthen this trait or emotion.",
    'anger': "Anger (about 0-1); higher values strengthen this trait or emotion.",
    'fear': "Fear (about 0-1); higher values strengthen this trait or emotion.",
    'sadness': "Sadness (about 0-1); higher values strengthen this trait or emotion.",
    'joy': "Joy (about 0-1); higher values strengthen this trait or emotion.",
    'confidence': "Confidence (about 0-1); higher values strengthen this trait or emotion.",
    'loneliness': "Loneliness (about 0-1); higher values strengthen this trait or emotion.",
    'hope': "Hope (about 0-1); higher values strengthen this trait or emotion.",
    'peace': "Peace (about 0-1); higher values strengthen this trait or emotion.",
    'envy': "Envy (about 0-1); higher values strengthen this trait or emotion.",
    'pride': "Pride (about 0-1); higher values strengthen this trait or emotion.",
    'importance': "Importance (about 0-1); higher memories are more likely to be raised by NPCs.",
    'emotionalImpact': "Emotional impact of this memory.",
    'involvedCharacter': "Character name involved in this memory or relationship.",
    'targetCharacter': "Target character's name.",
    'targetLocation': "Target location code.",
    'targetValue': "Target progress value.",
    'currentValue': "Current progress value.",
    'progress': "Current progress (0-1).",
    'priority': "Priority (about 0-1); higher priorities are chosen more often.",
    'isCompleted': "Whether completed.",
    'createdTime': "Creation time.",
    'timestamp': "Record time.",
    'weaponPower': "Weapon power; affects attack damage.",
    'armorClass': "Armor class; affects damage taken.",
    'armorType': "Armor type (enum integer).",
    'weaponType': "Weapon type (enum integer).",
    'slot': "Equipment slot (enum integer).",
    'rarity': "Rarity (enum integer).",
    'isIdentified': "Whether identified.",
    'isCursed': "Whether cursed.",
    'strengthRequired': "Strength required to use this equipment.",
    'bonusMaxHP': "Max HP bonus from equipment or effects.",
    'bonusWeapPow': "Weapon power bonus from equipment or effects.",
    'bonusArmPow': "Armor power bonus from equipment or effects.",
    'status': "Status (enum integer).",
    'reward': "Reward value.",
    'rewardType': "Reward type (enum integer).",
    'penalty': "Penalty value.",
    'penaltyType': "Penalty type (enum integer).",
    'daysToComplete': "Days allowed to complete the quest.",
    'minLevel': "Minimum level to accept or appear.",
    'maxLevel': "Maximum level to accept or appear.",
    'questType': "Quest type (enum integer).",
    'questTarget': "Quest target identifier.",
    'targetNPCName': "Name of the quest target NPC.",
    'objectives': "Quest objective list.",
    'monsters': "Monsters involved in the quest or event.",
    'isPlayerBounty': "Whether this is a bounty on the player.",
    'bountyGold': "Bounty amount.",
    'isMercContract': "Whether this is a mercenary contract.",
    'issuingFaction': "Faction that issued the quest.",
    'mercContractTier': "Mercenary contract tier.",
    'item': "Item object.",
    'seller': "Seller name.",
    'isNPCSeller': "Whether the seller is an NPC.",
    'sellerNPCId': "Seller NPC ID.",
    'price': "Price.",
    'posted': "Listing time.",
}

# Tokens for the generated "literal" note. Unknown tokens stay in English, so the note
# is still honest when a field has no curated description.
WORD_ZH = {
    'total': "total",
    'today': "today",
    'last': "last",
    'bonus': "bonus",
    'has': "has",
    'god': "god",
    'active': "active",
    'type': "type",
    'day': "day",
    'days': "days",
    'is': "is",
    'gold': "gold",
    'buff': "buff",
    'combats': "combats",
    'id': "ID",
    'ids': "IDs",
    'name': "name",
    'date': "date",
    'used': "used",
    'player': "player",
    'herb': "herb",
    'shop': "shop",
    'completed': "completed",
    'level': "level",
    'value': "value",
    'settlement': "settlement",
    'damage': "damage",
    'mental': "mental",
    'enchant': "enchant",
    'divine': "divine",
    'from': "from",
    'team': "team",
    'faction': "faction",
    'left': "left",
    'magic': "magic",
    'dungeon': "dungeon",
    'armor': "armor",
    'npc': "NPC",
    'proposal': "proposal",
    'stats': "stats",
    'killed': "killed",
    'target': "target",
    'base': "base",
    'choices': "choices",
    'spells': "spells",
    'drug': "drug",
    'merc': "merc",
    'encounters': "encounters",
    'quests': "quests",
    'loan': "loan",
    'claimed': "claimed",
    'monsters': "monsters",
    'shrine': "shrine",
    'actions': "actions",
    'time': "time",
    'cast': "cast",
    'made': "made",
    'title': "title",
    'weapon': "weapon",
    'king': "king",
    'cursed': "cursed",
    'favor': "favor",
    'monster': "monster",
    'lost': "lost",
    'utc': "UTC",
    'item': "item",
    'items': "items",
    'earned': "earned",
    'royal': "royal",
    'experience': "experience",
    'mana': "mana",
    'pending': "pending",
    'building': "building",
    'tax': "tax",
    'dark': "dark",
    'moral': "moral",
    'created': "created",
    'game': "game",
    'power': "power",
    'slayer': "slayer",
    'death': "death",
    'key': "key",
    'fights': "fights",
    'applied': "applied",
    'blessing': "blessing",
    'current': "current",
    'lovers': "lovers",
    'standing': "standing",
    'max': "max",
    'gambling': "gambling",
    'training': "training",
    'weekly': "weekly",
    'boss': "boss",
    'healing': "healing",
    'poison': "poison",
    'song': "song",
    'strength': "strength",
    'world': "world",
    'character': "character",
    'count': "count",
    'market': "market",
    'hp': "HP",
    'since': "since",
    'login': "login",
    'streak': "streak",
    'xp': "XP",
    'times': "times",
    'disabled': "disabled",
    'quest': "quest",
    'betrayed': "betrayed",
    'bank': "bank",
    'guard': "guard",
    'floors': "floors",
    'reward': "reward",
    'church': "church",
    'shown': "shown",
    'abilities': "abilities",
    'args': "args",
    'seller': "seller",
    'description': "description",
    'pit': "pit",
    'stranger': "stranger",
    'father': "father",
    'shield': "shield",
    'history': "history",
    'weight': "weight",
    'street': "street",
    'penalty': "penalty",
    'week': "week",
    'stat': "stat",
    'ticks': "ticks",
    'personal': "personal",
    'teammate': "teammate",
    'bounty': "bounty",
    'critical': "critical",
    'progress': "progress",
    'workshop': "workshop",
    'daily': "daily",
    'real': "real",
    'wilderness': "wilderness",
    'bosses': "bosses",
    'comment': "comment",
    'intimate': "intimate",
    'barred': "barred",
    'until': "until",
    'rank': "rank",
    'wrath': "wrath",
    'class': "class",
    'defense': "defense",
    'highest': "highest",
    'food': "food",
    'black': "black",
    'betrayal': "betrayal",
    'proposed': "proposed",
    'played': "played",
    'family': "family",
    'attuned': "attuned",
    'attempts': "attempts",
    'nr': "no.",
    'floor': "floor",
    'hag': "haggle",
    'arm': "arm",
    'pet': "pet",
    'songs': "songs",
    'explored': "explored",
    'constitution': "constitution",
    'tier': "tier",
    'taken': "taken",
    'shadow': "shadow",
    'contracts': "contracts",
    'banned': "banned",
    'finger': "finger",
    'pregnancy': "pregnancy",
    'due': "due",
    'relationship': "relationship",
    'tavern': "tavern",
    'vote': "vote",
    'hand': "hand",
    'schema': "schema",
    'given': "given",
    'jealousy': "jealousy",
    'defeats': "defeats",
    'original': "original",
    'holy': "holy",
    'companions': "companions",
    'rival': "rival",
    'gained': "gained",
    'requires': "requires",
    'extra': "extra",
    'town': "town",
    'money': "money",
    'encounter': "encounter",
    'success': "success",
    'failed': "failed",
    'attack': "attack",
    'defence': "defence",
    'chance': "chance",
    'amount': "amount",
    'duration': "duration",
    'turns': "turns",
    'rounds': "rounds",
    'remaining': "remaining",
    'min': "min",
    'rate': "rate",
    'percent': "percent",
    'modifier': "modifier",
    'multiplier': "multiplier",
    'cost': "cost",
    'price': "price",
    'quality': "quality",
    'rarity': "rarity",
    'unique': "unique",
    'special': "special",
    'normal': "normal",
    'rare': "rare",
    'epic': "epic",
    'legendary': "legendary",
    'unlocked': "unlocked",
    'seen': "seen",
    'known': "known",
    'visited': "visited",
    'discovered': "discovered",
    'finished': "finished",
    'started': "started",
    'skipped': "skipped",
    'read': "read",
    'heard': "heard",
    'found': "found",
    'defeated': "defeated",
    'won': "won",
    'fled': "fled",
    'dealt': "dealt",
    'received': "received",
    'spent': "spent",
    'sold': "sold",
    'bought': "bought",
    'crafted': "crafted",
    'gathered': "gathered",
    'average': "average",
    'best': "best",
    'worst': "worst",
    'first': "first",
    'next': "next",
    'previous': "previous",
    'recent': "recent",
    'monthly': "monthly",
    'yearly': "yearly",
    'hourly': "hourly",
    'minute': "minute",
    'hour': "hour",
    'second': "second",
    'morning': "morning",
    'afternoon': "afternoon",
    'evening': "evening",
    'night': "night",
}

SAVE_HINT = ("Close the game before saving: it keeps the save open and rewrites it on autosave."
             " A timestamped backup is created next to the save before every save.")


# ============================== save discovery ==============================

def find_saves_directory(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)

    # FileSaveBackend writes to %APPDATA%\UsurperReloaded\saves and falls back to a saves folder
    # beside the game. Look at both and use whichever holds the newest save.
    candidates: list[Path] = []
    if sys.platform.startswith("win"):
        appdata = os.environ.get("APPDATA")
        if appdata:
            candidates.append(Path(appdata) / "UsurperReloaded" / "saves")
    else:
        home = os.environ.get("HOME")
        if home:
            candidates.append(Path(home) / ".local" / "share" / "UsurperReloaded" / "saves")

    root = find_repo_root()
    if root is not None:
        candidates += [root / "bin" / "Debug" / "net8.0" / "saves",
                       root / "bin" / "Release" / "net8.0" / "saves"]
    candidates.append(Path.cwd() / "saves")

    existing = [path for path in candidates if path.is_dir()]
    if existing:
        def newest(directory: Path) -> float:
            saves = list(directory.glob("*.json"))
            return max((p.stat().st_mtime for p in saves), default=0)
        return max(existing, key=newest)
    if root is not None:
        return root / "bin" / "Debug" / "net8.0" / "saves"
    return Path.cwd() / "saves"


def list_saves(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    return sorted(directory.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)


def describe(path: Path) -> str:
    stamp = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    return f"{path.name}   ({stamp}, {path.stat().st_size // 1024} KB)"


def load_save(path: Path) -> dict:
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict) or not isinstance(data.get("player"), dict):
        raise ValueError(f"{path.name} has no player object")
    return data


def save_data(path: Path, data: dict) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = path.with_name(f"{path.name}.bak-{stamp}")
    counter = 1
    while backup.exists():
        backup = path.with_name(f"{path.name}.bak-{stamp}-{counter}")
        counter += 1
    shutil.copy2(path, backup)

    handle, temporary = tempfile.mkstemp(prefix=".editing-", dir=path.parent, text=True)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise
    return backup


# ============================== JSON paths ==============================

@dataclass(frozen=True)
class Leaf:
    """One editable scalar, or one list that can gain and lose elements."""

    path: tuple
    value: Any
    kind: str
    is_container: bool = False
    scalar_list: bool = False
    element_kind: str | None = None

    @property
    def list_length(self) -> int:
        return len(self.value) if isinstance(self.value, list) else 0


def kind_of(value: Any) -> str:
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if value is None:
        return "null"
    if isinstance(value, list):
        return "list"
    return "dict"


def is_editable(value: Any) -> bool:
    return isinstance(value, (int, float, bool, str))


def show(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    return str(value)


def display_value(value: Any, limit: int = 160) -> str:
    text = show(value).replace("\r\n", "\n").replace("\r", "\n").replace("\n", " ⏎ ")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def path_text(path: tuple) -> str:
    text = ""
    for part in path:
        if isinstance(part, int):
            text += f"[{part}]"
        else:
            text = f"{text}.{part}" if text else str(part)
    return text


def label_of(path: tuple) -> str:
    """Friendly label: the leaf key, or the parent key for a list element."""
    if not path:
        return ""
    part = path[-1]
    if isinstance(part, int):
        if len(path) < 2:
            return str(part)
        part = path[-2]
    if str(part) == "description" and path[:-1] in (("player",), ("player", "description")):
        return "Appearance description"
    return LABELS.get(str(part), str(part))


_CAMEL_WORDS = re.compile(r"[A-Z]+(?=[A-Z][a-z]|$)|[A-Z]?[a-z]+|[0-9]+")


def split_camel(key: str) -> list[str]:
    return _CAMEL_WORDS.findall(key)


def is_schema_key(key: str) -> bool:
    """True for a camelCase field name; names, ids and numeric dictionary keys are not."""
    return bool(re.match(r"^[a-z][A-Za-z0-9]*$", key))


def mechanical_phrase(key: str) -> str:
    """A word-by-word Chinese gloss. Unknown words stay in English instead of guessing."""
    words = split_camel(key)
    return " · ".join(WORD_ZH.get(word.lower(), word) for word in words) or key


def find_repo_root() -> Path | None:
    for parent in [Path(__file__).resolve().parent, *Path(__file__).resolve().parents]:
        if (parent / GAME_PROJECT).is_file():
            return parent
    return None


_source_notes: dict[str, str] | None = None


GAME_DATA_FILES = [
    ("Equipment", "equipment.json"),
    ("NPC", "npcs.json"),
    ("Monster families", "monster_families.json"),
    ("Dreams", "dreams.json"),
    ("Dialogue", "dialogue.json"),
    ("Balance", "balance.json"),
]


def game_executable() -> Path | None:
    root = find_repo_root()
    if root is None:
        return None
    for relative in ("bin/Debug/net8.0/UsurperReborn.exe", "bin/Release/net8.0/UsurperReborn.exe",
                     "bin/Debug/net8.0/UsurperReborn", "bin/Release/net8.0/UsurperReborn"):
        path = root / relative
        if path.exists():
            return path
    return None


def game_data_directory() -> Path:
    exe = game_executable()
    if exe is not None:
        return exe.parent / "GameData"
    root = find_repo_root()
    return (root / "GameData") if root is not None else (Path.cwd() / "GameData")


def export_default_game_data() -> str:
    exe = game_executable()
    if exe is None:
        raise FileNotFoundError("UsurperReborn.exe was not found, so the default GameData cannot be exported.")
    result = subprocess.run([str(exe), "--export-data"], cwd=str(exe.parent),
                            capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or "Export failed").strip())
    return f"Default GameData exported to: {game_data_directory()}"


def source_notes() -> dict[str, str]:
    """Comments next to the save-model properties, used when no curated note exists.

    The comments are the game's own; version tags are stripped so "1.3.10: dying wish
    messages" reads as "dying wish messages".
    """
    global _source_notes
    if _source_notes is not None:
        return _source_notes

    notes: dict[str, str] = {}
    root = find_repo_root()
    if root is None:
        _source_notes = notes
        return notes
    files = [root / "Scripts/Systems/SaveDataStructures.cs",
             root / "Scripts/Systems/CompanionSystem.cs"]
    files += list((root / "Scripts").rglob("*SaveData*.cs"))
    for path in dict.fromkeys(files):
        if not path.is_file():
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for index, line in enumerate(lines):
            match = re.search(r"public\s+(?:static\s+)?(?:readonly\s+)?[\w<>\[\],.? ]+"
                              r"\s+(\w+)\s*(?:\{\s*get|;)", line)
            if match is None:
                continue
            name = match.group(1)
            key = name[0].lower() + name[1:]
            comment = line.split("//", 1)[1].strip() if "//" in line else ""
            if not comment:
                collected = []
                previous = index - 1
                while previous >= 0 and lines[previous].strip().startswith("//"):
                    collected.append(lines[previous].strip().lstrip("/").strip())
                    previous -= 1
                comment = " ".join(reversed(collected))
            comment = re.sub(r"<[^>]+>", "", comment)
            comment = re.sub(r"^v?\d+(?:\.\d+)*\s*[:\-]?\s*", "", comment).strip()
            if len(comment) >= 6 and key not in notes:
                notes[key] = comment[:300]
    _source_notes = notes
    return notes


def get_path(root: Any, path: tuple) -> Any:
    node = root
    for part in path:
        node = node[part]
    return node


def set_path(root: Any, path: tuple, value: Any) -> None:
    parent = get_path(root, path[:-1])
    parent[path[-1]] = value


def iter_leaves(node: Any, path: tuple = (), depth: int = 0) -> Iterator[Leaf]:
    """Every scalar below node, plus a row for every list so it can be selected for add/remove."""
    if depth > 32:
        return
    if isinstance(node, dict):
        for key, value in node.items():
            child = path + (key,)
            yield from iter_leaves(value, child, depth + 1) if isinstance(value, dict) else _value_leaves(value, child, depth)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            child = path + (index,)
            yield from iter_leaves(value, child, depth + 1) if isinstance(value, dict) else _value_leaves(value, child, depth)


def _value_leaves(value: Any, path: tuple, depth: int) -> Iterator[Leaf]:
    if isinstance(value, list):
        scalar_list = all(not isinstance(item, (dict, list)) for item in value)
        if not value:
            # An empty list alone does not say what it holds; only the schema-known ones
            # may be extended here, or a string could land in a List<SomeObject>.
            scalar_list = path in EMPTY_SCALAR_LISTS
        element_kind = EMPTY_SCALAR_LISTS.get(path) if not value else None
        if value and scalar_list:
            element_kind = kind_of(value[0])
        if not scalar_list:
            element_kind = None
        yield Leaf(path, value, "list", is_container=True,
                   scalar_list=scalar_list, element_kind=element_kind)
        for index, item in enumerate(value):
            child = path + (index,)
            if isinstance(item, (dict, list)):
                yield from iter_leaves(item, child, depth + 1)
            else:
                yield Leaf(child, item, kind_of(item))
    elif isinstance(value, dict):
        yield from iter_leaves(value, path, depth + 1)
    else:
        yield Leaf(path, value, kind_of(value))


def coerce(current: Any, text: str) -> Any:
    """Turn typed text into a value of the kind the field already has."""
    kind = kind_of(current)
    if kind == "bool":
        lowered = text.strip().lower()
        if lowered in ("true", "1", "yes", "y", "Yes", "True"):
            return True
        if lowered in ("false", "0", "no", "n", "No", "False"):
            return False
        raise ValueError("Expected true/false, yes/no, or 1/0")

    if kind == "int":
        try:
            return int(text.strip())
        except ValueError:
            raise ValueError("Expected an integer") from None

    if kind == "float":
        try:
            value = float(text.strip())
        except ValueError:
            raise ValueError("Expected a number") from None
        if not math.isfinite(value):
            raise ValueError("Expected a finite number")
        return value

    if kind == "null":
        raise ValueError("This field is null, so its type is unknown and it cannot be edited directly")

    return text


NAME_KEYS = {"name", "name1", "name2", "realName"}
MARKUP_CHARS = set('<>&"')


def validate_change(path: tuple, current: Any, text: str) -> Any:
    """Coerce a staged value, refusing a name that carries markup the game bans."""
    value = coerce(current, text)
    if path and str(path[-1]) in NAME_KEYS and isinstance(value, str):
        bad = sorted(set(value) & MARKUP_CHARS)
        if bad:
            raise ValueError(f"Names cannot contain {' '.join(bad)}")
    return value


def apply_changes(data: dict, pending: dict[tuple, str]) -> tuple[list[str], list[str]]:
    """Validate every staged value first, then apply them together.

    Returns (applied, refused) readable lines. If anything is refused nothing is applied, so a
    save never half-lands and the caller can point at every bad value at once.
    """
    resolved: list[tuple[tuple, Any]] = []
    applied: list[str] = []
    refused: list[str] = []
    for path, text in pending.items():
        try:
            current = get_path(data, path)
        except (KeyError, IndexError, TypeError):
            refused.append(f"{path_text(path)}: this save no longer has this field")
            continue
        if not is_editable(current):
            refused.append(f"{path_text(path)}: not a simple value")
            continue
        try:
            updated = validate_change(path, current, text)
        except ValueError as error:
            refused.append(f"{path_text(path)}: {error}")
            continue
        resolved.append((path, updated))
        applied.append(f"{path_text(path)} = {show(updated)}")
    if refused:
        return [], refused
    for path, updated in resolved:
        set_path(data, path, updated)
    return applied, refused


def list_add(data: dict, list_path: tuple, value: Any) -> None:
    target = get_path(data, list_path)
    if not isinstance(target, list):
        raise ValueError("Target is not a list")
    target.append(value)


def list_remove(data: dict, list_path: tuple, index: int) -> Any:
    target = get_path(data, list_path)
    if not isinstance(target, list):
        raise ValueError("Target is not a list")
    if not 0 <= index < len(target):
        raise ValueError("Index out of list range")
    return target.pop(index)


def check(directory: Path) -> int:
    saves = list_saves(directory)
    if not saves:
        print(f"No saves found: {directory}")
        return 1
    print(f"Save directory: {directory}")
    for path in saves[:10]:
        try:
            data = load_save(path)
        except (ValueError, json.JSONDecodeError) as error:
            print(f"  {path.name}: unreadable ({error})")
            continue
        player = data["player"]
        leaves = list(iter_leaves(data))
        editable = sum(1 for leaf in leaves if not leaf.is_container and is_editable(leaf.value))
        print(f"  {path.name}: Lv.{player.get('level')} {player.get('name2')}, "
              f"{len(data.get('npCs') or [])} NPCs, "
              f"{editable} editable fields (plus {sum(1 for x in leaves if x.is_container)} lists)")
    return 0


# ============================== window ==============================

class EditorWindow:
    """Sections on the top bar, fields in the middle, one field editor on the right."""

    MAX_ROWS = 2500

    def __init__(self, directory: Path):
        import tkinter as tk
        from tkinter import messagebox, ttk

        self.tk = tk
        self.ttk = ttk
        self.messagebox = messagebox
        self.simpledialog = __import__("tkinter.simpledialog", fromlist=["simpledialog"])
        self.directory = directory
        self.saves: list[Path] = []
        self.save_path: Path | None = None
        self.data: dict = {}
        self.all_leaves: list[Leaf] = []
        self.rows: list[Leaf] = []
        self.pending: dict[tuple, str] = {}
        self.dirty = False
        self.npc_index: int | None = None

        self.root = tk.Tk()
        self.root.title("Usurper Reborn Save Editor")
        self.root.geometry("1180x760")
        self.root.minsize(980, 620)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.bind("<Control-s>", lambda _event: self.save())
        self.root.bind("<F5>", lambda _event: self.reload())

        self._build_top()
        self._build_body()
        self._build_footer()
        self.populate_saves()
        self.root.after(100, self.load_selected)

    # ---- layout -----------------------------------------------------------------------------------

    def _build_top(self) -> None:
        ttk = self.ttk
        tk = self.tk

        top = ttk.Frame(self.root, padding=8)
        top.pack(fill="x")
        ttk.Label(top, text="Save").pack(side="left")
        self.save_box = ttk.Combobox(top, state="readonly", width=54)
        self.save_box.pack(side="left", padx=6)
        self.save_box.bind("<<ComboboxSelected>>", lambda _event: self.load_selected())
        ttk.Button(top, text="Rescan", command=self.rescan_saves).pack(side="left")
        ttk.Button(top, text="Change Folder", command=self.choose_directory).pack(side="left", padx=(6, 0))
        ttk.Button(top, text="Open Folder", command=self.open_directory).pack(side="left", padx=(6, 0))

        top2 = ttk.Frame(self.root, padding=(8, 0, 8, 6))
        top2.pack(fill="x")
        ttk.Label(top2, text="Section").pack(side="left")
        self.section_box = ttk.Combobox(top2, state="readonly", width=18,
                                        values=[name for name, _ in SECTIONS])
        self.section_box.current(0)
        self.section_box.pack(side="left", padx=6)
        self.section_box.bind("<<ComboboxSelected>>", lambda _event: self.render())

        ttk.Label(top2, text="NPC").pack(side="left", padx=(10, 0))
        self.npc_box = ttk.Combobox(top2, state="readonly", width=38, values=[])
        self.npc_box.pack(side="left", padx=6)
        self.npc_box.bind("<<ComboboxSelected>>", lambda _event: self.on_npc_changed())

        ttk.Label(top2, text="Search").pack(side="left", padx=(10, 0))
        self.search = ttk.Entry(top2, width=28)
        self.search.pack(side="left", padx=6)
        self.search.bind("<KeyRelease>", lambda _event: self.render())
        ttk.Button(top2, text="Clear", command=self.clear_search).pack(side="left")

        bar = ttk.Frame(self.root, padding=(8, 0, 8, 6))
        bar.pack(fill="x")
        ttk.Button(bar, text="Companion Manager", command=self.open_companion_manager).pack(side="left")
        ttk.Button(bar, text="Dungeon Party", command=self.open_party_manager).pack(side="left", padx=6)
        ttk.Button(bar, text="Save Manager", command=self.open_save_manager).pack(side="left")
        ttk.Button(bar, text="Game Data", command=self.open_game_data).pack(side="left", padx=6)
        ttk.Button(bar, text="Summary", command=self.show_summary).pack(side="left")
        ttk.Button(bar, text="File Locations", command=self.show_paths).pack(side="left", padx=6)
        self.save_button = ttk.Button(bar, text="Save All Changes", command=self.save)
        self.save_button.pack(side="left", padx=(18, 0))
        ttk.Button(bar, text="Reload (Discard Changes)", command=self.reload).pack(side="left", padx=6)
        self.change_count = ttk.Label(bar, text="No unsaved changes", foreground="#555")
        self.change_count.pack(side="right")

        self.action_bar = ttk.Frame(self.root, padding=(8, 0, 8, 6))
        self.action_bar.pack(fill="x")

    def _build_body(self) -> None:
        ttk = self.ttk
        tk = self.tk
        body = ttk.Panedwindow(self.root, orient="horizontal")
        body.pack(fill="both", expand=True, padx=8)

        left = ttk.Frame(body)
        body.add(left, weight=4)
        table = ttk.Frame(left)
        table.pack(fill="both", expand=True)
        self.list = ttk.Treeview(table, columns=("value", "type", "note", "path"),
                                 show="tree headings", height=22, selectmode="browse")
        self.list.heading("#0", text="Field")
        self.list.heading("value", text="Current Value")
        self.list.heading("type", text="Type")
        self.list.heading("note", text="Notes")
        self.list.heading("path", text="Path")
        self.list.column("#0", width=220)
        self.list.column("value", width=250)
        self.list.column("type", width=56)
        self.list.column("note", width=430)
        self.list.column("path", width=320)
        self.list.grid(row=0, column=0, sticky="nsew")
        vertical = ttk.Scrollbar(table, orient="vertical", command=self.list.yview)
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal = ttk.Scrollbar(table, orient="horizontal", command=self.list.xview)
        horizontal.grid(row=1, column=0, sticky="ew")
        table.rowconfigure(0, weight=1)
        table.columnconfigure(0, weight=1)
        self.list.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.list.bind("<<TreeviewSelect>>", lambda _event: self.show_selected())
        self.list.tag_configure("pending", foreground="#b45309")
        self.list.tag_configure("container", foreground="#6b7280")

        right = ttk.Frame(body, padding=(12, 0, 0, 0), width=330)
        body.add(right, weight=1)
        right.pack_propagate(False)

        self.field_label = ttk.Label(right, text="(Select a field)", font=("Segoe UI", 11, "bold"),
                                     wraplength=310)
        self.field_label.pack(anchor="w", pady=(4, 2))
        self.path_label = ttk.Label(right, text="", foreground="#555", wraplength=310)
        self.path_label.pack(anchor="w", pady=(0, 6))

        ttk.Label(right, text="Field Notes").pack(anchor="w")
        note_frame = ttk.Frame(right)
        note_frame.pack(fill="x", pady=(2, 8))
        self.note = tk.Text(note_frame, height=5, wrap="word", state="disabled")
        self.note.pack(side="left", fill="both", expand=True)
        note_bar = ttk.Scrollbar(note_frame, orient="vertical", command=self.note.yview)
        note_bar.pack(side="right", fill="y")
        self.note.configure(yscrollcommand=note_bar.set)

        ttk.Label(right, text="Current Value").pack(anchor="w")
        self.current_label = ttk.Label(right, text="—", foreground="#333", wraplength=310)
        self.current_label.pack(anchor="w", pady=(0, 8))

        ttk.Label(right, text="New Value").pack(anchor="w")
        editor_frame = ttk.Frame(right)
        editor_frame.pack(fill="x", pady=(0, 6))
        self.editor = tk.Text(editor_frame, height=4, wrap="word", undo=True)
        self.editor.pack(side="left", fill="both", expand=True)
        editor_bar = ttk.Scrollbar(editor_frame, orient="vertical", command=self.editor.yview)
        editor_bar.pack(side="right", fill="y")
        self.editor.configure(yscrollcommand=editor_bar.set)
        self.editor.bind("<Control-Return>", lambda _event: self.stage_selected())

        buttons = ttk.Frame(right)
        buttons.pack(fill="x")
        self.apply_button = ttk.Button(buttons, text="Apply This Field", command=self.stage_selected)
        self.apply_button.pack(side="left")
        self.revert_button = ttk.Button(buttons, text="Revert This Field", command=self.revert_selected)
        self.revert_button.pack(side="left", padx=6)

        self.bool_frame = ttk.Frame(right)
        self.bool_frame.pack(fill="x", pady=(6, 0))
        ttk.Button(self.bool_frame, text="Set true", command=lambda: self.set_editor("true")).pack(side="left")
        ttk.Button(self.bool_frame, text="Set false", command=lambda: self.set_editor("false")).pack(side="left", padx=6)

        ttk.Separator(right).pack(fill="x", pady=12)
        ttk.Label(right, text="List Tools").pack(anchor="w")
        self.add_button = ttk.Button(right, text="Add Element to List", command=self.add_to_list)
        self.add_button.pack(fill="x", pady=(4, 4))
        self.delete_button = ttk.Button(right, text="Delete Selected List Element", command=self.delete_from_list)
        self.delete_button.pack(fill="x")

        ttk.Separator(right).pack(fill="x", pady=12)
        ttk.Label(right, text="Notes", foreground="#555", wraplength=310).pack(anchor="w")
        ttk.Label(right, text="Ctrl+Enter applies this field, Ctrl+S saves, F5 reloads."
                             "The quick actions above the section mirror the G editor's category operations and ask before running."
                             "Files are written only when you save. Fixed-length lists cannot gain or lose elements;"
                             "paired lists such as items and itemTypes ask for confirmation first.",
                  foreground="#555", wraplength=310).pack(anchor="w")

    def _build_footer(self) -> None:
        tk = self.tk
        frame = tk.Frame(self.root)
        frame.pack(fill="x", padx=8, pady=8)
        self.status = tk.Text(frame, height=7, wrap="word")
        self.status.pack(side="left", fill="both", expand=True)
        bar = self.ttk.Scrollbar(frame, orient="vertical", command=self.status.yview)
        bar.pack(side="right", fill="y")
        self.status.configure(state="disabled", yscrollcommand=bar.set)
        tk.Label(self.root, text=SAVE_HINT, foreground="#b91c1c").pack(anchor="w", padx=8, pady=(0, 6))

    # ---- save files -------------------------------------------------------------------------------

    def populate_saves(self, select: Path | None = None) -> None:
        self.saves = list_saves(self.directory)
        self.save_box["values"] = [describe(path) for path in self.saves]
        if not self.saves:
            self.say(f"No saves found: {self.directory}")
            return
        index = 0
        if select is not None:
            for position, path in enumerate(self.saves):
                if path == select:
                    index = position
                    break
        self.save_box.current(index)

    def rescan_saves(self) -> None:
        self.populate_saves(self.save_path)

    def choose_directory(self) -> None:
        from tkinter import filedialog
        chosen = filedialog.askdirectory(parent=self.root, initialdir=str(self.directory),
                                         title="Choose Save Directory")
        if not chosen:
            return
        if self.has_changes() and not self.confirm_discard():
            return
        self.directory = Path(chosen)
        self.pending.clear()
        self.dirty = False
        self.save_path = None
        self.populate_saves()
        self.load_selected()

    def open_directory(self) -> None:
        try:
            if sys.platform.startswith("win"):
                os.startfile(self.directory)  # type: ignore[attr-defined]
            else:
                import subprocess
                subprocess.Popen(["xdg-open", str(self.directory)])
        except Exception as error:
            self.say(f"Could not open the folder: {error}")

    def load_selected(self) -> None:
        index = self.save_box.current()
        if index < 0 or index >= len(self.saves):
            return
        path = self.saves[index]
        if path == self.save_path and self.data:
            return
        if self.has_changes() and not self.confirm_discard():
            self.populate_saves(self.save_path)
            return
        try:
            data = load_save(path)
        except (ValueError, json.JSONDecodeError, OSError) as error:
            self.say(f"Load failed: {error}")
            return
        self.save_path = path
        self.data = data
        self.pending.clear()
        self.dirty = False
        self.npc_index = None
        self.rebuild_view()
        player = data.get("player", {})
        self.say(f"{path.name}: {player.get('name2')}  Lv.{player.get('level')}, "
                 f"{len(data.get('npCs') or [])} NPCs, {len(self.all_leaves)} rows browsable.")

    def reload(self) -> None:
        if self.has_changes() and not self.confirm_discard():
            return
        target = self.save_path
        self.pending.clear()
        self.dirty = False
        self.save_path = None
        self.populate_saves(target)
        self.load_selected()

    def has_changes(self) -> bool:
        return bool(self.pending) or self.dirty

    def confirm_discard(self) -> bool:
        return bool(self.messagebox.askyesno(
            "Discard changes?", "There are unsaved changes. Discard them and continue?", parent=self.root))

    # ---- viewing ----------------------------------------------------------------------------------

    def rebuild_view(self) -> None:
        self.all_leaves = list(iter_leaves(self.data))
        self.refresh_npc_box()
        self.render()
        self.update_change_count()

    def refresh_npc_box(self) -> None:
        npcs = self.data.get("npCs") or []
        values = []
        for npc in npcs:
            if not isinstance(npc, dict):
                values.append("(Unrecognized NPC)")
                continue
            dead = " · Dead" if npc.get("isDead") else ""
            values.append(f"{npc.get('name', '?')}  Lv.{npc.get('level', '?')}  "
                          f"{npc.get('location', '?')}{dead}")
        self.npc_box["values"] = values
        if values:
            index = self.npc_index if self.npc_index is not None else 0
            index = max(0, min(index, len(values) - 1))
            self.npc_box.current(index)
            if self.npc_index is None:
                self.npc_index = index
        else:
            self.npc_box.set("")

    def on_npc_changed(self) -> None:
        index = self.npc_box.current()
        if index >= 0:
            self.npc_index = index
            self.section_box.set(SECTIONS[2][0])
            self.render()

    def current_section(self) -> str:
        index = self.section_box.current()
        return SECTIONS[index][1] if 0 <= index < len(SECTIONS) else "player_common"

    def section_leaves(self) -> list[Leaf]:
        section = self.current_section()
        leaves = self.all_leaves

        if section == "char_info":
            return self.player_key_leaves(CHAR_INFO_KEYS)
        if section == "stats":
            return self.player_key_leaves(STAT_KEYS)
        if section == "economy":
            return self.player_key_leaves(ECONOMY_KEYS)
        if section == "appearance":
            return self.player_key_leaves(APPEARANCE_KEYS)
        if section == "team":
            return self.player_key_leaves(TEAM_KEYS)
        if section == "status":
            chosen = self.player_key_leaves(STATUS_KEYS)
            for prefix in (("player", "activeStatuses"), ("player", "timedStatBuffs"),
                           ("player", "permakillLog")):
                chosen += [leaf for leaf in leaves if leaf.path[:2] == prefix]
            return chosen
        if section == "inventory":
            return self.prefix_leaves(("player", "inventory"), ("player", "equippedItems"),
                                      ("player", "dynamicEquipment"), ("player", "items"),
                                      ("player", "itemTypes"))
        if section == "spells":
            return self.prefix_leaves(("player", "spells"), ("player", "learnedAbilities"),
                                      ("player", "quickbar"))
        if section == "companions":
            return self.prefix_leaves(("storySystems", "companions"),
                                      ("storySystems", "activeCompanionIds"),
                                      ("storySystems", "fallenCompanions"),
                                      ("storySystems", "activeGriefs"),
                                      ("storySystems", "griefMemories"))
        if section == "quests":
            return self.prefix_leaves(("player", "activeQuests"), ("worldState", "activeQuests"))
        if section == "relationships":
            chosen = self.prefix_leaves(("player", "relationships"), ("storySystems", "children"),
                                        ("storySystems", "npcMarriages"),
                                        ("storySystems", "affairs"))
            chosen += self.player_key_leaves(FAMILY_KEYS)
            return chosen
        if section == "training":
            chosen = self.prefix_leaves(("player", "skillProficiencies"),
                                        ("player", "statTrainingCounts"),
                                        ("player", "skillTrainingProgress"),
                                        ("player", "craftingMaterials"))
            chosen += self.player_key_leaves(TRAINING_KEYS)
            return chosen
        if section == "player_common":
            order = {key: (group_index, key_index)
                     for group_index, (_, group) in enumerate(PLAYER_GROUPS)
                     for key_index, key in enumerate(group)}
            common = [leaf for leaf in leaves
                      if len(leaf.path) == 2 and leaf.path[0] == "player" and leaf.path[1] in order]
            common.sort(key=lambda leaf: order[leaf.path[1]])
            return common
        if section == "player_all":
            return [leaf for leaf in leaves if leaf.path and leaf.path[0] == "player"]
        if section == "npc":
            return self.npc_leaves()
        if section == "party":
            prefixes = [("storySystems", "companions"), ("storySystems", "activeCompanionIds"),
                        ("storySystems", "dungeonPartyNPCIds"),
                        ("storySystems", "dungeonPartyPlayerNames"),
                        ("storySystems", "fallenCompanions")]
            chosen = [leaf for leaf in leaves if any(leaf.path[: len(p)] == p for p in prefixes)]
            chosen += [leaf for leaf in leaves if len(leaf.path) == 2 and leaf.path[0] == "player"
                       and leaf.path[1] in PLAYER_PARTY_KEYS]
            return chosen
        if section == "world":
            return [leaf for leaf in leaves if leaf.path and leaf.path[0] == "worldState"]
        if section == "story":
            return [leaf for leaf in leaves if leaf.path and leaf.path[0] == "storySystems"]
        if section == "settings":
            chosen = [leaf for leaf in leaves if leaf.path and leaf.path[0] == "settings"]
            chosen += [leaf for leaf in leaves if len(leaf.path) == 2 and leaf.path[0] == "player"
                       and leaf.path[1] in PLAYER_SETTING_KEYS]
            return chosen
        return leaves

    def npc_leaves(self) -> list[Leaf]:
        npcs = self.data.get("npCs") or []
        needle = self.search.get().strip().lower()
        if needle:
            # A search in the NPC view looks through the whole roster, which is how one finds
            # "that NPC" by a remembered line or field.
            return [leaf for leaf in self.all_leaves
                    if leaf.path and leaf.path[0] == "npCs" and self.matches(leaf, needle)]
        index = self.npc_index
        if index is None or index < 0 or index >= len(npcs):
            return []
        return [leaf for leaf in self.all_leaves
                if len(leaf.path) >= 2 and leaf.path[0] == "npCs" and leaf.path[1] == index]

    def player_key_leaves(self, keys: set[str]) -> list[Leaf]:
        return [leaf for leaf in self.all_leaves
                if len(leaf.path) == 2 and leaf.path[0] == "player" and leaf.path[1] in keys]

    def prefix_leaves(self, *prefixes: tuple) -> list[Leaf]:
        return [leaf for leaf in self.all_leaves
                if any(leaf.path[: len(prefix)] == prefix for prefix in prefixes)]

    def matches(self, leaf: Leaf, needle: str) -> bool:
        haystack = f"{path_text(leaf.path)} {self.field_text(leaf)} {display_value(leaf.value)}".lower()
        return needle in haystack

    def field_text(self, leaf: Leaf) -> str:
        path = leaf.path
        name = label_of(path)
        if leaf.is_container:
            return f"{name} (list)"
        prefix = self.context_prefix(path)
        return f"{prefix}{name}"

    def row_value(self, leaf: Leaf, value: Any) -> str:
        if not leaf.is_container and isinstance(value, int):
            if leaf.path[:-1] == ("storySystems", "activeCompanionIds"):
                name = COMPANION_NAMES.get(value)
                return f"{value}" + (f" ({name})" if name else "")
        if not leaf.is_container and isinstance(value, str):
            if leaf.path[:-1] == ("storySystems", "dungeonPartyNPCIds"):
                return f"{display_value(value)} ({self.npc_name_by_id(value)})"
        return display_value(value)

    def describe(self, leaf: Leaf) -> str:
        """One explanation for every row: curated, then the game's comment, then a direct gloss."""
        path = leaf.path
        if leaf.is_container:
            text = f"List \"{label_of(path)}\", with {leaf.list_length} items."
            if leaf.scalar_list:
                if path in FIXED_LISTS:
                    text += " This is a fixed-length list; you can only edit existing elements, not add or remove them."
                else:
                    text += "Every element is a simple value; select this row to add elements on the right."
                if path in PAIRED_LISTS:
                    text += f" It is paired with {path_text(PAIRED_LISTS[path])} and must correspond one-to-one."
            elif leaf.list_length == 0:
                text += " Empty list; the element type cannot be determined, so add/remove is unavailable here. Edit the JSON by hand instead."
            else:
                text += "Elements are objects; only existing elements can be edited here, not added or removed."
            return text

        part = path[-1]
        if isinstance(part, int):
            parent = path[-2] if len(path) > 1 else ""
            text = f"\"{label_of(path[:-1])}\" list, item {part + 1} items."
            if path[:-1] == ("player", "description"):
                return text + " One line of the player's appearance description."
            parent_note = FIELD_NOTES.get(str(parent))
            if parent_note:
                text += " " + parent_note
            return text

        key = str(part)
        parent = str(path[-2]) if len(path) > 1 else ""
        if not is_schema_key(key):
            if parent == "oldGodStates" and key.isdigit():
                name = OLD_GOD_NAMES.get(int(key))
                return f"Old God \"{name}\" state (enum integer)." if name else f"Old God number {key} state."
            if parent == "storyFlags":
                return f"Story flag \"{key}\": boolean; true means the flag is set."
            if parent == "playerGods":
                return f"Player \"{key}\" worships this god."
            if parent == "scores":
                return f"Archetype number {key} score."
            if parent == "npcRelationship":
                return f"Relationship with town-story NPC \"{key}\"."
            if parent == "relationships":
                return f"With \"{key}\" relationship data."
            return (f"Dictionary \"{LABELS.get(parent, parent)}\" key \"{key}\"."
                    "This is a name or identifier, not a field name; its value is interpreted according to the dictionary's meaning.")

        if key == "description":
            if path == ("player", "description"):
                return "The player's four-line appearance description (height, build, clothing and more); fixed length."
            if "memories" in path:
                return "Description text for this memory, recording the events the NPC remembers."
            return "Description text for this entry; its exact meaning depends on the containing object."

        note = FIELD_NOTES.get(key)
        if note:
            return note
        if key in LABELS:
            text = f"{LABELS[key]}: the raw value stored in the save."
        else:
            text = f"Literal: {mechanical_phrase(key)}."
        source = source_notes().get(key)
        if source:
            text += f"\nCode comment: {source}"
        return text

    def short_note(self, leaf: Leaf) -> str:
        note = self.describe(leaf).split("\n", 1)[0]
        return note if len(note) <= 110 else note[:109] + "…"

    def set_note(self, text: str) -> None:
        self.note.configure(state="normal")
        self.note.delete("1.0", "end")
        self.note.insert("1.0", text)
        self.note.configure(state="disabled")

    def context_prefix(self, path: tuple) -> str:
        if len(path) >= 3 and path[0] == "npCs" and isinstance(path[1], int):
            npcs = self.data.get("npCs") or []
            if 0 <= path[1] < len(npcs) and isinstance(npcs[path[1]], dict):
                return f"{npcs[path[1]].get('name', 'NPC')} · "
        if len(path) >= 3 and path[0] == "storySystems" and path[1] == "companions" \
                and isinstance(path[2], int):
            companions = self.story_systems().get("companions")
            companion_id = path[2]
            if isinstance(companions, list) and 0 <= path[2] < len(companions) \
                    and isinstance(companions[path[2]], dict):
                companion_id = companions[path[2]].get("id", path[2])
            name = COMPANION_NAMES.get(companion_id, f"#{companion_id}")
            return f"Companion {name} · "
        if len(path) == 2 and path[0] == "player":
            for group, keys in PLAYER_GROUPS:
                if path[1] in keys:
                    return f"{group} · "
        return ""

    def is_pending(self, leaf: Leaf) -> bool:
        return not leaf.is_container and leaf.path in self.pending

    def render(self) -> None:
        needle = self.search.get().strip().lower()
        leaves = self.section_leaves()
        if needle:
            leaves = [leaf for leaf in leaves if self.matches(leaf, needle)]
        self.rows = leaves[: self.MAX_ROWS]
        self.list.delete(*self.list.get_children())
        for position, leaf in enumerate(self.rows):
            value = display_value(self.pending[leaf.path]) if leaf.path in self.pending \
                else self.row_value(leaf, leaf.value)
            tags = []
            if leaf.is_container:
                tags.append("container")
                value = f"{leaf.list_length} items"
                kind = "list"
            else:
                kind = leaf.kind
                if leaf.path in self.pending:
                    tags.append("pending")
            self.list.insert("", "end", iid=str(position),
                             text=self.field_text(leaf),
                             values=(value, kind, self.short_note(leaf), path_text(leaf.path)),
                             tags=tuple(tags))
        hidden = len(leaves) - len(self.rows)
        if hidden > 0:
            self.say(f"Matched {len(leaves)} rows; showing the first {self.MAX_ROWS} rows. Narrow it down with search.")
        self.render_actions()

    def clear_search(self) -> None:
        self.search.delete(0, "end")
        self.render()

    # ---- editing ----------------------------------------------------------------------------------

    def selected_leaf(self) -> Leaf | None:
        selection = self.list.selection()
        if not selection:
            return None
        try:
            return self.rows[int(selection[0])]
        except (ValueError, IndexError):
            return None

    def show_selected(self) -> None:
        leaf = self.selected_leaf()
        if leaf is None:
            return
        self.field_label.configure(text=self.field_text(leaf))
        self.path_label.configure(text=path_text(leaf.path))
        note = self.describe(leaf)
        if not leaf.is_container:
            note += f"\nType: {TYPE_ZH.get(leaf.kind, leaf.kind)}"
        self.set_note(note)
        self.current_label.configure(text=(f"<list, {leaf.list_length} items>"
                                           if leaf.is_container else display_value(leaf.value, 400)))
        self.editor.delete("1.0", "end")
        editable = not leaf.is_container and is_editable(leaf.value)
        if leaf.is_container:
            self.editor.insert("1.0", "")
        elif is_editable(leaf.value):
            self.editor.insert("1.0", self.pending.get(leaf.path, show(leaf.value)))
        else:
            self.editor.insert("1.0", "(This field is null, so its type is unknown and it cannot be edited directly)")
        state = "normal" if editable else "disabled"
        self.editor.configure(state=state)
        self.apply_button.configure(state=state)
        self.revert_button.configure(state=state)
        self.bool_frame.pack_forget()
        if not leaf.is_container and leaf.kind == "bool":
            self.bool_frame.pack(fill="x", pady=(6, 0), after=self.apply_button.master)
        self.update_list_buttons(leaf)

    def update_list_buttons(self, leaf: Leaf | None) -> None:
        can_add = bool(leaf and leaf.is_container and leaf.scalar_list)
        can_delete = bool(leaf and not leaf.is_container and isinstance(leaf.path[-1], int)
                          and self.parent_is_scalar_list(leaf))
        self.add_button.configure(state="normal" if can_add else "disabled")
        self.delete_button.configure(state="normal" if can_delete else "disabled")

    def parent_is_scalar_list(self, leaf: Leaf) -> bool:
        try:
            parent = get_path(self.data, leaf.path[:-1])
        except (KeyError, IndexError, TypeError):
            return False
        return isinstance(parent, list) and all(not isinstance(x, (dict, list)) for x in parent)

    def set_editor(self, text: str) -> None:
        self.editor.configure(state="normal")
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", text)

    def stage_selected(self) -> None:
        leaf = self.selected_leaf()
        if leaf is None or leaf.is_container:
            return
        if not is_editable(leaf.value):
            self.say(f"{path_text(leaf.path)} is null, so its type is unknown and it cannot be edited directly.")
            return
        text = self.editor.get("1.0", "end-1c")
        try:
            validate_change(leaf.path, leaf.value, text)
        except ValueError as error:
            self.say(f"{path_text(leaf.path)}: {error}")
            return
        if text == show(leaf.value):
            self.pending.pop(leaf.path, None)
        else:
            self.pending[leaf.path] = text
        self.render()
        self.select_path(leaf.path)
        self.update_change_count()
        self.say(f"{path_text(leaf.path)} staged as new value {display_value(text)} (not written to the file yet)")

    def revert_selected(self) -> None:
        leaf = self.selected_leaf()
        if leaf is None or leaf.is_container:
            return
        self.pending.pop(leaf.path, None)
        self.render()
        self.select_path(leaf.path)
        self.update_change_count()
        self.say(f"{path_text(leaf.path)} reverted to the value in the save.")

    def select_path(self, path: tuple) -> None:
        for position, leaf in enumerate(self.rows):
            if leaf.path == path:
                iid = str(position)
                self.list.selection_set(iid)
                self.list.see(iid)
                self.show_selected()
                return

    def update_change_count(self) -> None:
        if self.has_changes():
            parts = []
            if self.pending:
                parts.append(f"{len(self.pending)} value changes")
            if self.dirty:
                parts.append("list/companion changes")
            self.change_count.configure(text="Unsaved: " + ", ".join(parts), foreground="#b45309")
            self.save_button.configure(text="Save All Changes")
        else:
            self.change_count.configure(text="No unsaved changes", foreground="#555")
            self.save_button.configure(text="Save All Changes")

    # ---- quick actions (the G editor's category operations) ---------------------------------------

    def player(self) -> dict:
        player = self.data.get("player")
        if not isinstance(player, dict):
            player = {}
            self.data["player"] = player
        return player

    def actions_for_section(self) -> list[tuple[str, object]]:
        section = self.current_section()
        if section == "inventory":
            return [("Add Item from Template", self.act_pick_inventory_item),
                    ("Equip Item from Template", self.act_equip_template_item),
                    ("Add Item (JSON)", self.act_add_inventory_item),
                    ("Delete Selected Item", self.act_remove_selected_inventory),
                    ("Clear Inventory", self.act_clear_inventory),
                    ("Clear Equipment", self.act_clear_equipment),
                    ("Remove Equipment Curses", self.act_uncurse_equipment)]
        if section == "spells":
            return [("Learn Ability by ID", self.act_learn_ability),
                    ("Learn All", self.act_learn_all_spells),
                    ("Master All", self.act_master_all_spells),
                    ("Clear Spells", self.act_clear_spells),
                    ("Clear Learned Abilities", self.act_clear_abilities),
                    ("Clear Quickbar", self.act_clear_quickbar)]
        if section == "companions":
            return [("Revive All Companions", self.act_revive_companions),
                    ("Companion Manager", self.open_companion_manager),
                    ("Dungeon Party", self.open_party_manager)]
        if section == "quests":
            return [("Mark All Complete", self.act_complete_quests),
                    ("Mark All Abandoned", self.act_abandon_quests),
                    ("Clear Quests", self.act_clear_quests)]
        if section == "story":
            return [("Set Old God State", self.act_set_old_god),
                    ("Grant Artifact", self.act_grant_artifact),
                    ("Grant All Seals", self.act_grant_seals),
                    ("Clear Seals", self.act_clear_seals),
                    ("Set NG+ Cycle", self.act_set_cycle),
                    ("Clear Story Flags", self.act_clear_story_flags)]
        if section == "relationships":
            return [("Set Relationship Score", self.act_set_relationship),
                    ("Clear All Relationships", self.act_clear_relationships),
                    ("Clear Divine Wrath", self.act_clear_divine_wrath)]
        if section == "status":
            return [("Cure Diseases", self.act_cure_diseases),
                    ("Clear Poison", self.act_clear_poison),
                    ("Clear Drugs", self.act_clear_drugs),
                    ("Clear Status Effects", self.act_clear_statuses),
                    ("Release from Prison", self.act_release_prison),
                    ("Clear Wanted Level", self.act_clear_wanted),
                    ("Clear Murder Weight", self.act_clear_murder),
                    ("Clear Timed Buffs", self.act_clear_buffs),
                    ("Reset Daily Counters", self.act_reset_daily)]
        if section == "training":
            return [("Set Skill Proficiency", self.act_set_skill),
                    ("Clear Skill Proficiencies", self.act_clear_skills),
                    ("Clear Stat Training", self.act_clear_stat_training),
                    ("Add Crafting Material", self.act_add_material),
                    ("Clear Crafting Materials", self.act_clear_materials)]
        if section == "team":
            return [("Clear Team Info", self.act_clear_team)]
        return []

    def render_actions(self) -> None:
        for child in self.action_bar.winfo_children():
            child.destroy()
        actions = self.actions_for_section()
        if not actions:
            return
        self.ttk.Label(self.action_bar, text="Quick actions: ", foreground="#555").pack(side="left")
        for label, command in actions:
            self.ttk.Button(self.action_bar, text=label, command=command).pack(side="left", padx=(4, 0))

    def run_quick(self, label: str, action, confirm: str | None = None) -> None:
        if not self.data:
            self.say("Select a save first.")
            return
        if not self.structural_allowed():
            return
        if confirm and not self.messagebox.askyesno("Confirm Action", confirm, parent=self.root):
            return
        try:
            message = action()
        except Exception as error:
            self.say(f"{label} failed: {error}")
            return
        if message is None:
            return
        self.dirty = True
        self.rebuild_view()
        self.say(message)

    def act_pick_inventory_item(self) -> str | None:
        from save_editor_lib.item_picker import pick_item, to_inventory
        row = pick_item(self.root, "en")
        if row is None:
            return None
        player = self.player()
        inventory = player.get("inventory")
        if not isinstance(inventory, list):
            inventory = []
            player["inventory"] = inventory
        inventory.append(to_inventory(row))
        return f"Added {row['nameEn']}. The inventory now holds {len(inventory)} items."

    def act_equip_template_item(self) -> str | None:
        from save_editor_lib.item_picker import pick_item
        row = pick_item(self.root, "en")
        if row is None:
            return None
        player = self.player()
        equipped = player.get("equippedItems")
        if not isinstance(equipped, dict):
            equipped = {}
            player["equippedItems"] = equipped
        equipped[str(row["slotInt"])] = row["id"]
        return f"Equipped {row['nameEn']} in {row['slot']} (ID {row['id']})."

    def act_add_inventory_item(self) -> str | None:
        text = self.simpledialog.askstring(
            "Add Item", "Paste an item JSON object (one line):", parent=self.root,
            initialvalue='{"name": "New Item", "type": 0, "value": 0}')
        if not text:
            return None
        try:
            item = json.loads(text)
        except json.JSONDecodeError as error:
            return f"Invalid JSON: {error}"
        if not isinstance(item, dict):
            return "The item must be a JSON object."
        player = self.player()
        inventory = player.get("inventory")
        if not isinstance(inventory, list):
            inventory = []
            player["inventory"] = inventory
        inventory.append(item)
        return f"Added item \"{item.get('name', '?')}\"; the inventory now holds {len(inventory)} items."

    def act_remove_selected_inventory(self) -> str | None:
        leaf = self.selected_leaf()
        if leaf is None:
            return "Select an item in the inventory first."
        path = leaf.path
        if len(path) < 3 or path[0] != "player" or path[1] != "inventory" or not isinstance(path[2], int):
            return "Select an item from the inventory list."
        inventory = self.player().get("inventory")
        if not isinstance(inventory, list) or path[2] >= len(inventory):
            return "Invalid inventory index."
        item = inventory[path[2]]
        name = item.get("name", "?") if isinstance(item, dict) else "?"
        if not self.messagebox.askyesno("Delete Item", f"Delete \"{name}\" from the inventory?", parent=self.root):
            return None
        del inventory[path[2]]
        return f"Deleted \"{name}\"."

    def act_learn_ability(self) -> str | None:
        name = self.simpledialog.askstring("Learn Ability", "Class ability ID (for example power_strike):", parent=self.root)
        if not name:
            return None
        player = self.player()
        abilities = player.get("learnedAbilities")
        if not isinstance(abilities, list):
            abilities = []
            player["learnedAbilities"] = abilities
        if name in abilities:
            return f"{name} is already learned."
        abilities.append(name)
        return f"Learned {name}."

    def act_set_old_god(self) -> str | None:
        god = self.simpledialog.askinteger(
            "Set Old God State", "Old God number (0 Maelketh through 6 Manwe):", parent=self.root,
            initialvalue=0, minvalue=0, maxvalue=6)
        if god is None:
            return None
        status = self.simpledialog.askinteger(
            "Old God State", "Status integer: 0 Unknown, 1 Imprisoned, 2 Dormant, 3 Dying, 4 Corrupted,"
                       "5 Neutral, 6 Awakened, 7 Hostile, 8 Allied, 9 Saved, 10 Defeated, 11 Consumed",
            parent=self.root, initialvalue=2, minvalue=0, maxvalue=11)
        if status is None:
            return None
        states = self.story_systems().get("oldGodStates")
        if not isinstance(states, dict):
            states = {}
            self.story_systems()["oldGodStates"] = states
        states[str(god)] = status
        return f"Old God {god} state set to {status}. Note that the game does not enforce Old God prerequisites."

    def act_grant_artifact(self) -> str | None:
        artifact = self.simpledialog.askinteger(
            "Grant Artifact", "Artifact number: 0 The Creator's Eye, 1 The Soulweaver's Loom, 2 The Scales of Absolute Law, 3 The Shadow Crown,"
                       "4 The Sunforged Blade, 5 The Worldstone, 6 The Void Key:", parent=self.root,
            initialvalue=0, minvalue=0, maxvalue=6)
        if artifact is None:
            return None
        systems = self.story_systems()
        artifacts = systems.get("collectedArtifacts")
        if not isinstance(artifacts, list):
            artifacts = []
            systems["collectedArtifacts"] = artifacts
        if artifact not in artifacts:
            artifacts.append(artifact)
        return f"Granted artifact {artifact}."

    def act_clear_inventory(self) -> str | None:
        player = self.player()
        count = len(player.get("inventory") or [])
        if not self.messagebox.askyesno("Clear Inventory", f"Clear all {count} items from the inventory?", parent=self.root):
            return None
        player["inventory"] = []
        return f"Cleared the inventory ({count} items)."

    def act_clear_equipment(self) -> str | None:
        player = self.player()
        count = len(player.get("equippedItems") or {})
        if not self.messagebox.askyesno("Clear Equipment", f"Unequip and clear {count} equipment slots?", parent=self.root):
            return None
        player["equippedItems"] = {}
        player["dynamicEquipment"] = []
        return f"Cleared equipment ({count} slots)."

    def act_uncurse_equipment(self) -> str:
        player = self.player()
        for key in ("weaponCursed", "armorCursed", "shieldCursed"):
            if key in player:
                player[key] = False
        return "Cleared the curse flags on weapon, armor and shield."

    def spell_rows(self) -> list:
        rows = self.player().get("spells")
        if not isinstance(rows, list):
            rows = []
            self.player()["spells"] = rows
        return rows

    def set_spell_state(self, known: bool | None, mastered: bool | None) -> int:
        count = 0
        for row in self.spell_rows():
            if isinstance(row, list) and len(row) >= 2:
                if known is not None:
                    row[0] = known
                if mastered is not None:
                    row[1] = mastered
                count += 1
        return count

    def act_learn_all_spells(self) -> str:
        count = self.set_spell_state(True, None)
        return f"Marked {count} spell records as learned."

    def act_master_all_spells(self) -> str:
        count = self.set_spell_state(True, True)
        return f"Marked {count} spell records as mastered."

    def act_clear_spells(self) -> str | None:
        if not self.messagebox.askyesno("Clear Spells", "Forget all spells?", parent=self.root):
            return None
        count = self.set_spell_state(False, False)
        return f"Cleared {count} spell records."

    def act_clear_abilities(self) -> str | None:
        player = self.player()
        count = len(player.get("learnedAbilities") or [])
        if not self.messagebox.askyesno("Clear Abilities", f"Remove all {count} learned class abilities?", parent=self.root):
            return None
        player["learnedAbilities"] = []
        return f"Removed {count} learned class abilities."

    def act_clear_quickbar(self) -> str | None:
        player = self.player()
        bar = player.get("quickbar")
        if not isinstance(bar, list):
            return "The quickbar field is missing or is not a list."
        if not self.messagebox.askyesno("Clear Quickbar", "Clear all 9 quickbar slots?", parent=self.root):
            return None
        bar[:] = [None] * len(bar)
        return "Quickbar cleared (slot count unchanged)."

    def act_revive_companions(self) -> str:
        return self.revive_companions()

    def quest_list(self) -> list:
        player = self.player()
        quests = player.get("activeQuests")
        if not isinstance(quests, list):
            quests = []
            player["activeQuests"] = quests
        return quests

    def set_quest_status(self, status: int) -> int:
        count = 0
        for quest in self.quest_list():
            if isinstance(quest, dict):
                quest["status"] = status
                count += 1
        return count

    def act_complete_quests(self) -> str:
        count = self.set_quest_status(1)
        return f"Marked {count} quests as complete."

    def act_abandon_quests(self) -> str:
        count = self.set_quest_status(3)
        return f"Marked {count} quests as abandoned."

    def act_clear_quests(self) -> str | None:
        count = len(self.quest_list())
        if not self.messagebox.askyesno("Clear Quests", f"Remove all {count} quests from the save?", parent=self.root):
            return None
        self.player()["activeQuests"] = []
        return f"Removed {count} quests."

    def act_grant_seals(self) -> str:
        self.story_systems()["collectedSeals"] = [1, 2, 3, 4, 5, 6, 7]
        return "Granted all 7 seals."

    def act_clear_seals(self) -> str | None:
        if not self.messagebox.askyesno("Clear Seals", "Clear all collected seals?", parent=self.root):
            return None
        self.story_systems()["collectedSeals"] = []
        return "Seals cleared."

    def act_set_cycle(self) -> str | None:
        value = self.simpledialog.askinteger(
            "NG+ Cycle", "New cycle number (starting at 1):", parent=self.root, initialvalue=1, minvalue=1, maxvalue=99)
        if value is None:
            return None
        self.story_systems()["currentCycle"] = value
        if value > 1 and self.messagebox.askyesno(
                "Set the XP multiplier too?",
                f"Set CycleExpMultiplier to {1.0 + (value - 1) * 0.25:.2f}x?\n"
                "Without it, higher cycles add difficulty without the matching XP reward.", parent=self.root):
            self.player()["cycleExpMultiplier"] = 1.0 + (value - 1) * 0.25
        return f"NG+ cycle set to {value}."

    def act_clear_story_flags(self) -> str | None:
        if not self.messagebox.askyesno(
                "Clear Story Flags", "This clears StoryFlags and may unlock or re-block story progress. Are you sure?", parent=self.root):
            return None
        self.story_systems()["storyFlags"] = {}
        return "Story flags cleared."

    def act_set_relationship(self) -> str | None:
        name = self.simpledialog.askstring("Set Relationship", "Exact NPC name:", parent=self.root)
        if not name:
            return None
        value = self.simpledialog.askfloat(
            "Relationship Score", f"Relationship score with {name} (typically -100 to 100):", parent=self.root, initialvalue=0.0)
        if value is None:
            return None
        player = self.player()
        relationships = player.get("relationships")
        if not isinstance(relationships, dict):
            relationships = {}
            player["relationships"] = relationships
        relationships[name] = value
        return f"{name} relationship score set to {value:g}."

    def act_clear_relationships(self) -> str | None:
        player = self.player()
        count = len(player.get("relationships") or {})
        if not self.messagebox.askyesno("Clear Relationships", f"Clear all {count} NPC relationship scores?", parent=self.root):
            return None
        player["relationships"] = {}
        return f"Cleared {count} relationships."

    def act_clear_divine_wrath(self) -> str:
        player = self.player()
        player["divineWrathLevel"] = 0
        player["divineWrathPending"] = False
        player["divineWrathTurnsRemaining"] = 0
        player["angeredGodName"] = ""
        player["betrayedForGodName"] = ""
        return "Divine wrath cleared."

    def act_cure_diseases(self) -> str:
        player = self.player()
        keys = [key for key in ("blind", "plague", "smallpox", "measles", "leprosy", "loversBane")
                if key in player]
        for key in keys:
            player[key] = False
        return "All diseases cured." if keys else "The save has no disease fields."

    def act_clear_poison(self) -> str:
        player = self.player()
        player["poison"] = 0
        player["poisonTurns"] = 0
        if "gnollP" in player:
            player["gnollP"] = 0
        return "Poison cleared."

    def act_clear_drugs(self) -> str:
        player = self.player()
        for key in ("addict", "steroidDays", "drugEffectDays", "activeDrug"):
            if key in player:
                player[key] = 0
        return "Drug addiction and steroid effects cleared."

    def act_clear_statuses(self) -> str:
        player = self.player()
        player["activeStatuses"] = {}
        return "All active status effects cleared."

    def act_release_prison(self) -> str:
        player = self.player()
        player["daysInPrison"] = 0
        player["isMurderConvict"] = False
        player["cellDoorOpen"] = False
        player["prisonEscapes"] = 3
        return "Released from prison."

    def act_clear_wanted(self) -> str:
        self.player()["wantedLvl"] = 0
        return "Wanted level reset to 0."

    def act_clear_murder(self) -> str:
        player = self.player()
        player["murderWeight"] = 0
        player["permakillLog"] = []
        return "Murder weight and permakill log cleared."

    def act_clear_buffs(self) -> str | None:
        if not self.messagebox.askyesno("Clear Timed Buffs", "Clear all timed stat buffs and Groggo's blessing?", parent=self.root):
            return None
        player = self.player()
        player["timedStatBuffs"] = []
        player["groggoShadowBlessingDex"] = 0
        return "Timed stat buffs cleared."

    def act_reset_daily(self) -> str | None:
        if not self.messagebox.askyesno(
                "Reset Daily Counters", "Reset daily counters such as fights, thefts, brawls and dungeon events to a new day?", parent=self.root):
            return None
        player = self.player()
        for key, value in (("fights", 5), ("pFights", 3), ("tFights", 2),
                           ("thiefs", 3), ("brawls", 3), ("assa", 3)):
            if key in player:
                player[key] = value
        for key in ("murdersToday", "executionsToday", "npcsImprisonedToday",
                    "bankRobberyAttempts", "templeResurrectionsUsed", "reforgesToday", "sparesToday",
                    "teamWarsToday", "drinkingGamesToday", "loveStreetVisitsToday",
                    "intimateEncountersToday", "gauntletRunsToday", "tributeDemandsToday",
                    "mercContractsClaimedToday", "almsGivenToday", "orphanageGiftsToday",
                    "hospiceTithesToday", "confessionsToday", "desecrationsToday",
                    "gamblingRoundsToday", "innDuelsToday", "pitFightsToday", "armWrestlesToday",
                    "mealsToday", "prisonActivitiesToday", "wildernessExplorationsToday",
                    "wildernessRevisitsToday", "sethFightsToday", "royQuestsToday"):
            if key in player and isinstance(player[key], int):
                player[key] = 0
        for key in ("throneChallengedToday", "playerImprisonedToday", "freeBlessingClaimedToday",
                    "jailbreakAttemptedToday", "miracleUsedToday", "settlementCircleUsedToday",
                    "settlementGoldClaimedToday", "settlementHerbClaimedToday",
                    "settlementShrineUsedToday", "settlementWorkshopUsedToday",
                    "tavernStrangerTalkedToday", "marshToadAntidoteClaimedToday"):
            if key in player:
                player[key] = False
        for key in ("dailyMercStandingGain", "chastisedToday"):
            if key in player:
                player[key] = {} if isinstance(player[key], dict) else []
        return "Daily counters reset."

    def act_set_skill(self) -> str | None:
        name = self.simpledialog.askstring("Set Skill", "Skill ID (for example sword, stealth):", parent=self.root)
        if not name:
            return None
        level = self.simpledialog.askinteger(
            "Skill Level", f"{name} proficiency (0 Untrained to 8 Legendary):", parent=self.root,
            initialvalue=0, minvalue=0, maxvalue=8)
        if level is None:
            return None
        player = self.player()
        skills = player.get("skillProficiencies")
        if not isinstance(skills, dict):
            skills = {}
            player["skillProficiencies"] = skills
        skills[name] = level
        return f"{name} proficiency set to {level}."

    def act_clear_skills(self) -> str | None:
        player = self.player()
        count = len(player.get("skillProficiencies") or {})
        if not self.messagebox.askyesno("Clear Skill Proficiencies", f"Clear all {count} skill proficiencies?", parent=self.root):
            return None
        player["skillProficiencies"] = {}
        return f"Cleared {count} skill proficiencies."

    def act_clear_stat_training(self) -> str | None:
        player = self.player()
        count = len(player.get("statTrainingCounts") or {})
        if not self.messagebox.askyesno("Clear Stat Training", f"Clear all {count} stat training counts?", parent=self.root):
            return None
        player["statTrainingCounts"] = {}
        return f"Cleared {count} stat training counts."

    def act_add_material(self) -> str | None:
        name = self.simpledialog.askstring("Add Material", "Material name:", parent=self.root)
        if not name:
            return None
        quantity = self.simpledialog.askinteger(
            "Add Material", f"{name} quantity:", parent=self.root, initialvalue=1, minvalue=1, maxvalue=999999)
        if quantity is None:
            return None
        player = self.player()
        materials = player.get("craftingMaterials")
        if not isinstance(materials, dict):
            materials = {}
            player["craftingMaterials"] = materials
        materials[name] = materials.get(name, 0) + quantity
        return f"Increased {name} to {materials[name]}."

    def act_clear_materials(self) -> str | None:
        player = self.player()
        count = len(player.get("craftingMaterials") or {})
        if not self.messagebox.askyesno("Clear Crafting Materials", f"Clear all {count} crafting materials?", parent=self.root):
            return None
        player["craftingMaterials"] = {}
        return f"Cleared {count} crafting materials."

    def act_clear_team(self) -> str | None:
        if not self.messagebox.askyesno("Clear Team Info", "Leave the team and clear the team name, password and leader flag?", parent=self.root):
            return None
        player = self.player()
        player["team"] = ""
        player["teamPassword"] = ""
        player["isTeamLeader"] = False
        player["teamRec"] = 0
        return "Team info cleared."

    # ---- list tools -------------------------------------------------------------------------------

    def empty_list_kind(self, path: tuple) -> str | None:
        """The type an empty list holds, for the lists the game schema pins down."""
        return EMPTY_SCALAR_LISTS.get(path)

    def list_edit_blocked(self, path: tuple) -> str | None:
        if path in FIXED_LISTS:
            return "This list has a fixed length and cannot gain or lose elements; you can edit existing elements directly."
        return None

    def confirm_paired(self, path: tuple) -> bool:
        mate = PAIRED_LISTS.get(path)
        if mate is None:
            return True
        return bool(self.messagebox.askyesno(
            "Paired Lists",
            f"{path_text(path)} and {path_text(mate)} must correspond one-to-one.\n"
            "Editing only one side misaligns items and types and can even make the save fail to load. Continue?",
            parent=self.root))

    def check_list_addition(self, path: tuple, value: Any) -> str | None:
        """Refuse a list element the game would not accept, before it reaches the file."""
        if path == ACTIVE_COMPANIONS_PATH:
            if not isinstance(value, int) or isinstance(value, bool):
                return "Active companion IDs must be integers."
            if value not in COMPANION_NAMES:
                return "Companion IDs must be 0-4 (Lyris, Aldric, Mira, Vex, Melodia)."
            if value in self.active_ids():
                return "This companion is already in the active party."
            if len(self.active_ids()) >= MAX_ACTIVE_COMPANIONS:
                return f"At most {MAX_ACTIVE_COMPANIONS} active companions."
            entry = self.companion_entry(value)
            if entry and entry.get("isDead"):
                return "This companion is dead; revive them in the Companion Manager first."
        if path == DUNGEON_PARTY_PATH:
            if not isinstance(value, str):
                return "Dungeon party NPC IDs must be text."
            if value in self.party_ids():
                return "This NPC is already in the party."
            if len(self.party_ids()) >= MAX_DUNGEON_PARTY:
                return f"The dungeon party holds at most {MAX_DUNGEON_PARTY} members."
            npc = next((n for n in self.npc_roster() if n.get("id") == value), None)
            if npc is None:
                return "This ID is not in the NPC roster."
            if npc.get("isDead"):
                return "This NPC is dead; revive them before adding them to the party."
        return None

    def after_list_add(self, path: tuple, value: Any) -> None:
        if path == ACTIVE_COMPANIONS_PATH:
            entry = self.companion_entry(value, create=True)
            assert entry is not None
            entry["isRecruited"] = True
            entry["isActive"] = True

    def after_list_remove(self, path: tuple, value: Any) -> None:
        if path == ACTIVE_COMPANIONS_PATH:
            entry = self.companion_entry(value)
            if entry is not None:
                entry["isActive"] = False

    def add_to_list(self) -> None:
        leaf = self.selected_leaf()
        if leaf is None or not leaf.is_container or not leaf.scalar_list:
            return
        if not self.structural_allowed():
            return
        blocked = self.list_edit_blocked(leaf.path)
        if blocked:
            self.say(blocked)
            return
        if not self.confirm_paired(leaf.path):
            return
        try:
            value = self.ask_new_element(leaf)
        except ValueError as error:
            self.say(f"Not added: {error}")
            return
        if value is _CANCELLED:
            return
        refusal = self.check_list_addition(leaf.path, value)
        if refusal:
            self.say(f"Not added: {refusal}")
            return
        try:
            list_add(self.data, leaf.path, value)
        except (KeyError, TypeError, ValueError) as error:
            self.say(f"Not added: {error}")
            return
        self.after_list_add(leaf.path, value)
        self.dirty = True
        self.rebuild_view()
        self.select_path(leaf.path)
        self.update_change_count()
        self.say(f"{path_text(leaf.path)}: appended {show(value)} (not written to the file yet)")

    def ask_new_element(self, leaf: Leaf) -> Any:
        tk = self.tk
        ttk = self.ttk
        from tkinter import simpledialog

        if leaf.element_kind in ("int", "float", "bool"):
            text = simpledialog.askstring("Add Element", f"Add a {leaf.element_kind} to "
                                          f"{path_text(leaf.path)}: ", parent=self.root)
            if text is None:
                return _CANCELLED
            sample = {"int": 0, "float": 0.0, "bool": False}[leaf.element_kind]
            return coerce(sample, text)

        if leaf.list_length > 0:
            text = simpledialog.askstring("Add Element", f"Add text to {path_text(leaf.path)}: ",
                                          parent=self.root)
            if text is None:
                return _CANCELLED
            return text

        # An empty list has no element to copy the type from, so ask which type it holds.
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Element")
        dialog.transient(self.root)
        dialog.grab_set()
        ttk.Label(dialog, text=f"{path_text(leaf.path)} is now empty. What type is the new element?",
                  padding=10).pack()
        kind_box = ttk.Combobox(dialog, state="readonly", values=["Text", "Integer", "Decimal", "Boolean"])
        known = self.empty_list_kind(leaf.path)
        kind_box.current({"int": 1, "float": 2, "bool": 3}.get(known or "", 0))
        kind_box.pack(fill="x", padx=10)
        value_entry = ttk.Entry(dialog)
        value_entry.pack(fill="x", padx=10, pady=6)
        result: list[Any] = []

        def okay() -> None:
            kind = kind_box.get()
            text = value_entry.get()
            try:
                if kind == "Integer":
                    result.append(int(text.strip()))
                elif kind == "Decimal":
                    result.append(float(text.strip()))
                elif kind == "Boolean":
                    result.append(coerce(False, text))
                else:
                    result.append(text)
            except ValueError as error:
                ttk.Label(dialog, text=str(error), foreground="#b91c1c").pack()
                return
            dialog.destroy()

        ttk.Button(dialog, text="Add", command=okay).pack(pady=(0, 10))
        self.root.wait_window(dialog)
        return result[0] if result else _CANCELLED

    def delete_from_list(self) -> None:
        leaf = self.selected_leaf()
        if leaf is None or leaf.is_container or not isinstance(leaf.path[-1], int):
            return
        if not self.parent_is_scalar_list(leaf):
            return
        if not self.structural_allowed():
            return
        list_path = leaf.path[:-1]
        blocked = self.list_edit_blocked(list_path)
        if blocked:
            self.say(blocked)
            return
        if not self.confirm_paired(list_path):
            return
        index = leaf.path[-1]
        if not self.messagebox.askyesno(
                "Delete Element", f"Delete item {index} ({display_value(leaf.value)}) from {path_text(list_path)}?",
                parent=self.root):
            return
        try:
            removed = list_remove(self.data, list_path, index)
        except (KeyError, TypeError, ValueError) as error:
            self.say(f"Not deleted: {error}")
            return
        self.after_list_remove(list_path, removed)
        self.dirty = True
        self.rebuild_view()
        self.select_path(list_path)
        self.update_change_count()
        self.say(f"{path_text(list_path)}: deleted item {index} ({show(removed)}); not written to the file yet")

    def structural_allowed(self) -> bool:
        if self.pending:
            self.say("There are unsaved value changes. Click \"Save All Changes\" or \"Reload\" to discard them before editing lists.")
            return False
        return True

    # ---- companion manager ------------------------------------------------------------------------

    def open_companion_manager(self) -> None:
        if not self.structural_allowed():
            return
        CompanionManager(self)

    def story_systems(self) -> dict:
        systems = self.data.get("storySystems")
        if not isinstance(systems, dict):
            systems = {}
            self.data["storySystems"] = systems
        return systems

    def companion_entries(self) -> list[dict]:
        systems = self.story_systems()
        entries = systems.get("companions")
        if not isinstance(entries, list):
            entries = []
            systems["companions"] = entries
        return entries

    def companion_entry(self, companion_id: int, create: bool = False) -> dict | None:
        for entry in self.companion_entries():
            if isinstance(entry, dict) and entry.get("id") == companion_id:
                return entry
        if not create:
            return None
        entry = {"id": companion_id, "isRecruited": False, "isActive": False, "isDead": False,
                 "loyaltyLevel": 50, "trustLevel": 50, "romanceLevel": 0, "level": 1,
                 "experience": 0, "healingPotions": 0, "manaPotions": 0}
        self.companion_entries().append(entry)
        return entry

    def active_ids(self) -> list[int]:
        systems = self.story_systems()
        ids = systems.get("activeCompanionIds")
        if not isinstance(ids, list):
            ids = []
            systems["activeCompanionIds"] = ids
        return ids

    def drop_fallen(self, companion_id: int) -> None:
        systems = self.story_systems()
        for key in ("fallenCompanions", "activeGriefs", "griefMemories"):
            entries = systems.get(key)
            if isinstance(entries, list):
                entries[:] = [entry for entry in entries
                              if not (isinstance(entry, dict) and entry.get("companionId") == companion_id)]

    def set_companion_active(self, companion_id: int, active: bool) -> str:
        entry = self.companion_entry(companion_id, create=True)
        assert entry is not None
        ids = self.active_ids()
        if active:
            if entry.get("isDead"):
                return "This companion is dead; click \"Revive\" or \"Recruit\" first."
            if not entry.get("isRecruited"):
                return "This companion is not recruited yet; click \"Recruit\" first."
            if companion_id not in ids and len(ids) >= MAX_ACTIVE_COMPANIONS:
                return f"At most {MAX_ACTIVE_COMPANIONS} active companions; rest one first."
            if companion_id not in ids:
                ids.append(companion_id)
            entry["isActive"] = True
        else:
            if companion_id in ids:
                ids.remove(companion_id)
            entry["isActive"] = False
        self.dirty = True
        self.rebuild_view()
        return f"{COMPANION_NAMES.get(companion_id, companion_id)} is now {'active' if active else 'resting'}."

    def set_companion_recruited(self, companion_id: int, recruited: bool) -> str:
        entry = self.companion_entry(companion_id, create=True)
        assert entry is not None
        if recruited:
            entry["isRecruited"] = True
            entry["isDead"] = False
            self.drop_fallen(companion_id)
            self.dirty = True
            self.rebuild_view()
            return f"Recruited {COMPANION_NAMES.get(companion_id, companion_id)}."
        entry["isRecruited"] = False
        entry["isActive"] = False
        ids = self.active_ids()
        if companion_id in ids:
            ids.remove(companion_id)
        self.dirty = True
        self.rebuild_view()
        return f"Dismissed {COMPANION_NAMES.get(companion_id, companion_id)}."

    def revive_companions(self) -> str:
        revived = []
        for entry in self.companion_entries():
            if isinstance(entry, dict) and entry.get("isDead"):
                entry["isDead"] = False
                revived.append(entry.get("id"))
                self.drop_fallen(entry.get("id"))
        if revived:
            self.dirty = True
            self.rebuild_view()
            return "Revived: " + ", ".join(COMPANION_NAMES.get(i, str(i)) for i in revived)
        return "No companions have fallen."

    # ---- dungeon party manager --------------------------------------------------------------------

    def open_party_manager(self) -> None:
        if not self.structural_allowed():
            return
        PartyManager(self)

    def npc_roster(self) -> list[dict]:
        npcs = self.data.get("npCs")
        return [npc for npc in npcs if isinstance(npc, dict)] if isinstance(npcs, list) else []

    def npc_name_by_id(self, npc_id: str) -> str:
        for npc in self.npc_roster():
            if npc.get("id") == npc_id:
                return str(npc.get("name") or npc_id)
        return npc_id

    def party_ids(self) -> list[str]:
        systems = self.story_systems()
        ids = systems.get("dungeonPartyNPCIds")
        if not isinstance(ids, list):
            ids = []
            systems["dungeonPartyNPCIds"] = ids
        return ids

    def add_party_npc(self, npc_id: str) -> str:
        ids = self.party_ids()
        if npc_id in ids:
            return "This NPC is already in the party."
        if len(ids) >= MAX_DUNGEON_PARTY:
            return f"The dungeon party holds at most {MAX_DUNGEON_PARTY} members."
        npc = next((n for n in self.npc_roster() if n.get("id") == npc_id), None)
        if npc is None:
            return "This ID is not in the NPC roster."
        if npc.get("isDead"):
            return "This NPC is dead; revive them before adding them to the party."
        ids.append(npc_id)
        self.dirty = True
        self.rebuild_view()
        return f"Added {npc.get('name')} to the dungeon party."

    def remove_party_npc(self, npc_id: str) -> str:
        ids = self.party_ids()
        if npc_id not in ids:
            return "That NPC is not in the party."
        ids.remove(npc_id)
        self.dirty = True
        self.rebuild_view()
        return f"Removed {self.npc_name_by_id(npc_id)} from the dungeon party."

    def clear_party(self) -> str:
        ids = self.party_ids()
        if not ids:
            return "The dungeon party is already empty."
        count = len(ids)
        ids.clear()
        self.dirty = True
        self.rebuild_view()
        return f"Cleared the dungeon party ({count} members)."

    # ---- G editor tools: save management, summary, paths ------------------------------------------

    def open_save_manager(self) -> None:
        if self.has_changes() and not self.confirm_discard():
            return
        SaveManagerWindow(self)

    def open_game_data(self) -> None:
        GameDataWindow(self)

    def show_paths(self) -> None:
        exe = game_executable()
        lines = [
            f"Save directory: {self.directory}",
            f"GameData directory: {game_data_directory()}",
            f"Game executable: {exe if exe else 'Not found'}",
            f"Source directory: {find_repo_root() or 'Not found'}",
        ]
        self.messagebox.showinfo("File Locations", "\n".join(lines), parent=self.root)

    def show_summary(self) -> None:
        if not self.data:
            self.say("Select a save first.")
            return
        player = self.data.get("player") or {}
        story = self.data.get("storySystems") or {}
        lines = [
            f"Save: {self.save_path.name if self.save_path else '?'}",
            f"Character: {player.get('name2') or player.get('name1')}  Lv.{player.get('level')}",
            f"Class / Race: {player.get('class')} / {player.get('race')}",
            f"HP: {player.get('hp')} / {player.get('maxHP')}    Mana: {player.get('mana')} / {player.get('maxMana')}",
            f"Gold: {player.get('gold')}    Bank: {player.get('bankGold')}",
            f"Stats: STR {player.get('strength')}  DEX {player.get('dexterity')}  CON {player.get('constitution')}  INT {player.get('intelligence')}  WIS {player.get('wisdom')}  CHA {player.get('charisma')}",
            f"Items: {len(player.get('inventory') or [])}    Equipped slots: {len(player.get('equippedItems') or {})}",
            f"Quests: {len(player.get('activeQuests') or [])}    Abilities: {len(player.get('learnedAbilities') or [])}    Spell slots: {len(player.get('spells') or [])}",
            f"Companions: {len(story.get('companions') or [])}    Seals: {len(story.get('collectedSeals') or [])}/7    Artifacts: {len(story.get('collectedArtifacts') or [])}",
            f"NG+ cycle: {story.get('currentCycle')}",
        ]
        self.messagebox.showinfo("Save Summary", "\n".join(lines), parent=self.root)

    # ---- saving -----------------------------------------------------------------------------------

    def save(self) -> None:
        if not self.save_path:
            return
        if not self.has_changes():
            self.say("No changes.")
            return

        # Work on a copy so a refused edit or a failed write never leaves the window out of step
        # with the file on disk.
        try:
            working = json.loads(json.dumps(self.data, ensure_ascii=False))
        except (TypeError, ValueError) as error:
            self.say(f"Not saved: the save contains a value that cannot be written back to JSON ({error})")
            return

        applied: list[str] = []
        if self.pending:
            applied, refused = apply_changes(working, self.pending)
            if refused:
                self.say("Not saved; fix these values first:\n" + "\n".join(refused))
                return

        try:
            backup = save_data(self.save_path, working)
        except OSError as error:
            self.say(f"Write failed: {error}")
            return

        self.data = working
        self.pending.clear()
        self.dirty = False
        self.rebuild_view()
        self.populate_saves(self.save_path)
        lines = ["Saved."] + applied
        lines += ["", f"Backup: {backup.name}"]
        self.say("\n".join(lines))
        self.update_change_count()

    # ---- misc -------------------------------------------------------------------------------------

    def say(self, text: str) -> None:
        self.status.configure(state="normal")
        self.status.delete("1.0", "end")
        self.status.insert("1.0", text)
        self.status.configure(state="disabled")

    def on_close(self) -> None:
        if self.has_changes() and not self.confirm_discard():
            return
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


_CANCELLED = object()


class SaveManagerWindow:
    """Clone, delete, back up and restore save files from the G editor's Save File Management."""

    def __init__(self, app: "EditorWindow"):
        self.app = app
        tk = app.tk
        ttk = app.ttk
        self.top = tk.Toplevel(app.root)
        self.top.title("Save Manager")
        self.top.geometry("860x520")
        self.top.transient(app.root)
        self.box = ttk.Frame(self.top, padding=8)
        self.box.pack(fill="both", expand=True)
        self.list = tk.Listbox(self.box, height=18)
        self.list.pack(fill="both", expand=True)
        bar = ttk.Frame(self.box)
        bar.pack(fill="x", pady=(8, 0))
        ttk.Button(bar, text="Clone", command=self.clone).pack(side="left")
        ttk.Button(bar, text="Delete", command=self.delete).pack(side="left", padx=6)
        ttk.Button(bar, text="Restore Latest Backup", command=self.restore).pack(side="left")
        ttk.Button(bar, text="Open Folder", command=app.open_directory).pack(side="left", padx=6)
        ttk.Button(bar, text="Refresh", command=self.refresh).pack(side="left")
        ttk.Button(bar, text="Close", command=self.top.destroy).pack(side="right")
        self.refresh()

    def refresh(self) -> None:
        self.paths = list_saves(self.app.directory)
        self.list.delete(0, "end")
        for path in self.paths:
            self.list.insert("end", describe(path))

    def selected(self) -> Path | None:
        selection = self.list.curselection()
        return self.paths[selection[0]] if selection else None

    def clone(self) -> None:
        source = self.selected()
        if source is None:
            self.app.messagebox.showinfo("Clone Save", "Select a save first.", parent=self.top)
            return
        name = self.app.simpledialog.askstring("Clone Save", "New character name:", parent=self.top)
        if not name:
            return
        try:
            data = load_save(source)
        except (ValueError, json.JSONDecodeError, OSError) as error:
            self.app.messagebox.showerror("Clone Failed", str(error), parent=self.top)
            return
        player = data.setdefault("player", {})
        player["name2"] = name
        if "name1" in player:
            player["name1"] = name
        safe = re.sub(r"[^0-9A-Za-z_\-\u4e00-\u9fff]+", "_", name).strip("_") or "clone"
        target = self.app.directory / f"{safe}_clone_{datetime.now():%Y-%m-%d_%H-%M-%S}.json"
        counter = 1
        while target.exists():
            target = self.app.directory / f"{safe}_clone_{datetime.now():%Y-%m-%d_%H-%M-%S}-{counter}.json"
            counter += 1
        target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        self.app.populate_saves(target)
        self.refresh()
        self.app.messagebox.showinfo("Clone Save", f"Cloned to: {target.name}", parent=self.top)

    def delete(self) -> None:
        path = self.selected()
        if path is None:
            self.app.messagebox.showinfo("Delete Save", "Select a save first.", parent=self.top)
            return
        if not self.app.messagebox.askyesno(
                "Delete Save", f"Permanently delete {path.name}?\nBackup files are kept.", parent=self.top):
            return
        try:
            path.unlink()
        except OSError as error:
            self.app.messagebox.showerror("Delete Failed", str(error), parent=self.top)
            return
        if self.app.save_path == path:
            self.app.reload()
        self.refresh()

    def restore(self) -> None:
        path = self.selected()
        if path is None:
            self.app.messagebox.showinfo("Restore Backup", "Select a save first.", parent=self.top)
            return
        backups = sorted(path.parent.glob(path.name + ".bak-*"),
                         key=lambda item: item.stat().st_mtime, reverse=True)
        if not backups:
            self.app.messagebox.showinfo("Restore Backup", "This save has no .bak backups.", parent=self.top)
            return
        backup = backups[0]
        if not self.app.messagebox.askyesno(
                "Restore Backup", f"Overwrite {backup.name} with backup {path.name}?\nThe current file is saved as a new backup first.",
                parent=self.top):
            return
        try:
            shutil.copy2(path, path.with_name(f"{path.name}.bak-{datetime.now():%Y%m%d-%H%M%S}"))
            shutil.copy2(backup, path)
        except OSError as error:
            self.app.messagebox.showerror("Restore Failed", str(error), parent=self.top)
            return
        self.app.reload()
        self.refresh()
        self.app.messagebox.showinfo("Restore Backup", "Restored.", parent=self.top)


class GameDataWindow:
    """Edit GameData/*.json in a raw JSON window, with validation and a backup on every save."""

    def __init__(self, app: "EditorWindow"):
        self.app = app
        tk = app.tk
        ttk = app.ttk
        self.top = tk.Toplevel(app.root)
        self.top.title("Game Data / Modding")
        self.top.geometry("1080x700")
        self.top.transient(app.root)
        body = ttk.Panedwindow(self.top, orient="horizontal")
        body.pack(fill="both", expand=True, padx=8, pady=8)
        left = tk.Frame(body)
        body.add(left, weight=1)
        self.files = tk.Listbox(left)
        self.files.pack(fill="both", expand=True)
        for label, name in GAME_DATA_FILES:
            self.files.insert("end", f"{label}  ·  {name}")
        self.files.bind("<<ListboxSelect>>", lambda _event: self.load())
        ttk.Button(left, text="Export Default Data", command=self.export_defaults).pack(fill="x", pady=(6, 0))
        right = ttk.Frame(body)
        body.add(right, weight=5)
        self.path_label = ttk.Label(right, text="", foreground="#555")
        self.path_label.pack(anchor="w")
        self.text = tk.Text(right, wrap="none", undo=True)
        self.text.pack(fill="both", expand=True, pady=(4, 6))
        bar = ttk.Frame(right)
        bar.pack(fill="x")
        ttk.Button(bar, text="Form Editor", command=self.open_forms).pack(side="left")
        ttk.Button(bar, text="Validate JSON", command=self.validate).pack(side="left", padx=(6, 0))
        ttk.Button(bar, text="Save (with backup)", command=self.save).pack(side="left", padx=6)
        ttk.Button(bar, text="Reload", command=self.load).pack(side="left")
        ttk.Button(bar, text="Close", command=self.top.destroy).pack(side="right")
        self.current: Path | None = None
        self.files.selection_set(0)
        self.load()

    def open_forms(self) -> None:
        from save_editor_lib.game_data_forms import GameDataFormsWindow
        GameDataFormsWindow(self.top, language="en")

    def selected_file(self) -> tuple[str, str] | None:
        selection = self.files.curselection()
        return GAME_DATA_FILES[selection[0]] if selection else None

    def load(self) -> None:
        selected = self.selected_file()
        if selected is None:
            return
        _label, name = selected
        path = game_data_directory() / name
        self.current = path
        self.path_label.configure(text=str(path))
        try:
            text = path.read_text(encoding="utf-8") if path.exists() else "{\n}\n"
        except OSError as error:
            self.app.messagebox.showerror("Read Failed", str(error), parent=self.top)
            return
        self.text.delete("1.0", "end")
        self.text.insert("1.0", text)

    def validate(self) -> bool:
        try:
            json.loads(self.text.get("1.0", "end-1c"))
        except json.JSONDecodeError as error:
            self.app.messagebox.showerror("Invalid JSON", str(error), parent=self.top)
            return False
        self.app.messagebox.showinfo("JSON", "JSON is valid.", parent=self.top)
        return True

    def save(self) -> None:
        if self.current is None:
            return
        try:
            data = json.loads(self.text.get("1.0", "end-1c"))
        except json.JSONDecodeError as error:
            self.app.messagebox.showerror("Invalid JSON", str(error), parent=self.top)
            return
        self.current.parent.mkdir(parents=True, exist_ok=True)
        if self.current.exists():
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            shutil.copy2(self.current, self.current.with_name(f"{self.current.name}.bak-{stamp}"))
        self.current.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.app.messagebox.showinfo("Saved Successfully", f"Saved {self.current.name}", parent=self.top)

    def export_defaults(self) -> None:
        try:
            message = export_default_game_data()
        except Exception as error:
            self.app.messagebox.showerror("Export failed", str(error), parent=self.top)
            return
        self.load()
        self.app.messagebox.showinfo("Export Default Data", message, parent=self.top)


class CompanionManager:
    """The five story companions, with the flags and the active-id list kept in step."""

    def __init__(self, window: EditorWindow):
        import tkinter as tk
        from tkinter import ttk, simpledialog

        self.window = window
        self.tk = tk
        self.simpledialog = simpledialog
        self.top = tk.Toplevel(window.root)
        self.top.title("Companion Manager")
        self.top.geometry("780x360")
        self.top.transient(window.root)
        self.top.grab_set()

        ttk.Label(self.top, padding=8, text=(
            "Recruitment, active status, death and relationship values write directly to storySystems.companions and activeCompanionIds;"
            "files are written only when you click \"Save All Changes\" in the main window.")).pack(fill="x")

        tree_frame = ttk.Frame(self.top)
        tree_frame.pack(fill="both", expand=True, padx=8)
        self.tree = ttk.Treeview(tree_frame, columns=("recruited", "active", "dead", "level",
                                                      "loyalty", "trust", "romance"),
                                 show="tree headings", selectmode="browse", height=8)
        self.tree.heading("#0", text="Companions")
        for column, title in (("recruited", "Recruited"), ("active", "Active"), ("dead", "Dead"),
                              ("level", "Level"), ("loyalty", "Loyalty"), ("trust", "Trust"),
                              ("romance", "Romance")):
            self.tree.heading(column, text=title)
            self.tree.column(column, width=70, anchor="center")
        self.tree.column("#0", width=110)
        self.tree.pack(side="left", fill="both", expand=True)
        tree_bar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        tree_bar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=tree_bar.set)

        buttons = ttk.Frame(self.top, padding=8)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Recruit/Dismiss", command=self.toggle_recruited).pack(side="left")
        ttk.Button(buttons, text="Active/Resting", command=self.toggle_active).pack(side="left", padx=6)
        ttk.Button(buttons, text="Set Loyalty/Trust/Romance", command=self.edit_relationship).pack(side="left")
        ttk.Button(buttons, text="Set Level/Experience", command=self.edit_level).pack(side="left", padx=6)
        ttk.Button(buttons, text="Revive All", command=self.revive_all).pack(side="left")

        self.status = ttk.Label(self.top, padding=(8, 0, 8, 8), foreground="#555")
        self.status.pack(fill="x")
        self.fill()

    def fill(self) -> None:
        self.tree.delete(*self.tree.get_children())
        for companion_id in sorted(COMPANION_NAMES):
            entry = self.window.companion_entry(companion_id) or {}
            self.tree.insert("", "end", iid=str(companion_id), text=COMPANION_NAMES[companion_id],
                             values=("Yes" if entry.get("isRecruited") else "No",
                                     "Yes" if entry.get("isActive") else "No",
                                     "Yes" if entry.get("isDead") else "No",
                                     entry.get("level", 1),
                                     entry.get("loyaltyLevel", 50),
                                     entry.get("trustLevel", 50),
                                     entry.get("romanceLevel", 0)))

    def selected_id(self) -> int | None:
        selection = self.tree.selection()
        return int(selection[0]) if selection else None

    def say(self, text: str) -> None:
        self.status.configure(text=text)

    def toggle_recruited(self) -> None:
        companion_id = self.selected_id()
        if companion_id is None:
            return
        entry = self.window.companion_entry(companion_id) or {}
        message = self.window.set_companion_recruited(companion_id, not entry.get("isRecruited"))
        self.fill()
        self.say(message)

    def toggle_active(self) -> None:
        companion_id = self.selected_id()
        if companion_id is None:
            return
        entry = self.window.companion_entry(companion_id) or {}
        message = self.window.set_companion_active(companion_id, not entry.get("isActive"))
        self.fill()
        self.say(message)

    def edit_relationship(self) -> None:
        companion_id = self.selected_id()
        if companion_id is None:
            return
        entry = self.window.companion_entry(companion_id, create=True)
        assert entry is not None
        for key, title in (("loyaltyLevel", "Loyalty"), ("trustLevel", "Trust"), ("romanceLevel", "Romance")):
            value = self.simpledialog.askinteger(title, f"{COMPANION_NAMES[companion_id]}'s {title} (0-100): ",
                                                 parent=self.top, initialvalue=int(entry.get(key, 50)),
                                                 minvalue=0, maxvalue=100)
            if value is not None:
                entry[key] = value
        self.window.dirty = True
        self.window.rebuild_view()
        self.fill()
        self.say(f"{COMPANION_NAMES[companion_id]}'s relationship values updated (not written to the file yet).")

    def edit_level(self) -> None:
        companion_id = self.selected_id()
        if companion_id is None:
            return
        entry = self.window.companion_entry(companion_id, create=True)
        assert entry is not None
        level = self.simpledialog.askinteger("Level", f"{COMPANION_NAMES[companion_id]}'s level (1-100):",
                                             parent=self.top, initialvalue=int(entry.get("level", 1)),
                                             minvalue=1, maxvalue=100)
        if level is not None:
            entry["level"] = level
        experience = self.simpledialog.askinteger(
            "Experience", f"{COMPANION_NAMES[companion_id]}'s experience (leave blank to keep the current value):",
            parent=self.top, initialvalue=int(entry.get("experience", 0)), minvalue=0)
        if experience is not None:
            entry["experience"] = experience
        self.window.dirty = True
        self.window.rebuild_view()
        self.fill()
        self.say(f"{COMPANION_NAMES[companion_id]}'s level/experience updated (not written to the file yet).")

    def revive_all(self) -> None:
        self.say(self.window.revive_companions())
        self.fill()


class PartyManager:
    """The NPCs restored beside the player in the dungeon (game cap: four)."""

    def __init__(self, window: EditorWindow):
        import tkinter as tk
        from tkinter import ttk

        self.window = window
        self.tk = tk
        self.top = tk.Toplevel(window.root)
        self.top.title("Dungeon Party")
        self.top.geometry("860x520")
        self.top.transient(window.root)
        self.top.grab_set()

        ttk.Label(self.top, padding=8, text=(
            "This manages storySystems.dungeonPartyNPCIds: the NPCs brought along when entering the dungeon."
            f"At most {MAX_DUNGEON_PARTY} members; dead NPCs cannot join.")).pack(fill="x")

        body = ttk.Frame(self.top, padding=(8, 0))
        body.pack(fill="both", expand=True)

        current = ttk.LabelFrame(body, text="Current Party", padding=6)
        current.pack(side="left", fill="both", expand=True)
        current_frame = ttk.Frame(current)
        current_frame.pack(fill="both", expand=True)
        self.current = tk.Listbox(current_frame, height=18)
        self.current.pack(side="left", fill="both", expand=True)
        current_bar = ttk.Scrollbar(current_frame, orient="vertical", command=self.current.yview)
        current_bar.pack(side="right", fill="y")
        self.current.configure(yscrollcommand=current_bar.set)
        current_buttons = ttk.Frame(current)
        current_buttons.pack(fill="x", pady=(6, 0))
        ttk.Button(current_buttons, text="Remove Selected", command=self.remove_selected).pack(side="left")
        ttk.Button(current_buttons, text="Clear Party", command=self.clear).pack(side="left", padx=6)

        available = ttk.LabelFrame(body, text="NPC Roster", padding=6)
        available.pack(side="left", fill="both", expand=True, padx=(8, 0))
        search = ttk.Frame(available)
        search.pack(fill="x")
        ttk.Label(search, text="Search").pack(side="left")
        self.search = ttk.Entry(search)
        self.search.pack(side="left", fill="x", expand=True, padx=6)
        self.search.bind("<KeyRelease>", lambda _event: self.fill_available())
        available_frame = ttk.Frame(available)
        available_frame.pack(fill="both", expand=True, pady=(6, 0))
        self.available = tk.Listbox(available_frame, height=14)
        self.available.pack(side="left", fill="both", expand=True)
        available_bar = ttk.Scrollbar(available_frame, orient="vertical", command=self.available.yview)
        available_bar.pack(side="right", fill="y")
        self.available.configure(yscrollcommand=available_bar.set)
        ttk.Button(available, text="Add Selected NPC to Party", command=self.add_selected).pack(fill="x", pady=(6, 0))

        self.status = ttk.Label(self.top, padding=8, foreground="#555")
        self.status.pack(fill="x")

        self.current_names: dict[str, str] = {}
        self.available_ids: list[str] = []
        self.fill_current()
        self.fill_available()

    def fill_current(self) -> None:
        self.current.delete(0, "end")
        self.current_names.clear()
        for npc_id in self.window.party_ids():
            name = self.window.npc_name_by_id(npc_id)
            self.current_names[str(self.current.size())] = npc_id
            self.current.insert("end", name)

    def fill_available(self) -> None:
        needle = self.search.get().strip().lower()
        self.available.delete(0, "end")
        self.available_ids.clear()
        party = set(self.window.party_ids())
        for npc in sorted(self.window.npc_roster(), key=lambda n: str(n.get("name", ""))):
            npc_id = npc.get("id")
            if not isinstance(npc_id, str) or npc_id in party:
                continue
            line = f"{npc.get('name', '?')}  Lv.{npc.get('level', '?')}  {npc.get('location', '?')}"
            if npc.get("isDead"):
                line += "  · Dead"
            if needle and needle not in line.lower():
                continue
            self.available_ids.append(npc_id)
            self.available.insert("end", line)

    def say(self, text: str) -> None:
        self.status.configure(text=text)

    def add_selected(self) -> None:
        selection = self.available.curselection()
        if not selection:
            return
        message = self.window.add_party_npc(self.available_ids[selection[0]])
        self.say(message)
        self.fill_current()
        self.fill_available()

    def remove_selected(self) -> None:
        selection = self.current.curselection()
        if not selection:
            return
        npc_id = self.current_names[str(selection[0])]
        self.say(self.window.remove_party_npc(npc_id))
        self.fill_current()
        self.fill_available()

    def clear(self) -> None:
        self.say(self.window.clear_party())
        self.fill_current()
        self.fill_available()


# ============================== entry point ==============================

def main() -> int:
    # Windows consoles default to a legacy code page in some shells, which turns the messages into noise.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    parser = argparse.ArgumentParser(description="Edit a Usurper Reborn single-player save (player, NPCs, party, world)")
    parser.add_argument("--saves", help="Save directory (defaults to the automatically found bin/Debug/net8.0/saves)")
    parser.add_argument("--check", action="store_true", help="List saves only, without opening a window")
    args = parser.parse_args()

    directory = find_saves_directory(args.saves)
    if args.check:
        return check(directory)
    if not directory.is_dir():
        print(f"Save directory not found: {directory}", file=sys.stderr)
        return 1

    EditorWindow(directory).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
