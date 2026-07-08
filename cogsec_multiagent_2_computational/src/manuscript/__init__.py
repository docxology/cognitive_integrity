"""Manuscript utilities for CIF Paper 2.
from __future__ import annotations


Provides manuscript verification and LaTeX table conversion functionality
used by thin orchestrator scripts.
"""

from .latex_converter import convert_file, convert_latex_table_to_markdown
from .verifier import ManuscriptVerifier

__all__ = [
    "ManuscriptVerifier",
    "convert_file",
    "convert_latex_table_to_markdown",
]
