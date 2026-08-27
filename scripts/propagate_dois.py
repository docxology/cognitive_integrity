#!/usr/bin/env python3
"""Carry a newly reserved DOI from the config into every place that prints it.

The release tooling reserves a DOI and writes it to ``publication.doi`` in the
part's ``manuscript/config.yaml``. The cover page reads a different key,
``paper.doi``, and the abstracts, cross-part signposts, READMEs and BibTeX
entries hold the identifier as literal text -- 165 occurrences across the three
papers. Nothing carried the reserved value from the first key to the rest, so a
DOI could be minted, land in the config, and never reach the paper it names.

This closes that gap. For each part it takes ``publication.doi`` as the truth,
and rewrites ``paper.doi`` plus every tracked occurrence of the DOI that key is
replacing. Run it after a reservation and before the render that produces the
deposited PDF:

    python3 scripts/propagate_dois.py --check     # report, change nothing
    python3 scripts/propagate_dois.py             # rewrite

``--check`` exits 1 when a rewrite is pending, so a release can refuse to
proceed with a stale identifier on the cover.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PARTS = (
    "cogsec_multiagent_1_theory",
    "cogsec_multiagent_2_computational",
    "cogsec_multiagent_3_practical",
)
SUFFIXES = (".md", ".yaml", ".yml", ".cff", ".bib", ".py", ".toml", ".txt", ".json")

_PAPER_DOI = re.compile(r"^(\s{2}doi:\s*)(['\"]?)(10\.\d{4,9}/\S+?)\2\s*$", re.M)
_PUBLICATION_DOI = re.compile(
    r"^publication:\n(?:[ \t]+.*\n|\n)*?[ \t]+doi:\s*['\"]?(10\.\d{4,9}/[^'\"\s]+)['\"]?",
    re.M,
)


def _tracked_text_files() -> list[Path]:
    out = subprocess.run(
        ["git", "-C", str(REPO), "ls-files", "-z"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [
        REPO / name
        for name in out.split("\0")
        if name and Path(name).suffix in SUFFIXES and (REPO / name).is_file()
    ]


def pending_rewrites() -> dict[str, tuple[str, str]]:
    """Per part, the ``(old, new)`` DOI pair still to be carried across."""
    pending: dict[str, tuple[str, str]] = {}
    for part in PARTS:
        config = REPO / part / "manuscript" / "config.yaml"
        text = config.read_text(encoding="utf-8")
        publication = _PUBLICATION_DOI.search(text)
        paper = _PAPER_DOI.search(text)
        if not publication:
            raise SystemExit(f"{config}: no publication.doi to propagate from")
        if not paper:
            raise SystemExit(f"{config}: no paper.doi to propagate into")
        if publication.group(1) != paper.group(3):
            pending[part] = (paper.group(3), publication.group(1))
    return pending


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="report pending rewrites and exit 1 rather than performing them",
    )
    parser.add_argument(
        "--map",
        action="append",
        metavar="OLD=NEW",
        default=[],
        help="explicit old=new DOI replacement to carry across tracked files "
        "(repeatable). Needed when reserve already wrote the new DOI into "
        "both config keys, which makes the derived cover-vs-publication "
        "comparison see no pending rewrite even though every literal "
        "occurrence elsewhere is stale.",
    )
    args = parser.parse_args(argv)

    pending = pending_rewrites()
    for spec in args.map:
        old_doi, sep, new_doi = spec.partition("=")
        if not sep or not old_doi.startswith("10.") or not new_doi.startswith("10."):
            raise SystemExit(f"--map expects OLD=NEW DOIs, got: {spec}")
        pending[f"cli:{old_doi}"] = (old_doi, new_doi)
    if not pending:
        print("every part's cover DOI already matches its publication DOI")
        return 0

    for part, (old, new) in sorted(pending.items()):
        print(f"  {part}: {old} -> {new}")
    if args.check:
        print(f"{len(pending)} part(s) carry a superseded DOI on the cover")
        return 1

    files = _tracked_text_files()
    touched = 0
    replaced = 0
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        updated = text
        for old, new in pending.values():
            if old in updated:
                replaced += updated.count(old)
                updated = updated.replace(old, new)
        # The record URL follows the identifier.
        for old, new in pending.values():
            old_id, new_id = old.rsplit(".", 1)[-1], new.rsplit(".", 1)[-1]
            for template in ("https://zenodo.org/records/{}", "https://zenodo.org/record/{}"):
                if template.format(old_id) in updated:
                    replaced += updated.count(template.format(old_id))
                    updated = updated.replace(template.format(old_id), template.format(new_id))
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            touched += 1

    print(f"rewrote {replaced} occurrence(s) across {touched} file(s)")
    still = pending_rewrites()
    if still:
        print(f"{len(still)} part(s) still mismatched after the rewrite", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
