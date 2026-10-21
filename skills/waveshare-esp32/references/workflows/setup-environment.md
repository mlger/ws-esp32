# Set up the toolchain

Start by running `python scripts/wsesp.py doctor`. It shows which tools are installed, their versions, and the serial ports it can see. Then install only what is missing for the framework the user picked (see `../frameworks.md`).

Show install commands to the user. Don't run installers without their approval.

## ESP-IDF

**Version:** use the `software.esp_idf` version in the board profile when there is one. Otherwise use the newest stable release from https://github.com/espressif/esp-idf/releases. Waveshare demos are written for 5.x, so a new major release may need code changes. Pin the version per project (record it in the project README or CI).

| OS | Recommended way |
|---|---|
| Windows | Espressif's ESP-IDF Installation Manager (EIM) or the VS Code "ESP-IDF" extension. Use the "ESP-IDF PowerShell" shortcut it creates. |
| macOS / Linux | EIM, or the manual git install below. |
| Any (CI, reproducible) | Docker image `espressif/idf:<version>` |

Manual install (macOS/Linux):

```bash
mkdir -p ~/esp && cd ~/esp
git clone -b v5.5.2 --recursive https://github.com/espressif/esp-idf.git esp-idf-v5.5.2
cd esp-idf-v5.5.2 && ./install.sh esp32s3,esp32c6
. ./export.sh          # run in every new shell (or add an alias)
idf.py --version
```

Linux prerequisites (Debian/Ubuntu): `sudo apt install git wget flex bison gperf python3 python3-venv cmake ninja-build ccache libffi-dev libssl-dev dfu-util libusb-1.0-0`.

## Arduino

```bash
arduino-cli config init
arduino-cli config add board_manager.additional_urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
arduino-cli core update-index
arduino-cli core install esp32:esp32@3.0.7     # pick the board's software.arduino_core
```

Notes:
- ESP32-C6 needs core 3.x.
- ESP32-S3-Touch-LCD-1.28 demos target core 2.0.12. Its TFT_eSPI setup does not build on 3.x without changes.
- In the Arduino IDE, add the same URL under Preferences, then install "esp32 by Espressif Systems" from Boards Manager.

## PlatformIO

```bash
python -m pip install -U platformio
```

The official `espressif32` platform ships Arduino-ESP32 2.x. For 3.x (needed for C6 and most current Waveshare demos), use the community pioarduino platform. `wsesp.py new --framework pio` already sets this up.

## USB drivers and permissions

| Board USB | Shows up as | Driver |
|---|---|---|
| Native USB (S3/C3/C6) | `303A:1001` USB-Serial-JTAG. COMx / `/dev/ttyACM*` / `/dev/cu.usbmodem*` | None needed |
| CH343P bridge (1.28", 4.3" UART port) | `1A86:55D3`. COMx / `/dev/ttyACM*` / `/dev/cu.wchusbserial*` | Built in on Win 10+/macOS/Linux. If missing, install WCH's CH343SER driver. |

- **Linux:** `sudo usermod -aG dialout $USER` (Arch: `uucp`), then log out and back in. If ModemManager grabs the port, stop it or add a udev rule to ignore the device.
- **WSL2:** USB is not passed through by default. Use `usbipd-win`: `usbipd list`, `usbipd bind --busid <id>` (admin shell), `usbipd attach --wsl --busid <id>`. You can also build in WSL and flash from Windows.
- **Charge-only cables** are the most common cause of "no port". Try another cable before anything else.

## Docker / dev containers

Build in a container to get the same toolchain on every machine:

```bash
docker run --rm -v "$PWD":/project -w /project espressif/idf:v5.5.2 idf.py build
```

Flashing from a container only works on Linux hosts (`--device=/dev/ttyACM0`). On Windows or macOS, build in the container and flash from the host, either with `esptool` or by running `esp_rfc2217_server` on the host and `idf.py -p rfc2217://host.docker.internal:4000 flash` in the container.

## Verify

```bash
python scripts/wsesp.py doctor
python scripts/wsesp.py new <board> --framework idf --name hello && cd hello && idf.py build
```
