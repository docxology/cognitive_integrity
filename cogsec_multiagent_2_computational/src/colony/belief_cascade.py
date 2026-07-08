"""Omega_2 scenario: manipulated beliefs cascade through network.

Two well-positioned adversaries inject false beliefs that propagate through
a small-world connectivity network.  Each honest agent updates beliefs as a
weighted average of its neighbours.  The simulation tracks cascade depth and
colony integrity over time.
"""

from __future__ import annotations

from typing import Any, List

import numpy as np

from .scorecard import compute_ccs, compute_recovery_steps, compute_resilience

# Network topology parameters
SMALL_WORLD_K = 6  # Each node connects to k/2 neighbours on each side
SMALL_WORLD_REWIRE_P = 0.1  # Rewiring probability for small-world construction

# Belief dynamics parameters
GROUND_TRUTH_BELIEF = 0.5  # Target belief value for honest agents
ADVERSARY_TARGET_BELIEF = 0.95  # Target belief value for adversaries
BELIEF_UPDATE_WEIGHT = 0.2  # How much neighbours influence each other
BELIEF_NOISE_SIGMA = 0.02  # Standard deviation of belief noise for honest agents
ADVERSARY_NOISE_SIGMA = 0.01  # Standard deviation of belief noise for adversaries

# Timing and detection parameters
ADVERSARY_ACTIVATION_STEP = 30  # When adversaries start injecting false beliefs
BELIEF_DEVIATION_THRESHOLD = 0.2  # Threshold for detecting belief deviation
INTEGRITY_TARGET_THRESHOLD = 0.1  # Distance threshold for integrity computation
RECOVERY_INTEGRITY_THRESHOLD = 0.9  # Integrity threshold for recovery evaluation


