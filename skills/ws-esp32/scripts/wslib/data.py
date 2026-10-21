"""Load and validate chip rules and board profiles."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

SKILL_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = SKILL_ROOT / "data"
BOARDS_DIR = DATA_DIR / "boards"
TEMPLATES_DIR = SKILL_ROOT / "templates"

VERIFICATION_LEVELS = ("partial", "wiki", "schematic", "hardware-tested")
PSRAM_MODES = ("none", "quad", "octal")
CONSOLES = ("uart0", "usb_serial_jtag")
EXIO_RE = re.compile(r"^EXIO\d+$")
ADDR_RE = re.compile(r"^0x[0-9A-Fa-f]{2}(-0x[0-9A-Fa-f]{2})?$")
REQUIRED_KEYS = ("id", "name", "chip", "soc", "flash_mb", "psram_mb", "psram_mode",
                 "usb", "verification", "peripherals")


def load_chips() -> Dict[str, Any]:
    with open(DATA_DIR / "chips.json", encoding="utf-8") as f:
        chips = json.load(f)
    chips.pop("$comment", None)
    return chips


def load_boards() -> Dict[str, Dict[str, Any]]:
    boards = {}
    for path in sorted(BOARDS_DIR.glob("*.json")):
        with open(path, encoding="utf-8") as f:
            board = json.load(f)
        board["_path"] = str(path)
        boards[board.get("id", path.stem)] = board
    return boards


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def find_board(query: str, boards: Optional[Dict[str, Dict[str, Any]]] = None
               ) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """Return (board, candidates). board is set only on a single clear match."""
    boards = boards if boards is not None else load_boards()
    q = _norm(query)
    for b in boards.values():
        names = [b["id"], b["name"]] + b.get("aliases", [])
        if any(_norm(n) == q for n in names):
            return b, [b["id"]]
    hits = [b["id"] for b in boards.values()
            if any(q in _norm(n) for n in [b["id"], b["name"]] + b.get("aliases", []))]
    if len(hits) > 1:
        # "7" or "2.8": prefer boards whose name ends with the query (so "2.8" doesn't hit "1.28").
        tail = [h for h in hits if _norm(h.rsplit("-", 1)[-1]) == q]
        if tail:
            hits = tail
    if len(hits) == 1:
        return boards[hits[0]], hits
    return None, hits


def chip_gpios(chip: Dict[str, Any]) -> List[int]:
    out: List[int] = []
    for lo, hi in chip["gpio_ranges"]:
        out.extend(range(lo, hi + 1))
    return out


def iter_pins(board: Dict[str, Any]) -> Iterator[Tuple[Dict[str, Any], str, Any]]:
    """Yield (peripheral, signal, value) for every pin entry."""
    for p in board.get("peripherals", []):
        for sig, val in (p.get("pins") or {}).items():
            yield p, sig, val


def parse_addr_list(items: List[str]) -> List[int]:
    out: List[int] = []
    for item in items:
        if "-" in item:
            lo, hi = item.split("-")
            out.extend(range(int(lo, 16), int(hi, 16) + 1))
        else:
            out.append(int(item, 16))
    return out


def bus_reserved_addrs(board: Dict[str, Any], bus_id: str) -> Dict[int, str]:
    """I2C addresses already taken on a board bus -> who owns them."""
    taken: Dict[int, str] = {}
    for p in board["peripherals"]:
        if p["id"] == bus_id:
            for a in parse_addr_list(p.get("reserved_addrs", [])):
                taken.setdefault(a, "reserved by the board")
        if p.get("bus") == bus_id and p.get("addr"):
            for a in parse_addr_list([p["addr"]]):
                taken[a] = f'{p["id"]} ({p.get("part", "?")})'
    return taken


def validate_board(board: Dict[str, Any], chips: Dict[str, Any]) -> List[str]:
    """Return a list of problems with a board profile (empty = OK)."""
    errs: List[str] = []
    bid = board.get("id", "?")
    for k in REQUIRED_KEYS:
        if k not in board:
            errs.append(f"{bid}: missing key '{k}'")
    if errs:
        return errs

    path = board.get("_path")
    if path and Path(path).stem != bid:
        errs.append(f"{bid}: file name must be '{bid}.json'")
    if not re.fullmatch(r"[a-z0-9][a-z0-9.\-]*", bid):
        errs.append(f"{bid}: id must be lowercase letters, digits, '.' and '-'")

    chip = chips.get(board["chip"])
    if chip is None:
        return errs + [f"{bid}: unknown chip '{board['chip']}' (add it to chips.json)"]
    gpios = set(chip_gpios(chip))

    if board["psram_mode"] not in PSRAM_MODES:
        errs.append(f"{bid}: psram_mode must be one of {PSRAM_MODES}")
    if (board["psram_mb"] == 0) != (board["psram_mode"] == "none"):
        errs.append(f"{bid}: psram_mb and psram_mode disagree")
    usb = board["usb"]
    if usb.get("console") not in CONSOLES:
        errs.append(f"{bid}: usb.console must be one of {CONSOLES}")
    if usb.get("console") == "usb_serial_jtag" and not usb.get("native"):
        errs.append(f"{bid}: usb_serial_jtag console needs usb.native = true")

    ver = board["verification"]
    if ver.get("status") not in VERIFICATION_LEVELS:
        errs.append(f"{bid}: verification.status must be one of {VERIFICATION_LEVELS}")
    if not ver.get("sources"):
        errs.append(f"{bid}: verification.sources must list at least one URL")

    ids = [p.get("id") for p in board["peripherals"]]
    if len(ids) != len(set(ids)):
        errs.append(f"{bid}: duplicate peripheral ids")
    bus_ids = {p["id"] for p in board["peripherals"] if p.get("kind") == "bus"}
    has_expander = any(p.get("kind") == "io_expander" for p in board["peripherals"])
    has_null = False

    owners: Dict[int, Tuple[str, Optional[str]]] = {}
    for p, sig, val in iter_pins(board):
        where = f'{bid}: {p["id"]}.{sig}'
        if val is None:
            has_null = True
        elif isinstance(val, bool) or not isinstance(val, (int, str)):
            errs.append(f"{where}: pin must be an int, 'EXIOn' or null")
        elif isinstance(val, str):
            if not EXIO_RE.match(val):
                errs.append(f"{where}: string pins must look like 'EXIO2'")
            elif not has_expander:
                errs.append(f"{where}: uses {val} but the board has no io_expander peripheral")
        else:
            if val not in gpios:
                errs.append(f"{where}: GPIO{val} does not exist on {chip['name']}")
            if val in chip["flash_pins"]:
                errs.append(f"{where}: GPIO{val} is a flash pin")
            prev = owners.get(val)
            share = p.get("share")
            if prev and not (share and prev[1] == share):
                errs.append(f"{where}: GPIO{val} already used by {prev[0]} (add a matching 'share' group if intended)")
            owners.setdefault(val, (p["id"], share))
    for p in board["peripherals"]:
        if p.get("bus") and p["bus"] not in bus_ids:
            errs.append(f'{bid}: {p["id"]} refers to unknown bus "{p["bus"]}"')
        addr = p.get("addr")
        if addr is not None and not ADDR_RE.match(str(addr)):
            errs.append(f'{bid}: {p["id"]}.addr must look like "0x3C"')
        for a in p.get("reserved_addrs", []):
            if not ADDR_RE.match(a):
                errs.append(f'{bid}: {p["id"]}.reserved_addrs entry "{a}" is malformed')
    if has_null and ver.get("status") != "partial":
        errs.append(f"{bid}: has unknown (null) pins, so verification.status must be 'partial'")
    for fp in board.get("free_pins") or []:
        if fp in owners:
            errs.append(f"{bid}: free pin GPIO{fp} is also used by {owners[fp][0]}")
    return errs
