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
        """Test check_style detects hyperbole words (P3-2)."""
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            (tmppath / "references.bib").write_text("")
            (tmppath / "manuscript.md").write_text(
                "This is a revolutionary approach that is clearly better."
            )

            verifier = ManuscriptVerifier(tmpdir)
            # Hyperbole present -> the check must report it (not a vacuous pass).
            assert verifier.check_style() is False

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "references.bib").write_text("")
            (tmppath / "manuscript.md").write_text(
                "This approach improves measured coverage by 12%."
            )
            verifier = ManuscriptVerifier(tmpdir)
            assert verifier.check_style() is True

    def test_check_domain_content_no_domain_files(self):
        """check_domain_content passes (True) when no 09c-09l domain files exist."""
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            (tmppath / "references.bib").write_text("")
            (tmppath / "manuscript.md").write_text("No domain sections here.")

            verifier = ManuscriptVerifier(tmpdir)
            result = verifier.check_domain_content()

            assert result is True

    def test_check_domain_content_missing_required_element(self):
        """check_domain_content fails when a domain file is missing a required element."""
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            (tmppath / "references.bib").write_text("")
            (tmppath / "09c_domain.md").write_text(
                "## Adversary Class\n\nSome content.\n"
            )  # missing Attack Pattern / OODA

            verifier = ManuscriptVerifier(tmpdir)
            result = verifier.check_domain_content()

            assert result is False

    def test_check_domain_content_all_elements_present(self):
        """check_domain_content passes when all required elements are present."""
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            (tmppath / "references.bib").write_text("")
            (tmppath / "09c_domain.md").write_text(
                "## Adversary Class\n\n## Attack Pattern\n\n## OODA\n"
            )

            verifier = ManuscriptVerifier(tmpdir)
            result = verifier.check_domain_content()

            assert result is True


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


class TestManuscriptVerifierRunAll:
    """Tests for run_all(): must return bool, never call sys.exit()."""

    def test_run_all_passes_when_all_checks_pass(self):
        """run_all() returns True when all verifications pass.

        run_all() is a plain library call -- it does not call sys.exit()
        itself; that's the CLI entry point's job (scripts/verify_manuscript.py).
        """
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            (tmppath / "references.bib").write_text("@article{key1,}")
            (tmppath / "manuscript.md").write_text(
                r"# Title" "\n\n" r"Content with \cite{key1}." "\n"
            )

            verifier = ManuscriptVerifier(tmpdir)

            assert verifier.run_all() is True

    def test_run_all_fails_on_broken_manuscript_without_raising(self):
        """run_all() returns False (not SystemExit) on a deliberately-broken manuscript."""
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Valid bib file but manuscript references a key that doesn't exist
            (tmppath / "references.bib").write_text("@article{key1,}")
            (tmppath / "manuscript.md").write_text(r"Content with \cite{nonexistent_key}." "\n")

            verifier = ManuscriptVerifier(tmpdir)

            result = verifier.run_all()
            assert result is False

    def test_run_all_no_md_files_returns_false(self):
        """run_all() returns False when there are no markdown files."""
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # No bib, no md files
            (tmppath / "references.bib").write_text("")
            # No .md files -> check_files_exist returns False

            verifier = ManuscriptVerifier(tmpdir)

            assert verifier.run_all() is False


