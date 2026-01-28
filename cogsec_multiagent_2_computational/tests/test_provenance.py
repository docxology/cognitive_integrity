"""Tests for provenance tracking and taint propagation."""

from datetime import datetime, timedelta

import pytest
from provenance import (CausalAttribution, ProvenanceChain, ProvenanceGraph,
                        ProvenanceRecord, TaintLabel)


class TestTaintLabel:
    """Tests for TaintLabel enum."""

    def test_taint_ordering(self):
        """Taint labels have defined trust ordering."""
        # SYSTEM_VERIFIED is most trusted
        assert (
            TaintLabel.SYSTEM_VERIFIED.trust_level
            > TaintLabel.PRINCIPAL_INPUT.trust_level
        )
        assert (
            TaintLabel.PRINCIPAL_INPUT.trust_level
            > TaintLabel.AGENT_INTERNAL.trust_level
        )
        assert (
            TaintLabel.AGENT_INTERNAL.trust_level
            > TaintLabel.AGENT_EXTERNAL.trust_level
        )
        assert (
            TaintLabel.AGENT_EXTERNAL.trust_level > TaintLabel.TOOL_OUTPUT.trust_level
        )
        assert TaintLabel.TOOL_OUTPUT.trust_level > TaintLabel.WEB_CONTENT.trust_level
        assert TaintLabel.WEB_CONTENT.trust_level > TaintLabel.UNVERIFIED.trust_level

    def test_is_trusted(self):
        """Trusted sources are identifiable."""
        assert TaintLabel.SYSTEM_VERIFIED.is_trusted
        assert TaintLabel.PRINCIPAL_INPUT.is_trusted
        assert not TaintLabel.UNVERIFIED.is_trusted
        assert not TaintLabel.WEB_CONTENT.is_trusted


class TestProvenanceRecord:
    """Tests for individual provenance records."""

    def test_record_creation(self):
        """Records capture source and timestamp."""
        record = ProvenanceRecord(
            belief_id="belief-1",
            content="The sky is blue",
            source=TaintLabel.PRINCIPAL_INPUT,
            agent_id="agent-0",
        )
        assert record.belief_id == "belief-1"
        assert record.source == TaintLabel.PRINCIPAL_INPUT
        assert record.agent_id == "agent-0"
        assert isinstance(record.timestamp, datetime)

    def test_record_with_parent(self):
        """Records can reference parent records."""
        parent = ProvenanceRecord(
            belief_id="parent-1",
            content="Base fact",
            source=TaintLabel.SYSTEM_VERIFIED,
            agent_id="agent-0",
        )
        child = ProvenanceRecord(
            belief_id="child-1",
            content="Derived fact",
            source=TaintLabel.AGENT_INTERNAL,
            agent_id="agent-0",
            parent_ids=["parent-1"],
        )
        assert "parent-1" in child.parent_ids


