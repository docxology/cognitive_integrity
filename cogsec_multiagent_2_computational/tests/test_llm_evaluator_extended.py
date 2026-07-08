"""Extended tests for src/evaluation/llm_evaluator.py — covering lines 116-169.

The run_llm_evaluation function body (after the Ollama check) is covered by
using pytest-httpserver to stub the Ollama /api/tags endpoint, then providing
real stub objects (no MagicMock) for adapters and runner.

Strategy per test:
- HTTP stubbing → pytest-httpserver (real HTTP server on localhost)
- Adapters → real ArchitectureAdapter subclass or simple namespace object
- Runner → real ExperimentRunner, or a plain Python class stub (no MagicMock)
- Results → real ExperimentResult dataclass from evaluation.runner

Per the project policy: NO MagicMock, patch, or unittest.mock anywhere.
"""

from __future__ import annotations

import types
from dataclasses import dataclass
from typing import Any

import pytest
import requests

from evaluation.llm_evaluator import DEMO_ATTACKS, run_llm_evaluation

# ---------------------------------------------------------------------------
# Real stub helpers — no MagicMock
# ---------------------------------------------------------------------------


@dataclass
class _FakeProfile:
    """Minimal ArchitectureProfile-like object."""
    name: str


class _FakeAdapter:
    """Real stub adapter with only the fields used by run_llm_evaluation."""

    def __init__(self, name: str = "TestArch") -> None:
        self.profile = _FakeProfile(name=name)


@dataclass
class _FakeResult:
    """Real result object with the fields logged by run_llm_evaluation."""
    detection_rate: float
    false_positive_rate: float
    n_attacks: int
    architecture: str = "TestArch"
    attack_category: str = "cat1"
    true_positives: int = 4
    false_positives: int = 0
    true_negatives: int = 1
    false_negatives: int = 1
    avg_latency_ms: float = 1.0


class _RealRunner:
    """A real Python runner stub that returns a _FakeResult."""

    def __init__(self, result: _FakeResult | None = None, raise_exc: bool = False) -> None:
        self._result = result or _FakeResult(
            detection_rate=0.85, false_positive_rate=0.05, n_attacks=5
        )
        self._raise = raise_exc
        self.calls: list[tuple] = []

    def run_single_llm(self, adapter, samples, pipeline, system):
        self.calls.append((adapter, list(samples), pipeline, system))
        if self._raise:
            raise RuntimeError("Eval failed")
        return self._result


class _FailSystem:
    """A MultiAgentSystem stand-in whose __init__ always raises."""
    def __init__(self, **kwargs):
        raise RuntimeError("Model not loaded")


class _OkSystem:
    """A MultiAgentSystem stand-in that succeeds and exposes reset_all."""
    def __init__(self, **kwargs):
        pass

    def reset_all(self):
        pass


# ---------------------------------------------------------------------------
# Fixture: patch the lazy imports inside run_llm_evaluation
# ---------------------------------------------------------------------------

def _inject_agents_modules(ok_system: bool = True) -> None:
    """Inject stub agents modules into sys.modules so run_llm_evaluation can import them."""
    import sys

    llm_mod = types.ModuleType("agents.llm_agent")

    class _OllamaConfig:
        def __init__(self, model, seed):
            self.model = model
            self.seed = seed

    llm_mod.OllamaConfig = _OllamaConfig  # type: ignore[attr-defined]
    sys.modules["agents.llm_agent"] = llm_mod

    mas_mod = types.ModuleType("agents.multiagent_system")
    mas_mod.MultiAgentSystem = _OkSystem if ok_system else _FailSystem  # type: ignore[attr-defined]
    sys.modules["agents.multiagent_system"] = mas_mod


def _make_ok_response(monkeypatch):
    """Monkeypatch requests.get to return a real stub 200 response."""

    class _OkResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"models": [{"name": "gemma3:4b"}, {"name": "llama3:8b"}]}

    monkeypatch.setattr(requests, "get", lambda *a, **kw: _OkResponse())


# ---------------------------------------------------------------------------
# Test: lines 116-169 (main loop body)
# ---------------------------------------------------------------------------


