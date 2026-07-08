"""Tests for src/visualization/composer_data.py.

Covers:
- MODULE_REGISTRY constant: structure, 8 modules, required fields.
- ALGEBRA_FORMULAS constant: 4 strategies, required fields.
- PRESET_PIPELINES constant: 4 presets, required fields.
- _series_detection_rate, _parallel_detection_rate, _hybrid_detection_rate.
- _series_latency, _parallel_latency, _hybrid_latency.
- get_module_registry, get_algebra_formulas, get_preset_pipelines.
- compute_custom_pipeline_stats: valid and invalid inputs.
- get_composer_data: structure with and without category theory.

All tests use real computation. No mocks.
"""

from __future__ import annotations

import pytest

from visualization.composer_data import (
    ALGEBRA_FORMULAS,
    MODULE_REGISTRY,
    PRESET_PIPELINES,
    _hybrid_detection_rate,
    _hybrid_latency,
    _parallel_detection_rate,
    _parallel_latency,
    _series_detection_rate,
    _series_latency,
    compute_custom_pipeline_stats,
    get_algebra_formulas,
    get_composer_data,
    get_module_registry,
    get_preset_pipelines,
)

# ---------------------------------------------------------------------------
# MODULE_REGISTRY constant
# ---------------------------------------------------------------------------


class TestModuleRegistry:
    """Tests for the MODULE_REGISTRY module-level constant."""

    def test_has_eight_modules(self):
        assert len(MODULE_REGISTRY) == 8

    def test_expected_module_names(self):
        expected = {"Firewall", "Detection", "Tripwire", "TrustCalc",
                    "Consensus", "Provenance", "Sandbox", "Invariants"}
        assert set(MODULE_REGISTRY.keys()) == expected

    def test_each_module_has_required_fields(self):
        required = {"detection_rate", "latency_ms", "omega_class",
                    "morphism_type", "description", "color", "handles_attack_types"}
        for name, meta in MODULE_REGISTRY.items():
            missing = required - set(meta.keys())
            assert not missing, f"Module {name} missing fields: {missing}"

    def test_detection_rates_in_unit_interval(self):
        for name, meta in MODULE_REGISTRY.items():
            dr = meta["detection_rate"]
            assert 0.0 < dr <= 1.0, f"{name} detection_rate={dr} out of range"

    def test_latencies_positive(self):
        for name, meta in MODULE_REGISTRY.items():
            lat = meta["latency_ms"]
            assert lat > 0.0, f"{name} latency={lat} not positive"

    def test_handles_attack_types_is_list(self):
        for name, meta in MODULE_REGISTRY.items():
            assert isinstance(meta["handles_attack_types"], list)
            assert len(meta["handles_attack_types"]) >= 1


# ---------------------------------------------------------------------------
# ALGEBRA_FORMULAS constant
# ---------------------------------------------------------------------------


class TestAlgebraFormulas:
    """Tests for the ALGEBRA_FORMULAS constant."""

    def test_has_four_strategies(self):
        assert len(ALGEBRA_FORMULAS) == 4

    def test_expected_strategy_keys(self):
        expected = {"series", "parallel", "hybrid", "weighted_parallel"}
        assert set(ALGEBRA_FORMULAS.keys()) == expected

    def test_each_strategy_has_required_fields(self):
        required = {"name", "theorem", "formula", "latency_formula", "description"}
        for key, val in ALGEBRA_FORMULAS.items():
            missing = required - set(val.keys())
            assert not missing, f"Strategy {key} missing: {missing}"


# ---------------------------------------------------------------------------
# PRESET_PIPELINES constant
# ---------------------------------------------------------------------------


