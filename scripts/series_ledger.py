#!/usr/bin/env python3
"""The series ledger: every cross-paper number, derived from its artifact.

Why this exists
---------------
Part 2 already runs derive-then-verify on its own manuscript: ``injector.py``
writes measured values into the prose and ``claim_registry.py`` reads them back
out and re-derives them.  Parts 1 and 3 had neither.  Every number they quote
from Part 2 -- detection rates, corpus size, architecture counts, confidence
intervals, test counts -- was typed by hand, which is exactly how the parametric
ceiling came to be published as two different values in three papers that cite
each other.

This module is the single source of truth for those numbers.  Each
:class:`LedgerVariable` binds a name to a *deriver* that recomputes the value
from a shipped artifact under Part 2's ``output/data/``.  Nothing here stores a
number; every value is computed on demand from the evidence.

How it is used
--------------
``scripts/check_series_integrity.py`` imports :data:`LEDGER` and, for every
variable that declares a prose ``pattern``, checks that each in-context
occurrence across all three manuscripts equals the derived value.  A stated
number that disagrees with its artifact is a failure; so is a pattern that stops
matching, because a guard that silently matches nothing is indistinguishable
from a clean run.

    python3 scripts/series_ledger.py              # print every derived value
    python3 scripts/series_ledger.py --json       # machine-readable
    python3 scripts/series_ledger.py --coverage   # how much of the prose is managed

Adding a variable
-----------------
Give it a ``deriver`` that reads an artifact, and -- if the value appears in
prose -- a ``pattern`` with exactly one capturing group plus ``require`` context
keywords tight enough that it cannot collide with a neighbouring quantity of the
same shape.  If you cannot write a safe pattern, still add the variable with
``pattern=None``: it will be derived and reported, just not gated.
"""

from __future__ import annotations

import argparse
import ast
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent

PARTS: dict[str, str] = {
    "1": "cogsec_multiagent_1_theory",
    "2": "cogsec_multiagent_2_computational",
    "3": "cogsec_multiagent_3_practical",
}

DATA_DIR = REPO_ROOT / PARTS["2"] / "output" / "data"

#: pandoc ``--``, a literal en/em dash, or a plain hyphen between two numbers.
DASH = r"(?:--|–|—|-)"

#: Two-sided 95% normal quantile, matching Part 2's injector.
Z95 = 1.959963984540054


class MissingArtifact(RuntimeError):
    """Raised when a variable's backing artifact is absent or unusable."""


_CACHE: dict[str, object] = {}


def artifact(name: str) -> object:
    """Load a shipped artifact, once per process."""
    if name not in _CACHE:
        path = DATA_DIR / name
        if not path.is_file():
            raise MissingArtifact(f"{path.relative_to(REPO_ROOT)} is missing")
        try:
            _CACHE[name] = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:  # pragma: no cover - corrupt artifact
            raise MissingArtifact(f"{name} is not valid JSON: {exc}") from exc
    return _CACHE[name]


def _rows(name: str) -> list[dict]:
    data = artifact(name)
    if not isinstance(data, list) or not data:
        raise MissingArtifact(f"{name} holds no rows")
    return [r for r in data if isinstance(r, dict)]


def _obj(name: str) -> dict:
    data = artifact(name)
    if not isinstance(data, dict):
        raise MissingArtifact(f"{name} is not an object")
    return data


# ---------------------------------------------------------------------------
# Derivers
# ---------------------------------------------------------------------------


def _parametric() -> list[dict]:
    return _rows("full_evaluation_results.json")


def parametric_ceiling_low() -> float:
    return min(float(r["detection_rate"]) for r in _parametric()) * 100.0


def parametric_ceiling_high() -> float:
    return max(float(r["detection_rate"]) for r in _parametric()) * 100.0


def direct_injection_low() -> float:
    rates = [float(r["detection_rate"]) for r in _parametric()
             if r.get("attack_category") == "direct_injection"]
    if not rates:
        raise MissingArtifact("no direct_injection rows in the parametric artifact")
    return min(rates) * 100.0


def direct_injection_high() -> float:
    rates = [float(r["detection_rate"]) for r in _parametric()
             if r.get("attack_category") == "direct_injection"]
    if not rates:
        raise MissingArtifact("no direct_injection rows in the parametric artifact")
    return max(rates) * 100.0


