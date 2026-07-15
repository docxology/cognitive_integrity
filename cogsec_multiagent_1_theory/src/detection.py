"""
Anomaly Detection for Cognitive Security.

Implements drift detection and behavioral scoring.
"""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class DetectionConfig:
    """Configuration for anomaly detection."""

    drift_threshold: float = 0.3  # KL divergence threshold
    window_size: int = 100  # Sliding window size
    baseline_samples: int = 50  # Samples for baseline
    sigma_multiplier: float = 3.0  # For threshold setting


class DriftDetector:
    """
    Detects belief distribution drift over time.

    Uses KL divergence and max-delta scoring.
    """

    def __init__(self, config: Optional[DetectionConfig] = None):
        self.config = config or DetectionConfig()
        self._history: deque = deque(maxlen=self.config.window_size)
        self._baseline_mean: Optional[np.ndarray] = None
        self._baseline_std: Optional[np.ndarray] = None
        self._calibrated: bool = False
        self._calibrated_threshold: Optional[float] = None

    def add_observation(self, beliefs: Dict[str, float]) -> None:
        """Add belief state observation."""
        # Convert to sorted array for consistency
        keys = sorted(beliefs.keys())
        values = np.array([beliefs[k] for k in keys])
        self._history.append((keys, values))

    def calibrate_baseline(self) -> None:
        """Calibrate baseline from collected observations.

        Computes per-feature mean/std of the raw belief history (kept for
        introspection/back-compat) and, per Property (drift-threshold) in
        the manuscript, calibrates the drift-score anomaly threshold as
        theta = mu_baseline + k * sigma_baseline, where the baseline
        distribution is the drift score computed retrospectively over the
        collected history and k = config.sigma_multiplier. Once calibrated,
        `is_anomalous` uses this calibrated threshold instead of the static
        `config.drift_threshold`.
        """
        if len(self._history) < self.config.baseline_samples:
            raise ValueError(
                f"Need {self.config.baseline_samples} samples, have {len(self._history)}"
            )

        # Stack observations (assuming consistent keys)
        values = np.array([v for _, v in self._history])
        self._baseline_mean = np.mean(values, axis=0)
        self._baseline_std = np.std(values, axis=0) + 1e-6  # Avoid div by 0

        # Retrospectively compute drift scores across the collected history
        # to calibrate a data-driven anomaly threshold.
        history_list = list(self._history)
        drift_scores: List[float] = []
        for i in range(1, len(history_list)):
            keys, current_values = history_list[i]
            current = dict(zip(keys, current_values))
            window = min(i, 10)
            kl_div, max_delta = self._drift_from_slice(
                history_list[:i], current, window
            )
            drift_scores.append(kl_div + 0.5 * max_delta)

        if drift_scores:
            mu = float(np.mean(drift_scores))
            sigma = float(np.std(drift_scores))
            self._calibrated_threshold = mu + self.config.sigma_multiplier * sigma
        else:
            self._calibrated_threshold = self.config.drift_threshold

        self._calibrated = True

    def _kl_divergence(self, p: np.ndarray, q: np.ndarray) -> float:
        """
        Compute KL divergence D_KL(P || Q).

        Uses smoothing to avoid log(0).
        """
        eps = 1e-10
        p = np.clip(p, eps, 1 - eps)
        q = np.clip(q, eps, 1 - eps)

        # Normalize to distributions
        p = p / p.sum()
        q = q / q.sum()

        return float(np.sum(p * np.log(p / q)))

    def _drift_from_slice(
        self,
        history_slice: List[Tuple[List[str], np.ndarray]],
        current: Dict[str, float],
        window: int,
    ) -> Tuple[float, float]:
        """Compute (kl_divergence, max_delta) of `current` against a given history slice."""
        if len(history_slice) < window:
            return 0.0, 0.0

        # Get historical average
        recent = history_slice[-window:]
        keys = sorted(current.keys())
        current_arr = np.array([current.get(k, 0.5) for k in keys])

        # Average of recent observations
        hist_values = np.array([v for _, v in recent if len(v) == len(keys)])
        if len(hist_values) == 0:
            return 0.0, 0.0

        hist_mean = np.mean(hist_values, axis=0)

        # Compute metrics
        kl_div = self._kl_divergence(current_arr, hist_mean)
        max_delta = float(np.max(np.abs(current_arr - hist_mean)))

        return kl_div, max_delta

    def compute_drift(self, current: Dict[str, float], window: int = 10) -> Tuple[float, float]:
        """
        Compute drift from recent history.

        Args:
            current: Current belief state
            window: Lookback window

        Returns:
            Tuple of (kl_divergence, max_delta)
        """
        return self._drift_from_slice(list(self._history), current, window)

    def is_anomalous(
        self, current: Dict[str, float], window: int = 10, lambda_weight: float = 0.5
    ) -> Tuple[bool, float]:
        """
        Check if current state is anomalous.

        If `calibrate_baseline()` has been called, the calibrated
        data-driven threshold (theta = mu_baseline + k * sigma_baseline,
        cf. manuscript Property drift-threshold) is used instead of the
        static `config.drift_threshold`.

        Args:
            current: Current belief state
            window: Lookback window
            lambda_weight: Weight for max_delta component

        Returns:
            Tuple of (is_anomalous, score)
        """
        kl_div, max_delta = self.compute_drift(current, window)
        score = kl_div + lambda_weight * max_delta

        threshold = (
            self._calibrated_threshold
            if self._calibrated and self._calibrated_threshold is not None
            else self.config.drift_threshold
        )

        return score > threshold, score

    def get_drift_history(self, n: int = 20) -> List[float]:
        """Get recent drift scores."""
        if len(self._history) < 2:
            return []

        scores = []
        history_list = list(self._history)

        for i in range(max(1, len(history_list) - n), len(history_list)):
            keys, values = history_list[i]
            current = dict(zip(keys, values))
            _, score = self.is_anomalous(current, window=min(i, 10))
            scores.append(score)

        return scores


