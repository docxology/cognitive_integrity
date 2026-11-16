\newpage

# Bayesian Uncertainty Quantification {#sec:bayesian-uncertainty}

The primary statistical claims in this paper---detection rates, confidence intervals, and significance tests---are computed using frequentist methods (Wilson score intervals, two-proportion $z$-tests). This supplementary analysis reframes the reported proportions within a Bayesian Beta-Binomial model, providing credible intervals and a power analysis that quantifies the precision of each evaluation mode. No Bayes factor is claimed for unmatched arms. The Bayesian reanalysis adds an explicit precision estimate that motivates the methodological recommendations in \cref{sec:power-analysis}.

> **Reproducibility**: Posterior and power calculations use \texttt{src/statistics/bayesian.py}; the representative multi-seed plug-in reads \texttt{output/data/multi_seed\_results.json} directly. Validation and cross-checks against \texttt{scipy.stats.beta} are in \texttt{tests/test\_bayesian.py}.

## Beta-Binomial Model {#sec:beta-binomial}

Every detection-rate claim in this paper is a binary proportion: each evaluation trial either detects an attack or does not. The conjugate Bayesian model for $k$ detections out of $n$ trials is
\begin{equation}
\theta \sim \mathrm{Beta}(\alpha_0, \beta_0), \qquad k \mid \theta \sim \mathrm{Binomial}(n, \theta),
\end{equation}
\label{eq:beta-binomial-prior}
which yields the closed-form posterior
\begin{equation}
\theta \mid k, n \sim \mathrm{Beta}(\alpha_0 + k,\ \beta_0 + n - k).
\end{equation}
\label{eq:beta-binomial-posterior}
We use the uniform prior $\mathrm{Beta}(1, 1)$ throughout. This prior is noncommittal about the true detection rate, pulls posterior means toward $1/2$ only for small $n$, and is consistent with the conservative stance that a defense should not be credited with performance it has not empirically demonstrated. The Jeffreys prior $\mathrm{Beta}(0.5, 0.5)$ produces quantitatively similar intervals at all sample sizes relevant here; the choice does not affect any qualitative conclusion.

Credible intervals are reported as 95\% Highest Density Intervals (HDI), computed via \texttt{BetaPosterior.hdi()}. For symmetric posteriors the HDI coincides with the equal-tailed interval, but for posteriors near the boundary of $[0, 1]$ the HDI is narrower and more interpretable.

## Posterior Detection Rates for All Claimed Results {#sec:posterior-rates}

\cref{tab:bayesian-posteriors} restates each major detection claim from \cref{sec:results} and \cref{sec:parametric-analysis} as a Beta posterior with an explicit 95\% HDI, computed via `BetaPosterior(1 + k, 1 + n - k).hdi(0.95)`. For the multi-seed pipeline, $n = 100$ is the per-seed attack evaluation size (30 seeds, with 120 additional benign messages per seed) and $k = 86$ is obtained by rounding the measured mean rate of $0.863$ to a representative count. The row is therefore only a plug-in posterior for one representative 100-attack arm, not an observed seed's posterior or a posterior for 3,000 pooled trials. The across-seed mean CI is computed separately from the 30 seed-level rates.

