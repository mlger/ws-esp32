# Display, touch and LVGL bring-up

## Generated code (preferred)

For boards where `wsesp.py show <board>` reports "Display codegen: yes", generate a working project instead of writing display code by hand:

```bash
python scripts/wsesp.py new <board> --framework idf --with display --name ui --out ./ui
```

This adds `main/display.c` (panel driver, optional touch, esp_lvgl_port, LVGL 9 demo screen) and turns on the needed components in `idf_component.yml`.

- **SPI panels** (ST7789, GC9A01, optional CST816S touch): 1.28", 1.47" S3/C6, 2.8".
- **RGB panels with a CH422G expander** (4.3", 7"): timings come from the profile's `rgb_timing` (copied from Waveshare's demo). The code brings up the CH422G (backlight, LCD reset, GT911 reset sequence), uses two PSRAM frame buffers with a bounce buffer, and adds the PSRAM XIP options to `sdkconfig.defaults`.
- **Arduino** (`--framework arduino --with display`): Arduino_GFX sketch for SPI panels. Install the "GFX Library for Arduino" library first. The panel settings (`LCD_INVERT`, `LCD_RGB_ORDER`, `LCD_GAP_X/Y`, `LCD_MIRROR_*`) are `#define`s at the top of `display.c` and come from the profile's `panel_init`. If `panel_init.verified` is false, tell the user the picture may need one of those flipped (see the symptom table below). Once they confirm what works, update the profile.

Not generated yet: QSPI AMOLED (SH8601), CST328 touch, RGB panels on Arduino, and PlatformIO. For those, use the manual steps below.

## Manual bring-up

Bring the display up in stages. Get each stage working before starting the next:

1. **Backlight on.** The starter project already does this. On the 4.3" the backlight is on CH422G EXIO2, so the expander has to be set up first. The AMOLED has no backlight pin; brightness is register 0x51.
2. **Panel fills a solid color** with `esp_lcd_panel_draw_bitmap` (no LVGL yet).
3. **LVGL label shows up**, through `esp_lvgl_port`.
4. **Touch reports coordinates** (log them before wiring them into LVGL).

## Driver map

| Controller | Interface | Boards | ESP-IDF driver |
|---|---|---|---|
| ST7789 | SPI | S3-LCD-1.47, C6-LCD-1.47 | built-in `esp_lcd_new_panel_st7789` |
| GC9A01 | SPI | S3-Touch-LCD-1.28 | `espressif/esp_lcd_gc9a01` |
| SH8601 | QSPI | S3-Touch-AMOLED-1.8 | `espressif/esp_lcd_sh8601` |
| ST7262 (RGB, no init cmds) | RGB565 parallel | S3-Touch-LCD-4.3 | built-in `esp_lcd_new_rgb_panel` |
| CST816S / GT911 / FT3168 | I2C touch | see profiles | `espressif/esp_lcd_touch_cst816s`, `esp_lcd_touch_gt911`, FT3168 is FT5x06-compatible (`esp_lcd_touch_ft5x06`) - verify |
| LVGL glue | - | all | `espressif/esp_lvgl_port` (2.x supports LVGL 8 and 9) |

Add components with `idf.py add-dependency "espressif/esp_lcd_gc9a01^2"` (check the current major version on components.espressif.com), or uncomment them in the generated `idf_component.yml`.

## SPI panel skeleton (ESP-IDF >= 5.1)

```c
#include "driver/spi_master.h"
#include "esp_lcd_panel_io.h"
#include "esp_lcd_panel_ops.h"
#include "esp_lcd_panel_vendor.h"
#include "board_pins.h"

static esp_lcd_panel_handle_t lcd_init(esp_lcd_panel_io_handle_t *io_out)
{
    spi_bus_config_t bus = {
        .sclk_io_num = WS_SPI_SCLK,
        .mosi_io_num = WS_SPI_MOSI,
        .miso_io_num = -1,
        .quadwp_io_num = -1,
        .quadhd_io_num = -1,
        .max_transfer_sz = WS_LCD_H_RES * 40 * sizeof(uint16_t),
    };
    ESP_ERROR_CHECK(spi_bus_initialize(SPI2_HOST, &bus, SPI_DMA_CH_AUTO));

    esp_lcd_panel_io_spi_config_t io_cfg = {
        .dc_gpio_num = WS_LCD_DC,
        .cs_gpio_num = WS_LCD_CS,
        .pclk_hz = 40 * 1000 * 1000,
        .lcd_cmd_bits = 8,
        .lcd_param_bits = 8,
        .spi_mode = 0,
        .trans_queue_depth = 10,
    };
    ESP_ERROR_CHECK(esp_lcd_new_panel_io_spi((esp_lcd_spi_bus_handle_t)SPI2_HOST, &io_cfg, io_out));

    esp_lcd_panel_dev_config_t panel_cfg = {
        .reset_gpio_num = WS_LCD_RST,
        .rgb_ele_order = LCD_RGB_ELEMENT_ORDER_RGB,
        .bits_per_pixel = 16,
    };
    esp_lcd_panel_handle_t panel;
    ESP_ERROR_CHECK(esp_lcd_new_panel_st7789(*io_out, &panel_cfg, &panel)); /* or esp_lcd_new_panel_gc9a01 */
    ESP_ERROR_CHECK(esp_lcd_panel_reset(panel));
    ESP_ERROR_CHECK(esp_lcd_panel_init(panel));
    ESP_ERROR_CHECK(esp_lcd_panel_invert_color(panel, true)); /* IPS panels usually need this */
    /* 172x320 ST7789 panels: esp_lcd_panel_set_gap(panel, 34, 0); */
    ESP_ERROR_CHECK(esp_lcd_panel_disp_on_off(panel, true));
    return panel;
}
```

