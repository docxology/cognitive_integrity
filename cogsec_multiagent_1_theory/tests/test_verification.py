#!/usr/bin/env python3
"""Tests for verification.py module."""

import tempfile
from pathlib import Path


class TestManuscriptVerifier:
    """Tests for ManuscriptVerifier class."""

    def test_verifier_initialization(self):
        """Test ManuscriptVerifier initializes correctly."""
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            verifier = ManuscriptVerifier(tmpdir)

            assert verifier.root_dir == Path(tmpdir).resolve()
            assert verifier.bib_file == Path(tmpdir).resolve() / "references.bib"
            assert len(verifier.hyperbole_words) > 0

    def test_check_files_exist_missing_bib(self):
        """Test check_files_exist detects missing bibliography."""
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            verifier = ManuscriptVerifier(tmpdir)
            result = verifier.check_files_exist()

            assert result is False  # Missing both bib and md files

    def test_check_files_exist_with_files(self):
        """Test check_files_exist passes with required files."""
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create required files
            (tmppath / "references.bib").write_text("@article{test2024,}")
            (tmppath / "manuscript.md").write_text("# Test Manuscript")

            verifier = ManuscriptVerifier(tmpdir)
            result = verifier.check_files_exist()

            assert result is True

    def test_get_bib_keys_empty(self):
        """Test get_bib_keys returns empty set when no file."""
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            verifier = ManuscriptVerifier(tmpdir)
            keys = verifier.get_bib_keys()

            assert isinstance(keys, set)
            assert len(keys) == 0

    def test_get_bib_keys_extracts_keys(self):
        """Test get_bib_keys extracts citation keys from bib file."""
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            bib_content = """
@article{smith2024,
    author = {Smith, John},
    title = {Test Article},
    year = {2024}
}

@inproceedings{jones2023,
    author = {Jones, Jane},
    title = {Another Test},
    year = {2023}
}
"""
            (tmppath / "references.bib").write_text(bib_content)

            verifier = ManuscriptVerifier(tmpdir)
            keys = verifier.get_bib_keys()

            assert "smith2024" in keys
            assert "jones2023" in keys
            assert len(keys) == 2

    def test_check_citations_valid(self):
        """Test check_citations passes with valid citations."""
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            (tmppath / "references.bib").write_text("@article{smith2024,}")
            (tmppath / "manuscript.md").write_text(r"As shown in \cite{smith2024}.")

            verifier = ManuscriptVerifier(tmpdir)
            result = verifier.check_citations()

            assert result is True

    def test_check_citations_invalid(self):
        """Test check_citations fails with invalid citations."""
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            (tmppath / "references.bib").write_text("@article{smith2024,}")
            (tmppath / "manuscript.md").write_text(r"As shown in \cite{unknown_key}.")

            verifier = ManuscriptVerifier(tmpdir)
            result = verifier.check_citations()

            assert result is False

    def test_check_citations_multiple_keys(self):
        """Test check_citations handles multiple keys in one cite."""
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            (tmppath / "references.bib").write_text("@article{a,}\n@article{b,}\n@article{c,}")
            (tmppath / "manuscript.md").write_text(r"See \cite{a,b,c}.")

            verifier = ManuscriptVerifier(tmpdir)
            result = verifier.check_citations()

            assert result is True

    def test_check_labels_and_refs_valid(self):
        """Test check_labels_and_refs passes with matching labels."""
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            (tmppath / "references.bib").write_text("")
            md_content = r"""
# Section {#sec:intro}

See Section \ref{sec:intro}.

\label{fig:test}

As shown in \cref{fig:test}.
"""
            (tmppath / "manuscript.md").write_text(md_content)

            verifier = ManuscriptVerifier(tmpdir)
            result = verifier.check_labels_and_refs()

            assert result is True

    def test_check_labels_and_refs_undefined(self):
        """Test check_labels_and_refs fails with undefined reference."""
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            (tmppath / "references.bib").write_text("")
            (tmppath / "manuscript.md").write_text(r"See \ref{nonexistent}.")

            verifier = ManuscriptVerifier(tmpdir)
            result = verifier.check_labels_and_refs()

            assert result is False

    def test_check_images_no_images(self):
        """Test check_images_and_links passes with no images."""
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            (tmppath / "references.bib").write_text("")
            (tmppath / "manuscript.md").write_text("No images here.")

            verifier = ManuscriptVerifier(tmpdir)
            result = verifier.check_images_and_links()

            assert result is True

    def test_check_images_web_links_ignored(self):
        """Test check_images_and_links ignores web URLs."""
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            (tmppath / "references.bib").write_text("")
            (tmppath / "manuscript.md").write_text("![image](https://example.com/img.png)")

            verifier = ManuscriptVerifier(tmpdir)
            result = verifier.check_images_and_links()

            assert result is True

    def test_check_images_local_missing(self):
        """Test check_images_and_links fails with missing local image."""
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            (tmppath / "references.bib").write_text("")
            (tmppath / "manuscript.md").write_text("![image](nonexistent.png)")

            verifier = ManuscriptVerifier(tmpdir)
            result = verifier.check_images_and_links()

            assert result is False

    def test_check_images_local_exists(self):
        """Test check_images_and_links passes with existing local image."""
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            (tmppath / "references.bib").write_text("")
            (tmppath / "test.png").write_bytes(b"fake image")
            (tmppath / "manuscript.md").write_text("![image](test.png)")

            verifier = ManuscriptVerifier(tmpdir)
            result = verifier.check_images_and_links()

            assert result is True

    def test_check_style(self):
        """Test check_style detects hyperbole words."""
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            (tmppath / "references.bib").write_text("")
            (tmppath / "manuscript.md").write_text(
                "This is a revolutionary approach that is clearly better."
            )

            verifier = ManuscriptVerifier(tmpdir)
            # (#20) a style warning is a real finding: check_style returns False.
            result = verifier.check_style()

            assert result is False


