"""Tests for the Result monad used in CIF defense chains.

Covers:
- Monad law compliance (left identity, right identity, associativity).
- Err short-circuit semantics.
- from_defense_result lifting.
- sequence over lists of Result.
- MonadicPipeline with a real DefenseModule (lightweight subclass).

NO MOCKS. All tests use real :class:`DefenseResult` values produced by
real (trivially deterministic) defense modules.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

from src.composition.pipeline import DefenseModule
from src.core.monad import (
    DetectionEvent,
    Err,
    MonadicPipeline,
    Ok,
    Result,
    bind,
    from_defense_result,
    map_result,
    sequence,
    verify_monad_laws,
)
from src.utils.types import DefenseResult

# ---------------------------------------------------------------------------
# Deterministic DefenseModule fixtures
# ---------------------------------------------------------------------------

class _Pass(DefenseModule):
    """Module that never flags; returns a fixed score."""

    def __init__(self, score: float = 0.1, name: str = "pass") -> None:
        self._score = score
        self._name = name

    @property
    def name(self) -> str:  # type: ignore[override]
        return self._name

    def evaluate(self, message, context=None):  # type: ignore[override]
        return DefenseResult(
            detected=False,
            score=self._score,
            module_name=self._name,
            details={"message_len": len(message)},
        )


class _Flag(DefenseModule):
    """Module that always flags; returns a fixed score."""

    def __init__(self, score: float = 0.95, name: str = "flag") -> None:
        self._score = score
        self._name = name

    @property
    def name(self) -> str:  # type: ignore[override]
        return self._name

    def evaluate(self, message, context=None):  # type: ignore[override]
        return DefenseResult(
            detected=True,
            score=self._score,
            module_name=self._name,
            details={"reason": "always flags"},
        )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_ok_bind_chains():
    """Ok.bind threads the value through successive continuations."""
    result: Result = Ok(10)
    r1 = result.bind(lambda x: Ok(x + 1))
    r2 = r1.bind(lambda x: Ok(x * 2))
    assert isinstance(r2, Ok)
    assert r2.unwrap() == 22


def test_err_bind_short_circuits():
    """Err.bind ignores the continuation and returns the same Err."""
    evt = DetectionEvent(module_name="firewall", score=0.9)
    err: Result = Err(evt)

    counter = {"calls": 0}

    def never_called(x):
        counter["calls"] += 1
        return Ok(x + 1)

    r1 = err.bind(never_called).bind(never_called).bind(never_called)
    assert isinstance(r1, Err)
    assert r1.error == evt
    assert counter["calls"] == 0


def test_ok_map_applies_pure_function():
    """Ok.map applies a pure function and rewraps the result."""
    r: Result = Ok([1, 2, 3])
    mapped = r.map(lambda xs: sum(xs))
    assert isinstance(mapped, Ok)
    assert mapped.unwrap() == 6


def test_err_map_is_noop():
    """Err.map ignores the function and returns the same Err."""
    err: Result = Err(DetectionEvent("m", 0.5))
    mapped = err.map(lambda x: x + 1)
    assert isinstance(mapped, Err)
    assert mapped.error == err.error


def test_err_unwrap_raises():
    """Err.unwrap raises ValueError -- there is no value to unwrap."""
    err: Result = Err(DetectionEvent("m", 0.5))
    with pytest.raises(ValueError):
        err.unwrap()


def test_from_defense_result_detected_becomes_err():
    """Detected DefenseResult lifts to Err(DetectionEvent)."""
    dr = DefenseResult(
        detected=True,
        score=0.88,
        module_name="firewall",
        details={"reason": "pattern match"},
    )
    lifted = from_defense_result(dr)
    assert isinstance(lifted, Err)
    assert lifted.error.module_name == "firewall"
    assert lifted.error.score == pytest.approx(0.88)
    assert lifted.error.details == {"reason": "pattern match"}


def test_from_defense_result_clean_becomes_ok():
    """Non-detected DefenseResult lifts to Ok wrapping the result by default."""
    dr = DefenseResult(detected=False, score=0.1, module_name="pass")
    lifted = from_defense_result(dr)
    assert isinstance(lifted, Ok)
    assert lifted.unwrap() is dr


def test_from_defense_result_pass_through_value():
    """pass_through argument controls the Ok-wrapped value."""
    dr = DefenseResult(detected=False, score=0.2, module_name="pass")
    lifted = from_defense_result(dr, pass_through="message payload")
    assert isinstance(lifted, Ok)
    assert lifted.unwrap() == "message payload"


def test_sequence_all_ok_returns_ok_list():
    """sequence collects values when every element is Ok."""
    rs = [Ok(1), Ok(2), Ok(3)]
    collapsed = sequence(rs)
    assert isinstance(collapsed, Ok)
    assert collapsed.unwrap() == [1, 2, 3]


def test_sequence_first_err_wins():
    """sequence short-circuits on the first Err, preserving its payload."""
    evt1 = DetectionEvent("m1", 0.9)
    evt2 = DetectionEvent("m2", 0.8)
    rs = [Ok(1), Err(evt1), Err(evt2), Ok(4)]
    collapsed = sequence(rs)
    assert isinstance(collapsed, Err)
    assert collapsed.error == evt1


def test_module_dispatchers_bind_and_map():
    """Top-level bind / map_result dispatch to the underlying variant."""
    r_ok: Result = Ok(5)
    r_err: Result = Err(DetectionEvent("m", 0.5))
    assert bind(r_ok, lambda x: Ok(x + 1)).unwrap() == 6
    assert isinstance(bind(r_err, lambda x: Ok(x + 1)), Err)
    assert map_result(r_ok, lambda x: x * 2).unwrap() == 10
    assert isinstance(map_result(r_err, lambda x: x * 2), Err)


def test_monadic_pipeline_all_clean():
    """MonadicPipeline returns Ok(list) when every module passes."""
    pipeline = MonadicPipeline([
        _Pass(score=0.1, name="p1"),
        _Pass(score=0.2, name="p2"),
        _Pass(score=0.15, name="p3"),
    ])
    result = pipeline.run("benign message", context=None)
    assert isinstance(result, Ok)
    values = result.unwrap()
    assert len(values) == 3
    assert all(isinstance(v, DefenseResult) for v in values)
    assert [v.module_name for v in values] == ["p1", "p2", "p3"]
    assert all(v.detected is False for v in values)


def test_monadic_pipeline_short_circuits_on_first_flag():
    """Pipeline returns Err at the first flagging module and stops evaluation."""
    p3 = _Pass(score=0.2, name="p3_never_runs")
    pipeline = MonadicPipeline([
        _Pass(score=0.1, name="p1"),
        _Flag(score=0.88, name="f2"),
        p3,
    ])
    result = pipeline.run("malicious message")
    assert isinstance(result, Err)
    assert result.error.module_name == "f2"
    assert result.error.score == pytest.approx(0.88)


def test_monadic_pipeline_requires_modules():
    """Empty module list is rejected."""
    with pytest.raises(ValueError):
        MonadicPipeline([])


def test_verify_monad_laws_passes_on_mixed_results():
    """Empirical verification finds all three laws satisfied on mixed input."""
    test_results = [
        DefenseResult(detected=False, score=0.1, module_name="m1"),
        DefenseResult(detected=True, score=0.9, module_name="m2"),
        DefenseResult(detected=False, score=0.4, module_name="m3"),
        DefenseResult(detected=True, score=0.75, module_name="m4"),
    ]
    laws = verify_monad_laws(test_results)
    assert laws == {
        "left_identity": True,
        "right_identity": True,
        "associativity": True,
    }