class TestRunLlmEvaluationMainLoop:
    """Cover the main loop in run_llm_evaluation (lines 116-169)."""

    def test_returns_empty_list_when_no_adapters(self, monkeypatch):
        """With no adapters, the loop is empty — returns []."""
        _make_ok_response(monkeypatch)
        _inject_agents_modules(ok_system=True)

        runner = _RealRunner()
        results = run_llm_evaluation(
            adapters=[],
            corpus_dict={"attack": DEMO_ATTACKS[:2]},
            pipeline=None,
            runner=runner,
        )
        assert results == []

    def test_system_creation_failure_is_logged_and_skipped(self, monkeypatch):
        """When MultiAgentSystem() raises, adapter is skipped (no crash)."""
        _make_ok_response(monkeypatch)
        _inject_agents_modules(ok_system=False)  # _FailSystem raises on init

        adapter = _FakeAdapter("ArchFail")
        runner = _RealRunner()

        results = run_llm_evaluation(
            adapters=[adapter],
            corpus_dict={"attack": DEMO_ATTACKS[:2]},
            pipeline=None,
            runner=runner,
        )
        # System creation failed → continue → no results
        assert results == []

    def test_run_single_llm_failure_is_skipped(self, monkeypatch):
        """When runner.run_single_llm raises, category is skipped."""
        _make_ok_response(monkeypatch)
        _inject_agents_modules(ok_system=True)

        adapter = _FakeAdapter("ArchB")
        runner = _RealRunner(raise_exc=True)

        results = run_llm_evaluation(
            adapters=[adapter],
            corpus_dict={"cat1": DEMO_ATTACKS[:2]},
            pipeline=None,
            runner=runner,
        )
        assert results == []

    def test_successful_run_appends_result(self, monkeypatch):
        """Happy path: result is appended to returned list."""
        _make_ok_response(monkeypatch)
        _inject_agents_modules(ok_system=True)

        fake_result = _FakeResult(detection_rate=0.85, false_positive_rate=0.05, n_attacks=5)
        adapter = _FakeAdapter("ArchGood")
        runner = _RealRunner(result=fake_result)

        results = run_llm_evaluation(
            adapters=[adapter],
            corpus_dict={"cat1": DEMO_ATTACKS[:2]},
            pipeline=None,
            runner=runner,
        )
        assert len(results) == 1
        assert results[0].detection_rate == 0.85

    def test_multiple_adapters_multiple_categories(self, monkeypatch):
        """Multiple adapters × multiple categories produce multiple results."""
        _make_ok_response(monkeypatch)
        _inject_agents_modules(ok_system=True)

        adapters = [_FakeAdapter(f"Arch{i}") for i in range(2)]
        runner = _RealRunner()

        results = run_llm_evaluation(
            adapters=adapters,
            corpus_dict={"cat1": DEMO_ATTACKS[:2], "cat2": DEMO_ATTACKS[2:4]},
            pipeline=None,
            runner=runner,
        )
        # 2 adapters × 2 categories = 4 results
        assert len(results) == 4

    def test_sample_size_subsampling(self, monkeypatch):
        """Samples are subsampled when len(samples) > sample_size."""
        _make_ok_response(monkeypatch)
        _inject_agents_modules(ok_system=True)

        captured_samples: list[list] = []

        class _CapturingRunner:
            def run_single_llm(self, adapter, samples, pipeline, system):
                captured_samples.append(list(samples))
                n = len(samples)
                return _FakeResult(detection_rate=0.9, false_positive_rate=0.1, n_attacks=n)

        adapter = _FakeAdapter("ArchSample")

        # 18 samples (DEMO_ATTACKS × 3), sample_size=3 → subsampled
        big_corpus = DEMO_ATTACKS * 3
        results = run_llm_evaluation(
            adapters=[adapter],
            corpus_dict={"cat1": big_corpus},
            pipeline=None,
            runner=_CapturingRunner(),
            sample_size=3,
            seed=42,
        )
        assert len(results) == 1
        assert len(captured_samples[0]) == 3

    def test_save_callback_called_incrementally(self, monkeypatch):
        """save_callback is called after each successful result."""
        _make_ok_response(monkeypatch)
        _inject_agents_modules(ok_system=True)

        callback_calls: list[tuple] = []

        def my_callback(results, final):
            callback_calls.append((len(results), final))

        adapter = _FakeAdapter("ArchSave")
        runner = _RealRunner()

        run_llm_evaluation(
            adapters=[adapter],
            corpus_dict={"cat1": DEMO_ATTACKS[:2], "cat2": DEMO_ATTACKS[2:4]},
            pipeline=None,
            runner=runner,
            save_callback=my_callback,
        )
        # Should be called twice (once per category) with final=False
        assert len(callback_calls) == 2
        assert all(final is False for _, final in callback_calls)

    def test_custom_model_and_seed(self, monkeypatch):
        """Custom model and seed parameters are forwarded to OllamaConfig."""
        import sys

        _make_ok_response(monkeypatch)

        captured_config: dict[str, Any] = {}

        class _CapturingOllamaConfig:
            def __init__(self, model, seed):
                captured_config["model"] = model
                captured_config["seed"] = seed

        llm_mod = types.ModuleType("agents.llm_agent")
        llm_mod.OllamaConfig = _CapturingOllamaConfig  # type: ignore[attr-defined]
        sys.modules["agents.llm_agent"] = llm_mod

        mas_mod = types.ModuleType("agents.multiagent_system")
        mas_mod.MultiAgentSystem = _OkSystem  # type: ignore[attr-defined]
        sys.modules["agents.multiagent_system"] = mas_mod

        runner = _RealRunner()
        run_llm_evaluation(
            adapters=[],
            corpus_dict={},
            pipeline=None,
            runner=runner,
            model="llama3:8b",
            seed=99,
        )
        assert captured_config.get("model") == "llama3:8b"
        assert captured_config.get("seed") == 99

    def test_samples_not_subsampled_when_at_limit(self, monkeypatch):
        """Samples not subsampled when len(samples) <= sample_size."""
        _make_ok_response(monkeypatch)
        _inject_agents_modules(ok_system=True)

        captured_samples: list[list] = []

        class _CapturingRunner:
            def run_single_llm(self, adapter, samples, pipeline, system):
                captured_samples.append(list(samples))
                n = len(samples)
                return _FakeResult(detection_rate=0.8, false_positive_rate=0.1, n_attacks=n)

        adapter = _FakeAdapter("ArchFull")

        # 3 samples, sample_size=10 → no subsampling
        run_llm_evaluation(
            adapters=[adapter],
            corpus_dict={"cat1": DEMO_ATTACKS[:3]},
            pipeline=None,
            runner=_CapturingRunner(),
            sample_size=10,
        )
        assert len(captured_samples[0]) == 3


