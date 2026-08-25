#!/usr/bin/env python3
"""Write every ledger value back into the manuscripts that quote it.

``scripts/check_series_integrity.py`` is the read path: it fails the build when a
stated number disagrees with the artifact it came from.  This is the matching
write path.  Together they close the loop that Part 2 already had for its own
manuscript (``injector.py`` + ``claim_registry.py``) and that Parts 1 and 3 had
not: regenerate the evidence, run this, and every number the papers share is
rewritten from the artifacts rather than re-typed by a human.

    python3 scripts/inject_series_values.py            # report, change nothing
    python3 scripts/inject_series_values.py --write    # actually rewrite
    python3 scripts/inject_series_values.py --write --only parametric_ceiling_low

Design
------
Every substitution reuses the *same* pattern and context rules the gate checks
with, taken from :mod:`series_ledger`.  Two mechanisms that must agree about
where a number lives is the defect class this whole apparatus exists to catch,
so there is one definition and both sides import it.

Formatting is decided per unit, not per call site: percentages keep the number
of decimals already written at that site, so rewriting 44.8 does not silently
become 44.80 and counts stay integral.  A substitution that would not change the
text is not counted as a change.

Safety
------
Reporting is the default; ``--write`` is required to touch a file.  The run
refuses to write if any ledger variable fails to derive, because injecting a
subset of the values would leave the manuscripts in a state where some numbers
came from the artifacts and some did not, which is worse than either extreme.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

from series_ledger import (  # noqa: E402
    LEDGER,
    REPO_ROOT,
    LedgerVariable,
    MissingArtifact,
    manuscript_files,
    to_number,
)

WORD_FOR = {
    1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
    6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
    11: "eleven", 12: "twelve",
}


@dataclass
class Change:
    path: Path
    line: int
    variable: str
    before: str
    after: str
    #: Character offsets of the matched literal within its line. The rewrite
    #: is applied to this span and nowhere else.
    start: int = -1
    end: int = -1

    def render(self) -> str:
        # A path outside the repository is unusual but must not raise here:
        # this method is called from the refusal branch, and a crash while
        # reporting that a rewrite was declined would turn a safe refusal into
        # a failed run.
        try:
            location: Path | str = self.path.relative_to(REPO_ROOT)
        except ValueError:
            location = self.path
        return f"  {location}:{self.line}: {self.variable}: {self.before!r} -> {self.after!r}"


def format_like(stated: str, value: float) -> str:
    """Render ``value`` in the shape the site already uses.

    A site written ``44.8`` gets one decimal back, not ``44.80``; a site written
    ``ten`` gets a word back, not ``10``.  Preserving the existing shape keeps
    the diff to the digits that actually changed, which is what makes an
    injected manuscript reviewable.
    """
    text = stated.strip()
    if text.lower() in {w for w in WORD_FOR.values()}:
        return WORD_FOR.get(int(round(value)), str(int(round(value))))
    if "{,}" in text or "," in text:
        return f"{int(round(value)):,}".replace(",", "{,}") if "{,}" in text else f"{int(round(value)):,}"
    if "." in text:
        decimals = len(text.split(".", 1)[1])
        return f"{value:.{decimals}f}"
    return str(int(round(value)))


def substitutions_for(var: LedgerVariable, value: float) -> Iterable[Change]:
    """Every site this variable governs, with the text it should carry."""
    if var.pattern is None:
        return
    for part in var.parts:
        for path in manuscript_files(part):
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            for number, line in enumerate(lines, start=1):
                seen = False
                for match in var.pattern.finditer(line):
                    if not var.in_scope(line, match):
                        continue
                    if var.first_only and seen:
                        break
                    seen = True
                    stated = match.group(1)
                    try:
                        current = to_number(stated)
                    except ValueError:
                        continue
                    if abs(current - value) <= var.tolerance:
                        continue
                    yield Change(
                        path,
                        number,
                        var.id,
                        stated,
                        format_like(stated, value),
                        match.start(1),
                        match.end(1),
                    )


def apply_changes(changes: Sequence[Change]) -> int:
    """Rewrite files, one line at a time, replacing only the stated literal."""
    by_path: dict[Path, list[Change]] = {}
    for change in changes:
        by_path.setdefault(change.path, []).append(change)

    written = 0
    for path, items in by_path.items():
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        # Apply right-to-left so an earlier edit cannot shift a later offset,
        # and highest line first for the same reason across a line boundary.
        for change in sorted(items, key=lambda c: (c.line, c.start), reverse=True):
            index = change.line - 1
            line = lines[index]
            if change.start < 0:
                # No recorded span: refuse rather than guess. This used to fall
                # back to ``line.replace(before, after, 1)``, which rewrote the
                # first occurrence of the literal anywhere on the line rather
                # than the one the pattern matched. With a one-character
                # literal that is almost always the wrong number: writing the
                # narrow end of a gap turned "Assumption 4" into
                # "Assumption 10" in Part 1, and "$\sim$44\% mean detection
                # rate" into "$\sim$104\%" in Part 2's S08 -- both on lines
                # whose gap phrase was several clauses away, and both silently.
                print(
                    f"  refused (no span recorded): {change.render().strip()}",
                    file=sys.stderr,
                )
                continue
            if line[change.start : change.end] != change.before:
                print(
                    f"  refused (line moved under the match): "
                    f"{change.render().strip()}",
                    file=sys.stderr,
                )
                continue
            lines[index] = line[: change.start] + change.after + line[change.end :]
            written += 1
        path.write_text("".join(lines), encoding="utf-8")
    return written


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", action="store_true", help="apply the changes")
    parser.add_argument("--only", action="append", help="restrict to this variable (repeatable)")
    args = parser.parse_args(list(argv) if argv is not None else None)

    selected = [v for v in LEDGER if not args.only or v.id in args.only]
    if args.only:
        unknown = set(args.only) - {v.id for v in LEDGER}
        if unknown:
            print(f"unknown variable(s): {sorted(unknown)}", file=sys.stderr)
            return 2

    values: dict[str, float] = {}
    underivable: list[str] = []
    for var in selected:
        try:
            values[var.id] = var.value()
        except (MissingArtifact, KeyError, IndexError, TypeError, ValueError) as exc:
            underivable.append(f"{var.id}: {type(exc).__name__}: {exc}")

    if underivable:
        print("refusing to run: these variables do not derive, so an injection would")
        print("leave some numbers sourced from the artifacts and some not:")
        for line in underivable:
            print(f"  {line}")
        return 1

    changes = [c for var in selected for c in substitutions_for(var, values[var.id])]

    if not changes:
        print(f"{len(selected)} variable(s) checked; every governed site already matches its artifact.")
        return 0

    print(f"{len(changes)} site(s) disagree with the artifacts:")
    for change in changes:
        print(change.render())

    if not args.write:
        print("\nreport only; pass --write to apply")
        return 1

    written = apply_changes(changes)
    print(f"\nrewrote {written} site(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
