#!/usr/bin/env python3
"""CLI wrapper: compile the controls/ tree to a flat {alias: canonical} JSON.

The library bakes this at build time (see hatch_build.py); this is for ad-hoc
regeneration / inspection.

Usage:  python compile_cli.py [controls-dir] [out.json]
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
from ir_canonical.compile import compile_controls  # noqa: E402


def main(argv):
    here = os.path.dirname(os.path.abspath(__file__))
    controls = argv[0] if argv else os.path.join(here, "src", "ir_canonical", "controls")
    out = argv[1] if len(argv) > 1 else os.path.join(here, "src", "ir_canonical", "control_map.json")
    mapping, conflicts = compile_controls(controls)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(dict(sorted(mapping.items())), fh, ensure_ascii=False, separators=(",", ":"))
    for key, first, second in conflicts:
        print(f"conflict: alias {key!r} claimed by both {first} and {second}", file=sys.stderr)
    print(f"compiled {len(mapping)} aliases -> {out}")
    return 1 if conflicts else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
