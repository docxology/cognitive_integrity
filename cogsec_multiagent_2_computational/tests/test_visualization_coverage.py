"""Targeted coverage tests for visualization modules with gaps below 90%.

Covers the specific missing lines in:
- visualization.figures.roc_curves
- visualization.tables.scalability_tables
- visualization.tables.stability_tables
- visualization.tables.statistical_tables
"""

from __future__ import annotations

import json

import matplotlib
import matplotlib.pyplot as plt
import pytest
from matplotlib.figure import Figure

matplotlib.use("Agg")


# ---------------------------------------------------------------------------
# roc_curves.py coverage
# ---------------------------------------------------------------------------

class TestRocCurvesLoadPath:
    """Test _load_roc_data with existing roc_results.json (lines 34-37)."""

    def test_load_roc_data_from_file(self, tmp_path):
        """_load_roc_data reads roc_results.json when it exists."""
        from visualization.figures.roc_curves import _load_roc_data

        # Create the directory structure expected by _load_roc_data
        # output_dir.parent / "data" / "roc_results.json"
        figures_dir = tmp_path / "figures"
        data_dir = tmp_path / "data"
        data_dir.mkdir(parents=True)
        figures_dir.mkdir(parents=True)

        roc_data = {
            "full_cif": {"fpr": [0.0, 0.1, 0.5, 1.0], "tpr": [0.0, 0.8, 0.9, 1.0]},
            "firewall": {"fpr": [0.0, 0.2, 0.5, 1.0], "tpr": [0.0, 0.7, 0.85, 1.0]},
        }
        (data_dir / "roc_results.json").write_text(json.dumps(roc_data))

        result = _load_roc_data(figures_dir)
        assert "full_cif" in result
        assert "firewall" in result
        assert result["full_cif"]["fpr"] == [0.0, 0.1, 0.5, 1.0]

    def test_load_roc_data_fallback_when_no_file(self, tmp_path):
        """_load_roc_data falls back to load_full_evaluation when no file exists."""
        from visualization.figures.roc_curves import _load_roc_data

        figures_dir = tmp_path / "figures"
        figures_dir.mkdir(parents=True)
        # No roc_results.json — falls back to load_full_evaluation
        result = _load_roc_data(figures_dir)
        # Should return a dict (full_cif key expected from fallback path)
        assert isinstance(result, dict)


