#!/usr/bin/env python3
"""Tests for visualization modules.

This test module covers all visualization functions to ensure they generate
figures correctly without errors.
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend

import matplotlib.pyplot as plt
import pytest


@pytest.fixture
def detection_inputs(tmp_path):
    """Complete test-only inputs, never producer or manuscript evidence."""
    output_dir = tmp_path / "figures"
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True)
    configs = [
        {
            "name": name,
            "detection_rates": {"prompt_injection": rate, "trust_exploitation": rate},
            "latency_overhead_pct": latency,
        }
        for name, rate, latency in (
            ("Baseline", 0.1, 0),
            ("Firewall Only", 0.8, 8),
            ("Full CIF", 0.9, 23),
        )
    ]
    (data_dir / "detection_results.json").write_text(
        json.dumps({"defense_configurations": configs}), encoding="utf-8"
    )
    component_rates = {
        "full_cif": 0.94,
        "minus_firewall": 0.81,
        "minus_sandbox": 0.88,
        "minus_tripwires": 0.85,
        "minus_invariants": 0.89,
        "minus_trust_decay": 0.91,
    }
    ablation = {"metadata": {"illustrative": True}}
    ablation.update({key: {"detection": rate} for key, rate in component_rates.items()})
    (data_dir / "ablation_study.json").write_text(json.dumps(ablation), encoding="utf-8")
    (data_dir / "integrity_timeseries.csv").write_text(
        "attack_attempt,baseline_integrity,firewall_integrity,full_cif_integrity\n"
        "0,0.45,0.75,0.96\n10,0.44,0.745,0.959\n",
        encoding="utf-8",
    )
    return output_dir


class TestVisualizationUtils:
    """Tests for visualization/utils.py functions."""

    def test_setup_plotting(self):
        """Test setup_plotting configures matplotlib correctly."""
        from src.visualization.utils import setup_plotting

        setup_plotting()

        # Verify key settings were applied (font.family returns a list)
        assert "serif" in plt.rcParams["font.family"]
        assert plt.rcParams["font.size"] == 14
        assert plt.rcParams["axes.labelsize"] == 14
        assert plt.rcParams["figure.dpi"] == 300

    def test_get_color_palette(self):
        """Test get_color_palette returns IBM colorblind-safe colors."""
        from src.visualization.utils import get_color_palette

        palette = get_color_palette()

        assert isinstance(palette, list)
        assert len(palette) == 5
        # Verify IBM Design palette colors
        assert "#648FFF" in palette  # Blue
        assert "#DC267F" in palette  # Magenta
        assert "#FFB000" in palette  # Yellow

    def test_save_figure_creates_files(self):
        """Test save_figure creates PNG and PDF files."""
        from src.visualization.utils import save_figure

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            fig, ax = plt.subplots()
            ax.plot([1, 2, 3], [1, 2, 3])

            result = save_figure(fig, output_dir, "test_figure")
            plt.close(fig)

            assert (output_dir / "test_figure.png").exists()
            assert (output_dir / "test_figure.pdf").exists()
            assert result == output_dir / "test_figure.pdf"

    def test_save_figure_creates_directory(self):
        """Test save_figure creates output directory if it doesn't exist."""
        from src.visualization.utils import save_figure

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "nested" / "output"
            fig, ax = plt.subplots()
            ax.plot([1, 2, 3], [1, 2, 3])

            save_figure(fig, output_dir, "test_figure")
            plt.close(fig)

            assert output_dir.exists()
            assert (output_dir / "test_figure.png").exists()


