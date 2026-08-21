#!/usr/bin/env python3
"""Manuscript Verification Module

Part of the Cognitive Integrity Framework.

This module provides automated checks on manuscript files to ensure
consistency, correctness, and adherence to style guidelines.

Features:
- Validates LaTeX citations against references.bib
- Checks internal links and image references
- Verifies LaTeX labels and cross-references (\\cref, \\ref)
- Detects potential hyperbole and weasel words
- Checks for file existence
- Verifies domain-application sections have required structural elements
- Detailed logging
"""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path
from typing import Set

logger = logging.getLogger(__name__)


def _configure_verification_logging(log_dir: str | None = None) -> None:
    """Configure logging once when running verification as a CLI entrypoint.

    Args:
        log_dir: Directory to write ``manuscript_verification.log`` into. When
            omitted the log lands in the current working directory; callers
            should pass the project root so the artifact is reproducible
            regardless of where the command is invoked.
    """
    if logger.handlers:
        return
    log_path = (
        str(Path(log_dir) / "manuscript_verification.log")
        if log_dir
        else "manuscript_verification.log"
    )
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_path),
        ],
    )


class ManuscriptVerifier:
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

        # Math-hygiene checks (ported from Part 1 round-7):
        self.subscript_star_pattern = re.compile(r"[A-Za-z}]\*[{A-Za-z]")
        self.double_backslash_cmd_pattern = re.compile(r"\\\\[a-zA-Z]")

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

    def check_pandoc_attributes(self) -> bool:
        """Check for bare ``{#label}`` attribute lines that pandoc passes
        through as literal text (breaking the LaTeX build).
        """
        logger.info("Verifying pandoc attributes...")
        status = True
        bare_attr = re.compile(r"^\s*\{#[^}]+\}\s*$", re.MULTILINE)

        for md_file in self.md_files:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
            for m in bare_attr.finditer(content):
                line = content.count("\n", 0, m.start()) + 1
                logger.warning(
                    f"Bare pandoc attribute line {m.group(0).strip()} in "
                    f"{md_file.name}:{line} will pass through to LaTeX as "
                    f"literal text and break the PDF build; attach it to the "
                    f"enclosing environment (e.g. \\label inside the equation)"
                )
                status = False
        return status

    def check_math_hygiene(self) -> bool:
        """Check for LaTeX math-notational corruption that renders wrong but
        does not fail the label/citation checks.
        """
        logger.info("Verifying math hygiene...")
        status = True
        legit_starred = ("vspace*{", "DeclareMathOperator*{")

        for md_file in self.md_files:
            with open(md_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for i, line in enumerate(lines):
                for m in self.subscript_star_pattern.finditer(line):
                    ctx = line[max(0, m.start() - 20) : m.end()]
                    if any(token in ctx for token in legit_starred):
                        continue
                    logger.warning(
                        f"Subscript-star corruption '{m.group(0)}' in "
                        f"{md_file.name}:{i + 1}: replace '*' with '_' "
                        f"(literal stars render as binary operators in math)"
                    )
                    status = False

                for m in self.double_backslash_cmd_pattern.finditer(line):
                    logger.warning(
                        f"Double-escaped control sequence '{m.group(0)}' in "
                        f"{md_file.name}:{i + 1}: use a single backslash "
                        f"inside math"
                    )
                    status = False
        return status

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
        keys: set[str] = set()
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
                            logger.warning(f"Missing citation key: '{key}' in {md_file.name}")
                            status = False

        return status

    def check_labels_and_refs(self) -> bool:
        """Check \\label definitions and \\ref usage."""
        logger.info("Verifying definition labels and references...")
        status = True
        defined_labels: dict[str, int] = {}
        # pass 1: collect labels
        for md_file in self.md_files:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
                # LaTeX labels
                labels = self.label_pattern.findall(content)
                for label in labels:
                    defined_labels[label] = defined_labels.get(label, 0) + 1

                # Pandoc identifiers start with a letter; "#1"-style LaTeX
                # macro parameters must not be counted as labels.
                pandoc_labels = re.findall(r"\{#([A-Za-z][^}]*)\}", content)
                for label in pandoc_labels:
                    defined_labels[label] = defined_labels.get(label, 0) + 1

        for label, count in sorted(defined_labels.items()):
            if count > 1:
                logger.warning(
                    f"Duplicate label '{label}' defined {count} times; "
                    f"\\cref resolves to the last definition - rename one "
                    f"occurrence"
                )
                status = False

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

    @staticmethod
    def _escapes_root(clean_path: str) -> bool:
        """True if the path is absolute or escapes the manuscript root (P3-M3)."""
        p = Path(clean_path)
        if p.is_absolute():
            return True
        return ".." in p.parts

    def check_images_and_links(self) -> bool:
        """Verify local image paths and markdown links.

        Fixes (P3-M3): (1) reject absolute or ``..``-escaping image refs
        instead of letting ``root / ref`` read outside the manuscript dir;
        (2) actually validate markdown links (previously unexercised).
        """
        logger.info("Verifying images and links...")
        status = True
        link_status = True

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
                    if self._escapes_root(clean_path):
                        logger.warning(
                            f"Image path escapes manuscript root (absolute or "
                            f"'..'): '{clean_path}' in {md_file.name}"
                        )
                        status = False
                        continue
                    target = self.root_dir / clean_path

                    if not target.exists():
                        # Try relative to file
                        target_rel = md_file.parent / clean_path
                        if not target_rel.exists():
                            # Try figures dir relative to manuscript root
                            target_figs = self.root_dir / "figures" / Path(clean_path).name
                            if not target_figs.exists():
                                # Try output/figures directory (generated figures)
                                target_output = output_figures_dir / Path(clean_path).name
                                if not target_output.exists():
                                    logger.warning(
                                        f"Missing image: '{clean_path}' in {md_file.name}"
                                    )
                                    status = False

                # Check markdown links (P3-M3): wire the previously unused pattern
                for dest in self.link_pattern.findall(content):
                    d = dest.split(" ")[0]
                    if not d or d.startswith("#") or d.startswith("http"):
                        continue  # anchors / web links: fine
                    if Path(d).suffix.lower() in {
                        ".png", ".jpg", ".jpeg", ".svg", ".pdf", ".gif", ".webp",
                    }:
                        continue  # figure assets are checked above w/ output/ dirs
                    if d.startswith("file:"):
                        logger.warning(
                            f"file: link (non-portable/disallowed) '{dest}' in {md_file.name}"
                        )
                        link_status = False
                        continue
                    if self._escapes_root(d):
                        logger.warning(
                            f"Link target escapes manuscript root: '{dest}' in {md_file.name}"
                        )
                        link_status = False
                        continue
                    local = (md_file.parent / d).resolve()
                    if not local.exists():
                        logger.warning(
                            f"Broken or unresolvable link target '{dest}' in {md_file.name}"
                        )
                        link_status = False

        status = status and link_status
        return status

    def check_style(self) -> bool:
        """Check for stylistic issues like hyperbole.

        Returns True only when no style warnings were found.  A style issue
        is a real (if advisory) finding, so the summary row must reflect it
        rather than always reporting "Style: PASS" (a vacuous pass).
        """
        logger.info("Checking style guidelines...")
        status = True

        for md_file in self.md_files:
            with open(md_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for i, line in enumerate(lines):
                    for word in self.hyperbole_words:
                        if re.search(r"\b" + re.escape(word) + r"\b", line, re.IGNORECASE):
                            logger.warning(
                                f"Potential hyperbole '{word}' in {md_file.name}:{i + 1}"
                            )
                            status = False

        return status

    def check_domain_content(self) -> bool:
        """Verify domain application sections have required structural elements."""
        logger.info("Checking domain section content...")
        status = True

        domain_files = sorted(self.root_dir.glob("09c_*.md"))
        domain_files += sorted(self.root_dir.glob("09d_*.md"))
        domain_files += sorted(self.root_dir.glob("09e_*.md"))
        domain_files += sorted(self.root_dir.glob("09f_*.md"))
        domain_files += sorted(self.root_dir.glob("09g_*.md"))
        domain_files += sorted(self.root_dir.glob("09h_*.md"))
        domain_files += sorted(self.root_dir.glob("09i_*.md"))
        domain_files += sorted(self.root_dir.glob("09j_*.md"))
        domain_files += sorted(self.root_dir.glob("09k_*.md"))
        domain_files += sorted(self.root_dir.glob("09l_*.md"))

        if not domain_files:
            logger.warning("No domain section files found (09c–09l).")
            return True  # Don't fail if this is not the applications paper

        required_elements = [
            "Adversary Class",
            "Attack Pattern",
            "OODA",
        ]

        for domain_file in domain_files:
            with open(domain_file, "r", encoding="utf-8") as f:
                content = f.read()

            for element in required_elements:
                if element not in content:
                    logger.warning(
                        f"Domain {domain_file.name} missing required element: '{element}'"
                    )
                    status = False

        if status:
            logger.info(f"  All {len(domain_files)} domain sections have required elements.")

        return status

    def run_all(self) -> bool:
        """Run all verifications.

        Returns:
            True if every check passed, False otherwise. Does not call
            sys.exit() -- callers (e.g. the CLI entry point in
            scripts/verify_manuscript.py) own the process exit code, so
            this method stays usable as a plain library call (including
            from tests, without needing pytest.raises(SystemExit)).
        """
        logger.info(f"Starting verification on {self.root_dir}...")

        results = {
            "Files": self.check_files_exist(),
            "Pandoc Attributes": self.check_pandoc_attributes(),
            "Math Hygiene": self.check_math_hygiene(),
            "Citations": self.check_citations(),
            "Labels/Refs": self.check_labels_and_refs(),
            "Images/Links": self.check_images_and_links(),
            "Style": self.check_style(),
            "Domain Content": self.check_domain_content(),
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
