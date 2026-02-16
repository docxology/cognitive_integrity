#!/usr/bin/env python3
"""Run the full 950 x 6 detection evaluation matrix.

Produces a 36-cell matrix (6 architectures x 6 attack types) with
detection rates, false positive rates, and latency measurements.

Usage:
    python scripts/run_full_evaluation.py [--seed 42] [--output output/data]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import numpy as np

from utils.random_seed import set_global_seed
from utils.types import ExperimentConfig
from attacks.corpus import AttackCorpus
from architectures.base import ArchitectureAdapter
from architectures.claude_code import ClaudeCodeAdapter
from architectures.autogpt import AutoGPTAdapter
from architectures.crewai import CrewAIAdapter
from architectures.langgraph import LangGraphAdapter
from architectures.metagpt import MetaGPTAdapter
from architectures.camel import CamelAdapter
from evaluation.runner import ExperimentRunner
from composition.factory import create_full_pipeline


def get_all_adapters() -> list[ArchitectureAdapter]:
    """Return instances of all 6 architecture adapters."""
    return [
        ClaudeCodeAdapter(),
        AutoGPTAdapter(),
        CrewAIAdapter(),
        LangGraphAdapter(),
        MetaGPTAdapter(),
        CamelAdapter(),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run full evaluation matrix")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=str, default="output/data")
    args = parser.parse_args()

    set_global_seed(args.seed)
    output_dir = ROOT / args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("CIF Full Evaluation — 950 attacks x 6 architectures")
    print("=" * 70)

    # Generate attack corpus
    print("\n[1/3] Generating 950-attack corpus...")
    corpus = AttackCorpus.generate(seed=args.seed)
    print(f"  Corpus size: {len(corpus)}")
    for cat in ["injection", "trust_exploitation", "belief_manipulation", "coordination"]:
        samples = corpus.by_top_category(cat)
        print(f"  {cat}: {len(samples)} attacks")

    # Get adapters
    adapters = get_all_adapters()
    print(f"\n[2/3] Running evaluation across {len(adapters)} architectures...")

    # Run evaluation
    config = ExperimentConfig(seed=args.seed)
    runner = ExperimentRunner(config)
    # Convert corpus to dict format expected by run_full_matrix
    corpus_dict: dict[str, list[dict]] = {}
    for cat in ["injection", "trust_exploitation", "belief_manipulation", "coordination"]:
        samples = corpus.by_top_category(cat)
        corpus_dict[cat] = [
            {"category": s.subcategory, "content": s.payload, "is_attack": True}
            for s in samples
        ]
    pipeline = create_full_pipeline()
    results = runner.run_full_matrix(adapters, corpus_dict, pipeline)

    # Display results
    print(f"\n[3/3] Results ({len(results)} cells):")
    print("-" * 70)
    summary = runner.summary_table(results)
    header = f"{'Architecture':<20}"
    categories = sorted({r.attack_category for r in results})
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

    # Save results
    results_data = [
        {
            "architecture": r.architecture,
            "attack_category": r.attack_category,
            "n_attacks": r.n_attacks,
            "true_positives": r.true_positives,
            "false_positives": r.false_positives,
            "true_negatives": r.true_negatives,
            "false_negatives": r.false_negatives,
            "detection_rate": r.detection_rate,
            "false_positive_rate": r.false_positive_rate,
            "avg_latency_ms": r.avg_latency_ms,
        }
        for r in results
    ]
    out_path = output_dir / "full_evaluation_results.json"
    with open(out_path, "w") as f:
        json.dump(results_data, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
