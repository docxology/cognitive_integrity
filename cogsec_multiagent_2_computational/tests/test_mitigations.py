"""Tests for the false-positive mitigations and the study over them.

Six strategies were published with paired FPR/TPR deltas under a caption
describing measured effectiveness, and none of them existed. These tests are
mostly about the two ways that could recur: a strategy that does not do what
its name says, and a measurement whose basis quietly makes one of them look
impossible.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from composition.mitigations import (
    MITIGATIONS,
    Verdict,
    combined,
    confirmation_cascade,
    contextual_whitelist,
    cost_sensitive,
    identity,
    temporal_smoothing,
)
from utils.types import DefenseResult

REPO = Path(__file__).resolve().parents[1]
ARTIFACT = REPO / "output" / "data" / "fp_mitigation.json"


def _result(detected: bool, score: float, name: str = "m") -> DefenseResult:
    return DefenseResult(detected=detected, score=score, module_name=name, details={})


def _verdict(*modules: tuple[bool, float]) -> Verdict:
    results = [_result(d, s, f"m{i}") for i, (d, s) in enumerate(modules)]
    return Verdict(
        flagged=any(d for d, _ in modules),
        score=max((s for _, s in modules), default=0.0),
        module_results=tuple(results),
    )


class TestEachStrategyDoesWhatItsNameSays:
    def test_identity_changes_nothing(self):
        v = [_verdict((True, 0.9)), _verdict((False, 0.1))]
        assert identity(v) == [True, False]

    def test_a_mitigation_never_creates_a_flag(self):
        """Every strategy is a filter. None may flag what the pipeline did not.

        A mitigation that raised the true-positive rate would be a detector,
        and its delta would not be a mitigation's delta.
        """
        stream = [_verdict((False, 0.2)), _verdict((True, 0.9), (True, 0.8))]
        for name, mitigation in MITIGATIONS.items():
            out = mitigation(stream)
            for kept, verdict in zip(out, stream):
                assert not (kept and not verdict.flagged), name

    def test_confirmation_cascade_needs_two_modules(self):
        assert confirmation_cascade([_verdict((True, 0.9))]) == [False]
        assert confirmation_cascade([_verdict((True, 0.9), (True, 0.7))]) == [True]

    def test_cost_sensitive_is_a_score_floor(self):
        assert cost_sensitive([_verdict((True, 0.65))], threshold=0.7) == [False]
        assert cost_sensitive([_verdict((True, 0.75))], threshold=0.7) == [True]

    def test_contextual_whitelist_keeps_strong_or_corroborated(self):
        assert contextual_whitelist([_verdict((True, 0.3))]) == [False]
        assert contextual_whitelist([_verdict((True, 0.9))]) == [True]
        assert contextual_whitelist([_verdict((True, 0.3), (True, 0.2))]) == [True]

    def test_temporal_smoothing_needs_a_burst(self):
        lone = [_verdict((False, 0.1))] * 4 + [_verdict((True, 0.9))]
        assert temporal_smoothing(lone)[-1] is False
        burst = [_verdict((True, 0.9)), _verdict((True, 0.9))]
        assert temporal_smoothing(burst)[-1] is True

    def test_combined_is_the_conjunction_it_claims_to_be(self):
        stream = [
            _verdict((True, 0.9)),
            _verdict((True, 0.3), (True, 0.2)),
            _verdict((True, 0.9), (True, 0.8)),
        ]
        assert combined(stream) == [
            a and b
            for a, b in zip(confirmation_cascade(stream), contextual_whitelist(stream))
        ]

    def test_incremental_learning_is_absent(self):
        """The one strategy that must not be faked.

        It needs a model that updates on labelled feedback and every module in
        this framework is a fixed scorer. A strategy under that name would be
        something adjacent wearing it.
        """
        assert "incremental_learning" not in MITIGATIONS


class TestTheStudy:
    @pytest.fixture(scope="class")
    def payload(self) -> dict:
        assert ARTIFACT.is_file(), "run scripts/run_fp_mitigation.py first"
        return json.loads(ARTIFACT.read_text(encoding="utf-8"))

    def test_every_implemented_strategy_is_measured(self, payload):
        assert set(payload["strategies"]) == set(MITIGATIONS)

    def test_the_root_causes_partition_the_false_positives(self, payload):
        """They must sum to the count, not to a round number.

        The table this replaces had five causes summing to exactly 100%
        because they were chosen to. These are attributions of individual
        false positives, so they add up or the attribution is broken.
        """
        assert sum(payload["root_causes"].values()) == payload["false_positives"]
        assert sum(payload["false_positives_by_benign_category"].values()) == payload[
            "false_positives"
        ]

    def test_the_verdicts_carry_every_module(self, payload):
        """The measurement basis, pinned.

        SeriesPipeline short-circuits on the first module that flags, so a
        cascade evaluated against its output sees one flagging module every
        time and reports -100% detection: a strategy failing for a reason that
        has nothing to do with the strategy. If the cascade's TPR ever returns
        to exactly zero, that is the first thing to check.
        """
        cascade = payload["strategies"]["confirmation_cascade"]
        assert cascade["tpr"] > 0.0, (
            "the confirmation cascade detects nothing, which is what happens "
            "when the verdicts are built from a short-circuiting pipeline "
            "rather than from every module"
        )

    def test_a_mitigation_that_helps_is_visible(self, payload):
        """At least one strategy must beat the baseline on Youden's J.

        Not a demand that the framework be good --- a demand that the study be
        able to show it if it is. A table where every row is worse than doing
        nothing would more likely mean the post-filters are misapplied than
        that no mitigation can work.
        """
        base = payload["strategies"]["none"]["youden_j"]
        assert max(
            row["youden_j"] for row in payload["strategies"].values()
        ) > base

    def test_incremental_learning_is_recorded_as_not_implemented(self, payload):
        """Absent from the results and present in the record of what is missing."""
        assert "incremental_learning" in payload["not_implemented"]
        assert "incremental_learning" not in payload["strategies"]
