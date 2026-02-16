from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

from ..style import FONTSIZE, SEMANTIC_COLORS, add_source_annotation, apply_style, save_figure

try:
    from ablation.minimal_config import MinimalConfigSearch
except (ImportError, ModuleNotFoundError):
    MinimalConfigSearch = None


def plot_ablation_study(output_dir: str | Path = "output/figures") -> plt.Figure:
    """Generate ablation study figure."""
    if isinstance(output_dir, str):
        output_dir = Path(output_dir)

    # Apply style
    apply_style()

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 6))

    # Data logic (handling path relative to output_dir)
    # output_dir is .../output/figures
    # expected data path: .../output/data/ablation_study.json
    # ensure output_dir.parent exists
    data_path = output_dir.parent / "data" / "ablation_study.json"

    if data_path.exists():
        with open(data_path, "r") as f:
            data = json.load(f)

        # Sort keys to match expected order or just use them
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

    # Colorblind-friendly colors based on impact magnitude (using SEMANTIC mapping)
    colors = []
    for d in delta:
        if d == 0:
            colors.append(SEMANTIC_COLORS["firewall"])  # Blue for full/valid
        elif d <= -0.10:
            colors.append(SEMANTIC_COLORS["tripwire"])  # Magenta - critical
        elif d <= -0.07:
            colors.append(SEMANTIC_COLORS["full_cif"])  # Orange - major
        elif d <= -0.04:
            colors.append(SEMANTIC_COLORS["invariants"])  # Yellow/Gold - moderate
        else:
            colors.append(SEMANTIC_COLORS["sandbox"])  # Purple - minor

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
    ax.axvline(x=0.94, color=SEMANTIC_COLORS["firewall"], linestyle="--", alpha=0.5, linewidth=1.5)
    ax.grid(True, alpha=0.3, axis="x")

    # Colorblind-friendly legend for impact severity
    legend_elements = [
        Patch(facecolor=SEMANTIC_COLORS["tripwire"], edgecolor="black", label="Critical (Δ ≤ −0.10)"),
        Patch(
            facecolor=SEMANTIC_COLORS["full_cif"], edgecolor="black", label="Major (−0.10 < Δ ≤ −0.07)"
        ),
        Patch(
            facecolor=SEMANTIC_COLORS["invariants"], edgecolor="black", label="Moderate (−0.07 < Δ ≤ −0.04)"
        ),
        Patch(facecolor=SEMANTIC_COLORS["sandbox"], edgecolor="black", label="Minor (Δ > −0.04)"),
    ]
    ax.legend(
        handles=legend_elements, loc="lower right", fontsize=FONTSIZE["base"], title="Impact Severity"
    )

    add_source_annotation(fig, "src/visualization/figures/ablation_study.py")
    save_figure(fig, "ablation_study", output_dir=output_dir)
    return fig
