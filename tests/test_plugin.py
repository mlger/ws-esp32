import json
import re
import shutil
import subprocess
import sys

import pytest
from conftest import ROOT

sys.path.insert(0, str(ROOT / "tools"))
from run_evals import check  # noqa: E402

NODE = shutil.which("node")


def hook(command: str) -> str:
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    res = subprocess.run([NODE, str(ROOT / "hooks" / "esp-guard.mjs")], input=payload,
                         capture_output=True, text=True, timeout=20)
    assert res.returncode == 0
    return res.stdout


@pytest.mark.skipif(not NODE, reason="node not installed")
@pytest.mark.parametrize("cmd", [
    "espefuse.py --port COM3 burn_efuse FLASH_CRYPT_CNT 1",
    "python -m espefuse burn-key BLOCK_KEY0 key.bin",
    "idf.py -p /dev/ttyACM0 erase-flash",
    "esptool.py --chip esp32s3 erase_flash",
    "esptool erase-region 0x9000 0x6000",
    "espsecure.py sign_data --keyfile k.pem app.bin",
])
def test_hook_asks(cmd):
    out = json.loads(hook(cmd))
    assert out["hookSpecificOutput"]["permissionDecision"] == "ask"


@pytest.mark.skipif(not NODE, reason="node not installed")
@pytest.mark.parametrize("cmd", ["idf.py build", "idf.py -p COM3 flash monitor", "esptool.py flash_id", "ls"])
def test_hook_allows(cmd):
    assert hook(cmd) == ""


def test_hooks_json():
    cfg = json.loads((ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    entry = cfg["hooks"]["PreToolUse"][0]
    assert "Bash" in entry["matcher"]
    assert "esp-guard.mjs" in entry["hooks"][0]["command"]


@pytest.mark.parametrize("name", ["esp-new", "esp-flash", "esp-doctor"])
def test_commands_have_frontmatter(name):
    text = (ROOT / "commands" / f"{name}.md").read_text(encoding="utf-8")
    assert re.match(r"^---\ndescription: .+\n", text)


def test_evals_file():
    data = json.loads((ROOT / "evals" / "evals.json").read_text(encoding="utf-8"))
    ids = [c["id"] for c in data["evals"]]
    assert len(ids) == len(set(ids)) >= 5
    for c in data["evals"]:
        for pat in c.get("must_include", []) + c.get("must_not_include", []):
            re.compile(pat)


def test_eval_checker():
    case = {"must_include": ["backlight"], "must_not_include": ["is free"]}
    assert check("GPIO2 drives the backlight", case) == []
    assert len(check("GPIO2 is free", case)) == 2
