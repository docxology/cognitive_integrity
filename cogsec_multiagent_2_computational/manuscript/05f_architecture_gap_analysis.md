\newpage

# Architecture Implementation Gap Analysis {#sec:architecture-gap-analysis}

The Bayes factor in \cref{sec:bayes-factors} establishes that the gap between the parametric simulation's 96--100\% design-level ceiling and the real pipeline's 44.8\% multi-seed mean is structural rather than statistical. This section decomposes that gap into attributable components, assesses the maturity of each defense module adapter, identifies the dominant failure mode per module, and projects the detection-rate recovery achievable at each maturity level. The result is an ordered roadmap whose cumulative effect is projected to raise real-pipeline detection from $\approx 45\%$ toward the $80$--$86\%$ range without any change to the CIF formal framework itself.

## Gap Attribution Framework {#sec:gap-attribution}

For a fixed architecture $A$ and attack category $\adversary{}$, define the observed gap
\begin{equation}
\mathrm{Gap}(A, \adversary{}) = \mathrm{DR}_{\text{parametric}}(A, \adversary{}) - \mathrm{DR}_{\text{empirical}}(A, \adversary{}).
\end{equation}
\label{eq:architecture-gap}
We decompose this quantity into three non-overlapping components:

\begin{enumerate}
\item \emph{Adapter Maturity Gap} $G_{\text{adapter}}$: the portion attributable to defense-module adapters that do not fully implement the idealized detection logic assumed by the parametric simulation. A stub adapter that returns a constant score, for example, contributes entirely to $G_{\text{adapter}}$.
\item \emph{Distribution Shift Gap} $G_{\text{distribution}}$: the portion attributable to the real attack corpus exhibiting distributional properties not captured by the parametric model's calibrated base rates (difficulty, coverage, category balance).
\item \emph{Interaction Gap} $G_{\text{interaction}}$: the portion attributable to emergent multi-module interactions not captured by the parametric model's independence assumption (the product form $\prod (1 - r_i)$).
\end{enumerate}

The total gap decomposes additively: $G_{\text{total}} = G_{\text{adapter}} + G_{\text{distribution}} + G_{\text{interaction}}$. Empirically, the ablation-study pattern---Detection module carries 42\% of pipeline TPR ($\Delta\mathrm{TPR}_{\text{contribution}} = -0.052$), while Sandbox and Consensus contribute $\leq 0.002$---is consistent with $G_{\text{adapter}}$ being dominant. Modules that in principle have high detection potential (per the parametric rates) but measured near-zero marginal contribution in ablation are the signature of adapter-maturity-dominated gaps; modules whose ablation contribution matches the parametric prediction are closer to maturity.

## Adapter Maturity Scale {#sec:maturity-scale}

We adopt a 5-level maturity rubric modeled on the Capability Maturity Model Integration (CMMI) scale but specialized to defense-module adapters (\cref{tab:maturity-rubric}). Each level implies a typical range of marginal TPR contribution and a typical dominant failure mode.

