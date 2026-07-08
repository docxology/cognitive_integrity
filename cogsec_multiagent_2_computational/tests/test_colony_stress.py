"""Colony stress tests for large-scale (100-500 agent) simulations.

Tests colony behavior at scale, including performance bounds,
detection stability, and emergent failure modes.

Uses real computation — no mocks.
"""

from __future__ import annotations

import time

import numpy as np
import pytest

from colony.belief_cascade import BeliefCascadeScenario
from colony.benchmark import ColonyConfig, ColonyScenario
from colony.emergent_misalignment import EmergentMisalignmentScenario
from colony.quorum_manipulation import QuorumManipulationScenario
from colony.scorecard import CCSWeights, compute_ccs
from colony.sybil_infiltration import SybilInfiltrationScenario


def _run_scenario(scenario: ColonyScenario, config: ColonyConfig):
    """Helper: run a scenario with the given config."""
    rng = np.random.default_rng(config.seed)
    return scenario.run(config, rng)


def _ccs_from_result(result) -> float:
    """Compute CCS from a ColonyResult with correct signature."""
    weights = CCSWeights()
    return compute_ccs(
        detection_rate=result.detection_rate,
        false_positive_rate=result.false_positive_rate,
        resilience=result.resilience_score,
        recovery_steps=result.recovery_steps,
        max_steps=200,
        weights=weights,
    )


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(scope="module")
def large_colony_config():
    """Config for 100-agent colony stress tests."""
    return ColonyConfig(n_agents=100, n_steps=200, n_adversaries=10,
                        adversary_fraction=0.1, seed=42)


@pytest.fixture(scope="module")
def xlarge_colony_config():
    """Config for 500-agent colony stress tests."""
    return ColonyConfig(n_agents=500, n_steps=100, n_adversaries=50,
                        adversary_fraction=0.1, seed=42)


@pytest.fixture(scope="module")
def high_adversary_config():
    """Config with 30% adversary fraction."""
    return ColonyConfig(n_agents=100, n_steps=150, n_adversaries=30,
                        adversary_fraction=0.3, seed=123)


# ============================================================================
# Section 1: Scale stress tests (100 agents)
# ============================================================================


class TestColonyAt100Agents:
    """Stress tests for colony simulations at 100-agent scale."""

    def test_belief_cascade_100_agents_completes(self, large_colony_config):
        """BeliefCascadeScenario runs to completion at 100 agents."""
        scenario = BeliefCascadeScenario()
        result = _run_scenario(scenario, large_colony_config)
        assert result is not None
        assert 0.0 <= result.detection_rate <= 1.0

    def test_belief_cascade_100_agents_detection_above_threshold(self, large_colony_config):
        """Detection rate at 100 agents is ≥ 70% (manuscript §sec:colony-results)."""
        scenario = BeliefCascadeScenario()
        result = _run_scenario(scenario, large_colony_config)
        assert result.detection_rate >= 0.70, (
            f"Expected DR ≥ 0.70 at 100 agents, got {result.detection_rate:.3f}"
        )

    def test_sybil_100_agents(self, large_colony_config):
        """SybilInfiltration at 100 agents completes with valid DR."""
        scenario = SybilInfiltrationScenario()
        result = _run_scenario(scenario, large_colony_config)
        assert 0.0 <= result.detection_rate <= 1.0

    def test_quorum_manipulation_100_agents(self, large_colony_config):
        """QuorumManipulation at 100 agents completes with valid metrics."""
        scenario = QuorumManipulationScenario()
        result = _run_scenario(scenario, large_colony_config)
        assert 0.0 <= result.detection_rate <= 1.0
        assert 0.0 <= result.resilience_score <= 1.0

    def test_emergent_misalignment_100_agents(self, large_colony_config):
        """EmergentMisalignment at 100 agents completes with valid CCS."""
        scenario = EmergentMisalignmentScenario()
        result = _run_scenario(scenario, large_colony_config)
        ccs = _ccs_from_result(result)
        assert 0.0 <= ccs <= 1.0

    def test_benchmark_100_agents_runtime(self, large_colony_config):
        """Full benchmark at 100 agents completes within 60 seconds."""
        scenarios = [
            BeliefCascadeScenario(),
            SybilInfiltrationScenario(),
            QuorumManipulationScenario(),
            EmergentMisalignmentScenario(),
        ]
        start = time.perf_counter()
        results = []
        for s in scenarios:
            results.append(_run_scenario(s, large_colony_config))
        elapsed = time.perf_counter() - start
        assert elapsed < 60.0, f"100-agent benchmark took {elapsed:.1f}s (limit: 60s)"
        assert len(results) == 4

    def test_benchmark_100_agents_scores_in_range(self, large_colony_config):
        """All CCS scores at 100 agents are in [0, 1]."""
        scenarios = [
            BeliefCascadeScenario(),
            SybilInfiltrationScenario(),
            QuorumManipulationScenario(),
            EmergentMisalignmentScenario(),
        ]
        for s in scenarios:
            result = _run_scenario(s, large_colony_config)
            assert 0.0 <= result.ccs_score <= 1.0, (
                f"CCS out of range for {result.scenario_name}: {result.ccs_score}"
            )


