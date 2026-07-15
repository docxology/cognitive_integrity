"""Ablation study package for the Cognitive Security Framework.

Re-exports all public classes from:
- component_removal: Systematic leave-one-out and leave-k-out ablation
- minimal_config: Minimum viable configuration search
- synergy: Pairwise synergy analysis between defense components
"""

from __future__ import annotations

from .component_removal import AblationResult, ComponentRemovalStudy
from .minimal_config import MinimalConfigResult, MinimalConfigSearch
from .synergy import PairwiseSynergyAnalysis, SynergyResult

__all__ = [
    "AblationResult", "ComponentRemovalStudy",
    "MinimalConfigResult", "MinimalConfigSearch",
    "PairwiseSynergyAnalysis", "SynergyResult",
]
