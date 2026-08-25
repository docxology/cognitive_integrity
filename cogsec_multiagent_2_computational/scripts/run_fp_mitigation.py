#!/usr/bin/env python3
"""What each false-positive mitigation actually costs and saves.

Two tables in Part 2's supplement describe false positives: one attributing
them to five root causes with frequencies summing to 100%, and one reporting
the measured effectiveness of six mitigation strategies. Neither was measured,
and none of the six strategies existed.

This measures both.

Root causes come from the benign corpus's own construction. Every benign sample
records the ``TRIGGER_SURFACE`` terms it contains -- the detector vocabulary,
placed in innocent sentences on purpose -- so a false positive can be
attributed to whether the message carried such a term, and to which modules
fired. That is a real taxonomy with a real denominator, rather than five
percentages that sum to a suspiciously round number.

Mitigations come from ``composition.mitigations``. Each is a post-filter over
the pipeline's per-module results, so the deltas below are what can be
recovered without retraining anything. Five of the supplement's six are
implemented; "Incremental Learning" is not, because there is no model in this
framework that updates on feedback, and implementing something adjacent under
that name would be the original defect with working code behind it.

    python3 scripts/run_fp_mitigation.py
    python3 scripts/run_fp_mitigation.py --check
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from attacks.corpus import AttackCorpus  # noqa: E402
from composition.factory import MODULE_REGISTRY  # noqa: E402
from composition.mitigations import MITIGATIONS, Verdict  # noqa: E402
from evaluation.benign_corpus import BenignCorpus  # noqa: E402

OUTPUT = REPO / "output" / "data" / "fp_mitigation.json"


def _verdicts(modules: dict, messages: list[str]) -> list[Verdict]:
    """Build a verdict per message with *every* module's result present.

    Not by calling the series pipeline. ``SeriesPipeline`` short-circuits on
    the first module that flags, so ``module_results`` holds only the modules
    that ran, and ``n_flagging`` is 1 for every flagged message by
    construction. A confirmation cascade evaluated on that basis reports
    -100% true positives and looks like a catastrophic strategy when what it
    actually met was an artefact of the evaluation.

    Each module is therefore run independently and the flag is the maximum
    rule the pipeline itself applies -- same decision, complete evidence.
    """
    out = []
    for message in messages:
        results = [module.evaluate(message) for module in modules.values()]
        out.append(
            Verdict(
                flagged=any(r.detected for r in results),
                score=max((r.score for r in results), default=0.0),
                module_results=tuple(results),
            )
        )
    return out


def build(seed: int = 42) -> dict[str, object]:
    attacks = list(AttackCorpus.generate(seed=seed))
    benign = list(BenignCorpus.generate())
    modules = {name: cls() for name, cls in MODULE_REGISTRY.items()}

    attack_verdicts = _verdicts(modules, [s.payload for s in attacks])
    benign_verdicts = _verdicts(modules, [b.text for b in benign])

    # --- root causes of the false positives the pipeline actually produces ---
    causes: Counter[str] = Counter()
    by_module: Counter[str] = Counter()
    by_category: Counter[str] = Counter()
    false_positives = 0
    for sample, verdict in zip(benign, benign_verdicts):
        if not verdict.flagged:
            continue
        false_positives += 1
        by_category[sample.category] += 1
        for result in verdict.module_results:
            if result.detected:
                by_module[result.module_name] += 1
        if sample.trigger_terms:
            causes[
                "attack_adjacent_vocabulary"
                if verdict.n_flagging == 1
                else "attack_adjacent_vocabulary_multi_module"
            ] += 1
        else:
            causes["no_trigger_term_present"] += 1

    # --- what each mitigation costs and saves ---
    baseline_tpr = sum(v.flagged for v in attack_verdicts) / len(attack_verdicts)
    baseline_fpr = sum(v.flagged for v in benign_verdicts) / len(benign_verdicts)

    strategies: dict[str, dict[str, float]] = {}
    for name, mitigation in MITIGATIONS.items():
        tpr = sum(mitigation(attack_verdicts)) / len(attack_verdicts)
        fpr = sum(mitigation(benign_verdicts)) / len(benign_verdicts)
        strategies[name] = {
            "tpr": tpr,
            "fpr": fpr,
            "youden_j": tpr - fpr,
            "delta_tpr": tpr - baseline_tpr,
            "delta_fpr": fpr - baseline_fpr,
            "relative_fpr_reduction": (
                (baseline_fpr - fpr) / baseline_fpr if baseline_fpr > 0 else 0.0
            ),
        }

    return {
        "data_origin": "real_pipeline",
        "source_script": "scripts/run_fp_mitigation.py",
        "seed": seed,
        "n_attacks": len(attacks),
        "n_benign": len(benign),
        "baseline": {"tpr": baseline_tpr, "fpr": baseline_fpr},
        "false_positives": false_positives,
        "root_causes": dict(causes),
        "false_positives_by_module": dict(by_module),
        "false_positives_by_benign_category": dict(by_category),
        "strategies": strategies,
        "not_implemented": {
            "incremental_learning": (
                "requires a model that updates on labelled feedback; every "
                "module in this framework is a fixed scorer, so there is "
                "nothing to update"
            )
        },
        "note": (
            "Root causes are attributed from the benign corpus's own recorded "
            "trigger terms, so they partition the false positives rather than "
            "summing to a round number. temporal_smoothing depends on the order "
            "messages arrive in, which is a property of the strategy and not of "
            "this measurement."
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
        if stored.get("strategies") != fresh["strategies"]:
            print("fp mitigation study is stale")
            return 1
        print("fp mitigation study: current")
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(fresh, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(REPO)}")
    base = fresh["baseline"]
    print(f"  baseline TPR {base['tpr']:.3f}  FPR {base['fpr']:.3f}")
    print(f"  {'strategy':26s} {'TPR':>7s} {'FPR':>7s} {'dTPR':>7s} {'dFPR':>7s} {'J':>7s}")
    for name, row in fresh["strategies"].items():
        print(
            f"  {name:26s} {row['tpr']:7.3f} {row['fpr']:7.3f} "
            f"{row['delta_tpr']:+7.3f} {row['delta_fpr']:+7.3f} {row['youden_j']:+7.3f}"
        )
    print(f"  false positives: {fresh['false_positives']}  by cause: {fresh['root_causes']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
