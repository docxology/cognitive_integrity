#!/usr/bin/env python3
"""Thin orchestrator: CIF-AD-OODA domain coverage figures (Part 3+4 §10)."""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path for imports (mirrors scripts 01-06).
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.applications.domain_coverage import render_domain_coverage_figures

OUTPUT_DIR = project_root / "output" / "figures"


def main() -> None:
    print("Generating CIF-AD-OODA domain coverage figures...")
    for path in render_domain_coverage_figures(OUTPUT_DIR):
        print(f"Saved: {path}")
    print("Done.")


if __name__ == "__main__":
    main()
