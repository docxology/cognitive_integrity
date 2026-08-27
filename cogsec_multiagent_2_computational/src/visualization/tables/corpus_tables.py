"""LaTeX tables for attack corpus composition.

Generates a table showing category, subcategory, count, and percentage
for the attack corpus.

Every count is measured from ``AttackCorpus.generate()`` at build time,
including the subtotals.  Subtotals are the trap here: a hand-typed
subcategory breakdown can disagree with the generator row by row while its
top-level sums still add up, so a table checked only at the totals passes
while most of its cells are wrong.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional

from .latex import escape_latex

if TYPE_CHECKING:  # pragma: no cover - typing only
    from attacks.corpus import AttackCorpus

# Corpus generation is deterministic given the seed; 42 is the canonical
# seed used by every other consumer of the corpus in this project.
CORPUS_SEED = 42


@dataclass(frozen=True)
class CorpusRow:
    """One measured ``(top category, subcategory, count)`` row."""

    category: str
    subcategory: str
    count: int


def _label(name: str) -> str:
    return escape_latex(name.replace("_", " ").title())


def corpus_rows(corpus: Optional["AttackCorpus"] = None) -> List[CorpusRow]:
    """Measure the corpus composition, preserving generation order.

    Parameters
    ----------
    corpus:
        A corpus to measure.  Generated with :data:`CORPUS_SEED` if *None*.

    Returns
    -------
    list of CorpusRow
        One row per ``(top category, subcategory)`` pair actually present,
        in first-appearance order so the table groups naturally without a
        hardcoded ordering list.
    """
    if corpus is None:
        from attacks.corpus import AttackCorpus

        corpus = AttackCorpus.generate(seed=CORPUS_SEED)

    order: List[tuple[str, str]] = []
    counts: dict[tuple[str, str], int] = {}
    for sample in corpus:
        key = (sample.category.top_category, sample.subcategory)
        if key not in counts:
            counts[key] = 0
            order.append(key)
        counts[key] += 1

    return [CorpusRow(cat, sub, counts[(cat, sub)]) for cat, sub in order]


def generate_corpus_table(corpus: Optional["AttackCorpus"] = None) -> str:
    """Generate a LaTeX table of the attack corpus composition.

    Parameters
    ----------
    corpus:
        A corpus to tabulate.  Generated with :data:`CORPUS_SEED` if *None*.

    Returns
    -------
    str
        Complete LaTeX table string showing the category breakdown.

    Raises
    ------
    ValueError
        If the corpus is empty; a percentage column over a zero total is
        undefined and a zero-row composition table would be misleading.
    """
    rows = corpus_rows(corpus)
    total = sum(r.count for r in rows)
    if total == 0:
        raise ValueError("attack corpus is empty; nothing to tabulate")

    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        f"\\caption{{Attack Corpus Composition ({total} Attacks). "
        f"Counts measured from \\texttt{{AttackCorpus.generate(seed={CORPUS_SEED})}}.}}",
        r"\label{tab:corpus}",
        r"\begin{tabular}{llrr}",
        r"\toprule",
        r"Category & Subcategory & Count & \% \\",
        r"\midrule",
    ]

    prev_cat: Optional[str] = None
    for row in rows:
        pct = row.count / total * 100
        if row.category != prev_cat:
            if prev_cat is not None:
                lines.append(r"\midrule")
            cat_display = _label(row.category)
            prev_cat = row.category
        else:
            cat_display = ""
        lines.append(
            f"{cat_display} & {_label(row.subcategory)} & {row.count} & {pct:.1f}\\% \\\\"
        )

    # Category subtotals, in the same first-appearance order.
    lines.append(r"\midrule")
    cat_order: List[str] = []
    cat_totals: dict[str, int] = {}
    for row in rows:
        if row.category not in cat_totals:
            cat_totals[row.category] = 0
            cat_order.append(row.category)
        cat_totals[row.category] += row.count

    for cat in cat_order:
        subtotal = cat_totals[cat]
        pct = subtotal / total * 100
        lines.append(
            f"\\textbf{{{_label(cat)}}} & \\textit{{Subtotal}} & "
            f"\\textbf{{{subtotal}}} & \\textbf{{{pct:.1f}\\%}} \\\\"
        )

    lines.extend([
        r"\midrule",
        f"\\textbf{{Total}} & & \\textbf{{{total}}} & \\textbf{{100.0\\%}} \\\\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ])

    return "\n".join(lines)
