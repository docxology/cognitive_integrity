"""LaTeX tables for scaling results and regression.

Generates a table showing latency and memory measurements across agent
counts with regression fit statistics.  Reads from scalability_data.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

import numpy as np

logger = __import__('logging').getLogger(__name__)


def _load_scalability_data():
    """Load scalability measurements from scalability_data.json."""
    p = Path(__file__).resolve().parent.parent.parent.parent / "output" / "data" / "scalability_data.json"
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    agents = np.array(data["agent_counts"])
    latency = np.array(data["latency_ms"])
    memory = np.array(data["memory_mb"])
    logger.info("Loaded scalability data from %s", p)
    return agents, latency, memory


def generate_scalability_table(results: Optional[Dict] = None) -> str:
    """Generate a LaTeX table of scalability results.

    Parameters
    ----------
    results : dict, optional
        Dictionary with 'agents', 'latency', 'memory' arrays.
        Loaded from output data if *None*.

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
        agents, latency, memory = _load_scalability_data()

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
