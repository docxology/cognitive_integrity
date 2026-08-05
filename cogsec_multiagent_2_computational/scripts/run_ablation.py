#!/usr/bin/env python3
"""Run ablation studies: component removal, minimal config, and synergy.

Thin orchestrator — all logic lives in src/ablation/runner.py.

Usage:
    python scripts/run_ablation.py [--seed 42] [--output output/data]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ablation.runner import run_full_ablation


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ablation studies")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=str, default="output/data")
    args = parser.parse_args()

    output_dir = ROOT / args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("Ablation Studies")
    print("=" * 70)

    results = run_full_ablation(seed=args.seed)

    # Display summary
    print("\nComponent removal impacts:")
    for r in results["component_removal"]:
        print(f"  {r['removed']:<20} TPR={r['tpr']:.3f}  ΔTPR={r['delta_tpr']:+.4f}")

    print(
        f"\nMinimal forward:  {results['minimal_forward']['components']} (TPR={results['minimal_forward']['tpr']:.4f})"  # noqa: E501
    )  # noqa: E501
    print(
        f"Minimal backward: {results['minimal_backward']['components']} (TPR={results['minimal_backward']['tpr']:.4f})"  # noqa: E501
    )  # noqa: E501

    print("\nTop synergistic pairs:")
    for s in results["top_synergies"]:
        print(f"  {s['a']} + {s['b']}: synergy = {s['synergy']:+.4f}")

    # Save
    out_path = output_dir / "ablation_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    sys.exit(main())
