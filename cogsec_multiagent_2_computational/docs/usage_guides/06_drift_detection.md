# Drift Detection Usage Guide

## Concept

**Drift Detection** monitors the statistical distribution of an agent's beliefs over time. It uses metrics like KL-Divergence to detect gradual, subtle manipulations (like "goals shifting") that might not trigger discrete tripwires.

Formal Definition: *Part 1, Section 6.1*

## Implementation

The core logic is implemented in `src/core/detection.py`.

### Key Classes

- `DriftDetector`: Computes distributional shift over sliding windows.
- `AnomalyScorer`: Scores individual belief states for likelihood under the baseline model.

## Usage Example

```python
from src.core.detection import DriftDetector

# 1. Initialize Detector
# - window_size: How many historical samples to keep
# - threshold: KL divergence threshold for alerting
detector = DriftDetector(window_size=100, threshold=0.5)

# 2. Record Baseline Observations (Training Phase)
# Assuming belief_vector is a numerical representation of system state
baseline_states = [[0.1, 0.9], [0.12, 0.88], [0.11, 0.89]] 
for state in baseline_states:
    detector.update(state)

# 3. Monitor for Drift (Runtime)
# Normal state
normal_state = [0.13, 0.87]
score = detector.score(normal_state)
print(f"Normal Drift Score: {score:.4f}") # Low score

# Anomalous state (radical shift)
anomalous_state = [0.9, 0.1] 
score = detector.score(anomalous_state)
print(f"Anomalous Drift Score: {score:.4f}") # High score

if score > detector.threshold:
    print("DRIFT DETECTED: System behavior has deviated significantly from baseline.")
```

## Testing

The detection module is tested in `tests/core/test_detection.py`, covering:

- Statistical calculations (KL-div).
- Window management (FIFO behavior).
- Threshold sensitivity.

Run tests:

```bash
pytest projects/cognitive_integrity/cogsec_multiagent_2_computational/tests/core/test_detection.py
```
