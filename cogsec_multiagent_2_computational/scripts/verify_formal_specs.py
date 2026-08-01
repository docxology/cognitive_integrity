#!/usr/bin/env python3
"""Formal Specification Verification Script.

Thin orchestrator — all spec generation and checker invocation lives in
``src/formal/spec_verifier.py``.  This script's own responsibility is the
*verdict*: turning three per-tool :class:`VerificationStatus` values into a
process exit code that a caller cannot misread.

Exit-code contract (fail-closed)
--------------------------------
``0``
    Every checker actually ran and reported positive evidence (``PASS``).
    This is the *only* code that means "the specifications were verified".
``1``
    At least one checker reported a violated property (``FAIL``).
``2``
    No checker reported a violation, but at least one did not verify —
    ``SKIP`` (binary absent), ``ERROR`` (present but unrunnable), or
    ``INCONCLUSIVE`` (ran, but its output establishes nothing).

An earlier version of this script printed the three statuses and returned
``None``, so the interpreter exited 0.  On a machine with no NuSMV/SPIN/TLC —
which is the normal case — that turned "nothing was verified" into a green
gate standing behind the manuscript's exhaustive-verification claims.

Usage:
    python scripts/verify_formal_specs.py [--output-dir output/formal]
                                          [--allow-unverified]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Mapping

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from formal.spec_verifier import (  # noqa: E402
    VerificationResult,
    VerificationStatus,
    generate_and_verify_all,
)

EXIT_VERIFIED = 0
EXIT_PROPERTY_VIOLATED = 1
EXIT_NOT_VERIFIED = 2

#: Statuses that do *not* constitute verification.  Kept explicit rather than
#: derived as "not PASSED" so that adding a status to the enum is a visible,
#: deliberate decision here too.
NON_VERIFYING = (
    VerificationStatus.SKIPPED,
    VerificationStatus.ERROR,
    VerificationStatus.INCONCLUSIVE,
)


def decide_exit_code(results: Mapping[str, VerificationResult]) -> int:
    """Map per-tool verdicts onto the exit-code contract above.

    Args:
        results: Mapping of tool name → :class:`VerificationResult`.

    Returns:
        ``EXIT_VERIFIED`` only when *every* result is ``PASSED`` and the
        mapping is non-empty; ``EXIT_PROPERTY_VIOLATED`` if any result is
        ``FAILED``; ``EXIT_NOT_VERIFIED`` otherwise (including for an empty
        mapping, which verifies nothing).
    """
    if not results:
        return EXIT_NOT_VERIFIED
    if any(r.status is VerificationStatus.FAILED for r in results.values()):
        return EXIT_PROPERTY_VIOLATED
    if all(r.status is VerificationStatus.PASSED for r in results.values()):
        return EXIT_VERIFIED
    return EXIT_NOT_VERIFIED


def write_evidence(
    output_dir: Path, results: Mapping[str, VerificationResult]
) -> Path:
    """Persist the verdicts next to the generated specs.

    The specs themselves are inputs, not evidence.  This file is the only
    machine-readable record that says whether a checker ran at all.

    Returns:
        Path of the written JSON file.
    """
    payload = {
        "tools": {
            tool: {"status": r.status.value, "detail": r.detail}
            for tool, r in sorted(results.items())
        },
        "verified": all(r.status is VerificationStatus.PASSED for r in results.values())
        and bool(results),
        "exit_code": decide_exit_code(results),
    }
    path = output_dir / "verification_summary.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate and model-check the CIF formal specifications."
    )
    parser.add_argument(
        "--output-dir",
        default=str(ROOT / "output" / "formal"),
        help="Directory for generated specs and the verification summary.",
    )
    parser.add_argument(
        "--allow-unverified",
        action="store_true",
        help=(
            "Return 0 even when checkers were skipped/errored/inconclusive. "
            "A property violation still returns 1. Use only for spec "
            "generation; never as a verification gate."
        ),
    )
    args = parser.parse_args(argv)

    print("Cognitive Integrity Framework - Formal Verification")
    print("===================================================")

    output_dir = Path(args.output_dir)
    results = generate_and_verify_all(output_dir)

    for spec_name, result in results.items():
        print(f"  {spec_name}: [{result}]")

    evidence_path = write_evidence(output_dir, results)
    print(f"\nVerdicts written to {evidence_path}")

    code = decide_exit_code(results)
    print("---------------------------------------------------")
    if code == EXIT_VERIFIED:
        print("VERIFIED: every checker ran and reported all properties true.")
    elif code == EXIT_PROPERTY_VIOLATED:
        violated = sorted(
            t for t, r in results.items() if r.status is VerificationStatus.FAILED
        )
        print(f"PROPERTY VIOLATED by: {', '.join(violated)}")
    else:
        unverified = sorted(
            f"{t}={r.status.value}"
            for t, r in results.items()
            if r.status in NON_VERIFYING
        )
        print(
            "NOT VERIFIED — specifications were generated but not "
            "model-checked: " + ", ".join(unverified)
        )
        print(
            "Install NuSMV / SPIN / TLC and re-run to obtain a verification "
            "verdict. Spec generation alone is not verification."
        )

    if args.allow_unverified and code == EXIT_NOT_VERIFIED:
        return EXIT_VERIFIED
    return code


if __name__ == "__main__":
    sys.exit(main())
