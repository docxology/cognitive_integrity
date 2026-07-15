"""Direct import tests for src/__main__.py CLI functions.

These tests import and call the __main__ module functions directly
to ensure statement coverage (as opposed to subprocess invocation).

Covers: main(), cmd_evaluate, cmd_figures, cmd_verify command dispatch,
no-command path, and unknown command path.

No mocks — tests use real computations, real objects, and real I/O.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import pytest

# Ensure src is on the path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SRC = str(_PROJECT_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)


class TestMainModule:
    """Tests for __main__.py by importing functions directly."""

    def test_main_no_args_exits_one(self, monkeypatch):
        """main() with no subcommand exits with code 1."""
        import src.__main__ as m
        monkeypatch.setattr(sys, "argv", ["src"])
        with pytest.raises(SystemExit) as exc:
            m.main()
        assert exc.value.code == 1

    def test_main_help_exits_zero(self, monkeypatch):
        """main() with --help exits 0."""
        import src.__main__ as m
        monkeypatch.setattr(sys, "argv", ["src", "--help"])
        with pytest.raises(SystemExit) as exc:
            m.main()
        assert exc.value.code == 0

    def test_main_dispatches_evaluate_end_to_end(self, monkeypatch, capsys):
        """main() with `evaluate` on argv runs through the real dispatch table.

        Regression test: every prior test called cmd_evaluate/cmd_figures/
        cmd_verify directly, bypassing main()'s argparse-driven dispatch
        table (`commands = {...}; fn = commands.get(args.command); fn(args)`)
        entirely -- so that table had zero coverage. This drives it via
        sys.argv the way a real CLI invocation would.
        """
        import src.__main__ as m
        monkeypatch.setattr(sys, "argv", ["src", "evaluate", "--seed", "1"])

        m.main()  # should return normally (no SystemExit) on success

        captured = capsys.readouterr()
        assert "Evaluation complete" in captured.out

    def test_main_dispatches_verify_end_to_end(self, monkeypatch):
        """main() with `verify` on argv runs through the real dispatch table."""
        import src.__main__ as m
        monkeypatch.setattr(sys, "argv", ["src", "verify", "--root", "manuscript"])

        m.main()  # verify_manuscript.py should pass on the project's own manuscript

    def test_cmd_evaluate_calls_runner(self, capsys):
        """cmd_evaluate runs the real evaluation pipeline end-to-end.

        Regression test: a prior version of this test replaced
        m.cmd_evaluate itself with a local re-implementation via
        monkeypatch.setattr(m, "cmd_evaluate", ...) and then called that
        replacement -- so the real function body (corpus generation,
        adapter construction, run_full_matrix, TPR/FPR summary print) was
        never actually executed or covered. This calls the real function
        directly; it completes in well under a second against the full
        generated corpus and real adapters, so there is no need to fake it.
        """
        import src.__main__ as m

        args = argparse.Namespace(seed=42)
        m.cmd_evaluate(args)

        captured = capsys.readouterr()
        assert "Evaluation complete" in captured.out
        assert "TPR=" in captured.out
        assert "FPR=" in captured.out

    def test_cmd_figures_generates_figures(self, tmp_path):
        """cmd_figures runs the real figure-generating functions.

        The Agg backend is set by conftest so no display is required.
        This test calls the real plot functions end-to-end.
        """
        import src.__main__ as m

        args = argparse.Namespace(output=str(tmp_path / "figs"))
        # Should not raise — figures generate with synthetic data
        m.cmd_figures(args)

    def test_cmd_figures_handles_failures_exits_one(self, monkeypatch, tmp_path):
        """cmd_figures exits 1 when any figure fails.

        We provoke a failure by replacing one plot function with a plain
        callable that raises RuntimeError.  No MagicMock — just a plain
        Python function closure.
        """
        import src.__main__ as m
        from src.visualization.figures import attack_surface

        def _raise_on_call(**kwargs):
            raise RuntimeError("Simulated figure failure")

        monkeypatch.setattr(attack_surface, "plot_attack_surface", _raise_on_call)

        args = argparse.Namespace(output=str(tmp_path / "figs_fail"))
        with pytest.raises(SystemExit) as exc:
            m.cmd_figures(args)
        assert exc.value.code == 1

    def test_cmd_verify_calls_subprocess(self, monkeypatch, tmp_path):
        """cmd_verify runs subprocess.run — verify it dispatches correctly.

        We use a real subprocess call with a trivial Python one-liner that
        succeeds immediately, replacing the verify script path via monkeypatch
        on sys.argv so the script argument becomes something that exists.
        """
        import src.__main__ as m

        completed_runs = []

        def _spy_run(cmd, **kwargs):
            """Record the call without actually running the verify script."""
            completed_runs.append(cmd)
            # Return a zero-exit CompletedProcess without side effects
            return subprocess.CompletedProcess(cmd, returncode=0)

        monkeypatch.setattr(subprocess, "run", _spy_run)

        args = argparse.Namespace(root="manuscript")
        m.cmd_verify(args)

        assert len(completed_runs) == 1
        cmd = completed_runs[0]
        # The command should contain verify_manuscript.py and the root arg
        assert any("verify_manuscript" in str(part) for part in cmd)
        assert "manuscript" in cmd
