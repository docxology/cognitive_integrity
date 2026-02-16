#!/usr/bin/env python3
"""CLI entry point for the Cognitive Security Framework.

Usage:
    python -m src evaluate [--seed SEED]
    python -m src figures [--output DIR]
    python -m src verify [--root DIR]
"""

from __future__ import annotations

import argparse
import sys


def cmd_evaluate(args: argparse.Namespace) -> None:
    """Run evaluation experiments."""
    from .evaluation.runner import ExperimentRunner

    runner = ExperimentRunner(seed=args.seed)
    result = runner.run()
    print(f"Evaluation complete: TPR={result.tpr:.3f}, FPR={result.fpr:.3f}")


def cmd_figures(args: argparse.Namespace) -> None:
    """Generate all manuscript figures."""
    import os

    os.environ.setdefault("MPLBACKEND", "Agg")

    from .visualization.figures import (
        ablation_study,
        attack_surface,
        cif_comprehensive,
        comprehensive_taxonomy,
        defense_composition,
        detection_performance,
        roc_curves,
        trust_decay,
    )

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

    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)

    failures = 0
    for name, plot_fn in figures:
        print(f"  Generating {name}...", end=" ", flush=True)
        try:
            fig = plot_fn(output_dir=output_dir)
            if fig is not None:
                import matplotlib.pyplot as plt
                plt.close(fig)
            print("OK")
        except Exception as e:
            print(f"FAILED: {e}", file=sys.stderr)
            failures += 1

    if failures:
        sys.exit(1)


def cmd_verify(args: argparse.Namespace) -> None:
    """Run manuscript verification."""
    import subprocess

    subprocess.run(
        [sys.executable, "scripts/verify_manuscript.py", "--root", args.root],
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m src",
        description="Cognitive Security Framework CLI",
    )
    sub = parser.add_subparsers(dest="command")

    # evaluate
    p_eval = sub.add_parser("evaluate", help="Run evaluation experiments")
    p_eval.add_argument("--seed", type=int, default=42, help="Random seed")

    # figures
    p_fig = sub.add_parser("figures", help="Generate manuscript figures")
    p_fig.add_argument("--output", default="output/figures", help="Output directory")

    # verify
    p_ver = sub.add_parser("verify", help="Verify manuscript integrity")
    p_ver.add_argument("--root", default="manuscript", help="Manuscript root")

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        sys.exit(1)

    commands = {
        "evaluate": cmd_evaluate,
        "figures": cmd_figures,
        "verify": cmd_verify,
    }
    fn = commands.get(args.command)
    if fn is None:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        parser.print_help(sys.stderr)
        sys.exit(1)
    fn(args)


if __name__ == "__main__":
    main()
