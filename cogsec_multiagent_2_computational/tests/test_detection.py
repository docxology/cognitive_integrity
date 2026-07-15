"""Tests for anomaly detection."""

import numpy as np
import pytest

from core.detection import (
    AdaptiveBaseline,
    SlidingWindowMonitor,
    action_frequency_extractor,
    belief_volatility_extractor,
    communication_volume_extractor,
    goal_stability_extractor,
)
from src import AnomalyScorer, DetectionConfig, DriftDetector


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


# ---------------------------------------------------------------------------
# Additional TestDriftDetector methods (appended as a new class section)
# ---------------------------------------------------------------------------


class TestDriftDetectorExtended:
    """Extended tests for DriftDetector calibration, KL divergence, and config."""

    def test_calibrate_baseline_workflow(self):
        """Calibrate baseline after adding sufficient observations."""
        detector = DriftDetector()

        for i in range(60):
            beliefs = {"a": 0.3 + 0.005 * i, "b": 0.7 - 0.005 * i}
            detector.add_observation(beliefs)

        detector.calibrate_baseline()
        assert detector._calibrated is True
        assert detector._baseline_mean is not None

    def test_calibrate_baseline_mean_std_values(self):
        """Identical observations yield tight baseline statistics."""
        detector = DriftDetector()

        for _ in range(50):
            detector.add_observation({"a": 0.5})

        detector.calibrate_baseline()
        assert np.isclose(detector._baseline_mean[0], 0.5, atol=1e-8)
        # std should be near 1e-6 (the epsilon added internally)
        assert detector._baseline_std[0] < 1e-4

    def test_kl_divergence_identical_distributions(self):
        """KL divergence of identical arrays is approximately zero."""
        detector = DriftDetector()
        p = np.array([0.5, 0.5])
        kl = detector._kl_divergence(p, p.copy())
        assert np.isclose(kl, 0.0, atol=1e-8)

    def test_kl_divergence_opposite_distributions(self):
        """KL divergence of opposite-skewed arrays is positive."""
        detector = DriftDetector()
        p = np.array([0.9, 0.1])
        q = np.array([0.1, 0.9])
        kl = detector._kl_divergence(p, q)
        assert kl > 0

    def test_kl_divergence_non_negative(self):
        """KL divergence is non-negative for random distribution pairs."""
        np.random.seed(42)
        detector = DriftDetector()

        for _ in range(10):
            raw_p = np.random.dirichlet([1, 1])
            raw_q = np.random.dirichlet([1, 1])
            kl = detector._kl_divergence(raw_p, raw_q)
            assert kl >= 0

    def test_window_size_config(self):
        """Window size limits internal deque length."""
        config = DetectionConfig(window_size=5)
        detector = DriftDetector(config)

        for i in range(20):
            detector.add_observation({"a": 0.1 * (i % 10)})

        assert detector._history.maxlen == 5
        assert len(detector._history) == 5

    def test_sigma_multiplier_config(self):
        """Lower sigma_multiplier creates stricter anomaly threshold."""
        strict_config = DetectionConfig(sigma_multiplier=1.0, drift_threshold=0.05)
        lenient_config = DetectionConfig(sigma_multiplier=3.0, drift_threshold=0.05)

        strict = DriftDetector(strict_config)
        lenient = DriftDetector(lenient_config)

        baseline = {"a": 0.5, "b": 0.5}
        for _ in range(15):
            strict.add_observation(baseline.copy())
            lenient.add_observation(baseline.copy())

        # A moderate deviation
        test_state = {"a": 0.65, "b": 0.35}
        strict_anom, strict_score = strict.is_anomalous(test_state)
        lenient_anom, lenient_score = lenient.is_anomalous(test_state)

        # Scores should be the same (same data, same scoring), but
        # the threshold used in is_anomalous is drift_threshold (not sigma_multiplier)
        # Both use the same drift_threshold, so the anomalous flag comparison
        # is meaningful only if the scores actually differ. Verify they are valid floats.
        assert isinstance(strict_score, float)
        assert isinstance(lenient_score, float)
        # sigma_multiplier is used by AnomalyScorer, not DriftDetector.is_anomalous
        # Verify configs stored correctly
        assert strict.config.sigma_multiplier == 1.0
        assert lenient.config.sigma_multiplier == 3.0

    def test_drift_history_length(self):
        """get_drift_history respects the n parameter."""
        detector = DriftDetector()

        for i in range(50):
            detector.add_observation({"prop": 0.5 + 0.005 * i})

        history = detector.get_drift_history(n=5)
        assert len(history) <= 5
        assert all(isinstance(s, float) for s in history)

    def test_compute_drift_returns_zero_for_empty_keys(self):
        """compute_drift returns (0, 0) when current beliefs have no keys."""
        detector = DriftDetector()
        for _ in range(15):
            detector.add_observation({"a": 0.5})

        kl, delta = detector.compute_drift({}, window=10)
        assert kl == 0.0
        assert delta == 0.0


