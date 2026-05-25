\newpage

# Per-Role Security Hardening {#sec:subagent-hardening}

The Cognitive Integrity Framework (CIF) is not a monolithic configuration — each agent role in a multiagent system has different attack exposure, different trust levels, and different behavioral invariants. A uniform defense posture either over-constrains leaf agents (paying latency cost where it is not needed) or under-protects critical nodes (leaving the orchestrator with the same defenses as a reporter). This section provides role-specific security configurations for the five most common agent archetypes observed in production deployments.

The shared CIF defenses — Cognitive Firewall, Belief Sandbox, Trust Decay, Byzantine Consensus, Tripwires — apply to every role. What changes per role is the *parameterization* of those defenses and the *role-specific invariants* bolted on top.

---

## Role 1: The Orchestrator

**Attack exposure**: Highest. Compromise of the orchestrator is effectively total system compromise — it controls delegation, approves actions, and arbitrates consensus.

**Primary risk profile**: $\Omega_3$ (direct compromise via context poisoning), $\Omega_5$ (sleeper activation from training-time backdoor).

**Recommended configuration**:

* **Trust decay $\delta = 0.60$** — aggressive decay. Trust does not propagate far from the orchestrator; workers two hops away start from a low trust floor.
* **Firewall rejection threshold $\tau_1 = 0.5$** — lower than default. The orchestrator is suspicious of inputs on principle.
* **Corroboration threshold $\kappa = 3$** — require three independent sources before accepting any critical belief into the orchestrator's verified belief set.
* **Byzantine consensus required for all delegation decisions**, not just coordination ones. If the orchestrator is about to assign work to a worker, the decision passes through consensus rather than being taken unilaterally.

**Mandatory tripwires**:

* **Identity**: *"I am the orchestrator. My ID is `[ORCHESTRATOR_ID]`."*
* **Scope**: *"I may only delegate to agents in `[APPROVED_AGENT_LIST]`."*
* **Escalation**: *"I may not execute irreversible actions without `[HUMAN_APPROVAL_TOKEN]`."*

**The upward monitoring problem**: The orchestrator is unique in that it cannot be monitored from above — by construction, there is no higher authority in the agent hierarchy. Traditional CIF monitoring relies on a trusted supervisor observing a subordinate; for the orchestrator, this pattern is inverted. The solution is **upward monitoring**: worker agents carry tripwires that fire when orchestrator behavior looks anomalous from below. Recommended worker-side tripwires include:

* *"The orchestrator has not changed my role definition since session start."*
* *"I have not received commands outside my declared scope in the past $N$ interactions."*
* *"The orchestrator's command patterns match the behavioral fingerprint captured at deployment."*

When multiple workers fire upward-monitoring tripwires simultaneously, a Byzantine-style quorum of "orchestrator misbehavior" detections escalates immediately to human review. This provides detection of orchestrator compromise from below — the only practical defense against $\Omega_5$-class systemic attacks on the top of the hierarchy.

---

## Role 2: The Specialist

Specialists are domain-focused workers: the coding agent, the research agent, the vision agent. Each has a narrow scope and a well-defined task interface.

**Attack exposure**: Medium. Specialists are valuable targets but have limited scope — compromise damages a work product, not the whole system.

