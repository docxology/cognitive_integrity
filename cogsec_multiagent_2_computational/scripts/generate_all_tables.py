#!/usr/bin/env python3
"""Generate all LaTeX tables for the manuscript.

Usage:
    python scripts/generate_all_tables.py [--output output/tables]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate all LaTeX tables")
    parser.add_argument("--output", type=str, default="output/tables")
    args = parser.parse_args()

    output_dir = ROOT / args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    from visualization.tables.detection_tables import generate_detection_table
    from visualization.tables.statistical_tables import generate_hypothesis_table, generate_effect_size_table
    from visualization.tables.scalability_tables import generate_scalability_table
    from visualization.tables.ablation_tables import generate_ablation_table, generate_synergy_table
    from visualization.tables.corpus_tables import generate_corpus_table
    from visualization.tables.assumption_tables import generate_assumption_table
    from visualization.tables.cross_validation_tables import generate_cross_validation_table
    from visualization.tables.stability_tables import generate_stability_table

    tables = [
        ("detection_rates.tex", generate_detection_table),
        ("hypothesis_tests.tex", generate_hypothesis_table),
        ("effect_sizes.tex", generate_effect_size_table),
        ("scalability.tex", generate_scalability_table),
        ("ablation.tex", generate_ablation_table),
        ("synergy.tex", generate_synergy_table),
        ("corpus_composition.tex", generate_corpus_table),
        ("assumption_tests.tex", generate_assumption_table),
        ("cross_validation.tex", generate_cross_validation_table),
        ("stability.tex", generate_stability_table),
    ]

    print("=" * 70)
    print(f"Generating {len(tables)} LaTeX Tables")
    print("=" * 70)

    for name, gen_fn in tables:
        print(f"  {name}...", end=" ", flush=True)
        try:
            latex = gen_fn()
            out_path = output_dir / name
            out_path.write_text(latex, encoding="utf-8")
            print("OK")
        except Exception as e:
            print(f"FAILED: {e}")

    print("-" * 70)
    print(f"Tables saved to {output_dir}/")


if __name__ == "__main__":
    main()
