#!/usr/bin/env python3
"""Generate ROC curves visualization for defense mechanisms."""

import sys
from pathlib import Path

# Add project root to path to allow importing src
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from src.visualization.roc_curves import create_roc_curves_figure

if __name__ == "__main__":
    output_dir = project_root / "output" / "figures"
    create_roc_curves_figure(output_dir)
