\newpage

# Supplement S10: Information Geometry of Belief Manipulation {#sec:information-geometry}

This supplement develops the information-geometric structure of the CIF belief state space and shows how this geometry illuminates three otherwise disconnected aspects of the framework: the drift-detection threshold $\theta_{\text{drift}} = 0.3$, the sandbox corroboration threshold $\kappa$, and the choice of canary-belief probability $\tau_{\text{canary}}$ for tripwires. Implementations of the constructions below are in [`src/analysis/information_geometry.py`](../../src/analysis/information_geometry.py); the numerical checks on curvature and geodesic lengths are in \texttt{tests/test\_information\_geometry.py}.

> **Cross-paper reading guide.**
> • **Stealth–impact tradeoff** is posed as an open formalization in Part 1 \cite{friedman2026cogsec1}; the Fisher–Rao construction does not prove it.
> • **Operational implications** of the geodesic attack path for active-inference-based monitoring are discussed in Part 3 \cite{friedman2026cogsec3}'s theory-review section, under The Science Behind Belief Updates: Free Energy (Practical Implication for Operators).
> • **Domain applications** — the geodesic framework applies to high-stakes sectors where adversarial inputs stay within a stealth budget; see Part 3 \cite{friedman2026cogsec3}, its Distilling Fake from Real News domain (information ecosystems, fake-news detection) in particular, where the Fisher--Rao metric informs distribution-shift monitoring.

> **Reproducibility.** All geometric quantities (Fisher–Rao distances, geodesic paths, natural gradient directions) can be regenerated from [`src/analysis/information_geometry.py`](../../src/analysis/information_geometry.py). Thin orchestrator: invoke via the publication suite (`uv run python scripts/run_publication_suite.py`) or directly via `StatisticalManifold` / `geodesic_attack_path`.

## Belief Space as Statistical Manifold {#sec:s10-manifold}

Each agent's belief state is a probability distribution over a finite belief vocabulary of size $n$: $p = (p_1, \ldots, p_n)$ with $p_i \geq 0$ and $\sum_i p_i = 1$. The set of such distributions is the probability simplex $\Delta^{n-1} \subset \mathbb{R}^n$, a smooth manifold of dimension $n - 1$.

The canonical Riemannian metric on $\Delta^{n-1}$ is the \emph{Fisher-Rao metric}, given in barycentric coordinates by
\begin{equation}
G_{ij}(p) = \frac{\delta_{ij}}{p_i}.
\end{equation}
\label{eq:fisher-rao-metric}
The Fisher-Rao metric is the unique metric (up to scaling) invariant under sufficient statistics \cite{cencov1982statistical,amari2000methods}; using any other metric would implicitly privilege some coordinate chart over the intrinsic probabilistic structure.

A useful change of coordinates is the \emph{Hellinger embedding} $p \mapsto (\sqrt{p_1}, \ldots, \sqrt{p_n})$, which maps $\Delta^{n-1}$ onto the positive orthant of the unit sphere $S^{n-1}$ in $\mathbb{R}^n$ (a hemisphere only in the two-outcome case). Under this embedding, the Fisher-Rao geodesic distance between distributions $p, q$ is the \emph{Bhattacharyya angle}
\begin{equation}
d_{\mathrm{FR}}(p, q) = 2 \arccos\!\left(\sum_{i=1}^{n} \sqrt{p_i \, q_i}\right).
\end{equation}
\label{eq:bhattacharyya-angle}

The unit sphere has sectional curvature $1$ and, in dimension $n-1$, scalar curvature $(n-1)(n-2)$. The number $(n-1)(n-2)$ is the \emph{scalar} curvature in that dimension; $\kappa=n(n-1)/4$ uses the number of categories rather than the manifold dimension and is not a sectional-curvature formula. (Part 1 instead uses the scaled embedding $2\sqrt p$, whose sphere has sectional curvature $1/4$.) For small perturbations, the local quadratic approximation $\KL[p\|p+\delta]\approx \delta^\top G(p)\delta/2$ gives a Fisher-Rao displacement $r\approx\sqrt{2\KL}$; for $\KL=0.1$ this is approximately $0.45$ radians. Pinsker's inequality is not a claim that KL is always bounded above by the resulting displacement, and constant positive curvature does not by itself amplify distinguishability.

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
That is, the KL divergence is locally one half the squared Fisher-Rao distance. A normalized KL drift threshold $\theta_{\text{drift}}=0.3$ therefore corresponds to $r\approx\sqrt{2(0.3)}=0.775$ radians under that small-step approximation, not $0.28$. This is only a geometric interpretation of a chosen detector threshold: it neither derives nor calibrates an operational security boundary, and it says nothing about whether a channel is adversarial.

