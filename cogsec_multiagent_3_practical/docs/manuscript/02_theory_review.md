# The Formal Foundation: Concepts from Part 1 {#sec:theory-review}

Part 3 builds on the formal framework in Part 1. This section summarizes core definitions and theorems using the same notation as the Part 1 manuscript.

## The Adversary Hierarchy ($\Omega$) {#sec:adversary-hierarchy}

Part 1 formalized the "Scope of Threat" through a hierarchical taxonomy. This hierarchy allows precise definition of defensive scope.

* **$\Omega_1$ (External)**: The adversary controls inputs (e.g., prompt injection). The agent's internal state is intact.
* **$\Omega_2$ (Peripheral)**: The adversary controls tools or RAG data (e.g., poisoned retrieval). The agent's perception is compromised.
* **$\Omega_3$ (Agent)**: The adversary controls the agent's weights or context (e.g., identity implementation). The agent itself is untrusted.
* **$\Omega_4$ (Coordination)**: The adversary controls a subset of the swarm (e.g., Sybil agents). The consensus mechanism is under attack.
* **$\Omega_5$ (Systemic)**: The adversary controls the orchestrator or infrastructure. The system's rules are compromised.

The simulations in Part 2 show defense difficulty rising non-linearly with this hierarchy: $\Omega_1$ attacks are largely caught by surface-level filters (see Part 2 for category-level rates), while $\Omega_4$ coordination attacks need quorum- and graph-level analysis and remain structurally harder to flag than single-channel injections.

## The Trust Calculus ($T$) {#sec:trust-calculus-review}

A central contribution of Part 1 is the **Trust Calculus**, a formal system for reasoning about belief reliability. It defines Trust ($T$) not as a binary permission but as a continuous property of a belief $b$, denoted as $T(b) \in [0, 1]$.

Part 1's Trust Boundedness theorem establishes that trust must decay across delegation chains:

> **Theorem 3.1 (Trust Preservation)**: *For any delegation chain $C = \{a_1 \to a_2 \to \dots \to a_n\}$, the trust in the final output cannot exceed the trust of the weakest link, degraded by the distance from the source.*
> $$ T(result) \le \min_{i} T(a_i) \cdot \delta^{\lvert C\rvert} $$
> *where $\delta$ is the decay factor ($0 < \delta < 1$).*

This theorem provides the mathematical basis for the "Trust Decay" mechanism evaluated in Part 2. It ensures that uncertainty is preserved and amplified effectively as information travels through the network.

*In active inference terms, $\delta$ is precision decay: each hop along a delegation chain attenuates channel precision. That matches precision-weighted belief updating—the same idea as weighting sensory evidence by reliability. Part 2 (FEP.1--FEP.2) states the correspondence between CIF’s trust update rules and variational free energy for the shared generative-model setup used there.*

## The Cognitive Firewall ($\Phi$) {#sec:firewall-review}

The **Cognitive Firewall** is defined in Part 1 as a function $\Phi$ that maps inputs to decisions based on three verification layers:

1. **Syntactic Verification ($V_{syn}$)**: Checks for structural anomalies.
2. **Semantic Verification ($V_{sem}$)**: Checks for meaning-level violations.
3. **Pragmatic Verification ($V_{prag}$)**: Checks for contextual anomalies.

In the Part 2 experiments, this modular structure was shown to be the primary defense against $\Omega_1$ (External) attacks.

## The Stealth-Impact Tradeoff {#sec:stealth-impact-review}

Part 1 poses a Stealth-Impact Tradeoff as an open formalization, not a proved theorem. Detection probability can rise with divergence in particular observation models, but no universal bound follows that catastrophic attacks must be easier to detect than subtle attacks. Part 2 does not test an impact-stratified version: its corpus deliberately carries no per-sample impact label, so no such detection rate has been computed. The hypothesis remains a target for a separately labelled evaluation rather than an empirical result.

## Defense Composition {#sec:composition-review}

Finally, Part 1 defines the **Composition Algebra**, determining how output probabilities of distinct modules interact. The key result is that orthogonal defenses compose multiplicatively.

Part 2's historical parametric model reports a 96--100% design-level detection ceiling; that is not a measured field result or evidence that a stack outperforms the sum of its parts. The real architecture-agnostic multi-seed pipeline mean is 86.3%, with a different corpus and denominator. On Part 2's 100-attack ablation corpus, the full pipeline reaches 89% and Invariants alone 85%, leaving a four-percentage-point margin over the best singleton. Compose layers for coverage, not on the assumption that each contributes an independent slice.

## The Science Behind Belief Updates: Free Energy {#sec:fep-connection}

The Cognitive Integrity Framework's formal mechanisms have a deep connection to the **Free Energy Principle (FEP)**—the leading computational theory of how intelligent agents maintain coherent beliefs about their environment \cite{friston2010free}. Understanding this connection helps explain *why* CIF's defenses work, not just *that* they work.

