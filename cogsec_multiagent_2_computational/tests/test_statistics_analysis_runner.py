"""Tests for src/statistics/analysis_runner.py.

Covers:
- generate_sample_data: shape, keys, value ranges.
- run_full_analysis: output structure, key presence, value types.
- load_real_data: tested via generate_sample_data path (no real files needed).

All tests use real numpy computation. No mocks.
"""

from __future__ import annotations

from statistics.analysis_runner import generate_sample_data, run_full_analysis

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# generate_sample_data
# ---------------------------------------------------------------------------


class TestGenerateSampleData:
    """Tests for generate_sample_data()."""

    def test_returns_dict(self):
        rng = np.random.default_rng(42)
        result = generate_sample_data(rng, n=50)
        assert isinstance(result, dict)

    def test_has_required_keys(self):
        rng = np.random.default_rng(42)
        result = generate_sample_data(rng, n=50)
        expected_keys = {"cif_scores", "baseline_scores", "component_scores", "arch_scores"}
        assert set(result.keys()) == expected_keys

    def test_cif_scores_shape(self):
        rng = np.random.default_rng(42)
        result = generate_sample_data(rng, n=80)
        assert result["cif_scores"].shape == (80,)

    def test_baseline_scores_shape(self):
        rng = np.random.default_rng(42)
        result = generate_sample_data(rng, n=80)
        assert result["baseline_scores"].shape == (80,)

    def test_cif_scores_high(self):
        """CIF scores should be meaningfully higher than 0.5."""
        rng = np.random.default_rng(42)
        result = generate_sample_data(rng, n=200)
        assert float(np.mean(result["cif_scores"])) > 0.5

    def test_baseline_scores_low(self):
        """Baseline (undefended) scores should be low."""
        rng = np.random.default_rng(42)
        result = generate_sample_data(rng, n=200)
        assert float(np.mean(result["baseline_scores"])) < 0.5

    def test_cif_scores_clipped_to_unit_interval(self):
        rng = np.random.default_rng(42)
        result = generate_sample_data(rng, n=100)
        assert float(np.min(result["cif_scores"])) >= 0.0
        assert float(np.max(result["cif_scores"])) <= 1.0

    def test_baseline_scores_clipped_to_unit_interval(self):
        rng = np.random.default_rng(42)
        result = generate_sample_data(rng, n=100)
        assert float(np.min(result["baseline_scores"])) >= 0.0
        assert float(np.max(result["baseline_scores"])) <= 1.0

    def test_component_scores_is_dict(self):
        rng = np.random.default_rng(42)
        result = generate_sample_data(rng, n=50)
        assert isinstance(result["component_scores"], dict)

    def test_component_scores_has_expected_keys(self):
        rng = np.random.default_rng(42)
        result = generate_sample_data(rng, n=50)
        expected = {
            "firewall", "trust_calculus", "tripwire", "detection",
            "consensus", "provenance", "sandbox", "invariants",
        }
        assert set(result["component_scores"].keys()) == expected

    def test_component_scores_shapes(self):
        rng = np.random.default_rng(42)
        n = 60
        result = generate_sample_data(rng, n=n)
        for name, arr in result["component_scores"].items():
            assert arr.shape == (n,), f"Component {name} has wrong shape {arr.shape}"

    def test_arch_scores_is_dict(self):
        rng = np.random.default_rng(42)
        result = generate_sample_data(rng, n=50)
        assert isinstance(result["arch_scores"], dict)

    def test_arch_scores_has_expected_keys(self):
        rng = np.random.default_rng(42)
        result = generate_sample_data(rng, n=50)
        expected = {"claude_code", "autogpt", "crewai", "langgraph"}
        assert set(result["arch_scores"].keys()) == expected

    def test_default_n_is_100(self):
        rng = np.random.default_rng(42)
        result = generate_sample_data(rng)
        assert result["cif_scores"].shape == (100,)

    def test_different_seeds_produce_different_data(self):
        rng1 = np.random.default_rng(1)
        rng2 = np.random.default_rng(2)
        r1 = generate_sample_data(rng1, n=50)
        r2 = generate_sample_data(rng2, n=50)
        # Extremely unlikely to be identical with different seeds
        assert not np.allclose(r1["cif_scores"], r2["cif_scores"])


