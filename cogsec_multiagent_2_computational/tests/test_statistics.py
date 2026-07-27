"""Comprehensive tests for the statistics package.

Tests all 10 modules: anova, assumptions, confidence, cross_validation,
effect_size, hypothesis, nonparametric, regression, sensitivity, stability.

NO MOCKS. All tests use real data, real computation, deterministic seeds.
"""

import math

# ---------------------------------------------------------------------------
# ANOVA imports
# ---------------------------------------------------------------------------
from statistics.anova import (
    AnovaResult,
    eta_squared,
    partial_eta_squared,
    two_way_anova,
)

# ---------------------------------------------------------------------------
# Assumptions imports
# ---------------------------------------------------------------------------
from statistics.assumptions import (
    AssumptionCheckResult,
    check_parametric_assumptions,
    levene_homogeneity,
    shapiro_wilk_normality,
)

# ---------------------------------------------------------------------------
# Confidence imports
# ---------------------------------------------------------------------------
from statistics.confidence import (
    bootstrap_ci,
    bootstrap_diff_ci,
    bootstrap_mean_ci,
    wilson_ci,
)

# ---------------------------------------------------------------------------
# Cross-validation imports
# ---------------------------------------------------------------------------
from statistics.cross_validation import (
    CrossValidationResult,
    FoldResult,
    run_cross_validation,
    stratified_corpus_folds,
)

# ---------------------------------------------------------------------------
# Effect size imports
# ---------------------------------------------------------------------------
from statistics.effect_size import (
    EffectSizeResult,
    cohens_d,
    cohens_d_ci,
    interpret_cohens_d,
    number_needed_to_treat,
    odds_ratio,
)

# ---------------------------------------------------------------------------
# Hypothesis imports
# Alias the test_h* functions to avoid pytest collecting them as test cases
# ---------------------------------------------------------------------------
from statistics.hypothesis import (
    HypothesisResult,
    bonferroni_correct,
    paired_ttest,
)
from statistics.hypothesis import (
    test_h1_cif_vs_baseline as h1_cif_vs_baseline,
)
from statistics.hypothesis import (
    test_h2_cif_vs_components as h2_cif_vs_components,
)
from statistics.hypothesis import (
    test_h3_per_architecture as h3_per_architecture,
)

# ---------------------------------------------------------------------------
# Nonparametric imports
# ---------------------------------------------------------------------------
from statistics.nonparametric import (
    dunn_posthoc,
    kruskal_wallis,
    mann_whitney_u,
    rank_biserial_correlation,
)

# ---------------------------------------------------------------------------
# Regression imports
# ---------------------------------------------------------------------------
from statistics.regression import (
    RegressionResult,
    fit_linear,
    fit_log_linear,
    fit_quadratic,
    predict,
    r_squared,
)

# ---------------------------------------------------------------------------
# Sensitivity imports
# ---------------------------------------------------------------------------
from statistics.sensitivity import (
    SensitivityResult,
    compute_sensitivity_index,
    grid_search_2d,
    k_fold_cross_validation,
    leave_one_out,
    parameter_sweep,
)

# ---------------------------------------------------------------------------
# Stability imports
# ---------------------------------------------------------------------------
from statistics.stability import (
    SeedMetrics,
    StabilityReport,
    coefficient_of_variation,
    run_multi_seed_stability,
)

import numpy as np
import pytest

# ===========================================================================
# 1. ANOVA TESTS
# ===========================================================================


class TestAnovaEtaSquared:
    """Tests for the eta_squared effect size helper."""

    def test_eta_squared_basic(self):
        """Eta-squared for known SS values."""
        result = eta_squared(25.0, 100.0)
        assert result == pytest.approx(0.25)

    def test_eta_squared_zero_total(self):
        """Returns 0.0 when total SS is zero (no variance)."""
        result = eta_squared(0.0, 0.0)
        assert result == 0.0

    def test_eta_squared_full_variance(self):
        """Effect explains all variance."""
        result = eta_squared(100.0, 100.0)
        assert result == pytest.approx(1.0)

    def test_eta_squared_no_effect(self):
        """Effect explains no variance."""
        result = eta_squared(0.0, 100.0)
        assert result == pytest.approx(0.0)


class TestAnovaPartialEtaSquared:
    """Tests for partial_eta_squared."""

    def test_partial_eta_squared_basic(self):
        """Partial eta-squared for known values."""
        result = partial_eta_squared(30.0, 70.0)
        assert result == pytest.approx(0.3)

    def test_partial_eta_squared_zero_denominator(self):
        """Returns 0.0 when both effect and error are zero."""
        result = partial_eta_squared(0.0, 0.0)
        assert result == 0.0

    def test_partial_eta_squared_large_effect(self):
        """Large effect with small error."""
        result = partial_eta_squared(90.0, 10.0)
        assert result == pytest.approx(0.9)


class TestTwoWayAnova:
    """Tests for two_way_anova with Type I SS decomposition."""

    def test_two_way_anova_balanced_design(self):
        """Two-way ANOVA on a balanced 2x2 design with clear factor effects."""
        rng = np.random.default_rng(42)
        # Factor 1 has 2 levels, factor 2 has 2 levels, 10 replicates each
        a, b, n = 2, 2, 10
        data = np.zeros((a, b, n))

        # Factor 1 effect: level 0 adds 0, level 1 adds 5
        # Factor 2 effect: level 0 adds 0, level 1 adds 3
        for i in range(a):
            for j in range(b):
                base = i * 5.0 + j * 3.0
                data[i, j, :] = base + rng.normal(0, 0.5, n)

        results = two_way_anova(data, factor1_levels=2, factor2_levels=2)

        assert len(results) == 4
        assert results[0].source == "factor1"
        assert results[1].source == "factor2"
        assert results[2].source == "interaction"
        assert results[3].source == "residual"

        # Factor 1 (strong effect) should be highly significant
        assert results[0].p_value < 0.001
        assert results[0].f_statistic > 10.0

        # Factor 2 (moderate effect) should be significant
        assert results[1].p_value < 0.001
        assert results[1].f_statistic > 5.0

        # No interaction designed, so p should be high
        assert results[2].p_value > 0.01

    def test_two_way_anova_with_interaction(self):
        """Two-way ANOVA with an explicit interaction effect."""
        rng = np.random.default_rng(99)
        a, b, n = 2, 2, 20
        data = np.zeros((a, b, n))

        # Add a strong interaction: only cell (1,1) has a large value
        for i in range(a):
            for j in range(b):
                if i == 1 and j == 1:
                    data[i, j, :] = 10.0 + rng.normal(0, 0.3, n)
                else:
                    data[i, j, :] = 1.0 + rng.normal(0, 0.3, n)

        results = two_way_anova(data, factor1_levels=2, factor2_levels=2)

        # Interaction should be significant
        assert results[2].p_value < 0.001
        assert results[2].f_statistic > 10.0

    def test_two_way_anova_result_structure(self):
        """Result objects have correct types and fields."""
        rng = np.random.default_rng(7)
        data = rng.normal(5.0, 1.0, (3, 2, 5))

        results = two_way_anova(data, factor1_levels=3, factor2_levels=2)

        for r in results:
            assert isinstance(r, AnovaResult)
            assert isinstance(r.source, str)
            assert isinstance(r.ss, float)
            assert isinstance(r.df, int)
            assert isinstance(r.ms, float)
            assert isinstance(r.f_statistic, float)
            assert isinstance(r.p_value, float)
            assert r.ss >= 0.0
            assert r.df >= 0

    def test_two_way_anova_ss_decomposition(self):
        """Sum of squares components add up to total SS."""
        rng = np.random.default_rng(123)
        data = rng.normal(0, 1, (3, 4, 8))

        results = two_way_anova(data, factor1_levels=3, factor2_levels=4)

        ss_total_computed = np.sum((data - data.mean()) ** 2)
        ss_sum = sum(r.ss for r in results)

        assert ss_sum == pytest.approx(ss_total_computed, rel=1e-10)

    def test_two_way_anova_degrees_of_freedom(self):
        """Degrees of freedom are computed correctly."""
        a, b, n = 3, 4, 5
        rng = np.random.default_rng(10)
        data = rng.normal(0, 1, (a, b, n))

        results = two_way_anova(data, factor1_levels=a, factor2_levels=b)

        assert results[0].df == a - 1  # factor1: 2
        assert results[1].df == b - 1  # factor2: 3
        assert results[2].df == (a - 1) * (b - 1)  # interaction: 6
        assert results[3].df == a * b * (n - 1)  # residual: 48

    def test_two_way_anova_invalid_shape(self):
        """Raises ValueError for non-3D data."""
        with pytest.raises(ValueError, match="3-D"):
            two_way_anova(np.ones((3, 4)), factor1_levels=3, factor2_levels=4)

    def test_two_way_anova_shape_mismatch(self):
        """Raises ValueError when shape does not match declared levels."""
        data = np.ones((2, 3, 5))
        with pytest.raises(ValueError, match="Shape mismatch"):
            two_way_anova(data, factor1_levels=3, factor2_levels=3)

    def test_two_way_anova_residual_row(self):
        """Residual row has f_statistic=0 and p_value=1."""
        rng = np.random.default_rng(55)
        data = rng.normal(0, 1, (2, 2, 5))
        results = two_way_anova(data, factor1_levels=2, factor2_levels=2)
        assert results[3].f_statistic == 0.0
        assert results[3].p_value == 1.0

    def test_two_way_anova_no_within_cell_variance(self):
        """When all replicates in every cell are identical, residual SS is zero."""
        data = np.zeros((2, 2, 3))
        data[0, 0, :] = 1.0
        data[0, 1, :] = 2.0
        data[1, 0, :] = 3.0
        data[1, 1, :] = 4.0

        results = two_way_anova(data, factor1_levels=2, factor2_levels=2)
        assert results[3].ss == pytest.approx(0.0, abs=1e-12)


