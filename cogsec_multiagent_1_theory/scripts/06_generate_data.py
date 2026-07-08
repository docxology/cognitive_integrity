#!/usr/bin/env python3
"""Generate experimental data for the paper."""

import sys
from pathlib import Path

# Add project root to path to allow importing src
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from src.data_generation import generate_experimental_data

if __name__ == "__main__":
    output_dir = project_root / "output" / "figures"
    generate_experimental_data(output_dir)
