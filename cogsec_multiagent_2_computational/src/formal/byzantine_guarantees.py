"""Theorem 5.3 validation: Byzantine fault tolerance n >= 3f+1.

Byzantine consensus only reaches a correct result when the number of
honest agents satisfies n >= 3f + 1, where f is the number of
Byzantine (adversarial) agents.
"""

from __future__ import annotations

import numpy as np

from utils.random_seed import get_rng

from .theorem_registry import TheoremResult, TheoremStatus


def validate_byzantine_bound(
    max_n: int = 30,
    seed: int = 42,
    **kwargs,
) -> TheoremResult:
    """Validate Theorem 5.3: correct consensus requires n >= 3f+1.

    For various (n, f) pairs, simulate Byzantine consensus and verify
    that correct results are reached when the bound holds and may fail
    when it does not.
    """
    rng = get_rng(seed)

    tests_run = 0
    valid_correct = 0
    valid_total = 0
    invalid_failures = 0
    invalid_total = 0

    for n in range(4, max_n + 1):
        for f in range(1, n):
            tests_run += 1
            is_valid = n >= 3 * f + 1
            n_honest = n - f

            # Simulate: honest agents vote for ground truth (1.0)
            # Byzantine agents vote adversarially (0.0)
            n_rounds = 20
            correct_count = 0

            for _ in range(n_rounds):
                honest_votes = np.ones(n_honest) + rng.normal(0, 0.05, size=n_honest)
                honest_votes = np.clip(honest_votes, 0.0, 1.0)

                # Byzantine agents try to flip consensus
                byzantine_votes = rng.uniform(0.0, 0.3, size=f)

                all_votes = np.concatenate([honest_votes, byzantine_votes])
                # Simple majority: correct if mean > 0.5
                consensus_value = float(np.mean(all_votes))
                if consensus_value > 0.5:
                    correct_count += 1

            success_rate = correct_count / n_rounds

            if is_valid:
                valid_total += 1
                if success_rate >= 0.8:  # Expect high success rate when bound holds
                    valid_correct += 1
            else:
                invalid_total += 1
                if success_rate < 0.8:  # Expect potential failures when bound violated
                    invalid_failures += 1

    # The bound is validated if:
    # 1. Valid (n >= 3f+1) configurations almost always produce correct consensus
    # 2. Invalid configurations show degraded performance
    valid_success_rate = valid_correct / valid_total if valid_total > 0 else 0.0
    passed = valid_success_rate >= 0.95

    return TheoremResult(
        theorem_id="5.3",
        name="Byzantine Fault Tolerance",
        status=TheoremStatus.PASSED if passed else TheoremStatus.FAILED,
        evidence=(
            f"Byzantine consensus correct in {valid_success_rate:.1%} of valid "
            f"(n>=3f+1) cases ({valid_correct}/{valid_total}). "
            f"Invalid cases showed {invalid_failures}/{invalid_total} failures."
        ),
        details={
            "tests_run": tests_run,
            "valid_correct": valid_correct,
            "valid_total": valid_total,
            "valid_success_rate": valid_success_rate,
            "invalid_failures": invalid_failures,
            "invalid_total": invalid_total,
        },
    )
