"""Tests for the reader-side manuscript claim registry.

Two layers:

1. Machinery tests on synthetic manuscripts and synthetic data written into
   ``tmp_path``. Each correctness property is proved with a positive control:
   the violating case is constructed and the checker is shown to reject it.
2. Binding tests against the *shipped* ``manuscript/`` and ``output/data/``,
   which is where the registry earns its keep. The key invariant there is
   that no registered pattern is dead - a pattern matching zero times is how
   a fabricated number hides from a checker.
"""

from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from manuscript.claim_registry import (
    CLAIMS,
    EXACT,
    F3,
    PCT1,
    RECOVERY_TOL,
    Claim,
    ClaimDataUnavailable,
    ClaimReport,
    GroundTruth,
    claim_ids,
    parse_stated,
    verify_claims,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REAL_MANUSCRIPT = PROJECT_ROOT / "manuscript"
REAL_DATA = PROJECT_ROOT / "output" / "data"

# Claims that do NOT currently match the shipped data.
#
# These are real, reproduced defects in the manuscript prose - not registry
# bugs - and they are the manuscript-reconciliation wave's work, not this
# module's. They are pinned here so the suite stays green on the known state
# while still failing the moment *new* drift appears. The assertion is a
# subset check, so fixing a row in the prose never breaks this test; only
# introducing a new unsupported number does.
#
# To refresh after a prose fix:
#   uv run python scripts/verify_claims.py --only-failures
# These four claims are UNBACKED (not MISMATCH/NOT_FOUND): the LLM validation
# arm's artifact reports status='skipped' because COGSEC_RUN_LLM_ANALYSIS was
# not set when llm_demo_results.json was generated. They cannot be value-
# reconciled without re-running the Ollama-backed LLM demo, so they are pinned
# as the only known-unreconciled claims. Every non-LLM claim is reconciled
# (0 MISMATCH, 0 NOT_FOUND as of the release-hardening pass).
KNOWN_UNRECONCILED = frozenset(
    {
        "abstract.llm_dr_low",
        "abstract.llm_dr_high",
        "05b.llm_claude_dr",
        "05b.llm_crewai_dr",
    }
)


# ── synthetic fixtures ──────────────────────────────────────────────────


def _write_data(data_dir: Path, **files: object) -> GroundTruth:
    """Write JSON artifacts into ``data_dir`` and return a GroundTruth."""
    data_dir.mkdir(parents=True, exist_ok=True)
    for name, payload in files.items():
        (data_dir / f"{name}.json").write_text(json.dumps(payload), encoding="utf-8")
    return GroundTruth(data_dir)


def _deepcopy_json(obj):
    """JSON-safe deep copy (payloads are JSON-serializable)."""
    return json.loads(json.dumps(obj))


def _ablation(n: int = 50, detected: int = 10) -> dict[str, object]:
    """A minimal ablation artifact whose rates are k/n."""
    return {
        "full_pipeline": {"tpr": detected / n},
        "component_removal": [
            {"removed": "detection", "tpr": (detected - 5) / n, "delta_tpr": -5 / n},
            {"removed": "firewall", "tpr": (detected - 1) / n, "delta_tpr": -1 / n},
            {"removed": "sandbox", "tpr": detected / n, "delta_tpr": 0.0},
        ],
        "top_synergies": [
            {
                "a": "firewall",
                "b": "detection",
                "synergy": 3 / n,
                "tpr_a": 1 / n,
                "tpr_b": 5 / n,
                "combined_tpr": 9 / n,
            }
        ],
    }


def _claim(
    claim_id: str,
    pattern: str,
    deriver,
    tolerance: float = F3,
    unit: str = "fraction",
    provenance: str = "real",
    file: str = "doc.md",
) -> Claim:
    return Claim(
        id=claim_id,
        file=file,
        pattern=re.compile(pattern),
        deriver=deriver,
        tolerance=tolerance,
        unit=unit,  # type: ignore[arg-type]
        provenance=provenance,  # type: ignore[arg-type]
    )


# ── Claim construction guards ───────────────────────────────────────────


class TestClaimConstruction:
    """A malformed Claim must be rejected at construction time."""

    def test_zero_group_pattern_rejected(self):
        with pytest.raises(ValueError, match="exactly one capturing group"):
            _claim("c", r"no groups here", lambda gt: 1.0)

    def test_two_group_pattern_rejected(self):
        with pytest.raises(ValueError, match="exactly one capturing group"):
            _claim("c", r"(\d+)\.(\d+)", lambda gt: 1.0)

    def test_single_group_pattern_accepted(self):
        claim = _claim("c", r"(\d+\.\d+)", lambda gt: 1.0)
        assert claim.pattern.groups == 1

    def test_negative_tolerance_rejected(self):
        with pytest.raises(ValueError, match="tolerance"):
            _claim("c", r"(\d+)", lambda gt: 1.0, tolerance=-0.1)


class TestParseStated:
    """Captured literals map onto the derived value's units."""

    def test_fraction_is_verbatim(self):
        assert parse_stated("0.448", "fraction") == pytest.approx(0.448)

    def test_percent_is_divided(self):
        assert parse_stated("44.8", "percent") == pytest.approx(0.448)

    def test_latex_thousands_separator(self):
        assert parse_stated("3{,}800", "count") == pytest.approx(3800.0)

    def test_plain_thousands_separator(self):
        assert parse_stated("3,800", "count") == pytest.approx(3800.0)


# ── verdicts (each with a positive control) ─────────────────────────────


class TestVerdicts:
    """MATCH / MISMATCH / NOT_FOUND / UNBACKED, each proved reachable."""

    def _setup(self, tmp_path: Path, prose: str) -> tuple[Path, GroundTruth]:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "doc.md").write_text(prose, encoding="utf-8")
        gt = _write_data(tmp_path / "data", ablation_results=_ablation())
        return manuscript, gt

    def test_match_inside_tolerance(self, tmp_path):
        manuscript, gt = self._setup(tmp_path, "The pipeline reaches 0.200 TPR.\n")
        claim = _claim("tpr", r"reaches (\d+\.\d+) TPR", lambda g: g.full_pipeline_tpr())
        report = verify_claims([claim], manuscript, gt)
        assert report.results[0].verdict == "MATCH"
        assert report.ok

    def test_mismatch_outside_tolerance(self, tmp_path):
        """POSITIVE CONTROL: a perturbed number must be reported MISMATCH."""
        manuscript, gt = self._setup(tmp_path, "The pipeline reaches 0.999 TPR.\n")
        claim = _claim("tpr", r"reaches (\d+\.\d+) TPR", lambda g: g.full_pipeline_tpr())
        report = verify_claims([claim], manuscript, gt)
        result = report.results[0]
        assert result.verdict == "MISMATCH"
        assert result.stated == pytest.approx(0.999)
        assert result.derived == pytest.approx(0.2)
        assert result.delta == pytest.approx(0.799)
        assert not report.ok
        assert result.is_failure

    def test_not_found_is_a_failure_not_a_skip(self, tmp_path):
        """POSITIVE CONTROL: a pattern matching nothing must FAIL the gate."""
        manuscript, gt = self._setup(tmp_path, "The pipeline is quite good.\n")
        claim = _claim("tpr", r"reaches (\d+\.\d+) TPR", lambda g: g.full_pipeline_tpr())
        report = verify_claims([claim], manuscript, gt)
        result = report.results[0]
        assert result.verdict == "NOT_FOUND"
        assert result.n_matches == 0
        assert result.stated is None
        # The derived value is still reported so the fix is obvious.
        assert result.derived == pytest.approx(0.2)
        assert result.is_failure
        assert not report.ok

    def test_not_found_when_manuscript_file_is_absent(self, tmp_path):
        manuscript, gt = self._setup(tmp_path, "text\n")
        claim = _claim(
            "tpr", r"reaches (\d+\.\d+) TPR", lambda g: g.full_pipeline_tpr(), file="gone.md"
        )
        report = verify_claims([claim], manuscript, gt)
        assert report.results[0].verdict == "NOT_FOUND"
        assert "missing" in report.results[0].detail

    def test_unbacked_when_artifact_reports_skipped(self, tmp_path):
        manuscript, gt = self._setup(tmp_path, "LLM detection was 80\\%.\n")
        (gt.data_dir / "llm_demo_results.json").write_text(
            json.dumps({"status": "skipped", "reason": "not enabled"}), encoding="utf-8"
        )
        claim = _claim(
            "llm",
            r"LLM detection was (\d+)\\%",
            lambda g: g.llm_detection_rate("claude_code"),
            unit="percent",
        )
        report = verify_claims([claim], manuscript, gt)
        result = report.results[0]
        assert result.verdict == "UNBACKED"
        assert result.stated == pytest.approx(0.8)
        assert result.derived is None
        assert "skipped" in result.detail
        assert result.is_failure

    def test_unbacked_when_artifact_is_absent(self, tmp_path):
        manuscript, gt = self._setup(tmp_path, "LLM detection was 80\\%.\n")
        claim = _claim(
            "llm",
            r"LLM detection was (\d+)\\%",
            lambda g: g.llm_detection_rate("claude_code"),
            unit="percent",
        )
        report = verify_claims([claim], manuscript, gt)
        assert report.results[0].verdict == "UNBACKED"
        assert "not found" in report.results[0].detail

    def test_deriver_exception_is_reported_not_swallowed(self, tmp_path):
        manuscript, gt = self._setup(tmp_path, "Value 0.500 here.\n")

        def boom(_g: GroundTruth) -> float:
            raise KeyError("missing_field")

        claim = _claim("boom", r"Value (\d+\.\d+) here", boom)
        report = verify_claims([claim], manuscript, gt)
        assert report.results[0].verdict == "UNBACKED"
        assert "KeyError" in report.results[0].detail

    def test_unparseable_capture_is_a_mismatch(self, tmp_path):
        manuscript, gt = self._setup(tmp_path, "Value abc here.\n")
        claim = _claim("bad", r"Value (\w+) here", lambda g: g.full_pipeline_tpr())
        report = verify_claims([claim], manuscript, gt)
        assert report.results[0].verdict == "MISMATCH"
        assert "unparseable" in report.results[0].detail

    def test_worst_of_several_matches_is_reported(self, tmp_path):
        """Two sites, one right and one wrong, must still MISMATCH."""
        manuscript, gt = self._setup(
            tmp_path, "TPR is 0.200 here.\nBut TPR is 0.900 there.\n"
        )
        claim = _claim("tpr", r"TPR is (\d+\.\d+)", lambda g: g.full_pipeline_tpr())
        report = verify_claims([claim], manuscript, gt)
        result = report.results[0]
        assert result.n_matches == 2
        assert result.verdict == "MISMATCH"
        assert result.stated == pytest.approx(0.9)

    def test_all_matches_consistent_is_a_match(self, tmp_path):
        manuscript, gt = self._setup(tmp_path, "TPR is 0.200 here.\nTPR is 0.200 there.\n")
        claim = _claim("tpr", r"TPR is (\d+\.\d+)", lambda g: g.full_pipeline_tpr())
        report = verify_claims([claim], manuscript, gt)
        assert report.results[0].verdict == "MATCH"
        assert report.results[0].n_matches == 2


