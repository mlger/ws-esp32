#!/usr/bin/env python3
"""wsesp - command line helper for the waveshare-esp32 agent skill.

Examples:
  python wsesp.py boards
  python wsesp.py show esp32-s3-touch-lcd-1.28
  python wsesp.py pins esp32-s3-touch-lcd-1.28 --use 16=gpio_out:relay --use i2c@0x3C:oled
  python wsesp.py new esp32-c6-lcd-1.47 --framework idf --name hello --out ./hello
  python wsesp.py doctor
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from wslib import __version__  # noqa: E402
from wslib.data import find_board, load_boards, load_chips, validate_board  # noqa: E402
from wslib.display import UnsupportedDisplay, display_support  # noqa: E402
from wslib.doctor import list_ports, run_doctor  # noqa: E402
from wslib.pins import check_pins, has_errors, parse_use  # noqa: E402
from wslib.scaffold import FRAMEWORKS, plan_project, render_header, write_project  # noqa: E402

ICONS = {"ok": "OK   ", "info": "INFO ", "warn": "WARN ", "error": "ERROR"}


def _print_json(obj) -> None:
    print(json.dumps(obj, indent=2, default=str))


def _get_board(query: str):
    board, hits = find_board(query)
    if board is None:
        if hits:
            sys.exit(f"'{query}' matches several boards: {', '.join(hits)}")
        sys.exit(f"No board matches '{query}'. Run 'wsesp.py boards' to list them, or add a profile "
                 "(see references/workflows/add-board.md).")
    return board


def _clean(board):
    return {k: v for k, v in board.items() if not k.startswith("_")}


def cmd_boards(args) -> int:
    boards = load_boards()
    if args.json:
        _print_json([{"id": b["id"], "name": b["name"], "chip": b["chip"],
                      "status": b["verification"]["status"]} for b in boards.values()])
        return 0
    print(f"{'ID':32} {'CHIP':9} {'FLASH/PSRAM':12} {'USB':8} STATUS")
    for b in boards.values():
        mem = f"{b['flash_mb']}M/{b['psram_mb']}M"
        usb = "native" if b["usb"].get("native") else (b["usb"].get("bridge") or "?")
        print(f"{b['id']:32} {b['chip']:9} {mem:12} {usb:8} {b['verification']['status']}")
    return 0


def cmd_show(args) -> int:
    board = _get_board(args.board)
    if args.json:
        _print_json(_clean(board))
        return 0
    v = board["verification"]
    print(f"{board['name']}  [{board['id']}]")
    print(f"  SoC: {board['soc']} ({board['chip']}), flash {board['flash_mb']} MB, "
          f"PSRAM {board['psram_mb']} MB {board['psram_mode']}")
    usb = board["usb"]
    print(f"  USB: native={usb.get('native')} bridge={usb.get('bridge')} console={usb.get('console')}")
    print(f"  Data: {v['status']} (checked {v.get('checked')}) {', '.join(v.get('sources', []))}")
    for p in board["peripherals"]:
        pins = ", ".join(f"{k}={'?' if val is None else val}" for k, val in (p.get("pins") or {}).items())
        extra = " ".join(x for x in [p.get("part") or "", f"on {p['bus']}" if p.get("bus") else "",
                                     f"@{p['addr']}" if p.get("addr") else ""] if x)
        print(f"  - {p['id']:12} {p['kind']:11} {extra}")
        if pins:
            print(f"      {pins}")
        if p.get("notes"):
            print(f"      note: {p['notes']}")
    if board.get("free_pins") is not None:
        print(f"  Free pins: {board['free_pins']}")
    ok, why = display_support(board)
    print(f"  Display codegen (new --with display): {'yes, ' if ok else 'no, '}{why}")
    sw = {k: val for k, val in (board.get("software") or {}).items() if val}
    if sw:
        print("  Tested with: " + ", ".join(f"{k} {val}" for k, val in sw.items()))
    for w in board.get("warnings", []):
        print(f"  ! {w}")
    return 0


def cmd_pins(args) -> int:
    board = _get_board(args.board)
    uses = []
    if args.file:
        text = sys.stdin.read() if args.file == "-" else Path(args.file).read_text(encoding="utf-8")
        data = json.loads(text)
        uses.extend(data["pins"] if isinstance(data, dict) else data)
    for spec in args.use or []:
        try:
            uses.append(parse_use(spec))
        except ValueError:
            sys.exit(f"Bad --use '{spec}'. Use GPIO=FUNCTION[:LABEL] or BUS@0xADDR[:LABEL]")
    if not uses:
        sys.exit("Nothing to check. Pass --use or --file.")
    findings = check_pins(board, load_chips(), uses, wifi=not args.no_wifi)
    if args.json:
        _print_json({"board": board["id"], "ok": not has_errors(findings), "findings": findings})
    else:
        for f in findings:
            label = f"[{f['label']}] " if f["label"] else ""
            print(f"{ICONS[f['level']]} {label}{f['message']}")
    return 1 if has_errors(findings) else 0


def cmd_header(args) -> int:
    print(render_header(_get_board(args.board)), end="")
    return 0


def cmd_new(args) -> int:
    board = _get_board(args.board)
    chip = load_chips()[board["chip"]]
    try:
        files = plan_project(board, chip, args.framework, args.name, with_display="display" in (args.with_ or []))
    except UnsupportedDisplay as e:
        sys.exit(f"Can't generate display code for {board['name']}: {e}")
    except ValueError as e:
        sys.exit(str(e))
    out = Path(args.out or args.name)
    if args.dry_run:
        for rel in files:
            print(out / rel)
        return 0
    try:
        written = write_project(files, out, force=args.force)
    except FileExistsError as e:
        sys.exit(str(e))
    for p in written:
        print(f"created {p}")
    if board["verification"]["status"] == "partial":
        print("WARNING: board profile is partial; unknown pins are commented out in board_pins.h.")
    return 0


def cmd_doctor(args) -> int:
    report = run_doctor()
    if args.json:
        _print_json(report)
        return 0
    print(f"OS: {report['os']}")
    for c in report["checks"]:
        print(f"{'OK  ' if c['ok'] else 'MISS'} {c['name']:12} {c['detail']}")
        if not c["ok"] and c["fix"]:
            print(f"     fix: {c['fix']}")
    _print_ports(report["serial"])
    if report["os_hint"]:
        print(f"Tip: {report['os_hint']}")
    return 0


def _print_ports(serial) -> None:
    if not serial["available"]:
        print(serial["hint"])
    elif not serial["ports"]:
        print("No serial ports found. Try another cable (many are charge-only) or hold BOOT while plugging in.")
    else:
        for p in serial["ports"]:
            print(f"PORT {p['device']:14} {p['kind']}  ({p['vid']}:{p['pid']} {p['description']})")


def cmd_ports(args) -> int:
    serial = list_ports()
    if args.json:
        _print_json(serial)
    else:
        _print_ports(serial)
    return 0


def cmd_validate(args) -> int:
    chips = load_chips()
    problems = []
    boards = load_boards()
    for b in boards.values():
        problems += validate_board(b, chips)
    for p in problems:
        print(f"ERROR {p}")
    print(f"{len(boards)} boards checked, {len(problems)} problems")
    return 1 if problems else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="wsesp", description="Waveshare ESP32 skill helper")
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("boards", help="list known boards")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_boards)

    s = sub.add_parser("show", help="show one board profile")
    s.add_argument("board")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_show)

    s = sub.add_parser("pins", help="check planned pin usage")
    s.add_argument("board")
    s.add_argument("--use", action="append", help="GPIO=FUNCTION[:LABEL] or BUS@0xADDR[:LABEL]")
    s.add_argument("--file", help="JSON file ({'pins': [...]}) or '-' for stdin")
    s.add_argument("--no-wifi", action="store_true", help="app does not use Wi-Fi (relaxes ADC2 warning)")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_pins)

    s = sub.add_parser("header", help="print board_pins.h")
    s.add_argument("board")
    s.set_defaults(fn=cmd_header)

    s = sub.add_parser("new", help="create a starter project")
    s.add_argument("board")
    s.add_argument("--framework", choices=FRAMEWORKS, default="idf")
    s.add_argument("--name", required=True)
    s.add_argument("--out", help="output directory (default: ./NAME)")
    s.add_argument("--with", dest="with_", action="append", choices=["display"],
                   help="extra features: display = LCD/touch/LVGL code (ESP-IDF, SPI panels)")
    s.add_argument("--force", action="store_true", help="overwrite existing files")
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(fn=cmd_new)

    s = sub.add_parser("doctor", help="check installed tools and serial ports")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_doctor)

    s = sub.add_parser("ports", help="list serial ports and identify USB chips")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_ports)

    s = sub.add_parser("validate-data", help="check every board profile (used by CI)")
    s.set_defaults(fn=cmd_validate)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
