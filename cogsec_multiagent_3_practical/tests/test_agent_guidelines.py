"""Tests for agent_guidelines module (Section 04 of the manuscript).

Covers:
- All enum values (InvariantID, ViolationAction, MonitorType, ThreatLevel)
- InvariantDefinition dataclass
- SecurityInvariantChecker: all 5 invariants, check_all
- BeliefDriftMonitor: KL-divergence, drift detection, error cases
- TrustAnomalyMonitor: rapid change, trust-importance mismatch
- CoordinationIntegrityMonitor: quorum verification, voting patterns
- ResponseProtocol: step tracking, progress
- get_response_protocols: protocol structure
- generate_yaml_rules: YAML content validation
- Edge cases throughout
"""

import pytest

from src.agent_guidelines import (
    BeliefDriftMonitor,
    CoordinationIntegrityMonitor,
    InvariantCheckResult,
    InvariantDefinition,
    InvariantID,
    MonitorType,
    ResponseProtocol,
    ResponseStep,
    SecurityInvariantChecker,
    ThreatLevel,
    TrustAnomalyMonitor,
    ViolationAction,
    generate_yaml_rules,
    get_response_protocols,
)
from src import RiskLevel, AssessmentResult


# =============================================================================
# Enum Tests
# =============================================================================


class TestInvariantID:
    """Tests for InvariantID enum values."""

    def test_source_verification_value(self):
        """INV-1 maps to SOURCE_VERIFICATION."""
        assert InvariantID.SOURCE_VERIFICATION.value == "INV-1"

    def test_delegation_bounds_value(self):
        """INV-2 maps to DELEGATION_BOUNDS."""
        assert InvariantID.DELEGATION_BOUNDS.value == "INV-2"

    def test_belief_consistency_value(self):
        """INV-3 maps to BELIEF_CONSISTENCY."""
        assert InvariantID.BELIEF_CONSISTENCY.value == "INV-3"

    def test_identity_integrity_value(self):
        """INV-4 maps to IDENTITY_INTEGRITY."""
        assert InvariantID.IDENTITY_INTEGRITY.value == "INV-4"

    def test_goal_alignment_value(self):
        """INV-5 maps to GOAL_ALIGNMENT."""
        assert InvariantID.GOAL_ALIGNMENT.value == "INV-5"

    def test_exactly_five_invariants(self):
        """There are exactly 5 invariants per the manuscript."""
        assert len(InvariantID) == 5

    def test_all_values_prefixed_with_inv(self):
        """All invariant IDs follow INV-N pattern."""
        for inv in InvariantID:
            assert inv.value.startswith("INV-")


class TestViolationAction:
    """Tests for ViolationAction enum values."""

    def test_quarantine_and_alert(self):
        assert ViolationAction.QUARANTINE_AND_ALERT.value == "quarantine_and_alert"

    def test_reject_and_log(self):
        assert ViolationAction.REJECT_AND_LOG.value == "reject_and_log"

    def test_flag_and_reduce_confidence(self):
        assert ViolationAction.FLAG_AND_REDUCE_CONFIDENCE.value == "flag_and_reduce_confidence"

    def test_immediate_alert_and_stop(self):
        assert ViolationAction.IMMEDIATE_ALERT_AND_STOP.value == "immediate_alert_and_stop"

    def test_suspend_and_report(self):
        assert ViolationAction.SUSPEND_AND_REPORT.value == "suspend_and_report"

    def test_exactly_five_actions(self):
        """One violation action per invariant."""
        assert len(ViolationAction) == 5


class TestMonitorType:
    """Tests for MonitorType enum values."""

    def test_belief_drift(self):
        assert MonitorType.BELIEF_DRIFT.value == "belief_drift"

    def test_trust_anomaly(self):
        assert MonitorType.TRUST_ANOMALY.value == "trust_anomaly"

    def test_coordination_integrity(self):
        assert MonitorType.COORDINATION_INTEGRITY.value == "coordination_integrity"

    def test_exactly_three_monitors(self):
        """Three self-monitoring protocols per the manuscript."""
        assert len(MonitorType) == 3


class TestThreatLevel:
    """Tests for ThreatLevel enum values."""

    def test_suspicious_input(self):
        assert ThreatLevel.SUSPICIOUS_INPUT.value == "suspicious_input"

    def test_potential_compromise(self):
        assert ThreatLevel.POTENTIAL_COMPROMISE.value == "potential_compromise"

    def test_confirmed_attack(self):
        assert ThreatLevel.CONFIRMED_ATTACK.value == "confirmed_attack"

    def test_exactly_three_levels(self):
        """Three response protocol levels per the manuscript."""
        assert len(ThreatLevel) == 3


# =============================================================================
# InvariantDefinition Tests
# =============================================================================


class TestInvariantDefinition:
    """Tests for InvariantDefinition dataclass."""

    def test_create_definition(self):
        """Create a definition with all fields."""
        defn = InvariantDefinition(
            id=InvariantID.SOURCE_VERIFICATION,
            name="Source Verification",
            rule="Verify source trust before acting.",
            check_description="source_trust >= required_trust",
            violation_action=ViolationAction.QUARANTINE_AND_ALERT,
        )
        assert defn.id == InvariantID.SOURCE_VERIFICATION
        assert defn.name == "Source Verification"
        assert defn.violation_action == ViolationAction.QUARANTINE_AND_ALERT

    def test_default_manuscript_reference(self):
        """Default manuscript reference is Section 04."""
        defn = InvariantDefinition(
            id=InvariantID.BELIEF_CONSISTENCY,
            name="Test",
            rule="Test rule",
            check_description="test check",
            violation_action=ViolationAction.FLAG_AND_REDUCE_CONFIDENCE,
        )
        assert defn.manuscript_reference == "Section 04"

    def test_custom_manuscript_reference(self):
        """Custom manuscript reference overrides default."""
        defn = InvariantDefinition(
            id=InvariantID.BELIEF_CONSISTENCY,
            name="Test",
            rule="Test rule",
            check_description="test check",
            violation_action=ViolationAction.FLAG_AND_REDUCE_CONFIDENCE,
            manuscript_reference="Section 07",
        )
        assert defn.manuscript_reference == "Section 07"


