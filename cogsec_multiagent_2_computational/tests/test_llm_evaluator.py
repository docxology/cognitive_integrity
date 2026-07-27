"""Tests for src/evaluation/llm_evaluator.py.

Covers:
- DEMO_ATTACKS constant: structure, types, required fields.
- run_llm_evaluation: error path when Ollama is unreachable (RuntimeError).
  The happy path is skipped when Ollama is not running.

No mocks — Ollama availability is detected at runtime via conftest.
HTTP error scenarios use a simple stub response class instead of MagicMock.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
import requests

from evaluation.llm_evaluator import DEMO_ATTACKS, run_llm_evaluation

ROOT = Path(__file__).resolve().parent.parent


def _load_llm_demo_script():
    """Import scripts/run_llm_demo.py as a module without shadowing a package."""
    path = ROOT / "scripts" / "run_llm_demo.py"
    spec = importlib.util.spec_from_file_location("_run_llm_demo_under_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

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


# ---------------------------------------------------------------------------
# scripts/run_llm_demo.py result schema
#
# The demo script is the *producer* end of the LLM evidence chain. These tests
# pin the property that makes the chain auditable: a run that produced no
# measurements must be machine-distinguishable from a run that measured zero.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def demo():
    """The run_llm_demo script, imported as a module."""
    return _load_llm_demo_script()


def _phase2_block() -> dict:
    return {
        "Claude Code": {
            "detection_rate": 0.6,
            "false_positive_rate": 0.0,
            "n_attacks": 5,
            "true_positives": 3,
            "false_negatives": 2,
            "avg_latency_ms": 15.2,
        },
        "CrewAI": {
            "detection_rate": 0.0,
            "false_positive_rate": 0.0,
            "n_attacks": 5,
            "true_positives": 0,
            "false_negatives": 5,
            "avg_latency_ms": 15.9,
        },
    }


class TestArchitectureSlug:
    """Display names must never leak into the results keys."""

    @pytest.mark.parametrize(
        ("display", "expected"),
        [
            ("Claude Code", "claude_code"),
            ("CrewAI", "crewai"),
            ("LangGraph", "langgraph"),
            ("Auto GPT", "auto_gpt"),
        ],
    )
    def test_slugs(self, demo, display, expected):
        assert demo.architecture_slug(display) == expected


class TestResultPayloads:
    """Both the measured and the not-measured path write the full schema."""

    @pytest.mark.parametrize(
        "status", ["skipped", "ollama_unavailable", "timeout", "error"]
    )
    def test_unavailable_payload_is_schema_complete(self, demo, status):
        payload = demo.build_unavailable_payload(status, "because", "gemma3:4b")
        assert set(demo.RESULT_KEYS) <= set(payload)
        assert payload["status"] == status
        assert payload["reason"] == "because"
        assert payload["multiagent_results"] is None

    def test_unavailable_payload_rejects_a_success_status(self, demo):
        """Positive control: 'ok' cannot be smuggled through the outage path."""
        with pytest.raises(ValueError, match="not one of the unavailable statuses"):
            demo.build_unavailable_payload("ok", "because", "gemma3:4b")

    def test_success_payload_is_schema_complete_and_slug_keyed(self, demo):
        payload = demo.build_success_payload(
            {
                "phase1_baseline": [],
                "phase2_architectures": _phase2_block(),
                "phase3_comparison": {},
            },
            "gemma3:4b",
        )
        assert set(demo.RESULT_KEYS) <= set(payload)
        assert payload["status"] == "ok"
        assert sorted(payload["multiagent_results"]) == ["claude_code", "crewai"]
        assert payload["multiagent_results"]["claude_code"] == {
            "detection_rate": 0.6,
            "true_positives": 3,
            "false_negatives": 2,
            "total": 5,
            "false_positive_rate": 0.0,
            "avg_latency_ms": 15.2,
        }

    def test_measured_zero_survives_as_zero(self, demo):
        """A real 0% detection rate is written, not dropped."""
        payload = demo.build_success_payload(
            {"phase2_architectures": _phase2_block()}, "gemma3:4b"
        )
        crewai = payload["multiagent_results"]["crewai"]
        assert crewai["detection_rate"] == 0.0
        assert crewai["total"] == 5

    def test_write_results_refuses_an_incomplete_payload(self, demo, tmp_path):
        """Positive control for the schema guard."""
        target = tmp_path / "llm_demo_results.json"
        with pytest.raises(ValueError, match="missing keys"):
            demo.write_results(target, {"status": "skipped"})
        assert not target.exists()

        demo.write_results(
            target, demo.build_unavailable_payload("skipped", "not set", "gemma3:4b")
        )
        assert set(demo.RESULT_KEYS) <= set(json.loads(target.read_text()))


class TestProducerConsumerContract:
    """The producer's output must drive the consumer's fail-closed decision."""

    def test_skipped_payload_yields_no_numbers_downstream(self, demo, tmp_path):
        from manuscript.injector import _load_llm_ground_truth

        target = tmp_path / "llm_demo_results.json"
        demo.write_results(
            target,
            demo.build_unavailable_payload(
                "skipped", "COGSEC_RUN_LLM_ANALYSIS not set", "g"
            ),
        )

        values, reason = _load_llm_ground_truth(target)

        assert values is None
        assert "skipped" in reason

    def test_success_payload_is_accepted_downstream(self, demo, tmp_path):
        """Positive control: the same writer's success path IS consumable.

        Before this contract existed the producer wrote 'phase2_architectures'
        while the consumer read 'multiagent_results', so a real run was
        silently replaced by hardcoded 80%/100% defaults.
        """
        from manuscript.injector import _load_llm_ground_truth

        target = tmp_path / "llm_demo_results.json"
        demo.write_results(
            target,
            demo.build_success_payload(
                {"phase2_architectures": _phase2_block()}, "gemma3:4b"
            ),
        )

        values, reason = _load_llm_ground_truth(target)

        assert reason is None
        assert values["llm_claude_dr"] == 0.6
        assert values["llm_crewai_dr"] == 0.0
        assert values["llm_total_n"] == 10
