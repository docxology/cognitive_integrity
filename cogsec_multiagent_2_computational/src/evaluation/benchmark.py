"""Latency and memory profiling for defense pipelines.

Provides ``LatencyProfiler`` for wall-clock latency measurement,
``MemoryProfiler`` for memory-usage estimation, and ``BenchmarkResult``
for aggregated results.
"""

from __future__ import annotations

import logging
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

import numpy as np

from utils.timing import LatencyAccumulator

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Benchmark result
# ---------------------------------------------------------------------------

@dataclass
class BenchmarkResult:
    """Aggregated benchmark results.

    Attributes:
        latency_summary: Latency percentile summary dict.
        memory_bytes: Estimated memory usage in bytes.
        throughput_per_second: Samples processed per second.
    """

    latency_summary: Dict[str, float]
    memory_bytes: int
    throughput_per_second: float


# ---------------------------------------------------------------------------
# Latency profiler
# ---------------------------------------------------------------------------

class LatencyProfiler:
    """Measure wall-clock latency for defense pipeline evaluation.

    Usage::

        profiler = LatencyProfiler()
        acc = profiler.profile(pipeline, samples, n_runs=100)
        print(acc.summary())
    """

    def profile(
        self,
        pipeline: Any,
        samples: List[Any],
        n_runs: int = 100,
    ) -> LatencyAccumulator:
        """Run the pipeline repeatedly and collect latency samples.

        Each run evaluates every sample in *samples* through
        ``pipeline.evaluate(sample)`` (or ``pipeline.evaluate(sample, None)``
        for pipelines expecting context).

        Args:
            pipeline: Object with an ``evaluate`` method.
            samples: Input samples (strings or dicts).
            n_runs: Number of full passes over all samples.

        Returns:
            A ``LatencyAccumulator`` with all recorded latencies.
        """
        acc = LatencyAccumulator(label="pipeline_latency")

        for _ in range(n_runs):
            for sample in samples:
                msg = sample if isinstance(sample, str) else sample.get("content", "")
                t0 = time.perf_counter()
                try:
                    pipeline.evaluate(msg)
                except TypeError:
                    # Pipeline may expect (message, context)
                    pipeline.evaluate(msg, None)
                elapsed_ms = (time.perf_counter() - t0) * 1000.0
                acc.record(elapsed_ms)

        return acc

    def profile_by_module(
        self,
        pipeline: Any,
        sample: Any,
    ) -> Dict[str, LatencyAccumulator]:
        """Profile latency per module within a pipeline.

        Requires the pipeline to expose a ``modules`` attribute
        (list of ``DefenseModule`` instances with ``evaluate`` methods).

        Args:
            pipeline: A pipeline with a ``modules`` attribute.
            sample: A single input sample.

        Returns:
            Dict mapping module name to its ``LatencyAccumulator``.
        """
        msg = sample if isinstance(sample, str) else sample.get("content", "")
        accumulators: Dict[str, LatencyAccumulator] = {}

        modules = getattr(pipeline, "modules", [])
        for module in modules:
            name = getattr(module, "name", module.__class__.__name__)
            acc = LatencyAccumulator(label=name)

            t0 = time.perf_counter()
            try:
                module.evaluate(msg)
            except TypeError:
                module.evaluate(msg, None)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            acc.record(elapsed_ms)

            accumulators[name] = acc

        return accumulators


# ---------------------------------------------------------------------------
# Memory profiler
# ---------------------------------------------------------------------------

@dataclass
class MemoryEstimate:
    """Result of a memory estimation pass over a pipeline.

    Attributes:
        total_bytes: Estimated total memory in bytes.
        skipped_attributes: ``(attribute_name, exception_repr)`` for every
            attribute whose value could not be read.  Each entry is memory
            that is *missing* from ``total_bytes``, so a non-empty list means
            the total is an undercount of unknown size.
    """

    total_bytes: int
    skipped_attributes: List[Tuple[str, str]] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        """True if every public attribute was successfully accounted for."""
        return not self.skipped_attributes


