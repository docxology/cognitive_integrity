"""Precision-recall curves with bootstrap average-precision confidence intervals.

Computes threshold-swept PR curves and average precision (AP) from binary
labels and continuous scores, with optional bootstrap CIs for the AP.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np


@dataclass
class PRCurve:
    """Precision-recall curve data.

    Attributes:
        precision: Precision values at each threshold.
        recall: Recall values at each threshold.
        thresholds: Score thresholds (length = len(precision) - 1).
        average_precision: Area under the PR curve.
    """

    precision: np.ndarray
    recall: np.ndarray
    thresholds: np.ndarray
    average_precision: float


def compute_pr_curve(
    y_true: np.ndarray,
    scores: np.ndarray,
    n_thresholds: int = 200,
) -> PRCurve:
    """Compute a precision-recall curve from labels and scores.

    Parameters
    ----------
    y_true : ndarray
        Binary labels (1 = positive, 0 = negative).
    scores : ndarray
        Continuous scores in [0, 1].
    n_thresholds : int
        Number of threshold steps.

    Returns
    -------
    PRCurve
    """
    y_true = np.asarray(y_true, dtype=int)
    scores = np.asarray(scores, dtype=float)

    thresholds = np.linspace(0.0, 1.0, n_thresholds)
    precisions = []
    recalls = []

    total_positives = np.sum(y_true == 1)
    if total_positives == 0:
        return PRCurve(
            precision=np.ones(n_thresholds),
            recall=np.zeros(n_thresholds),
            thresholds=thresholds,
            average_precision=0.0,
        )

    for t in thresholds:
        predicted_pos = scores >= t
        tp = np.sum((predicted_pos) & (y_true == 1))
        fp = np.sum((predicted_pos) & (y_true == 0))
        fn = np.sum((~predicted_pos) & (y_true == 1))

        prec = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0

        precisions.append(prec)
        recalls.append(rec)

    precision_arr = np.array(precisions)
    recall_arr = np.array(recalls)

    ap = compute_average_precision_from_arrays(precision_arr, recall_arr)

    return PRCurve(
        precision=precision_arr,
        recall=recall_arr,
        thresholds=thresholds,
        average_precision=ap,
    )


def compute_average_precision_from_arrays(
    precision: np.ndarray,
    recall: np.ndarray,
) -> float:
    """Compute average precision from precision and recall arrays.

    Uses the trapezoidal rule on the monotone-decreasing envelope.
    """
    # Sort by recall (ascending)
    order = np.argsort(recall)
    recall_sorted = recall[order]
    precision_sorted = precision[order]

    # Make precision monotonically decreasing from right
    for i in range(len(precision_sorted) - 2, -1, -1):
        precision_sorted[i] = max(precision_sorted[i], precision_sorted[i + 1])

    # Compute AP as sum of rectangular strips
    ap = 0.0
    for i in range(1, len(recall_sorted)):
        dr = recall_sorted[i] - recall_sorted[i - 1]
        if dr > 0:
            ap += precision_sorted[i] * dr

    return float(ap)


# NOTE (P2-F15): AP is computed on a threshold grid, so the result is
# a bounded-accuracy approximation of the exact AP (can differ slightly
# from a pointwise/rank-based AP for coarse grids).
def compute_average_precision(pr: PRCurve) -> float:
    """Convenience wrapper: return the AP from a PRCurve."""
    return pr.average_precision


def bootstrap_ap_ci(
    y_true: np.ndarray,
    scores: np.ndarray,
    n_bootstrap: int = 1000,
    confidence: float = 0.95,
    seed: int = 42,
) -> Tuple[float, float, float]:
    """Bootstrap confidence interval for average precision.

    Parameters
    ----------
    y_true : ndarray
        Binary ground-truth labels.
    scores : ndarray
        Continuous prediction scores.
    n_bootstrap : int
        Number of bootstrap resamples.
    confidence : float
        Confidence level (e.g. 0.95).
    seed : int
        Random seed.

    Returns
    -------
    ap : float
        Point estimate of average precision.
    ci_lower : float
        Lower bound of the confidence interval.
    ci_upper : float
        Upper bound of the confidence interval.
    """
    rng = np.random.default_rng(seed)
    y_true = np.asarray(y_true, dtype=int)
    scores = np.asarray(scores, dtype=float)
    n = len(y_true)

    ap_point = compute_pr_curve(y_true, scores).average_precision

    ap_samples = []
    for _ in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)
        boot_true = y_true[idx]
        boot_scores = scores[idx]
        if np.sum(boot_true) == 0:
            continue
        pr = compute_pr_curve(boot_true, boot_scores)
        ap_samples.append(pr.average_precision)

    if not ap_samples:
        return ap_point, ap_point, ap_point

    alpha = 1.0 - confidence
    lo = float(np.percentile(ap_samples, 100 * alpha / 2))
    hi = float(np.percentile(ap_samples, 100 * (1 - alpha / 2)))

    return ap_point, lo, hi


__all__ = [
    "PRCurve",
    "compute_pr_curve",
    "compute_average_precision",
    "compute_average_precision_from_arrays",
    "bootstrap_ap_ci",
]
