"""Sweep the firewall's thresholds and report the operating curve.

Part 3 reports a τ₂ tuning outcome as an observed deployment result: moving the
quarantine threshold from 0.50 to 0.55 drops the false-positive rate from 6% to
3% while true positives fall from 72% to 68%. Four numbers, presented as a
before-and-after, and nothing had swept anything: the thresholds are read from
``FirewallConfig`` by the ledger, but no code varied one and measured what
happened.

This module does. It is deliberately a module rather than a script body,
because two other things want it: the operating-point discussion in Part 2's
supplement, and any future question about where to sit on the curve for a
particular deployment. A sweep that lives inside a script can only ever answer
the question the script was written for.

The scoring convention
----------------------
An input is *flagged* when the firewall does anything other than accept it --
``QUARANTINE`` and ``REJECT`` both count. That is the convention an operator
experiences: a quarantined message is one a human has to look at, so it lands
in the false-positive budget exactly as a rejection does. Counting only
``REJECT`` would report a false-positive rate no deployment ever sees.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable, Sequence

from core.firewall import Classification, CognitiveFirewall, FirewallConfig

__all__ = ["ThresholdPoint", "sweep_quarantine_threshold", "sweep_reject_threshold"]


@dataclass(frozen=True)
class ThresholdPoint:
    """One operating point: what the firewall catches and what it costs.

    Attributes
    ----------
    tau:
        The threshold value swept to.
    which:
        Which threshold was varied, ``"quarantine"`` or ``"reject"``.
    tpr:
        Fraction of attacks flagged.
    fpr:
        Fraction of benign messages flagged.
    quarantine_rate / reject_rate:
        The two dispositions separately, over the attack arm. An operator
        cares which one a flag was, even though both count as flagged.
    n_attacks / n_benign:
        Arm sizes, carried so a rate is never separated from its denominator.
    """

    tau: float
    which: str
    tpr: float
    fpr: float
    quarantine_rate: float
    reject_rate: float
    n_attacks: int
    n_benign: int

    @property
    def youden_j(self) -> float:
        return self.tpr - self.fpr


def _flagged(result: Classification) -> bool:
    """Anything but ACCEPT costs someone something."""
    return result is not Classification.ACCEPT


def _measure(
    firewall: CognitiveFirewall,
    attacks: Sequence[str],
    benign: Sequence[str],
    tau: float,
    which: str,
) -> ThresholdPoint:
    attack_results = [firewall.classify(p) for p in attacks]
    benign_results = [firewall.classify(b) for b in benign]
    n_a, n_b = len(attacks), len(benign)
    return ThresholdPoint(
        tau=tau,
        which=which,
        tpr=sum(1 for r in attack_results if _flagged(r)) / n_a,
        fpr=sum(1 for r in benign_results if _flagged(r)) / n_b,
        quarantine_rate=sum(
            1 for r in attack_results if r is Classification.QUARANTINE
        ) / n_a,
        reject_rate=sum(1 for r in attack_results if r is Classification.REJECT) / n_a,
        n_attacks=n_a,
        n_benign=n_b,
    )


def _sweep(
    field: str,
    which: str,
    taus: Iterable[float],
    attacks: Sequence[str],
    benign: Sequence[str],
    base: FirewallConfig | None = None,
) -> list[ThresholdPoint]:
    if not attacks or not benign:
        raise ValueError(
            f"both arms must be non-empty; got {len(attacks)} attacks and "
            f"{len(benign)} benign. A sweep over one arm reports a rate with no "
            f"cost beside it, which is how a threshold gets recommended."
        )
    config = base or FirewallConfig()
    points: list[ThresholdPoint] = []
    for tau in taus:
        if not 0.0 <= tau <= 1.0:
            raise ValueError(f"threshold {tau} is outside [0, 1]")
        firewall = CognitiveFirewall(replace(config, **{field: tau}))
        points.append(_measure(firewall, attacks, benign, tau, which))
    return points


def sweep_quarantine_threshold(
    taus: Iterable[float],
    attacks: Sequence[str],
    benign: Sequence[str],
    base: FirewallConfig | None = None,
) -> list[ThresholdPoint]:
    """Vary τ₂, holding τ₁ at its shipped value.

    This is the sweep Part 3's case study describes. The reject threshold is
    held fixed deliberately: moving both at once produces a surface, and the
    claim being checked is about one knob.
    """
    return _sweep("suspicious_threshold", "quarantine", taus, attacks, benign, base)


def sweep_reject_threshold(
    taus: Iterable[float],
    attacks: Sequence[str],
    benign: Sequence[str],
    base: FirewallConfig | None = None,
) -> list[ThresholdPoint]:
    """Vary τ₁, holding τ₂ at its shipped value."""
    return _sweep("injection_threshold", "reject", taus, attacks, benign, base)
