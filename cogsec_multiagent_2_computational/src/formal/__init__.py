"""Formal verification module for the Cognitive Security Framework.

Re-exports theorem validation infrastructure and model checker spec
generators for NuSMV, SPIN/Promela, and TLA+.
"""

from .byzantine_guarantees import validate_byzantine_bound
from .composition_proofs import (
    validate_associativity,
    validate_parallel_composition,
    validate_series_composition,
)
from .latency_bound import validate_latency_bound
from .nusmv_spec import generate_nusmv_spec, parse_nusmv_result
from .spin_spec import generate_promela_spec, parse_spin_result
from .stealth_impact import validate_stealth_impact
from .theorem_registry import TheoremRegistry, TheoremResult, TheoremStatus
from .tla_spec import generate_tla_spec, parse_tla_result
from .trust_bounds import validate_trust_bound

__all__ = [
    # Registry
    "TheoremRegistry",
    "TheoremResult",
    "TheoremStatus",
    # Validators
    "validate_trust_bound",
    "validate_series_composition",
    "validate_parallel_composition",
    "validate_associativity",
    "validate_byzantine_bound",
    "validate_stealth_impact",
    "validate_latency_bound",
    # Model checker specs
    "generate_nusmv_spec",
    "parse_nusmv_result",
    "generate_promela_spec",
    "parse_spin_result",
    "generate_tla_spec",
    "parse_tla_result",
]