class TestTrustDecay:
    """Tests for visualization/trust_decay.py."""

    def test_generate_trust_decay_figure(self):
        """Test trust decay figure generation."""
        from src.visualization.trust_decay import generate_trust_decay_figure

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = generate_trust_decay_figure(output_dir)

            assert result.exists()
            assert result.suffix == ".pdf"
            assert "trust_decay" in result.name

    def test_generate_trust_decay_creates_directory(self):
        """Test that function creates directory if missing."""
        from src.visualization.trust_decay import generate_trust_decay_figure

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "nested"
            result = generate_trust_decay_figure(output_dir)

            assert output_dir.exists()
            assert result.exists()

    def test_decay_curves_match_caption_domain(self, monkeypatch):
        import numpy as np

        from src.visualization.trust_decay import generate_trust_decay_figure

        monkeypatch.setattr(plt, "close", lambda *args, **kwargs: None)
        with tempfile.TemporaryDirectory() as tmpdir:
            generate_trust_decay_figure(Path(tmpdir))
            ax = plt.gcf().axes[0]
            curves = {
                float(line.get_label().split("=")[1]): line
                for line in ax.lines
                if line.get_label().startswith("$\\delta$")
            }
            assert set(curves) == {0.5, 0.7, 0.8, 0.9}
            for delta, line in curves.items():
                np.testing.assert_array_equal(line.get_xdata(), np.arange(1, 11))
                np.testing.assert_allclose(line.get_ydata(), delta ** np.arange(1, 11))
            assert ax.get_xlim() == (1.0, 10.0)


class TestAblationStudy:
    """Tests for visualization/ablation_study.py."""

    def test_create_ablation_study_figure(self):
        """Test ablation study figure generation."""
        from src.visualization.ablation_study import create_ablation_study_figure

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "figures"
            result = create_ablation_study_figure(output_dir)

            assert result.exists()
            assert result.suffix == ".pdf"
            assert "ablation_study" in result.name

    def test_create_ablation_study_with_data_file(self):
        """Test ablation study with actual data file."""
        from src.visualization.ablation_study import create_ablation_study_figure

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create data directory and file
            output_dir = Path(tmpdir) / "figures"
            data_dir = output_dir / "data"
            data_dir.mkdir(parents=True)

            data = {
                "full_cif": {"detection": 0.94, "delta": 0.0},
                "minus_firewall": {"detection": 0.81, "delta": -0.13},
                "minus_sandbox": {"detection": 0.88, "delta": -0.06},
            }
            with open(data_dir / "ablation_study.json", "w") as f:
                json.dump(data, f)

            result = create_ablation_study_figure(output_dir)

            assert result.exists()


class TestAttackSurface:
    """Tests for visualization/attack_surface.py."""

    def test_generate_attack_surface_figure(self):
        """Test attack surface figure generation."""
        from src.visualization.attack_surface import generate_attack_surface_figure

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = generate_attack_surface_figure(output_dir)

            assert result.exists()
            assert result.suffix == ".pdf"


class TestAttackTimeline:
    """Tests for visualization/attack_timeline.py."""

    def test_create_attack_timeline_figure(self):
        """Test attack timeline figure generation."""
        from src.visualization.attack_timeline import create_attack_timeline_figure

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = create_attack_timeline_figure(output_dir)

            # Returns tuple (png, pdf)
            if isinstance(result, tuple):
                png_path, pdf_path = result
                assert pdf_path.exists()
            else:
                assert result.exists()


class TestBeliefSandbox:
    """Tests for visualization/belief_sandbox.py."""

    def test_create_belief_sandbox_figure(self):
        """Test belief sandbox figure generation."""
        from src.visualization.belief_sandbox import create_belief_sandbox_figure

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = create_belief_sandbox_figure(output_dir)

            # Returns tuple (png, pdf)
            if isinstance(result, tuple):
                png_path, pdf_path = result
                assert pdf_path.exists()
            else:
                assert result.exists()


class TestCIFArchitecture:
    """Tests for visualization/cif_architecture.py."""

    def test_create_cif_architecture_figure(self):
        """Test CIF architecture figure generation."""
        from src.visualization.cif_architecture import create_cif_architecture_figure

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = create_cif_architecture_figure(output_dir)

            assert result.exists()
            assert result.suffix == ".pdf"


class TestCIFComprehensive:
    """Tests for visualization/cif_comprehensive.py."""

    def test_create_cif_comprehensive_figure(self):
        """Test CIF comprehensive figure generation."""
        from src.visualization.cif_comprehensive import create_cif_comprehensive_figure

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = create_cif_comprehensive_figure(output_dir)

            assert result.exists()
            assert result.suffix == ".pdf"


