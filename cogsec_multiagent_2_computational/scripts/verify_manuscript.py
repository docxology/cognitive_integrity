#!/usr/bin/env python3
"""
Manuscript Verification Script
==============================

Thin orchestrator that verifies manuscript integrity using the
ManuscriptVerifier from src/manuscript/verifier.py.

Import is side-effect free
--------------------------
Logging is configured inside :func:`main`, never at import time, and writes
under ``output/logs/`` (generated and gitignored), overwriting rather than
appending.  Calling ``logging.basicConfig`` with a ``FileHandler`` at import
time against a CWD-relative path would make importing this module fail with
``PermissionError`` in a read-only checkout, before any code under test runs;
it would dirty the working tree on every ``make verify``; and it would grow a
tracked log without bound.

Usage:
    python scripts/verify_manuscript.py [--root manuscript] [--log PATH]
"""

import argparse
import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from manuscript.verifier import ManuscriptVerifier  # noqa: E402

DEFAULT_LOG_PATH = ROOT / "output" / "logs" / "manuscript_verification.log"


def configure_logging(log_path: Path | None) -> None:
    """Attach stdout and (optionally) file handlers to the root logger.

    Args:
        log_path: Destination log file, or ``None`` to log to stdout only.
            Parent directories are created.  The file is opened in ``"w"``
            mode so repeated runs do not accumulate.
    """
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_path, mode="w"))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=handlers,
        force=True,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify manuscript integrity.")
    # Default to project's own manuscript directory (not CWD-relative)
    project_dir = os.environ.get("PROJECT_DIR", str(ROOT))
    default_root = str(Path(project_dir) / "manuscript")
    parser.add_argument(
        "--root", default=default_root, help="Path to manuscript root directory."
    )
    parser.add_argument(
        "--log",
        default=str(DEFAULT_LOG_PATH),
        help=(
            "Log file path (created/overwritten). Pass an empty string to "
            "disable file logging entirely."
        ),
    )
    args = parser.parse_args(argv)

    configure_logging(Path(args.log) if args.log else None)

    verifier = ManuscriptVerifier(args.root)
    passed = verifier.run_all()
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
