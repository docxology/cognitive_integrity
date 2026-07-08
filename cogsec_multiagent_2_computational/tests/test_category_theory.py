"""Tests for category-theoretic defense algebra.

Covers:
- Identity morphism semantics (never detects, score 0).
- Sequential composition and left/right identity laws.
- Categorical product (max-score arbitration).
- Associativity across three morphisms.
- lift_defense_module for a real DefenseModule subclass.
- DefenseCategory registry + verify_all_laws.

NO MOCKS. All tests use real DefenseResult values and pure morphisms.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

from src.composition.pipeline import DefenseModule
from src.formal.category_theory import (
    DefenseCategory,
    DefenseMorphism,
    categorical_product,
    compose_morphisms,
    identity_morphism,
    lift_defense_module,
    verify_category_laws,
)
from src.utils.types import DefenseResult

# ---------------------------------------------------------------------------
# Fixtures: deterministic morphisms on scalar cognitive states
# ---------------------------------------------------------------------------

def _make_threshold_morphism(
    name: str,
    threshold: float,
    score: float,
) -> DefenseMorphism:
    """Detect when state['x'] > threshold; always report *score*."""

    def _fn(state):
        x = float(state.get("x", 0.0))
        return DefenseResult(
            detected=x > threshold,
            score=score,
            module_name=name,
        )

    return DefenseMorphism(fn=_fn, name=name)


_STATES = [
    {"x": 0.05},
    {"x": 0.2},
    {"x": 0.55},
    {"x": 0.78},
    {"x": 0.95},
]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_identity_morphism_never_detects():
    """Identity morphism returns detected=False, score=0 regardless of state."""
    identity = identity_morphism()
    for s in _STATES:
        r = identity(s)
        assert r.detected is False
        assert r.score == 0.0
        assert r.module_name == "identity"
    assert identity.identity is True


def test_compose_short_circuits_on_first_detection():
    """g ∘ f returns f's result when f detects, without calling g."""
    f = _make_threshold_morphism("f", threshold=0.5, score=0.8)

    call_counter = {"g_calls": 0}

    def _g_fn(state):
        call_counter["g_calls"] += 1
        return DefenseResult(detected=True, score=0.99, module_name="g")

    g = DefenseMorphism(fn=_g_fn, name="g")
    composed = compose_morphisms(f, g)

    # f detects at x = 0.78; g should not be called.
    r = composed({"x": 0.78})
    assert r.detected is True
    assert r.module_name == "f"
    assert call_counter["g_calls"] == 0

    # f does not detect at x = 0.2; g should be called.
    composed({"x": 0.2})
    assert call_counter["g_calls"] == 1


def test_compose_passes_through_when_neither_detects():
    """If neither arm detects, the composed score is max of the two."""
    f = _make_threshold_morphism("f", threshold=0.9, score=0.3)
    g = _make_threshold_morphism("g", threshold=0.9, score=0.6)
    composed = compose_morphisms(f, g)
    r = composed({"x": 0.1})
    assert r.detected is False
    assert r.score == pytest.approx(0.6)


def test_left_identity_law():
    """id ∘ f == f (scores and detections agree on all test states)."""
    f = _make_threshold_morphism("f", threshold=0.5, score=0.4)
    identity = identity_morphism()
    composed = compose_morphisms(f, identity)  # compose f first then id
    for s in _STATES:
        r_composed = composed(s)
        r_f = f(s)
        assert r_composed.detected == r_f.detected
        assert r_composed.score == pytest.approx(r_f.score)


def test_right_identity_law():
    """f ∘ id == f (scores and detections agree on all test states)."""
    f = _make_threshold_morphism("f", threshold=0.5, score=0.4)
    identity = identity_morphism()
    composed = compose_morphisms(identity, f)  # id first then f
    for s in _STATES:
        r_composed = composed(s)
        r_f = f(s)
        assert r_composed.detected == r_f.detected
        assert r_composed.score == pytest.approx(r_f.score)


