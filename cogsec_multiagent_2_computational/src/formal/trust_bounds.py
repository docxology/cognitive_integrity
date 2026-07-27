"""Theorem 3.1 validation: trust delegation decay bound.

The theorem states

    T_delegated(i->k via j) <= min(T(i->j), T(j->k)) * delta^d

for a delegation chain of depth *d* with decay factor ``delta`` in (0, 1).
Two independent properties follow, and both are checked here against the
*actual* delegation implementation (:meth:`core.trust.TrustCalculus.delegate_trust`)
rather than against a restatement of its own formula:

1. **Absolute decay bound** — ``T_delegated <= delta^d``.
2. **Non-amplification (weakest link)** — ``T_delegated <= min(source, target) * delta^d``.

Property 1 alone is vacuous: because every trust value lies in [0, 1], *any*
aggregator ``g(source, target) in [0, 1]`` scaled by ``delta^d`` satisfies it.
In particular an implementation that used ``max`` instead of ``min`` — which
*amplifies* trust through delegation, the exact failure the theorem forbids —
passed the old check unchanged.  Property 2 binds the verdict to the sampled
``(source, target)`` pair and rejects such an implementation.
"""

from __future__ import annotations

from typing import Callable, Optional

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

#: Signature of a delegation implementation: (source, target, depth) -> trust.
DelegateFn = Callable[[float, float, int], float]


def validate_trust_bound(
    delta: float = DECAY_FACTOR_DEFAULT,
    max_depth: int = MAX_DEPTH_DEFAULT,
    n_trials: int = N_TRIALS_DEFAULT,
    seed: int = 42,
    delegate_fn: Optional[DelegateFn] = None,
    **kwargs,
) -> TheoremResult:
    """Validate Theorem 3.1: trust delegation decays as ``min(s, t) * delta^d``.

    For each depth ``d`` in ``[1 .. max_depth]``, generate *n_trials* random
    (source, target) trust pairs and check both the absolute decay bound and
    the non-amplification bound.

    Args:
        delta: Decay factor in (0, 1).
        max_depth: Maximum delegation depth to test.
        n_trials: Number of random chains per depth.
        seed: Random seed.
        delegate_fn: Delegation implementation under test.  Defaults to the
            production :meth:`core.trust.TrustCalculus.delegate_trust`.  Tests
            inject a deliberately amplifying stub here as a positive control,
            proving the checker can actually report FAILED.

    Returns:
        TheoremResult with PASSED only if every sample satisfies both bounds.
    """
    rng = np.random.default_rng(seed)
    # Constructed unconditionally: TrustConfig validates ``delta`` in (0, 1),
    # so an out-of-range decay is rejected even with an injected delegate_fn.
    config = TrustConfig(alpha=TRUST_ALPHA, beta=TRUST_BETA, gamma=TRUST_GAMMA, decay=delta)
    calculus = TrustCalculus(config)

    delegate: DelegateFn
    if delegate_fn is None:
        delegate = calculus.delegate_trust
        implementation = "core.trust.TrustCalculus.delegate_trust"
    else:
        delegate = delegate_fn
        implementation = getattr(delegate_fn, "__name__", repr(delegate_fn))

    total_samples = 0
    decay_violations = 0
    amplification_violations = 0
    max_violation = 0.0
    max_amplification = 0.0

    for d in range(1, max_depth + 1):
        decay_bound = delta ** d
        for _ in range(n_trials):
            total_samples += 1
            source_trust = float(rng.uniform(TRUST_MIN, TRUST_MAX))
            target_trust = float(rng.uniform(TRUST_MIN, TRUST_MAX))

            delegated = delegate(source_trust, target_trust, d)

            # Property 1: absolute decay bound.
            if delegated > decay_bound + TOLERANCE_EPSILON:
                decay_violations += 1
                max_violation = max(max_violation, delegated - decay_bound)

            # Property 2: non-amplification — delegation may never yield more
            # trust than the weakest link in the chain, after decay.
            weakest_link_bound = min(source_trust, target_trust) * decay_bound
            if delegated > weakest_link_bound + TOLERANCE_EPSILON:
                amplification_violations += 1
                max_amplification = max(
                    max_amplification, delegated - weakest_link_bound
                )

    violations = decay_violations + amplification_violations
    details = {
        "delta": delta,
        "max_depth": max_depth,
        "n_trials": n_trials,
        "total_samples": total_samples,
        "violations": violations,
        "max_violation": max_violation,
        "decay_violations": decay_violations,
        "amplification_violations": amplification_violations,
        "max_amplification": max_amplification,
        "implementation": implementation,
    }

    if violations == 0:
        return TheoremResult(
            theorem_id="3.1",
            name="Trust delegation decay bound",
            status=TheoremStatus.PASSED,
            evidence=(
                f"All {total_samples} samples satisfy T <= delta^d and "
                f"T <= min(source, target) * delta^d "
                f"(max violation: {max_violation:.6f}, "
                f"max amplification: {max_amplification:.6f})"
            ),
            details=details,
        )
    return TheoremResult(
        theorem_id="3.1",
        name="Trust delegation decay bound",
        status=TheoremStatus.FAILED,
        evidence=(
            f"{decay_violations}/{total_samples} samples violated T <= delta^d "
            f"and {amplification_violations}/{total_samples} amplified trust "
            f"beyond min(source, target) * delta^d "
            f"(max violation: {max_violation:.6f}, "
            f"max amplification: {max_amplification:.6f})"
        ),
        details=details,
    )
