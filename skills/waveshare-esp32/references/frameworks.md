# Choosing a framework

| | ESP-IDF | Arduino-ESP32 | PlatformIO |
|---|---|---|---|
| Best for | Products, LVGL GUIs, RGB/QSPI displays, low power, OTA, security | Fast prototypes, huge library ecosystem | Multi-board repos, VS Code users, CI |
| Language | C / C++ | C++ (Arduino API) | Either (`framework = arduino` or `espidf`) |
| Config | `sdkconfig` / `menuconfig` | Board menu or FQBN options | `platformio.ini` |
| Display stack | `esp_lcd` + `esp_lvgl_port` | `ESP32_Display_Panel`, `Arduino_GFX`, TFT_eSPI | Same as the framework underneath |
| Waveshare demos | Most boards | Most boards | Few. Port from the Arduino demos |
| Pitfalls | Version changes between 5.x minors | 2.x vs 3.x API break | Official platform is still on Arduino 2.x, so use pioarduino for 3.x |

Recommendation:
- If the user is new and only wants something on screen fast, use **Arduino** with the board's tested core version.
- For anything going into a product, or with an RGB/QSPI display, use **ESP-IDF**.
- **Arduino as an ESP-IDF component** (`espressif/arduino-esp32` in `idf_component.yml`) gives Arduino libraries plus full `sdkconfig` control. It works, but the two versions must match. Check the arduino-esp32 docs for the supported IDF version.

MicroPython and CircuitPython: Waveshare ships custom MicroPython firmware for some boards. This skill doesn't generate MicroPython projects, but the board profiles (pins, I2C addresses) still apply.