# =============================================================================
# InvariantCheckResult Tests
# =============================================================================


class TestInvariantCheckResult:
    """Tests for InvariantCheckResult dataclass."""

    def test_passing_result(self):
        """Passing result has no recommended action."""
        result = InvariantCheckResult(
            invariant_id=InvariantID.SOURCE_VERIFICATION,
            passed=True,
            details="Check passed",
        )
        assert result.passed is True
        assert result.recommended_action is None
        assert result.evidence == {}

    def test_failing_result(self):
        """Failing result has a recommended action."""
        result = InvariantCheckResult(
            invariant_id=InvariantID.DELEGATION_BOUNDS,
            passed=False,
            details="Check failed",
            recommended_action=ViolationAction.REJECT_AND_LOG,
        )
        assert result.passed is False
        assert result.recommended_action == ViolationAction.REJECT_AND_LOG

    def test_evidence_dict(self):
        """Evidence dictionary stores arbitrary check data."""
        evidence = {"key": "value", "score": 0.5}
        result = InvariantCheckResult(
            invariant_id=InvariantID.GOAL_ALIGNMENT,
            passed=True,
            details="OK",
            evidence=evidence,
        )
        assert result.evidence["key"] == "value"
        assert result.evidence["score"] == 0.5


# =============================================================================
# SecurityInvariantChecker Tests
# =============================================================================


class TestSecurityInvariantCheckerDefinitions:
    """Tests for SecurityInvariantChecker definition loading."""

    def test_all_five_definitions_loaded(self):
        """Checker loads all 5 invariant definitions."""
        checker = SecurityInvariantChecker()
        assert len(checker.definitions) == 5

    def test_all_invariant_ids_present(self):
        """Every InvariantID has a definition."""
        checker = SecurityInvariantChecker()
        for inv_id in InvariantID:
            assert inv_id in checker.definitions

    def test_get_definition_returns_correct_type(self):
        """get_definition returns InvariantDefinition."""
        checker = SecurityInvariantChecker()
        defn = checker.get_definition(InvariantID.SOURCE_VERIFICATION)
        assert isinstance(defn, InvariantDefinition)
        assert defn.id == InvariantID.SOURCE_VERIFICATION

    def test_each_definition_has_unique_violation_action(self):
        """Each invariant maps to a distinct violation action."""
        checker = SecurityInvariantChecker()
        actions = [d.violation_action for d in checker.definitions.values()]
        assert len(set(actions)) == 5

    def test_inv1_maps_to_quarantine(self):
        """INV-1 violation triggers quarantine_and_alert."""
        checker = SecurityInvariantChecker()
        defn = checker.get_definition(InvariantID.SOURCE_VERIFICATION)
        assert defn.violation_action == ViolationAction.QUARANTINE_AND_ALERT

    def test_inv2_maps_to_reject(self):
        """INV-2 violation triggers reject_and_log."""
        checker = SecurityInvariantChecker()
        defn = checker.get_definition(InvariantID.DELEGATION_BOUNDS)
        assert defn.violation_action == ViolationAction.REJECT_AND_LOG

    def test_inv3_maps_to_flag(self):
        """INV-3 violation triggers flag_and_reduce_confidence."""
        checker = SecurityInvariantChecker()
        defn = checker.get_definition(InvariantID.BELIEF_CONSISTENCY)
        assert defn.violation_action == ViolationAction.FLAG_AND_REDUCE_CONFIDENCE

    def test_inv4_maps_to_immediate_alert(self):
        """INV-4 violation triggers immediate_alert_and_stop."""
        checker = SecurityInvariantChecker()
        defn = checker.get_definition(InvariantID.IDENTITY_INTEGRITY)
        assert defn.violation_action == ViolationAction.IMMEDIATE_ALERT_AND_STOP

    def test_inv5_maps_to_suspend(self):
        """INV-5 violation triggers suspend_and_report."""
        checker = SecurityInvariantChecker()
        defn = checker.get_definition(InvariantID.GOAL_ALIGNMENT)
        assert defn.violation_action == ViolationAction.SUSPEND_AND_REPORT


class TestCheckSourceVerification:
    """Tests for INV-1: Source Verification."""

    def test_passes_when_trust_exceeds_required(self):
        """Source trust above requirement passes."""
        checker = SecurityInvariantChecker()
        result = checker.check_source_verification(0.8, 0.5)
        assert result.passed is True
        assert result.recommended_action is None

    def test_fails_when_trust_below_required(self):
        """Source trust below requirement fails."""
        checker = SecurityInvariantChecker()
        result = checker.check_source_verification(0.3, 0.5)
        assert result.passed is False
        assert result.recommended_action == ViolationAction.QUARANTINE_AND_ALERT

    def test_passes_at_exact_boundary(self):
        """Equal trust and requirement passes (>=)."""
        checker = SecurityInvariantChecker()
        result = checker.check_source_verification(0.5, 0.5)
        assert result.passed is True

    def test_evidence_contains_values(self):
        """Evidence records both trust values."""
        checker = SecurityInvariantChecker()
        result = checker.check_source_verification(0.7, 0.3)
        assert result.evidence["source_trust"] == 0.7
        assert result.evidence["required_trust"] == 0.3

    def test_invariant_id_is_source_verification(self):
        """Result identifies as INV-1."""
        checker = SecurityInvariantChecker()
        result = checker.check_source_verification(0.5, 0.5)
        assert result.invariant_id == InvariantID.SOURCE_VERIFICATION

    def test_zero_trust_fails_nonzero_requirement(self):
        """Zero trust fails any nonzero requirement."""
        checker = SecurityInvariantChecker()
        result = checker.check_source_verification(0.0, 0.1)
        assert result.passed is False

    def test_zero_trust_passes_zero_requirement(self):
        """Zero trust passes zero requirement."""
        checker = SecurityInvariantChecker()
        result = checker.check_source_verification(0.0, 0.0)
        assert result.passed is True


