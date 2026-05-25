"""Tests for the information-geometric structure of belief space.

Covers:
- Fisher-Rao / Hellinger distance symmetry and self-distance.
- Geodesic path endpoints match start / end.
- Geodesic path elements remain on the probability simplex.
- Curvature constant for categorical distributions.
- defense_as_curvature_constraint blocks large steps, accepts small.
- Natural-gradient sensitivity scaling by p.
- Natural-gradient attack ascent increases the score.

NO MOCKS. All tests use real numerical distributions.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pytest

from src.analysis.information_geometry import (
    StatisticalManifold,
    defense_as_curvature_constraint,
    geodesic_attack_path,
    natural_gradient_attack,
    sensitivity_via_riemannian_metric,
)


def test_fisher_information_matrix_diagonal():
    """Fisher information is the diagonal of 1/p."""
    mfd = StatisticalManifold(n_outcomes=3)
    p = np.array([0.2, 0.3, 0.5])
    G = mfd.fisher_information_matrix(p)
    assert G.shape == (3, 3)
    # Off-diagonal entries are zero.
    assert np.allclose(G - np.diag(np.diag(G)), 0.0)
    # Diagonal is approximately 1/p.
    assert np.allclose(np.diag(G), 1.0 / (p + 1e-12), atol=1e-8)


def test_riemannian_distance_symmetry():
    """d(p, q) == d(q, p)."""
    mfd = StatisticalManifold(n_outcomes=4)
    p = np.array([0.4, 0.3, 0.2, 0.1])
    q = np.array([0.1, 0.2, 0.3, 0.4])
    d_pq = mfd.riemannian_distance(p, q)
    d_qp = mfd.riemannian_distance(q, p)
    assert d_pq == pytest.approx(d_qp, abs=1e-12)
    assert d_pq > 0


def test_riemannian_self_distance_zero():
    """d(p, p) == 0 up to the numerical arccos floor."""
    mfd = StatisticalManifold(n_outcomes=3)
    p = np.array([0.5, 0.3, 0.2])
    # The clip at (1 - 1e-10) introduces an O(sqrt(1e-10)) ~ 1e-5 floor.
    assert mfd.riemannian_distance(p, p) == pytest.approx(0.0, abs=1e-4)


def test_geodesic_path_endpoints_match():
    """The first and last path points are (approximately) the endpoints."""
    mfd = StatisticalManifold(n_outcomes=3)
    start = np.array([0.8, 0.1, 0.1])
    end = np.array([0.1, 0.1, 0.8])
    path = mfd.geodesic_path(start, end, n_steps=50)
    assert path.shape == (50, 3)
    np.testing.assert_allclose(path[0], start, atol=1e-10)
    np.testing.assert_allclose(path[-1], end, atol=1e-10)


def test_geodesic_path_stays_on_simplex():
    """Every path point sums to 1 and has non-negative entries."""
    mfd = StatisticalManifold(n_outcomes=4)
    start = np.array([0.25, 0.25, 0.25, 0.25])
    end = np.array([0.7, 0.1, 0.1, 0.1])
    path = mfd.geodesic_path(start, end, n_steps=30)
    sums = path.sum(axis=1)
    assert np.allclose(sums, 1.0, atol=1e-10)
    assert np.all(path >= -1e-12)


def test_curvature_constant_for_categorical():
    """Scalar curvature is n*(n-1)/4 for the Hellinger-embedded simplex."""
    mfd = StatisticalManifold(n_outcomes=4)
    p = np.array([0.1, 0.2, 0.3, 0.4])
    c = mfd.curvature_at(p)
    assert c == pytest.approx(4 * 3 / 4.0)


def test_geodesic_attack_path_shapes():
    """geodesic_attack_path returns path/distances/risk of matching length."""
    baseline = np.array([0.5, 0.3, 0.2])
    target = np.array([0.1, 0.3, 0.6])
    out = geodesic_attack_path(baseline, target, n_steps=40)
    assert out["path"].shape == (40, 3)
    assert out["distances"].shape == (40,)
    assert out["detection_risk"].shape == (40,)
    # Distance at t=0 is 0; at t=1 is the total Fisher-Rao distance.
    # (O(1e-5) floor from arccos clip -- assert "near zero" not exactly zero.)
    assert out["distances"][0] == pytest.approx(0.0, abs=1e-4)
    assert out["distances"][-1] > 0.0
    # Risk is monotone in distance (detection_risk is 1 - exp(-2d)).
    risk = out["detection_risk"]
    assert risk[0] == pytest.approx(0.0, abs=1e-3)
    assert risk[-1] > 0.0
    for t in range(1, len(risk)):
        assert risk[t] >= risk[t - 1] - 1e-8


def test_defense_as_curvature_constraint_blocks_large_step():
    """A large candidate update is rejected; prior state is returned."""
    p = np.array([0.5, 0.3, 0.2])
    proposed = np.array([0.01, 0.01, 0.98])
    accepted, blocked = defense_as_curvature_constraint(
        p, max_geodesic_step=0.05, proposed_update=proposed
    )
    assert blocked is True
    np.testing.assert_allclose(accepted, p)


def test_defense_as_curvature_constraint_accepts_small_step():
    """A small update is accepted; the returned belief is normalised."""
    p = np.array([0.5, 0.3, 0.2])
    proposed = np.array([0.51, 0.29, 0.20])
    accepted, blocked = defense_as_curvature_constraint(
        p, max_geodesic_step=0.5, proposed_update=proposed
    )
    assert blocked is False
    assert accepted.sum() == pytest.approx(1.0, abs=1e-10)


def test_sensitivity_natural_gradient_scales_by_p():
    """The natural gradient is the elementwise product of p and scores."""
    scores = np.array([0.8, 0.5, 0.2])
    p = np.array([0.1, 0.4, 0.5])
    nat = sensitivity_via_riemannian_metric(scores, p)
    np.testing.assert_allclose(nat, p * scores)


def test_natural_gradient_attack_increases_score():
    """Ascent along the natural gradient raises the score monotonically on avg."""
    mfd = StatisticalManifold(n_outcomes=3)
    p0 = np.array([0.33, 0.33, 0.34])

    def score(p):
        # Linear score favouring the first state.
        return float(p[0])

    result = natural_gradient_attack(
        p0, score_fn=score, manifold=mfd, step_size=0.05, n_steps=20
    )
    assert result["path"].shape == (21, 3)
    assert result["scores"].shape == (21,)
    assert result["scores"][-1] > result["scores"][0]
    # Every intermediate belief is on the simplex.
    assert np.allclose(result["path"].sum(axis=1), 1.0, atol=1e-8)


def test_natural_gradient_attack_rejects_mismatched_p():
    """Shape mismatch between p and manifold raises ValueError."""
    mfd = StatisticalManifold(n_outcomes=3)
    with pytest.raises(ValueError):
        natural_gradient_attack(
            np.array([0.5, 0.5]),
            score_fn=lambda x: float(x[0]),
            manifold=mfd,
            step_size=0.1,
            n_steps=2,
        )
