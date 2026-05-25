\newpage

# Operational Monitoring Guide {#sec:monitoring-guide}

Cognitive Integrity Framework (CIF) defenses are active, not passive. Effective deployment requires ongoing monitoring to detect degraded performance, emerging attack patterns, and configuration drift. This guide specifies the metrics, thresholds, and dashboard design for operational CIF monitoring.

Monitoring plays two roles. First, it provides **real-time visibility** into the defensive posture — are attacks being detected? Are rejection rates climbing? Second, it provides **calibration feedback** — is the false positive rate acceptable? Are thresholds still appropriate for current traffic? Without both, CIF drifts silently from its target operating point.

> **Domain-calibrated thresholds.** The thresholds presented below reflect baseline settings suitable for common deployments. Part 4 (*Applications of the Cognitive Integrity Framework*) shows how these thresholds must shift across operational sectors — from millisecond OODA cycles in drone swarms (\S{3.04}) to year-scale diplomatic agents (\S{3.02}) — and introduces three domain-specific monitoring extensions (verification channel separation, active perturbation probing, physics-informed invariants) in \S{3.06}, \S{3.08}, and \S{3.09} respectively. Consult Part 4 before finalizing thresholds for a specific sector.

## Core Metrics

The following six metrics constitute the minimum viable monitoring set. Operators with richer telemetry infrastructure should add metrics; operators with less should not remove any of these.

\begin{table}[htbp]
\centering
\caption{Core CIF monitoring metrics with warning and critical thresholds.}
\label{tab:core-metrics}
\begin{tabular}{@{}p{2.5cm}p{2.8cm}lllp{2cm}p{1.6cm}@{}}
\toprule
Metric & Description & Warning & Critical & Collection Method & Frequency \\
\midrule
Firewall rejection rate & \% of inputs with score $> \tau_1$ & $>5\%$ & $>20\%$ & Count(rejected)/Count(total) per window & Per minute \\
Trust matrix mean & Average pairwise trust & $<0.4$ & $<0.25$ & $\mathrm{mean}(T)$ & Per batch \\
Belief drift score & Per-agent $D_{\mathrm{KL}}$ from baseline & $>0.15$ & $>0.30$ & DriftDetector output & Per round \\
Colony entropy & Diversity of agent interaction patterns & $<2.0$ bits & $<1.0$ bits & $H$(interaction frequency) & Hourly \\
False positive rate & \% of reviewed alerts confirmed clean & $>10\%$ & $>20\%$ & Manual review queue & Daily \\
Consensus latency (p95) & 95th pct consensus decision time & $>2.0$s & $>4.2$s & Timing log & Per round \\
\bottomrule
\end{tabular}
\end{table}

Each metric targets a specific failure mode: rejection rate catches attack waves, trust mean catches silent degradation, drift score catches per-agent compromise, colony entropy catches coordination attacks, FPR catches calibration drift, and consensus latency catches scaling issues.

## Alert Escalation

Metrics become actionable through escalation rules. The escalation ladder below maps metric states to response tiers, with both automated and human response expectations at each tier.

\begin{table}[htbp]
\centering
\caption{Alert severity levels and escalation paths.}
\label{tab:alert-escalation-ops}
\begin{tabular}{@{}lp{3.2cm}p{3.5cm}p{4.5cm}@{}}
\toprule
Severity & Trigger & Automated Response & Human Response \\
\midrule
Warning & Any single metric in warning range & Log \& notify monitoring channel & Review during next business hours \\
Alert & Two+ metrics in warning OR one in critical & Agent quarantine + PagerDuty notification & On-call investigation within 1 hour \\
Critical & Confirmed attack detected & Playbook execution starts & Immediate response per relevant playbook \\
Incident & $\Omega_3$ or $\Omega_5$ class detected & System pause + forensic capture & Full incident response team activated \\
\bottomrule
\end{tabular}
\end{table}

## Dashboard Design

A well-designed dashboard surfaces the six core metrics plus supporting context in a single view. The recommended layout is a **six-panel grid**, top three panels for real-time state and bottom three for trend analysis.

**Panel 1 — Real-Time Rejection Rate** (top-left): Time series, 24-hour window, 1-minute granularity. Show rolling average and peak. Draw warning/critical threshold lines.

**Panel 2 — Trust Matrix Heatmap** (top-center): $n \times n$ heatmap of pairwise trust scores. Color scale: green (>0.7) → yellow (0.4–0.7) → red (<0.4). Updated per interaction batch. Clusters of mutually-high trust are visible as bright blocks off the diagonal — this is the Sybil-coalition fingerprint.

**Panel 3 — Per-Agent Drift Scores** (top-right): Bar chart showing current $D_{\mathrm{KL}}$ for each agent. Warning/critical threshold horizontal lines. Sort by highest drift first for fast triage.

**Panel 4 — Attack Type Distribution** (middle-left): Pie or donut chart of detected attack types over rolling 7-day window. Helps identify if the attacker is shifting strategy (e.g., falling $\Omega_1$ share with rising $\Omega_4$ share signals a campaign pivoting to coordination attacks).

**Panel 5 — Detection/FP Rates Over Time** (middle-center): Dual-line chart: daily detection rate (blue) vs. false positive rate (orange). Shows whether calibration is drifting. A rising FP rate at stable detection is the classic signal for threshold recalibration.

**Panel 6 — Agent Interaction Graph** (middle-right): Network graph of agent communication topology. Color nodes by trust score; highlight anomalous edge patterns. Updated hourly. Unexpected edges (an agent communicating with another it should not be speaking to) surface coordination attacks before trust-matrix analysis catches them.

## Monthly Health Check

Beyond real-time monitoring, monthly health checks catch slow degradation that metrics-in-isolation miss. The recommended checklist:

1. **Behavioral fingerprint comparison**: compare current output distributions to deployment baseline. Statistically significant drift at the agent-population level indicates slow-motion $\Omega_5$ attacks that CIF's real-time detectors miss.
2. **Attack corpus update**: review any new detected attacks, classify, add to training corpus. New attack variants observed in the wild should be added to regression testing.
3. **Threshold calibration review**: are warning/critical thresholds still appropriate given current traffic? A deployment whose traffic has scaled $10\times$ may have warning thresholds that are now too noisy or too quiet.
4. **Parametric re-simulation**: re-run parametric evaluation with any updated defense module configurations. This catches regression in the parametric performance ceiling before it manifests as empirical detection loss.
5. **Trust decay audit**: verify that aged trust scores are decaying as expected; no agents should maintain unusually high trust without recent positive interactions. Persistent high-trust agents without fresh trust-building interactions indicate either stale data or undetected reputation farming.

These checks run monthly, take approximately half a day of analyst time, and provide the calibration loop that real-time monitoring alone cannot. An unmonitored CIF deployment is a stale CIF deployment — the defenses are running, but the operator has no insight into whether they are still working.
