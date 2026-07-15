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

from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Auto-skip requires_ollama when Ollama is unreachable, or when it's running
# but lacks the specific model the integration tests need. Probing only
# server reachability is not enough: on a machine running Ollama with a
# different model set installed, the tests would hard-fail with an
# uncaught 404 from /api/chat instead of skipping cleanly.
# ---------------------------------------------------------------------------

# Model the requires_ollama integration tests hardcode (tests/test_agents.py
# TestLLMAgentIntegration). Keep in sync if those tests change model.
_REQUIRED_OLLAMA_MODEL = "gemma3:4b"


def _ollama_status() -> tuple[bool, bool]:
    """Probe Ollama server once and check whether the required model is pulled.

    Returns:
        (server_up, model_present)
    """
    try:
        import requests
        resp = requests.get("http://localhost:11434/api/tags", timeout=2)
        if resp.status_code != 200:
            return False, False
        models = {m.get("name", "") for m in resp.json().get("models", [])}
        # Ollama tag names may include a suffix (e.g. "gemma3:4b" exactly, or
        # with a digest); match on the "name:tag" prefix to be tolerant.
        model_present = any(
            name == _REQUIRED_OLLAMA_MODEL or name.startswith(f"{_REQUIRED_OLLAMA_MODEL}-")
            for name in models
        )
        return True, model_present
    except Exception:
        return False, False


_OLLAMA_STATUS: tuple[bool, bool] | None = None


def pytest_collection_modifyitems(config, items):
    """Auto-skip tests marked `requires_ollama` when Ollama is not running

    or the required model isn't pulled, so the suite degrades to a clean
    skip rather than a false-negative failure in any environment where
    Ollama runs a different model set.
    """
    global _OLLAMA_STATUS  # noqa: PLW0603
    if _OLLAMA_STATUS is None:
        _OLLAMA_STATUS = _ollama_status()

    server_up, model_present = _OLLAMA_STATUS

    if server_up and model_present:
        return  # Ollama is up and has the required model — run all tests

    if not server_up:
        reason = "Ollama not running at localhost:11434"
    else:
        reason = f"Ollama running but model '{_REQUIRED_OLLAMA_MODEL}' not pulled"

    skip_marker = pytest.mark.skip(reason=reason)
    for item in items:
        if "requires_ollama" in item.keywords:
            item.add_marker(skip_marker)

# Try to import DataGenerator, preventing import errors if src is not yet importable or during collection  # noqa: E501
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
