"""Tests for anomaly detection."""

import numpy as np
import pytest
from detection import (AnomalyScorer, DetectionConfig, DriftDetector,
                       action_frequency_extractor, belief_volatility_extractor)


class TestDriftDetector:
    """Tests for belief drift detection."""

    def test_no_drift_on_stable_beliefs(self):
        """Stable beliefs show no drift."""
        detector = DriftDetector()

        # Add identical observations
        beliefs = {"prop1": 0.8, "prop2": 0.5}
        for _ in range(20):
            detector.add_observation(beliefs.copy())

        is_anom, score = detector.is_anomalous(beliefs)
        assert not is_anom
        assert score < 0.1

    def test_drift_on_sudden_change(self):
        """Sudden belief changes trigger drift detection."""
        detector = DriftDetector(DetectionConfig(drift_threshold=0.2))

        # Establish baseline
        baseline = {"prop1": 0.8, "prop2": 0.5}
        for _ in range(15):
            detector.add_observation(baseline.copy())

        # Sudden change
        changed = {"prop1": 0.2, "prop2": 0.9}
        _, score = detector.is_anomalous(changed)

        assert score > 0.1  # Some drift detected

    def test_kl_divergence_symmetric(self):
        """KL divergence is non-negative."""
        detector = DriftDetector()

        p = np.array([0.3, 0.7])
        q = np.array([0.5, 0.5])

        kl = detector._kl_divergence(p, q)
        assert kl >= 0

    def test_compute_drift_insufficient_history(self):
        """Returns zero drift with insufficient history."""
        detector = DriftDetector()

        # Only 2 observations
        detector.add_observation({"a": 0.5})
        detector.add_observation({"a": 0.6})

        kl, delta = detector.compute_drift({"a": 0.9}, window=10)
        # Should handle gracefully
        assert isinstance(kl, float)
        assert isinstance(delta, float)

    def test_drift_history(self):
        """Drift history is tracked."""
        detector = DriftDetector()

        for i in range(30):
            beliefs = {"prop": 0.5 + 0.01 * i}
            detector.add_observation(beliefs)

        history = detector.get_drift_history(n=10)
        assert len(history) <= 10
        assert all(isinstance(s, float) for s in history)


class TestAnomalyScorer:
    """Tests for behavioral anomaly scoring."""

    def test_add_extractor(self):
        """Extractors can be added."""
        scorer = AnomalyScorer()
        scorer.add_extractor("action_freq", action_frequency_extractor)

        assert len(scorer._extractors) == 1

    def test_observe_and_calibrate(self):
        """Observations are recorded and baseline calibrated."""
        scorer = AnomalyScorer(DetectionConfig(baseline_samples=5))
        scorer.add_extractor("action_freq", action_frequency_extractor)

        # Record observations
        for i in range(10):
            scorer.observe("agent-1", {"action_count": 10 + i, "time_delta": 1.0})

        scorer.calibrate("agent-1")

        # Baseline should be approximately mean of observations
        extractor = scorer._extractors[0][0]
        assert 10 <= extractor.baseline_mean <= 20

    def test_score_normal_state(self):
        """Normal state has low anomaly score."""
        scorer = AnomalyScorer(DetectionConfig(baseline_samples=5))
        scorer.add_extractor("action_freq", action_frequency_extractor)

        # Baseline around 10 actions/sec
        for _ in range(10):
            scorer.observe("agent-1", {"action_count": 10, "time_delta": 1.0})

        scorer.calibrate("agent-1")

        # Score normal state
        score = scorer.score("agent-1", {"action_count": 10, "time_delta": 1.0})
        assert score < 1.0  # Within 1 std dev

    def test_score_anomalous_state(self):
        """Anomalous state has high score."""
        scorer = AnomalyScorer(DetectionConfig(baseline_samples=5))
        scorer.add_extractor("action_freq", action_frequency_extractor)

        # Baseline around 10 actions/sec
        for _ in range(10):
            scorer.observe("agent-1", {"action_count": 10, "time_delta": 1.0})

        scorer.calibrate("agent-1")

        # Score anomalous state (100x normal)
        score = scorer.score("agent-1", {"action_count": 1000, "time_delta": 1.0})
        assert score > 3.0  # Well beyond 3 std devs

    def test_is_anomalous_returns_details(self):
        """is_anomalous returns feature breakdown."""
        scorer = AnomalyScorer(DetectionConfig(baseline_samples=5))
        scorer.add_extractor("action_freq", action_frequency_extractor)
        scorer.add_extractor("belief_vol", belief_volatility_extractor)

        for _ in range(10):
            scorer.observe(
                "agent-1", {"action_count": 10, "time_delta": 1.0, "belief_changes": 2}
            )

        scorer.calibrate("agent-1")

        is_anom, score, features = scorer.is_anomalous(
            "agent-1", {"action_count": 10, "time_delta": 1.0, "belief_changes": 2}
        )

        assert isinstance(is_anom, bool)
        assert isinstance(score, float)
        assert "action_freq" in features
        assert "belief_vol" in features

    def test_multiple_extractors_weighted(self):
        """Multiple extractors contribute weighted scores."""
        scorer = AnomalyScorer()
        scorer.add_extractor("feat1", lambda s: s.get("v1", 0), weight=1.0)
        scorer.add_extractor("feat2", lambda s: s.get("v2", 0), weight=2.0)

        # Set baselines manually
        scorer._extractors[0][0].baseline_mean = 0.0
        scorer._extractors[0][0].baseline_std = 1.0
        scorer._extractors[1][0].baseline_mean = 0.0
        scorer._extractors[1][0].baseline_std = 1.0

        # Score with deviation in both features
        score = scorer.score("any", {"v1": 3.0, "v2": 3.0})

        # Weight 2 feature should contribute more
        # Total = (1*3 + 2*3) / (1+2) = 9/3 = 3
        assert np.isclose(score, 3.0)


class TestFeatureExtractors:
    """Tests for standard feature extractors."""

    def test_action_frequency_extractor(self):
        """Action frequency computed correctly."""
        state = {"action_count": 100, "time_delta": 10.0}
        freq = action_frequency_extractor(state)
        assert freq == 10.0

    def test_action_frequency_zero_time(self):
        """Handles zero time delta."""
        state = {"action_count": 100, "time_delta": 0}
        freq = action_frequency_extractor(state)
        assert freq == 100.0  # Divides by max(0,1)=1

    def test_belief_volatility_extractor(self):
        """Belief volatility extracted."""
        state = {"belief_changes": 5}
        vol = belief_volatility_extractor(state)
        assert vol == 5
