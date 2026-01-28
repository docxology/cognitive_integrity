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
import sys
from pathlib import Path

# Add project root to path to allow importing src
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from src.verification import ManuscriptVerifier

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify manuscript integrity.")
    parser.add_argument(
        "--root", default="manuscript", help="Path to manuscript root directory."
    )
    args = parser.parse_args()

    verifier = ManuscriptVerifier(args.root)
    verifier.run_all()
