#!/usr/bin/env python3
"""Generate deployment checklist flowchart.

Thin orchestrator script - business logic in src/visualization.py.
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.visualization import (
    get_deployment_phases_data,
    render_checklist_flowchart,
)


def main() -> None:
    """Generate checklist flowchart figure."""
    # Get deployment phases data
    data = get_deployment_phases_data()

    # Render figure
    fig = render_checklist_flowchart(data)
    fig.tight_layout()

    # Save outputs
    output_dir = project_root / "output" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    png_path = output_dir / "checklist_flowchart.png"
    pdf_path = output_dir / "checklist_flowchart.pdf"

    fig.savefig(png_path, dpi=150, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)

    # Print paths for manifest collection
    print(str(png_path))
    print(str(pdf_path))


if __name__ == "__main__":
    sys.exit(main())
