#!/usr/bin/env python3
"""Does the pipeline's combination rule cost more than its detectors?

The series pipeline decides by taking the maximum score across the eight defense
modules and comparing it to a single threshold.  That rule assumes the eight
scores are commensurable.  They are not: measured against ``BenignCorpus``, four
of the modules never score a legitimate message above 0.0, the firewall reaches
0.56 and the detection module 0.51.  A maximum over incomparable scales is
dominated by whichever module happens to use the widest range, regardless of how
much evidence any of them carries.

The consequence is not subtle.  On held-out data the shipped rule scores a
Youden's J of **-0.069** -- worse than a detector that always says "no".  The
same eight modules, with no change to any of them, standardised against a benign
calibration sample and then combined, reach **+0.052**; the best subset reaches
**+0.254**.  The gap between -0.069 and +0.254 is entirely in the arithmetic
that combines the detectors, not in the detectors.

The subset that wins is the interesting part.  It is ``consensus``,
``provenance``, ``sandbox`` and ``invariants`` -- precisely the four modules the
ablation study reports as contributing exactly nothing.  They contribute nothing
under the maximum rule because their scores are small in absolute terms.  Once
each is measured in units of its own benign distribution, they are the only four
that separate the classes at all, and the four heavily-engineered pattern
matchers are what drags the ensemble below random.

Protocol
--------
Three disjoint splits of the benign corpus and of the attack corpus:

    b1  standardise   each module's mean and standard deviation come from here
    b2  select        the subset and the threshold are chosen here
    b3  TEST          every number reported is measured here, once

Splitting three ways rather than two is deliberate.  Choosing the best of 255
subsets on the same data used to report its score inflates the result badly --
an earlier pass of this analysis reported J = 0.323 that way, against 0.254 when
selection and reporting were finally separated.  This file exists partly to make
that discipline reproducible rather than remembered.

    python3 scripts/run_combination_rule_study.py
    python3 scripts/run_combination_rule_study.py --check
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path
from typing import Sequence

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from attacks.corpus import AttackCorpus  # noqa: E402
from composition.factory import MODULE_REGISTRY  # noqa: E402
from evaluation.benign_corpus import BenignCorpus  # noqa: E402

OUTPUT = REPO / "output" / "data" / "combination_rule_study.json"


def _best_threshold(attack: np.ndarray, benign: np.ndarray) -> tuple[float, float]:
    """The Youden-maximising threshold and its J, on the arrays given."""
    candidates = np.unique(np.concatenate([attack, benign]))
    if not len(candidates):
        return 0.0, 0.0
    j, threshold = max(
        (
            (float((attack > t).mean() - (benign > t).mean()), float(t))
            for t in candidates
        )
    )
    return threshold, j


def _rates(attack: np.ndarray, benign: np.ndarray, threshold: float) -> dict[str, float]:
    tpr = float((attack > threshold).mean())
    fpr = float((benign > threshold).mean())
    return {"tpr": tpr, "fpr": fpr, "youden_j": tpr - fpr}


def build(seed: int) -> dict[str, object]:
    attacks = list(AttackCorpus.generate(seed=42, extended=True))
    benign = list(BenignCorpus.generate())
    modules = {name: cls() for name, cls in MODULE_REGISTRY.items()}
    names = list(modules)

    attack_scores = {
        n: np.array([modules[n].evaluate(s.payload).score for s in attacks]) for n in names
    }
    benign_scores = {
        n: np.array([modules[n].evaluate(x.text).score for x in benign]) for n in names
    }

    rng = np.random.default_rng(seed)
    b1, b2, b3 = np.array_split(rng.permutation(len(benign)), 3)
    a1, a2, a3 = np.array_split(rng.permutation(len(attacks)), 3)

    # Standardise each module against the calibration split only. Its own
    # benign mean and spread are the units in which its score means anything.
    standardised: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for name in names:
        reference = benign_scores[name][b1]
        mean = float(reference.mean())
        spread = float(reference.std()) or 1e-9
        standardised[name] = (
            (attack_scores[name] - mean) / spread,
            (benign_scores[name] - mean) / spread,
        )

    def combine(subset: Sequence[str]) -> tuple[np.ndarray, np.ndarray]:
        return (
            np.max(np.stack([standardised[n][0] for n in subset]), axis=0),
            np.max(np.stack([standardised[n][1] for n in subset]), axis=0),
        )

    # Select on b2/a2, never on b3/a3.
    best_subset: tuple[str, ...] = ()
    best_j = -np.inf
    best_threshold = 0.0
    for size in range(1, len(names) + 1):
        for subset in itertools.combinations(names, size):
            a, b = combine(subset)
            threshold, j = _best_threshold(a[a2], b[b2])
            if j > best_j:
                best_subset, best_j, best_threshold = subset, j, threshold

    results: dict[str, object] = {}

    raw_a = np.max(np.stack([attack_scores[n] for n in names]), axis=0)
    raw_b = np.max(np.stack([benign_scores[n] for n in names]), axis=0)
    shipped_threshold, _ = _best_threshold(raw_a[a2], raw_b[b2])
    results["shipped_max_rule"] = {
        "threshold": shipped_threshold,
        "held_out": _rates(raw_a[a3], raw_b[b3], shipped_threshold),
        "at_default_0_5": _rates(raw_a[a3], raw_b[b3], 0.5),
    }

    all_a, all_b = combine(names)
    all_threshold, _ = _best_threshold(all_a[a2], all_b[b2])
    results["standardised_all_modules"] = {
        "threshold": all_threshold,
        "held_out": _rates(all_a[a3], all_b[b3], all_threshold),
    }

    sub_a, sub_b = combine(best_subset)
    results["standardised_best_subset"] = {
        "subset": list(best_subset),
        "threshold": best_threshold,
        "selection_half_j": best_j,
        "held_out": _rates(sub_a[a3], sub_b[b3], best_threshold),
    }

    results["per_module_benign_scale"] = {
        name: {
            "benign_mean": float(benign_scores[name].mean()),
            "benign_max": float(benign_scores[name].max()),
            "attack_mean": float(attack_scores[name].mean()),
        }
        for name in names
    }

    return {
        "data_origin": "real_pipeline",
        "source_script": "scripts/run_combination_rule_study.py",
        "note": (
            "Every reported number is measured on the third split, which is used "
            "for nothing else. Selecting and reporting on one split inflated an "
            "earlier version of this result from 0.254 to 0.323."
        ),
        "seed": seed,
        "protocol": {
            "standardise_on": len(b1),
            "select_on": len(b2),
            "test_on": len(b3),
            "attacks": len(attacks),
            "benign": len(benign),
        },
        "modules": names,
        "results": results,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)

    fresh = build(args.seed)
    if args.check:
        if not OUTPUT.is_file():
            print(f"missing {OUTPUT.relative_to(REPO)}", file=sys.stderr)
            return 1
        stored = json.loads(OUTPUT.read_text(encoding="utf-8"))
        if stored.get("results") != fresh["results"]:
            print("combination-rule study is stale")
            return 1
        print("combination-rule study: current")
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(fresh, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    r = fresh["results"]
    print(f"wrote {OUTPUT.relative_to(REPO)}")
    print(f"  shipped max rule, held out    J = {r['shipped_max_rule']['held_out']['youden_j']:+.4f}")
    print(f"  standardised, all 8 modules   J = {r['standardised_all_modules']['held_out']['youden_j']:+.4f}")
    best = r["standardised_best_subset"]
    print(
        f"  standardised, best subset     J = {best['held_out']['youden_j']:+.4f}"
        f"  TPR {best['held_out']['tpr']:.4f} FPR {best['held_out']['fpr']:.4f}"
    )
    print(f"    subset: {', '.join(best['subset'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
