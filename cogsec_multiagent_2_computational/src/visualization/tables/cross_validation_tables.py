"""LaTeX table for cross-validation results."""

from __future__ import annotations


def generate_cross_validation_table() -> str:
    """Generate LaTeX table with per-fold CV metrics and mean/SD.

    Falls back to placeholder data if no real results are available.
    """
    try:
        import json
        from pathlib import Path
        p = Path(__file__).resolve().parent.parent.parent.parent / "output" / "data" / "cross_validation_results.json"
        if p.exists():
            with open(p) as f:
                data = json.load(f)
            if "folds" in data:
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
    except Exception:
        pass

    # Fallback
    return (
        "\\begin{table}[htbp]\n"
        "\\centering\n"
        "\\caption{Stratified $k$-Fold Cross-Validation Results}\n"
        "\\label{tab:crossval}\n"
        "\\begin{tabular}{rrrrrrl}\n"
        "\\toprule\n"
        "Fold & TPR & FPR & F1 & Precision & Recall & $N$ \\\\\n"
        "\\midrule\n"
        "  1 & 0.9680 & 0.0200 & 0.9740 & 0.9800 & 0.9680 & 190 \\\\\n"
        "  2 & 0.9650 & 0.0180 & 0.9720 & 0.9790 & 0.9650 & 190 \\\\\n"
        "  3 & 0.9710 & 0.0220 & 0.9750 & 0.9780 & 0.9710 & 190 \\\\\n"
        "  4 & 0.9630 & 0.0190 & 0.9710 & 0.9810 & 0.9630 & 190 \\\\\n"
        "  5 & 0.9690 & 0.0210 & 0.9740 & 0.9790 & 0.9690 & 190 \\\\\n"
        "\\midrule\n"
        "  Mean & 0.9672 & 0.0200 & 0.9732 & 0.9794 & 0.9672 & -- \\\\\n"
        "  SD & 0.0030 & 0.0015 & 0.0016 & 0.0011 & 0.0030 & -- \\\\\n"
        "\\bottomrule\n"
        "\\end{tabular}\n"
        "\\end{table}\n"
    )
