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

import pytest
from pathlib import Path

# Try to import DataGenerator, preventing import errors if src is not yet importable or during collection
try:
    from src.data.generate import DataGenerator
except ImportError:
    DataGenerator = None

@pytest.fixture(scope="session", autouse=True)
def ensure_test_data():
    """Ensure test data exists in output/data before running tests.
    
    The pipeline cleans output/ directories before running tests, so we need
    to regenerate the data if it's missing to avoid FileNotFoundError in
    visualization tests.
    """
    if DataGenerator is None:
        return

    # Use absolute path so tests work regardless of CWD
    output_dir = Path(__file__).resolve().parent.parent / "output" / "data"
    
    # Check if key files exist
    required_files = ["full_evaluation_results.json", "ablation_results.json"]
    missing = not output_dir.exists() or not all((output_dir / f).exists() for f in required_files)
    
    if missing:
        print("\n[conftest] Generating missing test data in output/data/...")
        output_dir.mkdir(parents=True, exist_ok=True)
        # Use str(output_dir) to ensure compatibility if expecting string
        generator = DataGenerator(output_dir=str(output_dir))
        generator.generate_all()
        print("[conftest] Data generation complete.")
