# Troubleshooting

Always get the **full serial log from reset** (`idf.py monitor`, then press RESET) before changing code. The first lines (`rst:`, `boot:`) explain most boot problems.

## Connection and flashing

| Message / symptom | Cause | Fix |
|---|---|---|
| No port appears | Charge-only cable, bad hub, missing driver, or a crashed app on a native-USB board | Try another cable or a direct port. Run `wsesp.py ports`. Enter download mode (see `build-flash-monitor.md`). |
| Port disappears right after flashing (native USB) | App reuses GPIO19/20 (S3) or 12/13 (C6), enters deep sleep, or crashes early | Enter download mode manually and flash a known-good app (the starter project) |
| `Failed to connect ... No serial data received` | Board not in download mode, wrong port, something else has the port open | Close other monitors. Use BOOT + RESET. Lower the baud: `-b 115200` |
| `A fatal error occurred: Invalid head of packet` | Noisy USB or wrong port | Different cable or port, lower baud |
| Permission denied `/dev/ttyACM0` | Linux group | `sudo usermod -aG dialout $USER`, then log in again |
| `Wrong --chip argument?` / chip mismatch | Project target doesn't match the board | `idf.py set-target <chip from profile>` |

## Boot problems

| Log line | Cause | Fix |
|---|---|---|
| `invalid header: 0xffffffff` repeating | Flash is empty or the app was written to the wrong offset | Flash the full project (bootloader + partition table + app) |
| `Brownout detector was triggered` | Weak USB supply or current spikes (Wi-Fi TX, backlight, motors) | Better supply or cable. Don't power motors or LED strips from the board's 3V3 |
| `quad_psram: PSRAM ID read error` / `PSRAM init failed` | PSRAM mode doesn't match the hardware (octal vs quad) | Use the profile's `psram_mode`: `CONFIG_SPIRAM_MODE_OCT` for R8/N16R8, `QUAD` for R2 |
| `Detected size(4096k) smaller than the size in the binary image header(16384k)` | Flash size setting too big | Set flash size to the profile's `flash_mb` |
| Stuck in download mode (`waiting for download`) | A strapping pin is held at reset (GPIO0/GPIO9 low, or GPIO46/45/3 on S3) | Disconnect external hardware from strapping pins, then run `wsesp.py pins` |
| `rst:0xc (RTC_SW_CPU_RST)` loops after `Guru Meditation` | App crash | Decode the backtrace (see below) |
| `Task watchdog got triggered` | A task loops without yielding (often an LVGL loop or a busy-wait) | Add `vTaskDelay`, or move heavy work to its own task |
| `***ERROR*** A stack overflow in task X` | Stack too small (LVGL, TLS and JSON are common) | Increase the stack in `xTaskCreate`, or the main task stack (`CONFIG_ESP_MAIN_TASK_STACK_SIZE`) |

## Crash decoding

`Guru Meditation Error: Core 0 panic'ed (LoadProhibited)` usually means a NULL or invalid pointer. `StoreProhibited` is a write through a bad pointer. `InstrFetchProhibited` is a bad function pointer or a corrupted stack.

Decode the backtrace to get the file and line. `idf.py monitor` does this by itself. For a saved log, run `python scripts/wsesp.py decode build/<app>.elf crash.log --board <id>`, which finds the right addr2line for the chip. Read the code at that line before suggesting a fix.

## Arduino-specific

| Symptom | Fix |
|---|---|
| `Serial.print` shows nothing on a native USB board | Set USB CDC On Boot: Enabled (`CDCOnBoot=cdc`). Add `delay()` after `Serial.begin` |
| `PSRAM not detected` | Tools > PSRAM: "OPI PSRAM" for R8 / N16R8, "QSPI PSRAM" for R2 |
| Library compiles on 2.x but not 3.x (or the reverse) | API changes (`ledcSetup`/`ledcAttachPin` became `ledcAttach`, timer API, `neopixelWrite` became `rgbLedWrite`). Match `software.arduino_core` |
| Sketch too big | Tools > Partition Scheme, for example "16M Flash (3MB APP/9.9MB FATFS)" |

## Display and touch

See the symptom table in `display-bringup.md`.

## Wi-Fi

- ADC2 readings break when Wi-Fi is on (ESP32, S3). Move the sensor to an ADC1 pin.
- Weak signal: keep the ceramic antenna clear of metal, the case wall, and your hand.
- C6 supports Wi-Fi 6 on 2.4 GHz only. No ESP32 joins 5 GHz networks (except C5).
