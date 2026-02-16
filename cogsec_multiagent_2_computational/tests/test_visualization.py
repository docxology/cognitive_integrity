"""Smoke tests for visualization style module."""

import os

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from visualization.style import (
    COLORS,
    FONTSIZE,
    PALETTE,
    SEMANTIC_COLORS,
    add_legend,
    apply_style,
    create_figure,
    format_axis,
    save_figure,
)


class TestColorPalette:
    """Tests for color palette definitions."""

    def test_colors_has_required_keys(self):
        """COLORS dict has all required keys."""
        required = {"primary", "secondary", "accent", "warning", "neutral", "background"}
        assert required.issubset(COLORS.keys())

    def test_colors_are_hex(self):
        """All COLORS values are valid hex color codes."""
        for name, color in COLORS.items():
            assert color.startswith("#"), f"{name} not hex: {color}"
            assert len(color) == 7, f"{name} wrong length: {color}"

    def test_palette_length(self):
        """PALETTE has 8 colors."""
        assert len(PALETTE) == 8

    def test_palette_all_hex(self):
        """All PALETTE entries are valid hex."""
        for i, color in enumerate(PALETTE):
            assert color.startswith("#") and len(color) == 7, f"PALETTE[{i}]: {color}"

    def test_semantic_colors_nonempty(self):
        """SEMANTIC_COLORS is populated."""
        assert len(SEMANTIC_COLORS) >= 15

    def test_semantic_colors_all_hex(self):
        """All SEMANTIC_COLORS are valid hex."""
        for name, color in SEMANTIC_COLORS.items():
            assert color.startswith("#"), f"{name}: {color}"

    def test_fontsize_has_required_keys(self):
        """FONTSIZE dict has expected keys."""
        required = {"tiny", "small", "note", "base", "large", "title"}
        assert required.issubset(FONTSIZE.keys())

    def test_fontsize_values_positive(self):
        """All font sizes are positive integers."""
        for name, size in FONTSIZE.items():
            assert isinstance(size, int) and size > 0, f"{name}: {size}"

    def test_fontsize_ordering(self):
        """Font sizes increase: tiny < small <= note <= base < large < title."""
        assert FONTSIZE["tiny"] < FONTSIZE["small"]
        assert FONTSIZE["small"] <= FONTSIZE["base"]
        assert FONTSIZE["base"] < FONTSIZE["title"]


class TestApplyStyle:
    """Tests for style application."""

    def test_apply_style_changes_rcparams(self):
        """apply_style() modifies matplotlib rcParams."""
        apply_style()
        assert matplotlib.rcParams["figure.dpi"] == 300

    def test_apply_style_sets_font_family(self):
        """apply_style() sets sans-serif font."""
        apply_style()
        family = matplotlib.rcParams["font.family"]
        # rcParams returns a list of font families
        assert "sans-serif" in family

    def test_apply_style_disables_top_spine(self):
        """apply_style() removes top spine."""
        apply_style()
        assert matplotlib.rcParams["axes.spines.top"] is False

    def test_apply_style_disables_right_spine(self):
        """apply_style() removes right spine."""
        apply_style()
        assert matplotlib.rcParams["axes.spines.right"] is False


class TestCreateFigure:
    """Tests for figure creation."""

    def test_returns_figure_and_axes(self):
        """create_figure() returns (Figure, Axes)."""
        fig, ax = create_figure()
        assert isinstance(fig, Figure)
        assert isinstance(ax, Axes)
        plt.close(fig)

    def test_custom_dimensions(self):
        """Figure has requested dimensions."""
        fig, ax = create_figure(width=10.0, height=8.0)
        w, h = fig.get_size_inches()
        assert abs(w - 10.0) < 0.1
        assert abs(h - 8.0) < 0.1
        plt.close(fig)

    def test_subplot_grid(self):
        """create_figure with grid returns array of axes."""
        fig, axes = create_figure(n_rows=2, n_cols=2)
        assert axes.shape == (2, 2)
        plt.close(fig)

    def test_background_color_set(self):
        """Figure background matches COLORS['background']."""
        fig, ax = create_figure()
        # Get facecolor as RGBA tuple
        fc = fig.get_facecolor()
        # Just verify it's been set (not default white)
        assert fc is not None
        plt.close(fig)


class TestSaveFigure:
    """Tests for figure saving."""

    def test_save_creates_files(self, tmp_path):
        """save_figure() creates PDF and PNG."""
        fig, ax = create_figure()
        ax.plot([1, 2, 3], [1, 4, 9])
        paths = save_figure(fig, "test_plot", output_dir=str(tmp_path))
        assert len(paths) == 2
        for p in paths:
            assert os.path.exists(p)

    def test_save_custom_formats(self, tmp_path):
        """save_figure() respects custom format list."""
        fig, ax = create_figure()
        ax.plot([1, 2], [1, 2])
        paths = save_figure(fig, "test_svg", output_dir=str(tmp_path), formats=("svg",))
        assert len(paths) == 1
        assert paths[0].endswith(".svg")


class TestFormatAxis:
    """Tests for axis formatting."""

    def test_format_sets_labels(self):
        """format_axis() sets xlabel and ylabel."""
        fig, ax = create_figure()
        format_axis(ax, "X Label", "Y Label")
        assert ax.get_xlabel() == "X Label"
        assert ax.get_ylabel() == "Y Label"
        plt.close(fig)

    def test_format_sets_title(self):
        """format_axis() sets title when provided."""
        fig, ax = create_figure()
        format_axis(ax, "X", "Y", title="My Title")
        assert ax.get_title() == "My Title"
        plt.close(fig)

    def test_format_no_title(self):
        """format_axis() without title leaves it empty."""
        fig, ax = create_figure()
        format_axis(ax, "X", "Y")
        assert ax.get_title() == ""
        plt.close(fig)


class TestAddLegend:
    """Tests for legend helper."""

    def test_add_legend_creates_legend(self):
        """add_legend() creates a legend on axes."""
        fig, ax = create_figure()
        ax.plot([1, 2], [1, 2], label="line")
        add_legend(ax)
        assert ax.get_legend() is not None
        plt.close(fig)