# ===========================================================================
# 2. ASSUMPTIONS TESTS
# ===========================================================================


class TestShapiroWilkNormality:
    """Tests for shapiro_wilk_normality."""

    def test_normal_data_passes(self):
        """Data drawn from a normal distribution should pass the test."""
        rng = np.random.default_rng(42)
        data = rng.normal(0, 1, 50)

        result = shapiro_wilk_normality(data, group_name="test_group")

        assert isinstance(result, AssumptionCheckResult)
        assert result.test_name == "Shapiro-Wilk"
        assert result.group_name == "test_group"
        assert bool(result.passed) is True
        assert result.p_value > 0.05

    def test_uniform_data_fails(self):
        """Data from a uniform distribution should fail the normality test."""
        rng = np.random.default_rng(42)
        data = rng.uniform(0, 1, 100)

        result = shapiro_wilk_normality(data, group_name="uniform")

        assert bool(result.passed) is False
        assert result.p_value < 0.05

    def test_too_few_samples(self):
        """Fewer than 3 samples returns NaN and passes=False."""
        data = np.array([1.0, 2.0])
        result = shapiro_wilk_normality(data)

        assert math.isnan(result.statistic)
        assert math.isnan(result.p_value)
        assert result.passed is False

    def test_custom_alpha(self):
        """Custom alpha level is respected.

        The Shapiro-Wilk test has H0: data is normal. The ``passed`` field
        is ``p >= alpha``. A strict alpha (low value like 0.01) makes it
        easier to "pass" (keep H0), while a lenient alpha (high value
        like 0.99) makes it harder to "pass" because you would need
        p >= 0.99.
        """
        rng = np.random.default_rng(42)
        data = rng.normal(0, 1, 30)

        result_strict = shapiro_wilk_normality(data, alpha=0.01)
        result_lenient = shapiro_wilk_normality(data, alpha=0.10)

        assert result_strict.alpha == 0.01
        assert result_lenient.alpha == 0.10
        # Normal data with strict alpha should easily pass
        assert bool(result_strict.passed) is True
        # Normal data with moderately lenient alpha should also pass
        assert bool(result_lenient.passed) is True


class TestLeveneHomogeneity:
    """Tests for levene_homogeneity."""

    def test_equal_variance_passes(self):
        """Groups with similar variance pass Levene's test."""
        rng = np.random.default_rng(42)
        g1 = rng.normal(0, 1.0, 50)
        g2 = rng.normal(5, 1.0, 50)

        result = levene_homogeneity(g1, g2)

        assert isinstance(result, AssumptionCheckResult)
        assert result.test_name == "Levene"
        assert bool(result.passed) is True
        assert result.p_value > 0.05

    def test_unequal_variance_fails(self):
        """Groups with very different variances fail Levene's test."""
        rng = np.random.default_rng(42)
        g1 = rng.normal(0, 1.0, 100)
        g2 = rng.normal(0, 10.0, 100)

        result = levene_homogeneity(g1, g2)

        assert bool(result.passed) is False
        assert result.p_value < 0.05

    def test_single_group_returns_nan(self):
        """Fewer than 2 groups returns NaN and passed=False."""
        g1 = np.array([1.0, 2.0, 3.0])
        result = levene_homogeneity(g1)

        assert math.isnan(result.statistic)
        assert result.passed is False

    def test_three_groups(self):
        """Levene's test with three groups of equal variance."""
        rng = np.random.default_rng(42)
        g1 = rng.normal(0, 1.0, 40)
        g2 = rng.normal(3, 1.0, 40)
        g3 = rng.normal(6, 1.0, 40)

        result = levene_homogeneity(g1, g2, g3)
        assert bool(result.passed) is True


class TestCheckParametricAssumptions:
    """Tests for check_parametric_assumptions (combined check)."""

    def test_normal_equal_variance_all_met(self):
        """Normal data with equal variance satisfies all assumptions."""
        rng = np.random.default_rng(42)
        g1 = rng.normal(10, 2, 50)
        g2 = rng.normal(12, 2, 50)

        results, all_met = check_parametric_assumptions(g1, g2)

        assert len(results) == 3
        assert all_met is True
        assert results[0].test_name == "Shapiro-Wilk"
        assert results[1].test_name == "Shapiro-Wilk"
        assert results[2].test_name == "Levene"

    def test_non_normal_data_fails(self):
        """Highly skewed data fails the normality check."""
        rng = np.random.default_rng(42)
        # Exponential is non-normal
        g1 = rng.exponential(1.0, 100)
        g2 = rng.normal(0, 1, 100)

        results, all_met = check_parametric_assumptions(g1, g2)
        assert all_met is False

    def test_custom_alpha_propagated(self):
        """Alpha value is propagated to all sub-tests."""
        rng = np.random.default_rng(42)
        g1 = rng.normal(0, 1, 30)
        g2 = rng.normal(0, 1, 30)

        results, _ = check_parametric_assumptions(g1, g2, alpha=0.01)
        for r in results:
            assert r.alpha == 0.01


# ===========================================================================
# 3. CONFIDENCE INTERVAL TESTS
# ===========================================================================


class TestWilsonCI:
    """Tests for wilson_ci (Wilson score confidence interval)."""

    def test_basic_proportion(self):
        """Basic proportion CI for 80/100 successes."""
        prop, lower, upper = wilson_ci(80, 100, confidence=0.95)

        assert prop == pytest.approx(0.8)
        assert lower < 0.8
        assert upper > 0.8
        assert lower > 0.0
        assert upper < 1.0
        # CI should contain the true proportion
        assert lower < 0.8 < upper

    def test_perfect_proportion(self):
        """100% success rate."""
        prop, lower, upper = wilson_ci(100, 100)

        assert prop == pytest.approx(1.0)
        assert upper == pytest.approx(1.0)
        assert lower < 1.0  # lower bound should be < 1

    def test_zero_proportion(self):
        """0% success rate."""
        prop, lower, upper = wilson_ci(0, 100)

        assert prop == pytest.approx(0.0)
        assert lower == pytest.approx(0.0)
        assert upper > 0.0

    def test_single_trial(self):
        """Single trial, one success."""
        prop, lower, upper = wilson_ci(1, 1)
        assert prop == pytest.approx(1.0)
        assert 0.0 <= lower <= upper <= 1.0

    def test_invalid_total(self):
        """Raises ValueError for total < 1."""
        with pytest.raises(ValueError, match="total must be >= 1"):
            wilson_ci(0, 0)

    def test_successes_out_of_range(self):
        """Raises ValueError if successes > total."""
        with pytest.raises(ValueError, match="successes must be in"):
            wilson_ci(5, 3)

    def test_wider_ci_at_lower_confidence(self):
        """Higher confidence produces wider intervals."""
        _, low_90, high_90 = wilson_ci(50, 100, confidence=0.90)
        _, low_99, high_99 = wilson_ci(50, 100, confidence=0.99)

        width_90 = high_90 - low_90
        width_99 = high_99 - low_99
        assert width_99 > width_90


