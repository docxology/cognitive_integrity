\newpage

# Incident Response Playbooks {#sec:incident-response}

![Deployment lifecycle phases (Pre-Deployment $\rightarrow$ Operational $\rightarrow$ Incident Response) with CIF security activities.](figures/timeline.png){#fig:timeline width=85%}

When the Cognitive Integrity Framework (CIF) detects an attack, automated response handles quarantine and escalation. But automated response is not enough — effective recovery requires human judgment, forensics, and prevention hardening. These playbooks guide the human response to each adversary class.

> **Companion reference.** The Supplementary Material S3 of this unified paper catalogues six documented 2024–2025 AI-agent security incidents (Replit agent meltdown, GitHub Copilot RCE CVE-2025-53773, Slack AI data exfiltration, a \$3.2M procurement fraud, and two others) with full attack-chain reconstructions mapped to the adversary classes below. When rehearsing these playbooks, using the S3 incident transcripts as training exercises grounds the guidance in real production failures.

**General principles applying to all incidents**:

1. **Log first, analyze second** — never modify state before capturing it.
2. **Containment before eradication** — isolate before investigating.
3. **Preserve the belief audit trail** — agent interaction history ($H_i$) is forensic gold.
4. **Assume lateral movement** — one detected compromise means others may be undetected.

The playbooks below are organized by adversary class ($\Omega_1$ through $\Omega_5$). Each is a sequence of time-boxed steps with explicit handoffs; treat the timelines as targets, not strict SLAs.

---

## Playbook 1: $\Omega_1$ External Adversary (Prompt Injection)

**Detection triggers**: Firewall score $> \tau_1 = 0.7$; or tripwire CRITICAL on any agent.

**Timeline**: Resolution typically 15–60 minutes for isolated injection.

**Steps**:

1. **[0–2 min] Quarantine**. Move affected agent(s) to provisional belief mode. No further message processing until cleared.
2. **[2–10 min] Preserve state**. Capture full cognitive state snapshot (beliefs, goals, interaction history $H_i$) before any rollback.
3. **[10–20 min] Triage**. Identify injection point (which message?), payload type (identity? scope? credential?), and affected belief(s).
4. **[20–30 min] Containment**. Roll back affected beliefs to last verified state. Invalidate any actions taken since the infection point.
5. **[30–45 min] Recovery**. Re-inject from trusted source. Run belief consistency check. Verify invariants.
6. **[45–60 min] Hardening**. Update firewall pattern library with injection variant. Log to attack corpus (Part 2, §3.1) for future training.

**Signs of escalation to $\Omega_3$**: the injected instruction attempts to change the agent's role, modify its trust scores, or alter its goal set. If any of these, escalate to Playbook 3.

---

## Playbook 2: $\Omega_2$ Peripheral Adversary (Tool/API Compromise)

**Detection triggers**: Provenance verification failure; unexpected tool output format; belief contradiction between tool output and independent source.

**Timeline**: 30–120 minutes depending on tool scope.

**Steps**:

1. **[0–5 min] Disable tool**. Immediately route to fallback API or queue pending tasks.
2. **[5–15 min] Audit affected beliefs**. All beliefs sourced from the compromised tool are now provisional. Query the provenance graph: which beliefs trace to this tool?
3. **[15–30 min] Re-verify from independent source**. For each affected belief, obtain corroboration from an independent source ($\kappa \geq 2$). Beliefs that cannot be corroborated are invalidated.
4. **[30–60 min] Impact assessment**. Which downstream actions were taken based on invalidated beliefs? Are those actions reversible?
5. **[60–90 min] Recovery**. Re-query from a verified alternative source. Rebuild affected belief states.
6. **[90–120 min] Post-incident**. Report tool provider (responsible disclosure if API). Update trust score for tool. Add to provenance monitoring watchlist.

**Note**: If the tool compromise persisted for multiple interaction rounds, downstream agent beliefs may be deeply poisoned — the provenance graph may show a "belief tree" rooted at the compromised tool. Full tree invalidation is required; this can disrupt multiple agents.

---

## Playbook 3: $\Omega_3$ Insider Adversary (Agent Compromise)

**Detection triggers**: Identity tripwire violation; behavioral deviation from role invariants; goal drift (KL divergence $> \theta_{\text{drift}} = 0.3$).

**Timeline**: 60–240 minutes; complex forensics required.

**Steps**:

1. **[0–5 min] Hard quarantine**. Remove agent from all communication channels immediately. No outbound messages.
2. **[5–30 min] Forensic capture**. Full snapshot: beliefs, goals, interaction history, tool call log, outbound messages.
3. **[30–60 min] Root cause analysis**. When did compromise occur? (Inspect interaction history for anomalous message, unusual source, or trust escalation.) What was exfiltrated or acted upon?
4. **[60–120 min] Downstream invalidation**. All beliefs that the compromised agent shared with other agents are now suspect. Trace the agent's output messages and invalidate received beliefs in those agents.
5. **[120–180 min] Credential rotation**. Any credentials, API keys, or authorization tokens accessible to the compromised agent must be rotated.
6. **[180–240 min] Recovery**. Restart agent from clean state using fresh initialization. Replay only messages from verified sources.
7. **Post-incident**. Review training data and system prompt for sleeper agent patterns. Consider Spotcheck protocol for all agents with similar role profiles.

This is the most consequential playbook — $\Omega_3$ compromise typically requires full audit of the affected agent's interaction history and all downstream agents.

---

## Playbook 4: $\Omega_4$ Coordination Adversary (Sybil/Coalition)

**Detection triggers**: Byzantine consensus flags multiple faulty agents; trust score bimodality (cluster of agents with inflated mutual trust); Sybil infiltration alert.

**Timeline**: 30–90 minutes.

**Steps**:

1. **[0–5 min] Conservative consensus**. Fall back to unanimous voting threshold until coalition is identified.
2. **[5–20 min] Trust graph analysis**. Plot the trust matrix. Coalition members typically show elevated mutual trust (trust inflation). Identify cluster.
3. **[20–40 min] Isolation**. Quarantine coalition members. Reduce their trust floors to minimum.
4. **[40–60 min] Verify honest quorum**. Confirm remaining agents still satisfy $n \geq 3f+1$ (with $f$ now being the remaining suspect agents, if any). If not, require human-in-the-loop for consensus decisions.
5. **[60–90 min] Recovery**. Bootstrap fresh consensus state from isolated honest agents.
6. **Post-incident**. Implement cryptographic attestation for agent identity verification. Consider hardware attestation for critical production deployments.

**Note**: CIF's trust decay ($\delta^d$) and bounded trust guarantee (Theorem 4.2, Part 1) mean that reputation farming cannot drive a Sybil agent to unlimited influence. However, it *can* inflate trust within the coalition — the trust matrix visualization is the key forensic tool here.

---

## Playbook 5: $\Omega_5$ Emergent Misalignment (Distributed Drift)

**Detection triggers**: Colony drift score exceeds threshold; anomalous output distribution from multiple agents simultaneously; behavioral fingerprint deviates from baseline over extended period.

**Critical caveat**: CIF detects **74.3% of emergent misalignment cases** (Part 2's 30-seed colony benchmark; an earlier single-seed figure of 56.1% is not the publication estimate). This means roughly a quarter of such cases will *not* trigger automated response — operator vigilance is the primary defense.

**Steps**:

1. **[0–10 min] System pause**. Freeze all agent interactions. Lock all belief states. Do not allow new interactions until investigation complete.
2. **[10–30 min] Behavioral fingerprinting**. Sample recent outputs from all agents. Compare statistical distribution of outputs to baseline behavioral fingerprint.
3. **[30–90 min] Gradual restart**. Start with most-constrained agents (reporters, validators) in high-security mode. Observe for 30 minutes before enabling specialists.
4. **[90–180 min] Orchestrator verification**. If orchestrator behavior has changed, this is the most serious scenario. Verify orchestrator's interaction history against human-approved task definitions.
5. **Preventive monitoring**. Implement **weekly behavioral audits** — statistical comparison of agent output distributions against baseline. This is the primary detection mechanism for the 44% of $\Omega_5$ cases CIF misses.

**Practical note**: Emergent misalignment often develops over days or weeks, not minutes. The most effective defense is not detection-after-the-fact but **baseline maintenance**: capture agent behavioral fingerprints at deployment and compare weekly. A drift that is invisible in any single interaction may be visible as a distribution shift across thousands of interactions.
