"""Tests for scalability measurement robustness and regression inference.

Covers three defects and one missing capability:

* A failed ``evaluate()`` must not contribute a latency sample (its
  time-to-raise is ~0 ms and makes the broken configuration look fastest).
* ``MemoryProfiler`` must not swallow every attribute error while walking a
  pipeline; unreadable attributes must be reported and unexpected exceptions
  must propagate.
* ``fit_with_inference`` must supply standard errors, confidence intervals
  and p-values -- and must be *able to decline* a quadratic claim when the
  data contain no quadratic term.

Every property test is paired with a control that shows it can fail.
No mocks: all pipelines below are real objects doing real work.
"""

from __future__ import annotations

import logging
import time

import numpy as np
import pytest

from architectures.base import ArchitectureAdapter, ArchitectureProfile
from evaluation.benchmark import MemoryEstimate, MemoryProfiler
from evaluation.scalability import (
    RegressionInference,
    ScalabilityBenchmark,
    ScalabilityResult,
    fit_with_inference,
)

# ---------------------------------------------------------------------------
# Real (non-mock) test doubles: concrete classes doing real computation
# ---------------------------------------------------------------------------


class _WideAdapter(ArchitectureAdapter):
    """Concrete adapter supporting 1..200 agents (no clamping in range)."""

    _PROFILE = ArchitectureProfile(
        name="WideTestArch",
        agent_count_range=(1, 200),
        trust_topology="flat",
        has_central_orchestrator=False,
        communication_pattern="mesh",
        delegation_depth=1,
    )

    @property
    def profile(self) -> ArchitectureProfile:
        return self._PROFILE

    def create_trust_matrix(self, n_agents: int) -> np.ndarray:
        return np.eye(n_agents, dtype=np.float64)

    def get_agent_roles(self, n_agents: int) -> list:
        return ["worker"] * n_agents

    def get_communication_graph(self, n_agents: int) -> np.ndarray:
        return np.ones((n_agents, n_agents), dtype=np.float64)

    def simulate_delegation(self, source: int, target: int, depth: int) -> float:
        return 0.9**depth

    def get_attack_surface_multiplier(self) -> float:
        return 1.0


class _NarrowAdapter(_WideAdapter):
    """Adapter that supports only 2..10 agents, so larger counts clamp."""

    _PROFILE = ArchitectureProfile(
        name="NarrowTestArch",
        agent_count_range=(2, 10),
        trust_topology="flat",
        has_central_orchestrator=False,
        communication_pattern="mesh",
        delegation_depth=1,
    )


class _WorkingPipeline:
    """Pipeline that sleeps a fixed, known duration on every evaluation."""

    #: Guaranteed lower bound on one successful evaluation, in milliseconds.
    SUCCESS_MS = 5.0

    def __init__(self, n_agents: int) -> None:
        self.n_agents = n_agents
        self.modules: list = []
        self.calls = 0

    def evaluate(self, message: str, context=None):
        self.calls += 1
        time.sleep(self.SUCCESS_MS / 1000.0)
        return True


class _AlwaysFailingPipeline:
    """Pipeline whose evaluate raises immediately on every call."""

    def __init__(self, n_agents: int) -> None:
        self.n_agents = n_agents
        self.modules: list = []
        self.calls = 0

    def evaluate(self, message: str, context=None):
        self.calls += 1
        raise ValueError("unsupported agent configuration")


class _HalfFailingPipeline(_WorkingPipeline):
    """Fails the first *n_failures* calls instantly, then works normally."""

    def __init__(self, n_agents: int, n_failures: int) -> None:
        super().__init__(n_agents)
        self.n_failures = n_failures

    def evaluate(self, message: str, context=None):
        self.calls += 1
        if self.calls <= self.n_failures:
            raise RuntimeError("transient backend outage")
        return super().evaluate(message, context)


