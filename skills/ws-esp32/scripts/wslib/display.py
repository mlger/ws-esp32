"""Generate ESP-IDF display (+ touch) + LVGL code for boards whose display data is complete.

Supported:
  spi    - ST7789, GC9A01 (+ CST816S touch)
  rgb565 - ST7262-style RGB panels with a CH422G expander (+ GT911 touch)
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

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
GT911 = ("espressif/esp_lcd_touch_gt911", "^1.2")
LVGL_DEPS = [("espressif/esp_lvgl_port", "^2.4"), ("lvgl/lvgl", "^9.2")]
# RGB565 data bus order D0..D15 used by esp_lcd: blue, green, red (LSB first).
RGB_DATA_ORDER = ["b3", "b4", "b5", "b6", "b7", "g2", "g3", "g4", "g5", "g6", "g7", "r3", "r4", "r5", "r6", "r7"]
RGB_SDKCONFIG = [
    "# RGB panel: keep PSRAM bandwidth for the frame buffers",
    "CONFIG_SPIRAM_FETCH_INSTRUCTIONS=y",
    "CONFIG_SPIRAM_RODATA=y",
    "CONFIG_ESP32S3_DATA_CACHE_LINE_64B=y",
]


class UnsupportedDisplay(Exception):
    pass


def _periph(board: Dict[str, Any], pid: str) -> Optional[Dict[str, Any]]:
    return next((p for p in board["peripherals"] if p["id"] == pid), None)


def _is_gpio(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _is_exio(v: Any) -> bool:
    return isinstance(v, str) and v.startswith("EXIO")


def display_support(board: Dict[str, Any]) -> Tuple[bool, str]:
    try:
        plan = display_plan(board)
    except UnsupportedDisplay as e:
        return False, str(e)
    touch = f" + {plan['touch_part']} touch" if plan["touch"] else ""
    return True, f"{plan['panel_part']} over {plan['kind'].upper()}{touch}"


def display_plan(board: Dict[str, Any]) -> Dict[str, Any]:
    """Work out what display code to generate, or raise UnsupportedDisplay with the reason."""
    lcd = _periph(board, "lcd")
    if not lcd or lcd.get("kind") != "display":
        raise UnsupportedDisplay("board has no display")
    if not lcd.get("resolution"):
        raise UnsupportedDisplay("display resolution is unknown")
    interface = lcd.get("interface")
    if interface == "spi":
        return _plan_spi(board, lcd)
    if interface == "rgb565":
        return _plan_rgb(board, lcd)
    raise UnsupportedDisplay(f"{interface} displays are not generated yet (SPI and RGB only); "
                             "see references/workflows/display-bringup.md")


def _plan_spi(board: Dict[str, Any], lcd: Dict[str, Any]) -> Dict[str, Any]:
    part = (lcd.get("part") or "").upper()
    key = next((k for k in PANELS if part.startswith(k)), None)
    if not key:
        raise UnsupportedDisplay(f"no generator for controller {lcd.get('part')}")
    pins = lcd.get("pins", {})
    for sig in ("cs", "dc"):
        if not _is_gpio(pins.get(sig)):
            raise UnsupportedDisplay(f"lcd.{sig} pin is unknown or not a GPIO")
    if pins.get("bl") is not None and not _is_gpio(pins["bl"]):
        raise UnsupportedDisplay("SPI display with backlight on an IO expander is not generated yet")
    bus = _periph(board, lcd.get("bus", ""))
    if not bus or not all(_is_gpio(bus["pins"].get(s)) for s in ("sclk", "mosi")):
        raise UnsupportedDisplay("SPI bus pins are unknown")

    init = {"rgb_order": "rgb", "invert": True, "mirror_x": False, "mirror_y": False, "swap_xy": False,
            "gap": [0, 0], "pclk_mhz": 40, "verified": False, "source": "generic defaults"}
    init.update(lcd.get("panel_init") or {})

    touch = None
    tp = _periph(board, "touch")
    if tp and tp.get("part", "").upper() in TOUCH:
        i2c = _periph(board, tp.get("bus", ""))
        ok_bus = i2c and all(_is_gpio(i2c["pins"].get(s)) for s in ("sda", "scl"))
        ok_pins = all(v is None or _is_gpio(v) for v in tp.get("pins", {}).values())
        if ok_bus and ok_pins:
            touch = TOUCH[tp["part"].upper()]
    return {"kind": "spi", "panel": PANELS[key], "panel_part": lcd["part"], "init": init,
            "touch": touch, "touch_part": tp.get("part") if touch else None}


def _plan_rgb(board: Dict[str, Any], lcd: Dict[str, Any]) -> Dict[str, Any]:
    if board["psram_mode"] == "none":
        raise UnsupportedDisplay("RGB panels need PSRAM for frame buffers")
    timing = lcd.get("rgb_timing")
    if not timing:
        raise UnsupportedDisplay("RGB timings are unknown (add lcd.rgb_timing from the vendor demo)")
    pins = lcd.get("pins", {})
    missing = [s for s in RGB_DATA_ORDER + ["hsync", "vsync", "de", "pclk"] if not _is_gpio(pins.get(s))]
    if missing:
        raise UnsupportedDisplay(f"RGB pins unknown: {', '.join(missing)}")
    exp = _periph(board, "expander")
    if not exp or (exp.get("part") or "").upper() != "CH422G":
        raise UnsupportedDisplay("RGB generator only supports boards with a CH422G expander so far")
    if not (_is_exio(pins.get("bl")) and _is_exio(pins.get("rst"))):
        raise UnsupportedDisplay("expected backlight and reset on the CH422G")
    i2c = _periph(board, exp.get("bus", ""))
    if not i2c or not all(_is_gpio(i2c["pins"].get(s)) for s in ("sda", "scl")):
        raise UnsupportedDisplay("I2C pins are unknown")

    touch, tp = None, _periph(board, "touch")
    if tp and (tp.get("part") or "").upper() == "GT911":
        tpins = tp.get("pins", {})
        if _is_gpio(tpins.get("int")) and _is_exio(tpins.get("rst")):
            touch = {"component": GT911}
    return {"kind": "rgb", "panel": None, "panel_part": lcd.get("part", "RGB panel"), "timing": timing,
            "pins": pins, "touch": touch, "touch_part": "GT911" if touch else None}


def _bool(v: Any) -> str:
    return "true" if v else "false"


def render_display(board: Dict[str, Any], templates: Dict[str, str]) -> Dict[str, str]:
    """templates: {'spi': display.c.tmpl text, 'rgb': display_rgb.c.tmpl text}"""
    plan = display_plan(board)
    touch = plan["touch"]
    values = {
        "BOARD_NAME": board["name"],
        "PANEL_PART": plan["panel_part"],
        "TOUCH_TITLE": f" + {plan['touch_part']} touch" if touch else "",
        "HAS_TOUCH": "1" if touch else "0",
    }
    if plan["kind"] == "spi":
        init = plan["init"]
        values.update({
            "INIT_SOURCE": init["source"],
            "INIT_VERIFIED": "yes" if init.get("verified") else "no",
            "PANEL_INCLUDE": plan["panel"]["include"],
            "PANEL_NEW": plan["panel"]["new"],
            "TOUCH_INCLUDE": touch["include"] if touch else "",
            "TOUCH_NEW": touch["new"] if touch else "",
            "TOUCH_IO_CONFIG": touch["io_config"] if touch else "{0}",
            "PCLK_MHZ": str(init["pclk_mhz"]),
            "RGB_ORDER": "LCD_RGB_ELEMENT_ORDER_BGR" if init["rgb_order"] == "bgr" else "LCD_RGB_ELEMENT_ORDER_RGB",
            "INVERT": _bool(init["invert"]),
            "GAP_X": str(init["gap"][0]),
            "GAP_Y": str(init["gap"][1]),
            "SWAP_XY": _bool(init["swap_xy"]),
            "MIRROR_X": _bool(init["mirror_x"]),
            "MIRROR_Y": _bool(init["mirror_y"]),
        })
        code = templates["spi"]
    else:
        t = plan["timing"]
        values.update({
            "TIMING_SOURCE": t["source"],
            "PCLK_HZ": str(t["pclk_hz"]),
            "HPW": str(t["hsync_pulse_width"]), "HBP": str(t["hsync_back_porch"]),
            "HFP": str(t["hsync_front_porch"]), "VPW": str(t["vsync_pulse_width"]),
            "VBP": str(t["vsync_back_porch"]), "VFP": str(t["vsync_front_porch"]),
            "PCLK_NEG": "1" if t.get("pclk_active_neg", True) else "0",
            "BOUNCE_LINES": str(t.get("bounce_buffer_lines", 10)),
            "DATA_PINS": ", ".join(f"WS_LCD_{s.upper()}" for s in RGB_DATA_ORDER),
            "EXIO_EXTRA": "EXIO_BIT(5) /* USB_SEL high, as in Waveshare's demo (0x2C) */",
        })
        code = templates["rgb"]
    for k, v in values.items():
        code = code.replace("{{" + k + "}}", v)
    header = ('#pragma once\n\n#include "esp_err.h"\n\n'
              "/* Start the LCD, touch and LVGL, and show a demo screen. */\n"
              "esp_err_t display_start(void);\n")
    return {"main/display.c": code, "main/display.h": header}


def display_sdkconfig(board: Dict[str, Any]) -> list:
    return RGB_SDKCONFIG if display_plan(board)["kind"] == "rgb" else []


def display_dependencies(board: Dict[str, Any]) -> Dict[str, str]:
    plan = display_plan(board)
    deps = dict(LVGL_DEPS)
    if plan["panel"] and plan["panel"]["component"]:
        name, ver = plan["panel"]["component"]
        deps[name] = ver
    if plan["touch"]:
        name, ver = plan["touch"]["component"]
        deps[name] = ver
    return deps


ARDUINO_GFX = {"ST7789": "Arduino_ST7789", "GC9A01": "Arduino_GC9A01"}


def render_arduino_display(board: Dict[str, Any], template: str) -> str:
    """Arduino_GFX sketch for SPI panels. Raises UnsupportedDisplay otherwise."""
    plan = display_plan(board)
    if plan["kind"] != "spi":
        raise UnsupportedDisplay("Arduino display code is only generated for SPI panels; "
                                 "use --framework idf for RGB panels")
    init = plan["init"]
    part = plan["panel_part"].upper()
    cls = next(v for k, v in ARDUINO_GFX.items() if part.startswith(k))
    gx, gy = init["gap"]
    ctor = (f"new {cls}(bus, WS_LCD_RST, 0 /* rotation */, {_bool(init['invert'])} /* ips */, "
            f"WS_LCD_H_RES, WS_LCD_V_RES, {gx}, {gy}, {gx}, {gy})")
    values = {"BOARD_NAME": board["name"], "GFX_CTOR": ctor, "INIT_SOURCE": init["source"],
              "INIT_VERIFIED": "yes" if init.get("verified") else "no"}
    for k, v in values.items():
        template = template.replace("{{" + k + "}}", v)
    return template
