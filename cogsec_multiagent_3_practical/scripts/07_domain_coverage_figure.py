#!/usr/bin/env python3
"""Thin orchestrator: CIF-AD-OODA domain coverage figures (Part 3+4 §10)."""

from __future__ import annotations

from pathlib import Path

from src.applications.domain_coverage import render_domain_coverage_figures

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output" / "figures"


def main() -> None:
    print("Generating CIF-AD-OODA domain coverage figures...")
    for path in render_domain_coverage_figures(OUTPUT_DIR):
        print(f"Saved: {path}")
    print("Done.")


if __name__ == "__main__":
    main()
