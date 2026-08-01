#!/usr/bin/env python3
"""Front-matter lists and cross-reference verification
======================================================

Two real transformations over ``manuscript/*.md``, driven by
``output/data/figure_registry.json``:

1. **\\listoffigures / \\listoftables** — injected into ``preamble.md`` inside
   the LaTeX code block if not already present.
2. **\\Cref reference verification** — every ``\\Cref{fig:...}`` /
   ``\\Cref{tab:...}`` target in the manuscript must exist in the registry.
   The check is anti-vacuity guarded: if *zero* targets are found the script
   fails rather than printing "all resolved".

**What this script does not do.** It used to advertise a third transformation,
"``\\label`` injection", implemented by ``inject_latex_label``, whose body was
``return content, 0`` — an unconditional no-op that could never fire. It has
been deleted rather than implemented, because it is not needed: figures in
this manuscript carry pandoc attribute blocks (``{#fig:foo width=95%}``) and
pandoc-crossref emits the corresponding ``\\label{}`` itself when compiling to
PDF via XeLaTeX. A manual injector would duplicate those labels.

The script is **non-destructive**: it only *adds* LoF/LoT commands; it never
removes or rewrites captions.

Exit codes: ``0`` all targets resolved; ``1`` registry missing or the
cross-reference check would have been vacuous; ``2`` unresolved targets found.

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

#: A manuscript with no cross-references at all would make ``verify_cref_targets``
#: trivially "pass". Treat that as a broken run, not a clean one.
MIN_CREF_TARGETS = 1


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def load_registry(path: Path) -> dict:
    if not path.exists():
        logger.error("Registry file not found: %s — run generate_figure_registry.py first", path)
        sys.exit(1)
    return json.loads(path.read_text(encoding="utf-8"))


def verify_cref_targets(manuscript_dir: Path, registry: dict) -> tuple[list[str], int]:
    """Check every ``\\Cref``/``\\cref`` target against the registry.

    Args:
        manuscript_dir: Directory of manuscript ``*.md`` files.
        registry: Mapping of label → registry entry.

    Returns:
        ``(warnings, n_targets)`` where *warnings* names each unresolved
        target and *n_targets* is the total number of targets inspected.
        Callers must check *n_targets* — a zero-target run resolves
        vacuously.
    """
    warnings = []
    n_targets = 0
    for md_file in sorted(manuscript_dir.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        # Match both \Cref{...} and \cref{...}
        for m in re.finditer(r"\\[Cc]ref\{((?:fig|tab|tbl):[^}]+)\}", content):
            target = m.group(1)
            n_targets += 1
            # Normalise: tbl: → tab:
            canonical = target.replace("tbl:", "tab:")
            if canonical not in registry and target not in registry:
                warnings.append(f"{md_file.name}: unresolved \\Cref{{{target}}}")
    return warnings, n_targets


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

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inject LoF/LoT into the preamble and verify \\Cref targets."
    )
    base_dir = Path(__file__).resolve().parent.parent
    parser.add_argument("--root", default=str(base_dir / "manuscript"))
    parser.add_argument(
        "--registry", default=str(base_dir / "output" / "data" / "figure_registry.json")
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print changes without writing files"
    )
    args = parser.parse_args(argv)

    manuscript_dir = Path(args.root)
    registry_path = Path(args.registry)

    registry = load_registry(registry_path)
    logger.info("Loaded registry: %d entries", len(registry))

    # Preamble LoF/LoT
    preamble_path = manuscript_dir / "preamble.md"
    if preamble_path.exists():
        ensure_lof_lot_in_preamble(preamble_path, dry_run=args.dry_run)
    else:
        logger.warning("No preamble.md in %s — skipping LoF/LoT injection", manuscript_dir)

    # Cross-reference verification
    logger.info("Verifying \\Cref targets …")
    warnings, n_targets = verify_cref_targets(manuscript_dir, registry)
    if n_targets < MIN_CREF_TARGETS:
        logger.error(
            "Cross-reference check inspected %d targets (minimum %d) — it would "
            "have passed vacuously. Check --root=%s.",
            n_targets,
            MIN_CREF_TARGETS,
            manuscript_dir,
        )
        return 1
    if warnings:
        logger.warning(
            "Unresolved cross-references found (%d of %d targets):",
            len(warnings),
            n_targets,
        )
        for w in warnings:
            logger.warning("  %s", w)
        return 2

    logger.info("All %d \\Cref targets resolved against the registry", n_targets)
    return 0


if __name__ == "__main__":
    sys.exit(main())
