#!/usr/bin/env python3
"""Inject validated data values into manuscript files.

Thin orchestrator — all logic lives in src/manuscript/injector.py.

Usage:
    python scripts/z_inject_manuscript_values.py [--dry-run] [--verbose]
"""

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from manuscript.injector import inject_all

logger = logging.getLogger("inject_manuscript")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inject validated data into manuscript")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(name)s: %(message)s",
    )

    data_dir = ROOT / "output" / "data"
    manuscript_dir = ROOT / "manuscript"

    logger.info("Loading ground truth from %s...", data_dir)
    inject_all(data_dir, manuscript_dir, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
