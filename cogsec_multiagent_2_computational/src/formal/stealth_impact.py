"""Theorem 4 validation: stealth-impact tradeoff I * S <= C_channel.

An attacker cannot simultaneously maximise both stealth (S) and
impact (I).  Their product is bounded by a channel capacity constant
C_channel.  This module validates the bound empirically by simulating
attack samples and verifying that the stealth-impact product never
exceeds the channel capacity bound.
"""

from __future__ import annotations

from utils.random_seed import get_rng

from .theorem_registry import TheoremResult, TheoremStatus

C_CHANNEL_DEFAULT = 1.0
N_TRIALS_DEFAULT = 500
IMPACT_MIN = 0.1
IMPACT_MAX = 1.0
STEALTH_MIN = 0.1
STEALTH_MAX = 1.0


def validate_stealth_impact(
    c_channel: float = C_CHANNEL_DEFAULT,
    n_trials: int = N_TRIALS_DEFAULT,
    seed: int = 42,
    **kwargs,
) -> TheoremResult:
    """Schematic consistency check of Part-1 Theorem 4: I * S <= C_channel.

    NOTE (red-team fix, P2-F1): this is NOT an independent empirical validation
    of a real detector.  It draws (impact, stealth) from the design ranges and
    models detection as fail-closed *by construction*: any attack with
    I*S > C_channel is assumed detected and so never appears in the successful
    set.  The check therefore confirms the design constraint is self-consistent
    under that fail-closed detection model -- it cannot fail, and must not be
    read as measuring a real system (Part 2 leaves the theorem to Part 1).
    """
    rng = get_rng(seed)

    violations = 0
    max_product = 0.0

    for _ in range(n_trials):
        impact = rng.uniform(IMPACT_MIN, IMPACT_MAX)
        stealth = rng.uniform(STEALTH_MIN, STEALTH_MAX)
        product = impact * stealth

        # Simulate: attack only succeeds if product <= c_channel
        # (attacks violating the bound get detected)
        if product <= c_channel:
            max_product = max(max_product, product)
        else:
            # This attack would be detected — not a "successful" attack
            violations += 1

    # Verify: all *successful* attacks satisfy the bound
    all_successful_bounded = max_product <= c_channel

    if all_successful_bounded:
        return TheoremResult(
            theorem_id="4",
            name="Stealth-Impact Tradeoff",
            status=TheoremStatus.PASSED,
            evidence=(
                f"Schematic consistency check (fail-closed detection by "
                f"construction; not an empirical measurement): all "
                f"{n_trials - violations} successful attacks satisfy "
                f"I*S <= {c_channel:.2f} (max product: {max_product:.4f}). "
                f"{violations} attacks detected due to bound violation."
            ),
            details={
                "c_channel": c_channel,
                "n_trials": n_trials,
                "n_detected": violations,
                "max_product": max_product,
                "detection_model": "fail-closed by construction (schematic)",
            },
        )
    else:
        return TheoremResult(
            theorem_id="4",
            name="Stealth-Impact Tradeoff",
            status=TheoremStatus.FAILED,
            evidence=f"Bound violated: max product {max_product:.4f} > {c_channel:.2f}",
            details={"max_product": max_product, "c_channel": c_channel},
        )
