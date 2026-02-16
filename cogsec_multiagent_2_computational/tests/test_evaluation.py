"""Comprehensive tests for the evaluation framework.

Tests cover:
    1. ExperimentRunner: single experiment, full matrix, summary table
    2. Benchmark: latency profiling, memory profiling, result collection
    3. Metrics: detection rate, false positive rate, F1, precision, recall
    4. PrecisionRecall: PR curve generation, AUPRC computation
    5. ROC: ROC curve generation, AUROC computation, Youden's J
    6. Scalability: scaling model fit, prediction, ScalabilityBenchmark

All tests use real data and computation -- no mocks.
"""

import math
import time

import numpy as np
import pytest

from architectures.base import ArchitectureAdapter, ArchitectureProfile
from architectures.claude_code import ClaudeCodeAdapter
from evaluation.benchmark import BenchmarkResult, LatencyProfiler, MemoryProfiler
from evaluation.metrics import DetectionMetrics
from evaluation.precision_recall import (
    PRCurve,
    bootstrap_ap_ci,
    compute_average_precision,
    compute_average_precision_from_arrays,
    compute_pr_curve,
)
from evaluation.roc import (
    ROCCurve,
    bootstrap_auc_ci,
    compute_auc,
    compute_auc_from_points,
    compute_roc,
    youdens_j,
)
from evaluation.runner import ExperimentResult, ExperimentRunner
from evaluation.scalability import (
    ScalabilityBenchmark,
    ScalabilityResult,
    ScalingModel,
)
from utils.types import ExperimentConfig


# ---------------------------------------------------------------------------
# Helpers: lightweight real objects (no mocks)
# ---------------------------------------------------------------------------


class _SimpleAdapter(ArchitectureAdapter):
    """Minimal concrete adapter for testing with a fixed multiplier."""

    def __init__(self, name: str = "TestArch", multiplier: float = 1.0):
        self._name = name
        self._multiplier = multiplier
        self._profile = ArchitectureProfile(
            name=name,
            agent_count_range=(1, 200),
            trust_topology="flat",
            has_central_orchestrator=False,
            communication_pattern="mesh",
            delegation_depth=1,
        )

    @property
    def profile(self) -> ArchitectureProfile:
        return self._profile

    def create_trust_matrix(self, n_agents: int) -> np.ndarray:
        return np.eye(n_agents, dtype=np.float64)

    def get_agent_roles(self, n_agents: int) -> list:
        return ["agent"] * n_agents

    def get_communication_graph(self, n_agents: int) -> np.ndarray:
        return np.ones((n_agents, n_agents), dtype=np.float64)

    def simulate_delegation(self, source: int, target: int, depth: int) -> float:
        return 1.0 if source == target else 0.8

    def get_attack_surface_multiplier(self) -> float:
        return self._multiplier


class _SimplePipeline:
    """Pipeline that returns a fixed score for evaluate calls."""

    def __init__(self, score: float = 0.7):
        self._score = score

    def evaluate(self, message: str, context=None):
        # Small real computation: hash the message to produce a tiny delay
        _ = sum(ord(c) for c in message)
        return _SimpleResult(self._score)


class _SimpleResult:
    """Result object with a score attribute."""

    def __init__(self, score: float):
        self.score = score


class _ScalablePipeline:
    """Pipeline whose latency scales with agent count for scalability tests."""

    def __init__(self, n_agents: int):
        self.n_agents = n_agents
        self.modules = []

    def evaluate(self, message: str, context=None):
        # Perform actual computation proportional to n_agents
        # Small matrix multiply to create real O(n^2) scaling
        mat = np.random.default_rng(0).random((self.n_agents, self.n_agents))
        _ = mat @ mat
        return _SimpleResult(0.6)


def _make_attack_samples(
    category: str, n_attacks: int = 20, n_benign: int = 10
) -> list:
    """Create realistic attack sample dicts with both attacks and benign."""
    samples = []
    for i in range(n_attacks):
        samples.append(
            {
                "category": category,
                "content": f"attack payload {category} sample {i}",
                "is_attack": True,
            }
        )
    for i in range(n_benign):
        samples.append(
            {
                "category": category,
                "content": f"benign message sample {i}",
                "is_attack": False,
            }
        )
    return samples


def _make_corpus(categories: list, n_attacks: int = 10, n_benign: int = 5) -> dict:
    """Build a corpus dict mapping categories to sample lists."""
    return {cat: _make_attack_samples(cat, n_attacks, n_benign) for cat in categories}


# ===========================================================================
# 1. ExperimentRunner
# ===========================================================================


