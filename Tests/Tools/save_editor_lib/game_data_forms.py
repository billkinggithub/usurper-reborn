"""Structured record editor for the GameData JSON files.

The C# G editor has a hand-written form per data source. This module keeps a
single form engine but gives every source its own field order, labels, pickers
and validation, matching the C# editor's choices. Records are added, cloned and
deleted here; saving always writes a timestamped backup first.
"""

from __future__ import annotations

import copy
import json
import re
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk, simpledialog
from typing import Any

from .common import GAME_DATA_FILES, export_defaults, game_data_dir, load_json, write_json
from .game_data_loc import GameDataLocalizer

CAMEL = re.compile(r"[A-Z]+(?=[A-Z][a-z]|$)|[A-Z]?[a-z]+|[0-9]+")
NONE_STORY_ROLE = "(none - regular NPC)"

UI_ZH = {
    "GameData editor": "GameData 编辑器",
    "Export defaults": "导出默认数据",
    "Filter by name, ID, or text:": "按名称、ID 或文本筛选：",
    "Add": "添加",
    "Clone": "克隆",
    "Delete": "删除",
    "Show vocabulary": "查看词表",
    "Show extra JSON fields (not exposed by the C# editor)": "显示额外 JSON 字段（C# 编辑器未开放）",
    "Other JSON fields": "其他 JSON 字段",
    "Apply form": "应用表单",
    "Save file (backup)": "保存文件（备份）",
    "Reload file": "重新载入",
    "Close": "关闭",
    "Edit tiers...": "编辑层级...",
    "Edit content...": "编辑内容...",
    "Discard unsaved changes": "放弃未保存的更改",
    "Discard unsaved changes?": "放弃未保存的更改吗？",
    "Discard unsaved changes and close?": "放弃未保存的更改并关闭？",
    "Invalid value": "无效的值",
    "Validation failed": "校验失败",
    "Saved": "已保存",
    "Save failed": "保存失败",
    "Export failed": "导出失败",
    "Overwrite GameData with the built-in defaults?": "用内置默认数据覆盖 GameData？",
    "Delete record": "删除记录",
    "Delete the selected record?": "删除选中的记录？",
    "Add value": "添加数值",
    "Key:": "键：",
    "Dialogue vocabulary": "对话词表",
    "Categories:": "分类：",
    "Personalities:": "性格类型：",
    "Emotions:": "情绪：",
    "Contexts:": "情境：",
    "Name": "名称",
    "Value": "数值",
    "Description": "描述",
    "Slot": "装备栏位",
    "Lines:": "台词行：",
    "Line text:": "台词文本：",
    "Append line": "追加一行",
    "Replace selected": "替换选中行",
    "Delete selected": "删除选中行",
    "Clear all lines": "清空所有行",
    "Commit and close": "提交并关闭",
    "Cancel": "取消",
    "Clear all lines?": "清空所有行吗？",
    "Content of": "内容：",
    "Tier name": "层级名称",
    "MinLevel": "最低等级",
    "MaxLevel": "最高等级",
    "PowerMultiplier": "强度倍率",
    "Color": "颜色",
    "SpecialAbilities:": "特殊能力：",
    "SignatureAbilities (advanced):": "标志能力（高级）：",
    "Add ability": "添加能力",
    "Remove ability": "移除能力",
    "Apply tier": "应用层级",
    "Add new tier": "添加层级",
    "Delete tier": "删除层级",
    "Ability to add": "要添加的能力",
    "Signature ability": "标志能力",
    "Ability name:": "能力名称：",
    "tiers": "层级",
    "Invalid tier": "无效的层级",
    "Tier name is required.": "层级名称不能为空。",
    "Levels and PowerMultiplier must be numeric.": "等级与强度倍率必须是数字。",
    "MinLevel/MaxLevel must be 1-100 and MaxLevel >= MinLevel.": "最低/最高等级必须在 1-100 之间，且最高等级不低于最低等级。",
    "Delete tier?": "删除层级",
    "Lines": "行数",
    "Add tier?": "添加层级",
}

try:
    ZH_FIELDS: dict[str, str] = json.loads(
        Path(__file__).with_name("editor_zh_fields.json").read_text(encoding="utf-8"))
except (OSError, ValueError):
    ZH_FIELDS = {}

try:
    ZH_VALUES: dict[str, str] = json.loads(
        Path(__file__).with_name("editor_zh_values.json").read_text(encoding="utf-8"))
except (OSError, ValueError):
    ZH_VALUES = {}


def tr(language: str, text: str) -> str:
    return UI_ZH.get(text, text) if language == "zh" else text


def tr_field(language: str, text: str) -> str:
    return ZH_FIELDS.get(text, text) if language == "zh" else text


def tr_value(language: str, value: str) -> str:
    return ZH_VALUES.get(value, value) if language == "zh" else value


FILE_NAMES_ZH = {
    "Equipment": "装备",
    "NPCs": "NPC",
    "Monster families": "怪物家族",
    "Dreams": "梦境",
    "Dialogue": "对话",
    "Balance values": "平衡数值",
}

# BalanceConfig property types, so the list shows the same Int32/Single/Double
# names as the C# editor even though JSON only has one number type.
BALANCE_TYPES = {
    "criticalHitChance": "Int32",
    "criticalHitMultiplier": "Single",
    "backstabMultiplier": "Single",
    "berserkMultiplier": "Single",
    "bossPotionCooldownRounds": "Int32",
    "bossEnrageDamageMultiplier": "Double",
    "bossEnrageDefenseMultiplier": "Double",
    "bossEnrageExtraAttacks": "Int32",
    "bossCorruptionDamageBase": "Int32",
    "bossCorruptionMaxStacks": "Int32",
    "bossDoomDefaultRounds": "Int32",
    "bossTankAoEAbsorption": "Double",
    "bossPhaseImmunityResidual": "Double",
    "bossChannelInterruptSpeedThreshold": "Int32",
    "bossChannelInterruptChance": "Double",
    "defaultGymSessions": "Int32",
    "defaultDrinksAtOrbs": "Int32",
    "defaultIntimacyActs": "Int32",
    "defaultMaxWrestlings": "Int32",
    "defaultPickPocketAttempts": "Int32",
}

SLOTS = ["None", "Head", "Body", "Arms", "Hands", "Legs", "Feet", "Waist", "Neck",
         "Neck2", "Face", "Cloak", "LFinger", "RFinger", "MainHand", "OffHand"]
HANDEDNESS = ["None", "OneHanded", "TwoHanded", "OffHandOnly"]
WEAPON_TYPES = ["None", "Sword", "Axe", "Mace", "Dagger", "Rapier", "Hammer", "Flail",
                "Scimitar", "Greatsword", "Greataxe", "Polearm", "Staff", "Maul", "Bow",
                "Instrument", "Shield", "Buckler", "TowerShield"]
ARMOR_TYPES = ["None", "Cloth", "Leather", "Chain", "Scale", "Plate", "Magic", "Artifact"]
WEIGHT_CLASSES = ["None", "Light", "Medium", "Heavy"]
RARITIES = ["Common", "Uncommon", "Rare", "Epic", "Legendary", "Artifact"]
SHIELD_TYPES = {"Shield", "Buckler", "TowerShield"}
WEAPON_SLOTS = {"MainHand", "OffHand"}
CLASSES = ["Alchemist", "Assassin", "Barbarian", "Bard", "Cleric", "Jester", "Magician",
           "Paladin", "Ranger", "Sage", "Warrior", "Tidesworn", "Wavecaller", "Cyclebreaker",
           "Abysswarden", "Voidreaver", "MysticShaman"]
RACES = ["Human", "Hobbit", "Elf", "HalfElf", "Dwarf", "Troll", "Orc", "Gnome", "Gnoll", "Mutant"]
ALIGNMENTS = ["Good", "Evil", "Neutral"]
GENDERS = ["Male", "Female", "NonBinary", "Genderfluid", "TransMale", "TransFemale"]
ORIENTATIONS = ["Straight", "Gay", "Lesbian", "Bisexual", "Pansexual", "Asexual", "Demisexual"]
INTIMATE = ["Dominant", "Submissive", "Switch", "Vanilla", "Adventurous"]
RELATIONSHIP_PREFS = ["Monogamous", "OpenRelationship", "Polyamorous", "CasualOnly",
                      "FriendsWithBenefits", "Undecided"]