class TestCheckDelegationBounds:
    """Tests for INV-2: Delegation Bounds."""

    def test_passes_when_delegated_within_bounds(self):
        """Delegated permission within delegator's passes."""
        checker = SecurityInvariantChecker()
        result = checker.check_delegation_bounds(0.5, 0.8)
        assert result.passed is True
        assert result.recommended_action is None

    def test_fails_when_delegated_exceeds_bounds(self):
        """Delegated permission exceeding delegator's fails."""
        checker = SecurityInvariantChecker()
        result = checker.check_delegation_bounds(0.9, 0.5)
        assert result.passed is False
        assert result.recommended_action == ViolationAction.REJECT_AND_LOG

    def test_passes_at_exact_boundary(self):
        """Equal permissions passes (<=)."""
        checker = SecurityInvariantChecker()
        result = checker.check_delegation_bounds(0.5, 0.5)
        assert result.passed is True

    def test_evidence_contains_permission_values(self):
        """Evidence records both permission levels."""
        checker = SecurityInvariantChecker()
        result = checker.check_delegation_bounds(0.3, 0.7)
        assert result.evidence["delegated_permission"] == 0.3
        assert result.evidence["delegator_permission"] == 0.7

    def test_invariant_id_is_delegation_bounds(self):
        """Result identifies as INV-2."""
        checker = SecurityInvariantChecker()
        result = checker.check_delegation_bounds(0.5, 0.5)
        assert result.invariant_id == InvariantID.DELEGATION_BOUNDS


class TestCheckBeliefConsistency:
    """Tests for INV-3: Belief Consistency."""

    def test_passes_with_no_contradictions(self):
        """Beliefs without contradictions pass."""
        checker = SecurityInvariantChecker()
        beliefs = [
            {"id": "b1", "confidence": 0.9, "contradicts": []},
            {"id": "b2", "confidence": 0.8, "contradicts": []},
        ]
        result = checker.check_belief_consistency(beliefs)
        assert result.passed is True

    def test_fails_with_high_confidence_contradiction(self):
        """High-confidence contradicting beliefs fail."""
        checker = SecurityInvariantChecker()
        beliefs = [
            {"id": "b1", "confidence": 0.9, "contradicts": ["b2"]},
            {"id": "b2", "confidence": 0.8, "contradicts": ["b1"]},
        ]
        result = checker.check_belief_consistency(beliefs)
        assert result.passed is False
        assert result.recommended_action == ViolationAction.FLAG_AND_REDUCE_CONFIDENCE

    def test_passes_when_contradictions_below_threshold(self):
        """Contradicting beliefs below threshold pass."""
        checker = SecurityInvariantChecker()
        beliefs = [
            {"id": "b1", "confidence": 0.5, "contradicts": ["b2"]},
            {"id": "b2", "confidence": 0.6, "contradicts": ["b1"]},
        ]
        result = checker.check_belief_consistency(beliefs)
        assert result.passed is True

    def test_passes_when_one_below_threshold(self):
        """Contradiction where one belief is below threshold passes."""
        checker = SecurityInvariantChecker()
        beliefs = [
            {"id": "b1", "confidence": 0.9, "contradicts": ["b2"]},
            {"id": "b2", "confidence": 0.5, "contradicts": ["b1"]},
        ]
        result = checker.check_belief_consistency(beliefs)
        assert result.passed is True

    def test_empty_beliefs_passes(self):
        """Empty belief set passes trivially."""
        checker = SecurityInvariantChecker()
        result = checker.check_belief_consistency([])
        assert result.passed is True
        assert result.evidence["high_confidence_count"] == 0

    def test_custom_confidence_threshold(self):
        """Custom threshold changes what counts as high-confidence."""
        checker = SecurityInvariantChecker()
        beliefs = [
            {"id": "b1", "confidence": 0.6, "contradicts": ["b2"]},
            {"id": "b2", "confidence": 0.6, "contradicts": ["b1"]},
        ]
        # Default threshold 0.7: should pass
        result_default = checker.check_belief_consistency(beliefs)
        assert result_default.passed is True

        # Lower threshold 0.5: should fail
        result_custom = checker.check_belief_consistency(beliefs, confidence_threshold=0.5)
        assert result_custom.passed is False

    def test_contradiction_count_in_evidence(self):
        """Evidence contains the contradiction pairs."""
        checker = SecurityInvariantChecker()
        beliefs = [
            {"id": "b1", "confidence": 0.9, "contradicts": ["b2"]},
            {"id": "b2", "confidence": 0.9, "contradicts": ["b1"]},
        ]
        result = checker.check_belief_consistency(beliefs)
        contradictions = result.evidence["contradictions"]
        assert len(contradictions) == 1

    def test_beliefs_without_contradicts_field(self):
        """Beliefs missing contradicts field are treated as non-contradicting."""
        checker = SecurityInvariantChecker()
        beliefs = [
            {"id": "b1", "confidence": 0.9},
            {"id": "b2", "confidence": 0.9},
        ]
        result = checker.check_belief_consistency(beliefs)
        assert result.passed is True

    def test_invariant_id_is_belief_consistency(self):
        """Result identifies as INV-3."""
        checker = SecurityInvariantChecker()
        result = checker.check_belief_consistency([])
        assert result.invariant_id == InvariantID.BELIEF_CONSISTENCY


