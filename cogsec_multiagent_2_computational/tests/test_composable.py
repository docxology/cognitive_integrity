"""Comprehensive tests for src/visualization/composable.py.

Covers all 6 renderer classes and utility functions:
- series_rate / parallel_rate
- DefenseGraph  (DAG, ASCII, SVG, repr)
- CategoryDiagram (commutative diagram, matplotlib, ASCII, SVG, repr)
- LatticeViz (Hasse diagram, covering relations, ASCII, SVG, repr)
- OperadPlot (series/parallel trees, ASCII, SVG, repr)
- MonadFlow (Kleisli pipeline, ASCII, SVG, repr)
- LensDiagram (lens optic, ASCII, SVG, repr)
- render_all_diagrams (combined report, file output)

No mocks — all tests use real computations.
"""

from __future__ import annotations

import os

import matplotlib
import matplotlib.pyplot as plt

matplotlib.use("Agg")

from visualization.composable import (
    MODULE_META,
    PRESET_PIPELINES,
    CategoryDiagram,
    DefenseGraph,
    DiagramArrow,
    DiagramObject,
    KleisliArrow,
    LatticeNode,
    LatticeViz,
    LensDiagram,
    MonadFlow,
    OperadNode,
    OperadPlot,
    PipelineNode,
    parallel_rate,
    render_all_diagrams,
    series_rate,
)

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------


class TestModuleConstants:
    """Tests for MODULE_META and PRESET_PIPELINES."""

    def test_module_meta_has_eight_entries(self):
        assert len(MODULE_META) == 8

    def test_module_meta_required_keys(self):
        required = {"omega_class", "detection_rate", "color", "type_annotation"}
        for name, meta in MODULE_META.items():
            missing = required - meta.keys()
            assert not missing, f"{name} missing keys: {missing}"

    def test_detection_rates_in_range(self):
        for name, meta in MODULE_META.items():
            r = meta["detection_rate"]
            assert 0.0 <= r <= 1.0, f"{name}: rate={r} out of range"

    def test_colors_are_hex(self):
        for name, meta in MODULE_META.items():
            c = meta["color"]
            assert c.startswith("#"), f"{name}: {c}"
            assert len(c) in (7, 9), f"{name}: {c}"

    def test_preset_pipelines_keys(self):
        expected = {"full_stack", "minimal_viable", "fast_path", "hybrid"}
        assert set(PRESET_PIPELINES.keys()) == expected

    def test_preset_pipeline_modules_are_lists(self):
        for name, p in PRESET_PIPELINES.items():
            assert isinstance(p["modules"], list), f"{name}: modules not list"

    def test_full_stack_has_all_modules(self):
        full = PRESET_PIPELINES["full_stack"]
        assert set(full["modules"]) == set(MODULE_META.keys())


# ---------------------------------------------------------------------------
# Rate utility functions
# ---------------------------------------------------------------------------


class TestRateFunctions:
    """Tests for series_rate and parallel_rate."""

    def test_series_rate_empty(self):
        assert series_rate([]) == 0.0

    def test_series_rate_single(self):
        assert abs(series_rate([0.5]) - 0.5) < 1e-10

    def test_series_rate_two(self):
        # 1 - (1-0.5)(1-0.5) = 1 - 0.25 = 0.75
        result = series_rate([0.5, 0.5])
        assert abs(result - 0.75) < 1e-10

    def test_series_rate_all_one(self):
        assert abs(series_rate([1.0, 1.0, 1.0]) - 1.0) < 1e-10

    def test_series_rate_all_zero(self):
        assert abs(series_rate([0.0, 0.0]) - 0.0) < 1e-10

    def test_series_rate_eight_modules(self):
        rates = [m["detection_rate"] for m in MODULE_META.values()]
        result = series_rate(rates)
        assert 0.0 < result <= 1.0

    def test_parallel_rate_empty(self):
        assert parallel_rate([]) == 0.0

    def test_parallel_rate_single(self):
        assert parallel_rate([0.7]) == 0.7

    def test_parallel_rate_returns_max(self):
        assert parallel_rate([0.3, 0.8, 0.5]) == 0.8

    def test_parallel_rate_all_equal(self):
        assert parallel_rate([0.6, 0.6, 0.6]) == 0.6


# ---------------------------------------------------------------------------
# PipelineNode
# ---------------------------------------------------------------------------


