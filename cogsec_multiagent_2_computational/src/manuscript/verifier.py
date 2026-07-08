"""
from __future__ import annotations

Manuscript Verification Module
==============================

Provides automated checks on manuscript files to ensure consistency,
correctness, and adherence to style guidelines.

Features:
- Validates LaTeX citations against references.bib
- Checks internal links and image references
- Verifies LaTeX labels and cross-references (\\cref, \\ref)
- Detects potential hyperbole and weasel words
- Checks for file existence
- Detailed logging
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Set

logger = logging.getLogger(__name__)


class ManuscriptVerifier:
    """Verifies manuscript integrity: citations, labels, images, style, tables."""

    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir).resolve()
        self.bib_file = self.root_dir / "references.bib"
        self.md_files = sorted(list(self.root_dir.glob("**/*.md")))

        # Regex patterns
        self.cite_pattern = re.compile(r"\\cite\{([^}]+)\}")
        self.bib_entry_pattern = re.compile(r"@\w+\{([^,]+),")
        self.label_pattern = re.compile(r"\\label\{([^}]+)\}")
        self.ref_pattern = re.compile(r"\\(cref|ref|autoref)\{([^}]+)\}")
        self.img_pattern = re.compile(r"!\[.*?\]\((.*?)\)")
        self.link_pattern = re.compile(r"\[.*?\]\((.*?)\)")

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

    def get_bib_keys(self) -> Set[str]:
        """Extract keys from references.bib."""
        keys: Set[str] = set()
        if not self.bib_file.exists():
            return keys

        with open(self.bib_file, "r", encoding="utf-8") as f:
            content = f.read()
            matches = self.bib_entry_pattern.findall(content)
            keys.update(matches)

        logger.info(f"Found {len(keys)} bibliography entries.")
        return keys

    def check_citations(self) -> bool:
        """Verify all citations map to a valid bib entry."""
        logger.info("Verifying citations...")
        status = True
        valid_keys = self.get_bib_keys()

        for md_file in self.md_files:
            if md_file.name == "references.bib":
                continue

            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
                citations = self.cite_pattern.findall(content)

                for citation in citations:
                    # Handle multiple citations like \cite{key1,key2}
                    keys = [k.strip() for k in citation.split(",")]
                    for key in keys:
                        if key not in valid_keys:
                            logger.warning(
                                f"Missing citation key: '{key}' in {md_file.name}"
                            )
                            status = False

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

    def check_images_and_links(self) -> bool:
        """Verify local image paths and links."""
        logger.info("Verifying images and links...")
        status = True

        # Output figures directory (figures are generated here)
        output_figures_dir = self.root_dir.parent / "output" / "figures"

        for md_file in self.md_files:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()

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
        """Check for stylistic issues like hyperbole."""
        logger.info("Checking style guidelines...")
        status = True

        for md_file in self.md_files:
            with open(md_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for i, line in enumerate(lines):
                    for word in self.hyperbole_words:
                        if re.search(
                            r"\b" + re.escape(word) + r"\b", line, re.IGNORECASE
                        ):
                            logger.warning(
                                f"Potential hyperbole '{word}' in {md_file.name}:{i+1}"
                            )

        return status

    def check_table_format(self) -> bool:
        """Check for common markdown table formatting errors."""
        logger.info("Checking table formatting...")
        status = True

        garbled_pattern = re.compile(r"\|\s*[lcr]+p\{")
        # A line that starts with non-| content followed by | --- pattern
        re.compile(r"^[^|]*\|[^|]+\|\s*\|?\s*---")

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
