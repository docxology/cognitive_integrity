"""Omega_2 scenario: adversary joins trusted set via gradual reputation building.

Adversary agents start with normal behaviour, gradually build trust over an
initial phase, then exploit their position to shift colony beliefs.  Honest
agents use an exponential moving average of peer beliefs.  Detection monitors
for sudden belief changes after the trust-establishment phase.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Forward-declared types to avoid circular imports at module level.
# The actual ColonyConfig / ColonyResult / ColonyScenario are defined in
# benchmark.py; we import them lazily to keep the module self-contained.
# ---------------------------------------------------------------------------
from dataclasses import dataclass
from typing import List

import numpy as np

from .scorecard import compute_ccs, compute_recovery_steps, compute_resilience


@dataclass
class _ColonyConfig:
    """Lightweight mirror -- real one lives in benchmark.py."""
    n_agents: int = 20
    n_steps: int = 100
    n_adversaries: int = 2
    adversary_fraction: float = 0.1
    seed: int = 42


@dataclass
class _ColonyResult:
    scenario_name: str = ""
    config: object = None
    detection_rate: float = 0.0
    false_positive_rate: float = 0.0
    resilience_score: float = 0.0
    recovery_steps: int = 0
    ccs_score: float = 0.0
    timeline: List[float] = None  # type: ignore[assignment]

    def __post_init__(self):
        if self.timeline is None:
            self.timeline = []


class RecruitmentPoisoningScenario:
    """Omega_2 scenario: adversary builds trust then exploits it.

    Two adversary agents behave honestly for a trust-building phase,
    then begin injecting manipulated beliefs once they have gained
    sufficient reputation among the colony.
    """

    @property
    def name(self) -> str:
        return "recruitment_poisoning"

    def default_config(self):
        """Return default colony configuration for this scenario."""
        # Import here to avoid circular; benchmark.py imports this module
        try:
            from .benchmark import ColonyConfig
            return ColonyConfig(
                n_agents=20, n_steps=100, n_adversaries=2,
                adversary_fraction=2 / 20, seed=42,
            )
        except ImportError:
            return _ColonyConfig()

    # ------------------------------------------------------------------
    # Simulation
    # ------------------------------------------------------------------

    def run(self, config, rng: np.random.Generator):
        """Run the recruitment-poisoning simulation.

        Args:
            config: ColonyConfig (or duck-typed equivalent).
            rng: numpy Generator for reproducibility.

        Returns:
            ColonyResult with detection metrics.
        """
        try:
            from .benchmark import ColonyResult
        except ImportError:
            ColonyResult = _ColonyResult  # type: ignore[misc]

        n = config.n_agents
        n_adv = config.n_adversaries
        n_steps = config.n_steps

        # Ground-truth belief is 0.5 (neutral)
        ground_truth = 0.5
        # Adversary target is 0.9 (far from truth)
        adversary_target = 0.9

        # Initial beliefs -- all agents start near ground truth
        beliefs = np.full(n, ground_truth, dtype=np.float64)
        beliefs += rng.normal(0, 0.02, size=n)
        beliefs = np.clip(beliefs, 0.0, 1.0)

        # Adversary indices are the last n_adv agents
        adv_indices = set(range(n - n_adv, n))
        honest_indices = set(range(n - n_adv))

        # Trust scores (all start at 0.5)
        trust = np.full(n, 0.5, dtype=np.float64)

        # Trust-building phase: first 40 % of steps
        trust_phase_end = int(0.4 * n_steps)

        # EMA smoothing factor for honest agents
        alpha = 0.15

        # Detection threshold — lowered for catching subtler manipulation
        detection_threshold = 0.08

        timeline: List[float] = []
        detections = 0
        detection_opportunities = 0
        false_positives = 0
        honest_checks = 0

        # Track which agents have been flagged as adversaries
        flagged_agents: set = set()

        for step in range(n_steps):
            # -- Adversary behaviour --
            for a in adv_indices:
                if step < trust_phase_end:
                    # Behave honestly to build trust
                    beliefs[a] = ground_truth + rng.normal(0, 0.02)
                    trust[a] = min(1.0, trust[a] + 0.01)
                else:
                    # Gradually shift toward adversary target
                    progress = (step - trust_phase_end) / max(n_steps - trust_phase_end, 1)
                    beliefs[a] = ground_truth + (adversary_target - ground_truth) * progress
                    beliefs[a] += rng.normal(0, 0.01)

            beliefs = np.clip(beliefs, 0.0, 1.0)

            # -- Honest agents update via trust-weighted EMA of peers --
            new_beliefs = beliefs.copy()
            for h in honest_indices:
                # Weighted average of peer beliefs
                peer_sum = 0.0
                weight_sum = 0.0
                for j in range(n):
                    if j == h:
                        continue
                    w = trust[j]
                    peer_sum += w * beliefs[j]
                    weight_sum += w
                if weight_sum > 0:
                    peer_avg = peer_sum / weight_sum
                    new_beliefs[h] = (1 - alpha) * beliefs[h] + alpha * peer_avg

            # -- Detection: flag belief changes with lowered threshold --
            if step > trust_phase_end:
                for a in adv_indices:
                    detection_opportunities += 1
                    shift = abs(beliefs[a] - ground_truth)
                    if shift > detection_threshold:
                        detections += 1
                        flagged_agents.add(a)

                        # Active response: reduce trust of detected adversary
                        trust[a] = max(0.0, trust[a] * 0.5)

                for h in honest_indices:
                    honest_checks += 1
                    shift = abs(new_beliefs[h] - ground_truth)
                    if shift > detection_threshold:
                        false_positives += 1

                # -- Belief correction: if adversaries detected, honest agents
                #    revert toward colony mean (excluding flagged agents) --
                if flagged_agents:
                    unflagged = [i for i in range(n) if i not in flagged_agents]
                    if unflagged:
                        colony_mean = float(np.mean(beliefs[unflagged]))
                        for h in honest_indices:
                            # Gently correct toward the unflagged colony mean
                            correction_strength = 0.1
                            new_beliefs[h] = (1 - correction_strength) * new_beliefs[h] + correction_strength * colony_mean

            beliefs = np.clip(new_beliefs, 0.0, 1.0)

            # -- Trust update for honest agents (observe peer accuracy) --
            for h in honest_indices:
                for j in range(n):
                    if j == h:
                        continue
                    accuracy = 1.0 - abs(beliefs[j] - ground_truth)
                    trust[j] = 0.95 * trust[j] + 0.05 * accuracy
            trust = np.clip(trust, 0.0, 1.0)

            # Colony integrity = fraction of honest agents within 0.07 of truth
            correct = np.sum(np.abs(beliefs[:n - n_adv] - ground_truth) < 0.07)
            integrity = float(correct / max(len(honest_indices), 1))
            timeline.append(integrity)

        # Compute aggregate metrics
        dr = detections / max(detection_opportunities, 1)
        fpr = false_positives / max(honest_checks, 1)
        res = compute_resilience(timeline, adversary_start_step=trust_phase_end)
        rec = compute_recovery_steps(timeline, threshold=0.9)
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
