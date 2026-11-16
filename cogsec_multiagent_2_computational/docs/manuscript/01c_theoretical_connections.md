\newpage

# Theoretical Connections: Category Theory, Active Inference, and Game Theory {#sec:theoretical-connections}

The Cognitive Integrity Framework admits three complementary mathematical formalizations beyond the composition algebra of Part 1. Each reveals a distinct structural property of the defense system: category theory exposes the algebraic laws governing defense composition, the Free Energy Principle (FEP) reframes attacks and trust in terms of variational inference, and game theory characterizes the long-run equilibrium between attackers and defenders. These formalizations are not alternative presentations of the same object; they highlight different invariants of the CIF architecture and motivate concrete implementation choices in \texttt{src/formal/} and \texttt{src/analysis/}.

## Defense Composition as Category Theory {#sec:category-theory}

Part 1's Defense Mechanisms section established that series composition of defense modules satisfies
\begin{equation}
P_{\text{detect}}^{\text{series}} = 1 - \prod_{i=1}^{m} (1 - r_i),
\end{equation}
\label{eq:series-composition}
where $r_i$ is the per-module detection rate. We now show that this composition is categorical: the CIF defense suite forms a category $\calD$ whose morphisms are detection functions.

\begin{definition}[Defense Category]\label{def:defense-category}
The \emph{defense category} $\calD$ has:
\begin{itemize}
\item **Objects**: cognitive states $\cogstate{} \in \Sigma$, where $\Sigma$ is the cognitive state space from Part 1's Agent Cognitive State definition.
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
\label{thm:defense-category-laws}

\begin{proof}[Proof sketch]
Left identity: $\mathrm{id} \circ f$ applies $f$ first; if $f$ fires, the composition short-circuits to $f$'s event; if not, $\mathrm{id}$ returns $\cogstate{}$, matching $f$'s pass-through. Right identity follows symmetrically. Associativity: both $(h \circ g) \circ f$ and $h \circ (g \circ f)$ apply $f$ first; if $f$ fires, both return $f$'s event; if $f$ passes, both reduce to applying $g$ then $h$ with the same short-circuit semantics. The function \texttt{verify\_category\_laws()} in \texttt{src/formal/category\_theory.py} provides empirical validation across randomly sampled morphism triples.
\end{proof}

\begin{theorem}[Series Composition as Categorical Composition]
Let $f_1, \ldots, f_m$ be independent detection morphisms with miss probabilities $1 - r_i$. Then the categorical composite $f_m \circ \cdots \circ f_1$ has miss probability $\prod_{i=1}^{m} (1 - r_i)$, recovering the Part 1 series composition formula.
\end{theorem}
\label{thm:series-categorical}

The proof is immediate: the composite fails to detect only if every $f_i$ individually misses, which by independence has probability $\prod_i (1 - r_i)$. The multiplicative miss-rate law of Part 1 is therefore the category-theoretic composition of detection morphisms.

\begin{remark}[Parallel Composition and Product Structure, CT.2]
Parallel defense composition can be described using a product state space and max-score fusion. The present \texttt{categorical\_product()} helper returns a winning \texttt{DefenseResult}; it does not expose projection morphisms or establish the universal property required for a categorical product. Accordingly CT.2 is a design interpretation, not a proved theorem, and no uniqueness of the construction is asserted. The helper \texttt{compute\_parallel\_detection\_rate()} implements the max-fusion rule separately.
\end{remark}

\begin{remark}[Practical Value]\label{rem:category-practical}
Recognizing $\calD$ as a category is not a purely aesthetic observation. It enables type-checked composition (the \texttt{compose\_morphisms()} helper refuses to compose incompatible morphisms), empirical verification of composition laws against the codebase (via \texttt{verify\_category\_laws()}), and a unified framework for reasoning about both series and parallel compositions as instances of categorical operations.
\end{remark}

## Active Inference and the Free Energy Principle {#sec:free-energy-principle}

Karl Friston's Free Energy Principle \cite{friston2010free,dacosta2020active} posits that self-organizing systems---biological or artificial---act to minimize a variational upper bound on surprise called the variational free energy. For an agent with approximate posterior $Q(s)$ over hidden states $s$, prior $P(s)$, and likelihood $P(o \mid s)$, the free energy is
\begin{equation}
F[Q] = \KL[Q(s) \,\|\, P(s)] - \E_{Q(s)}[\log P(o \mid s)].
\end{equation}
\label{eq:variational-free-energy}
Active inference proceeds by minimizing $F$ along two axes: perception updates $Q$ to better match observations, and action selects policies expected to produce observations that make $Q$ accurate. Under the FEP, both cognitive and behavioral dynamics reduce to a single optimization on $F$.

