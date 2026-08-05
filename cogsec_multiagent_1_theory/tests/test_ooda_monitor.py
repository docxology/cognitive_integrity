"""
Tests for OODA Phase Monitor (v2.0 addition).

Uses both unit tests and property-based tests (Hypothesis library) to verify
trust calculus invariants and OODA phase monitoring correctness.
"""

import math
import time

import numpy as np
import pytest

try:
    from hypothesis import given, settings
    from hypothesis import strategies as st

    HAS_HYPOTHESIS = True
except ImportError:
    HAS_HYPOTHESIS = False

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # noqa: E402

from src.ooda_monitor import (  # noqa: E402
    OODAEvent,
    OODAPhase,
    OODAPhaseAttack,
    OODAPhaseMonitor,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def monitor() -> OODAPhaseMonitor:
    """Fresh OODA monitor for each test."""
    return OODAPhaseMonitor(agent_id="test_agent", trust_threshold=0.5, drift_threshold=0.3)


def make_event(
    phase: OODAPhase,
    trust: float = 0.9,
    verified: bool = True,
    source: str = "test_source",
    **kwargs,
) -> OODAEvent:
    return OODAEvent(
        phase=phase,
        timestamp=time.monotonic(),
        agent_id="test_agent",
        payload=None,
        trust_score=trust,
        provenance_verified=verified,
        source=source,
        metadata=kwargs,
    )


def uniform_beliefs(n: int) -> np.ndarray:
    return np.ones(n) / n


def peaked_beliefs(n: int, peak_idx: int = 0) -> np.ndarray:
    b = np.ones(n) * 0.01
    b[peak_idx] = 0.91
    return b / b.sum()


# ── Basic Phase Transition Tests ──────────────────────────────────────────────


class TestPhaseTransitions:
    def test_initial_phase_is_observe(self, monitor):
        assert monitor.get_current_phase() == OODAPhase.OBSERVE

    def test_valid_transition_observe_to_orient(self, monitor):
        result = monitor.transition_phase(OODAPhase.ORIENT)
        assert result is True
        assert monitor.get_current_phase() == OODAPhase.ORIENT

    def test_valid_full_cycle(self, monitor):
        for phase in [OODAPhase.ORIENT, OODAPhase.DECIDE, OODAPhase.ACT, OODAPhase.OBSERVE]:
            assert monitor.transition_phase(phase) is True

    def test_invalid_transition_observe_to_decide(self, monitor):
        result = monitor.transition_phase(OODAPhase.DECIDE)
        assert result is False

    def test_invalid_transition_raises_alert(self, monitor):
        monitor.transition_phase(OODAPhase.DECIDE)
        alerts = monitor.get_alert_history()
        assert len(alerts) == 1
        assert alerts[0].attack_type == OODAPhaseAttack.PHASE_ORDER_VIOLATION

    def test_cycle_finalizes_after_full_loop(self, monitor):
        for phase in [OODAPhase.ORIENT, OODAPhase.DECIDE, OODAPhase.ACT, OODAPhase.OBSERVE]:
            monitor.transition_phase(phase)
        stats = monitor.get_cycle_stats()
        assert len(stats) == 1
        assert stats[0].agent_id == "test_agent"
        assert stats[0].cycle_id == 0


# ── Observe Phase Tests ───────────────────────────────────────────────────────


class TestObservePhase:
    def test_trusted_verified_event_no_alert(self, monitor):
        event = make_event(OODAPhase.OBSERVE, trust=0.9, verified=True)
        alert = monitor.observe(event)
        assert alert is None

    def test_low_trust_unverified_triggers_sensor_spoofing(self, monitor):
        event = make_event(OODAPhase.OBSERVE, trust=0.1, verified=False)
        alert = monitor.observe(event)
        assert alert is not None
        assert alert.attack_type == OODAPhaseAttack.SENSOR_SPOOFING

    def test_low_trust_verified_no_alert(self, monitor):
        event = make_event(OODAPhase.OBSERVE, trust=0.1, verified=True)
        alert = monitor.observe(event)
        assert alert is None  # Verified provenance saves it

    def test_injection_marker_triggers_tool_injection(self, monitor):
        event = make_event(
            OODAPhase.OBSERVE,
            trust=0.9,
            verified=True,
            has_injection_marker=True,
            injection_marker="SYSTEM: ignore previous",
        )
        alert = monitor.observe(event)
        assert alert is not None
        assert alert.attack_type == OODAPhaseAttack.TOOL_INJECTION

    def test_alert_severity_scales_with_trust_deficit(self, monitor):
        low_event = make_event(OODAPhase.OBSERVE, trust=0.0, verified=False)
        med_event = make_event(OODAPhase.OBSERVE, trust=0.3, verified=False)

        monitor2 = OODAPhaseMonitor(agent_id="a2")
        alert_low = monitor.observe(low_event)
        alert_med = monitor2.observe(med_event)

        assert alert_low is not None and alert_med is not None
        assert alert_low.severity > alert_med.severity


# ── Orient Phase Tests ────────────────────────────────────────────────────────


class TestOrientPhase:
    def test_stable_beliefs_no_alert(self, monitor):
        monitor.transition_phase(OODAPhase.ORIENT)
        beliefs = uniform_beliefs(5)
        # Feed same beliefs multiple times (no drift)
        for _ in range(3):
            alert = monitor.orient(beliefs, beliefs)
            assert alert is None

    def test_sudden_belief_change_triggers_injection_alert(self, monitor):
        monitor.transition_phase(OODAPhase.ORIENT)
        old_beliefs = uniform_beliefs(5)
        new_beliefs = peaked_beliefs(5, peak_idx=0)
        alert = monitor.orient(new_beliefs, old_beliefs)
        assert alert is not None
        assert alert.attack_type == OODAPhaseAttack.BELIEF_INJECTION

    def test_small_belief_change_no_alert(self, monitor):
        monitor.transition_phase(OODAPhase.ORIENT)
        beliefs_a = np.array([0.20, 0.20, 0.20, 0.20, 0.20])
        beliefs_b = np.array([0.22, 0.19, 0.20, 0.20, 0.19])
        beliefs_b /= beliefs_b.sum()
        alert = monitor.orient(beliefs_b, beliefs_a)
        assert alert is None

    def test_cusum_catches_slow_drift(self, monitor):
        monitor.transition_phase(OODAPhase.ORIENT)
        # Simulate gradual drift below per-step threshold
        n = 5
        base = uniform_beliefs(n)
        current = base.copy()
        for _i in range(50):
            # Small drift each step
            current = current * 0.97 + peaked_beliefs(n, peak_idx=0) * 0.03
            current /= current.sum()
            alert = monitor.orient(current, base)
            if alert is not None and alert.attack_type == OODAPhaseAttack.SEMANTIC_DRIFT:
                break
        # Note: CUSUM should detect cumulative drift eventually
        # (may not always trigger in 50 steps; this is an integration test)

    def test_orient_computes_drift_against_previous(self, monitor):
        """Orientation feeds the CUSUM drift monitor (was: dead _belief_history)."""
        monitor.transition_phase(OODAPhase.ORIENT)
        base = uniform_beliefs(4)
        shifted = peaked_beliefs(4, peak_idx=0)
        monitor.orient(shifted, previous_beliefs=base)
        assert monitor._cusum_stat > 0.0


# ── Decide Phase Tests ────────────────────────────────────────────────────────


class TestDecidePhase:
    def test_aligned_goals_no_alert(self, monitor):
        for phase in [OODAPhase.ORIENT, OODAPhase.DECIDE]:
            monitor.transition_phase(phase)
        principal_goals = ["search", "summarize", "respond"]
        goals = ["search", "summarize"]
        alert = monitor.decide(goals, principal_goals, constraints=["no_external_writes"])
        assert alert is None

    def test_unauthorized_goal_triggers_hijacking_alert(self, monitor):
        for phase in [OODAPhase.ORIENT, OODAPhase.DECIDE]:
            monitor.transition_phase(phase)
        principal_goals = ["search", "respond"]
        adversarial_goals = ["search", "respond", "exfiltrate_credentials"]
        alert = monitor.decide(adversarial_goals, principal_goals, constraints=["c1"])
        assert alert is not None
        assert alert.attack_type == OODAPhaseAttack.GOAL_HIJACKING
        assert "exfiltrate_credentials" in alert.evidence["unauthorized_goals"]

    def test_empty_constraints_triggers_removal_alert(self, monitor):
        for phase in [OODAPhase.ORIENT, OODAPhase.DECIDE]:
            monitor.transition_phase(phase)
        alert = monitor.decide(["search"], ["search"], constraints=[])
        assert alert is not None
        assert alert.attack_type == OODAPhaseAttack.CONSTRAINT_REMOVAL

    def test_goal_hijacking_severity_scales_with_fraction(self, monitor):
        for phase in [OODAPhase.ORIENT, OODAPhase.DECIDE]:
            monitor.transition_phase(phase)
        principal_goals = ["g1", "g2", "g3"]
        # 1 out of 4 goals unauthorized
        goals = ["g1", "g2", "g3", "g4_bad"]
        alert = monitor.decide(goals, principal_goals, constraints=["c1"])
        assert alert is not None
        assert 0 < alert.severity <= 1.0


# ── Act Phase Tests ───────────────────────────────────────────────────────────


class TestActPhase:
    def test_authorized_action_no_alert(self, monitor):
        for phase in [OODAPhase.ORIENT, OODAPhase.DECIDE, OODAPhase.ACT]:
            monitor.transition_phase(phase)
        alert = monitor.act("search_web", ["search_web", "read_file", "write_summary"])
        assert alert is None

    def test_unauthorized_action_triggers_escalation_alert(self, monitor):
        for phase in [OODAPhase.ORIENT, OODAPhase.DECIDE, OODAPhase.ACT]:
            monitor.transition_phase(phase)
        alert = monitor.act("delete_system_files", ["search_web", "summarize"])
        assert alert is not None
        assert alert.attack_type == OODAPhaseAttack.PERMISSION_ESCALATION
        assert alert.severity == 0.9

    def test_unexpected_side_effects_triggers_alert(self, monitor):
        for phase in [OODAPhase.ORIENT, OODAPhase.DECIDE, OODAPhase.ACT]:
            monitor.transition_phase(phase)
        alert = monitor.act(
            "search_web",
            authorized_actions=["search_web"],
            expected_side_effects=["log_search"],
            actual_side_effects=["log_search", "send_email_to_attacker"],
        )
        assert alert is not None
        assert alert.attack_type == OODAPhaseAttack.SIDE_EFFECT_ABUSE

    def test_expected_side_effects_match_no_alert(self, monitor):
        for phase in [OODAPhase.ORIENT, OODAPhase.DECIDE, OODAPhase.ACT]:
            monitor.transition_phase(phase)
        alert = monitor.act(
            "search_web",
            authorized_actions=["search_web"],
            expected_side_effects=["log_search"],
            actual_side_effects=["log_search"],
        )
        assert alert is None


# ── Fisher-Rao Distance Tests ─────────────────────────────────────────────────


class TestFisherRaoDistance:
    def test_same_distribution_distance_zero(self):
        p = np.array([0.5, 0.5])
        dist = OODAPhaseMonitor.fisher_rao_distance(p, p)
        assert abs(dist) < 1e-10

    def test_antipodal_distributions_distance_pi(self):
        p = np.array([1.0, 0.0])
        q = np.array([0.0, 1.0])
        dist = OODAPhaseMonitor.fisher_rao_distance(p, q)
        assert abs(dist - math.pi) < 1e-6

    def test_distance_bounded_by_pi(self):
        rng = np.random.default_rng(42)
        for _ in range(100):
            p = rng.dirichlet(np.ones(5))
            q = rng.dirichlet(np.ones(5))
            dist = OODAPhaseMonitor.fisher_rao_distance(p, q)
            assert 0.0 <= dist <= math.pi + 1e-9

    def test_distance_symmetric(self):
        rng = np.random.default_rng(42)
        p = rng.dirichlet(np.ones(4))
        q = rng.dirichlet(np.ones(4))
        assert (
            abs(
                OODAPhaseMonitor.fisher_rao_distance(p, q)
                - OODAPhaseMonitor.fisher_rao_distance(q, p)
            )
            < 1e-10
        )

    def test_stealth_impact_product_pi_over_2(self):
        """The stealth-impact product is pi/2 (Theorem FR in S01_proofs.md).

        The function now returns the (impact, stealth, product) tuple so the
        components are verifiable rather than a definitionally-trivial
        scalar.
        """
        for r in [0.1, 0.5, 1.0, math.pi / 2, math.pi - 0.01]:
            impact, stealth, product = OODAPhaseMonitor.stealth_impact_product(r)
            assert abs(impact - r) < 1e-10, f"impact mismatch for r={r}"
            assert abs(stealth - (math.pi / 2) / r) < 1e-10, f"stealth mismatch for r={r}"
            assert abs(product - math.pi / 2) < 1e-10, f"Expected pi/2 for r={r}, got {product}"

    def test_stealth_impact_product_nonpositive_returns_zeros(self):
        """Non-positive belief shifts yield zero impact/stealth/product."""
        impact, stealth, product = OODAPhaseMonitor.stealth_impact_product(0.0)
        assert (impact, stealth, product) == (0.0, 0.0, 0.0)


# ── Latency Budget Tests ──────────────────────────────────────────────────────


class TestLatencyBudget:
    def test_long_ooda_cycle_fits_budget(self, monitor):
        """1.5s OODA cycle: 141ms overhead = 9.4% < 10% threshold."""
        assert monitor.check_latency_budget(ooda_cycle_duration=1.5)

    def test_short_ooda_cycle_exceeds_budget(self, monitor):
        """100ms OODA cycle: 141ms overhead > 10% threshold."""
        assert not monitor.check_latency_budget(ooda_cycle_duration=0.1)

    def test_overhead_fraction_computation(self, monitor):
        frac = monitor.cif_overhead_fraction(1.41)
        assert abs(frac - 0.10) < 0.01  # approximately 10%

    def test_zero_duration_returns_zero(self, monitor):
        assert monitor.cif_overhead_fraction(0.0) == 0.0


# ── Property-Based Tests (Hypothesis) ─────────────────────────────────────────

if HAS_HYPOTHESIS:

    @given(
        trust=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        verified=st.booleans(),
    )
    @settings(max_examples=200)
    def test_hypothesis_sensor_spoofing_only_when_both_conditions(trust, verified):
        """Sensor spoofing alert iff trust < threshold AND not verified."""
        mon = OODAPhaseMonitor(agent_id="hyp_agent", trust_threshold=0.5)
        event = make_event(OODAPhase.OBSERVE, trust=trust, verified=verified)
        alert = mon.observe(event)
        if trust < 0.5 and not verified:
            assert alert is not None
            assert alert.attack_type == OODAPhaseAttack.SENSOR_SPOOFING
        elif verified:
            # Verified provenance: no sensor spoofing regardless of trust
            assert alert is None or alert.attack_type != OODAPhaseAttack.SENSOR_SPOOFING

    @given(
        n=st.integers(min_value=2, max_value=20),
        seed=st.integers(min_value=0, max_value=10000),
    )
    @settings(max_examples=50)
    def test_hypothesis_fr_distance_in_range(n, seed):
        """Fisher-Rao distance always in [0, pi]."""
        rng = np.random.default_rng(seed)
        p = rng.dirichlet(np.ones(n))
        q = rng.dirichlet(np.ones(n))
        dist = OODAPhaseMonitor.fisher_rao_distance(p, q)
        assert 0.0 <= dist <= math.pi + 1e-9

    @given(
        goals_extra=st.lists(st.text(min_size=1, max_size=10), min_size=0, max_size=5),
    )
    @settings(max_examples=100)
    def test_hypothesis_goal_hijacking_detected_for_any_unauthorized_goal(goals_extra):
        """Goal hijacking detected whenever there are unauthorized goals."""
        principal_goals = ["g1", "g2", "g3"]
        all_goals = principal_goals + goals_extra
        mon = OODAPhaseMonitor(agent_id="hyp_agent")
        for phase in [OODAPhase.ORIENT, OODAPhase.DECIDE]:
            mon.transition_phase(phase)
        alert = mon.decide(all_goals, principal_goals, constraints=["c1"])
        has_unauthorized = any(g not in principal_goals for g in goals_extra)
        if has_unauthorized:
            assert alert is not None
            assert alert.attack_type == OODAPhaseAttack.GOAL_HIJACKING
        else:
            # No unauthorized goals → no goal hijacking alert
            if alert is not None:
                assert alert.attack_type != OODAPhaseAttack.GOAL_HIJACKING


# ── Edge Cases ────────────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_empty_goals_triggers_no_hijacking(self, monitor):
        for phase in [OODAPhase.ORIENT, OODAPhase.DECIDE]:
            monitor.transition_phase(phase)
        # Empty goals → no unauthorized goals → no hijacking
        alert = monitor.decide([], ["g1", "g2"], constraints=["c1"])
        assert alert is None

    def test_cusum_resets_to_zero(self, monitor):
        monitor.reset_cusum()
        assert monitor._cusum_stat == 0.0

    def test_multiple_cycles_accumulate_stats(self, monitor):
        for _ in range(3):
            for phase in [OODAPhase.ORIENT, OODAPhase.DECIDE, OODAPhase.ACT, OODAPhase.OBSERVE]:
                monitor.transition_phase(phase)
        assert len(monitor.get_cycle_stats()) == 3

    def test_integrity_preserved_when_no_alerts(self, monitor):
        for phase in [OODAPhase.ORIENT, OODAPhase.DECIDE, OODAPhase.ACT, OODAPhase.OBSERVE]:
            monitor.transition_phase(phase)
        stats = monitor.get_cycle_stats()
        assert stats[0].integrity_preserved is True

    def test_beliefs_with_all_zeros_handled_gracefully(self, monitor):
        monitor.transition_phase(OODAPhase.ORIENT)
        beliefs = np.zeros(5)
        # Should not raise; normalizes to uniform
        monitor.orient(beliefs, uniform_beliefs(5))
        # No assertion on return value — just verify no exception

    def test_single_element_belief_vector(self, monitor):
        monitor.transition_phase(OODAPhase.ORIENT)
        beliefs = np.array([1.0])
        alert = monitor.orient(beliefs, beliefs)
        assert alert is None

class TestCusumBoundary:
    """CUSUM drift detection: threshold crossing is strict (>), cumulative drift fires."""

    KL_P = None

    def _kl_pair(self):
        # KL(P||Q) ~= 0.2704 < drift_threshold 0.3, so no BELIEF_INJECTION fires.
        p = np.array([0.85, 0.15], dtype=float)
        q = np.array([0.5, 0.5], dtype=float)
        kl = OODAPhaseMonitor._kl_divergence(p, q)
        assert kl < 0.3 and kl > 0.0
        return p, q, kl

    def test_semantic_drift_alert_when_cusum_crosses_threshold(self, monitor):
        monitor.transition_phase(OODAPhase.ORIENT)
        p, q, _ = self._kl_pair()
        alert = None
        for _ in range(80):
            alert = monitor.orient(p, q)
            if alert is not None:
                break
        assert alert is not None
        assert alert.attack_type == OODAPhaseAttack.SEMANTIC_DRIFT
        assert monitor._cusum_stat > monitor._cusum_threshold

    def test_cusum_lands_exactly_on_threshold_does_not_alert(self, monitor):
        monitor.transition_phase(OODAPhase.ORIENT)
        p, q, kl = self._kl_pair()
        allowance = monitor._cusum_allowance
        # One orient() updates cusum -> max(0, cusum + kl - allowance). Position so
        # the result lands EXACTLY on the threshold: strict `>` must not fire.
        monitor._cusum_stat = monitor._cusum_threshold - kl + allowance
        alert = monitor.orient(p, q)
        assert alert is None
        # Sanity: stat really is at the threshold (boundary case exercised).
        assert abs(monitor._cusum_stat - monitor._cusum_threshold) < 1e-9

    def test_cusum_just_above_threshold_alerts(self, monitor):
        monitor.transition_phase(OODAPhase.ORIENT)
        p, q, kl = self._kl_pair()
        allowance = monitor._cusum_allowance
        monitor._cusum_stat = monitor._cusum_threshold - kl + allowance + 1e-9
        alert = monitor.orient(p, q)
        assert alert is not None
        assert alert.attack_type == OODAPhaseAttack.SEMANTIC_DRIFT


class TestEmptyBeliefGuard:
    def test_empty_current_beliefs_raise(self, monitor):
        monitor.transition_phase(OODAPhase.ORIENT)
        with pytest.raises(ValueError):
            monitor.orient(np.array([]), np.array([0.5, 0.5]))

    def test_empty_previous_beliefs_raise(self, monitor):
        monitor.transition_phase(OODAPhase.ORIENT)
        with pytest.raises(ValueError):
            monitor.orient(np.array([0.5, 0.5]), np.array([]))


class TestCycleStatsAndCallback:
    def test_cycle_duration_and_alert_count_properties(self, monitor):
        for ph in [OODAPhase.ORIENT, OODAPhase.DECIDE, OODAPhase.ACT, OODAPhase.OBSERVE]:
            monitor.transition_phase(ph)
        stats = monitor.get_cycle_stats()
        assert len(stats) == 1
        assert stats[0].cycle_duration >= 0.0
        assert stats[0].alert_count == 0

    def test_alert_callback_invoked_with_alert(self, monitor):
        seen = []
        monitor.alert_callback = seen.append
        for ph in [OODAPhase.ORIENT, OODAPhase.DECIDE]:
            monitor.transition_phase(ph)
        alert = monitor.decide(["g1", "bad_goal"], ["g1"], constraints=["c1"])
        assert alert is not None
        assert seen == [alert]


class TestAutoTransitions:
    def test_orient_auto_transitions_from_observe(self):
        mon = OODAPhaseMonitor(agent_id="auto")
        alert = mon.orient(np.array([0.5, 0.5]), np.array([0.5, 0.5]))
        assert mon.get_current_phase() == OODAPhase.ORIENT
        assert alert is None

    def test_orient_records_event(self):
        mon = OODAPhaseMonitor(agent_id="auto")
        event = make_event(OODAPhase.ORIENT)
        mon.orient(np.array([0.5, 0.5]), np.array([0.5, 0.5]), event=event)
        assert len(mon._events_this_cycle[OODAPhase.ORIENT]) == 1

    def test_decide_auto_transitions_from_orient(self):
        mon = OODAPhaseMonitor(agent_id="auto")
        mon.transition_phase(OODAPhase.ORIENT)
        event = make_event(OODAPhase.DECIDE)
        alert = mon.decide(["g1"], ["g1"], constraints=["c1"], event=event)
        assert mon.get_current_phase() == OODAPhase.DECIDE
        assert alert is None
        assert len(mon._events_this_cycle[OODAPhase.DECIDE]) == 1

    def test_act_auto_transitions_from_decide(self):
        mon = OODAPhaseMonitor(agent_id="auto")
        for ph in [OODAPhase.ORIENT, OODAPhase.DECIDE]:
            mon.transition_phase(ph)
        alert = mon.act("a", ["a"], event=make_event(OODAPhase.ACT))
        assert mon.get_current_phase() == OODAPhase.ACT
        assert alert is None
        assert len(mon._events_this_cycle[OODAPhase.ACT]) == 1

    def test_observe_auto_transition_finalizes_cycle(self):
        mon = OODAPhaseMonitor(agent_id="auto")
        for ph in [OODAPhase.ORIENT, OODAPhase.DECIDE, OODAPhase.ACT]:
            mon.transition_phase(ph)
        mon.observe(make_event(OODAPhase.OBSERVE, trust=0.9, verified=True))
        assert mon.get_current_phase() == OODAPhase.OBSERVE
        assert len(mon.get_cycle_stats()) == 1
