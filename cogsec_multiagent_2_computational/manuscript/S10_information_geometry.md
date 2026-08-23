\newpage

# Supplement S10: Information Geometry of Belief Manipulation {#sec:information-geometry}

This supplement develops the information-geometric structure of the CIF belief state space and shows how this geometry illuminates three otherwise disconnected aspects of the framework: the drift-detection threshold $\theta_{\text{drift}} = 0.3$, the sandbox corroboration threshold $\kappa$, and the choice of canary-belief probability $\tau_{\text{canary}}$ for tripwires. Implementations of the constructions below are in [`src/analysis/information_geometry.py`](../src/analysis/information_geometry.py); the numerical checks on curvature and geodesic lengths are in \texttt{tests/test\_information\_geometry.py}.

> **Cross-paper reading guide.**
> • **Formal stealth–impact bound** (which the Fisher–Rao construction realizes) is stated and proved in Part 1 \cite{friedman2026cogsec1} §4.3.
> • **Operational implications** of the geodesic attack path for active-inference-based monitoring are discussed in Part 3 \cite{friedman2026cogsec3} §2 (theory review).
> • **Domain applications** — the geodesic framework applies to high-stakes sectors where adversarial inputs stay within a stealth budget; see unified Part 3+4 \cite{friedman2026cogsec3}, Section 9.12 (information ecosystems, fake-news detection) in particular, where the Fisher--Rao metric informs distribution-shift monitoring.

> **Reproducibility.** All geometric quantities (Fisher–Rao distances, geodesic paths, natural gradient directions) can be regenerated from [`src/analysis/information_geometry.py`](../src/analysis/information_geometry.py). Thin orchestrator: invoke via the publication suite (`uv run python scripts/run_publication_suite.py`) or directly via `StatisticalManifold` / `geodesic_attack_path`.

## Belief Space as Statistical Manifold {#sec:s10-manifold}

Each agent's belief state is a probability distribution over a finite belief vocabulary of size $n$: $p = (p_1, \ldots, p_n)$ with $p_i \geq 0$ and $\sum_i p_i = 1$. The set of such distributions is the probability simplex $\Delta^{n-1} \subset \mathbb{R}^n$, a smooth manifold of dimension $n - 1$.

The canonical Riemannian metric on $\Delta^{n-1}$ is the \emph{Fisher-Rao metric}, given in barycentric coordinates by
\begin{equation}
G_{ij}(p) = \frac{\delta_{ij}}{p_i}.
\end{equation}
\label{eq:fisher-rao-metric}
The Fisher-Rao metric is the unique metric (up to scaling) invariant under sufficient statistics \cite{cencov1982statistical,amari2000methods}; using any other metric would implicitly privilege some coordinate chart over the intrinsic probabilistic structure.

A useful change of coordinates is the \emph{Hellinger embedding} $p \mapsto (\sqrt{p_1}, \ldots, \sqrt{p_n})$, which maps $\Delta^{n-1}$ isometrically onto a hemisphere of the unit sphere $S^{n-1}$ in $\mathbb{R}^n$. Under this embedding, the Fisher-Rao geodesic distance between distributions $p, q$ is the \emph{Bhattacharyya angle}
\begin{equation}
d_{\mathrm{FR}}(p, q) = 2 \arccos\!\left(\sum_{i=1}^{n} \sqrt{p_i \, q_i}\right).
\end{equation}
\label{eq:bhattacharyya-angle}

The manifold has constant positive curvature $\kappa_{\mathrm{curv}} = n(n-1)/4$. The practical consequence is that small differences in KL divergence translate to even larger geometric separations: two distributions that differ by $\KL = 0.1$ correspond to a geodesic distance bounded above by $\sqrt{2 \cdot 0.1} \approx 0.45$ radians (by the Pinsker-type inequality connecting KL and Fisher-Rao distance), and the positive curvature \emph{amplifies} the geometric distinguishability of nearby distributions in a bounded way.

## Attacks as Geodesic Updates {#sec:s10-geodesic-attacks}