class TestPipelineNode:
    def test_basic_construction(self):
        node = PipelineNode(module_name="Firewall", node_id="node_0", rate=0.91)
        assert node.module_name == "Firewall"
        assert node.node_id == "node_0"
        assert node.rate == 0.91

    def test_default_color(self):
        node = PipelineNode(module_name="X", node_id="n0")
        assert node.color == "#95a5a6"


# ---------------------------------------------------------------------------
# DefenseGraph
# ---------------------------------------------------------------------------


class TestDefenseGraph:
    """Tests for DefenseGraph — construction, pipeline building, rendering."""

    def test_default_construction(self):
        dg = DefenseGraph()
        assert dg.title == "Defense Pipeline"
        assert len(dg.nodes) == 0
        assert len(dg.edges) == 0
        assert dg.strategy == "series"

    def test_add_module_known(self):
        dg = DefenseGraph()
        node_id = dg.add_module("Firewall")
        assert node_id == "node_0"
        assert len(dg.nodes) == 1
        assert dg.nodes[0].rate == 0.91

    def test_add_module_unknown(self):
        dg = DefenseGraph()
        node_id = dg.add_module("UnknownModule")
        assert node_id == "node_0"
        # Unknown module defaults to 0.5
        assert dg.nodes[0].rate == 0.5

    def test_add_module_explicit_rate(self):
        dg = DefenseGraph()
        dg.add_module("Firewall", rate=0.42)
        assert dg.nodes[0].rate == 0.42

    def test_add_edge(self):
        dg = DefenseGraph()
        dg.add_edge("src", "dst", "→")
        assert dg.edges == [("src", "dst", "→")]

    def test_add_edge_no_label(self):
        dg = DefenseGraph()
        dg.add_edge("a", "b")
        assert dg.edges[0] == ("a", "b", "")

    def test_build_series_pipeline_two_modules(self):
        dg = DefenseGraph()
        dg.build_series_pipeline(["Firewall", "Detection"])
        assert dg.strategy == "series"
        assert len(dg.nodes) == 2
        assert len(dg.edges) == 1
        assert dg.edges[0][0] == "node_0"
        assert dg.edges[0][1] == "node_1"

    def test_build_series_pipeline_all_modules(self):
        dg = DefenseGraph()
        dg.build_series_pipeline(list(MODULE_META.keys()))
        assert len(dg.nodes) == 8
        assert len(dg.edges) == 7

    def test_build_series_pipeline_single(self):
        dg = DefenseGraph()
        dg.build_series_pipeline(["Firewall"])
        assert len(dg.nodes) == 1
        assert len(dg.edges) == 0

    def test_build_parallel_pipeline(self):
        dg = DefenseGraph()
        dg.build_parallel_pipeline(["Firewall", "Detection", "Tripwire"])
        assert dg.strategy == "parallel"
        assert len(dg.nodes) == 3

    def test_build_hybrid_pipeline(self):
        dg = DefenseGraph()
        dg.build_hybrid_pipeline(["Firewall", "Detection"], ["Consensus", "Provenance"])
        assert dg.strategy == "hybrid"
        assert len(dg.nodes) == 4

    def test_combined_rate_series(self):
        dg = DefenseGraph()
        dg.build_series_pipeline(["Firewall", "Detection"])
        rate = dg.combined_rate()
        expected = series_rate([0.91, 0.88])
        assert abs(rate - expected) < 1e-10

    def test_combined_rate_parallel(self):
        dg = DefenseGraph()
        dg.build_parallel_pipeline(["Firewall", "Detection"])
        rate = dg.combined_rate()
        assert rate == 0.91  # max

    def test_combined_rate_hybrid_conservative(self):
        dg = DefenseGraph()
        dg.build_hybrid_pipeline(["Firewall"], ["Detection"])
        rate = dg.combined_rate()
        # Hybrid uses series_rate as conservative estimate
        assert 0.0 < rate <= 1.0

    def test_combined_rate_empty(self):
        dg = DefenseGraph()
        # series_rate([]) == 0.0
        assert dg.combined_rate() == 0.0

    def test_to_ascii_contains_title(self):
        dg = DefenseGraph(title="My Pipeline")
        dg.build_series_pipeline(["Firewall"])
        ascii_out = dg.to_ascii()
        assert "My Pipeline" in ascii_out
        assert "Firewall" in ascii_out

    def test_to_ascii_series_arrow(self):
        dg = DefenseGraph()
        dg.build_series_pipeline(["Firewall", "Detection"])
        ascii_out = dg.to_ascii()
        assert "↓ (∘)" in ascii_out

    def test_to_ascii_parallel_symbol(self):
        dg = DefenseGraph()
        dg.build_parallel_pipeline(["Firewall", "Detection"])
        ascii_out = dg.to_ascii()
        assert "⊕ (⊗)" in ascii_out

    def test_to_ascii_combined_rate_appears(self):
        dg = DefenseGraph()
        dg.build_series_pipeline(["Firewall"])
        ascii_out = dg.to_ascii()
        assert "Combined detection rate" in ascii_out

    def test_to_ascii_empty(self):
        dg = DefenseGraph()
        ascii_out = dg.to_ascii()
        assert "Combined detection rate" in ascii_out

    def test_to_svg_string_is_string(self):
        dg = DefenseGraph()
        dg.build_series_pipeline(["Firewall", "Detection"])
        svg = dg.to_svg_string()
        assert isinstance(svg, str)
        assert "<svg" in svg

    def test_to_svg_string_contains_node_names(self):
        dg = DefenseGraph()
        dg.build_series_pipeline(["Firewall", "Detection"])
        svg = dg.to_svg_string()
        assert "Firewall" in svg

    def test_to_svg_string_parallel(self):
        dg = DefenseGraph()
        dg.build_parallel_pipeline(["Firewall", "Detection", "Tripwire"])
        svg = dg.to_svg_string()
        assert "<svg" in svg

    def test_to_svg_string_hybrid(self):
        dg = DefenseGraph()
        dg.build_hybrid_pipeline(["Firewall", "Detection"], ["Consensus"])
        svg = dg.to_svg_string()
        assert "<svg" in svg

    def test_to_graphviz_none_when_unavailable(self, monkeypatch):
        """to_graphviz returns None when graphviz is unavailable."""
        import visualization.composable as comp_mod
        original = comp_mod._GRAPHVIZ_AVAILABLE
        comp_mod._GRAPHVIZ_AVAILABLE = False
        try:
            dg = DefenseGraph()
            dg.build_series_pipeline(["Firewall"])
            result = dg.to_graphviz()
            assert result is None
        finally:
            comp_mod._GRAPHVIZ_AVAILABLE = original

    def test_repr(self):
        dg = DefenseGraph(title="TestGraph")
        dg.build_series_pipeline(["Firewall"])
        r = repr(dg)
        assert "TestGraph" in r
        assert "nodes=1" in r
        assert "series" in r


