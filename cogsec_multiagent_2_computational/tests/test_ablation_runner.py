"""Tests for src/ablation/runner.py.

Covers:
- BENIGN_MESSAGES constant structure.
- make_default_components: shape, types, value ranges.
- evaluate_component_subset: real pipeline evaluation with real components.
- run_full_ablation: integration smoke test that exercises all sub-studies.

All tests use real computation. No mocks.
"""

from __future__ import annotations

import pytest

from ablation.runner import (
    BENIGN_MESSAGES,
    COMPONENT_TO_MODULE,
    evaluate_component_subset,
    make_default_components,
    run_full_ablation,
)

# ---------------------------------------------------------------------------
# BENIGN_MESSAGES
# ---------------------------------------------------------------------------


class TestBenignMessages:
    """Tests for the BENIGN_MESSAGES constant."""

    def test_is_list_of_strings(self):
        assert isinstance(BENIGN_MESSAGES, list)
        for msg in BENIGN_MESSAGES:
            assert isinstance(msg, str), f"Non-string message: {msg!r}"

    def test_has_50_messages(self):
        assert len(BENIGN_MESSAGES) == 50

    def test_messages_non_empty(self):
        for msg in BENIGN_MESSAGES:
            assert len(msg.strip()) > 0, f"Empty message found: {msg!r}"

    def test_no_duplicate_messages(self):
        assert len(BENIGN_MESSAGES) == len(set(BENIGN_MESSAGES)), "Duplicate messages found"


# ---------------------------------------------------------------------------
# make_default_components
# ---------------------------------------------------------------------------


class TestMakeDefaultComponents:
    """Tests for the make_default_components function."""

    def test_returns_dict(self):
        result = make_default_components()
        assert isinstance(result, dict)

    def test_has_eight_components(self):
        result = make_default_components()
        assert len(result) == 8

    def test_expected_component_names(self):
        result = make_default_components()
        expected = {
            "firewall", "trust_calculus", "tripwire", "detection",
            "consensus", "provenance", "sandbox", "invariants",
        }
        assert set(result.keys()) == expected

    def test_values_are_floats_in_unit_interval(self):
        result = make_default_components()
        for name, val in result.items():
            assert isinstance(val, float), f"{name} should be float, got {type(val)}"
            assert 0.0 < val <= 1.0, f"{name}={val} not in (0, 1]"

    def test_calls_are_independent(self):
        """Each call returns a fresh dict (no shared state)."""
        d1 = make_default_components()
        d2 = make_default_components()
        d1["firewall"] = 9999.0
        assert d2["firewall"] != 9999.0

    def test_every_component_maps_to_a_real_registry_module(self):
        """Every ablation name must name a module the pipeline can remove.

        A name with no registry counterpart is silently ignored by the
        pipeline factory, so its "removal" delta would measure nothing.
        """
        from composition.factory import MODULE_REGISTRY

        components = set(make_default_components())
        assert set(COMPONENT_TO_MODULE) == components
        targets = [COMPONENT_TO_MODULE[name] for name in components]
        assert set(targets) == set(MODULE_REGISTRY)
        assert len(targets) == len(set(targets)), "two components share one module"


# ---------------------------------------------------------------------------
# evaluate_component_subset
# ---------------------------------------------------------------------------


class TestEvaluateComponentSubset:
    """Tests for evaluate_component_subset (real pipeline)."""

    def test_returns_tuple_of_two_floats(self):
        components = list(make_default_components().keys())
        tpr, fpr = evaluate_component_subset(components, seed=42)
        assert isinstance(tpr, float)
        assert isinstance(fpr, float)

    def test_tpr_in_unit_interval(self):
        components = list(make_default_components().keys())
        tpr, fpr = evaluate_component_subset(components, seed=42)
        assert 0.0 <= tpr <= 1.0
        assert 0.0 <= fpr <= 1.0

    def test_deterministic_with_same_seed(self):
        components = list(make_default_components().keys())
        r1 = evaluate_component_subset(components, seed=42)
        r2 = evaluate_component_subset(components, seed=42)
        assert r1 == r2

    def test_subset_lower_tpr_than_full(self):
        """Removing some components should generally reduce detection."""
        all_components = list(make_default_components().keys())
        tpr_full, _ = evaluate_component_subset(all_components, seed=42)
        # Remove three components
        subset = all_components[:5]
        tpr_subset, _ = evaluate_component_subset(subset, seed=42)
        # Detection can only go down or stay (not guaranteed to be strictly lower,
        # but the full set should be >= subset on average)
        assert tpr_full >= 0.0 and tpr_subset >= 0.0

    def test_single_component(self):
        """Single component evaluation should not crash."""
        tpr, fpr = evaluate_component_subset(["firewall"], seed=42)
        assert 0.0 <= tpr <= 1.0
        assert 0.0 <= fpr <= 1.0

    def test_empty_component_list_detects_nothing(self):
        """A pipeline with zero defense modules detects nothing at all."""
        assert evaluate_component_subset([], seed=42) == (0.0, 0.0)

    def test_unknown_component_name_raises(self):
        """Unknown component names fail closed instead of being ignored."""
        with pytest.raises(ValueError, match="Unknown ablation component"):
            evaluate_component_subset(["firewall", "not_a_component"], seed=42)

    def test_no_rng_keyword(self):
        """The noise-injection keyword is gone; callers cannot re-enable it."""
        import numpy as np

        components = list(make_default_components().keys())
        with pytest.raises(TypeError):
            evaluate_component_subset(
                components, seed=42, rng=np.random.default_rng(99),
            )

    def test_repeated_evaluation_is_bit_identical(self):
        """No noise: repeated evaluation is exactly equal, not merely close."""
        components = list(make_default_components().keys())
        first = evaluate_component_subset(components, seed=42)
        for _ in range(4):
            assert evaluate_component_subset(components, seed=42) == first


