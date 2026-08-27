#!/usr/bin/env python3
"""Every DOI the series prints must be real, and every part must point at one repo.

Two of the three papers shipped a cover-page DOI that did not exist. Both
returned 404 from Zenodo's API and from doi.org, and between them they appeared
148 times across 43 tracked files -- on covers, in abstracts, in cross-part
signposts, in BibTeX entries a reader would paste into their own bibliography.
Nothing checked, because nothing had been written to check it: the ledger gates
quantities, the claim registry gates Part 2's prose, and neither has an opinion
about an identifier.

This checks identity rather than measurement:

  * each part's ``manuscript/config.yaml`` is the authority for that part's DOI;
  * every series DOI appearing anywhere in tracked files is one of those, so a
    retired or invented identifier cannot survive in a corner of the tree;
  * each part signposts the same repository URL, and every part signposts it;
  * with ``--network``, every registered DOI resolves.

The resolution check is opt-in because an offline run must not manufacture a
failure, and a network error is not a 404: only an explicit 404 from Zenodo is
read as "this identifier does not exist".

    python3 scripts/check_publication_identity.py [--network]
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

#: The one repository the whole series points a reader at.
CANONICAL_REPO_URL = "https://github.com/docxology/cognitive_integrity"

#: Zenodo DOIs that belong to works outside this series and are cited normally.
EXTERNAL_ZENODO: frozenset[str] = frozenset({"10.5281/zenodo.5759807"})

_ZENODO = re.compile(r"10\.5281/zenodo\.\d+")
_CONFIG_DOI = re.compile(r"^\s{2}doi:\s*['\"]?(10\.\d{4,9}/[^'\"\s]+)['\"]?", re.M)
_CONFIG_CONCEPT = re.compile(r"^\s{2}concept_doi:\s*['\"]?(10\.\d{4,9}/[^'\"\s]+)['\"]?", re.M)
#: The release tooling writes ``publication.doi``; the cover page reads
#: ``paper.doi``. They are different keys in the same file, and nothing kept
#: them in step, so a reserved DOI could land in the config without reaching
#: the cover of the paper it identifies.
_PUBLICATION_DOI = re.compile(
    r"^publication:\n(?:[ \t]+.*\n|\n)*?[ \t]+doi:\s*['\"]?(10\.\d{4,9}/[^'\"\s]+)['\"]?",
    re.M,
)

#: Below these counts the patterns are broken rather than the tree clean, and a
#: check that scans nothing must fail rather than pass.
MIN_DOI_OCCURRENCES = 20
MIN_URL_FILES_PER_PART = 1


def _tracked(*patterns: str) -> list[Path]:
    args = ["git", "-C", str(REPO), "ls-files", "-z", *patterns]
    out = subprocess.run(args, capture_output=True, text=True, check=True).stdout
    return [REPO / name for name in out.split("\0") if name]


def _text_files() -> list[Path]:
    keep = (".md", ".yaml", ".yml", ".cff", ".bib", ".py", ".toml", ".txt", ".json")
    return [p for p in _tracked() if p.suffix in keep and p.is_file()]


def registered_dois() -> dict[str, dict[str, str]]:
    """Each part's own DOIs, read from the config the renderer reads."""
    registry: dict[str, dict[str, str]] = {}
    for part in PARTS:
        config = REPO / part / "manuscript" / "config.yaml"
        if not config.is_file():
            raise SystemExit(f"{config} is missing; the registry cannot be built")
        text = config.read_text(encoding="utf-8")
        entry: dict[str, str] = {}
        version = _CONFIG_DOI.search(text)
        if version:
            entry["version"] = version.group(1)
        concept = _CONFIG_CONCEPT.search(text)
        if concept:
            entry["concept"] = concept.group(1)
        publication = _PUBLICATION_DOI.search(text)
        if publication:
            entry["publication"] = publication.group(1)
        registry[part] = entry
    return registry


