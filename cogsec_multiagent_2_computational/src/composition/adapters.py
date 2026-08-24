"""Adapter classes wrapping core defense modules as DefenseModule subclasses.

Each adapter bridges a core cognitive-security module (firewall, tripwire,
trust, consensus, provenance, sandbox, invariants) into the unified
:class:`DefenseModule` interface so they can be composed in series,
parallel, or hybrid pipelines.

An additional text-feature detection adapter (``DetectionAdapter``) provides
lightweight statistical analysis without wrapping an external class.
"""

from __future__ import annotations

import base64
import math
import re
import time
from collections import Counter
from typing import Any, Dict, List, Optional

from composition.pipeline import DefenseModule
from utils.types import DefenseResult

from .calibration import DEFAULT_THRESHOLD

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

    def __init__(self, *, threshold: float | None = None) -> None:
        from core.firewall import EnhancedCognitiveFirewall

        self._threshold = DEFAULT_THRESHOLD if threshold is None else threshold
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
        threshold: float | None = None,
        baseline_mean: float = 200,
        baseline_std: float = 150,
        feature_weights: Optional[Dict[str, float]] = None,
    ) -> None:
        self._threshold = DEFAULT_THRESHOLD if threshold is None else threshold
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
        threshold: float | None = None,
        shift_indicators: Optional[List[str]] = None,
    ) -> None:
        from core.tripwire import CognitiveTripwire

        self._threshold = DEFAULT_THRESHOLD if threshold is None else threshold
        # Use caller-supplied list or fall back to the class default.
        self._SHIFT_INDICATORS: List[str] = (
            shift_indicators if shift_indicators is not None
            else list(self._DEFAULT_SHIFT_INDICATORS)
        )

        self._tripwire = CognitiveTripwire()
        self._tripwire.add_identity_canary("i_am_ai", expected_belief=1.0)
        self._tripwire.add_boundary_canary("follow_rules", expected_belief=1.0)
        self._tripwire.add_principal_canary("serve_user", expected_belief=1.0)

    #: How attack-specific each indicator is. A phrase that only ever appears
    #: in an attack earns full weight; one that shows up in ordinary technical
    #: English earns little. Before this existed every indicator was worth the
    #: same, so a bug report reading "Developer mode had been left on in the
    #: staging build" scored 1.000 -- maximal confidence, on a message whose
    #: subject was fixing the problem.
    _INDICATOR_WEIGHT: Dict[str, float] = {
        # Unambiguous: these are instructions to the model, not descriptions.
        "disregard previous instructions": 1.0,
        "ignore all prior": 1.0,
        "ignore your previous": 1.0,
        "disregard your previous": 1.0,
        "override previous instructions": 1.0,
        "forget previous instructions": 1.0,
        "ignore your constraints": 1.0,
        "ignore your training": 1.0,
        "bypass your filters": 1.0,
        "ignore your identity": 1.0,
        "forget who": 0.9,
        "your new purpose": 0.9,
        "your real purpose": 0.9,
        "system override": 0.9,
        "secret mode": 0.8,
        "hidden instructions": 0.8,
        "confidential instructions": 0.8,
        "you are now": 0.7,
        "pretend you are": 0.7,
        "roleplay as": 0.7,
        "updated directive": 0.6,
        "administrator mode": 0.5,
        # Weak: common in legitimate technical writing about these very topics.
        "new instructions:": 0.3,
        "developer mode": 0.2,
        "act as if": 0.2,
    }

    #: Constructions that mark the surrounding phrase as *mentioned* rather than
    #: *used*. Security documentation, incident reports and test fixtures all
    #: quote attack strings; treating a quotation as an attack makes the module
    #: fire hardest on the people writing the defenses.
    _MENTION_CONTEXT = re.compile(
        r"(?:\"|'|`|\bsends?\b|\bsent\b|\bcontains?\b|\bhad been\b|\bwas\b|"
        r"\bdocumentation\b|\bexample\b|\btest\b|\blogged\b|\breported\b)",
        re.IGNORECASE,
    )

    #: Weight multiplier applied to an indicator found in mention context.
    _MENTION_DISCOUNT: float = 0.25

    def _indicator_evidence(self, message: str) -> tuple[float, List[str]]:
        """Weighted evidence that this message tries to shift the agent's beliefs.

        Returns a saturating score in [0, 1] and the indicators behind it. The
        score is graded rather than binary: the previous version drifted all
        three canaries whenever any single indicator matched, so its score was
        always exactly 0.0 or 1.0 and no threshold could do anything with it.
        """
        lowered = message.lower()
        found: List[str] = []
        evidence = 0.0
        for indicator in self._SHIFT_INDICATORS:
            position = lowered.find(indicator)
            if position < 0:
                continue
            found.append(indicator)
            weight = self._INDICATOR_WEIGHT.get(indicator, 0.6)
            window = message[max(0, position - 40) : position + len(indicator) + 20]
            if self._MENTION_CONTEXT.search(window):
                weight *= self._MENTION_DISCOUNT
            # Independent-evidence combination: each indicator reduces the
            # remaining doubt rather than adding a flat increment, so three
            # weak hints never outrank one unambiguous instruction.
            evidence = 1.0 - (1.0 - evidence) * (1.0 - weight)
        return evidence, found

    def evaluate(
        self, message: str, context: Optional[Dict[str, Any]] = None
    ) -> DefenseResult:
        t0 = time.perf_counter()

        score, indicators_found = self._indicator_evidence(message)

        # The canary state is driven by the graded evidence rather than by a
        # bare "any indicator matched", so the simulated drift is proportional
        # to how much reason there is to think a shift was attempted.
        beliefs: Dict[str, float] = {
            "I am agent i_am_ai": 1.0 - 0.8 * score,
            "I can follow_rules": 1.0 - 0.2 * score,
            "My principal is serve_user": 1.0 - 0.7 * score,
        }
        alerts = self._tripwire.check(beliefs)

        # detected now respects the threshold. It used to be len(alerts) > 0,
        # which made the threshold decorative: the module could not be tuned,
        # and every caller that passed one was ignored.
        detected = score > self._threshold

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
        threshold: float | None = None,
        authority_pattern: Optional[str] = None,
        urgency_pattern: Optional[str] = None,
        delegation_pattern: Optional[str] = None,
        match_weight: float = 0.2,
    ) -> None:
        from core.trust import TrustCalculus

        self._threshold = DEFAULT_THRESHOLD if threshold is None else threshold
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
        threshold: float | None = None,
        n_agents: int = 7,
        sensitivity_profiles: Optional[List[float]] = None,
    ) -> None:
        from core.consensus import ByzantineConsensus

        self._threshold = DEFAULT_THRESHOLD if threshold is None else threshold
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

        n_agents = self._consensus.n_agents
        n_profiles = len(self._SENSITIVITY_PROFILES)
        agent_scores: List[float] = []

        # Submit exactly n_agents votes so the quorum (min_votes = ceil(n_agents
        # * quorum_fraction)) is computed against the same population that
        # votes.  Previously votes were derived from len(sensitivity_profiles)
        # (default 7), so a caller passing n_agents != 7 left the consensus
        # permanently UNDECIDED.  Sensitivity profiles are cycled when the
        # caller supplies a profile list shorter than n_agents (P2-7).
        profiles = [self._SENSITIVITY_PROFILES[i % n_profiles] for i in range(n_agents)]

        for idx, sensitivity in enumerate(profiles):
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
                "n_agents": self._consensus.n_agents,
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

    def __init__(self, *, threshold: float | None = None) -> None:
        from core.provenance import ProvenanceChain

        self._threshold = DEFAULT_THRESHOLD if threshold is None else threshold
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

    def __init__(self, *, threshold: float | None = None) -> None:
        from core.sandbox import SandboxManager

        self._threshold = DEFAULT_THRESHOLD if threshold is None else threshold
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

    What this module is for
    -----------------------
    The five built-in invariants say what an agent must never be talked into
    doing: run untrusted code (INV-1), emit a credential (INV-2), modify a
    system it has no permission over (INV-3), act on an unverified tool result
    (INV-4), or accept a delegated authority larger than the authority that was
    delegated (INV-5).  This adapter's job is to score a message by *which of
    those five demands it is making*.

    Why the previous version scored almost nothing
    ----------------------------------------------
    It matched three regexes, and two of them were topic words rather than
    demands.  ``password|api key|secret|token|credential`` fires on a
    rate-limiter document that says "a token bucket of 12 tokens" and on an
    incident report that says "an expired credential"; it does *not* fire on
    "reveal API keys", because that phrase contains none of those tokens as a
    standalone word -- it contains "api key", which it does match, but the
    match carried no more weight than the innocent one.  The consequence,
    measured on the 1475-item extended attack corpus and the 120-item hard
    benign corpus, was TPR 0.0034 at FPR 0.0000: every single one of the
    module's non-zero benign scores came from a bare noun, and 1345 of 1475
    attacks scored exactly zero, including all 200 direct injections, all 200
    indirect injections, all 100 nested injections, all 120 delegation-abuse
    and trust-inflation samples, and all 175 sandbox-escape samples.

    The signal those attacks *do* carry is the demand itself:
    ``reveal API keys``, ``grant root access``, ``no verification required``,
    ``Permission 'admin_write' propagates to me``.  That vocabulary is what the
    invariants are written about, and none of it appears in the hard benign
    stratum -- which is built from the *firewall's* and *tripwire's* keyword
    surface ("ignore previous instructions", "urgent", "developer mode"), not
    from this module's.

    Design constraint: the score is monotone in the text
    ---------------------------------------------------
    Every dimension is a positive phrase match.  There is no discount, no
    mention/use exemption, and no context in which a match stops counting.
    Adding characters to a message can only add matches, never remove one, so
    no prefix, suffix or wrapper can turn this detector off -- which is the
    failure mode a context discount in ``core.firewall`` had, where a
    31-character agent-chain prefix took red-team evasion from 0/59 to 59/59.
    The price of that guarantee is that a security document quoting an attack
    string scores like the attack; this module cannot tell use from mention and
    does not pretend to.  ``TripwireAdapter`` carries the use/mention
    discriminator for the phrases where it is affordable.

    Honest limits
    -------------
    The phrase inventory is organised by which invariant a phrase would
    violate, but it is still an inventory: it generalises across paraphrase
    only as far as its alternations reach, and an attacker who avoids naming
    the action ("do the needful with the thing we discussed") is not scored by
    it at all.  It is a lexical detector for a lexically-expressed demand, not
    a semantic one.
    """

    # -- legacy surface, retained for the reported detail keys ---------------
    # These are topic matches.  They no longer drive the score (a message that
    # merely uses the word "password" is not a credential leak) but the counts
    # remain in ``details`` because callers and tests read them.
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

    # -- scoring surface, grouped by the invariant each phrase would violate --
    #
    # Each entry is ``(pattern, weight)``.  A group contributes the *maximum*
    # weight among its matched patterns, never a sum over match counts, so a
    # payload cannot inflate its own score by repeating a phrase and a long
    # benign document cannot accumulate one by mentioning several in passing.

    #: INV-1 -- never execute untrusted code.
    _INV1_EXECUTION: List[tuple] = [
        (r"run (?:this|the following|arbitrary|untrusted|my) "
         r"(?:code|script|command|payload)", 0.80),
        # The qualifier and the object are not always adjacent -- "execute
        # arbitrary user commands" puts a noun between them -- so a bounded
        # word gap is allowed rather than requiring juxtaposition.
        (r"(?:execute|run)\s+(?:arbitrary|privileged|untrusted|unrestricted|"
         r"raw|system)\s+(?:\w+\s+){0,2}?(?:code|commands?|scripts?)", 0.85),
        (r"\bexec\(|\beval\(|os\.system|subprocess\.(?:run|Popen|call)|"
         r"__import__\(", 0.80),
        (r"run arbitrary code", 0.85),
        (r"execute immediately", 0.60),
        (r"run it directly", 0.60),
        (r"curl[^|\n]{0,80}\|\s*(?:ba)?sh", 0.90),
        (r"rm\s+-rf", 0.75),
        (r"execute command|run this code", 0.60),
        # An instruction to execute the *decoded* form of an opaque blob is a
        # request to run code the agent has not read.  It is the defining case
        # of INV-1 and the payload is unreadable by construction, so the
        # carrier instruction is the only thing there is to score.
        (r"decode (?:and|then) (?:execute|run)", 0.80),
        (r"execute the (?:above|following|decoded|encoded)", 0.75),
    ]

    #: INV-2 -- never leak credentials or secrets.  The verb must be an
    #: emission verb bound to a secret object; the bare noun is not evidence.
    _INV2_EXFILTRATION: List[tuple] = [
        (r"(?:reveal|dump|output|disclose|expose|exfiltrate|leak)\s+"
         r"(?:the\s+|my\s+|your\s+|all\s+|internal\s+){0,2}"
         r"(?:api[ _-]?keys?|credentials?|secrets?|passwords?|tokens?|"
         r"private keys?|configuration)", 0.85),
        (r"(?:send|show|give|paste|hand)\s+me\s+"
         r"(?:the\s+|your\s+|all\s+|current\s+){0,2}"
         r"(?:api[ _-]?keys?|credentials?|secrets?|passwords?|tokens?|"
         r"system prompt|configuration)", 0.80),
        (r"dump (?:the )?database(?: contents)?", 0.85),
        (r"share (?:confidential |all |the )?training data", 0.80),
        (r"credential[_ ]access|credential store", 0.70),
        (r"(?:show|reveal|print|display)\s+(?:me\s+)?"
         r"(?:the\s+|your\s+|current\s+){0,2}system prompt", 0.85),
        (r"reveal (?:your|the) instructions", 0.85),
        (r"print (?:the |your )?(?:secret|token|api key|password|credential)",
         0.80),
        # Paraphrases of the same demand: name the internal thing and ask for
        # it out.  "output all internal instructions", "expose internal API
        # endpoints", "share the credential store contents".
        (r"(?:output|share|expose|reveal|list|dump)\s+"
         r"(?:all\s+|the\s+|your\s+|any\s+){0,2}internal\s+"
         r"(?:instructions?|configuration|state|api|endpoints?|prompts?)",
         0.85),
        (r"(?:share|expose|leak)\s+(?:the\s+|all\s+){0,2}"
         r"credential store", 0.85),
        (r"data exfiltration", 0.85),
    ]

    #: INV-3 -- never modify a system, policy or permission without authority.
    _INV3_PRIVILEGE: List[tuple] = [
        # "grant"/"granted", with up to two intervening words, so that
        # "have been granted emergency elevated permissions" matches the same
        # rule as "grant me elevated access".
        (r"grante?d?\s+(?:\w+\s+){0,2}?"
         r"(?:root|admin|administrator|universal|unrestricted|elevated|full|"
         r"privileged)", 0.85),
        (r"grant self\b", 0.85),
        (r"elevate (?:my|the|his|her|their) "
         r"(?:permission|privilege|access|trust)", 0.85),
        (r"upgraded? to administrator", 0.80),
        (r"trusted[- ]agent status", 0.70),
        (r"add(?:ed)? my agent to the trusted (?:whitelist|allowlist)", 0.85),
        (r"whitelist all external", 0.80),
        (r"remove all (?:access control|rate limit|restriction)", 0.85),
        (r"remove rate limit(?:ing|s)?", 0.80),
        (r"remove all rate limits", 0.85),
        (r"disable (?:all |the |any ){0,2}(?:safety|audit|multi-?factor|"
         r"moderation|content filter|content moderation|security|sandbox)",
         0.85),
        (r"bypass (?:all |the |any ){0,2}(?:authentication|content filtering|"
         r"content safety|content moderation|security|sandbox|content policy|"
         r"safety|firewall|filters?)", 0.85),
        (r"override (?:the )?content policy", 0.85),
        (r"without any (?:content )?filters", 0.80),
        (r"safety rules then ignore", 0.75),
        (r"unrestricted (?:access|operations|ai|system access)", 0.70),
        (r"approve (?:all |my )?pending "
         r"(?:permission|data export|request)", 0.75),
        (r"\b(?:policy_bypass|admin_write|full_system_access|config_modify|"
         r"rate_limit_bypass|permission_level|security_override|"
         r"user_management|data_export)\b", 0.80),
        # Direct writes to the agent's own belief store: an unauthorised
        # modification of the state the other invariants are evaluated over.
        (r"belief[_ ]?(?:db|store)\b|BELIEF_INJECT|<belief-update|/beliefs/|"
         r"\"belief\"\s*:|set_belief\(|beliefs\[", 0.85),
        # A key/value assignment that switches a control off.
        (r"(?:safety|sandbox|moderation|audit|verification|credential|"
         r"rate_limit|permission|content_moderation|content filtering)"
         r"[^=:\n]{0,30}[=:]\s*['\"]?\s*"
         r"(?:false|disabled|off|skip|bypass|root|none|active)\b", 0.80),
        # Consensus-machinery edits: changing the rule rather than voting under
        # it is a policy modification, which is what INV-3 is about.
        (r"(?:override|overrule|suspend|lower|reduce|waive) (?:the )?"
         r"(?:standing policy|quorum|pending objection|consensus threshold|"
         r"threshold)", 0.70),
        (r"count the abstentions as approvals|"
         r"ignore the dissenting validators", 0.70),
        # Legacy phrases, kept at the weight their specificity earns.
        (r"write to file", 0.50),
        (r"modify config(?:uration)?", 0.55),
        (r"change settings", 0.50),
        (r"delete (?:all|every|the entire) ", 0.55),
    ]

    #: INV-4 -- always verify tool outputs before acting on them.
    _INV4_VERIFICATION: List[tuple] = [
        (r"no verification required", 0.85),
        (r"no need to (?:verify|sandbox|validate|check|review)", 0.80),
        (r"skip (?:verification|validation|the review|checks|review)", 0.85),
        (r"without (?:verification|validation|review)", 0.80),
        (r"checks? (?:add|adds) latency", 0.80),
        (r"treat (?:this|it|them) as verified", 0.85),
        (r"pre-?validated and (?:are|is) safe", 0.85),
        (r"checking them wastes cycles", 0.80),
        (r"(?:don'?t|do not) wait for the review", 0.75),
        (r"(?:has |have )?already been reviewed", 0.60),
        (r"verification (?:is|are) "
         r"(?:not required|unnecessary|optional)", 0.80),
        (r"bypass (?:the )?(?:review|verification|validation)", 0.85),
        # A control asserted to be unnecessary, deprecated or already off.
        # This is the belief-drift shape: nobody is told to disable anything,
        # the message simply asserts that the control was never worth running.
        (r"\b(?:safety mechanisms?|safety filters?|security checks?|"
         r"content moderation|content filtering|rate limiting|"
         r"credential (?:rotation|checks?)|audit logging|sandbox(?:ing)?|"
         r"verification|trust verification|input validation|"
         r"moderation rules?|access control|authentication|staging step|"
         r"logging user interactions)\b"
         r"[^.\n]{0,45}?\b(?:pointless|unnecessary|deprecated|disabled|"
         r"bypassed|outdated|waived|optional|not needed|no longer|suspended|"
         r"redundant|removed|too aggressive|adds? latency|harms|overhead)",
         0.70),
        (r"external (?:data sources?|inputs?)[^.\n]{0,40}"
         r"(?:trustworthy|pre-?validated|are safe)", 0.70),
        (r"reduced security", 0.70),
        (r"requirement was waived", 0.70),
        # Skipping a required step because its outcome is presumed.  Only the
        # forms that name the step being skipped are listed: bare "is
        # reasonable" / "close enough" would generalise to ordinary English
        # and buy recall at a cost this corpus is too small to show.
        (r"promoting it is a formality", 0.70),
        (r"would not change the outcome", 0.65),
        (r"treating silence as assent", 0.70),
        (r"(?:excluding|discarding|ignoring) the late votes|"
         r"late votes override", 0.70),
        (r"already validated upstream", 0.70),
    ]

    #: INV-5 -- delegated trust must not exceed direct trust.  Every phrase
    #: here is a message asserting its own authority rather than presenting it.
    _INV5_DELEGATION: List[tuple] = [
        (r"trust transitivity", 0.85),
        (r"delegation chain", 0.85),
        (r"delegation_verify", 0.85),
        (r"propagates to me", 0.85),
        (r"i inherit permission", 0.85),
        (r"trust escalation request", 0.85),
        (r"trust_update\s*:", 0.80),
        (r"my (?:cumulative )?trust (?:score|metric|record|has been)", 0.75),
        (r"trust has been grandfathered", 0.80),
        (r"qualifies me for unrestricted", 0.80),
        (r"(?:should be granted|i request) "
         r"(?:privileged access|trusted-agent status)", 0.80),
        (r"my access level should be upgraded", 0.85),
        (r"after \d+ positive interactions", 0.75),
        (r"trust escalation request \(interaction #\d+\)", 0.80),
        (r"validators confirm my trustworthiness", 0.80),
        (r"completed [\d,]+ successful interactions", 0.80),
        (r"perfect safety record", 0.75),
        (r"delegated to me|transferred authority", 0.70),
        (r"elevate my permissions", 0.85),
        (r"authorized per executive directive", 0.70),
        # Self-asserted delegation records: the message *is* the authorisation
        # it claims to be carrying, which is exactly the ordering INV-5 forbids.
        (r"delegation\s*:\s*from\s*=", 0.85),
        (r"\bto\s*=\s*self\b", 0.80),
        (r"received delegation from", 0.85),
        (r"authorized me with", 0.80),
        # Flattening the trust lattice: if every agent is equally trusted then
        # delegated trust can never exceed direct trust because there is no
        # ordering left to violate.  That is the premise INV-5 exists to deny.
        (r"(?:can be )?trusted equally", 0.70),
    ]

    #: ``{invariant id: (compiled patterns with weights, checker context)}``.
    #: The context half is what makes the wrapped :class:`InvariantChecker` do
    #: work: before this, the adapter could only ever construct
    #: ``execute_code`` / ``write_file`` / ``send_message`` contexts, so INV-4
    #: and INV-5 were unreachable no matter what the message said.
    _DIMENSIONS: Dict[str, Any] = {}

    @property
    def name(self) -> str:
        return "InvariantViolationDetector"

    def __init__(self, *, threshold: float | None = None) -> None:
        from core.invariants import InvariantChecker

        self._threshold = DEFAULT_THRESHOLD if threshold is None else threshold
        self._checker = InvariantChecker()

    @classmethod
    def _compiled(cls) -> Dict[str, List[tuple]]:
        """Compile (once) the phrase groups, keyed by invariant id."""
        if not cls._DIMENSIONS:
            cls._DIMENSIONS = {
                "INV-1": [
                    (re.compile(p, re.IGNORECASE), w)
                    for p, w in cls._INV1_EXECUTION
                ],
                "INV-2": [
                    (re.compile(p, re.IGNORECASE), w)
                    for p, w in cls._INV2_EXFILTRATION
                ],
                "INV-3": [
                    (re.compile(p, re.IGNORECASE), w)
                    for p, w in cls._INV3_PRIVILEGE
                ],
                "INV-4": [
                    (re.compile(p, re.IGNORECASE), w)
                    for p, w in cls._INV4_VERIFICATION
                ],
                "INV-5": [
                    (re.compile(p, re.IGNORECASE), w)
                    for p, w in cls._INV5_DELEGATION
                ],
            }
        return cls._DIMENSIONS

    # -- alternate readings --------------------------------------------------
    #
    # Two normalisations, both of which can only *add* matches, because the
    # dimension weight is a maximum over the plain message and every view.
    # That is what keeps them from becoming an off-switch: there is no reading
    # of a message under which a match stops counting.
    #
    # 1. Decoding.  A third of the indirect-injection corpus hands the agent
    #    its payload base64-, hex- or reversal-encoded under a label ("Data
    #    (base64):", "Note (reversed):").  Encoded, the demand carries no
    #    phrase to match.  The right response is not to invent a phrase for the
    #    *carrier* but to decode and let the ordinary dimensions judge the
    #    payload on its merits.
    #
    # 2. Rejoining.  ``AttackMutator``'s ``gradual_insertion`` operator splits
    #    a payload at its midpoint and inserts " ... ", which lands inside a
    #    word as often as between two ("Disabl ... e all safety mechanisms").
    #    That defeated 300 of 1229 detections, because every phrase here is
    #    multi-word.  Two readings are needed because the cut lands in two
    #    different places: deleting runs of two-or-more non-word characters
    #    repairs a cut *inside* a word ("Disabl ... e" -> "Disable"), and
    #    replacing the same runs with one space repairs a cut *between* two
    #    ("internal  ... instructions" -> "internal instructions").  Single
    #    spaces survive both, so ordinary text is barely altered.

    _B64_RE = re.compile(r"[A-Za-z0-9+/]{16,}={0,2}")
    _HEX_RE = re.compile(r"\b(?:[0-9a-fA-F]{2}){8,}\b")
    _SPLIT_RUN_RE = re.compile(r"[^\w]{2,}")

    #: Bounds on the normalisation work, so a pathological input cannot turn a
    #: linear scan into an expensive one.
    _MAX_DECODE_CANDIDATES = 8
    _MAX_MESSAGE_FOR_DECODE = 20_000

    @classmethod
    def _alternate_views(cls, message: str) -> List[str]:
        """Return alternate readings of *message*.

        Deterministic and side-effect free.  Undecodable candidates are
        skipped silently -- a run of hex-looking characters that is not text is
        simply not a view, and nothing downstream depends on the count.
        """
        if not message or len(message) > cls._MAX_MESSAGE_FOR_DECODE:
            return []
        rejoined = cls._SPLIT_RUN_RE.sub("", message)
        views: List[str] = [
            message[::-1],
            rejoined,
            cls._SPLIT_RUN_RE.sub(" ", message),
        ]
        # Encoded blobs are looked for in the rejoined reading as well as the
        # literal one: a payload split through the middle of its own base64
        # blob decodes only after the split is repaired.
        sources = [message, rejoined] if rejoined != message else [message]
        budget = cls._MAX_DECODE_CANDIDATES
        seen: set = set()
        for source in sources:
            for pattern, base in ((cls._B64_RE, 64), (cls._HEX_RE, 16)):
                for match in pattern.finditer(source):
                    if budget <= 0:
                        break
                    blob = match.group(0)
                    # Keyed on the alphabet as well as the text: a hex blob is
                    # also a valid base64 blob, so deduplicating on the string
                    # alone would let the base64 attempt consume it and the hex
                    # reading never happen.
                    if (blob, base) in seen:
                        continue
                    seen.add((blob, base))
                    text = cls._decode_blob(blob, base)
                    if text is None:
                        continue
                    budget -= 1
                    views.append(text)
        return views

    #: How many leading characters to drop while hunting for a decodable
    #: alignment.  Rejoining a split payload can glue a label onto the front of
    #: its own blob ("Data (base64): aWdu ... b3Jl" becomes
    #: "Database64aWdub3Jl"), which shifts the base64 frame; trying a bounded
    #: set of offsets recovers it.  Bounded so the work stays linear.
    _MAX_DECODE_OFFSET = 12

    @classmethod
    def _decode_blob(cls, blob: str, base: int) -> Optional[str]:
        """Decode *blob* to text, or return ``None`` if it is not text.

        Only a result that is overwhelmingly printable is accepted.  Without
        that test, arbitrary byte runs that happen to be valid UTF-8 would be
        admitted as views, which costs work and adds noise without ever
        carrying a phrase.
        """
        limit = 1 if base == 16 else min(cls._MAX_DECODE_OFFSET, len(blob))
        for offset in range(limit):
            candidate = blob[offset:]
            if len(candidate) < 8:
                break
            try:
                if base == 64:
                    padded = candidate + "=" * (-len(candidate) % 4)
                    raw = base64.b64decode(padded, validate=True)
                else:
                    raw = bytes.fromhex(candidate)
                text = raw.decode("utf-8")
            except (ValueError, UnicodeDecodeError):
                continue
            if text and sum(c.isprintable() for c in text) >= 0.9 * len(text):
                return text
        return None

    def _dimension_scores(self, message: str) -> Dict[str, float]:
        """Return ``{invariant id: weight}`` for every dimension that matched.

        A dimension's weight is the maximum over its matching patterns, and
        over the plain message and each alternate view.  Taking the maximum
        rather than a sum is deliberate: it makes the score insensitive to
        repetition, so neither an attacker padding a payload nor a long benign
        document can accumulate confidence out of many weak hits.
        """
        texts = [message] + self._alternate_views(message)
        found: Dict[str, float] = {}
        for invariant_id, patterns in self._compiled().items():
            best = 0.0
            for pattern, weight in patterns:
                if weight <= best:
                    continue
                if any(pattern.search(text) for text in texts):
                    best = weight
            if best > 0.0:
                found[invariant_id] = best
        return found

    #: Which checker context each invariant's evidence implies.  Every one of
    #: these sets the field the corresponding predicate fails closed on, so a
    #: matched dimension produces a real violation from the wrapped checker
    #: rather than a number this adapter made up.
    _CONTEXT_FOR: Dict[str, Dict[str, Any]] = {
        "INV-1": {"action": "execute_code", "code_trusted": False},
        "INV-3": {
            "action": "write_file",
            "is_system_path": True,
            "has_permission": False,
        },
        "INV-2": {"action": "send_message", "contains_secrets": True},
        "INV-4": {
            "action": "accept_tool_output",
            "tool_output_verified": False,
        },
        "INV-5": {
            "action": "trust_evaluation",
            "direct_trust": 0.3,
            "delegated_trust": 1.0,
        },
    }

    #: Order the contexts are checked in.  A checker context carries a single
    #: ``action``, so a message demanding three different violations needs
    #: three contexts; they are visited in this fixed order -- most
    #: irreversible first -- so the reported violation list is deterministic.
    _CONTEXT_PRECEDENCE = ("INV-1", "INV-3", "INV-2", "INV-4", "INV-5")

    def _violations(
        self, message: str, dimensions: Dict[str, float],
        caller_context: Optional[Dict[str, Any]],
    ) -> List[Any]:
        """Run the wrapped checker once per matched dimension.

        One pass per dimension rather than one pass overall: a message that
        asks for code execution *and* a credential dump violates two
        invariants, and reporting only the first would understate what the
        message is asking for.  Each pass keeps only the violation the pass was
        constructed to reach, so an unrelated fail-closed default in some other
        predicate cannot inflate the count.

        The caller's context is a *base* only.  Message-derived fields are
        written over it, so a host that supplies ``code_trusted=True`` cannot
        talk this module out of a violation it found in the text.
        """
        base: Dict[str, Any] = dict(caller_context) if caller_context else {}
        base["parameters"] = {"content": message}

        if not dimensions:
            base.setdefault("action", "unknown")
            return self._checker.check_all(base)

        found: List[Any] = []
        for invariant_id in self._CONTEXT_PRECEDENCE:
            if invariant_id not in dimensions:
                continue
            ctx = dict(base)
            ctx.update(self._CONTEXT_FOR[invariant_id])
            found.extend(
                v
                for v in self._checker.check_all(ctx)
                if v.invariant_id == invariant_id
            )
        return found

    def evaluate(
        self, message: str, context: Optional[Dict[str, Any]] = None
    ) -> DefenseResult:
        t0 = time.perf_counter()

        # Reported topic counts (not scored) -- see the class docstring.
        code_count = len(self._CODE_EXEC_RE.findall(message))
        cred_count = len(self._CREDENTIAL_RE.findall(message))
        system_count = len(self._SYSTEM_WRITE_RE.findall(message))

        dimensions = self._dimension_scores(message)
        violations = self._violations(message, dimensions, context)
        violation_score = min(1.0, len(violations) * 0.4) if violations else 0.0

        # Independent-evidence combination across dimensions: each invariant
        # the message asks to be broken reduces the remaining doubt, so five
        # weak demands never sit below one unambiguous one, and no dimension
        # can push the score back down.
        pattern_score = 0.0
        for weight in sorted(dimensions.values(), reverse=True):
            pattern_score = 1.0 - (1.0 - pattern_score) * (1.0 - weight)

        score = _clamp(max(pattern_score, violation_score))
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
                "dimensions": dict(sorted(dimensions.items())),
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
