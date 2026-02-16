"""Minimum viable configuration search.

Searches for the smallest subset of defense components that still
achieves a target detection rate (TPR).  Implements greedy forward
selection, greedy backward elimination, and exhaustive enumeration.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class MinimalConfigResult:
    """Result from a minimal-configuration search.

    Attributes:
        components: Names of the selected components.
        detection_rate: Achieved TPR with the selected subset.
        n_components: Number of components in the subset.
        meets_threshold: Whether the detection rate meets or exceeds the
            target TPR.
    """

    components: List[str]
    detection_rate: float
    n_components: int
    meets_threshold: bool


# ---------------------------------------------------------------------------
# Minimal configuration search
# ---------------------------------------------------------------------------

class MinimalConfigSearch:
    """Search for the minimum viable defense configuration.

    The *evaluate_fn* receives a dictionary of active components
    (name -> instance) and must return a scalar TPR.

    Args:
        all_components: Dictionary mapping component name to instance.
        evaluate_fn: Callable ``Dict[str, Any] -> float`` returning TPR.
        target_tpr: Minimum acceptable detection rate.
    """

    def __init__(
        self,
        all_components: Dict[str, Any],
        evaluate_fn: Callable[[Dict[str, Any]], float],
        target_tpr: float = 0.90,
    ) -> None:
        self._components = dict(all_components)
        self._evaluate_fn = evaluate_fn
        self._target_tpr = target_tpr

    def greedy_forward_search(self) -> MinimalConfigResult:
        """Greedy forward selection: build up from empty set.

        At each step, add the component whose inclusion yields the
        greatest TPR improvement.  Stop when the target is met or all
        components have been added.

        Returns:
            :class:`MinimalConfigResult` with the selected subset.
        """
        selected: Dict[str, Any] = {}
        remaining = dict(self._components)
        best_tpr = 0.0

        while remaining:
            best_candidate: Optional[str] = None
            best_candidate_tpr = -1.0

            for name, instance in remaining.items():
                trial = dict(selected)
                trial[name] = instance
                tpr = self._evaluate_fn(trial)

                if tpr > best_candidate_tpr:
                    best_candidate_tpr = tpr
                    best_candidate = name

            if best_candidate is None:
                break

            selected[best_candidate] = remaining.pop(best_candidate)
            best_tpr = best_candidate_tpr

            if best_tpr >= self._target_tpr:
                break

        return MinimalConfigResult(
            components=list(selected.keys()),
            detection_rate=best_tpr,
            n_components=len(selected),
            meets_threshold=best_tpr >= self._target_tpr,
        )

    def greedy_backward_search(self) -> MinimalConfigResult:
        """Greedy backward elimination: prune from the full set.

        At each step, remove the component whose removal causes the
        smallest TPR drop.  Stop when removing any further component
        would bring TPR below the target.

        Returns:
            :class:`MinimalConfigResult` with the reduced subset.
        """
        current = dict(self._components)
        current_tpr = self._evaluate_fn(current)

        while len(current) > 1:
            least_impact_name: Optional[str] = None
            least_impact_tpr = -1.0

            for name in current:
                trial = {k: v for k, v in current.items() if k != name}
                tpr = self._evaluate_fn(trial)

                if tpr > least_impact_tpr:
                    least_impact_tpr = tpr
                    least_impact_name = name

            # If removing the least impactful component still meets target
            if (
                least_impact_name is not None
                and least_impact_tpr >= self._target_tpr
            ):
                del current[least_impact_name]
                current_tpr = least_impact_tpr
            else:
                # Can't remove any more without going below target
                break

        return MinimalConfigResult(
            components=list(current.keys()),
            detection_rate=current_tpr,
            n_components=len(current),
            meets_threshold=current_tpr >= self._target_tpr,
        )

    def exhaustive_search(
        self, max_size: Optional[int] = None
    ) -> List[MinimalConfigResult]:
        """Exhaustive enumeration of all component subsets.

        Evaluates every combination of components from size 1 up to
        *max_size* (or all components if ``None``).

        Args:
            max_size: Maximum subset size to consider.  Defaults to the
                total number of components.

        Returns:
            List of :class:`MinimalConfigResult` for *all* subsets that
            meet the target TPR, sorted by ``n_components`` ascending
            then ``detection_rate`` descending.
        """
        names = list(self._components.keys())
        n = len(names)
        if max_size is None:
            max_size = n

        viable: List[MinimalConfigResult] = []

        for size in range(1, max_size + 1):
            for combo in itertools.combinations(names, size):
                subset = {name: self._components[name] for name in combo}
                tpr = self._evaluate_fn(subset)
                meets = tpr >= self._target_tpr

                result = MinimalConfigResult(
                    components=list(combo),
                    detection_rate=tpr,
                    n_components=size,
                    meets_threshold=meets,
                )

                if meets:
                    viable.append(result)

        # Sort by size (ascending), then by TPR (descending)
        viable.sort(key=lambda r: (r.n_components, -r.detection_rate))
        return viable