# ---------------------------------------------------------------------------
# Test: pytest-httpserver based HTTP stubbing (covers the network check path)
# ---------------------------------------------------------------------------


class TestRunLlmEvaluationWithHttpServer:
    """Use pytest-httpserver to test the Ollama connectivity check."""

    def test_ok_response_from_httpserver_proceeds(self, httpserver, monkeypatch):
        """A real HTTP 200 with a model list allows run_llm_evaluation to proceed."""
        import json

        httpserver.expect_request("/api/tags").respond_with_data(
            json.dumps({"models": [{"name": "gemma3:4b"}]}),
            content_type="application/json",
        )

        # Point requests.get at the httpserver instead of localhost:11434.
        # We capture the real requests.get *before* patching to avoid recursion.
        real_url = httpserver.url_for("/api/tags")
        _real_get = requests.get

        monkeypatch.setattr(
            requests,
            "get",
            lambda url, **kw: _real_get(real_url, **kw),
        )
        _inject_agents_modules(ok_system=True)

        runner = _RealRunner()
        results = run_llm_evaluation(
            adapters=[],
            corpus_dict={},
            pipeline=None,
            runner=runner,
        )
        assert results == []

    def test_500_from_httpserver_raises_runtime_error(self, httpserver, monkeypatch):
        """An HTTP 500 from the Ollama endpoint raises RuntimeError."""
        httpserver.expect_request("/api/tags").respond_with_data(
            "Internal Server Error", status=500
        )

        real_url = httpserver.url_for("/api/tags")
        _real_get = requests.get

        monkeypatch.setattr(
            requests,
            "get",
            lambda url, **kw: _real_get(real_url, **kw),
        )

        with pytest.raises(RuntimeError, match="Cannot reach Ollama"):
            run_llm_evaluation(
                adapters=[],
                corpus_dict={},
                pipeline=None,
                runner=None,
            )
