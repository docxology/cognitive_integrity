\newpage

# Supplement S11: Adversarial Training Theory {#sec:adversarial-training-theory}

This supplement provides the theoretical foundations for the adversarial training
(AT) protocol described in §\ref{sec:adversarial-training}. We formalize the AT
game, derive convergence guarantees, and prove the connection to the information-
geometric framework of §\ref{sec:information-geometry}.

> **Cross-paper reading guide.**
> • **Formal foundations** for the adversary taxonomy appear in Part 1
>   \cite{friedman2026cogsec1} §3.2 (adversary capability levels) and §4.3
>   (stealth–impact bounds).
> • **Operational implications** for practitioners are in the merged Part 3+4
>   \cite{friedman2026cogsec3} §4.2 (red-team integration) and §5.3 (iterative hardening).
>
> **Reproducibility.** The AT convergence analysis is implemented in
> `src/redteam/convergence.py`; theoretical bounds can be verified against
> empirical AT results via `scripts/verify_at_convergence.py`.

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
In practice, $\Theta$ is a bounded hypercube (all thresholds in $[0,1]$) and
$\mathrm{DR}$ is approximately concave-convex near the operational point, making the
minimax theorem approximately applicable.

## Convergence Guarantees {#sec:at-convergence-theory}

### Theorem S11.1 (AT Convergence Rate)

\begin{theorem}[Adversarial Training Convergence]
Under the following conditions:
\begin{enumerate}
  \item The AT game $G$ has a unique Nash equilibrium $(\theta^*, a^*)$.
  \item The detection rate $\mathrm{DR}(\theta, a)$ is $L$-Lipschitz in $\theta$ for
        fixed $a$.
  \item The threshold refinement step is $\theta^{(k)} = \theta^{(k-1)} +
        \alpha \nabla_\theta \hat{\mathrm{DR}}^{(k)}$ with step size $\alpha \leq 1/(2L)$.
\end{enumerate}
The AT sequence $\{\theta^{(k)}\}$ satisfies:
$$\|\theta^{(k)} - \theta^*\|_2 \leq (1 - \alpha L)^k \|\theta^{(0)} - \theta^*\|_2$$
\label{eq:at-convergence-rate}
\end{theorem}
\label{thm:at-convergence}

\begin{proof}
By $L$-Lipschitz continuity, the gradient step is a contraction with constant
$(1 - \alpha L)$ when $\alpha \leq 1/L$. The contraction mapping theorem then
gives the stated geometric convergence rate.
\end{proof}

**No Lipschitz constant is recoverable from the AT results.** The contraction
bound above invites reading an observed geometric decay ratio as $1 - \alpha L$
and solving for $L$ given the step size. Neither input supports it. The step
size is real: `ATConfig.learning_rate`
is $0.05$ and `AdversarialTrainer.run_round` applies `learning_rate * gradient`
to every threshold. But in the default `model` measurement mode --- the mode that
produced the AT results of §\ref{sec:at-convergence} --- the reported round
detection rates come from the `ROUND_GAP_ATTRIBUTION` constants via
`_simulate_hardened_dr` and never read the updated thresholds: re-running the
five rounds at $\alpha = 0$, $0.5$ and $5.0$ reproduces the identical gain
sequence $(7.27, 5.60, 5.04, 2.91, 2.41)$ pp. Nor is $0.65$ an observation; it is
the constant `geometric_convergence_projection` returns when the gain list is
empty or its first entry is non-positive. On the measured per-round increments
the median ratio is $0.80$, and on the cumulative gain series it is $1.28$ ---
divergent, with an infinite projection --- which is why
§\ref{sec:at-convergence} describes the sequence as approximately linear rather
than geometrically decaying. No Lipschitz constant for the detection-rate
surface is recoverable from these runs.

## Information-Geometric View of Adversarial Training {#sec:at-infogeo}

