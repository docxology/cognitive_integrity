"""Tests for behavioral invariant checking."""

from datetime import datetime

from src import (
    AgentAction,
    Invariant,
    InvariantChecker,
    InvariantSeverity,
    InvariantViolation,
    RuntimeMonitor,
)


class TestInvariant:
    """Tests for Invariant dataclass."""

    def test_invariant_creation(self):
        """Invariants have predicate, description, and severity."""
        inv = Invariant(
            id="INV-TEST",
            predicate=lambda ctx: ctx.get("value", 0) > 0,
            description="Value must be positive",
            severity=InvariantSeverity.HIGH,
        )
        assert inv.id == "INV-TEST"
        assert inv.severity == InvariantSeverity.HIGH

    def test_invariant_check_passes(self):
        """Invariant check passes when predicate returns True."""
        inv = Invariant(
            id="INV-POS",
            predicate=lambda ctx: ctx.get("value", 0) > 0,
            description="Value must be positive",
            severity=InvariantSeverity.MEDIUM,
        )
        context = {"value": 5}
        assert inv.check(context) is True

    def test_invariant_check_fails(self):
        """Invariant check fails when predicate returns False."""
        inv = Invariant(
            id="INV-POS",
            predicate=lambda ctx: ctx.get("value", 0) > 0,
            description="Value must be positive",
            severity=InvariantSeverity.MEDIUM,
        )
        context = {"value": -1}
        assert inv.check(context) is False


class TestInvariantSeverity:
    """Tests for InvariantSeverity enum."""

    def test_severity_ordering(self):
        """Severities have defined ordering."""
        assert InvariantSeverity.CRITICAL.value > InvariantSeverity.HIGH.value
        assert InvariantSeverity.HIGH.value > InvariantSeverity.MEDIUM.value
        assert InvariantSeverity.MEDIUM.value > InvariantSeverity.LOW.value


class TestInvariantChecker:
    """Tests for InvariantChecker with pre-built invariants."""

    def test_builtin_inv1_untrusted_code(self):
        """INV-1: Never execute untrusted code."""
        checker = InvariantChecker()

        # Trusted code execution should pass
        context = {
            "action": "execute_code",
            "code_source": "system_verified",
            "code_trusted": True,
        }
        violations = checker.check_all(context)
        inv1_violations = [v for v in violations if v.invariant_id == "INV-1"]
        assert len(inv1_violations) == 0

        # Untrusted code execution should fail
        context = {
            "action": "execute_code",
            "code_source": "web_content",
            "code_trusted": False,
        }
        violations = checker.check_all(context)
        inv1_violations = [v for v in violations if v.invariant_id == "INV-1"]
        assert len(inv1_violations) == 1

    def test_builtin_inv2_credential_leak(self):
        """INV-2: Never leak credentials."""
        checker = InvariantChecker()

        # Normal message should pass
        context = {
            "action": "send_message",
            "message_content": "Hello, how are you?",
            "contains_secrets": False,
        }
        violations = checker.check_all(context)
        inv2_violations = [v for v in violations if v.invariant_id == "INV-2"]
        assert len(inv2_violations) == 0

        # Message with credentials should fail
        context = {
            "action": "send_message",
            "message_content": "API_KEY=secret123",
            "contains_secrets": True,
        }
        violations = checker.check_all(context)
        inv2_violations = [v for v in violations if v.invariant_id == "INV-2"]
        assert len(inv2_violations) == 1

    def test_builtin_inv3_system_files(self):
        """INV-3: Never modify system files without permission."""
        checker = InvariantChecker()

        # User file modification should pass
        context = {
            "action": "write_file",
            "file_path": "/home/user/document.txt",
            "is_system_path": False,
            "has_permission": True,
        }
        violations = checker.check_all(context)
        inv3_violations = [v for v in violations if v.invariant_id == "INV-3"]
        assert len(inv3_violations) == 0

        # System file without permission should fail
        context = {
            "action": "write_file",
            "file_path": "/etc/passwd",
            "is_system_path": True,
            "has_permission": False,
        }
        violations = checker.check_all(context)
        inv3_violations = [v for v in violations if v.invariant_id == "INV-3"]
        assert len(inv3_violations) == 1

    def test_builtin_inv4_verify_tool_outputs(self):
        """INV-4: Always verify tool outputs."""
        checker = InvariantChecker()

        # Verified tool output should pass
        context = {"action": "use_tool_result", "tool_output_verified": True}
        violations = checker.check_all(context)
        inv4_violations = [v for v in violations if v.invariant_id == "INV-4"]
        assert len(inv4_violations) == 0

        # Unverified tool output should fail
        context = {"action": "use_tool_result", "tool_output_verified": False}
        violations = checker.check_all(context)
        inv4_violations = [v for v in violations if v.invariant_id == "INV-4"]
        assert len(inv4_violations) == 1

    def test_builtin_inv5_trust_delegation(self):
        """INV-5: Never trust delegated > direct trust."""
        checker = InvariantChecker()

        # Proper trust ordering should pass
        context = {
            "action": "trust_evaluation",
            "direct_trust": 0.8,
            "delegated_trust": 0.6,
        }
        violations = checker.check_all(context)
        inv5_violations = [v for v in violations if v.invariant_id == "INV-5"]
        assert len(inv5_violations) == 0

        # Inverted trust should fail
        context = {
            "action": "trust_evaluation",
            "direct_trust": 0.5,
            "delegated_trust": 0.9,
        }
        violations = checker.check_all(context)
        inv5_violations = [v for v in violations if v.invariant_id == "INV-5"]
        assert len(inv5_violations) == 1

    def test_add_custom_invariant(self):
        """Custom invariants can be added."""
        checker = InvariantChecker()

        custom = Invariant(
            id="CUSTOM-1",
            predicate=lambda ctx: ctx.get("custom_check", True),
            description="Custom business rule",
            severity=InvariantSeverity.MEDIUM,
        )
        checker.add_invariant(custom)

        context = {"custom_check": False}
        violations = checker.check_all(context)
        custom_violations = [v for v in violations if v.invariant_id == "CUSTOM-1"]
        assert len(custom_violations) == 1

    def test_check_returns_violations(self):
        """check_all returns list of violations."""
        checker = InvariantChecker()

        # Context that violates multiple invariants
        context = {
            "action": "execute_code",
            "code_trusted": False,
            "contains_secrets": True,
        }
        violations = checker.check_all(context)

        assert isinstance(violations, list)
        assert all(isinstance(v, InvariantViolation) for v in violations)

    def test_violation_contains_context(self):
        """Violations include context information."""
        checker = InvariantChecker()

        context = {
            "action": "execute_code",
            "code_trusted": False,
            "agent_id": "agent-1",
        }
        violations = checker.check_all(context)

        if violations:
            v = violations[0]
            assert v.context == context
            assert isinstance(v.timestamp, datetime)