class TestComprehensiveTaxonomy:
    """Tests for visualization/comprehensive_taxonomy.py."""

    def test_create_comprehensive_taxonomy_figure(self, monkeypatch):
        """Test taxonomy generation and its detection-difficulty semantics."""
        from src.visualization.comprehensive_taxonomy import create_comprehensive_taxonomy_figure

        monkeypatch.setattr(plt, "close", lambda *args, **kwargs: None)
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = create_comprehensive_taxonomy_figure(output_dir)

            assert result.exists()
            assert result.suffix == ".pdf"
            texts = [text.get_text() for ax in plt.gcf().axes for text in ax.texts]
            assert "Detection difficulty: " in texts
            assert "High (<60%)" in texts
            assert "Medium (60-79%)" in texts
            assert "Low (≥80%)" in texts
            assert "High (≥80%)" not in texts
            assert "Low (<60%)" not in texts


class TestDefenseComposition:
    """Tests for visualization/defense_composition.py."""

    def test_create_defense_composition_figure(self, monkeypatch):
        """Test defense composition generation and triple-region membership."""
        from src.visualization.defense_composition import create_defense_composition_figure

        monkeypatch.setattr(plt, "close", lambda *args, **kwargs: None)
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = create_defense_composition_figure(output_dir)

            assert isinstance(result, tuple)
            assert result[1].exists()
            ax = plt.gcf().axes[0]
            circles = list(ax.patches)[:4]
            for label, expected_membership in (
                ("Coordinated\nAttacks", (True, False, True, True)),
                ("Gradual\nDrift", (False, True, True, True)),
            ):
                text = next(item for item in ax.texts if item.get_text() == label)
                x, y = text.get_position()
                membership = tuple(
                    (x - circle.center[0]) ** 2 + (y - circle.center[1]) ** 2
                    < circle.radius**2
                    for circle in circles
                )
                assert membership == expected_membership


class TestDetectionPerformance:
    """Tests for visualization/detection_performance.py."""

    def test_create_detection_performance_figure(self):
        """Test detection performance figure generation."""
        from src.visualization.detection_performance import create_detection_performance_figure

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = create_detection_performance_figure(output_dir)

            assert result.exists()
            assert result.suffix == ".pdf"


class TestDetectionResults:
    """Tests for visualization/detection_results.py."""

    def test_create_detection_results_figure(self, detection_inputs):
        """Complete artifacts produce both formats and the documented PDF path."""
        from src.visualization.detection_results import create_detection_results_figure

        result = create_detection_results_figure(detection_inputs)
        assert result == detection_inputs / "detection_results.pdf"
        assert result.is_file()
        assert (detection_inputs / "detection_results.png").is_file()


class TestFPMitigation:
    """Tests for visualization/fp_mitigation.py."""

    def test_create_fp_mitigation_figure(self):
        """Test FP mitigation figure generation."""
        from src.visualization.fp_mitigation import create_fp_mitigation_figure

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = create_fp_mitigation_figure(output_dir)

            assert result.exists()
            assert result.suffix == ".pdf"