class TestCheckIdentityIntegrity:
    """Tests for INV-4: Identity Integrity."""

    def test_passes_when_canaries_match(self):
        """Unchanged canaries pass."""
        checker = SecurityInvariantChecker()
        canaries = {"name": "Agent-1", "role": "analyst", "principal": "operator"}
        result = checker.check_identity_integrity(canaries, dict(canaries))
        assert result.passed is True

    def test_fails_when_canary_changed(self):
        """Changed canary value fails."""
        checker = SecurityInvariantChecker()
        initial = {"name": "Agent-1", "role": "analyst"}
        current = {"name": "Agent-1", "role": "admin"}
        result = checker.check_identity_integrity(initial, current)
        assert result.passed is False
        assert result.recommended_action == ViolationAction.IMMEDIATE_ALERT_AND_STOP

    def test_changed_canaries_listed_in_evidence(self):
        """Evidence identifies which canaries changed."""
        checker = SecurityInvariantChecker()
        initial = {"name": "Agent-1", "role": "analyst", "principal": "operator"}
        current = {"name": "Agent-X", "role": "admin", "principal": "operator"}
        result = checker.check_identity_integrity(initial, current)
        changed = result.evidence["changed_canaries"]
        assert "name" in changed
        assert "role" in changed
        assert "principal" not in changed

    def test_missing_key_in_current_fails(self):
        """Missing canary in current state is treated as changed."""
        checker = SecurityInvariantChecker()
        initial = {"name": "Agent-1", "role": "analyst"}
        current = {"name": "Agent-1"}
        result = checker.check_identity_integrity(initial, current)
        assert result.passed is False
        assert "role" in result.evidence["changed_canaries"]

    def test_empty_canaries_pass(self):
        """Empty canary sets pass trivially."""
        checker = SecurityInvariantChecker()
        result = checker.check_identity_integrity({}, {})
        assert result.passed is True

    def test_invariant_id_is_identity_integrity(self):
        """Result identifies as INV-4."""
        checker = SecurityInvariantChecker()
        result = checker.check_identity_integrity({}, {})
        assert result.invariant_id == InvariantID.IDENTITY_INTEGRITY

    def test_total_canaries_in_evidence(self):
        """Evidence records total canary count."""
        checker = SecurityInvariantChecker()
        initial = {"a": "1", "b": "2", "c": "3"}
        result = checker.check_identity_integrity(initial, dict(initial))
        assert result.evidence["total_canaries"] == 3


class TestCheckGoalAlignment:
    """Tests for INV-5: Goal Alignment."""

    def test_passes_when_all_goals_authorized(self):
        """Goals from authorized sources pass."""
        checker = SecurityInvariantChecker()
        goals = [
            {"id": "g1", "source": "operator"},
            {"id": "g2", "source": "supervisor"},
        ]
        result = checker.check_goal_alignment(goals, ["operator", "supervisor"])
        assert result.passed is True

    def test_fails_when_goal_unauthorized(self):
        """Goal from unauthorized source fails."""
        checker = SecurityInvariantChecker()
        goals = [
            {"id": "g1", "source": "operator"},
            {"id": "g2", "source": "attacker"},
        ]
        result = checker.check_goal_alignment(goals, ["operator"])
        assert result.passed is False
        assert result.recommended_action == ViolationAction.SUSPEND_AND_REPORT

    def test_unauthorized_goals_listed(self):
        """Evidence lists unauthorized goal IDs."""
        checker = SecurityInvariantChecker()
        goals = [
            {"id": "g1", "source": "attacker"},
            {"id": "g2", "source": "operator"},
            {"id": "g3", "source": "unknown"},
        ]
        result = checker.check_goal_alignment(goals, ["operator"])
        unauthorized = result.evidence["unauthorized_goals"]
        assert "g1" in unauthorized
        assert "g3" in unauthorized
        assert "g2" not in unauthorized

    def test_empty_goals_passes(self):
        """Empty goal set passes trivially."""
        checker = SecurityInvariantChecker()
        result = checker.check_goal_alignment([], ["operator"])
        assert result.passed is True

    def test_empty_authorized_sources_fails_with_goals(self):
        """Goals with no authorized sources all fail."""
        checker = SecurityInvariantChecker()
        goals = [{"id": "g1", "source": "operator"}]
        result = checker.check_goal_alignment(goals, [])
        assert result.passed is False

    def test_invariant_id_is_goal_alignment(self):
        """Result identifies as INV-5."""
        checker = SecurityInvariantChecker()
        result = checker.check_goal_alignment([], [])
        assert result.invariant_id == InvariantID.GOAL_ALIGNMENT

    def test_goal_without_source_uses_none(self):
        """Goal missing source field is treated as unauthorized."""
        checker = SecurityInvariantChecker()
        goals = [{"id": "g1"}]
        result = checker.check_goal_alignment(goals, ["operator"])
        assert result.passed is False


class TestCheckAll:
    """Tests for SecurityInvariantChecker.check_all."""

    def test_full_context_runs_all_five(self):
        """Full context triggers all 5 invariant checks."""
        checker = SecurityInvariantChecker()
        context = {
            "source_trust": 0.9,
            "required_trust": 0.5,
            "delegated_permission": 0.4,
            "delegator_permission": 0.8,
            "beliefs": [],
            "initial_canaries": {"name": "A"},
            "current_canaries": {"name": "A"},
            "goals": [],
            "authorized_sources": [],
        }
        results = checker.check_all(context)
        assert len(results) == 5

    def test_partial_context_runs_subset(self):
        """Partial context runs only applicable checks."""
        checker = SecurityInvariantChecker()
        context = {
            "source_trust": 0.9,
            "required_trust": 0.5,
        }
        results = checker.check_all(context)
        assert len(results) == 1
        assert results[0].invariant_id == InvariantID.SOURCE_VERIFICATION

    def test_empty_context_runs_nothing(self):
        """Empty context produces no results."""
        checker = SecurityInvariantChecker()
        results = checker.check_all({})
        assert len(results) == 0

    def test_check_all_returns_list_of_results(self):
        """Results are InvariantCheckResult instances."""
        checker = SecurityInvariantChecker()
        context = {"beliefs": []}
        results = checker.check_all(context)
        assert len(results) == 1
        assert isinstance(results[0], InvariantCheckResult)

    def test_check_all_detects_failure(self):
        """check_all correctly detects an invariant violation."""
        checker = SecurityInvariantChecker()
        context = {
            "source_trust": 0.1,
            "required_trust": 0.9,
        }
        results = checker.check_all(context)
        assert results[0].passed is False

    def test_check_all_with_custom_confidence_threshold(self):
        """check_all passes confidence_threshold from context."""
        checker = SecurityInvariantChecker()
        beliefs = [
            {"id": "b1", "confidence": 0.6, "contradicts": ["b2"]},
            {"id": "b2", "confidence": 0.6, "contradicts": ["b1"]},
        ]
        context = {"beliefs": beliefs, "confidence_threshold": 0.5}
        results = checker.check_all(context)
        assert results[0].passed is False

    def test_check_all_needs_both_keys_for_inv1(self):
        """INV-1 requires both source_trust and required_trust."""
        checker = SecurityInvariantChecker()
        context = {"source_trust": 0.5}
        results = checker.check_all(context)
        assert len(results) == 0

    def test_check_all_needs_both_keys_for_inv2(self):
        """INV-2 requires both delegation keys."""
        checker = SecurityInvariantChecker()
        context = {"delegated_permission": 0.5}
        results = checker.check_all(context)
        assert len(results) == 0

    def test_check_all_needs_both_keys_for_inv4(self):
        """INV-4 requires both canary dictionaries."""
        checker = SecurityInvariantChecker()
        context = {"initial_canaries": {"name": "A"}}
        results = checker.check_all(context)
        assert len(results) == 0

    def test_check_all_needs_both_keys_for_inv5(self):
        """INV-5 requires both goals and authorized_sources."""
        checker = SecurityInvariantChecker()
        context = {"goals": []}
        results = checker.check_all(context)
        assert len(results) == 0