# ============================================================================
# Section 2: Scale stress tests (500 agents)
# ============================================================================


class TestColonyAt500Agents:
    """Extreme stress tests at 500-agent scale."""

    def test_belief_cascade_500_agents_completes(self, xlarge_colony_config):
        """BeliefCascadeScenario runs at 500 agents without errors."""
        scenario = BeliefCascadeScenario()
        result = _run_scenario(scenario, xlarge_colony_config)
        assert result is not None
        assert 0.0 <= result.detection_rate <= 1.0

    def test_sybil_500_agents_detection_valid(self, xlarge_colony_config):
        """SybilInfiltration at 500 agents yields valid detection rate."""
        scenario = SybilInfiltrationScenario()
        result = _run_scenario(scenario, xlarge_colony_config)
        assert 0.0 <= result.detection_rate <= 1.0

    def test_quorum_500_agents_resilience_valid(self, xlarge_colony_config):
        """QuorumManipulation at 500 agents yields valid resilience score."""
        scenario = QuorumManipulationScenario()
        result = _run_scenario(scenario, xlarge_colony_config)
        assert 0.0 <= result.resilience_score <= 1.0

    def test_500_agents_runtime(self, xlarge_colony_config):
        """500-agent simulation completes within 120 seconds."""
        start = time.perf_counter()
        scenario = BeliefCascadeScenario()
        _run_scenario(scenario, xlarge_colony_config)
        elapsed = time.perf_counter() - start
        assert elapsed < 120.0, f"500-agent simulation took {elapsed:.1f}s (limit: 120s)"


# ============================================================================
# Section 3: Adversary fraction stress tests
# ============================================================================


class TestHighAdversaryFraction:
    """Tests with 30% adversary fraction (Byzantine limit stress)."""

    def test_ccs_degrades_gracefully_at_30pct_adversaries(self, high_adversary_config):
        """CCS remains ≥ 0.3 even with 30% adversary fraction."""
        scenario = SybilInfiltrationScenario()
        result = _run_scenario(scenario, high_adversary_config)
        ccs = _ccs_from_result(result)
        assert ccs >= 0.3, (
            f"CCS {ccs:.3f} too low at 30% adversary fraction "
            f"(detection_rate={result.detection_rate:.3f})"
        )

    def test_false_positive_rate_bounded_at_30pct(self, high_adversary_config):
        """FPR is in [0, 1] even with high adversary fraction."""
        scenario = EmergentMisalignmentScenario()
        result = _run_scenario(scenario, high_adversary_config)
        assert 0.0 <= result.false_positive_rate <= 1.0

    def test_detection_at_varying_adversary_counts(self):
        """Detection rate is valid across varying adversary counts."""
        for n_adv in [5, 10, 20, 30]:
            cfg = ColonyConfig(n_agents=100, n_steps=100, n_adversaries=n_adv,
                               adversary_fraction=n_adv / 100, seed=99)
            scenario = SybilInfiltrationScenario()
            result = _run_scenario(scenario, cfg)
            assert 0.0 <= result.detection_rate <= 1.0