An adversary that seeks to drive agent $i$'s beliefs from a baseline $p^{(0)}$ to an attacker-preferred target $p^{(\text{target})}$ is, geometrically, traversing $\Delta^{n-1}$ along some path. The \emph{minimum-effort} path in the Fisher-Rao metric is the geodesic
\begin{equation}
\gamma_{\text{attack}}(t) = \mathrm{normalize}\!\left( \left( \sqrt{p^{(0)}} + t\,(\sqrt{p^{(\text{target})}} - \sqrt{p^{(0)}}) \right)^2 \right), \quad t \in [0, 1],
\end{equation}
\label{eq:geodesic-attack-path}
a great-circle arc on the Hellinger hemisphere. The helper \texttt{geodesic\_attack\_path()} in \texttt{src/analysis/information\_geometry.py} constructs $\gamma_{\text{attack}}$ and samples it at a configurable step count.

The connection to CIF's drift detector (Part 1's Drift Score definition) comes from the following standard fact: for small steps $\delta$ from a distribution $p$,
\begin{equation}
\KL[p \,\|\, p + \delta] = \frac{1}{2}\, \delta^{\top} G(p) \delta + O(\|\delta\|^3).
\end{equation}
\label{eq:kl-fisher-second-order}
That is, the KL divergence is (to second order) the squared Fisher-Rao distance. The drift-detector threshold $\theta_{\text{drift}} = 0.3$ therefore corresponds to a geodesic step whose length, in radians on the Hellinger hemisphere, is approximately $2 \arcsin(\sqrt{0.3}/2) \approx 0.28$ radians. The empirically-calibrated threshold thus admits a principled geometric interpretation: it is the arc length beyond which belief updates have crossed from ``ordinary learning'' into ``territory probably controlled by a single adversarial channel''. This is a more satisfying justification than ``tuned on the validation corpus'' and is robust to changes in the corpus that do not change the underlying geometry.

## Defense as Curvature Constraint {#sec:s10-curvature-constraint}

The sandbox's corroboration criterion (Part 1's Sandbox Promotion Soundness theorem) can be restated geometrically. A belief update is provisionally allowed inside the sandbox, but promotion to the verified partition requires corroboration count $\geq \kappa$; equivalently, it requires that the updated belief lie within a geodesic ball around a multiply-witnessed reference.

\begin{theorem}[Curvature Constraint Defense, CG.1]
The CIF belief sandbox with corroboration threshold $\kappa$ and per-step update precision $\epsilon_{\text{precision}}$ implements a geodesic ball constraint of radius
\begin{equation}
\rho = 2 \arccos\!\left( \sqrt{1 - \kappa \cdot \epsilon_{\text{precision}}} \right)
\end{equation}
\label{eq:sandbox-geodesic-radius}
around the baseline belief state $p^{(0)}$ in the Fisher-Rao metric: a provisional update $p^{(*)}$ is promoted if and only if $d_{\mathrm{FR}}(p^{(0)}, p^{(*)}) \leq \rho$.
\end{theorem}

\begin{proof}[Proof sketch]
The corroboration criterion requires that $\kappa$ independent corroborating observations have been seen, each of which reduces the posterior uncertainty by $\epsilon_{\text{precision}}$ under the FEP-equivalent formulation (\cref{thm:attack-fep}). The cumulative effect is a tightening of the posterior's Bhattacharyya coefficient with the reference distribution to at least $1 - \kappa \cdot \epsilon_{\text{precision}}$, which translates to the Fisher-Rao ball radius $\rho = 2\arccos(\sqrt{1 - \kappa \cdot \epsilon_{\text{precision}}})$. The helper \texttt{defense\_as\_curvature\_constraint()} evaluates this radius and accepts or rejects an update against it.
\end{proof}
\label{thm:curvature-constraint}

\cref{thm:curvature-constraint} provides a concrete practical implication. Operators who want to harden the sandbox against belief-manipulation attacks can either (a) increase $\kappa$, (b) raise the per-observation precision $\epsilon_{\text{precision}}$ by filtering low-precision channels, or (c) directly specify the geodesic radius $\rho$ and back-solve for $(\kappa, \epsilon_{\text{precision}})$. Option (c) is preferable when the security requirement is geometric (``no update moves beliefs by more than $x$ radians'') rather than statistical (``$\kappa$ corroborators required'').

## Natural Gradient Attacks and Sensitivity {#sec:s10-natural-gradient}

The natural gradient \cite{amari1998natural} is the gradient of a loss $L(p)$ expressed with respect to the Fisher-Rao metric rather than the Euclidean metric:
\begin{equation}
\widetilde{\nabla}_i L(p) = G^{-1}(p) \nabla L(p) = p_i \, \frac{\partial L}{\partial p_i}.
\end{equation}
\label{eq:natural-gradient-belief}
On the probability simplex, the natural gradient is the coordinate-wise product of the Euclidean gradient and the belief probabilities themselves.

