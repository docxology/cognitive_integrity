"""
Agent-Readable Security Guidelines for Cognitive Security.

Implements Section 04 of the Practical Implementation Guide:
Security invariants, self-monitoring protocols, response protocols,
and machine-readable YAML rule generation.

Manuscript mapping:
    Section 04 - Agent-Readable Guidelines
    - 5 Core Security Invariants (INV-1 through INV-5)
    - 3 Self-Monitoring Protocols (belief drift, trust anomaly, coordination)
    - 3 Response Protocols (suspicious, compromise, confirmed attack)
    - Machine-readable YAML output format
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np

# =============================================================================
# Invariant System
# =============================================================================


class InvariantID(Enum):
    """Identifiers for the five core security invariants.

    Each value matches the manuscript notation (INV-1 through INV-5).
    """

    SOURCE_VERIFICATION = "INV-1"
    DELEGATION_BOUNDS = "INV-2"
    BELIEF_CONSISTENCY = "INV-3"
    IDENTITY_INTEGRITY = "INV-4"
    GOAL_ALIGNMENT = "INV-5"


class ViolationAction(Enum):
    """Actions to take on invariant violation.

    Each action maps to a specific invariant's violation response
    as defined in the manuscript Section 04.
    """

    QUARANTINE_AND_ALERT = "quarantine_and_alert"
    REJECT_AND_LOG = "reject_and_log"
    FLAG_AND_REDUCE_CONFIDENCE = "flag_and_reduce_confidence"
    IMMEDIATE_ALERT_AND_STOP = "immediate_alert_and_stop"
    SUSPEND_AND_REPORT = "suspend_and_report"


class MonitorType(Enum):
    """Types of self-monitoring protocols.

    Maps to the three monitoring protocols defined in Section 04.
    """

    BELIEF_DRIFT = "belief_drift"
    TRUST_ANOMALY = "trust_anomaly"
    COORDINATION_INTEGRITY = "coordination_integrity"


class ThreatLevel(Enum):
    """Threat severity levels for response protocols.

    Ordered from least to most severe. Each level triggers
    a distinct response protocol.
    """

    SUSPICIOUS_INPUT = "suspicious_input"
    POTENTIAL_COMPROMISE = "potential_compromise"
    CONFIRMED_ATTACK = "confirmed_attack"


@dataclass
class InvariantDefinition:
    """Definition of a security invariant.

    Captures the complete specification of a single invariant from
    the manuscript, including its checking rule and violation response.

    Args:
        id: Invariant identifier (INV-1 through INV-5)
        name: Human-readable name
        rule: Natural language rule description
        check_description: What the check verifies (predicate form)
        violation_action: What to do on violation
        manuscript_reference: Section reference in the manuscript
    """

    id: InvariantID
    name: str
    rule: str
    check_description: str
    violation_action: ViolationAction
    manuscript_reference: str = "Section 04"


@dataclass
class InvariantCheckResult:
    """Result of checking a single invariant.

    Produced by SecurityInvariantChecker methods. When the invariant
    holds, ``passed`` is True and ``recommended_action`` is None.
    When violated, ``recommended_action`` contains the violation action.

    Args:
        invariant_id: Which invariant was checked
        passed: Whether the invariant held
        details: Description of check outcome
        evidence: Supporting evidence dictionary
        recommended_action: What to do next (None if passed)
    """

    invariant_id: InvariantID
    passed: bool
    details: str
    evidence: dict[str, Any] = field(default_factory=dict)
    recommended_action: ViolationAction | None = None


class SecurityInvariantChecker:
    """Implements all 5 security invariants with predicate functions.

    Each invariant has a dedicated check method that accepts typed
    parameters and returns an InvariantCheckResult. The ``check_all``
    method accepts a context dictionary and dispatches to all applicable
    individual checks.

    Example::

        checker = SecurityInvariantChecker()
        result = checker.check_source_verification(
            source_trust=0.3, required_trust=0.5
        )
        assert not result.passed
    """

    def __init__(self) -> None:
        """Initialize with invariant definitions."""
        self.definitions: dict[InvariantID, InvariantDefinition] = {}
        self._load_definitions()

    def _load_definitions(self) -> None:
        """Load the 5 invariant definitions from manuscript Section 04."""
        self.definitions = {
            InvariantID.SOURCE_VERIFICATION: InvariantDefinition(
                id=InvariantID.SOURCE_VERIFICATION,
                name="Source Verification",
                rule="Before acting on information, verify its source is within expected trust bounds.",
                check_description="source_trust >= required_trust_for_action",
                violation_action=ViolationAction.QUARANTINE_AND_ALERT,
            ),
            InvariantID.DELEGATION_BOUNDS: InvariantDefinition(
                id=InvariantID.DELEGATION_BOUNDS,
                name="Delegation Bounds",
                rule="Never accept delegated authority that exceeds the delegator's direct authority.",
                check_description="delegated_permission <= delegator_direct_permission",
                violation_action=ViolationAction.REJECT_AND_LOG,
            ),
            InvariantID.BELIEF_CONSISTENCY: InvariantDefinition(
                id=InvariantID.BELIEF_CONSISTENCY,
                name="Belief Consistency",
                rule="Do not hold high-confidence beliefs that contradict each other.",
                check_description="No contradicting beliefs with confidence > 0.7",
                violation_action=ViolationAction.FLAG_AND_REDUCE_CONFIDENCE,
            ),
            InvariantID.IDENTITY_INTEGRITY: InvariantDefinition(
                id=InvariantID.IDENTITY_INTEGRITY,
                name="Identity Integrity",
                rule="Core identity beliefs must not change during a session.",
                check_description="Identity canaries (name, role, principal, capabilities) unchanged",
                violation_action=ViolationAction.IMMEDIATE_ALERT_AND_STOP,
            ),
            InvariantID.GOAL_ALIGNMENT: InvariantDefinition(
                id=InvariantID.GOAL_ALIGNMENT,
                name="Goal Alignment",
                rule="Current goals must trace to authorized sources.",
                check_description="Goal provenance leads to principal or authorized delegator",
                violation_action=ViolationAction.SUSPEND_AND_REPORT,
            ),
        }

    def get_definition(self, invariant_id: InvariantID) -> InvariantDefinition:
        """Get invariant definition by ID.

        Args:
            invariant_id: Which invariant to retrieve

        Returns:
            InvariantDefinition for the specified invariant

        Raises:
            KeyError: If invariant_id is not recognized
        """
        return self.definitions[invariant_id]

    def check_source_verification(
        self,
        source_trust: float,
        required_trust: float,
    ) -> InvariantCheckResult:
        """INV-1: Check source trust meets requirement.

        Verifies that the information source has sufficient trust
        to perform the requested action.

        Args:
            source_trust: Trust level of the source (0.0-1.0)
            required_trust: Minimum trust required for action (0.0-1.0)

        Returns:
            InvariantCheckResult indicating pass/fail
        """
        passed = source_trust >= required_trust
        return InvariantCheckResult(
            invariant_id=InvariantID.SOURCE_VERIFICATION,
            passed=passed,
            details=(
                f"Source trust {source_trust:.2f} {'meets' if passed else 'below'} "
                f"required {required_trust:.2f}"
            ),
            evidence={"source_trust": source_trust, "required_trust": required_trust},
            recommended_action=None if passed else ViolationAction.QUARANTINE_AND_ALERT,
        )

    def check_delegation_bounds(
        self,
        delegated_permission: float,
        delegator_permission: float,
    ) -> InvariantCheckResult:
        """INV-2: Check delegated authority doesn't exceed delegator's.

        Ensures no permission escalation through delegation chains.

        Args:
            delegated_permission: Permission level being delegated (0.0-1.0)
            delegator_permission: Delegator's direct permission (0.0-1.0)

        Returns:
            InvariantCheckResult indicating pass/fail
        """
        passed = delegated_permission <= delegator_permission
        return InvariantCheckResult(
            invariant_id=InvariantID.DELEGATION_BOUNDS,
            passed=passed,
            details=(
                f"Delegated {delegated_permission:.2f} "
                f"{'within' if passed else 'exceeds'} "
                f"delegator's {delegator_permission:.2f}"
            ),
            evidence={
                "delegated_permission": delegated_permission,
                "delegator_permission": delegator_permission,
            },
            recommended_action=None if passed else ViolationAction.REJECT_AND_LOG,
        )

    def check_belief_consistency(
        self,
        beliefs: list[dict[str, Any]],
        confidence_threshold: float = 0.7,
    ) -> InvariantCheckResult:
        """INV-3: Check for contradicting high-confidence beliefs.

        Scans all beliefs above the confidence threshold for mutual
        contradictions. A contradiction exists when belief A lists
        belief B in its ``contradicts`` field and both exceed the
        threshold.

        Each belief dict should have:
        - ``"id"``: str identifier
        - ``"confidence"``: float (0-1)
        - ``"contradicts"``: list[str] of belief IDs it contradicts

        Args:
            beliefs: List of belief dictionaries
            confidence_threshold: Confidence above which contradictions matter

        Returns:
            InvariantCheckResult indicating pass/fail
        """
        high_confidence = {
            b["id"]: b
            for b in beliefs
            if b.get("id") is not None and b.get("confidence", 0) > confidence_threshold
        }

        contradictions: list[tuple[str, str]] = []
        for bid, belief in high_confidence.items():
            for contra_id in belief.get("contradicts", []):
                if contra_id in high_confidence and (contra_id, bid) not in contradictions:
                    contradictions.append((bid, contra_id))

        passed = len(contradictions) == 0
        return InvariantCheckResult(
            invariant_id=InvariantID.BELIEF_CONSISTENCY,
            passed=passed,
            details=(
                f"No contradictions found among {len(high_confidence)} high-confidence beliefs"
                if passed
                else f"Found {len(contradictions)} contradiction(s) among high-confidence beliefs"
            ),
            evidence={
                "high_confidence_count": len(high_confidence),
                "contradictions": contradictions,
            },
            recommended_action=None if passed else ViolationAction.FLAG_AND_REDUCE_CONFIDENCE,
        )

    def check_identity_integrity(
        self,
        initial_canaries: dict[str, str],
        current_canaries: dict[str, str],
    ) -> InvariantCheckResult:
        """INV-4: Check identity canaries haven't changed.

        Compares session-start canary values against current values.
        Any change in name, role, principal, or capabilities fields
        indicates potential identity compromise.

        Args:
            initial_canaries: Canary values at session start
            current_canaries: Current canary values

        Returns:
            InvariantCheckResult indicating pass/fail
        """
        changed: list[str] = []
        for key, initial_val in initial_canaries.items():
            current_val = current_canaries.get(key)
            if current_val != initial_val:
                changed.append(key)

        passed = len(changed) == 0
        return InvariantCheckResult(
            invariant_id=InvariantID.IDENTITY_INTEGRITY,
            passed=passed,
            details=(
                f"All {len(initial_canaries)} identity canaries intact"
                if passed
                else f"Identity canaries changed: {', '.join(changed)}"
            ),
            evidence={
                "total_canaries": len(initial_canaries),
                "changed_canaries": changed,
            },
            recommended_action=None if passed else ViolationAction.IMMEDIATE_ALERT_AND_STOP,
        )

    def check_goal_alignment(
        self,
        goals: list[dict[str, Any]],
        authorized_sources: list[str],
    ) -> InvariantCheckResult:
        """INV-5: Check all goals trace to authorized sources.

        Verifies that every active goal's provenance chain leads
        back to an authorized principal or delegator.

        Each goal dict should have:
        - ``"id"``: str identifier
        - ``"source"``: str source of the goal

        Args:
            goals: List of active goal dictionaries
            authorized_sources: List of authorized goal sources

        Returns:
            InvariantCheckResult indicating pass/fail
        """
        unauthorized: list[str] = []
        for goal in goals:
            if goal.get("source") not in authorized_sources:
                unauthorized.append(goal.get("id", "unknown"))

        passed = len(unauthorized) == 0
        return InvariantCheckResult(
            invariant_id=InvariantID.GOAL_ALIGNMENT,
            passed=passed,
            details=(
                f"All {len(goals)} goals trace to authorized sources"
                if passed
                else f"{len(unauthorized)} goal(s) from unauthorized sources"
            ),
            evidence={
                "total_goals": len(goals),
                "unauthorized_goals": unauthorized,
                "authorized_sources": authorized_sources,
            },
            recommended_action=None if passed else ViolationAction.SUSPEND_AND_REPORT,
        )

    def check_all(self, context: dict[str, Any]) -> list[InvariantCheckResult]:
        """Run all applicable invariant checks on a context.

        Dispatches to individual check methods based on which keys
        are present in the context dictionary.

        Context keys (all optional -- only runs checks for present keys):
        - ``"source_trust"`` + ``"required_trust"``: triggers INV-1
        - ``"delegated_permission"`` + ``"delegator_permission"``: triggers INV-2
        - ``"beliefs"``: triggers INV-3
        - ``"initial_canaries"`` + ``"current_canaries"``: triggers INV-4
        - ``"goals"`` + ``"authorized_sources"``: triggers INV-5

        Args:
            context: Dictionary with check parameters

        Returns:
            List of InvariantCheckResult for all applicable checks
        """
        results: list[InvariantCheckResult] = []

        if "source_trust" in context and "required_trust" in context:
            results.append(
                self.check_source_verification(context["source_trust"], context["required_trust"])
            )

        if "delegated_permission" in context and "delegator_permission" in context:
            results.append(
                self.check_delegation_bounds(
                    context["delegated_permission"], context["delegator_permission"]
                )
            )

        if "beliefs" in context:
            results.append(
                self.check_belief_consistency(
                    context["beliefs"],
                    context.get("confidence_threshold", 0.7),
                )
            )

        if "initial_canaries" in context and "current_canaries" in context:
            results.append(
                self.check_identity_integrity(
                    context["initial_canaries"], context["current_canaries"]
                )
            )

        if "goals" in context and "authorized_sources" in context:
            results.append(
                self.check_goal_alignment(context["goals"], context["authorized_sources"])
            )

        return results


# =============================================================================
# Self-Monitoring Protocols
# =============================================================================


class BeliefDriftMonitor:
    """Monitors belief distribution drift using KL-divergence.

    Implements the belief drift monitoring protocol from Section 04.
    After every external input, computes KL-divergence between the
    current belief confidence distribution and the session baseline.

    The KL-divergence D_KL(P || Q) measures how much distribution P
    (current) diverges from reference distribution Q (baseline).
    Values near 0 indicate minimal drift; values above the threshold
    trigger a flag.

    Example::

        monitor = BeliefDriftMonitor(threshold=0.5)
        monitor.set_baseline([0.9, 0.8, 0.7])
        result = monitor.check_drift([0.9, 0.8, 0.7])
        assert not result["flagged"]
    """

    def __init__(self, threshold: float = 0.5) -> None:
        """Initialize drift monitor.

        Args:
            threshold: KL-divergence threshold for flagging (default 0.5)
        """
        self.threshold = threshold
        self.baseline: list[float] | None = None
        self.drift_history: list[float] = []

    def set_baseline(self, confidences: list[float]) -> None:
        """Set baseline belief confidence distribution.

        Should be called at session start with the initial confidence
        values for all tracked beliefs.

        Args:
            confidences: List of confidence values (0-1) for all beliefs

        Raises:
            ValueError: If confidences is empty
        """
        if not confidences:
            raise ValueError("Confidences list cannot be empty")
        self.baseline = list(confidences)

    @staticmethod
    def _kl_divergence(p: list[float], q: list[float], epsilon: float = 1e-10) -> float:
        """Compute KL-divergence D_KL(P || Q).

        Both distributions are normalized to sum to 1 before
        computation. A small epsilon is added to avoid log(0).

        Args:
            p: Distribution P (current)
            q: Distribution Q (baseline)
            epsilon: Small value to avoid log(0)

        Returns:
            KL-divergence value (non-negative float)
        """
        p_arr = np.array(p, dtype=np.float64) + epsilon
        q_arr = np.array(q, dtype=np.float64) + epsilon

        # Normalize to proper probability distributions
        p_arr = p_arr / p_arr.sum()
        q_arr = q_arr / q_arr.sum()

        return float(np.sum(p_arr * np.log(p_arr / q_arr)))

    def check_drift(self, current_confidences: list[float]) -> dict[str, Any]:
        """Check belief drift against baseline.

        Computes KL-divergence between current confidence values and
        the baseline, appends to drift history, and returns analysis.

        Args:
            current_confidences: Current belief confidence values

        Returns:
            Dictionary with:
            - ``"kl_divergence"``: float -- computed divergence
            - ``"flagged"``: bool -- whether threshold exceeded
            - ``"threshold"``: float -- current threshold
            - ``"drift_trend"``: list of up to 10 recent KL values

        Raises:
            ValueError: If baseline not set or lengths mismatch
        """
        if self.baseline is None:
            raise ValueError("Baseline not set. Call set_baseline() first.")
        if len(current_confidences) != len(self.baseline):
            raise ValueError(
                f"Confidence count mismatch: {len(current_confidences)} vs "
                f"baseline {len(self.baseline)}"
            )

        kl = self._kl_divergence(current_confidences, self.baseline)
        self.drift_history.append(kl)

        return {
            "kl_divergence": kl,
            "flagged": kl > self.threshold,
            "threshold": self.threshold,
            "drift_trend": list(self.drift_history[-10:]),
        }


class TrustAnomalyMonitor:
    """Monitors for trust anomalies in inter-agent communication.

    Implements the trust anomaly monitoring protocol from Section 04.
    On every inter-agent communication, this monitor:
    1. Verifies identity (via recorded trust history)
    2. Checks trust vs importance for mismatches
    3. Flags unusual patterns (rapid trust changes)

    Detects:
    - Rapid trust changes between consecutive observations
    - Trust/importance mismatches (low-trust agent sending
      high-importance messages)
    """

    def __init__(
        self,
        rapid_change_threshold: float = 0.3,
        mismatch_threshold: float = 0.5,
    ) -> None:
        """Initialize trust anomaly monitor.

        Args:
            rapid_change_threshold: Max allowable trust change between
                consecutive observations before flagging
            mismatch_threshold: Max allowable difference between
                message importance and sender trust
        """
        self.rapid_change_threshold = rapid_change_threshold
        self.mismatch_threshold = mismatch_threshold
        self.trust_history: dict[str, list[float]] = {}

    def record_trust(self, agent_id: str, trust_score: float) -> None:
        """Record a trust score observation for an agent.

        Args:
            agent_id: Agent identifier
            trust_score: Current trust score (0-1)
        """
        if agent_id not in self.trust_history:
            self.trust_history[agent_id] = []
        self.trust_history[agent_id].append(trust_score)

    def check_rapid_change(self, agent_id: str) -> dict[str, Any]:
        """Check for rapid trust changes for an agent.

        Compares the two most recent trust observations. If the
        absolute change exceeds ``rapid_change_threshold``, the
        result is flagged.

        Args:
            agent_id: Agent to check

        Returns:
            Dict with:
            - ``"flagged"``: bool
            - ``"change"``: float (absolute change, 0.0 if < 2 observations)
            - ``"agent_id"``: str
            - ``"previous"``: float (if available)
            - ``"current"``: float (if available)
        """
        history = self.trust_history.get(agent_id, [])
        if len(history) < 2:
            return {"flagged": False, "change": 0.0, "agent_id": agent_id}

        change = abs(history[-1] - history[-2])
        return {
            "flagged": change > self.rapid_change_threshold,
            "change": change,
            "previous": history[-2],
            "current": history[-1],
            "agent_id": agent_id,
        }

    def check_trust_importance_mismatch(
        self,
        agent_id: str,
        trust_score: float,
        message_importance: float,
    ) -> dict[str, Any]:
        """Check if message importance exceeds sender trust.

        A low-trust agent sending high-importance messages is anomalous
        and may indicate attempted social engineering or compromise.

        Args:
            agent_id: Sending agent identifier
            trust_score: Sender's trust score (0-1)
            message_importance: Message importance level (0-1)

        Returns:
            Dict with:
            - ``"flagged"``: bool
            - ``"mismatch"``: float (importance - trust)
            - ``"trust_score"``: float
            - ``"message_importance"``: float
            - ``"agent_id"``: str
        """
        mismatch = message_importance - trust_score
        return {
            "flagged": mismatch > self.mismatch_threshold,
            "mismatch": mismatch,
            "trust_score": trust_score,
            "message_importance": message_importance,
            "agent_id": agent_id,
        }


class CoordinationIntegrityMonitor:
    """Monitors coordination integrity for multi-agent decisions.

    Implements the coordination integrity protocol from Section 04.
    Before any multi-agent decision, this monitor:
    1. Verifies quorum is met
    2. Checks voting patterns for anomalies
    3. Validates consensus legitimacy

    Detects:
    - Quorum violations (insufficient participation)
    - Suspicious voting patterns (simultaneous + identical votes)
    """

    def __init__(self, min_quorum: int = 3) -> None:
        """Initialize coordination monitor.

        Args:
            min_quorum: Minimum number of agents required for a valid
                quorum in multi-agent decisions
        """
        self.min_quorum = min_quorum

    def verify_quorum(
        self,
        total_agents: int,
        participating_agents: int,
    ) -> dict[str, Any]:
        """Verify quorum is met for a decision.

        Args:
            total_agents: Total agents in the system
            participating_agents: Agents participating in the decision

        Returns:
            Dict with:
            - ``"quorum_met"``: bool
            - ``"participating"``: int
            - ``"required"``: int
            - ``"total"``: int
            - ``"participation_rate"``: float (0-1)
        """
        quorum_met = participating_agents >= self.min_quorum
        participation_rate = participating_agents / total_agents if total_agents > 0 else 0.0
        return {
            "quorum_met": quorum_met,
            "participating": participating_agents,
            "required": self.min_quorum,
            "total": total_agents,
            "participation_rate": participation_rate,
        }

    def check_voting_patterns(
        self,
        votes: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Check for suspicious voting patterns.

        Detects two anomaly types:
        - **Simultaneous**: All votes arrive within 1 second
        - **Identical**: All votes have the same value

        A vote is ``suspicious`` only when BOTH conditions hold,
        suggesting coordinated manipulation.

        Each vote dict should have:
        - ``"agent_id"``: str
        - ``"vote"``: Any (the vote value)
        - ``"timestamp"``: float (epoch seconds)

        Args:
            votes: List of vote dictionaries

        Returns:
            Dict with:
            - ``"suspicious"``: bool (both simultaneous AND identical)
            - ``"simultaneous"``: bool (all within 1 second)
            - ``"identical"``: bool (all same vote value)
            - ``"time_spread"``: float (max - min timestamp)
            - ``"unique_vote_count"``: int
            - ``"vote_count"``: int
        """
        if len(votes) < 2:
            return {
                "suspicious": False,
                "simultaneous": False,
                "identical": False,
                "vote_count": len(votes),
            }

        # Check simultaneous (all within 1 second)
        timestamps = [v.get("timestamp", 0) for v in votes]
        time_spread = max(timestamps) - min(timestamps)
        simultaneous = time_spread < 1.0

        # Check identical votes
        vote_values = [str(v.get("vote", "")) for v in votes]
        unique_votes = set(vote_values)
        identical = len(unique_votes) == 1 and len(votes) > 1

        suspicious = simultaneous and identical

        return {
            "suspicious": suspicious,
            "simultaneous": simultaneous,
            "identical": identical,
            "time_spread": time_spread,
            "unique_vote_count": len(unique_votes),
            "vote_count": len(votes),
        }