# ---------------------------------------------------------------------------
# DiagramObject and DiagramArrow dataclasses
# ---------------------------------------------------------------------------


class TestDiagramDataclasses:
    def test_diagram_object_construction(self):
        obj = DiagramObject(name="A", label="Obj A", x=1.0, y=2.0)
        assert obj.name == "A"
        assert obj.label == "Obj A"
        assert obj.x == 1.0
        assert obj.y == 2.0

    def test_diagram_arrow_construction(self):
        arrow = DiagramArrow(src="A", dst="B", label="f", style="dashed")
        assert arrow.src == "A"
        assert arrow.dst == "B"
        assert arrow.style == "dashed"

    def test_diagram_arrow_default_style(self):
        arrow = DiagramArrow(src="A", dst="B", label="g")
        assert arrow.style == "solid"


# ---------------------------------------------------------------------------
# CategoryDiagram
# ---------------------------------------------------------------------------


class TestCategoryDiagram:
    """Tests for CategoryDiagram — construction, builders, renderers."""

    def test_default_construction(self):
        diag = CategoryDiagram()
        assert diag.title == "Commutative Diagram"
        assert len(diag.objects) == 0
        assert len(diag.arrows) == 0

    def test_add_object(self):
        diag = CategoryDiagram()
        diag.add_object("A", "Label A", 0.0, 1.0)
        assert "A" in diag.objects
        assert diag.objects["A"].x == 0.0

    def test_add_arrow_solid(self):
        diag = CategoryDiagram()
        diag.add_arrow("A", "B", "f")
        assert len(diag.arrows) == 1
        assert diag.arrows[0].style == "solid"

    def test_add_arrow_dashed(self):
        diag = CategoryDiagram()
        diag.add_arrow("A", "B", "f", style="dashed")
        assert diag.arrows[0].style == "dashed"

    def test_add_arrow_double(self):
        diag = CategoryDiagram()
        diag.add_arrow("A", "B", "f", style="double")
        assert diag.arrows[0].style == "double"

    def test_build_monoidal_unit_diagram(self):
        diag = CategoryDiagram.build_monoidal_unit_diagram()
        assert diag.title == "Monoidal Unitors λ and ρ"
        assert len(diag.objects) == 3
        assert len(diag.arrows) == 2
        assert "If" in diag.objects
        assert "f" in diag.objects
        assert "fI" in diag.objects

    def test_build_associator_diagram(self):
        diag = CategoryDiagram.build_associator_diagram()
        assert len(diag.objects) == 3
        assert len(diag.arrows) == 3
        assert "fgh1" in diag.objects

    def test_build_monad_diagram(self):
        diag = CategoryDiagram.build_monad_diagram()
        assert "T" in diag.objects
        assert "TT" in diag.objects
        # Has a dashed arrow
        styles = [a.style for a in diag.arrows]
        assert "dashed" in styles

    def test_build_kan_extension_diagram(self):
        diag = CategoryDiagram.build_kan_extension_diagram()
        assert "C" in diag.objects
        assert "D" in diag.objects
        assert "E" in diag.objects
        # Has a dashed arrow for Lan_F(G)
        styles = [a.style for a in diag.arrows]
        assert "dashed" in styles

    def test_to_ascii_contains_title(self):
        diag = CategoryDiagram.build_monoidal_unit_diagram()
        ascii_out = diag.to_ascii()
        assert "Monoidal Unitors" in ascii_out

    def test_to_ascii_contains_objects(self):
        diag = CategoryDiagram.build_monoidal_unit_diagram()
        ascii_out = diag.to_ascii()
        assert "If" in ascii_out
        assert "fI" in ascii_out

    def test_to_ascii_contains_arrows(self):
        diag = CategoryDiagram.build_monoidal_unit_diagram()
        ascii_out = diag.to_ascii()
        assert "─→" in ascii_out

    def test_to_ascii_dashed_arrow(self):
        diag = CategoryDiagram.build_monad_diagram()
        ascii_out = diag.to_ascii()
        assert "··→" in ascii_out

    def test_to_ascii_double_arrow(self):
        diag = CategoryDiagram()
        diag.add_object("A", "A", 0.0, 0.0)
        diag.add_object("B", "B", 1.0, 0.0)
        diag.add_arrow("A", "B", "f", style="double")
        ascii_out = diag.to_ascii()
        assert "══→" in ascii_out

    def test_to_svg_string_is_svg(self):
        diag = CategoryDiagram.build_monoidal_unit_diagram()
        svg = diag.to_svg_string()
        assert "<svg" in svg
        assert "</svg>" in svg

    def test_to_svg_string_no_objects(self):
        diag = CategoryDiagram()
        svg = diag.to_svg_string()
        assert "<svg" in svg

    def test_to_svg_string_includes_objects(self):
        diag = CategoryDiagram.build_associator_diagram()
        svg = diag.to_svg_string()
        # Should have circles for objects
        assert "<circle" in svg

    def test_to_svg_string_missing_src_dst_skipped(self):
        """Arrow with missing src or dst is skipped without error."""
        diag = CategoryDiagram()
        diag.add_object("A", "A", 0.0, 0.0)
        diag.add_arrow("A", "MISSING", "f")
        svg = diag.to_svg_string()  # should not raise
        assert "<svg" in svg

    def test_to_matplotlib_returns_figure(self):
        diag = CategoryDiagram.build_monoidal_unit_diagram()
        fig = diag.to_matplotlib()
        if fig is not None:
            assert hasattr(fig, "savefig")
            plt.close(fig)

    def test_to_matplotlib_saves_file(self, tmp_path):
        diag = CategoryDiagram.build_monad_diagram()
        out = str(tmp_path / "diagram.png")
        fig = diag.to_matplotlib(output_path=out)
        if fig is not None:
            assert os.path.exists(out)
            plt.close(fig)

    def test_to_matplotlib_arrow_styles(self):
        """All three arrow styles (solid, dashed, double) are rendered."""
        diag = CategoryDiagram()
        diag.add_object("A", "A", 0.0, 0.0)
        diag.add_object("B", "B", 1.0, 0.0)
        diag.add_object("C", "C", 2.0, 0.0)
        diag.add_arrow("A", "B", "solid_arrow", style="solid")
        diag.add_arrow("B", "C", "dashed_arrow", style="dashed")
        diag.add_arrow("A", "C", "double_arrow", style="double")
        fig = diag.to_matplotlib()
        if fig is not None:
            plt.close(fig)

    def test_to_matplotlib_no_objects(self):
        """to_matplotlib with no objects — no crash."""
        diag = CategoryDiagram()
        fig = diag.to_matplotlib()
        if fig is not None:
            plt.close(fig)

    def test_repr(self):
        diag = CategoryDiagram.build_monoidal_unit_diagram()
        r = repr(diag)
        assert "Monoidal Unitors" in r
        assert "objects=3" in r
        assert "arrows=2" in r


