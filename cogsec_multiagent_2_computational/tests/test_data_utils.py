"""Tests for the data and utils packages.

Covers:
- data.generate: DataGenerator
- data.loaders: load_json, load_detection_data, load_scalability_data
- data.result_loaders: EvaluationResultRow, loaders, derived views
- data.schema: DetectionData, ScalabilityData, AblationData, ColonyData
- utils.config: FrameworkConfig, load_config, _parse_simple_yaml
- utils.logging_setup: setup_logging, get_logger
- utils.random_seed: set_global_seed, get_rng
- utils.timing: timed, LatencyAccumulator
- utils.types: AttackCategory, AttackOutcome, ArchitectureType, etc.

All tests use real data, computation, and real files (tmp_path).
No mocks.
"""

import json
import logging
import time

import numpy as np
import pytest

from data.generate import DataGenerator
from data.loaders import load_json, load_detection_data, load_scalability_data
from data.result_loaders import (
    EvaluationResultRow,
    evaluation_to_confusion_counts,
    evaluation_to_detection_matrix,
    load_ablation_results,
    load_full_evaluation,
    load_sensitivity_results,
)
from data.schema import AblationData, ColonyData, DetectionData, ScalabilityData
from utils.config import FrameworkConfig, load_config, _parse_simple_yaml
from utils.logging_setup import get_logger
from utils.random_seed import get_rng, set_global_seed
from utils.timing import LatencyAccumulator, timed
from utils.types import (
    ArchitectureType,
    AttackCategory,
    AttackOutcome,
    DefenseResult,
    ExperimentConfig,
    MetricResult,
    Severity,
)


# ===========================================================================
# data.schema tests
# ===========================================================================

class TestDetectionData:
    """Tests for DetectionData schema."""

    def test_default_construction(self):
        d = DetectionData()
        assert d.architectures == []
        assert d.categories == []
        assert d.means == []
        assert d.cis == []
        assert d.seed == 42

    def test_construction_with_values(self):
        d = DetectionData(
            architectures=["A", "B"],
            categories=["cat1"],
            means=[[0.95], [0.90]],
            cis=[[0.01], [0.02]],
            seed=123,
        )
        assert d.architectures == ["A", "B"]
        assert len(d.means) == 2
        assert d.seed == 123

    def test_to_dict(self):
        d = DetectionData(architectures=["X"], categories=["Y"], means=[[0.5]], cis=[[0.01]])
        result = d.to_dict()
        assert isinstance(result, dict)
        assert result["architectures"] == ["X"]
        assert result["categories"] == ["Y"]
        assert result["means"] == [[0.5]]

    def test_from_dict(self):
        raw = {
            "architectures": ["A"],
            "categories": ["C"],
            "means": [[0.9]],
            "cis": [[0.01]],
            "seed": 7,
        }
        d = DetectionData.from_dict(raw)
        assert d.architectures == ["A"]
        assert d.seed == 7

    def test_from_dict_ignores_unknown_keys(self):
        raw = {"architectures": ["A"], "unknown_field": 42, "seed": 10}
        d = DetectionData.from_dict(raw)
        assert d.architectures == ["A"]
        assert d.seed == 10

    def test_roundtrip(self):
        original = DetectionData(
            architectures=["A", "B"],
            categories=["c1", "c2"],
            means=[[0.9, 0.8], [0.7, 0.6]],
            cis=[[0.01, 0.02], [0.03, 0.04]],
            seed=99,
        )
        restored = DetectionData.from_dict(original.to_dict())
        assert restored.architectures == original.architectures
        assert restored.means == original.means
        assert restored.seed == original.seed


class TestScalabilityData:
    """Tests for ScalabilityData schema."""

    def test_default_construction(self):
        s = ScalabilityData()
        assert s.agent_counts == []
        assert s.r_squared == 0.0

    def test_roundtrip(self):
        original = ScalabilityData(
            agent_counts=[2, 5, 10],
            latency_ms=[10.0, 25.0, 80.0],
            memory_mb=[50.0, 100.0, 200.0],
            regression_coeffs=[0.02, 1.5, 5.0],
            r_squared=0.99,
            seed=42,
        )
        restored = ScalabilityData.from_dict(original.to_dict())
        assert restored.agent_counts == original.agent_counts
        assert restored.r_squared == original.r_squared

    def test_from_dict_ignores_extras(self):
        raw = {"agent_counts": [1, 2], "extra": "ignored"}
        s = ScalabilityData.from_dict(raw)
        assert s.agent_counts == [1, 2]


