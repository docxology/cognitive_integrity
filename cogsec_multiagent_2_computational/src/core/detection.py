"""
Anomaly Detection for Cognitive Security.

Implements drift detection and behavioral scoring.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np


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

    def add_observation(self, beliefs: Dict[str, float]) -> None:
        """Add belief state observation."""
        # Convert to sorted array for consistency
        keys = sorted(beliefs.keys())
        values = np.array([beliefs[k] for k in keys])
        self._history.append((keys, values))

    def calibrate_baseline(self) -> None:
        """Calibrate baseline from collected observations."""
        if len(self._history) < self.config.baseline_samples:
            raise ValueError(
                f"Need {self.config.baseline_samples} samples, "
                f"have {len(self._history)}"
            )

        # Stack observations (assuming consistent keys)
        values = np.array([v for _, v in self._history])
        self._baseline_mean = np.mean(values, axis=0)
        self._baseline_std = np.std(values, axis=0) + 1e-6  # Avoid div by 0
        self._calibrated = True

    def _kl_divergence(self, p: np.ndarray, q: np.ndarray) -> float:
        """Compute KL divergence D_KL(P || Q) with additive smoothing.

        Formula:
            D_KL(P || Q) = Sum_i p_i . log(p_i / q_i)

        Smoothing: Both P and Q are clipped to [eps, 1-eps] with eps = 10^-10
        before normalization, preventing log(0) while introducing
        negligible bias (< 10^-9 nats for typical distributions).

        Properties:
            - D_KL >= 0 (Gibbs' inequality)
            - D_KL = 0 iff P = Q
            - Not symmetric: D_KL(P||Q) != D_KL(Q||P) in general
        """
        eps = 1e-10
        p = np.clip(p, eps, 1 - eps)
        q = np.clip(q, eps, 1 - eps)

        # Normalize to distributions
        p = p / p.sum()
        q = q / q.sum()

        return float(np.sum(p * np.log(p / q)))

    def compute_drift(
        self, current: Dict[str, float], window: int = 10
    ) -> Tuple[float, float]:
        """
        Compute drift from recent history.

        Args:
            current: Current belief state
            window: Lookback window

        Returns:
            Tuple of (kl_divergence, max_delta)
        """
        if len(self._history) < window:
            return 0.0, 0.0

        # Get historical average
        recent = list(self._history)[-window:]
        keys = sorted(current.keys())
        if not keys:
            return 0.0, 0.0
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

    def is_anomalous(
        self, current: Dict[str, float], window: int = 10, lambda_weight: float = 0.5
    ) -> Tuple[bool, float]:
        """
        Check if current state is anomalous.

        Args:
            current: Current belief state
            window: Lookback window
            lambda_weight: Weight for max_delta component

        Returns:
            Tuple of (is_anomalous, score)
        """
        kl_div, max_delta = self.compute_drift(current, window)
        score = kl_div + lambda_weight * max_delta

        return score > self.config.drift_threshold, score

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
            except (TypeError, KeyError, ValueError, AttributeError):
                pass  # Skip failed extractions

    def calibrate(self, agent_id: str) -> None:
        """Calibrate baselines for agent from history."""
        for extractor, _ in self._extractors:
            key = f"{agent_id}:{extractor.name}"
            if (
                key in self._history
                and len(self._history[key]) >= self.config.baseline_samples
            ):
                values = np.array(list(self._history[key]))
                extractor.baseline_mean = float(np.mean(values))
                extractor.baseline_std = float(np.std(values)) + 1e-6

    def score(self, agent_id: str, state: dict) -> float:
        """Compute weighted Z-score anomaly measure for agent state.

        Formula:
            S = Sum_j [w_j . |x_j - mu_j| / sigma_j] / Sum_j w_j

        where x_j is the j-th feature value, mu_j and sigma_j are the
        calibrated baseline mean and standard deviation, and w_j is
        the feature weight. Division by zero is avoided: if sigma_j = 0,
        the z-score for that feature defaults to 0.0.

        Args:
            agent_id: Agent identifier (currently unused but reserved
                for per-agent baseline lookup)
            state: Current agent state dictionary

        Returns:
            Weighted anomaly score >= 0; higher indicates more anomalous
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
            except (TypeError, KeyError, ValueError, AttributeError):
                pass

        return total_score / total_weight if total_weight > 0 else 0.0

    def is_anomalous(
        self, agent_id: str, state: dict
    ) -> Tuple[bool, float, Dict[str, float]]:
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
                if extractor.baseline_std > 0:
                    z = abs(value - extractor.baseline_mean) / extractor.baseline_std
                else:
                    z = 0.0
                feature_scores[extractor.name] = z
                total_score += weight * z
                total_weight += weight
            except (TypeError, KeyError, ValueError, AttributeError):
                pass

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


class AdaptiveBaseline:
    """Feedback-driven EMA baseline update (S-Algorithm 5).

    Adjusts detection thresholds based on operator feedback:
    false positive feedback raises the threshold, true positive
    feedback lowers it. Uses exponential moving average for
    baseline tracking.
    """

    def __init__(
        self,
        n_features: int,
        learning_rate: float = 0.01,
        threshold: float = 3.0,
        fp_raise: int = 5,
        tp_lower: int = 10,
        delta: float = 0.05,
    ):
        """Initialize adaptive baseline.

        Args:
            n_features: Dimensionality of feature vectors.
            learning_rate: EMA learning rate (alpha).
            threshold: Initial detection threshold.
            fp_raise: Number of consecutive FPs before raising threshold.
            tp_lower: Number of consecutive TPs before lowering threshold.
            delta: Amount to adjust threshold per update.
        """
        if n_features <= 0:
            raise ValueError("n_features must be positive")
        self.n_features = n_features
        self.learning_rate = learning_rate
        self._threshold = threshold
        self.fp_raise = fp_raise
        self.tp_lower = tp_lower
        self.delta = delta

        self._mean = np.zeros(n_features)
        self._var = np.ones(n_features)
        self._count = 0
        self._consecutive_fp = 0
        self._consecutive_tp = 0

    def update(self, features: np.ndarray, feedback: str) -> None:
        """Update baseline with new observation and feedback.

        Args:
            features: Feature vector of shape (n_features,).
            feedback: "FP" for false positive, "TP" for true positive.
        """
        features = np.asarray(features, dtype=float)
        self._count += 1

        # EMA update for mean and variance
        alpha = self.learning_rate
        self._mean = (1 - alpha) * self._mean + alpha * features
        diff = features - self._mean
        self._var = (1 - alpha) * self._var + alpha * (diff ** 2)

        # Threshold adjustment based on feedback
        if feedback == "FP":
            self._consecutive_fp += 1
            self._consecutive_tp = 0
            if self._consecutive_fp >= self.fp_raise:
                self._threshold += self.delta
                self._consecutive_fp = 0
        elif feedback == "TP":
            self._consecutive_tp += 1
            self._consecutive_fp = 0
            if self._consecutive_tp >= self.tp_lower:
                self._threshold = max(0.1, self._threshold - self.delta)
                self._consecutive_tp = 0

    @property
    def threshold(self) -> float:
        """Current adaptive threshold."""
        return self._threshold

    @property
    def baseline(self) -> Tuple[np.ndarray, np.ndarray]:
        """Current baseline (mean, std)."""
        return self._mean.copy(), np.sqrt(self._var) + 1e-10


class SlidingWindowMonitor:
    """Periodic monitoring with EMA feature tracking (S-Algorithm 6).

    Collects snapshots of agent state at regular intervals,
    maintains an EMA of feature values, and detects anomalies
    when features deviate significantly from the running average.
    """

    def __init__(
        self,
        window_size: int = 200,
        threshold: float = 3.0,
        alpha: float = 0.1,
    ):
        """Initialize sliding window monitor.

        Args:
            window_size: Maximum number of snapshots to retain.
            threshold: Z-score threshold for anomaly detection.
            alpha: EMA smoothing factor.
        """
        self.window_size = window_size
        self.threshold = threshold
        self.alpha = alpha

        self._snapshots: deque = deque(maxlen=window_size)
        self._ema_mean: Optional[np.ndarray] = None
        self._ema_var: Optional[np.ndarray] = None

    def _state_to_features(self, state: dict) -> np.ndarray:
        """Convert state dict to numeric feature vector."""
        numeric_values = []
        for key in sorted(state.keys()):
            val = state[key]
            if isinstance(val, (int, float)):
                numeric_values.append(float(val))
        return np.array(numeric_values) if numeric_values else np.array([0.0])

    def collect_snapshot(self, state: dict) -> None:
        """Record a state snapshot and update EMA.

        Args:
            state: Agent state dictionary with numeric values.
        """
        import time

        features = self._state_to_features(state)
        self._snapshots.append((time.time(), features))

        # Initialize or update EMA
        if self._ema_mean is None:
            self._ema_mean = features.copy()
            self._ema_var = np.zeros_like(features)
        else:
            # Ensure dimension compatibility
            if len(features) != len(self._ema_mean):
                self._ema_mean = features.copy()
                self._ema_var = np.zeros_like(features)
            else:
                diff = features - self._ema_mean
                self._ema_mean = (1 - self.alpha) * self._ema_mean + self.alpha * features
                self._ema_var = (
                    (1 - self.alpha) * self._ema_var + self.alpha * (diff ** 2)
                )

    def check_anomalies(self) -> List[Dict]:
        """Check recent snapshots for anomalies.

        Returns:
            List of anomaly dicts with keys: timestamp, score, features.
        """
        if self._ema_mean is None or len(self._snapshots) < 2:
            return []

        anomalies = []
        std = np.sqrt(self._ema_var) + 1e-10

        for timestamp, features in self._snapshots:
            if len(features) != len(self._ema_mean):
                continue
            z = np.abs(features - self._ema_mean) / std
            score = float(np.max(z))
            if score > self.threshold:
                anomalies.append({
                    "timestamp": timestamp,
                    "score": score,
                    "features": features.tolist(),
                })

        return anomalies

    def prune(self, max_age: Optional[float] = None) -> int:
        """Remove old snapshots.

        Args:
            max_age: Maximum age in seconds. If None, removes
                snapshots beyond window_size (already handled by deque).

        Returns:
            Number of snapshots pruned.
        """
        if max_age is None:
            return 0

        import time

        cutoff = time.time() - max_age
        original_len = len(self._snapshots)

        self._snapshots = deque(
            ((t, f) for t, f in self._snapshots if t >= cutoff),
            maxlen=self.window_size,
        )

        return original_len - len(self._snapshots)

    def run_monitoring_step(self, state: dict) -> List[Dict]:
        """Collect snapshot and check for anomalies in one step.

        Args:
            state: Agent state dictionary.

        Returns:
            List of detected anomalies (may be empty).
        """
        self.collect_snapshot(state)
        return self.check_anomalies()