# =============================================================================
# Response Protocols
# =============================================================================


@dataclass
class ResponseStep:
    """A single step in a response protocol.

    Steps are ordered sequentially and tracked for completion
    as the protocol is executed.

    Args:
        order: Step sequence number (1-based)
        action: Description of the action to take
        completed: Whether this step has been executed
    """

    order: int
    action: str
    completed: bool = False


@dataclass
class ResponseProtocol:
    """Response protocol for a threat level.

    Encapsulates the ordered set of actions to take when a
    specific threat level is detected. Supports progress tracking
    and sequential step execution.

    Args:
        threat_level: The threat level this protocol responds to
        name: Human-readable protocol name
        steps: Ordered list of response steps
    """

    threat_level: ThreatLevel
    name: str
    steps: list[ResponseStep] = field(default_factory=list)

    def next_step(self) -> ResponseStep | None:
        """Get the next incomplete step.

        Returns:
            Next incomplete ResponseStep, or None if all complete
        """
        for step in self.steps:
            if not step.completed:
                return step
        return None

    def progress(self) -> float:
        """Calculate protocol progress as a fraction.

        Returns:
            Float between 0.0 (no steps complete) and 1.0 (all complete).
            Returns 1.0 if the protocol has no steps.
        """
        if not self.steps:
            return 1.0
        return sum(1 for s in self.steps if s.completed) / len(self.steps)


