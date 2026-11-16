\newpage

# Architecture Implementation Gap Analysis {#sec:architecture-gap-analysis}

The parametric simulation's 96--100\% design-level range and the architecture-agnostic pipeline's 86.3\% multi-seed mean come from different corpora, denominators, and evaluation modes. Their descriptive separation is not a matched-arm effect estimate, and no Bayes factor establishes that it is structural rather than statistical. This section therefore limits itself to the measured ablation and module-capability results, distinguishes marginal contribution from module coverage, and identifies engineering questions without attributing the gap to adapter maturity or projecting detection-rate gains.

## Descriptive Contrast and Attribution Limits {#sec:gap-attribution}

A fixed-architecture subtraction would require the parametric and empirical arms to share an architecture, corpus, attack-category mixture, and operating point. They do not: the multi-seed pipeline has no architecture adapter and samples all five attack families, while the historical parametric simulation evaluates 950 attacks under each of four modeled architectures. Accordingly, this paper does not estimate adapter-maturity, distribution-shift, or interaction components, and it does not claim that those components sum to the observed difference.

The measured ablation result is narrower: on its 100-attack corpus, removing Invariants costs $\Delta\mathrm{TPR}=-0.670$ from a 0.890 baseline, removing Tripwires costs 0.010, and every other removal has zero measured marginal cost. This establishes the marginal hierarchy on that corpus, not a causal decomposition of the parametric--empirical contrast.

## Marginal Contribution Is Not Maturity {#sec:maturity-scale}

A leave-one-out ablation measures only the detections lost when a module is removed from the full pipeline. It does not measure solo capability, code-path coverage, implementation maturity, or independence. Zero marginal contribution therefore cannot justify calling a module a stub or saying that it was unexercised.

The shipped artifacts directly contradict that interpretation. On the 100-attack ablation corpus, Consensus and Sandbox have solo TPRs of 0.06 and 0.05 respectively, even though removing either from the full pipeline has zero measured marginal cost. Their detections overlap with detections supplied by the remaining pipeline, especially Invariants. The separate capability experiment on all 1,475 attacks likewise reaches every module: Consensus detects 81.1\% of byzantine-manipulation samples, Provenance 20.0\% of provenance-laundering samples, and Sandbox 28.6\% of sandbox-escape samples. Those capability rates are not ablation-corpus rates and must not be substituted into the 100-attack ablation table.

## Diagnostic Questions {#sec:failure-modes}

Feature coverage, threshold calibration, corpus coverage, and integration hooks remain useful diagnostic categories for future controlled experiments. The present ablation does not assign any of them as a module's dominant failure mode. In particular, a zero leave-one-out delta is evidence of redundant detection in the full configuration, not evidence of an unexercised code path or a missing hook; the solo and capability measurements above show that the modules are reached. Likewise, the architecture-agnostic multi-seed arm cannot support architecture-specific threshold or adapter conclusions.

## Measured Module Coverage {#sec:gap-closure-roadmap}

The capability matrix describes coverage on the full 1,475-attack corpus. It does not estimate how many points any change would add to the 100-attack ablation or the 30-seed pipeline arm.

- *Detection module.* Reaches 44.0\% on belief injection, 10.0\% on Sybil attacks, and under 8\% on every other category, for 3.3\% overall. Measured as a ranked scorer, its drift component sits below chance (AUC 0.373); any retuning requires a new controlled evaluation rather than an assumed recovery.
- *Consensus.* Reaches 81.1\% on byzantine manipulation and zero on every other category, for 9.6\% overall. This is category-specific coverage, not evidence that the module was absent from the ablation.
- *Sandbox.* Reaches 28.6\% on sandbox escape and zero elsewhere, for 3.4\% overall. The multi-seed arm supplies no architecture-specific corroboration-rate comparison.
- *Provenance.* Reaches 20.0\% on provenance laundering and zero elsewhere, for 2.4\% overall. This is a measured coverage limitation; its causes and the effect of adding metadata require separate experiments.

These observations quantify what each module reaches without claiming that engineering maturity explains the 9.7--11-point descriptive separation between evaluation modes.
