#!/usr/bin/env python3
"""Run every numbered figure script in order, and fail if any of them fails.

The figure scripts in this directory are numbered and independently runnable,
which is convenient while writing one and dangerous when regenerating all of
them: a caller that loops over the directory and discards output reports
success whether or not a figure was produced, and a caller that invokes a
`generate_all_figures.py` this project did not have fails with a file-not-found
that is easy to swallow. Both leave stale PNGs in `output/figures/` and a
manuscript that renders them without complaint.

This is the single entry point. It runs each script with the current
interpreter, prints one line per script, and exits non-zero listing every
script that failed rather than stopping at the first.

    python scripts/generate_all_figures.py [--list]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
_NUMBERED = re.compile(r"^\d{2}_.*\.py$")


def numbered_scripts() -> list[Path]:
    """Every ``NN_name.py`` in this directory, in numeric order."""
    found = sorted(p for p in SCRIPTS_DIR.glob("*.py") if _NUMBERED.match(p.name))
    if not found:
        raise SystemExit(
            f"no numbered figure scripts found in {SCRIPTS_DIR}; discovery is "
            f"broken, and a generator that generates nothing must not report success"
        )
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="list the scripts and exit")
    args = parser.parse_args()

    scripts = numbered_scripts()
    if args.list:
        for script in scripts:
            print(script.name)
        return 0

    failures: list[tuple[str, str]] = []
    for script in scripts:
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            cwd=SCRIPTS_DIR.parent,
        )
        status = "ok" if result.returncode == 0 else f"FAILED ({result.returncode})"
        print(f"  {script.name:<44} {status}")
        if result.returncode != 0:
            tail = (result.stderr or result.stdout).strip().splitlines()
            failures.append((script.name, tail[-1] if tail else "no output"))

    print(f"{len(scripts) - len(failures)}/{len(scripts)} figure script(s) succeeded")
    for name, reason in failures:
        print(f"  {name}: {reason}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
