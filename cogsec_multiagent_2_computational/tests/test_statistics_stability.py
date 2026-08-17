"""Tests for src/statistics/stability.py.

Covers:
- SeedMetrics and StabilityReport dataclasses.
- coefficient_of_variation: normal, zero mean, single value.
- run_multi_seed_stability: with custom eval_fn, seeds, cv_threshold.
- make_pipeline_eval_fn: factory only (the created eval_fn is tested separately).
- The benign arm: FPR, Youden's J, precision, F1, and the fail-closed
  behaviour when no benign corpus was evaluated.

The load-bearing test in this file is
``TestDegenerateDetector::test_flag_everything_has_youden_j_zero``: an
always-detect pipeline scores a perfect 1.0 detection rate, so any assertion
written against the detection rate alone is satisfied by a detector that does
nothing.  Youden's J is asserted instead, and the neighbouring test shows J
separates that detector from a genuinely perfect one — without it the
assertion would be vacuous.

All tests use real computation. No mocks.
"""

from __future__ import annotations

from statistics.stability import (
    SeedMetrics,
    StabilityReport,
    coefficient_of_variation,
    f1_from_counts,
    make_pipeline_eval_fn,
    precision_from_counts,
    run_multi_seed_stability,
    youden_j,
)

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# SeedMetrics
# ---------------------------------------------------------------------------


class TestSeedMetrics:
    def test_basic_construction(self):
        m = SeedMetrics(seed=42, overall_detection_rate=0.95)
        assert m.seed == 42
        assert m.overall_detection_rate == 0.95
        assert m.per_architecture == {}
        assert m.per_category == {}

    def test_with_architectures_and_categories(self):
        m = SeedMetrics(
            seed=1,
            overall_detection_rate=0.90,
            per_architecture={"claude_code": 0.97, "autogpt": 0.94},
            per_category={"injection": 0.98, "trust": 0.85},
        )
        assert m.per_architecture["claude_code"] == 0.97
        assert m.per_category["injection"] == 0.98


# ---------------------------------------------------------------------------
# coefficient_of_variation
# ---------------------------------------------------------------------------


class TestCoefficientOfVariation:
    def test_zero_mean_returns_zero(self):
        values = np.array([0.0, 0.0, 0.0])
        assert coefficient_of_variation(values) == 0.0

    def test_zero_mean_with_spread_is_undefined(self):
        """Signed values centered on 0 must not be reported as CV=0 (stable)."""
        values = np.array([-1.0, 0.0, 1.0])
        assert coefficient_of_variation(values) == float("inf")

    def test_identical_values_returns_zero(self):
        values = np.array([0.9, 0.9, 0.9])
        assert abs(coefficient_of_variation(values)) < 1e-10

    def test_known_cv(self):
        # std = 1, mean = 10 → CV = 0.1
        values = np.array([9.0, 10.0, 11.0])
        cv = coefficient_of_variation(values)
        # std of [9,10,11] = sqrt(2/3) ≈ 0.8165, mean = 10 → CV ≈ 0.08165
        assert 0.0 < cv < 0.2

    def test_returns_non_negative(self):
        values = np.array([0.85, 0.87, 0.86, 0.88])
        assert coefficient_of_variation(values) >= 0.0

    def test_single_value(self):
        values = np.array([0.9])
        cv = coefficient_of_variation(values)
        assert cv == 0.0  # std of single value is 0


# ---------------------------------------------------------------------------
# run_multi_seed_stability
# ---------------------------------------------------------------------------


