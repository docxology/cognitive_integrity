"""The stable surface the supplements document: state in, result out.

Three supplements describe CIF's core types as living here, and until now they
did not exist: ``from src.core.base import DefenseResult, CognitiveState``
raised ``ModuleNotFoundError``, and a reader following S09 or §02c got that
error on the first line of the first example. ``DefenseResult`` was real but
lived in :mod:`utils.types`; ``CognitiveState`` was real only as a string in a
morphism label, ``"CognitiveState -> DefenseResult"``, printed on a figure
describing a type that nothing defined.

This module makes the documented surface true rather than deleting the
documentation, because the documentation was describing something worth having.
The composition algebra in §02c is stated over a morphism from a cognitive
state to a defense result, and every adapter in the framework really does take
a message plus optional context -- which is a cognitive state with its parts
passed separately. Naming it lets the algebra's objects be objects.

Nothing here changes behaviour. :class:`CognitiveState` is accepted anywhere a
message string is, through :func:`coerce_message`, and every existing caller
that passes a ``str`` keeps working unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Union

from composition.pipeline import DefenseModule
from utils.types import DefenseResult

__all__ = ["CognitiveState", "DefenseResult", "DefenseModule", "coerce_message"]


@dataclass(frozen=True)
class CognitiveState:
    """What an agent believes it has been asked, at the moment of evaluation.

    The object of the composition algebra: a defense module is a morphism from
    one of these to a :class:`DefenseResult`. Frozen because a defense that can
    edit the state it is judging is not a defense, and because the pipeline
    hands the same state to every module in a coalition -- one of them mutating
    it would silently change what the others were asked about.

    Attributes
    ----------
    message:
        The payload under evaluation. Never ``None``: a state with nothing to
        judge is not a state, and the alternative is every module growing its
        own guard for it.
    context:
        Provenance and history the modules may consult -- agent id, delegation
        depth, prior turns. Defaults to empty rather than ``None`` so callers
        never branch on which they got.
    agent_id:
        Which agent holds this state, when that is known. Optional because most
        of the corpus is evaluated without one.
    """

    message: str
    context: Mapping[str, Any] = field(default_factory=dict)
    agent_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.message, str):
            raise TypeError(
                f"CognitiveState.message must be str, got {type(self.message).__name__}"
            )

    @classmethod
    def of(cls, message: str, **context: Any) -> "CognitiveState":
        """Build a state from a message and keyword context.

        ``CognitiveState.of("...", agent_id="agent-3", depth=2)`` reads better
        at a call site than assembling a dict, and it is the form the
        supplements use.
        """
        agent_id = context.pop("agent_id", None)
        return cls(message=message, context=dict(context), agent_id=agent_id)

    def with_context(self, **extra: Any) -> "CognitiveState":
        """A copy carrying additional context. The original is untouched."""
        merged: Dict[str, Any] = dict(self.context)
        merged.update(extra)
        return CognitiveState(message=self.message, context=merged, agent_id=self.agent_id)


#: What every module's ``evaluate`` accepts. The union is deliberate: the
#: framework was written against ``str`` and there is no reason to churn a
#: thousand call sites to name a type.
Evaluatable = Union[str, CognitiveState]


def coerce_message(value: Evaluatable) -> tuple[str, Optional[Dict[str, Any]]]:
    """Split an evaluatable into the ``(message, context)`` modules expect.

    Returns the context as ``None`` for a bare string rather than an empty
    dict, so that a module distinguishing "no context supplied" from "empty
    context supplied" can still do so.
    """
    if isinstance(value, CognitiveState):
        context: Dict[str, Any] = dict(value.context)
        if value.agent_id is not None:
            context.setdefault("agent_id", value.agent_id)
        return value.message, context or None
    if isinstance(value, str):
        return value, None
    raise TypeError(
        f"expected str or CognitiveState, got {type(value).__name__}"
    )
