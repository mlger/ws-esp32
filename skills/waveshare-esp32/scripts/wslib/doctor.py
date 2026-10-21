"""Check the local toolchain and list serial ports. Read-only: never installs anything."""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Optional

# USB VID:PID -> what it usually is on Waveshare boards
USB_IDS = {
    ("303A", "1001"): "ESP32-S3/C3/C6 native USB-Serial-JTAG",
    ("303A", "0002"): "ESP32-S2/S3 native USB (TinyUSB CDC)",
    ("1A86", "55D3"): "WCH CH343 USB-UART",
    ("1A86", "55D4"): "WCH CH9102 USB-UART",
    ("1A86", "7523"): "WCH CH340 USB-UART",
    ("10C4", "EA60"): "Silicon Labs CP210x USB-UART",
    ("0403", "6001"): "FTDI FT232 USB-UART",
}

DRIVER_HINTS = {
    "Windows": "CH343/CH9102 boards need the WCH CH343SER driver on older Windows; native USB boards need no driver.",
    "Linux": "Add yourself to the 'dialout' (Debian/Ubuntu) or 'uucp' (Arch) group, then log out and in.",
    "Darwin": "Native USB and CH34x work without drivers on recent macOS. "
              "Ports show up as /dev/cu.usbmodem* or /dev/cu.wchusbserial*.",
}


def _run(cmd: List[str], timeout: int = 20) -> Optional[str]:
    exe = shutil.which(cmd[0])
    if not exe:
        return None
    try:
        res = subprocess.run([exe] + cmd[1:], capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return (res.stdout or res.stderr).strip()


def _first_version(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    m = re.search(r"v?(\d+\.\d+(?:\.\d+)?(?:[-.\w]*)?)", text)
    return m.group(0) if m else text.splitlines()[0][:80]


def list_ports() -> Dict[str, Any]:
    try:
        from serial.tools import list_ports  # type: ignore
    except ImportError:
        return {"available": False, "ports": [],
                "hint": "Install pyserial for port detection: python -m pip install pyserial"}
    ports = []
    for p in list_ports.comports():
        vid = f"{p.vid:04X}" if p.vid is not None else None
        pid = f"{p.pid:04X}" if p.pid is not None else None
        ports.append({"device": p.device, "description": p.description, "vid": vid, "pid": pid,
                      "kind": USB_IDS.get((vid, pid), "unknown")})
    return {"available": True, "ports": ports}


def run_doctor() -> Dict[str, Any]:
    checks: List[Dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str, fix: str = "") -> None:
        checks.append({"name": name, "ok": ok, "detail": detail, "fix": fix})

    add("python", sys.version_info >= (3, 9), platform.python_version(),
        "Install Python 3.9 or newer.")

    idf_path = os.environ.get("IDF_PATH")
    idf_ver = _first_version(_run(["idf.py", "--version"]))
    if idf_ver:
        add("esp-idf", True, f"{idf_ver} (IDF_PATH={idf_path})")
    else:
        add("esp-idf", False, "idf.py not on PATH" + (f" (IDF_PATH={idf_path})" if idf_path else ""),
            "Install with Espressif's EIM installer or the VS Code ESP-IDF extension, then open an "
            "ESP-IDF terminal (export.sh / export.ps1). Optional if you only use Arduino or PlatformIO.")

    esptool = _first_version(_run(["esptool.py", "version"]) or _run(["esptool", "version"]))
    add("esptool", bool(esptool), esptool or "not found",
        "python -m pip install esptool (also bundled with ESP-IDF, Arduino and PlatformIO).")

    acli = _first_version(_run(["arduino-cli", "version"]))
    if acli:
        cores = _run(["arduino-cli", "core", "list"]) or ""
        m = re.search(r"esp32:esp32\s+(\S+)", cores)
        add("arduino-cli", True, acli + (f", esp32 core {m.group(1)}" if m else ", esp32 core NOT installed"),
            "" if m else "arduino-cli core install esp32:esp32 --additional-urls "
                         "https://espressif.github.io/arduino-esp32/package_esp32_index.json")
    else:
        add("arduino-cli", False, "not found", "Optional. https://arduino.github.io/arduino-cli/")

    pio = _first_version(_run(["pio", "--version"]) or _run(["platformio", "--version"]))
    add("platformio", bool(pio), pio or "not found", "Optional. python -m pip install platformio")

    git = _first_version(_run(["git", "--version"]))
    add("git", bool(git), git or "not found", "Install git; ESP-IDF and component manager need it.")

    ports = list_ports()
    return {"os": platform.system(), "os_hint": DRIVER_HINTS.get(platform.system(), ""),
            "checks": checks, "serial": ports}
