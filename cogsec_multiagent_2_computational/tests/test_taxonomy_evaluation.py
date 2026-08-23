"""Tests for the taxonomy x defense-lattice evaluation.

The artifact this produces is meant to replace 294 numeric cells that no
measurement stood behind, so the obligation here is not that the script runs.
It is that the numbers it writes are real, complete, and reproducible, and that
the script fails loudly in the specific ways that would otherwise let a
plausible-but-wrong number through.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "run_taxonomy_evaluation.py"
ARTIFACT = REPO / "output" / "data" / "taxonomy_evaluation_results.json"


def _module():
    spec = importlib.util.spec_from_file_location("run_taxonomy_evaluation", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["run_taxonomy_evaluation"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def payload() -> dict:
    assert ARTIFACT.is_file(), "run scripts/run_taxonomy_evaluation.py first"
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def test_every_corpus_category_has_a_family(payload) -> None:
    """A category with no family is silently dropped from the six-way roll-up.

    That is precisely the failure the roll-up exists to prevent, so the builder
    raises rather than dropping; this pins the invariant on the shipped file.
    """
    module = _module()
    assert set(payload["category_counts"]) <= set(module.FAMILY_OF)
    assert sum(payload["category_counts"].values()) == payload["corpus_size"]


def test_the_lattice_is_complete(payload) -> None:
    """2^8 subsets, or the Shapley values below are approximations pretending not to be."""
    assert payload["configurations"] == 2 ** len(payload["components"]) == 256
    assert payload["cells"]["baseline"]["per_family"]["overall"] == 0.0


def test_shapley_values_satisfy_efficiency(payload) -> None:
    """They must sum to full-stack minus baseline, exactly.

    This is the check that catches a malformed lattice: any missing or
    misindexed coalition breaks additivity, and nothing else in the artifact
    would show it.
    """
    full_key = "+".join(sorted(payload["components"]))
    full = payload["cells"][full_key]["per_family"]["overall"]
    baseline = payload["cells"]["baseline"]["per_family"]["overall"]
    assert sum(payload["shapley_overall_tpr"].values()) == pytest.approx(full - baseline, abs=1e-9)


def test_per_family_rates_are_consistent_with_their_categories(payload) -> None:
    """The roll-up must be an aggregate of counts, not an average of rates."""
    module = _module()
    full_key = "+".join(sorted(payload["components"]))
    cell = payload["cells"][full_key]
    detected: dict[str, int] = {}
    total: dict[str, int] = {}
    for category, record in cell["per_category"].items():
        family = module.FAMILY_OF[category]
        detected[family] = detected.get(family, 0) + record["detected"]
        total[family] = total.get(family, 0) + record["n"]
    for family, count in total.items():
        assert cell["per_family"][family] == pytest.approx(detected[family] / count)


def test_the_run_is_reproducible(payload) -> None:
    """Same seed, same numbers. Otherwise --check can only ever re-measure."""
    module = _module()
    fresh = module.build(payload["seed"], "axes")
    for key in ("baseline", *payload["components"]):
        assert fresh["cells"][key]["per_category"] == payload["cells"][key]["per_category"]
    assert fresh["corpus_digest"] == payload["corpus_digest"]


def test_an_unmapped_category_is_a_failure_not_a_silent_drop(monkeypatch) -> None:
    """The anti-vacuity case: extending the corpus must not quietly shrink the roll-up."""
    module = _module()
    trimmed = dict(module.FAMILY_OF)
    trimmed.pop("timing_attack")
    monkeypatch.setattr(module, "FAMILY_OF", trimmed)
    with pytest.raises(module.TaxonomyMismatch, match="no family"):
        module.build(42, "axes")


def test_modules_the_corpus_never_exercises_are_visible(payload) -> None:
    """Zero contribution must be distinguishable from zero capability.

    Three adapters -- consensus, provenance, sandbox -- fire on none of the 950
    payloads, so their Shapley value is exactly zero in every coalition. That is
    a statement about corpus coverage, not about the mechanisms: the corpus
    contains no instance of what they are built to catch. The distinction is
    the difference between "this defense does not work" and "this evaluation
    does not test it", and the artifact has to keep it legible.
    """
    silent = [c for c, v in payload["shapley_overall_tpr"].items() if v == 0.0]
    assert silent, "expected the corpus-coverage gap to be visible in the artifact"
    for component in silent:
        assert payload["cells"][component]["per_family"]["overall"] == 0.0
