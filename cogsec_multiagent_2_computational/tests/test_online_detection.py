"""Tests for online anomaly detection (S-Algorithm 3)."""

import numpy as np
import pytest

from core.online_detection import CircularBuffer, OnlineDetector, OnlineStatistics


class TestCircularBuffer:
    """Tests for CircularBuffer."""

    def test_push_and_len(self):
        """Push items and verify length."""
        buf = CircularBuffer(5)
        assert len(buf) == 0
        buf.push(np.array([1.0]))
        assert len(buf) == 1
        buf.push(np.array([2.0]))
        assert len(buf) == 2

    def test_maxlen_property(self):
        """Maxlen property returns configured size."""
        buf = CircularBuffer(10)
        assert buf.maxlen == 10

    def test_wrap_around(self):
        """Buffer wraps around when full."""
        buf = CircularBuffer(3)
        for i in range(5):
            buf.push(np.array([float(i)]))
        assert len(buf) == 3
        arr = buf.to_array()
        np.testing.assert_array_equal(arr, [[2.0], [3.0], [4.0]])

    def test_to_array_empty(self):
        """Empty buffer returns empty array."""
        buf = CircularBuffer(5)
        arr = buf.to_array()
        assert len(arr) == 0

    def test_to_array_shape(self):
        """to_array returns correct 2D shape."""
        buf = CircularBuffer(10)
        for i in range(4):
            buf.push(np.array([float(i), float(i) * 2]))
        arr = buf.to_array()
        assert arr.shape == (4, 2)

    def test_invalid_maxlen(self):
        """Zero or negative maxlen raises ValueError."""
        with pytest.raises(ValueError, match="maxlen must be positive"):
            CircularBuffer(0)
        with pytest.raises(ValueError, match="maxlen must be positive"):
            CircularBuffer(-1)

    def test_single_capacity(self):
        """Buffer with maxlen=1 keeps only latest item."""
        buf = CircularBuffer(1)
        buf.push(np.array([10.0]))
        buf.push(np.array([20.0]))
        assert len(buf) == 1
        np.testing.assert_array_equal(buf.to_array(), [[20.0]])


class TestOnlineStatistics:
    """Tests for Welford's online statistics."""

    def test_single_observation(self):
        """Single observation gives mean = observation, variance = 0."""
        stats = OnlineStatistics(2)
        stats.update(np.array([3.0, 5.0]))
        assert stats.count == 1
        np.testing.assert_array_almost_equal(stats.mean, [3.0, 5.0])
        np.testing.assert_array_almost_equal(stats.variance, [0.0, 0.0])

    def test_running_mean_correctness(self):
        """Running mean matches numpy mean."""
        np.random.seed(42)
        stats = OnlineStatistics(3)
        data = np.random.randn(50, 3)
        for row in data:
            stats.update(row)
        np.testing.assert_array_almost_equal(stats.mean, np.mean(data, axis=0), decimal=10)

    def test_running_variance_correctness(self):
        """Running variance matches numpy population variance."""
        np.random.seed(42)
        stats = OnlineStatistics(3)
        data = np.random.randn(100, 3)
        for row in data:
            stats.update(row)
        np.testing.assert_array_almost_equal(
            stats.variance, np.var(data, axis=0), decimal=6
        )

    def test_std_avoids_zero(self):
        """Std has epsilon to avoid division by zero."""
        stats = OnlineStatistics(2)
        stats.update(np.array([1.0, 1.0]))
        # With only 1 observation, variance is 0, std should be ~1e-10
        assert all(s > 0 for s in stats.std)

    def test_count_tracking(self):
        """Count increments with each update."""
        stats = OnlineStatistics(1)
        for i in range(10):
            stats.update(np.array([float(i)]))
        assert stats.count == 10

    def test_invalid_n_features(self):
        """Zero or negative n_features raises ValueError."""
        with pytest.raises(ValueError, match="n_features must be positive"):
            OnlineStatistics(0)
        with pytest.raises(ValueError, match="n_features must be positive"):
            OnlineStatistics(-3)


class TestOnlineDetector:
    """Tests for streaming anomaly detector."""

    def test_normal_stream_no_alerts(self):
        """Normal consistent states produce 'accept' decisions."""
        detector = OnlineDetector(threshold=5.0)
        for _ in range(20):
            state = {"action_count": 10, "time_delta": 1.0,
                     "belief_changes": 2, "messages_sent": 5,
                     "messages_received": 3}
            decision, score = detector.process(state)
            # After warmup, all should accept
        assert decision == "accept"

    def test_anomalous_triggers_quarantine(self):
        """Extreme outlier triggers quarantine decision."""
        detector = OnlineDetector(threshold=3.0)
        # Build baseline
        for _ in range(30):
            detector.process({"action_count": 10, "time_delta": 1.0,
                              "belief_changes": 2, "messages_sent": 5,
                              "messages_received": 3})
        # Inject anomaly
        decision, score = detector.process(
            {"action_count": 10000, "time_delta": 1.0,
             "belief_changes": 500, "messages_sent": 1000,
             "messages_received": 1000}
        )
        assert decision == "quarantine"
        assert score > 3.0

    def test_detect_stream_generator(self):
        """detect_stream yields results for each state."""
        detector = OnlineDetector(threshold=5.0)
        states = [
            {"action_count": 10, "time_delta": 1.0, "belief_changes": 2,
             "messages_sent": 5, "messages_received": 3}
            for _ in range(10)
        ]
        results = list(detector.detect_stream(iter(states)))
        assert len(results) == 10
        for decision, score in results:
            assert decision in ("accept", "quarantine")
            assert isinstance(score, float)

    def test_custom_feature_extractors(self):
        """Custom extractors are used instead of defaults."""
        extractors = [lambda s: s.get("x", 0.0)]
        detector = OnlineDetector(feature_extractors=extractors)
        assert len(detector.feature_extractors) == 1
        decision, score = detector.process({"x": 1.0})
        assert decision == "accept"

    def test_warmup_period_accepts_all(self):
        """First few observations always accept (insufficient statistics)."""
        detector = OnlineDetector(threshold=0.0001)  # Very strict
        decision1, score1 = detector.process(
            {"action_count": 10, "time_delta": 1.0, "belief_changes": 2,
             "messages_sent": 5, "messages_received": 3}
        )
        assert decision1 == "accept"
        assert score1 == 0.0

    def test_empty_stream(self):
        """Empty stream yields nothing."""
        detector = OnlineDetector()
        results = list(detector.detect_stream(iter([])))
        assert results == []

    def test_statistics_accumulation(self):
        """Internal statistics track observation count."""
        detector = OnlineDetector()
        for _ in range(15):
            detector.process({"action_count": 10, "time_delta": 1.0,
                              "belief_changes": 0, "messages_sent": 0,
                              "messages_received": 0})
        assert detector._stats.count == 15
        assert len(detector._window) == 15