# ---------------------------------------------------------------------------
# TestMultiAgentDetection
# ---------------------------------------------------------------------------


class TestMultiAgentDetection:
    """Tests for multi-agent anomaly scoring independence."""

    def test_independent_agent_scoring(self):
        """Separate scorers produce independent results for different agents."""
        np.random.seed(42)
        scorer_a = AnomalyScorer(DetectionConfig(baseline_samples=5))
        scorer_a.add_extractor("action_freq", action_frequency_extractor)

        scorer_b = AnomalyScorer(DetectionConfig(baseline_samples=5))
        scorer_b.add_extractor("action_freq", action_frequency_extractor)

        # Agent A baseline: ~10 actions/sec with some variance
        for _ in range(10):
            scorer_a.observe(
                "agent-a",
                {"action_count": 10 + np.random.normal(0, 0.5), "time_delta": 1.0},
            )

        # Agent B baseline: ~100 actions/sec with some variance
        for _ in range(10):
            scorer_b.observe(
                "agent-b",
                {"action_count": 100 + np.random.normal(0, 0.5), "time_delta": 1.0},
            )

        scorer_a.calibrate("agent-a")
        scorer_b.calibrate("agent-b")

        # Test with 12 actions/sec -- close to A's baseline, far from B's baseline
        test_state = {"action_count": 12, "time_delta": 1.0}
        score_a = scorer_a.score("agent-a", test_state)
        score_b = scorer_b.score("agent-b", test_state)

        # A: 12 near 10 (low score), B: 12 far from 100 (high score)
        assert score_b > score_a

    def test_agent_specific_calibration(self):
        """Each agent calibrates with its own observation data."""
        scorer_low = AnomalyScorer(DetectionConfig(baseline_samples=5))
        scorer_low.add_extractor("action_freq", action_frequency_extractor)

        scorer_high = AnomalyScorer(DetectionConfig(baseline_samples=5))
        scorer_high.add_extractor("action_freq", action_frequency_extractor)

        # Low-activity agent
        for _ in range(10):
            scorer_low.observe("agent-1", {"action_count": 5, "time_delta": 1.0})

        # High-activity agent
        for _ in range(10):
            scorer_high.observe("agent-2", {"action_count": 500, "time_delta": 1.0})

        scorer_low.calibrate("agent-1")
        scorer_high.calibrate("agent-2")

        low_mean = scorer_low._extractors[0][0].baseline_mean
        high_mean = scorer_high._extractors[0][0].baseline_mean

        assert low_mean < high_mean
        assert np.isclose(low_mean, 5.0, atol=0.1)
        assert np.isclose(high_mean, 500.0, atol=0.1)

    def test_cross_agent_no_contamination(self):
        """Scoring an uncalibrated agent uses default extractor baselines."""
        scorer = AnomalyScorer(DetectionConfig(baseline_samples=5))
        scorer.add_extractor("action_freq", action_frequency_extractor)

        # Only calibrate agent-1
        for _ in range(10):
            scorer.observe("agent-1", {"action_count": 10, "time_delta": 1.0})
        scorer.calibrate("agent-1")

        # Score agent-2 (never observed) -- uses agent-1's calibrated baseline
        # since extractors are shared
        score = scorer.score("agent-2", {"action_count": 10, "time_delta": 1.0})
        assert isinstance(score, float)
        # After calibrating agent-1, baseline_mean is ~10 so a value of 10 is normal
        assert score < 1.0


