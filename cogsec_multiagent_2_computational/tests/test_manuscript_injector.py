"""Tests for data-backed manuscript value injection."""

from __future__ import annotations

import json
from pathlib import Path

from manuscript.injector import inject_all, load_ground_truth


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2))


def _write_required_data(data_dir: Path, *, include_optional: bool = True) -> None:
    data_dir.mkdir()
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
                "overall_metrics": {
                    "mean_detection_rate": 0.447,
                    "cv_detection_rate": 0.097,
                    "min_detection_rate": 0.37,
                    "max_detection_rate": 0.56,
                    "n_seeds": 30,
                },
            },
        )
        _write_json(
            data_dir / "llm_demo_results.json",
            {
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
                    },
                },
            },
        )
        _write_json(data_dir / "colony_results.json", [{"scenario": "sybil"}])


def _write_manuscript_files(manuscript_dir: Path) -> None:
    manuscript_dir.mkdir()
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


def test_load_ground_truth_uses_defaults_for_optional_outputs(tmp_path: Path) -> None:
    """Optional LLM, multi-seed, and colony outputs have deterministic defaults."""
    data_dir = tmp_path / "data"
    _write_required_data(data_dir, include_optional=False)

    ground_truth = load_ground_truth(data_dir)

    assert ground_truth["multi_seed_mean_dr"] == 0.447
    assert ground_truth["llm_claude_dr"] == 0.80
    assert ground_truth["llm_crewai_dr"] == 1.00
    assert ground_truth["colony_scenarios"] == []


def test_inject_all_updates_manuscript_files_from_data(tmp_path: Path) -> None:
    """Injection writes measured values into markdown files idempotently."""
    data_dir = tmp_path / "data"
    manuscript_dir = tmp_path / "manuscript"
    _write_required_data(data_dir)
    _write_manuscript_files(manuscript_dir)

    assert inject_all(data_dir, manuscript_dir, dry_run=True) > 0
    assert "0.447" not in (manuscript_dir / "05_results.md").read_text()

    changed_count = inject_all(data_dir, manuscript_dir)
    assert changed_count == 8

    assert "Mean Detection Rate | 0.447" in (manuscript_dir / "05_results.md").read_text()
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
