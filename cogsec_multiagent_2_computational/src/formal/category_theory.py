"""Category-theoretic defense algebra for the Cognitive Integrity Framework.

We model the space of defenses as a category ``DefenseCategory`` whose:

- **Objects** are :data:`CognitiveState` -- dict mappings from belief
  names to probabilities.
- **Morphisms** are :class:`DefenseMorphism` wrappers around
  :data:`DetectionFn` -- deterministic functions from cognitive states
  to :class:`DefenseResult`.

Categorical composition ``g ∘ f`` corresponds to sequential (series)
defense composition with short-circuit on detection, and categorical
product ``f × g`` corresponds to parallel composition with max-score
arbitration.  The identity morphism is a no-op defender that never
flags.

The module also exposes :class:`DefenseCategory` for registering named
morphisms and verifying the three fundamental category laws
(left-identity, right-identity, associativity) empirically on a list
of test states.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

import numpy as np

from utils.types import DefenseResult

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

CognitiveState = Dict[str, float]
"""Belief distribution: mapping from belief name to probability.

Values are expected to be non-negative but no normalisation is enforced.
"""

DetectionFn = Callable[[CognitiveState], DefenseResult]
"""Deterministic function from cognitive state to :class:`DefenseResult`."""


# ---------------------------------------------------------------------------
# Defense morphism
# ---------------------------------------------------------------------------

@dataclass
class DefenseMorphism:
    """A morphism in :class:`DefenseCategory`.

    Wraps a :data:`DetectionFn` with a label and an optional
    ``identity`` flag.  The morphism is callable and forwards to the
    underlying function.

    Attributes:
        fn: Underlying detection function.
        name: Human-readable name for diagnostics.
        identity: ``True`` iff this is the identity morphism (never
            detects); useful for short-circuiting in composition.
    """

    fn: DetectionFn
    name: str = ""
    identity: bool = False

    def __call__(self, state: CognitiveState) -> DefenseResult:
        """Apply the morphism to a cognitive state."""
        return self.fn(state)


def identity_morphism() -> DefenseMorphism:
    """The identity morphism ``id``: never flags, score 0.0.

    Satisfies ``id ∘ f = f`` and ``f ∘ id = f`` for every morphism ``f``.
    """

    def _id(state: CognitiveState) -> DefenseResult:
        return DefenseResult(
            detected=False,
            score=0.0,
            module_name="identity",
            details={"identity": True},
            latency_ms=0.0,
        )

    return DefenseMorphism(fn=_id, name="identity", identity=True)


# ---------------------------------------------------------------------------
# Composition operators
# ---------------------------------------------------------------------------

def compose_morphisms(
    f: DefenseMorphism,
    g: DefenseMorphism,
) -> DefenseMorphism:
    """Sequential (categorical) composition: run ``f`` first, then ``g``.

    Mirrors a series defense pipeline:

    - If ``f`` detects, the composition returns ``f(σ)`` (short-circuit).
    - Otherwise it runs ``g(σ)`` and, if ``g`` does not detect either,
      returns a clean result whose score is the *maximum* of ``f(σ)``
      and ``g(σ)``.  Using the max preserves whichever arm carries
      the stronger (still sub-threshold) signal and crucially makes
      the identity morphism a *two-sided unit*: the identity always
      scores ``0.0``, so ``id ∘ f`` and ``f ∘ id`` both score
      ``max(0, f.score) = f.score``.

    In category-theoretic notation the returned morphism is ``g ∘ f``
    (``f`` applied first); ``compose_morphisms`` is named in
    evaluation order.

    Args:
        f: First morphism to apply.
        g: Second morphism, applied only if ``f`` passes.

    Returns:
        A new :class:`DefenseMorphism` implementing the composition.
    """

    def _composed(state: CognitiveState) -> DefenseResult:
        r_f = f(state)
        if r_f.detected:
            return r_f
        r_g = g(state)
        if r_g.detected:
            return r_g
        # Neither detected: carry forward the higher-score result so
        # identity morphisms act as two-sided units.
        winner = r_f if r_f.score >= r_g.score else r_g
        return DefenseResult(
            detected=False,
            score=winner.score,
            module_name=winner.module_name,
            details=dict(winner.details),
            latency_ms=r_f.latency_ms + r_g.latency_ms,
        )

    composed_name = f"({g.name} ∘ {f.name})" if (f.name or g.name) else ""
    return DefenseMorphism(fn=_composed, name=composed_name, identity=False)


def categorical_product(
    f: DefenseMorphism,
    g: DefenseMorphism,
) -> DefenseMorphism:
    """Categorical product: run both morphisms and pick the higher-score one.

    ``(f × g)(σ)`` returns ``f(σ)`` if ``f(σ).score >= g(σ).score``
    else ``g(σ)``.  The ``detected`` flag is the logical OR of the two
    underlying flags so any detection in either arm propagates.

    Args:
        f, g: Morphisms whose outputs are arbitrated by score.

    Returns:
        A new :class:`DefenseMorphism` implementing the product.
    """

    def _product(state: CognitiveState) -> DefenseResult:
        r_f = f(state)
        r_g = g(state)
        winner = r_f if r_f.score >= r_g.score else r_g
        detected = bool(r_f.detected or r_g.detected)
        return DefenseResult(
            detected=detected,
            score=winner.score,
            module_name=f"({f.name} × {g.name})" if (f.name or g.name) else winner.module_name,
            details={
                "left": {
                    "module": r_f.module_name,
                    "detected": r_f.detected,
                    "score": r_f.score,
                },
                "right": {
                    "module": r_g.module_name,
                    "detected": r_g.detected,
                    "score": r_g.score,
                },
                "winner": winner.module_name,
            },
            latency_ms=r_f.latency_ms + r_g.latency_ms,
        )

    prod_name = f"({f.name} × {g.name})" if (f.name or g.name) else ""
    return DefenseMorphism(fn=_product, name=prod_name, identity=False)


# ---------------------------------------------------------------------------
# Lifting DefenseModule -> DefenseMorphism
# ---------------------------------------------------------------------------

def lift_defense_module(module: Any) -> DefenseMorphism:
    """Adapt a :class:`DefenseModule` to a :class:`DefenseMorphism`.

    Maps a :data:`CognitiveState` into ``(message, context)`` for the
    underlying module.  By convention the key ``__message__`` is
    consumed as a text marker (the numeric value is used as a proxy
    for the message) and all other keys are forwarded as context.

    Args:
        module: Instance of :class:`DefenseModule` with ``.evaluate``.

    Returns:
        A :class:`DefenseMorphism` delegating to ``module.evaluate``.
    """
    module_name = getattr(module, "name", module.__class__.__name__)

    def _lifted(state: CognitiveState) -> DefenseResult:
        # Reconstruct a synthetic message / context pair from the state.
        message_marker = state.get("__message__", 0.0)
        message = f"state_message_{float(message_marker):.6f}"
        context = {k: v for k, v in state.items() if k != "__message__"}
        return module.evaluate(message, context if context else None)

    return DefenseMorphism(fn=_lifted, name=module_name, identity=False)


# ---------------------------------------------------------------------------
# Category law verification
# ---------------------------------------------------------------------------

def _score_vec(
    morphism: DefenseMorphism,
    states: List[CognitiveState],
) -> np.ndarray:
    """Evaluate a morphism on each state and return the score vector."""
    return np.array([morphism(s).score for s in states], dtype=float)


def _detected_vec(
    morphism: DefenseMorphism,
    states: List[CognitiveState],
) -> np.ndarray:
    """Evaluate a morphism on each state and return the detection flag vector."""
    return np.array([morphism(s).detected for s in states], dtype=bool)


def verify_category_laws(
    f: DefenseMorphism,
    g: DefenseMorphism,
    h: DefenseMorphism,
    test_states: List[CognitiveState],
    tolerance: float = 1e-10,
) -> Dict[str, bool]:
    """Empirically verify the three category laws on *test_states*.

    Laws checked:

    - ``left_identity``:  ``id ∘ f == f``
    - ``right_identity``: ``f ∘ id == f``
    - ``associativity``:  ``(h ∘ g) ∘ f == h ∘ (g ∘ f)``

    Equality is compared pointwise on scores (within ``tolerance``) and
    detection flags.

    Args:
        f, g, h: Three morphisms to exercise associativity with.
        test_states: List of cognitive states to evaluate against.
        tolerance: Absolute tolerance for score comparison.

    Returns:
        Dict ``{"left_identity": bool, "right_identity": bool,
        "associativity": bool}``.
    """
    identity = identity_morphism()

    # left_identity: id ∘ f == f
    lhs_left = compose_morphisms(f, identity)
    left_ok = (
        np.allclose(
            _score_vec(lhs_left, test_states),
            _score_vec(f, test_states),
            atol=tolerance,
        )
        and np.array_equal(
            _detected_vec(lhs_left, test_states),
            _detected_vec(f, test_states),
        )
    )

    # right_identity: f ∘ id == f
    rhs_right = compose_morphisms(identity, f)
    right_ok = (
        np.allclose(
            _score_vec(rhs_right, test_states),
            _score_vec(f, test_states),
            atol=tolerance,
        )
        and np.array_equal(
            _detected_vec(rhs_right, test_states),
            _detected_vec(f, test_states),
        )
    )

    # associativity: (h ∘ g) ∘ f == h ∘ (g ∘ f)
    lhs_assoc = compose_morphisms(f, compose_morphisms(g, h))
    rhs_assoc = compose_morphisms(compose_morphisms(f, g), h)
    assoc_ok = (
        np.allclose(
            _score_vec(lhs_assoc, test_states),
            _score_vec(rhs_assoc, test_states),
            atol=tolerance,
        )
        and np.array_equal(
            _detected_vec(lhs_assoc, test_states),
            _detected_vec(rhs_assoc, test_states),
        )
    )

    return {
        "left_identity": bool(left_ok),
        "right_identity": bool(right_ok),
        "associativity": bool(assoc_ok),
    }


# ---------------------------------------------------------------------------
# DefenseCategory registry
# ---------------------------------------------------------------------------

@dataclass
class DefenseCategory:
    """Registry of named morphisms in the defense category.

    Supports building composite morphisms from registered pieces via
    :meth:`compose` and running a battery of category-law checks on
    all registered morphisms via :meth:`verify_all_laws`.
    """

    _morphisms: Dict[str, DefenseMorphism] = field(default_factory=dict)

    def register(self, name: str, morphism: DefenseMorphism) -> None:
        """Register *morphism* under *name*."""
        self._morphisms[name] = morphism

    def get(self, name: str) -> DefenseMorphism:
        """Retrieve a registered morphism.

        Raises:
            KeyError: If *name* is not registered.
        """
        if name not in self._morphisms:
            raise KeyError(f"Unknown morphism: {name}")
        return self._morphisms[name]

    def compose(self, *names: str) -> DefenseMorphism:
        """Compose registered morphisms left-to-right.

        ``compose("f", "g", "h")`` returns ``h ∘ g ∘ f`` (``f`` first).
        """
        if not names:
            return identity_morphism()
        result = self.get(names[0])
        for nm in names[1:]:
            result = compose_morphisms(result, self.get(nm))
        return result

    def verify_all_laws(
        self,
        test_states: List[CognitiveState],
        tolerance: float = 1e-10,
    ) -> Dict[str, bool]:
        """Verify category laws using three registered morphisms.

        Picks the first three registered morphisms as ``f, g, h``; if
        fewer are registered, the identity morphism fills the gap.

        Returns:
            Same shape as :func:`verify_category_laws`.
        """
        identity = identity_morphism()
        morphisms = list(self._morphisms.values())
        while len(morphisms) < 3:
            morphisms.append(identity)
        f, g, h = morphisms[:3]
        return verify_category_laws(f, g, h, test_states, tolerance=tolerance)


__all__ = [
    "CognitiveState",
    "DetectionFn",
    "DefenseMorphism",
    "identity_morphism",
    "compose_morphisms",
    "categorical_product",
    "lift_defense_module",
    "verify_category_laws",
    "DefenseCategory",
]