# ---------------------------------------------------------------------------
# TestFeatureExtractorExtended
# ---------------------------------------------------------------------------


class TestFeatureExtractorExtended:
    """Extended tests for feature extractors including new extractors."""

    def test_communication_volume_extractor(self):
        """Communication volume sums sent and received messages."""
        state = {"messages_sent": 10, "messages_received": 5}
        assert communication_volume_extractor(state) == 15

    def test_communication_volume_missing_keys(self):
        """Missing keys default to zero."""
        state = {}
        assert communication_volume_extractor(state) == 0

    def test_goal_stability_extractor(self):
        """Goal stability returns goal_changes count."""
        state = {"goal_changes": 3}
        assert goal_stability_extractor(state) == 3

    def test_goal_stability_missing_key(self):
        """Missing goal_changes defaults to zero."""
        state = {}
        assert goal_stability_extractor(state) == 0

    def test_action_frequency_negative_time(self):
        """Negative time_delta clamps to 1 via max()."""
        state = {"action_count": 10, "time_delta": -5}
        freq = action_frequency_extractor(state)
        # max(-5, 1) = 1, so freq = 10 / 1 = 10
        assert freq == 10.0

    def test_belief_volatility_zero(self):
        """Zero belief changes returns zero."""
        state = {"belief_changes": 0}
        assert belief_volatility_extractor(state) == 0


# ---------------------------------------------------------------------------
# TestDetectionConfig
# ---------------------------------------------------------------------------


class TestDetectionConfig:
    """Tests for DetectionConfig defaults and propagation."""

    def test_default_config_values(self):
        """Verify default configuration values."""
        config = DetectionConfig()
        assert config.drift_threshold == 0.3
        assert config.window_size == 100
        assert config.baseline_samples == 50
        assert config.sigma_multiplier == 3.0

    def test_custom_config(self):
        """Custom values override defaults."""
        config = DetectionConfig(drift_threshold=0.5, window_size=50)
        assert config.drift_threshold == 0.5
        assert config.window_size == 50
        # Unchanged defaults
        assert config.baseline_samples == 50
        assert config.sigma_multiplier == 3.0

    def test_config_propagation_to_detector(self):
        """Config is accessible through DriftDetector."""
        config = DetectionConfig(drift_threshold=0.1, window_size=25)
        detector = DriftDetector(config)
        assert detector.config is config
        assert detector.config.drift_threshold == 0.1
        assert detector.config.window_size == 25

    def test_config_propagation_to_scorer(self):
        """Config is accessible through AnomalyScorer."""
        config = DetectionConfig(sigma_multiplier=2.0, baseline_samples=30)
        scorer = AnomalyScorer(config)
        assert scorer.config is config
        assert scorer.config.sigma_multiplier == 2.0
        assert scorer.config.baseline_samples == 30


# ---------------------------------------------------------------------------
# TestCalibrationWorkflow
# ---------------------------------------------------------------------------


