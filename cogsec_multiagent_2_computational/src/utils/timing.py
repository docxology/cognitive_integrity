"""Timing utilities for latency measurement and profiling.

Provides a ``@timed`` decorator for individual function calls and a
``LatencyAccumulator`` for aggregating latency statistics across many
invocations.
"""

from __future__ import annotations

import functools
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import numpy as np


def timed(fn: Optional[Callable] = None, *, label: Optional[str] = None) -> Any:
    """Decorator that records wall-clock execution time.

    The decorated function gains a ``last_latency_ms`` attribute holding
    the most recent execution time in milliseconds.

    Can be used bare (``@timed``) or with a label (``@timed(label='foo')``).
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
            finally:
                elapsed = (time.perf_counter() - start) * 1000.0
                wrapper.last_latency_ms = elapsed
            return result

        wrapper.last_latency_ms = 0.0
        wrapper._timed_label = label or func.__qualname__
        return wrapper

    if fn is not None:
        return decorator(fn)
    return decorator


@dataclass
class LatencyAccumulator:
    """Collects latency samples and computes percentile statistics.

    Attributes:
        label: Human-readable label for this accumulator.
        samples: Raw latency samples in milliseconds.
    """

    label: str = ""
    samples: List[float] = field(default_factory=list)

    def record(self, latency_ms: float) -> None:
        """Record a single latency sample."""
        self.samples.append(latency_ms)

    def p50(self) -> float:
        """Median latency."""
        return float(np.percentile(self.samples, 50)) if self.samples else 0.0

    def p95(self) -> float:
        """95th-percentile latency."""
        return float(np.percentile(self.samples, 95)) if self.samples else 0.0

    def p99(self) -> float:
        """99th-percentile latency."""
        return float(np.percentile(self.samples, 99)) if self.samples else 0.0

    def mean(self) -> float:
        """Mean latency."""
        return float(np.mean(self.samples)) if self.samples else 0.0

    def std(self) -> float:
        """Standard deviation of latency."""
        return float(np.std(self.samples, ddof=1)) if len(self.samples) > 1 else 0.0

    def count(self) -> int:
        """Number of recorded samples."""
        return len(self.samples)

    def summary(self) -> Dict[str, float]:
        """Return a summary dict with p50, p95, p99, mean, std, count."""
        return {
            "p50": self.p50(),
            "p95": self.p95(),
            "p99": self.p99(),
            "mean": self.mean(),
            "std": self.std(),
            "count": float(self.count()),
        }

    def reset(self) -> None:
        """Clear all recorded samples."""
        self.samples.clear()
