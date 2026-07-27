"""Tests for data-backed manuscript value injection.

The module under test is an *evidence chain*: every number it writes into the
manuscript must come from a measurement on disk. These tests therefore pair
each "the good input works" assertion with a positive control that constructs
the violating input and proves the code refuses it. A test that would stay
green if the fail-closed logic were deleted is worthless here.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from manuscript.injector import (
    GroundTruthUnavailableError,
    InjectionPatternError,
    InjectionReport,
    inject_ablation,
    inject_abstract,
    inject_all,
    inject_conclusion,
    inject_discussion,
    inject_experimental_setup,
    inject_parametric_supplement,
    inject_results,
    inject_statistical,
    is_available,
    load_ground_truth,
)

ALL_INJECTORS = (
    inject_abstract,
    inject_results,
    inject_ablation,
    inject_discussion,
    inject_experimental_setup,
    inject_conclusion,
    inject_statistical,
    inject_parametric_supplement,
)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2))


def _llm_payload() -> dict:
    """A schema-complete, internally consistent LLM results payload."""
    return {
        "schema_version": 1,
        "status": "ok",
        "reason": None,
        "model": "gemma3:4b",
        "multiagent_results": {
            "claude_code": {
                "detection_rate": 0.80,
                "true_positives": 4,
                "false_negatives": 1,
                "total": 5,
            },
            "crewai": {
                "detection_rate": 1.00,
                "true_positives": 5,
                "false_negatives": 0,
                "total": 5,
            },
        },
    }


def _write_required_data(data_dir: Path, *, include_optional: bool = True) -> None:
    data_dir.mkdir(exist_ok=True)
    _write_json(
        data_dir / "full_evaluation_results.json",
        [
            {"architecture": "AutoGPT", "detection_rate": 0.96},
            {"architecture": "AutoGPT", "detection_rate": 0.98},
            {"architecture": "Claude Code", "detection_rate": 1.0},
            {"architecture": "CrewAI", "detection_rate": 1.0},
        ],
    )
    _write_json(
        data_dir / "ablation_results.json",
        {
            "component_removal": [
                {"removed": "detection", "tpr": 0.068, "delta_tpr": -0.052},
                {"removed": "firewall", "tpr": 0.101, "delta_tpr": -0.019},
                {"removed": "trust_calculus", "tpr": 0.105, "delta_tpr": -0.015},
                {"removed": "tripwire", "tpr": 0.109, "delta_tpr": -0.011},
            ],
            "top_synergies": [
                {"a": "firewall", "b": "detection", "synergy": 0.026},
            ],
        },
    )
    _write_json(
        data_dir / "statistical_results.json",
        {
            "cohens_d_cif_vs_baseline": 2.345,
            "kruskal_wallis": {"h": 12.0, "p": 0.0004},
        },
    )
    if include_optional:
        _write_json(
            data_dir / "multi_seed_results.json",
            {
                "data_origin": "real_pipeline",
                "source_script": "scripts/run_multi_seed.py",
                "n_seeds": 3,
                "overall_cv": 0.097,
                "seed_metrics": [
                    {"seed": 1, "overall": 0.37},
                    {"seed": 2, "overall": 0.447},
                    {"seed": 3, "overall": 0.56},
                ],
            },
        )
        _write_json(data_dir / "llm_demo_results.json", _llm_payload())
        _write_json(data_dir / "colony_results.json", [{"scenario": "sybil"}])


def _write_manuscript_files(manuscript_dir: Path) -> None:
    manuscript_dir.mkdir(exist_ok=True)
    (manuscript_dir / "00_abstract.md").write_text(
        "mean detection rate of 0.0\\% [95\\% CI: 0.0\\%, 0.0\\%]\n"
        "$\\Delta\\text{TPR} = -0.000$ achieving 0--0\\% detection across\n"
    )
    (manuscript_dir / "05_results.md").write_text(
        "Mean Detection Rate | 0.000\n"
        "Coefficient of Variation | 0.000\n"
        "Min Detection Rate | 0.00\n"
        "Max Detection Rate | 0.00\n"
        "| Claude Code | Hub-spoke | 0.0\\%\n"
        "| CrewAI | Chain | 0.0\\%\n"
        "| Detection Rate (simulation) | 0.000\n"
    )
    (manuscript_dir / "05d_ablation_and_scalability.md").write_text(
        "The Detection module contributes $\\Delta\\text{TPR} = -0.000), "
        "followed by Tripwire ($-0.011$). The Firewall + Detection pair "
        "exhibits the strongest positive synergy ($+0.000$ beyond additive prediction).\n"
        "| Detection module | 0.000 | $-0.000$ | text |\n"
        "| Firewall | 0.000 | $-0.000$ | text |\n"
        "| Trust Calculus | 0.000 | $-0.000$ | text |\n"
        "| Tripwire | 0.000 | $-0.000$ | text |\n"
        "Detection module $>$ Tripwire. multi-seed analysis shows $\\sim$0.0\\%\n"
    )
    (manuscript_dir / "06_discussion.md").write_text(
        "mean detection rate of 0.0\\% [95\\% CI: 0.0\\%, 0.0\\%] "
        "$\\Delta\\text{TPR} = -0.000) strongest synergy ($+0.000$\n"
    )
    (manuscript_dir / "04_experimental_setup.md").write_text(
        "validation ($N=5$ | Claude Code | Hub-spoke | 0.0\\% "
        "| CrewAI | Chain | 0.0\\% mean DR $\\sim$0\\%\n"
    )
    (manuscript_dir / "07_conclusion.md").write_text(
        "mean DR = 0.0\\% $\\Delta\\text{TPR} = -0.000 synergy ($+0.000$\n"
    )
    (manuscript_dir / "05b_statistical_significance.md").write_text(
        "Mean DR | 0.000\n"
        "CV | 0.000 |\n"
        "None (full pipeline) | 0.000\n"
    )
    (manuscript_dir / "S08_parametric_analysis.md").write_text(
        "| Detection Rate (simulation) | 0.000\n"
        "| Detection Rate — AutoGPT only | 0.000\n"
        "Cohen's $d$ = 0.00\n"
    )


@pytest.fixture()
def project(tmp_path: Path) -> tuple[Path, Path]:
    """A complete, fully-backed data + manuscript pair."""
    data_dir = tmp_path / "data"
    manuscript_dir = tmp_path / "manuscript"
    _write_required_data(data_dir)
    _write_manuscript_files(manuscript_dir)
    return data_dir, manuscript_dir


# ---------------------------------------------------------------------------
# Ground truth: measured values
# ---------------------------------------------------------------------------


def test_load_ground_truth_recovers_baseline_from_ablation_rows(tmp_path: Path) -> None:
    """Full-pipeline TPR is reconstructed from real ablation deltas."""
    data_dir = tmp_path / "data"
    _write_required_data(data_dir)

    ground_truth = load_ground_truth(data_dir)

    assert ground_truth["full_pipeline_tpr"] == 0.12
    assert ground_truth["firewall_delta"] == -0.019
    assert ground_truth["top_synergy"] == {
        "a": "firewall",
        "b": "detection",
        "synergy": 0.026,
    }
    assert ground_truth["llm_total_n"] == 10
    assert ground_truth["colony_scenarios"] == [{"scenario": "sybil"}]
    assert is_available(ground_truth, "llm")
    assert is_available(ground_truth, "multi_seed")
    assert is_available(ground_truth, "colony")


def test_multi_seed_ci_halfwidth_is_derived_from_the_seed_spread(tmp_path: Path) -> None:
    """The 95% CI is computed from the seeds, not from a frozen constant."""
    data_dir = tmp_path / "data"
    _write_required_data(data_dir)

    gt = load_ground_truth(data_dir)

    # rates 0.37 / 0.447 / 0.56 -> mean 0.459, sample sd 0.09557, n = 3
    assert gt["multi_seed_mean_dr"] == pytest.approx(0.459)
    assert gt["multi_seed_ci_halfwidth"] == pytest.approx(0.108142, abs=1e-5)

    # Positive control: widen the spread and the halfwidth must grow. If the
    # halfwidth were a hardcoded 0.016 this assertion could never fail.
    payload = json.loads((data_dir / "multi_seed_results.json").read_text())
    payload["seed_metrics"] = [
        {"seed": 1, "overall": 0.10},
        {"seed": 2, "overall": 0.459},
        {"seed": 3, "overall": 0.83},
    ]
    _write_json(data_dir / "multi_seed_results.json", payload)
    widened = load_ground_truth(data_dir)
    assert widened["multi_seed_mean_dr"] == pytest.approx(0.463, abs=1e-3)
    assert widened["multi_seed_ci_halfwidth"] > gt["multi_seed_ci_halfwidth"] * 2


def test_multi_seed_cv_is_derived_when_absent_from_the_payload(tmp_path: Path) -> None:
    """A missing overall_cv is recomputed from the seeds rather than defaulted."""
    data_dir = tmp_path / "data"
    _write_required_data(data_dir)
    payload = json.loads((data_dir / "multi_seed_results.json").read_text())
    del payload["overall_cv"]
    _write_json(data_dir / "multi_seed_results.json", payload)

    gt = load_ground_truth(data_dir)

    # sd 0.09557 / mean 0.459 -> 0.2082, nothing like the old 0.097 default.
    assert gt["multi_seed_cv"] == pytest.approx(0.20822, abs=1e-4)
    assert gt["multi_seed_cv"] != 0.097


def test_multi_seed_single_seed_without_cv_is_unavailable(tmp_path: Path) -> None:
    """A single seed cannot yield a CV, so the source is marked unavailable."""
    data_dir = tmp_path / "data"
    _write_required_data(data_dir)
    _write_json(
        data_dir / "multi_seed_results.json",
        {"n_seeds": 1, "seed_metrics": [{"seed": 1, "overall": 0.42}]},
    )

    gt = load_ground_truth(data_dir)

    assert not is_available(gt, "multi_seed")
    assert "multi_seed_cv" not in gt


# ---------------------------------------------------------------------------
# Fail-closed: no numeric fallbacks anywhere
# ---------------------------------------------------------------------------

_NUMERIC_LLM_KEYS = (
    "llm_claude_dr",
    "llm_claude_tp",
    "llm_claude_fn",
    "llm_crewai_dr",
    "llm_crewai_tp",
    "llm_crewai_fn",
    "llm_n_per_arch",
    "llm_total_n",
)

_NUMERIC_MULTI_SEED_KEYS = (
    "multi_seed_mean_dr",
    "multi_seed_cv",
    "multi_seed_min_dr",
    "multi_seed_max_dr",
    "multi_seed_n",
    "multi_seed_ci_halfwidth",
)


def _break_llm(data_dir: Path, payload: object) -> None:
    _write_json(data_dir / "llm_demo_results.json", payload)


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param(
            {"status": "skipped", "reason": "COGSEC_RUN_LLM_ANALYSIS not set",
             "model": "gemma3:4b"},
            id="status_skipped_stub_on_disk_today",
        ),
        pytest.param(
            {"status": "ollama_unavailable", "model": "gemma3:4b"},
            id="status_ollama_unavailable",
        ),
        pytest.param(
            {"status": "timeout", "timeout_seconds": 300},
            id="status_timeout",
        ),
        pytest.param(
            {"status": "ok", "phase2_architectures": {"Claude Code": {}}},
            id="results_key_absent",
        ),
        pytest.param(
            {"status": "ok", "multiagent_results": {}},
            id="results_key_empty",
        ),
        pytest.param(
            {"status": "ok", "multiagent_results": {"crewai": {"detection_rate": 1.0}}},
            id="architecture_missing",
        ),
        pytest.param(
            {
                "status": "ok",
                "multiagent_results": {
                    "claude_code": {"detection_rate": 0.8, "true_positives": 4},
                    "crewai": {"detection_rate": 1.0, "true_positives": 5,
                               "false_negatives": 0, "total": 5},
                },
            },
            id="required_field_missing",
        ),
        pytest.param(
            {
                "status": "ok",
                "multiagent_results": {
                    "claude_code": {"detection_rate": 0.8, "true_positives": 4,
                                    "false_negatives": 1, "total": 9},
                    "crewai": {"detection_rate": 1.0, "true_positives": 5,
                               "false_negatives": 0, "total": 5},
                },
            },
            id="tp_plus_fn_disagrees_with_total",
        ),
        pytest.param(
            {
                "status": "ok",
                "multiagent_results": {
                    "claude_code": {"detection_rate": 0.99, "true_positives": 4,
                                    "false_negatives": 1, "total": 5},
                    "crewai": {"detection_rate": 1.0, "true_positives": 5,
                               "false_negatives": 0, "total": 5},
                },
            },
            id="detection_rate_disagrees_with_counts",
        ),
        pytest.param(
            {
                "status": "ok",
                "multiagent_results": {
                    "claude_code": {"detection_rate": 0.0, "true_positives": 0,
                                    "false_negatives": 0, "total": 0},
                    "crewai": {"detection_rate": 1.0, "true_positives": 5,
                               "false_negatives": 0, "total": 5},
                },
            },
            id="zero_total",
        ),
        pytest.param([1, 2, 3], id="not_a_json_object"),
    ],
)
def test_llm_ground_truth_fails_closed_and_emits_no_number(
    tmp_path: Path, payload: object
) -> None:
    """No LLM number is produced unless a real run measured it.

    Positive control for the whole family: the historic bug was that each of
    these states silently yielded 0.80 / 1.00 / N=10.
    """
    data_dir = tmp_path / "data"
    _write_required_data(data_dir)
    _break_llm(data_dir, payload)

    gt = load_ground_truth(data_dir)

    assert not is_available(gt, "llm")
    for key in _NUMERIC_LLM_KEYS:
        assert key not in gt, f"{key} was fabricated from a fallback"
    assert gt["_unavailable"]["llm"]


@pytest.mark.parametrize("status", ["skipped", "ollama_unavailable", "timeout", "error"])
def test_status_field_alone_invalidates_a_populated_results_block(
    tmp_path: Path, status: str
) -> None:
    """A stale results block does not survive a non-success status.

    This is the laundering vector the ``status`` check exists for: a previous
    successful run leaves ``multiagent_results`` on disk, a later run is
    skipped and rewrites only the status. Without the status check the old
    numbers would be re-reported as current measurements.
    """
    data_dir = tmp_path / "data"
    _write_required_data(data_dir)
    stale = _llm_payload()
    stale["status"] = status
    stale["reason"] = "did not run"
    _write_json(data_dir / "llm_demo_results.json", stale)

    gt = load_ground_truth(data_dir)

    assert not is_available(gt, "llm")
    for key in _NUMERIC_LLM_KEYS:
        assert key not in gt, f"{key} survived a status={status!r} run"

    # Positive control: identical payload with status "ok" is accepted.
    stale["status"] = "ok"
    _write_json(data_dir / "llm_demo_results.json", stale)
    assert is_available(load_ground_truth(data_dir), "llm")


def test_status_field_alone_invalidates_populated_seed_metrics(tmp_path: Path) -> None:
    """Same laundering vector for the multi-seed source."""
    data_dir = tmp_path / "data"
    _write_required_data(data_dir)
    stale = json.loads((data_dir / "multi_seed_results.json").read_text())
    stale["status"] = "error"
    _write_json(data_dir / "multi_seed_results.json", stale)

    gt = load_ground_truth(data_dir)

    assert not is_available(gt, "multi_seed")
    for key in _NUMERIC_MULTI_SEED_KEYS:
        assert key not in gt

    stale["status"] = "ok"
    _write_json(data_dir / "multi_seed_results.json", stale)
    assert is_available(load_ground_truth(data_dir), "multi_seed")


def test_llm_ground_truth_fails_closed_when_file_absent(tmp_path: Path) -> None:
    """A missing results file yields no LLM numbers."""
    data_dir = tmp_path / "data"
    _write_required_data(data_dir)
    (data_dir / "llm_demo_results.json").unlink()

    gt = load_ground_truth(data_dir)

    assert not is_available(gt, "llm")
    for key in _NUMERIC_LLM_KEYS:
        assert key not in gt


def test_llm_ground_truth_fails_closed_on_corrupt_json(tmp_path: Path) -> None:
    """A truncated results file yields no LLM numbers."""
    data_dir = tmp_path / "data"
    _write_required_data(data_dir)
    (data_dir / "llm_demo_results.json").write_text("{not json")

    gt = load_ground_truth(data_dir)

    assert not is_available(gt, "llm")
    assert "not valid JSON" in gt["_unavailable"]["llm"]


def test_llm_ground_truth_reports_a_measured_zero_as_zero(tmp_path: Path) -> None:
    """A real run that detected nothing is a measurement, not an outage.

    This is the discrimination the schema exists for: 0.0 must survive, while
    the skipped stub above must produce nothing at all.
    """
    data_dir = tmp_path / "data"
    _write_required_data(data_dir)
    _break_llm(
        data_dir,
        {
            "status": "ok",
            "multiagent_results": {
                "claude_code": {"detection_rate": 0.0, "true_positives": 0,
                                "false_negatives": 5, "total": 5},
                "crewai": {"detection_rate": 0.0, "true_positives": 0,
                           "false_negatives": 5, "total": 5},
            },
        },
    )

    gt = load_ground_truth(data_dir)

    assert is_available(gt, "llm")
    assert gt["llm_claude_dr"] == 0.0
    assert gt["llm_crewai_dr"] == 0.0
    assert gt["llm_total_n"] == 10


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({"status": "skipped", "reason": "not run"}, id="status_skipped"),
        pytest.param({"n_seeds": 30, "seed_metrics": []}, id="empty_seed_metrics"),
        pytest.param({"n_seeds": 30}, id="seed_metrics_absent"),
        pytest.param(
            {"n_seeds": 2, "seed_metrics": [{"seed": 1}, {"seed": 2}]},
            id="no_overall_field",
        ),
    ],
)
def test_multi_seed_ground_truth_fails_closed(tmp_path: Path, payload: object) -> None:
    """The multi-seed fallbacks (0.447 / 0.097 / 0.37 / 0.56) are gone."""
    data_dir = tmp_path / "data"
    _write_required_data(data_dir)
    _write_json(data_dir / "multi_seed_results.json", payload)

    gt = load_ground_truth(data_dir)

    assert not is_available(gt, "multi_seed")
    for key in _NUMERIC_MULTI_SEED_KEYS:
        assert key not in gt, f"{key} was fabricated from a fallback"


def test_multi_seed_ground_truth_fails_closed_when_file_absent(tmp_path: Path) -> None:
    """A missing multi-seed file yields no multi-seed numbers."""
    data_dir = tmp_path / "data"
    _write_required_data(data_dir, include_optional=False)

    gt = load_ground_truth(data_dir)

    assert not is_available(gt, "multi_seed")
    for key in _NUMERIC_MULTI_SEED_KEYS:
        assert key not in gt
    assert not is_available(gt, "colony")
    assert "colony_scenarios" not in gt


# ---------------------------------------------------------------------------
# Honest logging: a fallback is never tagged [REAL]
# ---------------------------------------------------------------------------


def test_unavailable_llm_is_never_logged_as_real(
    project: tuple[Path, Path], caplog: pytest.LogCaptureFixture
) -> None:
    """Substituting nothing must also mean claiming nothing."""
    data_dir, manuscript_dir = project
    _break_llm(data_dir, {"status": "skipped", "reason": "not run"})

    with caplog.at_level(logging.INFO, logger="manuscript.injector"):
        with pytest.raises(GroundTruthUnavailableError):
            inject_all(data_dir, manuscript_dir, dry_run=True)

    llm_lines = [r.getMessage() for r in caplog.records if "LLM" in r.getMessage()]
    assert llm_lines, "the LLM state was not reported at all"
    assert not any("[REAL]" in line for line in llm_lines)
    assert any("[UNAVAILABLE]" in line for line in llm_lines)


def test_measured_llm_is_logged_as_real(
    project: tuple[Path, Path], caplog: pytest.LogCaptureFixture
) -> None:
    """Positive control for the logging test above: measured values do say [REAL]."""
    data_dir, manuscript_dir = project

    with caplog.at_level(logging.INFO, logger="manuscript.injector"):
        inject_all(data_dir, manuscript_dir, dry_run=True)

    llm_lines = [r.getMessage() for r in caplog.records if "LLM" in r.getMessage()]
    assert any("[REAL]" in line for line in llm_lines)
    assert not any("[UNAVAILABLE]" in line for line in llm_lines)


def test_unavailable_llm_leaves_the_manuscript_untouched(project: tuple[Path, Path]) -> None:
    """No LLM number is written when no LLM run happened."""
    data_dir, manuscript_dir = project
    _break_llm(data_dir, {"status": "skipped", "reason": "not run"})
    before = (manuscript_dir / "05_results.md").read_text()

    with pytest.raises(GroundTruthUnavailableError):
        inject_all(data_dir, manuscript_dir, strict=True)

    after = (manuscript_dir / "05_results.md").read_text()
    assert "| Claude Code | Hub-spoke | 0.0\\%" in after
    assert "80.0" not in after
    # Multi-seed rows are backed, so the file legitimately changed there.
    assert before != after
    assert "Mean Detection Rate | 0.459" in after


def test_strict_false_reports_unbacked_claims_instead_of_raising(
    project: tuple[Path, Path],
) -> None:
    """Non-strict mode still refuses to invent a number; it only defers the error."""
    data_dir, manuscript_dir = project
    _break_llm(data_dir, {"status": "skipped", "reason": "not run"})
    report = InjectionReport()

    inject_all(data_dir, manuscript_dir, dry_run=True, strict=False, report=report)

    unbacked_labels = {label for _, label, _ in report.unbacked}
    assert unbacked_labels == {
        "llm_detection_range",
        "llm_claude_dr",
        "llm_crewai_dr",
        "llm_total_n",
    }
    assert not report.ok
    # Positive control: the same run with real data has nothing unbacked.
    _write_json(data_dir / "llm_demo_results.json", _llm_payload())
    clean = InjectionReport()
    inject_all(data_dir, manuscript_dir, dry_run=True, strict=False, report=clean)
    assert clean.unbacked == []
    assert clean.ok


# ---------------------------------------------------------------------------
# A zero-match pattern is an error, not "no changes needed"
# ---------------------------------------------------------------------------


def test_zero_match_pattern_raises_instead_of_reporting_success(
    project: tuple[Path, Path],
) -> None:
    """Manuscript drift must surface as a failure, not as a clean run."""
    data_dir, manuscript_dir = project
    results = manuscript_dir / "05_results.md"
    # Drift the row exactly the way the real manuscript drifted: keep the claim,
    # change the notation so the injector pattern no longer matches.
    results.write_text(
        results.read_text().replace(
            "| Claude Code | Hub-spoke | 0.0\\%",
            "| Claude Code | Hub-spoke | $\\approx$0.0\\%",
        )
    )

    with pytest.raises(InjectionPatternError) as excinfo:
        inject_all(data_dir, manuscript_dir, dry_run=True)

    assert "llm_claude_dr" in str(excinfo.value)


def test_clean_run_does_not_raise(project: tuple[Path, Path]) -> None:
    """Positive control for the drift test: the undrifted fixture passes."""
    data_dir, manuscript_dir = project
    assert inject_all(data_dir, manuscript_dir, dry_run=True) == 8


def test_zero_match_is_reported_even_when_nothing_needed_changing(
    project: tuple[Path, Path],
) -> None:
    """The old bug: a fully-dead pattern set logged '✅ no changes needed'."""
    data_dir, manuscript_dir = project
    inject_all(data_dir, manuscript_dir)  # bring the fixture up to date

    # Now drift one document. Nothing needs updating any more, so the old code
    # path would have reported success.
    conclusion = manuscript_dir / "07_conclusion.md"
    conclusion.write_text(conclusion.read_text().replace("mean DR = ", "mean DR of "))

    report = InjectionReport()
    with pytest.raises(InjectionPatternError):
        inject_all(data_dir, manuscript_dir, strict=False, report=report)

    # Nothing needed rewriting, yet the run is a failure rather than a "✅".
    assert [label for _, label, _ in report.misses] == ["multi_seed_mean_dr"]
    assert not report.ok

    # Positive control: restore the wording and the identical run is clean.
    conclusion.write_text(conclusion.read_text().replace("mean DR of ", "mean DR = "))
    clean = InjectionReport()
    assert inject_all(data_dir, manuscript_dir, report=clean) == 0
    assert clean.ok


def test_unavailable_multi_seed_leaves_every_dependent_claim_alone(
    project: tuple[Path, Path],
) -> None:
    """All seven documents that cite the multi-seed run must fail closed together."""
    data_dir, manuscript_dir = project
    _write_json(data_dir / "multi_seed_results.json", {"status": "error"})
    before = {p.name: p.read_text() for p in manuscript_dir.glob("*.md")}

    report = InjectionReport()
    inject_all(data_dir, manuscript_dir, strict=False, report=report)

    unbacked_docs = {doc for doc, _, _ in report.unbacked}
    assert unbacked_docs == {
        "00_abstract.md",
        "05_results.md",
        "05d_ablation_and_scalability.md",
        "06_discussion.md",
        "04_experimental_setup.md",
        "07_conclusion.md",
        "05b_statistical_significance.md",
    }
    assert report.misses == []
    # The historic defaults must appear nowhere in the rendered manuscript.
    for name, text in before.items():
        after = (manuscript_dir / name).read_text()
        for fabricated in ("0.447", "44.7", "0.097", "0.56", "0.37"):
            assert fabricated not in after, f"{name} gained fabricated value {fabricated}"
        del text

    # Positive control: restore the data and every one of those claims is filled.
    _write_required_data(data_dir)
    clean = InjectionReport()
    inject_all(data_dir, manuscript_dir, strict=False, report=clean)
    assert clean.unbacked == []
    assert "Mean Detection Rate | 0.459" in (manuscript_dir / "05_results.md").read_text()


def test_component_baseline_tpr_of_no_components_is_zero() -> None:
    """Degenerate ablation input does not blow up the loader helper."""
    from manuscript.injector import _component_baseline_tpr

    assert _component_baseline_tpr([]) == 0.0
    assert _component_baseline_tpr(
        [{"tpr": 0.1, "delta_tpr": -0.02}, {"tpr": 0.08, "delta_tpr": -0.04}]
    ) == pytest.approx(0.12)


def test_report_counts_matches_rather_than_assuming_them(project: tuple[Path, Path]) -> None:
    """Every maintained claim is accounted for in the report."""
    data_dir, manuscript_dir = project
    report = InjectionReport()
    inject_all(data_dir, manuscript_dir, dry_run=True, report=report)

    assert report.ok
    assert report.misses == []
    assert report.unbacked == []
    assert report.n_substitutions >= len(report.substitutions) > 20


def test_missing_supplement_is_skipped_without_a_miss(project: tuple[Path, Path]) -> None:
    """An absent optional supplement is a skip, not a zero-match error."""
    data_dir, manuscript_dir = project
    (manuscript_dir / "S08_parametric_analysis.md").unlink()

    report = InjectionReport()
    inject_all(data_dir, manuscript_dir, dry_run=True, report=report)

    assert report.ok
    assert not any(doc.startswith("S08") for doc, _, _ in report.substitutions)


@pytest.mark.parametrize("inject", ALL_INJECTORS, ids=lambda f: f.__name__)
def test_each_injector_can_run_standalone(project: tuple[Path, Path], inject) -> None:
    """Each entry point validates its own report when used on its own."""
    data_dir, manuscript_dir = project
    gt = load_ground_truth(data_dir)
    assert inject(gt, manuscript_dir, True) is True


@pytest.mark.parametrize("inject", ALL_INJECTORS, ids=lambda f: f.__name__)
def test_each_injector_raises_standalone_on_a_dead_document(
    project: tuple[Path, Path], inject
) -> None:
    """Positive control: blank the document and every injector must complain."""
    data_dir, manuscript_dir = project
    gt = load_ground_truth(data_dir)
    for path in manuscript_dir.glob("*.md"):
        path.write_text("nothing to substitute here\n")

    if inject is inject_parametric_supplement:
        # This document is optional; prove the *present but dead* case raises.
        (manuscript_dir / "S08_parametric_analysis.md").write_text("dead\n")

    with pytest.raises(InjectionPatternError):
        inject(gt, manuscript_dir, True)


# ---------------------------------------------------------------------------
# End-to-end
# ---------------------------------------------------------------------------


def test_inject_all_updates_manuscript_files_from_data(project: tuple[Path, Path]) -> None:
    """Injection writes measured values into markdown files idempotently."""
    data_dir, manuscript_dir = project

    assert inject_all(data_dir, manuscript_dir, dry_run=True) > 0
    assert "0.459" not in (manuscript_dir / "05_results.md").read_text()

    changed_count = inject_all(data_dir, manuscript_dir)
    assert changed_count == 8

    assert "Mean Detection Rate | 0.459" in (manuscript_dir / "05_results.md").read_text()
    assert "| Claude Code | Hub-spoke | 80.0\\%" in (
        manuscript_dir / "05_results.md"
    ).read_text()
    assert "| Detection module | 0.068 | $-0.052$" in (
        manuscript_dir / "05d_ablation_and_scalability.md"
    ).read_text()
    assert "None (full pipeline) | 0.120" in (
        manuscript_dir / "05b_statistical_significance.md"
    ).read_text()
    assert "Cohen's $d$ = 2.35" in (
        manuscript_dir / "S08_parametric_analysis.md"
    ).read_text()

    assert inject_all(data_dir, manuscript_dir) == 0


def test_injected_llm_values_track_the_data_file(project: tuple[Path, Path]) -> None:
    """Change the measurement, and the manuscript number must change with it.

    Positive control against a re-hardcoded 80/100: these numbers are not the
    historic defaults, so a fallback could not produce them.
    """
    data_dir, manuscript_dir = project
    payload = _llm_payload()
    payload["multiagent_results"]["claude_code"] = {
        "detection_rate": 0.6,
        "true_positives": 3,
        "false_negatives": 2,
        "total": 5,
    }
    payload["multiagent_results"]["crewai"] = {
        "detection_rate": 0.75,
        "true_positives": 6,
        "false_negatives": 2,
        "total": 8,
    }
    _write_json(data_dir / "llm_demo_results.json", payload)

    inject_all(data_dir, manuscript_dir)

    setup = (manuscript_dir / "04_experimental_setup.md").read_text()
    assert "| Claude Code | Hub-spoke | 60.0\\%" in setup
    assert "| CrewAI | Chain | 75.0\\%" in setup
    assert "validation ($N=13$" in setup
    assert "achieving 60--75\\% detection across" in (
        manuscript_dir / "00_abstract.md"
    ).read_text()
