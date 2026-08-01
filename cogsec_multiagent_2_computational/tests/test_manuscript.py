"""Tests for the manuscript package: verifier and latex_converter.

Every ``check_*`` method is exercised in both directions. A gate that is only
ever shown a clean input is not tested: an edit flipping ``status = False`` to
``status = True`` would leave the suite green while the gate silently became
fail-open. The ``TestVerifierNegativeControls`` class below is the positive
control for that -- each test constructs the violating manuscript and asserts
the check rejects it.
"""

import re
import textwrap
from pathlib import Path

from manuscript.latex_converter import (
    convert_file,
    convert_latex_table_to_markdown,
)
from manuscript.verifier import ManuscriptVerifier

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ── ManuscriptVerifier ──────────────────────────────────────────────────


class TestManuscriptVerifierInit:
    """Initialisation and file-existence checks."""

    def test_init_sets_root(self, tmp_path):
        v = ManuscriptVerifier(str(tmp_path))
        assert v.root_dir == tmp_path.resolve()

    def test_check_files_exist_no_bib(self, tmp_path):
        (tmp_path / "doc.md").write_text("hello")
        v = ManuscriptVerifier(str(tmp_path))
        assert v.check_files_exist() is False

    def test_check_files_exist_no_md(self, tmp_path):
        (tmp_path / "references.bib").write_text("@article{k, title={T}}")
        v = ManuscriptVerifier(str(tmp_path))
        assert v.check_files_exist() is False

    def test_check_files_exist_ok(self, tmp_path):
        (tmp_path / "references.bib").write_text("@article{k, title={T}}")
        (tmp_path / "doc.md").write_text("hello")
        v = ManuscriptVerifier(str(tmp_path))
        assert v.check_files_exist() is True


class TestBibKeys:
    """get_bib_keys parsing."""

    def test_extracts_keys(self, tmp_path):
        bib = textwrap.dedent("""\
            @article{smith2024,
              author = {Smith},
            }
            @inproceedings{jones2023,
              title = {Jones},
            }
        """)
        (tmp_path / "references.bib").write_text(bib)
        v = ManuscriptVerifier(str(tmp_path))
        keys = v.get_bib_keys()
        assert keys == {"smith2024", "jones2023"}

    def test_no_bib_returns_empty(self, tmp_path):
        v = ManuscriptVerifier(str(tmp_path))
        keys = v.get_bib_keys()
        assert keys == set()


class TestCitations:
    """check_citations validation, in both directions."""

    def test_valid_citations_pass(self, tmp_path):
        (tmp_path / "references.bib").write_text("@article{k1, title={T}}\n@book{k2, author={A}}")
        (tmp_path / "doc.md").write_text(r"See \cite{k1} and \cite{k1,k2}.")
        v = ManuscriptVerifier(str(tmp_path))
        assert v.check_citations() is True

    def test_missing_citation_fails(self, tmp_path):
        (tmp_path / "references.bib").write_text("@article{k1, title={T}}")
        (tmp_path / "doc.md").write_text(r"See \cite{missing_key}.")
        v = ManuscriptVerifier(str(tmp_path))
        assert v.check_citations() is False

    def test_natbib_forms_are_scanned(self, tmp_path):
        r"""\citet/\citep/\citealp used to be invisible to the checker."""
        (tmp_path / "references.bib").write_text("@article{k1, title={T}}")
        for macro in (r"\citet", r"\citep", r"\citealp", r"\citeauthor", r"\citep*"):
            (tmp_path / "doc.md").write_text(f"See {macro}{{nonexistent2027}}.")
            v = ManuscriptVerifier(str(tmp_path))
            assert v.check_citations() is False, macro

    def test_natbib_forms_resolve_when_present(self, tmp_path):
        (tmp_path / "references.bib").write_text("@article{k1, title={T}}")
        (tmp_path / "doc.md").write_text(r"See \citet{k1} and \citep{k1}.")
        v = ManuscriptVerifier(str(tmp_path))
        assert v.check_citations() is True

    def test_duplicate_bib_key_fails(self, tmp_path):
        (tmp_path / "references.bib").write_text(
            "@article{dup, title={A}}\n@inproceedings{dup, title={B}}\n"
        )
        (tmp_path / "doc.md").write_text(r"See \cite{dup}.")
        v = ManuscriptVerifier(str(tmp_path))
        assert v.check_citations() is False

    def test_unused_entry_warns_but_passes(self, tmp_path, caplog):
        """Citation padding is editorial, so it warns rather than failing."""
        (tmp_path / "references.bib").write_text(
            "@article{used, title={A}}\n@article{never_cited, title={B}}\n"
        )
        (tmp_path / "doc.md").write_text(r"See \cite{used}.")
        v = ManuscriptVerifier(str(tmp_path))
        with caplog.at_level("WARNING"):
            assert v.check_citations() is True
        assert "never_cited" in caplog.text

    def test_cited_keys_are_collected_across_files(self, tmp_path):
        (tmp_path / "references.bib").write_text("@article{a, t={}}\n@article{b, t={}}")
        (tmp_path / "one.md").write_text(r"\cite{a}")
        (tmp_path / "two.md").write_text(r"\citep{b}")
        v = ManuscriptVerifier(str(tmp_path))
        assert v.get_cited_keys() == {"a", "b"}

    def test_bib_entry_keys_include_repeats(self, tmp_path):
        (tmp_path / "references.bib").write_text("@article{x, t={}}\n@book{x, t={}}")
        v = ManuscriptVerifier(str(tmp_path))
        assert v.get_bib_entry_keys() == ["x", "x"]
        assert v.get_bib_keys() == {"x"}

    def test_bib_entry_keys_empty_without_bib(self, tmp_path):
        assert ManuscriptVerifier(str(tmp_path)).get_bib_entry_keys() == []


