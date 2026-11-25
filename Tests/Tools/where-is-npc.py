#!/usr/bin/env python3
"""Print where the NPCs are in a single-player save, so "I lost that person" is one command.

NPCs move between locations and some die, and there is no in-game directory of who is where. This reads
the newest save, or the one named, and prints each match with its location and whether it is dead.

    python where-is-npc.py                  # everyone
    python where-is-npc.py ursula           # names containing "ursula", case-insensitive
    python where-is-npc.py --save ll.json quest

The save is the same file the game reads, so what this prints is where the world actually has them.
Nothing is written.
"""

import argparse
import glob
import json
import os
import sys

SAVE_GLOB = os.path.join("bin", "Debug", "net8.0", "saves", "*.json")


def newest_save(explicit):
    if explicit:
        return explicit
    candidates = glob.glob(SAVE_GLOB)
    if not candidates:
        sys.exit(f"no save found under {SAVE_GLOB}; run the game once")
    return max(candidates, key=os.path.getmtime)


def name_of(npc):
    return npc.get("name2") or npc.get("name") or "?"


def main():
    parser = argparse.ArgumentParser(description="Where is that NPC?")
    parser.add_argument("pattern", nargs="?", default="", help="part of a name, case-insensitive")
    parser.add_argument("--save", help="an explicit save file instead of the newest")
    args = parser.parse_args()

    path = newest_save(args.save)
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)

    npcs = data.get("npCs") or []
    if not npcs:
        sys.exit(f"{os.path.basename(path)} carries no NPCs")

    wanted = args.pattern.lower()
    rows = []
    for npc in npcs:
        name = name_of(npc)
        if wanted and wanted not in name.lower():
            continue
        rows.append((
            name,
            npc.get("location") or npc.get("currentLocation") or "?",
            bool(npc.get("isDead") or npc.get("isPermaDead")),
        ))

    if not rows:
        sys.exit(f"no NPC matches {args.pattern!r} in {os.path.basename(path)}")

    width = max(len(name) for name, _, _ in rows)
    print(f"{os.path.basename(path)}: {len(rows)} of {len(npcs)} NPCs")
    for name, location, dead in sorted(rows):
        print(f"  {name:<{width}}  {location:<24}{'  DEAD' if dead else ''}")


if __name__ == "__main__":
    main()