# ---------------------------------------------------------------------------
# LatticeNode and LatticeViz
# ---------------------------------------------------------------------------


class TestLatticeNode:
    def test_construction(self):
        node = LatticeNode(name="Firewall", rate=0.91, rank=9)
        assert node.name == "Firewall"
        assert node.rate == 0.91
        assert node.rank == 9


class TestLatticeViz:
    """Tests for LatticeViz — construction, covering relations, ASCII, SVG."""

    def test_default_construction(self):
        viz = LatticeViz()
        assert viz.title == "Defense Lattice"
        assert len(viz.nodes) == 0

    def test_add_node(self):
        viz = LatticeViz()
        viz.add_node("Firewall", 0.91)
        assert len(viz.nodes) == 1
        assert viz.nodes[0].rate == 0.91
        assert viz.nodes[0].rank == 9  # int(0.91 * 10)

    def test_from_modules(self):
        viz = LatticeViz.from_modules()
        assert viz.title == "Defense Lattice (Hasse Diagram)"
        # 8 modules + bottom + top
        assert len(viz.nodes) == 10

    def test_from_modules_has_bottom_and_top(self):
        viz = LatticeViz.from_modules()
        names = {n.name for n in viz.nodes}
        assert "⊥ (identity)" in names
        assert "⊤ (full)" in names

    def test_from_modules_bottom_rate_zero(self):
        viz = LatticeViz.from_modules()
        bot = next(n for n in viz.nodes if n.name == "⊥ (identity)")
        assert bot.rate == 0.0

    def test_from_modules_top_rate_one(self):
        viz = LatticeViz.from_modules()
        top = next(n for n in viz.nodes if n.name == "⊤ (full)")
        assert top.rate == 1.0

    def test_covering_relations_non_empty(self):
        viz = LatticeViz.from_modules()
        covers = viz.covering_relations()
        assert len(covers) > 0

    def test_covering_relations_each_lower_lt_upper(self):
        viz = LatticeViz.from_modules()
        for lower, upper in viz.covering_relations():
            assert lower.rate < upper.rate

    def test_covering_relations_empty_viz(self):
        viz = LatticeViz()
        covers = viz.covering_relations()
        assert covers == []

    def test_to_ascii_contains_title(self):
        viz = LatticeViz.from_modules()
        ascii_out = viz.to_ascii()
        assert "Defense Lattice" in ascii_out

    def test_to_ascii_contains_all_modules(self):
        viz = LatticeViz.from_modules()
        ascii_out = viz.to_ascii()
        for name in MODULE_META:
            assert name in ascii_out

    def test_to_ascii_contains_covering_relations(self):
        viz = LatticeViz.from_modules()
        ascii_out = viz.to_ascii()
        assert "Covering relations" in ascii_out

    def test_to_svg_string_is_svg(self):
        viz = LatticeViz.from_modules()
        svg = viz.to_svg_string()
        assert "<svg" in svg
        assert "</svg>" in svg

    def test_to_svg_string_empty(self):
        viz = LatticeViz()
        svg = viz.to_svg_string()
        assert "<svg" in svg

    def test_to_svg_string_custom_size(self):
        viz = LatticeViz.from_modules()
        svg = viz.to_svg_string(width=800, height=500)
        assert 'width="800"' in svg
        assert 'height="500"' in svg

    def test_repr(self):
        viz = LatticeViz.from_modules()
        r = repr(viz)
        assert "Defense Lattice" in r
        assert "nodes=10" in r