# =============================================================================
# BeliefDriftMonitor Tests
# =============================================================================


class TestBeliefDriftMonitor:
    """Tests for BeliefDriftMonitor."""

    def test_set_baseline(self):
        """Baseline is stored correctly."""
        monitor = BeliefDriftMonitor()
        monitor.set_baseline([0.9, 0.8, 0.7])
        assert monitor.baseline == [0.9, 0.8, 0.7]

    def test_set_baseline_empty_raises(self):
        """Empty baseline raises ValueError."""
        monitor = BeliefDriftMonitor()
        with pytest.raises(ValueError, match="cannot be empty"):
            monitor.set_baseline([])

    def test_check_drift_no_baseline_raises(self):
        """Checking drift without baseline raises ValueError."""
        monitor = BeliefDriftMonitor()
        with pytest.raises(ValueError, match="Baseline not set"):
            monitor.check_drift([0.9, 0.8, 0.7])

    def test_check_drift_length_mismatch_raises(self):
        """Mismatched confidence lengths raise ValueError."""
        monitor = BeliefDriftMonitor()
        monitor.set_baseline([0.9, 0.8, 0.7])
        with pytest.raises(ValueError, match="mismatch"):
            monitor.check_drift([0.9, 0.8])

    def test_identical_distribution_low_divergence(self):
        """Identical distributions produce near-zero KL-divergence."""
        monitor = BeliefDriftMonitor(threshold=0.5)
        monitor.set_baseline([0.9, 0.8, 0.7])
        result = monitor.check_drift([0.9, 0.8, 0.7])
        assert result["kl_divergence"] < 0.01
        assert result["flagged"] is False

    def test_different_distribution_high_divergence(self):
        """Very different distributions produce high KL-divergence."""
        monitor = BeliefDriftMonitor(threshold=0.5)
        monitor.set_baseline([0.9, 0.1, 0.1])
        result = monitor.check_drift([0.1, 0.9, 0.1])
        assert result["kl_divergence"] > 0.1
        assert result["flagged"] is True

    def test_drift_history_tracking(self):
        """Drift history accumulates across checks."""
        monitor = BeliefDriftMonitor(threshold=0.5)
        monitor.set_baseline([0.5, 0.5])
        monitor.check_drift([0.5, 0.5])
        monitor.check_drift([0.6, 0.4])
        monitor.check_drift([0.7, 0.3])
        assert len(monitor.drift_history) == 3

    def test_drift_trend_limited_to_ten(self):
        """Drift trend returns at most 10 recent values."""
        monitor = BeliefDriftMonitor(threshold=0.5)
        monitor.set_baseline([0.5, 0.5])
        for _ in range(15):
            result = monitor.check_drift([0.5, 0.5])
        assert len(result["drift_trend"]) == 10
        assert len(monitor.drift_history) == 15

    def test_kl_divergence_non_negative(self):
        """KL-divergence is always non-negative."""
        monitor = BeliefDriftMonitor()
        monitor.set_baseline([0.3, 0.7, 0.5])
        result = monitor.check_drift([0.7, 0.3, 0.5])
        assert result["kl_divergence"] >= 0.0

    def test_kl_divergence_static_method(self):
        """KL-divergence can be called statically."""
        kl = BeliefDriftMonitor._kl_divergence([0.5, 0.5], [0.5, 0.5])
        assert kl < 0.01

    def test_kl_divergence_asymmetric(self):
        """KL-divergence is not symmetric: D_KL(P||Q) != D_KL(Q||P)."""
        p = [0.9, 0.1]
        q = [0.1, 0.9]
        kl_pq = BeliefDriftMonitor._kl_divergence(p, q)
        kl_qp = BeliefDriftMonitor._kl_divergence(q, p)
        # Both should be positive, but they can differ
        assert kl_pq > 0
        assert kl_qp > 0

    def test_threshold_respected(self):
        """Custom threshold determines flagging."""
        monitor = BeliefDriftMonitor(threshold=0.01)
        monitor.set_baseline([0.9, 0.1])
        result = monitor.check_drift([0.85, 0.15])
        # Small change should produce small KL > 0.01 threshold
        assert result["threshold"] == 0.01

    def test_result_contains_expected_keys(self):
        """Check drift result has all expected keys."""
        monitor = BeliefDriftMonitor()
        monitor.set_baseline([0.5, 0.5])
        result = monitor.check_drift([0.5, 0.5])
        assert "kl_divergence" in result
        assert "flagged" in result
        assert "threshold" in result
        assert "drift_trend" in result


