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
# Ground truth derived from Part 2's shipped artifacts
# ---------------------------------------------------------------------------


class MissingArtifact(RuntimeError):
    """Raised when a derived quantity's backing artifact is absent."""


def _load(name: str) -> object:
    path = DATA_DIR / name
    if not path.is_file():
        raise MissingArtifact(f"{path.relative_to(REPO_ROOT)} is missing")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - corrupt artifact
        raise MissingArtifact(f"{path.name} is not valid JSON: {exc}") from exc


def _parametric_rows() -> list[dict]:
    rows = _load("full_evaluation_results.json")
    if not isinstance(rows, list) or not rows:
        raise MissingArtifact("full_evaluation_results.json holds no rows")
    return [r for r in rows if isinstance(r, dict)]


def parametric_ceiling_low() -> float:
    """Lowest single parametric detection rate, as a percentage."""
    return min(float(r["detection_rate"]) for r in _parametric_rows()) * 100.0


def parametric_ceiling_high() -> float:
    return max(float(r["detection_rate"]) for r in _parametric_rows()) * 100.0


def architecture_count() -> float:
    return float(len({str(r["architecture"]) for r in _parametric_rows()}))


def corpus_size() -> float:
    """Attacks per architecture in the parametric sweep."""
    per_arch: dict[str, int] = {}
    for row in _parametric_rows():
        arch = str(row["architecture"])
        per_arch[arch] = per_arch.get(arch, 0) + int(row["n_attacks"])
    sizes = set(per_arch.values())
    if len(sizes) != 1:
        raise MissingArtifact(f"architectures disagree on corpus size: {per_arch}")
    return float(sizes.pop())


def multiseed_mean() -> float:
    data = _load("multi_seed_results.json")
    if not isinstance(data, dict):
        raise MissingArtifact("multi_seed_results.json is not an object")
    for key in ("tpr_mean", "detection_rate_mean", "mean_detection_rate"):
        if key in data:
            return float(data[key]) * 100.0
    raise MissingArtifact("multi_seed_results.json has no mean detection-rate key")


# ---------------------------------------------------------------------------
# Shared-quantity table
# ---------------------------------------------------------------------------


#: How far either side of a match to look for the context keywords that decide
#: whether the match really is this quantity.
CONTEXT_WINDOW = 110


@dataclass(frozen=True)
class SharedQuantity:
    """A number that appears in more than one paper and must agree everywhere.

    Matching a bare numeric shape is not enough: a single sentence in Part 2's
    abstract carries the LLM arm's ``80--100%``, the colony arm's ``81--100%``
    and the parametric ceiling's ``96--100%``, all in the same shape.  So a
    match counts as this quantity only when, inside a window of
    :data:`CONTEXT_WINDOW` characters either side, at least one ``require``
    keyword is present and no ``exclude`` keyword is.  ``exclude`` is what
    keeps a neighbouring arm's identically-shaped range from being compared
    against this quantity's ground truth.
    """

    id: str
    pattern: re.Pattern[str]
    require: tuple[str, ...]
    deriver: Callable[[], float] | None
    tolerance: float
    unit: str
    exclude: tuple[str, ...] = ()
    parts: tuple[str, ...] = ("1", "2", "3")
    min_occurrences: int = 2
    note: str = ""

    def __post_init__(self) -> None:
        if self.pattern.groups != 1:
            raise ValueError(
                f"{self.id}: pattern needs exactly one capturing group, "
                f"has {self.pattern.groups}"
            )

    def in_scope(self, line: str, match: re.Match[str]) -> bool:
        start = max(0, match.start() - CONTEXT_WINDOW)
        window = line[start : match.end() + CONTEXT_WINDOW].lower()
        if any(token in window for token in self.exclude):
            return False
        return any(token in window for token in self.require)


