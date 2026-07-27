#!/usr/bin/env python3
"""Generate Figure Registry for Part 1 (Theory)
==================================================

Scans all manuscript/*.md files for {#fig:...} and {#tab:...} labels
(pandoc-crossref style) as well as \\label{fig:...} and \\label{tab:...}
(LaTeX style) in document order and writes a JSON registry with
auto-assigned sequential numbers.

Output: output/data/figure_registry.json

Usage:
    python scripts/generate_figure_registry.py \
        [--root manuscript] [--output output/data/figure_registry.json]

Registry format:
    {
        "fig:trust-network": {
            "number": 1,
            "caption": "Trust Network Topology",
            "section": "04_formal_framework",
            "label": "fig:trust-network",
            "type": "figure"
        },
        "tab:adversary-classes": {
            "number": 1,
            "caption": "Five-tier adversary hierarchy",
            "section": "03_threat_model",
            "label": "tab:adversary-classes",
            "type": "table"
        },
        ...
    }
"""

import argparse
import json
import logging
import re
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# Section ordering — matches the Part 1 manuscript compile order
# --------------------------------------------------------------------------
SECTION_ORDER = [
    "00_quote",
    "01_abstract",
    "02_introduction",
    "03_threat_model",
    "04_formal_framework",
    "05_defense_mechanisms",
    "06_detection_methods",
    "07_formal_verification",
    "08_discussion",
    "09_conclusion",
    "10_limitations",
    "99_references",
    "S01_proofs",
    "S02_eusocial_cogsec",
    "S03_notation",
]


# --------------------------------------------------------------------------
# Regex patterns
# --------------------------------------------------------------------------
# Pandoc-crossref style: {#fig:label} or {#tab:label}
PANDOC_FIG_RE = re.compile(r"\{#(fig:[a-zA-Z0-9_:.-]+)\}")
PANDOC_TAB_RE = re.compile(r"\{#(tab:[a-zA-Z0-9_:.-]+)\}")

# LaTeX style: \label{fig:label} or \label{tab:label}
LATEX_FIG_RE = re.compile(r"\\label\{(fig:[a-zA-Z0-9_:.-]+)\}")
LATEX_TAB_RE = re.compile(r"\\label\{(tab:[a-zA-Z0-9_:.-]+)\}")

# Caption extraction for LaTeX figures: \caption{...}
LATEX_CAPTION_RE = re.compile(r"\\caption\{([^}]+)\}")

# Caption extraction for pandoc figures: ![caption text](...)
PANDOC_IMG_CAPTION_RE = re.compile(r"!\[([^\]]+)\]\([^)]+\)\{#(?:fig|tab):[^}]+\}")

# LaTeX table caption: \caption{...} before \label{tab:...}
LATEX_TAB_CAPTION_RE = re.compile(r"\\caption\{([^}]+)\}")


def extract_caption_near_label(lines: list[str], label_line_idx: int, window: int = 10) -> str:
    """Search within ±window lines of a label for a caption."""
    start = max(0, label_line_idx - window)
    end = min(len(lines), label_line_idx + window + 1)
    for line in lines[start:end]:
        m = LATEX_CAPTION_RE.search(line)
        if m:
            return m.group(1).strip()
    return ""


def scan_file(md_path: Path) -> list[dict]:
    """Return list of {label, type, caption, line_no} dicts in order found."""
    text = md_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    entries = []

    for idx, line in enumerate(lines):
        # Pandoc-crossref figures
        for m in PANDOC_FIG_RE.finditer(line):
            label = m.group(1)
            # Caption: look at beginning of the same line (markdown image syntax)
            cap_m = PANDOC_IMG_CAPTION_RE.search(line)
            caption = cap_m.group(1).strip() if cap_m else ""
            entries.append(
                {
                    "label": label,
                    "type": "figure",
                    "caption": caption,
                    "line_no": idx + 1,
                }
            )

        # Pandoc-crossref tables
        for m in PANDOC_TAB_RE.finditer(line):
            label = m.group(1)
            caption = ""
            entries.append(
                {
                    "label": label,
                    "type": "table",
                    "caption": caption,
                    "line_no": idx + 1,
                }
            )

        # LaTeX figures
        for m in LATEX_FIG_RE.finditer(line):
            label = m.group(1)
            caption = extract_caption_near_label(lines, idx)
            entries.append(
                {
                    "label": label,
                    "type": "figure",
                    "caption": caption,
                    "line_no": idx + 1,
                }
            )

        # LaTeX tables
        for m in LATEX_TAB_RE.finditer(line):
            label = m.group(1)
            caption = extract_caption_near_label(lines, idx)
            entries.append(
                {
                    "label": label,
                    "type": "table",
                    "caption": caption,
                    "line_no": idx + 1,
                }
            )

    return entries


def build_registry(root: Path) -> dict:
    """Scan all section files in order and build the registry."""
    registry: dict[str, dict] = {}
    fig_counter = 0
    tab_counter = 0
    seen_labels: set[str] = set()

    for section_stem in SECTION_ORDER:
        md_path = root / f"{section_stem}.md"
        if not md_path.exists():
            logger.debug("Section file not found, skipping: %s", md_path)
            continue

        entries = scan_file(md_path)
        for entry in entries:
            label = entry["label"]
            if label in seen_labels:
                logger.warning(
                    "Duplicate label %s in %s (line %d) — skipping",
                    label,
                    md_path.name,
                    entry["line_no"],
                )
                continue
            seen_labels.add(label)

            if entry["type"] == "figure":
                fig_counter += 1
                number = fig_counter
            else:
                tab_counter += 1
                number = tab_counter

            registry[label] = {
                "number": number,
                "caption": entry["caption"],
                "section": section_stem,
                "label": label,
                "type": entry["type"],
                "line_no": entry["line_no"],
            }
            logger.info(
                "  %-40s  %s %d  (line %d)", label, entry["type"].upper(), number, entry["line_no"]
            )

    return registry


def main() -> int:
    base_dir = Path(__file__).resolve().parent.parent

    parser = argparse.ArgumentParser(
        description="Generate figure/table registry for Part 1 manuscript"
    )
    parser.add_argument(
        "--root", default=str(base_dir / "manuscript"), help="Path to manuscript/ directory"
    )
    parser.add_argument(
        "--output",
        default=str(base_dir / "output" / "data" / "figure_registry.json"),
        help="Output JSON path",
    )
    args = parser.parse_args()

    root = Path(args.root)
    if not root.is_dir():
        logger.error("Manuscript directory not found: %s", root)
        return 1

    logger.info("Scanning %s ...", root)
    registry = build_registry(root)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8")

    figures = sum(1 for v in registry.values() if v["type"] == "figure")
    tables = sum(1 for v in registry.values() if v["type"] == "table")
    logger.info("Registry written: %s  (%d figures, %d tables)", out_path, figures, tables)
    return 0


if __name__ == "__main__":
    sys.exit(main())