class TestBootstrapCI:
    """Tests for bootstrap_ci and bootstrap_mean_ci."""

    def test_bootstrap_ci_mean(self):
        """Bootstrap CI for the mean of normal data contains the true mean."""
        rng = np.random.default_rng(42)
        data = rng.normal(5.0, 1.0, 200)

        point, lower, upper = bootstrap_ci(
            data, statistic_fn=lambda x: float(np.mean(x)),
            n_bootstrap=5000, confidence=0.95, seed=42,
        )

        assert lower < 5.0 < upper
        assert point == pytest.approx(np.mean(data))

    def test_bootstrap_mean_ci_convenience(self):
        """bootstrap_mean_ci produces consistent results with bootstrap_ci."""
        rng = np.random.default_rng(42)
        data = rng.normal(10.0, 2.0, 100)

        point, lower, upper = bootstrap_mean_ci(
            data, n_bootstrap=5000, seed=42,
        )

        assert lower < upper
        assert lower < point < upper
        assert abs(point - np.mean(data)) < 1e-10

    def test_bootstrap_ci_median(self):
        """Bootstrap CI for the median."""
        rng = np.random.default_rng(42)
        data = rng.normal(3.0, 0.5, 150)

        point, lower, upper = bootstrap_ci(
            data, statistic_fn=lambda x: float(np.median(x)),
            n_bootstrap=5000, seed=42,
        )

        assert lower < 3.0 < upper

    def test_bootstrap_ci_deterministic(self):
        """Same seed produces identical results."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])

        r1 = bootstrap_ci(data, lambda x: float(np.mean(x)), seed=99)
        r2 = bootstrap_ci(data, lambda x: float(np.mean(x)), seed=99)

        assert r1 == r2


class TestBootstrapDiffCI:
    """Tests for bootstrap_diff_ci."""

    def test_diff_ci_detects_difference(self):
        """Detects a genuine difference in means."""
        rng = np.random.default_rng(42)
        x = rng.normal(10.0, 1.0, 100)
        y = rng.normal(5.0, 1.0, 100)

        diff, lower, upper = bootstrap_diff_ci(x, y, n_bootstrap=5000, seed=42)

        # True difference is 5.0; CI should be entirely positive
        assert lower > 0.0
        assert diff > 0.0
        assert diff == pytest.approx(np.mean(x) - np.mean(y))

    def test_diff_ci_no_difference(self):
        """No significant difference when samples are from the same population."""
        rng = np.random.default_rng(42)
        x = rng.normal(0.0, 1.0, 100)
        y = rng.normal(0.0, 1.0, 100)

        diff, lower, upper = bootstrap_diff_ci(x, y, n_bootstrap=5000, seed=42)

        # CI should contain zero
        assert lower < 0.0 < upper


# ===========================================================================
# 4. CROSS-VALIDATION TESTS
# ===========================================================================


class TestStratifiedCorpusFolds:
    """Tests for stratified_corpus_folds."""

    def _make_corpus(self, n_per_category=20):
        """Create a simple labeled corpus for testing."""
        samples = []
        for i in range(n_per_category):
            samples.append({
                "category": "cat_a",
                "is_attack": True,
                "content": f"attack_a_{i}",
            })
        for i in range(n_per_category):
            samples.append({
                "category": "cat_b",
                "is_attack": False,
                "content": f"benign_b_{i}",
            })
        return samples

    def test_fold_count(self):
        """Correct number of folds produced."""
        samples = self._make_corpus(20)
        folds = stratified_corpus_folds(samples, k=5, seed=42)
        assert len(folds) == 5

    def test_all_samples_covered(self):
        """Every sample appears in exactly one test fold."""
        samples = self._make_corpus(20)
        folds = stratified_corpus_folds(samples, k=5, seed=42)

        test_contents = []
        for _, test in folds:
            test_contents.extend(s["content"] for s in test)

        all_contents = [s["content"] for s in samples]
        assert sorted(test_contents) == sorted(all_contents)

    def test_train_test_disjoint(self):
        """Train and test sets within a fold share no samples."""
        samples = self._make_corpus(20)
        folds = stratified_corpus_folds(samples, k=5, seed=42)

        for train, test in folds:
            train_contents = {s["content"] for s in train}
            test_contents = {s["content"] for s in test}
            assert train_contents.isdisjoint(test_contents)

    def test_deterministic(self):
        """Same seed produces identical folds."""
        samples = self._make_corpus(20)
        f1 = stratified_corpus_folds(samples, k=3, seed=42)
        f2 = stratified_corpus_folds(samples, k=3, seed=42)

        for (train1, test1), (train2, test2) in zip(f1, f2):
            assert [s["content"] for s in test1] == [s["content"] for s in test2]


class TestRunCrossValidation:
    """Tests for run_cross_validation."""

    def _make_corpus(self):
        """Create a corpus with clear attack/benign distinction."""
        samples = []
        for i in range(30):
            samples.append({
                "category": "injection",
                "is_attack": True,
                "content": f"attack_{i}",
            })
        for i in range(30):
            samples.append({
                "category": "benign",
                "is_attack": False,
                "content": f"benign_{i}",
            })
        return samples

    def test_perfect_detector(self):
        """A perfect detector yields TPR=1.0 and FPR=0.0."""
        samples = self._make_corpus()

        def perfect_eval(content):
            is_attack = content.startswith("attack")
            return (is_attack, 1.0 if is_attack else 0.0)

        result = run_cross_validation(samples, perfect_eval, k=5, seed=42)

        assert isinstance(result, CrossValidationResult)
        assert result.k == 5
        assert len(result.fold_results) == 5
        assert result.mean_tpr == pytest.approx(1.0)
        assert result.mean_fpr == pytest.approx(0.0)
        assert result.mean_f1 == pytest.approx(1.0)

    def test_random_detector(self):
        """A random detector yields metrics between 0 and 1."""
        samples = self._make_corpus()
        rng = np.random.default_rng(42)

        def random_eval(content):
            return (rng.random() > 0.5, rng.random())

        result = run_cross_validation(samples, random_eval, k=5, seed=42)

        for fr in result.fold_results:
            assert 0.0 <= fr.tpr <= 1.0
            assert 0.0 <= fr.fpr <= 1.0
            assert 0.0 <= fr.f1 <= 1.0

    def test_fold_result_structure(self):
        """FoldResult objects have correct types."""
        samples = self._make_corpus()

        def dummy_eval(content):
            return (True, 0.5)

        result = run_cross_validation(samples, dummy_eval, k=3, seed=42)

        for fr in result.fold_results:
            assert isinstance(fr, FoldResult)
            assert isinstance(fr.fold, int)
            assert isinstance(fr.n_samples, int)
            assert fr.n_samples > 0


# ===========================================================================
# 5. EFFECT SIZE TESTS
# ===========================================================================


class TestInterpretCohensD:
    """Tests for interpret_cohens_d thresholds."""

    def test_negligible(self):
        assert interpret_cohens_d(0.1) == "negligible"
        assert interpret_cohens_d(-0.1) == "negligible"
        assert interpret_cohens_d(0.0) == "negligible"

    def test_small(self):
        assert interpret_cohens_d(0.3) == "small"
        assert interpret_cohens_d(-0.3) == "small"

    def test_medium(self):
        assert interpret_cohens_d(0.6) == "medium"
        assert interpret_cohens_d(-0.6) == "medium"

    def test_large(self):
        assert interpret_cohens_d(0.9) == "large"
        assert interpret_cohens_d(-0.9) == "large"

    def test_very_large(self):
        assert interpret_cohens_d(1.5) == "very large"
        assert interpret_cohens_d(-2.0) == "very large"
        assert interpret_cohens_d(4.2) == "very large"

    def test_boundary_values(self):
        """Test exact boundary values."""
        assert interpret_cohens_d(0.2) == "small"
        assert interpret_cohens_d(0.5) == "medium"
        assert interpret_cohens_d(0.8) == "large"
        assert interpret_cohens_d(1.2) == "very large"


class TestCohensD:
    """Tests for cohens_d computation."""

    def test_large_effect(self):
        """Two well-separated groups produce a large Cohen's d."""
        rng = np.random.default_rng(42)
        g1 = rng.normal(10.0, 1.0, 50)
        g2 = rng.normal(5.0, 1.0, 50)

        result = cohens_d(g1, g2)

        assert isinstance(result, EffectSizeResult)
        assert result.measure == "Cohen's d"
        assert result.value > 3.0  # Very large effect
        assert result.interpretation == "very large"
        assert result.ci_lower < result.value < result.ci_upper

    def test_no_effect(self):
        """Samples from the same population produce a near-zero d."""
        rng = np.random.default_rng(42)
        g1 = rng.normal(0, 1, 100)
        g2 = rng.normal(0, 1, 100)

        result = cohens_d(g1, g2)

        assert abs(result.value) < 0.5  # Should be negligible or small
        # CI should contain zero
        assert result.ci_lower < 0.0 < result.ci_upper

    def test_negative_effect(self):
        """Group 1 lower than group 2 gives negative d."""
        rng = np.random.default_rng(42)
        g1 = rng.normal(0, 1, 50)
        g2 = rng.normal(5, 1, 50)

        result = cohens_d(g1, g2)
        assert result.value < -3.0

    def test_too_few_observations(self):
        """Raises ValueError with fewer than 2 observations."""
        with pytest.raises(ValueError, match="at least 2"):
            cohens_d(np.array([1.0]), np.array([2.0, 3.0]))

    def test_identical_groups(self):
        """Identical constant groups produce d=0."""
        g1 = np.array([5.0, 5.0, 5.0, 5.0])
        g2 = np.array([5.0, 5.0, 5.0, 5.0])

        result = cohens_d(g1, g2)
        assert result.value == 0.0


