"""LaTeX table for cross-validation results.

Reads from cross_validation_results.json.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def generate_cross_validation_table() -> str:
    """Generate LaTeX table with per-fold CV metrics and mean/SD.

    Reads from cross_validation_results.json.  Raises FileNotFoundError
    if the data file is not available.
    """
    p = Path(__file__).resolve().parent.parent.parent.parent / "output" / "data" / "cross_validation_results.json"
    with open(p) as f:
        data = json.load(f)

    rows = []
    for fold in data["folds"]:
        rows.append(
            f"  {fold['fold']+1} & {fold['tpr']:.4f} & {fold['fpr']:.4f} & "
            f"{fold['f1']:.4f} & {fold['precision']:.4f} & {fold['recall']:.4f} & "
            f"{fold['n_samples']} \\\\"
        )
    rows.append("\\midrule")
    rows.append(
        f"  Mean & {data['mean_tpr']:.4f} & -- & {data['mean_f1']:.4f} & -- & -- & -- \\\\"
    )
    rows.append(
        f"  SD & {data['std_tpr']:.4f} & -- & {data['std_f1']:.4f} & -- & -- & -- \\\\"
    )
    body = "\n".join(rows)

    logger.info("Loaded cross-validation results from %s", p)
    return (
        "\\begin{table}[htbp]\n"
        "\\centering\n"
        "\\caption{Stratified $k$-Fold Cross-Validation Results}\n"
        "\\label{tab:crossval}\n"
        "\\begin{tabular}{rrrrrrl}\n"
        "\\toprule\n"
        "Fold & TPR & FPR & F1 & Precision & Recall & $N$ \\\\\n"
        "\\midrule\n"
        f"{body}\n"
        "\\bottomrule\n"
        "\\end{tabular}\n"
        "\\end{table}\n"
    )
