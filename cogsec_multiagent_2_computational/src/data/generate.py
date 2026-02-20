"""Master data generation for schema validation and development.

Provides a :class:`DataGenerator` that produces reproducible seed
datasets for detection, scalability, ablation, and colony benchmarks.
These datasets are used for schema testing and development bootstrapping;
published results come from the real pipeline scripts (``run_full_evaluation.py``,
``run_ablation.py``, etc.).  All randomness is controlled by a single seed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import numpy as np

from .schema import AblationData, ColonyData, DetectionData, ScalabilityData

_ARCHITECTURES = [
    "Claude Code", "AutoGPT", "CrewAI", "LangGraph",
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

        Produces both the basic seed datasets (detection, scalability,
        ablation, colony) and the pipeline-format result files consumed
        by the visualization and table generation modules.

        Returns
        -------
        dict
            Mapping of dataset name to its typed data object or dict.
        """
        datasets: Dict[str, Any] = {
            "detection": self.generate_detection_data(),
            "scalability": self.generate_scalability_data(),
            "ablation": self.generate_ablation_data(),
            "colony": self.generate_colony_data(),
        }
        for name, data in datasets.items():
            self.save(data.to_dict(), f"{name}_data.json")

        # Pipeline-format result files for visualization modules
        pipeline_datasets = {
            "full_evaluation_results": self.generate_full_evaluation_results(),
            "ablation_results": self.generate_ablation_results(),
            "colony_results": self.generate_colony_results(),
            "sensitivity_results": self.generate_sensitivity_results(),
            "cross_validation_results": self.generate_cross_validation_results(),
            "statistical_results": self.generate_statistical_results(),
            "multi_seed_results": self.generate_multi_seed_results(),
        }
        for name, data in pipeline_datasets.items():
            self.save(data, f"{name}.json")
        datasets.update(pipeline_datasets)

        return datasets

    def generate_detection_data(self) -> DetectionData:
        """Generate 4x4 detection matrix data.

        Returns
        -------
        DetectionData
        """
        base_means = np.array([
            [0.98, 0.94, 0.91, 0.96],
            [0.95, 0.90, 0.88, 0.93],
            [0.96, 0.92, 0.89, 0.94],
            [0.97, 0.93, 0.90, 0.95],
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
    # Pipeline-format result generators (for visualization modules)
    # ------------------------------------------------------------------

    def generate_full_evaluation_results(self) -> list:
        """Generate full evaluation results matching run_full_evaluation.py output.

        Produces a list of per-architecture × per-category evaluation
        rows with detection rates, confusion counts, and latency.

        Returns
        -------
        list of dict
        """
        architectures = _ARCHITECTURES
        categories = ["injection", "trust_exploitation",
                       "belief_manipulation", "coordination"]

        base_rates = {
            "Claude Code":  [0.98, 0.94, 0.91, 0.96],
            "AutoGPT":      [0.95, 0.90, 0.88, 0.93],
            "CrewAI":       [0.96, 0.92, 0.89, 0.94],
            "LangGraph":    [0.97, 0.93, 0.90, 0.95],
        }

        results = []
        for arch in architectures:
            for j, cat in enumerate(categories):
                dr = float(np.clip(
                    base_rates[arch][j] + self._rng.normal(0, 0.005),
                    0.80, 0.99,
                ))
                n_attacks = int(self._rng.integers(200, 260))
                tp = int(round(dr * n_attacks))
                fn = n_attacks - tp
                fpr_val = float(np.clip(
                    self._rng.uniform(0.02, 0.08), 0.0, 0.15,
                ))
                n_benign = int(self._rng.integers(80, 120))
                fp = int(round(fpr_val * n_benign))
                tn = n_benign - fp
                latency = float(np.clip(
                    self._rng.normal(12.0, 3.0), 5.0, 30.0,
                ))

                results.append({
                    "architecture": arch,
                    "attack_category": cat,
                    "n_attacks": n_attacks,
                    "true_positives": tp,
                    "false_positives": fp,
                    "true_negatives": tn,
                    "false_negatives": fn,
                    "detection_rate": dr,
                    "false_positive_rate": fpr_val,
                    "avg_latency_ms": latency,
                })
        return results

    def generate_ablation_results(self) -> Dict[str, Any]:
        """Generate ablation results matching run_ablation.py output.

        Produces component removal deltas, minimal config results,
        and pairwise synergy scores.

        Returns
        -------
        dict
        """
        components = [
            "firewall", "trust_calculus", "tripwire", "detection",
            "consensus", "provenance", "sandbox", "invariants",
        ]
        full_tpr = 0.965

        # Component removal: each component's removal drops TPR
        removal = []
        deltas = [0.14, 0.09, 0.06, 0.08, 0.05, 0.04, 0.03, 0.035]
        for i, comp in enumerate(components):
            noise = float(self._rng.normal(0, 0.003))
            tpr = float(np.clip(full_tpr - deltas[i] + noise, 0.78, 0.96))
            removal.append({
                "removed": comp,
                "tpr": tpr,
                "delta_tpr": full_tpr - tpr,
            })

        # Minimal configs
        forward = {
            "components": ["firewall", "detection", "trust_calculus", "tripwire"],
            "tpr": float(np.clip(0.92 + self._rng.normal(0, 0.005), 0.90, 0.95)),
        }
        backward = {
            "components": ["firewall", "detection", "trust_calculus",
                          "tripwire", "consensus"],
            "tpr": float(np.clip(0.93 + self._rng.normal(0, 0.005), 0.90, 0.96)),
        }

        # Top synergies
        pairs = [
            ("firewall", "trust_calculus"),
            ("firewall", "tripwire"),
            ("detection", "consensus"),
            ("trust_calculus", "detection"),
            ("tripwire", "consensus"),
        ]
        synergies = []
        for a, b in pairs:
            syn = float(np.clip(self._rng.normal(0.03, 0.015), -0.02, 0.08))
            synergies.append({"a": a, "b": b, "synergy": syn})

        return {
            "component_removal": removal,
            "minimal_forward": forward,
            "minimal_backward": backward,
            "top_synergies": synergies,
        }

    def generate_colony_results(self) -> list:
        """Generate colony benchmark results matching run_colony_benchmarks.py output.

        Returns
        -------
        list of dict
        """
        scenarios = [
            ("Recruitment Poisoning", 20, 100, 3),
            ("Sybil Infiltration", 50, 100, 5),
            ("Coordinated Attack", 30, 100, 4),
            ("Emergent Misalignment", 40, 100, 0),
            ("Consensus Subversion", 25, 100, 3),
        ]
        results = []
        for name, n_agents, n_steps, n_adv in scenarios:
            dr = float(np.clip(self._rng.normal(0.92, 0.03), 0.80, 0.99))
            fpr = float(np.clip(self._rng.uniform(0.02, 0.06), 0.0, 0.10))
            resilience = float(np.clip(self._rng.normal(0.88, 0.05), 0.70, 0.99))
            recovery = int(np.clip(self._rng.normal(15, 5), 5, 40))
            ccs = float(np.clip(
                0.4 * dr + 0.3 * resilience + 0.2 * (1 - fpr) + 0.1 * (1 - recovery / 100),
                0.0, 1.0,
            ))
            results.append({
                "scenario": name,
                "n_agents": n_agents,
                "n_steps": n_steps,
                "n_adversaries": n_adv,
                "detection_rate": dr,
                "false_positive_rate": fpr,
                "resilience_score": resilience,
                "recovery_steps": recovery,
                "ccs_score": ccs,
            })
        return results

    def generate_sensitivity_results(self) -> Dict[str, Any]:
        """Generate sensitivity results matching run_sensitivity_analysis.py output.

        Returns
        -------
        dict
        """
        params = {
            "injection_threshold": (0.3, 0.9, 0.65),
            "drift_threshold": (0.1, 0.6, 0.25),
            "trust_decay": (0.5, 0.99, 0.85),
            "consensus_quorum": (0.5, 0.9, 0.667),
        }

        sweeps = []
        sensitivity_index = {}
        for param_name, (lo, hi, opt) in params.items():
            values = np.linspace(lo, hi, 25).tolist()
            # Detection rate peaks near optimal and drops away
            metrics = []
            for v in values:
                base = 0.85
                effect = -2.0 * (v - opt) ** 2
                rate = float(np.clip(
                    base + effect + 0.10 + self._rng.normal(0, 0.005),
                    0.60, 0.99,
                ))
                metrics.append(rate)

            best_idx = int(np.argmax(metrics))
            sweeps.append({
                "parameter": param_name,
                "best_value": values[best_idx],
                "best_metric": metrics[best_idx],
                "values": values,
                "metrics": metrics,
            })
            sensitivity_index[param_name] = float(max(metrics) - min(metrics))

        # Grid best for 2D interaction
        grid_best = {
            "injection": float(np.clip(0.65 + self._rng.normal(0, 0.02), 0.55, 0.75)),
            "drift": float(np.clip(0.25 + self._rng.normal(0, 0.02), 0.15, 0.35)),
            "dr": float(np.clip(0.96 + self._rng.normal(0, 0.005), 0.93, 0.99)),
        }

        return {
            "sweeps": sweeps,
            "sensitivity_index": sensitivity_index,
            "grid_best": grid_best,
        }

    def generate_cross_validation_results(self) -> Dict[str, Any]:
        """Generate cross-validation results matching run_cross_validation.py output.

        Returns
        -------
        dict
        """
        k = 5
        folds = []
        tprs, f1s = [], []
        for fold_idx in range(k):
            tpr = float(np.clip(self._rng.normal(0.965, 0.008), 0.93, 0.99))
            fpr = float(np.clip(self._rng.normal(0.04, 0.01), 0.01, 0.08))
            precision = float(np.clip(tpr / (tpr + fpr) if (tpr + fpr) > 0 else 0.0, 0.0, 1.0))
            recall = tpr
            f1 = float(2 * precision * recall / (precision + recall)
                       if (precision + recall) > 0 else 0.0)
            n_samples = int(self._rng.integers(220, 240))

            folds.append({
                "fold": fold_idx,
                "tpr": tpr,
                "fpr": fpr,
                "f1": f1,
                "precision": precision,
                "recall": recall,
                "n_samples": n_samples,
            })
            tprs.append(tpr)
            f1s.append(f1)

        return {
            "k": k,
            "folds": folds,
            "mean_tpr": float(np.mean(tprs)),
            "std_tpr": float(np.std(tprs)),
            "mean_f1": float(np.mean(f1s)),
            "std_f1": float(np.std(f1s)),
        }

    def generate_statistical_results(self) -> Dict[str, Any]:
        """Generate statistical results matching run_statistical_analysis.py output.

        Returns
        -------
        dict
        """
        # H1: CIF > Baseline — strong significance expected
        h1_stat = float(np.clip(self._rng.normal(45.0, 5.0), 30.0, 60.0))
        h1 = {
            "statistic": h1_stat,
            "p_value": float(np.clip(self._rng.exponential(1e-20), 1e-50, 1e-10)),
            "significant": True,
        }

        # H2: CIF > individual components
        component_names = [
            "Firewall", "Trust Calculus", "Tripwire", "Detection",
            "Consensus", "Provenance", "Sandbox", "Invariants",
        ]
        h2 = []
        for name in component_names:
            h2.append({
                "name": name,
                "p_value": float(np.clip(self._rng.exponential(1e-8), 1e-20, 0.01)),
                "significant": True,
            })

        # H3: per-architecture
        arch_names = ["claude_code", "autogpt", "crewai", "langgraph"]
        h3 = []
        for name in arch_names:
            h3.append({
                "name": name,
                "p_value": float(np.clip(self._rng.exponential(1e-10), 1e-30, 0.001)),
                "significant": True,
            })

        # Cohen's d (large effect)
        cohens_d = float(np.clip(self._rng.normal(4.5, 0.5), 3.0, 6.0))

        # Assumption checks
        assumptions = [
            {
                "test": "Shapiro-Wilk",
                "group": "CIF",
                "statistic": float(np.clip(self._rng.normal(0.98, 0.01), 0.95, 1.0)),
                "p_value": float(np.clip(self._rng.uniform(0.05, 0.9), 0.01, 1.0)),
                "passed": True,
            },
            {
                "test": "Shapiro-Wilk",
                "group": "Baseline",
                "statistic": float(np.clip(self._rng.normal(0.97, 0.02), 0.93, 1.0)),
                "p_value": float(np.clip(self._rng.uniform(0.03, 0.8), 0.01, 1.0)),
                "passed": True,
            },
            {
                "test": "Levene",
                "group": "CIF vs Baseline",
                "statistic": float(np.clip(self._rng.normal(2.5, 1.0), 0.5, 5.0)),
                "p_value": float(np.clip(self._rng.uniform(0.05, 0.5), 0.01, 1.0)),
                "passed": True,
            },
        ]

        return {
            "h1": h1,
            "h2": h2,
            "h3": h3,
            "cohens_d_cif_vs_baseline": cohens_d,
            "assumptions": assumptions,
            "assumptions_met": True,
            "kruskal_wallis": {
                "h": float(np.clip(self._rng.normal(3.5, 1.5), 0.5, 8.0)),
                "p": float(np.clip(self._rng.uniform(0.1, 0.5), 0.01, 1.0)),
            },
        }

    def generate_multi_seed_results(self) -> Dict[str, Any]:
        """Generate multi-seed stability results matching run_multi_seed.py output.

        Returns
        -------
        dict
        """
        n_seeds = 30
        cv_threshold = 0.05

        # Generate per-seed metrics
        seed_metrics = []
        overall_rates = []
        arch_rates: Dict[str, list] = {
            "Claude Code": [], "AutoGPT": [], "CrewAI": [], "LangGraph": [],
        }
        cat_rates: Dict[str, list] = {
            "injection": [], "trust_exploitation": [],
            "belief_manipulation": [], "coordination": [],
        }

        for s in range(1, n_seeds + 1):
            overall = float(np.clip(self._rng.normal(0.967, 0.008), 0.93, 1.0))
            overall_rates.append(overall)

            per_arch = {}
            for arch, (mu, sigma) in [
                ("Claude Code", (0.972, 0.010)),
                ("AutoGPT", (0.948, 0.012)),
                ("CrewAI", (0.965, 0.011)),
                ("LangGraph", (0.960, 0.011)),
            ]:
                val = float(np.clip(self._rng.normal(mu, sigma), 0.90, 1.0))
                per_arch[arch] = val
                arch_rates[arch].append(val)

            per_cat = {}
            for cat, (mu, sigma) in [
                ("injection", (0.985, 0.006)),
                ("trust_exploitation", (0.960, 0.010)),
                ("belief_manipulation", (0.940, 0.012)),
                ("coordination", (0.975, 0.008)),
            ]:
                val = float(np.clip(self._rng.normal(mu, sigma), 0.89, 1.0))
                per_cat[cat] = val
                cat_rates[cat].append(val)

            seed_metrics.append({
                "seed": s,
                "overall": overall,
                "per_architecture": per_arch,
                "per_category": per_cat,
            })

        # Compute CVs
        overall_arr = np.array(overall_rates)
        overall_cv = float(np.std(overall_arr) / np.mean(overall_arr)) if np.mean(overall_arr) > 0 else 0.0

        per_arch_cv = {}
        for arch, rates in arch_rates.items():
            arr = np.array(rates)
            per_arch_cv[arch] = float(np.std(arr) / np.mean(arr)) if np.mean(arr) > 0 else 0.0

        per_cat_cv = {}
        for cat, rates in cat_rates.items():
            arr = np.array(rates)
            per_cat_cv[cat] = float(np.std(arr) / np.mean(arr)) if np.mean(arr) > 0 else 0.0

        return {
            "n_seeds": n_seeds,
            "overall_cv": overall_cv,
            "cv_threshold": cv_threshold,
            "stable": overall_cv <= cv_threshold,
            "per_architecture_cv": per_arch_cv,
            "per_category_cv": per_cat_cv,
            "seed_metrics": seed_metrics,
        }

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