def near(*words: str, chars: int = 50, unless: tuple[str, ...] = ()) -> "Callable[[re.Match[str], str], bool]":
    """A guard requiring one of ``words`` within ``chars`` of the match.

    ``require`` uses a wide window so a quantity can be recognised from a
    sentence's general subject.  That is too coarse when two quantities of the
    same shape share one sentence -- "the full CIF stack achieved a 96--100%
    ceiling, with direct injection at 99--100%" puts both subjects in both
    windows.  Proximity is what actually separates them, and ``unless`` handles
    the case where even the tight window still catches the neighbour.
    """
    lowered = tuple(w.lower() for w in words)
    blocked = tuple(w.lower() for w in unless)

    def _guard(match: "re.Match[str]", line: str) -> bool:
        start = max(0, match.start() - chars)
        window = line[start : match.end() + chars].lower()
        if any(w in window for w in blocked):
            return False
        return any(w in window for w in lowered)

    return _guard


def _low_end_is_the_ceiling_floor(match: "re.Match[str]", line: str) -> bool:
    """True when this range's low end is the parametric ceiling floor.

    Distinguishes "the full CIF stack reached a 96--100% ceiling" from the
    "isolated layers were on the order of 60--70% detection" sitting in the same
    sentence, where the word "ceiling" is in context for both.
    """
    # The low end is inside the match, not before it: the pattern spans the
    # whole range and captures only its high end.
    low = re.match(r"\s*(\d{2})", match.group(0))
    if not low:
        return False
    try:
        return abs(float(low.group(1)) - parametric_ceiling_low()) < 0.001
    except (MissingArtifact, KeyError, TypeError, ValueError):
        return False


def architecture_count() -> float:
    return float(len({str(r["architecture"]) for r in _parametric()}))


def corpus_size() -> float:
    per_arch: dict[str, int] = {}
    for row in _parametric():
        per_arch[str(row["architecture"])] = per_arch.get(str(row["architecture"]), 0) + int(
            row["n_attacks"]
        )
    sizes = set(per_arch.values())
    if len(sizes) != 1:
        raise MissingArtifact(f"architectures disagree on corpus size: {per_arch}")
    return float(sizes.pop())


def parametric_instances() -> float:
    return float(sum(int(r["n_attacks"]) for r in _parametric()))


def _multiseed() -> dict:
    return _obj("multi_seed_results.json")


def multiseed_mean() -> float:
    return float(_multiseed()["tpr_mean"]) * 100.0


def multiseed_fpr() -> float:
    return float(_multiseed()["fpr_mean"]) * 100.0


def multiseed_cv() -> float:
    return float(_multiseed()["overall_cv"])


def multiseed_seeds() -> float:
    return float(_multiseed()["n_seeds"])


def _ablation() -> dict:
    return _obj("ablation_results.json")


def ablation_full_tpr() -> float:
    return float(_ablation()["full_pipeline"]["tpr"]) * 100.0


def ablation_corpus_size() -> float:
    """Recover the denominator from the measurement resolution.

    The artifact records rates, not counts.  With an n-sample corpus every
    delta is an integer multiple of 1/n, so the smallest non-zero delta *is*
    1/n.  (Deriving it from the full-pipeline TPR alone would give 49, because
    12/98 reduces to 6/49; the deltas pin the true resolution.)
    """
    deltas = [abs(v) for v in _removal().values() if abs(v) > 1e-12]
    if not deltas:
        raise MissingArtifact("no non-zero component-removal deltas to resolve against")
    n = round(1.0 / min(deltas))
    if not 1 < n < 100_000 or abs(min(deltas) * n - 1.0) > 1e-6:
        raise MissingArtifact(f"delta resolution {min(deltas)!r} implies no clean denominator")
    return float(n)


def _removal() -> dict[str, float]:
    return {r["removed"]: float(r["delta_tpr"]) for r in _ablation()["component_removal"]}


def ablation_detection_delta() -> float:
    return abs(_removal()["detection"])


def ablation_trust_delta() -> float:
    return abs(_removal()["trust_calculus"])


def ablation_tied_delta() -> float:
    """The three-way tie behind Trust Calculus; raises if they stop being tied."""
    tied = {_removal()[k] for k in ("firewall", "invariants", "tripwire")}
    if len(tied) != 1:
        raise MissingArtifact(f"firewall/invariants/tripwire are no longer tied: {tied}")
    return abs(tied.pop())


def top_synergy() -> float:
    return float(_ablation()["top_synergies"][0]["synergy"])


def top_synergy_tie_count() -> float:
    best = float(_ablation()["top_synergies"][0]["synergy"])
    return float(sum(1 for s in _ablation()["top_synergies"] if float(s["synergy"]) == best))