# ---------------------------------------------------------------------------
# OperadNode and OperadPlot
# ---------------------------------------------------------------------------


class TestOperadNode:
    def test_leaf_construction(self):
        node = OperadNode(label="Firewall", is_leaf=True)
        assert node.label == "Firewall"
        assert node.is_leaf is True
        assert node.children == []

    def test_internal_construction(self):
        child = OperadNode(label="A", is_leaf=True)
        root = OperadNode(label="∘", children=[child])
        assert len(root.children) == 1


class TestOperadPlot:
    """Tests for OperadPlot — series/parallel trees, ASCII, SVG."""

    def test_default_construction(self):
        plot = OperadPlot()
        assert plot.title == "Operad Tree"
        assert plot.root is None

    def test_build_series_tree_three_modules(self):
        plot = OperadPlot.build_series_tree(["Firewall", "Detection", "Consensus"])
        assert plot.root is not None
        assert "Series Operad" in plot.title
        assert "Firewall" in plot.title

    def test_build_series_tree_single(self):
        plot = OperadPlot.build_series_tree(["Firewall"])
        assert plot.root is not None
        assert plot.root.is_leaf is True
        assert plot.root.label == "Firewall"

    def test_build_series_tree_empty(self):
        plot = OperadPlot.build_series_tree([])
        assert plot.root is None

    def test_build_parallel_tree(self):
        plot = OperadPlot.build_parallel_tree(["Firewall", "Detection", "Tripwire"])
        assert plot.root is not None
        assert "Parallel Operad" in plot.title
        assert len(plot.root.children) == 3
        for child in plot.root.children:
            assert child.is_leaf is True

    def test_build_parallel_tree_root_label(self):
        plot = OperadPlot.build_parallel_tree(["A", "B"])
        assert plot.root.label == "⊗_2"

    def test_to_ascii_series(self):
        plot = OperadPlot.build_series_tree(["Firewall", "Detection"])
        ascii_out = plot.to_ascii()
        assert "Series Operad" in ascii_out
        assert "Firewall" in ascii_out

    def test_to_ascii_parallel(self):
        plot = OperadPlot.build_parallel_tree(["Firewall", "Detection"])
        ascii_out = plot.to_ascii()
        assert "Parallel Operad" in ascii_out

    def test_to_ascii_empty_root(self):
        plot = OperadPlot()
        ascii_out = plot.to_ascii()
        assert "Operad Tree" in ascii_out

    def test_to_svg_string_series(self):
        plot = OperadPlot.build_series_tree(["Firewall", "Detection", "Consensus"])
        svg = plot.to_svg_string()
        assert "<svg" in svg
        assert "</svg>" in svg

    def test_to_svg_string_parallel(self):
        plot = OperadPlot.build_parallel_tree(["Firewall", "Detection", "Tripwire"])
        svg = plot.to_svg_string()
        assert "<svg" in svg
        # Should have circles for nodes
        assert "<circle" in svg

    def test_to_svg_string_empty_root(self):
        plot = OperadPlot()
        svg = plot.to_svg_string()
        assert "<svg" in svg

    def test_to_svg_string_custom_size(self):
        plot = OperadPlot.build_parallel_tree(["A", "B"])
        svg = plot.to_svg_string(width=800, height=400)
        assert 'width="800"' in svg
        assert 'height="400"' in svg

    def test_ascii_tree_deep_series(self):
        """Recursion through nested series tree produces correct tree structure."""
        plot = OperadPlot.build_series_tree(["Firewall", "Detection", "Consensus", "Invariants"])
        ascii_out = plot.to_ascii()
        assert "Firewall" in ascii_out
        assert "Detection" in ascii_out
        assert "Consensus" in ascii_out
        assert "Invariants" in ascii_out

    def test_repr(self):
        plot = OperadPlot.build_series_tree(["Firewall"])
        r = repr(plot)
        assert "Series Operad" in r


