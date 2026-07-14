"""Analysis modules: game theory, information geometry.

Game-theoretic and information-geometric analysis of CIF defense
configurations.  Game theory yields Nash equilibria and arms-race
dynamics; information geometry provides the Fisher-Rao metric on
belief space used for geodesic attack paths and curvature-based
defenses.
"""

from __future__ import annotations

from .game_theory import (
    GameResult,
    arms_race_simulation,
    compute_cif_payoff_matrix,
    fictitious_play,
    minimax_regret,
    solve_zero_sum_game,
)
from .information_geometry import (
    StatisticalManifold,
    defense_as_curvature_constraint,
    geodesic_attack_path,
    sensitivity_via_riemannian_metric,
)

__all__ = [
    "solve_zero_sum_game",
    "GameResult",
    "fictitious_play",
    "arms_race_simulation",
    "compute_cif_payoff_matrix",
    "minimax_regret",
    "StatisticalManifold",
    "geodesic_attack_path",
    "defense_as_curvature_constraint",
    "sensitivity_via_riemannian_metric",
]