def _colony_scenario(fragment: str) -> dict:
    for scenario in _obj("colony_results.json")["scenarios"]:
        name = str(scenario.get("scenario") or scenario.get("name") or "")
        if fragment in name.lower().replace("_", " "):
            return scenario
    raise MissingArtifact(f"no colony scenario matching {fragment!r}")


def colony_emergent_dr() -> float:
    return float(_colony_scenario("emergent")["detection_rate_mean"]) * 100.0


def colony_emergent_fpr() -> float:
    return float(_colony_scenario("emergent")["false_positive_rate_mean"]) * 100.0


def _crossval() -> dict:
    return _obj("cross_validation_results.json")


def crossval_folds() -> float:
    return float(_crossval()["k"])


def crossval_mean_tpr() -> float:
    return float(_crossval()["mean_tpr"]) * 100.0


def scalability_max_agents() -> float:
    track = _obj("scalability_results.json")["framework_track"]
    return float(max(int(r["n_agents"]) for r in track))


def redteam_attacks_generated() -> float:
    return float(_obj("redteam_evaluation_results.json")["n_attacks_generated"])


def at_baseline_dr() -> float:
    return float(_obj("adversarial_training_results.json")["baseline_dr"]) * 100.0


def at_final_hardened_dr() -> float:
    return float(_obj("adversarial_training_results.json")["final_hardened_dr"]) * 100.0


def at_total_delta() -> float:
    return float(_obj("adversarial_training_results.json")["total_delta_dr"]) * 100.0


def at_rounds() -> float:
    return float(_obj("adversarial_training_results.json")["n_rounds"])


def part2_test_count() -> float:
    """Tests in Part 2's suite, from the collected inventory.

    Quoted by Part 3, and typed by hand until now: it was published as 2,283,
    then 3,308, then 3,369, each correct on the day it was written. Collection
    counts rather than pass counts, because collection is deterministic and a
    pass count depends on the environment a given run happened to have.
    """
    return float(_obj("test_inventory.json")["per_part"]["cogsec_multiagent_2_computational"])


def series_test_count() -> float:
    """Every test in the series, including the program-level suites."""
    return float(_obj("test_inventory.json")["total"])


def gap_low() -> float:
    """Parametric floor minus the multi-seed mean: the narrow end of the gap."""
    return parametric_ceiling_low() - multiseed_mean()


def gap_high() -> float:
    """Parametric ceiling minus the ablation TPR: the wide end."""
    return parametric_ceiling_high() - ablation_full_tpr()


def ablation_series_prediction() -> float:
    """Series-composition prediction from the solo mechanism rates: 1 - prod(1 - r_i)."""
    data = _obj("ablation_results.json")
    synergies = data.get("top_synergies") or []
    solo: dict[str, float] = {}
    for pair in synergies:
        for side in ("a", "b"):
            name, rate = pair.get(side), pair.get(f"tpr_{side}")
            if name is None or rate is None:
                continue
            solo[name] = float(rate)
    if not solo:
        raise MissingArtifact("no solo mechanism rates in the ablation artifact")
    missed = 1.0
    for rate in solo.values():
        missed *= 1.0 - rate
    return (1.0 - missed) * 100.0


def domain_count() -> float:
    """Counted from Part 3's files, not typed: 09c..09l are the domain sections."""
    root = REPO_ROOT / PARTS["3"] / "manuscript"
    return float(len([p for p in root.glob("09[c-z]_*.md")]))


def _dataclass_default(part: str, relative: str, class_name: str, field: str) -> float:
    """Read a dataclass field's default straight out of the source.

    The firewall thresholds are the one pair of published numbers that live in
    Python rather than in a JSON artifact, and they are the pair the series got
    wrong: five prose sites stated the implementation default as 0.7 while
    ``FirewallConfig`` had shipped 0.8 since the fork with Part 1.  Parsing the
    source with :mod:`ast` rather than importing it keeps this deriver usable
    from the program root, which has no virtualenv of its own, and keeps a
    manuscript gate from executing the package it is auditing.
    """
    path = REPO_ROOT / PARTS[part] / relative
    if not path.is_file():
        raise MissingArtifact(f"{relative} is missing from Part {part}")
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if not (isinstance(node, ast.ClassDef) and node.name == class_name):
            continue
        for stmt in node.body:
            if (
                isinstance(stmt, ast.AnnAssign)
                and isinstance(stmt.target, ast.Name)
                and stmt.target.id == field
            ):
                if stmt.value is None:
                    raise MissingArtifact(
                        f"{class_name}.{field} has no default to publish"
                    )
                try:
                    return float(ast.literal_eval(stmt.value))
                except (ValueError, TypeError) as exc:
                    raise MissingArtifact(
                        f"{class_name}.{field} default is not a number: {exc}"
                    ) from exc
        raise MissingArtifact(f"{class_name} has no field {field!r}")
    raise MissingArtifact(f"{relative} defines no class {class_name!r}")