Table: Beta-Binomial posteriors for major detection claims. Prior: $\mathrm{Beta}(1, 1)$; posterior $\mathrm{Beta}(1 + k,\, 1 + n - k)$; 95\% HDI computed via \texttt{BetaPosterior.hdi()}. {#tab:bayesian-posteriors}

| Result | $k$ | $n$ | Posterior | 95\% HDI |
| --- | --- | --- | --- | --- |
| Multi-seed pipeline (representative plug-in at rounded mean rate; not an observed seed) | 86 | 100 | $\mathrm{Beta}(87, 15)$ | $[0.784, 0.918]$ |
| Ablation full pipeline TPR | 89 | 100 | $\mathrm{Beta}(90, 12)$ | $[0.819, 0.941]$ |
| LLM validation (Claude Code) | 4 | 5 | $\mathrm{Beta}(5, 2)$ | $[0.409, 0.982]$ |
| LLM validation (CrewAI) | 5 | 5 | $\mathrm{Beta}(6, 1)$ | $[0.607, 1.000]$ |
| Parametric full CIF (direct injection) | 92 | 100 | $\mathrm{Beta}(93, 9)$ | $[0.856, 0.963]$ |
| Colony: Sybil infiltration | 20 | 20 | $\mathrm{Beta}(21, 1)$ | $[0.867, 1.000]$ |
| Colony: Emergent misalignment (30-seed mean) | — | 30 seeds | Not Beta-Binomial; bootstrap CI in \cref{sec:colony-results} | 0.743 point estimate |

The representative multi-seed plug-in posterior under the uniform prior has a posterior median detection rate of $0.855$ with a 95\% HDI of $[0.784, 0.918]$. This interval width (0.134) reflects the per-seed sample size ($n = 100$). It is constructed by rounding the 0.863 mean to $k=86$ detections in a representative 100-attack seed; it is not an observed seed's posterior and does not pool the 30 seeds as 3,000 independent Bernoulli trials. The 30-seed run instead characterizes between-seed variability. Two observations are immediately visible. First, the LLM validation results have extremely wide HDIs (Claude Code width 0.573, CrewAI width 0.393) due to small sample sizes ($n = 5$ per architecture); these cannot support the 80–100\% detection range claimed in the abstract without acknowledging the wide credible intervals. Second, the ablation TPR posterior uses the observed $89/100$ detections from \cref{sec:extended-ablation}, whereas the multi-seed row is only the representative plug-in described above. Their intervals are not a matched-arm comparison, so no gap between them is inferred.

## Limits of the Parametric--Empirical Comparison {#sec:bayes-factors}

A Bayes factor compares matched proportions on the same experiment \cite{kass1995bayes}; the arms below are not matched, so no such factor is reported.

No Bayes factor is reported for the parametric--empirical contrast. The parametric direct-injection response surface and the architecture-agnostic multi-seed arm use different corpora, category mixtures, denominators, and evaluation modes. Treating them as two matched binomial samples would manufacture a comparison that the experiments did not perform and could not identify a structural or adapter-maturity cause.

The representative multi-seed posterior is instead computed directly from the shipped artifact, with the plug-in construction made explicit:

\begin{lstlisting}[language=Python]
import json
from pathlib import Path
from src.statistics.bayesian import BetaPosterior

payload = json.loads(
    Path("output/data/multi_seed_results.json").read_text(encoding="utf-8")
)
n = payload["seed_metrics"][0]["n_attacks"]
k = round(payload["tpr_mean"] * n)
posterior = BetaPosterior(1 + k, 1 + n - k)
# Current artifact: n=100, k=86, posterior=Beta(87, 15).
# Representative plug-in only; not a 30-seed independent-trial aggregate.
\end{lstlisting}

## Power Analysis {#sec:power-analysis}

The last and most actionable Bayesian analysis is the prospective power calculation: how many evaluation trials are required to resolve each detection rate to a target HDI width? Using \texttt{power\_analysis\_beta\_binomial()} with target HDI half-width $0.05$ (i.e.\ $\pm 5$ percentage points), we obtain the following:

Table: Required sample size $n^*$ for $\pm 5$ pp HDI at each mode's estimated true rate. ``Adequately powered'' means current $n$ achieves $\pm 5$ pp HDI. {#tab:power-analysis}

| Evaluation Mode | Est.\ True Rate | Current $n$ | Required $n^*$ | Adequate? |
| --- | --- | --- | --- | --- |
| Parametric simulation | 0.96 | 3{,}800 | 75 | yes |
| Colony structured scenarios | 0.90 | 20--100 | 145 | partial |
| Multi-seed pipeline (representative per-seed plug-in) | 0.863 | 100 | 185 | **no** |
| LLM validation (per architecture) | 0.80 | 5--10 | 245 | **no** |
| Ablation TPR | 0.89 | 100 | 150 | **no** |


Three results in \cref{tab:power-analysis} warrant attention. The representative multi-seed plug-in at $n=100$ falls short of the $n^*=185$ required for its $\pm5$ pp target; this does not change the separately estimated across-seed mean CI. The LLM validation evaluations (currently $n = 5$--$10$ per architecture) achieve only $\pm 29$ to $\pm 22$ percentage points of precision at the observed $80\%$ rate (the 95\% HDI at $n=5$ is $[0.409, 0.982]$). A minimum of $n = 245$ evaluations per architecture is required to bring the HDI half-width down to $\pm 5$ pp. This is the single largest precision deficit in the current study and the highest-priority methodological gap for future replications. The ablation TPR evaluation is also underpowered: at its $0.89$ detection rate the current $n = 100$ gives a 95\% HDI half-width of $\pm 6$ pp, short of the $n^* = 150$ required for $\pm 5$ pp.

\begin{remark}[Underpowering vs.\ Publication Bias]\label{rem:not-publication-bias}
The underpowering documented here is a limitation of the current study, not an indicator of publication bias. The parametric simulations are adequately powered at $n = 3{,}800$; the colony structured scenarios are adequately powered in aggregate; and the representative multi-seed plug-in at $n = 100$ has roughly $\pm 7$ pp precision. Separately, the normal-approximation CI for the mean of the 30 seed-level rates is $[0.855,0.871]$; this is not obtained by treating 3,000 attacks as iid trials. All detection rates in \cref{tab:bayesian-posteriors} are reported with credible intervals that reflect the stated sample size and plug-in status. The appropriate response to \cref{tab:power-analysis} is replication at the required $n^*$, not reinterpretation of the existing point estimates.
\end{remark}
