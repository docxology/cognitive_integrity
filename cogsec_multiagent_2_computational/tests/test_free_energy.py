"""Tests for the Variational Free Energy formulation of CIF.

Covers:
- KL divergence basics (same distribution -> 0).
- Free energy increases under adversarial belief shifts.
- Precision-weighted trust fusion normalisation and composite precision.
- Epistemic / pragmatic value.
- Belief sandbox blocking suspicious updates that inflate ΔF.
- Mapping TrustConfig to FEP precisions sums to 1.

NO MOCKS. All tests use real numerical distributions and computations.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pytest

from src.core.trust import TrustConfig
from src.formal.free_energy import (
    BeliefState,
    GenerativeModel,
    belief_sandbox_as_constrained_inference,
    connect_to_trust_calculus,
    epistemic_value,
    free_energy_of_attack,
    kl_divergence,
    pragmatic_value,
    precision_weighted_trust,
    variational_free_energy,
)


def test_belief_state_validates_length():
    """BeliefState post_init checks probs/labels length match."""
    with pytest.raises(ValueError):
        BeliefState(probs=np.array([0.5, 0.5]), labels=["only_one_label"])


def test_belief_state_rejects_negative_probs():
    """Negative entries in probs are rejected."""
    with pytest.raises(ValueError):
        BeliefState(
            probs=np.array([0.7, -0.1, 0.4]),
            labels=["a", "b", "c"],
        )


def test_generative_model_validates_shapes():
    """likelihood columns must match prior length."""
    with pytest.raises(ValueError):
        GenerativeModel(
            prior=np.array([0.5, 0.5]),
            likelihood=np.array([[0.5, 0.5, 0.5]]),
        )


def test_kl_divergence_zero_for_identical_distributions():
    """KL(p || p) == 0 (up to epsilon flooring)."""
    p = np.array([0.2, 0.3, 0.5])
    assert abs(kl_divergence(p, p)) < 1e-8


def test_kl_divergence_non_negative_and_asymmetric():
    """KL is non-negative and generally asymmetric."""
    # Non-palindromic distributions so KL(p||q) != KL(q||p).
    p = np.array([0.7, 0.25, 0.05])
    q = np.array([0.1, 0.3, 0.6])
    assert kl_divergence(p, q) > 0
    assert kl_divergence(q, p) > 0
    assert abs(kl_divergence(p, q) - kl_divergence(q, p)) > 1e-3


def test_variational_free_energy_rejects_shape_mismatch():
    """q.probs must match prior shape."""
    q = BeliefState(probs=np.array([0.5, 0.5, 0.0]), labels=["a", "b", "c"])
    m = GenerativeModel(
        prior=np.array([0.5, 0.5]),
        likelihood=np.array([[0.8, 0.2], [0.2, 0.8]]),
    )
    with pytest.raises(ValueError):
        variational_free_energy(q, m, 0)


def test_free_energy_of_attack_increases_under_mismatched_belief():
    """Pushing belief *away* from the observation's likelihood raises F."""
    # Observation index 0 strongly supports state 0; attacker shifts
    # mass to state 1 instead.
    model = GenerativeModel(
        prior=np.array([0.5, 0.5]),
        likelihood=np.array([[0.9, 0.1], [0.1, 0.9]]),
    )
    baseline = BeliefState(probs=np.array([0.5, 0.5]), labels=["A", "B"])
    attacked = BeliefState(probs=np.array([0.05, 0.95]), labels=["A", "B"])

    result = free_energy_of_attack(baseline, attacked, model, observation_idx=0)
    assert result["free_energy_increase"] > 0.5
    assert result["kl_from_prior"] > 0.2
    assert result["is_attack"] is True


