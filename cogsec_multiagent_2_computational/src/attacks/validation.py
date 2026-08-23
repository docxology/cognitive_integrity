"""Attack quality assurance pipeline.

Validates the integrity and quality of an :class:`AttackCorpus` by
checking for duplicates, coverage, balance, and payload sanity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set

from utils.types import AttackCategory

from .corpus import AttackCorpus

# ---------------------------------------------------------------------------
# Expected distribution
# ---------------------------------------------------------------------------

EXPECTED_DISTRIBUTION = {
    "injection": 500,
    "trust_exploitation": 200,
    "belief_manipulation": 150,
    "coordination": 100,
}

EXPECTED_TOTAL = 950

EXPECTED_SUBCATEGORY_DISTRIBUTION = {
    "direct_injection": 200,
    "indirect_injection": 200,
    "nested_injection": 100,
    "impersonation": 80,
    "trust_inflation": 60,
    "delegation_abuse": 60,
    "belief_drift": 50,
    "belief_fabrication": 50,
    "belief_injection": 50,
    "sybil_attack": 40,
    "consensus_poisoning": 30,
    "timing_attack": 30,
}

#: The published corpus's twelve categories. Deliberately NOT ``set(AttackCategory)``:
#: the enum also carries the three extension families, and a validator that
#: demands every enum member appear would reject the 950-item corpus every
#: measured number in this series is built on, the moment a category is added.
PUBLISHED_CATEGORIES = {
    category
    for category in AttackCategory
    if category.value in EXPECTED_SUBCATEGORY_DISTRIBUTION
}

#: What the extended corpus must additionally contain.
EXTENSION_CATEGORIES = set(AttackCategory) - PUBLISHED_CATEGORIES

EXPECTED_EXTENDED_SUBCATEGORY_DISTRIBUTION = {
    **EXPECTED_SUBCATEGORY_DISTRIBUTION,
    "provenance_laundering": 175,
    "sandbox_escape": 175,
    "byzantine_manipulation": 175,
}

EXPECTED_EXTENDED_TOTAL = EXPECTED_TOTAL + 525

# ---------------------------------------------------------------------------
# Validation report
# ---------------------------------------------------------------------------

@dataclass
class ValidationReport:
    """Results from corpus validation.

    Attributes:
        total: Total number of samples in the corpus.
        valid: Number of samples that passed all checks.
        invalid: Number of samples that failed at least one check.
        warnings: List of warning messages.
        errors: List of error messages (hard failures).
        distribution: Observed top-level category distribution.
        subcategory_distribution: Observed subcategory distribution.
        passed: Whether the corpus passes overall validation.
    """

    total: int = 0
    valid: int = 0
    invalid: int = 0
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    distribution: Dict[str, int] = field(default_factory=dict)
    subcategory_distribution: Dict[str, int] = field(default_factory=dict)
    passed: bool = False


# ---------------------------------------------------------------------------
# Validation functions
# ---------------------------------------------------------------------------

def validate_corpus(
    corpus: AttackCorpus,
    tolerance: float = 0.05,
    min_payload_length: int = 10,
    max_payload_length: int = 5000,
) -> ValidationReport:
    """Run the full validation pipeline on an attack corpus.

    Checks performed:
        1. **Total count**: Must equal 950.
        2. **No duplicate IDs**: All sample IDs are unique.
        3. **No duplicate payloads**: All payloads are unique.
        4. **Category coverage**: All 12 subcategories are present.
        5. **Distribution balance**: Each top-level category is within
           *tolerance* of its expected count.
        6. **Payload quality**: Non-empty, reasonable length, no null bytes.
        7. **Difficulty validity**: Must be 'easy', 'medium', or 'hard'.

    Args:
        corpus: The corpus to validate.
        tolerance: Fractional tolerance for distribution balance (default 5%).
        min_payload_length: Minimum payload string length.
        max_payload_length: Maximum payload string length.

    Returns:
        A :class:`ValidationReport` with detailed findings.
    """
    report = ValidationReport()
    report.total = len(corpus)

    seen_ids: Set[str] = set()
    seen_payloads: Set[str] = set()
    valid_difficulties = {"easy", "medium", "hard"}
    observed_categories: Set[AttackCategory] = set()
    invalid_count = 0

    for sample in corpus:
        sample_valid = True

        # Duplicate ID check
        if sample.id in seen_ids:
            report.errors.append(f"Duplicate ID: {sample.id}")
            sample_valid = False
        seen_ids.add(sample.id)

        # Duplicate payload check
        payload_hash = sample.payload.strip()
        if payload_hash in seen_payloads:
            report.warnings.append(f"Duplicate payload in sample {sample.id}")
        seen_payloads.add(payload_hash)

        # Category tracking
        observed_categories.add(sample.category)

        # Payload quality
        if not sample.payload or not sample.payload.strip():
            report.errors.append(f"Empty payload in sample {sample.id}")
            sample_valid = False
        elif len(sample.payload) < min_payload_length:
            report.warnings.append(
                f"Short payload ({len(sample.payload)} chars) in sample {sample.id}"
            )
        elif len(sample.payload) > max_payload_length:
            report.warnings.append(
                f"Long payload ({len(sample.payload)} chars) in sample {sample.id}"
            )

        # Null byte check
        if "\x00" in sample.payload:
            report.errors.append(f"Null byte in payload of sample {sample.id}")
            sample_valid = False

        # Difficulty check
        if sample.difficulty not in valid_difficulties:
            report.errors.append(
                f"Invalid difficulty '{sample.difficulty}' in sample {sample.id}"
            )
            sample_valid = False

        if not sample_valid:
            invalid_count += 1

    report.invalid = invalid_count
    report.valid = report.total - invalid_count

    # Which corpus is this? The extension is a separate corpus, not a
    # replacement, so it is validated against its own expectations rather than
    # loosening the published ones.
    extended = bool(observed_categories & EXTENSION_CATEGORIES)
    expected_total = EXPECTED_EXTENDED_TOTAL if extended else EXPECTED_TOTAL
    expected_subcategories = (
        EXPECTED_EXTENDED_SUBCATEGORY_DISTRIBUTION
        if extended
        else EXPECTED_SUBCATEGORY_DISTRIBUTION
    )
    required_categories = (
        PUBLISHED_CATEGORIES | EXTENSION_CATEGORIES if extended else PUBLISHED_CATEGORIES
    )

    # Total count check
    if report.total != expected_total:
        report.errors.append(
            f"Expected {expected_total} samples, got {report.total}"
        )

    # Category coverage check
    missing_cats = required_categories - observed_categories
    if missing_cats:
        for cat in missing_cats:
            report.errors.append(f"Missing category: {cat.value}")

    # Distribution checks
    report.distribution = corpus.distribution()
    report.subcategory_distribution = corpus.subcategory_distribution()

    for top_cat, expected in EXPECTED_DISTRIBUTION.items():
        actual = report.distribution.get(top_cat, 0)
        diff = abs(actual - expected)
        if diff > expected * tolerance:
            report.warnings.append(
                f"Distribution imbalance for '{top_cat}': "
                f"expected {expected}, got {actual} "
                f"(diff={diff}, tolerance={expected * tolerance:.0f})"
            )

    for subcat, expected in expected_subcategories.items():
        actual = report.subcategory_distribution.get(subcat, 0)
        if actual != expected:
            report.warnings.append(
                f"Subcategory count mismatch for '{subcat}': "
                f"expected {expected}, got {actual}"
            )

    # Overall pass/fail
    report.passed = len(report.errors) == 0

    return report
