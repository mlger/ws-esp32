import copy
import json
import re

import pytest
from conftest import ROOT
from wslib import __version__
from wslib.data import find_board, validate_board


def test_all_profiles_valid(boards, chips):
    problems = [p for b in boards.values() for p in validate_board(b, chips)]
    assert problems == []


def test_at_least_one_board(boards):
    assert len(boards) >= 7


@pytest.mark.parametrize("query,expected", [
    ("esp32-s3-touch-lcd-1.28", "esp32-s3-touch-lcd-1.28"),
    ("ESP32-C6-LCD-1.47", "esp32-c6-lcd-1.47"),
    ("s3 zero", "esp32-s3-zero"),
    ("4.3", "esp32-s3-touch-lcd-4.3"),
])
def test_find_board(boards, query, expected):
    board, _ = find_board(query, boards)
    assert board and board["id"] == expected


def test_find_board_ambiguous(boards):
    board, hits = find_board("1.47", boards)
    assert board is None and len(hits) == 2


def _base(boards):
    b = copy.deepcopy(boards["esp32-c6-lcd-1.47"])
    b.pop("_path", None)
    return b


def test_rejects_flash_pin(boards, chips):
    b = _base(boards)
    b["peripherals"][1]["pins"]["cs"] = 26
    assert any("flash pin" in e for e in validate_board(b, chips))


def test_rejects_duplicate_pin(boards, chips):
    b = _base(boards)
    b["peripherals"][1]["pins"]["cs"] = 4  # SD CS
    assert any("already used" in e for e in validate_board(b, chips))


def test_null_pin_requires_partial(boards, chips):
    b = _base(boards)
    b["peripherals"][1]["pins"]["cs"] = None
    assert any("partial" in e for e in validate_board(b, chips))


def test_exio_requires_expander(boards, chips):
    b = _base(boards)
    b["peripherals"][1]["pins"]["bl"] = "EXIO2"
    assert any("io_expander" in e for e in validate_board(b, chips))


def test_psram_mode_consistency(boards, chips):
    b = _base(boards)
    b["psram_mode"] = "octal"
    assert any("disagree" in e for e in validate_board(b, chips))


def test_versions_in_sync():
    plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert plugin["version"] == __version__


def test_skill_frontmatter():
    text = (ROOT / "skills" / "ws-esp32" / "SKILL.md").read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, "SKILL.md needs YAML frontmatter"
    fm = dict(line.split(": ", 1) for line in m.group(1).splitlines() if ": " in line)
    assert fm["name"] == "ws-esp32"
    assert 50 < len(fm["description"]) <= 1024
    assert len(text.splitlines()) < 500


def test_referenced_files_exist():
    skill = ROOT / "skills" / "ws-esp32"
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    for rel in set(re.findall(r"`(references/[\w/.-]+\.md)`", text)):
        assert (skill / rel).exists(), rel
