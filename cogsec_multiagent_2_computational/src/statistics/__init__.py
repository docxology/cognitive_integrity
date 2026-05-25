"""Statistical analysis package for the Cognitive Security Framework.
from __future__ import annotations


Re-exports all public classes and functions from:
- hypothesis: H1/H2/H3 hypothesis tests
- effect_size: Cohen's d, odds ratios, NNT
- confidence: Wilson score, bootstrap CIs
- nonparametric: Kruskal-Wallis, Mann-Whitney U
- regression: Linear, quadratic, log-linear fits
- anova: Two-way ANOVA
- sensitivity: Parameter sweeps, cross-validation
"""

# Hypothesis testing
# ANOVA
from .anova import (
    AnovaResult,
    eta_squared,
    partial_eta_squared,
    two_way_anova,
)

# Assumption tests
from .assumptions import (
    AssumptionCheckResult,
    check_parametric_assumptions,
    levene_homogeneity,
    shapiro_wilk_normality,
)

# Confidence intervals
from .confidence import (
    bootstrap_ci,
    bootstrap_diff_ci,
    bootstrap_mean_ci,
    wilson_ci,
)

# Cross-validation
from .cross_validation import (
    CrossValidationResult,
    FoldResult,
    run_cross_validation,
    stratified_corpus_folds,
)

# Effect sizes
from .effect_size import (
    EffectSizeResult,
    cohens_d,
    cohens_d_ci,
    interpret_cohens_d,
    number_needed_to_treat,
    odds_ratio,
)
from .hypothesis import (
    HypothesisResult,
    bonferroni_correct,
    paired_ttest,
    test_h1_cif_vs_baseline,
    test_h2_cif_vs_components,
    test_h3_per_architecture,
)

# Non-parametric tests
from .nonparametric import (
    dunn_posthoc,
    kruskal_wallis,
    mann_whitney_u,
    rank_biserial_correlation,
)

# Regression
from .regression import (
    RegressionResult,
    fit_linear,
    fit_log_linear,
    fit_quadratic,
    predict,
    r_squared,
)

# Sensitivity analysis
from .sensitivity import (
    SensitivityResult,
    compute_sensitivity_index,
    grid_search_2d,
    k_fold_cross_validation,
    leave_one_out,
    parameter_sweep,
)

# Stability analysis
from .stability import (
    SeedMetrics,
    StabilityReport,
    coefficient_of_variation,
    run_multi_seed_stability,
)

# Convenience alias
hypothesis_test = paired_ttest

__all__ = [
    # Hypothesis
    "HypothesisResult", "paired_ttest", "bonferroni_correct",
    "test_h1_cif_vs_baseline", "test_h2_cif_vs_components",
    "test_h3_per_architecture",
    # Effect size
    "EffectSizeResult", "cohens_d", "cohens_d_ci", "interpret_cohens_d",
    "odds_ratio", "number_needed_to_treat",
    # Confidence
    "wilson_ci", "bootstrap_ci", "bootstrap_mean_ci", "bootstrap_diff_ci",
    # Non-parametric
    "kruskal_wallis", "mann_whitney_u", "rank_biserial_correlation",
    "dunn_posthoc",
    # Regression
    "RegressionResult", "fit_linear", "fit_quadratic", "fit_log_linear",
    "r_squared", "predict",
    # ANOVA
    "AnovaResult", "two_way_anova", "eta_squared", "partial_eta_squared",
    # Sensitivity
    "SensitivityResult", "parameter_sweep", "grid_search_2d",
    "k_fold_cross_validation", "leave_one_out", "compute_sensitivity_index",
    # Assumptions
    "AssumptionCheckResult", "shapiro_wilk_normality", "levene_homogeneity",
    "check_parametric_assumptions",
    # Cross-validation
    "FoldResult", "CrossValidationResult", "stratified_corpus_folds",
    "run_cross_validation",
    # Stability
    "SeedMetrics", "StabilityReport", "coefficient_of_variation",
    "run_multi_seed_stability",
    # Convenience alias
    "hypothesis_test",
]
