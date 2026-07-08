#!/usr/bin/env python3
"""Auto-Number Figures & Tables
================================

Reads figure_registry.json and performs the following transformations
across all manuscript/*.md files:

1. **Label anchors** — {#fig:foo width=95%} → {#fig:foo width=95%}   (kept as-is)
2. **\\label injection** — adds ``\\label{fig:foo}`` immediately after each
   figure's caption attribute block so XeLaTeX can resolve \\cref / \\Cref.
3. **\\listoffigures / \\listoftables** — injects the commands into preamble.md
   inside the LaTeX code block if they are not already present.
4. **\\Cref reference verification** — warns if any \\Cref{fig:foo} or
   \\Cref{tab:foo} target is absent from the registry.

The script is **non-destructive**: it only *adds* label anchors where they are
missing and inserts LoF/LoT commands; it never removes or rewrites captions.

Usage:
    python scripts/auto_number_figures.py [--root manuscript]
        [--registry output/data/figure_registry.json] [--dry-run]
"""

import argparse
import json
import logging
import re
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def load_registry(path: Path) -> dict:
    if not path.exists():
        logger.error("Registry file not found: %s — run generate_figure_registry.py first", path)
        sys.exit(1)
    return json.loads(path.read_text(encoding="utf-8"))


def inject_latex_label(content: str, label: str) -> tuple[str, int]:
    """NOTE: pandoc-crossref automatically generates \\label{} from {#fig:...}
    attribute blocks when compiling to PDF via XeLaTeX. Manual \\label injection
    is therefore NOT needed for figures managed by pandoc-crossref.

    This function is retained for supplementary files or custom LaTeX environments
    where pandoc-crossref is not active, but returns unchanged content by default.

    Returns (content, 0) — no changes.
    """
    # Pandoc-crossref handles \label{} generation; no injection needed.
    return content, 0


def verify_cref_targets(manuscript_dir: Path, registry: dict) -> list[str]:
    """Return list of warning strings for \\Cref{} targets not in the registry."""
    warnings = []
    for md_file in sorted(manuscript_dir.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        # Match both \Cref{...} and \cref{...}
        for m in re.finditer(r"\\[Cc]ref\{((?:fig|tab|tbl):[^}]+)\}", content):
            target = m.group(1)
            # Normalise: tbl: → tab:
            canonical = target.replace("tbl:", "tab:")
            if canonical not in registry and target not in registry:
                warnings.append(f"{md_file.name}: unresolved \\Cref{{{target}}}")
    return warnings


def ensure_lof_lot_in_preamble(preamble_path: Path, dry_run: bool = False) -> bool:
    """Add \\listoffigures and \\listoftables to preamble.md if not already present."""
    content = preamble_path.read_text(encoding="utf-8")
    changed = False

    # We inject just before the closing ``` of the main latex block
    lof_marker = "\\listoffigures"
    lot_marker = "\\listoftables"

    if lof_marker not in content or lot_marker not in content:
        # Find the last ``` (closing code fence)
        # Strategy: insert before the final closing ```
        closing_fence_pattern = re.compile(r"^```\s*$", re.MULTILINE)
        matches = list(closing_fence_pattern.finditer(content))
        if matches:
            insert_pos = matches[-1].start()
            inject = ""
            if lof_marker not in content:
                inject += "\n% Lists of figures and tables for front matter\n\\listoffigures\n"
            if lot_marker not in content:
                inject += "\\listoftables\n"

            new_content = content[:insert_pos] + inject + content[insert_pos:]
            if not dry_run:
                preamble_path.write_text(new_content, encoding="utf-8")
                logger.info("Injected \\listoffigures/\\listoftables into %s", preamble_path)
            else:
                logger.info("[DRY-RUN] Would inject LoF/LoT into %s", preamble_path)
            changed = True
        else:
            logger.warning("Could not find closing ``` fence in %s — skipping LoF/LoT injection", preamble_path)  # noqa: E501

    return changed


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-number figures/tables in manuscript.")
    base_dir = Path(__file__).resolve().parent.parent
    parser.add_argument("--root", default=str(base_dir / "manuscript"))
    parser.add_argument(
        "--registry", default=str(base_dir / "output" / "data" / "figure_registry.json")
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print changes without writing files"
    )
    args = parser.parse_args()

    manuscript_dir = Path(args.root)
    registry_path = Path(args.registry)

    registry = load_registry(registry_path)
    logger.info("Loaded registry: %d entries", len(registry))

    total_injections = 0

    for md_file in sorted(manuscript_dir.glob("*.md")):
        if md_file.name == "preamble.md":
            continue
        content = md_file.read_text(encoding="utf-8")
        new_content = content
        file_injections = 0

        for label, entry in registry.items():
            if entry["section"] + ".md" != md_file.name:
                continue
            if entry["type"] == "figure":
                new_content, n = inject_latex_label(new_content, label)
                file_injections += n
            # Tables: \\label injection for tables (optional — LaTeX handles them differently)
            # We skip table label injection to avoid disrupting table markdown syntax

        if new_content != content:
            if not args.dry_run:
                md_file.write_text(new_content, encoding="utf-8")
                logger.info("Updated %s (+%d labels)", md_file.name, file_injections)
            else:
                logger.info("[DRY-RUN] Would update %s (+%d labels)", md_file.name, file_injections)
            total_injections += file_injections

    logger.info("Total \\label injections: %d", total_injections)

    # Preamble LoF/LoT
    preamble_path = manuscript_dir / "preamble.md"
    if preamble_path.exists():
        ensure_lof_lot_in_preamble(preamble_path, dry_run=args.dry_run)

    # Cross-reference verification
    logger.info("Verifying \\Cref targets …")
    warnings = verify_cref_targets(manuscript_dir, registry)
    if warnings:
        logger.warning("Unresolved cross-references found (%d):", len(warnings))
        for w in warnings:
            logger.warning("  %s", w)
    else:
        logger.info("All \\Cref targets resolved ✓")

    return 0 if not warnings else 2


if __name__ == "__main__":
    sys.exit(main())