class TestROCCurves:
    """Tests for visualization/roc_curves.py."""

    def test_compute_roc_auc_normal(self):
        """Non-degenerate ROC curves use the trapezoidal rule."""
        import numpy as np

        from src.visualization.roc_curves import compute_roc_auc

        fpr = np.linspace(0, 1, 100)
        tpr = fpr  # diagonal -> AUC 0.5
        assert abs(compute_roc_auc(tpr, fpr) - 0.5) < 1e-3

    def test_compute_roc_auc_degenerate_constant_fpr(self):
        """A vertical segment at FPR=0 includes the half-area jump to (1, 1)."""
        import numpy as np

        from src.visualization.roc_curves import compute_roc_auc

        fpr = np.zeros(20)
        tpr = np.array([0.6] * 6 + [0.0] * 14)
        assert abs(compute_roc_auc(tpr, fpr) - 0.8) < 1e-12

    def test_compute_roc_auc_empty_returns_zero(self):
        from src.visualization.roc_curves import compute_roc_auc

        assert compute_roc_auc([], []) == 0.0

    def test_create_roc_curves_figure(self):
        """Test ROC curves figure generation."""
        from src.visualization.roc_curves import create_roc_curves_figure

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "figures"
            result = create_roc_curves_figure(output_dir)

            # Returns tuple (png, pdf)
            if isinstance(result, tuple):
                png_path, pdf_path = result
                assert pdf_path.exists()
            else:
                assert result.exists()

    def test_create_roc_curves_figure_with_data_file(self):
        """Test ROC curves figure with pre-populated roc_results.json data (measured path)."""
        import numpy as np

        from src.visualization.roc_curves import create_roc_curves_figure

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "figures"
            # Create the data directory relative to output_dir.parent/"data"
            data_dir = output_dir / "data"
            data_dir.mkdir(parents=True)

            # Create roc_results.json with firewall FPR/TPR data
            fpr = list(np.linspace(0, 1, 20))
            tpr = list(np.clip(np.linspace(0, 1, 20) ** 0.5, 0, 1))
            roc_data = {
                "firewall": {
                    "fpr": fpr,
                    "tpr": tpr,
                }
            }
            with open(data_dir / "roc_results.json", "w") as f:
                json.dump(roc_data, f)

            result = create_roc_curves_figure(output_dir)

            # Returns tuple (png, pdf)
            assert isinstance(result, tuple)
            png_path, pdf_path = result
            assert pdf_path.exists()
            assert png_path.exists()

    def test_degenerate_measured_points_are_visible(self, monkeypatch):
        from src.visualization.roc_curves import create_roc_curves_figure

        monkeypatch.setattr(plt, "close", lambda *args, **kwargs: None)
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "figures"
            data_dir = output_dir / "data"
            data_dir.mkdir(parents=True)
            (data_dir / "roc_results.json").write_text(json.dumps({
                "firewall": {"fpr": [0.0] * 20, "tpr": [0.5] * 20}
            }))

            create_roc_curves_figure(output_dir)
            ax = plt.gcf().axes[0]
            measured = next(
                line
                for line in ax.lines
                if line.get_label().startswith("Cognitive Firewall (Measured")
            )
            assert measured.get_marker() == "o"
            assert len(measured.get_xdata()) == 20
            assert "AUC=0.750" in measured.get_label()
            assert not ax.collections


class TestScalability:
    """Tests for visualization/scalability.py."""

    def test_create_scalability_figure(self, monkeypatch):
        """Test scalability figure generation with data file."""
        from src.visualization.scalability import create_scalability_figure

        monkeypatch.setattr(plt, "close", lambda *args, **kwargs: None)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "figures"
            data_dir = output_dir / "data"
            data_dir.mkdir(parents=True)

            # Create required scalability data
            data = [
                {
                    "agent_count": 4,
                    "detection_time_ms": 5.2,
                    "memory_mb": 12,
                    "consensus_latency_ms": 8,
                },
                {
                    "agent_count": 8,
                    "detection_time_ms": 5.5,
                    "memory_mb": 18,
                    "consensus_latency_ms": 25,
                },
                {
                    "agent_count": 16,
                    "detection_time_ms": 5.8,
                    "memory_mb": 32,
                    "consensus_latency_ms": 85,
                },
                {
                    "agent_count": 32,
                    "detection_time_ms": 6.1,
                    "memory_mb": 58,
                    "consensus_latency_ms": 310,
                },
            ]
            with open(data_dir / "scalability_results.json", "w") as f:
                json.dump(data, f)

            result = create_scalability_figure(output_dir)

            png_path, pdf_path = result
            assert png_path.is_file() and pdf_path.is_file()
            footer = " ".join(text.get_text() for text in plt.gcf().texts).lower()
            assert "analytic" in footer and "not measured" in footer


class TestThreatTaxonomy:
    """Tests for visualization/threat_taxonomy.py."""

    def test_create_threat_taxonomy_figure(self):
        """Test threat taxonomy figure generation."""
        from src.visualization.threat_taxonomy import create_threat_taxonomy_figure

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = create_threat_taxonomy_figure(output_dir)

            assert result.exists()
            assert result.suffix == ".pdf"


class TestTrustCalculus:
    """Tests for visualization/trust_calculus.py."""

    def test_create_trust_calculus_figure(self, monkeypatch):
        """Test trust calculus generation and internally consistent chain values."""
        from src.visualization.trust_calculus import create_trust_calculus_figure

        monkeypatch.setattr(plt, "close", lambda *args, **kwargs: None)
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = create_trust_calculus_figure(output_dir)

            assert result.exists()
            assert result.suffix == ".pdf"
            texts = [text.get_text() for ax in plt.gcf().axes for text in ax.texts]
            assert texts.count("T=1.00") == 2
            assert "T(A→B)=1.0" in texts
            assert "T(A→E) ≤ δ³·T(A→B) = 0.9³ × 1.0 = 0.73" in texts
            assert not any("Theorem 3.1" in text for text in texts)


