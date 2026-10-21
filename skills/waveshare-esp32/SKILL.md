---
name: waveshare-esp32
description: Build, flash and debug firmware for Waveshare ESP32 development boards (ESP32-S3/C6/C3 boards with LCD, AMOLED, touch, IMU, SD, RGB LED). Use when the user mentions a Waveshare board, asks for board pinouts, wants to start an ESP-IDF / Arduino / PlatformIO project for one, bring up its display or touch with LVGL, check whether a GPIO is safe to use, set up an ESP32 toolchain, or fix flashing, boot-loop and serial-port problems.
---

# Waveshare ESP32

Help the user build firmware for Waveshare ESP32 boards using board data that has been checked against Waveshare's docs, not guessed.

The skill directory (the folder holding this file) contains:

- `data/boards/*.json` - one profile per board: chip, flash/PSRAM, USB, every onboard pin, I2C addresses, tested library versions, known problems.
- `data/chips.json` - chip rules: flash pins, strapping pins, USB/UART0/JTAG pins, ADC channels.
- `scripts/wsesp.py` - CLI (Python 3.9+, standard library only). Run it as `python <skill-dir>/scripts/wsesp.py ...`.
- `references/` - workflows and topic guides. Load only what the task needs.

## Ground rules

1. **Pins come from the board profile, never from memory.** Run `wsesp.py show <board>` before writing pin numbers. If the board has no profile, or the profile says `partial` with `null` pins, say so and ask the user to confirm from the Waveshare wiki or schematic. Never invent a pin.
2. **Check before wiring.** Before you tell the user to connect anything, run `wsesp.py pins <board> --use GPIO=FUNCTION:label ...` and report every ERROR and WARN.
3. **Use generated `board_pins.h`.** Put pins in code through `WS_*` macros from `wsesp.py header <board>`, not hard-coded numbers.
4. **Match the tested versions.** Profiles list the Arduino core, LVGL and ESP-IDF versions Waveshare's demos use (`software`). LVGL 8 and 9 APIs differ; Arduino-ESP32 2.x and 3.x APIs differ. Ask or check before mixing them.
5. **Ask before irreversible or risky commands.** Get explicit approval for `esptool erase_flash`, any `espefuse` command (eFuses can't be undone), enabling flash encryption or secure boot, or writing to an unfamiliar serial port. Never burn eFuses as part of a fix.
6. **Read-only first.** `wsesp.py doctor` only inspects. It never installs anything. Show the user install commands and let them run or approve them.

## Pick the workflow

| User wants to... | Read |
|---|---|
| Install or fix the toolchain (ESP-IDF, Arduino, PlatformIO, drivers) | `references/workflows/setup-environment.md` |
| Start a new project for a board | `references/workflows/new-project.md` |
| Build, flash, monitor, pick a serial port | `references/workflows/build-flash-monitor.md` |
| Get a display / touch / LVGL working | `wsesp.py show <board>` says whether `new --with display` can generate it; then `references/workflows/display-bringup.md` |
| Fix a crash, boot loop, "no serial port", flashing errors | `references/workflows/troubleshooting.md` |
| Add hardware (sensor, relay, I2C device) to a board | Run `wsesp.py pins`, then `references/chips.md` |
| Support a board that has no profile | `references/workflows/add-board.md` |
| Choose between ESP-IDF, Arduino and PlatformIO | `references/frameworks.md` |

## CLI quick reference

```bash
python scripts/wsesp.py boards                       # list profiles
python scripts/wsesp.py show 1.28                    # fuzzy match on id/name/alias
python scripts/wsesp.py pins esp32-s3-touch-lcd-1.28 --use 16=gpio_out:relay --use i2c@0x3C:oled
python scripts/wsesp.py header esp32-c6-lcd-1.47 > board_pins.h
python scripts/wsesp.py new esp32-s3-touch-lcd-4.3 --framework idf --name hmi --out ./hmi
python scripts/wsesp.py new esp32-s3-touch-lcd-1.28 --framework idf --with display --name ui   # LCD+touch+LVGL 9
python scripts/wsesp.py doctor                       # toolchain + serial ports
python scripts/wsesp.py ports                        # identify CH343 vs native USB
```

Add `--json` to `boards`, `show`, `pins`, `doctor` and `ports` for machine-readable output. `pins` exits with 1 when it finds an error.

Pin functions: `gpio`, `gpio_in`, `gpio_out`, `adc`, `pwm`, `button`, `interrupt`, `uart_tx`, `uart_rx`, `i2c_sda`, `i2c_scl`, `spi_mosi`, `spi_miso`, `spi_sclk`, `spi_cs`, `i2s_bclk`, `i2s_ws`, `i2s_dout`, `i2s_din`, `i2s_mclk`, `ws2812`, `onewire`, `can_tx`, `can_rx`, `rmt_tx`, `rmt_rx`, `touch`. To add a device on a board's existing I2C bus, use `BUS@0xADDR:label` (for example `i2c@0x3C:oled`).

## How to answer

- Name the board profile and its verification level (`partial`, `wiki`, `schematic` or `hardware-tested`) when giving pins.
- Pass on relevant `warnings` from the profile, such as shared buses, strapping pins or the 4.3" CAN/RS485 pin sharing.
- Give complete, buildable code: includes, `CMakeLists.txt` or `platformio.ini` changes, and `sdkconfig` options. Show the command to build and flash it.
- For the serial port, run `wsesp.py ports` instead of guessing `COM3` or `/dev/ttyUSB0`.
- When something fails, ask for the exact log (build output or serial monitor from reset) before changing code.
