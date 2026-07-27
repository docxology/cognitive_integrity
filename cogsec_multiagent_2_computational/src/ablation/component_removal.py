"""Systematic defense component removal study.

Implements the ablation methodology from the CIF evaluation: remove one
(or k) defense components at a time and measure the impact on detection
rate and false-positive rate.  This quantifies each component's marginal
contribution to the integrated framework.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any, Callable, Dict, List, Tuple

# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class AblationResult:
    """Result from removing one or more defense components.

    Attributes:
        removed_component: Name(s) of the removed component(s), comma-
            separated when multiple.
        remaining_components: Names of the components that remain active.
        detection_rate: TPR with the reduced component set.
        delta_tpr: Change in TPR relative to the full pipeline
            (negative means performance dropped).
        false_positive_rate: FPR with the reduced component set.
        delta_fpr: Change in FPR relative to the full pipeline
            (positive means more false positives).
    """

    removed_component: str
    remaining_components: List[str]
    detection_rate: float
    delta_tpr: float
    false_positive_rate: float
    delta_fpr: float

    @property
    def youden_j(self) -> float:
        """Youden's J statistic (TPR - FPR) for the reduced component set.

        A TPR-only ranking cannot distinguish a component that adds true
        detections from one that merely raises the overall flag rate.
        J is the standard single-number summary that subtracts the
        false-positive cost from the true-positive benefit.
        """
        return self.detection_rate - self.false_positive_rate

    @property
    def delta_youden_j(self) -> float:
        """Change in Youden's J relative to the full pipeline.

        Algebraically ``delta_tpr - delta_fpr``: both deltas are taken
        against the same cached full-pipeline baseline, so the baseline
        terms cancel exactly.
        """
        return self.delta_tpr - self.delta_fpr


# ---------------------------------------------------------------------------
# Component removal study
# ---------------------------------------------------------------------------

class ComponentRemovalStudy:
    """Systematic single-component and leave-k-out ablation.

    The study wraps a set of named defense components and an evaluation
    function.  The *evaluate_fn* receives a dictionary of active components
    (name -> instance) and must return ``(tpr, fpr)``.

    Args:
        components: Dictionary mapping component name to module instance.
        evaluate_fn: Callable that takes ``Dict[str, Any]`` of active
            components and returns ``(detection_rate, false_positive_rate)``.
    """

    def __init__(
        self,
        components: Dict[str, Any],
        evaluate_fn: Callable[[Dict[str, Any]], Tuple[float, float]],
    ) -> None:
        self._components = dict(components)
        self._evaluate_fn = evaluate_fn
        self._full_tpr: float | None = None
        self._full_fpr: float | None = None

    def _get_full_baseline(self) -> Tuple[float, float]:
        """Evaluate the full pipeline once and cache the result."""
        if self._full_tpr is None or self._full_fpr is None:
            tpr, fpr = self._evaluate_fn(self._components)
            self._full_tpr = tpr
            self._full_fpr = fpr
        return self._full_tpr, self._full_fpr

    def full_baseline(self) -> Tuple[float, float]:
        """Public accessor for the cached full-pipeline ``(tpr, fpr)``.

        Callers that serialise ablation output need the operating point
        of the *unablated* pipeline; reconstructing it by averaging
        ``tpr - delta_tpr`` across rows is lossy and error-prone.
        """
        return self._get_full_baseline()

    def run_full_ablation(self) -> List[AblationResult]:
        """Remove each component one at a time and measure impact.

        Returns:
            List of :class:`AblationResult`, one per component, sorted
            by delta_tpr (largest drop first).
        """
        full_tpr, full_fpr = self._get_full_baseline()
        results: List[AblationResult] = []

        for name in self._components:
            reduced = {k: v for k, v in self._components.items() if k != name}
            remaining = list(reduced.keys())

            tpr, fpr = self._evaluate_fn(reduced)

            results.append(
                AblationResult(
                    removed_component=name,
                    remaining_components=remaining,
                    detection_rate=tpr,
                    delta_tpr=tpr - full_tpr,
                    false_positive_rate=fpr,
                    delta_fpr=fpr - full_fpr,
                )
            )

        # Sort by delta_tpr ascending (largest drop = most negative first).
        # Components with identical impact tie *exactly* once no noise is
        # injected, so the name is a secondary key: without it the published
        # ranking would silently depend on `components` insertion order.
        results.sort(key=lambda r: (r.delta_tpr, r.removed_component))
        return results

    def run_leave_k_out(self, k: int = 2) -> List[AblationResult]:
        """Remove k components at a time and measure impact.

        Args:
            k: Number of components to remove simultaneously.

        Returns:
            List of :class:`AblationResult` for all C(n, k) combinations,
            sorted by delta_tpr.

        Raises:
            ValueError: If k >= number of components (would leave nothing).
        """
        names = list(self._components.keys())
        n = len(names)

        if k >= n:
            raise ValueError(
                f"k={k} must be less than the number of components ({n})"
            )
        if k < 1:
            raise ValueError("k must be >= 1")

        full_tpr, full_fpr = self._get_full_baseline()
        results: List[AblationResult] = []

        for combo in combinations(names, k):
            removed_set = set(combo)
            reduced = {
                key: val
                for key, val in self._components.items()
                if key not in removed_set
            }
            remaining = list(reduced.keys())

            tpr, fpr = self._evaluate_fn(reduced)

            results.append(
                AblationResult(
                    removed_component=", ".join(combo),
                    remaining_components=remaining,
                    detection_rate=tpr,
                    delta_tpr=tpr - full_tpr,
                    false_positive_rate=fpr,
                    delta_fpr=fpr - full_fpr,
                )
            )

        results.sort(key=lambda r: (r.delta_tpr, r.removed_component))
        return results

    def get_critical_components(
        self, threshold: float = 0.05
    ) -> List[str]:
        """Identify components whose removal drops TPR by more than threshold.

        Args:
            threshold: Minimum absolute TPR drop to be considered critical.

        Returns:
            Names of critical components, sorted by impact (most critical
            first).
        """
        ablation_results = self.run_full_ablation()
        critical = [
            r.removed_component
            for r in ablation_results
            if abs(r.delta_tpr) > threshold
        ]
        return critical

    def rank_by_importance(self) -> List[Tuple[str, float]]:
        """Rank components by their contribution to TPR.

        Components whose removal causes the largest TPR drop are ranked
        first (most important).

        Returns:
            List of ``(component_name, abs_delta_tpr)`` tuples sorted
            descending by importance.
        """
        ablation_results = self.run_full_ablation()
        ranked = [
            (r.removed_component, abs(r.delta_tpr))
            for r in ablation_results
        ]
        ranked.sort(key=lambda t: t[1], reverse=True)
        return ranked
