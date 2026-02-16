"""Detection metrics: TPR, FPR, F1, accuracy, precision, recall, MCC.

Provides the ``DetectionMetrics`` class for computing standard binary
classification metrics from confusion-matrix counts or from raw
prediction lists.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List

if TYPE_CHECKING:
    from .runner import ExperimentResult


@dataclass
class DetectionMetrics:
    """Binary classification metrics from a confusion matrix.

    Attributes:
        tp: True positives.
        fp: False positives.
        tn: True negatives.
        fn: False negatives.
    """

    tp: int
    fp: int
    tn: int
    fn: int

    # ---- derived properties ----

    @property
    def tpr(self) -> float:
        """True positive rate (sensitivity / recall)."""
        denom = self.tp + self.fn
        return self.tp / denom if denom > 0 else 0.0

    @property
    def fpr(self) -> float:
        """False positive rate (fall-out)."""
        denom = self.fp + self.tn
        return self.fp / denom if denom > 0 else 0.0

    @property
    def fnr(self) -> float:
        """False negative rate (miss rate)."""
        denom = self.tp + self.fn
        return self.fn / denom if denom > 0 else 0.0

    @property
    def precision(self) -> float:
        """Positive predictive value."""
        denom = self.tp + self.fp
        return self.tp / denom if denom > 0 else 0.0

    @property
    def recall(self) -> float:
        """Same as TPR (sensitivity)."""
        return self.tpr

    @property
    def f1(self) -> float:
        """Harmonic mean of precision and recall."""
        p = self.precision
        r = self.recall
        return 2.0 * p * r / (p + r) if (p + r) > 0 else 0.0

    @property
    def accuracy(self) -> float:
        """Overall accuracy."""
        total = self.tp + self.fp + self.tn + self.fn
        return (self.tp + self.tn) / total if total > 0 else 0.0

    @property
    def specificity(self) -> float:
        """True negative rate."""
        denom = self.fp + self.tn
        return self.tn / denom if denom > 0 else 0.0

    @property
    def mcc(self) -> float:
        """Matthews correlation coefficient.

        MCC = (TP*TN - FP*FN) / sqrt((TP+FP)(TP+FN)(TN+FP)(TN+FN))

        Returns 0.0 if the denominator is zero.
        """
        tp, fp, tn, fn = self.tp, self.fp, self.tn, self.fn
        numerator = tp * tn - fp * fn
        denominator = math.sqrt(
            (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)
        )
        return numerator / denominator if denominator > 0 else 0.0

    # ---- factory methods ----

    @classmethod
    def from_predictions(cls, y_true: List[bool], y_pred: List[bool]) -> "DetectionMetrics":
        """Construct metrics from paired truth/prediction lists.

        Args:
            y_true: Ground-truth labels (True = attack present).
            y_pred: Predicted labels (True = detected).

        Returns:
            ``DetectionMetrics`` with computed confusion counts.
        """
        if len(y_true) != len(y_pred):
            raise ValueError(
                f"Length mismatch: y_true has {len(y_true)}, y_pred has {len(y_pred)}"
            )

        tp = fp = tn = fn = 0
        for truth, pred in zip(y_true, y_pred):
            if truth and pred:
                tp += 1
            elif not truth and pred:
                fp += 1
            elif not truth and not pred:
                tn += 1
            else:
                fn += 1

        return cls(tp=tp, fp=fp, tn=tn, fn=fn)

    @classmethod
    def from_experiment_result(cls, result: "ExperimentResult") -> "DetectionMetrics":
        """Construct metrics from an ``ExperimentResult`` dataclass.

        Args:
            result: An experiment result with confusion-matrix fields.

        Returns:
            ``DetectionMetrics`` instance.
        """
        return cls(
            tp=result.true_positives,
            fp=result.false_positives,
            tn=result.true_negatives,
            fn=result.false_negatives,
        )

    # ---- export ----

    def to_dict(self) -> Dict[str, float]:
        """Export all metrics as a flat dictionary."""
        return {
            "tp": float(self.tp),
            "fp": float(self.fp),
            "tn": float(self.tn),
            "fn": float(self.fn),
            "tpr": self.tpr,
            "fpr": self.fpr,
            "fnr": self.fnr,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "accuracy": self.accuracy,
            "specificity": self.specificity,
            "mcc": self.mcc,
        }
