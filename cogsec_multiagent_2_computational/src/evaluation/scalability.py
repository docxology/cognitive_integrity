"""Agent-count scaling benchmarks from 2 to 100 agents.

Measures how pipeline latency and memory grow with agent count,
fits a quadratic scaling model T = beta0 + beta1*n + beta2*n^2,
and reports goodness-of-fit via R-squared.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, List, Optional

import numpy as np
from scipy.optimize import least_squares

# ---------------------------------------------------------------------------
# Result containers
# ---------------------------------------------------------------------------

@dataclass
class ScalingModel:
    """Quadratic scaling model: T = beta0 + beta1*n + beta2*n^2.

    Attributes:
        beta0: Constant (overhead) term.
        beta1: Linear coefficient.
        beta2: Quadratic coefficient.
        r_squared: Coefficient of determination.
    """

    beta0: float
    beta1: float
    beta2: float
    r_squared: float

    def predict(self, n: int) -> float:
        """Predict latency for *n* agents.

        Args:
            n: Number of agents.

        Returns:
            Predicted latency in milliseconds.
        """
        return self.beta0 + self.beta1 * n + self.beta2 * n * n


@dataclass
class ScalabilityResult:
    """Raw scalability benchmark results.

    Attributes:
        agent_counts: List of agent counts tested.
        latencies_ms: Mean latency at each count.
        memory_bytes: Estimated memory at each count.
    """

    agent_counts: List[int]
    latencies_ms: List[float]
    memory_bytes: List[int]


# ---------------------------------------------------------------------------
# Scalability benchmark
# ---------------------------------------------------------------------------

class ScalabilityBenchmark:
    """Measure pipeline performance as agent count scales.

    For each agent count, creates an adapter with that many agents,
    builds a pipeline, and measures latency and memory.

    Usage::

        bench = ScalabilityBenchmark()
        result = bench.run(ClaudeCodeAdapter, pipeline_factory)
        model = bench.fit_scaling_model(result)
        print(model.predict(25))
    """

    def __init__(
        self,
        agent_counts: Optional[List[int]] = None,
        n_timing_runs: int = 10,
    ) -> None:
        """
        Args:
            agent_counts: List of agent counts to benchmark.
            n_timing_runs: Number of timing runs per agent count for
                averaging.
        """
        self.agent_counts = agent_counts or [2, 3, 5, 7, 10, 15, 20, 30, 50, 100]
        self.n_timing_runs = n_timing_runs

    def run(
        self,
        adapter_class: Any,
        pipeline_factory: Callable[[Any, int], Any],
    ) -> ScalabilityResult:
        """Run the scalability benchmark.

        For each agent count:
            1. Instantiate the adapter.
            2. Call ``pipeline_factory(adapter, n_agents)`` to build a pipeline.
            3. Measure pipeline creation + evaluation latency.
            4. Estimate memory usage.

        Args:
            adapter_class: The architecture adapter class (not instance).
            pipeline_factory: Callable ``(adapter, n_agents) -> pipeline``
                that builds a defense pipeline for the given adapter and
                agent count.  The pipeline must have an ``evaluate(msg)``
                method.

        Returns:
            A ``ScalabilityResult`` with latencies and memory at each count.
        """
        latencies: List[float] = []
        memories: List[int] = []

        adapter = adapter_class()
        lo, hi = adapter.profile.agent_count_range

        for n in self.agent_counts:
            # Clamp agent count to adapter's supported range
            clamped_n = max(lo, min(hi, n))

            # Build pipeline
            pipeline = pipeline_factory(adapter, clamped_n)

            # Time multiple runs of evaluate
            run_latencies: List[float] = []
            sample_msg = f"test message for {clamped_n} agents"

            for _ in range(self.n_timing_runs):
                t0 = time.perf_counter()
                try:
                    pipeline.evaluate(sample_msg)
                except TypeError:
                    pipeline.evaluate(sample_msg, None)
                except (TypeError, RuntimeError, ValueError):
                    pass
                elapsed_ms = (time.perf_counter() - t0) * 1000.0
                run_latencies.append(elapsed_ms)

            avg_latency = float(np.mean(run_latencies))
            latencies.append(avg_latency)

            # Memory estimate: trust matrix + comm graph + overhead
            trust_bytes = clamped_n * clamped_n * 8  # float64
            comm_bytes = clamped_n * clamped_n * 8
            overhead = clamped_n * 1024  # per-agent state
            pipeline_bytes = _estimate_pipeline_memory(pipeline)
            total_mem = trust_bytes + comm_bytes + overhead + pipeline_bytes
            memories.append(total_mem)

        return ScalabilityResult(
            agent_counts=list(self.agent_counts),
            latencies_ms=latencies,
            memory_bytes=memories,
        )

    def fit_scaling_model(self, results: ScalabilityResult) -> ScalingModel:
        """Fit T = beta0 + beta1*n + beta2*n^2 using scipy least_squares.

        Args:
            results: Raw benchmark results.

        Returns:
            A ``ScalingModel`` with fitted coefficients and R-squared.
        """
        n_arr = np.array(results.agent_counts, dtype=np.float64)
        t_arr = np.array(results.latencies_ms, dtype=np.float64)

        if len(n_arr) < 3:
            # Not enough data for a 3-parameter fit
            return ScalingModel(beta0=0.0, beta1=0.0, beta2=0.0, r_squared=0.0)

        def residuals(params: np.ndarray) -> np.ndarray:
            b0, b1, b2 = params
            predicted = b0 + b1 * n_arr + b2 * n_arr ** 2
            return predicted - t_arr

        # Initial guess: small coefficients
        x0 = np.array([0.1, 0.01, 0.001])
        result = least_squares(residuals, x0)
        b0, b1, b2 = result.x

        # Compute R-squared
        predicted = b0 + b1 * n_arr + b2 * n_arr ** 2
        ss_res = float(np.sum((t_arr - predicted) ** 2))
        ss_tot = float(np.sum((t_arr - np.mean(t_arr)) ** 2))
        r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        return ScalingModel(
            beta0=float(b0),
            beta1=float(b1),
            beta2=float(b2),
            r_squared=r_squared,
        )


def _estimate_pipeline_memory(pipeline: Any) -> int:
    """Quick memory estimate for a pipeline object.

    Uses ``sys.getsizeof`` on the pipeline and its ``modules`` list
    if present.
    """
    import sys

    total = sys.getsizeof(pipeline)
    modules = getattr(pipeline, "modules", [])
    for m in modules:
        total += sys.getsizeof(m)
    return total
