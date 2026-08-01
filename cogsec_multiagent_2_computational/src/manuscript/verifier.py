"""
Manuscript Verification Module
==============================

Provides automated checks on manuscript files to ensure consistency,
correctness, and adherence to style guidelines.

Features:
- Validates LaTeX citations against references.bib, in both directions
  (\\cite/\\citet/\\citep/\\citealp keys must resolve; duplicate bib keys are
  an error; never-cited entries are reported as a warning)
- Checks internal links and image references
- Verifies LaTeX labels and cross-references (\\cref, \\ref)
- Detects hyperbole outside quoted material
- Checks for file existence
- Detailed logging

Every ``check_*`` method returns ``False`` on a violation, and ``run_all``
fails when any of them does. Nothing here is advisory-only: a check that can
never return ``False`` is a gate that certifies whatever it is shown.
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Set

logger = logging.getLogger(__name__)

#: Spans whose contents are quoted material rather than authorial voice.
#: LaTeX ``...'' pairs, straight double quotes, and typographic quotes.
_QUOTED_SPAN = re.compile(r"``.*?''|\"[^\"]*\"|“[^”]*”")

#: A link target that is worth resolving on disk: no whitespace, no URL
#: scheme, no anchor-only reference. Anything else (an LTL formula that
#: happens to look like ``[](a => b)``, a mailto:, an http URL) is skipped.
_LOCAL_PATH = re.compile(r"^[\w./~-]+$")


def _mask_quotations(line: str) -> str:
    """Blank out quoted spans, preserving offsets.

    A term of art quoted from the literature ("almost perfect" agreement, per
    Landis & Koch) is not the author claiming perfection. Masking the quoted
    span - rather than allow-listing a word - keeps the exemption tied to a
    syntactic region instead of to a bypass keyword.
    """
    return _QUOTED_SPAN.sub(lambda m: " " * len(m.group(0)), line)


class ManuscriptVerifier:
    """Verifies manuscript integrity: citations, labels, images, style, tables."""

    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir).resolve()
        self.bib_file = self.root_dir / "references.bib"
        self.md_files = sorted(list(self.root_dir.glob("**/*.md")))

        # Regex patterns.
        # cite_pattern covers the natbib family (\citet, \citep, \citealp,
        # \citeauthor, ...) and starred forms, not just the bare \cite: a
        # \citet{nonexistent} used to be invisible to check_citations.
        self.cite_pattern = re.compile(r"\\cite[a-z]*\*?\{([^}]+)\}")
        self.bib_entry_pattern = re.compile(r"@\w+\{([^,]+),")
        self.label_pattern = re.compile(r"\\label\{([^}]+)\}")
        self.ref_pattern = re.compile(r"\\(cref|ref|autoref)\{([^}]+)\}")
        self.img_pattern = re.compile(r"!\[.*?\]\((.*?)\)")
        # Markdown links that are NOT images (negative lookbehind on '!').
        self.link_pattern = re.compile(r"(?<!!)\[.*?\]\((.*?)\)")

        # Style checks
        self.hyperbole_words = [
            "revolutionary",
            "groundbreaking",
            "unprecedented",
            "perfect",
            "flawless",
            "clearly",
            "obviously",
            "undoubtedly",
        ]

    def check_files_exist(self) -> bool:
        """Check if essential files exist."""
        logger.info("Checking file existence...")
        status = True
        if not self.bib_file.exists():
            logger.error(f"Missing bibliography file: {self.bib_file}")
            status = False

        if not self.md_files:
            logger.error(f"No markdown files found in {self.root_dir}")
            status = False

        return status

    def get_bib_entry_keys(self) -> List[str]:
        """Every bib key in file order, including repeats."""
        if not self.bib_file.exists():
            return []
        content = self.bib_file.read_text(encoding="utf-8")
        return [key.strip() for key in self.bib_entry_pattern.findall(content)]

    def get_bib_keys(self) -> Set[str]:
        """Extract the distinct keys defined in references.bib."""
        keys = set(self.get_bib_entry_keys())
        if keys:
            logger.info(f"Found {len(keys)} bibliography entries.")
        return keys

    def get_cited_keys(self) -> Set[str]:
        """Every key cited anywhere in the manuscript."""
        cited: Set[str] = set()
        for md_file in self.md_files:
            content = md_file.read_text(encoding="utf-8")
            for citation in self.cite_pattern.findall(content):
                cited.update(k.strip() for k in citation.split(",") if k.strip())
        return cited

    def check_citations(self) -> bool:
        """Verify citations and bibliography agree, in both directions.

        Failures:
          * a cited key with no bib entry;
          * the same bib key defined more than once.

        Warning only (citation padding is an editorial matter, not a build
        error): a bib entry that is never cited.
        """
        logger.info("Verifying citations...")
        status = True
        entry_keys = self.get_bib_entry_keys()
        valid_keys = set(entry_keys)

        duplicates = sorted(key for key, count in Counter(entry_keys).items() if count > 1)
        for key in duplicates:
            logger.warning(f"Duplicate bibliography key: '{key}' in {self.bib_file.name}")
            status = False

        for md_file in self.md_files:
            content = md_file.read_text(encoding="utf-8")
            for citation in self.cite_pattern.findall(content):
                # Handle multiple citations like \cite{key1,key2}
                for key in (k.strip() for k in citation.split(",")):
                    if key and key not in valid_keys:
                        logger.warning(f"Missing citation key: '{key}' in {md_file.name}")
                        status = False

        unused = sorted(valid_keys - self.get_cited_keys())
        if unused:
            logger.warning(
                f"{len(unused)} of {len(valid_keys)} bibliography entries are never cited: "
                f"{', '.join(unused)}"
            )

        return status

    def check_labels_and_refs(self) -> bool:
        """Check \\label definitions and \\ref usage."""
        logger.info("Verifying definition labels and references...")
        status = True
        defined_labels = set()

        # pass 1: collect labels
        for md_file in self.md_files:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
                # LaTeX labels
                labels = self.label_pattern.findall(content)
                defined_labels.update(labels)

                # Pandoc labels {#label} or {#label attr=...}
                # Match #identifier at start of braces, stopping at space or }
                pandoc_labels = re.findall(r"\{#([a-zA-Z0-9_:-]+)", content)
                defined_labels.update(pandoc_labels)

        # pass 2: check refs
        for md_file in self.md_files:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
                refs = self.ref_pattern.findall(content)
                for ref_type, ref_key in refs:
                    # Handle multiple refs like \cref{fig:1,fig:2}
                    keys = [k.strip() for k in ref_key.split(",")]
                    for key in keys:
                        if key not in defined_labels:
                            logger.warning(
                                f"Undefined reference: '\\{ref_type}{{{key}}}' in {md_file.name}"
                            )
                            status = False

        return status

    def _check_local_links(self, md_file: Path, content: str) -> bool:
        """Resolve non-image markdown links that point at local paths."""
        status = True
        for target in self.link_pattern.findall(content):
            candidate = target.split("#", 1)[0].strip()
            if not candidate or not _LOCAL_PATH.match(candidate):
                # URLs, mailto:, anchors, and pseudo-links such as the LTL
                # formulas written as [](a => b) are not filesystem paths.
                continue
            if (md_file.parent / candidate).exists() or (self.root_dir / candidate).exists():
                continue
            logger.warning(f"Broken local link: '{candidate}' in {md_file.name}")
            status = False
        return status

    def check_images_and_links(self) -> bool:
        """Verify local image paths and links."""
        logger.info("Verifying images and links...")
        status = True

        # Output figures directory (figures are generated here)
        output_figures_dir = self.root_dir.parent / "output" / "figures"

        for md_file in self.md_files:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()

                if not self._check_local_links(md_file, content):
                    status = False

                # Check images
                for img_path in self.img_pattern.findall(content):
                    # Ignore web links
                    if img_path.startswith("http") or img_path.startswith("www"):
                        continue

                    # Remove potential brackets or styling
                    clean_path = img_path.split(" ")[0].split("{")[0]
                    target = self.root_dir / clean_path

                    if not target.exists():
                        # Try relative to file
                        target_rel = md_file.parent / clean_path
                        if not target_rel.exists():
                            # Try figures dir relative to manuscript root
                            target_figs = (
                                self.root_dir / "figures" / Path(clean_path).name
                            )
                            if not target_figs.exists():
                                # Try output/figures directory (generated figures)
                                target_output = output_figures_dir / Path(clean_path).name
                                if not target_output.exists():
                                    logger.warning(
                                        f"Missing image: '{clean_path}' in {md_file.name}"
                                    )
                                    status = False

        return status

    def check_style(self) -> bool:
        """Fail on hyperbole written in the author's own voice.

        Quoted spans are masked first (see :func:`_mask_quotations`), so a
        quoted term of art does not trip the gate while the same word used
        unquoted - on the same line - still does.
        """
        logger.info("Checking style guidelines...")
        status = True

        for md_file in self.md_files:
            with open(md_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for i, line in enumerate(lines):
                    unquoted = _mask_quotations(line)
                    for word in self.hyperbole_words:
                        if re.search(r"\b" + re.escape(word) + r"\b", unquoted, re.IGNORECASE):
                            logger.warning(f"Hyperbole '{word}' in {md_file.name}:{i+1}")
                            status = False

        return status

    def check_table_format(self) -> bool:
        """Check for common markdown table formatting errors."""
        logger.info("Checking table formatting...")
        status = True

        garbled_pattern = re.compile(r"\|\s*[lcr]+p\{")

        for md_file in self.md_files:
            with open(md_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                in_table = False
                for i, line in enumerate(lines):
                    stripped = line.strip()

                    # Check for garbled LaTeX table syntax
                    if garbled_pattern.search(stripped):
                        logger.warning(
                            f"Garbled LaTeX table syntax in {md_file.name}:{i+1}: {stripped[:60]}"
                        )
                        status = False

                    # Track table context
                    if stripped.startswith("|"):
                        in_table = True
                    elif in_table and stripped == "":
                        in_table = False

                    # Check for table rows missing leading |
                    if (
                        in_table
                        and not stripped.startswith("|")
                        and "|" in stripped
                        and stripped
                        and not stripped.startswith("*")
                        and not stripped.startswith("#")
                        and not stripped.startswith("-")
                    ):
                        # Looks like a table row without leading |
                        if re.match(r"^\S.*\|", stripped):
                            logger.warning(
                                f"Table row missing leading '|' in {md_file.name}:{i+1}: {stripped[:60]}"  # noqa: E501
                            )
                            status = False

        return status

    def check_duplicate_labels(self) -> bool:
        """Warn when the same label appears in multiple files."""
        logger.info("Checking for duplicate labels...")
        status = True
        label_locations: Dict[str, List[str]] = {}

        for md_file in self.md_files:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
                # LaTeX labels
                for label in self.label_pattern.findall(content):
                    label_locations.setdefault(label, []).append(md_file.name)
                # Pandoc labels (skip pure numbers — those are LaTeX \newcommand params)
                for label in re.findall(r"\{#([a-zA-Z0-9_:-]+)", content):
                    if not label.isdigit():
                        label_locations.setdefault(label, []).append(md_file.name)

        for label, files in label_locations.items():
            if len(files) > 1:
                logger.warning(
                    f"Duplicate label '{label}' in: {', '.join(files)}"
                )
                status = False

        return status

    def check_figure_accessibility(self) -> bool:
        """Verify figure references have meaningful alt text and captions."""
        logger.info("Checking figure accessibility...")
        status = True
        MIN_CAPTION_LENGTH = 20

        # Pattern matches ![alt](path) where alt might be empty
        fig_pattern = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")

        for md_file in self.md_files:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
                for match in fig_pattern.finditer(content):
                    alt_text = match.group(1).strip()
                    img_path = match.group(2).strip()

                    if not alt_text:
                        logger.warning(
                            f"Empty alt text for image '{img_path}' in {md_file.name}"
                        )
                        status = False
                    elif len(alt_text) < MIN_CAPTION_LENGTH:
                        logger.warning(
                            f"Short alt text ({len(alt_text)} chars) for image in {md_file.name}: '{alt_text[:40]}...'"  # noqa: E501
                        )
                        status = False

        return status

    def run_all(self) -> bool:
        """Run all verifications. Returns True if all pass, False otherwise."""
        logger.info(f"Starting verification on {self.root_dir}...")

        results = {
            "Files": self.check_files_exist(),
            "Citations": self.check_citations(),
            "Labels/Refs": self.check_labels_and_refs(),
            "Images/Links": self.check_images_and_links(),
            "Style": self.check_style(),
            "Table Format": self.check_table_format(),
            "Duplicate Labels": self.check_duplicate_labels(),
            "Fig Accessibility": self.check_figure_accessibility(),
        }

        logger.info("-" * 40)
        logger.info("Verification Summary:")
        failed = False
        for check, result in results.items():
            status_str = "PASS" if result else "FAIL"
            if not result:
                failed = True
            logger.info(f"{check:<15}: {status_str}")
        logger.info("-" * 40)

        if failed:
            logger.error("Verification failed. See logs for details.")
        else:
            logger.info("All checks passed successfully.")

        return not failed