class TestRuntimeMonitor:
    """Tests for RuntimeMonitor continuous checking."""

    def test_monitor_action(self):
        """Monitor checks actions against invariants."""
        monitor = RuntimeMonitor()

        action = AgentAction(
            agent_id="agent-1",
            action_type="execute_code",
            parameters={"code_trusted": True},
        )

        violations = monitor.check_action(action)
        assert isinstance(violations, list)

    def test_monitor_logs_violations(self):
        """Monitor maintains violation log."""
        monitor = RuntimeMonitor()

        action = AgentAction(
            agent_id="agent-1",
            action_type="execute_code",
            parameters={"code_trusted": False},
        )

        monitor.check_action(action)
        log = monitor.get_violation_log()

        assert isinstance(log, list)

    def test_monitor_by_agent(self):
        """Monitor can filter by agent."""
        monitor = RuntimeMonitor()

        action1 = AgentAction(
            agent_id="agent-1",
            action_type="execute_code",
            parameters={"code_trusted": False},
        )
        action2 = AgentAction(
            agent_id="agent-2",
            action_type="send_message",
            parameters={"contains_secrets": True},
        )

        monitor.check_action(action1)
        monitor.check_action(action2)

        agent1_violations = monitor.get_violations_by_agent("agent-1")
        agent2_violations = monitor.get_violations_by_agent("agent-2")

        # Each agent should have their own violations
        assert all(v.context.get("agent_id") == "agent-1" for v in agent1_violations)
        assert all(v.context.get("agent_id") == "agent-2" for v in agent2_violations)

    def test_monitor_severity_filter(self):
        """Monitor can filter by severity."""
        monitor = RuntimeMonitor()

        # Add a low severity invariant
        low_inv = Invariant(
            id="LOW-INV",
            predicate=lambda ctx: ctx.get("low_check", True),
            description="Low severity check",
            severity=InvariantSeverity.LOW,
        )
        monitor.checker.add_invariant(low_inv)

        action = AgentAction(
            agent_id="agent-1",
            action_type="test",
            parameters={"low_check": False, "code_trusted": False},
        )

        monitor.check_action(action)

        critical_only = monitor.get_violations_by_severity(InvariantSeverity.CRITICAL)
        all_violations = monitor.get_violation_log()

        # Critical filter should have fewer or equal violations
        assert len(critical_only) <= len(all_violations)

    def test_monitor_clear_log(self):
        """Monitor log can be cleared."""
        monitor = RuntimeMonitor()

        action = AgentAction(
            agent_id="agent-1",
            action_type="execute_code",
            parameters={"code_trusted": False},
        )

        monitor.check_action(action)
        assert len(monitor.get_violation_log()) > 0

        monitor.clear_log()
        assert len(monitor.get_violation_log()) == 0

    def test_monitor_stats(self):
        """Monitor tracks statistics."""
        monitor = RuntimeMonitor()

        for i in range(5):
            action = AgentAction(
                agent_id=f"agent-{i % 2}",
                action_type="execute_code",
                parameters={"code_trusted": False},
            )
            monitor.check_action(action)

        stats = monitor.get_stats()

        assert "total_checks" in stats
        assert "total_violations" in stats
        assert stats["total_checks"] == 5