def firewall_tau1() -> float:
    """The operational reject threshold: Part 2's ``FirewallConfig`` default."""
    return _dataclass_default("2", "src/core/firewall.py", "FirewallConfig", "injection_threshold")


def firewall_tau2() -> float:
    """The operational quarantine threshold, from the same dataclass."""
    return _dataclass_default("2", "src/core/firewall.py", "FirewallConfig", "suspicious_threshold")


def firewall_tau1_reference() -> float:
    """Part 1's deliberately different reference-implementation default."""
    return _dataclass_default("1", "src/firewall.py", "FirewallConfig", "injection_threshold")


# ---------------------------------------------------------------------------
# Variable registry
# ---------------------------------------------------------------------------

#: Evaluation arms that share a numeric shape with the parametric ceiling.
OTHER_ARMS = (
    "llm-backed",
    "llm validation",
    "llm-backed evaluation",
    "colony",
    "gemma",
    "hdi",
    "evaluation modes",
    "across evaluation",
    "variation across",
)

CONTEXT_WINDOW = 110


@dataclass(frozen=True)
class LedgerVariable:
    """One number the series quotes, bound to the computation that produces it.

    ``pattern`` is optional.  A variable with no pattern is still derived and
    reported -- it just is not gated, because no regex could distinguish it from
    a neighbouring quantity of the same shape without producing false positives.
    A noisy gate is worse than an absent one; it gets ignored, and then so does
    the real failure sitting next to it.
    """

    id: str
    description: str
    artifact: str
    deriver: Callable[[], float]
    unit: str
    pattern: re.Pattern[str] | None = None
    require: tuple[str, ...] = ()
    exclude: tuple[str, ...] = ()
    parts: tuple[str, ...] = ("1", "2", "3")
    tolerance: float = 0.001
    min_occurrences: int = 1
    #: When a table row or sentence carries several values of the same shape --
    #: a scenario's detection rate immediately followed by its false-positive
    #: rate, say -- only the first in-context match is this quantity. Context
    #: keywords cannot separate them: they share the row.
    first_only: bool = False
    #: An extra structural test on a candidate match, for quantities that
    #: keywords cannot isolate. The high end of the ceiling range is the case
    #: that forced this: a sentence can carry both "60--70% for isolated
    #: layers" and "96--100% ceiling", and "ceiling" is in context for both.
    #: What separates them is that only one has the ceiling floor as its low
    #: end, which is a property of the match, not of the surrounding words.
    guard: Callable[[re.Match[str], str], bool] | None = None

    def __post_init__(self) -> None:
        if self.pattern is not None:
            if self.pattern.groups != 1:
                raise ValueError(
                    f"{self.id}: pattern needs exactly one capturing group, "
                    f"has {self.pattern.groups}"
                )
            if not self.require:
                raise ValueError(
                    f"{self.id}: a gated pattern must declare context keywords, or it "
                    f"will collide with unrelated numbers of the same shape"
                )

    def in_scope(self, line: str, match: re.Match[str]) -> bool:
        start = max(0, match.start() - CONTEXT_WINDOW)
        window = line[start : match.end() + CONTEXT_WINDOW].lower()
        if any(token in window for token in self.exclude):
            return False
        if not any(token in window for token in self.require):
            return False
        if self.guard is not None and not self.guard(match, line):
            return False
        return True

    def value(self) -> float:
        return float(self.deriver())


def _pct(digits: int = 1) -> re.Pattern[str]:
    """A percentage with the given decimal places, optionally bolded."""
    frac = rf"\.\d{{{digits}}}" if digits else ""
    return re.compile(rf"\*{{0,2}}(\d{{1,3}}{frac})\s*\\?%")


