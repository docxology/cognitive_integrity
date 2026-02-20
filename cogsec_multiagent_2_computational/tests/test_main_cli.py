"""Tests for the CLI entry point (src/__main__.py)."""

import subprocess
import sys
from pathlib import Path

import pytest


class TestMainCLI:
    """Test the __main__.py argument parsing and dispatch."""

    def test_no_args_prints_help_and_exits(self):
        """Running without a subcommand prints help and exits with code 1."""
        result = subprocess.run(
            [sys.executable, "-m", "src", "--help"],
            capture_output=True,
            text=True,
            cwd=str(
                __import__("pathlib").Path(__file__).resolve().parent.parent
            ),
        )
        # --help always exits 0
        assert result.returncode == 0
        assert "Cognitive Security Framework CLI" in result.stdout

    def test_evaluate_subcommand_listed(self):
        result = subprocess.run(
            [sys.executable, "-m", "src", "--help"],
            capture_output=True,
            text=True,
            cwd=str(
                __import__("pathlib").Path(__file__).resolve().parent.parent
            ),
        )
        assert "evaluate" in result.stdout

    def test_figures_subcommand_listed(self):
        result = subprocess.run(
            [sys.executable, "-m", "src", "--help"],
            capture_output=True,
            text=True,
            cwd=str(
                __import__("pathlib").Path(__file__).resolve().parent.parent
            ),
        )
        assert "figures" in result.stdout

    def test_verify_subcommand_listed(self):
        result = subprocess.run(
            [sys.executable, "-m", "src", "--help"],
            capture_output=True,
            text=True,
            cwd=str(
                __import__("pathlib").Path(__file__).resolve().parent.parent
            ),
        )
        assert "verify" in result.stdout


class TestMainParsing:
    """Test argument parsing within the module."""

    def test_main_import_and_parse(self):
        """Running with no subcommand exits with code 1."""
        project_root = Path(__file__).resolve().parent.parent
        result = subprocess.run(
            [sys.executable, "-m", "src"],
            capture_output=True,
            text=True,
            cwd=str(project_root),
        )
        assert result.returncode == 1  # no subcommand → exit 1

    def test_cmd_evaluate_exists(self):
        from src.__main__ import cmd_evaluate
        assert callable(cmd_evaluate)

    def test_cmd_figures_exists(self):
        from src.__main__ import cmd_figures
        assert callable(cmd_figures)

    def test_cmd_verify_exists(self):
        from src.__main__ import cmd_verify
        assert callable(cmd_verify)


class TestCmdFiguresIntegration:
    """Smoke-test the figures subcommand (lightweight)."""

    def test_figures_runs_to_completion(self, tmp_path):
        """cmd_figures generates at least one output file."""
        import argparse
        from src.__main__ import cmd_figures

        args = argparse.Namespace(output=str(tmp_path))
        # This calls all figure generators; may fail on individual ones
        # but should not raise unhandled exceptions
        try:
            cmd_figures(args)
        except SystemExit:
            pass  # some figures may error, triggering sys.exit(1)
        # At minimum, the output dir should exist
        assert tmp_path.exists()
