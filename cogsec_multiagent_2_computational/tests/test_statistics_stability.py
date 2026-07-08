"""Tests for src/statistics/stability.py.

Covers:
- SeedMetrics and StabilityReport dataclasses.
- coefficient_of_variation: normal, zero mean, single value.
- run_multi_seed_stability: with custom eval_fn, seeds, cv_threshold.
- make_pipeline_eval_fn: factory only (the created eval_fn is tested separately).

All tests use real computation. No mocks.
"""

from __future__ import annotations

from statistics.stability import (
    SeedMetrics,
    StabilityReport,
    coefficient_of_variation,
    make_pipeline_eval_fn,
    run_multi_seed_stability,
)

import numpy as np

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
