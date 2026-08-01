"""ROC curves computed from measured per-payload detector scores.

Both panels are drawn from ``output/data/baseline_comparison.json``, which
``scripts/run_baseline_comparison.py`` produces by running the real CIF
pipeline and the real baseline detectors over the same labelled corpus:

* Left — every detector in the comparison (CIF, keyword regex, length-only,
  bag-of-words, and the chance-level null), each with its measured AUC and
  bootstrap 95% CI, plus each detector's *deployed* operating point.
* Right — the CIF pipeline split by attack family, each family scored against
  the shared benign controls.

Shaded regions are vertical-averaging bootstrap bands: the 2.5/97.5 pointwise
percentiles of the resampled curves.  Nothing on this figure is drawn from a
random number generator standing in for a measurement, and no curve is drawn
for a series whose scores do not exist.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from evaluation.baselines import auc_in_order, load_comparison_artifact

from ..style import SEMANTIC_COLORS, add_source_annotation, apply_style, save_figure

matplotlib.use("Agg")
logger = logging.getLogger(__name__)

#: Stable colour per detector so the panels and the manuscript agree.
DETECTOR_COLORS: dict[str, str] = {
    "cif_full_pipeline": SEMANTIC_COLORS["full_cif"],
    "keyword_regex": SEMANTIC_COLORS["firewall"],
    "length_only": SEMANTIC_COLORS["tripwire"],
    "bag_of_words_lr": SEMANTIC_COLORS["sandbox"],
    "random_null": SEMANTIC_COLORS["baseline"],
}

#: Human-readable series labels.
DETECTOR_LABELS: dict[str, str] = {
    "cif_full_pipeline": "Full CIF pipeline",
    "keyword_regex": "Keyword regex baseline",
    "length_only": "Payload length only",
    "bag_of_words_lr": "Bag-of-words LR (out-of-fold)",
    "random_null": "Chance null (matched flag rate)",
}

CATEGORY_COLORS: dict[str, str] = {
    "injection": SEMANTIC_COLORS["firewall"],
    "trust_exploitation": SEMANTIC_COLORS["sandbox"],
    "belief_manipulation": SEMANTIC_COLORS["tripwire"],
    "coordination": SEMANTIC_COLORS["coordination"],
}


def _series_from_artifact(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Project the comparison artifact onto the per-detector series mapping."""
    series: dict[str, dict[str, Any]] = {}
    for detector in payload.get("detectors", []):
        curves = detector.get("curves", {})
        metrics = detector.get("metrics", {})
        series[str(detector["name"])] = {
            "fpr": curves["fpr"],
            "tpr": curves["tpr"],
            "auc": curves["auc"],
            "auc_ci95": curves["auc_ci95"],
            "band_fpr": curves["band_fpr"],
            "band_tpr_lo": curves["band_tpr_lo"],
            "band_tpr_hi": curves["band_tpr_hi"],
            "n_bootstrap_used": curves["n_bootstrap_used"],
            "operating_point": (metrics.get("fpr"), metrics.get("tpr")),
            "kind": detector.get("kind", "baseline"),
        }
    return series


def _load_roc_data(output_dir: Path) -> dict:
    """Load ROC series for :func:`plot_roc_curves`.

    Resolution order:

    1. ``<output_dir>/../data/roc_results.json`` — an explicit caller-supplied
       override of ``{name: {"fpr": [...], "tpr": [...]}}`` series.
    2. ``<output_dir>/../data/baseline_comparison.json``.
    3. The canonical ``<project>/output/data/baseline_comparison.json``.

    There is no synthetic fallback.  The previous implementation derived
    curves for four defense mechanisms from a power law over an ablation
    detection rate — four *identical* fabricated curves that every one of
    which reported AUC=0.857 — and derived "Full CIF" from sixteen
    per-architecture operating points that all sat at FPR=0 and therefore
    integrated to AUC=0.000.  Both are gone.

    Args:
        output_dir: Figure output directory (its sibling ``data`` directory is
            searched first).

    Returns:
        Mapping of series name to plot data.

    Raises:
        FileNotFoundError: If no real artifact can be found.
    """
    legacy = output_dir.parent / "data" / "roc_results.json"
    if legacy.exists():
        with open(legacy, "r", encoding="utf-8") as handle:
            data: dict = json.load(handle)
        logger.info("Loaded explicit ROC series from %s", legacy)
        return data

    payload = load_comparison_artifact(search_dirs=[output_dir.parent / "data"])
    logger.info(
        "Loaded measured ROC series for %d detectors from %s",
        len(payload.get("detectors", [])),
        payload.get("source_script"),
    )
    return _series_from_artifact(payload)


