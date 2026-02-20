"""LaTeX table for parametric assumption test results.

Reads from statistical_results.json.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def generate_assumption_table() -> str:
    """Generate LaTeX table summarising Shapiro-Wilk and Levene test results.

    Reads from statistical_results.json.  Raises FileNotFoundError if
    the data file is not available.
    """
    p = Path(__file__).resolve().parent.parent.parent.parent / "output" / "data" / "statistical_results.json"
    with open(p) as f:
        data = json.load(f)

    rows = []
    for a in data["assumptions"]:
        status = "\\checkmark" if a["passed"] else "\\texttimes"
        rows.append(
            f"  {a['test']} & {a['group']} & {a['statistic']:.4f} & "
            f"{a['p_value']:.4e} & {status} \\\\"
        )
    body = "\n".join(rows)

    logger.info("Loaded assumption test results from %s", p)
    return (
        "\\begin{table}[htbp]\n"
        "\\centering\n"
        "\\caption{Parametric Assumption Tests}\n"
        "\\label{tab:assumptions}\n"
        "\\begin{tabular}{llrrr}\n"
        "\\toprule\n"
        "Test & Group & Statistic & $p$-value & Passed \\\\\n"
        "\\midrule\n"
        f"{body}\n"
        "\\bottomrule\n"
        "\\end{tabular}\n"
        "\\end{table}\n"
    )
