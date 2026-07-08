"""Tests for src/formal/spec_verifier.py.

Covers:
- check_tool: returns path string or None.
- run_command: returns stdout or error string.
- generate_and_verify_all: writes spec files and returns result dict.

No external tools (NuSMV, SPIN, TLA+) are required; all three should return
SKIP status on a machine without those tools installed.
"""

from __future__ import annotations

import shutil

from formal.spec_verifier import (
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
        result = run_command(["echo", "hello_spec_verifier"], cwd=tmp_path)
        assert "hello_spec_verifier" in result

    def test_nonexistent_command_returns_error_string(self, tmp_path):
        result = run_command(
            ["__totally_nonexistent_binary_xyz__", "--flag"], cwd=tmp_path
        )
        assert isinstance(result, str)
        # Should not raise — returns error message
        assert len(result) > 0

    def test_failing_command_returns_error_string(self, tmp_path):
        # 'ls /nonexistent_path_xyz' fails with non-zero exit
        result = run_command(["ls", "/nonexistent_path_xyz_that_does_not_exist"], cwd=tmp_path)
        # CalledProcessError path — returns error string
        assert isinstance(result, str)

    def test_returns_string(self, tmp_path):
        result = run_command(["echo", "test"], cwd=tmp_path)
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# verify_nusmv / verify_spin / verify_tla — tool-absent path
# ---------------------------------------------------------------------------


class TestVerifyToolsAbsent:
    """When the external verification tools are absent, functions return SKIP."""

    def test_verify_nusmv_skip_when_absent(self, tmp_path, monkeypatch):
        monkeypatch.setattr(shutil, "which", lambda name: None)
        result = verify_nusmv(tmp_path / "dummy.smv")
        assert result.startswith("SKIP")

    def test_verify_spin_skip_when_absent(self, tmp_path, monkeypatch):
        monkeypatch.setattr(shutil, "which", lambda name: None)
        result = verify_spin(tmp_path / "dummy.pml")
        assert result.startswith("SKIP")

    def test_verify_tla_skip_when_absent(self, tmp_path, monkeypatch):
        monkeypatch.setattr(shutil, "which", lambda name: None)
        result = verify_tla(tmp_path / "dummy.tla")
        assert result.startswith("SKIP")


# ---------------------------------------------------------------------------
# generate_and_verify_all
# ---------------------------------------------------------------------------


class TestGenerateAndVerifyAll:
    """Tests for generate_and_verify_all()."""

    def test_returns_dict_with_three_keys(self, tmp_path):
        result = generate_and_verify_all(tmp_path)
        assert set(result.keys()) == {"NuSMV", "SPIN", "TLA+"}

    def test_values_are_strings(self, tmp_path):
        result = generate_and_verify_all(tmp_path)
        for key, val in result.items():
            assert isinstance(val, str), f"{key} result should be str, got {type(val)}"

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
        """Without external tools, all three results should start with SKIP."""
        monkeypatch.setattr(shutil, "which", lambda name: None)
        result = generate_and_verify_all(tmp_path)
        for key, val in result.items():
            assert val.startswith("SKIP"), f"{key}: expected SKIP, got {val!r}"

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