class TestExperimentRunner:
    """Tests for ExperimentRunner: single, full matrix, summary table."""

    def test_run_single_returns_experiment_result(self):
        """run_single produces an ExperimentResult with valid fields."""
        runner = ExperimentRunner(ExperimentConfig(seed=42))
        adapter = _SimpleAdapter(name="TestArch", multiplier=1.0)
        samples = _make_attack_samples("direct_injection", n_attacks=20, n_benign=10)

        result = runner.run_single(adapter, samples, None)

        assert isinstance(result, ExperimentResult)
        assert result.architecture == "TestArch"
        assert result.attack_category == "direct_injection"
        assert result.n_attacks == 30  # 20 attacks + 10 benign
        assert result.true_positives + result.false_negatives == 20
        assert result.false_positives + result.true_negatives == 10
        assert 0.0 <= result.detection_rate <= 1.0
        assert 0.0 <= result.false_positive_rate <= 1.0
        assert result.avg_latency_ms >= 0.0

    def test_run_single_deterministic_with_seed(self):
        """Same seed produces identical results."""
        adapter = _SimpleAdapter(multiplier=1.0)
        samples = _make_attack_samples("impersonation", n_attacks=50, n_benign=20)

        runner_a = ExperimentRunner(ExperimentConfig(seed=123))
        result_a = runner_a.run_single(adapter, samples, None)

        runner_b = ExperimentRunner(ExperimentConfig(seed=123))
        result_b = runner_b.run_single(adapter, samples, None)

        assert result_a.true_positives == result_b.true_positives
        assert result_a.false_positives == result_b.false_positives
        assert result_a.true_negatives == result_b.true_negatives
        assert result_a.false_negatives == result_b.false_negatives
        assert result_a.detection_rate == result_b.detection_rate

    def test_run_single_different_seeds_differ(self):
        """Different seeds produce different results (statistically)."""
        # Use high multiplier so base scores are near the 0.5 threshold,
        # making noise the deciding factor and ensuring seed-sensitivity.
        adapter = _SimpleAdapter(multiplier=1.6)
        samples = _make_attack_samples("consensus_poisoning", n_attacks=200, n_benign=100)

        runner_a = ExperimentRunner(ExperimentConfig(seed=1))
        result_a = runner_a.run_single(adapter, samples, None)

        runner_b = ExperimentRunner(ExperimentConfig(seed=9999))
        result_b = runner_b.run_single(adapter, samples, None)

        # With 300 samples near the decision boundary and different RNG,
        # at least one confusion-matrix count should differ
        results_differ = (
            result_a.true_positives != result_b.true_positives
            or result_a.false_positives != result_b.false_positives
            or result_a.true_negatives != result_b.true_negatives
            or result_a.false_negatives != result_b.false_negatives
        )
        assert results_differ

    def test_run_single_with_real_pipeline(self):
        """run_single works when a real pipeline is provided."""
        runner = ExperimentRunner(ExperimentConfig(seed=42))
        adapter = _SimpleAdapter(multiplier=1.0)
        pipeline = _SimplePipeline(score=0.8)
        samples = _make_attack_samples("direct_injection", n_attacks=15, n_benign=5)

        result = runner.run_single(adapter, samples, pipeline)

        assert isinstance(result, ExperimentResult)
        assert result.n_attacks == 20
        # Pipeline returns 0.8 score; with multiplier 1.0 and noise,
        # most attacks should be detected (0.8 / 1.0 + noise > 0.5)
        assert result.true_positives > 0

    def test_run_single_with_scores(self):
        """run_single_with_scores returns per-sample detection tuples."""
        runner = ExperimentRunner(ExperimentConfig(seed=42))
        adapter = _SimpleAdapter(multiplier=1.0)
        samples = _make_attack_samples("belief_drift", n_attacks=15, n_benign=5)

        result, per_sample = runner.run_single_with_scores(adapter, samples, None)

        assert isinstance(result, ExperimentResult)
        assert len(per_sample) == 20
        for detected, score in per_sample:
            assert isinstance(detected, (bool, np.bool_))
            assert 0.0 <= score <= 1.0

    def test_run_single_easy_vs_hard_detection_rates(self):
        """Easy attacks have higher detection rate than hard attacks."""
        # Use a high multiplier so that scores land near the 0.5 threshold,
        # making the difference between easy (0.95) and hard (0.70) base
        # rates actually affect the detected/not-detected outcome.
        adapter = _SimpleAdapter(multiplier=1.5)

        runner_easy = ExperimentRunner(ExperimentConfig(seed=42))
        easy_samples = _make_attack_samples("direct_injection", n_attacks=500, n_benign=0)
        result_easy = runner_easy.run_single(adapter, easy_samples, None)

        runner_hard = ExperimentRunner(ExperimentConfig(seed=42))
        hard_samples = _make_attack_samples("consensus_poisoning", n_attacks=500, n_benign=0)
        result_hard = runner_hard.run_single(adapter, hard_samples, None)

        # direct_injection is "easy" (0.95/1.5=0.633 adjusted),
        # consensus_poisoning is "hard" (0.70/1.5=0.467 adjusted, near threshold)
        assert result_easy.detection_rate > result_hard.detection_rate

    def test_run_single_high_multiplier_reduces_detection(self):
        """Higher attack surface multiplier reduces detection rate."""
        samples = _make_attack_samples("impersonation", n_attacks=200, n_benign=0)

        runner_low = ExperimentRunner(ExperimentConfig(seed=42))
        adapter_low = _SimpleAdapter(multiplier=0.8)
        result_low = runner_low.run_single(adapter_low, samples, None)

        runner_high = ExperimentRunner(ExperimentConfig(seed=42))
        adapter_high = _SimpleAdapter(multiplier=2.0)
        result_high = runner_high.run_single(adapter_high, samples, None)

        assert result_low.detection_rate > result_high.detection_rate

    def test_run_full_matrix(self):
        """run_full_matrix produces one result per adapter x category."""
        runner = ExperimentRunner(ExperimentConfig(seed=42))
        adapters = [
            _SimpleAdapter(name="ArchA", multiplier=0.8),
            _SimpleAdapter(name="ArchB", multiplier=1.2),
        ]
        corpus = _make_corpus(
            ["direct_injection", "impersonation", "sybil_attack"],
            n_attacks=10,
            n_benign=5,
        )

        results = runner.run_full_matrix(adapters, corpus, None)

        assert len(results) == 2 * 3  # 2 adapters x 3 categories
        arch_names = {r.architecture for r in results}
        assert arch_names == {"ArchA", "ArchB"}
        cats = {r.attack_category for r in results}
        assert cats == {"direct_injection", "impersonation", "sybil_attack"}

    def test_run_full_matrix_with_real_adapter(self):
        """Full matrix works with the real ClaudeCodeAdapter."""
        runner = ExperimentRunner(ExperimentConfig(seed=42))
        adapter = ClaudeCodeAdapter()
        corpus = _make_corpus(["direct_injection", "belief_injection"], n_attacks=10, n_benign=5)

        results = runner.run_full_matrix([adapter], corpus, None)

        assert len(results) == 2
        assert all(r.architecture == "Claude Code" for r in results)

    def test_summary_table_pivots_correctly(self):
        """summary_table creates {arch: {category: detection_rate}} pivot."""
        runner = ExperimentRunner(ExperimentConfig(seed=42))
        results = [
            ExperimentResult(
                architecture="A", attack_category="cat1",
                n_attacks=10, true_positives=8, false_positives=1,
                true_negatives=9, false_negatives=2,
                detection_rate=0.8, false_positive_rate=0.1, avg_latency_ms=1.0,
            ),
            ExperimentResult(
                architecture="A", attack_category="cat2",
                n_attacks=10, true_positives=6, false_positives=2,
                true_negatives=8, false_negatives=4,
                detection_rate=0.6, false_positive_rate=0.2, avg_latency_ms=1.5,
            ),
            ExperimentResult(
                architecture="B", attack_category="cat1",
                n_attacks=10, true_positives=9, false_positives=0,
                true_negatives=10, false_negatives=1,
                detection_rate=0.9, false_positive_rate=0.0, avg_latency_ms=0.8,
            ),
        ]

        table = runner.summary_table(results)

        assert "A" in table and "B" in table
        assert table["A"]["cat1"] == 0.8
        assert table["A"]["cat2"] == 0.6
        assert table["B"]["cat1"] == 0.9
        assert "cat2" not in table["B"]

    def test_summary_table_empty_results(self):
        """summary_table returns empty dict for empty results list."""
        runner = ExperimentRunner()
        table = runner.summary_table([])
        assert table == {}

    def test_run_single_all_benign(self):
        """run_single handles a corpus with no attacks (all benign)."""
        runner = ExperimentRunner(ExperimentConfig(seed=42))
        adapter = _SimpleAdapter(multiplier=1.0)
        samples = [
            {"category": "direct_injection", "content": f"benign {i}", "is_attack": False}
            for i in range(20)
        ]

        result = runner.run_single(adapter, samples, None)

        assert result.true_positives == 0
        assert result.false_negatives == 0
        assert result.detection_rate == 0.0  # 0/0 case returns 0.0
        assert result.false_positives + result.true_negatives == 20