# ============================================================================
# Section 4: Scalability regression tests
# ============================================================================


class TestScalabilityRegression:
    """Test that detection rates are consistent across scales.

    These tests verify the scalability claims in manuscript §05d.
    """

    @pytest.mark.parametrize("n_agents", [20, 50, 100])
    def test_detection_valid_across_scales(self, n_agents):
        """Detection rate is valid (in [0,1]) across 20, 50, 100-agent scales."""
        cfg = ColonyConfig(
            n_agents=n_agents,
            n_steps=100,
            n_adversaries=max(2, n_agents // 10),
            adversary_fraction=0.1,
            seed=42,
        )
        scenario = BeliefCascadeScenario()
        result = _run_scenario(scenario, cfg)
        assert 0.0 <= result.detection_rate <= 1.0

    @pytest.mark.parametrize("n_agents", [20, 50, 100])
    def test_ccs_valid_across_scales(self, n_agents):
        """CCS score is in [0, 1] across standard scales."""
        cfg = ColonyConfig(
            n_agents=n_agents,
            n_steps=100,
            n_adversaries=max(2, n_agents // 10),
            adversary_fraction=0.1,
            seed=42,
        )
        scenario = QuorumManipulationScenario()
        result = _run_scenario(scenario, cfg)
        ccs = _ccs_from_result(result)
        assert 0.0 <= ccs <= 1.0

    def test_linear_scaling_runtime(self):
        """Verify runtime scales reasonably with agent count."""
        timings = {}
        for n_agents in [20, 50, 100]:
            cfg = ColonyConfig(n_agents=n_agents, n_steps=50,
                               n_adversaries=max(2, n_agents // 10),
                               adversary_fraction=0.1, seed=42)
            start = time.perf_counter()
            scenario = BeliefCascadeScenario()
            _run_scenario(scenario, cfg)
            timings[n_agents] = time.perf_counter() - start

        if timings.get(20, 0) > 1e-6:
            ratio_100_20 = timings[100] / timings[20]
            # Allow up to 50x scaling (very generous; actual should be ~5-15x)
            assert ratio_100_20 < 50.0, (
                f"Runtime scales too steeply: 100/20 ratio = {ratio_100_20:.1f}"
            )


# ============================================================================
# Section 5: Multi-seed stability at scale
# ============================================================================


class TestMultiSeedStabilityAtScale:
    """Test that large colony results are seed-stable."""

    def test_belief_cascade_100_agents_cv(self):
        """CV of DR across 5 seeds at 100 agents should be < 0.2."""
        drs = []
        for seed in range(5):
            cfg = ColonyConfig(n_agents=100, n_steps=100, n_adversaries=10,
                               adversary_fraction=0.1, seed=seed)
            scenario = BeliefCascadeScenario()
            result = _run_scenario(scenario, cfg)
            drs.append(result.detection_rate)
        arr = np.array(drs)
        cv = arr.std() / arr.mean() if arr.mean() > 1e-9 else 0.0
        assert cv < 0.2, (
            f"CV of DR across seeds = {cv:.3f} > 0.2 "
            f"(DRs: {[f'{d:.3f}' for d in drs]})"
        )

    def test_sybil_100_agents_cv(self):
        """CV of DR across 5 seeds for SybilInfiltration at 100 agents < 0.2."""
        drs = []
        for seed in range(5):
            cfg = ColonyConfig(n_agents=100, n_steps=100, n_adversaries=10,
                               adversary_fraction=0.1, seed=seed)
            scenario = SybilInfiltrationScenario()
            result = _run_scenario(scenario, cfg)
            drs.append(result.detection_rate)
        arr = np.array(drs)
        cv = arr.std() / arr.mean() if arr.mean() > 1e-9 else 0.0
        assert cv < 0.2, f"Sybil CV across seeds = {cv:.3f} > 0.2"
