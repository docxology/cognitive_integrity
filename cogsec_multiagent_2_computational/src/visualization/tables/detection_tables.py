"""LaTeX tables for per-architecture detection rates.

Generates a formatted LaTeX table showing detection rates (mean +/- CI)
for each architecture across all attack categories.
Reads data from full_evaluation_results.json.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import numpy as np

logger = __import__('logging').getLogger(__name__)

_ARCHITECTURES = ["Claude Code", "AutoGPT", "CrewAI", "LangGraph"]
_CATEGORIES = ["Injection", "Trust Exploit.", "Belief Manip.", "Coordination"]


def _load_results(seed: int = 42):
    """Load detection results and compute real confidence intervals.

    Confidence intervals are computed using the Wilson score interval
    for binomial proportions, derived from the TP and FN counts in
    each cell of the evaluation matrix.
    """
    import json

    from data.result_loaders import evaluation_to_detection_matrix

    data_path = Path(__file__).resolve().parent.parent.parent.parent / "output" / "data" / "full_evaluation_results.json"  # noqa: E501
    archs, cats, matrix = evaluation_to_detection_matrix(path=str(data_path))

    # Load raw rows to extract TP/FN counts for CI computation
    with open(data_path, "r", encoding="utf-8") as f:
        raw_rows = json.load(f)

    # Build lookup: (architecture, category) -> (tp, fn)
    counts: dict = {}
    for r in raw_rows:
        counts[(r["architecture"], r["attack_category"])] = (
            r["true_positives"],
            r["false_negatives"],
        )

    # Compute Wilson score 95% CI half-widths
    z = 1.96  # 95% confidence level
    cis = np.zeros(matrix.shape)
    for i, arch in enumerate(archs):
        for j, cat in enumerate(cats):
            tp, fn = counts.get((arch, cat), (0, 0))
            n = tp + fn
            if n > 0:
                p_hat = tp / n
                denom = 1 + z**2 / n
                (p_hat + z**2 / (2 * n)) / denom
                margin = z * np.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * n)) / n) / denom
                cis[i, j] = margin
            else:
                cis[i, j] = 0.0

    logger.info("Loaded detection data with Wilson CIs from %s", data_path)
    return matrix, cis


def generate_detection_table(results: Optional[Dict] = None) -> str:
    """Generate a LaTeX table of per-architecture detection rates.

    Parameters
    ----------
    results : dict, optional
        Dictionary with 'means' (4x4 array) and 'cis' (4x4 array).
        Loaded from output data if *None*.

    Returns
    -------
    str
        Complete LaTeX table string.
    """
    if results is not None:
        means = np.asarray(results["means"])
        cis = np.asarray(results["cis"])
    else:
        means, cis = _load_results()

    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Detection Rates by Architecture and Attack Category (Mean $\pm$ 95\% CI)}",
        r"\label{tab:detection-rates}",
        r"\begin{tabular}{l" + "c" * (len(_CATEGORIES) + 1) + "}",
        r"\toprule",
        r"Architecture & " + " & ".join(_CATEGORIES) + r" & Overall \\",
        r"\midrule",
    ]

    for i, arch in enumerate(_ARCHITECTURES):
        row_parts = [arch]
        for j in range(len(_CATEGORIES)):
            row_parts.append(f"${means[i, j]:.3f} \\pm {cis[i, j]:.3f}$")
        overall = means[i].mean()
        overall_ci = np.sqrt(np.sum(cis[i] ** 2)) / len(_CATEGORIES)
        row_parts.append(f"${overall:.3f} \\pm {overall_ci:.3f}$")
        lines.append(" & ".join(row_parts) + r" \\")

    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ])

    return "\n".join(lines)
