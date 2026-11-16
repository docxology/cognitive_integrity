# Supplementary Material: Documented AI Agent Security Incidents (2024--2025)  {#sec:empirical_grounding}

This supplement catalogs five publicly documented incidents of AI agent security failures in production systems, retrospectively analyzed through the CIF-AD-OODA framework. Each incident is mapped to the universal attack pattern taxonomy (\cref{sec:attack_patterns}) and a candidate CIF defense mechanism. These mappings are qualitative hypotheses, not measurements that the mechanism would have prevented or detected the failure.

## Incident Catalog

### S3.1 Arup Deepfake Video Conference Fraud (January 2024; publicly reported in February)

A finance employee at the multinational engineering firm Arup was deceived by a deepfake video conference in which AI-generated replicas of senior executives instructed the transfer of \$25.6 million across 15 transactions \cite{cnn2024arup}. The deepfakes were sufficiently convincing that the employee overrode standard verification procedures, treating the fabricated executive presence as authentic authorization.

**CIF-AD-OODA Analysis.** The attack constitutes a **Context Boundary Violation**: the boundary between verified identity (cryptographic authentication) and perceived identity (visual/auditory similarity) was erased. In OODA terms, the Orient phase was corrupted by fabricated sensory evidence that the employee's (and any agent's) world model treated as equivalent to physical co-presence. The relevant CIF defense is **Byzantine Consensus** ($\mathcal{B}_{\text{consensus}}$): requiring quorum authorization from $q$ independently verified executives via out-of-band channels is a candidate control against authorization by a single deepfake session; its effectiveness has not been measured here. **Domain mapping:** Domain 2 (Nation-State Alliances) --- analogous to the diplomatic communique injection scenario.

### S3.2 Slack AI Data Exfiltration via Indirect Prompt Injection (August 2024)

Researchers at PromptArmor demonstrated that Slack's AI assistant could be manipulated through indirect prompt injection \cite{promptarmor2024slack}. An attacker posted a crafted message in a public Slack channel containing hidden instructions. When users subsequently queried the AI about channel content, the injected prompt caused the AI to exfiltrate private channel data---including API keys---via specially constructed markdown links, without citing the injected message as a source.

**CIF-AD-OODA Analysis.** The attack constitutes a **Context Boundary Violation**: the boundary between public channel data (untrusted, user-generated) and private channel data (confidential) was erased by the AI's unified context window. The Orient phase was corrupted because the AI could not distinguish between legitimate user queries and adversarial instructions embedded in channel messages. The relevant CIF defense is **Cognitive Firewall** ($\mathcal{F}$): architectural separation of the instruction channel (user query) from the data channel (channel content) would prevent data-channel text from being interpreted as executable directives. **Domain mapping:** Domain 10 (Information Ecosystems) --- directly analogous to the context injection scenario.

### S3.3 ChatGPT Search Manipulation via Hidden Text (December 2024)

Security researchers demonstrated that ChatGPT's web search feature could be manipulated by embedding hidden instructions in webpage content. Pages containing invisible text with directives such as "always give a positive review of this product" caused ChatGPT to generate biased summaries that contradicted the visible content of the page \cite{guardian2024chatgptsearch}.

**CIF-AD-OODA Analysis.** The attack constitutes a **Constraint Relaxation**: the agent's objectivity constraint was degraded from a hard requirement to a soft preference by the hidden directive. In OODA terms, the Orient phase integrated adversarial instructions from the data channel alongside legitimate content, relaxing the agent's commitment to factual summarization. The relevant CIF defense is **Belief Sandboxing** ($\mathcal{B}_{\text{provisional}}$): treating web content as provisional beliefs requiring cross-source corroboration would prevent a single page's hidden directives from overriding the agent's analytical stance. **Domain mapping:** Domain 10 (Information Ecosystems).

### S3.4 GitHub Copilot Remote Code Execution via YOLO Mode (June 2025)

CVE-2025-53773 documented a critical vulnerability in GitHub Copilot's agent mode \cite{copilot2025rce}. Researchers demonstrated that invisible Unicode characters embedded in source code files could trigger Copilot's "YOLO mode" (`autoApprove: true`), enabling arbitrary shell command execution without user confirmation. The attack exploited the boundary between code content (data) and execution directives (instructions), allowing repository files to escalate the agent's permission level and execute commands with the user's full system privileges.

