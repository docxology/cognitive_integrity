"""Additional tests for src/statistics/analysis_runner.py — load_real_data path.

Covers the load_real_data function (lines 62-134) which was not previously
exercised because it requires real data files.

Uses the existing output/data directory which is populated by conftest.py.
"""

from __future__ import annotations

from pathlib import Path
from statistics.analysis_runner import load_real_data, run_full_analysis

import numpy as np
import pytest

# Locate the output data directory relative to the project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_EVAL_PATH = _PROJECT_ROOT / "output" / "data" / "full_evaluation_results.json"
_ABLATION_PATH = _PROJECT_ROOT / "output" / "data" / "ablation_results.json"


# ---------------------------------------------------------------------------
# load_real_data
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not _EVAL_PATH.exists(),
    reason="output/data/full_evaluation_results.json not found",
)
class TestLoadRealData:
    """Tests for load_real_data using the real output data files."""

    @pytest.fixture(scope="class")
    def loaded(self):
        rng = np.random.default_rng(42)
        return load_real_data(_EVAL_PATH, _ABLATION_PATH, rng)

    def test_returns_dict(self, loaded):
        assert isinstance(loaded, dict)

    def test_has_required_keys(self, loaded):
        expected = {"cif_scores", "baseline_scores", "component_scores", "arch_scores"}
        assert set(loaded.keys()) == expected

    def test_cif_scores_is_array(self, loaded):
        assert isinstance(loaded["cif_scores"], np.ndarray)
        assert len(loaded["cif_scores"]) > 0

    def test_cif_scores_in_unit_interval(self, loaded):
        assert float(np.min(loaded["cif_scores"])) >= 0.0
        assert float(np.max(loaded["cif_scores"])) <= 1.0

    def test_baseline_scores_in_unit_interval(self, loaded):
        assert float(np.min(loaded["baseline_scores"])) >= 0.0
        assert float(np.max(loaded["baseline_scores"])) <= 1.0

    def test_component_scores_is_dict(self, loaded):
        assert isinstance(loaded["component_scores"], dict)
        assert len(loaded["component_scores"]) > 0

    def test_arch_scores_is_dict(self, loaded):
        assert isinstance(loaded["arch_scores"], dict)

    def test_component_scores_arrays(self, loaded):
        for name, arr in loaded["component_scores"].items():
            assert isinstance(arr, np.ndarray), f"{name} should be ndarray"
            assert len(arr) > 0

    def test_run_full_analysis_on_real_data(self, loaded):
        result = run_full_analysis(loaded, seed=42)
        assert isinstance(result, dict)
        assert "h1" in result
        assert "cohens_d_cif_vs_baseline" in result


@pytest.mark.skipif(
    not _EVAL_PATH.exists(),
    reason="output/data/full_evaluation_results.json not found",
)
class TestLoadRealDataWithoutAblation:
    """Test load_real_data when ablation file doesn't exist."""

    def test_load_without_ablation_uses_defaults(self):
        rng = np.random.default_rng(42)
        result = load_real_data(_EVAL_PATH, ablation_path=None, rng=rng)
        assert isinstance(result, dict)
        assert len(result["component_scores"]) > 0

    def test_load_with_missing_ablation_path(self, tmp_path):
        rng = np.random.default_rng(42)
        missing_ablation = tmp_path / "nonexistent_ablation.json"
        result = load_real_data(_EVAL_PATH, ablation_path=missing_ablation, rng=rng)
        assert isinstance(result, dict)
        # Should fall back to default component scores
        assert len(result["component_scores"]) > 0
