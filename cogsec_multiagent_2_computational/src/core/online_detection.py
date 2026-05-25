"""
from __future__ import annotations

Online Detection for Cognitive Security.

Implements streaming anomaly detection (S-Algorithm 3) and
batch offline analysis (S-Algorithm 4 delegated to batch_detection.py).
"""

from collections import deque
from typing import Callable, Iterator, List, Optional, Tuple

import numpy as np


class CircularBuffer:
    """Fixed-size ring buffer for streaming features."""

    def __init__(self, maxlen: int):
        """Initialize buffer with maximum length.

        Args:
            maxlen: Maximum number of items in the buffer.
        """
        if maxlen <= 0:
            raise ValueError("maxlen must be positive")
        self._maxlen = maxlen
        self._buffer: deque = deque(maxlen=maxlen)

    def push(self, item: np.ndarray) -> None:
        """Push an item into the buffer, evicting oldest if full."""
        self._buffer.append(item)

    def __len__(self) -> int:
        return len(self._buffer)

    @property
    def maxlen(self) -> int:
        """Maximum buffer capacity."""
        return self._maxlen

    def to_array(self) -> np.ndarray:
        """Convert buffer contents to numpy array.

        Returns:
            2D array of shape (n_items, n_features).
        """
        if len(self._buffer) == 0:
            return np.array([])
        return np.array(list(self._buffer))


class OnlineStatistics:
    """Welford's online mean/variance algorithm.

    Computes running mean and variance in a single pass
    without storing all observations.
    """

    def __init__(self, n_features: int):
        """Initialize online statistics tracker.

        Args:
            n_features: Dimensionality of feature vectors.
        """
        if n_features <= 0:
            raise ValueError("n_features must be positive")
        self.n_features = n_features
        self._count: int = 0
        self._mean = np.zeros(n_features)
        self._m2 = np.zeros(n_features)

    def update(self, features: np.ndarray) -> None:
        """Update running statistics with new observation.

        Uses Welford's algorithm for numerical stability.

        Args:
            features: Feature vector of shape (n_features,).
        """
        features = np.asarray(features, dtype=float)
        self._count += 1
        delta = features - self._mean
        self._mean += delta / self._count
        delta2 = features - self._mean
        self._m2 += delta * delta2

    @property
    def count(self) -> int:
        """Number of observations seen."""
        return self._count

    @property
    def mean(self) -> np.ndarray:
        """Current running mean."""
        return self._mean.copy()

    @property
    def variance(self) -> np.ndarray:
        """Current running variance (population)."""
        if self._count < 2:
            return np.zeros(self.n_features)
        return self._m2 / self._count

    @property
    def std(self) -> np.ndarray:
        """Current running standard deviation."""
        return np.sqrt(self.variance) + 1e-10  # avoid division by zero


class OnlineDetector:
    """Streaming anomaly detector (S-Algorithm 3).

    Processes agent states one at a time, maintaining running
    statistics and a feature window for z-score based detection.
    """

    def __init__(
        self,
        window_size: int = 100,
        threshold: float = 3.0,
        feature_extractors: Optional[List[Callable[[dict], float]]] = None,
    ):
        """Initialize online detector.

        Args:
            window_size: Size of the sliding feature window.
            threshold: Z-score threshold for anomaly detection.
            feature_extractors: List of functions that extract a float
                feature from an agent state dict. If None, uses default
                extractors.
        """
        self.window_size = window_size
        self.threshold = threshold

        if feature_extractors is None:
            self.feature_extractors = [
                lambda s: s.get("action_count", 0) / max(s.get("time_delta", 1), 1),
                lambda s: float(s.get("belief_changes", 0)),
                lambda s: float(
                    s.get("messages_sent", 0) + s.get("messages_received", 0)
                ),
            ]
        else:
            self.feature_extractors = list(feature_extractors)

        n_features = len(self.feature_extractors)
        self._stats = OnlineStatistics(n_features)
        self._window = CircularBuffer(window_size)

    def _extract_features(self, state: dict) -> np.ndarray:
        """Extract feature vector from agent state."""
        return np.array([f(state) for f in self.feature_extractors])

    def process(self, state: dict) -> Tuple[str, float]:
        """Process a single agent state observation.

        Args:
            state: Agent state dictionary.

        Returns:
            Tuple of (decision, score) where decision is
            "quarantine" or "accept" and score is the anomaly score.
        """
        features = self._extract_features(state)
        self._stats.update(features)
        self._window.push(features)

        # Need at least a few observations for meaningful statistics
        if self._stats.count < 3:
            return "accept", 0.0

        # Compute z-score
        z = (features - self._stats.mean) / self._stats.std
        score = float(np.linalg.norm(z))

        if score > self.threshold:
            return "quarantine", score
        return "accept", score

    def detect_stream(
        self, states: Iterator[dict]
    ) -> Iterator[Tuple[str, float]]:
        """Process a stream of agent states.

        Args:
            states: Iterator of agent state dicts.

        Yields:
            Tuple of (decision, score) for each state.
        """
        for state in states:
            yield self.process(state)