class _ContextOnlyPipeline(_WorkingPipeline):
    """Pipeline that requires the (message, context) two-argument form."""

    def evaluate(self, message: str, context=None):  # type: ignore[override]
        if context is None and not getattr(self, "_probed", False):
            self._probed = True
            raise TypeError("evaluate() missing 1 required positional argument")
        return super().evaluate(message, context)


class _UnexpectedErrorPipeline:
    """Pipeline raising an exception type outside the failure allow-list."""

    def __init__(self, n_agents: int) -> None:
        self.n_agents = n_agents
        self.modules: list = []

    def evaluate(self, message: str, context=None):
        raise KeyError("configuration key missing")


# ===========================================================================
# Section 1: failed evaluate() must not become a latency sample
# ===========================================================================


class TestFailedEvaluationsExcludedFromLatency:
    """A time-to-raise is not a latency measurement."""

    def test_all_failing_count_yields_nan_not_a_fast_measurement(self):
        """The pathology: a broken count used to look like the fastest one."""
        counts = [2, 10, 50]

        def factory(adapter, n):
            return _AlwaysFailingPipeline(n) if n == 50 else _WorkingPipeline(n)

        bench = ScalabilityBenchmark(agent_counts=counts, n_timing_runs=4)
        result = bench.run(_WideAdapter, factory)

        assert result.failures == [0, 0, 4]
        assert result.total_failures == 4
        assert np.isnan(result.latencies_ms[2])
        # Positive control on the defect itself: before the fix the broken
        # count produced a *finite, near-zero* latency.  Assert it is not a
        # finite value smaller than the working counts.
        assert not (
            np.isfinite(result.latencies_ms[2])
            and result.latencies_ms[2] < min(result.latencies_ms[:2])
        )

    def test_partial_failures_do_not_drag_the_mean_down(self):
        """Mean must be over successes only, not successes plus zeros."""
        n_runs = 10
        n_failures = 5

        def factory(adapter, n):
            return _HalfFailingPipeline(n, n_failures=n_failures)

        bench = ScalabilityBenchmark(agent_counts=[8], n_timing_runs=n_runs)
        result = bench.run(_WideAdapter, factory)

        assert result.failures == [n_failures]
        measured = result.latencies_ms[0]
        # Each success sleeps >= 5 ms, so an honest mean is >= 5 ms.  Averaging
        # the 5 instant failures in as well would put it near 2.5 ms.
        assert measured >= _WorkingPipeline.SUCCESS_MS * 0.9, measured
        # Upper bound is a load-tolerance sanity check, not the bug detector:
        # averaging the 5 failed (0 ms) runs in would drive the mean to ~2.5 ms,
        # which already fails the lower bound above.  A loaded scheduler can
        # stretch a 5 ms sleep past 10 ms wall-clock, so keep it generous here.
        assert measured < _WorkingPipeline.SUCCESS_MS * 6.0, measured

    def test_context_requiring_pipeline_still_measured(self):
        """A TypeError signature probe is a retry, not a failure."""
        bench = ScalabilityBenchmark(agent_counts=[4], n_timing_runs=3)
        result = bench.run(_WideAdapter, lambda adapter, n: _ContextOnlyPipeline(n))

        assert result.failures == [0]
        assert np.isfinite(result.latencies_ms[0])

    def test_unexpected_exception_type_propagates(self):
        """Only the declared failure types are absorbed; others surface."""
        bench = ScalabilityBenchmark(agent_counts=[4], n_timing_runs=2)
        with pytest.raises(KeyError):
            bench.run(_WideAdapter, lambda adapter, n: _UnexpectedErrorPipeline(n))

    def test_failure_is_logged_at_debug(self, caplog):
        def factory(adapter, n):
            return _AlwaysFailingPipeline(n)

        bench = ScalabilityBenchmark(agent_counts=[4], n_timing_runs=2)
        with caplog.at_level(logging.DEBUG, logger="evaluation.scalability"):
            bench.run(_WideAdapter, factory)
        assert any("excluded from latency" in rec.message for rec in caplog.records)

    def test_clamped_counts_are_recorded_and_flagged(self):
        """A count outside the adapter range is not a measurement at n."""
        bench = ScalabilityBenchmark(agent_counts=[2, 10, 50], n_timing_runs=2)
        result = bench.run(_NarrowAdapter, lambda adapter, n: _WorkingPipeline(n))

        assert result.clamped_counts == [2, 10, 10]
        assert result.any_clamped is True

        unclamped = ScalabilityBenchmark(agent_counts=[2, 10], n_timing_runs=2).run(
            _NarrowAdapter, lambda adapter, n: _WorkingPipeline(n)
        )
        assert unclamped.any_clamped is False

    def test_memory_estimate_accounts_for_pipeline_modules(self):
        """A pipeline carrying modules must estimate larger than a bare one."""

        class _Module:
            def __init__(self, payload: np.ndarray) -> None:
                self.payload = payload

        class _ModularPipeline(_WorkingPipeline):
            def __init__(self, n_agents: int) -> None:
                super().__init__(n_agents)
                self.modules = [
                    _Module(np.zeros(1000, dtype=np.float64)) for _ in range(4)
                ]

        bench = ScalabilityBenchmark(agent_counts=[4], n_timing_runs=1)
        bare = bench.run(_WideAdapter, lambda adapter, n: _WorkingPipeline(n))
        modular = bench.run(_WideAdapter, lambda adapter, n: _ModularPipeline(n))

        assert modular.memory_bytes[0] > bare.memory_bytes[0]

    def test_fit_drops_non_finite_latencies(self):
        """A nan from an all-failed count must not poison the whole fit."""
        counts = [2, 5, 10, 20, 50]
        latencies = [1.0 + 0.1 * n + 0.005 * n * n for n in counts]
        latencies[2] = float("nan")

        result = ScalabilityResult(
            agent_counts=counts,
            latencies_ms=latencies,
            memory_bytes=[n * n * 16 for n in counts],
        )
        model = ScalabilityBenchmark().fit_scaling_model(result)

        assert np.isfinite(model.beta0)
        assert np.isfinite(model.beta2)
        assert model.beta2 == pytest.approx(0.005, abs=1e-3)


