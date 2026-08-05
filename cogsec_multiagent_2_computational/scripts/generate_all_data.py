#!/usr/bin/env python3
"""Generate all experimental datasets.

Every artifact written here carries a run-provenance block (git SHA + dirty
flag, interpreter, platform, numpy/scipy/matplotlib versions, UTC timestamp)
so a reader can tell which revision and environment produced it.  Pass
``--no-timestamp`` to drop the wall-clock field, which is the only
nondeterministic one: with it dropped, two runs from the same checkout and
environment at the same seed produce byte-identical files.

The datasets written here are schema-compliant PLACEHOLDERS.  See REPRODUCE.md,
"Synthetic vs. Real Data", for the scripts that produce measured results.

Usage:
    python scripts/generate_all_data.py [--seed 42] [--output output/data]
                                        [--no-timestamp]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from data.generate import DataGenerator
from utils.random_seed import set_global_seed
from utils.run_provenance import format_run_provenance


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate all experimental data")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=str, default="output/data")
    parser.add_argument(
        "--no-timestamp",
        action="store_true",
        help=(
            "Omit the wall-clock field from the recorded run provenance so "
            "output is byte-identical across runs (deterministic mode)."
        ),
    )
    args = parser.parse_args()

    set_global_seed(args.seed)
    output_dir = str(ROOT / args.output)

    generator = DataGenerator(
        seed=args.seed,
        output_dir=output_dir,
        include_timestamp=not args.no_timestamp,
    )

    print("=" * 70)
    print("Generating All Experimental Datasets")
    print("=" * 70)
    print(f"Run provenance: {format_run_provenance(generator.run_provenance())}")

    generator.generate_all()

    print("-" * 70)
    print(f"All data saved to {output_dir}/")


if __name__ == "__main__":
    sys.exit(main())
