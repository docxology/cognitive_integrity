"""LaTeX escaping for data-derived table cells.

Every table in this package interpolates strings that come from result
JSONs -- hypothesis names such as ``H2_detection``, group labels such as
``all_groups``, architecture names.  Those strings are *data*, not LaTeX,
and an unescaped ``_`` in text mode is a hard ``Missing $ inserted``
compile error, not a cosmetic issue: it takes the whole document down.
Before this helper existed, ``hypothesis_tests.tex`` and
``assumption_tests.tex`` both shipped uncompilable underscores.
"""

from __future__ import annotations

_REPLACEMENTS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
    # Not errors, but under the default OT1 encoding a text-mode "<" or ">"
    # typesets as an inverted exclamation / question mark, so a description
    # reading "CIF > baseline" would silently print as "CIF ¿ baseline".
    "<": r"\textless{}",
    ">": r"\textgreater{}",
}


def escape_latex(text: str) -> str:
    """Return *text* safe to interpolate into a LaTeX text-mode cell.

    Substitution is per input character, never a sequence of whole-string
    ``str.replace`` passes.  A sequential version cannot be made correct by
    reordering: escaping ``\\`` first emits ``\\textbackslash{}``, whose
    braces the later ``{``/``}`` passes then escape again, yielding
    ``\\textbackslash\\{\\}``.

    Examples
    --------
    >>> escape_latex("H2_detection")
    'H2\\\\_detection'
    >>> escape_latex("a\\\\b")
    'a\\\\textbackslash{}b'
    """
    return "".join(_REPLACEMENTS.get(ch, ch) for ch in str(text))


__all__ = ["escape_latex"]