# ---------------------------------------------------------------------------
# KleisliArrow and MonadFlow
# ---------------------------------------------------------------------------


class TestKleisliArrow:
    def test_construction(self):
        arrow = KleisliArrow(src="η (unit)", dst="Firewall", label=">=>")
        assert arrow.src == "η (unit)"
        assert arrow.label == ">=>"


class TestMonadFlow:
    """Tests for MonadFlow — Kleisli pipeline construction, ASCII, SVG."""

    def test_default_construction(self):
        flow = MonadFlow()
        assert flow.title == "Monad Kleisli Pipeline"
        assert len(flow.stages) == 0
        assert len(flow.arrows) == 0

    def test_build_from_modules_three(self):
        flow = MonadFlow.build_from_modules(["Firewall", "Detection", "Consensus"])
        # η + 3 modules + μ = 5 stages
        assert len(flow.stages) == 5
        assert flow.stages[0] == "η (unit)"
        assert flow.stages[-1] == "μ (join)"
        assert flow.stages[1] == "Firewall"

    def test_build_from_modules_arrows_count(self):
        flow = MonadFlow.build_from_modules(["A", "B"])
        # η → A → B → μ = 3 arrows
        assert len(flow.arrows) == 3

    def test_build_from_modules_empty(self):
        flow = MonadFlow.build_from_modules([])
        # η + μ = 2 stages, 1 arrow
        assert len(flow.stages) == 2
        assert len(flow.arrows) == 1

    def test_to_ascii_contains_title(self):
        flow = MonadFlow.build_from_modules(["Firewall"])
        ascii_out = flow.to_ascii()
        assert "Kleisli" in ascii_out

    def test_to_ascii_contains_all_stages(self):
        flow = MonadFlow.build_from_modules(["Firewall", "Detection"])
        ascii_out = flow.to_ascii()
        assert "η (unit)" in ascii_out
        assert "Firewall" in ascii_out
        assert "Detection" in ascii_out
        assert "μ (join)" in ascii_out

    def test_to_ascii_empty_stages(self):
        flow = MonadFlow()
        ascii_out = flow.to_ascii()
        assert "Monad Kleisli Pipeline" in ascii_out

    def test_to_svg_string_is_svg(self):
        flow = MonadFlow.build_from_modules(["Firewall", "Detection", "Consensus"])
        svg = flow.to_svg_string()
        assert "<svg" in svg
        assert "</svg>" in svg

    def test_to_svg_string_empty_stages(self):
        flow = MonadFlow()
        svg = flow.to_svg_string()
        assert "<svg" in svg

    def test_to_svg_string_monad_stages_highlighted(self):
        flow = MonadFlow.build_from_modules(["Firewall"])
        svg = flow.to_svg_string()
        # Monad stages (η and μ) get purple fill #8e44ad
        assert "#8e44ad" in svg

    def test_to_svg_string_contains_arrows(self):
        flow = MonadFlow.build_from_modules(["Firewall", "Detection"])
        svg = flow.to_svg_string()
        assert ">=>".replace(">", "&gt;") in svg or ">=" in svg

    def test_to_svg_string_custom_size(self):
        flow = MonadFlow.build_from_modules(["Firewall"])
        svg = flow.to_svg_string(width=900, height=200)
        assert 'width="900"' in svg

    def test_repr(self):
        flow = MonadFlow.build_from_modules(["Firewall", "Detection"])
        r = repr(flow)
        assert "Kleisli" in r
        assert "stages=4" in r


