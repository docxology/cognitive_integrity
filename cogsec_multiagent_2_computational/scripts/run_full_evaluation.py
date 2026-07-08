#!/usr/bin/env python3
"""Run the full 950 x 6 detection evaluation matrix.

Thin orchestrator — simulation uses src/evaluation/runner.py,
LLM mode uses src/evaluation/llm_evaluator.py.

Supports three evaluation modes:
  simulation  Parametric simulation (fast, no deps)
  pipeline    CIF defense pipeline on raw text
  llm         Real LLM multiagent simulation + CIF pipeline

Usage:
    python scripts/run_full_evaluation.py --mode simulation --seed 42
    python scripts/run_full_evaluation.py --mode llm --model gemma3:4b --sample-size 5
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import numpy as np

from architectures.autogpt import AutoGPTAdapter
from architectures.claude_code import ClaudeCodeAdapter
from architectures.crewai import CrewAIAdapter
from architectures.langgraph import LangGraphAdapter
from attacks.corpus import AttackCorpus
from evaluation.runner import ExperimentRunner
from utils.random_seed import set_global_seed
from utils.types import ExperimentConfig

logger = logging.getLogger(__name__)


def get_all_adapters():
    """Return instances of all 4 architecture adapters."""
    return [ClaudeCodeAdapter(), AutoGPTAdapter(), CrewAIAdapter(), LangGraphAdapter()]


def _create_pipeline(mode: str):
    """Create the CIF defense pipeline (or None for simulation mode)."""
    if mode == "simulation":
        return None
    from composition.factory import create_full_pipeline
    return create_full_pipeline()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run full CIF evaluation matrix",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=str, default="output/data")
    parser.add_argument(
        "--mode", type=str, default="simulation",
        choices=["simulation", "pipeline", "llm"],
    )
    parser.add_argument("--model", type=str, default="gemma3:4b")
    parser.add_argument("--sample-size", type=int, default=5)
    parser.add_argument("--replicates", type=int, default=1)
    args = parser.parse_args()

    if args.mode == "llm":
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")  # noqa: E501

    set_global_seed(args.seed)
    output_dir = ROOT / args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(f"CIF Full Evaluation — Mode: {args.mode.upper()}")
    print("=" * 70)

    # Generate attack corpus
    print("\n[1/3] Generating 950-attack corpus...")
    corpus = AttackCorpus.generate(seed=args.seed)
    print(f"  Corpus size: {len(corpus)}")

    adapters = get_all_adapters()
    print(f"\n[2/3] Running evaluation across {len(adapters)} architectures...")

    # Build corpus dict
    corpus_dict: dict[str, list[dict]] = {}
    for cat in ["injection", "trust_exploitation", "belief_manipulation", "coordination"]:
        samples = corpus.by_top_category(cat)
        if args.mode == "simulation" and args.replicates > 1:
            samples = samples * args.replicates
        corpus_dict[cat] = [
            {"category": s.subcategory, "content": s.payload, "is_attack": True}
            for s in samples
        ]

    # Save helper
    def save_results_to_file(results_list, final=False):
        if not results_list:
            return
        results_data = [
            {
                "architecture": r.architecture, "attack_category": r.attack_category,
                "n_attacks": r.n_attacks, "true_positives": r.true_positives,
                "false_positives": r.false_positives, "true_negatives": r.true_negatives,
                "false_negatives": r.false_negatives, "detection_rate": r.detection_rate,
                "false_positive_rate": r.false_positive_rate,
                "avg_latency_ms": r.avg_latency_ms, "mode": args.mode,
            }
            for r in results_list
        ]
        suffix = f"_{args.mode}" if args.mode != "simulation" else ""
        if not final:
            suffix += "_partial"
        out_path = output_dir / f"full_evaluation_results{suffix}.json"
        with open(out_path, "w") as f:
            json.dump(results_data, f, indent=2)
        if final:
            print(f"\nResults saved to {out_path}")
            partial = output_dir / f"full_evaluation_results_{args.mode}_partial.json"
            if partial.exists():
                partial.unlink()
            import datetime as _dt
            marker = output_dir / ".real_data_marker"
            marker.write_text(f"mode={args.mode} seed={args.seed} generated={_dt.datetime.now().isoformat()}\n")  # noqa: E501

    config = ExperimentConfig(seed=args.seed)
    runner = ExperimentRunner(config)
    pipeline = _create_pipeline(args.mode)

    results = []
    try:
        if args.mode == "llm":
            from evaluation.llm_evaluator import run_llm_evaluation
            results = run_llm_evaluation(
                adapters, corpus_dict, pipeline, runner,
                model=args.model, sample_size=args.sample_size,
                seed=args.seed, save_callback=save_results_to_file,
            )
        else:
            results = runner.run_full_matrix(adapters, corpus_dict, pipeline)
    finally:
        if results:
            print(f"\nSaving {len(results)} results...")
            save_results_to_file(results, final=True)

    # Display
    print(f"\n[3/3] Results ({len(results)} cells):")
    print("-" * 70)
    summary = runner.summary_table(results)
    categories = sorted({r.attack_category for r in results})
    header = f"{'Architecture':<20}"
    for cat in categories:
        header += f" {cat[:12]:>12}"
    header += f" {'Overall':>12}"
    print(header)
    print("-" * 70)
    for arch_name, cat_rates in sorted(summary.items()):
        row = f"{arch_name:<20}"
        overall_rates = []
        for cat in categories:
            rate = cat_rates.get(cat, 0.0)
            overall_rates.append(rate)
            row += f" {rate:>11.1%}"
        row += f" {np.mean(overall_rates):>11.1%}"
        print(row)
    print("-" * 70)


if __name__ == "__main__":
    main()