class TestCohensDCI:
    """Tests for cohens_d_ci."""

    def test_ci_contains_point_estimate(self):
        """CI contains the point estimate."""
        lower, upper = cohens_d_ci(1.0, 30, 30, ci=0.95)
        assert lower < 1.0 < upper

    def test_wider_ci_with_higher_confidence(self):
        """99% CI is wider than 95% CI."""
        low95, high95 = cohens_d_ci(0.5, 50, 50, ci=0.95)
        low99, high99 = cohens_d_ci(0.5, 50, 50, ci=0.99)

        assert (high99 - low99) > (high95 - low95)

    def test_narrower_ci_with_larger_sample(self):
        """Larger samples produce narrower CIs."""
        low_small, high_small = cohens_d_ci(1.0, 10, 10)
        low_large, high_large = cohens_d_ci(1.0, 200, 200)

        assert (high_large - low_large) < (high_small - low_small)


class TestOddsRatio:
    """Tests for odds_ratio."""

    def test_strong_association(self):
        """High TP and TN with low FP and FN produces a strong OR."""
        result = odds_ratio(tp=90, fp=5, fn=10, tn=95)

        assert isinstance(result, EffectSizeResult)
        assert result.measure == "odds ratio"
        assert result.value > 3.0
        assert result.interpretation == "strong association"
        assert result.ci_lower < result.value < result.ci_upper

    def test_no_association(self):
        """Equal distribution yields OR near 1."""
        result = odds_ratio(tp=25, fp=25, fn=25, tn=25)

        assert result.value == pytest.approx(1.0)

    def test_continuity_correction(self):
        """Zero cells trigger the 0.5 continuity correction."""
        # tp=0 triggers correction
        result = odds_ratio(tp=0, fp=10, fn=5, tn=85)

        assert result.value > 0  # Should still compute
        assert result.ci_lower < result.ci_upper

    def test_inverse_association(self):
        """Low TP and high FP/FN yields OR < 1."""
        result = odds_ratio(tp=5, fp=45, fn=45, tn=5)
        assert result.value < 1.0
        assert result.interpretation == "inverse association"


class TestNumberNeededToTreat:
    """Tests for number_needed_to_treat."""

    def test_basic_nnt(self):
        """NNT for a treatment that improves detection from 0.5 to 0.9."""
        nnt = number_needed_to_treat(0.5, 0.9)
        assert nnt == pytest.approx(1.0 / 0.4)
        assert nnt == pytest.approx(2.5)

    def test_equal_rates(self):
        """Equal rates yield infinite NNT."""
        nnt = number_needed_to_treat(0.5, 0.5)
        assert nnt == float("inf")

    def test_perfect_improvement(self):
        """0% to 100% improvement gives NNT=1."""
        nnt = number_needed_to_treat(0.0, 1.0)
        assert nnt == pytest.approx(1.0)

    def test_negative_nnt(self):
        """Treatment worse than control gives negative NNT."""
        nnt = number_needed_to_treat(0.8, 0.5)
        assert nnt < 0


# ===========================================================================
# 6. HYPOTHESIS TESTS
# ===========================================================================


class TestPairedTTest:
    """Tests for paired_ttest."""

    def test_significant_difference(self):
        """Paired t-test detects a clear difference."""
        rng = np.random.default_rng(42)
        x = rng.normal(10, 1, 30)
        y = rng.normal(5, 1, 30)

        t_stat, p_val = paired_ttest(x, y, alternative="greater")

        assert t_stat > 0
        assert p_val < 0.001

    def test_no_difference(self):
        """Paired t-test on nearly identical data yields non-significant result."""
        # Note: Exactly identical arrays yield NaN from scipy's ttest_rel
        # (zero variance in differences), so we use near-identical data.
        rng = np.random.default_rng(42)
        base = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
        noise = rng.normal(0, 0.001, len(base))
        t_stat, p_val = paired_ttest(base, base + noise, alternative="two-sided")

        # With negligible noise, p-value should be high (non-significant)
        assert p_val > 0.05

    def test_shape_mismatch(self):
        """Raises ValueError for different-length arrays."""
        with pytest.raises(ValueError, match="same shape"):
            paired_ttest(np.array([1, 2, 3]), np.array([1, 2]))

    def test_too_few_observations(self):
        """Raises ValueError with fewer than 2 observations."""
        with pytest.raises(ValueError, match="at least 2"):
            paired_ttest(np.array([1.0]), np.array([2.0]))

    def test_two_sided(self):
        """Two-sided test catches difference in either direction."""
        rng = np.random.default_rng(42)
        x = rng.normal(0, 1, 30)
        y = rng.normal(3, 1, 30)

        t_stat, p_val = paired_ttest(x, y, alternative="two-sided")
        assert p_val < 0.001


class TestBonferroniCorrect:
    """Tests for bonferroni_correct."""

    def test_single_comparison(self):
        """Single comparison: same as uncorrected."""
        result = bonferroni_correct([0.01], alpha=0.05)
        assert result == [True]

    def test_multiple_comparisons(self):
        """With 5 comparisons, alpha/5 = 0.01."""
        p_values = [0.005, 0.02, 0.008, 0.04, 0.001]
        result = bonferroni_correct(p_values, alpha=0.05)

        # Only p < 0.01 should be significant
        assert result == [True, False, True, False, True]

    def test_empty_list(self):
        """Empty p-value list returns empty list."""
        assert bonferroni_correct([]) == []

    def test_all_significant(self):
        """All p-values below corrected threshold."""
        p_values = [0.001, 0.002, 0.003]
        result = bonferroni_correct(p_values, alpha=0.05)
        # Corrected alpha = 0.05/3 ~ 0.0167
        assert all(result)

    def test_none_significant(self):
        """All p-values above corrected threshold."""
        p_values = [0.5, 0.6, 0.7]
        result = bonferroni_correct(p_values, alpha=0.05)
        assert not any(result)


