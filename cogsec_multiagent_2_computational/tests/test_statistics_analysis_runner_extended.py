"""Additional tests for src/statistics/analysis_runner.py — load_real_data path.

Covers the load_real_data function, which requires real data files, and the
fail-closed contract around the ablation input: component scores come from the
measured ablation file or the run stops. There is no default table any more.

Uses the existing output/data directory which is populated by conftest.py.
"""

from __future__ import annotations

import json
from pathlib import Path
from statistics.analysis_runner import (
    AblationDataUnavailableError,
    load_real_data,
    run_full_analysis,
)

import numpy as np
import pytest

#: Per-component means the deleted fallback used to invent. If any of these
#: reappears in a component score distribution, the fallback is back.
_FABRICATED_COMPONENT_MEANS = {
    "firewall": 0.82,
    "trust_calculus": 0.71,
    "tripwire": 0.68,
    "detection": 0.74,
    "consensus": 0.65,
    "provenance": 0.60,
    "sandbox": 0.58,
    "invariants": 0.63,
}

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

    def test_simulated_control_false_fails_closed(self):
        """Requesting a real (non-simulated) control arm is impossible
        because no undefended control was ever run, so load_real_data
        must refuse rather than fabricate a baseline (P2-15)."""
        rng = np.random.default_rng(42)
        with pytest.raises(ValueError, match="no observed control arm|opt in"):
            load_real_data(_EVAL_PATH, _ABLATION_PATH, rng, simulated_control=False)

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

    def test_component_names_come_from_the_ablation_file(self, loaded):
        """The component set is whatever the file says, not a fixed table."""
        measured = {
            row["removed"] for row in json.loads(_ABLATION_PATH.read_text())["component_removal"]
        }
        assert set(loaded["component_scores"]) == measured

    def test_component_means_track_the_measured_tprs(self, loaded):
        """Each distribution is centred on its own measured TPR.

        Positive control against the deleted fallback: the invented means
        (firewall 0.82, detection 0.74, ...) are nowhere near the measured
        ones, so this assertion fails immediately if defaults come back.
        """
        rows = {
            row["removed"]: float(row["tpr"])
            for row in json.loads(_ABLATION_PATH.read_text())["component_removal"]
        }
        for name, arr in loaded["component_scores"].items():
            observed = float(np.mean(arr))
            assert observed == pytest.approx(rows[name], abs=0.02), name
            fabricated = _FABRICATED_COMPONENT_MEANS.get(name)
            if fabricated is not None:
                assert abs(observed - fabricated) > 0.02, (
                    f"{name} is centred on the deleted fallback mean {fabricated}"
                )


@pytest.mark.skipif(
    not _EVAL_PATH.exists(),
    reason="output/data/full_evaluation_results.json not found",
)
class TestAblationDataIsMandatory:
    """load_real_data fails closed instead of inventing component scores."""

    @pytest.mark.parametrize(
        ("payload", "expected_fragment"),
        [
            pytest.param({}, "component_removal", id="empty_object"),
            pytest.param({"component_removal": []}, "component_removal", id="empty_rows"),
            pytest.param({"full_pipeline": {"tpr": 0.12}}, "component_removal", id="rows_renamed"),
            pytest.param(
                {"component_removal": [{"tpr": 0.07}]}, "'removed'", id="row_lost_removed"
            ),
            pytest.param(
                {"component_removal": [{"removed": "detection"}]},
                "'tpr'",
                id="row_lost_tpr",
            ),
            pytest.param(
                {"component_removal": [{"removed": "detection", "tpr": "n/a"}]},
                "not a",
                id="tpr_not_a_number",
            ),
            pytest.param([1, 2, 3], "not a JSON object", id="top_level_list"),
            pytest.param(
                {"component_removal": ["detection"]},
                "is not an object",
                id="row_is_a_bare_string",
            ),
        ],
    )
    def test_schema_damage_raises(self, tmp_path, payload, expected_fragment):
        ablation = tmp_path / "ablation_results.json"
        ablation.write_text(json.dumps(payload))
        rng = np.random.default_rng(42)

        with pytest.raises(AblationDataUnavailableError) as excinfo:
            load_real_data(_EVAL_PATH, ablation_path=ablation, rng=rng)

        message = str(excinfo.value)
        assert expected_fragment in message
        assert str(ablation) in message or "ablation" in message

    def test_truncated_file_raises(self, tmp_path):
        """A half-written JSON file is an error, not a silent default."""
        ablation = tmp_path / "ablation_results.json"
        full = json.dumps({"component_removal": [{"removed": "detection", "tpr": 0.071}]})
        ablation.write_text(full[: len(full) // 2])
        rng = np.random.default_rng(42)

        with pytest.raises(AblationDataUnavailableError, match="not valid JSON"):
            load_real_data(_EVAL_PATH, ablation_path=ablation, rng=rng)

        # Positive control: the same call on the untruncated file succeeds, so
        # the raise above is caused by the truncation and not by the fixture.
        ablation.write_text(full)
        result = load_real_data(_EVAL_PATH, ablation_path=ablation, rng=rng)
        assert set(result["component_scores"]) == {"detection"}

    def test_absent_file_raises_and_names_it(self, tmp_path):
        rng = np.random.default_rng(42)
        missing = tmp_path / "nonexistent_ablation.json"

        with pytest.raises(AblationDataUnavailableError) as excinfo:
            load_real_data(_EVAL_PATH, ablation_path=missing, rng=rng)

        assert "nonexistent_ablation.json" in str(excinfo.value)

    def test_none_path_raises(self):
        rng = np.random.default_rng(42)
        with pytest.raises(AblationDataUnavailableError):
            load_real_data(_EVAL_PATH, ablation_path=None, rng=rng)

    def test_no_fabricated_component_survives_a_failure(self, tmp_path):
        """Nothing is returned on failure — not even a partial dict."""
        ablation = tmp_path / "ablation_results.json"
        ablation.write_text(
            json.dumps(
                {
                    "component_removal": [
                        {"removed": "detection", "tpr": 0.071},
                        {"removed": "firewall"},  # schema damage on row 2
                    ]
                }
            )
        )
        rng = np.random.default_rng(42)

        with pytest.raises(AblationDataUnavailableError, match=r"\[1\]"):
            load_real_data(_EVAL_PATH, ablation_path=ablation, rng=rng)
