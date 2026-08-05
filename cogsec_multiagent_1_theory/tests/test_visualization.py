#!/usr/bin/env python3
"""Tests for visualization modules.

This test module covers all visualization functions to ensure they generate
figures correctly without errors.
"""

import json
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend

import matplotlib.pyplot as plt


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

    def test_create_comprehensive_taxonomy_figure(self):
        """Test comprehensive taxonomy figure generation."""
        from src.visualization.comprehensive_taxonomy import create_comprehensive_taxonomy_figure

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = create_comprehensive_taxonomy_figure(output_dir)

            assert result.exists()
            assert result.suffix == ".pdf"


class TestDefenseComposition:
    """Tests for visualization/defense_composition.py."""

    def test_create_defense_composition_figure(self):
        """Test defense composition figure generation."""
        from src.visualization.defense_composition import create_defense_composition_figure

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = create_defense_composition_figure(output_dir)

            # Returns tuple (png, pdf)
            if isinstance(result, tuple):
                png_path, pdf_path = result
                assert pdf_path.exists()
            else:
                assert result.exists()


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

    def test_create_detection_results_figure(self):
        """Test detection results figure generation with proper data format."""
        from src.visualization.detection_results import create_detection_results_figure

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "figures"
            data_dir = output_dir / "data"
            data_dir.mkdir(parents=True)

            # Create required data in correct format
            data = {
                "defense_configurations": [
                    {
                        "name": "Baseline",
                        "detection_rates": {
                            "prompt_injection": 0.15,
                            "trust_exploitation": 0.10,
                            "belief_manipulation": 0.12,
                            "coordination_attack": 0.08,
                            "temporal_attack": 0.05,
                        },
                    },
                    {
                        "name": "Firewall Only",
                        "detection_rates": {
                            "prompt_injection": 0.85,
                            "trust_exploitation": 0.70,
                            "belief_manipulation": 0.65,
                            "coordination_attack": 0.55,
                            "temporal_attack": 0.50,
                        },
                    },
                    {
                        "name": "Full CIF",
                        "detection_rates": {
                            "prompt_injection": 0.98,
                            "trust_exploitation": 0.95,
                            "belief_manipulation": 0.92,
                            "coordination_attack": 0.88,
                            "temporal_attack": 0.85,
                        },
                    },
                ]
            }
            with open(data_dir / "detection_results.json", "w") as f:
                json.dump(data, f)

            result = create_detection_results_figure(output_dir)

            # May return Path or tuple
            if isinstance(result, tuple):
                png_path, pdf_path = result
                assert pdf_path.exists()
            else:
                assert result.exists()
                assert result.suffix == ".pdf"


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
        """Degenerate all-zero FPR reports max(TPR), not AUC 0.000 (P1-4).

        A classifier that never fires on negatives has FPR=0 at every
        measured threshold; the trapezoidal rule over a zero-FPR width would
        return 0.0, displaying a perfect-precision curve as AUC 0.000.
        """
        import numpy as np

        from src.visualization.roc_curves import compute_roc_auc

        fpr = np.zeros(20)
        tpr = np.array([0.6] * 6 + [0.0] * 14)
        assert abs(compute_roc_auc(tpr, fpr) - 0.6) < 1e-12

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


class TestScalability:
    """Tests for visualization/scalability.py."""

    def test_create_scalability_figure(self):
        """Test scalability figure generation with data file."""
        from src.visualization.scalability import create_scalability_figure

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

            if isinstance(result, tuple):
                png_path, pdf_path = result
                assert pdf_path.exists()


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

    def test_create_trust_calculus_figure(self):
        """Test trust calculus figure generation."""
        from src.visualization.trust_calculus import create_trust_calculus_figure

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = create_trust_calculus_figure(output_dir)

            assert result.exists()
            assert result.suffix == ".pdf"


class TestTrustNetwork:
    """Tests for visualization/trust_network.py."""

    def test_generate_trust_network_figure(self):
        """Test trust network figure generation."""
        from src.visualization.trust_network import generate_trust_network_figure

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = generate_trust_network_figure(output_dir)

            # Returns a list of paths
            if isinstance(result, list):
                assert len(result) > 0
                assert result[0].exists()
            else:
                assert result.exists()


class TestFigureDataIntegrityGuards:
    """Guard the P1-#10 / #11 data-integrity fixes (test gap #14)."""

    def test_detection_performance_is_documented_schematic(self):
        """The fabricated-metrics figure must remain visibly labelled schematic."""
        import inspect
        from src.visualization import detection_performance as m
        doc = (inspect.getdoc(m.create_detection_performance_figure) or "").upper()
        assert "SCHEMATIC" in doc and "NOT MEASUREMENT" in doc.replace("measurements", "measurement").upper() or "NOT MEASURED" in doc

    def test_detection_results_uses_only_measured_categories(self):
        """detection_results must not plot fabricated (never-produced) categories."""
        import inspect
        from src.visualization import detection_results as dr
        src = inspect.getsource(dr)
        assert "belief_manipulation" not in src
        assert "temporal_attack" not in src
        assert "coordination_attack" not in src
