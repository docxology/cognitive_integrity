"""Convergence analysis for adversarial training Nash equilibrium estimation."""

from __future__ import annotations

import math

import numpy as np


def natural_gradient_at_step(
    theta: np.ndarray,
    gradient: np.ndarray,
    fisher_info: np.ndarray,
    learning_rate: float = 0.05,
) -> np.ndarray:
    """Execute a natural gradient AT update step.

    Computes the Fisher-Rao metric-aware gradient ascent step for the
    defender's threshold configuration, achieving second-order convergence
    near the Nash equilibrium (Theorem S11.2).

    Args:
        theta: Current defense configuration vector.
        gradient: Euclidean gradient of detection rate w.r.t. theta.
        fisher_info: Fisher information matrix at theta (symmetric positive definite).
        learning_rate: Step size alpha.

    Returns:
        Updated theta after natural gradient step.
    """
    # Natural gradient: G^{-1} * gradient
    try:
        nat_grad = np.linalg.solve(fisher_info, gradient)
    except np.linalg.LinAlgError:
        # Fall back to Euclidean gradient if Fisher matrix is singular
        nat_grad = gradient
    return theta + learning_rate * nat_grad


def geometric_convergence_projection(
    gains: list[float],
    baseline_dr: float,
) -> tuple[float, float]:
    """Project Nash equilibrium DR using geometric decay model.

    Args:
        gains: Per-round DR improvement over baseline.
        baseline_dr: Pre-AT baseline detection rate.

    Returns:
        Tuple of (projected_equilibrium_dr, geometric_ratio).
    """
    if not gains or gains[0] <= 0:
        return baseline_dr, 0.65

    # Compute per-step ratios
    ratios = [
        gains[i + 1] / gains[i]
        for i in range(len(gains) - 1)
        if gains[i] > 1e-9
    ]
    ratio = float(np.median(ratios)) if ratios else 0.65
    ratio = max(0.01, min(0.99, ratio))

    # Geometric series: total gain = first_gain / (1 - ratio)
    total_gain = gains[0] / (1.0 - ratio)
    projected_dr = min(1.0, baseline_dr + total_gain)
    return float(projected_dr), ratio


def convergence_round_estimate(
    gains: list[float],
    tolerance: float = 0.001,
) -> int:
    """Estimate the round at which gains fall below tolerance.

    Args:
        gains: Per-round DR improvement values.
        tolerance: Convergence threshold.

    Returns:
        Estimated convergence round.
    """
    if not gains or gains[0] <= tolerance:
        return 0
    _, ratio = geometric_convergence_projection(gains, 0.0)
    if ratio <= 0:
        return 0
    k = math.log(tolerance / gains[0]) / math.log(ratio)
    return int(math.ceil(k))


def empirical_lipschitz_constant(
    config: dict[str, float],
    dr_evaluator: object,
    epsilon: float = 0.01,
) -> float:
    """Estimate Lipschitz constant of DR w.r.t. configuration perturbations.

    Perturbs each dimension of the config by epsilon and measures
    the resulting change in DR, returning the maximum ratio.

    Args:
        config: Defense configuration dict.
        dr_evaluator: Object with evaluate(config) -> float method.
        epsilon: Perturbation magnitude.

    Returns:
        Estimated Lipschitz constant L.
    """
    if not hasattr(dr_evaluator, "evaluate"):
        raise ValueError("dr_evaluator must have an evaluate(config) method")

    base_dr = dr_evaluator.evaluate(config)  # type: ignore[attr-defined]
    keys = list(config.keys())
    max_ratio = 0.0

    for key in keys:
        perturbed = dict(config)
        perturbed[key] = min(1.0, config[key] + epsilon)
        perturbed_dr = dr_evaluator.evaluate(perturbed)  # type: ignore[attr-defined]
        ratio = abs(perturbed_dr - base_dr) / epsilon
        max_ratio = max(max_ratio, ratio)

    return float(max_ratio)
