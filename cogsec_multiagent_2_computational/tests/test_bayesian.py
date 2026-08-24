"""Tests for Beta-Binomial Bayesian analysis.

Covers:
- Closed-form posterior moments against analytical values.
- Credible intervals and HDI bracketing.
- Sampler reproducibility and Beta-shape moments.
- Bayes factor behaviour for clearly different vs identical proportions.
- Power analysis returns a finite sample size for realistic CI widths.
- Calibration metrics (ECE, Brier) on perfect and miscalibrated predictors.

NO MOCKS. All tests use analytical values or real computations.
"""

from __future__ import annotations

# ``statistics`` here is this project's ``src/statistics`` package, which
# pytest puts on sys.path via ``pythonpath = ["src"]``.  Importing it as
# ``src.statistics`` instead loads a *second*, distinct copy of the same
# module -- ``src.statistics.bayesian`` and ``statistics.bayesian`` end up as
# separate objects with separate ``BetaPosterior`` classes, so an isinstance
# check across the boundary silently fails.  Every other statistics import in
# the repo uses the bare form; this one is kept in line with it.
from statistics.bayesian import (
    BetaPosterior,
    CalibrationResult,
    bayes_factor_two_proportions,
    beta_binomial_posterior,
    calibration_analysis,
    power_analysis_beta_binomial,
)

import numpy as np
import pytest
from scipy import stats


def test_posterior_mean_matches_analytical():
    """Beta(2, 2) has mean 0.5; general formula a/(a+b)."""
    post = beta_binomial_posterior(successes=5, trials=10)  # Beta(6, 6)
    assert post.alpha == pytest.approx(6.0)
    assert post.beta_ == pytest.approx(6.0)
    assert post.mean() == pytest.approx(0.5)


def test_posterior_mode_interior():
    """Beta(6, 6) mode at (a-1)/(a+b-2) = 5/10 = 0.5."""
    post = beta_binomial_posterior(successes=5, trials=10)
    assert post.mode() == pytest.approx(0.5)


def test_posterior_mode_boundary():
    """Beta(1, 5) has boundary mode at 0 (alpha <= 1 branch)."""
    post = BetaPosterior(alpha=1.0, beta_=5.0)
    assert post.mode() == 0.0


def test_credible_interval_contains_mean():
    """95% equal-tailed CI brackets the posterior mean."""
    post = beta_binomial_posterior(successes=80, trials=100)
    lo, hi = post.credible_interval(width=0.95)
    mean = post.mean()
    assert lo < mean < hi
    # Independent verification against scipy.
    exp_lo = float(stats.beta.ppf(0.025, post.alpha, post.beta_))
    exp_hi = float(stats.beta.ppf(0.975, post.alpha, post.beta_))
    assert lo == pytest.approx(exp_lo, rel=1e-9)
    assert hi == pytest.approx(exp_hi, rel=1e-9)


def test_hdi_shorter_than_equal_tailed():
    """For a skewed posterior the HDI is no wider than the equal-tailed CI."""
    # Beta(2, 20) is strongly right-skewed, so HDI should be narrower.
    post = BetaPosterior(alpha=2.0, beta_=20.0)
    ci_lo, ci_hi = post.credible_interval(width=0.95)
    hdi_lo, hdi_hi = post.hdi(width=0.95)
    assert (hdi_hi - hdi_lo) <= (ci_hi - ci_lo) + 1e-8


def test_sampler_mean_close_to_posterior_mean():
    """Sampled mean approaches analytical mean under law of large numbers."""
    post = beta_binomial_posterior(successes=50, trials=100)
    samples = post.sample(n=50_000, seed=42)
    assert samples.shape == (50_000,)
    assert np.all(samples >= 0.0)
    assert np.all(samples <= 1.0)
    assert samples.mean() == pytest.approx(post.mean(), abs=0.005)


def test_bayes_factor_strongly_different_proportions():
    """80/100 vs 20/100 favours H1 (different rates) overwhelmingly."""
    bf = bayes_factor_two_proportions(n1=100, k1=80, n2=100, k2=20)
    assert bf > 1000.0, f"BF10 should be >> 1, got {bf}"


def test_bayes_factor_identical_proportions_favours_h0():
    """Identical data favours H0 (same rate) -- BF10 < 1."""
    bf = bayes_factor_two_proportions(n1=100, k1=50, n2=100, k2=50)
    assert bf < 1.0, f"BF10 should be < 1 for identical data, got {bf}"


def test_bayes_factor_rejects_invalid_counts():
    """Negative or oversized counts raise ValueError."""
    with pytest.raises(ValueError):
        bayes_factor_two_proportions(n1=10, k1=20, n2=10, k2=5)


def test_power_analysis_realistic_regime():
    """0.8 true rate with ±5% target CI half-width needs > 200 samples."""
    result = power_analysis_beta_binomial(true_rate=0.8, desired_ci_half_width=0.05)
    assert result["n_required"] > 200
    assert result["actual_half_width_at_n"] <= 0.05
    assert 0.75 <= result["posterior_mean_at_n"] <= 0.85


def test_power_analysis_rejects_out_of_range_rate():
    """true_rate outside (0, 1) is rejected."""
    with pytest.raises(ValueError):
        power_analysis_beta_binomial(true_rate=1.5)


def test_calibration_perfect_predictor_low_ece():
    """A perfectly calibrated predictor has near-zero ECE and Brier."""
    # 1000 predictions: half at 0.1 (positive 10% of the time), half at 0.9
    # (positive 90% of the time) -- perfectly calibrated.
    rng = np.random.default_rng(0)
    probs = np.concatenate([np.full(500, 0.1), np.full(500, 0.9)])
    outcomes = np.concatenate([
        rng.binomial(1, 0.1, size=500),
        rng.binomial(1, 0.9, size=500),
    ]).astype(float)
    cal = calibration_analysis(probs, outcomes, n_bins=10)
    assert isinstance(cal, CalibrationResult)
    assert cal.ece < 0.05
    # Brier score for a calibrated 0.1/0.9 predictor is 0.1*0.9 = 0.09
    assert 0.05 < cal.brier_score < 0.15


def test_calibration_miscalibrated_predictor_high_ece():
    """A wildly miscalibrated predictor has notably higher ECE."""
    rng = np.random.default_rng(0)
    # Predict 0.9 when truth is 10% positive.
    probs = np.full(1000, 0.9)
    outcomes = rng.binomial(1, 0.1, size=1000).astype(float)
    cal = calibration_analysis(probs, outcomes, n_bins=10)
    assert cal.ece > 0.5
    assert cal.brier_score > 0.5


def test_calibration_rejects_mismatched_shapes():
    """Shape mismatch between probs and outcomes is rejected."""
    with pytest.raises(ValueError):
        calibration_analysis(np.array([0.1, 0.2]), np.array([0.0]))