class TestLabelsAndRefs:
    """check_labels_and_refs validation."""

    def test_valid_refs_pass(self, tmp_path):
        (tmp_path / "references.bib").write_text("")
        md = textwrap.dedent(r"""
            \label{fig:cool}
            See \ref{fig:cool}.
        """)
        (tmp_path / "doc.md").write_text(md)
        v = ManuscriptVerifier(str(tmp_path))
        assert v.check_labels_and_refs() is True

    def test_undefined_ref_fails(self, tmp_path):
        (tmp_path / "references.bib").write_text("")
        (tmp_path / "doc.md").write_text(r"See \ref{fig:nowhere}.")
        v = ManuscriptVerifier(str(tmp_path))
        assert v.check_labels_and_refs() is False

    def test_pandoc_labels(self, tmp_path):
        (tmp_path / "references.bib").write_text("")
        md = "# Heading {#sec:intro}\n\nSee \\ref{sec:intro}."
        (tmp_path / "doc.md").write_text(md)
        v = ManuscriptVerifier(str(tmp_path))
        assert v.check_labels_and_refs() is True


class TestImagesAndLinks:
    """check_images_and_links validation."""

    def test_valid_image(self, tmp_path):
        (tmp_path / "references.bib").write_text("")
        img_dir = tmp_path / "img"
        img_dir.mkdir()
        (img_dir / "fig.png").write_text("PNG")
        (tmp_path / "doc.md").write_text("![fig](img/fig.png)")
        v = ManuscriptVerifier(str(tmp_path))
        assert v.check_images_and_links() is True

    def test_missing_image_fails(self, tmp_path):
        (tmp_path / "references.bib").write_text("")
        (tmp_path / "doc.md").write_text("![fig](img/missing.png)")
        v = ManuscriptVerifier(str(tmp_path))
        assert v.check_images_and_links() is False

    def test_remote_image_url_is_not_resolved_on_disk(self, tmp_path):
        (tmp_path / "references.bib").write_text("")
        (tmp_path / "doc.md").write_text(
            "![a remote figure with a caption](https://example.com/f.png)\n"
            "![another remote figure here](www.example.com/g.png)\n"
        )
        v = ManuscriptVerifier(str(tmp_path))
        assert v.check_images_and_links() is True

    def test_broken_local_link_fails(self, tmp_path):
        (tmp_path / "references.bib").write_text("")
        (tmp_path / "doc.md").write_text("See [the module](../src/does_not_exist.py).")
        v = ManuscriptVerifier(str(tmp_path))
        assert v.check_images_and_links() is False

    def test_resolvable_local_link_passes(self, tmp_path):
        (tmp_path / "references.bib").write_text("")
        (tmp_path / "target.md").write_text("hi")
        (tmp_path / "doc.md").write_text("See [target](target.md).")
        v = ManuscriptVerifier(str(tmp_path))
        assert v.check_images_and_links() is True

    def test_link_anchor_is_stripped_before_resolving(self, tmp_path):
        (tmp_path / "references.bib").write_text("")
        (tmp_path / "target.md").write_text("hi")
        (tmp_path / "doc.md").write_text("See [target](target.md#section).")
        v = ManuscriptVerifier(str(tmp_path))
        assert v.check_images_and_links() is True

    def test_non_path_link_targets_are_skipped(self, tmp_path):
        """URLs, anchors and pseudo-links (LTL formulas) are not filesystem paths."""
        (tmp_path / "references.bib").write_text("")
        (tmp_path / "doc.md").write_text(
            "[web](https://example.com)\n"
            "[mail](mailto:a@b.c)\n"
            "[anchor](#sec:intro)\n"
            "[](attacked_F - baseline_F <= Kappa => ~is_detected)\n"
        )
        v = ManuscriptVerifier(str(tmp_path))
        assert v.check_images_and_links() is True

    def test_image_syntax_is_not_double_reported_as_a_link(self, tmp_path):
        """`![alt](p.png)` must be handled by the image branch only."""
        (tmp_path / "references.bib").write_text("")
        figs = tmp_path / "figures"
        figs.mkdir()
        (figs / "p.png").write_text("PNG")
        (tmp_path / "doc.md").write_text("![a real caption here](figures/p.png)")
        v = ManuscriptVerifier(str(tmp_path))
        assert v.check_images_and_links() is True


