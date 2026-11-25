"""Read-only Chinese text for GameData records.

The JSON in GameData stays English because it is the source/fallback text; the
game translates dreams, NPC dialogue and monster names through Localization/
zh.json, and the wiki build already has Chinese descriptions for monsters and
items. This module exposes those translations so the editor can show a Chinese
preview without rewriting the source data.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .common import game_data_dir, game_executable, repo_root

SNAKE = re.compile(r"[^A-Za-z0-9]+")


def _read(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _clean(value: Any) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else ""


def _snake(name: str) -> str:
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    return SNAKE.sub("_", spaced).strip("_").lower()


class GameDataLocalizer:
    def __init__(self, language: str = "en"):
        self.language = language
        self.enabled = language == "zh"
        self.localization: dict[str, Any] = {}
        self.mod: dict[str, Any] = {}
        self.generated: dict[str, Any] = {}
        self.manual: dict[str, Any] = {}
        if not self.enabled:
            return
        self.reload()

    def reload(self) -> None:
        if not self.enabled:
            return
        self.localization = _read(self._localization_path())
        self.mod = {}
        for path in self._mod_localization_files():
            self.mod.update(_read(path))
        self.generated = _read(self._repo_file("tools/wiki-build/wiki-zh-generated.json"))
        self.manual = _read(Path(__file__).with_name("editor_zh_content.json"))

    def _mod_localization_files(self) -> list[Path]:
        base = game_data_dir() / "Localization"
        files: list[Path] = []
        direct = base / f"{self.language}.json"
        if direct.exists():
            files.append(direct)
        subdir = base / self.language
        if subdir.is_dir():
            files.extend(sorted(subdir.glob("*.json")))
        return files

    def _lookup(self, key: str) -> str:
        return _clean(self.mod.get(key)) or _clean(self.localization.get(key))

    @staticmethod
    def _repo_file(relative: str) -> Path:
        root = repo_root()
        return (root / relative) if root is not None else Path(relative)

    def _localization_path(self) -> Path:
        candidates: list[Path] = []
        root = repo_root()
        if root is not None:
            candidates.append(root / "Localization" / "zh.json")
        exe = game_executable()
        if exe is not None:
            candidates.append(exe.parent / "Localization" / "zh.json")
        here = Path(__file__).resolve()
        for parent in here.parents:
            candidates.append(parent / "Localization" / "zh.json")
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return candidates[0]

    def dream_title(self, dream: dict) -> str:
        return self._lookup(f"dream.{dream.get('id', '')}.title")

    def dream_hint(self, dream: dict) -> str:
        return self._lookup(f"dream.{dream.get('id', '')}.hint")

    def dream_content(self, dream: dict, index: int) -> str:
        return self._lookup(f"dream.{dream.get('id', '')}.content.{index}")

    def dialogue_text(self, line: dict) -> str:
        translated = self._lookup(f"npc_dialogue.{line.get('id', '')}")
        if translated:
            return translated
        text = line.get("text", "")
        return self.manual.get(text) or self.generated.get(text) or ""

    def monster_family(self, name: str) -> str:
        return (self._lookup(f"mod.monster.{name}.name")
                or self._lookup(f"monster.family.{name.lower()}"))

    def monster_tier(self, name: str) -> str:
        return (self._lookup(f"mod.monster.tier.{name}.name")
                or self._lookup(f"monster.name.{_snake(name)}"))

    def monster_description(self, record: dict) -> str:
        family = str(record.get("familyName", ""))
        return (self._lookup(f"mod.monster.{family}.description")
                or self.description(record.get("description", "")))

    def equipment_name(self, record: dict) -> str:
        return self._lookup(f"mod.equipment.{record.get('id', '')}.name")

    def equipment_description(self, record: dict) -> str:
        return (self._lookup(f"mod.equipment.{record.get('id', '')}.description")
                or self.description(record.get("description", "")))

    def npc_name(self, record: dict) -> str:
        return self._lookup(f"mod.npc.{record.get('name', '')}.name")

    def npc_lore(self, record: dict) -> str:
        return (self._lookup(f"mod.npc.{record.get('name', '')}.lore")
                or self.description(record.get("loreNote", "")))

    def description(self, text: Any) -> str:
        if not isinstance(text, str) or not text.strip():
            return ""
        return _clean(self.manual.get(text) or self.generated.get(text))

    lore = description
