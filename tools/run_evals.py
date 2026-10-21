"""Run the skill evals in evals/evals.json against an agent CLI.

The agent must be able to see the skill (install the plugin, or run from this repo).
Default command is Claude Code in print mode:

  python tools/run_evals.py                       # all evals
  python tools/run_evals.py --only pin-conflict-backlight
  python tools/run_evals.py --cmd "claude -p"     # any CLI that takes the prompt as last argument

Not run in CI because it needs an authenticated agent.
"""

import argparse
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check(answer: str, case: dict) -> list:
    problems = []
    for pat in case.get("must_include", []):
        if not re.search(pat, answer, re.I):
            problems.append(f"missing /{pat}/")
    for pat in case.get("must_not_include", []):
        if re.search(pat, answer, re.I):
            problems.append(f"should not contain /{pat}/")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cmd", default="claude -p", help="agent command; the prompt is appended")
    ap.add_argument("--only", action="append", help="eval id(s) to run")
    ap.add_argument("--timeout", type=int, default=300)
    args = ap.parse_args()

    cases = json.loads((ROOT / "evals" / "evals.json").read_text(encoding="utf-8"))["evals"]
    if args.only:
        cases = [c for c in cases if c["id"] in args.only]
    failed = 0
    for case in cases:
        try:
            res = subprocess.run(shlex.split(args.cmd) + [case["prompt"]], capture_output=True, text=True,
                                 timeout=args.timeout, cwd=ROOT)
            answer = res.stdout
        except (OSError, subprocess.TimeoutExpired) as e:
            answer, problems = "", [f"agent failed: {e}"]
        else:
            problems = check(answer, case)
        status = "PASS" if not problems else "FAIL"
        failed += bool(problems)
        print(f"{status} {case['id']}" + (": " + "; ".join(problems) if problems else ""))
    print(f"{len(cases) - failed}/{len(cases)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
