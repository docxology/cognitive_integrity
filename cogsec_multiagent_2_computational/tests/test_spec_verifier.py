"""Tests for src/formal/spec_verifier.py.

Covers:
- check_tool: returns path string or None.
- run_command: structured CommandOutcome, including launch failures.
- verify_* tool-absent path.
- generate_and_verify_all: writes spec files and returns VerificationResults.

No external model checkers are required; without them all three verifiers must
report SKIPPED.  Tool-present behaviour is exercised in
``test_spec_verifier_extended.py`` with real executable shims on PATH.
"""

from __future__ import annotations

import shutil

from formal.spec_verifier import (
    VerificationResult,
    VerificationStatus,
    check_tool,
    generate_and_verify_all,
    run_command,
    verify_nusmv,
    verify_spin,
    verify_tla,
)

# ---------------------------------------------------------------------------
# check_tool
# ---------------------------------------------------------------------------


class TestCheckTool:
    """Tests for check_tool()."""

    def test_python_is_found(self):
        """Python (or python3) should be findable via shutil.which."""
        result = check_tool("python3") or check_tool("python")
        # At least one should be non-None
        assert result is not None or check_tool("python") is not None

    def test_nonexistent_tool_returns_none(self):
        result = check_tool("__definitely_not_a_real_tool_xyz123__")
        assert result is None

    def test_returns_string_when_found(self):
        # Use a tool that is almost certainly present: 'ls' or 'echo'
        found = check_tool("ls") or check_tool("echo")
        if found is not None:
            assert isinstance(found, str)

    def test_echo_or_sh_is_found(self):
        result = check_tool("echo") or check_tool("sh") or check_tool("bash")
        assert result is not None


# ---------------------------------------------------------------------------
# run_command
# ---------------------------------------------------------------------------


class TestRunCommand:
    """Tests for run_command()."""

    def test_echo_returns_expected_output(self, tmp_path):
        outcome = run_command(["echo", "hello_spec_verifier"], cwd=tmp_path)
        assert outcome.executed
        assert outcome.returncode == 0
        assert "hello_spec_verifier" in outcome.stdout
        assert outcome.error == ""

    def test_nonexistent_command_reports_launch_failure(self, tmp_path):
        """A missing binary must be flagged as *not executed*.

        The old implementation folded this into a free-text string that
        happened not to contain the word "error", which the SPIN verdict logic
        then read as a pass.
        """
        outcome = run_command(
            ["__totally_nonexistent_binary_xyz__", "--flag"], cwd=tmp_path
        )
        assert outcome.executed is False
        assert outcome.returncode is None
        assert outcome.error != ""

    def test_unusable_cwd_reports_launch_failure(self, tmp_path):
        """A vanished working directory is a launch failure, not a success."""
        outcome = run_command(["echo", "hi"], cwd=tmp_path / "does_not_exist")
        assert outcome.executed is False
        assert outcome.error != ""

    def test_failing_command_is_executed_with_nonzero_exit(self, tmp_path):
        outcome = run_command(
            ["ls", "/nonexistent_path_xyz_that_does_not_exist"], cwd=tmp_path
        )
        assert outcome.executed is True
        assert outcome.returncode != 0

    def test_timeout_reports_launch_failure(self, tmp_path):
        outcome = run_command(["sleep", "5"], cwd=tmp_path, timeout=0.2)
        assert outcome.executed is False
        assert "timed out" in outcome.error

    def test_combined_includes_both_streams(self, tmp_path):
        outcome = run_command(
            ["sh", "-c", "echo out; echo err 1>&2"], cwd=tmp_path
        )
        assert "out" in outcome.combined
        assert "err" in outcome.combined


# ---------------------------------------------------------------------------
# verify_nusmv / verify_spin / verify_tla — tool-absent path
# ---------------------------------------------------------------------------


