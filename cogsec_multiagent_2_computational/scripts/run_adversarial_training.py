#!/usr/bin/env python3
"""Run adversarial training (AT) rounds against CIF defense thresholds.

Thin orchestrator — all logic lives in src/redteam/ (AdversarialTrainer,
NashEquilibriumEstimator). Reproduces the headline v2.0 result cited in
README.md and manuscript/05g_adversarial_training.md (per-round detection-rate
improvement and projected Nash-equilibrium detection rate).

Usage:
    uv run python scripts/run_adversarial_training.py --n-rounds 5 --seed 42
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from redteam import AdversarialTrainer, ATConfig, NashEquilibriumEstimator  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run adversarial training rounds")
    parser.add_argument("--n-rounds", type=int, default=5)
    parser.add_argument("--attacks-per-round", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=str, default="output/data")
    args = parser.parse_args()

    output_dir = ROOT / args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(f"Adversarial Training ({args.n_rounds} rounds, seed={args.seed})")
    print("=" * 70)

    config = ATConfig(
        n_rounds=args.n_rounds,
        attacks_per_round=args.attacks_per_round,
        seed=args.seed,
    )
    trainer = AdversarialTrainer(config=config)
    rounds = trainer.run()

    for r in rounds:
        print(
            f"  Round {r.round_num}: base_dr={r.base_detection_rate:.3f} "
            f"hardened_dr={r.hardened_detection_rate:.3f} "
            f"delta_dr={r.delta_dr:+.3f} ({r.primary_gap_closed})"
        )

    summary = trainer.summary()
    estimator = NashEquilibriumEstimator([r.delta_dr for r in rounds])
    summary["projected_nash_dr_independent_estimate"] = estimator.projected_equilibrium_dr(
        summary["baseline_dr"]
    )
    summary["omega_level_dr"] = trainer.omega_level_dr()

    print(f"\nBaseline DR:        {summary['baseline_dr']:.3f}")
    print(f"Final hardened DR:  {summary['final_hardened_dr']:.3f}")
    print(f"Total delta DR:     {summary['total_delta_dr']:+.3f}")
    print(f"Projected Nash DR:  {summary['projected_nash_dr']:.3f}")

    out_path = output_dir / "adversarial_training_results.json"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(out_path)


if __name__ == "__main__":
    main()
