\newpage

# Category-Theoretic Foundations of Defense Composition {#sec:category-theoretic-foundations}

> **Reading guide.**
> This section explores category-theoretic descriptions of CIF defenses.
> Some helpers and structural checks exist under `src/formal/`; they do not
> establish every claimed universal property, and the empirical artifacts do
> not verify these categorical laws as stated. In particular, the symmetric
> monoidal, enriched-category, pipeline-monad, Kan and optic claims below are
> scoped to the structures actually implemented rather than presented as
> completed proofs. For visualisations, see Supplement S12
> (\cref{sec:composable-visualization}).

## Defense Lattice {#sec:defense-lattice}

We equip the set of CIF defense morphisms with the **detection-rate partial
order**: $f \leq g$ iff $\mathrm{DR}(f) \leq \mathrm{DR}(g)$.  The resulting
poset extends to a **complete lattice** $(\mathcal{L}_\text{def},\,\leq,\,\wedge,\,\vee,\,\bot,\,\top)$
with:

$$\bot = \mathrm{DR}^{-1}(0),\qquad \top = \mathrm{DR}^{-1}(1),$$
\label{eq:lattice-bounds}
$$f \wedge g = \mathrm{DR}^{-1}\!\bigl(\min(\mathrm{DR}(f),\mathrm{DR}(g))\bigr),$$
\label{eq:lattice-meet}
$$f \vee g = \mathrm{DR}^{-1}\!\bigl(\max(\mathrm{DR}(f),\mathrm{DR}(g))\bigr).$$
\label{eq:lattice-join}
The independent series composition formula $\mathrm{DR}(f)+\mathrm{DR}(g)-\mathrm{DR}(f)\mathrm{DR}(g)$ is not this join: it can exceed $\max(\mathrm{DR}(f),\mathrm{DR}(g))$, so it is not the least upper bound. The poset construction above has meet and join by real-number minimum and maximum, with $\bot$ and $\top$ given by the rate extrema; it must not be conflated with series composition.

**Axiom verification** (`DefenseLattice` and `src/formal/advanced/lattice.py`):
the helper checks a finite set of representative rate examples, not all attack measurements. It is not a `verify_all_axioms()` API, and an empty example set is not a proof. Verification must be read as bounded property testing of the stated poset, not proof over the 950-attack corpus.

## Symmetric Monoidal Category {#sec:monoidal-category}

