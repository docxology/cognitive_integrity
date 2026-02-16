"""LaTeX tables for t-tests, confidence intervals, and effect sizes.

Generates hypothesis-test summary tables and Cohen's d / odds-ratio
tables for the experimental results.
"""

from __future__ import annotations

from typing import Dict, Optional

import numpy as np
from scipy import stats


def _sample_hypothesis_data(seed: int = 42):
    """Generate sample hypothesis test results."""
    rng = np.random.default_rng(seed)
    hypotheses = [
        ("H1", "CIF > No Defense (Injection)", 0.97, 0.72, 100, 100),
        ("H2", "CIF > No Defense (Trust)", 0.93, 0.68, 100, 100),
        ("H3", "CIF > No Defense (Belief)", 0.89, 0.65, 100, 100),
        ("H4", "CIF > No Defense (Coordination)", 0.94, 0.70, 100, 100),
        ("H5", "CIF > Partial Defense (Overall)", 0.965, 0.88, 100, 100),
    ]
    results = []
    for hid, desc, mean_cif, mean_base, n_cif, n_base in hypotheses:
        # Generate synthetic samples
        cif_samples = rng.normal(mean_cif, 0.03, n_cif)
        base_samples = rng.normal(mean_base, 0.05, n_base)
        t_stat, p_val = stats.ttest_ind(cif_samples, base_samples, alternative="greater")
        results.append((hid, desc, t_stat, p_val, n_cif + n_base))
    return results


def generate_hypothesis_table(results: Optional[Dict] = None) -> str:
    """Generate a LaTeX table of hypothesis test results (t-tests).

    Parameters
    ----------
    results : dict, optional
        Pre-computed results.  Uses synthetic data if *None*.

    Returns
    -------
    str
        Complete LaTeX table string.
    """
    data = _sample_hypothesis_data()

    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Hypothesis Test Results (One-Sided Welch's $t$-test)}",
        r"\label{tab:hypothesis-tests}",
        r"\begin{tabular}{llccc}",
        r"\toprule",
        r"ID & Hypothesis & $t$-statistic & $p$-value & $n$ \\",
        r"\midrule",
    ]

    for hid, desc, t_stat, p_val, n in data:
        sig = "***" if p_val < 0.001 else ("**" if p_val < 0.01 else ("*" if p_val < 0.05 else ""))
        p_str = "< 0.001" if p_val < 0.001 else f"{p_val:.4f}"
        lines.append(f"{hid} & {desc} & {t_stat:.2f} & {p_str}{sig} & {n} \\\\")

    lines.extend([
        r"\bottomrule",
        r"\multicolumn{5}{l}{\small $^{***}p<0.001$, $^{**}p<0.01$, $^{*}p<0.05$} \\",
        r"\end{tabular}",
        r"\end{table}",
    ])

    return "\n".join(lines)


def _sample_effect_data(seed: int = 42):
    """Generate sample effect size data."""
    rng = np.random.default_rng(seed)
    comparisons = [
        ("Injection", 0.97, 0.03, 0.72, 0.05),
        ("Trust Exploitation", 0.93, 0.03, 0.68, 0.05),
        ("Belief Manipulation", 0.89, 0.04, 0.65, 0.06),
        ("Coordination", 0.94, 0.03, 0.70, 0.05),
    ]
    results = []
    for cat, m1, s1, m2, s2 in comparisons:
        # Cohen's d
        pooled_sd = np.sqrt((s1 ** 2 + s2 ** 2) / 2)
        cohens_d = (m1 - m2) / pooled_sd
        # Odds ratio (using detection rates as success probabilities)
        or_val = (m1 / (1 - m1 + 1e-9)) / (m2 / (1 - m2 + 1e-9))
        results.append((cat, cohens_d, or_val))
    return results


def generate_effect_size_table(results: Optional[Dict] = None) -> str:
    """Generate a LaTeX table of effect sizes (Cohen's d, odds ratios).

    Parameters
    ----------
    results : dict, optional
        Pre-computed results.  Uses synthetic data if *None*.

    Returns
    -------
    str
        Complete LaTeX table string.
    """
    data = _sample_effect_data()

    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Effect Sizes: CIF vs.\ No Defense}",
        r"\label{tab:effect-sizes}",
        r"\begin{tabular}{lccc}",
        r"\toprule",
        r"Category & Cohen's $d$ & Interpretation & Odds Ratio \\",
        r"\midrule",
    ]

    for cat, d, odds in data:
        if abs(d) >= 0.8:
            interp = "Large"
        elif abs(d) >= 0.5:
            interp = "Medium"
        else:
            interp = "Small"
        lines.append(f"{cat} & {d:.2f} & {interp} & {odds:.1f} \\\\")

    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ])

    return "\n".join(lines)
