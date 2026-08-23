"""Tests for src/utils/types.py serialization helpers.

Covers:
- AttackCategory.top_category for all 12 subcategories.
- AttackOutcome and ArchitectureType enums.
- Severity IntEnum.
- DefenseResult: to_dict, from_dict roundtrip.
- MetricResult: to_dict.
- ExperimentConfig: to_dict.
- _serialize_value: all branches.
- serialize_defense_result, serialize_metric_result, serialize_attack_category.
- serialize_experiment_config, make_web_ui_payload.

All tests use real computation. No mocks.
"""

from __future__ import annotations

import json

from utils.types import (
    ArchitectureType,
    AttackCategory,
    AttackOutcome,
    DefenseResult,
    ExperimentConfig,
    MetricResult,
    Severity,
    _serialize_value,
    make_web_ui_payload,
    serialize_attack_category,
    serialize_defense_result,
    serialize_experiment_config,
    serialize_metric_result,
)

# ---------------------------------------------------------------------------
# AttackCategory
# ---------------------------------------------------------------------------


class TestAttackCategory:
    """Tests for AttackCategory enum and top_category property."""

    def test_all_injection_categories_map_to_injection(self):
        for cat in (
            AttackCategory.DIRECT_INJECTION,
            AttackCategory.INDIRECT_INJECTION,
            AttackCategory.NESTED_INJECTION,
        ):
            assert cat.top_category == "injection"

    def test_all_trust_categories_map_to_trust_exploitation(self):
        for cat in (
            AttackCategory.IMPERSONATION,
            AttackCategory.TRUST_INFLATION,
            AttackCategory.DELEGATION_ABUSE,
        ):
            assert cat.top_category == "trust_exploitation"

    def test_all_belief_categories_map_to_belief_manipulation(self):
        for cat in (
            AttackCategory.BELIEF_DRIFT,
            AttackCategory.BELIEF_FABRICATION,
            AttackCategory.BELIEF_INJECTION,
        ):
            assert cat.top_category == "belief_manipulation"

    def test_all_coordination_categories_map_to_coordination(self):
        for cat in (
            AttackCategory.SYBIL_ATTACK,
            AttackCategory.CONSENSUS_POISONING,
            AttackCategory.TIMING_ATTACK,
        ):
            assert cat.top_category == "coordination"

    def test_has_twelve_published_categories_plus_three_extension_families(self):
        """12 published + 3 that probe provenance, sandbox and consensus."""
        from attacks.validation import EXTENSION_CATEGORIES, PUBLISHED_CATEGORIES

        assert len(PUBLISHED_CATEGORIES) == 12
        assert len(EXTENSION_CATEGORIES) == 3
        assert len(AttackCategory) == 15


# ---------------------------------------------------------------------------
# AttackOutcome and ArchitectureType
# ---------------------------------------------------------------------------


class TestAttackOutcome:
    def test_values_exist(self):
        assert AttackOutcome.DETECTED.value == "detected"
        assert AttackOutcome.MISSED.value == "missed"
        assert AttackOutcome.PARTIAL.value == "partial"


class TestArchitectureType:
    def test_values_exist(self):
        assert ArchitectureType.CLAUDE_CODE.value == "claude_code"
        assert ArchitectureType.AUTOGPT.value == "autogpt"
        assert ArchitectureType.CREWAI.value == "crewai"
        assert ArchitectureType.LANGGRAPH.value == "langgraph"


# ---------------------------------------------------------------------------
# Severity
# ---------------------------------------------------------------------------


class TestSeverity:
    def test_ordering(self):
        assert Severity.LOW < Severity.MEDIUM < Severity.HIGH < Severity.CRITICAL

    def test_values(self):
        assert Severity.LOW == 1
        assert Severity.CRITICAL == 4


# ---------------------------------------------------------------------------
# DefenseResult
# ---------------------------------------------------------------------------