def test_precision_weighted_trust_normalises_and_sums_precisions():
    """Weighted fusion returns a valid posterior with summed precision."""
    a = BeliefState(probs=np.array([0.8, 0.2]), labels=["A", "B"], precision=0.3)
    b = BeliefState(probs=np.array([0.4, 0.6]), labels=["A", "B"], precision=0.7)
    fused = precision_weighted_trust([a, b], [0.3, 0.7])
    assert fused.probs.sum() == pytest.approx(1.0)
    assert fused.precision == pytest.approx(1.0)
    # Expected posterior: (0.3*0.8 + 0.7*0.4) / 1.0 = 0.52 on state A.
    assert fused.probs[0] == pytest.approx(0.52)


def test_precision_weighted_trust_rejects_bad_inputs():
    """Mismatched lengths and all-zero precisions are rejected."""
    a = BeliefState(probs=np.array([0.5, 0.5]), labels=["A", "B"])
    with pytest.raises(ValueError):
        precision_weighted_trust([a], [0.3, 0.7])
    with pytest.raises(ValueError):
        precision_weighted_trust([a], [0.0])


def test_epistemic_value_positive_when_posterior_is_sharper():
    """Information gain is positive when entropy decreases."""
    before = BeliefState(probs=np.array([0.5, 0.5]), labels=["A", "B"])
    after = BeliefState(probs=np.array([0.95, 0.05]), labels=["A", "B"])
    assert epistemic_value(before, after) > 0


def test_pragmatic_value_maximal_at_target():
    """-KL(Q || P*) is 0 when Q == P* and negative otherwise."""
    target = np.array([0.5, 0.5])
    q_match = BeliefState(probs=target.copy(), labels=["A", "B"])
    q_off = BeliefState(probs=np.array([0.9, 0.1]), labels=["A", "B"])
    assert abs(pragmatic_value(q_match, target)) < 1e-8
    assert pragmatic_value(q_off, target) < 0


def test_belief_sandbox_blocks_high_delta_F_update():
    """An update that drives beliefs away from the observation is blocked."""
    model = GenerativeModel(
        prior=np.array([0.5, 0.5]),
        likelihood=np.array([[0.9, 0.1], [0.1, 0.9]]),
    )
    prior = BeliefState(probs=np.array([0.5, 0.5]), labels=["A", "B"], precision=1.0)
    # Strongly pushes all mass away from state 0 (which is what obs 0 supports).
    result = belief_sandbox_as_constrained_inference(
        prior,
        suspicious_update=np.array([-10.0, 10.0]),
        model=model,
        observation_idx=0,
        kappa_threshold=0.5,
    )
    assert result["sandbox_blocks"] is True
    assert result["delta_F"] > 0
    # Rejected: q_accepted is the original prior.
    accepted = result["q_accepted"]
    np.testing.assert_allclose(accepted.probs, prior.probs)


def test_belief_sandbox_accepts_reasonable_update():
    """A small, aligned update is accepted."""
    model = GenerativeModel(
        prior=np.array([0.5, 0.5]),
        likelihood=np.array([[0.9, 0.1], [0.1, 0.9]]),
    )
    prior = BeliefState(probs=np.array([0.5, 0.5]), labels=["A", "B"], precision=1.0)
    result = belief_sandbox_as_constrained_inference(
        prior,
        suspicious_update=np.array([0.1, -0.1]),  # gentle push toward state 0
        model=model,
        observation_idx=0,
        kappa_threshold=2.0,
    )
    assert result["sandbox_blocks"] is False
    accepted = result["q_accepted"]
    assert accepted.probs[0] > prior.probs[0]


def test_connect_to_trust_calculus_matches_defaults():
    """The default TrustConfig maps to precisions summing to 1.0."""
    cfg = TrustConfig()
    precisions = connect_to_trust_calculus(cfg)
    assert precisions["alpha_precision"] == pytest.approx(cfg.alpha)
    assert precisions["beta_precision"] == pytest.approx(cfg.beta)
    assert precisions["gamma_precision"] == pytest.approx(cfg.gamma)
    assert precisions["composite_precision"] == pytest.approx(1.0)