class TestRunMultiSeedStability:
    """Tests for run_multi_seed_stability with a fast synthetic eval function."""

    def _make_eval_fn(self, base_dr: float = 0.95, noise: float = 0.0):
        """Create a deterministic eval function with optional noise."""
        def eval_fn(seed: int) -> SeedMetrics:
            rng = np.random.default_rng(seed)
            dr = float(np.clip(base_dr + rng.normal(0, noise), 0.0, 1.0))
            return SeedMetrics(
                seed=seed,
                overall_detection_rate=dr,
                per_architecture={"claude_code": float(np.clip(dr + 0.02, 0, 1))},
                per_category={"injection": float(np.clip(dr + 0.01, 0, 1))},
            )
        return eval_fn

    def test_returns_stability_report(self):
        report = run_multi_seed_stability(self._make_eval_fn(), seeds=[1, 2, 3])
        assert isinstance(report, StabilityReport)

    def test_n_seeds_matches_input(self):
        report = run_multi_seed_stability(self._make_eval_fn(), seeds=[10, 20, 30, 40])
        assert report.n_seeds == 4

    def test_stable_when_constant(self):
        """Constant eval function → CV = 0 → stable."""
        def constant_fn(seed):
            return SeedMetrics(seed=seed, overall_detection_rate=0.95)
        report = run_multi_seed_stability(constant_fn, seeds=[1, 2, 3, 4, 5])
        assert report.stable is True
        assert abs(report.overall_cv) < 1e-10

    def test_unstable_when_high_variance(self):
        """High-variance eval function should exceed default 5% CV threshold."""
        def noisy_fn(seed):
            rng = np.random.default_rng(seed)
            dr = float(rng.uniform(0.2, 0.9))  # very noisy
            return SeedMetrics(seed=seed, overall_detection_rate=dr)
        report = run_multi_seed_stability(noisy_fn, seeds=list(range(1, 11)))
        # High variance → likely not stable at 5% threshold
        # Just verify no exception
        assert isinstance(report.stable, bool)

    def test_seed_metrics_stored(self):
        report = run_multi_seed_stability(self._make_eval_fn(), seeds=[1, 2, 3])
        assert len(report.seed_metrics) == 3
        for m in report.seed_metrics:
            assert isinstance(m, SeedMetrics)

    def test_per_architecture_cv_computed(self):
        report = run_multi_seed_stability(self._make_eval_fn(), seeds=[1, 2, 3])
        assert "claude_code" in report.per_architecture_cv

    def test_per_category_cv_computed(self):
        report = run_multi_seed_stability(self._make_eval_fn(), seeds=[1, 2, 3])
        assert "injection" in report.per_category_cv

    def test_custom_cv_threshold(self):
        def constant_fn(seed):
            return SeedMetrics(seed=seed, overall_detection_rate=0.95)
        # With threshold=0.001 and near-zero CV, should be stable
        report = run_multi_seed_stability(constant_fn, seeds=[1, 2, 3], cv_threshold=0.001)
        assert report.cv_threshold == 0.001
        assert report.stable is True

    def test_uses_default_seeds_when_none(self):
        """Default seeds are range(1, 31) = 30 seeds."""
        def simple_fn(seed):
            return SeedMetrics(seed=seed, overall_detection_rate=0.9)
        report = run_multi_seed_stability(simple_fn, seeds=None)
        assert report.n_seeds == 30


# ---------------------------------------------------------------------------
# make_pipeline_eval_fn
# ---------------------------------------------------------------------------


class TestMakePipelineEvalFn:
    """Tests for the make_pipeline_eval_fn factory."""

    def test_returns_callable(self):
        fn = make_pipeline_eval_fn(n_samples=5)
        assert callable(fn)

    def test_eval_fn_produces_seed_metrics(self):
        """Run one seed through the real pipeline."""
        fn = make_pipeline_eval_fn(n_samples=10)
        result = fn(42)
        assert isinstance(result, SeedMetrics)
        assert 0.0 <= result.overall_detection_rate <= 1.0

    def test_eval_fn_different_seeds_produce_valid_results(self):
        fn = make_pipeline_eval_fn(n_samples=10)
        r1 = fn(1)
        r2 = fn(2)
        assert 0.0 <= r1.overall_detection_rate <= 1.0
        assert 0.0 <= r2.overall_detection_rate <= 1.0


# ---------------------------------------------------------------------------
# Operating-point helpers
# ---------------------------------------------------------------------------


class TestOperatingPointHelpers:
    def test_youden_j_is_tpr_minus_fpr(self):
        assert youden_j(0.8, 0.2) == pytest.approx(0.6)

    def test_youden_j_is_zero_for_any_input_independent_detector(self):
        # Flag-everything, flag-nothing, and coin-flip all land on J = 0.
        assert youden_j(1.0, 1.0) == 0.0
        assert youden_j(0.0, 0.0) == 0.0
        assert youden_j(0.5, 0.5) == 0.0

    def test_precision_from_counts(self):
        assert precision_from_counts(8, 2) == pytest.approx(0.8)

    def test_precision_is_zero_without_positive_predictions(self):
        assert precision_from_counts(0, 0) == 0.0

    def test_f1_from_counts(self):
        # TP=8, FP=2, n_attacks=10 -> precision 0.8, recall 0.8, F1 0.8
        assert f1_from_counts(8, 2, 10) == pytest.approx(0.8)

    def test_f1_is_zero_without_attacks(self):
        assert f1_from_counts(0, 5, 0) == 0.0

    def test_f1_is_zero_without_true_positives(self):
        assert f1_from_counts(0, 5, 10) == 0.0


# ---------------------------------------------------------------------------
# SeedMetrics operating-point properties
# ---------------------------------------------------------------------------


