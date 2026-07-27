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

# ``evaluate_fn`` returns the measured operating point ``(tpr, fpr)``.
# A TPR-only synergy score cannot distinguish two components that
# genuinely complement each other from two that simply flag more.
EvaluateFn = Callable[[Dict[str, Any]], Tuple[float, float]]

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
        individual_a_fpr: FPR when only component A is active.
        individual_b_fpr: FPR when only component B is active.
        combined_fpr: FPR when both A and B are active together.
    """

    component_a: str
    component_b: str
    individual_a_tpr: float
    individual_b_tpr: float
    combined_tpr: float
    synergy_score: float
    individual_a_fpr: float
    individual_b_fpr: float
    combined_fpr: float

    @property
    def youden_synergy_score(self) -> float:
        """Synergy measured on Youden's J instead of raw TPR.

        ``J(combined) - max(J(a), J(b))`` where ``J = TPR - FPR``.  A pair
        whose TPR synergy is bought entirely with extra false positives
        has a J synergy of zero or below.
        """
        j_a = self.individual_a_tpr - self.individual_a_fpr
        j_b = self.individual_b_tpr - self.individual_b_fpr
        j_combined = self.combined_tpr - self.combined_fpr
        return j_combined - max(j_a, j_b)


# ---------------------------------------------------------------------------
# Pairwise synergy analysis
# ---------------------------------------------------------------------------

class PairwiseSynergyAnalysis:
    """Compute pairwise synergy scores for all defense component pairs.

    The *evaluate_fn* receives a dictionary of active components
    (name -> instance) and returns ``(tpr, fpr)``.

    Args:
        components: Dictionary mapping component name to instance.
        evaluate_fn: Callable ``Dict[str, Any] -> (tpr, fpr)``.
    """

    def __init__(
        self,
        components: Dict[str, Any],
        evaluate_fn: EvaluateFn,
    ) -> None:
        self._components = dict(components)
        self._evaluate_fn = evaluate_fn
        self._individual_rates: Dict[str, Tuple[float, float]] = {}
        self._pair_results: List[SynergyResult] | None = None

    def _get_individual_rates(self, name: str) -> Tuple[float, float]:
        """Evaluate a single component in isolation (cached)."""
        if name not in self._individual_rates:
            single = {name: self._components[name]}
            self._individual_rates[name] = self._evaluate_fn(single)
        return self._individual_rates[name]

    def compute_all_pairs(self) -> List[SynergyResult]:
        """Compute synergy scores for all C(n, 2) component pairs.

        Returns:
            List of :class:`SynergyResult`, one per pair, sorted by
            synergy score descending (highest synergy first).
        """
        names = list(self._components.keys())
        results: List[SynergyResult] = []

        for a, b in combinations(names, 2):
            tpr_a, fpr_a = self._get_individual_rates(a)
            tpr_b, fpr_b = self._get_individual_rates(b)

            combined = {a: self._components[a], b: self._components[b]}
            tpr_combined, fpr_combined = self._evaluate_fn(combined)

            synergy = tpr_combined - max(tpr_a, tpr_b)

            results.append(
                SynergyResult(
                    component_a=a,
                    component_b=b,
                    individual_a_tpr=tpr_a,
                    individual_b_tpr=tpr_b,
                    combined_tpr=tpr_combined,
                    synergy_score=synergy,
                    individual_a_fpr=fpr_a,
                    individual_b_fpr=fpr_b,
                    combined_fpr=fpr_combined,
                )
            )

        # Highest synergy first.  Pairs tie *exactly* once no noise is
        # injected, so component names are an explicit secondary key:
        # otherwise the published "top synergy pair" would depend on the
        # insertion order of `components`.
        results.sort(key=lambda r: (-r.synergy_score, r.component_a, r.component_b))
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
        antagonistic.sort(key=lambda r: (r.synergy_score, r.component_a, r.component_b))
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
