\vspace*{2cm}

\begin{center}
\begin{minipage}{0.7\textwidth}
\centering
\Large\itshape
``The difference between theory and practice\\[0.3em]
is larger in practice than in theory.''
\vspace{1em}

\normalsize\upshape
--- Jan van de Snepscheut, Computer Scientist
\end{minipage}
\end{center}

\vspace{2cm}

# Abstract

This paper provides computational validation of the **Cognitive Integrity Framework (CIF)** introduced in Part 1. We implement the complete defense suite—cognitive firewalls, belief sandboxes, trust calculus, and Byzantine-tolerant consensus—and evaluate performance across production multiagent architectures.

## Contributions

- **Attack Corpus**: 950 cognitive attacks across four categories (prompt injection, trust exploitation, belief manipulation, coordination attacks)
- **Cross-Architecture Validation**: Evaluation across Claude Code, AutoGPT, CrewAI, LangGraph, MetaGPT, and Camel
- **Detection Performance**: 94% detection rate with layered defenses; 20-25% latency overhead
- **Statistical Analysis**: Significance testing with large effect sizes (Cohen's d > 0.8), ablation studies, scalability benchmarks

## Key Findings

1. **Composition Matters**: No individual defense achieves acceptable protection; layered composition yields multiplicative detection improvement
2. **Trust Decay Works**: Bounded delegation (δ^d) prevents trust amplification across all architectures
3. **Architecture Vulnerability**: Peer-to-peer systems show largest relative improvement, confirming lateral movement analysis

All notation follows definitions from Part 1 (Supplementary Section S03).

## Paper Series

**DOI**: 10.5281/zenodo.18364128

This is Part 2 of the *Cognitive Security for Multiagent Operators* series:

- **Part 1** (DOI: 10.5281/zenodo.18364119): Formal foundations and theoretical analysis
- **Part 2** (this paper): Computational validation and implementation
- **Part 3** (DOI: 10.5281/zenodo.18364130): Practical deployment guidance
