#!/usr/bin/env python3
"""Sweep the firewall's two thresholds and record the operating curve.

Part 3's case study reports a τ₂ tuning outcome as an observed deployment
result -- 0.50 → 0.55 dropping the false-positive rate from 6% to 3% while true
positives fall from 72% to 68%. Nothing had ever varied a threshold and
measured what happened.

What the sweep finds is worse than four wrong numbers. Across the whole range
the firewall's τ₂ is **flat between 0.20 and 0.75**: every value in that band,
including both endpoints of the published tuning, produces exactly the same
TPR and the same FPR. Above 0.80 the firewall stops flagging anything at all.
So the knob the case study recommends tuning does nothing where it recommends
tuning it.

And the curve it does trace is negative. The firewall alone flags more benign
messages than attacks at every threshold below 0.80, so Youden's J never rises
above zero: the best available operating point is the one where the component
is switched off. That is consistent with what the ablation and the capability
matrix already say about this module -- 0.054 detection at a 0.100 benign
false-positive rate -- and it is the first time the threshold story has been
measured rather than asserted.

    python3 scripts/run_threshold_sweep.py
    python3 scripts/run_threshold_sweep.py --check
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from attacks.corpus import AttackCorpus  # noqa: E402
from core.firewall import FirewallConfig  # noqa: E402
from evaluation.benign_corpus import BenignCorpus  # noqa: E402
from evaluation.threshold_sweep import (  # noqa: E402
    sweep_quarantine_threshold,
    sweep_reject_threshold,
)

OUTPUT = REPO / "output" / "data" / "threshold_sweep.json"

#: Twenty-first steps: fine enough to find a plateau's edges, coarse enough
#: that the artifact stays readable.
GRID = [i / 20 for i in range(21)]


def _serialise(points) -> list[dict]:
    return [
        {
            "tau": p.tau,
            "tpr": p.tpr,
            "fpr": p.fpr,
            "youden_j": p.youden_j,
            "quarantine_rate": p.quarantine_rate,
            "reject_rate": p.reject_rate,
        }
        for p in points
    ]


def _plateau(points) -> dict | None:
    """The widest run of thresholds that change nothing.

    A threshold documented as tunable that is flat across the band it is tuned
    in is a different defect from one whose numbers are merely stale, and it is
    invisible unless something looks for it.
    """
    best = None
    start = 0
    for i in range(1, len(points) + 1):
        same = i < len(points) and (
            points[i].tpr == points[start].tpr and points[i].fpr == points[start].fpr
        )
        if not same:
            width = i - start
            if best is None or width > best[0]:
                best = (width, points[start].tau, points[i - 1].tau,
                        points[start].tpr, points[start].fpr)
            start = i
    if best is None or best[0] < 2:
        return None
    return {
        "n_points": best[0],
        "tau_low": best[1],
        "tau_high": best[2],
        "tpr": best[3],
        "fpr": best[4],
    }


def build(seed: int = 42) -> dict[str, object]:
    attacks = [s.payload for s in AttackCorpus.generate(seed=seed)]
    benign = [b.text for b in BenignCorpus.generate()]
    shipped = FirewallConfig()

    quarantine = sweep_quarantine_threshold(GRID, attacks, benign)
    reject = sweep_reject_threshold(GRID, attacks, benign)

    best = max(quarantine, key=lambda p: p.youden_j)
    return {
        "data_origin": "real_pipeline",
        "source_script": "scripts/run_threshold_sweep.py",
        "seed": seed,
        "n_attacks": len(attacks),
        "n_benign": len(benign),
        "shipped": {
            "injection_threshold": shipped.injection_threshold,
            "suspicious_threshold": shipped.suspicious_threshold,
        },
        "quarantine_sweep": _serialise(quarantine),
        "reject_sweep": _serialise(reject),
        "quarantine_plateau": _plateau(quarantine),
        "best_quarantine_point": {
            "tau": best.tau,
            "tpr": best.tpr,
            "fpr": best.fpr,
            "youden_j": best.youden_j,
        },
        "note": (
            "Scored on the firewall alone, not the pipeline: the claim under "
            "test is about the firewall's own threshold. An input counts as "
            "flagged when the firewall does anything but accept it, because a "
            "quarantined message costs an operator a review exactly as a "
            "rejected one does."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    fresh = build(args.seed)
    if args.check:
        if not OUTPUT.is_file():
            print(f"missing {OUTPUT.relative_to(REPO)}", file=sys.stderr)
            return 1
        stored = json.loads(OUTPUT.read_text(encoding="utf-8"))
        if stored.get("quarantine_sweep") != fresh["quarantine_sweep"]:
            print("threshold sweep is stale")
            return 1
        print("threshold sweep: current")
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(fresh, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(REPO)}")
    for row in fresh["quarantine_sweep"]:
        print(
            f"  tau2={row['tau']:.2f}  TPR {row['tpr']:.3f}  FPR {row['fpr']:.3f}  "
            f"J {row['youden_j']:+.3f}"
        )
    plateau = fresh["quarantine_plateau"]
    if plateau:
        print(
            f"  flat from tau2 {plateau['tau_low']:.2f} to {plateau['tau_high']:.2f} "
            f"({plateau['n_points']} points): TPR {plateau['tpr']:.3f}, "
            f"FPR {plateau['fpr']:.3f}"
        )
    best = fresh["best_quarantine_point"]
    print(f"  best J {best['youden_j']:+.3f} at tau2 {best['tau']:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
