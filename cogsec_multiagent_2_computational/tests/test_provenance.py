"""Tests for provenance tracking and taint propagation."""

from datetime import datetime

from src import CausalAttribution, ProvenanceChain, ProvenanceGraph, ProvenanceRecord, TaintLabel


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
        ProvenanceRecord(
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
        chain.add_belief(
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
        assert report["effective_taint"] == TaintLabel.WEB_CONTENT.value
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


# ---------------------------------------------------------------------------
# Extended ProvenanceGraph tests (diamond patterns, isolated nodes)
# ---------------------------------------------------------------------------


class TestProvenanceGraphExtended:
    """Extended tests for ProvenanceGraph dependency analysis."""

    def test_diamond_dependency(self):
        """Diamond pattern: A->B, A->C, B->D, C->D. D depends on A, B, C."""
        chain = ProvenanceChain()
        chain.add_belief("A", "Root", TaintLabel.SYSTEM_VERIFIED, "sys")
        chain.add_belief(
            "B", "Left", TaintLabel.AGENT_INTERNAL, "ag", parent_ids=["A"]
        )
        chain.add_belief(
            "C", "Right", TaintLabel.AGENT_INTERNAL, "ag", parent_ids=["A"]
        )
        chain.add_belief(
            "D", "Merge", TaintLabel.AGENT_INTERNAL, "ag", parent_ids=["B", "C"]
        )

        graph = ProvenanceGraph(chain)

        assert graph.depends_on("D", "A")
        assert graph.depends_on("D", "B")
        assert graph.depends_on("D", "C")
        # A does not depend on D
        assert not graph.depends_on("A", "D")

    def test_get_dependents_diamond(self):
        """In diamond pattern, get_dependents('A') includes B, C, D."""
        chain = ProvenanceChain()
        chain.add_belief("A", "Root", TaintLabel.SYSTEM_VERIFIED, "sys")
        chain.add_belief(
            "B", "Left", TaintLabel.AGENT_INTERNAL, "ag", parent_ids=["A"]
        )
        chain.add_belief(
            "C", "Right", TaintLabel.AGENT_INTERNAL, "ag", parent_ids=["A"]
        )
        chain.add_belief(
            "D", "Merge", TaintLabel.AGENT_INTERNAL, "ag", parent_ids=["B", "C"]
        )

        graph = ProvenanceGraph(chain)
        dependents = graph.get_dependents("A")

        assert "B" in dependents
        assert "C" in dependents
        assert "D" in dependents

    def test_isolated_node_no_dependents(self):
        """Isolated node with no children has empty dependents."""
        chain = ProvenanceChain()
        chain.add_belief("isolated", "Alone", TaintLabel.SYSTEM_VERIFIED, "sys")
        chain.add_belief("other", "Other", TaintLabel.AGENT_INTERNAL, "ag")

        graph = ProvenanceGraph(chain)
        dependents = graph.get_dependents("isolated")

        assert len(dependents) == 0


# ---------------------------------------------------------------------------
# Extended CausalAttribution tests (complex graphs, deep chains)
# ---------------------------------------------------------------------------


class TestCausalAttributionExtended:
    """Extended tests for CausalAttribution with complex topologies."""

    def test_complex_multi_source_graph(self):
        """Two untrusted sources feed into a chain; both are identified."""
        chain = ProvenanceChain()
        chain.add_belief("bad1", "Untrusted A", TaintLabel.UNVERIFIED, "unk")
        chain.add_belief("bad2", "Untrusted B", TaintLabel.WEB_CONTENT, "web")
        chain.add_belief(
            "merge1",
            "First merge",
            TaintLabel.AGENT_INTERNAL,
            "ag",
            parent_ids=["bad1"],
        )
        chain.add_belief(
            "merge2",
            "Second merge",
            TaintLabel.AGENT_INTERNAL,
            "ag",
            parent_ids=["bad2"],
        )
        chain.add_belief(
            "final",
            "Final combination",
            TaintLabel.AGENT_INTERNAL,
            "ag",
            parent_ids=["merge1", "merge2"],
        )

        attribution = CausalAttribution(chain)
        sources = attribution.identify_untrusted_sources("final")

        assert "bad1" in sources
        assert "bad2" in sources

    def test_attribution_all_trusted(self):
        """All sources SYSTEM_VERIFIED: identify_untrusted_sources returns empty."""
        chain = ProvenanceChain()
        chain.add_belief("s1", "Sys1", TaintLabel.SYSTEM_VERIFIED, "sys")
        chain.add_belief("s2", "Sys2", TaintLabel.SYSTEM_VERIFIED, "sys")
        chain.add_belief(
            "derived",
            "Derived",
            TaintLabel.PRINCIPAL_INPUT,
            "principal",
            parent_ids=["s1", "s2"],
        )

        attribution = CausalAttribution(chain)
        sources = attribution.identify_untrusted_sources("derived")

        assert len(sources) == 0

    def test_deep_chain_taint(self):
        """10-hop chain from UNVERIFIED source; taint preserved at hop 9."""
        chain = ProvenanceChain()
        chain.add_belief("origin", "Bad origin", TaintLabel.UNVERIFIED, "unk")

        prev = "origin"
        for i in range(10):
            hop_id = f"hop-{i}"
            chain.add_belief(
                hop_id,
                f"Hop {i}",
                TaintLabel.AGENT_INTERNAL,
                "ag",
                parent_ids=[prev],
            )
            prev = hop_id

        # Effective taint at the 10th hop (hop-9) should still be UNVERIFIED
        taint = chain.get_effective_taint("hop-9")
        assert taint == TaintLabel.UNVERIFIED

    def test_report_multiple_untrusted(self):
        """Three untrusted sources merging; report shows all three."""
        chain = ProvenanceChain()
        chain.add_belief("u1", "Unverified 1", TaintLabel.UNVERIFIED, "unk")
        chain.add_belief("u2", "Web content", TaintLabel.WEB_CONTENT, "web")
        chain.add_belief("u3", "Tool output", TaintLabel.TOOL_OUTPUT, "tool")
        chain.add_belief(
            "combined",
            "All merged",
            TaintLabel.AGENT_INTERNAL,
            "ag",
            parent_ids=["u1", "u2", "u3"],
        )

        attribution = CausalAttribution(chain)
        report = attribution.generate_report("combined")

        assert report["belief_id"] == "combined"
        untrusted_ids = set(report["untrusted_sources"])
        assert "u1" in untrusted_ids
        assert "u2" in untrusted_ids
        assert "u3" in untrusted_ids
        assert len(untrusted_ids) == 3


# ---------------------------------------------------------------------------
# TaintLabel ordering and boundary tests
# ---------------------------------------------------------------------------


class TestTaintLevelOrdering:
    """Tests for TaintLabel trust level ordering and boundaries."""

    def test_all_taint_levels_defined(self):
        """All 7 TaintLabel values exist."""
        expected = {
            "SYSTEM_VERIFIED",
            "PRINCIPAL_INPUT",
            "AGENT_INTERNAL",
            "AGENT_EXTERNAL",
            "TOOL_OUTPUT",
            "WEB_CONTENT",
            "UNVERIFIED",
        }
        actual = {label.name for label in TaintLabel}
        assert actual == expected
        assert len(actual) == 7

    def test_trust_level_numeric(self):
        """Each TaintLabel has a numeric trust_level attribute."""
        for label in TaintLabel:
            assert isinstance(label.trust_level, int)

    def test_strict_ordering(self):
        """Full strict ordering: SV > PI > AI > AE > TO > WC > UV."""
        ordered = [
            TaintLabel.SYSTEM_VERIFIED,
            TaintLabel.PRINCIPAL_INPUT,
            TaintLabel.AGENT_INTERNAL,
            TaintLabel.AGENT_EXTERNAL,
            TaintLabel.TOOL_OUTPUT,
            TaintLabel.WEB_CONTENT,
            TaintLabel.UNVERIFIED,
        ]
        for i in range(len(ordered) - 1):
            assert ordered[i].trust_level > ordered[i + 1].trust_level, (
                f"{ordered[i].name} should have higher trust than {ordered[i + 1].name}"
            )

    def test_is_trusted_boundary(self):
        """Only SYSTEM_VERIFIED, PRINCIPAL_INPUT, AGENT_INTERNAL are trusted."""
        trusted_expected = {
            TaintLabel.SYSTEM_VERIFIED: True,
            TaintLabel.PRINCIPAL_INPUT: True,
            TaintLabel.AGENT_INTERNAL: True,
            TaintLabel.AGENT_EXTERNAL: False,
            TaintLabel.TOOL_OUTPUT: False,
            TaintLabel.WEB_CONTENT: False,
            TaintLabel.UNVERIFIED: False,
        }
        for label, expected in trusted_expected.items():
            assert label.is_trusted == expected, (
                f"{label.name}.is_trusted should be {expected}"
            )


# ---------------------------------------------------------------------------
# Extended ProvenanceChain tests (edge cases)
# ---------------------------------------------------------------------------


class TestProvenanceChainExtended:
    """Extended tests for ProvenanceChain edge cases."""

    def test_get_record_nonexistent(self):
        """get_record for a nonexistent ID returns None."""
        chain = ProvenanceChain()
        chain.add_belief("exists", "I exist", TaintLabel.SYSTEM_VERIFIED, "sys")

        result = chain.get_record("nonexistent_id")
        assert result is None

    def test_ancestry_root_node(self):
        """get_ancestry of root node (no parents) returns empty set."""
        chain = ProvenanceChain()
        chain.add_belief("root", "I am root", TaintLabel.SYSTEM_VERIFIED, "sys")

        ancestry = chain.get_ancestry("root")
        assert len(ancestry) == 0