class TestTrustNetwork:
    """Tests for visualization/trust_network.py."""

    def test_generate_trust_network_figure(self, monkeypatch):
        """Test distinct hierarchical/peer layouts and bidirectional edges."""
        from src.visualization.trust_network import generate_trust_network_figure

        monkeypatch.setattr(plt, "close", lambda *args, **kwargs: None)
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = generate_trust_network_figure(output_dir)

            assert isinstance(result, list) and result
            assert result[0].exists()
            fig = plt.gcf()
            assert fig.axes[0].get_title() == "A. Hierarchical Trust Network (illustrative)"
            assert fig.axes[1].get_title() == "B. Peer-to-peer Trust Network (illustrative)"
            left_nodes = [patch.center for patch in fig.axes[0].patches]
            right_nodes = [patch.center for patch in fig.axes[1].patches]
            assert left_nodes != right_nodes
            arrows = [
                text.arrow_patch
                for ax in fig.axes
                for text in ax.texts
                if not text.get_text() and getattr(text, "arrow_patch", None) is not None
            ]
            assert len(arrows) == 29
            assert all(type(arrow.get_arrowstyle()).__name__ == "CurveAB" for arrow in arrows)


class TestFigureDataIntegrityGuards:
    """Guard the P1-#10 / #11 data-integrity fixes (test gap #14)."""

    def test_detection_performance_is_visibly_schematic(self, monkeypatch):
        """The rendered figure, not merely its docstring, disclaims measurements."""
        from src.visualization.detection_performance import create_detection_performance_figure

        monkeypatch.setattr(plt, "close", lambda *args, **kwargs: None)
        with tempfile.TemporaryDirectory() as tmpdir:
            create_detection_performance_figure(Path(tmpdir))
            footer = " ".join(text.get_text() for text in plt.gcf().texts).lower()
            assert "schematic" in footer
            assert "not measured" in footer

    def test_detection_results_uses_only_measured_categories(self, monkeypatch, detection_inputs):
        """No fabricated categories; schematic panels retain explicit labels."""
        from src.visualization.detection_results import create_detection_results_figure

        monkeypatch.setattr(plt, "close", lambda *args, **kwargs: None)
        path = detection_inputs / "data" / "detection_results.json"
        data = json.loads(path.read_text())
        for config in data["defense_configurations"]:
            config["detection_rates"]["belief_manipulation"] = 0.3
        path.write_text(json.dumps(data))

        create_detection_results_figure(detection_inputs)
        ax = plt.gcf().axes[0]
        assert [tick.get_text() for tick in ax.get_xticklabels()] == [
            "Prompt\nInjection", "Trust\nExploit",
        ]
        assert len(ax.patches) == 6
        assert "illustrative, not measured" in plt.gcf().axes[1].get_title()
        assert "illustrative, not measured" in plt.gcf().axes[2].get_title()
        assert "not measured" in plt.gcf().axes[3].get_xlabel()