def get_response_protocols() -> dict[ThreatLevel, ResponseProtocol]:
    """Get all response protocols from manuscript Section 04.

    Returns three protocols, one per threat level:
    - Suspicious Input: classify, quarantine/reject/accept-with-flag
    - Potential Compromise: preserve state, notify, scrutinize, review
    - Confirmed Attack: cease, alert, await, forensics

    Returns:
        Dictionary mapping threat levels to their response protocols
    """
    return {
        ThreatLevel.SUSPICIOUS_INPUT: ResponseProtocol(
            threat_level=ThreatLevel.SUSPICIOUS_INPUT,
            name="Suspicious Input Protocol",
            steps=[
                ResponseStep(1, "Classify input through cognitive firewall"),
                ResponseStep(2, "If QUARANTINE: Hold pending corroboration"),
                ResponseStep(3, "If REJECT: Log and discard"),
                ResponseStep(4, "If ACCEPT with concerns: Flag for human review"),
            ],
        ),
        ThreatLevel.POTENTIAL_COMPROMISE: ResponseProtocol(
            threat_level=ThreatLevel.POTENTIAL_COMPROMISE,
            name="Potential Compromise Protocol",
            steps=[
                ResponseStep(1, "Preserve current state for analysis"),
                ResponseStep(2, "Notify other agents of potential compromise"),
                ResponseStep(3, "Increase scrutiny on own outputs"),
                ResponseStep(4, "Request operator review before high-impact actions"),
            ],
        ),
        ThreatLevel.CONFIRMED_ATTACK: ResponseProtocol(
            threat_level=ThreatLevel.CONFIRMED_ATTACK,
            name="Confirmed Attack Protocol",
            steps=[
                ResponseStep(1, "Cease processing external inputs"),
                ResponseStep(2, "Alert entire agent network"),
                ResponseStep(3, "Await operator instructions"),
                ResponseStep(4, "Prepare state for forensic analysis"),
            ],
        ),
    }


