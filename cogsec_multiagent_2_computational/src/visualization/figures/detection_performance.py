"""Detection Performance module.

Implements functionality for the Cognitive Integrity Framework.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from composition.algebra import compute_series_detection_rate

from ..style import FONTSIZE, SEMANTIC_COLORS, add_source_annotation, apply_style, save_figure

logger = logging.getLogger(__name__)


def _load_detection_data(output_dir: Path) -> dict:
    """Load generated detection data from the pipeline output."""
    data_path = output_dir.parent / "data" / "detection_data.json"
    if not data_path.exists():
        data_path = Path(__file__).resolve().parent.parent.parent.parent / "output" / "data" / "detection_data.json"  # noqa: E501
    with open(data_path) as f:
        data = json.load(f)
    logger.info("Loaded detection data from %s", data_path)
    return data


def _load_ablation_data(output_dir: Path) -> dict:
    """Read the ablation artifact, the source of every number in Panel A."""
    path = output_dir.parent / "data" / "ablation_results.json"
    if not path.exists():
        path = Path(__file__).resolve().parents[3] / "output" / "data" / "ablation_results.json"
    with open(path) as handle:
        return json.load(handle)


def plot_detection_performance(output_dir: str | Path = "output/figures") -> plt.Figure:
    """Generate detection performance comparison figure.

    Uses real data from full_evaluation_results.json (Panel A) and
    detection_data.json (Panel B).
    """
    if isinstance(output_dir, str):
        output_dir = Path(output_dir)

    apply_style()
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    colors = {
        "baseline": SEMANTIC_COLORS["baseline"],
        "firewall": SEMANTIC_COLORS["firewall"],
        "sandbox": SEMANTIC_COLORS["sandbox"],
        "tripwire": SEMANTIC_COLORS["tripwire"],
        "full_cif": SEMANTIC_COLORS["full_cif"],
    }

    # Panel A: single-mechanism vs. full-pipeline detection, from the ablation run.
    #
    # This panel used to label its bars "Firewall Only", "Sandbox Only",
    # "Tripwires Only" and "Invariants Only" while plotting the mean detection
    # rate of architectures 1-4 from full_evaluation_results.json -- a different
    # evaluation arm entirely, and one whose values (~0.94) are an order of
    # magnitude above what any single mechanism actually achieves.  The FPR
    # series was a hardcoded list that appears in no artifact, and the "F1"
    # was 2t(1-f)/(t+(1-f)), which is not F1.
    #
    # Everything below is read from ablation_results.json.  Single-mechanism
    # rates come from the pairwise synergy records, which carry each
    # mechanism's solo TPR and FPR; only the four mechanisms that appear there
    # can be plotted, so the panel shows those four and says so.
    ax1 = axes[0]
    ablation = _load_ablation_data(output_dir)

    solo: dict[str, tuple[float, float]] = {}
    for pair in ablation["top_synergies"]:
        for side in ("a", "b"):
            solo[pair[side]] = (float(pair[f"tpr_{side}"]), float(pair.get(f"fpr_{side}", 0.0)))

    mechanisms = sorted(solo, key=lambda name: solo[name][0])
    defenses = ["Baseline"] + [m.replace("_", "\n").title() + "\nOnly" for m in mechanisms] + ["Full CIF"]

    full = ablation["full_pipeline"]
    tpr = [0.0] + [solo[m][0] for m in mechanisms] + [float(full["tpr"])]
    fpr = [0.0] + [solo[m][1] for m in mechanisms] + [float(full["fpr"])]

    # With FPR measured at zero, precision is exactly 1 and F1 reduces to
    # 2r/(1+r).  Computing it from the measured pair rather than assuming
    # precision keeps the identity visible if a future run has a non-zero FPR.
    def _f1(recall: float, false_positive_rate: float) -> float:
        if recall <= 0:
            return 0.0
        precision = 1.0 if false_positive_rate == 0 else recall / (recall + false_positive_rate)
        return 2 * precision * recall / (precision + recall)

    f1 = [_f1(t, f) for t, f in zip(tpr, fpr)]

    theoretical_cif = compute_series_detection_rate([solo[m][0] for m in mechanisms])
    logger.info(
        "Panel A from ablation_results.json: %d single mechanisms, full-pipeline TPR %.4f, "
        "series-composition prediction %.4f",
        len(mechanisms),
        full["tpr"],
        theoretical_cif,
    )

    x = np.arange(len(defenses))
    width = 0.25

    ax1.bar(x - width, tpr, width, label="TPR (Recall)", color=SEMANTIC_COLORS["firewall"], edgecolor="black")  # noqa: E501
    ax1.bar(x, fpr, width, label="FPR", color=SEMANTIC_COLORS["tripwire"], edgecolor="black")
    ax1.bar(x + width, f1, width, label="F1 Score", color=SEMANTIC_COLORS["sandbox"], edgecolor="black")  # noqa: E501

    ax1.annotate(
        f"Theoretical: {theoretical_cif:.2f}",
        xy=(len(defenses) - 1 - width, theoretical_cif),
        xytext=(len(defenses) - 2.0, theoretical_cif + 0.08),
        fontsize=FONTSIZE["small"],
        color=SEMANTIC_COLORS["full_cif"],
        arrowprops=dict(arrowstyle="->", color=SEMANTIC_COLORS["full_cif"], lw=1),
    )

    ax1.set_ylabel("Score", fontsize=12)
    ax1.set_title(
        "A. Single-Mechanism vs. Full-Pipeline Detection (ablation run)",
        fontsize=12,
        fontweight="bold",
    )
    ax1.set_xticks(x)
    ax1.set_xticklabels(defenses, fontsize=FONTSIZE["base"])
    ax1.legend(loc="upper left", fontsize=FONTSIZE["base"])
    ax1.set_ylim(0, max(max(tpr), max(f1), theoretical_cif) * 1.35)
    ax1.grid(True, alpha=0.3, axis="y")

    # Panel B: measured detection rate per architecture, by attack category.
    #
    # This panel previously drew three series -- "Baseline", "Firewall Only"
    # and "Full CIF" -- of which only the third was measured.  "Baseline" was
    # a hardcoded list of zeros, and "Firewall Only" was the Full CIF value
    # multiplied by 0.80, so the "significant gap" the caption drew attention
    # to was exactly 20% by construction, in every category, for every run.
    #
    # What this panel is NOT: measured. An earlier repair here replaced one
    # fabrication with another, plotting detection_data.json as "measured" with
    # "the bootstrap intervals the artifact ships".  Neither half is true.
    # src/data/generate.py::generate_detection_data hardcodes a 4x4 base_means
    # matrix and adds N(0, 0.005); its `cis` are i.i.d. Uniform(0.008, 0.025)
    # draws with no resampling behind them and no relation to sample size.  The
    # only per-architecture-by-category artifact in the repo is a calibrated
    # model, so the panel says so and the fake intervals are not drawn at all --
    # an error bar asserts a sampling distribution, and there is none here.
    generated = _load_detection_data(output_dir)

    ax2 = axes[1]
    categories = generated["categories"]
    means = generated["means"]  # [arch][category]
    architectures = generated["architectures"]

    attack_types = [c.replace(" ", "\n") for c in categories]
    n_arch = len(means)
    logger.info(
        "Panel B: %d architectures x %d categories from the calibrated model "
        "(detection_data.json is generated, not measured)",
        n_arch,
        len(categories),
    )

    x = np.arange(len(attack_types))
    width = 0.8 / n_arch
    palette = [
        SEMANTIC_COLORS["firewall"],
        SEMANTIC_COLORS["sandbox"],
        SEMANTIC_COLORS["tripwire"],
        SEMANTIC_COLORS["full_cif"],
    ]
    for a, architecture in enumerate(architectures):
        offset = (a - (n_arch - 1) / 2) * width
        ax2.bar(
            x + offset,
            means[a],
            width,
            label=architecture,
            color=palette[a % len(palette)],
            edgecolor="black",
        )

    ax2.set_ylabel("Detection Rate", fontsize=12)
    ax2.set_title(
        "B. Calibrated Model: Detection Rate by Attack Type (not measured)",
        fontsize=12,
        fontweight="bold",
    )
    ax2.set_xticks(x)
    ax2.set_xticklabels(attack_types, fontsize=FONTSIZE["base"])
    # Four architectures put the legend on top of the tallest group; give it
    # its own band above the bars rather than letting it cover a data point.
    ax2.set_ylim(0, 1.32)
    ax2.legend(loc="upper center", ncol=4, fontsize=FONTSIZE["small"], frameon=False)
    ax2.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    add_source_annotation(fig, "src/visualization/figures/detection_performance.py")
    save_figure(fig, "detection_performance", output_dir=output_dir)
    return fig
