#!/usr/bin/env python3
"""Generate Five Pillars posture radar chart.

Thin orchestrator script - business logic in src/visualization.py.
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.visualization import (
    get_five_pillars_data,
    render_posture_radar,
)


def main() -> None:
    """Generate posture radar figure."""
    # A worked example of the src/posture.py questionnaire, not an assessment
    # of any system. There is no assessed deployment behind these five scores;
    # they exist to show what the radar looks like when the questionnaire is
    # filled in. The title says so, because a radar chart of five two-decimal
    # scores reads as a measurement of something otherwise.
    data = get_five_pillars_data(
        firewall_score=0.85,  # Strong input filtering
        sandbox_score=0.70,  # Moderate belief isolation
        tripwire_score=0.60,  # Basic identity verification
        invariant_score=0.90,  # Robust behavioral constraints
        provenance_score=0.55,  # Limited tracking
    )

    # Render figure
    fig = render_posture_radar(data)
    fig.tight_layout()

    # Save outputs
    output_dir = project_root / "output" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    png_path = output_dir / "posture_radar.png"
    pdf_path = output_dir / "posture_radar.pdf"

    fig.savefig(png_path, dpi=150, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)

    # Print paths for manifest collection
    print(str(png_path))
    print(str(pdf_path))


if __name__ == "__main__":
    sys.exit(main())