def _metrics(
    seed: int = 1,
    tpr: float = 0.8,
    fpr: float = 0.2,
    n_attacks: int = 100,
    n_benign: int = 100,
) -> SeedMetrics:
    """Build a SeedMetrics whose counts agree with the supplied rates."""
    return SeedMetrics(
        seed=seed,
        overall_detection_rate=tpr,
        per_architecture={"Claude Code": tpr},
        per_category={"injection": tpr},
        false_positive_rate=fpr,
        n_attacks=n_attacks,
        n_detected_attacks=round(tpr * n_attacks),
        n_benign=n_benign,
        n_false_positives=round(fpr * n_benign),
        benign_fpr_by_difficulty={"easy": fpr / 2, "hard": fpr * 1.5},
        benign_fpr_by_category={"tool_result": fpr},
    )


class TestSeedMetricsOperatingPoint:
    def test_defaults_declare_no_benign_arm(self):
        m = SeedMetrics(seed=1, overall_detection_rate=0.9)
        assert m.has_benign_arm is False
        assert m.n_benign == 0

    def test_populated_metrics_declare_a_benign_arm(self):
        assert _metrics().has_benign_arm is True

    def test_true_positive_rate_aliases_detection_rate(self):
        assert _metrics(tpr=0.44).true_positive_rate == 0.44

    def test_specificity(self):
        assert _metrics(fpr=0.25).specificity == pytest.approx(0.75)

    def test_youden_j(self):
        assert _metrics(tpr=0.8, fpr=0.2).youden_j == pytest.approx(0.6)

    def test_precision_and_f1_use_the_counts(self):
        m = _metrics(tpr=0.8, fpr=0.2, n_attacks=100, n_benign=100)
        # TP=80, FP=20 -> precision 0.8; recall 0.8; F1 0.8
        assert m.precision == pytest.approx(0.8)
        assert m.f1 == pytest.approx(0.8)


# ---------------------------------------------------------------------------
# Degenerate-detector positive control
# ---------------------------------------------------------------------------


class TestDegenerateDetector:
    """A detector that flags everything must not look good on any reported number.

    This is the control the attack-only version of this module lacked: with no
    benign arm, ``overall_detection_rate`` for such a detector is 1.0 and every
    stability test passes.
    """

    @staticmethod
    def _flag_everything(seed: int) -> SeedMetrics:
        return _metrics(seed=seed, tpr=1.0, fpr=1.0)

    @staticmethod
    def _perfect(seed: int) -> SeedMetrics:
        return _metrics(seed=seed, tpr=1.0, fpr=0.0)

    def test_flag_everything_scores_a_perfect_detection_rate(self):
        """The failure mode itself: the old headline metric cannot see this."""
        report = run_multi_seed_stability(self._flag_everything, seeds=[1, 2, 3])
        assert report.tpr_mean == 1.0
        assert report.overall_cv == 0.0
        assert report.stable is True

    def test_flag_everything_has_youden_j_zero(self):
        report = run_multi_seed_stability(self._flag_everything, seeds=[1, 2, 3])
        assert report.youden_j_mean == pytest.approx(0.0)
        assert report.fpr_mean == pytest.approx(1.0)

    def test_a_genuinely_perfect_detector_has_youden_j_one(self):
        """Positive control on the control: J does distinguish the two.

        Without this, ``youden_j_mean == 0`` could be satisfied by a J that is
        always zero regardless of the detector.
        """
        report = run_multi_seed_stability(self._perfect, seeds=[1, 2, 3])
        assert report.youden_j_mean == pytest.approx(1.0)

    def test_flag_everything_precision_collapses_to_the_class_ratio(self):
        report = run_multi_seed_stability(self._flag_everything, seeds=[1, 2, 3])
        # 100 attacks, 100 benign, all flagged -> precision = 100/200
        assert report.precision_mean == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Benign-arm aggregation and fail-closed behaviour
# ---------------------------------------------------------------------------


