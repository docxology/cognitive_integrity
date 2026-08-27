"""LaTeX tables for t-tests, confidence intervals, and effect sizes.

Generates hypothesis-test summary tables and a Cohen's d table.  Reads
data from statistical_results.json.

Two things this module deliberately does not do:

* It does not renumber the hypotheses.  ``statistical_results.json``
  already names them (``H2_detection``, ``H3_autogpt``, ...); printing a
  fresh ``H2..H9`` counter alongside those names produced rows reading
  "H4 & CIF > H2_firewall", which is two different IDs for one test.
* It does not emit a column it has no data for.  A column of ``--`` claims
  a measurement exists and was merely not filled in.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .latex import escape_latex

logger = logging.getLogger(__name__)

_DATA_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "output" / "data" / "statistical_results.json"
)


def _load_statistical_results() -> Dict[str, Any]:
    """Load statistical results from statistical_results.json."""
    with open(_DATA_PATH, "r", encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)
    logger.info("Loaded statistical results from %s", _DATA_PATH)
    return data


def _p_str(p_val: float) -> str:
    # Math mode: a bare "<" in LaTeX text mode does not typeset as a
    # less-than sign under the default OT1 encoding.
    return "$< 0.001$" if p_val < 0.001 else f"{p_val:.4f}"


def _stat_str(entry: Dict[str, Any]) -> str:
    """Format a test statistic, or ``--`` when the record does not carry one.

    ``run_statistical_analysis.py`` serialises only ``name``/``p_value``/
    ``significant`` for the H2 and H3 families even though
    :class:`statistics.hypothesis.HypothesisResult` carries
    ``test_statistic`` as well, so those rows legitimately have no
    statistic to print.  ``--`` says that; it does not stand in for one.
    """
    for key in ("statistic", "test_statistic"):
        stat = entry.get(key)
        if stat is not None:
            return f"{float(stat):.2f}"
    return "--"


def _description(entry: Dict[str, Any]) -> str:
    """Describe a hypothesis row, preferring the record's own description.

    The fallbacks restate the definitions in
    ``src/statistics/hypothesis.py``: ``test_h2_cif_vs_components`` names
    each result ``H2_<component>`` and compares CIF against that single
    component; ``test_h3_per_architecture`` names each result
    ``H3_<architecture>`` and compares CIF against the baseline within
    that architecture.
    """
    described = entry.get("description")
    if described:
        return escape_latex(str(described))

    name = str(entry.get("name", ""))
    if name.startswith("H2_"):
        return f"CIF $>$ {escape_latex(name[3:].replace('_', ' '))} component alone"
    if name.startswith("H3_"):
        return f"CIF $>$ baseline on {escape_latex(name[3:].replace('_', ' '))}"
    return escape_latex(name)


def generate_hypothesis_table(results: Optional[Dict] = None) -> str:
    """Generate a LaTeX table of hypothesis test results.

    Parameters
    ----------
    results : dict, optional
        Unused; retained for signature compatibility.  Results are always
        read from ``output/data/statistical_results.json``.

    Returns
    -------
    str
        Complete LaTeX table string.
    """
    data = _load_statistical_results()

    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Hypothesis Test Results (One-Sided Welch's $t$-test). "
        r"Identifiers are the hypothesis names recorded by "
        r"\texttt{scripts/run\_statistical\_analysis.py}.}",
        r"\label{tab:hypothesis-tests}",
        r"\begin{tabular}{llccc}",
        r"\toprule",
        r"ID & Hypothesis & $t$-statistic & $p$-value & Significant \\",
        r"\midrule",
    ]

    h1 = data.get("h1")
    if h1:
        sig = "Yes" if h1.get("significant", False) else "No"
        lines.append(
            f"H1 & CIF $>$ Baseline & {_stat_str(h1)} & "
            f"{_p_str(h1.get('p_value', 1.0))} & {sig} \\\\"
        )

    # H2 (per-component) and H3 (per-architecture) are recorded the same
    # way; both are emitted so no recorded test is silently dropped.
    for key in ("h2", "h3"):
        entries: List[Dict[str, Any]] = data.get(key, [])
        for entry in entries:
            name = str(entry.get("name", key.upper()))
            sig = "Yes" if entry.get("significant", False) else "No"
            lines.append(
                f"{escape_latex(name)} & {_description(entry)} & "
                f"{_stat_str(entry)} & {_p_str(entry.get('p_value', 1.0))} & {sig} \\\\"
            )

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
        Unused; retained for signature compatibility.  Results are always
        read from ``output/data/statistical_results.json``.

    Returns
    -------
    str
        Complete LaTeX table string.
    """
    data = _load_statistical_results()
    d_val = float(data.get("cohens_d_cif_vs_baseline", 0.0))
    odds_ratio = data.get("odds_ratio_cif_vs_baseline")

    if abs(d_val) >= 0.8:
        interp = "Large"
    elif abs(d_val) >= 0.5:
        interp = "Medium"
    else:
        interp = "Small"

    header = r"Comparison & Cohen's $d$ & Interpretation"
    row = f"CIF vs Baseline & {d_val:.2f} & {interp}"
    with_or = odds_ratio is not None
    if odds_ratio is not None:
        header += r" & Odds Ratio"
        row += f" & {float(odds_ratio):.2f}"

    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Effect Sizes: CIF vs.\ No Defense}",
        r"\label{tab:effect-sizes}",
        r"\begin{tabular}{lcc" + ("c" if with_or else "") + "}",
        r"\toprule",
        header + r" \\",
        r"\midrule",
        row + r" \\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ]

    return "\n".join(lines)
