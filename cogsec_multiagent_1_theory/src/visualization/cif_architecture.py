"""Cif Architecture module.

Part of the Cognitive Integrity Framework.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""CIF architecture visualization module."""

import os

os.environ["MPLBACKEND"] = "Agg"

import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from .utils import save_figure, setup_plotting


#: Part 2's ablation artifact. Part 1 states the framework's structure and
#: Part 2 measures it, so a number appearing on a Part 1 figure has to come
#: across the series boundary rather than be typed on this side of it.
_ABLATION_PATH = (
    Path(__file__).resolve().parents[3]
    / "cogsec_multiagent_2_computational"
    / "output"
    / "data"
    / "ablation_results.json"
)


def _top_synergy() -> float:
    """The strongest measured pairwise synergy, from Part 2's ablation.

    Fails closed: an architecture diagram annotated with an invented synergy is
    the defect, and this is the policy the ledger's ``top_synergy`` variable
    already applies to the same quantity in the prose.
    """
    if not _ABLATION_PATH.is_file():
        raise FileNotFoundError(
            f"{_ABLATION_PATH} is missing; run Part 2's scripts/run_ablation.py. "
            f"This annotation reports a measured synergy and has no stand-in."
        )
    rows = json.loads(_ABLATION_PATH.read_text(encoding="utf-8")).get("top_synergies")
    if not rows:
        raise ValueError(f"{_ABLATION_PATH} records no top_synergies")
    return max(float(r["synergy"]) for r in rows)


