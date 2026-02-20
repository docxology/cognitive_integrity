#!/usr/bin/env python3
"""Run the full 950 x 6 detection evaluation matrix.

Produces a 36-cell matrix (6 architectures x 6 attack types) with
detection rates, false positive rates, and latency measurements.

Supports three evaluation modes:
    - simulation: Parametric simulation (fast, no dependencies)
    - pipeline:   CIF defense pipeline on raw attack text
    - llm:        Real LLM multiagent simulation + CIF pipeline (requires Ollama)

Usage:
    python scripts/run_full_evaluation.py --mode simulation
    python scripts/run_full_evaluation.py --mode pipeline
    python scripts/run_full_evaluation.py --mode llm --model gemma3:4b --sample-size 50
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
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
from evaluation.runner import ExperimentRunner

logger = logging.getLogger(__name__)


def get_all_adapters() -> list[ArchitectureAdapter]:
    """Return instances of all 4 architecture adapters.

    Each adapter represents a distinct communication topology:
      - Claude Code: hub-spoke (hierarchical delegation)
      - AutoGPT: mesh (autonomous with reviewer)
      - CrewAI: chain (role-based sequential)
      - LangGraph: mesh (state-machine routing, deep delegation)
    """
    return [
        ClaudeCodeAdapter(),
        AutoGPTAdapter(),
        CrewAIAdapter(),
        LangGraphAdapter(),
    ]


def _create_pipeline(mode: str):
    """Create the CIF defense pipeline (or None for simulation mode)."""
    if mode == "simulation":
        return None
    from composition.factory import create_full_pipeline
    return create_full_pipeline()


def _run_llm_mode(
    runner: ExperimentRunner,
    adapters: list[ArchitectureAdapter],
    corpus_dict: dict[str, list[dict]],
    pipeline,
    model: str,
    sample_size: int,
    seed: int,
):
    """Run evaluation in LLM multiagent mode."""
    from agents.multiagent_system import MultiAgentSystem
    from agents.llm_agent import OllamaConfig

    # Check Ollama availability
    import requests
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=3)
        resp.raise_for_status()
        models = [m["name"] for m in resp.json().get("models", [])]
        print(f"  Ollama available. Models: {', '.join(models[:5])}")
        if model not in models and f"{model}:latest" not in models:
            print(f"  WARNING: Model '{model}' not found locally. Ollama will pull it.")
    except Exception as e:
        print(f"  ERROR: Cannot reach Ollama at localhost:11434: {e}")
        print("  Start Ollama with: ollama serve")
        sys.exit(1)

    config = OllamaConfig(model=model, seed=seed)
    results = []
    rng = np.random.default_rng(seed)

    total_attacks = sum(len(s) for s in corpus_dict.values())
    print(f"\n  LLM Mode: {model} | {sample_size}/{total_attacks} samples/category")
    print(f"  Estimated time: ~{len(adapters) * len(corpus_dict) * sample_size * 5}s")
    print()

    for adapter in adapters:
        arch_name = adapter.profile.name
        print(f"  [{arch_name}] Creating multiagent system...")
        llm_system = MultiAgentSystem(
            adapter=adapter, config=config, seed=seed,
        )

        for cat_key, samples in corpus_dict.items():
            # Downsample for LLM mode
            if len(samples) > sample_size:
                indices = rng.choice(len(samples), size=sample_size, replace=False)
                samples_subset = [samples[i] for i in sorted(indices)]
            else:
                samples_subset = samples

            t0 = time.time()
            result = runner.run_single_llm(
                adapter, samples_subset, pipeline, llm_system,
            )
            elapsed = time.time() - t0

            print(
                f"    {cat_key}: DR={result.detection_rate:.1%} "
                f"FPR={result.false_positive_rate:.1%} "
                f"n={result.n_attacks} ({elapsed:.1f}s)"
            )
            results.append(result)

    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run full CIF evaluation matrix",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Modes:\n"
            "  simulation  Parametric simulation (fast, no deps)\n"
            "  pipeline    CIF defense pipeline on raw text\n"
            "  llm         Real LLM multiagent simulation + CIF pipeline\n"
        ),
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=str, default="output/data")
    parser.add_argument(
        "--mode", type=str, default="pipeline",
        choices=["simulation", "pipeline", "llm"],
        help="Evaluation mode (default: pipeline)",
    )
    parser.add_argument(
        "--model", type=str, default="gemma3:4b",
        help="Ollama model for LLM mode (default: gemma3:4b)",
    )
    parser.add_argument(
        "--sample-size", type=int, default=50,
        help="Max attacks per category in LLM mode (default: 50)",
    )
    parser.add_argument(
        "--replicates", type=int, default=1,
        help="Number of replicates for simulation mode (default: 1)",
    )
    args = parser.parse_args()

    # Configure logging for LLM mode
    if args.mode == "llm":
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        )

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
    for cat in ["injection", "trust_exploitation", "belief_manipulation", "coordination"]:
        samples = corpus.by_top_category(cat)
        print(f"  {cat}: {len(samples)} attacks")

    # Get adapters
    adapters = get_all_adapters()
    print(f"\n[2/3] Running evaluation across {len(adapters)} architectures...")

    # Build corpus dict
    corpus_dict: dict[str, list[dict]] = {}
    for cat in ["injection", "trust_exploitation", "belief_manipulation", "coordination"]:
        samples = corpus.by_top_category(cat)
        # Apply replicates for simulation mode
        if args.mode == "simulation" and args.replicates > 1:
            samples = samples * args.replicates
            
        corpus_dict[cat] = [
            {"category": s.subcategory, "content": s.payload, "is_attack": True}
            for s in samples
        ]
    
    if args.mode == "simulation" and args.replicates > 1:
        print(f"  Applying {args.replicates}x replication. Total samples per architecture: {sum(len(v) for v in corpus_dict.values())}")

    # Define save helper
    def save_results_to_file(results_list, final=False):
        if not results_list:
            return
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
                "mode": args.mode,
            }
            for r in results_list
        ]
        suffix = f"_{args.mode}" if args.mode != "pipeline" else ""
        if not final:
            suffix += "_partial"
        out_path = output_dir / f"full_evaluation_results{suffix}.json"
        with open(out_path, "w") as f:
            json.dump(results_data, f, indent=2)
        if final:
            print(f"\nResults saved to {out_path}")
            # Clean up partial file if it exists
            partial = output_dir / f"full_evaluation_results_{args.mode}_partial.json"
            if partial.exists():
                partial.unlink()

    # Run evaluation
    config = ExperimentConfig(seed=args.seed)
    runner = ExperimentRunner(config)
    pipeline = _create_pipeline(args.mode)

    results = []
    try:
        if args.mode == "llm":
            # Modified _run_llm_mode inline to support incremental saving
            # (Refactoring slightly to avoid changing function signature too much)
            
            # Check Ollama first
            import requests
            try:
                resp = requests.get("http://localhost:11434/api/tags", timeout=3)
                resp.raise_for_status()
                models = [m["name"] for m in resp.json().get("models", [])]
                print(f"  Ollama available. Models: {', '.join(models[:5])}")
                if args.model not in models and f"{args.model}:latest" not in models:
                    print(f"  WARNING: Model '{args.model}' not found locally. Ollama will pull it.")
            except Exception as e:
                print(f"  ERROR: Cannot reach Ollama at localhost:11434: {e}")
                print("  Start Ollama with: ollama serve")
                sys.exit(1)

            from agents.multiagent_system import MultiAgentSystem
            from agents.llm_agent import OllamaConfig

            llm_config = OllamaConfig(model=args.model, seed=args.seed)
            rng = np.random.default_rng(args.seed)
            
            total_attacks = sum(len(s) for s in corpus_dict.values())
            print(f"\n  LLM Mode: {args.model} | {args.sample_size}/{total_attacks} samples/category")
            
            for adapter in adapters:
                arch_name = adapter.profile.name
                print(f"  [{arch_name}] Creating multiagent system...")
                try:
                    llm_system = MultiAgentSystem(
                        adapter=adapter, config=llm_config, seed=args.seed,
                    )
                except Exception as e:
                    print(f"  ERROR creating system for {arch_name}: {e}")
                    print(f"  Skipping {arch_name}, continuing with remaining architectures...")
                    continue

                for cat_key, samples in corpus_dict.items():
                    # Downsample for LLM mode
                    if len(samples) > args.sample_size:
                        indices = rng.choice(len(samples), size=args.sample_size, replace=False)
                        samples_subset = [samples[i] for i in sorted(indices)]
                    else:
                        samples_subset = samples

                    t0 = time.time()
                    try:
                        result = runner.run_single_llm(
                            adapter, samples_subset, pipeline, llm_system,
                        )
                        elapsed = time.time() - t0

                        print(
                            f"    {cat_key}: DR={result.detection_rate:.1%} "
                            f"FPR={result.false_positive_rate:.1%} "
                            f"n={result.n_attacks} ({elapsed:.1f}s)"
                        )
                        results.append(result)
                        
                        # Save incremental results
                        save_results_to_file(results, final=False)
                        
                    except Exception as e:
                        print(f"    ERROR running {arch_name}/{cat_key}: {e}")
                        # Continue to next category instead of crashing
                        continue

        else:
            results = runner.run_full_matrix(adapters, corpus_dict, pipeline)

    finally:
        # Save final results (or partial if crashed)
        if results:
            print(f"\nSaving {len(results)} results...")
            save_results_to_file(results, final=True)

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


if __name__ == "__main__":
    main()




