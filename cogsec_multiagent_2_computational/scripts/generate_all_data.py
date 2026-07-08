#!/usr/bin/env python3
"""Generate all experimental datasets.

Usage:
    python scripts/generate_all_data.py [--seed 42] [--output output/data]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from data.generate import DataGenerator
from utils.random_seed import set_global_seed


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate all experimental data")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=str, default="output/data")
    args = parser.parse_args()

    set_global_seed(args.seed)
    output_dir = str(ROOT / args.output)

    print("=" * 70)
    print("Generating All Experimental Datasets")
    print("=" * 70)

    generator = DataGenerator(seed=args.seed, output_dir=output_dir)
    generator.generate_all()

    print("-" * 70)
    print(f"All data saved to {output_dir}/")


if __name__ == "__main__":
    main()
