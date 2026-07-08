#!/usr/bin/env python3
"""Generate Figure Registry
============================

Scans all manuscript/*.md files for {#fig:...} and {#tab:...} / {#tbl:...}
labels in document order (section file order) and writes a JSON registry with
auto-assigned sequential numbers.

Output: output/data/figure_registry.json

Usage:
    python scripts/generate_figure_registry.py [--root manuscript]
        [--output output/data/figure_registry.json]  # noqa: E501

Registry format:
    {
        "fig:cif-comprehensive": {
            "number": 1,
            "caption": "CIF Comprehensive Architecture",
            "section": "01_introduction",
            "label": "fig:cif-comprehensive",
            "type": "figure"
        },
        "tab:related-work-comparison": {
            "number": 1,
            "caption": "Related work comparison",
            "section": "01b_related_work",
            "label": "tab:related-work-comparison",
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
# Section ordering — matches the manuscript compile order
# --------------------------------------------------------------------------
SECTION_ORDER = [
    "00_abstract",
    "01_introduction",
    "01b_related_work",
    "01c_theoretical_connections",
    "02_methodology",
    "02a_defense_algorithms",
    "02b_configuration_parameters",
    "02c_composability_algebra",
    "03_attack_corpus",
    "03b_attack_examples",
    "03c_attack_ethics",
    "04_experimental_setup",
    "05_results",
    "05b_statistical_significance",
    "05c_sensitivity_analysis",
    "05d_ablation_and_scalability",
    "05e_bayesian_uncertainty",
    "05f_architecture_gap_analysis",
    "05g_adversarial_training",
    "05h_redteam_evaluation",
    "06_discussion",
    "07_conclusion",
    "08_category_theoretic_foundations",
    "99_references",
    "S01_notation_reference",
    "S02_detection_algorithms",
    "S03_benchmark_implementation",
    "S04_model_checking",
    "S05_framework_api",
    "S06_deployment_guide",
    "S07_algorithm_pseudocode",
    "S08_parametric_analysis",
    "S09_functional_api",
    "S10_information_geometry",
    "S11_adversarial_training_theory",
    "S12_composable_visualization",
]


def _section_sort_key(filename: str) -> int:
    """Return a sort index based on SECTION_ORDER; unrecognised files go last."""
    stem = Path(filename).stem
    try:
        return SECTION_ORDER.index(stem)
    except ValueError:
        # Alphabetical fallback for files not in the predefined order
        return len(SECTION_ORDER) + ord(stem[0]) if stem else 999


def extract_caption_from_markdown(content: str, label: str, label_type: str) -> str:
    """Try to extract a human-readable caption for a label.

    For figures: the alt-text of the markdown image that precedes the label.
    For tables: the text of the caption line immediately before the table.
    """
    if label_type == "figure":
        # Pattern: ![Caption text](path){#fig:label-with-optional-width}
        # Capture the first sentence (up to period or 80 chars)
        pattern = re.compile(
            r"!\[([^\]]+)\]\([^)]+\)\{#fig:" + re.escape(label.replace("fig:", "")) + r"[^}]*\}",
            re.DOTALL,
        )
        m = pattern.search(content)
        if m:
            raw = m.group(1).strip()
            # Return first sentence / first 100 chars
            sentence_end = raw.find(".")
            if 0 < sentence_end < 120:
                return raw[: sentence_end + 1]
            return raw[:120] + ("..." if len(raw) > 120 else "")
    else:
        # Table: look for **Table: ...** or caption line before {#tab:...}
        bare = label.replace("tab:", "").replace("tbl:", "")
        pattern = re.compile(
            r"\*\*(?:Table|Tab)[^*]*\*\*\s*\{#(?:tab|tbl):" + re.escape(bare) + r"[^}]*\}",
            re.IGNORECASE | re.DOTALL,
        )
        m = pattern.search(content)
        if m:
            raw = m.group(0)
            inner = re.sub(r"\{#[^}]+\}", "", raw).strip(" *")
            return inner[:120]
        # Fallback: prettify the label itself
    return label.replace("-", " ").replace("_", " ").title()


def scan_manuscript(manuscript_dir: Path) -> tuple[list, list]:
    """Scan all .md files and return (figures_list, tables_list) in document order."""
    md_files = [f for f in manuscript_dir.iterdir() if f.suffix == ".md"]
    md_files.sort(key=lambda f: _section_sort_key(f.name))

    figures = []  # list of dicts
    tables = []   # list of dicts
    seen_fig_labels: set[str] = set()
    seen_tab_labels: set[str] = set()

    for md_file in md_files:
        section = md_file.stem
        content = md_file.read_text(encoding="utf-8")

        # --- Figures ---
        # Match {#fig:LABEL} or {#fig:LABEL width=XX%}
        for m in re.finditer(r"\{#fig:([^}\s]+)", content):
            raw_label = m.group(1).rstrip()
            # Skip code-span placeholders like {#fig:...}
            if raw_label == "...":
                continue
            label = f"fig:{raw_label}"
            if label in seen_fig_labels:
                logger.warning("Duplicate figure label '%s' in %s (skipped)", label, section)
                continue
            seen_fig_labels.add(label)
            caption = extract_caption_from_markdown(content, label, "figure")
            figures.append({"label": label, "section": section, "caption": caption})

        # --- Tables (both #tbl: and #tab: prefixes) ---
        for prefix in ("tbl", "tab"):
            for m in re.finditer(r"\{#" + prefix + r":([^}\s]+)", content):
                raw_label = m.group(1).rstrip()
                # Skip code-span placeholders like {#tab:...}
                if raw_label == "...":
                    continue
                # Normalise to "tab:" prefix in registry
                canonical = f"tab:{raw_label}"
                if canonical in seen_tab_labels:
                    logger.warning(
                        "Duplicate table label '%s' in %s (skipped)", canonical, section
                    )
                    continue
                seen_tab_labels.add(canonical)
                caption = extract_caption_from_markdown(content, canonical, "table")
                tables.append({"label": canonical, "section": section, "caption": caption})

    return figures, tables


def build_registry(figures: list, tables: list) -> dict:
    """Assign sequential numbers and build the registry dict."""
    registry: dict[str, dict] = {}
    for i, fig in enumerate(figures, start=1):
        registry[fig["label"]] = {
            "number": i,
            "display": f"Fig. {i}",
            "caption": fig["caption"],
            "section": fig["section"],
            "label": fig["label"],
            "type": "figure",
        }
    for i, tab in enumerate(tables, start=1):
        registry[tab["label"]] = {
            "number": i,
            "display": f"Table {i}",
            "caption": tab["caption"],
            "section": tab["section"],
            "label": tab["label"],
            "type": "table",
        }
    return registry


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate figure/table registry JSON.")
    base_dir = Path(__file__).resolve().parent.parent
    parser.add_argument(
        "--root",
        default=str(base_dir / "manuscript"),
        help="Path to manuscript directory (default: <project>/manuscript)",
    )
    parser.add_argument(
        "--output",
        default=str(base_dir / "output" / "data" / "figure_registry.json"),
        help="Path to write registry JSON (default: output/data/figure_registry.json)",
    )
    args = parser.parse_args()

    manuscript_dir = Path(args.root)
    if not manuscript_dir.is_dir():
        logger.error("Manuscript directory not found: %s", manuscript_dir)
        return 1

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Scanning %s …", manuscript_dir)
    figures, tables = scan_manuscript(manuscript_dir)
    logger.info("Found %d figures, %d tables", len(figures), len(tables))

    registry = build_registry(figures, tables)

    output_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Registry written to %s", output_path)

    # Summary
    print("\n=== Figure Registry Summary ===")
    print(f"Figures: {len(figures)}")
    for fig in figures:
        key = fig['label']
        entry = registry[key]
        print(f"  {entry['display']:10s}  {key}  [{fig['section']}]")
    print(f"\nTables:  {len(tables)}")
    for tab in tables:
        key = tab['label']
        entry = registry[key]
        print(f"  {entry['display']:10s}  {key}  [{tab['section']}]")

    return 0


if __name__ == "__main__":
    sys.exit(main())