class TestVerifyToolsAbsent:
    """When the external verification tools are absent, verifiers SKIP."""

    def test_verify_nusmv_skip_when_absent(self, tmp_path, monkeypatch):
        monkeypatch.setattr(shutil, "which", lambda name: None)
        result = verify_nusmv(tmp_path / "dummy.smv")
        assert result.status is VerificationStatus.SKIPPED
        assert result.passed is False

    def test_verify_spin_skip_when_absent(self, tmp_path, monkeypatch):
        monkeypatch.setattr(shutil, "which", lambda name: None)
        result = verify_spin(tmp_path / "dummy.pml")
        assert result.status is VerificationStatus.SKIPPED
        assert result.passed is False

    def test_verify_tla_skip_when_absent(self, tmp_path, monkeypatch):
        monkeypatch.setattr(shutil, "which", lambda name: None)
        result = verify_tla(tmp_path / "dummy.tla")
        assert result.status is VerificationStatus.SKIPPED
        assert result.passed is False

    def test_absent_tools_never_report_pass(self, tmp_path, monkeypatch):
        """Regression guard for audit INTEG-03.

        A machine with no model checkers must never yield a passing verdict
        from any verifier.
        """
        monkeypatch.setattr(shutil, "which", lambda name: None)
        for verify, suffix in (
            (verify_nusmv, ".smv"),
            (verify_spin, ".pml"),
            (verify_tla, ".tla"),
        ):
            result = verify(tmp_path / f"dummy{suffix}")
            assert result.status is not VerificationStatus.PASSED
            assert not str(result).startswith("PASS")


# ---------------------------------------------------------------------------
# VerificationResult rendering
# ---------------------------------------------------------------------------


class TestVerificationResultRendering:
    """The string form keeps the legacy 'STATUS: detail' shape."""

    def test_str_without_detail(self):
        assert str(VerificationResult("SPIN", VerificationStatus.PASSED)) == "PASS"

    def test_str_with_detail(self):
        result = VerificationResult("SPIN", VerificationStatus.SKIPPED, "no binary")
        assert str(result) == "SKIP: no binary"

    def test_passed_property_only_true_for_passed(self):
        for status in VerificationStatus:
            result = VerificationResult("t", status, "d")
            assert result.passed == (status is VerificationStatus.PASSED)


# ---------------------------------------------------------------------------
# generate_and_verify_all
# ---------------------------------------------------------------------------


class TestGenerateAndVerifyAll:
    """Tests for generate_and_verify_all()."""

    def test_returns_dict_with_three_keys(self, tmp_path):
        result = generate_and_verify_all(tmp_path)
        assert set(result.keys()) == {"NuSMV", "SPIN", "TLA+"}

    def test_values_are_verification_results(self, tmp_path):
        result = generate_and_verify_all(tmp_path)
        for key, val in result.items():
            assert isinstance(val, VerificationResult), f"{key}: {type(val)}"
            assert isinstance(str(val), str) and str(val)

    def test_creates_output_directory(self, tmp_path):
        out_dir = tmp_path / "specs_output"
        assert not out_dir.exists()
        generate_and_verify_all(out_dir)
        assert out_dir.exists()

    def test_writes_spec_files(self, tmp_path):
        generate_and_verify_all(tmp_path)
        assert (tmp_path / "cif_model.smv").exists()
        assert (tmp_path / "cif_model.pml").exists()
        assert (tmp_path / "CognitiveIntegrityFramework.tla").exists()

    def test_spec_files_non_empty(self, tmp_path):
        generate_and_verify_all(tmp_path)
        for fname in ("cif_model.smv", "cif_model.pml", "CognitiveIntegrityFramework.tla"):
            content = (tmp_path / fname).read_text()
            assert len(content) > 100, f"{fname} appears too short"

    def test_skip_status_when_tools_absent(self, tmp_path, monkeypatch):
        """Without external tools, all three results are SKIPPED — never PASSED."""
        monkeypatch.setattr(shutil, "which", lambda name: None)
        result = generate_and_verify_all(tmp_path)
        for key, val in result.items():
            assert val.status is VerificationStatus.SKIPPED, f"{key}: {val}"
            assert not val.passed

    def test_custom_n_agents(self, tmp_path):
        result = generate_and_verify_all(tmp_path, n_agents=7, max_byzantine=2)
        assert isinstance(result, dict)
        # Content of NuSMV spec should reference the agent count
        smv_content = (tmp_path / "cif_model.smv").read_text()
        assert "7" in smv_content

    def test_existing_dir_does_not_raise(self, tmp_path):
        """Calling twice with the same directory should not raise."""
        generate_and_verify_all(tmp_path)
        generate_and_verify_all(tmp_path)  # second call — dir already exists

    def test_nested_output_dir_created(self, tmp_path):
        nested = tmp_path / "deep" / "nested" / "specs"
        assert not nested.exists()
        generate_and_verify_all(nested)
        assert nested.exists()
