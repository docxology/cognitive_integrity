\newpage

# Supplement S11: Adversarial Training Theory {#sec:adversarial-training-theory}

This supplement defines a hypothetical adversarial-training (AT) game for the
protocol described in §\ref{sec:adversarial-training} and separates that model
from what the implementation and artifacts establish. It does not claim a
measured Nash equilibrium, a convergence guarantee, or an information-geometric
convergence proof.

> **Cross-paper reading guide.**
> • **Formal foundations** for the adversary taxonomy appear in Part 1
>   \cite{friedman2026cogsec1} §3.2 (adversary capability levels) and §4.3
>   (stealth–impact bounds).
> • **Operational implications** for practitioners are in the merged Part 3+4
>   \cite{friedman2026cogsec3} §4.2 (red-team integration) and §5.3 (iterative hardening).
>
> **Reproducibility.** Diagnostic helpers live in `src/redteam/convergence.py`,
> and `scripts/run_adversarial_training.py` runs the parametric model or its
> explicitly selected real-firewall mode. These are numerical diagnostics, not
> verification of equilibrium existence or convergence theorems.

## The Adversarial Training Game {#sec:at-game}

### Formal Setup

Let $\Theta$ denote the space of defense configurations (thresholds, weights, and
structural parameters of the CIF pipeline). Let $\mathcal{A}$ denote the space of
attack strategies (parameterized by the red-team generator).

**Definition S11.1 (AT Game).** The adversarial training game is the two-player
zero-sum game $G = (\Theta, \mathcal{A}, \mathrm{DR})$ where:
- The defender's strategy is $\theta \in \Theta$, chosen to maximize $\mathrm{DR}(\theta, a)$.
- The adversary's strategy is $a \in \mathcal{A}$, chosen to minimize $\mathrm{DR}(\theta, a)$.
- The payoff is the detection rate $\mathrm{DR}(\theta, a) \in [0, 1]$.

The Nash equilibrium $(\theta^*, a^*) \in \Theta \times \mathcal{A}$ satisfies:
$$\mathrm{DR}(\theta^*, a) \geq \mathrm{DR}(\theta^*, a^*) \geq \mathrm{DR}(\theta, a^*)$$
\label{eq:nash-equilibrium-condition}
for all $\theta \in \Theta, a \in \mathcal{A}$.

### Connection to Minimax Theorem

When both $\Theta$ and $\mathcal{A}$ are convex compact sets and $\mathrm{DR}$ is
concave-convex (concave in $\theta$, convex in $a$), the minimax theorem
\cite{von1928theorie} guarantees existence of a Nash equilibrium satisfying:
$$\max_{\theta} \min_a \mathrm{DR}(\theta, a) = \min_a \max_\theta \mathrm{DR}(\theta, a)$$
\label{eq:minimax-theorem-at}
The shipped parameter sets include thresholds and structural choices, and the
code does not establish compact convex strategy spaces or concave-convexity of
$\mathrm{DR}$. Consequently this minimax statement is a conditional property of
the hypothetical game, not a theorem about the shipped AT runs.

## Convergence Diagnostics, Not Guarantees {#sec:at-convergence-theory}

Lipschitz continuity alone does not make a gradient-ascent step a contraction,
and the implementation does not establish the strong monotonicity, smoothness,
or equilibrium-uniqueness assumptions from which a convergence-rate theorem
could follow. Accordingly, no AT convergence-rate theorem is asserted here.

`ATConfig.learning_rate` controls threshold updates, but in the default `model`
mode the round detection rates come from `ROUND_GAP_ATTRIBUTION` through
`_simulate_hardened_dr`; they are not measurements of the updated thresholds'
effect on a detector. Neither that mode nor the geometric helper identifies a
Nash equilibrium or a Lipschitz constant for the detection-rate surface.

Each `ATRoundResult.delta_dr` is **cumulative**: hardened detection rate minus
the common baseline. A geometric-increment diagnostic must first convert the
sequence $d_1,\ldots,d_K$ to per-round increments
$g_1=d_1$ and $g_k=d_k-d_{k-1}$ for $k>1$. Feeding $(d_k)$ itself to a geometric
series sums cumulative values and is invalid. In particular, a ratio above one
for cumulative gains is not evidence of divergence, and clamping a ratio or the
resulting detection rate to one is not evidence of convergence or of a 100%
Nash-equilibrium detection rate. This supplement therefore reports no infinite,
divergent, or saturated numerical equilibrium projection.

When positive per-round increments decay geometrically with ratio $0<r<1$, the
expression $g_1/(1-r)$ is only a fitted model extrapolation. Nonpositive or
nonconvergent increments must be reported as nonconvergence rather than mapped
to a negative round, an arbitrary default ratio, or a finite equilibrium claim.

## Information-Geometric View of Adversarial Training {#sec:at-infogeo}

A future probabilistic AT model could use information geometry (extending
§\ref{sec:information-geometry}). If that model supplies a normalized likelihood
$p_\theta(y\mid x)$, its Fisher information metric is \cite{amari2000methods}:
$$G_F(\theta)_{ij} = \mathbb{E}_{(x,y) \sim \mathcal{D}} \left[
  \frac{\partial \log p_\theta(y\mid x)}{\partial \theta_i}
  \frac{\partial \log p_\theta(y\mid x)}{\partial \theta_j}
\right]$$ {#eq:fisher-info-at}
where $\mathcal{D}$ is the modelled data distribution. A scalar detection-rate
surface is not itself such a likelihood, and the shipped AT experiments do not
estimate $p_\theta$ or $G_F$.

Under a positive-definite Fisher metric, a natural-gradient ascent step has the
form
$$\theta^{(k+1)} = \theta^{(k)} + \alpha G_F(\theta^{(k)})^{-1} \nabla_\theta \mathrm{DR}.$$
\label{eq:natural-gradient-ascent}
`src/redteam/convergence.py::natural_gradient_at_step()` implements this linear
algebra operation and falls back to the Euclidean gradient when the supplied
matrix is singular. The function does not estimate a Fisher matrix from AT data,
select a step size with a convergence guarantee, or establish second-order
convergence. No acceleration theorem is claimed for the shipped AT protocol.

## Adversarial Robustness Limitations {#sec:at-robustness-bound}

Without a convergence theorem and a measured sensitivity bound, no general
lower bound on post-training detection rate follows for an arbitrary attack or
$\Omega$ level. The code does not estimate level-specific sensitivity
coefficients. In particular, it does not establish that coordinated attacks
receive the largest equilibrium benefit or that any level converges to a given
detection rate.

## Adversarial Training and the Stealth–Impact Bound {#sec:at-stealth-bound}

Part 1's stealth-impact product is an open formalization, not a theorem \cite{friedman2026cogsec1}. No universal radius expansion follows from adversarial training: a refinement that changes thresholds can decrease coverage for some attacks while increasing it for others. A monotone radius claim requires an attack distribution and a refinement policy that are not supplied here. The independent geometric step-budget helper in §\ref{sec:s10-curvature-constraint} is not evidence for such a guarantee.
