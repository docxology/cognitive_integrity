"""950-attack corpus with stratified splits and persistence.

The corpus contains 950 attack samples distributed across 4 top-level
categories and 12 subcategories:

    injection (500):
        direct_injection (200), indirect_injection (200), nested_injection (100)
    trust_exploitation (200):
        impersonation (80), trust_inflation (60), delegation_abuse (60)
    belief_manipulation (150):
        belief_drift (50), belief_fabrication (50), belief_injection (50)
    coordination (100):
        sybil_attack (40), consensus_poisoning (30), timing_attack (30)

All generation is deterministic given a seed value.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

import numpy as np

from utils.types import AttackCategory

# ---------------------------------------------------------------------------
# Attack sample dataclass
# ---------------------------------------------------------------------------

@dataclass
class AttackSample:
    """A single attack sample in the corpus.

    Attributes:
        id: Unique identifier (e.g. ``'INJ-D-0001'``).
        payload: The attack payload text.
        category: :class:`AttackCategory` enum value.
        subcategory: Human-readable subcategory string.
        difficulty: ``'easy'``, ``'medium'``, or ``'hard'``.
        expected_detection: Whether defenses are expected to detect this. Note
        this is an invariant/assertion for corpus entries (all are attacks;
        always True in generated samples) rather than a per-sample
        difficulty estimate (P2-28).
        metadata: Additional information (technique, variant, etc.).
    """

    id: str
    payload: str
    category: AttackCategory
    subcategory: str
    difficulty: str
    expected_detection: bool
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain dict (JSON-safe)."""
        d = asdict(self)
        d["category"] = self.category.value
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AttackSample":
        """Deserialize from a plain dict."""
        data = dict(data)  # shallow copy
        data["category"] = AttackCategory(data["category"])
        return cls(**data)


# ---------------------------------------------------------------------------
# Category ID prefixes
# ---------------------------------------------------------------------------

_CATEGORY_PREFIX = {
    AttackCategory.DIRECT_INJECTION: "INJ-D",
    AttackCategory.INDIRECT_INJECTION: "INJ-I",
    AttackCategory.NESTED_INJECTION: "INJ-N",
    AttackCategory.IMPERSONATION: "TRE-I",
    AttackCategory.TRUST_INFLATION: "TRE-T",
    AttackCategory.DELEGATION_ABUSE: "TRE-D",
    AttackCategory.BELIEF_DRIFT: "BLM-D",
    AttackCategory.BELIEF_FABRICATION: "BLM-F",
    AttackCategory.BELIEF_INJECTION: "BLM-I",
    AttackCategory.SYBIL_ATTACK: "CRD-S",
    AttackCategory.CONSENSUS_POISONING: "CRD-C",
    AttackCategory.TIMING_ATTACK: "CRD-T",
    AttackCategory.PROVENANCE_LAUNDERING: "PRI-P",
    AttackCategory.SANDBOX_ESCAPE: "PRI-S",
    AttackCategory.BYZANTINE_MANIPULATION: "PRI-B",
}

_TOP_CATEGORY_MAP = {
    "injection": [
        AttackCategory.DIRECT_INJECTION,
        AttackCategory.INDIRECT_INJECTION,
        AttackCategory.NESTED_INJECTION,
    ],
    "trust_exploitation": [
        AttackCategory.IMPERSONATION,
        AttackCategory.TRUST_INFLATION,
        AttackCategory.DELEGATION_ABUSE,
    ],
    "belief_manipulation": [
        AttackCategory.BELIEF_DRIFT,
        AttackCategory.BELIEF_FABRICATION,
        AttackCategory.BELIEF_INJECTION,
    ],
    "coordination": [
        AttackCategory.SYBIL_ATTACK,
        AttackCategory.CONSENSUS_POISONING,
        AttackCategory.TIMING_ATTACK,
    ],
}


# ---------------------------------------------------------------------------
# Attack corpus
# ---------------------------------------------------------------------------