class TestDetectionResultsBranches:
    """Fail-closed boundaries for required artifact/configuration/numeric inputs."""

    @pytest.mark.parametrize(
        "filename", ("detection_results.json", "ablation_study.json", "integrity_timeseries.csv")
    )
    def test_data_missing_raises(self, detection_inputs, filename):
        from src.visualization.detection_results import create_detection_results_figure

        (detection_inputs / "data" / filename).unlink()
        figures_before = plt.get_fignums()
        with pytest.raises(FileNotFoundError, match=filename):
            create_detection_results_figure(detection_inputs)
        assert not list(detection_inputs.glob("*.pdf"))
        assert not list(detection_inputs.glob("*.png"))
        assert plt.get_fignums() == figures_before

    def test_with_ablation_and_integrity_data(self, monkeypatch, detection_inputs):
        """The supplied values, not fallback arrays or noise, reach the panels."""
        import numpy as np

        from src.visualization.detection_results import create_detection_results_figure

        monkeypatch.setattr(plt, "close", lambda *args, **kwargs: None)
        create_detection_results_figure(detection_inputs)
        axes = plt.gcf().axes
        np.testing.assert_allclose(
            [bar.get_width() for bar in axes[1].patches],
            [0.94, 0.81, 0.88, 0.85, 0.89, 0.91],
        )
        np.testing.assert_array_equal(axes[2].lines[0].get_xdata(), [0, 10])
        np.testing.assert_allclose(axes[2].lines[0].get_ydata(), [0.45, 0.44])
        np.testing.assert_allclose(axes[2].lines[1].get_ydata(), [0.75, 0.745])
        np.testing.assert_allclose(axes[2].lines[2].get_ydata(), [0.96, 0.959])

    @pytest.mark.parametrize("name", ("Baseline", "Firewall Only", "Full CIF"))
    def test_missing_config_raises(self, detection_inputs, name):
        from src.visualization.detection_results import create_detection_results_figure

        path = detection_inputs / "data" / "detection_results.json"
        data = json.loads(path.read_text())
        data["defense_configurations"] = [
            config for config in data["defense_configurations"] if config["name"] != name
        ]
        path.write_text(json.dumps(data))
        with pytest.raises(ValueError, match=name):
            create_detection_results_figure(detection_inputs)
        assert not list(detection_inputs.glob("*.pdf"))
        assert not list(detection_inputs.glob("*.png"))

    @pytest.mark.parametrize(
        ("field", "value"),
        (
            ("prompt_injection", None),
            ("trust_exploitation", "0.9"),
            ("prompt_injection", float("nan")),
            ("prompt_injection", True),
            ("trust_exploitation", 1.5),
            ("latency_overhead_pct", None),
            ("latency_overhead_pct", -1),
        ),
    )
    def test_invalid_numeric_field_raises(self, detection_inputs, field, value):
        from src.visualization.detection_results import create_detection_results_figure

        path = detection_inputs / "data" / "detection_results.json"
        data = json.loads(path.read_text())
        config = data["defense_configurations"][0]
        if field == "latency_overhead_pct":
            config[field] = value
        elif value is None:
            del config["detection_rates"][field]
        else:
            config["detection_rates"][field] = value
        path.write_text(json.dumps(data))
        with pytest.raises(ValueError, match="detection_results.json"):
            create_detection_results_figure(detection_inputs)
        assert not list(detection_inputs.glob("*.pdf"))
        assert not list(detection_inputs.glob("*.png"))

    @pytest.mark.parametrize(
        ("filename", "content"),
        (
            ("detection_results.json", "{invalid"),
            ("detection_results.json", "[]"),
            ("ablation_study.json", "{}"),
            ("ablation_study.json", "null"),
            ("integrity_timeseries.csv", ""),
            ("integrity_timeseries.csv", "attack_attempt,baseline_integrity\n0,0.4\n"),
            (
                "integrity_timeseries.csv",
                "attack_attempt,baseline_integrity,firewall_integrity,full_cif_integrity\n"
                "0,0.4,nan,0.9\n",
            ),
            (
                "integrity_timeseries.csv",
                "attack_attempt,baseline_integrity,firewall_integrity,full_cif_integrity\n",
            ),
        ),
    )
    def test_malformed_artifact_raises(self, detection_inputs, filename, content):
        from src.visualization.detection_results import create_detection_results_figure

        (detection_inputs / "data" / filename).write_text(content)
        with pytest.raises(ValueError, match=filename):
            create_detection_results_figure(detection_inputs)
        assert not list(detection_inputs.glob("*.pdf"))
        assert not list(detection_inputs.glob("*.png"))

