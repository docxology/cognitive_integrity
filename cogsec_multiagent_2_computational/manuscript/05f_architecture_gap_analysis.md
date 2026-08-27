\newpage

# Architecture Implementation Gap Analysis {#sec:architecture-gap-analysis}

The Bayes factor in \cref{sec:bayes-factors} establishes that the gap between the parametric simulation's 96--100\% design-level ceiling and the real pipeline's 86.3\% multi-seed mean is structural rather than statistical. This section decomposes that gap into attributable components, assesses the maturity of each defense module adapter, identifies the dominant failure mode per module, and projects the detection-rate recovery achievable at each maturity level. The result is an ordered roadmap whose cumulative effect is projected to raise real-pipeline detection from $\approx 45\%$ toward the $80$--$86\%$ range without any change to the CIF formal framework itself.

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

The total gap decomposes additively: $G_{\text{total}} = G_{\text{adapter}} + G_{\text{distribution}} + G_{\text{interaction}}$. Empirically, the ablation-study pattern---the Invariants module carries most of the pipeline ($\Delta\mathrm{TPR} = -0.650$ of a 0.890 TPR), while six of the eight modules, Detection and the Firewall and Sandbox among them, contribute exactly $0.000$ marginally on this corpus---is consistent with $G_{\text{adapter}}$ being dominant. Modules that in principle have high detection potential (per the parametric rates) but measured near-zero marginal contribution in ablation are the signature of adapter-maturity-dominated gaps; modules whose ablation contribution matches the parametric prediction are closer to maturity.

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
| Detection | 3 | $\Delta\mathrm{TPR} = 0.000$; statistical features | B (threshold) |
| Trust Calculus | 3 | $\Delta\mathrm{TPR} = 0.000$; authority-claim detection | B (threshold) |
| Firewall | 2 | $\Delta\mathrm{TPR} = 0.000$; pattern matching | A (feature) |
| Tripwires | 2 | $\Delta\mathrm{TPR} = -0.020$; canary monitoring | A (feature) |
| Invariants | 2 | $\Delta\mathrm{TPR} = -0.650$; rule-based | C (unexercised) |
| Consensus | 1 | $\Delta\mathrm{TPR} = 0.000$; uncalibrated mock votes | D (adapter hook) |
| Provenance | 1 | $\Delta\mathrm{TPR} = 0.000$; stub on current corpus | D (adapter hook) |
| Sandbox | 1 | $\Delta\mathrm{TPR} = 0.000$; limited contribution | C (unexercised) |


The Detection module holds a Level 3 rating on the strength of its calibrated statistical features, yet its marginal contribution in ablation is $\Delta\mathrm{TPR} = 0.000$: the Invariants module catches everything Detection catches on this corpus, and leave-one-out removal cannot see a detector whose output is a subset of another's. Level and marginal contribution are therefore distinct properties, and the rubric in \cref{tab:maturity-rubric} states adapter engineering maturity rather than measured share. Trust Calculus sits in the same position ($\Delta\mathrm{TPR} = 0.000$ marginally). The Consensus, Provenance, and Sandbox modules show $\Delta\mathrm{TPR} = 0.000$ for a different reason: not because their formal mechanisms are inadequate, but because their current adapters use mock/stub implementations that are not exercised by the 100-attack stratified corpus. This is a classic $G_{\text{adapter}}$ failure: the formal mechanism is sound; the plumbing that connects the corpus to the mechanism is stub-level.

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

Combining the maturity assessment with the failure-mode taxonomy yields a prioritized remediation roadmap.

Each entry lists the module, the gap the capability matrix measures, and the remediation that would close it. No projected point gain is quoted for any of them. A marginal-gain estimate is only meaningful against a fixed baseline and a fixed corpus, and neither is fixed here; what is stated instead is what each module does and does not reach, measured on the full 1,475-item corpus.

- *Detection module.* Reaches 44.0\% on belief injection and under 8\% on every other category, for 3.3\% overall. Its features are calibrated against a pooled corpus; per-architecture tuning would recover feature-space coverage without changing the underlying statistical model. Measured as a ranked scorer its drift component sits below chance (AUC 0.374), so retuning has to be validated against ranking quality and not against threshold accuracy alone.
- *Consensus.* Reaches 81.1\% on byzantine manipulation and zero on every other category, for 9.6\% overall. This is the intended shape rather than a defect: the module answers one question well. What is missing is coverage of consensus poisoning and sybil attacks, which the trust module partly reaches instead.
- *Sandbox.* Reaches 28.6\% on sandbox escape and zero elsewhere, for 3.4\% overall. The corroboration threshold $\kappa$ is uniform across architectures while the adapters differ in their corroboration-signal rate, so per-architecture calibration is the first move.
- *Provenance.* Reaches 20.0\% on provenance laundering and zero elsewhere, for 2.4\% overall. The adapter does not produce or consume cryptographic attestation, so the formally specified verification logic is only partly exercised; adding the metadata pipeline is the remediation.

None of this requires a change to the CIF formal framework. It quantifies the engineering maturity that stands between the current pipeline and the design-level ceiling, and that distance is now 9.7 to 11 percentage points rather than the much larger gap this section was originally written to explain. The Part 3 deployment guide gives the operational steps in order.
