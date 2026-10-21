# Chip GPIO rules

`data/chips.json` is the source of truth for these rules, and `wsesp.py pins` applies them. This page explains the reasons behind them.

## Never use

- **Flash pins.** ESP32: GPIO6-11. S3: GPIO26-32. C3: GPIO12-17. C6: GPIO24-30. Using them crashes the chip immediately. (ESP32-P4 flash and PSRAM use dedicated pads, so no GPIO is lost.)
- **Octal PSRAM pins (S3 with R8 / N16R8):** GPIO33-37.
- **WROVER PSRAM (classic ESP32):** GPIO16-17.

## Use with care

| Chip | Strapping pins | Rule |
|---|---|---|
| ESP32 | 0, 2, 5, 12, 15 | **GPIO12 high at reset selects 1.8 V flash, so the board won't boot.** Never add a pull-up to it. |
| ESP32-S3 | 0, 3, 45, 46 | GPIO0 low = download mode. Avoid external pulls on 45/46. |
| ESP32-C3 | 2, 8, 9 | GPIO9 low = download mode. GPIO8 must be high to download. |
| ESP32-C6 | 4, 5, 8, 9, 15 | GPIO9 low = download mode. GPIO8 must be high to download. |
| ESP32-P4 | 34, 35, 36, 37, 38 | GPIO35 low = download mode (GPIO36 high). GPIO34 selects the JTAG source. 37/38 are also UART0. |

Strapping pins are fine as outputs after boot. The danger is an external pull-up/down or a connected device holding the pin at the wrong level during reset.

## ESP32-P4 chip revisions

P4 chips before v3.0 (ECO1, early ESP32-P4-NANO) and v3.x (part numbers ending in X) need different builds. Board profiles set `chip_revision` (`v1` or `v3`), and `wsesp.py new` turns it into `CONFIG_ESP32P4_SELECTS_REV_LESS_V3`, the Arduino `ChipVariant` menu, or the PlatformIO board (`esp32-p4` / `esp32-p4_r3`). Firmware built for one revision does not boot on the other. Check the chip with `wsesp.py detect`.

## Other limits

- **Input-only:** ESP32 GPIO34-39 have no output driver and no internal pull resistors.
- **ADC:** use ADC1 when Wi-Fi is on. ESP32 ADC1 = GPIO32-39. S3 ADC1 = GPIO1-10. C3 = GPIO0-4. C6 = GPIO0-6. P4 has no Wi-Fi of its own (boards add a C6/C5 coprocessor), so ADC1 = GPIO16-23 and ADC2 = GPIO49-54 both work.
- **Native USB:** S3 GPIO19/20, C3 GPIO18/19, C6 GPIO12/13, P4 GPIO24/25 (USB Serial/JTAG). Reusing them on a native-only board removes your only flash and console port.
- **UART0 console:** S3 43/44, C3 21/20, C6 16/17, P4 37/38, ESP32 1/3.
- **JTAG:** S3 GPIO39-42, C3/C6 GPIO4-7, P4 GPIO2-5. Usable as GPIO, but then you lose external JTAG debugging. Built-in USB-JTAG on S3/C3/C6 still works.
- **Current:** about 20-40 mA per pin. Use a transistor or MOSFET for relays, motors and LED strips. Keep total draw within the board's LDO rating (Waveshare boards often use an 800 mA ME6217).
- **Voltage:** all GPIOs are 3.3 V only. 5 V signals need a level shifter or divider.

## I2C

- One bus can hold many devices, but every address must be unique. `wsesp.py pins <board> --use i2c@0x3C:oled` checks against the board's onboard devices.
- Onboard buses already have pull-ups. Don't add strong extra pull-ups.
- Common onboard addresses: CST816S 0x15, GT911 0x5D (or 0x14), FT3168/FT6336 0x38, AXP2101 0x34, PCF85063 0x51, ES8311 0x18, QMI8658 0x6A/0x6B, TCA9554 0x20-0x27, CH422G 0x20-0x27 + 0x30-0x3F.
