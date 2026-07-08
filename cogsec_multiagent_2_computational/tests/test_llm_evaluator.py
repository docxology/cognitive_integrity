"""Tests for src/evaluation/llm_evaluator.py.

Covers:
- DEMO_ATTACKS constant: structure, types, required fields.
- run_llm_evaluation: error path when Ollama is unreachable (RuntimeError).
  The happy path is skipped when Ollama is not running.

No mocks — Ollama availability is detected at runtime via conftest.
HTTP error scenarios use a simple stub response class instead of MagicMock.
"""

from __future__ import annotations

import pytest
import requests

from evaluation.llm_evaluator import DEMO_ATTACKS, run_llm_evaluation

# ---------------------------------------------------------------------------
# DEMO_ATTACKS constant
# ---------------------------------------------------------------------------


class TestDemoAttacks:
    """Tests for the DEMO_ATTACKS module-level constant."""

    def test_is_list(self):
        assert isinstance(DEMO_ATTACKS, list)

    def test_non_empty(self):
        assert len(DEMO_ATTACKS) > 0

    def test_each_entry_is_dict(self):
        for entry in DEMO_ATTACKS:
            assert isinstance(entry, dict), f"Non-dict entry: {entry!r}"

    def test_required_keys_present(self):
        required = {"category", "content", "is_attack", "label"}
        for entry in DEMO_ATTACKS:
            missing = required - set(entry.keys())
            assert not missing, f"Missing keys {missing} in {entry}"

    def test_category_is_string(self):
        for entry in DEMO_ATTACKS:
            assert isinstance(entry["category"], str)

    def test_content_is_non_empty_string(self):
        for entry in DEMO_ATTACKS:
            assert isinstance(entry["content"], str)
            assert len(entry["content"].strip()) > 0

    def test_is_attack_is_bool(self):
        for entry in DEMO_ATTACKS:
            assert isinstance(entry["is_attack"], bool)

    def test_label_is_non_empty_string(self):
        for entry in DEMO_ATTACKS:
            assert isinstance(entry["label"], str)
            assert len(entry["label"].strip()) > 0

    def test_has_at_least_one_attack_and_one_benign(self):
        attacks = [e for e in DEMO_ATTACKS if e["is_attack"]]
        benign = [e for e in DEMO_ATTACKS if not e["is_attack"]]
        assert len(attacks) >= 1, "Expected at least one attack sample"
        assert len(benign) >= 1, "Expected at least one benign sample"

    def test_categories_are_diverse(self):
        """At least two distinct categories are represented."""
        categories = {e["category"] for e in DEMO_ATTACKS}
        assert len(categories) >= 2

    def test_benign_category_present(self):
        categories = {e["category"] for e in DEMO_ATTACKS}
        assert "benign" in categories


# ---------------------------------------------------------------------------
# run_llm_evaluation — error path when Ollama is unreachable
# ---------------------------------------------------------------------------


class TestRunLlmEvaluationErrorPath:
    """Verify run_llm_evaluation raises RuntimeError when Ollama is unreachable."""

    def test_raises_runtime_error_when_ollama_unreachable(self, monkeypatch):
        """Simulate Ollama being unreachable by monkeypatching requests.get."""

        def _fail(*args, **kwargs):
            raise requests.exceptions.ConnectionError("simulated connection error")

        monkeypatch.setattr(requests, "get", _fail)

        # Dummy args — should raise before using them
        with pytest.raises(RuntimeError, match="Cannot reach Ollama"):
            run_llm_evaluation(
                adapters=[],
                corpus_dict={},
                pipeline=None,
                runner=None,
            )

    def test_raises_runtime_error_on_http_error(self, monkeypatch):
        """Simulate a non-200 HTTP response from Ollama using a real stub class."""

        class _ErrorResponse:
            """Minimal stub that raises HTTPError on raise_for_status."""

            def raise_for_status(self):
                raise requests.HTTPError("503 Service Unavailable")

            def json(self):
                return {}

        monkeypatch.setattr(requests, "get", lambda *a, **kw: _ErrorResponse())

        with pytest.raises(RuntimeError, match="Cannot reach Ollama"):
            run_llm_evaluation(
                adapters=[],
                corpus_dict={},
                pipeline=None,
                runner=None,
            )

    def test_raises_runtime_error_on_timeout(self, monkeypatch):
        """Simulate a timeout from Ollama."""

        def _timeout(*args, **kwargs):
            raise requests.exceptions.Timeout("timed out")

        monkeypatch.setattr(requests, "get", _timeout)

        with pytest.raises(RuntimeError, match="Cannot reach Ollama"):
            run_llm_evaluation(
                adapters=[],
                corpus_dict={},
                pipeline=None,
                runner=None,
            )
