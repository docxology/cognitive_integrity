"""
Information Flow Tracking with Taint Propagation.

Implements provenance chains for tracking belief origins and contamination.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set


class TaintLabel(Enum):
    """
    Taint labels for information sources with trust ordering.

    Higher trust_level = more trusted source.
    """

    SYSTEM_VERIFIED = ("system_verified", 7, True)
    PRINCIPAL_INPUT = ("principal_input", 6, True)
    AGENT_INTERNAL = ("agent_internal", 5, True)
    AGENT_EXTERNAL = ("agent_external", 4, False)
    TOOL_OUTPUT = ("tool_output", 3, False)
    WEB_CONTENT = ("web_content", 2, False)
    UNVERIFIED = ("unverified", 1, False)

    def __init__(self, label: str, level: int, trusted: bool):
        self._label = label
        self._trust_level = level
        self._is_trusted = trusted

    @property
    def trust_level(self) -> int:
        """Return trust level (higher = more trusted)."""
        return self._trust_level

    @property
    def is_trusted(self) -> bool:
        """Return whether this source is considered trusted."""
        return self._is_trusted


@dataclass
class ProvenanceRecord:
    """
    Record of a belief's provenance.

    Tracks the source, derivation chain, and metadata.
    """

    belief_id: str
    content: str
    source: TaintLabel
    agent_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    parent_ids: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


class ProvenanceChain:
    """
    Tracks belief provenance and derivation chains.

    Maintains a directed acyclic graph of belief derivations
    with taint propagation semantics.
    """

    def __init__(self):
        self._records: Dict[str, ProvenanceRecord] = {}

    def add_belief(
        self,
        belief_id: str,
        content: str,
        source: TaintLabel,
        agent_id: str,
        parent_ids: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
        timestamp: Optional[datetime] = None,
    ) -> ProvenanceRecord:
        """
        Add a belief to the provenance chain.

        Args:
            belief_id: Unique identifier for the belief
            content: The belief content
            source: Taint label for the immediate source
            agent_id: Agent that created/received this belief
            parent_ids: IDs of beliefs this was derived from
            metadata: Additional metadata
            timestamp: Creation timestamp (defaults to now)

        Returns:
            The created ProvenanceRecord
        """
        record = ProvenanceRecord(
            belief_id=belief_id,
            content=content,
            source=source,
            agent_id=agent_id,
            timestamp=timestamp or datetime.now(),
            parent_ids=parent_ids or [],
            metadata=metadata or {},
        )
        self._records[belief_id] = record
        return record

    def get_record(self, belief_id: str) -> Optional[ProvenanceRecord]:
        """Get a provenance record by belief ID."""
        return self._records.get(belief_id)

    def get_ancestry(self, belief_id: str) -> Set[str]:
        """
        Get all ancestor belief IDs (transitive parents).

        Args:
            belief_id: The belief to trace ancestry for

        Returns:
            Set of all ancestor belief IDs
        """
        ancestors = set()
        queue = [belief_id]
        visited = set()

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)

            record = self._records.get(current)
            if record and record.parent_ids:
                for parent_id in record.parent_ids:
                    if parent_id not in visited:
                        ancestors.add(parent_id)
                        queue.append(parent_id)

        return ancestors

    def get_effective_taint(self, belief_id: str) -> TaintLabel:
        """
        Get effective taint level for a belief.

        The effective taint is the minimum trust level across
        the belief and all its ancestors. Taint propagates
        conservatively - a belief is only as trusted as its
        least trusted source.

        Args:
            belief_id: The belief to evaluate

        Returns:
            The effective (minimum) taint label
        """
        record = self._records.get(belief_id)
        if not record:
            return TaintLabel.UNVERIFIED

        # Start with this belief's source
        min_taint = record.source
        min_level = min_taint.trust_level

        # Check all ancestors
        ancestors = self.get_ancestry(belief_id)
        for ancestor_id in ancestors:
            ancestor = self._records.get(ancestor_id)
            if ancestor and ancestor.source.trust_level < min_level:
                min_taint = ancestor.source
                min_level = ancestor.source.trust_level

        return min_taint

    def get_all_records(self) -> List[ProvenanceRecord]:
        """Get all provenance records."""
        return list(self._records.values())


class ProvenanceGraph:
    """
    Graph-based analysis of provenance dependencies.

    Provides efficient queries for dependency and contamination analysis.
    """

    def __init__(self, chain: ProvenanceChain):
        self._chain = chain
        self._dependents: Dict[str, Set[str]] = {}  # parent -> children
        self._build_graph()

    def _build_graph(self) -> None:
        """Build dependency graph from chain."""
        self._dependents.clear()

        for record in self._chain.get_all_records():
            # Initialize entry for this belief
            if record.belief_id not in self._dependents:
                self._dependents[record.belief_id] = set()

            # Register as dependent of each parent
            for parent_id in record.parent_ids:
                if parent_id not in self._dependents:
                    self._dependents[parent_id] = set()
                self._dependents[parent_id].add(record.belief_id)

    def depends_on(self, belief_id: str, ancestor_id: str) -> bool:
        """
        Check if belief depends on ancestor.

        Args:
            belief_id: The belief to check
            ancestor_id: Potential ancestor

        Returns:
            True if belief depends on ancestor
        """
        record = self._chain.get_record(belief_id)
        if not record:
            return False

        # Direct parent
        if ancestor_id in record.parent_ids:
            return True

        # Check transitive ancestors
        ancestry = self._chain.get_ancestry(belief_id)
        return ancestor_id in ancestry

    def get_dependents(self, belief_id: str) -> Set[str]:
        """
        Get all beliefs that depend on a given belief (transitively).

        Args:
            belief_id: The source belief

        Returns:
            Set of all dependent belief IDs
        """
        dependents = set()
        queue = list(self._dependents.get(belief_id, set()))

        while queue:
            current = queue.pop(0)
            if current not in dependents:
                dependents.add(current)
                # Add this node's dependents to queue
                for dep in self._dependents.get(current, set()):
                    if dep not in dependents:
                        queue.append(dep)

        return dependents

    def get_contaminated_by(self, source_id: str) -> Set[str]:
        """
        Get all beliefs contaminated by a source.

        Alias for get_dependents, named for clarity in
        security contexts.

        Args:
            source_id: The contamination source

        Returns:
            Set of contaminated belief IDs
        """
        return self.get_dependents(source_id)


class CausalAttribution:
    """
    Identifies compromise sources through causal analysis.

    Given a potentially compromised belief, traces back to
    identify which untrusted sources contributed to it.
    """

    def __init__(self, chain: ProvenanceChain):
        self._chain = chain
        self._graph = ProvenanceGraph(chain)

    def identify_untrusted_sources(self, belief_id: str) -> Set[str]:
        """
        Identify all untrusted sources in a belief's ancestry.

        Args:
            belief_id: The belief to analyze

        Returns:
            Set of untrusted source belief IDs
        """
        untrusted: set[str] = set()
        record = self._chain.get_record(belief_id)

        if not record:
            return untrusted

        # Check the belief itself
        if not record.source.is_trusted:
            untrusted.add(belief_id)

        # Check all ancestors
        ancestors = self._chain.get_ancestry(belief_id)
        for ancestor_id in ancestors:
            ancestor = self._chain.get_record(ancestor_id)
            if ancestor and not ancestor.source.is_trusted:
                untrusted.add(ancestor_id)

        return untrusted

    def trace_to_untrusted(self, belief_id: str) -> List[List[str]]:
        """
        Trace paths from belief to untrusted sources.

        Args:
            belief_id: The belief to trace from

        Returns:
            List of paths (each path is a list of belief IDs)
        """
        paths = []
        untrusted_sources = self.identify_untrusted_sources(belief_id)

        for source_id in untrusted_sources:
            # Find path from belief to this untrusted source
            path = self._find_path(belief_id, source_id)
            if path:
                paths.append(path)

        return paths

    def _find_path(self, start_id: str, target_id: str) -> Optional[List[str]]:
        """
        Find path from start to target through parent links.

        Uses BFS to find shortest path.
        """
        if start_id == target_id:
            return [start_id]

        queue = [[start_id]]
        visited = {start_id}

        while queue:
            path = queue.pop(0)
            current = path[-1]

            record = self._chain.get_record(current)
            if not record:
                continue

            for parent_id in record.parent_ids:
                if parent_id == target_id:
                    return path + [parent_id]

                if parent_id not in visited:
                    visited.add(parent_id)
                    queue.append(path + [parent_id])

        return None

    def generate_report(self, belief_id: str) -> Dict:
        """
        Generate an attribution report for a belief.

        Args:
            belief_id: The belief to analyze

        Returns:
            Dict containing:
            - belief_id: The analyzed belief
            - effective_taint: The effective taint level
            - untrusted_sources: List of untrusted source IDs
            - paths: Paths to untrusted sources
            - ancestry_size: Total number of ancestors
        """
        record = self._chain.get_record(belief_id)
        if not record:
            return {
                "belief_id": belief_id,
                "effective_taint": TaintLabel.UNVERIFIED,
                "untrusted_sources": [],
                "paths": [],
                "ancestry_size": 0,
                "error": "Belief not found",
            }

        effective_taint = self._chain.get_effective_taint(belief_id)
        untrusted_sources = self.identify_untrusted_sources(belief_id)
        paths = self.trace_to_untrusted(belief_id)
        ancestry = self._chain.get_ancestry(belief_id)

        return {
            "belief_id": belief_id,
            "effective_taint": effective_taint,
            "untrusted_sources": list(untrusted_sources),
            "paths": paths,
            "ancestry_size": len(ancestry),
        }
