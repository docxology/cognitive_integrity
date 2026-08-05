#!/usr/bin/env python3
"""Run parameter sensitivity analysis.

Thin orchestrator — evaluation function lives in src/statistics/sensitivity.py.

Usage:
    python scripts/run_sensitivity_analysis.py [--seed 42] [--output output/data]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from statistics.sensitivity import (
    compute_sensitivity_index,
    grid_search_2d,
    make_default_evaluate_fn,
    parameter_sweep,
)

import numpy as np

from utils.random_seed import set_global_seed


def main() -> None:
    parser = argparse.ArgumentParser(description="Run sensitivity analysis")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=str, default="output/data")
    args = parser.parse_args()

    rng = set_global_seed(args.seed)
    output_dir = ROOT / args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    evaluate = make_default_evaluate_fn(rng)

    print("=" * 70)
    print("Parameter Sensitivity Analysis")
    print("=" * 70)

    # 1. Individual parameter sweeps
    print("\n[1/3] Individual parameter sweeps...")
    params = {
        "injection_threshold": np.linspace(0.3, 0.9, 25),
        "drift_threshold": np.linspace(0.1, 0.6, 25),
        "trust_decay": np.linspace(0.5, 0.99, 25),
        "consensus_quorum": np.linspace(0.5, 0.9, 25),
    }
    sweeps = []
    for param_name, param_range in params.items():

        def eval_single(val, _pn=param_name):
            return evaluate(**{_pn: val})

        result = parameter_sweep(param_name, param_range, eval_single)
        sweeps.append(result)
        print(f"  {param_name}: best={result.best_value:.3f} (DR={result.best_metric:.4f})")

    # 2. Sensitivity ranking
    print("\n[2/3] Sensitivity index ranking...")
    sensitivity = compute_sensitivity_index(sweeps)
    for name, idx in sorted(sensitivity.items(), key=lambda x: -x[1]):
        print(f"  {name}: {idx:.4f}")

    # 3. 2D grid search
    print("\n[3/3] 2D parameter interaction grid...")
    grid_result = grid_search_2d(
        "injection_threshold",
        np.linspace(0.4, 0.8, 15),
        "drift_threshold",
        np.linspace(0.15, 0.45, 15),
        lambda p1, p2: evaluate(injection_threshold=p1, drift_threshold=p2),
    )
    best_params = grid_result["best_params"]
    print(
        f"  Best: injection={best_params['injection_threshold']:.3f}, drift={best_params['drift_threshold']:.3f}"  # noqa: E501
    )  # noqa: E501
    print(f"  Detection rate: {grid_result['best_metric']:.4f}")

    # Save — with honest provenance.  This analysis evaluates a closed-form
    # quadratic response-surface model (make_default_evaluate_fn), NOT the
    # measured pipeline, so it is stamped `parametric_simulation` and never
    # `real_pipeline` (a machine reader must not mistake design-model numbers
    # for measurements; P2-1).
    out_path = output_dir / "sensitivity_results.json"
    data = {
        "data_origin": "parametric_simulation",
        "source_script": "scripts/run_sensitivity_analysis.py",
        "generated_by": (
            "scripts/run_sensitivity_analysis.py --seed {args.seed} --output {args.output}"
        ),
        "seed": args.seed,
        "provenance": {
            "measurement": (
                "closed-form parametric response-surface model "
                "(quadratic interaction effects + Gaussian noise); not a "
                "pipeline-in-the-loop measurement. Do not report these "
                "numbers as measured detection rates."
            ),
            "model": "statistics.sensitivity.make_default_evaluate_fn",
        },
        "sweeps": [
            {
                "parameter": s.parameter_name,
                "best_value": float(s.best_value),
                "best_metric": float(s.best_metric),
                "values": s.values.tolist(),
                "metrics": s.metric_values.tolist(),
            }
            for s in sweeps
        ],
        "sensitivity_index": sensitivity,
        "grid_best": {
            "injection": best_params["injection_threshold"],
            "drift": best_params["drift_threshold"],
            "dr": grid_result["best_metric"],
        },
    }
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2, default=float)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    sys.exit(main())
