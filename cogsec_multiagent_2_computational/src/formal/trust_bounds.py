"""Theorem 3.1 validation: trust delegation decay bound T_delegated <= delta^d.

For each delegation depth *d*, the delegated trust score must satisfy
``T_delegated <= delta^d`` where delta is the decay factor.  This is
validated empirically across many random trust chains.
"""

from __future__ import annotations

import numpy as np

try:
    from core.trust import TrustCalculus, TrustConfig
except (ImportError, ModuleNotFoundError):
    from src.core.trust import TrustCalculus, TrustConfig
from .theorem_registry import TheoremResult, TheoremStatus


def validate_trust_bound(
    delta: float = 0.85,
    max_depth: int = 10,
    n_trials: int = 1000,
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
    config = TrustConfig(alpha=0.3, beta=0.4, gamma=0.3, decay=delta)
    calculus = TrustCalculus(config)

    total_samples = 0
    violations = 0
    max_violation = 0.0

    for d in range(1, max_depth + 1):
        bound = delta ** d
        for _ in range(n_trials):
            total_samples += 1
            # Generate random trust values for the chain
            source_trust = rng.uniform(0.0, 1.0)
            target_trust = rng.uniform(0.0, 1.0)

            delegated = calculus.delegate_trust(source_trust, target_trust, depth=d)

            if delegated > bound + 1e-10:  # small epsilon for float
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
