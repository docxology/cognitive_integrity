"""Theorem 3.1 validation: trust delegation decay bound T_delegated <= delta^d.

For each delegation depth *d*, the delegated trust score must satisfy
``T_delegated <= delta^d`` where delta is the decay factor.  This is
validated empirically across many random trust chains by simulating trust
delegation through multi-hop networks and verifying exponential decay.
"""

from __future__ import annotations

import numpy as np

from core.trust import TrustCalculus, TrustConfig
from .theorem_registry import TheoremResult, TheoremStatus

DECAY_FACTOR_DEFAULT = 0.85
MAX_DEPTH_DEFAULT = 10
N_TRIALS_DEFAULT = 1000
TRUST_MIN = 0.0
TRUST_MAX = 1.0
TRUST_ALPHA = 0.3
TRUST_BETA = 0.4
TRUST_GAMMA = 0.3
TOLERANCE_EPSILON = 1e-10


def validate_trust_bound(
    delta: float = DECAY_FACTOR_DEFAULT,
    max_depth: int = MAX_DEPTH_DEFAULT,
    n_trials: int = N_TRIALS_DEFAULT,
    seed: int = 42,
    **kwargs,
) -> TheoremResult:
    """Validate Theorem 3.1: trust delegation decays as delta^d.

    For each depth ``d`` in ``[1 .. max_depth]``, generate *n_trials*
    random trust chains and verify that the delegated trust never
    exceeds ``delta^d``.

    Args:
        delta: Decay factor in (0, 1).
        max_depth: Maximum delegation depth to test.
        n_trials: Number of random chains per depth.
        seed: Random seed.

    Returns:
        TheoremResult with PASSED if all samples satisfy the bound.
    """
    rng = np.random.default_rng(seed)
    config = TrustConfig(alpha=TRUST_ALPHA, beta=TRUST_BETA, gamma=TRUST_GAMMA, decay=delta)
    calculus = TrustCalculus(config)

    total_samples = 0
    violations = 0
    max_violation = 0.0

    for d in range(1, max_depth + 1):
        bound = delta ** d
        for _ in range(n_trials):
            total_samples += 1
            source_trust = rng.uniform(TRUST_MIN, TRUST_MAX)
            target_trust = rng.uniform(TRUST_MIN, TRUST_MAX)

            delegated = calculus.delegate_trust(source_trust, target_trust, depth=d)

            if delegated > bound + TOLERANCE_EPSILON:
                violations += 1
                violation_amount = delegated - bound
                max_violation = max(max_violation, violation_amount)

    if violations == 0:
        return TheoremResult(
            theorem_id="3.1",
            name="Trust delegation decay bound",
            status=TheoremStatus.PASSED,
            evidence=(
                f"All {total_samples} samples satisfy T <= delta^d "
                f"(max violation: {max_violation:.6f})"
            ),
            details={
                "delta": delta,
                "max_depth": max_depth,
                "n_trials": n_trials,
                "total_samples": total_samples,
                "violations": violations,
                "max_violation": max_violation,
            },
        )
    else:
        return TheoremResult(
            theorem_id="3.1",
            name="Trust delegation decay bound",
            status=TheoremStatus.FAILED,
            evidence=(
                f"{violations}/{total_samples} samples violated T <= delta^d "
                f"(max violation: {max_violation:.6f})"
            ),
            details={
                "delta": delta,
                "max_depth": max_depth,
                "n_trials": n_trials,
                "total_samples": total_samples,
                "violations": violations,
                "max_violation": max_violation,
            },
        )
