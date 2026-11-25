"""Built-in equipment picker for the Python editor.

The game's C# editor copies a template from EquipmentDatabase. The Python
editor ships the exported built-in templates with the tool, so adding or
equipping an item by ID does not require a running game or a GameData export.
"""

from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import ttk

TEMPLATES = Path(__file__).with_name("equipment_templates.json")

SLOT_NAMES = {
    "Head": "Head", "Body": "Body", "Arms": "Arms", "Hands": "Hands",
    "Legs": "Legs", "Feet": "Feet", "Waist": "Waist", "Neck": "Neck",
    "Face": "Face", "Cloak": "Cloak", "LFinger": "Left finger",
    "RFinger": "Right finger", "MainHand": "Main hand", "OffHand": "Off hand",
}

RARITY_NAMES = {0: "Common", 1: "Uncommon", 2: "Rare", 3: "Epic", 4: "Legendary", 5: "Artifact"}


def load_templates() -> list[dict]:
    return json.loads(TEMPLATES.read_text(encoding="utf-8"))


def to_inventory(row: dict) -> dict:
    return {
        "name": row["nameEn"],
        "value": row["value"],
        "type": row["type"],
        "attack": row["attack"],
        "armor": row["armor"],
        "strength": row["strength"],
        "dexterity": row["dexterity"],
        "wisdom": row["wisdom"],
        "defence": row["defence"],
        "shieldBonus": row["shieldBonus"],
        "blockChance": row["blockChance"],
        "hp": row["hp"],
        "mana": row["mana"],
        "charisma": row["charisma"],
        "agility": row["agility"],
        "stamina": row["stamina"],
        "minLevel": row["minLevel"],
        "rarity": row["rarity"],
        "family": "",
        "isCursed": False,
        "isIdentified": True,
        "shop": False,
        "dungeon": False,
        "description": [],
    }


class ItemPicker:
    def __init__(self, parent: tk.Misc, language: str = "en", need_slot: bool = False):
        self.language = language
        self.need_slot = need_slot
        self.rows = load_templates()
        self.result: dict | None = None
        self.top = tk.Toplevel(parent)
        self.top.title("Choose a built-in item" if language == "en" else "选择内置物品")
        self.top.geometry("900x620")
        self.top.transient(parent)
        top = ttk.Frame(self.top, padding=8)
        top.pack(fill="both", expand=True)
        search_bar = ttk.Frame(top)
        search_bar.pack(fill="x")
        ttk.Label(search_bar, text="Search:" if language == "en" else "搜索：").pack(side="left")
        self.search = ttk.Entry(search_bar, width=42)
        self.search.pack(side="left", padx=6)
        self.search.bind("<KeyRelease>", lambda _event: self.refresh())
        ttk.Label(search_bar, text="ID:" if language == "en" else "ID：").pack(side="left", padx=(12, 0))
        self.id_box = ttk.Entry(search_bar, width=10)
        self.id_box.pack(side="left", padx=6)
        self.id_box.bind("<Return>", lambda _event: self.pick_id())
        ttk.Button(search_bar, text="Pick ID" if language == "en" else "按 ID 选择",
                   command=self.pick_id).pack(side="left")

        frame = ttk.Frame(top)
        frame.pack(fill="both", expand=True, pady=8)
        self.list = tk.Listbox(frame, exportselection=False)
        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.list.yview)
        self.list.configure(yscrollcommand=scroll.set)
        self.list.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.list.bind("<Double-Button-1>", lambda _event: self.pick())
        self.list.bind("<Return>", lambda _event: self.pick())

        bar = ttk.Frame(top)
        bar.pack(fill="x")
        ttk.Button(bar, text="Add" if language == "en" else "添加",
                   command=self.pick).pack(side="left")
        ttk.Button(bar, text="Cancel" if language == "en" else "取消",
                   command=self.top.destroy).pack(side="right")
        self.refresh()
        self.top.grab_set()
        self.top.wait_window()

    def refresh(self) -> None:
        needle = self.search.get().strip().lower()
        self.list.delete(0, "end")
        self.visible = []
        for row in self.rows:
            name = row["nameZh"] if self.language == "zh" else row["nameEn"]
            haystack = f"{row['id']} {row['nameEn']} {row['nameZh']} {row['slot']}".lower()
            if needle and needle not in haystack:
                continue
            self.visible.append(row)
            rarity = RARITY_NAMES.get(row["rarity"], row["rarity"])
            self.list.insert("end", f"{row['id']:>6}  {name}  [{SLOT_NAMES.get(row['slot'], row['slot'])}]  "
                                     f"{rarity}  Lv.{row['minLevel']}  {row['value']}g")

    def pick(self) -> None:
        selection = self.list.curselection()
        if not selection:
            return
        self.result = self.visible[selection[0]]
        self.top.destroy()

    def pick_id(self) -> None:
        try:
            wanted = int(self.id_box.get().strip())
        except ValueError:
            return
        for row in self.rows:
            if row["id"] == wanted:
                self.result = row
                self.top.destroy()
                return
        self.id_box.configure(foreground="#b91c1c")


def pick_item(parent: tk.Misc, language: str = "en", need_slot: bool = False) -> dict | None:
    return ItemPicker(parent, language, need_slot).result