class TestScalabilityBranches:
    def test_data_missing_raises(self, tmp_path):
        from src.visualization.scalability import create_scalability_figure

        output_dir = tmp_path / "figures"
        figures_before = plt.get_fignums()
        with pytest.raises(FileNotFoundError, match="scalability_results.json"):
            create_scalability_figure(output_dir)
        assert not output_dir.exists()
        assert plt.get_fignums() == figures_before

    @pytest.mark.parametrize(
        "content",
        (
            "{invalid",
            "[]",
            "{}",
            '[{"agent_count": 4}]',
            '[{"agent_count": 0, "detection_time_ms": 1, '
            '"memory_mb": 2, "consensus_latency_ms": 3}]',
            '[{"agent_count": 4, "detection_time_ms": "1", '
            '"memory_mb": 2, "consensus_latency_ms": 3}]',
            '[{"agent_count": 4, "detection_time_ms": NaN, '
            '"memory_mb": 2, "consensus_latency_ms": 3}]',
            '[{"agent_count": 4, "detection_time_ms": 1, '
            '"memory_mb": -2, "consensus_latency_ms": 3}]',
        ),
    )
    def test_malformed_artifact_raises(self, tmp_path, content):
        from src.visualization.scalability import create_scalability_figure

        output_dir = tmp_path / "figures"
        data_dir = output_dir / "data"
        data_dir.mkdir(parents=True)
        (data_dir / "scalability_results.json").write_text(content)
        figures_before = plt.get_fignums()
        with pytest.raises(ValueError, match="scalability_results.json"):
            create_scalability_figure(output_dir)
        assert not list(output_dir.glob("*.pdf"))
        assert not list(output_dir.glob("*.png"))
        assert plt.get_fignums() == figures_before


class TestRound7FigureHonesty:
    """Keep schematic figure values visibly distinct from measurements."""

    def test_schematic_figures_render_honesty_footers(self, monkeypatch):
        from src.visualization import ablation_study, fp_mitigation, trust_decay

        monkeypatch.setattr(plt, "close", lambda *args, **kwargs: None)
        generators = (
            ablation_study.create_ablation_study_figure,
            fp_mitigation.create_fp_mitigation_figure,
            trust_decay.generate_trust_decay_figure,
        )
        for generate in generators:
            with tempfile.TemporaryDirectory() as tmpdir:
                generate(Path(tmpdir))
                footer = " ".join(text.get_text() for text in plt.gcf().texts).lower()
                assert "schematic" in footer, generate.__module__
                assert "not measured" in footer, generate.__module__


class TestCIFADCouplingFigure:
    def test_unachievable_portfolio_refuses_all_artifacts(self, tmp_path, monkeypatch):
        """The .80 requirement fails before any image or JSON can be exported."""
        import importlib.util

        script_path = (
            Path(__file__).resolve().parents[1]
            / "scripts"
            / "19_cif_ad_coupling_figure.py"
        )
        spec = importlib.util.spec_from_file_location("cif_ad_coupling_figure", script_path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        monkeypatch.setattr(module, "OUTPUT_DIR", tmp_path / "figures")
        monkeypatch.setattr(module, "DATA_DIR", tmp_path / "figures" / "data")

        with pytest.raises(ValueError, match="Refusing.*0.80 coverage"):
            module.generate_cif_ad_coupling_figure()

        assert not list(tmp_path.rglob("cif_ad_coupling.pdf"))
        assert not list(tmp_path.rglob("cif_ad_coupling.png"))
        assert not list(tmp_path.rglob("cif_ad_coupling.json"))


class TestMissingArtifactScriptFailures:
    @pytest.mark.parametrize(
        ("script_name", "missing_artifacts"),
        (
            ("03_detection_results_figure.py", ("detection_results.json",)),
            ("08_scalability_figure.py", ("scalability_results.json",)),
            (
                "generate_all_figures.py",
                ("detection_results.json", "scalability_results.json"),
            ),
        ),
    )
    def test_actual_scripts_exit_nonzero_without_inputs(
        self, tmp_path, script_name, missing_artifacts
    ):
        """Run unchanged entry points in an isolated tree, not fake script paths."""
        project_root = Path(__file__).resolve().parents[1]
        isolated = tmp_path / "part1"
        shutil.copytree(
            project_root / "src",
            isolated / "src",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        scripts = isolated / "scripts"
        scripts.mkdir()
        for name in (
            "03_detection_results_figure.py",
            "08_scalability_figure.py",
            "generate_all_figures.py",
        ):
            shutil.copy2(project_root / "scripts" / name, scripts / name)
        result = subprocess.run(
            [sys.executable, str(scripts / script_name)],
            cwd=isolated,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        assert result.returncode != 0, result.stdout
        output = result.stdout + result.stderr
        for artifact in missing_artifacts:
            assert artifact in output, output
        if script_name == "generate_all_figures.py":
            assert "0/2 figure script(s) succeeded" in result.stdout
            assert "03_detection_results_figure.py" in result.stderr
            assert "08_scalability_figure.py" in result.stderr
        assert not (isolated / "output").exists()
