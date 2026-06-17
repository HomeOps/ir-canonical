"""Canonical media-control vocabulary + Flipper-IRDB name→canonical mapping.

Two ways to resolve a button name to a canonical control id:

  resolve(name)    curated lookup via the bundled controls/ tree (fast, exact) —
                   the human-maintained source of truth, baked to control_map.json
                   at build time.
  canonical(name)  the broad rule-based engine — maps spellings the curated tree
                   hasn't enumerated yet (and the full vocabulary, not just CORE).

Both are case-insensitive. `MAP` is the compiled {alias: canonical} dict.
"""

import functools
import json
import os

from .normalize import CORE, canonical

__all__ = ["canonical", "resolve", "MAP", "CORE", "controls_dir", "__version__"]

try:
    from importlib.metadata import version as _pkg_version

    __version__ = _pkg_version("homeops-ir-canonical")
except Exception:                       # not installed (e.g. running from source)
    __version__ = "0.0.0"

_HERE = os.path.dirname(os.path.abspath(__file__))


def controls_dir():
    """Path to the bundled curated controls/ tree."""
    return os.path.join(_HERE, "controls")


@functools.lru_cache(maxsize=1)
def _load_map():
    # Prefer the compiled map baked at build time; fall back to compiling the
    # bundled tree (e.g. an editable install before a build ran).
    baked = os.path.join(_HERE, "control_map.json")
    if os.path.exists(baked):
        with open(baked, encoding="utf-8") as fh:
            return json.load(fh)
    from .compile import compile_controls
    return compile_controls(controls_dir())[0]


MAP = _load_map()


def resolve(name):
    """Curated lookup: alias → canonical control id via the controls tree, or None."""
    return MAP.get(name.lower())
