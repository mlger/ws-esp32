# ws-esp32: Waveshare ESP32 Agent Skill

[![CI](https://github.com/mlger/ws-esp32/actions/workflows/ci.yml/badge.svg)](https://github.com/mlger/ws-esp32/actions/workflows/ci.yml)
[![Firmware builds](https://github.com/mlger/ws-esp32/actions/workflows/firmware.yml/badge.svg)](https://github.com/mlger/ws-esp32/actions/workflows/firmware.yml)
[![Release](https://img.shields.io/github/v/release/mlger/ws-esp32)](https://github.com/mlger/ws-esp32/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

An agent skill that helps AI coding agents (Claude Code, Claude.ai, Codex, Cursor and others) write firmware for **Waveshare ESP32 boards** without guessing pin numbers.

- **Board profiles**: one JSON file per board with chip, flash/PSRAM, USB, every onboard pin, I2C addresses, tested library versions and known problems. Every pin links to its source. Browse them on the **[board pinout site](https://mlger.github.io/ws-esp32/)**.
- **Pin checker**: catches flash/PSRAM pins, strapping pins, onboard conflicts, native-USB pins, ADC2 + Wi-Fi and I2C address clashes before you wire anything.
- **Project generator**: buildable ESP-IDF, Arduino and PlatformIO starters with the right flash size, PSRAM mode and USB console already set, plus a generated `board_pins.h`.
- **Display generator**: `--with display` adds working screen + touch + LVGL 9 code: SPI panels (1.28" round, 1.47", 2.8") and RGB panels (4.3", 7") on ESP-IDF, and SPI panels on Arduino.
- **Device tools**: `detect` tells you which board is plugged in; `decode` turns a crash backtrace into file and line.
- **Safety hook**: Claude Code asks you before running eFuse, erase-flash, flash-encryption or secure-boot commands.
- **Workflows**: toolchain setup (Windows/macOS/Linux/WSL/Docker), build-flash-monitor, display bring-up and troubleshooting.
- **No dependencies**: Python 3.9+ standard library. `pyserial` and `esptool` are optional.

## Supported boards

| Board | Chip | Flash / PSRAM | Display codegen | Data |
|---|---|---|---|---|
| ESP32-S3-Touch-LCD-1.28 | ESP32-S3 | 16 MB / 2 MB | IDF + Arduino (GC9A01 + touch) | wiki |
| ESP32-S3-LCD-1.47 | ESP32-S3 | 16 MB / 8 MB | IDF + Arduino (ST7789) | wiki |
| ESP32-S3-Touch-LCD-2.8 | ESP32-S3 | 16 MB / 8 MB | IDF + Arduino (ST7789) | wiki |
| ESP32-S3-Touch-LCD-4.3 | ESP32-S3 | 16 MB / 8 MB | IDF (RGB + GT911 touch) | wiki |
| ESP32-S3-Touch-LCD-7 | ESP32-S3 | 16 MB / 8 MB | IDF (RGB + GT911 touch) | wiki |
| ESP32-S3-Touch-AMOLED-1.8 | ESP32-S3 | 16 MB / 8 MB | not yet (QSPI) | wiki |
| ESP32-S3-ETH | ESP32-S3 | 16 MB / 8 MB | - | wiki |
| ESP32-S3-Zero | ESP32-S3 | 4 MB / 2 MB | - | wiki |
| ESP32-C6-LCD-1.47 | ESP32-C6 | 4 MB / - | IDF + Arduino (ST7789) | wiki |
| ESP32-C6-Zero | ESP32-C6 | 4 MB / - | - | wiki |
| ESP32-C3-Zero | ESP32-C3 | 4 MB / - | - | wiki |
| ESP32-P4-NANO | ESP32-P4 (v1.x) | 16 MB / 32 MB | - | partial |
| ESP32-P4-NANO-WIFI6-DB | ESP32-P4 (v3.x) | 16 MB / 32 MB | - | wiki |

**Data levels:** `partial` means some pins are still unknown. `wiki` means all pins come from Waveshare's docs or demo code. `schematic` means checked against the schematic. `hardware-tested` means confirmed on a real board. No board is `hardware-tested` yet, so if you own one, please [send a test report](https://github.com/mlger/ws-esp32/issues/new?template=hardware-test.yml).

## Install

### Claude Code (plugin, recommended)

Includes the skill, the safety hook and the `/esp-new`, `/esp-flash`, `/esp-doctor` commands.

```text
/plugin marketplace add mlger/ws-esp32
/plugin install ws-esp32@ws-esp32
```

### Claude Code (skill folder only)

```bash
git clone https://github.com/mlger/ws-esp32
cp -r ws-esp32/skills/ws-esp32 ~/.claude/skills/
```

### Claude.ai / Claude Desktop

Download `ws-esp32-<version>.zip` from [Releases](https://github.com/mlger/ws-esp32/releases) and upload it under Settings > Capabilities > Skills.

### Other agents (Codex, Cursor, Gemini CLI, Copilot)

Copy `skills/ws-esp32/` into your project and point the agent at it from `AGENTS.md` (or `.cursor/rules`). See [AGENTS.md](AGENTS.md) for an example.

## Use

Ask in plain language:

- "Start an ESP-IDF project for my ESP32-S3-Touch-LCD-1.28 that shows a clock with LVGL"
- "Can I use GPIO16 for a relay and add an SSD1306 OLED on the C6-LCD-1.47?"
- "My 4.3 inch screen drifts when Wi-Fi is on"
- "Which board is plugged in?"

Or use the slash commands: `/ws-esp32:esp-new 4.3 idf display hmi`, `/ws-esp32:esp-flash`, `/ws-esp32:esp-doctor`.

The CLI also works on its own:

```bash
cd skills/ws-esp32
python scripts/wsesp.py boards
python scripts/wsesp.py show 1.28
python scripts/wsesp.py pins esp32-s3-touch-lcd-1.28 --use 16=gpio_out:relay --use i2c@0x3C:oled
python scripts/wsesp.py new esp32-s3-touch-lcd-4.3 --framework idf --with display --name hmi
python scripts/wsesp.py new esp32-c6-lcd-1.47 --framework arduino --with display --name ui
python scripts/wsesp.py detect
python scripts/wsesp.py decode build/hmi.elf crash.log --board esp32-s3-touch-lcd-4.3
python scripts/wsesp.py doctor
```

Sample `pins` output:

```text
OK    [relay] GPIO16 looks fine for gpio_out
ERROR [fan] GPIO2 is already used onboard by lcd.bl (GC9A01A)
ERROR [dup] I2C address 0x15 on i2c is taken by touch (CST816S)
OK    [oled] 0x3C is free on i2c (SDA=6, SCL=7)
```

## Repository layout

```text
.claude-plugin/            plugin + marketplace manifests
commands/                  /esp-new, /esp-flash, /esp-doctor
hooks/                     safety hook (asks before eFuse / erase / secure boot commands)
skills/ws-esp32/
  SKILL.md                 entry point the agent reads first
  data/chips.json          chip GPIO rules
  data/boards/*.json       board profiles (schema: data/board.schema.json)
  references/              workflows and guides, loaded on demand
  scripts/wsesp.py         CLI
  templates/               project templates
evals/                     prompts that check the skill gives correct answers
tests/                     pytest suite
tools/                     CI helpers, docs site builder, eval runner, release packaging
.github/                   CI, firmware build matrix, docs site, issue templates
```

## Development

```bash
python -m pip install pytest jsonschema pre-commit
pre-commit install          # ruff, JSON/YAML checks, board validation and tests on every commit
python -m pytest
python tools/build_docs.py  # preview the docs site in ./site
python tools/run_evals.py   # needs an authenticated `claude` CLI
```

Or open the repo in VS Code with the dev container (`.devcontainer/`), which ships ESP-IDF, Python and the board schema already set up.

On every change, CI generates projects for **every board** and compiles them with ESP-IDF (each board's tested version and the latest), Arduino-ESP32 and PlatformIO, plus the display projects. It also runs weekly to catch upstream breakage.

## Disclaimer

This project is not affiliated with Waveshare or Espressif. Product names belong to their owners. Board data is checked against public documentation, but always confirm against your board's revision and schematic before connecting hardware.

## License

[MIT](LICENSE)