class TestProvenanceChain:
    """Tests for ProvenanceChain tracking."""

    def test_add_and_get_record(self):
        """Records can be added and retrieved."""
        chain = ProvenanceChain()
        record = chain.add_belief(
            belief_id="b1",
            content="Test belief",
            source=TaintLabel.PRINCIPAL_INPUT,
            agent_id="agent-1",
        )
        retrieved = chain.get_record("b1")
        assert retrieved is not None
        assert retrieved.content == "Test belief"

    def test_chain_ancestry(self):
        """Chain tracks complete ancestry."""
        chain = ProvenanceChain()

        # Root belief
        chain.add_belief("root", "Root fact", TaintLabel.SYSTEM_VERIFIED, "sys")

        # Derived belief
        chain.add_belief(
            "derived",
            "Derived fact",
            TaintLabel.AGENT_INTERNAL,
            "agent-1",
            parent_ids=["root"],
        )

        # Second-level derived
        chain.add_belief(
            "derived-2",
            "Second derived",
            TaintLabel.AGENT_INTERNAL,
            "agent-1",
            parent_ids=["derived"],
        )

        ancestry = chain.get_ancestry("derived-2")
        assert "root" in ancestry
        assert "derived" in ancestry

    def test_effective_taint(self):
        """Effective taint is minimum across ancestry."""
        chain = ProvenanceChain()

        # High trust root
        chain.add_belief("root", "Trusted", TaintLabel.SYSTEM_VERIFIED, "sys")

        # Lower trust transformation
        chain.add_belief(
            "derived",
            "Derived",
            TaintLabel.WEB_CONTENT,  # Lower trust
            "agent-1",
            parent_ids=["root"],
        )

        # Effective taint should be WEB_CONTENT (lower)
        taint = chain.get_effective_taint("derived")
        assert taint == TaintLabel.WEB_CONTENT

    def test_multiple_parents_taint(self):
        """Multiple parents use minimum taint."""
        chain = ProvenanceChain()

        chain.add_belief("p1", "Parent 1", TaintLabel.SYSTEM_VERIFIED, "sys")
        chain.add_belief("p2", "Parent 2", TaintLabel.WEB_CONTENT, "web")

        chain.add_belief(
            "child",
            "Combined",
            TaintLabel.AGENT_INTERNAL,
            "agent",
            parent_ids=["p1", "p2"],
        )

        # Should be WEB_CONTENT (lowest of ancestors)
        taint = chain.get_effective_taint("child")
        assert taint == TaintLabel.WEB_CONTENT


class TestProvenanceGraph:
    """Tests for ProvenanceGraph dependency analysis."""

    def test_graph_construction(self):
        """Graph builds from chain."""
        chain = ProvenanceChain()
        chain.add_belief("a", "A", TaintLabel.SYSTEM_VERIFIED, "sys")
        chain.add_belief("b", "B", TaintLabel.AGENT_INTERNAL, "ag", parent_ids=["a"])
        chain.add_belief("c", "C", TaintLabel.AGENT_INTERNAL, "ag", parent_ids=["b"])

        graph = ProvenanceGraph(chain)

        # Check dependency relationships
        assert graph.depends_on("c", "b")
        assert graph.depends_on("c", "a")
        assert not graph.depends_on("a", "c")

    def test_get_dependents(self):
        """Get all beliefs depending on a source."""
        chain = ProvenanceChain()
        chain.add_belief("root", "Root", TaintLabel.SYSTEM_VERIFIED, "sys")
        chain.add_belief(
            "d1", "D1", TaintLabel.AGENT_INTERNAL, "ag", parent_ids=["root"]
        )
        chain.add_belief(
            "d2", "D2", TaintLabel.AGENT_INTERNAL, "ag", parent_ids=["root"]
        )
        chain.add_belief("d3", "D3", TaintLabel.AGENT_INTERNAL, "ag", parent_ids=["d1"])

        graph = ProvenanceGraph(chain)
        dependents = graph.get_dependents("root")

        assert "d1" in dependents
        assert "d2" in dependents
        assert "d3" in dependents

    def test_contamination_spread(self):
        """Track contamination from compromised source."""
        chain = ProvenanceChain()
        chain.add_belief("clean", "Clean", TaintLabel.SYSTEM_VERIFIED, "sys")
        chain.add_belief("dirty", "Dirty", TaintLabel.UNVERIFIED, "unk")
        chain.add_belief(
            "mixed",
            "Mixed",
            TaintLabel.AGENT_INTERNAL,
            "ag",
            parent_ids=["clean", "dirty"],
        )
        chain.add_belief(
            "downstream",
            "Downstream",
            TaintLabel.AGENT_INTERNAL,
            "ag",
            parent_ids=["mixed"],
        )

        graph = ProvenanceGraph(chain)
        contaminated = graph.get_contaminated_by("dirty")

        assert "mixed" in contaminated
        assert "downstream" in contaminated
        assert "clean" not in contaminated


