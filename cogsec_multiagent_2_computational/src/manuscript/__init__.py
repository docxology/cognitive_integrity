"""Manuscript utilities for CIF Paper 2.

Provides manuscript verification and LaTeX table conversion functionality
used by thin orchestrator scripts.
"""

from .verifier import ManuscriptVerifier
from .latex_converter import convert_file, convert_latex_table_to_markdown

__all__ = [
    "ManuscriptVerifier",
    "convert_file",
    "convert_latex_table_to_markdown",
]
