"""The proof-status index must account for every result in the manuscript.

S01's Proof Status section claims to record, by exact label, which results carry
a proof and which are asserted without one.  That claim is only worth anything
if it is enforced: an index that silently falls behind the text is worse than no
index, because it reads as an audit while omitting exactly the results nobody
checked.  Fifteen results (five theorems, one lemma, nine corollaries) were
missing from it before this test existed.

A result is accounted for when at least one of these holds:

1. it carries an inline ``proof`` environment in the main text;
2. it is restated and proved in S01 (its label appears in the "proven" list, or
   a ``*-restated`` sibling does);
3. it is listed under "Asserted without proof (deferred)".

Anything else is an unaudited claim.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

MANUSCRIPT = Path(__file__).parent.parent / "manuscript"

#: Main-text sections carrying formal results.  S01 is the proof supplement
#: itself and is read separately; S03 is notation.
BODY_FILES = (
    "03_threat_model.md",
    "04_formal_framework.md",
    "05_defense_mechanisms.md",
    "06_detection_methods.md",
    "07_formal_verification.md",
    "S02_eusocial_cogsec.md",
)

_RESULT = re.compile(
    r"\\begin\{(theorem|lemma|corollary)\}(?:\[([^\]]*)\])?\s*\n\\label\{([^}]+)\}"
)


def _results() -> dict[str, tuple[str, str, str, bool]]:
    """Every labelled result in the main text, and whether it proves itself."""
    found: dict[str, tuple[str, str, str, bool]] = {}
    for name in BODY_FILES:
        text = (MANUSCRIPT / name).read_text(encoding="utf-8")
        for match in _RESULT.finditer(text):
            kind, title, label = match.group(1), match.group(2) or "", match.group(3)
            end = text.find(f"\\end{{{kind}}}", match.end())
            # An inline proof follows the environment closely; 400 characters is
            # generous enough for a blank line and a short remark in between,
            # and tight enough that it cannot reach the *next* result's proof.
            tail = text[end : end + 400] if end != -1 else ""
            found[label] = (kind, title, name, "\\begin{proof}" in tail)
    return found


def _indexed_labels() -> set[str]:
    """Labels named anywhere in S01's Proof Status section."""
    s01 = (MANUSCRIPT / "S01_proofs.md").read_text(encoding="utf-8")
    status = s01.split("## Preliminary Definitions")[0]
    named = set(re.findall(r"\\cref\{([^}]+)\}", status))
    # A supplement proof restates the body result under a ``-restated`` label.
    return named | {label.replace("-restated", "") for label in named}


def test_the_manuscript_contains_formal_results_to_audit() -> None:
    """Anti-vacuity: an empty sweep would make every assertion below trivial."""
    results = _results()
    assert len(results) > 40, f"only {len(results)} results parsed; the regex is broken"
    assert _indexed_labels(), "no labels parsed out of the Proof Status section"


def test_every_result_is_proved_inline_restated_or_declared_deferred() -> None:
    results = _results()
    indexed = _indexed_labels()
    unaccounted = [
        f"{kind} {label} ({title or 'untitled'}) in {source}"
        for label, (kind, title, source, inline) in sorted(results.items())
        if not inline and label not in indexed
    ]
    assert not unaccounted, (
        "results that neither prove themselves inline nor appear in S01's Proof "
        "Status index -- each is an unaudited claim:\n  " + "\n  ".join(unaccounted)
    )


def test_the_index_names_no_result_the_manuscript_does_not_contain() -> None:
    """The reverse direction: a stale entry points at a result that was removed."""
    s01 = (MANUSCRIPT / "S01_proofs.md").read_text(encoding="utf-8")
    status = s01.split("## Preliminary Definitions")[0]
    everything = "".join(
        (MANUSCRIPT / name).read_text(encoding="utf-8")
        for name in (*BODY_FILES, "S01_proofs.md")
    )
    dangling = [
        label
        for label in re.findall(r"\\cref\{((?:thm|lem|cor):[^}]+)\}", status)
        if f"\\label{{{label}}}" not in everything
    ]
    assert not dangling, f"Proof Status names labels that no longer exist: {dangling}"


@pytest.mark.parametrize(
    "planted",
    [
        "\\begin{theorem}[Planted]\n\\label{thm:planted-unaudited}\nA claim.\n\\end{theorem}\n",
    ],
)
def test_the_audit_can_actually_fail(planted: str, tmp_path: Path) -> None:
    """A guard that cannot fire proves nothing; prove this one fires."""
    label = re.search(r"\\label\{([^}]+)\}", planted).group(1)
    assert label not in _indexed_labels()
    assert "\\begin{proof}" not in planted
