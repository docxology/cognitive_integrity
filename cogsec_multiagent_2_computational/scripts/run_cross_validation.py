#!/usr/bin/env python3
"""Run stratified 5-fold cross-validation on the 950-attack corpus.

Thin orchestrator — cross-validation logic lives in src/statistics/cross_validation.py,
benign messages in src/ablation/runner.py.

Usage:
    python scripts/run_cross_validation.py [--seed 42] [--k 5] [--output output/data]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from statistics.cross_validation import run_cross_validation

import numpy as np

from ablation.runner import BENIGN_MESSAGES
from attacks.corpus import AttackCorpus
from composition.factory import create_full_pipeline
from utils.random_seed import set_global_seed


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

    # Build corpus
    print("\n[1/3] Generating attack corpus...")
    corpus = AttackCorpus.generate(seed=args.seed)
    samples = [
        {"category": s.subcategory, "content": s.payload, "is_attack": True}
        for s in list(corpus)
    ]

    # Add benign samples
    rng_sampling = np.random.default_rng(args.seed)
    benign_categories = ["benign_general", "benign_technical", "benign_academic"]
    for msg in BENIGN_MESSAGES:
        cat = rng_sampling.choice(benign_categories)
        samples.append({"category": cat, "content": msg, "is_attack": False})

    rng_sampling.shuffle(samples)
    n_attack = sum(1 for s in samples if s["is_attack"])
    n_benign = len(samples) - n_attack
    print(f"  Corpus size: {len(samples)} ({n_attack} attacks + {n_benign} benign)")

    # Pipeline eval_fn
    print("\n[2/3] Running cross-validation...")
    pipeline = create_full_pipeline()

    def eval_fn(message):
        result = pipeline.evaluate(message)
        return result.detected, result.score

    print("  Using real CIF pipeline")

    cv_result = run_cross_validation(samples, eval_fn, k=args.k, seed=args.seed)

    # Display results
    print(f"\n[3/3] Results ({args.k} folds):")
    print("-" * 70)
    print(f"{'Fold':<6} {'TPR':>8} {'FPR':>8} {'F1':>8} {'Prec':>8} {'Rec':>8} {'N':>6}")
    print("-" * 70)
    for f in cv_result.fold_results:
        print(f"{f.fold:<6} {f.tpr:>8.4f} {f.fpr:>8.4f} {f.f1:>8.4f} "
              f"{f.precision:>8.4f} {f.recall:>8.4f} {f.n_samples:>6}")
    print("-" * 70)
    print(f"{'Mean':<6} {cv_result.mean_tpr:>8.4f} {cv_result.mean_fpr:>8.4f} "
          f"{cv_result.mean_f1:>8.4f} {cv_result.mean_precision:>8.4f} {cv_result.mean_recall:>8.4f}")  # noqa: E501

    # Save
    out_path = output_dir / "cross_validation_results.json"
    data = {
        "data_origin": "real_pipeline",
        "source_script": "scripts/run_cross_validation.py",
        "k": cv_result.k,
        "folds": [
            {"fold": f.fold, "tpr": f.tpr, "fpr": f.fpr, "f1": f.f1,
             "precision": f.precision, "recall": f.recall, "n_samples": f.n_samples}
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
