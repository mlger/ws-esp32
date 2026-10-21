"""Print GitHub Actions matrices:
matrix         = every board          {"include": [{board, target}, ...]}
display_matrix = boards that support  `new --with display`
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "waveshare-esp32" / "scripts"))

from wslib.data import load_boards, load_chips  # noqa: E402
from wslib.display import display_support  # noqa: E402

chips = load_chips()
boards = load_boards().values()
every = [{"board": b["id"], "target": chips[b["chip"]]["idf_target"]} for b in boards]
display = [{"board": b["id"], "target": chips[b["chip"]]["idf_target"]} for b in boards if display_support(b)[0]]
print("matrix=" + json.dumps({"include": every}))
print("display_matrix=" + json.dumps({"include": display}))