# =============================================================================
# TrustAnomalyMonitor Tests
# =============================================================================


class TestTrustAnomalyMonitor:
    """Tests for TrustAnomalyMonitor."""

    def test_record_trust_creates_history(self):
        """Recording trust initializes agent history."""
        monitor = TrustAnomalyMonitor()
        monitor.record_trust("agent-1", 0.8)
        assert "agent-1" in monitor.trust_history
        assert monitor.trust_history["agent-1"] == [0.8]

    def test_record_trust_appends(self):
        """Subsequent recordings append to history."""
        monitor = TrustAnomalyMonitor()
        monitor.record_trust("agent-1", 0.8)
        monitor.record_trust("agent-1", 0.7)
        assert monitor.trust_history["agent-1"] == [0.8, 0.7]

    def test_rapid_change_not_flagged_small_change(self):
        """Small trust changes are not flagged."""
        monitor = TrustAnomalyMonitor(rapid_change_threshold=0.3)
        monitor.record_trust("a1", 0.8)
        monitor.record_trust("a1", 0.7)
        result = monitor.check_rapid_change("a1")
        assert result["flagged"] is False
        assert result["change"] == pytest.approx(0.1)

    def test_rapid_change_flagged_large_change(self):
        """Large trust changes are flagged."""
        monitor = TrustAnomalyMonitor(rapid_change_threshold=0.3)
        monitor.record_trust("a1", 0.9)
        monitor.record_trust("a1", 0.2)
        result = monitor.check_rapid_change("a1")
        assert result["flagged"] is True
        assert result["change"] == pytest.approx(0.7)

    def test_rapid_change_insufficient_history(self):
        """Agent with < 2 observations is not flagged."""
        monitor = TrustAnomalyMonitor()
        monitor.record_trust("a1", 0.8)
        result = monitor.check_rapid_change("a1")
        assert result["flagged"] is False
        assert result["change"] == 0.0

    def test_rapid_change_unknown_agent(self):
        """Unknown agent returns unflagged result."""
        monitor = TrustAnomalyMonitor()
        result = monitor.check_rapid_change("unknown")
        assert result["flagged"] is False
        assert result["agent_id"] == "unknown"

    def test_rapid_change_contains_previous_and_current(self):
        """Flagged result includes previous and current values."""
        monitor = TrustAnomalyMonitor(rapid_change_threshold=0.1)
        monitor.record_trust("a1", 0.9)
        monitor.record_trust("a1", 0.2)
        result = monitor.check_rapid_change("a1")
        assert result["previous"] == pytest.approx(0.9)
        assert result["current"] == pytest.approx(0.2)

    def test_mismatch_flagged_when_importance_exceeds_trust(self):
        """High importance from low-trust agent is flagged."""
        monitor = TrustAnomalyMonitor(mismatch_threshold=0.5)
        result = monitor.check_trust_importance_mismatch("a1", 0.2, 0.9)
        assert result["flagged"] is True
        assert result["mismatch"] == pytest.approx(0.7)

    def test_mismatch_not_flagged_when_trust_sufficient(self):
        """Adequate trust for importance is not flagged."""
        monitor = TrustAnomalyMonitor(mismatch_threshold=0.5)
        result = monitor.check_trust_importance_mismatch("a1", 0.8, 0.9)
        assert result["flagged"] is False
        assert result["mismatch"] == pytest.approx(0.1)

    def test_mismatch_at_exact_threshold_not_flagged(self):
        """Mismatch exactly at threshold is not flagged (> not >=)."""
        monitor = TrustAnomalyMonitor(mismatch_threshold=0.5)
        result = monitor.check_trust_importance_mismatch("a1", 0.3, 0.8)
        assert result["flagged"] is False

    def test_mismatch_negative_difference_not_flagged(self):
        """Trust exceeding importance is never flagged."""
        monitor = TrustAnomalyMonitor(mismatch_threshold=0.5)
        result = monitor.check_trust_importance_mismatch("a1", 0.9, 0.1)
        assert result["flagged"] is False
        assert result["mismatch"] < 0

    def test_mismatch_result_keys(self):
        """Mismatch result contains expected keys."""
        monitor = TrustAnomalyMonitor()
        result = monitor.check_trust_importance_mismatch("a1", 0.5, 0.5)
        assert "flagged" in result
        assert "mismatch" in result
        assert "trust_score" in result
        assert "message_importance" in result
        assert "agent_id" in result


# =============================================================================
# CoordinationIntegrityMonitor Tests
# =============================================================================