class TestStyleChecks:
    """check_style is a real gate, not an advisory logger."""

    def test_no_hyperbole_passes(self, tmp_path):
        (tmp_path / "references.bib").write_text("")
        (tmp_path / "doc.md").write_text("This method achieves high accuracy.")
        v = ManuscriptVerifier(str(tmp_path))
        assert v.check_style() is True

    def test_hyperbole_fails(self, tmp_path):
        """POSITIVE CONTROL: check_style used to return True unconditionally."""
        (tmp_path / "references.bib").write_text("")
        (tmp_path / "doc.md").write_text("This revolutionary approach is groundbreaking.")
        v = ManuscriptVerifier(str(tmp_path))
        assert v.check_style() is False

    def test_every_listed_hyperbole_word_trips_the_gate(self, tmp_path):
        (tmp_path / "references.bib").write_text("")
        v = ManuscriptVerifier(str(tmp_path))
        for word in v.hyperbole_words:
            (tmp_path / "doc.md").write_text(f"The result is {word} in every respect.")
            assert ManuscriptVerifier(str(tmp_path)).check_style() is False, word

    def test_quoted_term_of_art_does_not_trip_the_gate(self, tmp_path):
        """``almost perfect'' agreement (Landis & Koch) is a quotation, not a claim."""
        (tmp_path / "references.bib").write_text("")
        (tmp_path / "doc.md").write_text(
            "Cohen's kappa = 0.84, indicating ``almost perfect'' agreement.\n"
            'The reviewer called it "a perfect example" of the genre.\n'
        )
        v = ManuscriptVerifier(str(tmp_path))
        assert v.check_style() is True

    def test_quoting_does_not_exempt_the_rest_of_the_line(self, tmp_path):
        """The exemption is a syntactic region, not a bypass keyword."""
        (tmp_path / "references.bib").write_text("")
        (tmp_path / "doc.md").write_text(
            "``almost perfect'' agreement confirms our groundbreaking result.\n"
        )
        v = ManuscriptVerifier(str(tmp_path))
        assert v.check_style() is False


class TestTableFormatting:
    """check_table_format validation."""

    def test_valid_table_passes(self, tmp_path):
        (tmp_path / "references.bib").write_text("")
        table = textwrap.dedent("""\
            | Col A | Col B |
            |-------|-------|
            | 1     | 2     |
        """)
        (tmp_path / "doc.md").write_text(table)
        v = ManuscriptVerifier(str(tmp_path))
        assert v.check_table_format() is True

    def test_column_count_mismatch_is_not_detected(self, tmp_path):
        """Documents a real limitation: the checker counts pipes, not columns."""
        (tmp_path / "references.bib").write_text("")
        table = textwrap.dedent("""\
            | Col A | Col B | Col C |
            |-------|-------|
            | 1     | 2     |
        """)
        (tmp_path / "doc.md").write_text(table)
        v = ManuscriptVerifier(str(tmp_path))
        assert v.check_table_format() is True

    def test_garbled_latex_column_spec_fails(self, tmp_path):
        (tmp_path / "references.bib").write_text("")
        (tmp_path / "doc.md").write_text(r"| lcp{3cm} | x |")
        v = ManuscriptVerifier(str(tmp_path))
        assert v.check_table_format() is False

    def test_table_row_missing_leading_pipe_fails(self, tmp_path):
        (tmp_path / "references.bib").write_text("")
        table = textwrap.dedent("""\
            | A | B |
            |---|---|
            x | 2 |
        """)
        (tmp_path / "doc.md").write_text(table)
        v = ManuscriptVerifier(str(tmp_path))
        assert v.check_table_format() is False


