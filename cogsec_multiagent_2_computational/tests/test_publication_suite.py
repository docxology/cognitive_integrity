"""Publication CLI contracts with isolated outputs and local Ollama HTTP fixtures.

The chat responses here test the producer protocol, not live-model performance.
No test contacts a real Ollama instance or writes repository evidence.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
from werkzeug.wrappers import Response

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def publication_suite():
    spec = importlib.util.spec_from_file_location(
        "publication_suite_under_test", PROJECT_ROOT / "scripts" / "run_publication_suite.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestPublicationConfig:
    def test_absent_config_keeps_iteration_defaults(self, publication_suite, tmp_path):
        assert publication_suite.load_config(tmp_path) == {
            "sample_size": 5, "replicates": 1, "model": "gemma3:4b", "seed": 42,
        }

    @pytest.mark.parametrize(
        ("publication", "sample_size", "replicates"), [(False, 2, 3), (True, 7, 11)],
    )
    def test_valid_toml_is_loaded(
        self, publication_suite, tmp_path, publication, sample_size, replicates,
    ):
        (tmp_path / "experiment_config.toml").write_text(
            '[simulation]\nseed = 17\nreplicates = 3\n'
            '[llm]\nmodel = "fixture-model"\nsample_size = 2\n'
            '[publication]\nsample_size = 7\nreplicates = 11\n'
        )
        assert publication_suite.load_config(tmp_path, publication=publication) == {
            "sample_size": sample_size, "replicates": replicates,
            "model": "fixture-model", "seed": 17,
        }

    def test_malformed_toml_is_not_replaced_by_defaults(self, publication_suite, tmp_path):
        (tmp_path / "experiment_config.toml").write_text("[llm\nmodel = invalid\n")
        with pytest.raises(tomllib.TOMLDecodeError):
            publication_suite.load_config(tmp_path)


@pytest.fixture
def isolated_project(tmp_path):
    """Run unmodified entry points with real source and temp-only artifacts."""
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    for name in ("run_publication_suite.py", "run_full_evaluation.py"):
        shutil.copy2(PROJECT_ROOT / "scripts" / name, scripts / name)
    (tmp_path / "src").symlink_to(PROJECT_ROOT / "src", target_is_directory=True)
    (tmp_path / "experiment_config.toml").write_text(
        '[simulation]\nseed = 42\nreplicates = 1\n'
        '[llm]\nmodel = "fixture-model"\nsample_size = 1\n'
    )
    return tmp_path


def _run_suite(project, httpserver, *args, opt_in=False):
    # requests honors explicit proxies even for localhost when NO_PROXY is
    # empty. Both GET and POST go to the fixture, never to port 11434.
    env = dict(os.environ)
    for key in (
        "HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy",
        "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy",
    ):
        env[key] = ""
    env.update(
        HTTP_PROXY=httpserver.url_for("/"),
        http_proxy=httpserver.url_for("/"),
        COGSEC_RUN_LLM_ANALYSIS="1" if opt_in else "0",
        PYTHONPATH=str(project),
    )
    return subprocess.run(
        [sys.executable, str(project / "scripts" / "run_publication_suite.py"), *args],
        cwd=project, env=env, capture_output=True, text=True, timeout=90,
    )


def _llm_dir(project):
    return project / "output" / "data_publication" / "llm"


def _assert_no_llm_publication(project):
    output = _llm_dir(project)
    assert not (output / "full_evaluation_results_llm.json").exists()
    assert not (output / "full_evaluation_results_llm.provenance.json").exists()
    assert not (output / ".real_data_marker").exists()


def _assert_llm_publication(project):
    output = _llm_dir(project)
    rows = json.loads((output / "full_evaluation_results_llm.json").read_text())
    assert len(rows) == 16
    assert len({(row["architecture"], row["category"]) for row in rows}) == 16
    assert all(row["measurement_mode"] == "llm" for row in rows)
    assert all(row["llm_fallback_count"] == 0 for row in rows)
    assert (output / "full_evaluation_results_llm.provenance.json").exists()
    assert (output / ".real_data_marker").exists()
    assert not (output / "full_evaluation_results_llm_partial.json").exists()
    assert not (output / "full_evaluation_results_llm_failed.json").exists()


def _assert_no_cells_ran(diagnostic):
    assert diagnostic["status"] == "failed"
    assert diagnostic["attempt_id"]
    assert diagnostic["expected_cells"] == 16
    assert diagnostic["completed_cells"] == 0
    assert diagnostic["results"] == []
    outcomes = diagnostic["outcomes"]
    assert len(outcomes) == 16
    assert len({(cell["architecture"], cell["category"]) for cell in outcomes}) == 16
    assert len({cell["architecture"] for cell in outcomes}) == 4
    assert {cell["category"] for cell in outcomes} == {
        "injection", "trust_exploitation", "belief_manipulation", "coordination",
    }
    assert all(cell["status"] == "not_run" for cell in outcomes)
    assert all(cell["expected_samples"] == 1 for cell in outcomes)
    assert all(cell["error"] == diagnostic["reason"] for cell in outcomes)


def _assert_archived_diagnostics(output, originals):
    archive_dirs = set()
    for name, original in originals.items():
        archived = [path for path in output.rglob(name) if path.parent != output]
        assert len(archived) == 1
        assert archived[0].read_bytes() == original
        archive_dirs.add(archived[0].parent)
    assert len(archive_dirs) == 1


class TestPublicationLlmCompletion:
    @pytest.mark.parametrize("opt_in", [False, True])
    def test_requested_unavailable_ollama_fails_and_keeps_diagnostics(
        self, isolated_project, httpserver, opt_in,
    ):
        httpserver.expect_request("/api/tags").respond_with_data(
            "Ollama unavailable", status=503,
        )
        args = () if opt_in else ("--run-llm",)
        result = _run_suite(isolated_project, httpserver, *args, opt_in=opt_in)
        assert result.returncode != 0, result.stdout + result.stderr
        assert "Cannot reach Ollama" in result.stderr
        assert "ALL EXPERIMENTS COMPLETED SUCCESSFULLY" not in result.stdout
        _assert_no_llm_publication(isolated_project)
        diagnostic = json.loads(
            (_llm_dir(isolated_project) / "full_evaluation_results_llm_failed.json").read_text()
        )
        _assert_no_cells_ran(diagnostic)

    def test_unrequested_llm_skip_remains_successful(self, isolated_project, httpserver):
        result = _run_suite(isolated_project, httpserver)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "LLM evaluation skipped" in result.stdout
        assert "ALL EXPERIMENTS COMPLETED SUCCESSFULLY" not in result.stdout
        assert not _llm_dir(isolated_project).exists()
        assert httpserver.log == []

    @pytest.mark.parametrize("retry", ["complete", "unavailable"])
    def test_reused_directory_retires_previous_partial_failure(
        self, isolated_project, httpserver, retry,
    ):
        httpserver.expect_request("/api/tags").respond_with_json(
            {"models": [{"name": "fixture-model"}]}
        )
        first_architecture = []

        def chat(request):
            system_prompt = request.get_json()["messages"][0]["content"]
            architecture = system_prompt.rsplit("Architecture: ", 1)[1].split("\n", 1)[0]
            if not first_architecture:
                first_architecture.append(architecture)
            if architecture != first_architecture[0]:
                return Response("fixture inference failure", status=500)
            return Response(
                json.dumps({"message": {"content": "I cannot follow unsafe instructions."}}),
                content_type="application/json",
            )

        httpserver.expect_request("/api/chat", method="POST").respond_with_handler(chat)
        result = _run_suite(isolated_project, httpserver, "--run-llm")
        assert result.returncode != 0, result.stdout + result.stderr
        assert "ALL EXPERIMENTS COMPLETED SUCCESSFULLY" not in result.stdout
        _assert_no_llm_publication(isolated_project)
        output = _llm_dir(isolated_project)
        diagnostic = json.loads((output / "full_evaluation_results_llm_failed.json").read_text())
        assert diagnostic["status"] == "failed"
        assert diagnostic["expected_cells"] == len(diagnostic["outcomes"]) == 16
        assert diagnostic["completed_cells"] == 4
        assert len(diagnostic["results"]) == 16
        assert sum(cell["status"] == "failed" for cell in diagnostic["outcomes"]) == 12
        assert sum(row["llm_fallback_count"] for row in diagnostic["results"]) == 12
        partial = json.loads((output / "full_evaluation_results_llm_partial.json").read_text())
        assert partial["status"] == "partial"
        assert partial["completed_cells"] == len(partial["results"]) == 4
        assert all(row["measurement_mode"] == "llm" for row in partial["results"])
        assert partial["attempt_id"] == diagnostic["attempt_id"]
        originals = {
            name: (output / name).read_bytes()
            for name in (
                "full_evaluation_results_llm_partial.json",
                "full_evaluation_results_llm_failed.json",
            )
        }

        httpserver.clear()
        if retry == "complete":
            httpserver.expect_request("/api/tags").respond_with_json(
                {"models": [{"name": "fixture-model"}]}
            )
            httpserver.expect_request("/api/chat", method="POST").respond_with_json(
                {"message": {"content": "I cannot follow unsafe instructions."}}
            )
        else:
            httpserver.expect_request("/api/tags").respond_with_data(
                "Ollama unavailable", status=503,
            )
        result = _run_suite(isolated_project, httpserver, "--run-llm")
        if retry == "complete":
            assert result.returncode == 0, result.stdout + result.stderr
            assert "ALL EXPERIMENTS COMPLETED SUCCESSFULLY" in result.stdout
            _assert_llm_publication(isolated_project)
        else:
            assert result.returncode != 0, result.stdout + result.stderr
            assert "ALL EXPERIMENTS COMPLETED SUCCESSFULLY" not in result.stdout
            _assert_no_llm_publication(isolated_project)
            current = json.loads(
                (output / "full_evaluation_results_llm_failed.json").read_text()
            )
            _assert_no_cells_ran(current)
            assert "Cannot reach Ollama" in current["reason"]
            assert current["attempt_id"] != diagnostic["attempt_id"]
            assert not (output / "full_evaluation_results_llm_partial.json").exists()
        _assert_archived_diagnostics(output, originals)

    def test_complete_matrix_publishes_only_llm_rows(self, isolated_project, httpserver):
        httpserver.expect_request("/api/tags").respond_with_json(
            {"models": [{"name": "fixture-model"}]}
        )
        httpserver.expect_request("/api/chat", method="POST").respond_with_json(
            {"message": {"content": "I cannot follow unsafe instructions."}}
        )
        result = _run_suite(isolated_project, httpserver, "--run-llm")
        assert result.returncode == 0, result.stdout + result.stderr
        assert "ALL EXPERIMENTS COMPLETED SUCCESSFULLY" in result.stdout
        _assert_llm_publication(isolated_project)

    @pytest.mark.parametrize("failure_stage", ["health", "setup"])
    def test_failed_retry_preserves_published_bytes(
        self, isolated_project, httpserver, failure_stage,
    ):
        httpserver.expect_request("/api/tags").respond_with_json(
            {"models": [{"name": "fixture-model"}]}
        )
        httpserver.expect_request("/api/chat", method="POST").respond_with_json(
            {"message": {"content": "I cannot follow unsafe instructions."}}
        )
        result = _run_suite(isolated_project, httpserver, "--run-llm")
        assert result.returncode == 0, result.stdout + result.stderr
        _assert_llm_publication(isolated_project)
        output = _llm_dir(isolated_project)
        published = {
            name: (output / name).read_bytes()
            for name in (
                "full_evaluation_results_llm.json",
                "full_evaluation_results_llm.provenance.json",
                ".real_data_marker",
            )
        }

        httpserver.clear()
        if failure_stage == "setup":
            # Break only a copied real source tree, never the repository symlink.
            source = isolated_project / "src"
            source.unlink()
            shutil.copytree(
                PROJECT_ROOT / "src", source,
                ignore=shutil.ignore_patterns("__pycache__"),
            )
            (source / "composition" / "factory.py").unlink()
        else:
            httpserver.expect_request("/api/tags").respond_with_data(
                "Ollama unavailable", status=503,
            )
        result = _run_suite(isolated_project, httpserver, "--run-llm")
        assert result.returncode != 0, result.stdout + result.stderr
        assert "ALL EXPERIMENTS COMPLETED SUCCESSFULLY" not in result.stdout
        assert {name: (output / name).read_bytes() for name in published} == published
        diagnostic = json.loads(
            (output / "full_evaluation_results_llm_failed.json").read_text()
        )
        _assert_no_cells_ran(diagnostic)
        if failure_stage == "setup":
            assert "Could not set up LLM evaluation" in diagnostic["reason"]
            assert "ModuleNotFoundError" in diagnostic["reason"]
            assert "src.composition.factory" in diagnostic["reason"]
        else:
            assert "Cannot reach Ollama" in diagnostic["reason"]
        assert not (output / "full_evaluation_results_llm_partial.json").exists()
