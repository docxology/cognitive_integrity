"""Composable visualization engine for the Cognitive Integrity Framework.

Provides:
- DefenseGraph:    Graphviz-based DAG of any composition pipeline
- CategoryDiagram: Commutative diagram renderer for categorical constructions
- LatticeViz:      Hasse diagram of the defense lattice
- OperadPlot:      Operadic tree visualization
- MonadFlow:       Monadic pipeline visualization with Kleisli arrows
- LensDiagram:     Lens optic diagram for attack-defense pairs

All renderers produce either:
  1. An SVG/PNG via graphviz (if available), or
  2. A plain-text/ASCII fallback (always available)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# Optional graphviz import — graceful degradation
try:
    import graphviz  # type: ignore[import]
    _GRAPHVIZ_AVAILABLE = True
except ImportError:
    _GRAPHVIZ_AVAILABLE = False

# Optional matplotlib import — graceful degradation
try:
    import matplotlib  # type: ignore[import]
    import matplotlib.pyplot as plt  # type: ignore[import]
    matplotlib.use("Agg")
    _MATPLOTLIB_AVAILABLE = True
except ImportError:
    _MATPLOTLIB_AVAILABLE = False


def _escape_xml(text: str) -> str:
    """Escape the three XML-significant characters for safe embedding in SVG text nodes.

    Order matters: '&' must be escaped first so the entities introduced for
    '<' and '>' aren't themselves re-escaped.
    """
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _svg_document(
    width: int,
    height: int,
    title: str = "",
    title_y: int = 22,
    font_size: int = 13,
    bg: str = "#1a1a2e",
    title_extra: str = "",
) -> List[str]:
    """Common SVG scaffold shared by the composable diagram renderers.

    Returns the opening `<svg>` tag, a full-canvas background `<rect>`, and
    (if `title` is given) a centered title `<text>` in the shared dark-theme
    Georgia font. Callers append their own body content, then close the
    document with `lines.append("</svg>"); "\n".join(lines)`.
    """
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        f'<rect width="{width}" height="{height}" fill="{bg}"/>',
    ]
    if title:
        extra = f" {title_extra}" if title_extra else ""
        lines.append(
            f'<text x="{width // 2}" y="{title_y}" text-anchor="middle" font-family="Georgia" '
            f'font-size="{font_size}" fill="#ecf0f1"{extra}>{title}</text>'
        )
    return lines


# ---------------------------------------------------------------------------
# Module metadata (matches the 8 CIF defense modules)
# ---------------------------------------------------------------------------

MODULE_META: Dict[str, Dict[str, Any]] = {
    "Firewall": {
        "omega_class": "Injection",
        "detection_rate": 0.91,
        "color": "#e74c3c",
        "type_annotation": "CognitiveState → DefenseResult",
    },
    "Detection": {
        "omega_class": "Steganographic",
        "detection_rate": 0.88,
        "color": "#e67e22",
        "type_annotation": "CognitiveState → DefenseResult",
    },
    "Tripwire": {
        "omega_class": "Sleeper",
        "detection_rate": 0.85,
        "color": "#f39c12",
        "type_annotation": "CognitiveState → DefenseResult",
    },
    "TrustCalc": {
        "omega_class": "Social",
        "detection_rate": 0.82,
        "color": "#27ae60",
        "type_annotation": "CognitiveState → DefenseResult",
    },
    "Consensus": {
        "omega_class": "Byzantine",
        "detection_rate": 0.79,
        "color": "#2980b9",
        "type_annotation": "CognitiveState → DefenseResult",
    },
    "Provenance": {
        "omega_class": "Provenance",
        "detection_rate": 0.76,
        "color": "#8e44ad",
        "type_annotation": "CognitiveState → DefenseResult",
    },
    "Sandbox": {
        "omega_class": "Resource",
        "detection_rate": 0.73,
        "color": "#16a085",
        "type_annotation": "CognitiveState → DefenseResult",
    },
    "Invariants": {
        "omega_class": "Logic",
        "detection_rate": 0.70,
        "color": "#2c3e50",
        "type_annotation": "CognitiveState → DefenseResult",
    },
}

PRESET_PIPELINES: Dict[str, Dict[str, Any]] = {
    "full_stack": {
        "modules": list(MODULE_META.keys()),
        "strategy": "series",
        "label": "Full Stack (Series)",
    },
    "minimal_viable": {
        "modules": ["Firewall", "Detection", "Consensus"],
        "strategy": "series",
        "label": "Minimal Viable",
    },
    "fast_path": {
        "modules": ["Firewall", "Detection", "Tripwire"],
        "strategy": "parallel",
        "label": "Fast Path (Parallel)",
    },
    "hybrid": {
        "modules": ["Firewall", "Detection"],
        "deep_modules": ["Consensus", "Provenance", "Invariants"],
        "strategy": "hybrid",
        "label": "Hybrid (Fast→Deep)",
    },
}


# ---------------------------------------------------------------------------
# Combined detection rate calculators
# ---------------------------------------------------------------------------

def series_rate(rates: List[float]) -> float:
    """Combined detection rate for series composition."""
    miss = 1.0
    for r in rates:
        miss *= (1 - r)
    return 1.0 - miss


def parallel_rate(rates: List[float]) -> float:
    """Combined detection rate for parallel composition (max)."""
    return max(rates) if rates else 0.0


# ---------------------------------------------------------------------------
# 1. DefenseGraph — DAG of a composition pipeline
# ---------------------------------------------------------------------------

@dataclass
class PipelineNode:
    """A node in a defense pipeline graph."""
    module_name: str
    node_id: str
    rate: float = 0.0
    color: str = "#95a5a6"


@dataclass
class DefenseGraph:
    """Graphviz-based DAG visualization of any defense composition pipeline.

    Supports series (→), parallel (⊞), and hybrid (⊟) topologies.
    Falls back to ASCII art if graphviz is not installed.
    """

    title: str = "Defense Pipeline"
    nodes: List[PipelineNode] = field(default_factory=list)
    edges: List[Tuple[str, str, str]] = field(default_factory=list)  # (src, dst, label)
    strategy: str = "series"

    def add_module(self, name: str, rate: Optional[float] = None) -> str:
        """Add a defense module node. Returns its node ID."""
        node_id = f"node_{len(self.nodes)}"
        r = rate if rate is not None else MODULE_META.get(name, {}).get("detection_rate", 0.5)
        color = MODULE_META.get(name, {}).get("color", "#95a5a6")
        self.nodes.append(PipelineNode(module_name=name, node_id=node_id, rate=r, color=color))
        return node_id

    def add_edge(self, src: str, dst: str, label: str = "") -> None:
        self.edges.append((src, dst, label))

    def build_series_pipeline(self, module_names: List[str]) -> "DefenseGraph":
        """Build a series pipeline from a list of module names."""
        self.strategy = "series"
        prev_id: Optional[str] = None
        for name in module_names:
            node_id = self.add_module(name)
            if prev_id is not None:
                self.add_edge(prev_id, node_id, "→")
            prev_id = node_id
        return self

    def build_parallel_pipeline(self, module_names: List[str]) -> "DefenseGraph":
        """Build a parallel pipeline from a list of module names."""
        self.strategy = "parallel"
        in_id = "parallel_in"
        out_id = "parallel_out"

        if _GRAPHVIZ_AVAILABLE:
            for name in module_names:
                node_id = self.add_module(name)
                self.add_edge(in_id, node_id, "⊞")
                self.add_edge(node_id, out_id, "max")
        else:
            for name in module_names:
                node_id = self.add_module(name)
        return self

    def build_hybrid_pipeline(
        self,
        fast_modules: List[str],
        deep_modules: List[str],
    ) -> "DefenseGraph":
        """Build a hybrid (fast parallel + deep series) pipeline."""
        self.strategy = "hybrid"
        # Fast parallel stage
        fast_out = "fast_gate"
        for name in fast_modules:
            node_id = self.add_module(name)
            self.add_edge(node_id, fast_out, "⊞")
        # Deep series stage
        prev_id: str = fast_out
        for name in deep_modules:
            node_id = self.add_module(name)
            self.add_edge(prev_id, node_id, "→")
            prev_id = node_id
        return self

    def combined_rate(self) -> float:
        """Calculate the combined detection rate for this pipeline."""
        rates = [n.rate for n in self.nodes]
        if self.strategy == "series":
            return series_rate(rates)
        elif self.strategy == "parallel":
            return parallel_rate(rates)
        else:
            return series_rate(rates)  # conservative estimate

    def to_graphviz(self) -> Optional[Any]:
        """Render to a graphviz.Digraph object (if available)."""
        if not _GRAPHVIZ_AVAILABLE:
            return None

        dot = graphviz.Digraph(
            name=self.title,
            graph_attr={
                "rankdir": "LR",
                "bgcolor": "#1a1a2e",
                "fontcolor": "white",
                "label": f"{self.title}\\nCombined rate: {self.combined_rate():.1%}",
                "fontsize": "14",
            },
            node_attr={
                "style": "filled,rounded",
                "fontcolor": "white",
                "fontsize": "11",
                "shape": "box",
            },
            edge_attr={"color": "#7f8c8d", "fontcolor": "#bdc3c7"},
        )

        for node in self.nodes:
            meta = MODULE_META.get(node.module_name, {})
            label = (
                f"{node.module_name}\\n"
                f"rate={node.rate:.0%}\\n"
                f"Ω:{meta.get('omega_class', '?')}"
            )
            dot.node(node.node_id, label=label, fillcolor=node.color)

        for src, dst, lbl in self.edges:
            dot.edge(src, dst, label=lbl)

        return dot

    def to_ascii(self) -> str:
        """Render pipeline as ASCII art (always available)."""
        lines = [f"┌─ {self.title} [{self.strategy.upper()}] ─┐"]
        rates = []
        for i, node in enumerate(self.nodes):
            bar = "█" * int(node.rate * 20)
            lines.append(f"  [{node.node_id}] {node.module_name:<15} {bar:<20} {node.rate:.0%}")
            if i < len(self.nodes) - 1:
                if self.strategy == "series":
                    lines.append("         ↓ (∘)")
                else:
                    lines.append("         ⊕ (⊗)")
            rates.append(node.rate)
        combined = self.combined_rate()
        lines.append(f"└─ Combined detection rate: {combined:.1%} ─┘")
        return "\n".join(lines)

    def to_svg_string(self) -> str:
        """Render to SVG string (via graphviz or ASCII embedded in SVG)."""
        dot = self.to_graphviz()
        if dot is not None:
            try:
                return dot.pipe(format="svg").decode("utf-8")
            except Exception:
                pass
        # SVG wrapping ASCII fallback
        ascii_art = self.to_ascii()
        lines = ascii_art.split("\n")
        height = len(lines) * 18 + 20
        svg_lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="600" height="{height}">',
            '<rect width="600" height="100%" fill="#1a1a2e"/>',
        ]
        for i, line in enumerate(lines):
            escaped = _escape_xml(line)
            svg_lines.append(
                f'<text x="10" y="{20 + i * 18}" font-family="monospace" '
                f'font-size="13" fill="#ecf0f1">{escaped}</text>'
            )
        svg_lines.append("</svg>")
        return "\n".join(svg_lines)

    def __repr__(self) -> str:
        return f"DefenseGraph({self.title!r}, nodes={len(self.nodes)}, strategy={self.strategy!r})"


# ---------------------------------------------------------------------------
# 2. CategoryDiagram — commutative diagram renderer
# ---------------------------------------------------------------------------

@dataclass
class DiagramObject:
    name: str
    label: str
    x: float = 0.0
    y: float = 0.0


@dataclass
class DiagramArrow:
    src: str
    dst: str
    label: str
    style: str = "solid"  # "solid" | "dashed" | "double"


@dataclass
class CategoryDiagram:
    """Commutative diagram renderer for categorical constructions.

    Renders objects as nodes and morphisms as labeled arrows.
    Supports matplotlib rendering and ASCII fallback.
    """

    title: str = "Commutative Diagram"
    objects: Dict[str, DiagramObject] = field(default_factory=dict)
    arrows: List[DiagramArrow] = field(default_factory=list)

    def add_object(self, name: str, label: str, x: float, y: float) -> None:
        self.objects[name] = DiagramObject(name=name, label=label, x=x, y=y)

    def add_arrow(self, src: str, dst: str, label: str, style: str = "solid") -> None:
        self.arrows.append(DiagramArrow(src=src, dst=dst, label=label, style=style))

    @classmethod
    def build_monoidal_unit_diagram(cls) -> "CategoryDiagram":
        """Build the left/right unitor commutative diagram."""
        diag = cls(title="Monoidal Unitors λ and ρ")
        diag.add_object("If", "I ⊗ f", 0.0, 1.0)
        diag.add_object("f", "f", 1.0, 1.0)
        diag.add_object("fI", "f ⊗ I", 2.0, 1.0)
        diag.add_arrow("If", "f", "λ_f (left unitor)")
        diag.add_arrow("fI", "f", "ρ_f (right unitor)")
        return diag

    @classmethod
    def build_associator_diagram(cls) -> "CategoryDiagram":
        """Build the associator pentagon diagram."""
        diag = cls(title="Associator α: (f⊗g)⊗h ≅ f⊗(g⊗h)")
        diag.add_object("fgh1", "(f⊗g)⊗h", 0.0, 0.0)
        diag.add_object("fgh2", "f⊗(g⊗h)", 2.0, 0.0)
        diag.add_object("fg", "f⊗g", 1.0, 1.0)
        diag.add_arrow("fgh1", "fgh2", "α_{f,g,h}")
        diag.add_arrow("fgh1", "fg", "id_f ⊗ α")
        diag.add_arrow("fg", "fgh2", "α ⊗ id_h")
        return diag

    @classmethod
    def build_monad_diagram(cls) -> "CategoryDiagram":
        """Build the monad unit/counit square."""
        diag = cls(title="Monad Laws: η and μ")
        diag.add_object("T", "T", 0.0, 1.0)
        diag.add_object("TT", "T²", 1.0, 1.0)
        diag.add_object("T2", "T", 1.0, 0.0)
        diag.add_arrow("T", "TT", "η (unit)")
        diag.add_arrow("TT", "T2", "μ (join)")
        diag.add_arrow("T", "T2", "id_T", style="dashed")
        return diag

    @classmethod
    def build_kan_extension_diagram(cls) -> "CategoryDiagram":
        """Build the Kan extension universal property diagram."""
        diag = cls(title="Kan Extension: Lan_F(G)")
        diag.add_object("C", "C", 0.0, 1.0)
        diag.add_object("D", "D", 2.0, 1.0)
        diag.add_object("E", "DefenseCategory", 1.0, 0.0)
        diag.add_arrow("C", "D", "F (functor)")
        diag.add_arrow("C", "E", "G")
        diag.add_arrow("D", "E", "Lan_F(G)", style="dashed")
        return diag

    def to_matplotlib(self, output_path: Optional[str] = None) -> Optional[Any]:
        """Render to matplotlib figure (if available)."""
        if not _MATPLOTLIB_AVAILABLE:
            return None

        fig, ax = plt.subplots(1, 1, figsize=(8, 5))
        ax.set_facecolor("#1a1a2e")
        fig.patch.set_facecolor("#1a1a2e")
        ax.set_title(self.title, color="white", fontsize=14, pad=15)
        ax.axis("off")

        # Plot objects
        for name, obj in self.objects.items():
            circle = plt.Circle((obj.x, obj.y), 0.15, color="#3498db", zorder=5)
            ax.add_patch(circle)
            ax.text(
                obj.x, obj.y + 0.25, obj.label,
                ha="center", va="bottom", color="white", fontsize=11,
                fontweight="bold",
            )

        # Plot arrows
        for arrow in self.arrows:
            if arrow.src not in self.objects or arrow.dst not in self.objects:
                continue
            sx, sy = self.objects[arrow.src].x, self.objects[arrow.src].y
            dx, dy = self.objects[arrow.dst].x, self.objects[arrow.dst].y
            ls = "--" if arrow.style == "dashed" else "-"
            ax.annotate(
                "",
                xy=(dx, dy), xytext=(sx, sy),
                arrowprops=dict(
                    arrowstyle="->", color="#e74c3c" if arrow.style == "double" else "#2ecc71",
                    lw=2, linestyle=ls,
                ),
            )
            mx, my = (sx + dx) / 2, (sy + dy) / 2
            ax.text(
                mx, my + 0.1, arrow.label,
                ha="center", va="bottom", color="#f39c12", fontsize=9, style="italic",
            )

        # Set axis limits with padding
        if self.objects:
            xs = [o.x for o in self.objects.values()]
            ys = [o.y for o in self.objects.values()]
            ax.set_xlim(min(xs) - 0.5, max(xs) + 0.5)
            ax.set_ylim(min(ys) - 0.5, max(ys) + 0.8)

        if output_path:
            fig.savefig(output_path, bbox_inches="tight", facecolor=fig.get_facecolor())

        return fig

    def to_ascii(self) -> str:
        """Render commutative diagram as ASCII art."""
        lines = [f"=== {self.title} ==="]
        for name, obj in self.objects.items():
            lines.append(f"  [{name}] {obj.label}  @ ({obj.x:.1f}, {obj.y:.1f})")
        lines.append("")
        for arrow in self.arrows:
            style_map = {"solid": "─→", "dashed": "··→", "double": "══→"}
            s = style_map.get(arrow.style, "─→")
            lines.append(f"  {arrow.src} {s} {arrow.dst}   [{arrow.label}]")
        return "\n".join(lines)

    def to_svg_string(self) -> str:
        """Render to SVG string."""
        if self.objects:
            xs = [o.x for o in self.objects.values()]
            ys = [o.y for o in self.objects.values()]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
        else:
            min_x, max_x, min_y, max_y = 0, 2, 0, 2

        scale = 120
        pad = 80
        width = int((max_x - min_x) * scale) + 2 * pad + 200
        height = int((max_y - min_y) * scale) + 2 * pad + 80

        def tx(x: float) -> int:
            return int((x - min_x) * scale) + pad

        def ty(y: float) -> int:
            return height - (int((y - min_y) * scale) + pad) - 40

        lines = _svg_document(
            width, height, self.title, title_y=25, font_size=15,
            title_extra='font-style="italic"',
        )

        # Draw arrows first (behind nodes)
        for arrow in self.arrows:
            if arrow.src not in self.objects or arrow.dst not in self.objects:
                continue
            sx, sy = tx(self.objects[arrow.src].x), ty(self.objects[arrow.src].y)
            dx, dy = tx(self.objects[arrow.dst].x), ty(self.objects[arrow.dst].y)
            color = "#2ecc71" if arrow.style != "double" else "#e74c3c"
            dash = "stroke-dasharray='5,5'" if arrow.style == "dashed" else ""
            lines.append(
                f'<line x1="{sx}" y1="{sy}" x2="{dx}" y2="{dy}" '
                f'stroke="{color}" stroke-width="2" {dash} '
                f'marker-end="url(#arrowhead)"/>'
            )
            mx, my = (sx + dx) // 2, (sy + dy) // 2
            escaped = _escape_xml(arrow.label)
            lines.append(
                f'<text x="{mx}" y="{my - 8}" text-anchor="middle" font-family="Georgia" '
                f'font-size="11" fill="#f39c12" font-style="italic">{escaped}</text>'
            )

        # Arrow head marker
        lines.insert(2,
            '<defs><marker id="arrowhead" markerWidth="10" markerHeight="7" '
            'refX="10" refY="3.5" orient="auto">'
            '<polygon points="0 0, 10 3.5, 0 7" fill="#7f8c8d"/></marker></defs>'
        )

        # Draw nodes
        for name, obj in self.objects.items():
            x, y = tx(obj.x), ty(obj.y)
            escaped = obj.label.replace("⊗", "⊗").replace("≅", "≅")
            lines.append(
                f'<circle cx="{x}" cy="{y}" r="22" fill="#2980b9" stroke="#3498db" stroke-width="2"/>'  # noqa: E501
            )
            lines.append(
                f'<text x="{x}" y="{y + 4}" text-anchor="middle" font-family="Georgia" '
                f'font-size="12" fill="white" font-style="italic">{escaped}</text>'
            )

        lines.append("</svg>")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return (
            f"CategoryDiagram({self.title!r}, "
            f"objects={len(self.objects)}, arrows={len(self.arrows)})"
        )


# ---------------------------------------------------------------------------
# 3. LatticeViz — Hasse diagram of the defense lattice
# ---------------------------------------------------------------------------

@dataclass
class LatticeNode:
    name: str
    rate: float
    rank: int  # 0 = bottom, higher = closer to top


@dataclass
class LatticeViz:
    """Hasse diagram of the defense lattice.

    Orders morphisms by detection rate and draws covering relations.
    """

    title: str = "Defense Lattice"
    nodes: List[LatticeNode] = field(default_factory=list)

    def add_node(self, name: str, rate: float) -> None:
        self.nodes.append(LatticeNode(name=name, rate=rate, rank=int(rate * 10)))

    @classmethod
    def from_modules(cls) -> "LatticeViz":
        """Build from all 8 CIF modules."""
        viz = cls(title="Defense Lattice (Hasse Diagram)")
        viz.add_node("⊥ (identity)", 0.0)
        for name, meta in MODULE_META.items():
            viz.add_node(name, meta["detection_rate"])
        viz.add_node("⊤ (full)", 1.0)
        return viz

    def covering_relations(self) -> List[Tuple[LatticeNode, LatticeNode]]:
        """Compute Hasse covering relations (immediate successors only)."""
        sorted_nodes = sorted(self.nodes, key=lambda n: n.rate)
        covers: List[Tuple[LatticeNode, LatticeNode]] = []
        for i, lower in enumerate(sorted_nodes):
            for upper in sorted_nodes[i + 1:]:
                # covering: no intermediate element
                intermediate = any(
                    lower.rate < mid.rate < upper.rate
                    for mid in sorted_nodes
                    if mid is not lower and mid is not upper
                )
                if not intermediate:
                    covers.append((lower, upper))
                    break  # only immediate cover
        return covers

    def to_ascii(self) -> str:
        sorted_nodes = sorted(self.nodes, key=lambda n: n.rate, reverse=True)
        lines = [f"=== {self.title} ==="]
        for node in sorted_nodes:
            bar = "█" * int(node.rate * 30)
            lines.append(f"  {node.name:<20} {bar:<30} {node.rate:.1%}")
        lines.append("\nCovering relations (a < b means a is directly below b):")
        for a, b in self.covering_relations():
            lines.append(f"  {a.name} < {b.name}")
        return "\n".join(lines)

    def to_svg_string(self, width: int = 600, height: int = 400) -> str:
        """Render Hasse diagram as SVG."""
        sorted_nodes = sorted(self.nodes, key=lambda n: n.rate)
        n = len(sorted_nodes)
        if n == 0:
            return '<svg xmlns="http://www.w3.org/2000/svg" width="600" height="200"/>'

        # Assign positions
        positions: Dict[str, Tuple[int, int]] = {}
        for i, node in enumerate(sorted_nodes):
            x = 50 + (i * (width - 100) // max(n - 1, 1))
            y = height - 50 - int(node.rate * (height - 100))
            positions[node.name] = (x, y)

        covers = self.covering_relations()
        lines = _svg_document(width, height, self.title, title_y=22, font_size=14)

        # Cover edges
        for a, b in covers:
            if a.name not in positions or b.name not in positions:
                continue
            ax, ay = positions[a.name]
            bx, by = positions[b.name]
            lines.append(
                f'<line x1="{ax}" y1="{ay}" x2="{bx}" y2="{by}" '
                f'stroke="#7f8c8d" stroke-width="1.5" stroke-dasharray="4,2"/>'
            )

        # Nodes
        for node in sorted_nodes:
            if node.name not in positions:
                continue
            x, y = positions[node.name]
            shade = int(node.rate * 200) + 30
            fill = f"rgb(30,{shade},{shade//2 + 50})"
            escaped = _escape_xml(node.name)
            lines.append(
                f'<circle cx="{x}" cy="{y}" r="18" fill="{fill}" stroke="#3498db" stroke-width="1.5"/>'  # noqa: E501
            )
            short = escaped[:6] + "…" if len(escaped) > 8 else escaped
            lines.append(
                f'<text x="{x}" y="{y + 4}" text-anchor="middle" font-family="monospace" '
                f'font-size="9" fill="white">{short}</text>'
            )
            lines.append(
                f'<text x="{x}" y="{y + 28}" text-anchor="middle" font-family="monospace" '
                f'font-size="8" fill="#95a5a6">{node.rate:.0%}</text>'
            )

        lines.append("</svg>")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"LatticeViz({self.title!r}, nodes={len(self.nodes)})"


# ---------------------------------------------------------------------------
# 4. OperadPlot — operadic tree visualization
# ---------------------------------------------------------------------------

@dataclass
class OperadNode:
    label: str
    children: List["OperadNode"] = field(default_factory=list)
    is_leaf: bool = False


@dataclass
class OperadPlot:
    """Operadic tree visualization.

    Renders series composition as a planar tree and parallel composition
    as a branching tree with a common root.
    """

    title: str = "Operad Tree"
    root: Optional[OperadNode] = None

    @classmethod
    def build_series_tree(cls, module_names: List[str]) -> "OperadPlot":
        """Build a planar tree for series composition."""
        plot = cls(title=f"Series Operad: {' ∘ '.join(reversed(module_names))}")
        if not module_names:
            return plot
        # Right-spine tree
        def build(names: List[str]) -> OperadNode:
            if len(names) == 1:
                return OperadNode(label=names[0], is_leaf=True)
            return OperadNode(
                label="∘",
                children=[build(names[:1]), build(names[1:])],
            )
        plot.root = build(module_names)
        return plot

    @classmethod
    def build_parallel_tree(cls, module_names: List[str]) -> "OperadPlot":
        """Build a branching tree for parallel composition."""
        plot = cls(title=f"Parallel Operad: ⊗({', '.join(module_names)})")
        leaves = [OperadNode(label=n, is_leaf=True) for n in module_names]
        plot.root = OperadNode(label=f"⊗_{len(module_names)}", children=leaves)
        return plot

    def _ascii_tree(self, node: OperadNode, prefix: str = "", is_last: bool = True) -> str:
        connector = "└── " if is_last else "├── "
        result = prefix + connector + node.label + "\n"
        child_prefix = prefix + ("    " if is_last else "│   ")
        for i, child in enumerate(node.children):
            result += self._ascii_tree(child, child_prefix, i == len(node.children) - 1)
        return result

    def to_ascii(self) -> str:
        lines = [f"=== {self.title} ==="]
        if self.root:
            lines.append(self._ascii_tree(self.root))
        return "\n".join(lines)

    def _svg_tree(
        self,
        node: OperadNode,
        x: float,
        y: float,
        x_spread: float,
        level_height: float,
        lines: List[str],
    ) -> None:
        """Recursively render tree nodes into SVG lines list."""
        fill = "#27ae60" if node.is_leaf else "#2980b9"
        label = _escape_xml(node.label)
        lines.append(
            f'<circle cx="{int(x)}" cy="{int(y)}" r="20" fill="{fill}" stroke="#ecf0f1" stroke-width="1.5"/>'  # noqa: E501
        )
        short = label[:5] + "…" if len(label) > 7 else label
        lines.append(
            f'<text x="{int(x)}" y="{int(y) + 4}" text-anchor="middle" font-family="monospace" '
            f'font-size="9" fill="white">{short}</text>'
        )

        n = len(node.children)
        if n == 0:
            return
        child_spread = x_spread / max(n, 1)
        child_x_start = x - x_spread / 2 + child_spread / 2
        for i, child in enumerate(node.children):
            cx = child_x_start + i * child_spread
            cy = y + level_height
            lines.append(
                f'<line x1="{int(x)}" y1="{int(y) + 20}" x2="{int(cx)}" y2="{int(cy) - 20}" '
                f'stroke="#7f8c8d" stroke-width="1.5"/>'
            )
            self._svg_tree(child, cx, cy, child_spread, level_height, lines)

    def to_svg_string(self, width: int = 600, height: int = 350) -> str:
        lines = _svg_document(width, height, self.title, title_y=22, font_size=13)
        if self.root:
            self._svg_tree(self.root, width / 2, 60, width - 80, 80, lines)
        lines.append("</svg>")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"OperadPlot({self.title!r})"


# ---------------------------------------------------------------------------
# 5. MonadFlow — monadic pipeline with Kleisli arrows
# ---------------------------------------------------------------------------

@dataclass
class KleisliArrow:
    src: str
    dst: str
    label: str  # e.g. ">=> Detection"


@dataclass
class MonadFlow:
    """Monadic pipeline visualization with Kleisli arrows.

    Shows the Kleisli composition chain (f >=> g >=> h …) as a flow
    diagram, with η and μ explicitly labelled.
    """

    title: str = "Monad Kleisli Pipeline"
    stages: List[str] = field(default_factory=list)
    arrows: List[KleisliArrow] = field(default_factory=list)

    @classmethod
    def build_from_modules(cls, module_names: List[str]) -> "MonadFlow":
        flow = cls(title=f"Kleisli: η >{' >=> '.join(module_names)}")
        flow.stages = ["η (unit)"] + module_names + ["μ (join)"]
        for i in range(len(flow.stages) - 1):
            flow.arrows.append(KleisliArrow(
                src=flow.stages[i],
                dst=flow.stages[i + 1],
                label=">=>",
            ))
        return flow

    def to_ascii(self) -> str:
        lines = [f"=== {self.title} ==="]
        for i, stage in enumerate(self.stages):
            prefix = "  " if i == 0 else "  "
            lines.append(f"{prefix}┌─{stage}─┐")
            if i < len(self.stages) - 1:
                lines.append("      │ >==>")
        return "\n".join(lines)

    def to_svg_string(self, width: int = 700, height: int = 160) -> str:
        n = len(self.stages)
        if n == 0:
            return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"/>'

        pad = 60
        step = (width - 2 * pad) // max(n - 1, 1)

        lines = _svg_document(width, height, self.title, title_y=20, font_size=13)

        cy = height // 2 + 10

        for i, stage in enumerate(self.stages):
            x = pad + i * step
            is_monad = stage.startswith("η") or stage.startswith("μ")
            fill = "#8e44ad" if is_monad else "#2980b9"
            escaped = _escape_xml(stage)
            lines.append(
                f'<rect x="{x - 40}" y="{cy - 22}" width="80" height="44" rx="8" '
                f'fill="{fill}" stroke="#ecf0f1" stroke-width="1.5"/>'
            )
            short = escaped[:8] + "…" if len(escaped) > 10 else escaped
            lines.append(
                f'<text x="{x}" y="{cy + 5}" text-anchor="middle" font-family="monospace" '
                f'font-size="10" fill="white">{short}</text>'
            )

            if i < n - 1:
                x2 = pad + (i + 1) * step
                lines.append(
                    f'<line x1="{x + 40}" y1="{cy}" x2="{x2 - 40}" y2="{cy}" '
                    f'stroke="#2ecc71" stroke-width="2" marker-end="url(#mf_arrow)"/>'
                )
                mx = (x + 40 + x2 - 40) // 2
                lines.append(
                    f'<text x="{mx}" y="{cy - 10}" text-anchor="middle" font-family="monospace" '
                    f'font-size="9" fill="#f39c12">&gt;=&gt;</text>'
                )

        lines.insert(2,
            '<defs><marker id="mf_arrow" markerWidth="8" markerHeight="6" '
            'refX="8" refY="3" orient="auto">'
            '<polygon points="0 0, 8 3, 0 6" fill="#2ecc71"/></marker></defs>'
        )

        lines.append("</svg>")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"MonadFlow({self.title!r}, stages={len(self.stages)})"


# ---------------------------------------------------------------------------
# 6. LensDiagram — lens optic diagram for attack-defense pairs
# ---------------------------------------------------------------------------

@dataclass
class LensDiagram:
    """Lens optic diagram for a cognitive attack-defense pair.

    Visualizes:
      - get: S → A  (attacker observes belief state)
      - set: (S, B) → T  (attacker/defender modifies belief state)
      - defense: A → B  (defense transforms the view)
    """

    title: str = "Lens Optic: Attack-Defense"
    focus: str = "trust"
    attack_strength: float = 0.8
    defense_rate: float = 0.7

    def to_ascii(self) -> str:
        lines = [
            f"=== {self.title} ===",
            f"  Focus belief: '{self.focus}'",
            "",
            "  ┌────────────────── S (CognitiveState) ──────────────────┐",
            f"  │  get ──────→  A (belief['{self.focus}'])                │",
            "  │  set ←──────  B (defense-filtered A)                   │",
            "  └────────────────────────────────────────────────────────┘",
            "",
            f"  Attacker: get({self.focus}) = {self.attack_strength:.2f}  [manipulation attempt]",
            f"  Defender: reduces effective A from {self.attack_strength:.2f} "
            f"to {self.attack_strength * (1 - self.defense_rate):.2f}",
            "",
            "  Lens laws:",
            "    ✓ GetPut: set(s, get(s)) = s",
            "    ✓ PutGet: get(set(s, v)) = v",
            "    ✓ PutPut: set(set(s, v₁), v₂) = set(s, v₂)",
        ]
        return "\n".join(lines)

    def to_svg_string(self, width: int = 700, height: int = 340) -> str:
        lines = _svg_document(width, height, self.title, title_y=28, font_size=15)
        lines += [
            '<defs><marker id="lens_arrow" markerWidth="8" markerHeight="6" '
            'refX="8" refY="3" orient="auto">'
            '<polygon points="0 0, 8 3, 0 6" fill="#e74c3c"/></marker>',
            '<marker id="def_arrow" markerWidth="8" markerHeight="6" '
            'refX="8" refY="3" orient="auto">'
            '<polygon points="0 0, 8 3, 0 6" fill="#2ecc71"/></marker></defs>',
        ]

        # Boxes: S, A, B, T
        boxes = [
            (80,  140, "S", "CognitiveState", "#2c3e50"),
            (280, 80,  "A", f"belief['{self.focus}']", "#c0392b"),
            (280, 220, "B", "defended belief", "#27ae60"),
            (520, 140, "T", "ModifiedState", "#2c3e50"),
        ]
        for bx, by, label, sublabel, fill in boxes:
            escaped_sub = _escape_xml(sublabel)
            lines.append(
                f'<rect x="{bx - 60}" y="{by - 28}" width="120" height="56" rx="10" '
                f'fill="{fill}" stroke="#ecf0f1" stroke-width="1.5"/>'
            )
            lines.append(
                f'<text x="{bx}" y="{by}" text-anchor="middle" font-family="Georgia" '
                f'font-size="16" fill="white" font-weight="bold">{label}</text>'
            )
            lines.append(
                f'<text x="{bx}" y="{by + 18}" text-anchor="middle" font-family="monospace" '
                f'font-size="9" fill="#bdc3c7">{escaped_sub}</text>'
            )

        # Arrows
        arrows_data = [
            (140, 130, 220, 90, "#e74c3c", "lens_arrow", "get"),
            (140, 165, 220, 232, "#e74c3c", "lens_arrow", "view"),
            (340, 80, 460, 130, "#27ae60", "def_arrow", "defense →"),
            (340, 220, 460, 168, "#27ae60", "def_arrow", "put ←"),
            (220, 95, 220, 215, "#f39c12", "def_arrow", f"rate={self.defense_rate:.0%}"),
        ]
        for ax1, ay1, ax2, ay2, color, marker, label in arrows_data:
            lines.append(
                f'<line x1="{ax1}" y1="{ay1}" x2="{ax2}" y2="{ay2}" '
                f'stroke="{color}" stroke-width="2" marker-end="url(#{marker})"/>'
            )
            mx, my = (ax1 + ax2) // 2, (ay1 + ay2) // 2
            lines.append(
                f'<text x="{mx}" y="{my - 6}" text-anchor="middle" font-family="monospace" '
                f'font-size="9" fill="#f39c12">{label}</text>'
            )

        # Lens laws
        laws = ["✓ GetPut: set(s, get(s)) = s", "✓ PutGet: get(set(s,v)) = v", "✓ PutPut: set(set(s,v₁),v₂) = set(s,v₂)"]  # noqa: E501
        for i, law in enumerate(laws):
            escaped = _escape_xml(law)
            lines.append(
                f'<text x="20" y="{290 + i * 16}" font-family="monospace" '
                f'font-size="10" fill="#2ecc71">{escaped}</text>'
            )

        lines.append("</svg>")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"LensDiagram(focus={self.focus!r}, defense_rate={self.defense_rate:.0%})"


# ---------------------------------------------------------------------------
# Combined SVG report
# ---------------------------------------------------------------------------

def render_all_diagrams(output_dir: Optional[str] = None) -> Dict[str, str]:
    """Render all diagram types and return their SVG strings.

    Args:
        output_dir: If provided, write SVG files to this directory.

    Returns:
        Dict mapping diagram name → SVG string.
    """
    import os

    diagrams: Dict[str, str] = {}

    # Defense graph — full stack
    dg = DefenseGraph(title="Full-Stack Defense Pipeline")
    dg.build_series_pipeline(list(MODULE_META.keys()))
    diagrams["defense_graph_series"] = dg.to_svg_string()

    # Parallel graph
    dg_par = DefenseGraph(title="Fast-Path Parallel Pipeline")
    dg_par.build_parallel_pipeline(["Firewall", "Detection", "Tripwire"])
    diagrams["defense_graph_parallel"] = dg_par.to_svg_string()

    # Category diagrams
    for name, builder in [
        ("cat_unitors", CategoryDiagram.build_monoidal_unit_diagram),
        ("cat_associator", CategoryDiagram.build_associator_diagram),
        ("cat_monad", CategoryDiagram.build_monad_diagram),
        ("cat_kan", CategoryDiagram.build_kan_extension_diagram),
    ]:
        diag = builder()
        diagrams[name] = diag.to_svg_string()

    # Lattice
    lv = LatticeViz.from_modules()
    diagrams["lattice"] = lv.to_svg_string()

    # Operad trees
    diagrams["operad_series"] = OperadPlot.build_series_tree(
        ["Firewall", "Detection", "Consensus"]
    ).to_svg_string()
    diagrams["operad_parallel"] = OperadPlot.build_parallel_tree(
        ["Firewall", "Detection", "Tripwire"]
    ).to_svg_string()

    # Monad flow
    diagrams["monad_flow"] = MonadFlow.build_from_modules(
        ["Firewall", "Detection", "Consensus"]
    ).to_svg_string()

    # Lens
    diagrams["lens"] = LensDiagram(
        title="Trust-Belief Lens: Attack-Defense",
        focus="trust",
        attack_strength=0.8,
        defense_rate=0.7,
    ).to_svg_string()

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        for name, svg in diagrams.items():
            path = os.path.join(output_dir, f"{name}.svg")
            with open(path, "w", encoding="utf-8") as f:
                f.write(svg)

    return diagrams


__all__ = [
    "MODULE_META",
    "PRESET_PIPELINES",
    "series_rate",
    "parallel_rate",
    "DefenseGraph",
    "PipelineNode",
    "CategoryDiagram",
    "DiagramObject",
    "DiagramArrow",
    "LatticeViz",
    "LatticeNode",
    "OperadPlot",
    "OperadNode",
    "MonadFlow",
    "KleisliArrow",
    "LensDiagram",
    "render_all_diagrams",
]
