"""Review-bound publication identities and observed render input provenance.

Historical files are immutable reference artifacts. Cross-platform PNG encoders
and rasterizers need not reproduce their bytes or pixels. Fresh renders instead
retain their own strict determinism check and must use the reviewed source/input
snapshot; this module never writes or updates that authoritative snapshot.
"""

from __future__ import annotations

import hashlib
import os
import platform
import re
import sys
import zlib
from pathlib import Path
from typing import Any, Sequence


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RenderTrace:
    """Observe project JSON reads; record loaded project sources after rendering."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.active = True
        self.reads: set[Path] = set()
        sys.addaudithook(self._observe)

    def _observe(self, event: str, args: tuple[Any, ...]) -> None:
        if not self.active or event != "open":
            return
        file, mode, flags = args
        if not isinstance(file, (str, bytes, os.PathLike)):
            return
        if flags & (os.O_WRONLY | os.O_RDWR):
            return
        path = Path(os.fsdecode(file)).resolve()
        if path.is_relative_to(self.root / "output" / "data") and path.suffix == ".json":
            self.reads.add(path)

    def finish(self, figures: Sequence[str]) -> dict[str, Any]:
        """Stop observing and emit a non-authoritative record for this render."""
        self.active = False
        paths = set(self.reads)
        paths.update(self.root / name for name in (
            "scripts/generate_all_figures.py", "uv.lock", "pyproject.toml"
        ))
        for module in list(sys.modules.values()):
            file = getattr(module, "__file__", None)
            if file:
                path = Path(file).resolve()
                if path.is_relative_to(self.root / "src") and path.suffix == ".py":
                    paths.add(path)

        import matplotlib
        import numpy
        import PIL
        from matplotlib import font_manager, ft2font

        return {
            "schema_version": 1,
            "kind": "observed_render_inputs",
            "figures": list(figures),
            "inputs": {p.relative_to(self.root).as_posix(): _digest(p) for p in sorted(paths)},
            "renderer": {
                "python": platform.python_version(), "platform": platform.system(),
                "architecture": platform.machine(), "matplotlib": matplotlib.__version__,
                "numpy": numpy.__version__, "pillow": PIL.__version__,
                "freetype": ft2font.__freetype_version__, "zlib": zlib.ZLIB_RUNTIME_VERSION,
                "font_sha256": _digest(Path(font_manager.findfont("DejaVu Sans"))),
            },
        }


def snapshot_findings(
    root: Path, snapshot: dict[str, Any], observed: dict[str, Any]
) -> list[str]:
    """Reject changed historical artifacts, inputs, or the observed input roster."""
    findings: list[str] = []
    if snapshot.get("schema_version") != 1 or snapshot.get("kind") != "reviewed_render_snapshot":
        return ["invalid reviewed snapshot identity"]
    if observed.get("schema_version") != 1 or observed.get("kind") != "observed_render_inputs":
        return ["invalid observed render identity"]
    figures = observed.get("figures")
    if not isinstance(figures, list) or not figures or len(figures) != len(set(figures)):
        return ["missing or duplicate observed figure roster"]
    expected_artifacts = {
        f"output/figures/{name}.{ext}" for name in figures for ext in ("png", "pdf")
    }
    if set(snapshot.get("artifacts", {})) != expected_artifacts:
        findings.append("historical artifact roster differs from the observed generators")
    if observed.get("inputs") != snapshot.get("inputs"):
        findings.append("observed source/input fingerprints differ from the reviewed snapshot")

    for group in ("inputs", "artifacts"):
        entries = snapshot.get(group)
        if not isinstance(entries, dict) or not entries:
            findings.append(f"missing or empty {group}")
            continue
        for relative, digest in entries.items():
            if not isinstance(relative, str) or not isinstance(digest, str):
                findings.append(f"invalid {group} entry")
                continue
            path = Path(relative)
            allowed = (
                relative in ("uv.lock", "pyproject.toml", "scripts/generate_all_figures.py")
                or (relative.startswith("src/") and path.suffix == ".py")
                or (relative.startswith("output/data/") and path.suffix == ".json")
            ) if group == "inputs" else (
                relative.startswith("output/figures/") and path.suffix in (".png", ".pdf")
            )
            target = (root / path).resolve()
            if path.is_absolute() or ".." in path.parts or not allowed or not target.is_relative_to(
                root.resolve()
            ):
                findings.append(f"unsafe {group} path: {relative}")
            elif not re.fullmatch(r"[0-9a-f]{64}", digest):
                findings.append(f"invalid digest: {relative}")
            elif not target.is_file():
                findings.append(f"missing file: {relative}")
            elif _digest(target) != digest:
                findings.append(f"changed {group} file: {relative}")
    return findings