class TestDefenseResult:
    """Tests for DefenseResult dataclass."""

    def test_basic_construction(self):
        r = DefenseResult(detected=True, score=0.85, module_name="firewall")
        assert r.detected is True
        assert r.score == 0.85
        assert r.module_name == "firewall"
        assert r.details == {}
        assert r.latency_ms == 0.0

    def test_to_dict_keys(self):
        r = DefenseResult(detected=False, score=0.2, module_name="tripwire")
        d = r.to_dict()
        assert "detected" in d
        assert "score" in d
        assert "module_name" in d
        assert "details" in d
        assert "latency_ms" in d

    def test_to_dict_values(self):
        r = DefenseResult(detected=True, score=0.9876, module_name="sandbox", latency_ms=5.123)
        d = r.to_dict()
        assert d["detected"] is True
        assert d["module_name"] == "sandbox"
        assert abs(d["score"] - 0.9876) < 1e-5
        assert abs(d["latency_ms"] - 5.123) < 1e-2

    def test_from_dict_roundtrip(self):
        r = DefenseResult(
            detected=True, score=0.75, module_name="consensus",
            details={"reason": "threshold_exceeded"}, latency_ms=12.5,
        )
        d = r.to_dict()
        r2 = DefenseResult.from_dict(d)
        assert r2.detected == r.detected
        assert abs(r2.score - r.score) < 1e-5
        assert r2.module_name == r.module_name
        assert abs(r2.latency_ms - r.latency_ms) < 1e-2

    def test_to_dict_json_serialisable(self):
        r = DefenseResult(detected=False, score=0.3, module_name="provenance")
        json_str = json.dumps(r.to_dict())
        assert len(json_str) > 0


# ---------------------------------------------------------------------------
# MetricResult
# ---------------------------------------------------------------------------


class TestMetricResult:
    def test_to_dict_keys(self):
        m = MetricResult(name="TPR", value=0.967)
        d = m.to_dict()
        assert "name" in d
        assert "value" in d
        assert "ci_lower" in d
        assert "ci_upper" in d
        assert "n" in d

    def test_to_dict_none_ci_stays_none(self):
        m = MetricResult(name="F1", value=0.85)
        d = m.to_dict()
        assert d["ci_lower"] is None
        assert d["ci_upper"] is None

    def test_to_dict_with_ci(self):
        m = MetricResult(name="AUC", value=0.92, ci_lower=0.89, ci_upper=0.95, n=100)
        d = m.to_dict()
        assert d["ci_lower"] is not None
        assert d["ci_upper"] is not None
        assert d["n"] == 100


# ---------------------------------------------------------------------------
# ExperimentConfig
# ---------------------------------------------------------------------------


class TestExperimentConfig:
    def test_default_construction(self):
        cfg = ExperimentConfig()
        assert cfg.seed == 42
        assert cfg.n_runs == 10
        assert len(cfg.agent_counts) > 0

    def test_to_dict_keys(self):
        cfg = ExperimentConfig()
        d = cfg.to_dict()
        assert "seed" in d
        assert "n_runs" in d
        assert "agent_counts" in d
        assert "attack_corpus_size" in d
        assert "architectures" in d
        assert "output_dir" in d

    def test_to_dict_architectures_are_strings(self):
        cfg = ExperimentConfig()
        d = cfg.to_dict()
        for a in d["architectures"]:
            assert isinstance(a, str)

    def test_to_dict_json_serialisable(self):
        cfg = ExperimentConfig(seed=99, n_runs=5)
        json.dumps(cfg.to_dict())  # should not raise


# ---------------------------------------------------------------------------
# _serialize_value
# ---------------------------------------------------------------------------


