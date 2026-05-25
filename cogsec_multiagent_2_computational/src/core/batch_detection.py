"""
from __future__ import annotations

Batch Detection for Cognitive Security.

Implements offline batch analysis pipeline (S-Algorithm 4).
"""

from typing import Dict, List, Optional

import numpy as np


class BatchDetector:
    """Offline batch analysis pipeline (S-Algorithm 4).

    Analyzes a collection of historical observations to identify
    anomalous patterns, mine attack signatures, and optimize
    detection thresholds.
    """

    def __init__(self, detectors: Optional[list] = None):
        """Initialize batch detector.

        Args:
            detectors: List of detector instances with a `score` or
                `process` method. If None, uses internal scoring.
        """
        self._detectors = detectors or []

    def batch_score(self, features: np.ndarray) -> np.ndarray:
        """Score a batch of feature vectors for anomalies.

        Computes z-scores against the batch mean/std for each feature,
        then returns the L2 norm of the z-score vector per sample.

        Args:
            features: Array of shape (n_samples, n_features).

        Returns:
            Array of shape (n_samples,) with anomaly scores.
        """
        features = np.asarray(features, dtype=float)
        if features.ndim == 1:
            features = features.reshape(1, -1)

        mean = np.mean(features, axis=0)
        std = np.std(features, axis=0) + 1e-10

        z_scores = (features - mean) / std
        scores = np.linalg.norm(z_scores, axis=1)
        return scores

    def mine_patterns(
        self, history: List[dict], scores: np.ndarray
    ) -> List[Dict]:
        """Mine anomalous patterns from scored history.

        Identifies clusters of high-scoring observations and extracts
        common features.

        Args:
            history: List of agent state dicts.
            scores: Anomaly scores from batch_score.

        Returns:
            List of pattern dicts with keys: indices, mean_score,
            common_features.
        """
        if len(history) == 0 or len(scores) == 0:
            return []

        scores = np.asarray(scores)
        threshold = np.mean(scores) + 2 * np.std(scores)

        anomalous_indices = np.where(scores > threshold)[0]
        if len(anomalous_indices) == 0:
            return []

        # Extract common features from anomalous observations
        anomalous_states = [history[i] for i in anomalous_indices]
        common_keys = set(anomalous_states[0].keys())
        for s in anomalous_states[1:]:
            common_keys &= set(s.keys())

        # Find features with high variance among anomalous samples
        patterns = []
        pattern = {
            "indices": anomalous_indices.tolist(),
            "mean_score": float(np.mean(scores[anomalous_indices])),
            "count": len(anomalous_indices),
            "common_features": sorted(common_keys),
        }
        patterns.append(pattern)

        return patterns

    def optimize_thresholds(
        self,
        scores: np.ndarray,
        labels: np.ndarray,
        n_candidates: int = 100,
    ) -> Dict[str, float]:
        """Find optimal detection threshold via F1 maximization.

        Searches over candidate thresholds between min and max scores
        to find the threshold that maximizes F1 score.

        Args:
            scores: Anomaly scores array.
            labels: Binary labels (1 = attack, 0 = benign).
            n_candidates: Number of threshold candidates to evaluate.

        Returns:
            Dict with keys: threshold, precision, recall, f1.
        """
        scores = np.asarray(scores, dtype=float)
        labels = np.asarray(labels, dtype=int)

        candidates = np.linspace(
            float(np.min(scores)), float(np.max(scores)), n_candidates
        )

        best_f1 = -1.0
        best_result: Dict[str, float] = {
            "threshold": float(np.mean(scores)),
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
        }

        for t in candidates:
            predicted = (scores > t).astype(int)
            tp = int(np.sum((predicted == 1) & (labels == 1)))
            fp = int(np.sum((predicted == 1) & (labels == 0)))
            fn = int(np.sum((predicted == 0) & (labels == 1)))

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (
                2 * precision * recall / (precision + recall)
                if (precision + recall) > 0
                else 0.0
            )

            if f1 > best_f1:
                best_f1 = f1
                best_result = {
                    "threshold": float(t),
                    "precision": precision,
                    "recall": recall,
                    "f1": f1,
                }

        return best_result

    def analyze(
        self,
        history: List[dict],
        feature_extractors: Optional[list] = None,
        labels: Optional[np.ndarray] = None,
    ) -> Dict:
        """Run complete batch analysis pipeline.

        Extracts features, scores anomalies, mines patterns,
        and optionally optimizes thresholds.

        Args:
            history: List of agent state dicts.
            feature_extractors: List of callables that extract float
                features from state dicts. If None, extracts all
                numeric values.
            labels: Optional binary labels for threshold optimization.

        Returns:
            Dict with keys: scores, patterns, thresholds (if labels provided),
            n_samples, n_anomalous.
        """
        if len(history) == 0:
            return {
                "scores": np.array([]),
                "patterns": [],
                "n_samples": 0,
                "n_anomalous": 0,
            }

        # Extract features
        if feature_extractors:
            features = np.array(
                [[f(state) for f in feature_extractors] for state in history]
            )
        else:
            # Use all numeric values from state dicts
            numeric_keys = sorted(
                k
                for k, v in history[0].items()
                if isinstance(v, (int, float))
            )
            features = np.array(
                [[state.get(k, 0.0) for k in numeric_keys] for state in history]
            )

        # Score
        scores = self.batch_score(features)

        # Mine patterns
        patterns = self.mine_patterns(history, scores)

        # Count anomalous
        threshold = np.mean(scores) + 2 * np.std(scores)
        n_anomalous = int(np.sum(scores > threshold))

        result: Dict = {
            "scores": scores,
            "patterns": patterns,
            "n_samples": len(history),
            "n_anomalous": n_anomalous,
        }

        # Optimize thresholds if labels provided
        if labels is not None:
            result["thresholds"] = self.optimize_thresholds(scores, labels)

        return result
