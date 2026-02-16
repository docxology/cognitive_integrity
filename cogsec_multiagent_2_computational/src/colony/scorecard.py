"""Colony Cognitive Security (CCS) score computation.

Computes composite CCS scores from detection rate, false positive rate,
resilience, and recovery metrics.  Weights are configurable via the
``CCSWeights`` dataclass.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import numpy as np


@dataclass
class CCSWeights:
    """Weights for the Colony Cognitive Security composite score.

    Attributes:
        detection: Weight for detection rate component.
        precision: Weight for precision (1 - FPR) component.
        resilience: Weight for resilience component.
        recovery: Weight for recovery speed component.
    """

    detection: float = 0.3
    precision: float = 0.2
    resilience: float = 0.3
    recovery: float = 0.2

    def __post_init__(self) -> None:
        total = self.detection + self.precision + self.resilience + self.recovery
        if not np.isclose(total, 1.0):
            raise ValueError(
                f"CCS weights must sum to 1.0, got {total:.4f}"
            )


def compute_ccs(
    detection_rate: float,
    false_positive_rate: float,
    resilience: float,
    recovery_steps: int,
    max_steps: int,
    weights: Optional[CCSWeights] = None,
) -> float:
    """Compute Colony Cognitive Security score.

    CCS = w1 * DR + w2 * (1 - FPR) + w3 * Resilience + w4 * Recovery_score

    where Recovery_score = 1 - (recovery_steps / max_steps).

    Args:
        detection_rate: Fraction of adversarial actions detected [0, 1].
        false_positive_rate: Fraction of honest actions falsely flagged [0, 1].
        resilience: Ratio of post-attack integrity to pre-attack integrity [0, 1].
        recovery_steps: Number of steps until integrity recovers above threshold.
        max_steps: Maximum simulation steps (normaliser for recovery).
        weights: Optional custom weights; defaults to ``CCSWeights()``.

    Returns:
        CCS score in [0, 1].
    """
    w = weights or CCSWeights()
    recovery_score = 1.0 - (recovery_steps / max(max_steps, 1))
    recovery_score = float(np.clip(recovery_score, 0.0, 1.0))

    ccs = (
        w.detection * detection_rate
        + w.precision * (1.0 - false_positive_rate)
        + w.resilience * resilience
        + w.recovery * recovery_score
    )
    return float(np.clip(ccs, 0.0, 1.0))


def compute_resilience(
    timeline: List[float],
    adversary_start_step: int,
) -> float:
    """Compute resilience from an integrity timeline.

    Resilience = min(integrity after attack) / integrity before attack.
    A value of 1.0 means the attack had no effect; lower values indicate
    greater impact.

    Args:
        timeline: Integrity scores per simulation step.
        adversary_start_step: Step at which the adversary becomes active.

    Returns:
        Resilience score in [0, 1].
    """
    if not timeline or adversary_start_step >= len(timeline):
        return 1.0

    pre_attack = timeline[:adversary_start_step] if adversary_start_step > 0 else [1.0]
    pre_attack_value = float(np.mean(pre_attack))
    if pre_attack_value <= 0.0:
        return 0.0

    post_attack = timeline[adversary_start_step:]
    if not post_attack:
        return 1.0

    min_post = float(np.min(post_attack))
    return float(np.clip(min_post / pre_attack_value, 0.0, 1.0))


def compute_recovery_steps(
    timeline: List[float],
    threshold: float = 0.9,
) -> int:
    """Compute number of steps until integrity recovers above threshold.

    Finds the minimum-integrity point, then counts steps until the first
    subsequent step that exceeds *threshold*.

    Args:
        timeline: Integrity scores per simulation step.
        threshold: Recovery threshold; integrity must exceed this.

    Returns:
        Number of steps from minimum point to recovery.  Returns
        ``len(timeline)`` if recovery never occurs.
    """
    if not timeline:
        return 0

    arr = np.asarray(timeline, dtype=np.float64)
    min_idx = int(np.argmin(arr))

    # Scan forward from minimum for recovery
    for i in range(min_idx, len(arr)):
        if arr[i] >= threshold:
            return i - min_idx

    # Never recovered
    return len(arr) - min_idx
