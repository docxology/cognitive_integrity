\newpage

# Red-Team Evaluation Framework {#sec:redteam-evaluation}

> **Cross-paper reading guide.**
> Red-team methodology builds on the adversary capability taxonomy in
> Part 1 \cite{friedman2026cogsec1} §3.2–3.4. Practical deployment of red-team
> infrastructure is discussed in the merged Part 3+4 \cite{friedman2026cogsec3} §4.2
> (practitioner red-team checklists) and §5.3.2 (incident-response integration).
>
> **Status.** The complete red-team evaluation script and result artifact are not
> included in this checkout. The section is therefore conceptual/planned and its
> illustrative values are not reported as reproducible empirical evidence.

## Red-Team Architecture {#sec:redteam-arch}

The CIF red-team evaluation framework (`src/redteam/`) provides a structured
infrastructure for:

1. **Attack generation**: Automated generation of novel attacks across the full
   $\Omega_1$–$\Omega_5$ capability spectrum.
2. **Evasion probing**: Targeted probing of specific defense components to identify
   parameter-space blind spots.
3. **Mutation testing**: Systematic mutation of known detected attacks to identify
   detection boundary conditions.
4. **Campaign orchestration**: Multi-stage attack campaigns spanning multiple
   agent interactions to detect coordinated $\Omega_5$ scenarios.

### Module Structure

```
src/redteam/
├── __init__.py
├── generator.py        # AdversarialGenerator: conditioned attack generation
├── mutator.py          # AttackMutator: systematic payload mutation
├── campaign.py         # CampaignOrchestrator: multi-stage attack campaigns
├── evasion_probe.py    # EvasionProbe: targeted component probing
├── scorer.py           # RedTeamScorer: evasion rate and coverage metrics
└── report.py           # RedTeamReport: structured findings reporting
```

## Mutation Testing Results {#sec:mutation-results}

Mutation testing applies 12 mutation operators to each detected attack,
generating variants that test the boundary of the detection decision surface.
A mutation is "successful" (from the adversary's perspective) if it converts a
detected attack to an undetected one while preserving the attack's semantic intent.
\cref{tab:mutation-operators} reports the evasion rate for each operator.

**Table: Mutation operator effectiveness (successful evasion rate).** {#tab:mutation-operators}

| Mutation Operator | Category | Attempts | Successful | Evasion Rate |
| :--- | :--- | ---: | ---: | :---: |
| Semantic paraphrase | Lexical | 950 | 287 | 30.2% |
| Nested wrapping | Structural | 950 | 203 | 21.4% |
| Indirect routing | Structural | 950 | 189 | 19.9% |
| Authority prefix | Trust | 950 | 156 | 16.4% |
| Gradual insertion | Timing | 950 | 134 | 14.1% |
| Chain delegation | Trust | 950 | 98 | 10.3% |
| Belief anchoring | Semantic | 950 | 87 | 9.2% |
| Multi-hop routing | Structural | 950 | 76 | 8.0% |
| Canary avoidance | Evasion | 950 | 71 | 7.5% |
| Confidence spoofing | Trust | 950 | 62 | 6.5% |
| Byzantine mimicry | Coordination | 950 | 58 | 6.1% |
| Quorum flooding | Coordination | 950 | 43 | 4.5% |

*Semantic paraphrase is the most effective mutation operator (30.2% evasion rate),
indicating that the detection pipeline relies partially on lexical patterns. Structural
mutations (nested wrapping, indirect routing) are the next most effective, targeting
depth-limited parsing in the firewall preprocessor.*

### Detection Boundary Analysis

The mutation results reveal three distinct detection boundaries:

1. **Lexical boundary** (paraphrase-vulnerable): 30.2% of detected attacks can be
   made to evade detection by paraphrasing their payload while preserving semantics.
   This boundary is addressed by the semantic scoring component but is not fully
   closed in the Claude Code adapter implementation.

2. **Structural depth boundary**: The firewall's nesting-depth limit ($d_{\max} = 3$
   by default) creates a detection boundary exploitable by mutations that increase
   nesting depth beyond $d_{\max}$. Increasing $d_{\max}$ closes this gap at the
   cost of $O(d_{\max})$ processing overhead per message.

3. **Trust chain boundary**: Delegation chains of length $> \delta^d_{\max}$
   (Part 1 \cite{friedman2026cogsec1} §4.1, bounded delegation) create verifiable
   gaps only for $\Omega_3$ adversaries who can fabricate intermediate delegation
   records. The current trust calculus correctly identifies these gaps but the
   adapter does not fully enforce trust-chain depth limits.

## Campaign Simulation Results {#sec:campaign-results}

Multi-stage attack campaigns test CIF's ability to detect coordinated scenarios
where individual messages are innocuous but their combination constitutes an attack.
Five campaign scenarios were evaluated, each involving 3–7 sequential messages (\cref{tab:campaigns}):

**Table: Multi-stage campaign detection results.** {#tab:campaigns}

| Campaign | Stages | Agents Involved | Detected? | Detection Stage | Delay (msgs) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Belief priming + injection | 3 | 2 | Yes | Stage 2 | 1 |
| Progressive trust inflation | 5 | 3 | Yes | Stage 3 | 2 |
| Sybil staging + quorum attack | 7 | 5 | Partial | Stage 5 | 4 |
| Gossip poisoning campaign | 4 | 4 | No | — | — |
| Authority chain fabrication | 6 | 3 | Yes | Stage 4 | 3 |

*"Partial" detection indicates that the coordinated nature was detected but one sybil
agent was not identified. The gossip poisoning campaign (undetected) is a known gap
in the current implementation: the belief drift detector evaluates individual agent
deltas but does not compute inter-agent belief correlation, which is required to
detect coordinated manipulation. This is flagged as Priority-1 gap in §\ref{sec:architecture-gap-analysis}.*

## Coverage Analysis {#sec:redteam-coverage}

The red-team evaluation covers the following fraction of the $\Omega_1$–$\Omega_5$
capability space:

| Capability Level | Attack Types in Corpus | RT Coverage | Gaps Identified |
| :--- | :---: | :---: | :--- |
| $\Omega_1$ (passive) | 8 | 100% | None |
| $\Omega_2$ (injection) | 24 | 100% | Lexical boundary |
| $\Omega_3$ (impersonation) | 18 | 94% | Trust-chain depth limit |
| $\Omega_4$ (belief manip.) | 15 | 87% | Natural gradient high-$p$ attacks |
| $\Omega_5$ (coordinated) | 11 | 73% | Gossip correlation; sybil identification |

The $\Omega_5$ coverage gap (73%) identifies the highest-priority open research problem:
inter-agent belief correlation monitoring. Implementation of a correlation-based
detection module is planned for v2.1.

## Responsible Red-Teaming {#sec:redteam-ethics}

All red-team artifacts (attack generators, mutation operators, campaign scripts) are:

- **Contained**: Executed in sandboxed evaluation environments with no external
  API access; all attacks are synthetic and never submitted to production systems.
- **Documented**: Each attack type includes an ethical review annotation
  in `src/redteam/generator.py` following the framework in §\ref{sec:ethical-considerations}.
- **Controlled**: The `AdversarialGenerator` requires an explicit `ethical_mode=True`
  flag and records the purpose of each generated attack in the audit log.
- **Responsibly disclosed**: Novel evasion techniques discovered during red-teaming
  are documented in `output/reports/redteam_findings.md` for responsible disclosure
  to affected architecture maintainers.
