"""LaTeX tables for ablation study results.

Generates tables for single-component removal impact and pairwise
synergy analysis.  Reads data from ablation_results.json.

Sign convention (audit MSC-12).  ``ablation_results.json`` defines

    delta_tpr = tpr_without_component - tpr_full_pipeline

so the full-pipeline rate is recovered by *subtracting* the delta from an
ablated row's rate, never by adding it.  An earlier version of this module
added, which reported ``Full CIF = 0.019`` against a real 0.122 and turned
every removal row into an apparent improvement -- the exact inverse of the
layered-defence claim.  :func:`_ablation_rows` now cross-checks every row
against ``full_pipeline.tpr`` and raises on disagreement, so the same
inversion cannot be reintroduced silently.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .binomial_ci import rate_to_successes, wilson_half_width
from .latex import escape_latex

logger = __import__('logging').getLogger(__name__)

_DATA_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "output" / "data" / "ablation_results.json"
)

# Rate/delta agreement tolerance.  The JSON stores full-precision floats, so
# the only slack needed is float round-off, not measurement slack.
_TOL = 1e-9

FULL_LABEL = "Full CIF"


@dataclass(frozen=True)
class AblationRow:
    """One row of the component-removal table.

    Attributes
    ----------
    label:
        Row label as printed (``"Full CIF"`` or ``"- Detection"``).
    tpr:
        True-positive rate for this configuration.
    delta_tpr:
        ``tpr - tpr_full``; ``None`` for the full-pipeline row.
    ci_half_width:
        Wilson 95% half-width, or ``None`` when the JSON does not record
        the sample size the rate was measured over.  ``None`` prints as
        ``--``; it is never replaced by a stand-in constant.
    """

    label: str
    tpr: float
    delta_tpr: Optional[float]
    ci_half_width: Optional[float]


@dataclass(frozen=True)
class SynergyPair:
    """One recorded pairwise-synergy measurement."""

    a: str
    b: str
    tpr_a: float
    tpr_b: float
    combined_tpr: float
    synergy: float


def _read_json(path: Optional[Path] = None) -> Dict[str, Any]:
    p = Path(path) if path is not None else _DATA_PATH
    with open(p, "r", encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)
    logger.info("Loaded ablation data from %s", p)
    return data


def _sample_size(data: Dict[str, Any]) -> Optional[int]:
    """Return the attack-sample size the rates were measured over, if recorded.

    ``run_full_ablation`` does not currently serialise it, so this returns
    ``None`` for the shipped artifact and the CI column prints ``--``.
    Both a top-level ``n_attacks`` and ``full_pipeline.n_attacks`` are
    honoured so the column lights up as soon as the runner records it.
    """
    for candidate in (data.get("n_attacks"), data.get("full_pipeline", {}).get("n_attacks")):
        if candidate is None:
            continue
        n = int(candidate)
        if n <= 0:
            raise ValueError(f"n_attacks must be positive, got {candidate!r}")
        return n
    return None


def _ci(rate: float, n: Optional[int]) -> Optional[float]:
    if n is None:
        return None
    return wilson_half_width(rate_to_successes(rate, n), n)


def _ablation_rows(data: Dict[str, Any]) -> List[AblationRow]:
    """Build the component-removal rows, validating the delta convention.

    Raises
    ------
    ValueError
        If ``component_removal`` is missing/empty, or if any row's
        ``tpr - delta_tpr`` disagrees with the full-pipeline rate.  That
        disagreement is exactly what a sign flip on either side produces,
        so it must fail rather than render.
    """
    removal_list = data.get("component_removal")
    if not removal_list:
        raise ValueError("ablation results contain no 'component_removal' entries")

    implied = [entry["tpr"] - entry["delta_tpr"] for entry in removal_list]

    if "full_pipeline" in data:
        full_tpr = float(data["full_pipeline"]["tpr"])
    else:
        full_tpr = float(implied[0])

    for entry, value in zip(removal_list, implied):
        if abs(value - full_tpr) > _TOL:
            raise ValueError(
                f"ablation row {entry['removed']!r} is inconsistent with the full "
                f"pipeline: tpr({entry['tpr']!r}) - delta_tpr({entry['delta_tpr']!r}) "
                f"= {value!r}, expected {full_tpr!r}. Either delta_tpr does not follow "
                "the 'removed minus full' convention or the rates are stale."
            )

    n = _sample_size(data)
    rows = [AblationRow(FULL_LABEL, full_tpr, None, _ci(full_tpr, n))]
    for entry in removal_list:
        label = f"- {entry['removed'].replace('_', ' ').title()}"
        rows.append(
            AblationRow(label, float(entry["tpr"]), float(entry["delta_tpr"]), _ci(entry["tpr"], n))
        )
    return rows


def _load_ablation_data(path: Optional[Path] = None) -> List[AblationRow]:
    """Load component-removal rows from ``ablation_results.json``."""
    return _ablation_rows(_read_json(path))


def _rows_from_mapping(results: Dict[str, Any]) -> List[AblationRow]:
    """Adapt the legacy ``{label: (rate, ci)}`` mapping to :class:`AblationRow`.

    The full-pipeline rate is taken from the ``"Full CIF"`` entry; deltas are
    computed against it.  A mapping without that entry cannot be rendered,
    because there would be nothing to take a delta against.
    """
    if FULL_LABEL not in results:
        raise ValueError(f"results mapping must contain a {FULL_LABEL!r} entry")

    full_rate = float(results[FULL_LABEL][0])
    rows: List[AblationRow] = []
    for name, value in results.items():
        rate = float(value[0])
        ci = None if len(value) < 2 or value[1] is None else float(value[1])
        delta = None if name == FULL_LABEL else rate - full_rate
        rows.append(AblationRow(name, rate, delta, ci))
    return rows


def _load_synergy_pairs(path: Optional[Path] = None) -> List[SynergyPair]:
    """Load the recorded pairwise synergies from ``ablation_results.json``.

    The JSON records only the *top* pairs (``get_top_synergies(n=5)``), not
    the full component x component matrix.  The previous implementation
    rendered a 5x5 matrix and printed ``0.000`` in every cell it had no
    measurement for, which asserts "these components do not interact" about
    pairs that were simply never written to the file.  Emitting the recorded
    pairs as rows says only what the data says.
    """
    data = _read_json(path)
    pairs = data.get("top_synergies", [])
    records = [
        SynergyPair(
            a=s["a"],
            b=s["b"],
            tpr_a=float(s["tpr_a"]),
            tpr_b=float(s["tpr_b"]),
            combined_tpr=float(s["combined_tpr"]),
            synergy=float(s["synergy"]),
        )
        for s in pairs
    ]
    # Deterministic strongest-first order that does not depend on dict or
    # file ordering; exact ties keep a stable alphabetical sub-order.
    records.sort(key=lambda r: (-r.synergy, r.a, r.b))
    return records


def _pretty(name: str) -> str:
    return escape_latex(name.replace("_", " ").title())


def generate_ablation_table(results: Optional[Dict] = None) -> str:
    """Generate a LaTeX table of ablation study results.

    Parameters
    ----------
    results : dict, optional
        Legacy mapping of config name to ``(detection_rate, ci)`` tuples.
        Loaded from ``output/data/ablation_results.json`` if *None*.

    Returns
    -------
    str
        Complete LaTeX table string.
    """
    rows = _rows_from_mapping(results) if results is not None else _load_ablation_data()

    # The CI column exists only when every rate has one.  When the ablation
    # runner does not record the sample size, there is no interval to print,
    # and a column of stand-in constants is worse than no column at all.
    with_ci = all(row.ci_half_width is not None for row in rows)

    caption = "Ablation Study: Detection Rate Impact of Component Removal"
    if with_ci:
        caption += ". CI is the Wilson 95\\% score-interval half-width"

    header = "Configuration & Detection Rate"
    if with_ci:
        header += r" & 95\% CI"
    header += r" & $\Delta$ Rate \\"

    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        f"\\caption{{{caption}.}}",
        r"\label{tab:ablation}",
        r"\begin{tabular}{l" + ("cc" if with_ci else "c") + "r}",
        r"\toprule",
        header,
        r"\midrule",
    ]

    for row in rows:
        cells = [escape_latex(row.label), f"{row.tpr:.3f}"]
        if with_ci:
            # mypy: `with_ci` already proves this is not None.
            cells.append(f"$\\pm {row.ci_half_width:.3f}$")  # type: ignore[str-format]
        if row.delta_tpr is None:
            cells.append("---")
        elif row.delta_tpr == 0.0:
            # An exactly-zero delta is a measured no-op, not a tiny gain;
            # "+0.000" would read as a sign it does not have.
            cells.append("0.000")
        else:
            cells.append(f"{row.delta_tpr:+.3f}")
        lines.append(" & ".join(cells) + r" \\")
        if row.label == FULL_LABEL:
            lines.append(r"\midrule")

    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ])

    return "\n".join(lines)


def generate_synergy_table(results: Optional[Dict] = None) -> str:
    """Generate a LaTeX table of the recorded pairwise component synergies.

    Parameters
    ----------
    results : dict, optional
        Unused; retained for signature compatibility.  Synergies are always
        read from ``output/data/ablation_results.json``.

    Returns
    -------
    str
        Complete LaTeX table string.
    """
    pairs = _load_synergy_pairs()

    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Recorded pairwise component synergies. "
        r"Synergy is the combined-pair TPR minus the sum of the two "
        r"single-component TPRs. Only the pairs serialised by the ablation "
        r"runner are listed; unlisted pairs were not measured, which is not "
        r"the same as measuring zero.}",
        r"\label{tab:synergy}",
        r"\begin{tabular}{llrrrr}",
        r"\toprule",
        r"Component A & Component B & TPR$_A$ & TPR$_B$ & TPR$_{A+B}$ & Synergy \\",
        r"\midrule",
    ]

    for p in pairs:
        lines.append(
            f"{_pretty(p.a)} & {_pretty(p.b)} & {p.tpr_a:.4f} & {p.tpr_b:.4f} & "
            f"{p.combined_tpr:.4f} & {p.synergy:+.4f} \\\\"
        )

    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ])

    return "\n".join(lines)
