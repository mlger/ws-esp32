"""`detect` (identify a connected board) and `decode` (crash backtrace -> source lines)."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Optional

CHIP_NAMES = {"ESP32": "esp32", "ESP32-S3": "esp32s3", "ESP32-C3": "esp32c3", "ESP32-C6": "esp32c6",
              "ESP32-P4": "esp32p4"}
ADDR2LINE = {
    "esp32": "xtensa-esp32-elf-addr2line",
    "esp32s3": "xtensa-esp32s3-elf-addr2line",
    "esp32c3": "riscv32-esp-elf-addr2line",
    "esp32c6": "riscv32-esp-elf-addr2line",
    "esp32p4": "riscv32-esp-elf-addr2line",
}


# ---------- detect ----------

def parse_esptool(text: str) -> Dict[str, Any]:
    """Pull chip, PSRAM and flash size out of `esptool flash_id` output (v4 and v5 formats)."""
    info: Dict[str, Any] = {"chip": None, "chip_name": None, "psram_mb": 0, "flash_mb": None, "mac": None}
    m = re.search(r"(?:Chip is|Chip type:)\s+(ESP32(?:-[A-Z0-9]+)?)", text)
    if m:
        info["chip_name"] = m.group(1)
        info["chip"] = CHIP_NAMES.get(m.group(1))
    m = re.search(r"Embedded PSRAM (\d+)MB", text)
    if m:
        info["psram_mb"] = int(m.group(1))
    m = re.search(r"Detected flash size:\s*(\d+)MB", text)
    if m:
        info["flash_mb"] = int(m.group(1))
    m = re.search(r"MAC:\s*([0-9a-f:]{17})", text, re.I)
    if m:
        info["mac"] = m.group(1)
    return info


def match_boards(info: Dict[str, Any], boards: Dict[str, Dict[str, Any]]) -> List[str]:
    """Board ids consistent with what the chip reports. External (module) PSRAM isn't
    always reported by esptool, so a board with PSRAM still matches when psram reads 0."""
    out = []
    for b in boards.values():
        if info["chip"] and b["chip"] != info["chip"]:
            continue
        if info["flash_mb"] and b["flash_mb"] != info["flash_mb"]:
            continue
        if info["psram_mb"] and b["psram_mb"] != info["psram_mb"]:
            continue
        out.append(b["id"])
    return out


def run_esptool(port: str) -> str:
    cmds = []
    for exe in ("esptool", "esptool.py"):
        if shutil.which(exe):
            cmds.append([exe])
    cmds.append([sys.executable, "-m", "esptool"])
    last = ""
    for base in cmds:
        try:
            res = subprocess.run(base + ["--port", port, "flash_id"], capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.TimeoutExpired) as e:
            last = str(e)
            continue
        out = (res.stdout or "") + (res.stderr or "")
        if "No module named esptool" in out:
            last = out
            continue
        return out
    raise RuntimeError("esptool not found. Install it with: python -m pip install esptool\n" + last)


# ---------- decode ----------

def parse_backtrace(log: str) -> List[str]:
    """Return code addresses from an ESP-IDF panic log, in order, without duplicates.

    Xtensa: 'Backtrace: 0x4200abcd:0x3fc9... 0x...'  (PC:SP pairs)
    RISC-V: 'MEPC    : 0x42001234' plus 'RA      : 0x...'
    """
    addrs: List[str] = []
    for line in log.splitlines():
        if "Backtrace:" in line:
            addrs += re.findall(r"(0x[0-9a-fA-F]{8}):0x[0-9a-fA-F]{8}", line)
        m = re.match(r"\s*(?:MEPC|RA|PC)\s*:\s*(0x[0-9a-fA-F]{8})", line)
        if m:
            addrs.append(m.group(1))
    seen, out = set(), []
    for a in addrs:
        a = a.lower()
        # Skip addresses outside flash/IRAM code ranges (0x4xxxxxxx).
        if a.startswith("0x4") and a not in seen:
            seen.add(a)
            out.append(a)
    return out


def find_addr2line(chip: str, explicit: Optional[str] = None) -> Optional[str]:
    if explicit:
        return explicit
    return shutil.which(ADDR2LINE.get(chip, ""))


def decode(elf: str, addrs: List[str], tool: str) -> str:
    res = subprocess.run([tool, "-pfiaC", "-e", elf] + addrs, capture_output=True, text=True, timeout=60)
    return (res.stdout or res.stderr).strip()
