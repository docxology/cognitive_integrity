\newpage

# Attack Corpus: Methodology and Ethical Considerations {#sec:attack-methodology}

This section documents how the attack corpus is generated, what can and cannot be concluded from it, and the ethical position of publishing it.

## Attack Generation Methodology {#sec:generation-methodology}

### Deterministic Generation {#sec:synthetic-generation}

The corpus is not collected, curated or hand-written. It is produced by a single seeded call, `AttackCorpus.generate(seed=42)`, which draws one `numpy` generator and passes it to five category modules under `src/attacks/generators/`. Each module expands parameterised templates for its categories, and the call returns 1,475 samples across fifteen categories:

- `generate_all_injection` --- 500 samples: direct, indirect and nested injection
- `generate_all_trust_exploitation` --- 200 samples: trust inflation, delegation abuse, impersonation
- `generate_all_belief_manipulation` --- 150 samples: belief injection, drift and fabrication
- `generate_all_coordination` --- 100 samples: consensus poisoning, sybil and timing attacks
- `generate_all_provenance_and_isolation` --- 525 samples: provenance laundering, sandbox escape, byzantine manipulation

Passing `extended=False` reproduces the earlier 950-item corpus without the final module. That corpus is retained only so a reader can reproduce results computed against it: it contains no instance of what the provenance, sandbox and consensus adapters detect, so those three modules score a Shapley value of exactly zero in every one of the 256 coalitions of the defense lattice. A corpus that cannot reach three of eight mechanisms cannot measure the framework, and every number reported in this paper is measured against one that can.

Because generation is a pure function of the seed, the corpus needs no distribution: it is a property of the published code, and any reader who clones the repository obtains exactly the corpus evaluated here.

### What Stands in for Review {#sec:corpus-validation}

There is no human annotation stage in this pipeline, and therefore no inter-annotator agreement to report. Three mechanical guards do the work that review would otherwise do, and each fails loudly rather than warning:

1. **Category profile completeness.** Every category must declare an adversary class and a target in `_CATEGORY_PROFILE`; a category without an entry raises at generation time rather than being silently dropped from every stratified result.
2. **Identifier uniqueness and category alignment.** Each sample is assigned a per-category sequential identifier, and the test suite asserts that counts, prefixes and category labels agree with the generator that produced them.
3. **Corpus composition.** The composition table (\cref{tab:corpus-composition-actual}) is generated from the corpus object itself rather than typed, so the paper cannot state a distribution the corpus does not have.

The honest limitation is the one this design cannot escape: the attacks are template expansions, and a detector keyed on structural features is being asked to recognise generated structure. Detection rates measured on this corpus are upper bounds relative to adversarial text written by a person trying to evade the specific detector, and are read that way throughout.

## Attack Effectiveness {#sec:effectiveness-analysis}

Per-category and per-module effectiveness is reported where it is measured rather than restated here. The module capability matrix (`output/data/module_capability_matrix.json`) records, for each of the eight defense modules, its detection rate on each of the fifteen categories and on the corpus as a whole; the ablation study (\cref{sec:ablation-summary}) records what each module contributes to a pipeline that already contains the others. The two are different questions, and the matrix exists because they had been conflated.

The summary finding is that capability is concentrated. Measured alone on the full corpus, the invariants checker detects 83.3\% and no other module exceeds 10\%; measured as ranked scorers, the drift score and the firewall pattern matcher fall below chance, with AUCs of 0.374 and 0.383 whose intervals exclude 0.5. Any claim that the layered architecture distributes work evenly across modules is not supported by this corpus, and the paper does not make it.

## Ethical Considerations {#sec:ethical-considerations}

### Dual-Use Considerations {#sec:dual-use}

The corpus is a dual-use resource. It is also, unavoidably, public: it is regenerated from published code by a published seed, so there is no version of this work in which the attacks are available to defenders and withheld from anyone else. No access tier, request process or use agreement is operated for it, and describing one would misrepresent what publishing this repository does.

That is a deliberate position rather than a concession. The attacks are template expansions of patterns already documented in the public literature on prompt injection and agent manipulation, and their value lies in being a fixed, reproducible measuring stick rather than in being novel. A corpus that cannot be regenerated cannot be used to check a reported number, which is the whole purpose it serves here.

No previously unknown vulnerability in any named third-party framework was discovered in the course of this work, so no coordinated disclosure was required and none was undertaken. The architectures named in the parametric simulation are modelled configurations, not systems that were probed.

### Defense Framework Dual-Use Considerations {#sec:defense-dual-use}

The defense framework presents its own dual-use risks, distinct from those of the corpus.

**Detection algorithm inversion.** The detection algorithms documented in \cref{sec:detection-algorithms} can be analysed to design evasive attacks that stay below detection thresholds. An adversary holding the full specification can target known blind spots or probe the feature space for classification boundaries. This risk is inherent to any published detection methodology, and it is sharpened here by the concentration reported above: an attacker who defeats the invariants checker defeats most of the pipeline.

**Trust calculus parameter exposure.** The trust decay parameter ($\delta$), delegation depth limits and threshold configurations published here would let an adversary who knew a target's exact values craft delegation chains that sit just above threshold, or time attacks to trust recovery.

**Mitigations available to a deployer.** These are approaches a deployment can take; none is claimed to have been evaluated in this paper.
1. **API abstraction**: deploy CIF behind a layer that exposes binary allow/block outcomes without confidence scores or feature contributions.
2. **Parameter randomisation**: vary threshold and decay values across instances so published defaults are not the deployed ones.
3. **Adversarial probing detection**: monitor for repeated near-threshold submissions and systematic parameter variation.

The defense composition algebra established in Part 1 holds regardless of specific parameter choices, so the theoretical guarantees survive operational parameters that differ from the published defaults. Deployment configurations are discussed in Part 3.

### Human Subjects {#sec:human-subjects}

This research involved no human subjects, no participants and no user study. Every evaluation runs against synthetic agent configurations in sandboxed processes, and no production system or real user was involved at any point. No institutional review was sought, because none of the work falls within the scope of human-subjects review.

## Data Availability {#sec:data-availability}

Everything this paper reports is public and reproducible from one repository, <https://github.com/docxology/cognitive_integrity>:

- the attack corpus, as the seeded generator that produces it;
- the benign corpus, including the deliberately hard stratum used for false-positive rates;
- every defense implementation, evaluation script and analysis script;
- the result artifacts each figure and table is derived from, under `output/data/`, each carrying a provenance record naming the script that wrote it.

There is no restricted tier and nothing is held back. Every quantity the three papers share is derived from a single ledger and checked in continuous integration, so a reader can regenerate any reported number rather than take it on trust.

## References {#sec:corpus-references}

The attack corpus contains no items from JailbreakBench \cite{chao2024jailbreakbench}, PromptInject \cite{liu2023prompt}, TensorTrust \cite{toyer2024tensortrust}, or HarmBench \cite{mazeika2024harmbench}; those benchmarks informed the \emph{design} of the attack templates, but every one of the 1,475 samples is generated by deterministic template expansion (\cref{sec:corpus-overview}). It also contains no gradient-optimised adversarial suffixes of the kind GCG produces \cite{zou2023universal}: every attack here is a readable message, which bounds what these results say about attacks that are not.