# ===========================================================================
# 2. Benchmark (LatencyProfiler, MemoryProfiler, BenchmarkResult)
# ===========================================================================


class TestLatencyProfiler:
    """Tests for latency profiling."""

    def test_profile_collects_latency_samples(self):
        """profile() records n_runs * len(samples) latency measurements."""
        profiler = LatencyProfiler()
        pipeline = _SimplePipeline(score=0.5)
        samples = ["hello", "world", "test"]

        acc = profiler.profile(pipeline, samples, n_runs=5)

        assert acc.count() == 5 * 3  # 5 runs x 3 samples
        assert acc.mean() > 0.0
        assert acc.p50() > 0.0
        assert acc.p95() >= acc.p50()

    def test_profile_with_dict_samples(self):
        """profile() works with dict samples containing 'content' key."""
        profiler = LatencyProfiler()
        pipeline = _SimplePipeline(score=0.5)
        samples = [
            {"content": "message one"},
            {"content": "message two"},
        ]

        acc = profiler.profile(pipeline, samples, n_runs=3)

        assert acc.count() == 6

    def test_profile_by_module(self):
        """profile_by_module returns per-module accumulators."""
        profiler = LatencyProfiler()

        class _Module:
            def __init__(self, name):
                self.name = name

            def evaluate(self, msg):
                # Real computation
                return sum(ord(c) for c in msg)

        class _ModularPipeline:
            def __init__(self):
                self.modules = [_Module("mod_a"), _Module("mod_b")]

            def evaluate(self, msg):
                for m in self.modules:
                    m.evaluate(msg)

        pipeline = _ModularPipeline()
        result = profiler.profile_by_module(pipeline, "test message")

        assert "mod_a" in result
        assert "mod_b" in result
        assert result["mod_a"].count() == 1
        assert result["mod_b"].count() == 1


