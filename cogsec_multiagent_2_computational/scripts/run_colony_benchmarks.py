#!/usr/bin/env python3
"""Run colony-level CogSec benchmarks over a seed sweep.

Executes 5 colony scenarios ``--n-repeats`` times on distinct seeds and
reports each headline metric as a mean with a 95% bootstrap confidence
interval plus the observed min/max.  Single-run point estimates from a
stochastic multi-agent simulation are not publishable numbers; the sweep is
the default and ``--n-repeats 1`` exists only to reproduce the legacy
single-seed artifact for comparison.

Usage:
    python scripts/run_colony_benchmarks.py [--seed 42] [--n-repeats 30] \
        [--output output/data]
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from colony.benchmark import ColonyBenchmark, ColonyScenarioSummary
from utils.random_seed import set_global_seed


def _summary_record(summary: ColonyScenarioSummary) -> dict:
    """Serialise one scenario summary, including every per-repeat value.

    Deliberately omits bare ``detection_rate`` / ``false_positive_rate`` /
    ``ccs_score`` keys.  Those names previously held a single-seed draw; a
    consumer that still expects them must fail loudly rather than silently
    read a seed-sweep mean under the old name.
    """
    first = summary.runs[0]
    config = first.config
    return {
        "scenario": summary.scenario_name,
        "n_agents": config.n_agents if config is not None else None,
        "n_steps": config.n_steps if config is not None else None,
        "n_adversaries": config.n_adversaries if config is not None else None,
        "n_repeats": summary.n_repeats,
        "seeds": summary.seeds,
        "detection_rate_mean": summary.detection_rate_mean,
        "detection_rate_ci95": list(summary.detection_rate_ci95),
        "detection_rate_min": summary.detection_rate_range[0],
        "detection_rate_max": summary.detection_rate_range[1],
        "detection_rate_values": summary.detection_rate_values,
        "false_positive_rate_mean": summary.fpr_mean,
        "false_positive_rate_ci95": list(summary.fpr_ci95),
        "false_positive_rate_min": summary.fpr_range[0],
        "false_positive_rate_max": summary.fpr_range[1],
        "false_positive_rate_values": summary.fpr_values,
        "ccs_score_mean": summary.ccs_mean,
        "ccs_score_ci95": list(summary.ccs_ci95),
        "ccs_score_min": summary.ccs_range[0],
        "ccs_score_max": summary.ccs_range[1],
        "ccs_score_values": summary.ccs_values,
        "resilience_score_values": [r.resilience_score for r in summary.runs],
        "recovery_steps_values": [r.recovery_steps for r in summary.runs],
        # Guarantee-shaped claims must hold on *every* repeat, not on average.
        "detection_perfect_all_seeds": summary.all_runs_at("detection_rate", 1.0),
        "fpr_zero_all_seeds": summary.all_runs_at("false_positive_rate", 0.0),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run colony benchmarks")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--n-repeats",
        type=int,
        default=30,
        help="Seeds per scenario (default 30; 1 reproduces the legacy artifact)",
    )
    parser.add_argument("--output", type=str, default="output/data")
    args = parser.parse_args()

    if args.n_repeats < 1:
        parser.error("--n-repeats must be >= 1")

    set_global_seed(args.seed)
    output_dir = ROOT / args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 78)
    print(f"Colony-Level CogSec Benchmarks  (n_repeats={args.n_repeats}, seed={args.seed})")
    print("=" * 78)

    benchmark = ColonyBenchmark()
    summaries = benchmark.run_all_repeated(seed=args.seed, n_repeats=args.n_repeats)

    header = (
        f"{'Scenario':<24} {'DR mean':>9} {'DR 95% CI':>20} "
        f"{'FPR mean':>10} {'FPR range':>22} {'CCS mean':>9}"
    )
    print("\n" + header)
    print("-" * len(header))
    for s in summaries:
        dr_ci = f"[{s.detection_rate_ci95[0]:.4f}, {s.detection_rate_ci95[1]:.4f}]"
        fpr_rng = f"[{s.fpr_range[0]:.5f}, {s.fpr_range[1]:.5f}]"
        print(
            f"{s.scenario_name:<24} "
            f"{s.detection_rate_mean:>9.4f} "
            f"{dr_ci:>20} "
            f"{s.fpr_mean:>10.5f} "
            f"{fpr_rng:>22} "
            f"{s.ccs_mean:>9.4f}"
        )
    print("-" * len(header))

    print("\nGuarantee checks (must hold on EVERY seed, not on average):")
    for s in summaries:
        print(
            f"  {s.scenario_name:<24} "
            f"detection==1.0 on all {s.n_repeats} seeds: "
            f"{s.all_runs_at('detection_rate', 1.0)!s:<5}  "
            f"FPR==0.0 on all {s.n_repeats} seeds: "
            f"{s.all_runs_at('false_positive_rate', 0.0)!s}"
        )

    payload = {
        "data_origin": "real_pipeline",
        "generator": "scripts/run_colony_benchmarks.py",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "base_seed": args.seed,
        "n_repeats": args.n_repeats,
        "ci_method": "bootstrap percentile over per-seed values, B=2000, 95%",
        "python": platform.python_version(),
        "scenarios": [_summary_record(s) for s in summaries],
    }

    out_path = output_dir / "colony_results.json"
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"\nSeed-sweep results saved to {out_path}")

    # Backwards-compatible point-estimate file: first repeat of each scenario,
    # explicitly labelled as a single draw so no consumer mistakes it for the
    # published estimate.
    legacy = {
        "data_origin": "real_pipeline",
        "generator": "scripts/run_colony_benchmarks.py",
        "note": (
            "Single-seed draw (repeat 0) retained for comparison only. "
            "Published numbers must come from colony_results.json, which "
            "reports the seed sweep with confidence intervals."
        ),
        "base_seed": args.seed,
        "results": [
            {
                "scenario": r.scenario_name,
                "seed": r.config.seed if r.config is not None else None,
                "n_agents": r.config.n_agents if r.config is not None else None,
                "n_steps": r.config.n_steps if r.config is not None else None,
                "n_adversaries": r.config.n_adversaries if r.config is not None else None,
                "detection_rate": r.detection_rate,
                "false_positive_rate": r.false_positive_rate,
                "resilience_score": r.resilience_score,
                "recovery_steps": r.recovery_steps,
                "ccs_score": r.ccs_score,
            }
            for r in (s.runs[0] for s in summaries)
        ],
    }
    legacy_path = output_dir / "colony_results_single_seed.json"
    with open(legacy_path, "w") as f:
        json.dump(legacy, f, indent=2)
    print(f"Single-seed draw saved to {legacy_path}")


if __name__ == "__main__":
    main()
