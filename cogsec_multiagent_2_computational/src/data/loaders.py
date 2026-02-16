"""Typed data loading utilities.

Provides convenience functions for loading JSON data files and coercing
them into the typed schema dataclasses.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from .schema import DetectionData, ScalabilityData


def load_json(path: str) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary.

    Parameters
    ----------
    path : str
        Path to the JSON file.

    Returns
    -------
    dict

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    json.JSONDecodeError
        If the file is not valid JSON.
    """
    p = Path(path)
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def load_detection_data(path: str) -> DetectionData:
    """Load detection data from a JSON file.

    Parameters
    ----------
    path : str
        Path to a JSON file produced by
        :meth:`DataGenerator.generate_detection_data`.

    Returns
    -------
    DetectionData
    """
    raw = load_json(path)
    return DetectionData.from_dict(raw)


def load_scalability_data(path: str) -> ScalabilityData:
    """Load scalability data from a JSON file.

    Parameters
    ----------
    path : str
        Path to a JSON file produced by
        :meth:`DataGenerator.generate_scalability_data`.

    Returns
    -------
    ScalabilityData
    """
    raw = load_json(path)
    return ScalabilityData.from_dict(raw)
