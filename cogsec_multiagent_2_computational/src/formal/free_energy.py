"""Variational Free Energy formulation of cognitive attacks.

Friston's Free Energy Principle (FEP) states that self-organising
agents minimise variational free energy ``F = D_KL[Q || P] -
E_Q[log P(o | s)]`` over their approximate posterior ``Q`` about
hidden states ``s``.  We cast CIF defenses in this language:

- An **attack** is any update that increases ``F`` beyond what the
  agent's prior and likelihood can justify -- concretely
  ``ΔF > κ_FEP`` for some threshold.
- **Trust** in a message channel is the *precision* weight that the
  agent places on evidence from that channel.  High trust = high
  precision.
- **Belief sandboxing** is a constrained-inference step that refuses
  any update whose ``ΔF`` exceeds ``κ_FEP * prior.precision``.

This module provides the core quantities needed to plug CIF
components into a minimal FEP agent: KL divergence, variational free
energy, precision-weighted belief fusion, epistemic and pragmatic
value, and the sandbox constraint.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

import numpy as np

KL_EPSILON = 1e-12
TOLERANCE_IDENTITY = 1e-10
ATTACK_THRESHOLD = 0.1
SANDBOX_UPDATE_SCALE = 0.1
SANDBOX_KAPPA_DEFAULT = 2.0

# ---------------------------------------------------------------------------
# Belief state
# ---------------------------------------------------------------------------

@dataclass
class BeliefState:
    """A categorical posterior over discrete hidden states.

    Attributes:
        probs: 1-D array of probabilities (not necessarily normalised).
        labels: Names of the hidden states (same length as ``probs``).
        precision: Scalar precision weight (inverse variance) of this
            belief state -- higher values mean the belief is held with
            more confidence.
    """

    probs: np.ndarray
    labels: List[str]
    precision: float = 1.0

    def __post_init__(self) -> None:
        self.probs = np.asarray(self.probs, dtype=float)
        if self.probs.ndim != 1:
            raise ValueError("BeliefState.probs must be 1-D")
        if len(self.probs) != len(self.labels):
            raise ValueError(
                f"Length mismatch: probs={len(self.probs)} "
                f"labels={len(self.labels)}"
            )
        if np.any(self.probs < 0.0):
            raise ValueError("BeliefState.probs must be non-negative")

    def normalize(self) -> "BeliefState":
        """Return a copy of this state with probabilities summing to 1.

        Raises:
            ValueError: If all probabilities are zero.
        """
        total = float(self.probs.sum())
        if total <= 0.0:
            raise ValueError("Cannot normalize an all-zero BeliefState")
        return BeliefState(
            probs=self.probs / total,
            labels=list(self.labels),
            precision=self.precision,
        )

    def entropy(self) -> float:
        """Shannon entropy ``-sum p log p`` (natural log).

        Zero probabilities contribute ``0 * log 0 = 0`` (handled
        gracefully via masking).
        """
        p = self.probs
        # Only sum over strictly positive entries to avoid log(0).
        mask = p > 0.0
        return float(-np.sum(p[mask] * np.log(p[mask])))


# ---------------------------------------------------------------------------
# Generative model
# ---------------------------------------------------------------------------

@dataclass
class GenerativeModel:
    """A minimal generative model ``P(s) P(o | s)``.

    Attributes:
        prior: Shape ``(n_states,)`` -- prior ``P(s)``.
        likelihood: Shape ``(n_obs, n_states)`` -- likelihood
            ``P(o | s)`` indexed as ``likelihood[o, s]``.
    """

    prior: np.ndarray
    likelihood: np.ndarray

    def __post_init__(self) -> None:
        self.prior = np.asarray(self.prior, dtype=float)
        self.likelihood = np.asarray(self.likelihood, dtype=float)
        if self.prior.ndim != 1:
            raise ValueError("prior must be 1-D")
        if self.likelihood.ndim != 2:
            raise ValueError("likelihood must be 2-D")
        n_states = self.prior.shape[0]
        if self.likelihood.shape[1] != n_states:
            raise ValueError(
                f"likelihood columns ({self.likelihood.shape[1]}) "
                f"must match prior length ({n_states})"
            )
        if np.any(self.prior < 0.0) or np.any(self.likelihood < 0.0):
            raise ValueError("prior and likelihood must be non-negative")


# ---------------------------------------------------------------------------
# KL divergence (stable)
# ---------------------------------------------------------------------------

def kl_divergence(
    p: np.ndarray,
    q: np.ndarray,
    epsilon: float = KL_EPSILON,
) -> float:
    """Kullback-Leibler divergence ``D_KL(P || Q)``.

    Numerically stable: contributions from zero entries of ``p`` are
    dropped (since ``0 log 0 = 0``) and ``q`` is floored at ``epsilon``
    to avoid ``log 0``.

    Args:
        p: Reference distribution (1-D).
        q: Comparison distribution (1-D, same shape as ``p``).
        epsilon: Floor added to ``q`` before taking logs (default: KL_EPSILON).

    Returns:
        ``sum_i p_i * log(p_i / (q_i + epsilon))``.
    """
    p = np.asarray(p, dtype=float)
    q = np.asarray(q, dtype=float)
    mask = p > 0.0
    return float(np.sum(p[mask] * np.log(p[mask] / (q[mask] + epsilon))))


# ---------------------------------------------------------------------------
# Variational free energy
# ---------------------------------------------------------------------------

def variational_free_energy(
    q: BeliefState,
    model: GenerativeModel,
    observation_idx: int,
) -> float:
    """Variational free energy ``F = D_KL[Q || P] - E_Q[log P(o | s)]``.

    Args:
        q: Current approximate posterior.
        model: Generative model providing prior and likelihood.
        observation_idx: Index into ``model.likelihood`` rows for the
            observed outcome.

    Returns:
        Scalar ``F`` in nats.
    """
    q_probs = q.probs
    if q_probs.shape != model.prior.shape:
        raise ValueError(
            f"q.probs shape {q_probs.shape} does not match "
            f"prior shape {model.prior.shape}"
        )
    if not 0 <= observation_idx < model.likelihood.shape[0]:
        raise ValueError(
            f"observation_idx {observation_idx} out of range "
            f"[0, {model.likelihood.shape[0]})"
        )

    # D_KL[Q || P(s)]
    d_kl = kl_divergence(q_probs, model.prior)

    # E_Q[log P(o | s)] with masking for zero q entries.
    likelihood_row = model.likelihood[observation_idx]
    mask = q_probs > 0.0
    log_like = np.log(likelihood_row[mask] + KL_EPSILON)
    expected_log_like = float(np.sum(q_probs[mask] * log_like))

    return float(d_kl - expected_log_like)


# ---------------------------------------------------------------------------
# Precision-weighted trust
# ---------------------------------------------------------------------------

def precision_weighted_trust(
    messages: List[BeliefState],
    precisions: List[float],
) -> BeliefState:
    """Fuse belief messages by precision weighting.

    Each message contributes ``precision_i * messages[i].probs`` to
    the unnormalised sum; the result is renormalised to a valid
    posterior.  The composite precision is the sum of the inputs --
    more trusted channels, combined, yield a sharper posterior.

    Args:
        messages: List of :class:`BeliefState` -- must share ``labels``.
        precisions: Non-negative scalar weight per message.

    Returns:
        Fused :class:`BeliefState` with ``precision = sum(precisions)``.
    """
    if not messages:
        raise ValueError("precision_weighted_trust requires >= 1 message")
    if len(messages) != len(precisions):
        raise ValueError("messages and precisions length mismatch")
    if any(pr < 0.0 for pr in precisions):
        raise ValueError("precisions must be non-negative")
    if sum(precisions) <= 0.0:
        raise ValueError("Sum of precisions must be positive")

    labels = messages[0].labels
    n = len(labels)
    acc = np.zeros(n, dtype=float)

    for m, pr in zip(messages, precisions):
        if len(m.probs) != n:
            raise ValueError("All messages must share dimension")
        acc = acc + pr * m.probs

    total = acc.sum()
    if total <= 0.0:
        raise ValueError("Accumulated mass is zero after weighting")
    normalised = acc / total
    return BeliefState(
        probs=normalised,
        labels=list(labels),
        precision=float(sum(precisions)),
    )


# ---------------------------------------------------------------------------
# Epistemic / pragmatic value
# ---------------------------------------------------------------------------

def epistemic_value(
    q_before: BeliefState,
    q_after: BeliefState,
) -> float:
    """Information gain: ``H(q_before) - H(q_after)``.

    Positive values indicate the posterior is sharper (more
    informative) after the update.
    """
    return float(q_before.entropy() - q_after.entropy())


def pragmatic_value(
    q: BeliefState,
    preferred_states: np.ndarray,
) -> float:
    """Pragmatic value: ``-D_KL(Q || P*)``.

    ``preferred_states`` encodes ``P*`` -- the agent's goal-distribution
    over states.  Higher (less negative) values mean current beliefs
    are more aligned with preferences.
    """
    preferred_states = np.asarray(preferred_states, dtype=float)
    if preferred_states.shape != q.probs.shape:
        raise ValueError("preferred_states shape mismatch")
    return float(-kl_divergence(q.probs, preferred_states))


# ---------------------------------------------------------------------------
# Attack detection via free-energy increase
# ---------------------------------------------------------------------------

def free_energy_of_attack(
    baseline_q: BeliefState,
    attacked_q: BeliefState,
    model: GenerativeModel,
    observation_idx: int,
) -> Dict[str, float]:
    """Compute diagnostic quantities for an attack candidate.

    Returns a dict with:

    - ``free_energy_baseline``:   ``F(q_baseline)``.
    - ``free_energy_attacked``:   ``F(q_attacked)``.
    - ``free_energy_increase``:   ``ΔF``.
    - ``kl_from_prior``:          ``D_KL(Q_attacked || P)``.
    - ``entropy_change``:         ``H(attacked) - H(baseline)``.
    - ``is_attack``:              ``bool(ΔF > 0.1)``.
    """
    f_base = variational_free_energy(baseline_q, model, observation_idx)
    f_att = variational_free_energy(attacked_q, model, observation_idx)
    delta_f = f_att - f_base
    kl_prior = kl_divergence(attacked_q.probs, model.prior)
    d_h = attacked_q.entropy() - baseline_q.entropy()
    return {
        "free_energy_baseline": float(f_base),
        "free_energy_attacked": float(f_att),
        "free_energy_increase": float(delta_f),
        "kl_from_prior": float(kl_prior),
        "entropy_change": float(d_h),
        "is_attack": bool(delta_f > ATTACK_THRESHOLD),
    }


# ---------------------------------------------------------------------------
# Belief sandbox as constrained inference
# ---------------------------------------------------------------------------

def belief_sandbox_as_constrained_inference(
    q_prior: BeliefState,
    suspicious_update: np.ndarray,
    model: GenerativeModel,
    observation_idx: int,
    kappa_threshold: float = SANDBOX_KAPPA_DEFAULT,
) -> Dict[str, Any]:
    """Sandbox: reject updates whose ``ΔF`` exceeds ``κ * prior.precision``.

    The candidate posterior is ``normalize(q_prior.probs + SANDBOX_UPDATE_SCALE *
    suspicious_update)``.  If ``ΔF > kappa_threshold * prior.precision``
    the candidate is refused and the prior is returned; otherwise the
    candidate is accepted.

    Args:
        q_prior: Prior belief state.
        suspicious_update: Additive update vector on the probability
            simplex (same shape as ``q_prior.probs``).
        model: Generative model.
        observation_idx: Index into ``model.likelihood`` rows.
        kappa_threshold: Sandbox strictness -- larger means more
            permissive (default: SANDBOX_KAPPA_DEFAULT).

    Returns:
        Dict with ``delta_F``, ``sandbox_blocks``, and ``q_accepted``.
    """
    suspicious_update = np.asarray(suspicious_update, dtype=float)
    if suspicious_update.shape != q_prior.probs.shape:
        raise ValueError("suspicious_update shape mismatch")

    candidate = q_prior.probs + SANDBOX_UPDATE_SCALE * suspicious_update
    # Clip to non-negative before normalising -- the sandbox is more
    # conservative than any particular rectification scheme.
    candidate = np.clip(candidate, 0.0, None)
    total = candidate.sum()
    if total <= 0.0:
        # Degenerate update: nothing survives rectification, block it.
        return {
            "delta_F": float("inf"),
            "sandbox_blocks": True,
            "q_accepted": q_prior,
        }
    candidate = candidate / total
    candidate_state = BeliefState(
        probs=candidate,
        labels=list(q_prior.labels),
        precision=q_prior.precision,
    )

    f_prior = variational_free_energy(q_prior, model, observation_idx)
    f_candidate = variational_free_energy(
        candidate_state, model, observation_idx
    )
    delta_f = f_candidate - f_prior

    blocks = bool(delta_f > kappa_threshold * q_prior.precision)
    return {
        "delta_F": float(delta_f),
        "sandbox_blocks": blocks,
        "q_accepted": q_prior if blocks else candidate_state,
    }


# ---------------------------------------------------------------------------
# Trust calculus <-> precision correspondence
# ---------------------------------------------------------------------------

def connect_to_trust_calculus(trust_config: Any) -> Dict[str, float]:
    """Map :class:`TrustConfig` weights to FEP precision values.

    The CIF trust calculus mixes three components with weights
    ``alpha, beta, gamma`` that sum to 1.  In the FEP interpretation
    each weight *is* a precision on its associated evidence channel,
    and the composite trust *is* the total precision.

    Args:
        trust_config: Any object with ``alpha``, ``beta``, ``gamma``
            attributes (e.g. :class:`TrustConfig`).

    Returns:
        Dict with ``alpha_precision``, ``beta_precision``,
        ``gamma_precision``, and ``composite_precision``.
    """
    alpha = float(trust_config.alpha)
    beta = float(trust_config.beta)
    gamma = float(trust_config.gamma)
    return {
        "alpha_precision": alpha,
        "beta_precision": beta,
        "gamma_precision": gamma,
        "composite_precision": alpha + beta + gamma,
    }


__all__ = [
    "BeliefState",
    "GenerativeModel",
    "kl_divergence",
    "variational_free_energy",
    "precision_weighted_trust",
    "epistemic_value",
    "pragmatic_value",
    "free_energy_of_attack",
    "belief_sandbox_as_constrained_inference",
    "connect_to_trust_calculus",
]
