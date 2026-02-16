"""Framework configuration and tuning profiles.

Provides a central ``FrameworkConfig`` that collects sub-module configs
and offers YAML/dict-based loading for reproducible experiments.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class FrameworkConfig:
    """Top-level configuration for the Cognitive Security Framework.

    Collects tuning parameters across all defense modules into a single
    object that can be serialised to / deserialised from a dictionary.

    Attributes:
        injection_threshold: Firewall injection detection threshold.
        suspicious_threshold: Firewall suspicious-pattern threshold.
        drift_threshold: Detection drift anomaly threshold.
        trust_decay: Delegation trust decay factor (delta).
        consensus_acceptance: Byzantine consensus acceptance threshold.
        consensus_quorum: Quorum fraction for consensus.
        sandbox_ttl: Default belief sandbox TTL in seconds.
        canary_tolerance: Default tripwire canary tolerance.
        invariant_check_interval: Runtime monitor check interval in seconds.
        seed: Global random seed for reproducibility.
    """

    # Firewall
    injection_threshold: float = 0.7
    suspicious_threshold: float = 0.4

    # Detection
    drift_threshold: float = 0.3

    # Trust
    trust_decay: float = 0.85

    # Consensus
    consensus_acceptance: float = 0.7
    consensus_quorum: float = 2 / 3

    # Sandbox
    sandbox_ttl: float = 300.0

    # Tripwire
    canary_tolerance: float = 0.1

    # Invariants
    invariant_check_interval: float = 1.0

    # Reproducibility
    seed: int = 42

    # ---- serialisation helpers ----

    def to_dict(self) -> Dict[str, Any]:
        """Export configuration to a plain dictionary."""
        from dataclasses import asdict
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FrameworkConfig":
        """Create a ``FrameworkConfig`` from a dictionary, ignoring unknown keys."""
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


def load_config(path: Optional[str] = None) -> FrameworkConfig:
    """Load a ``FrameworkConfig`` from a YAML or JSON file.

    If *path* is ``None``, returns the default configuration.
    Supports ``.yaml``, ``.yml``, and ``.json`` extensions.
    Falls back to ``FrameworkConfig()`` if the file is missing.
    """
    if path is None:
        return FrameworkConfig()

    p = Path(path)
    if not p.exists():
        return FrameworkConfig()

    text = p.read_text(encoding="utf-8")

    if p.suffix in (".yaml", ".yml"):
        # Minimal YAML parsing without PyYAML dependency
        data = _parse_simple_yaml(text)
    elif p.suffix == ".json":
        import json
        data = json.loads(text)
    else:
        return FrameworkConfig()

    return FrameworkConfig.from_dict(data)


def _parse_simple_yaml(text: str) -> Dict[str, Any]:
    """Parse a flat key: value YAML file without external dependencies."""
    result: Dict[str, Any] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        # Type coercion
        if val.lower() in ("true", "false"):
            result[key] = val.lower() == "true"
        else:
            try:
                result[key] = int(val)
            except ValueError:
                try:
                    result[key] = float(val)
                except ValueError:
                    result[key] = val
    return result
