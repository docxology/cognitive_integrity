#!/usr/bin/env python3
"""Compare the full CIF pipeline against baseline detectors and a chance null.

Thin orchestrator — all logic lives in ``src/evaluation/baselines.py``.

Every detector, CIF included, is measured by the same code on the same
payloads: the 98-sample stratified attack draw plus the 50 benign control
messages that the published ablation uses.  The trained comparator
(bag-of-words logistic regression) is scored strictly out of fold, so no
detector is ever evaluated on rows it was fitted on.

The output artifact ``output/data/baseline_comparison.json`` carries the
per-payload scores as well as the summary metrics, so the ROC and PR figures
plot measured curves with measured bootstrap bands instead of drawing shapes
from a random number generator.

Usage:
    python scripts/run_baseline_comparison.py [--seed 42] [--output output/data]
                                              [--bootstrap 1000] [--folds 5]
                                              [--permutations 10000]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import numpy as np

from evaluation.baselines import (
    DEFAULT_KEYWORD_PATTERNS,
    BagOfWordsDetector,
    CIFPipelineDetector,
    Detector,
    DetectorOutput,
    KeywordDetector,
    LengthDetector,
    RandomDetector,
    build_evaluation_corpus,
    compare_detectors,
    curve_summary,
    evaluate_output,
    out_of_fold_output,
    permutation_null_from_output,
    run_detector,
)

ARTIFACT_NAME = "baseline_comparison.json"

#: Stated plainly in the artifact so no downstream reader can quote the
#: comparison without the limits that bound its interpretation.
CAVEATS: tuple[str, ...] = (
    "The attack corpus is template-generated, so lexical baselines are partly "
    "matched to the generators. This cuts both ways: either the corpus is too "
    "lexically stereotyped to support a claim about semantic defenses, or the "
    "CIF pipeline underperforms trivial detectors on it. Both readings are "
    "adverse to a bare 'the layered architecture is validated' claim.",
    "Attack payloads are systematically longer than the benign controls, so "
    "the length-only detector is measuring a corpus construction artifact, not "
    "an attack property. It is included precisely to expose that confound.",
    "The benign control set is 50 messages, so every false-positive rate here "
    "has a Wilson 95% upper bound near 7% even when zero false positives are "
    "observed. No claim of a low FPR is supportable at this sample size.",
    "Baselines were written from public prompt-injection patterns before being "
    "run against this corpus and were not revised afterwards in either "
    "direction. A comparator tuned down would be as much an overclaim as a "
    "fabricated result.",
    "The CIF detector's detect() is the pipeline's own verdict, which is not "
    "identical to thresholding its fused score at 0.5; the number of "
    "disagreements is recorded per detector as verdict_score_disagreements.",
)


def _detector_specs(flag_rate: float, seed: int) -> list[tuple[Detector, str, str]]:
    """Return ``(detector, kind, description)`` for every untrained detector."""
    return [
        (
            CIFPipelineDetector(mode="series"),
            "cif",
            "Full 8-module CIF series pipeline (the published configuration).",
        ),
        (
            KeywordDetector(),
            "baseline",
            f"Case-insensitive regex over {len(DEFAULT_KEYWORD_PATTERNS)} frozen "
            "prompt-injection phrases.",
        ),
        (
            LengthDetector(),
            "baseline",
            "Non-semantic floor: flag any payload of at least 120 characters.",
        ),
        (
            RandomDetector(flag_rate=flag_rate, seed=seed),
            "null",
            "Chance-level null flagging at the CIF pipeline's empirical flag "
            f"rate ({flag_rate:.6f}), blind to the payload.",
        ),
    ]


def build_report(
    seed: int = 42,
    n_folds: int = 5,
    n_bootstrap: int = 1000,
    n_thresholds: int = 200,
    n_permutations: int = 10_000,
) -> dict[str, Any]:
    """Run every detector over the shared corpus and assemble the report."""
    corpus = build_evaluation_corpus(seed=seed)
    labels = corpus.label_array

    # The null must be matched to CIF's own flag rate, so CIF is measured first.
    cif = CIFPipelineDetector(mode="series")
    cif_output = run_detector(cif, corpus)
    cif_metrics = evaluate_output(cif_output, corpus)

    outputs: dict[str, DetectorOutput] = {}
    entries: list[dict[str, Any]] = []
    nulls: dict[str, Any] = {}

    for detector, kind, description in _detector_specs(cif_metrics.flag_rate, seed):
        output = cif_output if detector.name == cif_output.name else run_detector(detector, corpus)
        outputs[output.name] = output
        nulls[output.name] = permutation_null_from_output(
            output, corpus, n_permutations=n_permutations, seed=seed
        ).to_dict()
        entries.append({"name": output.name, "kind": kind, "description": description})

    # Trained comparator: out-of-fold only.
    bow_output = out_of_fold_output(
        BagOfWordsDetector, corpus, n_folds=n_folds, seed=seed
    )
    outputs[bow_output.name] = bow_output
    nulls[bow_output.name] = permutation_null_from_output(
        bow_output, corpus, n_permutations=n_permutations, seed=seed
    ).to_dict()
    entries.append(
        {
            "name": bow_output.name,
            "kind": "baseline",
            "description": (
                f"TF-IDF + L2-regularised logistic regression, {n_folds}-fold "
                "out-of-fold predictions (numpy/scipy only)."
            ),
        }
    )

    rows = compare_detectors(outputs, corpus, trained_names=[bow_output.name])
    by_name = {row.metrics.name: row for row in rows}

    detectors: list[dict[str, Any]] = []
    for entry in entries:
        name = str(entry["name"])
        row = by_name[name]
        output = outputs[name]
        summary = curve_summary(
            name,
            labels,
            output.scores,
            n_thresholds=n_thresholds,
            n_bootstrap=n_bootstrap,
            seed=seed,
        )
        detectors.append(
            {
                **entry,
                "trained": row.trained,
                "metrics": row.metrics.to_dict(),
                "curves": summary.to_dict(),
                "permutation_null": nulls.get(name),
                "scores": [round(float(v), 6) for v in output.scores],
                "detections": [bool(v) for v in output.detections],
            }
        )

    # Per-attack-family ROC for the CIF pipeline, each family scored against
    # the shared benign controls.  This is what the manuscript's ROC caption
    # claims to show; until now no such measurement existed.
    tops = np.asarray(corpus.top_categories)
    per_category: dict[str, Any] = {}
    for category in sorted(set(tops.tolist()) - {"benign"}):
        mask = (tops == category) | (tops == "benign")
        per_category[category] = curve_summary(
            category,
            labels[mask],
            cif_output.scores[mask],
            n_thresholds=n_thresholds,
            n_bootstrap=n_bootstrap,
            seed=seed,
        ).to_dict()

    ranking = [row.metrics.name for row in rows]
    best_non_cif = next(r for r in rows if r.metrics.name != cif_output.name)

    return {
        "data_origin": "real_pipeline",
        "source_script": "scripts/run_baseline_comparison.py",
        "generated_by": "evaluation.baselines",
        "seed": seed,
        "config": {
            "n_folds": n_folds,
            "n_bootstrap": n_bootstrap,
            "n_thresholds": n_thresholds,
            "n_permutations": n_permutations,
            "keyword_patterns": list(DEFAULT_KEYWORD_PATTERNS),
        },
        "corpus": {
            "n_total": len(corpus),
            "n_attacks": corpus.n_positive,
            "n_benign": corpus.n_negative,
            "construction": (
                "Stratified attack sample (proportional over 12 subcategories, "
                "target 100 -> 98 after rounding) from AttackCorpus.generate(seed), "
                "plus ablation.runner.BENIGN_MESSAGES."
            ),
            "labels": [bool(v) for v in labels],
            "groups": list(corpus.groups),
            "top_categories": list(corpus.top_categories),
        },
        "detectors": detectors,
        "cif_by_attack_category": per_category,
        "ranking_by_youden_j": ranking,
        "headline": {
            "cif_tpr": cif_metrics.tpr,
            "cif_fpr": cif_metrics.fpr,
            "cif_youden_j": cif_metrics.youden_j,
            "best_detector": ranking[0],
            "best_non_cif_detector": best_non_cif.metrics.name,
            "best_non_cif_youden_j": best_non_cif.metrics.youden_j,
            "cif_beats_best_baseline": bool(
                cif_metrics.youden_j > best_non_cif.metrics.youden_j
            ),
            "cif_rank": ranking.index(cif_output.name) + 1,
            "n_detectors": len(ranking),
        },
        "caveats": list(CAVEATS),
    }


def main(argv: list[str] | None = None) -> int:
    """Run the comparison and write the artifact; return a process exit code."""
    parser = argparse.ArgumentParser(
        description="Compare CIF against baseline detectors and a chance null"
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=str, default="output/data")
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--thresholds", type=int, default=200)
    parser.add_argument("--permutations", type=int, default=10_000)
    args = parser.parse_args(argv)

    output_dir = Path(args.output)
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("Baseline Comparison — CIF vs non-CIF detectors and a chance null")
    print("=" * 70)

    report = build_report(
        seed=args.seed,
        n_folds=args.folds,
        n_bootstrap=args.bootstrap,
        n_thresholds=args.thresholds,
        n_permutations=args.permutations,
    )

    header = (
        f"{'detector':<24}{'TPR':>8}{'FPR':>8}{'J':>9}{'AUC':>8}"
        f"{'AUC 95% CI':>18}{'perm p':>10}"
    )
    print()
    print(header)
    print("-" * len(header))
    for name in report["ranking_by_youden_j"]:
        entry = next(d for d in report["detectors"] if d["name"] == name)
        m = entry["metrics"]
        c = entry["curves"]
        null = entry["permutation_null"]
        ci = f"[{c['auc_ci95'][0]:.3f}, {c['auc_ci95'][1]:.3f}]"
        print(
            f"{name:<24}{m['tpr']:>8.4f}{m['fpr']:>8.4f}{m['youden_j']:>9.4f}"
            f"{c['auc']:>8.4f}{ci:>18}{null['p_value']:>10.4f}"
        )

    head = report["headline"]
    print()
    print(
        f"CIF ranks {head['cif_rank']} of {head['n_detectors']} by Youden's J. "
        f"Strongest non-CIF detector: {head['best_non_cif_detector']} "
        f"(J={head['best_non_cif_youden_j']:.4f} vs CIF J={head['cif_youden_j']:.4f})."
    )
    if not head["cif_beats_best_baseline"]:
        print(
            "RESULT: the layered CIF pipeline does NOT beat the strongest "
            "non-CIF baseline on this corpus."
        )

    out_path = output_dir / ARTIFACT_NAME
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\nResults saved to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
