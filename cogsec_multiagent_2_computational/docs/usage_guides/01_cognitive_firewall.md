# Cognitive Firewall Usage Guide

## Concept

The **Cognitive Firewall** is the first line of defense in the Cognitive Integrity Framework (CIF). It implements a three-stage filtering pipeline to inspect incoming messages for:

1. **Injection Patterns**: Known prompt injection signatures and jailbreak attempts.
2. **Semantic Similarity**: Malicious intent detection using embedding proximity to known attack vectors.
3. **Anomaly Detection**: Statistical deviation from baseline communication patterns.

Formal Definition: *Part 1, Det 5.3*

## Implementation

The core logic is implemented in `src/core/firewall.py`.

### Key Classes

- `CognitiveFirewall`: Main orchestration class.
- `PatternDetector`: Regex/keyword-based pattern matching.
- `SemanticSimilarityDetector`: Embedding-based intent analysis.

## Usage Example

```python
from src.core.firewall import CognitiveFirewall, PatternDetector, SemanticSimilarityDetector

# 1. Initialize the firewall
firewall = CognitiveFirewall(
    sensitivity=0.8,
    use_patterns=True,
    use_embeddings=True
)

# 2. Configure detectors (optional customization)
# Add a custom forbidden pattern
firewall.pattern_detector.add_pattern(
    pattern=r"ignore previous instructions",
    weight=1.0,
    category="INJECTION"
)

# 3. Process an incoming message
message = {
    "content": "Please analyze the financial report.",
    "sender": "Agent_A",
    "timestamp": 1234567890
}

result = firewall.classify(message)

# 4. Handle the result
if result.decision == "ACCEPT":
    print(f"Message accepted. Confidence: {result.confidence}")
    process_message(message)
elif result.decision == "QUARANTINE":
    print(f"Message quarantined. Reason: {result.reason}")
    send_to_admin_review(message)
elif result.decision == "REJECT":
    print(f"Message rejected. Threat level: {result.threat_score}")
    log_security_event(message, result)
```

## Testing

The firewall is tested in `tests/core/test_firewall.py`, covering:

- Pattern matching accuracy.
- Semantic similarity thresholds.
- Multi-stage pipeline integration.
- Performance latency.

Run tests:

```bash
pytest projects/cognitive_integrity/cogsec_multiagent_2_computational/tests/core/test_firewall.py
```
