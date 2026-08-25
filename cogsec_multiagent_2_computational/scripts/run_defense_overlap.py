#!/usr/bin/env python3
"""How much of the corpus each defense catches, and how much only it catches.

The defense-composition figure has always shown a five-row table of per-mechanism
``unique``, ``shared`` and ``total`` detection rates. Sixteen of its twenty
cells were literal strings -- ``"23%"``, ``"35%"``, ``"58%"`` -- and the
seventeenth, the Full CIF row, was computed by feeding the four literal totals
through the series-composition rule. A reader saw four measured mechanisms and
a composition theorem confirmed against them. Nothing had been measured, and
the one computed cell could only ever agree with the literals it was computed
from.

This measures it. For every module in ``MODULE_REGISTRY``, over the integrated
attack corpus:

``total``
    the fraction of attacks the module detects on its own.
``unique``
    the fraction it is the *only* module to detect. This is the number the
    figure is really about, because a mechanism whose every detection is also
    caught by another contributes nothing to a union and everything to a
    marginal-contribution table that reads zero.
``shared``
    ``total - unique``, by construction rather than by assertion.

The union row is the real full-pipeline rate: the fraction of attacks at least
one module detects. It is reported next to what the series composition rule
predicts from the same solo rates, and the two are allowed to disagree --
disagreement is the finding, because the rule assumes independence and the
modules are anything but independent. Publishing the prediction in place of the
measurement, as the figure did, made a test of the composition algebra into a
restatement of its own inputs.

    python3 scripts/run_defense_overlap.py
    python3 scripts/run_defense_overlap.py --check
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from attacks.corpus import AttackCorpus  # noqa: E402
from composition.factory import MODULE_REGISTRY  # noqa: E402
from composition.algebra import (  # noqa: E402
    compute_parallel_detection_rate,
    compute_series_detection_rate,
)
from evaluation.benign_corpus import BenignCorpus  # noqa: E402

OUTPUT = REPO / "output" / "data" / "defense_overlap.json"


def build(seed: int = 42) -> dict[str, object]:
    corpus = list(AttackCorpus.generate(seed=seed))
    benign = list(BenignCorpus.generate())
    modules = {name: cls() for name, cls in MODULE_REGISTRY.items()}
    names = sorted(modules)

    # One pass, one detection matrix: every rate below is a projection of it,
    # so no two numbers in this artifact can disagree about the same event.
    detected: dict[str, list[bool]] = {
        name: [modules[name].evaluate(s.payload).detected for s in corpus] for name in names
    }
    benign_flagged: dict[str, list[bool]] = {
        name: [modules[name].evaluate(b.text).detected for b in benign] for name in names
    }

    n = len(corpus)
    per_module: dict[str, dict[str, float]] = {}
    for name in names:
        hits = detected[name]
        others = [detected[other] for other in names if other != name]
        unique = sum(
            1 for i, hit in enumerate(hits) if hit and not any(o[i] for o in others)
        )
        total = sum(hits)
        per_module[name] = {
            "total": total / n,
            "unique": unique / n,
            "shared": (total - unique) / n,
            "benign_fpr": sum(benign_flagged[name]) / len(benign),
        }

    union = sum(1 for i in range(n) if any(detected[name][i] for name in names)) / n
    union_benign = sum(
        1 for i in range(len(benign)) if any(benign_flagged[name][i] for name in names)
    ) / len(benign)

    solo_rates = [per_module[name]["total"] for name in names]
    series_prediction = compute_series_detection_rate(solo_rates)
    parallel_prediction = compute_parallel_detection_rate(solo_rates, strategy="max")

    # A module every one of whose detections is also caught by another cannot
    # raise a union, however high its solo rate. Naming them is the point of
    # measuring uniqueness rather than assuming it.
    fully_redundant = sorted(
        name for name in names if per_module[name]["total"] > 0 and per_module[name]["unique"] == 0
    )

    return {
        "data_origin": "real_pipeline",
        "source_script": "scripts/run_defense_overlap.py",
        "seed": seed,
        "corpus_size": n,
        "benign_size": len(benign),
        "modules": names,
        "per_module": per_module,
        "union": {"tpr": union, "fpr": union_benign},
        "composition": {
            "series_prediction": series_prediction,
            "parallel_max_prediction": parallel_prediction,
            "measured_union": union,
            "series_error": series_prediction - union,
        },
        "fully_redundant_modules": fully_redundant,
        "note": (
            "unique = detected by this module and no other; shared = total - unique. "
            "series_prediction assumes the modules are independent and is reported "
            "beside the measured union rather than in place of it: the gap between "
            "them is how far that assumption is from true on this corpus."
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
        if stored.get("per_module") != fresh["per_module"]:
            print("defense overlap is stale")
            return 1
        print("defense overlap: current")
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(fresh, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(REPO)}")
    print(f"  {'module':16s} {'total':>8s} {'unique':>8s} {'shared':>8s} {'benign':>8s}")
    for name in fresh["modules"]:
        row = fresh["per_module"][name]
        print(
            f"  {name:16s} {row['total']:8.3f} {row['unique']:8.3f} "
            f"{row['shared']:8.3f} {row['benign_fpr']:8.3f}"
        )
    c = fresh["composition"]
    print(f"  union (measured)   TPR {fresh['union']['tpr']:.3f}  FPR {fresh['union']['fpr']:.3f}")
    print(
        f"  series rule predicts {c['series_prediction']:.3f}, "
        f"error {c['series_error']:+.3f}"
    )
    print(f"  fully redundant: {', '.join(fresh['fully_redundant_modules']) or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