PERSONALITIES = [
    "Aggressive", "Ambitious", "Arrogant", "Brave", "Brooding", "Brutal", "Charming", "Cold",
    "Compassionate", "Cowardly", "Cruel", "Cunning", "Curious", "Deadly", "Devout",
    "Disciplined", "Eccentric", "Fanatical", "Fierce", "Flashy", "Free-spirited", "Gentle",
    "Greedy", "Gruff", "Honorable", "Insane", "Kind", "Loyal", "Lucky", "Merciless",
    "Mysterious", "Nervous", "Noble", "Obsessed", "Optimistic", "Peaceful", "Pious",
    "Professional", "Radiant", "Resolute", "Righteous", "Ruthless", "Scheming", "Scholarly",
    "Secretive", "Serene", "Sharp", "Silent", "Sinister", "Sneaky", "Solitary", "Stern",
    "Strict", "Stubborn", "Tormented", "Tough", "Wise", "Zealous",
]
STORY_ROLES = [NONE_STORY_ROLE, "FallenPaladin", "HighPriest", "Lysandra", "MaelkethChampion",
               "Mordecai", "OceanOracle", "SealScholar", "ShadowAgent", "Sylvana", "TheStranger"]
ANSI_COLORS = ["black", "blue", "green", "cyan", "red", "magenta", "yellow", "white",
               "gray", "darkgray", "bright_blue", "bright_green", "bright_cyan", "bright_red",
               "bright_magenta", "bright_yellow", "bright_white", "dark_blue", "dark_green",
               "dark_cyan", "dark_red", "dark_magenta", "dark_yellow"]
ATTACK_TYPES = ["physical", "magic", "poison", "fire", "frost", "lightning", "holy", "shadow",
                "arcane", "necrotic"]
DIALOGUE_CATEGORIES = ["greeting", "farewell", "smalltalk", "reaction", "mood_prefix", "memory"]
DIALOGUE_PERSONALITIES = ["aggressive", "noble", "cunning", "pious", "scholarly", "cynical",
                          "charming", "stoic"]
EMOTIONS = ["anger", "fear", "joy", "sadness", "confidence", "disgust", "surprise", "trust",
            "anticipation"]
CONTEXTS = ["low_hp", "rich", "is_king", "after_combat", "night", "day", "in_tavern",
            "in_dungeon", "player_wounded", "player_low_fame", "player_high_fame"]
MEMORY_TYPES = ["helped", "attacked", "betrayed", "saved", "spoken_to"]
EVENT_TYPES = ["combat_victory", "combat_defeat", "ally_death", "level_up", "became_king",
               "divorced", "got_married", "companion_recruited"]
MONSTER_ABILITIES = [
    "Multiattack", "CrushingBlow", "VenomousBite", "BleedingWound", "FireBreath", "FrostBreath",
    "PoisonCloud", "LifeDrain", "ManaDrain", "Regeneration", "Thorns", "ArmorHarden", "Vanish",
    "Phase", "PetrifyingGaze", "HorrifyingScream", "BlindingFlash", "Curse", "Silence",
    "Enfeeble", "Devour", "Berserk", "SummonMinions", "Explosion", "SoulReap", "Backstab",
    "Flee", "CallForHelp", "Enrage", "Heal", "CriticalStrike", "Rally", "CommandArmy",
    "Paralyze", "Incorporeal", "Spellcasting", "Phylactery", "Rage", "Frenzy", "Warcry",
    "Cleave", "Flight", "DragonFear", "AncientMagic", "Invisibility", "Teleport", "Hellfire",
    "Corruption", "Dominate", "Boulder", "Stoneskin", "Lightning", "Earthquake", "PackTactics",
    "Bite", "Lycanthropy", "Howl", "Moonlight", "Burn", "Immolate", "Fireball", "Rebirth",
    "Inferno", "Corrosion", "Split", "Engulf", "Absorb", "ShapeShift", "Madness", "WebTrap",
    "PhaseShift", "Poison", "SummonSpiders", "DeadlyVenom", "Swarm", "Cocoon", "ImmuneMagic",
    "PoisonGas", "Indestructible", "SelfRepair", "Overload", "Sleep", "TreeMeld", "Charm",
    "AnimateTrees", "RootEntangle", "TimeStop", "WildShape", "TentacleGrab", "InkCloud",
    "Whirlpool", "TidalWave", "HolySmite", "Purify", "DivineJudgment", "Sanctuary",
    "Resurrection", "StrengthDrain", "Terror", "Possess", "Nightmare", "DevourSoul",
]


def label(key: str) -> str:
    words = CAMEL.findall(key)
    return " ".join(word.capitalize() for word in words) if words else key


def field(key, title, kind="str", options=None, minimum=None, maximum=None, section=None,
          unique=False, required=False, default=None, group=None, optional=False,
          readonly=False):
    return {"key": key, "title": title, "kind": kind, "options": options,
            "min": minimum, "max": maximum, "section": section, "unique": unique,
            "required": required, "default": default, "group": group,
            "optional": optional, "readonly": readonly}


SCHEMAS: dict[str, list[dict]] = {
    "equipment.json": [
        field("id", "ID", "int", minimum=200000, unique=True, required=True, readonly=True),
        field("name", "Name", required=True),
        field("description", "Description", "text"),
        field("slot", "Slot", "choice", SLOTS),
        field("handedness", "Handedness", "choice", HANDEDNESS, group="weapon"),
        field("weaponType", "WeaponType", "choice", WEAPON_TYPES, group="weapon"),
        field("weaponPower", "WeaponPower", "int", minimum=0, group="weapon"),
        field("shieldBonus", "ShieldBonus", "int", minimum=0, group="shield"),
        field("blockChance", "BlockChance (percent)", "int", minimum=0, maximum=100,
              group="shield"),
        field("armorType", "ArmorType", "choice", ARMOR_TYPES, group="armor"),
        field("weightClass", "WeightClass", "choice", WEIGHT_CLASSES, group="armor"),
        field("armorClass", "ArmorClass", "int", minimum=0, group="armor"),
        field("strengthBonus", "STR", "int",
              section="Primary stat bonuses (negative allowed for cursed items)"),
        field("dexterityBonus", "DEX", "int"),
        field("constitutionBonus", "CON", "int"),
        field("intelligenceBonus", "INT", "int"),
        field("wisdomBonus", "WIS", "int"),
        field("charismaBonus", "CHA", "int"),
        field("maxHPBonus", "MaxHP+", "int", section="Secondary bonuses"),
        field("maxManaBonus", "MaxMana+", "int"),
        field("defenceBonus", "Defence+", "int"),
        field("minLevel", "MinLevel", "int", minimum=1, maximum=100, default=1,
              section="Restrictions & economy"),
        field("value", "Value (gold, 0 = unsellable)", "int", minimum=0),
        field("rarity", "Rarity", "choice", RARITIES),
    ],
    "npcs.json": [
        field("name", "Name", required=True),
        field("class", "Class", "choice", CLASSES),
        field("race", "Race", "choice", RACES),
        field("personality", "Personality", "choice", PERSONALITIES, default=""),
        field("alignment", "Alignment", "choice", ALIGNMENTS, default=""),
        field("startLevel", "StartLevel", "int", minimum=1, maximum=100, default=5),
        field("gender", "Gender", "choice", GENDERS),
        field("orientation", "Orientation", "choice", ORIENTATIONS),
        field("intimateStyle", "IntimateStyle", "choice", INTIMATE, default="Switch"),
        field("relationshipPref", "RelationshipPref", "choice", RELATIONSHIP_PREFS,
              default="Undecided"),
        field("storyRole", "StoryRole (links NPC to a faction)", "choice", STORY_ROLES,
              optional=True),
        field("loreNote", "LoreNote (one-line description of this NPC's lore role; blank if generic)",
              "text", optional=True),
    ],
    "monster_families.json": [
        field("familyName", "Name", required=True),
        field("description", "Description", "text"),
        field("baseColor", "BaseColor", "choice", ANSI_COLORS, default="white"),
        field("attackType", "AttackType", "choice", ATTACK_TYPES, default="physical"),
        field("tiers", "Tiers", "tiers"),
    ],
    "dreams.json": [
        field("id", "Id (unique identifier)", required=True, unique=True),
        field("title", "Title", required=True, default="New Dream"),
        field("minLevel", "MinLevel", "int", minimum=0, maximum=100, default=0),
        field("maxLevel", "MaxLevel", "int", minimum=0, maximum=100, default=100),
        field("minAwakening", "MinAwakening (0-7)", "int", minimum=0, maximum=7, default=0),
        field("maxAwakening", "MaxAwakening", "int", minimum=0, maximum=7, default=7),
        field("minCycle", "MinCycle", "int", minimum=1, default=1),
        field("requiredFloor", "RequiredFloor (0 = any)", "int", minimum=0, default=0),
        field("maxFloor", "MaxFloor (0 = any)", "int", minimum=0, default=0),
        field("priority", "Priority (higher = picked first)", "int", default=10),
        field("awakeningGain", "AwakeningGain (added on trigger)", "int", minimum=0, default=0),
        field("minChivalry", "MinChivalry", "int", minimum=0, default=0),
        field("minDarkness", "MinDarkness", "int", minimum=0, default=0),
        field("minKills", "MinKills", "int", minimum=0, default=0),
        field("minDeepestFloor", "MinDeepestFloor", "int", minimum=0, default=0),
        field("requiresIsKing", "RequiresIsKing", "bool"),
        field("requiresMarriage", "RequiresMarriage", "bool"),
        field("requiresAllSeals", "RequiresAllSeals", "bool"),
        field("requiresAnyCompanionQuestDone", "RequiresAnyCompanionQuestDone", "bool"),
        field("philosophicalHint", "PhilosophicalHint (optional subtitle)", "text"),
        field("content", "Content", "content"),
    ],
    "dialogue.json": [
        field("id", "Id (unique)", required=True),
        field("text", "Text", "text", required=True),
        field("category", "Category", "choice", DIALOGUE_CATEGORIES, default="greeting"),
        field("npcName", "NpcName (blank = generic)", optional=True),
        field("personalityType", "PersonalityType (blank = any)", "choice",
              [""] + DIALOGUE_PERSONALITIES, optional=True),
        field("relationshipTier", "RelationshipTier (0 = any)", "int", minimum=0, default=0),
        field("emotion", "Emotion (blank = any)", "choice", [""] + EMOTIONS, optional=True),
        field("context", "Context (blank = any)", "choice", [""] + CONTEXTS, optional=True),
        field("memoryType", "MemoryType (blank = any)", "choice", [""] + MEMORY_TYPES,
              optional=True),
        field("eventType", "EventType (blank = any)", "choice", [""] + EVENT_TYPES,
              optional=True),
    ],
}