class TestIllustrativeProvenance:
    """Illustrative claims are reported but do not gate on value."""

    def _setup(self, tmp_path: Path, prose: str):
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "doc.md").write_text(prose, encoding="utf-8")
        return manuscript, _write_data(tmp_path / "data", ablation_results=_ablation())

    def test_illustrative_mismatch_is_not_a_failure(self, tmp_path):
        manuscript, gt = self._setup(tmp_path, "Illustrative TPR 0.900.\n")
        claim = _claim(
            "illus",
            r"Illustrative TPR (\d+\.\d+)",
            lambda g: g.full_pipeline_tpr(),
            provenance="illustrative",
        )
        report = verify_claims([claim], manuscript, gt)
        assert report.results[0].verdict == "MISMATCH"
        assert not report.results[0].is_failure
        assert report.ok

    def test_illustrative_not_found_is_still_a_failure(self, tmp_path):
        """The exemption is narrow: a dead pattern fails even when illustrative."""
        manuscript, gt = self._setup(tmp_path, "Nothing here.\n")
        claim = _claim(
            "illus",
            r"Illustrative TPR (\d+\.\d+)",
            lambda g: g.full_pipeline_tpr(),
            provenance="illustrative",
        )
        report = verify_claims([claim], manuscript, gt)
        assert report.results[0].verdict == "NOT_FOUND"
        assert report.results[0].is_failure
        assert not report.ok


