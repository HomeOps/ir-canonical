"""Compile the controls/ tree into a flat {alias: canonical} lookup."""

import json
import os


def compile_controls(controls_dir):
    """Return ({alias_lower: canonical}, conflicts) from a controls/ tree.

    Each ``controls/<Name>/aliases.json`` is a JSON list of spellings; the folder
    name (lower-cased) is the canonical id. Keys are lower-cased so lookups are
    case-insensitive. ``conflicts`` lists any alias claimed by two controls.
    """
    mapping, conflicts, canon_ids = {}, [], []
    for entry in sorted(os.listdir(controls_dir)):
        aliases_path = os.path.join(controls_dir, entry, "aliases.json")
        if not os.path.isfile(aliases_path):
            continue
        canonical = entry.lower()
        canon_ids.append(canonical)
        with open(aliases_path, encoding="utf-8") as fh:
            aliases = json.load(fh)
        for name in aliases:
            key = name.lower()
            if key in mapping and mapping[key] != canonical:
                conflicts.append((key, mapping[key], canonical))
            mapping[key] = canonical
    # A canonical id always resolves to itself, even if some alias collides with it.
    for canonical in canon_ids:
        mapping[canonical] = canonical
    return mapping, conflicts