### What Is Free Energy?

In computational neuroscience, **variational free energy** $F$ measures how well an agent's internal model $Q$ of the world matches reality:

$$F = D_\text{KL}[Q \| P] - \mathbb{E}_Q[\log P(o | s)]$$

The first term penalizes divergence from the prior; the second rewards accurate prediction of observations. Healthy cognition minimizes $F$—beliefs that minimize free energy are accurate, coherent, and resistant to manipulation.

### Attacks as Free Energy Increases

From the FEP perspective, **a cognitive attack is any intervention that forces an agent's free energy up**. Prompt injections, belief manipulation, and trust exploitation all work by injecting observations (or "observations"—fabricated messages, false context) that drive the agent's belief state $Q$ away from its prior $P$ in ways that serve the attacker's goals rather than the agent's.

CIF formalizes a related diagnostic in Part 2 (FEP.1): $\Delta F(\omega) = F(Q_\text{attacked}) - F(Q_\text{baseline})$ can flag an update when it exceeds a chosen threshold. That is not an if-and-only-if attack test: an observation model can have a small $\Delta F$ while behavior is still unsafe. A high-precision prior changes the response to a message, but does not by itself guarantee greater attack resistance.

### Trust as Precision Weighting

CIF's trust calculus (the $\delta^d$ decay) has a natural interpretation under FEP: **trust score = precision weight**. When agent $A$ receives a message from agent $B$ with trust score $T(B \to A)$, it should weight that message's evidence proportional to $T(B \to A)$, treating it as an observation with precision $\rho = T(B \to A)$. Trust decay across delegation chains ($\delta^d$) corresponds to precision attenuation in distal channels—the same mechanism that makes far-away sensory signals less reliable than proximal ones.

### The Belief Sandbox as Constrained Inference

The belief sandbox (Part 1) can be interpreted as **constrained variational inference** where the update is only accepted if $\Delta F \leq \kappa \cdot \varepsilon_\text{precision}$. That threshold is not, without a specified observation model, equivalent to a bounded Fisher–Rao radius. Part 2 supplies a separate geodesic step-budget helper, not a proof of this equivalence.

### Practical Implication for Operators

This connection is not just theoretical. It means:

1. **Emergent misalignment is difficult for per-message monitors** when each individual change is sub-threshold but the collective drift accumulates. Colony-scale monitoring is therefore one candidate response; this mechanism is not a proof that every emergent scenario minimizes $\Delta F$ per agent.
2. **Trust calibration is precision calibration**: operators who carefully calibrate trust scores are effectively setting the precision weighting of their agent network. Well-calibrated trust → robust cognition.
3. **Compromised orchestrators are a distinct verification problem**: systematic manipulation can change the agent's baseline generative model $P$ itself, not just $Q$. Out-of-band verification is therefore a candidate control, not a measured $\Omega_5$ miss-rate result; Part 2 does not publish per-access-class measured miss rates.

For the full mathematical treatment, see Part~2's theoretical-connections and information-geometry sections.

## Category-Theoretic Formalization of Defense Composition {#sec:category-theory-crossref}

Part 2's Theoretical Connections and Composability Algebra sections explore category-theoretic descriptions of defense composition. These are design languages plus executable property checks, not a full verified framework of universal guarantees.

**The Defense Category $\calD$** (Part 2, Definition CT.1): The CIF defense suite forms a category whose objects are cognitive states $\cogstate{} \in \Sigma$ and whose morphisms are detection functions $f : \cogstate{} \to \mathrm{DefenseResult}$. The composition rule formalizes *short-circuit detection*: once any module fires, subsequent modules do not override the event.

**Three structural ideas** (Part 2, CT.1–CT.3):
- **CT.1 (Category Laws)**: Short-circuit composition is designed to satisfy identity and associativity — an algebraic scaffold for multi-layer defenses.
- **CT.2 (Product Structure)**: Parallel composition uses product states and max-score fusion; the implementation does not establish a categorical universal property.
- **CT.3 (Composition Preservation)**: Architecture adapters aim to preserve short-circuit behavior; this is not a guarantee that every transformation preserves measured detection rates.

**Practical value for operators**: The categorical framing enables *type-checked composition* (incompatible modules are refused at composition time), *empirical law verification* (the `verify_category_laws()` function in Part 2's `src/formal/category_theory.py` validates the laws against randomly sampled morphism triples), and a unified framework for reasoning about series and parallel configurations. When designing a new CIF deployment, the Defense Category $\calD$ provides the structural language to specify *what it means* for two defense modules to compose correctly.

Part 2 also provides a **composable visualization engine** (`DefenseGraph`, `CategoryDiagram`, `LatticeViz`, `OperadPlot`, `MonadFlow`, `LensDiagram`) and a **composer data bundle** (`scripts/generate_composer_data.py` → `output/data/composer_data.json`) carrying each module's description and its measured detection rate and latency. There is no interactive application; an operator reads the bundle.