# ── GroundTruth accessors ───────────────────────────────────────────────


class TestGroundTruthAblation:
    """Ablation accessors, including the corpus-size recovery."""

    def test_component_lookup(self, tmp_path):
        gt = _write_data(tmp_path, ablation_results=_ablation())
        assert gt.component_tpr("detection") == pytest.approx(0.1)
        assert gt.component_delta("detection") == pytest.approx(-0.1)
        assert gt.component_delta_magnitude("detection") == pytest.approx(0.1)

    def test_unknown_component_raises(self, tmp_path):
        gt = _write_data(tmp_path, ablation_results=_ablation())
        with pytest.raises(ClaimDataUnavailable, match="no component row"):
            gt.component("nope")

    def test_corpus_size_recovers_the_denominator(self, tmp_path):
        """POSITIVE CONTROL: change N in the artifact, the derived N follows."""
        gt50 = _write_data(tmp_path / "a", ablation_results=_ablation(n=50, detected=10))
        assert gt50.ablation_corpus_size() == pytest.approx(50.0)
        gt98 = _write_data(tmp_path / "b", ablation_results=_ablation(n=98, detected=12))
        assert gt98.ablation_corpus_size() == pytest.approx(98.0)

    def test_corpus_size_ignores_zero_rates(self, tmp_path):
        """A 0/N rate carries no denominator information and must be skipped."""
        payload = _ablation(n=40, detected=8)
        payload["component_removal"].append(
            {"removed": "zeroed", "tpr": 0.0, "delta_tpr": -8 / 40}
        )
        gt = _write_data(tmp_path, ablation_results=payload)
        assert gt.ablation_corpus_size() == pytest.approx(40.0)

    def test_corpus_size_rejects_implausible_denominator(self, tmp_path):
        """Rates that are not k/N for any sane N must not yield a fake corpus size."""
        payload = {
            "full_pipeline": {"tpr": math.pi / 10},
            "component_removal": [
                {"removed": "x", "tpr": math.e / 10, "delta_tpr": -0.1},
                {"removed": "y", "tpr": math.sqrt(2) / 10, "delta_tpr": -0.1},
            ],
            "top_synergies": [],
        }
        gt = _write_data(tmp_path, ablation_results=payload)
        with pytest.raises(ClaimDataUnavailable, match="implied denominator"):
            gt.ablation_corpus_size()

    def test_synergy_is_order_independent(self, tmp_path):
        gt = _write_data(tmp_path, ablation_results=_ablation())
        assert gt.synergy("firewall", "detection") == pytest.approx(0.06)
        assert gt.synergy("detection", "firewall") == pytest.approx(0.06)

    def test_unrecorded_synergy_pair_raises(self, tmp_path):
        gt = _write_data(tmp_path, ablation_results=_ablation())
        with pytest.raises(ClaimDataUnavailable, match="top_synergies"):
            gt.synergy("sandbox", "detection")

    def test_detection_share_and_top_n_share(self, tmp_path):
        gt = _write_data(tmp_path, ablation_results=_ablation())
        # detection contributes 5/50 of a 10/50 baseline.
        assert gt.detection_share_of_pipeline() == pytest.approx(0.5)
        # harmful magnitudes are 5/50 and 1/50; the top 1 holds 5/6.
        assert gt.top_n_harmful_share(1) == pytest.approx(5 / 6)
        assert gt.top_n_harmful_share(3) == pytest.approx(1.0)

    def test_zero_baseline_share_raises(self, tmp_path):
        payload = _ablation()
        payload["full_pipeline"] = {"tpr": 0.0}
        gt = _write_data(tmp_path, ablation_results=payload)
        with pytest.raises(ClaimDataUnavailable, match="not positive"):
            gt.detection_share_of_pipeline()

    def test_missing_full_pipeline_block_raises(self, tmp_path):
        payload = _ablation()
        del payload["full_pipeline"]
        gt = _write_data(tmp_path, ablation_results=payload)
        with pytest.raises(ClaimDataUnavailable, match="full_pipeline"):
            gt.full_pipeline_tpr()

    def test_empty_component_rows_raise(self, tmp_path):
        gt = _write_data(tmp_path, ablation_results={"component_removal": []})
        with pytest.raises(ClaimDataUnavailable, match="component_removal"):
            gt.component("detection")

    def test_no_harmful_removals_raises(self, tmp_path):
        payload = {
            "full_pipeline": {"tpr": 0.2},
            "component_removal": [{"removed": "a", "tpr": 0.2, "delta_tpr": 0.0}],
            "top_synergies": [],
        }
        gt = _write_data(tmp_path, ablation_results=payload)
        with pytest.raises(ClaimDataUnavailable, match="harmful"):
            gt.top_n_harmful_share()

    def test_missing_synergy_block_raises(self, tmp_path):
        payload = _ablation()
        payload["top_synergies"] = []
        gt = _write_data(tmp_path, ablation_results=payload)
        with pytest.raises(ClaimDataUnavailable, match="top_synergies"):
            gt.synergy("a", "b")

    def test_non_object_ablation_raises(self, tmp_path):
        gt = _write_data(tmp_path, ablation_results=[1, 2, 3])
        with pytest.raises(ClaimDataUnavailable, match="not a JSON object"):
            gt.ablation()