class TestPresetPipelines:
    """Tests for the PRESET_PIPELINES constant."""

    def test_has_four_presets(self):
        assert len(PRESET_PIPELINES) == 4

    def test_expected_preset_keys(self):
        expected = {"full_stack", "minimal_viable", "fast_path", "hybrid"}
        assert set(PRESET_PIPELINES.keys()) == expected

    def test_each_preset_has_detection_rate(self):
        for key, preset in PRESET_PIPELINES.items():
            assert "detection_rate" in preset, f"Preset {key} missing detection_rate"
            assert 0.0 < preset["detection_rate"] <= 1.0

    def test_each_preset_has_latency(self):
        for key, preset in PRESET_PIPELINES.items():
            assert "latency_ms" in preset
            assert preset["latency_ms"] > 0.0

    def test_full_stack_has_all_modules(self):
        assert len(PRESET_PIPELINES["full_stack"]["modules"]) == 8


# ---------------------------------------------------------------------------
# Detection rate formulas
# ---------------------------------------------------------------------------


class TestSeriesDetectionRate:
    def test_single_module(self):
        rate = _series_detection_rate([0.8])
        assert abs(rate - 0.8) < 1e-10

    def test_two_modules(self):
        # 1 - (1-0.8)*(1-0.7) = 1 - 0.2*0.3 = 1 - 0.06 = 0.94
        rate = _series_detection_rate([0.8, 0.7])
        assert abs(rate - 0.94) < 1e-10

    def test_empty_list(self):
        rate = _series_detection_rate([])
        assert abs(rate - 0.0) < 1e-10

    def test_all_ones(self):
        rate = _series_detection_rate([1.0, 1.0])
        assert abs(rate - 1.0) < 1e-10

    def test_monotonically_increasing_with_more_modules(self):
        r1 = _series_detection_rate([0.8])
        r2 = _series_detection_rate([0.8, 0.7])
        r3 = _series_detection_rate([0.8, 0.7, 0.6])
        assert r1 <= r2 <= r3


class TestParallelDetectionRate:
    def test_equivalent_to_series(self):
        rates = [0.9, 0.8, 0.7]
        assert abs(_parallel_detection_rate(rates) - _series_detection_rate(rates)) < 1e-10


class TestHybridDetectionRate:
    def test_two_stages(self):
        fast = [0.9, 0.8]
        deep = [0.7, 0.6]
        rate = _hybrid_detection_rate(fast, deep)
        r_fast = _series_detection_rate(fast)
        r_deep = _series_detection_rate(deep)
        expected = 1.0 - (1.0 - r_fast) * (1.0 - r_deep)
        assert abs(rate - expected) < 1e-10

    def test_empty_fast(self):
        deep = [0.8, 0.7]
        rate = _hybrid_detection_rate([], deep)
        # r_fast = 0.0
        assert abs(rate - _series_detection_rate(deep)) < 1e-10

    def test_empty_deep(self):
        fast = [0.9]
        rate = _hybrid_detection_rate(fast, [])
        assert abs(rate - _parallel_detection_rate(fast)) < 1e-10


# ---------------------------------------------------------------------------
# Latency formulas
# ---------------------------------------------------------------------------


class TestSeriesLatency:
    def test_sum_of_latencies(self):
        assert abs(_series_latency([10.0, 20.0, 30.0]) - 60.0) < 1e-10

    def test_empty(self):
        assert _series_latency([]) == 0.0


class TestParallelLatency:
    def test_max_of_latencies(self):
        assert abs(_parallel_latency([10.0, 50.0, 30.0]) - 50.0) < 1e-10

    def test_empty(self):
        assert _parallel_latency([]) == 0.0


class TestHybridLatency:
    def test_max_fast_plus_sum_deep(self):
        fast = [10.0, 50.0]
        deep = [30.0, 20.0]
        expected = 50.0 + 50.0  # max(fast) + sum(deep)
        assert abs(_hybrid_latency(fast, deep) - expected) < 1e-10


# ---------------------------------------------------------------------------
# Public API functions
# ---------------------------------------------------------------------------


