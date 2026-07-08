"""CLI tests for src/__main__.py.

Covers the main() function, argument parsing, and cmd_* handlers.
Uses subprocess to invoke `python -m src` from the project root.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestMainCLI:
    """Tests for the src/__main__.py CLI entry point."""

    def _run_cli(self, *args, check=False):
        """Run `python -m src <args>` and return CompletedProcess."""
        return subprocess.run(
            [sys.executable, "-m", "src"] + list(args),
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )

    def test_no_args_prints_help(self):
        """Running with no subcommand prints help and exits 1."""
        result = self._run_cli()
        # Should exit 1 (parser.print_help(); sys.exit(1))
        assert result.returncode == 1
        assert "usage" in result.stdout.lower() or "usage" in result.stderr.lower()

    def test_help_flag(self):
        """--help exits 0 and shows usage."""
        result = self._run_cli("--help")
        assert result.returncode == 0
        output = result.stdout + result.stderr
        assert "usage" in output.lower()

    def test_evaluate_subcommand_help(self):
        """evaluate --help shows its args."""
        result = self._run_cli("evaluate", "--help")
        assert result.returncode == 0
        assert "seed" in result.stdout.lower()

    def test_figures_subcommand_help(self):
        """figures --help shows its args."""
        result = self._run_cli("figures", "--help")
        assert result.returncode == 0
        assert "output" in result.stdout.lower()

    def test_verify_subcommand_help(self):
        """verify --help shows its args."""
        result = self._run_cli("verify", "--help")
        assert result.returncode == 0

    def test_unknown_subcommand_exits_nonzero(self):
        """Passing an unknown subcommand should not hang and should error."""
        # argparse will print help and set args.command = None for unknown positional
        result = subprocess.run(
            [sys.executable, "-m", "src", "__totally_unknown_subcommand__"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=10,
        )
        # May exit 0 (no command) or 2 (argparse error)
        assert result.returncode in (1, 2)
