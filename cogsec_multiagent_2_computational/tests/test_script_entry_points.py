"""Honesty tests for the entry-point scripts in ``scripts/``.

These bind the *verdict* each script reports, not just that it runs:

* ``verify_formal_specs.py`` — an absent model checker must never exit 0.
* ``run_formal_validation.py`` — the theorem total must count distinct
  theorems, and a double-registered validator must be refused.
* ``auto_number_figures.py`` — the cross-reference check must be able to fail
  and must refuse to pass vacuously.
* ``verify_manuscript.py`` — importing the module must have no filesystem
  side effects.

Every assertion here has a paired positive control: a constructed violating
input that the code under test rejects.  A test that would stay green with the
production logic inverted is worthless.

No mocks — real files under ``tmp_path``, real subprocesses, real objects.
"""

from __future__ import annotations

import importlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = str(_PROJECT_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

auto_number_figures = importlib.import_module("auto_number_figures")
run_formal_validation = importlib.import_module("run_formal_validation")
verify_formal_specs = importlib.import_module("verify_formal_specs")
verify_manuscript = importlib.import_module("verify_manuscript")

from formal.spec_verifier import VerificationResult, VerificationStatus  # noqa: E402
from formal.theorem_registry import TheoremResult, TheoremStatus  # noqa: E402

# ---------------------------------------------------------------------------
# verify_formal_specs.py — audit SCRIPT-02
# ---------------------------------------------------------------------------


def _result(status: VerificationStatus) -> VerificationResult:
    return VerificationResult("tool", status, "detail")


class TestVerifyFormalSpecsExitCode:
    """The exit code must distinguish "verified" from "not verified"."""

    def test_all_passed_is_zero(self):
        results = {
            "NuSMV": _result(VerificationStatus.PASSED),
            "SPIN": _result(VerificationStatus.PASSED),
            "TLA+": _result(VerificationStatus.PASSED),
        }
        assert verify_formal_specs.decide_exit_code(results) == 0

    @pytest.mark.parametrize(
        "status",
        [
            VerificationStatus.SKIPPED,
            VerificationStatus.ERROR,
            VerificationStatus.INCONCLUSIVE,
        ],
    )
    def test_single_non_verifying_tool_blocks_zero(self, status):
        """Positive control: flip ONE tool off PASS and 0 must disappear.

        This is the inverted-logic guard — with the old `main()` (which never
        inspected the statuses) every one of these cases returned 0.
        """
        results = {
            "NuSMV": _result(VerificationStatus.PASSED),
            "SPIN": _result(status),
            "TLA+": _result(VerificationStatus.PASSED),
        }
        assert verify_formal_specs.decide_exit_code(results) == 2

    def test_failure_outranks_skip(self):
        results = {
            "NuSMV": _result(VerificationStatus.FAILED),
            "SPIN": _result(VerificationStatus.SKIPPED),
        }
        assert verify_formal_specs.decide_exit_code(results) == 1

    def test_empty_results_is_not_verified(self):
        """Verifying nothing is not verifying."""
        assert verify_formal_specs.decide_exit_code({}) == 2

    def test_write_evidence_records_non_verification(self, tmp_path):
        results = {"NuSMV": _result(VerificationStatus.SKIPPED)}
        path = verify_formal_specs.write_evidence(tmp_path, results)
        payload = json.loads(path.read_text())
        assert payload["verified"] is False
        assert payload["exit_code"] == 2
        assert payload["tools"]["NuSMV"]["status"] == "SKIP"

    def test_write_evidence_records_verification(self, tmp_path):
        results = {"NuSMV": _result(VerificationStatus.PASSED)}
        payload = json.loads(
            verify_formal_specs.write_evidence(tmp_path, results).read_text()
        )
        assert payload["verified"] is True
        assert payload["exit_code"] == 0

    @pytest.mark.skipif(
        any(shutil.which(t) for t in ("NuSMV", "spin", "tlc")),
        reason="a model checker is installed; this test asserts the absent-tool path",
    )
    def test_main_returns_two_when_no_checker_installed(self, tmp_path, capsys):
        """End-to-end: on a machine with no checkers, main() must not return 0."""
        code = verify_formal_specs.main(["--output-dir", str(tmp_path)])
        assert code == 2
        assert "NOT VERIFIED" in capsys.readouterr().out
        assert (tmp_path / "verification_summary.json").exists()

    @pytest.mark.skipif(
        any(shutil.which(t) for t in ("NuSMV", "spin", "tlc")),
        reason="a model checker is installed; this test asserts the absent-tool path",
    )
    def test_allow_unverified_flag_downgrades_only_code_two(self, tmp_path):
        code = verify_formal_specs.main(
            ["--output-dir", str(tmp_path), "--allow-unverified"]
        )
        assert code == 0


# ---------------------------------------------------------------------------
# run_formal_validation.py — audit SCRIPT-03
# ---------------------------------------------------------------------------


def _thm(theorem_id: str, status: TheoremStatus = TheoremStatus.PASSED) -> TheoremResult:
    return TheoremResult(theorem_id=theorem_id, name=theorem_id, status=status)


class TestFormalValidationCounting:
    """The headline "N/N theorems" must count theorems, not registry rows."""

    def test_no_duplicates_on_clean_results(self):
        results = [_thm("3.1"), _thm("3.2"), _thm("4")]
        assert run_formal_validation.duplicate_theorem_ids(results) == {}

    def test_duplicate_is_detected(self):
        """Positive control: reproduce the exact defect the audit found.

        The old script registered ``validate_trust_bound`` under both ``3.1``
        and ``3.1a``; both rows reported ``theorem_id="3.1"``.
        """
        results = [_thm("3.1"), _thm("3.1"), _thm("3.2")]
        assert run_formal_validation.duplicate_theorem_ids(results) == {"3.1": 2}

    def test_distinct_counts_collapse_duplicates(self):
        results = [_thm("3.1"), _thm("3.1"), _thm("3.2")]
        counts = run_formal_validation.distinct_status_counts(results)
        assert sum(counts.values()) == 2, "duplicate theorem inflated the total"
        assert counts["passed"] == 2

    def test_distinct_counts_track_failures(self):
        results = [
            _thm("3.1"),
            _thm("3.2", TheoremStatus.FAILED),
            _thm("4", TheoremStatus.ERROR),
        ]
        counts = run_formal_validation.distinct_status_counts(results)
        assert counts == {"passed": 1, "failed": 1, "skipped": 0, "error": 1}

    def test_live_registry_has_twelve_distinct_theorems(self):
        """Bind the published theorem count to the registry, not to prose."""
        from formal.theorem_registry import TheoremRegistry

        results = TheoremRegistry().validate_all(seed=42)
        assert run_formal_validation.duplicate_theorem_ids(results) == {}
        counts = run_formal_validation.distinct_status_counts(results)
        assert sum(counts.values()) == 12
        assert counts["passed"] == 12

    def test_main_reports_twelve_and_writes_structured_json(self, tmp_path, capsys):
        code = run_formal_validation.main(["--seed", "42", "--output", str(tmp_path)])
        assert code == 0
        out = capsys.readouterr().out
        assert "12/12 distinct theorems validated" in out
        assert "16/16" not in out
        payload = json.loads(
            (tmp_path / "formal_validation_results.json").read_text()
        )
        assert payload["n_distinct_theorems"] == 12
        assert payload["n_registry_entries"] == 12
        assert len(payload["theorems"]) == 12
        ids = [t["theorem_id"] for t in payload["theorems"]]
        assert len(set(ids)) == len(ids), f"duplicate theorem ids persisted: {ids}"


# ---------------------------------------------------------------------------
# auto_number_figures.py — audit SCRIPT-04
# ---------------------------------------------------------------------------


class TestCrefVerification:
    """The cross-reference check must be able to fail, and never pass vacuously."""

    def test_resolved_target_produces_no_warning(self, tmp_path):
        (tmp_path / "a.md").write_text("See \\Cref{fig:alpha} here.\n")
        warnings, n = auto_number_figures.verify_cref_targets(
            tmp_path, {"fig:alpha": {"type": "figure"}}
        )
        assert warnings == []
        assert n == 1

    def test_unresolved_target_is_reported(self, tmp_path):
        """Positive control: an unknown target must be flagged."""
        (tmp_path / "a.md").write_text("See \\Cref{fig:missing} here.\n")
        warnings, n = auto_number_figures.verify_cref_targets(
            tmp_path, {"fig:alpha": {"type": "figure"}}
        )
        assert n == 1
        assert len(warnings) == 1
        assert "fig:missing" in warnings[0]

    def test_tbl_prefix_is_normalised_to_tab(self, tmp_path):
        (tmp_path / "a.md").write_text("\\cref{tbl:one}\n")
        warnings, n = auto_number_figures.verify_cref_targets(
            tmp_path, {"tab:one": {"type": "table"}}
        )
        assert (warnings, n) == ([], 1)

    def test_main_exits_two_on_unresolved_target(self, tmp_path):
        """Positive control at the CLI boundary."""
        msc = tmp_path / "manuscript"
        msc.mkdir()
        (msc / "a.md").write_text("\\Cref{fig:nope}\n")
        registry = tmp_path / "reg.json"
        registry.write_text(json.dumps({"fig:alpha": {"type": "figure"}}))
        code = auto_number_figures.main(
            ["--root", str(msc), "--registry", str(registry)]
        )
        assert code == 2

    def test_main_exits_one_when_check_would_be_vacuous(self, tmp_path):
        """Zero targets is a broken run, not a clean one."""
        msc = tmp_path / "manuscript"
        msc.mkdir()
        (msc / "a.md").write_text("No cross references at all.\n")
        registry = tmp_path / "reg.json"
        registry.write_text(json.dumps({"fig:alpha": {"type": "figure"}}))
        code = auto_number_figures.main(
            ["--root", str(msc), "--registry", str(registry)]
        )
        assert code == 1

    def test_main_exits_zero_on_clean_manuscript(self, tmp_path):
        msc = tmp_path / "manuscript"
        msc.mkdir()
        (msc / "a.md").write_text("\\Cref{fig:alpha} and \\Cref{tab:one}\n")
        registry = tmp_path / "reg.json"
        registry.write_text(
            json.dumps({"fig:alpha": {"type": "figure"}, "tab:one": {"type": "table"}})
        )
        assert (
            auto_number_figures.main(
                ["--root", str(msc), "--registry", str(registry)]
            )
            == 0
        )

    def test_dead_label_injector_is_gone(self):
        """The no-op ``inject_latex_label`` must not come back.

        It advertised a transformation whose body was ``return content, 0``.
        pandoc-crossref emits ``\\label{}`` from the ``{#fig:...}`` attribute
        blocks, so a manual injector would duplicate labels.
        """
        assert not hasattr(auto_number_figures, "inject_latex_label")

    def test_lof_lot_injection_is_idempotent(self, tmp_path):
        preamble = tmp_path / "preamble.md"
        preamble.write_text("---\n```{=latex}\n\\usepackage{x}\n```\n")
        assert auto_number_figures.ensure_lof_lot_in_preamble(preamble) is True
        text = preamble.read_text()
        assert "\\listoffigures" in text and "\\listoftables" in text
        # Second call must be a no-op, not a second injection.
        assert auto_number_figures.ensure_lof_lot_in_preamble(preamble) is False
        assert preamble.read_text() == text

    def test_lof_lot_dry_run_does_not_write(self, tmp_path):
        preamble = tmp_path / "preamble.md"
        original = "---\n```{=latex}\n\\usepackage{x}\n```\n"
        preamble.write_text(original)
        assert (
            auto_number_figures.ensure_lof_lot_in_preamble(preamble, dry_run=True)
            is True
        )
        assert preamble.read_text() == original

    def test_missing_registry_exits_one(self, tmp_path):
        with pytest.raises(SystemExit) as exc:
            auto_number_figures.load_registry(tmp_path / "absent.json")
        assert exc.value.code == 1

    def test_real_manuscript_resolves_every_cref(self):
        """Anti-vacuity: the project's own manuscript must supply real targets."""
        registry_path = _PROJECT_ROOT / "output" / "data" / "figure_registry.json"
        manuscript_dir = _PROJECT_ROOT / "manuscript"
        if not registry_path.exists() or not manuscript_dir.exists():
            pytest.skip("figure registry or manuscript not present in this checkout")
        registry = json.loads(registry_path.read_text())
        warnings, n = auto_number_figures.verify_cref_targets(manuscript_dir, registry)
        assert n >= auto_number_figures.MIN_CREF_TARGETS
        assert n > 10, f"only {n} cross-references found — check would be near-vacuous"
        assert warnings == []


# ---------------------------------------------------------------------------
# verify_manuscript.py — audit TEST-16 / CI-03
# ---------------------------------------------------------------------------


class TestVerifyManuscriptLogging:
    """Importing the module must not touch the filesystem."""

    def test_import_creates_no_log_in_cwd(self, tmp_path, monkeypatch):
        """Positive control: a read-only CWD used to make the import raise.

        Run the import in a *child* interpreter whose CWD is a directory the
        process cannot write to.  Under the old module-level
        ``logging.FileHandler("manuscript_verification.log")`` this raised
        ``PermissionError`` before any code ran.
        """
        readonly = tmp_path / "readonly"
        readonly.mkdir()
        os.chmod(readonly, 0o555)
        try:
            proc = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    (
                        "import sys; sys.path.insert(0, %r);"
                        "import verify_manuscript as vm;"
                        "print(vm.ManuscriptVerifier.__name__)" % _SCRIPTS
                    ),
                ],
                cwd=str(readonly),
                capture_output=True,
                text=True,
                timeout=120,
            )
        finally:
            os.chmod(readonly, 0o755)
        assert proc.returncode == 0, proc.stderr[-800:]
        assert "ManuscriptVerifier" in proc.stdout
        assert not (readonly / "manuscript_verification.log").exists()

    def test_default_log_path_is_under_output(self):
        """The log must not live at the repo root where it was git-tracked."""
        default = verify_manuscript.DEFAULT_LOG_PATH
        assert default.parent.name == "logs"
        assert default.parent.parent.name == "output"

    def test_configure_logging_creates_parent_and_truncates(self, tmp_path):
        import logging

        log_path = tmp_path / "deep" / "nested" / "run.log"
        verify_manuscript.configure_logging(log_path)
        logging.getLogger(__name__).info("first-run-marker")
        logging.shutdown()
        assert "first-run-marker" in log_path.read_text()

        # A second run must overwrite, not append — the tracked log grew to
        # 408 KB precisely because the handler opened in append mode.
        verify_manuscript.configure_logging(log_path)
        logging.getLogger(__name__).info("second-run-marker")
        logging.shutdown()
        text = log_path.read_text()
        assert "second-run-marker" in text
        assert "first-run-marker" not in text

    def test_configure_logging_none_writes_no_file(self, tmp_path, monkeypatch):
        import logging

        monkeypatch.chdir(tmp_path)
        verify_manuscript.configure_logging(None)
        logging.getLogger(__name__).info("stdout-only")
        logging.shutdown()
        assert list(tmp_path.iterdir()) == []

    def test_main_returns_zero_on_the_projects_own_manuscript(self, tmp_path):
        manuscript_dir = _PROJECT_ROOT / "manuscript"
        if not manuscript_dir.exists():
            pytest.skip("manuscript directory not present")
        code = verify_manuscript.main(
            ["--root", str(manuscript_dir), "--log", str(tmp_path / "v.log")]
        )
        assert code == 0

    def test_main_returns_one_on_a_broken_manuscript(self, tmp_path):
        """Positive control: the verifier's exit code must be able to be 1."""
        empty = tmp_path / "manuscript"
        empty.mkdir()
        code = verify_manuscript.main(
            ["--root", str(empty), "--log", str(tmp_path / "v.log")]
        )
        assert code == 1
