#!/usr/bin/env python3
"""Run colony-level CogSec benchmarks.

Executes 5 colony scenarios and computes CCS scores.

Usage:
    python scripts/run_colony_benchmarks.py [--seed 42] [--output output/data]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from utils.random_seed import set_global_seed
from colony.benchmark import ColonyBenchmark


def main() -> None:
    parser = argparse.ArgumentParser(description="Run colony benchmarks")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=str, default="output/data")
    args = parser.parse_args()

    set_global_seed(args.seed)
    output_dir = ROOT / args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("Colony-Level CogSec Benchmarks")
    print("=" * 70)

    benchmark = ColonyBenchmark()
    results = benchmark.run_all(seed=args.seed)

    print(f"\n{'Scenario':<30} {'DR':>8} {'FPR':>8} {'Resil':>8} {'Rec':>8} {'CCS':>8}")
    print("-" * 70)
    for result in results:
        print(
            f"{result.scenario_name:<30} "
            f"{result.detection_rate:>7.3f} "
            f"{result.false_positive_rate:>7.3f} "
            f"{result.resilience_score:>7.3f} "
            f"{result.recovery_steps:>7d} "
            f"{result.ccs_score:>7.3f}"
        )
    print("-" * 70)

    summary = benchmark.summary()
    print("\nCCS Scores:")
    for name, ccs in sorted(summary.items()):
        print(f"  {name}: {ccs:.3f}")

    # Save results
    out_path = output_dir / "colony_results.json"
    data = [
        {
            "scenario": r.scenario_name,
            "n_agents": r.config.n_agents,
            "n_steps": r.config.n_steps,
            "n_adversaries": r.config.n_adversaries,
            "detection_rate": r.detection_rate,
            "false_positive_rate": r.false_positive_rate,
            "resilience_score": r.resilience_score,
            "recovery_steps": r.recovery_steps,
            "ccs_score": r.ccs_score,
        }
        for r in results
    ]
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
