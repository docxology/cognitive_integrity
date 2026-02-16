"""LaTeX tables for per-architecture detection rates.

Generates a formatted LaTeX table showing detection rates (mean +/- CI)
for each architecture across all attack categories.
"""

from __future__ import annotations

from typing import Dict, Optional

import numpy as np

_ARCHITECTURES = ["Claude Code", "AutoGPT", "CrewAI", "LangGraph", "MetaGPT", "CAMEL"]
_CATEGORIES = ["Injection", "Trust Exploit.", "Belief Manip.", "Coordination"]


def _default_results(seed: int = 42):
    """Generate default detection results."""
    rng = np.random.default_rng(seed)
    means = np.array([
        [0.98, 0.94, 0.91, 0.96],
        [0.95, 0.90, 0.88, 0.93],
        [0.96, 0.92, 0.89, 0.94],
        [0.97, 0.93, 0.90, 0.95],
        [0.94, 0.89, 0.86, 0.92],
        [0.93, 0.87, 0.82, 0.90],
    ])
    cis = rng.uniform(0.008, 0.025, means.shape)
    return means, cis


def generate_detection_table(results: Optional[Dict] = None) -> str:
    """Generate a LaTeX table of per-architecture detection rates.

    Parameters
    ----------
    results : dict, optional
        Dictionary with 'means' (6x4 array) and 'cis' (6x4 array).
        Uses default sample data if *None*.

    Returns
    -------
    str
        Complete LaTeX table string.
    """
    if results is not None:
        means = np.asarray(results["means"])
        cis = np.asarray(results["cis"])
    else:
        means, cis = _default_results()

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
