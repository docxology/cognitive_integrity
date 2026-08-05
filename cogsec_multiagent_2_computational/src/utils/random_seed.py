"""Reproducibility seed management.

Centralises random seed handling so that all modules draw from a single
``numpy.random.Generator``, making full experiments reproducible.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

_GLOBAL_SEED: int = 42
_GLOBAL_RNG: Optional[np.random.Generator] = None


def set_global_seed(seed: int = 42) -> np.random.Generator:
    """Set the global random seed and return a fresh Generator.

    All subsequent calls to :func:`get_rng` will derive from this seed.

    Args:
        seed: Integer seed value.

    Returns:
        A new ``numpy.random.Generator`` seeded with *seed*.
    """
    global _GLOBAL_SEED, _GLOBAL_RNG
    _GLOBAL_SEED = seed
    _GLOBAL_RNG = np.random.default_rng(seed)
    return _GLOBAL_RNG


def get_rng(seed: Optional[int] = None) -> np.random.Generator:
    """Return the global RNG, optionally re-seeded.

    If neither a global seed nor a local *seed* has been set, a default
    seed of 42 is used.

    Args:
        seed: If provided, reset the global RNG with this seed first.

    Returns:
        The global ``numpy.random.Generator``.
    """
    global _GLOBAL_RNG
    if seed is not None:
        # P2-F5: derive a fresh, independent stream instead of re-seeding the
        # shared global RNG.  Callers that pass a seed get deterministic,
        # call-order-independent draws and never perturb other consumers.
        return np.random.default_rng(seed)
    if _GLOBAL_RNG is None:
        _GLOBAL_RNG = np.random.default_rng(_GLOBAL_SEED)
    return _GLOBAL_RNG
