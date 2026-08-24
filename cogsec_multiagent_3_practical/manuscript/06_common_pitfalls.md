\newpage

# Common Pitfalls and What the Research Shows {#sec:pitfalls}

![Common pitfalls by severity across security/configuration/operational categories (e.g. implicit trust in outputs, missing input validation).](figures/pitfall_severity.png){#fig:pitfall-severity width=80%}

The CIF research identifies recurring failure modes in multiagent deployments. This section catalogs eight anti-patterns, each assessed through what Parts 1 and 2 add to the problem and its mitigation.

These pitfalls are ranked by severity. We prioritize critical and high-severity items as they represent verifiable vulnerabilities in the defense architecture.

---

## Pitfall 1: Implicit Trust (Critical)

**The pattern**: Treating all inter-agent communication as trusted by default.

**What the research shows**: Part 1's trust calculus exists specifically because implicit trust enables trust laundering attacks. Without explicit trust scores, a single compromised agent influences the entire system---adversarial content enters through a low-trust source and exits through a high-trust agent, with no mechanism to track or attenuate the trust transfer.

Part 2's simulation confirms that trust exploitation attacks achieve their highest success rates against architectures without trust decay. The $\delta^d$ mechanism isn't optional hardening---it's the structural foundation that prevents systemic compromise from local failures.

**Mitigation Strategies**:

1. Implement explicit trust scoring on every inter-agent channel
2. Require minimum trust thresholds for consequential actions
3. Apply delegation decay ($\delta < 1$) at every hop
4. Verify source identity on every inter-agent message

---

## Pitfall 2: Security as Afterthought (Critical)

**The pattern**: Adding cognitive security after the architecture is finalized.

**What the research shows**: Part 1's defense composition algebra demonstrates that security mechanisms compose best when designed together. Retrofitted defenses create integration gaps---bypass opportunities at the boundaries between the original architecture and the bolted-on security layer.

Part 2's architecture-specific results show that systems with natural security affordances (LangGraph's explicit state transitions, CrewAI's role boundaries) outperform systems where security must be externally imposed. Architecture is security posture.

**Mitigation Strategies**:

1. Define trust boundaries during architectural design, not deployment
2. Embed trust checks in delegation logic from the start
3. Build provenance tracking into belief management
4. Include cognitive security constraints in agent system prompts

---

## Pitfall 3: Uncalibrated Thresholds (High)

**The pattern**: Setting security thresholds without understanding the tradeoffs.

**What the research shows**: Part 2's parametric simulation reveals that detection rates are highly sensitive to threshold configuration. The same defense module can range from too-strict (high false positive rate, operational friction) to too-permissive (attacks succeed undetected) depending on threshold settings.

The risk-profile-based configuration in Section 5 provides calibrated starting points. But these are starting points---production thresholds should be tuned against representative attack samples from Part 2's corpus.

**Mitigation Strategies**:

1. Assess risk profile before configuring (Section 5)
2. Test thresholds against representative attack samples
3. Monitor false positive/negative rates in production
4. Adjust based on operational feedback

---

## Pitfall 4: Individual-Only Security (High)

**The pattern**: Focusing on single-agent security while ignoring multi-agent attack surfaces.

**What the research shows**: Part 1's entire contribution is premised on the observation that multiagent systems introduce qualitatively new attack surfaces. The adversary hierarchy ($\Omega_3$--$\Omega_5$) specifically targets coordination, consensus, and systemic properties that don't exist in single-agent systems.

Part 2's colony benchmark measures the collective attack surface once collective-level defenses are deployed: sybil infiltration, quorum manipulation, and belief cascade are each detected at 100\%, while emergent misalignment---distributed sub-threshold drift with no explicit adversary and no single-agent analogue---remains the hardest scenario at 74.3\% detection (\cref{sec:paper2-review}, Finding 6). Those are the numbers a system gets *because* it has collective-level defenses; individual-only security has no mechanism that observes coordination at all, so the $\Omega_3$--$\Omega_5$ surfaces go unwatched rather than merely under-detected.

**Mitigation Strategies**:

1. Implement Byzantine consensus for critical collective decisions
2. Require agent authentication before counting votes
3. Monitor for unusual coordination patterns (simultaneous votes, identical analyses)
4. Set quorum requirements assuming adversarial presence

---

## Pitfall 5: Static Tripwires (Medium)

**The pattern**: Deploying canary tripwires once without rotation.

**What the research shows**: Part 1 notes that tripwire effectiveness depends on unpredictability. If an adversary can identify and avoid canary beliefs, the detection mechanism fails silently---giving false confidence in detection coverage.

The analog in traditional security is static honeypots: effective initially but useless once adversaries learn to recognize them.

**Mitigation Strategies**:

1. Implement automated canary rotation on a defined schedule
2. Vary placement across agents and belief categories
3. Monitor canary check patterns, not just modifications
4. Include non-obvious canaries that don't follow predictable naming conventions

---

## Pitfall 6: Ignoring Progressive Drift (Medium)

**The pattern**: Only alerting on large, sudden belief changes.

**What the research shows**: Part 1's stealth-impact tradeoff theorem bounds *per-interaction* impact but explicitly acknowledges that progressive drift---sub-threshold changes accumulating over time---is the hardest attack pattern to detect. The theorem doesn't rule out slow drift; it rules out sudden, invisible, high-impact attacks.

Part 2's corpus has four categories --- prompt injection, trust exploitation, belief manipulation and coordination --- and none of them isolates multi-turn social engineering. The result that speaks to this gap is the colony benchmark's emergent-misalignment scenario, the weakest structured result at 74.3\% detection: no single agent's divergence spikes, so a per-agent KL threshold systematically misses the collective drift. Attacks spread across turns or across agents avoid the concentrated statistical signature that single-turn, single-agent attacks produce.

**Mitigation Strategies**:

1. Use sliding window drift detection (not just per-update thresholds)
2. Track *cumulative* drift, not just per-update delta
3. Periodic baseline comparison over extended time windows
4. Alert on *trends* as well as absolute magnitude

---

## Pitfall 7: Insufficient Logging (Medium)

**The pattern**: Retaining insufficient information for post-incident analysis.

**What the research shows**: Part 1's provenance tracking and belief state representation are designed to produce a complete audit trail. Without this trail, incident responders cannot reconstruct attack paths, identify injection points, or assess the full scope of belief corruption.

This is the cognitive security equivalent of running a production system without structured logging. When something goes wrong---and it will---the ability to investigate depends entirely on what was recorded.

**Mitigation Strategies**:

1. Log all belief updates with provenance tags (source, trust level, derivation chain)
2. Retain inter-agent message history
3. Take periodic cognitive state snapshots
4. Use structured logging formats that support causal analysis

---

## Pitfall 8: Single-Orchestrator Reliance (High)

**The pattern**: Relying entirely on one orchestrator's integrity without backup.

**What the research shows**: Part 1's $\Omega_5$ adversary class---systemic compromise---is defined precisely as orchestrator-level control. Section 4's Scenario 5 illustrates the consequences: the attacker controls the entity responsible for coordinating defense, rendering downstream defenses moot.

Part 2's hierarchical architecture results confirm the pattern: hierarchical systems show strong *average* detection because the orchestrator is a natural defense chokepoint, but they have the worst *catastrophic* failure mode because that same chokepoint is a single point of failure.

**Mitigation Strategies**:

1. Consider multi-orchestrator architectures for critical decisions
2. Monitor orchestrator behavior with the same rigor applied to worker agents
3. Workers should verify orchestrator identity on critical commands
4. Implement orchestrator-specific tripwires with rotation

---

## Summary Checklist

| Pitfall | Assessment | Status |
| :--- | :--- | :--- |
| Implicit trust | Trust scoring implemented? | $\square$ |
| Security afterthought | Security in initial architecture? | $\square$ |
| Uncalibrated thresholds | Thresholds tested against attacks? | $\square$ |
| Individual-only security | Byzantine consensus deployed? | $\square$ |
| Static tripwires | Canary rotation scheduled? | $\square$ |
| Ignoring drift | Progressive drift monitoring? | $\square$ |
| Insufficient logging | Full belief history retained? | $\square$ |
| Single orchestrator | Orchestrator monitored? | $\square$ |

Address unchecked items before production deployment.
