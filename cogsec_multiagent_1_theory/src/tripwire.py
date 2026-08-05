"""
Cognitive Tripwire System.

Embeds canary beliefs to detect manipulation.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Dict, List, Optional


@dataclass
class Canary:
    """
    A canary belief for tripwire detection.

    Attributes:
        proposition: The belief statement
        expected_belief: Expected confidence level [0,1]
        tolerance: Allowed drift from expected
        category: Type of canary (identity, boundary, principal, temporal)
    """

    proposition: str
    expected_belief: float
    tolerance: float = 0.1
    category: str = "general"
    created_at: datetime = field(default_factory=datetime.now)

    def check(self, actual_belief: float) -> bool:
        """
        Check if canary has been triggered.

        Returns:
            True if belief is within tolerance, False if triggered
        """
        return abs(actual_belief - self.expected_belief) <= self.tolerance


@dataclass
class TripwireAlert:
    """Alert generated when tripwire is triggered."""

    canary: Canary
    actual_belief: float
    drift: float
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def severity(self) -> str:
        """Compute alert severity based on drift magnitude."""
        if self.drift > 0.5:
            return "CRITICAL"
        elif self.drift > 0.3:
            return "HIGH"
        elif self.drift > 0.2:
            return "MEDIUM"
        return "LOW"


class CognitiveTripwire:
    """
    Monitors canary beliefs for manipulation detection.

    Categories:
    - identity: Agent identity beliefs
    - boundary: Capability boundary beliefs
    - principal: Authority chain beliefs
    - temporal: Time/session beliefs
    """

    CATEGORIES = ["identity", "boundary", "principal", "temporal", "general"]

    def __init__(self):
        self._canaries: Dict[str, Canary] = {}
        self._alerts: List[TripwireAlert] = []
        self._alert_handlers: List[Callable[[TripwireAlert], None]] = []

    def add_canary(self, canary: Canary) -> None:
        """Register a canary belief."""
        self._canaries[canary.proposition] = canary

    def add_identity_canary(self, agent_id: str, expected_belief: float = 1.0) -> None:
        """Add identity verification canary."""
        self.add_canary(
            Canary(
                proposition=f"I am agent {agent_id}",
                expected_belief=expected_belief,
                tolerance=0.05,
                category="identity",
            )
        )

    def add_boundary_canary(self, forbidden_action: str, expected_belief: float = 0.0) -> None:
        """Add capability boundary canary."""
        self.add_canary(
            Canary(
                proposition=f"I can {forbidden_action}",
                expected_belief=expected_belief,
                tolerance=0.1,
                category="boundary",
            )
        )

    def add_principal_canary(self, principal_name: str, expected_belief: float = 1.0) -> None:
        """Add principal authority canary."""
        self.add_canary(
            Canary(
                proposition=f"My principal is {principal_name}",
                expected_belief=expected_belief,
                tolerance=0.05,
                category="principal",
            )
        )

    def add_temporal_canary(self, session_id: str, expected_belief: float = 1.0) -> None:
        """Add session/temporal canary."""
        self.add_canary(
            Canary(
                proposition=f"Current session is {session_id}",
                expected_belief=expected_belief,
                tolerance=0.05,
                category="temporal",
            )
        )

    def check(self, beliefs: Dict[str, float]) -> List[TripwireAlert]:
        """
        Check all canaries against current beliefs.

        Args:
            beliefs: Map of proposition -> belief confidence

        Returns:
            List of triggered alerts
        """
        triggered = []

        for prop, canary in self._canaries.items():
            actual = beliefs.get(prop, 0.5)  # Default to uncertain

            if not canary.check(actual):
                drift = abs(actual - canary.expected_belief)
                alert = TripwireAlert(canary=canary, actual_belief=actual, drift=drift)
                triggered.append(alert)
                self._alerts.append(alert)

                # Notify handlers
                for handler in self._alert_handlers:
                    handler(alert)

        return triggered

    def check_single(self, proposition: str, actual_belief: float) -> Optional[TripwireAlert]:
        """
        Check single canary.

        Returns:
            Alert if triggered, None otherwise
        """
        if proposition not in self._canaries:
            return None

        canary = self._canaries[proposition]
        if not canary.check(actual_belief):
            drift = abs(actual_belief - canary.expected_belief)
            alert = TripwireAlert(canary=canary, actual_belief=actual_belief, drift=drift)
            self._alerts.append(alert)
            return alert

        return None

    def register_handler(self, handler: Callable[[TripwireAlert], None]) -> None:
        """Register alert handler callback."""
        self._alert_handlers.append(handler)

    def get_alerts(
        self, category: Optional[str] = None, min_severity: Optional[str] = None
    ) -> List[TripwireAlert]:
        """
        Get alerts with optional filtering.

        Args:
            category: Filter by canary category
            min_severity: Minimum severity level

        Returns:
            Filtered list of alerts
        """
        severity_order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
        min_level = severity_order.get(min_severity, 0) if min_severity else 0

        return [
            a
            for a in self._alerts
            if (category is None or a.canary.category == category)
            and severity_order.get(a.severity, 0) >= min_level
        ]

    def clear_alerts(self) -> None:
        """Clear alert history."""
        self._alerts.clear()

    def get_canary_count(self) -> Dict[str, int]:
        """Get canary counts by category."""
        counts = {cat: 0 for cat in self.CATEGORIES}
        for canary in self._canaries.values():
            counts[canary.category] = counts.get(canary.category, 0) + 1
        return counts

    def rotate_canaries(self, category: str, new_canaries: List[Canary]) -> None:
        """
        Rotate canaries in a category.

        Used to prevent adversarial learning of canary positions.
        """
        # Remove old canaries in category
        self._canaries = {p: c for p, c in self._canaries.items() if c.category != category}

        # Add new canaries
        for original in new_canaries:
            # Operate on a copy so the caller's Canary objects are not mutated.
            canary = copy.copy(original)
            canary.category = category
            self.add_canary(canary)
