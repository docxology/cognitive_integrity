#!/usr/bin/env python3
"""What each defense module can detect, separated from what it contributes.

The ablation reports a Shapley value of exactly zero for the provenance,
sandbox and consensus adapters, and that number has been read three different
ways over this project's life. It was first read as "these mechanisms do not
work". It was then read as "the corpus contains no instance of what they
catch", and ``AttackCorpus`` was extended by 525 items across
``provenance_laundering``, ``sandbox_escape`` and ``byzantine_manipulation`` to
close exactly that gap. The Shapley values stayed at zero.

This artifact exists because both readings were wrong, and neither could be
distinguished from the other by looking at an ablation table. Measured one
module at a time against the family built for it:

* ``provenance`` detects 20.0% of provenance-laundering payloads.
* ``sandbox`` detects 28.6% of sandbox-escape payloads.
* ``consensus`` detected 0.0% of byzantine-manipulation payloads, and 0.0% of
  everything else, until it was rewritten. It now detects 81.1% of them at a
  false-positive rate of 0.0% against the hard benign corpus, and its Shapley
  value is still exactly zero.

So none of the three is incapable: all three are *masked*. The invariants
adapter independently catches 24.0%, 85.1% and 89.7% of those same three
families, and a maximum-rule pipeline that already contains invariants gains
nothing by adding a detector that fires on a subset of the same payloads. Zero
marginal contribution in a coalition is a statement about redundancy, not about
capacity, and consensus is the proof: a module can go from detecting nothing to
detecting four payloads in five without its Shapley value moving by a digit.
Where it does show up is in the pairwise synergies, which are measured over
coalitions that exclude invariants -- consensus pairs with sandbox and with
tripwire at +0.05 each. A module that is redundant with the best detector
present is not redundant when that detector is absent, which is the whole
argument for defense in depth and is invisible in the marginal column.

Marginal contribution and capability are different measurements and this file
reports both, because the ablation alone cannot tell them apart and three
successive rounds of this project read it wrong.

    python3 scripts/run_module_capability_matrix.py
    python3 scripts/run_module_capability_matrix.py --check
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from attacks.corpus import AttackCorpus  # noqa: E402
from composition.factory import MODULE_REGISTRY  # noqa: E402
from evaluation.benign_corpus import BenignCorpus  # noqa: E402

OUTPUT = REPO / "output" / "data" / "module_capability_matrix.json"


def build(seed: int = 42) -> dict[str, object]:
    corpus = list(AttackCorpus.generate(seed=seed))
    benign = list(BenignCorpus.generate())
    modules = {name: cls() for name, cls in MODULE_REGISTRY.items()}

    by_category: dict[str, list[str]] = defaultdict(list)
    for sample in corpus:
        key = getattr(sample.category, "value", str(sample.category))
        by_category[key].append(sample.payload)

    matrix: dict[str, dict[str, float]] = {}
    latency: dict[str, dict[str, float]] = {}
    for name, module in modules.items():
        matrix[name] = {
            category: sum(1 for p in payloads if module.evaluate(p).detected) / len(payloads)
            for category, payloads in sorted(by_category.items())
        }
        # Per-call latency, measured on the same pass. The modules differ by
        # more than an order of magnitude and every published per-module
        # latency in this project had been a typed round number, so the
        # distribution is recorded rather than the mean alone: these are
        # wall-clock timings and the mean is what one scheduling hiccup moves.
        samples = sorted(module.evaluate(s.payload).latency_ms for s in corpus)
        middle = len(samples) // 2
        latency[name] = {
            "mean_ms": sum(samples) / len(samples),
            "median_ms": (
                samples[middle]
                if len(samples) % 2
                else (samples[middle - 1] + samples[middle]) / 2
            ),
            "p95_ms": samples[min(len(samples) - 1, int(0.95 * len(samples)))],
            "max_ms": samples[-1],
            "n": len(samples),
        }
        matrix[name]["_overall"] = sum(
            1 for s in corpus if module.evaluate(s.payload).detected
        ) / len(corpus)
        matrix[name]["_benign_fpr"] = sum(
            1 for b in benign if module.evaluate(b.text).detected
        ) / len(benign)

    # A module is dead only if it fires on nothing anywhere. A module that
    # fires and still contributes nothing is masked by a stronger one.
    silent = sorted(n for n, row in matrix.items() if row["_overall"] == 0.0)
    live_but_maskable = sorted(
        n for n, row in matrix.items() if 0.0 < row["_overall"] < 0.10
    )

    return {
        "data_origin": "real_pipeline",
        "source_script": "scripts/run_module_capability_matrix.py",
        "seed": seed,
        "corpus_size": len(corpus),
        "categories": len(by_category),
        "benign_size": len(benign),
        "category_counts": {k: len(v) for k, v in sorted(by_category.items())},
        "detection_rate": matrix,
        "latency_ms": latency,
        "silent_modules": silent,
        "low_rate_modules": live_but_maskable,
        "note": (
            "detection_rate[module][category] is that module evaluated alone. "
            "It is not a marginal contribution and must never be compared to a "
            "Shapley value: a module can detect a family and still add nothing "
            "to a pipeline that already contains a module detecting the same "
            "payloads."
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
        if stored.get("detection_rate") != fresh["detection_rate"]:
            print("module capability matrix is stale")
            return 1
        print("module capability matrix: current")
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(fresh, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(REPO)}")
    for name, row in sorted(fresh["detection_rate"].items()):
        print(f"  {name:16s} overall {row['_overall']:.3f}   benign FPR {row['_benign_fpr']:.3f}")
    print(f"  silent (fire on nothing): {', '.join(fresh['silent_modules']) or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