def test_associativity_law():
    """(h ∘ g) ∘ f == h ∘ (g ∘ f) on test states."""
    f = _make_threshold_morphism("f", threshold=0.3, score=0.2)
    g = _make_threshold_morphism("g", threshold=0.6, score=0.5)
    h = _make_threshold_morphism("h", threshold=0.9, score=0.1)

    left = compose_morphisms(compose_morphisms(f, g), h)
    right = compose_morphisms(f, compose_morphisms(g, h))
    for s in _STATES:
        lr = left(s)
        rr = right(s)
        assert lr.detected == rr.detected
        assert lr.score == pytest.approx(rr.score)


def test_verify_category_laws_reports_all_true():
    """The combined law checker returns True on all three laws."""
    f = _make_threshold_morphism("f", threshold=0.5, score=0.3)
    g = _make_threshold_morphism("g", threshold=0.7, score=0.4)
    h = _make_threshold_morphism("h", threshold=0.9, score=0.2)
    laws = verify_category_laws(f, g, h, _STATES)
    assert laws == {
        "left_identity": True,
        "right_identity": True,
        "associativity": True,
    }


def test_categorical_product_picks_higher_score():
    """f × g returns the arm with the higher score; detection is OR-ed."""
    def make(name, detected, score):
        def _fn(state):
            return DefenseResult(detected=detected, score=score, module_name=name)
        return DefenseMorphism(fn=_fn, name=name)

    f = make("f", detected=False, score=0.2)
    g = make("g", detected=True, score=0.85)
    prod = categorical_product(f, g)
    r = prod({})
    # g has higher score so winner's score is 0.85.
    assert r.score == pytest.approx(0.85)
    # At least one detected -> product detects.
    assert r.detected is True


def test_categorical_product_reports_both_arms():
    """The product's details include left and right arm diagnostics."""
    f = DefenseMorphism(
        fn=lambda s: DefenseResult(detected=False, score=0.4, module_name="f"),
        name="f",
    )
    g = DefenseMorphism(
        fn=lambda s: DefenseResult(detected=False, score=0.2, module_name="g"),
        name="g",
    )
    prod = categorical_product(f, g)
    r = prod({})
    assert "left" in r.details and "right" in r.details
    assert r.details["left"]["module"] == "f"
    assert r.details["right"]["module"] == "g"
    assert r.details["winner"] == "f"  # 0.4 > 0.2


def test_lift_defense_module_forwards_to_evaluate():
    """A DefenseModule subclass is lifted into a working DefenseMorphism."""

    class _Counter(DefenseModule):
        def __init__(self):
            self.calls = 0

        @property
        def name(self):  # type: ignore[override]
            return "counter"

        def evaluate(self, message, context=None):  # type: ignore[override]
            self.calls += 1
            score = 0.5 if context and context.get("suspicious") else 0.1
            return DefenseResult(
                detected=score > 0.3,
                score=score,
                module_name="counter",
                details={"received": message, "context": context},
            )

    mod = _Counter()
    morphism = lift_defense_module(mod)
    # Clean call:
    r_clean = morphism({"__message__": 0.1, "suspicious": False})
    assert mod.calls == 1
    assert r_clean.detected is False
    # Suspicious context:
    r_flag = morphism({"__message__": 0.9, "suspicious": True})
    assert mod.calls == 2
    assert r_flag.detected is True


def test_defense_category_compose_and_laws():
    """DefenseCategory composes registered morphisms and checks all laws."""
    cat = DefenseCategory()
    f = _make_threshold_morphism("f", 0.4, 0.3)
    g = _make_threshold_morphism("g", 0.6, 0.5)
    h = _make_threshold_morphism("h", 0.8, 0.2)
    cat.register("f", f)
    cat.register("g", g)
    cat.register("h", h)

    composed = cat.compose("f", "g", "h")
    # On a low-x state, no morphism detects; max score is g's 0.5.
    r = composed({"x": 0.1})
    assert r.detected is False
    assert r.score == pytest.approx(0.5)

    laws = cat.verify_all_laws(_STATES)
    assert all(laws.values())


def test_defense_category_get_raises_on_unknown():
    """Accessing an unregistered morphism raises KeyError."""
    cat = DefenseCategory()
    with pytest.raises(KeyError):
        cat.get("missing")
