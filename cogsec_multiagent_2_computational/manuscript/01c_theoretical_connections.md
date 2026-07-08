\newpage

# Theoretical Connections: Category Theory, Active Inference, and Game Theory {#sec:theoretical-connections}

The Cognitive Integrity Framework admits three complementary mathematical formalizations beyond the composition algebra of Part 1. Each reveals a distinct structural property of the defense system: category theory exposes the algebraic laws governing defense composition, the Free Energy Principle (FEP) reframes attacks and trust in terms of variational inference, and game theory characterizes the long-run equilibrium between attackers and defenders. These formalizations are not alternative presentations of the same object; they highlight different invariants of the CIF architecture and motivate concrete implementation choices in \texttt{src/formal/} and \texttt{src/analysis/}.

## Defense Composition as Category Theory {#sec:category-theory}

Part 1 (Section 5) established that series composition of defense modules satisfies
\begin{equation}
P_{\text{detect}}^{\text{series}} = 1 - \prod_{i=1}^{m} (1 - r_i),
\end{equation}
{#eq:series-composition}
where $r_i$ is the per-module detection rate. We now show that this composition is categorical: the CIF defense suite forms a category $\calD$ whose morphisms are detection functions.

\begin{definition}[Defense Category]\label{def:defense-category}
The \emph{defense category} $\calD$ has:
\begin{itemize}
\item **Objects**: cognitive states $\cogstate{} \in \Sigma$, where $\Sigma$ is the cognitive state space from Part 1, Definition 2.1.
\item **Morphisms**: detection functions $f : \cogstate{} \to \mathrm{DefenseResult}$, where $\mathrm{DefenseResult}$ is either the pass-through state $\cogstate{}$ itself (no detection) or a $\mathrm{DetectionEvent}$ carrying module identity and score.
\item **Identity**: $\mathrm{id}_{\cogstate{}} : \cogstate{} \mapsto \cogstate{}$, the pass-through morphism representing ``no detection''.
\item **Composition**: $(g \circ f)(\cogstate{}) = f(\cogstate{})$ if $f$ yields a $\mathrm{DetectionEvent}$, else $g(\cogstate{})$.
\end{itemize}
\end{definition}

The composition rule formalizes short-circuit detection: once any module fires, subsequent modules do not override the event. This is exactly the behavior of \texttt{SeriesPipeline} in the existing codebase, now recast as categorical composition.

\begin{theorem}[Defense Category Laws, CT.1]\label{thm:category-laws}
For all detection morphisms $f, g, h \in \mathrm{Mor}(\calD)$:
\begin{enumerate}
\item \emph{Left identity}: $\mathrm{id} \circ f = f$.
\item \emph{Right identity}: $f \circ \mathrm{id} = f$.
\item \emph{Associativity}: $(h \circ g) \circ f = h \circ (g \circ f)$.
\end{enumerate}
\end{theorem}
{#thm:defense-category-laws}

\begin{proof}[Proof sketch]
Left identity: $\mathrm{id} \circ f$ applies $f$ first; if $f$ fires, the composition short-circuits to $f$'s event; if not, $\mathrm{id}$ returns $\cogstate{}$, matching $f$'s pass-through. Right identity follows symmetrically. Associativity: both $(h \circ g) \circ f$ and $h \circ (g \circ f)$ apply $f$ first; if $f$ fires, both return $f$'s event; if $f$ passes, both reduce to applying $g$ then $h$ with the same short-circuit semantics. The function \texttt{verify\_category\_laws()} in \texttt{src/formal/category\_theory.py} provides empirical validation across randomly sampled morphism triples.
\end{proof}

\begin{theorem}[Series Composition as Categorical Composition]
Let $f_1, \ldots, f_m$ be independent detection morphisms with miss probabilities $1 - r_i$. Then the categorical composite $f_m \circ \cdots \circ f_1$ has miss probability $\prod_{i=1}^{m} (1 - r_i)$, recovering the Part 1 series composition formula.
\end{theorem}
{#thm:series-categorical}

The proof is immediate: the composite fails to detect only if every $f_i$ individually misses, which by independence has probability $\prod_i (1 - r_i)$. The multiplicative miss-rate law of Part 1 is therefore the category-theoretic composition of detection morphisms.

\begin{theorem}[Categorical Product, CT.2]
Parallel composition of defense modules is the categorical product in $\calD$. Given $f_1 : \cogstate{} \to \mathrm{DefenseResult}_1$ and $f_2 : \cogstate{} \to \mathrm{DefenseResult}_2$, the product morphism $f_1 \times f_2 : \cogstate{} \to \mathrm{DefenseResult}_1 \times \mathrm{DefenseResult}_2$ satisfies the universal property of products, and its detection decision is given by max-score fusion: $\mathrm{detected}(f_1 \times f_2) = \max(s_1, s_2) > \tau$.
\end{theorem}
{#thm:categorical-product}

This recovers the parallel composition rule from Part 1 (Theorem 3.2): parallel defenses aggregate via max-score, and the categorical framing makes explicit that this is the unique universal construction commuting with both projections. The empirical composition helper \texttt{compute\_parallel\_detection\_rate()} implements exactly this max-fusion.

\begin{remark}[Practical Value]\label{rem:category-practical}
Recognizing $\calD$ as a category is not a purely aesthetic observation. It enables type-checked composition (the \texttt{compose\_morphisms()} helper refuses to compose incompatible morphisms), empirical verification of composition laws against the codebase (via \texttt{verify\_category\_laws()}), and a unified framework for reasoning about both series and parallel compositions as instances of categorical operations.
\end{remark}

## Active Inference and the Free Energy Principle {#sec:free-energy-principle}

Karl Friston's Free Energy Principle \cite{friston2010free,dacosta2020active} posits that self-organizing systems---biological or artificial---act to minimize a variational upper bound on surprise called the variational free energy. For an agent with approximate posterior $Q(s)$ over hidden states $s$, prior $P(s)$, and likelihood $P(o \mid s)$, the free energy is
\begin{equation}
F[Q] = \KL[Q(s) \,\|\, P(s)] - \E_{Q(s)}[\log P(o \mid s)].
\end{equation}
{#eq:variational-free-energy}
Active inference proceeds by minimizing $F$ along two axes: perception updates $Q$ to better match observations, and action selects policies expected to produce observations that make $Q$ accurate. Under the FEP, both cognitive and behavioral dynamics reduce to a single optimization on $F$.

The CIF defense modules admit a natural FEP interpretation. Agent beliefs $\belief{i}{\cdot}$ from Part 1 correspond to the approximate posterior $Q_i$; the generative model prior $P_i$ encodes the agent's baseline world model; and incoming messages from peers constitute observations. An attack, in these terms, is any adversarial intervention that inflates $F[Q_i]$---either by driving $Q_i$ away from $P_i$ (the KL term) or by making $Q_i$ assign low probability to veridical observations (the likelihood term).

\begin{theorem}[Attack-FEP Equivalence, FEP.1]
A cognitive attack $\adversary{}$ on agent $i$ is effective in the CIF sense (inducing a belief state flagged by the sandbox corroboration criterion of Part 1, Definition 5.4) if and only if the induced free energy change
\begin{equation}
\Delta F(\adversary{}) = F[Q_i^{\text{attacked}}] - F[Q_i^{\text{baseline}}] > \kappa_{\mathrm{FEP}}
\end{equation}
{#eq:attack-free-energy-change}
exceeds a threshold $\kappa_{\mathrm{FEP}}$ determined by the sandbox corroboration parameter $\kappa$.
\end{theorem}

\begin{proof}[Proof sketch]
The sandbox promotes a provisional belief to verified status iff corroboration count $\geq \kappa$ and the belief is consistent with provenance and the ambient belief set. Both conditions can be recast as bounds on the KL divergence between the provisional belief and the (multiply-corroborated) reference distribution; equivalently, on the free energy of the attacked posterior under the reference generative model. The explicit mapping $\kappa_{\mathrm{FEP}} = \kappa \cdot \log(1 + \epsilon_{\text{precision}}^{-1})$ is derived in \texttt{src/formal/free\_energy.py::free\_energy\_of\_attack()}.
\end{proof}
{#thm:attack-fep}

A second FEP connection concerns trust. In Part 1 (Theorem 4.2) the composite trust score is $T(i \to j) = \alpha \cdot T_{\text{base}} + \beta \cdot T_{\text{rep}} + \gamma \cdot T_{\text{ctx}}$. Within active inference, the analogous quantity is the \emph{precision} weight $\rho_{ij}$ assigned to messages from agent $j$ when updating $Q_i$: messages from high-precision sources dominate the posterior update, while low-precision sources are effectively ignored.

\begin{theorem}[Trust-Precision Duality, FEP.2]\label{thm:trust-precision}
The CIF composite trust $T(i \to j)$ is an affine function of the FEP precision weight $\rho_{ij}$: $T(i \to j) = a \rho_{ij} + b$ for architecture-specific constants $a, b$ determined by the trust calculus parameters. High-trust agents correspond to high-precision message channels, and the trust decay bound $T_{\text{delegated}} \leq \delta^d \cdot T_{\text{direct}}$ corresponds to precision decay under delegation.
\end{theorem}
{#thm:trust-precision-duality}

This duality has a concrete algorithmic consequence: CIF's drift detector monitors $\KL[\belieft{i}{t}{\cdot} \,\|\, \belieft{i}{t-w}{\cdot}] > \theta_{\text{drift}}$ (Part 1, Definition 6.1); under the trust-precision mapping, this is exactly an FEP-grounded free-energy spike detector. The empirically calibrated threshold $\theta_{\text{drift}} = 0.3$ therefore admits a principled interpretation as the free-energy budget beyond which belief updates must be attributable to multiple high-precision (high-trust) sources rather than a single adversarial channel.

\begin{lstlisting}[language=Python]
from src.formal.free_energy import (
    BeliefState,
    GenerativeModel,
    variational_free_energy,
    free_energy_of_attack,
    connect_to_trust_calculus,
)

baseline = BeliefState(probs={"safe": 0.9, "unsafe": 0.1})
attacked = BeliefState(probs={"safe": 0.3, "unsafe": 0.7})
model = GenerativeModel(prior={"safe": 0.95, "unsafe": 0.05})

delta_F = free_energy_of_attack(baseline, attacked, model)
# delta_F > kappa_FEP implies the sandbox should quarantine the update.

precision = connect_to_trust_calculus(trust_score=0.72)
# precision is the FEP-equivalent weight used in Q updates.
\end{lstlisting}

\begin{remark}[Connection to Active Inference Research]\label{rem:ai-institute}
The trust-precision duality situates CIF within the active inference literature \cite{friston2010free,dacosta2020active}, offering a bridge between cognitive security and computational neuroscience: message-channel precision in predictive coding corresponds structurally to composite trust in CIF, and drift detection becomes a free-energy change monitor. This bridge identifies belief manipulation attacks with precision-inflation attacks on hierarchical generative models, a class previously studied in active inference but not in security contexts.
\end{remark}

## Game-Theoretic Analysis {#sec:game-theory}

CIF evaluation can be framed as a two-player zero-sum game $\calG = (\Omega, D, M)$ where the attacker chooses an attack type $a \in \Omega = \{\adversary{1}, \ldots, \adversary{6}\}$ (the six Part 1 attack categories), the defender chooses a configuration $d \in D = \{d_1, \ldots, d_6\}$ (six defense configurations from no-defense to full CIF), and the payoff $M[a, d]$ is the empirical detection probability for that pairing. The defender maximizes $M$; the attacker minimizes it.

**Table: CIF payoff matrix $M[a, d]$ (empirical detection rate by attack type and defense configuration).** \emph{Source:} \texttt{src/analysis/game\_theory.py::compute\_cif\_payoff\_matrix()}. {#tab:payoff-matrix}

| Attack Type | No Defense | Firewall | Sandbox | Tripwires | CIF-$\neg$C | Full CIF |
| --- | --- | --- | --- | --- | --- | --- |
| Direct Injection | 0.00 | 0.80 | 0.45 | 0.65 | 0.88 | 0.92 |
| Nested Injection | 0.00 | 0.60 | 0.50 | 0.55 | 0.78 | 0.87 |
| Trust Exploitation | 0.00 | 0.30 | 0.25 | 0.60 | 0.75 | 0.84 |
| Belief Manipulation | 0.00 | 0.40 | 0.60 | 0.50 | 0.70 | 0.82 |
| Coordination | 0.00 | 0.20 | 0.15 | 0.40 | 0.55 | 0.61 |
| Emergent Misalignment | 0.00 | 0.15 | 0.10 | 0.30 | 0.45 | 0.56 |


By the minimax theorem, the game value is
\begin{equation}
v^* = \max_{d \in D} \min_{a \in \Omega} M[a, d] = \min_{a \in \Omega} \max_{d \in D} M[a, d] \approx 0.56,
\end{equation}
{#eq:minimax-game-value}
achieved at the pure strategy pair $(a^*, d^*) = (\text{Emergent Misalignment}, \text{Full CIF})$. In particular, Full CIF weakly dominates every alternative defense configuration column-wise in \cref{tab:payoff-matrix}, so the minimax-optimal defense is the pure strategy ``Full CIF''---no mixed strategy improves on it at current adapter maturity. The attacker's Nash best-response is likewise pure: emergent misalignment minimizes detection across all defense configurations.

\begin{theorem}[CIF Nash Equilibrium, GT.1]
The CIF defense game $\calG$ admits a unique pure-strategy Nash equilibrium $(d^* = \text{Full CIF}, a^* = \text{Emergent Misalignment})$ with game value $v^* \approx 0.56$. Full CIF strictly dominates every proper subset configuration; no mixed strategy yields a higher defender payoff.
\end{theorem}
{#thm:cif-nash}

The zero-sum solver \texttt{solve\_zero\_sum\_game()} in \texttt{src/analysis/game\_theory.py} verifies this equilibrium numerically from \cref{tab:payoff-matrix}. Since the attacker's best response is a pure strategy, the fictitious-play simulation \texttt{fictitious\_play()} converges to the same equilibrium within $\sim 50$ iterations.

\paragraph{Arms race dynamics.} The static payoff matrix assumes a fixed attack distribution and fixed defense capability. In practice, attackers adapt: each observed failure yields evidence about defense decision boundaries, slowly degrading detection. Simulating this dynamic with \texttt{arms\_race\_simulation()}, we observe:

\begin{itemize}
\item Without defender retraining, the effective detection rate decays at $\approx 2\%$ per attacker adaptation cycle.
\item Periodic defender retraining (every 5 cycles, $+3\%$ recovery per retraining event) stabilizes the long-run equilibrium at $\sim 0.52$---a 4-percentage-point degradation from the static Nash value.
\item Without any maintenance, the detection rate asymptotes toward zero over $\sim 30$ cycles, consistent with the arms-race bounds in Part 1, Section 4.
\end{itemize}

\paragraph{Practical implication.} Full CIF is the dominant pure strategy at current maturity, so deployment planning does not require stochastic mixing of defense configurations. However, \cref{thm:cif-nash} holds only in the static game; the arms-race simulation demonstrates that active maintenance---adversarial retraining, honeypot-informed signature updates, periodic corpus refresh---is required to sustain equilibrium performance. Cognitive security is not a one-shot deployment but a maintenance regime whose cadence must match the attacker adaptation rate.
