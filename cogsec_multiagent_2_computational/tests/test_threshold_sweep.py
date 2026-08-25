"""Tests for the firewall threshold sweep.

Part 3 published a τ₂ tuning outcome as an observed deployment result and
nothing had ever varied a threshold. The sweep exists now, and what it found is
sharper than four wrong numbers: the knob is flat across the band the tuning
used. These tests pin both the mechanics and that finding, because a plateau
that quietly disappears would be as interesting as one that appears.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from attacks.corpus import AttackCorpus
from core.firewall import FirewallConfig
from evaluation.benign_corpus import BenignCorpus
from evaluation.threshold_sweep import (
    sweep_quarantine_threshold,
    sweep_reject_threshold,
)

REPO = Path(__file__).resolve().parents[1]
ARTIFACT = REPO / "output" / "data" / "threshold_sweep.json"


@pytest.fixture(scope="module")
def arms() -> tuple[list[str], list[str]]:
    attacks = [s.payload for s in AttackCorpus.generate(seed=42)][:300]
    benign = [b.text for b in BenignCorpus.generate()]
    return attacks, benign


class TestTheSweepMechanics:
    def test_both_arms_are_required(self, arms):
        """A sweep over one arm reports a rate with no cost beside it."""
        attacks, benign = arms
        with pytest.raises(ValueError, match="both arms"):
            sweep_quarantine_threshold([0.5], attacks, [])
        with pytest.raises(ValueError, match="both arms"):
            sweep_quarantine_threshold([0.5], [], benign)

    def test_a_threshold_outside_the_unit_interval_raises(self, arms):
        attacks, benign = arms
        with pytest.raises(ValueError, match="outside"):
            sweep_quarantine_threshold([1.5], attacks, benign)

    def test_rates_carry_their_denominators(self, arms):
        attacks, benign = arms
        point = sweep_quarantine_threshold([0.5], attacks, benign)[0]
        assert point.n_attacks == len(attacks)
        assert point.n_benign == len(benign)
        assert point.youden_j == pytest.approx(point.tpr - point.fpr)

    def test_quarantine_and_reject_partition_the_flags(self, arms):
        """An input is flagged when the firewall does anything but accept it.

        Counting only REJECT would report a false-positive rate no operator
        ever sees, because a quarantined message still costs a review.
        """
        attacks, benign = arms
        point = sweep_quarantine_threshold([0.3], attacks, benign)[0]
        assert point.tpr == pytest.approx(point.quarantine_rate + point.reject_rate)

    def test_raising_the_threshold_never_raises_the_flag_rate(self, arms):
        """Monotonicity. A non-monotone sweep means the comparison is wrong."""
        attacks, benign = arms
        points = sweep_quarantine_threshold([i / 10 for i in range(11)], attacks, benign)
        for earlier, later in zip(points, points[1:]):
            assert later.tpr <= earlier.tpr + 1e-12
            assert later.fpr <= earlier.fpr + 1e-12

    def test_the_reject_sweep_moves_something(self, arms):
        """Anti-vacuity: a sweep that changes nothing anywhere is not a sweep."""
        attacks, benign = arms
        points = sweep_reject_threshold([0.0, 0.5, 1.0], attacks, benign)
        assert len({(p.tpr, p.fpr) for p in points}) > 1

    def test_the_shipped_config_is_not_mutated(self, arms):
        """The sweep builds new configs; the default must survive it."""
        attacks, benign = arms
        before = FirewallConfig().suspicious_threshold
        sweep_quarantine_threshold([0.1, 0.9], attacks, benign)
        assert FirewallConfig().suspicious_threshold == before


class TestTheFinding:
    @pytest.fixture(scope="class")
    def payload(self) -> dict:
        assert ARTIFACT.is_file(), "run scripts/run_threshold_sweep.py first"
        return json.loads(ARTIFACT.read_text(encoding="utf-8"))

    def test_the_quarantine_threshold_is_flat_where_it_is_tuned(self, payload):
        """The finding: the knob does nothing in the band it is tuned in.

        Part 3 recommended moving τ₂ from 0.50 to 0.55. Both endpoints sit
        inside a plateau of identical TPR and FPR. If this ever fails, the
        firewall's scoring has changed and the case study's recommendation
        becomes worth re-examining rather than retracting.
        """
        plateau = payload["quarantine_plateau"]
        assert plateau is not None, "no plateau; the scoring has changed"
        assert plateau["tau_low"] <= 0.50 <= plateau["tau_high"]
        assert plateau["tau_low"] <= 0.55 <= plateau["tau_high"]
        assert plateau["n_points"] >= 3

    def test_the_firewall_alone_never_beats_doing_nothing(self, payload):
        """Youden's J at or below zero everywhere is the second half of it."""
        best = payload["best_quarantine_point"]
        assert best["youden_j"] <= 0.0 + 1e-12, (
            f"the firewall alone now reaches J = {best['youden_j']:.3f}; that is "
            f"an improvement and the manuscript's account of this needs rewriting"
        )

    def test_the_shipped_thresholds_are_recorded(self, payload):
        shipped = payload["shipped"]
        config = FirewallConfig()
        assert shipped["injection_threshold"] == config.injection_threshold
        assert shipped["suspicious_threshold"] == config.suspicious_threshold
