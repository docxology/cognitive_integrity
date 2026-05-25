"""Shared plotting utilities for Part 1 visualizations.

Provides publication-quality defaults, a colorblind-safe palette, and a
`save_figure` helper that flushes the figure from memory after saving.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns


def setup_plotting() -> None:
    """Apply publication-quality rcParams (serif fonts, 300 DPI, whitegrid)."""
    sns.set_theme(style="whitegrid")
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 14,
        "axes.labelsize": 14,
        "axes.titlesize": 16,
        "axes.titleweight": "bold",
        "legend.fontsize": 12,
        "xtick.labelsize": 12,
        "ytick.labelsize": 12,
        "figure.titlesize": 18,
        "figure.dpi": 300,
        "lines.linewidth": 2,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.1,
    })


def get_color_palette() -> list[str]:
    """Return IBM Design Language colorblind-safe palette (5 colors)."""
    return ["#648FFF", "#DC267F", "#FFB000", "#785EF0", "#FE6100"]


def save_figure(fig: plt.Figure, output_dir: Path, name: str) -> Path:
    """Save *fig* as PNG and PDF, then close it to free memory.

    Args:
        fig: Matplotlib figure to save.
        output_dir: Destination directory (created if absent).
        name: Base filename without extension.

    Returns:
        Path to the saved PDF file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    png_path = output_dir / f"{name}.png"
    pdf_path = output_dir / f"{name}.pdf"

    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved {png_path}")
    print(f"Saved {pdf_path}")
    return pdf_path
