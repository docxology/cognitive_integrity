#!/usr/bin/env python3
"""AUC with bootstrap intervals, for the drift detector and the fused ensemble.

``tab:auc-ci`` in S02 was captioned "Empirical AUC with 95% confidence
intervals" and reported Drift Score 0.87 [0.84, 0.90] and Ensemble 0.94
[0.92, 0.96]. Nothing produced any of the four numbers, and a note two lines
above the table called them design-level values from parametric evaluation,
contradicting the caption in the same breath.

The machinery to measure them was already present and unused:
``evaluation.roc`` builds the curve and bootstraps the interval, and
``composition.fusion`` combines module scores. This runs both over the attack
corpus and the hard benign corpus, which is the pair every other rate in this
series is measured against.

Why the ensemble is the whole registry
--------------------------------------
The fused row combines all eight modules through
:class:`~composition.fusion.WeightedAverageFusion` at equal weight. An ensemble
of a chosen subset would need the choice justified, and choosing on the data
you then report from is the inflation this project has already corrected once.

    python3 scripts/run_detector_auc.py
    python3 scripts/run_detector_auc.py --check
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from attacks.corpus import AttackCorpus  # noqa: E402
from composition.factory import MODULE_REGISTRY  # noqa: E402
from composition.fusion import WeightedAverageFusion  # noqa: E402
from evaluation.benign_corpus import BenignCorpus  # noqa: E402
from evaluation.roc import bootstrap_auc_ci  # noqa: E402

OUTPUT = REPO / "output" / "data" / "detector_auc.json"

#: Resamples behind each interval. Recorded in the artifact so the caption can
#: state it instead of asserting a number nobody chose.
N_BOOTSTRAP = 1000


def build(seed: int = 42) -> dict[str, object]:
    attacks = [s.payload for s in AttackCorpus.generate(seed=seed)]
    benign = [b.text for b in BenignCorpus.generate()]
    messages = attacks + benign
    labels = np.array([True] * len(attacks) + [False] * len(benign))

    modules = {name: cls() for name, cls in MODULE_REGISTRY.items()}
    names = sorted(modules)

    # One evaluation per module per message, kept as DefenseResult objects:
    # WeightedAverageFusion.fuse consumes results, not bare scores.
    results = {
        name: [modules[name].evaluate(m) for m in messages] for name in names
    }
    scores = {
        name: np.array([r.score for r in results[name]]) for name in names
    }

    # The ensemble: equal-weight average over every module, scored per message.
    fusion = WeightedAverageFusion()
    fused = np.array(
        [
            # fuse returns (detected, score); the AUC needs the score.
            fusion.fuse([results[n][i] for n in names])[1]
            for i in range(len(messages))
        ]
    )

    detectors: dict[str, dict[str, float]] = {}
    for label, series in [
        ("drift_detection", scores["detection"]),
        ("invariants", scores["invariants"]),
        ("firewall", scores["firewall"]),
        ("ensemble_weighted_average", fused),
    ]:
        auc, low, high = bootstrap_auc_ci(
            labels, series, n_bootstrap=N_BOOTSTRAP, seed=seed
        )
        detectors[label] = {"auc": auc, "ci_low": low, "ci_high": high}

    return {
        "data_origin": "real_pipeline",
        "source_script": "scripts/run_detector_auc.py",
        "seed": seed,
        "n_attacks": len(attacks),
        "n_benign": len(benign),
        "n_bootstrap": N_BOOTSTRAP,
        "ci": 0.95,
        "fusion": "WeightedAverageFusion, equal weights over all eight modules",
        "detectors": detectors,
        "note": (
            "Scored over the integrated attack corpus and the 120-item hard "
            "benign corpus. The interval is a percentile bootstrap over "
            f"{N_BOOTSTRAP} resamples of the labelled set, not an assumed "
            "sampling distribution."
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
        if stored.get("detectors") != fresh["detectors"]:
            print("detector AUC study is stale")
            return 1
        print("detector AUC: current")
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(fresh, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(REPO)}")
    for name, row in fresh["detectors"].items():
        print(
            f"  {name:28s} AUC {row['auc']:.3f}  "
            f"95% CI [{row['ci_low']:.3f}, {row['ci_high']:.3f}]"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
