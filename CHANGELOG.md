# Changelog

## 0.1.0 (2026-06-17)


### Features

* add discrete input controls (HDMI/AUX/optical/coax/ARC…) to the canonical set ([68cfbd0](https://github.com/HomeOps/ir-canonical/commit/68cfbd05d39246c2cfd4464042608c981156b915))
* canonical media-control vocabulary + Flipper name→canonical map ([302abaf](https://github.com/HomeOps/ir-canonical/commit/302abaf7fd7447878da3078ace078670856f0e01))
* compile_map.py — flatten controls/ tree to a fast-load {alias: canonical} JSON ([b230b7e](https://github.com/HomeOps/ir-canonical/commit/b230b7e579766f49c84697b62ce915198eb20f8e))
* human-editable controls/ tree (folder per control + aliases.json) ([b4bd466](https://github.com/HomeOps/ir-canonical/commit/b4bd466f14e8c05827665ba24453a364e858934f))
* package ir-canonical as a pip library with release-please + PyPI publish ([f4f29ba](https://github.com/HomeOps/ir-canonical/commit/f4f29ba5ba557c2d7bf31ee63f02dfc8447937f6))


### Bug Fixes

* case-fold flipper_name_map.json keys to dedupe and unblock parsers ([121e3aa](https://github.com/HomeOps/ir-canonical/commit/121e3aab05ff9fd1eb7bb6ae0e0abffb24bbaa5b))
