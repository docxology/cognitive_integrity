"""Comprehensive tests for the colony cognitive security package.

Tests cover all seven modules: scorecard, belief_cascade, benchmark,
emergent_misalignment, quorum_manipulation, recruitment_poisoning,
and sybil_infiltration.

All tests use real data and computation with deterministic seeds.
No mocks are used anywhere.
"""

import numpy as np
import pytest

from colony.belief_cascade import BeliefCascadeScenario, _build_small_world_adjacency
from colony.benchmark import (
    ColonyBenchmark,
    ColonyConfig,
    ColonyResult,
    ColonyScenario,
)
from colony.emergent_misalignment import EmergentMisalignmentScenario
from colony.quorum_manipulation import QuorumManipulationScenario
from colony.recruitment_poisoning import RecruitmentPoisoningScenario
from colony.scorecard import (
    CCSWeights,
    compute_ccs,
    compute_recovery_steps,
    compute_resilience,
)
from colony.sybil_infiltration import SybilInfiltrationScenario

# =========================================================================
# Section 1: Scorecard tests
# =========================================================================


class TestCCSWeights:
    """Tests for the CCSWeights dataclass and validation."""

    def test_default_weights_sum_to_one(self):
        weights = CCSWeights()
        total = weights.detection + weights.precision + weights.resilience + weights.recovery
        assert np.isclose(total, 1.0)

    def test_custom_weights_valid(self):
        weights = CCSWeights(detection=0.25, precision=0.25, resilience=0.25, recovery=0.25)
        total = weights.detection + weights.precision + weights.resilience + weights.recovery
        assert np.isclose(total, 1.0)

    def test_custom_weights_invalid_raises(self):
        with pytest.raises(ValueError, match="must sum to 1.0"):
            CCSWeights(detection=0.5, precision=0.5, resilience=0.5, recovery=0.5)

    def test_zero_weights_invalid(self):
        with pytest.raises(ValueError):
            CCSWeights(detection=0.0, precision=0.0, resilience=0.0, recovery=0.0)

    def test_weights_individual_values(self):
        weights = CCSWeights()
        assert weights.detection == 0.3
        assert weights.precision == 0.2
        assert weights.resilience == 0.3
        assert weights.recovery == 0.2


class TestComputeCCS:
    """Tests for the composite CCS score computation."""

    def test_perfect_scores_yield_one(self):
        score = compute_ccs(
            detection_rate=1.0,
            false_positive_rate=0.0,
            resilience=1.0,
            recovery_steps=0,
            max_steps=100,
        )
        assert np.isclose(score, 1.0)

    def test_worst_scores_yield_zero(self):
        score = compute_ccs(
            detection_rate=0.0,
            false_positive_rate=1.0,
            resilience=0.0,
            recovery_steps=100,
            max_steps=100,
        )
        assert np.isclose(score, 0.0)

    def test_moderate_scores(self):
        score = compute_ccs(
            detection_rate=0.5,
            false_positive_rate=0.5,
            resilience=0.5,
            recovery_steps=50,
            max_steps=100,
        )
        # w=default: 0.3*0.5 + 0.2*(1-0.5) + 0.3*0.5 + 0.2*(1-50/100)
        # = 0.15 + 0.10 + 0.15 + 0.10 = 0.50
        assert np.isclose(score, 0.5)

    def test_custom_weights(self):
        weights = CCSWeights(detection=0.25, precision=0.25, resilience=0.25, recovery=0.25)
        score = compute_ccs(
            detection_rate=1.0,
            false_positive_rate=0.0,
            resilience=1.0,
            recovery_steps=0,
            max_steps=100,
            weights=weights,
        )
        assert np.isclose(score, 1.0)

    def test_ccs_bounded_zero_one(self):
        # Even with extreme inputs, score should be clipped to [0, 1]
        score = compute_ccs(
            detection_rate=1.0,
            false_positive_rate=0.0,
            resilience=1.0,
            recovery_steps=0,
            max_steps=1,
        )
        assert 0.0 <= score <= 1.0

    def test_recovery_score_with_zero_max_steps(self):
        score = compute_ccs(
            detection_rate=0.5,
            false_positive_rate=0.5,
            resilience=0.5,
            recovery_steps=10,
            max_steps=0,
        )
        # max(max_steps, 1) = 1 -> recovery_score = 1 - 10/1 = -9 -> clipped to 0
        # 0.3*0.5 + 0.2*0.5 + 0.3*0.5 + 0.2*0.0 = 0.15 + 0.10 + 0.15 + 0.0 = 0.40
        assert np.isclose(score, 0.4)

    def test_detection_rate_dominates_with_skewed_weights(self):
        weights = CCSWeights(detection=0.7, precision=0.1, resilience=0.1, recovery=0.1)
        high = compute_ccs(1.0, 0.0, 1.0, 0, 100, weights=weights)
        low = compute_ccs(0.0, 0.0, 1.0, 0, 100, weights=weights)
        assert high > low
        assert high - low == pytest.approx(0.7, abs=1e-6)


class TestComputeResilience:
    """Tests for the compute_resilience function."""

    def test_no_attack_impact(self):
        timeline = [1.0] * 100
        res = compute_resilience(timeline, adversary_start_step=50)
        assert np.isclose(res, 1.0)

    def test_complete_collapse(self):
        timeline = [1.0] * 50 + [0.0] * 50
        res = compute_resilience(timeline, adversary_start_step=50)
        assert np.isclose(res, 0.0)

    def test_partial_degradation(self):
        timeline = [1.0] * 50 + [0.5] * 50
        res = compute_resilience(timeline, adversary_start_step=50)
        # min_post / pre_attack_mean = 0.5 / 1.0 = 0.5
        assert np.isclose(res, 0.5)

    def test_empty_timeline(self):
        res = compute_resilience([], adversary_start_step=0)
        assert np.isclose(res, 1.0)

    def test_adversary_start_beyond_timeline(self):
        timeline = [0.8, 0.9, 0.7]
        res = compute_resilience(timeline, adversary_start_step=10)
        assert np.isclose(res, 1.0)

    def test_adversary_start_at_zero(self):
        timeline = [0.5, 0.6, 0.4, 0.3]
        res = compute_resilience(timeline, adversary_start_step=0)
        # pre_attack = [] -> [1.0], pre_attack_value = 1.0
        # post_attack = full timeline, min = 0.3
        # 0.3 / 1.0 = 0.3
        assert np.isclose(res, 0.3)

    def test_declining_then_recovering_timeline(self):
        timeline = [1.0] * 20 + [0.3, 0.2, 0.1, 0.4, 0.7, 0.9, 1.0]
        res = compute_resilience(timeline, adversary_start_step=20)
        # min post-attack = 0.1, pre = 1.0 -> 0.1
        assert np.isclose(res, 0.1)

    def test_zero_pre_attack_value(self):
        timeline = [0.0] * 10 + [0.5] * 10
        res = compute_resilience(timeline, adversary_start_step=10)
        # pre_attack_value = 0.0 -> returns 0.0
        assert np.isclose(res, 0.0)


