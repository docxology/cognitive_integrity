"""No adversary scenario: emergent misalignment from accumulated errors.

No adversary is present.  Each agent has small random noise (std=0.01) per
step.  Over 1000 steps, cumulative drift can cause the colony to become
misaligned from its initial state.  This tests whether the system can
detect *organic* drift.
"""

from __future__ import annotations

from typing import Any, List

import numpy as np

from .scorecard import compute_ccs, compute_recovery_steps, compute_resilience


class EmergentMisalignmentScenario:
    """No-adversary scenario: misalignment from accumulated random errors.

    All agents are honest but accumulate small random perturbations each
    step.  Over many steps the colony drifts away from the initial ground
    truth.
    """

    @property
    def name(self) -> str:
        return "emergent_misalignment"

    def default_config(self) -> Any:
        """Return default colony configuration for this scenario."""
        try:
            from .benchmark import ColonyConfig
            return ColonyConfig(
                n_agents=50, n_steps=1000, n_adversaries=0,
                adversary_fraction=0.0, seed=42,
            )
        except ImportError:
            from dataclasses import dataclass as _dc
            @_dc
            class _Cfg:
                n_agents: int = 50
                n_steps: int = 1000
                n_adversaries: int = 0
                adversary_fraction: float = 0.0
                seed: int = 42
            return _Cfg()

    def run(self, config: Any, rng: np.random.Generator) -> Any:
        """Run the emergent-misalignment simulation.

        Args:
            config: ColonyConfig with n_agents, n_steps.
            rng: numpy Generator for reproducibility.

        Returns:
            ColonyResult capturing drift metrics over time.
        """
        try:
            from .benchmark import ColonyResult
        except ImportError:
            from .recruitment_poisoning import (  # type: ignore[assignment]
                _ColonyResult as ColonyResult,
            )

        n = config.n_agents
        n_steps = config.n_steps

        # Ground truth = 0.5; all agents start exactly here
        ground_truth = 0.5
        noise_std = 0.015  # Increased from 0.01 for faster drift accumulation

        beliefs = np.full(n, ground_truth, dtype=np.float64)

        # Agents share information via averaging with peers
        peer_weight = 0.05  # Lower peer anchoring allows more individual drift

        timeline: List[float] = []
        drift_detected = 0
        drift_checks = 0
        false_positives = 0
        honest_checks = 0

        # Detection thresholds
        point_drift_threshold = 0.02  # Lowered from 0.05 for earlier detection
        trend_window = 20  # Sliding window for trend-based drift detection

        # Track mean belief history for trend detection
        mean_history: List[float] = []

        for step in range(n_steps):
            # -- Each agent gets a small random perturbation --
            perturbation = rng.normal(0, noise_std, size=n)
            beliefs += perturbation

            # -- Peer averaging (each agent averages with 3 random peers) --
            new_beliefs = beliefs.copy()
            for i in range(n):
                peers = rng.choice(n, size=min(3, n - 1), replace=False)
                # Exclude self from peers
                peers = peers[peers != i]
                if len(peers) > 0:
                    peer_avg = float(np.mean(beliefs[peers]))
                    new_beliefs[i] = (1 - peer_weight) * beliefs[i] + peer_weight * peer_avg

            beliefs = np.clip(new_beliefs, 0.0, 1.0)

            # -- Track mean for trend detection --
            current_mean = float(np.mean(beliefs))
            mean_history.append(current_mean)

            # -- Drift detection: multi-signal approach --
            mean_drift = abs(current_mean - ground_truth)
            drift_checks += 1

            # Signal 1: Point drift threshold
            point_detected = mean_drift > point_drift_threshold

            # Signal 2: Trend detection via sliding window
            trend_detected = False
            if len(mean_history) >= trend_window:
                window = mean_history[-trend_window:]
                window_start = np.mean(window[:trend_window // 2])
                window_end = np.mean(window[trend_window // 2:])
                trend_magnitude = abs(window_end - window_start)
                if trend_magnitude > 0.005:  # Detect systematic drift trends
                    trend_detected = True

            if point_detected or trend_detected:
                drift_detected += 1

            # -- False positive tracking --
            for i in range(n):
                honest_checks += 1
                individual_drift = abs(beliefs[i] - ground_truth)
                if individual_drift > point_drift_threshold and mean_drift <= point_drift_threshold:
                    # Flagged an agent when colony-level drift is small
                    false_positives += 1

            # Integrity = fraction of agents within 0.03 of ground truth
            correct = np.sum(np.abs(beliefs - ground_truth) < 0.03)
            integrity = float(correct / n)
            timeline.append(integrity)

        # In a no-adversary scenario, detection rate is how well we spot
        # organic drift; false positive rate should be low
        dr = drift_detected / max(drift_checks, 1)
        fpr = false_positives / max(honest_checks, 1)
        # Resilience is 1.0 since there is no attack per se
        res = compute_resilience(timeline, adversary_start_step=0)
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
