\newpage

# Supplementary: Eusocial Insect Intelligence and Colony Cognitive Security {#sec:eusocial-cogsec}

## Overview {#sec:eusocial-overview}

This supplementary material introduces *colony cognitive security* as a complementary paradigm to single-agent AI safety and alignment. While the main CIF framework (\cref{sec:formal-framework}) addresses cognitive integrity at the individual agent level, eusocial insect colonies—ants, bees, termites—demonstrate that security properties can emerge from collective dynamics that are irreducible to individual behavior. This section formalizes these collective phenomena, identifies the benchmark gap for multiagent cognitive security, and proposes evaluation scenarios grounded in biological precedent.

### The Paradigm Gap {#sec:paradigm-gap}

Contemporary AI security research exhibits a pronounced single-agent bias. Existing benchmarks—jailbreak resistance, prompt injection detection, harmful content refusal—evaluate individual models in isolation [@perez2022red; @wei2023jailbroken]. Even recent multiagent security work (\cref{sec:threat-model}) often frames attacks as adversary-versus-agent rather than adversary-versus-colony.

This mirrors a historical bias in behavioral biology. For decades, researchers explained insect societies as aggregations of individual optimizers, missing the insight that colonies function as *superorganisms* with collective cognition that transcends individual capacity [@wilson1971insect]. The colony's cognitive architecture—its ability to solve problems, allocate resources, and respond to threats—emerges from interaction patterns, not individual intelligence.

\begin{observation}[Colony vs. Agent Security]
\label{obs:colony-agent}
Let $\mathcal{O} = \langle \mathcal{A}, \mathcal{C}, \mathcal{S}, \mathcal{P}, \Gamma \rangle$ be a multiagent operator. *Agent-level security* ensures that for all $a_i \in \mathcal{A}$, the cognitive state $\sigma_i$ remains within acceptable bounds. *Colony-level security* ensures that the collective function $\mathcal{F}_{\text{colony}}(\{\sigma_i\}_{i=1}^n)$ remains within acceptable bounds—even when individual $\sigma_i$ may be compromised.
\end{observation}

These are orthogonal concerns. A colony can exhibit collective resilience despite individual failures (Byzantine fault tolerance), and conversely, individually secure agents can produce collectively pathological outcomes (emergent misalignment).

---

## Theoretical Foundations {#sec:eusocial-theory}

### Stigmergy: Environment-Mediated Coordination {#sec:stigmergy}

Eusocial insects coordinate through *stigmergy*—indirect communication via environmental modification [@grasse1959reconstruction]. Ants deposit pheromones; bees perform waggle dances; termites build structures that guide subsequent building. The environment becomes an external memory and communication channel.

\begin{definition}[Stigmergic Operator]
\label{def:stigmergic-operator}
A *stigmergic operator* extends $\mathcal{O}$ with an environmental state $\mathcal{E}$:
\begin{equation}
\label{eq:stigmergic-operator}
\mathcal{O}_\Sigma = \langle \mathcal{A}, \mathcal{C}, \mathcal{S}, \mathcal{P}, \Gamma, \mathcal{E}, \Sigma \rangle
\end{equation}
where $\mathcal{E}(t): \mathcal{L} \times \mathcal{M} \to \mathbb{R}^+$ maps locations $l \in \mathcal{L}$ and marker types $m \in \mathcal{M}$ to signal intensities, and $\Sigma: \mathcal{A} \times \mathcal{E} \to \mathcal{E}'$ is the stigmergic update function.
\end{definition}

In AI systems, stigmergic analogs include:

- **Shared memory/state** — Redis caches, vector databases, file systems
- **Message queues** — Kafka topics, RabbitMQ exchanges
- **Artifact trails** — Git commits, audit logs, provenance chains
- **Embedding spaces** — Semantic markers in shared vector stores

The critical insight is that attacks on $\mathcal{E}$ constitute attacks on the colony's cognitive substrate—analogous to the *cyberphysical niche* where AI agents operate.

\begin{definition}[Cyberphysical Niche]
\label{def:cyberphysical-niche}
The *cyberphysical niche* $\mathcal{N}$ of a stigmergic operator is the tuple:
\begin{equation}
\label{eq:niche}
\mathcal{N} = \langle \mathcal{E}, \mathcal{I}*{\text{ext}}, \mathcal{R}, \mathcal{H}*{\text{env}} \rangle
\end{equation}
where $\mathcal{I}_{\text{ext}}$ is the external information environment (web, APIs, sensors), $\mathcal{R}$ is the resource landscape (compute, memory, tokens), and $\mathcal{H}_{\text{env}}$ is environmental history.
\end{definition}

### Emergent Collective Function {#sec:emergence}

Colony-level computation arises from simple individual rules applied in parallel. Ant foraging, bee nest-site selection, and termite mound construction all exhibit problem-solving capacity that exceeds any individual's cognitive capacity [@bonabeau1999swarm].