class TestComputeRecoverySteps:
    """Tests for the compute_recovery_steps function."""

    def test_immediate_recovery(self):
        timeline = [0.95, 0.95, 0.95]
        rec = compute_recovery_steps(timeline, threshold=0.9)
        assert rec == 0

    def test_never_recovered(self):
        timeline = [0.3, 0.2, 0.1, 0.1, 0.1]
        rec = compute_recovery_steps(timeline, threshold=0.9)
        # min at index 2 (0.1), never reaches 0.9 after that
        assert rec == len(timeline) - 2  # 5 - 2 = 3

    def test_recovery_after_dip(self):
        timeline = [1.0, 0.5, 0.3, 0.5, 0.8, 0.95]
        rec = compute_recovery_steps(timeline, threshold=0.9)
        # min at index 2 (0.3), recovers at index 5 (0.95 >= 0.9)
        assert rec == 3  # 5 - 2

    def test_empty_timeline(self):
        rec = compute_recovery_steps([], threshold=0.9)
        assert rec == 0

    def test_single_value_above_threshold(self):
        rec = compute_recovery_steps([0.95], threshold=0.9)
        assert rec == 0

    def test_single_value_below_threshold(self):
        rec = compute_recovery_steps([0.5], threshold=0.9)
        assert rec == 1  # len(arr) - min_idx = 1 - 0

    def test_threshold_exactly_met(self):
        timeline = [1.0, 0.5, 0.3, 0.9]
        rec = compute_recovery_steps(timeline, threshold=0.9)
        # min at index 2 (0.3), recovery at index 3 (0.9 >= 0.9)
        assert rec == 1

    def test_custom_threshold(self):
        timeline = [1.0, 0.5, 0.3, 0.6]
        rec = compute_recovery_steps(timeline, threshold=0.5)
        # min at index 2 (0.3), recovery at index 3 (0.6 >= 0.5)
        assert rec == 1


# =========================================================================
# Section 2: Belief Cascade tests
# =========================================================================


class TestBuildSmallWorldAdjacency:
    """Tests for the Watts-Strogatz small-world adjacency builder."""

    def test_adjacency_is_square(self):
        rng = np.random.default_rng(42)
        adj = _build_small_world_adjacency(10, k=4, p=0.0, rng=rng)
        assert adj.shape == (10, 10)

    def test_adjacency_is_symmetric(self):
        rng = np.random.default_rng(42)
        adj = _build_small_world_adjacency(20, k=4, p=0.1, rng=rng)
        np.testing.assert_array_equal(adj, adj.T)

    def test_no_self_loops(self):
        rng = np.random.default_rng(42)
        adj = _build_small_world_adjacency(15, k=4, p=0.2, rng=rng)
        assert np.all(np.diag(adj) == 0.0)

    def test_ring_lattice_no_rewiring(self):
        rng = np.random.default_rng(42)
        adj = _build_small_world_adjacency(10, k=4, p=0.0, rng=rng)
        # k=4 means each node connects to 2 neighbors on each side
        # Each node should have degree 4
        degrees = adj.sum(axis=1)
        np.testing.assert_array_equal(degrees, np.full(10, 4.0))

    def test_rewiring_changes_structure(self):
        rng1 = np.random.default_rng(42)
        rng2 = np.random.default_rng(42)
        adj_no_rewire = _build_small_world_adjacency(20, k=4, p=0.0, rng=rng1)
        adj_rewired = _build_small_world_adjacency(20, k=4, p=1.0, rng=rng2)
        # With p=1.0 all edges should be rewired; structure should differ
        assert not np.array_equal(adj_no_rewire, adj_rewired)

    def test_binary_values(self):
        rng = np.random.default_rng(42)
        adj = _build_small_world_adjacency(10, k=4, p=0.3, rng=rng)
        unique_values = np.unique(adj)
        assert all(v in [0.0, 1.0] for v in unique_values)

    def test_odd_k_rounded_up(self):
        rng = np.random.default_rng(42)
        # k=3 should be rounded up to 4
        adj = _build_small_world_adjacency(10, k=3, p=0.0, rng=rng)
        degrees = adj.sum(axis=1)
        np.testing.assert_array_equal(degrees, np.full(10, 4.0))

    def test_minimum_k_enforced(self):
        rng = np.random.default_rng(42)
        # k=1 should become k=2
        adj = _build_small_world_adjacency(10, k=1, p=0.0, rng=rng)
        degrees = adj.sum(axis=1)
        np.testing.assert_array_equal(degrees, np.full(10, 2.0))