class TestAgentAction:
    """Tests for AgentAction dataclass."""

    def test_action_creation(self):
        """Actions capture agent, type, and parameters."""
        action = AgentAction(
            agent_id="agent-1",
            action_type="write_file",
            parameters={"path": "/tmp/test.txt", "content": "hello"},
        )

        assert action.agent_id == "agent-1"
        assert action.action_type == "write_file"
        assert action.parameters["path"] == "/tmp/test.txt"

    def test_action_to_context(self):
        """Actions can be converted to context dict."""
        action = AgentAction(
            agent_id="agent-1",
            action_type="send_message",
            parameters={"message_content": "hello", "recipient": "agent-2"},
        )

        context = action.to_context()

        assert context["agent_id"] == "agent-1"
        assert context["action"] == "send_message"
        assert context["message_content"] == "hello"


class TestInvariantRemovalAndRecheck:
    """Tests for invariant removal and rechecking behavior."""

    def test_remove_invariant(self):
        """Removing an invariant excludes it from subsequent check_all calls."""
        checker = InvariantChecker()

        custom = Invariant(
            id="CUSTOM-1",
            predicate=lambda ctx: ctx.get("custom_check", True),
            description="Custom business rule",
            severity=InvariantSeverity.MEDIUM,
        )
        checker.add_invariant(custom)

        # Verify CUSTOM-1 is present
        context = {"custom_check": False}
        violations = checker.check_all(context)
        custom_violations = [v for v in violations if v.invariant_id == "CUSTOM-1"]
        assert len(custom_violations) == 1

        # Remove and verify absent
        checker.remove_invariant("CUSTOM-1")
        violations = checker.check_all(context)
        custom_violations = [v for v in violations if v.invariant_id == "CUSTOM-1"]
        assert len(custom_violations) == 0

    def test_recheck_after_removal(self):
        """After removing INV-1, context that would violate INV-1 passes cleanly."""
        checker = InvariantChecker()

        untrusted_code_context = {
            "action": "execute_code",
            "code_trusted": False,
        }

        # Should violate INV-1 before removal
        violations_before = checker.check_all(untrusted_code_context)
        inv1_before = [v for v in violations_before if v.invariant_id == "INV-1"]
        assert len(inv1_before) == 1

        # Remove INV-1
        checker.remove_invariant("INV-1")

        # Should no longer violate INV-1
        violations_after = checker.check_all(untrusted_code_context)
        inv1_after = [v for v in violations_after if v.invariant_id == "INV-1"]
        assert len(inv1_after) == 0

    def test_add_duplicate_id(self):
        """Adding invariant with duplicate id replaces the previous one (dict-keyed storage)."""
        checker = InvariantChecker(load_builtins=False)

        inv_a = Invariant(
            id="DUP-1",
            predicate=lambda ctx: True,  # always passes
            description="Version A - always passes",
            severity=InvariantSeverity.LOW,
        )
        inv_b = Invariant(
            id="DUP-1",
            predicate=lambda ctx: False,  # always fails
            description="Version B - always fails",
            severity=InvariantSeverity.HIGH,
        )

        checker.add_invariant(inv_a)
        checker.add_invariant(inv_b)

        # Only one invariant should exist with id DUP-1 (the last one added)
        all_invariants = checker.get_invariants()
        dup_invariants = [i for i in all_invariants if i.id == "DUP-1"]
        assert len(dup_invariants) == 1

        # The replacement (inv_b) should be the active one - always fails
        violations = checker.check_all({})
        dup_violations = [v for v in violations if v.invariant_id == "DUP-1"]
        assert len(dup_violations) == 1
        assert dup_violations[0].description == "Version B - always fails"
        assert dup_violations[0].severity == InvariantSeverity.HIGH


