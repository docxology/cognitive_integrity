"""Publication-quality visualization for the Cognitive Security Framework.

Subpackages
-----------
- ``figures``: 18 figure generators (attack surface, ROC curves, heatmaps, etc.)
- ``tables``: 5 LaTeX table generators (detection, statistical, scalability, etc.)

Shared style configuration lives in :mod:`src.visualization.style`.
"""

from __future__ import annotations

from .style import (
    COLORS,
    PALETTE,
    add_legend,
    apply_style,
    create_figure,
    format_axis,
    save_figure,
)

__all__ = [
    "COLORS",
    "PALETTE",
    "apply_style",
    "create_figure",
    "save_figure",
    "format_axis",
    "add_legend",
]
