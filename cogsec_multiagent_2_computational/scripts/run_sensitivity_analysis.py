#!/usr/bin/env python3
"""Run parameter sensitivity analysis.

Sweeps key parameters and measures detection rate sensitivity.

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

import numpy as np

from utils.random_seed import set_global_seed
from statistics.sensitivity import parameter_sweep, grid_search_2d, compute_sensitivity_index


def _make_evaluate_fn(rng: np.random.Generator):
    """Create evaluation function parameterized by defense thresholds."""

    def evaluate(injection_threshold: float = 0.7, drift_threshold: float = 0.3,
                 trust_decay: float = 0.85, consensus_quorum: float = 0.667) -> float:
        """Simulate detection rate for given parameter settings."""
        # Model: detection rate is a function of threshold interactions
        base = 0.85
        # Injection threshold: too low = false positives, too high = misses
        inj_effect = -2.0 * (injection_threshold - 0.65) ** 2 + 0.10
        # Drift threshold: lower is more sensitive
        drift_effect = -1.5 * (drift_threshold - 0.25) ** 2 + 0.06
        # Trust decay: moderate values optimal
        trust_effect = -3.0 * (trust_decay - 0.85) ** 2 + 0.05
        # Consensus quorum: 2/3 is optimal
        quorum_effect = -2.5 * (consensus_quorum - 0.667) ** 2 + 0.04

        rate = base + inj_effect + drift_effect + trust_effect + quorum_effect
        rate += rng.normal(0, 0.005)
        return float(np.clip(rate, 0.0, 1.0))

    return evaluate


def main() -> None:
    parser = argparse.ArgumentParser(description="Run sensitivity analysis")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=str, default="output/data")
    args = parser.parse_args()

    rng = set_global_seed(args.seed)
    output_dir = ROOT / args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    evaluate = _make_evaluate_fn(rng)

    print("=" * 70)
    print("Parameter Sensitivity Analysis")
    print("=" * 70)

    # 1. Individual parameter sweeps
    print("\n[1/3] Individual parameter sweeps...")
    sweeps = []

    params = {
        "injection_threshold": np.linspace(0.3, 0.9, 25),
        "drift_threshold": np.linspace(0.1, 0.6, 25),
        "trust_decay": np.linspace(0.5, 0.99, 25),
        "consensus_quorum": np.linspace(0.5, 0.9, 25),
    }

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
        "injection_threshold", np.linspace(0.4, 0.8, 15),
        "drift_threshold", np.linspace(0.15, 0.45, 15),
        lambda p1, p2: evaluate(injection_threshold=p1, drift_threshold=p2),
    )
    best_params = grid_result["best_params"]
    print(f"  Best combination: injection={best_params['injection_threshold']:.3f}, drift={best_params['drift_threshold']:.3f}")
    print(f"  Detection rate: {grid_result['best_metric']:.4f}")

    # Save
    out_path = output_dir / "sensitivity_results.json"
    data = {
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
    main()