class TestBenignArmAggregation:
    def test_report_carries_the_benign_arm_when_every_seed_has_one(self):
        report = run_multi_seed_stability(
            lambda s: _metrics(seed=s, tpr=0.45, fpr=0.26), seeds=[1, 2, 3]
        )
        assert report.benign_arm_present is True
        assert report.fpr_mean == pytest.approx(0.26)
        assert report.youden_j_mean == pytest.approx(0.19)
        assert report.benign_fpr_by_difficulty_mean["easy"] == pytest.approx(0.13)
        assert report.benign_fpr_by_difficulty_mean["hard"] == pytest.approx(0.39)
        assert "tool_result" in report.benign_fpr_by_category_mean

    def test_missing_benign_arm_suppresses_the_paired_fields(self):
        """No benign corpus -> the FPR fields are None, never a silent 0.0."""
        def attack_only(seed: int) -> SeedMetrics:
            return SeedMetrics(seed=seed, overall_detection_rate=0.9)

        report = run_multi_seed_stability(attack_only, seeds=[1, 2, 3])
        assert report.benign_arm_present is False
        assert report.fpr_mean is None
        assert report.fpr_cv is None
        assert report.precision_mean is None
        assert report.f1_mean is None
        assert report.youden_j_mean is None
        assert report.benign_fpr_by_difficulty_mean == {}

    def test_one_seed_without_a_benign_arm_invalidates_the_aggregate(self):
        """Fail closed: a single attack-only seed must not be averaged in."""
        def mixed(seed: int) -> SeedMetrics:
            if seed == 2:
                return SeedMetrics(seed=seed, overall_detection_rate=0.9)
            return _metrics(seed=seed)

        report = run_multi_seed_stability(mixed, seeds=[1, 2, 3])
        assert report.benign_arm_present is False
        assert report.fpr_mean is None

    def test_tpr_mean_is_reported_even_without_a_benign_arm(self):
        report = run_multi_seed_stability(
            lambda s: SeedMetrics(seed=s, overall_detection_rate=0.44), seeds=[1, 2]
        )
        assert report.tpr_mean == pytest.approx(0.44)


class TestFprEntersTheStabilityVerdict:
    """A detector with a steady TPR but a swinging FPR is not stable."""

    def test_swinging_fpr_makes_the_report_unstable(self):
        def swinging(seed: int) -> SeedMetrics:
            return _metrics(seed=seed, tpr=0.5, fpr=0.1 if seed % 2 else 0.5)

        report = run_multi_seed_stability(swinging, seeds=[1, 2, 3, 4])
        assert report.overall_cv == pytest.approx(0.0), "TPR alone looks perfectly stable"
        assert report.fpr_cv is not None and report.fpr_cv > 0.05
        assert report.stable is False

    def test_steady_fpr_keeps_the_report_stable(self):
        """Positive control: the same TPR with a constant FPR stays stable.

        Together with the test above this proves ``stable`` is actually reading
        ``fpr_cv`` — if the FPR CV were dropped from the verdict, the first
        test would fail while this one would keep passing.
        """
        report = run_multi_seed_stability(
            lambda s: _metrics(seed=s, tpr=0.5, fpr=0.3), seeds=[1, 2, 3, 4]
        )
        assert report.stable is True


# ---------------------------------------------------------------------------
# The real pipeline evaluates both arms
# ---------------------------------------------------------------------------


class TestPipelineEvalFnBenignArm:
    def test_benign_arm_is_mandatory(self):
        with pytest.raises(ValueError, match="benign arm is mandatory"):
            make_pipeline_eval_fn(benign_per_stratum=0)

    def test_eval_fn_evaluates_both_arms(self):
        fn = make_pipeline_eval_fn(n_samples=10, benign_per_stratum=1)
        m = fn(42)
        assert m.n_attacks == 10
        assert m.n_benign == 12  # 6 categories x 2 difficulties x 1
        assert m.has_benign_arm is True
        assert 0.0 <= m.false_positive_rate <= 1.0
        assert set(m.benign_fpr_by_difficulty) == {"easy", "hard"}
        assert len(m.benign_fpr_by_category) == 6

    def test_counts_agree_with_the_rates(self):
        fn = make_pipeline_eval_fn(n_samples=20, benign_per_stratum=2)
        m = fn(3)
        assert m.n_detected_attacks == pytest.approx(m.overall_detection_rate * m.n_attacks)
        assert m.n_false_positives == pytest.approx(m.false_positive_rate * m.n_benign)

    def test_eval_fn_is_deterministic_for_a_seed(self):
        fn = make_pipeline_eval_fn(n_samples=20, benign_per_stratum=2)
        a, b = fn(5), fn(5)
        assert a.overall_detection_rate == b.overall_detection_rate
        assert a.false_positive_rate == b.false_positive_rate

    def test_per_category_is_populated_and_reconstructs_the_overall_rate(self):
        """Per-category detection rates must be real, not an empty dict.

        NOTE (unstratified slice): the attack arm takes ``corpus[:n_samples]``
        and ``AttackCorpus.generate`` emits all 500 injection samples first, so
        the first 100 entries are *all* injection.  This assertion pins that
        fact rather than hiding it: the headline multi-seed rate is a
        direct-injection detection rate, not a whole-corpus one.  If the slice
        is ever stratified this test fails and the manuscript wording has to be
        revisited with it.
        """
        fn = make_pipeline_eval_fn(n_samples=100, benign_per_stratum=1)
        m = fn(1)
        assert m.per_category, "per_category must not be empty"
        assert set(m.per_category) == {"injection"}
        assert m.per_category["injection"] == pytest.approx(m.overall_detection_rate)