class TestGroundTruthPayload:
    """Fail-closed payload loading."""

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(ClaimDataUnavailable, match="not found"):
            GroundTruth(tmp_path).payload("nope.json")

    def test_invalid_json_raises(self, tmp_path):
        (tmp_path / "bad.json").write_text("{not json", encoding="utf-8")
        with pytest.raises(ClaimDataUnavailable, match="not valid JSON"):
            GroundTruth(tmp_path).payload("bad.json")

    @pytest.mark.parametrize(
        "status", ["skipped", "ollama_unavailable", "timeout", "error", "failed", "unavailable"]
    )
    def test_every_unavailable_status_raises(self, tmp_path, status):
        (tmp_path / "s.json").write_text(json.dumps({"status": status}), encoding="utf-8")
        with pytest.raises(ClaimDataUnavailable, match=status):
            GroundTruth(tmp_path).payload("s.json")

    def test_success_status_is_accepted_and_cached(self, tmp_path):
        (tmp_path / "s.json").write_text(json.dumps({"status": "ok", "v": 1}), encoding="utf-8")
        gt = GroundTruth(tmp_path)
        assert gt.payload("s.json")["v"] == 1
        # Second read comes from the cache even if the file is deleted.
        (tmp_path / "s.json").unlink()
        assert gt.payload("s.json")["v"] == 1


class TestGroundTruthBaseline:
    """Fail-closed and happy paths for the baseline_comparison accessors."""

    _VALID = {
        "detectors": [
            {
                "name": "cif",
                "metrics": {"tpr": 0.4, "fpr": 0.1, "youden_j": 0.3},
                "curves": {"auc": 0.9},
                "permutation_null": {"p_value": 0.001},
            }
        ],
        "headline": {"cif_rank": 1},
    }

    def test_non_object_baseline_raises(self, tmp_path):
        gt = _write_data(tmp_path, baseline_comparison=[1, 2, 3])
        with pytest.raises(ClaimDataUnavailable, match="not a JSON object"):
            gt.baseline_comparison()

    def test_unknown_detector_raises(self, tmp_path):
        gt = _write_data(tmp_path, baseline_comparison=self._VALID)
        with pytest.raises(ClaimDataUnavailable, match="has no detector"):
            gt.baseline_metric("banana", "tpr")

    def test_missing_metric_raises(self, tmp_path):
        gt = _write_data(tmp_path, baseline_comparison=self._VALID)
        with pytest.raises(ClaimDataUnavailable, match="no metrics.precision"):
            gt.baseline_metric("cif", "precision")

    def test_missing_auc_raises(self, tmp_path):
        payload = _deepcopy_json(self._VALID)
        payload["detectors"][0]["curves"] = {}
        gt = _write_data(tmp_path, baseline_comparison=payload)
        with pytest.raises(ClaimDataUnavailable, match="no curves.auc"):
            gt.baseline_auc("cif")

    def test_missing_permutation_p_raises(self, tmp_path):
        payload = _deepcopy_json(self._VALID)
        payload["detectors"][0]["permutation_null"] = {}
        gt = _write_data(tmp_path, baseline_comparison=payload)
        with pytest.raises(ClaimDataUnavailable, match="no permutation_null.p_value"):
            gt.baseline_permutation_p("cif")

    def test_missing_cif_rank_raises(self, tmp_path):
        payload = _deepcopy_json(self._VALID)
        payload["headline"] = {}
        gt = _write_data(tmp_path, baseline_comparison=payload)
        with pytest.raises(ClaimDataUnavailable, match="no headline.cif_rank"):
            gt.baseline_cif_rank()

    def test_valid_baseline_returns_values(self, tmp_path):
        gt = _write_data(tmp_path, baseline_comparison=self._VALID)
        assert gt.baseline_metric("cif", "fpr") == 0.1
        assert gt.baseline_auc("cif") == 0.9
        assert gt.baseline_permutation_p("cif") == 0.001
        assert gt.baseline_cif_rank() == 1


