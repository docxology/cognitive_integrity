"""Parameter sensitivity analysis: sweeps and cross-validation.

Provides utilities for systematic parameter exploration, including
one-dimensional sweeps, two-dimensional grid search, and k-fold /
leave-one-out cross-validation -- all without sklearn.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class SensitivityResult:
    """Result of sweeping a single parameter.

    Attributes:
        parameter_name: Name of the parameter that was varied.
        values: Array of parameter values tested.
        metric_values: Corresponding metric at each parameter value.
        best_value: Parameter value that achieved the best metric.
        best_metric: Best (highest) metric observed.
    """

    parameter_name: str
    values: np.ndarray
    metric_values: np.ndarray
    best_value: float
    best_metric: float


# ---------------------------------------------------------------------------
# Single-parameter sweep
# ---------------------------------------------------------------------------

def parameter_sweep(
    param_name: str,
    param_range: np.ndarray,
    evaluate_fn: Callable[[float], float],
) -> SensitivityResult:
    """Sweep a single parameter across a range and record the metric.

    Args:
        param_name: Name of the parameter being swept.
        param_range: Array of values to evaluate.
        evaluate_fn: Callable that takes a parameter value and returns a
            scalar metric (higher is better).

    Returns:
        :class:`SensitivityResult` with the full sweep and best setting.
    """
    param_range = np.asarray(param_range, dtype=np.float64)
    metric_values = np.array(
        [evaluate_fn(float(v)) for v in param_range], dtype=np.float64
    )

    best_idx = int(np.argmax(metric_values))

    return SensitivityResult(
        parameter_name=param_name,
        values=param_range,
        metric_values=metric_values,
        best_value=float(param_range[best_idx]),
        best_metric=float(metric_values[best_idx]),
    )


# ---------------------------------------------------------------------------
# 2-D grid search
# ---------------------------------------------------------------------------

def grid_search_2d(
    param1_name: str,
    param1_range: np.ndarray,
    param2_name: str,
    param2_range: np.ndarray,
    evaluate_fn: Callable[[float, float], float],
) -> Dict:
    """2-D parameter interaction grid search.

    Evaluates every combination of *param1_range* x *param2_range* and
    returns a dictionary containing the full grid and the best point.

    Args:
        param1_name: Name of the first parameter.
        param1_range: Values for parameter 1.
        param2_name: Name of the second parameter.
        param2_range: Values for parameter 2.
        evaluate_fn: Callable ``(p1, p2) -> metric``.

    Returns:
        Dictionary with keys:
        - ``'grid'``: ``{(p1, p2): metric}``
        - ``'best_params'``: ``{param1_name: val, param2_name: val}``
        - ``'best_metric'``: float
        - ``'param1_name'``, ``'param2_name'``: parameter names
    """
    p1_range = np.asarray(param1_range, dtype=np.float64)
    p2_range = np.asarray(param2_range, dtype=np.float64)

    grid: Dict[Tuple[float, float], float] = {}
    best_metric = -np.inf
    best_p1 = float(p1_range[0])
    best_p2 = float(p2_range[0])

    for p1 in p1_range:
        for p2 in p2_range:
            metric = evaluate_fn(float(p1), float(p2))
            grid[(float(p1), float(p2))] = metric
            if metric > best_metric:
                best_metric = metric
                best_p1 = float(p1)
                best_p2 = float(p2)

    return {
        "grid": grid,
        "best_params": {param1_name: best_p1, param2_name: best_p2},
        "best_metric": best_metric,
        "param1_name": param1_name,
        "param2_name": param2_name,
    }


# ---------------------------------------------------------------------------
# K-fold cross-validation
# ---------------------------------------------------------------------------

def k_fold_cross_validation(
    data: np.ndarray,
    labels: np.ndarray,
    k: int = 5,
    evaluate_fn: Optional[Callable[[np.ndarray, np.ndarray, np.ndarray, np.ndarray], float]] = None,
    seed: int = 42,
) -> List[float]:
    """Stratified k-fold cross-validation.

    Splits *data* into *k* stratified folds (preserving label proportions),
    trains on k-1 folds, and evaluates on the held-out fold.

    Args:
        data: Feature array of shape ``(n_samples, ...)``.
        labels: Binary label array of shape ``(n_samples,)``.
        k: Number of folds.
        evaluate_fn: Callable ``(train_data, train_labels, test_data,
            test_labels) -> float``.  If ``None``, returns accuracy
            computed as the proportion of majority-class labels in the
            test fold (naive baseline).
        seed: RNG seed for fold assignment.

    Returns:
        List of per-fold metric values.

    Raises:
        ValueError: If k < 2 or k > n_samples.
    """
    data = np.asarray(data)
    labels = np.asarray(labels)
    n = len(data)

    if k < 2:
        raise ValueError("k must be >= 2")
    if k > n:
        raise ValueError(f"k ({k}) exceeds number of samples ({n})")

    rng = np.random.default_rng(seed)

    # Stratified fold assignment
    unique_labels = np.unique(labels)
    fold_indices: List[List[int]] = [[] for _ in range(k)]

    for label in unique_labels:
        label_idx = np.where(labels == label)[0]
        rng.shuffle(label_idx)
        # Round-robin assign to folds
        for i, idx in enumerate(label_idx):
            fold_indices[i % k].append(int(idx))

    # Shuffle within each fold for good measure
    for fold in fold_indices:
        rng.shuffle(fold)

    # Default evaluator: majority-class accuracy
    if evaluate_fn is None:
        def _default_eval(
            train_d: np.ndarray,
            train_l: np.ndarray,
            test_d: np.ndarray,
            test_l: np.ndarray,
        ) -> float:
            # Predict the most common training label
            unique, counts = np.unique(train_l, return_counts=True)
            majority = unique[np.argmax(counts)]
            return float(np.mean(test_l == majority))

        evaluate_fn = _default_eval

    fold_metrics: List[float] = []
    for fold_idx in range(k):
        test_indices = np.array(fold_indices[fold_idx])
        train_indices = np.concatenate(
            [np.array(fold_indices[j]) for j in range(k) if j != fold_idx]
        ).astype(int)

        train_data = data[train_indices]
        train_labels = labels[train_indices]
        test_data = data[test_indices]
        test_labels = labels[test_indices]

        metric = evaluate_fn(train_data, train_labels, test_data, test_labels)
        fold_metrics.append(float(metric))

    return fold_metrics


# ---------------------------------------------------------------------------
# Leave-one-out cross-validation
# ---------------------------------------------------------------------------

def leave_one_out(
    data: np.ndarray,
    labels: np.ndarray,
    evaluate_fn: Callable[[np.ndarray, np.ndarray, np.ndarray, np.ndarray], float],
) -> List[float]:
    """Leave-one-out cross-validation.

    Each sample is used once as the test set while all remaining samples
    form the training set.  Equivalent to k-fold with k = n.

    Args:
        data: Feature array of shape ``(n_samples, ...)``.
        labels: Label array of shape ``(n_samples,)``.
        evaluate_fn: Callable ``(train_data, train_labels, test_data,
            test_labels) -> float``.

    Returns:
        List of per-sample metric values (length = n_samples).
    """
    data = np.asarray(data)
    labels = np.asarray(labels)
    n = len(data)

    metrics: List[float] = []
    all_indices = np.arange(n)

    for i in range(n):
        train_mask = all_indices != i
        train_data = data[train_mask]
        train_labels = labels[train_mask]
        test_data = data[i : i + 1]
        test_labels = labels[i : i + 1]

        metric = evaluate_fn(train_data, train_labels, test_data, test_labels)
        metrics.append(float(metric))

    return metrics


# ---------------------------------------------------------------------------
# Sensitivity ranking
# ---------------------------------------------------------------------------

def compute_sensitivity_index(
    results: List[SensitivityResult],
) -> Dict[str, float]:
    """Rank parameters by influence on the metric.

    The sensitivity index for each parameter is defined as the range
    (max - min) of the metric values observed during the sweep.
    Parameters with a larger range are more influential.

    Args:
        results: List of :class:`SensitivityResult` from individual
            parameter sweeps.

    Returns:
        Dictionary mapping parameter name to sensitivity index, sorted
        in descending order of influence.
    """
    index: Dict[str, float] = {}
    for r in results:
        metric_range = float(np.max(r.metric_values) - np.min(r.metric_values))
        index[r.parameter_name] = metric_range

    # Sort descending by sensitivity
    return dict(sorted(index.items(), key=lambda kv: kv[1], reverse=True))


# NOTE (P2-F10): synthetic quadratic surrogate for a defence-parameter response
# surface, NOT the real pipeline.  Its indices are labelled parametric/demo
# (parametric_simulation provenance) and must never be read as measured.
def make_default_evaluate_fn(
    rng: np.random.Generator,
) -> Callable[[float, float, float, float], float]:
    """Create a parameterized defense-threshold evaluation function.

    Models the detection rate as a function of interaction effects
    across injection_threshold, drift_threshold, trust_decay, and
    consensus_quorum.  Small Gaussian noise is added via *rng*.

    Parameters
    ----------
    rng : np.random.Generator
        Seeded random number generator.

    Returns
    -------
    callable
        ``(injection_threshold, drift_threshold, trust_decay,
        consensus_quorum) -> detection_rate``.
    """
    def evaluate(
        injection_threshold: float = 0.7,
        drift_threshold: float = 0.3,
        trust_decay: float = 0.85,
        consensus_quorum: float = 0.667,
    ) -> float:
        base = 0.85
        inj_effect = -2.0 * (injection_threshold - 0.65) ** 2 + 0.10
        drift_effect = -1.5 * (drift_threshold - 0.25) ** 2 + 0.06
        trust_effect = -3.0 * (trust_decay - 0.85) ** 2 + 0.05
        quorum_effect = -2.5 * (consensus_quorum - 0.667) ** 2 + 0.04

        rate = base + inj_effect + drift_effect + trust_effect + quorum_effect
        rate += rng.normal(0, 0.005)
        return float(np.clip(rate, 0.0, 1.0))

    return evaluate

