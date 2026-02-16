"""LaTeX tables for attack corpus composition.

Generates a table showing category, subcategory, count, and percentage
for the full 950-attack corpus.
"""

from __future__ import annotations

_CORPUS = [
    ("Injection", "Direct Injection", 200),
    ("Injection", "Indirect Injection", 180),
    ("Injection", "Nested Injection", 120),
    ("Trust Exploitation", "Impersonation", 80),
    ("Trust Exploitation", "Trust Inflation", 70),
    ("Trust Exploitation", "Delegation Abuse", 50),
    ("Belief Manipulation", "Belief Drift", 60),
    ("Belief Manipulation", "Belief Fabrication", 50),
    ("Belief Manipulation", "Belief Injection", 40),
    ("Coordination", "Sybil Attack", 40),
    ("Coordination", "Consensus Poisoning", 35),
    ("Coordination", "Timing Attack", 25),
]

_TOTAL = 950


def generate_corpus_table() -> str:
    """Generate a LaTeX table of the attack corpus composition.

    Returns
    -------
    str
        Complete LaTeX table string showing category breakdown.
    """
    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Attack Corpus Composition (950 Attacks)}",
        r"\label{tab:corpus}",
        r"\begin{tabular}{llrr}",
        r"\toprule",
        r"Category & Subcategory & Count & \% \\",
        r"\midrule",
    ]

    prev_cat = None
    for cat, sub, count in _CORPUS:
        pct = count / _TOTAL * 100
        if cat != prev_cat:
            if prev_cat is not None:
                lines.append(r"\midrule")
            cat_display = cat
            prev_cat = cat
        else:
            cat_display = ""
        lines.append(f"{cat_display} & {sub} & {count} & {pct:.1f}\\% \\\\")

    # Category subtotals
    lines.append(r"\midrule")
    cat_totals = {}
    for cat, _, count in _CORPUS:
        cat_totals[cat] = cat_totals.get(cat, 0) + count

    for cat, total in cat_totals.items():
        pct = total / _TOTAL * 100
        lines.append(f"\\textbf{{{cat}}} & \\textit{{Subtotal}} & \\textbf{{{total}}} & \\textbf{{{pct:.1f}\\%}} \\\\")

    lines.extend([
        r"\midrule",
        f"\\textbf{{Total}} & & \\textbf{{{_TOTAL}}} & \\textbf{{100.0\\%}} \\\\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ])

    return "\n".join(lines)
