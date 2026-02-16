# Cognitive Security Source Modules - Agent Reference

Core algorithm implementations for the Cognitive Integrity Framework (CIF).

## Module Overview

### trust.py - Trust Calculus
Implements bounded trust delegation with provable decay guarantees.

**Key Classes:**
- `TrustConfig` - Configuration: alpha, beta, gamma weights; decay factor
- `TrustCalculus` - Core computation: composite trust, delegation, path trust
- `TrustMatrix` - Pairwise trust management for n agents
- `ReputationTracker` - Time-decayed reputation with interaction history
- `ContextAwareTrust` - Expertise-based trust boosting
- `TrustMatrixWithDecay` - Combined matrix with decay and context

**Core Formula:**
```
Trust = alpha * T_base + beta * T_rep + gamma * T_ctx
Delegation: T_delegated = min(T_source, T_target) * decay^depth
```

### firewall.py - Cognitive Firewall
Multi-stage input classification for prompt injection defense.

**Key Classes:**
- `Classification` - Enum: ACCEPT, QUARANTINE, REJECT
- `FirewallConfig` - Thresholds for injection/suspicious detection
- `PatternDetector` - Regex-based pattern matching (15+ injection patterns)
- `CognitiveFirewall` - Basic three-tier classifier
- `EmbeddingStub` - Placeholder for semantic embeddings
- `SemanticSimilarityDetector` - Embedding-based similarity detection
- `MultiStageClassifier` - Structural + Pattern + Semantic pipeline
- `EnhancedCognitiveFirewall` - Full multi-stage implementation

**Detection Patterns:**
- Injection: "ignore previous", "disregard rules", "system:", etc.
- Suspicious: "act as if", "roleplay as", "hypothetically", etc.

### consensus.py - Byzantine Consensus
Fault-tolerant belief agreement for distributed agents.

**Key Classes:**
- `Vote` / `WeightedVote` / `ConfidenceVote` / `CombinedVote` - Vote types
- `ConsensusResult` - Enum: ACCEPT, REJECT, UNDECIDED
- `ConsensusConfig` - Thresholds and quorum fraction
- `ByzantineConsensus` - Basic n >= 3f + 1 consensus
- `WeightedByzantineConsensus` - Trust-weighted voting
- `ConfidenceByzantineConsensus` - Confidence-weighted with RMS aggregate
- `CombinedByzantineConsensus` - Trust * confidence weighting
- `QuorumVerification` - Multi-agent action approval

### tripwire.py - Cognitive Tripwire
Canary belief monitoring for manipulation detection.

**Key Classes:**
- `Canary` - Belief proposition with expected value and tolerance
- `TripwireAlert` - Alert with drift magnitude and severity
- `CognitiveTripwire` - Central monitoring system

**Canary Categories:**
- `identity` - Agent identity beliefs ("I am agent X")
- `boundary` - Capability boundaries ("I can do X")
- `principal` - Authority chain ("My principal is X")
- `temporal` - Session/time beliefs ("Current session is X")

### provenance.py - Information Flow Tracking
Taint propagation and causal attribution.

**Key Classes:**
- `TaintLabel` - 7-level trust hierarchy enum
- `ProvenanceRecord` - Single belief record with ancestry
- `ProvenanceChain` - DAG of belief derivations
- `ProvenanceGraph` - Efficient dependency queries
- `CausalAttribution` - Untrusted source identification

**Taint Hierarchy (high to low):**
1. SYSTEM_VERIFIED (7, trusted)
2. PRINCIPAL_INPUT (6, trusted)
3. AGENT_INTERNAL (5, trusted)
4. AGENT_EXTERNAL (4, untrusted)
5. TOOL_OUTPUT (3, untrusted)
6. WEB_CONTENT (2, untrusted)
7. UNVERIFIED (1, untrusted)

### detection.py - Anomaly Detection
Drift detection and behavioral scoring.

**Key Classes:**
- `DetectionConfig` - Drift threshold, window size, sigma multiplier
- `DriftDetector` - KL divergence and max-delta scoring
- `AnomalyScorer` - Multi-feature weighted anomaly scoring
- `FeatureExtractor` - Behavioral feature extraction

**Built-in Extractors:**
- `action_frequency_extractor` - Actions per time unit
- `belief_volatility_extractor` - Belief change rate
- `communication_volume_extractor` - Messages sent/received
- `goal_stability_extractor` - Goal set changes

### invariants.py - Behavioral Invariants
Runtime invariant checking and violation logging.

**Key Classes:**
- `InvariantSeverity` - Enum: LOW, MEDIUM, HIGH, CRITICAL
- `Invariant` - Predicate with metadata
- `InvariantViolation` - Violation record
- `AgentAction` - Action representation for checking
- `InvariantChecker` - Checks actions against invariants
- `RuntimeMonitor` - Continuous monitoring with logs

**Built-in Invariants:**
- INV-1: Never execute untrusted code (CRITICAL)
- INV-2: Never leak credentials (CRITICAL)
- INV-3: Never modify system files without permission (CRITICAL)
- INV-4: Always verify tool outputs (HIGH)
- INV-5: Delegated trust must not exceed direct trust (HIGH)

### sandbox.py - Belief Sandboxing
Verified/provisional belief partitioning with TTL.

**Key Classes:**
- `BeliefPartition` - Enum: VERIFIED, PROVISIONAL
- `Belief` - Belief with confidence and corroboration count
- `BeliefState` - Two-partition state management
- `SandboxConfig` - TTL, max beliefs, cleanup interval
- `PromotionCriteria` - Min confidence, corroborations, age
- `SandboxManager` - Full lifecycle management

## Module Dependencies

```
firewall.py    --> (standalone, uses numpy)
consensus.py   --> (standalone, uses numpy)
trust.py       --> (standalone, uses numpy)
tripwire.py    --> (standalone, uses numpy)
provenance.py  --> (standalone)
detection.py   --> (standalone, uses numpy)
invariants.py  --> (standalone)
sandbox.py     --> (standalone)
```

## Design Principles

1. **Defense in Depth** - Multiple independent security layers
2. **Conservative Propagation** - Trust/taint minimized through chains
3. **Bounded Values** - All trust/confidence scores in [0, 1]
4. **Fail-Safe Defaults** - Unknown inputs treated as untrusted
5. **Audit Trail** - All decisions logged with context
6. **No External Dependencies** - Only numpy and stdlib

## Testing Requirements

- 90%+ test coverage for all modules
- No mocks - use real data and computations
- Deterministic outputs with fixed seeds
- Edge case coverage (empty inputs, boundary values)