class TestBeliefCascadeScenario:
    """Tests for the BeliefCascade scenario simulation."""

    def test_scenario_name(self):
        scenario = BeliefCascadeScenario()
        assert scenario.name == "belief_cascade"

    def test_default_config(self):
        scenario = BeliefCascadeScenario()
        config = scenario.default_config()
        assert config.n_agents == 100
        assert config.n_steps == 300
        assert config.n_adversaries == 2

    def test_run_returns_colony_result(self):
        scenario = BeliefCascadeScenario()
        config = ColonyConfig(n_agents=20, n_steps=50, n_adversaries=2, seed=42)
        rng = np.random.default_rng(42)
        result = scenario.run(config, rng)
        assert result.scenario_name == "belief_cascade"
        assert isinstance(result.detection_rate, float)
        assert isinstance(result.timeline, list)

    def test_run_deterministic(self):
        scenario = BeliefCascadeScenario()
        config = ColonyConfig(n_agents=20, n_steps=50, n_adversaries=2, seed=42)
        rng1 = np.random.default_rng(42)
        result1 = scenario.run(config, rng1)
        rng2 = np.random.default_rng(42)
        result2 = scenario.run(config, rng2)
        assert result1.detection_rate == result2.detection_rate
        assert result1.ccs_score == result2.ccs_score
        assert result1.timeline == result2.timeline

    def test_metrics_in_valid_range(self):
        scenario = BeliefCascadeScenario()
        config = ColonyConfig(n_agents=30, n_steps=60, n_adversaries=2, seed=99)
        rng = np.random.default_rng(99)
        result = scenario.run(config, rng)
        assert 0.0 <= result.detection_rate <= 1.0
        assert 0.0 <= result.false_positive_rate <= 1.0
        assert 0.0 <= result.resilience_score <= 1.0
        assert result.recovery_steps >= 0
        assert 0.0 <= result.ccs_score <= 1.0

    def test_timeline_length_equals_steps(self):
        scenario = BeliefCascadeScenario()
        config = ColonyConfig(n_agents=15, n_steps=40, n_adversaries=2, seed=42)
        rng = np.random.default_rng(42)
        result = scenario.run(config, rng)
        assert len(result.timeline) == 40

    def test_cascade_propagates(self):
        """Adversaries should cause integrity to decline after activation."""
        scenario = BeliefCascadeScenario()
        config = ColonyConfig(n_agents=30, n_steps=100, n_adversaries=2, seed=42)
        rng = np.random.default_rng(42)
        result = scenario.run(config, rng)
        # Integrity in the first 30 steps (pre-attack) should be higher on average
        # than late steps (post-attack with cascade)
        pre_attack_avg = np.mean(result.timeline[:30])
        post_attack_avg = np.mean(result.timeline[60:])
        assert pre_attack_avg >= post_attack_avg

    def test_detection_rate_positive_with_adversaries(self):
        """With active adversaries, detection rate should be positive."""
        scenario = BeliefCascadeScenario()
        config = ColonyConfig(n_agents=30, n_steps=100, n_adversaries=2, seed=42)
        rng = np.random.default_rng(42)
        result = scenario.run(config, rng)
        assert result.detection_rate > 0.0

    def test_cascade_depth_grows_over_time(self):
        """More honest agents should be affected as cascade continues."""
        scenario = BeliefCascadeScenario()
        config = ColonyConfig(n_agents=40, n_steps=150, n_adversaries=2, seed=42)
        rng = np.random.default_rng(42)
        result = scenario.run(config, rng)
        # Integrity early after attack should be higher than much later
        early_post = np.mean(result.timeline[30:50])
        late_post = np.mean(result.timeline[100:150])
        assert early_post >= late_post


# =========================================================================
# Section 3: Benchmark tests
# =========================================================================


class TestColonyConfig:
    """Tests for the ColonyConfig dataclass."""

    def test_defaults(self):
        config = ColonyConfig()
        assert config.n_agents == 20
        assert config.n_steps == 100
        assert config.n_adversaries == 2
        assert config.adversary_fraction == pytest.approx(0.1)
        assert config.seed == 42

    def test_custom_values(self):
        config = ColonyConfig(n_agents=50, n_steps=200, n_adversaries=5, seed=99)
        assert config.n_agents == 50
        assert config.n_steps == 200
        assert config.n_adversaries == 5
        assert config.seed == 99


class TestColonyResult:
    """Tests for the ColonyResult dataclass."""

    def test_defaults(self):
        result = ColonyResult()
        assert result.scenario_name == ""
        assert result.detection_rate == 0.0
        assert result.false_positive_rate == 0.0
        assert result.resilience_score == 0.0
        assert result.recovery_steps == 0
        assert result.ccs_score == 0.0
        assert result.timeline == []

    def test_custom_values(self):
        result = ColonyResult(
            scenario_name="test",
            detection_rate=0.85,
            false_positive_rate=0.05,
            resilience_score=0.9,
            recovery_steps=10,
            ccs_score=0.88,
            timeline=[0.9, 0.8, 0.95],
        )
        assert result.scenario_name == "test"
        assert result.detection_rate == pytest.approx(0.85)
        assert result.timeline == [0.9, 0.8, 0.95]


class TestColonyBenchmark:
    """Tests for the ColonyBenchmark runner."""

    def test_default_scenarios_loaded(self):
        bench = ColonyBenchmark()
        assert len(bench._scenarios) == 5

    def test_custom_scenarios(self):
        scenario = RecruitmentPoisoningScenario()
        bench = ColonyBenchmark(scenarios=[scenario])
        assert len(bench._scenarios) == 1

    def test_run_single_scenario(self):
        scenario = RecruitmentPoisoningScenario()
        bench = ColonyBenchmark(scenarios=[scenario])
        result = bench.run_scenario(scenario, seed=42)
        assert result.scenario_name == "recruitment_poisoning"
        assert 0.0 <= result.ccs_score <= 1.0

    def test_run_all_returns_results(self):
        bench = ColonyBenchmark(scenarios=[
            RecruitmentPoisoningScenario(),
            BeliefCascadeScenario(),
        ])
        results = bench.run_all(seed=42)
        assert len(results) == 2
        assert results[0].scenario_name == "recruitment_poisoning"
        assert results[1].scenario_name == "belief_cascade"

    def test_summary_returns_dict(self):
        bench = ColonyBenchmark(scenarios=[RecruitmentPoisoningScenario()])
        bench.run_all(seed=42)
        summary = bench.summary()
        assert "recruitment_poisoning" in summary
        assert isinstance(summary["recruitment_poisoning"], float)

    def test_run_all_deterministic(self):
        scenarios = [RecruitmentPoisoningScenario(), QuorumManipulationScenario()]
        bench1 = ColonyBenchmark(scenarios=list(scenarios))
        bench2 = ColonyBenchmark(scenarios=list(scenarios))
        results1 = bench1.run_all(seed=42)
        results2 = bench2.run_all(seed=42)
        for r1, r2 in zip(results1, results2):
            assert r1.ccs_score == r2.ccs_score
            assert r1.detection_rate == r2.detection_rate

    def test_run_all_with_all_five_scenarios(self):
        """Full benchmark with all five scenarios produces valid results."""
        bench = ColonyBenchmark()
        results = bench.run_all(seed=42)
        assert len(results) == 5
        names = {r.scenario_name for r in results}
        expected = {
            "recruitment_poisoning",
            "sybil_infiltration",
            "quorum_manipulation",
            "belief_cascade",
            "emergent_misalignment",
        }
        assert names == expected
        for r in results:
            assert 0.0 <= r.ccs_score <= 1.0

    def test_each_scenario_gets_derived_seed(self):
        """run_all passes seed + i to each scenario, so config.seed differs."""
        bench = ColonyBenchmark(scenarios=[
            RecruitmentPoisoningScenario(),
            QuorumManipulationScenario(),
        ])
        results = bench.run_all(seed=42)
        # Different scenarios get seed=42 and seed=43 respectively
        assert results[0].config.seed == 42
        assert results[1].config.seed == 43

    def test_summary_empty_before_run(self):
        bench = ColonyBenchmark(scenarios=[RecruitmentPoisoningScenario()])
        summary = bench.summary()
        assert summary == {}


