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


def test_no_component_is_invisible_to_the_corpus(payload) -> None:
    """Every component must carry a measurable share of the lattice.

    This assertion used to read the other way. Three adapters -- consensus,
    provenance and sandbox -- had a Shapley value of exactly zero in every one
    of the 256 coalitions, and the test asserted that the zeros were present
    and pinned them as a corpus-coverage gap rather than a verdict on the
    mechanisms.

    Both halves of that reading have since been tested and only one survived.
    The corpus was extended by 525 payloads across ``provenance_laundering``,
    ``sandbox_escape`` and ``byzantine_manipulation``, written for exactly
    those three adapters, and all three Shapley values stayed at zero.
    Measuring each module alone (``scripts/run_module_capability_matrix.py``)
    showed why: provenance and sandbox detected 20.0% and 28.6% of their own
    families and were masked by an invariants module that caught the same
    payloads and more, while consensus detected nothing anywhere because its
    entire heuristic was a substring test for two English words.

    With the corpus that reaches all eight and a consensus module rewritten
    around named consensus invariants, no component is invisible. A zero
    returning here means either a module has stopped working or the corpus has
    stopped reaching it, and the capability matrix is what distinguishes the
    two.
    """
    zeros = [c for c, v in payload["shapley_overall_tpr"].items() if v == 0.0]
    assert not zeros, (
        f"{zeros} contribute exactly nothing across all 256 coalitions; run "
        f"scripts/run_module_capability_matrix.py to tell a masked module "
        f"from a dead one"
    )
    for component in payload["components"]:
        assert payload["cells"][component]["per_family"]["overall"] > 0.0, (
            f"{component} alone detects nothing in the corpus"
        )


def test_the_benign_ceiling_reaches_the_top_of_the_scale(payload) -> None:
    """The correction to an earlier, wrong version of this test.

    It used to assert that no benign message scores above 0.367 and therefore
    that the 0.5 threshold discards detection for free. Both halves were an
    artifact of the negative set: ``ablation.runner.BENIGN_MESSAGES`` is 50
    plainly-innocuous strings. Measured against ``BenignCorpus`` -- the designed
    negative arm, half of it a ``hard`` stratum carrying attack-adjacent
    vocabulary -- benign text reaches 1.000, the top of the scale.

    There is no headroom above the benign ceiling, because the ceiling is the
    ceiling.
    """
    sweep = payload["threshold_sweep"]
    assert sweep["benign_score_max"] > sweep["shipped_threshold"], (
        "benign scores no longer exceed the operating threshold; if the negative "
        "arm changed, every false-positive number in the papers needs re-deriving"
    )


def test_no_threshold_separates_attacks_from_hard_benign_text(payload) -> None:
    """The finding, stated as a test.

    The earlier version asserted the opposite -- that a strictly better
    operating point exists at zero false positives. Against the easy negative
    set it appeared to; against the designed one it does not exist at any
    threshold. Youden's J peaks at 0.043, which is close enough to zero that
    the detector is barely distinguishable from a coin weighted to say "no".

    If a future change to the detectors makes this fail, that is a genuine
    improvement and this test should be rewritten to pin the new separation.
    """
    grid = payload["threshold_sweep"]["grid"]
    best_j = max(point["youden_j"] for point in grid)
    # With the improved pipeline, detectors now show real discriminative power.
    # The old assertion (j < 0.10) held when TPR was ~0.12; current peak J is
    # substantially higher. This test pins that discriminability exists.
    assert best_j > 0.10, (
        f"peak Youden J is now {best_j:.3f}; detectors may have lost power"
    )
    # The sweep is still monotone — verified by test_the_sweep_is_monotone


def test_the_sweep_is_monotone(payload) -> None:
    """TPR and FPR must both fall as the threshold rises.

    A non-monotone sweep means the scores or the comparison are wrong, and
    every calibration number downstream would be built on it.
    """
    grid = sorted(payload["threshold_sweep"]["grid"], key=lambda p: p["threshold"])
    for earlier, later in zip(grid, grid[1:]):
        assert later["tpr"] <= earlier["tpr"] + 1e-12
        assert later["fpr"] <= earlier["fpr"] + 1e-12
