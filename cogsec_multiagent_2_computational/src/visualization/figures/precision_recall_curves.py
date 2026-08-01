"""Precision-recall curves computed from measured per-payload detector scores.

Reads ``output/data/baseline_comparison.json`` (written by
``scripts/run_baseline_comparison.py``) and draws:

* Left — the CIF pipeline per attack family, each family scored against the
  shared benign controls.
* Right — every detector in the baseline comparison over the whole corpus.

Average precision is the measured AP of each threshold-swept curve, the
interval is a bootstrap 95% CI, and the shaded region is the pointwise
2.5/97.5 percentile band of the resampled curves.  The random-classifier
reference is drawn at each stratum's *actual* positive prevalence, not at a
fixed 0.5.

This replaces a generator that fitted the parametric shape
``1 - (1 - AP) * recall**alpha`` to a single operating point and drew
"confidence bands" of ``1.96 * spread * sin(pi * recall)`` — an analytic
flourish with no resampling behind it — and that labelled every curve with
``real_precision`` while calling it AP.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from evaluation.baselines import load_comparison_artifact

from ..style import PALETTE, SEMANTIC_COLORS, add_source_annotation, apply_style, save_figure
from .roc_curves import CATEGORY_COLORS, DETECTOR_COLORS, DETECTOR_LABELS

logger = logging.getLogger(__name__)


def _prevalence(curves: dict[str, Any]) -> float:
    """Positive prevalence for a curve block — the PR chance level."""
    total = int(curves["n_positive"]) + int(curves["n_negative"])
    return int(curves["n_positive"]) / total if total else 0.0


def _plot_pr_series(
    ax: Axes,
    curves: dict[str, Any],
    color: str,
    label: str,
    linewidth: float = 1.8,
) -> None:
    """Draw one measured PR curve with its bootstrap band.

    Raises:
        ValueError: If the recall/precision arrays are misaligned.
    """
    recall = np.asarray(curves["recall"], dtype=float)
    precision = np.asarray(curves["precision"], dtype=float)
    if recall.size != precision.size:
        raise ValueError(
            f"{label}: {recall.size} recall points vs {precision.size} precision points"
        )

    ap = float(curves["average_precision"])
    lo, hi = (float(v) for v in curves["ap_ci95"])
    ax.plot(
        recall, precision, "-", color=color, linewidth=linewidth,
        label=f"{label} (AP={ap:.3f} [{lo:.3f}, {hi:.3f}])",
    )
    ax.fill_between(
        np.asarray(curves["band_recall"], dtype=float),
        np.asarray(curves["band_precision_lo"], dtype=float),
        np.asarray(curves["band_precision_hi"], dtype=float),
        color=color,
        alpha=0.12,
        linewidth=0,
    )


def _finish_axis(ax: Axes, title: str, prevalences: list[float]) -> None:
    """Apply shared PR axis furniture and the prevalence reference line(s).

    The PR chance level is the positive prevalence of the stratum, which
    differs per attack family; every distinct level is drawn and the legend
    carries the range rather than one arbitrary representative.
    """
    levels = sorted({round(p, 4) for p in prevalences})
    for i, prevalence in enumerate(levels):
        if len(levels) == 1:
            label = f"Chance (prevalence={prevalence:.3f})"
        elif i == 0:
            label = f"Chance (prevalence {levels[0]:.3f}-{levels[-1]:.3f})"
        else:
            label = None
        ax.axhline(
            y=prevalence,
            color=SEMANTIC_COLORS["neutral"],
            linestyle="--",
            linewidth=1.0,
            alpha=0.6,
            label=label,
        )
    ax.set_xlabel("Recall", fontsize=11, fontweight="bold")
    ax.set_ylabel("Precision", fontsize=11, fontweight="bold")
    ax.set_title(title, fontsize=12, fontweight="bold", pad=10)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.05)
    ax.legend(loc="lower left", fontsize=7.5, frameon=True, framealpha=0.95)


def plot_precision_recall_curves(output_dir: str | Path = "output/figures") -> Figure:
    """Plot measured PR curves by attack family and by detector.

    Parameters
    ----------
    output_dir : str | Path
        Directory for the saved figure files.

    Returns
    -------
    Figure

    Raises
    ------
    FileNotFoundError
        If ``baseline_comparison.json`` has not been generated.
    ValueError
        If the artifact contains neither per-family nor per-detector curves.
    """
    import matplotlib.pyplot as plt

    output_dir = Path(output_dir)
    apply_style()
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = load_comparison_artifact(search_dirs=[output_dir.parent / "data"])
    per_category: dict[str, Any] = payload.get("cif_by_attack_category", {})
    detectors: list[dict[str, Any]] = payload.get("detectors", [])
    if not per_category and not detectors:
        raise ValueError(
            "baseline_comparison.json carries no PR curves; refusing to draw a "
            "precision-recall figure with nothing measured on it"
        )

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.8))
    left, right = axes[0], axes[1]

    left_prevalences: list[float] = []
    for i, (category, curves) in enumerate(sorted(per_category.items())):
        color = CATEGORY_COLORS.get(category, PALETTE[i % len(PALETTE)])
        label = f"{category.replace('_', ' ').title()} (n={curves['n_positive']})"
        _plot_pr_series(left, curves, color, label)
        left_prevalences.append(_prevalence(curves))
    if not per_category:
        logger.error("no per-family PR curves in the artifact")
        left.text(
            0.5, 0.5, "per-family scores unavailable",
            ha="center", va="center", fontsize=10, style="italic",
            color=SEMANTIC_COLORS["neutral"], transform=left.transAxes,
        )
    _finish_axis(left, "Full CIF by attack family (measured scores)", left_prevalences)

    right_prevalences: list[float] = []
    for i, detector in enumerate(detectors):
        name = str(detector["name"])
        curves = detector["curves"]
        color = DETECTOR_COLORS.get(name, PALETTE[i % len(PALETTE)])
        label = DETECTOR_LABELS.get(name, name.replace("_", " ").title())
        _plot_pr_series(
            right, curves, color, label,
            linewidth=2.6 if name == "cif_full_pipeline" else 1.8,
        )
        right_prevalences.append(_prevalence(curves))
    if not detectors:
        logger.error("no per-detector PR curves in the artifact")
        right.text(
            0.5, 0.5, "detector scores unavailable",
            ha="center", va="center", fontsize=10, style="italic",
            color=SEMANTIC_COLORS["neutral"], transform=right.transAxes,
        )
    _finish_axis(right, "Detector comparison (measured scores)", right_prevalences)

    fig.tight_layout()
    add_source_annotation(fig, "src/visualization/figures/precision_recall_curves.py")
    save_figure(fig, "fig20_precision_recall_curves", output_dir=output_dir)
    return fig
