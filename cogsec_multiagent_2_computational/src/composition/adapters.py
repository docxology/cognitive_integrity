"""Adapter classes wrapping core defense modules as DefenseModule subclasses.

Each adapter bridges a core cognitive-security module (firewall, tripwire,
trust, consensus, provenance, sandbox, invariants) into the unified
:class:`DefenseModule` interface so they can be composed in series,
parallel, or hybrid pipelines.

An additional text-feature detection adapter (``DetectionAdapter``) provides
lightweight statistical analysis without wrapping an external class.
"""

from __future__ import annotations

import math
import re
import time
from collections import Counter
from typing import Any, Dict, List, Optional

from composition.pipeline import DefenseModule
from utils.types import DefenseResult

__all__ = [
    "FirewallAdapter",
    "DetectionAdapter",
    "TripwireAdapter",
    "TrustAdapter",
    "ConsensusAdapter",
    "ProvenanceAdapter",
    "SandboxAdapter",
    "InvariantsAdapter",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp *x* into the closed interval [lo, hi]."""
    return max(lo, min(hi, x))


# ---------------------------------------------------------------------------
# 1. FirewallAdapter
# ---------------------------------------------------------------------------

class FirewallAdapter(DefenseModule):
    """Wraps :class:`EnhancedCognitiveFirewall` as a pipeline module.

    Uses the multi-stage classifier (structural + pattern + semantic)
    to score incoming messages and flag those whose aggregate score
    exceeds *threshold*.
    """

    @property
    def name(self) -> str:
        return "CognitiveFirewall"

    def __init__(self, *, threshold: float = 0.5) -> None:
        from core.firewall import EnhancedCognitiveFirewall

        self._threshold = threshold
        self._firewall = EnhancedCognitiveFirewall(use_semantic=True)

    def evaluate(
        self, message: str, context: Optional[Dict[str, Any]] = None
    ) -> DefenseResult:
        t0 = time.perf_counter()

        result = self._firewall.classify_detailed(message)
        aggregate_score: float = result.get("aggregate_score", 0.0)
        detected = aggregate_score > self._threshold

        latency_ms = (time.perf_counter() - t0) * 1000.0

        return DefenseResult(
            detected=detected,
            score=aggregate_score,
            module_name=self.name,
            details={
                "classification": str(result.get("classification", "")),
                "scores": result.get("scores", {}),
                "aggregate_score": aggregate_score,
                "threshold": self._threshold,
            },
            latency_ms=latency_ms,
        )


# ---------------------------------------------------------------------------
# 2. DetectionAdapter
# ---------------------------------------------------------------------------

class DetectionAdapter(DefenseModule):
    """Text-feature extraction module (standalone, no wrapped class).

    Computes four statistical features from the raw message text and
    derives a weighted suspicion score:

    - ``length_zscore`` -- z-score relative to *baseline_mean* / *baseline_std*.
    - ``entropy`` -- Shannon entropy of character distribution.
    - ``special_char_ratio`` -- fraction of non-alphanumeric, non-space chars.
    - ``lexical_diversity`` -- unique-words / total-words ratio.
    """

    @property
    def name(self) -> str:
        return "TextFeatureDetection"

    def __init__(
        self,
        *,
        threshold: float = 0.5,
        baseline_mean: float = 200,
        baseline_std: float = 150,
        feature_weights: Optional[Dict[str, float]] = None,
    ) -> None:
        self._threshold = threshold
        self._baseline_mean = baseline_mean
        self._baseline_std = baseline_std
        # Default equal-weight across the four features.
        self._feature_weights: Dict[str, float] = feature_weights or {
            "length_zscore": 0.25,
            "entropy": 0.25,
            "special_char": 0.25,
            "lexical_diversity": 0.25,
        }

    def evaluate(
        self, message: str, context: Optional[Dict[str, Any]] = None
    ) -> DefenseResult:
        t0 = time.perf_counter()

        msg_len = len(message)

        # --- Feature 1: length z-score ---
        length_zscore = (msg_len - self._baseline_mean) / self._baseline_std

        # --- Feature 2: Shannon entropy ---
        entropy = 0.0
        if msg_len > 0:
            counts = Counter(message)
            for count in counts.values():
                p = count / msg_len
                if p > 0:
                    entropy -= p * math.log2(p)

        # --- Feature 3: special character ratio ---
        if msg_len > 0:
            special_count = sum(
                1 for ch in message if not ch.isalnum() and ch != " "
            )
            special_char_ratio = special_count / msg_len
        else:
            special_char_ratio = 0.0

        # --- Feature 4: lexical diversity ---
        words = message.split()
        total_words = len(words)
        if total_words > 0:
            lexical_diversity = len(set(w.lower() for w in words)) / total_words
        else:
            lexical_diversity = 1.0

        w = self._feature_weights
        # --- Composite score ---
        score = (
            w.get("length_zscore", 0.25) * _clamp(abs(length_zscore) / 3.0)
            + w.get("entropy", 0.25) * _clamp(entropy / 5.0)
            + w.get("special_char", 0.25) * _clamp(special_char_ratio * 5.0)
            + w.get("lexical_diversity", 0.25) * _clamp(1.0 - lexical_diversity)
        )

        detected = score > self._threshold
        latency_ms = (time.perf_counter() - t0) * 1000.0

        return DefenseResult(
            detected=detected,
            score=score,
            module_name=self.name,
            details={
                "length_zscore": length_zscore,
                "entropy": entropy,
                "special_char_ratio": special_char_ratio,
                "lexical_diversity": lexical_diversity,
                "threshold": self._threshold,
            },
            latency_ms=latency_ms,
        )


# ---------------------------------------------------------------------------
# 3. TripwireAdapter
# ---------------------------------------------------------------------------

class TripwireAdapter(DefenseModule):
    """Wraps :class:`CognitiveTripwire` with default canary beliefs.

    Scans the message for belief-shift indicators and simulates a
    shifted belief state to see whether any canaries trip.
    """

    # Default phrases that suggest an attempt to shift the agent's identity/beliefs.
    # Expanded from 4 to 20+ entries to cover broader injection corpus patterns.
    _DEFAULT_SHIFT_INDICATORS: List[str] = [
        # Identity/role override patterns
        "you are now",
        "forget who",
        "your new purpose",
        "ignore your identity",
        "pretend you are",
        "act as if",
        "roleplay as",
        "your real purpose",
        # Instruction override patterns
        "disregard previous instructions",
        "ignore all prior",
        "ignore your previous",
        "disregard your previous",
        "override previous instructions",
        "forget previous instructions",
        # System/mode override patterns
        "system override",
        "new instructions:",
        "updated directive",
        "administrator mode",
        "developer mode",
        # Constraint bypass patterns
        "ignore your constraints",
        "bypass your filters",
        "ignore your training",
        # Hidden instruction patterns
        "hidden instructions",
        "confidential instructions",
        "secret mode",
    ]

    @property
    def name(self) -> str:
        return "CognitiveTripwire"

    def __init__(
        self,
        *,
        threshold: float = 0.5,
        shift_indicators: Optional[List[str]] = None,
    ) -> None:
        from core.tripwire import CognitiveTripwire

        self._threshold = threshold
        # Use caller-supplied list or fall back to the class default.
        self._SHIFT_INDICATORS: List[str] = (
            shift_indicators if shift_indicators is not None
            else list(self._DEFAULT_SHIFT_INDICATORS)
        )

        self._tripwire = CognitiveTripwire()
        self._tripwire.add_identity_canary("i_am_ai", expected_belief=1.0)
        self._tripwire.add_boundary_canary("follow_rules", expected_belief=1.0)
        self._tripwire.add_principal_canary("serve_user", expected_belief=1.0)

    def evaluate(
        self, message: str, context: Optional[Dict[str, Any]] = None
    ) -> DefenseResult:
        t0 = time.perf_counter()

        msg_lower = message.lower()

        # Build a belief state based on detected shift indicators.
        beliefs: Dict[str, float] = {}
        indicators_found: List[str] = []

        for indicator in self._SHIFT_INDICATORS:
            if indicator in msg_lower:
                indicators_found.append(indicator)

        if indicators_found:
            # Simulate shifted beliefs -- each canary gets a drifted value.
            beliefs["I am agent i_am_ai"] = 0.2
            beliefs["I can follow_rules"] = 0.8
            beliefs["My principal is serve_user"] = 0.3
        else:
            # Normal operation -- beliefs match expectations.
            beliefs["I am agent i_am_ai"] = 1.0
            beliefs["I can follow_rules"] = 1.0
            beliefs["My principal is serve_user"] = 1.0

        alerts = self._tripwire.check(beliefs)
        score = min(1.0, len(alerts) * 0.35)
        detected = len(alerts) > 0

        latency_ms = (time.perf_counter() - t0) * 1000.0

        return DefenseResult(
            detected=detected,
            score=score,
            module_name=self.name,
            details={
                "indicators_found": indicators_found,
                "alert_count": len(alerts),
                "alerts": [
                    {
                        "proposition": a.canary.proposition,
                        "drift": a.drift,
                        "severity": a.severity,
                    }
                    for a in alerts
                ],
                "threshold": self._threshold,
            },
            latency_ms=latency_ms,
        )


# ---------------------------------------------------------------------------
# 4. TrustAdapter
# ---------------------------------------------------------------------------

class TrustAdapter(DefenseModule):
    """Wraps :class:`TrustCalculus` for trust-exploitation detection.

    Scans the message for authority claims, urgency indicators, and
    delegation claims. When the claim pressure exceeds the baseline
    trust for an unknown source, the input is flagged.
    """

    _DEFAULT_AUTHORITY_PATTERN = (
        r"I am the admin|authorized by|I have permission|official request"
    )
    _DEFAULT_URGENCY_PATTERN = (
        r"immediately|urgent|right now|emergency|critical"
    )
    _DEFAULT_DELEGATION_PATTERN = (
        r"on behalf of|delegated to me|transferred authority"
    )

    @property
    def name(self) -> str:
        return "TrustExploitationDetector"

    def __init__(
        self,
        *,
        threshold: float = 0.5,
        authority_pattern: Optional[str] = None,
        urgency_pattern: Optional[str] = None,
        delegation_pattern: Optional[str] = None,
        match_weight: float = 0.2,
    ) -> None:
        from core.trust import TrustCalculus

        self._threshold = threshold
        self._match_weight = match_weight
        self._AUTHORITY_RE = re.compile(
            authority_pattern or self._DEFAULT_AUTHORITY_PATTERN, re.IGNORECASE
        )
        self._URGENCY_RE = re.compile(
            urgency_pattern or self._DEFAULT_URGENCY_PATTERN, re.IGNORECASE
        )
        self._DELEGATION_RE = re.compile(
            delegation_pattern or self._DEFAULT_DELEGATION_PATTERN, re.IGNORECASE
        )
        self._trust = TrustCalculus()

    def evaluate(
        self, message: str, context: Optional[Dict[str, Any]] = None
    ) -> DefenseResult:
        t0 = time.perf_counter()

        authority_matches = len(self._AUTHORITY_RE.findall(message))
        urgency_matches = len(self._URGENCY_RE.findall(message))
        delegation_matches = len(self._DELEGATION_RE.findall(message))
        total_matches = authority_matches + urgency_matches + delegation_matches

        claim_score = min(1.0, total_matches * self._match_weight)

        # Baseline trust for an unknown source (low across all three axes).
        trust_score = self._trust.compute_trust(0.3, 0.3, 0.3)

        detected = claim_score > trust_score
        score = claim_score

        latency_ms = (time.perf_counter() - t0) * 1000.0

        return DefenseResult(
            detected=detected,
            score=score,
            module_name=self.name,
            details={
                "authority_claims": authority_matches,
                "urgency_indicators": urgency_matches,
                "delegation_claims": delegation_matches,
                "total_matches": total_matches,
                "claim_score": claim_score,
                "trust_score": trust_score,
                "threshold": self._threshold,
            },
            latency_ms=latency_ms,
        )


# ---------------------------------------------------------------------------
# 5. ConsensusAdapter
# ---------------------------------------------------------------------------

class ConsensusAdapter(DefenseModule):
    """Wraps :class:`ByzantineConsensus` simulating an *n_agents*-agent panel.

    Each agent has a different sensitivity profile.  A simple
    heuristic derives a per-agent suspicion score from the message,
    and votes are submitted to the consensus mechanism.
    """

    _DEFAULT_SENSITIVITY_PROFILES: List[float] = [0.3, 0.4, 0.5, 0.5, 0.6, 0.7, 0.8]

    @property
    def name(self) -> str:
        return "ByzantineConsensusPanel"

    def __init__(
        self,
        *,
        threshold: float = 0.5,
        n_agents: int = 7,
        sensitivity_profiles: Optional[List[float]] = None,
    ) -> None:
        from core.consensus import ByzantineConsensus

        self._threshold = threshold
        self._SENSITIVITY_PROFILES: List[float] = (
            sensitivity_profiles if sensitivity_profiles is not None
            else list(self._DEFAULT_SENSITIVITY_PROFILES)
        )
        max_byzantine = max(1, n_agents // 3)
        self._consensus = ByzantineConsensus(
            n_agents=n_agents, max_byzantine=max_byzantine
        )

    def evaluate(
        self, message: str, context: Optional[Dict[str, Any]] = None
    ) -> DefenseResult:
        from core.consensus import Vote

        t0 = time.perf_counter()

        # Reset consensus state for a fresh evaluation.
        self._consensus.reset()

        msg_lower = message.lower()
        words = message.split()
        total_words = max(len(words), 1)
        upper_words = sum(1 for w in words if w.isupper() and len(w) > 3)

        agent_scores: List[float] = []

        for idx, sensitivity in enumerate(self._SENSITIVITY_PROFILES):
            base_suspicion = (upper_words / total_words) * 0.3
            if "ignore" in msg_lower or "override" in msg_lower:
                base_suspicion += 0.2
            if len(message) > 1000:
                base_suspicion += 0.1
            agent_score = _clamp(base_suspicion * (1.0 + sensitivity))
            agent_scores.append(agent_score)

            self._consensus.submit_vote(
                Vote(
                    agent_id=f"agent-{idx}",
                    proposition="message_suspicious",
                    belief=agent_score,
                )
            )

        # Compute average belief across votes.
        avg_belief = sum(agent_scores) / len(agent_scores)
        score = _clamp(avg_belief)
        detected = score > self._threshold

        latency_ms = (time.perf_counter() - t0) * 1000.0

        return DefenseResult(
            detected=detected,
            score=score,
            module_name=self.name,
            details={
                "agent_scores": agent_scores,
                "average_belief": avg_belief,
                "n_agents": len(self._SENSITIVITY_PROFILES),
                "threshold": self._threshold,
            },
            latency_ms=latency_ms,
        )


# ---------------------------------------------------------------------------
# 6. ProvenanceAdapter
# ---------------------------------------------------------------------------

class ProvenanceAdapter(DefenseModule):
    """Wraps :class:`ProvenanceChain` for provenance red-flag detection.

    Scans the message for indicators of untrusted sourcing and
    deliberate chain-of-custody obfuscation.
    """

    _UNTRUSTED_RE = re.compile(
        r"anonymous source|unverified|I heard that|someone told me|rumor",
        re.IGNORECASE,
    )
    _OBSCURING_RE = re.compile(
        r"don't ask where|trust me on this|no need to verify|just believe",
        re.IGNORECASE,
    )

    @property
    def name(self) -> str:
        return "ProvenanceAnalysis"

    def __init__(self, *, threshold: float = 0.5) -> None:
        from core.provenance import ProvenanceChain

        self._threshold = threshold
        self._provenance = ProvenanceChain()

    def evaluate(
        self, message: str, context: Optional[Dict[str, Any]] = None
    ) -> DefenseResult:
        t0 = time.perf_counter()

        untrusted_count = len(self._UNTRUSTED_RE.findall(message))
        obscuring_count = len(self._OBSCURING_RE.findall(message))

        score = min(1.0, untrusted_count * 0.25 + obscuring_count * 0.3)
        detected = score > self._threshold

        latency_ms = (time.perf_counter() - t0) * 1000.0

        return DefenseResult(
            detected=detected,
            score=score,
            module_name=self.name,
            details={
                "untrusted_indicators": untrusted_count,
                "chain_obscuring_indicators": obscuring_count,
                "threshold": self._threshold,
            },
            latency_ms=latency_ms,
        )


# ---------------------------------------------------------------------------
# 7. SandboxAdapter
# ---------------------------------------------------------------------------

class SandboxAdapter(DefenseModule):
    """Wraps :class:`SandboxManager` for sandbox-bypass detection.

    Looks for patterns indicating an attempt to skip sandboxing,
    inflate certainty, or apply time pressure.
    """

    _BYPASS_RE = re.compile(
        r"execute immediately|skip verification|no need to sandbox|bypass security",
        re.IGNORECASE,
    )
    _CERTAINTY_RE = re.compile(
        r"absolutely certain|100% guaranteed|undeniable fact|proven beyond doubt",
        re.IGNORECASE,
    )
    _URGENCY_RE = re.compile(
        r"act now|don't wait|time sensitive|window closing",
        re.IGNORECASE,
    )

    @property
    def name(self) -> str:
        return "SandboxBypassDetector"

    def __init__(self, *, threshold: float = 0.5) -> None:
        from core.sandbox import SandboxManager

        self._threshold = threshold
        self._sandbox = SandboxManager()

    def evaluate(
        self, message: str, context: Optional[Dict[str, Any]] = None
    ) -> DefenseResult:
        t0 = time.perf_counter()

        bypass_count = len(self._BYPASS_RE.findall(message))
        certainty_count = len(self._CERTAINTY_RE.findall(message))
        urgency_count = len(self._URGENCY_RE.findall(message))

        score = min(
            1.0,
            bypass_count * 0.35 + certainty_count * 0.2 + urgency_count * 0.15,
        )
        detected = score > self._threshold

        latency_ms = (time.perf_counter() - t0) * 1000.0

        return DefenseResult(
            detected=detected,
            score=score,
            module_name=self.name,
            details={
                "bypass_patterns": bypass_count,
                "certainty_inflation": certainty_count,
                "urgency_pressure": urgency_count,
                "threshold": self._threshold,
            },
            latency_ms=latency_ms,
        )


# ---------------------------------------------------------------------------
# 8. InvariantsAdapter
# ---------------------------------------------------------------------------

class InvariantsAdapter(DefenseModule):
    """Wraps :class:`InvariantChecker` for invariant-violation detection.

    Analyses the message for patterns associated with code execution,
    credential access, or system modification, and also passes a
    constructed context through the checker's built-in invariants.
    """

    _CODE_EXEC_RE = re.compile(
        r"run this code|execute command|eval\(|exec\(|os\.system",
        re.IGNORECASE,
    )
    _CREDENTIAL_RE = re.compile(
        r"password|api key|secret|token|credential",
        re.IGNORECASE,
    )
    _SYSTEM_WRITE_RE = re.compile(
        r"write to file|modify config|change settings|delete",
        re.IGNORECASE,
    )

    @property
    def name(self) -> str:
        return "InvariantViolationDetector"

    def __init__(self, *, threshold: float = 0.5) -> None:
        from core.invariants import InvariantChecker

        self._threshold = threshold
        self._checker = InvariantChecker()

    def evaluate(
        self, message: str, context: Optional[Dict[str, Any]] = None
    ) -> DefenseResult:
        t0 = time.perf_counter()

        code_count = len(self._CODE_EXEC_RE.findall(message))
        cred_count = len(self._CREDENTIAL_RE.findall(message))
        system_count = len(self._SYSTEM_WRITE_RE.findall(message))

        # Determine the primary action type detected.
        if code_count > 0:
            action_type = "execute_code"
        elif system_count > 0:
            action_type = "write_file"
        elif cred_count > 0:
            action_type = "send_message"
        else:
            action_type = "unknown"

        # Build a context dict for the built-in invariants.
        inv_context: Dict[str, Any] = {
            "action": action_type,
            "parameters": {"content": message},
        }
        if action_type == "execute_code":
            inv_context["code_trusted"] = False
        if action_type == "send_message" and cred_count > 0:
            inv_context["contains_secrets"] = True
        if action_type == "write_file":
            inv_context["is_system_path"] = True
            inv_context["has_permission"] = False

        violations = self._checker.check_all(inv_context)
        violation_score = min(1.0, len(violations) * 0.4) if violations else 0.0

        # Pattern-based score (independent of invariant checker).
        pattern_score = min(
            1.0,
            code_count * 0.3 + cred_count * 0.25 + system_count * 0.25,
        )

        score = max(pattern_score, violation_score)
        detected = score > self._threshold

        latency_ms = (time.perf_counter() - t0) * 1000.0

        return DefenseResult(
            detected=detected,
            score=score,
            module_name=self.name,
            details={
                "code_execution_patterns": code_count,
                "credential_access_patterns": cred_count,
                "system_write_patterns": system_count,
                "pattern_score": pattern_score,
                "invariant_violations": len(violations),
                "violation_details": [
                    {
                        "invariant_id": v.invariant_id,
                        "description": v.description,
                        "severity": v.severity.name,
                    }
                    for v in violations
                ],
                "violation_score": violation_score,
                "threshold": self._threshold,
            },
            latency_ms=latency_ms,
        )
