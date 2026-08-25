"""The firewall's threshold, swept, and what tuning it buys.

The quarantine threshold is documented as the operator's tuning knob. Swept
against both arms it is flat across most of its range: every value from 0.25 to
0.75 produces the same true-positive rate and the same false-positive rate, so
the band an operator would actually tune in contains no distinguishable
operating points at all. Above 0.80 the firewall stops flagging.

Drawing the plateau is the point. A table of eleven identical rows reads as
repetition and invites the eye to skip; a flat line with its extent shaded
reads as a property of the system.

The right panel is the same sweep in ROC space, with the diagonal marked. The
curve sits below it, which is the second half of the finding: measured alone
against the hard benign corpus, this component flags more legitimate messages
than attacks at every threshold where it flags anything.
"""

from __future__ import annotations

from pathlib import Path

from matplotlib.figure import Figure

from ..artifact import annotate_provenance, load_artifact
from ..style import FONTSIZE, SEMANTIC_COLORS, create_figure, save_figure


def plot_operating_curve(output_dir: str | Path = "output/figures") -> Figure:
    """The quarantine-threshold sweep, as a curve and in ROC space."""
    payload = load_artifact(
        "threshold_sweep", required=("quarantine_sweep", "shipped", "quarantine_plateau")
    )
    sweep = sorted(payload["quarantine_sweep"], key=lambda p: p["tau"])
    taus = [p["tau"] for p in sweep]
    tprs = [p["tpr"] for p in sweep]
    fprs = [p["fpr"] for p in sweep]
    shipped_tau = payload["shipped"]["suspicious_threshold"]
    plateau = payload["quarantine_plateau"]

    # Cropped to the data. A y-axis to 1.0 devotes two thirds of the panel to
    # empty space and flattens the plateau into a line near the floor.
    ceiling = max(max(tprs), max(fprs)) * 1.35

    fig, axes = create_figure(width=11, height=4.4, n_rows=1, n_cols=2)
    rate_axis, roc_axis = axes

    if plateau:
        rate_axis.axvspan(
            plateau["tau_low"], plateau["tau_high"],
            color="#B0BEC5", alpha=0.35, zorder=0,
            label=f"flat: {plateau['tau_low']:.2f}–{plateau['tau_high']:.2f}",
        )
    rate_axis.plot(taus, tprs, "-o", color=SEMANTIC_COLORS["firewall"],
                   markersize=3.5, label="attacks flagged (TPR)")
    rate_axis.plot(taus, fprs, "-s", color=SEMANTIC_COLORS["attack"],
                   markersize=3.5, label="benign flagged (FPR)")
    rate_axis.axvline(shipped_tau, color="#2C3E50", linestyle=":", linewidth=1.4)
    rate_axis.text(
        shipped_tau + 0.012, ceiling * 0.97, rf"shipped $\tau_2={shipped_tau:g}$",
        fontsize=FONTSIZE["small"], color="#2C3E50", rotation=90, va="top",
    )
    rate_axis.set_xlabel(r"Quarantine threshold $\tau_2$", fontsize=FONTSIZE["base"])
    rate_axis.set_ylabel("Fraction flagged", fontsize=FONTSIZE["base"])
    rate_axis.set_title("A. Both arms across the sweep",
                        fontsize=FONTSIZE["base"] + 1, fontweight="bold")
    rate_axis.set_ylim(-0.01, ceiling)
    rate_axis.grid(True, alpha=0.3)
    rate_axis.set_axisbelow(True)
    rate_axis.legend(loc="upper right", fontsize=FONTSIZE["small"], frameon=False)

    roc_axis.plot([0, 1], [0, 1], "--", color="#95A5A6", linewidth=1.2, label="chance")
    roc_axis.plot(fprs, tprs, "-o", color=SEMANTIC_COLORS["firewall"], markersize=3.5)
    for point in sweep:
        if abs(point["tau"] - shipped_tau) < 1e-9:
            roc_axis.plot(point["fpr"], point["tpr"], "*", markersize=14,
                          color=SEMANTIC_COLORS["attack"], markeredgecolor="black",
                          label=r"shipped $\tau_2$", zorder=5)
    roc_axis.set_xlabel("False-positive rate", fontsize=FONTSIZE["base"])
    roc_axis.set_ylabel("True-positive rate", fontsize=FONTSIZE["base"])
    roc_axis.set_title("B. The same sweep in ROC space",
                       fontsize=FONTSIZE["base"] + 1, fontweight="bold")
    roc_axis.set_xlim(-0.02, 0.45)
    roc_axis.set_ylim(-0.02, 0.45)
    roc_axis.grid(True, alpha=0.3)
    roc_axis.set_axisbelow(True)
    roc_axis.legend(loc="lower right", fontsize=FONTSIZE["small"], frameon=False)

    fig.suptitle(
        "The firewall's threshold is not a usable knob",
        fontsize=FONTSIZE["base"] + 3, fontweight="bold", y=0.99,
    )
    fig.text(
        0.5, 0.925,
        "Measured on the firewall alone, against the hard benign corpus. "
        "A quarantined message costs a review, so it counts as flagged.",
        ha="center", fontsize=FONTSIZE["small"], style="italic", color="#5A6472",
    )
    fig.tight_layout(rect=(0, 0.035, 1, 0.90))
    annotate_provenance(fig, payload, "threshold_sweep.json")
    save_figure(fig, "operating_curve", output_dir=output_dir)
    return fig