Table: Adapter maturity rubric and typical marginal TPR contribution. {#tab:maturity-rubric}

| Level | Name | Description | Marginal TPR |
| --- | --- | --- | --- |
| 1 | Stub | Hardcoded scores; no domain logic | $\approx 0\%$ |
| 2 | Heuristic | Pattern matching; uncalibrated thresholds | $1$--$5\%$ |
| 3 | Statistical | Calibrated thresholds; regression features | $5$--$15\%$ |
| 4 | Adaptive | Online learning; per-architecture tuning | $15$--$30\%$ |
| 5 | Verified | Formal guarantees; cross-architecture validated | $30\%+$ |


Using the ablation contributions from \cref{sec:extended-ablation}, each CIF module can be placed on this scale:

Table: Current adapter maturity assessment per module. Evidence: $\Delta\mathrm{TPR}$ is the measured marginal detection-rate contribution when the module is removed (from \cref{tab:component-removal}); failure-mode letters follow the Type A--D taxonomy in \cref{sec:failure-modes}. {#tab:module-maturity}

| Module | Level | Evidence | Primary Failure Mode |
| --- | --- | --- | --- |
| Detection | 3 | $\Delta\mathrm{TPR} = -0.051$; statistical features | B (threshold) |
| Trust Calculus | 3 | $\Delta\mathrm{TPR} = -0.020$; authority-claim detection | B (threshold) |
| Firewall | 2 | $\Delta\mathrm{TPR} = -0.010$; pattern matching | A (feature) |
| Tripwires | 2 | $\Delta\mathrm{TPR} = -0.010$; canary monitoring | A (feature) |
| Invariants | 2 | $\Delta\mathrm{TPR} = -0.010$; rule-based | C (unexercised) |
| Consensus | 1 | $\Delta\mathrm{TPR} = 0.000$; uncalibrated mock votes | D (adapter hook) |
| Provenance | 1 | $\Delta\mathrm{TPR} = 0.000$; stub on current corpus | D (adapter hook) |
| Sandbox | 1 | $\Delta\mathrm{TPR} = 0.000$; limited contribution | C (unexercised) |


The Detection module's Level 3 rating reflects its calibrated statistical features and matches its dominant position in ablation ($\Delta\mathrm{TPR} = -0.051$, 42% of baseline). The elevated Trust Calculus impact ($\Delta\mathrm{TPR} = -0.020$) relative to earlier manuscript revisions reflects the corrected ablation key mapping (see §\ref{sec:component-removal}) — previous versions reported $\Delta\mathrm{TPR} \approx -0.007$ because a name mismatch caused the Trust Calculus adapter to remain active in all ablation configurations. The Consensus, Provenance, and Sandbox modules show $\Delta\mathrm{TPR} = 0.000$ not because their formal mechanisms are inadequate, but because their current adapters use mock/stub implementations that are not exercised by the 98-attack stratified corpus. This is a classic $G_{\text{adapter}}$ failure: the formal mechanism is sound; the plumbing that connects the corpus to the mechanism is stub-level.

## Failure Mode Taxonomy {#sec:failure-modes}

We classify adapter failures into four types, each with a distinct remediation:

\begin{itemize}
\item **Type A --- Feature Extraction Mismatch.** The attack's semantic signature is present but not represented in the adapter's feature space. Example: a paraphrased injection attack whose intent is preserved but whose surface tokens differ from the pattern vocabulary. Remediation: expand feature vocabulary or adopt embedding-based features.
\item **Type B --- Threshold Miscalibration.** The adapter computes a discriminative score but uses a decision threshold tuned for a different distribution. Example: a firewall that produces $S = 0.48$ on a medium-difficulty injection with $\tau = 0.50$, yielding a marginal miss. Remediation: per-architecture threshold tuning against held-out corpus.
\item **Type C --- Unexercised Code Path.** The defense logic is correct and well-calibrated, but the evaluation corpus never activates it. Example: the sandbox's consistency-check is correct, but the corpus does not include attacks that pass provenance and consistency yet fail corroboration. Remediation: augment corpus with targeted attack variants.
\item **Type D --- Missing Adapter Hook.** The defense module is never called for this architecture/attack combination because the architecture adapter has no hook for it. Example: consensus is not invoked in the Claude Code adapter for single-agent attack evaluations. Remediation: add architecture-specific integration hook.
\end{itemize}

The ``Primary Failure Mode'' column of \cref{tab:module-maturity} maps each current module to its dominant failure type, derived from inspection of the adapter code and from the ablation pattern (Type C modules show zero marginal contribution despite formal-model coverage; Type D modules show zero contribution across all architectures).

## Roadmap to Gap Closure {#sec:gap-closure-roadmap}

Combining the maturity assessment with the failure-mode taxonomy yields a prioritized remediation roadmap. Each entry lists the module, the current$\to$target maturity level, the remediation action, the projected marginal TPR gain, and the affected attack categories.

\begin{enumerate}
\item \emph{Detection module}, Level 3$\to$4: architecture-specific feature retraining against per-architecture corpus. Projected gain: $+15$ pp across all injection categories. Rationale: current Detection features are calibrated against a pooled corpus; per-architecture tuning recovers the remaining feature-space coverage without changing the underlying statistical model.
\item \emph{Consensus}, Level 1$\to$3: deploy with real agent voting rather than mock votes; calibrate against the coordination-attack subcorpus. Projected gain: $+12$ pp on coordination attacks. Rationale: the formal BFT guarantees from Part 1 are strong, but the adapter currently bypasses them. Wiring real votes into the adapter is an engineering task, not a research task.
\item \emph{Sandbox}, Level 1$\to$3: calibrate corroboration threshold $\kappa$ per architecture based on observed false-positive rate on the current corpus. Projected gain: $+8$ pp on belief-manipulation and trust-exploitation attacks. Rationale: $\kappa$ is currently uniform across architectures, but the architecture adapters differ in their corroboration-signal rate.
\item \emph{Provenance}, Level 1$\to$3: implement real cryptographic attestation rather than the current stub. Projected gain: $+6$ pp on tool-call-mediated and indirect-injection attacks. Rationale: provenance currently contributes $\approx 0$ because the adapter does not produce or consume provenance metadata; adding the metadata pipeline activates the formally-specified verification logic.
\end{enumerate}

The cumulative projected effect is $+35$ to $+41$ percentage points of detection-rate recovery, bringing the real-pipeline detection rate from $44.8\%$ to approximately $80$--$86\%$. Note the target levels differ by module: Detection reaches Level 4, while Consensus, Sandbox and Provenance reach Level 3. Realising the full parametric ceiling would require Level 4--5 across the board, which this roadmap does not attempt. This projection does not require any change to the CIF formal framework; it quantifies the engineering maturity required to realize the existing parametric ceiling. The Part 3 deployment guide provides the operational steps for each of these upgrades in order.