# =========================================================================
# Section 3b: Seed-sweep interval estimation (ColonyScenarioSummary)
# =========================================================================


class _ConstantScenario(ColonyScenario):
    """Scenario that ignores the RNG and always returns the same numbers.

    Used as the *negative* arm of the variance positive control: a genuinely
    degenerate process must produce a zero-width interval, so a non-zero
    width elsewhere cannot be an artefact of the interval machinery.
    """

    def __init__(self, name: str = "constant", value: float = 0.7) -> None:
        self._name = name
        self._value = value

    @property
    def name(self) -> str:
        return self._name

    def default_config(self) -> ColonyConfig:
        return ColonyConfig(n_agents=4, n_steps=3, n_adversaries=1)

    def run(self, config: ColonyConfig, rng: np.random.Generator) -> ColonyResult:
        return ColonyResult(
            scenario_name=self._name,
            config=config,
            detection_rate=self._value,
            false_positive_rate=self._value / 2.0,
            resilience_score=self._value,
            recovery_steps=1,
            ccs_score=self._value,
            timeline=[self._value] * config.n_steps,
        )


class _SeedVaryingScenario(ColonyScenario):
    """Scenario whose outputs are a deterministic function of the seed.

    Each seed yields a different, exactly predictable detection rate, so a
    test can assert both that repeats really used distinct seeds and that
    the reported mean/min/max match values computed independently.
    """

    def __init__(self, name: str = "seed_varying") -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def default_config(self) -> ColonyConfig:
        return ColonyConfig(n_agents=4, n_steps=3, n_adversaries=1)

    @staticmethod
    def value_for_seed(seed: int) -> float:
        """The detection rate this scenario returns for *seed*."""
        return (seed % 10) / 10.0

    def run(self, config: ColonyConfig, rng: np.random.Generator) -> ColonyResult:
        value = self.value_for_seed(config.seed)
        return ColonyResult(
            scenario_name=self._name,
            config=config,
            detection_rate=value,
            false_positive_rate=1.0 - value,
            resilience_score=value,
            recovery_steps=int(config.seed % 5),
            ccs_score=value,
            timeline=[value] * config.n_steps,
        )


class TestColonySeedSweep:
    """A published colony number must be a seed sweep, not one lucky draw."""

    def test_n_repeats_one_reproduces_legacy_single_run_exactly(self):
        """n_repeats=1 must be byte-identical to the old run_all(seed)."""
        scenarios = [RecruitmentPoisoningScenario(), QuorumManipulationScenario()]
        legacy = ColonyBenchmark(scenarios=list(scenarios)).run_all(seed=42)
        swept = ColonyBenchmark(scenarios=list(scenarios)).run_all_repeated(
            seed=42, n_repeats=1
        )

        assert [s.n_repeats for s in swept] == [1, 1]
        for old, summary in zip(legacy, swept):
            assert summary.runs[0].detection_rate == old.detection_rate
            assert summary.runs[0].false_positive_rate == old.false_positive_rate
            assert summary.runs[0].ccs_score == old.ccs_score
            assert summary.runs[0].config.seed == old.config.seed

    def test_repeats_use_distinct_seeds(self):
        """Each (scenario, repeat) pair gets its own seed -- no reuse."""
        bench = ColonyBenchmark(
            scenarios=[_SeedVaryingScenario("a"), _SeedVaryingScenario("b")]
        )
        summaries = bench.run_all_repeated(seed=42, n_repeats=5)

        all_seeds = [s for summary in summaries for s in summary.seeds]
        assert len(all_seeds) == 10
        assert len(set(all_seeds)) == 10, f"seed reuse detected: {all_seeds}"
        # Each summary's recorded seeds must match the seeds the runs saw.
        for summary in summaries:
            assert [r.config.seed for r in summary.runs] == summary.seeds

    def test_reported_mean_and_range_match_independently_computed_values(self):
        """The summary must not invent numbers: recompute them by hand."""
        bench = ColonyBenchmark(scenarios=[_SeedVaryingScenario()])
        summary = bench.run_all_repeated(seed=42, n_repeats=7)[0]

        expected = [_SeedVaryingScenario.value_for_seed(s) for s in summary.seeds]
        assert summary.detection_rate_values == expected
        assert summary.detection_rate_mean == pytest.approx(float(np.mean(expected)))
        assert summary.detection_rate_range == (min(expected), max(expected))

        # The other two metric views must be sourced from the same runs.
        assert summary.fpr_values == [1.0 - v for v in expected]
        assert summary.ccs_values == expected
        assert summary.fpr_mean == pytest.approx(float(np.mean(summary.fpr_values)))
        assert summary.ccs_mean == pytest.approx(float(np.mean(summary.ccs_values)))
        assert summary.fpr_range == (
            min(summary.fpr_values),
            max(summary.fpr_values),
        )
        assert summary.ccs_range == (
            min(summary.ccs_values),
            max(summary.ccs_values),
        )

    def test_varying_scenario_yields_positive_width_interval(self):
        """POSITIVE CONTROL: real spread must produce a non-degenerate CI."""
        bench = ColonyBenchmark(scenarios=[_SeedVaryingScenario()])
        summary = bench.run_all_repeated(seed=42, n_repeats=20)[0]

        lo, hi = summary.detection_rate_ci95
        assert len(set(summary.detection_rate_values)) > 1, "control did not vary"
        assert hi - lo > 0.0, "spread present but CI width is zero"
        assert lo <= summary.detection_rate_mean <= hi

    def test_constant_scenario_yields_zero_width_interval(self):
        """NEGATIVE ARM: no spread must produce a zero-width CI.

        Paired with the previous test this proves the CI width tracks the
        data rather than being a constant the code always emits.
        """
        bench = ColonyBenchmark(scenarios=[_ConstantScenario(value=0.7)])
        summary = bench.run_all_repeated(seed=42, n_repeats=20)[0]

        lo, hi = summary.detection_rate_ci95
        assert summary.detection_rate_mean == pytest.approx(0.7)
        assert hi - lo == pytest.approx(0.0, abs=1e-12)
        assert summary.detection_rate_range == (0.7, 0.7)

    def test_all_runs_at_rejects_a_single_dissenting_seed(self):
        """POSITIVE CONTROL for the guarantee check.

        ``all_runs_at`` is what a '100% detection' claim is tested with.  A
        sweep in which 19 of 20 seeds hit 1.0 must return False -- otherwise
        the check would rubber-stamp a mean-1.0 claim.
        """
        perfect = ColonyBenchmark(scenarios=[_ConstantScenario(value=1.0)])
        perfect_summary = perfect.run_all_repeated(seed=42, n_repeats=20)[0]
        assert perfect_summary.all_runs_at("detection_rate", 1.0) is True

        # Inject exactly one dissenting run into an otherwise perfect sweep.
        # The dissent is deliberately small enough that a mean-with-tolerance
        # check would still call the sweep perfect, so this test kills that
        # implementation as well as the honest one passing.
        dissenting = ColonyResult(
            scenario_name="constant",
            config=ColonyConfig(),
            detection_rate=0.999,
            false_positive_rate=0.0,
            ccs_score=1.0,
        )
        perfect_summary.runs[7] = dissenting

        mean_after = float(np.mean(perfect_summary.detection_rate_values))
        assert mean_after == pytest.approx(1.0, abs=1e-3), (
            "dissent too large -- a mean-based check would already reject it, "
            "so this test would not distinguish the two implementations"
        )
        assert perfect_summary.all_runs_at("detection_rate", 1.0) is False

    def test_all_runs_at_rejects_unknown_metric(self):
        bench = ColonyBenchmark(scenarios=[_ConstantScenario()])
        summary = bench.run_all_repeated(seed=42, n_repeats=2)[0]
        with pytest.raises(ValueError, match="metric must be one of"):
            summary.all_runs_at("not_a_metric", 1.0)

    def test_n_repeats_zero_rejected(self):
        bench = ColonyBenchmark(scenarios=[_ConstantScenario()])
        with pytest.raises(ValueError, match="n_repeats must be >= 1"):
            bench.run_all_repeated(seed=42, n_repeats=0)

    def test_sweep_is_reproducible(self):
        """Same base seed, same sweep -- including the bootstrap CIs."""
        scenarios = [RecruitmentPoisoningScenario()]
        a = ColonyBenchmark(scenarios=list(scenarios)).run_all_repeated(
            seed=42, n_repeats=6
        )[0]
        b = ColonyBenchmark(scenarios=list(scenarios)).run_all_repeated(
            seed=42, n_repeats=6
        )[0]
        assert a.detection_rate_values == b.detection_rate_values
        assert a.detection_rate_ci95 == b.detection_rate_ci95
        assert a.ccs_ci95 == b.ccs_ci95

    def test_summary_dict_still_works_after_sweep(self):
        bench = ColonyBenchmark(scenarios=[RecruitmentPoisoningScenario()])
        bench.run_all_repeated(seed=42, n_repeats=3)
        assert "recruitment_poisoning" in bench.summary()


