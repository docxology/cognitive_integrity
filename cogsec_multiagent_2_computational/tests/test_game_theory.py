"""Tests for the zero-sum attacker-defender game.

Covers:
- LP Nash equilibrium on small and CIF-sized payoff matrices.
- Value bounded by min/max of the payoff matrix.
- Fictitious play converges near the LP solution.
- Minimax regret is a one-hot pure strategy summing to 1.
- compute_cif_payoff_matrix shape and monotonicity in full_cif column.
- Arms race simulation produces consistent output shapes.

NO MOCKS. All tests use real numerical payoff matrices.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pytest

from src.analysis.game_theory import (
    GameResult,
    arms_race_simulation,
    compute_cif_payoff_matrix,
    fictitious_play,
    minimax_regret,
    solve_zero_sum_game,
)


def test_cif_payoff_matrix_shape_and_labels():
    """The CIF payoff matrix is 6 x 6 with matching label lists."""
    M, attacks, defenses = compute_cif_payoff_matrix()
    assert M.shape == (6, 6)
    assert len(attacks) == 6
    assert len(defenses) == 6
    # no_defense column is all zero.
    assert np.allclose(M[:, 0], 0.0)


def test_cif_payoff_full_cif_dominates_subsets():
    """full_cif column >= all other columns row-wise."""
    M, _, _ = compute_cif_payoff_matrix()
    # Column index 5 = full_cif.
    for col in range(M.shape[1]):
        if col == 5:
            continue
        assert np.all(M[:, 5] >= M[:, col])


def test_solve_zero_sum_game_value_within_matrix_range():
    """Nash game value lies in [min(M), max(M)]."""
    M, _, _ = compute_cif_payoff_matrix()
    result = solve_zero_sum_game(M)
    assert M.min() - 1e-9 <= result.game_value <= M.max() + 1e-9


def test_solve_zero_sum_game_strategies_are_distributions():
    """Attacker and defender strategies are probability distributions."""
    M, _, _ = compute_cif_payoff_matrix()
    result = solve_zero_sum_game(M)
    assert result.attacker_strategy.shape == (6,)
    assert result.defender_strategy.shape == (6,)
    assert np.all(result.attacker_strategy >= -1e-12)
    assert np.all(result.defender_strategy >= -1e-12)
    assert result.attacker_strategy.sum() == pytest.approx(1.0, abs=1e-8)
    assert result.defender_strategy.sum() == pytest.approx(1.0, abs=1e-8)


def test_solve_rejects_empty_matrix():
    """Empty payoff matrix raises ValueError."""
    with pytest.raises(ValueError):
        solve_zero_sum_game(np.zeros((0, 0)))


def test_fictitious_play_converges_near_linprog():
    """Fictitious play's game value is close to the LP solution."""
    M, _, _ = compute_cif_payoff_matrix()
    lp = solve_zero_sum_game(M)
    fp = fictitious_play(M, n_iterations=10_000, seed=42)
    assert isinstance(fp, GameResult)
    assert abs(fp.game_value - lp.game_value) < 0.01


def test_fictitious_play_strategies_are_distributions():
    """Fictitious play produces normalised mixed strategies."""
    M, _, _ = compute_cif_payoff_matrix()
    fp = fictitious_play(M, n_iterations=2_000, seed=7)
    assert fp.attacker_strategy.sum() == pytest.approx(1.0, abs=1e-8)
    assert fp.defender_strategy.sum() == pytest.approx(1.0, abs=1e-8)


def test_minimax_regret_is_one_hot():
    """minimax_regret returns a one-hot pure-strategy distribution."""
    M, _, _ = compute_cif_payoff_matrix()
    dist, worst = minimax_regret(M)
    assert dist.shape == (6,)
    assert dist.sum() == pytest.approx(1.0)
    # Exactly one entry is 1.0.
    assert np.sum(dist > 0.5) == 1
    assert worst >= 0.0


