"""LaTeX tables for per-architecture detection rates.

Generates a formatted LaTeX table showing detection rates with Wilson 95%
score intervals for each architecture across every attack category present
in ``full_evaluation_results.json``.

Both the row labels (architectures) and the column labels (attack
categories) are derived from the data (audit REPRO-04).  They used to be
two hardcoded parallel lists -- ``_ARCHITECTURES`` and ``_CATEGORIES`` --
while the matrix columns came back in whatever order the loader produced,
so the column headed "Injection" carried the ``belief_drift`` measurements
and "Belief Manip." carried the n=500 ``indirect_injection`` measurements.

The "Overall" column pools the raw TP/FN counts rather than averaging the
per-category rates.  The categories have very unequal sample sizes
(500/200/150/100), so an unweighted mean of rates is not the
architecture's detection rate over its attacks.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from .binomial_ci import wilson_half_width
from .latex import escape_latex

logger = __import__('logging').getLogger(__name__)

_DATA_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "output" / "data" / "full_evaluation_results.json"
)

# Display names for the category strings that appear in the shipped data.
# These are subcategory labels; the evaluation measures one representative
# subcategory per top-level attack family, not the family as a whole.
# Unknown categories fall back to a title-cased form of the raw string, so
# an added category shows up rather than being dropped or mislabelled.
_CATEGORY_LABELS = {
    "indirect_injection": "Indirect Inj.",
    "impersonation": "Impersonation",
    "belief_drift": "Belief Drift",
    "sybil_attack": "Sybil Attack",
}

_Counts = Dict[Tuple[str, str], Tuple[int, int]]


def _category_label(cat: str) -> str:
    return escape_latex(_CATEGORY_LABELS.get(cat, cat.replace("_", " ").title()))


def _load_results(
    path: Optional[Path] = None,
) -> Tuple[List[str], List[str], np.ndarray, np.ndarray, _Counts, List[str]]:
    """Load the detection matrix, Wilson CIs, the raw TP/FN counts, and modes.

    Returns
    -------
    archs, cats, matrix, cis, counts, modes
        ``matrix[i, j]`` is the recorded detection rate and ``cis[i, j]``
        the Wilson 95% half-width derived from ``counts[(arch, cat)]``.
        ``modes`` is the sorted set of ``mode`` values on the rows -- the
        shipped artifact is entirely ``simulation``, which the caption must
        say rather than letting the reader assume live measurement.

    Raises
    ------
    ValueError
        If a recorded ``detection_rate`` disagrees with its own TP/FN
        counts.  A cell whose rate and counts contradict each other cannot
        be published either way, so this fails rather than silently
        preferring one of them.
    """
    from data.result_loaders import evaluation_to_detection_matrix

    data_path = Path(path) if path is not None else _DATA_PATH
    archs, cats, matrix = evaluation_to_detection_matrix(path=str(data_path))

    with open(data_path, "r", encoding="utf-8") as f:
        raw_rows = json.load(f)

    counts: _Counts = {}
    for r in raw_rows:
        counts[(r["architecture"], r["attack_category"])] = (
            int(r["true_positives"]),
            int(r["false_negatives"]),
        )

    cis = np.zeros(matrix.shape)
    for i, arch in enumerate(archs):
        for j, cat in enumerate(cats):
            tp, fn = counts.get((arch, cat), (0, 0))
            n = tp + fn
            if n <= 0:
                cis[i, j] = 0.0
                continue
            if abs(tp / n - matrix[i, j]) > 1e-9:
                raise ValueError(
                    f"detection_rate {matrix[i, j]!r} for ({arch}, {cat}) disagrees "
                    f"with its own counts tp={tp}, fn={fn} (tp/(tp+fn) = {tp / n!r})"
                )
            cis[i, j] = wilson_half_width(tp, n)

    modes = sorted({str(r["mode"]) for r in raw_rows if r.get("mode")})

    logger.info("Loaded detection data with Wilson CIs from %s", data_path)
    return archs, cats, matrix, cis, counts, modes


def generate_detection_table(results: Optional[Dict] = None) -> str:
    """Generate a LaTeX table of per-architecture detection rates.

    Parameters
    ----------
    results : dict, optional
        Explicit table contents with keys ``architectures``, ``categories``,
        ``means`` and ``cis``; an optional ``counts`` mapping
        ``(architecture, category) -> (tp, fn)`` enables the pooled Overall
        column.  Loaded from ``output/data/full_evaluation_results.json``
        if *None*.

    Returns
    -------
    str
        Complete LaTeX table string.
    """
    counts: _Counts = {}
    if results is not None:
        archs = list(results["architectures"])
        cats = list(results["categories"])
        means = np.asarray(results["means"], dtype=float)
        cis = np.asarray(results["cis"], dtype=float)
        counts = dict(results.get("counts", {}))
        modes = list(results.get("modes", []))
    else:
        archs, cats, means, cis, counts, modes = _load_results()

    labels = [_category_label(c) for c in cats]

    caption = (
        r"Detection Rates by Architecture and Attack Category "
        r"($\pm$ Wilson 95\% score-interval half-width). "
        r"Overall pools the raw TP/FN counts across categories."
    )
    if modes:
        caption += (
            " Evaluation mode: "
            + ", ".join(escape_latex(m) for m in modes)
            + "."
        )

    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        f"\\caption{{{caption}}}",
        r"\label{tab:detection-rates}",
        r"\begin{tabular}{l" + "c" * (len(cats) + 1) + "}",
        r"\toprule",
        r"Architecture & " + " & ".join(labels) + r" & Overall \\",
        r"\midrule",
    ]

    for i, arch in enumerate(archs):
        row_parts = [escape_latex(arch)]
        for j in range(len(cats)):
            row_parts.append(f"${means[i, j]:.3f} \\pm {cis[i, j]:.3f}$")

        tp_total = sum(counts.get((arch, cat), (0, 0))[0] for cat in cats)
        n_total = sum(sum(counts.get((arch, cat), (0, 0))) for cat in cats)
        if n_total > 0:
            overall = tp_total / n_total
            row_parts.append(f"${overall:.3f} \\pm {wilson_half_width(tp_total, n_total):.3f}$")
        else:
            row_parts.append("--")
        lines.append(" & ".join(row_parts) + r" \\")

    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ])

    return "\n".join(lines)