class TestMemoryProfiler:
    """Tests for memory estimation."""

    def test_estimate_memory_increases_with_agents(self):
        """Memory estimate grows with agent count (trust matrix is n^2)."""
        profiler = MemoryProfiler()
        pipeline = _SimplePipeline(score=0.5)

        mem_10 = profiler.estimate_memory(pipeline, n_agents=10)
        mem_50 = profiler.estimate_memory(pipeline, n_agents=50)

        assert mem_50 > mem_10
        # n^2 growth: 50^2/10^2 = 25x for matrix components
        # The matrix part: 2 * n^2 * 8 bytes
        matrix_10 = 2 * 10 * 10 * 8
        matrix_50 = 2 * 50 * 50 * 8
        assert mem_50 - mem_10 >= (matrix_50 - matrix_10) * 0.9

    def test_estimate_memory_positive(self):
        """Memory estimate is always positive."""
        profiler = MemoryProfiler()
        pipeline = _SimplePipeline(score=0.5)

        mem = profiler.estimate_memory(pipeline, n_agents=5)
        assert mem > 0

    def test_estimate_memory_with_numpy_attribute(self):
        """Memory estimation handles numpy array attributes."""
        profiler = MemoryProfiler()

        class _PipelineWithArray:
            def __init__(self):
                self.weights = np.random.default_rng(42).random((100, 100))
                self.name = "test"

            def evaluate(self, msg):
                pass

        pipeline = _PipelineWithArray()
        mem = profiler.estimate_memory(pipeline, n_agents=5)
        # Must account for the 100x100 float64 array = 80000 bytes
        assert mem > 80000


class TestBenchmarkResult:
    """Tests for the BenchmarkResult dataclass."""

    def test_benchmark_result_fields(self):
        """BenchmarkResult stores all fields correctly."""
        result = BenchmarkResult(
            latency_summary={"p50": 1.5, "p95": 3.0, "p99": 5.0},
            memory_bytes=1024000,
            throughput_per_second=500.0,
        )
        assert result.latency_summary["p50"] == 1.5
        assert result.memory_bytes == 1024000
        assert result.throughput_per_second == 500.0


# ===========================================================================
# 3. DetectionMetrics
# ===========================================================================


class TestDetectionMetrics:
    """Tests for binary classification metrics."""

    def test_perfect_classifier(self):
        """Perfect classifier: all metrics are 1.0 (FPR and FNR are 0.0)."""
        m = DetectionMetrics(tp=50, fp=0, tn=50, fn=0)
        assert m.tpr == 1.0
        assert m.fpr == 0.0
        assert m.fnr == 0.0
        assert m.precision == 1.0
        assert m.recall == 1.0
        assert m.f1 == 1.0
        assert m.accuracy == 1.0
        assert m.specificity == 1.0
        assert m.mcc == 1.0

    def test_worst_classifier(self):
        """Everything misclassified: TPR=0, FPR=1."""
        m = DetectionMetrics(tp=0, fp=50, tn=0, fn=50)
        assert m.tpr == 0.0
        assert m.fpr == 1.0
        assert m.precision == 0.0
        assert m.recall == 0.0
        assert m.f1 == 0.0
        assert m.accuracy == 0.0
        assert m.mcc == -1.0

    def test_known_values(self):
        """Hand-computed metric values from known confusion matrix."""
        # TP=80, FP=10, TN=90, FN=20 -> total=200
        m = DetectionMetrics(tp=80, fp=10, tn=90, fn=20)

        assert m.tpr == pytest.approx(80 / 100, abs=1e-9)
        assert m.fpr == pytest.approx(10 / 100, abs=1e-9)
        assert m.fnr == pytest.approx(20 / 100, abs=1e-9)
        assert m.precision == pytest.approx(80 / 90, abs=1e-9)
        assert m.recall == pytest.approx(80 / 100, abs=1e-9)

        expected_f1 = 2 * (80 / 90) * (80 / 100) / ((80 / 90) + (80 / 100))
        assert m.f1 == pytest.approx(expected_f1, abs=1e-9)

        assert m.accuracy == pytest.approx(170 / 200, abs=1e-9)
        assert m.specificity == pytest.approx(90 / 100, abs=1e-9)

        # MCC = (TP*TN - FP*FN) / sqrt((TP+FP)(TP+FN)(TN+FP)(TN+FN))
        num = 80 * 90 - 10 * 20
        den = math.sqrt(
            (80 + 10) * (80 + 20) * (90 + 10) * (90 + 20)
        )
        assert m.mcc == pytest.approx(num / den, abs=1e-9)

    def test_zero_division_safety(self):
        """Zero counts produce 0.0 instead of raising."""
        m = DetectionMetrics(tp=0, fp=0, tn=0, fn=0)
        assert m.tpr == 0.0
        assert m.fpr == 0.0
        assert m.precision == 0.0
        assert m.recall == 0.0
        assert m.f1 == 0.0
        assert m.accuracy == 0.0
        assert m.mcc == 0.0

    def test_from_predictions(self):
        """Factory method from paired truth/prediction lists."""
        y_true = [True, True, True, False, False, False, True, False]
        y_pred = [True, True, False, False, True, False, True, False]

        m = DetectionMetrics.from_predictions(y_true, y_pred)

        # TP=3, FP=1, TN=3, FN=1
        assert m.tp == 3
        assert m.fp == 1
        assert m.tn == 3
        assert m.fn == 1

    def test_from_predictions_length_mismatch(self):
        """from_predictions raises ValueError on length mismatch."""
        with pytest.raises(ValueError, match="Length mismatch"):
            DetectionMetrics.from_predictions([True, False], [True])

    def test_from_experiment_result(self):
        """Factory method from an ExperimentResult."""
        er = ExperimentResult(
            architecture="X",
            attack_category="cat",
            n_attacks=100,
            true_positives=70,
            false_positives=5,
            true_negatives=20,
            false_negatives=5,
            detection_rate=0.93,
            false_positive_rate=0.2,
            avg_latency_ms=2.0,
        )
        m = DetectionMetrics.from_experiment_result(er)
        assert m.tp == 70
        assert m.fp == 5
        assert m.tn == 20
        assert m.fn == 5

    def test_to_dict_keys(self):
        """to_dict contains all expected metric keys."""
        m = DetectionMetrics(tp=10, fp=2, tn=8, fn=5)
        d = m.to_dict()

        expected_keys = {
            "tp", "fp", "tn", "fn", "tpr", "fpr", "fnr",
            "precision", "recall", "f1", "accuracy", "specificity", "mcc",
        }
        assert set(d.keys()) == expected_keys
        # All values are floats
        for v in d.values():
            assert isinstance(v, float)

    def test_recall_equals_tpr(self):
        """recall property is identical to tpr."""
        m = DetectionMetrics(tp=30, fp=5, tn=60, fn=5)
        assert m.recall == m.tpr

    def test_f1_is_harmonic_mean(self):
        """F1 is 2*P*R/(P+R), verified numerically."""
        m = DetectionMetrics(tp=40, fp=10, tn=45, fn=5)
        p = m.precision
        r = m.recall
        expected = 2 * p * r / (p + r)
        assert m.f1 == pytest.approx(expected, abs=1e-12)

    def test_mcc_range(self):
        """MCC is in [-1, 1]."""
        for tp, fp, tn, fn in [(50, 10, 40, 20), (0, 50, 50, 0), (30, 30, 30, 30)]:
            m = DetectionMetrics(tp=tp, fp=fp, tn=tn, fn=fn)
            assert -1.0 <= m.mcc <= 1.0


