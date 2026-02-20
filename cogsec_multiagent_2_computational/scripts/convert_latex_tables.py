#!/usr/bin/env python3
"""
LaTeX Table Conversion Script
==============================

Thin orchestrator that converts LaTeX tables in manuscript markdown files
to markdown pipe-style tables using src/manuscript/latex_converter.py.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from manuscript.latex_converter import convert_file


def main():
    """Convert all LaTeX tables in manuscript files."""
    manuscript_dir = Path(__file__).parent.parent / "manuscript"

    if not manuscript_dir.exists():
        print(f"Manuscript directory not found: {manuscript_dir}")
        return

    md_files = sorted(manuscript_dir.glob("*.md"))
    print(f"Found {len(md_files)} markdown files")

    converted = 0
    for fpath in md_files:
        if convert_file(fpath):
            print(f"  ✓ {fpath.name}")
            converted += 1

    print(f"\nConverted {converted} files")


if __name__ == "__main__":
    main()
