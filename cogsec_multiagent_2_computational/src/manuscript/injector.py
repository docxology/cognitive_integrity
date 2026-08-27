"""Manuscript value injection from validated data files.

Reads output/data/*.json ground truth and programmatically updates
manuscript files to ensure numeric claims match the data.

All operations are idempotent — running twice produces no changes.

Data sources:
  - full_evaluation_results.json  → parametric simulation (→ S08)
  - ablation_results.json         → real pipeline ablation (→ 05d, 06)
  - statistical_results.json      → parametric stats (→ S08)
  - multi_seed_results.json       → real pipeline stability (→ 05, 05b, 04, 06, 07, abstract)
  - llm_demo_results.json         → real LLM validation (→ 05, 04, 03b, abstract)
  - colony_results.json           → real colony benchmarks (→ 05, abstract)

Fail-closed contract
--------------------
This module never invents a number. A value is substituted into the
manuscript **only** when it was measured and read out of a data file:

* A missing data file, a file whose ``status`` says the run did not happen
  (``skipped`` / ``ollama_unavailable`` / ``timeout`` / ...), or a file that
  lacks the expected results block, makes the dependent manuscript claims
  *unbacked*. Unbacked claims are recorded and left untouched — they are
  never filled from a default.
* ``inject_all`` raises :class:`GroundTruthUnavailableError` when any claim
  it was asked to maintain is unbacked (``strict=True``, the default).
* A substitution pattern that matches **zero** times is an error, not a
  silent no-op: those are collected as *misses* and raised as
  :class:`InjectionPatternError`. "No changes needed" is only reported when
  every pattern matched and the resulting text was already correct.

Provenance is carried in ``ground_truth["_provenance"]`` and is what the
log tags (``[REAL]`` / ``[PARAMETRIC]`` / ``[UNAVAILABLE]``) are derived
from, so a fallback can never be printed as a measurement.

Prose is not restyled
---------------------
A substitution replaces the **number** and nothing else. Where the
manuscript writes a LaTeX qualifier before a maintained value
(``= -0.051`` vs ``\\approx -0.051``), the qualifier is captured and
written back unchanged, so re-running the injector never converts an
"approximately" claim into an exact one (or vice versa). Signs are
likewise taken from the data (``{:+.3f}``) rather than assumed negative.
"""

from __future__ import annotations

import json
import logging
import math
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

#: Statuses a producer script writes to say "this run produced no measurements".
UNAVAILABLE_STATUSES = frozenset(
    {"skipped", "ollama_unavailable", "timeout", "error", "failed", "unavailable"}
)

#: Provenance tags.
PROV_MEASURED = "measured"
PROV_UNAVAILABLE = "unavailable"

#: Normal-approximation z for a two-sided 95% interval.
_Z95 = 1.959963984540054

#: Tolerance when cross-checking detection_rate against true/false positives.
_RATE_TOLERANCE = 1e-6

#: Two synergy scores closer than this are treated as tied. The ablation
#: corpus has N=98 attacks, so the measurement resolution is 1/98 ≈ 0.0102;
#: anything below 1e-9 apart is the same measured value re-derived through a
#: different floating-point path, not a real ordering.
_SYNERGY_TIE_TOLERANCE = 1e-9

#: LaTeX qualifier that may sit between a claim's name and its number
#: ("= -0.051", "\approx -0.051", "\sim -0.051", or nothing at all). Captured
#: and written back verbatim so the injector maintains values, not wording.
_QUALIFIER = r"(?:=|\\\\approx|\\\\sim|\\approx|\\sim)?\s*"


class GroundTruthUnavailableError(RuntimeError):
    """Raised when a manuscript claim has no measured value behind it."""


class InjectionPatternError(RuntimeError):
    """Raised when a substitution pattern matched zero times."""


