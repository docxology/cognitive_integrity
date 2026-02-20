#!/usr/bin/env python3
"""
Manuscript Verification Script
==============================

Thin orchestrator that verifies manuscript integrity using the
ManuscriptVerifier from src/manuscript/verifier.py.

Usage:
    python verify_manuscript.py [--root manuscript]
"""

import argparse
import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from manuscript.verifier import ManuscriptVerifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("manuscript_verification.log"),
    ],
)


def main():
    parser = argparse.ArgumentParser(description="Verify manuscript integrity.")
    # Default to project's own manuscript directory (not CWD-relative)
    project_dir = os.environ.get(
        "PROJECT_DIR",
        str(Path(__file__).resolve().parent.parent)
    )
    default_root = str(Path(project_dir) / "manuscript")
    parser.add_argument(
        "--root", default=default_root, help="Path to manuscript root directory."
    )
    args = parser.parse_args()

    verifier = ManuscriptVerifier(args.root)
    passed = verifier.run_all()
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
