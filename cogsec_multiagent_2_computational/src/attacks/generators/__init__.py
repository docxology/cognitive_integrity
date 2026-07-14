"""Attack corpus generators for each category.

Each generator module produces deterministic attack samples given a
numpy RNG, covering all 12 subcategories across 4 top-level categories.
"""

from __future__ import annotations

from .belief_manipulation import (
    generate_all_belief_manipulation,
    generate_belief_drift,
    generate_belief_fabrication,
    generate_belief_injection,
)
from .coordination import (
    generate_all_coordination,
    generate_consensus_poisoning,
    generate_sybil_attacks,
    generate_timing_attacks,
)
from .injection import (
    generate_all_injection,
    generate_direct_injection,
    generate_indirect_injection,
    generate_nested_injection,
)
from .trust_exploitation import (
    generate_all_trust_exploitation,
    generate_delegation_abuse,
    generate_impersonation,
    generate_trust_inflation,
)

__all__ = [
    # Injection
    "generate_all_injection",
    "generate_direct_injection",
    "generate_indirect_injection",
    "generate_nested_injection",
    # Trust exploitation
    "generate_all_trust_exploitation",
    "generate_impersonation",
    "generate_trust_inflation",
    "generate_delegation_abuse",
    # Belief manipulation
    "generate_all_belief_manipulation",
    "generate_belief_drift",
    "generate_belief_fabrication",
    "generate_belief_injection",
    # Coordination
    "generate_all_coordination",
    "generate_sybil_attacks",
    "generate_consensus_poisoning",
    "generate_timing_attacks",
]
