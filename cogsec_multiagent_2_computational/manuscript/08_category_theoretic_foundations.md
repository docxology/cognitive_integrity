\\newpage

# Category-Theoretic Foundations of Defense Composition {#sec:category-theoretic-foundations}

> **Reading guide.**
> This section formalises the compositional structure of CIF defenses using
> category theory, providing the mathematical backbone for the composability
> algebra introduced in §\ref{sec:composability-algebra}. The constructions
> here are implemented in `src/formal/category_theory_advanced.py` and verified
> against empirical detection data throughout
> §\ref{sec:results}–§\ref{sec:discussion}. For visualisations of these
> structures, see Supplement S12 (\cref{sec:composable-visualization}).

## Defense Lattice {#sec:defense-lattice}

We equip the set of CIF defense morphisms with the **detection-rate partial
order**: $f \leq g$ iff $\mathrm{DR}(f) \leq \mathrm{DR}(g)$.  The resulting
poset extends to a **complete lattice** $(\mathcal{L}_\text{def},\,\leq,\,\wedge,\,\vee,\,\bot,\,\top)$
with:

$$\bot = \mathrm{DR}^{-1}(0),\qquad \top = \mathrm{DR}^{-1}(1),$$ {#eq:lattice-bounds}
$$f \wedge g = \mathrm{DR}^{-1}\!\bigl(\min(\mathrm{DR}(f),\mathrm{DR}(g))\bigr),$$ {#eq:lattice-meet}
$$f \vee g = \mathrm{DR}^{-1}\!\bigl(1 - (1-\mathrm{DR}(f))(1-\mathrm{DR}(g))\bigr).$$ {#eq:lattice-join}

The join formula $f \vee g$ is precisely the **series composition** detection
rate from Part 1, Theorem 3.1 \cite{friedman2026cogsec1}: independent
miss-events multiply, so the combined detection equals $\mathrm{DR}(f) + \mathrm{DR}(g) - \mathrm{DR}(f)\cdot\mathrm{DR}(g)$.

**Axiom verification** (`DefenseLattice`, `src/formal/category_theory_advanced.py`):
all seven standard lattice axioms (reflexivity, antisymmetry, transitivity,
existence of meet, existence of join, bottom, top) are verified empirically
over all 950-attack detection-rate measurements via `verify_all_axioms()`.

## Symmetric Monoidal Category {#sec:monoidal-category}

**Definition 8.1 (Defense Category).** $\mathbf{Def}$ is the category whose:
- *objects* are cognitive states $\sigma \in \Sigma$ (Definition 2.1, Part 1 \cite{friedman2026cogsec1});
- *morphisms* $f : \sigma \to \sigma'$ are CIF defense operations
  (firewall, sandbox, tripwire, trust calculus, Byzantine consensus, provenance);
- *composition* is sequential pipeline application; identity is the pass-through.

**Theorem 8.1 (Symmetric Monoidal Structure).** $(\mathbf{Def},\,\otimes,\, I)$
is a symmetric monoidal category, where $\otimes$ is parallel composition,
$I$ is the identity defense, and the following natural isomorphisms hold:

- **Left unitor** $\lambda_f : I \otimes f \xrightarrow{\sim} f$,
- **Right unitor** $\rho_f : f \otimes I \xrightarrow{\sim} f$,
- **Associator** $\alpha_{f,g,h} : (f \otimes g) \otimes h \xrightarrow{\sim} f \otimes (g \otimes h)$,
- **Symmetry** $\gamma_{f,g} : f \otimes g \xrightarrow{\sim} g \otimes f$,

satisfying Pentagon and Hexagon coherence equations (verified in
`verify_monoidal_laws()`, `src/formal/category_theory_advanced.py`).

*Proof sketch.* The coherence maps are all detection-rate-preserving; the
Pentagon and Hexagon equations reduce to commutativity of real-number
arithmetic. $\blacksquare$

## Operad Defense Composition {#sec:operad}

The coloured operad $\mathcal{O}_\text{CIF}$ captures *arity-aware*
composition: a defense of arity $n$ takes $n$ partial attack signals and
returns one filtered output.

- **Series tree** — planar-tree substitution in $\mathcal{O}_\text{CIF}$
  corresponds to sequential pipeline composition (§\ref{sec:pipeline-architecture}).
- **Parallel grafting** — the grafting operation corresponds to independent
  parallel defense lanes whose outputs are max-score fused
  (§\ref{sec:composability-algebra}).

Operadic associativity (`verify_operad_associativity()`) guarantees that
re-bracketing a defense pipeline never changes detection semantics.

## Enriched Category Over $[0,1]$ {#sec:enriched-category}

$\mathbf{Def}$ is enriched over the monoidal category $([0,1], \times, 1)$
(unit interval with multiplication), assigning to each hom-set the
**detection-distance**:

$$\mathbf{Def}(f,g) = \bigl|\mathrm{DR}(f) - \mathrm{DR}(g)\bigr| \in [0,1].$$ {#eq:detection-distance}

This enrichment makes $\mathbf{Def}$ a *Lawvere metric space* where distance
measures how much two defenses differ in efficacy.  The Cauchy-completion of
$\mathbf{Def}$ with respect to this metric yields the ideal defense $\top$.

## Pipeline Monad {#sec:pipeline-monad}

The defense pipeline forms a **monad** $\mathbb{T} = (T, \eta, \mu)$ over
$\mathbf{Set}$ of cognitive states:

- $T(\sigma)$ — the set of possible post-defense cognitive states reachable
  from $\sigma$ under all CIF modules;
- $\eta_\sigma : \sigma \mapsto \{\sigma\}$ — unit (no defense applied);
- $\mu_\sigma : T(T(\sigma)) \to T(\sigma)$ — join (flatten nested pipeline
  applications).

**Monad laws** (verified in `PipelineMonad`, `src/formal/category_theory_advanced.py`):
left unit $\mu \circ \eta T = \mathrm{id}$, right unit $\mu \circ T\eta = \mathrm{id}$,
associativity $\mu \circ T\mu = \mu \circ \mu T$.

The Kleisli category of $\mathbb{T}$ is precisely the category of *guarded*
CIF operations — morphisms that may conditionally block or sandbox their input.

## Kan Extensions Between Architectures {#sec:kan-extensions}

Different multiagent architectures induce functors $F : \mathbf{Arch}_1 \to
\mathbf{Arch}_2$ between categories of deployment configurations.  A defense
validated on architecture $\mathbf{Arch}_1$ **lifts** to $\mathbf{Arch}_2$
via the **left Kan extension** $\mathrm{Lan}_F D$:

$$\mathrm{Lan}_F D(\sigma_2) = \mathrm{colim}_{F(\sigma_1) \to \sigma_2} D(\sigma_1).$$ {#eq:kan-extension}

Implemented as `left_kan_extension()` / `right_kan_extension()` in
`src/formal/category_theory_advanced.py`, this provides a principled
architecture-transfer mechanism that preserves detection-rate lower bounds
(used in the cross-architecture gap analysis, §\ref{sec:architecture-gap-analysis}).

## Lens/Optic Profunctor for Attack-Defense {#sec:lens-optic}

A cognitive attack is modelled as a **lens** $(s,\,a) \to (b,\,t)$:

$$\mathrm{get}: s \to a \quad (\text{observe belief state}),$$ {#eq:lens-get}
$$\mathrm{set}: s \times b \to t \quad (\text{overwrite belief state with adversarial content}).$$ {#eq:lens-set}

A CIF defense module is the corresponding **profunctor optic** that mediates
the lens: it intercepts the $\mathrm{set}$ action, applies detection and
sandboxing, and returns a *residual* that either permits or blocks the write.

The optic representation (`CognitiveAttackLens`, `AttackDefenseOptic` in
`src/formal/category_theory_advanced.py`) enables compositional reasoning
about **attack composition**: stacking two lenses corresponds to a coordinated
two-stage attack, whose combined optic is exactly the composition of the
corresponding defense optics — ensuring that the defense pipeline is
*closed under composition* with respect to the attack model.

## Cross-Reference to Composable Visualization {#sec:cat-theory-viz-ref}

All categorical structures in this section are rendered as interactive diagrams
by the composable visualization engine documented in Supplement S12
(\cref{sec:composable-visualization}):
`CategoryDiagram` renders the $\mathbf{Def}$ morphism graph,
`LatticeViz` renders the detection-rate lattice,
`OperadPlot` renders composition trees,
`MonadFlow` renders the Kleisli pipeline,
and `LensDiagram` renders the attack-defense optic.
The visualization data is generated by `scripts/generate_composer_data.py`
into `output/data/composer_data.json`, which feeds the diagram components
listed above. An interactive web deployment is planned but not yet shipped;
the current artifact is the JSON data layer.
