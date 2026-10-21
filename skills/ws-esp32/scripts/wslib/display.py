"""Generate ESP-IDF display (+ touch) + LVGL code for boards whose display data is complete."""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

# Display controllers we can generate code for (SPI only for now).
PANELS = {
    "ST7789": {"include": "", "new": "esp_lcd_new_panel_st7789", "component": None},
    "GC9A01": {"include": '#include "esp_lcd_gc9a01.h"', "new": "esp_lcd_new_panel_gc9a01",
               "component": ("espressif/esp_lcd_gc9a01", "^2")},
}
TOUCH = {
    "CST816S": {"include": '#include "esp_lcd_touch_cst816s.h"', "new": "esp_lcd_touch_new_i2c_cst816s",
                "io_config": "ESP_LCD_TOUCH_IO_I2C_CST816S_CONFIG()",
                "component": ("espressif/esp_lcd_touch_cst816s", "^1.1")},
}
LVGL_DEPS = [("espressif/esp_lvgl_port", "^2.4"), ("lvgl/lvgl", "^9.2")]


class UnsupportedDisplay(Exception):
    pass


def _periph(board: Dict[str, Any], pid: str) -> Optional[Dict[str, Any]]:
    return next((p for p in board["peripherals"] if p["id"] == pid), None)


def _panel_key(part: str) -> Optional[str]:
    part = (part or "").upper()
    return next((k for k in PANELS if part.startswith(k)), None)


def _is_gpio(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def display_support(board: Dict[str, Any]) -> Tuple[bool, str]:
    try:
        plan = display_plan(board)
    except UnsupportedDisplay as e:
        return False, str(e)
    touch = f" + {plan['touch_part']} touch" if plan["touch"] else ""
    return True, f"{plan['panel_part']} over SPI{touch}"


def display_plan(board: Dict[str, Any]) -> Dict[str, Any]:
    """Work out what display code to generate, or raise UnsupportedDisplay with the reason."""
    lcd = _periph(board, "lcd")
    if not lcd or lcd.get("kind") != "display":
        raise UnsupportedDisplay("board has no display")
    if lcd.get("interface") != "spi":
        raise UnsupportedDisplay(f"{lcd.get('interface')} displays are not generated yet "
                                 "(SPI only); see references/workflows/display-bringup.md")
    key = _panel_key(lcd.get("part", ""))
    if not key:
        raise UnsupportedDisplay(f"no generator for controller {lcd.get('part')}")
    pins = lcd.get("pins", {})
    for sig in ("cs", "dc"):
        if not _is_gpio(pins.get(sig)):
            raise UnsupportedDisplay(f"lcd.{sig} pin is unknown or not a GPIO")
    if pins.get("bl") is not None and not _is_gpio(pins["bl"]):
        raise UnsupportedDisplay("backlight is on an IO expander; not generated yet")
    bus = _periph(board, lcd.get("bus", ""))
    if not bus or not all(_is_gpio(bus["pins"].get(s)) for s in ("sclk", "mosi")):
        raise UnsupportedDisplay("SPI bus pins are unknown")
    if not lcd.get("resolution"):
        raise UnsupportedDisplay("display resolution is unknown")

    init = {"rgb_order": "rgb", "invert": True, "mirror_x": False, "mirror_y": False, "swap_xy": False,
            "gap": [0, 0], "pclk_mhz": 40, "verified": False, "source": "generic defaults"}
    init.update(lcd.get("panel_init") or {})

    touch_plan = None
    tp = _periph(board, "touch")
    if tp and tp.get("part", "").upper() in TOUCH:
        i2c = _periph(board, tp.get("bus", ""))
        tpins = tp.get("pins", {})
        ok_bus = i2c and all(_is_gpio(i2c["pins"].get(s)) for s in ("sda", "scl"))
        ok_pins = all(v is None or _is_gpio(v) for v in tpins.values())
        if ok_bus and ok_pins:
            touch_plan = TOUCH[tp["part"].upper()]
    return {"panel": PANELS[key], "panel_part": lcd["part"], "init": init,
            "touch": touch_plan, "touch_part": tp.get("part") if touch_plan else None}


def render_display(board: Dict[str, Any], template: str) -> Dict[str, str]:
    plan = display_plan(board)
    init, touch = plan["init"], plan["touch"]
    values = {
        "BOARD_NAME": board["name"],
        "PANEL_PART": plan["panel_part"],
        "TOUCH_TITLE": f" + {plan['touch_part']} touch" if touch else "",
        "INIT_SOURCE": init["source"],
        "INIT_VERIFIED": "yes" if init.get("verified") else "no",
        "PANEL_INCLUDE": plan["panel"]["include"],
        "PANEL_NEW": plan["panel"]["new"],
        "HAS_TOUCH": "1" if touch else "0",
        "TOUCH_INCLUDE": touch["include"] if touch else "",
        "TOUCH_NEW": touch["new"] if touch else "",
        "TOUCH_IO_CONFIG": touch["io_config"] if touch else "{0}",
        "PCLK_MHZ": str(init["pclk_mhz"]),
        "RGB_ORDER": "LCD_RGB_ELEMENT_ORDER_BGR" if init["rgb_order"] == "bgr" else "LCD_RGB_ELEMENT_ORDER_RGB",
        "INVERT": "true" if init["invert"] else "false",
        "GAP_X": str(init["gap"][0]),
        "GAP_Y": str(init["gap"][1]),
        "SWAP_XY": "true" if init["swap_xy"] else "false",
        "MIRROR_X": "true" if init["mirror_x"] else "false",
        "MIRROR_Y": "true" if init["mirror_y"] else "false",
    }
    code = template
    for k, v in values.items():
        code = code.replace("{{" + k + "}}", v)
    header = ('#pragma once\n\n#include "esp_err.h"\n\n'
              "/* Start the LCD, touch and LVGL, and show a demo screen. */\n"
              "esp_err_t display_start(void);\n")
    return {"main/display.c": code, "main/display.h": header}


def display_dependencies(board: Dict[str, Any]) -> Dict[str, str]:
    plan = display_plan(board)
    deps = dict(LVGL_DEPS)
    if plan["panel"]["component"]:
        name, ver = plan["panel"]["component"]
        deps[name] = ver
    if plan["touch"]:
        name, ver = plan["touch"]["component"]
        deps[name] = ver
    return deps
