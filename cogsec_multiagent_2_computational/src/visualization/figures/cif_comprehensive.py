"""Cif Comprehensive module.

Implements functionality for the Cognitive Integrity Framework.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from ..style import SEMANTIC_COLORS, add_source_annotation, apply_style, save_figure


def plot_cif_comprehensive(output_dir: str | Path = "output/figures") -> plt.Figure:
    """Create comprehensive CIF architecture diagram.

    Every component label maps to a real class/method in src/core/:
      - CognitiveFirewall.classify()        → src/core/firewall.py
      - SandboxManager.promote()            → src/core/sandbox.py
      - InvariantChecker.check_all()        → src/core/invariants.py
      - DriftDetector.compute_drift()       → src/core/detection.py
      - CognitiveTripwire.check()           → src/core/tripwire.py
      - ProvenanceChain.get_effective_taint()→ src/core/provenance.py
      - TrustCalculus.delegate_trust()      → src/core/trust.py
      - ByzantineConsensus.compute_consensus() → src/core/consensus.py
      - QuorumVerification.approve()        → src/core/consensus.py
    """
    if isinstance(output_dir, str):
        output_dir = Path(output_dir)

    apply_style()

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(18, 13))
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 13)
    ax.axis("off")

    # Colorblind-friendly colors
    colors = {
        "defense": SEMANTIC_COLORS["tripwire"],      # Magenta
        "detection": SEMANTIC_COLORS["anomaly"],      # Gold
        "agent": SEMANTIC_COLORS["agent"],            # Purple
        "coordination": SEMANTIC_COLORS["systemic"],  # Green
        "input": SEMANTIC_COLORS["user"],             # Blue
        "external": SEMANTIC_COLORS["external"],      # Red
        "header": "#2C3E50",
        "flow": "#7F8C8D",
    }

    # --- Title ---
    ax.text(
        9, 12.5,
        "COGNITIVE INTEGRITY FRAMEWORK (CIF)",
        ha="center", va="center", fontsize=22, fontweight="bold",
        color=colors["header"],
    )
    ax.text(
        9, 12.0,
        "Layered Defense Architecture for Multiagent AI Systems",
        ha="center", va="center", fontsize=14, style="italic",
        color="#5D6D7E",
    )

    # --- Main frame ---
    frame = FancyBboxPatch(
        (0.5, 0.5), 17, 11,
        boxstyle="round,pad=0.02",
        facecolor="white", edgecolor=colors["header"], linewidth=3,
    )
    ax.add_patch(frame)

    # --- Input Sources (left sidebar) ---
    input_box = FancyBboxPatch(
        (0.8, 7.0), 2.2, 3.0,
        boxstyle="round,pad=0.02",
        facecolor=colors["input"], edgecolor="black", linewidth=2, alpha=0.9,
    )
    ax.add_patch(input_box)
    ax.text(1.9, 9.2, "INPUT", ha="center", va="center",
            fontsize=13, fontweight="bold", color="white")
    ax.text(1.9, 8.8, "SOURCES", ha="center", va="center",
            fontsize=13, fontweight="bold", color="white")
    ax.text(1.9, 8.1, "• User Prompts", ha="center", va="center",
            fontsize=12, color="white")
    ax.text(1.9, 7.7, "• Tool Responses", ha="center", va="center",
            fontsize=12, color="white")
    ax.text(1.9, 7.3, "• Agent Messages", ha="center", va="center",
            fontsize=12, color="white")

    # --- Layer definitions ---
    # Each component: (display_name, class.method, formula)
    # All map to real src/core/ implementations
    layers = [
        {
            "name": "DEFENSE LAYER",
            "y": 8.8,
            "height": 2.0,
            "color": colors["defense"],
            "components": [
                ("Cognitive Firewall", "firewall.py\nCognitiveFirewall.classify()", "τ_f = 0.5"),
                ("Belief Sandbox", "sandbox.py\nSandboxManager.promote()", "γ → promotion"),
                ("Behavioral Invariants", "invariants.py\nInvariantChecker.check_all()", "I ⊆ permitted"),
            ],
        },
        {
            "name": "DETECTION LAYER",
            "y": 6.4,
            "height": 2.0,
            "color": colors["detection"],
            "components": [
                ("Drift Detection", "detection.py\nDriftDetector.compute_drift()", "σ(Δb) > τ_d"),
                ("Tripwire Monitor", "tripwire.py\nCognitiveTripwire.check()", "c_i ∈ B?"),
                ("Provenance Tracker", "provenance.py\nProvenanceChain.get_taint()", "P: B → sources"),
            ],
        },
        {
            "name": "AGENT LAYER",
            "y": 3.8,
            "height": 2.2,
            "color": colors["agent"],
            "components": [
                ("Beliefs (B)", "Propositions\nP(b) ∈ [0,1]", "verified/provisional"),
                ("Goals (G)", "Objectives\n⟨G, ≺⟩ ordered", "priority queue"),
                ("Intentions (I)", "Actions\nπ: S → A", "policy mapping"),
            ],
        },
        {
            "name": "COORDINATION LAYER",
            "y": 1.0,
            "height": 2.4,
            "color": colors["coordination"],
            "components": [
                ("Trust Calculus", "trust.py\nTrustCalculus.delegate_trust()", "T(a→c) ≤ δ^d"),
                ("Byzantine Consensus", "consensus.py\nByzantineConsensus\n.compute_consensus()", "BFT: n≥3f+1"),
                ("Quorum Verification", "consensus.py\nQuorumVerification.approve()", "Byzantine tolerance"),
            ],
        },
    ]

    # --- Draw layers ---
    layer_left = 3.3
    layer_width = 10.5  # Narrower to avoid External Services overlap
    for layer in layers:
        # Layer background
        layer_box = FancyBboxPatch(
            (layer_left, layer["y"]),
            layer_width, layer["height"],
            boxstyle="round,pad=0.02",
            facecolor=layer["color"], edgecolor="black",
            linewidth=2, alpha=0.2,
        )
        ax.add_patch(layer_box)

        # Layer label
        ax.text(
            layer_left + 0.3,
            layer["y"] + layer["height"] - 0.3,
            layer["name"],
            fontsize=13, fontweight="bold", color=colors["header"],
        )

        # Components
        n_comp = len(layer["components"])
        comp_width = (layer_width - 0.6 - 0.3 * (n_comp - 1)) / n_comp
        start_x = layer_left + 0.3

        for i, (name, desc, formula) in enumerate(layer["components"]):
            x = start_x + i * (comp_width + 0.3)

            # Component box
            comp_box = FancyBboxPatch(
                (x, layer["y"] + 0.15),
                comp_width, layer["height"] - 0.55,
                boxstyle="round,pad=0.02",
                facecolor="white", edgecolor=layer["color"],
                linewidth=1.5,
            )
            ax.add_patch(comp_box)

            # Component name
            ax.text(
                x + comp_width / 2,
                layer["y"] + layer["height"] - 0.65,
                name,
                ha="center", va="center",
                fontsize=12, fontweight="bold", color=colors["header"],
            )
            # Description (class.method)
            ax.text(
                x + comp_width / 2,
                layer["y"] + layer["height"] / 2 - 0.1,
                desc,
                ha="center", va="center",
                fontsize=10, color="#5D6D7E",
                fontfamily="monospace",
            )
            # Formula
            ax.text(
                x + comp_width / 2,
                layer["y"] + 0.45,
                formula,
                ha="center", va="center",
                fontsize=10, style="italic",
                color=layer["color"], fontfamily="monospace",
            )

    # --- Data flow arrows (left side, vertical) ---
    arrow_x = 3.1
    flows = [
        (10.5, 10.8, "Raw Input"),
        (8.8, 6.4, "Filtered"),
        (6.4, 3.8, "Verified"),
        (3.8, 1.0, "Coordinated"),
    ]
    for y_end, y_start, label in flows:
        ax.annotate(
            "", xy=(arrow_x, y_end),
            xytext=(arrow_x, y_start + 0.1),
            arrowprops=dict(
                arrowstyle="-|>", color=colors["flow"], lw=2, mutation_scale=15
            ),
        )

    # Input → Defense arrow
    ax.annotate(
        "", xy=(3.3, 8.3), xytext=(3.0, 8.3),
        arrowprops=dict(
            arrowstyle="-|>", color=colors["input"], lw=2, mutation_scale=15
        ),
    )

    # --- External Services (right sidebar, OUTSIDE the layers) ---
    ext_box = FancyBboxPatch(
        (14.3, 4.5), 2.8, 4.0,
        boxstyle="round,pad=0.02",
        facecolor=colors["external"], edgecolor="black", linewidth=2,
    )
    ax.add_patch(ext_box)
    ax.text(15.7, 8.0, "EXTERNAL", ha="center", va="center",
            fontsize=13, fontweight="bold", color="white")
    ax.text(15.7, 7.5, "SERVICES", ha="center", va="center",
            fontsize=13, fontweight="bold", color="white")
    ax.text(15.7, 6.8, "• Web APIs", ha="center", va="center",
            fontsize=12, color="white")
    ax.text(15.7, 6.3, "• Tools", ha="center", va="center",
            fontsize=12, color="white")
    ax.text(15.7, 5.8, "• Databases", ha="center", va="center",
            fontsize=12, color="white")
    ax.text(15.7, 5.2, "(Sandboxed Access)", ha="center", va="center",
            fontsize=11, style="italic", color="white")

    # External ↔ Layers connection arrow
    ax.annotate(
        "", xy=(13.8, 6.5), xytext=(14.3, 6.5),
        arrowprops=dict(
            arrowstyle="<->", color=colors["external"], lw=2,
        ),
    )

    # --- Key Metrics (left sidebar, below input) ---
    metrics_box = FancyBboxPatch(
        (0.8, 1.2), 2.2, 3.0,
        boxstyle="round,pad=0.02",
        facecolor="#F8F9FA", edgecolor=colors["header"], linewidth=1.5,
    )
    ax.add_patch(metrics_box)
    ax.text(1.9, 3.9, "KEY METRICS", ha="center", va="center",
            fontsize=12, fontweight="bold", color=colors["header"])
    ax.text(1.9, 3.3, "Detection: 94%", ha="center", va="center",
            fontsize=12, color=SEMANTIC_COLORS["firewall"], fontweight="bold")
    ax.text(1.9, 2.8, "FPR: 6%", ha="center", va="center",
            fontsize=12, color=colors["defense"])
    ax.text(1.9, 2.3, "Latency: +23%", ha="center", va="center",
            fontsize=12, color=colors["detection"])
    ax.text(1.9, 1.8, "Integrity: +127%", ha="center", va="center",
            fontsize=12, color=colors["coordination"])

    # --- Properties (left sidebar, between input and metrics) ---
    props_box = FancyBboxPatch(
        (0.8, 4.5), 2.2, 2.2,
        boxstyle="round,pad=0.02",
        facecolor="#F8F9FA", edgecolor=colors["header"], linewidth=1.5,
    )
    ax.add_patch(props_box)
    ax.text(1.9, 6.4, "PROPERTIES", ha="center", va="center",
            fontsize=12, fontweight="bold", color=colors["header"])
    ax.text(1.9, 5.9, "• Belief Integrity", ha="center", va="center",
            fontsize=11, color=colors["defense"])
    ax.text(1.9, 5.5, "• Trust Boundedness", ha="center", va="center",
            fontsize=11, color=colors["coordination"])
    ax.text(1.9, 5.1, "• Goal Alignment", ha="center", va="center",
            fontsize=11, color=colors["agent"])
    ax.text(1.9, 4.7, "• Provenance", ha="center", va="center",
            fontsize=11, color=colors["detection"])

    plt.tight_layout()
    add_source_annotation(fig, "src/visualization/figures/cif_comprehensive.py")

    save_figure(fig, "cif_comprehensive", output_dir=output_dir)
    return fig