LEDGER: tuple[LedgerVariable, ...] = (
    LedgerVariable(
        id="parametric_ceiling_low",
        description="Lowest per-cell parametric detection rate: the floor of the design ceiling.",
        artifact="full_evaluation_results.json",
        deriver=parametric_ceiling_low,
        unit="percent",
        pattern=re.compile(rf"(\d{{2}})\s*{DASH}\s*100\s*\\?%"),
        require=("parametric", "design ceiling", "design-level", "coverage ceiling", "design target"),
        exclude=OTHER_ARMS,
        guard=near("ceiling", "design-level", "design target",
                   unless=("direct injection", "direct-injection")),
        min_occurrences=2,
    ),
    LedgerVariable(
        id="parametric_ceiling_high",
        description="Highest per-cell parametric detection rate.",
        artifact="full_evaluation_results.json",
        deriver=parametric_ceiling_high,
        unit="percent",
        # Capturing a literal 100 would mean the check can only ever match text
        # that is already right: a wrong high end simply would not match, and the
        # quantity would look absent rather than wrong.
        pattern=re.compile(rf"\d{{2}}\s*{DASH}\s*(\d{{2,3}})\s*\\?%"),
        require=("parametric", "design ceiling", "design-level", "coverage ceiling", "design target"),
        exclude=OTHER_ARMS,
        guard=_low_end_is_the_ceiling_floor,
        min_occurrences=2,
    ),
    LedgerVariable(
        id="direct_injection_range_low",
        description="Lowest parametric detection rate on direct injection, across architectures.",
        artifact="full_evaluation_results.json",
        deriver=direct_injection_low,
        unit="percent",
        pattern=re.compile(rf"(\d{{2}})\s*{DASH}\s*\d{{2,3}}\s*\\?%"),
        require=("direct-injection", "direct injection"),
        exclude=OTHER_ARMS,
        guard=near("direct injection", "direct-injection"),
        # A sentence may pair this range with another category's range of the
        # same shape ("99--100% against direct injection and 96--100% against
        # impersonation"); direct injection is the one stated first.
        first_only=True,
    ),
    LedgerVariable(
        id="parametric_ceiling_low_bare",
        description="The ceiling floor quoted as a single number rather than a range.",
        artifact="full_evaluation_results.json",
        deriver=parametric_ceiling_low,
        unit="percent",
        pattern=re.compile(rf"(?<![\d\-–—])(\d{{2}})\s*\\?%(?!\s*{DASH}\s*\d)"),
        require=("design-level ceiling", "achievable ceiling", "design ceiling"),
        exclude=OTHER_ARMS,
    ),
    LedgerVariable(
        id="attack_corpus_size",
        description="Attacks per architecture in the parametric sweep.",
        artifact="full_evaluation_results.json",
        deriver=corpus_size,
        unit="count",
        pattern=re.compile(rf"(\d{{3}})\s*{DASH}?\s*attack\b(?=[- ]?(?:corpus|set)\b)"),
        require=("corpus", "set"),
        exclude=("ablation",),
        min_occurrences=2,
    ),
    LedgerVariable(
        id="parametric_instances",
        description="Total parametric evaluation instances (corpus x architectures).",
        artifact="full_evaluation_results.json",
        deriver=parametric_instances,
        unit="count",
        pattern=re.compile(r"\$N\s*=\s*(\d\{,\}\d{3})\$"),
        require=("parametric", "simulation"),
    ),
    LedgerVariable(
        id="architecture_count",
        description="Distinct architectures in the parametric sweep.",
        artifact="full_evaluation_results.json",
        deriver=architecture_count,
        unit="count",
        pattern=re.compile(
            r"\b(four|five|six|seven|eight|\d+)\s+production\s+multiagent\s+"
            r"(?:architectures|systems|topologies)"
        ),
        require=("production",),
        min_occurrences=2,
    ),
    LedgerVariable(
        id="multiseed_mean",
        description="30-seed pipeline mean detection rate.",
        artifact="multi_seed_results.json",
        deriver=multiseed_mean,
        unit="percent",
        pattern=re.compile(r"mean(?:\s+detection\s+rate)?\s+of\s+\*{0,2}(\d{2}\.\d)\s*\\?%"),
        require=("seed",),
        tolerance=0.06,
    ),
    LedgerVariable(
        id="multiseed_fpr",
        description="30-seed pipeline mean false-positive rate.",
        artifact="multi_seed_results.json",
        deriver=multiseed_fpr,
        unit="percent",
        pattern=re.compile(r"(\d{2}\.\d)\s*\\?%\s+false[- ]positive rate"),
        require=("seed", "multi-seed", "pipeline"),
        tolerance=0.06,
    ),
    LedgerVariable(
        id="multiseed_seeds",
        description="Number of seeds in the multi-seed arm.",
        artifact="multi_seed_results.json",
        deriver=multiseed_seeds,
        unit="count",
        pattern=re.compile(r"across\s+(\d{2})\s+(?:random\s+)?seeds"),
        require=("seed",),
        min_occurrences=2,
    ),
    LedgerVariable(
        id="ablation_full_tpr",
        description="Full-pipeline TPR on the ablation corpus.",
        artifact="ablation_results.json",
        deriver=ablation_full_tpr,
        unit="percent",
        pattern=re.compile(r"against a measured\s+(\d+\.\d)\\%"),
        require=("measured",),
        parts=("2",),
        tolerance=0.05,
    ),
    LedgerVariable(
        id="ablation_series_prediction",
        description=(
            "What the series composition rule 1 - prod(1 - r_i) predicts from the solo "
            "mechanism rates the ablation records. The detection-performance figure "
            "compares it against the measured full-pipeline TPR; the two agreeing to "
            "within half a point is the sharpest test of the composition algebra in the "
            "series, and it is only a test while both numbers come from the artifact."
        ),
        artifact="ablation_results.json",
        deriver=ablation_series_prediction,
        unit="percent",
        pattern=re.compile(r"predicts\s+(\d+\.\d)\\%"),
        require=("composition", "predicts"),
        parts=("2",),
        tolerance=0.05,
    ),
    LedgerVariable(
        id="ablation_corpus_size",
        description="Ablation corpus size, recovered from the measurement resolution.",
        artifact="ablation_results.json",
        deriver=ablation_corpus_size,
        unit="count",
        pattern=re.compile(r"(\d{2,3})\s*-?\s*attack\s+ablation\s+(?:corpus|subsample)"),
        require=("ablation",),
        min_occurrences=2,
    ),
    LedgerVariable(
        id="ablation_detection_delta",
        description="Marginal TPR lost when the Detection module is removed.",
        artifact="ablation_results.json",
        deriver=ablation_detection_delta,
        unit="fraction",
        pattern=None,
    ),
    LedgerVariable(
        id="ablation_trust_delta",
        description="Marginal TPR lost when the Trust Calculus is removed.",
        artifact="ablation_results.json",
        deriver=ablation_trust_delta,
        unit="fraction",
        pattern=None,
    ),
    LedgerVariable(
        id="ablation_tied_delta",
        description="The three-way tie (firewall / invariants / tripwire) behind Trust Calculus.",
        artifact="ablation_results.json",
        deriver=ablation_tied_delta,
        unit="fraction",
        pattern=None,
    ),
    LedgerVariable(
        id="top_synergy",
        description="Highest pairwise synergy beyond additive prediction.",
        artifact="ablation_results.json",
        deriver=top_synergy,
        unit="fraction",
        pattern=None,
    ),
    LedgerVariable(
        id="top_synergy_tie_count",
        description="How many pairs share the top synergy. Two means no single winner exists.",
        artifact="ablation_results.json",
        deriver=top_synergy_tie_count,
        unit="count",
        pattern=None,
    ),
    LedgerVariable(
        id="colony_emergent_dr",
        description="Emergent-misalignment detection rate, the weakest colony scenario.",
        artifact="colony_results.json",
        deriver=colony_emergent_dr,
        unit="percent",
        pattern=re.compile(r"(\d{2}\.\d)\s*\\?%"),
        require=("emergent misalignment", "emergent-misalignment"),
        # The same sentence and the same table row also carry this scenario's
        # false-positive rate, which has the identical shape.
        exclude=("false positive", "false-positive", "fpr"),
        first_only=True,
        tolerance=0.06,
    ),
    LedgerVariable(
        id="colony_emergent_fpr",
        description="Emergent-misalignment false-positive rate.",
        artifact="colony_results.json",
        deriver=colony_emergent_fpr,
        unit="percent",
        pattern=None,
    ),
    LedgerVariable(
        id="crossval_folds",
        description="Cross-validation fold count.",
        artifact="cross_validation_results.json",
        deriver=crossval_folds,
        unit="count",
        # No manuscript writes "N-fold", so a gated pattern here could only ever
        # match nothing. Derived and reported, not gated.
        pattern=None,
    ),
    LedgerVariable(
        id="crossval_mean_tpr",
        description="Mean TPR across cross-validation folds.",
        artifact="cross_validation_results.json",
        deriver=crossval_mean_tpr,
        unit="percent",
        pattern=None,
    ),
    LedgerVariable(
        id="scalability_max_agents",
        description="Largest agent count in the measured scalability sweep.",
        artifact="scalability_results.json",
        deriver=scalability_max_agents,
        unit="count",
        pattern=None,
    ),
    LedgerVariable(
        id="redteam_attacks_generated",
        description="Attacks emitted by the red-team generator.",
        artifact="redteam_evaluation_results.json",
        deriver=redteam_attacks_generated,
        unit="count",
        pattern=None,
    ),
    LedgerVariable(
        id="at_baseline_dr",
        description="Pre-adversarial-training baseline detection rate.",
        artifact="adversarial_training_results.json",
        deriver=at_baseline_dr,
        unit="percent",
        pattern=re.compile(r"pre-AT baseline \((\d{2}\.\d)\\?%\)"),
        require=("baseline",),
        parts=("2",),
        tolerance=0.06,
    ),
    LedgerVariable(
        id="at_final_hardened_dr",
        description="Detection rate after the final adversarial-training round.",
        artifact="adversarial_training_results.json",
        deriver=at_final_hardened_dr,
        unit="percent",
        pattern=re.compile(r"(?:reaches|to) (\d{2}\.\d)\\?%"),
        require=("Round 5", "Round-5", "hardened"),
        parts=("2",),
        tolerance=0.06,
    ),
    LedgerVariable(
        id="at_total_delta",
        description="Cumulative adversarial-training gain over baseline.",
        artifact="adversarial_training_results.json",
        deriver=at_total_delta,
        unit="percent",
        pattern=re.compile(r"\+(\d{2}\.\d) ?pp"),
        require=("cumulative", "AT-Round"),
        parts=("2",),
        tolerance=0.06,
    ),
    LedgerVariable(
        id="at_rounds",
        description="Adversarial-training rounds run.",
        artifact="adversarial_training_results.json",
        deriver=at_rounds,
        unit="count",
        pattern=None,
    ),
    LedgerVariable(
        id="part2_test_count",
        description="Tests in Part 2's suite; quoted by Part 3 and previously hand-typed.",
        artifact="test_inventory.json",
        deriver=part2_test_count,
        unit="count",
        # Three thousand-separator spellings are in use across the tree:
        # a plain comma, pandoc's ``{,}``, and none at all.
        pattern=re.compile(r"\*{0,2}(\d[,]\d{3}|\d\{,\}\d{3}|\d{4})\*{0,2}\s+(?:passing\s+)?tests"),
        require=("test",),
    ),
    LedgerVariable(
        id="series_test_count",
        description="Every test across the three parts plus the program-level suites.",
        artifact="test_inventory.json",
        deriver=series_test_count,
        unit="count",
        pattern=None,
    ),
    LedgerVariable(
        id="gap_low",
        description="Narrow end of the ceiling-to-pipeline gap (derived, never typed).",
        artifact="(derived)",
        deriver=gap_low,
        unit="percent",
        pattern=re.compile(rf"(\d{{2}})\s*{DASH}\s*\d{{2}}\s+percentage[- ]point gap"),
        require=("gap",),
        tolerance=0.6,
    ),
    LedgerVariable(
        id="gap_high",
        description="Wide end of the ceiling-to-pipeline gap (derived, never typed).",
        artifact="(derived)",
        deriver=gap_high,
        unit="percent",
        pattern=re.compile(rf"\d{{2}}\s*{DASH}\s*(\d{{2}})\s+percentage[- ]point gap"),
        require=("gap",),
        tolerance=0.6,
    ),
    LedgerVariable(
        id="firewall_tau1",
        description=(
            "Reject threshold as shipped: FirewallConfig.injection_threshold. Five prose "
            "sites published 0.7 as the implementation default while the dataclass had "
            "held 0.8 since the fork with Part 1's reference implementation."
        ),
        artifact="cogsec_multiagent_2_computational/src/core/firewall.py",
        deriver=firewall_tau1,
        unit="threshold",
        pattern=re.compile(r"(?:\\tau_1\s*=\s*|tau_1:\s+)(\d\.\d+)"),
        # "operational default" is the phrase the papers now use wherever they
        # state the shipped value.  It is what separates this quantity from the
        # two neighbours that share its shape and cannot be told apart by the
        # symbol alone: S08's parametric optimum (also a tau_1, also written
        # "tau_1 = 0.7", but a sweep result rather than a default) and Part 3's
        # per-profile tuning, whose whole point is to differ from the default.
        require=("operational default",),
        parts=("2", "3"),
        min_occurrences=4,
    ),
    LedgerVariable(
        id="firewall_tau2",
        description="Quarantine threshold as shipped: FirewallConfig.suspicious_threshold.",
        artifact="cogsec_multiagent_2_computational/src/core/firewall.py",
        deriver=firewall_tau2,
        unit="threshold",
        pattern=re.compile(r"(?:\\tau_2\s*=\s*|tau_2:\s+)(\d\.\d+)"),
        require=("operational default",),
        parts=("2", "3"),
        min_occurrences=2,
    ),
    LedgerVariable(
        id="firewall_tau1_reference",
        description=(
            "Part 1's reference-implementation reject threshold. Deliberately different "
            "from Part 2's operational default; gated so the documented fork stays a "
            "fork rather than quietly becoming a contradiction."
        ),
        artifact="cogsec_multiagent_1_theory/src/firewall.py",
        deriver=firewall_tau1_reference,
        unit="threshold",
        pattern=re.compile(r"reference implementation deliberately uses (\d\.\d+)"),
        require=("reference implementation",),
        parts=("2",),
    ),
    LedgerVariable(
        id="domain_count",
        description="Applied domains, counted from Part 3's section files rather than typed.",
        artifact="(structural)",
        deriver=domain_count,
        unit="count",
        pattern=re.compile(r"\b(ten|nine|eleven|\d{2})\s+(?:critical\s+|operational\s+|high-stakes\s+)*domains"),
        require=("domain",),
        min_occurrences=2,
    ),
)

