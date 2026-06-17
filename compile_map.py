#!/usr/bin/env python3
"""Compile the controls/ tree into a flat {alias: canonical} JSON for fast load.

`controls/` is the human-curated source of truth (one folder per control, an
`aliases.json` inside). This flattens it to a single compact JSON dict with
lower-cased keys, so a consumer — e.g. the ESPHome codegen, which bakes this at
Docker build time — loads one small file and resolves a button with
`canonical = MAP.get(name.lower())` instead of walking the tree at runtime.

Usage:  python compile_map.py [controls-dir] [out.json]

Exits non-zero if two controls claim the same alias (a curation bug).
"""

import json
import os
import sys


def compile_tree(controls_dir):
    """Return ({alias_lower: canonical}, conflicts) from a controls/ tree."""
    mapping, conflicts = {}, []
    for entry in sorted(os.listdir(controls_dir)):
        aliases_path = os.path.join(controls_dir, entry, "aliases.json")
        if not os.path.isfile(aliases_path):
            continue
        canonical = entry.lower()                       # Volume_Up -> volume_up
        with open(aliases_path, encoding="utf-8") as fh:
            aliases = json.load(fh)
        for name in [canonical, *aliases]:
            key = name.lower()
            if key in mapping and mapping[key] != canonical:
                conflicts.append((key, mapping[key], canonical))
            mapping[key] = canonical
    return mapping, conflicts


def main(argv):
    here = os.path.dirname(os.path.abspath(__file__))
    controls = argv[0] if argv else os.path.join(here, "controls")
    out = argv[1] if len(argv) > 1 else os.path.join(here, "control_map.json")

    mapping, conflicts = compile_tree(controls)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(dict(sorted(mapping.items())), fh, ensure_ascii=False,
                  separators=(",", ":"))     # compact: smaller + faster to load

    for key, first, second in conflicts:
        print(f"conflict: alias {key!r} claimed by both {first} and {second}",
              file=sys.stderr)
    controls_n = sum(1 for e in os.scandir(controls) if e.is_dir())
    print(f"compiled {len(mapping)} aliases from {controls_n} controls -> {out}")
    return 1 if conflicts else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
