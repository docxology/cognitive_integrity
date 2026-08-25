"""False-positive mitigations, as things that run rather than things listed.

Part 2's supplement reports the measured effectiveness of six false-positive
mitigation strategies -- Confirmation Cascade at −60% FPR and −5% TPR,
Temporal Smoothing at −40%/−3%, and four more -- in a table captioned as
results. None of the six existed. The table was a design menu with numbers on
it, which is the most persuasive form a design menu can take.

This module implements the ones that are definable over the shipped pipeline
and says plainly which is not. Each is a *post-filter*: it sees the pipeline's
per-module results for a message and decides whether the flag survives. That
shape is deliberate --- a mitigation that changed the modules would be a
different pipeline, and the question the table asks is what can be recovered
without retraining anything.

The one that is not here
------------------------
"Incremental Learning" is absent. It requires a model that updates on labelled
feedback, and there is no such model in this framework: every module is a fixed
scorer. Implementing something adjacent and calling it incremental learning
would put the same defect back with working code behind it, which is harder to
see, not easier.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol, Sequence

from utils.types import DefenseResult

__all__ = [
    "Verdict",
    "Mitigation",
    "identity",
    "confirmation_cascade",
    "temporal_smoothing",
    "contextual_whitelist",
    "cost_sensitive",
    "combined",
    "MITIGATIONS",
]


@dataclass(frozen=True)
class Verdict:
    """What the pipeline saw for one message, before any mitigation.

    Attributes
    ----------
    flagged:
        The pipeline's own decision.
    score:
        Its aggregate score.
    module_results:
        Per-module results, in pipeline order. A mitigation that needs to know
        *how many* modules agreed, or *which*, reads them here.
    """

    flagged: bool
    score: float
    module_results: Sequence[DefenseResult]

    @property
    def n_flagging(self) -> int:
        return sum(1 for r in self.module_results if r.detected)


class Mitigation(Protocol):
    """A post-filter over a stream of verdicts.

    It takes the whole stream rather than one verdict because two of the
    strategies are temporal: a decision that depends on what came before
    cannot be expressed one message at a time without hiding the state.
    """

    def __call__(self, verdicts: Sequence[Verdict]) -> list[bool]:
        ...


def identity(verdicts: Sequence[Verdict]) -> list[bool]:
    """The control. Every reported delta is against this."""
    return [v.flagged for v in verdicts]


def confirmation_cascade(
    verdicts: Sequence[Verdict], *, required: int = 2
) -> list[bool]:
    """Keep a flag only when at least *required* modules independently raised it.

    The cheapest idea in the table and the one most likely to work, because the
    pipeline's own rule is a maximum: one module firing is enough. Requiring a
    second is exactly the disagreement a maximum discards.
    """
    return [v.flagged and v.n_flagging >= required for v in verdicts]


def temporal_smoothing(
    verdicts: Sequence[Verdict], *, window: int = 5, required: int = 2
) -> list[bool]:
    """Keep a flag only when *required* of the last *window* messages also flagged.

    Models an operator who ignores an isolated alert and acts on a burst. The
    window is over the stream as presented, so the order the corpus is
    evaluated in is part of the measurement -- which is a real limitation of
    this strategy and not an artefact of the implementation.
    """
    out: list[bool] = []
    recent: list[bool] = []
    for verdict in verdicts:
        recent.append(verdict.flagged)
        if len(recent) > window:
            recent.pop(0)
        out.append(verdict.flagged and sum(recent) >= required)
    return out


def contextual_whitelist(
    verdicts: Sequence[Verdict], *, evidence_floor: float = 0.6
) -> list[bool]:
    """Drop a flag whose only evidence is a weak score from a single module.

    The use-versus-mention filter, expressed as the pipeline can express it:
    a benign message that trips one detector on attack-adjacent vocabulary
    scores low and alone, where a real attack usually scores high or trips
    more than one. It cannot read context, and calling it a whitelist would
    overstate it -- there is no list.
    """
    return [
        v.flagged and (v.n_flagging >= 2 or v.score >= evidence_floor)
        for v in verdicts
    ]


def cost_sensitive(verdicts: Sequence[Verdict], *, threshold: float = 0.7) -> list[bool]:
    """Raise the bar: keep only flags scoring above *threshold*.

    The simplest strategy and the one whose cost is most legible, since it
    trades true positives for false positives along the pipeline's own score.
    """
    return [v.flagged and v.score >= threshold for v in verdicts]


def combined(verdicts: Sequence[Verdict]) -> list[bool]:
    """Confirmation cascade and the contextual filter together.

    Composed rather than tuned as a seventh strategy: the table reported a
    "Combined" row and the honest version of that is the conjunction of the
    ones that survive on their own.
    """
    cascade = confirmation_cascade(verdicts)
    contextual = contextual_whitelist(verdicts)
    return [a and b for a, b in zip(cascade, contextual)]


#: The implemented strategies, by the names the supplement uses.
MITIGATIONS: dict[str, Callable[[Sequence[Verdict]], list[bool]]] = {
    "none": identity,
    "confirmation_cascade": confirmation_cascade,
    "temporal_smoothing": temporal_smoothing,
    "contextual_whitelist": contextual_whitelist,
    "cost_sensitive": cost_sensitive,
    "combined": combined,
}
