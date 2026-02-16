"""Tests for batch anomaly detection (S-Algorithm 4)."""

import numpy as np

from core.batch_detection import BatchDetector


class TestBatchDetector:
    """Tests for BatchDetector offline analysis pipeline."""

    def test_batch_score_shape(self):
        """batch_score returns correct shape."""
        detector = BatchDetector()
        features = np.random.randn(20, 3)
        scores = detector.batch_score(features)
        assert scores.shape == (20,)

    def test_batch_score_1d_input(self):
        """1D input is reshaped to (1, n_features)."""
        detector = BatchDetector()
        features = np.array([1.0, 2.0, 3.0])
        scores = detector.batch_score(features)
        assert scores.shape == (1,)

    def test_batch_score_nonnegative(self):
        """All scores are non-negative (L2 norm)."""
        detector = BatchDetector()
        features = np.random.randn(50, 4)
        scores = detector.batch_score(features)
        assert np.all(scores >= 0)

    def test_batch_score_outlier_highest(self):
        """Outlier point gets highest score."""
        detector = BatchDetector()
        # 19 normal points clustered near 0, 1 outlier at 100
        features = np.vstack([
            np.random.randn(19, 2) * 0.1,
            np.array([[100.0, 100.0]])
        ])
        scores = detector.batch_score(features)
        assert np.argmax(scores) == 19  # outlier is last

    def test_mine_patterns_empty_input(self):
        """Empty history returns no patterns."""
        detector = BatchDetector()
        patterns = detector.mine_patterns([], np.array([]))
        assert patterns == []

    def test_mine_patterns_finds_anomalies(self):
        """mine_patterns identifies high-scoring observations."""
        detector = BatchDetector()
        history = [{"x": i} for i in range(20)]
        # Scores: first 19 low, last one very high
        scores = np.array([1.0] * 19 + [100.0])
        patterns = detector.mine_patterns(history, scores)
        assert len(patterns) >= 1
        assert 19 in patterns[0]["indices"]
        assert patterns[0]["mean_score"] > 50.0

    def test_mine_patterns_no_anomalies(self):
        """Uniform scores produce no patterns (all below threshold)."""
        detector = BatchDetector()
        history = [{"x": 1.0}] * 10
        scores = np.array([1.0] * 10)
        patterns = detector.mine_patterns(history, scores)
        assert patterns == []

    def test_optimize_thresholds_perfect_separation(self):
        """Perfect separation yields F1 = 1.0."""
        detector = BatchDetector()
        scores = np.array([0.1, 0.2, 0.3, 0.9, 0.95, 1.0])
        labels = np.array([0, 0, 0, 1, 1, 1])
        result = detector.optimize_thresholds(scores, labels)
        assert result["f1"] > 0.9
        assert result["precision"] > 0.9
        assert result["recall"] > 0.9
        assert 0.3 <= result["threshold"] < 0.9

    def test_optimize_thresholds_all_same_label(self):
        """All same labels still returns valid result."""
        detector = BatchDetector()
        scores = np.array([0.1, 0.2, 0.3])
        labels = np.array([1, 1, 1])
        result = detector.optimize_thresholds(scores, labels)
        assert "threshold" in result
        assert "f1" in result

    def test_optimize_thresholds_returns_dict_keys(self):
        """Result dict has expected keys."""
        detector = BatchDetector()
        scores = np.array([0.1, 0.5, 0.9])
        labels = np.array([0, 1, 1])
        result = detector.optimize_thresholds(scores, labels)
        assert set(result.keys()) == {"threshold", "precision", "recall", "f1"}

    def test_analyze_empty_history(self):
        """Empty history returns zero-valued result."""
        detector = BatchDetector()
        result = detector.analyze([])
        assert result["n_samples"] == 0
        assert result["n_anomalous"] == 0
        assert result["patterns"] == []

    def test_analyze_with_numeric_states(self):
        """analyze extracts numeric features automatically."""
        np.random.seed(42)
        detector = BatchDetector()
        history = [
            {"action_count": 10 + np.random.normal(0, 1), "time_delta": 1.0}
            for _ in range(30)
        ]
        result = detector.analyze(history)
        assert result["n_samples"] == 30
        assert len(result["scores"]) == 30
        assert isinstance(result["patterns"], list)

    def test_analyze_with_custom_extractors(self):
        """analyze uses provided feature extractors."""
        detector = BatchDetector()
        extractors = [lambda s: s["x"], lambda s: s["y"]]
        history = [{"x": float(i), "y": float(i * 2)} for i in range(20)]
        result = detector.analyze(history, feature_extractors=extractors)
        assert result["n_samples"] == 20
        assert len(result["scores"]) == 20

    def test_analyze_with_labels(self):
        """analyze includes threshold optimization when labels provided."""
        np.random.seed(42)
        detector = BatchDetector()
        history = [{"val": 1.0}] * 15 + [{"val": 100.0}] * 5
        labels = np.array([0] * 15 + [1] * 5)
        extractors = [lambda s: s["val"]]
        result = detector.analyze(history, feature_extractors=extractors, labels=labels)
        assert "thresholds" in result
        assert result["thresholds"]["f1"] >= 0.0

    def test_analyze_without_labels(self):
        """analyze omits thresholds when no labels given."""
        detector = BatchDetector()
        history = [{"val": 1.0}] * 10
        extractors = [lambda s: s["val"]]
        result = detector.analyze(history, feature_extractors=extractors)
        assert "thresholds" not in result
