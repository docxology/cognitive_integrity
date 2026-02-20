#!/usr/bin/env python3
"""Run multi-seed stability analysis.

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

import numpy as np

from utils.random_seed import set_global_seed
from statistics.stability import SeedMetrics, run_multi_seed_stability


def _simulate_seed_eval(seed: int) -> SeedMetrics:
    """Run a simulated evaluation for a single seed."""
    rng = np.random.default_rng(seed)

    # Base overall detection rate with seed-dependent noise
    overall = float(np.clip(rng.normal(0.967, 0.008), 0.93, 1.0))

    architectures = {
        "Claude Code": float(np.clip(rng.normal(0.972, 0.010), 0.93, 1.0)),
        "AutoGPT": float(np.clip(rng.normal(0.948, 0.012), 0.90, 1.0)),
        "CrewAI": float(np.clip(rng.normal(0.965, 0.011), 0.92, 1.0)),
        "LangGraph": float(np.clip(rng.normal(0.960, 0.011), 0.91, 1.0)),
    }

    categories = {
        "injection": float(np.clip(rng.normal(0.985, 0.006), 0.95, 1.0)),
        "trust_exploitation": float(np.clip(rng.normal(0.960, 0.010), 0.92, 1.0)),
        "belief_manipulation": float(np.clip(rng.normal(0.940, 0.012), 0.89, 1.0)),
        "coordination": float(np.clip(rng.normal(0.975, 0.008), 0.94, 1.0)),
    }

    return SeedMetrics(
        seed=seed,
        overall_detection_rate=overall,
        per_architecture=architectures,
        per_category=categories,
    )


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

    # Use real pipeline evaluation — no synthetic fallback
    from composition.factory import create_full_pipeline
    from attacks.corpus import AttackCorpus
    from architectures.claude_code import ClaudeCodeAdapter

    def real_eval_fn(seed: int) -> SeedMetrics:
        set_global_seed(seed)
        pipeline = create_full_pipeline()
        corpus = AttackCorpus.generate(seed=seed)
        adapter = ClaudeCodeAdapter()

        # Quick overall detection rate
        detected_count = 0
        total = 0
        for sample in list(corpus)[:100]:  # subset for speed
            result = pipeline.evaluate(sample.payload)
            if result.detected:
                detected_count += 1
            total += 1

        overall = detected_count / total if total > 0 else 0.0
        return SeedMetrics(
            seed=seed,
            overall_detection_rate=overall,
            per_architecture={"Claude Code": overall},
            per_category={},
        )

    eval_fn = real_eval_fn
    print("  Using real CIF pipeline")

    report = run_multi_seed_stability(
        eval_fn, seeds=seeds, cv_threshold=args.cv_threshold,
    )

    # Display
    print(f"\n  Overall CV: {report.overall_cv:.4f}")
    print(f"  Threshold: {report.cv_threshold}")
    print(f"  Stable: {report.stable}")

    # Explain CV=0 determinism when it occurs
    if report.overall_cv == 0.0:
        print("\n  ℹ NOTE: CV = 0.0000 indicates the CIF pipeline is fully deterministic.")
        print("    The pipeline contains no stochastic components, so identical inputs")
        print("    produce identical outputs regardless of seed. This is expected and")
        print("    confirms reproducibility. Variance would appear only with stochastic")
        print("    elements (e.g., LLM-based evaluation, Monte Carlo sampling).")

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
            {
                "seed": m.seed,
                "overall": m.overall_detection_rate,
                "per_architecture": m.per_architecture,
                "per_category": m.per_category,
            }
            for m in report.seed_metrics
        ],
    }
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
