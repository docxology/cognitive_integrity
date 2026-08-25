#!/usr/bin/env python3
"""Generate all 8 manuscript figures.

Usage:
    python scripts/generate_all_figures.py [--output output/figures]

Exit status:
    0  every figure was generated
    1  at least one figure generator raised; the failures are listed at the end

Reproducibility
---------------
matplotlib stamps ``/CreationDate`` into every PDF it writes, so two
byte-identical plots produced a minute apart hashed differently and the
publication PDFs were not bit-reproducible.  matplotlib honours the
``SOURCE_DATE_EPOCH`` convention, so this entry point pins it (respecting an
externally supplied value) before matplotlib is imported anywhere.  Verified
with::

    for d in a b; do python scripts/generate_all_figures.py --output "$TMP/$d"; done
    shasum -a 256 "$TMP"/a/*.pdf "$TMP"/b/*.pdf
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Callable, Optional, Sequence

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

# Force headless backend
os.environ.setdefault("MPLBACKEND", "Agg")

# Deterministic PDF /CreationDate (2024-01-01T00:00:00Z).  Overridable by the
# caller; must be set before matplotlib is imported.
DEFAULT_SOURCE_DATE_EPOCH = "1704067200"
os.environ.setdefault("SOURCE_DATE_EPOCH", DEFAULT_SOURCE_DATE_EPOCH)

#: Fixed salt so SVG element ids are stable too, should a figure ever be
#: written in that format.
SVG_HASHSALT = "cogsec-multiagent-figures"


def default_figures() -> list[tuple[str, Callable[..., object]]]:
    """Every manuscript-referenced figure generator.

    The five at the end read the measurements added with the control arm, the
    stratification, the threshold sweep, the load driver and the mitigation
    study. Each fails closed if its artifact is absent, so a figure here is
    either drawn from a measurement or not drawn at all.
    """
    from visualization.figures import (
        ablation_study,
        attack_surface,
        cif_comprehensive,
        comprehensive_taxonomy,
        defense_composition,
        detection_performance,
        load_saturation,
        mitigation_tradeoff,
        module_capability,
        operating_curve,
        roc_curves,
        stratified_detection,
        trust_decay,
    )

    return [
        ("attack_surface", attack_surface.plot_attack_surface),
        ("trust_decay", trust_decay.plot_trust_decay),
        ("roc_curves", roc_curves.plot_roc_curves),
        ("defense_composition", defense_composition.plot_defense_composition),
        ("ablation_study", ablation_study.plot_ablation_study),
        ("detection_performance", detection_performance.plot_detection_performance),
        ("comprehensive_taxonomy", comprehensive_taxonomy.plot_comprehensive_taxonomy),
        ("cif_comprehensive", cif_comprehensive.plot_cif_comprehensive),
        ("module_capability", module_capability.plot_module_capability),
        ("stratified_detection", stratified_detection.plot_stratified_detection),
        ("operating_curve", operating_curve.plot_operating_curve),
        ("load_saturation", load_saturation.plot_load_saturation),
        ("mitigation_tradeoff", mitigation_tradeoff.plot_mitigation_tradeoff),
    ]


def run_generators(
    figures: Sequence[tuple[str, Callable[..., object]]],
    output_dir: str,
) -> list[tuple[str, str]]:
    """Run every generator and return ``(name, error)`` for the ones that raised.

    Every generator is attempted even after one fails, so a single run reports
    all problems.  The caller is responsible for turning a non-empty result
    into a non-zero exit status -- see :func:`main`.
    """
    import matplotlib.pyplot as plt

    failures: list[tuple[str, str]] = []
    for i, (name, plot_fn) in enumerate(figures, 1):
        print(f"  [{i:d}/{len(figures)}] {name}...", end=" ", flush=True)
        try:
            fig = plot_fn(output_dir=output_dir)
            if fig is not None:
                plt.close(fig)
            print("OK")
        except Exception as e:  # noqa: BLE001 - report all, fail at the end
            failures.append((name, f"{type(e).__name__}: {e}"))
            print(f"FAILED: {e}")
    return failures


def main(
    argv: Optional[Sequence[str]] = None,
    figures: Optional[Sequence[tuple[str, Callable[..., object]]]] = None,
) -> int:
    """Generate every figure; return 0 on full success, 1 if anything failed."""
    parser = argparse.ArgumentParser(description="Generate all figures")
    parser.add_argument("--output", type=str, default="output/figures")
    args = parser.parse_args(argv)

    # An absolute --output wins; a relative one is resolved against the project.
    output_dir = str(ROOT / args.output)
    os.makedirs(output_dir, exist_ok=True)

    import matplotlib

    matplotlib.rcParams["svg.hashsalt"] = SVG_HASHSALT

    items = list(figures) if figures is not None else default_figures()

    print("=" * 70)
    print(f"Generating {len(items)} Manuscript Figures")
    print(f"SOURCE_DATE_EPOCH={os.environ['SOURCE_DATE_EPOCH']}")
    print("=" * 70)

    # Attempt every figure, then report *all* failures -- but never exit 0 with
    # a missing figure, which would make `make figures` a fail-open no-op.
    failures = run_generators(items, output_dir)

    print("-" * 70)
    print(f"Figures saved to {output_dir}/")

    if failures:
        print(f"\n{len(failures)} of {len(items)} figure(s) FAILED:")
        for name, err in failures:
            print(f"  - {name}: {err}")
        return 1

    print(f"All {len(items)} figures generated successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
