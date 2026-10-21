"""Check a user's planned pin usage against chip rules and the board profile."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .data import bus_reserved_addrs, chip_gpios, iter_pins, parse_addr_list

INPUT_FUNCS = {"gpio_in", "adc", "uart_rx", "spi_miso", "i2s_din", "button", "interrupt"}
OUTPUT_FUNCS = {"gpio_out", "pwm", "uart_tx", "spi_mosi", "spi_sclk", "spi_cs", "i2c_sda",
                "i2c_scl", "ws2812", "i2s_bclk", "i2s_ws", "i2s_dout", "i2s_mclk", "onewire",
                "can_tx", "rmt_tx"}
BIDIR_FUNCS = {"gpio", "can_rx", "rmt_rx", "touch"}
KNOWN_FUNCS = INPUT_FUNCS | OUTPUT_FUNCS | BIDIR_FUNCS


def _finding(level: str, msg: str, gpio: Optional[int] = None, label: str = "") -> Dict[str, Any]:
    return {"level": level, "gpio": gpio, "label": label, "message": msg}


def board_pin_owners(board: Dict[str, Any]) -> Dict[int, List[Dict[str, Any]]]:
    owners: Dict[int, List[Dict[str, Any]]] = {}
    for p, sig, val in iter_pins(board):
        if isinstance(val, int) and not isinstance(val, bool):
            owners.setdefault(val, []).append({"peripheral": p["id"], "part": p.get("part"),
                                               "signal": sig, "soft": bool(p.get("soft"))})
    return owners


def parse_use(spec: str) -> Dict[str, Any]:
    """Parse CLI specs: '15=gpio_out:relay' or 'i2c@0x3C:oled'."""
    if "@" in spec:
        bus, rest = spec.split("@", 1)
        addr, _, label = rest.partition(":")
        return {"bus": bus, "addr": addr, "label": label}
    gpio, _, rest = spec.partition("=")
    func, _, label = rest.partition(":")
    return {"gpio": int(gpio.strip().upper().removeprefix("GPIO")), "function": func or "gpio",
            "label": label}


def check_pins(board: Dict[str, Any], chips: Dict[str, Any], uses: List[Dict[str, Any]],
               wifi: bool = True) -> List[Dict[str, Any]]:
    chip = chips[board["chip"]]
    valid = set(chip_gpios(chip))
    owners = board_pin_owners(board)
    usb_native_only = bool(board["usb"].get("native")) and not board["usb"].get("bridge")
    console_uart = board["usb"].get("console") == "uart0"
    out: List[Dict[str, Any]] = []
    seen: Dict[int, str] = {}
    bus_addrs: Dict[str, Dict[int, str]] = {}

    if board["verification"]["status"] == "partial":
        out.append(_finding("warn", "Board profile is partial; some onboard pins are unknown, so "
                                    "conflicts with them cannot be detected. Check the schematic."))

    for use in uses:
        label = use.get("label") or ""
        if "bus" in use:
            bus_id = use["bus"]
            bus = next((p for p in board["peripherals"]
                        if p["id"] == bus_id and p.get("kind") == "bus"), None)
            if bus is None:
                out.append(_finding("error", f'Board has no bus "{bus_id}"', label=label))
                continue
            try:
                addr = parse_addr_list([use["addr"]])[0]
            except (ValueError, KeyError, IndexError):
                out.append(_finding("error", f'Bad I2C address "{use.get("addr")}"', label=label))
                continue
            taken = bus_addrs.setdefault(bus_id, bus_reserved_addrs(board, bus_id))
            if addr in taken:
                out.append(_finding("error", f"I2C address 0x{addr:02X} on {bus_id} is taken by "
                                             f"{taken[addr]}", label=label))
            else:
                taken[addr] = label or "your device"
                pins = bus.get("pins", {})
                out.append(_finding("ok", f"0x{addr:02X} is free on {bus_id} "
                                          f"(SDA={pins.get('sda')}, SCL={pins.get('scl')})", label=label))
            continue

        gpio = use["gpio"]
        func = use.get("function", "gpio")
        n_before = len(out)

        if func not in KNOWN_FUNCS:
            out.append(_finding("warn", f'Unknown function "{func}"; direction checks skipped', gpio, label))
        if gpio not in valid:
            out.append(_finding("error", f"GPIO{gpio} does not exist on {chip['name']}", gpio, label))
            continue
        if gpio in board.get("not_exposed", []):
            out.append(_finding("error", f"GPIO{gpio} is not broken out on {board['name']}", gpio, label))
            continue
        if gpio in seen:
            out.append(_finding("error", f"GPIO{gpio} is assigned twice (also '{seen[gpio]}')", gpio, label))
        seen[gpio] = label or func
        if gpio in chip["flash_pins"]:
            out.append(_finding("error", f"GPIO{gpio} is wired to SPI flash. Using it will crash or brick the boot.",
                                gpio, label))
        if board["psram_mode"] == "octal" and gpio in chip.get("octal_psram_pins", []):
            out.append(_finding("error", f"GPIO{gpio} is used by octal PSRAM on this board", gpio, label))
        if board["psram_mode"] == "quad" and gpio in chip.get("quad_psram_pins", []):
            out.append(_finding("error", f"GPIO{gpio} is used by PSRAM on this board", gpio, label))
        for o in owners.get(gpio, []):
            what = f'{o["peripheral"]}.{o["signal"]}' + (f' ({o["part"]})' if o["part"] else "")
            if o["peripheral"] == "usb":
                lvl = "error" if usb_native_only else "warn"
                out.append(_finding(lvl, f"GPIO{gpio} is native USB ({o['signal'].upper()}). Reusing it "
                                         "removes USB flashing/console" +
                                    (" and this board has no other USB port." if usb_native_only else "."),
                                    gpio, label))
            elif o["soft"]:
                out.append(_finding("warn", f"GPIO{gpio} is shared with the onboard {what}", gpio, label))
            else:
                out.append(_finding("error", f"GPIO{gpio} is already used onboard by {what}", gpio, label))
        if func in OUTPUT_FUNCS and gpio in chip.get("input_only", []):
            out.append(_finding("error", f"GPIO{gpio} is input-only and cannot drive '{func}'", gpio, label))
        strap = chip.get("strapping", {}).get(str(gpio))
        if strap:
            out.append(_finding("warn", f"GPIO{gpio} is a strapping pin ({strap}). Do not pull it the wrong "
                                        "way at reset; outputs are fine after boot.", gpio, label))
        uart0 = chip.get("uart0") or {}
        if console_uart and gpio in uart0.values():
            out.append(_finding("warn", f"GPIO{gpio} is UART0 (console/flash port on this board)", gpio, label))
        if gpio in chip.get("jtag", []) and gpio not in chip.get("strapping", {}):
            out.append(_finding("info", f"GPIO{gpio} is a JTAG pin; external JTAG debugging will not work "
                                        "while it is used", gpio, label))
        if func == "adc":
            if gpio in chip.get("adc1", []):
                pass
            elif gpio in chip.get("adc2", []):
                note = chip.get("adc2_wifi_conflict")
                if wifi and note:
                    out.append(_finding("warn", f"GPIO{gpio} is ADC2. {note}", gpio, label))
            else:
                out.append(_finding("error", f"GPIO{gpio} has no ADC on {chip['name']}", gpio, label))
        free = board.get("free_pins")
        if free is not None and gpio not in free and not owners.get(gpio) and len(out) == n_before:
            out.append(_finding("warn", f"GPIO{gpio} is not in this board's list of broken-out free pins",
                                gpio, label))
        if len(out) == n_before:
            out.append(_finding("ok", f"GPIO{gpio} looks fine for {func}", gpio, label))
    return out


def has_errors(findings: List[Dict[str, Any]]) -> bool:
    return any(f["level"] == "error" for f in findings)
