"""Backend data exporter for the CIF Composer web UI.

This module provides a single-call API to extract all CIF module definitions,
composition algebra formulas, category-theory verification results, and preset
pipeline configurations as plain JSON-serialisable Python dicts.  The web UI
can call :func:`get_composer_data` once at startup to hydrate its state.

Usage::

    from visualization.composer_data import get_composer_data
    import json

    data = get_composer_data()
    print(json.dumps(data, indent=2))

Or via the CLI script ``scripts/generate_composer_data.py``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Module registry — mirrors MODULE_META in composable.py but adds extra fields
# ---------------------------------------------------------------------------

#: Complete registry of all 8 CIF defense modules with their detection rates,
#: latencies (in ms), Ω-class labels, morphism type signatures, and hex colors.
MODULE_REGISTRY: Dict[str, Dict[str, Any]] = {
    "Firewall": {
        "detection_rate": 0.91,
        "latency_ms": 12.0,
        "omega_class": "Injection",
        "morphism_type": "CognitiveState → DefenseResult",
        "description": "Pattern-matching firewall for prompt-injection attacks.",
        "color": "#e74c3c",
        "handles_attack_types": [
            "direct_injection",
            "indirect_injection",
            "nested_injection",
        ],
    },
    "Detection": {
        "detection_rate": 0.88,
        "latency_ms": 18.0,
        "omega_class": "Steganographic",
        "morphism_type": "CognitiveState → DefenseResult",
        "description": "Statistical anomaly detection for steganographic payloads.",
        "color": "#e67e22",
        "handles_attack_types": [
            "indirect_injection",
            "belief_injection",
        ],
    },
    "Tripwire": {
        "detection_rate": 0.85,
        "latency_ms": 8.0,
        "omega_class": "Sleeper",
        "morphism_type": "CognitiveState → DefenseResult",
        "description": "Canary-based detection for sleeper/timing attacks.",
        "color": "#f39c12",
        "handles_attack_types": [
            "timing_attack",
            "belief_drift",
        ],
    },
    "TrustCalc": {
        "detection_rate": 0.82,
        "latency_ms": 22.0,
        "omega_class": "Social",
        "morphism_type": "CognitiveState → DefenseResult",
        "description": "Trust-score calculator for social-engineering and impersonation.",
        "color": "#27ae60",
        "handles_attack_types": [
            "impersonation",
            "trust_inflation",
            "delegation_abuse",
        ],
    },
    "Consensus": {
        "detection_rate": 0.79,
        "latency_ms": 35.0,
        "omega_class": "Byzantine",
        "morphism_type": "CognitiveState → DefenseResult",
        "description": "Byzantine-fault-tolerant consensus checker.",
        "color": "#2980b9",
        "handles_attack_types": [
            "sybil_attack",
            "consensus_poisoning",
        ],
    },
    "Provenance": {
        "detection_rate": 0.76,
        "latency_ms": 28.0,
        "omega_class": "Provenance",
        "morphism_type": "CognitiveState → DefenseResult",
        "description": "Cryptographic provenance chain verifier.",
        "color": "#8e44ad",
        "handles_attack_types": [
            "belief_fabrication",
            "delegation_abuse",
        ],
    },
    "Sandbox": {
        "detection_rate": 0.73,
        "latency_ms": 55.0,
        "omega_class": "Resource",
        "morphism_type": "CognitiveState → DefenseResult",
        "description": "Execution sandbox for resource-abuse detection.",
        "color": "#16a085",
        "handles_attack_types": [
            "timing_attack",
            "sybil_attack",
        ],
    },
    "Invariants": {
        "detection_rate": 0.70,
        "latency_ms": 15.0,
        "omega_class": "Logic",
        "morphism_type": "CognitiveState → DefenseResult",
        "description": "Formal invariant checker for belief-state consistency.",
        "color": "#2c3e50",
        "handles_attack_types": [
            "belief_drift",
            "belief_fabrication",
            "belief_injection",
        ],
    },
}


# ---------------------------------------------------------------------------
# Composition algebra formulas — serialisable descriptions
# ---------------------------------------------------------------------------

def _series_detection_rate(rates: List[float]) -> float:
    """1 − ∏(1 − rᵢ)  (Theorem 3.1)."""
    miss = 1.0
    for r in rates:
        miss *= (1.0 - r)
    return 1.0 - miss


def _parallel_detection_rate(rates: List[float]) -> float:
    """max fusion: at-least-one detection = series formula."""
    return _series_detection_rate(rates)


def _hybrid_detection_rate(fast_rates: List[float], deep_rates: List[float]) -> float:
    """Two-stage hybrid: fast stage runs in parallel, deep stage in series.

    Formula::

        R_hybrid = 1 − (1 − R_fast) · (1 − R_deep)

    where R_fast = max-fusion of fast-stage rates and R_deep = series-fusion
    of deep-stage rates.  The stages are treated as independent, so the
    combined miss rate is the product of the individual stage miss rates.
    """
    r_fast = _parallel_detection_rate(fast_rates) if fast_rates else 0.0
    r_deep = _series_detection_rate(deep_rates) if deep_rates else 0.0
    return 1.0 - (1.0 - r_fast) * (1.0 - r_deep)


def _series_latency(latencies_ms: List[float]) -> float:
    """Series latency = sum of all stage latencies."""
    return sum(latencies_ms)


def _parallel_latency(latencies_ms: List[float]) -> float:
    """Parallel latency = max of all stage latencies (they run concurrently)."""
    return max(latencies_ms) if latencies_ms else 0.0


def _hybrid_latency(fast_ms: List[float], deep_ms: List[float]) -> float:
    """Hybrid latency = max(fast) + sum(deep) — fast runs in parallel, deep in series."""
    return _parallel_latency(fast_ms) + _series_latency(deep_ms)


ALGEBRA_FORMULAS: Dict[str, Dict[str, Any]] = {
    "series": {
        "name": "Series Composition",
        "theorem": "Theorem 3.1",
        "formula": "R = 1 − ∏(1 − rᵢ)",
        "latency_formula": "L = Σ lᵢ",
        "description": (
            "Modules evaluated left-to-right; early exit on first detection. "
            "Combined miss rate is the product of individual miss rates."
        ),
    },
    "parallel": {
        "name": "Parallel Composition (Max Fusion)",
        "theorem": "Theorem 3.2",
        "formula": "R = 1 − ∏(1 − rᵢ)  [max fusion ≡ series]",
        "latency_formula": "L = max(lᵢ)",
        "description": (
            "All modules run concurrently; max score is taken. Under max fusion "
            "the detection formula is identical to series composition."
        ),
    },
    "hybrid": {
        "name": "Hybrid (Two-Stage)",
        "theorem": "Corollary 3.3",
        "formula": "R = 1 − (1 − R_fast)(1 − R_deep)",
        "latency_formula": "L = max(l_fast) + Σ(l_deep)",
        "description": (
            "Fast stage runs in parallel for low-latency screening; deep stage "
            "runs in series for high-accuracy verification. The combined rate "
            "is complementary across the two independent stages."
        ),
    },
    "weighted_parallel": {
        "name": "Weighted Parallel Fusion",
        "theorem": "Theorem 3.2 (weighted variant)",
        "formula": "R ≈ P(Σ wᵢXᵢ > θ)  via normal approximation",
        "latency_formula": "L = max(lᵢ)",
        "description": (
            "Each module's Bernoulli output is weighted; the weighted sum is "
            "compared to a threshold θ (default 0.5). Uses a Gaussian "
            "approximation for tractable computation."
        ),
    },
}


# ---------------------------------------------------------------------------
# Preset pipeline configurations
# ---------------------------------------------------------------------------

def _build_preset_stats(
    modules: List[str],
    strategy: str,
    deep_modules: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Compute detection rate and latency for a preset pipeline."""
    rates = [MODULE_REGISTRY[m]["detection_rate"] for m in modules]
    latencies = [MODULE_REGISTRY[m]["latency_ms"] for m in modules]

    if strategy == "series":
        detection_rate = _series_detection_rate(rates)
        latency_ms = _series_latency(latencies)
    elif strategy == "parallel":
        detection_rate = _parallel_detection_rate(rates)
        latency_ms = _parallel_latency(latencies)
    elif strategy == "hybrid" and deep_modules:
        deep_rates = [MODULE_REGISTRY[m]["detection_rate"] for m in deep_modules]
        deep_lats = [MODULE_REGISTRY[m]["latency_ms"] for m in deep_modules]
        detection_rate = _hybrid_detection_rate(rates, deep_rates)
        latency_ms = _hybrid_latency(latencies, deep_lats)
    else:
        detection_rate = _series_detection_rate(rates)
        latency_ms = _series_latency(latencies)

    return {
        "detection_rate": round(detection_rate, 4),
        "latency_ms": round(latency_ms, 1),
    }