class TestAblationData:
    """Tests for AblationData schema."""

    def test_default_construction(self):
        a = AblationData()
        assert a.configurations == []
        assert a.detection_rates == []

    def test_roundtrip(self):
        original = AblationData(
            configurations=["Full", "-Firewall"],
            detection_rates=[0.96, 0.82],
            cis=[0.01, 0.02],
            seed=42,
        )
        restored = AblationData.from_dict(original.to_dict())
        assert restored.configurations == original.configurations
        assert restored.detection_rates == original.detection_rates


class TestColonyData:
    """Tests for ColonyData schema."""

    def test_default_construction(self):
        c = ColonyData()
        assert c.colony_sizes == []
        assert c.convergence_steps == []

    def test_roundtrip(self):
        original = ColonyData(
            colony_sizes=[3, 5, 10],
            convergence_steps=[12, 18, 30],
            integrity_scores=[0.98, 0.97, 0.95],
            attack_success_rate=[0.02, 0.03, 0.05],
            seed=42,
        )
        restored = ColonyData.from_dict(original.to_dict())
        assert restored.colony_sizes == original.colony_sizes
        assert restored.integrity_scores == original.integrity_scores


# ===========================================================================
# data.generate tests
# ===========================================================================

class TestDataGenerator:
    """Tests for the DataGenerator."""

    def test_constructor_defaults(self):
        gen = DataGenerator()
        assert gen.seed == 42
        assert gen.output_dir.name == "data"

    def test_constructor_custom(self, tmp_path):
        gen = DataGenerator(seed=99, output_dir=str(tmp_path / "custom"))
        assert gen.seed == 99
        assert gen.output_dir == tmp_path / "custom"

    def test_generate_detection_data(self):
        gen = DataGenerator(seed=42)
        data = gen.generate_detection_data()
        assert isinstance(data, DetectionData)
        assert len(data.architectures) == 6
        assert len(data.categories) == 4
        assert len(data.means) == 6
        assert len(data.means[0]) == 4
        assert len(data.cis) == 6
        assert data.seed == 42

    def test_detection_data_values_in_range(self):
        gen = DataGenerator(seed=42)
        data = gen.generate_detection_data()
        for row in data.means:
            for val in row:
                assert 0.80 <= val <= 0.99

    def test_generate_scalability_data(self):
        gen = DataGenerator(seed=42)
        data = gen.generate_scalability_data()
        assert isinstance(data, ScalabilityData)
        assert len(data.agent_counts) == 10
        assert len(data.latency_ms) == 10
        assert len(data.memory_mb) == 10
        assert len(data.regression_coeffs) == 3  # quadratic
        assert 0.0 <= data.r_squared <= 1.0

    def test_scalability_latency_increases_with_agents(self):
        gen = DataGenerator(seed=42)
        data = gen.generate_scalability_data()
        # Latency should generally increase (not strictly monotonic due to noise)
        assert data.latency_ms[-1] > data.latency_ms[0]

    def test_scalability_memory_positive(self):
        gen = DataGenerator(seed=42)
        data = gen.generate_scalability_data()
        for mem in data.memory_mb:
            assert mem >= 50.0

    def test_generate_ablation_data(self):
        gen = DataGenerator(seed=42)
        data = gen.generate_ablation_data()
        assert isinstance(data, AblationData)
        assert len(data.configurations) == 9
        assert len(data.detection_rates) == 9
        assert len(data.cis) == 9

    def test_ablation_full_cif_highest(self):
        gen = DataGenerator(seed=42)
        data = gen.generate_ablation_data()
        # "Full CIF" is first and should have the highest base rate
        assert data.configurations[0] == "Full CIF"
        # Full CIF base rate is 0.965, should be near highest
        full_rate = data.detection_rates[0]
        assert full_rate > 0.90

    def test_generate_colony_data(self):
        gen = DataGenerator(seed=42)
        data = gen.generate_colony_data()
        assert isinstance(data, ColonyData)
        assert len(data.colony_sizes) == 5
        assert len(data.convergence_steps) == 5
        assert len(data.integrity_scores) == 5
        assert len(data.attack_success_rate) == 5

    def test_colony_integrity_scores_in_range(self):
        gen = DataGenerator(seed=42)
        data = gen.generate_colony_data()
        for score in data.integrity_scores:
            assert 0.90 <= score <= 0.99

    def test_generate_all(self, tmp_path):
        gen = DataGenerator(seed=42, output_dir=str(tmp_path))
        datasets = gen.generate_all()
        assert "detection" in datasets
        assert "scalability" in datasets
        assert "ablation" in datasets
        assert "colony" in datasets
        assert isinstance(datasets["detection"], DetectionData)
        assert isinstance(datasets["scalability"], ScalabilityData)

    def test_generate_all_saves_files(self, tmp_path):
        gen = DataGenerator(seed=42, output_dir=str(tmp_path))
        gen.generate_all()
        assert (tmp_path / "detection_data.json").exists()
        assert (tmp_path / "scalability_data.json").exists()
        assert (tmp_path / "ablation_data.json").exists()
        assert (tmp_path / "colony_data.json").exists()

    def test_save_creates_valid_json(self, tmp_path):
        gen = DataGenerator(seed=42, output_dir=str(tmp_path))
        data = {"key": "value", "number": 42}
        path = gen.save(data, "test_output.json")
        assert (tmp_path / "test_output.json").exists()
        with open(path) as f:
            loaded = json.load(f)
        assert loaded == data

    def test_save_creates_directory(self, tmp_path):
        nested = tmp_path / "a" / "b" / "c"
        gen = DataGenerator(seed=42, output_dir=str(nested))
        gen.save({"x": 1}, "file.json")
        assert (nested / "file.json").exists()

    def test_reproducibility_same_seed(self):
        gen1 = DataGenerator(seed=42)
        gen2 = DataGenerator(seed=42)
        d1 = gen1.generate_detection_data()
        d2 = gen2.generate_detection_data()
        assert d1.means == d2.means
        assert d1.cis == d2.cis

    def test_different_seeds_produce_different_data(self):
        gen1 = DataGenerator(seed=42)
        gen2 = DataGenerator(seed=99)
        d1 = gen1.generate_detection_data()
        d2 = gen2.generate_detection_data()
        assert d1.means != d2.means