def record_title(record: Any, index: int, filename: str = "",
                 localizer: GameDataLocalizer | None = None) -> str:
    if not isinstance(record, dict):
        return f"{index + 1}. {record}"
    zh = localizer is not None

    def value(name: Any) -> Any:
        return tr_value("zh", str(name)) if zh else name

    if filename == "equipment.json":
        return (f"#{record.get('id', '?')}  {record.get('name', '')}  "
                f"({value(record.get('slot', ''))})")
    if filename == "npcs.json":
        return (f"{record.get('name', '')}  L{record.get('startLevel', '?')}  "
                f"{value(record.get('race', ''))} {value(record.get('class', ''))} "
                f"{value(record.get('alignment', ''))} {value(record.get('personality', ''))}")
    if filename == "monster_families.json":
        tiers = record.get("tiers")
        count = len(tiers) if isinstance(tiers, list) else 0
        name = (localizer.monster_family(record.get("familyName", ""))
                if localizer else "") or record.get("familyName", "")
        return (f"{name}  attack={value(record.get('attackType', ''))}  "
                f"color={value(record.get('baseColor', ''))}  tiers={count}")
    if filename == "dreams.json":
        title = (localizer.dream_title(record) if localizer else "") or record.get("title", "")
        return f"{record.get('id', '')} — {title}"
    if filename == "dialogue.json":
        snippet = ((localizer.dialogue_text(record) if localizer else "")
                   or str(record.get("text", "")))
        if len(snippet) > 50:
            snippet = snippet[:47] + "..."
        personality = record.get("personalityType")
        personality = ("任意" if zh else "any") if not personality else value(personality)
        return (f"{record.get('id', '')} [{value(record.get('category', ''))}] "
                f"[{personality}] \"{snippet}\"")
    for key in ("name", "familyName", "title", "id"):
        value = record.get(key)
        if isinstance(value, str) and value:
            return value
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return f"{index + 1}. {value}"
    return f"{index + 1}. {label(next(iter(record), 'record'))}"


def choose_from_list(parent: tk.Misc, title: str, options: list[str],
                     language: str = "en") -> str | None:
    """Modal searchable single-choice picker, used for monster abilities."""
    top = tk.Toplevel(parent)
    top.title(title)
    top.geometry("320x460")
    top.transient(parent)
    result: list[str | None] = [None]
    entry = ttk.Entry(top)
    entry.pack(fill="x", padx=8, pady=6)
    frame = ttk.Frame(top)
    frame.pack(fill="both", expand=True, padx=8)
    box = tk.Listbox(frame, exportselection=False)
    scroll = ttk.Scrollbar(frame, orient="vertical", command=box.yview)
    box.configure(yscrollcommand=scroll.set)
    box.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    def refill(*_event):
        query = entry.get().casefold()
        box.delete(0, "end")
        for option in options:
            if query in option.casefold():
                box.insert("end", option)

    def accept(*_event):
        selection = box.curselection()
        if selection:
            result[0] = box.get(selection[0])
            top.destroy()

    entry.bind("<KeyRelease>", refill)
    box.bind("<Double-Button-1>", accept)
    bar = ttk.Frame(top)
    bar.pack(fill="x", padx=8, pady=8)
    ttk.Button(bar, text=tr(language, "Add"), command=accept).pack(side="left")
    ttk.Button(bar, text=tr(language, "Cancel"), command=top.destroy).pack(side="right")
    refill()
    top.grab_set()
    top.wait_window()
    return result[0]


class StringListEditor(tk.Toplevel):
    """Backs the C# dream 'Content' submenu: append, edit, delete, clear, commit."""

    def __init__(self, parent: tk.Misc, title: str, values: list[str], on_commit,
                 language: str = "en", previews: list[str] | None = None):
        super().__init__(parent)
        self.title(title)
        self.geometry("760x600")
        self.transient(parent)
        self.language = language
        self.values = list(values)
        self.previews = list(previews or [])
        while len(self.previews) < len(self.values):
            self.previews.append("")
        self.on_commit = on_commit

        frame = ttk.Frame(self, padding=8)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=tr(language, "Lines:")).pack(anchor="w")
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill="both", expand=True, pady=(2, 6))
        self.lines = tk.Listbox(list_frame, height=14, exportselection=False)
        self.lines.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.lines.yview)
        self.lines.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.lines.bind("<<ListboxSelect>>", lambda _event: self.load_selected())

        ttk.Label(frame, text=tr(language, "Line text:")).pack(anchor="w")
        self.entry = ttk.Entry(frame)
        self.entry.pack(fill="x", pady=(2, 6))

        self.preview_label = None
        self.preview = None
        if language == "zh":
            ttk.Label(frame, text="中文预览：").pack(anchor="w")
            self.preview = tk.Text(frame, height=4, wrap="word", state="disabled",
                                   background="#f3faf6")
            self.preview.pack(fill="x", pady=(2, 6))

        buttons = ttk.Frame(frame)
        buttons.pack(fill="x")
        ttk.Button(buttons, text=tr(language, "Append line"),
                   command=self.append_line).pack(side="left")
        ttk.Button(buttons, text=tr(language, "Replace selected"),
                   command=self.replace_line).pack(side="left", padx=4)
        ttk.Button(buttons, text=tr(language, "Delete selected"),
                   command=self.delete_line).pack(side="left")
        ttk.Button(buttons, text=tr(language, "Clear all lines"),
                   command=self.clear_lines).pack(side="left", padx=4)
        ttk.Button(buttons, text=tr(language, "Commit and close"),
                   command=self.commit).pack(side="right")
        ttk.Button(buttons, text=tr(language, "Cancel"),
                   command=self.destroy).pack(side="right", padx=4)

        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.refresh()
        if self.values:
            self.lines.selection_set(0)
            self.set_preview(0)
        self.grab_set()

    def refresh(self) -> None:
        self.lines.delete(0, "end")
        for line in self.values:
            self.lines.insert("end", line)

    def set_preview(self, index: int | None) -> None:
        if self.preview is None:
            return
        text = self.previews[index] if index is not None and 0 <= index < len(self.previews) else ""
        if not text and index is not None:
            text = "（这一行还没有中文翻译。）"
        self.preview.configure(state="normal")
        self.preview.delete("1.0", "end")
        self.preview.insert("1.0", text)
        self.preview.configure(state="disabled")

    def load_selected(self) -> None:
        selection = self.lines.curselection()
        if selection:
            index = selection[0]
            self.entry.delete(0, "end")
            self.entry.insert(0, self.values[index])
            self.set_preview(index)

    def append_line(self) -> None:
        text = self.entry.get()
        if text:
            self.values.append(text)
            self.previews.append("")
            self.refresh()
            self.lines.selection_set(self.lines.size() - 1)
            self.set_preview(len(self.values) - 1)

    def replace_line(self) -> None:
        selection = self.lines.curselection()
        if not selection:
            return
        index = selection[0]
        self.values[index] = self.entry.get()
        self.previews[index] = ""
        self.refresh()
        self.lines.selection_set(index)
        self.set_preview(index)

    def delete_line(self) -> None:
        selection = self.lines.curselection()
        if selection:
            index = selection[0]
            del self.values[index]
            if index < len(self.previews):
                del self.previews[index]
            self.refresh()
            self.set_preview(None)

    def clear_lines(self) -> None:
        if self.values and messagebox.askyesno(
                tr(self.language, "Clear all lines"),
                tr(self.language, "Clear all lines?"), parent=self):
            self.values.clear()
            self.previews.clear()
            self.refresh()
            self.set_preview(None)

    def commit(self) -> None:
        self.on_commit(list(self.values))
        self.destroy()


