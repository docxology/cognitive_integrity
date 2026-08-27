"""Python examples printed in the manuscript must actually run.

S06's deployment example could not construct a firewall: it passed ``tau_1`` and
``tau_2`` to a ``FirewallConfig`` whose fields are ``injection_threshold`` and
``suspicious_threshold``, compared ``classify()``'s enum result against the
string ``"REJECT"`` (never equal, so the rejection branch was dead and the code
failed open), and called ``compute_trust`` and ``add_provisional`` with
signatures neither has. A reader following the deployment guide got a
``TypeError`` on the first statement.

Nothing checked it, because a fenced block in a markdown file is invisible to
both the test suite and the manuscript verifier. This module makes the examples
executable artifacts: every fenced ``python`` block that declares itself
runnable is compiled and executed against the shipped modules.

A block opts in by starting with the marker comment below. Blocks that are
deliberately partial -- a signature sketch, a snippet with an ellipsis -- simply
omit it, which keeps the opt-in honest rather than forcing fake scaffolding into
illustrative fragments.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

MANUSCRIPT = Path(__file__).parent.parent / "manuscript"
SRC = Path(__file__).parent.parent / "src"

#: A block carrying this first line is executed verbatim.
RUNNABLE_MARKER = "# Verified against the shipped API: this block runs as written."

_FENCE = re.compile(r"^```python\n(.*?)^```", re.MULTILINE | re.DOTALL)

#: The same opt-in for LaTeX listings. S09's "Complete working example" -- the
#: normative reference for composing defenses -- was written as an lstlisting
#: rather than a fence, so it was invisible to this module while importing two
#: mechanisms the pipeline cannot call and reading a DetectionEvent field that
#: does not exist. A reader following it got an AttributeError on the first run.
_LISTING = re.compile(
    r"^\\begin\{lstlisting\}\[language=Python\]\n(.*?)^\\end\{lstlisting\}",
    re.MULTILINE | re.DOTALL,
)


def _runnable_blocks() -> list[tuple[str, int, str]]:
    found: list[tuple[str, int, str]] = []
    for path in sorted(MANUSCRIPT.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for match in (*_FENCE.finditer(text), *_LISTING.finditer(text)):
            body = match.group(1)
            if body.lstrip().startswith(RUNNABLE_MARKER):
                line = text.count("\n", 0, match.start()) + 1
                found.append((path.name, line, body))
    return found


def test_at_least_one_example_is_marked_runnable() -> None:
    """Anti-vacuity: an opt-in nobody uses would make this module decorative."""
    blocks = _runnable_blocks()
    assert blocks, (
        "no manuscript code block is marked runnable; either the marker changed "
        f"or the opt-in was dropped. Marker: {RUNNABLE_MARKER!r}"
    )


def test_every_python_block_at_least_parses() -> None:
    """Even an illustrative block should be syntactically valid Python."""
    bad: list[str] = []
    for path in sorted(MANUSCRIPT.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for match in _FENCE.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            body = match.group(1)
            # Fragments legitimately use an ellipsis or a bare continuation.
            if "..." in body or body.strip().startswith("#"):
                continue
            try:
                compile(body, f"{path.name}:{line}", "exec")
            except SyntaxError as exc:
                bad.append(f"{path.name}:{line}: {exc}")
    assert not bad, "manuscript python blocks that do not parse:\n  " + "\n  ".join(bad)


@pytest.mark.parametrize(
    "name,line,body",
    [
        pytest.param(name, line, block, id=f"{name}:{line}")
        for name, line, block in _runnable_blocks()
    ],
)
def test_runnable_example_executes(name: str, line: int, body: str) -> None:
    """Execute the block against the real modules, in a fresh namespace."""
    if str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))
    namespace: dict[str, object] = {"__name__": "__manuscript_example__"}
    try:
        exec(compile(body, f"{name}:{line}", "exec"), namespace)  # noqa: S102
    except Exception as exc:  # noqa: BLE001 - report, never mask
        pytest.fail(
            f"{name}:{line} does not run against the shipped API: "
            f"{type(exc).__name__}: {exc}"
        )


def test_the_runner_would_catch_a_broken_example(tmp_path: Path) -> None:
    """A guard that cannot fire proves nothing; prove this one fires."""
    broken = (
        f"{RUNNABLE_MARKER}\n"
        "from core.firewall import FirewallConfig\n"
        "FirewallConfig(tau_1=0.7)\n"
    )
    if str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))
    with pytest.raises(TypeError):
        exec(compile(broken, "<planted>", "exec"), {"__name__": "<planted>"})  # noqa: S102
