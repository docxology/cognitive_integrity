\newpage

# Supplement S10: Information Geometry of Belief Manipulation {#sec:information-geometry}

This supplement develops the information-geometric structure of the CIF belief state space and shows how this geometry illuminates three otherwise disconnected aspects of the framework: the drift-detection threshold $\theta_{\text{drift}} = 0.3$, the sandbox corroboration threshold $\kappa$, and the choice of canary-belief probability $\tau_{\text{canary}}$ for tripwires. Implementations of the constructions below are in [`src/analysis/information_geometry.py`](../src/analysis/information_geometry.py); the numerical checks on curvature and geodesic lengths are in \texttt{tests/test\_information\_geometry.py}.

> **Cross-paper reading guide.**
> • **Formal stealth–impact bound** (which the Fisher–Rao construction realizes) is stated and proved in Part 1 \cite{friedman2026cogsec1} §4.3.
> • **Operational implications** of the geodesic attack path for active-inference-based monitoring are discussed in Part 3 \cite{friedman2026cogsec3} §2 (theory review).
> • **Domain applications** — the geodesic framework applies to high-stakes sectors where adversarial inputs stay within a stealth budget; see Part 4 \cite{friedman2026cogsec4} §3.10 (information ecosystems, fake-news detection) in particular, where the Fisher–Rao metric informs distribution-shift monitoring.

> **Reproducibility.** All geometric quantities (Fisher–Rao distances, geodesic paths, natural gradient directions) can be regenerated from [`src/analysis/information_geometry.py`](../src/analysis/information_geometry.py). Thin orchestrator: invoke via the publication suite (`uv run python scripts/run_publication_suite.py`) or directly via `StatisticalManifold` / `geodesic_attack_path`.

## Belief Space as Statistical Manifold {#sec:s10-manifold}

Each agent's belief state is a probability distribution over a finite belief vocabulary of size $n$: $p = (p_1, \ldots, p_n)$ with $p_i \geq 0$ and $\sum_i p_i = 1$. The set of such distributions is the probability simplex $\Delta^{n-1} \subset \mathbb{R}^n$, a smooth manifold of dimension $n - 1$.

The canonical Riemannian metric on $\Delta^{n-1}$ is the \emph{Fisher-Rao metric}, given in barycentric coordinates by
\begin{equation}
G_{ij}(p) = \frac{\delta_{ij}}{p_i}.
\end{equation}
The Fisher-Rao metric is the unique metric (up to scaling) invariant under sufficient statistics \cite{cencov1982statistical,amari2000methods}; using any other metric would implicitly privilege some coordinate chart over the intrinsic probabilistic structure.

A useful change of coordinates is the \emph{Hellinger embedding} $p \mapsto (\sqrt{p_1}, \ldots, \sqrt{p_n})$, which maps $\Delta^{n-1}$ isometrically onto a hemisphere of the unit sphere $S^{n-1}$ in $\mathbb{R}^n$. Under this embedding, the Fisher-Rao geodesic distance between distributions $p, q$ is the \emph{Bhattacharyya angle}
\begin{equation}
d_{\mathrm{FR}}(p, q) = 2 \arccos\!\left(\sum_{i=1}^{n} \sqrt{p_i \, q_i}\right).
\end{equation}

The manifold has constant positive curvature $\kappa_{\mathrm{curv}} = n(n-1)/4$. The practical consequence is that small differences in KL divergence translate to even larger geometric separations: two distributions that differ by $\KL = 0.1$ correspond to a geodesic distance bounded above by $\sqrt{2 \cdot 0.1} \approx 0.45$ radians (by the Pinsker-type inequality connecting KL and Fisher-Rao distance), and the positive curvature \emph{amplifies} the geometric distinguishability of nearby distributions in a bounded way.

## Attacks as Geodesic Updates {#sec:s10-geodesic-attacks}

An adversary that seeks to drive agent $i$'s beliefs from a baseline $p^{(0)}$ to an attacker-preferred target $p^{(\text{target})}$ is, geometrically, traversing $\Delta^{n-1}$ along some path. The \emph{minimum-effort} path in the Fisher-Rao metric is the geodesic
\begin{equation}
\gamma_{\text{attack}}(t) = \mathrm{normalize}\!\left( \left( \sqrt{p^{(0)}} + t\,(\sqrt{p^{(\text{target})}} - \sqrt{p^{(0)}}) \right)^2 \right), \quad t \in [0, 1],
\end{equation}
a great-circle arc on the Hellinger hemisphere. The helper \texttt{geodesic\_attack\_path()} in \texttt{src/analysis/information\_geometry.py} constructs $\gamma_{\text{attack}}$ and samples it at a configurable step count.