@dataclass
class FeatureExtractor:
    """Extracts behavioral features from agent state."""

    name: str
    extract: Callable[[dict], float]
    baseline_mean: float = 0.0
    baseline_std: float = 1.0


class AnomalyScorer:
    """
    Scores agents for behavioral anomalies.

    Uses multiple feature extractors with weighted scoring.
    """

    def __init__(self, config: Optional[DetectionConfig] = None):
        self.config = config or DetectionConfig()
        self._extractors: List[Tuple[FeatureExtractor, float]] = []
        self._history: Dict[str, deque] = {}

    def add_extractor(
        self, name: str, extract_fn: Callable[[dict], float], weight: float = 1.0
    ) -> None:
        """
        Add feature extractor.

        Args:
            name: Feature name
            extract_fn: Function that extracts feature from state
            weight: Weight in final score
        """
        extractor = FeatureExtractor(name=name, extract=extract_fn)
        self._extractors.append((extractor, weight))
        self._history[name] = deque(maxlen=self.config.window_size)

    def observe(self, agent_id: str, state: dict) -> None:
        """
        Record observation for agent.

        Args:
            agent_id: Agent identifier
            state: Agent state dictionary
        """
        for extractor, _ in self._extractors:
            try:
                value = extractor.extract(state)
                key = f"{agent_id}:{extractor.name}"
                if key not in self._history:
                    self._history[key] = deque(maxlen=self.config.window_size)
                self._history[key].append(value)
            except (TypeError, ValueError, KeyError) as exc:
                logger.debug("Extractor %s failed on agent %s: %s", extractor.name, agent_id, exc)

    def calibrate(self, agent_id: str) -> None:
        """Calibrate baselines for agent from history."""
        for extractor, _ in self._extractors:
            key = f"{agent_id}:{extractor.name}"
            if key in self._history and len(self._history[key]) >= self.config.baseline_samples:
                values = np.array(list(self._history[key]))
                extractor.baseline_mean = float(np.mean(values))
                extractor.baseline_std = float(np.std(values)) + 1e-6

    def score(self, agent_id: str, state: dict) -> float:
        """
        Compute anomaly score for agent state.

        Args:
            agent_id: Agent identifier
            state: Current agent state

        Returns:
            Weighted anomaly score
        """
        total_score = 0.0
        total_weight = 0.0

        for extractor, weight in self._extractors:
            try:
                value = extractor.extract(state)

                # Z-score from baseline
                if extractor.baseline_std > 0:
                    z = abs(value - extractor.baseline_mean) / extractor.baseline_std
                else:
                    z = 0.0

                total_score += weight * z
                total_weight += weight
            except (TypeError, ValueError, KeyError, ZeroDivisionError) as exc:
                logger.debug("Extractor %s failed: %s", extractor.name, exc)

        return total_score / total_weight if total_weight > 0 else 0.0

    def is_anomalous(self, agent_id: str, state: dict) -> Tuple[bool, float, Dict[str, float]]:
        """
        Check if agent state is anomalous.

        Returns:
            Tuple of (is_anomalous, score, feature_scores)
        """
        feature_scores = {}
        total_score = 0.0
        total_weight = 0.0

        for extractor, weight in self._extractors:
            try:
                value = extractor.extract(state)
                z = abs(value - extractor.baseline_mean) / extractor.baseline_std
                feature_scores[extractor.name] = z
                total_score += weight * z
                total_weight += weight
            except (TypeError, ValueError, KeyError, ZeroDivisionError) as exc:
                logger.debug("Extractor %s failed: %s", extractor.name, exc)

        score = total_score / total_weight if total_weight > 0 else 0.0
        threshold = self.config.sigma_multiplier

        return score > threshold, score, feature_scores


# Standard feature extractors
def action_frequency_extractor(state: dict) -> float:
    """Extract actions per time unit."""
    return state.get("action_count", 0) / max(state.get("time_delta", 1), 1)


def belief_volatility_extractor(state: dict) -> float:
    """Extract belief change rate."""
    return state.get("belief_changes", 0)


def communication_volume_extractor(state: dict) -> float:
    """Extract messages sent/received."""
    return state.get("messages_sent", 0) + state.get("messages_received", 0)


def goal_stability_extractor(state: dict) -> float:
    """Extract goal set changes (should be near 0)."""
    return state.get("goal_changes", 0)
