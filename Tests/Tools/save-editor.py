#!/usr/bin/env python3
"""A window for editing a single-player save, with no build step and no dependencies.

    python Tests/Tools/save-editor.py            # normal use
    python Tests/Tools/save-editor.py --check    # list saves and field counts, open no window
    python Tests/Tools/save-editor.py --saves <dir>

The window covers more than the player object: every scalar in the save is reachable, with
first-class views for the player, the NPC roster, the companions and dungeon party, the world
state, the story systems and the settings. Every field carries a Chinese label and a note
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

# The player fields worth reaching quickly. Everything is still searchable in "玩家（全部）".
PLAYER_GROUPS: list[tuple[str, list[str]]] = [
    ("基础", ["name1", "name2", "realName", "level", "experience", "class", "race", "sex",
              "age", "difficulty", "specialization"]),
    ("属性", ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma",
              "defence", "agility", "stamina", "baseStrength", "baseDexterity",
              "baseConstitution", "baseIntelligence", "baseWisdom", "baseCharisma",
              "baseDefence", "baseAgility", "baseStamina"]),
    ("生命与法力", ["hp", "maxHP", "baseMaxHP", "mana", "maxMana", "baseMaxMana", "healing",
                    "healingPotions", "manaPotions", "antidotes", "poisonVials", "smokeBombs",
                    "poison", "poisonTurns", "fatigue"]),
    ("金钱与银行", ["gold", "bankGold", "bankLoan", "bankWage", "bankInterest",
                    "royalLoanAmount", "royalLoanDueDay", "loanAmount", "loanDaysRemaining",
                    "loanInterestAccrued"]),
    ("战斗", ["weapPow", "armPow", "bonusWeapPow", "bonusArmPow", "fights", "pFights",
              "tFights", "mKills", "mDefeats", "pKills", "pDefeats", "combatSpeed",
              "autoCombatHealPercent", "resurrections", "maxResurrections",
              "resurrectionsUsed", "playthroughDeaths"]),
    ("声望与阵营", ["fame", "chivalry", "darkness", "mental", "wantedLvl", "murderWeight",
                    "darkAlleyReputation", "loyalty", "haunt", "karma"]),
    ("任务与进度", ["quests", "royQuests", "turnsRemaining", "turnCount", "trainingPoints",
                    "currentLocation", "daysInPrison", "innerSanctumLastDay", "currentDay"]),
    ("家园", ["homeLevel", "chestLevel", "trainingRoomLevel", "gardenLevel", "bedLevel",
              "hearthLevel", "homeRestsToday", "herbsGatheredToday"]),
    ("设置", ["language", "autoHeal", "screenReaderMode", "compactMode", "autoLook",
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

SECTIONS = [
    ("玩家 · 常用", "player_common"),
    ("玩家 · 全部", "player_all"),
    ("NPC", "npc"),
    ("队伍与同伴", "party"),
    ("世界状态", "world"),
    ("剧情系统", "story"),
    ("设置", "settings"),
    ("全部字段", "all"),
]

# One Chinese label per key name. The path is always shown too, so an unknown key stays usable.
LABELS = {
    # character
    "name": "姓名", "name1": "名字", "name2": "显示名", "realName": "本名",
    "level": "等级", "experience": "经验", "class": "职业", "race": "种族", "sex": "性别",
    "age": "年龄", "difficulty": "难度", "specialization": "专精", "archetype": "原型",
    "location": "位置", "team": "队伍", "isTeamLeader": "队长", "teamPassword": "队伍密码",
    "gold": "金币", "bankGold": "银行存款", "bankLoan": "银行贷款", "bankWage": "银行工资",
    "bankInterest": "银行利息", "bankInterestRate": "银行利率", "bankVaultReserve": "银行金库储备",
    "hp": "生命", "maxHP": "最大生命", "baseMaxHP": "基础最大生命",
    "mana": "法力", "maxMana": "最大法力", "baseMaxMana": "基础最大法力",
    "strength": "力量", "defence": "防御", "agility": "敏捷", "dexterity": "灵巧",
    "charisma": "魅力", "intelligence": "智力", "wisdom": "智慧", "constitution": "体质",
    "stamina": "耐力", "baseStrength": "基础力量", "baseDefence": "基础防御",
    "baseAgility": "基础敏捷", "baseDexterity": "基础灵巧", "baseConstitution": "基础体质",
    "baseIntelligence": "基础智力", "baseWisdom": "基础智慧", "baseCharisma": "基础魅力",
    "baseStamina": "基础耐力", "weapPow": "武器威力", "armPow": "护甲威力",
    "baseWeapPow": "基础武器威力", "baseArmPow": "基础护甲威力",
    "fame": "声望", "chivalry": "善良", "darkness": "黑暗", "mental": "精神", "karma": "业力",
    "loyalty": "忠诚", "haunt": "怨念", "wantedLvl": "通缉等级", "murderWeight": "谋杀值",
    "healing": "治疗量", "healingPotions": "治疗药剂", "manaPotions": "法力药剂",
    "antidotes": "解毒剂", "poisonVials": "毒药瓶", "smokeBombs": "烟雾弹",
    "poison": "中毒", "poisonTurns": "中毒回合", "fatigue": "疲劳",
    "resurrections": "复活次数", "maxResurrections": "最大复活次数",
    "resurrectionsUsed": "已用复活", "playthroughDeaths": "死亡次数",
    "trainingPoints": "训练点", "quests": "任务数", "royQuests": "王室任务",
    "turnsRemaining": "剩余回合", "turnCount": "回合数", "daysInPrison": "坐牢天数",
    "currentLocation": "当前位置", "day": "天数", "currentDay": "当前天数",
    "homeLevel": "家园等级", "chestLevel": "宝箱等级", "trainingRoomLevel": "训练室等级",
    "gardenLevel": "花园等级", "bedLevel": "床铺等级", "hearthLevel": "壁炉等级",
    "fights": "战斗次数", "pFights": "玩家战斗", "tFights": "队伍战斗",
    "mKills": "怪物击杀", "mDefeats": "怪物击败", "pKills": "玩家击杀", "pDefeats": "玩家击败",
    "combatSpeed": "战斗速度", "autoCombatHealPercent": "自动喝药阈值",
    "language": "语言", "autoHeal": "自动治疗", "screenReaderMode": "屏幕阅读器",
    "compactMode": "紧凑模式", "autoLook": "自动观察", "dungeonAutoMap": "地牢自动地图",
    "autoLevelUp": "自动升级", "autoEquipDisabled": "禁用自动装备", "colorTheme": "配色主题",
    "dateFormatPreference": "日期格式", "menuKeysNeedEnter": "菜单键需回车",
    "webMenuKeysNeedEnter": "网页菜单键需回车",
    "items": "物品", "inventory": "背包", "equippedItems": "已装备", "dynamicEquipment": "动态装备",
    "spells": "法术", "skills": "技能", "learnedAbilities": "已学技能", "quickbar": "快捷栏",
    "activeQuests": "进行中任务", "achievements": "成就", "statistics": "统计",
    "personalityProfile": "性格", "memories": "记忆", "relationships": "关系",
    "emotionalState": "情绪", "currentGoals": "当前目标", "enemies": "敌人",
    "marketInventory": "商店库存", "skillProficiencies": "技能熟练度",
    "skillTrainingProgress": "技能训练进度", "craftingMaterials": "制作材料",
    # NPC roster
    "id": "ID", "characterID": "角色ID", "isDead": "已死亡", "isPermaDead": "永久死亡",
    "isMarried": "已婚", "married": "已婚", "spouseName": "配偶", "npcFaction": "NPC派系",
    "worshippedGod": "信奉神明", "isHostile": "敌对", "isAIDriven": "AI 驱动",
    "gangId": "帮派ID", "recentDialogueIds": "最近对话", "knownCharacters": "认识的人",
    "motherName": "母亲", "fatherName": "父亲", "isKing": "国王",
    # companions and party
    "isRecruited": "已招募", "isActive": "出战", "loyaltyLevel": "忠诚", "trustLevel": "信任",
    "romanceLevel": "恋爱", "personalQuestStarted": "个人任务开始",
    "personalQuestCompleted": "个人任务完成", "recruitedDay": "招募天数",
    "companions": "同伴", "activeCompanionIds": "出战同伴ID", "fallenCompanions": "阵亡同伴",
    "dungeonPartyNPCIds": "地牢队友ID", "dungeonPartyPlayerNames": "地牢队友玩家名",
    "activeGriefs": "进行中的哀伤", "griefMemories": "哀伤记忆", "companionId": "同伴ID",
    # world
    "townPotValue": "城镇金库", "currentRuler": "当前统治者", "activeEvents": "进行中事件",
    "shopInventories": "商店库存", "recentNews": "最近新闻",
    "marketplaceListings": "拍卖行挂售", "settlement": "定居点", "usedNPCNames": "已用NPC名",
    "bankRobberiesToday": "今日银行抢劫", "bankRobberiesDate": "银行抢劫日期",
    # story systems
    "awakeningLevel": "觉醒等级", "collectedFragments": "收集碎片", "collectedSeals": "收集封印",
    "collectedArtifacts": "收集神器", "currentCycle": "轮回数", "currentChapter": "章节",
    "griefStage": "哀伤阶段", "griefDaysRemaining": "哀伤剩余天数",
    "griefCompanionName": "哀伤对象", "oldGodStates": "旧神状态", "oldGodsEncountered": "遭遇旧神",
    "majorChoices": "重大选择", "playerGods": "玩家神明", "children": "孩子",
    "archetypeTracker": "原型统计", "royalCourt": "王庭", "factions": "派系",
    "townNPCStories": "镇民故事", "dreams": "梦境", "amnesia": "失忆", "betrayal": "背叛",
    "culturalMemes": "文化模因", "storyFlags": "剧情标记", "storyFlagBits": "剧情位",
    "completedEndings": "已完成结局", "npcMarriages": "NPC 婚姻", "affairs": "婚外情",
    # royal court / settlement
    "kingName": "国王名", "throneVacant": "王座空悬", "treasury": "国库",
    "taxRate": "税率", "kingTaxPercent": "国王税率", "cityTaxPercent": "城市税率",
    "courtMembers": "宫廷成员", "heirs": "继承人", "guards": "守卫", "prisoners": "囚犯",
    "orphans": "孤儿", "activePlots": "进行中的阴谋", "coronationDate": "加冕日期",
    "founded": "已建立", "settlerNames": "定居者", "communalTreasury": "公共金库",
    "playerContributions": "玩家贡献", "buildingTiers": "建筑等级",
    # settings
    "mode": "模式", "lastResetTime": "上次重置", "autoSaveEnabled": "自动存档",
    "autoSaveInterval": "自动存档间隔",
    # top level
    "version": "存档版本", "saveTime": "存档时间", "lastDailyReset": "上次每日重置",
    "dailyCycleMode": "每日循环模式", "player": "玩家", "npCs": "NPC 名单",
    "worldState": "世界状态", "settings": "设置", "storySystems": "剧情系统",
    "npcStates": "NPC 状态", "npcId": "NPC ID", "currentStage": "当前阶段",
    "completedStages": "已完成阶段", "choicesMade": "已做选择", "stageCompletedOnDay": "阶段完成日",
    # player counters and progress
    "accountCreated": "账号创建", "lastLogin": "上次登录", "lastLoginDate": "上次登录日期",
    "loginStreak": "连续登录", "longestLoginStreak": "最长连续登录",
    "gameTimeMinutes": "游戏时间(分)", "presentDays": "当前世界天数", "agePlus": "额外年龄",
    "bankGuard": "银行守卫", "bankRobberyAttempts": "银行抢劫次数",
    "marryActions": "求婚次数", "wolfFeed": "喂狼次数", "royalAdoptions": "王室收养",
    "wrestlings": "摔跤次数", "gymSessions": "健身次数", "pickPocketAttempts": "扒窃尝试",
    "massage": "按摩次数", "umanBearTries": "乌曼熊尝试",
    "templeResurrectionsUsed": "神殿复活次数", "blessingsReceived": "获祝福次数",
    "churchDonations": "教会捐款", "sacrificesMade": "献祭次数",
    "healingsReceived": "受治疗次数", "hasHolyWater": "拥有圣水",
    "bardSongsLeft": "剩余吟游歌曲", "daysInPower": "掌权天数", "thievery": "偷窃值",
    "taxRelief": "税收减免", "royTaxPaid": "已付王室税", "kingVotePoll": "国王投票",
    "kingLastVote": "上次国王投票", "throneChallengedToday": "今日挑战王座",
    "totalExecutions": "累计处决", "executionsToday": "今日处决",
    "playerImprisonedToday": "玩家今日入狱", "npCsImprisonedToday": "今日入狱NPC",
    "kids": "孩子数", "disRes": "纠纷解决", "weaponCursed": "武器被诅咒",
    "armorCursed": "护甲被诅咒", "shieldCursed": "盾牌被诅咒",
    "king": "国王", "teamRec": "队伍招募", "bGuard": "银行守卫标记", "bGuardNr": "银行守卫编号",
    "cityTaxEarnedThisWeek": "本周城市税", "cityTaxEarnedLifetime": "累计城市税",
    "activeStatuses": "当前状态效果", "gnollP": "豺狼人点数", "addict": "成瘾",
    "steroidDays": "类固醇天数", "drugEffectDays": "药物效果天数", "activeDrug": "当前药物",
    "mercy": "仁慈", "blind": "失明", "plague": "瘟疫", "smallpox": "天花",
    "measles": "麻疹", "leprosy": "麻风", "loversBane": "情人之灾",
    "divineWrathLevel": "神怒等级", "angeredGodName": "触怒的神明",
    "betrayedForGodName": "为神背叛者", "divineWrathPending": "神怒待触发",
    "divineWrathTurnsRemaining": "神怒剩余回合", "royalLoanAmount": "王室贷款",
    "royalLoanDueDay": "王室贷款到期日", "royalLoanBountyPosted": "王室贷款悬赏",
    "nobleTitle": "贵族头衔", "isKnighted": "已授勋", "familySurname": "家族姓氏",
    "permakillLog": "永久击杀记录", "lastMurderWeightDecay": "谋杀值衰减",
    "devMenuUsed": "用过开发者菜单", "skipIntimateScenes": "跳过亲密场景",
    "disableCharacterMonsterArt": "禁用角色怪物插画", "autoLevelUp": "自动升级",
    "autoEquipDisabled": "禁用自动装备", "classicMainStreet": "经典主街",
    "districtsMainStreet": "主街街区", "menuKeysNeedEnter": "菜单键需回车",
    "webMenuKeysNeedEnter": "网页菜单键需回车", "classicTipDraws": "经典提示抽取",
    "dateFormatPreference": "日期格式", "autoRedistributeXP": "自动重分经验",
    "specialization": "专精", "teamXPPercent": "队伍经验比例",
    "teamXPIsExplicit": "手动队伍经验", "teamXPEvenSplit": "队伍经验均分",
    "loyalty": "忠诚", "haunt": "怨念", "master": "主人", "wellWish": "水井愿望",
    "height": "身高", "weight": "体重", "eyes": "眼睛", "hair": "头发", "skin": "肤色",
    "phrases": "台词短语", "description": "描述", "romanceData": "恋爱数据",
    "achievementsData": "成就数据", "learnedAbilities": "已学能力", "quickbar": "快捷栏",
    "trains": "训练次数", "skillProficiencies": "技能熟练度",
    "skillTrainingProgress": "技能训练进度", "statTrainingCounts": "属性训练次数",
    "unpaidWageDays": "欠薪天数", "craftingMaterials": "制作材料",
    "spells": "法术", "skills": "技能", "lHand": "左手", "rHand": "右手",
    "head": "头部", "body": "身体", "arms": "手臂", "lFinger": "左手指",
    "rFinger": "右手指", "legs": "腿部", "feet": "脚部", "waist": "腰部",
    "neck": "颈部", "neck2": "颈部2", "face": "面部", "shield": "盾牌",
    "hands": "手部", "aBody": "备用身体", "immortal": "不朽", "battleCry": "战吼",
    "mKills": "怪物击杀", "mDefeats": "怪物击败", "pKills": "玩家击杀",
    "pDefeats": "玩家击败", "activeStatuses": "当前状态效果",
    # home and buffs
    "hasTrophyRoom": "奖杯室", "hasTeleportCircle": "传送阵",
    "hasLegendaryArmory": "传说军械库", "hasVitalityFountain": "活力喷泉",
    "hasStudy": "书房", "hasServants": "仆人", "hasReinforcedDoor": "加固门",
    "homeRestsToday": "今日在家休息", "herbsGatheredToday": "今日采集草药",
    "wellRestedCombats": "充分休息战斗", "wellRestedBonus": "充分休息加成",
    "loversBlissCombats": "爱侣祝福战斗", "loversBlissBonus": "爱侣祝福加成",
    "cycleExpMultiplier": "轮回经验倍率",
    "herbHealing": "治疗草", "herbIronbark": "铁皮草", "herbFirebloom": "火焰花",
    "herbSwiftthistle": "疾风蓟", "herbStarbloom": "星花",
    "herbBuffType": "草药增益类型", "herbBuffCombats": "草药增益战斗",
    "herbBuffValue": "草药增益值", "herbExtraAttacks": "草药额外攻击",
    "godSlayerCombats": "弑神战斗", "godSlayerDamageBonus": "弑神伤害加成",
    "godSlayerDefenseBonus": "弑神防御加成", "songBuffType": "歌曲增益类型",
    "songBuffCombats": "歌曲增益战斗", "songBuffValue": "歌曲增益值",
    "songBuffValue2": "歌曲增益值2", "heardLoreSongs": "听过的传说歌",
    "foodBuffType": "食物增益类型", "foodBuffCombats": "食物增益战斗",
    "foodBuffValue": "食物增益值", "mealsToday": "今日用餐",
    "innDuelsToday": "今日旅店决斗", "tavernStrangerTalkedToday": "今日与陌生人交谈",
    "visitedSettlements": "访问过的定居点", "settlementLoreRead": "读过的定居点传说",
    "wildernessExplorationsToday": "今日荒野探索",
    "wildernessRevisitsToday": "今日荒野重访", "wildernessDiscoveries": "荒野发现",
    "darkPactCombats": "黑暗契约战斗", "darkPactDamageBonus": "黑暗契约伤害加成",
    "hasShatteredSealFragment": "拥有碎裂封印", "hasTouchedTheVoid": "接触过虚空",
    "settlementBuffType": "定居点增益类型",
    "settlementBuffCombats": "定居点增益战斗", "settlementBuffValue": "定居点增益值",
    "smugglersCachePurchases": "走私者秘藏购买",
    "settlementGoldClaimedToday": "今日领取定居点金币",
    "settlementHerbClaimedToday": "今日领取定居点草药",
    "settlementShrineUsedToday": "今日使用定居点神龛",
    "jailbreakAttemptedToday": "今日尝试越狱",
    "settlementCircleUsedToday": "今日使用定居点法阵",
    "settlementWorkshopUsedToday": "今日使用定居点工坊",
    "workshopBuffCombats": "工坊增益战斗", "poisonCoatingCombats": "毒药涂层战斗",
    "activePoisonType": "当前毒药类型", "innerSanctumLastDay": "上次内殿日",
    "lastDailyResetBoundary": "上次每日重置边界", "lastPrayerRealDate": "上次祈祷日期",
    "lastInnerSanctumRealDate": "上次内殿日期",
    "lastBindingOfSoulsRealDate": "上次缚魂日期", "sethFightsToday": "今日赛斯战斗",
    "armWrestlesToday": "今日掰手腕", "sethDefeatsTotal": "赛斯累计击败",
    "royQuestsToday": "今日王室任务", "groggoShadowBlessingDex": "格罗戈暗影祝福灵巧",
    "timedStatBuffs": "限时属性增益", "artifactStatsApplied": "神器属性已应用",
    "cycleStatBonusApplied": "轮回属性加成已应用",
    "voidreaverConstitutionApplied": "虚空掠夺者体质已应用",
    "steroidShopPurchases": "类固醇商店购买", "alchemistINTBoosts": "炼金术士智力提升",
    "gamblingRoundsToday": "今日赌博回合", "pitFightsToday": "今日竞技场战斗",
    "desecrationsToday": "今日亵渎", "confessionsToday": "今日忏悔",
    "murdersToday": "今日谋杀", "reforgesToday": "今日重铸",
    "sparesToday": "今日饶恕", "teamWarsToday": "今日队伍战",
    "drinkingGamesToday": "今日饮酒游戏", "loveStreetVisitsToday": "今日爱之街",
    "intimateEncountersToday": "今日亲密", "gauntletRunsToday": "今日挑战",
    "marshToadAntidoteClaimedToday": "今日领取沼泽蟾蜍解药",
    "tributeDemandsToday": "今日贡品要求", "freeBlessingClaimedToday": "今日领取免费祝福",
    "mercContractsCompleted": "雇佣兵契约完成",
    "mercContractsClaimedToday": "今日领取雇佣兵契约",
    "lastMercBoardRefreshUtc": "雇佣兵板刷新", "dailyMercStandingGain": "每日雇佣兵声望",
    "blackMarketStockSeed": "黑市库存种子", "lastBlackMarketRefreshUtc": "黑市刷新",
    "blackMarketStock": "黑市库存", "almsGivenToday": "今日施舍",
    "orphanageGiftsToday": "今日孤儿院礼物", "hospiceTithesToday": "今日济贫院什一税",
    "lifetimeCharityGoldDonated": "累计慈善捐款", "attunedShrineId": "调谐神龛ID",
    "attunedShrineExpiresUtc": "调谐神龛到期",
    "attunedShrineExpiresGameDay": "调谐神龛到期日", "shrineFavor": "神龛恩宠",
    "discoveredFeatureIds": "已发现互动", "recognizedChildren": "已认子女",
    "permadeathInheritanceClaimed": "永久死亡继承已领取",
    "completedFamilyArcs": "完成家庭线", "completedArcChildNames": "完成家庭线子女",
    "petRoster": "宠物名单", "activePetId": "当前宠物ID",
    "lastPartnerBondingUtc": "上次伴侣羁绊", "lastRiteOfReturnUtc": "上次回归仪式",
    "dyingMessages": "临终留言", "loanAmount": "贷款金额",
    "loanDaysRemaining": "贷款剩余天数", "loanInterestAccrued": "贷款累计利息",
    "darkAlleyReputation": "暗巷声望", "drugTolerance": "药物耐受",
    "safeHouseResting": "安全屋休息", "bloodMoonDay": "血月日",
    # NPC
    "characterID": "角色ID", "baseStatsHP": "基础生命", "baseStatsAttack": "基础攻击",
    "baseStatsDefense": "基础防御", "baseStatsMagicPower": "基础魔力",
    "baseStatsSpeed": "基础速度", "baseStatsHealingPower": "基础治疗",
    "isAgedDeath": "老死", "birthDate": "出生日期", "marriedTimes": "结婚次数",
    "memoryTimesKept": "保留记忆时间", "emergentRole": "涌现角色",
    "roleStabilityTicks": "角色稳定计时", "originalMotherName": "原母亲名",
    "originalFatherName": "原父亲名", "soulAtGraduation": "毕业灵魂",
    "wasRaisedByPlayer": "由玩家养大", "lastOnPlayerTeamAt": "上次入队",
    "pregnancyDueDate": "怀孕到期", "pregnancyFatherName": "怀孕父亲",
    "recentDialogueIds": "最近对话ID", "equippedItemsSave": "同伴装备",
    "disabledAbilities": "禁用能力", "disabledSpells": "禁用法术",
    "personalQuestBeat": "个人任务阶段", "recruitedDate": "招募日期",
    # world and story
    "bankRobberiesToday": "今日银行抢劫", "bankRobberiesDate": "银行抢劫日期",
    "townPotValue": "城镇金库", "currentRuler": "当前统治者",
    "activeEvents": "进行中事件", "shopInventories": "商店库存",
    "recentNews": "最近新闻", "marketplaceListings": "拍卖行挂售",
    "settlement": "定居点", "usedNPCNames": "已用NPC名",
    "collectedFragments": "收集碎片", "experiencedMoments": "经历时刻",
    "oceanInsightIds": "海洋洞见ID", "completedParadoxIds": "已完成悖论ID",
    "moralUtilitarianChoices": "功利道德选择", "moralDeontologicalChoices": "义务道德选择",
    "moralVirtueChoices": "美德道德选择", "moralNihilistChoices": "虚无道德选择",
    "collectedSeals": "收集封印", "activeCompanionIds": "出战同伴ID",
    "fallenCompanions": "阵亡同伴", "dungeonPartyNPCIds": "地牢队友ID",
    "dungeonPartyPlayerNames": "地牢队友玩家名", "activeGriefs": "进行中的哀伤",
    "activeNpcGriefs": "NPC 哀伤", "griefMemories": "哀伤记忆",
    "storyFlags": "剧情标记", "storyFlagBits": "剧情标记位",
    "majorChoices": "重大选择", "playerGods": "玩家神明", "children": "孩子",
    "archetypeTracker": "原型统计", "royalCourt": "王庭", "townNPCStories": "镇民故事",
    "dreams": "梦境", "amnesia": "失忆", "betrayal": "背叛",
    "culturalMemes": "文化模因", "npcMarriages": "NPC 婚姻", "affairs": "婚外情",
    "oldGodsEncountered": "遭遇旧神", "currentChapter": "章节", "currentCycle": "轮回数",
    "collectedArtifacts": "收集神器", "completedEndings": "已完成结局",
    "relationships": "关系", "strangerEncounters": "陌生人遭遇", "factions": "派系",
    "npcRelationship": "NPC 关系", "profiles": "档案", "records": "记录",
    "betrayalPoints": "背叛点数", "isPendingBetrayal": "待触发背叛",
    "triggerReason": "触发原因", "hasBetrayed": "已背叛", "wasForgiven": "已获原谅",
    "betrayalDay": "背叛日", "warningShown": "已显示警告",
    "actsOfKindness": "善举次数", "departedCompanionId": "离队同伴ID",
    # royal court and settlement
    "kingName": "国王名", "throneVacant": "王座空悬", "treasury": "国库",
    "taxRate": "税率", "kingTaxPercent": "国王税率", "cityTaxPercent": "城市税率",
    "courtMembers": "宫廷成员", "heirs": "继承人", "guards": "守卫",
    "prisoners": "囚犯", "orphans": "孤儿", "activePlots": "进行中的阴谋",
    "coronationDate": "加冕日期", "magicBudget": "魔法预算",
    "establishmentStatus": "体制状态", "lastProclamation": "上次公告",
    "lastProclamationDate": "上次公告日期", "monarchHistory": "君主历史",
    "designatedHeir": "指定继承人", "kingAI": "国王AI类型", "kingSex": "国王性别",
    "taxAlignment": "税收倾向", "totalReign": "总在位时间", "daysReigned": "在位天数",
    "founded": "已建立", "settlerNames": "定居者", "communalTreasury": "公共金库",
    "playerContributions": "玩家贡献", "activeBuildingIndex": "当前建筑序号",
    "buildingTiers": "建筑等级", "buildingPools": "建筑资源池",
    "proposedBuildingTiers": "提议建筑等级", "proposedBuildingPools": "提议建筑资源池",
    "activeProposedBuildingId": "当前提议建筑ID", "proposalCooldowns": "提议冷却",
    "contributionBoostTicks": "贡献加成计时", "activeProposalId": "当前提议ID",
    "activeProposalProposer": "提议者", "activeProposalTicksLeft": "提议剩余计时",
    "activeProposalSupport": "提议支持", "activeProposalOppose": "提议反对",
    "activeProposalPlayerVotes": "玩家投票",
    # dream / meme / town stories containers
    "experiencedDreams": "经历过的梦境", "seenDungeonVisions": "见过的地牢幻象",
    "restsSinceLastDream": "距上次梦境的休息", "recoveredMemories": "恢复的记忆",
    "restCount": "休息次数", "truthRevealed": "真相已揭示",
    "activeMemes": "活跃模因", "npcMemeAwareness": "NPC 模因认知",
    "locationMemeStrength": "地点模因强度", "unlockDates": "解锁日期",
    # settings and top-level dates
    "mode": "模式", "lastResetTime": "上次重置", "autoSaveEnabled": "自动存档",
    "autoSaveInterval": "自动存档间隔", "utcNow": "当前 UTC 时间",
    # personality and emotion traits
    "aggression": "攻击性", "greed": "贪婪", "courage": "勇气", "vengefulness": "报复心",
    "impulsiveness": "冲动", "sociability": "社交性", "ambition": "野心",
    "trustworthiness": "可信度", "caution": "谨慎", "mysticism": "神秘倾向",
    "patience": "耐心", "romanticism": "浪漫", "flirtatiousness": "调情",
    "passion": "热情", "tenderness": "温柔", "happiness": "幸福", "anger": "愤怒",
    "fear": "恐惧", "sadness": "悲伤", "joy": "喜悦", "confidence": "自信",
    "loneliness": "孤独", "hope": "希望", "peace": "平静", "envy": "嫉妒",
    "pride": "骄傲", "compassion": "同情", "honesty": "诚实", "commitment": "承诺",
    "receptivity": "接受度", "sensuality": "感官倾向", "adventurousness": "冒险倾向",
    "exhibitionism": "暴露倾向", "voyeurism": "窥视倾向",
    "relationshipPref": "关系偏好", "intimateStyle": "亲密风格",
    "handedness": "惯用手", "gender": "性别", "currentLovers": "当前恋人",
    "exSpouses": "前配偶", "exes": "前任", "spouses": "配偶", "family": "家庭",
    "cuckArrangements": "绿帽安排", "jealousyLevels": "嫉妒程度",
    "polyNetworks": "多角关系网络", "currentProgress": "当前进度",
    # memory, goal, relationship entries
    "importance": "重要度", "emotionalImpact": "情感影响",
    "involvedCharacter": "相关角色", "targetCharacter": "目标角色",
    "targetLocation": "目标地点", "targetValue": "目标值",
    "createdTime": "创建时间", "isCompleted": "已完成", "priority": "优先级",
    "recentGameEvents": "最近游戏事件", "conversationStates": "对话状态",
    "responseHistory": "回应历史", "topicsDiscussed": "谈过的话题",
    "lastConversationDate": "上次对话日期", "personalQuestionsAsked": "私人问题",
    "flirtSuccessCount": "调情成功次数", "lastFlirtWasPositive": "上次调情成功",
    "currentStreak": "当前连续", "longestStreak": "最长连续", "longestSession": "最长会话",
    "totalPlayTime": "总游玩时间", "totalSessionsPlayed": "总会话数",
    "highestLevelReached": "最高等级", "highestGoldHeld": "最高持金",
    "deepestDungeonLevel": "最深地牢层", "lastDungeonFloor": "上次地牢层",
    "totalDaysPlayed": "总游玩天数", "totalMonstersKilled": "累计击杀怪物",
    "totalBossesKilled": "累计击杀首领", "totalCombatsWon": "累计战斗胜利",
    "totalCombatsLost": "累计战斗失败", "totalCombatsFled": "累计逃跑",
    "totalGoldEarned": "累计获得金币", "totalGoldSpent": "累计花费金币",
    "totalExperienceEarned": "累计获得经验", "totalDamageDealt": "累计造成伤害",
    "totalDamageTaken": "累计承受伤害", "totalCriticalHits": "累计暴击",
    "totalLevelUps": "累计升级", "totalItemsBought": "累计购买物品",
    "totalItemsSold": "累计售出物品", "totalHealingPotionsUsed": "累计使用治疗药剂",
    "totalManaPotionsUsed": "累计使用法力药剂", "totalSpellsCast": "累计施法",
    "totalQuestsCompleted": "累计完成任务", "totalDeaths": "累计死亡",
    "totalTimesResurrected": "累计复活", "totalPlayerKills": "累计击杀玩家",
    "totalRoomsExplored": "累计探索房间", "totalChestsOpened": "累计开箱",
    "totalTrapsDisarmed": "累计拆除陷阱", "totalTrapsTriggered": "累计触发陷阱",
    "totalSecretsFound": "累计发现秘密", "totalNPCInteractions": "累计NPC互动",
    "totalConversations": "累计对话", "totalFriendsGained": "累计交友",
    "totalGiftsGiven": "累计送礼", "totalRomances": "累计恋爱",
    # equipment and item entries
    "weaponPower": "武器威力", "armorClass": "护甲等级", "armorType": "护甲类型",
    "weaponType": "武器类型", "rarity": "稀有度", "isIdentified": "已鉴定",
    "isCursed": "被诅咒", "isUnique": "唯一", "strengthRequired": "力量需求",
    "itemValue": "物品价值", "itemName": "物品名", "itemType": "物品类型",
    "slot": "装备槽", "attack": "攻击", "defense": "防御",
    "blockChance": "格挡几率", "magicResistance": "魔法抗性",
    "hpRegen": "生命回复", "manaRegen": "法力回复", "thorns": "荆棘反伤",
    "lifeSteal": "吸血", "manaSteal": "吸法", "armorPiercing": "破甲",
    "criticalChanceBonus": "暴击几率加成", "criticalDamageBonus": "暴击伤害加成",
    "bonusMaxHP": "最大生命加成", "bonusWeapPow": "武器威力加成",
    "bonusArmPow": "护甲威力加成", "maxHPBonus": "最大生命加成",
    "maxManaBonus": "最大法力加成", "enchantBase": "附魔基础",
    "enchantMarkers": "附魔标记", "hasFireEnchant": "火焰附魔",
    "hasFrostEnchant": "冰霜附魔", "hasHolyEnchant": "神圣附魔",
    "hasLightningEnchant": "闪电附魔", "hasPoisonEnchant": "毒附魔",
    "hasShadowEnchant": "暗影附魔", "hasTitanResolve": "泰坦之志",
    # quests, events and marketplace entries
    "status": "状态", "reward": "奖励", "rewardType": "奖励类型", "penalty": "惩罚",
    "penaltyType": "惩罚类型", "daysToComplete": "完成天数", "minLevel": "最低等级",
    "maxLevel": "最高等级", "questType": "任务类型", "questTarget": "任务目标",
    "targetNPCName": "目标NPC", "isPlayerBounty": "玩家悬赏", "bountyGold": "赏金",
    "objectives": "任务目标列表", "monsters": "怪物列表",
    "isMercContract": "雇佣兵契约", "issuingFaction": "发布派系",
    "mercContractTier": "雇佣兵契约层级", "forced": "强制", "offeredTo": "提供给",
    "initiator": "发起者", "occupier": "占据者", "occupiedDays": "占据天数",
    "startTime": "开始时间", "endReason": "结束原因", "createdOnGameDay": "创建游戏日",
    "activeProposalId": "当前提议ID", "activeProposalProposer": "提议者",
    "activeProposalTicksLeft": "提议剩余计时", "activeProposalSupport": "提议支持",
    "activeProposalOppose": "提议反对", "activeProposalPlayerVotes": "玩家投票",
    "proposalCooldowns": "提议冷却", "contributionBoostTicks": "贡献加成计时",
    "activeBuildingIndex": "当前建筑序号", "buildingTiers": "建筑等级",
    "buildingPools": "建筑资源池", "proposedBuildingTiers": "提议建筑等级",
    "proposedBuildingPools": "提议建筑资源池",
    "activeProposedBuildingId": "当前提议建筑ID",
    # marketplace / news / misc records
    "item": "物品", "seller": "卖家", "isNPCSeller": "NPC卖家",
    "sellerNPCId": "卖家NPC ID", "price": "价格", "posted": "挂售时间",
    "titleKey": "标题键", "titleArgs": "标题参数", "commentKey": "说明键",
    "commentArgs": "说明参数", "descriptionKey": "描述键", "descriptionArgs": "描述参数",
    "initiatorKey": "发起者键",
    # remaining counters, bonuses and life statistics
    "actionsSinceLastEncounter": "距上次遭遇的行动", "agilityBonus": "敏捷加成",
    "ai": "AI", "arenaChampionTier": "竞技场冠军层级", "armHag": "护甲讨价还价",
    "armor": "护甲", "armorShopBarredUntilDay": "护甲店禁止至天",
    "artifactsCollected": "收集神器", "ascensionDate": "飞升日期", "assa": "暗杀次数",
    "bannedFromChurch": "禁止入教会", "bannedMarry": "禁止结婚",
    "betrayedFaction": "背叛派系", "bonusReward": "额外奖励",
    "bossesDefeated": "击败首领", "bountiesCompleted": "完成赏金",
    "brawls": "斗殴次数", "cellDoorOpen": "牢门打开", "challengesCompleted": "完成挑战",
    "characterCreated": "已创建角色", "charismaBonus": "魅力加成",
    "charitableActions": "慈善行为", "chestContents": "宝箱内容",
    "constitutionBonus": "体质加成",
    "chivNr": "善良行为数", "comment": "说明", "companionsLost": "失去同伴",
    "companionsSaved": "拯救同伴", "completionTime": "完成时间",
    "confessionAccepted": "忏悔已接受", "count": "数量", "currentValue": "当前值",
    "cursed": "被诅咒", "dailySalary": "每日薪水", "darkChoicesMade": "黑暗选择",
    "darkNr": "黑暗行为数", "daysAsRuler": "统治天数", "daysSinceDevotion": "距上次虔诚",
    "daysSinceSpellCast": "距上次施法", "deathDate": "死亡日期", "deedsLeft": "剩余善举",
    "defenceBonus": "防御加成", "deleted": "已删除", "dexterityBonus": "灵巧加成",
    "divineBlessingBonus": "神圣祝福加成", "divineBlessingCombats": "神圣祝福战斗",
    "divineBoonConfig": "神圣恩惠配置", "divineDomain": "神域", "divineName": "神名",
    "drinksLeft": "剩余饮品", "dungeon": "地牢", "dungeonFloorsExplored": "已探索地牢层",
    "encountersHad": "遭遇次数", "executeLeft": "剩余处决",
    "experienceFromMonsters": "怪物经验", "experienceFromQuests": "任务经验",
    "experienceFromTraining": "训练经验", "factionRank": "派系等级",
    "factionReputation": "派系声望", "fatherID": "父亲ID", "godAlignment": "神明阵营",
    "godExperience": "神明经验", "godFavor": "神明恩宠", "godFavorGod": "恩宠神明",
    "godFavorSchema": "恩宠结构", "godLevel": "神明等级",
    "godStandingPenaltyWeek": "神明声望惩罚周", "hasBetrayedFaction": "背叛过派系",
    "hasBossSlayer": "拥有弑神者", "hasConfessed": "已忏悔",
    "hasEarnedAltSlot": "获得备用槽", "healingActionsTaken": "治疗行为",
    "highestSingleHit": "单次最高伤害", "idTag1": "ID标签1", "idTag2": "ID标签2",
    "intelligenceBonus": "智力加成", "isBloodMoon": "血月", "isImmortal": "不朽",
    "isMurderConvict": "谋杀犯", "isOptional": "可选", "itemsCrafted": "制作物品",
    "jealousy": "嫉妒", "jokesOrTricksMade": "玩笑/恶作剧", "killedBy1": "击杀者1",
    "killedBy2": "击杀者2", "knowledgeGained": "获得知识",
    "lastDexterityTraining": "上次灵巧训练", "lastGodSwitchDay": "上次改信日",
    "lastPlayed": "上次游玩", "lastPlayerContactDay": "上次联系玩家日",
    "lastStrengthTraining": "上次力量训练", "lastTugOfWar": "上次拔河",
    "lastUpdated": "上次更新", "lastWrestling": "上次摔跤",
    "leadershipActions": "领导行为", "lootEffects": "战利品效果",
    "magicHag": "魔法讨价还价", "magicShopBarredUntilDay": "魔法店禁止至天",
    "marriagesFormed": "缔结婚姻", "marriedDays": "已婚天数",
    "mentalBroken": "精神崩溃", "mentalDrugBoost": "精神药物增益",
    "mentalDrugUses": "精神药物使用", "mentalHintShown": "精神提示",
    "mentalLastDrugDay": "上次精神药物日", "mentalRecoveryUsedToday": "今日精神恢复",
    "mentalSchema": "精神结构", "mentalStrainRemainder": "精神压力余数",
    "mercifulChoices": "仁慈选择", "miracleUsedToday": "今日神迹",
    "monsterName": "怪物名", "monsterType": "怪物类型", "monstersKilled": "击杀怪物",
    "mostExpensivePurchase": "最贵购买", "motherID": "母亲ID", "mudTitle": "MUD头衔",
    "neglectLetterSentDay": "忽视信日", "nightmareStartLevel": "噩梦起始等级",
    "objectiveType": "目标类型", "orientation": "性取向",
    "pendingGroupDeath": "待处理队伍死亡", "permanentDamageBonus": "永久伤害加成",
    "permanentDefenseBonus": "永久防御加成", "personalQuestSuccess": "个人任务成功",
    "playerFaction": "玩家派系", "playerKnowsTruth": "玩家知道真相",
    "playerSuspectsStranger": "玩家怀疑陌生人", "poisonDamage": "毒伤害",
    "previousWeeklyRank": "上周排名", "prisonActivitiesToday": "今日监狱活动",
    "prisonEscapes": "越狱次数", "prisonsLeft": "剩余入狱次数", "progress": "进度",
    "pvPDefeats": "PvP失败", "pvPVictories": "PvP胜利", "questsCompleted": "完成任务数",
    "questsLeft": "剩余任务", "recurringDuelist": "常客决斗者", "relation1": "关系1",
    "relation2": "关系2", "requiredProgress": "所需进度", "requiresEvil": "需要邪恶",
    "requiresGood": "需要善良", "rescuedBy": "被谁救出", "rivalLevel": "对手等级",
    "rivalName": "对手名字", "romanceEncounters": "恋爱遭遇",
    "royalMercenaries": "王室佣兵", "rulesDefied": "违反规则",
    "sealsCollected": "收集封印", "secretsDiscovered": "发现秘密",
    "sharedPotionBelt": "共享药剂带", "shieldBonus": "盾牌加成", "shop": "商店",
    "spellsCast": "施法次数", "spouse": "配偶", "staminaBonus": "耐力加成",
    "strengthBonus": "力量加成", "targetFloor": "目标楼层", "targetId": "目标ID",
    "targetName": "目标名字", "teamActions": "队伍行动", "thiefs": "偷窃次数",
    "timesRuler": "统治次数", "timestamp": "时间戳", "title": "标题",
    "totalAbilitiesUsed": "累计使用能力", "totalAccessoriesPurchased": "累计购买饰品",
    "totalCursesBroken": "累计破除诅咒", "totalDeathSpellsCast": "累计死亡法术",
    "totalDiseasesContracted": "累计染病", "totalDiseasesCured": "累计治愈疾病",
    "totalDungeonFloorsCovered": "累计下探楼层",
    "totalEnchantmentsApplied": "累计附魔", "totalEnemiesMade": "累计制造敌人",
    "totalGamblingRounds": "累计赌博回合",
    "totalGoldFromGambling": "赌博获得金币",
    "totalGoldFromMonsters": "怪物掉落金币", "totalGoldFromQuests": "任务获得金币",
    "totalGoldFromSelling": "出售获得金币",
    "totalGoldLostGambling": "赌博损失金币", "totalGoldLostToThieves": "被偷金币",
    "totalGoldStolen": "偷得金币", "totalHealthRestored": "累计恢复生命",
    "totalLoveSpellsCast": "累计爱情法术",
    "totalMagicShopGoldSpent": "魔法商店花费", "totalManaRestored": "累计恢复法力",
    "totalMonsterDeaths": "怪物死亡数",
    "totalMonstersEncountered": "累计遭遇怪物",
    "totalPickpocketAttempts": "累计扒窃尝试",
    "totalPickpocketSuccesses": "累计扒窃成功",
    "totalPitFightsLost": "竞技场失败", "totalPitFightsWon": "竞技场胜利",
    "totalPlayerDeaths": "玩家死亡数", "totalPoisonings": "累计下毒",
    "totalTeamBattles": "队伍战斗数", "totalUniquesKilled": "击杀独特怪物",
    "transformationsMade": "变形次数", "trust": "信任", "type": "类型",
    "value": "数值", "wealthAccumulated": "累计财富", "weapHag": "武器讨价还价",
    "weaponShopBarredUntilDay": "武器店禁止至天", "weeklyGod": "本周神明",
    "weeklyGodWeek": "本周神明周", "weeklyRank": "每周排名",
    "weightClass": "重量级", "willowDraughts": "柳树药剂", "wisdomBonus": "智慧加成",
    "worldBossDamageDealt": "世界首领伤害", "worldBossMVPCount": "世界首领MVP",
    "worldBossesKilled": "击杀世界首领",
}

# A short Chinese gloss for every field. Keys not listed here still get a generated
# "直译" note, and the C# save-model comments are added when available, so the editor
# never shows a field without an explanation.
TYPE_ZH = {"int": "整数", "float": "小数", "bool": "布尔", "str": "文本",
           "list": "列表", "dict": "对象", "null": "空值"}

OLD_GOD_NAMES = {0: "梅尔凯斯", 1: "薇洛拉", 2: "索格瑞姆", 3: "诺克图拉",
                 4: "奥雷利昂", 5: "泰拉沃克", 6: "曼威"}

FIELD_NOTES = {
    # top level
    "version": "存档格式版本，游戏用它判断是否迁移旧存档；一般不要改。",
    "saveTime": "这份存档的保存时间，只用于显示和排序。",
    "lastDailyReset": "上一次每日重置的时间。",
    "currentDay": "当前游戏天数；每日事件、房租、银行利息都按它计算。",
    "dailyCycleMode": "每日循环模式的枚举值。",
    "player": "玩家对象，保存角色的全部状态。",
    "npCs": "世界里的 NPC 名单，每项是一个 NPC 的完整存档。",
    "worldState": "世界状态：银行、城镇金库、事件、任务、拍卖行和定居点。",
    "settings": "自动存档与每日重置设置。",
    "storySystems": "剧情与系统状态：觉醒、封印、同伴、旧神、派系、王庭、梦境等。",

    # player identity and progress
    "id": "内部唯一标识，队伍、恋爱和家庭记录会引用它；一般不要改。",
    "name1": "玩家内部名字，通常与显示名相同。",
    "name2": "玩家显示名，NPC 和存档列表显示这个名字。",
    "realName": "剧情用的真名，可以为空。",
    "level": "当前等级。改高不会自动补发属性点、技能或装备。",
    "experience": "当前经验值；达到升级所需后可在等级导师处升级。",
    "class": "职业的枚举值；改职业不会重算已获得的属性。",
    "race": "种族的枚举值。",
    "sex": "性别文本（M/F 等）。",
    "age": "角色年龄。",
    "difficulty": "难度枚举值。",
    "specialization": "职业专精的枚举值。",
    "currentLocation": "当前所在地点代码，例如 Main Street。",
    "turnCount": "已经历的游戏回合数。",
    "turnsRemaining": "当天剩余行动回合。",
    "gameTimeMinutes": "游戏内已流逝的分钟数。",
    "daysInPrison": "剩余坐牢天数。",
    "resurrections": "可用复活次数。",
    "maxResurrections": "复活次数上限。",
    "resurrectionsUsed": "已经使用过的复活次数。",
    "playthroughDeaths": "本周目累计死亡次数。",
    "trainingPoints": "可用的训练点，在等级导师处花掉。",
    "quests": "完成的任务数量。",
    "royQuests": "完成的王室任务数量。",

    # resources
    "hp": "当前生命值；读档时不要高于最大生命。",
    "maxHP": "最大生命值；装备、祝福和永久加成会叠加到它上面。",
    "mana": "当前法力值。",
    "maxMana": "最大法力值。",
    "stamina": "耐力/体力，部分职业用它施放技能。",
    "healing": "治疗量或治疗相关数值。",
    "healingPotions": "治疗药剂数量。",
    "manaPotions": "法力药剂数量。",
    "antidotes": "解毒剂数量。",
    "poisonVials": "毒药瓶数量。",
    "smokeBombs": "烟雾弹数量。",
    "gold": "随身金币。",
    "bankGold": "银行里的存款。",
    "bankLoan": "当前银行贷款。",
    "bankWage": "银行工资/利息相关数值。",
    "bankInterest": "银行累计利息。",
    "bankGuard": "是否雇了银行守卫。",
    "bankRobberyAttempts": "尝试抢劫银行的次数。",
    "royalLoanAmount": "欠王室的贷款金额。",
    "royalLoanDueDay": "王室贷款的到期游戏日。",
    "royalLoanBountyPosted": "王室是否已为这笔贷款发布悬赏。",
    "loanAmount": "小额贷款本金。",
    "loanDaysRemaining": "小额贷款剩余天数。",
    "loanInterestAccrued": "小额贷款累计利息。",

    # attributes and combat
    "strength": "力量：影响近战伤害。",
    "defence": "防御：影响受到的伤害。",
    "agility": "敏捷：影响命中、闪避和出手顺序。",
    "dexterity": "灵巧：影响命中、暴击和部分技能。",
    "charisma": "魅力：影响对话、恋爱和商店价格。",
    "intelligence": "智力：影响法术和部分职业能力。",
    "wisdom": "智慧：影响法力和部分职业能力。",
    "constitution": "体质：影响最大生命和抗性。",
    "baseStrength": "基础力量，不含装备与临时加成。",
    "baseDefence": "基础防御，不含装备与临时加成。",
    "baseAgility": "基础敏捷，不含装备与临时加成。",
    "baseDexterity": "基础灵巧，不含装备与临时加成。",
    "baseCharisma": "基础魅力，不含装备与临时加成。",
    "baseIntelligence": "基础智力，不含装备与临时加成。",
    "baseWisdom": "基础智慧，不含装备与临时加成。",
    "baseConstitution": "基础体质，不含装备与临时加成。",
    "baseStamina": "基础耐力，不含装备与临时加成。",
    "weapPow": "武器威力合计；由已装备武器和加成决定。",
    "armPow": "护甲威力合计；由已装备护甲和加成决定。",
    "fame": "声望。",
    "chivalry": "善良/守序倾向，与 darkness 相对。",
    "darkness": "黑暗/邪恶倾向，与 chivalry 相对。",
    "mental": "精神值；过低会触发精神崩溃相关状态。",
    "combatSpeed": "战斗速度偏好（瞬间/快速/正常）。",
    "autoCombatHealPercent": "自动喝治疗药剂的生命阈值百分比。",
    "fights": "普通战斗次数。",
    "pFights": "玩家对玩家战斗次数。",
    "tFights": "队伍战斗次数。",
    "mKills": "击杀怪物数。",
    "mDefeats": "被怪物击败次数。",
    "pKills": "击杀玩家数。",
    "pDefeats": "被玩家击败次数。",
    "murderWeight": "谋杀行为累计的罪恶值。",
    "wantedLvl": "通缉等级。",
    "poison": "当前中毒层数/数值。",
    "poisonTurns": "中毒剩余回合。",

    # inventory and abilities
    "items": "物品 ID 列表；与 itemTypes 一一对应，增删会同时影响两边的对齐。",
    "itemTypes": "物品类型列表；与 items 一一对应。",
    "inventory": "背包里的物品对象。",
    "equippedItems": "已装备物品，按装备槽保存。",
    "dynamicEquipment": "动态生成的装备（附魔或掉落物）。",
    "quickbar": "快捷栏 1-9 的技能/法术绑定，长度固定。",
    "spells": "法术学习表；每行通常是 [已学, 已精通]。",
    "skills": "技能列表。",
    "learnedAbilities": "已学会的职业能力。",
    "skillProficiencies": "技能熟练度。",
    "skillTrainingProgress": "技能训练进度。",
    "craftingMaterials": "制作材料。",
    "activeQuests": "进行中的任务列表。",
    "achievements": "已解锁成就。",
    "achievementsData": "成就进度数据。",
    "statistics": "生涯统计；主要供界面展示。",
    "phrases": "角色台词/外观短语，长度固定。",
    "description": "该条目的描述文本，具体含义随所在对象而定。",
    "relationships": "与 NPC 的关系数据。",
    "romanceData": "恋爱、婚姻和家庭数据。",
    "teammateStances": "每名队友的战斗姿态。",
    "teammateDisabledAbilities": "被禁用的队友能力。",
    "teammateDisabledSpells": "被禁用的队友法术。",
    "team": "所属队伍名。",
    "teamPassword": "队伍密码。",
    "isTeamLeader": "是否是队伍队长。",
    "teamRec": "队伍招募相关数值。",
    "teamXPPercent": "每名队友分得的经验比例，长度固定。",
    "teamXPIsExplicit": "是否手动指定了队伍经验分配。",
    "teamXPEvenSplit": "是否按队伍人数平均分配经验。",

    # appearance and settings
    "height": "身高。", "weight": "体重。", "eyes": "眼睛颜色。",
    "hair": "头发颜色。", "skin": "肤色。",
    "language": "界面语言代码。",
    "autoHeal": "是否自动使用治疗药剂。",
    "screenReaderMode": "是否启用屏幕阅读器模式。",
    "compactMode": "是否使用紧凑界面。",
    "autoLook": "进入地点时是否自动观察。",
    "dungeonAutoMap": "是否自动绘制地牢地图。",
    "autoLevelUp": "是否自动升级。",
    "autoEquipDisabled": "是否禁用自动装备。",
    "colorTheme": "界面配色主题。",
    "dateFormatPreference": "日期显示格式。",
    "menuKeysNeedEnter": "菜单按键是否需要再按回车。",
    "webMenuKeysNeedEnter": "网页版菜单按键是否需要回车。",
    "classicMainStreet": "是否使用经典主街布局。",
    "districtsMainStreet": "主街是否按街区显示。",
    "autoRedistributeXP": "是否自动重新分配队伍经验。",
    "loginStreak": "当前连续登录天数。",
    "longestLoginStreak": "最长连续登录天数。",
    "lastLogin": "上次登录时间。",
    "lastLoginDate": "上次登录日期。",
    "accountCreated": "账号创建时间。",

    # home, buffs and daily counters
    "homeLevel": "家园等级。", "chestLevel": "宝箱等级。",
    "trainingRoomLevel": "训练室等级。", "gardenLevel": "花园等级。",
    "bedLevel": "床铺等级。", "hearthLevel": "壁炉等级。",
    "hasTrophyRoom": "是否建有 trophy room。",
    "hasTeleportCircle": "是否建有传送阵。",
    "hasLegendaryArmory": "是否建有传说军械库。",
    "hasVitalityFountain": "是否建有活力喷泉。",
    "hasStudy": "是否建有书房。",
    "hasServants": "是否雇佣了仆人。",
    "hasReinforcedDoor": "是否安装了加固门。",
    "herbHealing": "草药：治疗草数量。",
    "herbIronbark": "草药：铁皮草数量。",
    "herbFirebloom": "草药：火焰花数量。",
    "herbSwiftthistle": "草药：疾风蓟数量。",
    "herbStarbloom": "草药：星花数量。",
    "herbBuffType": "草药增益类型。",
    "herbBuffCombats": "草药增益剩余战斗次数。",
    "herbBuffValue": "草药增益数值。",
    "foodBuffType": "食物增益类型。",
    "foodBuffCombats": "食物增益剩余战斗次数。",
    "foodBuffValue": "食物增益数值。",
    "songBuffType": "歌曲增益类型。",
    "songBuffCombats": "歌曲增益剩余战斗次数。",
    "songBuffValue": "歌曲增益数值。",
    "settlementBuffType": "定居点增益类型。",
    "settlementBuffCombats": "定居点增益剩余战斗次数。",
    "settlementBuffValue": "定居点增益数值。",

    # NPC
    "archetype": "NPC 原型（guard、merchant 等），影响行为与对话。",
    "location": "NPC 当前所在地点。",
    "isDead": "NPC 是否已经死亡。",
    "isPermaDead": "是否永久死亡；复活手段通常无效。",
    "isMarried": "是否已婚。", "married": "是否已婚（兼容旧字段）。",
    "spouseName": "配偶名字。",
    "isKing": "是否是国王。",
    "isHostile": "是否对玩家敌对。",
    "isAIDriven": "是否由世界模拟的 AI 驱动。",
    "isTeamLeader": "是否是所在队伍的队长。",
    "worshippedGod": "信奉的神明。",
    "npcFaction": "NPC 所属派系。",
    "gangId": "所属帮派 ID；空字符串表示没有帮派。",
    "personalityProfile": "NPC 性格：攻击性、贪婪、勇气、社交性等。",
    "memories": "NPC 对玩家和其他角色的记忆。",
    "memoryTimesKept": "是否保留真实记忆时间。",
    "currentGoals": "NPC 当前的目标。",
    "emotionalState": "NPC 当前情绪。",
    "enemies": "NPC 的敌人。",
    "knownCharacters": "NPC 认识的角色。",
    "marketInventory": "商人 NPC 的商店库存。",
    "equippedItemsSave": "同伴已装备的物品。",
    "disabledAbilities": "被禁用的能力。", "disabledSpells": "被禁用的法术。",

    # companions
    "isRecruited": "是否已经招募这名同伴。",
    "isActive": "是否在出战队伍里；应与 activeCompanionIds 保持一致。",
    "loyaltyLevel": "同伴忠诚度（0-100）。",
    "trustLevel": "同伴信任度（0-100）。",
    "romanceLevel": "同伴恋爱度（0-100）。",
    "personalQuestStarted": "同伴个人任务是否已开始。",
    "personalQuestCompleted": "同伴个人任务是否已完成。",
    "personalQuestSuccess": "同伴个人任务是否成功。",
    "recruitedDay": "招募发生在第几个游戏日。",
    "companions": "五名剧情同伴的完整存档。",
    "activeCompanionIds": "出战同伴的 ID 列表；最多 4 名。",
    "fallenCompanions": "已阵亡同伴的记录。",
    "dungeonPartyNPCIds": "进入地牢时带到身边的 NPC ID 列表；最多 4 名。",
    "dungeonPartyPlayerNames": "地牢队伍中的其他玩家名字（在线回声）。",
    "activeGriefs": "正在进行的哀伤状态。",
    "griefMemories": "与哀伤相关的记忆。",

    # world
    "bankInterestRate": "银行利率（整数百分比或内部单位）。",
    "bankVaultReserve": "银行金库储备。",
    "bankRobberiesToday": "今日银行被抢次数。",
    "bankRobberiesDate": "银行抢劫计数对应的日期。",
    "townPotValue": "城镇公共金库金额。",
    "currentRuler": "当前统治者；空表示没有。",
    "activeEvents": "进行中的世界事件。",
    "shopInventories": "各商店的库存。",
    "recentNews": "最近的城镇新闻。",
    "marketplaceListings": "拍卖行的挂售记录。",
    "settlement": "地牢定居点状态。",
    "usedNPCNames": "世界已经使用过的 NPC 名字，避免重名。",

    # story
    "awakeningLevel": "海洋哲学的觉醒等级。",
    "collectedFragments": "已收集的觉醒碎片。",
    "experiencedMoments": "已经历的觉醒时刻。",
    "oceanInsightIds": "已获得的海洋洞见 ID。",
    "completedParadoxIds": "已回答的道德悖论 ID。",
    "collectedSeals": "已找到的封印 ID。",
    "collectedArtifacts": "已收集的神器 ID。",
    "griefStage": "哀伤阶段（旧字段）。",
    "griefDaysRemaining": "哀伤剩余天数（旧字段）。",
    "griefCompanionName": "哀伤对象名字（旧字段）。",
    "activeNpcGriefs": "NPC 队友的哀伤状态。",
    "storyFlags": "剧情标记字典；true 表示该标记已置位。",
    "currentCycle": "新游戏+轮回数。",
    "completedEndings": "已完成的结局 ID。",
    "oldGodStates": "旧神状态字典：键是旧神编号。",
    "oldGodsEncountered": "已经遇到过的旧神。",
    "currentChapter": "当前剧情章节编号。",
    "storyFlagBits": "剧情标记位（打包成整数的标记）。",
    "majorChoices": "重大剧情选择记录。",
    "playerGods": "玩家信奉的神明字典。",
    "children": "玩家的孩子。",
    "archetypeTracker": "荣格原型追踪数据。",
    "royalCourt": "王庭状态：国王、税率、宫廷成员、阴谋等。",
    "factions": "派系声望与关系。",
    "townNPCStories": "镇民故事线的进度。",
    "dreams": "梦境系统状态。",
    "amnesia": "失忆系统状态。",
    "betrayal": "背叛系统状态。",
    "culturalMemes": "文化模因状态。",
    "npcMarriages": "NPC 之间的婚姻。",
    "affairs": "NPC 婚外情记录。",
    "griefMemories": "哀伤记忆。",

    # settings
    "mode": "每日循环模式。",
    "lastResetTime": "上次每日重置时间。",
    "autoSaveEnabled": "是否启用自动存档。",
    "autoSaveInterval": "自动存档间隔（文本）。",

    # common list/object labels
    "npcStates": "镇民故事线里每个 NPC 的状态。",
    "npcId": "镇民故事使用的 NPC 标识。",
    "currentStage": "当前故事阶段。",
    "completedStages": "已完成的故事阶段。",
    "choicesMade": "在每个阶段做过的选择。",
    "stageCompletedOnDay": "每个阶段完成的游戏日。",
    "npcRelationship": "与镇民故事 NPC 的关系值。",

    # personality and emotion values (0.0-1.0 unless the game clamps them)
    "aggression": "攻击性（约 0-1）：越高越容易选择攻击、挑衅和敌对行为。",
    "greed": "贪婪（约 0-1）：越高越看重金钱、交易和占便宜。",
    "courage": "勇气（约 0-1）：越高越敢进入战斗和冒险。",
    "vengefulness": "报复心（约 0-1）：越高越容易记仇并追求复仇。",
    "impulsiveness": "冲动（约 0-1）：越高越容易随机选择非最优行动。",
    "sociability": "社交性（约 0-1）：越高越常去酒馆、交友和闲聊。",
    "ambition": "野心（约 0-1）：越高越追求权力与地位。",
    "trustworthiness": "可信度（约 0-1）：越高越不容易背叛或撒谎。",
    "caution": "谨慎（约 0-1）：越高越倾向规避风险。",
    "mysticism": "神秘倾向（约 0-1）：越高越接近神明、仪式和魔法。",
    "patience": "耐心（约 0-1）：影响等待与长期目标。",
    "romanticism": "浪漫（约 0-1）：影响恋爱与婚姻行为。",
    "flirtatiousness": "调情倾向（约 0-1）。",
    "passion": "热情（约 0-1），影响亲密关系。",
    "tenderness": "温柔（约 0-1），影响亲密关系。",
    "anger": "愤怒情绪强度（约 0-1）。",
    "fear": "恐惧情绪强度（约 0-1）。",
    "sadness": "悲伤情绪强度（约 0-1）。",
    "joy": "喜悦情绪强度（约 0-1）。",
    "confidence": "自信情绪强度（约 0-1）。",
    "loneliness": "孤独情绪强度（约 0-1）。",
    "hope": "希望情绪强度（约 0-1）。",
    "peace": "平静情绪强度（约 0-1）。",
    "envy": "嫉妒情绪强度（约 0-1）。",
    "pride": "骄傲情绪强度（约 0-1）。",

    # memory / relationship / goal entries
    "importance": "重要度（约 0-1）；越高的记忆越容易被 NPC 提起。",
    "emotionalImpact": "这条记忆带来的情感影响。",
    "involvedCharacter": "这条记忆或关系涉及的角色名。",
    "targetCharacter": "目标角色的名字。",
    "targetLocation": "目标地点代码。",
    "targetValue": "目标进度值。",
    "currentValue": "当前进度值。",
    "progress": "当前进度（0-1）。",
    "priority": "优先级（约 0-1）；越高越容易被选中。",
    "isCompleted": "是否已完成。",
    "createdTime": "创建时间。",
    "timestamp": "记录时间。",

    # item / equipment entries
    "weaponPower": "武器威力，影响攻击伤害。",
    "armorClass": "护甲等级，影响受到的伤害。",
    "armorType": "护甲类型（枚举整数）。",
    "weaponType": "武器类型（枚举整数）。",
    "slot": "装备槽（枚举整数）。",
    "rarity": "稀有度（枚举整数）。",
    "isIdentified": "是否已经鉴定。",
    "isCursed": "是否被诅咒。",
    "strengthRequired": "使用这件装备所需的力量。",
    "bonusMaxHP": "装备或效果提供的最大生命加成。",
    "bonusWeapPow": "装备或效果提供的武器威力加成。",
    "bonusArmPow": "装备或效果提供的护甲威力加成。",

    # quest / event / marketplace entries
    "status": "状态（枚举整数）。",
    "reward": "奖励数值。",
    "rewardType": "奖励类型（枚举整数）。",
    "penalty": "惩罚数值。",
    "penaltyType": "惩罚类型（枚举整数）。",
    "difficulty": "难度（枚举整数或等级）。",
    "daysToComplete": "任务允许完成的天数。",
    "minLevel": "接取或出现的最低等级。",
    "maxLevel": "接取或出现的最高等级。",
    "questType": "任务类型（枚举整数）。",
    "questTarget": "任务目标标识。",
    "targetNPCName": "任务目标的 NPC 名字。",
    "objectives": "任务目标列表。",
    "monsters": "任务或事件涉及的怪物列表。",
    "isPlayerBounty": "是否是针对玩家的悬赏。",
    "bountyGold": "悬赏金额。",
    "isMercContract": "是否是雇佣兵契约。",
    "issuingFaction": "发布任务的派系。",
    "mercContractTier": "雇佣兵契约层级。",
    "item": "物品对象。",
    "seller": "卖家名字。",
    "isNPCSeller": "卖家是否是 NPC。",
    "sellerNPCId": "卖家 NPC 的 ID。",
    "price": "价格。",
    "posted": "挂售时间。",
}

# Tokens for the generated "直译" note. Unknown tokens stay in English, so the note
# is still honest when a field has no curated description.
WORD_ZH = {
    "total": "累计", "today": "今日", "last": "上次", "bonus": "加成", "has": "拥有",
    "god": "神明", "active": "进行中", "type": "类型", "day": "天", "days": "天数",
    "is": "是否", "gold": "金币", "buff": "增益", "combats": "战斗", "id": "编号",
    "ids": "编号", "name": "名称", "date": "日期", "used": "已使用", "player": "玩家",
    "herb": "草药", "shop": "商店", "completed": "已完成", "level": "等级",
    "value": "数值", "settlement": "定居点", "damage": "伤害", "mental": "精神",
    "enchant": "附魔", "divine": "神圣", "from": "来自", "team": "队伍",
    "faction": "派系", "left": "剩余", "magic": "魔法", "dungeon": "地牢",
    "armor": "护甲", "npc": "NPC", "proposal": "提案", "stats": "属性",
    "killed": "击杀", "target": "目标", "base": "基础", "choices": "选择",
    "spells": "法术", "drug": "药物", "merc": "雇佣兵", "encounters": "遭遇",
    "quests": "任务", "loan": "贷款", "claimed": "已领取", "monsters": "怪物",
    "shrine": "神龛", "actions": "行动", "time": "时间", "cast": "施放",
    "made": "做出", "title": "头衔", "weapon": "武器", "king": "国王",
    "cursed": "诅咒", "favor": "恩宠", "monster": "怪物", "lost": "损失",
    "utc": "UTC", "item": "物品", "items": "物品", "earned": "获得",
    "royal": "王室", "experience": "经验", "mana": "法力", "pending": "待处理",
    "building": "建筑", "tax": "税", "dark": "黑暗", "moral": "道德",
    "created": "创建", "game": "游戏", "power": "力量", "slayer": "屠戮者",
    "death": "死亡", "key": "键", "fights": "战斗", "applied": "已应用",
    "blessing": "祝福", "current": "当前", "lovers": "恋人", "standing": "声望",
    "max": "最大", "gambling": "赌博", "training": "训练", "weekly": "每周",
    "boss": "首领", "healing": "治疗", "poison": "中毒", "song": "歌曲",
    "strength": "力量", "world": "世界", "character": "角色", "count": "次数",
    "market": "市场", "hp": "生命", "since": "自", "login": "登录",
    "streak": "连续", "xp": "经验", "times": "次数", "disabled": "禁用",
    "quest": "任务", "betrayed": "背叛", "bank": "银行", "guard": "守卫",
    "floors": "楼层", "reward": "奖励", "church": "教会", "shown": "已显示",
    "abilities": "技能", "args": "参数", "seller": "卖家", "description": "描述",
    "pit": "竞技场", "stranger": "陌生人", "father": "父亲", "shield": "盾牌",
    "history": "历史", "weight": "重量", "street": "街道", "penalty": "惩罚",
    "week": "周", "stat": "属性", "ticks": "计时", "personal": "个人",
    "teammate": "队友", "bounty": "赏金", "critical": "暴击", "progress": "进度",
    "workshop": "工坊", "daily": "每日", "real": "真实", "wilderness": "荒野",
    "bosses": "首领", "comment": "评论", "intimate": "亲密", "barred": "禁止",
    "until": "直到", "rank": "等级", "wrath": "愤怒", "class": "职业",
    "defense": "防御", "highest": "最高", "food": "食物", "black": "黑",
    "betrayal": "背叛", "proposed": "提议", "played": "游玩", "family": "家庭",
    "attuned": "调谐", "attempts": "尝试", "nr": "编号", "floor": "楼层",
    "hag": "讨价还价", "arm": "护甲", "pet": "宠物", "songs": "歌曲",
    "explored": "已探索", "constitution": "体质", "tier": "层级",
    "taken": "已承受", "shadow": "暗影", "contracts": "契约", "banned": "禁止",
    "finger": "手指", "pregnancy": "怀孕", "due": "预产", "relationship": "关系",
    "tavern": "酒馆", "vote": "投票", "hand": "手", "schema": "结构",
    "given": "已给予", "jealousy": "嫉妒", "defeats": "失败", "original": "原始",
    "holy": "神圣", "companions": "同伴", "rival": "对手", "gained": "获得",
    "requires": "需要", "extra": "额外", "town": "城镇", "money": "金钱",
    "encounter": "遭遇", "success": "成功", "failed": "失败", "attack": "攻击",
    "defence": "防御", "chance": "几率", "amount": "数量", "duration": "持续",
    "turns": "回合", "rounds": "回合", "remaining": "剩余", "min": "最小",
    "rate": "速率", "percent": "百分比", "modifier": "修正", "multiplier": "倍率",
    "cost": "花费", "price": "价格", "quality": "品质", "rarity": "稀有度",
    "unique": "独特", "special": "特殊", "normal": "普通", "rare": "稀有",
    "epic": "史诗", "legendary": "传说", "unlocked": "已解锁", "seen": "已见过",
    "known": "已知", "visited": "已访问", "discovered": "已发现",
    "finished": "已完成", "started": "已开始", "skipped": "跳过", "read": "已读",
    "heard": "已听过", "found": "已找到", "defeated": "击败", "won": "获胜",
    "fled": "逃跑", "dealt": "造成", "received": "受到", "spent": "花费",
    "sold": "售出", "bought": "购买", "crafted": "制作", "gathered": "采集",
    "average": "平均", "best": "最佳", "worst": "最差", "first": "首次",
    "next": "下次", "previous": "上次", "recent": "最近", "monthly": "每月",
    "yearly": "每年", "hourly": "每小时", "minute": "分钟", "hour": "小时",
    "second": "秒", "morning": "早晨", "afternoon": "下午", "evening": "傍晚",
    "night": "夜晚",
}

SAVE_HINT = ("保存前请关闭游戏：游戏运行时会用自动存档覆盖修改。"
             " 每次保存前都会在存档旁生成带时间戳的备份。")


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
        raise ValueError(f"{path.name} 里没有 player 对象")
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
        return "外观描述"
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
        if lowered in ("true", "1", "yes", "y", "是", "真"):
            return True
        if lowered in ("false", "0", "no", "n", "否", "假"):
            return False
        raise ValueError("需要 true/false、是/否 或 1/0")

    if kind == "int":
        try:
            return int(text.strip())
        except ValueError:
            raise ValueError("需要整数") from None

    if kind == "float":
        try:
            value = float(text.strip())
        except ValueError:
            raise ValueError("需要数字") from None
        if not math.isfinite(value):
            raise ValueError("需要有限数字")
        return value

    if kind == "null":
        raise ValueError("这个字段是 null，类型未知，不能直接改")

    return text


NAME_KEYS = {"name", "name1", "name2", "realName"}
MARKUP_CHARS = set('<>&"')


def validate_change(path: tuple, current: Any, text: str) -> Any:
    """Coerce a staged value, refusing a name that carries markup the game bans."""
    value = coerce(current, text)
    if path and str(path[-1]) in NAME_KEYS and isinstance(value, str):
        bad = sorted(set(value) & MARKUP_CHARS)
        if bad:
            raise ValueError(f"名字不能包含 {' '.join(bad)}")
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
            refused.append(f"{path_text(path)}: 这个存档已经没有这个字段")
            continue
        if not is_editable(current):
            refused.append(f"{path_text(path)}: 不是简单值")
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
        raise ValueError("目标不是列表")
    target.append(value)


def list_remove(data: dict, list_path: tuple, index: int) -> Any:
    target = get_path(data, list_path)
    if not isinstance(target, list):
        raise ValueError("目标不是列表")
    if not 0 <= index < len(target):
        raise ValueError("下标超出列表范围")
    return target.pop(index)


def check(directory: Path) -> int:
    saves = list_saves(directory)
    if not saves:
        print(f"没有找到存档：{directory}")
        return 1
    print(f"存档目录：{directory}")
    for path in saves[:10]:
        try:
            data = load_save(path)
        except (ValueError, json.JSONDecodeError) as error:
            print(f"  {path.name}: 读不了（{error}）")
            continue
        player = data["player"]
        leaves = list(iter_leaves(data))
        editable = sum(1 for leaf in leaves if not leaf.is_container and is_editable(leaf.value))
        print(f"  {path.name}: Lv.{player.get('level')} {player.get('name2')}，"
              f"{len(data.get('npCs') or [])} 个 NPC，"
              f"{editable} 个可编辑字段（另有 {sum(1 for x in leaves if x.is_container)} 个列表）")
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
        self.root.title("Usurper Reborn 存档编辑器")
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
        ttk.Label(top, text="存档").pack(side="left")
        self.save_box = ttk.Combobox(top, state="readonly", width=54)
        self.save_box.pack(side="left", padx=6)
        self.save_box.bind("<<ComboboxSelected>>", lambda _event: self.load_selected())
        ttk.Button(top, text="重新扫描", command=self.rescan_saves).pack(side="left")
        ttk.Button(top, text="换目录", command=self.choose_directory).pack(side="left", padx=(6, 0))
        ttk.Button(top, text="打开目录", command=self.open_directory).pack(side="left", padx=(6, 0))

        top2 = ttk.Frame(self.root, padding=(8, 0, 8, 6))
        top2.pack(fill="x")
        ttk.Label(top2, text="区域").pack(side="left")
        self.section_box = ttk.Combobox(top2, state="readonly", width=14,
                                        values=[name for name, _ in SECTIONS])
        self.section_box.current(0)
        self.section_box.pack(side="left", padx=6)
        self.section_box.bind("<<ComboboxSelected>>", lambda _event: self.render())

        ttk.Label(top2, text="NPC").pack(side="left", padx=(10, 0))
        self.npc_box = ttk.Combobox(top2, state="readonly", width=38, values=[])
        self.npc_box.pack(side="left", padx=6)
        self.npc_box.bind("<<ComboboxSelected>>", lambda _event: self.on_npc_changed())

        ttk.Label(top2, text="搜索").pack(side="left", padx=(10, 0))
        self.search = ttk.Entry(top2, width=28)
        self.search.pack(side="left", padx=6)
        self.search.bind("<KeyRelease>", lambda _event: self.render())
        ttk.Button(top2, text="清除", command=self.clear_search).pack(side="left")

        bar = ttk.Frame(self.root, padding=(8, 0, 8, 6))
        bar.pack(fill="x")
        ttk.Button(bar, text="同伴管理", command=self.open_companion_manager).pack(side="left")
        ttk.Button(bar, text="地牢队伍", command=self.open_party_manager).pack(side="left", padx=6)
        self.save_button = ttk.Button(bar, text="保存全部改动", command=self.save)
        self.save_button.pack(side="left", padx=(18, 0))
        ttk.Button(bar, text="重新读取（放弃改动）", command=self.reload).pack(side="left", padx=6)
        self.change_count = ttk.Label(bar, text="没有未保存改动", foreground="#555")
        self.change_count.pack(side="right")

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
        self.list.heading("#0", text="字段")
        self.list.heading("value", text="当前值")
        self.list.heading("type", text="类型")
        self.list.heading("note", text="说明")
        self.list.heading("path", text="路径")
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

        self.field_label = ttk.Label(right, text="（选一个字段）", font=("Segoe UI", 11, "bold"),
                                     wraplength=310)
        self.field_label.pack(anchor="w", pady=(4, 2))
        self.path_label = ttk.Label(right, text="", foreground="#555", wraplength=310)
        self.path_label.pack(anchor="w", pady=(0, 6))

        ttk.Label(right, text="字段说明").pack(anchor="w")
        note_frame = ttk.Frame(right)
        note_frame.pack(fill="x", pady=(2, 8))
        self.note = tk.Text(note_frame, height=5, wrap="word", state="disabled")
        self.note.pack(side="left", fill="both", expand=True)
        note_bar = ttk.Scrollbar(note_frame, orient="vertical", command=self.note.yview)
        note_bar.pack(side="right", fill="y")
        self.note.configure(yscrollcommand=note_bar.set)

        ttk.Label(right, text="当前值").pack(anchor="w")
        self.current_label = ttk.Label(right, text="—", foreground="#333", wraplength=310)
        self.current_label.pack(anchor="w", pady=(0, 8))

        ttk.Label(right, text="新值").pack(anchor="w")
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
        self.apply_button = ttk.Button(buttons, text="应用这一项", command=self.stage_selected)
        self.apply_button.pack(side="left")
        self.revert_button = ttk.Button(buttons, text="恢复这一项", command=self.revert_selected)
        self.revert_button.pack(side="left", padx=6)

        self.bool_frame = ttk.Frame(right)
        self.bool_frame.pack(fill="x", pady=(6, 0))
        ttk.Button(self.bool_frame, text="设为 true", command=lambda: self.set_editor("true")).pack(side="left")
        ttk.Button(self.bool_frame, text="设为 false", command=lambda: self.set_editor("false")).pack(side="left", padx=6)

        ttk.Separator(right).pack(fill="x", pady=12)
        ttk.Label(right, text="列表工具").pack(anchor="w")
        self.add_button = ttk.Button(right, text="向列表添加元素", command=self.add_to_list)
        self.add_button.pack(fill="x", pady=(4, 4))
        self.delete_button = ttk.Button(right, text="删除选中的列表元素", command=self.delete_from_list)
        self.delete_button.pack(fill="x")

        ttk.Separator(right).pack(fill="x", pady=12)
        ttk.Label(right, text="说明", foreground="#555", wraplength=310).pack(anchor="w")
        ttk.Label(right, text="Ctrl+Enter 应用这一项，Ctrl+S 保存，F5 重新读取。"
                             "只有保存时才会写文件。固定长度的列表不能增删；"
                             "items 与 itemTypes 等成对列表会先要求确认。",
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
            self.say(f"没有找到存档：{self.directory}")
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
                                         title="选择存档目录")
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
            self.say(f"打不开目录：{error}")

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
            self.say(f"读取失败：{error}")
            return
        self.save_path = path
        self.data = data
        self.pending.clear()
        self.dirty = False
        self.npc_index = None
        self.rebuild_view()
        player = data.get("player", {})
        self.say(f"{path.name}：{player.get('name2')}  Lv.{player.get('level')}，"
                 f"{len(data.get('npCs') or [])} 个 NPC，{len(self.all_leaves)} 行可浏览。")

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
            "放弃改动？", "还有未保存的改动。放弃它们并继续吗？", parent=self.root))

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
                values.append("（无法识别的 NPC）")
                continue
            dead = " · 已死亡" if npc.get("isDead") else ""
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

    def matches(self, leaf: Leaf, needle: str) -> bool:
        haystack = f"{path_text(leaf.path)} {self.field_text(leaf)} {display_value(leaf.value)}".lower()
        return needle in haystack

    def field_text(self, leaf: Leaf) -> str:
        path = leaf.path
        name = label_of(path)
        if leaf.is_container:
            return f"{name}（列表）"
        prefix = self.context_prefix(path)
        return f"{prefix}{name}"

    def row_value(self, leaf: Leaf, value: Any) -> str:
        if not leaf.is_container and isinstance(value, int):
            if leaf.path[:-1] == ("storySystems", "activeCompanionIds"):
                name = COMPANION_NAMES.get(value)
                return f"{value}" + (f"（{name}）" if name else "")
        if not leaf.is_container and isinstance(value, str):
            if leaf.path[:-1] == ("storySystems", "dungeonPartyNPCIds"):
                return f"{display_value(value)}（{self.npc_name_by_id(value)}）"
        return display_value(value)

    def describe(self, leaf: Leaf) -> str:
        """One explanation for every row: curated, then the game's comment, then a direct gloss."""
        path = leaf.path
        if leaf.is_container:
            text = f"列表「{label_of(path)}」，共 {leaf.list_length} 项。"
            if leaf.scalar_list:
                if path in FIXED_LISTS:
                    text += " 这是固定长度列表，只能修改已有元素，不能增删。"
                else:
                    text += "每个元素都是简单值，选中本行后可在右侧添加元素。"
                if path in PAIRED_LISTS:
                    text += f" 它与 {path_text(PAIRED_LISTS[path])} 成对，必须一一对应。"
            elif leaf.list_length == 0:
                text += " 空列表，无法判断元素类型；这里不提供增删，可在 JSON 中手改。"
            else:
                text += "元素是对象，这里只编辑已有元素，不在这里增删。"
            return text

        part = path[-1]
        if isinstance(part, int):
            parent = path[-2] if len(path) > 1 else ""
            text = f"「{label_of(path[:-1])}」列表中的第 {part + 1} 项。"
            if path[:-1] == ("player", "description"):
                return text + " 玩家外观描述的其中一行。"
            parent_note = FIELD_NOTES.get(str(parent))
            if parent_note:
                text += " " + parent_note
            return text

        key = str(part)
        parent = str(path[-2]) if len(path) > 1 else ""
        if not is_schema_key(key):
            if parent == "oldGodStates" and key.isdigit():
                name = OLD_GOD_NAMES.get(int(key))
                return f"旧神「{name}」的状态（枚举整数）。" if name else f"旧神编号 {key} 的状态。"
            if parent == "storyFlags":
                return f"剧情标记「{key}」：布尔值，true 表示该标记已经置位。"
            if parent == "playerGods":
                return f"玩家「{key}」信奉的神明名。"
            if parent == "scores":
                return f"原型编号 {key} 的得分。"
            if parent == "npcRelationship":
                return f"与镇民故事 NPC「{key}」的关系值。"
            if parent == "relationships":
                return f"与「{key}」的关系数据。"
            return (f"字典「{LABELS.get(parent, parent)}」中的键「{key}」。"
                    "这是名称或标识，不是字段名；它对应的值按该字典的含义解读。")

        if key == "description":
            if path == ("player", "description"):
                return "玩家的四行外观描述（身高、体型、服饰等），长度固定。"
            if "memories" in path:
                return "这条记忆的描述文本，记录 NPC 记住的事件经过。"
            return "该条目的描述文本，具体含义随所在对象而定。"

        note = FIELD_NOTES.get(key)
        if note:
            return note
        if key in LABELS:
            text = f"{LABELS[key]}：存档中记录的原始值。"
        else:
            text = f"直译：{mechanical_phrase(key)}。"
        source = source_notes().get(key)
        if source:
            text += f"\n代码注释：{source}"
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
            return f"同伴 {name} · "
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
                value = f"{leaf.list_length} 项"
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
            self.say(f"匹配 {len(leaves)} 行，只显示前 {self.MAX_ROWS} 行；请用搜索缩小范围。")

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
            note += f"\n类型：{TYPE_ZH.get(leaf.kind, leaf.kind)}"
        self.set_note(note)
        self.current_label.configure(text=(f"<列表，{leaf.list_length} 项>"
                                           if leaf.is_container else display_value(leaf.value, 400)))
        self.editor.delete("1.0", "end")
        editable = not leaf.is_container and is_editable(leaf.value)
        if leaf.is_container:
            self.editor.insert("1.0", "")
        elif is_editable(leaf.value):
            self.editor.insert("1.0", self.pending.get(leaf.path, show(leaf.value)))
        else:
            self.editor.insert("1.0", "（这个字段是 null，类型未知，不能直接改）")
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
            self.say(f"{path_text(leaf.path)} 是 null，类型未知，不能直接改。")
            return
        text = self.editor.get("1.0", "end-1c")
        try:
            validate_change(leaf.path, leaf.value, text)
        except ValueError as error:
            self.say(f"{path_text(leaf.path)}：{error}")
            return
        if text == show(leaf.value):
            self.pending.pop(leaf.path, None)
        else:
            self.pending[leaf.path] = text
        self.render()
        self.select_path(leaf.path)
        self.update_change_count()
        self.say(f"{path_text(leaf.path)} 待保存为新值 {display_value(text)}（还没有写文件）")

    def revert_selected(self) -> None:
        leaf = self.selected_leaf()
        if leaf is None or leaf.is_container:
            return
        self.pending.pop(leaf.path, None)
        self.render()
        self.select_path(leaf.path)
        self.update_change_count()
        self.say(f"{path_text(leaf.path)} 恢复为存档里的值。")

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
                parts.append(f"{len(self.pending)} 项数值改动")
            if self.dirty:
                parts.append("列表/同伴改动")
            self.change_count.configure(text="未保存：" + "，".join(parts), foreground="#b45309")
            self.save_button.configure(text="保存全部改动")
        else:
            self.change_count.configure(text="没有未保存改动", foreground="#555")
            self.save_button.configure(text="保存全部改动")

    # ---- list tools -------------------------------------------------------------------------------

    def empty_list_kind(self, path: tuple) -> str | None:
        """The type an empty list holds, for the lists the game schema pins down."""
        return EMPTY_SCALAR_LISTS.get(path)

    def list_edit_blocked(self, path: tuple) -> str | None:
        if path in FIXED_LISTS:
            return "这个列表的长度是固定的，不能增删元素；可以直接修改已有的元素。"
        return None

    def confirm_paired(self, path: tuple) -> bool:
        mate = PAIRED_LISTS.get(path)
        if mate is None:
            return True
        return bool(self.messagebox.askyesno(
            "成对列表",
            f"{path_text(path)} 与 {path_text(mate)} 必须一一对应。\n"
            "只改一边会让物品与类型错位，甚至让读档失败。确定继续吗？",
            parent=self.root))

    def check_list_addition(self, path: tuple, value: Any) -> str | None:
        """Refuse a list element the game would not accept, before it reaches the file."""
        if path == ACTIVE_COMPANIONS_PATH:
            if not isinstance(value, int) or isinstance(value, bool):
                return "出战同伴 ID 必须是整数。"
            if value not in COMPANION_NAMES:
                return "同伴 ID 只能是 0-4（Lyris、Aldric、Mira、Vex、Melodia）。"
            if value in self.active_ids():
                return "这名同伴已经在出战列表里。"
            if len(self.active_ids()) >= MAX_ACTIVE_COMPANIONS:
                return f"出战同伴最多 {MAX_ACTIVE_COMPANIONS} 名。"
            entry = self.companion_entry(value)
            if entry and entry.get("isDead"):
                return "这名同伴已经死了，先在“同伴管理”里复活。"
        if path == DUNGEON_PARTY_PATH:
            if not isinstance(value, str):
                return "地牢队友 ID 必须是文本。"
            if value in self.party_ids():
                return "这个 NPC 已经在队伍里。"
            if len(self.party_ids()) >= MAX_DUNGEON_PARTY:
                return f"地牢队伍最多 {MAX_DUNGEON_PARTY} 人。"
            npc = next((n for n in self.npc_roster() if n.get("id") == value), None)
            if npc is None:
                return "NPC 名单里没有这个 ID。"
            if npc.get("isDead"):
                return "这个 NPC 已经死了，先复活再加入队伍。"
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
            self.say(f"没有添加：{error}")
            return
        if value is _CANCELLED:
            return
        refusal = self.check_list_addition(leaf.path, value)
        if refusal:
            self.say(f"没有添加：{refusal}")
            return
        try:
            list_add(self.data, leaf.path, value)
        except (KeyError, TypeError, ValueError) as error:
            self.say(f"没有添加：{error}")
            return
        self.after_list_add(leaf.path, value)
        self.dirty = True
        self.rebuild_view()
        self.select_path(leaf.path)
        self.update_change_count()
        self.say(f"{path_text(leaf.path)}：已在末尾加入 {show(value)}（还没有写文件）")

    def ask_new_element(self, leaf: Leaf) -> Any:
        tk = self.tk
        ttk = self.ttk
        from tkinter import simpledialog

        if leaf.element_kind in ("int", "float", "bool"):
            text = simpledialog.askstring("添加元素", f"给 {path_text(leaf.path)} 添加一个"
                                          f" {leaf.element_kind}：", parent=self.root)
            if text is None:
                return _CANCELLED
            sample = {"int": 0, "float": 0.0, "bool": False}[leaf.element_kind]
            return coerce(sample, text)

        if leaf.list_length > 0:
            text = simpledialog.askstring("添加元素", f"给 {path_text(leaf.path)} 添加文本：",
                                          parent=self.root)
            if text is None:
                return _CANCELLED
            return text

        # An empty list has no element to copy the type from, so ask which type it holds.
        dialog = tk.Toplevel(self.root)
        dialog.title("添加元素")
        dialog.transient(self.root)
        dialog.grab_set()
        ttk.Label(dialog, text=f"{path_text(leaf.path)} 现在是空的。新元素是什么类型？",
                  padding=10).pack()
        kind_box = ttk.Combobox(dialog, state="readonly", values=["文本", "整数", "小数", "布尔"])
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
                if kind == "整数":
                    result.append(int(text.strip()))
                elif kind == "小数":
                    result.append(float(text.strip()))
                elif kind == "布尔":
                    result.append(coerce(False, text))
                else:
                    result.append(text)
            except ValueError as error:
                ttk.Label(dialog, text=str(error), foreground="#b91c1c").pack()
                return
            dialog.destroy()

        ttk.Button(dialog, text="添加", command=okay).pack(pady=(0, 10))
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
                "删除元素", f"从 {path_text(list_path)} 删除第 {index} 项 {display_value(leaf.value)}？",
                parent=self.root):
            return
        try:
            removed = list_remove(self.data, list_path, index)
        except (KeyError, TypeError, ValueError) as error:
            self.say(f"没有删除：{error}")
            return
        self.after_list_remove(list_path, removed)
        self.dirty = True
        self.rebuild_view()
        self.select_path(list_path)
        self.update_change_count()
        self.say(f"{path_text(list_path)}：已删除第 {index} 项 {show(removed)}（还没有写文件）")

    def structural_allowed(self) -> bool:
        if self.pending:
            self.say("还有未保存的数值改动。请先点“保存全部改动”，或“重新读取”放弃，再改列表。")
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
                return "这名同伴已经死了，先点“复活”或“招募”。"
            if not entry.get("isRecruited"):
                return "还没有招募，先点“招募”。"
            if companion_id not in ids and len(ids) >= MAX_ACTIVE_COMPANIONS:
                return f"出战同伴最多 {MAX_ACTIVE_COMPANIONS} 名，先让一位休战。"
            if companion_id not in ids:
                ids.append(companion_id)
            entry["isActive"] = True
        else:
            if companion_id in ids:
                ids.remove(companion_id)
            entry["isActive"] = False
        self.dirty = True
        self.rebuild_view()
        return f"{COMPANION_NAMES.get(companion_id, companion_id)} 现在{'出战' if active else '休战'}。"

    def set_companion_recruited(self, companion_id: int, recruited: bool) -> str:
        entry = self.companion_entry(companion_id, create=True)
        assert entry is not None
        if recruited:
            entry["isRecruited"] = True
            entry["isDead"] = False
            self.drop_fallen(companion_id)
            self.dirty = True
            self.rebuild_view()
            return f"已招募 {COMPANION_NAMES.get(companion_id, companion_id)}。"
        entry["isRecruited"] = False
        entry["isActive"] = False
        ids = self.active_ids()
        if companion_id in ids:
            ids.remove(companion_id)
        self.dirty = True
        self.rebuild_view()
        return f"已解散 {COMPANION_NAMES.get(companion_id, companion_id)}。"

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
            return "已复活：" + "、".join(COMPANION_NAMES.get(i, str(i)) for i in revived)
        return "没有阵亡的同伴。"

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
            return "这个 NPC 已经在队伍里。"
        if len(ids) >= MAX_DUNGEON_PARTY:
            return f"地牢队伍最多 {MAX_DUNGEON_PARTY} 人。"
        npc = next((n for n in self.npc_roster() if n.get("id") == npc_id), None)
        if npc is None:
            return "NPC 名单里没有这个 ID。"
        if npc.get("isDead"):
            return "这个 NPC 已经死了，先复活再加入队伍。"
        ids.append(npc_id)
        self.dirty = True
        self.rebuild_view()
        return f"已把 {npc.get('name')} 加入地牢队伍。"

    def remove_party_npc(self, npc_id: str) -> str:
        ids = self.party_ids()
        if npc_id not in ids:
            return "队伍里没有这个 NPC。"
        ids.remove(npc_id)
        self.dirty = True
        self.rebuild_view()
        return f"已把 {self.npc_name_by_id(npc_id)} 移出地牢队伍。"

    def clear_party(self) -> str:
        ids = self.party_ids()
        if not ids:
            return "地牢队伍已经是空的。"
        count = len(ids)
        ids.clear()
        self.dirty = True
        self.rebuild_view()
        return f"已清空地牢队伍（{count} 人）。"

    # ---- saving -----------------------------------------------------------------------------------

    def save(self) -> None:
        if not self.save_path:
            return
        if not self.has_changes():
            self.say("没有改动。")
            return

        # Work on a copy so a refused edit or a failed write never leaves the window out of step
        # with the file on disk.
        try:
            working = json.loads(json.dumps(self.data, ensure_ascii=False))
        except (TypeError, ValueError) as error:
            self.say(f"没有保存：存档里有无法写回 JSON 的值（{error}）")
            return

        applied: list[str] = []
        if self.pending:
            applied, refused = apply_changes(working, self.pending)
            if refused:
                self.say("没有保存；先修正这些值：\n" + "\n".join(refused))
                return

        try:
            backup = save_data(self.save_path, working)
        except OSError as error:
            self.say(f"写入失败：{error}")
            return

        self.data = working
        self.pending.clear()
        self.dirty = False
        self.rebuild_view()
        self.populate_saves(self.save_path)
        lines = ["已保存。"] + applied
        lines += ["", f"备份：{backup.name}"]
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


