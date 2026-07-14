"""Attack corpus and generators for the Cognitive Security Framework.

Provides a 950-sample attack corpus covering 4 top-level categories
(injection, trust exploitation, belief manipulation, coordination)
and 12 subcategories, with deterministic generation, stratified
splitting, and quality validation.
"""

from __future__ import annotations

from .corpus import AttackCorpus, AttackSample
from .generators import (
    generate_all_belief_manipulation,
    generate_all_coordination,
    generate_all_injection,
    generate_all_trust_exploitation,
    generate_belief_drift,
    generate_belief_fabrication,
    generate_belief_injection,
    generate_consensus_poisoning,
    generate_delegation_abuse,
    generate_direct_injection,
    generate_impersonation,
    generate_indirect_injection,
    generate_nested_injection,
    generate_sybil_attacks,
    generate_timing_attacks,
    generate_trust_inflation,
)
from .templates import AttackTemplate, expand_template, get_all_templates
from .validation import ValidationReport, validate_corpus

__all__ = [
    # Core
    "AttackCorpus",
    "AttackSample",
    "ValidationReport",
    "validate_corpus",
    # Templates
    "AttackTemplate",
    "expand_template",
    "get_all_templates",
    # Generators - injection
    "generate_all_injection",
    "generate_direct_injection",
    "generate_indirect_injection",
    "generate_nested_injection",
    # Generators - trust exploitation
    "generate_all_trust_exploitation",
    "generate_impersonation",
    "generate_trust_inflation",
    "generate_delegation_abuse",
    # Generators - belief manipulation
    "generate_all_belief_manipulation",
    "generate_belief_drift",
    "generate_belief_fabrication",
    "generate_belief_injection",
    # Generators - coordination
    "generate_all_coordination",
    "generate_sybil_attacks",
    "generate_consensus_poisoning",
    "generate_timing_attacks",
]
