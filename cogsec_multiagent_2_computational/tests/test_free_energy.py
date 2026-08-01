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
    SANDBOX_UPDATE_SCALE,
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


def _binary_model() -> GenerativeModel:
    """A two-state / two-observation generative model used across tests."""
    return GenerativeModel(
        prior=np.array([0.5, 0.5]),
        likelihood=np.array([[0.9, 0.1], [0.1, 0.9]]),
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


# ---------------------------------------------------------------------------
# Belief-sandbox fail-closed path (audit TEST-14)
#
# The security-relevant branch: a candidate posterior that clips to all-zeros
# cannot be normalised, so the sandbox must refuse it outright rather than
# attempting an update it cannot represent.
# ---------------------------------------------------------------------------


def test_sandbox_blocks_degenerate_update_that_clips_to_zero():
    """An update that annihilates the posterior is BLOCKED, not accepted."""
    model = _binary_model()
    prior = BeliefState(probs=np.array([0.5, 0.5]), labels=["A", "B"], precision=1.0)
    # candidate = probs + SCALE * (-probs / SCALE) = 0 exactly.
    suspicious = -prior.probs / SANDBOX_UPDATE_SCALE

    result = belief_sandbox_as_constrained_inference(
        prior,
        suspicious_update=suspicious,
        model=model,
        observation_idx=0,
    )

    assert result["sandbox_blocks"] is True
    assert result["delta_F"] == float("inf")
    assert result["q_accepted"] is prior


def test_sandbox_blocks_update_that_clips_to_zero_via_negative_rectification():
    """Every component driven negative also lands on the fail-closed branch."""
    model = _binary_model()
    prior = BeliefState(probs=np.array([0.25, 0.75]), labels=["A", "B"], precision=1.0)

    result = belief_sandbox_as_constrained_inference(
        prior,
        suspicious_update=np.array([-100.0, -100.0]),
        model=model,
        observation_idx=1,
    )

    assert result["sandbox_blocks"] is True
    assert result["delta_F"] == float("inf")
    assert result["q_accepted"] is prior


def test_positive_control_sandbox_does_not_block_a_survivable_update():
    """Proves the degenerate-update tests above discriminate.

    The same call shape with an update that leaves surviving mass must take
    the ordinary path: a finite ΔF and (here) acceptance.  If the fail-closed
    branch were unconditional, this assertion would fail.
    """
    model = _binary_model()
    prior = BeliefState(probs=np.array([0.5, 0.5]), labels=["A", "B"], precision=1.0)

    result = belief_sandbox_as_constrained_inference(
        prior,
        suspicious_update=np.array([-4.0, 0.0]),  # clips A to 0.1, B survives
        model=model,
        observation_idx=0,
    )

    assert np.isfinite(result["delta_F"])
    assert result["q_accepted"] is not prior
    assert result["q_accepted"].probs.sum() == pytest.approx(1.0)


def test_sandbox_rejects_shape_mismatched_update():
    model = _binary_model()
    prior = BeliefState(probs=np.array([0.5, 0.5]), labels=["A", "B"])
    with pytest.raises(ValueError, match="suspicious_update shape mismatch"):
        belief_sandbox_as_constrained_inference(
            prior,
            suspicious_update=np.array([0.1, 0.1, 0.1]),
            model=model,
            observation_idx=0,
        )


# ---------------------------------------------------------------------------
# BeliefState.normalize (audit TEST-14): a public API no test called.
# ---------------------------------------------------------------------------


def test_normalize_sums_to_one_and_preserves_proportions():
    state = BeliefState(probs=np.array([2.0, 6.0]), labels=["A", "B"], precision=3.5)
    normalised = state.normalize()

    assert normalised.probs.sum() == pytest.approx(1.0)
    np.testing.assert_allclose(normalised.probs, np.array([0.25, 0.75]))
    assert normalised.labels == ["A", "B"]
    assert normalised.precision == pytest.approx(3.5)
    # The original is untouched (normalize returns a copy).
    np.testing.assert_allclose(state.probs, np.array([2.0, 6.0]))
    assert normalised.labels is not state.labels


def test_normalize_is_idempotent_on_an_already_normalised_state():
    state = BeliefState(probs=np.array([0.25, 0.75]), labels=["A", "B"])
    np.testing.assert_allclose(state.normalize().probs, state.probs)


def test_normalize_all_zero_raises():
    """A state with no mass cannot be normalised -- it must not silently pass."""
    state = BeliefState(probs=np.array([0.0, 0.0]), labels=["A", "B"])
    with pytest.raises(ValueError, match="Cannot normalize an all-zero BeliefState"):
        state.normalize()


# ---------------------------------------------------------------------------
# Every remaining ValueError guard in the module (audit TEST-14).
#
# Each case is paired, in the same parametrisation, with the observation that
# the *adjacent* valid input is accepted -- see the positive control below --
# so a guard that fired unconditionally would be caught.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (
            lambda: BeliefState(probs=np.array([[0.5, 0.5]]), labels=["A", "B"]),
            "must be 1-D",
        ),
        (
            lambda: GenerativeModel(prior=np.array([[0.5, 0.5]]), likelihood=np.eye(2)),
            "prior must be 1-D",
        ),
        (
            lambda: GenerativeModel(prior=np.array([0.5, 0.5]), likelihood=np.array([0.5, 0.5])),
            "likelihood must be 2-D",
        ),
        (
            lambda: GenerativeModel(prior=np.array([-0.5, 1.5]), likelihood=np.eye(2)),
            "must be non-negative",
        ),
        (
            lambda: variational_free_energy(
                BeliefState(probs=np.array([0.5, 0.5]), labels=["A", "B"]),
                _binary_model(),
                observation_idx=7,
            ),
            "out of range",
        ),
        (
            lambda: precision_weighted_trust([], []),
            "requires >= 1 message",
        ),
        (
            lambda: precision_weighted_trust(
                [BeliefState(probs=np.array([0.5, 0.5]), labels=["A", "B"])], [1.0, 2.0]
            ),
            "length mismatch",
        ),
        (
            lambda: precision_weighted_trust(
                [BeliefState(probs=np.array([0.5, 0.5]), labels=["A", "B"])], [-1.0]
            ),
            "must be non-negative",
        ),
        (
            lambda: precision_weighted_trust(
                [BeliefState(probs=np.array([0.5, 0.5]), labels=["A", "B"])], [0.0]
            ),
            "must be positive",
        ),
        (
            lambda: precision_weighted_trust(
                [
                    BeliefState(probs=np.array([0.5, 0.5]), labels=["A", "B"]),
                    BeliefState(probs=np.array([0.3, 0.3, 0.4]), labels=["A", "B", "C"]),
                ],
                [1.0, 1.0],
            ),
            "must share dimension",
        ),
        (
            lambda: precision_weighted_trust(
                [BeliefState(probs=np.array([0.0, 0.0]), labels=["A", "B"])], [1.0]
            ),
            "Accumulated mass is zero",
        ),
        (
            lambda: pragmatic_value(
                BeliefState(probs=np.array([0.5, 0.5]), labels=["A", "B"]),
                np.array([0.3, 0.3, 0.4]),
            ),
            "preferred_states shape mismatch",
        ),
    ],
)
def test_guard_clauses_reject_invalid_input(call, message):
    with pytest.raises(ValueError, match=message):
        call()


def test_positive_control_guard_clauses_admit_valid_input():
    """The guards above are conditional, not unconditional raises.

    Each production call exercised in the parametrisation is repeated here
    with the one offending argument corrected; every one must succeed.
    """
    model = _binary_model()
    good = BeliefState(probs=np.array([0.5, 0.5]), labels=["A", "B"])

    assert BeliefState(probs=np.array([0.5, 0.5]), labels=["A", "B"]).probs.ndim == 1
    assert GenerativeModel(prior=np.array([0.5, 0.5]), likelihood=np.eye(2)).likelihood.ndim == 2
    assert np.isfinite(variational_free_energy(good, model, observation_idx=1))
    assert precision_weighted_trust([good], [1.0]).precision == pytest.approx(1.0)
    assert precision_weighted_trust([good, good], [1.0, 1.0]).probs.sum() == pytest.approx(1.0)
    assert pragmatic_value(good, np.array([0.5, 0.5])) == pytest.approx(0.0, abs=1e-9)
