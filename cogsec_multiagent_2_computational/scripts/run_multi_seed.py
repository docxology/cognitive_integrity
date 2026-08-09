#!/usr/bin/env python3
"""Run multi-seed stability analysis over both arms of the evaluation.

Thin orchestrator — evaluation function lives in src/statistics/stability.py.

Each seed is scored on an attack corpus (true-positive rate) *and* on a
benign corpus (false-positive rate), so the reported detection rate has an
operating point attached.  A detection rate published without its FPR cannot
be distinguished from a flag-everything detector.

Usage:
    python scripts/run_multi_seed.py [--n-seeds 30] [--seed 1]
                                     [--cv-threshold 0.05]
                                     [--benign-per-stratum 10]
                                     [--output output/data]

``--seed`` is the first seed of the evaluated block: the default
``--seed 1 --n-seeds 30`` evaluates seeds 1..30, which is the seed set the
published multi-seed figures were measured on.
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
    parser.add_argument(
        "--seed",
        type=int,
        default=1,
        help="First seed of the evaluated block (seeds are seed..seed+n_seeds-1)",
    )
    parser.add_argument("--cv-threshold", type=float, default=0.05)
    parser.add_argument(
        "--benign-per-stratum",
        type=int,
        default=10,
        help="Benign samples per (category, difficulty) stratum; 12 strata total",
    )
    parser.add_argument("--output", type=str, default="output/data")
    args = parser.parse_args()

    output_dir = ROOT / args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    seeds = list(range(args.seed, args.seed + args.n_seeds))

    print("=" * 70)
    print(f"Multi-Seed Stability Analysis (n={args.n_seeds}, seeds {seeds[0]}..{seeds[-1]})")
    print("=" * 70)

    eval_fn = make_pipeline_eval_fn(benign_per_stratum=args.benign_per_stratum)
    print("  Using real CIF pipeline (attack arm + benign arm)")

    report = run_multi_seed_stability(eval_fn, seeds=seeds, cv_threshold=args.cv_threshold)

    # A missing benign arm is a hard error, not a footnote: every paired
    # number below would be a default rather than a measurement.
    if not report.benign_arm_present:
        raise SystemExit(
            "ERROR: no benign arm was evaluated — TPR alone is not an operating point. "
            "This indicates make_pipeline_eval_fn was bypassed or the benign corpus is empty."
        )

    # Display
    print(f"\n  Mean TPR (attack arm):  {report.tpr_mean:.4f}")
    assert report.fpr_mean is not None  # guaranteed by benign_arm_present
    assert report.youden_j_mean is not None
    assert report.precision_mean is not None
    assert report.f1_mean is not None
    print(f"  Mean FPR (benign arm):  {report.fpr_mean:.4f}")
    print(f"  Youden's J (TPR-FPR):   {report.youden_j_mean:.4f}")
    print(f"  Precision:              {report.precision_mean:.4f}")
    print(f"  F1:                     {report.f1_mean:.4f}")
    print(f"\n  Overall CV: {report.overall_cv:.4f}")
    if report.fpr_cv is not None:
        print(f"  FPR CV:     {report.fpr_cv:.4f}")
    print(f"  Threshold: {report.cv_threshold}")
    print(f"  Stable: {report.stable}")

    if report.overall_cv == 0.0:
        print("\n  ℹ NOTE: CV = 0.0000 indicates the CIF pipeline is fully deterministic.")

    if report.benign_fpr_by_difficulty_mean:
        print("\n  Benign FPR by difficulty stratum:")
        for name, val in sorted(report.benign_fpr_by_difficulty_mean.items()):
            print(f"    {name:<20} FPR={val:.4f}")

    if report.benign_fpr_by_category_mean:
        print("\n  Benign FPR by message category:")
        for name, val in sorted(report.benign_fpr_by_category_mean.items()):
            print(f"    {name:<20} FPR={val:.4f}")

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

    # Save.  Existing keys are preserved verbatim so downstream readers
    # (manuscript injector, stability tables) keep working; the benign-arm
    # keys are additive.
    out_path = output_dir / "multi_seed_results.json"
    data = {
        "data_origin": "real_pipeline",
        "source_script": "scripts/run_multi_seed.py",
        "n_seeds": report.n_seeds,
        "first_seed": seeds[0],
        "overall_cv": report.overall_cv,
        "cv_threshold": report.cv_threshold,
        "stable": report.stable,
        "per_architecture_cv": report.per_architecture_cv,
        "architecture_scope": (
            "not_applicable: one architecture-agnostic CIF pipeline"
            if not report.per_architecture_cv
            else "multiple architecture series"
        ),
        "per_category_cv": report.per_category_cv,
        "benign_arm_present": report.benign_arm_present,
        "benign_per_stratum": args.benign_per_stratum,
        "tpr_mean": report.tpr_mean,
        "fpr_mean": report.fpr_mean,
        "fpr_cv": report.fpr_cv,
        "precision_mean": report.precision_mean,
        "f1_mean": report.f1_mean,
        "youden_j_mean": report.youden_j_mean,
        "benign_fpr_by_difficulty_mean": report.benign_fpr_by_difficulty_mean,
        "benign_fpr_by_category_mean": report.benign_fpr_by_category_mean,
        "seed_metrics": [
            {
                "seed": m.seed,
                "overall": m.overall_detection_rate,
                "per_architecture": m.per_architecture,
                "per_category": m.per_category,
                "false_positive_rate": m.false_positive_rate,
                "n_attacks": m.n_attacks,
                "n_detected_attacks": m.n_detected_attacks,
                "n_benign": m.n_benign,
                "n_false_positives": m.n_false_positives,
                "youden_j": m.youden_j,
                "precision": m.precision,
                "f1": m.f1,
                "benign_fpr_by_difficulty": m.benign_fpr_by_difficulty,
                "benign_fpr_by_category": m.benign_fpr_by_category,
            }
            for m in report.seed_metrics
        ],
    }
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    sys.exit(main())
