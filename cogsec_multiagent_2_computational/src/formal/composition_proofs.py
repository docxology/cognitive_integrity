"""Theorems 3.1-3.2 validation: composition algebra properties.

Validates that series and parallel defense composition satisfies the
algebraic properties claimed in Paper 1.
"""

from __future__ import annotations

import numpy as np

from utils.random_seed import get_rng
from .theorem_registry import TheoremResult, TheoremStatus

_SIMULATION_ATTACKS: int = 10_000  # Monte-Carlo sample size for composition theorems


def validate_series_composition(
    n_modules: int = 5,
    n_trials: int = 1000,
    seed: int = 42,
    **kwargs,
) -> TheoremResult:
    """Validate series composition: P_miss = product(1 - r_i).

    For a series pipeline, the combined miss rate equals the product
    of individual miss rates.
    """
    rng = get_rng(seed)

    violations = 0
    max_error = 0.0

    for _ in range(n_trials):
        # Random detection rates for each module
        rates = rng.uniform(0.3, 0.95, size=n_modules)

        # Theoretical: P_miss = product(1 - r_i)
        p_miss_theoretical = float(np.prod(1.0 - rates))
        combined_theoretical = 1.0 - p_miss_theoretical

        # Empirical: simulate _SIMULATION_ATTACKS attacks
        n_attacks = _SIMULATION_ATTACKS
        detected = np.zeros(n_attacks, dtype=bool)
        for r in rates:
            module_detections = rng.random(n_attacks) < r
            detected |= module_detections
        combined_empirical = float(np.mean(detected))

        error = abs(combined_empirical - combined_theoretical)
        max_error = max(max_error, error)

        # Allow tolerance for sampling noise
        if error > 0.05:
            violations += 1

    passed = violations == 0

    return TheoremResult(
        theorem_id="3.1b",
        name="Series Composition Detection",
        status=TheoremStatus.PASSED if passed else TheoremStatus.FAILED,
        evidence=(
            f"Series composition P_miss = prod(1-r_i) validated across "
            f"{n_trials} trials (max error: {max_error:.4f}, violations: {violations})"
        ),
        details={
            "n_trials": n_trials,
            "n_modules": n_modules,
            "violations": violations,
            "max_error": max_error,
        },
    )


def validate_parallel_composition(
    n_modules: int = 5,
    n_trials: int = 1000,
    seed: int = 42,
    **kwargs,
) -> TheoremResult:
    """Validate parallel composition: detection rate >= max(r_i).

    Parallel composition always does at least as well as the best
    individual module.
    """
    rng = get_rng(seed)

    violations = 0

    for _ in range(n_trials):
        rates = rng.uniform(0.3, 0.95, size=n_modules)
        max_individual = float(np.max(rates))

        # Parallel with max-score fusion: combined >= max individual
        # With OR logic: 1 - product(1 - r_i) >= max(r_i)
        combined = 1.0 - float(np.prod(1.0 - rates))

        if combined < max_individual - 1e-10:
            violations += 1

    passed = violations == 0

    return TheoremResult(
        theorem_id="3.2",
        name="Parallel Composition Detection",
        status=TheoremStatus.PASSED if passed else TheoremStatus.FAILED,
        evidence=(
            f"Parallel composition rate >= max(r_i) validated across "
            f"{n_trials} trials (violations: {violations})"
        ),
        details={"n_trials": n_trials, "violations": violations},
    )


def validate_associativity(
    seed: int = 42,
    n_trials: int = 100,
    **kwargs,
) -> TheoremResult:
    """Validate composition associativity: compose(A, compose(B, C)) ~= compose(compose(A, B), C).

    Uses the series composition algebra which should be associative
    since it's based on multiplication of miss rates.
    """
    rng = get_rng(seed)

    max_error = 0.0

    for _ in range(n_trials):
        r_a = rng.uniform(0.3, 0.95)
        r_b = rng.uniform(0.3, 0.95)
        r_c = rng.uniform(0.3, 0.95)

        # Left-associated: compose(compose(A, B), C)
        ab_miss = (1.0 - r_a) * (1.0 - r_b)
        ab_rate = 1.0 - ab_miss
        left = 1.0 - (1.0 - ab_rate) * (1.0 - r_c)

        # Right-associated: compose(A, compose(B, C))
        bc_miss = (1.0 - r_b) * (1.0 - r_c)
        bc_rate = 1.0 - bc_miss
        right = 1.0 - (1.0 - r_a) * (1.0 - bc_rate)

        error = abs(left - right)
        max_error = max(max_error, error)

    passed = max_error < 1e-10

    return TheoremResult(
        theorem_id="3.3",
        name="Composition Associativity",
        status=TheoremStatus.PASSED if passed else TheoremStatus.FAILED,
        evidence=(
            f"Composition is associative: max error {max_error:.2e} across "
            f"{n_trials} trials"
        ),
        details={"n_trials": n_trials, "max_error": max_error},
    )