class MemoryProfiler:
    """Estimate memory usage of defense pipeline data structures.

    Uses ``sys.getsizeof`` for Python objects and estimates numpy
    array memory from dtype and shape.
    """

    #: Exceptions treated as "this attribute is not currently readable"
    #: (e.g. a lazily initialised property).  Anything else propagates so a
    #: genuinely broken pipeline surfaces instead of silently undercounting.
    SKIPPABLE_ATTR_ERRORS: Tuple[type[BaseException], ...] = (
        AttributeError,
        NotImplementedError,
        RuntimeError,
    )

    def estimate_memory(self, pipeline: Any, n_agents: int) -> int:
        """Estimate total memory usage in bytes.

        Thin wrapper over :meth:`estimate_memory_detailed` that returns only
        the total.  A warning is logged when any attribute was skipped, since
        the returned int cannot otherwise convey that it is an undercount;
        callers that must not publish an undercount should use
        :meth:`estimate_memory_detailed` and check ``is_complete``.

        Args:
            pipeline: The defense pipeline object.
            n_agents: Number of agents (for matrix sizing estimates).

        Returns:
            Estimated memory in bytes.
        """
        estimate = self.estimate_memory_detailed(pipeline, n_agents)
        if not estimate.is_complete:
            logger.warning(
                "memory estimate for %s is an undercount: %d attribute(s) "
                "could not be read (%s)",
                type(pipeline).__name__,
                len(estimate.skipped_attributes),
                ", ".join(name for name, _ in estimate.skipped_attributes),
            )
        return estimate.total_bytes

    def estimate_memory_detailed(self, pipeline: Any, n_agents: int) -> MemoryEstimate:
        """Estimate total memory usage, reporting unreadable attributes.

        Walks the pipeline's attributes and estimates memory for:
        - Python primitive attributes (via ``sys.getsizeof``)
        - numpy arrays (dtype itemsize x total elements)
        - Lists/dicts (recursive estimation)
        - Agent-count-dependent structures (trust matrices = n^2)

        Attributes that raise one of :attr:`SKIPPABLE_ATTR_ERRORS` on access
        are recorded in ``skipped_attributes`` and omitted from the total.
        Any other exception propagates to the caller.

        Args:
            pipeline: The defense pipeline object.
            n_agents: Number of agents (for matrix sizing estimates).

        Returns:
            A :class:`MemoryEstimate`.

        Raises:
            ValueError: If *n_agents* is negative.
        """
        if n_agents < 0:
            raise ValueError(f"n_agents must be >= 0, got {n_agents}")

        total = 0
        skipped: List[Tuple[str, str]] = []

        # Base object overhead
        total += sys.getsizeof(pipeline)

        # Walk public attributes
        for attr_name in dir(pipeline):
            if attr_name.startswith("_"):
                continue
            try:
                val = getattr(pipeline, attr_name)
            except self.SKIPPABLE_ATTR_ERRORS as exc:
                logger.debug(
                    "skipping attribute %r of %s: %s: %s",
                    attr_name,
                    type(pipeline).__name__,
                    type(exc).__name__,
                    exc,
                )
                skipped.append((attr_name, f"{type(exc).__name__}: {exc}"))
                continue

            if callable(val) and not isinstance(val, np.ndarray):
                continue

            total += self._estimate_object(val)

        # Estimate agent-count-dependent structures (P2-F6): only count the
        # matrix structures that actually exist on the pipeline.  The previous
        # code unconditionally added two n^2 terms, inflating estimates for
        # pipelines that hold no such matrices.
        matrix_like = 0
        for attr_name in dir(pipeline):
            if attr_name.startswith("_"):
                continue
            try:
                val = getattr(pipeline, attr_name)
            except self.SKIPPABLE_ATTR_ERRORS:
                continue
            if isinstance(val, np.ndarray) and val.ndim >= 2:
                matrix_like += 1
        trust_matrix_bytes = n_agents * n_agents * 8 * matrix_like
        total += trust_matrix_bytes

        # Per-agent state overhead (estimated 1KB per agent)
        agent_state_bytes = n_agents * 1024
        total += agent_state_bytes

        return MemoryEstimate(total_bytes=total, skipped_attributes=skipped)

    def _estimate_object(self, obj: Any, depth: int = 0) -> int:
        """Recursively estimate memory for a single object.

        Limits recursion depth to 5 to avoid cycles.
        """
        if depth > 5:
            return 0

        if isinstance(obj, np.ndarray):
            return int(obj.nbytes) + sys.getsizeof(obj)

        if isinstance(obj, (list, tuple)):
            total = sys.getsizeof(obj)
            for item in obj[:100]:  # Cap to prevent huge lists
                total += self._estimate_object(item, depth + 1)
            return total

        if isinstance(obj, dict):
            total = sys.getsizeof(obj)
            for k, v in list(obj.items())[:100]:
                total += self._estimate_object(k, depth + 1)
                total += self._estimate_object(v, depth + 1)
            return total

        return sys.getsizeof(obj)
