"""Tests for the visualization style module and the LaTeX table generators.

The table sections below bind every emitted cell to the artifact it claims
to summarise -- ``output/data/*.json`` or ``AttackCorpus.generate()`` --
rather than asserting that a non-empty string came back.  Audit findings
MSC-11, MSC-12 and REPRO-04 all survived a green suite precisely because
the only table assertions in the repository were
``isinstance(result, str) and len(result) > 0``.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pytest
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

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DATA_DIR = _PROJECT_ROOT / "output" / "data"
_TABLE_DIR = _PROJECT_ROOT / "output" / "tables"
_SCRIPTS_DIR = _PROJECT_ROOT / "scripts"


def _load_json(name: str) -> dict:
    with open(_DATA_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


def _body_rows(latex: str) -> list[list[str]]:
    """Split a generated table into its data rows, as lists of stripped cells."""
    rows = []
    for line in latex.splitlines():
        line = line.strip()
        if not line.endswith(r"\\"):
            continue
        cells = [c.strip() for c in line[:-2].split("&")]
        rows.append(cells)
    return rows


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


# ===========================================================================
# Wilson confidence intervals (visualization.tables.binomial_ci)
# ===========================================================================

class TestBinomialCI:
    """The ± printed in the tables must be computed, and must fail closed."""

    @pytest.mark.parametrize(("k", "n"), [(96, 100), (12, 98), (500, 500), (0, 40)])
    def test_endpoints_satisfy_the_score_equation(self, k, n):
        """Bind to the *definition*, not to a constant transcribed by hand.

        The Wilson endpoints are by construction the two roots of

            (p_hat - x)^2 = z^2 * x * (1 - x) / n

        so checking that identity verifies the implementation against the
        interval's definition instead of against a remembered number.
        """
        from visualization.tables.binomial_ci import Z_95, wilson_interval

        p_hat = k / n
        for x in wilson_interval(k, n):
            lhs = (p_hat - x) ** 2
            rhs = Z_95**2 * x * (1 - x) / n
            assert abs(lhs - rhs) < 1e-12, (k, n, x, lhs, rhs)

    def test_score_equation_check_rejects_a_wrong_interval(self):
        """POSITIVE CONTROL for the test above: a Wald interval fails it."""
        import math

        from visualization.tables.binomial_ci import Z_95

        k, n = 96, 100
        p_hat = k / n
        wald = Z_95 * math.sqrt(p_hat * (1 - p_hat) / n)
        residuals = [
            abs((p_hat - x) ** 2 - Z_95**2 * x * (1 - x) / n)
            for x in (p_hat - wald, p_hat + wald)
        ]
        assert max(residuals) > 1e-6, residuals

    def test_wilson_interval_reference_values(self):
        """Regression pin for 96/100, produced by the verified implementation."""
        from visualization.tables.binomial_ci import wilson_interval

        lo, hi = wilson_interval(96, 100)
        assert abs(lo - 0.9016292856411208) < 1e-12, lo
        assert abs(hi - 0.9843366960084523) < 1e-12, hi

    def test_wilson_interval_is_nondegenerate_at_p_equals_one(self):
        """At p = 1.0 the Wald interval collapses to zero width; Wilson must not.

        Every ``1.000`` cell in ``detection_rates.tex`` sits exactly here, so
        a degenerate interval would print ``± 0.000`` for every one of them.
        """
        from visualization.tables.binomial_ci import wilson_half_width

        assert wilson_half_width(500, 500) > 0.0
        assert wilson_half_width(100, 100) > wilson_half_width(500, 500)

    def test_wilson_rejects_zero_trials(self):
        """POSITIVE CONTROL: a degenerate n raises instead of printing ±0.000."""
        from visualization.tables.binomial_ci import wilson_interval

        with pytest.raises(ValueError, match="n must be positive"):
            wilson_interval(0, 0)

    def test_wilson_rejects_successes_above_n(self):
        """POSITIVE CONTROL: impossible counts raise."""
        from visualization.tables.binomial_ci import wilson_interval

        with pytest.raises(ValueError, match=r"successes must lie in \[0, 5\]"):
            wilson_interval(6, 5)

    def test_rate_to_successes_recovers_the_count(self):
        from visualization.tables.binomial_ci import rate_to_successes

        assert rate_to_successes(12 / 98, 98) == 12
        assert rate_to_successes(0.0, 98) == 0
        assert rate_to_successes(1.0, 98) == 98

    def test_rate_to_successes_rejects_a_rate_that_is_not_a_multiple_of_1_over_n(self):
        """POSITIVE CONTROL: a rate/n mismatch raises rather than rounding away."""
        from visualization.tables.binomial_ci import rate_to_successes

        with pytest.raises(ValueError, match="not a multiple"):
            rate_to_successes(0.1234, 98)

    def test_rate_to_successes_rejects_zero_trials(self):
        """POSITIVE CONTROL: a zero denominator raises before the division."""
        from visualization.tables.binomial_ci import rate_to_successes

        with pytest.raises(ValueError, match="n must be positive"):
            rate_to_successes(0.5, 0)


# ===========================================================================
# Ablation table (audit MSC-12) — every cell bound to ablation_results.json
# ===========================================================================

def _ablation_cells(latex: str) -> dict[str, tuple[str, str]]:
    """Map row label -> (rate cell, delta cell) from a generated ablation table."""
    out = {}
    for cells in _body_rows(latex):
        if len(cells) < 3 or cells[0].startswith(("Configuration", r"\textbf")):
            continue
        out[cells[0]] = (cells[1], cells[-1])
    return out


class TestAblationTableBindsToJson:
    """``ablation.tex`` must reproduce ``ablation_results.json`` exactly.

    Audit MSC-12: the loader added ``delta_tpr`` to an ablated row's ``tpr``
    where the JSON's convention (``delta = removed - full``) requires a
    subtraction.  The shipped table therefore read ``Full CIF 0.019`` with
    every removal row a positive improvement -- the inverse of the paper's
    claim -- and the suite stayed green because nothing compared a cell to
    the data.
    """

    def test_full_cif_cell_equals_json_full_pipeline_tpr(self):
        from visualization.tables.ablation_tables import generate_ablation_table

        data = _load_json("ablation_results.json")
        cells = _ablation_cells(generate_ablation_table())
        expected = f"{data['full_pipeline']['tpr']:.3f}"
        assert cells["Full CIF"][0] == expected

    def test_every_removal_row_matches_its_json_entry(self):
        from visualization.tables.ablation_tables import generate_ablation_table

        data = _load_json("ablation_results.json")
        cells = _ablation_cells(generate_ablation_table())

        assert len(cells) == len(data["component_removal"]) + 1

        for entry in data["component_removal"]:
            label = "- " + entry["removed"].replace("_", " ").title()
            assert label in cells, f"{label} missing from the emitted table"
            rate_cell, delta_cell = cells[label]
            assert rate_cell == f"{entry['tpr']:.3f}"
            delta = entry["delta_tpr"]
            expected_delta = "0.000" if delta == 0.0 else f"{delta:+.3f}"
            assert delta_cell == expected_delta, (
                f"{label}: emitted delta {delta_cell} != JSON delta {expected_delta}"
            )

    def test_no_removal_row_claims_an_improvement(self):
        """Every recorded delta is <= 0, so no emitted delta may be positive.

        This is the assertion the sign bug violated: it printed ``+0.052``
        through ``+0.106`` for the eight removals.
        """
        from visualization.tables.ablation_tables import generate_ablation_table

        data = _load_json("ablation_results.json")
        assert all(e["delta_tpr"] <= 0 for e in data["component_removal"]), (
            "precondition: the tracked JSON records no beneficial removal"
        )

        cells = _ablation_cells(generate_ablation_table())
        for label, (_rate, delta_cell) in cells.items():
            if label == "Full CIF":
                continue
            assert not delta_cell.startswith("+"), f"{label} claims an improvement"

    def test_full_rate_is_the_maximum_rate_in_the_table(self):
        """Removing a component cannot beat the full pipeline in this data."""
        from visualization.tables.ablation_tables import generate_ablation_table

        cells = _ablation_cells(generate_ablation_table())
        full = float(cells["Full CIF"][0])
        for label, (rate, _delta) in cells.items():
            assert float(rate) <= full + 1e-12, f"{label} exceeds Full CIF"

    def test_sign_convention_is_subtraction_not_addition(self, tmp_path):
        """POSITIVE CONTROL for the MSC-12 fix, on numbers that discriminate.

        With ``tpr = 0.4`` and ``delta_tpr = -0.2`` the correct full-pipeline
        rate is ``0.6``; the reverted ``tpr + delta_tpr`` gives ``0.2``.  Run
        against the pre-fix module this assertion fails outright.
        """
        from visualization.tables.ablation_tables import _load_ablation_data

        path = tmp_path / "ablation_results.json"
        path.write_text(json.dumps({
            "full_pipeline": {"tpr": 0.6, "fpr": 0.0},
            "component_removal": [
                {"removed": "detection", "tpr": 0.4, "delta_tpr": -0.2},
            ],
        }))

        rows = _load_ablation_data(path)
        assert rows[0].label == "Full CIF"
        assert abs(rows[0].tpr - 0.6) < 1e-12
        assert abs(rows[0].tpr - 0.2) > 1e-3, "emitted the tpr + delta_tpr value"

    def test_inverted_delta_convention_is_rejected(self, tmp_path):
        """POSITIVE CONTROL: flipping the JSON's delta sign must raise.

        This is the guard that keeps the sign error from coming back through
        the *runner* rather than through this module.
        """
        from visualization.tables.ablation_tables import _load_ablation_data

        path = tmp_path / "ablation_results.json"
        path.write_text(json.dumps({
            "full_pipeline": {"tpr": 0.6},
            "component_removal": [
                # delta written as full - removed instead of removed - full
                {"removed": "detection", "tpr": 0.4, "delta_tpr": +0.2},
            ],
        }))

        with pytest.raises(ValueError, match="inconsistent with the full"):
            _load_ablation_data(path)

    def test_empty_component_removal_is_rejected(self, tmp_path):
        """POSITIVE CONTROL: no data must raise, not render a 0.965 placeholder."""
        from visualization.tables.ablation_tables import _load_ablation_data

        path = tmp_path / "ablation_results.json"
        path.write_text(json.dumps({"component_removal": []}))
        with pytest.raises(ValueError, match="no 'component_removal'"):
            _load_ablation_data(path)

    def test_ci_column_is_omitted_when_the_runner_records_no_sample_size(self):
        """No sample size means no interval -- and no invented ±0.008/±0.015."""
        from visualization.tables.ablation_tables import generate_ablation_table

        data = _load_json("ablation_results.json")
        assert "n_attacks" not in data, (
            "precondition changed: the runner now records n_attacks, so the "
            "CI column should be asserted present instead"
        )
        latex = generate_ablation_table()
        assert r"95\% CI" not in latex
        # The two retired stand-in constants, matched as whole cells so a
        # legitimate future rate of 0.008 cannot trip this.
        assert r"$\pm 0.008$" not in latex
        assert r"$\pm 0.015$" not in latex

    def test_ci_column_appears_and_is_computed_once_n_is_recorded(self, tmp_path):
        """POSITIVE CONTROL: the CI column is reachable and data-derived."""
        from visualization.tables.ablation_tables import (
            _load_ablation_data,
            generate_ablation_table,
        )
        from visualization.tables.binomial_ci import wilson_half_width

        path = tmp_path / "ablation_results.json"
        path.write_text(json.dumps({
            "full_pipeline": {"tpr": 0.6},
            "n_attacks": 100,
            "component_removal": [
                {"removed": "detection", "tpr": 0.4, "delta_tpr": -0.2},
            ],
        }))

        rows = _load_ablation_data(path)
        assert rows[0].ci_half_width == pytest.approx(wilson_half_width(60, 100))
        assert rows[1].ci_half_width == pytest.approx(wilson_half_width(40, 100))

        latex = generate_ablation_table(
            {r.label: (r.tpr, r.ci_half_width) for r in rows}
        )
        assert r"95\% CI" in latex
        assert f"$\\pm {wilson_half_width(60, 100):.3f}$" in latex

    def test_sample_size_may_be_recorded_inside_full_pipeline(self, tmp_path):
        """Either placement for ``n_attacks`` is honoured."""
        from visualization.tables.ablation_tables import _load_ablation_data

        path = tmp_path / "ablation_results.json"
        path.write_text(json.dumps({
            "full_pipeline": {"tpr": 0.6, "n_attacks": 100},
            "component_removal": [
                {"removed": "detection", "tpr": 0.4, "delta_tpr": -0.2},
            ],
        }))
        assert _load_ablation_data(path)[0].ci_half_width is not None

    def test_non_positive_sample_size_is_rejected(self, tmp_path):
        """POSITIVE CONTROL: n <= 0 raises instead of producing a bogus CI."""
        from visualization.tables.ablation_tables import _load_ablation_data

        path = tmp_path / "ablation_results.json"
        path.write_text(json.dumps({
            "full_pipeline": {"tpr": 0.6},
            "n_attacks": 0,
            "component_removal": [
                {"removed": "detection", "tpr": 0.4, "delta_tpr": -0.2},
            ],
        }))
        with pytest.raises(ValueError, match="n_attacks must be positive"):
            _load_ablation_data(path)

    def test_full_rate_is_derived_when_full_pipeline_block_is_absent(self, tmp_path):
        """Older result files carry no ``full_pipeline`` block."""
        from visualization.tables.ablation_tables import _load_ablation_data

        path = tmp_path / "ablation_results.json"
        path.write_text(json.dumps({
            "component_removal": [
                {"removed": "detection", "tpr": 0.4, "delta_tpr": -0.2},
                {"removed": "firewall", "tpr": 0.55, "delta_tpr": -0.05},
            ],
        }))
        rows = _load_ablation_data(path)
        assert rows[0].tpr == pytest.approx(0.6)
        assert rows[0].ci_half_width is None

    def test_explicit_results_mapping_is_rendered(self):
        """The legacy ``{label: (rate, ci)}`` entry point still works."""
        from visualization.tables.ablation_tables import generate_ablation_table

        latex = generate_ablation_table({
            "Full CIF": (0.90, None),
            "- Firewall": (0.75, None),
        })
        cells = _ablation_cells(latex)
        assert cells["Full CIF"] == ("0.900", "---")
        assert cells["- Firewall"] == ("0.750", "-0.150")

    def test_explicit_results_mapping_requires_a_full_cif_entry(self):
        """POSITIVE CONTROL: without a baseline there is nothing to delta against."""
        from visualization.tables.ablation_tables import generate_ablation_table

        with pytest.raises(ValueError, match="must contain a 'Full CIF'"):
            generate_ablation_table({"- Firewall": (0.75, 0.01)})


class TestSynergyTableBindsToJson:
    """``synergy.tex`` may only report pairs the runner actually measured."""

    def test_one_row_per_recorded_pair_with_matching_values(self):
        from visualization.tables.ablation_tables import generate_synergy_table

        pairs = _load_json("ablation_results.json")["top_synergies"]
        rows = [r for r in _body_rows(generate_synergy_table()) if len(r) == 6]
        rows = [r for r in rows if not r[0].startswith("Component")]

        assert len(rows) == len(pairs)

        emitted = {(r[0], r[1]): r for r in rows}
        for p in pairs:
            key = (
                p["a"].replace("_", " ").title(),
                p["b"].replace("_", " ").title(),
            )
            assert key in emitted, f"{key} missing"
            row = emitted[key]
            assert row[2] == f"{p['tpr_a']:.4f}"
            assert row[3] == f"{p['tpr_b']:.4f}"
            assert row[4] == f"{p['combined_tpr']:.4f}"
            assert row[5] == f"{p['synergy']:+.4f}"

    def test_unmeasured_pairs_are_not_reported_as_zero(self):
        """The old 5x5 matrix printed 0.000 for pairs never written to the JSON.

        ``consensus`` appears in ``component_removal`` but in no synergy
        pair, so a table that mentions it is asserting an unmeasured zero.
        """
        from visualization.tables.ablation_tables import generate_synergy_table

        data = _load_json("ablation_results.json")
        measured = {p["a"] for p in data["top_synergies"]} | {
            p["b"] for p in data["top_synergies"]
        }
        unmeasured = {e["removed"] for e in data["component_removal"]} - measured
        assert unmeasured, "precondition: some component has no recorded synergy"

        latex = generate_synergy_table()
        for name in unmeasured:
            assert name.replace("_", " ").title() not in latex, (
                f"{name} has no recorded synergy but appears in the table"
            )

    def test_exact_ties_are_both_reported(self):
        """firewall+detection and tripwire+detection are exactly tied.

        A ranking that silently kept one of a tied pair would misreport the
        result; both must survive to the table.
        """
        from visualization.tables.ablation_tables import generate_synergy_table

        pairs = _load_json("ablation_results.json")["top_synergies"]
        top = max(p["synergy"] for p in pairs)
        tied = [p for p in pairs if p["synergy"] == top]
        assert len(tied) >= 2, "precondition: the top synergy is a tie"

        latex = generate_synergy_table()
        assert latex.count(f"{top:+.4f}") == len(tied)


# ===========================================================================
# Corpus composition table (audit MSC-11)
# ===========================================================================

def _corpus_counts_from_table(latex: str) -> dict[str, int]:
    """Extract ``{subcategory label: count}`` from a generated corpus table."""
    counts = {}
    for cells in _body_rows(latex):
        if len(cells) != 4 or cells[0].startswith(("Category", r"\textbf")):
            continue
        if cells[1].startswith(r"\textit"):
            continue
        counts[cells[1]] = int(cells[2])
    return counts


class TestCorpusTableBindsToGenerator:
    """``corpus_composition.tex`` must measure ``AttackCorpus``, not a literal.

    Audit MSC-11: the module carried a 12-row literal whose subcategory
    counts disagreed with the generator in 8 rows while the four top-level
    subtotals happened to agree, so nothing downstream noticed.
    """

    def test_every_subcategory_count_matches_the_generator(self):
        from attacks.corpus import AttackCorpus
        from visualization.tables.corpus_tables import generate_corpus_table

        corpus = AttackCorpus.generate(seed=42)
        expected = {
            sub.replace("_", " ").title(): n
            for sub, n in corpus.subcategory_distribution().items()
        }
        assert _corpus_counts_from_table(generate_corpus_table()) == expected

    def test_subtotals_and_total_sum_to_the_corpus_length(self):
        from attacks.corpus import AttackCorpus
        from visualization.tables.corpus_tables import generate_corpus_table

        corpus = AttackCorpus.generate(seed=42)
        latex = generate_corpus_table()

        subtotals = [
            int(re.sub(r"\\textbf\{|\}", "", c[2]))
            for c in _body_rows(latex)
            if len(c) == 4 and c[1].startswith(r"\textit{Subtotal}")
        ]
        assert sum(subtotals) == len(corpus)
        assert f"\\textbf{{{len(corpus)}}}" in latex

    def test_the_stale_literal_counts_are_gone(self):
        """The retired literal's wrong counts must not appear as counts.

        180/120/70/50/60/40/35/25 were the hand-typed values; the generator
        measures 200/100/60/60/50/50/30/30.
        """
        from visualization.tables.corpus_tables import generate_corpus_table

        counts = set(_corpus_counts_from_table(generate_corpus_table()).values())
        for stale in (180, 120, 70, 35, 25):
            assert stale not in counts, f"stale literal count {stale} still emitted"

    def test_table_follows_a_substituted_corpus(self):
        """POSITIVE CONTROL: feed a different corpus, get a different table.

        A hardcoded literal cannot pass this: the emitted counts must be the
        ones this three-sample corpus actually contains.
        """
        from attacks.corpus import AttackCorpus, AttackSample
        from utils.types import AttackCategory
        from visualization.tables.corpus_tables import generate_corpus_table

        samples = [
            AttackSample(
                id=f"X-{i:04d}",
                payload="p",
                category=cat,
                subcategory=cat.value,
                difficulty="easy",
                expected_detection=True,
            )
            for i, cat in enumerate(
                [AttackCategory.DIRECT_INJECTION] * 3 + [AttackCategory.SYBIL_ATTACK]
            )
        ]
        latex = generate_corpus_table(AttackCorpus(samples))

        assert _corpus_counts_from_table(latex) == {
            "Direct Injection": 3,
            "Sybil Attack": 1,
        }
        assert "(4 Attacks)" in latex
        assert "950" not in latex

    def test_empty_corpus_is_rejected(self):
        """POSITIVE CONTROL: a zero-row composition table raises."""
        from attacks.corpus import AttackCorpus
        from visualization.tables.corpus_tables import generate_corpus_table

        with pytest.raises(ValueError, match="empty"):
            generate_corpus_table(AttackCorpus([]))


# ===========================================================================
# Detection-rate table (audit REPRO-04)
# ===========================================================================

class TestDetectionTableBindsToJson:
    """Column headers and cells must both come from the evaluation data.

    Audit REPRO-04: ``_CAT_ORDER`` listed four category strings that occur
    nowhere in ``full_evaluation_results.json``, so the loader fell through
    to alphabetical order while the table printed a hardcoded header list.
    The column headed "Injection" carried the ``belief_drift`` (n=150)
    measurements and "Belief Manip." carried ``indirect_injection`` (n=500).
    """

    def test_header_order_follows_the_data(self):
        from data.result_loaders import evaluation_to_detection_matrix
        from visualization.tables.detection_tables import (
            _category_label,
            generate_detection_table,
        )

        path = _DATA_DIR / "full_evaluation_results.json"
        _archs, cats, _matrix = evaluation_to_detection_matrix(path=str(path))
        header = _body_rows(generate_detection_table())[0]
        assert header[1:-1] == [_category_label(c) for c in cats]

    def test_every_cell_matches_its_json_row(self):
        from visualization.tables.binomial_ci import wilson_half_width
        from visualization.tables.detection_tables import generate_detection_table

        raw = _load_json("full_evaluation_results.json")
        by_key = {(r["architecture"], r["attack_category"]): r for r in raw}

        from data.result_loaders import evaluation_to_detection_matrix
        archs, cats, _m = evaluation_to_detection_matrix(
            path=str(_DATA_DIR / "full_evaluation_results.json")
        )

        rows = _body_rows(generate_detection_table())[1:]
        assert len(rows) == len(archs)

        for arch, cells in zip(archs, rows):
            assert cells[0] == arch
            for cat, cell in zip(cats, cells[1:-1]):
                r = by_key[(arch, cat)]
                tp, fn = r["true_positives"], r["false_negatives"]
                expected = (
                    f"${r['detection_rate']:.3f} \\pm "
                    f"{wilson_half_width(tp, tp + fn):.3f}$"
                )
                assert cell == expected, f"{arch}/{cat}: {cell} != {expected}"

    def test_overall_column_pools_counts_rather_than_averaging_rates(self):
        """AutoGPT's pooled rate (931/950 = 0.980) differs from the rate mean.

        The unweighted mean of its four category rates is 0.974; the
        categories have n = 500/200/150/100, so the mean is not the
        architecture's detection rate.
        """
        from visualization.tables.detection_tables import generate_detection_table

        raw = [r for r in _load_json("full_evaluation_results.json")
               if r["architecture"] == "AutoGPT"]
        tp = sum(r["true_positives"] for r in raw)
        n = tp + sum(r["false_negatives"] for r in raw)
        pooled = tp / n
        rate_mean = sum(r["detection_rate"] for r in raw) / len(raw)
        assert abs(pooled - rate_mean) > 1e-3, "precondition: the two differ"

        row = next(
            r for r in _body_rows(generate_detection_table()) if r[0] == "AutoGPT"
        )
        assert row[-1].startswith(f"${pooled:.3f} \\pm")

    def test_a_renamed_category_moves_the_header(self, tmp_path):
        """POSITIVE CONTROL: headers cannot be a hardcoded parallel list."""
        from visualization.tables.detection_tables import (
            _load_results,
            generate_detection_table,
        )

        path = tmp_path / "full_evaluation_results.json"
        path.write_text(json.dumps([
            {
                "architecture": "Claude Code",
                "attack_category": "gossip_poisoning",
                "n_attacks": 10, "true_positives": 7, "false_positives": 0,
                "true_negatives": 0, "false_negatives": 3,
                "detection_rate": 0.7, "false_positive_rate": 0.0,
                "avg_latency_ms": 1.0,
            },
        ]))

        archs, cats, means, cis, counts, modes = _load_results(path)
        assert cats == ["gossip_poisoning"]
        assert modes == [], "rows without a 'mode' key contribute nothing"

        latex = generate_detection_table(results={
            "architectures": archs, "categories": cats,
            "means": means, "cis": cis, "counts": counts, "modes": modes,
        })
        header = _body_rows(latex)[0]
        assert header == ["Architecture", "Gossip Poisoning", "Overall"]
        assert "Injection" not in latex
        assert "Evaluation mode" not in latex

    def test_an_unknown_category_is_not_silently_dropped(self, tmp_path):
        """POSITIVE CONTROL for the ``_ordered`` fix in result_loaders.

        The old all-or-nothing guard returned the whole preferred list as
        soon as one label matched, dropping every unrecognised category.
        """
        from data.result_loaders import evaluation_to_detection_matrix

        path = tmp_path / "full_evaluation_results.json"
        path.write_text(json.dumps([
            {
                "architecture": "Claude Code", "attack_category": "impersonation",
                "n_attacks": 4, "true_positives": 2, "false_positives": 0,
                "true_negatives": 0, "false_negatives": 2,
                "detection_rate": 0.5, "false_positive_rate": 0.0,
                "avg_latency_ms": 1.0,
            },
            {
                "architecture": "Claude Code", "attack_category": "zzz_new_category",
                "n_attacks": 4, "true_positives": 1, "false_positives": 0,
                "true_negatives": 0, "false_negatives": 3,
                "detection_rate": 0.25, "false_positive_rate": 0.0,
                "avg_latency_ms": 1.0,
            },
        ]))

        _archs, cats, matrix = evaluation_to_detection_matrix(path=str(path))
        assert cats == ["impersonation", "zzz_new_category"]
        assert matrix.shape == (1, 2)
        assert matrix[0, 1] == 0.25

    def test_a_rate_contradicting_its_own_counts_is_rejected(self, tmp_path):
        """POSITIVE CONTROL: the cell cannot be published either way."""
        from visualization.tables.detection_tables import _load_results

        path = tmp_path / "full_evaluation_results.json"
        path.write_text(json.dumps([
            {
                "architecture": "Claude Code", "attack_category": "impersonation",
                "n_attacks": 10, "true_positives": 5, "false_positives": 0,
                "true_negatives": 0, "false_negatives": 5,
                "detection_rate": 0.99, "false_positive_rate": 0.0,
                "avg_latency_ms": 1.0,
            },
        ]))

        with pytest.raises(ValueError, match="disagrees with its own counts"):
            _load_results(path)

    def test_a_cell_with_no_attacks_prints_a_zero_interval_and_no_overall(self):
        """A row with no trials gets ``--`` for Overall, not a fabricated rate."""
        from visualization.tables.detection_tables import generate_detection_table

        latex = generate_detection_table(results={
            "architectures": ["Empty Arch"],
            "categories": ["impersonation"],
            "means": [[0.0]],
            "cis": [[0.0]],
            "counts": {},
        })
        row = next(r for r in _body_rows(latex) if r[0] == "Empty Arch")
        assert row[-1] == "--"

    def test_missing_counts_give_a_zero_ci_rather_than_raising(self, tmp_path):
        """A JSON row absent from the counts map yields ci = 0, not a crash."""
        from visualization.tables.detection_tables import _load_results

        # Two architectures, but only one has a row for the second category:
        # the (CrewAI, impersonation) cell has no counts entry at all.
        path = tmp_path / "full_evaluation_results.json"
        path.write_text(json.dumps([
            {
                "architecture": "Claude Code", "attack_category": "impersonation",
                "n_attacks": 4, "true_positives": 2, "false_positives": 0,
                "true_negatives": 0, "false_negatives": 2,
                "detection_rate": 0.5, "false_positive_rate": 0.0,
                "avg_latency_ms": 1.0,
            },
            {
                "architecture": "CrewAI", "attack_category": "sybil_attack",
                "n_attacks": 4, "true_positives": 4, "false_positives": 0,
                "true_negatives": 0, "false_negatives": 0,
                "detection_rate": 1.0, "false_positive_rate": 0.0,
                "avg_latency_ms": 1.0,
            },
        ]))
        archs, cats, means, cis, counts, _modes = _load_results(path)
        assert archs == ["Claude Code", "CrewAI"]
        assert cats == ["impersonation", "sybil_attack"]
        assert cis[0][1] == 0.0
        assert cis[1][0] == 0.0

    def test_caption_reports_the_recorded_evaluation_mode(self):
        """Every shipped row is ``mode: simulation``; the caption must say so."""
        from visualization.tables.detection_tables import generate_detection_table

        raw = _load_json("full_evaluation_results.json")
        modes = sorted({r["mode"] for r in raw})
        assert modes == ["simulation"], modes
        assert "Evaluation mode: simulation." in generate_detection_table()


# ===========================================================================
# Tracked .tex artifacts must be regenerable (audit REPRO-04, MSC-15)
# ===========================================================================

def _default_tables():
    if str(_SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS_DIR))
    import generate_all_tables

    return generate_all_tables.default_tables()


class TestTrackedTablesAreRegenerable:
    """Each tracked ``output/tables/*.tex`` must be byte-identical to a fresh run.

    Audit REPRO-04 found ``detection_rates.tex`` was committed from synthetic
    ``DataGenerator`` output while the committed JSON held real values, so
    regenerating it silently changed every cell.  Six of the ten tracked
    files failed this comparison before this wave.
    """

    def test_every_generator_reproduces_its_tracked_artifact(self):
        stale = []
        for name, gen_fn in _default_tables():
            tracked = _TABLE_DIR / name
            assert tracked.exists(), f"{name} is not tracked in output/tables/"
            if tracked.read_text(encoding="utf-8") != gen_fn():
                stale.append(name)
        assert not stale, (
            "tracked table(s) do not match a fresh generator run; regenerate "
            f"with `python scripts/generate_all_tables.py`: {stale}"
        )

    def test_generation_is_deterministic_across_processes(self, tmp_path):
        """Two independent interpreters must emit byte-identical tables."""
        script = (
            "import sys; sys.path.insert(0, {scripts!r});\n"
            "import generate_all_tables as g;\n"
            "sys.exit(g.main(argv=['--output', {out!r}]))\n"
        )
        digests = []
        for run in ("a", "b"):
            out = tmp_path / run
            out.mkdir()
            proc = subprocess.run(
                [sys.executable, "-c",
                 script.format(scripts=str(_SCRIPTS_DIR), out=str(out))],
                capture_output=True, text=True, timeout=110,
                env={**os.environ, "MPLBACKEND": "Agg"},
            )
            assert proc.returncode == 0, proc.stdout + proc.stderr
            digests.append({
                p.name: p.read_text(encoding="utf-8") for p in sorted(out.glob("*.tex"))
            })
        assert digests[0] == digests[1]


class TestGeneratedTablesAreLatexSafe:
    """A data-derived ``_`` in text mode is a hard LaTeX compile error.

    ``hypothesis_tests.tex`` shipped ``H2_detection`` and
    ``assumption_tests.tex`` shipped ``all_groups``; both would abort the
    document with "Missing $ inserted".
    """

    @staticmethod
    def _unescaped_underscores(text: str) -> list[str]:
        # Strip math-mode spans first: an underscore is legal there.
        stripped = re.sub(r"\$[^$]*\$", "", text)
        return [
            m.group(0)
            for m in re.finditer(r"(?<!\\)_", stripped)
        ]

    def test_no_tracked_table_contains_an_unescaped_underscore(self):
        offenders = {}
        for name, _gen in _default_tables():
            found = self._unescaped_underscores(
                (_TABLE_DIR / name).read_text(encoding="utf-8")
            )
            if found:
                offenders[name] = len(found)
        assert not offenders, offenders

    def test_escaper_actually_escapes(self):
        """POSITIVE CONTROL: the detector fires on unescaped input."""
        from visualization.tables.latex import escape_latex

        assert self._unescaped_underscores("H2_detection") == ["_"]
        assert self._unescaped_underscores(escape_latex("H2_detection")) == []
        assert escape_latex("100% & x") == r"100\% \& x"
        assert escape_latex(r"a\b") == r"a\textbackslash{}b"
