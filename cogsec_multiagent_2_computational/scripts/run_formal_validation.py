#!/usr/bin/env python3
"""Validate Paper 1 theorems computationally.

Maps each formal theorem to a computational validator and reports pass/fail.

Usage:
    python scripts/run_formal_validation.py [--seed 42] [--output output/data]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from utils.random_seed import set_global_seed
from formal.theorem_registry import TheoremRegistry, TheoremStatus
from formal.trust_bounds import validate_trust_bound
from formal.composition_proofs import (
    validate_series_composition,
    validate_parallel_composition,
    validate_associativity,
)
from formal.byzantine_guarantees import validate_byzantine_bound
from formal.stealth_impact import validate_stealth_impact
from formal.latency_bound import validate_latency_bound


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Paper 1 theorems")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=str, default="output/data")
    args = parser.parse_args()

    set_global_seed(args.seed)
    output_dir = ROOT / args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("Paper 1 Theorem Validation")
    print("=" * 70)

    # Register validators
    registry = TheoremRegistry()
    registry.register("3.1a", "Trust Delegation Decay Bound", validate_trust_bound)
    registry.register("3.1b", "Series Composition Detection", validate_series_composition)
    registry.register("3.2", "Parallel Composition Detection", validate_parallel_composition)
    registry.register("3.3", "Composition Associativity", validate_associativity)
    registry.register("4", "Stealth-Impact Tradeoff", validate_stealth_impact)
    registry.register("5.3", "Byzantine Fault Tolerance", validate_byzantine_bound)
    registry.register("6", "CIF Latency Overhead Bound", validate_latency_bound)

    # Run all validators
    results = registry.validate_all(seed=args.seed)

    print(f"\n{'Theorem':<12} {'Name':<35} {'Status':<10} {'Evidence'}")
    print("-" * 90)
    for r in results:
        status_icon = {
            TheoremStatus.PASSED: "PASS",
            TheoremStatus.FAILED: "FAIL",
            TheoremStatus.SKIPPED: "SKIP",
            TheoremStatus.ERROR: "ERR ",
        }[r.status]
        evidence_short = r.evidence[:40] + "..." if len(r.evidence) > 40 else r.evidence
        print(f"  Thm {r.theorem_id:<7} {r.name:<35} {status_icon:<10} {evidence_short}")
    print("-" * 90)

    summary = registry.summary()
    print(f"\nSummary: {summary}")
    total = sum(summary.values())
    passed = summary.get("passed", summary.get("PASSED", 0))
    print(f"Result: {passed}/{total} theorems validated")

    # Save
    out_path = output_dir / "formal_validation_results.json"
    data = [
        {
            "theorem_id": r.theorem_id,
            "name": r.name,
            "status": r.status.value,
            "evidence": r.evidence,
            "details": r.details,
        }
        for r in results
    ]
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
