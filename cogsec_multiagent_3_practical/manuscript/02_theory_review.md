# The Formal Foundation: Concepts from Paper 1 {#sec:theory-review}

Part 3 builds directly on the formal framework established in Part 1. For clarity, we summarize the core definitions and theorems here, utilizing the notation defined in the formal manuscript.

## The Adversary Hierarchy ($\Omega$) {#sec:adversary-hierarchy}

Paper 1 formalized the "Scope of Threat" through a hierarchical taxonomy. This hierarchy allows precise definition of defensive scope.

* **$\Omega_1$ (External)**: The adversary controls inputs (e.g., prompt injection). The agent's internal state is intact.
* **$\Omega_2$ (Peripheral)**: The adversary controls tools or RAG data (e.g., poisoned retrieval). The agent's perception is compromised.
* **$\Omega_3$ (Agent)**: The adversary controls the agent's weights or context (e.g., identity implementation). The agent itself is untrusted.
* **$\Omega_4$ (Coordination)**: The adversary controls a subset of the swarm (e.g., Sybil agents). The consensus mechanism is under attack.
* **$\Omega_5$ (Systemic)**: The adversary controls the orchestrator or infrastructure. The system's rules are compromised.

The simulations in Part 2 demonstrated that defense difficulty scales non-linearly with this hierarchy. While $\Omega_1$ attacks were consistently blocked by surface-level filters (96%+), $\Omega_4$ attacks required coordination-level protocols to detect (74%).

## The Trust Calculus ($T$) {#sec:trust-calculus-review}

A central contribution of Paper 1 is the **Trust Calculus**, a formal system for reasoning about belief reliability. It defines Trust ($T$) not as a binary permission but as a continuous property of a belief $b$, denoted as $T(b) \in [0, 1]$.

The formal definition of Trust Update (Theorem 3.1 in Paper 1) establishes that trust must decay across delegation chains:

> **Theorem 3.1 (Trust Preservation)**: *For any delegation chain $C = \{a_1 \to a_2 \to \dots \to a_n\}$, the trust in the final output cannot exceed the trust of the weakest link, degraded by the distance from the source.*
> $$ T(result) \le \min_{i} T(a_i) \cdot \delta^{|C|} $$
> *where $\delta$ is the decay factor ($0 < \delta < 1$).*

This theorem provides the mathematical basis for the "Trust Decay" mechanism evaluated in Part 2. It ensures that uncertainty is preserved and amplified effectively as information travels through the network.

## The Cognitive Firewall ($\Phi$) {#sec:firewall-review}

The **Cognitive Firewall** is defined in Paper 1 as a function $\Phi$ that maps inputs to decisions based on three verification layers:

1. **Syntactic Verification ($V_{syn}$)**: Checks for structural anomalies.
2. **Semantic Verification ($V_{sem}$)**: Checks for meaning-level violations.
3. **Pragmatic Verification ($V_{prag}$)**: Checks for contextual anomalies.

In the Part 2 experiments, this modular structure was shown to be the primary defense against $\Omega_1$ (External) attacks.

## The Stealth-Impact Tradeoff {#sec:stealth-impact-review}

Paper 1 provides a theoretical bound on attack performance, formalized as the Stealth-Impact Tradeoff.

> **Stealth-Impact Tradeoff**: *For a given defense sensitivity $\epsilon$, the probability of detection $P(d)$ approaches 1 as the divergence of the attack behavior from the baseline increases.*

This formalism suggests that catastrophic attacks are inherently easier to detect than subtle attacks. Part 2's data consistently validated this: High-impact attacks were detected 98% of the time, while low-impact attacks were detected only 74% of the time.

## Defense Composition {#sec:composition-review}

Finally, Paper 1 defines the **Composition Algebra**, determining how output probabilities of distinct modules interact. The key result is that orthogonal defenses compose multiplicatively.

This "Swiss Cheese Model" was empirically validated in Part 2, where the full stack (94% overall detection, 95% CI: [0.92, 0.96]) significantly outperformed the sum of its parts.
