#!/usr/bin/env python3
"""Run multi-seed stability analysis.

Thin orchestrator — evaluation function lives in src/statistics/stability.py.

Usage:
    python scripts/run_multi_seed.py [--n-seeds 30] [--cv-threshold 0.05] [--output output/data]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from statistics.stability import make_pipeline_eval_fn, run_multi_seed_stability


def main() -> None:
    parser = argparse.ArgumentParser(description="Run multi-seed stability analysis")
    parser.add_argument("--n-seeds", type=int, default=30)
    parser.add_argument("--cv-threshold", type=float, default=0.05)
    parser.add_argument("--output", type=str, default="output/data")
    args = parser.parse_args()

    output_dir = ROOT / args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    seeds = list(range(1, args.n_seeds + 1))

    print("=" * 70)
    print(f"Multi-Seed Stability Analysis (n={args.n_seeds})")
    print("=" * 70)

    eval_fn = make_pipeline_eval_fn()
    print("  Using real CIF pipeline")

    report = run_multi_seed_stability(eval_fn, seeds=seeds, cv_threshold=args.cv_threshold)

    # Display
    print(f"\n  Overall CV: {report.overall_cv:.4f}")
    print(f"  Threshold: {report.cv_threshold}")
    print(f"  Stable: {report.stable}")

    if report.overall_cv == 0.0:
        print("\n  ℹ NOTE: CV = 0.0000 indicates the CIF pipeline is fully deterministic.")

    if report.per_architecture_cv:
        print("\n  Per-architecture CV:")
        for arch, cv in sorted(report.per_architecture_cv.items()):
            status = "OK" if cv <= report.cv_threshold else "UNSTABLE"
            print(f"    {arch:<20} CV={cv:.4f}  [{status}]")

    if report.per_category_cv:
        print("\n  Per-category CV:")
        for cat, cv in sorted(report.per_category_cv.items()):
            status = "OK" if cv <= report.cv_threshold else "UNSTABLE"
            print(f"    {cat:<25} CV={cv:.4f}  [{status}]")

    # Save
    out_path = output_dir / "multi_seed_results.json"
    data = {
        "n_seeds": report.n_seeds,
        "overall_cv": report.overall_cv,
        "cv_threshold": report.cv_threshold,
        "stable": report.stable,
        "per_architecture_cv": report.per_architecture_cv,
        "per_category_cv": report.per_category_cv,
        "seed_metrics": [
            {"seed": m.seed, "overall": m.overall_detection_rate,
             "per_architecture": m.per_architecture, "per_category": m.per_category}
            for m in report.seed_metrics
        ],
    }
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
