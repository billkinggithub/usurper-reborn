"""A scan-and-fill editor for GameData/Localization/<lang>.json.

The flat key/value form is fine for a handful of overrides, but a mod author
should not have to remember every key. This window reads the GameData files,
lists the translatable entries with their English source, shows the official
Chinese text as a reference where one exists, and only asks for the rows that
actually need a mod translation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from tkinter import messagebox, ttk
import tkinter as tk
from typing import Any

from .common import game_data_dir, load_json, write_json
from .game_data_loc import (
    GameDataLocalizer, localizable_tier_key, localization_file,
)

REPLACEMENTS = [
    ("Good {time_of_day}", "{5}"),
    ("all {time_of_day}", "{6}"),
    ("{player_name}", "{0}"),
    ("{npc_name}", "{1}"),
    ("{player_title}", "{2}"),
    ("{time_of_day}", "{3}"),
    ("{player_class}", "{4}"),
]

UI = {
    "zh": {
        "title": "模组翻译助手",
        "file": "翻译文件",
        "filter": "显示",
        "filters": ["需要翻译", "全部", "已有模组翻译", "可沿用官方"],
        "search": "搜索键或原文",
        "groups": {"dream": "梦境", "dialogue": "对话", "equipment": "装备",
                   "npc": "NPC", "monster": "怪物", "other": "其他已有键"},
        "status": {"translated": "已有模组翻译", "needed": "待翻译",
                   "official": "可沿用官方", "override": "未覆盖"},
        "key": "键", "source": "原文（英文）", "official": "官方中文参考",
        "translation": "模组翻译", "status_col": "状态",
        "note_stale": "官方译文对应旧文本，仅供参考。",
        "note_dialogue": "这条对话的英文文本与官方不同；要让中文生效，英文模组翻译也要写入同样的模板文本。",
        "note_other": "这是翻译文件中已有的键，扫描不到对应的 GameData 条目。",
        "no_entry": "选择左侧的一条翻译。",
        "apply": "应用当前", "fill_official": "填入官方翻译",
        "fill_source": "填入英文原文", "clear": "清空",
        "save": "保存翻译文件", "rescan": "重新扫描", "close": "关闭",
        "saved": "已保存翻译文件。", "save_failed": "保存失败",
        "discard": "放弃未保存的翻译？",
        "created": "已创建翻译文件：",
        "counts": "需要处理 {needed} 条 · 已有模组翻译 {done} 条 · 可沿用官方 {official} 条",
        "empty": "当前筛选没有条目。",
        "no_official": "（没有官方译文）",
        "src_blank": "（扫描不到 GameData 原文）",
        "trans_hint": "在这里填写中文；留空表示不覆盖官方翻译。",
        "group_counts": "{name} ({count})",
    },
    "en": {
        "title": "Mod translation assistant",
        "file": "Translation file",
        "filter": "Show",
        "filters": ["Not overridden", "All", "Has mod translation"],
        "search": "Search key or source",
        "groups": {"dream": "Dreams", "dialogue": "Dialogue", "equipment": "Equipment",
                   "npc": "NPCs", "monster": "Monsters", "other": "Other existing keys"},
        "status": {"translated": "Overridden", "needed": "Not overridden",
                   "official": "Official text", "override": "Not overridden"},
        "key": "Key", "source": "Source text", "official": "Official text",
        "translation": "Mod translation", "status_col": "Status",
        "note_stale": "",
        "note_dialogue": "",
        "note_other": "This key exists in the translation file but has no matching GameData entry.",
        "no_entry": "Select an entry on the left.",
        "apply": "Apply", "fill_official": "Fill official text",
        "fill_source": "Fill source text", "clear": "Clear",
        "save": "Save translation file", "rescan": "Rescan", "close": "Close",
        "saved": "Translation file saved.", "save_failed": "Save failed",
        "discard": "Discard unsaved translations?",
        "created": "Created translation file: ",
        "counts": "{needed} to do · {done} overridden · {official} official",
        "empty": "No entries match the filter.",
        "no_official": "(no official translation)",
        "src_blank": "(no matching GameData source)",
        "trans_hint": "Write the local text here; blank leaves the official text in place.",
        "group_counts": "{name} ({count})",
    },
}


def dialogue_template(text: str) -> str:
    for named, argument in REPLACEMENTS:
        text = text.replace(named, argument)
    return text


@dataclass
class Entry:
    group: str
    key: str
    source: str
    official: str = ""
    official_valid: bool = True
    note: str = ""


class ModTranslationWindow:
    def __init__(self, parent: tk.Misc, language: str = "zh"):
        self.language = language if language in UI else "en"
        self.t = UI[self.language]
        self.top = tk.Toplevel(parent)
        self.top.title(self.t["title"])
        self.top.geometry("1240x800")
        self.top.transient(parent)

        self.reference = GameDataLocalizer("zh")
        self.english = load_json(localization_file("en"), {})
        self.mod_path = game_data_dir() / "Localization" / f"{self.language}.json"
        self.mod_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.mod_path.exists():
            self.mod_path.write_text("{}\n", encoding="utf-8")
        self.translations: dict[str, str] = {
            str(key): str(value) for key, value in
            (load_json(self.mod_path, {}) or {}).items()
            if value is not None
        }
        self.entries: list[Entry] = []
        self.entry_iids: dict[str, Entry] = {}
        self.current: Entry | None = None
        self.current_iid: str | None = None
        self.dirty = False

        self.filter_var = tk.StringVar(value=self.t["filters"][0])
        self.search_var = tk.StringVar()

        body = ttk.Panedwindow(self.top, orient="horizontal")
        body.pack(fill="both", expand=True, padx=8, pady=8)
        left = ttk.Frame(body)
        body.add(left, weight=3)
        controls = ttk.Frame(left)
        controls.pack(fill="x")
        ttk.Label(controls, text=self.t["filter"]).pack(side="left")
        filter_box = ttk.Combobox(controls, textvariable=self.filter_var,
                                  values=self.t["filters"], state="readonly", width=18)
        filter_box.pack(side="left", padx=(4, 10))
        filter_box.bind("<<ComboboxSelected>>", lambda _event: self.refresh_tree())
        ttk.Label(controls, text=self.t["search"]).pack(side="left")
        search = ttk.Entry(controls, textvariable=self.search_var, width=28)
        search.pack(side="left", padx=4)
        search.bind("<KeyRelease>", lambda _event: self.refresh_tree())

        tree_frame = ttk.Frame(left)
        tree_frame.pack(fill="both", expand=True, pady=(6, 4))
        self.tree = ttk.Treeview(tree_frame, columns=("status", "source"),
                                 show="tree headings", selectmode="browse")
        self.tree.heading("#0", text=self.t["key"])
        self.tree.heading("status", text=self.t["status_col"])
        self.tree.heading("source", text=self.t["source"])
        self.tree.column("#0", width=330)
        self.tree.column("status", width=120, stretch=False)
        self.tree.column("source", width=420)
        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", lambda _event: self.on_select())
        self.count_label = ttk.Label(left, text="", foreground="#555")
        self.count_label.pack(anchor="w")

        right = ttk.Frame(body)
        body.add(right, weight=2)
        self.file_label = ttk.Label(right, text="", foreground="#555", wraplength=480)
        self.file_label.pack(anchor="w", pady=(0, 6))
        self.key_label = ttk.Label(right, text=self.t["no_entry"], font=("Consolas", 10, "bold"),
                                   wraplength=480)
        self.key_label.pack(anchor="w")

        ttk.Label(right, text=self.t["source"]).pack(anchor="w", pady=(8, 2))
        self.source_text = tk.Text(right, height=5, wrap="word", state="disabled",
                                   background="#f7f7f7")
        self.source_text.pack(fill="x")

        self.official_frame = ttk.Frame(right)
        if self.language == "zh":
            self.official_frame.pack(fill="x", pady=(8, 0))
            ttk.Label(self.official_frame, text=self.t["official"]).pack(anchor="w", pady=(0, 2))
            self.official_text = tk.Text(self.official_frame, height=5, wrap="word",
                                         state="disabled", background="#f3faf6")
            self.official_text.pack(fill="x")
        else:
            self.official_text = None

        ttk.Label(right, text=self.t["translation"]).pack(anchor="w", pady=(8, 2))
        self.translation = tk.Text(right, height=9, wrap="word", undo=True)
        self.translation.pack(fill="both", expand=True)
        self.note_label = ttk.Label(right, text="", foreground="#a60", wraplength=480,
                                    justify="left")
        self.note_label.pack(anchor="w", pady=(4, 0))

        buttons = ttk.Frame(right)
        buttons.pack(fill="x", pady=(8, 0))
        self.apply_button = ttk.Button(buttons, text=self.t["apply"],
                                       command=self.apply_current)
        self.apply_button.pack(side="left")
        self.official_button = ttk.Button(buttons, text=self.t["fill_official"],
                                          command=self.fill_official)
        self.official_button.pack(side="left", padx=4)
        ttk.Button(buttons, text=self.t["fill_source"], command=self.fill_source).pack(
            side="left")
        ttk.Button(buttons, text=self.t["clear"], command=self.clear_translation).pack(
            side="left", padx=4)

        foot = ttk.Frame(right)
        foot.pack(fill="x", pady=(8, 0))
        ttk.Button(foot, text=self.t["save"], command=self.save).pack(side="left")
        ttk.Button(foot, text=self.t["rescan"], command=self.rescan).pack(side="left", padx=4)
        ttk.Button(foot, text=self.t["close"], command=self.close).pack(side="right")

        self.top.protocol("WM_DELETE_WINDOW", self.close)
        self.file_label.configure(text=f"{self.t['file']}: {self.mod_path}")
        self.scan()
        self.top.bind("<Control-s>", lambda _event: self.save())

    # ---- scanning --------------------------------------------------------------------------

    def scan(self) -> None:
        self.entries = []
        seen: set[str] = set()

        def add(group: str, key: str, source: str, official: str = "",
                official_valid: bool = True, note: str = "") -> None:
            if key in seen:
                return
            seen.add(key)
            self.entries.append(Entry(group, key, source, official, official_valid, note))

        data_dir = game_data_dir()
        for dream in load_json(data_dir / "dreams.json", []) or []:
            if not isinstance(dream, dict) or not dream.get("id"):
                continue
            dream_id = str(dream["id"])
            title = str(dream.get("title", ""))
            key = f"dream.{dream_id}.title"
            add("dream", key, title, self._official(key),
                self.english.get(key) == title, self._stale_note(key, self.english.get(key) == title))
            for index, line in enumerate(dream.get("content") or []):
                if not isinstance(line, str) or not line.strip():
                    continue
                key = f"dream.{dream_id}.content.{index}"
                add("dream", key, line, self._official(key),
                    self.english.get(key) == line, self._stale_note(key, self.english.get(key) == line))
            hint = str(dream.get("philosophicalHint", "") or "")
            if hint:
                key = f"dream.{dream_id}.hint"
                add("dream", key, hint, self._official(key),
                    self.english.get(key) == hint, self._stale_note(key, self.english.get(key) == hint))

        for line in load_json(data_dir / "dialogue.json", []) or []:
            if not isinstance(line, dict) or not line.get("id"):
                continue
            line_id = str(line["id"])
            source = str(line.get("text", ""))
            key = f"npc_dialogue.{line_id}"
            template = dialogue_template(source)
            valid = self.english.get(key) == template
            note = self._stale_note(key, valid)
            if self.language == "zh" and not valid:
                note = (note + " " if note else "") + self.t["note_dialogue"]
            add("dialogue", key, source, self._official(key), valid, note)

        for item in load_json(data_dir / "equipment.json", []) or []:
            if not isinstance(item, dict) or item.get("id") is None:
                continue
            item_id = item["id"]
            name = str(item.get("name", ""))
            if name:
                add("equipment", f"mod.equipment.{item_id}.name", name)

        for family in load_json(data_dir / "monster_families.json", []) or []:
            if not isinstance(family, dict) or not family.get("familyName"):
                continue
            name = str(family["familyName"])
            name_key = f"monster.family.{name.lower()}"
            add("monster", f"mod.monster.{name}.name", name, self._official(name_key),
                self.english.get(name_key) == name,
                self._stale_note(name_key, self.english.get(name_key) == name))
            for tier in family.get("tiers") or []:
                if not isinstance(tier, dict) or not tier.get("name"):
                    continue
                tier_name = str(tier["name"])
                tier_key = f"monster.name.{localizable_tier_key(tier_name)}"
                add("monster", f"mod.monster.tier.{tier_name}.name", tier_name,
                    self._official(tier_key), self.english.get(tier_key) == tier_name,
                    self._stale_note(tier_key, self.english.get(tier_key) == tier_name))

        # Preserve keys a mod already added by hand; they stay editable here.
        for key in sorted(self.translations):
            if key not in seen:
                seen.add(key)
                self.entries.append(Entry("other", key, "", "", True, self.t["note_other"]))

        self.refresh_tree()

    def _official(self, key: str) -> str:
        if self.language != "zh":
            return ""
        value = self.reference.localization.get(key)
        return value if isinstance(value, str) and value.strip() else ""

    def _stale_note(self, key: str, valid: bool) -> str:
        if self.language == "zh" and self._official(key) and not valid:
            return self.t["note_stale"]
        return ""

    def status(self, entry: Entry) -> str:
        if self.translations.get(entry.key, "").strip():
            return "translated"
        if self.language != "zh":
            return "needed"
        if entry.official and entry.official_valid:
            return "official"
        return "needed"

    def wanted(self, entry: Entry) -> bool:
        choice = self.filter_var.get()
        status = self.status(entry)
        filters = self.t["filters"]
        if choice == filters[1]:  # All
            return True
        if choice == filters[2]:  # Has mod translation
            return status == "translated"
        if self.language == "zh" and choice == filters[3]:
            return status == "official"
        return status == "needed"

    def matches(self, entry: Entry) -> bool:
        needle = self.search_var.get().strip().casefold()
        if not needle:
            return True
        return needle in f"{entry.key} {entry.source} {entry.official}".casefold()

    def refresh_tree(self) -> None:
        if self.current is not None:
            self.apply_current(quiet=True)
        selected = self.current_iid
        self.tree.delete(*self.tree.get_children())
        self.entry_iids = {}
        counts = {"needed": 0, "translated": 0, "official": 0}
        for entry in self.entries:
            status = self.status(entry)
            if status == "needed" or status == "override":
                counts["needed"] += 1
            elif status == "translated":
                counts["translated"] += 1
            elif status == "official":
                counts["official"] += 1
        order = ["dream", "dialogue", "equipment", "npc", "monster", "other"]
        for group in order:
            entries = [e for e in self.entries if e.group == group and self.wanted(e) and self.matches(e)]
            if not entries:
                continue
            group_iid = f"g:{group}"
            self.tree.insert("", "end", iid=group_iid, text=self.t["group_counts"].format(
                name=self.t["groups"][group], count=len(entries)), open=True)
            for entry in entries:
                iid = f"e:{len(self.entry_iids)}"
                self.entry_iids[iid] = entry
                source = entry.source.replace("\n", " ")
                if len(source) > 90:
                    source = source[:87] + "..."
                self.tree.insert(group_iid, "end", iid=iid,
                                 text=entry.key,
                                 values=(self.t["status"][self.status(entry)], source))
                if entry.key == (self.current.key if self.current else None):
                    selected = iid
        self.count_label.configure(text=self.t["counts"].format(
            needed=counts["needed"], done=counts["translated"], official=counts["official"]))
        if selected and self.tree.exists(selected):
            self.tree.selection_set(selected)
            self.tree.see(selected)
        elif self.tree.get_children():
            first_group = self.tree.get_children()[0]
            children = self.tree.get_children(first_group)
            if children:
                self.tree.selection_set(children[0])
                self.tree.see(children[0])
            else:
                self.clear_editor()
        else:
            self.count_label.configure(text=self.t["empty"] + "  " + self.count_label.cget("text"))
            self.clear_editor()

    def on_select(self) -> None:
        selection = self.tree.selection()
        if not selection or selection[0] not in self.entry_iids:
            return
        if self.current is not None:
            self.apply_current(quiet=True)
        self.current_iid = selection[0]
        self.current = self.entry_iids[selection[0]]
        self.load_entry(self.current)

    def load_entry(self, entry: Entry) -> None:
        self.key_label.configure(text=entry.key)
        self.set_text(self.source_text, entry.source or self.t["src_blank"])
        if self.official_text is not None:
            self.set_text(self.official_text, entry.official or self.t["no_official"])
        self.translation.delete("1.0", "end")
        self.translation.insert("1.0", self.translations.get(entry.key, ""))
        self.note_label.configure(text=entry.note)
        self.official_button.configure(
            state="normal" if entry.official else "disabled")

    def clear_editor(self) -> None:
        self.current = None
        self.current_iid = None
        self.key_label.configure(text=self.t["no_entry"])
        self.set_text(self.source_text, "")
        if self.official_text is not None:
            self.set_text(self.official_text, "")
        self.translation.delete("1.0", "end")
        self.note_label.configure(text="")
        self.official_button.configure(state="disabled")

    @staticmethod
    def set_text(widget: tk.Text, text: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    # ---- editing ---------------------------------------------------------------------------

    def apply_current(self, quiet: bool = False) -> None:
        if self.current is None:
            return
        text = self.translation.get("1.0", "end-1c").strip()
        old = self.translations.get(self.current.key, "")
        if text:
            self.translations[self.current.key] = text
        else:
            self.translations.pop(self.current.key, None)
        if text != old:
            self.dirty = True
        if not quiet and self.current_iid and self.tree.exists(self.current_iid):
            self.tree.item(self.current_iid, values=(
                self.t["status"][self.status(self.current)],
                (self.current.source.replace("\n", " ")[:87] + "...")
                if len(self.current.source.replace("\n", " ")) > 90
                else self.current.source.replace("\n", " ")))

    def fill_official(self) -> None:
        if self.current and self.current.official:
            self.translation.delete("1.0", "end")
            self.translation.insert("1.0", self.current.official)
            self.apply_current()

    def fill_source(self) -> None:
        if self.current and self.current.source:
            self.translation.delete("1.0", "end")
            self.translation.insert("1.0", self.current.source)
            self.apply_current()

    def clear_translation(self) -> None:
        self.translation.delete("1.0", "end")
        self.apply_current()

    # ---- file ------------------------------------------------------------------------------

    def save(self) -> None:
        self.apply_current(quiet=True)
        try:
            backup = write_json(self.mod_path, dict(sorted(self.translations.items())))
        except OSError as error:
            messagebox.showerror(self.t["save_failed"], str(error), parent=self.top)
            return
        self.dirty = False
        message = self.t["saved"] + f"\n{self.mod_path}"
        if backup:
            message += f"\n{backup.name}"
        messagebox.showinfo(self.t["title"], message, parent=self.top)
        self.refresh_tree()

    def rescan(self) -> None:
        self.apply_current(quiet=True)
        self.scan()

    def close(self) -> None:
        self.apply_current(quiet=True)
        if self.dirty and not messagebox.askyesno(
                self.t["title"], self.t["discard"], parent=self.top):
            return
        self.top.destroy()
