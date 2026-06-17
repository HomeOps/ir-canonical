#!/usr/bin/env python3
"""Build the Flipper button-name -> canonical media-control map.

Flipper-IRDB has no enforced button naming, so one control appears under dozens
of spellings (VOL+, Vol_up, VOLUME_UP, VOL_^, TV_Vol+, ...). This walks a
Flipper-IRDB clone, normalizes every button name to a canonical media-control
name, and writes (into <out>/):

  canonical_controls.yaml  - the canonical vocabulary, grouped by category
  flipper_name_map.json    - { raw_name: canonical_name } for mapped names
  unmapped_names.txt        - the long tail, by frequency, for review

Usage:  python build_name_map.py <path-to-Flipper-IRDB-clone> [out-dir]

Mapping is ORDER-INDEPENDENT and rule-based, so unseen variants still map: a name
is tokenized (camelCase + separators + sign glyphs), each token is expanded
(vol->volume, +->up, ^->up, ffwd->fast_forward, ...), device/noise tokens are
dropped, and the resulting token SET is matched against CANON. Digits and inputs
(hdmi/video/aux + optional number) get dedicated handlers. The same `canonical()`
function is importable, so the codegen can normalize at YAML-generation time
instead of relying on a frozen lookup.
"""

import json
import os
import re
import sys
from collections import Counter

# --- token expansion: raw token -> canonical token(s) (space = multiple) -------
TOKEN_EXPAND = {
    # power
    "pwr": "power", "pow": "power", "powr": "power",
    # volume / channel
    "vol": "volume", "volm": "volume", "vlume": "volume",
    "ch": "channel", "chan": "channel", "chann": "channel", "chnl": "channel",
    "tune": "channel", "preset": "channel",
    # directions
    "dn": "down", "increase": "up", "decrease": "down", "inc": "up", "dec": "down",
    # transport
    "ffwd": "fast forward", "ff": "fast forward", "ffw": "fast forward",
    "fastforward": "fast forward", "fwd": "forward",
    "rew": "rewind", "rwd": "rewind", "rev": "rewind", "reverse": "rewind",
    "prev": "previous", "nxt": "next", "rec": "record",
    "playpause": "play pause",
    "channelup": "channel up", "channeldown": "channel down",
    "volumeup": "volume up", "volumedown": "volume down",
    "powertoggle": "power toggle", "poweron": "power on", "poweroff": "power off",
    "skipforward": "skip forward", "skipback": "skip back",
    # navigation
    "ok": "select", "sel": "select", "enter": "select",
    "cursor": "", "arrow": "", "navigate": "",
    "osd": "menu", "topmenu": "top menu",
    "return": "back", "esc": "back",
    "information": "info", "disp": "display",
    "epg": "guide",
    "setup": "settings", "setting": "settings", "config": "settings",
    "configuration": "settings", "set": "settings", "option": "settings",
    "options": "settings", "tools": "settings",
    "pageup": "page up", "pagedown": "page down",
    # a/v
    "subtitle": "subtitle", "subtitles": "subtitle", "subs": "subtitle",
    "sub": "subtitle", "cc": "subtitle", "teletext": "subtitle", "text": "subtitle",
    "txt": "subtitle", "ttx": "subtitle", "caption": "subtitle", "captions": "subtitle",
    "sound": "audio", "mts": "audio", "sap": "audio",
    "zm": "zoom", "wide": "aspect", "format": "aspect", "size": "aspect",
    "pic": "picture", "still": "freeze",
    "muting": "mute", "bt": "bluetooth", "ant": "antenna", "cbl": "cable",
    "grn": "green", "blu": "blue", "ylw": "yellow",
    # extras seen in the long tail
    "rpt": "repeat", "fav": "favorite", "favorites": "favorite",
    "favourite": "favorite", "favourites": "favorite", "again": "repeat",
    "srch": "search", "in": "input",
}

# Device-context / filler tokens to drop (so "TV_Vol+" -> volume_up). dvd/cd/vcr
# are dropped as prefixes (DVD_Menu -> menu); their input side is rarer than the
# menu/control side, an accepted trade-off.
DROP = {
    "tv", "dvd", "vcr", "cd", "bd", "stb", "amp", "amplifier", "receiver",
    "rcvr", "avr", "key", "btn", "button", "remote", "the", "my", "dvr",
}

