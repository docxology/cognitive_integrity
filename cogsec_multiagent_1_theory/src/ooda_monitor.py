"""
OODA Phase Monitor for CIF v2.0

Monitors agent OODA (Observe-Orient-Decide-Act) loop phases, detects phase-level
cognitive attacks, and integrates with CIF defense mechanisms.

Added in Second Edition (v2.0) as part of CIF-OODA integration (§4 of manuscript).
"""

from __future__ import annotations

import math
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np


class OODAPhase(Enum):
    """OODA loop phases as a finite state machine."""

    OBSERVE = auto()
    ORIENT = auto()
    DECIDE = auto()
    ACT = auto()


class OODAPhaseAttack(Enum):
    """Detected attack types by OODA phase."""

    SENSOR_SPOOFING = "sensor_spoofing"  # Observe phase
    TOOL_INJECTION = "tool_injection"  # Observe phase
    BELIEF_INJECTION = "belief_injection"  # Orient phase
    SEMANTIC_DRIFT = "semantic_drift"  # Orient phase
    GOAL_HIJACKING = "goal_hijacking"  # Decide phase
    CONSTRAINT_REMOVAL = "constraint_removal"  # Decide phase
    PERMISSION_ESCALATION = "permission_escalation"  # Act phase
    SIDE_EFFECT_ABUSE = "side_effect_abuse"  # Act phase


@dataclass
class OODAEvent:
    """An event in the OODA loop with associated security metadata."""

    phase: OODAPhase
    timestamp: float
    agent_id: str
    payload: Any
    trust_score: float = 1.0
    provenance_verified: bool = True
    source: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OODAAlert:
    """Security alert raised during OODA monitoring."""

    phase: OODAPhase
    attack_type: OODAPhaseAttack
    agent_id: str
    timestamp: float
    severity: float  # 0–1, higher is more severe
    evidence: Dict[str, Any] = field(default_factory=dict)
    description: str = ""


@dataclass
class OODACycleStats:
    """Statistics for a completed OODA cycle."""

    agent_id: str
    cycle_id: int
    start_time: float
    end_time: float
    phase_durations: Dict[str, float]
    events_by_phase: Dict[str, int]
    alerts: List[OODAAlert]
    integrity_preserved: bool

    @property
    def cycle_duration(self) -> float:
        """Total OODA cycle duration in seconds."""
        return self.end_time - self.start_time

    @property
    def alert_count(self) -> int:
        return len(self.alerts)


