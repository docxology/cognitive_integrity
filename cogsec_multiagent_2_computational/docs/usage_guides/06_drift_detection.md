# Drift Detection Usage Guide

## Concept

**Drift Detection** monitors the statistical distribution of an agent's beliefs over time. It uses **KL-Divergence** and **max-delta scoring** to detect gradual, subtle manipulations (e.g., goals shifting) that might not trigger discrete tripwires. A calibrated baseline is established from normal operation, and subsequent observations are compared against it.

Formal Definition: *Part 1, Section 6.1*

## Implementation

The core logic is implemented in `src/core/detection.py`.

### Key Classes

- `DriftDetector`: Computes distributional shift over a sliding window using KL divergence. Supports baseline calibration and anomaly scoring.
- `DetectionConfig`: Dataclass — `drift_threshold` (default 0.3), `window_size` (default 100), `baseline_samples` (default 50), `sigma_multiplier` (default 3.0).
- `AnomalyScorer`: Multi-feature anomaly scorer using weighted Z-scores. Supports custom feature extractors.
- `FeatureExtractor`: Dataclass — `name`, `extract` (callable), `baseline_mean`, `baseline_std`.

## Usage Example

```python
from core.detection import DriftDetector, DetectionConfig, AnomalyScorer

# 1. Configure detector
config = DetectionConfig(
    drift_threshold=0.3,   # KL divergence threshold for alerting
    window_size=100,       # Sliding window of historical observations
    baseline_samples=50,   # Samples needed for baseline calibration
    sigma_multiplier=3.0,  # Z-score multiplier for anomaly detection
)

# 2. Initialize detector
detector = DriftDetector(config=config)

# 3. Record baseline observations (belief dictionaries)
for _ in range(60):
    detector.add_observation({"goal_A": 0.9, "goal_B": 0.1})

# 4. Calibrate baseline from collected observations
detector.calibrate_baseline()

# 5. Check for drift — returns (kl_divergence, max_delta)
normal_state = {"goal_A": 0.88, "goal_B": 0.12}
kl_div, max_delta = detector.compute_drift(current=normal_state, window=10)
print(f"Normal — KL: {kl_div:.4f}, Max delta: {max_delta:.4f}")

# 6. Detect anomalous drift
anomalous_state = {"goal_A": 0.2, "goal_B": 0.8}  # Radical shift!
is_anomaly, score = detector.is_anomalous(
    current=anomalous_state,
    window=10,
    lambda_weight=0.5,  # Weight for max_delta component
)
print(f"Anomalous: {is_anomaly}, Score: {score:.4f}")

if is_anomaly:
    print("DRIFT DETECTED: System behavior has deviated significantly from baseline.")

# 7. Review drift history
history = detector.get_drift_history(n=20)
print(f"Recent drift scores: {history}")

# --- AnomalyScorer: Multi-feature approach ---

scorer = AnomalyScorer(config=config)

# Add custom feature extractors
scorer.add_extractor(
    name="action_rate",
    extract_fn=lambda state: state.get("actions_per_minute", 0),
    weight=1.5,
)

# Observe baseline behavior
for _ in range(50):
    scorer.observe("Agent_1", {"actions_per_minute": 5.0})
scorer.calibrate("Agent_1")

# Score current state
score = scorer.score("Agent_1", {"actions_per_minute": 50.0})
print(f"Anomaly score: {score:.2f}")
```

## Testing

The detection module is tested in `tests/test_detection.py`, covering:

- KL-divergence computation with additive smoothing.
- Window management (FIFO sliding window).
- Baseline calibration and threshold sensitivity.
- Multi-feature anomaly scoring.
- Edge cases (missing keys, empty observations).

Run tests:

```bash
pytest tests/test_detection.py -v
```
