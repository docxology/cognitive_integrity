"""Smoke tests for visualization figure and table generators.

Each function is called with a temp output directory.  We verify it
returns a matplotlib Figure (or paths for ROC) and closes cleanly.
"""


import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest
from matplotlib.figure import Figure

# ── Figure smoke tests ──────────────────────────────────────────────────

class TestFigureGenerators:
    """Smoke-test every plot_* function in visualization.figures."""

    @pytest.fixture(autouse=True)
    def _output_dir(self, tmp_path):
        self.out = str(tmp_path)

    # -- Individual figure modules --

    def test_attack_surface(self):
        from visualization.figures.attack_surface import plot_attack_surface
        fig = plot_attack_surface(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_trust_decay(self):
        from visualization.figures.trust_decay import plot_trust_decay
        fig = plot_trust_decay(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_defense_composition(self):
        from visualization.figures.defense_composition import plot_defense_composition
        fig = plot_defense_composition(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_ablation_study(self):
        from visualization.figures.ablation_study import plot_ablation_study
        fig = plot_ablation_study(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_detection_performance(self):
        from visualization.figures.detection_performance import plot_detection_performance
        fig = plot_detection_performance(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_comprehensive_taxonomy(self):
        from visualization.figures.comprehensive_taxonomy import plot_comprehensive_taxonomy
        fig = plot_comprehensive_taxonomy(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_cif_comprehensive(self):
        from visualization.figures.cif_comprehensive import plot_cif_comprehensive
        fig = plot_cif_comprehensive(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_roc_curves(self):
        from visualization.figures.roc_curves import plot_roc_curves
        result = plot_roc_curves(output_dir=self.out)
        # Returns tuple of paths or a Figure
        if isinstance(result, Figure):
            plt.close(result)
        else:
            assert len(result) >= 1

    def test_scalability(self):
        from visualization.figures.scalability import plot_scalability
        fig = plot_scalability(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_trust_calculus(self):
        from visualization.figures.trust_calculus import plot_trust_calculus
        fig = plot_trust_calculus(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_belief_sandbox(self):
        from visualization.figures.belief_sandbox import plot_belief_sandbox
        fig = plot_belief_sandbox(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_fp_mitigation(self):
        from visualization.figures.fp_mitigation import plot_fp_mitigation
        fig = plot_fp_mitigation(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_confusion_matrices(self):
        from visualization.figures.confusion_matrices import plot_confusion_matrices
        fig = plot_confusion_matrices(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_detection_distributions(self):
        from visualization.figures.detection_distributions import plot_detection_distributions
        fig = plot_detection_distributions(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_cif_architecture(self):
        from visualization.figures.cif_architecture import plot_cif_architecture
        fig = plot_cif_architecture(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_trust_network(self):
        from visualization.figures.trust_network import plot_trust_network
        fig = plot_trust_network(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_threat_taxonomy(self):
        from visualization.figures.threat_taxonomy import plot_threat_taxonomy
        fig = plot_threat_taxonomy(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_attack_timeline(self):
        from visualization.figures.attack_timeline import plot_attack_timeline
        fig = plot_attack_timeline(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_component_interactions(self):
        from visualization.figures.component_interactions import plot_component_interactions
        fig = plot_component_interactions(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_detection_results(self):
        from visualization.figures.detection_results import plot_detection_heatmap
        fig = plot_detection_heatmap(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_sensitivity_heatmap(self):
        from visualization.figures.sensitivity_heatmap import plot_sensitivity_heatmap
        fig = plot_sensitivity_heatmap(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_precision_recall_curves(self):
        from visualization.figures.precision_recall_curves import plot_precision_recall_curves
        fig = plot_precision_recall_curves(output_dir=self.out)
        assert isinstance(fig, Figure)
        plt.close(fig)


# ── Table generator smoke tests ─────────────────────────────────────────

class TestTableGenerators:
    """Smoke-test every generate_* function in visualization.tables."""

    def test_corpus_table(self):
        from visualization.tables.corpus_tables import generate_corpus_table
        result = generate_corpus_table()
        assert isinstance(result, str) and len(result) > 0

    def test_cross_validation_table(self):
        from visualization.tables.cross_validation_tables import generate_cross_validation_table
        result = generate_cross_validation_table()
        assert isinstance(result, str) and len(result) > 0

    def test_assumption_table(self):
        from visualization.tables.assumption_tables import generate_assumption_table
        result = generate_assumption_table()
        assert isinstance(result, str) and len(result) > 0

    def test_ablation_table(self):
        from visualization.tables.ablation_tables import generate_ablation_table
        result = generate_ablation_table()
        assert isinstance(result, str) and len(result) > 0

    def test_synergy_table(self):
        from visualization.tables.ablation_tables import generate_synergy_table
        result = generate_synergy_table()
        assert isinstance(result, str) and len(result) > 0

    def test_hypothesis_table(self):
        from visualization.tables.statistical_tables import generate_hypothesis_table
        result = generate_hypothesis_table()
        assert isinstance(result, str) and len(result) > 0

    def test_effect_size_table(self):
        from visualization.tables.statistical_tables import generate_effect_size_table
        result = generate_effect_size_table()
        assert isinstance(result, str) and len(result) > 0

    def test_detection_table(self):
        from visualization.tables.detection_tables import generate_detection_table
        result = generate_detection_table()
        assert isinstance(result, str) and len(result) > 0

    def test_stability_table(self):
        from visualization.tables.stability_tables import generate_stability_table
        result = generate_stability_table()
        assert isinstance(result, str) and len(result) > 0

    def test_scalability_table(self):
        from visualization.tables.scalability_tables import generate_scalability_table
        result = generate_scalability_table()
        assert isinstance(result, str) and len(result) > 0
