"""Evaluation framework for the Cognitive Security Framework.

Provides experiment orchestration, detection metrics, ROC analysis,
latency/memory benchmarking, and agent-count scalability assessment.
"""

from .benchmark import BenchmarkResult, LatencyProfiler, MemoryProfiler
from .metrics import DetectionMetrics
from .precision_recall import (
    PRCurve,
    bootstrap_ap_ci,
    compute_average_precision,
    compute_average_precision_from_arrays,
    compute_pr_curve,
)
from .roc import ROCCurve, bootstrap_auc_ci, compute_auc, compute_roc, youdens_j
from .runner import ExperimentResult, ExperimentRunner
from .scalability import ScalabilityBenchmark, ScalabilityResult, ScalingModel

__all__ = [
    # Runner
    "ExperimentRunner",
    "ExperimentResult",
    # Metrics
    "DetectionMetrics",
    # ROC
    "ROCCurve",
    "compute_roc",
    "compute_auc",
    "bootstrap_auc_ci",
    "youdens_j",
    # Benchmark
    "LatencyProfiler",
    "MemoryProfiler",
    "BenchmarkResult",
    # Scalability
    "ScalabilityBenchmark",
    "ScalabilityResult",
    "ScalingModel",
    # Precision-Recall
    "PRCurve",
    "compute_pr_curve",
    "compute_average_precision",
    "compute_average_precision_from_arrays",
    "bootstrap_ap_ci",
]