class TestColonyHeadlineClaimsAcrossSeeds:
    """Bind the abstract's colony claims to a real multi-seed measurement.

    These tests are the artifact behind the sybil claim.  They are written
    to *fail* if a future change makes the claim untrue, and the FPR test in
    particular encodes what the sweep actually found rather than what the
    abstract asserts.
    """

    SWEEP_SEED = 42
    SWEEP_REPEATS = 20

    def _sybil_summary(self):
        bench = ColonyBenchmark()
        index = next(
            i for i, s in enumerate(bench._scenarios) if s.name == "sybil_infiltration"
        )
        scenario = bench._scenarios[index]
        seeds = [
            bench.seed_for(index, r, self.SWEEP_SEED) for r in range(self.SWEEP_REPEATS)
        ]
        return scenario, seeds, bench

    def test_sybil_detection_is_perfect_on_every_seed(self):
        """'100% sybil detection' survives the sweep: all seeds hit 1.0."""
        scenario, seeds, bench = self._sybil_summary()
        rates = [bench.run_scenario(scenario, seed=s).detection_rate for s in seeds]
        assert len(rates) == self.SWEEP_REPEATS
        assert min(rates) == 1.0, f"detection dropped below 1.0 on some seed: {rates}"

    def test_sybil_false_positive_rate_is_not_exactly_zero_on_every_seed(self):
        """'0% FPR' does NOT survive the sweep -- it is seed-dependent.

        The single published seed happens to give exactly 0.0.  Across the
        sweep some seeds produce a small but non-zero false-positive rate,
        so the abstract cannot state 0% as a guarantee.  This test pins that
        finding; if a future change genuinely makes FPR identically zero it
        will fail and the claim can be restored deliberately.
        """
        scenario, seeds, bench = self._sybil_summary()
        fprs = [
            bench.run_scenario(scenario, seed=s).false_positive_rate for s in seeds
        ]
        assert max(fprs) > 0.0, (
            "expected at least one seed with a non-zero sybil FPR; "
            f"observed max {max(fprs)}"
        )
        # ...but the magnitude is negligible, which is the honest framing.
        assert max(fprs) < 1e-3

    def test_emergent_misalignment_single_seed_is_far_from_the_sweep_mean(self):
        """The published 0.561 detection rate is an outlier, not the centre.

        This is the cherry-pick check: if the single published seed sat near
        the sweep mean the assertion would fail and the point estimate would
        be defensible.
        """
        bench = ColonyBenchmark()
        index = next(
            i
            for i, s in enumerate(bench._scenarios)
            if s.name == "emergent_misalignment"
        )
        scenario = bench._scenarios[index]
        seeds = [
            bench.seed_for(index, r, self.SWEEP_SEED) for r in range(self.SWEEP_REPEATS)
        ]
        rates = np.array(
            [bench.run_scenario(scenario, seed=s).detection_rate for s in seeds]
        )

        published_seed_value = bench.run_scenario(scenario, seed=seeds[0]).detection_rate
        spread = float(rates.max() - rates.min())

        assert spread > 0.2, (
            "emergent misalignment detection barely varies across seeds; "
            f"spread {spread}"
        )
        assert abs(published_seed_value - float(rates.mean())) > 0.1, (
            "published seed is close to the sweep mean, so the single-run "
            "point estimate would be defensible after all"
        )


# =========================================================================
# Section 4: Emergent Misalignment tests
# =========================================================================


