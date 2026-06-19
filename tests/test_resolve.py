"""Tests for the installed ir_canonical package (run against the built wheel)."""

from ir_canonical import CORE, MAP, canonical, resolve


def test_resolve_curated_aliases():
    assert resolve("VOL+") == "volume_up"
    assert resolve("TV_Power") == "power_toggle"
    assert resolve("5") == "digit_5"
    assert resolve("nonexistent button xyz") is None


def test_resolve_is_case_insensitive():
    assert resolve("vol+") == resolve("VOL+") == "volume_up"


def test_canonical_engine_handles_unseen_spellings():
    assert canonical("Ch_prev") == "channel_down"
    assert canonical("Play/Pause") == "play_pause"
    assert canonical("SCAN_>>") == "fast_forward"


def test_input_controls():
    assert canonical("HDMI_1") == "input_hdmi1"
    assert canonical("AUX 2") == "input_aux2"
    assert canonical("Optical") == "input_optical"
    assert canonical("ARC") == "input_arc"
    assert resolve("HDMI_1") == "input_hdmi1"


def test_video_app_controls():
    # curated aliases (resolve) + rule engine (canonical)
    assert resolve("Netflix") == "app_netflix"
    assert resolve("You_Tube") == "app_youtube"
    assert resolve("Disney+") == "app_disney_plus"
    assert resolve("HBO Max") == "app_hbo_max"
    assert canonical("Netflix") == "app_netflix"
    assert canonical("YT") == "app_youtube"
    assert canonical("Prime Video") == "app_prime_video"
    # "TV" is a dropped device token, so "Apple TV" reduces to {apple}
    assert canonical("Apple TV") == "app_apple_tv"


def test_gamepad_controls():
    # no IR source, but the canonical vocabulary + tree must carry them
    assert resolve("pad_a") == "pad_a"
    assert resolve("pad_menu") == "pad_menu"
    assert canonical("Pad_A") == "pad_a"
    assert canonical("pad l1") == "pad_l1"


def test_map_keys_are_lowercased():
    assert all(key == key.lower() for key in MAP)


def test_every_core_control_round_trips():
    # each CORE control has a folder, so its id resolves to itself
    for control in CORE:
        assert resolve(control) == control
