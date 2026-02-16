"""Stratified k-fold cross-validation for the CIF defense pipeline.

Splits a labeled corpus into stratified folds, evaluates a pipeline on
each fold, and reports per-fold and aggregate metrics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Tuple

import numpy as np


@dataclass
class FoldResult:
    """Metrics for a single cross-validation fold.

    Attributes:
        fold: Fold index (0-based).
        tpr: True positive rate (sensitivity / recall).
        fpr: False positive rate.
        f1: F1 score.
        precision: Precision.
        recall: Recall (same as tpr, included for clarity).
        n_samples: Number of samples in this fold.
    """

    fold: int
    tpr: float
    fpr: float
    f1: float
    precision: float
    recall: float
    n_samples: int


@dataclass
class CrossValidationResult:
    """Aggregated k-fold cross-validation result.

    Attributes:
        k: Number of folds.
        fold_results: Per-fold metrics.
        mean_tpr: Mean true positive rate across folds.
        std_tpr: Standard deviation of TPR.
        mean_fpr: Mean false positive rate.
        std_fpr: Standard deviation of FPR.
        mean_f1: Mean F1 score.
        std_f1: Standard deviation of F1.
        mean_precision: Mean precision.
        std_precision: Standard deviation of precision.
        mean_recall: Mean recall.
        std_recall: Standard deviation of recall.
    """

    k: int
    fold_results: List[FoldResult]
    mean_tpr: float
    std_tpr: float
    mean_fpr: float
    std_fpr: float
    mean_f1: float
    std_f1: float
    mean_precision: float
    std_precision: float
    mean_recall: float
    std_recall: float


def stratified_corpus_folds(
    samples: List[Dict[str, Any]],
    k: int = 5,
    seed: int = 42,
) -> List[Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]]:
    """Split *samples* into *k* stratified train/test folds.

    Stratification is by the ``"category"`` key in each sample dict.

    Parameters
    ----------
    samples : list of dict
        Each dict must have ``"category"`` (str) and ``"is_attack"`` (bool).
    k : int
        Number of folds.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    list of (train, test) tuples
    """
    rng = np.random.default_rng(seed)

    # Group by category
    by_cat: Dict[str, List[int]] = {}
    for i, s in enumerate(samples):
        cat = s.get("category", "unknown")
        by_cat.setdefault(cat, []).append(i)

    # Shuffle within each category and assign to folds
    fold_indices: List[List[int]] = [[] for _ in range(k)]
    for cat, indices in by_cat.items():
        arr = np.array(indices)
        rng.shuffle(arr)
        for i, idx in enumerate(arr):
            fold_indices[i % k].append(int(idx))

    # Build train/test splits
    folds = []
    for test_fold in range(k):
        test_idx = set(fold_indices[test_fold])
        train = [samples[i] for i in range(len(samples)) if i not in test_idx]
        test = [samples[i] for i in fold_indices[test_fold]]
        folds.append((train, test))

    return folds


def _compute_fold_metrics(
    predictions: List[Tuple[bool, bool]],
) -> Tuple[float, float, float, float, float]:
    """Compute TPR, FPR, F1, precision, recall from (is_attack, detected) pairs."""
    tp = fp = tn = fn = 0
    for is_attack, detected in predictions:
        if is_attack:
            if detected:
                tp += 1
            else:
                fn += 1
        else:
            if detected:
                fp += 1
            else:
                tn += 1

    tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tpr
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    return tpr, fpr, f1, precision, recall


def run_cross_validation(
    samples: List[Dict[str, Any]],
    eval_fn: Callable[[str], Tuple[bool, float]],
    k: int = 5,
    seed: int = 42,
) -> CrossValidationResult:
    """Run stratified k-fold cross-validation.

    Parameters
    ----------
    samples : list of dict
        Must have ``"content"`` (str), ``"is_attack"`` (bool), ``"category"`` (str).
    eval_fn : callable
        ``(message) -> (detected: bool, score: float)``.
    k : int
        Number of folds.
    seed : int
        Random seed.

    Returns
    -------
    CrossValidationResult
    """
    folds = stratified_corpus_folds(samples, k=k, seed=seed)
    fold_results: List[FoldResult] = []

    for fold_idx, (_train, test) in enumerate(folds):
        predictions = []
        for sample in test:
            content = sample.get("content", "")
            is_attack = sample.get("is_attack", True)
            detected, _score = eval_fn(content)
            predictions.append((is_attack, detected))

        tpr, fpr, f1, prec, rec = _compute_fold_metrics(predictions)
        fold_results.append(FoldResult(
            fold=fold_idx,
            tpr=tpr,
            fpr=fpr,
            f1=f1,
            precision=prec,
            recall=rec,
            n_samples=len(test),
        ))

    tprs = [f.tpr for f in fold_results]
    fprs = [f.fpr for f in fold_results]
    f1s = [f.f1 for f in fold_results]
    precs = [f.precision for f in fold_results]
    recs = [f.recall for f in fold_results]

    return CrossValidationResult(
        k=k,
        fold_results=fold_results,
        mean_tpr=float(np.mean(tprs)),
        std_tpr=float(np.std(tprs)),
        mean_fpr=float(np.mean(fprs)),
        std_fpr=float(np.std(fprs)),
        mean_f1=float(np.mean(f1s)),
        std_f1=float(np.std(f1s)),
        mean_precision=float(np.mean(precs)),
        std_precision=float(np.std(precs)),
        mean_recall=float(np.mean(recs)),
        std_recall=float(np.std(recs)),
    )


__all__ = [
    "FoldResult",
    "CrossValidationResult",
    "stratified_corpus_folds",
    "run_cross_validation",
]
