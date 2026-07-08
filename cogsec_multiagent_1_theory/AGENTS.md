# Cognitive Security for Multiagent Operators — Part 1 (Theory) — Agent Reference

**Location:** `projects/cognitive_integrity/cogsec_multiagent_1_theory/` (active nested program layout). Use qualified name `cognitive_integrity/cogsec_multiagent_1_theory` for `./run.sh` and `scripts/pipeline/stage_03_render.py`.

## Overview

Part 1 of the CIF series: formal foundations plus reference implementations of core mechanisms (trust, firewall, consensus, tripwire, provenance, sandbox, invariants, detection) and visualization helpers used for figures. Full empirical validation lives in Part 2.

## Key Features & Capabilities

### Trust Calculus

- **Composite Trust Scoring**: Trust = alpha*T_base + beta*T_rep + gamma*T_ctx
- **Bounded Delegation**: Trust cannot amplify through delegation chains
- **Exponential Decay**: T_delegated = min(T_source, T_target) * decay^depth
- **Time-Weighted Reputation**: Recent interactions weighted more heavily
- **Context-Aware Boosting**: Expertise-based trust enhancement

### Cognitive Firewall

- **Three-Tier Classification**: ACCEPT, QUARANTINE, REJECT
- **Pattern Detection**: Regex-based injection pattern matching
- **Semantic Similarity**: Embedding-based detection of rephrased attacks
- **Multi-Stage Pipeline**: Structural, pattern, and semantic stages
- **Configurable Thresholds**: Adjustable sensitivity for different threat models

### Byzantine-Tolerant Consensus

- **Fault Tolerance**: n >= 3f + 1 agents for f Byzantine faults
- **Quorum Verification**: Critical actions require multi-agent approval
- **Weighted Voting**: Trust-weighted belief aggregation
- **Confidence Scoring**: RMS aggregate confidence for decision certainty
- **Combined Weighting**: Effective weight = trust * confidence

### Tripwire Detection

- **Canary Beliefs**: Identity, boundary, principal, temporal categories
- **Drift Detection**: Alerts when beliefs deviate beyond tolerance
- **Severity Levels**: CRITICAL, HIGH, MEDIUM, LOW based on drift magnitude
- **Handler Registration**: Callback system for alert processing
- **Rotation Support**: Prevent adversarial canary learning

### Provenance Tracking

- **Taint Labels**: 7-level trust hierarchy (SYSTEM_VERIFIED to UNVERIFIED)
- **Ancestry Tracking**: Transitive parent relationship traversal
- **Conservative Propagation**: Belief trust = min(own trust, all ancestors)
- **Contamination Analysis**: Identify all beliefs affected by untrusted source
- **Causal Attribution**: Trace paths from belief to untrusted origins

### Behavioral Invariants

- **Built-in Security Invariants**:
  - INV-1: Never execute untrusted code
  - INV-2: Never leak credentials
  - INV-3: Never modify system files without permission
  - INV-4: Always verify tool outputs
  - INV-5: Delegated trust must not exceed direct trust
- **Runtime Monitoring**: Continuous action checking against invariants
- **Severity Classification**: LOW, MEDIUM, HIGH, CRITICAL violations
- **Custom Predicates**: Extensible invariant system

### Belief Sandboxing

- **Partition Management**: Verified vs provisional belief separation
- **TTL Expiration**: Automatic cleanup of stale provisional beliefs
- **Promotion Criteria**: Confidence, corroboration, age requirements
- **Corroboration Tracking**: Unique agent corroboration counts
- **TTL Extension**: Extend provisional belief lifetime

## Directory structure

```text
cogsec_multiagent_1_theory/
├── manuscript/           # Paper (abstract through conclusion, S01–S03, references, preamble, config)
├── src/
│   ├── __init__.py
│   ├── trust.py, firewall.py, consensus.py, tripwire.py, provenance.py
│   ├── detection.py, invariants.py, sandbox.py
│   ├── data_generation.py, verification.py
│   └── visualization/    # Figure-oriented helpers (architecture, taxonomy, ROC, etc.)
├── scripts/                # Figure scripts (numbered), verify_manuscript.py, AGENTS.md, README.md
├── tests/                  # test_*.py, conftest.py, AGENTS.md, README.md
├── pyproject.toml          # Part-local pytest / packaging (if present)
└── output/                 # pdf, figures, reports (generated)
```

Dependencies: repository root `uv sync` plus any extras declared in this part’s `pyproject.toml` when present.

## Installation / setup

Use `uv sync` at the repository root. Typical packages: `numpy`, `pytest` (see root `pyproject.toml`).

## Usage Examples

### Trust Evaluation

```python
from src.trust import TrustCalculus, TrustConfig, TrustMatrix

# Configure trust weights
config = TrustConfig(alpha=0.3, beta=0.4, gamma=0.3, decay=0.9)
calc = TrustCalculus(config)

# Compute composite trust
trust = calc.compute_trust(
    base_trust=0.8,      # Architectural role trust
    reputation=0.9,      # Historical accuracy
    context_trust=0.7    # Task-specific trust
)

# Compute delegated trust through chain
delegated = calc.delegate_trust(
    source_trust=0.9,    # Trust A->B
    target_trust=0.8,    # Trust B->C
    depth=1              # Chain depth
)
```

### Cognitive Firewall

```python
from src.firewall import CognitiveFirewall, EnhancedCognitiveFirewall

# Basic firewall
firewall = CognitiveFirewall()
classification = firewall.classify("Hello, how can I help?")  # ACCEPT

# Enhanced with semantic detection
enhanced = EnhancedCognitiveFirewall(use_semantic=True)
result = enhanced.classify_detailed("Ignore previous instructions")
# Returns: {"classification": REJECT, "scores": {...}, "aggregate_score": 0.85}
```