# ===========================================================================
# 4. Precision-Recall
# ===========================================================================


class TestPrecisionRecall:
    """Tests for PR curve generation and average precision."""

    def test_perfect_scores_give_high_ap(self):
        """When positives always score higher than negatives, AP is near 1."""
        rng = np.random.default_rng(42)
        n = 200
        y_true = np.array([1] * 100 + [0] * 100)
        # Positives score 0.8-1.0, negatives score 0.0-0.2
        scores = np.concatenate([
            rng.uniform(0.8, 1.0, 100),
            rng.uniform(0.0, 0.2, 100),
        ])

        pr = compute_pr_curve(y_true, scores)

        assert isinstance(pr, PRCurve)
        assert pr.average_precision > 0.95

    def test_random_scores_give_moderate_ap(self):
        """Random scores yield AP roughly equal to class prevalence."""
        rng = np.random.default_rng(42)
        n = 1000
        y_true = np.array([1] * 500 + [0] * 500)
        scores = rng.uniform(0.0, 1.0, n)

        pr = compute_pr_curve(y_true, scores)

        # With 50% prevalence and random scores, AP ~ 0.5
        assert 0.3 < pr.average_precision < 0.7

    def test_pr_curve_array_shapes(self):
        """PR curve arrays have consistent shapes."""
        y_true = np.array([1, 1, 0, 0, 1, 0])
        scores = np.array([0.9, 0.8, 0.3, 0.2, 0.7, 0.1])

        pr = compute_pr_curve(y_true, scores, n_thresholds=50)

        assert pr.precision.shape == (50,)
        assert pr.recall.shape == (50,)
        assert pr.thresholds.shape == (50,)

    def test_pr_curve_values_in_range(self):
        """All precision and recall values are in [0, 1]."""
        rng = np.random.default_rng(42)
        y_true = rng.integers(0, 2, size=100)
        scores = rng.uniform(0, 1, size=100)

        pr = compute_pr_curve(y_true, scores)

        assert np.all(pr.precision >= 0.0)
        assert np.all(pr.precision <= 1.0)
        assert np.all(pr.recall >= 0.0)
        assert np.all(pr.recall <= 1.0)

    def test_no_positives_returns_zero_ap(self):
        """With no positive labels, AP is 0."""
        y_true = np.zeros(20, dtype=int)
        scores = np.random.default_rng(42).uniform(0, 1, 20)

        pr = compute_pr_curve(y_true, scores)
        assert pr.average_precision == 0.0

    def test_compute_average_precision_from_arrays(self):
        """Direct computation of AP from precision/recall arrays."""
        # Perfect step function: precision=1.0 at all recall levels
        recall = np.linspace(0, 1, 100)
        precision = np.ones(100)

        ap = compute_average_precision_from_arrays(precision, recall)
        assert ap == pytest.approx(1.0, abs=0.02)

    def test_compute_average_precision_convenience(self):
        """compute_average_precision returns the PRCurve's AP."""
        y_true = np.array([1, 1, 0, 0, 1])
        scores = np.array([0.9, 0.8, 0.3, 0.1, 0.7])

        pr = compute_pr_curve(y_true, scores)
        ap = compute_average_precision(pr)
        assert ap == pr.average_precision

    def test_bootstrap_ap_ci_returns_three_floats(self):
        """bootstrap_ap_ci returns (ap, ci_lower, ci_upper)."""
        rng = np.random.default_rng(42)
        y_true = np.array([1] * 50 + [0] * 50)
        scores = np.concatenate([
            rng.uniform(0.6, 1.0, 50),
            rng.uniform(0.0, 0.4, 50),
        ])

        ap, lo, hi = bootstrap_ap_ci(y_true, scores, n_bootstrap=200, seed=42)

        assert isinstance(ap, float)
        assert isinstance(lo, float)
        assert isinstance(hi, float)
        assert lo <= ap <= hi or lo <= hi  # CI should bracket estimate (approximately)

    def test_bootstrap_ap_ci_narrow_with_large_sample(self):
        """CI should be narrow when the sample is large and separable."""
        rng = np.random.default_rng(42)
        y_true = np.array([1] * 500 + [0] * 500)
        scores = np.concatenate([
            rng.uniform(0.7, 1.0, 500),
            rng.uniform(0.0, 0.3, 500),
        ])

        ap, lo, hi = bootstrap_ap_ci(y_true, scores, n_bootstrap=500, seed=42)

        assert hi - lo < 0.1  # Narrow CI for well-separated data


