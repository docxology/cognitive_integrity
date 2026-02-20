# Cognitive Security Tests - Agent Reference

Test suite for the Cognitive Integrity Framework modules.

## Test Organization

### test_trust.py

Tests for trust calculus implementation.

**TestTrustConfig:**

- `test_valid_config` - Weights summing to 1.0 accepted
- `test_invalid_weights_raises` - Non-unity weights rejected
- `test_invalid_decay_raises` - Decay outside (0,1) rejected

**TestTrustCalculus:**

- `test_compute_trust_weighted` - Weighted sum computation
- `test_delegate_trust_bounded` - Trust cannot exceed min(src, tgt)
- `test_delegate_trust_decays_with_depth` - Exponential decay verification
- `test_path_trust_composition` - Multi-hop trust bounded
- `test_empty_path_returns_zero` - Edge case handling

**TestTrustMatrix:**

- `test_self_trust_maximal` - Self-trust always 1.0
- `test_initial_trust_neutral` - Default trust ~0.5
- `test_reputation_update` - Learning rate behavior
- `test_delegation_path` - Path trust computation

**TestReputationTracker:**

- `test_time_decay` - Recent interactions weighted more
- `test_default_reputation` - Unknown pairs return default

**TestContextAwareTrust:**

- `test_expertise_boost` - Context-based trust increase
- `test_similarity_fallback` - Similar context matching

### test_firewall.py

Tests for cognitive firewall classification.

**TestPatternDetector:**

- `test_injection_patterns` - Known injection patterns detected
- `test_suspicious_patterns` - Suspicious content flagged
- `test_clean_message` - Normal messages pass
- `test_structural_heuristics` - Length, caps, newlines

**TestCognitiveFirewall:**

- `test_accept_normal` - Clean messages accepted
- `test_reject_injection` - Injection attempts rejected
- `test_quarantine_suspicious` - Suspicious quarantined
- `test_quarantine_queue` - Quarantine storage

**TestMultiStageClassifier:**

- `test_structural_stage` - Length/format checks
- `test_pattern_stage` - Regex detection
- `test_semantic_stage` - Embedding similarity
- `test_early_rejection` - High-score early exit

**TestSemanticSimilarityDetector:**

- `test_register_pattern` - Malicious pattern registration
- `test_similarity_scoring` - Cosine similarity computation

### test_consensus.py

Tests for Byzantine-tolerant consensus.

**TestByzantineConsensus:**

- `test_byzantine_tolerance` - n >= 3f + 1 enforced
- `test_quorum_required` - Insufficient votes undecided
- `test_accept_consensus` - High-belief agreement
- `test_reject_consensus` - Low-belief agreement
- `test_vote_update` - Latest vote replaces previous

**TestQuorumVerification:**

- `test_quorum_calculation` - ceil((n+f+1)/2)
- `test_approve_reaches_quorum` - Approval counting
- `test_cancel_pending` - Request cancellation

**TestWeightedConsensus:**

- `test_trust_weighted_average` - Weight-aware aggregation

**TestConfidenceConsensus:**

- `test_confidence_weighted` - Confidence weighting
- `test_aggregate_confidence` - RMS confidence
- `test_low_confidence_undecided` - Uncertain rejection

### test_tripwire.py

Tests for canary belief monitoring.

**TestCanary:**

- `test_check_within_tolerance` - Belief in range
- `test_check_outside_tolerance` - Drift detected

**TestTripwireAlert:**

- `test_severity_critical` - drift > 0.5
- `test_severity_high` - drift > 0.3
- `test_severity_medium` - drift > 0.2
- `test_severity_low` - drift <= 0.2

**TestCognitiveTripwire:**

- `test_add_identity_canary` - Identity belief monitoring
- `test_add_boundary_canary` - Capability boundaries
- `test_add_principal_canary` - Authority chain
- `test_check_triggers_alert` - Alert generation
- `test_handler_callback` - Handler invocation
- `test_rotate_canaries` - Category rotation

### test_provenance.py

Tests for information flow tracking.

