"""Data generation and management for the Cognitive Security Framework.

Modules
-------
- ``generate``: Master data generator for all experiments.
- ``schema``: Typed dataclass schemas for experimental results.
- ``loaders``: Convenience loaders with type coercion.
"""

from __future__ import annotations

from .generate import DataGenerator
from .loaders import load_detection_data, load_json, load_scalability_data
from .result_loaders import (
    EvaluationResultRow,
    evaluation_to_confusion_counts,
    evaluation_to_detection_matrix,
    load_ablation_results,
    load_full_evaluation,
    load_sensitivity_results,
)
from .schema import AblationData, ColonyData, DetectionData, ScalabilityData

__all__ = [
    "DataGenerator",
    "DetectionData",
    "ScalabilityData",
    "AblationData",
    "ColonyData",
    "load_json",
    "load_detection_data",
    "load_scalability_data",
    # Result loaders
    "EvaluationResultRow",
    "load_full_evaluation",
    "load_ablation_results",
    "load_sensitivity_results",
    "evaluation_to_detection_matrix",
    "evaluation_to_confusion_counts",
]
