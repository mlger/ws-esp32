"""Print GitHub Actions matrices (one `name=json` line each):

matrix          every board                 {board, target}
idf_matrix      every board x ESP-IDF        {board, target, idf}   tested version + latest
display_matrix  boards with display codegen  {board, target, idf}
arduino_display boards with Arduino display  {board, target}
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "ws-esp32" / "scripts"))

from wslib.data import load_boards, load_chips  # noqa: E402
from wslib.display import display_plan, display_support  # noqa: E402

DEFAULT_IDF = "v5.5.2"
LATEST = "latest"

chips = load_chips()
boards = list(load_boards().values())


def row(b):
    return {"board": b["id"], "target": chips[b["chip"]]["idf_target"]}


def tested_idf(b):
    v = (b.get("software") or {}).get("esp_idf")
    return f"v{v}" if v else DEFAULT_IDF


every = [row(b) for b in boards]
idf = [dict(row(b), idf=v) for b in boards for v in (tested_idf(b), LATEST)]
display = [dict(row(b), idf=tested_idf(b)) for b in boards if display_support(b)[0]]
arduino_display = [row(b) for b in boards if display_support(b)[0] and display_plan(b)["kind"] == "spi"]

for name, rows in [("matrix", every), ("idf_matrix", idf), ("display_matrix", display),
                   ("arduino_display", arduino_display)]:
    print(f"{name}=" + json.dumps({"include": rows}))
