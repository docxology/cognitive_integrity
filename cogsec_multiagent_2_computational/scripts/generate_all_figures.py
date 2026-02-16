#!/usr/bin/env python3
"""Generate all 8 manuscript figures.

Usage:
    python scripts/generate_all_figures.py [--output output/figures]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

# Force headless backend
os.environ.setdefault("MPLBACKEND", "Agg")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate all figures")
    parser.add_argument("--output", type=str, default="output/figures")
    args = parser.parse_args()

    output_dir = str(ROOT / args.output)
    os.makedirs(output_dir, exist_ok=True)

    from visualization.figures import attack_surface
    from visualization.figures import trust_decay
    from visualization.figures import roc_curves
    from visualization.figures import defense_composition
    from visualization.figures import ablation_study
    from visualization.figures import detection_performance
    from visualization.figures import comprehensive_taxonomy
    from visualization.figures import cif_comprehensive

    # 8 manuscript-referenced figures only
    figures = [
        ("attack_surface", attack_surface.plot_attack_surface),
        ("trust_decay", trust_decay.plot_trust_decay),
        ("roc_curves", roc_curves.plot_roc_curves),
        ("defense_composition", defense_composition.plot_defense_composition),
        ("ablation_study", ablation_study.plot_ablation_study),
        ("detection_performance", detection_performance.plot_detection_performance),
        ("comprehensive_taxonomy", comprehensive_taxonomy.plot_comprehensive_taxonomy),
        ("cif_comprehensive", cif_comprehensive.plot_cif_comprehensive),
    ]

    print("=" * 70)
    print(f"Generating {len(figures)} Manuscript Figures")
    print("=" * 70)

    for i, (name, plot_fn) in enumerate(figures, 1):
        print(f"  [{i:d}/{len(figures)}] {name}...", end=" ", flush=True)
        try:
            fig = plot_fn(output_dir=output_dir)
            if fig is not None:
                import matplotlib.pyplot as plt
                plt.close(fig)
            print("OK")
        except Exception as e:
            print(f"FAILED: {e}")

    print("-" * 70)
    print(f"Figures saved to {output_dir}/")


if __name__ == "__main__":
    main()
