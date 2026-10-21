# Start a new project

1. **Identify the board.** Run `wsesp.py boards` or `wsesp.py show <part of the name>`. If there's no match, follow `add-board.md` or ask the user for the exact product name printed on the PCB or listed on the store page.
2. **Pick the framework** if the user hasn't (see `../frameworks.md`). Defaults:
   - LVGL GUI, RGB/QSPI display, or production work: ESP-IDF.
   - Quick experiments or a user who already knows Arduino: Arduino.
   - Multi-board projects or VS Code users: PlatformIO.
3. **Generate the project:**
   ```bash
   python scripts/wsesp.py new <board> --framework idf|arduino|pio --name <name> --out <dir>
   ```
   Add `--dry-run` to list the files without writing them. The command won't overwrite existing files unless you pass `--force`. Ask the user before using it.
4. **Build it unchanged first.** That proves the toolchain works before you add features. See `build-flash-monitor.md`.
5. **Add features one at a time.** Run `wsesp.py pins` for any new pin, then build, flash and check the serial log after each step.

## What gets generated

| File | Purpose |
|---|---|
| `board_pins.h` | `WS_*` macros for every onboard pin, I2C address and screen size. Unknown pins appear as comments. |
| `sdkconfig.defaults` (IDF) | Target, flash size, PSRAM mode (quad/octal), console (UART vs USB-Serial-JTAG), large app partition, 1 kHz tick |
| `main/idf_component.yml` (IDF) | Driver components for the board's display and touch, commented out |
| `sketch.yaml` (Arduino) | `default_fqbn` with the right FlashSize / PSRAM / CDCOnBoot options |
| `platformio.ini` (PIO) | pioarduino platform, flash size, partitions, PSRAM memory type, USB CDC flags |
| `main.c` / sketch | Prints chip, flash and PSRAM info, turns on the backlight, blinks the RGB LED |

The starter app checks the profile against real hardware. If the PSRAM size it prints doesn't match the profile, either the config is wrong or the board is a different variant. Tell the user.

## Next steps the user usually wants

- Display and touch: `display-bringup.md`.
- Wi-Fi credentials: keep them in `secrets.h` or Kconfig (`idf.py menuconfig`). `secrets.h` is already in `.gitignore`. Never commit credentials.
- OTA updates: use the `two_ota` partition table (`CONFIG_PARTITION_TABLE_TWO_OTA=y`). On 4 MB boards, check that the app fits in one slot.
- CI for the user's project: copy this repo's `.github/workflows/firmware.yml` pattern (espressif/esp-idf-ci-action).
