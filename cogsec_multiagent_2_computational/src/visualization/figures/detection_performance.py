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


#: The per-architecture-by-category artifact, written by
#: scripts/run_full_evaluation.py and provenanced as parametric_simulation.
_PARAMETRIC_PATH = (
    Path(__file__).resolve().parents[3] / "output" / "data" / "full_evaluation_results.json"
)

#: How the artifact's category keys are spelled in the figure.
_CATEGORY_LABEL = {
    "injection": "Injection",
    "trust_exploitation": "Trust Exploitation",
    "belief_manipulation": "Belief Manipulation",
    "coordination": "Coordination",
}


def _load_parametric_detection() -> tuple[list[str], list[str], list[list[float]], list[list[float]]]:
    """Detection rates and Wilson half-widths, per architecture and category.

    Fails closed. The defect being repaired is a panel that drew a matrix
    nothing computed, so a fallback to plausible values would put it straight
    back in a form that is harder to see than the original.
    """
    from visualization.tables.binomial_ci import wilson_half_width

    if not _PARAMETRIC_PATH.is_file():
        raise FileNotFoundError(
            f"{_PARAMETRIC_PATH} is missing; run scripts/run_full_evaluation.py. "
            f"This panel has no stand-in values."
        )
    rows = json.loads(_PARAMETRIC_PATH.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{_PARAMETRIC_PATH} records no rows")

    architectures: list[str] = []
    categories: list[str] = []
    for row in rows:
        if row["architecture"] not in architectures:
            architectures.append(row["architecture"])
        if row["category"] not in categories:
            categories.append(row["category"])

    index = {(r["architecture"], r["category"]): r for r in rows}
    missing = [
        (a, c) for a in architectures for c in categories if (a, c) not in index
    ]
    if missing:
        raise ValueError(f"{_PARAMETRIC_PATH} has no row for {missing}")

    means = [[index[(a, c)]["detection_rate"] for c in categories] for a in architectures]
    intervals = [
        [
            wilson_half_width(
                int(index[(a, c)]["true_positives"]), int(index[(a, c)]["n_attacks"])
            )
            for c in categories
        ]
        for a in architectures
    ]
    labels = [_CATEGORY_LABEL.get(c, c.replace("_", " ").title()) for c in categories]
    return architectures, labels, means, intervals


def _load_ablation_data(output_dir: Path) -> dict:
    """Read the ablation artifact, the source of every number in Panel A."""
    path = output_dir.parent / "data" / "ablation_results.json"
    if not path.exists():
        path = Path(__file__).resolve().parents[3] / "output" / "data" / "ablation_results.json"
    with open(path) as handle:
        return json.load(handle)


def plot_detection_performance(output_dir: str | Path = "output/figures") -> plt.Figure:
    """Generate detection performance comparison figure.

    Both panels read full_evaluation_results.json and ablation_results.json.
    Panel B used to read detection_data.json, a DataGenerator placeholder with
    no provenance and invented confidence intervals; that file is gone.
    """
    if isinstance(output_dir, str):
        output_dir = Path(output_dir)

    apply_style()
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # colors dict kept for documentation but unused in current impl

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
    defenses = ["Baseline"] + [m.replace("_", "\n").title() + "\nOnly"
                for m in mechanisms] + ["Full CIF"]

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
    # It used to read detection_data.json, which nothing produces: no
    # data_origin, no source_script, a 4x4 base_means matrix hardcoded in
    # src/data/generate.py with N(0, 0.005) noise added, and `cis` drawn
    # i.i.d. from Uniform(0.008, 0.025) with no resampling behind them and no
    # relation to any sample size. An earlier repair here stopped calling it
    # measured and stopped drawing the invented intervals, which was right as
    # far as it went; it still plotted a matrix nothing had computed.
    #
    # The panel now reads full_evaluation_results.json, which is the same
    # 4 x 4 shape, is produced by scripts/run_full_evaluation.py, and carries
    # per-cell counts. So the intervals can be real: Wilson on
    # true_positives out of n_attacks. They are narrow, because the parametric
    # arm evaluates 500 attacks per cell, and a narrow interval honestly
    # derived is worth more than a wide one invented.
    #
    # It is still not a measurement of a deployed system -- the artifact's
    # sidecar records parametric_simulation and the title says so.
    architectures, categories, means, intervals = _load_parametric_detection()

    ax2 = axes[1]
    attack_types = [c.replace(" ", "\n") for c in categories]
    n_arch = len(means)
    logger.info(
        "Panel B: %d architectures x %d categories from %s "
        "(parametric simulation, Wilson intervals on the per-cell counts)",
        n_arch,
        len(categories),
        _PARAMETRIC_PATH.name,
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
            yerr=intervals[a],
            capsize=2,
            error_kw={"elinewidth": 0.8, "ecolor": "#2C3E50"},
            label=architecture,
            color=palette[a % len(palette)],
            edgecolor="black",
        )

    ax2.set_ylabel("Detection Rate", fontsize=12)
    ax2.set_title(
        "B. Parametric Simulation: Detection Rate by Attack Type "
        "(95% Wilson CI; not a deployed measurement)",
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