class TestDuplicateLabels:
    """check_duplicate_labels validation."""

    def test_distinct_labels_pass(self, tmp_path):
        (tmp_path / "references.bib").write_text("")
        (tmp_path / "a.md").write_text("# A {#sec:a}")
        (tmp_path / "b.md").write_text("# B {#sec:b}")
        v = ManuscriptVerifier(str(tmp_path))
        assert v.check_duplicate_labels() is True

    def test_duplicate_label_across_files_fails(self, tmp_path):
        (tmp_path / "references.bib").write_text("")
        (tmp_path / "a.md").write_text("# A {#sec:same}")
        (tmp_path / "b.md").write_text("# B {#sec:same}")
        v = ManuscriptVerifier(str(tmp_path))
        assert v.check_duplicate_labels() is False

    def test_numeric_pandoc_braces_are_ignored(self, tmp_path):
        r"""`{#1}` in a \newcommand body is a parameter, not a label."""
        (tmp_path / "references.bib").write_text("")
        (tmp_path / "a.md").write_text(r"\newcommand{\f}[1]{#1}")
        (tmp_path / "b.md").write_text(r"\newcommand{\g}[1]{#1}")
        v = ManuscriptVerifier(str(tmp_path))
        assert v.check_duplicate_labels() is True


class TestFigureAccessibility:
    """check_figure_accessibility validation."""

    def test_descriptive_alt_text_passes(self, tmp_path):
        (tmp_path / "references.bib").write_text("")
        (tmp_path / "doc.md").write_text("![A descriptive caption of the figure](f.png)")
        v = ManuscriptVerifier(str(tmp_path))
        assert v.check_figure_accessibility() is True

    def test_empty_alt_text_fails(self, tmp_path):
        (tmp_path / "references.bib").write_text("")
        (tmp_path / "doc.md").write_text("![](f.png)")
        v = ManuscriptVerifier(str(tmp_path))
        assert v.check_figure_accessibility() is False

    def test_short_alt_text_fails(self, tmp_path):
        (tmp_path / "references.bib").write_text("")
        (tmp_path / "doc.md").write_text("![fig 1](f.png)")
        v = ManuscriptVerifier(str(tmp_path))
        assert v.check_figure_accessibility() is False


class TestRunAll:
    """run_all aggregation."""

    def test_run_all_clean_manuscript(self, tmp_path):
        (tmp_path / "references.bib").write_text("@article{k1, title={T}}")
        (tmp_path / "doc.md").write_text(r"See \cite{k1}.")
        v = ManuscriptVerifier(str(tmp_path))
        assert v.run_all() is True

    def test_run_all_fails_when_a_single_check_fails(self, tmp_path):
        """POSITIVE CONTROL: run_all had no test that ever drove it to False."""
        (tmp_path / "references.bib").write_text("@article{k1, title={T}}")
        (tmp_path / "doc.md").write_text(r"See \cite{nope}.")
        v = ManuscriptVerifier(str(tmp_path))
        assert v.run_all() is False

    def test_run_all_reports_failure(self, tmp_path, caplog):
        (tmp_path / "references.bib").write_text("@article{k1, title={T}}")
        (tmp_path / "doc.md").write_text(r"See \cite{nope}.")
        v = ManuscriptVerifier(str(tmp_path))
        with caplog.at_level("INFO"):
            assert v.run_all() is False
        assert re.search(r"Citations\s+: FAIL", caplog.text)
        assert "Verification failed" in caplog.text

    def test_run_all_reports_success(self, tmp_path, caplog):
        (tmp_path / "references.bib").write_text("@article{k1, title={T}}")
        (tmp_path / "doc.md").write_text(r"See \cite{k1}.")
        v = ManuscriptVerifier(str(tmp_path))
        with caplog.at_level("INFO"):
            assert v.run_all() is True
        assert "All checks passed successfully." in caplog.text


