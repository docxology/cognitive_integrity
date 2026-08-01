#!/usr/bin/env python3
"""Reader-side manuscript claim verification.

Re-derives every registered numeric claim from ``output/data/*.json`` and
compares it against the value actually printed in the manuscript prose.

This is the check that closes the loop the injector leaves open: the injector
*writes* numbers, this *reads them back*. It is designed to run as a CI gate.

Exit status
-----------
0
    Every claim matched.
1
    At least one claim MISMATCHed, was NOT_FOUND (its pattern matched zero
    times — a dead pattern is how a fabricated number hides), or was UNBACKED
    (the artifact behind it is missing or reports a non-success status).

Usage:
    python scripts/verify_claims.py
    python scripts/verify_claims.py --only-failures --json output/claim_report.json
"""

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from manuscript.claim_registry import CLAIMS, GroundTruth, verify_claims


def build_parser() -> argparse.ArgumentParser:
    """Command-line interface for the claim verifier."""
    project_dir = Path(os.environ.get("PROJECT_DIR", str(ROOT)))
    parser = argparse.ArgumentParser(
        description="Re-derive manuscript numbers from output/data and compare them."
    )
    parser.add_argument(
        "--data",
        default=str(project_dir / "output" / "data"),
        help="Directory containing the JSON data artifacts.",
    )
    parser.add_argument(
        "--manuscript",
        default=str(project_dir / "manuscript"),
        help="Directory containing the manuscript markdown files.",
    )
    parser.add_argument(
        "--json",
        dest="json_path",
        default=None,
        help="Also write the full report as JSON to this path.",
    )
    parser.add_argument(
        "--only-failures",
        action="store_true",
        help="Print only the rows that fail the gate.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the registry and return the process exit code."""
    args = build_parser().parse_args(argv)

    gt = GroundTruth(Path(args.data))
    report = verify_claims(CLAIMS, Path(args.manuscript), gt)

    print(report.render_table(only_failures=args.only_failures))
    counts = report.to_dict()["counts"]
    print()
    print(
        f"{counts['total']} claim(s): {counts['match']} MATCH, "
        f"{counts['mismatch']} MISMATCH, {counts['not_found']} NOT_FOUND, "
        f"{counts['unbacked']} UNBACKED"
    )

    for result in report.failures:
        print(f"  FAIL {result.claim_id} [{result.verdict}] {result.detail}")

    if args.json_path:
        out = Path(args.json_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
        print(f"report written to {out}")

    if report.ok:
        print("OK: every manuscript claim matches the data.")
        return 0
    print(f"FAILED: {len(report.failures)} claim(s) are not supported by the data.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
