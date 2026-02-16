"""Maps Paper 1 theorems to computational validators.

Provides a registry that associates theorem identifiers (e.g. "3.1", "4")
with executable validator functions.  Running ``validate_all`` produces a
complete validation report.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List


class TheoremStatus(Enum):
    """Result status for a theorem validation."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TheoremResult:
    """Result of validating a single theorem.

    Attributes:
        theorem_id: Identifier (e.g. ``"3.1"``).
        name: Human-readable theorem name.
        status: Validation outcome.
        evidence: Summary string describing evidence.
        details: Additional structured data from the validator.
    """

    theorem_id: str
    name: str
    status: TheoremStatus
    evidence: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


class TheoremRegistry:
    """Registry mapping Paper 1 theorem IDs to validator functions.

    Validators are callables with signature ``(**kwargs) -> TheoremResult``.

    Usage::

        registry = TheoremRegistry()
        result = registry.validate("3.1", delta=0.85)
        all_results = registry.validate_all(seed=42)
    """

    def __init__(self) -> None:
        self._validators: Dict[str, tuple] = {}  # id -> (name, fn)
        self._register_defaults()

    def register(
        self,
        theorem_id: str,
        name: str,
        validator_fn: Callable[..., TheoremResult],
    ) -> None:
        """Register a validator for a theorem.

        Args:
            theorem_id: Unique theorem identifier (e.g. ``"3.1"``).
            name: Human-readable name.
            validator_fn: Callable that returns ``TheoremResult``.
        """
        self._validators[theorem_id] = (name, validator_fn)

    def validate(self, theorem_id: str, **kwargs: Any) -> TheoremResult:
        """Run the validator for a single theorem.

        Args:
            theorem_id: Theorem to validate.
            **kwargs: Passed through to the validator function.

        Returns:
            TheoremResult from the validator.

        Raises:
            KeyError: If *theorem_id* is not registered.
        """
        if theorem_id not in self._validators:
            raise KeyError(f"Unknown theorem: {theorem_id}")

        name, fn = self._validators[theorem_id]
        try:
            return fn(**kwargs)
        except Exception as exc:
            return TheoremResult(
                theorem_id=theorem_id,
                name=name,
                status=TheoremStatus.ERROR,
                evidence=f"Validator raised {type(exc).__name__}: {exc}",
            )

    def validate_all(self, **kwargs: Any) -> List[TheoremResult]:
        """Run all registered validators.

        Args:
            **kwargs: Passed through to every validator.

        Returns:
            List of TheoremResult, one per registered theorem.
        """
        results: List[TheoremResult] = []
        for tid in sorted(self._validators.keys()):
            results.append(self.validate(tid, **kwargs))
        return results

    def summary(self) -> Dict[str, int]:
        """Count results by status from the last ``validate_all`` run.

        Must call ``validate_all`` first to populate results.

        Returns:
            Dict mapping status name to count.
        """
        # Run all with defaults to get current state
        results = self.validate_all()
        counts: Dict[str, int] = {s.value: 0 for s in TheoremStatus}
        for r in results:
            counts[r.status.value] += 1
        return counts

    def _register_defaults(self) -> None:
        """Pre-register all Paper 1 theorems (3.1, 3.2, 4, 5.3, 6)."""
        from .byzantine_guarantees import validate_byzantine_bound
        from .composition_proofs import (
            validate_associativity,
            validate_parallel_composition,
            validate_series_composition,
        )
        from .latency_bound import validate_latency_bound
        from .stealth_impact import validate_stealth_impact
        from .trust_bounds import validate_trust_bound

        self.register(
            "3.1",
            "Trust delegation decay bound",
            validate_trust_bound,
        )
        self.register(
            "3.2a",
            "Series composition P_miss = product(1-r_i)",
            validate_series_composition,
        )
        self.register(
            "3.2b",
            "Parallel composition DR >= max(r_i)",
            validate_parallel_composition,
        )
        self.register(
            "3.2c",
            "Composition associativity",
            validate_associativity,
        )
        self.register(
            "4",
            "Stealth-impact tradeoff I*S <= C_channel",
            validate_stealth_impact,
        )
        self.register(
            "5.3",
            "Byzantine fault tolerance n >= 3f+1",
            validate_byzantine_bound,
        )
        self.register(
            "6",
            "CIF latency overhead bound 23%",
            validate_latency_bound,
        )