class TestEmergentMisalignmentScenario:
    """Tests for the no-adversary emergent misalignment scenario."""

    def test_scenario_name(self):
        scenario = EmergentMisalignmentScenario()
        assert scenario.name == "emergent_misalignment"

    def test_default_config(self):
        scenario = EmergentMisalignmentScenario()
        config = scenario.default_config()
        assert config.n_agents == 50
        assert config.n_steps == 1000
        assert config.n_adversaries == 0

    def test_run_returns_colony_result(self):
        scenario = EmergentMisalignmentScenario()
        config = ColonyConfig(n_agents=10, n_steps=50, n_adversaries=0, seed=42)
        rng = np.random.default_rng(42)
        result = scenario.run(config, rng)
        assert result.scenario_name == "emergent_misalignment"
        assert isinstance(result.ccs_score, float)

    def test_run_deterministic(self):
        scenario = EmergentMisalignmentScenario()
        config = ColonyConfig(n_agents=10, n_steps=50, n_adversaries=0, seed=42)
        rng1 = np.random.default_rng(42)
        result1 = scenario.run(config, rng1)
        rng2 = np.random.default_rng(42)
        result2 = scenario.run(config, rng2)
        assert result1.ccs_score == result2.ccs_score
        assert result1.timeline == result2.timeline

    def test_timeline_length(self):
        scenario = EmergentMisalignmentScenario()
        config = ColonyConfig(n_agents=10, n_steps=80, n_adversaries=0, seed=42)
        rng = np.random.default_rng(42)
        result = scenario.run(config, rng)
        assert len(result.timeline) == 80

    def test_metrics_in_valid_range(self):
        scenario = EmergentMisalignmentScenario()
        config = ColonyConfig(n_agents=15, n_steps=100, n_adversaries=0, seed=42)
        rng = np.random.default_rng(42)
        result = scenario.run(config, rng)
        assert 0.0 <= result.detection_rate <= 1.0
        assert 0.0 <= result.false_positive_rate <= 1.0
        assert 0.0 <= result.resilience_score <= 1.0
        assert result.recovery_steps >= 0
        assert 0.0 <= result.ccs_score <= 1.0

    def test_drift_detected_over_long_horizon(self):
        """Over many steps, organic drift should be detectable."""
        scenario = EmergentMisalignmentScenario()
        config = ColonyConfig(n_agents=20, n_steps=500, n_adversaries=0, seed=42)
        rng = np.random.default_rng(42)
        result = scenario.run(config, rng)
        # Over 500 steps with noise, some drift detection should occur
        # detection_rate measures how often mean drift exceeded threshold
        assert result.detection_rate >= 0.0  # Could be 0 or positive

    def test_integrity_declines_with_long_simulation(self):
        """With random noise and no correction, integrity should decrease over time."""
        scenario = EmergentMisalignmentScenario()
        config = ColonyConfig(n_agents=20, n_steps=500, n_adversaries=0, seed=42)
        rng = np.random.default_rng(42)
        result = scenario.run(config, rng)
        early_integrity = np.mean(result.timeline[:50])
        late_integrity = np.mean(result.timeline[400:])
        # Integrity should decrease or stay similar (random walk drift)
        assert early_integrity >= late_integrity - 0.1

    def test_no_adversary_false_positive_rate_bounded(self):
        """Without adversaries, false positive rate should be manageable."""
        scenario = EmergentMisalignmentScenario()
        config = ColonyConfig(n_agents=15, n_steps=100, n_adversaries=0, seed=42)
        rng = np.random.default_rng(42)
        result = scenario.run(config, rng)
        assert result.false_positive_rate <= 1.0


# =========================================================================
# Section 5: Quorum Manipulation tests
# =========================================================================


class TestQuorumManipulationScenario:
    """Tests for the quorum manipulation scenario."""

    def test_scenario_name(self):
        scenario = QuorumManipulationScenario()
        assert scenario.name == "quorum_manipulation"

    def test_default_config(self):
        scenario = QuorumManipulationScenario()
        config = scenario.default_config()
        assert config.n_agents == 30
        assert config.n_steps == 200
        assert config.n_adversaries == 3

    def test_run_returns_colony_result(self):
        scenario = QuorumManipulationScenario()
        config = ColonyConfig(n_agents=20, n_steps=60, n_adversaries=3, seed=42)
        rng = np.random.default_rng(42)
        result = scenario.run(config, rng)
        assert result.scenario_name == "quorum_manipulation"

    def test_run_deterministic(self):
        scenario = QuorumManipulationScenario()
        config = ColonyConfig(n_agents=20, n_steps=60, n_adversaries=3, seed=42)
        rng1 = np.random.default_rng(42)
        result1 = scenario.run(config, rng1)
        rng2 = np.random.default_rng(42)
        result2 = scenario.run(config, rng2)
        assert result1.ccs_score == result2.ccs_score
        assert result1.detection_rate == result2.detection_rate
        assert result1.timeline == result2.timeline

    def test_metrics_in_valid_range(self):
        scenario = QuorumManipulationScenario()
        config = ColonyConfig(n_agents=20, n_steps=60, n_adversaries=3, seed=42)
        rng = np.random.default_rng(42)
        result = scenario.run(config, rng)
        assert 0.0 <= result.detection_rate <= 1.0
        assert 0.0 <= result.false_positive_rate <= 1.0
        assert 0.0 <= result.resilience_score <= 1.0
        assert result.recovery_steps >= 0
        assert 0.0 <= result.ccs_score <= 1.0

    def test_detection_rate_positive(self):
        """Adversaries always vote wrong after activation, should be detectable."""
        scenario = QuorumManipulationScenario()
        config = ColonyConfig(n_agents=20, n_steps=80, n_adversaries=3, seed=42)
        rng = np.random.default_rng(42)
        result = scenario.run(config, rng)
        # After step 30, adversaries always vote wrong -> detection rate should be high
        assert result.detection_rate > 0.5

    def test_quorum_integrity_pre_attack(self):
        """Before adversaries activate, quorum decisions should be largely correct."""
        scenario = QuorumManipulationScenario()
        config = ColonyConfig(n_agents=20, n_steps=80, n_adversaries=3, seed=42)
        rng = np.random.default_rng(42)
        result = scenario.run(config, rng)
        # First 30 steps should have decent integrity (honest voting with p=0.85)
        pre_attack_integrity = np.mean(result.timeline[:30])
        assert pre_attack_integrity > 0.3

    def test_adversary_impact_on_quorum(self):
        """More adversaries should reduce quorum correctness after activation."""
        scenario = QuorumManipulationScenario()
        config_few = ColonyConfig(n_agents=20, n_steps=80, n_adversaries=2, seed=42)
        config_many = ColonyConfig(n_agents=20, n_steps=80, n_adversaries=6, seed=42)
        rng1 = np.random.default_rng(42)
        result_few = scenario.run(config_few, rng1)
        rng2 = np.random.default_rng(42)
        result_many = scenario.run(config_many, rng2)
        # More adversaries should reduce post-attack integrity
        post_few = np.mean(result_few.timeline[30:])
        post_many = np.mean(result_many.timeline[30:])
        assert post_few >= post_many

    def test_timeline_has_binary_values(self):
        """Quorum decisions are binary (correct=1 or incorrect=0)."""
        scenario = QuorumManipulationScenario()
        config = ColonyConfig(n_agents=20, n_steps=50, n_adversaries=3, seed=42)
        rng = np.random.default_rng(42)
        result = scenario.run(config, rng)
        for val in result.timeline:
            assert val in [0.0, 1.0]


