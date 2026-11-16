from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, TypeVar

import numpy as np

from src.formal.category_theory import (
    CognitiveState,
    DefenseMorphism,
    DefenseResult,
    compose_morphisms,
)

A = TypeVar("A")
B = TypeVar("B")
S = TypeVar("S")

# 7. MONAD STRUCTURE
# ============================================================================


@dataclass
class DefenseMonad:
    """Defence pipeline monad over CognitiveState.

    T(CognitiveState) = "a computation that may detect an attack and
    returns a DefenseResult enriched with the detection context".

    - η (unit): CognitiveState → T(CognitiveState)
        Lifts a state into the trivial non-detecting computation.

    - μ (join / multiply): T(T(CognitiveState)) → T(CognitiveState)
        Flattens two nested defence applications into one.

    Monad laws (verified empirically):
        Left unit:  μ ∘ η_T = id_T
        Right unit: μ ∘ T(η) = id_T
        Associativity: μ ∘ μ_T = μ ∘ T(μ)
    """

    def eta(self, state: CognitiveState) -> DefenseResult:
        """Unit: lift a state into the trivial (non-detecting) computation."""
        return DefenseResult(
            detected=False,
            score=0.0,
            module_name="monad_unit",
            details={"state_keys": list(state.keys())},
            latency_ms=0.0,
        )

    def mu(self, outer: DefenseMorphism, inner: DefenseMorphism) -> DefenseMorphism:
        """Join: flatten nested defence into a single morphism.

        μ(outer, inner) = compose_morphisms(inner, outer)
        """
        return compose_morphisms(inner, outer)

    def kleisli_compose(
        self,
        f: Callable[[CognitiveState], DefenseResult],
        g: Callable[[CognitiveState], DefenseResult],
    ) -> Callable[[CognitiveState], DefenseResult]:
        """Kleisli composition ``f >=> g`` using the same join as ``mu``.

        Sequencing short-circuits on detection.  Only two clean results are
        arbitrated by maximum score; composing every pair with max/OR would
        run a defense after an earlier detection and disagree with ``mu``.
        """
        f_morphism = DefenseMorphism(
            fn=f, name=getattr(f, "name", getattr(f, "__name__", "f"))
        )
        g_morphism = DefenseMorphism(
            fn=g, name=getattr(g, "name", getattr(g, "__name__", "g"))
        )
        return self.mu(g_morphism, f_morphism)

    def verify_left_unit(
        self,
        f: DefenseMorphism,
        states: List[CognitiveState],
        tol: float = 1e-10,
    ) -> bool:
        """Left unit: η >=> f ≅ f."""
        composed = self.kleisli_compose(self.eta, f)
        vf = np.array([f(s).score for s in states])
        vc = np.array([composed(s).score for s in states])
        return bool(np.allclose(vc, vf, atol=tol, rtol=0.0))

    def verify_right_unit(
        self,
        f: DefenseMorphism,
        states: List[CognitiveState],
        tol: float = 1e-10,
    ) -> bool:
        """Right unit: f >=> η ≅ f."""
        composed = self.kleisli_compose(f, self.eta)
        vf = np.array([f(s).score for s in states])
        vc = np.array([composed(s).score for s in states])
        return bool(np.allclose(vc, vf, atol=tol, rtol=0.0))

    def verify_associativity(
        self,
        f: DefenseMorphism,
        g: DefenseMorphism,
        h: DefenseMorphism,
        states: List[CognitiveState],
        tol: float = 1e-10,
    ) -> bool:
        """Monad associativity: (f >=> g) >=> h ≅ f >=> (g >=> h)."""
        fg = self.kleisli_compose(f, g)
        lhs = self.kleisli_compose(fg, h)
        gh = self.kleisli_compose(g, h)
        rhs = self.kleisli_compose(f, gh)
        vl = np.array([lhs(s).score for s in states])
        vr = np.array([rhs(s).score for s in states])
        return bool(np.allclose(vl, vr, atol=tol, rtol=0.0))

    def verify_all(
        self,
        f: DefenseMorphism,
        g: DefenseMorphism,
        h: DefenseMorphism,
        states: List[CognitiveState],
    ) -> Dict[str, bool]:
        return {
            "left_unit": self.verify_left_unit(f, states),
            "right_unit": self.verify_right_unit(f, states),
            "associativity": self.verify_associativity(f, g, h, states),
        }


# ============================================================================
