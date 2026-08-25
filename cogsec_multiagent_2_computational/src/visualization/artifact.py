"""One way to read a measurement into a figure, and one way to refuse.

Every figure in this package that reports a measured quantity needs the same
three things: the path to its artifact, a loud failure when it is absent, and a
line on the rendered page saying which artifact and which script produced it.
Written once per figure, those three things drift: one module falls back to a
plausible default, another forgets to say where its numbers came from, and the
reader cannot tell the difference on the page.

They are written once here instead.

The failure mode this exists to prevent
---------------------------------------
A figure that silently substitutes defaults when its artifact is missing looks
identical, on the rendered page, to one drawn from a measurement. That is the
defect that put a hardcoded matrix into a published panel and an invented
optimum onto a sensitivity surface. :func:`load_artifact` has no fallback and
never will; a caller that wants one has to write it, visibly, at the call site.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from matplotlib.figure import Figure

__all__ = ["DATA_DIR", "load_artifact", "provenance_line", "annotate_provenance"]

#: Where the shipped measurements live.
DATA_DIR = Path(__file__).resolve().parents[2] / "output" / "data"


def load_artifact(name: str, *, required: tuple[str, ...] = ()) -> dict[str, Any]:
    """Read ``output/data/<name>`` or raise, naming the script that writes it.

    Parameters
    ----------
    name:
        File name, with or without the ``.json`` suffix.
    required:
        Top-level keys the caller depends on. Checked here so a figure fails
        at load with a message naming the key, rather than three frames later
        on a ``KeyError`` that says only what was missing and not from where.
    """
    path = DATA_DIR / (name if name.endswith(".json") else f"{name}.json")
    if not path.is_file():
        raise FileNotFoundError(
            f"{path} is missing. This figure reports a measured quantity and "
            f"has no stand-in values; run the script named in the artifact's "
            f"provenance block to produce it."
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"{path.name} is not an object; got {type(payload).__name__}")
    missing = [key for key in required if key not in payload]
    if missing:
        raise KeyError(
            f"{path.name} carries no {missing}; the artifact and the figure "
            f"that reads it have diverged"
        )
    return payload


def provenance_line(payload: dict[str, Any], name: str) -> str:
    """A one-line statement of where a figure's numbers came from.

    Includes the origin verbatim rather than paraphrasing it: a reader needs
    to know whether ``parametric_simulation`` or ``real_pipeline`` produced
    what they are looking at, and no arrangement of colours conveys that.
    """
    origin = payload.get("data_origin", "origin not recorded")
    script = payload.get("source_script", "producing script not recorded")
    seed = payload.get("seed")
    suffix = f", seed {seed}" if seed is not None else ""
    return f"Source: {name} ({origin}{suffix}) — {script}"


def annotate_provenance(fig: Figure, payload: dict[str, Any], name: str) -> None:
    """Write the provenance line along the bottom of *fig*."""
    fig.text(
        0.5,
        0.005,
        provenance_line(payload, name),
        ha="center",
        va="bottom",
        fontsize=6.5,
        color="#5A6472",
        style="italic",
    )