class TierEditor(tk.Toplevel):
    """Backs the C# monster-family tier editor, including ability pickers."""

    def __init__(self, parent: tk.Misc, family: dict, on_change, language: str = "en",
                 localizer: GameDataLocalizer | None = None):
        super().__init__(parent)
        self.language = language
        self.localizer = localizer
        family_name = family.get("familyName", "Monster family")
        if language == "zh" and localizer is not None:
            family_name = localizer.monster_family(family_name) or family_name
        self.title(f"{family_name} " + ("层级" if language == "zh" else "tiers"))
        self.geometry("900x620")
        self.transient(parent)
        self.family = family
        self.on_change = on_change
        self.tiers = family.setdefault("tiers", [])
        if not isinstance(self.tiers, list):
            self.tiers = []
            family["tiers"] = self.tiers
        self.current: int | None = None

        body = ttk.Panedwindow(self, orient="horizontal")
        body.pack(fill="both", expand=True, padx=8, pady=8)
        left = ttk.Frame(body)
        body.add(left, weight=1)
        self.listbox = tk.Listbox(left, exportselection=False)
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        bar = ttk.Frame(left)
        bar.pack(fill="x", pady=(6, 0))
        ttk.Button(bar, text=tr(language, "Add new tier"),
                   command=self.add_tier).pack(fill="x")
        ttk.Button(bar, text=tr(language, "Delete tier"),
                   command=self.delete_tier).pack(fill="x", pady=(4, 0))

        right = ttk.Frame(body)
        body.add(right, weight=3)
        form = ttk.Frame(right)
        form.pack(fill="x")
        self.vars: dict[str, tk.StringVar] = {}
        for row_index, (key, title) in enumerate((
                ("name", "Tier name"), ("minLevel", "MinLevel"),
                ("maxLevel", "MaxLevel"), ("powerMultiplier", "PowerMultiplier"))):
            ttk.Label(form, text=tr(language, title), width=18).grid(
                row=row_index, column=0, sticky="w", pady=3)
            var = tk.StringVar()
            ttk.Entry(form, textvariable=var, width=40).grid(
                row=row_index, column=1, sticky="ew", pady=3)
            self.vars[key] = var
        ttk.Label(form, text=tr(language, "Color"), width=18).grid(
            row=4, column=0, sticky="w", pady=3)
        self.color = tk.StringVar()
        ttk.Combobox(form, textvariable=self.color, values=ANSI_COLORS,
                     state="readonly", width=37).grid(row=4, column=1, sticky="ew", pady=3)

        self.preview_label = None
        if language == "zh":
            self.preview_label = ttk.Label(right, text="中文预览：", foreground="#0a6a4a",
                                           wraplength=520, justify="left")
            self.preview_label.pack(anchor="w", pady=(6, 0))
            self.vars["name"].trace_add("write", lambda *_args: self.update_preview())

        ttk.Label(right, text=tr(language, "SpecialAbilities:")).pack(anchor="w", pady=(8, 2))
        ability_frame = ttk.Frame(right)
        ability_frame.pack(fill="both", expand=True)
        self.abilities = tk.Listbox(ability_frame, height=6, exportselection=False)
        self.abilities.pack(side="left", fill="both", expand=True)
        ability_bar = ttk.Frame(ability_frame)
        ability_bar.pack(side="left", fill="y", padx=(6, 0))
        ttk.Button(ability_bar, text=tr(language, "Add ability"),
                   command=self.add_ability).pack(fill="x")
        ttk.Button(ability_bar, text=tr(language, "Remove ability"),
                   command=self.remove_ability).pack(fill="x", pady=(4, 0))

        ttk.Label(right, text=tr(language, "SignatureAbilities (advanced):")).pack(
            anchor="w", pady=(8, 2))
        sig_frame = ttk.Frame(right)
        sig_frame.pack(fill="both", expand=True)
        self.signature = tk.Listbox(sig_frame, height=4, exportselection=False)
        self.signature.pack(side="left", fill="both", expand=True)
        sig_bar = ttk.Frame(sig_frame)
        sig_bar.pack(side="left", fill="y", padx=(6, 0))
        ttk.Button(sig_bar, text=tr(language, "Add ability"),
                   command=self.add_signature).pack(fill="x")
        ttk.Button(sig_bar, text=tr(language, "Remove ability"),
                   command=self.remove_signature).pack(fill="x", pady=(4, 0))

        foot = ttk.Frame(right)
        foot.pack(fill="x", pady=(8, 0))
        ttk.Button(foot, text=tr(language, "Apply tier"),
                   command=self.apply_current).pack(side="left")
        ttk.Button(foot, text=tr(language, "Close"), command=self.close).pack(side="right")

        self.protocol("WM_DELETE_WINDOW", self.close)
        self.refresh()
        if self.tiers:
            self.listbox.selection_set(0)
            self.load_tier(0)
        self.grab_set()

    def refresh(self) -> None:
        self.listbox.delete(0, "end")
        for tier in self.tiers:
            if isinstance(tier, dict):
                name = tier.get("name", "")
                if self.language == "zh" and self.localizer is not None:
                    name = self.localizer.monster_tier(name) or name
                self.listbox.insert(
                    "end", f"{name}  L{tier.get('minLevel', '?')}-"
                           f"{tier.get('maxLevel', '?')}  x{tier.get('powerMultiplier', '?')}"
                           f"  color={tier.get('color', '')}"
                           f"  abilities={len(tier.get('specialAbilities') or [])}")
            else:
                self.listbox.insert("end", str(tier))

    def on_select(self, _event=None) -> None:
        selection = self.listbox.curselection()
        if not selection or selection[0] == self.current:
            return
        previous = self.current
        if previous is not None and not self.apply_current():
            self.listbox.selection_clear(0, "end")
            self.listbox.selection_set(previous)
            return
        self.load_tier(selection[0])

    def load_tier(self, index: int) -> None:
        self.current = index
        if self.listbox.curselection() != (index,):
            self.listbox.selection_clear(0, "end")
            self.listbox.selection_set(index)
        tier = self.tiers[index]
        if not isinstance(tier, dict):
            tier = {}
            self.tiers[index] = tier
        self.vars["name"].set(str(tier.get("name", "")))
        self.vars["minLevel"].set(str(tier.get("minLevel", 1)))
        self.vars["maxLevel"].set(str(tier.get("maxLevel", 1)))
        self.vars["powerMultiplier"].set(str(tier.get("powerMultiplier", 1.0)))
        self.color.set(str(tier.get("color", "white")))
        self.abilities.delete(0, "end")
        for ability in tier.get("specialAbilities") or []:
            self.abilities.insert("end", ability)
        self.signature.delete(0, "end")
        for ability in tier.get("signatureAbilities") or []:
            self.signature.insert("end", ability)

    def update_preview(self) -> None:
        if self.preview_label is None:
            return
        name = self.vars["name"].get().strip()
        translated = ""
        if self.localizer is not None and name:
            translated = self.localizer.monster_tier(name)
        self.preview_label.configure(
            text="中文预览：" + (translated or "（这个层级名还没有中文翻译。）"))

    def apply_current(self) -> bool:
        if self.current is None:
            return True
        tier = self.tiers[self.current]
        name = self.vars["name"].get().strip()
        if not name:
            messagebox.showerror(
                tr(self.language, "Invalid tier"),
                tr(self.language, "Tier name is required."), parent=self)
            return False
        try:
            min_level = int(self.vars["minLevel"].get())
            max_level = int(self.vars["maxLevel"].get())
            power = float(self.vars["powerMultiplier"].get())
        except ValueError:
            messagebox.showerror(
                tr(self.language, "Invalid tier"),
                tr(self.language, "Levels and PowerMultiplier must be numeric."), parent=self)
            return False
        if not 1 <= min_level <= 100 or not 1 <= max_level <= 100 or max_level < min_level:
            messagebox.showerror(
                tr(self.language, "Invalid tier"),
                tr(self.language, "MinLevel/MaxLevel must be 1-100 and MaxLevel >= MinLevel."),
                parent=self)
            return False
        tier.update({
            "name": name,
            "minLevel": min_level,
            "maxLevel": max_level,
            "color": self.color.get(),
            "powerMultiplier": power,
            "specialAbilities": list(self.abilities.get(0, "end")),
            "signatureAbilities": list(self.signature.get(0, "end")),
        })
        self.refresh()
        if self.current < self.listbox.size():
            self.listbox.selection_clear(0, "end")
            self.listbox.selection_set(self.current)
        return True

    def add_tier(self) -> None:
        if not self.apply_current():
            return
        self.tiers.append({
            "name": "New Tier", "minLevel": 1, "maxLevel": 1, "color": "white",
            "powerMultiplier": 1.0, "specialAbilities": [], "signatureAbilities": [],
        })
        self.current = None
        self.refresh()
        self.load_tier(len(self.tiers) - 1)

    def delete_tier(self) -> None:
        selection = self.listbox.curselection()
        if not selection:
            return
        tier = self.tiers[selection[0]]
        prompt = (f"删除层级「{tier.get('name', '')}」？"
                  if self.language == "zh" else f"Delete tier \"{tier.get('name', '')}\"?")
        if not messagebox.askyesno(tr(self.language, "Delete tier"), prompt, parent=self):
            return
        del self.tiers[selection[0]]
        self.current = None
        self.refresh()
        if self.tiers:
            self.load_tier(0)
        else:
            self.vars["name"].set("")
            self.vars["minLevel"].set("")
            self.vars["maxLevel"].set("")
            self.vars["powerMultiplier"].set("")
            self.abilities.delete(0, "end")
            self.signature.delete(0, "end")

    def add_ability(self) -> None:
        ability = choose_from_list(self, tr(self.language, "Ability to add"),
                                   MONSTER_ABILITIES, self.language)
        if ability and ability not in self.abilities.get(0, "end"):
            self.abilities.insert("end", ability)

    def remove_ability(self) -> None:
        selection = self.abilities.curselection()
        if selection:
            self.abilities.delete(selection[0])

    def add_signature(self) -> None:
        ability = simpledialog.askstring(
            tr(self.language, "Signature ability"), tr(self.language, "Ability name:"),
            parent=self)
        if ability and ability not in self.signature.get(0, "end"):
            self.signature.insert("end", ability.strip())

    def remove_signature(self) -> None:
        selection = self.signature.curselection()
        if selection:
            self.signature.delete(selection[0])

    def close(self) -> None:
        if self.apply_current():
            self.on_change()
            self.destroy()


