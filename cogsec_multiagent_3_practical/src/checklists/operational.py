from __future__ import annotations

from .. import ChecklistItem
from .models import ChecklistPhase, EnhancedChecklistItem, OperationalFrequency


class OperationalChecklist:
    """Daily and weekly operational checklist.

    Implements the operational section of manuscript Section 03.
    Supports daily and weekly reset cycles for ongoing cognitive
    security hygiene.

    Daily items (4):
        1. Review drift alerts
        2. Verify tripwire integrity
        3. Check trust metrics
        4. Review failed consensus

    Weekly items (4):
        1. Analyze attack patterns
        2. Audit delegation chains
        3. Verify invariant compliance
        4. Update threat intel
    """

    def __init__(self) -> None:
        """Initialize with default operational items from manuscript."""
        self.items: list[EnhancedChecklistItem] = []
        self._load_defaults()

    def _load_defaults(self) -> None:
        """Load default daily and weekly items from manuscript."""
        # Daily items
        daily_items = [
            (
                "daily-001",
                "Review drift alerts: Check for unusual belief changes",
            ),
            (
                "daily-002",
                "Verify tripwire integrity: Confirm canary beliefs unchanged",
            ),
            (
                "daily-003",
                "Check trust metrics: Monitor for unexpected trust score changes",
            ),
            (
                "daily-004",
                "Review failed consensus: Investigate any Byzantine fault indications",
            ),
        ]
        for id_, desc in daily_items:
            self.items.append(
                EnhancedChecklistItem(
                    item=ChecklistItem(id=id_, category="daily", description=desc),
                    phase=ChecklistPhase.OPERATIONAL,
                    category=OperationalFrequency.DAILY.value,
                )
            )

        # Weekly items
        weekly_items = [
            (
                "weekly-001",
                "Analyze attack patterns: Review blocked injection attempts",
            ),
            (
                "weekly-002",
                "Audit delegation chains: Check for unusual delegation patterns",
            ),
            (
                "weekly-003",
                "Verify invariant compliance: Confirm no invariant violations",
            ),
            (
                "weekly-004",
                "Update threat intel: Incorporate new attack techniques into defenses",
            ),
        ]
        for id_, desc in weekly_items:
            self.items.append(
                EnhancedChecklistItem(
                    item=ChecklistItem(id=id_, category="weekly", description=desc),
                    phase=ChecklistPhase.OPERATIONAL,
                    category=OperationalFrequency.WEEKLY.value,
                )
            )

    def get_daily_items(self) -> list[EnhancedChecklistItem]:
        """Get all daily checklist items.

        Returns:
            List of items with daily frequency.
        """
        return [i for i in self.items if i.category == OperationalFrequency.DAILY.value]

    def get_weekly_items(self) -> list[EnhancedChecklistItem]:
        """Get all weekly checklist items.

        Returns:
            List of items with weekly frequency.
        """
        return [i for i in self.items if i.category == OperationalFrequency.WEEKLY.value]

    def complete_item(self, item_id: str) -> None:
        """Mark an operational item as completed.

        Args:
            item_id: Item ID to complete (e.g., "daily-001").

        Raises:
            ValueError: If item_id is not found in the checklist.
        """
        for enhanced in self.items:
            if enhanced.item.id == item_id:
                enhanced.completed = True
                return
        raise ValueError(f"Item '{item_id}' not found")

    def reset_daily(self) -> None:
        """Reset all daily items to incomplete for a new cycle.

        Called at the start of each day to begin a fresh daily
        checklist cycle. Does not affect weekly items.
        """
        for item in self.get_daily_items():
            item.completed = False

    def reset_weekly(self) -> None:
        """Reset all weekly items to incomplete for a new cycle.

        Called at the start of each week to begin a fresh weekly
        checklist cycle. Does not affect daily items.
        """
        for item in self.get_weekly_items():
            item.completed = False

    def daily_complete(self) -> bool:
        """Check if all daily items are complete.

        Returns:
            True if every daily item has been marked completed.
            False if the daily list is empty or any item is incomplete.
        """
        daily = self.get_daily_items()
        return all(i.completed for i in daily) if daily else False

    def weekly_complete(self) -> bool:
        """Check if all weekly items are complete.

        Returns:
            True if every weekly item has been marked completed.
            False if the weekly list is empty or any item is incomplete.
        """
        weekly = self.get_weekly_items()
        return all(i.completed for i in weekly) if weekly else False


# =============================================================================
