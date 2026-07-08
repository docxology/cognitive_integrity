"""Tests for src/manuscript/figure_registry.py.

Covers:
- FigureEntry: dataclass, display property, to_dict.
- FigureRegistry: add_figure, add_table, get_number, get_entry,
  figures/tables properties, validate_no_duplicates, validate_cref_targets,
  to_json, save, load.
- AutoNumberer: process_directory, _extract_caption, _process_file.
- _sort_key helper.

All tests use real computation. No mocks.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from manuscript.figure_registry import (
    AutoNumberer,
    FigureEntry,
    FigureRegistry,
    _sort_key,
)

# ---------------------------------------------------------------------------
# FigureEntry
# ---------------------------------------------------------------------------


class TestFigureEntry:
    """Tests for the FigureEntry dataclass."""

    def test_basic_construction(self):
        e = FigureEntry(
            label="fig:foo", number=3, caption="A caption.", section="01_intro", entry_type="figure"
        )
        assert e.label == "fig:foo"
        assert e.number == 3
        assert e.caption == "A caption."
        assert e.section == "01_intro"
        assert e.entry_type == "figure"

    def test_display_figure(self):
        e = FigureEntry(label="fig:foo", number=5, caption="x", section="s", entry_type="figure")
        assert e.display == "Fig. 5"

    def test_display_table(self):
        e = FigureEntry(label="tab:bar", number=2, caption="x", section="s", entry_type="table")
        assert e.display == "Table 2"

    def test_to_dict_keys(self):
        e = FigureEntry(label="fig:cif", number=1, caption="CIF.", section="02_methods", entry_type="figure")  # noqa: E501
        d = e.to_dict()
        assert "number" in d
        assert "display" in d
        assert "caption" in d
        assert "section" in d
        assert "label" in d
        assert "type" in d

    def test_to_dict_values(self):
        e = FigureEntry(label="fig:roc", number=7, caption="ROC curve.", section="05_results", entry_type="figure")  # noqa: E501
        d = e.to_dict()
        assert d["number"] == 7
        assert d["display"] == "Fig. 7"
        assert d["caption"] == "ROC curve."
        assert d["section"] == "05_results"
        assert d["label"] == "fig:roc"
        assert d["type"] == "figure"


# ---------------------------------------------------------------------------
# FigureRegistry
# ---------------------------------------------------------------------------


class TestFigureRegistry:
    """Tests for the FigureRegistry class."""

    def _make_registry_with_entries(self):
        reg = FigureRegistry()
        reg.add_figure("fig:alpha", "Figure A.", "01_intro")
        reg.add_figure("fig:beta", "Figure B.", "02_methods")
        reg.add_table("tab:gamma", "Table G.", "03_results")
        return reg

    def test_empty_registry(self):
        reg = FigureRegistry()
        assert reg.figures == []
        assert reg.tables == []

    def test_add_figure_returns_entry(self):
        reg = FigureRegistry()
        e = reg.add_figure("fig:foo", "Caption.", "01_intro")
        assert isinstance(e, FigureEntry)
        assert e.label == "fig:foo"
        assert e.number == 1
        assert e.entry_type == "figure"

    def test_add_table_returns_entry(self):
        reg = FigureRegistry()
        e = reg.add_table("tab:results", "Table caption.", "05_results")
        assert isinstance(e, FigureEntry)
        assert e.entry_type == "table"
        assert e.number == 1

    def test_figures_sequential_numbering(self):
        reg = self._make_registry_with_entries()
        assert reg.figures[0].number == 1
        assert reg.figures[1].number == 2

    def test_tables_sequential_numbering(self):
        reg = self._make_registry_with_entries()
        assert reg.tables[0].number == 1

    def test_get_number_figure(self):
        reg = self._make_registry_with_entries()
        assert reg.get_number("fig:alpha") == 1
        assert reg.get_number("fig:beta") == 2

    def test_get_number_table(self):
        reg = self._make_registry_with_entries()
        assert reg.get_number("tab:gamma") == 1

    def test_get_number_nonexistent_returns_none(self):
        reg = FigureRegistry()
        assert reg.get_number("fig:nonexistent") is None

    def test_get_entry_returns_figure_entry(self):
        reg = self._make_registry_with_entries()
        entry = reg.get_entry("fig:alpha")
        assert entry is not None
        assert entry.label == "fig:alpha"

    def test_get_entry_nonexistent_returns_none(self):
        reg = FigureRegistry()
        assert reg.get_entry("fig:unknown") is None

    def test_duplicate_figure_raises(self):
        reg = FigureRegistry()
        reg.add_figure("fig:dup", "First.", "01_intro")
        with pytest.raises(ValueError, match="Duplicate figure"):
            reg.add_figure("fig:dup", "Second.", "02_methods")

    def test_duplicate_table_raises(self):
        reg = FigureRegistry()
        reg.add_table("tab:dup", "First table.", "01_intro")
        with pytest.raises(ValueError, match="Duplicate table"):
            reg.add_table("tab:dup", "Second table.", "02_methods")

    def test_tbl_prefix_normalised_to_tab(self):
        reg = FigureRegistry()
        reg.add_table("tbl:example", "Caption.", "01_intro")
        # Should be accessible via tab: prefix
        assert reg.get_number("tab:example") == 1

    def test_tbl_duplicate_detected_after_normalisation(self):
        reg = FigureRegistry()
        reg.add_table("tab:dup2", "First.", "01_intro")
        with pytest.raises(ValueError):
            reg.add_table("tbl:dup2", "Second.", "02_methods")

    def test_figures_property_returns_copy(self):
        reg = self._make_registry_with_entries()
        figs = reg.figures
        figs.clear()  # should not affect registry
        assert len(reg.figures) == 2

    def test_tables_property_returns_copy(self):
        reg = self._make_registry_with_entries()
        tabs = reg.tables
        tabs.clear()
        assert len(reg.tables) == 1

    def test_validate_no_duplicates_clean(self):
        reg = self._make_registry_with_entries()
        errors = reg.validate_no_duplicates()
        assert errors == []

    def test_to_json_structure(self):
        reg = self._make_registry_with_entries()
        j = reg.to_json()
        assert isinstance(j, dict)
        assert "fig:alpha" in j
        assert "fig:beta" in j
        assert "tab:gamma" in j

    def test_to_json_serialisable(self):
        reg = self._make_registry_with_entries()
        j = reg.to_json()
        # Should be JSON-serialisable without errors
        json_str = json.dumps(j)
        assert len(json_str) > 0

    def test_save_and_load_roundtrip(self, tmp_path):
        reg = self._make_registry_with_entries()
        save_path = tmp_path / "registry.json"
        reg.save(save_path)
        assert save_path.exists()

        loaded = FigureRegistry.load(save_path)
        assert len(loaded.figures) == 2
        assert len(loaded.tables) == 1
        assert loaded.get_number("fig:alpha") == 1
        assert loaded.get_number("tab:gamma") == 1

    def test_save_creates_parent_dirs(self, tmp_path):
        reg = FigureRegistry()
        reg.add_figure("fig:x", "Test.", "01_intro")
        deep_path = tmp_path / "nested" / "deep" / "registry.json"
        reg.save(deep_path)
        assert deep_path.exists()

    def test_validate_cref_targets_no_warnings_when_registered(self, tmp_path):
        reg = FigureRegistry()
        reg.add_figure("fig:cif-arch", "CIF Architecture.", "02_methods")

        # Write a markdown file with a Cref to the registered figure
        md = tmp_path / "02_methods.md"
        md.write_text("See \\Cref{fig:cif-arch} for details.\n")

        warnings = reg.validate_cref_targets(tmp_path)
        assert warnings == []

    def test_validate_cref_targets_warns_on_unresolved(self, tmp_path):
        reg = FigureRegistry()
        # Not adding any figures — so Cref targets are unresolved

        md = tmp_path / "02_methods.md"
        md.write_text("See \\Cref{fig:missing} for details.\n")

        warnings = reg.validate_cref_targets(tmp_path)
        assert len(warnings) == 1
        assert "fig:missing" in warnings[0]

    def test_validate_cref_targets_empty_dir(self, tmp_path):
        reg = FigureRegistry()
        warnings = reg.validate_cref_targets(tmp_path)
        assert warnings == []


# ---------------------------------------------------------------------------
# _sort_key
# ---------------------------------------------------------------------------


class TestSortKey:
    """Tests for the _sort_key helper."""

    def test_known_section_returns_index(self):
        k = _sort_key("01_introduction")
        assert isinstance(k, int)
        assert k >= 0

    def test_unknown_section_returns_large_number(self):
        k_unknown = _sort_key("__completely_unknown_section_xyz__")
        k_known = _sort_key("01_introduction")
        assert k_unknown > k_known

    def test_ordering_consistent(self):
        # Abstract comes before Introduction
        k_abstract = _sort_key("00_abstract")
        k_intro = _sort_key("01_introduction")
        assert k_abstract < k_intro

    def test_appendix_before_references(self):
        # S01 sections (appendices) should come before unknown
        k_s01 = _sort_key("S01_notation_reference")
        k_unknown = _sort_key("unknown_section")
        assert k_s01 < k_unknown


# ---------------------------------------------------------------------------
# AutoNumberer
# ---------------------------------------------------------------------------


class TestAutoNumberer:
    """Tests for the AutoNumberer class."""

    def _write_md(self, path: Path, content: str) -> None:
        path.write_text(content, encoding="utf-8")

    def test_process_directory_registers_figures(self, tmp_path):
        self._write_md(
            tmp_path / "01_introduction.md",
            "![My Figure]( path/to/fig.pdf){#fig:cif-arch}\n"
        )
        reg = FigureRegistry()
        numberer = AutoNumberer(reg)
        numberer.process_directory(tmp_path)
        assert reg.get_number("fig:cif-arch") == 1

    def test_process_directory_registers_tables(self, tmp_path):
        self._write_md(
            tmp_path / "05_results.md",
            "**Table results** {#tab:detection-results}\n\n| A | B |\n|---|---|\n| 1 | 2 |\n"
        )
        reg = FigureRegistry()
        numberer = AutoNumberer(reg)
        numberer.process_directory(tmp_path)
        assert reg.get_number("tab:detection-results") == 1

    def test_process_directory_skips_preamble(self, tmp_path):
        # preamble.md should be ignored
        self._write_md(
            tmp_path / "preamble.md",
            "![Preamble Figure](p.pdf){#fig:preamble-fig}\n"
        )
        reg = FigureRegistry()
        numberer = AutoNumberer(reg)
        numberer.process_directory(tmp_path)
        assert reg.get_number("fig:preamble-fig") is None

    def test_process_directory_multiple_files(self, tmp_path):
        self._write_md(
            tmp_path / "01_introduction.md",
            "![Figure 1](f1.pdf){#fig:intro-fig}\n"
        )
        self._write_md(
            tmp_path / "02_methodology.md",
            "![Figure 2](f2.pdf){#fig:method-fig}\n"
        )
        reg = FigureRegistry()
        numberer = AutoNumberer(reg)
        numberer.process_directory(tmp_path)
        assert len(reg.figures) == 2

    def test_duplicate_figure_in_two_files_logged_not_raised(self, tmp_path):
        self._write_md(
            tmp_path / "01_introduction.md",
            "![Fig A](fa.pdf){#fig:dup}\n"
        )
        self._write_md(
            tmp_path / "02_methodology.md",
            "![Fig A again](fa2.pdf){#fig:dup}\n"
        )
        reg = FigureRegistry()
        numberer = AutoNumberer(reg)
        # Should not raise — duplicate is logged and skipped
        numberer.process_directory(tmp_path)
        # Only first occurrence registered
        assert reg.get_number("fig:dup") == 1
        assert len(reg.figures) == 1

    def test_empty_directory_produces_empty_registry(self, tmp_path):
        reg = FigureRegistry()
        numberer = AutoNumberer(reg)
        numberer.process_directory(tmp_path)
        assert reg.figures == []
        assert reg.tables == []

    def test_tbl_prefix_normalised(self, tmp_path):
        self._write_md(
            tmp_path / "05_results.md",
            "**Table of data** {#tbl:my-table}\n"
        )
        reg = FigureRegistry()
        numberer = AutoNumberer(reg)
        numberer.process_directory(tmp_path)
        # tbl: should normalise to tab:
        assert reg.get_number("tab:my-table") == 1
