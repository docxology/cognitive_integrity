"""Extended tests for src/formal/spec_verifier.py — tool-found code paths.

These tests install *real* executable shims on PATH (small `/bin/sh` scripts
written into ``tmp_path``) and run the verifiers against them.  Only the PATH
environment variable is overridden, which AGENTS.md permits; no library call is
replaced, so the subprocess plumbing, exit codes, and launch-failure handling
are all genuinely exercised.

Audit INTEG-03 regression coverage
----------------------------------
``verify_spin`` used to return ``"PASS"`` whenever the tool output did not
contain the substring ``"error"``.  That negative-form test made three
distinct broken states indistinguishable from success:

* the binary on PATH could not actually be executed (``OSError`` message
  "[Errno 2] No such file or directory" contains no "error"),
* a silent stub that is not SPIN at all printed nothing, and
* ``spin -a`` only *translates* the model — it never model-checks it.

``verify_nusmv`` had the mirror-image defect: it looked for the substring
``"is true"`` anywhere in the output, so a run that reported one property true
and another false was scored as a pass.  Each of those is pinned below.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from formal.spec_verifier import (
    VerificationStatus,
    generate_and_verify_all,
    verify_nusmv,
    verify_spin,
    verify_tla,
)


def install_shim(bin_dir: Path, name: str, body: str, monkeypatch) -> Path:
    """Write an executable ``/bin/sh`` shim and put it first on PATH."""
    bin_dir.mkdir(parents=True, exist_ok=True)
    shim = bin_dir / name
    shim.write_text(f"#!/bin/sh\n{body}\n")
    shim.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    return shim


def make_spec(tmp_path: Path, name: str, content: str = "spec\n") -> Path:
    spec_dir = tmp_path / "specs"
    spec_dir.mkdir(parents=True, exist_ok=True)
    spec = spec_dir / name
    spec.write_text(content)
    return spec


# ---------------------------------------------------------------------------
# verify_nusmv — tool found paths
# ---------------------------------------------------------------------------


class TestVerifyNuSMVToolFound:
    """Tests for the code paths where NuSMV is present."""

    def test_all_specifications_true_is_pass(self, tmp_path, monkeypatch):
        install_shim(
            tmp_path / "bin",
            "NuSMV",
            "echo '-- specification AG safe  is true'\n"
            "echo '-- specification AG live  is true'",
            monkeypatch,
        )
        result = verify_nusmv(make_spec(tmp_path, "test.smv", "MODULE main\n"))
        assert result.status is VerificationStatus.PASSED
        assert "2 specifications" in result.detail

    def test_single_false_specification_is_fail(self, tmp_path, monkeypatch):
        install_shim(
            tmp_path / "bin",
            "NuSMV",
            "echo '-- specification AG safe  is false'",
            monkeypatch,
        )
        result = verify_nusmv(make_spec(tmp_path, "test.smv", "MODULE main\n"))
        assert result.status is VerificationStatus.FAILED

    def test_mixed_true_and_false_is_fail_not_pass(self, tmp_path, monkeypatch):
        """Positive control for the substring bug.

        The old check (``"is true" in output``) returned PASS here because one
        specification held.  A single falsified property must sink the verdict.
        """
        install_shim(
            tmp_path / "bin",
            "NuSMV",
            "echo '-- specification AG safe  is true'\n"
            "echo '-- specification AG live  is false'",
            monkeypatch,
        )
        result = verify_nusmv(make_spec(tmp_path, "test.smv", "MODULE main\n"))
        assert result.status is VerificationStatus.FAILED
        assert "AG live" in result.detail

    def test_unrecognised_output_is_inconclusive(self, tmp_path, monkeypatch):
        install_shim(tmp_path / "bin", "NuSMV", "echo 'banner only'", monkeypatch)
        result = verify_nusmv(make_spec(tmp_path, "test.smv", "MODULE main\n"))
        assert result.status is VerificationStatus.INCONCLUSIVE
        assert not result.passed

    def test_nonzero_exit_with_verdicts_is_error(self, tmp_path, monkeypatch):
        install_shim(
            tmp_path / "bin",
            "NuSMV",
            "echo '-- specification AG safe  is true'\nexit 3",
            monkeypatch,
        )
        result = verify_nusmv(make_spec(tmp_path, "test.smv", "MODULE main\n"))
        assert result.status is VerificationStatus.ERROR

    def test_launch_failure_is_error_not_pass(self, tmp_path, monkeypatch):
        """A tool that resolves on PATH but cannot be run must not PASS."""
        install_shim(tmp_path / "bin", "NuSMV", "exit 0", monkeypatch)
        vanished = tmp_path / "gone" / "test.smv"
        result = verify_nusmv(vanished)
        assert result.status is VerificationStatus.ERROR
        assert not result.passed


# ---------------------------------------------------------------------------
# verify_spin — tool found paths
# ---------------------------------------------------------------------------


class TestVerifySpinToolFound:
    """Tests for the code paths where SPIN is present."""

    def test_clean_translation_is_inconclusive_not_pass(self, tmp_path, monkeypatch):
        """`spin -a` generates pan.c; it does not verify anything.

        Reporting PASS here credits the model with a model check that never
        ran, which is exactly what the old negative-form test did.
        """
        install_shim(tmp_path / "bin", "spin", "echo 'ok'\ntouch pan.c", monkeypatch)
        result = verify_spin(make_spec(tmp_path, "test.pml", "proctype P(){skip}\n"))
        assert result.status is VerificationStatus.INCONCLUSIVE
        assert not result.passed
        assert "does not model-check" in result.detail

    def test_syntax_error_is_fail(self, tmp_path, monkeypatch):
        install_shim(
            tmp_path / "bin",
            "spin",
            "echo 'spin: test.pml:3, Error: syntax error' 1>&2\nexit 1",
            monkeypatch,
        )
        result = verify_spin(make_spec(tmp_path, "test.pml", "garbage\n"))
        assert result.status is VerificationStatus.FAILED

    def test_silent_stub_producing_no_pan_c_is_error(self, tmp_path, monkeypatch):
        """Positive control: a stub that prints nothing must not PASS.

        Under the old rule ("no 'error' in output" ⇒ PASS) an unrelated binary
        named ``spin`` that exits 0 silently produced a passing verdict.
        """
        install_shim(tmp_path / "bin", "spin", "exit 0", monkeypatch)
        result = verify_spin(make_spec(tmp_path, "test.pml", "proctype P(){skip}\n"))
        assert result.status is VerificationStatus.ERROR
        assert not result.passed
        assert "pan.c" in result.detail

    def test_unrunnable_tool_is_error_not_pass(self, tmp_path, monkeypatch):
        """Positive control: the historical fail-open.

        The tool resolves on PATH but the invocation cannot be launched (the
        spec's parent directory does not exist).  The old code turned the
        resulting "[Errno 2] No such file or directory" message — which does
        not contain the substring "error" — into ``PASS``.
        """
        install_shim(tmp_path / "bin", "spin", "exit 0", monkeypatch)
        result = verify_spin(tmp_path / "vanished_dir" / "test.pml")
        assert result.status is VerificationStatus.ERROR
        assert not result.passed
        assert "not runnable" in result.detail


# ---------------------------------------------------------------------------
# verify_tla — tool found paths
# ---------------------------------------------------------------------------


class TestVerifyTlaToolFound:
    """Tests for the code paths where TLC (TLA+) is present."""

    def test_success_banner_is_pass(self, tmp_path, monkeypatch):
        install_shim(
            tmp_path / "bin",
            "tlc",
            "echo 'Model checking completed. No error has been found.'",
            monkeypatch,
        )
        result = verify_tla(make_spec(tmp_path, "CIF.tla", "---- MODULE CIF ----\n"))
        assert result.status is VerificationStatus.PASSED

    def test_invariant_violation_is_fail(self, tmp_path, monkeypatch):
        install_shim(
            tmp_path / "bin",
            "tlc",
            "echo 'Error: Invariant Safety is violated.'\nexit 1",
            monkeypatch,
        )
        result = verify_tla(make_spec(tmp_path, "CIF.tla", "---- MODULE CIF ----\n"))
        assert result.status is VerificationStatus.FAILED

    def test_unrecognised_clean_output_is_inconclusive(self, tmp_path, monkeypatch):
        install_shim(tmp_path / "bin", "tlc", "echo 'TLC2 Version 2.18'", monkeypatch)
        result = verify_tla(make_spec(tmp_path, "CIF.tla", "---- MODULE CIF ----\n"))
        assert result.status is VerificationStatus.INCONCLUSIVE
        assert not result.passed

    def test_nonzero_exit_without_verdict_is_error(self, tmp_path, monkeypatch):
        install_shim(tmp_path / "bin", "tlc", "echo 'usage: tlc'\nexit 2", monkeypatch)
        result = verify_tla(make_spec(tmp_path, "CIF.tla", "---- MODULE CIF ----\n"))
        assert result.status is VerificationStatus.ERROR

    def test_launch_failure_is_error_not_pass(self, tmp_path, monkeypatch):
        install_shim(tmp_path / "bin", "tlc", "exit 0", monkeypatch)
        result = verify_tla(tmp_path / "vanished_dir" / "CIF.tla")
        assert result.status is VerificationStatus.ERROR
        assert not result.passed


# ---------------------------------------------------------------------------
# Cross-cutting fail-closed guarantee
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "verify,tool,suffix",
    [
        (verify_nusmv, "NuSMV", ".smv"),
        (verify_spin, "spin", ".pml"),
        (verify_tla, "tlc", ".tla"),
    ],
)
class TestNoPassWithoutEvidence:
    """No verifier may PASS on a broken or uninformative checker."""

    def test_silent_stub_never_passes(self, tmp_path, monkeypatch, verify, tool, suffix):
        install_shim(tmp_path / "bin", tool, "exit 0", monkeypatch)
        result = verify(make_spec(tmp_path, f"m{suffix}"))
        assert result.status is not VerificationStatus.PASSED

    def test_crashing_tool_never_passes(self, tmp_path, monkeypatch, verify, tool, suffix):
        install_shim(tmp_path / "bin", tool, "echo boom 1>&2\nexit 42", monkeypatch)
        result = verify(make_spec(tmp_path, f"m{suffix}"))
        assert result.status is not VerificationStatus.PASSED

    def test_unlaunchable_tool_never_passes(
        self, tmp_path, monkeypatch, verify, tool, suffix
    ):
        install_shim(tmp_path / "bin", tool, "exit 0", monkeypatch)
        result = verify(tmp_path / "no_such_dir" / f"m{suffix}")
        assert result.status is VerificationStatus.ERROR


# ---------------------------------------------------------------------------
# generate_and_verify_all — tool found paths
# ---------------------------------------------------------------------------


class TestGenerateAndVerifyAllToolFound:
    """Tests for generate_and_verify_all when all tools are found."""

    def test_all_tools_found_produce_structured_results(self, tmp_path, monkeypatch):
        bin_dir = tmp_path / "bin"
        install_shim(
            bin_dir,
            "NuSMV",
            "echo '-- specification AG safe  is true'",
            monkeypatch,
        )
        install_shim(bin_dir, "spin", "touch pan.c", monkeypatch)
        install_shim(
            bin_dir,
            "tlc",
            "echo 'Model checking completed. No error has been found.'",
            monkeypatch,
        )

        out = tmp_path / "specs_out"
        result = generate_and_verify_all(out)
        assert set(result.keys()) == {"NuSMV", "SPIN", "TLA+"}
        assert result["NuSMV"].status is VerificationStatus.PASSED
        assert result["TLA+"].status is VerificationStatus.PASSED
        # spin -a translated the model but did not model-check it.
        assert result["SPIN"].status is VerificationStatus.INCONCLUSIVE

    def test_broken_tools_do_not_report_pass(self, tmp_path, monkeypatch):
        """A machine where every checker is a broken stub yields zero passes."""
        bin_dir = tmp_path / "bin"
        for tool in ("NuSMV", "spin", "tlc"):
            install_shim(bin_dir, tool, "exit 0", monkeypatch)

        result = generate_and_verify_all(tmp_path / "specs_out")
        assert not any(res.passed for res in result.values())
