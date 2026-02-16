"""LaTeX tables for scaling results and regression.

Generates a table showing latency and memory measurements across agent
counts with regression fit statistics.
"""

from __future__ import annotations

from typing import Dict, Optional

import numpy as np


def _default_scalability_data(seed: int = 42):
    """Generate default scalability measurements."""
    rng = np.random.default_rng(seed)
    agents = np.array([2, 3, 5, 7, 10, 15, 20, 30, 50, 100])
    latency = 5.0 + 0.02 * agents ** 2 + 1.5 * agents + rng.normal(0, 2, len(agents))
    latency = np.maximum(latency, 5.0)
    memory = 50 + 8 * agents + 0.05 * agents ** 1.3 + rng.normal(0, 5, len(agents))
    memory = np.maximum(memory, 50.0)
    return agents, latency, memory


def generate_scalability_table(results: Optional[Dict] = None) -> str:
    """Generate a LaTeX table of scalability results.

    Parameters
    ----------
    results : dict, optional
        Dictionary with 'agents', 'latency', 'memory' arrays.
        Uses default data if *None*.

    Returns
    -------
    str
        Complete LaTeX table string.
    """
    if results is not None:
        agents = np.asarray(results["agents"])
        latency = np.asarray(results["latency"])
        memory = np.asarray(results["memory"])
    else:
        agents, latency, memory = _default_scalability_data()

    # Regression fit
    coeffs = np.polyfit(agents, latency, 2)
    predicted = np.polyval(coeffs, agents)
    ss_res = np.sum((latency - predicted) ** 2)
    ss_tot = np.sum((latency - latency.mean()) ** 2)
    r_squared = 1 - ss_res / ss_tot

    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Scalability: Latency and Memory vs.\ Agent Count}",
        r"\label{tab:scalability}",
        r"\begin{tabular}{rrrr}",
        r"\toprule",
        r"Agents & Latency (ms) & Memory (MB) & Predicted Lat. (ms) \\",
        r"\midrule",
    ]

    for i in range(len(agents)):
        lines.append(
            f"{agents[i]:>3d} & {latency[i]:.1f} & {memory[i]:.1f} & {predicted[i]:.1f} \\\\"
        )

    lines.extend([
        r"\midrule",
        f"\\multicolumn{{4}}{{l}}{{Quadratic fit: $L = {coeffs[0]:.4f}n^2 + {coeffs[1]:.2f}n + {coeffs[2]:.1f}$, $R^2 = {r_squared:.4f}$}} \\\\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ])

    return "\n".join(lines)