The connection to CIF's drift detector (Part 1, Definition 6.1) comes from the following standard fact: for small steps $\delta$ from a distribution $p$,
\begin{equation}
\KL[p \,\|\, p + \delta] = \frac{1}{2}\, \delta^{\top} G(p) \delta + O(\|\delta\|^3).
\end{equation}
That is, the KL divergence is (to second order) the squared Fisher-Rao distance. The drift-detector threshold $\theta_{\text{drift}} = 0.3$ therefore corresponds to a geodesic step whose length, in radians on the Hellinger hemisphere, is approximately $2 \arcsin(\sqrt{0.3}/2) \approx 0.28$ radians. The empirically-calibrated threshold thus admits a principled geometric interpretation: it is the arc length beyond which belief updates have crossed from ``ordinary learning'' into ``territory probably controlled by a single adversarial channel''. This is a more satisfying justification than ``tuned on the validation corpus'' and is robust to changes in the corpus that do not change the underlying geometry.

## Defense as Curvature Constraint {#sec:s10-curvature-constraint}

The sandbox's corroboration criterion (Part 1, Definition 5.4) can be restated geometrically. A belief update is provisionally allowed inside the sandbox, but promotion to the verified partition requires corroboration count $\geq \kappa$; equivalently, it requires that the updated belief lie within a geodesic ball around a multiply-witnessed reference.

\begin{theorem}[Curvature Constraint Defense, CG.1]\label{thm:curvature-constraint}
The CIF belief sandbox with corroboration threshold $\kappa$ and per-step update precision $\epsilon_{\text{precision}}$ implements a geodesic ball constraint of radius
\begin{equation}
\rho = 2 \arccos\!\left( \sqrt{1 - \kappa \cdot \epsilon_{\text{precision}}} \right)
\end{equation}
around the baseline belief state $p^{(0)}$ in the Fisher-Rao metric: a provisional update $p^{(*)}$ is promoted if and only if $d_{\mathrm{FR}}(p^{(0)}, p^{(*)}) \leq \rho$.
\end{theorem}

\begin{proof}[Proof sketch]
The corroboration criterion requires that $\kappa$ independent corroborating observations have been seen, each of which reduces the posterior uncertainty by $\epsilon_{\text{precision}}$ under the FEP-equivalent formulation (\cref{thm:attack-fep}). The cumulative effect is a tightening of the posterior's Bhattacharyya coefficient with the reference distribution to at least $1 - \kappa \cdot \epsilon_{\text{precision}}$, which translates to the Fisher-Rao ball radius $\rho = 2\arccos(\sqrt{1 - \kappa \cdot \epsilon_{\text{precision}}})$. The helper \texttt{defense\_as\_curvature\_constraint()} evaluates this radius and accepts or rejects an update against it.
\end{proof}

\cref{thm:curvature-constraint} provides a concrete practical implication. Operators who want to harden the sandbox against belief-manipulation attacks can either (a) increase $\kappa$, (b) raise the per-observation precision $\epsilon_{\text{precision}}$ by filtering low-precision channels, or (c) directly specify the geodesic radius $\rho$ and back-solve for $(\kappa, \epsilon_{\text{precision}})$. Option (c) is preferable when the security requirement is geometric (``no update moves beliefs by more than $x$ radians'') rather than statistical (``$\kappa$ corroborators required'').

## Natural Gradient Attacks and Sensitivity {#sec:s10-natural-gradient}

The natural gradient \cite{amari1998natural} is the gradient of a loss $L(p)$ expressed with respect to the Fisher-Rao metric rather than the Euclidean metric:
\begin{equation}
\widetilde{\nabla}_i L(p) = G^{-1}(p) \nabla L(p) = p_i \, \frac{\partial L}{\partial p_i}.
\end{equation}
On the probability simplex, the natural gradient is the coordinate-wise product of the Euclidean gradient and the belief probabilities themselves.

An adversary performing gradient-based belief manipulation is, from a geometric standpoint, more efficient using the natural gradient than the Euclidean gradient because the natural gradient respects the manifold's curvature and moves along geodesics rather than across them. The helper \texttt{sensitivity\_via\_riemannian\_metric()} quantifies the resulting sensitivity by computing $\widetilde{\nabla} L$ at each belief and reporting the per-dimension magnitude.

The result is a non-obvious security insight: high-probability beliefs (large $p_i$) have proportionally larger natural-gradient magnitude and are therefore \emph{more} susceptible to gradient-based attacks than low-probability beliefs. This inverts the naive intuition that confident beliefs are hard to move. A belief at $p_i = 0.95$ has natural gradient magnitude nearly twenty times larger than a belief at $p_i = 0.05$, for the same Euclidean gradient.

CIF's tripwire monitoring of canary beliefs (\cref{alg:tripwire-impl}) at thresholds $\tau_{\text{canary}} > 0.9$ directly addresses this vulnerability: canary placements are concentrated at the beliefs that geometric analysis identifies as the most gradient-sensitive, precisely where an efficient adversary will focus their effort. The canary-threshold choice of $0.9$ is therefore not an arbitrary high-probability convention but a principled selection of the points of maximum geometric vulnerability on the simplex.