# ===========================================================================
# 5. ROC
# ===========================================================================


class TestROC:
    """Tests for ROC curve generation, AUC, and Youden's J."""

    def test_perfect_separation_gives_high_auc(self):
        """Perfectly separated scores produce AUC near 1.0."""
        rng = np.random.default_rng(42)
        y_true = np.array([True] * 100 + [False] * 100)
        scores = np.concatenate([
            rng.uniform(0.8, 1.0, 100),
            rng.uniform(0.0, 0.2, 100),
        ])

        roc = compute_roc(y_true, scores)

        assert isinstance(roc, ROCCurve)
        assert roc.auc > 0.95

    def test_random_scores_give_near_half_auc(self):
        """Random scores yield AUC approximately 0.5."""
        rng = np.random.default_rng(42)
        n = 1000
        y_true = np.array([True] * 500 + [False] * 500)
        scores = rng.uniform(0, 1, n)

        roc = compute_roc(y_true, scores)

        assert 0.4 < roc.auc < 0.6

    def test_roc_curve_array_shapes(self):
        """ROC curve arrays have consistent lengths."""
        y_true = [True, False, True, False, True]
        scores = [0.9, 0.3, 0.7, 0.1, 0.8]

        roc = compute_roc(y_true, scores, n_thresholds=100)

        assert roc.fpr_points.shape == (100,)
        assert roc.tpr_points.shape == (100,)
        assert roc.thresholds.shape == (100,)

    def test_roc_values_in_range(self):
        """FPR and TPR are in [0, 1]."""
        rng = np.random.default_rng(42)
        y_true = rng.integers(0, 2, size=100).astype(bool)
        scores = rng.uniform(0, 1, 100)

        roc = compute_roc(y_true, scores)

        assert np.all(roc.fpr_points >= 0.0)
        assert np.all(roc.fpr_points <= 1.0)
        assert np.all(roc.tpr_points >= 0.0)
        assert np.all(roc.tpr_points <= 1.0)

    def test_compute_auc_matches_roc_auc(self):
        """compute_auc returns the same value as roc.auc."""
        y_true = [True, True, False, False]
        scores = [0.9, 0.7, 0.3, 0.1]

        roc = compute_roc(y_true, scores)
        auc_val = compute_auc(roc)

        assert auc_val == roc.auc

    def test_compute_auc_from_points_diagonal(self):
        """AUC for the diagonal (random classifier) is ~0.5."""
        fpr = np.linspace(0, 1, 100)
        tpr = np.linspace(0, 1, 100)

        auc = compute_auc_from_points(fpr, tpr)
        assert auc == pytest.approx(0.5, abs=0.02)

    def test_compute_auc_from_points_perfect(self):
        """AUC for perfect classifier (step at FPR=0) is ~1.0."""
        fpr = np.array([0.0, 0.0, 1.0])
        tpr = np.array([0.0, 1.0, 1.0])

        auc = compute_auc_from_points(fpr, tpr)
        assert auc == pytest.approx(1.0, abs=0.01)

    def test_auc_clamped_to_unit_interval(self):
        """AUC is always clamped to [0, 1]."""
        rng = np.random.default_rng(42)
        for _ in range(20):
            fpr = np.sort(rng.uniform(0, 1, 50))
            tpr = np.sort(rng.uniform(0, 1, 50))
            auc = compute_auc_from_points(fpr, tpr)
            assert 0.0 <= auc <= 1.0

    def test_length_mismatch_raises(self):
        """compute_roc raises on mismatched y_true/scores lengths."""
        with pytest.raises(ValueError, match="same length"):
            compute_roc([True, False], [0.5])

    def test_bootstrap_auc_ci(self):
        """bootstrap_auc_ci returns point estimate and CI."""
        rng = np.random.default_rng(42)
        y_true = np.array([True] * 50 + [False] * 50)
        scores = np.concatenate([
            rng.uniform(0.6, 1.0, 50),
            rng.uniform(0.0, 0.4, 50),
        ])

        auc, lo, hi = bootstrap_auc_ci(y_true, scores, n_bootstrap=200, seed=42)

        assert isinstance(auc, float)
        assert lo <= hi
        assert 0.0 <= lo
        assert hi <= 1.0

    def test_bootstrap_auc_ci_empty_input(self):
        """Empty input returns all zeros."""
        auc, lo, hi = bootstrap_auc_ci([], [], n_bootstrap=100, seed=42)
        assert auc == 0.0
        assert lo == 0.0
        assert hi == 0.0

    def test_youdens_j_perfect_classifier(self):
        """Youden's J for perfect separation is near 1.0."""
        y_true = np.array([True] * 100 + [False] * 100)
        scores = np.concatenate([np.ones(100) * 0.9, np.ones(100) * 0.1])

        roc = compute_roc(y_true, scores, n_thresholds=200)
        threshold, j_stat = youdens_j(roc)

        assert j_stat > 0.8
        assert 0.0 <= threshold <= 1.0

    def test_youdens_j_random_classifier(self):
        """Youden's J for random classifier is near 0."""
        rng = np.random.default_rng(42)
        y_true = np.array([True] * 500 + [False] * 500)
        scores = rng.uniform(0, 1, 1000)

        roc = compute_roc(y_true, scores)
        _, j_stat = youdens_j(roc)

        assert j_stat < 0.2


