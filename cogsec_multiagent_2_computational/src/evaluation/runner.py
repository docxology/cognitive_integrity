"""ExperimentRunner: orchestrates the full 950 x 6 evaluation matrix.

Runs every combination of architecture adapter and attack category
through a defense pipeline, simulating detection using architecture-
specific attack-surface modifiers and trust topologies.  Results
are deterministic given a fixed seed.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from utils.types import ExperimentConfig

# ---------------------------------------------------------------------------
# Attack difficulty mapping
# ---------------------------------------------------------------------------

_DIFFICULTY_MAP: Dict[str, str] = {
    # Injection (easy to detect -- pattern-heavy)
    "direct_injection": "easy",
    "indirect_injection": "medium",
    "nested_injection": "hard",
    # Trust exploitation
    "impersonation": "medium",
    "trust_inflation": "hard",
    "delegation_abuse": "hard",
    # Belief manipulation
    "belief_drift": "hard",
    "belief_fabrication": "medium",
    "belief_injection": "medium",
    # Coordination
    "sybil_attack": "medium",
    "consensus_poisoning": "hard",
    "timing_attack": "hard",
}

_BASE_DETECTION: Dict[str, float] = {
    "easy": 0.95,
    "medium": 0.85,
    "hard": 0.70,
}


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class ExperimentResult:
    """Results from a single architecture x attack-category experiment.

    Attributes:
        architecture: Architecture name.
        attack_category: Attack (sub-)category value string.
        n_attacks: Number of attack samples evaluated.
        true_positives: Correctly detected attacks.
        false_positives: Benign samples incorrectly flagged.
        true_negatives: Correctly passed benign samples.
        false_negatives: Missed attacks.
        detection_rate: TP / (TP + FN).
        false_positive_rate: FP / (FP + TN).
        avg_latency_ms: Mean processing latency per sample.
    """

    architecture: str
    attack_category: str
    n_attacks: int
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    detection_rate: float
    false_positive_rate: float
    avg_latency_ms: float


# ---------------------------------------------------------------------------
# Experiment runner
# ---------------------------------------------------------------------------

class ExperimentRunner:
    """Orchestrates evaluation across architectures and attack categories.

    Usage::

        runner = ExperimentRunner()
        result = runner.run_single(adapter, attack_samples, pipeline)
        results = runner.run_full_matrix(adapters, corpus, pipeline)
    """

    def __init__(self, config: Optional[ExperimentConfig] = None) -> None:
        self.config = config or ExperimentConfig()
        self._rng = np.random.default_rng(self.config.seed)

    # ---- public API ----

    def run_single(
        self,
        architecture_adapter: Any,
        attack_samples: List[Dict[str, Any]],
        defense_pipeline: Any,
    ) -> ExperimentResult:
        """Run one architecture x one category evaluation.

        Args:
            architecture_adapter: An ``ArchitectureAdapter`` instance.
            attack_samples: List of dicts with at least ``category`` (str),
                ``content`` (str), and ``is_attack`` (bool) keys.
            defense_pipeline: A pipeline with an ``evaluate(message, context)``
                method, or ``None`` to use simulated detection.

        Returns:
            An ``ExperimentResult`` summarising the experiment.
        """
        multiplier = architecture_adapter.get_attack_surface_multiplier()
        arch_name = architecture_adapter.profile.name

        tp = fp = tn = fn = 0
        latencies: List[float] = []

        for sample in attack_samples:
            is_attack = sample.get("is_attack", True)
            category = sample.get("category", "direct_injection")

            t0 = time.perf_counter()
            detected, score = self._simulate_detection(
                architecture_adapter, sample, defense_pipeline
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            latencies.append(elapsed_ms)

            if is_attack:
                if detected:
                    tp += 1
                else:
                    fn += 1
            else:
                if detected:
                    fp += 1
                else:
                    tn += 1

        total = tp + fn
        detection_rate = tp / total if total > 0 else 0.0
        neg_total = fp + tn
        fpr = fp / neg_total if neg_total > 0 else 0.0
        avg_lat = float(np.mean(latencies)) if latencies else 0.0

        # Determine dominant category from samples
        categories = [s.get("category", "unknown") for s in attack_samples]
        dominant = max(set(categories), key=categories.count) if categories else "unknown"

        return ExperimentResult(
            architecture=arch_name,
            attack_category=dominant,
            n_attacks=len(attack_samples),
            true_positives=tp,
            false_positives=fp,
            true_negatives=tn,
            false_negatives=fn,
            detection_rate=detection_rate,
            false_positive_rate=fpr,
            avg_latency_ms=avg_lat,
        )

    def run_single_with_scores(
        self,
        architecture_adapter: Any,
        attack_samples: List[Dict[str, Any]],
        defense_pipeline: Any,
    ) -> Tuple[ExperimentResult, List[Tuple[bool, float]]]:
        """Run one evaluation and also return per-sample (detected, score) tuples.

        This variant collects the raw per-sample detection decisions alongside
        the aggregated ExperimentResult, enabling ROC and PR curve computation
        from real pipeline output.

        Parameters
        ----------
        architecture_adapter : ArchitectureAdapter
        attack_samples : list of dict
        defense_pipeline : pipeline or None

        Returns
        -------
        result : ExperimentResult
        per_sample : list of (detected, score)
        """
        multiplier = architecture_adapter.get_attack_surface_multiplier()
        arch_name = architecture_adapter.profile.name

        tp = fp = tn = fn = 0
        latencies: List[float] = []
        per_sample: List[Tuple[bool, float]] = []

        for sample in attack_samples:
            is_attack = sample.get("is_attack", True)
            category = sample.get("category", "direct_injection")

            t0 = time.perf_counter()
            detected, score = self._simulate_detection(
                architecture_adapter, sample, defense_pipeline
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            latencies.append(elapsed_ms)
            per_sample.append((detected, score))

            if is_attack:
                if detected:
                    tp += 1
                else:
                    fn += 1
            else:
                if detected:
                    fp += 1
                else:
                    tn += 1

        total = tp + fn
        detection_rate = tp / total if total > 0 else 0.0
        neg_total = fp + tn
        fpr_val = fp / neg_total if neg_total > 0 else 0.0
        avg_lat = float(np.mean(latencies)) if latencies else 0.0

        categories = [s.get("category", "unknown") for s in attack_samples]
        dominant = max(set(categories), key=categories.count) if categories else "unknown"

        result = ExperimentResult(
            architecture=arch_name,
            attack_category=dominant,
            n_attacks=len(attack_samples),
            true_positives=tp,
            false_positives=fp,
            true_negatives=tn,
            false_negatives=fn,
            detection_rate=detection_rate,
            false_positive_rate=fpr_val,
            avg_latency_ms=avg_lat,
        )

        return result, per_sample

    def run_full_matrix(
        self,
        adapters: List[Any],
        corpus: Dict[str, List[Dict[str, Any]]],
        pipeline: Any,
    ) -> List[ExperimentResult]:
        """Run all architecture x category combinations.

        Args:
            adapters: List of ``ArchitectureAdapter`` instances.
            corpus: Dict mapping category string to sample lists.
            pipeline: A defense pipeline (or ``None`` for simulation).

        Returns:
            List of ``ExperimentResult`` for every combination.
        """
        results: List[ExperimentResult] = []

        for adapter in adapters:
            for category_key, samples in corpus.items():
                result = self.run_single(adapter, samples, pipeline)
                results.append(result)

        return results

    def summary_table(
        self, results: List[ExperimentResult]
    ) -> Dict[str, Dict[str, float]]:
        """Pivot results into ``{architecture: {category: detection_rate}}``.

        Args:
            results: Flat list of experiment results.

        Returns:
            Nested dict keyed by architecture name then attack category.
        """
        table: Dict[str, Dict[str, float]] = {}
        for r in results:
            if r.architecture not in table:
                table[r.architecture] = {}
            table[r.architecture][r.attack_category] = r.detection_rate
        return table

    # ---- internal ----

    def _simulate_detection(
        self,
        adapter: Any,
        sample: Dict[str, Any],
        pipeline: Any,
    ) -> Tuple[bool, float]:
        """Simulate detection probability modulated by architecture.

        Algorithm:
            1. Look up base detection rate from attack difficulty.
            2. Divide by the architecture's attack_surface_multiplier
               (higher multiplier = harder to detect).
            3. Add Gaussian noise (std=0.05) for realism.
            4. Clamp score to [0, 1].
            5. Detected if score > 0.5.

        If a real pipeline is provided and has an ``evaluate`` method,
        it is used instead for the base score.

        Returns:
            ``(detected, score)`` tuple.
        """
        category = sample.get("category", "direct_injection")
        is_attack = sample.get("is_attack", True)

        # If real pipeline available, use it for score
        if pipeline is not None and hasattr(pipeline, "evaluate"):
            content = sample.get("content", "")
            result = pipeline.evaluate(content)
            base_score = result.score if hasattr(result, "score") else 0.5
        else:
            if is_attack:
                difficulty = _DIFFICULTY_MAP.get(category, "medium")
                base_score = _BASE_DETECTION[difficulty]
            else:
                # Benign samples: low base score (should not trigger)
                base_score = 0.15

        multiplier = adapter.get_attack_surface_multiplier()
        # Higher multiplier = more attack surface = harder to detect
        adjusted = base_score * (1.0 / multiplier)

        # Gaussian noise for realism
        noise = float(self._rng.normal(0.0, 0.05))
        score = float(np.clip(adjusted + noise, 0.0, 1.0))

        detected = score > 0.5
        return detected, score