class GameDataFormsWindow:
    def __init__(self, parent: tk.Misc, language: str = "en"):
        self.language = language
        self.localizer = GameDataLocalizer(language)
        self.top = tk.Toplevel(parent)
        self.top.title(tr(language, "GameData editor"))
        self.top.geometry("1240x800")
        self.top.transient(parent)

        self.data: Any = None
        self.path = None
        self.filename = ""
        self.mode = "list"
        self.schema: list[dict] | None = None
        self.index: int | None = None
        self.field_widgets: dict[str, tuple] = {}
        self.choice_value_maps: dict[str, dict[str, str]] = {}
        self.rows: dict[str, ttk.Frame] = {}
        self.record_indices: list[int] = []
        self.dict_keys: list[str] = []
        self.show_extras = tk.BooleanVar(value=False)
        self.dirty = False
        self.file_position = 0

        body = ttk.Panedwindow(self.top, orient="horizontal")
        body.pack(fill="both", expand=True, padx=8, pady=8)
        left = ttk.Frame(body)
        body.add(left, weight=1)
        self.files = tk.Listbox(left, exportselection=False)
        self.files.pack(fill="both", expand=True)
        for name, filename in GAME_DATA_FILES:
            shown = FILE_NAMES_ZH.get(name, name) if language == "zh" else name
            self.files.insert("end", f"{shown}  ·  {filename}")
        self.files.bind("<<ListboxSelect>>", lambda _event: self.load_file())
        ttk.Button(left, text=tr(language, "Export defaults"),
                   command=self.export_defaults).pack(fill="x", pady=(6, 0))

        right = ttk.Frame(body)
        body.add(right, weight=5)
        self.path_label = ttk.Label(right, text="", foreground="#555")
        self.path_label.pack(anchor="w")
        self.status_label = ttk.Label(right, text="", foreground="#555")
        self.status_label.pack(anchor="w")
        options = ttk.Frame(right)
        options.pack(fill="x")
        self.vocab_button = ttk.Button(options, text=tr(language, "Show vocabulary"),
                                       command=self.show_dialogue_vocabulary)
        ttk.Checkbutton(
            options,
            text=tr(language, "Show extra JSON fields (not exposed by the C# editor)"),
            variable=self.show_extras, command=self.toggle_extras).pack(side="right")
        split = ttk.Panedwindow(right, orient="horizontal")
        split.pack(fill="both", expand=True, pady=(6, 6))

        records_frame = ttk.Frame(split)
        split.add(records_frame, weight=1)
        ttk.Label(records_frame, text=tr(language, "Filter by name, ID, or text:")).pack(
            anchor="w")
        self.filter_var = tk.StringVar()
        filter_entry = ttk.Entry(records_frame, textvariable=self.filter_var)
        filter_entry.pack(fill="x", pady=(2, 4))
        filter_entry.bind("<KeyRelease>", lambda _event: self.refresh_records())
        self.records = tk.Listbox(records_frame, exportselection=False)
        self.records.pack(fill="both", expand=True)
        self.records.bind("<<ListboxSelect>>", lambda _event: self.show_record())
        record_bar = ttk.Frame(records_frame)
        record_bar.pack(fill="x", pady=(4, 0))
        ttk.Button(record_bar, text=tr(language, "Add"),
                   command=self.add_record).pack(side="left")
        ttk.Button(record_bar, text=tr(language, "Clone"),
                   command=self.clone_record).pack(side="left", padx=4)
        ttk.Button(record_bar, text=tr(language, "Delete"),
                   command=self.delete_record).pack(side="left")

        form_holder = ttk.Frame(split)
        split.add(form_holder, weight=4)
        self.canvas = tk.Canvas(form_holder, highlightthickness=0)
        scroll = ttk.Scrollbar(form_holder, orient="vertical", command=self.canvas.yview)
        self.form = ttk.Frame(self.canvas)
        self.form.bind("<Configure>",
                       lambda _event: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.form, anchor="nw")
        self.canvas.configure(yscrollcommand=scroll.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        bar = ttk.Frame(right)
        bar.pack(fill="x")
        ttk.Button(bar, text=tr(language, "Apply form"),
                   command=self.apply_form).pack(side="left")
        ttk.Button(bar, text=tr(language, "Save file (backup)"),
                   command=self.save_file).pack(side="left", padx=6)
        ttk.Button(bar, text=tr(language, "Reload file"),
                   command=self.load_file).pack(side="left")
        ttk.Button(bar, text=tr(language, "Close"),
                   command=self.close_window).pack(side="right")

        self.top.protocol("WM_DELETE_WINDOW", self.close_window)
        self.files.selection_set(0)
        self.load_file()

    # ---- file and records --------------------------------------------------------------------

    def selected_file(self):
        selection = self.files.curselection()
        return GAME_DATA_FILES[selection[0]] if selection else None

    def load_file(self, force: bool = False) -> None:
        selected = self.selected_file()
        if selected is None:
            return
        if self.dirty and not force:
            if not messagebox.askyesno(
                    tr(self.language, "Discard unsaved changes"),
                    tr(self.language, "Discard unsaved changes?"), parent=self.top):
                self.files.selection_clear(0, "end")
                self.files.selection_set(self.file_position)
                return
        self.file_position = self.files.curselection()[0]
        _name, filename = selected
        self.filename = filename
        self.path = game_data_dir() / filename
        self.path_label.configure(text=str(self.path))
        self.schema = SCHEMAS.get(filename)
        self.data = load_json(self.path, {} if filename == "balance.json" else [])
        self.mode = "dict" if isinstance(self.data, dict) else "list"
        self.dict_keys = sorted(self.data) if isinstance(self.data, dict) else []
        self.index = None
        self.dirty = False
        self.filter_var.set("")
        if filename == "dialogue.json":
            self.vocab_button.pack(side="left")
        else:
            self.vocab_button.pack_forget()
        self.refresh_records()

    def filtered_indices(self) -> list[int]:
        query = self.filter_var.get().strip().casefold() if hasattr(self, "filter_var") else ""
        if self.mode == "list":
            indices = list(range(len(self.data)))
            if query:
                indices = [i for i in indices
                           if query in self.search_text(self.data[i], i).casefold()]
            return indices
        indices = list(range(len(self.dict_keys)))
        if query:
            indices = [i for i in indices if query in self.dict_keys[i].casefold()]
        return indices

    def update_status(self) -> None:
        count = len(self.data) if self.mode == "list" else len(self.dict_keys)
        if self.language == "zh":
            unit = "条记录" if self.mode == "list" else "个数值"
            text = f"{count} {unit}"
            if self.dirty:
                text += "  [未保存]"
        else:
            unit = "record(s)" if self.mode == "list" else "value(s)"
            text = f"{count} {unit}"
            if self.dirty:
                text += "  [UNSAVED]"
        self.status_label.configure(text=text)

    def search_text(self, record: Any, index: int) -> str:
        title = record_title(record, index, self.filename,
                             self.localizer if self.language == "zh" else None)
        try:
            raw = json.dumps(record, ensure_ascii=False)
        except (TypeError, ValueError):
            raw = ""
        return f"{title} {raw}"

    def refresh_records(self) -> None:
        previous = self.index
        self.records.delete(0, "end")
        self.record_indices = self.filtered_indices()
        localizer = self.localizer if self.language == "zh" else None
        csharp_types = {bool: "Boolean", int: "Int32", float: "Single", str: "String"}
        if self.mode == "list":
            for index in self.record_indices:
                self.records.insert("end", record_title(
                    self.data[index], index, self.filename, localizer))
        else:
            for index in self.record_indices:
                key = self.dict_keys[index]
                value = self.data[key]
                type_name = BALANCE_TYPES.get(key) or csharp_types.get(
                    type(value), type(value).__name__)
                self.records.insert("end", f"{key} = {value}   ({type_name})")
        self.update_status()
        if not self.records.size():
            self.index = None
            self.clear_form()
            return
        position = 0
        if previous is not None and previous in self.record_indices:
            position = self.record_indices.index(previous)
        self.records.selection_clear(0, "end")
        self.records.selection_set(position)
        self.show_record()

    def clear_form(self) -> None:
        for child in self.form.winfo_children():
            child.destroy()
        self.field_widgets = {}
        self.choice_value_maps = {}
        self.rows = {}

    def current_record(self) -> Any:
        if self.index is None:
            return None
        if self.mode == "list":
            return self.data[self.index]
        return self.data[self.dict_keys[self.index]]

    def show_record(self, *_event) -> None:
        selection = self.records.curselection()
        if not selection:
            self.clear_form()
            return
        self.index = self.record_indices[selection[0]]
        self.clear_form()
        record = self.current_record()
        if self.mode == "dict" or not isinstance(record, dict):
            self.add_field("value", "Value", record, None)
            return
        keys = set(record)
        if self.schema:
            section = None
            for spec in self.schema:
                if spec.get("section") and spec["section"] != section:
                    section = spec["section"]
                    ttk.Label(self.form, text=tr_field(self.language, section),
                              font=("Segoe UI", 10, "bold"),
                              foreground="#555").pack(anchor="w", pady=(10, 2))
                value = record.get(spec["key"], self.default_for(spec))
                self.add_field(spec["key"], tr_field(self.language, spec["title"]), value, spec)
                preview = self.preview_for(spec["key"], record, value)
                if preview:
                    self.add_preview(preview)
                keys.discard(spec["key"])
        if self.show_extras.get() and keys:
            ttk.Label(self.form, text=tr(self.language, "Other JSON fields"),
                      font=("Segoe UI", 10, "bold"),
                      foreground="#555").pack(anchor="w", pady=(10, 2))
            for key in sorted(keys):
                self.add_field(key, label(key), record[key], None)
        if self.filename == "equipment.json" and self.schema:
            self.update_equipment_visibility()

    def preview_for(self, key: str, record: dict, value: Any) -> str:
        if not self.localizer.enabled:
            return ""
        if self.filename == "dreams.json":
            if key == "title":
                return self.localizer.dream_title(record)
            if key == "philosophicalHint":
                return self.localizer.dream_hint(record)
        if self.filename == "dialogue.json" and key == "text":
            return self.localizer.dialogue_text(record)
        if self.filename == "monster_families.json":
            if key == "familyName":
                return self.localizer.monster_family(str(value or ""))
            if key == "description":
                return self.localizer.description(value)
        if self.filename == "equipment.json" and key == "description":
            return self.localizer.description(value)
        if self.filename == "npcs.json" and key == "loreNote":
            return self.localizer.description(value)
        return ""

    def add_preview(self, text: str) -> None:
        ttk.Label(self.form, text="中文预览：" + text, foreground="#0a6a4a",
                  wraplength=760, justify="left").pack(
            anchor="w", padx=(36, 0), pady=(0, 3))

    @staticmethod
    def default_for(spec: dict) -> Any:
        if spec.get("default") is not None:
            return spec["default"]
        if spec["kind"] == "bool":
            return False
        if spec["kind"] == "int":
            return spec["min"] if spec.get("min") is not None else 0
        if spec["kind"] == "float":
            return 0.0
        if spec["kind"] in ("json", "tiers", "content"):
            return []
        if spec["kind"] == "choice":
            options = spec.get("options") or [""]
            return options[0]
        return ""

    # ---- form widgets ------------------------------------------------------------------------

    def add_field(self, key: str, title: str, value: Any, spec: dict | None) -> None:
        row = ttk.Frame(self.form, padding=(0, 3))
        row.pack(fill="x", anchor="w")
        self.rows[key] = row
        ttk.Label(row, text=title, width=34).pack(side="left", anchor="n")
        kind = spec["kind"] if spec else None
        if spec and spec.get("readonly"):
            ttk.Label(row, text=str(value), foreground="#333").pack(side="left")
            self.field_widgets[key] = ("readonly", value, spec)
        elif kind == "bool":
            variable = tk.BooleanVar(value=bool(value))
            ttk.Checkbutton(row, variable=variable).pack(side="left")
            self.field_widgets[key] = ("bool", variable, spec)
        elif kind == "choice":
            options = list(spec.get("options") or [])
            if str(value) not in options:
                options.insert(0, str(value))
            display_map: dict[str, str] = {}
            for option in options:
                display = tr_value(self.language, option)
                if display in display_map:
                    display = f"{display} ({option})"
                display_map[display] = option
            current_display = tr_value(self.language, str(value))
            if current_display not in display_map:
                display_map[current_display] = str(value)
            self.choice_value_maps[key] = display_map
            variable = tk.StringVar(value=current_display)
            box = ttk.Combobox(row, textvariable=variable, values=list(display_map),
                               state="readonly", width=60)
            box.pack(side="left", fill="x", expand=True)
            if self.filename == "equipment.json" and key in ("slot", "weaponType"):
                box.bind("<<ComboboxSelected>>", lambda _event: self.update_equipment_visibility())
            self.field_widgets[key] = ("choice", variable, spec)
        elif kind == "int":
            variable = tk.StringVar(value=str(value))
            ttk.Entry(row, textvariable=variable, width=70).pack(side="left", fill="x", expand=True)
            self.field_widgets[key] = ("int", variable, spec)
        elif kind == "float":
            variable = tk.StringVar(value=str(value))
            ttk.Entry(row, textvariable=variable, width=70).pack(side="left", fill="x", expand=True)
            self.field_widgets[key] = ("float", variable, spec)
        elif kind == "text":
            widget = tk.Text(row, height=4, width=70, wrap="word")
            widget.insert("1.0", "" if value is None else str(value))
            widget.pack(side="left", fill="x", expand=True)
            self.field_widgets[key] = ("text", widget, spec)
        elif kind == "tiers":
            tiers = value if isinstance(value, list) else []
            summary = (f"{len(tiers)} 个层级" if self.language == "zh"
                       else f"{len(tiers)} tier(s)")
            ttk.Label(row, text=summary).pack(side="left")
            ttk.Button(row, text=tr(self.language, "Edit tiers..."),
                       command=lambda: self.open_tiers(tiers)).pack(side="left", padx=6)
            self.field_widgets[key] = ("tiers", tiers, spec)
        elif kind == "content":
            lines = value if isinstance(value, list) else []
            summary = (f"{len(lines)} 行" if self.language == "zh"
                       else f"{len(lines)} line(s)")
            ttk.Label(row, text=summary).pack(side="left")
            ttk.Button(row, text=tr(self.language, "Edit content..."),
                       command=lambda: self.open_content(lines)).pack(side="left", padx=6)
            self.field_widgets[key] = ("content", lines, spec)
        elif kind == "json" or isinstance(value, (dict, list)) or value is None:
            widget = tk.Text(row, height=6, width=70, wrap="word")
            widget.insert("1.0", json.dumps(value, ensure_ascii=False, indent=2))
            widget.pack(side="left", fill="x", expand=True)
            self.field_widgets[key] = ("json", widget, spec)
        elif isinstance(value, bool):
            variable = tk.BooleanVar(value=value)
            ttk.Checkbutton(row, variable=variable).pack(side="left")
            self.field_widgets[key] = ("bool", variable, spec)
        elif isinstance(value, str) and (len(value) > 80 or "\n" in value):
            widget = tk.Text(row, height=4, width=70, wrap="word")
            widget.insert("1.0", value)
            widget.pack(side="left", fill="x", expand=True)
            self.field_widgets[key] = ("strtext", widget, spec)
        else:
            variable = tk.StringVar(value="" if value is None else str(value))
            ttk.Entry(row, textvariable=variable, width=70).pack(side="left", fill="x", expand=True)
            inferred = "int" if isinstance(value, int) and not isinstance(value, bool) else \
                "float" if isinstance(value, float) else "str"
            self.field_widgets[key] = (inferred, variable, spec)

    def choice_value(self, key: str) -> str:
        widget = self.field_widgets.get(key)
        if not widget:
            return "None"
        shown = widget[1].get()
        return self.choice_value_maps.get(key, {}).get(shown, shown)

    def update_equipment_visibility(self) -> None:
        slot_value = self.choice_value("slot")
        weapon_value = self.choice_value("weaponType")
        is_weapon = slot_value in WEAPON_SLOTS
        is_shield = is_weapon and weapon_value in SHIELD_TYPES
        for key, row in self.rows.items():
            spec = next((s for s in self.schema or [] if s["key"] == key), None)
            group = spec.get("group") if spec else None
            visible = (group is None
                       or (group == "weapon" and is_weapon)
                       or (group == "shield" and is_shield)
                       or (group == "armor" and not is_weapon))
            if visible:
                if not row.winfo_manager():
                    row.pack(fill="x", anchor="w")
            elif row.winfo_manager():
                row.pack_forget()

    def open_tiers(self, tiers: list) -> None:
        if not self.apply_form():
            return
        record = self.current_record()
        if not isinstance(record, dict):
            return

        def changed():
            self.dirty = True
            self.refresh_records()

        TierEditor(self.top, record, changed, self.language, self.localizer)

    def open_content(self, lines: list) -> None:
        if not self.apply_form():
            return
        record = self.current_record()
        if not isinstance(record, dict):
            return

        def commit(values):
            record["content"] = values
            self.dirty = True
            self.refresh_records()

        display_title = (self.localizer.dream_title(record)
                         if self.localizer.enabled else "") or record.get("title", "")
        title = (f"「{display_title}」的内容" if self.language == "zh"
                 else f"Content of \"{record.get('title', '')}\"")
        previews = [self.localizer.dream_content(record, index) for index in range(len(lines))] \
            if self.localizer.enabled else []
        StringListEditor(self.top, title, lines, commit, self.language, previews)

    def read_field(self, key: str) -> Any:
        kind, widget, spec = self.field_widgets[key]
        title = spec["title"] if spec else label(key)
        if kind == "readonly":
            return widget
        if kind == "bool":
            return bool(widget.get())
        if kind == "choice":
            shown = widget.get()
            return self.choice_value_maps.get(key, {}).get(shown, shown)
        if kind in ("text", "strtext"):
            return widget.get("1.0", "end-1c")
        if kind in ("tiers", "content"):
            return widget
        if kind == "json":
            try:
                return json.loads(widget.get("1.0", "end-1c"))
            except json.JSONDecodeError as error:
                if self.language == "zh":
                    raise ValueError(f"{title}：JSON 无效：{error}") from error
                raise ValueError(f"{title}: invalid JSON: {error}") from error
        raw = widget.get()
        if kind == "int":
            try:
                value = int(raw)
            except ValueError as error:
                if self.language == "zh":
                    raise ValueError(f"{title}：需要整数") from error
                raise ValueError(f"{title}: expected an integer") from error
        elif kind == "float":
            try:
                value = float(raw)
            except ValueError as error:
                if self.language == "zh":
                    raise ValueError(f"{title}：需要数字") from error
                raise ValueError(f"{title}: expected a number") from error
        else:
            value = raw
        if spec:
            if spec.get("min") is not None and value < spec["min"]:
                if self.language == "zh":
                    raise ValueError(f"{title}：不能小于 {spec['min']}")
                raise ValueError(f"{title}: must be at least {spec['min']}")
            if spec.get("max") is not None and value > spec["max"]:
                if self.language == "zh":
                    raise ValueError(f"{title}：不能大于 {spec['max']}")
                raise ValueError(f"{title}: must be at most {spec['max']}")
        return value

    def normalize(self, spec: dict | None, value: Any) -> Any:
        if spec and spec.get("optional") and isinstance(value, str) and not value.strip():
            return None
        if spec and spec["key"] == "storyRole" and value == NONE_STORY_ROLE:
            return None
        return value

    def apply_form(self, mark_dirty: bool = True) -> bool:
        if self.index is None:
            return False
        try:
            values = {}
            for key in self.field_widgets:
                spec = self.field_widgets[key][2]
                values[key] = self.normalize(spec, self.read_field(key))
        except ValueError as error:
            messagebox.showerror(tr(self.language, "Invalid value"), str(error), parent=self.top)
            return False
        if self.mode == "list":
            record = self.data[self.index]
            if isinstance(record, dict):
                original_keys = set(record)
                for key, value in values.items():
                    if key not in original_keys and (value is None or value == "" or value == []
                                                      or value is False):
                        continue
                    record[key] = value
            else:
                self.data[self.index] = values.get("value")
        else:
            key = self.dict_keys[self.index]
            value = values.get("value")
            if isinstance(self.data[key], bool) and not isinstance(value, bool):
                value = str(value).strip().lower() in ("true", "1", "yes")
            self.data[key] = value
        if mark_dirty:
            self.dirty = True
        self.refresh_records()
        return True

    # ---- validation and saving ---------------------------------------------------------------

    def validate_data(self) -> str | None:
        if not self.schema or self.mode != "list":
            return None
        seen = set()
        for index, record in enumerate(self.data):
            if not isinstance(record, dict):
                continue
            for spec in self.schema:
                key = spec["key"]
                value = record.get(key)
                title = tr_field(self.language, spec["title"])
                if spec.get("required") and (value is None or value == ""):
                    if self.language == "zh":
                        return f"第 {index + 1} 条记录：{title} 为必填项。"
                    return f"Record {index + 1}: {spec['title']} is required."
                if spec.get("optional") and value is None:
                    continue
                if spec["kind"] in ("int", "float") and isinstance(value, (int, float)):
                    if spec.get("min") is not None and value < spec["min"]:
                        if self.language == "zh":
                            return f"第 {index + 1} 条记录：{title} 不能小于 {spec['min']}。"
                        return f"Record {index + 1}: {spec['title']} is below {spec['min']}."
                    if spec.get("max") is not None and value > spec["max"]:
                        if self.language == "zh":
                            return f"第 {index + 1} 条记录：{title} 不能大于 {spec['max']}。"
                        return f"Record {index + 1}: {spec['title']} is above {spec['max']}."
                if spec.get("unique") and value is not None:
                    if value in seen:
                        if self.language == "zh":
                            return f"{title} 重复：{value}。"
                        return f"Duplicate {spec['title']}: {value}."
                    seen.add(value)
            if self.filename == "dreams.json":
                if record.get("minLevel", 0) > record.get("maxLevel", 100):
                    return ("第 %d 条记录：最低等级高于最高等级。" % (index + 1)
                            if self.language == "zh"
                            else f"Record {index + 1}: MinLevel is above MaxLevel.")
                if record.get("minAwakening", 0) > record.get("maxAwakening", 7):
                    return ("第 %d 条记录：最低觉醒高于最高觉醒。" % (index + 1)
                            if self.language == "zh"
                            else f"Record {index + 1}: MinAwakening is above MaxAwakening.")
            if self.filename == "monster_families.json":
                for tier in record.get("tiers") or []:
                    if isinstance(tier, dict) and tier.get("minLevel", 0) > tier.get("maxLevel", 100):
                        return ("第 %d 条记录：某个层级的最低等级高于最高等级。" % (index + 1)
                                if self.language == "zh"
                                else f"Record {index + 1}: a tier's MinLevel is above MaxLevel.")
        return None

    def save_file(self) -> None:
        if self.path is None:
            return
        if self.index is not None and not self.apply_form():
            return
        problem = self.validate_data()
        if problem:
            messagebox.showerror(tr(self.language, "Validation failed"), problem,
                                 parent=self.top)
            return
        try:
            backup = write_json(self.path, self.data)
        except OSError as error:
            messagebox.showerror(tr(self.language, "Save failed"), str(error), parent=self.top)
            return
        self.dirty = False
        self.update_status()
        if self.language == "zh":
            message = f"已保存 {self.path.name}。"
            if backup:
                message += f"\n备份：{backup.name}"
        else:
            message = f"Saved {self.path.name}."
            if backup:
                message += f"\nBackup: {backup.name}"
        messagebox.showinfo(tr(self.language, "Saved"), message, parent=self.top)

    def toggle_extras(self) -> None:
        if self.index is not None:
            self.apply_form(mark_dirty=False)
        else:
            self.refresh_records()

    def show_dialogue_vocabulary(self) -> None:
        categories = sorted({d.get("category", "") for d in self.data
                             if isinstance(d, dict) and d.get("category")})
        personalities = sorted({d.get("personalityType", "") for d in self.data
                                if isinstance(d, dict) and d.get("personalityType")})
        emotions = sorted({d.get("emotion", "") for d in self.data
                           if isinstance(d, dict) and d.get("emotion")})
        contexts = sorted({d.get("context", "") for d in self.data
                           if isinstance(d, dict) and d.get("context")})
        if self.language == "zh":
            body = ("分类：\n  " + ", ".join(categories)
                    + "\n\n性格类型：\n  " + ", ".join(personalities)
                    + "\n\n情绪：\n  " + ", ".join(emotions)
                    + "\n\n情境：\n  " + ", ".join(contexts))
        else:
            body = ("Categories:\n  " + ", ".join(categories)
                    + "\n\nPersonalities:\n  " + ", ".join(personalities)
                    + "\n\nEmotions:\n  " + ", ".join(emotions)
                    + "\n\nContexts:\n  " + ", ".join(contexts))
        messagebox.showinfo(tr(self.language, "Dialogue vocabulary"), body, parent=self.top)

    def close_window(self) -> None:
        if self.dirty and not messagebox.askyesno(
                tr(self.language, "Discard unsaved changes"),
                tr(self.language, "Discard unsaved changes and close?"), parent=self.top):
            return
        self.top.destroy()

    # ---- record operations -------------------------------------------------------------------

    def blank_record(self) -> dict:
        record = {}
        for spec in self.schema or []:
            value = self.default_for(spec)
            if spec.get("optional") and value in ("", None, [], NONE_STORY_ROLE):
                continue
            record[spec["key"]] = value
        if self.filename == "equipment.json":
            ids = [r.get("id") for r in self.data if isinstance(r, dict)
                   and isinstance(r.get("id"), int)]
            record["id"] = max(ids, default=200000) + 1
            record["minLevel"] = 1
        if self.filename == "dreams.json":
            record["id"] = "new_dream_" + str(time.time_ns())
            record["title"] = "New Dream"
        if self.filename == "monster_families.json":
            record["familyName"] = "New Family"
        if self.filename == "npcs.json":
            record["name"] = "New NPC"
        if self.filename == "dialogue.json":
            record["id"] = "mod_" + str(time.time_ns())
            record["category"] = "greeting"
        return record

    def add_record(self) -> None:
        if self.mode == "list":
            if self.schema:
                record = self.blank_record()
            else:
                sample = next((record for record in self.data if isinstance(record, dict)), None)
                record = {key: self.blank_like(value) for key, value in sample.items()} \
                    if isinstance(sample, dict) else {}
            self.data.append(record)
            self.index = len(self.data) - 1
            self.filter_var.set("")
        else:
            key = simpledialog.askstring(
                tr(self.language, "Add value"), tr(self.language, "Key:"), parent=self.top)
            if not key or key in self.data:
                return
            self.data[key] = 0
            self.dict_keys = sorted(self.data)
            self.index = self.dict_keys.index(key)
            self.filter_var.set("")
        self.dirty = True
        self.refresh_records()

    @staticmethod
    def blank_like(value: Any) -> Any:
        if isinstance(value, bool):
            return False
        if isinstance(value, int):
            return 0
        if isinstance(value, float):
            return 0.0
        if isinstance(value, str):
            return ""
        if isinstance(value, list):
            return []
        if isinstance(value, dict):
            return {}
        return None

    def clone_record(self) -> None:
        selection = self.records.curselection()
        if not selection or self.mode != "list":
            return
        index = self.record_indices[selection[0]]
        clone = copy.deepcopy(self.data[index])
        if isinstance(clone, dict) and self.schema:
            for spec in self.schema:
                key = spec["key"]
                if spec.get("unique") and spec["kind"] == "int":
                    ids = [r.get(key) for r in self.data if isinstance(r, dict)
                           and isinstance(r.get(key), int)]
                    clone[key] = max(ids, default=spec["min"] or 0) + 1
                elif spec.get("unique") and isinstance(clone.get(key), str):
                    clone[key] = clone[key] + "_copy_" + str(time.time_ns())
        self.data.append(clone)
        self.index = len(self.data) - 1
        self.filter_var.set("")
        self.dirty = True
        self.refresh_records()

    def delete_record(self) -> None:
        selection = self.records.curselection()
        if not selection:
            return
        index = self.record_indices[selection[0]]
        if not messagebox.askyesno(
                tr(self.language, "Delete record"),
                tr(self.language, "Delete the selected record?"), parent=self.top):
            return
        if self.mode == "list":
            del self.data[index]
        else:
            del self.data[self.dict_keys[index]]
            self.dict_keys = sorted(self.data)
        self.index = None
        self.dirty = True
        self.refresh_records()

    def export_defaults(self) -> None:
        if not messagebox.askyesno(
                tr(self.language, "Export defaults"),
                tr(self.language, "Overwrite GameData with the built-in defaults?"),
                parent=self.top):
            return
        try:
            folder = export_defaults()
        except Exception as error:
            messagebox.showerror(tr(self.language, "Export failed"), str(error), parent=self.top)
            return
        self.load_file(force=True)
        message = (f"已导出到 {folder}" if self.language == "zh"
                   else f"Exported to {folder}")
        messagebox.showinfo(tr(self.language, "Export defaults"), message, parent=self.top)