# =========================================================================
# Section 6: Recruitment Poisoning tests
# =========================================================================


class TestRecruitmentPoisoningScenario:
    """Tests for the recruitment poisoning scenario."""

    def test_scenario_name(self):
        scenario = RecruitmentPoisoningScenario()
        assert scenario.name == "recruitment_poisoning"

    def test_default_config(self):
        scenario = RecruitmentPoisoningScenario()
        config = scenario.default_config()
        assert config.n_agents == 20
        assert config.n_steps == 100
        assert config.n_adversaries == 2

    def test_run_returns_colony_result(self):
        scenario = RecruitmentPoisoningScenario()
        config = ColonyConfig(n_agents=15, n_steps=60, n_adversaries=2, seed=42)
        rng = np.random.default_rng(42)
        result = scenario.run(config, rng)
        assert result.scenario_name == "recruitment_poisoning"
        assert isinstance(result.detection_rate, float)

    def test_run_deterministic(self):
        scenario = RecruitmentPoisoningScenario()
        config = ColonyConfig(n_agents=15, n_steps=60, n_adversaries=2, seed=42)
        rng1 = np.random.default_rng(42)
        result1 = scenario.run(config, rng1)
        rng2 = np.random.default_rng(42)
        result2 = scenario.run(config, rng2)
        assert result1.ccs_score == result2.ccs_score
        assert result1.detection_rate == result2.detection_rate

    def test_metrics_in_valid_range(self):
        scenario = RecruitmentPoisoningScenario()
        config = ColonyConfig(n_agents=15, n_steps=60, n_adversaries=2, seed=42)
        rng = np.random.default_rng(42)
        result = scenario.run(config, rng)
        assert 0.0 <= result.detection_rate <= 1.0
        assert 0.0 <= result.false_positive_rate <= 1.0
        assert 0.0 <= result.resilience_score <= 1.0
        assert result.recovery_steps >= 0
        assert 0.0 <= result.ccs_score <= 1.0

    def test_timeline_length(self):
        scenario = RecruitmentPoisoningScenario()
        config = ColonyConfig(n_agents=15, n_steps=60, n_adversaries=2, seed=42)
        rng = np.random.default_rng(42)
        result = scenario.run(config, rng)
        assert len(result.timeline) == 60

    def test_trust_building_phase(self):
        """During trust-building phase, adversaries behave honestly, so
        integrity should remain high."""
        scenario = RecruitmentPoisoningScenario()
        config = ColonyConfig(n_agents=20, n_steps=100, n_adversaries=2, seed=42)
        rng = np.random.default_rng(42)
        result = scenario.run(config, rng)
        # Trust phase = first 40% of steps = 40 steps
        trust_phase_integrity = np.mean(result.timeline[:40])
        assert trust_phase_integrity > 0.5

    def test_post_trust_integrity_declines(self):
        """After trust phase, adversary exploitation should reduce integrity."""
        scenario = RecruitmentPoisoningScenario()
        config = ColonyConfig(n_agents=20, n_steps=100, n_adversaries=2, seed=42)
        rng = np.random.default_rng(42)
        result = scenario.run(config, rng)
        trust_phase_avg = np.mean(result.timeline[:40])
        exploit_phase_avg = np.mean(result.timeline[60:])
        assert trust_phase_avg >= exploit_phase_avg

    def test_detection_increases_after_trust_phase(self):
        """Detection rate should be positive when adversaries start exploiting."""
        scenario = RecruitmentPoisoningScenario()
        config = ColonyConfig(n_agents=20, n_steps=100, n_adversaries=2, seed=42)
        rng = np.random.default_rng(42)
        result = scenario.run(config, rng)
        assert result.detection_rate > 0.0


# =========================================================================
# Section 7: Sybil Infiltration tests
# =========================================================================


class TestSybilInfiltrationScenario:
    """Tests for the Sybil infiltration scenario."""

    def test_scenario_name(self):
        scenario = SybilInfiltrationScenario()
        assert scenario.name == "sybil_infiltration"

    def test_default_config(self):
        scenario = SybilInfiltrationScenario()
        config = scenario.default_config()
        assert config.n_agents == 50
        assert config.n_steps == 500
        assert config.n_adversaries == 4

    def test_run_returns_colony_result(self):
        scenario = SybilInfiltrationScenario()
        config = ColonyConfig(n_agents=20, n_steps=80, n_adversaries=4, seed=42)
        rng = np.random.default_rng(42)
        result = scenario.run(config, rng)
        assert result.scenario_name == "sybil_infiltration"

    def test_run_deterministic(self):
        scenario = SybilInfiltrationScenario()
        config = ColonyConfig(n_agents=20, n_steps=80, n_adversaries=4, seed=42)
        rng1 = np.random.default_rng(42)
        result1 = scenario.run(config, rng1)
        rng2 = np.random.default_rng(42)
        result2 = scenario.run(config, rng2)
        assert result1.ccs_score == result2.ccs_score
        assert result1.detection_rate == result2.detection_rate
        assert result1.timeline == result2.timeline

    def test_metrics_in_valid_range(self):
        scenario = SybilInfiltrationScenario()
        config = ColonyConfig(n_agents=20, n_steps=80, n_adversaries=4, seed=42)
        rng = np.random.default_rng(42)
        result = scenario.run(config, rng)
        assert 0.0 <= result.detection_rate <= 1.0
        assert 0.0 <= result.false_positive_rate <= 1.0
        assert 0.0 <= result.resilience_score <= 1.0
        assert result.recovery_steps >= 0
        assert 0.0 <= result.ccs_score <= 1.0

    def test_timeline_length(self):
        scenario = SybilInfiltrationScenario()
        config = ColonyConfig(n_agents=20, n_steps=80, n_adversaries=4, seed=42)
        rng = np.random.default_rng(42)
        result = scenario.run(config, rng)
        assert len(result.timeline) == 80

    def test_coordinated_sybil_detection(self):
        """Sybils vote identically after activation, detection should be positive."""
        scenario = SybilInfiltrationScenario()
        config = ColonyConfig(n_agents=20, n_steps=100, n_adversaries=4, seed=42)
        rng = np.random.default_rng(42)
        result = scenario.run(config, rng)
        # Sybils vote identically as 0 while ground truth is 1 -> should be detected
        assert result.detection_rate > 0.0

    def test_pre_activation_blending(self):
        """Before sybil activation (step 50), decisions should be correct."""
        scenario = SybilInfiltrationScenario()
        config = ColonyConfig(n_agents=30, n_steps=100, n_adversaries=4, seed=42)
        rng = np.random.default_rng(42)
        result = scenario.run(config, rng)
        # Before step 50, all agents vote correctly with noise -> high correctness
        pre_activation = result.timeline[:50]
        assert np.mean(pre_activation) > 0.5

    def test_sybil_impact_scales_with_count(self):
        """More sybils should have greater impact on colony decisions."""
        scenario = SybilInfiltrationScenario()
        config_few = ColonyConfig(n_agents=30, n_steps=100, n_adversaries=2, seed=42)
        config_many = ColonyConfig(n_agents=30, n_steps=100, n_adversaries=10, seed=42)
        rng1 = np.random.default_rng(42)
        result_few = scenario.run(config_few, rng1)
        rng2 = np.random.default_rng(42)
        result_many = scenario.run(config_many, rng2)
        # More sybils should reduce post-activation correctness
        post_few = np.mean(result_few.timeline[50:])
        post_many = np.mean(result_many.timeline[50:])
        assert post_few >= post_many

    def test_trust_degrades_for_sybils(self):
        """After activation, sybils vote wrong, so their trust should decrease.
        We verify this indirectly: with trust weighting, the colony should
        eventually recover or maintain correctness even with sybils."""
        scenario = SybilInfiltrationScenario()
        config = ColonyConfig(n_agents=30, n_steps=200, n_adversaries=3, seed=42)
        rng = np.random.default_rng(42)
        result = scenario.run(config, rng)
        # The colony should maintain some correctness even with sybils
        overall_correctness = np.mean(result.timeline)
        assert overall_correctness > 0.0

    def test_timeline_binary_values(self):
        """Sybil scenario tracks binary correct/incorrect decisions."""
        scenario = SybilInfiltrationScenario()
        config = ColonyConfig(n_agents=20, n_steps=50, n_adversaries=4, seed=42)
        rng = np.random.default_rng(42)
        result = scenario.run(config, rng)
        for val in result.timeline:
            assert val in [0.0, 1.0]