CANON = {}        # frozenset(tokens) -> canonical
CATEGORY = {}     # canonical -> category


def reg(canonical, category, *token_sets):
    CATEGORY[canonical] = category
    for ts in token_sets:
        CANON[frozenset(ts.split())] = canonical


# power
reg("power_toggle", "power", "power", "standby", "power toggle")
reg("power_on", "power", "power on", "on")
reg("power_off", "power", "power off", "off")
# volume
reg("volume_up", "volume", "volume up")
reg("volume_down", "volume", "volume down")
reg("mute", "volume", "mute")
reg("mute_on", "volume", "mute on")
reg("mute_off", "volume", "mute off")
# channel
reg("channel_up", "channel", "channel up", "channel next")
reg("channel_down", "channel", "channel down", "channel previous")
reg("channel_last", "channel", "last", "recall", "flashback", "jump")
# transport
reg("play", "transport", "play")
reg("pause", "transport", "pause")
reg("play_pause", "transport", "play pause")
reg("stop", "transport", "stop")
reg("record", "transport", "record")
reg("rewind", "transport", "rewind")
reg("fast_forward", "transport", "fast forward", "forward")
reg("next", "transport", "next", "track up")
reg("previous", "transport", "previous", "track down")
reg("skip_forward", "transport", "skip forward", "skip")
reg("skip_back", "transport", "skip back", "skip backward")
reg("slow", "transport", "slow")
reg("eject", "transport", "eject", "open", "open close")
# navigation
reg("up", "navigation", "up")
reg("down", "navigation", "down")
reg("left", "navigation", "left")
reg("right", "navigation", "right")
reg("select", "navigation", "select")
reg("menu", "navigation", "menu", "top menu")
reg("back", "navigation", "back")
reg("exit", "navigation", "exit")
reg("home", "navigation", "home")
reg("info", "navigation", "info")
reg("display", "navigation", "display")
reg("guide", "navigation", "guide")
reg("settings", "navigation", "settings")
reg("page_up", "navigation", "page up")
reg("page_down", "navigation", "page down")
# colors
for _c in ("red", "green", "blue", "yellow", "white"):
    reg(_c, "color", _c)
# a/v
reg("source", "input", "source", "input", "input select")
reg("sleep", "av", "sleep", "sleep timer")
reg("zoom", "av", "zoom")
reg("zoom_in", "av", "zoom up")
reg("zoom_out", "av", "zoom down")
reg("aspect", "av", "aspect")
reg("pip", "av", "pip")
reg("subtitle", "av", "subtitle")
reg("audio", "av", "audio")
reg("picture", "av", "picture")
reg("surround", "av", "surround")
reg("freeze", "av", "freeze")
reg("bass_up", "av", "bass up")
reg("bass_down", "av", "bass down")
reg("treble_up", "av", "treble up")
reg("treble_down", "av", "treble down")
reg("repeat", "transport", "repeat")
reg("random", "transport", "random")
reg("shuffle", "transport", "shuffle")
reg("replay", "transport", "replay")
reg("scan", "channel", "scan")
reg("fast_forward", "transport", "scan forward")
reg("rewind", "transport", "scan back")
reg("mode", "av", "mode")
reg("angle", "av", "angle")
reg("aspect", "av", "format")
reg("three_d", "av", "3d")
reg("stereo", "av", "stereo")
reg("surround", "av", "surround")
reg("auto", "av", "auto")
reg("test", "av", "test")
reg("time", "av", "time")
reg("timer", "av", "timer")
reg("memory", "av", "memory")
reg("band", "input", "band")
# navigation / on-screen
reg("title", "navigation", "title")
reg("favorite", "navigation", "favorite")
reg("list", "navigation", "list")
reg("help", "navigation", "help")
reg("status", "navigation", "status")
reg("index", "navigation", "index")
reg("search", "navigation", "search")
# editing / numeric entry
reg("clear", "edit", "clear")
reg("reset", "edit", "reset")
reg("store", "edit", "store")
reg("delete", "edit", "delete")

