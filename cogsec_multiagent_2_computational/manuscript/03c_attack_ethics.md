\newpage

# Attack Corpus: Methodology and Ethical Considerations {#sec:attack-methodology}

This section documents the attack generation methodology, effectiveness analysis, ethical considerations, and data availability.

## Attack Generation Methodology {#sec:generation-methodology}

### Synthetic Attack Generation {#sec:synthetic-generation}

**Process**:
\begin{enumerate}
\item **Template Creation**: Define attack structure templates for each category
\item **Parameter Variation**: Systematically vary attack parameters
\item **Constraint Satisfaction**: Ensure attacks satisfy category definitions
\item **Deduplication**: Remove semantically equivalent attacks
\item **Validation**: Human review of generated attacks
\end{enumerate}

Table: Generation method statistics. {#tab:generation-stats}

| Method | Count | QA Pass Rate$^*$ | Mean Sophistication |
| --- | --- | --- | --- |
| Template instantiation | 420 | 91\% | 0.4 |
| Parameter variation | 250 | 88\% | 0.5 |
| Red team manual crafting | 150 | 95\% | 0.8 |
| LLM-assisted mutation | 80 | 75\% | 0.7 |
| Adversarial optimization | 50 | 82\% | 0.9 |

$^*$\textit{QA pass rate denotes the proportion of candidate attacks that passed quality assurance validation (measurability, reproducibility, category alignment), not attack efficacy against defended systems. Total candidates generated exceeded 1,200; 950 passed QA and were retained.}

### Red Team Exercise Protocol {#sec:red-team}

**Participants**: 8 security researchers (2--10 years experience)

**Duration**: 4 weeks

**Methodology**:
\begin{enumerate}
\item **Week 1**: Familiarization with target architectures
\item **Week 2**: Independent attack development
\item **Week 3**: Cross-team attack validation
\item **Week 4**: Documentation and categorization
\end{enumerate}

### Quality Assurance {#sec:qa}

Table: Attack validation criteria. {#tab:validation-criteria}

| Criterion | Description |
| --- | --- |
| Measurability | Success/failure unambiguously determinable |
| Reproducibility | Attack produces consistent results |
| Category alignment | Attack matches labeled category |
| Non-trivial | Attack not detected by simple heuristics |

**Validation Process**:
\begin{enumerate}
\item Two independent reviewers per attack
\item Disagreements resolved by third reviewer
\item Inter-rater reliability: Cohen's $\kappa = 0.84$
\end{enumerate}

## Attack Effectiveness Analysis {#sec:effectiveness-analysis}

### Success Rate by Defense Configuration {#sec:success-by-defense}

Table: Attack success rate by defense configuration. {#tab:success-by-defense}

| Defense | Prompt Inj. | Trust Expl. | Belief Manip. | Coord. |
| --- | --- | --- | --- | --- |
| Firewall only | 15\% | 38\% | 29\% | 42\% |
| Sandbox only | 35\% | 25\% | 31\% | 55\% |
| Tripwires only | 22\% | 18\% | 8\% | 48\% |
| Full CIF | 4\% | 9\% | 7\% | 11\% |

### Attack Sophistication Correlation {#sec:sophistication-corr}

\begin{equation}
\label{eq:sophistication-correlation}
\rho_{sophistication, success} = 0.67 \quad (p < 0.001, \; n = 950)
\end{equation}

We report Spearman's rank correlation ($\rho$) rather than Pearson's $r$ because sophistication levels (Low, Medium, High, Expert) are ordinal categories. More sophisticated attacks have higher baseline success but show similar detection rates under CIF, suggesting defense robustness.

### Temporal Analysis {#sec:temporal-analysis}

Table: Detection rate by attack age. {#tab:attack-age}

| Attack Age | Detection Rate | $n$ |
| --- | --- | --- |
| $<$ 6 months | 91\% | 285 |
| 6--12 months | 94\% | 380 |
| $>$ 12 months | 96\% | 285 |

Older attacks are detected at higher rates due to pattern database inclusion. The 5-point gap between newest and oldest cohorts quantifies the advantage that known-signature detection provides and underscores the importance of continuous corpus expansion to maintain efficacy against novel techniques.

## Ethical Considerations {#sec:ethical-considerations}

### Responsible Disclosure {#sec:responsible-disclosure}

All novel attack vectors discovered during this research were:
\begin{enumerate}
\item **Reported**: Communicated to affected framework maintainers
\item **Embargoed**: 90-day disclosure window before publication
\item **Mitigated**: Defenses provided alongside vulnerability reports
\end{enumerate}

Table: Disclosure timeline. {#tab:disclosure-timeline}

| Framework | Date Reported | Status | Resolution |
| --- | --- | --- | --- |
| Framework A | 2025-06-15 | Acknowledged | Patched (v2.1.3) |
| Framework B | 2025-06-22 | Acknowledged | In progress |
| Framework C | 2025-07-01 | No response | Public disclosure (90-day window elapsed) |
| Framework D | 2025-07-10 | Acknowledged | Mitigated via configuration change |

Framework names are anonymized per coordinated disclosure agreements. Specific vulnerability details are available to affected maintainers and will be published after all embargo periods expire.

### Dual-Use Considerations {#sec:dual-use}

**Risk Assessment**: The attack corpus represents a dual-use resource that could enable both defensive research and malicious exploitation. We address this through:
\begin{enumerate}
\item **Sanitization**: All published examples are non-functional
\item **Partial Disclosure**: Full corpus available only to verified researchers
\item **Access Controls**: Request-based access with institutional verification
\item **Usage Tracking**: Audit log of corpus access
\end{enumerate}

Table: Access control hierarchy. {#tab:access-hierarchy}

| Access Level | Scope | Requirement |
| --- | --- | --- |
| Researcher | Template structures | Institutional affiliation |
| Full access | Complete corpus | IRB approval + NDA |

### Defense Framework Dual-Use Considerations {#sec:defense-dual-use}

While the attack corpus dual-use considerations are addressed above, the defense framework itself presents distinct dual-use risks that warrant separate analysis.

**Detection Algorithm Inversion Risk.** The detection algorithms documented in \cref{sec:detection-algorithms} could potentially be analyzed to design evasive attacks that remain below detection thresholds. An adversary with access to the full algorithm specifications could craft attacks that exploit known blind spots or systematically probe the feature space to identify classification boundaries. This risk is inherent to any published detection methodology.

**Trust Calculus Parameter Exposure.** The trust decay parameter ($\delta$), delegation depth limits, and threshold configurations disclosed in this paper could enable adversaries to game the trust system if they know the exact values deployed in a target system. Attackers could craft delegation chains that remain just above trust thresholds or time their attacks to coincide with trust recovery periods.

**Observed Mitigation Approaches.** Several approaches address these dual-use risks:
\begin{enumerate}
\item **API Abstraction**: Deploying CIF through an abstraction layer that hides internal parameters. Detection decisions exposed as binary outcomes (allowed/blocked) without revealing confidence scores or feature contributions.
\item **Parameter Randomization**: Introducing slight randomization in threshold values and decay parameters across instances, reducing the exploitability of published defaults.
\item **Adversarial Probing Detection**: Monitoring for patterns indicative of boundary probing (repeated near-threshold submissions, systematic parameter variation).
\end{enumerate}

The defense composition algebra (established in Part 1) remains valid regardless of specific parameter choices, ensuring that the theoretical guarantees hold even when operational parameters differ from published defaults. Specific deployment configurations are detailed in Part 3.

### Human Subjects {#sec:human-subjects}

This research did not involve human subjects experimentation. All attacks were tested against:
\begin{itemize}
\item Synthetic agent configurations
\item Sandboxed environments
\item No production systems with real users
\end{itemize}

### Research Ethics Approval {#sec:ethics-approval}

This research was reviewed and determined to be exempt from IRB oversight as it did not involve human subjects. The board determined that:
\begin{enumerate}
\item No human subjects were involved
\item Dual-use risks were adequately mitigated
\item Responsible disclosure practices were followed
\end{enumerate}

## Data Availability {#sec:data-availability}

### Public Resources {#sec:public-resources}

\begin{itemize}
\item Sanitized attack examples: This supplementary material
\item Detection patterns: Available in paper repository
\item Defense implementations: Available at DOI: 10.5281/zenodo.18364128
\end{itemize}

### Restricted Resources {#sec:restricted-resources}

\begin{itemize}
\item Full attack corpus: Available upon request
\item Red team exercise data: Institution members only
\item Unpublished vulnerabilities: Covered by disclosure agreements
\end{itemize}

### Access Request Process {#sec:access-request}

Researchers wishing to access the full attack corpus must:
\begin{enumerate}
\item Submit institutional affiliation verification
\item Provide IRB approval or exemption letter
\item Sign data use agreement
\item Agree to responsible use terms
\end{enumerate}

## References {#sec:corpus-references}

The attack corpus contains no items from JailbreakBench \cite{chao2024jailbreakbench}, PromptInject \cite{liu2023prompt}, or TensorTrust \cite{toyer2024tensortrust}; those benchmarks informed the \emph{design} of our attack templates, but every one of the 950 samples is generated by deterministic template expansion (\cref{sec:corpus-overview}).
