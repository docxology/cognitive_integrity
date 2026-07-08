"""Information geometry of belief space for CIF.

Belief distributions live on the probability simplex ``Δ^{n-1}``.
Equipped with the Fisher-Rao metric ``G_ij(p) = δ_ij / p_i`` the
simplex becomes a Riemannian manifold whose geodesic (Hellinger)
distance is::

    d(p, q) = 2 arccos(sum_i sqrt(p_i * q_i))

This module provides:

- :class:`StatisticalManifold` -- Fisher information, Riemannian
  distance, geodesic paths, and scalar curvature.
- :func:`geodesic_attack_path` -- simulate an attacker following the
  shortest information-geometric path towards a target belief.
- :func:`defense_as_curvature_constraint` -- reject belief updates
  whose geodesic step exceeds a budget (natural-gradient sandbox).
- :func:`sensitivity_via_riemannian_metric` -- natural-gradient
  reweighting of per-state detection scores.
- :func:`natural_gradient_attack` -- adversarial ascent using the
  natural gradient (``G^{-1}(p) ∇``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# Statistical manifold
# ---------------------------------------------------------------------------

@dataclass
class StatisticalManifold:
    """Probability simplex with Fisher-Rao Riemannian structure.

    Attributes:
        n_outcomes: Dimension of the underlying categorical
            distribution (number of elementary outcomes).
    """

    n_outcomes: int

    def fisher_information_matrix(self, p: np.ndarray) -> np.ndarray:
        """Fisher information ``G(p) = diag(1 / p_i)`` (with ε floor).

        Args:
            p: Probability vector of length ``n_outcomes``.

        Returns:
            ``(n, n)`` diagonal matrix.
        """
        p = np.asarray(p, dtype=float)
        if p.shape != (self.n_outcomes,):
            raise ValueError(
                f"p shape {p.shape} does not match manifold "
                f"n_outcomes={self.n_outcomes}"
            )
        return np.diag(1.0 / (p + 1e-12))

    def riemannian_distance(
        self,
        p: np.ndarray,
        q: np.ndarray,
    ) -> float:
        """Fisher-Rao / Hellinger geodesic distance on the simplex.

        ``d(p, q) = 2 arccos(sum_i sqrt(p_i q_i))`` with the inner
        product clipped into ``[-1+1e-10, 1-1e-10]`` for numerical
        safety.
        """
        p = np.asarray(p, dtype=float)
        q = np.asarray(q, dtype=float)
        if p.shape != q.shape:
            raise ValueError("p and q must share shape")
        dot = float(np.sum(np.sqrt(np.clip(p, 0.0, None) *
                                   np.clip(q, 0.0, None))))
        dot = float(np.clip(dot, -1.0 + 1e-10, 1.0 - 1e-10))
        return float(2.0 * np.arccos(dot))

    def geodesic_path(
        self,
        p_start: np.ndarray,
        p_end: np.ndarray,
        n_steps: int = 100,
    ) -> np.ndarray:
        """Parametrised geodesic from *p_start* to *p_end* on the simplex.

        Uses the Hellinger embedding: ``γ(t) = normalise_sqmag(
        sqrt(p_start) + t * (sqrt(p_end) - sqrt(p_start)))``.  The
        result is a sequence of squared magnitudes renormalised to
        valid probability vectors.

        Args:
            p_start, p_end: Endpoint probability vectors.
            n_steps: Number of points along the geodesic (inclusive).

        Returns:
            Array of shape ``(n_steps, n_outcomes)``.
        """
        p_start = np.asarray(p_start, dtype=float)
        p_end = np.asarray(p_end, dtype=float)
        if p_start.shape != (self.n_outcomes,) or p_end.shape != (self.n_outcomes,):
            raise ValueError("Endpoints must match manifold n_outcomes")

        s_start = np.sqrt(np.clip(p_start, 0.0, None))
        s_end = np.sqrt(np.clip(p_end, 0.0, None))

        ts = np.linspace(0.0, 1.0, n_steps)
        path = np.zeros((n_steps, self.n_outcomes), dtype=float)
        for i, t in enumerate(ts):
            mixed = s_start + t * (s_end - s_start)
            squared = mixed ** 2
            total = squared.sum()
            if total <= 0.0:
                # Degenerate mid-point: fall back to uniform.
                path[i] = np.ones(self.n_outcomes) / self.n_outcomes
            else:
                path[i] = squared / total
        return path

    def curvature_at(self, p: np.ndarray) -> float:  # noqa: ARG002 (p unused)
        """Scalar curvature of the simplex under Fisher-Rao.

        After the Hellinger embedding the simplex becomes a portion of
        a positive-radius sphere, so the scalar curvature is constant
        and independent of ``p``: ``n * (n - 1) / 4``.
        """
        n = self.n_outcomes
        return float(n * (n - 1) / 4.0)


# ---------------------------------------------------------------------------
# Geodesic attack simulation
# ---------------------------------------------------------------------------

def geodesic_attack_path(
    baseline_beliefs: np.ndarray,
    target_beliefs: np.ndarray,
    n_steps: int = 50,
) -> Dict[str, np.ndarray]:
    """Simulate an attacker interpolating beliefs along the geodesic.

    Computes the Fisher-Rao geodesic from *baseline_beliefs* to
    *target_beliefs*, the cumulative distance from the baseline at
    each step, and a smooth detection-risk proxy ``1 - exp(-2*d)``
    (monotone in ``d``).

    Args:
        baseline_beliefs: Starting probability vector.
        target_beliefs: Target probability vector.
        n_steps: Number of path samples.

    Returns:
        Dict with ``path`` (shape ``(n_steps, n)``), ``distances``
        (shape ``(n_steps,)``), ``detection_risk`` (shape ``(n_steps,)``).
    """
    baseline = np.asarray(baseline_beliefs, dtype=float)
    target = np.asarray(target_beliefs, dtype=float)
    if baseline.shape != target.shape:
        raise ValueError("baseline and target must share shape")

    manifold = StatisticalManifold(n_outcomes=len(baseline))
    path = manifold.geodesic_path(baseline, target, n_steps=n_steps)

    distances = np.array(
        [manifold.riemannian_distance(baseline, path[t])
         for t in range(n_steps)],
        dtype=float,
    )
    detection_risk = 1.0 - np.exp(-2.0 * distances)

    return {
        "path": path,
        "distances": distances,
        "detection_risk": detection_risk,
    }


# ---------------------------------------------------------------------------
# Curvature / step-budget constraint
# ---------------------------------------------------------------------------

def defense_as_curvature_constraint(
    p: np.ndarray,
    max_geodesic_step: float,
    proposed_update: np.ndarray,
) -> Tuple[np.ndarray, bool]:
    """Reject proposed updates whose geodesic step exceeds the budget.

    Normalises ``proposed_update`` to a probability vector and
    computes its Fisher-Rao distance from ``p``.  If the distance is
    greater than ``max_geodesic_step`` the original ``p`` is returned
    with ``blocked=True``; otherwise the update is accepted.

    Args:
        p: Current belief.
        max_geodesic_step: Maximum allowed geodesic step.
        proposed_update: Candidate new belief (to be renormalised).

    Returns:
        Tuple ``(accepted_belief, blocked)``.
    """
    p = np.asarray(p, dtype=float)
    prop = np.asarray(proposed_update, dtype=float)
    if prop.shape != p.shape:
        raise ValueError("proposed_update must share shape with p")
    prop_clipped = np.clip(prop, 0.0, None)
    total = prop_clipped.sum()
    if total <= 0.0:
        return p, True
    p_new = prop_clipped / total

    manifold = StatisticalManifold(n_outcomes=len(p))
    dist = manifold.riemannian_distance(p, p_new)
    if dist > max_geodesic_step:
        return p, True
    return p_new, False


# ---------------------------------------------------------------------------
# Natural-gradient sensitivity
# ---------------------------------------------------------------------------

def sensitivity_via_riemannian_metric(
    detection_scores: np.ndarray,
    p: np.ndarray,
) -> np.ndarray:
    """Natural-gradient reweighting: ``G^{-1}(p) · scores = p · scores``.

    Under the Fisher-Rao metric ``G^{-1}`` is ``diag(p)`` so the
    natural gradient is the pointwise product of probability mass and
    per-outcome detection sensitivity.

    Args:
        detection_scores: Per-state raw sensitivity scores.
        p: Current belief.

    Returns:
        Array with same shape as ``detection_scores``.
    """
    detection_scores = np.asarray(detection_scores, dtype=float)
    p = np.asarray(p, dtype=float)
    if detection_scores.shape != p.shape:
        raise ValueError("detection_scores and p must share shape")
    return p * detection_scores


# ---------------------------------------------------------------------------
# Natural-gradient attack simulation
# ---------------------------------------------------------------------------

def natural_gradient_attack(
    p: np.ndarray,
    score_fn: Callable[[np.ndarray], float],
    manifold: StatisticalManifold,
    step_size: float = 0.01,
    n_steps: int = 100,
) -> Dict[str, np.ndarray]:
    """Ascend ``score_fn`` along the natural gradient ``G^{-1} ∇ score``.

    The gradient is estimated via central finite differences; the
    natural gradient is obtained by elementwise multiplication with
    ``p`` (diagonal ``G^{-1}``).  After each step the iterate is
    clipped to the simplex and renormalised.

    Args:
        p: Initial belief.
        score_fn: Scalar function of belief to ascend.
        manifold: Statistical manifold (fixes dimension).
        step_size: Step size for the natural-gradient update.
        n_steps: Number of ascent steps.

    Returns:
        Dict with ``path`` (shape ``(n_steps+1, n)``) and ``scores``
        (shape ``(n_steps+1,)``).
    """
    p = np.asarray(p, dtype=float).copy()
    if p.shape != (manifold.n_outcomes,):
        raise ValueError("p must match manifold n_outcomes")

    n = len(p)
    eps = 1e-4
    path = np.zeros((n_steps + 1, n), dtype=float)
    scores = np.zeros(n_steps + 1, dtype=float)
    path[0] = p
    scores[0] = float(score_fn(p))

    for t in range(n_steps):
        grad = np.zeros(n, dtype=float)
        for i in range(n):
            plus = p.copy()
            minus = p.copy()
            plus[i] = plus[i] + eps
            minus[i] = max(0.0, minus[i] - eps)
            # Re-normalise the perturbed vectors.
            plus = plus / plus.sum() if plus.sum() > 0 else p
            minus = minus / minus.sum() if minus.sum() > 0 else p
            grad[i] = (score_fn(plus) - score_fn(minus)) / (2.0 * eps)

        # Natural gradient: G^{-1} @ grad with G^{-1} = diag(p)
        nat = p * grad
        p = p + step_size * nat
        p = np.clip(p, 0.0, None)
        total = p.sum()
        if total <= 0.0:
            p = np.ones(n) / n
        else:
            p = p / total
        path[t + 1] = p
        scores[t + 1] = float(score_fn(p))

    return {"path": path, "scores": scores}


__all__ = [
    "StatisticalManifold",
    "geodesic_attack_path",
    "defense_as_curvature_constraint",
    "sensitivity_via_riemannian_metric",
    "natural_gradient_attack",
]