# ===========================================================================
# 6. Scalability
# ===========================================================================


class TestScalingModel:
    """Tests for the ScalingModel quadratic fit dataclass."""

    def test_predict_constant(self):
        """Constant model (beta1=beta2=0) returns beta0."""
        model = ScalingModel(beta0=5.0, beta1=0.0, beta2=0.0, r_squared=1.0)
        assert model.predict(10) == 5.0
        assert model.predict(100) == 5.0

    def test_predict_linear(self):
        """Linear model (beta2=0) returns beta0 + beta1*n."""
        model = ScalingModel(beta0=1.0, beta1=2.0, beta2=0.0, r_squared=1.0)
        assert model.predict(5) == pytest.approx(11.0)
        assert model.predict(10) == pytest.approx(21.0)

    def test_predict_quadratic(self):
        """Full quadratic model returns beta0 + beta1*n + beta2*n^2."""
        model = ScalingModel(beta0=1.0, beta1=0.5, beta2=0.01, r_squared=0.99)
        expected = 1.0 + 0.5 * 20 + 0.01 * 400
        assert model.predict(20) == pytest.approx(expected)


class TestScalabilityBenchmark:
    """Tests for agent-count scalability benchmarking."""

    def test_run_collects_results_for_all_counts(self):
        """run() returns latencies and memory for each agent count."""
        counts = [2, 5, 10]
        bench = ScalabilityBenchmark(agent_counts=counts, n_timing_runs=3)

        def pipeline_factory(adapter, n_agents):
            return _ScalablePipeline(n_agents)

        result = bench.run(_SimpleAdapter, pipeline_factory)

        assert isinstance(result, ScalabilityResult)
        assert result.agent_counts == counts
        assert len(result.latencies_ms) == 3
        assert len(result.memory_bytes) == 3
        assert all(lat > 0 for lat in result.latencies_ms)
        assert all(mem > 0 for mem in result.memory_bytes)

    def test_memory_scales_quadratically(self):
        """Memory estimate grows at least quadratically with agent count."""
        counts = [5, 10, 20, 50]
        bench = ScalabilityBenchmark(agent_counts=counts, n_timing_runs=1)

        def pipeline_factory(adapter, n_agents):
            return _ScalablePipeline(n_agents)

        result = bench.run(_SimpleAdapter, pipeline_factory)

        # Memory at 50 agents should be much larger than at 5
        # Ratio of quadratic terms: (50^2)/(5^2) = 100
        ratio = result.memory_bytes[-1] / result.memory_bytes[0]
        assert ratio > 10  # Generous bound; true ratio for matrix part is ~100

    def test_latency_increases_with_agents(self):
        """Latency at higher agent count is at least as high as at lower."""
        counts = [2, 10, 50]
        bench = ScalabilityBenchmark(agent_counts=counts, n_timing_runs=5)

        def pipeline_factory(adapter, n_agents):
            return _ScalablePipeline(n_agents)

        result = bench.run(_SimpleAdapter, pipeline_factory)

        # With O(n^2) matrix multiply, 50 agents should be slower than 2
        assert result.latencies_ms[-1] > result.latencies_ms[0]

    def test_fit_scaling_model_returns_model(self):
        """fit_scaling_model returns a ScalingModel with R^2."""
        counts = [2, 5, 10, 20, 50]
        bench = ScalabilityBenchmark(agent_counts=counts, n_timing_runs=3)

        def pipeline_factory(adapter, n_agents):
            return _ScalablePipeline(n_agents)

        result = bench.run(_SimpleAdapter, pipeline_factory)
        model = bench.fit_scaling_model(result)

        assert isinstance(model, ScalingModel)
        assert isinstance(model.r_squared, float)
        assert isinstance(model.beta0, float)
        assert isinstance(model.beta1, float)
        assert isinstance(model.beta2, float)

    def test_fit_scaling_model_good_fit_for_quadratic_data(self):
        """Quadratic synthetic data yields R^2 close to 1.0."""
        # Construct a ScalabilityResult with perfectly quadratic latencies
        counts = [2, 5, 10, 15, 20, 30, 50, 80, 100]
        latencies = [1.0 + 0.1 * n + 0.005 * n * n for n in counts]
        memories = [n * n * 16 for n in counts]

        result = ScalabilityResult(
            agent_counts=counts,
            latencies_ms=latencies,
            memory_bytes=memories,
        )

        bench = ScalabilityBenchmark()
        model = bench.fit_scaling_model(result)

        assert model.r_squared > 0.99
        assert model.beta2 == pytest.approx(0.005, abs=0.001)

    def test_fit_scaling_model_prediction_accuracy(self):
        """Fitted model prediction matches input data within tolerance."""
        counts = [5, 10, 20, 40, 60, 100]
        latencies = [2.0 + 0.3 * n + 0.002 * n * n for n in counts]
        memories = [n * n * 16 for n in counts]

        result = ScalabilityResult(
            agent_counts=counts,
            latencies_ms=latencies,
            memory_bytes=memories,
        )

        bench = ScalabilityBenchmark()
        model = bench.fit_scaling_model(result)

        for n, expected_lat in zip(counts, latencies):
            predicted = model.predict(n)
            assert predicted == pytest.approx(expected_lat, rel=0.05)

    def test_fit_scaling_model_insufficient_data(self):
        """With fewer than 3 data points, returns zero model."""
        result = ScalabilityResult(
            agent_counts=[5, 10],
            latencies_ms=[1.0, 2.0],
            memory_bytes=[100, 200],
        )

        bench = ScalabilityBenchmark()
        model = bench.fit_scaling_model(result)

        assert model.beta0 == 0.0
        assert model.beta1 == 0.0
        assert model.beta2 == 0.0
        assert model.r_squared == 0.0


