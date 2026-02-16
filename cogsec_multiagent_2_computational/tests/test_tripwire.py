"""Tests for cognitive tripwire system."""

import pytest
from src import Canary, CognitiveTripwire, TripwireAlert


class TestCanary:
    """Tests for Canary beliefs."""

    def test_canary_check_within_tolerance(self):
        """Canary passes when belief is within tolerance."""
        canary = Canary(proposition="I am Agent-1", expected_belief=1.0, tolerance=0.1)
        assert canary.check(0.95)
        assert canary.check(1.0)

    def test_canary_check_outside_tolerance(self):
        """Canary fails when belief exceeds tolerance."""
        canary = Canary(proposition="I am Agent-1", expected_belief=1.0, tolerance=0.1)
        assert not canary.check(0.8)
        assert not canary.check(0.5)


class TestTripwireAlert:
    """Tests for TripwireAlert."""

    def test_severity_critical(self):
        """Large drift is CRITICAL severity."""
        canary = Canary("test", 1.0)
        alert = TripwireAlert(canary=canary, actual_belief=0.3, drift=0.7)
        assert alert.severity == "CRITICAL"

    def test_severity_high(self):
        """Medium-large drift is HIGH severity."""
        canary = Canary("test", 1.0)
        alert = TripwireAlert(canary=canary, actual_belief=0.6, drift=0.4)
        assert alert.severity == "HIGH"

    def test_severity_medium(self):
        """Medium drift is MEDIUM severity."""
        canary = Canary("test", 1.0)
        alert = TripwireAlert(canary=canary, actual_belief=0.75, drift=0.25)
        assert alert.severity == "MEDIUM"

    def test_severity_low(self):
        """Small drift is LOW severity."""
        canary = Canary("test", 1.0)
        alert = TripwireAlert(canary=canary, actual_belief=0.85, drift=0.15)
        assert alert.severity == "LOW"


class TestCognitiveTripwire:
    """Tests for CognitiveTripwire system."""

    def test_add_canary(self):
        """Canaries can be added."""
        tripwire = CognitiveTripwire()
        canary = Canary("I am Agent-1", 1.0)
        tripwire.add_canary(canary)

        assert "I am Agent-1" in tripwire._canaries

    def test_add_identity_canary(self):
        """Identity canaries are created correctly."""
        tripwire = CognitiveTripwire()
        tripwire.add_identity_canary("Agent-7")

        assert "I am agent Agent-7" in tripwire._canaries
        canary = tripwire._canaries["I am agent Agent-7"]
        assert canary.category == "identity"
        assert canary.expected_belief == 1.0

    def test_add_boundary_canary(self):
        """Boundary canaries expect low belief."""
        tripwire = CognitiveTripwire()
        tripwire.add_boundary_canary("access /etc/passwd")

        canary = tripwire._canaries["I can access /etc/passwd"]
        assert canary.category == "boundary"
        assert canary.expected_belief == 0.0

    def test_check_no_triggers(self):
        """Check returns empty when beliefs match."""
        tripwire = CognitiveTripwire()
        tripwire.add_identity_canary("Agent-1")

        beliefs = {"I am agent Agent-1": 1.0}
        alerts = tripwire.check(beliefs)

        assert len(alerts) == 0

    def test_check_triggers_on_drift(self):
        """Check returns alerts when beliefs drift."""
        tripwire = CognitiveTripwire()
        tripwire.add_identity_canary("Agent-1")

        # Significant drift from expected 1.0
        beliefs = {"I am agent Agent-1": 0.3}
        alerts = tripwire.check(beliefs)

        assert len(alerts) == 1
        assert alerts[0].drift > 0.5

    def test_check_single(self):
        """Single canary check works."""
        tripwire = CognitiveTripwire()
        tripwire.add_canary(Canary("test prop", 0.8, tolerance=0.1))

        # Within tolerance
        assert tripwire.check_single("test prop", 0.75) is None

        # Outside tolerance
        alert = tripwire.check_single("test prop", 0.5)
        assert alert is not None
        assert alert.drift == pytest.approx(0.3)

    def test_handler_called_on_trigger(self):
        """Registered handlers are called on trigger."""
        tripwire = CognitiveTripwire()
        tripwire.add_canary(Canary("test", 1.0, tolerance=0.1))

        handler_called = []

        def handler(alert):
            handler_called.append(alert)

        tripwire.register_handler(handler)
        tripwire.check({"test": 0.5})

        assert len(handler_called) == 1

    def test_get_alerts_filtering(self):
        """Alerts can be filtered by category and severity."""
        tripwire = CognitiveTripwire()
        tripwire.add_identity_canary("Agent-1")
        tripwire.add_boundary_canary("do bad thing")

        # Trigger both
        tripwire.check(
            {
                "I am agent Agent-1": 0.2,  # identity, high drift
                "I can do bad thing": 0.8,  # boundary, high drift
            }
        )

        identity_alerts = tripwire.get_alerts(category="identity")
        assert len(identity_alerts) == 1

        high_alerts = tripwire.get_alerts(min_severity="HIGH")
        assert all(a.severity in ["HIGH", "CRITICAL"] for a in high_alerts)

    def test_clear_alerts(self):
        """Alerts can be cleared."""
        tripwire = CognitiveTripwire()
        tripwire.add_canary(Canary("test", 1.0))
        tripwire.check({"test": 0.0})

        assert len(tripwire._alerts) > 0
        tripwire.clear_alerts()
        assert len(tripwire._alerts) == 0

    def test_canary_count_by_category(self):
        """Canary counts are tracked by category."""
        tripwire = CognitiveTripwire()
        tripwire.add_identity_canary("A1")
        tripwire.add_identity_canary("A2")
        tripwire.add_boundary_canary("action1")
        tripwire.add_principal_canary("Alice")

        counts = tripwire.get_canary_count()
        assert counts["identity"] == 2
        assert counts["boundary"] == 1
        assert counts["principal"] == 1

    def test_rotate_canaries(self):
        """Canaries can be rotated by category."""
        tripwire = CognitiveTripwire()
        tripwire.add_identity_canary("Old-Agent")

        new_canaries = [
            Canary("I am New-Agent-1", 1.0, category="identity"),
            Canary("I am New-Agent-2", 1.0, category="identity"),
        ]
        tripwire.rotate_canaries("identity", new_canaries)

        counts = tripwire.get_canary_count()
        assert counts["identity"] == 2
        assert "I am agent Old-Agent" not in tripwire._canaries