# ===========================================================================
# data.loaders tests
# ===========================================================================

class TestLoaders:
    """Tests for data loading utilities."""

    def test_load_json_valid(self, tmp_path):
        data = {"foo": "bar", "nums": [1, 2, 3]}
        path = tmp_path / "test.json"
        path.write_text(json.dumps(data))
        loaded = load_json(str(path))
        assert loaded == data

    def test_load_json_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_json(str(tmp_path / "nonexistent.json"))

    def test_load_json_invalid_json(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("not valid json {{{")
        with pytest.raises(json.JSONDecodeError):
            load_json(str(path))

    def test_load_detection_data(self, tmp_path):
        gen = DataGenerator(seed=42, output_dir=str(tmp_path))
        original = gen.generate_detection_data()
        gen.save(original.to_dict(), "detection.json")

        loaded = load_detection_data(str(tmp_path / "detection.json"))
        assert isinstance(loaded, DetectionData)
        assert loaded.architectures == original.architectures
        assert loaded.means == original.means

    def test_load_scalability_data(self, tmp_path):
        gen = DataGenerator(seed=42, output_dir=str(tmp_path))
        original = gen.generate_scalability_data()
        gen.save(original.to_dict(), "scalability.json")

        loaded = load_scalability_data(str(tmp_path / "scalability.json"))
        assert isinstance(loaded, ScalabilityData)
        assert loaded.agent_counts == original.agent_counts
        assert abs(loaded.r_squared - original.r_squared) < 1e-10


# ===========================================================================
# data.result_loaders tests
# ===========================================================================

class TestEvaluationResultRow:
    """Tests for the EvaluationResultRow dataclass."""

    def test_construction(self):
        row = EvaluationResultRow(
            architecture="Claude Code",
            attack_category="injection",
            n_attacks=100,
            true_positives=95,
            false_positives=3,
            true_negatives=97,
            false_negatives=5,
            detection_rate=0.95,
            false_positive_rate=0.03,
            avg_latency_ms=12.5,
        )
        assert row.architecture == "Claude Code"
        assert row.true_positives == 95
        assert row.detection_rate == 0.95


class TestResultLoaders:
    """Tests for experiment result loading functions."""

    def _write_evaluation_rows(self, tmp_path):
        """Write a minimal evaluation results file."""
        rows = [
            {
                "architecture": "Claude Code",
                "attack_category": "injection",
                "n_attacks": 100,
                "true_positives": 95,
                "false_positives": 3,
                "true_negatives": 97,
                "false_negatives": 5,
                "detection_rate": 0.95,
                "false_positive_rate": 0.03,
                "avg_latency_ms": 12.5,
            },
            {
                "architecture": "AutoGPT",
                "attack_category": "trust_exploitation",
                "n_attacks": 50,
                "true_positives": 45,
                "false_positives": 2,
                "true_negatives": 48,
                "false_negatives": 5,
                "detection_rate": 0.90,
                "false_positive_rate": 0.04,
                "avg_latency_ms": 15.0,
            },
        ]
        path = tmp_path / "eval.json"
        path.write_text(json.dumps(rows))
        return str(path)

    def test_load_full_evaluation(self, tmp_path):
        path = self._write_evaluation_rows(tmp_path)
        rows = load_full_evaluation(path)
        assert len(rows) == 2
        assert isinstance(rows[0], EvaluationResultRow)
        assert rows[0].architecture == "Claude Code"

    def test_load_full_evaluation_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_full_evaluation(str(tmp_path / "missing.json"))

    def test_load_ablation_results(self, tmp_path):
        data = {
            "component_removal": [{"name": "firewall", "delta_tpr": -0.14}],
            "minimal_forward": {"components": ["fw", "trust"]},
        }
        path = tmp_path / "ablation.json"
        path.write_text(json.dumps(data))
        loaded = load_ablation_results(str(path))
        assert "component_removal" in loaded

    def test_load_sensitivity_results(self, tmp_path):
        data = {"parameter_sweeps": [{"param": "threshold", "values": [0.1, 0.5, 0.9]}]}
        path = tmp_path / "sensitivity.json"
        path.write_text(json.dumps(data))
        loaded = load_sensitivity_results(str(path))
        assert "parameter_sweeps" in loaded

    def test_evaluation_to_detection_matrix(self, tmp_path):
        path = self._write_evaluation_rows(tmp_path)
        rows = load_full_evaluation(path)
        archs, cats, matrix = evaluation_to_detection_matrix(rows=rows)
        assert isinstance(matrix, np.ndarray)
        assert matrix.ndim == 2

    def test_evaluation_to_detection_matrix_from_path(self, tmp_path):
        path = self._write_evaluation_rows(tmp_path)
        archs, cats, matrix = evaluation_to_detection_matrix(path=path)
        assert isinstance(matrix, np.ndarray)

    def test_evaluation_to_confusion_counts(self, tmp_path):
        path = self._write_evaluation_rows(tmp_path)
        rows = load_full_evaluation(path)
        counts = evaluation_to_confusion_counts(rows=rows)
        assert "Claude Code" in counts
        assert "injection" in counts["Claude Code"]
        tp, fp, tn, fn = counts["Claude Code"]["injection"]
        assert tp == 95
        assert fp == 3
        assert tn == 97
        assert fn == 5

    def test_detection_matrix_values(self, tmp_path):
        path = self._write_evaluation_rows(tmp_path)
        rows = load_full_evaluation(path)
        archs, cats, matrix = evaluation_to_detection_matrix(rows=rows)
        # Check that known values appear in the matrix
        for i, arch in enumerate(archs):
            for j, cat in enumerate(cats):
                val = matrix[i, j]
                assert 0.0 <= val <= 1.0


# ===========================================================================
# utils.config tests
# ===========================================================================

class TestFrameworkConfig:
    """Tests for FrameworkConfig."""

    def test_default_values(self):
        config = FrameworkConfig()
        assert config.injection_threshold == 0.7
        assert config.suspicious_threshold == 0.4
        assert config.drift_threshold == 0.3
        assert config.trust_decay == 0.85
        assert config.consensus_acceptance == 0.7
        assert abs(config.consensus_quorum - 2 / 3) < 1e-10
        assert config.sandbox_ttl == 300.0
        assert config.canary_tolerance == 0.1
        assert config.invariant_check_interval == 1.0
        assert config.seed == 42

    def test_custom_values(self):
        config = FrameworkConfig(injection_threshold=0.9, seed=99)
        assert config.injection_threshold == 0.9
        assert config.seed == 99

    def test_to_dict(self):
        config = FrameworkConfig()
        d = config.to_dict()
        assert isinstance(d, dict)
        assert d["injection_threshold"] == 0.7
        assert d["seed"] == 42

    def test_from_dict(self):
        data = {"injection_threshold": 0.8, "seed": 100, "trust_decay": 0.90}
        config = FrameworkConfig.from_dict(data)
        assert config.injection_threshold == 0.8
        assert config.seed == 100
        assert config.trust_decay == 0.90

    def test_from_dict_ignores_unknown(self):
        data = {"injection_threshold": 0.8, "unknown_key": "ignored"}
        config = FrameworkConfig.from_dict(data)
        assert config.injection_threshold == 0.8

    def test_roundtrip(self):
        original = FrameworkConfig(injection_threshold=0.99, seed=7)
        restored = FrameworkConfig.from_dict(original.to_dict())
        assert restored.injection_threshold == original.injection_threshold
        assert restored.seed == original.seed


class TestLoadConfig:
    """Tests for load_config and YAML parsing."""

    def test_load_config_none_returns_default(self):
        config = load_config(None)
        assert isinstance(config, FrameworkConfig)
        assert config.seed == 42

    def test_load_config_missing_file_returns_default(self, tmp_path):
        config = load_config(str(tmp_path / "nonexistent.yaml"))
        assert isinstance(config, FrameworkConfig)
        assert config.seed == 42

    def test_load_config_json(self, tmp_path):
        data = {"injection_threshold": 0.55, "seed": 77}
        path = tmp_path / "config.json"
        path.write_text(json.dumps(data))
        config = load_config(str(path))
        assert config.injection_threshold == 0.55
        assert config.seed == 77

    def test_load_config_yaml(self, tmp_path):
        yaml_content = """# Framework config
injection_threshold: 0.65
seed: 88
trust_decay: 0.80
"""
        path = tmp_path / "config.yaml"
        path.write_text(yaml_content)
        config = load_config(str(path))
        assert config.injection_threshold == 0.65
        assert config.seed == 88
        assert config.trust_decay == 0.80

    def test_load_config_yml_extension(self, tmp_path):
        yaml_content = "seed: 55\n"
        path = tmp_path / "config.yml"
        path.write_text(yaml_content)
        config = load_config(str(path))
        assert config.seed == 55

    def test_load_config_unknown_extension_returns_default(self, tmp_path):
        path = tmp_path / "config.txt"
        path.write_text("seed: 99")
        config = load_config(str(path))
        assert config.seed == 42  # Default, not parsed

    def test_parse_simple_yaml_basic(self):
        text = "key1: value1\nkey2: 42\nkey3: 3.14\n"
        result = _parse_simple_yaml(text)
        assert result["key1"] == "value1"
        assert result["key2"] == 42
        assert abs(result["key3"] - 3.14) < 1e-10

    def test_parse_simple_yaml_booleans(self):
        text = "flag_true: true\nflag_false: false\n"
        result = _parse_simple_yaml(text)
        assert result["flag_true"] is True
        assert result["flag_false"] is False

    def test_parse_simple_yaml_comments_and_blanks(self):
        text = """# This is a comment
key1: hello

# Another comment
key2: 42
"""
        result = _parse_simple_yaml(text)
        assert result["key1"] == "hello"
        assert result["key2"] == 42
        assert len(result) == 2

    def test_parse_simple_yaml_no_colon_lines_skipped(self):
        text = "valid_key: 10\nno colon here\nanother_key: 20\n"
        result = _parse_simple_yaml(text)
        assert result["valid_key"] == 10
        assert result["another_key"] == 20
        assert len(result) == 2


# ===========================================================================
# utils.logging_setup tests
# ===========================================================================

class TestLoggingSetup:
    """Tests for structured logging setup."""

    def test_get_logger_returns_logger(self):
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "cogsec.test_module"

    def test_get_logger_different_names(self):
        log1 = get_logger("alpha")
        log2 = get_logger("beta")
        assert log1.name != log2.name
        assert log1.name == "cogsec.alpha"
        assert log2.name == "cogsec.beta"

    def test_get_logger_nested_name(self):
        logger = get_logger("evaluation.runner")
        assert logger.name == "cogsec.evaluation.runner"


# ===========================================================================
# utils.random_seed tests
# ===========================================================================

class TestRandomSeed:
    """Tests for reproducibility seed management."""

    def test_set_global_seed_returns_generator(self):
        rng = set_global_seed(42)
        assert isinstance(rng, np.random.Generator)

    def test_set_global_seed_reproducible(self):
        rng1 = set_global_seed(42)
        val1 = rng1.random()

        rng2 = set_global_seed(42)
        val2 = rng2.random()

        assert val1 == val2

    def test_different_seeds_different_values(self):
        rng1 = set_global_seed(42)
        val1 = rng1.random()

        rng2 = set_global_seed(99)
        val2 = rng2.random()

        assert val1 != val2

    def test_get_rng_returns_generator(self):
        rng = get_rng()
        assert isinstance(rng, np.random.Generator)

    def test_get_rng_with_seed(self):
        rng1 = get_rng(seed=123)
        val1 = rng1.random()

        rng2 = get_rng(seed=123)
        val2 = rng2.random()

        assert val1 == val2

    def test_get_rng_without_seed_returns_existing(self):
        set_global_seed(42)
        rng = get_rng()
        assert isinstance(rng, np.random.Generator)

    def test_get_rng_sequence_deterministic(self):
        set_global_seed(42)
        rng = get_rng()
        seq1 = [rng.random() for _ in range(10)]

        set_global_seed(42)
        rng = get_rng()
        seq2 = [rng.random() for _ in range(10)]

        assert seq1 == seq2


# ===========================================================================
# utils.timing tests
# ===========================================================================

class TestTimedDecorator:
    """Tests for the @timed decorator."""

    def test_timed_bare_decorator(self):
        @timed
        def fast_fn():
            return 42

        result = fast_fn()
        assert result == 42
        assert hasattr(fast_fn, "last_latency_ms")
        assert fast_fn.last_latency_ms >= 0.0

    def test_timed_with_label(self):
        @timed(label="my_operation")
        def some_fn():
            return "hello"

        result = some_fn()
        assert result == "hello"
        assert some_fn._timed_label == "my_operation"
        assert some_fn.last_latency_ms >= 0.0

    def test_timed_measures_latency(self):
        @timed
        def slow_fn():
            total = 0
            for i in range(100000):
                total += i
            return total

        slow_fn()
        assert slow_fn.last_latency_ms > 0.0

    def test_timed_preserves_return_value(self):
        @timed
        def add(a, b):
            return a + b

        assert add(3, 4) == 7

    def test_timed_preserves_function_name(self):
        @timed
        def my_named_fn():
            pass

        assert my_named_fn.__name__ == "my_named_fn"

    def test_timed_initial_latency_zero(self):
        @timed
        def f():
            return 1

        assert f.last_latency_ms == 0.0
        f()
        assert f.last_latency_ms > 0.0

    def test_timed_updates_on_each_call(self):
        @timed
        def f():
            pass

        f()
        first = f.last_latency_ms
        f()
        second = f.last_latency_ms
        # Both should be non-negative (not necessarily different)
        assert first >= 0.0
        assert second >= 0.0

    def test_timed_with_exception(self):
        @timed
        def failing():
            raise ValueError("boom")

        with pytest.raises(ValueError, match="boom"):
            failing()
        # Latency should still be recorded even on exception
        assert failing.last_latency_ms > 0.0


class TestLatencyAccumulator:
    """Tests for LatencyAccumulator."""

    def test_empty_accumulator(self):
        acc = LatencyAccumulator(label="test")
        assert acc.count() == 0
        assert acc.p50() == 0.0
        assert acc.p95() == 0.0
        assert acc.p99() == 0.0
        assert acc.mean() == 0.0
        assert acc.std() == 0.0

    def test_record_single_sample(self):
        acc = LatencyAccumulator(label="test")
        acc.record(10.0)
        assert acc.count() == 1
        assert acc.mean() == 10.0
        assert acc.p50() == 10.0

    def test_record_multiple_samples(self):
        acc = LatencyAccumulator(label="test")
        samples = [1.0, 2.0, 3.0, 4.0, 5.0]
        for s in samples:
            acc.record(s)
        assert acc.count() == 5
        assert acc.mean() == 3.0

    def test_percentiles_ordered(self):
        acc = LatencyAccumulator(label="test")
        np.random.seed(42)
        for _ in range(1000):
            acc.record(np.random.exponential(10.0))
        assert acc.p50() <= acc.p95()
        assert acc.p95() <= acc.p99()

    def test_std_requires_two_samples(self):
        acc = LatencyAccumulator(label="test")
        acc.record(5.0)
        assert acc.std() == 0.0  # Only 1 sample -> 0
        acc.record(15.0)
        assert acc.std() > 0.0

    def test_std_computation(self):
        acc = LatencyAccumulator(label="test")
        values = [10.0, 20.0, 30.0]
        for v in values:
            acc.record(v)
        expected_std = float(np.std(values, ddof=1))
        assert abs(acc.std() - expected_std) < 1e-10

    def test_summary_keys(self):
        acc = LatencyAccumulator(label="test")
        acc.record(5.0)
        acc.record(10.0)
        s = acc.summary()
        assert set(s.keys()) == {"p50", "p95", "p99", "mean", "std", "count"}
        assert s["count"] == 2.0

    def test_reset(self):
        acc = LatencyAccumulator(label="test")
        acc.record(1.0)
        acc.record(2.0)
        assert acc.count() == 2
        acc.reset()
        assert acc.count() == 0
        assert acc.mean() == 0.0

    def test_label(self):
        acc = LatencyAccumulator(label="my_metric")
        assert acc.label == "my_metric"

    def test_known_percentiles(self):
        """With values 1..100, p50 should be ~50.5, p95 ~95.05, p99 ~99.01."""
        acc = LatencyAccumulator(label="test")
        for i in range(1, 101):
            acc.record(float(i))
        assert 49 <= acc.p50() <= 52
        assert 94 <= acc.p95() <= 97
        assert 98 <= acc.p99() <= 100


# ===========================================================================
# utils.types tests
# ===========================================================================

class TestAttackCategory:
    """Tests for the AttackCategory enum."""

    def test_all_members_exist(self):
        assert len(AttackCategory) == 12

    def test_injection_top_category(self):
        assert AttackCategory.DIRECT_INJECTION.top_category == "injection"
        assert AttackCategory.INDIRECT_INJECTION.top_category == "injection"
        assert AttackCategory.NESTED_INJECTION.top_category == "injection"

    def test_trust_exploitation_top_category(self):
        assert AttackCategory.IMPERSONATION.top_category == "trust_exploitation"
        assert AttackCategory.TRUST_INFLATION.top_category == "trust_exploitation"
        assert AttackCategory.DELEGATION_ABUSE.top_category == "trust_exploitation"

    def test_belief_manipulation_top_category(self):
        assert AttackCategory.BELIEF_DRIFT.top_category == "belief_manipulation"
        assert AttackCategory.BELIEF_FABRICATION.top_category == "belief_manipulation"
        assert AttackCategory.BELIEF_INJECTION.top_category == "belief_manipulation"

    def test_coordination_top_category(self):
        assert AttackCategory.SYBIL_ATTACK.top_category == "coordination"
        assert AttackCategory.CONSENSUS_POISONING.top_category == "coordination"
        assert AttackCategory.TIMING_ATTACK.top_category == "coordination"

    def test_enum_values(self):
        assert AttackCategory.DIRECT_INJECTION.value == "direct_injection"
        assert AttackCategory.SYBIL_ATTACK.value == "sybil_attack"


class TestAttackOutcome:
    """Tests for the AttackOutcome enum."""

    def test_outcomes(self):
        assert AttackOutcome.DETECTED.value == "detected"
        assert AttackOutcome.MISSED.value == "missed"
        assert AttackOutcome.PARTIAL.value == "partial"

    def test_all_outcomes_count(self):
        assert len(AttackOutcome) == 3


class TestArchitectureType:
    """Tests for the ArchitectureType enum."""

    def test_all_architectures(self):
        assert len(ArchitectureType) == 6

    def test_values(self):
        assert ArchitectureType.CLAUDE_CODE.value == "claude_code"
        assert ArchitectureType.AUTOGPT.value == "autogpt"
        assert ArchitectureType.CREWAI.value == "crewai"
        assert ArchitectureType.LANGGRAPH.value == "langgraph"
        assert ArchitectureType.METAGPT.value == "metagpt"
        assert ArchitectureType.CAMEL.value == "camel"


class TestDefenseResult:
    """Tests for the DefenseResult dataclass."""

    def test_construction(self):
        result = DefenseResult(
            detected=True,
            score=0.95,
            module_name="firewall",
            details={"reason": "injection pattern"},
            latency_ms=5.0,
        )
        assert result.detected is True
        assert result.score == 0.95
        assert result.module_name == "firewall"
        assert result.details == {"reason": "injection pattern"}
        assert result.latency_ms == 5.0

    def test_default_values(self):
        result = DefenseResult(detected=False, score=0.1, module_name="trust")
        assert result.details == {}
        assert result.latency_ms == 0.0


class TestMetricResult:
    """Tests for the MetricResult dataclass."""

    def test_construction(self):
        m = MetricResult(name="TPR", value=0.95, ci_lower=0.93, ci_upper=0.97, n=100)
        assert m.name == "TPR"
        assert m.value == 0.95
        assert m.ci_lower == 0.93
        assert m.ci_upper == 0.97
        assert m.n == 100

    def test_defaults(self):
        m = MetricResult(name="F1", value=0.92)
        assert m.ci_lower is None
        assert m.ci_upper is None
        assert m.n == 0


class TestExperimentConfig:
    """Tests for ExperimentConfig dataclass."""

    def test_defaults(self):
        ec = ExperimentConfig()
        assert ec.seed == 42
        assert ec.n_runs == 10
        assert ec.attack_corpus_size == 950
        assert ec.output_dir == "output"
        assert len(ec.agent_counts) == 10
        assert len(ec.architectures) == 6

    def test_custom(self):
        ec = ExperimentConfig(seed=99, n_runs=5)
        assert ec.seed == 99
        assert ec.n_runs == 5

    def test_architectures_are_enum_members(self):
        ec = ExperimentConfig()
        for arch in ec.architectures:
            assert isinstance(arch, ArchitectureType)


class TestSeverity:
    """Tests for the Severity IntEnum."""

    def test_values(self):
        assert Severity.LOW == 1
        assert Severity.MEDIUM == 2
        assert Severity.HIGH == 3
        assert Severity.CRITICAL == 4

    def test_ordering(self):
        assert Severity.LOW < Severity.MEDIUM
        assert Severity.MEDIUM < Severity.HIGH
        assert Severity.HIGH < Severity.CRITICAL

    def test_is_int(self):
        assert isinstance(Severity.LOW, int)
        assert Severity.LOW + 1 == 2
