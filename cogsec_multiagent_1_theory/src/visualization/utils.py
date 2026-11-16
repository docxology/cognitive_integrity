"""Shared plotting utilities for Part 1 visualizations.

Provides publication-quality defaults, a colorblind-safe palette, and a
`save_figure` helper that flushes the figure from memory after saving.
"""

from __future__ import annotations

import json
import math
from numbers import Real
from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns


def setup_plotting() -> None:
    """Apply publication-quality rcParams (serif fonts, 300 DPI, whitegrid)."""
    sns.set_theme(style="whitegrid")
    plt.rcParams.update(
        {
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
        }
    )


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


def _load_json_data(path: Path) -> object:
    """Read required figure input without creating output on failure."""
    def unique_fields(pairs):
        record = {}
        for key, value in pairs:
            if key in record:
                raise ValueError(f"duplicate JSON field {key!r}")
            record[key] = value
        return record

    try:
        with path.open(encoding="utf-8") as stream:
            return json.load(stream, object_pairs_hook=unique_fields)
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"Required figure data not found: {path}. Supply the source artifact; "
            "no figure was generated."
        ) from exc
    except ValueError as exc:
        raise ValueError(f"Invalid JSON figure data in {path}: {exc}") from exc


def _require_number(
    value: object,
    path: Path,
    field: str,
    *,
    minimum: float = 0.0,
    maximum: float | None = None,
) -> float:
    """Require a finite numeric field; missing values are never zero-filled."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{path}: {field} must be a finite number, got {value!r}")
    try:
        number = float(value)
    except OverflowError as exc:
        raise ValueError(f"{path}: {field} is outside the finite numeric range") from exc
    if not math.isfinite(number) or number < minimum or (
        maximum is not None and number > maximum
    ):
        bounds = f">= {minimum}" if maximum is None else f"in [{minimum}, {maximum}]"
        raise ValueError(f"{path}: {field} must be finite and {bounds}, got {value!r}")
    return number
