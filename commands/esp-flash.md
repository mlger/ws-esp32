---
description: Build, flash and monitor the current ESP32 project
argument-hint: [port]
---

Use the ws-esp32 skill to build and flash the project in the current folder.

Arguments: $ARGUMENTS

1. Detect the framework: `CMakeLists.txt` + `main/` means ESP-IDF, `platformio.ini` means PlatformIO, a `*.ino` with `sketch.yaml` means Arduino CLI.
2. If no port was given, run `python <skill-dir>/scripts/wsesp.py ports` and pick the ESP32 port. If there are several, ask.
3. Build first and show any errors. Don't flash a failed build.
4. Flash, then open the monitor (ESP-IDF: `idf.py -p PORT flash monitor`). If connecting fails, walk the user through BOOT + RESET download mode (see references/workflows/build-flash-monitor.md).
5. Never erase flash or touch eFuses as part of this command.
