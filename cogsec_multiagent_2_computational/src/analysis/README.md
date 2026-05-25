# `src/analysis/` — Game-Theoretic + Information-Geometric Analysis

Analytical layer that sits above the core defense mechanisms: game-theoretic formulation of attacker–defender dynamics (Nash equilibrium, arms race) and information-geometric structure of the belief manifold (Fisher–Rao metric, geodesic attack paths, curvature-constraint defenses).

## Series Position

Part 2 of four in the *Cognitive Security for Multiagent Operators* series. This subpackage realizes the theoretical-connections chapter of the manuscript:

- **§1c Theoretical Connections** — game theory + information geometry framing
- **§6 Discussion** — Nash analysis, arms race, adaptive defenders
- **§S10 Information Geometry** — full supplementary treatment

## Modules

| Module | Purpose | Key Exports |
| ------ | ------- | ----------- |
| `game_theory.py` | Two-player zero-sum game formulation; Nash equilibrium via `scipy.optimize.linprog`; fictitious play; arms-race simulation; minimax regret | `solve_zero_sum_game`, `GameResult`, `fictitious_play`, `arms_race_simulation`, `compute_cif_payoff_matrix`, `minimax_regret` |
| `information_geometry.py` | Statistical manifold of belief distributions; Fisher–Rao metric; geodesic attack paths; curvature-constraint defense formulation; sensitivity via Riemannian metric | `StatisticalManifold`, `geodesic_attack_path`, `defense_as_curvature_constraint`, `sensitivity_via_riemannian_metric` |

## Quick Usage

```python
from src.analysis import (
    solve_zero_sum_game,
    compute_cif_payoff_matrix,
    arms_race_simulation,
    StatisticalManifold,
    geodesic_attack_path,
)

# 1. Nash equilibrium over the CIF config space vs. attack distribution
payoff = compute_cif_payoff_matrix(
    defense_configs=["firewall-only", "firewall+sandbox", "full-cif"],
    attack_categories=["direct", "indirect", "coordination", "emergent"],
)
result = solve_zero_sum_game(payoff)
print(result.defender_strategy, result.value)   # mixed strategy + game value

# 2. Arms-race dynamics with adaptive attacker and periodic retraining
trace = arms_race_simulation(
    initial_defense="full-cif",
    attacker_adapt_rate=0.02,
    defender_retrain_every=5,
    defender_recovery=0.03,
    horizon=50,
)
print(trace.asymptotic_detection_rate)   # ~0.52 with retraining

# 3. Geodesic attack path on the belief manifold
manifold = StatisticalManifold(dim=10)
path = geodesic_attack_path(
    manifold,
    start=baseline_belief,
    end=target_belief,
    stealth_budget=0.05,
)
print(path.length, path.detection_probability)
```

## Manuscript Anchor

| Claim | Implementation |
| ----- | -------------- |
| Nash equilibrium of CIF config vs. attack distribution | `game_theory.solve_zero_sum_game` |
| Arms-race asymptote with periodic retraining | `game_theory.arms_race_simulation` |
| Minimax-regret fallback configuration | `game_theory.minimax_regret` |
| Fisher–Rao metric on belief distributions | `information_geometry.StatisticalManifold` |
| Geodesic attack path with stealth constraint | `information_geometry.geodesic_attack_path` |
| Defense as curvature constraint on the manifold | `information_geometry.defense_as_curvature_constraint` |

## Dependencies

- `numpy >= 1.22`
- `scipy >= 1.10` (for `linprog`, `minimize`, numerical integration)

## Testing

Tests in `tests/test_game_theory.py` and `tests/test_information_geometry.py` verify:

- Nash solutions against known small-game closed-form examples
- Arms-race monotonicity + convergence properties
- Fisher–Rao geodesics reduce to straight lines for Gaussian families (consistency check)

All tests use real numerical computation — see [`../AGENTS.md`](../AGENTS.md) for the no-mocks policy.
