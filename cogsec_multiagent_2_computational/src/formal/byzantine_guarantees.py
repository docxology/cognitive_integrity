"""Theorem 5.3 validation: Byzantine fault tolerance n >= 3f+1.

Byzantine consensus only reaches a correct result when the number of agents
satisfies ``n >= 3f + 1``, where ``f`` is the number of Byzantine
(adversarial) agents.

Why the simulation is quorum-based
----------------------------------
An earlier version of this validator averaged all ``n`` votes and declared
consensus correct when the mean exceeded 0.5.  Plain averaging tolerates far
more than ``n/3`` adversaries (roughly ``0.58 n`` with the vote distributions
used), so the simulated outcome did not depend on the bound at all: replacing
``n >= 3f + 1`` with ``n >= 2f + 1`` left the validator reporting a 100% pass.
The check therefore proved nothing about the theorem.

The simulation below models the argument that actually produces the bound.
A correct agent cannot wait for more than ``n - f`` responses, because the
``f`` Byzantine agents may stay silent.  A worst-case adversary schedules
delivery so that its ``f`` votes are all inside that quorum and ``f`` honest
votes are excluded, leaving ``n - 2f`` honest votes.  Majority within the
quorum therefore decides correctly exactly when ``n - 2f > f``, i.e. when
``n >= 3f + 1``.  Simulated success now tracks the bound, so mutating the
predicate is detected.
"""

from __future__ import annotations

from typing import Callable, Optional

import numpy as np

from utils.random_seed import get_rng

from .theorem_registry import TheoremResult, TheoremStatus

#: Fraction of rounds that must decide correctly for a configuration to count
#: as "consensus reached".
SUCCESS_RATE_THRESHOLD = 0.8
#: Fraction of configurations on each arm that must behave as predicted.
ARM_AGREEMENT_THRESHOLD = 0.95
#: Standard deviation of honest agents' noisy votes around the ground truth.
HONEST_VOTE_NOISE = 0.05
#: Upper bound (exclusive) on adversarial votes; below the 0.5 decision line.
BYZANTINE_VOTE_MAX = 0.5

#: Signature of a tolerance predicate: (n, f) -> "bound satisfied".
BoundPredicate = Callable[[int, int], bool]


def default_bound_predicate(n: int, f: int) -> bool:
    """Theorem 5.3's tolerance condition: ``n >= 3f + 1``."""
    return n >= 3 * f + 1


def _simulate_quorum_agreement(
    n: int, f: int, rng: np.random.Generator, n_rounds: int
) -> float:
    """Simulate worst-case-scheduled quorum agreement; return the success rate.

    Honest agents vote for the ground truth (1.0, with Gaussian noise);
    Byzantine agents vote for the opposing value (uniform in
    ``[0, BYZANTINE_VOTE_MAX)``).  The adversary controls message delivery and
    fills the ``n - f`` response quorum with all of its own votes first, so the
    quorum holds ``max(n - 2f, 0)`` honest votes.  A round decides correctly
    when a strict majority of quorum members voted above the 0.5 decision line.

    Args:
        n: Total agents.
        f: Byzantine agents.
        rng: Seeded generator.
        n_rounds: Rounds to simulate.

    Returns:
        Fraction of rounds that decided the correct value.
    """
    quorum_size = max(n - f, 0)
    if quorum_size == 0:
        return 0.0
    byzantine_in_quorum = min(f, quorum_size)
    honest_in_quorum = quorum_size - byzantine_in_quorum

    correct_rounds = 0
    for _ in range(n_rounds):
        honest_votes = np.clip(
            np.ones(honest_in_quorum)
            + rng.normal(0, HONEST_VOTE_NOISE, size=honest_in_quorum),
            0.0,
            1.0,
        )
        byzantine_votes = rng.uniform(
            0.0, BYZANTINE_VOTE_MAX, size=byzantine_in_quorum
        )
        quorum_votes = np.concatenate([honest_votes, byzantine_votes])
        supporting = int(np.count_nonzero(quorum_votes > 0.5))
        if supporting * 2 > quorum_size:
            correct_rounds += 1

    return correct_rounds / n_rounds


def validate_byzantine_bound(
    max_n: int = 30,
    seed: int = 42,
    n_rounds: int = 20,
    bound_predicate: Optional[BoundPredicate] = None,
    **kwargs,
) -> TheoremResult:
    """Validate Theorem 5.3: correct consensus requires ``n >= 3f+1``.

    Both arms of the claim are checked, and both must hold for a PASS:

    * configurations satisfying the bound must reach correct consensus, and
    * configurations violating it must fail to.

    The earlier implementation ignored the second arm entirely, so a predicate
    that admitted unsafe configurations still passed.

    Args:
        max_n: Largest agent count to sweep.
        seed: Random seed.
        n_rounds: Rounds simulated per (n, f) configuration.
        bound_predicate: Tolerance condition under test.  Defaults to
            :func:`default_bound_predicate` (``n >= 3f + 1``).  Tests inject a
            deliberately wrong predicate (``n >= 2f + 1``) as a positive
            control, proving the validator can report FAILED.

    Returns:
        TheoremResult for theorem 5.3.
    """
    rng = get_rng(seed)
    predicate = bound_predicate or default_bound_predicate
    predicate_name = getattr(predicate, "__name__", repr(predicate))

    tests_run = 0
    valid_correct = 0
    valid_total = 0
    invalid_failures = 0
    invalid_total = 0

    for n in range(4, max_n + 1):
        for f in range(1, n):
            tests_run += 1
            success_rate = _simulate_quorum_agreement(n, f, rng, n_rounds)

            if predicate(n, f):
                valid_total += 1
                if success_rate >= SUCCESS_RATE_THRESHOLD:
                    valid_correct += 1
            else:
                invalid_total += 1
                if success_rate < SUCCESS_RATE_THRESHOLD:
                    invalid_failures += 1

    valid_success_rate = valid_correct / valid_total if valid_total > 0 else 0.0
    invalid_failure_rate = (
        invalid_failures / invalid_total if invalid_total > 0 else 1.0
    )
    passed = (
        valid_success_rate >= ARM_AGREEMENT_THRESHOLD
        and invalid_failure_rate >= ARM_AGREEMENT_THRESHOLD
    )

    return TheoremResult(
        theorem_id="5.3",
        name="Byzantine Fault Tolerance",
        status=TheoremStatus.PASSED if passed else TheoremStatus.FAILED,
        evidence=(
            f"Byzantine consensus correct in {valid_success_rate:.1%} of "
            f"tolerated cases ({valid_correct}/{valid_total}) and failed in "
            f"{invalid_failure_rate:.1%} of untolerated cases "
            f"({invalid_failures}/{invalid_total}) under predicate "
            f"'{predicate_name}'."
        ),
        details={
            "tests_run": tests_run,
            "valid_correct": valid_correct,
            "valid_total": valid_total,
            "valid_success_rate": valid_success_rate,
            "invalid_failures": invalid_failures,
            "invalid_total": invalid_total,
            "invalid_failure_rate": invalid_failure_rate,
            "predicate": predicate_name,
        },
    )