class TestGroundTruthMultiSeed:
    """Multi-seed statistics."""

    @staticmethod
    def _payload(rates, **extra):
        payload = {
            "n_seeds": len(rates),
            "seed_metrics": [{"seed": i, "overall": r} for i, r in enumerate(rates)],
        }
        payload.update(extra)
        return payload

    def test_mean_min_max_n(self, tmp_path):
        gt = _write_data(tmp_path, multi_seed_results=self._payload([0.4, 0.5, 0.6]))
        assert gt.ms_mean() == pytest.approx(0.5)
        assert gt.ms_min() == pytest.approx(0.4)
        assert gt.ms_max() == pytest.approx(0.6)
        assert gt.ms_n() == pytest.approx(3.0)

    def test_cv_prefers_recorded_value(self, tmp_path):
        gt = _write_data(
            tmp_path, multi_seed_results=self._payload([0.4, 0.5, 0.6], overall_cv=0.25)
        )
        assert gt.ms_cv() == pytest.approx(0.25)

    def test_cv_is_derived_when_absent(self, tmp_path):
        gt = _write_data(tmp_path, multi_seed_results=self._payload([0.4, 0.5, 0.6]))
        # sd = 0.1, mean = 0.5
        assert gt.ms_cv() == pytest.approx(0.2)

    def test_cv_underivable_raises(self, tmp_path):
        gt = _write_data(tmp_path, multi_seed_results=self._payload([0.5]))
        with pytest.raises(ClaimDataUnavailable, match="overall_cv"):
            gt.ms_cv()

    def test_ci_brackets_the_mean(self, tmp_path):
        gt = _write_data(tmp_path, multi_seed_results=self._payload([0.4, 0.5, 0.6]))
        assert gt.ms_ci_low() < gt.ms_mean() < gt.ms_ci_high()

    def test_ci_needs_more_than_one_seed(self, tmp_path):
        gt = _write_data(tmp_path, multi_seed_results=self._payload([0.5]))
        with pytest.raises(ClaimDataUnavailable, match="need >1 seed"):
            gt.ms_ci_low()

    def test_empty_seed_metrics_raise(self, tmp_path):
        gt = _write_data(tmp_path, multi_seed_results={"seed_metrics": []})
        with pytest.raises(ClaimDataUnavailable, match="seed_metrics"):
            gt.ms_mean()

    def test_seed_metrics_without_overall_raise(self, tmp_path):
        gt = _write_data(tmp_path, multi_seed_results={"seed_metrics": [{"seed": 1}]})
        with pytest.raises(ClaimDataUnavailable, match="overall"):
            gt.ms_mean()

    def test_non_object_payload_raises(self, tmp_path):
        gt = _write_data(tmp_path, multi_seed_results=[1, 2])
        with pytest.raises(ClaimDataUnavailable, match="not a JSON object"):
            gt.multi_seed()


class TestGroundTruthColony:
    """Colony benchmark accessors."""

    ROWS = [
        {"scenario": "a", "n_agents": 20, "n_adversaries": 2, "detection_rate": 0.8, "fpr": 0.1},
        {"scenario": "b", "n_agents": 100, "n_adversaries": 4, "detection_rate": 1.0},
        {"scenario": "c", "n_agents": 50, "n_adversaries": 0, "detection_rate": 0.2},
    ]

    def test_scenario_lookup(self, tmp_path):
        gt = _write_data(tmp_path, colony_results=self.ROWS)
        assert gt.colony_field("a", "detection_rate") == pytest.approx(0.8)

    def test_unknown_scenario_raises(self, tmp_path):
        gt = _write_data(tmp_path, colony_results=self.ROWS)
        with pytest.raises(ClaimDataUnavailable, match="no scenario"):
            gt.colony_scenario("zzz")

    def test_unknown_field_raises(self, tmp_path):
        gt = _write_data(tmp_path, colony_results=self.ROWS)
        with pytest.raises(ClaimDataUnavailable, match="ccs_score"):
            gt.colony_field("a", "ccs_score")

    def test_multi_repeat_schema_reads_the_mean(self, tmp_path):
        rows = [
            {
                "scenario": "a",
                "n_agents": 20,
                "n_adversaries": 2,
                "detection_rate_mean": 0.75,
                "detection_rate_values": [0.7, 0.8],
            }
        ]
        gt = _write_data(tmp_path, colony_results=rows)
        assert gt.colony_field("a", "detection_rate") == pytest.approx(0.75)

    def test_values_list_is_averaged_when_no_mean_is_recorded(self, tmp_path):
        rows = [
            {
                "scenario": "a",
                "n_agents": 20,
                "n_adversaries": 2,
                "recovery_steps_values": [8, 9, 10],
            }
        ]
        gt = _write_data(tmp_path, colony_results=rows)
        assert gt.colony_field("a", "recovery_steps") == pytest.approx(9.0)

    def test_empty_values_list_still_raises(self, tmp_path):
        rows = [{"scenario": "a", "n_agents": 5, "n_adversaries": 1, "ccs_score_values": []}]
        gt = _write_data(tmp_path, colony_results=rows)
        with pytest.raises(ClaimDataUnavailable, match="ccs_score"):
            gt.colony_field("a", "ccs_score")

    def test_structured_range_excludes_adversary_free_scenarios(self, tmp_path):
        """The 0.2 row has no adversaries, so it must not widen the range."""
        gt = _write_data(tmp_path, colony_results=self.ROWS)
        assert gt.colony_structured_dr_min() == pytest.approx(0.8)
        assert gt.colony_structured_dr_max() == pytest.approx(1.0)

    def test_no_adversarial_scenarios_raises(self, tmp_path):
        gt = _write_data(
            tmp_path,
            colony_results=[{"scenario": "c", "n_agents": 5, "n_adversaries": 0}],
        )
        with pytest.raises(ClaimDataUnavailable, match="adversarial"):
            gt.colony_structured_dr_min()

    def test_agent_range(self, tmp_path):
        gt = _write_data(tmp_path, colony_results=self.ROWS)
        assert gt.colony_agents_min() == pytest.approx(20.0)
        assert gt.colony_agents_max() == pytest.approx(100.0)

    def test_dict_wrapped_scenarios_supported(self, tmp_path):
        gt = _write_data(tmp_path, colony_results={"scenarios": self.ROWS})
        assert gt.colony_agents_max() == pytest.approx(100.0)

    def test_empty_rows_raise(self, tmp_path):
        gt = _write_data(tmp_path, colony_results=[])
        with pytest.raises(ClaimDataUnavailable, match="no scenario rows"):
            gt.colony()


