#!/usr/bin/env python3
"""Run all statistical hypothesis tests for manuscript claims.

Thin orchestrator — all logic lives in src/statistics/analysis_runner.py.

Usage:
    python scripts/run_statistical_analysis.py [--seed 42] [--output output/data]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from statistics.analysis_runner import load_real_data, run_full_analysis

from utils.random_seed import set_global_seed


def main() -> None:
    parser = argparse.ArgumentParser(description="Run statistical analysis")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=str, default="output/data")
    args = parser.parse_args()

    rng = set_global_seed(args.seed)
    output_dir = ROOT / args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    eval_path = output_dir / "full_evaluation_results.json"
    ablation_path = output_dir / "ablation_results.json"

    print("=" * 70)
    print("Statistical Analysis — Manuscript Hypothesis Tests")
    print("=" * 70)

    data = load_real_data(eval_path, ablation_path, rng)
    results = run_full_analysis(data, seed=args.seed)

    # Display summary
    print(f"\n  H1 p-value: {results['h1']['p_value']:.2e}  (sig={results['h1']['significant']})")
    print(f"  Cohen's d:  {results['cohens_d_cif_vs_baseline']:.2f}")
    print(f"  KW H:       {results['kruskal_wallis']['h']:.2f}")
    print(f"  KW p:       {results['kruskal_wallis']['p']:.4e}")

    # Save. Provenance is emitted in two complementary forms: the top-level
    # preservation marker (data_origin/source_script/generated_by/seed) so the
    # shipped artifact is never clobbered by DataGenerator's synthetic output,
    # and an honest nested `provenance` block documenting that the CIF values
    # are compared against a *simulated* control (no observed control arm ran).
    out_path = output_dir / "statistical_results.json"
    payload = {
        "data_origin": "real_pipeline",  # preservation marker for a shipped result
        "source_script": "scripts/run_statistical_analysis.py",
        "generated_by": (
            f"scripts/run_statistical_analysis.py --seed {args.seed} "
            f"--output {str(args.output)}"
        ),
        "seed": args.seed,
        **results,
    }
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2, default=float)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