WORD_NUMBERS = {
    "one": 1.0, "two": 2.0, "three": 3.0, "four": 4.0, "five": 5.0,
    "six": 6.0, "seven": 7.0, "eight": 8.0, "nine": 9.0, "ten": 10.0,
    "eleven": 11.0, "twelve": 12.0,
}


def to_number(literal: str) -> float:
    text = literal.strip().replace(",", "").replace("{", "").replace("}", "")
    if text.lower() in WORD_NUMBERS:
        return WORD_NUMBERS[text.lower()]
    return float(text)


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def manuscript_files(part: str) -> list[Path]:
    root = REPO_ROOT / PARTS[part] / "manuscript"
    if not root.is_dir():
        return []
    return sorted(p for p in root.glob("*.md") if p.name != "preamble.md")


def derive_all() -> dict[str, object]:
    out: dict[str, object] = {}
    for var in LEDGER:
        try:
            out[var.id] = {
                "value": var.value(),
                "unit": var.unit,
                "artifact": var.artifact,
                "gated": var.pattern is not None,
                "description": var.description,
            }
        except (MissingArtifact, KeyError, IndexError, TypeError, ValueError) as exc:
            out[var.id] = {"error": f"{type(exc).__name__}: {exc}", "artifact": var.artifact}
    return out