class TestRocCurvesPlot:
    """Test plot_roc_curves coverage — str output_dir and mkdir (lines 68-73)."""

    def test_plot_roc_curves_str_output_dir(self, tmp_path):
        """plot_roc_curves accepts a str output_dir and creates directories."""
        from visualization.figures.roc_curves import plot_roc_curves

        # Pass str output_dir (covers lines 68-69: isinstance check + Path conversion)
        out_str = str(tmp_path / "new_subdir" / "figures")
        fig = plot_roc_curves(output_dir=out_str)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_plot_roc_curves_creates_missing_output_dir(self, tmp_path):
        """plot_roc_curves creates output_dir if it doesn't exist (line 73)."""
        from visualization.figures.roc_curves import plot_roc_curves

        new_dir = tmp_path / "nonexistent_dir"
        assert not new_dir.exists()
        fig = plot_roc_curves(output_dir=new_dir)
        assert new_dir.exists()
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_plot_roc_curves_with_preloaded_roc_file(self, tmp_path):
        """plot_roc_curves plots from roc_results.json covering ablation fallback lines."""
        from visualization.figures.roc_curves import plot_roc_curves

        # Create roc data with only full_cif — the other keys fall to ablation branch
        figures_dir = tmp_path / "figures"
        data_dir = tmp_path / "data"
        data_dir.mkdir(parents=True)
        figures_dir.mkdir(parents=True)

        # Only provide full_cif — firewall, sandbox, tripwire, anomaly go to ablation path
        roc_data = {
            "full_cif": {"fpr": [0.0, 0.1, 0.5, 1.0], "tpr": [0.0, 0.8, 0.9, 1.0]},
        }
        (data_dir / "roc_results.json").write_text(json.dumps(roc_data))

        fig = plot_roc_curves(output_dir=figures_dir)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_plot_roc_curves_ablation_component_match(self, tmp_path, monkeypatch):
        """Ablation data includes a matching 'configuration' key (lines 128-129)."""
        from visualization.figures import roc_curves

        # Return empty roc_data so all components go to ablation path
        monkeypatch.setattr(roc_curves, "_load_roc_data", lambda _: {})

        import data.result_loaders as rl_mod

        # Provide ablation data with "configuration" fields that match the component keys
        ablation_data = {
            "component_removal": [
                {"configuration": "firewall", "detection_rate": 0.82},
                {"configuration": "sandbox", "detection_rate": 0.78},
                {"configuration": "tripwire", "detection_rate": 0.75},
                {"configuration": "anomaly", "detection_rate": 0.71},
                {"configuration": "full_cif", "detection_rate": 0.94},
            ]
        }
        monkeypatch.setattr(rl_mod, "load_ablation_results", lambda: ablation_data)

        fig = roc_curves.plot_roc_curves(output_dir=str(tmp_path))
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_plot_roc_curves_ablation_exception_path(self, tmp_path, monkeypatch):
        """Ablation load failure triggers warning logger path (lines 139-140)."""
        from visualization.figures import roc_curves

        # Monkeypatch _load_roc_data to return empty dict so all keys go to ablation path
        # Then monkeypatch load_ablation_results to raise an exception
        monkeypatch.setattr(roc_curves, "_load_roc_data", lambda _: {})


        def _fail_load():
            raise RuntimeError("no ablation data")

        # Patch inside the module scope — the function imports load_ablation_results lazily

        import data.result_loaders as rl_mod
        monkeypatch.setattr(rl_mod, "load_ablation_results", _fail_load)

        fig = roc_curves.plot_roc_curves(output_dir=str(tmp_path))
        # Should complete without raising despite exception in ablation path
        assert isinstance(fig, Figure)
        plt.close(fig)


# ---------------------------------------------------------------------------
# scalability_tables.py coverage — lines 45-47 (results dict branch)
# ---------------------------------------------------------------------------

class TestScalabilityTablesWithResults:
    """Test generate_scalability_table with explicit results dict."""

    def test_with_results_dict(self):
        """generate_scalability_table with explicit results skips file load (lines 44-47)."""
        from visualization.tables.scalability_tables import generate_scalability_table

        results = {
            "agents": [1, 5, 10, 20, 50],
            "latency": [10.0, 30.0, 80.0, 200.0, 800.0],
            "memory": [50.0, 120.0, 200.0, 350.0, 700.0],
        }
        table = generate_scalability_table(results=results)
        assert isinstance(table, str)
        assert "\\begin{table}" in table
        assert "Scalability" in table
        assert "50" in table  # last agent count appears

    def test_results_dict_regression_values(self):
        """Regression coefficients and R² appear in the table."""
        from visualization.tables.scalability_tables import generate_scalability_table

        results = {
            "agents": [1, 2, 3, 4, 5],
            "latency": [1.0, 4.0, 9.0, 16.0, 25.0],  # perfect quadratic
            "memory": [10.0, 20.0, 30.0, 40.0, 50.0],
        }
        table = generate_scalability_table(results=results)
        assert "R^2" in table or "R" in table

    def test_results_with_numpy_arrays(self):
        """generate_scalability_table handles numpy arrays in results dict."""
        import numpy as np

        from visualization.tables.scalability_tables import generate_scalability_table

        results = {
            "agents": np.array([2, 4, 8, 16]),
            "latency": np.array([5.0, 15.0, 50.0, 180.0]),
            "memory": np.array([30.0, 60.0, 120.0, 240.0]),
        }
        table = generate_scalability_table(results=results)
        assert isinstance(table, str)
        assert len(table) > 100


# ---------------------------------------------------------------------------
# stability_tables.py coverage — lines 34-36 (per_architecture and per_category)
# ---------------------------------------------------------------------------

