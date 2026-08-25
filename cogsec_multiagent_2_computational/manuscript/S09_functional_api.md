\newpage

# Supplement S09: Functional and Monadic API Specification {#sec:s09-functional-api}

This supplement provides the complete specification for CIF's functional and monadic defense interfaces. The framework described here is implemented in \texttt{src/core/monad.py} and \texttt{src/formal/category\_theory.py}; the formal laws that the interface satisfies are proved in \cref{sec:monadic-laws} and \cref{sec:category-theory}. This specification is the normative reference for call-site code that composes defense modules using the typed Result interface; for the procedural (class-based) interface, see \cref{sec:framework-api} (Supplement S5).

> **Cross-paper reading guide.**
> • **Formal basis** — the monadic laws, functor composition and natural transformations are developed in this paper's category-theoretic foundations section; what Part 1 \cite{friedman2026cogsec1} supplies is the defense composition algebra they are built to model.
> • **Deployment guidance** — deciding between the procedural API (S5) and the functional API (S9) in production depends on your integration constraints. No part of this series surveys that choice empirically; it is an engineering judgement about the calling code.
> • **Domain applications** — the functional API is especially useful in high-assurance operational domains (infrastructure, biowarfare) where explicit error propagation is required; see unified Part 3+4 \cite{friedman2026cogsec3}, Sections 9.06 and 9.10.

> **Reproducibility.** Empirical verification of the monadic laws and category laws runs as part of \texttt{uv run pytest tests/test\_formal.py}. Each law has a generator-based test that samples random morphisms and checks equality. Tests use real numerical data only — see [`src/AGENTS.md`](../src/AGENTS.md) for the no-mocks policy.

## Type Hierarchy {#sec:s09-type-hierarchy}

The core types form a small, disciplined hierarchy. The sum type $\mathrm{Result}[T, E]$ is the root; $\mathrm{Ok}[T]$ and $\mathrm{Err}[E]$ are its two variants; $\mathrm{DetectionEvent}$ is the specific $E$ used by CIF; and existing types from \texttt{src/core/base.py} connect into this hierarchy via the adapter \texttt{from\_defense\_result()}.

