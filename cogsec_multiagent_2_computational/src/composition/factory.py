"""Convenience functions for constructing defense pipelines.

Provides factory helpers that assemble the 8 canonical defense adapters
into series, parallel, or custom pipelines.  The :data:`MODULE_REGISTRY`
maps human-readable names to adapter classes, and :data:`CANONICAL_ORDER`
defines the standard evaluation sequence used across experiments and
ablation studies.
"""

from __future__ import annotations

from typing import Dict, List

from .adapters import (
    ConsensusAdapter,
    DetectionAdapter,
    FirewallAdapter,
    InvariantsAdapter,
    ProvenanceAdapter,
    SandboxAdapter,
    TripwireAdapter,
    TrustAdapter,
)
from .pipeline import DefenseModule, ParallelPipeline, SeriesPipeline

__all__ = [
    "CANONICAL_ORDER",
    "MODULE_REGISTRY",
    "create_full_pipeline",
    "create_pipeline_without",
    "create_module_dict",
]

# ---------------------------------------------------------------------------
# Canonical ordering and registry
# ---------------------------------------------------------------------------

CANONICAL_ORDER: List[str] = [
    "firewall",
    "detection",
    "tripwire",
    "trust",
    "consensus",
    "provenance",
    "sandbox",
    "invariants",
]

MODULE_REGISTRY: Dict[str, type] = {
    "firewall": FirewallAdapter,
    "detection": DetectionAdapter,
    "tripwire": TripwireAdapter,
    "trust": TrustAdapter,
    "consensus": ConsensusAdapter,
    "provenance": ProvenanceAdapter,
    "sandbox": SandboxAdapter,
    "invariants": InvariantsAdapter,
}

# ---------------------------------------------------------------------------
# Factory functions
# ---------------------------------------------------------------------------


def create_full_pipeline(mode: str = "series") -> SeriesPipeline | ParallelPipeline:
    """Create a pipeline with all 8 defense modules in canonical order.

    Args:
        mode: ``"series"`` or ``"parallel"``.

    Returns:
        A configured pipeline with all 8 modules.
    """
    modules = [MODULE_REGISTRY[name]() for name in CANONICAL_ORDER]
    if mode == "parallel":
        return ParallelPipeline(modules)
    return SeriesPipeline(modules)


def create_pipeline_without(
    excluded: List[str],
    mode: str = "series",
) -> SeriesPipeline | ParallelPipeline:
    """Create a pipeline with specified modules excluded (for ablation).

    The exclusion list is validated *fail-closed*: a name that is not a
    key of :data:`MODULE_REGISTRY` raises rather than being silently
    ignored.  Silently ignoring an unknown name is how an ablation can
    report a "removal" delta for a module that was never removed.

    Args:
        excluded: List of module names to exclude.  Every name must be a
            key of :data:`MODULE_REGISTRY`.
        mode: ``"series"`` or ``"parallel"``.

    Returns:
        A pipeline missing the excluded modules.

    Raises:
        ValueError: If any excluded name is not a registered module, or
            if all modules are excluded.
    """
    unknown = sorted(set(excluded) - set(MODULE_REGISTRY))
    if unknown:
        raise ValueError(
            f"Unknown module name(s) in `excluded`: {unknown}. "
            f"Known modules: {sorted(MODULE_REGISTRY)}"
        )
    modules = [
        MODULE_REGISTRY[name]()
        for name in CANONICAL_ORDER
        if name not in excluded
    ]
    if not modules:
        raise ValueError("Cannot create pipeline with all modules excluded")
    if mode == "parallel":
        return ParallelPipeline(modules)
    return SeriesPipeline(modules)


def create_module_dict() -> Dict[str, DefenseModule]:
    """Create a dict of all module instances keyed by canonical name."""
    return {name: MODULE_REGISTRY[name]() for name in CANONICAL_ORDER}