# Curated subset of canonical controls to publish as {name, aliases}. These are
# the controls that matter for driving activities across TVs / AVRs / STBs /
# players — not the full 194 (inputs, colors, niche A/V keys are left out).
CORE = [
    "power_toggle", "power_on", "power_off",
    "volume_up", "volume_down", "mute",
    "channel_up", "channel_down",
    "play", "pause", "stop", "record",
    "rewind", "fast_forward", "next", "previous",
    "up", "down", "left", "right", "select", "back", "exit",
    "home", "menu", "info", "guide",
    "digit_0", "digit_1", "digit_2", "digit_3", "digit_4",
    "digit_5", "digit_6", "digit_7", "digit_8", "digit_9",
    "source",
]

INPUT_LABELS = {
    "hdmi", "video", "component", "composite", "vga", "dvi", "scart", "av",
    "aux", "usb", "pc", "antenna", "cable", "tuner", "phono", "bluetooth",
    "game", "sat",
}

# A standalone button whose whole name is one of these selects that source
# (CD, DVD, TV, TAPE, FM …). They're dropped as *prefix* tokens (DVD_Menu -> menu),
# so this is checked before dropping, only when the name is the bare label.
SOURCE_LABELS = INPUT_LABELS | {
    "tv", "cd", "dvd", "vcr", "tape", "ld", "md", "dvr", "radio", "fm", "am",
}


def _tokens(name, drop=True):
    s = name.strip()
    s = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", s)          # camelCase -> spaces
    s = s.lower()
    s = s.replace(">>", " forward ").replace("<<", " back ")
    s = s.replace("^", " up ")
    s = re.sub(r"\+", " up ", s)
    s = re.sub(r"-(?![a-z])", " down ", s)               # trailing/standalone minus
    s = re.sub(r"[<>\[\]()*#~&!?:;\"'`=]", " ", s)        # drop stray symbols
    s = re.sub(r"[/_.,\-]", " ", s)                       # separators
    out = []
    for tok in s.split():
        exp = TOKEN_EXPAND.get(tok, tok)
        for piece in exp.split():
            if piece and (not drop or piece not in DROP):
                out.append(piece)
    return out


# Labels where a small index is a real discrete input (HDMI 1, AV 2, …). Others
# (tuner/cable/sat/antenna/phono) carry preset/frequency numbers, not inputs.
NUMBERED_INPUTS = {
    "hdmi", "video", "av", "aux", "component", "composite", "pc", "vga",
    "dvi", "scart", "game",
}


def _input_canonical(tokens):
    digits = [t for t in tokens if t.isdigit()]
    rest = [t for t in tokens if not t.isdigit()]
    if len(digits) > 1:
        return None
    d = digits[0] if digits else None
    if d is not None and len(d) != 1:      # only single-digit input indices
        return None
    if rest == ["input"]:
        return f"input_{d}" if d else None
    if len(rest) == 1 and rest[0] in INPUT_LABELS:
        lab = rest[0]
        if d:
            return f"input_{lab}_{d}" if lab in NUMBERED_INPUTS else None
        return f"input_{lab}"
    return None


def canonical(name):
    """Map a raw Flipper button name to a canonical control, or None."""
    raw = name.strip()
    if not raw:
        return None
    if re.fullmatch(r"\d", raw):
        return f"digit_{raw}"
    if raw == "10":
        return "digit_10"
    # A bare source label (CD, DVD, TV, …) selects that source.
    nodrop = _tokens(name, drop=False)
    if len(nodrop) == 1 and nodrop[0] in SOURCE_LABELS:
        return f"input_{nodrop[0]}"
    tokens = _tokens(name)
    if not tokens:
        return None
    hit = CANON.get(frozenset(tokens))
    if hit:
        return hit
    return _input_canonical(tokens)


_NAME_RE = re.compile(r"^name:\s*(.+?)\s*$")


