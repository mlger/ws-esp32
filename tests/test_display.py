import re

import pytest
from wslib.display import UnsupportedDisplay, display_dependencies, display_plan, display_support
from wslib.scaffold import plan_project

SUPPORTED = {"esp32-s3-touch-lcd-1.28", "esp32-s3-lcd-1.47", "esp32-c6-lcd-1.47", "esp32-s3-touch-lcd-4.3",
             "esp32-s3-touch-lcd-7", "esp32-s3-touch-lcd-2.8"}


def test_support_matrix(boards):
    assert {b for b in boards if display_support(boards[b])[0]} == SUPPORTED


@pytest.mark.parametrize("board_id,reason", [
    ("esp32-s3-touch-amoled-1.8", "qspi"),
    ("esp32-s3-zero", "no display"),
])
def test_unsupported_reasons(boards, board_id, reason):
    with pytest.raises(UnsupportedDisplay, match=reason):
        display_plan(boards[board_id])


def test_touch_only_on_1_28(boards):
    assert display_plan(boards["esp32-s3-touch-lcd-1.28"])["touch"] is not None
    assert display_plan(boards["esp32-c6-lcd-1.47"])["touch"] is None


def test_dependencies(boards):
    deps = display_dependencies(boards["esp32-s3-touch-lcd-1.28"])
    assert set(deps) == {"espressif/esp_lvgl_port", "lvgl/lvgl", "espressif/esp_lcd_gc9a01",
                         "espressif/esp_lcd_touch_cst816s"}
    assert "espressif/esp_lcd_gc9a01" not in display_dependencies(boards["esp32-c6-lcd-1.47"])


@pytest.mark.parametrize("board_id", sorted(SUPPORTED))
def test_generated_project(boards, chips, board_id):
    b = boards[board_id]
    files = plan_project(b, chips[b["chip"]], "idf", "app", with_display=True)
    code = files["main/display.c"]
    assert not re.search(r"\{\{[A-Z_]+\}\}", code)
    assert '"display.c"' in files["main/CMakeLists.txt"]
    assert "display_start()" in files["main/main.c"]
    assert "esp_lvgl_port" in files["main/idf_component.yml"]
    assert "# espressif/esp_lvgl_port" not in files["main/idf_component.yml"]


def test_gap_and_order(boards, chips):
    b = boards["esp32-s3-lcd-1.47"]
    code = plan_project(b, chips[b["chip"]], "idf", "app", with_display=True)["main/display.c"]
    assert "#define LCD_GAP_X       34" in code
    assert "LCD_RGB_ELEMENT_ORDER_RGB" in code


def test_display_not_for_pio(boards, chips):
    b = boards["esp32-s3-lcd-1.47"]
    with pytest.raises(ValueError):
        plan_project(b, chips[b["chip"]], "pio", "app", with_display=True)


def test_arduino_display(boards, chips):
    b = boards["esp32-s3-lcd-1.47"]
    ino = plan_project(b, chips[b["chip"]], "arduino", "ui", with_display=True)["ui/ui.ino"]
    assert "new Arduino_ST7789(bus, WS_LCD_RST, 0 /* rotation */, true /* ips */" in ino
    assert "WS_LCD_H_RES, WS_LCD_V_RES, 34, 0, 34, 0)" in ino
    b = boards["esp32-s3-touch-lcd-1.28"]
    assert "Arduino_GC9A01" in plan_project(b, chips[b["chip"]], "arduino", "ui", with_display=True)["ui/ui.ino"]
    b = boards["esp32-s3-touch-lcd-4.3"]
    with pytest.raises(UnsupportedDisplay, match="SPI"):
        plan_project(b, chips[b["chip"]], "arduino", "ui", with_display=True)


def test_without_display_unchanged(boards, chips):
    b = boards["esp32-s3-lcd-1.47"]
    files = plan_project(b, chips[b["chip"]], "idf", "app")
    assert "main/display.c" not in files
    assert "#define APP_HAS_DISPLAY" not in files["main/main.c"]
    assert files["main/CMakeLists.txt"].startswith('idf_component_register(SRCS "main.c"\n')


def test_rgb_project(boards, chips):
    b = boards["esp32-s3-touch-lcd-4.3"]
    files = plan_project(b, chips[b["chip"]], "idf", "app", with_display=True)
    code = files["main/display.c"]
    assert "esp_lcd_new_rgb_panel" in code and ".pclk_hz = 16000000" in code
    assert "WS_LCD_B3, WS_LCD_B4" in code and code.count("WS_LCD_R7") == 1
    assert "CONFIG_SPIRAM_FETCH_INSTRUCTIONS=y" in files["sdkconfig.defaults"]
    assert "espressif/esp_lcd_touch_gt911" in files["main/idf_component.yml"]


def test_rgb_needs_timing(boards):
    import copy
    b = copy.deepcopy(boards["esp32-s3-touch-lcd-4.3"])
    next(p for p in b["peripherals"] if p["id"] == "lcd").pop("rgb_timing")
    with pytest.raises(UnsupportedDisplay, match="timings"):
        display_plan(b)
