from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional, TypeVar

from formal.category_theory import (
    CognitiveState,
    DefenseMorphism,
    DefenseResult,
)

A = TypeVar("A")
B = TypeVar("B")
S = TypeVar("S")

# 3. F-ALGEBRA / INITIAL ALGEBRA (catamorphism)
# ============================================================================


@dataclass
class CognitiveFunctor:
    """The CognitiveState endofunctor F on DefenseCategory.

    F(X) = Option(X) -- wrapping states in optional context.
    The F-algebra carrier is DefenseResult; the structure map is
    alpha: F(DefenseResult) -> DefenseResult.
    """

    def fmap(
        self,
        fn: Callable[[CognitiveState], CognitiveState],
        state: CognitiveState,
    ) -> CognitiveState:
        """Functorial action: lift a state transformation."""
        return fn(state)


@dataclass
class FAlgebra:
    """An F-algebra (A, α) where A = DefenseResult and α : F(A) -> A."""

    carrier_name: str
    structure_map: Callable[[Optional[DefenseResult]], DefenseResult]

    def apply(self, fa: Optional[DefenseResult]) -> DefenseResult:
        return self.structure_map(fa)


def make_detection_algebra() -> FAlgebra:
    """F-algebra for detection rate accumulation."""

    def alpha(prev: Optional[DefenseResult]) -> DefenseResult:
        if prev is None:
            return DefenseResult(
                detected=False,
                score=0.0,
                module_name="f_algebra_base",
                details={},
                latency_ms=0.0,
            )
        return DefenseResult(
            detected=prev.detected,
            score=min(prev.score * 1.05, 1.0),  # slight amplification
            module_name=f"f_algebra({prev.module_name})",
            details=prev.details,
            latency_ms=prev.latency_ms,
        )

    return FAlgebra(carrier_name="DefenseResult", structure_map=alpha)


def cata(
    algebra: FAlgebra,
    morphisms: List[DefenseMorphism],
    initial_state: CognitiveState,
) -> DefenseResult:
    """Catamorphism (fold) over a list of morphisms via the F-algebra.

    Evaluates each morphism in sequence, threading results through the
    algebra's structure map.

    Args:
        algebra: The F-algebra to fold with.
        morphisms: Ordered list of defence morphisms.
        initial_state: The initial cognitive state.

    Returns:
        Final DefenseResult after the catamorphic fold.
    """
    acc: Optional[DefenseResult] = None
    for morphism in morphisms:
        result = morphism(initial_state)
        # Thread through algebra: chain result into accumulator
        combined = DefenseResult(
            detected=result.detected or (acc.detected if acc else False),
            score=max(result.score, acc.score if acc else 0.0),
            module_name=result.module_name,
            details=result.details,
            latency_ms=result.latency_ms + (acc.latency_ms if acc else 0.0),
        )
        acc = algebra.apply(combined)
    return acc if acc is not None else algebra.apply(None)


# ============================================================================