On the C6-LCD-1.47 the SD card shares this SPI bus. Initialize the bus once and give each device its own CS.

## LVGL via esp_lvgl_port

```c
#include "esp_lvgl_port.h"

const lvgl_port_cfg_t lvgl_cfg = ESP_LVGL_PORT_INIT_CONFIG();
ESP_ERROR_CHECK(lvgl_port_init(&lvgl_cfg));

const lvgl_port_display_cfg_t disp_cfg = {
    .io_handle = io,
    .panel_handle = panel,
    .buffer_size = WS_LCD_H_RES * 40,
    .double_buffer = true,
    .hres = WS_LCD_H_RES,
    .vres = WS_LCD_V_RES,
    .flags = { .buff_dma = true, .swap_bytes = true },
};
lvgl_port_add_disp(&disp_cfg);

lvgl_port_lock(0);                 /* every LVGL call outside LVGL callbacks needs the lock */
lv_obj_t *label = lv_label_create(lv_scr_act());   /* LVGL 9: lv_screen_active() */
lv_label_set_text(label, WS_BOARD_NAME);
lv_obj_center(label);
lvgl_port_unlock();
```

Buffers: on boards without PSRAM (C6) keep `buffer_size` around 1/10 of the screen, in internal DMA RAM. On S3 boards with PSRAM, an RGB panel's frame buffers go in PSRAM, but SPI DMA buffers must stay in internal RAM.

## RGB panel (4.3")

- Take the timing values (pclk, porches, pulse widths, polarity) from Waveshare's demo for that exact board revision. They are not on the wiki, so don't guess them.
- Use `num_fbs = 2` with `bounce_buffer_size_px = 10 * WS_LCD_H_RES` to stop drift and tearing while Wi-Fi or flash writes run. Also set:
  ```
  CONFIG_SPIRAM_FETCH_INSTRUCTIONS=y
  CONFIG_SPIRAM_RODATA=y
  CONFIG_ESP32S3_DATA_CACHE_LINE_64B=y
  ```
- Turn the backlight and touch reset on through the CH422G first. Waveshare's `ESP32_IO_Expander` (Arduino) or demo driver (IDF) handles it.

## Common symptoms

| Symptom | Likely cause |
|---|---|
| Backlight on, screen black | Wrong reset pin/sequence, `disp_on_off` never called, wrong CS/DC |
| Colors inverted (white looks black) | Toggle `esp_lcd_panel_invert_color` |
| Red and blue swapped | `rgb_ele_order` RGB vs BGR |
| Colors look like noise or stripes | RGB565 byte order: `swap_bytes` (LVGL 8: `LV_COLOR_16_SWAP`) |
| Image shifted or garbage at one edge | Missing `set_gap` offset (172-wide ST7789: x=34) |
| Rotated or mirrored | `swap_xy` / `mirror` on both the panel and the touch config |
| Touch works but coordinates are off | Touch `x_max/y_max` and swap/mirror flags don't match the panel |
| Touch never responds | I2C address (scan the bus), reset line on the IO expander not released, INT pin wrong |

## LVGL 8 vs 9 cheat sheet

| LVGL 8 | LVGL 9 |
|---|---|
| `lv_disp_t`, `lv_disp_drv_t` | `lv_display_t` (no driver struct) |
| `lv_scr_act()` | `lv_screen_active()` |
| `lv_img_*`, `lv_btn_*` | `lv_image_*`, `lv_button_*` |
| `lv_obj_clear_flag` | `lv_obj_remove_flag` |
| `lv_indev_drv_t` + `lv_indev_drv_register` | `lv_indev_create()` + setters |
| `LV_COLOR_16_SWAP` in `lv_conf.h` | swap in the flush callback (`lv_draw_sw_rgb565_swap`) |

Waveshare demos mostly use LVGL 8.3/8.4. Don't mix code from the two versions. Check which `lvgl` version `dependencies.lock` (IDF) or the library manager resolved.
