"""Score fusion strategies for parallel defense pipelines.

Each strategy takes a list of :class:`DefenseResult` objects produced by
independent defense modules and produces a single (detected, score) tuple
that represents the fused verdict.

Strategies implemented:
  - WeightedAverageFusion: weighted average of scores.
  - MajorityVotingFusion: majority vote on detection flags.
  - MaxScoreFusion: maximum score (most conservative).
  - AttentionFusion: softmax-attention over module scores.
  - LearnedFusion: simple numpy MLP trained via gradient descent.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

import numpy as np

from utils.types import DefenseResult

# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class FusionStrategy(ABC):
    """Abstract base for score-fusion strategies."""

    @abstractmethod
    def fuse(self, results: List[DefenseResult]) -> Tuple[bool, float]:
        """Fuse a list of module results into a single verdict.

        Returns:
            (detected, score) where *detected* is the binary flag and
            *score* is the fused confidence in [0, 1].
        """
        ...


# ---------------------------------------------------------------------------
# Weighted average
# ---------------------------------------------------------------------------

class WeightedAverageFusion(FusionStrategy):
    """Weighted average of module scores.

    If no weights are given, uniform weights are used.  The input is
    detected if the fused score exceeds *threshold*.

    Args:
        weights: Per-module weights (length must match results list).
        threshold: Detection threshold (default 0.5).
    """

    def __init__(self, weights: Optional[List[float]] = None, threshold: float = 0.5) -> None:
        self.weights = weights
        self.threshold = threshold

    def fuse(self, results: List[DefenseResult]) -> Tuple[bool, float]:
        if not results:
            return False, 0.0

        scores = np.array([r.score for r in results], dtype=np.float64)

        if self.weights is not None:
            if len(self.weights) != len(results):
                raise ValueError(
                    f"Weight count ({len(self.weights)}) != result count ({len(results)})"
                )
            w = np.array(self.weights, dtype=np.float64)
        else:
            w = np.ones(len(results), dtype=np.float64)

        w_sum = w.sum()
        if w_sum == 0:
            return False, 0.0

        fused = float(np.dot(w, scores) / w_sum)
        return fused >= self.threshold, fused


# ---------------------------------------------------------------------------
# Majority voting
# ---------------------------------------------------------------------------

class MajorityVotingFusion(FusionStrategy):
    """Majority vote on detection flags.

    Detected if strictly more than half of the modules flag the input.
    The score is the fraction of modules that voted ``detected=True``.

    Args:
        threshold: Fraction threshold for majority (default 0.5, i.e. >50%).
    """

    def __init__(self, threshold: float = 0.5) -> None:
        self.threshold = threshold

    def fuse(self, results: List[DefenseResult]) -> Tuple[bool, float]:
        if not results:
            return False, 0.0

        votes = sum(1 for r in results if r.detected)
        fraction = votes / len(results)
        return fraction > self.threshold, fraction


# ---------------------------------------------------------------------------
# Max score
# ---------------------------------------------------------------------------

class MaxScoreFusion(FusionStrategy):
    """Maximum score across modules (most conservative / sensitive).

    Detected if the maximum score exceeds *threshold*.

    Args:
        threshold: Detection threshold (default 0.5).
    """

    def __init__(self, threshold: float = 0.5) -> None:
        self.threshold = threshold

    def fuse(self, results: List[DefenseResult]) -> Tuple[bool, float]:
        if not results:
            return False, 0.0

        max_score = max(r.score for r in results)
        return max_score >= self.threshold, max_score


# ---------------------------------------------------------------------------
# Attention fusion
# ---------------------------------------------------------------------------

class AttentionFusion(FusionStrategy):
    """Softmax-attention over module scores.

    Computes attention weights as softmax(scores / temperature) and then
    returns the attention-weighted sum of scores.

    Args:
        temperature: Temperature for the softmax (default 1.0).
            Lower values make the weighting peakier.
        threshold: Detection threshold (default 0.5).
    """

    def __init__(self, temperature: float = 1.0, threshold: float = 0.5) -> None:
        if temperature <= 0:
            raise ValueError("temperature must be positive")
        self.temperature = temperature
        self.threshold = threshold

    def fuse(self, results: List[DefenseResult]) -> Tuple[bool, float]:
        if not results:
            return False, 0.0

        scores = np.array([r.score for r in results], dtype=np.float64)

        # Numerically stable softmax
        scaled = scores / self.temperature
        shifted = scaled - scaled.max()
        exp_vals = np.exp(shifted)
        attention = exp_vals / exp_vals.sum()

        fused = float(np.dot(attention, scores))
        return fused >= self.threshold, fused


# ---------------------------------------------------------------------------
# Learned fusion (numpy-only MLP)
# ---------------------------------------------------------------------------

class LearnedFusion(FusionStrategy):
    """Simple single-hidden-layer MLP for learned score fusion.

    Architecture: input(n) -> hidden(hidden_dim, tanh) -> output(1, sigmoid)

    Trained with simple gradient descent (no external ML libraries).

    Args:
        hidden_dim: Hidden layer size (default 16).
        threshold: Detection threshold for the sigmoid output (default 0.5).
        learning_rate: SGD learning rate (default 0.01).
        n_epochs: Training epochs (default 100).
    """

    def __init__(
        self,
        hidden_dim: int = 16,
        threshold: float = 0.5,
        learning_rate: float = 0.01,
        n_epochs: int = 100,
    ) -> None:
        self.hidden_dim = hidden_dim
        self.threshold = threshold
        self.learning_rate = learning_rate
        self.n_epochs = n_epochs

        # Weights initialised lazily on first fit / fuse
        self._W1: Optional[np.ndarray] = None
        self._b1: Optional[np.ndarray] = None
        self._W2: Optional[np.ndarray] = None
        self._b2: Optional[np.ndarray] = None
        self._fitted = False

    # -- internal helpers --

    @staticmethod
    def _sigmoid(x: np.ndarray) -> np.ndarray:
        """Numerically stable sigmoid."""
        # Numerically stable sigmoid using masking to prevent overflow
        result = np.zeros_like(x)
        mask = x >= 0
        
        # For x >= 0: 1 / (1 + exp(-x))
        z_pos = np.exp(-x[mask])
        result[mask] = 1.0 / (1.0 + z_pos)
        
        # For x < 0: exp(x) / (1 + exp(x))
        z_neg = np.exp(x[~mask])
        result[~mask] = z_neg / (1.0 + z_neg)
        
        return result

    @staticmethod
    def _sigmoid_deriv(s: np.ndarray) -> np.ndarray:
        return s * (1.0 - s)

    @staticmethod
    def _tanh_deriv(t: np.ndarray) -> np.ndarray:
        return 1.0 - t ** 2

    def _init_weights(self, input_dim: int, rng: np.random.Generator) -> None:
        """Xavier initialization."""
        scale1 = np.sqrt(2.0 / (input_dim + self.hidden_dim))
        self._W1 = rng.normal(0, scale1, (input_dim, self.hidden_dim))
        self._b1 = np.zeros(self.hidden_dim)

        scale2 = np.sqrt(2.0 / (self.hidden_dim + 1))
        self._W2 = rng.normal(0, scale2, (self.hidden_dim, 1))
        self._b2 = np.zeros(1)

    def _forward(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Forward pass. Returns (hidden, output_pre_activation, output)."""
        z1 = X @ self._W1 + self._b1  # (N, hidden)
        h = np.tanh(z1)               # (N, hidden)
        z2 = h @ self._W2 + self._b2  # (N, 1)
        o = self._sigmoid(z2)          # (N, 1)
        return h, z2, o

    # -- public API --

    def fit(
        self,
        results_list: List[List[DefenseResult]],
        labels: List[bool],
        seed: int = 42,
    ) -> List[float]:
        """Train the MLP on labeled fusion examples.

        Args:
            results_list: Each element is a list of DefenseResult (one per module)
                for a single input sample.
            labels: Ground-truth detection labels for each sample.
            seed: Random seed for weight initialisation.

        Returns:
            Loss history (one entry per epoch).
        """
        if not results_list:
            raise ValueError("Cannot fit with empty training data")

        rng = np.random.default_rng(seed)

        # Build feature matrix: each row = scores from all modules
        X = np.array(
            [[r.score for r in sample] for sample in results_list],
            dtype=np.float64,
        )
        y = np.array(labels, dtype=np.float64).reshape(-1, 1)
        N, input_dim = X.shape

        self._init_weights(input_dim, rng)

        losses: List[float] = []

        for epoch in range(self.n_epochs):
            # Forward
            h, z2, o = self._forward(X)

            # Binary cross-entropy loss (with clipping for numerical stability)
            eps = 1e-12
            o_clip = np.clip(o, eps, 1 - eps)
            loss = -np.mean(y * np.log(o_clip) + (1 - y) * np.log(1 - o_clip))
            losses.append(float(loss))

            # Backward
            dL_do = (o_clip - y) / (o_clip * (1 - o_clip) + eps)  # (N, 1)
            do_dz2 = self._sigmoid_deriv(o)                        # (N, 1)
            delta2 = dL_do * do_dz2 / N                            # (N, 1)

            dW2 = h.T @ delta2                                     # (hidden, 1)
            db2 = delta2.sum(axis=0)                                # (1,)

            dh = delta2 @ self._W2.T                               # (N, hidden)
            dtanh = self._tanh_deriv(h)                             # (N, hidden)
            delta1 = dh * dtanh                                    # (N, hidden)

            dW1 = X.T @ delta1                                     # (input, hidden)
            db1 = delta1.sum(axis=0)                                # (hidden,)

            # SGD update
            self._W1 -= self.learning_rate * dW1
            self._b1 -= self.learning_rate * db1
            self._W2 -= self.learning_rate * dW2
            self._b2 -= self.learning_rate * db2

        self._fitted = True
        return losses

    def fuse(self, results: List[DefenseResult]) -> Tuple[bool, float]:
        """Fuse module results using the trained MLP.

        If the model has not been fitted, falls back to max-score fusion.
        """
        if not results:
            return False, 0.0

        scores = np.array([[r.score for r in results]], dtype=np.float64)  # (1, n)

        if not self._fitted or self._W1 is None:
            # Fallback: max score
            max_s = float(scores.max())
            return max_s >= self.threshold, max_s

        _, _, o = self._forward(scores)
        fused = float(o[0, 0])
        return fused >= self.threshold, fused