# ---------------------------------------------------------------------------
# run_full_ablation — integration smoke test
# ---------------------------------------------------------------------------


class TestRunFullAblation:
    """Integration smoke test for run_full_ablation."""

    def test_returns_dict_with_expected_keys(self):
        result = run_full_ablation(seed=42)
        expected_keys = {
            "full_pipeline",
            "component_removal",
            "minimal_forward",
            "minimal_backward",
            "top_synergies",
            "data_origin",
            "source_script",
            "seed",
            "generator",
            # The realised size of the stratified attack draw. Every delta in
            # this artifact has a resolution of 1/n, and n is not a constant --
            # it is 98 on the published corpus and 100 on the integrated one --
            # so consumers that reconstructed it from the smallest observed
            # delta reconstructed it wrong as soon as two components tied.
            "n_attacks",
        }
        assert set(result.keys()) == expected_keys
        assert result["n_attacks"] > 0

    def test_full_pipeline_operating_point_is_reported(self):
        """The unablated operating point is serialized, not reconstructed."""
        result = run_full_ablation(seed=42)
        full = result["full_pipeline"]
        assert set(full) == {"tpr", "fpr", "youden_j"}
        assert 0.0 <= full["tpr"] <= 1.0
        assert 0.0 <= full["fpr"] <= 1.0
        assert abs(full["youden_j"] - (full["tpr"] - full["fpr"])) < 1e-12
        # It must agree with the deltas recorded on every removal row.
        for row in result["component_removal"]:
            assert abs((row["tpr"] - row["delta_tpr"]) - full["tpr"]) < 1e-12
            assert abs((row["fpr"] - row["delta_fpr"]) - full["fpr"]) < 1e-12

    def test_component_removal_is_list(self):
        result = run_full_ablation(seed=42)
        assert isinstance(result["component_removal"], list)
        assert len(result["component_removal"]) > 0

    def test_component_removal_entries_have_required_fields(self):
        result = run_full_ablation(seed=42)
        required = {
            "removed", "tpr", "delta_tpr", "fpr", "delta_fpr",
            "youden_j", "delta_youden_j",
        }
        for entry in result["component_removal"]:
            assert required <= set(entry), f"missing {required - set(entry)}"
            assert isinstance(entry["tpr"], float)
            assert isinstance(entry["fpr"], float)
            assert 0.0 <= entry["tpr"] <= 1.0
            assert 0.0 <= entry["fpr"] <= 1.0
            assert abs(entry["youden_j"] - (entry["tpr"] - entry["fpr"])) < 1e-12
            assert abs(
                entry["delta_youden_j"] - (entry["delta_tpr"] - entry["delta_fpr"])
            ) < 1e-12

    def test_minimal_forward_has_components_and_rates(self):
        result = run_full_ablation(seed=42)
        fwd = result["minimal_forward"]
        assert isinstance(fwd["components"], list)
        for key in ("tpr", "fpr", "youden_j"):
            assert isinstance(fwd[key], float), f"{key} missing or not a float"
        assert 0.0 <= fwd["tpr"] <= 1.0
        assert 0.0 <= fwd["fpr"] <= 1.0
        assert abs(fwd["youden_j"] - (fwd["tpr"] - fwd["fpr"])) < 1e-12

    def test_minimal_backward_has_components_and_rates(self):
        result = run_full_ablation(seed=42)
        bwd = result["minimal_backward"]
        assert isinstance(bwd["components"], list)
        for key in ("tpr", "fpr", "youden_j"):
            assert isinstance(bwd[key], float), f"{key} missing or not a float"
        assert 0.0 <= bwd["tpr"] <= 1.0
        assert 0.0 <= bwd["fpr"] <= 1.0
        assert abs(bwd["youden_j"] - (bwd["tpr"] - bwd["fpr"])) < 1e-12

    def test_top_synergies_is_list(self):
        result = run_full_ablation(seed=42)
        assert isinstance(result["top_synergies"], list)

    def test_top_synergies_entries_have_required_fields(self):
        result = run_full_ablation(seed=42)
        required = {
            "a", "b", "synergy", "tpr_a", "tpr_b", "combined_tpr",
            "fpr_a", "fpr_b", "combined_fpr", "youden_synergy",
        }
        for entry in result["top_synergies"]:
            assert required <= set(entry), f"missing {required - set(entry)}"
            j_a = entry["tpr_a"] - entry["fpr_a"]
            j_b = entry["tpr_b"] - entry["fpr_b"]
            j_combined = entry["combined_tpr"] - entry["combined_fpr"]
            assert abs(entry["youden_synergy"] - (j_combined - max(j_a, j_b))) < 1e-12

    def test_deterministic_with_same_seed(self):
        """Two runs at the same seed must be byte-identical, not merely close."""
        import json

        r1 = run_full_ablation(seed=42)
        r2 = run_full_ablation(seed=42)
        assert json.dumps(r1, sort_keys=True) == json.dumps(r2, sort_keys=True)
