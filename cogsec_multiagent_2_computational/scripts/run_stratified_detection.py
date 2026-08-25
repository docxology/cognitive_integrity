#!/usr/bin/env python3
"""Detection stratified by adversary class and by what the attack targets.

Four claims across two papers stratify results along dimensions the corpus did
not carry. ``AttackSample`` had category, subcategory and difficulty and
nothing else, so a "third view of the same 950 samples" had no third dimension
to view them along, a per-adversary-class miss rate had no class to group by,
and the numbers published for both were typed.

``omega_level`` and ``target`` now exist on the sample, assigned per category
in ``attacks.corpus._CATEGORY_PROFILE``. This scores the corpus through the
full pipeline and reports the breakdown along both.

What this is not
----------------
An independent axis. Both fields are category-determined, so a stratum here is
a re-grouping of the category breakdown rather than a new measurement. The
groupings are the ones Part 1's threat model uses and the categories do not map
onto them one to one, which is what makes the view worth having; it is not what
would make it a second experiment.

A third dimension the papers report, *impact*, is deliberately absent. Unlike
class and target it varies within a category by design, so assigning it per
category would manufacture an axis rather than expose one, and the impact-
stratified claim it would support has been retracted instead.

    python3 scripts/run_stratified_detection.py
    python3 scripts/run_stratified_detection.py --check
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from attacks.corpus import ATTACK_TARGETS, AttackCorpus  # noqa: E402
from composition.factory import create_full_pipeline  # noqa: E402
from evaluation.benign_corpus import BenignCorpus  # noqa: E402

OUTPUT = REPO / "output" / "data" / "stratified_detection.json"


def build(seed: int = 42) -> dict[str, object]:
    corpus = list(AttackCorpus.generate(seed=seed))
    benign = list(BenignCorpus.generate())
    pipeline = create_full_pipeline()

    unlabelled = [s.id for s in corpus if not s.target or not s.omega_level]
    if unlabelled:
        raise RuntimeError(
            f"{len(unlabelled)} samples carry no target or adversary class "
            f"(first: {unlabelled[0]}); a stratified report that silently "
            f"dropped them would be the defect this file replaces"
        )

    by_target: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    by_omega: dict[int, list[int]] = defaultdict(lambda: [0, 0])
    for sample in corpus:
        detected = pipeline.evaluate(sample.payload).detected
        for bucket, key in ((by_target, sample.target), (by_omega, sample.omega_level)):
            bucket[key][1] += 1
            if detected:
                bucket[key][0] += 1

    fpr = sum(1 for b in benign if pipeline.evaluate(b.text).detected) / len(benign)

    def rates(bucket: dict) -> dict:
        return {
            str(key): {
                "n": n,
                "detected": d,
                "tpr": d / n,
                "miss_rate": (n - d) / n,
            }
            for key, (d, n) in sorted(bucket.items())
        }

    return {
        "data_origin": "real_pipeline",
        "source_script": "scripts/run_stratified_detection.py",
        "seed": seed,
        "corpus_size": len(corpus),
        "benign_size": len(benign),
        "benign_fpr": fpr,
        "targets": list(ATTACK_TARGETS),
        "by_target": rates(by_target),
        "by_omega_level": rates(by_omega),
        "note": (
            "omega_level and target are assigned per category, so a stratum is "
            "a re-grouping of the category breakdown rather than an independent "
            "axis. The false-positive rate is a property of the pipeline and the "
            "benign corpus, not of any stratum, so it is reported once."
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
        if stored.get("by_target") != fresh["by_target"] or stored.get(
            "by_omega_level"
        ) != fresh["by_omega_level"]:
            print("stratified detection is stale")
            return 1
        print("stratified detection: current")
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(fresh, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(REPO)}")
    for label, bucket in (("target", fresh["by_target"]), ("Omega", fresh["by_omega_level"])):
        print(f"  by {label}:")
        for key, row in bucket.items():
            print(
                f"    {key:22s} n={row['n']:5d}  TPR {row['tpr']:.3f}  "
                f"miss {row['miss_rate']:.3f}"
            )
    print(f"  benign FPR (whole pipeline, all strata): {fresh['benign_fpr']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
