"""Agent-count scaling benchmarks from 2 to 100 agents.

Measures how pipeline latency and memory grow with agent count,
fits a quadratic scaling model T = beta0 + beta1*n + beta2*n^2,
and reports goodness-of-fit via R-squared.

``fit_with_inference`` additionally returns ordinary-least-squares standard
errors, 95% confidence intervals and two-sided p-values for each coefficient,
so a fitted scaling model can be reported with uncertainty rather than as a
bare point estimate.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, Sequence, Tuple

import numpy as np
from scipy import stats
from scipy.optimize import least_squares

logger = logging.getLogger(__name__)

# Exception types treated as a *failed* evaluation rather than a latency
# sample.  Anything outside this set propagates so a genuinely broken
# pipeline is not silently absorbed into the timing distribution.
_EVALUATE_FAILURES: Tuple[type[BaseException], ...] = (TypeError, RuntimeError, ValueError)

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
        agent_counts: List of agent counts requested.
        latencies_ms: Mean latency over the *successful* runs at each count.
            ``nan`` when every timing run at that count failed.
        memory_bytes: Estimated memory at each count.
        failures: Number of failed ``evaluate()`` calls at each count.  A
            failed call is excluded from ``latencies_ms``; see
            :meth:`ScalabilityBenchmark.run`.
        clamped_counts: The agent count actually used at each index after
            clamping to the adapter's supported range.  Differs from
            ``agent_counts`` when a requested count is out of range, in which
            case the corresponding measurement is a duplicate of the clamp
            boundary and must not be reported as a measurement at the
            requested count.
        n_timing_runs: Timing runs attempted per agent count.
    """

    agent_counts: List[int]
    latencies_ms: List[float]
    memory_bytes: List[int]
    failures: List[int] = field(default_factory=list)
    clamped_counts: List[int] = field(default_factory=list)
    n_timing_runs: int = 0

    @property
    def total_failures(self) -> int:
        """Total number of failed ``evaluate()`` calls across all counts."""
        return int(sum(self.failures))

    @property
    def any_clamped(self) -> bool:
        """True if any requested agent count was clamped to the adapter range."""
        return any(
            requested != used
            for requested, used in zip(self.agent_counts, self.clamped_counts)
        )


@dataclass
class RegressionInference:
    """OLS fit of a polynomial scaling model with full inference.

    Attributes:
        beta: Fitted coefficients, lowest order first
            (``[beta0, beta1, ..., beta_degree]``).
        stderr: Standard error of each coefficient.
        ci95: ``(lower, upper)`` 95% confidence interval per coefficient.
        p_values: Two-sided p-value per coefficient under H0: beta_k = 0.
        r_squared: Coefficient of determination.
        adj_r_squared: R-squared adjusted for the number of predictors.
        n_obs: Number of observations used in the fit.
        df_resid: Residual degrees of freedom (``n_obs - len(beta)``).
        degree: Polynomial degree of the design matrix.
        residual_std: Residual standard deviation (sqrt of sigma-hat squared).
    """

    beta: List[float]
    stderr: List[float]
    ci95: List[Tuple[float, float]]
    p_values: List[float]
    r_squared: float
    adj_r_squared: float
    n_obs: int
    df_resid: int
    degree: int
    residual_std: float

    def predict(self, x: float) -> float:
        """Evaluate the fitted polynomial at *x*."""
        return float(sum(b * (x ** k) for k, b in enumerate(self.beta)))

    def ci_excludes_zero(self, index: int) -> bool:
        """True if the 95% CI for coefficient *index* does not straddle zero."""
        lo, hi = self.ci95[index]
        return lo > 0.0 or hi < 0.0


