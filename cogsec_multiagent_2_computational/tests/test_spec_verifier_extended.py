"""Extended tests for src/formal/spec_verifier.py — tool-found code paths.

Covers the branches where the verification tools ARE found in PATH,
exercising lines 47-50, 58-61, 69-72 (the run_command + status-string paths).

Uses monkeypatch (acceptable per AGENTS.md for env/path overrides) to
simulate a tool being present and returning specific output strings.
"""

from __future__ import annotations

import shutil
import subprocess

from formal.spec_verifier import (
    generate_and_verify_all,
    verify_nusmv,
    verify_spin,
    verify_tla,
)

# ---------------------------------------------------------------------------
# verify_nusmv — tool found paths
# ---------------------------------------------------------------------------


class TestVerifyNuSMVToolFound:
    """Tests for the code paths where NuSMV is present."""

    def test_returns_pass_when_is_true_in_output(self, tmp_path, monkeypatch):
        """Simulate NuSMV returning 'is true' in output → PASS."""
        spec = tmp_path / "test.smv"
        spec.write_text("MODULE main\n")
        monkeypatch.setattr(shutil, "which", lambda name: "/fake/NuSMV" if name == "NuSMV" else None)  # noqa: E501

        # Patch subprocess.run to return a successful output
        fake_cp = subprocess.CompletedProcess(
            args=["/fake/NuSMV", "test.smv"],
            returncode=0,
            stdout="-- specification is true\n",
            stderr="",
        )
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake_cp)

        result = verify_nusmv(spec)
        assert result == "PASS"

    def test_returns_fail_when_not_is_true(self, tmp_path, monkeypatch):
        """Simulate NuSMV returning output without 'is true' → FAIL."""
        spec = tmp_path / "test.smv"
        spec.write_text("MODULE main\n")
        monkeypatch.setattr(shutil, "which", lambda name: "/fake/NuSMV" if name == "NuSMV" else None)  # noqa: E501

        fake_cp = subprocess.CompletedProcess(
            args=["/fake/NuSMV", "test.smv"],
            returncode=0,
            stdout="-- specification is false\n",
            stderr="",
        )
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake_cp)

        result = verify_nusmv(spec)
        assert result.startswith("FAIL")


# ---------------------------------------------------------------------------
# verify_spin — tool found paths
# ---------------------------------------------------------------------------


class TestVerifySpinToolFound:
    """Tests for the code paths where SPIN is present."""

    def test_returns_pass_when_no_error_in_output(self, tmp_path, monkeypatch):
        """Simulate SPIN returning output with no 'error' → PASS."""
        spec = tmp_path / "test.pml"
        spec.write_text("proctype P() { skip }\n")
        monkeypatch.setattr(shutil, "which", lambda name: "/fake/spin" if name == "spin" else None)

        fake_cp = subprocess.CompletedProcess(
            args=["/fake/spin", "-a", "test.pml"],
            returncode=0,
            stdout="Spin Version 6.0 output\nAll good.\n",
            stderr="",
        )
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake_cp)

        result = verify_spin(spec)
        assert result == "PASS"

    def test_returns_fail_when_error_in_output(self, tmp_path, monkeypatch):
        """Simulate SPIN returning output with 'error' → FAIL."""
        spec = tmp_path / "test.pml"
        spec.write_text("proctype P() { skip }\n")
        monkeypatch.setattr(shutil, "which", lambda name: "/fake/spin" if name == "spin" else None)

        fake_cp = subprocess.CompletedProcess(
            args=["/fake/spin", "-a", "test.pml"],
            returncode=0,
            stdout="error: assertion violated\n",
            stderr="",
        )
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake_cp)

        result = verify_spin(spec)
        assert result.startswith("FAIL")


# ---------------------------------------------------------------------------
# verify_tla — tool found paths
# ---------------------------------------------------------------------------


class TestVerifyTlaToolFound:
    """Tests for the code paths where TLC (TLA+) is present."""

    def test_returns_pass_when_model_checking_completed(self, tmp_path, monkeypatch):
        """Simulate TLC returning successful output → PASS."""
        spec = tmp_path / "CIF.tla"
        spec.write_text("---- MODULE CIF ----\nEXTENDS Naturals\n====\n")
        monkeypatch.setattr(shutil, "which", lambda name: "/fake/tlc" if name == "tlc" else None)

        fake_cp = subprocess.CompletedProcess(
            args=["/fake/tlc", "CIF.tla"],
            returncode=0,
            stdout="Model checking completed. No error has been found.\n",
            stderr="",
        )
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake_cp)

        result = verify_tla(spec)
        assert result == "PASS"

    def test_returns_fail_when_errors_found(self, tmp_path, monkeypatch):
        """Simulate TLC returning error output → FAIL."""
        spec = tmp_path / "CIF.tla"
        spec.write_text("---- MODULE CIF ----\nEXTENDS Naturals\n====\n")
        monkeypatch.setattr(shutil, "which", lambda name: "/fake/tlc" if name == "tlc" else None)

        fake_cp = subprocess.CompletedProcess(
            args=["/fake/tlc", "CIF.tla"],
            returncode=1,
            stdout="Error: Invariant violated\n",
            stderr="",
        )
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake_cp)

        result = verify_tla(spec)
        assert result.startswith("FAIL")


# ---------------------------------------------------------------------------
# generate_and_verify_all — tool found paths
# ---------------------------------------------------------------------------


class TestGenerateAndVerifyAllToolFound:
    """Tests for generate_and_verify_all when all tools are found."""

    def test_all_tools_found_produce_results(self, tmp_path, monkeypatch):
        """When all tools are present, generate_and_verify_all returns string results."""
        monkeypatch.setattr(shutil, "which", lambda name: f"/fake/{name}")

        # Return tool-specific outputs for each call.
        # NuSMV: "is true" → PASS
        # SPIN: no "error" (case-insensitive) → PASS
        # TLA+: "Model checking completed. No error" → PASS
        call_count = [0]
        outputs = [
            "-- specification is true\n",           # NuSMV
            "Spin: all fine, nothing wrong here\n", # SPIN (no "error" substring)
            "Model checking completed. No error has been found.\n",  # TLA+
        ]

        def fake_run(*args, **kwargs):
            idx = call_count[0] % len(outputs)
            call_count[0] += 1
            return subprocess.CompletedProcess(
                args=[], returncode=0, stdout=outputs[idx], stderr=""
            )

        monkeypatch.setattr(subprocess, "run", fake_run)

        result = generate_and_verify_all(tmp_path)
        assert set(result.keys()) == {"NuSMV", "SPIN", "TLA+"}
        # All results should be non-empty strings
        for val in result.values():
            assert isinstance(val, str) and len(val) > 0