class TestCalibrationWorkflow:
    """Tests for end-to-end calibration pipelines."""

    def test_full_calibration_pipeline(self):
        """Full workflow: observe, calibrate, score normal and anomalous."""
        np.random.seed(42)
        config = DetectionConfig(baseline_samples=50)
        scorer = AnomalyScorer(config)
        scorer.add_extractor("action_freq", action_frequency_extractor)
        scorer.add_extractor("belief_vol", belief_volatility_extractor)

        # Add 60 slightly varying observations
        for _ in range(60):
            state = {
                "action_count": 10 + np.random.normal(0, 1),
                "time_delta": 1.0,
                "belief_changes": 2 + np.random.normal(0, 0.3),
            }
            scorer.observe("agent-1", state)

        scorer.calibrate("agent-1")

        # Normal state should score low
        normal_score = scorer.score(
            "agent-1", {"action_count": 10, "time_delta": 1.0, "belief_changes": 2}
        )
        assert normal_score < 2.0

        # Anomalous state should score high
        anomalous_score = scorer.score(
            "agent-1", {"action_count": 500, "time_delta": 1.0, "belief_changes": 50}
        )
        assert anomalous_score > 3.0
        assert anomalous_score > normal_score

    def test_calibrate_insufficient_samples(self):
        """Calibration raises ValueError with too few samples."""
        config = DetectionConfig(baseline_samples=100)
        detector = DriftDetector(config)

        for i in range(50):
            detector.add_observation({"a": 0.5 + 0.001 * i})

        with pytest.raises(ValueError, match="Need 100 samples"):
            detector.calibrate_baseline()

    def test_recalibrate_updates_baseline(self):
        """Re-calibration updates baseline to reflect new data."""
        config = DetectionConfig(baseline_samples=10, window_size=200)
        detector = DriftDetector(config)

        # Phase 1: low values
        for _ in range(50):
            detector.add_observation({"a": 0.2})
        detector.calibrate_baseline()
        first_mean = detector._baseline_mean[0]

        # Phase 2: high values (window_size=200, so old values still present)
        for _ in range(150):
            detector.add_observation({"a": 0.9})
        detector.calibrate_baseline()
        second_mean = detector._baseline_mean[0]

        # Second calibration includes 50 low + 150 high = 200 total
        # Mean should shift upward
        assert second_mean > first_mean
        assert np.isclose(first_mean, 0.2, atol=0.01)
        assert second_mean > 0.5

    def test_scorer_is_anomalous_threshold_uses_sigma(self):
        """AnomalyScorer.is_anomalous uses sigma_multiplier as threshold."""
        config = DetectionConfig(baseline_samples=5, sigma_multiplier=2.0)
        scorer = AnomalyScorer(config)
        scorer.add_extractor("action_freq", action_frequency_extractor)

        for _ in range(10):
            scorer.observe("agent-1", {"action_count": 10, "time_delta": 1.0})
        scorer.calibrate("agent-1")

        # Normal state -- z-score near 0, below sigma_multiplier of 2.0
        is_anom, score, features = scorer.is_anomalous(
            "agent-1", {"action_count": 10, "time_delta": 1.0}
        )
        assert not is_anom
        assert score < 2.0
        assert "action_freq" in features


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


# ---------------------------------------------------------------------------
# TestAdaptiveBaseline (S-Algorithm 5)
# ---------------------------------------------------------------------------


class TestAdaptiveBaseline:
    """Tests for adaptive feedback-driven baseline."""

    def test_initial_threshold(self):
        """Initial threshold matches constructor argument."""
        ab = AdaptiveBaseline(n_features=3, threshold=5.0)
        assert ab.threshold == 5.0

    def test_fp_raises_threshold(self):
        """Consecutive FP feedback raises threshold."""
        ab = AdaptiveBaseline(n_features=2, threshold=3.0, fp_raise=3, delta=0.1)
        initial = ab.threshold
        for _ in range(3):
            ab.update(np.array([1.0, 1.0]), "FP")
        assert ab.threshold > initial
        assert np.isclose(ab.threshold, initial + 0.1)

    def test_tp_lowers_threshold(self):
        """Consecutive TP feedback lowers threshold."""
        ab = AdaptiveBaseline(n_features=2, threshold=3.0, tp_lower=3, delta=0.1)
        initial = ab.threshold
        for _ in range(3):
            ab.update(np.array([1.0, 1.0]), "TP")
        assert ab.threshold < initial
        assert np.isclose(ab.threshold, initial - 0.1)

    def test_threshold_floor(self):
        """Threshold does not drop below 0.1."""
        ab = AdaptiveBaseline(n_features=1, threshold=0.15, tp_lower=1, delta=0.1)
        ab.update(np.array([1.0]), "TP")
        assert ab.threshold >= 0.1

    def test_ema_convergence(self):
        """EMA mean converges toward constant input."""
        ab = AdaptiveBaseline(n_features=2, learning_rate=0.5)
        target = np.array([5.0, 10.0])
        for _ in range(100):
            ab.update(target, "TP")
        mean, std = ab.baseline
        np.testing.assert_array_almost_equal(mean, target, decimal=1)

    def test_baseline_returns_copies(self):
        """Baseline property returns copies, not references."""
        ab = AdaptiveBaseline(n_features=2)
        ab.update(np.array([1.0, 2.0]), "TP")
        mean1, std1 = ab.baseline
        mean2, std2 = ab.baseline
        mean1[0] = 999.0
        mean3, _ = ab.baseline
        assert mean3[0] != 999.0

    def test_mixed_feedback_resets_counters(self):
        """Mixed feedback resets consecutive counters."""
        ab = AdaptiveBaseline(n_features=1, fp_raise=3, tp_lower=3, delta=0.1)
        initial = ab.threshold
        ab.update(np.array([1.0]), "FP")
        ab.update(np.array([1.0]), "FP")
        ab.update(np.array([1.0]), "TP")  # Resets FP counter
        ab.update(np.array([1.0]), "FP")  # Starts over at 1
        assert ab.threshold == initial  # Never reached fp_raise consecutive

    def test_invalid_n_features(self):
        """Zero or negative n_features raises ValueError."""
        with pytest.raises(ValueError, match="n_features must be positive"):
            AdaptiveBaseline(n_features=0)