## Defense as Curvature Constraint {#sec:s10-curvature-constraint}

The sandbox's corroboration criterion and a geodesic step budget are distinct controls, not an established equivalence. A count of independent corroborators does not determine a Bhattacharyya coefficient or a Fisher-Rao distance without an observation model; no such derivation is asserted here. The independent helper \texttt{defense\_as\_curvature\_constraint()} rejects proposed updates whose Fisher-Rao distance exceeds its explicit \texttt{max\_geodesic\_step} argument. That geometric budget can be used alongside the sandbox, but it is not a consequence of the sandbox's corroboration threshold $\kappa$.

## Natural Gradient Attacks and Sensitivity {#sec:s10-natural-gradient}

The natural gradient \cite{amari1998natural} is the gradient of a loss $L(p)$ expressed with respect to the Fisher-Rao metric rather than the Euclidean metric:
\begin{equation}
\widetilde{\nabla}_i L(p) = G^{-1}(p) \nabla L(p) = p_i \, \frac{\partial L}{\partial p_i}.
\end{equation}
\label{eq:natural-gradient-belief}
On the probability simplex, the natural gradient is the coordinate-wise product of the Euclidean gradient and the belief probabilities themselves.

The helper \texttt{sensitivity\_via\_riemannian\_metric()} computes $\widetilde{\nabla} L = p_i\,\partial_i L$ at each belief. A larger component of the natural gradient does not imply that an adversary can more easily move that belief, nor that a discrete natural-gradient step follows a geodesic; those conclusions require a loss, an attack model, and a step-size analysis not supplied here. Consequently the $0.9$ canary threshold is an operational choice, not a derived placement at a maximally vulnerable point.

## Fisher Information Metric: Complete Derivations {#sec:s10-fim-derivations}

> **Second-edition derivation.** This section derives the Fisher information matrix (FIM) for the CIF belief state parameterization, extending the survey in §\ref{sec:s10-manifold} with explicit computations for practical parameter choices used in the empirical evaluation.

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

**Numerical verification.** The implementation in `src/analysis/information_geometry.py::StatisticalManifold.fisher_information_matrix()` computes $G(\theta) = \text{diag}(1/\theta_i)$ and verifies positive semi-definiteness. The test `tests/test_property_based.py::TestInformationGeometryProperties::test_fisher_info_matrix_positive_definite` confirms PSD for all valid probability distributions generated by Hypothesis \cite{hypothesis2019}.

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

A separate geometric drift rule may compare the Fisher-Rao distance to a chosen radius $r_\theta$:
\begin{align}
d_{\text{FR}}(p^{(0)}, p) &= 2\arccos\!\left(\sum_i \sqrt{p^{(0)}_i p_i}\right) > r_\theta .
\end{align}
\label{eq:drift-fisher-rao-threshold}
For $r_\theta=0.3$ radians, the small-step KL approximation gives $\KL\approx r_\theta^2/2=0.045$, not $0.0225$. In a binary model $p^{(0)}=(1/2,1/2)$, the boundary is $p\approx0.611$ or $0.389$. This analogy must not be conflated with the operational normalized-KL threshold $\theta_{\text{drift}}=0.3$, whose local Fisher-Rao displacement is $r\approx\sqrt{0.6}=0.775$ radians. Neither value proves an adversarial intent or a first-activation point.

### Relation to the Stealth–Impact Bound

Fisher-Rao distance constrains geometric displacement, but it does not bound KL divergence either above or below by a universal function of radius alone. The small-step relation $\KL\approx r^2/2$ is an approximation, not the exact identity $2\sin^2(r/2)$; substituting a drift threshold does not derive Part 1's proposed stealth-impact tradeoff. That tradeoff remains unproved, and no capacity bound is asserted here.

