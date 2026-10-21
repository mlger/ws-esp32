# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [SemVer](https://semver.org/).

## [Unreleased]

### Added
- `wsesp.py new <board> --framework idf --with display`: generates working LCD + touch + LVGL 9 code (esp_lcd + esp_lvgl_port) for SPI-display boards: ESP32-S3-Touch-LCD-1.28 (GC9A01 + CST816S), ESP32-S3-LCD-1.47 and ESP32-C6-LCD-1.47 (ST7789).
- `panel_init` field in board profiles (color order, inversion, offsets, mirroring, SPI clock).
- `wsesp.py show` reports whether display code can be generated, and why not.
- CI builds the display projects for every supported board.

## [0.1.0] - 2026-10-21

### Added
- `ws-esp32` skill with workflows for setup, new projects, build/flash/monitor, display bring-up, troubleshooting and adding boards.
- Board profiles: ESP32-S3-Touch-LCD-1.28, ESP32-S3-Touch-LCD-4.3, ESP32-S3-LCD-1.47, ESP32-S3-Touch-AMOLED-1.8 (partial), ESP32-S3-Zero, ESP32-C6-LCD-1.47, ESP32-C6-Zero (partial).
- Chip rules for ESP32, ESP32-S3, ESP32-C3, ESP32-C6.
- `wsesp.py` CLI: `boards`, `show`, `pins`, `header`, `new`, `doctor`, `ports`, `validate-data`.
- ESP-IDF, Arduino and PlatformIO project templates.
- CI: tests on Linux/Windows/macOS, plus firmware builds for every board.
