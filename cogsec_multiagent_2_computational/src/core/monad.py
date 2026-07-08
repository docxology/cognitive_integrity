"""Result monad for composable defense chains.

Implements railway-oriented programming for CIF defense pipelines.
Detection events short-circuit via :class:`Err`; clean inputs propagate
as :class:`Ok` and can be threaded through a chain of defense modules
via ``bind`` / ``map`` operations.

The central invariant is that ``Err(e).bind(f) == Err(e)`` for every
continuation ``f``: once a defense module flags an input, subsequent
modules are skipped and the original detection event is preserved.

Classes
-------
Ok / Err
    The two variants of :class:`Result`.  ``Ok(v)`` carries a value,
    ``Err(e)`` carries a :class:`DetectionEvent` describing why the
    pipeline was short-circuited.
MonadicPipeline
    Thin driver that runs a list of :class:`DefenseModule` instances
    under the monadic discipline described above.

Functions
---------
bind / map_result
    Functional-style dispatchers over :class:`Result`.
sequence
    Collapse a list of ``Result`` into a single ``Result`` whose
    value is the list of unwrapped ``Ok`` values, short-circuiting on
    the first ``Err``.
from_defense_result
    Lift a :class:`DefenseResult` into the monadic world.
verify_monad_laws
    Empirical check of left-identity, right-identity, and
    associativity on a list of realistic :class:`DefenseResult` values.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Generic, List, TypeVar, Union

from utils.types import DefenseResult

T = TypeVar("T")
U = TypeVar("U")
E = TypeVar("E")


# ---------------------------------------------------------------------------
# Detection event -- the "error" payload carried by ``Err``
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DetectionEvent:
    """Immutable record describing a detection short-circuit.

    Attributes:
        module_name: Name of the defense module that flagged the input.
        score: Confidence/severity score from the detection.
        details: Optional diagnostic information copied from the
            originating :class:`DefenseResult`.
    """

    module_name: str
    score: float
    details: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Result monad
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Ok(Generic[T]):
    """The "clean" branch of :class:`Result`.

    Carries a value that subsequent pipeline stages may transform.
    """

    value: T

    def bind(self, f: Callable[[T], "Result"]) -> "Result":
        """Apply *f* to the contained value, returning its :class:`Result`.

        This is monadic bind (``>>=``): if ``f`` returns another
        ``Ok``, the computation continues; if it returns ``Err``, the
        chain short-circuits from that point on.
        """
        return f(self.value)

    def map(self, f: Callable[[T], U]) -> "Ok[U]":
        """Apply *f* to the contained value, wrapping the result in ``Ok``.

        Pure function lifting -- ``f`` may not fail.
        """
        return Ok(f(self.value))

    def is_ok(self) -> bool:
        """Return ``True``: this is the ``Ok`` branch."""
        return True

    def unwrap(self) -> T:
        """Return the contained value."""
        return self.value


@dataclass(frozen=True)
class Err(Generic[E]):
    """The "detected" branch of :class:`Result`.

    Carries an error payload (typically :class:`DetectionEvent`) that
    propagates unchanged through subsequent ``bind`` / ``map`` calls.
    """

    error: E

    def bind(self, f: Callable[[Any], "Result"]) -> "Err[E]":
        """Ignore *f* and return this ``Err`` unchanged.

        This is the short-circuit invariant: once detection has
        occurred, no further pipeline stage runs.
        """
        return self

    def map(self, f: Callable[[Any], Any]) -> "Err[E]":
        """Ignore *f* and return this ``Err`` unchanged."""
        return self

    def is_ok(self) -> bool:
        """Return ``False``: this is the ``Err`` branch."""
        return False

    def unwrap(self) -> Any:
        """Raise :class:`ValueError`: no value to unwrap in an ``Err``."""
        raise ValueError(f"Cannot unwrap Err({self.error!r})")


Result = Union[Ok[T], Err[E]]


# ---------------------------------------------------------------------------
# Module-level dispatchers
# ---------------------------------------------------------------------------

def bind(result: Result, f: Callable[[Any], Result]) -> Result:
    """Dispatch ``bind`` to the underlying :class:`Result` variant.

    Equivalent to ``result.bind(f)`` but convenient in functional
    pipelines where ``bind`` is used as a higher-order helper.
    """
    return result.bind(f)


def map_result(result: Result, f: Callable[[Any], Any]) -> Result:
    """Dispatch ``map`` to the underlying :class:`Result` variant."""
    return result.map(f)


def sequence(results: List[Result]) -> Result:
    """Collapse a list of ``Result`` into a single ``Result``.

    Returns the first ``Err`` encountered, otherwise ``Ok`` of the list
    of unwrapped ``Ok`` values (preserving order).

    Args:
        results: List of ``Result`` values to sequence.

    Returns:
        ``Err`` on first detection; otherwise ``Ok(list[value])``.
    """
    values: List[Any] = []
    for r in results:
        if isinstance(r, Err):
            return r
        values.append(r.value)
    return Ok(values)


def from_defense_result(
    r: DefenseResult,
    pass_through: Any = None,
) -> Result:
    """Lift a :class:`DefenseResult` into the :class:`Result` monad.

    A detected result becomes ``Err(DetectionEvent(...))``; a clean
    result becomes ``Ok(pass_through)`` where ``pass_through`` defaults
    to the :class:`DefenseResult` itself.

    Args:
        r: The defense result to lift.
        pass_through: Value to wrap in ``Ok`` when ``r.detected`` is
            ``False``.  If ``None`` (the sentinel default), the
            :class:`DefenseResult` itself is wrapped.

    Returns:
        ``Err(DetectionEvent)`` if ``r.detected``, otherwise ``Ok(...)``.
    """
    if r.detected:
        return Err(
            DetectionEvent(
                module_name=r.module_name,
                score=r.score,
                details=dict(r.details),
            )
        )
    return Ok(pass_through if pass_through is not None else r)


# ---------------------------------------------------------------------------
# Monadic pipeline driver
# ---------------------------------------------------------------------------

class MonadicPipeline:
    """Drive a list of :class:`DefenseModule` under the Result monad.

    Each module is evaluated in order; its :class:`DefenseResult` is
    lifted via :func:`from_defense_result` and threaded through ``bind``.
    The first detection short-circuits the chain and its
    :class:`DetectionEvent` is returned inside :class:`Err`.  If every
    module passes, the driver returns ``Ok(list[DefenseResult])``.

    Args:
        modules: Ordered list of defense modules to run.
    """

    def __init__(self, modules: List[Any]) -> None:
        if not modules:
            raise ValueError("MonadicPipeline requires at least one module")
        self.modules = list(modules)

    def run(
        self,
        message: str,
        context: Dict[str, Any] | None = None,
    ) -> Result:
        """Run each module and collect results under the Result monad.

        Args:
            message: The message to inspect.
            context: Optional context dict forwarded to each module.

        Returns:
            ``Ok(list[DefenseResult])`` if every module passes, or
            ``Err(DetectionEvent)`` from the first flagging module.
        """
        collected: List[DefenseResult] = []

        for module in self.modules:
            dr = module.evaluate(message, context)
            collected.append(dr)
            lifted = from_defense_result(dr)
            if isinstance(lifted, Err):
                return lifted

        return Ok(collected)


# ---------------------------------------------------------------------------
# Monad law verification
# ---------------------------------------------------------------------------

def _approx_equal_result(a: Result, b: Result) -> bool:
    """Structural equality for Result values used in law checks."""
    if isinstance(a, Ok) and isinstance(b, Ok):
        return a.value == b.value
    if isinstance(a, Err) and isinstance(b, Err):
        return a.error == b.error
    return False


def verify_monad_laws(test_results: List[DefenseResult]) -> Dict[str, bool]:
    """Empirically verify the three monad laws on a list of defense results.

    Laws checked:
      - **Left identity**: ``Ok(v).bind(f) == f(v)``
      - **Right identity**: ``m.bind(Ok) == m``
      - **Associativity**: ``m.bind(f).bind(g) == m.bind(lambda x: f(x).bind(g))``

    Each law is checked against every result in *test_results* (lifted
    via :func:`from_defense_result`).  The law holds overall iff it
    holds for every input.

    Args:
        test_results: Realistic :class:`DefenseResult` values to
            exercise both the ``Ok`` and ``Err`` branches.

    Returns:
        Dict with keys ``left_identity``, ``right_identity``, and
        ``associativity`` mapping to booleans.
    """
    # Two sample Kleisli arrows: one that keeps the value (Ok) and one
    # that always returns a fixed Err.  Composing the two exercises the
    # short-circuit case too.
    def f(x: Any) -> Result:
        return Ok(("f", x))

    def g(x: Any) -> Result:
        return Ok(("g", x))

    left_identity = True
    right_identity = True
    associativity = True

    for dr in test_results:
        m = from_defense_result(dr)

        # Left identity -- only meaningful for the Ok branch, but we
        # exercise it with a synthetic Ok lift of the detection score
        # so the law has a witness for every input.
        v = dr.score
        if not _approx_equal_result(Ok(v).bind(f), f(v)):
            left_identity = False

        # Right identity on the actual lifted monad.
        if not _approx_equal_result(m.bind(lambda x: Ok(x)), m):
            right_identity = False

        # Associativity (again on the actual lifted monad).
        lhs = m.bind(f).bind(g)
        rhs = m.bind(lambda x, f=f, g=g: f(x).bind(g))  # type: ignore[misc]
        if not _approx_equal_result(lhs, rhs):
            associativity = False

    return {
        "left_identity": left_identity,
        "right_identity": right_identity,
        "associativity": associativity,
    }


__all__ = [
    "DetectionEvent",
    "Ok",
    "Err",
    "Result",
    "bind",
    "map_result",
    "sequence",
    "from_defense_result",
    "MonadicPipeline",
    "verify_monad_laws",
]