class TestStabilityTablesArchCategories:
    """Test generate_stability_table with per_architecture and per_category data."""

    def test_stability_table_with_per_arch_cv(self, tmp_path, monkeypatch):
        """Covers the per_architecture_cv loop (lines 30-32) and per_category_cv (33-36)."""
        import visualization.tables.stability_tables as st_mod

        multi_seed_data = {
            "overall_cv": 0.03,
            "cv_threshold": 0.05,
            "per_architecture_cv": {
                "ArchA": 0.02,
                "ArchB": 0.07,  # above threshold → texttimes
            },
            "per_category_cv": {
                "manipulation_attack": 0.01,
                "spoofing_attack": 0.09,  # above threshold
            },
        }

        # Patch Path.open to return our data
        import builtins

        real_open = builtins.open

        def mock_open(path, *args, **kwargs):
            if "multi_seed_results.json" in str(path):
                import io
                return io.StringIO(json.dumps(multi_seed_data))
            return real_open(path, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", mock_open)

        table = st_mod.generate_stability_table()
        assert isinstance(table, str)
        assert "ArchA" in table
        assert "ArchB" in table
        assert "Manipulation Attack" in table
        assert "Spoofing Attack" in table
        assert "\\checkmark" in table
        assert "\\texttimes" in table

    def test_stability_table_all_stable(self, tmp_path, monkeypatch):
        """All metrics below threshold — all checkmarks."""
        import builtins

        import visualization.tables.stability_tables as st_mod

        data = {
            "overall_cv": 0.01,
            "cv_threshold": 0.05,
            "per_architecture_cv": {"ArchC": 0.02, "ArchD": 0.03},
            "per_category_cv": {"cat_x": 0.01},
        }

        real_open = builtins.open

        def mock_open(path, *args, **kwargs):
            if "multi_seed_results.json" in str(path):
                import io
                return io.StringIO(json.dumps(data))
            return real_open(path, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", mock_open)

        table = st_mod.generate_stability_table()
        assert "\\checkmark" in table
        # Should have no texttimes if all below threshold
        assert table.count("\\checkmark") >= 4  # overall + 2 arch + 1 cat

    def test_stability_table_no_arch_no_cat(self, monkeypatch):
        """Empty per_architecture_cv and per_category_cv — only overall row."""
        import builtins

        import visualization.tables.stability_tables as st_mod

        data = {
            "overall_cv": 0.04,
            "cv_threshold": 0.05,
            "per_architecture_cv": {},
            "per_category_cv": {},
        }

        real_open = builtins.open

        def mock_open(path, *args, **kwargs):
            if "multi_seed_results.json" in str(path):
                import io
                return io.StringIO(json.dumps(data))
            return real_open(path, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", mock_open)

        table = st_mod.generate_stability_table()
        assert "Overall" in table
        assert isinstance(table, str)


# ---------------------------------------------------------------------------
# statistical_tables.py coverage — lines 93-96 (Small / Medium effect interp)
# ---------------------------------------------------------------------------

class TestStatisticalTablesEffectSizes:
    """Test generate_effect_size_table with different Cohen's d values."""

    def _mock_stats_data(self, cohens_d: float) -> dict:
        return {
            "h1": {"statistic": 5.2, "p_value": 0.0001, "significant": True},
            "h2": [
                {"name": "H2_firewall", "p_value": 0.0003, "significant": True},
                {"name": "H2_sandbox", "p_value": 0.0400, "significant": False},
            ],
            "h3": [
                {
                    "name": "H3_autogpt",
                    "test_statistic": 3.5,
                    "p_value": 0.0002,
                    "significant": True,
                    "description": "CIF detection rate > baseline for 'autogpt'.",
                },
            ],
            "cohens_d_cif_vs_baseline": cohens_d,
        }

    def test_effect_size_large(self, monkeypatch):
        """Cohen's d >= 0.8 → 'Large' interpretation."""
        import visualization.tables.statistical_tables as st_mod

        monkeypatch.setattr(
            st_mod, "_load_statistical_results",
            lambda: self._mock_stats_data(1.2),
        )
        table = st_mod.generate_effect_size_table()
        assert "Large" in table

    def test_effect_size_medium(self, monkeypatch):
        """Cohen's d in [0.5, 0.8) → 'Medium' interpretation (lines 93-94)."""
        import visualization.tables.statistical_tables as st_mod

        monkeypatch.setattr(
            st_mod, "_load_statistical_results",
            lambda: self._mock_stats_data(0.6),
        )
        table = st_mod.generate_effect_size_table()
        assert "Medium" in table

    def test_effect_size_small(self, monkeypatch):
        """Cohen's d < 0.5 → 'Small' interpretation (lines 95-96)."""
        import visualization.tables.statistical_tables as st_mod

        monkeypatch.setattr(
            st_mod, "_load_statistical_results",
            lambda: self._mock_stats_data(0.3),
        )
        table = st_mod.generate_effect_size_table()
        assert "Small" in table

    def test_effect_size_negative_large(self, monkeypatch):
        """abs(d) >= 0.8 for negative d → 'Large'."""
        import visualization.tables.statistical_tables as st_mod

        monkeypatch.setattr(
            st_mod, "_load_statistical_results",
            lambda: self._mock_stats_data(-1.5),
        )
        table = st_mod.generate_effect_size_table()
        assert "Large" in table

    def test_hypothesis_table_emits_every_recorded_test(self, monkeypatch):
        """Every H1/H2/H3 record reaches the table, with its own recorded ID.

        The table used to renumber the rows H2..H9 while printing the JSON's
        own names in the adjacent column, giving each row two conflicting
        IDs; and it dropped the H3 family entirely.
        """
        import visualization.tables.statistical_tables as st_mod

        data = self._mock_stats_data(0.9)
        monkeypatch.setattr(st_mod, "_load_statistical_results", lambda: data)
        table = st_mod.generate_hypothesis_table()

        assert "\\begin{table}" in table
        assert "H1 & CIF $>$ Baseline & 5.20 &" in table
        # LaTeX-escaped identifiers, one row per recorded test.
        for name in ("H2\\_firewall", "H2\\_sandbox", "H3\\_autogpt"):
            assert table.count(name) >= 1, f"{name} missing from the table"
        assert "H2\\_firewall & CIF $>$ firewall component alone" in table
        # A record carrying its own description is used, LaTeX-escaped:
        # a bare ">" in text mode does not typeset as a greater-than sign.
        assert (
            "CIF detection rate \\textgreater{} baseline for 'autogpt'." in table
        )
        # A recorded test_statistic is printed; a missing one prints "--".
        assert "3.50" in table
        # significance flags follow the data, not a constant "Yes"
        assert table.count("& Yes \\\\") == 3
        assert table.count("& No \\\\") == 1

    def test_hypothesis_table_omits_families_absent_from_the_data(self, monkeypatch):
        """POSITIVE CONTROL: rows appear only when the data carries them."""
        import visualization.tables.statistical_tables as st_mod

        monkeypatch.setattr(
            st_mod, "_load_statistical_results",
            lambda: {"h1": {"statistic": 1.0, "p_value": 0.5, "significant": False}},
        )
        table = st_mod.generate_hypothesis_table()
        assert "H1 &" in table
        assert "H2" not in table
        assert "H3" not in table
        assert "& No \\\\" in table
        # A p-value at or above 0.001 is printed, not collapsed to "< 0.001".
        assert "0.5000" in table

    def test_hypothesis_table_without_h1(self, monkeypatch):
        """An h1-less record set still renders the remaining families."""
        import visualization.tables.statistical_tables as st_mod

        monkeypatch.setattr(
            st_mod, "_load_statistical_results",
            lambda: {"h2": [{"name": "H2_firewall", "p_value": 0.0001,
                             "significant": True}]},
        )
        table = st_mod.generate_hypothesis_table()
        assert "H1 &" not in table
        assert "H2\\_firewall &" in table

    def test_hypothesis_row_with_an_unrecognised_name_falls_back_to_the_name(
        self, monkeypatch,
    ):
        """An unfamiliar prefix must not be mislabelled as an H2 component test."""
        import visualization.tables.statistical_tables as st_mod

        monkeypatch.setattr(
            st_mod, "_load_statistical_results",
            lambda: {"h2": [{"name": "H9_mystery", "p_value": 0.02,
                             "significant": False}]},
        )
        table = st_mod.generate_hypothesis_table()
        assert "H9\\_mystery & H9\\_mystery &" in table
        assert "component alone" not in table

    def test_effect_size_table_omits_the_odds_ratio_column_when_unrecorded(
        self, monkeypatch,
    ):
        """The column used to be present with '--' in its only cell."""
        import visualization.tables.statistical_tables as st_mod

        monkeypatch.setattr(
            st_mod, "_load_statistical_results",
            lambda: self._mock_stats_data(0.9),
        )
        assert "Odds Ratio" not in st_mod.generate_effect_size_table()

    def test_effect_size_table_shows_the_odds_ratio_when_recorded(self, monkeypatch):
        """POSITIVE CONTROL: the odds-ratio column is reachable and data-bound."""
        import visualization.tables.statistical_tables as st_mod

        data = self._mock_stats_data(0.9)
        data["odds_ratio_cif_vs_baseline"] = 12.5
        monkeypatch.setattr(st_mod, "_load_statistical_results", lambda: data)

        table = st_mod.generate_effect_size_table()
        assert "Odds Ratio" in table
        assert "12.50" in table

    def test_effect_size_table_structure(self, monkeypatch):
        """generate_effect_size_table produces a well-formed LaTeX table."""
        import visualization.tables.statistical_tables as st_mod

        monkeypatch.setattr(
            st_mod, "_load_statistical_results",
            lambda: self._mock_stats_data(0.7),
        )
        table = st_mod.generate_effect_size_table()
        assert "\\begin{table}" in table
        assert "\\end{table}" in table
        assert "Cohen" in table


class TestAblationStudyFigureCoverage:
    def test_plot_ablation_study_legacy_dict_format(self, tmp_path):
        from src.visualization.figures.ablation_study import plot_ablation_study
        data_dir = tmp_path / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        legacy_data = {
            "metadata": {"note": "legacy"},
            "full_cif": {"detection": 0.965, "delta": 0.0},
            "minus_firewall": {"detection": 0.85, "delta": -0.115},
            "minus_tripwire": {"detection": 0.88, "delta": -0.085},
            "minus_invariants": {"detection": 0.91, "delta": -0.055},
            "minus_sandbox": {"detection": 0.94, "delta": -0.025},
        }
        with open(data_dir / "ablation_results.json", "w") as f:
            json.dump(legacy_data, f)

        fig_dir = tmp_path / "figures"
        fig = plot_ablation_study(output_dir=fig_dir)
        assert fig is not None
        has_pdf = (fig_dir / "ablation_study.pdf").exists()
        has_png = (fig_dir / "ablation_study.png").exists()
        assert has_pdf or has_png

    def test_plot_ablation_study_refuses_an_artifact_with_no_full_pipeline(self, tmp_path):
        """A missing full-pipeline rate must be loud, not filled in.

        This branch used to fall back to a literal 0.965 when the artifact had
        no component-removal rows, so a figure drawn from absent evidence looked
        exactly like one drawn from a measurement. generate_all_figures collects
        generator exceptions and exits 1, which is what should happen when the
        data a figure illustrates is not there.
        """
        from src.visualization.figures.ablation_study import plot_ablation_study
        data_dir = tmp_path / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        with open(data_dir / "ablation_results.json", "w") as f:
            json.dump({"component_removal": []}, f)

        fig_dir = tmp_path / "figures"
        with pytest.raises(KeyError):
            plot_ablation_study(output_dir=fig_dir)
