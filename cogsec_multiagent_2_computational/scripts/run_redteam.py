#!/usr/bin/env python3
"""Run red-team attack generation and mutation-operator evasion sweep.

Thin orchestrator — all logic lives in src/redteam/generator.py
(AdversarialGenerator, AttackMutator). Reproduces the reproducibility
pointer cited in manuscript/05h_redteam_evaluation.md ("Reproducibility ...
Run via `uv run python scripts/run_redteam.py`"): per-Omega-level attack
generation plus the 12-mutation-operator evasion-rate sweep.

Note: this script generates and scores attacks against the current defense
thresholds; it does not reproduce the full campaign-orchestration framework
described in manuscript/05h_redteam_evaluation.md's module-structure diagram
(campaign.py/evasion_probe.py/scorer.py/report.py are not implemented in
src/redteam/ as of this writing -- see AGENTS.md for the as-built module list).

Usage:
    uv run python scripts/run_redteam.py --seed 42 --n-attacks 950
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from core.firewall import Classification, CognitiveFirewall  # noqa: E402
from redteam.generator import AdversarialGenerator, AttackMutator, OmegaLevel  # noqa: E402

DEFAULT_THRESHOLDS = {
    "drift_threshold": 0.3,
    "anomaly_threshold": 0.5,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run red-team evaluation")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n-attacks", type=int, default=950)
    parser.add_argument("--output", type=str, default="output/data")
    args = parser.parse_args()

    output_dir = ROOT / args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(f"Red-Team Evaluation (n_attacks={args.n_attacks}, seed={args.seed})")
    print("=" * 70)

    # --- Attack generation across the Omega_1-Omega_5 capability spectrum ---
    per_level_attacks = args.n_attacks // len(OmegaLevel)
    generation_summary: dict[str, dict] = {}
    all_attacks = []
    for level in OmegaLevel:
        gen = AdversarialGenerator(
            config_thresholds=DEFAULT_THRESHOLDS,
            omega_level=level,
            seed=args.seed,
        )
        attacks = gen.generate_batch(per_level_attacks)
        all_attacks.extend(attacks)
        mean_evasion = sum(a.evasion_score for a in attacks) / len(attacks)
        generation_summary[level.name] = {
            "n_attacks": len(attacks),
            "mean_evasion_score": mean_evasion,
        }
        print(f"  {level.name:<25} n={len(attacks):<4} mean_evasion={mean_evasion:.3f}")

    # --- Mutation-operator evasion-rate sweep ---
    # Real red-team measurement: run each attack payload through the actual
    # CognitiveFirewall before and after mutation. A mutation "succeeds" if it
    # converts a REJECT/QUARANTINE payload to ACCEPT.
    mutator = AttackMutator(seed=args.seed)
    firewall = CognitiveFirewall()
    print("\nMutation operator sweep (scored against the real CognitiveFirewall):")
    mutation_summary: dict[str, dict] = {}
    detected_attacks = [
        a for a in all_attacks if firewall.classify(a.payload) != Classification.ACCEPT
    ][:200]
    for operator in AttackMutator.MUTATION_OPERATORS:
        successes = 0
        for attack in detected_attacks:
            mutated = mutator.mutate(attack, operator)
            if firewall.classify(mutated.payload) == Classification.ACCEPT:
                successes += 1
        n = len(detected_attacks) or 1
        evasion_rate = successes / n
        mutation_summary[operator] = {
            "attempts": len(detected_attacks),
            "successful": successes,
            "evasion_rate": evasion_rate,
        }
        print(
            f"  {operator:<22} attempts={len(detected_attacks):<4} "
            f"evasion_rate={evasion_rate:.3f}"
        )

    omega_counts: dict[str, int] = defaultdict(int)
    for a in all_attacks:
        omega_counts[a.omega_level.name] += 1

    summary = {
        "seed": args.seed,
        "n_attacks_generated": len(all_attacks),
        "omega_level_counts": dict(omega_counts),
        "generation_summary": generation_summary,
        "mutation_summary": mutation_summary,
    }

    out_path = output_dir / "redteam_evaluation_results.json"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n{out_path}")


if __name__ == "__main__":
    main()
