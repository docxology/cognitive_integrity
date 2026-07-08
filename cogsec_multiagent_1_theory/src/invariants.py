from __future__ import annotations

"""
Behavioral Invariant Checking for Multiagent Systems.

Implements invariant predicates and runtime monitoring.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class InvariantSeverity(IntEnum):
    """Severity levels for invariant violations."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Invariant:
    """
    A behavioral invariant with predicate and metadata.

    Attributes:
        id: Unique identifier (e.g., "INV-1")
        predicate: Function returning True if invariant holds
        description: Human-readable description
        severity: Violation severity level
    """

    id: str
    predicate: Callable[[Dict], bool]
    description: str
    severity: InvariantSeverity = InvariantSeverity.MEDIUM

    def check(self, context: Dict) -> bool:
        """
        Check if invariant holds for given context.

        Args:
            context: Dictionary of action/state parameters

        Returns:
            True if invariant holds, False if violated
        """
        try:
            return self.predicate(context)
        except Exception as exc:
            # If predicate fails, assume invariant doesn't apply
            logger.warning("Invariant %s predicate raised %s, assuming holds", self.id, exc)
            return True


@dataclass
class InvariantViolation:
    """
    Record of an invariant violation.

    Attributes:
        invariant_id: ID of violated invariant
        description: Description of the invariant
        severity: Severity level
        context: Context that caused violation
        timestamp: When violation occurred
    """

    invariant_id: str
    description: str
    severity: InvariantSeverity
    context: Dict
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AgentAction:
    """
    Represents an agent action for monitoring.

    Attributes:
        agent_id: Acting agent
        action_type: Type of action
        parameters: Action parameters
        timestamp: When action occurred
    """

    agent_id: str
    action_type: str
    parameters: Dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_context(self) -> Dict:
        """Convert action to context dictionary for invariant checking."""
        context = {
            "agent_id": self.agent_id,
            "action": self.action_type,
            "timestamp": self.timestamp,
        }
        context.update(self.parameters)
        return context