An adversary performing gradient-based belief manipulation is, from a geometric standpoint, more efficient using the natural gradient than the Euclidean gradient because the natural gradient respects the manifold's curvature and moves along geodesics rather than across them. The helper \texttt{sensitivity\_via\_riemannian\_metric()} quantifies the resulting sensitivity by computing $\widetilde{\nabla} L$ at each belief and reporting the per-dimension magnitude.

The result is a non-obvious security insight: high-probability beliefs (large $p_i$) have proportionally larger natural-gradient magnitude and are therefore \emph{more} susceptible to gradient-based attacks than low-probability beliefs. This inverts the naive intuition that confident beliefs are hard to move. A belief at $p_i = 0.95$ has natural gradient magnitude nearly twenty times larger than a belief at $p_i = 0.05$, for the same Euclidean gradient.

CIF's tripwire monitoring of canary beliefs (\cref{alg:tripwire-impl}) at thresholds $\tau_{\text{canary}} > 0.9$ directly addresses this vulnerability: canary placements are concentrated at the beliefs that geometric analysis identifies as the most gradient-sensitive, precisely where an efficient adversary will focus their effort. The canary-threshold choice of $0.9$ is therefore not an arbitrary high-probability convention but a principled selection of the points of maximum geometric vulnerability on the simplex.

## Fisher Information Metric: Complete Derivations {#sec:s10-fim-derivations}

> **v1.0 addition.** This section provides complete derivations of the Fisher information matrix (FIM) for the CIF belief state parameterization, extending the survey in §\ref{sec:s10-manifold} with explicit computations for practical parameter choices used in the empirical evaluation.

### Parameterized Belief Family

Fix a finite vocabulary $\mathcal{V} = \{v_1, \ldots, v_n\}$ with $|\mathcal{V}| = n$. The CIF belief state is parameterized as a categorical distribution:
\begin{equation}
p(\theta) = \text{Categorical}(\theta_1, \ldots, \theta_{n-1}), \quad
\theta_i = p(v_i), \quad \theta_n = 1 - \sum_{i=1}^{n-1} \theta_i.
\end{equation}
\label{eq:categorical-parameterization}
This is an exponential family with natural parameters $\eta_i = \log(\theta_i / \theta_n)$ (log-ratios to the base category $v_n$).

### FIM in Natural Parameters

The Fisher information matrix in natural parameters $\eta \in \mathbb{R}^{n-1}$ is:
\begin{equation}
I(\eta)_{ij} = \mathbb{E}_{x \sim p(\eta)}\left[\frac{\partial \log p(x;\eta)}{\partial \eta_i} \frac{\partial \log p(x;\eta)}{\partial \eta_j}\right].
\end{equation}
\label{eq:fim-natural-params}
For the categorical family, the score function for observation $x = v_k$ is:
\begin{equation}
\frac{\partial \log p(x;\eta)}{\partial \eta_i} = \mathbb{1}[x = v_i] - p_i(\eta), \quad i = 1, \ldots, n-1.
\end{equation}
\label{eq:categorical-score-function}
Therefore:
\begin{equation}
I(\eta)_{ij} = \begin{cases}
  p_i(1 - p_i) & i = j \\
  -p_i p_j      & i \neq j
\end{cases}
\end{equation}
\label{eq:categorical-fim}
This is precisely the $(n-1) \times (n-1)$ covariance matrix of the indicator vector $(X_1, \ldots, X_{n-1})$ where $X_i = \mathbb{1}[x = v_i]$.

### FIM in Probability Parameters

In probability parameters $\theta \in \Delta^{n-1}$, the FIM is diagonal in the Hellinger embedding but has a specific structure in Cartesian coordinates:
\begin{equation}
G_{ij}(\theta) = \frac{\delta_{ij}}{\theta_i} + \frac{1}{\theta_n}, \quad
G^{-1}_{ij}(\theta) = \theta_i \delta_{ij} - \theta_i \theta_j.
\end{equation}
\label{eq:fim-probability-params}
The diagonal form $G_{ij}(\theta) = \delta_{ij}/\theta_i$ holds exactly when restricted to the $n-1$ free coordinates; the full $n \times n$ metric on $\mathbb{R}^n$ is singular (reflecting the constraint $\sum \theta_i = 1$).

