#!/usr/bin/env python3
"""A window for editing a single-player save, with no build step and no dependencies.

    python Tests/Tools/save-editor.py            # normal use
    python Tests/Tools/save-editor.py --check    # list saves and field counts, open no window
    python Tests/Tools/save-editor.py --saves <dir>

The window covers more than the player object: every scalar in the save is reachable, with
first-class views for the player, the NPC roster, the companions and dungeon party, the world
state, the story systems and the settings. A field keeps the type it already had, so a level
cannot become 5.5 and a gold total cannot lose its digits; a list can gain or lose an element,
and the companion and dungeon-party managers keep the flags and the id lists in step.

Saving copies the file it replaces to a timestamped backup first and renames its own temporary
file into place, so nothing is written halfway.

Close the game before saving: it holds the save open and rewrites it on autosave.
"""

from __future__ import annotations

import argparse
import json
import math
import os
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

    root: Path | None = None
    for parent in [Path(__file__).resolve().parent, *Path(__file__).resolve().parents]:
        if (parent / GAME_PROJECT).is_file():
            root = parent
            candidates += [parent / "bin" / "Debug" / "net8.0" / "saves",
                           parent / "bin" / "Release" / "net8.0" / "saves"]
            break
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
    return LABELS.get(str(part), str(part))


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
        element_kind = kind_of(value[0]) if value else None
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
        self.list = ttk.Treeview(left, columns=("value", "type", "path"),
                                 show="tree headings", height=22, selectmode="browse")
        self.list.heading("#0", text="字段")
        self.list.heading("value", text="当前值")
        self.list.heading("type", text="类型")
        self.list.heading("path", text="路径")
        self.list.column("#0", width=240)
        self.list.column("value", width=300)
        self.list.column("type", width=56)
        self.list.column("path", width=330)
        self.list.pack(side="left", fill="both", expand=True)
        bar = ttk.Scrollbar(left, orient="vertical", command=self.list.yview)
        bar.pack(side="right", fill="y")
        self.list.configure(yscrollcommand=bar.set)
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
        self.path_label.pack(anchor="w", pady=(0, 8))

        ttk.Label(right, text="当前值").pack(anchor="w")
        self.current_label = ttk.Label(right, text="—", foreground="#333", wraplength=310)
        self.current_label.pack(anchor="w", pady=(0, 8))

        ttk.Label(right, text="新值").pack(anchor="w")
        self.editor = tk.Text(right, height=4, wrap="word", undo=True)
        self.editor.pack(fill="x", pady=(0, 6))
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
        self.status = tk.Text(self.root, height=7, wrap="word")
        self.status.pack(fill="x", padx=8, pady=8)
        self.status.configure(state="disabled")
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
                             values=(value, kind, path_text(leaf.path)),
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
        if path == ACTIVE_COMPANIONS_PATH:
            return "int"
        if path == DUNGEON_PARTY_PATH:
            return "str"
        return None

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

        self.tree = ttk.Treeview(self.top, columns=("recruited", "active", "dead", "level",
                                                    "loyalty", "trust", "romance"),
                                 show="tree headings", selectmode="browse", height=8)
        self.tree.heading("#0", text="同伴")
        for column, title in (("recruited", "已招募"), ("active", "出战"), ("dead", "死亡"),
                              ("level", "等级"), ("loyalty", "忠诚"), ("trust", "信任"),
                              ("romance", "恋爱")):
            self.tree.heading(column, text=title)
            self.tree.column(column, width=70, anchor="center")
        self.tree.column("#0", width=110)
        self.tree.pack(fill="both", expand=True, padx=8)

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
        self.current = tk.Listbox(current, height=18)
        self.current.pack(fill="both", expand=True)
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
        self.available = tk.Listbox(available, height=14)
        self.available.pack(fill="both", expand=True, pady=(6, 0))
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