class TestMultipleSimultaneousViolations:
    """Tests for contexts that violate multiple invariants at once."""

    def test_multiple_violations_at_once(self):
        """Custom invariants can detect multiple simultaneous violations."""
        # Built-in INV-1/2/3 have disjoint action sets, so use custom invariants.

        checker_custom = InvariantChecker(load_builtins=False)
        checker_custom.add_invariant(Invariant(
            id="SIM-1",
            predicate=lambda ctx: ctx.get("a", True),
            description="Check A",
            severity=InvariantSeverity.CRITICAL,
        ))
        checker_custom.add_invariant(Invariant(
            id="SIM-2",
            predicate=lambda ctx: ctx.get("b", True),
            description="Check B",
            severity=InvariantSeverity.HIGH,
        ))
        checker_custom.add_invariant(Invariant(
            id="SIM-3",
            predicate=lambda ctx: ctx.get("c", True),
            description="Check C",
            severity=InvariantSeverity.MEDIUM,
        ))

        # All three false -> all three violated
        violations = checker_custom.check_all({"a": False, "b": False, "c": False})
        violated_ids = {v.invariant_id for v in violations}
        assert violated_ids == {"SIM-1", "SIM-2", "SIM-3"}

    def test_violation_count_matches_failed_invariants(self):
        """Number of violations equals number of invariants whose predicates return False."""
        checker = InvariantChecker(load_builtins=False)

        for i in range(7):
            checker.add_invariant(Invariant(
                id=f"COUNT-{i}",
                predicate=lambda ctx, idx=i: idx % 2 == 0,  # even pass, odd fail
                description=f"Count invariant {i}",
                severity=InvariantSeverity.MEDIUM,
            ))

        violations = checker.check_all({})
        expected_fail_count = len([i for i in range(7) if i % 2 != 0])  # 1,3,5 = 3
        assert len(violations) == expected_fail_count
        assert len(violations) == 3

    def test_violation_severity_mixed(self):
        """Violations from mixed severity levels are all present in results."""
        checker = InvariantChecker(load_builtins=False)

        checker.add_invariant(Invariant(
            id="MIX-LOW",
            predicate=lambda ctx: False,
            description="Low severity fail",
            severity=InvariantSeverity.LOW,
        ))
        checker.add_invariant(Invariant(
            id="MIX-CRIT",
            predicate=lambda ctx: False,
            description="Critical severity fail",
            severity=InvariantSeverity.CRITICAL,
        ))

        violations = checker.check_all({})
        severities = {v.severity for v in violations}
        assert InvariantSeverity.LOW in severities
        assert InvariantSeverity.CRITICAL in severities
        assert len(violations) == 2