class AttackCorpus:
    """A collection of :class:`AttackSample` objects with indexing and persistence.

    The canonical corpus contains 950 samples and is generated
    deterministically via :meth:`generate`.
    """

    def __init__(self, samples: Optional[List[AttackSample]] = None) -> None:
        self._samples: List[AttackSample] = list(samples) if samples else []

    # -- container protocol --

    def __len__(self) -> int:
        return len(self._samples)

    def __getitem__(self, index: int) -> AttackSample:
        return self._samples[index]

    def __iter__(self) -> Iterator[AttackSample]:
        return iter(self._samples)

    def __repr__(self) -> str:
        return f"AttackCorpus(n={len(self)})"

    # -- filtering --

    def by_category(self, cat: AttackCategory) -> List[AttackSample]:
        """Return all samples matching a specific :class:`AttackCategory`."""
        return [s for s in self._samples if s.category == cat]

    def by_top_category(self, name: str) -> List[AttackSample]:
        """Return all samples in a top-level category.

        Args:
            name: One of ``'injection'``, ``'trust_exploitation'``,
                ``'belief_manipulation'``, ``'coordination'``.

        Raises:
            KeyError: If *name* is not a valid top-level category.
        """
        cats = _TOP_CATEGORY_MAP[name]
        return [s for s in self._samples if s.category in cats]

    def by_difficulty(self, difficulty: str) -> List[AttackSample]:
        """Return all samples matching a difficulty level."""
        return [s for s in self._samples if s.difficulty == difficulty]

    # -- stratified split --

    def stratified_split(
        self,
        train_frac: float = 0.7,
        seed: int = 42,
    ) -> Tuple["AttackCorpus", "AttackCorpus"]:
        """Split the corpus into train/test sets, stratified by subcategory.

        Each subcategory maintains its proportion in both splits.

        Args:
            train_frac: Fraction of samples for the training set.
            seed: Random seed for the shuffle.

        Returns:
            (train_corpus, test_corpus)
        """
        rng = np.random.default_rng(seed)

        # Group by subcategory
        groups: Dict[str, List[AttackSample]] = {}
        for sample in self._samples:
            groups.setdefault(sample.subcategory, []).append(sample)

        train_samples: List[AttackSample] = []
        test_samples: List[AttackSample] = []

        for subcat in sorted(groups.keys()):
            group = groups[subcat]
            indices = rng.permutation(len(group))
            n_train = max(1, int(len(group) * train_frac))
            for idx in indices[:n_train]:
                train_samples.append(group[idx])
            for idx in indices[n_train:]:
                test_samples.append(group[idx])

        return AttackCorpus(train_samples), AttackCorpus(test_samples)

    # -- persistence --

    def save(self, path: str) -> None:
        """Save the corpus to a JSON file.

        Args:
            path: File path (will be created / overwritten).
        """
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        data = [s.to_dict() for s in self._samples]
        p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: str) -> "AttackCorpus":
        """Load a corpus from a JSON file.

        Args:
            path: File path to a previously saved corpus.

        Returns:
            A new :class:`AttackCorpus` with the loaded samples.

        Raises:
            FileNotFoundError: If *path* does not exist.
        """
        p = Path(path)
        data = json.loads(p.read_text(encoding="utf-8"))
        samples = [AttackSample.from_dict(d) for d in data]
        return cls(samples)

    # -- generation --

    @classmethod
    def generate(cls, seed: int = 42, *, extended: bool = False) -> "AttackCorpus":
        """Generate the attack corpus: 950 published samples, or 1475 extended.

        ``extended=True`` is the integrated corpus and the default: 1475 items
        across fifteen categories, and the only corpus that exercises all eight
        defense modules. The earlier 950-item corpus contained no instance of
        what the provenance, sandbox and consensus adapters detect, which is
        why the full defense lattice gave all three a Shapley value of exactly
        zero in every one of its 256 coalitions. A corpus that cannot reach
        three of eight mechanisms cannot measure the framework, and every
        number this series reports is now measured against one that can.

        ``extended=False`` reproduces those original 950 items unchanged. It is
        kept for the comparison and for reproducing previously published
        figures, not because two corpora are wanted going forward.

        Uses the four generator modules to produce samples for each
        category, assigns unique IDs, and returns the corpus.

        Args:
            seed: Random seed for reproducible generation.

        Returns:
            A new :class:`AttackCorpus` with 950 samples.
        """
        from .generators.belief_manipulation import generate_all_belief_manipulation
        from .generators.coordination import generate_all_coordination
        from .generators.injection import generate_all_injection
        from .generators.provenance_and_isolation import (
            generate_all_provenance_and_isolation,
        )
        from .generators.trust_exploitation import generate_all_trust_exploitation

        rng = np.random.default_rng(seed)

        raw_samples: List[dict] = []
        raw_samples.extend(generate_all_injection(rng))            # 500
        raw_samples.extend(generate_all_trust_exploitation(rng))   # 200
        raw_samples.extend(generate_all_belief_manipulation(rng))  # 150
        raw_samples.extend(generate_all_coordination(rng))         # 100
        if extended:
            raw_samples.extend(generate_all_provenance_and_isolation(rng))  # 525

        # Assign unique IDs and create AttackSample objects
        counters: Dict[str, int] = {}
        samples: List[AttackSample] = []

        for raw in raw_samples:
            cat: AttackCategory = raw["category"]
            prefix = _CATEGORY_PREFIX[cat]
            counters.setdefault(prefix, 0)
            counters[prefix] += 1
            sample_id = f"{prefix}-{counters[prefix]:04d}"

            samples.append(AttackSample(
                id=sample_id,
                payload=raw["payload"],
                category=cat,
                subcategory=raw["subcategory"],
                difficulty=raw["difficulty"],
                expected_detection=True,  # All corpus entries are attacks
                metadata=raw.get("metadata", {}),
            ))

        return cls(samples)

    # -- statistics --

    def distribution(self) -> Dict[str, int]:
        """Return a dict mapping top-level category -> count."""
        dist: Dict[str, int] = {}
        for sample in self._samples:
            top = sample.category.top_category
            dist[top] = dist.get(top, 0) + 1
        return dist

    def subcategory_distribution(self) -> Dict[str, int]:
        """Return a dict mapping subcategory -> count."""
        dist: Dict[str, int] = {}
        for sample in self._samples:
            dist[sample.subcategory] = dist.get(sample.subcategory, 0) + 1
        return dist
