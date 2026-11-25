"""Path discovery, JSON I/O and backups shared by the Python editor windows."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

GAME_DATA_FILES = [
    ("Equipment", "equipment.json"),
    ("NPCs", "npcs.json"),
    ("Monster families", "monster_families.json"),
    ("Dreams", "dreams.json"),
    ("Dialogue", "dialogue.json"),
    ("Balance values", "balance.json"),
    ("Achievements (normally disabled)", "achievements.json"),
]


def repo_root() -> Path | None:
    here = Path(__file__).resolve()
    for candidate in (here.parent, *here.parents):
        if (candidate / "usurper-reloaded.csproj").exists():
            return candidate
    return None


def game_executable() -> Path | None:
    root = repo_root()
    if root is None:
        return None
    for relative in (
        "bin/Debug/net8.0/UsurperReborn.exe",
        "bin/Release/net8.0/UsurperReborn.exe",
        "bin/Debug/net8.0/UsurperReborn",
        "bin/Release/net8.0/UsurperReborn",
    ):
        path = root / relative
        if path.exists():
            return path
    return None


def game_data_dir() -> Path:
    exe = game_executable()
    if exe is not None:
        return exe.parent / "GameData"
    root = repo_root()
    return (root / "GameData") if root is not None else Path.cwd() / "GameData"


def save_dir(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit)
    candidates: list[Path] = []
    if sys.platform.startswith("win"):
        appdata = os.environ.get("APPDATA")
        if appdata:
            candidates.append(Path(appdata) / "UsurperReloaded" / "saves")
    elif os.environ.get("HOME"):
        candidates.append(Path(os.environ["HOME"]) / ".local/share/UsurperReloaded/saves")
    root = repo_root()
    if root is not None:
        candidates += [root / "bin/Debug/net8.0/saves", root / "bin/Release/net8.0/saves"]
    candidates.append(Path.cwd() / "saves")
    existing = [path for path in candidates if path.is_dir()]
    if existing:
        def newest(directory: Path) -> float:
            return max((p.stat().st_mtime for p in directory.glob("*.json")), default=0)
        return max(existing, key=newest)
    return candidates[0] if candidates else Path.cwd() / "saves"


def load_json(path: Path, default):
    if not path.exists():
        return default
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data, backup: bool = True) -> Path | None:
    path.parent.mkdir(parents=True, exist_ok=True)
    saved = None
    if backup and path.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        saved = path.with_name(f"{path.name}.bak-{stamp}")
        counter = 1
        while saved.exists():
            saved = path.with_name(f"{path.name}.bak-{stamp}-{counter}")
            counter += 1
        shutil.copy2(path, saved)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return saved


def export_defaults() -> str:
    exe = game_executable()
    if exe is None:
        raise FileNotFoundError("UsurperReborn.exe was not found; cannot export GameData.")
    result = subprocess.run(
        [str(exe), "--export-data"], cwd=str(exe.parent), capture_output=True, text=True, timeout=180)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or "export failed").strip())
    return str(game_data_dir())