class TestRuntimeMonitorMultiAgent:
    """Tests for RuntimeMonitor with multiple concurrent agents."""

    def test_agent_isolation(self):
        """Violations from agent-1 do not appear in agent-2 queries."""
        monitor = RuntimeMonitor()

        action_1 = AgentAction(
            agent_id="agent-1",
            action_type="execute_code",
            parameters={"code_trusted": False},
        )
        action_2 = AgentAction(
            agent_id="agent-2",
            action_type="execute_code",
            parameters={"code_trusted": True},  # no violation
        )

        monitor.check_action(action_1)
        monitor.check_action(action_2)

        agent1_violations = monitor.get_violations_by_agent("agent-1")
        agent2_violations = monitor.get_violations_by_agent("agent-2")

        assert len(agent1_violations) > 0
        assert len(agent2_violations) == 0

        # Double-check no cross-contamination
        for v in agent1_violations:
            assert v.context.get("agent_id") == "agent-1"

    def test_multiple_agents_stats(self):
        """Stats total_checks reflects checks across 3 distinct agents."""
        monitor = RuntimeMonitor()

        for agent_num in range(3):
            action = AgentAction(
                agent_id=f"agent-{agent_num}",
                action_type="execute_code",
                parameters={"code_trusted": True},
            )
            monitor.check_action(action)

        stats = monitor.get_stats()
        assert stats["total_checks"] == 3

    def test_violation_log_ordering(self):
        """Violation log preserves chronological order of check_action calls."""
        monitor = RuntimeMonitor()

        for i in range(3):
            action = AgentAction(
                agent_id=f"agent-{i}",
                action_type="execute_code",
                parameters={"code_trusted": False},
            )
            monitor.check_action(action)

        log = monitor.get_violation_log()
        assert len(log) >= 3

        # Timestamps should be non-decreasing (monotonic)
        for j in range(len(log) - 1):
            assert log[j].timestamp <= log[j + 1].timestamp

    def test_empty_agent_violations(self):
        """Querying violations for a nonexistent agent returns empty list."""
        monitor = RuntimeMonitor()

        action = AgentAction(
            agent_id="agent-1",
            action_type="execute_code",
            parameters={"code_trusted": False},
        )
        monitor.check_action(action)

        result = monitor.get_violations_by_agent("nonexistent")
        assert isinstance(result, list)
        assert len(result) == 0


class TestAgentActionExtended:
    """Extended tests for AgentAction dataclass."""

    def test_action_timestamp_auto(self):
        """AgentAction created without explicit timestamp has auto-generated datetime."""
        action = AgentAction(
            agent_id="agent-1",
            action_type="test_action",
            parameters={"key": "value"},
        )

        assert hasattr(action, "timestamp")
        assert isinstance(action.timestamp, datetime)
        # Timestamp should be recent (within last 60 seconds)
        delta = (datetime.now() - action.timestamp).total_seconds()
        assert 0 <= delta < 60

    def test_action_to_context_preserves_all_params(self):
        """to_context includes all 5 parameters from the action."""
        params = {
            "alpha": 1,
            "beta": "two",
            "gamma": 3.0,
            "delta": True,
            "epsilon": [4, 5],
        }
        action = AgentAction(
            agent_id="agent-x",
            action_type="multi_param_action",
            parameters=params,
        )

        context = action.to_context()

        for key, value in params.items():
            assert key in context, f"Parameter '{key}' missing from context"
            assert context[key] == value

        # Also verify structural fields
        assert context["agent_id"] == "agent-x"
        assert context["action"] == "multi_param_action"
        assert "timestamp" in context

    def test_action_to_context_action_type_mapping(self):
        """to_context maps action_type to context['action'] key."""
        action_types = ["execute_code", "send_message", "write_file", "trust_evaluation"]

        for atype in action_types:
            action = AgentAction(
                agent_id="agent-map",
                action_type=atype,
                parameters={},
            )
            context = action.to_context()
            assert context["action"] == atype


class TestInvariantPredicateEdgeCases:
    """Tests for edge cases in invariant predicate evaluation."""

    def test_predicate_exception_handling(self):
        """Invariant with predicate raising TypeError is treated as 'holds' (not violated).

        The Invariant.check() method catches TypeError, KeyError, ValueError
        and returns True, meaning the invariant is considered to hold.
        """
        def bad_predicate(ctx):
            raise TypeError("deliberate type error in predicate")

        inv = Invariant(
            id="ERR-1",
            predicate=bad_predicate,
            description="Predicate that raises TypeError",
            severity=InvariantSeverity.HIGH,
        )

        checker = InvariantChecker(load_builtins=False)
        checker.add_invariant(inv)

        # TypeError is caught by Invariant.check() -> returns True -> no violation
        violations = checker.check_all({"anything": True})
        err_violations = [v for v in violations if v.invariant_id == "ERR-1"]
        assert len(err_violations) == 0

    def test_predicate_returns_none(self):
        """Invariant with predicate returning None (falsy) is treated as violation."""
        inv = Invariant(
            id="NONE-1",
            predicate=lambda ctx: None,  # None is falsy
            description="Predicate returning None",
            severity=InvariantSeverity.MEDIUM,
        )

        checker = InvariantChecker(load_builtins=False)
        checker.add_invariant(inv)

        violations = checker.check_all({})
        none_violations = [v for v in violations if v.invariant_id == "NONE-1"]
        assert len(none_violations) == 1
        assert none_violations[0].severity == InvariantSeverity.MEDIUM
