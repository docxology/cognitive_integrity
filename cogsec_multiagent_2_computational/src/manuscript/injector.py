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


class GroundTruthUnavailableError(RuntimeError):
    """Raised when a manuscript claim has no measured value behind it."""


class InjectionPatternError(RuntimeError):
    """Raised when a substitution pattern matched zero times."""


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
            raise GroundTruthUnavailableError(
                f"{len(self.unbacked)} manuscript claim(s) have no measured "
                f"value behind them: {detail}"
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


def _load_multi_seed_ground_truth(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    """Load measured multi-seed values, or explain why there are none."""
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

    # Detection delta from ablation
    delta = abs(gt["detection_delta"])
    text = _apply(
        text,
        r"\\Delta\\text\{TPR\}\s*=\s*-[\d.]+",
        f"\\\\Delta\\\\text{{TPR}} = -{delta:.3f}",
        document=document,
        label="detection_delta",
        report=report,
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

    text = _apply(
        text,
        r"\| Detection Rate \(simulation\)\s*\|\s*\d+\.\d+",
        f"| Detection Rate (simulation) | {gt['parametric_overall_dr_mean']:.3f}",
        document=document,
        label="parametric_overall_dr",
        report=report,
    )

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

    det_delta = abs(gt["detection_delta"])
    text = _apply(
        text,
        r"\\Delta\\text\{TPR\}\s*=\s*-[\d.]+\)",
        f"\\\\Delta\\\\text{{TPR}} = -{det_delta:.3f})",
        document=document,
        label="detection_delta",
        report=report,
    )

    components = gt["ablation_components"]
    caption_parts = []
    for c in components[1:]:
        name = c["removed"].replace("_", " ").title()
        caption_parts.append(f"{name} ($-{abs(c['delta_tpr']):.3f}$)")
    new_order_str = ", ".join(caption_parts[:-1]) + f", and {caption_parts[-1]}"
    # Non-greedy so the replacement (which contains '.' inside numbers) stays
    # matchable on a second run — the idempotency property this module claims.
    text = _apply(
        text,
        r"followed by .+?\. The",
        f"followed by {new_order_str}. The",
        document=document,
        label="component_order_caption",
        report=report,
    )

    syn_val = gt["top_synergy"]["synergy"]
    syn_a = gt["top_synergy"]["a"].replace("_", " ").title()
    syn_b = gt["top_synergy"]["b"].replace("_", " ").title()
    text = _apply(
        text,
        r"strongest positive synergy \(\$\+[\d.]+\$",
        f"strongest positive synergy ($+{syn_val:.3f}$",
        document=document,
        label="top_synergy_value",
        report=report,
    )
    text = _apply(
        text,
        r"The [A-Z][a-z]+ \+ [A-Z][a-z]+ pair exhibits the strongest",
        f"The {syn_a} + {syn_b} pair exhibits the strongest",
        document=document,
        label="top_synergy_pair",
        report=report,
    )

    for c in components:
        name_display = c["removed"].replace("_", " ").title()
        if c["removed"] == "detection":
            name_display = "Detection module"
        old_pattern = rf"\| {re.escape(name_display)}\s*\|\s*[\d.]+\s*\|\s*\$[-+]?[\d.]+\$"
        delta_str = f"-{abs(c['delta_tpr']):.3f}"
        new_row = f"| {name_display} | {c['tpr']:.3f} | ${delta_str}$"
        new_text, count = re.subn(old_pattern, new_row, text, flags=re.IGNORECASE)
        if count == 0:
            report.record_miss(document, f"ablation_row:{c['removed']}", old_pattern)
        else:
            report.record_match(document, f"ablation_row:{c['removed']}", count)
        text = new_text

    hierarchy_names = [c["removed"].replace("_", " ").title() for c in components]
    hierarchy_names[0] = "Detection module"
    hierarchy_str = " $>$ ".join(hierarchy_names)
    text = _apply(
        text,
        r"Detection module\s*\$>\$[^.]+\.",
        f"{hierarchy_str}.",
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

    det_delta = abs(gt["detection_delta"])
    text = _apply(
        text,
        r"\\Delta\\text\{TPR\}\s*=\s*-[\d.]+\)",
        f"\\\\Delta\\\\text{{TPR}} = -{det_delta:.3f})",
        document=document,
        label="detection_delta",
        report=report,
    )

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

    text = _apply(
        text,
        r"strongest synergy \(\$\+[\d.]+\$",
        f"strongest synergy ($+{gt['top_synergy']['synergy']:.3f}$",
        document=document,
        label="top_synergy_value",
        report=report,
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
            r"validation \(\$N=\d+\$",
            f"validation ($N={gt['llm_total_n']}$",
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

    det_delta = abs(gt["detection_delta"])
    text = _apply(
        text,
        r"\\Delta\\text\{TPR\}\s*=\s*-[\d.]+",
        f"\\\\Delta\\\\text{{TPR}} = -{det_delta:.3f}",
        document=document,
        label="detection_delta",
        report=report,
    )

    text = _apply(
        text,
        r"synergy \(\$\+[\d.]+\$",
        f"synergy ($+{gt['top_synergy']['synergy']:.3f}$",
        document=document,
        label="top_synergy_value",
        report=report,
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
        r"None \(full pipeline\)\s*\|\s*\d+\.\d+",
        f"None (full pipeline) | {gt['full_pipeline_tpr']:.3f}",
        document=document,
        label="full_pipeline_tpr",
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
    """
    report, owns = _resolve_report(report)
    document = "S08_parametric_analysis.md"
    path = manuscript_dir / document
    if not path.exists():
        logger.info("%s: not found — skipping", document)
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
    text = _apply(
        text,
        r"Cohen's \$d\$ = \d+\.\d+",
        f"Cohen's $d$ = {gt['cohens_d']:.2f}",
        document=document,
        label="cohens_d",
        report=report,
    )

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