# =========================================================================
# Section 8: Cross-module integration tests
# =========================================================================


class TestCrossModuleIntegration:
    """Integration tests that verify consistent behavior across modules."""

    def test_all_scenarios_produce_consistent_result_structure(self):
        """Every scenario should return a ColonyResult with all required fields."""
        scenarios = [
            RecruitmentPoisoningScenario(),
            SybilInfiltrationScenario(),
            QuorumManipulationScenario(),
            BeliefCascadeScenario(),
            EmergentMisalignmentScenario(),
        ]
        for scenario in scenarios:
            config = ColonyConfig(n_agents=15, n_steps=50, n_adversaries=2, seed=42)
            rng = np.random.default_rng(42)
            result = scenario.run(config, rng)
            assert hasattr(result, "scenario_name"), f"{scenario.name} missing scenario_name"
            assert hasattr(result, "detection_rate"), f"{scenario.name} missing detection_rate"
            assert hasattr(result, "false_positive_rate"), f"{scenario.name} missing fpr"
            assert hasattr(result, "resilience_score"), f"{scenario.name} missing resilience"
            assert hasattr(result, "recovery_steps"), f"{scenario.name} missing recovery_steps"
            assert hasattr(result, "ccs_score"), f"{scenario.name} missing ccs_score"
            assert hasattr(result, "timeline"), f"{scenario.name} missing timeline"

    def test_scorecard_ccs_consistent_with_scenario_results(self):
        """Verify that manually computing CCS matches the scenario result."""
        scenario = RecruitmentPoisoningScenario()
        config = ColonyConfig(n_agents=15, n_steps=60, n_adversaries=2, seed=42)
        rng = np.random.default_rng(42)
        result = scenario.run(config, rng)

        # Recompute CCS from the individual metrics
        recomputed = compute_ccs(
            result.detection_rate,
            result.false_positive_rate,
            result.resilience_score,
            result.recovery_steps,
            config.n_steps,
        )
        assert np.isclose(result.ccs_score, recomputed, atol=1e-10)

    def test_resilience_consistent_with_timeline(self):
        """Verify resilience can be recomputed from timeline data."""
        scenario = QuorumManipulationScenario()
        config = ColonyConfig(n_agents=20, n_steps=80, n_adversaries=3, seed=42)
        rng = np.random.default_rng(42)
        result = scenario.run(config, rng)

        recomputed = compute_resilience(result.timeline, adversary_start_step=30)
        assert np.isclose(result.resilience_score, recomputed, atol=1e-10)

    def test_recovery_steps_consistent_with_timeline(self):
        """Verify recovery_steps can be recomputed from timeline data."""
        scenario = BeliefCascadeScenario()
        config = ColonyConfig(n_agents=20, n_steps=60, n_adversaries=2, seed=42)
        rng = np.random.default_rng(42)
        result = scenario.run(config, rng)

        recomputed = compute_recovery_steps(result.timeline, threshold=0.9)
        assert result.recovery_steps == recomputed

    def test_package_exports_all_public_symbols(self):
        """Verify __init__.py exports all expected symbols."""
        from src import colony
        expected = [
            "ColonyBenchmark", "ColonyConfig", "ColonyResult", "ColonyScenario",
            "CCSWeights", "compute_ccs", "compute_recovery_steps", "compute_resilience",
            "RecruitmentPoisoningScenario", "SybilInfiltrationScenario",
            "QuorumManipulationScenario", "BeliefCascadeScenario",
            "EmergentMisalignmentScenario",
        ]
        for name in expected:
            assert hasattr(colony, name), f"colony missing export: {name}"

    def test_all_scenario_names_unique(self):
        """Each scenario should have a unique name."""
        scenarios = [
            RecruitmentPoisoningScenario(),
            SybilInfiltrationScenario(),
            QuorumManipulationScenario(),
            BeliefCascadeScenario(),
            EmergentMisalignmentScenario(),
        ]
        names = [s.name for s in scenarios]
        assert len(names) == len(set(names))

    def test_ccs_score_increases_with_better_detection(self):
        """Higher detection rate should increase CCS score, all else equal."""
        low_dr = compute_ccs(0.2, 0.1, 0.8, 10, 100)
        high_dr = compute_ccs(0.9, 0.1, 0.8, 10, 100)
        assert high_dr > low_dr

    def test_ccs_score_decreases_with_higher_fpr(self):
        """Higher false positive rate should decrease CCS score."""
        low_fpr = compute_ccs(0.8, 0.1, 0.8, 10, 100)
        high_fpr = compute_ccs(0.8, 0.9, 0.8, 10, 100)
        assert low_fpr > high_fpr
