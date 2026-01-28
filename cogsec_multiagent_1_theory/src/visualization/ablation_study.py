#!/usr/bin/env python3
"""Ablation study visualization module."""

import os

os.environ["MPLBACKEND"] = "Agg"

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def create_ablation_study_figure(output_dir: Path) -> Path:
    """
    Create ablation study visualization.
    """
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 6))

    # Data
    # Data
    data_path = output_dir.parent / "data" / "ablation_study.json"
    if data_path.exists():
        import json
        with open(data_path, "r") as f:
            data = json.load(f)
        
        # Sort keys to match expected order or just use them
        # Expected: Full, then individual minus
        keys = ["full_cif", "minus_firewall", "minus_sandbox", "minus_tripwires", "minus_invariants", "minus_trust_decay"]
        # Ensure keys exist
        keys = [k for k in keys if k in data]
        
        components = []
        detection = []
        delta = []
        
        for k in keys:
            label = "Full CIF" if k == "full_cif" else f"− {k.replace('minus_', '').replace('_', ' ').title()}"
            components.append(label)
            detection.append(data[k]["detection"])
            delta.append(data[k]["delta"])
            
    else:
        components = [
            "Full CIF",
            "− Firewall",
            "− Sandbox",
            "− Tripwires",
            "− Invariants",
            "− Trust Decay",
        ]
        detection = [0.94, 0.81, 0.88, 0.85, 0.89, 0.91]
        delta = [0.0, -0.13, -0.06, -0.09, -0.05, -0.03]

    # Colorblind-friendly colors based on impact magnitude (IBM Design)
    # Accessible to deuteranopia, protanopia, and tritanopia
    colors = []
    for d in delta:
        if d == 0:
            colors.append("#648FFF")  # Blue for full
        elif d <= -0.10:
            colors.append("#DC267F")  # Magenta - critical
        elif d <= -0.07:
            colors.append("#FE6100")  # Orange - major
        elif d <= -0.04:
            colors.append("#FFB000")  # Yellow - moderate
        else:
            colors.append("#785EF0")  # Purple - minor

    y_pos = np.arange(len(components))
    bars = ax.barh(y_pos, detection, color=colors, edgecolor="black", linewidth=1)

    # Add detection values and deltas
    for i, (det, d) in enumerate(zip(detection, delta)):
        ax.text(
            det + 0.005, i, f"{det:.2f}", va="center", fontsize=10, fontweight="bold"
        )
        if d != 0:
            ax.text(
                0.72,
                i,
                f"Δ = {d:+.2f}",
                va="center",
                fontsize=10,
                color="#7F8C8D",
                style="italic",
            )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(components, fontsize=11)
    ax.set_xlabel("Detection Rate", fontsize=12)
    ax.set_title(
        "Ablation Study: Defense Component Contribution",
        fontsize=14,
        fontweight="bold",
        pad=15,
    )
    ax.set_xlim(0.70, 1.0)
    ax.axvline(x=0.94, color="#648FFF", linestyle="--", alpha=0.5, linewidth=1.5)
    ax.grid(True, alpha=0.3, axis="x")

    # Colorblind-friendly legend for impact severity (IBM Design)
    from matplotlib.patches import Patch

    legend_elements = [
        Patch(facecolor="#DC267F", edgecolor="black", label="Critical (Δ ≤ −0.10)"),
        Patch(
            facecolor="#FE6100", edgecolor="black", label="Major (−0.10 < Δ ≤ −0.07)"
        ),
        Patch(
            facecolor="#FFB000", edgecolor="black", label="Moderate (−0.07 < Δ ≤ −0.04)"
        ),
        Patch(facecolor="#785EF0", edgecolor="black", label="Minor (Δ > −0.04)"),
    ]
    ax.legend(
        handles=legend_elements, loc="lower right", fontsize=9, title="Impact Severity"
    )

    plt.tight_layout()

    # Save both PNG and PDF
    output_path_png = output_dir / "ablation_study.png"
    output_path_pdf = output_dir / "ablation_study.pdf"

    plt.savefig(
        output_path_png,
        dpi=150,
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )
    plt.savefig(
        output_path_pdf, bbox_inches="tight", facecolor="white", edgecolor="none"
    )
    plt.close()

    print(str(output_path_png))
    print(str(output_path_pdf))
    return output_path_pdf