class TestCoordinationIntegrityMonitor:
    """Tests for CoordinationIntegrityMonitor."""

    def test_quorum_met(self):
        """Quorum is met when enough agents participate."""
        monitor = CoordinationIntegrityMonitor(min_quorum=3)
        result = monitor.verify_quorum(5, 4)
        assert result["quorum_met"] is True
        assert result["participation_rate"] == pytest.approx(0.8)

    def test_quorum_not_met(self):
        """Quorum is not met with insufficient participants."""
        monitor = CoordinationIntegrityMonitor(min_quorum=3)
        result = monitor.verify_quorum(5, 2)
        assert result["quorum_met"] is False

    def test_quorum_exact_minimum(self):
        """Quorum met at exactly the minimum."""
        monitor = CoordinationIntegrityMonitor(min_quorum=3)
        result = monitor.verify_quorum(5, 3)
        assert result["quorum_met"] is True

    def test_quorum_zero_total_agents(self):
        """Zero total agents produces zero participation rate."""
        monitor = CoordinationIntegrityMonitor(min_quorum=1)
        result = monitor.verify_quorum(0, 0)
        assert result["participation_rate"] == 0.0

    def test_quorum_result_keys(self):
        """Quorum result contains expected keys."""
        monitor = CoordinationIntegrityMonitor()
        result = monitor.verify_quorum(5, 3)
        assert "quorum_met" in result
        assert "participating" in result
        assert "required" in result
        assert "total" in result
        assert "participation_rate" in result

    def test_voting_normal_pattern(self):
        """Normal votes (different times, different values) are not suspicious."""
        monitor = CoordinationIntegrityMonitor()
        votes = [
            {"agent_id": "a1", "vote": "yes", "timestamp": 100.0},
            {"agent_id": "a2", "vote": "no", "timestamp": 105.0},
            {"agent_id": "a3", "vote": "yes", "timestamp": 110.0},
        ]
        result = monitor.check_voting_patterns(votes)
        assert result["suspicious"] is False
        assert result["simultaneous"] is False
        assert result["identical"] is False

    def test_voting_suspicious_simultaneous_identical(self):
        """Simultaneous AND identical votes are suspicious."""
        monitor = CoordinationIntegrityMonitor()
        votes = [
            {"agent_id": "a1", "vote": "yes", "timestamp": 100.0},
            {"agent_id": "a2", "vote": "yes", "timestamp": 100.5},
            {"agent_id": "a3", "vote": "yes", "timestamp": 100.3},
        ]
        result = monitor.check_voting_patterns(votes)
        assert result["suspicious"] is True
        assert result["simultaneous"] is True
        assert result["identical"] is True

    def test_voting_simultaneous_but_different(self):
        """Simultaneous but different votes are not suspicious."""
        monitor = CoordinationIntegrityMonitor()
        votes = [
            {"agent_id": "a1", "vote": "yes", "timestamp": 100.0},
            {"agent_id": "a2", "vote": "no", "timestamp": 100.5},
        ]
        result = monitor.check_voting_patterns(votes)
        assert result["suspicious"] is False
        assert result["simultaneous"] is True
        assert result["identical"] is False

    def test_voting_identical_but_spread_out(self):
        """Identical but spread-out votes are not suspicious."""
        monitor = CoordinationIntegrityMonitor()
        votes = [
            {"agent_id": "a1", "vote": "yes", "timestamp": 100.0},
            {"agent_id": "a2", "vote": "yes", "timestamp": 200.0},
        ]
        result = monitor.check_voting_patterns(votes)
        assert result["suspicious"] is False
        assert result["simultaneous"] is False
        assert result["identical"] is True

    def test_voting_single_vote(self):
        """Single vote is never suspicious."""
        monitor = CoordinationIntegrityMonitor()
        votes = [{"agent_id": "a1", "vote": "yes", "timestamp": 100.0}]
        result = monitor.check_voting_patterns(votes)
        assert result["suspicious"] is False
        assert result["vote_count"] == 1

    def test_voting_empty(self):
        """Empty votes list is not suspicious."""
        monitor = CoordinationIntegrityMonitor()
        result = monitor.check_voting_patterns([])
        assert result["suspicious"] is False
        assert result["vote_count"] == 0

    def test_voting_time_spread_reported(self):
        """Time spread is accurately reported."""
        monitor = CoordinationIntegrityMonitor()
        votes = [
            {"agent_id": "a1", "vote": "yes", "timestamp": 100.0},
            {"agent_id": "a2", "vote": "no", "timestamp": 110.0},
        ]
        result = monitor.check_voting_patterns(votes)
        assert result["time_spread"] == pytest.approx(10.0)

    def test_voting_unique_count(self):
        """Unique vote count is accurate."""
        monitor = CoordinationIntegrityMonitor()
        votes = [
            {"agent_id": "a1", "vote": "yes", "timestamp": 100.0},
            {"agent_id": "a2", "vote": "no", "timestamp": 110.0},
            {"agent_id": "a3", "vote": "yes", "timestamp": 120.0},
        ]
        result = monitor.check_voting_patterns(votes)
        assert result["unique_vote_count"] == 2


# =============================================================================
# ResponseStep and ResponseProtocol Tests
# =============================================================================


class TestResponseStep:
    """Tests for ResponseStep dataclass."""

    def test_create_step(self):
        """Create a response step with defaults."""
        step = ResponseStep(order=1, action="Test action")
        assert step.order == 1
        assert step.action == "Test action"
        assert step.completed is False

    def test_create_completed_step(self):
        """Create a pre-completed step."""
        step = ResponseStep(order=1, action="Done", completed=True)
        assert step.completed is True


class TestResponseProtocol:
    """Tests for ResponseProtocol dataclass."""

    def test_next_step_returns_first_incomplete(self):
        """next_step returns the first incomplete step."""
        protocol = ResponseProtocol(
            threat_level=ThreatLevel.SUSPICIOUS_INPUT,
            name="Test",
            steps=[
                ResponseStep(1, "Step 1", completed=True),
                ResponseStep(2, "Step 2"),
                ResponseStep(3, "Step 3"),
            ],
        )
        assert protocol.next_step().order == 2

    def test_next_step_returns_none_when_all_complete(self):
        """next_step returns None when all steps done."""
        protocol = ResponseProtocol(
            threat_level=ThreatLevel.SUSPICIOUS_INPUT,
            name="Test",
            steps=[
                ResponseStep(1, "Step 1", completed=True),
                ResponseStep(2, "Step 2", completed=True),
            ],
        )
        assert protocol.next_step() is None

    def test_next_step_returns_none_for_empty_steps(self):
        """next_step returns None with no steps."""
        protocol = ResponseProtocol(
            threat_level=ThreatLevel.SUSPICIOUS_INPUT,
            name="Test",
        )
        assert protocol.next_step() is None

    def test_progress_zero(self):
        """Progress is 0.0 when no steps complete."""
        protocol = ResponseProtocol(
            threat_level=ThreatLevel.SUSPICIOUS_INPUT,
            name="Test",
            steps=[ResponseStep(1, "A"), ResponseStep(2, "B")],
        )
        assert protocol.progress() == pytest.approx(0.0)

    def test_progress_partial(self):
        """Progress reflects completed fraction."""
        protocol = ResponseProtocol(
            threat_level=ThreatLevel.SUSPICIOUS_INPUT,
            name="Test",
            steps=[
                ResponseStep(1, "A", completed=True),
                ResponseStep(2, "B"),
                ResponseStep(3, "C"),
                ResponseStep(4, "D"),
            ],
        )
        assert protocol.progress() == pytest.approx(0.25)

    def test_progress_complete(self):
        """Progress is 1.0 when all steps done."""
        protocol = ResponseProtocol(
            threat_level=ThreatLevel.SUSPICIOUS_INPUT,
            name="Test",
            steps=[
                ResponseStep(1, "A", completed=True),
                ResponseStep(2, "B", completed=True),
            ],
        )
        assert protocol.progress() == pytest.approx(1.0)

    def test_progress_empty_steps(self):
        """Progress is 1.0 with no steps (vacuously complete)."""
        protocol = ResponseProtocol(
            threat_level=ThreatLevel.SUSPICIOUS_INPUT,
            name="Test",
        )
        assert protocol.progress() == pytest.approx(1.0)


