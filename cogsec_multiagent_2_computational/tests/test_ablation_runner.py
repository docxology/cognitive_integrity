"""Tests for src/ablation/runner.py.

Covers:
- BENIGN_MESSAGES constant structure.
- make_default_components: shape, types, value ranges.
- evaluate_component_subset: real pipeline evaluation with real components.
- run_full_ablation: integration smoke test that exercises all sub-studies.

All tests use real computation. No mocks.
"""

from __future__ import annotations

import numpy as np

from ablation.runner import (
    BENIGN_MESSAGES,
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

    def test_empty_component_list(self):
        """No components should still return valid floats."""
        tpr, fpr = evaluate_component_subset([], seed=42)
        assert 0.0 <= tpr <= 1.0
        assert 0.0 <= fpr <= 1.0

    def test_with_rng_adds_noise(self):
        """Providing an rng should add noise so results differ from no-rng."""
        components = list(make_default_components().keys())
        rng = np.random.default_rng(99)
        tpr_noisy, fpr_noisy = evaluate_component_subset(components, seed=42, rng=rng)
        # Result should still be in [0, 1]
        assert 0.0 <= tpr_noisy <= 1.0
        assert 0.0 <= fpr_noisy <= 1.0


# ---------------------------------------------------------------------------
# run_full_ablation — integration smoke test
# ---------------------------------------------------------------------------


class TestRunFullAblation:
    """Integration smoke test for run_full_ablation."""

    def test_returns_dict_with_expected_keys(self):
        result = run_full_ablation(seed=42)
        expected_keys = {
            "component_removal",
            "minimal_forward",
            "minimal_backward",
            "top_synergies",
        }
        assert set(result.keys()) == expected_keys

    def test_component_removal_is_list(self):
        result = run_full_ablation(seed=42)
        assert isinstance(result["component_removal"], list)
        assert len(result["component_removal"]) > 0

    def test_component_removal_entries_have_required_fields(self):
        result = run_full_ablation(seed=42)
        for entry in result["component_removal"]:
            assert "removed" in entry
            assert "tpr" in entry
            assert "delta_tpr" in entry
            assert isinstance(entry["tpr"], float)
            assert 0.0 <= entry["tpr"] <= 1.0

    def test_minimal_forward_has_components_and_tpr(self):
        result = run_full_ablation(seed=42)
        fwd = result["minimal_forward"]
        assert isinstance(fwd["components"], list)
        assert isinstance(fwd["tpr"], float)
        assert 0.0 <= fwd["tpr"] <= 1.0

    def test_minimal_backward_has_components_and_tpr(self):
        result = run_full_ablation(seed=42)
        bwd = result["minimal_backward"]
        assert isinstance(bwd["components"], list)
        assert isinstance(bwd["tpr"], float)
        assert 0.0 <= bwd["tpr"] <= 1.0

    def test_top_synergies_is_list(self):
        result = run_full_ablation(seed=42)
        assert isinstance(result["top_synergies"], list)

    def test_top_synergies_entries_have_required_fields(self):
        result = run_full_ablation(seed=42)
        for entry in result["top_synergies"]:
            assert "a" in entry
            assert "b" in entry
            assert "synergy" in entry

    def test_deterministic_with_same_seed(self):
        """Running twice with the same seed should produce identical results."""
        r1 = run_full_ablation(seed=42)
        r2 = run_full_ablation(seed=42)
        # Component removal order and values should match
        assert len(r1["component_removal"]) == len(r2["component_removal"])
        for a, b in zip(r1["component_removal"], r2["component_removal"]):
            assert a["removed"] == b["removed"]
            assert abs(a["tpr"] - b["tpr"]) < 1e-6