def _resolves(doi: str) -> tuple[bool, str]:
    """True when Zenodo serves the record; False only on an explicit 404."""
    import json
    import urllib.error
    import urllib.request

    record = doi.rsplit(".", 1)[-1]
    url = f"https://zenodo.org/api/records/{record}"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            payload = json.load(response)
        title = payload.get("metadata", {}).get("title", "")
        return True, f"HTTP 200 ({title[:60]})"
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return False, "HTTP 404 -- no such record"
        return True, f"HTTP {exc.code} (not a 404, so not read as absent)"
    except Exception as exc:  # noqa: BLE001 - a network error is not a 404
        return True, f"unreachable ({type(exc).__name__}), not read as absent"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--network",
        action="store_true",
        help="also require every registered DOI to resolve at Zenodo",
    )
    args = parser.parse_args(argv)

    problems: list[str] = []
    registry = registered_dois()

    known: set[str] = set(EXTERNAL_ZENODO)
    for part, entry in registry.items():
        if "version" not in entry:
            problems.append(f"{part}: manuscript/config.yaml declares no paper.doi")
        if "publication" not in entry:
            problems.append(f"{part}: manuscript/config.yaml declares no publication.doi")
        elif entry.get("version") and entry["publication"] != entry["version"]:
            problems.append(
                f"{part}: paper.doi is {entry['version']} but publication.doi is "
                f"{entry['publication']}; the release tooling writes the second "
                f"and the cover page prints the first"
            )
        known.update(entry.values())

    version_dois = [e["version"] for e in registry.values() if "version" in e]
    if len(set(version_dois)) != len(version_dois):
        problems.append(
            f"two parts share a version DOI: {sorted(version_dois)}; each paper "
            f"is a separate work and needs its own"
        )

    files = _text_files()
    occurrences = 0
    stray: dict[str, list[str]] = {}
    url_files: dict[str, int] = {part: 0 for part in PARTS}
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(REPO).as_posix()
        for doi in _ZENODO.findall(text):
            occurrences += 1
            if doi not in known:
                stray.setdefault(doi, []).append(rel)
        if CANONICAL_REPO_URL in text:
            for part in PARTS:
                if rel.startswith(f"{part}/"):
                    url_files[part] += 1

    for doi, where in sorted(stray.items()):
        problems.append(
            f"{doi} is printed in {len(where)} file(s) but is not any part's "
            f"registered DOI (first: {where[0]})"
        )

    if occurrences < MIN_DOI_OCCURRENCES:
        print(
            f"only {occurrences} Zenodo DOI occurrences found across "
            f"{len(files)} tracked files; the pattern is broken, which would "
            f"make this check pass without checking anything",
            file=sys.stderr,
        )
        return 2

    for part, count in url_files.items():
        if count < MIN_URL_FILES_PER_PART:
            problems.append(
                f"{part} never signposts {CANONICAL_REPO_URL}; a reader of that "
                f"paper alone cannot find the code"
            )

    other_repos: dict[str, list[str]] = {}
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for url in re.findall(r"https://github\.com/docxology/[A-Za-z0-9_.-]+", text):
            # A trailing "." is sentence punctuation and ".git" is the clone
            # URL; neither is a different repository.
            url = url.rstrip(".")
            if url.endswith(".git"):
                url = url[: -len(".git")]
            if url not in (CANONICAL_REPO_URL, "https://github.com/docxology/template"):
                other_repos.setdefault(url, []).append(path.relative_to(REPO).as_posix())
    for url, where in sorted(other_repos.items()):
        problems.append(f"{url} is signposted in {where[0]}; the series has one repository")

    checked_network = 0
    if args.network:
        for doi in sorted({d for e in registry.values() for d in e.values()}):
            ok, detail = _resolves(doi)
            checked_network += 1
            print(f"  {doi}: {detail}")
            if not ok:
                problems.append(f"{doi} does not resolve: {detail}")

    print(
        f"publication identity: {occurrences} DOI occurrence(s) across "
        f"{len(files)} tracked files, {len(known)} registered identifier(s), "
        f"{sum(url_files.values())} file(s) signposting the repository"
        + (f", {checked_network} resolved" if args.network else "")
    )
    for problem in problems:
        print(f"  {problem}")
    if problems:
        print(f"{len(problems)} publication-identity problem(s)")
        return 1
    print("every printed DOI is registered and every part signposts one repository")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
