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


# ---------------------------------------------------------------------------
# Auto-skip requires_ollama when Ollama is unreachable
# ---------------------------------------------------------------------------

def _ollama_available() -> bool:
    """Probe Ollama server once and cache result."""
    try:
        import requests
        resp = requests.get("http://localhost:11434/api/tags", timeout=2)
        return resp.status_code == 200
    except Exception:
        return False


_OLLAMA_UP: bool | None = None


def pytest_collection_modifyitems(config, items):
    """Auto-skip tests marked `requires_ollama` when Ollama is not running."""
    global _OLLAMA_UP  # noqa: PLW0603
    if _OLLAMA_UP is None:
        _OLLAMA_UP = _ollama_available()

    if _OLLAMA_UP:
        return  # Ollama is up — run all tests

    skip_marker = pytest.mark.skip(reason="Ollama not running at localhost:11434")
    for item in items:
        if "requires_ollama" in item.keywords:
            item.add_marker(skip_marker)

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
    
    # If a real-data sentinel exists, the pipeline has already produced results.
    # Do NOT overwrite with DataGenerator synthetic data — that would corrupt
    # published figures with fabricated values.
    sentinel = output_dir / ".real_data_marker"
    if sentinel.exists():
        return  # Real pipeline/simulation data present; skip synthetic generation.

    if missing:
        print("\n[conftest] Generating missing test data in output/data/...")
        print("[conftest] NOTE: This is synthetic data for schema/test validation.")
        print("[conftest]       Run scripts/run_full_evaluation.py to produce real data.")
        output_dir.mkdir(parents=True, exist_ok=True)
        # Use str(output_dir) to ensure compatibility if expecting string
        generator = DataGenerator(output_dir=str(output_dir))
        generator.generate_all()
        print("[conftest] Data generation complete.")