def test_minimax_regret_picks_full_cif_on_cif_matrix():
    """On the CIF matrix the full_cif defense minimises worst-case regret."""
    M, _, defenses = compute_cif_payoff_matrix()
    dist, worst = minimax_regret(M)
    chosen = int(np.argmax(dist))
    assert defenses[chosen] == "full_cif"
    assert worst == pytest.approx(0.0)


def test_arms_race_simulation_output_shapes():
    """arms_race_simulation returns arrays of the requested length."""
    out = arms_race_simulation(
        initial_detection_rate=0.85,
        n_rounds=30,
        seed=42,
    )
    for key in ("detection_rates", "attacker_evasion",
                "defender_coverage", "rounds"):
        assert out[key].shape == (30,)
    # Every reported value is in [0, 1] for rates/coverages/evasion.
    for key in ("detection_rates", "attacker_evasion", "defender_coverage"):
        assert np.all(out[key] >= 0.0)
        assert np.all(out[key] <= 1.0)


def test_arms_race_simulation_attacker_evasion_non_decreasing_trend():
    """Attacker evasion drifts upward with time (despite noise)."""
    out = arms_race_simulation(
        initial_detection_rate=0.9,
        attacker_adapt_rate=0.01,
        n_rounds=40,
        seed=0,
    )
    assert out["attacker_evasion"][-1] > out["attacker_evasion"][0]


def test_solve_handles_simple_2x2_matrix():
    """A classical 2x2 zero-sum game: matching pennies has value 0."""
    # Matching pennies payoffs for defender: correctly match -> 1, else -> -1.
    # We rescale to [0, 1] to respect the detection-probability interpretation.
    M = np.array(
        [
            [1.0, 0.0],  # attack 0: def 0 wins, def 1 loses
            [0.0, 1.0],  # attack 1: def 1 wins, def 0 loses
        ]
    )
    res = solve_zero_sum_game(M)
    # Value should be 0.5 (uniform mixing).
    assert res.game_value == pytest.approx(0.5, abs=1e-6)
    assert res.defender_strategy == pytest.approx(
        np.array([0.5, 0.5]), abs=1e-6
    )


def test_the_one_measured_payoff_cell_comes_from_the_artifact() -> None:
    """The emergent-misalignment cell must not be a typed literal.

    It carried 0.56 -- the single-seed figure the manuscripts explicitly
    retract as "not the publication estimate" -- while a Nash result computed
    from it was published as a finding. Reading it from colony_results.json is
    what makes that impossible to repeat: change the benchmark and the
    equilibrium changes with it, or the build fails.
    """
    import json
    from pathlib import Path

    from analysis.game_theory import compute_cif_payoff_matrix

    matrix, attacks, defenses = compute_cif_payoff_matrix()
    artifact = json.loads(
        (Path(__file__).resolve().parents[1] / "output" / "data" / "colony_results.json").read_text()
    )
    measured = next(
        s["detection_rate_mean"]
        for s in artifact["scenarios"]
        if s["scenario"] == "emergent_misalignment"
    )
    cell = matrix[attacks.index("emergent_misalignment"), defenses.index("full_cif")]
    assert cell == pytest.approx(measured), (
        f"payoff cell {cell} does not match the benchmark {measured}"
    )
    assert cell != pytest.approx(0.56, abs=1e-9), "the retracted single-seed value is back"


def test_the_equilibrium_follows_the_measured_cell() -> None:
    """Guard the conclusion, not just the input.

    On the published benchmark the attacker's best response is coordination.
    If someone re-hardcodes the cell, this fails alongside the one above rather
    than leaving the paper's headline quietly resting on a stale number.
    """
    from analysis.game_theory import compute_cif_payoff_matrix, solve_zero_sum_game

    matrix, attacks, defenses = compute_cif_payoff_matrix()
    result = solve_zero_sum_game(matrix)
    assert defenses[result.defender_pure_best] == "full_cif"
    assert attacks[result.attacker_pure_best] == "coordination"
    assert result.game_value == pytest.approx(0.61, abs=5e-3)
