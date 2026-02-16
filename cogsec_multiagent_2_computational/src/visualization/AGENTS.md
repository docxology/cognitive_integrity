# Visualization Package - Agent Reference

Publication-quality figures and LaTeX tables.

## Modules

### style.py

Shared matplotlib style configuration.

**Key Functions:**

- `setup_style()` - Apply publication style
- `save_figure()` - Save with proper DPI

**Key Constants:**

- `COLORS` - Colorblind-safe palette
- `FIGURE_SIZE` - Standard figure dimensions

### figures/

Subdirectory with individual figure generators.

### tables/

Subdirectory with table generators.

## Figure Types

- Attack surface diagrams
- Trust decay curves
- ROC curves
- Precision-recall curves
- Ablation heatmaps
- Scalability plots
- Architecture comparisons

## Usage

```python
from src.visualization import setup_style, save_figure
from src.visualization.figures import attack_surface

setup_style()
fig = attack_surface.generate(data)
save_figure(fig, "output/attack_surface.pdf")
```

## Style Guidelines

- Colorblind-safe palette (IBM/Wong)
- 300 DPI for print
- Vector formats (PDF/SVG) preferred
- Consistent font sizes across figures