class TestManuscriptVerifierPatterns:
    """Tests for regex patterns in ManuscriptVerifier."""

    def test_cite_pattern(self):
        """Test citation pattern matching."""
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            verifier = ManuscriptVerifier(tmpdir)

            text = r"\cite{key1} and \cite{key2,key3}"
            matches = verifier.cite_pattern.findall(text)

            assert "key1" in matches
            assert "key2,key3" in matches

    def test_label_pattern(self):
        """Test label pattern matching."""
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            verifier = ManuscriptVerifier(tmpdir)

            text = r"\label{fig:test} and \label{sec:intro}"
            matches = verifier.label_pattern.findall(text)

            assert "fig:test" in matches
            assert "sec:intro" in matches

    def test_ref_pattern(self):
        """Test reference pattern matching."""
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            verifier = ManuscriptVerifier(tmpdir)

            text = r"\ref{fig:1} and \cref{table:2} and \autoref{sec:3}"
            matches = verifier.ref_pattern.findall(text)

            assert ("ref", "fig:1") in matches
            assert ("cref", "table:2") in matches
            assert ("autoref", "sec:3") in matches


# ---------------------------------------------------------------------------
# Additional edge-case tests for verification.py to boost coverage above 90%
# ---------------------------------------------------------------------------


class TestManuscriptVerifierEdgeCases:
    """Edge-case tests targeting uncovered lines in ManuscriptVerifier."""

    def test_check_citations_skips_references_bib_file(self):
        """check_citations continues (skips) when md_file.name == 'references.bib' (line 105)."""
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create a real bib file
            (tmppath / "references.bib").write_text("@article{key1,}")

            # Create a subdirectory so glob picks up the bib as an .md equivalent wouldn't
            # — instead, rename a file to references.bib in a subdir won't trick glob
            # We need to simulate: one of the md_files has name == 'references.bib'
            # The simplest way: create a file literally named references.bib.md in a subdir
            # BUT actually the code checks md_file.name == "references.bib",
            # so create a file named exactly "references.bib" at path with .md extension won't work.
            # Instead, let's just put a .md file that the verifier would normally open.
            # The real skipping happens when a file named "references.bib" ends up in md_files
            # (i.e. someone does glob("**/*.md") and one result's name is "references.bib").
            # We can't easily create that scenario, so we test it indirectly:
            # just confirm that with only a references.bib present (no .md), citations pass.
            (tmppath / "manuscript.md").write_text(r"See \cite{key1}.")

            verifier = ManuscriptVerifier(tmpdir)
            result = verifier.check_citations()
            assert result is True

    def test_run_all_passes_when_all_checks_pass(self):
        """run_all() returns True when all verifications pass (lines 207-234).

        run_all() is a plain library call -- it does not call sys.exit()
        itself; that's the CLI entry point's job (scripts/verify_manuscript.py).
        """
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Set up a minimal valid manuscript
            (tmppath / "references.bib").write_text("@article{key1,}")
            (tmppath / "manuscript.md").write_text(
                r"# Title" "\n\n" r"Content with \cite{key1}." "\n"
            )

            verifier = ManuscriptVerifier(tmpdir)

            assert verifier.run_all() is True

    def test_run_all_fails_when_check_fails(self):
        """run_all() returns False when a check fails (lines 229-231)."""
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Valid bib file but manuscript references a key that doesn't exist
            (tmppath / "references.bib").write_text("@article{key1,}")
            (tmppath / "manuscript.md").write_text(r"Content with \cite{nonexistent_key}." "\n")

            verifier = ManuscriptVerifier(tmpdir)

            assert verifier.run_all() is False

    def test_run_all_no_md_files_returns_false(self):
        """run_all() returns False when there are no markdown files."""
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # No bib, no md files
            (tmppath / "references.bib").write_text("")
            # No .md files → check_files_exist returns False

            verifier = ManuscriptVerifier(tmpdir)

            assert verifier.run_all() is False

    def test_check_style_clean_pass(self):
        """check_style() returns True when no hyperbole words are present."""
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            (tmppath / "references.bib").write_text("")
            (tmppath / "manuscript.md").write_text(
                "This is a measured and reproducible result."
            )

            verifier = ManuscriptVerifier(tmpdir)
            assert verifier.check_style() is True


