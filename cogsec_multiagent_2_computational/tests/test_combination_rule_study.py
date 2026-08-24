"""Tests for the combination-rule study.

The claim this study makes is unusually easy to get wrong in a flattering
direction, so the tests are mostly about the protocol rather than the result:
that the reporting split is untouched by selection, that the modules really are
on incomparable scales, and that the headline gap is the one the artifact shows.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "run_combination_rule_study.py"
ARTIFACT = REPO / "output" / "data" / "combination_rule_study.json"


def _module():
    spec = importlib.util.spec_from_file_location("run_combination_rule_study", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["run_combination_rule_study"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def payload() -> dict:
    assert ARTIFACT.is_file(), "run scripts/run_combination_rule_study.py first"
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def test_the_three_splits_are_disjoint_and_nonempty(payload) -> None:
    """Selection and reporting must not share data.

    Choosing the best of 255 subsets on the split you then report it from
    inflates the number badly: this analysis read J = 0.323 that way against
    0.254 once the splits were separated. The protocol is the finding's
    credibility, so it is asserted rather than assumed.
    """
    protocol = payload["protocol"]
    for key in ("standardise_on", "select_on", "test_on"):
        assert protocol[key] > 0, f"{key} split is empty"
    assert (
        protocol["standardise_on"] + protocol["select_on"] + protocol["test_on"]
        == protocol["benign"]
    )


def test_the_modules_are_on_incomparable_scales(payload) -> None:
    """The premise. If they ever share a scale, a max rule becomes defensible."""
    scales = payload["results"]["per_module_benign_scale"]
    maxima = [m["benign_max"] for m in scales.values()]
    assert max(maxima) - min(maxima) > 0.3, (
        "module benign ranges have converged; the combination-rule argument "
        "needs re-deriving"
    )


def test_standardising_beats_the_shipped_rule_on_held_out_data(payload) -> None:
    """The result, on the split used for nothing else."""
    results = payload["results"]
    shipped = results["shipped_max_rule"]["held_out"]["youden_j"]
    standardised = results["standardised_all_modules"]["held_out"]["youden_j"]
    subset = results["standardised_best_subset"]["held_out"]["youden_j"]
    assert standardised > shipped
    assert subset > standardised
    assert shipped < 0, (
        "the shipped max rule now separates the classes; the paper's framing of "
        "this as a combination-rule defect needs revisiting"
    )


def test_the_winning_subset_is_the_modules_the_ablation_calls_worthless(payload) -> None:
    """The point of the finding, pinned.

    consensus, provenance, sandbox and invariants have a Shapley value of
    exactly zero in the ablation, which reads as four dead modules. They are
    dead only under a rule that compares their scores to modules using ten
    times the range. This test fails if that stops being true, which would mean
    the interpretation in the manuscript needs rewriting.
    """
    subset = set(payload["results"]["standardised_best_subset"]["subset"])
    silent = {"consensus", "provenance", "sandbox", "invariants"}
    assert subset & silent, (
        f"the winning subset {sorted(subset)} no longer includes any of the "
        f"modules the ablation reports as contributing nothing"
    )


def test_the_study_is_reproducible(payload) -> None:
    """Same seed, same numbers, or --check can only re-measure."""
    module = _module()
    fresh = module.build(payload["seed"])
    assert fresh["results"] == payload["results"]


def test_selection_never_sees_the_reporting_split(payload) -> None:
    """A behavioural check on the protocol, not just its recorded shape.

    Re-running with a different seed reshuffles all three splits. The selected
    subset may legitimately change; what must not happen is the held-out J
    matching the selection-half J exactly, which is the signature of reporting
    on the data you selected with.
    """
    module = _module()
    other = module.build(payload["seed"] + 1)
    best = other["results"]["standardised_best_subset"]
    assert best["selection_half_j"] != best["held_out"]["youden_j"], (
        "selection and held-out scores are identical; the splits have collapsed"
    )
