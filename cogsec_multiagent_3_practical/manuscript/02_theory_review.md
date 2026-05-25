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

The formal definition of Trust Update (Theorem 3.1 in Part 1) establishes that trust must decay across delegation chains:

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

Part 1 provides a theoretical bound on attack performance, formalized as the Stealth-Impact Tradeoff.

> **Stealth-Impact Tradeoff**: *For a given defense sensitivity $\epsilon$, the probability of detection $P(d)$ approaches 1 as the divergence of the attack behavior from the baseline increases.*

This formalism suggests that catastrophic attacks are inherently easier to detect than subtle attacks. Part 2's data consistently validated this: High-impact attacks were detected 98% of the time, while low-impact attacks were detected only 74% of the time.

## Defense Composition {#sec:composition-review}

Finally, Part 1 defines the **Composition Algebra**, determining how output probabilities of distinct modules interact. The key result is that orthogonal defenses compose multiplicatively.

This "Swiss Cheese Model" was empirically validated in Part 2, where the full stack (94% overall detection, 95% CI: [0.92, 0.96]) significantly outperformed the sum of its parts.

## The Science Behind Belief Updates: Free Energy {#sec:fep-connection}

The Cognitive Integrity Framework's formal mechanisms have a deep connection to the **Free Energy Principle (FEP)**—the leading computational theory of how intelligent agents maintain coherent beliefs about their environment \cite{friston2010free}. Understanding this connection helps explain *why* CIF's defenses work, not just *that* they work.

### What Is Free Energy?

In computational neuroscience, **variational free energy** $F$ measures how well an agent's internal model $Q$ of the world matches reality:

$$F = D_\text{KL}[Q \| P] - \mathbb{E}_Q[\log P(o | s)]$$

The first term penalizes divergence from the prior; the second rewards accurate prediction of observations. Healthy cognition minimizes $F$—beliefs that minimize free energy are accurate, coherent, and resistant to manipulation.

### Attacks as Free Energy Increases

From the FEP perspective, **a cognitive attack is any intervention that forces an agent's free energy up**. Prompt injections, belief manipulation, and trust exploitation all work by injecting observations (or "observations"—fabricated messages, false context) that drive the agent's belief state $Q$ away from its prior $P$ in ways that serve the attacker's goals rather than the agent's.

CIF formalizes this in Part 2 (FEP.1): an attack $\omega$ is detected when $\Delta F(\omega) = F(Q_\text{attacked}) - F(Q_\text{baseline}) > \kappa_\text{FEP}$. The threshold $\kappa_\text{FEP}$ is set by the precision of the agent's prior—agents with strong, well-calibrated priors (high precision) require larger perturbations to shift their beliefs, making them more attack-resistant.

### Trust as Precision Weighting

CIF's trust calculus (the $\delta^d$ decay) has a natural interpretation under FEP: **trust score = precision weight**. When agent $A$ receives a message from agent $B$ with trust score $T(B \to A)$, it should weight that message's evidence proportional to $T(B \to A)$, treating it as an observation with precision $\rho = T(B \to A)$. Trust decay across delegation chains ($\delta^d$) corresponds to precision attenuation in distal channels—the same mechanism that makes far-away sensory signals less reliable than proximal ones.

### The Belief Sandbox as Constrained Inference

The belief sandbox (Part 1, Definition 5.4) has a direct FEP interpretation: it is **constrained variational inference** where the update is only accepted if $\Delta F \leq \kappa \cdot \varepsilon_\text{precision}$. This is equivalent to requiring that accepted belief updates stay within a bounded geodesic radius on the statistical manifold of belief distributions—exactly Theorem CG.1 from Part 2.

### Practical Implication for Operators

This connection is not just theoretical. It means:

1. **Emergent misalignment is the hardest problem** because it minimizes $\Delta F$ per agent: each individual belief shift is sub-threshold, but the collective drift accumulates. This is precisely why colony-scale monitoring is necessary—the FEP signal is distributed across agents.
2. **Trust calibration is precision calibration**: operators who carefully calibrate trust scores are effectively setting the precision weighting of their agent network. Well-calibrated trust → robust cognition.
3. **The Ω₅ miss rate (44%) reflects FEP's fundamental challenge**: systematic manipulation by a compromised orchestrator can shift the agent's generative model $P$ itself (not just $Q$), making the baseline a moving target. This requires out-of-band verification (human review, Byzantine quorum) rather than in-context detection.

For the full mathematical treatment, see Part~2's theoretical-connections and information-geometry sections.