class TestSerializeValue:
    def test_none_passthrough(self):
        assert _serialize_value(None) is None

    def test_bool_passthrough(self):
        assert _serialize_value(True) is True
        assert _serialize_value(False) is False

    def test_int_passthrough(self):
        assert _serialize_value(42) == 42

    def test_float_passthrough(self):
        assert abs(_serialize_value(3.14) - 3.14) < 1e-10

    def test_str_passthrough(self):
        assert _serialize_value("hello") == "hello"

    def test_enum_becomes_value(self):
        result = _serialize_value(AttackCategory.DIRECT_INJECTION)
        assert result == "direct_injection"

    def test_dict_recursive(self):
        d = {"key": AttackCategory.TIMING_ATTACK}
        result = _serialize_value(d)
        assert result == {"key": "timing_attack"}

    def test_list_recursive(self):
        lst = [AttackCategory.SYBIL_ATTACK, "plain"]
        result = _serialize_value(lst)
        assert result == ["sybil_attack", "plain"]

    def test_tuple_recursive(self):
        t = (AttackCategory.BELIEF_DRIFT, 42)
        result = _serialize_value(t)
        assert result == ["belief_drift", 42]

    def test_dataclass_becomes_dict(self):
        r = DefenseResult(detected=True, score=0.5, module_name="m")
        result = _serialize_value(r)
        assert isinstance(result, dict)
        assert result["detected"] is True

    def test_unknown_type_becomes_str(self):
        class Weird:
            def __str__(self):
                return "weird_repr"
        result = _serialize_value(Weird())
        assert result == "weird_repr"


# ---------------------------------------------------------------------------
# serialize_* wrappers
# ---------------------------------------------------------------------------


class TestSerializeWrappers:
    def test_serialize_defense_result(self):
        r = DefenseResult(detected=True, score=0.8, module_name="fw")
        d = serialize_defense_result(r)
        assert d["detected"] is True

    def test_serialize_metric_result(self):
        m = MetricResult(name="TPR", value=0.95)
        d = serialize_metric_result(m)
        assert d["name"] == "TPR"

    def test_serialize_attack_category(self):
        d = serialize_attack_category(AttackCategory.DIRECT_INJECTION)
        assert d["value"] == "direct_injection"
        assert d["top_category"] == "injection"

    def test_serialize_experiment_config(self):
        cfg = ExperimentConfig(seed=7)
        d = serialize_experiment_config(cfg)
        assert d["seed"] == 7


# ---------------------------------------------------------------------------
# make_web_ui_payload
# ---------------------------------------------------------------------------


class TestMakeWebUiPayload:
    def test_empty_payload(self):
        payload = make_web_ui_payload()
        assert payload == {}

    def test_with_module_results(self):
        results = [DefenseResult(detected=True, score=0.9, module_name="fw")]
        payload = make_web_ui_payload(module_results=results)
        assert "module_results" in payload
        assert len(payload["module_results"]) == 1

    def test_with_metrics(self):
        metrics = [MetricResult(name="F1", value=0.92)]
        payload = make_web_ui_payload(metrics=metrics)
        assert "metrics" in payload

    def test_with_config(self):
        cfg = ExperimentConfig(seed=123)
        payload = make_web_ui_payload(config=cfg)
        assert "config" in payload
        assert payload["config"]["seed"] == 123

    def test_with_extra(self):
        payload = make_web_ui_payload(extra={"custom_key": "custom_value"})
        assert "custom_key" in payload

    def test_all_components_combined(self):
        results = [DefenseResult(detected=False, score=0.1, module_name="sandbox")]
        metrics = [MetricResult(name="AUC", value=0.88)]
        cfg = ExperimentConfig(seed=55)
        payload = make_web_ui_payload(
            module_results=results, metrics=metrics, config=cfg, extra={"version": "1.0"}
        )
        assert "module_results" in payload
        assert "metrics" in payload
        assert "config" in payload
        assert "version" in payload

    def test_payload_is_json_serialisable(self):
        results = [DefenseResult(detected=True, score=0.7, module_name="tripwire")]
        payload = make_web_ui_payload(module_results=results)
        json.dumps(payload)  # should not raise