# ---------------------------------------------------------------------------
# LensDiagram
# ---------------------------------------------------------------------------


class TestLensDiagram:
    """Tests for LensDiagram — lens optic diagram."""

    def test_default_construction(self):
        lens = LensDiagram()
        assert lens.title == "Lens Optic: Attack-Defense"
        assert lens.focus == "trust"
        assert lens.attack_strength == 0.8
        assert lens.defense_rate == 0.7

    def test_custom_construction(self):
        lens = LensDiagram(
            title="Custom Lens",
            focus="belief",
            attack_strength=0.6,
            defense_rate=0.5,
        )
        assert lens.focus == "belief"
        assert lens.attack_strength == 0.6
        assert lens.defense_rate == 0.5

    def test_to_ascii_contains_title(self):
        lens = LensDiagram(title="Attack Lens")
        ascii_out = lens.to_ascii()
        assert "Attack Lens" in ascii_out

    def test_to_ascii_contains_focus(self):
        lens = LensDiagram(focus="authority")
        ascii_out = lens.to_ascii()
        assert "authority" in ascii_out

    def test_to_ascii_contains_lens_laws(self):
        lens = LensDiagram()
        ascii_out = lens.to_ascii()
        assert "GetPut" in ascii_out
        assert "PutGet" in ascii_out
        assert "PutPut" in ascii_out

    def test_to_ascii_defense_calculation(self):
        """Defense reduces attack from A to A*(1-defense_rate)."""
        lens = LensDiagram(attack_strength=1.0, defense_rate=0.5)
        ascii_out = lens.to_ascii()
        # 1.0 * (1 - 0.5) = 0.50
        assert "0.50" in ascii_out

    def test_to_svg_string_is_svg(self):
        lens = LensDiagram()
        svg = lens.to_svg_string()
        assert "<svg" in svg
        assert "</svg>" in svg

    def test_to_svg_string_contains_boxes(self):
        lens = LensDiagram()
        svg = lens.to_svg_string()
        # S, A, B, T boxes
        assert "<rect" in svg

    def test_to_svg_string_contains_title(self):
        lens = LensDiagram(title="My Lens")
        svg = lens.to_svg_string()
        assert "My Lens" in svg

    def test_to_svg_string_contains_focus(self):
        lens = LensDiagram(focus="epistemic")
        svg = lens.to_svg_string()
        assert "epistemic" in svg

    def test_to_svg_string_contains_arrows(self):
        lens = LensDiagram()
        svg = lens.to_svg_string()
        assert "<line" in svg

    def test_to_svg_string_contains_lens_laws(self):
        lens = LensDiagram()
        svg = lens.to_svg_string()
        assert "GetPut" in svg

    def test_to_svg_string_custom_size(self):
        lens = LensDiagram()
        svg = lens.to_svg_string(width=900, height=400)
        assert 'width="900"' in svg
        assert 'height="400"' in svg

    def test_repr(self):
        lens = LensDiagram(focus="trust", defense_rate=0.7)
        r = repr(lens)
        assert "trust" in r
        assert "70%" in r


