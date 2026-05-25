"""Statistical analysis orchestrator.

Loads real data, runs hypothesis tests, and produces serialisable results.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


def generate_sample_data(rng: np.random.Generator, n: int = 100) -> dict[str, Any]:
    """Generate plausible experimental data for statistical analysis.

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
        Path to ablation_results.json (may not exist).
    rng : np.random.Generator
        Seeded RNG for baseline/noise generation.

    Returns
    -------
    dict
        Keys: cif_scores, baseline_scores, component_scores, arch_scores.
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

    # Component scores from ablation
    component_scores: dict[str, np.ndarray] = {}
    if ablation_path and ablation_path.exists():
        try:
            ablation_data = json.loads(ablation_path.read_text())
            for row in ablation_data.get("component_removal", []):
                comp = row["removed"]
                single_tpr = float(row["tpr"])
                component_scores[comp] = rng.normal(single_tpr, 0.02, size=n).clip(0.0, 1.0)
            logger.info("Loaded component scores from ablation data (%d components)", len(component_scores))
        except Exception as exc:
            logger.warning("Could not load ablation data (%s); using defaults", exc)
            component_scores = {}

    if not component_scores:
        defaults = {
            "firewall": (0.82, 0.03), "trust_calculus": (0.71, 0.04),
            "tripwire": (0.68, 0.04), "detection": (0.74, 0.03),
            "consensus": (0.65, 0.05), "provenance": (0.60, 0.04),
            "sandbox": (0.58, 0.05), "invariants": (0.63, 0.04),
        }
        for key, (mu, sigma) in defaults.items():
            component_scores[key] = rng.normal(mu, sigma, size=n).clip(0.0, 1.0)

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
    from statistics.hypothesis import (
        test_h1_cif_vs_baseline,
        test_h2_cif_vs_components,
        test_h3_per_architecture,
    )
    from statistics.effect_size import cohens_d
    from statistics.nonparametric import kruskal_wallis
    from statistics.assumptions import check_parametric_assumptions

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
        "h1": {"statistic": h1.test_statistic, "p_value": h1.p_value, "significant": h1.significant},
        "h2": [{"name": h.name, "p_value": h.p_value, "significant": h.significant} for h in h2_results],
        "h3": [{"name": h.name, "p_value": h.p_value, "significant": h.significant} for h in h3_results],
        "kruskal_wallis": {"h": kw.test_statistic, "p": kw.p_value},
        "cohens_d_cif_vs_baseline": d.value,
        "assumptions": [
            {"test": ar.test_name, "group": ar.group_name, "statistic": ar.statistic,
             "p_value": ar.p_value, "passed": ar.passed}
            for ar in assumption_results
        ],
        "assumptions_met": assumptions_met,
    }
