# Waveshare ESP32 Agent Skill

An agent skill that helps AI coding agents (Claude Code, Claude.ai, Codex, Cursor and others) write firmware for **Waveshare ESP32 boards** without guessing pin numbers.

- **Board profiles**: one JSON file per board with chip, flash/PSRAM, USB, every onboard pin, I2C addresses, tested library versions and known problems. Each profile records where its data came from and how well it has been verified.
- **Pin checker**: catches flash/PSRAM pins, strapping pins, onboard conflicts, native-USB pins, ADC2 + Wi-Fi and I2C address clashes before you wire anything.
- **Project generator**: buildable ESP-IDF, Arduino and PlatformIO starters with the right flash size, PSRAM mode and USB console already set, plus a generated `board_pins.h`.
- **Display generator**: `--with display` adds working LCD + touch + LVGL 9 code for SPI-screen boards (1.28" round, 1.47" S3/C6).
- **Workflows**: toolchain setup (Windows/macOS/Linux/WSL/Docker), build-flash-monitor, display + touch + LVGL bring-up, and troubleshooting for crashes and boot problems.
- **No dependencies**: Python 3.9+ standard library. `pyserial` is optional and only used for port detection.

## Supported boards

| Board | Chip | Flash / PSRAM | Data |
|---|---|---|---|
| ESP32-S3-Touch-LCD-1.28 | ESP32-S3 | 16 MB / 2 MB | wiki |
| ESP32-S3-Touch-LCD-4.3 | ESP32-S3 | 16 MB / 8 MB | wiki |
| ESP32-S3-LCD-1.47 | ESP32-S3 | 16 MB / 8 MB | wiki |
| ESP32-S3-Touch-AMOLED-1.8 | ESP32-S3 | 16 MB / 8 MB | partial |
| ESP32-S3-Zero | ESP32-S3 | 4 MB / 2 MB | wiki |
| ESP32-C6-LCD-1.47 | ESP32-C6 | 4 MB / - | wiki |
| ESP32-C6-Zero | ESP32-C6 | 4 MB / - | partial |

**Data levels:** `partial` means some pins are still unknown. `wiki` means all pins come from Waveshare's wiki. `schematic` means checked against the schematic. `hardware-tested` means confirmed on a real board. Help move boards up a level, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Install

### Claude Code (plugin)

```text
/plugin marketplace add mlger/waveshare-esp32-skill
/plugin install waveshare-esp32@waveshare-esp32-skill
```

### Claude Code (skill folder only)

```bash
git clone https://github.com/mlger/waveshare-esp32-skill
cp -r waveshare-esp32-skill/skills/waveshare-esp32 ~/.claude/skills/        # all projects
# or: cp -r ... <your-project>/.claude/skills/                               # one project
```

### Claude.ai / Claude Desktop

Download `waveshare-esp32-<version>.zip` from [Releases](../../releases) and upload it under Settings > Capabilities > Skills.

### Other agents (Codex, Cursor, Gemini CLI, Copilot)

Copy `skills/waveshare-esp32/` into your project and point the agent at it from `AGENTS.md` (or `.cursor/rules`). See [AGENTS.md](AGENTS.md) in this repo for an example.

## Use

Ask in plain language. The skill loads when you mention a Waveshare board or ESP32 work:

- "Start an ESP-IDF project for my ESP32-S3-Touch-LCD-1.28 that shows a clock with LVGL"
- "Can I use GPIO16 for a relay and add an SSD1306 OLED on the C6-LCD-1.47?"
- "My 4.3 inch screen drifts when Wi-Fi is on"
- "Set up ESP-IDF on Windows and flash my board"

The CLI also works on its own:

```bash
cd skills/waveshare-esp32
python scripts/wsesp.py boards
python scripts/wsesp.py show 1.28
python scripts/wsesp.py pins esp32-s3-touch-lcd-1.28 --use 16=gpio_out:relay --use i2c@0x3C:oled
python scripts/wsesp.py new esp32-c6-lcd-1.47 --framework idf --name hello --out ./hello
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
skills/waveshare-esp32/
  SKILL.md                 entry point the agent reads first
  data/chips.json          chip GPIO rules
  data/boards/*.json       board profiles
  references/              workflows and guides, loaded on demand
  scripts/wsesp.py         CLI (boards, show, pins, header, new, doctor, ports)
  templates/               project templates
tests/                     pytest suite
tools/                     CI helpers and release packaging
.github/                   CI, firmware build matrix, issue templates
```

## Development

```bash
python -m pip install pytest
python -m pytest
python skills/waveshare-esp32/scripts/wsesp.py validate-data
```

On every push, CI generates a starter project for **every board** and compiles it with ESP-IDF and Arduino-ESP32, so a broken profile or template fails the build.

## Disclaimer

This project is not affiliated with Waveshare or Espressif. Product names belong to their owners. Board data is checked against public documentation, but always confirm against your board's revision and schematic before connecting hardware.

## License

[MIT](LICENSE)