class TestGetModuleRegistry:
    def test_returns_dict(self):
        result = get_module_registry()
        assert isinstance(result, dict)

    def test_has_eight_modules(self):
        result = get_module_registry()
        assert len(result) == 8

    def test_is_a_copy(self):
        r1 = get_module_registry()
        r1["Firewall"]["detection_rate"] = 9999.0
        r2 = get_module_registry()
        assert r2["Firewall"]["detection_rate"] != 9999.0


class TestGetAlgebraFormulas:
    def test_returns_dict_with_four_entries(self):
        result = get_algebra_formulas()
        assert len(result) == 4

    def test_is_a_copy(self):
        r1 = get_algebra_formulas()
        r1["series"]["name"] = "MODIFIED"
        r2 = get_algebra_formulas()
        assert r2["series"]["name"] != "MODIFIED"


class TestGetPresetPipelines:
    def test_returns_dict_with_four_presets(self):
        result = get_preset_pipelines()
        assert len(result) == 4


class TestComputeCustomPipelineStats:
    def test_series_strategy(self):
        result = compute_custom_pipeline_stats(["Firewall", "Detection"], strategy="series")
        assert "detection_rate" in result
        assert "latency_ms" in result
        assert 0.0 < result["detection_rate"] <= 1.0

    def test_parallel_strategy(self):
        result = compute_custom_pipeline_stats(["Firewall", "Detection"], strategy="parallel")
        assert "detection_rate" in result

    def test_hybrid_strategy_with_deep_modules(self):
        result = compute_custom_pipeline_stats(
            ["Firewall", "Detection"],
            strategy="hybrid",
            deep_modules=["Consensus", "Provenance"],
        )
        assert "detection_rate" in result

    def test_returns_module_rates_and_latencies(self):
        result = compute_custom_pipeline_stats(["Firewall", "Tripwire"])
        assert "module_rates" in result
        assert "module_latencies" in result
        assert len(result["module_rates"]) == 2

    def test_unknown_module_raises(self):
        with pytest.raises(ValueError, match="Unknown module"):
            compute_custom_pipeline_stats(["Firewall", "__NonExistent__"])

    def test_unknown_deep_module_raises(self):
        with pytest.raises(ValueError, match="Unknown deep module"):
            compute_custom_pipeline_stats(
                ["Firewall"],
                strategy="hybrid",
                deep_modules=["__BadModule__"],
            )

    def test_single_module(self):
        result = compute_custom_pipeline_stats(["Firewall"])
        assert result["detection_rate"] == pytest.approx(MODULE_REGISTRY["Firewall"]["detection_rate"])  # noqa: E501

    def test_all_modules_series(self):
        all_modules = list(MODULE_REGISTRY.keys())
        result = compute_custom_pipeline_stats(all_modules, strategy="series")
        assert result["detection_rate"] > 0.99  # very high with 8 modules


class TestGetComposerData:
    def test_without_category_theory(self):
        data = get_composer_data(include_category_theory=False)
        assert "schema_version" in data
        assert "modules" in data
        assert "algebra" in data
        assert "presets" in data
        assert "category_theory" not in data

    def test_with_category_theory_does_not_raise(self):
        # category_theory_advanced may raise internally but get_composer_data
        # catches exceptions and returns {"error": ...}
        data = get_composer_data(include_category_theory=True)
        assert "category_theory" in data
        # Either a real result or an error dict
        ct = data["category_theory"]
        assert isinstance(ct, dict)

    def test_schema_version_string(self):
        data = get_composer_data(include_category_theory=False)
        assert isinstance(data["schema_version"], str)
        assert len(data["schema_version"]) > 0

    def test_modules_count(self):
        data = get_composer_data(include_category_theory=False)
        assert len(data["modules"]) == 8

    def test_algebra_count(self):
        data = get_composer_data(include_category_theory=False)
        assert len(data["algebra"]) == 4

    def test_presets_count(self):
        data = get_composer_data(include_category_theory=False)
        assert len(data["presets"]) == 4
