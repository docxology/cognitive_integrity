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


def create_scalability_figure(output_dir: Path) -> tuple[Path, Path]:
    """
    Create 3-panel scalability analysis figure.
    """
    if not output_dir.exists():
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

    np.random.seed(42)

    # Load generated data
    data_path = output_dir.parent / "data" / "scalability_results.json"
    if not data_path.exists():
        print(f"Data file not found: {data_path}")
        return output_dir / "error.png", output_dir / "error.pdf"

    import json

    with open(data_path, "r") as f:
        data = json.load(f)

    # Extract arrays
    agent_counts = np.array([d["agent_count"] for d in data])
    detection_latency = np.array([d["detection_time_ms"] for d in data])
    memory_usage = np.array([d["memory_mb"] for d in data])
    consensus_latency = np.array([d["consensus_latency_ms"] for d in data])

    # Panel A: Detection Latency (Firewall O(1))
    ax1 = axes[0]
    # For visualization comparison, we plot the measured O(1) vs theoretical O(N) baseline
    ax1.plot(
        agent_counts,
        detection_latency,
        "o-",
        color=colors["firewall"],
        linewidth=2.5,
        markersize=8,
        label="Cognitive Firewall (Measured)",
    )
    # Theoretical linear baseline for comparison
    ax1.plot(
        agent_counts,
        agent_counts * 0.5 + 5,
        "--",
        color=colors["tripwire"],
        label="Theoretical O(N)",
        alpha=0.5,
    )

    ax1.set_xlabel("Number of Agents", fontsize=12, fontweight="bold")
    ax1.set_ylabel("Detection Latency (ms)", fontsize=12, fontweight="bold")
    ax1.set_title("A. Detection Latency", fontsize=13, fontweight="bold")
    ax1.set_xscale("log", base=2)
    ax1.set_xticks(agent_counts)
    ax1.set_xticklabels([str(n) for n in agent_counts])
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
        label="Full CIF (Measured)",
    )

    ax2.set_xlabel("Number of Agents", fontsize=12, fontweight="bold")
    ax2.set_ylabel("Memory Usage (MB)", fontsize=12, fontweight="bold")
    ax2.set_title("B. Memory Usage Scaling", fontsize=13, fontweight="bold")
    ax2.set_xscale("log", base=2)
    ax2.set_xticks(agent_counts)
    ax2.set_xticklabels([str(n) for n in agent_counts])
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
        label="Consensus (Measured)",
    )

    # Theoretical O(N^2) fit for reference
    if len(agent_counts) > 2:
        try:
            # Simple fit a*x^2
            p = np.polyfit(agent_counts**2, consensus_latency, 1)
            fit_vals = np.polyval(p, agent_counts**2)
            ax3.plot(agent_counts, fit_vals, "k--", alpha=0.3, label=r"Fit O(N$^2$)")
        except (np.linalg.LinAlgError, ValueError):
            pass

    ax3.set_xlabel("Number of Agents", fontsize=12, fontweight="bold")
    ax3.set_ylabel("Consensus Time (ms)", fontsize=12, fontweight="bold")
    ax3.set_title("C. Consensus Time Scaling", fontsize=13, fontweight="bold")
    ax3.set_xscale("log", base=2)
    ax3.set_xticks(agent_counts)
    ax3.set_xticklabels([str(n) for n in agent_counts])
    ax3.legend(loc="upper left", fontsize=9)

    plt.tight_layout()

    # Save as both PNG and PDF
    output_png = output_dir / "scalability_analysis.png"
    output_pdf = output_dir / "scalability_analysis.pdf"

    plt.savefig(output_png, dpi=150, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.savefig(output_pdf, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close()

    print(str(output_png))
    print(str(output_pdf))
    return output_png, output_pdf
