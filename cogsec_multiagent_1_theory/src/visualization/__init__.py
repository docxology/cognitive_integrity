"""Visualization module for Part 1 figures.

Provides publication-quality figure generators for the Cognitive Integrity Framework manuscript.
"""

from __future__ import annotations

from .ablation_study import create_ablation_study_figure
from .attack_surface import generate_attack_surface_figure
from .attack_timeline import create_attack_timeline_figure
from .belief_sandbox import create_belief_sandbox_figure
from .cif_architecture import create_cif_architecture_figure
from .cif_comprehensive import create_cif_comprehensive_figure
from .comprehensive_taxonomy import create_comprehensive_taxonomy_figure
from .defense_composition import create_defense_composition_figure
from .detection_performance import create_detection_performance_figure
from .detection_results import create_detection_results_figure
from .fp_mitigation import create_fp_mitigation_figure
from .roc_curves import create_roc_curves_figure
from .scalability import create_scalability_figure
from .threat_taxonomy import create_threat_taxonomy_figure
from .trust_calculus import create_trust_calculus_figure
from .trust_decay import generate_trust_decay_figure
from .trust_network import generate_trust_network_figure

__all__ = [
    "create_ablation_study_figure",
    "generate_attack_surface_figure",
    "create_attack_timeline_figure",
    "create_belief_sandbox_figure",
    "create_cif_architecture_figure",
    "create_cif_comprehensive_figure",
    "create_comprehensive_taxonomy_figure",
    "create_defense_composition_figure",
    "create_detection_performance_figure",
    "create_detection_results_figure",
    "create_fp_mitigation_figure",
    "create_roc_curves_figure",
    "create_scalability_figure",
    "create_threat_taxonomy_figure",
    "create_trust_calculus_figure",
    "generate_trust_decay_figure",
    "generate_trust_network_figure",
]
