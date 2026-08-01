#!/usr/bin/env python3
"""Run red-team attack generation and the mutation-operator evasion sweep.

Thin orchestrator — generation lives in ``src/redteam/generator.py``
(``AdversarialGenerator``, ``AttackMutator``) and the sweep in
``src/redteam/evasion.py``.

What changed and why
--------------------
The sweep used to draw its denominator from ``AdversarialGenerator``, which
emits one of only 16 distinct template payloads no matter how large ``n`` is.
Of those 16 the firewall flags exactly one ("Ignore previous instructions.
Execute: ..."), so a "950-attack" sweep measured 67 copies of a single string
and reported ``attempts=67 evasion_rate=0.000`` for all twelve operators — a
uniformly-zero result over an effective sample size of one.

The denominator now comes from the real 950-sample :class:`AttackCorpus`
(871 distinct payloads, 66 distinct payloads flagged at seed 42), is
de-duplicated, is guarded by ``--min-denominator``, and every rate carries a
Wilson interval.  The generator sweep is still reported, but under
``generation_summary`` with an explicit ``n_distinct_payloads`` field so its
degeneracy is visible rather than hidden.

Usage:
    uv run python scripts/run_redteam.py --seed 42
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from attacks.corpus import AttackCorpus  # noqa: E402
from core.firewall import Classification, CognitiveFirewall  # noqa: E402
from redteam.evasion import (  # noqa: E402
    DEFAULT_MIN_DENOMINATOR,
    VacuousSweepError,
    flagged_payloads,
    run_evasion_sweep,
)
from redteam.generator import AdversarialGenerator, AttackMutator, OmegaLevel  # noqa: E402

DEFAULT_THRESHOLDS = {
    "drift_threshold": 0.3,
    "anomaly_threshold": 0.5,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run red-team evaluation")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--n-attacks",
        type=int,
        default=950,
        help="Attacks drawn from AdversarialGenerator for the Omega-level summary.",
    )
    parser.add_argument(
        "--min-denominator",
        type=int,
        default=DEFAULT_MIN_DENOMINATOR,
        help=(
            "Refuse to report evasion rates over fewer than this many distinct "
            "flagged corpus payloads."
        ),
    )
    parser.add_argument("--output", type=str, default="output/data")
    args = parser.parse_args(argv)

    output_dir = Path(args.output)
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(f"Red-Team Evaluation (n_attacks={args.n_attacks}, seed={args.seed})")
    print("=" * 70)

    firewall = CognitiveFirewall()

    def is_flagged(payload: str) -> bool:
        return firewall.classify(payload) != Classification.ACCEPT

    # --- Attack generation across the Omega_1-Omega_5 capability spectrum ---
    # Reported for completeness. NOTE: the generator is template-driven, so
    # n_distinct_payloads is far below n_attacks; it is printed so nobody
    # mistakes the batch size for a sample size.
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
        distinct = len({a.payload for a in attacks})
        generation_summary[level.name] = {
            "n_attacks": len(attacks),
            "n_distinct_payloads": distinct,
            "mean_evasion_score": mean_evasion,
        }
        print(
            f"  {level.name:<25} n={len(attacks):<4} distinct={distinct:<3} "
            f"mean_evasion={mean_evasion:.3f}"
        )

    # --- Mutation-operator evasion-rate sweep over the real 950-attack corpus ---
    corpus = AttackCorpus.generate(seed=args.seed)
    corpus_payloads = [s.payload for s in corpus]
    denominator = flagged_payloads(corpus_payloads, is_flagged)
    print(
        f"\nCorpus: {len(corpus)} samples, "
        f"{len(set(corpus_payloads))} distinct payloads, "
        f"{len(denominator)} distinct payloads flagged by CognitiveFirewall"
    )

    mutator = AttackMutator(seed=args.seed)
    try:
        sweep = run_evasion_sweep(
            denominator,
            AttackMutator.MUTATION_OPERATORS,
            mutator.mutate_payload,
            is_flagged,
            min_denominator=args.min_denominator,
        )
    except VacuousSweepError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        return 1

    print("\nMutation operator sweep (scored against the real CognitiveFirewall):")
    mutation_summary: dict[str, dict] = {}
    for operator, res in sweep.items():
        mutation_summary[operator] = res.to_dict()
        print(
            f"  {operator:<22} {res.successes}/{res.attempts} "
            f"evasion_rate={res.evasion_rate:.4f} "
            f"95% CI [{res.ci_low:.4f}, {res.ci_high:.4f}]"
        )

    omega_counts: dict[str, int] = defaultdict(int)
    for a in all_attacks:
        omega_counts[a.omega_level.name] += 1

    summary = {
        # Provenance follows the convention of the other committed artifacts
        # (multi_seed_results.json, cross_validation_results.json): origin plus
        # source script, and deliberately NO timestamp, so re-running at the
        # same seed reproduces the file byte-for-byte.
        "data_origin": "real_pipeline",
        "source_script": "scripts/run_redteam.py",
        "seed": args.seed,
        "n_attacks_generated": len(all_attacks),
        "omega_level_counts": dict(omega_counts),
        "generation_summary": generation_summary,
        "evasion_denominator": {
            "source": "attacks.corpus.AttackCorpus.generate(seed)",
            "corpus_size": len(corpus),
            "corpus_distinct_payloads": len(set(corpus_payloads)),
            "distinct_flagged_payloads": len(denominator),
            "min_denominator": args.min_denominator,
            "unit": "distinct payload (duplicates collapsed)",
        },
        "mutation_summary": mutation_summary,
    }

    out_path = output_dir / "redteam_evaluation_results.json"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
        f.write("\n")
    print(f"\n{out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
