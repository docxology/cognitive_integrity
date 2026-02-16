"""ROC curve construction, AUC computation, and confidence intervals.

Implements receiver-operating-characteristic analysis without sklearn,
using only numpy for threshold sweeping and trapezoidal AUC integration.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Union

import numpy as np


@dataclass
class ROCCurve:
    """Container for a computed ROC curve.

    Attributes:
        fpr_points: False positive rates at each threshold.
        tpr_points: True positive rates at each threshold.
        thresholds: Threshold values swept (descending).
        auc: Area under the ROC curve.
    """

    fpr_points: np.ndarray
    tpr_points: np.ndarray
    thresholds: np.ndarray
    auc: float


def compute_roc(
    y_true: Union[List[bool], np.ndarray],
    scores: Union[List[float], np.ndarray],
    n_thresholds: int = 200,
) -> ROCCurve:
    """Compute an ROC curve by sweeping thresholds from 0 to 1.

    Args:
        y_true: Ground-truth binary labels (True = positive).
        scores: Continuous scores in [0, 1] (higher = more likely positive).
        n_thresholds: Number of threshold steps to sweep.

    Returns:
        A ``ROCCurve`` with FPR/TPR points and AUC.
    """
    y_true_arr = np.asarray(y_true, dtype=bool)
    scores_arr = np.asarray(scores, dtype=np.float64)

    if len(y_true_arr) != len(scores_arr):
        raise ValueError("y_true and scores must have the same length")

    n_pos = int(y_true_arr.sum())
    n_neg = len(y_true_arr) - n_pos

    # Sweep thresholds from high to low
    thresholds = np.linspace(1.0, 0.0, n_thresholds)
    fpr_list: List[float] = []
    tpr_list: List[float] = []

    for thresh in thresholds:
        predictions = scores_arr >= thresh
        tp = int(np.sum(predictions & y_true_arr))
        fp = int(np.sum(predictions & ~y_true_arr))

        tpr = tp / n_pos if n_pos > 0 else 0.0
        fpr = fp / n_neg if n_neg > 0 else 0.0

        tpr_list.append(tpr)
        fpr_list.append(fpr)

    fpr_points = np.array(fpr_list, dtype=np.float64)
    tpr_points = np.array(tpr_list, dtype=np.float64)

    auc_val = compute_auc_from_points(fpr_points, tpr_points)

    return ROCCurve(
        fpr_points=fpr_points,
        tpr_points=tpr_points,
        thresholds=thresholds,
        auc=auc_val,
    )


def compute_auc(roc: ROCCurve) -> float:
    """Compute AUC from an existing ROC curve using the trapezoidal rule.

    Args:
        roc: A pre-computed ``ROCCurve``.

    Returns:
        Area under the curve (scalar).
    """
    return compute_auc_from_points(roc.fpr_points, roc.tpr_points)


def compute_auc_from_points(fpr: np.ndarray, tpr: np.ndarray) -> float:
    """Trapezoidal AUC from FPR/TPR arrays.

    Sorts by FPR ascending before integrating to handle any ordering.

    Args:
        fpr: Array of false positive rates.
        tpr: Array of true positive rates.

    Returns:
        AUC value in [0, 1].
    """
    # Sort by FPR ascending
    order = np.argsort(fpr)
    fpr_sorted = fpr[order]
    tpr_sorted = tpr[order]

    # Trapezoidal integration
    # np.trapezoid (numpy >=2.0), fallback to np.trapz for older versions
    _trapz = getattr(np, "trapezoid", None) or np.trapz
    auc = float(_trapz(tpr_sorted, fpr_sorted))
    return max(0.0, min(1.0, auc))


def bootstrap_auc_ci(
    y_true: Union[List[bool], np.ndarray],
    scores: Union[List[float], np.ndarray],
    n_bootstrap: int = 1000,
    ci: float = 0.95,
    seed: int = 42,
) -> Tuple[float, float, float]:
    """Bootstrap confidence interval for AUC.

    Resamples with replacement and computes AUC for each bootstrap
    sample, then extracts the percentile-based confidence interval.

    Args:
        y_true: Ground-truth binary labels.
        scores: Continuous prediction scores.
        n_bootstrap: Number of bootstrap resamples.
        ci: Confidence level (default 0.95 for 95% CI).
        seed: Random seed for reproducibility.

    Returns:
        ``(auc_point_estimate, ci_lower, ci_upper)`` tuple.
    """
    y_true_arr = np.asarray(y_true, dtype=bool)
    scores_arr = np.asarray(scores, dtype=np.float64)
    n = len(y_true_arr)

    if n == 0:
        return 0.0, 0.0, 0.0

    rng = np.random.default_rng(seed)

    # Point estimate
    roc = compute_roc(y_true_arr, scores_arr)
    point_auc = roc.auc

    # Bootstrap
    aucs: List[float] = []
    for _ in range(n_bootstrap):
        indices = rng.integers(0, n, size=n)
        boot_true = y_true_arr[indices]
        boot_scores = scores_arr[indices]

        # Skip degenerate samples (all same class)
        if boot_true.sum() == 0 or boot_true.sum() == n:
            continue

        boot_roc = compute_roc(boot_true, boot_scores, n_thresholds=100)
        aucs.append(boot_roc.auc)

    if not aucs:
        return point_auc, point_auc, point_auc

    alpha = 1.0 - ci
    lower = float(np.percentile(aucs, 100.0 * alpha / 2.0))
    upper = float(np.percentile(aucs, 100.0 * (1.0 - alpha / 2.0)))

    return point_auc, lower, upper


def youdens_j(roc: ROCCurve) -> Tuple[float, float]:
    """Find the optimal threshold using Youden's J statistic.

    J = TPR - FPR.  The optimal threshold maximises J.

    Args:
        roc: A pre-computed ``ROCCurve``.

    Returns:
        ``(optimal_threshold, j_statistic)`` tuple.
    """
    j_values = roc.tpr_points - roc.fpr_points
    best_idx = int(np.argmax(j_values))
    return float(roc.thresholds[best_idx]), float(j_values[best_idx])
