"""Pytest configuration for cogsec_multiagent_2_computational tests."""

# Unique pytest_plugins declaration prevents conftest collection conflicts
# when running tests from multiple projects simultaneously
pytest_plugins = []

import os
import sys

# Force headless backend for matplotlib in tests
os.environ.setdefault("MPLBACKEND", "Agg")

# Add project root to path so we can import via `src.*` package
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