def _build_small_world_adjacency(
    n: int, k: int, p: float, rng: np.random.Generator
) -> np.ndarray:
    """Build a Watts-Strogatz small-world adjacency matrix.

    Args:
        n: Number of nodes.
        k: Each node connects to k/2 neighbours on each side (must be even).
        p: Rewiring probability.
        rng: Random generator.

    Returns:
        n x n symmetric binary adjacency matrix.
    """
    k = max(k, 2)
    if k % 2 != 0:
        k += 1

    adj = np.zeros((n, n), dtype=np.float64)

    # Ring lattice
    for i in range(n):
        for j in range(1, k // 2 + 1):
            right = (i + j) % n
            adj[i, right] = 1.0
            adj[right, i] = 1.0

    # Rewire with probability p
    for i in range(n):
        for j in range(1, k // 2 + 1):
            if rng.random() < p:
                right = (i + j) % n
                # Remove existing edge
                adj[i, right] = 0.0
                adj[right, i] = 0.0
                # Add random edge (avoid self-loops and duplicates)
                candidates = [
                    x for x in range(n)
                    if x != i and adj[i, x] == 0.0
                ]
                if candidates:
                    new_target = rng.choice(candidates)
                    adj[i, new_target] = 1.0
                    adj[new_target, i] = 1.0

    return adj


class BeliefCascadeScenario:
    """Omega_2 scenario: belief cascade through small-world network.

    Two adversaries positioned at high-connectivity nodes inject false
    beliefs that propagate through the network topology.
    """

    @property
    def name(self) -> str:
        return "belief_cascade"

    def default_config(self) -> Any:
        """Return default colony configuration for this scenario."""
        try:
            from .benchmark import ColonyConfig
            return ColonyConfig(
                n_agents=100, n_steps=300, n_adversaries=2,
                adversary_fraction=2 / 100, seed=42,
            )
        except ImportError:
            from dataclasses import dataclass as _dc
            @_dc
            class _Cfg:
                n_agents: int = 100
                n_steps: int = 300
                n_adversaries: int = 2
                adversary_fraction: float = 0.02
                seed: int = 42
            return _Cfg()

    def run(self, config: Any, rng: np.random.Generator) -> Any:
        """Run the belief-cascade simulation.

        Args:
            config: ColonyConfig with n_agents, n_steps, n_adversaries.
            rng: numpy Generator for reproducibility.

        Returns:
            ColonyResult with detection metrics and cascade timeline.
        """
        try:
            from .benchmark import ColonyResult
        except ImportError:
            from .recruitment_poisoning import (  # type: ignore[assignment]
                _ColonyResult as ColonyResult,
            )

        n = config.n_agents
        n_adv = config.n_adversaries
        n_steps = config.n_steps

        # Build small-world network
        adj = _build_small_world_adjacency(n, k=SMALL_WORLD_K, p=SMALL_WORLD_REWIRE_P, rng=rng)

        # Pick adversary positions: highest-degree nodes
        degrees = adj.sum(axis=1)
        adv_indices = set(np.argsort(degrees)[-n_adv:].tolist())
        honest_indices = set(range(n)) - adv_indices

        # Ground truth and adversary target beliefs
        ground_truth = GROUND_TRUTH_BELIEF
        adversary_target = ADVERSARY_TARGET_BELIEF

        beliefs = np.full(n, ground_truth, dtype=np.float64)
        beliefs += rng.normal(0, BELIEF_NOISE_SIGMA, size=n)
        beliefs = np.clip(beliefs, 0.0, 1.0)

        # Adversaries become active at configured step
        adv_active_step = ADVERSARY_ACTIVATION_STEP
        update_weight = BELIEF_UPDATE_WEIGHT

        timeline: List[float] = []
        detections = 0
        detection_opportunities = 0
        false_positives = 0
        honest_checks = 0

        for step in range(n_steps):
            # -- Adversary behaviour --
            for a in adv_indices:
                if step >= adv_active_step:
                    beliefs[a] = adversary_target + rng.normal(0, ADVERSARY_NOISE_SIGMA)
                else:
                    beliefs[a] = ground_truth + rng.normal(0, BELIEF_NOISE_SIGMA)

            beliefs = np.clip(beliefs, 0.0, 1.0)

            # -- Honest agents: weighted average of neighbours --
            new_beliefs = beliefs.copy()
            for h in honest_indices:
                neighbours = np.where(adj[h] > 0)[0]
                if len(neighbours) == 0:
                    continue
                neighbour_avg = float(np.mean(beliefs[neighbours]))
                new_beliefs[h] = (1 - update_weight) * beliefs[h] + update_weight * neighbour_avg

            # -- Detection: look for belief deviation --
            if step >= adv_active_step:
                for a in adv_indices:
                    detection_opportunities += 1
                    if abs(beliefs[a] - ground_truth) > BELIEF_DEVIATION_THRESHOLD:
                        detections += 1

                for h in honest_indices:
                    honest_checks += 1
                    if abs(new_beliefs[h] - ground_truth) > BELIEF_DEVIATION_THRESHOLD:
                        false_positives += 1

            beliefs = np.clip(new_beliefs, 0.0, 1.0)

            # Integrity = fraction of honest agents within threshold of truth
            honest_list = sorted(honest_indices)
            correct = np.sum(np.abs(beliefs[honest_list] - ground_truth) < INTEGRITY_TARGET_THRESHOLD)  # noqa: E501
            integrity = float(correct / max(len(honest_indices), 1))
            timeline.append(integrity)

        # Aggregate metrics
        dr = detections / max(detection_opportunities, 1)
        fpr = false_positives / max(honest_checks, 1)
        res = compute_resilience(timeline, adversary_start_step=adv_active_step)
        rec = compute_recovery_steps(timeline, threshold=RECOVERY_INTEGRITY_THRESHOLD)
        ccs = compute_ccs(dr, fpr, res, rec, n_steps)

        return ColonyResult(
            scenario_name=self.name,
            config=config,
            detection_rate=dr,
            false_positive_rate=fpr,
            resilience_score=res,
            recovery_steps=rec,
            ccs_score=ccs,
            timeline=timeline,
        )
