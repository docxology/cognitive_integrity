#!/usr/bin/env python3
"""Generate the CIF Composer backend data file for the web UI.

Runs all category-theory verifications, aggregates module registry, algebra
formulas, and preset pipeline configurations, then writes the result to
``output/data/composer_data.json``.

Usage::

    # From the project root (cogsec_multiagent_2_computational/)
    python scripts/generate_composer_data.py

    # With a custom output path
    python scripts/generate_composer_data.py --output path/to/out.json

    # Skip slow category-theory verifications
    python scripts/generate_composer_data.py --no-category-theory

    # Verbose mode (print a summary to stdout)
    python scripts/generate_composer_data.py --verbose
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure src/ is on the Python path when running as a script
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent
_SRC = _PROJECT_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate composer_data.json for the CIF Composer web UI."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_PROJECT_ROOT / "output" / "data" / "composer_data.json",
        help="Output file path (default: output/data/composer_data.json)",
    )
    parser.add_argument(
        "--no-category-theory",
        action="store_true",
        default=False,
        help="Skip category-theory verification suite (faster startup).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Print a human-readable summary after generating.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation level (default: 2; use 0 for compact).",
    )
    return parser.parse_args()


def print_summary(data: dict, elapsed: float) -> None:  # type: ignore[type-arg]
    """Print a human-readable summary of the generated data."""
    modules = data.get("modules", {})
    presets = data.get("presets", {})
    algebra = data.get("algebra", {})
    ct = data.get("category_theory", {})

    print("\n=== CIF Composer Data Summary ===")
    print(f"  Schema version : {data.get('schema_version', 'n/a')}")
    print(f"  Generated in   : {elapsed:.2f}s")
    print()

    print(f"  Modules ({len(modules)}):")
    for name, meta in modules.items():
        print(
            f"    {name:12s}  rate={meta['detection_rate']:.2f}  "
            f"lat={meta['latency_ms']:.0f}ms  Ω={meta['omega_class']}"
        )

    print(f"\n  Preset Pipelines ({len(presets)}):")
    for key, preset in presets.items():
        print(
            f"    {preset['label']:30s}  "
            f"rate={preset['detection_rate']:.4f}  "
            f"lat={preset['latency_ms']:.0f}ms"
        )

    print(f"\n  Algebra Formulas ({len(algebra)}): {', '.join(algebra.keys())}")

    if "error" in ct:
        print(f"\n  Category Theory : ERROR — {ct['error']}")
    elif "verification_results" in ct:
        vr = ct["verification_results"]
        s = vr.get("summary", {})
        print(
            f"\n  Category Theory : {s.get('passed', '?')}/{s.get('total', '?')} "
            f"checks passed"
        )
        lattice = ct.get("lattice", {})
        print(f"    Lattice elements : {len(lattice.get('elements', []))}")
        print(f"    Hasse edges      : {len(lattice.get('hasse_edges', []))}")
        monoidal = ct.get("monoidal", {})
        coherence = monoidal.get("coherence", {})
        all_coherent = all(coherence.values()) if coherence else False
        print(f"    Monoidal coherence : {'✓ all passed' if all_coherent else '✗ some failed'}")
        operad = ct.get("operad", {})
        axioms_ok = all(a.get("passed", False) for a in operad.get("axioms", []))
        print(f"    Operad axioms    : {'✓ all passed' if axioms_ok else '✗ some failed'}")
    else:
        print("\n  Category Theory : not computed")

    print()


def main() -> int:
    args = parse_args()

    # Ensure the output directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # Import composer_data lazily (requires src/ on path)
    try:
        from visualization.composer_data import get_composer_data  # type: ignore[import]
    except ImportError as exc:
        print(f"ERROR: Cannot import composer_data: {exc}", file=sys.stderr)
        print(
            "Make sure you run this script from the project root or that "
            "src/ is on PYTHONPATH.",
            file=sys.stderr,
        )
        return 1

    if args.verbose:
        print(f"Generating composer data (category_theory={'enabled' if not args.no_category_theory else 'disabled'})...")  # noqa: E501

    t0 = time.perf_counter()
    try:
        data = get_composer_data(include_category_theory=not args.no_category_theory)
    except Exception as exc:
        print(f"ERROR: Data generation failed: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 2

    elapsed = time.perf_counter() - t0

    # Write JSON
    indent = args.indent if args.indent > 0 else None
    json_text = json.dumps(data, indent=indent, ensure_ascii=False)
    args.output.write_text(json_text, encoding="utf-8")

    if args.verbose:
        print_summary(data, elapsed)
        print(f"  Output written to: {args.output}")
    else:
        print(f"composer_data.json written to {args.output} ({elapsed:.2f}s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