# ===========================================================================
# Section 2: MemoryProfiler must not swallow every error
# ===========================================================================


class _LazyPipeline:
    """Pipeline with a property that raises until initialisation happens."""

    def __init__(self) -> None:
        self.small = np.zeros(10, dtype=np.float64)

    @property
    def big_matrix(self) -> np.ndarray:
        raise RuntimeError("lazy initialisation not yet performed")


class _ReadyPipeline:
    """Same shape as _LazyPipeline but with the big attribute readable."""

    def __init__(self) -> None:
        self.small = np.zeros(10, dtype=np.float64)
        self.big_matrix = np.zeros((500, 500), dtype=np.float64)  # 2 MB


class _BrokenPipeline:
    """Pipeline whose property raises an error outside the skip list."""

    @property
    def config(self):
        raise KeyError("missing config key")


class TestMemoryProfilerErrorHandling:
    """An unreadable attribute is a reported gap, not a silent zero."""

    def test_unreadable_attribute_is_reported_not_swallowed(self):
        estimate = MemoryProfiler().estimate_memory_detailed(_LazyPipeline(), n_agents=10)

        assert isinstance(estimate, MemoryEstimate)
        assert estimate.is_complete is False
        names = [name for name, _ in estimate.skipped_attributes]
        assert names == ["big_matrix"]
        assert "RuntimeError" in estimate.skipped_attributes[0][1]

    def test_undercount_is_material_and_measurable(self):
        """POSITIVE CONTROL: quantify what the silent skip used to hide."""
        profiler = MemoryProfiler()
        lazy = profiler.estimate_memory_detailed(_LazyPipeline(), n_agents=10)
        ready = profiler.estimate_memory_detailed(_ReadyPipeline(), n_agents=10)

        assert ready.is_complete is True
        # 500x500 float64 == 2,000,000 bytes of state dropped from the total.
        assert ready.total_bytes - lazy.total_bytes > 2_000_000

    def test_complete_pipeline_reports_no_skips(self):
        estimate = MemoryProfiler().estimate_memory_detailed(_ReadyPipeline(), n_agents=4)
        assert estimate.is_complete is True
        assert estimate.skipped_attributes == []

    def test_unexpected_exception_propagates(self):
        """A genuinely broken pipeline surfaces instead of undercounting."""
        with pytest.raises(KeyError):
            MemoryProfiler().estimate_memory_detailed(_BrokenPipeline(), n_agents=4)

    def test_int_api_warns_when_the_total_is_an_undercount(self, caplog):
        with caplog.at_level(logging.WARNING, logger="evaluation.benchmark"):
            total = MemoryProfiler().estimate_memory(_LazyPipeline(), n_agents=10)
        assert total > 0
        assert any("undercount" in rec.message for rec in caplog.records)

    def test_int_api_matches_detailed_total(self):
        profiler = MemoryProfiler()
        pipeline = _ReadyPipeline()
        assert profiler.estimate_memory(pipeline, n_agents=7) == (
            profiler.estimate_memory_detailed(pipeline, n_agents=7).total_bytes
        )

    def test_negative_agent_count_rejected(self):
        with pytest.raises(ValueError, match="n_agents must be >= 0"):
            MemoryProfiler().estimate_memory_detailed(_ReadyPipeline(), n_agents=-1)