class TestGroundTruthParametric:
    """Parametric-simulation accessors."""

    ROWS = [
        {"architecture": "A", "n_attacks": 10, "detection_rate": 0.9},
        {"architecture": "A", "n_attacks": 10, "detection_rate": 1.0},
        {"architecture": "B", "n_attacks": 30, "detection_rate": 0.8},
    ]

    def test_overall_and_per_architecture(self, tmp_path):
        gt = _write_data(tmp_path, full_evaluation_results=self.ROWS)
        assert gt.parametric_overall_dr() == pytest.approx(0.9)
        assert gt.parametric_arch_dr("A") == pytest.approx(0.95)
        assert gt.parametric_dr_min() == pytest.approx(0.8)
        assert gt.parametric_dr_max() == pytest.approx(1.0)
        assert gt.parametric_instances() == pytest.approx(50.0)

    def test_unknown_architecture_raises(self, tmp_path):
        gt = _write_data(tmp_path, full_evaluation_results=self.ROWS)
        with pytest.raises(ClaimDataUnavailable, match="architecture"):
            gt.parametric_arch_dr("Z")

    def test_corpus_size_requires_agreement(self, tmp_path):
        gt = _write_data(tmp_path, full_evaluation_results=self.ROWS)
        with pytest.raises(ClaimDataUnavailable, match="disagree on corpus size"):
            gt.attack_corpus_size()

    def test_corpus_size_when_architectures_agree(self, tmp_path):
        rows = [
            {"architecture": "A", "n_attacks": 25, "detection_rate": 0.9},
            {"architecture": "B", "n_attacks": 25, "detection_rate": 0.9},
        ]
        gt = _write_data(tmp_path, full_evaluation_results=rows)
        assert gt.attack_corpus_size() == pytest.approx(25.0)

    def test_empty_rows_raise(self, tmp_path):
        gt = _write_data(tmp_path, full_evaluation_results=[])
        with pytest.raises(ClaimDataUnavailable, match="no rows"):
            gt.parametric()


class TestGroundTruthStatistics:
    """Statistical / cross-validation / LLM accessors."""

    def test_cohens_d_and_kruskal(self, tmp_path):
        gt = _write_data(
            tmp_path,
            statistical_results={
                "cohens_d_cif_vs_baseline": 3.5,
                "kruskal_wallis": {"h": 14.0, "p": 0.002},
            },
        )
        assert gt.cohens_d() == pytest.approx(3.5)
        assert gt.kruskal_wallis("h") == pytest.approx(14.0)
        assert gt.kruskal_wallis("p") == pytest.approx(0.002)

    def test_missing_cohens_d_raises(self, tmp_path):
        gt = _write_data(tmp_path, statistical_results={})
        with pytest.raises(ClaimDataUnavailable, match="cohens_d"):
            gt.cohens_d()

    def test_missing_kruskal_field_raises(self, tmp_path):
        gt = _write_data(tmp_path, statistical_results={"kruskal_wallis": {"h": 1.0}})
        with pytest.raises(ClaimDataUnavailable, match="kruskal_wallis.p"):
            gt.kruskal_wallis("p")

    def test_non_object_statistical_raises(self, tmp_path):
        gt = _write_data(tmp_path, statistical_results=[])
        with pytest.raises(ClaimDataUnavailable, match="not a JSON object"):
            gt.statistical()

    def test_cross_validation_field(self, tmp_path):
        gt = _write_data(tmp_path, cross_validation_results={"mean_tpr": 0.16})
        assert gt.cross_validation("mean_tpr") == pytest.approx(0.16)

    def test_cross_validation_missing_field_raises(self, tmp_path):
        gt = _write_data(tmp_path, cross_validation_results={})
        with pytest.raises(ClaimDataUnavailable, match="mean_tpr"):
            gt.cross_validation("mean_tpr")

    def test_llm_accessors_with_measurements(self, tmp_path):
        gt = _write_data(
            tmp_path,
            llm_demo_results={
                "multiagent_results": {"claude_code": {"detection_rate": 0.8, "total": 5}}
            },
        )
        assert gt.llm_detection_rate("claude_code") == pytest.approx(0.8)
        assert gt.llm_total("claude_code") == pytest.approx(5.0)

    def test_llm_missing_architecture_raises(self, tmp_path):
        gt = _write_data(tmp_path, llm_demo_results={"multiagent_results": {}})
        with pytest.raises(ClaimDataUnavailable, match="crewai"):
            gt.llm_detection_rate("crewai")
        with pytest.raises(ClaimDataUnavailable, match="crewai"):
            gt.llm_total("crewai")

    def test_llm_missing_fields_raise(self, tmp_path):
        gt = _write_data(
            tmp_path, llm_demo_results={"multiagent_results": {"claude_code": {}}}
        )
        with pytest.raises(ClaimDataUnavailable, match="detection_rate"):
            gt.llm_detection_rate("claude_code")
        with pytest.raises(ClaimDataUnavailable, match="total"):
            gt.llm_total("claude_code")

    def test_llm_non_object_payload_raises(self, tmp_path):
        gt = _write_data(tmp_path, llm_demo_results=[1])
        with pytest.raises(ClaimDataUnavailable, match="not a JSON object"):
            gt.llm_detection_rate("claude_code")
        with pytest.raises(ClaimDataUnavailable, match="not a JSON object"):
            gt.llm_total("claude_code")


# ── report rendering ────────────────────────────────────────────────────


