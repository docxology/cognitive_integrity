#!/usr/bin/env python3
"""Record how many tests each part has, so the papers can stop guessing.

Part 3's abstract and introduction quote a total test count for the series.  It
has been typed by hand three times and been wrong three times: 2,283, then
3,308, then 3,369 -- each correct on the day it was written and stale by the
next commit that added a test.  A number that changes whenever anyone touches
the suite cannot be maintained in prose.

This script collects the real counts and writes them to
``cogsec_multiagent_2_computational/output/data/test_inventory.json``, where the
series ledger picks them up like any other artifact.  After that the count is
derived, gated, and rewritten by ``inject_series_values.py`` whenever it moves.

    python3 scripts/collect_test_inventory.py           # write the inventory
    python3 scripts/collect_test_inventory.py --check   # fail if it is stale

``--check`` is what CI runs: it recollects and compares, so a commit that adds
tests without refreshing the inventory fails loudly rather than leaving the
papers quoting yesterday's number.

Collection only -- no test is executed, so this is fast and has no side effects
beyond the JSON it writes.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent

PARTS: dict[str, str] = {
    "1": "cogsec_multiagent_1_theory",
    "2": "cogsec_multiagent_2_computational",
    "3": "cogsec_multiagent_3_practical",
}

#: The series-level suites that live at the program root rather than in a part.
PROGRAM_TESTS = REPO_ROOT / "tests"

INVENTORY = REPO_ROOT / PARTS["2"] / "output" / "data" / "test_inventory.json"

_COLLECTED = re.compile(r"(\d+) tests? collected")


class CollectionFailed(RuntimeError):
    """Raised when a suite cannot be collected at all."""


def _python_for(part_dir: Path) -> Path:
    venv = part_dir / ".venv" / "bin" / "python"
    if not venv.is_file():
        raise CollectionFailed(f"{part_dir.name} has no .venv; run `uv sync` there first")
    return venv


def collect(part_dir: Path, tests_dir: Path, interpreter: Path | None = None) -> int:
    """Return the number of tests pytest can collect, or raise."""
    python = interpreter or _python_for(part_dir)
    proc = subprocess.run(
        [str(python), "-m", "pytest", str(tests_dir), "--collect-only", "-q",
         "-p", "no:cacheprovider", "--no-header"],
        cwd=str(part_dir),
        capture_output=True,
        text=True,
        timeout=600,
    )
    match = _COLLECTED.search(proc.stdout)
    if not match:
        # A zero-collection run and a crashed run look the same from the exit
        # code alone, so refuse both rather than recording a plausible 0.
        tail = (proc.stdout or proc.stderr).strip().splitlines()[-5:]
        raise CollectionFailed(
            f"{part_dir.name}: pytest reported no collection count.\n  " + "\n  ".join(tail)
        )
    count = int(match.group(1))
    if count == 0:
        raise CollectionFailed(f"{part_dir.name}: collected 0 tests; refusing to record that")
    return count


def build_inventory() -> dict[str, object]:
    per_part: dict[str, int] = {}
    for part, package in sorted(PARTS.items()):
        part_dir = REPO_ROOT / package
        per_part[package] = collect(part_dir, part_dir / "tests")

    # The program-level suites have no venv of their own; any part's works,
    # since they only need pytest and the stdlib.
    program = collect(REPO_ROOT, PROGRAM_TESTS, _python_for(REPO_ROOT / PARTS["2"]))

    return {
        "data_origin": "real_pipeline",
        "source_script": "scripts/collect_test_inventory.py",
        "note": (
            "Counts are pytest collection totals, not pass counts: collection is "
            "deterministic and side-effect free, whereas a pass count depends on the "
            "environment a given run happened to have."
        ),
        "per_part": per_part,
        "program_level": program,
        "total": sum(per_part.values()) + program,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if the inventory is stale")
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        fresh = build_inventory()
    except (CollectionFailed, subprocess.TimeoutExpired) as exc:
        print(f"test inventory: FAILED -- {exc}", file=sys.stderr)
        return 2

    if args.check:
        if not INVENTORY.is_file():
            print(f"test inventory: missing {INVENTORY.relative_to(REPO_ROOT)}; run this "
                  f"script without --check to create it", file=sys.stderr)
            return 1
        stored = json.loads(INVENTORY.read_text(encoding="utf-8"))
        drift = {
            key: (stored.get(key), fresh[key])
            for key in ("per_part", "program_level", "total")
            if stored.get(key) != fresh[key]
        }
        if drift:
            print("test inventory is stale; the papers are quoting a number that no longer holds:")
            for key, (was, now) in drift.items():
                print(f"  {key}: recorded {was} -> collected {now}")
            print("\nrun `python3 scripts/collect_test_inventory.py` and re-inject")
            return 1
        print(f"test inventory: current ({fresh['total']} tests across the series)")
        return 0

    INVENTORY.parent.mkdir(parents=True, exist_ok=True)
    INVENTORY.write_text(json.dumps(fresh, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {INVENTORY.relative_to(REPO_ROOT)}: {fresh['total']} tests across the series")
    for package, count in fresh["per_part"].items():
        print(f"  {package:<34} {count}")
    print(f"  {'(program-level)':<34} {fresh['program_level']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
