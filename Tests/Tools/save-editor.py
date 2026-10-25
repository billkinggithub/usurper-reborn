#!/usr/bin/env python3
"""A window for editing a single-player save, with no build step and no dependencies.

    python Tools/save-editor.py            # normal use
    python Tools/save-editor.py --check    # list saves and field counts, open no window
    python Tools/save-editor.py --saves <dir>

Only the player object is editable, and only fields that already exist. A value keeps the type it already
had, so a level cannot become 5.5 and a gold total cannot lose its digits. Saving copies the file it replaces
to a timestamped backup first and renames its own temporary file into place, so nothing is written halfway.

Close the game before saving: it holds the save open and rewrites it on autosave.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

GAME_PROJECT = "usurper-reloaded.csproj"

# Fields worth reaching quickly. Everything is still searchable; this is only the order of the first screen.
PRIORITY = [
    "name2", "level", "experience", "gold", "bankGold",
    "hp", "maxHP", "mana", "maxMana", "stamina",
    "strength", "defence", "agility", "charisma", "intelligence", "wisdom",
    "constitution", "dexterity", "fame", "mental", "age",
]


def find_saves_directory(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    for parent in [Path(__file__).resolve().parent, *Path(__file__).resolve().parents]:
        if (parent / GAME_PROJECT).is_file():
            return parent / "bin" / "Debug" / "net8.0" / "saves"
    return Path.cwd() / "saves"


def list_saves(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    return sorted(directory.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)


def describe(path: Path) -> str:
    stamp = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    return f"{path.name}   ({stamp}, {path.stat().st_size // 1024} KB)"


def load_player(path: Path) -> dict:
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    player = data.get("player")
    if not isinstance(player, dict):
        raise ValueError(f"{path.name} has no player object")
    return data


def is_editable(value) -> bool:
    return isinstance(value, (int, float, bool, str))


def kind_of(value) -> str:
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    return "text"


def show(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def coerce(current, text: str):
    """Turn typed text into a value of the kind the field already has, or raise ValueError with a reason."""
    text = text.strip()
    kind = kind_of(current)

    if kind == "bool":
        lowered = text.lower()
        if lowered in ("true", "1", "yes", "y"):
            return True
        if lowered in ("false", "0", "no", "n"):
            return False
        raise ValueError("需要 true 或 false")

    if kind == "int":
        try:
            return int(text)
        except ValueError:
            raise ValueError("需要整数") from None

    if kind == "float":
        try:
            return float(text)
        except ValueError:
            raise ValueError("需要数字") from None

    return text


def apply_changes(player: dict, changes: dict) -> tuple[list[str], list[str]]:
    """Validate every change before touching the file. Returns (applied, refused) as readable lines."""
    applied: list[str] = []
    refused: list[str] = []
    for key, text in changes.items():
        if key not in player:
            refused.append(f"{key}: 这个存档没有这个字段")
            continue
        current = player[key]
        if not is_editable(current):
            refused.append(f"{key}: 不是简单值")
            continue
        try:
            player[key] = coerce(current, text)
        except ValueError as error:
            refused.append(f"{key}: {error}")
            continue
        applied.append(f"{key} = {show(player[key])}")
    return applied, refused


def save_player(path: Path, data: dict) -> Path:
    backup = path.with_name(f"{path.name}.bak-{datetime.now():%Y%m%d-%H%M%S}")
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


def check(directory: Path) -> int:
    saves = list_saves(directory)
    if not saves:
        print(f"没有找到存档：{directory}")
        return 1
    print(f"存档目录：{directory}")
    for path in saves[:10]:
        try:
            data = load_player(path)
        except (ValueError, json.JSONDecodeError) as error:
            print(f"  {path.name}: 读不了（{error}）")
            continue
        player = data["player"]
        editable = sum(1 for value in player.values() if is_editable(value))
        print(f"  {path.name}: {editable} 个可编辑字段，Lv.{player.get('level')} {player.get('name2')}")
    return 0


class EditorWindow:
    """A list of fields on the left, an editor for the selected one on the right."""

    def __init__(self, directory: Path):
        import tkinter as tk
        from tkinter import ttk

        self.tk = tk
        self.ttk = ttk
        self.directory = directory
        self.path: Path | None = None
        self.data: dict = {}
        self.player: dict = {}
        self.pending: dict[str, str] = {}   # key -> text as typed, not yet applied

        self.root = tk.Tk()
        self.root.title("Usurper Reborn 存档编辑器")
        self.root.geometry("900x620")

        top = ttk.Frame(self.root, padding=8)
        top.pack(fill="x")
        ttk.Label(top, text="存档").pack(side="left")
        self.save_box = ttk.Combobox(top, state="readonly", width=52)
        self.save_box.pack(side="left", padx=6)
        self.save_box.bind("<<ComboboxSelected>>", lambda _event: self.load_selected())
        ttk.Button(top, text="重新读取", command=self.load_selected).pack(side="left")

        ttk.Label(top, text="搜索").pack(side="left", padx=(16, 0))
        self.search = ttk.Entry(top, width=24)
        self.search.pack(side="left", padx=6)
        self.search.bind("<KeyRelease>", lambda _event: self.fill_list())

        body = ttk.Frame(self.root, padding=(8, 0))
        body.pack(fill="both", expand=True)

        left = ttk.Frame(body)
        left.pack(side="left", fill="both", expand=True)
        self.list = ttk.Treeview(left, columns=("value",), show="tree headings", height=22)
        self.list.heading("#0", text="字段")
        self.list.heading("value", text="当前值")
        self.list.column("#0", width=210)
        self.list.column("value", width=170)
        self.list.pack(side="left", fill="both", expand=True)
        bar = ttk.Scrollbar(left, orient="vertical", command=self.list.yview)
        bar.pack(side="right", fill="y")
        self.list.configure(yscrollcommand=bar.set)
        self.list.bind("<<TreeviewSelect>>", lambda _event: self.show_selected())
        self.list.tag_configure("changed", foreground="#b45309")

        right = ttk.Frame(body, padding=(12, 0, 0, 0), width=260)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)
        self.field_label = ttk.Label(right, text="（选一个字段）", font=("Segoe UI", 11, "bold"))
        self.field_label.pack(anchor="w", pady=(4, 8))
        ttk.Label(right, text="当前值").pack(anchor="w")
        self.current_label = ttk.Label(right, text="—", foreground="#555")
        self.current_label.pack(anchor="w", pady=(0, 8))
        ttk.Label(right, text="新值").pack(anchor="w")
        self.entry = ttk.Entry(right)
        self.entry.pack(fill="x", pady=(0, 6))
        self.entry.bind("<Return>", lambda _event: self.stage_selected())
        ttk.Button(right, text="应用这一项", command=self.stage_selected).pack(fill="x")
        ttk.Separator(right).pack(fill="x", pady=12)
        ttk.Button(right, text="保存全部改动", command=self.save).pack(fill="x")

        self.status = tk.Text(self.root, height=6, wrap="word")
        self.status.pack(fill="x", padx=8, pady=8)
        self.status.configure(state="disabled")

        ttk.Label(
            self.root,
            text="保存前请关闭游戏：游戏运行时会用自动存档覆盖修改。",
            foreground="#b91c1c",
        ).pack(anchor="w", padx=8, pady=(0, 6))

        self.refresh_saves()

    # ---- actions -----------------------------------------------------------------------------------

    def refresh_saves(self) -> None:
        saves = list_saves(self.directory)
        self.save_box["values"] = [describe(path) for path in saves]
        if saves:
            self.save_box.current(0)
            self.load_selected()
        else:
            self.say(f"没有找到存档：{self.directory}")

    def load_selected(self) -> None:
        index = self.save_box.current()
        saves = list_saves(self.directory)
        if index < 0 or index >= len(saves):
            return
        self.path = saves[index]
        try:
            self.data = load_player(self.path)
        except (ValueError, json.JSONDecodeError) as error:
            self.say(f"读取失败：{error}")
            return
        self.player = self.data["player"]
        self.pending.clear()
        self.fill_list()
        self.say(f"{self.path.name}：{self.player.get('name2')}  Lv.{self.player.get('level')}，"
                 f"{sum(1 for v in self.player.values() if is_editable(v))} 个可编辑字段。")

    def visible_keys(self) -> list[str]:
        needle = self.search.get().strip().lower()
        keys = [k for k, v in self.player.items() if is_editable(v)]
        if needle:
            keys = [k for k in keys if needle in k.lower()]
        order = {k: i for i, k in enumerate(PRIORITY)}
        keys.sort(key=lambda k: (order.get(k, len(PRIORITY)), k))
        return keys

    def fill_list(self) -> None:
        self.list.delete(*self.list.get_children())
        for key in self.visible_keys():
            text = self.pending.get(key, show(self.player[key]))
            tag = ("changed",) if key in self.pending and self.pending[key] != show(self.player[key]) else ()
            self.list.insert("", "end", iid=key, text=key, values=(text,), tags=tag)

    def selected_key(self) -> str | None:
        selection = self.list.selection()
        return selection[0] if selection else None

    def show_selected(self) -> None:
        key = self.selected_key()
        if key is None:
            return
        self.field_label.configure(text=key)
        self.current_label.configure(text=show(self.player[key]))
        self.entry.delete(0, "end")
        self.entry.insert(0, self.pending.get(key, show(self.player[key])))

    def stage_selected(self) -> None:
        key = self.selected_key()
        if key is None:
            return
        text = self.entry.get()
        if text == show(self.player[key]):
            self.pending.pop(key, None)
        else:
            self.pending[key] = text
        self.fill_list()
        self.list.selection_set(key)
        self.say(f"{key} 待保存为新值 {text}（还没写入文件）")

    def save(self) -> None:
        if not self.path:
            return
        if not self.pending:
            self.say("没有改动。")
            return

        applied, refused = apply_changes(self.player, self.pending)
        if not applied:
            self.say("没有保存：\n" + "\n".join(refused))
            return

        backup = save_player(self.path, self.data)
        self.pending.clear()
        self.fill_list()
        lines = ["已保存："] + applied
        if refused:
            lines += ["", "未保存："] + refused
        lines += ["", f"备份：{backup.name}"]
        self.say("\n".join(lines))

    def say(self, text: str) -> None:
        self.status.configure(state="normal")
        self.status.delete("1.0", "end")
        self.status.insert("1.0", text)
        self.status.configure(state="disabled")

    def run(self) -> None:
        self.root.mainloop()


def main() -> int:
    # Windows consoles default to a legacy code page in some shells, which turns the messages into noise.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    parser = argparse.ArgumentParser(description="编辑 Usurper Reborn 单机存档")
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
