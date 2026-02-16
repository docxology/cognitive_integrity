"""Pairwise and higher-order synergy analysis between defense components.

Quantifies whether pairs of defense components are synergistic (combined
performance exceeds the best individual) or antagonistic (combined
performance is worse than the best individual).

Key target: firewall + tripwires synergy = +0.09 TPR above max individual.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any, Callable, Dict, List, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class SynergyResult:
    """Result of a pairwise synergy measurement.

    Attributes:
        component_a: Name of the first component.
        component_b: Name of the second component.
        individual_a_tpr: TPR when only component A is active.
        individual_b_tpr: TPR when only component B is active.
        combined_tpr: TPR when both A and B are active together.
        synergy_score: ``combined - max(individual_a, individual_b)``.
            Positive values indicate synergy; negative values indicate
            antagonism.
    """

    component_a: str
    component_b: str
    individual_a_tpr: float
    individual_b_tpr: float
    combined_tpr: float
    synergy_score: float


# ---------------------------------------------------------------------------
# Pairwise synergy analysis
# ---------------------------------------------------------------------------

class PairwiseSynergyAnalysis:
    """Compute pairwise synergy scores for all defense component pairs.

    The *evaluate_fn* receives a dictionary of active components
    (name -> instance) and returns a scalar TPR.

    Args:
        components: Dictionary mapping component name to instance.
        evaluate_fn: Callable ``Dict[str, Any] -> float`` returning TPR.
    """

    def __init__(
        self,
        components: Dict[str, Any],
        evaluate_fn: Callable[[Dict[str, Any]], float],
    ) -> None:
        self._components = dict(components)
        self._evaluate_fn = evaluate_fn
        self._individual_tprs: Dict[str, float] = {}
        self._pair_results: List[SynergyResult] | None = None

    def _get_individual_tpr(self, name: str) -> float:
        """Evaluate a single component in isolation (cached)."""
        if name not in self._individual_tprs:
            single = {name: self._components[name]}
            self._individual_tprs[name] = self._evaluate_fn(single)
        return self._individual_tprs[name]

    def compute_all_pairs(self) -> List[SynergyResult]:
        """Compute synergy scores for all C(n, 2) component pairs.

        Returns:
            List of :class:`SynergyResult`, one per pair, sorted by
            synergy score descending (highest synergy first).
        """
        names = list(self._components.keys())
        results: List[SynergyResult] = []

        for a, b in combinations(names, 2):
            tpr_a = self._get_individual_tpr(a)
            tpr_b = self._get_individual_tpr(b)

            combined = {a: self._components[a], b: self._components[b]}
            tpr_combined = self._evaluate_fn(combined)

            synergy = tpr_combined - max(tpr_a, tpr_b)

            results.append(
                SynergyResult(
                    component_a=a,
                    component_b=b,
                    individual_a_tpr=tpr_a,
                    individual_b_tpr=tpr_b,
                    combined_tpr=tpr_combined,
                    synergy_score=synergy,
                )
            )

        results.sort(key=lambda r: r.synergy_score, reverse=True)
        self._pair_results = results
        return results

    def get_top_synergies(self, n: int = 5) -> List[SynergyResult]:
        """Return the top-n highest synergy pairs.

        Target: firewall + tripwires should yield synergy ~ +0.09.

        Args:
            n: Number of top pairs to return.

        Returns:
            Up to *n* :class:`SynergyResult` objects with the highest
            synergy scores.
        """
        if self._pair_results is None:
            self.compute_all_pairs()
        assert self._pair_results is not None
        return self._pair_results[:n]

    def get_antagonistic_pairs(self) -> List[SynergyResult]:
        """Return all pairs with negative synergy (antagonism).

        These are pairs where combining the two components produces
        *worse* detection than the best individual component alone.

        Returns:
            List of :class:`SynergyResult` with ``synergy_score < 0``,
            sorted by synergy ascending (most antagonistic first).
        """
        if self._pair_results is None:
            self.compute_all_pairs()
        assert self._pair_results is not None

        antagonistic = [r for r in self._pair_results if r.synergy_score < 0]
        antagonistic.sort(key=lambda r: r.synergy_score)
        return antagonistic

    def synergy_matrix(self) -> Tuple[List[str], np.ndarray]:
        """Build an n x n synergy matrix.

        Diagonal entries are 0.0 (self-synergy is undefined). Off-
        diagonal entry ``[i, j]`` is the synergy score between
        component i and component j.

        Returns:
            ``(names, matrix)`` where *names* is the list of component
            names and *matrix* is a symmetric numpy array of shape
            ``(n, n)``.
        """
        if self._pair_results is None:
            self.compute_all_pairs()
        assert self._pair_results is not None

        names = list(self._components.keys())
        n = len(names)
        name_to_idx = {name: i for i, name in enumerate(names)}

        matrix = np.zeros((n, n), dtype=np.float64)

        for result in self._pair_results:
            i = name_to_idx[result.component_a]
            j = name_to_idx[result.component_b]
            matrix[i, j] = result.synergy_score
            matrix[j, i] = result.synergy_score

        return names, matrix