**Numerical verification.** The implementation in `src/analysis/information_geometry.py::StatisticalManifold.fisher_information_matrix()` computes $G(\theta) = \text{diag}(1/\theta_i)$ and verifies positive semi-definiteness. The test `tests/test_property_based.py::TestInformationGeometryProperties::test_fisher_info_matrix_positive_definite` confirms PSD for all valid probability distributions generated by Hypothesis.

### Natural Gradient in CIF Threshold Space

For the defense configuration space $\Theta$ (§\ref{sec:at-infogeo}), the FIM generalizes to the parameter space of the CIF detection functions. For a binary detection function parameterized by threshold $\theta$:
\begin{equation}
I(\theta) = \frac{[\partial_\theta p_{\text{detect}}(\theta)]^2}{p_{\text{detect}}(\theta)(1 - p_{\text{detect}}(\theta))}.
\end{equation}
\label{eq:bernoulli-fim-threshold}
This is the Fisher information of a Bernoulli distribution with success probability $p_{\text{detect}}(\theta)$. The natural gradient of detection rate w.r.t. $\theta$ is:
\begin{equation}
\widetilde{\nabla}_\theta \text{DR}(\theta) = I(\theta)^{-1} \nabla_\theta \text{DR}(\theta) = \frac{p_{\text{detect}}(1 - p_{\text{detect}})}{[\partial_\theta p_{\text{detect}}]^2} \cdot \nabla_\theta \text{DR}.
\end{equation}
\label{eq:natural-gradient-dr}
Near the Nash equilibrium $\theta^*$ (where $p_{\text{detect}}(\theta^*) = \text{DR}^*$), the natural gradient converges quadratically (Theorem S11.2), while the Euclidean gradient converges only linearly. The function `src/redteam/convergence.py::natural_gradient_at_step()` implements this update.

### Geometric Interpretation of the Drift Threshold

The drift detection threshold $\theta_{\text{drift}} = 0.3$ admits a complete geometric derivation via the FIM. An agent's belief state $p$ drifts adversarially from baseline $p^{(0)}$ if the Fisher-Rao distance exceeds:
\begin{align}
d_{\text{FR}}(p^{(0)}, p) &= 2\arccos\!\left(\sum_i \sqrt{p^{(0)}_i p_i}\right) > \theta_{\text{drift}}.
\end{align}
\label{eq:drift-fisher-rao-threshold}
For two-dimensional belief spaces ($n = 2$), the threshold $\theta_{\text{drift}} = 0.3$ corresponds to:
\begin{equation}
\arccos\!\left(\sqrt{p \cdot (1-p)} + \sqrt{(1-p) \cdot p^{(0)}}\right) = 0.15 \text{ radians},
\end{equation}
\label{eq:drift-threshold-2d}
or equivalently a KL divergence of $\text{KL}(p \| p^{(0)}) \approx 0.0225$ (by the second-order Pinsker approximation). This is the scale at which CIF's drift detector first activates — a belief shift equivalent to moving from 50\% confidence to approximately 61\% on a binary hypothesis, consistent with ``ordinary learning'' rather than adversarial manipulation.

### Relation to the Stealth–Impact Bound

The Fisher-Rao geodesic distance provides the tightest information-theoretic constraint on stealth-bounded attacks. For an adversary constrained to move beliefs within a geodesic ball of radius $r$ (the stealth budget), the maximum achievable KL divergence from the baseline is:
\begin{equation}
\text{KL}_{\max}(r) = 2\sin^2(r/2) \leq r^2/2,
\end{equation}
\label{eq:stealth-kl-bound}
where the bound uses $\sin(x) \leq x$. The stealth–impact bound from Part 1 \cite{friedman2026cogsec1} §4.3 is recovered by substituting $r = \theta_{\text{drift}} / 2$ (half the detection radius):
\begin{equation}
\text{Impact} \leq f(\text{KL}_{\max}(r)) = f\!\left(2\sin^2(\theta_{\text{drift}}/4)\right),
\end{equation}
\label{eq:stealth-impact-bound}
where $f(\cdot)$ is the impact function from Definition 4.2 in Part 1. The information geometry thus provides a complete derivation of the stealth–impact bound from first principles, without requiring the empirical calibration of the drift threshold.

