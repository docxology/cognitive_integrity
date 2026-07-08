"""Figure Registry Module
=========================

Programmatic figure and table tracking for the CIF manuscript.

Provides:
- ``FigureRegistry``: Core class for tracking figures/tables with sequential
  auto-numbering, duplicate label detection, and JSON serialisation.
- ``AutoNumberer``: Processes manuscript markdown files to populate the registry
  and injects \\label{} anchors for XeLaTeX cross-referencing.
- Validation helpers to detect duplicate labels and verify \\Cref{} targets.

Typical use::

    from manuscript.figure_registry import FigureRegistry, AutoNumberer

    registry = FigureRegistry()
    numberer = AutoNumberer(registry)
    numberer.process_directory(Path("manuscript"))
    registry.save(Path("output/data/figure_registry.json"))
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class FigureEntry:
    """A registered figure or table."""

    label: str                       # e.g. "fig:cif-comprehensive"
    number: int                      # Sequential number (1-based)
    caption: str                     # Human-readable caption / first sentence
    section: str                     # Source section stem (e.g. "01_introduction")
    entry_type: str                  # "figure" or "table"

    @property
    def display(self) -> str:
        """Short display string, e.g. 'Fig. 3' or 'Table 7'."""
        prefix = "Fig." if self.entry_type == "figure" else "Table"
        return f"{prefix} {self.number}"

    def to_dict(self) -> dict:
        return {
            "number": self.number,
            "display": self.display,
            "caption": self.caption,
            "section": self.section,
            "label": self.label,
            "type": self.entry_type,
        }


# ---------------------------------------------------------------------------
# FigureRegistry
# ---------------------------------------------------------------------------


class FigureRegistry:
    """Registry for manuscript figures and tables with sequential numbering.

    Examples
    --------
    >>> reg = FigureRegistry()
    >>> reg.add_figure("fig:foo", "My caption", "01_intro")
    >>> reg.add_table("tab:bar", "My table caption", "02_methods")
    >>> reg.get_number("fig:foo")
    1
    >>> reg.get_number("tab:bar")
    1
    >>> d = reg.to_json()
    >>> "fig:foo" in d
    True
    """

    def __init__(self) -> None:
        self._figures: List[FigureEntry] = []
        self._tables: List[FigureEntry] = []
        self._fig_index: Dict[str, FigureEntry] = {}
        self._tab_index: Dict[str, FigureEntry] = {}

    # ------------------------------------------------------------------
    # Add entries
    # ------------------------------------------------------------------

    def add_figure(self, label: str, caption: str, section: str) -> FigureEntry:
        """Register a figure.

        Parameters
        ----------
        label:   Full pandoc-crossref label, e.g. ``fig:cif-comprehensive``.
        caption: Short caption text (first sentence / first 120 chars).
        section: Section stem, e.g. ``01_introduction``.

        Returns the created ``FigureEntry``.

        Raises ``ValueError`` on duplicate label.
        """
        if label in self._fig_index:
            raise ValueError(f"Duplicate figure label: {label!r}")
        entry = FigureEntry(
            label=label,
            number=len(self._figures) + 1,
            caption=caption,
            section=section,
            entry_type="figure",
        )
        self._figures.append(entry)
        self._fig_index[label] = entry
        logger.debug("Registered %s as Fig. %d", label, entry.number)
        return entry

    def add_table(self, label: str, caption: str, section: str) -> FigureEntry:
        """Register a table.

        Parameters
        ----------
        label:   Full label, e.g. ``tab:related-work-comparison``.  The ``tbl:``
                 prefix is automatically normalised to ``tab:``.
        caption: Short caption text.
        section: Section stem.

        Returns the created ``FigureEntry``.

        Raises ``ValueError`` on duplicate (canonical) label.
        """
        canonical = label.replace("tbl:", "tab:")
        if canonical in self._tab_index:
            raise ValueError(f"Duplicate table label: {canonical!r}")
        entry = FigureEntry(
            label=canonical,
            number=len(self._tables) + 1,
            caption=caption,
            section=section,
            entry_type="table",
        )
        self._tables.append(entry)
        self._tab_index[canonical] = entry
        logger.debug("Registered %s as Table %d", canonical, entry.number)
        return entry

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get_number(self, label: str) -> Optional[int]:
        """Return the sequential number for *label*, or None if not found."""
        canonical = label.replace("tbl:", "tab:")
        if canonical in self._fig_index:
            return self._fig_index[canonical].number
        if canonical in self._tab_index:
            return self._tab_index[canonical].number
        return None

    def get_entry(self, label: str) -> Optional[FigureEntry]:
        """Return the ``FigureEntry`` for *label*, or None."""
        canonical = label.replace("tbl:", "tab:")
        return self._fig_index.get(canonical) or self._tab_index.get(canonical)

    @property
    def figures(self) -> List[FigureEntry]:
        return list(self._figures)

    @property
    def tables(self) -> List[FigureEntry]:
        return list(self._tables)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_no_duplicates(self) -> List[str]:
        """Check for duplicate labels (should be empty after normal use).

        Returns list of error strings.
        """
        seen: dict[str, list] = {}
        errors: list[str] = []
        for entry in self._figures + self._tables:
            seen.setdefault(entry.label, []).append(entry.section)
        for lbl, sections in seen.items():
            if len(sections) > 1:
                errors.append(f"Duplicate label {lbl!r} in sections: {sections}")
        return errors

    def validate_cref_targets(self, manuscript_dir: Path) -> List[str]:
        """Verify every ``\\Cref{fig:…}`` / ``\\Cref{tab:…}`` in the manuscript
        has a corresponding registry entry.

        Returns list of warning strings.
        """
        all_labels = set(self._fig_index) | set(self._tab_index)
        warnings: list[str] = []
        for md_file in sorted(manuscript_dir.glob("*.md")):
            content = md_file.read_text(encoding="utf-8")
            for m in re.finditer(r"\\[Cc]ref\{((?:fig|tab|tbl):[^}]+)\}", content):
                target = m.group(1)
                canonical = target.replace("tbl:", "tab:")
                if canonical not in all_labels:
                    warnings.append(
                        f"{md_file.name}: unresolved \\Cref{{{target!r}}}"
                    )
        return warnings

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_json(self) -> dict:
        """Return a plain dict suitable for JSON serialisation."""
        result: dict = {}
        for entry in self._figures + self._tables:
            result[entry.label] = entry.to_dict()
        return result

    def save(self, path: Path) -> None:
        """Write the registry to *path* as indented JSON."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_json(), indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("Registry saved to %s (%d entries)", path, len(self._figures) + len(self._tables))  # noqa: E501

    @classmethod
    def load(cls, path: Path) -> "FigureRegistry":
        """Load a previously saved registry JSON."""
        data = json.loads(path.read_text(encoding="utf-8"))
        reg = cls()
        for label, entry in data.items():
            if entry["type"] == "figure":
                e = FigureEntry(
                    label=label,
                    number=entry["number"],
                    caption=entry["caption"],
                    section=entry["section"],
                    entry_type="figure",
                )
                reg._figures.append(e)
                reg._fig_index[label] = e
            else:
                e = FigureEntry(
                    label=label,
                    number=entry["number"],
                    caption=entry["caption"],
                    section=entry["section"],
                    entry_type="table",
                )
                reg._tables.append(e)
                reg._tab_index[label] = e
        return reg