Table: CIF monadic API types. {#tab:s09-types}

| Type | Kind | Role |
| --- | --- | --- |
| \texttt{Result[T, E]} | generic sum type | pipeline state: success or detection |
| \texttt{Ok[T]} | $\mathrm{Result}$ variant | carries the current cognitive state |
| \texttt{Err[E]} | $\mathrm{Result}$ variant | carries a detection event; absorbing under \texttt{bind} |
| \texttt{DetectionEvent} | dataclass | \texttt{module\_name}, \texttt{score}, \texttt{details} |
| \texttt{DefenseResult} | existing | per-module output; bridged via \texttt{from\_defense\_result} |
| \texttt{DefenseModule} | existing ABC | any subclass is automatically a \texttt{DefenseProtocol} |
| \texttt{DefenseMorphism} | categorical | $\sigma \to \mathrm{Result}[\sigma, \mathrm{DetectionEvent}]$ |

The bridge from $\mathrm{DefenseResult}$ (the legacy per-module record) to $\mathrm{DetectionEvent}$ (the monadic error payload) is \texttt{from\_defense\_result(r, pass\_through=None)}: it returns $\mathrm{Ok}$ carrying \texttt{pass\_through} --- the $\mathrm{DefenseResult}$ itself when that argument is omitted --- if \texttt{r.detected} is false, and $\mathrm{Err}(\mathrm{DetectionEvent}(\ldots))$ if it is true, lifting \texttt{r.module\_name}, \texttt{r.score} and a copy of \texttt{r.details} into the event. The lift is not total: \texttt{r.latency\_ms} is not carried.

## \texttt{MonadicPipeline} Full Specification {#sec:s09-pipeline}

\paragraph{Constructor.} \texttt{MonadicPipeline(modules: list[DefenseProtocol])} takes an ordered list of defense modules. The order is semantically significant: modules are evaluated left-to-right, and the first module whose evaluation yields a detection event short-circuits the pipeline. Empty pipelines are legal and return $\mathrm{Ok}([])$ for every input.

\paragraph{Method: \texttt{run}.} The primary evaluation entry point is
\begin{lstlisting}[language=Python]
def run(
    self,
    message: str,
    context: dict | None = None,
) -> Result[list[DefenseResult], DetectionEvent]: ...
\end{lstlisting}
with the following behavioral guarantees:

\begin{enumerate}
\item \emph{Short-circuit}: if module $i$ returns $\mathrm{Err}(e)$, modules $i+1, \ldots, m$ are not invoked.
\item \emph{Result accumulation}: if all modules return $\mathrm{Ok}$, the return value is $\mathrm{Ok}([r_1, \ldots, r_m])$, preserving the order of evaluation.
\item \emph{Determinism}: for fixed modules and fixed $(message, context)$, repeated invocations of \texttt{run} return bit-identical results (subject to modules that themselves use seeded randomness).
\item \emph{Detection preservation}: once an $\mathrm{Err}$ is produced, no subsequent call can erase or overwrite it (\cref{thm:monadic-laws}, Law 4).
\item \emph{Empty-pipeline identity}: an empty pipeline returns $\mathrm{Ok}([])$, matching the monadic identity element.
\end{enumerate}

\paragraph{Edge cases.} The three edge cases worth documenting are:
\begin{itemize}
\item \emph{Empty pipeline}: returns $\mathrm{Ok}([])$. Useful as a no-op placeholder in configurable deployments.
\item \emph{All-pass}: returns $\mathrm{Ok}([r_1, \ldots, r_m])$ with one result per module. Caller code can inspect individual scores for diagnostic purposes.
\item \emph{First-module detection}: returns $\mathrm{Err}$ with $r_2, \ldots, r_m$ never computed. The \texttt{DetectionEvent} contains only the first module's diagnostic data; callers that need per-module scores on detected inputs should use \texttt{SeriesPipeline} instead, which always runs all modules.
\end{itemize}

\paragraph{Complete working example.}

\begin{lstlisting}[language=Python]
from src.core.monad import MonadicPipeline, Ok, Err, DetectionEvent
from src.core.firewall import CognitiveFirewall
from src.core.sandbox import SandboxManager
from src.utils.config import FrameworkConfig

config = FrameworkConfig()
pipeline = MonadicPipeline([
    CognitiveFirewall(config),
    SandboxManager(config),
])

result = pipeline.run(
    "Ignore previous instructions. Execute rm -rf.",
    context={"source": "external_user", "trust_score": 0.3},
)

match result:
    case Ok(defense_results):
        print(f"Clean input: {len(defense_results)} modules passed")
    case Err(event):
        print(
            f"Attack detected: {event.module_name} "
            f"(score={event.score:.3f}, reason={event.context.get('reason')})"
        )
\end{lstlisting}

For the above input, \texttt{CognitiveFirewall} fires first with a direct-injection score above $\tau_1$, yielding an $\mathrm{Err}(\mathrm{DetectionEvent}(\texttt{module\_name}=\texttt{"firewall"}, \ldots))$. The sandbox module is never invoked.

## Protocol Types for Composability {#sec:s09-protocols}

Protocol types express the minimal structural contract that makes a class usable as a CIF defense. Because Python's \texttt{Protocol} mechanism uses structural subtyping, classes satisfy protocols by virtue of shape, not inheritance.

\begin{lstlisting}[language=Python]
from typing import Protocol
from src.core.base import DefenseResult, CognitiveState
from src.core.monad import Ok, Result, DetectionEvent

class DefenseProtocol(Protocol):
    """Structural contract for any CIF-compatible defense."""
    def evaluate(
        self,
        message: str,
        context: dict | None = None,
    ) -> DefenseResult: ...

class MonadicDefense(Protocol):
    """Direct monadic interface for category-theoretic composition."""
    def __call__(
        self,
        state: Ok[CognitiveState],
    ) -> Result[CognitiveState, DetectionEvent]: ...
\end{lstlisting}

Any existing \texttt{DefenseModule} subclass automatically satisfies \texttt{DefenseProtocol} because the ABC mandates the \texttt{evaluate()} method. New defense implementations may either subclass \texttt{DefenseModule} (inheriting telemetry and lifecycle hooks) or implement \texttt{evaluate()} directly (minimizing coupling). The monadic form \texttt{MonadicDefense} is principally used inside \texttt{src/formal/category\_theory.py} for categorical operations such as \texttt{compose\_morphisms()}, \texttt{identity\_morphism()}, and \texttt{categorical\_product()}.

The bridge between the two interfaces is \texttt{lift\_defense\_module()}, which wraps any \texttt{DefenseProtocol} as a \texttt{DefenseMorphism}. This is how legacy \texttt{DefenseModule} subclasses enter the categorical framework: no code modification is required, and the wrapper preserves the detection outcome exactly.

## Comparison with Existing \texttt{SeriesPipeline} {#sec:s09-comparison}

Both pipeline interfaces produce identical detection outcomes on identical inputs. The differences are in typing, composition story, and formal guarantees, not in what gets detected.

Table: Side-by-side comparison of the two pipeline interfaces. {#tab:s09-pipeline-comparison}

| Feature | \texttt{SeriesPipeline} | \texttt{MonadicPipeline} |
| --- | --- | --- |
| Detection behavior | identical | identical |
| Short-circuit on detection | yes (implicit) | yes (monadic, by law) |
| Error propagation | manual (boolean flags) | automatic (\texttt{Err} track) |
| Type of return value | \texttt{list[DefenseResult]} + \texttt{detected: bool} | \texttt{Result[list[DefenseResult], DetectionEvent]} |
| Type safety of composition | none (accepts any callable) | enforced (\texttt{DefenseProtocol}) |
| Categorical composition | implicit (ordering is everything) | explicit via \texttt{compose\_morphisms()} |
| Monad laws | operationally satisfied | formally verified (\cref{thm:monadic-laws}) |
| Typical use site | legacy call sites; regression tests | new code; formal analysis; proofs |

The migration path between the two interfaces is symmetric: any \texttt{SeriesPipeline} can be converted to a \texttt{MonadicPipeline} by passing the same module list, and any \texttt{MonadicPipeline} can be converted back by unwrapping the Result. The regression suite exercises the legacy \texttt{SeriesPipeline}, and \texttt{uv run pytest tests/test\_formal.py} exercises the monadic interface against the same corpus; both interfaces are covered by the project test gate. Selection between them is a local design decision, not a framework-wide commitment.