def _tied_top_synergies(synergies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Every synergy pair sharing the maximum score, in input order.

    Returns a single-element list when there is a clear winner. A longer list
    means the data does not distinguish those pairs and the manuscript must
    not claim it does.
    """
    if not synergies:
        return []
    best = max(float(s["synergy"]) for s in synergies)
    return [s for s in synergies if abs(float(s["synergy"]) - best) <= _SYNERGY_TIE_TOLERANCE]


def _format_pair(synergy: dict[str, Any]) -> str:
    """Render a synergy pair the way the manuscript names components."""
    return (
        f"{str(synergy['a']).replace('_', ' ').title()} + "
        f"{str(synergy['b']).replace('_', ' ').title()}"
    )


def _component_display_name(removed: str) -> str:
    """Manuscript spelling of an ablation component name."""
    if removed == "detection":
        return "Detection module"
    return removed.replace("_", " ").title()


def _component_hierarchy(components: list[dict[str, Any]]) -> str:
    """Render the component-importance chain, using ``$\\gg$`` for the first (largest)
    gap, ``$>$`` for subsequent non-tied gaps, and ``$\\approx$`` for measured ties.

    ``component_removal`` arrives ordered most-harmful-first. Joining it with
    ``$>$`` throughout would claim a strict ranking between components whose
    ``delta_tpr`` is bit-for-bit identical, which the ablation corpus cannot
    distinguish. Tied neighbours are joined with ``$\\approx$`` instead.
    """
    if not components:
        return ""
    parts = [_component_display_name(components[0]["removed"])]
    for i, (previous, current) in enumerate(zip(components, components[1:])):
        tied = float(previous["delta_tpr"]) == float(current["delta_tpr"])
        if tied:
            parts.append(r"$\\approx$")
        elif i == 0:
            parts.append(r"$\\gg$")
        else:
            parts.append("$>$")
        parts.append(_component_display_name(current["removed"]))
    return " ".join(parts)


def _component_baseline_tpr(components: list[dict[str, Any]]) -> float:
    """Recover the full-pipeline TPR from component-removal rows."""
    if not components:
        return 0.0
    baselines = [
        float(component["tpr"]) - float(component["delta_tpr"])
        for component in components
    ]
    return sum(baselines) / len(baselines)


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


@dataclass
class InjectionReport:
    """Accumulates what an injection run actually did.

    ``substitutions`` records ``(document, label, n_matches)`` for every
    pattern that fired. ``misses`` records ``(document, label, pattern)``
    for every pattern that matched zero times. ``unbacked`` records
    ``(document, label, reason)`` for every claim that was skipped because
    no measured value exists.
    """

    substitutions: list[tuple[str, str, int]] = field(default_factory=list)
    misses: list[tuple[str, str, str]] = field(default_factory=list)
    unbacked: list[tuple[str, str, str]] = field(default_factory=list)

    @property
    def n_substitutions(self) -> int:
        """Total number of pattern matches replaced."""
        return sum(count for _, _, count in self.substitutions)

    @property
    def ok(self) -> bool:
        """True when every pattern matched and every claim was backed."""
        return not self.misses and not self.unbacked

    def record_match(self, document: str, label: str, count: int) -> None:
        """Record a pattern that matched ``count`` (>0) times."""
        self.substitutions.append((document, label, count))

    def record_miss(self, document: str, label: str, pattern: str) -> None:
        """Record a pattern that matched zero times."""
        self.misses.append((document, label, pattern))
        logger.error(
            "%s: substitution %r matched 0 times — manuscript drifted away "
            "from the injector pattern %s",
            document,
            label,
            pattern,
        )

    def record_unbacked(self, document: str, label: str, reason: str) -> None:
        """Record a claim left untouched because no measured value exists."""
        self.unbacked.append((document, label, reason))
        logger.error(
            "%s: claim %r is UNBACKED (%s) — no value substituted",
            document,
            label,
            reason,
        )

    def raise_if_failed(self, *, strict: bool = True) -> None:
        """Raise if the run was not clean.

        Parameters
        ----------
        strict : bool
            When True (default) unbacked claims raise
            :class:`GroundTruthUnavailableError`. When False they are only
            reported. Zero-match patterns always raise
            :class:`InjectionPatternError`.
        """
        if strict and self.unbacked:
            detail = "; ".join(
                f"{doc}:{label} ({reason})" for doc, label, reason in self.unbacked
            )
            # Mention the misses too: this branch pre-empts InjectionPatternError,
            # so without this the pattern failures would be invisible to whoever
            # reads the traceback.
            also = (
                f" ({len(self.misses)} substitution pattern(s) also matched zero times)"
                if self.misses
                else ""
            )
            raise GroundTruthUnavailableError(
                f"{len(self.unbacked)} manuscript claim(s) have no measured "
                f"value behind them: {detail}{also}"
            )
        if self.misses:
            detail = "; ".join(
                f"{doc}:{label} (pattern {pattern!r})"
                for doc, label, pattern in self.misses
            )
            raise InjectionPatternError(
                f"{len(self.misses)} substitution pattern(s) matched zero "
                f"times: {detail}"
            )


def _resolve_report(report: InjectionReport | None) -> tuple[InjectionReport, bool]:
    """Return ``(report, owns_report)`` for a public injection entry point."""
    if report is None:
        return InjectionReport(), True
    return report, False


def _apply(
    text: str,
    pattern: str,
    repl: str,
    *,
    document: str,
    label: str,
    report: InjectionReport,
) -> str:
    """Substitute ``pattern`` in ``text``, recording a miss when it never matched."""
    new_text, count = re.subn(pattern, repl, text)
    if count == 0:
        report.record_miss(document, label, pattern)
    else:
        report.record_match(document, label, count)
    return new_text


def _apply_detection_delta(
    text: str,
    gt: dict,
    *,
    document: str,
    report: InjectionReport,
) -> str:
    r"""Maintain every numeric ``\Delta\text{TPR}`` detection claim in a document.

    Six manuscript files state this one number, and three of them state it
    more than once (body prose plus a figure caption). Driving them all from a
    single pattern is what stops them drifting apart when the ablation is
    re-run. The sign comes from the data, so a delta that turned positive
    would be reported as positive rather than silently negated.

    The match is anchored on a preceding capitalised "Detection" in the *same
    sentence* (``[^.]`` cannot cross a full stop). Without that anchor the
    pattern is claim-agnostic and will happily overwrite another component's
    delta with the detection figure — 04_experimental_setup.md states the
    trust-calculus delta in exactly this notation.
    """
    return _apply(
        text,
        r"(Detection[^.]{0,300}?\\Delta\\text\{TPR\}\s*" + _QUALIFIER + r")[-+][\d.]+",
        r"\g<1>" + f"{gt['detection_delta']:+.3f}",
        document=document,
        label="detection_delta",
        report=report,
    )


def _apply_top_synergy_value(
    text: str,
    gt: dict,
    lead_in: str,
    *,
    document: str,
    report: InjectionReport,
) -> str:
    """Maintain the top synergy score behind ``lead_in`` (a regex fragment).

    Two prose shapes carry this number.  The original names one pair and puts
    the score in a trailing parenthetical (``... strongest synergy ($\\approx
    +0.031$)``).  Since the measurement is an exact tie between two pairs, the
    honest phrasing instead names both and writes ``both $\\approx +0.031$``.
    Both must stay injectable: a substitution that silently stops matching is a
    dead write path, and the injector's own audit treats that as a failure.
    """
    single = r"(" + lead_in + r"\s*\(\$\s*" + _QUALIFIER + r")\+[\d.]+"
    # "both" when two pairs tie, "all at" when three or more do. The size of
    # the tie is a property of the artifact, so the pattern must not fix the
    # wording to one of them: when the tie widened from two pairs to three the
    # sentence changed and this substitution stopped matching, which the
    # injector's own audit reports as a dead write path.
    tie = r"((?:both|all at)\s*\$\s*" + _QUALIFIER + r")\+[\d.]+"
    pattern = single if re.search(single, text) else tie
    return _apply(
        text,
        pattern,
        r"\g<1>" + f"+{gt['top_synergy']['synergy']:.3f}",
        document=document,
        label="top_synergy_value",
        report=report,
    )


def _finish(
    path: Path,
    text: str,
    original: str,
    dry_run: bool,
    document: str,
) -> bool:
    """Write ``text`` when it changed; log the outcome. Returns True if modified."""
    if text != original:
        logger.info("%s: updated", document)
        if not dry_run:
            path.write_text(text)
        return True
    logger.info("%s: already matches data", document)
    return False


# ---------------------------------------------------------------------------
# Ground truth loading (fail-closed)
# ---------------------------------------------------------------------------


def _payload_status(payload: dict[str, Any]) -> str:
    """Normalised ``status`` field of a results payload ('' when absent)."""
    return str(payload.get("status", "")).strip().lower()


def _read_json_object(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    """Read a JSON object, returning ``(payload, reason_unavailable)``."""
    if not path.exists():
        return None, f"{path.name} not found"
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return None, f"{path.name} is not valid JSON ({exc})"
    if not isinstance(payload, dict):
        return None, f"{path.name} is not a JSON object"
    status = _payload_status(payload)
    if status in UNAVAILABLE_STATUSES:
        reason = payload.get("reason") or "no reason recorded"
        return None, f"{path.name} reports status={status!r} ({reason})"
    return payload, None


_LLM_ARCHITECTURES: tuple[tuple[str, str], ...] = (
    ("claude_code", "llm_claude"),
    ("crewai", "llm_crewai"),
)

_LLM_REQUIRED_FIELDS: tuple[tuple[str, str], ...] = (
    ("detection_rate", "dr"),
    ("true_positives", "tp"),
    ("false_negatives", "fn"),
    ("total", "total"),
)


def _load_llm_ground_truth(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    """Load measured LLM validation values, or explain why there are none.

    Returns ``(values, None)`` on success and ``(None, reason)`` otherwise.
    There is no fallback: an unavailable LLM run yields no numbers at all.
    """
    payload, reason = _read_json_object(path)
    if payload is None:
        return None, reason

    multi = payload.get("multiagent_results")
    if not isinstance(multi, dict) or not multi:
        return None, (
            f"{path.name} has no populated 'multiagent_results' block "
            f"(keys present: {sorted(payload)})"
        )

    values: dict[str, Any] = {}
    for slug, prefix in _LLM_ARCHITECTURES:
        arch = multi.get(slug)
        if not isinstance(arch, dict):
            return None, f"{path.name}: 'multiagent_results.{slug}' missing or not an object"
        for field_name, suffix in _LLM_REQUIRED_FIELDS:
            if field_name not in arch:
                return None, (
                    f"{path.name}: 'multiagent_results.{slug}' missing '{field_name}'"
                )
            values[f"{prefix}_{suffix}"] = arch[field_name]

        total = int(values[f"{prefix}_total"])
        true_pos = int(values[f"{prefix}_tp"])
        false_neg = int(values[f"{prefix}_fn"])
        rate = float(values[f"{prefix}_dr"])
        if total <= 0:
            return None, f"{path.name}: 'multiagent_results.{slug}.total' must be > 0"
        if true_pos + false_neg != total:
            return None, (
                f"{path.name}: 'multiagent_results.{slug}' inconsistent — "
                f"true_positives + false_negatives = {true_pos + false_neg} != total {total}"
            )
        if abs(rate - true_pos / total) > _RATE_TOLERANCE:
            return None, (
                f"{path.name}: 'multiagent_results.{slug}' inconsistent — "
                f"detection_rate {rate} != true_positives/total {true_pos / total}"
            )

    claude_total = int(values["llm_claude_total"])
    crewai_total = int(values["llm_crewai_total"])
    values["llm_n_per_arch"] = claude_total
    values["llm_total_n"] = claude_total + crewai_total
    return values, None


#: Human-readable name of the interval ``multi_seed_ci_halfwidth`` describes.
#: The manuscript must describe the published CI in exactly these terms.
MULTI_SEED_CI_METHOD = (
    "normal approximation on the mean of the per-seed detection rates "
    "(mean ± 1.959964 · s / √k, s = sample SD across seeds, ddof=1)"
)


def _load_multi_seed_ground_truth(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    """Load measured multi-seed values, or explain why there are none.

    Confidence interval
    -------------------
    ``multi_seed_ci_halfwidth`` is the half-width of a two-sided 95% interval
    on the **seed-level mean**, computed by normal approximation:

        mean ± z₀.₉₇₅ · s / √k

    where ``k`` is the number of seeds and ``s`` is the sample standard
    deviation across seeds (``ddof=1``). Nothing here is a constant: change
    the seed spread and the half-width moves.

    Why this interval and not a binomial one on the pooled counts. The
    published quantity is the mean detection rate *across seeds*, and the
    dominant uncertainty is seed-to-seed variation in the pipeline itself
    (stochastic detection scoring, cross-validation subsampling) — not
    sampling error inside any one seed's corpus. A Wilson or Wald interval on
    the pooled evaluation events treats them as i.i.d. Bernoulli draws and
    discards the between-seed component entirely, which on the current data
    understates the half-width by a factor of ~2.8 (0.00563 vs 0.01576). A
    bootstrap over the seed means was rejected because at k = 30 it only adds
    resampling noise; it relaxes no assumption that matters at this k.

    The interval is therefore *not* valid as a statement about a single seed,
    and the manuscript must not present it as one.
    """
    payload, reason = _read_json_object(path)
    if payload is None:
        return None, reason

    seed_metrics = payload.get("seed_metrics")
    if not isinstance(seed_metrics, list) or not seed_metrics:
        return None, f"{path.name} has an empty or missing 'seed_metrics' list"

    rates = [float(m["overall"]) for m in seed_metrics if isinstance(m, dict) and "overall" in m]
    if not rates:
        return None, f"{path.name}: no 'seed_metrics' entry carries an 'overall' rate"

    mean = sum(rates) / len(rates)
    values: dict[str, Any] = {
        "multi_seed_mean_dr": mean,
        "multi_seed_min_dr": min(rates),
        "multi_seed_max_dr": max(rates),
        "multi_seed_n": int(payload.get("n_seeds", len(rates))),
    }
    if "overall_cv" in payload:
        values["multi_seed_cv"] = float(payload["overall_cv"])
    elif mean > 0 and len(rates) > 1:
        variance = sum((r - mean) ** 2 for r in rates) / (len(rates) - 1)
        values["multi_seed_cv"] = math.sqrt(variance) / mean
    else:
        return None, f"{path.name}: cannot determine 'overall_cv' and cannot derive it"

    if len(rates) > 1:
        variance = sum((r - mean) ** 2 for r in rates) / (len(rates) - 1)
        values["multi_seed_ci_halfwidth"] = _Z95 * math.sqrt(variance / len(rates))
        values["multi_seed_ci_method"] = MULTI_SEED_CI_METHOD
    return values, None


def load_ground_truth(data_dir: Path) -> dict[str, Any]:
    """Load all data files and compute ground truth values.

    Optional sources (multi-seed, LLM, colony) are fail-closed: when they are
    missing or report a non-success status, **no numeric value is produced**
    for them. Availability is reported through ``ground_truth["_provenance"]``
    and ``ground_truth["_unavailable"]``.

    Parameters
    ----------
    data_dir : Path
        Directory containing the JSON data files.

    Returns
    -------
    dict
        Ground truth values keyed by metric name.
    """
    gt: dict[str, Any] = {}
    provenance: dict[str, str] = {}
    unavailable: dict[str, str] = {}
    gt["_provenance"] = provenance
    gt["_unavailable"] = unavailable

    # --- Full evaluation results (parametric, required) ---
    with open(data_dir / "full_evaluation_results.json") as f:
        full_eval = json.load(f)

    arch_rates: dict[str, list[float]] = defaultdict(list)
    for e in full_eval:
        arch_rates[e["architecture"]].append(e["detection_rate"])

    all_rates = [e["detection_rate"] for e in full_eval]
    gt["parametric_overall_dr_mean"] = sum(all_rates) / len(all_rates)
    gt["parametric_autogpt_dr_mean"] = sum(arch_rates["AutoGPT"]) / len(arch_rates["AutoGPT"])
    gt["parametric_autogpt_dr_min"] = min(arch_rates["AutoGPT"])
    gt["parametric_autogpt_dr_max"] = max(arch_rates["AutoGPT"])
    gt["parametric_n"] = len(full_eval)
    provenance["parametric"] = PROV_MEASURED

    # --- Ablation results (real pipeline, required) ---
    with open(data_dir / "ablation_results.json") as f:
        ablation = json.load(f)

    gt["ablation_components"] = ablation["component_removal"]
    gt["detection_delta"] = next(
        c["delta_tpr"] for c in ablation["component_removal"] if c["removed"] == "detection"
    )
    gt["firewall_delta"] = next(
        c["delta_tpr"] for c in ablation["component_removal"] if c["removed"] == "firewall"
    )
    gt["full_pipeline_tpr"] = _component_baseline_tpr(ablation["component_removal"])
    gt["top_synergy"] = ablation["top_synergies"][0]
    # The pipeline can produce exact ties (every ablation figure is a multiple
    # of 1/N_attacks). Taking [0] and calling it "the strongest" would invent a
    # ranking the data does not contain, so record every pair that shares the
    # maximum and let the prose substitution pluralise.
    gt["top_synergy_ties"] = _tied_top_synergies(ablation["top_synergies"])
    provenance["ablation"] = PROV_MEASURED

    # --- Statistical results (parametric-derived, required) ---
    with open(data_dir / "statistical_results.json") as f:
        stats = json.load(f)

    gt["cohens_d"] = stats["cohens_d_cif_vs_baseline"]
    gt["kw_h"] = stats["kruskal_wallis"]["h"]
    gt["kw_p"] = stats["kruskal_wallis"]["p"]
    provenance["statistical"] = PROV_MEASURED

    # --- Multi-seed results (real pipeline, optional, fail-closed) ---
    ms_values, ms_reason = _load_multi_seed_ground_truth(data_dir / "multi_seed_results.json")
    if ms_values is None:
        provenance["multi_seed"] = PROV_UNAVAILABLE
        unavailable["multi_seed"] = ms_reason or "unknown"
        logger.warning("Multi-seed ground truth unavailable: %s", ms_reason)
    else:
        provenance["multi_seed"] = PROV_MEASURED
        gt.update(ms_values)

    # --- LLM demo results (real LLM, optional, fail-closed) ---
    llm_values, llm_reason = _load_llm_ground_truth(data_dir / "llm_demo_results.json")
    if llm_values is None:
        provenance["llm"] = PROV_UNAVAILABLE
        unavailable["llm"] = llm_reason or "unknown"
        logger.warning("LLM ground truth unavailable: %s", llm_reason)
    else:
        provenance["llm"] = PROV_MEASURED
        gt.update(llm_values)

    # --- Colony results (real benchmarks, optional, fail-closed) ---
    colony_path = data_dir / "colony_results.json"
    if colony_path.exists():
        with open(colony_path) as f:
            colony = json.load(f)
        gt["colony_scenarios"] = colony if isinstance(colony, list) else colony.get("scenarios", [])
        provenance["colony"] = PROV_MEASURED
    else:
        # Fail closed: no key at all, so a consumer cannot mistake an outage
        # for "the benchmarks ran and found nothing".
        provenance["colony"] = PROV_UNAVAILABLE
        unavailable["colony"] = f"{colony_path.name} not found"
        logger.warning("Colony ground truth unavailable: %s", unavailable["colony"])

    return gt


def is_available(gt: dict, source: str) -> bool:
    """True when ``source`` was measured (never true for a fallback)."""
    return gt.get("_provenance", {}).get(source) == PROV_MEASURED


def unavailable_reason(gt: dict, source: str) -> str:
    """Human-readable reason ``source`` has no measured values."""
    return gt.get("_unavailable", {}).get(source, f"{source} unavailable")


def format_pct(val: float, decimals: int = 1) -> str:
    """Format a fraction as a percentage string (e.g. 0.974 → '97.4')."""
    return f"{val * 100:.{decimals}f}"


# ---------------------------------------------------------------------------
# Per-document injection
# ---------------------------------------------------------------------------


def inject_abstract(
    gt: dict,
    manuscript_dir: Path,
    dry_run: bool = False,
    *,
    report: InjectionReport | None = None,
) -> bool:
    """Update 00_abstract.md with ground truth values.

    Returns True if the file was modified.
    """
    report, owns = _resolve_report(report)
    document = "00_abstract.md"
    path = manuscript_dir / document
    text = path.read_text()
    original = text

    if is_available(gt, "multi_seed"):
        ms_pct = format_pct(gt["multi_seed_mean_dr"], 1)
        text = _apply(
            text,
            r"mean detection rate of \d+\.\d+\\%",
            f"mean detection rate of {ms_pct}\\%",
            document=document,
            label="multi_seed_mean_dr",
            report=report,
        )
    else:
        report.record_unbacked(
            document, "multi_seed_mean_dr", unavailable_reason(gt, "multi_seed")
        )

    # LLM detection range — only when a real LLM run produced measurements.
    if is_available(gt, "llm"):
        llm_lo = int(gt["llm_claude_dr"] * 100)
        llm_hi = int(gt["llm_crewai_dr"] * 100)
        text = _apply(
            text,
            r"achieving \d+--\d+\\% detection across",
            f"achieving {llm_lo}--{llm_hi}\\% detection across",
            document=document,
            label="llm_detection_range",
            report=report,
        )
    else:
        report.record_unbacked(document, "llm_detection_range", unavailable_reason(gt, "llm"))

    if "multi_seed_ci_halfwidth" in gt:
        ms_mean = gt["multi_seed_mean_dr"]
        half = gt["multi_seed_ci_halfwidth"]
        text = _apply(
            text,
            r"\[95\\% CI: \d+\.\d+\\%, \d+\.\d+\\%\]",
            f"[95\\% CI: {format_pct(ms_mean - half, 1)}\\%, {format_pct(ms_mean + half, 1)}\\%]",
            document=document,
            label="multi_seed_ci",
            report=report,
        )
    else:
        report.record_unbacked(document, "multi_seed_ci", unavailable_reason(gt, "multi_seed"))

    changed = _finish(path, text, original, dry_run, document)
    if owns:
        report.raise_if_failed()
    return changed


def inject_results(
    gt: dict,
    manuscript_dir: Path,
    dry_run: bool = False,
    *,
    report: InjectionReport | None = None,
) -> bool:
    """Update 05_results.md with ground truth values.

    Returns True if the file was modified.
    """
    report, owns = _resolve_report(report)
    document = "05_results.md"
    path = manuscript_dir / document
    text = path.read_text()
    original = text

    if is_available(gt, "multi_seed"):
        text = _apply(
            text,
            r"Mean Detection Rate\s*\|\s*\d+\.\d+",
            f"Mean Detection Rate | {gt['multi_seed_mean_dr']:.3f}",
            document=document,
            label="multi_seed_mean_dr",
            report=report,
        )
        text = _apply(
            text,
            r"Coefficient of Variation\s*\|\s*\d+\.\d+",
            f"Coefficient of Variation | {gt['multi_seed_cv']:.3f}",
            document=document,
            label="multi_seed_cv",
            report=report,
        )
        text = _apply(
            text,
            r"Min Detection Rate\s*\|\s*\d+\.\d+",
            f"Min Detection Rate | {gt['multi_seed_min_dr']:.2f}",
            document=document,
            label="multi_seed_min_dr",
            report=report,
        )
        text = _apply(
            text,
            r"Max Detection Rate\s*\|\s*\d+\.\d+",
            f"Max Detection Rate | {gt['multi_seed_max_dr']:.2f}",
            document=document,
            label="multi_seed_max_dr",
            report=report,
        )
    else:
        reason = unavailable_reason(gt, "multi_seed")
        for label in (
            "multi_seed_mean_dr",
            "multi_seed_cv",
            "multi_seed_min_dr",
            "multi_seed_max_dr",
        ):
            report.record_unbacked(document, label, reason)

    if is_available(gt, "llm"):
        text = _apply(
            text,
            r"\| Claude Code \| Hub-spoke \| \d+\.\d+\\%",
            f"| Claude Code | Hub-spoke | {format_pct(gt['llm_claude_dr'], 1)}\\%",
            document=document,
            label="llm_claude_dr",
            report=report,
        )
        text = _apply(
            text,
            r"\| CrewAI \| Chain \| \d+\.\d+\\%",
            f"| CrewAI | Chain | {format_pct(gt['llm_crewai_dr'], 1)}\\%",
            document=document,
            label="llm_crewai_dr",
            report=report,
        )
    else:
        reason = unavailable_reason(gt, "llm")
        report.record_unbacked(document, "llm_claude_dr", reason)
        report.record_unbacked(document, "llm_crewai_dr", reason)

    # NOTE: the "Detection Rate (simulation)" row lives only in
    # S08_parametric_analysis.md (see inject_parametric_supplement). No
    # substitution for it belongs here: a pattern kept against a document that
    # does not contain it is permanently dead, and a dead pattern is
    # indistinguishable from a satisfied one.
    changed = _finish(path, text, original, dry_run, document)
    if owns:
        report.raise_if_failed()
    return changed


def inject_ablation(
    gt: dict,
    manuscript_dir: Path,
    dry_run: bool = False,
    *,
    report: InjectionReport | None = None,
) -> bool:
    """Update 05d_ablation_and_scalability.md with ground truth values.

    Returns True if the file was modified.
    """
    report, owns = _resolve_report(report)
    document = "05d_ablation_and_scalability.md"
    path = manuscript_dir / document
    text = path.read_text()
    original = text

    components = gt["ablation_components"]
    caption_parts = []
    for c in components[1:]:
        name = c["removed"].replace("_", " ").title()
        # \approx matches this document's convention and is honest: every
        # delta is a multiple of 1/N_attacks, so 3 dp is a rounding.
        # The backslash is doubled because this string becomes an re.sub
        # *replacement*, where "\a" would otherwise be read as an escape and
        # emit a BEL control character instead of the literal \approx.
        caption_parts.append(f"{name} ($\\\\approx {c['delta_tpr']:+.3f}$)")
    new_order_str = ", ".join(caption_parts[:-1]) + f", and {caption_parts[-1]}"
    # Non-greedy so the replacement (which contains '.' inside numbers) stays
    # matchable on a second run — the idempotency property this module claims.
    # The trailing clause used to name Provenance, Sandbox and Consensus as the
    # zero-contribution set, which was true when it was written and is not now:
    # rewriting the Invariants module left Detection and Trust Calculus at zero
    # marginal contribution too. Hardcoding the membership of a set the data
    # decides is how a caption goes quietly stale, so it is derived.
    zero_components = [
        c["removed"].replace("_", " ").title()
        for c in components
        if abs(c["delta_tpr"]) < 1e-9
    ]
    zero_clause = (
        ", ".join(zero_components[:-1]) + f", and {zero_components[-1]}"
        if len(zero_components) > 1
        else (zero_components[0] if zero_components else "no component")
    )
    text = _apply(
        text,
        r"followed by .+?; .+? show no measurable independent contribution",
        f"followed by {new_order_str}; {zero_clause} show no measurable "
        f"independent contribution",
        document=document,
        label="component_order_caption",
        report=report,
    )

    # "both" only appears while the top pair is tied, and the tie broke when
    # the Invariants rewrite changed the ablation. A substitution that can only
    # maintain a tied value is dead the moment the tie is, so the qualifier is
    # optional here and the sentence carries whichever form is true.
    text = _apply(
        text,
        r"((?:The top synergy tier|The strongest pair) \([^()]*?"
        r"(?:both\s*)?\$\s*\\approx\s*)\+[\d.]+(\$)",
        r"\g<1>" + f"+{gt['top_synergy']['synergy']:.3f}" + r"\g<2>",
        document=document,
        label="top_synergy_value",
        report=report,
    )

    # Ties are real: with an N-attack corpus every synergy is a multiple of
    # 1/N, and two pairs currently share the maximum exactly. Naming only the
    # first would assert an ordering the measurement cannot support, so the
    # sentence pluralises over every tied pair. The manuscript uses lowercase
    # component names joined by '+' (e.g. "firewall+detection") inside the
    # top-synergy-tier parenthetical.
    tied = gt.get("top_synergy_ties") or [gt["top_synergy"]]
    pair_names = []
    for s in tied:
        a_lower = str(s["a"]).lower()
        b_lower = str(s["b"]).lower()
        pair_names.append(f"{a_lower}+{b_lower}")
    if len(pair_names) == 1:
        pair_label = pair_names[0]
    else:
        pair_label = " and ".join(pair_names)
    text = _apply(
        text,
        # "tier" presumes a tie; "strongest pair" is the singular form. The
        # prose carries whichever is true, so the pattern accepts both rather
        # than going dead the moment the measurement stops tying.
        r"((?:The top synergy tier|The strongest pair) \()[a-z+ -]+( and [a-z+ -]+)?(?=[,)])",
        r"\g<1>" + pair_label,
        document=document,
        label="top_synergy_pair",
        report=report,
    )

    for c in components:
        name_display = _component_display_name(c["removed"])
        # The manuscript pluralises some component names ("Tripwires") and
        # writes deltas as "$\approx -0.010$". Capture the label, the column
        # separators and the qualifier so only the numbers are rewritten.
        escaped = re.escape(name_display)
        if not name_display.endswith("s"):
            escaped += "s?"
        old_pattern = (
            rf"(\| {escaped}\s*\|\s*)[\d.]+(\s*\|\s*\$\s*" + _QUALIFIER + r")[-+]?[\d.]+(\$)"
        )
        new_row = rf"\g<1>{c['tpr']:.3f}\g<2>{c['delta_tpr']:+.3f}\g<3>"
        new_text, count = re.subn(old_pattern, new_row, text, flags=re.IGNORECASE)
        if count == 0:
            report.record_miss(document, f"ablation_row:{c['removed']}", old_pattern)
        else:
            report.record_match(document, f"ablation_row:{c['removed']}", count)
        text = new_text

    # The anchor is the component this hierarchy *starts* with, read from the
    # data, not the module that happened to lead when the sentence was written.
    # With "Detection module" hardcoded here the pattern stopped matching the
    # head of the sentence and started matching its tail, so each run spliced a
    # fresh copy of the hierarchy into the middle of the old one instead of
    # replacing it — the module's idempotency contract, broken silently.
    # ``components[0]`` is what ``_component_hierarchy`` writes first, so
    # anchoring on the same element is what makes the substitution a no-op the
    # second time round.
    hierarchy_head = _component_display_name(components[0]["removed"])
    head_anchor = re.escape(hierarchy_head) + ("" if hierarchy_head.endswith("s") else "s?")
    text = _apply(
        text,
        head_anchor + r"\s*\$(?:[>=]|\\approx|\\gg)\$[^.]+\.",
        f"{_component_hierarchy(components)}.",
        document=document,
        label="component_hierarchy",
        report=report,
    )

    if is_available(gt, "multi_seed"):
        text = _apply(
            text,
            r"multi-seed analysis shows \$\\sim\$\d+\.\d+\\%",
            f"multi-seed analysis shows $\\\\sim${format_pct(gt['multi_seed_mean_dr'], 1)}\\%",
            document=document,
            label="multi_seed_mean_dr",
            report=report,
        )
    else:
        report.record_unbacked(
            document, "multi_seed_mean_dr", unavailable_reason(gt, "multi_seed")
        )

    changed = _finish(path, text, original, dry_run, document)
    if owns:
        report.raise_if_failed()
    return changed


def inject_discussion(
    gt: dict,
    manuscript_dir: Path,
    dry_run: bool = False,
    *,
    report: InjectionReport | None = None,
) -> bool:
    """Update 06_discussion.md with ground truth values.

    Returns True if the file was modified.
    """
    report, owns = _resolve_report(report)
    document = "06_discussion.md"
    path = manuscript_dir / document
    text = path.read_text()
    original = text

    if is_available(gt, "multi_seed"):
        text = _apply(
            text,
            r"mean detection rate of \d+\.\d+\\%",
            f"mean detection rate of {format_pct(gt['multi_seed_mean_dr'], 1)}\\%",
            document=document,
            label="multi_seed_mean_dr",
            report=report,
        )
    else:
        report.record_unbacked(
            document, "multi_seed_mean_dr", unavailable_reason(gt, "multi_seed")
        )

    if "multi_seed_ci_halfwidth" in gt:
        ms_mean = gt["multi_seed_mean_dr"]
        half = gt["multi_seed_ci_halfwidth"]
        text = _apply(
            text,
            r"\[95\\% CI: \d+\.\d+\\%, \d+\.\d+\\%\]",
            f"[95\\% CI: {format_pct(ms_mean - half, 1)}\\%, {format_pct(ms_mean + half, 1)}\\%]",
            document=document,
            label="multi_seed_ci",
            report=report,
        )
    else:
        report.record_unbacked(document, "multi_seed_ci", unavailable_reason(gt, "multi_seed"))

    text = _apply_top_synergy_value(
        text, gt, r"strongest synergy", document=document, report=report
    )

    changed = _finish(path, text, original, dry_run, document)
    if owns:
        report.raise_if_failed()
    return changed


def inject_experimental_setup(
    gt: dict,
    manuscript_dir: Path,
    dry_run: bool = False,
    *,
    report: InjectionReport | None = None,
) -> bool:
    """Update 04_experimental_setup.md with ground truth values.

    Returns True if the file was modified.
    """
    report, owns = _resolve_report(report)
    document = "04_experimental_setup.md"
    path = manuscript_dir / document
    text = path.read_text()
    original = text

    if is_available(gt, "llm"):
        text = _apply(
            text,
            r"(LLM-backed(?: multiagent)? validation) \(\$N=\d+\$",
            r"\g<1> " + f"($N={gt['llm_total_n']}$",
            document=document,
            label="llm_total_n",
            report=report,
        )
        text = _apply(
            text,
            r"\| Claude Code \| Hub-spoke \| \d+\.\d+\\%",
            f"| Claude Code | Hub-spoke | {format_pct(gt['llm_claude_dr'], 1)}\\%",
            document=document,
            label="llm_claude_dr",
            report=report,
        )
        text = _apply(
            text,
            r"\| CrewAI \| Chain \| \d+\.\d+\\%",
            f"| CrewAI | Chain | {format_pct(gt['llm_crewai_dr'], 1)}\\%",
            document=document,
            label="llm_crewai_dr",
            report=report,
        )
    else:
        reason = unavailable_reason(gt, "llm")
        for label in ("llm_total_n", "llm_claude_dr", "llm_crewai_dr"):
            report.record_unbacked(document, label, reason)

    if is_available(gt, "multi_seed"):
        # Truncated (not rounded) to whole percent — preserves the historical
        # "$\sim$44\%" wording rather than silently re-rounding it to 45.
        ms_pct_int = format_pct(gt["multi_seed_mean_dr"], 1)[:-2]
        text = _apply(
            text,
            r"mean DR \$\\sim\$\d+\\%",
            f"mean DR $\\\\sim${ms_pct_int}\\%",
            document=document,
            label="multi_seed_mean_dr",
            report=report,
        )
    else:
        report.record_unbacked(
            document, "multi_seed_mean_dr", unavailable_reason(gt, "multi_seed")
        )

    # This is the one document that still states a numeric detection delta
    # ("Detection module: $\Delta\text{TPR} \approx +0.000$ when removed"), so
    # it is the only place the shared helper stays wired in. That claim survived
    # the Invariants rewrite; dropping this call along with the five genuinely
    # dead ones left a live number unmaintained, and no miss can ever report
    # that, because a deleted substitution never runs.
    text = _apply_detection_delta(text, gt, document=document, report=report)

    changed = _finish(path, text, original, dry_run, document)
    if owns:
        report.raise_if_failed()
    return changed


def inject_conclusion(
    gt: dict,
    manuscript_dir: Path,
    dry_run: bool = False,
    *,
    report: InjectionReport | None = None,
) -> bool:
    """Update 07_conclusion.md with ground truth values.

    Returns True if the file was modified.
    """
    report, owns = _resolve_report(report)
    document = "07_conclusion.md"
    path = manuscript_dir / document
    text = path.read_text()
    original = text

    if is_available(gt, "multi_seed"):
        text = _apply(
            text,
            r"mean DR = \d+\.\d+\\%",
            f"mean DR = {format_pct(gt['multi_seed_mean_dr'], 1)}\\%",
            document=document,
            label="multi_seed_mean_dr",
            report=report,
        )
    else:
        report.record_unbacked(
            document, "multi_seed_mean_dr", unavailable_reason(gt, "multi_seed")
        )

    # NOTE: no numeric \Delta\text{TPR} claim survives in the conclusion — it
    # cites the component hierarchy and the summed-magnitude share instead.
    # The substitution that used to live here matched nothing and was removed
    # rather than left dead. If a numeric delta returns to this document, add
    # `_apply_detection_delta` back; the shared helper already handles it.
    text = _apply_top_synergy_value(
        text, gt, r"synergy", document=document, report=report
    )

    changed = _finish(path, text, original, dry_run, document)
    if owns:
        report.raise_if_failed()
    return changed


def inject_statistical(
    gt: dict,
    manuscript_dir: Path,
    dry_run: bool = False,
    *,
    report: InjectionReport | None = None,
) -> bool:
    """Update 05b_statistical_significance.md with ground truth values.

    Returns True if the file was modified.
    """
    report, owns = _resolve_report(report)
    document = "05b_statistical_significance.md"
    path = manuscript_dir / document
    text = path.read_text()
    original = text

    if is_available(gt, "multi_seed"):
        text = _apply(
            text,
            r"Mean DR\s*\|\s*\d+\.\d+",
            f"Mean DR | {gt['multi_seed_mean_dr']:.3f}",
            document=document,
            label="multi_seed_mean_dr",
            report=report,
        )
        text = _apply(
            text,
            r"CV\s*\|\s*\d+\.\d+\s*\|",
            f"CV | {gt['multi_seed_cv']:.3f} |",
            document=document,
            label="multi_seed_cv",
            report=report,
        )
    else:
        reason = unavailable_reason(gt, "multi_seed")
        report.record_unbacked(document, "multi_seed_mean_dr", reason)
        report.record_unbacked(document, "multi_seed_cv", reason)

    text = _apply(
        text,
        r"(None \(full pipeline\)\s*\|\s*\$?\s*" + _QUALIFIER + r")[\d.]+",
        r"\g<1>" + f"{gt['full_pipeline_tpr']:.3f}",
        document=document,
        label="full_pipeline_tpr",
        report=report,
    )
    # The same figure is restated inline two paragraphs down ("vs.\ full
    # pipeline $\approx 0.959$"). Leaving it unmaintained put a table row and
    # its own interpretation paragraph in direct contradiction (0.122 vs
    # 0.124), so the restatement is driven from the same value rather than
    # trusted to be re-typed by hand.
    text = _apply(
        text,
        r"(full pipeline \$\s*" + _QUALIFIER + r")[\d.]+",
        r"\g<1>" + f"{gt['full_pipeline_tpr']:.3f}",
        document=document,
        label="full_pipeline_tpr_prose",
        report=report,
    )

    changed = _finish(path, text, original, dry_run, document)
    if owns:
        report.raise_if_failed()
    return changed


def inject_parametric_supplement(
    gt: dict,
    manuscript_dir: Path,
    dry_run: bool = False,
    *,
    report: InjectionReport | None = None,
) -> bool:
    """Update S08_parametric_analysis.md with ground truth values.

    Returns True if the file was modified.

    An absent document is *not* a clean skip: the claims it carries would go
    unmaintained while the run still reported success. It is recorded as
    unbacked so ``strict`` mode fails.
    """
    report, owns = _resolve_report(report)
    document = "S08_parametric_analysis.md"
    path = manuscript_dir / document
    if not path.exists():
        report.record_unbacked(
            document,
            "parametric_supplement",
            f"{document} not found in {manuscript_dir}",
        )
        if owns:
            report.raise_if_failed()
        return False

    text = path.read_text()
    original = text

    text = _apply(
        text,
        r"\| Detection Rate \(simulation\)\s*\|\s*\d+\.\d+",
        f"| Detection Rate (simulation) | {gt['parametric_overall_dr_mean']:.3f}",
        document=document,
        label="parametric_overall_dr",
        report=report,
    )
    text = _apply(
        text,
        r"\| Detection Rate — AutoGPT only\s*\|\s*\d+\.\d+",
        f"| Detection Rate — AutoGPT only | {gt['parametric_autogpt_dr_mean']:.3f}",
        document=document,
        label="parametric_autogpt_dr",
        report=report,
    )
    # NOTE: no substitution for gt["cohens_d"]. The value
    # (cohens_d_cif_vs_baseline, from statistical_results.json) is stated
    # nowhere in the manuscript: S08's effect-size table lists four *different*
    # comparisons (CIF vs Firewall-only / Sandbox-only / Tripwires-only /
    # Invariants-only), none of which this number describes. The old
    # "Cohen's $d$ = N.NN" pattern matched zero times and was removed rather
    # than left dead. Wiring d into that table requires the ablation-vs-CIF
    # effect sizes to actually be computed first — see the audit note.

    changed = _finish(path, text, original, dry_run, document)
    if owns:
        report.raise_if_failed()
    return changed


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def _log_ground_truth(gt: dict) -> None:
    """Log ground truth with provenance-derived tags.

    A value that was not measured is tagged ``[UNAVAILABLE]`` and printed
    without a number — it is structurally impossible for a fallback to be
    logged as ``[REAL]`` because no fallback exists.
    """
    logger.info("=== Ground Truth Values ===")
    logger.info(
        "  [PARAMETRIC] Overall DR: %s%% (N=%s)",
        format_pct(gt["parametric_overall_dr_mean"]),
        gt["parametric_n"],
    )
    logger.info(
        "  [PARAMETRIC] AutoGPT DR: %s%% [%s–%s%%]",
        format_pct(gt["parametric_autogpt_dr_mean"]),
        format_pct(gt["parametric_autogpt_dr_min"]),
        format_pct(gt["parametric_autogpt_dr_max"]),
    )

    if is_available(gt, "multi_seed"):
        logger.info(
            "  [REAL] Multi-seed mean DR: %s%% (N=%s seeds)",
            format_pct(gt["multi_seed_mean_dr"]),
            gt["multi_seed_n"],
        )
        logger.info(
            "  [REAL] Multi-seed range: %s–%s%%",
            format_pct(gt["multi_seed_min_dr"]),
            format_pct(gt["multi_seed_max_dr"]),
        )
    else:
        logger.warning(
            "  [UNAVAILABLE] Multi-seed: %s — no value substituted",
            unavailable_reason(gt, "multi_seed"),
        )

    if is_available(gt, "llm"):
        logger.info(
            "  [REAL] LLM Claude Code DR: %s%% (N=%s)",
            format_pct(gt["llm_claude_dr"]),
            gt["llm_claude_total"],
        )
        logger.info(
            "  [REAL] LLM CrewAI DR: %s%% (N=%s)",
            format_pct(gt["llm_crewai_dr"]),
            gt["llm_crewai_total"],
        )
    else:
        logger.warning(
            "  [UNAVAILABLE] LLM validation: %s — no value substituted",
            unavailable_reason(gt, "llm"),
        )

    logger.info("  [REAL] Ablation Detection Δ: %+.3f", gt["detection_delta"])
    logger.info("  [REAL] Ablation Firewall Δ: %+.3f", gt["firewall_delta"])
    logger.info(
        "  [REAL] Top synergy: %s+%s = %+.3f",
        gt["top_synergy"]["a"],
        gt["top_synergy"]["b"],
        gt["top_synergy"]["synergy"],
    )
    logger.info("  [PARAMETRIC] Cohen's d: %.2f", gt["cohens_d"])
    logger.info("  [PARAMETRIC] KW p: %.6f", gt["kw_p"])


def inject_all(
    data_dir: Path,
    manuscript_dir: Path,
    dry_run: bool = False,
    *,
    strict: bool = True,
    report: InjectionReport | None = None,
) -> int:
    """Inject all validated values into manuscript files.

    Parameters
    ----------
    data_dir : Path
        Directory containing JSON data files.
    manuscript_dir : Path
        Directory containing manuscript markdown files.
    dry_run : bool
        If True, report what would change without writing.
    strict : bool
        If True (default), raise :class:`GroundTruthUnavailableError` when a
        manuscript claim has no measured value behind it. Zero-match
        substitution patterns always raise :class:`InjectionPatternError`.
    report : InjectionReport, optional
        Accumulator to write into. Supply one to inspect misses and unbacked
        claims after a ``strict=False`` run.

    Returns
    -------
    int
        Number of files modified.

    Raises
    ------
    GroundTruthUnavailableError
        A claim would have needed a value that was never measured.
    InjectionPatternError
        A substitution pattern matched zero times (the manuscript drifted
        away from the injector, so the claim is no longer maintained).
    """
    gt = load_ground_truth(data_dir)
    _log_ground_truth(gt)

    if report is None:
        report = InjectionReport()

    changes = 0
    for inject in (
        inject_abstract,
        inject_results,
        inject_ablation,
        inject_discussion,
        inject_experimental_setup,
        inject_conclusion,
        inject_statistical,
        inject_parametric_supplement,
    ):
        changes += int(inject(gt, manuscript_dir, dry_run, report=report))

    if report.ok:
        if changes == 0:
            logger.info(
                "✅ All %d maintained value(s) matched and already agree with the "
                "data — no changes needed",
                report.n_substitutions,
            )
        else:
            verb = "would update" if dry_run else "updated"
            logger.info(
                "📝 %s %d manuscript file(s) from %d substitution(s)",
                verb,
                changes,
                report.n_substitutions,
            )
    else:
        logger.error(
            "❌ Injection incomplete: %d pattern(s) matched zero times, "
            "%d claim(s) unbacked, %d substitution(s) applied",
            len(report.misses),
            len(report.unbacked),
            report.n_substitutions,
        )

    report.raise_if_failed(strict=strict)
    return changes