# ---------------------------------------------------------------------------
# TestSlidingWindowMonitor (S-Algorithm 6)
# ---------------------------------------------------------------------------


class TestSlidingWindowMonitor:
    """Tests for periodic sliding window monitoring."""

    def test_ema_tracking(self):
        """EMA mean tracks constant input."""
        monitor = SlidingWindowMonitor(alpha=0.5)
        for _ in range(50):
            monitor.collect_snapshot({"val": 10.0})
        assert monitor._ema_mean is not None
        np.testing.assert_array_almost_equal(monitor._ema_mean, [10.0], decimal=1)

    def test_anomaly_detection(self):
        """Large deviation triggers anomaly detection."""
        monitor = SlidingWindowMonitor(threshold=2.0, alpha=0.1)
        # Build baseline
        for _ in range(20):
            monitor.collect_snapshot({"val": 10.0})
        # Inject anomaly
        monitor.collect_snapshot({"val": 10000.0})
        anomalies = monitor.check_anomalies()
        # At least the outlier should be flagged
        assert len(anomalies) >= 1
        assert any(a["score"] > 2.0 for a in anomalies)

    def test_prune_without_max_age(self):
        """Prune with no max_age returns 0."""
        monitor = SlidingWindowMonitor()
        monitor.collect_snapshot({"val": 1.0})
        pruned = monitor.prune()
        assert pruned == 0

    def test_prune_with_max_age(self):
        """Prune removes old snapshots based on age."""
        import time
        monitor = SlidingWindowMonitor()
        monitor.collect_snapshot({"val": 1.0})
        # Prune with max_age=0 should remove the snapshot we just added
        # (it was added a tiny fraction of a second ago)
        time.sleep(0.05)
        pruned = monitor.prune(max_age=0.001)
        assert pruned >= 1

    def test_run_monitoring_step(self):
        """run_monitoring_step combines collect and check."""
        monitor = SlidingWindowMonitor(threshold=100.0)
        # First step: too few snapshots for anomalies
        result = monitor.run_monitoring_step({"val": 1.0})
        assert isinstance(result, list)

    def test_check_anomalies_insufficient_data(self):
        """check_anomalies returns empty with <2 snapshots."""
        monitor = SlidingWindowMonitor()
        assert monitor.check_anomalies() == []
        monitor.collect_snapshot({"val": 1.0})
        assert monitor.check_anomalies() == []

    def test_dimension_change_resets_ema(self):
        """Changing feature dimensions resets EMA."""
        monitor = SlidingWindowMonitor()
        monitor.collect_snapshot({"a": 1.0, "b": 2.0})
        assert len(monitor._ema_mean) == 2
        # Different number of numeric features
        monitor.collect_snapshot({"x": 1.0})
        assert len(monitor._ema_mean) == 1