class TestH1CIFvsBaseline:
    """Tests for test_h1_cif_vs_baseline."""

    def test_cif_better_than_baseline(self):
        """H1 is supported when CIF scores are higher."""
        rng = np.random.default_rng(42)
        cif = rng.normal(0.95, 0.02, 30)
        baseline = rng.normal(0.60, 0.05, 30)

        result = h1_cif_vs_baseline(cif, baseline)

        assert isinstance(result, HypothesisResult)
        assert result.name == "H1"
        assert result.significant is True
        assert result.p_value < 0.001
        assert result.method == "paired t-test (one-sided, greater)"

    def test_cif_equal_to_baseline(self):
        """H1 is not supported when CIF and baseline are similar."""
        rng = np.random.default_rng(42)
        # Same distribution, slight noise -- should not be significant
        base = rng.normal(0.6, 0.05, 30)
        similar = rng.normal(0.6, 0.05, 30)
        result = h1_cif_vs_baseline(base, similar)

        assert result.significant is False


class TestH2CIFvsComponents:
    """Tests for test_h2_cif_vs_components."""

    def test_cif_beats_all_components(self):
        """CIF outperforms every individual component."""
        rng = np.random.default_rng(42)
        cif = rng.normal(0.95, 0.02, 30)

        components = {
            "firewall": rng.normal(0.70, 0.05, 30),
            "tripwire": rng.normal(0.65, 0.05, 30),
            "consensus": rng.normal(0.60, 0.05, 30),
        }

        results = h2_cif_vs_components(cif, components)

        assert len(results) == 3
        for r in results:
            assert r.significant is True
            assert "H2_" in r.name
            assert "Bonferroni" in r.method

    def test_cif_loses_to_one_component(self):
        """When CIF is worse than a component, that test is not significant."""
        rng = np.random.default_rng(42)
        cif = rng.normal(0.70, 0.02, 30)

        components = {
            "strong_component": rng.normal(0.95, 0.02, 30),
            "weak_component": rng.normal(0.40, 0.05, 30),
        }

        results = h2_cif_vs_components(cif, components)

        # strong_component should not be significant (CIF is worse)
        strong_result = [r for r in results if "strong_component" in r.name][0]
        assert strong_result.significant is False

        # weak_component should be significant (CIF is better)
        weak_result = [r for r in results if "weak_component" in r.name][0]
        assert weak_result.significant is True


class TestH3PerArchitecture:
    """Tests for test_h3_per_architecture."""

    def test_cif_superior_all_architectures(self):
        """CIF is superior across all architectures."""
        rng = np.random.default_rng(42)

        arch_results = {}
        for arch in ["transformer", "rnn", "cnn"]:
            cif = rng.normal(0.95, 0.02, 20)
            baseline = rng.normal(0.60, 0.05, 20)
            arch_results[arch] = (cif, baseline)

        results = h3_per_architecture(arch_results)

        assert len(results) == 3
        for r in results:
            assert r.significant is True
            assert "H3_" in r.name

    def test_single_architecture(self):
        """Works with a single architecture."""
        rng = np.random.default_rng(42)
        cif = rng.normal(0.90, 0.02, 15)
        baseline = rng.normal(0.50, 0.05, 15)

        results = h3_per_architecture({"single_arch": (cif, baseline)})

        assert len(results) == 1
        assert results[0].name == "H3_single_arch"


# ===========================================================================
# 7. NONPARAMETRIC TESTS
# ===========================================================================


class TestKruskalWallis:
    """Tests for kruskal_wallis."""

    def test_different_groups_significant(self):
        """Kruskal-Wallis detects differences between distinct groups."""
        rng = np.random.default_rng(42)
        g1 = rng.normal(0, 1, 30)
        g2 = rng.normal(3, 1, 30)
        g3 = rng.normal(6, 1, 30)

        result = kruskal_wallis(g1, g2, g3)

        assert isinstance(result, HypothesisResult)
        assert result.name == "Kruskal-Wallis"
        assert result.significant is True
        assert result.p_value < 0.05
        assert result.test_statistic > 0

    def test_same_distribution_not_significant(self):
        """Groups from the same distribution are not significantly different."""
        rng = np.random.default_rng(42)
        g1 = rng.normal(0, 1, 30)
        g2 = rng.normal(0, 1, 30)
        g3 = rng.normal(0, 1, 30)

        result = kruskal_wallis(g1, g2, g3)

        assert result.significant is False
        assert result.p_value > 0.05

    def test_too_few_groups(self):
        """Raises ValueError with fewer than 2 groups."""
        with pytest.raises(ValueError, match="at least 2"):
            kruskal_wallis(np.array([1, 2, 3]))

    def test_two_groups(self):
        """Works with exactly 2 groups."""
        rng = np.random.default_rng(42)
        g1 = rng.normal(0, 1, 20)
        g2 = rng.normal(5, 1, 20)

        result = kruskal_wallis(g1, g2)
        assert result.significant is True

    def test_kruskal_wallis_multi_group_scenario(self):
        """Test Kruskal-Wallis with 6 groups of different means."""
        rng = np.random.default_rng(42)
        groups = [
            rng.normal(0.90, 0.05, 20),
            rng.normal(0.85, 0.05, 20),
            rng.normal(0.80, 0.05, 20),
            rng.normal(0.75, 0.05, 20),
            rng.normal(0.70, 0.05, 20),
            rng.normal(0.60, 0.05, 20),
        ]
        result = kruskal_wallis(*groups)
        assert result.significant is True
        # H statistic should be substantial for 6 groups with spread
        assert result.test_statistic > 20.0


class TestMannWhitneyU:
    """Tests for mann_whitney_u."""

    def test_significant_difference(self):
        """Mann-Whitney detects a clear difference."""
        rng = np.random.default_rng(42)
        x = rng.normal(10, 1, 30)
        y = rng.normal(5, 1, 30)

        result = mann_whitney_u(x, y, alternative="greater")

        assert result.significant is True
        assert result.p_value < 0.05

    def test_no_difference(self):
        """Samples from identical distributions are not significant."""
        rng = np.random.default_rng(42)
        x = rng.normal(0, 1, 30)
        y = rng.normal(0, 1, 30)

        result = mann_whitney_u(x, y, alternative="two-sided")

        assert result.significant is False

    def test_two_sided_alternative(self):
        """Two-sided test detects difference regardless of direction."""
        rng = np.random.default_rng(42)
        x = rng.normal(0, 1, 30)
        y = rng.normal(5, 1, 30)

        result = mann_whitney_u(x, y, alternative="two-sided")
        assert result.significant is True

    def test_result_structure(self):
        """Result has correct HypothesisResult fields."""
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y = np.array([6.0, 7.0, 8.0, 9.0, 10.0])

        result = mann_whitney_u(x, y)
        assert isinstance(result, HypothesisResult)
        assert result.name == "Mann-Whitney U"
        assert "Mann-Whitney" in result.method


class TestRankBiserialCorrelation:
    """Tests for rank_biserial_correlation."""

    def test_perfect_separation(self):
        """Perfectly separated groups yield r near +/- 1."""
        x = np.array([10.0, 11.0, 12.0, 13.0, 14.0])
        y = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        r = rank_biserial_correlation(x, y)

        # x is entirely greater than y, so r should be near -1
        # (because U for x vs y when x > y gives U near n1*n2)
        assert abs(r) > 0.8

    def test_overlapping_groups(self):
        """Overlapping groups yield moderate r."""
        rng = np.random.default_rng(42)
        x = rng.normal(3, 1, 30)
        y = rng.normal(3, 1, 30)

        r = rank_biserial_correlation(x, y)
        assert -0.5 < r < 0.5

    def test_range_bounds(self):
        """Result is bounded in [-1, 1]."""
        rng = np.random.default_rng(42)
        x = rng.normal(0, 1, 20)
        y = rng.normal(0, 1, 20)

        r = rank_biserial_correlation(x, y)
        assert -1.0 <= r <= 1.0


