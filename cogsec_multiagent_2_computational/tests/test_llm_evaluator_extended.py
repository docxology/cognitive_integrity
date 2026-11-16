"""LLM matrix completion contracts, using real systems and local HTTP fixtures."""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest
import requests

from src.evaluation.llm_evaluator import (
    DEMO_ATTACKS,
    LLMEvaluationError,
    run_llm_evaluation,
)
from src.evaluation.runner import ExperimentResult


class _Adapter:
    def __init__(self, name="TestArch"):
        self.profile = SimpleNamespace(name=name)

    def create_trust_matrix(self, n_agents):
        return np.ones((n_agents, n_agents)) * 0.5

    def get_communication_graph(self, n_agents):
        return {}

    def get_agent_roles(self, n_agents):
        return ["assistant"] * n_agents


class _Runner:
    """An injected runner that records calls and returns real result objects."""

    def __init__(self):
        self.calls = []

    def run_single_llm(self, adapter, samples, pipeline, system):
        self.calls.append((adapter, list(samples), pipeline, system))
        n_attacks = sum(bool(sample.get("is_attack", True)) for sample in samples)
        return ExperimentResult(
            architecture=adapter.profile.name,
            attack_category=samples[0].get("category", "unknown"),
            n_attacks=n_attacks,
            true_positives=n_attacks,
            false_negatives=0,
            false_positives=0,
            true_negatives=len(samples) - n_attacks,
            detection_rate=1.0 if n_attacks else 0.0,
            false_positive_rate=0.0,
            avg_latency_ms=1.0,
            measurement_mode="llm",
        )


@pytest.fixture
def ollama_endpoint(httpserver, monkeypatch):
    """Redirect only the external health request to a real local HTTP server."""
    real_get = requests.get

    def get_tags(url, **kwargs):
        assert url == "http://localhost:11434/api/tags"
        return real_get(httpserver.url_for("/api/tags"), **kwargs)

    monkeypatch.setattr(requests, "get", get_tags)
    return httpserver


@pytest.fixture
def available_ollama(ollama_endpoint):
    ollama_endpoint.expect_request("/api/tags").respond_with_json(
        {"models": [{"name": "gemma3:4b"}]}
    )
    return ollama_endpoint