class TestClaimReport:
    """Report aggregation and rendering."""

    def _report(self, tmp_path) -> ClaimReport:
        manuscript = tmp_path / "m"
        manuscript.mkdir()
        (manuscript / "doc.md").write_text("good 0.200 bad 0.900\n", encoding="utf-8")
        gt = _write_data(tmp_path / "d", ablation_results=_ablation())
        claims = [
            _claim("ok", r"good (\d+\.\d+)", lambda g: g.full_pipeline_tpr()),
            _claim("bad", r"bad (\d+\.\d+)", lambda g: g.full_pipeline_tpr()),
            _claim("dead", r"absent (\d+\.\d+)", lambda g: g.full_pipeline_tpr()),
        ]
        return verify_claims(claims, manuscript, gt)

    def test_counts(self, tmp_path):
        report = self._report(tmp_path)
        assert len(report.matched) == 1
        assert len(report.mismatched) == 1
        assert len(report.not_found) == 1
        assert len(report.unbacked) == 0
        assert len(report.failures) == 2
        assert not report.ok

    def test_empty_report_is_ok(self):
        assert ClaimReport(()).ok

    def test_render_table_lists_every_row(self, tmp_path):
        table = self._report(tmp_path).render_table()
        assert "CLAIM" in table and "VERDICT" in table
        for claim_id in ("ok", "bad", "dead"):
            assert claim_id in table

    def test_render_only_failures_drops_the_match(self, tmp_path):
        table = self._report(tmp_path).render_table(only_failures=True)
        assert "bad" in table and "dead" in table
        assert not any(line.startswith("ok ") for line in table.splitlines())

    def test_render_table_with_no_rows(self):
        table = ClaimReport(()).render_table()
        assert table.splitlines()[0].startswith("CLAIM")

    def test_to_dict_is_json_serialisable(self, tmp_path):
        payload = self._report(tmp_path).to_dict()
        json.dumps(payload)
        assert payload["counts"]["total"] == 3
        assert payload["counts"]["failures"] == 2
        assert payload["ok"] is False
        assert {r["claim_id"] for r in payload["results"]} == {"ok", "bad", "dead"}

    def test_delta_is_none_without_both_values(self, tmp_path):
        report = self._report(tmp_path)
        dead = next(r for r in report.results if r.claim_id == "dead")
        assert dead.delta is None


# ── the shipped registry, against the shipped artifacts ─────────────────


@pytest.fixture(scope="module")
def real_report() -> ClaimReport:
    """The registry run against the shipped manuscript and data."""
    return verify_claims(CLAIMS, REAL_MANUSCRIPT, GroundTruth(REAL_DATA))


class TestShippedRegistry:
    """Binding tests: the registry must actually watch the real manuscript."""

    def test_registry_is_not_theatre(self):
        assert len(CLAIMS) >= 150, "a registry this small cannot cover the headline numbers"

    def test_claim_ids_are_unique(self):
        ids = claim_ids()
        assert len(ids) == len(set(ids))

    def test_registry_spans_every_numeric_manuscript_file(self):
        expected = {
            "00_abstract.md",
            "04_experimental_setup.md",
            "05_results.md",
            "05b_statistical_significance.md",
            "05d_ablation_and_scalability.md",
            "06_discussion.md",
            "07_conclusion.md",
            "S08_parametric_analysis.md",
        }
        assert expected <= {claim.file for claim in CLAIMS}

    def test_headline_numbers_are_registered(self):
        """The values the audit found fabricated must all be watched."""
        ids = set(claim_ids())
        for required in (
            "abstract.ms_mean",
            "abstract.ms_ci_low",
            "abstract.ms_ci_high",
            "05b.full_pipeline_tpr",
            "results.ms_cv_row",
            "results.ms_min_row",
            "results.ms_max_row",
            "05d.synergy.tripwire_detection",
            "05d.synergy.firewall_detection",
            "colony.dr.sybil_infiltration",
            "abstract.ablation_corpus_size",
        ):
            assert required in ids
        # every component-removal delta from the ablation artifact
        for component in (
            "detection",
            "trust_calculus",
            "firewall",
            "invariants",
            "tripwire",
            "consensus",
            "provenance",
            "sandbox",
        ):
            assert f"05d.delta.{component}" in ids
            assert f"05d.tpr.{component}" in ids

    def test_no_registered_pattern_is_dead(self, real_report):
        """Anti-vacuity: every pattern must locate its value in the prose.

        A NOT_FOUND here means the registry has silently stopped watching a
        number - which is the exact failure mode the injector had. Claims
        already tracked in ``KNOWN_UNRECONCILED`` are excluded; the gate is
        that no *new* dead patterns appear beyond the pinned set.
        """
        dead = sorted(r.claim_id for r in real_report.not_found)
        new_dead = sorted(set(dead) - KNOWN_UNRECONCILED)
        assert new_dead == [], f"new dead patterns (not in KNOWN_UNRECONCILED): {new_dead}"

    def test_most_claims_already_match(self, real_report):
        """The registry is not uniformly red - the tolerances are calibrated."""
        assert len(real_report.matched) >= 70

    def test_no_new_drift_beyond_the_pinned_set(self, real_report):
        failing = {r.claim_id for r in real_report.failures}
        new = sorted(failing - KNOWN_UNRECONCILED)
        assert new == [], f"new unsupported manuscript numbers: {new}"

    def test_pinned_set_only_names_real_claims(self):
        stale = sorted(KNOWN_UNRECONCILED - set(claim_ids()))
        assert stale == [], f"KNOWN_UNRECONCILED names claims that no longer exist: {stale}"

    def test_the_gate_is_currently_red(self, real_report):
        """Documents the state this wave hands to manuscript reconciliation."""
        assert not real_report.ok
        assert len(real_report.failures) > 0


