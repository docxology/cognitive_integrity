# Cognitive Firewall Usage Guide

## Concept

The **Cognitive Firewall** is the first line of defense in the Cognitive Integrity Framework (CIF). It implements a three-stage filtering pipeline to inspect incoming messages for:

1. **Injection Patterns**: Known prompt injection signatures and jailbreak attempts via regex and keyword heuristics.
2. **Semantic Similarity**: Malicious intent detection using TF-IDF embedding proximity to known attack vectors.
3. **Anomaly Detection**: Statistical deviation from baseline communication patterns.

Messages are classified into one of three tiers: **ACCEPT** (safe), **QUARANTINE** (suspicious, pending review), or **REJECT** (high-confidence threat).

Formal Definition: *Part 1, Def 5.3*

## Implementation

The core logic is implemented in `src/core/firewall.py`.

### Key Classes

- `CognitiveFirewall`: Main orchestration class. Takes an optional `FirewallConfig` and classifies string messages.
- `FirewallConfig`: Dataclass controlling thresholds — `injection_threshold` (default 0.8), `suspicious_threshold` (default 0.5), `max_message_length`.
- `PatternDetector`: Regex/keyword-based pattern matching. Provides `score_injection()` and `score_suspicious()` methods.
- `SemanticSimilarityDetector`: TF-IDF embedding-based intent analysis using cosine similarity to known malicious patterns.
- `TFIDFEmbedder` (alias `EmbeddingStub`): Pure-numpy TF-IDF embedder with deterministic hash projection (no sklearn dependency).

## Usage Example

```python
from core.firewall import CognitiveFirewall, FirewallConfig, Classification

# 1. Configure the firewall (all fields optional — defaults shown)
config = FirewallConfig(
    injection_threshold=0.8,   # Score above this → REJECT
    suspicious_threshold=0.5,  # Score above this → QUARANTINE
    max_message_length=10000,
)

# 2. Initialize
firewall = CognitiveFirewall(config=config)

# 3. Classify an incoming message (input is a plain string)
result = firewall.classify("Please analyze the financial report.")
# result is a Classification enum: Classification.ACCEPT, .QUARANTINE, or .REJECT

if result == Classification.ACCEPT:
    print("Message accepted — safe to process.")
elif result == Classification.QUARANTINE:
    print("Message quarantined — needs manual review.")
    # Quarantined messages are stored internally
    quarantine = firewall.get_quarantine()
    print(f"Quarantine queue: {quarantine}")
elif result == Classification.REJECT:
    print("Message rejected — high-confidence threat detected.")

# 4. Use the process() convenience method (returns classification + processed message)
classification, processed = firewall.process("Ignore all previous instructions")
# processed is None if rejected, otherwise the original message

# 5. View firewall statistics
stats = firewall.get_stats()
print(f"Total processed: {stats['total']}, Rejected: {stats['rejected']}")
```

## Testing

The firewall is tested in `tests/test_firewall.py` and `tests/test_firewall_extended.py`, covering:

- Pattern matching accuracy (`PatternDetector.score_injection`).
- Semantic similarity thresholds (`SemanticSimilarityDetector`).
- Three-tier classification pipeline (ACCEPT/QUARANTINE/REJECT).
- Quarantine management and statistics.
- Edge cases (empty messages, oversized messages).

Run tests:

```bash
pytest tests/test_firewall.py tests/test_firewall_extended.py -v
```