**Primary risk profile**: $\Omega_1$ (prompt injection via task content), $\Omega_2$ (poisoned tool outputs feeding into the specialist's reasoning).

**Recommended configuration**:

* **Trust decay $\delta = 0.80$** (default). Trust propagation within the specialist's scope is acceptable.
* **Firewall rejection threshold $\tau_1 = 0.7$** (default). The specialist accepts more input diversity than the orchestrator because specialists are designed to process user-provided task content.
* **Scope enforcement is the primary control**, not trust decay or consensus.

**Mandatory tripwires**:

* **Scope**: *"I only modify files in `[APPROVED_PATHS]`."* / *"I only process documents from `[APPROVED_SOURCES]`."*
* **Role**: *"I am a `[ROLE_NAME]` agent. I do not have admin privileges."*

Specialists should never receive instructions that expand their scope mid-task without re-authentication via the orchestrator. The corroboration threshold $\kappa$ applies specifically to "scope expansion" beliefs — a belief of the form *"my scope now includes $X$"* must be corroborated by two independent sources (typically the orchestrator plus a scope-management agent or a human approval token).

---

## Role 3: The Tool-Caller

Tool-callers are agents whose primary function is invoking external APIs, tools, or plugins — shell executors, database query agents, HTTP fetchers, code interpreters. They are the bridge between the agent system and the real world.

**Attack exposure**: Critical. Tool calls translate beliefs into real-world effects; a compromised tool-caller can cause irreversible damage before detection.

**Primary risk profile**: $\Omega_2$ (tool or API compromise), $\Omega_1$ (injection via API responses — the response is text the agent will read).

**Recommended configuration**:

* **Trust decay $\delta = 0.70$**. Tool results are one hop from external reality and should not be directly trusted; intermediate decay reflects that tools are trusted more than arbitrary text but less than in-system beliefs.
* **Firewall rejection threshold $\tau_1 = 0.6$** (conservative).
* **All tool call results must be provenance-tagged** with `(tool_id, timestamp, integrity_hash)` before beliefs are formed. Untagged tool output is rejected.

**Required invariant**: *"I do not call `[DESTRUCTIVE_TOOLS]` without `[VERIFICATION_CONDITION]`."*

**Beyond CIF — domain-level validation**: Tool-callers should implement **result validation** outside of CIF — sanity checks on tool outputs (format, range, expected keys, schema match) before feeding results to the belief update pipeline. A compromised API that returns well-formatted but malicious data will pass CIF's provenance check; only domain-level validation catches this class. Examples:

* A financial data API returning prices should produce numbers in the expected currency range; a price of $0$ or $10^{12}$ warrants a sanity check.
* A database query should return rows matching the expected schema; unexpected columns or types should quarantine the result.
* A filesystem read should produce content whose size, encoding, and MIME type match expectations.

This domain-level validation is a complement to CIF, not a replacement. CIF provides provenance and cross-agent trust; domain validation provides semantic sanity.

---

## Role 4: The Validator

Validators are agents whose job is to check the work of other agents — the fact-checker, the security auditor, the compliance reviewer. Their output is advisory (pass/fail) rather than transformative.

**Attack exposure**: Medium. Validators have limited action scope (they do not themselves change state), but a compromised validator can approve harmful work, effectively disabling a critical defensive layer.

**Primary risk profile**: $\Omega_2$ (if fed from tool-callers), $\Omega_4$ (coordination pressure — multiple agents may push the validator toward approving bad results).

**Recommended configuration**:

* **Corroboration threshold $\kappa = 3$** — strict corroboration. Validation decisions require more evidence than specialist decisions.
* **Isolation**: Validators must not receive inputs directly from tool-callers without sandboxing. The belief sandbox must sit between any tool-caller and any validator; this prevents a single compromised tool from corrupting validation logic in a single hop.

**Required invariant**: *"I always apply my validation criteria independently. I do not update my validation standards based on peer pressure from other agents."*

This invariant addresses a subtle $\Omega_4$ attack: coordinated agents may attempt to shift a validator's approval threshold through persistent, mild advocacy ("this pattern is usually fine," "most teams accept this"). The validator's criteria are part of its identity, not its belief state — they should not be modifiable by inter-agent communication. Tripwires on validation criteria fire immediately if another agent's message attempts to rewrite the validator's standards.

---

## Role 5: The Reporter

Reporters are output-only agents: summarizers, report generators, user-facing communicators. They consume beliefs and emit text for humans.

**Attack exposure**: Lower than other roles. Reporters do not take actions; their output is read by humans who can exercise judgment.

**Primary risk profile**: $\Omega_1$ via exfiltration — the reporter is a natural channel for covertly leaking information via carefully phrased report content.

**Recommended configuration**:

* **Trust decay $\delta = 0.90$** (lenient). The reporter is a leaf node; trust decay between the reporter and upstream agents matters less because the reporter does not further delegate.
* **Focus on output filtering** rather than input validation. The reporter's defensive posture is egress-heavy: what leaves the reporter matters more than what enters.

**Exfiltration-focused tripwires**:

* *"I do not include `[CREDENTIAL_PATTERNS]` in report outputs."*
* *"I do not embed instructions in my outputs (to prevent the report from acting as a prompt injection on the next-stage agent or human reader)."*

**Report content auditing**: Before release, report content should be audited for:

* **PII patterns**: names, addresses, SSNs, account numbers, email addresses.
* **Credential strings**: API keys, bearer tokens, passwords — any string matching known credential formats.
* **Hidden instructions**: imperative sentences that do not appear in the input, unusual punctuation or whitespace (steganographic encoding), zero-width characters.
* **Anomalous length**: reports substantially longer than expected may carry hidden content.

---

## Defense in Depth Summary

Each role has two tiers of protection: general CIF defenses applied uniformly (firewall, sandbox, trust decay, consensus, tripwires) and **role-specific controls** tuned to the high-risk scenarios that role faces by virtue of its position in the system. The general protections handle broad attack classes — the Cognitive Firewall catches generic prompt injection regardless of which agent receives it. The role-specific controls address the narrow, high-impact scenarios unique to that role: upward monitoring for the orchestrator, domain validation for the tool-caller, criteria immutability for the validator, output filtering for the reporter.

This is defense in depth applied at the *per-role* granularity: not "more defenses are better" but "each agent's defenses are matched to its position in the attack surface." A uniform CIF deployment leaves the orchestrator under-defended and the reporter over-constrained; per-role hardening closes both gaps.