class TestShippedRegistryPositiveControls:
    """The registry must reject a perturbed copy of the real manuscript."""

    @staticmethod
    def _copy(tmp_path: Path) -> Path:
        target = tmp_path / "manuscript"
        shutil.copytree(REAL_MANUSCRIPT, target)
        return target

    @staticmethod
    def _result(report: ClaimReport, claim_id: str):
        return next(r for r in report.results if r.claim_id == claim_id)

    def test_perturbed_value_flips_match_to_mismatch(self, tmp_path):
        """POSITIVE CONTROL 1: change a number, the checker must say MISMATCH."""
        gt = GroundTruth(REAL_DATA)
        baseline = self._result(verify_claims(CLAIMS, REAL_MANUSCRIPT, gt), "abstract.ms_mean")
        assert baseline.verdict == "MATCH", "control precondition: this claim starts green"

        manuscript = self._copy(tmp_path)
        abstract = manuscript / "00_abstract.md"
        text = abstract.read_text(encoding="utf-8")
        perturbed = text.replace(
            "mean detection rate of 44.8\\%", "mean detection rate of 99.9\\%"
        )
        assert perturbed != text, "control precondition: the target string must exist"
        abstract.write_text(perturbed, encoding="utf-8")

        after = self._result(verify_claims(CLAIMS, manuscript, gt), "abstract.ms_mean")
        assert after.verdict == "MISMATCH"
        assert after.stated == pytest.approx(0.999)
        assert after.derived == pytest.approx(0.448)

    def test_reworded_prose_is_reported_not_found(self, tmp_path):
        """POSITIVE CONTROL 2: break the pattern, the checker must say NOT_FOUND.

        This is the defect MISS-01 documents: a regex that matches nothing
        must not be indistinguishable from a passing check.
        """
        gt = GroundTruth(REAL_DATA)
        manuscript = self._copy(tmp_path)
        abstract = manuscript / "00_abstract.md"
        text = abstract.read_text(encoding="utf-8")
        reworded = text.replace(
            "mean detection rate of 44.8\\%", "an average detection rate of 44.8 percent"
        )
        assert reworded != text
        abstract.write_text(reworded, encoding="utf-8")

        report = verify_claims(CLAIMS, manuscript, gt)
        result = self._result(report, "abstract.ms_mean")
        assert result.verdict == "NOT_FOUND"
        assert result.n_matches == 0
        assert result.is_failure
        assert result.claim_id in {r.claim_id for r in report.failures}

    def test_deleting_a_manuscript_file_is_caught(self, tmp_path):
        gt = GroundTruth(REAL_DATA)
        manuscript = self._copy(tmp_path)
        (manuscript / "07_conclusion.md").unlink()
        report = verify_claims(CLAIMS, manuscript, gt)
        conclusion = [r for r in report.results if r.file == "07_conclusion.md"]
        assert conclusion
        assert all(r.verdict == "NOT_FOUND" for r in conclusion)

    def test_missing_data_directory_makes_every_claim_unbacked(self, tmp_path):
        """POSITIVE CONTROL 3: no data means UNBACKED, never a silent pass.

        Dead patterns (NOT_FOUND) also block a silent pass, so the assertion
        covers both UNBACKED and NOT_FOUND as acceptable non-passing verdicts.
        """
        report = verify_claims(CLAIMS, REAL_MANUSCRIPT, GroundTruth(tmp_path / "nowhere"))
        assert len(report.unbacked) + len(report.not_found) == len(CLAIMS)
        assert not report.ok


class TestVerifyClaimsCli:
    """The CI gate itself: scripts/verify_claims.py."""

    SCRIPT = PROJECT_ROOT / "scripts" / "verify_claims.py"

    def _run(self, tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
        env = dict(os.environ, MPLBACKEND="Agg", PYTHONDONTWRITEBYTECODE="1")
        return subprocess.run(
            [sys.executable, str(self.SCRIPT), *args],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            env=env,
            timeout=120,
            check=False,
        )

    def test_exits_nonzero_on_the_current_tree(self, tmp_path):
        """Run from an unrelated cwd: defaults must resolve to the project."""
        proc = self._run(tmp_path)
        assert proc.returncode == 1
        assert "FAILED:" in proc.stdout
        assert "VERDICT" in proc.stdout

    def test_writes_a_parseable_json_report(self, tmp_path):
        out = tmp_path / "nested" / "report.json"
        proc = self._run(tmp_path, "--only-failures", "--json", str(out))
        assert proc.returncode == 1
        payload = json.loads(out.read_text(encoding="utf-8"))
        assert payload["counts"]["total"] == len(CLAIMS)
        assert payload["ok"] is False

    def test_missing_data_dir_still_fails_closed(self, tmp_path):
        """No data must never be reported as 'everything checks out'."""
        proc = self._run(tmp_path, "--data", str(tmp_path / "nowhere"))
        assert proc.returncode == 1
        assert "UNBACKED" in proc.stdout
        assert "OK:" not in proc.stdout

    def test_help_is_available(self, tmp_path):
        proc = self._run(tmp_path, "--help")
        assert proc.returncode == 0
        assert "--manuscript" in proc.stdout


class TestUnitsOnRealClaims:
    """Every registered claim declares a coherent unit/tolerance pair."""

    def test_units_are_known(self):
        assert {c.unit for c in CLAIMS} <= {"fraction", "percent", "count"}

    def test_provenances_are_known(self):
        assert {c.provenance for c in CLAIMS} <= {"real", "parametric", "illustrative"}

    def test_count_claims_use_exact_tolerance(self):
        # Most count claims are exact; colony *recovery* is a mean over
        # per-seed values reported to one decimal, so it uses RECOVERY_TOL.
        allowed = {EXACT, RECOVERY_TOL}
        for claim in CLAIMS:
            if claim.unit == "count":
                assert claim.tolerance in allowed, claim.id

    def test_percent_claims_have_sane_tolerance(self):
        for claim in CLAIMS:
            if claim.unit == "percent":
                assert PCT1 <= claim.tolerance <= 0.01, claim.id
