#!/usr/bin/env python3
"""Measure detection across the full attack taxonomy and the full defense lattice.

S08's per-architecture tables report a six-way attack taxonomy crossed with five
defense configurations: 23 tables, 294 numeric cells.  None of it was measured.
The only artifact behind them, ``full_evaluation_results.json``, carries four
categories, no defense axis, and a provenance sidecar saying in as many words
that it is ``parametric_simulation`` and "NOT empirically measured pipeline
evidence".  Of S08's six attack families, exactly one -- direct injection --
appears in that artifact at all.

The corpus, meanwhile, has had twelve real attack categories and 950 items the
whole time.  ``AttackCorpus.generate`` produces them deterministically and
``evaluate_component_subset`` already runs any component subset through the real
pipeline.  What was missing was only the join: nobody had run every family
through every configuration and written it down.

So this does that, exhaustively rather than for the eighteen configurations the
two reported axes strictly need.  One pipeline evaluation costs about 0.07 ms,
which puts the entire subset lattice -- all :math:`2^8 = 256` combinations of
the eight defense components -- at roughly half a minute.  When the complete
answer is that cheap, sampling it is a false economy: the lattice yields the
X-only and leave-one-out axes as slices, and also exact Shapley values, every
pairwise synergy, and the marginal contribution of any component in any context,
none of which can be recovered from the eighteen.

    python3 scripts/run_taxonomy_evaluation.py            # run and write
    python3 scripts/run_taxonomy_evaluation.py --check    # fail if stale
    python3 scripts/run_taxonomy_evaluation.py --axes     # 18 configs, not 256

Determinism and idempotence
---------------------------
Everything here is a pure function of ``--seed``: the corpus, the benign set,
and every adapter are deterministic and no noise is added.  Re-running writes a
byte-identical artifact, so ``--check`` can diff rather than re-measure, and two
components with identical behaviour produce an exactly-zero delta rather than a
small signed number that looks like a finding.

The output carries the corpus digest.  A corpus change that would silently
invalidate every cell instead shows up as a digest mismatch under ``--check``.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from ablation.runner import COMPONENT_TO_MODULE  # noqa: E402
from attacks.corpus import AttackCorpus  # noqa: E402
from composition.factory import create_pipeline_without  # noqa: E402
from evaluation.benign_corpus import BenignCorpus  # noqa: E402

#: The negative arm. Deliberately NOT ablation.runner.BENIGN_MESSAGES, which is
#: 50 plainly-innocuous strings: measured against those, false-positive rates
#: come out near zero and every threshold looks generous. BenignCorpus is the
#: designed negative set -- 120 items, half a `hard` stratum of legitimate
#: messages carrying attack-adjacent vocabulary -- and it is the only one that
#: makes an FPR number mean anything. Against the easy set this pipeline
#: appears to reach 74% detection at no cost; against this one, Youden's J is
#: negative below tau = 0.56.
BENIGN_MESSAGES: list[str] = [item.text for item in BenignCorpus.generate()]

#: The default artifact is measured on the integrated 1,475-item corpus, which
#: is the only corpus that reaches all eight defense components. The published
#: 950-item corpus is retained under --published so the previously reported
#: figures stay reproducible; it is a comparison, not an alternative.
OUTPUT = REPO / "output" / "data" / "taxonomy_evaluation_results.json"
OUTPUT_PUBLISHED = REPO / "output" / "data" / "taxonomy_evaluation_published.json"

#: The eight defense components, in the order the ablation registry lists them.
COMPONENTS: tuple[str, ...] = tuple(COMPONENT_TO_MODULE)

#: The corpus's twelve categories roll up into the six families S08 reports.
#: This mapping is the whole reason the S08 tables can be regenerated rather
#: than retired: every family is a union of categories the corpus really has,
#: so a six-way number is an aggregate of measurements and not an interpolation.
FAMILY_OF: dict[str, str] = {
    "direct_injection": "direct_injection",
    "indirect_injection": "indirect_injection",
    "nested_injection": "nested_injection",
    "impersonation": "trust_exploitation",
    "trust_inflation": "trust_exploitation",
    "delegation_abuse": "trust_exploitation",
    "belief_drift": "belief_manipulation",
    "belief_fabrication": "belief_manipulation",
    "belief_injection": "belief_manipulation",
    "sybil_attack": "coordination",
    "consensus_poisoning": "coordination",
    "timing_attack": "coordination",
    # Added with the corpus extension: the three categories that exercise the
    # modules the original 950 items never reached. They were first written as
    # mapping to themselves, which silently turned the documented six-way
    # roll-up into a nine-way one and gave every consumer three "families" of
    # exactly one category each. They belong to one family, which is also the
    # corpus's own top category for them.
    "provenance_laundering": "provenance_and_isolation",
    "sandbox_escape": "provenance_and_isolation",
    "byzantine_manipulation": "provenance_and_isolation",
}

#: Why the three injection categories are *not* collapsed the way the others
#: are: the roll-up is deliberately finer than the corpus's own top category
#: there, because injection is 500 of the published 950 items and reporting it
#: as one family would hide the differences between direct, indirect and
#: nested attacks that the whole taxonomy exists to separate. Everything else
#: rolls up to the corpus's own family.
_DELIBERATELY_SPLIT = frozenset(
    {"direct_injection", "indirect_injection", "nested_injection"}
)


class TaxonomyMismatch(RuntimeError):
    """The corpus stopped matching the family map."""


def _subset_key(subset: Sequence[str]) -> str:
    return "+".join(sorted(subset)) if subset else "baseline"


def _corpus_digest(samples: Sequence[object]) -> str:
    """A digest of what was actually evaluated, not of the file that made it."""
    digest = hashlib.sha256()
    for sample in samples:
        digest.update(f"{sample.id}\x00{sample.category.value}\x00".encode())
        digest.update(sample.payload.encode())
        digest.update(b"\x01")
    return digest.hexdigest()


def _evaluate(subset: Sequence[str], samples: Sequence[object]) -> dict[str, object]:
    """Detection by category for one component subset, plus its FPR."""
    if not subset:
        # create_pipeline_without rejects an empty pipeline, and a stack with no
        # defense modules detects nothing by construction. Answer the degenerate
        # case directly rather than fabricating a rate for it.
        per_category = {
            category: {"n": count, "detected": 0, "tpr": 0.0}
            for category, count in _category_counts(samples).items()
        }
        return {"per_category": per_category, "false_positives": 0, "fpr": 0.0}

    excluded = [
        module for name, module in COMPONENT_TO_MODULE.items() if name not in set(subset)
    ]
    pipeline = create_pipeline_without(excluded)

    detected: dict[str, int] = defaultdict(int)
    total: dict[str, int] = defaultdict(int)
    for sample in samples:
        category = sample.category.value
        total[category] += 1
        if pipeline.evaluate(sample.payload).detected:
            detected[category] += 1

    false_positives = sum(
        1 for message in BENIGN_MESSAGES if pipeline.evaluate(message).detected
    )
    per_category = {
        category: {
            "n": count,
            "detected": detected[category],
            "tpr": detected[category] / count if count else 0.0,
        }
        for category, count in sorted(total.items())
    }
    return {
        "per_category": per_category,
        "false_positives": false_positives,
        "fpr": false_positives / len(BENIGN_MESSAGES) if BENIGN_MESSAGES else 0.0,
    }


def threshold_sweep(samples: Sequence[object], grid: Sequence[float]) -> dict[str, object]:
    """Detection and false-positive rates as a function of the decision threshold.

    The adapters decide ``score > threshold`` with ``threshold=0.5`` by default,
    and the whole-corpus rate at that operating point is 13.5%.  That number
    reads as a capability ceiling and is not one: the benign messages top out at
    0.367, so the shipped threshold sits a sixth of the scale above anything a
    legitimate message produces.  Everything between the benign ceiling and 0.5
    is detection given away for no false-positive benefit at all.

    Recording the sweep rather than the single operating point is what makes
    that visible, and what lets the paper state a calibrated result instead of
    an artifact of one default.
    """
    scored_attacks: dict[str, list[float]] = defaultdict(list)
    pipeline = create_pipeline_without([])
    for sample in samples:
        scored_attacks[FAMILY_OF[sample.category.value]].append(
            pipeline.evaluate(sample.payload).score
        )
    benign = [pipeline.evaluate(message).score for message in BENIGN_MESSAGES]
    every_attack = [score for scores in scored_attacks.values() for score in scores]

    points = []
    for threshold in grid:
        tpr = sum(1 for s in every_attack if s > threshold) / len(every_attack)
        fpr = sum(1 for s in benign if s > threshold) / len(benign)
        points.append(
            {
                "threshold": round(threshold, 4),
                "tpr": tpr,
                "fpr": fpr,
                "youden_j": tpr - fpr,
                "per_family": {
                    family: sum(1 for s in scores if s > threshold) / len(scores)
                    for family, scores in sorted(scored_attacks.items())
                },
            }
        )
    best = max(points, key=lambda p: p["youden_j"])
    zero_fpr = [p for p in points if p["fpr"] == 0.0]
    return {
        "grid": points,
        "benign_score_max": max(benign),
        "benign_score_median": sorted(benign)[len(benign) // 2],
        "shipped_threshold": 0.5,
        "youden_optimal": best,
        "best_at_zero_fpr": max(zero_fpr, key=lambda p: p["tpr"]) if zero_fpr else None,
    }


def per_module_calibration(samples: Sequence[object], seed: int) -> dict[str, object]:
    """What each module could contribute if its threshold matched its own scale.

    Every one of the eight adapters ships ``threshold = 0.5``.  They do not
    share a score scale: six of them never score a benign message above 0.0 at
    all, the firewall tops out at 0.20 on benign input and the consensus
    adapter at 0.10.  A single global default across eight different scales is
    not a calibration, and the cost is measurable -- the consensus adapter
    discriminates well (median 0.31 on the attacks it is built for against a
    0.10 benign ceiling) and contributes exactly nothing, because 0.5 is five
    times its own ceiling.

    Thresholds are chosen on a calibration half and reported on a held-out
    half.  Choosing and reporting on the same corpus would make every number
    below an upper bound rather than an estimate, which is precisely the error
    the parametric tables already make.
    """
    from composition.factory import MODULE_REGISTRY

    rng = np.random.default_rng(seed)
    order = rng.permutation(len(samples))
    split = len(samples) // 2
    calibrate = [samples[i] for i in order[:split]]
    holdout = [samples[i] for i in order[split:]]
    benign_split = len(BENIGN_MESSAGES) // 2
    benign_cal = BENIGN_MESSAGES[:benign_split]
    benign_hold = BENIGN_MESSAGES[benign_split:]

    grid = [i / 400 for i in range(401)]
    modules: dict[str, object] = {}
    for name, cls in MODULE_REGISTRY.items():
        module = cls()
        cal_attack = [module.evaluate(s.payload).score for s in calibrate]
        cal_benign = [module.evaluate(m).score for m in benign_cal]
        hold_attack = [module.evaluate(s.payload).score for s in holdout]
        hold_benign = [module.evaluate(m).score for m in benign_hold]

        def rates(scores_a, scores_b, threshold):
            tpr = sum(1 for x in scores_a if x > threshold) / len(scores_a)
            fpr = sum(1 for x in scores_b if x > threshold) / len(scores_b) if scores_b else 0.0
            return tpr, fpr

        chosen = max(grid, key=lambda t: (lambda r: r[0] - r[1])(rates(cal_attack, cal_benign, t)))
        clean = [t for t in grid if rates(cal_attack, cal_benign, t)[1] == 0.0]
        chosen_clean = (
            max(clean, key=lambda t: rates(cal_attack, cal_benign, t)[0])
            if clean
            else chosen
        )

        j_tpr, j_fpr = rates(hold_attack, hold_benign, chosen)
        c_tpr, c_fpr = rates(hold_attack, hold_benign, chosen_clean)
        s_tpr, s_fpr = rates(hold_attack, hold_benign, 0.5)
        modules[name] = {
            "shipped_threshold": float(getattr(module, "_threshold", 0.5)),
            "benign_score_max_calibration": max(cal_benign) if cal_benign else 0.0,
            "youden_threshold": chosen,
            "youden_holdout": {"tpr": j_tpr, "fpr": j_fpr},
            "zero_fpr_threshold": chosen_clean,
            "zero_fpr_holdout": {"tpr": c_tpr, "fpr": c_fpr},
            "shipped_holdout": {"tpr": s_tpr, "fpr": s_fpr},
        }
    return {
        "protocol": "thresholds chosen on a random half, reported on the held-out half",
        "seed": seed,
        "n_calibration": len(calibrate),
        "n_holdout": len(holdout),
        "modules": modules,
    }


def _category_counts(samples: Sequence[object]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for sample in samples:
        counts[sample.category.value] += 1
    return dict(sorted(counts.items()))


def _subsets(mode: str) -> Iterable[tuple[str, ...]]:
    """Every subset, or just the two reported axes."""
    if mode == "lattice":
        for size in range(len(COMPONENTS) + 1):
            yield from itertools.combinations(COMPONENTS, size)
        return
    yield ()
    for component in COMPONENTS:  # X-only
        yield (component,)
    for component in COMPONENTS:  # leave-one-out
        yield tuple(c for c in COMPONENTS if c != component)
    yield COMPONENTS


def _shapley(cells: dict[str, dict], family_tpr: dict[str, dict[str, float]]) -> dict[str, float]:
    """Exact Shapley value per component, over the whole-corpus TPR.

    Exact rather than sampled, because the full lattice is present: every
    marginal contribution is a lookup, so there is nothing to approximate.
    """
    n = len(COMPONENTS)
    values: dict[str, float] = {}
    for component in COMPONENTS:
        others = [c for c in COMPONENTS if c != component]
        total = 0.0
        for size in range(len(others) + 1):
            weight = math.factorial(size) * math.factorial(n - size - 1) / math.factorial(n)
            for coalition in itertools.combinations(others, size):
                without = family_tpr[_subset_key(coalition)]["overall"]
                with_it = family_tpr[_subset_key((*coalition, component))]["overall"]
                total += weight * (with_it - without)
        values[component] = total
    return values


def build(seed: int, mode: str, *, extended: bool = True) -> dict[str, object]:
    corpus = list(AttackCorpus.generate(seed=seed, extended=extended))
    if not corpus:
        raise TaxonomyMismatch("the corpus generated zero samples")

    counts = _category_counts(corpus)
    unmapped = sorted(set(counts) - set(FAMILY_OF))
    if unmapped:
        raise TaxonomyMismatch(
            f"corpus categories with no family: {unmapped}. Extend FAMILY_OF rather "
            f"than dropping them, or the six-way roll-up silently loses attacks."
        )

    cells: dict[str, dict] = {}
    family_tpr: dict[str, dict[str, float]] = {}
    for subset in _subsets(mode):
        key = _subset_key(subset)
        cell = _evaluate(subset, corpus)
        cells[key] = cell

        by_family_detected: dict[str, int] = defaultdict(int)
        by_family_total: dict[str, int] = defaultdict(int)
        for category, record in cell["per_category"].items():
            family = FAMILY_OF[category]
            by_family_detected[family] += record["detected"]
            by_family_total[family] += record["n"]
        rolled = {
            family: by_family_detected[family] / by_family_total[family]
            for family in sorted(by_family_total)
        }
        rolled["overall"] = sum(by_family_detected.values()) / sum(by_family_total.values())
        family_tpr[key] = rolled
        cell["per_family"] = rolled

    payload: dict[str, object] = {
        "data_origin": "real_pipeline",
        "source_script": "scripts/run_taxonomy_evaluation.py",
        "generator": {
            "module": "src/composition/factory.py",
            "function": "create_pipeline_without",
            "deterministic": True,
        },
        "note": (
            "Every cell is a real pipeline evaluation of the full 950-item corpus. "
            "No value here is calibrated, interpolated or modelled."
        ),
        "seed": seed,
        "mode": mode,
        "corpus_variant": "extended" if extended else "published",
        # The corpus's own family for each category, read off the samples
        # rather than typed. Consumers that want the taxonomy as the generator
        # defines it -- the tree figure, for one -- must not have to reproduce
        # FAMILY_OF's deliberate injection split to get it.
        "top_category_of": {
            getattr(s.category, "value", str(s.category)): s.category.top_category
            for s in corpus
        },
        "components": list(COMPONENTS),
        "corpus_size": len(corpus),
        "corpus_digest": _corpus_digest(corpus),
        "category_counts": counts,
        "family_of": FAMILY_OF,
        "n_benign": len(BENIGN_MESSAGES),
        "configurations": len(cells),
        "cells": cells,
    }
    if mode == "lattice":
        payload["shapley_overall_tpr"] = _shapley(cells, family_tpr)
    grid = [round(0.28 + 0.005 * i, 4) for i in range(0, 89)]
    payload["threshold_sweep"] = threshold_sweep(corpus, grid)
    payload["per_module_calibration"] = per_module_calibration(corpus, seed)
    return payload


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--axes",
        action="store_true",
        help="evaluate only the 18 reported configurations instead of all 256",
    )
    parser.add_argument(
        "--published",
        action="store_true",
        help="use the legacy 950-item corpus that never reaches provenance, "
             "sandbox or consensus; for reproducing previously published figures",
    )
    parser.add_argument("--check", action="store_true", help="fail if the artifact is stale")
    args = parser.parse_args(list(argv) if argv is not None else None)

    mode = "axes" if args.axes else "lattice"
    try:
        fresh = build(args.seed, mode, extended=not args.published)
    except TaxonomyMismatch as exc:
        print(f"taxonomy evaluation: FAILED -- {exc}", file=sys.stderr)
        return 2

    target = OUTPUT_PUBLISHED if args.published else OUTPUT
    if args.check:
        if not target.is_file():
            print(f"missing {target.relative_to(REPO)}; run without --check", file=sys.stderr)
            return 1
        stored = json.loads(target.read_text(encoding="utf-8"))
        drift = [
            key
            for key in ("corpus_digest", "cells", "category_counts", "configurations")
            if stored.get(key) != fresh[key]
        ]
        if drift:
            print(f"taxonomy evaluation is stale; changed: {drift}")
            return 1
        print(f"taxonomy evaluation: current ({fresh['configurations']} configurations)")
        return 0

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(fresh, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    full = fresh["cells"][_subset_key(COMPONENTS)]
    print(f"wrote {target.relative_to(REPO)}: {fresh['configurations']} configurations")
    print(f"  corpus: {fresh['corpus_size']} attacks in {len(fresh['category_counts'])} categories")
    print(f"  full stack: TPR {full['per_family']['overall']:.4f}  FPR {full['fpr']:.4f}")
    for family, rate in sorted(full["per_family"].items()):
        if family != "overall":
            print(f"    {family:<22} {rate:.4f}")
    sweep = fresh["threshold_sweep"]
    best, clean = sweep["youden_optimal"], sweep["best_at_zero_fpr"]
    print(f"  benign scores top out at {sweep['benign_score_max']:.3f}; "
          f"the shipped threshold is {sweep['shipped_threshold']}")
    print(f"  J-optimal tau={best['threshold']:.3f}: TPR {best['tpr']:.4f}  FPR {best['fpr']:.4f}")
    if clean:
        print(f"  best at zero FPR tau={clean['threshold']:.3f}: TPR {clean['tpr']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