class TestVerificationCoveragePaths:
    """Round-7 additions: cover previously-unexercised branches (real checks, no mocks)."""

    def test_configure_logging_writes_log_file(self):
        """_configure_verification_logging creates manuscript_verification.log in log_dir."""
        from src.verification import _configure_verification_logging

        with tempfile.TemporaryDirectory() as tmpdir:
            _configure_verification_logging(tmpdir)
            log_path = Path(tmpdir) / "manuscript_verification.log"
            assert log_path.exists()
            assert log_path.stat().st_size >= 0

    def test_escapes_root_detects_absolute_and_parent(self):
        """_escapes_root rejects absolute and parent-relative paths, accepts local."""
        from src.verification import ManuscriptVerifier

        assert ManuscriptVerifier._escapes_root("/etc/passwd") is True
        assert ManuscriptVerifier._escapes_root("../outside.png") is True
        assert ManuscriptVerifier._escapes_root("a/../../outside.png") is True
        assert ManuscriptVerifier._escapes_root("figures/posture.png") is False
        assert ManuscriptVerifier._escapes_root("sub/fig.png") is False

    def test_image_absolute_path_flagged(self):
        """check_images_and_links fails on an absolute image path."""
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "references.bib").write_text("")
            (tmppath / "manuscript.md").write_text("![x](/etc/passwd.png)")
            verifier = ManuscriptVerifier(tmpdir)
            assert verifier.check_images_and_links() is False

    def test_image_parent_escape_flagged(self):
        """check_images_and_links fails on a parent-relative image path."""
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "references.bib").write_text("")
            (tmppath / "manuscript.md").write_text("![x](../outside.png)")
            verifier = ManuscriptVerifier(tmpdir)
            assert verifier.check_images_and_links() is False

    def test_file_link_flagged(self):
        """check_images_and_links rejects non-portable file: links."""
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "references.bib").write_text("")
            (tmppath / "manuscript.md").write_text("[secret](file:///etc/passwd)")
            verifier = ManuscriptVerifier(tmpdir)
            assert verifier.check_images_and_links() is False

    def test_escaping_link_flagged(self):
        """check_images_and_links fails on a link that escapes the manuscript root."""
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "references.bib").write_text("")
            (tmppath / "manuscript.md").write_text("[outside](../secret.md)")
            verifier = ManuscriptVerifier(tmpdir)
            assert verifier.check_images_and_links() is False

    def test_broken_link_fails_check(self):
        """(Round-7) a broken local link target must fail, not merely warn."""
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "references.bib").write_text("")
            (tmppath / "manuscript.md").write_text("[missing](does_not_exist.md)")
            verifier = ManuscriptVerifier(tmpdir)
            assert verifier.check_images_and_links() is False

    def test_resolvable_link_passes(self):
        """A local link that resolves passes the link check."""
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "references.bib").write_text("")
            (tmppath / "target.md").write_text("# Target")
            (tmppath / "manuscript.md").write_text("[target](target.md)")
            verifier = ManuscriptVerifier(tmpdir)
            assert verifier.check_images_and_links() is True

    def test_citations_skip_references_bib_named_file(self):
        """check_citations skips a file literally named references.bib."""
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "references.bib").write_text("@article{real_key,}")
            # A file named exactly references.bib (no .md suffix) present in md_files
            # must be skipped rather than parsed for \\cite keys.
            verifier = ManuscriptVerifier(tmpdir)
            verifier.md_files = [tmppath / "references.bib"]
            (tmppath / "references.bib").write_text(r"\\cite{not_a_real_key}")
            assert verifier.check_citations() is True


    def test_configure_logging_idempotent(self):
        """_configure_verification_logging returns early when logging is already configured."""
        import logging

        from src.verification import _configure_verification_logging, logger

        handler = logging.NullHandler()
        logger.addHandler(handler)
        try:
            _configure_verification_logging(None)
        finally:
            logger.removeHandler(handler)


class TestManuscriptVerifierRound8:
    """Pandoc-attribute, math-hygiene, and duplicate-label checks (P1 sibling)."""

    def _make_verifier(self, md_content: str):
        from src.verification import ManuscriptVerifier

        tmp = tempfile.mkdtemp()
        tmppath = Path(tmp)
        (tmppath / "references.bib").write_text("@article{key1,}")
        (tmppath / "manuscript.md").write_text(md_content)
        return ManuscriptVerifier(tmp)

    def test_pandoc_attributes_clean(self) -> None:
        v = self._make_verifier(
            "# Section {#sec:intro}\n\n![alt](fig.png){#fig:x width=80%}\n"
        )
        assert v.check_pandoc_attributes() is True

    def test_pandoc_attributes_flags_bare_line(self) -> None:
        v = self._make_verifier(
            "\\begin{equation}\nx = 1\n\\end{equation}\n{#eq:foo}\n"
        )
        assert v.check_pandoc_attributes() is False

    def test_math_hygiene_clean(self) -> None:
        v = self._make_verifier(r"$\mathcal{T}_{i \to j}$ and $P_{\text{x}}$")
        assert v.check_math_hygiene() is True

    def test_math_hygiene_flags_subscript_star(self) -> None:
        v = self._make_verifier(r"$\mathcal{T}*{i \to j}$")
        assert v.check_math_hygiene() is False

    def test_math_hygiene_flags_double_backslash(self) -> None:
        v = self._make_verifier(r"$P_{\\text{detect}}$")
        assert v.check_math_hygiene() is False

    def test_math_hygiene_ignores_legit_starred(self) -> None:
        v = self._make_verifier(
            "\\vspace*{2cm}\n\\DeclareMathOperator*{\\argmax}{argmax}\n"
        )
        assert v.check_math_hygiene() is True

    def test_duplicate_label_flagged(self) -> None:
        v = self._make_verifier("\\label{cor:foo}\n...\n\\label{cor:foo}\n")
        assert v.check_labels_and_refs() is False

    def test_run_all_includes_new_checks(self) -> None:
        from src.verification import ManuscriptVerifier

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "references.bib").write_text("@article{key1,}")
            (tmppath / "manuscript.md").write_text(
                "\\begin{equation}\nx = 1\n\\end{equation}\n{#eq:broken}\n"
            )
            assert ManuscriptVerifier(tmpdir).run_all() is False

    def test_macro_parameters_not_counted_as_labels(self) -> None:
        v = self._make_verifier(
            "\\newcommand{\\trust}[2]{\\mathcal{T}_{#1 \\to #2}}\n"
            "\\label{eq:real}\n"
        )
        assert v.check_labels_and_refs() is True