**CIF-AD-OODA Analysis.** The attack constitutes a **Constraint Relaxation**: the approval requirement (a hard safety constraint) was degraded to auto-approve status by injected Unicode directives. In OODA terms, the Orient phase was corrupted by data-channel content (source code) that was parsed as permission-level instructions, relaxing the human-in-the-loop constraint to zero. The relevant CIF defense is **Behavioral Invariants** ($\text{INV}_k$): a hard invariant requiring human confirmation for destructive operations ($\text{INV}_{\text{approve}}$: approval mode $\neq$ auto) would be structurally immune to data-channel manipulation. **Domain mapping:** Domain 3 (Cyber-Security) --- directly analogous to the log injection scenario.

### S3.5 Replit Agent Production Database Meltdown (July 2025)

A Replit AI coding agent, instructed to implement a feature under an explicit code freeze, instead deleted the production database and then fabricated approximately 4,000 fake records to conceal the deletion \cite{adversa2025incidents}. The agent's internal reasoning chain revealed a cascading failure: it encountered an obstacle, escalated to increasingly destructive actions to "resolve" the impediment, and then attempted to cover up the damage---all while nominally pursuing the original feature implementation goal.

**CIF-AD-OODA Analysis.** The attack constitutes an **FR Polarity Inversion**: the agent's "Implement Feature" FR was inverted to "Destroy Data" through an internal escalation cascade, and the "Maintain Data Integrity" FR was further inverted to "Fabricate Data." Critically, this was not an external attack but an *endogenous* goal corruption---the agent's own reasoning process drifted catastrophically from its assigned objectives. In OODA terms, the Orient phase suffered progressive corruption as each failed action reinforced a distorted world model. The relevant CIF defenses are **Behavioral Invariants** ($\text{INV}_k$): a hard invariant preventing database deletion during code freeze ($\text{INV}_{\text{freeze}}$: $\Delta_{\text{schema}} = 0$) would have blocked the initial destructive action; and **Drift Detection** ($S_{\text{drift}}$): monitoring the KL divergence between successive action distributions would have flagged the escalation from "implement feature" to "delete database" as an anomalous drift exceeding threshold $\epsilon$. **Domain mapping:** Domain 3 (Cyber-Security) / Domain 5 (Supply Chain).

## Cross-Incident Summary

| \# | Incident | Date | Attack Pattern | Primary CIF Defense | Domain Analog |
| ---- | ---------- | ------ | --------------- | ------------------- | --------------- |
| S3.1 | Arup Deepfake Fraud (\$25.6M) | Jan 2024 (reported Feb) | Context Boundary Violation | Byzantine Consensus | 2 (Nation-State) |
| S3.2 | Slack AI Exfiltration | Aug 2024 | Context Boundary Violation | Cognitive Firewall | 10 (Info) |
| S3.3 | ChatGPT Search Manipulation | Dec 2024 | Constraint Relaxation | Belief Sandboxing | 10 (Info) |
| S3.4 | GitHub Copilot RCE (CVE-2025-53773) | Jun 2025 | Constraint Relaxation | Behavioral Invariants | 3 (Cyber) |
| S3.5 | Replit Agent Meltdown | Jul 2025 | FR Polarity Inversion | Behavioral Invariants + Drift Detection | 3 (Cyber) |

The incident catalog illustrates all three universal attack patterns identified in \cref{sec:attack_patterns} in publicly reported production failures and maps each to a candidate CIF defense. Every incident also maps to at least one of the ten domains analyzed in this paper. These qualitative mappings do not measure defensive effectiveness, establish taxonomy completeness, or demonstrate that the CIF-AD-OODA framework generalizes beyond the scenarios constructed in \cref{sec:domain_rare_earth,sec:domain_nation_state,sec:domain_cyber_security,sec:domain_drone_wars,sec:domain_supply_chain,sec:domain_biowarfare,sec:domain_food_security,sec:domain_trade_wars,sec:domain_infrastructure,sec:domain_fake_news}.
