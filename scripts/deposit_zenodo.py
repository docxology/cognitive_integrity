#!/usr/bin/env python3
"""Deposit the three papers to Zenodo, in three separable and auditable steps.

Two of the three cover-page DOIs in this series resolved to nothing for as long
as the papers existed: 10.5281/zenodo.18364128 and .18364130 returned 404 from
Zenodo's API and from doi.org, and a search of Zenodo for the series returned
one record. Part 1 is deposited (record 18364119, concept 18364118); Parts 2 and
3 never were. This script mints the identifiers that the papers already print.

The steps are deliberately separate commands, because only the last is
irreversible:

    reserve   create a draft per part and reserve its DOI; write both
              publication.doi and paper.doi into that part's config.yaml
    upload    attach the rendered combined PDF to each draft
    publish   PUBLISH the drafts -- a published Zenodo record cannot be deleted

Between ``reserve`` and ``upload`` you must run::

    python3 scripts/propagate_dois.py     # carry the DOI into every file
    <re-render all three papers>          # so the cover carries the real DOI

because ``reserve`` writes the identifier into the config and nothing else, and
the PDF uploaded must be the one whose cover page shows the DOI it is deposited
under.

Every command defaults to a dry run. ``--execute`` performs it. ``publish``
additionally requires ``--confirm-irreversible``.

Needs PyYAML, which the project venvs do not carry; run it with an interpreter
that has it (the template checkout's venv does).

    <python-with-yaml> scripts/deposit_zenodo.py reserve
    <python-with-yaml> scripts/deposit_zenodo.py reserve --execute
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
API = "https://zenodo.org/api"

#: Each part, and the record it is a new version of (None means a first
#: deposition). Part 1's concept record is 18364118; a new version must be
#: created from its latest published record, 18364119.
PARTS: dict[str, int | None] = {
    "cogsec_multiagent_1_theory": 18364119,
    "cogsec_multiagent_2_computational": None,
    "cogsec_multiagent_3_practical": None,
}

CANONICAL_REPO_URL = "https://github.com/docxology/cognitive_integrity"

#: These papers have not been submitted anywhere or peer reviewed, so they are
#: deposited as preprints. Calling them articles would assert a status they do
#: not have, which is the class of claim this series has just finished removing.
PUBLICATION_TYPE = "preprint"

KEYWORDS = [
    "cognitive security",
    "multiagent systems",
    "AI safety",
    "prompt injection",
    "trust calculus",
    "defense in depth",
]


def _token() -> str:
    token = os.environ.get("ZENODO_PROD_TOKEN")
    if not token:
        env = Path.home() / "Documents" / "GitHub" / "template" / ".env"
        if env.is_file():
            for line in env.read_text(encoding="utf-8").splitlines():
                if line.startswith("ZENODO_PROD_TOKEN="):
                    token = line.split("=", 1)[1].strip().strip("'\"")
                    break
    if not token:
        raise SystemExit("ZENODO_PROD_TOKEN is not set and was not found in template/.env")
    return token


def _call(method: str, url: str, token: str, payload: dict | None = None,
          data: bytes | None = None, content_type: str | None = None) -> dict:
    body = data if data is not None else (json.dumps(payload).encode() if payload is not None else None)
    request = urllib.request.Request(url, data=body, method=method)
    request.add_header("Authorization", f"Bearer {token}")
    request.add_header("Content-Type", content_type or "application/json")
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            raw = response.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:600]
        raise SystemExit(f"{method} {url} failed: HTTP {exc.code}\n{detail}") from exc


def _config(part: str) -> dict:
    import yaml

    return yaml.safe_load((REPO / part / "manuscript" / "config.yaml").read_text(encoding="utf-8"))


def _metadata(part: str, others: dict[str, str]) -> dict:
    config = _config(part)
    paper = config["paper"]
    creators = [
        {
            "name": f"{a['name'].split()[-1]}, {' '.join(a['name'].split()[:-1])}",
            "affiliation": a.get("affiliation"),
            "orcid": a.get("orcid"),
        }
        for a in config["authors"]
    ]
    related = [{"identifier": CANONICAL_REPO_URL, "relation": "isSupplementedBy", "scheme": "url"}]
    for other, doi in sorted(others.items()):
        if other != part and doi:
            related.append({"identifier": doi, "relation": "isPartOf", "scheme": "doi"})
    title = paper["title"]
    if paper.get("subtitle"):
        title = f"{title} ({paper['subtitle']})"
    return {
        "title": title,
        "upload_type": "publication",
        "publication_type": PUBLICATION_TYPE,
        "description": _html_description(config),
        "creators": creators,
        "access_right": "open",
        "license": "cc-by-4.0",
        "version": str(paper.get("version", "2.0")),
        "publication_date": str(paper["date"]),
        "keywords": KEYWORDS,
        "related_identifiers": related,
    }


def _html_description(config: dict) -> str:
    """The abstract, as paragraphs. Zenodo renders the description as HTML."""
    text = str(config.get("abstract") or "").strip()
    if not text:
        raise SystemExit("config.yaml declares no abstract; the deposit would have no description")
    paragraphs = [p.strip().replace("\n", " ") for p in text.split("\n\n") if p.strip()]
    return "".join(f"<p>{p}</p>" for p in paragraphs)


def _write_doi(part: str, doi: str, execute: bool) -> None:
    """Set both publication.doi and paper.doi, which are different keys."""
    import re

    path = REPO / part / "manuscript" / "config.yaml"
    text = path.read_text(encoding="utf-8")
    updated = re.sub(
        r"^(publication:\n(?:[ \t]+.*\n|\n)*?[ \t]+doi:\s*)['\"]?10\.\d{4,9}/\S+?['\"]?$",
        lambda m: m.group(1) + doi,
        text,
        count=1,
        flags=re.M,
    )
    updated = re.sub(
        r"^(\s{2}doi:\s*)(['\"]?)10\.\d{4,9}/\S+?\2\s*$",
        lambda m: f"{m.group(1)}{m.group(2)}{doi}{m.group(2)}",
        updated,
        count=1,
        flags=re.M,
    )
    if updated == text:
        raise SystemExit(f"{path}: neither doi key was rewritten; refusing to continue")
    if execute:
        path.write_text(updated, encoding="utf-8")


def cmd_reserve(args) -> int:
    token = _token()
    state: dict[str, dict] = {}
    for part, parent in PARTS.items():
        if parent is None:
            print(f"  {part}: new deposition")
            if not args.execute:
                state[part] = {"deposition": None, "doi": "(reserved on --execute)"}
                continue
            draft = _call("POST", f"{API}/deposit/depositions", token, payload={"metadata": {}})
        else:
            print(f"  {part}: new version of record {parent}")
            if not args.execute:
                state[part] = {"deposition": None, "doi": "(reserved on --execute)"}
                continue
            action = _call("POST", f"{API}/deposit/depositions/{parent}/actions/newversion", token)
            draft_url = action["links"]["latest_draft"]
            draft = _call("GET", draft_url, token)
        doi = draft["metadata"].get("prereserve_doi", {}).get("doi") or draft.get("doi")
        if not doi:
            raise SystemExit(f"{part}: Zenodo returned no reserved DOI for draft {draft.get('id')}")
        state[part] = {"deposition": draft["id"], "doi": doi, "links": draft["links"]}
        print(f"      draft {draft['id']} -> {doi}")

    if args.execute:
        dois = {p: s["doi"] for p, s in state.items()}
        for part, entry in state.items():
            _call("PUT", f"{API}/deposit/depositions/{entry['deposition']}", token,
                  payload={"metadata": _metadata(part, dois)})
            _write_doi(part, entry["doi"], execute=True)
        _state_path().write_text(json.dumps(state, indent=2), encoding="utf-8")
        print(f"\nwrote {_state_path().relative_to(REPO)}")
        print("next: python3 scripts/propagate_dois.py, then re-render all three, then upload")
    else:
        print("\ndry run; nothing was created. Pass --execute to reserve.")
    return 0


def _state_path() -> Path:
    return REPO / ".zenodo-drafts.json"


def _load_state() -> dict:
    if not _state_path().is_file():
        raise SystemExit(f"{_state_path()} is missing; run `reserve --execute` first")
    return json.loads(_state_path().read_text(encoding="utf-8"))


def cmd_upload(args) -> int:
    token = _token()
    state = _load_state()
    for part, entry in state.items():
        pdf = REPO / part / "output" / "pdf" / f"{part}_combined.pdf"
        if not pdf.is_file():
            raise SystemExit(f"{pdf} is missing; render before uploading")
        cover = _cover_doi(pdf)
        if cover != entry["doi"]:
            raise SystemExit(
                f"{part}: the PDF's cover page says {cover or 'no DOI'} but this draft is "
                f"{entry['doi']}. Propagate and re-render before uploading."
            )
        print(f"  {part}: {pdf.stat().st_size / 1048576:.1f} MB, cover DOI matches")
        if args.execute:
            bucket = entry["links"]["bucket"]
            _call("PUT", f"{bucket}/{pdf.name}", token, data=pdf.read_bytes(),
                  content_type="application/octet-stream")
            print("      uploaded")
    if not args.execute:
        print("\ndry run; nothing was uploaded. Pass --execute to upload.")
    return 0


def _cover_doi(pdf: Path) -> str | None:
    """The DOI printed on page 1, so a draft cannot receive the wrong PDF."""
    import re
    import subprocess

    try:
        text = subprocess.run(
            ["pdftotext", "-f", "1", "-l", "1", str(pdf), "-"],
            capture_output=True, text=True, check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        raise SystemExit("pdftotext is required to verify the cover DOI before upload")
    found = re.search(r"10\.5281/zenodo\.\d+", text)
    return found.group(0) if found else None


def cmd_publish(args) -> int:
    token = _token()
    state = _load_state()
    if args.execute and not args.confirm_irreversible:
        raise SystemExit(
            "publish --execute also requires --confirm-irreversible: a published "
            "Zenodo record cannot be deleted, only superseded by a new version"
        )
    for part, entry in state.items():
        print(f"  {part}: draft {entry['deposition']} -> {entry['doi']}")
        if args.execute:
            result = _call("POST", entry["links"]["publish"], token)
            print(f"      published: {result.get('doi')}  {result.get('links', {}).get('html')}")
    if not args.execute:
        print("\ndry run; nothing was published. Pass --execute --confirm-irreversible.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name, handler in (("reserve", cmd_reserve), ("upload", cmd_upload), ("publish", cmd_publish)):
        p = sub.add_parser(name)
        p.add_argument("--execute", action="store_true", help="actually perform the step")
        if name == "publish":
            p.add_argument("--confirm-irreversible", action="store_true")
        p.set_defaults(handler=handler)
    args = parser.parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
