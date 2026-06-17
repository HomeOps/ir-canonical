# ir-canonical

A **canonical media-control vocabulary** and a **Flipper-IRDB name → canonical**
mapping, so anything that processes IR remotes (the ESPHome codegen at
YAML-generation time, Concerto when resolving activities) can act on controls
*semantically* instead of matching raw button strings.

## Why

[Flipper-IRDB](https://github.com/Lucaslhm/Flipper-IRDB) has no enforced button
naming. Measured across the whole DB: **54,415 distinct names** over **301,921
occurrences**. One control appears under dozens of spellings — "volume up" alone:
`VOL+`, `Vol_up`, `VOLUME_UP`, `VOL_^`, `TV_Vol+`, `VOLUME+`, `VOL +`, … So you
cannot match a control by raw name.

## What's here

| File | What |
|------|------|
| `build_name_map.py` | Generator + the importable `canonical(name)` function. |
| `data/canonical_controls.yaml` | The canonical vocabulary, grouped by category. |
| `data/flipper_name_map.json` | `{ name: canonical_name }`, keys **lower-cased** — look up with `name.lower()`. |
| `data/unmapped_names.txt` | The long tail (device-specific labels, typos), by frequency, for review. |

## How the mapping works

It's **order-independent and rule-based**, so spellings not yet in the DB still
map. `canonical(name)`:

1. bare digit → `digit_N`;
2. a lone source label (`CD`, `DVD`, `TV`, `HDMI`, …) → `input_<label>`;
3. otherwise tokenize (camelCase + separators + sign glyphs `+ - ^ >> <<`),
   expand each token (`vol→volume`, `+→up`, `ffwd→fast_forward`, …), drop
   device/filler tokens (`tv`, `dvd`, `key`, …), and match the resulting token
   **set** against the canonical table;
4. labelled inputs with a single small index (`HDMI_1`, `Video_2`) →
   `input_<label>_<n>`.

Examples: `TV_Vol+ → volume_up`, `Ch_prev → channel_down`, `Play/Pause →
play_pause`, `SCAN_>> → fast_forward`, `DVD_Menu → menu`, `Open/Close → eject`.

The same `canonical()` is importable, so the codegen can normalize live rather
than depend on the frozen JSON.

> **JSON keys are case-folded.** Flipper files disagree on casing (`0/AV` vs
> `0/av`), and casing never changes meaning, so map keys are lower-cased and
> deduped — look up with `name.lower()`. This also keeps the file parseable by
> case-insensitive consumers (e.g. PowerShell `ConvertFrom-Json`).

## Coverage (current)

- **57.7%** of all button *occurrences* mapped (the head of the distribution).
- **194** canonical controls across power / volume / channel / transport /
  navigation / input / digit / color / a-v / edit.
- The unmapped ~51k distinct names are intentionally left alone — device-specific
  features, function keys, frequencies, and noise. Coverage of *occurrences*
  matters more than of *distinct names*; mapping the long tail risks wrong
  mappings, which are worse than none.

## Regenerate

```bash
python build_name_map.py /path/to/Flipper-IRDB-clone data
```

Reproducible as the database grows; extend `TOKEN_EXPAND` / the `reg(...)` table
to raise coverage, and re-run.
