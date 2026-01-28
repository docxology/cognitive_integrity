
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def setup_plotting():
    """Set up professional plotting environment."""
    # Use seaborn style for better defaults
    sns.set_theme(style="whitegrid")
    
    # Custom adjustments for academic paper - increased fonts for PDF clarity
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 14,
        "axes.labelsize": 14,
        "axes.titlesize": 16,
        "axes.titleweight": "bold",
        "legend.fontsize": 12,
        "xtick.labelsize": 12,
        "ytick.labelsize": 12,
        "figure.titlesize": 18,
        "figure.dpi": 300,
        "lines.linewidth": 2,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.1,
    })

def get_color_palette():
    """Return a colorblind-friendly palette."""
    # IBM Design Language Color Blind Safe Palette
    return ["#648FFF", "#DC267F", "#FFB000", "#785EF0", "#FE6100"]

def save_figure(fig, output_dir: Path, name: str):
    """Save figure in PNG and PDF formats."""
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
        
    png_path = output_dir / f"{name}.png"
    pdf_path = output_dir / f"{name}.pdf"
    
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    
    print(f"Saved {png_path}")
    print(f"Saved {pdf_path}")
    return pdf_path
