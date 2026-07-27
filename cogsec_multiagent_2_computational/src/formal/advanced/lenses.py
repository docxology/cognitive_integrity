from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Generic, List, TypeVar

from formal.category_theory import (
    CognitiveState,
    DefenseResult,
)

A = TypeVar("A")
B = TypeVar("B")
S = TypeVar("S")

# 8. LENSES / OPTICS
# ============================================================================


@dataclass
class BeliefLens(Generic[S]):
    """A van Laarhoven lens on cognitive belief state.

    get(state) = the observed belief value (a CognitiveState)
    set(state, new_value) = the manipulated state (attacker model)

    This models a cognitive attack: the adversary can both *observe*
    the agent's current belief state and *overwrite* it.
    """

    focus: str  # Which belief key the lens focuses on

    def get(self, state: CognitiveState) -> float:
        """Observe the focused belief."""
        return state.get(self.focus, 0.0)

    def set(self, state: CognitiveState, value: float) -> CognitiveState:
        """Manipulate the focused belief (attacker action)."""
        new_state = dict(state)
        new_state[self.focus] = value
        return new_state

    def modify(
        self,
        state: CognitiveState,
        fn: Callable[[float], float],
    ) -> CognitiveState:
        """Apply a function over the focused belief."""
        return self.set(state, fn(self.get(state)))

    def compose(self, other: "BeliefLens[Any]") -> "ComposedLens":
        """Compose two lenses (outer . inner)."""
        return ComposedLens(outer=self, inner=other)

    def __repr__(self) -> str:
        return f"BeliefLens(focus={self.focus!r})"


@dataclass
class ComposedLens:
    """Composition of two lenses: outer . inner."""

    outer: "BeliefLens[Any]"
    inner: "BeliefLens[Any]"

    def get(self, state: CognitiveState) -> float:
        intermediate = {self.inner.focus: self.inner.get(state)}
        return self.outer.get(intermediate)

    def set(self, state: CognitiveState, value: float) -> CognitiveState:
        current_inner = self.inner.get(state)
        new_inner_state = self.outer.set({self.inner.focus: current_inner}, value)
        return self.inner.set(state, new_inner_state.get(self.inner.focus, value))

    def __repr__(self) -> str:
        return f"ComposedLens({self.outer!r} . {self.inner!r})"


@dataclass
class DefenseProfunctor:
    """A defence as a profunctor optic P(A, B) → P(S, T).

    Models the defence as transforming the attacker's ability to observe
    and modify belief state: the defence reduces the set of reachable
    manipulated states.

    get: S → A  (read the attack surface from the full state)
    put: (S, B) → T  (apply the defended result back)
    """

    get_fn: Callable[[CognitiveState], CognitiveState]  # S → A
    put_fn: Callable[[CognitiveState, DefenseResult], CognitiveState]  # (S, B) → T

    def apply_get(self, state: CognitiveState) -> CognitiveState:
        return self.get_fn(state)

    def apply_put(self, state: CognitiveState, result: DefenseResult) -> CognitiveState:
        return self.put_fn(state, result)

    def compose(self, other: "DefenseProfunctor") -> "DefenseProfunctor":
        """Compose two profunctor optics."""
        outer_get = self.get_fn
        outer_put = self.put_fn
        inner_get = other.get_fn
        inner_put = other.put_fn

        def composed_get(state: CognitiveState) -> CognitiveState:
            return inner_get(outer_get(state))

        def composed_put(state: CognitiveState, result: DefenseResult) -> CognitiveState:
            intermediate = outer_get(state)
            inner_result = inner_put(intermediate, result)
            # Re-apply outer put: inject modified intermediate back
            return outer_put(state, DefenseResult(
                detected=result.detected,
                score=result.score,
                module_name=result.module_name,
                details={**result.details, "intermediate": inner_result},
                latency_ms=result.latency_ms,
            ))

        return DefenseProfunctor(get_fn=composed_get, put_fn=composed_put)

    def verify_lens_laws(
        self,
        lens: BeliefLens[Any],
        states: List[CognitiveState],
        tol: float = 1e-10,
    ) -> Dict[str, bool]:
        """Verify van Laarhoven lens laws for the underlying BeliefLens.

        - GetPut: set(s, get(s)) = s
        - PutGet: get(set(s, v)) = v
        - PutPut: set(set(s, v1), v2) = set(s, v2)
        """
        get_put_ok = True
        put_get_ok = True
        put_put_ok = True

        for state in states:
            v = lens.get(state)
            # GetPut
            restored = lens.set(state, v)
            if abs(restored.get(lens.focus, 0.0) - state.get(lens.focus, 0.0)) > tol:
                get_put_ok = False

            # PutGet
            new_v = 0.42
            modified = lens.set(state, new_v)
            if abs(lens.get(modified) - new_v) > tol:
                put_get_ok = False

            # PutPut
            v1, v2 = 0.3, 0.7
            s_after_two = lens.set(lens.set(state, v1), v2)
            s_after_one = lens.set(state, v2)
            if abs(
                s_after_two.get(lens.focus, 0.0) - s_after_one.get(lens.focus, 0.0)
            ) > tol:
                put_put_ok = False

        return {
            "get_put": get_put_ok,
            "put_get": put_get_ok,
            "put_put": put_put_ok,
        }


# ============================================================================
