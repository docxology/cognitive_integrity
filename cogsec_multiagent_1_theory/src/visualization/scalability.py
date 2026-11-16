"""Scalability module.

Part of the Cognitive Integrity Framework.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""Scalability analysis visualization module."""

import os

os.environ["MPLBACKEND"] = "Agg"

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from .utils import _load_json_data, _require_number


def create_scalability_figure(output_dir: Path) -> tuple[Path, Path]:
    """
    Render complete analytic-model inputs as PNG and PDF, not measurements.

    Missing/malformed input raises before any figure or output directory is
    created. Each record requires a positive, increasing integer agent count
    and finite, nonnegative detection/memory/consensus values.
    """
    data_path = output_dir / "data" / "scalability_results.json"
    data = _load_json_data(data_path)
    if not isinstance(data, list) or not data:
        raise ValueError(f"{data_path}: expected a nonempty list of scalability records")
    fields = ("agent_count", "detection_time_ms", "memory_mb", "consensus_latency_ms")
    values = {field: [] for field in fields}
    for index, record in enumerate(data):
        if not isinstance(record, dict):
            raise ValueError(f"{data_path}: record {index} must be an object")
        for field in fields:
            values[field].append(
                _require_number(record.get(field), data_path, f"record {index}.{field}")
            )
        count = values["agent_count"][-1]
        if count <= 0 or not count.is_integer() or (
            index > 0 and count <= values["agent_count"][-2]
        ):
            raise ValueError(
                f"{data_path}: record {index}.agent_count must be a positive integer "
                "in strictly increasing order"
            )
    agent_counts = np.array(values["agent_count"])
    detection_latency = np.array(values["detection_time_ms"])
    memory_usage = np.array(values["memory_mb"])
    consensus_latency = np.array(values["consensus_latency_ms"])
    fit_vals = None
    if len(agent_counts) > 2:
        try:
            coefficients = np.polyfit(agent_counts**2, consensus_latency, 1)
            fit_vals = np.polyval(coefficients, agent_counts**2)
        except (np.linalg.LinAlgError, ValueError) as exc:
            raise ValueError(
                f"{data_path}: cannot fit the supplied analytic consensus values"
            ) from exc
        if not np.isfinite(fit_vals).all():
            raise ValueError(
                f"{data_path}: supplied analytic consensus values produce a nonfinite fit"
            )

    output_dir.mkdir(parents=True, exist_ok=True)
    # Set up professional styling
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.size": 11,
            "axes.linewidth": 1.5,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # Colorblind-friendly palette
    colors = {
        "firewall": "#648FFF",
        "tripwire": "#DC267F",
        "consensus": "#FE6100",
        "full_cif": "#FFB000",
        "baseline": "#999999",
    }


    # Panel A: Detection Latency (Firewall O(1))
    ax1 = axes[0]
    # Compare the supplied analytic model with an explicitly theoretical guide.
    ax1.plot(
        agent_counts,
        detection_latency,
        "o-",
        color=colors["firewall"],
        linewidth=2.5,
        markersize=8,
        label="Cognitive Firewall (Analytic model)",
    )
    # Theoretical linear baseline for comparison
    ax1.plot(
        agent_counts,
        agent_counts * 0.5 + 5,
        "--",
        color=colors["tripwire"],
        label="Theoretical O(N) guide (not measured)",
        alpha=0.5,
    )

    ax1.set_xlabel("Number of Agents", fontsize=12, fontweight="bold")
    ax1.set_ylabel("Detection Latency (ms)", fontsize=12, fontweight="bold")
    ax1.set_title("A. Detection Latency", fontsize=13, fontweight="bold")
    ax1.set_xscale("log", base=2)
    ax1.set_xticks(agent_counts)
    ax1.set_xticklabels([f"{n:g}" for n in agent_counts])
    ax1.legend(loc="upper left", fontsize=9)
    ax1.set_ylim(0, max(detection_latency) * 1.5 + 10)

    # Panel B: Memory Usage
    ax2 = axes[1]
    ax2.plot(
        agent_counts,
        memory_usage,
        "^-",
        color=colors["full_cif"],
        linewidth=2.5,
        markersize=8,
        label="Full CIF (Analytic model)",
    )

    ax2.set_xlabel("Number of Agents", fontsize=12, fontweight="bold")
    ax2.set_ylabel("Memory Usage (MB)", fontsize=12, fontweight="bold")
    ax2.set_title("B. Memory Usage Scaling", fontsize=13, fontweight="bold")
    ax2.set_xscale("log", base=2)
    ax2.set_xticks(agent_counts)
    ax2.set_xticklabels([f"{n:g}" for n in agent_counts])
    ax2.legend(loc="upper left", fontsize=9)

    # Panel C: Consensus Time
    ax3 = axes[2]
    ax3.plot(
        agent_counts,
        consensus_latency,
        "o-",
        color=colors["consensus"],
        linewidth=2.5,
        markersize=8,
        label="Consensus (Analytic model)",
    )

    # This fit smooths the supplied analytic model; it is not independent evidence.
    if fit_vals is not None:
        ax3.plot(agent_counts, fit_vals, "k--", alpha=0.3, label=r"Analytic fit O(N$^2$)")

    ax3.set_xlabel("Number of Agents", fontsize=12, fontweight="bold")
    ax3.set_ylabel("Consensus Time (ms)", fontsize=12, fontweight="bold")
    ax3.set_title("C. Consensus Time Scaling", fontsize=13, fontweight="bold")
    ax3.set_xscale("log", base=2)
    ax3.set_xticks(agent_counts)
    ax3.set_xticklabels([f"{n:g}" for n in agent_counts])
    ax3.legend(loc="upper left", fontsize=9)

    fig.text(
        0.5, 0.02, "Analytic models and theoretical guides — not measured performance.",
        ha="center", fontsize=10,
    )
    plt.tight_layout(rect=[0, 0.06, 1, 1])

    # Save as both PNG and PDF
    output_png = output_dir / "scalability_analysis.png"
    output_pdf = output_dir / "scalability_analysis.pdf"

    plt.savefig(output_png, dpi=150, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.savefig(output_pdf, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close()

    print(str(output_png))
    print(str(output_pdf))
    return output_png, output_pdf
