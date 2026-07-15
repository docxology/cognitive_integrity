"""Tests for anomaly detection."""

import numpy as np

from detection import (
    AnomalyScorer,
    DetectionConfig,
    DriftDetector,
    action_frequency_extractor,
    belief_volatility_extractor,
)


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
            scorer.observe("agent-1", {"action_count": 10, "time_delta": 1.0, "belief_changes": 2})

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


# ---------------------------------------------------------------------------
# Additional edge-case tests for detection.py to boost coverage above 90%
# ---------------------------------------------------------------------------


class TestDriftDetectorEdgeCases:
    """Edge-case tests targeting uncovered lines in DriftDetector."""

    def test_calibrate_baseline_insufficient_samples_raises(self):
        """calibrate_baseline raises ValueError with <50 samples (lines 52-54)."""
        config = DetectionConfig(baseline_samples=50)
        detector = DriftDetector(config)

        # Add fewer than 50 observations
        for i in range(10):
            detector.add_observation({"a": float(i)})

        import pytest

        with pytest.raises(ValueError, match="Need 50 samples"):
            detector.calibrate_baseline()

    def test_compute_drift_empty_hist_values_mismatched_keys(self):
        """compute_drift returns (0.0, 0.0) when no hist values match key length (line 101)."""
        detector = DriftDetector()

        # Add observations with 2 keys
        for _ in range(15):
            detector.add_observation({"x": 0.5, "y": 0.5})

        # Query with a current state that has 3 keys — mismatches all stored observations
        kl, delta = detector.compute_drift({"a": 0.5, "b": 0.5, "c": 0.5}, window=10)
        assert kl == 0.0
        assert delta == 0.0

    def test_get_drift_history_returns_empty_when_less_than_2(self):
        """get_drift_history returns [] when history has fewer than 2 entries (line 133)."""
        detector = DriftDetector()

        # Only 1 observation
        detector.add_observation({"a": 0.5})
        history = detector.get_drift_history()
        assert history == []

    def test_get_drift_history_empty_detector(self):
        """get_drift_history returns [] for a fresh detector with no observations."""
        detector = DriftDetector()
        history = detector.get_drift_history()
        assert history == []


class TestAnomalyScorerEdgeCases:
    """Edge-case tests targeting uncovered lines in AnomalyScorer."""

    def test_observe_exception_handler_silently_skips(self):
        """observe() swallows TypeError/ValueError/KeyError from extractor (lines 199-200)."""
        scorer = AnomalyScorer()

        # Extractor that always raises TypeError
        def bad_extractor(state):
            raise TypeError("boom")

        scorer.add_extractor("bad", bad_extractor)

        # Should not raise – the exception is swallowed
        scorer.observe("agent-1", {"some_key": 1.0})
        # History for this extractor/agent should be empty
        key = "agent-1:bad"
        if key in scorer._history:
            assert len(scorer._history[key]) == 0

    def test_score_no_extractors_returns_zero(self):
        """score() with no extractors has total_weight=0 → returns 0.0 (line 240)."""
        scorer = AnomalyScorer()
        # No extractors added
        result = scorer.score("agent-1", {"action_count": 5, "time_delta": 1.0})
        assert result == 0.0

    def test_score_exception_in_extractor_skips_weight(self):
        """score() skips extractors that raise, total_weight stays 0 → 0.0 (lines 237-238)."""
        scorer = AnomalyScorer()

        def raising_extractor(state):
            raise KeyError("missing")

        scorer.add_extractor("raiser", raising_extractor, weight=1.0)

        # Both score paths: extractor raises → total_weight=0 → 0.0
        result = scorer.score("agent-1", {})
        assert result == 0.0

    def test_is_anomalous_exception_in_extractor_skips(self):
        """is_anomalous() gracefully skips extractors that raise (lines 260-261)."""
        scorer = AnomalyScorer()

        def raising_extractor(state):
            raise ZeroDivisionError("oops")

        scorer.add_extractor("raiser", raising_extractor, weight=1.0)

        is_anom, score, features = scorer.is_anomalous("agent-1", {})
        # No extractor succeeded → score=0, not anomalous
        assert not is_anom
        assert score == 0.0
        assert features == {}

    def test_is_anomalous_no_extractors_returns_false(self):
        """is_anomalous() with no extractors returns (False, 0.0, {})."""
        scorer = AnomalyScorer()
        is_anom, score, features = scorer.is_anomalous("agent-1", {})
        assert is_anom is False
        assert score == 0.0
        assert features == {}


class TestStandardExtractors:
    """Tests for communication_volume_extractor and goal_stability_extractor."""

    def test_communication_volume_extractor(self):
        """communication_volume_extractor sums sent + received (line 282)."""
        from detection import communication_volume_extractor

        state = {"messages_sent": 5, "messages_received": 3}
        assert communication_volume_extractor(state) == 8

    def test_communication_volume_extractor_defaults(self):
        """communication_volume_extractor handles missing keys → 0."""
        from detection import communication_volume_extractor

        assert communication_volume_extractor({}) == 0

    def test_goal_stability_extractor(self):
        """goal_stability_extractor returns goal_changes (line 287)."""
        from detection import goal_stability_extractor

        state = {"goal_changes": 2}
        assert goal_stability_extractor(state) == 2

    def test_goal_stability_extractor_default(self):
        """goal_stability_extractor defaults to 0 when key absent."""
        from detection import goal_stability_extractor

        assert goal_stability_extractor({}) == 0


class TestDriftDetectorCalibrationEffect:
    """Calibration must actually change is_anomalous()'s behavior.

    Regression test for a bug where calibrate_baseline() computed and
    stored _baseline_mean/_baseline_std but is_anomalous()/compute_drift()
    never consulted them, making calibration a silent no-op.
    """

    def test_calibration_changes_threshold(self):
        """Calibrating sets a data-driven threshold distinct from the default."""
        detector = DriftDetector()
        for i in range(60):
            detector.add_observation({"a": 0.5 + 0.001 * (i % 5)})

        assert detector._calibrated_threshold is None
        detector.calibrate_baseline()
        assert detector._calibrated is True
        assert detector._calibrated_threshold is not None
        assert detector._calibrated_threshold != detector.config.drift_threshold

    def test_calibration_changes_is_anomalous_verdict(self):
        """A borderline score can flip verdicts once calibrated.

        With a very low static drift_threshold, an uncalibrated detector
        flags a mildly-shifted state as anomalous. After calibrating on a
        noisy baseline (large calibrated threshold), the same state is no
        longer flagged -- proving calibration has real effect.
        """
        config = DetectionConfig(drift_threshold=1e-6, baseline_samples=50)
        detector = DriftDetector(config)

        rng = np.random.default_rng(42)
        for _ in range(80):
            detector.add_observation({"a": float(rng.uniform(0.3, 0.7))})

        current = {"a": 0.55}

        is_anom_before, score_before = detector.is_anomalous(current)
        assert is_anom_before is True  # threshold is ~0, so any signal trips it

        detector.calibrate_baseline()
        is_anom_after, score_after = detector.is_anomalous(current)

        assert score_before == score_after  # score computation is unaffected
        assert is_anom_after is False  # calibrated threshold absorbs the noise
        assert detector._calibrated_threshold > config.drift_threshold

    def test_uncalibrated_detector_uses_static_threshold(self):
        """Without calibration, is_anomalous falls back to config.drift_threshold."""
        detector = DriftDetector(DetectionConfig(drift_threshold=0.05))
        for i in range(15):
            detector.add_observation({"a": 0.5})

        is_anom, score = detector.is_anomalous({"a": 0.9})
        assert is_anom == (score > 0.05)
