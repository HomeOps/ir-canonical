"""Hatchling build hook: bake controls/ -> control_map.json at build time.

Every wheel/sdist build regenerates the flat {alias: canonical} map from the
curated controls/ tree and includes it as package data, so installing the
library gives consumers an instant, prebuilt lookup (no tree walk at runtime).
"""

import json
import os

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    PLUGIN_NAME = "custom"

    def initialize(self, version, build_data):
        pkg = os.path.join(self.root, "src", "ir_canonical")
        controls = os.path.join(pkg, "controls")
        mapping = {}
        for entry in sorted(os.listdir(controls)):
            aliases_path = os.path.join(controls, entry, "aliases.json")
            if not os.path.isfile(aliases_path):
                continue
            canonical = entry.lower()
            with open(aliases_path, encoding="utf-8") as fh:
                aliases = json.load(fh)
            for name in [canonical, *aliases]:
                mapping[name.lower()] = canonical
        out = os.path.join(pkg, "control_map.json")
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(dict(sorted(mapping.items())), fh, ensure_ascii=False,
                      separators=(",", ":"))
        # control_map.json is git-ignored (generated); force it into the build.
        build_data.setdefault("force_include", {})[out] = "ir_canonical/control_map.json"
        self.app.display_info(f"baked control_map.json: {len(mapping)} aliases")
