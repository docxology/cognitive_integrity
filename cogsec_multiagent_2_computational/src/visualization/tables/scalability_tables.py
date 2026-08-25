"""LaTeX tables for scaling results and regression.

Generates a table showing latency and memory measurements across agent
counts with regression fit statistics.  Reads the measured timings in
scalability_results.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

import numpy as np

logger = __import__('logging').getLogger(__name__)


#: The measured scalability artifact, written by scripts/run_scalability.py.
#: It records real per-round latency samples and peak traced memory on a named
#: platform, with the workload definition beside them.
_SCALABILITY_PATH = (
    Path(__file__).resolve().parents[3] / "output" / "data" / "scalability_results.json"
)


def _load_measured_scalability():
    """Agent counts, median latency in ms, and peak memory in MB, measured.

    This read ``scalability_data.json`` until now, which is a
    :class:`~data.generate.DataGenerator` placeholder: an ``agent_counts`` list
    with ``latency_ms`` and ``memory_mb`` arrays generated from a closed-form
    model with noise, no ``data_origin``, and no script that produces it. A
    real measurement of the same quantities has been sitting beside it in
    ``scalability_results.json`` -- fifteen timed rounds per agent count, peak
    traced bytes, the interpreter and processor recorded -- and nothing read it.

    The median is used rather than the mean because the samples are wall-clock
    timings on a shared machine, where the mean is the statistic a single
    scheduling hiccup moves.

    Fails closed: no placeholder fallback, because falling back to the
    placeholder is precisely the defect.
    """
    if not _SCALABILITY_PATH.is_file():
        raise FileNotFoundError(
            f"{_SCALABILITY_PATH} is missing; run scripts/run_scalability.py. "
            f"There is no stand-in: scalability_data.json is generated, not measured."
        )
    payload = json.loads(_SCALABILITY_PATH.read_text(encoding="utf-8"))
    track = payload.get("framework_track")
    if not track:
        raise ValueError(f"{_SCALABILITY_PATH} records no framework_track")

    rows = sorted(track, key=lambda r: r["n_agents"])
    # Agent counts are counts. The placeholder artifact stored them as
    # floats and the table formats them with "d", so keeping the int
    # dtype here is what lets the row read "20" rather than "20.0".
    agents = np.array([r["n_agents"] for r in rows], dtype=int)
    latency = np.array([r["latency_ms_median"] for r in rows], dtype=float)
    memory = np.array([r["peak_traced_bytes"] / (1024 * 1024) for r in rows], dtype=float)
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
        agents, latency, memory = _load_measured_scalability()

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
        f"\\multicolumn{{4}}{{l}}{{Quadratic fit: $L = {coeffs[0]:.4f}n^2 + {coeffs[1]:.2f}n + {coeffs[2]:.1f}$, $R^2 = {r_squared:.4f}$}} \\\\",  # noqa: E501
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ])

    return "\n".join(lines)
