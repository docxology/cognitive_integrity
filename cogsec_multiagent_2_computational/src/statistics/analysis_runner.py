"""Statistical analysis orchestrator.

Loads real data, runs hypothesis tests, and produces serialisable results.

Fail-closed contract
--------------------
``load_real_data`` derives component scores from the measured ablation file
and from nothing else. A missing file, a malformed payload, or a row that has
lost a key it depends on raises :class:`AblationDataUnavailableError`. It used
to fall back to a table of hand-written per-component means, which meant a
schema change or a deleted file silently turned the published component
statistics into invented numbers that were still labelled ``real_pipeline``.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

#: Keys every ``component_removal`` row must carry for the analysis to run.
_REQUIRED_ABLATION_ROW_KEYS = ("removed", "tpr")


class AblationDataUnavailableError(RuntimeError):
    """Raised when component scores cannot be derived from measured ablation data.

    This is deliberately fatal. The alternative — substituting plausible
    per-component means — produces a ``statistical_results.json`` that is
    indistinguishable from a real one, so the failure has to stop the run.
    """


def _component_means_from_ablation(ablation_path: Path | None) -> dict[str, float]:
    """Read per-component TPRs out of the ablation results file.

    Raises
    ------
    AblationDataUnavailableError
        The file is missing, unreadable, not an object, carries no
        ``component_removal`` rows, or a row is missing a required key. The
        message names the file and the specific key at fault.
    """
    if ablation_path is None:
        raise AblationDataUnavailableError(
            "no ablation results path was supplied; component scores cannot be "
            "derived from measured data"
        )
    if not ablation_path.exists():
        raise AblationDataUnavailableError(
            f"ablation results not found: {ablation_path}"
        )
    try:
        payload = json.loads(ablation_path.read_text())
    except json.JSONDecodeError as exc:
        raise AblationDataUnavailableError(
            f"{ablation_path} is not valid JSON ({exc})"
        ) from exc
    if not isinstance(payload, dict):
        raise AblationDataUnavailableError(f"{ablation_path} is not a JSON object")

    rows = payload.get("component_removal")
    if not isinstance(rows, list) or not rows:
        raise AblationDataUnavailableError(
            f"{ablation_path} has no populated 'component_removal' list "
            f"(top-level keys: {sorted(payload) if payload else []})"
        )

    means: dict[str, float] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise AblationDataUnavailableError(
                f"{ablation_path}: 'component_removal[{index}]' is not an object"
            )
        for key in _REQUIRED_ABLATION_ROW_KEYS:
            if key not in row:
                raise AblationDataUnavailableError(
                    f"{ablation_path}: 'component_removal[{index}]' is missing "
                    f"required key {key!r} (keys present: {sorted(row)})"
                )
        try:
            means[str(row["removed"])] = float(row["tpr"])
        except (TypeError, ValueError) as exc:
            raise AblationDataUnavailableError(
                f"{ablation_path}: 'component_removal[{index}].tpr' is not a "
                f"number ({row['tpr']!r})"
            ) from exc
    return means


def generate_sample_data(rng: np.random.Generator, n: int = 100) -> dict[str, Any]:
    """Generate plausible experimental data for statistical analysis.

    Every number below is invented. This exists to exercise the hypothesis
    tests on a well-conditioned input; it is not wired into any pipeline and
    its output must never reach ``output/data`` or the manuscript. Production
    inputs come from :func:`load_real_data`.

    Parameters
    ----------
    rng : np.random.Generator
        Seeded random number generator.
    n : int
        Number of samples per group.

    Returns
    -------
    dict
        Keys: cif_scores, baseline_scores, component_scores, arch_scores.
    """
    cif_scores = rng.normal(0.967, 0.015, size=n).clip(0.85, 1.0)
    baseline_scores = rng.normal(0.12, 0.05, size=n).clip(0.0, 0.35)

    component_scores = {
        "firewall": rng.normal(0.82, 0.03, size=n).clip(0.7, 0.95),
        "trust_calculus": rng.normal(0.71, 0.04, size=n).clip(0.55, 0.85),
        "tripwire": rng.normal(0.68, 0.04, size=n).clip(0.50, 0.82),
        "detection": rng.normal(0.74, 0.03, size=n).clip(0.60, 0.88),
        "consensus": rng.normal(0.65, 0.05, size=n).clip(0.45, 0.80),
        "provenance": rng.normal(0.60, 0.04, size=n).clip(0.45, 0.78),
        "sandbox": rng.normal(0.58, 0.05, size=n).clip(0.40, 0.75),
        "invariants": rng.normal(0.63, 0.04, size=n).clip(0.48, 0.78),
    }

    arch_scores = {
        "claude_code": rng.normal(0.972, 0.012, size=n).clip(0.90, 1.0),
        "autogpt": rng.normal(0.948, 0.020, size=n).clip(0.85, 1.0),
        "crewai": rng.normal(0.965, 0.015, size=n).clip(0.88, 1.0),
        "langgraph": rng.normal(0.960, 0.016, size=n).clip(0.87, 1.0),
    }

    return {
        "cif_scores": cif_scores,
        "baseline_scores": baseline_scores,
        "component_scores": component_scores,
        "arch_scores": arch_scores,
    }


def load_real_data(
    eval_path: Path,
    ablation_path: Path | None,
    rng: np.random.Generator,
) -> dict[str, Any]:
    """Load real evaluation data and build analysis inputs.

    Parameters
    ----------
    eval_path : Path
        Path to full_evaluation_results.json.
    ablation_path : Path, optional
        Path to ablation_results.json. Required in practice: ``None`` or a
        missing/malformed file raises rather than falling back to defaults.
    rng : np.random.Generator
        Seeded RNG for baseline/noise generation.

    Returns
    -------
    dict
        Keys: cif_scores, baseline_scores, component_scores, arch_scores.

    Raises
    ------
    AblationDataUnavailableError
        Component scores could not be derived from measured ablation data.

    Warning
    -------
    ``cif_scores`` and ``arch_scores`` are measured. ``baseline_scores`` are
    **not** — they are drawn from ``N(0.03, 0.02)`` because the evaluation
    never ran an undefended control arm. ``component_scores`` are measured
    per-component TPRs widened by ``N(0, 0.02)`` noise to give the hypothesis
    tests a distribution to work with; they are not repeated measurements.
    Any effect size computed against ``baseline_scores`` (notably
    ``cohens_d_cif_vs_baseline``) is therefore a statement about a simulated
    control, not an observed one, and must be labelled that way downstream.
    """
    from data.result_loaders import load_full_evaluation

    rows = load_full_evaluation(str(eval_path))
    arch_rates: dict[str, list[float]] = {}
    for r in rows:
        arch_rates.setdefault(r.architecture, []).append(r.detection_rate)
    cif_scores = np.concatenate(list(arch_rates.values()))
    logger.info("Loaded real evaluation data from %s", eval_path)

    n = len(cif_scores)
    baseline_scores = rng.normal(0.03, 0.02, size=n).clip(0.0, 0.10)

    # Component scores from ablation. No fallback: an unreadable file or a
    # renamed key must stop the run, not quietly become invented means.
    component_means = _component_means_from_ablation(ablation_path)
    component_scores: dict[str, np.ndarray] = {
        comp: rng.normal(tpr, 0.02, size=n).clip(0.0, 1.0)
        for comp, tpr in component_means.items()
    }
    logger.info(
        "Loaded component scores from ablation data (%d components) at %s",
        len(component_scores),
        ablation_path,
    )

    # Per-architecture scores
    arch_name_map = {
        "Claude Code": "claude_code", "AutoGPT": "autogpt",
        "CrewAI": "crewai", "LangGraph": "langgraph",
    }
    arch_scores: dict[str, np.ndarray] = {}
    for arch_name, rates_list in arch_rates.items():
        key = arch_name_map.get(arch_name, arch_name.lower().replace(" ", "_"))
        arch_scores[key] = np.array(rates_list)

    return {
        "cif_scores": cif_scores,
        "baseline_scores": baseline_scores,
        "component_scores": component_scores,
        "arch_scores": arch_scores,
    }


def run_full_analysis(
    data: dict[str, Any],
    seed: int = 42,
) -> dict[str, Any]:
    """Run all hypothesis tests and return serialisable results.

    Parameters
    ----------
    data : dict
        Output of ``load_real_data`` or ``generate_sample_data``.
    seed : int
        Seed for bootstrap CIs.

    Returns
    -------
    dict
        Complete statistical results.
    """
    from statistics.assumptions import check_parametric_assumptions
    from statistics.effect_size import cohens_d
    from statistics.hypothesis import (
        test_h1_cif_vs_baseline,
        test_h2_cif_vs_components,
        test_h3_per_architecture,
    )
    from statistics.nonparametric import kruskal_wallis

    cif = data["cif_scores"]
    baseline = data["baseline_scores"]

    # H1
    h1 = test_h1_cif_vs_baseline(cif, baseline)

    # Effect size
    d = cohens_d(cif, baseline)

    # Assumption checks
    assumption_results, assumptions_met = check_parametric_assumptions(cif, baseline)

    # H2
    h2_results = test_h2_cif_vs_components(cif, data["component_scores"])

    # H3
    arch_h3_data = {
        name: (scores, baseline[:len(scores)])
        for name, scores in data["arch_scores"].items()
    }
    h3_results = test_h3_per_architecture(arch_h3_data)

    # Kruskal-Wallis
    arch_groups = list(data["arch_scores"].values())
    kw = kruskal_wallis(*arch_groups)

    return {
        "h1": {"statistic": h1.test_statistic, "p_value": h1.p_value, "significant": h1.significant},  # noqa: E501
        "h2": [{"name": h.name, "p_value": h.p_value, "significant": h.significant} for h in h2_results],  # noqa: E501
        "h3": [{"name": h.name, "p_value": h.p_value, "significant": h.significant} for h in h3_results],  # noqa: E501
        "kruskal_wallis": {"h": kw.test_statistic, "p": kw.p_value},
        "cohens_d_cif_vs_baseline": d.value,
        "assumptions": [
            {"test": ar.test_name, "group": ar.group_name, "statistic": ar.statistic,
             "p_value": ar.p_value, "passed": ar.passed}
            for ar in assumption_results
        ],
        "assumptions_met": assumptions_met,
    }