**Definition 8.1 (Defense Category).** $\mathbf{Def}$ is the category whose:
- *objects* are cognitive states $\sigma \in \Sigma$ (Part 1's Agent Cognitive State definition \cite{friedman2026cogsec1});
- *morphisms* $f : \sigma \to \sigma'$ are CIF defense operations
  (firewall, sandbox, tripwire, trust calculus, Byzantine consensus, provenance);
- *composition* is sequential pipeline application; identity is the pass-through.

**Remark 8.1 (Monoidal structure is conditional, not proved).** Parallel composition has unit, associator and symmetry candidates, but short-circuit sequential composition is not generally compatible with that tensor. The required interchange law fails: there are detection morphisms for which $(f;f')\otimes(g;g') \neq (f\otimes g);(f'\otimes g')$. Thus $\mathbf{Def}$ is not shown to be symmetric monoidal as claimed, and no `verify_monoidal_laws()` routine is cited. Detection-rate equality alone would also be insufficient to prove the required natural isomorphisms.

## Operad Defense Composition {#sec:operad}

The coloured operad $\mathcal{O}_\text{CIF}$ captures *arity-aware*
composition: a defense of arity $n$ takes $n$ partial attack signals and
returns one filtered output.

- **Series tree** — planar-tree substitution in $\mathcal{O}_\text{CIF}$
  corresponds to sequential pipeline composition (§\ref{sec:pipeline-architecture}).
- **Parallel grafting** — the grafting operation corresponds to independent
  parallel defense lanes whose outputs are max-score fused
  (§\ref{sec:composability-algebra}).

The available associativity helper exercises selected examples of these tree constructions; it does not establish every operad law or a guarantee for arbitrary defense morphisms.

## Enriched Category Over $[0,1]$ {#sec:enriched-category}

A Lawvere-metric enrichment would instead use $([0,1], \le, 1, \min)$ with
$\mathrm{Hom}(f,f)=1$ in the chosen convention, not the multiplicative interval
with $\mathrm{Hom}(f,f)=0$ as an additive triangle calculation. The current
code checks a different additive-score construction and does not establish the
stated enrichment or its Cauchy completion. Accordingly this section describes
a metric-space analogy, not a proved enriched category or an ideal defense.

## Pipeline Monad {#sec:pipeline-monad}

The defense pipeline forms a **monad** $\mathbb{T} = (T, \eta, \mu)$ over
$\mathbf{Set}$ of cognitive states:

- $T(\sigma)$ — the set of possible post-defense cognitive states reachable
  from $\sigma$ under all CIF modules;
- $\eta_\sigma : \sigma \mapsto \{\sigma\}$ — unit (no defense applied);
- $\mu_\sigma : T(T(\sigma)) \to T(\sigma)$ — join (flatten nested pipeline
  applications).

**Monad laws are not established by the current helpers.** The available
Kleisli composition and flattening operations are not shown to be one coherent
monad: the verifiers do not call $\mu$ with the same semantics used by Kleisli
composition. Consequently no `PipelineMonad` verification is claimed here.

The guarded-operation interpretation remains useful descriptively, but it is not presented as the Kleisli category of a proved monad.

## Kan Extensions Between Architectures {#sec:kan-extensions}

Different multiagent architectures induce functors $F : \mathbf{Arch}_1 \to
\mathbf{Arch}_2$ between categories of deployment configurations.  A defense
validated on architecture $\mathbf{Arch}_1$ **lifts** to $\mathbf{Arch}_2$
via the **left Kan extension** $\mathrm{Lan}_F D$:

$$\mathrm{Lan}_F D(\sigma_2) = \mathrm{colim}_{F(\sigma_1) \to \sigma_2} D(\sigma_1).$$
\label{eq:kan-extension}
The existing Kan helpers are exploratory: the left helper short-circuits when a source is missing, and the right helper uses a max-product rule rather than a demonstrated meet. No `left_kan_extension()` or `right_kan_extension()` function is cited as established here, and no preservation of detection-rate lower bounds or validated architecture transfer is asserted.

## Lens/Optic Profunctor for Attack-Defense {#sec:lens-optic}

A cognitive attack is modelled as a **lens** $(s,\,a) \to (b,\,t)$:

$$\mathrm{get}: s \to a \quad (\text{observe belief state}),$$
\label{eq:lens-get}
$$\mathrm{set}: s \times b \to t \quad (\text{overwrite belief state with adversarial content}).$$
\label{eq:lens-set}
A CIF defense module is the corresponding **profunctor optic** that mediates
the lens: it intercepts the $\mathrm{set}$ action, applies detection and
sandboxing, and returns a *residual* that either permits or blocks the write.

The lens/optic helpers provide a descriptive representation, not a proof that defense pipelines are closed under attack composition. Current checks must not be read as establishing that closure or a profunctor universal property.

## Cross-Reference to Composable Visualization {#sec:cat-theory-viz-ref}

The composable visualization engine documented in Supplement S12
(\cref{sec:composable-visualization}) provides static ASCII/SVG representations
of these categorical structures: `CategoryDiagram` renders the $\mathbf{Def}$
morphism graph, `LatticeViz` renders the detection-rate lattice, `OperadPlot`
renders composition trees, `MonadFlow` renders the Kleisli pipeline, and
`LensDiagram` renders the attack-defense optic. Separately,
`scripts/generate_composer_data.py` exports `output/data/composer_data.json`
as a language-neutral data API. Neither artifact provides an interactive web UI.