class TestCausalAttribution:
    """Tests for CausalAttribution compromise identification."""

    def test_identify_compromise_source(self):
        """Identify which untrusted source caused contamination."""
        chain = ProvenanceChain()
        chain.add_belief("trusted", "Trusted", TaintLabel.SYSTEM_VERIFIED, "sys")
        chain.add_belief("untrusted", "Bad", TaintLabel.UNVERIFIED, "unk")
        chain.add_belief(
            "affected",
            "Affected",
            TaintLabel.AGENT_INTERNAL,
            "ag",
            parent_ids=["trusted", "untrusted"],
        )

        attribution = CausalAttribution(chain)
        sources = attribution.identify_untrusted_sources("affected")

        assert "untrusted" in sources

    def test_trace_path_to_compromise(self):
        """Trace path from belief to compromise source."""
        chain = ProvenanceChain()
        chain.add_belief("bad", "Bad", TaintLabel.WEB_CONTENT, "web")
        chain.add_belief(
            "mid", "Mid", TaintLabel.AGENT_INTERNAL, "ag", parent_ids=["bad"]
        )
        chain.add_belief(
            "end", "End", TaintLabel.AGENT_INTERNAL, "ag", parent_ids=["mid"]
        )

        attribution = CausalAttribution(chain)
        paths = attribution.trace_to_untrusted("end")

        assert len(paths) > 0
        # Path should include: end -> mid -> bad
        path = paths[0]
        assert "bad" in path
        assert "mid" in path

    def test_attribution_report(self):
        """Generate attribution report for belief."""
        chain = ProvenanceChain()
        chain.add_belief("sys", "System", TaintLabel.SYSTEM_VERIFIED, "sys")
        chain.add_belief("web", "Web data", TaintLabel.WEB_CONTENT, "web")
        chain.add_belief(
            "combined",
            "Combined",
            TaintLabel.AGENT_INTERNAL,
            "agent-1",
            parent_ids=["sys", "web"],
        )

        attribution = CausalAttribution(chain)
        report = attribution.generate_report("combined")

        assert report["belief_id"] == "combined"
        assert report["effective_taint"] == TaintLabel.WEB_CONTENT
        assert len(report["untrusted_sources"]) > 0

    def test_multi_hop_attribution(self):
        """Attribution works across multiple hops."""
        chain = ProvenanceChain()
        chain.add_belief("origin", "Bad origin", TaintLabel.UNVERIFIED, "unk")

        # Chain of derivations
        prev = "origin"
        for i in range(5):
            new_id = f"hop-{i}"
            chain.add_belief(
                new_id, f"Hop {i}", TaintLabel.AGENT_INTERNAL, "ag", parent_ids=[prev]
            )
            prev = new_id

        attribution = CausalAttribution(chain)
        sources = attribution.identify_untrusted_sources("hop-4")

        assert "origin" in sources


class TestTaintPropagation:
    """Tests for taint propagation semantics."""

    def test_taint_does_not_upgrade(self):
        """Taint never upgrades through derivation."""
        chain = ProvenanceChain()
        chain.add_belief("low", "Low trust", TaintLabel.UNVERIFIED, "unk")
        chain.add_belief(
            "derived",
            "Derived high?",
            TaintLabel.SYSTEM_VERIFIED,  # Claim high trust
            "sys",
            parent_ids=["low"],
        )

        # Effective taint should still be UNVERIFIED
        taint = chain.get_effective_taint("derived")
        assert taint == TaintLabel.UNVERIFIED

    def test_independent_beliefs_no_contamination(self):
        """Independent beliefs don't contaminate each other."""
        chain = ProvenanceChain()
        chain.add_belief("clean", "Clean", TaintLabel.SYSTEM_VERIFIED, "sys")
        chain.add_belief("dirty", "Dirty", TaintLabel.UNVERIFIED, "unk")

        # clean should not be affected by dirty
        clean_taint = chain.get_effective_taint("clean")
        assert clean_taint == TaintLabel.SYSTEM_VERIFIED

    def test_taint_metadata(self):
        """Records can carry arbitrary metadata."""
        chain = ProvenanceChain()
        record = chain.add_belief(
            "b1",
            "Test",
            TaintLabel.TOOL_OUTPUT,
            "tool",
            metadata={"tool_name": "web_scraper", "url": "https://example.com"},
        )

        assert record.metadata["tool_name"] == "web_scraper"
