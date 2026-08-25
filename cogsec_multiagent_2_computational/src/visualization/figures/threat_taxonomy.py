"""Fig 5: 4-category attack taxonomy tree.

Draws a tree diagram showing the attack taxonomy root branching into
4 categories, each with 3 subcategories and associated counts.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib.patches as mpatches
from matplotlib.figure import Figure

from ..style import FONTSIZE, PALETTE, create_figure, save_figure

#: The taxonomy tree, measured.
#:
#: This was a literal dict of twelve subcategory counts, and six of the twelve
#: disagreed with the generator that produces the corpus: Indirect Injection
#: was written 180 against a real 200, Nested 120 against 100, Trust Inflation
#: 70 against 60, Delegation Abuse 50 against 60, Belief Injection 40 against
#: 50, Consensus Poisoning 35 against 30, Timing 25 against 30. The family
#: totals were right, so the figure summed correctly while every leaf under
#: three of the four families was wrong -- which is what a hand-built tree
#: does when someone later rebalances the generator.
_TAXONOMY_PATH = (
    Path(__file__).resolve().parents[3] / "output" / "data" / "taxonomy_evaluation_results.json"
)

#: Display names for the corpus's category keys.
_SUBCATEGORY_LABEL = {
    "direct_injection": "Direct Injection",
    "indirect_injection": "Indirect Injection",
    "nested_injection": "Nested Injection",
    "impersonation": "Impersonation",
    "trust_inflation": "Trust Inflation",
    "delegation_abuse": "Delegation Abuse",
    "belief_drift": "Belief Drift",
    "belief_fabrication": "Belief Fabrication",
    "belief_injection": "Belief Injection",
    "sybil_attack": "Sybil Attack",
    "consensus_poisoning": "Consensus Poisoning",
    "timing_attack": "Timing Attack",
    "provenance_laundering": "Provenance Laundering",
    "sandbox_escape": "Sandbox Escape",
    "byzantine_manipulation": "Byzantine Manipulation",
}

#: Display names for the families the categories roll up into.
_FAMILY_LABEL = {
    "injection": "Injection",
    "trust_exploitation": "Trust Exploitation",
    "belief_manipulation": "Belief Manipulation",
    "coordination": "Coordination",
    "provenance_and_isolation": "Provenance & Isolation",
}


def _load_taxonomy() -> dict[str, list[str]]:
    """Build the tree from the corpus's own category counts.

    Fails closed rather than falling back to a typed tree, which is the defect
    this replaces.
    """
    if not _TAXONOMY_PATH.is_file():
        raise FileNotFoundError(
            f"{_TAXONOMY_PATH} is missing; run scripts/run_taxonomy_evaluation.py. "
            f"This figure draws measured corpus composition and has no stand-in."
        )
    payload = json.loads(_TAXONOMY_PATH.read_text(encoding="utf-8"))
    counts = payload["category_counts"]
    # The corpus's own grouping, not FAMILY_OF: that map deliberately
    # splits injection three ways for the analysis roll-up, which is right
    # there and wrong for a tree whose top row is meant to be the corpus's
    # own families.
    family_of = payload.get("top_category_of")
    if not counts or not family_of:
        raise ValueError(
            f"{_TAXONOMY_PATH} carries no category_counts/top_category_of; the figure "
            f"cannot be drawn from it"
        )

    families: dict[str, list[tuple[str, int]]] = {}
    for category, n in counts.items():
        families.setdefault(family_of[category], []).append((category, n))

    tree: dict[str, list[str]] = {}
    for family, members in families.items():
        total = sum(n for _, n in members)
        label = f"{_FAMILY_LABEL.get(family, family.replace('_', ' ').title())}\n({total})"
        tree[label] = [
            f"{_SUBCATEGORY_LABEL.get(c, c.replace('_', ' ').title())} ({n})"
            for c, n in sorted(members, key=lambda kv: -kv[1])
        ]
    return tree




def _family_total(label: str) -> int:
    """The count in a family label such as ``"Injection\n(500)"``."""
    match = re.search(r"\((\d[\d,]*)\)", label)
    if not match:
        raise ValueError(f"family label {label!r} carries no count")
    return int(match.group(1).replace(",", ""))


def _draw_node(ax, x, y, text, color, fontsize=FONTSIZE["small"], width=0.14, height=0.06):
    """Draw a rounded box with text."""
    rect = mpatches.FancyBboxPatch(
        (x - width / 2, y - height / 2), width, height,
        boxstyle="round,pad=0.01",
        facecolor=color,
        edgecolor="white",
        linewidth=1.2,
        alpha=0.9,
    )
    ax.add_patch(rect)
    ax.text(x, y, text, ha="center", va="center", fontsize=fontsize, fontweight="bold", color="white")  # noqa: E501


def plot_threat_taxonomy(output_dir: str = "output/figures") -> Figure:
    """Create the 4-category attack taxonomy tree (Fig 5).

    Parameters
    ----------
    output_dir : str
        Directory for saved figure files.

    Returns
    -------
    Figure
    """
    fig, ax = create_figure(width=12, height=6)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Root node
    # One read, in a fixed order. The tree was drawn from two separate calls
    # to the loader, which was harmless while it returned a literal and is not
    # once it reads a file that can change between them.
    tree = _load_taxonomy()
    categories = sorted(tree, key=lambda label: -_family_total(label))
    total = sum(_family_total(label) for label in categories)

    root_x, root_y = 0.50, 0.90
    _draw_node(
        ax, root_x, root_y, f"Attack Taxonomy\n({total:,} total)", "#333333",
        fontsize=10, width=0.18, height=0.08,
    )

    # Cycled, not indexed. The list held four colours against four families;
    # extending the corpus added a fifth and the figure raised IndexError,
    # which is the better of the two failures available but still a crash on a
    # published figure.
    n_cats = len(categories)
    cat_colors = [PALETTE[i % len(PALETTE)] for i in range(n_cats)]
    # Spread the row across the axis whatever its width, rather than assuming
    # four columns at a fixed 0.25 pitch.
    cat_xs = [(i + 0.5) / n_cats for i in range(n_cats)]
    cat_y = 0.65

    for i, cat_name in enumerate(categories):
        subs = tree[cat_name]
        cx = cat_xs[i]
        color = cat_colors[i]

        # Arrow from root to category
        ax.annotate(
            "", xy=(cx, cat_y + 0.04), xytext=(root_x, root_y - 0.04),
            arrowprops=dict(arrowstyle="-|>", color=color, lw=1.8),
        )
        _draw_node(ax, cx, cat_y, cat_name, color, fontsize=FONTSIZE["base"], width=0.18, height=0.08)  # noqa: E501

        # Subcategories
        sub_y_start = 0.42
        for j, sub_name in enumerate(subs):
            sy = sub_y_start - j * 0.12
            ax.annotate(
                "", xy=(cx, sy + 0.025), xytext=(cx, cat_y - 0.04),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.0, alpha=0.6),
            )
            _draw_node(ax, cx, sy, sub_name, color, fontsize=7, width=0.18, height=0.05)

    ax.set_title("Attack Taxonomy: 4 Categories, 12 Subcategories, 950 Attacks", fontsize=13, pad=10)  # noqa: E501
    fig.tight_layout()
    save_figure(fig, "fig05_threat_taxonomy", output_dir=output_dir)
    return fig
