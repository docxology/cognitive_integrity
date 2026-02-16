"""Master data generation for all experiments.

Provides a :class:`DataGenerator` that produces reproducible synthetic
datasets for detection, scalability, ablation, and colony benchmarks.
All randomness is controlled by a single seed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import numpy as np

from .schema import AblationData, ColonyData, DetectionData, ScalabilityData

_ARCHITECTURES = [
    "Claude Code", "AutoGPT", "CrewAI", "LangGraph", "MetaGPT", "CAMEL",
]
_CATEGORIES = ["Injection", "Trust Exploitation", "Belief Manipulation", "Coordination"]


class DataGenerator:
    """Reproducible data generator for all experimental datasets.

    Parameters
    ----------
    seed : int
        Master random seed for reproducibility.
    output_dir : str
        Directory for saving generated data.
    """

    def __init__(self, seed: int = 42, output_dir: str = "output/data") -> None:
        self.seed = seed
        self.output_dir = Path(output_dir)
        self._rng = np.random.default_rng(seed)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_all(self) -> Dict[str, Any]:
        """Generate and save all experimental datasets.

        Returns
        -------
        dict
            Mapping of dataset name to its typed data object.
        """
        datasets = {
            "detection": self.generate_detection_data(),
            "scalability": self.generate_scalability_data(),
            "ablation": self.generate_ablation_data(),
            "colony": self.generate_colony_data(),
        }
        for name, data in datasets.items():
            self.save(data.to_dict(), f"{name}_data.json")
        return datasets

    def generate_detection_data(self) -> DetectionData:
        """Generate 6x4 detection matrix data.

        Returns
        -------
        DetectionData
        """
        base_means = np.array([
            [0.98, 0.94, 0.91, 0.96],
            [0.95, 0.90, 0.88, 0.93],
            [0.96, 0.92, 0.89, 0.94],
            [0.97, 0.93, 0.90, 0.95],
            [0.94, 0.89, 0.86, 0.92],
            [0.93, 0.87, 0.82, 0.90],
        ])
        noise = self._rng.normal(0, 0.005, base_means.shape)
        means = np.clip(base_means + noise, 0.80, 0.99)
        cis = self._rng.uniform(0.008, 0.025, means.shape)

        return DetectionData(
            architectures=_ARCHITECTURES,
            categories=_CATEGORIES,
            means=means.tolist(),
            cis=cis.tolist(),
            seed=self.seed,
        )

    def generate_scalability_data(self) -> ScalabilityData:
        """Generate agent count sweep data.

        Returns
        -------
        ScalabilityData
        """
        agents = [2, 3, 5, 7, 10, 15, 20, 30, 50, 100]
        agents_arr = np.array(agents, dtype=float)

        latency = (
            5.0
            + 0.02 * agents_arr ** 2
            + 1.5 * agents_arr
            + self._rng.normal(0, 2, len(agents))
        )
        latency = np.maximum(latency, 5.0)

        memory = (
            50.0
            + 8.0 * agents_arr
            + 0.05 * agents_arr ** 1.3
            + self._rng.normal(0, 5, len(agents))
        )
        memory = np.maximum(memory, 50.0)

        # Regression
        coeffs = np.polyfit(agents_arr, latency, 2)
        predicted = np.polyval(coeffs, agents_arr)
        ss_res = float(np.sum((latency - predicted) ** 2))
        ss_tot = float(np.sum((latency - latency.mean()) ** 2))
        r_sq = 1.0 - ss_res / ss_tot

        return ScalabilityData(
            agent_counts=agents,
            latency_ms=latency.tolist(),
            memory_mb=memory.tolist(),
            regression_coeffs=coeffs.tolist(),
            r_squared=r_sq,
            seed=self.seed,
        )

    def generate_ablation_data(self) -> AblationData:
        """Generate component removal data.

        Returns
        -------
        AblationData
        """
        configs = [
            "Full CIF",
            "- Firewall",
            "- Trust Calculus",
            "- Drift Detection",
            "- Consensus",
            "- Tripwire",
            "- Invariant Check",
            "- Provenance",
            "- Sandbox",
        ]
        base_rates = [0.965, 0.82, 0.87, 0.91, 0.90, 0.93, 0.92, 0.94, 0.95]
        noise = self._rng.normal(0, 0.003, len(configs))
        rates = np.clip(np.array(base_rates) + noise, 0.78, 0.99).tolist()
        cis = self._rng.uniform(0.008, 0.025, len(configs)).tolist()

        return AblationData(
            configurations=configs,
            detection_rates=rates,
            cis=cis,
            seed=self.seed,
        )

    def generate_colony_data(self) -> ColonyData:
        """Generate colony benchmark data.

        Returns
        -------
        ColonyData
        """
        sizes = [3, 5, 10, 20, 50]
        sizes_arr = np.array(sizes, dtype=float)

        convergence = (10 + 2.5 * sizes_arr + self._rng.normal(0, 2, len(sizes))).astype(int).tolist()
        integrity = np.clip(
            0.98 - 0.001 * sizes_arr + self._rng.normal(0, 0.005, len(sizes)),
            0.90, 0.99,
        ).tolist()
        attack_rate = np.clip(
            0.02 + 0.002 * sizes_arr + self._rng.normal(0, 0.005, len(sizes)),
            0.01, 0.15,
        ).tolist()

        return ColonyData(
            colony_sizes=sizes,
            convergence_steps=convergence,
            integrity_scores=integrity,
            attack_success_rate=attack_rate,
            seed=self.seed,
        )

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, data: Dict[str, Any], filename: str) -> str:
        """Save data dictionary to JSON.

        Parameters
        ----------
        data : dict
            Data to serialise.
        filename : str
            Output filename (relative to ``output_dir``).

        Returns
        -------
        str
            Full path of saved file.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        return str(path)
