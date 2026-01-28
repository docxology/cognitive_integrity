#!/usr/bin/env python3
"""Generate common pitfalls severity bar chart.

Thin orchestrator script - business logic in src/visualization.py.
"""

from pathlib import Path

import matplotlib.pyplot as plt

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.visualization import (
    get_pitfalls_data,
    render_pitfall_severity,
)


def main() -> None:
    """Generate pitfall severity figure."""
    # Get pitfall data
    data = get_pitfalls_data()

    # Render figure
    fig = render_pitfall_severity(data)
    fig.tight_layout()

    # Save outputs
    output_dir = project_root / "output" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    png_path = output_dir / "pitfall_severity.png"
    pdf_path = output_dir / "pitfall_severity.pdf"

    fig.savefig(png_path, dpi=150, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)

    # Print paths for manifest collection
    print(str(png_path))
    print(str(pdf_path))


if __name__ == "__main__":
    main()
