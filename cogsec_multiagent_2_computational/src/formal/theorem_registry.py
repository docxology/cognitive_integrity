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
        """Pre-register all Paper 1 theorems (3.1, 3.2, 4, 5.3, 6) and
        Paper 2 extensions (CT.1–CT.3, FEP.1–FEP.2).
        """
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

        # -------------------------------------------------------------
        # Paper 2 extensions: category theory and FEP.
        # -------------------------------------------------------------
        self.register(
            "CT.1",
            "Defense Category Laws "
            "(series composition is categorical composition)",
            _validate_ct1_defense_category_laws,
        )
        self.register(
            "CT.2",
            "Categorical Product "
            "(parallel composition is categorical product)",
            _validate_ct2_categorical_product,
        )
        self.register(
            "CT.3",
            "Monadic Detection Preservation "
            "(detection short-circuits via Err)",
            _validate_ct3_monadic_preservation,
        )
        self.register(
            "FEP.1",
            "Attack-FEP Equivalence (attack iff ΔF > κ_FEP)",
            _validate_fep1_attack_fep_equivalence,
        )
        self.register(
            "FEP.2",
            "Trust-Precision Duality "
            "(trust score equals FEP precision weight)",
            _validate_fep2_trust_precision_duality,
        )


# ---------------------------------------------------------------------------
# Paper 2 extension validators
# ---------------------------------------------------------------------------

def _validate_ct1_defense_category_laws(**_kwargs: Any) -> TheoremResult:
    """Check the three category laws on a simple trio of morphisms."""
    from utils.types import DefenseResult

    from .category_theory import (
        DefenseMorphism,
        verify_category_laws,
    )

    def make(name: str, thresh: float, score: float) -> DefenseMorphism:
        def _fn(state):
            x = float(state.get("x", 0.0))
            return DefenseResult(
                detected=x > thresh,
                score=score,
                module_name=name,
            )
        return DefenseMorphism(fn=_fn, name=name)

    f = make("f", 0.3, 0.2)
    g = make("g", 0.6, 0.5)
    h = make("h", 0.9, 0.1)
    states = [{"x": 0.1}, {"x": 0.4}, {"x": 0.7}, {"x": 0.95}]
    laws = verify_category_laws(f, g, h, states)
    passed = all(laws.values())
    status = TheoremStatus.PASSED if passed else TheoremStatus.FAILED
    return TheoremResult(
        theorem_id="CT.1",
        name="Defense Category Laws",
        status=status,
        evidence=f"left={laws['left_identity']} "
                 f"right={laws['right_identity']} "
                 f"assoc={laws['associativity']}",
        details=laws,
    )


def _validate_ct2_categorical_product(**_kwargs: Any) -> TheoremResult:
    """Check that ``f × g`` reports the higher-score arm and OR'd detection."""
    from utils.types import DefenseResult

    from .category_theory import DefenseMorphism, categorical_product

    f = DefenseMorphism(
        fn=lambda s: DefenseResult(False, 0.2, "f"),
        name="f",
    )
    g = DefenseMorphism(
        fn=lambda s: DefenseResult(True, 0.8, "g"),
        name="g",
    )
    prod = categorical_product(f, g)
    r = prod({})
    ok = (r.detected is True) and abs(r.score - 0.8) < 1e-10
    status = TheoremStatus.PASSED if ok else TheoremStatus.FAILED
    return TheoremResult(
        theorem_id="CT.2",
        name="Categorical Product",
        status=status,
        evidence=f"detected={r.detected}, score={r.score:.3f}",
        details={"detected": r.detected, "score": r.score},
    )


def _validate_ct3_monadic_preservation(**_kwargs: Any) -> TheoremResult:
    """Check that ``Err(e).bind(f) == Err(e)`` and monad laws hold."""
    from core.monad import DetectionEvent, Err, Ok, verify_monad_laws
    from utils.types import DefenseResult

    evt = DetectionEvent("firewall", 0.9)
    err = Err(evt)
    bound = err.bind(lambda x: Ok(x + 1)).bind(lambda x: Ok(x * 2))
    short_circuit_ok = isinstance(bound, Err) and bound.error == evt

    drs = [
        DefenseResult(detected=False, score=0.1, module_name="m1"),
        DefenseResult(detected=True, score=0.9, module_name="m2"),
    ]
    laws = verify_monad_laws(drs)
    laws_ok = all(laws.values())

    ok = short_circuit_ok and laws_ok
    status = TheoremStatus.PASSED if ok else TheoremStatus.FAILED
    return TheoremResult(
        theorem_id="CT.3",
        name="Monadic Detection Preservation",
        status=status,
        evidence=(
            f"short_circuit={short_circuit_ok}, "
            f"laws={laws}"
        ),
        details={"short_circuit": short_circuit_ok, **laws},
    )


def _validate_fep1_attack_fep_equivalence(**_kwargs: Any) -> TheoremResult:
    """Check ``ΔF > 0.1`` on a mismatched-belief attack."""
    import numpy as np

    from .free_energy import (
        BeliefState,
        GenerativeModel,
        free_energy_of_attack,
    )

    model = GenerativeModel(
        prior=np.array([0.5, 0.5]),
        likelihood=np.array([[0.9, 0.1], [0.1, 0.9]]),
    )
    baseline = BeliefState(probs=np.array([0.5, 0.5]), labels=["A", "B"])
    attacked = BeliefState(probs=np.array([0.05, 0.95]), labels=["A", "B"])
    result = free_energy_of_attack(baseline, attacked, model, 0)

    ok = bool(result["is_attack"]) and result["free_energy_increase"] > 0.1
    status = TheoremStatus.PASSED if ok else TheoremStatus.FAILED
    return TheoremResult(
        theorem_id="FEP.1",
        name="Attack-FEP Equivalence",
        status=status,
        evidence=(
            f"ΔF={result['free_energy_increase']:.3f}, "
            f"is_attack={result['is_attack']}"
        ),
        details=result,
    )


def _validate_fep2_trust_precision_duality(**_kwargs: Any) -> TheoremResult:
    """Check that the TrustConfig weights sum to the composite precision."""
    from core.trust import TrustConfig

    from .free_energy import connect_to_trust_calculus

    cfg = TrustConfig()
    mapping = connect_to_trust_calculus(cfg)
    expected = cfg.alpha + cfg.beta + cfg.gamma
    ok = abs(mapping["composite_precision"] - expected) < 1e-10
    status = TheoremStatus.PASSED if ok else TheoremStatus.FAILED
    return TheoremResult(
        theorem_id="FEP.2",
        name="Trust-Precision Duality",
        status=status,
        evidence=(
            f"composite_precision={mapping['composite_precision']:.6f}, "
            f"alpha+beta+gamma={expected:.6f}"
        ),
        details=mapping,
    )