def coverage_report() -> dict[str, object]:
    """How much of the prose's numeric surface the ledger actually manages."""
    gated = [v for v in LEDGER if v.pattern is not None]
    managed_sites = 0
    for var in gated:
        for part in var.parts:
            for path in manuscript_files(part):
                for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                    managed_sites += sum(
                        1 for m in var.pattern.finditer(line) if var.in_scope(line, m)
                    )
    total_numeric = 0
    numeric = re.compile(r"\d+(?:\.\d+)?\s*\\?%")
    for part in PARTS:
        for path in manuscript_files(part):
            total_numeric += len(numeric.findall(path.read_text(encoding="utf-8", errors="replace")))
    return {
        "variables": len(LEDGER),
        "gated_variables": len(gated),
        "managed_prose_sites": managed_sites,
        "percentage_literals_in_prose": total_numeric,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--coverage", action="store_true", help="report ledger coverage")
    args = parser.parse_args(list(argv) if argv is not None else None)

    values = derive_all()
    # A variable that fails to derive is a failure in every mode. Reporting it
    # in the JSON body while exiting 0 would let a machine consumer treat a
    # broken ledger as a healthy one, which is the shape of hollow green the
    # rest of this apparatus exists to prevent.
    underivable = sorted(k for k, v in values.items() if isinstance(v, dict) and "error" in v)

    if args.coverage:
        report = coverage_report()
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            for key, val in report.items():
                print(f"{key:<32} {val}")
        if underivable:
            print(f"underivable variables: {underivable}", file=sys.stderr)
        return 1 if underivable else 0

    if args.json:
        print(json.dumps(values, indent=2))
        if underivable:
            print(f"underivable variables: {underivable}", file=sys.stderr)
        return 1 if underivable else 0

    failed = 0
    for var in LEDGER:
        entry = values[var.id]
        gate = "gated" if var.pattern is not None else "     "
        if "error" in entry:
            failed += 1
            print(f"  {var.id:<28} {gate}  ERROR  {entry['error']}")
        else:
            print(f"  {var.id:<28} {gate}  {entry['value']:>12.4f}  {var.unit:<8} {var.artifact}")
    print("-" * 78)
    print(f"{len(LEDGER)} variables, {sum(1 for v in LEDGER if v.pattern)} gated, {failed} underivable")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
