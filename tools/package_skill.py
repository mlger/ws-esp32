"""Zip the skill folder for Claude.ai upload / GitHub releases: dist/ws-esp32-<version>.zip"""

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "ws-esp32"
sys.path.insert(0, str(SKILL / "scripts"))

from wslib import __version__  # noqa: E402

SKIP_DIRS = {"__pycache__", ".pytest_cache"}


def main() -> int:
    out = ROOT / "dist" / f"ws-esp32-{__version__}.zip"
    out.parent.mkdir(exist_ok=True)
    count = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(SKILL.rglob("*")):
            if path.is_dir() or SKIP_DIRS.intersection(path.parts) or path.suffix == ".pyc":
                continue
            zf.write(path, Path("ws-esp32") / path.relative_to(SKILL))
            count += 1
    print(f"wrote {out} ({count} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