def fit_with_inference(
    n: Sequence[float] | np.ndarray,
    y: Sequence[float] | np.ndarray,
    degree: int = 2,
    confidence: float = 0.95,
) -> RegressionInference:
    """Fit ``y = beta0 + beta1*n + ... + beta_degree*n^degree`` by OLS.

    Unlike :meth:`ScalabilityBenchmark.fit_scaling_model`, this returns the
    full inferential summary: standard errors from
    ``sigma_hat^2 * (X^T X)^-1``, t-based confidence intervals and two-sided
    p-values.  This is what a scaling claim such as "memory growth is
    quadratic" has to be argued from -- a quadratic coefficient whose CI
    straddles zero does not support such a claim.

    The design matrix columns are normalised before inversion and the fitted
    quantities rescaled afterwards, which is an exact reparameterisation and
    keeps ``(X^T X)^-1`` well conditioned when ``n^degree`` is large.

    Args:
        n: Predictor values (agent counts).
        y: Response values (latency in ms, memory in bytes, ...).
        degree: Polynomial degree; ``2`` gives the quadratic scaling model.
        confidence: Confidence level for the intervals.

    Returns:
        A :class:`RegressionInference`.

    Raises:
        ValueError: If *n* and *y* differ in length, if *degree* < 1, if any
            value is non-finite, or if there are not strictly more
            observations than coefficients (inference needs df_resid >= 1).
    """
    if degree < 1:
        raise ValueError(f"degree must be >= 1, got {degree}")
    if not 0.0 < confidence < 1.0:
        raise ValueError(f"confidence must be in (0, 1), got {confidence}")

    n_arr = np.asarray(n, dtype=np.float64).ravel()
    y_arr = np.asarray(y, dtype=np.float64).ravel()

    if n_arr.size != y_arr.size:
        raise ValueError(
            f"n and y must have equal length, got {n_arr.size} and {y_arr.size}"
        )
    if not np.all(np.isfinite(n_arr)) or not np.all(np.isfinite(y_arr)):
        raise ValueError("n and y must be finite; drop failed measurements first")

    n_params = degree + 1
    n_obs = int(n_arr.size)
    df_resid = n_obs - n_params
    if df_resid < 1:
        raise ValueError(
            f"need at least {n_params + 1} observations for degree-{degree} "
            f"inference, got {n_obs}"
        )

    design = np.vander(n_arr, N=n_params, increasing=True)

    # Column normalisation: exact reparameterisation, better conditioning.
    scale = np.linalg.norm(design, axis=0)
    scale[scale == 0.0] = 1.0
    design_s = design / scale

    gram_inv_s = np.linalg.pinv(design_s.T @ design_s)
    beta_s = gram_inv_s @ (design_s.T @ y_arr)
    beta = beta_s / scale

    fitted = design @ beta
    resid = y_arr - fitted
    ss_res = float(resid @ resid)
    ss_tot = float(np.sum((y_arr - y_arr.mean()) ** 2))

    sigma2 = ss_res / df_resid
    cov_s = sigma2 * gram_inv_s
    var_s = np.clip(np.diag(cov_s), 0.0, None)
    stderr = np.sqrt(var_s) / scale

    t_crit = float(stats.t.ppf((1.0 + confidence) / 2.0, df_resid))
    with np.errstate(divide="ignore", invalid="ignore"):
        t_stat = np.where(stderr > 0.0, beta / stderr, np.inf * np.sign(beta))
    t_stat = np.nan_to_num(t_stat, nan=0.0, posinf=np.inf, neginf=-np.inf)
    p_values = 2.0 * stats.t.sf(np.abs(t_stat), df_resid)

    r_sq = 1.0 - ss_res / ss_tot if ss_tot > 0.0 else 0.0
    adj_r_sq = 1.0 - (1.0 - r_sq) * (n_obs - 1) / df_resid

    return RegressionInference(
        beta=[float(b) for b in beta],
        stderr=[float(s) for s in stderr],
        ci95=[
            (float(b - t_crit * s), float(b + t_crit * s))
            for b, s in zip(beta, stderr)
        ],
        p_values=[float(p) for p in p_values],
        r_squared=float(r_sq),
        adj_r_squared=float(adj_r_sq),
        n_obs=n_obs,
        df_resid=int(df_resid),
        degree=int(degree),
        residual_std=float(np.sqrt(sigma2)),
    )


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

        A timing run whose ``evaluate()`` raises is counted as a *failure*
        and excluded from the latency distribution: the time-to-raise of a
        broken configuration is not a latency sample, and recording it makes
        the broken configuration look like the fastest one measured.  Failure
        counts are reported in ``ScalabilityResult.failures``; if every run
        at a given agent count fails, that count's latency is ``nan``.

        Args:
            adapter_class: The architecture adapter class (not instance).
            pipeline_factory: Callable ``(adapter, n_agents) -> pipeline``
                that builds a defense pipeline for the given adapter and
                agent count.  The pipeline must have an ``evaluate(msg)``
                method.

        Returns:
            A ``ScalabilityResult`` with latencies, memory, failure counts
            and the (possibly clamped) agent count used at each index.
        """
        latencies: List[float] = []
        memories: List[int] = []
        failures: List[int] = []
        clamped_counts: List[int] = []

        adapter = adapter_class()
        lo, hi = adapter.profile.agent_count_range

        for n in self.agent_counts:
            # Clamp agent count to adapter's supported range
            clamped_n = max(lo, min(hi, n))
            if clamped_n != n:
                logger.warning(
                    "requested agent count %d is outside the %s range [%d, %d]; "
                    "measuring at %d instead -- this point is NOT a measurement "
                    "at n=%d",
                    n,
                    getattr(adapter.profile, "name", type(adapter).__name__),
                    lo,
                    hi,
                    clamped_n,
                    n,
                )
            clamped_counts.append(clamped_n)

            # Build pipeline
            pipeline = pipeline_factory(adapter, clamped_n)

            # Time multiple runs of evaluate
            run_latencies: List[float] = []
            n_failed = 0
            sample_msg = f"test message for {clamped_n} agents"

            for _ in range(self.n_timing_runs):
                t0 = time.perf_counter()
                try:
                    try:
                        pipeline.evaluate(sample_msg)
                    except TypeError:
                        # Pipeline may require (message, context).  Restart the
                        # clock so the failed signature probe is not timed.
                        t0 = time.perf_counter()
                        pipeline.evaluate(sample_msg, None)
                except _EVALUATE_FAILURES as exc:
                    n_failed += 1
                    logger.debug(
                        "evaluate() failed at n=%d (%s: %s); excluded from latency",
                        clamped_n,
                        type(exc).__name__,
                        exc,
                    )
                    continue
                elapsed_ms = (time.perf_counter() - t0) * 1000.0
                run_latencies.append(elapsed_ms)

            if run_latencies:
                avg_latency = float(np.mean(run_latencies))
            else:
                logger.warning(
                    "all %d timing runs failed at n=%d; latency recorded as nan",
                    self.n_timing_runs,
                    clamped_n,
                )
                avg_latency = float("nan")
            latencies.append(avg_latency)
            failures.append(n_failed)

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
            failures=failures,
            clamped_counts=clamped_counts,
            n_timing_runs=self.n_timing_runs,
        )

    def fit_scaling_model(self, results: ScalabilityResult) -> ScalingModel:
        """Fit T = beta0 + beta1*n + beta2*n^2 using scipy least_squares.

        Agent counts whose latency is non-finite (every timing run failed)
        are dropped before fitting rather than poisoning the whole fit with
        ``nan``; the drop is logged.

        Args:
            results: Raw benchmark results.

        Returns:
            A ``ScalingModel`` with fitted coefficients and R-squared.
        """
        n_arr = np.array(results.agent_counts, dtype=np.float64)
        t_arr = np.array(results.latencies_ms, dtype=np.float64)

        finite = np.isfinite(t_arr) & np.isfinite(n_arr)
        if not finite.all():
            logger.warning(
                "dropping %d agent count(s) with non-finite latency before fitting",
                int((~finite).sum()),
            )
            n_arr = n_arr[finite]
            t_arr = t_arr[finite]

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