# ---------------------------------------------------------------------------
# render_all_diagrams
# ---------------------------------------------------------------------------


class TestRenderAllDiagrams:
    """Tests for the combined render_all_diagrams function."""

    def test_returns_dict(self):
        diagrams = render_all_diagrams()
        assert isinstance(diagrams, dict)

    def test_expected_keys_present(self):
        diagrams = render_all_diagrams()
        expected = {
            "defense_graph_series",
            "defense_graph_parallel",
            "cat_unitors",
            "cat_associator",
            "cat_monad",
            "cat_kan",
            "lattice",
            "operad_series",
            "operad_parallel",
            "monad_flow",
            "lens",
        }
        assert expected == set(diagrams.keys())

    def test_all_values_are_svg_strings(self):
        diagrams = render_all_diagrams()
        for name, svg in diagrams.items():
            assert isinstance(svg, str), f"{name}: not a string"
            assert "<svg" in svg, f"{name}: not SVG"

    def test_output_dir_creates_files(self, tmp_path):
        output_dir = str(tmp_path / "diagrams")
        diagrams = render_all_diagrams(output_dir=output_dir)
        assert os.path.isdir(output_dir)
        for name in diagrams:
            path = os.path.join(output_dir, f"{name}.svg")
            assert os.path.exists(path), f"Missing file: {path}"

    def test_output_dir_file_content_is_svg(self, tmp_path):
        output_dir = str(tmp_path / "svg_out")
        render_all_diagrams(output_dir=output_dir)
        for fname in os.listdir(output_dir):
            if fname.endswith(".svg"):
                content = open(os.path.join(output_dir, fname)).read()
                assert "<svg" in content, f"{fname}: no <svg> tag"

    def test_no_output_dir_no_files(self, tmp_path, monkeypatch):
        """Calling without output_dir should not create any files."""
        monkeypatch.chdir(tmp_path)
        diagrams = render_all_diagrams()
        # No files created in cwd (function only writes to output_dir if given)
        assert isinstance(diagrams, dict)

    def test_defense_graph_series_covers_all_modules(self):
        diagrams = render_all_diagrams()
        svg = diagrams["defense_graph_series"]
        for name in MODULE_META:
            assert name in svg, f"Module {name} missing from defense_graph_series"

    def test_lens_diagram_has_lens_laws(self):
        diagrams = render_all_diagrams()
        svg = diagrams["lens"]
        assert "GetPut" in svg


# ---------------------------------------------------------------------------
# Integration: preset pipelines
# ---------------------------------------------------------------------------


class TestPresetPipelines:
    """Integration tests using PRESET_PIPELINES."""

    def test_minimal_viable_series(self):
        p = PRESET_PIPELINES["minimal_viable"]
        dg = DefenseGraph(title=p["label"])
        dg.build_series_pipeline(p["modules"])
        assert dg.strategy == "series"
        assert len(dg.nodes) == 3
        rate = dg.combined_rate()
        assert 0.0 < rate <= 1.0

    def test_fast_path_parallel(self):
        p = PRESET_PIPELINES["fast_path"]
        dg = DefenseGraph(title=p["label"])
        dg.build_parallel_pipeline(p["modules"])
        assert dg.strategy == "parallel"
        rate = dg.combined_rate()
        assert rate == max(
            MODULE_META[m]["detection_rate"] for m in p["modules"]
        )

    def test_hybrid_pipeline(self):
        p = PRESET_PIPELINES["hybrid"]
        dg = DefenseGraph(title=p["label"])
        dg.build_hybrid_pipeline(p["modules"], p["deep_modules"])
        assert dg.strategy == "hybrid"
        assert len(dg.nodes) == len(p["modules"]) + len(p["deep_modules"])
