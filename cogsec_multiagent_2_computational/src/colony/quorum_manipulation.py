"""Omega_3 scenario: adversaries target quorum-based decisions.

Three adversary agents strategically vote on quorum decisions to flip
outcomes.  A quorum requires 2/3 agreement.  Integrity is tracked as the
fraction of decisions that match the ground truth.
"""

from __future__ import annotations

from typing import Any, List

import numpy as np

from .scorecard import compute_ccs, compute_recovery_steps, compute_resilience


class QuorumManipulationScenario:
    """Omega_3 scenario: adversaries manipulate quorum votes.

    Three strategic adversaries attempt to exploit the 2/3 quorum
    requirement to either block correct decisions or push incorrect ones.
    """

    @property
    def name(self) -> str:
        return "quorum_manipulation"

    def default_config(self) -> Any:
        """Return default colony configuration for this scenario."""
        try:
            from .benchmark import ColonyConfig
            return ColonyConfig(
                n_agents=30, n_steps=200, n_adversaries=3,
                adversary_fraction=3 / 30, seed=42,
            )
        except ImportError:
            from dataclasses import dataclass as _dc
            @_dc
            class _Cfg:
                n_agents: int = 30
                n_steps: int = 200
                n_adversaries: int = 3
                adversary_fraction: float = 0.1
                seed: int = 42
            return _Cfg()

    def run(self, config: Any, rng: np.random.Generator) -> Any:
        """Run the quorum-manipulation simulation.

        Args:
            config: ColonyConfig with n_agents, n_steps, n_adversaries.
            rng: numpy Generator for reproducibility.

        Returns:
            ColonyResult with detection metrics.
        """
        try:
            from .benchmark import ColonyResult
        except ImportError:
            from .recruitment_poisoning import (
                _ColonyResult as ColonyResult,  # type: ignore[assignment]
            )

        n = config.n_agents
        n_adv = config.n_adversaries
        n_steps = config.n_steps
        quorum_fraction = 2.0 / 3.0

        adv_indices = list(range(n - n_adv, n))
        honest_indices = list(range(n - n_adv))

        # Adversaries become active at step 30
        adv_active_step = 30

        timeline: List[float] = []
        detections = 0
        detection_opportunities = 0
        false_positives = 0
        honest_checks = 0

        for step in range(n_steps):
            # Ground truth for this step's decision (binary, alternating)
            ground_truth = 1 if (step % 2 == 0) else 0

            # -- Generate votes (binary: 0 or 1) --
            votes = np.zeros(n, dtype=np.int32)

            # Honest agents vote correctly with p=0.85
            for h in honest_indices:
                if rng.random() < 0.85:
                    votes[h] = ground_truth
                else:
                    votes[h] = 1 - ground_truth

            # Adversary votes
            for a in adv_indices:
                if step < adv_active_step:
                    # Blend in -- vote correctly
                    if rng.random() < 0.85:
                        votes[a] = ground_truth
                    else:
                        votes[a] = 1 - ground_truth
                else:
                    # Strategically vote wrong to disrupt quorum
                    votes[a] = 1 - ground_truth

            # -- Quorum decision --
            agree_count = int(np.sum(votes == ground_truth))
            quorum_met = agree_count >= int(np.ceil(n * quorum_fraction))
            decision_correct = 1.0 if quorum_met else 0.0

            # -- Detection: monitor for persistent incorrect voters --
            if step >= adv_active_step:
                for a in adv_indices:
                    detection_opportunities += 1
                    if votes[a] != ground_truth:
                        detections += 1

                for h in honest_indices:
                    honest_checks += 1
                    if votes[h] != ground_truth:
                        false_positives += 1

            timeline.append(decision_correct)

        # Aggregate metrics
        dr = detections / max(detection_opportunities, 1)
        fpr = false_positives / max(honest_checks, 1)
        res = compute_resilience(timeline, adversary_start_step=adv_active_step)
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
