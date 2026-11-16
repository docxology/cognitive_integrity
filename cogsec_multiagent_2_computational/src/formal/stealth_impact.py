"""Theorem 4 validation: stealth-impact tradeoff I * S <= C_channel.

An attacker cannot simultaneously maximise both stealth (S) and
impact (I).  Their product is bounded by a channel capacity constant
C_channel.  This module validates the bound empirically by simulating
attack samples and verifying that the stealth-impact product never
exceeds the channel capacity bound.
"""

from __future__ import annotations

from src.utils.random_seed import get_rng

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

    details = {
        "c_channel": c_channel,
        "n_trials": n_trials,
        "n_detected": violations,
        "max_product": max_product,
        "detection_model": "fail-closed by construction (schematic)",
    }
    if n_trials <= 0:
        return TheoremResult(
            theorem_id="4",
            name="Stealth-Impact Tradeoff",
            status=TheoremStatus.FAILED,
            evidence="No stealth-impact samples were generated; the theorem was not validated.",
            details=details,
        )

    # Detection is defined by the same inequality being checked, so this
    # schematic cannot falsify the theorem and must not report a proof.
    return TheoremResult(
        theorem_id="4",
        name="Stealth-Impact Tradeoff",
        status=TheoremStatus.SKIPPED,
        evidence=(
            f"Schematic consistency only, not theorem validation: "
            f"{n_trials - violations} of {n_trials} attacks were admitted "
            f"by the construction I*S <= {c_channel:.2f}; {violations} were "
            "detected by that same construction."
        ),
        details=details,
    )
