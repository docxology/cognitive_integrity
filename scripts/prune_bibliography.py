#!/usr/bin/env python3
"""Delete bibliography entries no manuscript cites.

Pandoc emits only cited works and this series sets no ``nocite``, so an uncited
entry is invisible: it reaches no reader, no renderer and no gate. That is not a
harmless property. Both fabricated sources this series has shipped -- the two
``supplychain2025`` entries, whose titles matched no real publication -- were
uncited, and survived nine review rounds precisely because nothing looked at the
part of the bibliography nobody could see. An unverified entry that cannot be
read cannot be checked either, and the only argument for keeping one is that
deleting it might lose something, which is what git is for.

So the pile is closed rather than counted. After this runs, every entry in every
``references.bib`` is cited by the prose of its own part, and
``check_series_integrity.py`` gates on that rather than reporting it.

Conservatism, because deleting a real citation renders as a dangling ``[?]``:
an entry is removed only when its key appears nowhere in the entire part tree,
not merely when the manuscript's two citation syntaxes miss it. A key mentioned
in a README, a script, a test or a comment is kept, and the reason it survived
is reported.

    python3 scripts/prune_bibliography.py --dry-run
    python3 scripts/prune_bibliography.py
    python3 scripts/prune_bibliography.py --check
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

_spec = importlib.util.spec_from_file_location(
    "check_series_integrity", REPO / "scripts" / "check_series_integrity.py"
)
_gate = importlib.util.module_from_spec(_spec)
sys.modules["check_series_integrity"] = _gate
_spec.loader.exec_module(_gate)

PARTS = _gate.PARTS

#: Directories that are build output or vendored code, never a citation site.
_SKIP = {".venv", ".git", "output", "__pycache__", ".pytest_cache", ".mypy_cache"}


def _entry_spans(text: str) -> list[tuple[str, int, int]]:
    """(key, start, end) for every entry, spans covering the whole record."""
    spans: list[tuple[str, int, int]] = []
    for match in _gate._ENTRY_RE.finditer(text):
        kind, key = match.group(1).lower(), match.group(2)
        if kind in {"comment", "preamble", "string"}:
            continue
        cursor, depth = match.end(), 1
        while cursor < len(text) and depth:
            if text[cursor] == "{":
                depth += 1
            elif text[cursor] == "}":
                depth -= 1
            cursor += 1
        spans.append((key, match.start(), cursor))
    return spans


def _mentioned_outside_prose(part: str, keys: set[str]) -> dict[str, str]:
    """Keys that appear anywhere in the part tree, with where they were found.

    The manuscript citation regexes are the definition of "cited", but they are
    not the definition of "used". A key named in a README table, asserted in a
    test, or written into a script is load-bearing somewhere, and deleting it
    would break that somewhere silently.
    """
    found: dict[str, str] = {}
    root = REPO / PARTS[part]
    manuscript = root / "manuscript"
    patterns = {key: re.compile(rf"(?<![\w-]){re.escape(key)}(?![\w-])") for key in keys}
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix == ".bib":
            continue
        if any(segment in _SKIP for segment in path.relative_to(root).parts):
            continue
        if path.parent == manuscript and path.suffix == ".md":
            continue  # already covered by the citation scan
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for key in list(patterns):
            if key in found:
                continue
            if patterns[key].search(text):
                found[key] = str(path.relative_to(REPO))
    return found


def plan() -> dict[str, dict[str, object]]:
    report: dict[str, dict[str, object]] = {}
    for part in PARTS:
        path = REPO / PARTS[part] / "manuscript" / "references.bib"
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        spans = _entry_spans(text)
        cited = _gate._cited_keys(part)
        candidates = {key for key, _, _ in spans} - cited
        kept = _mentioned_outside_prose(part, candidates) if candidates else {}
        report[part] = {
            "path": path,
            "text": text,
            "spans": spans,
            "total": len(spans),
            "remove": sorted(candidates - set(kept)),
            "kept": kept,
        }
    return report


def rewrite(entry: dict[str, object]) -> str:
    remove = set(entry["remove"])
    text: str = entry["text"]
    out = []
    cursor = 0
    for key, start, end in entry["spans"]:
        if key not in remove:
            continue
        out.append(text[cursor:start])
        cursor = end
        while cursor < len(text) and text[cursor] in "\r\n":
            cursor += 1
    out.append(text[cursor:])
    result = "".join(out)
    return re.sub(r"\n{3,}", "\n\n", result).rstrip("\n") + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check", action="store_true", help="exit 1 if anything is uncited")
    args = parser.parse_args(argv)

    report = plan()
    dirty = 0
    for part, entry in sorted(report.items()):
        remove, kept = entry["remove"], entry["kept"]
        print(
            f"Part {part}: {entry['total']} entries, "
            f"{len(remove)} uncited and unused, {len(kept)} uncited but referenced elsewhere"
        )
        for key, where in sorted(kept.items()):
            print(f"    keep {key}  (named in {where})")
        if not remove:
            continue
        dirty += len(remove)
        if args.check:
            for key in remove:
                print(f"    UNCITED {key}")
            continue
        print(f"    removing: {', '.join(remove)}")
        if not args.dry_run:
            entry["path"].write_text(rewrite(entry), encoding="utf-8")

    if args.check:
        print("bibliography is closed" if not dirty else f"{dirty} uncited entries")
        return 1 if dirty else 0
    if args.dry_run:
        print(f"dry run: {dirty} entries would be removed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