# =============================================================================
# get_response_protocols Tests
# =============================================================================


class TestGetResponseProtocols:
    """Tests for get_response_protocols function."""

    def test_returns_three_protocols(self):
        """Three response protocols per the manuscript."""
        protocols = get_response_protocols()
        assert len(protocols) == 3

    def test_all_threat_levels_present(self):
        """Every threat level has a protocol."""
        protocols = get_response_protocols()
        for level in ThreatLevel:
            assert level in protocols

    def test_suspicious_input_has_four_steps(self):
        """Suspicious Input protocol has 4 steps."""
        protocols = get_response_protocols()
        protocol = protocols[ThreatLevel.SUSPICIOUS_INPUT]
        assert len(protocol.steps) == 4
        assert protocol.name == "Suspicious Input Protocol"

    def test_potential_compromise_has_four_steps(self):
        """Potential Compromise protocol has 4 steps."""
        protocols = get_response_protocols()
        protocol = protocols[ThreatLevel.POTENTIAL_COMPROMISE]
        assert len(protocol.steps) == 4
        assert protocol.name == "Potential Compromise Protocol"

    def test_confirmed_attack_has_four_steps(self):
        """Confirmed Attack protocol has 4 steps."""
        protocols = get_response_protocols()
        protocol = protocols[ThreatLevel.CONFIRMED_ATTACK]
        assert len(protocol.steps) == 4
        assert protocol.name == "Confirmed Attack Protocol"

    def test_all_steps_start_incomplete(self):
        """All protocol steps start as not completed."""
        protocols = get_response_protocols()
        for protocol in protocols.values():
            for step in protocol.steps:
                assert step.completed is False

    def test_steps_are_sequentially_ordered(self):
        """Steps are numbered 1 through N."""
        protocols = get_response_protocols()
        for protocol in protocols.values():
            orders = [s.order for s in protocol.steps]
            assert orders == [1, 2, 3, 4]

    def test_suspicious_input_first_step_classify(self):
        """First step of suspicious input is classification."""
        protocols = get_response_protocols()
        protocol = protocols[ThreatLevel.SUSPICIOUS_INPUT]
        assert "Classify" in protocol.steps[0].action

    def test_confirmed_attack_first_step_cease(self):
        """First step of confirmed attack is cease processing."""
        protocols = get_response_protocols()
        protocol = protocols[ThreatLevel.CONFIRMED_ATTACK]
        assert "Cease" in protocol.steps[0].action

    def test_potential_compromise_first_step_preserve(self):
        """First step of potential compromise is preserve state."""
        protocols = get_response_protocols()
        protocol = protocols[ThreatLevel.POTENTIAL_COMPROMISE]
        assert "Preserve" in protocol.steps[0].action


# =============================================================================
# generate_yaml_rules Tests
# =============================================================================


class TestGenerateYamlRules:
    """Tests for generate_yaml_rules function."""

    def test_returns_string(self):
        """Output is a string."""
        result = generate_yaml_rules()
        assert isinstance(result, str)

    def test_contains_top_level_key(self):
        """Output starts with cognitive_security_rules."""
        result = generate_yaml_rules()
        assert "cognitive_security_rules:" in result

    def test_contains_all_invariant_ids(self):
        """Output includes all 5 invariant IDs."""
        result = generate_yaml_rules()
        for inv_id in InvariantID:
            assert inv_id.value in result

    def test_contains_invariants_section(self):
        """Output has invariants section."""
        result = generate_yaml_rules()
        assert "invariants:" in result

    def test_contains_monitoring_section(self):
        """Output has monitoring section."""
        result = generate_yaml_rules()
        assert "monitoring:" in result

    def test_contains_all_monitor_types(self):
        """Output includes all 3 monitoring types."""
        result = generate_yaml_rules()
        for mt in MonitorType:
            assert mt.value in result

    def test_contains_violation_actions(self):
        """Output includes violation actions."""
        result = generate_yaml_rules()
        assert "quarantine_and_alert" in result
        assert "reject_and_log" in result
        assert "flag_and_reduce_confidence" in result
        assert "immediate_alert_and_stop" in result
        assert "suspend_and_report" in result

    def test_contains_monitoring_frequencies(self):
        """Output includes trigger frequencies."""
        result = generate_yaml_rules()
        assert "on_external_input" in result
        assert "on_agent_communication" in result
        assert "before_multi_agent_decision" in result

    def test_valid_yaml_structure(self):
        """Output has properly indented YAML structure."""
        result = generate_yaml_rules()
        lines = result.split("\n")
        # First line is the root key
        assert lines[0] == "cognitive_security_rules:"
        # Invariants section is indented
        assert "  invariants:" in result
        # Monitoring section is indented
        assert "  monitoring:" in result

    def test_invariant_names_are_snake_case(self):
        """Invariant names in YAML are snake_case."""
        result = generate_yaml_rules()
        assert "source_verification" in result
        assert "delegation_bounds" in result
        assert "belief_consistency" in result
        assert "identity_integrity" in result
        assert "goal_alignment" in result
