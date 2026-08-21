"""Pytest configuration for cogsec_multiagent_3_practical tests."""

# Unique pytest_plugins declaration prevents conftest collection conflicts
# when running tests from multiple projects simultaneously
pytest_plugins: list[str] = []

import pytest


@pytest.fixture
def sample_checklist_items():
    """Provide sample checklist items for testing."""
    from src import ChecklistItem

    return [
        ChecklistItem(
            id="auth-001",
            category="authentication",
            description="Verify agent identity before trust delegation",
            required=True,
        ),
        ChecklistItem(
            id="monitor-001",
            category="monitoring",
            description="Enable cognitive tripwire monitoring",
            required=True,
        ),
        ChecklistItem(
            id="logging-001",
            category="logging",
            description="Configure provenance tracking",
            required=False,
        ),
    ]
