#!/usr/bin/env python3
"""Formal Specification Verification Script.

Thin orchestrator — all logic lives in src/formal/spec_verifier.py.

Usage:
    python scripts/verify_formal_specs.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from formal.spec_verifier import generate_and_verify_all


def main() -> None:
    print("Cognitive Integrity Framework - Formal Verification")
    print("===================================================")

    output_dir = ROOT / "output" / "formal"
    results = generate_and_verify_all(output_dir)

    for spec_name, status in results.items():
        print(f"  {spec_name}: [{status}]")

    print("\n---------------------------------------------------")
    print("Verification Artifact Generation Complete.")


if __name__ == "__main__":
    main()
