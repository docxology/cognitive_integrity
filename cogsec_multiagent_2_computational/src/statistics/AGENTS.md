# Statistics Package - Agent Reference

Hypothesis testing, effect sizes, and confidence intervals.

## Modules

### hypothesis.py

Hypothesis testing framework.

**Key Functions:**

- `t_test()` - Two-sample t-test
- `wilcoxon_test()` - Non-parametric test
- `permutation_test()` - Permutation-based test

### effect_size.py

Effect size computation.

**Key Functions:**

- `cohens_d()` - Cohen's d
- `hedges_g()` - Hedges' g
- `cliffs_delta()` - Cliff's delta

### confidence.py

Confidence interval estimation.

**Key Functions:**

- `wilson_ci()` - Wilson score interval
- `bootstrap_ci()` - Bootstrap CI
- `bootstrap_mean_ci()` - Bootstrap CI on the mean
- `bootstrap_diff_ci()` - Bootstrap CI on a difference

(No `t_ci()` exists; the manuscript's small-sample intervals come from the
bootstrap machinery above, not a Student-t shortcut.)

### anova.py

Analysis of variance.

**Key Functions:**

- `one_way_anova()` - One-way ANOVA
- `two_way_anova()` - Two-way ANOVA

### nonparametric.py

Non-parametric tests.

### regression.py

Regression analysis.

### sensitivity.py

Sensitivity analysis.

### stability.py

Result stability analysis.

### assumptions.py

Statistical assumption checks.

### cross_validation.py

Cross-validation utilities.

## Usage

```python
from src.statistics import cohens_d, bootstrap_ci, t_test

d = cohens_d(group1, group2)
ci = bootstrap_ci(data, n_bootstrap=1000)
p_value = t_test(group1, group2)
```
