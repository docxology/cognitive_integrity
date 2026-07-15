#!/usr/bin/env python3
"""
Manuscript Verification Script
==============================

Performs automated checks on manuscript files to ensure
consistency, correctness, and adherence to style guidelines.

Usage:
    python verify_manuscript.py [--root manuscript]
"""

import argparse
import os
import sys
from pathlib import Path

# Add project root to path to allow importing src
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from src.verification import ManuscriptVerifier

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify manuscript integrity.")
    # Default to project's own manuscript directory (not CWD-relative)
    project_dir = os.environ.get("PROJECT_DIR", str(Path(__file__).resolve().parent.parent))
    default_root = str(Path(project_dir) / "manuscript")
    parser.add_argument("--root", default=default_root, help="Path to manuscript root directory.")
    args = parser.parse_args()

    verifier = ManuscriptVerifier(args.root)
    passed = verifier.run_all()
    sys.exit(0 if passed else 1)
