"""Structured record editor for the GameData JSON files.

The G editor has one hand-written form per data source. This module keeps a
single type-aware form engine: each file is a list of records or a key/value
dictionary, scalar fields get typed widgets, and nested lists or objects are
edited as JSON in a text box. Everything is written through the same backup
helper, so a mistaken save never destroys the previous file.
"""

from __future__ import annotations

import json
import re
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Any

from .common import GAME_DATA_FILES, export_defaults, game_data_dir, load_json, write_json

CAMEL = re.compile(r"[A-Z]+(?=[A-Z][a-z]|$)|[A-Z]?[a-z]+|[0-9]+")


def label(key: str) -> str:
    words = CAMEL.findall(key)
    return " ".join(word.capitalize() for word in words) if words else key


def record_title(record: Any, index: int) -> str:
    if isinstance(record, dict):
        for key in ("name", "familyName", "title", "id"):
            value = record.get(key)
            if isinstance(value, str) and value:
                return value
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return f"{index + 1}. {value}"
        return f"{index + 1}. {label(next(iter(record), 'record'))}"
    return f"{index + 1}. {record}"


class GameDataFormsWindow:
    def __init__(self, parent: tk.Misc):
        self.top = tk.Toplevel(parent)
        self.top.title("GameData editor")
        self.top.geometry("1180x760")
        self.top.transient(parent)

        self.data: Any = None
        self.path = None
        self.mode = "list"
        self.index: int | None = None
        self.fields: dict[str, Any] = {}
        self.field_widgets: dict[str, Any] = {}
        self.record_keys: list[str] = []

        body = ttk.Panedwindow(self.top, orient="horizontal")
        body.pack(fill="both", expand=True, padx=8, pady=8)
        left = ttk.Frame(body)
        body.add(left, weight=1)
        self.files = tk.Listbox(left, exportselection=False)
        self.files.pack(fill="both", expand=True)
        for name, filename in GAME_DATA_FILES:
            self.files.insert("end", f"{name}  ·  {filename}")
        self.files.bind("<<ListboxSelect>>", lambda _event: self.load_file())
        ttk.Button(left, text="Export defaults", command=self.export_defaults).pack(fill="x", pady=(6, 0))

        right = ttk.Frame(body)
        body.add(right, weight=5)
        self.path_label = ttk.Label(right, text="", foreground="#555")
        self.path_label.pack(anchor="w")
        split = ttk.Panedwindow(right, orient="horizontal")
        split.pack(fill="both", expand=True, pady=(6, 6))

        records_frame = ttk.Frame(split)
        split.add(records_frame, weight=1)
        self.records = tk.Listbox(records_frame, exportselection=False)
        self.records.pack(fill="both", expand=True)
        self.records.bind("<<ListboxSelect>>", lambda _event: self.show_record())
        record_bar = ttk.Frame(records_frame)
        record_bar.pack(fill="x", pady=(4, 0))
        ttk.Button(record_bar, text="Add", command=self.add_record).pack(side="left")
        ttk.Button(record_bar, text="Clone", command=self.clone_record).pack(side="left", padx=4)
        ttk.Button(record_bar, text="Delete", command=self.delete_record).pack(side="left")

        form_holder = ttk.Frame(split)
        split.add(form_holder, weight=4)
        self.canvas = tk.Canvas(form_holder, highlightthickness=0)
        scroll = ttk.Scrollbar(form_holder, orient="vertical", command=self.canvas.yview)
        self.form = ttk.Frame(self.canvas)
        self.form.bind("<Configure>", lambda _event: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.form, anchor="nw")
        self.canvas.configure(yscrollcommand=scroll.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        bar = ttk.Frame(right)
        bar.pack(fill="x")
        ttk.Button(bar, text="Apply form", command=self.apply_form).pack(side="left")
        ttk.Button(bar, text="Save file (backup)", command=self.save_file).pack(side="left", padx=6)
        ttk.Button(bar, text="Reload file", command=self.load_file).pack(side="left")
        ttk.Button(bar, text="Close", command=self.top.destroy).pack(side="right")

        self.files.selection_set(0)
        self.load_file()

    # ---- file and records ------------------------------------------------------------------------

    def selected_file(self):
        selection = self.files.curselection()
        return GAME_DATA_FILES[selection[0]] if selection else None

    def load_file(self) -> None:
        selected = self.selected_file()
        if selected is None:
            return
        _name, filename = selected
        self.path = game_data_dir() / filename
        self.path_label.configure(text=str(self.path))
        self.data = load_json(self.path, [] if filename != "balance.json" else {})
        self.mode = "dict" if isinstance(self.data, dict) else "list"
        self.index = None
        self.refresh_records()

    def refresh_records(self) -> None:
        self.records.delete(0, "end")
        if self.mode == "list":
            for index, record in enumerate(self.data):
                self.records.insert("end", record_title(record, index))
        elif isinstance(self.data, dict):
            for key, value in self.data.items():
                preview = value if not isinstance(value, (dict, list)) else type(value).__name__
                self.records.insert("end", f"{label(key)} = {preview}")
        if self.records.size():
            self.records.selection_set(0)
            self.show_record()
        else:
            self.clear_form()

    def clear_form(self) -> None:
        for child in self.form.winfo_children():
            child.destroy()
        self.fields = {}
        self.field_widgets = {}

    def show_record(self) -> None:
        selection = self.records.curselection()
        if not selection:
            self.clear_form()
            return
        self.index = selection[0]
        self.clear_form()
        if self.mode == "list":
            record = self.data[self.index]
            if not isinstance(record, dict):
                self.add_field("value", "Value", record)
                return
            for key, value in record.items():
                self.add_field(key, label(key), value)
        else:
            key = list(self.data)[self.index]
            self.add_field(key, label(key), self.data[key])

    # ---- form widgets ----------------------------------------------------------------------------

    def add_field(self, key: str, title: str, value: Any) -> None:
        row = ttk.Frame(self.form, padding=(0, 3))
        row.pack(fill="x", anchor="w")
        ttk.Label(row, text=title, width=28).pack(side="left", anchor="n")
        if isinstance(value, bool):
            variable = tk.BooleanVar(value=value)
            widget = ttk.Checkbutton(row, variable=variable)
            widget.pack(side="left")
            self.field_widgets[key] = ("bool", variable)
        elif isinstance(value, (dict, list)) or value is None:
            widget = tk.Text(row, height=4, width=70, wrap="word")
            widget.insert("1.0", json.dumps(value, ensure_ascii=False, indent=2))
            widget.pack(side="left", fill="x", expand=True)
            self.field_widgets[key] = ("json", widget)
        elif isinstance(value, str) and (len(value) > 80 or "\n" in value):
            widget = tk.Text(row, height=4, width=70, wrap="word")
            widget.insert("1.0", value)
            widget.pack(side="left", fill="x", expand=True)
            self.field_widgets[key] = ("str", widget)
        else:
            variable = tk.StringVar(value=str(value))
            widget = ttk.Entry(row, textvariable=variable, width=70)
            widget.pack(side="left", fill="x", expand=True)
            kind = "int" if isinstance(value, int) and not isinstance(value, bool) else \
                "float" if isinstance(value, float) else "str"
            self.field_widgets[key] = (kind, variable, value)

    def read_field(self, key: str) -> Any:
        kind, widget, *rest = self.field_widgets[key]
        if kind == "bool":
            return bool(widget.get())
        if kind == "json":
            text = widget.get("1.0", "end-1c")
            try:
                return json.loads(text)
            except json.JSONDecodeError as error:
                raise ValueError(f"{label(key)}: invalid JSON: {error}") from error
        if kind == "str" and isinstance(widget, tk.Text):
            return widget.get("1.0", "end-1c")
        raw = widget.get()
        if kind == "int":
            try:
                return int(raw)
            except ValueError as error:
                raise ValueError(f"{label(key)}: expected an integer") from error
        if kind == "float":
            try:
                return float(raw)
            except ValueError as error:
                raise ValueError(f"{label(key)}: expected a number") from error
        return raw

    def apply_form(self) -> bool:
        if self.index is None:
            return False
        try:
            values = {key: self.read_field(key) for key in self.field_widgets}
        except ValueError as error:
            messagebox.showerror("Invalid value", str(error), parent=self.top)
            return False
        if self.mode == "list":
            self.data[self.index] = values if len(values) != 1 or "value" not in values else values["value"]
        else:
            old_key = list(self.data)[self.index]
            self.data[old_key] = values[old_key] if old_key in values else next(iter(values.values()))
        self.refresh_records()
        return True

    # ---- record operations -----------------------------------------------------------------------

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

    def add_record(self) -> None:
        if self.mode == "list":
            sample = next((record for record in self.data if isinstance(record, dict)), None)
            self.data.append({key: self.blank_like(value) for key, value in sample.items()}
                             if isinstance(sample, dict) else {})
        else:
            key = simpledialog.askstring("Add value", "Key:", parent=self.top)
            if not key or key in self.data:
                return
            self.data[key] = 0
        self.refresh_records()
        if self.records.size():
            self.records.selection_clear(0, "end")
            self.records.selection_set(self.records.size() - 1)
            self.show_record()

    def clone_record(self) -> None:
        selection = self.records.curselection()
        if not selection or self.mode != "list":
            return
        import copy
        self.data.append(copy.deepcopy(self.data[selection[0]]))
        self.refresh_records()

    def delete_record(self) -> None:
        selection = self.records.curselection()
        if not selection:
            return
        index = selection[0]
        if not messagebox.askyesno("Delete record", "Delete the selected record?", parent=self.top):
            return
        if self.mode == "list":
            del self.data[index]
        else:
            del self.data[list(self.data)[index]]
        self.refresh_records()

    # ---- saving -----------------------------------------------------------------------------------

    def save_file(self) -> None:
        if self.path is None:
            return
        if not self.apply_form() and self.index is not None:
            return
        try:
            backup = write_json(self.path, self.data)
        except OSError as error:
            messagebox.showerror("Save failed", str(error), parent=self.top)
            return
        message = f"Saved {self.path.name}."
        if backup:
            message += f"\nBackup: {backup.name}"
        messagebox.showinfo("Saved", message, parent=self.top)

    def export_defaults(self) -> None:
        if not messagebox.askyesno(
                "Export defaults", "Overwrite GameData with the built-in defaults?", parent=self.top):
            return
        try:
            folder = export_defaults()
        except Exception as error:
            messagebox.showerror("Export failed", str(error), parent=self.top)
            return
        self.load_file()
        messagebox.showinfo("Export defaults", f"Exported to {folder}", parent=self.top)