The AT game has a natural information-geometric interpretation (extending
§\ref{sec:information-geometry}). The defender's threshold space $\Theta$ can be
equipped with a Fisher information metric \cite{amari2000methods}:
$$G_F(\theta)_{ij} = \mathbb{E}_{(x,y) \sim \mathcal{D}} \left[
  \frac{\partial \log \mathrm{DR}(\theta, x)}{\partial \theta_i}
  \frac{\partial \log \mathrm{DR}(\theta, x)}{\partial \theta_j}
\right]$$ {#eq:fisher-info-at}
where $\mathcal{D}$ is the attack distribution.

Under this metric, the natural gradient ascent for the defender:
$$\theta^{(k+1)} = \theta^{(k)} + \alpha G_F(\theta^{(k)})^{-1} \nabla_\theta \mathrm{DR}$$
\label{eq:natural-gradient-ascent}
follows the steepest ascent direction in the Riemannian sense, converging faster
than Euclidean gradient ascent near the Nash equilibrium.

**Theorem S11.2 (Natural Gradient AT Acceleration).** The natural gradient AT
update achieves second-order convergence near $\theta^*$:
$$\|\theta^{(k+1)}_{\text{NG}} - \theta^*\|_G \leq C \|\theta^{(k)}_{\text{NG}} - \theta^*\|_G^2$$
\label{eq:natural-gradient-quadratic-convergence}
for some constant $C > 0$, while the Euclidean gradient update achieves only
first-order (geometric) convergence. The implementation is in
`src/redteam/convergence.py::natural_gradient_at_step()`.

## Adversarial Robustness Bound {#sec:at-robustness-bound}

### Theorem S11.3 (Defense Robustness Under Adversarial Training)

\begin{theorem}[AT Robustness]
Let $\theta^{(K)}$ be the defense configuration after $K$ rounds of adversarial
training with geometric convergence rate $(1 - \alpha L)$. For any attack
$a \in \mathcal{A}$ generated by an adversary with capability level $\Omega_j$:
$$\mathrm{DR}(\theta^{(K)}, a) \geq \mathrm{DR}(\theta^*, a) -
  \epsilon_j \cdot (1 - \alpha L)^K \|\theta^{(0)} - \theta^*\|_2$$
\label{eq:at-robustness-bound}
where $\epsilon_j > 0$ is the sensitivity coefficient for capability level $\Omega_j$.
\end{theorem}
\label{thm:at-robustness}

The theorem shows that after $K$ rounds, the hardened configuration provides
detection rates within $\epsilon_j \cdot (1 - \alpha L)^K$ of the Nash equilibrium
rate. For the $\Omega_5$ case (coordinated attacks), $\epsilon_5$ is highest because
coordinated attacks are most sensitive to configuration gaps, making convergence to
the Nash equilibrium most impactful for $\Omega_5$ defense.

## Adversarial Training and the Stealth–Impact Bound {#sec:at-stealth-bound}

The stealth–impact bound from Part 1's Stealth-Impact Tradeoff theorem \cite{friedman2026cogsec1} (Information-Theoretic Detection Bounds) states that
for any attack in the Fisher-Rao ball of radius $r$ around the baseline,
the maximum impact is bounded by $I_{\max}(r)$. Adversarial training's effect on
this bound is:

**Proposition S11.1.** After $K$ rounds of AT, the effective detection radius
$r_{\text{eff}}^{(K)}$ of the hardened configuration satisfies:
$$r_{\text{eff}}^{(K)} \geq r_{\text{eff}}^{(0)} + \sum_{k=1}^K \Delta r^{(k)}$$
\label{eq:at-radius-monotone}
where $\Delta r^{(k)} > 0$ is the radius gain from round $k$'s threshold refinement.

This provides a monotone guarantee: adversarial training can only expand the
detection radius, never shrink it, as long as the refinement respects the
curvature constraint (Theorem CG.1 in §\ref{sec:s10-curvature-constraint}).