def _plot_series(ax: Axes, name: str, data: dict[str, Any], color: str, label: str) -> bool:
    """Draw one ROC series; return ``True`` if a curve was drawn.

    Raises:
        ValueError: If the series carries FPR/TPR arrays of different lengths —
            a malformed measurement must stop the render, not be skipped.
    """
    fpr = np.asarray(data.get("fpr", []), dtype=float)
    tpr = np.asarray(data.get("tpr", []), dtype=float)
    if fpr.size == 0 or tpr.size == 0:
        logger.warning("series %s has no points; not drawing a curve for it", name)
        return False
    if fpr.size != tpr.size:
        raise ValueError(
            f"series {name} has {fpr.size} FPR points and {tpr.size} TPR points"
        )

    auc = data.get("auc")
    if auc is None:
        auc = auc_in_order(fpr, tpr)
    ci = data.get("auc_ci95")
    suffix = f"AUC={auc:.3f}"
    if ci is not None:
        suffix += f" [{ci[0]:.3f}, {ci[1]:.3f}]"

    linewidth = 2.6 if name == "cif_full_pipeline" else 1.8
    linestyle = ":" if data.get("kind") == "null" else "-"
    ax.plot(fpr, tpr, linestyle, color=color, linewidth=linewidth,
            label=f"{label} ({suffix})")

    band_x = data.get("band_fpr")
    if band_x is not None:
        ax.fill_between(
            np.asarray(band_x, dtype=float),
            np.asarray(data["band_tpr_lo"], dtype=float),
            np.asarray(data["band_tpr_hi"], dtype=float),
            color=color,
            alpha=0.12,
            linewidth=0,
        )

    op = data.get("operating_point")
    if op is not None and op[0] is not None and op[1] is not None:
        ax.plot(
            [op[0]], [op[1]], marker="D", color=color, markersize=6,
            markeredgecolor="white", markeredgewidth=0.8, linestyle="none",
        )
    return True


def _finish_axis(ax: Axes, title: str) -> None:
    """Apply the shared ROC axis furniture."""
    ax.plot([0, 1], [0, 1], "--", color=SEMANTIC_COLORS["neutral"], linewidth=1.0,
            label="Chance (AUC=0.500)")
    ax.set_xlabel("False Positive Rate", fontsize=11, fontweight="bold")
    ax.set_ylabel("True Positive Rate", fontsize=11, fontweight="bold")
    ax.set_title(title, fontsize=12, fontweight="bold", pad=10)
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.legend(loc="lower right", fontsize=7.5, frameon=True, framealpha=0.95)


def plot_roc_curves(output_dir: str | Path = "output/figures") -> Figure:
    """Plot measured ROC curves per detector and for CIF by attack family.

    Diamond markers mark each detector's *deployed* operating point, which for
    CIF sits well below its own curve: the pipeline's score is informative but
    its threshold is not where Youden's J is maximised.

    Parameters
    ----------
    output_dir : str | Path
        Directory where the figure is saved.

    Returns
    -------
    Figure
        The created matplotlib figure.

    Raises
    ------
    ValueError
        If ROC series are present but none is plottable — a malformed
        measurement must fail the render rather than yield an empty axis.
    """
    import matplotlib.pyplot as plt

    output_dir = Path(output_dir)
    apply_style()
    output_dir.mkdir(parents=True, exist_ok=True)

    roc_data = _load_roc_data(output_dir)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.8))
    left, right = axes[0], axes[1]

    drawn = 0
    palette = list(SEMANTIC_COLORS.values())
    for i, (name, data) in enumerate(roc_data.items()):
        color = DETECTOR_COLORS.get(name, palette[i % len(palette)])
        label = DETECTOR_LABELS.get(name, name.replace("_", " ").title())
        drawn += int(_plot_series(left, name, data, color, label))

    if roc_data and drawn == 0:
        raise ValueError(
            "ROC series were supplied but none was plottable; refusing to emit "
            "an ROC figure with no measured curve on it"
        )
    if not roc_data:
        # Only reachable when a caller injects an empty mapping: the real
        # loader raises FileNotFoundError long before this point.  Say so on
        # the figure itself rather than shipping a blank axis a reader could
        # mistake for a measurement.
        logger.error("no ROC series available; emitting an explicitly empty figure")
        left.text(
            0.5, 0.5,
            "NO MEASURED DETECTOR SCORES AVAILABLE\n"
            "run scripts/run_baseline_comparison.py",
            ha="center", va="center", fontsize=11, fontweight="bold",
            color=SEMANTIC_COLORS["bad"], transform=left.transAxes,
        )

    _finish_axis(left, "Detector comparison (measured scores)")

    # Right panel: CIF per attack family, when the full artifact is available.
    per_category: dict[str, Any] = {}
    try:
        per_category = load_comparison_artifact(
            search_dirs=[output_dir.parent / "data"]
        ).get("cif_by_attack_category", {})
    except (FileNotFoundError, ValueError) as exc:
        logger.warning("per-family ROC unavailable (%s); drawing left panel only", exc)

    for i, (category, curves) in enumerate(sorted(per_category.items())):
        color = CATEGORY_COLORS.get(category, palette[i % len(palette)])
        label = f"{category.replace('_', ' ').title()} (n={curves['n_positive']})"
        _plot_series(right, category, {**curves, "kind": "cif"}, color, label)
    if not per_category:
        right.text(
            0.5, 0.5, "per-family scores unavailable",
            ha="center", va="center", fontsize=10, style="italic",
            color=SEMANTIC_COLORS["neutral"], transform=right.transAxes,
        )
    _finish_axis(right, "Full CIF by attack family (measured scores)")

    fig.tight_layout()
    add_source_annotation(fig, "src/visualization/figures/roc_curves.py")
    save_figure(fig, "roc_curves", output_dir=output_dir)
    return fig
