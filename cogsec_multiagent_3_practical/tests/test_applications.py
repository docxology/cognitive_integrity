"""Tests for the cross-domain application layer: ``src/applications/domain_coverage.py``.

These exercise the real figure/renderer code (no mocks) and independently bind
the two data matrices (``ATTACK_PATTERNS`` and ``COVERAGE_MATRIX``) to the
manuscript's §10.1 and §10.4 tables, so a renumbered domain or a flipped matrix
row cannot silently drift from the paper.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np

from src.applications.domain_coverage import (
    ATTACK_PATTERNS,
    COVERAGE_MATRIX,
    MECHANISMS,
    domain_coverage_payload,
    plot_attack_patterns,
    plot_cif_mechanism_coverage,
    render_domain_coverage_figures,
)

PROJECT_ROOT = Path(__file__).parent.parent
DISCOURSE = PROJECT_ROOT / "manuscript" / "10_cross_domain_discussion.md"


# ---------------------------------------------------------------------------
# Payload shape and totals
# ---------------------------------------------------------------------------


class TestDomainCoveragePayload:
    def test_shapes_are_consistent(self):
        payload = domain_coverage_payload()
        assert len(payload["domains"]) == 10
        assert len(payload["domains_short"]) == 10
        assert len(payload["pattern_labels"]) == 3
        assert len(payload["mechanisms"]) == 5
        assert np.asarray(payload["attack_patterns"]).shape == (10, 3)
        assert np.asarray(payload["coverage_matrix"]).shape == (5, 10)

    def test_attack_pattern_totals_are_5_1_4(self):
        """Column totals of the pattern matrix, pinned to the manuscript table.

        Cyber-Security was previously counted as a Constraint Relaxation, giving
        5/2/3.  Its post-attack design matrix introduces off-diagonal coupling
        into a diagonal matrix while leaving the diagonal magnitudes intact,
        which is the Context Boundary Violation signature, so the totals are
        5/1/4.  This pin exists so the matrix, the section-10.1 table and the
        per-domain sections cannot drift apart.
        """
        totals = ATTACK_PATTERNS.sum(axis=0).tolist()
        assert totals == [5, 1, 4], totals

    def test_mechanism_row_totals_are_3_4_5_3_3(self):
        totals = COVERAGE_MATRIX.sum(axis=1).tolist()
        assert totals == [3, 4, 5, 3, 3], totals

    def test_coverage_matrix_is_binary(self):
        assert set(COVERAGE_MATRIX.flatten().tolist()) <= {0.0, 1.0}


# ---------------------------------------------------------------------------
# Rendering (real matplotlib output, no mocks)
# ---------------------------------------------------------------------------


class TestRendering:
    def test_plot_attack_patterns_writes_png_and_pdf(self, tmp_path):
        paths = plot_attack_patterns(tmp_path)
        assert len(paths) == 2
        for p in paths:
            assert p.exists() and p.stat().st_size > 0, p

    def test_plot_cif_mechanism_coverage_writes_png_and_pdf(self, tmp_path):
        paths = plot_cif_mechanism_coverage(tmp_path)
        assert len(paths) == 2
        for p in paths:
            assert p.exists() and p.stat().st_size > 0, p

    def test_render_domain_coverage_figures_returns_all_four(self, tmp_path):
        paths = render_domain_coverage_figures(tmp_path)
        names = {p.name for p in paths}
        assert names == {
            "domain_coverage.png",
            "domain_coverage.pdf",
            "cif_mechanism_coverage.png",
            "cif_mechanism_coverage.pdf",
        }


# ---------------------------------------------------------------------------
# Manuscript binding (independent of the code's own constants)
# ---------------------------------------------------------------------------


def _has_check(line: str) -> bool:
    # Markdown table cells mark a hit with ``\\checkmark`` (possibly ``$\\checkmark$``).
    return bool(re.search(r"\\checkmark", line))


class TestAttackPatternsMatchManuscript:
    def test_matches_section_10_1_table(self):
        text = DISCOURSE.read_text()
        # Rows: "| N. Domain | <p1> | <p2> | <p3> |" with optional checkmarks.
        rows = 0
        expected = np.zeros((10, 3), dtype=float)
        for line in text.splitlines():
            m = re.match(r"^\|\s*\d+\.\s+[^|]+\|([^|]*)\|([^|]*)\|([^|]*)\|\s*$", line.strip())
            if m and rows < 10:
                cells = [m.group(1), m.group(2), m.group(3)]
                expected[rows] = [1.0 if _has_check(c) else 0.0 for c in cells]
                rows += 1
        assert rows == 10, f"parsed only {rows} §10.1 domain rows"
        assert (ATTACK_PATTERNS == expected).all()


class TestCoverageMatrixMatchesManuscript:
    def test_matches_section_10_4_table(self):
        text = DISCOURSE.read_text()
        # MECHANISMS entries are e.g. "Cognitive\nFirewall" — normalize to the
        # space-separated form that appears in the manuscript table header.
        mech_bases = [m.replace("\n", " ") for m in MECHANISMS]
        mech_rows: dict[str, list[int]] = {}
        for line in text.splitlines():
            cells = line.strip().split("|")
            # cells: ['', ' CIF Mechanism ', ' RE ', ..., ' FN ', ' Total ', '']
            if len(cells) < 13:
                continue
            name = cells[1].strip()
            dom_cells = cells[2:12]
            if len(dom_cells) != 10:
                continue
            for base in mech_bases:
                if name.startswith(base):
                    mech_rows[base] = [1 if _has_check(c) else 0 for c in dom_cells]

        assert len(mech_rows) == 5, f"parsed {len(mech_rows)} mechanism rows (expected 5)"
        # Row order must follow the MECHANISMS order (index i -> row i).
        for i, base in enumerate(mech_bases):
            assert base in mech_rows, f"mechanism {base!r} missing from §10.4"
            row = np.asarray(mech_rows[base], dtype=float)
            assert (COVERAGE_MATRIX[i] == row).all(), (
                f"COVERAGE_MATRIX row {i} ({base!r}) differs from manuscript: "
                f"matrix={COVERAGE_MATRIX[i].tolist()} manuscript={row.tolist()}"
            )
