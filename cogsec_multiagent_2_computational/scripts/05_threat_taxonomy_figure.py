#!/usr/bin/env python3
"""Generate threat taxonomy visualization figure."""

import os

os.environ["MPLBACKEND"] = "Agg"

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyBboxPatch


def create_threat_taxonomy_figure(output_dir: Path) -> Path:
    """
    Create cognitive attack taxonomy tree diagram.
    """
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(1, 1, figsize=(16, 10))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 10)
    ax.axis("off")

    # Colorblind-friendly category colors (IBM Design)
    # Accessible to deuteranopia, protanopia, and tritanopia
    colors = {
        "root": "#2C3E50",
        "epistemic": "#DC267F",  # Magenta
        "behavioral": "#648FFF",  # Blue
        "social": "#785EF0",  # Purple
        "temporal": "#FE6100",  # Orange
        "attack": "#F5F5F5",  # Light gray
    }

    # Root node
    root = FancyBboxPatch(
        (6.5, 8.5),
        3,
        0.8,
        boxstyle="round,pad=0.05",
        facecolor=colors["root"],
        edgecolor="black",
        linewidth=2,
    )
    ax.add_patch(root)
    ax.text(
        8,
        8.9,
        "Cognitive Attacks",
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
        color="white",
    )

    # Category definitions
    categories = [
        (
            "Epistemic",
            "What agents believe",
            colors["epistemic"],
            1,
            [
                "Belief Injection",
                "Evidence Fabrication",
                "Confidence Manipulation",
                "Memory Poisoning",
            ],
        ),
        (
            "Behavioral",
            "How agents act",
            colors["behavioral"],
            5,
            [
                "Goal Hijacking",
                "Action Restriction",
                "Reward Hacking",
                "Capability Elicitation",
            ],
        ),
        (
            "Social",
            "Inter-agent dynamics",
            colors["social"],
            9,
            [
                "Trust Exploitation",
                "Coalition Manipulation",
                "Sybil Injection",
                "Consensus Poisoning",
            ],
        ),
        (
            "Temporal",
            "Persistence & timing",
            colors["temporal"],
            13,
            [
                "Sleeper Activation",
                "Context Overflow",
                "Checkpoint Poisoning",
                "Progressive Drift",
            ],
        ),
    ]

    for name, desc, color, x_pos, attacks in categories:
        # Category box
        cat_box = FancyBboxPatch(
            (x_pos, 5.8),
            3,
            1.5,
            boxstyle="round,pad=0.05",
            facecolor=color,
            edgecolor="black",
            linewidth=2,
        )
        ax.add_patch(cat_box)

        ax.text(
            x_pos + 1.5,
            6.8,
            name,
            ha="center",
            va="center",
            fontsize=11,
            fontweight="bold",
            color="white",
        )
        ax.text(
            x_pos + 1.5,
            6.2,
            f"({desc})",
            ha="center",
            va="center",
            fontsize=9,
            color="white",
            style="italic",
        )

        # Connect to root
        ax.plot([x_pos + 1.5, 8], [7.3, 8.5], "k-", linewidth=2)

        # Attack boxes
        for i, attack in enumerate(attacks):
            y = 4.2 - i * 1.1
            attack_box = FancyBboxPatch(
                (x_pos + 0.2, y),
                2.6,
                0.8,
                boxstyle="round,pad=0.03",
                facecolor=colors["attack"],
                edgecolor=color,
                linewidth=1.5,
            )
            ax.add_patch(attack_box)

            ax.text(
                x_pos + 1.5,
                y + 0.4,
                attack,
                ha="center",
                va="center",
                fontsize=9,
                fontweight="bold",
            )

            # Connect to category
            if i == 0:
                ax.plot([x_pos + 1.5, x_pos + 1.5], [5.8, y + 0.8], "k-", linewidth=1.5)
            else:
                ax.plot(
                    [x_pos + 1.5, x_pos + 1.5],
                    [y + 1.1 + 0.3, y + 0.8],
                    "k-",
                    linewidth=1.5,
                )

    # Add severity legend
    ax.text(0.5, 0.8, "Severity Scale:", fontsize=10, fontweight="bold")

    # Colorblind-friendly severity scale
    severity_levels = [
        ("CRITICAL", "#DC267F", "System compromise"),  # Magenta
        ("HIGH", "#FE6100", "Major integrity loss"),  # Orange
        ("MEDIUM", "#FFB000", "Partial compromise"),  # Yellow
        ("LOW", "#648FFF", "Minor impact"),  # Blue
    ]

    for i, (level, color, desc) in enumerate(severity_levels):
        x = 2.5 + i * 3.5
        circle = Circle((x, 0.8), 0.2, facecolor=color, edgecolor="black")
        ax.add_patch(circle)
        ax.text(x + 0.4, 0.8, f"{level}: {desc}", fontsize=9, va="center")

    # Title
    ax.text(
        8,
        9.5,
        "Cognitive Attack Taxonomy",
        ha="center",
        va="center",
        fontsize=14,
        fontweight="bold",
    )

    output_path_png = output_dir / "threat_taxonomy.png"
    output_path_pdf = output_dir / "threat_taxonomy.pdf"

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


if __name__ == "__main__":
    # Derive base_dir from the script's actual location
    # Script is at: projects/{project_name}/scripts/{script}.py
    script_dir = Path(__file__).resolve().parent  # scripts/
    base_dir = script_dir.parent  # projects/{project_name}/
    
    output_dir = base_dir / "output" / "figures"
    create_threat_taxonomy_figure(output_dir)