class TestDunnPosthoc:
    """Tests for dunn_posthoc."""

    def test_pairwise_comparisons_returned(self):
        """Returns a p-value for each pair of groups."""
        rng = np.random.default_rng(42)
        groups = [
            rng.normal(0, 1, 20),
            rng.normal(3, 1, 20),
            rng.normal(6, 1, 20),
        ]

        result = dunn_posthoc(groups, p_value_kruskal=0.001)

        # 3 groups => 3 pairs
        assert len(result) == 3
        assert (0, 1) in result
        assert (0, 2) in result
        assert (1, 2) in result

    def test_all_p_values_bounded(self):
        """All corrected p-values are in [0, 1]."""
        rng = np.random.default_rng(42)
        groups = [
            rng.normal(0, 1, 20),
            rng.normal(1, 1, 20),
            rng.normal(2, 1, 20),
            rng.normal(3, 1, 20),
        ]

        result = dunn_posthoc(groups, p_value_kruskal=0.01)

        for key, p_val in result.items():
            assert 0.0 <= p_val <= 1.0

    def test_widely_separated_groups(self):
        """Widely separated groups have very small corrected p-values."""
        groups = [
            np.array([1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9]),
            np.array([50.0, 50.1, 50.2, 50.3, 50.4, 50.5, 50.6, 50.7, 50.8, 50.9]),
        ]

        result = dunn_posthoc(groups, p_value_kruskal=0.001)
        assert result[(0, 1)] < 0.05

    def test_fewer_than_two_groups(self):
        """Returns empty dict for fewer than 2 groups."""
        result = dunn_posthoc([np.array([1, 2, 3])], p_value_kruskal=0.5)
        assert result == {}


# ===========================================================================
# 8. REGRESSION TESTS
# ===========================================================================


