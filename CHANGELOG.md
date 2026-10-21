# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [SemVer](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-10-21

First release.

### Skill
- `ws-esp32` skill with workflows for toolchain setup, new projects, build/flash/monitor, display bring-up, troubleshooting and adding boards.
- 11 board profiles: ESP32-S3-Touch-LCD-1.28, -2.8, -4.3, -7, ESP32-S3-LCD-1.47, ESP32-S3-Touch-AMOLED-1.8, ESP32-S3-ETH, ESP32-S3-Zero, ESP32-C6-LCD-1.47, ESP32-C6-Zero, ESP32-C3-Zero. Every pin cites its source.
- Chip rules for ESP32, ESP32-S3, ESP32-C3, ESP32-C6.
- JSON Schema for board profiles.

### CLI (`wsesp.py`)
- `boards`, `show`, `pins`, `header`, `new`, `doctor`, `ports`, `detect`, `decode`, `validate-data`.
- `new` generates ESP-IDF, Arduino and PlatformIO projects.
- `new --with display`: screen + touch + LVGL 9 code for SPI panels (ST7789, GC9A01 + CST816S) and RGB panels with a CH422G expander (ST7262 + GT911) on ESP-IDF, and Arduino_GFX sketches for SPI panels.
- `new --with devcontainer`: VS Code dev container for the generated project.

### Claude Code plugin
- Safety hook that asks before eFuse, erase-flash, flash-encryption and secure-boot commands.
- `/esp-new`, `/esp-flash` and `/esp-doctor` commands.

### Project
- Evals (`evals/evals.json`, `tools/run_evals.py`).
- CI: tests on Linux/Windows/macOS; firmware builds for every board with ESP-IDF (tested + latest), Arduino and PlatformIO; display builds; weekly scheduled run; Dependabot.
- Docs site with a pinout page per board, built from the profiles.
- Dev container, pre-commit config, issue templates including a hardware test report.
