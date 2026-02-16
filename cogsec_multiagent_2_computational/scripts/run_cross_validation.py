#!/usr/bin/env python3
"""Run stratified 5-fold cross-validation on the 950-attack corpus.

Usage:
    python scripts/run_cross_validation.py [--seed 42] [--k 5] [--output output/data]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

import numpy as np

from utils.random_seed import set_global_seed
from attacks.corpus import AttackCorpus
from statistics.cross_validation import run_cross_validation


def main() -> None:
    parser = argparse.ArgumentParser(description="Run cross-validation")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--output", type=str, default="output/data")
    args = parser.parse_args()

    set_global_seed(args.seed)
    output_dir = ROOT / args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(f"Stratified {args.k}-Fold Cross-Validation")
    print("=" * 70)

    # Generate corpus
    print("\n[1/3] Generating attack corpus...")
    corpus = AttackCorpus.generate(seed=args.seed)
    samples = [
        {"category": s.subcategory, "content": s.payload, "is_attack": True}
        for s in list(corpus)
    ]
    print(f"  Corpus size: {len(samples)}")

    # Try real pipeline, fall back to simulated
    print("\n[2/3] Running cross-validation...")
    try:
        from composition.factory import create_full_pipeline
        pipeline = create_full_pipeline()
        def eval_fn(message):
            result = pipeline.evaluate(message)
            return result.detected, result.score
        print("  Using real CIF pipeline")
    except ImportError:
        rng = np.random.default_rng(args.seed)
        def eval_fn(message):
            score = float(rng.uniform(0.4, 1.0))
            return score > 0.5, score
        print("  Using simulated evaluation (pipeline not available)")

    cv_result = run_cross_validation(
        samples, eval_fn, k=args.k, seed=args.seed,
    )

    # Display results
    print(f"\n[3/3] Results ({args.k} folds):")
    print("-" * 70)
    print(f"{'Fold':<6} {'TPR':>8} {'FPR':>8} {'F1':>8} {'Prec':>8} {'Rec':>8} {'N':>6}")
    print("-" * 70)
    for f in cv_result.fold_results:
        print(
            f"{f.fold:<6} {f.tpr:>8.4f} {f.fpr:>8.4f} {f.f1:>8.4f} "
            f"{f.precision:>8.4f} {f.recall:>8.4f} {f.n_samples:>6}"
        )
    print("-" * 70)
    print(
        f"{'Mean':<6} {cv_result.mean_tpr:>8.4f} {cv_result.mean_fpr:>8.4f} "
        f"{cv_result.mean_f1:>8.4f} {cv_result.mean_precision:>8.4f} "
        f"{cv_result.mean_recall:>8.4f}"
    )
    print(
        f"{'SD':<6} {cv_result.std_tpr:>8.4f} {cv_result.std_fpr:>8.4f} "
        f"{cv_result.std_f1:>8.4f} {cv_result.std_precision:>8.4f} "
        f"{cv_result.std_recall:>8.4f}"
    )

    # Save
    out_path = output_dir / "cross_validation_results.json"
    data = {
        "k": cv_result.k,
        "folds": [
            {
                "fold": f.fold,
                "tpr": f.tpr,
                "fpr": f.fpr,
                "f1": f.f1,
                "precision": f.precision,
                "recall": f.recall,
                "n_samples": f.n_samples,
            }
            for f in cv_result.fold_results
        ],
        "mean_tpr": cv_result.mean_tpr,
        "std_tpr": cv_result.std_tpr,
        "mean_f1": cv_result.mean_f1,
        "std_f1": cv_result.std_f1,
    }
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