# =============================================================================
# YAML Rule Generation
# =============================================================================


def generate_yaml_rules() -> str:
    """Generate machine-readable YAML rules from manuscript Section 04.

    Produces a YAML-formatted string containing:
    - All 5 security invariants with their check predicates and
      violation actions
    - All 3 monitoring protocol types with trigger frequencies

    The output is intended for consumption by agent frameworks
    that parse YAML configuration for security rule enforcement.

    Returns:
        YAML string containing cognitive security rules
    """
    lines = [
        "cognitive_security_rules:",
        "  invariants:",
    ]

    checker = SecurityInvariantChecker()
    for inv_id, defn in checker.definitions.items():
        lines.extend(
            [
                f"    - id: {inv_id.value}",
                f"      name: {defn.name.lower().replace(' ', '_')}",
                f"      check: {defn.check_description}",
                f"      violation_action: {defn.violation_action.value}",
            ]
        )

    lines.extend(
        [
            "  monitoring:",
            "    - type: belief_drift",
            "      frequency: on_external_input",
            "    - type: trust_anomaly",
            "      frequency: on_agent_communication",
            "    - type: coordination_integrity",
            "      frequency: before_multi_agent_decision",
        ]
    )

    return "\n".join(lines)


__all__ = [
    "InvariantID",
    "ViolationAction",
    "MonitorType",
    "ThreatLevel",
    "InvariantDefinition",
    "InvariantCheckResult",
    "SecurityInvariantChecker",
    "BeliefDriftMonitor",
    "TrustAnomalyMonitor",
    "CoordinationIntegrityMonitor",
    "ResponseStep",
    "ResponseProtocol",
    "get_response_protocols",
    "generate_yaml_rules",
]