class CompanionManager:
    """The five story companions, with the flags and the active-id list kept in step."""

    def __init__(self, window: EditorWindow):
        import tkinter as tk
        from tkinter import ttk, simpledialog

        self.window = window
        self.tk = tk
        self.simpledialog = simpledialog
        self.top = tk.Toplevel(window.root)
        self.top.title("同伴管理")
        self.top.geometry("780x360")
        self.top.transient(window.root)
        self.top.grab_set()

        ttk.Label(self.top, padding=8, text=(
            "招募、出战、死亡和关系值会直接写进 storySystems.companions 与 activeCompanionIds；"
            "点主窗口的“保存全部改动”才写文件。")).pack(fill="x")

        tree_frame = ttk.Frame(self.top)
        tree_frame.pack(fill="both", expand=True, padx=8)
        self.tree = ttk.Treeview(tree_frame, columns=("recruited", "active", "dead", "level",
                                                      "loyalty", "trust", "romance"),
                                 show="tree headings", selectmode="browse", height=8)
        self.tree.heading("#0", text="同伴")
        for column, title in (("recruited", "已招募"), ("active", "出战"), ("dead", "死亡"),
                              ("level", "等级"), ("loyalty", "忠诚"), ("trust", "信任"),
                              ("romance", "恋爱")):
            self.tree.heading(column, text=title)
            self.tree.column(column, width=70, anchor="center")
        self.tree.column("#0", width=110)
        self.tree.pack(side="left", fill="both", expand=True)
        tree_bar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        tree_bar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=tree_bar.set)

        buttons = ttk.Frame(self.top, padding=8)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="招募/解散", command=self.toggle_recruited).pack(side="left")
        ttk.Button(buttons, text="出战/休战", command=self.toggle_active).pack(side="left", padx=6)
        ttk.Button(buttons, text="设置忠诚/信任/恋爱", command=self.edit_relationship).pack(side="left")
        ttk.Button(buttons, text="设置等级/经验", command=self.edit_level).pack(side="left", padx=6)
        ttk.Button(buttons, text="复活全部", command=self.revive_all).pack(side="left")

        self.status = ttk.Label(self.top, padding=(8, 0, 8, 8), foreground="#555")
        self.status.pack(fill="x")
        self.fill()

    def fill(self) -> None:
        self.tree.delete(*self.tree.get_children())
        for companion_id in sorted(COMPANION_NAMES):
            entry = self.window.companion_entry(companion_id) or {}
            self.tree.insert("", "end", iid=str(companion_id), text=COMPANION_NAMES[companion_id],
                             values=("是" if entry.get("isRecruited") else "否",
                                     "是" if entry.get("isActive") else "否",
                                     "是" if entry.get("isDead") else "否",
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
        for key, title in (("loyaltyLevel", "忠诚"), ("trustLevel", "信任"), ("romanceLevel", "恋爱")):
            value = self.simpledialog.askinteger(title, f"{COMPANION_NAMES[companion_id]} 的{title}（0-100）：",
                                                 parent=self.top, initialvalue=int(entry.get(key, 50)),
                                                 minvalue=0, maxvalue=100)
            if value is not None:
                entry[key] = value
        self.window.dirty = True
        self.window.rebuild_view()
        self.fill()
        self.say(f"{COMPANION_NAMES[companion_id]} 的关系值已更新（还没有写文件）。")

    def edit_level(self) -> None:
        companion_id = self.selected_id()
        if companion_id is None:
            return
        entry = self.window.companion_entry(companion_id, create=True)
        assert entry is not None
        level = self.simpledialog.askinteger("等级", f"{COMPANION_NAMES[companion_id]} 的等级（1-100）：",
                                             parent=self.top, initialvalue=int(entry.get("level", 1)),
                                             minvalue=1, maxvalue=100)
        if level is not None:
            entry["level"] = level
        experience = self.simpledialog.askinteger(
            "经验", f"{COMPANION_NAMES[companion_id]} 的经验（可留空保持原值）：",
            parent=self.top, initialvalue=int(entry.get("experience", 0)), minvalue=0)
        if experience is not None:
            entry["experience"] = experience
        self.window.dirty = True
        self.window.rebuild_view()
        self.fill()
        self.say(f"{COMPANION_NAMES[companion_id]} 的等级/经验已更新（还没有写文件）。")

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
        self.top.title("地牢队伍")
        self.top.geometry("860x520")
        self.top.transient(window.root)
        self.top.grab_set()

        ttk.Label(self.top, padding=8, text=(
            "这里管理 storySystems.dungeonPartyNPCIds：进入地牢时带到身边的 NPC。"
            f"最多 {MAX_DUNGEON_PARTY} 人；死亡的 NPC 不能加入。")).pack(fill="x")

        body = ttk.Frame(self.top, padding=(8, 0))
        body.pack(fill="both", expand=True)

        current = ttk.LabelFrame(body, text="当前队伍", padding=6)
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
        ttk.Button(current_buttons, text="移出选中", command=self.remove_selected).pack(side="left")
        ttk.Button(current_buttons, text="清空队伍", command=self.clear).pack(side="left", padx=6)

        available = ttk.LabelFrame(body, text="NPC 名单", padding=6)
        available.pack(side="left", fill="both", expand=True, padx=(8, 0))
        search = ttk.Frame(available)
        search.pack(fill="x")
        ttk.Label(search, text="搜索").pack(side="left")
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
        ttk.Button(available, text="把选中 NPC 加入队伍", command=self.add_selected).pack(fill="x", pady=(6, 0))

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
                line += "  · 已死亡"
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

    parser = argparse.ArgumentParser(description="编辑 Usurper Reborn 单机存档（玩家、NPC、队伍、世界）")
    parser.add_argument("--saves", help="存档目录（默认自动找到 bin/Debug/net8.0/saves）")
    parser.add_argument("--check", action="store_true", help="只列存档，不打开窗口")
    args = parser.parse_args()

    directory = find_saves_directory(args.saves)
    if args.check:
        return check(directory)
    if not directory.is_dir():
        print(f"没有找到存档目录：{directory}", file=sys.stderr)
        return 1

    EditorWindow(directory).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
