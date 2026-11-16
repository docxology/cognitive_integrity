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
import hashlib
import json
import logging
import os
import sys
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np

from src.architectures.autogpt import AutoGPTAdapter
from src.architectures.claude_code import ClaudeCodeAdapter
from src.architectures.crewai import CrewAIAdapter
from src.architectures.langgraph import LangGraphAdapter
from src.attacks.corpus import AttackCorpus
from src.data.generate import SIDECAR_HASH_KEY
from src.evaluation.llm_evaluator import LLMEvaluationError, run_llm_evaluation
from src.evaluation.runner import ExperimentRunner
from src.utils.random_seed import set_global_seed
from src.utils.types import ExperimentConfig

logger = logging.getLogger(__name__)


def get_all_adapters():
    """Return instances of all 4 architecture adapters."""
    return [ClaudeCodeAdapter(), AutoGPTAdapter(), CrewAIAdapter(), LangGraphAdapter()]


def _create_pipeline(mode: str):
    """Create the CIF defense pipeline (or None for simulation mode)."""
    if mode == "simulation":
        return None
    from src.composition.factory import create_full_pipeline
    return create_full_pipeline()


def main() -> int:
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

    attempt_id = None
    if args.mode == "llm":
        attempt_id = uuid.uuid4().hex
        previous_diagnostics = [
            path
            for kind in ("partial", "failed")
            if (path := output_dir / f"full_evaluation_results_llm_{kind}.json").exists()
        ]
        if previous_diagnostics:
            # Preserve even legacy diagnostics with missing or mismatched IDs.
            # The directory names the fresh attempt that displaced this snapshot.
            archive_dir = output_dir / "llm_attempts" / f"before-{attempt_id}"
            archive_dir.mkdir(parents=True)
            for diagnostic in previous_diagnostics:
                diagnostic.rename(archive_dir / diagnostic.name)

    print("=" * 70)
    print(f"CIF Full Evaluation — Mode: {args.mode.upper()}")
    print("=" * 70)

    # Generate attack corpus
    print("\n[1/3] Generating 950-attack corpus...")
    corpus = AttackCorpus.generate(seed=args.seed, extended=False)
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

    # Save helper (P2-5/P2-9): atomic write, honest measurement_mode,
    # null FPR on the 0/0 operating point, provenance sidecar, and a
    # content-hashed .real_data_marker so a stale or hand-edited results
    # file can be detected.
    def save_results_to_file(results_list, final=False, failure=None):
        if not results_list and failure is None:
            return
        results_data = [
            {
                "architecture": r.architecture,
                "category": r.category,
                "attack_category": r.attack_category,
                "n_attacks": r.n_attacks, "true_positives": r.true_positives,
                "false_positives": r.false_positives, "true_negatives": r.true_negatives,
                "false_negatives": r.false_negatives, "detection_rate": r.detection_rate,
                # FPR is structurally undefined when no benign samples ran
                # (tn == fp == 0); publish null rather than a fake 0.0 rate.
                "false_positive_rate": (
                    None
                    if (r.false_positives == 0 and r.true_negatives == 0)
                    else r.false_positive_rate
                ),
                # Wall-clock timing is not part of the reproducible result
                # artifact; retain it on ExperimentResult for runtime use.
                "mode": r.measurement_mode,
                # Honest provenance: what actually produced these numbers.
                "measurement_mode": r.measurement_mode,
                "llm_fallback_count": r.llm_fallback_count,
            }
            for r in results_list
        ]
        suffix = f"_{args.mode}" if args.mode != "simulation" else ""
        if failure is not None:
            suffix += "_failed"
        elif not final:
            suffix += "_partial"
        out_path = output_dir / f"full_evaluation_results{suffix}.json"

        payload_data: list[dict[str, object]] | dict[str, object] = results_data
        if args.mode == "llm" and not final:
            payload_data = {
                "status": "failed" if failure is not None else "partial",
                "attempt_id": attempt_id,
                "mode": "llm",
                "model": args.model,
                "seed": args.seed,
                "expected_cells": len(adapters) * len(corpus_dict),
                "completed_cells": (
                    sum(cell["status"] == "complete" for cell in failure.outcomes)
                    if failure is not None else len(results_list)
                ),
                "results": results_data,
            }
            if failure is not None:
                payload_data["reason"] = str(failure)
                payload_data["outcomes"] = failure.outcomes
        payload = json.dumps(payload_data, indent=2)
        # Atomic write: temp file in the same directory, then rename.
        fd, tmp = tempfile.mkstemp(dir=str(output_dir), suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as f:
                f.write(payload)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, out_path)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
        if failure is not None:
            logger.error("Failed LLM diagnostics saved to %s", out_path)

        if final:
            print(f"\nResults saved to {out_path}")
            partial = output_dir / f"full_evaluation_results_{args.mode}_partial.json"
            if partial.exists():
                partial.unlink()
            import datetime as _dt
            data_hash = hashlib.sha256(payload.encode()).hexdigest()
            marker = output_dir / ".real_data_marker"
            marker.write_text(
                f"mode={args.mode} seed={args.seed} "
                f"generated={_dt.datetime.now().isoformat()} "
                f"sha256={data_hash}\n"
            )
            prov = {
                "data_origin": (
                    "parametric_simulation"
                    if args.mode == "simulation"
                    else sorted({r.measurement_mode for r in results_list})
                ),
                "source_script": "scripts/run_full_evaluation.py",
                "seed": args.seed,
                "mode": args.mode,
                "note": (
                    "Parametric ceiling / simulation origin: these rows model "
                    "CIF behaviour with calibrated base rates; they are NOT "
                    "empirically measured pipeline evidence (P2-5)."
                    if args.mode == "simulation"
                    else (
                        "Complete LLM multiagent evaluation over the sampled attack corpus."
                        if args.mode == "llm"
                        else "Pipeline-mode rows over the attack corpus."
                    )
                ),
                "rows": len(results_data),
                # The reader binds a sidecar to its artifact through
                # ``SIDECAR_HASH_KEY``, and this line wrote the hash under the
                # literal "sha256" instead -- while importing the constant it
                # was supposed to use. The binding was therefore absent, the
                # reader fell through to its unbound branch, and because that
                # branch trusts only a "real_pipeline" claim, this parametric
                # artifact classified as `unknown` for as long as the sidecar
                # existed. The hash was correct the whole time; nothing could
                # find it.
                SIDECAR_HASH_KEY: data_hash,
            }
            (output_dir / f"full_evaluation_results{suffix}.provenance.json").write_text(
                json.dumps(prov, indent=2)
            )

    try:
        config = ExperimentConfig(seed=args.seed)
        runner = ExperimentRunner(config)
        pipeline = _create_pipeline(args.mode)
    except Exception as e:
        if args.mode != "llm":
            raise
        message = f"Could not set up LLM evaluation: {type(e).__name__}: {e}"
        failure = LLMEvaluationError(
            message, [],
            [
                {
                    "architecture": adapter.profile.name,
                    "category": category,
                    "expected_samples": min(len(samples), max(0, args.sample_size)),
                    "status": "not_run",
                    "error": message,
                }
                for adapter in adapters
                for category, samples in corpus_dict.items()
            ],
        )
        save_results_to_file([], failure=failure)
        logger.error("%s", failure)
        return 1

    if args.mode == "llm":
        try:
            results = run_llm_evaluation(
                adapters, corpus_dict, pipeline, runner,
                model=args.model, sample_size=args.sample_size,
                seed=args.seed, save_callback=save_results_to_file,
            )
        except LLMEvaluationError as e:
            save_results_to_file(e.results, failure=e)
            logger.error("%s", e)
            return 1
    else:
        results = runner.run_full_matrix(adapters, corpus_dict, pipeline)

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


    return 0


if __name__ == "__main__":
    sys.exit(main())
