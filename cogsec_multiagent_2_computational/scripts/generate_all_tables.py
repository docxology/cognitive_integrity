#!/usr/bin/env python3
"""Generate all LaTeX tables for the manuscript.

Usage:
    python scripts/generate_all_tables.py [--output output/tables]

Exit status:
    0  every table was generated
    1  at least one generator raised; the failures are listed at the end
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable, Optional, Sequence

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def default_tables() -> list[tuple[str, Callable[[], str]]]:
    """Return the ``(filename, generator)`` pairs for every manuscript table."""
    from visualization.tables.ablation_tables import generate_ablation_table, generate_synergy_table
    from visualization.tables.assumption_tables import generate_assumption_table
    from visualization.tables.corpus_tables import generate_corpus_table
    from visualization.tables.cross_validation_tables import generate_cross_validation_table
    from visualization.tables.detection_tables import generate_detection_table
    from visualization.tables.scalability_tables import generate_scalability_table
    from visualization.tables.stability_tables import generate_stability_table
    from visualization.tables.statistical_tables import (
        generate_effect_size_table,
        generate_hypothesis_table,
    )

    return [
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


def run_generators(
    tables: Sequence[tuple[str, Callable[[], str]]],
    output_dir: Path,
) -> list[tuple[str, str]]:
    """Write every table and return ``(name, error)`` for the ones that raised.

    Every generator is attempted even after one fails, so a single run reports
    all problems.  The caller must turn a non-empty result into a non-zero exit
    status -- see :func:`main`.
    """
    failures: list[tuple[str, str]] = []
    for name, gen_fn in tables:
        print(f"  {name}...", end=" ", flush=True)
        try:
            latex = gen_fn()
            out_path = output_dir / name
            out_path.write_text(latex, encoding="utf-8")
            print("OK")
        except Exception as e:  # noqa: BLE001 - report all, fail at the end
            failures.append((name, f"{type(e).__name__}: {e}"))
            print(f"FAILED: {e}")
    return failures


def main(
    argv: Optional[Sequence[str]] = None,
    tables: Optional[Sequence[tuple[str, Callable[[], str]]]] = None,
) -> int:
    """Generate every table; return 0 on full success, 1 if anything failed."""
    parser = argparse.ArgumentParser(description="Generate all LaTeX tables")
    parser.add_argument("--output", type=str, default="output/tables")
    args = parser.parse_args(argv)

    # An absolute --output wins; a relative one is resolved against the project.
    output_dir = ROOT / args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    items = list(tables) if tables is not None else default_tables()

    print("=" * 70)
    print(f"Generating {len(items)} LaTeX Tables")
    print("=" * 70)

    # Attempt every table, then report *all* failures -- but never exit 0 with
    # a missing table, which would make `make tables` a fail-open no-op.
    failures = run_generators(items, output_dir)

    print("-" * 70)
    print(f"Tables saved to {output_dir}/")

    if failures:
        print(f"\n{len(failures)} of {len(items)} table(s) FAILED:")
        for name, err in failures:
            print(f"  - {name}: {err}")
        return 1

    print(f"All {len(items)} tables generated successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