class TestRSquared:
    """Tests for r_squared."""

    def test_perfect_fit(self):
        """R^2 = 1 for perfect predictions."""
        y = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        assert r_squared(y, y) == pytest.approx(1.0)

    def test_constant_prediction(self):
        """R^2 = 0 when predicting the mean."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.full_like(y_true, np.mean(y_true))
        assert r_squared(y_true, y_pred) == pytest.approx(0.0)

    def test_poor_model_negative(self):
        """R^2 can be negative for a terrible model."""
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([10.0, 20.0, 30.0])
        assert r_squared(y_true, y_pred) < 0.0

    def test_constant_true_values(self):
        """When all true values are constant, R^2 = 1 if predictions match."""
        y_true = np.array([5.0, 5.0, 5.0])
        y_pred = np.array([5.0, 5.0, 5.0])
        assert r_squared(y_true, y_pred) == pytest.approx(1.0)

    def test_constant_true_with_error(self):
        """When all true values are constant but predictions differ, R^2 = 0."""
        y_true = np.array([5.0, 5.0, 5.0])
        y_pred = np.array([4.0, 5.0, 6.0])
        assert r_squared(y_true, y_pred) == pytest.approx(0.0)


class TestFitLinear:
    """Tests for fit_linear."""

    def test_perfect_linear_data(self):
        """Recovers exact coefficients from noiseless linear data."""
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y = 2.0 * x + 3.0  # y = 3 + 2x

        result = fit_linear(x, y)

        assert isinstance(result, RegressionResult)
        assert result.model_name == "linear (y = b0 + b1*x)"
        assert result.r_squared == pytest.approx(1.0, abs=1e-10)
        # coefficients are [b1, b0] = [2.0, 3.0]
        assert result.coefficients[0] == pytest.approx(2.0, abs=1e-10)
        assert result.coefficients[1] == pytest.approx(3.0, abs=1e-10)

    def test_noisy_linear_data(self):
        """Good R^2 for data with small noise."""
        rng = np.random.default_rng(42)
        x = np.linspace(0, 10, 50)
        y = 1.5 * x + 2.0 + rng.normal(0, 0.5, 50)

        result = fit_linear(x, y)
        assert result.r_squared > 0.95

    def test_prediction_function(self):
        """prediction_fn produces correct predictions."""
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y = 3.0 * x + 1.0

        result = fit_linear(x, y)
        predictions = predict(result, np.array([6.0, 7.0]))

        assert predictions[0] == pytest.approx(19.0, abs=1e-8)
        assert predictions[1] == pytest.approx(22.0, abs=1e-8)

    def test_residuals(self):
        """Residuals are y_true - y_pred."""
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([2.0, 4.0, 6.0])  # perfect linear

        result = fit_linear(x, y)
        assert np.allclose(result.residuals, 0.0, atol=1e-10)


class TestFitQuadratic:
    """Tests for fit_quadratic."""

    def test_perfect_quadratic_data(self):
        """Recovers exact coefficients from noiseless quadratic data."""
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y = 0.5 * x**2 + 2.0 * x + 1.0

        result = fit_quadratic(x, y)

        assert result.r_squared == pytest.approx(1.0, abs=1e-8)
        # coefficients: [b2, b1, b0] = [0.5, 2.0, 1.0]
        assert result.coefficients[0] == pytest.approx(0.5, abs=1e-8)
        assert result.coefficients[1] == pytest.approx(2.0, abs=1e-8)
        assert result.coefficients[2] == pytest.approx(1.0, abs=1e-8)

    def test_quadratic_better_than_linear(self):
        """Quadratic fit has higher R^2 than linear on quadratic data."""
        rng = np.random.default_rng(42)
        x = np.linspace(1, 10, 30)
        y = 2.0 * x**2 + 3.0 * x + 1.0 + rng.normal(0, 2.0, 30)

        linear_result = fit_linear(x, y)
        quad_result = fit_quadratic(x, y)

        assert quad_result.r_squared > linear_result.r_squared

    def test_high_r_squared_scaling(self):
        """Quadratic fit achieves high R^2 for scaling-like data."""
        # Simulate latency T = 0.1n^2 + 0.5n + 10 (as in the manuscript target)
        x = np.array([1, 2, 4, 8, 16, 32, 64], dtype=float)
        y = 0.1 * x**2 + 0.5 * x + 10.0

        result = fit_quadratic(x, y)
        assert result.r_squared > 0.99


class TestFitLogLinear:
    """Tests for fit_log_linear."""

    def test_perfect_log_linear_data(self):
        """Recovers coefficients from noiseless log-linear data."""
        x = np.array([1.0, 2.0, 5.0, 10.0, 20.0])
        # T = 3.0 + 2.0 * log(x)
        y = 3.0 + 2.0 * np.log(x)

        result = fit_log_linear(x, y)

        assert result.r_squared == pytest.approx(1.0, abs=1e-6)
        assert result.coefficients[0] == pytest.approx(3.0, abs=1e-4)
        assert result.coefficients[1] == pytest.approx(2.0, abs=1e-4)

    def test_invalid_x_values(self):
        """Raises ValueError for non-positive x values."""
        with pytest.raises(ValueError, match="positive"):
            fit_log_linear(np.array([0.0, 1.0, 2.0]), np.array([1.0, 2.0, 3.0]))

        with pytest.raises(ValueError, match="positive"):
            fit_log_linear(np.array([-1.0, 1.0, 2.0]), np.array([1.0, 2.0, 3.0]))

    def test_prediction_from_log_linear(self):
        """Log-linear model makes correct predictions."""
        x = np.array([1.0, 2.0, 4.0, 8.0, 16.0])
        y = 1.0 + 3.0 * np.log(x)

        result = fit_log_linear(x, y)
        pred = predict(result, np.array([32.0]))

        expected = 1.0 + 3.0 * np.log(32.0)
        assert pred[0] == pytest.approx(expected, abs=0.1)


class TestPredict:
    """Tests for the predict helper."""

    def test_predict_linear(self):
        """Predict on a linear model."""
        x = np.array([1.0, 2.0, 3.0, 4.0])
        y = 5.0 * x + 10.0

        model = fit_linear(x, y)
        preds = predict(model, np.array([5.0, 10.0]))

        assert preds[0] == pytest.approx(35.0, abs=1e-8)
        assert preds[1] == pytest.approx(60.0, abs=1e-8)


# ===========================================================================
# 9. SENSITIVITY ANALYSIS TESTS
# ===========================================================================


class TestParameterSweep:
    """Tests for parameter_sweep."""

    def test_basic_sweep(self):
        """Finds the maximum of a simple quadratic."""
        # f(x) = -(x-3)^2 + 9  => max at x=3 with value 9
        param_range = np.linspace(0, 6, 100)
        result = parameter_sweep(
            "threshold", param_range,
            evaluate_fn=lambda x: -(x - 3.0) ** 2 + 9.0,
        )

        assert isinstance(result, SensitivityResult)
        assert result.parameter_name == "threshold"
        assert result.best_value == pytest.approx(3.0, abs=0.1)
        assert result.best_metric == pytest.approx(9.0, abs=0.1)
        assert len(result.values) == 100
        assert len(result.metric_values) == 100

    def test_monotonic_function(self):
        """Best value is at the end of the range for a monotonic function."""
        param_range = np.linspace(0, 10, 50)
        result = parameter_sweep(
            "window_size", param_range,
            evaluate_fn=lambda x: x,
        )

        assert result.best_value == pytest.approx(10.0, abs=0.3)

    def test_sweep_values_match(self):
        """All parameter values and metrics are recorded."""
        param_range = np.array([1.0, 2.0, 3.0])
        result = parameter_sweep(
            "param", param_range,
            evaluate_fn=lambda x: x * 2,
        )

        np.testing.assert_array_equal(result.values, param_range)
        np.testing.assert_array_almost_equal(result.metric_values, [2.0, 4.0, 6.0])


class TestGridSearch2D:
    """Tests for grid_search_2d."""

    def test_basic_grid_search(self):
        """Finds the optimal combination on a 2D surface."""
        p1_range = np.linspace(0, 5, 20)
        p2_range = np.linspace(0, 5, 20)

        # Maximum at (3, 2): f = -(p1-3)^2 - (p2-2)^2 + 13
        result = grid_search_2d(
            "threshold", p1_range,
            "window", p2_range,
            evaluate_fn=lambda p1, p2: -(p1 - 3.0)**2 - (p2 - 2.0)**2 + 13.0,
        )

        assert result["param1_name"] == "threshold"
        assert result["param2_name"] == "window"
        assert result["best_params"]["threshold"] == pytest.approx(3.0, abs=0.5)
        assert result["best_params"]["window"] == pytest.approx(2.0, abs=0.5)
        assert result["best_metric"] == pytest.approx(13.0, abs=0.5)

    def test_grid_size(self):
        """Grid contains n1 * n2 entries."""
        p1 = np.array([1.0, 2.0, 3.0])
        p2 = np.array([10.0, 20.0])

        result = grid_search_2d(
            "a", p1, "b", p2,
            evaluate_fn=lambda a, b: a + b,
        )

        assert len(result["grid"]) == 6


class TestKFoldCrossValidation:
    """Tests for k_fold_cross_validation from the sensitivity module."""

    def test_basic_k_fold(self):
        """Returns k fold metrics."""
        rng = np.random.default_rng(42)
        data = rng.normal(0, 1, (100, 3))
        labels = np.array([0] * 50 + [1] * 50)

        fold_metrics = k_fold_cross_validation(data, labels, k=5, seed=42)

        assert len(fold_metrics) == 5
        for m in fold_metrics:
            assert isinstance(m, float)
            assert 0.0 <= m <= 1.0

    def test_custom_evaluator(self):
        """Custom evaluator is used instead of default."""
        data = np.array([[1], [2], [3], [4], [5], [6], [7], [8], [9], [10]], dtype=float)
        labels = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])

        def custom_eval(train_d, train_l, test_d, test_l):
            # Simple: return mean of test labels
            return float(np.mean(test_l))

        fold_metrics = k_fold_cross_validation(
            data, labels, k=5, evaluate_fn=custom_eval, seed=42,
        )

        assert len(fold_metrics) == 5

    def test_k_too_small(self):
        """Raises ValueError when k < 2."""
        with pytest.raises(ValueError, match="k must be >= 2"):
            k_fold_cross_validation(
                np.array([[1], [2]]), np.array([0, 1]), k=1,
            )

    def test_k_exceeds_samples(self):
        """Raises ValueError when k > n_samples."""
        with pytest.raises(ValueError, match="exceeds"):
            k_fold_cross_validation(
                np.array([[1], [2], [3]]), np.array([0, 1, 0]), k=5,
            )

    def test_deterministic(self):
        """Same seed produces identical fold metrics."""
        rng = np.random.default_rng(42)
        data = rng.normal(0, 1, (50, 2))
        labels = np.array([0] * 25 + [1] * 25)

        r1 = k_fold_cross_validation(data, labels, k=5, seed=42)
        r2 = k_fold_cross_validation(data, labels, k=5, seed=42)

        assert r1 == r2


class TestLeaveOneOut:
    """Tests for leave_one_out."""

    def test_basic_loo(self):
        """Returns n metrics for n samples."""
        data = np.array([[1.0], [2.0], [3.0], [4.0], [5.0]])
        labels = np.array([0, 0, 1, 1, 1])

        def eval_fn(train_d, train_l, test_d, test_l):
            # Predict majority class of training set
            majority = int(np.mean(train_l) >= 0.5)
            return float(test_l[0] == majority)

        metrics = leave_one_out(data, labels, eval_fn)

        assert len(metrics) == 5
        for m in metrics:
            assert m in (0.0, 1.0)  # Accuracy per single sample

    def test_loo_single_element_test(self):
        """Each fold has exactly 1 test sample and n-1 train samples."""
        n = 8
        data = np.arange(n).reshape(-1, 1).astype(float)
        labels = np.array([0, 0, 0, 0, 1, 1, 1, 1])

        train_sizes = []
        test_sizes = []

        def tracking_eval(train_d, train_l, test_d, test_l):
            train_sizes.append(len(train_d))
            test_sizes.append(len(test_d))
            return 1.0

        leave_one_out(data, labels, tracking_eval)

        assert all(ts == n - 1 for ts in train_sizes)
        assert all(ts == 1 for ts in test_sizes)


class TestComputeSensitivityIndex:
    """Tests for compute_sensitivity_index."""

    def test_ranking_by_influence(self):
        """Parameters are ranked by metric range (descending)."""
        results = [
            SensitivityResult(
                "threshold",
                np.array([0.1, 0.5, 0.9]),
                np.array([0.5, 0.8, 0.6]),  # range = 0.3
                best_value=0.5,
                best_metric=0.8,
            ),
            SensitivityResult(
                "window",
                np.array([1, 5, 10]),
                np.array([0.7, 0.71, 0.72]),  # range = 0.02
                best_value=10,
                best_metric=0.72,
            ),
            SensitivityResult(
                "decay",
                np.array([0.9, 0.95, 0.99]),
                np.array([0.4, 0.9, 0.5]),  # range = 0.5
                best_value=0.95,
                best_metric=0.9,
            ),
        ]

        index = compute_sensitivity_index(results)

        keys = list(index.keys())
        assert keys[0] == "decay"      # range 0.5
        assert keys[1] == "threshold"  # range 0.3
        assert keys[2] == "window"     # range 0.02

        assert index["decay"] == pytest.approx(0.5)
        assert index["threshold"] == pytest.approx(0.3)
        assert index["window"] == pytest.approx(0.02)

    def test_empty_results(self):
        """Empty results list returns empty index."""
        index = compute_sensitivity_index([])
        assert index == {}


# ===========================================================================
# 10. STABILITY TESTS
# ===========================================================================


class TestCoefficientOfVariation:
    """Tests for coefficient_of_variation."""

    def test_zero_mean(self):
        """Returns 0.0 when mean is zero."""
        assert coefficient_of_variation(np.array([0.0, 0.0, 0.0])) == 0.0

    def test_no_variation(self):
        """CV is 0 when all values are identical."""
        assert coefficient_of_variation(np.array([5.0, 5.0, 5.0])) == 0.0

    def test_known_cv(self):
        """CV = std/mean for known data."""
        values = np.array([10.0, 20.0, 30.0])
        expected_cv = np.std(values) / np.mean(values)
        assert coefficient_of_variation(values) == pytest.approx(expected_cv)

    def test_negative_values(self):
        """Works with negative mean (uses abs)."""
        values = np.array([-10.0, -20.0, -30.0])
        result = coefficient_of_variation(values)
        assert result > 0


class TestRunMultiSeedStability:
    """Tests for run_multi_seed_stability."""

    def test_stable_pipeline(self):
        """A deterministic pipeline is stable across seeds."""
        def deterministic_eval(seed):
            return SeedMetrics(
                seed=seed,
                overall_detection_rate=0.95,
                per_architecture={"transformer": 0.96, "rnn": 0.94},
                per_category={"injection": 0.97, "evasion": 0.93},
            )

        report = run_multi_seed_stability(
            deterministic_eval,
            seeds=[1, 2, 3, 4, 5],
            cv_threshold=0.05,
        )

        assert isinstance(report, StabilityReport)
        assert report.n_seeds == 5
        assert report.overall_cv == 0.0
        assert report.stable is True
        assert len(report.seed_metrics) == 5

    def test_unstable_pipeline(self):
        """A noisy pipeline is flagged as unstable."""
        np.random.default_rng(42)

        def noisy_eval(seed):
            # Deliberately noisy: CV > 5%
            local_rng = np.random.default_rng(seed)
            rate = local_rng.uniform(0.3, 0.9)
            return SeedMetrics(
                seed=seed,
                overall_detection_rate=rate,
                per_architecture={"arch_a": rate * 0.9},
                per_category={"cat_x": rate * 1.1},
            )

        report = run_multi_seed_stability(
            noisy_eval,
            seeds=list(range(1, 31)),
            cv_threshold=0.05,
        )

        assert report.stable is False
        assert report.overall_cv > 0.05

    def test_default_seeds(self):
        """Default seeds are range(1, 31) = 30 seeds."""
        call_count = 0

        def counting_eval(seed):
            nonlocal call_count
            call_count += 1
            return SeedMetrics(seed=seed, overall_detection_rate=0.9)

        report = run_multi_seed_stability(counting_eval)

        assert call_count == 30
        assert report.n_seeds == 30

    def test_per_architecture_cv(self):
        """Per-architecture CV is computed correctly."""
        def arch_eval(seed):
            local_rng = np.random.default_rng(seed)
            return SeedMetrics(
                seed=seed,
                overall_detection_rate=0.9,
                per_architecture={
                    "stable_arch": 0.95,  # No variation
                    "noisy_arch": 0.5 + local_rng.uniform(-0.3, 0.3),
                },
            )

        report = run_multi_seed_stability(
            arch_eval, seeds=list(range(1, 21)), cv_threshold=0.05,
        )

        assert report.per_architecture_cv["stable_arch"] == pytest.approx(0.0)
        assert report.per_architecture_cv["noisy_arch"] > 0.0

    def test_per_category_cv(self):
        """Per-category CV is computed correctly."""
        def cat_eval(seed):
            return SeedMetrics(
                seed=seed,
                overall_detection_rate=0.9,
                per_category={"injection": 0.95, "evasion": 0.85},
            )

        report = run_multi_seed_stability(
            cat_eval, seeds=[1, 2, 3], cv_threshold=0.05,
        )

        assert "injection" in report.per_category_cv
        assert "evasion" in report.per_category_cv
        assert report.per_category_cv["injection"] == pytest.approx(0.0)

    def test_stability_threshold(self):
        """Custom cv_threshold is stored and used."""
        def stable_eval(seed):
            return SeedMetrics(seed=seed, overall_detection_rate=0.9)

        report = run_multi_seed_stability(
            stable_eval, seeds=[1, 2], cv_threshold=0.10,
        )

        assert report.cv_threshold == 0.10


# ===========================================================================
# INTEGRATION: Cross-module usage patterns
# ===========================================================================


class TestCrossModuleIntegration:
    """Tests that verify modules work together as expected."""

    def test_anova_with_eta_squared(self):
        """Use ANOVA results to compute eta-squared effect sizes."""
        rng = np.random.default_rng(42)
        data = np.zeros((2, 3, 15))
        for i in range(2):
            for j in range(3):
                data[i, j, :] = i * 5.0 + j * 2.0 + rng.normal(0, 1, 15)

        results = two_way_anova(data, 2, 3)
        ss_total = sum(r.ss for r in results)

        for r in results[:3]:  # factor1, factor2, interaction
            es = eta_squared(r.ss, ss_total)
            assert 0.0 <= es <= 1.0

    def test_hypothesis_then_effect_size(self):
        """Run H1, then compute Cohen's d on the same data."""
        rng = np.random.default_rng(42)
        cif = rng.normal(0.95, 0.02, 30)
        baseline = rng.normal(0.60, 0.05, 30)

        h1_result = h1_cif_vs_baseline(cif, baseline)
        assert h1_result.significant is True

        effect = cohens_d(cif, baseline)
        assert effect.interpretation == "very large"

    def test_assumptions_guide_test_choice(self):
        """Check assumptions, then choose parametric or nonparametric test."""
        rng = np.random.default_rng(42)

        # Normal data -> parametric is appropriate
        g1 = rng.normal(5, 1, 50)
        g2 = rng.normal(8, 1, 50)

        _, all_met = check_parametric_assumptions(g1, g2)
        assert all_met is True

        # Use parametric (paired t-test)
        t_stat, p_val = paired_ttest(g1, g2, alternative="two-sided")
        assert p_val < 0.001

        # Also verify nonparametric gives consistent result direction
        mw_result = mann_whitney_u(g1, g2, alternative="two-sided")
        assert mw_result.significant is True

    def test_sensitivity_with_regression(self):
        """Sweep a parameter, then fit regression to the sweep curve."""
        param_range = np.linspace(0.1, 10.0, 50)
        sweep = parameter_sweep(
            "alpha", param_range,
            evaluate_fn=lambda x: 1.0 / (1.0 + np.exp(-x + 5)),
        )

        # Fit a regression to the sweep curve
        result = fit_quadratic(sweep.values, sweep.metric_values)
        # Quadratic should fit a sigmoid reasonably (not perfectly)
        assert result.r_squared > 0.8

    def test_cross_validation_with_stability(self):
        """Run k-fold inside a stability evaluation."""
        data = np.random.default_rng(42).normal(0, 1, (100, 3))
        labels = np.array([0] * 50 + [1] * 50)

        def stability_eval(seed):
            fold_metrics = k_fold_cross_validation(
                data, labels, k=5, seed=seed,
            )
            avg_metric = float(np.mean(fold_metrics))
            return SeedMetrics(
                seed=seed,
                overall_detection_rate=avg_metric,
            )

        report = run_multi_seed_stability(
            stability_eval,
            seeds=[1, 2, 3, 4, 5],
            cv_threshold=0.20,
        )

        assert report.n_seeds == 5
        # The default evaluator (majority class) should be relatively stable
        assert report.overall_cv < 0.50

    def test_bootstrap_diff_ci_with_effect_size(self):
        """Bootstrap difference CI corroborates Cohen's d direction."""
        rng = np.random.default_rng(42)
        g1 = rng.normal(10, 1, 50)
        g2 = rng.normal(7, 1, 50)

        # Cohen's d should show a very large positive effect
        effect = cohens_d(g1, g2)
        assert effect.value > 1.0  # Very large
        assert effect.interpretation == "very large"

        # Bootstrap difference CI should also be entirely positive
        diff, lower, upper = bootstrap_diff_ci(g1, g2, n_bootstrap=5000, seed=42)

        assert lower > 0  # Effect is genuinely positive
        assert lower < diff < upper
        # Both methods agree on the direction of the effect
        assert (effect.value > 0) == (diff > 0)
