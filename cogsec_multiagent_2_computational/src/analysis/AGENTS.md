# `src/analysis/` — Agent Reference

Guidance for agents modifying the game-theoretic and information-geometric analysis package.

## Purpose

Analytical layer over the core CIF defenses: Nash equilibrium, arms-race dynamics, Fisher–Rao manifold structure, geodesic attack paths. See [`README.md`](README.md) for the API map and manuscript anchors.

## Modules

### `game_theory.py`

Two-player zero-sum game formulation of attacker–defender interactions.

- Nash equilibrium: `scipy.optimize.linprog` with dual-variable recovery.
- Payoff matrix: `compute_cif_payoff_matrix(defense_configs, attack_categories)` constructs the matrix from empirical detection rates in `output/data/`.
- Arms-race: `arms_race_simulation` captures adversarial adaptation with periodic defender retraining (default 2% attacker adaptation per cycle; 3% defender recovery every 5 cycles).
- Regret: `minimax_regret` for robust defense selection under adversarial distribution uncertainty.

### `information_geometry.py`

Statistical manifold structure of belief space.

- `StatisticalManifold` — parameterized family of belief distributions with Fisher–Rao metric.
- `geodesic_attack_path` — shortest path on the manifold under a stealth budget (KL radius).
- `defense_as_curvature_constraint` — CIF mechanisms as curvature constraints restricting reachable attack manifold.
- `sensitivity_via_riemannian_metric` — per-direction sensitivity analysis.

## Rules

- **Real numerical solvers only** — use `scipy.optimize` / `numpy.linalg`, no fakes.
- **Deterministic** — accept `seed` in stochastic routines (`fictitious_play`, `arms_race_simulation`).
- **Numerical tolerances explicit** — Nash solutions returned with a documented tolerance (`result.tolerance`), so tests can assert within a stable bound.
- **Manuscript anchored** — non-trivial exports carry docstring references to Paper 2 §1c / §6 / §S10.

## When Editing

- Update [`README.md`](README.md) for any API change.
- Update [`../README.md`](../README.md) manuscript-to-code anchor if you add a new claim-backing function.
- Add tests in `tests/test_category_theory.py` (game theory) and `tests/test_information_geometry.py` — use closed-form small-case examples, not mocks.
- Cross-check with [`../../scripts/run_statistical_analysis.py`](../../scripts/run_statistical_analysis.py) which invokes these analyses for the publication suite.

## Cross-Paper Reference

The unified Part 3+4 paper (`friedman2026cogsec3`) §4 Discussion references the arms-race dynamics from `game_theory.arms_race_simulation` when motivating domain-calibrated retraining cadences.
