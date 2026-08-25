"""Defense composition pipelines: series, parallel, and hybrid.

Implements composable defense evaluation pipelines that chain or
fan-out multiple defense modules and aggregate their results into
a unified pipeline verdict.

Theorems 3.1-3.2 from Paper 1 establish that:
  - Series composition reduces the combined miss rate multiplicatively.
  - Parallel composition leverages fusion strategies for complementary coverage.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from utils.types import DefenseResult

# ---------------------------------------------------------------------------
# Abstract base -- every defense module must implement this
# ---------------------------------------------------------------------------

class DefenseModule(ABC):
    """Abstract base class for all defense modules in the framework.

    Subclasses must implement :meth:`evaluate`, which inspects a message
    (and optional context) and returns a :class:`DefenseResult` with a
    detection flag and confidence score.
    """

    @property
    def name(self) -> str:
        """Human-readable module name (defaults to class name)."""
        return self.__class__.__name__

    @abstractmethod
    def evaluate(self, message: str, context: Optional[Dict[str, Any]] = None) -> DefenseResult:
        """Evaluate a message for potential attacks.

        Args:
            message: The message / payload to inspect.
            context: Optional contextual metadata (agent id, history, etc.).

        Returns:
            A :class:`DefenseResult` with detection flag, score, and details.
        """
        ...

    def judge(self, state: Any) -> DefenseResult:
        """Evaluate a :class:`~core.base.CognitiveState` or a bare message.

        The composition algebra in the supplements is stated over a morphism
        from a cognitive state to a defense result, and this is that morphism.
        Every module gets it for free by subclassing, so the documented type
        is a type the framework actually uses rather than a name on a figure.

        A bare ``str`` is accepted and behaves exactly as
        :meth:`evaluate` does with no context, so nothing that already calls
        ``evaluate`` needs to change.
        """
        # Imported here rather than at module scope: core.base re-exports this
        # class, so a top-level import would close a cycle.
        from core.base import coerce_message

        message, context = coerce_message(state)
        return self.evaluate(message, context)


# ---------------------------------------------------------------------------
# Pipeline result
# ---------------------------------------------------------------------------

@dataclass
class PipelineResult:
    """Aggregated result from a defense pipeline.

    Attributes:
        detected: Whether the pipeline as a whole flagged the input.
        score: Aggregated confidence/severity score in [0, 1].
        module_results: Individual :class:`DefenseResult` from each module.
        strategy: Description of the composition strategy used.
        latency_ms: Total wall-clock latency for the pipeline evaluation.
    """

    detected: bool
    score: float
    module_results: List[DefenseResult]
    strategy: str
    latency_ms: float = 0.0


# ---------------------------------------------------------------------------
# Series pipeline
# ---------------------------------------------------------------------------

class SeriesPipeline:
    """Run defense modules sequentially.

    In a series pipeline the modules are evaluated one after another.
    Detection short-circuits: as soon as any module flags the input the
    pipeline returns immediately with ``detected=True``.  If no module
    detects, the pipeline returns with the *maximum* score observed across
    all modules (since a near-miss in any module is still informative).

    The combined miss rate for independent modules with individual
    detection rates r_i is:

        P_miss = product(1 - r_i)

    so the combined detection rate is 1 - P_miss.
    """

    def __init__(self, modules: List[DefenseModule]) -> None:
        if not modules:
            raise ValueError("SeriesPipeline requires at least one module")
        self.modules = list(modules)

    def evaluate(self, message: str, context: Optional[Dict[str, Any]] = None) -> PipelineResult:
        """Evaluate the message through each module in sequence.

        Returns early on the first detection. Otherwise returns the
        aggregate of all module results.
        """
        start = time.perf_counter()
        results: List[DefenseResult] = []
        detected = False
        max_score = 0.0

        for module in self.modules:
            t0 = time.perf_counter()
            result = module.evaluate(message, context)
            elapsed = (time.perf_counter() - t0) * 1000.0
            result.latency_ms = elapsed
            results.append(result)

            if result.score > max_score:
                max_score = result.score

            if result.detected:
                detected = True
                # Short-circuit: we already know the verdict.
                break

        total_ms = (time.perf_counter() - start) * 1000.0

        return PipelineResult(
            detected=detected,
            score=max_score,
            module_results=results,
            strategy="series",
            latency_ms=total_ms,
        )

    def __repr__(self) -> str:
        names = " -> ".join(m.name for m in self.modules)
        return f"SeriesPipeline([{names}])"


# ---------------------------------------------------------------------------
# Parallel pipeline
# ---------------------------------------------------------------------------

class ParallelPipeline:
    """Run defense modules in parallel and aggregate via a fusion strategy.

    All modules evaluate the same input independently. Their results are
    combined using a configurable :class:`FusionStrategy` (imported at
    call time to avoid circular imports).  The default strategy is
    ``MaxScoreFusion`` with a threshold of 0.5.

    Args:
        modules: The defense modules to run.
        fusion: A fusion strategy instance.  If ``None``, defaults to
            :class:`MaxScoreFusion`.
        threshold: Detection threshold applied by the fusion strategy
            (only used when *fusion* is ``None``).
    """

    def __init__(
        self,
        modules: List[DefenseModule],
        fusion: Optional[Any] = None,
        threshold: float = 0.5,
    ) -> None:
        if not modules:
            raise ValueError("ParallelPipeline requires at least one module")
        self.modules = list(modules)

        if fusion is None:
            from .fusion import MaxScoreFusion
            self.fusion = MaxScoreFusion(threshold=threshold)
        else:
            self.fusion = fusion

        self.threshold = threshold

    def evaluate(self, message: str, context: Optional[Dict[str, Any]] = None) -> PipelineResult:
        """Evaluate the message through all modules, then fuse results."""
        start = time.perf_counter()
        results: List[DefenseResult] = []

        for module in self.modules:
            t0 = time.perf_counter()
            result = module.evaluate(message, context)
            elapsed = (time.perf_counter() - t0) * 1000.0
            result.latency_ms = elapsed
            results.append(result)

        # Fuse
        detected, score = self.fusion.fuse(results)
        total_ms = (time.perf_counter() - start) * 1000.0

        return PipelineResult(
            detected=detected,
            score=score,
            module_results=results,
            strategy=f"parallel:{self.fusion.__class__.__name__}",
            latency_ms=total_ms,
        )

    def __repr__(self) -> str:
        names = " | ".join(m.name for m in self.modules)
        return f"ParallelPipeline([{names}], fusion={self.fusion.__class__.__name__})"


# ---------------------------------------------------------------------------
# Hybrid pipeline
# ---------------------------------------------------------------------------

class HybridPipeline:
    """Two-stage pipeline: fast parallel pre-filter, then deep series analysis.

    Stage 1 (parallel): Lightweight modules run in parallel.  If any flag
    the input, Stage 2 is skipped and the result is returned immediately.

    Stage 2 (series): Heavyweight modules run in sequence only when
    Stage 1 does *not* detect -- this is the expensive deep-inspection path.

    This mirrors real-world deployments where fast heuristics handle the
    majority of traffic and expensive analysis is reserved for ambiguous
    cases.
    """

    def __init__(
        self,
        fast_modules: List[DefenseModule],
        deep_modules: List[DefenseModule],
        fusion: Optional[Any] = None,
        threshold: float = 0.5,
    ) -> None:
        self.fast = ParallelPipeline(fast_modules, fusion=fusion, threshold=threshold)
        self.deep = SeriesPipeline(deep_modules) if deep_modules else None

    def evaluate(self, message: str, context: Optional[Dict[str, Any]] = None) -> PipelineResult:
        """Evaluate fast path first; fall through to deep path if clean."""
        start = time.perf_counter()

        fast_result = self.fast.evaluate(message, context)
        if fast_result.detected:
            fast_result.strategy = "hybrid:fast"
            fast_result.latency_ms = (time.perf_counter() - start) * 1000.0
            return fast_result

        if self.deep is None:
            fast_result.strategy = "hybrid:fast_only"
            fast_result.latency_ms = (time.perf_counter() - start) * 1000.0
            return fast_result

        deep_result = self.deep.evaluate(message, context)
        total_ms = (time.perf_counter() - start) * 1000.0

        # Merge module results from both stages
        all_results = fast_result.module_results + deep_result.module_results
        combined_score = max(fast_result.score, deep_result.score)

        return PipelineResult(
            detected=deep_result.detected,
            score=combined_score,
            module_results=all_results,
            strategy="hybrid:deep",
            latency_ms=total_ms,
        )

    def __repr__(self) -> str:
        return f"HybridPipeline(fast={self.fast!r}, deep={self.deep!r})"
