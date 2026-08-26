#!/usr/bin/env python3
"""Every percentage in a conclusion must exist in an artifact.

The series ledger gates the quantities the three papers share, and Part 2's
claim registry binds 171 numbers in its prose. Neither reaches a conclusion
that restates a measurement in its own words: a sentence reading "the gap
between Level 3 (44.8%) and Level 5 (96%)" matches no ledger pattern and no
registry regex, so it survived every gate while naming a rate the pipeline had
not produced for weeks.

Six such numbers were sitting in the three conclusions when this check was
written --- a retired multi-seed mean in two papers, a confidence interval from
before the arm was re-run, an ablation TPR from before the corpus changed, and
a Bayesian HDI computed against a rate that no longer exists.

It reads every decimal percentage in each conclusion and requires it to match,
to one decimal place, a quantity the series actually derives: a ledger variable
or a claim-registry value, taken as a fraction or as a percentage. The first
version of this check compared against every number in every artifact instead,
and could not fail --- twenty-five JSON files hold thousands of numbers, so a
fabricated 77.7 per cent matched one by coincidence and passed. The reference
set is the few dozen numbers the series is willing to state, which is small
enough that a coincidental match is unlikely rather than certain.

    python3 scripts/check_conclusion_numbers.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

#: The conclusion of each paper, which is where a reader looks for the headline
#: and where a stale number does the most damage.
CONCLUSIONS = (
    "cogsec_multiagent_1_theory/manuscript/09_conclusion.md",
    "cogsec_multiagent_2_computational/manuscript/07_conclusion.md",
    "cogsec_multiagent_3_practical/manuscript/08_conclusion.md",
)

#: Part 2 owns the artifacts the whole series cites.
DATA_DIR = REPO / "cogsec_multiagent_2_computational" / "output" / "data"

#: Percentages that are not measurements: design-level ceilings the papers
#: label as such, and round numbers used as thresholds or illustrations. Each
#: needs a reason, and the reason is checked by a human, not by this file.
EXEMPT: dict[float, str] = {
    96.0: "parametric design ceiling, labelled parametric wherever it appears",
    100.0: "the top of the scale",
}

_PERCENT = re.compile(r"(\d+\.\d)\\?%")


def _headline_values() -> tuple[dict[float, str], list[str]]:
    """The quantities the series actually reports, to one decimal.

    Not every number in every artifact. That was the first design and it could
    not fail: twenty-five JSON files hold thousands of numbers between them, so
    a fabricated 77.7 per cent matched something by coincidence and it passed.
    A gate that cannot fail is worse than no gate, because it also stops anyone
    from writing the one that would work.

    The set here is the ledger's derived variables plus the claim registry's
    derived values --- the numbers the series is willing to state, which is a
    few dozen rather than a few thousand, and small enough that a coincidental
    match is unlikely rather than certain.
    """
    values: dict[float, str] = {}
    unevaluated: list[str] = []

    sys.path.insert(0, str(REPO / "scripts"))
    import series_ledger

    for variable in series_ledger.LEDGER:
        try:
            derived = float(variable.deriver())
        except Exception as exc:  # noqa: BLE001
            # Not skipped. A reference value that cannot be derived shrinks the
            # set this gate judges against, and a smaller set turns a stale
            # number into an accusation against the manuscript or -- worse --
            # lets one through by removing the variable that would have
            # explained it. Under a bare interpreter with no numpy the set fell
            # from 108 values to 104 and the gate reported two "unbacked"
            # numbers that were in fact derived. It is reported, not absorbed.
            unevaluated.append(f"ledger: {variable.id} ({type(exc).__name__}: {exc})")
            continue
        for candidate in (round(derived, 1), round(derived * 100, 1)):
            values.setdefault(candidate, f"ledger: {variable.id}")

    registry_src = REPO / "cogsec_multiagent_2_computational" / "src"
    sys.path.insert(0, str(registry_src))
    try:
        from manuscript.claim_registry import CLAIMS, GroundTruth

        truth = GroundTruth(DATA_DIR)
        for claim in CLAIMS:
            try:
                derived = float(claim.deriver(truth))
            except Exception as exc:  # noqa: BLE001
                unevaluated.append(f"claim: {claim.id} ({type(exc).__name__}: {exc})")
                continue
            for candidate in (round(derived, 1), round(derived * 100, 1)):
                values.setdefault(candidate, f"claim: {claim.id}")
    except ImportError as exc:
        unevaluated.append(f"claim registry unimportable ({exc})")

    return values, unevaluated


def main() -> int:
    known, unevaluated = _headline_values()
    if unevaluated:
        print(
            f"{len(unevaluated)} reference value(s) could not be derived, so the "
            f"set this gate judges against is incomplete and its verdict on the "
            f"conclusions would not mean what it says:",
            file=sys.stderr,
        )
        for item in unevaluated:
            print(f"  {item}", file=sys.stderr)
        return 2
    if not known:
        print(
            "no headline values could be derived; the ledger or the registry is "
            "broken and this check would be vacuous",
            file=sys.stderr,
        )
        return 2

    problems: list[str] = []
    checked = 0
    for name in CONCLUSIONS:
        path = REPO / name
        if not path.is_file():
            problems.append(f"{name}: missing")
            continue
        text = path.read_text(encoding="utf-8")
        for value in sorted({float(v) for v in _PERCENT.findall(text)}):
            checked += 1
            if value in EXEMPT or value in known:
                continue
            problems.append(
                f"{name}: {value}\\% is not a quantity the ledger or the claim "
                f"registry derives"
            )

    if checked < 5:
        print(
            f"only {checked} percentages found across the three conclusions; the "
            f"pattern is probably broken, which would make this check pass "
            f"without checking anything",
            file=sys.stderr,
        )
        return 2

    print(
        f"conclusion numbers: {checked} checked across {len(CONCLUSIONS)} papers, "
        f"against {len(known)} derived headline values"
    )
    for problem in problems:
        print(f"  {problem}")
    if problems:
        print(f"{len(problems)} unbacked number(s) in a conclusion")
        return 1
    print("every conclusion percentage resolves to a derived quantity")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