**TestTaintLabel:**

- `test_trust_levels` - Level ordering
- `test_is_trusted` - Trust classification

**TestProvenanceChain:**

- `test_add_belief` - Record creation
- `test_ancestry` - Transitive parents
- `test_effective_taint` - Conservative propagation

**TestProvenanceGraph:**

- `test_depends_on` - Direct dependency
- `test_transitive_depends` - Indirect dependency
- `test_get_dependents` - Forward propagation

**TestCausalAttribution:**

- `test_identify_untrusted` - Source identification
- `test_trace_paths` - Path finding
- `test_generate_report` - Full report

### test_detection.py

Tests for anomaly detection.

**TestDriftDetector:**

- `test_kl_divergence` - Divergence calculation
- `test_compute_drift` - Drift metrics
- `test_is_anomalous` - Threshold comparison
- `test_calibration` - Baseline establishment

**TestAnomalyScorer:**

- `test_add_extractor` - Feature registration
- `test_observe` - History recording
- `test_calibrate` - Baseline computation
- `test_score` - Z-score calculation
- `test_is_anomalous` - Threshold detection

### test_invariants.py

Tests for behavioral invariant checking.

**TestInvariantChecker:**

- `test_builtin_invariants` - 5 invariants loaded
- `test_inv1_untrusted_code` - Code execution check
- `test_inv2_credential_leak` - Secret output check
- `test_inv3_system_write` - File permission check
- `test_inv4_tool_output` - Tool verification check
- `test_inv5_trust_ordering` - Delegation bound check

**TestRuntimeMonitor:**

- `test_check_action` - Action validation
- `test_violation_log` - Log accumulation
- `test_filter_by_agent` - Agent-specific queries
- `test_filter_by_severity` - Severity filtering
- `test_stats` - Monitoring statistics

### test_sandbox.py

Tests for belief sandboxing.

**TestBeliefState:**

- `test_add_verified` - Verified partition
- `test_add_provisional` - Provisional partition
- `test_promote` - Partition transfer
- `test_demote` - Reverse transfer

**TestPromotionCriteria:**

- `test_min_confidence` - Confidence threshold
- `test_min_corroborations` - Corroboration count
- `test_min_age` - Age requirement
- `test_custom_predicate` - Custom rules

**TestSandboxManager:**

- `test_add_provisional_with_ttl` - TTL assignment
- `test_cleanup_expired` - Expiration removal
- `test_promote_removes_ttl` - TTL cleared on verify
- `test_check_promotions` - Auto-promotion
- `test_add_corroboration` - Corroboration tracking
- `test_extend_ttl` - TTL extension

## Test Requirements

### No Mocks Policy

All tests use real objects and computations:

```python
# GOOD
calc = TrustCalculus()
result = calc.compute_trust(0.8, 0.9, 0.7)
assert np.isclose(result, 0.81)

# BAD (forbidden)
mock_calc = MagicMock()
mock_calc.compute_trust.return_value = 0.81
```

### Coverage Requirements

- 90%+ coverage for all src modules
- All public methods tested
- Edge cases included (empty inputs, boundary values)
- Error conditions verified

### Determinism

- Fixed seeds where randomness used
- Predictable test outputs
- Reproducible across runs

## Test Execution

```bash
# All tests with verbose output
pytest tests/ -v

# Single file
pytest tests/test_trust.py -v

# Single test class
pytest tests/test_trust.py::TestTrustCalculus -v

# Single test method
pytest tests/test_trust.py::TestTrustCalculus::test_delegate_trust_bounded -v

# With coverage report
pytest tests/ --cov=src --cov-report=html --cov-fail-under=90

# Show print output
pytest tests/ -v -s
```

## Fixtures (conftest.py)

Common fixtures available:

- `tmp_path` - Temporary directory (pytest built-in)
- Project-specific fixtures as needed

## Test Output

Test results are reported to:

- Console output (stdout/stderr via pytest)
- Coverage reports in `htmlcov/` (when `--cov-report=html` is used)
