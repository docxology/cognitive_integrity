"""Additional tests for src/formal/trust_bounds.py — the FAILED branch.

Audit TEST-05/TEST-06 background
--------------------------------
The previous version of this file claimed to cover ``validate_trust_bound``'s
FAILED branch but every test accepted either outcome
(``assert result.status in (PASSED, FAILED)``), so no test could ever fail.
The validator itself was tautological as well: it only checked
``T_delegated <= delta^d``, which holds for *any* aggregator of two values in
[0, 1] scaled by ``delta^d`` — including ``max``, i.e. an implementation that
amplifies trust through delegation.

Every FAILED-branch test below now asserts a definite status, and the
amplifying/no-decay stubs are the positive controls proving the checker can
actually reject a wrong implementation.

All tests use real computation. No mocks.
"""

from __future__ import annotations

import pytest

from core.trust import TrustCalculus, TrustConfig
from formal.theorem_registry import TheoremStatus
from formal.trust_bounds import DECAY_FACTOR_DEFAULT, validate_trust_bound


def amplifying_delegation(source: float, target: float, depth: int) -> float:
    """Wrong implementation: takes the *strongest* link instead of the weakest.

    Still obeys ``T <= delta^d`` because both inputs are in [0, 1], which is
    exactly why the old absolute-bound-only check could not see it.
    """
    return max(source, target) * (DECAY_FACTOR_DEFAULT ** depth)


def no_decay_delegation(source: float, target: float, depth: int) -> float:
    """Wrong implementation: weakest link but no depth attenuation."""
    return min(source, target)


def unit_delegation(source: float, target: float, depth: int) -> float:
    """Wrong implementation: full trust regardless of the chain."""
    return 1.0


class TestTrustBoundsFailedBranch:
    """Tests for the FAILED branch and edge cases in validate_trust_bound."""

    def test_default_params_pass(self):
        result = validate_trust_bound(seed=42)
        assert result.status == TheoremStatus.PASSED
        assert result.details["implementation"] == (
            "core.trust.TrustCalculus.delegate_trust"
        )

    def test_amplifying_implementation_is_rejected(self):
        """Positive control: trust amplification must be reported as FAILED.

        ``max`` instead of ``min`` survived the old checker untouched.
        """
        result = validate_trust_bound(
            delegate_fn=amplifying_delegation, max_depth=5, n_trials=200, seed=42
        )
        assert result.status == TheoremStatus.FAILED
        assert result.details["amplification_violations"] > 0
        assert result.details["max_amplification"] > 0.0
        # The absolute decay bound alone cannot see this defect — which is the
        # whole point of adding the weakest-link check.
        assert result.details["decay_violations"] == 0

    def test_no_decay_implementation_is_rejected(self):
        """An implementation that forgets delta^d must be reported as FAILED."""
        result = validate_trust_bound(
            delegate_fn=no_decay_delegation, max_depth=5, n_trials=200, seed=42
        )
        assert result.status == TheoremStatus.FAILED
        assert result.details["decay_violations"] > 0
        assert result.details["amplification_violations"] > 0

    def test_unit_delegation_is_rejected(self):
        result = validate_trust_bound(
            delegate_fn=unit_delegation, max_depth=3, n_trials=100, seed=7
        )
        assert result.status == TheoremStatus.FAILED
        assert result.details["violations"] > 0

    def test_failed_evidence_reports_both_violation_classes(self):
        result = validate_trust_bound(
            delegate_fn=amplifying_delegation, max_depth=3, n_trials=100, seed=42
        )
        assert result.status == TheoremStatus.FAILED
        assert "amplified" in result.evidence
        assert "violated" in result.evidence

    def test_production_delegation_matches_weakest_link_formula(self):
        """The passing verdict is bound to the shipped implementation.

        Sampled directly from ``TrustCalculus`` so the checker's premise —
        ``delegated == min(source, target) * delta^d`` — is asserted against
        real code rather than restated.
        """
        calculus = TrustCalculus(TrustConfig(decay=DECAY_FACTOR_DEFAULT))
        for depth in range(1, 6):
            for source in (0.1, 0.5, 0.9, 1.0):
                for target in (0.1, 0.5, 0.9, 1.0):
                    delegated = calculus.delegate_trust(source, target, depth=depth)
                    expected = min(source, target) * DECAY_FACTOR_DEFAULT ** depth
                    assert delegated == pytest.approx(expected, abs=1e-12)
                    # And the amplifying alternative genuinely differs whenever
                    # the two links are not equal.
                    if source != target:
                        assert delegated < amplifying_delegation(
                            source, target, depth
                        )

    def test_delta_greater_than_one_causes_violations(self):
        """delta > 1 is not valid — TrustConfig enforces decay in (0, 1)."""
        with pytest.raises(ValueError, match="Decay must be in"):
            validate_trust_bound(delta=1.5, max_depth=2, n_trials=10, seed=42)

    def test_delta_validated_even_with_injected_delegate_fn(self):
        """The decay range check must not be bypassed by the injection hook."""
        with pytest.raises(ValueError, match="Decay must be in"):
            validate_trust_bound(
                delta=1.5, delegate_fn=amplifying_delegation, n_trials=5
            )

    def test_tiny_delta_still_passes_for_production_code(self):
        """delta=1e-10: the bound shrinks with delta, so the real code holds."""
        result = validate_trust_bound(delta=1e-10, max_depth=1, n_trials=100, seed=42)
        assert result.status == TheoremStatus.PASSED
        assert result.details["violations"] == 0

    def test_result_details_keys(self):
        result = validate_trust_bound(seed=42)
        expected_keys = {
            "delta",
            "max_depth",
            "n_trials",
            "total_samples",
            "violations",
            "max_violation",
            "decay_violations",
            "amplification_violations",
            "max_amplification",
            "implementation",
        }
        assert expected_keys == set(result.details.keys())

    def test_total_samples_equals_depth_times_trials(self):
        max_depth = 5
        n_trials = 100
        result = validate_trust_bound(max_depth=max_depth, n_trials=n_trials, seed=42)
        assert result.details["total_samples"] == max_depth * n_trials

    def test_deterministic_with_same_seed(self):
        r1 = validate_trust_bound(delta=0.85, max_depth=5, n_trials=100, seed=99)
        r2 = validate_trust_bound(delta=0.85, max_depth=5, n_trials=100, seed=99)
        assert r1.details == r2.details