# ===========================================================================
# Section 3: regression inference (SEs, CIs, p-values)
# ===========================================================================


class TestFitWithInference:
    """A scaling claim needs an interval, and must be refusable."""

    def test_recovers_known_quadratic_and_declares_it_significant(self):
        """POSITIVE CONTROL: true quadratic -> tight CI excluding zero."""
        rng = np.random.default_rng(20260726)
        n = np.repeat(np.array([2, 5, 10, 15, 20, 30, 50, 75, 100], dtype=float), 5)
        y = 3.0 + 2.0 * n + 0.5 * n**2 + rng.normal(0.0, 0.5, size=n.size)

        fit = fit_with_inference(n, y, degree=2)

        assert isinstance(fit, RegressionInference)
        assert fit.n_obs == 45
        assert fit.df_resid == 42
        assert fit.beta[0] == pytest.approx(3.0, abs=0.5)
        assert fit.beta[1] == pytest.approx(2.0, abs=0.1)
        assert fit.beta[2] == pytest.approx(0.5, abs=0.01)
        assert fit.p_values[2] < 0.01
        assert fit.ci_excludes_zero(2) is True
        assert fit.r_squared > 0.999

    def test_declines_quadratic_when_data_are_linear(self):
        """NEGATIVE CONTROL: no quadratic term -> beta2 CI straddles zero.

        This is the property the prose never allowed for.  If this test
        passed unconditionally the inference would be incapable of refusing
        a quadratic claim, which would make the positive control worthless.
        """
        rng = np.random.default_rng(7)
        n = np.repeat(np.array([2, 5, 10, 15, 20, 30, 50, 75, 100], dtype=float), 5)
        y = 3.0 + 2.0 * n + rng.normal(0.0, 5.0, size=n.size)

        fit = fit_with_inference(n, y, degree=2)

        lo, hi = fit.ci95[2]
        assert lo < 0.0 < hi, f"beta2 CI {fit.ci95[2]} should straddle zero"
        assert fit.p_values[2] > 0.05
        assert fit.ci_excludes_zero(2) is False
        # The linear term is still recovered, so the fit is not simply broken.
        assert fit.beta[1] == pytest.approx(2.0, abs=0.5)
        assert fit.ci_excludes_zero(1) is True

    def test_standard_errors_shrink_as_noise_shrinks(self):
        """SEs must track the data, not be a constant the code emits."""
        n = np.repeat(np.array([2, 5, 10, 20, 50, 100], dtype=float), 6)
        truth = 3.0 + 2.0 * n + 0.5 * n**2

        noisy = fit_with_inference(
            n, truth + np.random.default_rng(1).normal(0.0, 20.0, size=n.size)
        )
        quiet = fit_with_inference(
            n, truth + np.random.default_rng(1).normal(0.0, 0.2, size=n.size)
        )
        assert quiet.stderr[2] < noisy.stderr[2] / 10.0

    def test_predict_matches_manual_polynomial_evaluation(self):
        n = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
        y = 1.0 + 2.0 * n + 3.0 * n**2
        fit = fit_with_inference(n, y, degree=2)
        expected = fit.beta[0] + fit.beta[1] * 7.0 + fit.beta[2] * 49.0
        assert fit.predict(7.0) == pytest.approx(expected)

    def test_linear_degree_supported(self):
        n = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y = 4.0 + 3.0 * n
        fit = fit_with_inference(n, y, degree=1)
        assert fit.degree == 1
        assert len(fit.beta) == 2
        assert fit.beta[1] == pytest.approx(3.0, abs=1e-6)

    def test_confidence_level_widens_the_interval(self):
        rng = np.random.default_rng(3)
        n = np.repeat(np.array([2.0, 5.0, 10.0, 20.0, 50.0]), 4)
        y = 1.0 + 1.5 * n + 0.02 * n**2 + rng.normal(0.0, 2.0, size=n.size)

        narrow = fit_with_inference(n, y, confidence=0.80)
        wide = fit_with_inference(n, y, confidence=0.99)
        nw = narrow.ci95[2][1] - narrow.ci95[2][0]
        ww = wide.ci95[2][1] - wide.ci95[2][0]
        assert ww > nw

    def test_insufficient_observations_rejected(self):
        with pytest.raises(ValueError, match="need at least 4 observations"):
            fit_with_inference([1.0, 2.0, 3.0], [1.0, 2.0, 3.0], degree=2)

    def test_non_finite_input_rejected(self):
        with pytest.raises(ValueError, match="must be finite"):
            fit_with_inference(
                [1.0, 2.0, 3.0, 4.0, 5.0], [1.0, 2.0, float("nan"), 4.0, 5.0]
            )

    def test_length_mismatch_rejected(self):
        with pytest.raises(ValueError, match="equal length"):
            fit_with_inference([1.0, 2.0, 3.0, 4.0], [1.0, 2.0, 3.0])

    def test_invalid_degree_rejected(self):
        with pytest.raises(ValueError, match="degree must be >= 1"):
            fit_with_inference([1.0, 2.0, 3.0, 4.0], [1.0, 2.0, 3.0, 4.0], degree=0)

    def test_invalid_confidence_rejected(self):
        with pytest.raises(ValueError, match="confidence must be in"):
            fit_with_inference(
                [1.0, 2.0, 3.0, 4.0], [1.0, 2.0, 3.0, 4.0], confidence=1.0
            )

    def test_large_agent_counts_do_not_destroy_conditioning(self):
        """n^2 up to 1e4 must not blow up the (X'X)^-1 based SEs."""
        n = np.repeat(np.array([2, 3, 5, 7, 10, 15, 20, 30, 50, 100], dtype=float), 3)
        y = 7642.0 - 203.0 * n + 33.5 * n**2
        fit = fit_with_inference(n, y, degree=2)

        assert fit.beta[2] == pytest.approx(33.5, rel=1e-6)
        assert fit.beta[1] == pytest.approx(-203.0, rel=1e-4)
        assert all(np.isfinite(s) for s in fit.stderr)
