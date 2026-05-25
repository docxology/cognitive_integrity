"""Bayesian detection rate estimation using the Beta-Binomial conjugate model.

The Beta distribution is the conjugate prior for the Binomial likelihood.
Given ``successes`` detections out of ``trials`` attempts and a
``Beta(alpha_prior, beta_prior)`` prior, the posterior is::

    Beta(alpha_prior + successes, beta_prior + trials - successes)

This module provides:

- :class:`BetaPosterior` -- posterior moments, credible intervals, HDI,
  and sampling.
- :func:`beta_binomial_posterior` -- construct posterior from data.
- :func:`bayes_factor_two_proportions` -- BF10 for two independent
  Beta-Binomial experiments.
- :func:`power_analysis_beta_binomial` -- smallest sample size such that
  the credible interval has the desired half-width.
- :func:`calibration_analysis` + :class:`CalibrationResult` -- expected
  calibration error (ECE) and Brier score for binary classifiers.

Numerical stability is handled via ``scipy.special.betaln`` /
``gammaln`` for log-space computations where needed.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats
from scipy.special import betaln, gammaln


# ---------------------------------------------------------------------------
# Beta posterior
# ---------------------------------------------------------------------------

@dataclass
class BetaPosterior:
    """Parameters of a posterior Beta distribution.

    The attribute ``beta_`` is named with a trailing underscore to
    avoid shadowing :mod:`scipy.stats.beta`.

    Attributes:
        alpha: First shape parameter of the Beta distribution.
        beta_: Second shape parameter of the Beta distribution.
    """

    alpha: float
    beta_: float

    def mean(self) -> float:
        """Posterior mean ``alpha / (alpha + beta)``."""
        return self.alpha / (self.alpha + self.beta_)

    def mode(self) -> float:
        """Posterior mode.

        - If both ``alpha > 1`` and ``beta_ > 1``: mode = (a-1)/(a+b-2).
        - Otherwise: 0.0 if ``alpha <= 1`` else 1.0 (boundary mode).
        """
        if self.alpha > 1 and self.beta_ > 1:
            return (self.alpha - 1.0) / (self.alpha + self.beta_ - 2.0)
        return 0.0 if self.alpha <= 1 else 1.0

    def credible_interval(self, width: float = 0.95) -> tuple[float, float]:
        """Equal-tailed credible interval of the given total probability mass.

        Args:
            width: Total probability mass of the interval (default 0.95).

        Returns:
            Tuple ``(lower, upper)`` with ``upper - lower`` credible mass.
        """
        lo_q = (1.0 - width) / 2.0
        hi_q = 1.0 - lo_q
        lo = float(stats.beta.ppf(lo_q, self.alpha, self.beta_))
        hi = float(stats.beta.ppf(hi_q, self.alpha, self.beta_))
        return lo, hi

    def hdi(self, width: float = 0.95) -> tuple[float, float]:
        """Highest density interval of the given probability mass.

        Computed by scanning 10 000 candidate left endpoints and picking
        the one whose right endpoint (placed so that ``width`` mass lies
        between them) is closest -- i.e. the shortest interval.

        Args:
            width: Probability mass contained in the interval.

        Returns:
            Tuple ``(lower, upper)`` giving the shortest such interval.
        """
        n_grid = 10_000
        # Candidate left-tail probabilities range from 0 up to 1 - width.
        lo_qs = np.linspace(0.0, 1.0 - width, n_grid)
        hi_qs = lo_qs + width
        lo_vals = stats.beta.ppf(lo_qs, self.alpha, self.beta_)
        hi_vals = stats.beta.ppf(hi_qs, self.alpha, self.beta_)
        widths = hi_vals - lo_vals
        idx = int(np.argmin(widths))
        return float(lo_vals[idx]), float(hi_vals[idx])

    def sample(self, n: int, seed: int = 42) -> np.ndarray:
        """Draw ``n`` samples from the posterior using a seeded RNG.

        Args:
            n: Number of samples.
            seed: Seed for :class:`numpy.random.default_rng`.

        Returns:
            1-D array of ``n`` samples in ``[0, 1]``.
        """
        rng = np.random.default_rng(seed)
        return rng.beta(self.alpha, self.beta_, size=n)


def beta_binomial_posterior(
    successes: int,
    trials: int,
    alpha_prior: float = 1.0,
    beta_prior: float = 1.0,
) -> BetaPosterior:
    """Construct the posterior for a Beta-Binomial model.

    Posterior = ``Beta(alpha_prior + successes, beta_prior + trials - successes)``.

    Args:
        successes: Number of successes (detections) observed.
        trials: Total number of trials.
        alpha_prior: Prior alpha (default 1.0 -- uniform).
        beta_prior: Prior beta (default 1.0 -- uniform).

    Returns:
        Posterior :class:`BetaPosterior`.
    """
    if trials < 0 or successes < 0 or successes > trials:
        raise ValueError(
            f"Invalid counts: successes={successes}, trials={trials}"
        )
    return BetaPosterior(
        alpha=alpha_prior + float(successes),
        beta_=beta_prior + float(trials - successes),
    )


# ---------------------------------------------------------------------------
# Bayes factor
# ---------------------------------------------------------------------------

def _log_binomial_coefficient(n: int, k: int) -> float:
    """``log C(n, k)`` via ``gammaln`` for numerical stability."""
    return gammaln(n + 1) - gammaln(k + 1) - gammaln(n - k + 1)


def _log_marginal(
    k: int,
    n: int,
    alpha_prior: float,
    beta_prior: float,
) -> float:
    """Log marginal likelihood for Beta-Binomial: ``log P(k | n, a, b)``.

    Uses the closed form ``log C(n,k) + betaln(k+a, n-k+b) - betaln(a, b)``.
    """
    return (
        _log_binomial_coefficient(n, k)
        + betaln(k + alpha_prior, n - k + beta_prior)
        - betaln(alpha_prior, beta_prior)
    )


def bayes_factor_two_proportions(
    n1: int,
    k1: int,
    n2: int,
    k2: int,
    alpha_prior: float = 1.0,
    beta_prior: float = 1.0,
) -> float:
    """Bayes factor BF10 comparing H1 (different rates) to H0 (same rate).

    Under H1 each experiment has its own rate drawn independently from
    ``Beta(alpha_prior, beta_prior)``; under H0 both share a single
    rate with the same prior.  The two joint log-marginals are::

        log P(k1, k2 | H1) = log_marginal(k1, n1, a, b)
                           + log_marginal(k2, n2, a, b)

        log P(k1, k2 | H0) = log C(n1, k1) + log C(n2, k2)
                           + betaln(k1+k2+a, n1+n2-k1-k2+b)
                           - betaln(a, b)

    Note that the joint H0 marginal is *not* ``log_marginal(k1+k2,
    n1+n2, a, b)``: the binomial coefficients stay separate because
    the observations are the pair ``(k1, k2)`` and the pooling only
    applies to the shared rate's posterior.

    Args:
        n1, k1: Trials and successes for experiment 1.
        n2, k2: Trials and successes for experiment 2.
        alpha_prior, beta_prior: Shared Beta prior hyperparameters.

    Returns:
        ``exp(log_BF)`` -- BF10 > 1 favours H1 (different rates),
        BF10 < 1 favours H0 (same rate).
    """
    if min(n1, n2, k1, k2) < 0 or k1 > n1 or k2 > n2:
        raise ValueError("Invalid counts for Bayes factor computation")

    # H1: independent rates -> product of two marginals.
    log_h1 = _log_marginal(k1, n1, alpha_prior, beta_prior) + _log_marginal(
        k2, n2, alpha_prior, beta_prior
    )
    # H0: shared rate -> joint marginal with separate binomial coefficients.
    log_h0 = (
        _log_binomial_coefficient(n1, k1)
        + _log_binomial_coefficient(n2, k2)
        + betaln(k1 + k2 + alpha_prior, n1 + n2 - k1 - k2 + beta_prior)
        - betaln(alpha_prior, beta_prior)
    )
    log_bf = log_h1 - log_h0
    return float(np.exp(log_bf))


# ---------------------------------------------------------------------------
# Power analysis
# ---------------------------------------------------------------------------

def power_analysis_beta_binomial(
    true_rate: float,
    desired_ci_half_width: float = 0.05,
    confidence: float = 0.95,
    alpha_prior: float = 1.0,
    beta_prior: float = 1.0,
) -> dict:
    """Smallest sample size yielding a credible interval with given half-width.

    Sweeps ``n`` over a geometric-ish progression (step 5 up to 5000)
    and returns the smallest ``n`` whose posterior credible interval
    centred on ``round(n * true_rate)`` has half-width at most
    ``desired_ci_half_width``.  If no ``n`` in range satisfies the
    criterion the largest candidate's diagnostics are returned with
    ``n_required = 5000``.

    Args:
        true_rate: Assumed true detection rate.
        desired_ci_half_width: Target half-width of the posterior CI.
        confidence: Credible-interval mass (default 0.95).
        alpha_prior, beta_prior: Beta prior hyperparameters.

    Returns:
        Dict with ``n_required`` (int), ``actual_half_width_at_n``
        (float), and ``posterior_mean_at_n`` (float).
    """
    if not 0.0 < true_rate < 1.0:
        raise ValueError("true_rate must lie strictly in (0, 1)")

    best_n: int = 5000
    best_half: float = float("inf")
    best_mean: float = 0.0

    for n in range(10, 5001, 5):
        k = int(round(n * true_rate))
        posterior = beta_binomial_posterior(
            successes=k,
            trials=n,
            alpha_prior=alpha_prior,
            beta_prior=beta_prior,
        )
        lo, hi = posterior.credible_interval(width=confidence)
        half = (hi - lo) / 2.0
        if half <= desired_ci_half_width:
            return {
                "n_required": int(n),
                "actual_half_width_at_n": float(half),
                "posterior_mean_at_n": float(posterior.mean()),
            }
        # Track best in case we exhaust the sweep.
        if half < best_half:
            best_half = half
            best_n = n
            best_mean = posterior.mean()

    return {
        "n_required": int(best_n),
        "actual_half_width_at_n": float(best_half),
        "posterior_mean_at_n": float(best_mean),
    }


# ---------------------------------------------------------------------------
# Calibration analysis
# ---------------------------------------------------------------------------

@dataclass
class CalibrationResult:
    """Diagnostics for probabilistic calibration.

    Attributes:
        bin_midpoints: Midpoint of each probability bin.
        empirical_frequencies: Observed positive frequency per bin.
        predicted_probabilities: Mean predicted probability per bin.
        ece: Expected calibration error (lower is better).
        brier_score: Mean squared error of predictions.
    """

    bin_midpoints: np.ndarray
    empirical_frequencies: np.ndarray
    predicted_probabilities: np.ndarray
    ece: float
    brier_score: float


def calibration_analysis(
    predicted_probs: np.ndarray,
    outcomes: np.ndarray,
    n_bins: int = 10,
) -> CalibrationResult:
    """Expected calibration error and Brier score.

    Uses equal-width bins in ``[0, 1]``.  ECE is the weighted absolute
    difference between mean predicted probability and empirical
    frequency within each non-empty bin::

        ECE = sum_b (|b| / n) * |mean_pred_b - mean_outcome_b|

    Args:
        predicted_probs: 1-D array of probabilities in ``[0, 1]``.
        outcomes: 1-D array of binary outcomes ``{0, 1}``.
        n_bins: Number of equal-width bins.

    Returns:
        :class:`CalibrationResult` with per-bin diagnostics.
    """
    predicted_probs = np.asarray(predicted_probs, dtype=float)
    outcomes = np.asarray(outcomes, dtype=float)
    if predicted_probs.shape != outcomes.shape:
        raise ValueError("predicted_probs and outcomes must match shape")

    n = len(predicted_probs)
    if n == 0:
        raise ValueError("Cannot compute calibration on empty arrays")

    edges = np.linspace(0.0, 1.0, n_bins + 1)
    midpoints = 0.5 * (edges[:-1] + edges[1:])

    pred_per_bin = np.zeros(n_bins)
    freq_per_bin = np.zeros(n_bins)
    ece = 0.0

    for b in range(n_bins):
        lo, hi = edges[b], edges[b + 1]
        # Include the right endpoint in the last bin.
        if b == n_bins - 1:
            mask = (predicted_probs >= lo) & (predicted_probs <= hi)
        else:
            mask = (predicted_probs >= lo) & (predicted_probs < hi)
        count = int(mask.sum())
        if count == 0:
            pred_per_bin[b] = midpoints[b]
            freq_per_bin[b] = 0.0
            continue
        mean_pred = float(predicted_probs[mask].mean())
        mean_out = float(outcomes[mask].mean())
        pred_per_bin[b] = mean_pred
        freq_per_bin[b] = mean_out
        ece += (count / n) * abs(mean_pred - mean_out)

    brier = float(np.mean((predicted_probs - outcomes) ** 2))

    return CalibrationResult(
        bin_midpoints=midpoints,
        empirical_frequencies=freq_per_bin,
        predicted_probabilities=pred_per_bin,
        ece=float(ece),
        brier_score=brier,
    )


__all__ = [
    "BetaPosterior",
    "beta_binomial_posterior",
    "bayes_factor_two_proportions",
    "power_analysis_beta_binomial",
    "CalibrationResult",
    "calibration_analysis",
]
