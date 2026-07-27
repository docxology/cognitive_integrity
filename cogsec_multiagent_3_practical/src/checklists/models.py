"""
Human-Actionable Checklists for Cognitive Security.

Implements Section 03 of the Practical Implementation Guide:
Pre-deployment, operational, and incident response checklists
with configuration reference validation.

This module provides three checklist types aligned to the manuscript:

1. **PreDeploymentChecklist** - 4 categories x 4 items = 16 items
   covering architecture review, defense configuration, monitoring
   setup, and incident response preparation.

2. **OperationalChecklist** - Daily (4 items) and weekly (4 items)
   operational security tasks with reset cycles.

3. **IncidentResponseChecklist** - 4 time-phased sections x 4 items
   = 16 items covering immediate through post-incident response.

Additionally, **ConfigurationReference** validates trust calculus
parameters, firewall thresholds, and tripwire configurations against
manuscript-specified recommended values and ranges.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .. import ChecklistItem

# =============================================================================
# Enums
# =============================================================================


class ChecklistPhase(Enum):
    """Top-level checklist phases.

    Maps to the three major sections of manuscript Section 03:
    pre-deployment preparation, ongoing operations, and incident response.
    """

    PRE_DEPLOYMENT = "pre_deployment"
    OPERATIONAL = "operational"
    INCIDENT_RESPONSE = "incident_response"


class ChecklistCategory(Enum):
    """Pre-deployment checklist categories.

    The four categories that must each be completed before
    a system can be considered deployment-ready.
    """

    ARCHITECTURE_REVIEW = "architecture_review"
    DEFENSE_CONFIGURATION = "defense_configuration"
    MONITORING_SETUP = "monitoring_setup"
    INCIDENT_RESPONSE_PREP = "incident_response_prep"


class OperationalFrequency(Enum):
    """Operational checklist frequencies.

    Operational tasks are divided into daily and weekly cadences
    to maintain ongoing cognitive security hygiene.
    """

    DAILY = "daily"
    WEEKLY = "weekly"


class IncidentSeverity(Enum):
    """Incident response time windows.

    Each severity level corresponds to a time window during
    incident response, from immediate triage through post-incident
    analysis.
    """

    IMMEDIATE = "immediate"  # First 15 minutes
    INVESTIGATION = "investigation"  # First hour
    RECOVERY = "recovery"  # Following hours
    POST_INCIDENT = "post_incident"  # Following days


# =============================================================================
# Enhanced Checklist Item
# =============================================================================


@dataclass
class EnhancedChecklistItem:
    """Extended checklist item with phase and evidence tracking.

    Wraps a base ChecklistItem with additional metadata for tracking
    which phase the item belongs to, who verified it, and what evidence
    supports its completion.

    Args:
        item: Base checklist item containing id, category, description.
        phase: Which top-level phase this item belongs to.
        category: Specific category within the phase (string form).
        evidence: Evidence of completion (e.g., screenshot path, log ref).
        verified_by: Who verified completion (e.g., operator name).
        verification_date: When verification occurred (ISO date string).
    """

    item: ChecklistItem
    phase: ChecklistPhase
    category: str = ""
    evidence: str = ""
    verified_by: str = ""
    verification_date: str = ""

    @property
    def completed(self) -> bool:
        """Whether the underlying item is completed.

        Returns:
            True if the base ChecklistItem is marked completed.
        """
        return self.item.completed

    @completed.setter
    def completed(self, value: bool) -> None:
        """Set completion on underlying item.

        Args:
            value: New completion status.
        """
        self.item.completed = value
