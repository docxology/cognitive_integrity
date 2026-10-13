"""Collection inventory must never accept a successful subset of a broken suite."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "inventory_collector", Path(__file__).resolve().parents[1]
    / "scripts" / "collect_test_inventory.py",
)
assert _SPEC is not None and _SPEC.loader is not None
collector = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(collector)


def test_partial_collection_is_refused_even_with_one_valid_test(tmp_path: Path) -> None:
    # Run actual pytest processes, including an inherited quiet setting that
    # would otherwise hide the summary the inventory parses.
    (tmp_path / "pyproject.toml").write_text(
        '[tool.pytest.ini_options]\naddopts = "-qq"\n', encoding="utf-8"
    )
    suite = tmp_path / "tests"
    suite.mkdir()
    (suite / "test_valid.py").write_text(
        "def test_valid():\n    assert True\n", encoding="utf-8"
    )
    interpreter = Path(sys.executable)
    assert collector.collect(tmp_path, suite, interpreter) == 1

    (suite / "test_import_error.py").write_text(
        "import intentionally_missing_cif_inventory_fixture_module\n", encoding="utf-8"
    )
    with pytest.raises(collector.CollectionFailed, match="refusing a partial inventory"):
        collector.collect(tmp_path, suite, interpreter)