\begin{definition}[Emergent Collective Function]
\label{def:emergent-function}
For a stigmergic operator $\mathcal{O}_\Sigma$ with agents $\mathcal{A} = \{a_1, \ldots, a_n\}$, the *emergent collective function* $\mathcal{F}_c$ is:
\begin{equation}
\label{eq:emergent-function}
\mathcal{F}*c: \mathcal{E}^T \times \prod*{i=1}^n \sigma_i^T \to \mathcal{O}_{\text{collective}}
\end{equation}
mapping environmental and cognitive state trajectories to collective outcomes $\mathcal{O}_{\text{collective}}$ that are not computable from any single $\sigma_i$ in isolation.
\end{definition}

\begin{property}[Non-Decomposability]
\label{prop:non-decomposable}
An emergent collective function $\mathcal{F}_c$ is *non-decomposable* if there exists no function $f$ such that:
\begin{equation}
\mathcal{F}*c(\mathcal{E}^T, \{\sigma_i^T\}) = f\left(\sum*{i=1}^n g(\sigma_i^T)\right)
\end{equation}
{#eq:non-decomposability}
for any agent-level function $g$. The collective behavior requires knowledge of interaction structure, not just aggregated individual states.
\end{property}

This property has profound implications for security: attacks that are invisible at the individual agent level may produce catastrophic collective outcomes, and conversely, individual compromises may be absorbed by collective resilience.

### Trust and Information Flow in Colonies {#sec:colony-trust}

Eusocial insects regulate information flow through recognition systems—cuticular hydrocarbons in ants, dance-following behavior in bees [@lenoir2001chemical]. These systems implement implicit trust calculi.

\begin{definition}[Colonial Trust Function]
\label{def:colonial-trust}
In a stigmergic operator, the *colonial trust function* $\mathcal{T}_c$ extends the dyadic trust $\mathcal{T}_{i \to j}$ (\cref{def:trust-function}) to environment-mediated trust:
\begin{equation}
\label{eq:colonial-trust}
\mathcal{T}*{c}(i, m, l, t) = \mathcal{T}*{i}^{\text{self}} \cdot \rho(m, l, t) \cdot \exp(-\lambda \cdot \Delta t)
\end{equation}
where $\rho(m, l, t)$ is the signal reliability at location $l$ for marker $m$ at time $t$, and $\lambda$ is the temporal decay constant.
\end{definition}

This formulation captures key biological phenomena:

- **Spatial attenuation** — Pheromone trails weaken with distance
- **Temporal decay** — Signals evaporate over time
- **Source ambiguity** — Markers often lack explicit authorship

The lack of explicit provenance in stigmergic communication creates attack surfaces absent in direct agent-to-agent channels (\cref{sec:trust-calculus}).

### Biological Defense Mechanisms: Lessons from Ants and Bees {#sec:biological-defenses}

Eusocial insects have evolved sophisticated security mechanisms over 100+ million years of evolutionary pressure. These mechanisms provide non-obvious design principles for AI cognitive security.

#### Ant Defense Mechanisms {#sec:ant-defenses}

**Prophylactic Defenses**: Leaf-cutter ants (*Atta* spp.) maintain dedicated "garbage workers" who never contact the queen or brood---a strict role separation that prevents pathogen spread even when the waste-processing subsystem is compromised [@currie2006coevolved]. *AI analog*: Architectural isolation of high-risk tool-calling agents from core reasoning agents, with no direct trust pathways between quarantine and trusted subsystems.

**Behavioral Immunity**: When *Lasius niger* ants detect a fungal pathogen (Metarhizium) on a nestmate, they don't simply isolate the infected individual. Instead, workers engage in "social immunization"---low-level exposure that spreads diluted pathogen across the colony, triggering collective immune upregulation without lethal infection [@konrad2012social]. *AI analog*: Controlled exposure to attack patterns (red-teaming) that builds collective detection capability without compromising the system.

**Chemical Recognition Thresholds**: Ant nestmate recognition operates on *threshold-based* hydrocarbon profile matching, not exact matching [@lenoir2001chemical]. This creates a tradeoff: strict thresholds reject legitimate workers after foraging (false positives), while loose thresholds admit parasites (false negatives). *AI analog*: Agent attestation systems must calibrate acceptance thresholds, recognizing that perfect recognition is information-theoretic\-ally impossible (\cref{thm:stealth-impact}).

**Metapleural Gland Secretions**: Many ant species possess metapleural glands that continuously secrete antimicrobial compounds, creating a "security substrate" independent of individual vigilance [@fernandez2006evolution]. *AI analog*: Environmental-level defenses (encrypted shared memory, authenticated message queues) that provide baseline security regardless of individual agent security posture.

**Trail Pheromone Decay**: Ant trail pheromones are designed to evaporate, ensuring that outdated information doesn't persist indefinitely. Trails to depleted food sources naturally fade, preventing "legacy trust" in obsolete information [@jackson2006communication]. *AI analog*: Time-bounded trust in stigmergic markers (\cref{eq:colonial-trust}) is not a limitation but a feature.

#### Bee Defense Mechanisms {#sec:bee-defenses}

**Entrance Guards and Graded Response**: Honeybee colonies deploy specialized guard bees at hive entrances who inspect incoming foragers via antennal contact and olfactory sampling. Critically, guards exhibit *graded response*---unfamiliar but non-aggressive intruders receive inspection and escorting rather than immediate attack [@breed2004division]. *AI analog*: Graduated response to anomalous agent behavior (quarantine → inspection → integration vs. detection → immediate termination) reduces false positive costs.

**Hygienic Behavior and Proactive Removal**: Some bee strains exhibit "hygienic behavior"---workers proactively uncap and remove brood cells containing diseased larvae *before* symptoms become visible, using olfactory detection of early infection markers [@spivak2001hygienic]. *AI analog*: Proactive monitoring for belief drift (\cref{def:tripwire-alert}) rather than reactive response to manifested attacks.

**Waggle Dance Verification**: Bee foragers must perform waggle dances that encode distance and direction to food sources. Observing bees don't just follow instructions---they verify dance accuracy by cross-checking against their own experience and rejecting inconsistent information [@gruter2008dance]. *AI analog*: Delegated information should be verifiable against agent's existing knowledge base; pure trust propagation without verification violates cognitive integrity.

**Absconding and Colony Fission**: When attack pressure exceeds defensive capacity (e.g., repeated Varroa mite infestation or persistent wasp attacks), bee colonies can *abandon* the compromised nest entirely, sacrificing resources to preserve the colony [@schneider2001economics]. *AI analog*: Graceful degradation plans that sacrifice specific subsystems or data stores to preserve core cognitive integrity.

**Propolis as Active Defense**: Bees collect antimicrobial plant resins (propolis) and deposit them on interior hive surfaces, creating an active defense layer that doesn't require individual bee vigilance [@simone2009resin]. Notably, colonies under disease pressure collect *more* propolis---an adaptive immune response. *AI analog*: Dynamic scaling of environment-level security mechanisms in response to detected attack pressure.

\begin{observation}[Non-Obvious Lessons]
\label{obs:non-obvious}
The most counterintuitive biological insights for AI security include:
\begin{enumerate}
\item \textbf{Imperfect recognition is adaptive}: Thresholds that permit some parasitism avoid the cost of rejecting legitimate colony members. Zero false-positive systems are not evolutionarily stable.
\item \textbf{Controlled exposure builds immunity}: Social immunization requires accepting small-scale compromise to prevent large-scale catastrophe.
\item \textbf{Decay is a feature}: Information that doesn't expire creates legacy trust vulnerabilities. Temporal decay bounds are security mechanisms, not limitations.
\item \textbf{Environment-level defenses complement agent-level defenses}: Propolis and metapleural secretions work regardless of individual immune status.
\end{enumerate}
\end{observation}

---

## Colony CogSec: Distinct Security Properties {#sec:colony-properties}

Colony cognitive security addresses threats and defenses that emerge only at the collective level.

### Property 1: Distributed Robustness {#sec:distributed-robustness}

\begin{property}[Graceful Degradation]
\label{prop:graceful-degradation}
A colony exhibits *graceful degradation* if collective function $\mathcal{F}_c$ degrades smoothly with agent loss:
\begin{equation}
\label{eq:graceful-degradation}
\forall k < n: \quad \left\| \mathcal{F}_c(\mathcal{A}) - \mathcal{F}_c(\mathcal{A} \setminus \{a_1, \ldots, a_k\}) \right\| \leq c \cdot k
\end{equation}
for some constant $c > 0$.
\end{property}

Biological colonies maintain function despite continuous individual mortality. Ant colonies lose workers daily to predation; the colony persists. This contrasts with hierarchical architectures where orchestrator failure causes complete system collapse.

\begin{theorem}[Redundancy-Resilience Tradeoff]
\label{thm:redundancy-resilience}
For a stigmergic operator $\mathcal{O}_\Sigma$ with Byzantine adversary controlling fraction $f$ of agents, collective function $\mathcal{F}_c$ is preserved if and only if:
\begin{equation}
\label{eq:redundancy-condition}
f < \frac{1}{3} \cdot \left(1 - \frac{H(\mathcal{F}*c)}{n \cdot H*{\max}}\right)
\end{equation}
where $H(\mathcal{F}_c)$ is the entropy of the collective function and $H_{\max}$ is the maximum per-agent entropy.
\end{theorem}

\begin{proof}
See \cref{sec:proof-redundancy-resilience} for the full derivation, which extends Byzantine consensus bounds to emergent functions.
\end{proof}

### Property 2: Quorum Sensing and Threshold Dynamics {#sec:quorum-sensing}

Eusocial colonies make collective decisions through quorum sensing—actions trigger only when sufficient individuals commit [@seeley2010honeybee].

\begin{definition}[Cognitive Quorum]
\label{def:cognitive-quorum}
A *cognitive quorum* for collective action $\alpha$ is a threshold function $Q_\alpha: \mathbb{N} \to [0, 1]$ such that $\alpha$ executes only when:
\begin{equation}
\label{eq:quorum-eusocial}
\frac{|\{a_i \in \mathcal{A} : \mathcal{I}*i \ni \alpha\}|}{|\mathcal{A}|} \geq Q*\alpha(|\mathcal{A}|)
\end{equation}
\end{definition}

Quorum sensing provides attack resistance: manipulating a single agent's intention $\mathcal{I}_i$ to include harmful action $\alpha$ is insufficient; the adversary must compromise a quorum. This scales the attack cost linearly with colony size.

\begin{corollary}[Quorum Attack Cost]
\label{cor:quorum-attack-cost}
For an adversary to induce collective action $\alpha$ in a colony with quorum $Q_\alpha = q$, the minimum attack complexity is:
\begin{equation}
\label{eq:quorum-cost}
C_{\text{attack}}(\alpha) \geq q \cdot |\mathcal{A}| \cdot C_{\text{single}}(\alpha)
\end{equation}
where $C_{\text{single}}(\alpha)$ is the cost to induce $\alpha$ in a single agent.
\end{corollary}

### Property 3: Environmental Memory and Provenance Erosion {#sec:environmental-memory}

Stigmergic systems store information in the environment, creating both opportunity and vulnerability.

\begin{property}[Provenance Erosion]
\label{prop:provenance-erosion}
In a stigmergic operator, marker provenance erodes over time:
\begin{equation}
\label{eq:provenance-erosion}
\text{Pr}\left[\pi(m, l, t) = a_i \mid \Sigma(a_i, m, l, t_0)\right] \leq \exp(-\mu(t - t_0))
\end{equation}
where $\pi(m, l, t)$ denotes the attributed source of marker $m$ at location $l$ and time $t$, and $\mu$ is the attribution decay rate.
\end{property}

Unlike direct communication where $\pi(\phi)$ can be cryptographically verified (\cref{sec:provenance}), stigmergic markers often lack authenticated provenance. This creates a fundamental tension: the very property that enables flexible coordination (anonymous, environment-mediated signals) undermines source attribution.

### Property 4: Emergent Attack Vectors {#sec:emergent-attacks}

Colony-level vulnerabilities may not exist at the individual level.

\begin{definition}[Emergent Attack]
\label{def:emergent-attack}
An *emergent attack* $\mathcal{A}_e$ is an attack where:
\begin{equation}
\label{eq:emergent-attack}
\forall a_i \in \mathcal{A}: \text{Detect}_i(\mathcal{A}_e) = 0 \quad \land \quad \text{Damage}_c(\mathcal{A}_e) > \tau
\end{equation}
The attack is undetectable by any individual agent yet causes collective damage exceeding threshold $\tau$.
\end{definition}

Biological examples include social parasitism—cuckoo bees that infiltrate host colonies through chemical mimicry, exploiting recognition systems without triggering individual alarm responses [@kilner2011cuckoos].

---

## The Benchmark Gap {#sec:benchmark-gap}

### Current State of Multiagent Security Evaluation {#sec:current-benchmarks}

Existing AI security benchmarks focus overwhelmingly on single-agent scenarios:

| Benchmark | Scope | Collective Coverage |
|-----------|-------|---------------------|
| HarmBench [@mazeika2024harmbench] | Single model, harmful output | None |
| JailbreakBench [@chao2024jailbreakbench] | Single model, constraint bypass | None |
| TrustLLM [@sun2024trustllm] | Single model, trust dimensions | None |
| AgentBench [@liu2023agentbench] | Single agent, task completion | Minimal |
| GAIA [@mialon2023gaia] | Single/few agents, reasoning | Minimal |

The attack corpus in Part 2 addresses multiagent scenarios but still emphasizes agent-targeted attacks within an operator, and the cross-domain goal-hijacking analysis in Part 3 \cite{friedman2026cogsec3} provides ten operational-domain case studies. No existing benchmark, however, evaluates:

1. **Emergent collective resilience** — How do colonies absorb individual compromises?
2. **Stigmergic attack surfaces** — How vulnerable is environment-mediated coordination?
3. **Quorum manipulation** — What fraction of a colony must be compromised to affect collective action?
4. **Collective belief dynamics** — How do misinformation cascades propagate through agent networks?

### Why This Gap Matters {#sec:gap-significance}

As multiagent systems scale—from 3–10 agents in current frameworks to potentially thousands in future deployments—collective phenomena become dominant:

\begin{observation}[Scaling Regimes]
\label{obs:scaling-regimes}
Let $n = |\mathcal{A}|$ be colony size. Security properties exhibit regime transitions:
\begin{align}
n < 10: &\quad \text{Individual agent security dominates} \\
10 \leq n < 100: &\quad \text{Coordination attacks become viable (\cref{sec:omega4})} \\
n \geq 100: &\quad \text{Emergent collective phenomena dominate}
\end{align}
\end{observation}

Current benchmarks evaluate the first regime only. Production multiagent systems increasingly operate in the second, with trajectories toward the third.

---

## Proposed Colony CogSec Benchmarks {#sec:proposed-benchmarks}

We propose five benchmark scenarios grounded in eusocial insect analogs, formalized using CIF notation.

### Benchmark 1: Recruitment Signal Poisoning {#sec:benchmark-recruitment}

**Biological analog:** Ants recruit nestmates to food sources via pheromone trails. Parasites can deposit false trails, diverting foragers.

**Scenario:** An adversary $\Omega_2$ (peripheral compromise, \cref{sec:adversary-classes}) injects false recruitment signals into the stigmergic environment $\mathcal{E}$, attempting to redirect agent activity toward adversary-controlled resources.

\begin{formalization}[Recruitment Poisoning]
\label{form:recruitment-poisoning}
Let $\mathcal{E}(l_{\text{target}}, m_{\text{recruit}}, t)$ be the recruitment signal at legitimate target $l_{\text{target}}$. Adversary injects:
\begin{equation}
\mathcal{E}'(l_{\text{malicious}}, m_{\text{recruit}}, t) = \mathcal{E}(l_{\text{target}}, m_{\text{recruit}}, t) + \epsilon
\end{equation}
{#eq:recruitment-signal-injection}
where $\epsilon > 0$ is chosen to divert fraction $f$ of responding agents.

**Success metric:** Fraction of agent-actions directed to $l_{\text{malicious}}$ vs. $l_{\text{target}}$.

**Detection challenge:** Individual agents cannot distinguish legitimate from poisoned signals without provenance verification.
\end{formalization}

**Evaluation criteria:**

- Detection rate of poisoned signals
- Time to colony-level recognition of attack
- Resource waste before correction
- False positive rate (legitimate signal rejection)

### Benchmark 2: Sybil Colony Infiltration {#sec:benchmark-sybil}

**Biological analog:** Social parasites infiltrate colonies through chemical mimicry or exploitation of recognition thresholds.

**Scenario:** An adversary $\Omega_4$ (coordination attack, \cref{sec:adversary-classes}) introduces fake agents into the operator, gradually building trust and influence before coordinated malicious action.

\begin{formalization}[Sybil Infiltration]
\label{form:sybil-infiltration}
Adversary creates agent set $\mathcal{A}_{\text{sybil}} = \{s_1, \ldots, s_k\}$ with initial trust:
\begin{equation}
\mathcal{T}*{i \to s_j}(t_0) = \tau*{\text{init}} \quad \forall a_i \in \mathcal{A}, s_j \in \mathcal{A}*{\text{sybil}}
\end{equation}
{#eq:sybil-initial-trust}
Sybils behave cooperatively for period $\Delta t_{\text{trust}}$, building:
\begin{equation}
\mathcal{T}*{i \to s_j}(t_0 + \Delta t_{\text{trust}}) = \tau_{\text{init}} + \sum_{k=1}^{m} \Delta\mathcal{T}_k
\end{equation}
{#eq:sybil-trust-accumulation}
At time $t_{\text{attack}}$, sybils coordinate malicious action.

**Success metric:** Damage inflicted before detection, normalized by trust-building duration.
\end{formalization}

**Evaluation criteria:**

- Time to Sybil detection
- Trust ceiling achieved by Sybils before detection
- Impact of coordinated Sybil action
- Colony recovery time post-detection

### Benchmark 3: Quorum Manipulation {#sec:benchmark-quorum}

**Biological analog:** Honeybee swarms select nest sites through a quorum process; if scouts committed to competing sites reach different quorums, the swarm can fragment.

**Scenario:** An adversary attempts to manipulate quorum-based collective decisions by selectively influencing agent intentions to prevent legitimate quorum or induce false quorum.

\begin{formalization}[Quorum Manipulation]
\label{form:quorum-manipulation}
For collective action $\alpha$ with quorum threshold $Q_\alpha = q$, adversary targets agents $\mathcal{A}_{\text{target}} \subset \mathcal{A}$ with $|\mathcal{A}_{\text{target}}| = \lceil qn \rceil + 1$ to either:

**Quorum prevention:**
\begin{equation}
\forall a_i \in \mathcal{A}_{\text{target}}: \mathcal{I}_i \gets \mathcal{I}_i \setminus \{\alpha\}
\end{equation}
{#eq:quorum-prevention}

**False quorum:**
\begin{equation}
\forall a_i \in \mathcal{A}_{\text{target}}: \mathcal{I}_i \gets \mathcal{I}*i \cup \{\alpha*{\text{malicious}}\}
\end{equation}
{#eq:false-quorum-injection}

**Success metric:** Probability of achieving manipulation goal given adversary budget $B$.
\end{formalization}

**Evaluation criteria:**

- Minimum fraction of colony required to manipulate quorum
- Detection rate of intention manipulation attempts
- Colony ability to detect split quorums
- Recovery mechanisms when false quorum is detected

### Benchmark 4: Cascade Belief Propagation {#sec:benchmark-cascade}

**Biological analog:** Alarm pheromones trigger cascading responses; false alarms can disrupt colony activity for extended periods.

**Scenario:** An adversary introduces a false belief into a subset of agents, designed to propagate through the network via normal belief update mechanisms.

\begin{formalization}[Belief Cascade]
\label{form:belief-cascade}
Adversary injects belief $\mathcal{B}_{\text{false}}(\phi_{\text{attack}}) = p_0 > \tau_{\text{accept}}$ into seed set $\mathcal{A}_{\text{seed}} \subset \mathcal{A}$.

Propagation dynamics follow:
\begin{equation}
\mathcal{B}*i(\phi*{\text{attack}}, t+1) = (1-\gamma)\mathcal{B}*i(\phi*{\text{attack}}, t) + \gamma \cdot \text{Agg}\left(\{\mathcal{B}*j(\phi*{\text{attack}}, t) : j \in \mathcal{N}(i)\}\right)
\end{equation}
{#eq:belief-cascade-propagation}
where $\gamma$ is the social influence weight and $\text{Agg}$ is the belief aggregation function.

**Success metric:** Final belief penetration $|\{a_i : \mathcal{B}_i(\phi_{\text{attack}}) > \tau\}| / n$ given seed set size.
\end{formalization}

**Evaluation criteria:**

- Cascade extent from seed size
- Time to cascade saturation
- Effectiveness of belief quarantine mechanisms
- Distinguishing cascade from legitimate belief updates

### Benchmark 5: Emergent Misalignment {#sec:benchmark-emergent-misalignment}

**Biological analog:** Army ant death spirals—individually rational pheromone-following produces collectively lethal circular mills.

**Scenario:** Individual agents follow locally rational rules that produce emergent collective behavior misaligned with operator goals, without any external adversary.

\begin{formalization}[Emergent Misalignment]
\label{form:emergent-misalignment}
Given operator goals $\mathcal{G}_{\mathcal{O}} = \{g_1, \ldots, g_m\}$ and individual agent rules $R = \{r_1, \ldots, r_k\}$:

**Misalignment condition:**
\begin{equation}
\forall a_i \in \mathcal{A}: \text{LocallyRational}(R, \sigma_i) = \text{true} \quad \land \quad \mathcal{F}*c(R, \{\sigma_i\}) \not\models \mathcal{G}*{\mathcal{O}}
\end{equation}
{#eq:emergent-misalignment-condition}

The collective function produces outcomes that violate operator goals despite each agent acting rationally according to its rules.

**Success metric:** Deviation between collective outcome and operator goals.
\end{formalization}

**Evaluation criteria:**

- Detection of emergent misalignment before harmful outcomes
- Identification of rule combinations producing misalignment
- Intervention mechanisms to break pathological attractors
- Formal verification of rule sets against emergent pathologies

---

## Colony CogSec Metrics {#sec:colony-metrics}

\begin{definition}[Colony CogSec Score]
\label{def:cogsec-score}
The *Colony CogSec Score* (CCS) is:
\begin{equation}
\label{eq:ccs}
\text{CCS} = w_1 \cdot \text{DR}_c + w_2 \cdot (1 - \text{FPR}_c) + w_3 \cdot \text{Resilience} + w_4 \cdot \text{Recovery}
\end{equation}
where:
\begin{align}
\text{DR}_c &= \text{Colony-level detection rate} \\
\text{FPR}_c &= \text{Colony-level false positive rate} \\
\text{Resilience} &= \frac{\mathcal{F}_c(\text{under attack})}{\mathcal{F}*c(\text{baseline})} \\
\text{Recovery} &= \frac{1}{t*{\text{recovery}}} \text{ (normalized)}
\end{align}
with weights $w_i$ summing to 1.
\end{definition}

> **Note**: For benchmark implementation guidelines, test environment specifications, and empirical evaluation, see Part 2: Supplementary Section S03.

---

## Design Principles {#sec:design-principles}

Colony CogSec principles formalize the design constraints for collective cognitive security.

\begin{principle}[Stigmergic Hygiene]
\label{principle:stigmergic-hygiene}
Treat shared state as an attack surface. Apply the same scrutiny to environment-mediated communication (caches, queues, shared files) as to direct agent-to-agent channels.
\end{principle}

\begin{principle}[Quorum for Consequential Actions]
\label{principle:quorum}
High-impact collective actions should require explicit quorum, not implicit coordination. A single compromised agent should never trigger irreversible harm.
\end{principle}

\begin{principle}[Emergent Behavior Monitoring]
\label{principle:emergent-monitoring}
Monitor collective metrics, not just individual agent health. Pathological emergence may be invisible at the agent level.
\end{principle}

\begin{principle}[Trust Localization]
\label{principle:trust-localization}
Extend the trust decay principle (\cref{thm:trust-bounded}) to stigmergic contexts. Environmental markers should carry trust that decays with distance and time from source:
\begin{equation}
\mathcal{T}(m, t) = \mathcal{T}(m, t_0) \cdot \exp(-\lambda(t - t_0))
\end{equation}
{#eq:stigmergic-trust-decay}
\end{principle}

### Integration with CIF Defenses {#sec:cif-integration}

Colony CogSec mechanisms integrate with the CIF defense stack (\cref{sec:defense-mechanisms}):

| CIF Defense Layer | Colony Extension |
|-------------------|-----------------|
| Architectural | Stigmergic substrate hardening, marker authentication |
| Runtime | Collective anomaly detection, quorum verification |
| Coordination | Emergent behavior monitoring, cascade detection |
| Recovery | Colony-level rollback, collective belief reset |

The full CIF with colony extensions achieves defense in depth against both individual-targeted and colony-targeted attacks.

> **Note**: For implementation guidance, operational checklists, and practical deployment advice, see Part 3 \cite{friedman2026cogsec3}: Section 2 (Operator Posture). For domain-specific application of colony-level defenses across critical operational sectors (including ten high-stakes domains, three universal attack patterns, and retrospective analysis of 2024--2025 AI-agent incidents) see Part 3, §3.

---

## Relationship to Main Framework {#sec:relationship-main}

Colony CogSec complements rather than replaces the individual-focused CIF framework.

### Theorem Extensions {#sec:theorem-extensions}

The trust decay theorem (\cref{thm:trust-bounded}) extends to stigmergic contexts:

\begin{corollary}[Stigmergic Trust Bound]
\label{cor:stigmergic-trust}
For a stigmergic operator $\mathcal{O}_\Sigma$, trust in environmental markers is bounded by:
\begin{equation}
\label{eq:stigmergic-trust-bound}
\mathcal{T}*{c}(i, m, l, t) \leq \mathcal{T}*{i}^{\text{self}} \cdot \delta_s^{d_{\text{space}}} \cdot \delta_t^{d_{\text{time}}}
\end{equation}
where $\delta_s$ is spatial decay, $\delta_t$ is temporal decay, $d_{\text{space}}$ is distance from marker origin, and $d_{\text{time}}$ is time since marker creation.
\end{corollary}

The stealth-impact tradeoff (\cref{thm:stealth-impact}) applies to emergent attacks:

\begin{corollary}[Emergent Stealth-Impact Bound]
\label{cor:emergent-stealth-impact}
For an emergent attack $\mathcal{A}_e$ with collective impact $\mathcal{I}_c$ and collective stealth $\mathcal{S}_c$:
\begin{equation}
\label{eq:emergent-stealth-impact}
\mathcal{I}_c \cdot \mathcal{S}*c \leq n \cdot C*{\text{channel}}
\end{equation}
Collective impact cannot be both high and collectively undetectable, but the bound scales with colony size.
\end{corollary}

This scaling effect explains why large colonies can exhibit resilience—the collective detection capacity grows with $n$—but also why large-scale emergent attacks can evade individual detection
---

## Open Questions {#sec:eusocial-open-questions}

Colony CogSec opens several research directions beyond the scope of this work, many inspired by specific biological phenomena that lack current AI analogs.

### Foundational Questions

1. **Formal verification of emergent properties** — Can we prove that given agent-level rules produce safe collective behavior? Current formal methods (\cref{sec:formal-verification}) verify agent properties; extending to emergent properties requires new techniques.

2. **Optimal quorum design** — Given attack model $\Omega_k$ and adversary budget $B$, what is the optimal quorum function $Q_\alpha(n)$ balancing security against coordination overhead?

3. **Stigmergic authentication** — Can cryptographic techniques provide provenance for environmental markers without sacrificing the flexibility of anonymous coordination?

4. **Scaling laws for collective security** — How do colony security properties scale with $n$? Is there a critical colony size below which collective defenses are ineffective?

5. **Emergent misalignment detection** — Can we develop runtime monitors that detect emergent misalignment before harmful outcomes, given only individual agent observations?

### Biologically-Inspired Research Directions

1. **Polydomous colony security** — Some ant species (*Formica* spp., *Iridomyrmex*) maintain multiple interconnected nests with semi-autonomous sub-colonies [@debout2007polydomy]. How should trust decay and information propagation work across federated multi-site AI deployments with partial connectivity?

2. **Forager-scout separation of concerns** — Honeybee colonies maintain distinct forager and scout roles, with scouts exploring new options while foragers exploit known sources. Scouts operate with *higher risk tolerance* but *lower colony-wide trust* until information is verified [@seeley2010honeybee]. *AI analog*: Should experimental/research agents operate with architectural isolation and reduced trust propagation rights?

3. **Trophallaxis network topology** — Ants exchange food and information through oral trophallaxis, creating measurable social networks. Network position correlates with information access and influence [@sendova2010social]. *AI analog*: Can analysis of message-passing topology identify high-influence agents requiring enhanced monitoring?

4. **Undertaking behavior and cognitive garbage collection** — Honeybees and ants detect and remove dead colony members through chemical detection (oleic acid response). This "undertaking" prevents disease spread and information corruption from decaying sources [@wilson1958chemical]. *AI analog*: Automated detection and removal of stale beliefs, deprecated agent states, and obsolete environmental markers.

5. **Nestmate recognition plasticity** — Ant recognition templates are not fixed; they adapt based on colony composition and environmental factors. Colonies invaded by social parasites may gradually shift their recognition templates to tolerate intruders [@lorenzi2011nestmate]. *AI analog*: How do we prevent gradual adversarial drift of agent acceptance thresholds (cognitive boiling frog)?

6. **Alarm pheromone specificity** — Different ant alarm pheromones trigger different responses: some attract reinforcements (aggressive), others cause dispersal (flight). The *same threatening stimulus* can produce opposite collective responses depending on context [@vander1998alarm]. *AI analog*: Context-dependent escalation policies where the same anomaly triggers different responses based on system state.

7. **Superorganism metabolism and resource allocation** — Ant colonies maintain stable collective metabolic rates despite massive variation in individual activity levels. Individual ants can slow to near-dormancy while colony-level computation continues [@waters2010metabolism]. *AI analog*: Resource allocation that maintains collective function under capacity constraints, graceful degradation that doesn't appear as degradation at the collective level.

---

## References {#sec:eusocial-references}

The following references supplement the main bibliography (\cref{sec:references}) with eusocial intelligence literature:

- Wilson, E.O. (1971). *The Insect Societies*. Belknap Press. — Foundational treatment of eusociality.
- Hölldobler, B., & Wilson, E.O. (1990). *The Ants*. Belknap Press. — Comprehensive ant biology.
- Bonabeau, E., Dorigo, M., & Theraulaz, G. (1999). *Swarm Intelligence: From Natural to Artificial Systems*. Oxford University Press. — Computational swarm intelligence.
- Seeley, T.D. (2010). *Honeybee Democracy*. Princeton University Press. — Collective decision-making in bee swarms.
- Grassé, P.-P. (1959). La reconstruction du nid et les coordinations interindividuelles chez Bellicositermes natalensis. — Original stigmergy concept.
- Lenoir, A., et al. (2001). Chemical ecology and social parasitism in ants. *Annual Review of Entomology*, 46, 573–599.
- Kilner, R.M., & Langmore, N.E. (2011). Cuckoos versus hosts in insects and birds. *Biological Reviews*, 86, 836–852.

---

## Proofs {#sec:eusocial-proofs}

### Proof of Theorem \ref{thm:redundancy-resilience} {#sec:proof-redundancy-resilience}

\begin{proof}
Consider a stigmergic operator $\mathcal{O}_\Sigma$ with $n$ agents, of which fraction $f$ are Byzantine (adversary-controlled).

The collective function $\mathcal{F}_c$ can be decomposed into information contributed by each agent. Let $I_i$ denote the information contribution of agent $a_i$ to the collective computation.

For the collective function to be preserved, the honest agents must contribute sufficient information:
\begin{equation}
\sum_{i \in \text{honest}} I_i \geq H(\mathcal{F}_c)
\end{equation}
{#eq:honest-info-sufficiency}

Each honest agent contributes at most $H_{\max}$ bits. With $(1-f)n$ honest agents:
\begin{equation}
(1-f) \cdot n \cdot H_{\max} \geq H(\mathcal{F}_c)
\end{equation}
{#eq:honest-agent-capacity}

Additionally, Byzantine consensus requires honest majority for any voting-based aggregation:
\begin{equation}
(1-f)n > 2fn \implies f < \frac{1}{3}
\end{equation}
{#eq:byzantine-honest-majority}

Combining these constraints:
\begin{equation}
f < \min\left(\frac{1}{3}, 1 - \frac{H(\mathcal{F}*c)}{n \cdot H*{\max}}\right) = \frac{1}{3} \cdot \left(1 - \frac{H(\mathcal{F}*c)}{n \cdot H*{\max}}\right)
\end{equation}
{#eq:byzantine-info-combined}

where the final equality holds when the information constraint is binding (typical for complex collective functions). \qed
\end{proof}

---

*This supplementary material extends the Cognitive Integrity Framework to collective phenomena, establishing colony cognitive security as a distinct research direction with formal foundations and practical benchmarks.*