class OODAPhaseMonitor:
    """
    Real-time OODA phase monitor with CIF integration.

    Monitors an agent's OODA loop for phase-level cognitive attacks.
    Integrates with the Cognitive Firewall, Belief Sandbox, and Invariant
    Checker for per-phase defense coverage.

    Reference: CIF v2.0, §4 (CIF-OODA Integration), Table 4 (OODA phase attacks).
    """

    # Phase transition graph (valid next phases from each phase)
    PHASE_TRANSITIONS: Dict[OODAPhase, List[OODAPhase]] = {
        OODAPhase.OBSERVE: [OODAPhase.ORIENT],
        OODAPhase.ORIENT: [OODAPhase.DECIDE],
        OODAPhase.DECIDE: [OODAPhase.ACT],
        OODAPhase.ACT: [OODAPhase.OBSERVE],  # Cycle back
    }

    # Maximum tolerable CIF overhead fraction (ε_OODA)
    MAX_OVERHEAD_FRACTION: float = 0.10

    def __init__(
        self,
        agent_id: str,
        trust_threshold: float = 0.5,
        drift_threshold: float = 0.3,
        belief_history_window: int = 10,
        alert_callback: Optional[Callable[[OODAAlert], None]] = None,
    ) -> None:
        """
        Initialize OODA phase monitor.

        Args:
            agent_id: Identifier of the monitored agent.
            trust_threshold: Minimum trust score for non-sandboxed processing.
            drift_threshold: KL divergence threshold triggering drift alert.
            belief_history_window: Window size for belief drift computation.
            alert_callback: Optional callback invoked on alert generation.
        """
        self.agent_id = agent_id
        self.trust_threshold = trust_threshold
        self.drift_threshold = drift_threshold
        self.belief_history_window = belief_history_window
        self.alert_callback = alert_callback

        self._current_phase: OODAPhase = OODAPhase.OBSERVE
        self._phase_start_time: float = time.monotonic()
        self._cycle_id: int = 0
        self._cycle_start_time: float = time.monotonic()

        # History buffers
        self._belief_history: deque = deque(maxlen=belief_history_window)
        self._events_this_cycle: Dict[OODAPhase, List[OODAEvent]] = {p: [] for p in OODAPhase}
        self._alerts_this_cycle: List[OODAAlert] = []
        self._completed_cycles: List[OODACycleStats] = []
        self._phase_durations_this_cycle: Dict[str, float] = {}

        # Cumulative KL tracking (CUSUM)
        self._cusum_stat: float = 0.0
        self._cusum_allowance: float = drift_threshold / 2.0  # Wald's optimal
        self._cusum_threshold: float = 4.6  # For ARL0 ~ 1000

    def transition_phase(self, new_phase: OODAPhase) -> bool:
        """
        Transition OODA state machine to a new phase.

        Args:
            new_phase: Target phase.

        Returns:
            True if transition is valid; False if it violates the OODA order.
        """
        valid_next = self.PHASE_TRANSITIONS[self._current_phase]
        if new_phase not in valid_next:
            self._raise_alert(
                OODAPhaseAttack.SIDE_EFFECT_ABUSE,
                self._current_phase,
                severity=0.7,
                evidence={
                    "attempted_transition": f"{self._current_phase} -> {new_phase}",
                    "valid_transitions": [p.name for p in valid_next],
                },
                description=(
                    f"Invalid OODA phase transition: {self._current_phase.name} -> {new_phase.name}"
                ),
            )
            return False

        # Record phase duration
        now = time.monotonic()
        elapsed = now - self._phase_start_time
        self._phase_durations_this_cycle[self._current_phase.name] = elapsed

        # If we completed a full cycle (transitioning back to OBSERVE)
        if new_phase == OODAPhase.OBSERVE and self._current_phase == OODAPhase.ACT:
            self._finalize_cycle(now)

        self._current_phase = new_phase
        self._phase_start_time = now
        return True

    def observe(self, event: OODAEvent) -> Optional[OODAAlert]:
        """
        Process an Observe-phase event: sensor reading or tool output.

        Checks for sensor spoofing (low trust, unverified provenance) and
        tool injection (adversarial content in tool responses).

        Args:
            event: OODA event in the Observe phase.

        Returns:
            Alert if attack detected; None otherwise.
        """
        if self._current_phase != OODAPhase.OBSERVE:
            self.transition_phase(OODAPhase.OBSERVE)

        self._events_this_cycle[OODAPhase.OBSERVE].append(event)

        # Check 1: Sensor spoofing (low trust + unverified)
        if event.trust_score < self.trust_threshold and not event.provenance_verified:
            return self._raise_alert(
                OODAPhaseAttack.SENSOR_SPOOFING,
                OODAPhase.OBSERVE,
                severity=0.6 * (1.0 - event.trust_score),
                evidence={
                    "trust_score": event.trust_score,
                    "provenance_verified": event.provenance_verified,
                    "source": event.source,
                },
                description="Low-trust, unverified sensor input detected",
            )

        # Check 2: Tool injection pattern (check metadata for injection markers)
        if event.metadata.get("has_injection_marker", False):
            return self._raise_alert(
                OODAPhaseAttack.TOOL_INJECTION,
                OODAPhase.OBSERVE,
                severity=0.8,
                evidence={"injection_marker": event.metadata.get("injection_marker")},
                description="Tool injection pattern detected in Observe phase",
            )

        return None

    def orient(
        self,
        current_beliefs: np.ndarray,
        previous_beliefs: Optional[np.ndarray] = None,
        event: Optional[OODAEvent] = None,
    ) -> Optional[OODAAlert]:
        """
        Process an Orient-phase event: belief update.

        Detects belief injection (sudden belief state change) and semantic drift
        (gradual distribution shift above KL threshold).

        Args:
            current_beliefs: Current belief distribution (probability vector).
            previous_beliefs: Previous belief distribution for drift detection.
            event: Optional OODA event associated with this orientation.

        Returns:
            Alert if attack detected; None otherwise.
        """
        if self._current_phase != OODAPhase.ORIENT:
            self.transition_phase(OODAPhase.ORIENT)

        if event:
            self._events_this_cycle[OODAPhase.ORIENT].append(event)

        # Normalize beliefs
        beliefs_norm = np.asarray(current_beliefs, dtype=float)
        total = beliefs_norm.sum()
        if total > 0:
            beliefs_norm /= total
        else:
            beliefs_norm = np.ones(len(beliefs_norm)) / len(beliefs_norm)

        # Check for belief injection: sudden large change
        if previous_beliefs is not None:
            prev_norm = np.asarray(previous_beliefs, dtype=float)
            prev_sum = prev_norm.sum()
            if prev_sum > 0:
                prev_norm /= prev_sum

            kl_div = self._kl_divergence(beliefs_norm, prev_norm)

            # CUSUM update
            self._cusum_stat = max(0.0, self._cusum_stat + kl_div - self._cusum_allowance)

            if kl_div > self.drift_threshold:
                return self._raise_alert(
                    OODAPhaseAttack.BELIEF_INJECTION,
                    OODAPhase.ORIENT,
                    severity=min(1.0, kl_div / (2 * self.drift_threshold)),
                    evidence={
                        "kl_divergence": kl_div,
                        "threshold": self.drift_threshold,
                        "cusum_stat": self._cusum_stat,
                    },
                    description=(
                        f"Belief injection: KL={kl_div:.3f} "
                        f"exceeds threshold {self.drift_threshold}"
                    ),
                )

            # CUSUM drift detection (slower gradual drift)
            if self._cusum_stat > self._cusum_threshold:
                return self._raise_alert(
                    OODAPhaseAttack.SEMANTIC_DRIFT,
                    OODAPhase.ORIENT,
                    severity=min(1.0, self._cusum_stat / (2 * self._cusum_threshold)),
                    evidence={
                        "cusum_stat": self._cusum_stat,
                        "cusum_threshold": self._cusum_threshold,
                        "recent_kl": kl_div,
                    },
                    description=(
                        f"Semantic drift: CUSUM={self._cusum_stat:.3f} "
                        f"exceeds threshold {self._cusum_threshold}"
                    ),
                )

        # Record belief in history
        self._belief_history.append(beliefs_norm.copy())
        return None

    def decide(
        self,
        goals: List[str],
        principal_goals: List[str],
        constraints: List[str],
        event: Optional[OODAEvent] = None,
    ) -> Optional[OODAAlert]:
        """
        Process a Decide-phase event: goal selection and intention formation.

        Detects goal hijacking (agent goal not in principal goal set) and
        constraint removal (legitimate constraints disappearing).

        Args:
            goals: Current agent goal set.
            principal_goals: Authorized goals from the principal.
            constraints: Active constraints on agent actions.
            event: Optional OODA event.

        Returns:
            Alert if attack detected; None otherwise.
        """
        if self._current_phase != OODAPhase.DECIDE:
            self.transition_phase(OODAPhase.DECIDE)

        if event:
            self._events_this_cycle[OODAPhase.DECIDE].append(event)

        goals_set = set(goals)
        principal_set = set(principal_goals)

        # Check goal alignment: G_i ⊆ G_principal (Property 4.2 in manuscript)
        unauthorized_goals = goals_set - principal_set
        if unauthorized_goals:
            return self._raise_alert(
                OODAPhaseAttack.GOAL_HIJACKING,
                OODAPhase.DECIDE,
                severity=min(1.0, len(unauthorized_goals) / max(1, len(goals_set))),
                evidence={
                    "unauthorized_goals": list(unauthorized_goals),
                    "principal_goals": list(principal_set),
                },
                description=(
                    f"Goal hijacking: {len(unauthorized_goals)} unauthorized goal(s) detected"
                ),
            )

        # Constraint removal detection (simplified: check if expected constraints present)
        if not constraints:
            return self._raise_alert(
                OODAPhaseAttack.CONSTRAINT_REMOVAL,
                OODAPhase.DECIDE,
                severity=0.7,
                evidence={"expected_constraints": "non-empty", "actual": "empty"},
                description="Constraint removal: no active constraints in Decide phase",
            )

        return None

    def act(
        self,
        action: str,
        authorized_actions: List[str],
        expected_side_effects: Optional[List[str]] = None,
        actual_side_effects: Optional[List[str]] = None,
        event: Optional[OODAEvent] = None,
    ) -> Optional[OODAAlert]:
        """
        Process an Act-phase event: action execution.

        Detects permission escalation (unauthorized action) and side-effect abuse
        (unexpected side effects from actions).

        Args:
            action: Proposed or executed action.
            authorized_actions: List of permitted actions.
            expected_side_effects: Expected side effects of the action.
            actual_side_effects: Observed side effects.
            event: Optional OODA event.

        Returns:
            Alert if attack detected; None otherwise.
        """
        if self._current_phase != OODAPhase.ACT:
            self.transition_phase(OODAPhase.ACT)

        if event:
            self._events_this_cycle[OODAPhase.ACT].append(event)

        # Check permission escalation
        if action not in authorized_actions:
            return self._raise_alert(
                OODAPhaseAttack.PERMISSION_ESCALATION,
                OODAPhase.ACT,
                severity=0.9,
                evidence={
                    "attempted_action": action,
                    "authorized_actions": authorized_actions[:10],  # truncate for safety
                },
                description=f"Permission escalation: action '{action}' not authorized",
            )

        # Check side-effect abuse
        if expected_side_effects is not None and actual_side_effects is not None:
            unexpected = set(actual_side_effects) - set(expected_side_effects)
            if unexpected:
                return self._raise_alert(
                    OODAPhaseAttack.SIDE_EFFECT_ABUSE,
                    OODAPhase.ACT,
                    severity=min(1.0, len(unexpected) / max(1, len(actual_side_effects))),
                    evidence={
                        "unexpected_side_effects": list(unexpected),
                        "expected": expected_side_effects,
                    },
                    description=f"Side-effect abuse: {len(unexpected)} unexpected side effect(s)",
                )

        return None

    def get_cycle_stats(self) -> List[OODACycleStats]:
        """Return statistics for all completed OODA cycles."""
        return list(self._completed_cycles)

    def get_current_phase(self) -> OODAPhase:
        """Return current OODA phase."""
        return self._current_phase

    def get_alert_history(self) -> List[OODAAlert]:
        """Return all alerts from the current cycle."""
        return list(self._alerts_this_cycle)

    def reset_cusum(self) -> None:
        """Reset CUSUM statistic (e.g., after verified system reset)."""
        self._cusum_stat = 0.0

    def cif_overhead_fraction(self, ooda_cycle_duration: float) -> float:
        """
        Compute the fraction of OODA cycle time consumed by CIF monitoring.

        Args:
            ooda_cycle_duration: Total OODA cycle duration in seconds.

        Returns:
            Overhead fraction in [0, 1].
        """
        if ooda_cycle_duration <= 0:
            return 0.0
        # CIF monitoring overhead (total detection latency = ~141ms from defense stack)
        cif_latency_s = 0.141  # 141ms default stack
        return min(1.0, cif_latency_s / ooda_cycle_duration)

    def check_latency_budget(self, ooda_cycle_duration: float) -> bool:
        """
        Check whether the OODA cycle is long enough for full CIF monitoring.

        Args:
            ooda_cycle_duration: Total OODA cycle duration in seconds.

        Returns:
            True if full CIF monitoring fits within budget (ε_OODA < 0.10).
        """
        return self.cif_overhead_fraction(ooda_cycle_duration) <= self.MAX_OVERHEAD_FRACTION

    # --- Private helpers ---

    def _raise_alert(
        self,
        attack_type: OODAPhaseAttack,
        phase: OODAPhase,
        severity: float,
        evidence: Dict[str, Any],
        description: str,
    ) -> OODAAlert:
        alert = OODAAlert(
            phase=phase,
            attack_type=attack_type,
            agent_id=self.agent_id,
            timestamp=time.monotonic(),
            severity=max(0.0, min(1.0, severity)),
            evidence=evidence,
            description=description,
        )
        self._alerts_this_cycle.append(alert)
        if self.alert_callback is not None:
            self.alert_callback(alert)
        return alert

    def _finalize_cycle(self, end_time: float) -> None:
        """Finalize the current OODA cycle, record stats, and reset."""
        events_by_phase = {p.name: len(self._events_this_cycle[p]) for p in OODAPhase}
        integrity = len(self._alerts_this_cycle) == 0

        stats = OODACycleStats(
            agent_id=self.agent_id,
            cycle_id=self._cycle_id,
            start_time=self._cycle_start_time,
            end_time=end_time,
            phase_durations=dict(self._phase_durations_this_cycle),
            events_by_phase=events_by_phase,
            alerts=list(self._alerts_this_cycle),
            integrity_preserved=integrity,
        )
        self._completed_cycles.append(stats)
        self._cycle_id += 1
        self._cycle_start_time = end_time
        self._events_this_cycle = {p: [] for p in OODAPhase}
        self._alerts_this_cycle = []
        self._phase_durations_this_cycle = {}

    @staticmethod
    def _kl_divergence(p: np.ndarray, q: np.ndarray, epsilon: float = 1e-10) -> float:
        """
        Compute KL(p || q) safely with epsilon smoothing.

        Args:
            p: Source distribution.
            q: Reference distribution.
            epsilon: Smoothing constant to avoid log(0).

        Returns:
            KL divergence value (non-negative).
        """
        p = np.clip(p, epsilon, 1.0)
        q = np.clip(q, epsilon, 1.0)
        p = p / p.sum()
        q = q / q.sum()
        return float(np.sum(p * np.log(p / q)))

    @staticmethod
    def fisher_rao_distance(p: np.ndarray, q: np.ndarray) -> float:
        """
        Compute Fisher-Rao geodesic distance between two distributions.

        d_FR(p, q) = 2 * arccos(sum_i sqrt(p_i * q_i))

        Reference: CIF v2.0, Supplement S01, Lemma FR.1.

        Args:
            p: First probability distribution.
            q: Second probability distribution.

        Returns:
            Fisher-Rao distance in [0, pi].
        """
        p_norm = np.clip(p, 0, None)
        q_norm = np.clip(q, 0, None)
        p_sum, q_sum = p_norm.sum(), q_norm.sum()
        if p_sum > 0:
            p_norm /= p_sum
        if q_sum > 0:
            q_norm /= q_sum

        bhattacharyya = np.sum(np.sqrt(p_norm * q_norm))
        bhattacharyya = np.clip(bhattacharyya, -1.0, 1.0)
        return float(2.0 * math.acos(bhattacharyya))

    @staticmethod
    def stealth_impact_product(belief_shift_fr: float) -> Tuple[float, float, float]:
        """
        Compute the stealth-impact pair and their product for a Fisher-Rao shift.

        From Theorem (FR Tight Bound): I_FR * S_FR <= pi/2, with equality
        when stealth is normalized as S = (pi/2) / I_FR.  Returning the raw
        product alone would be a tautology (it is always pi/2 by
        construction); returning the components lets consumers verify the
        bound against *computed* (not definitionally-normalized) values.

        Args:
            belief_shift_fr: Fisher-Rao distance of the attack.

        Returns:
            Tuple of (impact, stealth, product), where
            impact = belief_shift_fr, stealth = (pi/2) / belief_shift_fr,
            product = impact * stealth (<= pi/2 by construction).
        """
        if belief_shift_fr <= 0:
            return 0.0, 0.0, 0.0
        # Stealth normalized to [0, 1]: S = (pi/2) / r
        stealth = (math.pi / 2) / belief_shift_fr
        impact = belief_shift_fr
        return impact, stealth, impact * stealth