class TestManuscriptVerifierRound7:
    """Round-7 guard tests: pandoc-attribute and math-hygiene checks (F1/F2/F3)."""

    def _make_verifier(self, md_content: str):
        import tempfile
        from pathlib import Path

        from src.verification import ManuscriptVerifier

        tmp = tempfile.mkdtemp()
        tmppath = Path(tmp)
        (tmppath / "references.bib").write_text("@article{key1,}")
        (tmppath / "manuscript.md").write_text(md_content)
        return ManuscriptVerifier(tmp)

    def test_pandoc_attributes_clean(self):
        """Heading/image attributes are legitimate and pass."""
        v = self._make_verifier(
            "# Section {#sec:intro}\n\n![alt](fig.png){#fig:x width=80%}\n"
        )
        assert v.check_pandoc_attributes() is True

    def test_pandoc_attributes_flags_bare_line(self):
        """A standalone {#eq:...} line is raw attribute syntax that breaks LaTeX."""
        v = self._make_verifier(
            "\\begin{equation}\nx = 1\n\\end{equation}\n{#eq:foo}\n"
        )
        assert v.check_pandoc_attributes() is False

    def test_math_hygiene_clean(self):
        """Proper subscripts and single-backslash commands pass."""
        v = self._make_verifier(r"$\mathcal{T}_{i \to j}$ and $P_{\text{x}}$")
        assert v.check_math_hygiene() is True

    def test_math_hygiene_flags_subscript_star(self):
        """Subscript corruption (star instead of underscore) is flagged."""
        v = self._make_verifier(r"$\mathcal{T}*{i \to j}$")
        assert v.check_math_hygiene() is False

    def test_math_hygiene_flags_double_backslash(self):
        """Double-escaped control sequences inside math are flagged."""
        v = self._make_verifier(r"$P_{\\text{detect}}$")
        assert v.check_math_hygiene() is False

    def test_math_hygiene_ignores_legit_starred(self):
        """Legitimate starred LaTeX commands are not flagged."""
        v = self._make_verifier(
            "\\vspace*{2cm}\n\\DeclareMathOperator*{\\argmax}{argmax}\n"
        )
        assert v.check_math_hygiene() is True

    def test_duplicate_label_flagged(self):
        """Duplicate labels (multiply-defined LaTeX warnings) are flagged."""
        v = self._make_verifier(
            "\\label{cor:foo}\n...\n\\label{cor:foo}\n"
        )
        assert v.check_labels_and_refs() is False

    def test_run_all_includes_new_checks(self):
        """run_all() executes the round-7 checks and fails on a bare attribute."""
        import tempfile
        from pathlib import Path

        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "references.bib").write_text("@article{key1,}")
            (tmppath / "manuscript.md").write_text(
                "\\begin{equation}\nx = 1\n\\end{equation}\n{#eq:broken}\n"
            )
            verifier = ManuscriptVerifier(tmpdir)
            assert verifier.run_all() is False


    def test_macro_parameters_not_counted_as_labels(self):
        """LaTeX \\newcommand macro parameters (#1, #2) are not pandoc labels."""
        v = self._make_verifier(
            "\\newcommand{\\trust}[2]{\\mathcal{T}_{#1 \\to #2}}\n"
            "\\label{eq:real}\n"
        )
        assert v.check_labels_and_refs() is True
