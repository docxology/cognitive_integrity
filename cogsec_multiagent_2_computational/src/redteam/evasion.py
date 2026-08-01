"""Mutation-operator evasion sweep against the real CognitiveFirewall.

An *evasion* is a mutation that converts a payload the firewall flags
(``REJECT``/``QUARANTINE``) into one it accepts.  The sweep reports, per
mutation operator, how many of the flagged payloads it converts.

Why this module exists
----------------------
The sweep previously lived inline in ``scripts/run_redteam.py`` and was
vacuous in three independent ways, all of which this module guards against:

1. **Duplicate-inflated denominator.**  It drew payloads from
   ``AdversarialGenerator.generate_batch``, which emits one of only 16 distinct
   template strings regardless of ``n``.  A 950-attack "sweep" therefore had an
   effective sample size of 16, and its flagged subset was 67 copies of a
   *single* string.  :func:`flagged_payloads` de-duplicates and returns the
   distinct set, so the denominator counts independent payloads.
2. **No anti-vacuity guard.**  A denominator of 11 was reported without
   comment.  :func:`run_evasion_sweep` raises :class:`VacuousSweepError` below
   ``min_denominator``.
3. **No uncertainty.**  A rate of ``0.000`` over n=11 is indistinguishable
   from 0.30.  Every :class:`OperatorEvasion` now carries a Wilson interval.

A uniformly-zero result is still a legitimate finding — it means the operators
cannot defeat the detector — but it must be reported with its denominator and
interval so a reader can tell "measured zero" from "measured nothing".
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics.confidence import wilson_ci
from typing import Any, Callable, Dict, Iterable, List, Sequence

#: Fewest distinct flagged payloads for a sweep to carry any information.
#: Below this the Wilson interval spans most of [0, 1] and the measurement
#: cannot discriminate between competing operators.
DEFAULT_MIN_DENOMINATOR = 50


class VacuousSweepError(ValueError):
    """Raised when the evasion denominator is too small to measure anything."""


@dataclass(frozen=True)
class OperatorEvasion:
    """Evasion statistics for one mutation operator.

    Attributes:
        operator: Mutation operator name.
        attempts: Number of distinct flagged payloads mutated (denominator).
        successes: How many mutated payloads the firewall then accepted.
        evasion_rate: ``successes / attempts``.
        ci_low: Lower bound of the Wilson interval.
        ci_high: Upper bound of the Wilson interval.
        confidence: Confidence level of the interval.
    """

    operator: str
    attempts: int
    successes: int
    evasion_rate: float
    ci_low: float
    ci_high: float
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a JSON-safe dict."""
        return {
            "operator": self.operator,
            "attempts": self.attempts,
            "successful": self.successes,
            "evasion_rate": self.evasion_rate,
            "ci_low": self.ci_low,
            "ci_high": self.ci_high,
            "confidence": self.confidence,
        }


def flagged_payloads(
    payloads: Iterable[str],
    is_flagged: Callable[[str], bool],
) -> List[str]:
    """Return the distinct payloads the detector flags, in sorted order.

    De-duplication is the point: a corpus that repeats one string 67 times
    provides one payload's worth of evidence, not 67.  Sorting makes the
    denominator order-independent and the sweep reproducible.

    Args:
        payloads: Candidate attack payloads (duplicates permitted).
        is_flagged: Predicate that is true when the detector does *not*
            accept the payload.

    Returns:
        Sorted list of distinct flagged payloads.
    """
    return sorted({p for p in payloads if is_flagged(p)})


def run_evasion_sweep(
    payloads: Sequence[str],
    operators: Sequence[str],
    mutate: Callable[[str, str], str],
    is_flagged: Callable[[str], bool],
    *,
    min_denominator: int = DEFAULT_MIN_DENOMINATOR,
    confidence: float = 0.95,
) -> Dict[str, OperatorEvasion]:
    """Measure per-operator evasion over an already-flagged payload set.

    Args:
        payloads: Distinct payloads the detector currently flags — the
            denominator. Use :func:`flagged_payloads` to build it.
        operators: Mutation operator names to sweep.
        mutate: ``(payload, operator) -> mutated_payload``.
        is_flagged: Predicate that is true when the detector does *not*
            accept a payload.
        min_denominator: Refuse to report below this many payloads.
        confidence: Confidence level for the Wilson intervals.

    Returns:
        Mapping of operator name → :class:`OperatorEvasion`.

    Raises:
        VacuousSweepError: If ``len(payloads) < min_denominator`` or
            ``operators`` is empty — in either case the sweep would report a
            number that means nothing.
    """
    if not operators:
        raise VacuousSweepError("evasion sweep has no mutation operators")
    n = len(payloads)
    if n < min_denominator:
        raise VacuousSweepError(
            f"evasion sweep denominator too small: N={n} distinct flagged "
            f"payloads (minimum {min_denominator}). A rate measured over "
            f"N={n} cannot distinguish 0% from 30%."
        )

    results: Dict[str, OperatorEvasion] = {}
    for operator in operators:
        successes = sum(1 for p in payloads if not is_flagged(mutate(p, operator)))
        rate, low, high = wilson_ci(successes, n, confidence=confidence)
        results[operator] = OperatorEvasion(
            operator=operator,
            attempts=n,
            successes=successes,
            evasion_rate=rate,
            ci_low=low,
            ci_high=high,
            confidence=confidence,
        )
    return results
