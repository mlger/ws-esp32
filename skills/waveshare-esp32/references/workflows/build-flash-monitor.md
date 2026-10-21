# Build, flash, monitor

## Find the port

Run `python scripts/wsesp.py ports`. It identifies native USB (`303A:1001`) and CH343 (`1A86:55D3`) ports. Boards with two USB-C ports (such as the 4.3") show up twice when both are connected. Flash through the one the profile lists as `console`.

## Commands

| | ESP-IDF | Arduino CLI | PlatformIO |
|---|---|---|---|
| Set target | `idf.py set-target esp32s3` | in FQBN | in `platformio.ini` |
| Build | `idf.py build` | `arduino-cli compile .` | `pio run` |
| Flash | `idf.py -p PORT flash` | `arduino-cli upload -p PORT .` | `pio run -t upload --upload-port PORT` |
| Monitor | `idf.py -p PORT monitor` (exit `Ctrl+]`) | `arduino-cli monitor -p PORT -c baudrate=115200` | `pio device monitor` |
| All at once | `idf.py -p PORT flash monitor` | | `pio run -t upload -t monitor` |
| Config | `idf.py menuconfig` | Tools menu / FQBN options | `board_build.*` / `build_flags` |
| Clean | `idf.py fullclean` | `--clean` | `pio run -t clean` |

After changing `sdkconfig.defaults`, delete `sdkconfig` (or run `idf.py fullclean`) so the defaults apply again.

## Download (bootloader) mode

Flashing normally resets the board into the bootloader by itself. If it says "Failed to connect" or the port is missing:

1. Hold **BOOT**.
2. Press and release **RESET** (or plug in USB while holding BOOT).
3. Release **BOOT** and flash again.
4. On native USB boards, press **RESET** after flashing to start the app.

The boot pin is GPIO0 on ESP32/S3 and GPIO9 on C3/C6.

## Release binaries

To give users a single file they can flash at offset 0x0:

```bash
cd build && esptool.py --chip esp32s3 merge_bin -o ../firmware-merged.bin @flash_args
```

esptool v5 uses dashed command names (`merge-bin`, `write-flash`). The old underscore names still work but print a warning. Flash the merged file with `esptool.py -p PORT write_flash 0x0 firmware-merged.bin`, or point users to the browser-based ESP Web Tools / Espressif's web flasher.

## Decoding crashes

- `idf.py monitor` decodes backtraces by itself. Keep using it during development.
- PlatformIO: `monitor_filters = esp32_exception_decoder` (already set in generated projects).
- Arduino CLI or a raw log: run `xtensa-esp32s3-elf-addr2line -pfiaC -e build/<app>.elf 0x4200abcd 0x...` (RISC-V chips: `riscv32-esp-elf-addr2line`).

## Erasing

`idf.py erase-flash` / `esptool.py erase_flash` wipes NVS too: Wi-Fi credentials, calibration, pairing data. Ask the user first. Use it only when stale NVS or partition data is the likely cause.