class InvariantChecker:
    """
    Checks behavioral invariants against action contexts.

    Pre-loaded with critical security invariants:
    - INV-1: Never execute untrusted code
    - INV-2: Never leak credentials
    - INV-3: Never modify system files without permission
    - INV-4: Always verify tool outputs
    - INV-5: Never trust delegated > direct trust
    """

    def __init__(self, load_builtins: bool = True):
        """
        Initialize invariant checker.

        Args:
            load_builtins: Whether to load built-in invariants
        """
        self._invariants: Dict[str, Invariant] = {}

        if load_builtins:
            self._load_builtin_invariants()

    def _load_builtin_invariants(self) -> None:
        """Load the five built-in security invariants."""
        # INV-1: Never execute untrusted code
        self.add_invariant(
            Invariant(
                id="INV-1",
                predicate=self._inv1_no_untrusted_code,
                description="Never execute untrusted code",
                severity=InvariantSeverity.CRITICAL,
            )
        )

        # INV-2: Never leak credentials
        self.add_invariant(
            Invariant(
                id="INV-2",
                predicate=self._inv2_no_credential_leak,
                description="Never leak credentials or secrets",
                severity=InvariantSeverity.CRITICAL,
            )
        )

        # INV-3: Never modify system files without permission
        self.add_invariant(
            Invariant(
                id="INV-3",
                predicate=self._inv3_no_unauthorized_system_write,
                description="Never modify system files without permission",
                severity=InvariantSeverity.CRITICAL,
            )
        )

        # INV-4: Always verify tool outputs
        self.add_invariant(
            Invariant(
                id="INV-4",
                predicate=self._inv4_verify_tool_outputs,
                description="Always verify tool outputs before use",
                severity=InvariantSeverity.HIGH,
            )
        )

        # INV-5: Never trust delegated > direct trust
        self.add_invariant(
            Invariant(
                id="INV-5",
                predicate=self._inv5_trust_ordering,
                description="Delegated trust must not exceed direct trust",
                severity=InvariantSeverity.HIGH,
            )
        )

    @staticmethod
    def _inv1_no_untrusted_code(ctx: Dict) -> bool:
        """INV-1: Never execute untrusted code."""
        action = ctx.get("action", "")
        if action not in ("execute_code", "run_script", "eval"):
            return True  # Not a code execution action
        return ctx.get("code_trusted", True)

    @staticmethod
    def _inv2_no_credential_leak(ctx: Dict) -> bool:
        """INV-2: Never leak credentials."""
        action = ctx.get("action", "")
        if action not in ("send_message", "output", "log", "write"):
            return True  # Not an output action
        return not ctx.get("contains_secrets", False)

    @staticmethod
    def _inv3_no_unauthorized_system_write(ctx: Dict) -> bool:
        """INV-3: Never modify system files without permission."""
        action = ctx.get("action", "")
        if action not in ("write_file", "modify_file", "delete_file"):
            return True  # Not a file operation

        is_system = ctx.get("is_system_path", False)
        has_permission = ctx.get("has_permission", True)

        if is_system and not has_permission:
            return False
        return True

    @staticmethod
    def _inv4_verify_tool_outputs(ctx: Dict) -> bool:
        """INV-4: Always verify tool outputs."""
        action = ctx.get("action", "")
        if action not in ("use_tool_result", "accept_tool_output"):
            return True  # Not using tool output
        return ctx.get("tool_output_verified", True)

    @staticmethod
    def _inv5_trust_ordering(ctx: Dict) -> bool:
        """INV-5: Delegated trust must not exceed direct trust."""
        action = ctx.get("action", "")
        if action != "trust_evaluation":
            return True  # Not a trust evaluation

        direct = ctx.get("direct_trust", 1.0)
        delegated = ctx.get("delegated_trust", 0.0)

        return delegated <= direct

    def add_invariant(self, invariant: Invariant) -> None:
        """Add an invariant to the checker."""
        self._invariants[invariant.id] = invariant

    def remove_invariant(self, invariant_id: str) -> None:
        """Remove an invariant by ID."""
        self._invariants.pop(invariant_id, None)

    def check_all(self, context: Dict) -> List[InvariantViolation]:
        """
        Check all invariants against context.

        Args:
            context: Dictionary of action/state parameters

        Returns:
            List of violations (empty if all invariants hold)
        """
        violations = []

        for inv in self._invariants.values():
            if not inv.check(context):
                violations.append(
                    InvariantViolation(
                        invariant_id=inv.id,
                        description=inv.description,
                        severity=inv.severity,
                        context=context,
                    )
                )

        return violations

    def check_single(self, invariant_id: str, context: Dict) -> Optional[InvariantViolation]:
        """
        Check a single invariant.

        Args:
            invariant_id: ID of invariant to check
            context: Dictionary of action/state parameters

        Returns:
            Violation if invariant violated, None otherwise
        """
        inv = self._invariants.get(invariant_id)
        if not inv:
            return None

        if not inv.check(context):
            return InvariantViolation(
                invariant_id=inv.id,
                description=inv.description,
                severity=inv.severity,
                context=context,
            )
        return None

    def get_invariants(self) -> List[Invariant]:
        """Get all registered invariants."""
        return list(self._invariants.values())


class RuntimeMonitor:
    """
    Continuous runtime monitoring for invariant violations.

    Monitors agent actions and maintains violation logs.
    """

    def __init__(self, checker: Optional[InvariantChecker] = None):
        """
        Initialize runtime monitor.

        Args:
            checker: InvariantChecker to use (creates default if None)
        """
        self.checker = checker or InvariantChecker()
        self._violation_log: List[InvariantViolation] = []
        self._check_count: int = 0

    def check_action(self, action: AgentAction) -> List[InvariantViolation]:
        """
        Check an agent action against all invariants.

        Args:
            action: The action to check

        Returns:
            List of violations (empty if action is compliant)
        """
        context = action.to_context()
        violations = self.checker.check_all(context)

        # Log violations
        self._violation_log.extend(violations)
        self._check_count += 1

        return violations

    def get_violation_log(self) -> List[InvariantViolation]:
        """Get complete violation log."""
        return list(self._violation_log)

    def get_violations_by_agent(self, agent_id: str) -> List[InvariantViolation]:
        """Get violations for a specific agent."""
        return [v for v in self._violation_log if v.context.get("agent_id") == agent_id]

    def get_violations_by_severity(
        self, min_severity: InvariantSeverity
    ) -> List[InvariantViolation]:
        """Get violations at or above a severity level."""
        return [v for v in self._violation_log if v.severity >= min_severity]

    def clear_log(self) -> None:
        """Clear the violation log."""
        self._violation_log.clear()

    def get_stats(self) -> Dict:
        """Get monitoring statistics."""
        severity_counts = {s.name: 0 for s in InvariantSeverity}
        for v in self._violation_log:
            severity_counts[v.severity.name] += 1

        return {
            "total_checks": self._check_count,
            "total_violations": len(self._violation_log),
            "violations_by_severity": severity_counts,
        }