class TestRunLlmEvaluationMainLoop:
    @pytest.mark.parametrize(
        ("adapters", "corpus", "sample_size"),
        [
            ([], {"attack": DEMO_ATTACKS[:2]}, 5),
            ([_Adapter()], {}, 5),
            ([_Adapter()], {"attack": DEMO_ATTACKS[:2]}, 0),
            ([_Adapter()], {"attack": DEMO_ATTACKS[:2]}, -1),
        ],
    )
    def test_empty_matrix_is_not_success(self, adapters, corpus, sample_size):
        runner = _Runner()
        with pytest.raises(LLMEvaluationError, match="requires adapters") as caught:
            run_llm_evaluation(
                adapters, corpus, None, runner, sample_size=sample_size,
            )
        assert caught.value.results == []
        assert runner.calls == []

    def test_system_creation_failure_is_not_silent_success(self, available_ollama):
        class BrokenAdapter(_Adapter):
            def create_trust_matrix(self, n_agents):
                raise RuntimeError("Model not loaded")

        runner = _Runner()
        with pytest.raises(LLMEvaluationError, match="could not create LLM system") as caught:
            run_llm_evaluation(
                [BrokenAdapter("Broken"), _Adapter("Good")],
                {"cat1": DEMO_ATTACKS[:2], "cat2": DEMO_ATTACKS[2:4]},
                None, runner,
            )
        assert [cell["status"] for cell in caught.value.outcomes] == [
            "failed", "failed", "complete", "complete",
        ]
        assert len(runner.calls) == len(caught.value.results) == 2

    def test_run_single_llm_failure_is_not_silent_success(self, available_ollama):
        class FailingRunner(_Runner):
            def run_single_llm(self, *args):
                result = super().run_single_llm(*args)
                if len(self.calls) == 1:
                    raise RuntimeError("Eval failed")
                return result

        runner = FailingRunner()
        with pytest.raises(LLMEvaluationError, match="Eval failed") as caught:
            run_llm_evaluation(
                [_Adapter("ArchA"), _Adapter("ArchB")],
                {"cat1": DEMO_ATTACKS[:2], "cat2": DEMO_ATTACKS[2:4]},
                None, runner,
            )
        assert len(runner.calls) == 4
        assert len(caught.value.results) == 3
        assert [cell["status"] for cell in caught.value.outcomes] == [
            "failed", "complete", "complete", "complete",
        ]

    def test_successful_run_appends_result(self, available_ollama):
        results = run_llm_evaluation(
            [_Adapter("ArchGood")], {"cat1": DEMO_ATTACKS[:2]}, None, _Runner(),
        )
        assert len(results) == 1
        assert results[0].detection_rate == 1.0
        assert results[0].architecture == "ArchGood"
        assert results[0].category == "cat1"

    @pytest.mark.parametrize("fallback_count", [1, 2])
    def test_fallback_result_is_not_returned_as_llm_success(
        self, available_ollama, fallback_count,
    ):
        class FallbackRunner(_Runner):
            def run_single_llm(self, *args):
                return replace(
                    super().run_single_llm(*args),
                    llm_fallback_count=fallback_count,
                    measurement_mode="mixed" if fallback_count == 1 else "pipeline",
                )

        with pytest.raises(LLMEvaluationError, match="fell back") as caught:
            run_llm_evaluation(
                [_Adapter()], {"cat1": DEMO_ATTACKS[:2]}, None, FallbackRunner(),
            )
        assert caught.value.results[0].llm_fallback_count == fallback_count
        assert caught.value.outcomes[0]["status"] == "failed"

    @pytest.mark.parametrize("mode", ["parametric", "pipeline", "mixed", "real"])
    def test_non_llm_provenance_is_not_success(self, available_ollama, mode):
        class WrongModeRunner(_Runner):
            def run_single_llm(self, *args):
                return replace(super().run_single_llm(*args), measurement_mode=mode)

        with pytest.raises(LLMEvaluationError, match="not LLM evidence"):
            run_llm_evaluation(
                [_Adapter()], {"cat1": DEMO_ATTACKS[:2]}, None, WrongModeRunner(),
            )

    @pytest.mark.parametrize("returned_samples", [0, 1])
    def test_empty_or_partial_cell_result_is_not_success(
        self, available_ollama, returned_samples,
    ):
        class PartialRunner(_Runner):
            def run_single_llm(self, *args):
                return replace(
                    super().run_single_llm(*args),
                    n_attacks=returned_samples, true_positives=returned_samples,
                )

        with pytest.raises(LLMEvaluationError, match="incomplete") as caught:
            run_llm_evaluation(
                [_Adapter()], {"cat1": DEMO_ATTACKS[:2]}, None, PartialRunner(),
            )
        assert caught.value.outcomes[0]["observed_samples"] == returned_samples
        assert caught.value.results[0].n_attacks == returned_samples

    def test_empty_category_does_not_hide_other_cells(self, available_ollama):
        runner = _Runner()
        with pytest.raises(LLMEvaluationError, match="no samples") as caught:
            run_llm_evaluation(
                [_Adapter()], {"empty": [], "populated": DEMO_ATTACKS[:1]},
                None, runner,
            )
        assert [cell["status"] for cell in caught.value.outcomes] == [
            "failed", "complete",
        ]
        assert len(runner.calls) == 1

    def test_multiple_adapters_multiple_categories(self, available_ollama):
        results = run_llm_evaluation(
            [_Adapter("ArchA"), _Adapter("ArchB")],
            {"cat1": DEMO_ATTACKS[:2], "cat2": DEMO_ATTACKS[2:4]},
            None, _Runner(),
        )
        assert {(r.architecture, r.category) for r in results} == {
            ("ArchA", "cat1"), ("ArchA", "cat2"),
            ("ArchB", "cat1"), ("ArchB", "cat2"),
        }

    def test_sample_size_subsampling(self, available_ollama):
        runner = _Runner()
        results = run_llm_evaluation(
            [_Adapter()], {"cat1": DEMO_ATTACKS * 3}, None, runner,
            sample_size=3, seed=42,
        )
        assert len(results) == 1
        assert len(runner.calls[0][1]) == 3

    def test_save_callback_called_incrementally(self, available_ollama):
        callback_calls = []

        def save(results, final):
            callback_calls.append((len(results), final))

        run_llm_evaluation(
            [_Adapter()], {"cat1": DEMO_ATTACKS[:2], "cat2": DEMO_ATTACKS[2:4]},
            None, _Runner(), save_callback=save,
        )
        assert callback_calls == [(1, False), (2, False)]

    def test_custom_model_and_seed(self, available_ollama):
        runner = _Runner()
        run_llm_evaluation(
            [_Adapter()], {"cat1": DEMO_ATTACKS[:1]}, None, runner,
            model="llama3:8b", seed=99,
        )
        config = runner.calls[0][3].agents[0].config
        assert config.model == "llama3:8b"
        assert config.seed == 99

    def test_samples_not_subsampled_when_at_limit(self, available_ollama):
        runner = _Runner()
        run_llm_evaluation(
            [_Adapter()], {"cat1": DEMO_ATTACKS[:3]}, None, runner, sample_size=10,
        )
        assert runner.calls[0][1] == DEMO_ATTACKS[:3]


class TestRunLlmEvaluationWithHttpServer:
    def test_ok_response_from_httpserver_proceeds(self, available_ollama):
        results = run_llm_evaluation(
            [_Adapter()], {"cat1": DEMO_ATTACKS[:1]}, None, _Runner(),
        )
        assert len(results) == 1

    def test_500_from_httpserver_raises_runtime_error(self, ollama_endpoint):
        ollama_endpoint.expect_request("/api/tags").respond_with_data(
            "Internal Server Error", status=500,
        )
        with pytest.raises(LLMEvaluationError, match="Cannot reach Ollama") as caught:
            run_llm_evaluation(
                [_Adapter("ArchA"), _Adapter("ArchB")],
                {"cat1": DEMO_ATTACKS[:1], "cat2": DEMO_ATTACKS[1:2]},
                None, _Runner(),
            )
        assert caught.value.results == []
        assert len(caught.value.outcomes) == 4
        assert all(cell["status"] == "not_run" for cell in caught.value.outcomes)