class TestVerifierNegativeControls:
    """One manuscript that trips every check at once.

    If any ``status = False`` assignment in verifier.py were flipped to
    ``True``, at least one assertion here would fail. That is the property
    the gate was missing: it had no test that ever made it say no.
    """

    @staticmethod
    def _broken(tmp_path):
        (tmp_path / "references.bib").write_text(
            "@article{dup, title={A}}\n@inproceedings{dup, title={B}}\n"
        )
        (tmp_path / "a.md").write_text(
            "\n".join(
                [
                    r"See \citet{nonexistent2027}.",
                    r"See \cref{fig:nowhere}.",
                    "![](missing.png)",
                    "See [gone](does_not_exist.md).",
                    "This is a revolutionary and flawless result.",
                    r"| lcp{2cm} | x |",
                    "# Heading {#sec:clash}",
                ]
            )
        )
        (tmp_path / "b.md").write_text("# Other heading {#sec:clash}")
        return ManuscriptVerifier(str(tmp_path))

    def test_every_check_rejects_the_broken_manuscript(self, tmp_path):
        v = self._broken(tmp_path)
        assert v.check_citations() is False
        assert v.check_labels_and_refs() is False
        assert v.check_images_and_links() is False
        assert v.check_style() is False
        assert v.check_table_format() is False
        assert v.check_duplicate_labels() is False
        assert v.check_figure_accessibility() is False

    def test_run_all_rejects_the_broken_manuscript(self, tmp_path):
        assert self._broken(tmp_path).run_all() is False

    def test_files_check_is_the_only_one_that_can_still_pass(self, tmp_path):
        v = self._broken(tmp_path)
        assert v.check_files_exist() is True


class TestShippedManuscript:
    """The real manuscript must still satisfy the hardened gate."""

    def test_run_all_passes_on_the_shipped_manuscript(self):
        v = ManuscriptVerifier(str(PROJECT_ROOT / "manuscript"))
        assert v.run_all() is True


# ── LaTeX Converter ──────────────────────────────────────────────────────


class TestConvertLatexToMarkdown:
    """Tests for convert_latex_table_to_markdown."""

    _TABLE_PATTERN = re.compile(
        r'\\begin\{table\}(?:\[[^\]]*\])?\s*'
        r'(?:\\centering\s*)?'
        r'.*?'
        r'\\end\{table\}',
        re.DOTALL,
    )

    def test_basic_table(self):
        latex = textwrap.dedent(r"""
            \begin{table}[h]
            \caption{Test Table}
            \label{tab:test}
            \begin{tabular}{lcc}
            \hline
            Name & Score & Grade \\
            Alice & 95 & A \\
            Bob & 82 & B \\
            \hline
            \end{tabular}
            \end{table}
        """).strip()
        match = self._TABLE_PATTERN.search(latex)
        assert match is not None, "Regex should find the table block"
        result = convert_latex_table_to_markdown(match)
        assert isinstance(result, str)
        assert "|" in result  # Should contain pipe-separated columns

    def test_no_table_returns_unchanged(self):
        """When there is no table environment, sub() never calls the converter."""
        text = "No table here."
        output = self._TABLE_PATTERN.sub(convert_latex_table_to_markdown, text)
        assert output == text  # nothing to convert


class TestConvertFile:
    """Tests for convert_file."""

    def test_converts_file_with_table(self, tmp_path):
        content = textwrap.dedent(r"""
            # My Doc

            Some text.

            \begin{table}[h]
            \caption{Results}
            \begin{tabular}{lc}
            Method & Acc \\
            Ours & 0.95 \\
            \end{tabular}
            \end{table}

            More text.
        """)
        md_file = tmp_path / "test.md"
        md_file.write_text(content)
        assert convert_file(md_file) is True
        converted = md_file.read_text()
        assert r"\begin{tabular}" not in converted
        assert "| Method | Acc |" in converted

    def test_no_conversion_needed(self, tmp_path):
        md_file = tmp_path / "plain.md"
        original = "# Just text\n\nHello world.\n"
        md_file.write_text(original)
        assert convert_file(md_file) is False
        assert md_file.read_text() == original
