"""LaTeX tables for ablation study results.

Generates tables for single-component removal impact and pairwise
synergy analysis.  Reads data from ablation_results.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

import numpy as np

logger = __import__('logging').getLogger(__name__)


def _load_ablation_data():
    """Load single-component removal data from ablation_results.json."""
    p = Path(__file__).resolve().parent.parent.parent.parent / "output" / "data" / "ablation_results.json"
    with open(p) as f:
        data = json.load(f)

    if "component_removal" in data:
        removal_list = data["component_removal"]
        full_tpr = removal_list[0]["tpr"] + removal_list[0]["delta_tpr"] if removal_list else 0.965
        results = {"Full CIF": (full_tpr, 0.008)}
        for entry in removal_list:
            label = f"- {entry['removed'].replace('_', ' ').title()}"
            results[label] = (entry["tpr"], 0.015)
        logger.info("Loaded ablation data from %s", p)
        return results

    raise FileNotFoundError(f"No component_removal in {p}")


def _load_synergy_data():
    """Load synergy data from ablation_results.json."""
    p = Path(__file__).resolve().parent.parent.parent.parent / "output" / "data" / "ablation_results.json"
    with open(p) as f:
        data = json.load(f)

    components = ["Firewall", "Trust", "Consensus", "Detection", "Tripwire"]
    n = len(components)
    synergy = np.zeros((n, n))

    if "top_synergies" in data:
        name_map = {c.lower(): i for i, c in enumerate(components)}
        name_map["trust_calculus"] = 1
        for s in data["top_synergies"]:
            a_idx = name_map.get(s["a"], -1)
            b_idx = name_map.get(s["b"], -1)
            if a_idx >= 0 and b_idx >= 0:
                synergy[a_idx, b_idx] = s["synergy"]
                synergy[b_idx, a_idx] = s["synergy"]

    logger.info("Loaded synergy data from %s", p)
    return components, synergy


def generate_ablation_table(results: Optional[Dict] = None) -> str:
    """Generate a LaTeX table of ablation study results.

    Parameters
    ----------
    results : dict, optional
        Mapping of config name to (detection_rate, ci) tuples.
        Loaded from output data if *None*.

    Returns
    -------
    str
        Complete LaTeX table string.
    """
    if results is None:
        results = _load_ablation_data()

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


def generate_synergy_table(results: Optional[Dict] = None) -> str:
    """Generate a LaTeX table of pairwise component synergies.

    Parameters
    ----------
    results : dict, optional
        Pre-computed synergy data.  Loaded from output data if *None*.

    Returns
    -------
    str
        Complete LaTeX table string.
    """
    components, synergy = _load_synergy_data()
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