WORD_NUMBERS = {
    "one": 1.0,
    "two": 2.0,
    "three": 3.0,
    "four": 4.0,
    "five": 5.0,
    "six": 6.0,
    "seven": 7.0,
    "eight": 8.0,
    "nine": 9.0,
    "ten": 10.0,
}


def _to_number(literal: str) -> float:
    text = literal.strip().replace(",", "").replace("{", "").replace("}", "")
    if text.lower() in WORD_NUMBERS:
        return WORD_NUMBERS[text.lower()]
    return float(text)


#: Evaluation arms whose ranges share the ``NN--100%`` shape with the
#: parametric ceiling and must never be compared against it.
_OTHER_ARMS = (
    "llm-backed",
    "llm validation",
    "llm-backed evaluation",
    "colony",
    "gemma",
    "hdi",
    "evaluation modes",
    "across evaluation",
    "variation across",
)

SHARED_QUANTITIES: tuple[SharedQuantity, ...] = (
    SharedQuantity(
        id="parametric_ceiling_low",
        pattern=re.compile(rf"(\d{{2}})\s*{DASH}\s*100\s*\\?%"),
        require=(
            "parametric",
            "design ceiling",
            "design-level",
            "coverage ceiling",
            "design target",
        ),
        exclude=_OTHER_ARMS,
        deriver=parametric_ceiling_low,
        tolerance=0.001,
        unit="percent",
        note=(
            "The low end of the parametric design ceiling. Derived as the minimum "
            "per-cell detection rate in full_evaluation_results.json."
        ),
    ),
    SharedQuantity(
        id="parametric_ceiling_high",
        pattern=re.compile(rf"\d{{2}}\s*{DASH}\s*(100)\s*\\?%"),
        require=(
            "parametric",
            "design ceiling",
            "design-level",
            "coverage ceiling",
            "design target",
        ),
        exclude=_OTHER_ARMS,
        deriver=parametric_ceiling_high,
        tolerance=0.001,
        unit="percent",
    ),
    SharedQuantity(
        id="parametric_ceiling_low_bare",
        # A bare "96\\%" used as the ceiling, e.g. "96\\% as the achievable
        # ceiling" or "the simulation's 96--100\\% design-level ceiling". The
        # range-shaped pattern above misses this form entirely, which is how a
        # stale 94 survived a sweep of every NN--100 occurrence.
        # Not preceded by a digit or dash (so the "00" inside "100" and the
        # high end of "96--100" are both excluded), and not itself the low end
        # of a range (which the range-shaped quantity above already gates).
        pattern=re.compile(r"(?<![\d\-–—])(\d{2})\s*\\?%(?!\s*(?:--|–|—)\s*\d)"),
        require=("design-level ceiling", "achievable ceiling", "design ceiling"),
        exclude=_OTHER_ARMS,
        deriver=parametric_ceiling_low,
        tolerance=0.001,
        unit="percent",
        min_occurrences=1,
        note="A ceiling quoted as a single number rather than a range.",
    ),
    SharedQuantity(
        id="attack_corpus_size",
        pattern=re.compile(rf"(\d{{3}})\s*{DASH}?\s*attack\b(?=[- ]?(?:corpus|set)\b)"),
        require=("corpus", "set"),
        # The 98-attack ablation subsample is a different denominator.
        exclude=("ablation",),
        deriver=corpus_size,
        tolerance=0.001,
        unit="count",
        note="Corpus size per architecture, from AttackCorpus.generate(seed=42).",
    ),
    SharedQuantity(
        id="architecture_count",
        pattern=re.compile(
            r"\b(four|five|six|seven|eight|\d+)\s+production\s+multiagent\s+"
            r"(?:architectures|systems|topologies)"
        ),
        require=("production",),
        deriver=architecture_count,
        tolerance=0.001,
        unit="count",
        note="Number of distinct architectures in the parametric sweep.",
    ),
    SharedQuantity(
        id="multiseed_mean",
        pattern=re.compile(
            r"mean(?:\s+detection\s+rate)?\s+of\s+\*{0,2}(\d{2}\.\d)\s*\\?%"
        ),
        require=("seed",),
        deriver=multiseed_mean,
        tolerance=0.06,
        unit="percent",
        note="30-seed pipeline mean detection rate, from multi_seed_results.json.",
    ),
)


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
        try:
            derived = quantity.deriver() if quantity.deriver else None
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
                    for match in quantity.pattern.finditer(line):
                        if not quantity.in_scope(line, match):
                            continue
                        try:
                            value = _to_number(match.group(1))
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
                        + (f" ({quantity.note})" if quantity.note else ""),
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


