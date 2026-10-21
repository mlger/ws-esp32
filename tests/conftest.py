import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "ws-esp32" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from wslib.data import load_boards, load_chips  # noqa: E402


@pytest.fixture(scope="session")
def chips():
    return load_chips()


@pytest.fixture(scope="session")
def boards():
    return load_boards()
