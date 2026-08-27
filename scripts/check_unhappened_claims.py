#!/usr/bin/env python3
"""No sentence may report a human process this research did not carry out.

Part 2 shipped a methodology section describing eight security researchers over
a four-week red-team exercise, human review of every generated attack, an
inter-rater reliability of Cohen's kappa = 0.84, a sophistication-versus-success
correlation, a detection-rate-by-attack-age table, a 90-day coordinated
disclosure with four named framework vendors and their patch versions, an IRB
determination, and a tiered access process requiring an NDA. Its conclusion
thanked the eight researchers and the anonymous reviewers. None of it happened.
The corpus is one seeded call to five generator modules, the paper had never
been submitted anywhere, and the corpus it described as restricted is a pure
function of a published seed.

None of the existing checks could see it. The ledger gates quantities, the claim
registry covered 8 of 36 manuscript files, and neither has an opinion about a
sentence that reports an event. This one does: it looks for the vocabulary of
human process and external interaction, and requires every occurrence to be
registered with a reason.

The registry is deliberately awkward to add to. An entry is a promise that the
matched sentence is either about someone else's published work or is explicitly
framed as something not done, and each carries the reason in the file.

    python3 scripts/check_unhappened_claims.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

PARTS = (
    "cogsec_multiagent_1_theory",
    "cogsec_multiagent_2_computational",
    "cogsec_multiagent_3_practical",
)

#: Vocabulary that asserts a human process or an interaction with an outside
#: party. Each pattern is a claim a reader would take as a report of an event.
PATTERNS: dict[str, re.Pattern[str]] = {
    "participants": re.compile(
        # "recruitment" on its own is one of the colony scenarios, not a person
        # being recruited, so the pattern requires human context around it.
        r"\b(participants?\*{0,2}\s*[:(]"
        # A count in front of "researchers" is a headcount, not a reference to
        # the field: "8 security researchers" versus "researchers have shown".
        r"|\d+\s+(?:\w+\s+){0,2}researchers?\b"
        r"|recruited (?:participants?|volunteers?|subjects?)|volunteers?)\b",
        re.I,
    ),
    "acknowledgement-of-people": re.compile(
        r"\b(we|the authors?)\s+thank\b|\banonymous reviewers?\b|\breviewers?'?\s+feedback\b", re.I
    ),
    "annotation": re.compile(
        r"\b(inter-?(?:rater|annotator)|Cohen'?s?\s*\$?\\?kappa|independent (?:reviewers?|annotators?|labell?ers?)"
        r"|human (?:annotations?|labell?ing)|third reviewer)\b",
        re.I,
    ),
    "ethics-review": re.compile(
        r"\b(IRB|institutional review board|ethics (?:board|committee)|informed consent"
        r"|exempt from .{0,24}oversight)\b",
        re.I,
    ),
    "disclosure": re.compile(
        r"\b(\d+-day (?:disclosure|embargo)|embargo(?:ed|\s+period)|coordinated disclosure"
        r"|disclosure (?:timeline|agreements?)|reported to .{0,30}maintainers)\b",
        re.I,
    ),
    "gated-access": re.compile(
        r"\b(NDA\b|non-disclosure agreement|verified researchers|access (?:request|tier|control hierarchy)"
        r"|institutional (?:affiliation )?verification|data use agreement|usage tracking)\b",
        re.I,
    ),
    "field-study": re.compile(
        r"\b(we (?:interviewed|surveyed|contacted|deployed|piloted)|user stud(?:y|ies)"
        r"|field trial|pilot deployment|beta (?:test|users?)|in production at)\b",
        re.I,
    ),
    "pre-registration": re.compile(r"\bpre-?registered\b|\bpre-?registration\b", re.I),
    # Release history is a claim about the world too, and it hid in a place the
    # manuscript scan never reached: Part 2's config.yaml carried "v1.0
    # (2026-07-05): Initial public release" for a paper that had never been
    # deposited anywhere, and that file becomes the Zenodo record metadata.
    "release-history": re.compile(
        r"\b(initial (?:public )?release|previously (?:published|released|deposited)"
        r"|second edition|first edition|peer[- ]reviewed|accepted (?:at|for|to)"
        r"|published (?:in|at) the\b)",
        re.I,
    ),
}

#: Registered occurrences. Key is ``(relative path, pattern name)``; the value
#: is why that file is allowed to use that vocabulary. Registering a file
#: allows every occurrence in it, so the reason must cover them all.
ALLOWED: dict[tuple[str, str], str] = {
    (
        "cogsec_multiagent_2_computational/manuscript/03c_attack_ethics.md",
        "ethics-review",
    ): "states that no review was sought and none was required, which is the negative claim",
    (
        "cogsec_multiagent_2_computational/manuscript/03c_attack_ethics.md",
        "gated-access",
    ): "states that no access tier is operated and explains why one would be incoherent",
    (
        "cogsec_multiagent_2_computational/manuscript/03c_attack_ethics.md",
        "annotation",
    ): "states that there is no human annotation stage and therefore no agreement statistic",
    (
        "cogsec_multiagent_2_computational/manuscript/03c_attack_ethics.md",
        "disclosure",
    ): "states that no vulnerability was found and no coordinated disclosure was undertaken",
    (
        "cogsec_multiagent_2_computational/manuscript/06_discussion.md",
        "pre-registration",
    ): "states that there was no pre-registration, as a limitation",
    (
        "cogsec_multiagent_2_computational/manuscript/06_discussion.md",
        "annotation",
    ): "states that there was no external annotation, as a limitation",
    (
        "cogsec_multiagent_2_computational/manuscript/02b_configuration_parameters.md",
        "annotation",
    ): "a footnote distinguishing the corroboration count from Cohen's kappa, which is not reported",
    (
        "cogsec_multiagent_2_computational/manuscript/config.yaml",
        "release-history",
    ): "states that this paper has never been released before, which is the negative claim",
    (
        "cogsec_multiagent_1_theory/manuscript/config.yaml",
        "release-history",
    ): "records Part 1's real deposition history, which Zenodo record 18364119 confirms",
    (
        "cogsec_multiagent_2_computational/manuscript/03c_attack_ethics.md",
        "field-study",
    ): "states that there was no user study and no production system, as the negative claim",
    (
        "cogsec_multiagent_2_computational/manuscript/07_conclusion.md",
        "ethics-review",
    ): "states that no institutional review was sought because none was required",
    (
        "cogsec_multiagent_2_computational/manuscript/07_conclusion.md",
        "gated-access",
    ): "states that no access tier is operated and that nothing is held back",
    (
        "cogsec_multiagent_2_computational/manuscript/07_conclusion.md",
        "disclosure",
    ): "states that nothing was found to disclose and no coordinated disclosure took place",
    (
        "cogsec_multiagent_2_computational/manuscript/04_experimental_setup.md",
        "pre-registration",
    ): "names a preregistration file that is absent and says so, so the plan is not read as one",
    (
        "cogsec_multiagent_2_computational/manuscript/04_experimental_setup.md",
        "annotation",
    ): "defines the labels as generator properties and denies any inter-annotator statistic",
}

#: Below this the scan found nothing to look at, which means the file discovery
#: is broken rather than the manuscripts clean.
MIN_FILES = 40


def _manuscript_files() -> list[Path]:
    out = subprocess.run(
        [
            "git", "-C", str(REPO), "ls-files", "-z",
            *[f"{p}/manuscript/*.md" for p in PARTS],
            # config.yaml carries the abstract and changelog that become the
            # deposit's public metadata, so it is prose a reader sees.
            *[f"{p}/manuscript/config.yaml" for p in PARTS],
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [REPO / name for name in out.split("\0") if name]


def scan(files: list[Path]) -> list[tuple[str, str, int, str]]:
    """Every unregistered occurrence, as ``(path, pattern, line, excerpt)``."""
    findings: list[tuple[str, str, int, str]] = []
    for path in files:
        try:
            rel = path.relative_to(REPO).as_posix()
        except ValueError:
            # Scanning a file outside the tree is how the tests feed the gate a
            # sentence without editing a manuscript; such a file is never
            # registered, so every pattern in it must be reported.
            rel = path.as_posix()
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for name, pattern in PATTERNS.items():
                match = pattern.search(line)
                if not match:
                    continue
                if (rel, name) in ALLOWED:
                    continue
                start = max(0, match.start() - 40)
                findings.append((rel, name, number, line[start : match.end() + 40].strip()))
    return findings


def main() -> int:
    files = _manuscript_files()
    if len(files) < MIN_FILES:
        print(
            f"found only {len(files)} manuscript files; discovery is broken, and a "
            f"check that scans nothing must not pass",
            file=sys.stderr,
        )
        return 2

    findings = scan(files)
    print(f"unhappened claims: {len(files)} manuscript files scanned for "
          f"{len(PATTERNS)} kinds of process claim, {len(ALLOWED)} registered")
    for rel, name, number, excerpt in findings:
        print(f"  {rel}:{number} [{name}] {excerpt}")
    if findings:
        print(
            f"{len(findings)} unregistered process claim(s); each must be removed or "
            f"registered in ALLOWED with a reason"
        )
        return 1
    print("every process claim in the manuscripts is registered")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