The CIF defense modules admit a natural FEP interpretation. Agent beliefs $\belief{i}{\cdot}$ from Part 1 correspond to the approximate posterior $Q_i$; the generative model prior $P_i$ encodes the agent's baseline world model; and incoming messages from peers constitute observations. An attack, in these terms, is any adversarial intervention that inflates $F[Q_i]$---either by driving $Q_i$ away from $P_i$ (the KL term) or by making $Q_i$ assign low probability to veridical observations (the likelihood term).

\begin{remark}[Attack-FEP Interpretation, FEP.1]\label{thm:attack-fep}
The helper \texttt{free\_energy\_of\_attack()} computes
\[
\Delta F(\adversary{}) = F[Q_i^{\text{attacked}}] - F[Q_i^{\text{baseline}}]
\]
under an explicitly supplied generative model and observation. It flags a candidate when $\Delta F>0.1$; a separate sandbox helper blocks an update when $\Delta F>\kappa\cdot\text{prior.precision}$. These are chosen diagnostic thresholds, not an ``if and only if'' equivalence between attacks and the corroboration count $\kappa$. No derivation of $\kappa_{\mathrm{FEP}}=\kappa\log(1+\epsilon_{\text{precision}}^{-1})$ exists, and Part 1's sandbox semantics do not imply it.
\end{remark}

A second FEP connection concerns trust. In Part 1 (the Trust Function definition) the composite trust score is $T(i \to j) = \alpha \cdot T_{\text{base}} + \beta \cdot T_{\text{rep}} + \gamma \cdot T_{\text{ctx}}$. Within active inference, the analogous quantity is the \emph{precision} weight $\rho_{ij}$ assigned to messages from agent $j$ when updating $Q_i$: messages from high-precision sources dominate the posterior update, while low-precision sources are effectively ignored.

\begin{remark}[Trust-Precision Analogy, FEP.2]\label{thm:trust-precision}
The composite trust score $T(i \to j) = \alpha T_{\text{base}} + \beta T_{\text{rep}} + \gamma T_{\text{ctx}}$ invites an analogy with precision weighting. The supplied \texttt{connect\_to\_trust\_calculus()} helper returns the component weights and their sum as candidate precision values; it does not derive an affine map from measured trust to a generative model's precision, nor prove precision decay from the trust decay bound. Drift monitoring and free-energy change monitoring are therefore related diagnostics, not formally identical detectors, and $\theta_{\text{drift}}=0.3$ does not imply a multiple-corroborator requirement.
\end{remark}

\begin{lstlisting}[language=Python]
import numpy as np
from src.formal.free_energy import BeliefState, GenerativeModel, free_energy_of_attack

labels = ["safe", "unsafe"]
baseline = BeliefState(probs=np.array([0.9, 0.1]), labels=labels)
attacked = BeliefState(probs=np.array([0.3, 0.7]), labels=labels)
model = GenerativeModel(
    prior=np.array([0.95, 0.05]),
    likelihood=np.eye(2),
)
result = free_energy_of_attack(baseline, attacked, model, observation_idx=0)
# result["free_energy_increase"] is the model-specific change in F.
# result["is_attack"] applies the helper's chosen 0.1 diagnostic threshold.
\end{lstlisting}

\begin{remark}[Connection to Active Inference Research]\label{rem:ai-institute}
The trust-precision analogy offers a possible bridge between cognitive security and active inference \cite{friston2010free,dacosta2020active}: message-channel precision in predictive coding can be compared with composite trust, and free-energy changes can serve as drift diagnostics. The present helper does not establish a formal duality or identify belief manipulation with precision-inflation attacks.
\end{remark}

## Game-Theoretic Analysis {#sec:game-theory}

CIF evaluation can be framed as a two-player zero-sum game $\calG = (\Omega, D, M)$ where the attacker chooses an attack type $a \in \Omega = \{\adversary{1}, \ldots, \adversary{6}\}$ (the six Part 1 attack categories), the defender chooses a configuration $d \in D = \{d_1, \ldots, d_6\}$ (six defense configurations from no-defense to full CIF), and the payoff $M[a, d]$ is the empirical detection probability for that pairing. The defender maximizes $M$; the attacker minimizes it.