def tally(clone_dir):
    counts = Counter()
    for root, _dirs, files in os.walk(clone_dir):
        if ".git" in root.split(os.sep):
            continue
        for fn in files:
            if not fn.endswith(".ir"):
                continue
            path = os.path.join(root, fn)
            with open(path, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    m = _NAME_RE.match(line)
                    if m:
                        counts[m.group(1)] += 1
    return counts


def _title(canon):
    """canonical id -> human folder name: volume_up -> Volume_Up, source -> Source."""
    return "_".join(p.capitalize() for p in canon.split("_"))


def _category_of(canon):
    if canon.startswith("digit_"):
        return "digit"
    if canon.startswith("input_"):
        return "input"
    return CATEGORY.get(canon, "other")


def main(argv):
    if not argv:
        raise SystemExit("usage: build_name_map.py <Flipper-IRDB-clone> [out-dir]")
    clone = argv[0]
    out = argv[1] if len(argv) > 1 else os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(out, exist_ok=True)

    counts = tally(clone)
    mapping, unmapped = {}, []
    mapped_occ = total_occ = 0
    vocab = {}      # category -> set(canonical)
    for raw, n in counts.items():
        total_occ += n
        canon = canonical(raw)
        if canon:
            mapping[raw] = canon
            mapped_occ += n
            vocab.setdefault(_category_of(canon), set()).add(canon)
        else:
            unmapped.append((n, raw))

    # flipper_name_map.json — keys are CASE-FOLDED. Flipper files disagree on
    # casing (e.g. "0/AV" vs "0/av"), and canonical() is case-insensitive, so the
    # lookup map must be too: fold keys to lower-case and dedupe. (Keeping both
    # casings makes valid-but-fragile JSON that case-insensitive parsers — e.g.
    # PowerShell ConvertFrom-Json — reject.) Conflicting values would be a bug.
    folded, conflicts = {}, 0
    for raw, canon in mapping.items():
        key = raw.lower()
        if key in folded and folded[key] != canon:
            conflicts += 1
        folded[key] = canon
    with open(os.path.join(out, "flipper_name_map.json"), "w", encoding="utf-8") as fh:
        json.dump(dict(sorted(folded.items())), fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    # unmapped_names.txt — by frequency desc
    unmapped.sort(reverse=True)
    with open(os.path.join(out, "unmapped_names.txt"), "w", encoding="utf-8") as fh:
        for n, raw in unmapped:
            fh.write(f"{n}\t{raw}\n")

    # canonical_controls.yaml — vocabulary grouped by category
    order = ["power", "volume", "channel", "transport", "navigation",
             "input", "digit", "color", "av", "other"]
    with open(os.path.join(out, "canonical_controls.yaml"), "w", encoding="utf-8") as fh:
        fh.write("# Canonical media-control vocabulary "
                 "(generated by build_name_map.py).\n")
        fh.write("# The mapping logic in canonical() is the source of truth.\n")
        for cat in order:
            if cat not in vocab:
                continue
            fh.write(f"{cat}:\n")
            for canon in sorted(vocab[cat]):
                fh.write(f"  - {canon}\n")

    # controls/<Name>/aliases.json — the human-editable curated tree, one folder
    # per CORE control holding a JSON list of its spellings. Seeded from the DB
    # (most-frequent spelling first, case-insensitively deduped) and NEVER
    # overwritten once it exists, so hand edits survive a re-run.
    inv = {}
    for raw, n in counts.items():
        c = canonical(raw)
        if c:
            inv.setdefault(c, Counter())[raw] += n
    controls_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "controls")
    created = preserved = 0
    for name in CORE:
        folded = {}      # lower -> [best_raw, best_count, total_count]
        for raw, n in inv.get(name, Counter()).items():
            entry = folded.get(raw.lower())
            if entry is None:
                folded[raw.lower()] = [raw, n, n]
            else:
                entry[2] += n
                if n > entry[1]:
                    entry[0], entry[1] = raw, n
        aliases = [e[0] for e in sorted(folded.values(), key=lambda e: -e[2])]
        folder = os.path.join(controls_dir, _title(name))
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, "aliases.json")
        if os.path.exists(path):
            preserved += 1
            continue
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(aliases, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        created += 1

    distinct = len(counts)
    print(f"distinct names      : {distinct}")
    print(f"mapped distinct     : {len(mapping)} ({len(mapping) / distinct:.1%})")
    print(f"case-folded keys    : {len(folded)} (collapsed {len(mapping) - len(folded)}; conflicts {conflicts})")
    print(f"occurrences total   : {total_occ}")
    print(f"occurrences mapped  : {mapped_occ} ({mapped_occ / total_occ:.1%})")
    print(f"canonical controls  : {sum(len(v) for v in vocab.values())}")
    print(f"unmapped distinct   : {len(unmapped)}")
    print(f"controls tree       : {created} created, {preserved} preserved -> {controls_dir}")
    print(f"wrote -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
