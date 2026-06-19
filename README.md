# ir-canonical

A **canonical media-control vocabulary** and a **Flipper-IRDB name → canonical**
mapping, published as a small Python library so both the **ESPHome codegen**
(`esphome-ir-codegen`) and **Concerto** can resolve remote buttons *semantically*
instead of matching raw strings.

## Why

[Flipper-IRDB](https://github.com/Lucaslhm/Flipper-IRDB) has no enforced button
naming — **54,415 distinct names** over 301,921 occurrences. "Volume up" alone
appears as `VOL+`, `Vol_up`, `VOLUME_UP`, `VOL_^`, `TV_Vol+`, `AMP_VOL+`, … So you
cannot match a control by raw name.

## Use it

```bash
pip install homeops-ir-canonical
```

```python
from ir_canonical import resolve, canonical, MAP

resolve("VOL+")        # -> "volume_up"  (curated lookup, baked at build time)
resolve("TV_Power")    # -> "power_toggle"
canonical("Ch_prev")   # -> "channel_down"  (rule engine; maps unseen spellings)
canonical("HDMI_1")    # -> "input_hdmi_1"
MAP["vol+"]            # the flat {alias: canonical} dict, lower-cased keys
```

- **`resolve(name)`** — fast curated lookup via the bundled, human-maintained
  `controls/` tree (compiled to `control_map.json` at build time).
- **`canonical(name)`** — the broad rule-based engine; resolves spellings the
  curated tree hasn't enumerated yet, and the full vocabulary (not just the core).

Both are case-insensitive.

## The curated controls tree (edit this by hand)

`src/ir_canonical/controls/` is the human-owned source of truth for the **core**
controls that matter for driving activities (power / volume / channel / transport
/ navigation / digits / source — a curated subset):

```
src/ir_canonical/controls/
  Volume_Up/aliases.json     ["VOL+", "Vol_up", "VOLUME_UP", "AMP_VOL+", ...]
  Power_Toggle/aliases.json  ["POWER", "STANDBY", "TV_POWER", "PWR", ...]
  ...
```

Edit any `aliases.json` to prune or extend a control. The build **bakes** the tree
into `control_map.json` (so installs get an instant lookup); CI fails the build if
two controls claim the same alias.

### Beyond IR: app and gamepad families

Two families extend the vocabulary past classic IR remotes so one control language
spans IR, BLE, and native transports:

- **`app_*`** — video-app launch hotkeys (`app_netflix`, `app_youtube`,
  `app_prime_video`, `app_disney_plus`, …). These appear on real IR remotes, so
  both `resolve()` and `canonical()` map their Flipper spellings.
- **`pad_*`** — gamepad controller inputs (`pad_a`, `pad_up`, `pad_l1`,
  `pad_start`, …). These have **no IR source** — they exist purely as
  cross-transport canonical vocabulary, so `resolve()`/`canonical()` only match
  the namespaced `pad_*` spellings, not arbitrary remote names.

## Layout

| Path | What |
|------|------|
| `src/ir_canonical/normalize.py` | the rule-based `canonical()` engine + vocabulary |
| `src/ir_canonical/controls/` | the curated tree (edit by hand) |
| `src/ir_canonical/compile.py` | tree → `{alias: canonical}` compiler |
| `hatch_build.py` | build hook that bakes `control_map.json` into the wheel |
| `seed.py` | dev tool: seed the tree + `data/` reports from a Flipper-IRDB clone |
| `data/` | full auto-derived map + unmapped tail (reference, not shipped) |

## Develop

```bash
python -m build --wheel --no-isolation     # build (bakes the map)
pip install dist/*.whl && pytest -q         # test as a consumer
python seed.py /path/to/Flipper-IRDB-clone  # re-seed the tree (won't clobber edits)
```

## Release & publish

Versioning is managed by [release-please](https://github.com/googleapis/release-please)
(Conventional Commits). Merging the release PR tags a GitHub Release, which triggers
`publish.yaml` to upload the wheel to **PyPI via trusted publishing**.

> One-time PyPI setup: create the `homeops-ir-canonical` project and add a trusted
> publisher → owner `HomeOps`, repo `ir-canonical`, workflow `publish.yaml`,
> environment `pypi`.