def create_cif_architecture_figure(output_dir: Path) -> Path:
    """
    Create Cognitive Integrity Framework architecture diagram.

    Shows the three-layer defense architecture:
    - Layer 1 (Architectural): Cognitive Firewall, Belief Sandbox, Trust Calculus
    - Layer 2 (Runtime): Tripwires, Invariant verification, Drift detection
    - Layer 3 (Coordination): Byzantine consensus, Quorum verification, Provenance tracking
    """
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    # Set up styling
    setup_plotting()

    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis("off")

    # Color scheme (colorblind-friendly IBM Design)
    colors = {
        "header": "#2C3E50",
        "defense": "#648FFF",  # Blue
        "detection": "#785EF0",  # Purple
        "agent": "#FFB000",  # Yellow
        "coordination": "#DC267F",  # Magenta
        "component": "#F8F9FA",
    }

    # Main frame
    main_frame = FancyBboxPatch(
        (0.5, 0.5),
        13,
        9,
        boxstyle="round,pad=0.02",
        facecolor="white",
        edgecolor=colors["header"],
        linewidth=3,
    )
    ax.add_patch(main_frame)

    # Title
    ax.text(
        7,
        9.7,
        "COGNITIVE INTEGRITY FRAMEWORK (CIF)",
        ha="center",
        va="center",
        fontsize=16,
        fontweight="bold",
        color=colors["header"],
    )

    def draw_layer(y_start, height, color, title, components):
        """Draw a layer with components."""
        # Layer background
        layer = FancyBboxPatch(
            (1, y_start),
            12,
            height,
            boxstyle="round,pad=0.02",
            facecolor=color,
            edgecolor="black",
            linewidth=2,
            alpha=0.3,
        )
        ax.add_patch(layer)

        # Layer title
        ax.text(
            1.3,
            y_start + height - 0.35,
            title,
            fontsize=12,
            fontweight="bold",
            color=colors["header"],
        )

        # Components
        n_components = len(components)
        comp_width = 3.2
        total_width = n_components * comp_width + (n_components - 1) * 0.3
        start_x = (14 - total_width) / 2

        for i, (name, desc) in enumerate(components):
            x = start_x + i * (comp_width + 0.3)
            comp_box = FancyBboxPatch(
                (x, y_start + 0.3),
                comp_width,
                height - 0.7,
                boxstyle="round,pad=0.02",
                facecolor=colors["component"],
                edgecolor=color,
                linewidth=2,
            )
            ax.add_patch(comp_box)

            ax.text(
                x + comp_width / 2,
                y_start + height - 0.7,
                name,
                ha="center",
                va="center",
                fontsize=11,
                fontweight="bold",
            )
            ax.text(
                x + comp_width / 2,
                y_start + 0.65,
                desc,
                ha="center",
                va="center",
                fontsize=9,
                style="italic",
                wrap=True,
            )

    # Layer 1: Defense Layer (Architectural)
    draw_layer(
        7.2,
        1.8,
        colors["defense"],
        "LAYER 1 (ARCHITECTURAL)",
        [
            ("Cognitive Firewall", "Input classification"),
            ("Belief Sandbox", "Provisional beliefs"),
            ("Trust Calculus", "Bounded delegation"),
        ],
    )

    # Layer 2: Detection Layer (Runtime)
    draw_layer(
        5.2,
        1.8,
        colors["detection"],
        "LAYER 2 (RUNTIME)",
        [
            ("Tripwire Monitor", "Canary checking"),
            ("Invariant Check", "Constraint verification"),
            ("Drift Detection", "Belief distribution shift"),
        ],
    )

    # Layer 3: Agent Layer
    draw_layer(
        2.8,
        2.2,
        colors["agent"],
        "AGENT COGNITIVE STATE",
        [
            ("Beliefs (B)", "Propositions"),
            ("Goals (G)", "Objectives"),
            ("Intentions (I)", "Actions"),
            ("History (H)", "Trace"),
        ],
    )

    # Layer 4: Coordination Layer
    draw_layer(
        0.8,
        1.8,
        colors["coordination"],
        "LAYER 3 (COORDINATION)",
        [
            ("Byzantine Consensus", "n ≥ 3f + 1"),
            ("Quorum Verification", "Multi-agent approval"),
            ("Provenance Tracking", "Source attribution"),
        ],
    )

    # Add arrows between layers
    arrow_props = dict(arrowstyle="->", color=colors["header"], connectionstyle="arc3,rad=0", lw=2)

    # Defense -> Detection
    ax.annotate("", xy=(7, 7.0), xytext=(7, 7.2), arrowprops=arrow_props)

    # Detection -> Agent
    ax.annotate("", xy=(7, 5.0), xytext=(7, 5.2), arrowprops=arrow_props)

    # Agent -> Coordination
    ax.annotate("", xy=(7, 2.6), xytext=(7, 2.8), arrowprops=arrow_props)

    # Defense synergy, read from Part 2's ablation rather than typed.
    #
    # The annotation said "+9%" and the comment above it attributed the number
    # to a real experiment: "from ablation study: Firewall + Tripwires = +9%".
    # No ablation ever reported that pair at +0.09. The strongest measured
    # synergy is +0.050, and it is not that pair -- three pairs tie there, none
    # involving the firewall. An attribution to an experiment is what makes a
    # wrong number hard to find, because it reads as having a source.
    synergy = _top_synergy()
    ax.annotate(
        "",
        xy=(11.5, 7.5),
        xytext=(11.5, 5.5),
        arrowprops=dict(arrowstyle="<->", color="#888", linestyle="--", lw=1.5),
    )
    ax.text(
        12.2, 6.5, f"Defense synergy\n+{synergy:.0%}",
        fontsize=8, color="#666", ha="left", va="center",
    )

    # Add data flow annotation
    ax.text(
        13.3,
        5,
        "Data\nFlow",
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold",
        color=colors["header"],
        rotation=-90,
    )
    ax.annotate(
        "",
        xy=(13.1, 3),
        xytext=(13.1, 7),
        arrowprops=dict(arrowstyle="->", color=colors["header"], lw=2),
    )

    plt.tight_layout()

    # Save outputs
    output_path_pdf = save_figure(fig, output_dir, "cif_architecture")
    plt.close()

    return output_path_pdf
