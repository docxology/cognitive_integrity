"""The unhappened-claims gate must catch the sentences that motivated it.

Every string below was in a shipped manuscript. A gate written after the fact
is worth nothing unless it would have caught the thing it was written for, so
each one is fed back through the scanner.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "check_unhappened_claims", REPO / "scripts" / "check_unhappened_claims.py"
)
assert _SPEC is not None and _SPEC.loader is not None
gate = importlib.util.module_from_spec(_SPEC)
sys.modules["check_unhappened_claims"] = gate
_SPEC.loader.exec_module(gate)


#: Verbatim from the manuscripts before this gate existed.
SHIPPED_FABRICATIONS = [
    ("participants", "**Participants**: 8 security researchers (2--10 years experience)"),
    ("annotation", "\\item Inter-rater reliability: Cohen's $\\kappa = 0.84$"),
    ("annotation", "\\item **Validation**: Human annotation of generated attacks"),
    ("ethics-review", "This research was reviewed and determined to be exempt from IRB oversight."),
    ("disclosure", "\\item **Embargoed**: 90-day disclosure window before publication"),
    ("disclosure", "Framework names are anonymized per coordinated disclosure agreements."),
    ("gated-access", "| Full access | Complete corpus | IRB approval + NDA |"),
    ("gated-access", "Full corpus available only to verified researchers"),
    (
        "acknowledgement-of-people",
        "The authors thank the eight security researchers who participated in the red team "
        "exercise, and the anonymous reviewers whose feedback strengthened this work.",
    ),
    ("pre-registration", "pre-registered analysis protocols (all hypotheses stated before evaluation)"),
    ("field-study", "We interviewed twelve operators running CIF in production at scale."),
]


@pytest.mark.parametrize("expected,sentence", SHIPPED_FABRICATIONS)
def test_a_shipped_fabrication_is_caught(expected, sentence, tmp_path):
    unregistered = tmp_path / "cogsec_multiagent_2_computational" / "manuscript"
    unregistered.mkdir(parents=True)
    path = unregistered / "not_registered.md"
    path.write_text(sentence + "\n", encoding="utf-8")

    findings = gate.scan([path])
    names = {name for _, name, _, _ in findings}
    assert expected in names, f"{expected!r} not among {names or 'nothing'} for: {sentence[:60]}"


def test_the_real_manuscripts_pass():
    assert gate.main() == 0


def test_discovery_finds_the_manuscripts():
    files = gate._manuscript_files()
    assert len(files) >= gate.MIN_FILES, len(files)
    for part in gate.PARTS:
        assert any(part in f.as_posix() for f in files), part


def test_every_registration_names_a_real_file_and_pattern():
    for (rel, name), reason in gate.ALLOWED.items():
        assert (REPO / rel).is_file(), f"{rel} is registered but does not exist"
        assert name in gate.PATTERNS, f"{name} is registered but is not a pattern"
        assert len(reason.split()) >= 5, f"{rel}/{name} has no real reason: {reason!r}"


def test_a_registration_only_covers_its_own_pattern(tmp_path):
    """Registering a file for one pattern must not silence the others."""
    rel = "cogsec_multiagent_2_computational/manuscript/03c_attack_ethics.md"
    assert (rel, "ethics-review") in gate.ALLOWED
    assert (rel, "acknowledgement-of-people") not in gate.ALLOWED

    path = REPO / rel
    original = path.read_text(encoding="utf-8")
    try:
        path.write_text(original + "\nThe authors thank the reviewers.\n", encoding="utf-8")
        findings = gate.scan([path])
        assert any(name == "acknowledgement-of-people" for _, name, _, _ in findings)
    finally:
        path.write_text(original, encoding="utf-8")
