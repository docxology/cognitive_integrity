#!/usr/bin/env python3
"""Fix MSC-01: Convert bold-paragraph table labels to pandoc-crossref table captions.

The manuscript uses ``**Table: Title** {#tab:xxx}`` on a bold paragraph line
followed by a blank line and then a pipe table. pandoc-crossref does not
create table anchors for paragraphs, so every ``\\cref{tab:xxx}`` renders as
``??`` in the PDF.

This script:
1. Strips the ``**`` bold markers from the caption
2. Removes the blank line between caption and table so pandoc-crossref
   recognises the caption as belonging to the following pipe table

Run with ``--dry-run`` to preview changes without modifying files.
"""

import argparse
import re
import sys
from pathlib import Path

CAPTION_RE = re.compile(
    r'^\*\*Table: (.*?)\*\* \{#(tab:[^}]+)\}$',
    re.MULTILINE,
)


def fix_file(path: Path, *, dry_run: bool = False) -> list[str]:
    """Return the list of table IDs that were fixed in *path*."""
    original = path.read_text(encoding="utf-8")
    modified = original
    fixed: list[str] = []

    for match in CAPTION_RE.finditer(original):
        label = match.group(2)
        old_line = match.group(0)
        new_line = f"Table: {match.group(1)} {{#{label}}}"

        # Check if the next line (after the caption) is blank, and the one
        # after that starts a pipe table.  If so, collapse the blank line
        # so the caption attaches directly to the table.
        end = match.end()
        if original[end:end + 1] == "\n":
            rest = original[end + 1:]
            if rest.startswith("\n|"):
                # Caption + blank line + pipe table → caption + pipe table
                old_line += "\n"
                new_line += "\n"

        if old_line != new_line:
            modified = modified.replace(old_line, new_line, 1)
            fixed.append(label)

    if modified != original:
        if not dry_run:
            path.write_text(modified, encoding="utf-8")
            print(f"  fixed {len(fixed)} table(s) in {path.name}: {', '.join(fixed)}")
        else:
            print(f"  [DRY RUN] would fix {len(fixed)} table(s) in {path.name}: {', '.join(fixed)}")
    return fixed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manuscript",
        default="manuscript",
        help="Path to the manuscript directory (default: manuscript).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files.",
    )
    args = parser.parse_args(argv)

    manuscript = Path(args.manuscript)
    if not manuscript.is_dir():
        print(f"ERROR: {manuscript} is not a directory", file=sys.stderr)
        return 1

    md_files = sorted(manuscript.glob("*.md"))
    if not md_files:
        print(f"ERROR: no .md files found under {manuscript}", file=sys.stderr)
        return 1

    total = 0
    for path in md_files:
        fixed = fix_file(path, dry_run=args.dry_run)
        total += len(fixed)

    action = "would fix" if args.dry_run else "fixed"
    print(f"\n{action} {total} table label(s) across {len(md_files)} file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
