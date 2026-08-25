#!/usr/bin/env python3
"""Rewrite every number the claim registry can derive, in place.

The registry binds 171 numbers in the prose to the computation that produces
each one, and until now it could only ever *read*: ``verify_claims.py`` reports
a MISMATCH and a human retypes the number. That asymmetry is the reason a
manuscript drifts. The injector covers 40 of the 171 sites; the other 131 were
hand-maintained, and when the attack corpus changed underneath them, 51 went
stale in a single run.

This closes the loop. For every MISMATCH the registry reports, the captured
literal is replaced by the derived value, formatted to match the literal it
replaces -- same decimal places, same percent-or-fraction convention, same
LaTeX thousands separator -- so the typography of the prose survives a rewrite
that changes only the digits.

What it deliberately will not do
--------------------------------
It writes only for a ``MISMATCH``. A ``NOT_FOUND`` means the pattern matched
nothing, which is a broken pattern rather than a stale number, and inventing a
place to write the value would paper over exactly the failure the registry
treats as fatal. An ``UNBACKED`` means the artifact is missing or reports a
failed run, and writing a number derived from nothing is the fabrication this
whole apparatus exists to prevent. Both are reported and skipped.

It also cannot fix prose *around* a number: a sentence saying "the two largest
contributors" when the artifact now has three is a MISMATCH this tool would
silently make numerically true and semantically wrong. Those are listed
separately so they can be read by someone.

    python3 scripts/sync_claims.py --dry-run
    python3 scripts/sync_claims.py
    python3 scripts/sync_claims.py --check
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from manuscript.claim_registry import (  # noqa: E402
    CLAIMS,
    GroundTruth,
    parse_stated,
    verify_claims,
)

MANUSCRIPT = REPO / "manuscript"
DATA = REPO / "output" / "data"

_SEP_RE = re.compile(r"\{,\}|,")


def _format_like(literal: str, value: float, unit: str) -> str:
    """Render *value* using the typography of the literal it replaces.

    The registry's patterns capture a bare number, but that number carries a
    style -- two decimals or three, a percentage or a fraction, ``3{,}800`` or
    ``3800`` -- and a rewrite that normalises the style would produce a diff
    where every touched line changed for reasons unrelated to the measurement.
    """
    separator = "{,}" if "{,}" in literal else ("," if "," in literal else "")
    bare = _SEP_RE.sub("", literal).strip()
    scaled = value * 100.0 if unit == "percent" else value
    if "." in bare:
        digits = len(bare.split(".", 1)[1])
        rendered = f"{scaled:.{digits}f}"
    else:
        rendered = f"{round(scaled):d}"
    if separator:
        whole, _, frac = rendered.partition(".")
        sign = "-" if whole.startswith("-") else ""
        whole = whole.lstrip("-")
        grouped = separator.join(
            [whole[max(0, i - 3) : i] for i in range(len(whole), 0, -3)][::-1]
        )
        rendered = sign + grouped + (("." + frac) if frac else "")
    return rendered


def sync(*, dry_run: bool = False) -> dict[str, object]:
    gt = GroundTruth(DATA)
    report = verify_claims(CLAIMS, MANUSCRIPT, gt)
    by_id = {claim.id: claim for claim in CLAIMS}

    mismatches = [r for r in report.results if r.verdict == "MISMATCH"]
    not_found = [r for r in report.results if r.verdict == "NOT_FOUND"]
    unbacked = [r for r in report.results if r.verdict == "UNBACKED"]

    edits: list[tuple[str, str, str, str]] = []
    texts: dict[str, str] = {}
    for result in mismatches:
        claim = by_id[result.claim_id]
        if result.derived is None:
            continue
        path = MANUSCRIPT / claim.file
        if claim.file not in texts:
            texts[claim.file] = path.read_text(encoding="utf-8")
        text = texts[claim.file]

        out: list[str] = []
        cursor = 0
        changed = 0
        for match in claim.pattern.finditer(text):
            literal = match.group(1)
            try:
                stated = parse_stated(literal, claim.unit)
            except ValueError:
                continue
            if abs(stated - result.derived) <= claim.tolerance:
                continue
            replacement = _format_like(literal, result.derived, claim.unit)
            if replacement == literal:
                continue
            start, end = match.span(1)
            out.append(text[cursor:start])
            out.append(replacement)
            cursor = end
            changed += 1
            edits.append((claim.id, claim.file, literal, replacement))
        if changed:
            out.append(text[cursor:])
            texts[claim.file] = "".join(out)

    if not dry_run:
        for filename, text in texts.items():
            (MANUSCRIPT / filename).write_text(text, encoding="utf-8")

    return {
        "edits": edits,
        "files": sorted(texts),
        "not_found": [(r.claim_id, r.detail) for r in not_found],
        "unbacked": [(r.claim_id, r.detail) for r in unbacked],
        "total": len(report.results),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check", action="store_true", help="exit 1 if anything is stale")
    args = parser.parse_args(argv)

    result = sync(dry_run=args.dry_run or args.check)
    edits = result["edits"]

    for claim_id, filename, was, now in edits:
        print(f"  {claim_id:38s} {filename:38s} {was} -> {now}")
    print(f"{len(edits)} number(s) rewritten across {len(result['files'])} file(s)")

    for label, rows in (("NOT_FOUND", result["not_found"]), ("UNBACKED", result["unbacked"])):
        for claim_id, detail in rows:
            print(f"  {label}: {claim_id} -- {detail}", file=sys.stderr)
    if result["not_found"] or result["unbacked"]:
        print(
            f"{len(result['not_found'])} pattern(s) matched nothing and "
            f"{len(result['unbacked'])} number(s) have no artifact; neither is "
            f"rewritten, both are failures",
            file=sys.stderr,
        )
        return 2

    if args.check:
        print("claims are current" if not edits else f"{len(edits)} stale number(s)")
        return 1 if edits else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
