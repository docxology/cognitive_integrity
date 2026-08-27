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
- Detailed logging
"""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path
from typing import Set

# Logging is NOT configured at import time: a module-level basicConfig with a
# CWD-relative FileHandler would append to ./manuscript_verification.log on
# every `import src.verification` (including test runs), dirtying the working
# tree and failing from read-only CWDs.  Callers that want the file handler
# (e.g. scripts/verify_manuscript.py) call configure_logging() explicitly.
logger = logging.getLogger(__name__)


def configure_logging(level: int = logging.INFO) -> None:
    """Configure stream + file logging for the verification CLI.

    Idempotent; safe to call more than once (basicConfig is a no-op after
    the first call).  The file handler writes to the CWD-relative
    `manuscript_verification.log` (gitignored).
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("manuscript_verification.log"),
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

        # Math-hygiene checks (round-7 audit, F2/F11):
        # - [A-Za-z}]\*[{A-Za-z] catches subscript corruption where a literal
        #   star was substituted for an underscore (\mathcal{T}*{i \to j}),
        #   which pandoc passes through as a math-mode binary operator.
        # - \\[a-zA-Z] catches double-escaped control sequences (P_{\\text{...}})
        #   that pandoc leaves as two backslashes inside math, producing a
        #   line break + literal text in LaTeX.
        self.subscript_star_pattern = re.compile(r"[A-Za-z}]\*[{A-Za-z]")
        self.double_backslash_cmd_pattern = re.compile(r"\\\\[a-zA-Z]")

    def check_pandoc_attributes(self) -> bool:
        """Check for bare ``{#label}`` attribute lines that pandoc passes
        through as literal text (breaking the LaTeX build).

        A legitimate pandoc identifier attribute is attached to a heading,
        image, or div (``# Heading {#sec:x}``, ``![..](..){#fig:x}``).  A line
        that is *only* ``{#eq:...}`` is not valid pandoc attribute syntax and
        survives the markdown-to-LaTeX conversion verbatim, causing
        ``You can't use `macro parameter character #'`` LaTeX errors
        (round-7 audit, F1).
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

        Flags (round-7 audit, F2/F11):
        - subscript-corruption stars: ``\\mathcal{T}*{i \\to j}`` (should be
          ``\\mathcal{T}_{i \\to j}``)
        - double-escaped control sequences inside math: ``P_{\\text{x}}``
          (should be ``P_{\\text{x}}``)

        Legitimate starred commands (``\\vspace*``, ``\\DeclareMathOperator*``)
        are excluded.
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

                # Pandoc labels {#label}
                # Pandoc identifiers start with a letter; "#1"-style LaTeX
                # macro parameters must not be counted as labels.
                pandoc_labels = re.findall(r"\{#([A-Za-z][^}]*)\}", content)
                for label in pandoc_labels:
                    defined_labels[label] = defined_labels.get(label, 0) + 1

        # Duplicate labels produce "Label `X' multiply defined" LaTeX warnings
        # and make \\cref resolve to the *last* definition, silently
        # contradicting cross-references that intend the first (round-7
        # audit, F3: cor:layered-defense and sec:limitations were duplicated).
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
                    # Handle multiple refs like \\cref{fig:1,fig:2}
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

        Rejects absolute and parent-escaping image refs, which would
        otherwise let ``root / abs`` probe outside the manuscript tree, and
        validates every markdown link it matches: matching a link without
        checking it reports a clean run over targets nobody resolved.
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

                for dest in self.link_pattern.findall(content):
                    d = dest.split(" ")[0]
                    if not d or d.startswith("#") or d.startswith("http"):
                        continue
                    if Path(d).suffix.lower() in {
                        ".png", ".jpg", ".jpeg", ".svg", ".pdf", ".gif", ".webp",
                    }:
                        continue
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
        """Check for stylistic issues like hyperbole."""
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
                            # #20: reflect a real style hit in the status instead of
                            # always reporting PASS (a style warning is a finding).
                            status = False

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
            "Citations": self.check_citations(),
            "Labels/Refs": self.check_labels_and_refs(),
            "Pandoc Attributes": self.check_pandoc_attributes(),
            "Math Hygiene": self.check_math_hygiene(),
            "Images/Links": self.check_images_and_links(),
            "Style": self.check_style(),
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
