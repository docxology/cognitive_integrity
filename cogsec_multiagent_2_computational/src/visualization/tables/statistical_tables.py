"""LaTeX tables for t-tests, confidence intervals, and effect sizes.

Generates hypothesis-test summary tables and Cohen's d / odds-ratio
tables.  Reads data from statistical_results.json.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def _load_statistical_results():
    """Load statistical results from statistical_results.json."""
    p = Path(__file__).resolve().parent.parent.parent.parent / "output" / "data" / "statistical_results.json"  # noqa: E501
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    logger.info("Loaded statistical results from %s", p)
    return data


def generate_hypothesis_table(results: Optional[Dict] = None) -> str:
    """Generate a LaTeX table of hypothesis test results.

    Parameters
    ----------
    results : dict, optional
        Pre-computed results.  Loaded from output data if *None*.

    Returns
    -------
    str
        Complete LaTeX table string.
    """
    data = _load_statistical_results()

    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Hypothesis Test Results (One-Sided Welch's $t$-test)}",
        r"\label{tab:hypothesis-tests}",
        r"\begin{tabular}{llccc}",
        r"\toprule",
        r"ID & Hypothesis & $t$-statistic & $p$-value & Significant \\",
        r"\midrule",
    ]

    # H1
    h1 = data.get("h1", {})
    p_val = h1.get("p_value", 0)
    sig = "Yes" if h1.get("significant", False) else "No"
    p_str = "< 0.001" if p_val < 0.001 else f"{p_val:.4f}"
    lines.append(f"H1 & CIF > Baseline & {h1.get('statistic', 0):.2f} & {p_str} & {sig} \\\\")

    # H2 results
    for i, h2 in enumerate(data.get("h2", []), start=2):
        p_val = h2.get("p_value", 0)
        sig = "Yes" if h2.get("significant", False) else "No"
        p_str = "< 0.001" if p_val < 0.001 else f"{p_val:.4f}"
        lines.append(f"H{i} & CIF > {h2.get('name', 'Component')} & -- & {p_str} & {sig} \\\\")

    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ])

    return "\n".join(lines)


def generate_effect_size_table(results: Optional[Dict] = None) -> str:
    """Generate a LaTeX table of effect sizes.

    Parameters
    ----------
    results : dict, optional
        Pre-computed results.  Loaded from output data if *None*.

    Returns
    -------
    str
        Complete LaTeX table string.
    """
    data = _load_statistical_results()
    d_val = data.get("cohens_d_cif_vs_baseline", 0.0)

    if abs(d_val) >= 0.8:
        interp = "Large"
    elif abs(d_val) >= 0.5:
        interp = "Medium"
    else:
        interp = "Small"

    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Effect Sizes: CIF vs.\ No Defense}",
        r"\label{tab:effect-sizes}",
        r"\begin{tabular}{lccc}",
        r"\toprule",
        r"Comparison & Cohen's $d$ & Interpretation & Odds Ratio \\",
        r"\midrule",
        f"CIF vs Baseline & {d_val:.2f} & {interp} & -- \\\\",
    ]

    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ])

    return "\n".join(lines)
