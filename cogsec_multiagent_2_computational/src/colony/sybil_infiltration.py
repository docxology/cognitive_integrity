"""Omega_4 scenario: coordinated fake identities infiltrate colony.

Four sybil agents coordinate to shift consensus.  Each sybil votes
identically on every proposition.  Honest agents use majority rule with
trust weighting.  Integrity is tracked as the fraction of correct
consensus decisions.
"""

from __future__ import annotations

from typing import Any, List

import numpy as np

from .scorecard import compute_ccs, compute_recovery_steps, compute_resilience


class SybilInfiltrationScenario:
    """Omega_4 scenario: sybil agents coordinate to flip consensus.

    Four coordinated sybil identities join the colony and vote as a block,
    attempting to shift majority consensus away from the ground truth.
    """

    @property
    def name(self) -> str:
        return "sybil_infiltration"

    def default_config(self) -> Any:
        """Return default colony configuration for this scenario."""
        try:
            from .benchmark import ColonyConfig
            return ColonyConfig(
                n_agents=50, n_steps=500, n_adversaries=4,
                adversary_fraction=4 / 50, seed=42,
            )
        except ImportError:
            from dataclasses import dataclass as _dc
            @_dc
            class _Cfg:
                n_agents: int = 50
                n_steps: int = 500
                n_adversaries: int = 4
                adversary_fraction: float = 0.08
                seed: int = 42
            return _Cfg()

    def run(self, config: Any, rng: np.random.Generator) -> Any:
        """Run the sybil-infiltration simulation.

        Args:
            config: ColonyConfig with n_agents, n_steps, n_adversaries.
            rng: numpy Generator for reproducibility.

        Returns:
            ColonyResult with detection metrics.
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

        # Sybil indices are the last n_adv agents
        adv_indices = list(range(n - n_adv, n))
        honest_indices = list(range(n - n_adv))

        # Trust weights -- sybils start with moderate trust
        trust = np.full(n, 0.5, dtype=np.float64)

        # Each step is a binary consensus decision (ground truth = 1)
        ground_truth = 1
        sybil_vote = 0  # Sybils always vote opposite

        timeline: List[float] = []
        detections = 0
        detection_opportunities = 0
        false_positives = 0
        honest_checks = 0

        # Sybils become active at step 50 (after blending in)
        sybil_active_step = 50

        for step in range(n_steps):
            # -- Generate votes --
            votes = np.zeros(n, dtype=np.float64)

            # Honest agents vote correctly with some noise
            for h in honest_indices:
                noise = rng.normal(0, 0.1)
                votes[h] = float(ground_truth) + noise

            # Sybil agents
            for a in adv_indices:
                if step < sybil_active_step:
                    # Blend in -- vote correctly
                    votes[a] = float(ground_truth) + rng.normal(0, 0.1)
                else:
                    # All sybils vote identically (coordinated)
                    votes[a] = float(sybil_vote)

            votes = np.clip(votes, 0.0, 1.0)

            # -- Trust-weighted majority decision --
            weighted_sum = np.sum(trust * votes)
            weighted_total = np.sum(trust)
            decision = 1 if (weighted_sum / max(weighted_total, 1e-9)) > 0.5 else 0

            # Track correctness
            correct = int(decision == ground_truth)

            # -- Detection: identify coordinated identical votes --
            if step >= sybil_active_step:
                adv_votes = votes[adv_indices]
                vote_spread = float(np.std(adv_votes))

                for a in adv_indices:
                    detection_opportunities += 1
                    # Detect if vote is far from truth AND coordinated
                    if abs(votes[a] - ground_truth) > 0.4 and vote_spread < 0.05:
                        detections += 1

                for h in honest_indices:
                    honest_checks += 1
                    # False positive if honest agent flagged
                    if abs(votes[h] - ground_truth) > 0.4:
                        false_positives += 1

            # -- Update trust based on vote accuracy --
            for j in range(n):
                accuracy = 1.0 - abs(votes[j] - ground_truth)
                trust[j] = 0.95 * trust[j] + 0.05 * accuracy
            trust = np.clip(trust, 0.0, 1.0)

            timeline.append(float(correct))

        # Compute aggregate metrics
        dr = detections / max(detection_opportunities, 1)
        fpr = false_positives / max(honest_checks, 1)
        res = compute_resilience(timeline, adversary_start_step=sybil_active_step)
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