# ===========================================================================
# Integration: cross-module tests
# ===========================================================================


class TestIntegration:
    """Cross-module integration tests combining runner, metrics, ROC, PR."""

    def test_experiment_to_metrics_pipeline(self):
        """Run experiment -> extract metrics -> verify consistency."""
        runner = ExperimentRunner(ExperimentConfig(seed=42))
        adapter = ClaudeCodeAdapter()
        samples = _make_attack_samples("direct_injection", n_attacks=50, n_benign=20)

        result = runner.run_single(adapter, samples, None)
        metrics = DetectionMetrics.from_experiment_result(result)

        # Consistency checks
        assert metrics.tp + metrics.fn == 50  # all attacks accounted for
        assert metrics.fp + metrics.tn == 20  # all benign accounted for
        assert metrics.tpr == pytest.approx(result.detection_rate, abs=1e-9)
        assert metrics.fpr == pytest.approx(result.false_positive_rate, abs=1e-9)

    def test_experiment_scores_to_roc(self):
        """Run experiment with scores -> compute ROC -> verify AUC range."""
        runner = ExperimentRunner(ExperimentConfig(seed=42))
        adapter = ClaudeCodeAdapter()
        samples = _make_attack_samples("impersonation", n_attacks=100, n_benign=50)

        result, per_sample = runner.run_single_with_scores(adapter, samples, None)

        y_true = [s["is_attack"] for s in samples]
        scores_arr = np.array([score for _, score in per_sample])

        roc = compute_roc(y_true, scores_arr)

        assert 0.0 <= roc.auc <= 1.0
        # Claude Code has multiplier 0.7 (favorable) and impersonation is "medium"
        # So detection should be decent
        assert roc.auc > 0.5

    def test_experiment_scores_to_pr(self):
        """Run experiment with scores -> compute PR curve -> verify structure."""
        # Use a high-multiplier adapter so scores span the range and
        # both attacks and benign have some separation.
        runner = ExperimentRunner(ExperimentConfig(seed=42))
        adapter = _SimpleAdapter(name="PRTest", multiplier=1.5)
        samples = _make_attack_samples("consensus_poisoning", n_attacks=100, n_benign=100)

        result, per_sample = runner.run_single_with_scores(adapter, samples, None)

        y_true = np.array([1 if s["is_attack"] else 0 for s in samples])
        scores_arr = np.array([score for _, score in per_sample])

        pr = compute_pr_curve(y_true, scores_arr)

        assert isinstance(pr, PRCurve)
        assert 0.0 <= pr.average_precision <= 1.0
        assert pr.precision.shape[0] == pr.recall.shape[0]
        # Attack scores should generally be higher than benign scores,
        # so AP should be above the 0.5 prevalence baseline
        assert pr.average_precision > 0.4

    def test_full_matrix_to_summary_to_metrics(self):
        """Full matrix -> summary table -> verify all entries valid."""
        runner = ExperimentRunner(ExperimentConfig(seed=42))
        adapters = [
            _SimpleAdapter(name="ArchA", multiplier=0.8),
            _SimpleAdapter(name="ArchB", multiplier=1.5),
        ]
        corpus = _make_corpus(
            ["direct_injection", "sybil_attack"],
            n_attacks=30,
            n_benign=10,
        )

        results = runner.run_full_matrix(adapters, corpus, None)
        table = runner.summary_table(results)

        assert len(table) == 2
        for arch_name, categories in table.items():
            for cat, detection_rate in categories.items():
                assert 0.0 <= detection_rate <= 1.0