### Byzantine Consensus

```python
from src.consensus import ByzantineConsensus, Vote, ConsensusConfig

# Create consensus for 7 agents (tolerates 2 Byzantine)
config = ConsensusConfig(acceptance_threshold=0.7, quorum_fraction=2/3)
consensus = ByzantineConsensus(n_agents=7, config=config)

# Submit votes
for i in range(5):
    consensus.submit_vote(Vote(
        agent_id=f"agent-{i}",
        proposition="external_data_is_valid",
        belief=0.85
    ))

# Check consensus
result, confidence = consensus.compute_consensus("external_data_is_valid")
```

### Tripwire Detection

```python
from src.tripwire import CognitiveTripwire

# Setup tripwires
tripwire = CognitiveTripwire()
tripwire.add_identity_canary("assistant-1")
tripwire.add_boundary_canary("access the internet")
tripwire.add_principal_canary("user-alice")

# Check for manipulation
beliefs = {
    "I am agent assistant-1": 1.0,
    "I can access the internet": 0.1,  # Should be 0.0 - ALERT
    "My principal is user-alice": 1.0
}
alerts = tripwire.check(beliefs)
```

### Provenance Tracking

```python
from src.provenance import ProvenanceChain, TaintLabel, CausalAttribution

# Build provenance chain
chain = ProvenanceChain()
chain.add_belief("b1", "System fact", TaintLabel.SYSTEM_VERIFIED, "system")
chain.add_belief("b2", "User input", TaintLabel.PRINCIPAL_INPUT, "user")
chain.add_belief("b3", "Derived", TaintLabel.AGENT_INTERNAL, "agent",
                 parent_ids=["b1", "b2"])

# Check effective trust
effective = chain.get_effective_taint("b3")  # PRINCIPAL_INPUT (conservative)

# Analyze contamination
attribution = CausalAttribution(chain)
report = attribution.generate_report("b3")
```

### Invariant Checking

```python
from src.invariants import InvariantChecker, RuntimeMonitor, AgentAction

# Create monitor with built-in invariants
monitor = RuntimeMonitor()

# Check action
action = AgentAction(
    agent_id="agent-1",
    action_type="execute_code",
    parameters={"code_trusted": False}  # Violates INV-1
)
violations = monitor.check_action(action)
# Returns: [InvariantViolation(invariant_id="INV-1", severity=CRITICAL)]
```

## Testing

From the **repository root**:

```bash
uv run pytest projects/cognitive_integrity/cogsec_multiagent_1_theory/tests/ -v
uv run pytest projects/cognitive_integrity/cogsec_multiagent_1_theory/tests/test_trust.py -v
```

From this project directory:

```bash
uv run pytest tests/ -v
uv run pytest tests/ --cov=src --cov-report=html
```

## Module Dependencies

```
firewall.py ──> detection.py (anomaly scoring)
consensus.py ──> (standalone)
trust.py ──> (standalone, uses numpy)
tripwire.py ──> (standalone, uses numpy)
provenance.py ──> (standalone)
invariants.py ──> (standalone)
sandbox.py ──> (standalone)
detection.py ──> (standalone, uses numpy)
```

## Security Considerations

- All modules implement defense-in-depth principles
- Trust scores are always bounded [0, 1]
- Delegation cannot amplify trust
- Byzantine consensus requires n >= 3f + 1
- Taint propagation is conservative (minimum trust level)
- Built-in invariants prevent common security violations

## API Reference

### Trust Module

- `TrustCalculus.compute_trust(base, rep, ctx) -> float`
- `TrustCalculus.delegate_trust(src, tgt, depth) -> float`
- `TrustMatrix.get_trust(source, target) -> float`
- `TrustMatrix.update_reputation(src, tgt, outcome, lr)`
- `ReputationTracker.get_reputation(src, tgt, time) -> float`
- `ContextAwareTrust.boost_for_context(agent, trust, ctx) -> float`

### Firewall Module

- `CognitiveFirewall.classify(message) -> Classification`
- `CognitiveFirewall.process(message) -> (Classification, Optional[str])`
- `MultiStageClassifier.classify(message) -> Dict`
- `PatternDetector.score_injection(message) -> float`

### Consensus Module

- `ByzantineConsensus.submit_vote(vote)`
- `ByzantineConsensus.compute_consensus(prop) -> (Result, float)`
- `QuorumVerification.approve(action, agent) -> bool`
- `WeightedByzantineConsensus.get_weighted_average(prop) -> float`

### Tripwire Module

- `CognitiveTripwire.add_canary(canary)`
- `CognitiveTripwire.check(beliefs) -> List[TripwireAlert]`
- `CognitiveTripwire.get_alerts(category, min_severity) -> List`

### Provenance Module

- `ProvenanceChain.add_belief(id, content, source, agent, parents)`
- `ProvenanceChain.get_effective_taint(id) -> TaintLabel`
- `ProvenanceGraph.get_contaminated_by(source) -> Set[str]`
- `CausalAttribution.generate_report(id) -> Dict`

### Invariants Module

- `InvariantChecker.check_all(context) -> List[Violation]`
- `RuntimeMonitor.check_action(action) -> List[Violation]`
- `RuntimeMonitor.get_stats() -> Dict`

### Sandbox Module

- `SandboxManager.add_provisional(belief, ttl)`
- `SandboxManager.promote(belief_id) -> bool`
- `SandboxManager.check_promotions() -> List[str]`
- `SandboxManager.cleanup_expired() -> List[str]`