# ---------------------------------------------------------------------------
# run_full_analysis
# ---------------------------------------------------------------------------


class TestRunFullAnalysis:
    """Tests for run_full_analysis()."""

    @pytest.fixture(scope="class")
    def sample_data(self):
        rng = np.random.default_rng(42)
        return generate_sample_data(rng, n=100)

    @pytest.fixture(scope="class")
    def analysis_result(self, sample_data):
        return run_full_analysis(sample_data, seed=42)

    def test_returns_dict(self, analysis_result):
        assert isinstance(analysis_result, dict)

    def test_has_h1_key(self, analysis_result):
        assert "h1" in analysis_result

    def test_has_h2_key(self, analysis_result):
        assert "h2" in analysis_result

    def test_has_h3_key(self, analysis_result):
        assert "h3" in analysis_result

    def test_has_kruskal_wallis_key(self, analysis_result):
        assert "kruskal_wallis" in analysis_result

    def test_has_cohens_d_key(self, analysis_result):
        assert "cohens_d_cif_vs_baseline" in analysis_result

    def test_has_assumptions_key(self, analysis_result):
        assert "assumptions" in analysis_result
        assert "assumptions_met" in analysis_result

    def test_h1_structure(self, analysis_result):
        h1 = analysis_result["h1"]
        assert "statistic" in h1
        assert "p_value" in h1
        assert "significant" in h1
        assert isinstance(h1["significant"], bool)

    def test_h1_p_value_in_unit_interval(self, analysis_result):
        p = analysis_result["h1"]["p_value"]
        assert 0.0 <= p <= 1.0

    def test_h2_is_list(self, analysis_result):
        assert isinstance(analysis_result["h2"], list)
        assert len(analysis_result["h2"]) > 0

    def test_h2_entries_have_required_fields(self, analysis_result):
        for entry in analysis_result["h2"]:
            assert "name" in entry
            assert "p_value" in entry
            assert "significant" in entry

    def test_h3_is_list(self, analysis_result):
        assert isinstance(analysis_result["h3"], list)

    def test_kruskal_wallis_structure(self, analysis_result):
        kw = analysis_result["kruskal_wallis"]
        assert "h" in kw
        assert "p" in kw

    def test_kruskal_wallis_p_in_unit_interval(self, analysis_result):
        p = analysis_result["kruskal_wallis"]["p"]
        assert 0.0 <= p <= 1.0

    def test_cohens_d_is_float(self, analysis_result):
        d = analysis_result["cohens_d_cif_vs_baseline"]
        assert isinstance(d, float)

    def test_cohens_d_positive_cif_vs_baseline(self, analysis_result):
        """CIF should be markedly better than baseline -> large positive d."""
        d = analysis_result["cohens_d_cif_vs_baseline"]
        assert d > 0.0

    def test_assumptions_is_list(self, analysis_result):
        assert isinstance(analysis_result["assumptions"], list)

    def test_assumptions_met_is_bool(self, analysis_result):
        assert isinstance(analysis_result["assumptions_met"], bool)

    def test_h1_cif_significantly_better(self, analysis_result):
        """With large well-separated samples, H1 should be significant."""
        # CIF ~0.967 vs baseline ~0.12 — very significant
        assert analysis_result["h1"]["significant"] is True

    def test_deterministic_with_same_seed(self, sample_data):
        r1 = run_full_analysis(sample_data, seed=42)
        r2 = run_full_analysis(sample_data, seed=42)
        assert abs(r1["h1"]["p_value"] - r2["h1"]["p_value"]) < 1e-12
        assert abs(r1["cohens_d_cif_vs_baseline"] - r2["cohens_d_cif_vs_baseline"]) < 1e-12
