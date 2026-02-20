"""LaTeX table for multi-seed stability results.

Reads from multi_seed_results.json.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def generate_stability_table() -> str:
    """Generate LaTeX table showing CV per metric and stable flag.

    Reads from multi_seed_results.json.  Raises FileNotFoundError
    if the data file is not available.
    """
    p = Path(__file__).resolve().parent.parent.parent.parent / "output" / "data" / "multi_seed_results.json"
    with open(p) as f:
        data = json.load(f)

    threshold = data.get("cv_threshold", 0.05)
    rows = [
        f"  Overall & {data['overall_cv']:.4f} & {threshold:.2f} & "
        f"{'\\checkmark' if data['overall_cv'] <= threshold else '\\texttimes'} \\\\"
    ]
    for arch, cv in sorted(data.get("per_architecture_cv", {}).items()):
        stable = "\\checkmark" if cv <= threshold else "\\texttimes"
        rows.append(f"  {arch} & {cv:.4f} & {threshold:.2f} & {stable} \\\\")
    for cat, cv in sorted(data.get("per_category_cv", {}).items()):
        label = cat.replace("_", " ").title()
        stable = "\\checkmark" if cv <= threshold else "\\texttimes"
        rows.append(f"  {label} & {cv:.4f} & {threshold:.2f} & {stable} \\\\")
    body = "\n".join(rows)

    logger.info("Loaded multi-seed stability results from %s", p)
    return (
        "\\begin{table}[htbp]\n"
        "\\centering\n"
        "\\caption{Multi-Seed Stability Analysis}\n"
        "\\label{tab:stability}\n"
        "\\begin{tabular}{lrrr}\n"
        "\\toprule\n"
        "Metric & CV & Threshold & Stable \\\\\n"
        "\\midrule\n"
        f"{body}\n"
        "\\bottomrule\n"
        "\\end{tabular}\n"
        "\\end{table}\n"
    )
