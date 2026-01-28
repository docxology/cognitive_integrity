"""Tests for behavioral invariant checking."""

from datetime import datetime

import pytest
from invariants import (AgentAction, Invariant, InvariantChecker,
                        InvariantSeverity, InvariantViolation, RuntimeMonitor)


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
