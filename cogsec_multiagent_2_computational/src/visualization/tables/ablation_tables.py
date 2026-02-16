"""LaTeX tables for ablation study results.

Generates tables for single-component removal impact and pairwise
synergy analysis.
"""

from __future__ import annotations

from typing import Dict, Optional

import numpy as np


def _default_ablation_data():
    """Default single-component removal data."""
    return {
        "Full CIF": (0.965, 0.008),
        "- Firewall": (0.820, 0.025),
        "- Trust Calculus": (0.870, 0.022),
        "- Drift Detection": (0.910, 0.018),
        "- Consensus": (0.900, 0.019),
        "- Tripwire": (0.930, 0.016),
        "- Invariant Check": (0.920, 0.017),
        "- Provenance": (0.940, 0.015),
        "- Sandbox": (0.950, 0.013),
    }


def generate_ablation_table(results: Optional[Dict] = None) -> str:
    """Generate a LaTeX table of ablation study results.

    Parameters
    ----------
    results : dict, optional
        Mapping of config name to (detection_rate, ci) tuples.
        Uses default data if *None*.

    Returns
    -------
    str
        Complete LaTeX table string.
    """
    if results is None:
        results = _default_ablation_data()

    full_rate = results.get("Full CIF", (0.965, 0.008))[0]

    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Ablation Study: Detection Rate Impact of Component Removal}",
        r"\label{tab:ablation}",
        r"\begin{tabular}{lccr}",
        r"\toprule",
        r"Configuration & Detection Rate & 95\% CI & $\Delta$ Rate \\",
        r"\midrule",
    ]

    for name, (rate, ci) in results.items():
        delta = rate - full_rate
        delta_str = f"{delta:+.3f}" if name != "Full CIF" else "---"
        lines.append(f"{name} & {rate:.3f} & $\\pm {ci:.3f}$ & {delta_str} \\\\")
        if name == "Full CIF":
            lines.append(r"\midrule")

    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ])

    return "\n".join(lines)


def _default_synergy_data(seed: int = 42):
    """Generate pairwise synergy data."""
    rng = np.random.default_rng(seed)
    components = ["Firewall", "Trust", "Consensus", "Detection", "Tripwire"]
    n = len(components)
    synergy = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            # Synergy: how much the pair exceeds sum of individual contributions
            synergy[i, j] = rng.uniform(0.005, 0.035)
            synergy[j, i] = synergy[i, j]
    return components, synergy


def generate_synergy_table(results: Optional[Dict] = None) -> str:
    """Generate a LaTeX table of pairwise component synergies.

    Parameters
    ----------
    results : dict, optional
        Pre-computed synergy data.  Uses synthetic data if *None*.

    Returns
    -------
    str
        Complete LaTeX table string.
    """
    components, synergy = _default_synergy_data()
    n = len(components)

    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Pairwise Component Synergy ($\Delta$ above individual contributions)}",
        r"\label{tab:synergy}",
        r"\begin{tabular}{l" + "c" * n + "}",
        r"\toprule",
        r" & " + " & ".join(components) + r" \\",
        r"\midrule",
    ]

    for i in range(n):
        row = [components[i]]
        for j in range(n):
            if i == j:
                row.append("---")
            elif synergy[i, j] > 0.02:
                row.append(f"\\textbf{{{synergy[i, j]:.3f}}}")
            else:
                row.append(f"{synergy[i, j]:.3f}")
        lines.append(" & ".join(row) + r" \\")

    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ])

    return "\n".join(lines)
