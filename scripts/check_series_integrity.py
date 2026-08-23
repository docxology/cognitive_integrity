#!/usr/bin/env python3
"""Program-level integrity gate for the three-paper CIF series.

Every pre-existing gate in this repository is scoped to a *single* part: each
part runs its own ``pytest``, its own ``verify_manuscript.py``, and Part 2 runs
its own reader-side claim registry over its own ``manuscript/``.  Nothing
checked the series *as a whole*, which is why a shared quantity could be
published as two different numbers in two papers that cite each other, and why
a section could be deleted from Part 2 while Part 1 kept citing its contents.

This script is that missing gate.  It is deliberately stdlib-only and takes no
build step, so it can run from a bare checkout, from any part's virtualenv, or
from CI without installing anything.

Checks
------
``shared-quantities``
    A quantity that appears in more than one paper must appear with the *same*
    value everywhere, and where the value is derivable from Part 2's shipped
    data artifacts it must equal the derived value.  Patterns are matched
    line-wise and gated on context keywords so that, e.g., the LLM-arm's
    ``80--100%`` is never confused with the parametric ceiling's range.

``bibliography``
    Duplicate works within one ``references.bib`` (matched on normalised
    *title* + year, never on bibkey, because the whole failure mode is the same
    work entered twice under two keys), and metadata disagreement for the same
    work across the three bibliographies.

``truncation``
    No manuscript file may end mid-sentence, and no section heading may be
    followed by nothing.  Part 2 shipped a section that was a heading plus one
    severed subordinate clause; the per-part verifiers check cross-reference
    resolution but not section completeness, so the defect was invisible.

``cross-paper-pointers``
    Hardcoded cross-paper pointers of the form ``Part 1, Theorem 3.2a`` or
    ``Part 2, Definition 4`` are rejected.  Section, theorem and definition
    numbers are assigned by the renderer at build time and differ per part, so
    a hand-typed number is unverifiable by construction and silently rots when
    either paper is re-ordered.  Named pointers ("Part 1's Series Detection
    Rate theorem") survive re-ordering and can be checked by a human.

Anti-vacuity
------------
Every check refuses to pass on an empty input set.  A pattern that matches zero
lines is a **failure**, not a skip: a regex that silently stops matching is
indistinguishable from a clean run, and is exactly how a wrong number hides
from a checker.

Usage
-----
    python3 scripts/check_series_integrity.py            # all checks
    python3 scripts/check_series_integrity.py --only bibliography
    python3 scripts/check_series_integrity.py --json

Exit status is 0 only when every selected check passes.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Iterator, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent

PARTS: dict[str, str] = {
    "1": "cogsec_multiagent_1_theory",
    "2": "cogsec_multiagent_2_computational",
    "3": "cogsec_multiagent_3_practical",
}

#: Part 2 owns the generated evidence every paper cites.
DATA_DIR = REPO_ROOT / PARTS["2"] / "output" / "data"

#: Any of these written between two numbers is an en-dash range in this corpus:
#: pandoc ``--``, a literal en/em dash, or a plain hyphen.
DASH = r"(?:--|–|—|-)"


# ---------------------------------------------------------------------------
# Result model
# ---------------------------------------------------------------------------


@dataclass
class Problem:
    """One concrete defect, always carrying a file and a line."""

    check: str
    path: str
    line: int
    message: str

    def render(self) -> str:
        return f"  {self.path}:{self.line}: {self.message}"


@dataclass
class CheckResult:
    name: str
    problems: list[Problem] = field(default_factory=list)
    scanned: int = 0
    note: str = ""

    @property
    def ok(self) -> bool:
        return not self.problems


# ---------------------------------------------------------------------------
# Ground truth: the series ledger
# ---------------------------------------------------------------------------
#
# Every derived number lives in scripts/series_ledger.py, which recomputes it
# from Part 2's shipped artifacts. This module used to carry its own copy of the
# quantity table; two tables that must agree is the same defect class the gate
# exists to catch, so there is now one.

sys.path.insert(0, str(Path(__file__).resolve().parent))
from series_ledger import (  # noqa: E402
    CONTEXT_WINDOW,
    DASH,
    LEDGER,
    MissingArtifact,
    LedgerVariable,
    to_number,
)

SHARED_QUANTITIES = LEDGER

# ---------------------------------------------------------------------------
# File walking
# ---------------------------------------------------------------------------


def manuscript_dir(part: str) -> Path:
    return REPO_ROOT / PARTS[part] / "manuscript"


def manuscript_files(part: str) -> list[Path]:
    root = manuscript_dir(part)
    if not root.is_dir():
        return []
    # preamble.md is LaTeX plumbing, not prose; config.yaml is metadata.
    return sorted(p for p in root.glob("*.md") if p.name != "preamble.md")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:  # pragma: no cover - defensive
        return str(path)


def iter_lines(path: Path) -> Iterator[tuple[int, str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    for number, line in enumerate(text.splitlines(), start=1):
        yield number, line


# ---------------------------------------------------------------------------
# Check: shared quantities
# ---------------------------------------------------------------------------


def check_shared_quantities() -> CheckResult:
    result = CheckResult("shared-quantities")
    for quantity in SHARED_QUANTITIES:
        if quantity.pattern is None:
            continue
        try:
            derived = quantity.value()
        except (MissingArtifact, KeyError, TypeError, ValueError) as exc:
            result.problems.append(
                Problem(
                    result.name,
                    rel(DATA_DIR),
                    0,
                    f"{quantity.id}: cannot derive ground truth ({exc}). "
                    f"An underivable gated quantity is a failure, not a skip.",
                )
            )
            continue

        sightings: list[tuple[Path, int, float, str]] = []
        for part in quantity.parts:
            for path in manuscript_files(part):
                for number, line in iter_lines(path):
                    seen_on_line = False
                    for match in quantity.pattern.finditer(line):
                        if not quantity.in_scope(line, match):
                            continue
                        if quantity.first_only and seen_on_line:
                            break
                        seen_on_line = True
                        try:
                            value = to_number(match.group(1))
                        except ValueError:
                            result.problems.append(
                                Problem(
                                    result.name,
                                    rel(path),
                                    number,
                                    f"{quantity.id}: unparseable literal "
                                    f"{match.group(1)!r}",
                                )
                            )
                            continue
                        sightings.append((path, number, value, line.strip()))

        result.scanned += len(sightings)

        if len(sightings) < quantity.min_occurrences:
            result.problems.append(
                Problem(
                    result.name,
                    "scripts/check_series_integrity.py",
                    0,
                    f"{quantity.id}: matched {len(sightings)} line(s), expected at "
                    f"least {quantity.min_occurrences}. A gated quantity that stops "
                    f"matching is a broken guard, not a clean run.",
                )
            )
            continue

        if derived is None:
            values = {value for _, _, value, _ in sightings}
            if len(values) > 1:
                for path, number, value, _ in sightings:
                    result.problems.append(
                        Problem(
                            result.name,
                            rel(path),
                            number,
                            f"{quantity.id}: stated {value:g}, but the series also "
                            f"states {sorted(values - {value})}. One quantity, one value.",
                        )
                    )
            continue

        for path, number, value, _ in sightings:
            if abs(value - derived) > quantity.tolerance:
                result.problems.append(
                    Problem(
                        result.name,
                        rel(path),
                        number,
                        f"{quantity.id}: states {value:g} but the shipped artifact "
                        f"gives {derived:g}"
                        + (f" ({quantity.description})" if quantity.description else ""),
                    )
                )
    return result


# ---------------------------------------------------------------------------
# Check: bibliography
# ---------------------------------------------------------------------------

_ENTRY_RE = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", re.MULTILINE)
_FIELD_RE = re.compile(r"(\w+)\s*=\s*", re.MULTILINE)


def _balanced_value(text: str, start: int) -> tuple[str, int]:
    """Read a brace- or quote-delimited BibTeX value starting at ``start``."""
    while start < len(text) and text[start].isspace():
        start += 1
    if start >= len(text):
        return "", start
    opener = text[start]
    if opener == "{":
        depth = 0
        for index in range(start, len(text)):
            if text[index] == "{":
                depth += 1
            elif text[index] == "}":
                depth -= 1
                if depth == 0:
                    return text[start + 1 : index], index + 1
        return text[start + 1 :], len(text)
    if opener == '"':
        for index in range(start + 1, len(text)):
            if text[index] == '"' and text[index - 1] != "\\":
                return text[start + 1 : index], index + 1
        return text[start + 1 :], len(text)
    end = start
    while end < len(text) and text[end] not in ",}\n":
        end += 1
    return text[start:end], end


@dataclass
class BibEntry:
    key: str
    kind: str
    fields: dict[str, str]
    line: int


def parse_bib(path: Path) -> list[BibEntry]:
    text = path.read_text(encoding="utf-8", errors="replace")
    entries: list[BibEntry] = []
    for match in _ENTRY_RE.finditer(text):
        kind, key = match.group(1).lower(), match.group(2)
        if kind in {"comment", "preamble", "string"}:
            continue
        cursor = match.end()
        depth = 1
        end = cursor
        while end < len(text) and depth:
            if text[end] == "{":
                depth += 1
            elif text[end] == "}":
                depth -= 1
            end += 1
        body = text[cursor : end - 1]
        fields: dict[str, str] = {}
        pos = 0
        while True:
            field_match = _FIELD_RE.search(body, pos)
            if not field_match:
                break
            value, pos = _balanced_value(body, field_match.end())
            fields[field_match.group(1).lower()] = " ".join(value.split())
        entries.append(
            BibEntry(key, kind, fields, text.count("\n", 0, match.start()) + 1)
        )
    return entries


def normalise_title(title: str) -> str:
    folded = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", folded.lower())


def normalise_people(authors: str) -> str:
    folded = unicodedata.normalize("NFKD", authors).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z]", "", folded.lower())


def _cited_keys(part: str) -> set[str]:
    """Every bibkey the prose actually cites, in either citation syntax."""
    cited: set[str] = set()
    for path in manuscript_files(part):
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in re.finditer(r"\\cite[a-zA-Z]*\*?(?:\[[^\]]*\])*\{([^}]*)\}", text):
            cited |= {key.strip() for key in match.group(1).split(",") if key.strip()}
        for match in re.finditer(r"(?<![\w`])@([A-Za-z][\w:.#$%&+?<>~/-]*)", text):
            cited.add(match.group(1).rstrip(".,;:"))
    return cited


def check_bibliography() -> CheckResult:
    result = CheckResult("bibliography")
    by_title: dict[str, list[tuple[str, Path, BibEntry]]] = {}
    total = 0
    uncited: dict[str, int] = {}

    for part in PARTS:
        path = manuscript_dir(part) / "references.bib"
        if not path.is_file():
            result.problems.append(
                Problem(result.name, rel(path), 0, "bibliography file is missing")
            )
            continue
        entries = parse_bib(path)
        total += len(entries)
        uncited[part] = len({e.key for e in entries} - _cited_keys(part))
        if not entries:
            result.problems.append(
                Problem(result.name, rel(path), 0, "parsed zero entries")
            )
            continue

        # Duplicates inside one file, matched on the work, never on the bibkey.
        seen: dict[tuple[str, str], BibEntry] = {}
        for entry in entries:
            title = entry.fields.get("title", "")
            if not title:
                continue
            signature = (normalise_title(title), entry.fields.get("year", ""))
            if signature in seen:
                first = seen[signature]
                result.problems.append(
                    Problem(
                        result.name,
                        rel(path),
                        entry.line,
                        f"duplicate work: {entry.key!r} repeats {first.key!r} "
                        f"(line {first.line}) -- same title and year under two "
                        f"bibkeys renders as two identical reference rows",
                    )
                )
            else:
                seen[signature] = entry
            by_title.setdefault(signature[0], []).append((part, path, entry))

    # One bibkey must mean one work. Grouping by title cannot see this: it is
    # the opposite grouping, and it is the more dangerous defect, because a
    # reader following the same \cite in two papers lands on two sources.
    by_key: dict[str, list[tuple[str, Path, BibEntry]]] = {}
    for part in PARTS:
        path = manuscript_dir(part) / "references.bib"
        if not path.is_file():
            continue
        for entry in parse_bib(path):
            by_key.setdefault(entry.key, []).append((part, path, entry))

    for key, sightings in by_key.items():
        if len({part for part, _, _ in sightings}) < 2:
            continue
        for attribute, normaliser in (
            ("title", normalise_title),
            ("doi", lambda value: value.strip().lower()),
        ):
            values = {
                normaliser(entry.fields.get(attribute, ""))
                for _, _, entry in sightings
                if entry.fields.get(attribute)
            }
            if len(values) > 1:
                for part, path, entry in sightings:
                    stated = entry.fields.get(attribute, "")
                    if not stated:
                        continue
                    result.problems.append(
                        Problem(
                            result.name,
                            rel(path),
                            entry.line,
                            f"bibkey {key!r} resolves to a different {attribute} in "
                            f"another part; one key must mean one work "
                            f"(this file says {stated[:70]!r})",
                        )
                    )
                break

    # The same work must not disagree about itself across the three papers.
    for title_key, sightings in by_title.items():
        if len({part for part, _, _ in sightings}) < 2:
            continue
        # No "title" here: these entries were grouped by normalised title, so
        # that comparison is unreachable by construction. The bibkey pass above
        # is where a title disagreement can actually surface.
        for attribute, normaliser in (
            ("year", lambda value: value.strip()),
            ("author", normalise_people),
            ("doi", lambda value: value.strip().lower()),
        ):
            values = {
                normaliser(entry.fields.get(attribute, ""))
                for _, _, entry in sightings
                if entry.fields.get(attribute)
            }
            if len(values) > 1:
                for part, path, entry in sightings:
                    stated = entry.fields.get(attribute, "")
                    if not stated:
                        continue
                    result.problems.append(
                        Problem(
                            result.name,
                            rel(path),
                            entry.line,
                            f"{entry.key!r}: {attribute} disagrees with the same "
                            f"work in another part of the series "
                            f"(this file says {stated!r})",
                        )
                    )
                break

    result.scanned = total
    if total == 0:
        result.problems.append(
            Problem(
                result.name,
                "scripts/check_series_integrity.py",
                0,
                "no bibliography entries parsed at all; the parser is broken",
            )
        )

    if uncited:
        # Advisory, deliberately not a failure: pandoc emits only cited works, so
        # an uncited entry never reaches a reader and is not a defect in the
        # paper. It is worth counting anyway. Both fabricated sources this series
        # has shipped -- the two supplychain2025 entries, whose titles matched no
        # real publication -- were uncited, which is exactly why nothing caught
        # them: no reader saw them and no check looked at them. A visible count
        # means the pile cannot quietly grow.
        result.note = "uncited entries (not rendered; never reach a reader): " + ", ".join(
            f"Part {part} {count}" for part, count in sorted(uncited.items())
        )
    return result


# ---------------------------------------------------------------------------
# Check: truncation
# ---------------------------------------------------------------------------

#: A line that legitimately ends a file without sentence punctuation.
_STRUCTURAL_END = re.compile(
    r"^\s*(?:[-*+]\s|\d+\.\s|\||#{1,6}\s|```|~~~|\$\$|:::|<!--|>\s*$"
    r"|\\(?:end\{|newpage|clearpage|pagebreak|vfill|hrulefill)"
    # A "\textbf{Label}: value" line is a labelled field, not a sentence.
    r"|\\textbf\{)"
)
#: Trailing emphasis/quote markers that may follow the terminator: a sentence
#: closing an italic run ends ``...benchmarks.*``, which is complete prose.
_SENTENCE_END = re.compile(
    r"[.!?:;)}\]\"'”’][*_`\"'”’)\]]*\s*$"
    r"|\\\\\s*$"
    r"|-{3,}\s*$"
    # A proof or derivation closing on a QED mark is finished.
    r"|(?:\\blacksquare|\\square|\\qed)\s*\$?\s*$"
)


def check_truncation() -> CheckResult:
    """Every section must end in finished prose, not only the file.

    The first version of this check inspected a file's last non-blank line and
    nothing else.  That would have missed the very defect it was written for had
    the severed section not happened to be last: Part 2's adversarial-training
    section ended mid-clause, and if another section had followed it the file's
    final line would have been fine and the check silent.

    So the unit is the *section*: for each heading, the last non-blank line
    before the next heading must end like finished prose, and a heading with no
    body at all is a defect wherever it sits.
    """
    result = CheckResult("truncation")
    for part in PARTS:
        for path in manuscript_files(part):
            text = path.read_text(encoding="utf-8", errors="replace")
            lines = text.splitlines()
            result.scanned += 1

            fenced: set[int] = set()
            in_fence = False
            for n, raw in enumerate(lines, 1):
                if raw.lstrip().startswith(("```", "~~~")):
                    in_fence = not in_fence
                    fenced.add(n)
                elif in_fence:
                    fenced.add(n)

            numbered = [(n, s) for n, s in enumerate(lines, 1) if s.strip()]
            if not numbered:
                result.problems.append(Problem(result.name, rel(path), 0, "file is empty"))
                continue

            # Split into blocks: a heading and everything up to the next one.
            heading_at = [i for i, (_, s) in enumerate(numbered) if re.match(r"^#{1,6}\s", s)]
            boundaries = heading_at + [len(numbered)]
            blocks: list[tuple[int, list[tuple[int, str]]]] = []
            if heading_at and heading_at[0] > 0:
                blocks.append((0, numbered[: heading_at[0]]))
            for index, start_index in enumerate(heading_at):
                blocks.append((start_index, numbered[start_index : boundaries[index + 1]]))
            if not heading_at:
                blocks.append((0, numbered))

            for start_index, block in blocks:
                if not block:
                    continue
                head_number, head_text = block[0]
                body = block[1:] if re.match(r"^#{1,6}\s", head_text) else block
                if re.match(r"^#{1,6}\s", head_text) and not body:
                    # A parent heading immediately followed by a deeper one is
                    # ordinary structure, not an empty section. Only a heading
                    # whose successor is at the same or a shallower level has
                    # genuinely nothing under it.
                    level = len(head_text) - len(head_text.lstrip("#"))
                    following = numbered[start_index + 1 :]
                    next_head = next(
                        (s for _, s in following if re.match(r"^#{1,6}\s", s)), None
                    )
                    if next_head is not None:
                        next_level = len(next_head) - len(next_head.lstrip("#"))
                        if next_level > level:
                            continue
                    result.problems.append(
                        Problem(
                            result.name,
                            rel(path),
                            head_number,
                            f"section {head_text.strip()!r} has no body",
                        )
                    )
                    continue
                if not body:
                    continue
                last_number, last_line = body[-1]
                stripped = last_line.strip()
                if _STRUCTURAL_END.match(last_line) or _SENTENCE_END.search(stripped):
                    continue
                # A line inside a fenced block is not prose and has no sentence
                # terminator to find.
                if last_number in fenced:
                    continue
                result.problems.append(
                    Problem(
                        result.name,
                        rel(path),
                        last_number,
                        f"section ends mid-sentence: {stripped[-72:]!r}. A severed clause "
                        f"ships into the rendered PDF and no per-part verifier catches it.",
                    )
                )

    if result.scanned == 0:
        result.problems.append(
            Problem(
                result.name,
                "scripts/check_series_integrity.py",
                0,
                "scanned zero manuscript files; the glob is broken",
            )
        )
    return result


# ---------------------------------------------------------------------------
# Check: math hygiene
# ---------------------------------------------------------------------------

#: ``\mathcal{T}*{i \to j}`` where ``_`` was meant: a literal star renders as a
#: binary operator instead of a subscript.
# The subscripted token may be a digit: ``\mathcal{D}*2`` for ``\mathcal{D}_2``
#: renders as a multiplication and was invisible while this required a letter.
_SUBSCRIPT_STAR = re.compile(r"[A-Za-z}]\*[{A-Za-z0-9]")

#: A doubled backslash before a command name: pandoc emits a line break followed
#: by literal text rather than the control sequence.
_DOUBLE_BACKSLASH_CMD = re.compile(r"\\\\[a-zA-Z]")

#: Starred commands that are legitimately spelled with a star.
_LEGIT_STARRED = (
    "vspace*{",
    "hspace*{",
    "DeclareMathOperator*{",
    "newtheorem*{",
    "section*{",
    "subsection*{",
)


def check_math_hygiene() -> CheckResult:
    """Sweep all three parts for LaTeX corruption that renders wrong but builds.

    Parts 1 and 3 each run this inside their own ``verify_manuscript.py``; Part 2
    has no math-hygiene gate at all, so the same corruption sits uncaught there.
    Running it from the series gate covers every part with one implementation
    instead of asking each to grow its own copy.
    """
    result = CheckResult("math-hygiene")
    for part in PARTS:
        for path in manuscript_files(part):
            result.scanned += 1
            for number, line in iter_lines(path):
                for match in _SUBSCRIPT_STAR.finditer(line):
                    context = line[max(0, match.start() - 24) : match.end()]
                    if any(token in context for token in _LEGIT_STARRED):
                        continue
                    result.problems.append(
                        Problem(
                            result.name,
                            rel(path),
                            number,
                            f"subscript-star corruption {match.group(0)!r}: replace "
                            f"'*' with '_' (a literal star renders as a binary "
                            f"operator, so the expression builds but means "
                            f"something else)",
                        )
                    )
                for match in _DOUBLE_BACKSLASH_CMD.finditer(line):
                    result.problems.append(
                        Problem(
                            result.name,
                            rel(path),
                            number,
                            f"double-escaped control sequence {match.group(0)!r}: "
                            f"use a single backslash inside math, or the renderer "
                            f"emits a line break followed by literal text",
                        )
                    )
    if result.scanned == 0:
        result.problems.append(
            Problem(
                result.name,
                "scripts/check_series_integrity.py",
                0,
                "scanned zero manuscript files; the glob is broken",
            )
        )
    return result



# ---------------------------------------------------------------------------
# Check: cited-artifact provenance
# ---------------------------------------------------------------------------

#: A manuscript reference to a shipped data artifact, e.g.
#: ``output/data/scalability_results.json``.
# Both citation forms appear: the full path, and a bare filename in prose
#: ("the scalability_results.json file"). Only matching the path form let a
#: bare-filename citation of an undeclared artifact through.
_CITED_ARTIFACT = re.compile(
    r"(?:output/data/|`)([A-Za-z0-9_]+(?:\.provenance)?\.json)"
)

#: ``data_origin`` values that mark a file as a *placeholder*. The paper draws
#: honest distinctions between measured, parametric and design-model results, so
#: the rule is not "must be measured" -- it is "must say which it is, and must
#: not be a DataGenerator stand-in".
_SYNTHETIC_ORIGINS = frozenset(
    {"synthetic", "generated", "placeholder", "datagenerator", "mock", "fake", "stub"}
)

#: Keys any of which counts as a provenance declaration.
_PROVENANCE_KEYS = ("data_origin", "source_script", "generator")

#: Structural artifacts that carry no measurements and therefore have nothing to
#: declare: a registry of figure labels, and the composer UI's module/preset
#: configuration. Listed explicitly so the exemption is reviewable rather than
#: inferred from shape.
_STRUCTURAL_ARTIFACTS = frozenset({"figure_registry.json", "composer_data.json"})


def check_artifact_provenance() -> CheckResult:
    """A manuscript may only cite artifacts that declare real provenance.

    ``src/data/generate.py`` states in its own module docstring that
    ``DataGenerator`` outputs "must NOT be used for manuscript figures or
    tables" -- they are schema-valid placeholders for visualization tests. That
    rule was unenforced, and Part 2's agent-scaling table was built from
    ``scalability_data.json`` (a placeholder with no provenance keys) while the
    real measurement sat unused in ``scalability_results.json``, overstating
    per-round latency by roughly 35x.

    The rule here is fail-safe in the honest direction: a cited artifact must
    positively declare a real ``data_origin``.  A missing declaration is a
    failure, not a pass, because that is exactly what the placeholder looks
    like.
    """
    result = CheckResult("artifact-provenance")
    for part in PARTS:
        for path in manuscript_files(part):
            for number, line in iter_lines(path):
                for match in _CITED_ARTIFACT.finditer(line):
                    name = match.group(1)
                    # A sentence warning readers *off* an artifact names it too.
                    # Requiring provenance of a file the prose is disclaiming
                    # inverts the check: the disclaimer is the honest act.
                    lowered = line.lower()
                    if any(
                        phrase in lowered
                        for phrase in (
                            "placeholder",
                            "not a source",
                            "must not",
                            "do not use",
                        )
                    ):
                        continue
                    result.scanned += 1
                    artifact = DATA_DIR / name
                    if not artifact.is_file():
                        result.problems.append(
                            Problem(
                                result.name,
                                rel(path),
                                number,
                                f"cites {name}, which does not exist under "
                                f"{rel(DATA_DIR)}",
                            )
                        )
                        continue
                    try:
                        payload = json.loads(artifact.read_text(encoding="utf-8"))
                    except json.JSONDecodeError as exc:
                        result.problems.append(
                            Problem(result.name, rel(path), number,
                                    f"cites {name}, which is not valid JSON: {exc}")
                        )
                        continue
                    if name in _STRUCTURAL_ARTIFACTS:
                        continue
                    # A list-shaped artifact carries provenance in a sidecar, but
                    # the sidecar has to say something: an empty file, or one
                    # that declares nothing, satisfied the old existence test.
                    sidecar = DATA_DIR / f"{artifact.stem}.provenance.json"
                    if sidecar.is_file():
                        try:
                            side = json.loads(sidecar.read_text(encoding="utf-8"))
                        except json.JSONDecodeError:
                            side = None
                        if isinstance(side, dict) and any(
                            side.get(key) for key in _PROVENANCE_KEYS
                        ):
                            continue
                        result.problems.append(
                            Problem(
                                result.name,
                                rel(path),
                                number,
                                f"cites {name}, whose sidecar {sidecar.name} declares no "
                                f"provenance ({' / '.join(_PROVENANCE_KEYS)}). An empty "
                                f"sidecar satisfied the file-exists test while saying "
                                f"nothing at all.",
                            )
                        )
                        continue
                    declared = None
                    if isinstance(payload, dict):
                        for key in _PROVENANCE_KEYS:
                            if payload.get(key):
                                declared = str(payload[key])
                                break
                    if declared is None:
                        result.problems.append(
                            Problem(
                                result.name,
                                rel(path),
                                number,
                                f"cites {name}, which declares no provenance "
                                f"({' / '.join(_PROVENANCE_KEYS)}). DataGenerator "
                                f"placeholders look exactly like this, so a missing "
                                f"declaration is a failure rather than a pass.",
                            )
                        )
                    elif declared.lower() in _SYNTHETIC_ORIGINS:
                        result.problems.append(
                            Problem(
                                result.name,
                                rel(path),
                                number,
                                f"cites {name}, which declares itself {declared!r}: "
                                f"a placeholder, not a result. src/data/generate.py "
                                f"states these must not back manuscript tables.",
                            )
                        )
    if result.scanned == 0:
        result.problems.append(
            Problem(
                result.name,
                "scripts/check_series_integrity.py",
                0,
                "no manuscript cites any output/data artifact; the pattern is broken",
            )
        )
    return result


# ---------------------------------------------------------------------------
# Check: cross-paper pointers
# ---------------------------------------------------------------------------

_HARDCODED_POINTER = re.compile(
    # The gap between "Part N" and the kind word was capped at 24 characters,
    # which let three pointers through in the form "Part 1's Runtime Defenses
    # section (Definition 5.6)" -- 28 characters of intervening prose. The check
    # reported PASS at zero while they were still there. [^.\n] already stops the
    # match at a sentence boundary, so a wider window costs nothing.
    r"(?:Part|Paper)[~ ]?([123])\b[^.\n]{0,60}?"
    r"\b(Theorem|Thm\.?|Definition|Def\.?|Lemma|Corollary|Section|Sec\.?)\s*"
    r"~?\s*(\d+(?:\.\d+)*[a-z]?)\b",
    re.IGNORECASE,
)


def check_cross_paper_pointers() -> CheckResult:
    result = CheckResult("cross-paper-pointers")
    for part in PARTS:
        for path in manuscript_files(part):
            for number, line in iter_lines(path):
                for match in _HARDCODED_POINTER.finditer(line):
                    target, kind, numeral = match.groups()
                    if target == part:
                        # A self-reference should use \cref, but that is the
                        # per-part verifier's business, not this gate's.
                        continue
                    result.scanned += 1
                    result.problems.append(
                        Problem(
                            result.name,
                            rel(path),
                            number,
                            f"hardcoded cross-paper pointer {match.group(0)!r}: "
                            f"{kind} numbers in Part {target} are assigned by the "
                            f"renderer and cannot be verified from Part {part}. "
                            f"Name the result instead (e.g. \"Part {target}'s "
                            f"Series Detection Rate theorem\").",
                        )
                    )
    return result


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

CHECKS: dict[str, Callable[[], CheckResult]] = {
    "shared-quantities": check_shared_quantities,
    "bibliography": check_bibliography,
    "truncation": check_truncation,
    "math-hygiene": check_math_hygiene,
    "artifact-provenance": check_artifact_provenance,
    "cross-paper-pointers": check_cross_paper_pointers,
}


def run(selected: Sequence[str]) -> list[CheckResult]:
    return [CHECKS[name]() for name in selected]


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--only",
        action="append",
        choices=sorted(CHECKS),
        help="run only this check (repeatable)",
    )
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(list(argv) if argv is not None else None)

    selected = args.only or sorted(CHECKS)
    results = run(selected)

    if args.json:
        print(
            json.dumps(
                {
                    r.name: {
                        "ok": r.ok,
                        "scanned": r.scanned,
                        "problems": [
                            {"path": p.path, "line": p.line, "message": p.message}
                            for p in r.problems
                        ],
                    }
                    for r in results
                },
                indent=2,
            )
        )
    else:
        for result in results:
            status = "PASS" if result.ok else f"FAIL ({len(result.problems)})"
            print(f"{result.name:<24} {status}   [{result.scanned} scanned]")
            if result.note:
                for line in result.note.splitlines():
                    print(f"  note: {line}")
            for problem in result.problems:
                print(problem.render())
        print("-" * 60)

    # In --json mode the summary goes to stderr so stdout stays parseable.
    stream = sys.stderr if args.json else sys.stdout
    failed = [r.name for r in results if not r.ok]
    if failed:
        print(f"series integrity: FAIL -- {', '.join(failed)}", file=stream)
        return 1
    print("series integrity: PASS", file=stream)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
