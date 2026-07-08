"""Shared matplotlib style configuration for publication-quality figures.

Provides consistent colors, fonts, and helper functions used by every figure
module in the visualization package.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Literal, Optional, Sequence, Tuple, Union, overload

import matplotlib
import matplotlib.pyplot as plt
import numpy
from matplotlib.axes import Axes
from matplotlib.figure import Figure

# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------

# IBM Design / Wong colorblind-safe palette for accessibility
COLORS: Dict[str, str] = {
    "primary": "#2563EB",
    "secondary": "#059669",
    "accent": "#DC2626",
    "warning": "#D97706",
    "neutral": "#6B7280",
    "background": "#F9FAFB",
}

PALETTE: List[str] = [
    "#2563EB",  # blue
    "#DC2626",  # red
    "#059669",  # green
    "#D97706",  # amber
    "#7C3AED",  # violet
    "#DB2777",  # pink
    "#0891B2",  # cyan
    "#65A30D",  # lime
]

FONTSIZE: Dict[str, int] = {
    "tiny": 6,
    "small": 8,
    "note": 9,
    "base": 10,
    "large": 12,
    "title": 14,
}

# Semantic color mapping for consistency across figures
# Uses IBM Design / Wong colorblind-safe palette
SEMANTIC_COLORS: Dict[str, str] = {
    # System components
    "user": "#4A90D9",        # Sky Blue
    "firewall": "#648FFF",    # IBM Blue (Distinct from User)
    "orchestrator": "#27AE60", # Green
    "agent": "#9B59B6",       # Purple
    "external": "#E74C3C",    # Red
    "attack": "#C0392B",      # Dark Red

    # Taxonomy / Layers (Aliases for coherence)
    "peripheral": "#E74C3C",  # Red (Same as external tools)
    "coordination": "#FFB000", # Gold (Distinct from others)
    "systemic": "#27AE60",    # Green (Same as orchestrator)

    # Defense configurations
    "baseline": "#999999",    # Gray
    "sandbox": "#785EF0",     # IBM Purple
    "tripwire": "#DC267F",    # IBM Magenta
    "full_cif": "#FE6100",    # IBM Orange
    "invariants": "#FFB000",  # IBM Gold
    "anomaly": "#FFB000",     # IBM Gold (alias for invariants/anomaly)

    # General status
    "good": "#059669",        # Green
    "bad": "#DC2626",         # Red
    "neutral": "#6B7280",     # Gray
}


# ---------------------------------------------------------------------------
# Style application
# ---------------------------------------------------------------------------

def apply_style() -> None:
    """Configure matplotlib rcParams for publication-quality output."""
    matplotlib.rcParams.update({
        # Use DejaVu Sans for maximum Unicode coverage (subscripts, math symbols, etc.)
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
        "font.size": 10,
        "axes.labelsize": 11,
        "axes.titlesize": 12,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        # Don't use constrained_layout — figures call tight_layout() directly
        "figure.constrained_layout.use": False,
        "figure.autolayout": False,
        # Subtle grid with lighter alpha
        "axes.grid": True,
        "grid.alpha": 0.2,
        "grid.linestyle": "--",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": True,
        "axes.spines.bottom": True,
        "axes.edgecolor": "0.6",
        "axes.linewidth": 0.8,
        # Tighter tick settings
        "xtick.major.size": 3,
        "ytick.major.size": 3,
        "xtick.minor.size": 1.5,
        "ytick.minor.size": 1.5,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "xtick.direction": "in",
        "ytick.direction": "in",
        # Legend
        "legend.framealpha": 0.9,
        "legend.edgecolor": "0.8",
        "legend.fontsize": 9,
        "legend.fancybox": False,
        "legend.frameon": True,
        # Lines
        "lines.linewidth": 1.5,
        "lines.markersize": 5,
        # Patches (bars, boxes)
        "patch.force_edgecolor": True,
        "patch.edgecolor": "white",
        "patch.linewidth": 0.5,
    })


# ---------------------------------------------------------------------------
# Figure creation helpers
# ---------------------------------------------------------------------------

@overload
def create_figure(
    width: float = ...,
    height: float = ...,
    n_rows: Literal[1] = ...,
    n_cols: Literal[1] = ...,
) -> Tuple[Figure, Axes]: ...

@overload
def create_figure(
    width: float = ...,
    height: float = ...,
    n_rows: int = ...,
    n_cols: int = ...,
) -> Tuple[Figure, Union[Axes, "numpy.ndarray"]]: ...

def create_figure(
    width: float = 6.5,
    height: float = 4.5,
    n_rows: int = 1,
    n_cols: int = 1,
) -> Tuple[Figure, Union[Axes, "numpy.ndarray"]]:
    """Create a styled figure with the given grid layout.

    Returns
    -------
    fig : Figure
    axes : Axes or ndarray of Axes
    """
    apply_style()
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(width, height))
    fig.patch.set_facecolor(COLORS["background"])
    return fig, axes


def add_source_annotation(fig: Figure, source_file: str) -> None:
    """Add a small annotation showing the generating script path.

    Places italic text at the bottom of the figure so that each rendered
    figure is permanently linked to the script that produced it.
    """
    fig.text(
        0.99,
        0.01,
        f"Generated by: {source_file}",
        ha="right",
        va="bottom",
        fontsize=7,
        fontstyle="italic",
        color="#999999",
        transform=fig.transFigure,
    )



def save_figure(
    fig: Figure,
    name: str,
    output_dir: str | Path = "output/figures",
    formats: Sequence[str] = ("pdf", "png"),
) -> List[str]:
    """Save *fig* in multiple formats and return the list of saved paths."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    saved: List[str] = []
    for fmt in formats:
        path = out / f"{name}.{fmt}"
        fig.savefig(str(path), format=fmt)
        saved.append(str(path))
    plt.close(fig)
    return saved


def format_axis(
    ax: Axes,
    xlabel: str,
    ylabel: str,
    title: Optional[str] = None,
) -> None:
    """Apply standard axis labels and optional title."""
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if title is not None:
        ax.set_title(title)


def add_legend(ax: Axes, loc: str = "best", **kwargs) -> None:
    """Add a consistently-styled legend to *ax*."""
    ax.legend(
        loc=loc,
        framealpha=0.9,
        edgecolor="0.8",
        fontsize=FONTSIZE["base"],
        **kwargs,
    )
