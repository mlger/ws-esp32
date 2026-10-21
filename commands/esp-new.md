---
description: Create a new firmware project for a Waveshare ESP32 board
argument-hint: <board> [idf|arduino|pio] [display] [name]
---

Use the ws-esp32 skill to start a new project.

Arguments: $ARGUMENTS

1. Find the board with `python <skill-dir>/scripts/wsesp.py show <board>`. If nothing or several boards match, list the options and ask.
2. Framework defaults to `idf`. Add `--with display` when the user asked for "display", "lvgl", "screen" or "ui" and `show` reports display codegen is supported. If it isn't, say why.
3. Run `wsesp.py new <board> --framework <fw> [--with display] --name <name> --out ./<name>`. Never pass `--force` without asking.
4. Pass on the board's warnings and verification level. Then give the exact build and flash commands for the chosen framework.
