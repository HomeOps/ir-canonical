"""Rule-based, order-independent Flipper button-name → canonical normalizer.

One control appears in Flipper-IRDB under dozens of spellings (VOL+, Vol_up,
VOLUME_UP, VOL_^, TV_Vol+, ...). `canonical(name)` tokenizes a name (camelCase +
separators + sign glyphs), expands each token (vol→volume, +→up, ffwd→
fast_forward, ...), drops device/filler tokens, and matches the resulting token
SET against the canonical table — so spellings not yet seen still resolve.
"""

import re

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
reg("rewind", "transport", "rewind", "scan back")
reg("fast_forward", "transport", "fast forward", "forward", "scan forward")
reg("next", "transport", "next", "track up")
reg("previous", "transport", "previous", "track down")
reg("skip_forward", "transport", "skip forward", "skip")
reg("skip_back", "transport", "skip back", "skip backward")
reg("slow", "transport", "slow")
reg("eject", "transport", "eject", "open", "open close")
reg("repeat", "transport", "repeat")
reg("random", "transport", "random")
reg("shuffle", "transport", "shuffle")
reg("replay", "transport", "replay")
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
reg("title", "navigation", "title")
reg("favorite", "navigation", "favorite")
reg("list", "navigation", "list")
reg("help", "navigation", "help")
reg("status", "navigation", "status")
reg("index", "navigation", "index")
reg("search", "navigation", "search")
# colors
for _c in ("red", "green", "blue", "yellow", "white"):
    reg(_c, "color", _c)
# input
reg("source", "input", "source", "input", "input select")
reg("band", "input", "band")
# channel scan
reg("scan", "channel", "scan")
# a/v
reg("sleep", "av", "sleep", "sleep timer")
reg("zoom", "av", "zoom")
reg("zoom_in", "av", "zoom up")
reg("zoom_out", "av", "zoom down")
reg("aspect", "av", "aspect", "format")
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
reg("mode", "av", "mode")
reg("angle", "av", "angle")
reg("three_d", "av", "3d")
reg("stereo", "av", "stereo")
reg("auto", "av", "auto")
reg("test", "av", "test")
reg("time", "av", "time")
reg("timer", "av", "timer")
reg("memory", "av", "memory")
# editing / numeric entry
reg("clear", "edit", "clear")
reg("reset", "edit", "reset")
reg("store", "edit", "store")
reg("delete", "edit", "delete")

# Curated subset of canonical controls published as the controls/ tree. These are
# the controls that matter for driving activities across TVs / AVRs / STBs /
# players — not the full vocabulary (inputs, colors, niche A/V keys are left out).
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

# Labels where a small index is a real discrete input (HDMI 1, AV 2, …). Others
# (tuner/cable/sat/antenna/phono) carry preset/frequency numbers, not inputs.
NUMBERED_INPUTS = {
    "hdmi", "video", "av", "aux", "component", "composite", "pc", "vga",
    "dvi", "scart", "game",
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
    """Map a raw Flipper button name to a canonical control id, or None."""
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


def title(canon):
    """canonical id -> human folder name: volume_up -> Volume_Up, source -> Source."""
    return "_".join(p.capitalize() for p in canon.split("_"))


def category_of(canon):
    if canon.startswith("digit_"):
        return "digit"
    if canon.startswith("input_"):
        return "input"
    return CATEGORY.get(canon, "other")