PRESET_PIPELINES: Dict[str, Dict[str, Any]] = {
    "full_stack": {
        "label": "Full Stack (Series)",
        "modules": list(MODULE_REGISTRY.keys()),
        "deep_modules": None,
        "strategy": "series",
        "description": "All 8 modules in series — maximum detection, highest latency.",
        **_build_preset_stats(list(MODULE_REGISTRY.keys()), "series"),
    },
    "minimal_viable": {
        "label": "Minimal Viable (MVP)",
        "modules": ["Firewall", "Detection", "Consensus"],
        "deep_modules": None,
        "strategy": "series",
        "description": "Minimal 3-module series covering injection, anomaly, and Byzantine.",
        **_build_preset_stats(["Firewall", "Detection", "Consensus"], "series"),
    },
    "fast_path": {
        "label": "Fast Path (Parallel)",
        "modules": ["Firewall", "Detection", "Tripwire"],
        "deep_modules": None,
        "strategy": "parallel",
        "description": "Top-3 fast modules in parallel — lowest latency screening.",
        **_build_preset_stats(["Firewall", "Detection", "Tripwire"], "parallel"),
    },
    "hybrid": {
        "label": "Hybrid (Fast → Deep)",
        "modules": ["Firewall", "Detection"],
        "deep_modules": ["Consensus", "Provenance", "Invariants"],
        "strategy": "hybrid",
        "description": (
            "Fast parallel stage (Firewall + Detection) feeds into deep series stage "
            "(Consensus + Provenance + Invariants). Balances speed and accuracy."
        ),
        **_build_preset_stats(
            ["Firewall", "Detection"],
            "hybrid",
            deep_modules=["Consensus", "Provenance", "Invariants"],
        ),
    },
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_module_registry() -> Dict[str, Dict[str, Any]]:
    """Return the full module registry as a JSON-serialisable dict.

    Returns:
        Mapping from module name to its metadata dict containing
        ``detection_rate``, ``latency_ms``, ``omega_class``,
        ``morphism_type``, ``description``, ``color``, and
        ``handles_attack_types``.
    """
    return {name: dict(meta) for name, meta in MODULE_REGISTRY.items()}


def get_algebra_formulas() -> Dict[str, Dict[str, Any]]:
    """Return composition algebra formulas as a JSON-serialisable dict.

    Returns:
        Mapping from strategy key to a dict with ``name``, ``theorem``,
        ``formula``, ``latency_formula``, and ``description``.
    """
    return {key: dict(val) for key, val in ALGEBRA_FORMULAS.items()}


def get_preset_pipelines() -> Dict[str, Dict[str, Any]]:
    """Return all preset pipeline configurations.

    Returns:
        Mapping from preset key to a dict with ``label``, ``modules``,
        ``strategy``, ``detection_rate``, ``latency_ms``, and ``description``.
    """
    return {key: dict(val) for key, val in PRESET_PIPELINES.items()}


def compute_custom_pipeline_stats(
    modules: List[str],
    strategy: str = "series",
    deep_modules: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Compute detection rate and latency for an arbitrary pipeline selection.

    Args:
        modules: Ordered list of module names (must exist in MODULE_REGISTRY).
        strategy: One of ``'series'``, ``'parallel'``, ``'hybrid'``.
        deep_modules: For ``'hybrid'`` strategy: the deep-stage module names.

    Returns:
        Dict with ``detection_rate`` (float), ``latency_ms`` (float),
        ``module_rates`` (list), and ``module_latencies`` (list).

    Raises:
        ValueError: If any module name is unknown.
    """
    unknown = [m for m in modules if m not in MODULE_REGISTRY]
    if unknown:
        raise ValueError(f"Unknown module(s): {unknown}")
    if deep_modules:
        unknown_deep = [m for m in deep_modules if m not in MODULE_REGISTRY]
        if unknown_deep:
            raise ValueError(f"Unknown deep module(s): {unknown_deep}")

    rates = [MODULE_REGISTRY[m]["detection_rate"] for m in modules]
    latencies = [MODULE_REGISTRY[m]["latency_ms"] for m in modules]

    stats = _build_preset_stats(modules, strategy, deep_modules=deep_modules)
    return {
        **stats,
        "module_rates": rates,
        "module_latencies": latencies,
        "modules": modules,
        "strategy": strategy,
        "deep_modules": deep_modules,
    }


def get_composer_data(include_category_theory: bool = True) -> Dict[str, Any]:
    """Aggregate all composer backend data into a single JSON-serialisable dict.

    This is the primary entry-point for the web UI.  It returns a complete
    snapshot of the CIF composer state:

    - ``modules``:   module registry
    - ``algebra``:   composition formula descriptions
    - ``presets``:   preset pipeline configurations with pre-computed stats
    - ``category_theory``: optional verification results (25 checks)
    - ``schema_version``: monotonically increasing version string

    Args:
        include_category_theory: Whether to run and embed the full category-
            theory verification suite. Set ``False`` for faster startup when
            the verifications are not needed by the UI.

    Returns:
        Complete composer data dict ready for ``json.dumps``.
    """
    data: Dict[str, Any] = {
        "schema_version": "1.0.0",
        "modules": get_module_registry(),
        "algebra": get_algebra_formulas(),
        "presets": get_preset_pipelines(),
    }

    if include_category_theory:
        try:
            # Import lazily so the module can be used without numpy installed
            import os
            import sys
            # Ensure src/ is on path when called from outside the package
            _src = os.path.join(os.path.dirname(__file__), "..", "..")
            if _src not in sys.path:
                sys.path.insert(0, _src)

            from formal.category_theory_advanced import (  # type: ignore[import]
                get_lattice_data,
                get_monoidal_data,
                get_operad_data,
                serialize_verification_results,
            )

            data["category_theory"] = {
                "verification_results": serialize_verification_results(),
                "lattice": get_lattice_data(),
                "monoidal": get_monoidal_data(),
                "operad": get_operad_data(),
            }
        except Exception as exc:  # pragma: no cover
            data["category_theory"] = {"error": str(exc)}

    return data


__all__ = [
    "MODULE_REGISTRY",
    "ALGEBRA_FORMULAS",
    "PRESET_PIPELINES",
    "get_module_registry",
    "get_algebra_formulas",
    "get_preset_pipelines",
    "compute_custom_pipeline_stats",
    "get_composer_data",
]
