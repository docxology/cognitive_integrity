"""Two-player zero-sum game formulation of CIF attacker-defender interactions.

Attacker chooses an attack type ``a ∈ {Ω_1, ..., Ω_6}``; defender
chooses a defense configuration ``d ∈ D``.  The payoff matrix
``M[a, d]`` is the detection probability for ``(a, d)``: the defender
*maximises* it and the attacker *minimises* it.  A mixed Nash
equilibrium is found via linear programming and, for cross-validation,
via fictitious play.

The module also provides a deterministic CIF-specific payoff matrix
built from Paper 2 S08 parametric simulation results, plus a
lightweight arms-race simulation and a minimax-regret solver.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import numpy as np
from scipy.optimize import linprog

# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class GameResult:
    """Mixed Nash equilibrium diagnostics.

    Attributes:
        attacker_strategy: Probability distribution over attacks.
        defender_strategy: Probability distribution over defenses.
        game_value: Equilibrium value ``v^*`` (defender's expected
            payoff / attacker's expected loss).
        attacker_pure_best: Index of the attacker's best pure reply to
            the defender's Nash strategy.
        defender_pure_best: Index of the defender's best pure reply to
            the attacker's Nash strategy.
    """

    attacker_strategy: np.ndarray
    defender_strategy: np.ndarray
    game_value: float
    attacker_pure_best: int
    defender_pure_best: int


# ---------------------------------------------------------------------------
# Solver via linear programming
# ---------------------------------------------------------------------------

def solve_zero_sum_game(
    payoff_matrix: np.ndarray,
    method: str = "linprog",
) -> GameResult:
    """Compute the mixed Nash equilibrium of a zero-sum game.

    Formulation (defender's LP): variables ``x = [p_1, ..., p_m, v]``
    where ``p`` is the defender's mixed strategy over ``m`` defenses
    and ``v`` is the game value.

    - Objective:  minimise ``-v``.
    - Inequalities (one per attack ``a``): ``-sum_d M[a, d] p[d] + v <= 0``.
    - Equality:  ``sum_d p[d] = 1``.
    - Bounds:   ``p[d] >= 0``,  ``v`` unbounded.

    The attacker's Nash strategy is recovered from the dual variables
    (shadow prices of the inequality rows) returned by HiGHS.

    Args:
        payoff_matrix: Shape ``(n_attacks, n_defenses)``.  Entries are
            detection probabilities in ``[0, 1]``.
        method: Currently only ``"linprog"`` is implemented.

    Returns:
        :class:`GameResult` with mixed strategies and game value.
    """
    if method != "linprog":
        raise ValueError(f"Unsupported method: {method}")

    M = np.asarray(payoff_matrix, dtype=float)
    if M.ndim != 2:
        raise ValueError("payoff_matrix must be 2-D")
    n_attacks, n_defenses = M.shape
    if n_attacks == 0 or n_defenses == 0:
        raise ValueError("payoff_matrix must be non-empty")

    # Variables: [p_0, ..., p_{m-1}, v].  Objective: minimise -v.
    c = np.zeros(n_defenses + 1, dtype=float)
    c[-1] = -1.0

    # Inequality rows: [-M[a, 0], ..., -M[a, m-1], 1] @ x <= 0
    A_ub = np.hstack([-M, np.ones((n_attacks, 1), dtype=float)])
    b_ub = np.zeros(n_attacks, dtype=float)

    # Equality: sum(p) = 1  -> [1, 1, ..., 1, 0] @ x = 1
    A_eq = np.zeros((1, n_defenses + 1), dtype=float)
    A_eq[0, :n_defenses] = 1.0
    b_eq = np.array([1.0], dtype=float)

    bounds: List[Tuple[float | None, float | None]] = (
        [(0.0, None)] * n_defenses + [(None, None)]  # type: ignore[assignment]
    )

    res = linprog(
        c=c,
        A_ub=A_ub,
        b_ub=b_ub,
        A_eq=A_eq,
        b_eq=b_eq,
        bounds=bounds,
        method="highs",
    )
    if not res.success:
        raise RuntimeError(f"linprog failed: {res.message}")

    defender_strategy = np.clip(res.x[:n_defenses], 0.0, None)
    if defender_strategy.sum() > 0:
        defender_strategy = defender_strategy / defender_strategy.sum()
    game_value = float(-res.fun)

    # Attacker strategy from dual variables on the A_ub rows.
    dual = getattr(res, "ineqlin", None)
    if dual is not None and getattr(dual, "marginals", None) is not None:
        marginals = np.asarray(dual.marginals, dtype=float)
        attacker_strategy = np.abs(marginals)
    else:
        attacker_strategy = np.ones(n_attacks, dtype=float)

    total = attacker_strategy.sum()
    if total > 0:
        attacker_strategy = attacker_strategy / total
    else:
        attacker_strategy = np.ones(n_attacks, dtype=float) / n_attacks

    # Pure best replies to the *mixed* opponent strategy.
    defender_payoff_per_def = attacker_strategy @ M
    defender_pure_best = int(np.argmax(defender_payoff_per_def))

    attacker_payoff_per_att = M @ defender_strategy
    attacker_pure_best = int(np.argmin(attacker_payoff_per_att))

    return GameResult(
        attacker_strategy=attacker_strategy,
        defender_strategy=defender_strategy,
        game_value=game_value,
        attacker_pure_best=attacker_pure_best,
        defender_pure_best=defender_pure_best,
    )


# ---------------------------------------------------------------------------
# Fictitious play
# ---------------------------------------------------------------------------

def fictitious_play(
    payoff_matrix: np.ndarray,
    n_iterations: int = 10_000,
    seed: int = 42,
) -> GameResult:
    """Approximate Nash via fictitious play.

    Each iteration the attacker best-responds to the empirical
    frequency of the defender's past actions, and vice versa.
    Converges (in the time-average) to a Nash equilibrium for
    zero-sum games.

    Args:
        payoff_matrix: Shape ``(n_attacks, n_defenses)``.
        n_iterations: Number of fictitious-play iterations.
        seed: RNG seed (used only for initial tie-breaking).

    Returns:
        :class:`GameResult` with time-averaged strategies.
    """
    M = np.asarray(payoff_matrix, dtype=float)
    n_attacks, n_defenses = M.shape
    rng = np.random.default_rng(seed)

    # Initial counts: one action each, chosen randomly.
    attacker_counts = np.zeros(n_attacks, dtype=float)
    defender_counts = np.zeros(n_defenses, dtype=float)
    attacker_counts[rng.integers(0, n_attacks)] = 1.0
    defender_counts[rng.integers(0, n_defenses)] = 1.0

    for _ in range(n_iterations):
        # Attacker minimises: pick attack with lowest expected payoff.
        defender_freq = defender_counts / defender_counts.sum()
        attacker_payoffs = M @ defender_freq
        a_best = int(np.argmin(attacker_payoffs))

        # Defender maximises: pick defense with highest expected payoff.
        attacker_freq = attacker_counts / attacker_counts.sum()
        defender_payoffs = attacker_freq @ M
        d_best = int(np.argmax(defender_payoffs))

        attacker_counts[a_best] += 1.0
        defender_counts[d_best] += 1.0

    attacker_strategy = attacker_counts / attacker_counts.sum()
    defender_strategy = defender_counts / defender_counts.sum()
    game_value = float(attacker_strategy @ M @ defender_strategy)

    defender_pure_best = int(np.argmax(attacker_strategy @ M))
    attacker_pure_best = int(np.argmin(M @ defender_strategy))

    return GameResult(
        attacker_strategy=attacker_strategy,
        defender_strategy=defender_strategy,
        game_value=game_value,
        attacker_pure_best=attacker_pure_best,
        defender_pure_best=defender_pure_best,
    )


# ---------------------------------------------------------------------------
# Arms-race dynamics
# ---------------------------------------------------------------------------

def arms_race_simulation(
    initial_detection_rate: float,
    attacker_adapt_rate: float = 0.02,
    defender_adapt_rate: float = 0.03,
    n_rounds: int = 50,
    seed: int = 42,
) -> dict:
    """Simulate co-evolution of attacker evasion and defender coverage.

    Each round: attacker degrades the detection rate by
    ``attacker_adapt_rate`` (clipped to ``[0, 1]``); every 5 rounds the
    defender retrains and recovers ``defender_adapt_rate``.  Small
    Gaussian noise (seeded) is added to each update.

    Args:
        initial_detection_rate: Starting detection rate in ``[0, 1]``.
        attacker_adapt_rate: Per-round attacker improvement.
        defender_adapt_rate: Per-retrain defender improvement.
        n_rounds: Number of rounds to simulate.
        seed: RNG seed.

    Returns:
        Dict with ``detection_rates``, ``attacker_evasion``,
        ``defender_coverage``, and ``rounds``, each a length-``n_rounds``
        array.
    """
    rng = np.random.default_rng(seed)
    detection = np.zeros(n_rounds, dtype=float)
    attacker = np.zeros(n_rounds, dtype=float)
    defender = np.zeros(n_rounds, dtype=float)
    rounds = np.arange(n_rounds, dtype=float)

    current = float(initial_detection_rate)
    att_evasion = 0.0
    def_coverage = float(initial_detection_rate)

    for t in range(n_rounds):
        # Attacker degrades detection every round.
        att_evasion = min(1.0, att_evasion + attacker_adapt_rate +
                          float(rng.normal(0.0, 0.002)))
        current = max(0.0, current - attacker_adapt_rate -
                      float(rng.normal(0.0, 0.002)))

        # Defender retrains every 5 rounds.
        if t > 0 and t % 5 == 0:
            def_coverage = min(1.0, def_coverage + defender_adapt_rate +
                               float(rng.normal(0.0, 0.002)))
            current = min(1.0, current + defender_adapt_rate)

        current = float(np.clip(current, 0.0, 1.0))
        detection[t] = current
        attacker[t] = float(np.clip(att_evasion, 0.0, 1.0))
        defender[t] = float(np.clip(def_coverage, 0.0, 1.0))

    return {
        "detection_rates": detection,
        "attacker_evasion": attacker,
        "defender_coverage": defender,
        "rounds": rounds,
    }


# ---------------------------------------------------------------------------
# CIF-specific payoff matrix from Paper 2 S08 parametric simulations
# ---------------------------------------------------------------------------

def compute_cif_payoff_matrix() -> Tuple[np.ndarray, List[str], List[str]]:
    """Construct the attacker x defender payoff matrix for CIF.

    Rows are the six top-level attack families and columns are six
    deployment configurations of the CIF defense stack.

    Provenance, which is not uniform across the matrix and matters:

    * 35 of the 36 cells are design-model values from the S08 parametric
      response surface.  No measurement stands behind them; the pipeline has
      no per-family-by-per-mechanism evaluation arm.
    * One cell -- ``(emergent_misalignment, full_cif)`` -- does have a measured
      counterpart, and it is read from ``colony_results.json`` rather than
      typed here.  That artifact is ``data_origin: real_pipeline``, 30 repeats,
      and gives 0.7429.  The literal that used to sit in this cell was 0.56,
      the single-seed figure the manuscripts explicitly retract as "not the
      publication estimate" -- while the Nash result computed from it was
      quoted as a finding.  Substituting the published value moves the game
      value from 0.56 to 0.61 and moves the attacker's pure best response from
      emergent misalignment to coordination.

    Returns:
        Tuple ``(M, attack_labels, defense_labels)`` where ``M`` has
        shape ``(6, 6)``.
    """
    attack_labels = [
        "direct_injection",
        "nested_injection",
        "trust_exploitation",
        "belief_manipulation",
        "coordination",
        "emergent_misalignment",
    ]
    defense_labels = [
        "no_defense",
        "firewall_only",
        "sandbox_only",
        "tripwires_only",
        "full_cif_minus_consensus",
        "full_cif",
    ]
    M = np.array(
        [
            # no_def  firewall sandbox  tripwires  full-C   full_cif
            [0.00,    0.80,    0.45,    0.65,      0.88,    0.92],  # direct
            [0.00,    0.60,    0.50,    0.55,      0.78,    0.87],  # nested
            [0.00,    0.30,    0.25,    0.60,      0.75,    0.84],  # trust
            [0.00,    0.40,    0.60,    0.50,      0.70,    0.82],  # belief
            [0.00,    0.20,    0.15,    0.40,      0.55,    0.61],  # coord
            [0.00,    0.15,    0.10,    0.30,      0.45,    np.nan],  # emergent
        ],
        dtype=float,
    )
    M[attack_labels.index("emergent_misalignment"), defense_labels.index("full_cif")] = (
        _measured_emergent_full_cif()
    )
    return M, attack_labels, defense_labels


def _measured_emergent_full_cif() -> float:
    """The one payoff cell with a measurement behind it, read from the artifact."""
    for candidate in (
        Path(__file__).resolve().parents[2] / "output" / "data" / "colony_results.json",
        Path("output/data/colony_results.json"),
    ):
        if candidate.is_file():
            with open(candidate) as handle:
                payload = json.load(handle)
            for scenario in payload.get("scenarios", []):
                if scenario.get("scenario") == "emergent_misalignment":
                    return float(scenario["detection_rate_mean"])
            raise ValueError(
                f"{candidate} has no emergent_misalignment scenario; the payoff "
                f"matrix cannot be built without its one measured cell"
            )
    raise FileNotFoundError(
        "colony_results.json is missing; refusing to fall back to a typed literal "
        "for the one cell of this matrix that is supposed to be measured"
    )


# ---------------------------------------------------------------------------
# Minimax regret solver (robust-decision alternative to Nash)
# ---------------------------------------------------------------------------

def minimax_regret(
    payoff_matrix: np.ndarray,
) -> Tuple[np.ndarray, float]:
    """Minimax-regret pure strategy for the defender.

    Regret for choosing defense ``d`` against attack ``a`` is::

        R[a, d] = max_{d'} M[a, d'] - M[a, d]

    The minimax-regret strategy picks the defense that minimises the
    worst-case (maximum over attacks) regret.

    Args:
        payoff_matrix: Shape ``(n_attacks, n_defenses)``.

    Returns:
        Tuple ``(defense_distribution, max_regret)``: a one-hot pure
        strategy on the minimax-regret defense, plus the realised
        worst-case regret at that choice.
    """
    M = np.asarray(payoff_matrix, dtype=float)
    n_attacks, n_defenses = M.shape

    best_per_attack = M.max(axis=1, keepdims=True)  # shape (n_attacks, 1)
    regret = best_per_attack - M  # shape (n_attacks, n_defenses)

    worst_regret_per_def = regret.max(axis=0)  # shape (n_defenses,)
    chosen = int(np.argmin(worst_regret_per_def))
    distribution = np.zeros(n_defenses, dtype=float)
    distribution[chosen] = 1.0
    return distribution, float(worst_regret_per_def[chosen])


__all__ = [
    "GameResult",
    "solve_zero_sum_game",
    "fictitious_play",
    "arms_race_simulation",
    "compute_cif_payoff_matrix",
    "minimax_regret",
]