# ---------------------------------------------------------------------------
# AutoNumberer
# ---------------------------------------------------------------------------

_SECTION_ORDER = [
    "00_abstract", "01_introduction", "01b_related_work",
    "01c_theoretical_connections", "02_methodology", "02a_defense_algorithms",
    "02b_configuration_parameters", "02c_composability_algebra",
    "03_attack_corpus", "03b_attack_examples", "03c_attack_ethics",
    "04_experimental_setup", "05_results", "05b_statistical_significance",
    "05c_sensitivity_analysis", "05d_ablation_and_scalability",
    "05e_bayesian_uncertainty", "05f_architecture_gap_analysis",
    "05g_adversarial_training", "05h_redteam_evaluation", "06_discussion",
    "07_conclusion", "08_category_theoretic_foundations", "99_references",
    "S01_notation_reference", "S02_detection_algorithms",
    "S03_benchmark_implementation", "S04_model_checking", "S05_framework_api",
    "S06_deployment_guide", "S07_algorithm_pseudocode",
    "S08_parametric_analysis", "S09_functional_api",
    "S10_information_geometry", "S11_adversarial_training_theory",
    "S12_composable_visualization",
]


def _sort_key(stem: str) -> int:
    try:
        return _SECTION_ORDER.index(stem)
    except ValueError:
        return len(_SECTION_ORDER)


class AutoNumberer:
    """Scan manuscript markdown files and populate a ``FigureRegistry``.

    Usage::

        reg = FigureRegistry()
        numberer = AutoNumberer(reg)
        numberer.process_directory(Path("manuscript"))
        warnings = reg.validate_cref_targets(Path("manuscript"))
    """

    def __init__(self, registry: FigureRegistry) -> None:
        self.registry = registry

    def process_directory(self, manuscript_dir: Path) -> None:
        """Process all .md files in *manuscript_dir* in document order."""
        md_files = sorted(manuscript_dir.glob("*.md"), key=lambda f: _sort_key(f.stem))
        for md_file in md_files:
            if md_file.name == "preamble.md":
                continue
            self._process_file(md_file)

    def _extract_caption(self, content: str, bare_label: str, is_figure: bool) -> str:
        if is_figure:
            pattern = re.compile(
                r"!\[([^\]]+)\]\([^)]+\)\{#fig:" + re.escape(bare_label) + r"[^}]*\}",
                re.DOTALL,
            )
            m = pattern.search(content)
            if m:
                raw = m.group(1).strip()
                end = raw.find(".")
                return raw[: end + 1] if 0 < end < 120 else raw[:120]
        else:
            bare_esc = re.escape(bare_label)
            pattern = re.compile(
                r"\*\*(?:Table|Tab)[^*]*\*\*\s*\{#(?:tab|tbl):" + bare_esc + r"[^}]*\}",
                re.IGNORECASE,
            )
            m = pattern.search(content)
            if m:
                return re.sub(r"\{#[^}]+\}", "", m.group(0)).strip(" *")[:120]
        return bare_label.replace("-", " ").replace("_", " ").title()

    def _process_file(self, md_file: Path) -> None:
        section = md_file.stem
        content = md_file.read_text(encoding="utf-8")

        # Figures
        for m in re.finditer(r"\{#fig:([^}\s]+)", content):
            bare = m.group(1).rstrip()
            label = f"fig:{bare}"
            caption = self._extract_caption(content, bare, is_figure=True)
            try:
                self.registry.add_figure(label, caption, section)
            except ValueError:
                logger.warning("Duplicate figure label '%s' in %s — skipped", label, section)

        # Tables (both tab: and tbl:)
        for prefix in ("tab", "tbl"):
            for m in re.finditer(r"\{#" + prefix + r":([^}\s]+)", content):
                bare = m.group(1).rstrip()
                label = f"tab:{bare}"  # normalise
                caption = self._extract_caption(content, bare, is_figure=False)
                try:
                    self.registry.add_table(label, caption, section)
                except ValueError:
                    logger.warning("Duplicate table label '%s' in %s — skipped", label, section)