def check_bibliography() -> CheckResult:
    result = CheckResult("bibliography")
    by_title: dict[str, list[tuple[str, Path, BibEntry]]] = {}
    total = 0

    for part in PARTS:
        path = manuscript_dir(part) / "references.bib"
        if not path.is_file():
            result.problems.append(
                Problem(result.name, rel(path), 0, "bibliography file is missing")
            )
            continue
        entries = parse_bib(path)
        total += len(entries)
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

    # The same work must not disagree about itself across the three papers.
    for title_key, sightings in by_title.items():
        if len({part for part, _, _ in sightings}) < 2:
            continue
        for attribute, normaliser in (
            ("year", lambda value: value.strip()),
            ("title", normalise_title),
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
    return result


# ---------------------------------------------------------------------------
# Check: truncation
# ---------------------------------------------------------------------------

#: A line that legitimately ends a file without sentence punctuation.
_STRUCTURAL_END = re.compile(
    r"^\s*(?:[-*+]\s|\d+\.\s|\||#{1,6}\s|```|~~~|\$\$|:::|<!--|>\s*$"
    r"|\\(?:end\{|newpage|clearpage|pagebreak|vfill|hrulefill))"
)
#: Trailing emphasis/quote markers that may follow the terminator: a sentence
#: closing an italic run ends ``...benchmarks.*``, which is complete prose.
_SENTENCE_END = re.compile(r"[.!?:;)}\]\"'”’][*_`\"'”’)\]]*\s*$|\\\\\s*$|-{3,}\s*$")


def check_truncation() -> CheckResult:
    result = CheckResult("truncation")
    for part in PARTS:
        for path in manuscript_files(part):
            lines = [
                line
                for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
            ]
            result.scanned += 1
            trailing = [(n, s) for n, s in enumerate(lines, 1) if s.strip()]
            if not trailing:
                result.problems.append(
                    Problem(result.name, rel(path), 0, "file is empty")
                )
                continue

            last_number, last_line = trailing[-1]
            stripped = last_line.strip()
            if not (_STRUCTURAL_END.match(last_line) or _SENTENCE_END.search(stripped)):
                result.problems.append(
                    Problem(
                        result.name,
                        rel(path),
                        last_number,
                        "file ends mid-sentence: "
                        f"{stripped[-72:]!r}. A severed clause ships into the "
                        "rendered PDF and no per-part verifier catches it.",
                    )
                )

            # A heading whose section body never arrives.
            for index, (number, line) in enumerate(trailing):
                if not re.match(r"^#{1,6}\s", line):
                    continue
                rest = trailing[index + 1 :]
                if not rest:
                    result.problems.append(
                        Problem(
                            result.name,
                            rel(path),
                            number,
                            f"section {line.strip()!r} has no body -- the heading "
                            "is the last content in the file",
                        )
                    )
                    break
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
_SUBSCRIPT_STAR = re.compile(r"[A-Za-z}]\*[{A-Za-z]")

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
_CITED_ARTIFACT = re.compile(r"output/data/([A-Za-z0-9_]+\.json)")

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
                    # A list-shaped artifact carries provenance in a sidecar.
                    if (DATA_DIR / f"{artifact.stem}.provenance.json").is_file():
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
    r"(?:Part|Paper)[~ ]?([123])\b[^.\n]{0,24}?"
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
