---
description: Check the ESP32 toolchain, drivers and connected boards
---

Use the ws-esp32 skill to check the user's setup.

1. Run `python <skill-dir>/scripts/wsesp.py doctor` and summarize what's installed and missing.
2. If exactly one ESP32 port shows up, offer to run `wsesp.py detect` to identify the board (it resets the board).
3. For anything missing, give the install command from references/workflows/setup-environment.md for this OS. Don't install anything without the user's OK.