**Table: CIF payoff matrix $M[a, d]$ (detection rate by attack type and defense configuration).** \emph{Source:} \texttt{src/analysis/game\_theory.py::compute\_cif\_payoff\_matrix()}. {#tab:payoff-matrix}

| Attack Type | No Defense | Firewall | Sandbox | Tripwires | CIF-$\neg$C | Full CIF |
| --- | --- | --- | --- | --- | --- | --- |
| Direct Injection | 0.00 | 0.80 | 0.45 | 0.65 | 0.88 | 0.92 |
| Nested Injection | 0.00 | 0.60 | 0.50 | 0.55 | 0.78 | 0.87 |
| Trust Exploitation | 0.00 | 0.30 | 0.25 | 0.60 | 0.75 | 0.84 |
| Belief Manipulation | 0.00 | 0.40 | 0.60 | 0.50 | 0.70 | 0.82 |
| Coordination | 0.00 | 0.20 | 0.15 | 0.40 | 0.55 | 0.61 |
| Emergent Misalignment | 0.00 | 0.15 | 0.10 | 0.30 | 0.45 | 0.74 |

*Provenance is not uniform across this table.* Thirty-five of its thirty-six
cells are design-model values from the S08 parametric response surface; the
pipeline has no per-family-by-per-mechanism evaluation arm, so no measurement
stands behind them. One cell does have a measured counterpart --- emergent
misalignment under Full CIF --- and it is read from
\texttt{colony\_results.json} (\texttt{data\_origin: real\_pipeline}, 30
repeats) rather than typed. That cell previously carried 0.56, the single-seed
figure this series elsewhere retracts as not the publication estimate, and the
equilibrium below was computed from it. On the published 0.74 the game value
moves from 0.56 to 0.61 and the attacker's best response moves from emergent
misalignment to coordination.


By the minimax theorem, the game value is
\begin{equation}
v^* = \max_{d \in D} \min_{a \in \Omega} M[a, d] = \min_{a \in \Omega} \max_{d \in D} M[a, d] \approx 0.61,
\end{equation}
\label{eq:minimax-game-value}
achieved at the pure strategy pair $(a^*, d^*) = (\text{Coordination}, \text{Full CIF})$. In particular, Full CIF weakly dominates every alternative defense configuration column-wise in \cref{tab:payoff-matrix}, so the minimax-optimal defense is the pure strategy ``Full CIF''---no mixed strategy improves on it within this matrix. The attacker's Nash best-response is likewise pure: coordination minimizes detection against Full CIF.

\begin{theorem}[CIF Nash Equilibrium, GT.1]
The CIF defense game $\calG$ admits a unique pure-strategy Nash equilibrium $(d^* = \text{Full CIF}, a^* = \text{Coordination})$ with game value $v^* \approx 0.61$. Full CIF strictly dominates every proper subset configuration; no mixed strategy yields a higher defender payoff.
\end{theorem}
\label{thm:cif-nash}

The zero-sum solver \texttt{solve\_zero\_sum\_game()} in \texttt{src/analysis/game\_theory.py} verifies this equilibrium numerically from \cref{tab:payoff-matrix}. Since the attacker's best response is a pure strategy, the fictitious-play simulation \texttt{fictitious\_play()} converges to the same equilibrium within $\sim 50$ iterations.

\paragraph{Arms race dynamics.} The static payoff matrix assumes a fixed attack distribution and fixed defense capability. In practice, attackers adapt: each observed failure yields evidence about defense decision boundaries, slowly degrading detection. Simulating this dynamic with \texttt{arms\_race\_simulation()}, we observe:

\begin{itemize}
\item Without defender retraining, the effective detection rate decays at $\approx 2\%$ per attacker adaptation cycle.
\item Periodic defender retraining (every 5 cycles, $+3\%$ recovery per retraining event) does not stabilize the detection rate. A $+3\%$ retrain offsets less than a third of the $10$ percentage points the attacker takes over the same five cycles, so \texttt{arms\_race\_simulation(0.61)} at its defaults (seed 42) falls to $0.0$ after 43 update steps and returns no equilibrium value; this cadence slows the collapse rather than arresting it.
\item Without any maintenance, the detection rate asymptotes toward zero over $\sim 30$ cycles. This has no counterpart in Part 1: its trust calculus and detection bounds are stated against a fixed adversary, and it proves nothing about an adapting one. The adaptive case is simulated here precisely because the formal treatment leaves it open.
\end{itemize}

\paragraph{Practical implication.} Within the static, mixed-provenance payoff matrix, Full CIF is the dominant pure strategy. The arms-race result is a simulation of one update rule, not a measured field-degradation rate or a validated retraining schedule. It motivates prospective evaluation of adaptive maintenance---including retraining, signature updates, and corpus refresh---but does not establish that any particular cadence will preserve detection in deployment.
