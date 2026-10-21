# Add a board profile

Use this when a user's board has no profile, or when you're contributing one to the repo.

## Rules

- Every pin needs a source: the Waveshare wiki/docs page, the schematic PDF, or the demo code's pin header. Put the URLs in `verification.sources`.
- If a source doesn't give a pin, set it to `null` and mark the profile `"status": "partial"`. Don't fill gaps from similar boards. Waveshare reuses names across revisions with different pinouts.
- Record contradictions on the vendor page in `warnings` (wrong controller name, duplicated pins) instead of choosing one silently.

## Verification levels

| Status | Meaning |
|---|---|
| `partial` | Some pins unknown (`null`) |
| `wiki` | All pins from the wiki/docs page, not checked on hardware |
| `schematic` | Checked against the schematic PDF |
| `hardware-tested` | Starter project plus display/touch confirmed on a real board. Put the board revision in `notes` |

## Steps

Profiles follow `data/board.schema.json`. Editors that support JSON Schema (VS Code does, through the `$schema` line) give autocomplete and inline errors.

1. Copy the closest existing file in `data/boards/` to `data/boards/<id>.json`. The id is the product name in lowercase, for example `esp32-s3-touch-lcd-2.8`.
2. Fill in `chip` (a key from `data/chips.json`), `soc` (exact part, for example `ESP32-S3R8`), `flash_mb`, `psram_mb`, `psram_mode`, and `usb`.
   - In the part number, `R8` means 8 MB octal PSRAM, `R2` 2 MB quad, `N16` 16 MB flash, and `FH4` 4 MB in-package flash.
3. Add peripherals:
   - Shared buses as `kind: "bus"` (`i2c`, `spi`) with their pins. Devices on them use `"bus": "<id>"` and their own pins (CS, DC, INT...).
   - I2C addresses as `"addr": "0x15"`. Add `"addr_verified": false` if the address is a typical value rather than documented.
   - Expander pins as `"EXIO2"`. The board then needs a `kind: "io_expander"` peripheral.
   - Two peripherals on the same GPIOs (for example CAN and RS485) both get the same `"share": "<group>"`.
   - Things the user may still use (the BOOT button) get `"soft": true`, which turns conflicts into warnings.
   - Native USB pins as a `usb` peripheral with `dm`/`dp`.
   - Pins that exist on the chip but have no pad on the board go in `not_exposed`.
   - For RGB displays, add `rgb_timing` (pclk_hz, porches, pulse widths, source) copied from Waveshare's demo `waveshare_lcd_port.h`.
   - For SPI displays, add `panel_init` (`rgb_order`, `invert`, `mirror_x/y`, `swap_xy`, `gap`, `pclk_mhz`, `verified`, `source`) so `new --with display` can generate working code. Set `verified: true` only after seeing a correct image on hardware.
4. Use `free_pins` only if the source lists the broken-out pins. Otherwise leave it `null`.
5. Fill in `software` with the versions Waveshare's demos use.
6. Validate and preview:
   ```bash
   python scripts/wsesp.py validate-data
   python scripts/wsesp.py show <id>
   python scripts/wsesp.py new <id> --framework idf --name t --out /tmp/t && cd /tmp/t && idf.py build
   ```
7. For a new chip family, add it to `data/chips.json` (gpio ranges, flash pins, strapping, USB, UART0, ADC) from the Espressif datasheet.

## Peripheral `kind` values

`bus`, `display`, `touch`, `imu`, `rtc`, `pmu`, `codec`, `io_expander`, `storage`, `led`, `button`, `adc`, `can`, `uart`, `usb`, `camera`, `sensor`, `ethernet`.

Signal names used for `board_pins.h` macros: keep them short and lowercase (`cs`, `dc`, `rst`, `bl`, `int`, `sda`, `scl`, `mosi`, `miso`, `sclk`, `tx`, `rx`, `data`, `io`). The generated macro is `WS_<PERIPHERAL>_<SIGNAL>`, for example `WS_LCD_BL`.
