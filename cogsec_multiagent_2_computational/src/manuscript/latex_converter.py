"""
LaTeX Table Converter Module
============================

Converts LaTeX table environments in markdown files to markdown pipe-style tables.
This enables proper rendering in both PDF (via pandoc) and HTML outputs.
Handles LaTeX tabular column specifications and properly extracts headers.
"""

from __future__ import annotations

import re
from pathlib import Path


def convert_latex_table_to_markdown(match: re.Match) -> str:
    """Convert a matched LaTeX table block to markdown format.

    Args:
        match: Regex match object containing the full LaTeX table environment.

    Returns:
        Markdown pipe-style table string, or original block if parsing fails.
    """
    full_block = match.group(0)

    # Extract caption
    caption_match = re.search(r'\\caption\{([^}]+)\}', full_block)
    caption = caption_match.group(1) if caption_match else ""

    # Extract label
    label_match = re.search(r'\\label\{([^}]+)\}', full_block)
    label = label_match.group(1) if label_match else ""

    # Extract the entire tabular block content
    tabular_match = re.search(
        r'\\begin\{tabular\}\{[^}]+\}(.*?)\\end\{tabular\}',
        full_block,
        re.DOTALL
    )
    if not tabular_match:
        return full_block  # Couldn't parse, return original

    tabular_content = tabular_match.group(1)

    # Remove rule commands
    tabular_content = re.sub(r'\\toprule\s*', '', tabular_content)
    tabular_content = re.sub(r'\\midrule\s*', '', tabular_content)
    tabular_content = re.sub(r'\\bottomrule\s*', '', tabular_content)

    # Split by \\ to get rows and clean them
    raw_rows = [r.strip() for r in tabular_content.split('\\\\') if r.strip()]

    rows = []
    for row_text in raw_rows:
        # Split by & to get cells
        cells = []
        for cell in row_text.split('&'):
            cell = cell.strip()
            # Convert \textbf{} to markdown bold
            cell = re.sub(r'\\textbf\{([^}]*)\}', r'**\1**', cell)
            # Convert \textit{} to markdown italic
            cell = re.sub(r'\\textit\{([^}]*)\}', r'*\1*', cell)
            # Remove @{} column specs that might leak into content
            cell = re.sub(r'@\{[^}]*\}', '', cell)
            cells.append(cell)

        # Skip empty rows
        if cells and any(c for c in cells):
            rows.append(cells)

    if len(rows) < 2:
        return full_block  # Need header + at least one data row

    # Determine column count from header
    num_cols = len(rows[0])

    # Build markdown table
    lines = []

    # Caption line
    if caption:
        label_attr = f" {{#{label}}}" if label else ""
        lines.append(f"**Table: {caption}**{label_attr}")
        lines.append("")

    # Header row
    header_row = rows[0]
    lines.append("| " + " | ".join(header_row) + " |")

    # Separator row
    lines.append("| " + " | ".join(["---"] * num_cols) + " |")

    # Data rows
    for row in rows[1:]:
        # Normalize row length
        while len(row) < num_cols:
            row.append("")
        lines.append("| " + " | ".join(row[:num_cols]) + " |")

    lines.append("")  # Blank line after table
    return "\n".join(lines)


def convert_file(filepath: Path) -> bool:
    """Convert all LaTeX tables in a file to markdown format.

    Args:
        filepath: Path to the markdown file to convert.

    Returns:
        True if any conversions were made, False otherwise.
    """
    content = filepath.read_text()
    original = content

    # Pattern to match entire table environments
    # Handles optional positioning [htbp] and \centering
    table_pattern = re.compile(
        r'\\begin\{table\}(?:\[[^\]]*\])?\s*'
        r'(?:\\centering\s*)?'
        r'.*?'
        r'\\end\{table\}',
        re.DOTALL
    )

    content = table_pattern.sub(convert_latex_table_to_markdown, content)

    # Also convert remaining \textbf{} to markdown bold
    content = re.sub(r'\\textbf\{([^}]*)\}', r'**\1**', content)

    if content != original:
        filepath.write_text(content)
        return True
    return False
