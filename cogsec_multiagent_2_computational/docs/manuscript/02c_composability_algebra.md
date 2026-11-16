\newpage

# Composability Algebra: Monadic Defense Chains {#sec:composability-algebra}

The series and parallel composition theorems of Part 1 (the Defense Mechanisms section) specify the \emph{outcome} of composing defense modules, but not the idiomatic way to build such compositions in code. This section develops the missing algebra: a typed, monadic interface whose composition laws are formally verified and whose implementation (\texttt{src/core/monad.py}) produces detection outcomes identical to the existing \texttt{SeriesPipeline}.

## Railway-Oriented Programming for Defense {#sec:railway-oriented}

Traditional defense pipelines interleave success paths with explicit null-checking, exception handling, and early-return control flow. Each module must redundantly decide whether the previous module has already flagged the input, and subtle bugs arise when this bookkeeping is inconsistent across modules. Railway-oriented programming \cite{wlaschin2014railway} eliminates this redundancy by structuring computation as a two-track pipeline: every step either stays on the success track (\texttt{Ok}) or diverges to the error track (\texttt{Err}), and subsequent steps automatically receive the current track without the pipeline author writing any branching logic.

The CIF adaptation maps cleanly onto this pattern. Let $\mathrm{Result}[T, E] = \mathrm{Ok}[T] \mid \mathrm{Err}[E]$ be the sum type of successful values of type $T$ and errors of type $E$. The generic monad permits any $T$; \texttt{MonadicPipeline} specifically returns \texttt{Ok(list[DefenseResult])} after a clean run. Its detection branch carries a $\mathrm{DetectionEvent}$ with the firing module's identity, score, and details. A defense chain becomes

\begin{lstlisting}[language=Python]
from src.composition import create_module_dict
from src.core.monad import MonadicPipeline, Ok, Err

modules = create_module_dict()
pipeline = MonadicPipeline([modules["firewall"], modules["invariants"]])
result = pipeline.run("Ignore previous instructions. Disregard your rules.")

match result:
    case Ok(defense_results):
        # All modules passed; one DefenseResult per executed module.
        print([r.module_name for r in defense_results])
    case Err(event):
        # The firewall detected this input; invariants did not run.
        print(event.module_name, event.score, event.details)
\end{lstlisting}

The key operational property is that once any module returns a $\mathrm{DetectionEvent}$, the $\mathrm{Err}$ track short-circuits the remaining modules. No downstream module can mask, suppress, or ``apologize for'' an upstream detection. Both `MonadicPipeline([])` and `SeriesPipeline([])` raise `ValueError`; neither treats an empty defense chain as `Ok([])` or as a clean evaluation. We now prove this is a formal monadic property rather than an ad hoc implementation convention.

## Formal Monadic Laws {#sec:monadic-laws}

\begin{theorem}[Monadic Detection Preservation, CT.3]
The $\mathrm{Result}[T, E]$ construction equipped with the \texttt{bind} operation
\begin{align}
\label{eq:monad-bind}
\texttt{bind}(\mathrm{Ok}(t), f) &= f(t), \\
\texttt{bind}(\mathrm{Err}(e), f) &= \mathrm{Err}(e),
\end{align}
satisfies the three standard monad laws and a fourth CIF-specific detection-preservation law:
\begin{enumerate}
\item \emph{Left identity}: $\texttt{bind}(\mathrm{Ok}(\cogstate{}), f) = f(\cogstate{})$.
\item \emph{Right identity}: $\texttt{bind}(m, \mathrm{Ok}) = m$ for any $m \in \mathrm{Result}[T, E]$.
\item \emph{Associativity}: $\texttt{bind}(\texttt{bind}(m, f), g) = \texttt{bind}(m, \lambda \cogstate{}.\, \texttt{bind}(f(\cogstate{}), g))$.
\item \emph{Detection preservation}: $\texttt{bind}(\mathrm{Err}(e), f) = \mathrm{Err}(e)$ for every continuation $f$.
\end{enumerate}
\end{theorem}

\begin{proof}[Proof sketch]
Laws 1--3 follow from the standard construction of the error monad (also known as the ``either'' monad in Haskell's \texttt{Control.Monad.Error}). Left identity unfolds by definition of \texttt{bind} on an $\mathrm{Ok}$ argument. Right identity unfolds case-wise: if $m = \mathrm{Ok}(t)$, then $\texttt{bind}(\mathrm{Ok}(t), \mathrm{Ok}) = \mathrm{Ok}(t) = m$; if $m = \mathrm{Err}(e)$, then $\texttt{bind}(\mathrm{Err}(e), \mathrm{Ok}) = \mathrm{Err}(e) = m$. Associativity requires case analysis on $m$, $f(m)$; all four cases reduce algebraically via the \texttt{bind} definition.

Law 4 is the CIF-specific invariant that forbids any downstream module from promoting an $\mathrm{Err}$ back to $\mathrm{Ok}$. This property does not hold in arbitrary sum-type monads (e.g., \texttt{Either} in languages where error values can be pattern-matched away), but it is guaranteed in our construction because the \texttt{bind} definition fixes $\mathrm{Err}$ as an absorbing element: no $f$ receives the error value, so no $f$ can transform it. The \texttt{verify\_monad\_laws()} helper in \texttt{src/core/monad.py} checks the three standard monad laws over supplied inputs; detection preservation follows directly from the absorbing-element definition rather than from that helper.
\end{proof}
\label{thm:monadic-laws}

The detection-preservation law is the guarantee that makes monadic composition safe for security use: once a module fires, the detection event propagates to the pipeline caller regardless of what subsequent modules would have computed. Any bypass attack that attempts to suppress an upstream detection by exploiting a downstream module must therefore operate before the detecting module runs, not after.

## Protocol Types for Duck-Typed Composability {#sec:protocol-types}

The monadic pipeline accepts any object that implements a specific call signature. Python's \texttt{Protocol} mechanism \cite{pep544} expresses this via structural subtyping: a class implements a protocol if it has the required methods, regardless of inheritance. This yields zero-overhead composability with existing \texttt{DefenseModule} ABCs:

\begin{lstlisting}[language=Python]
from typing import Protocol
from src.core.base import CognitiveState
from src.core.monad import Ok, Result, DetectionEvent
from src.utils.types import DefenseResult

class DefenseProtocol(Protocol):
    """Any object with this signature is a CIF-compatible defense."""
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

The function \texttt{from\_defense\_result()} in \texttt{src/core/monad.py} lifts an individual \texttt{DefenseResult} into \texttt{Ok} or \texttt{Err}; it does not convert a module object into a \texttt{MonadicDefense}. \texttt{MonadicPipeline} itself accepts duck-typed modules implementing \texttt{evaluate(message, context)}. Existing composition adapters therefore work without subclass modification, while core classes that expose only a different API (for example, \texttt{CognitiveFirewall.classify}) must first be wrapped in an adapter. The separate categorical helper \texttt{lift\_defense\_module()} in \texttt{src/formal/category\_theory.py} is not required by \texttt{MonadicPipeline}.

## Relationship to Existing Architecture {#sec:monadic-vs-series}

\cref{thm:monadic-laws} proves that the monadic pipeline is a formal object with the detection-preservation law baked in. Given the same nonempty ordered module list and input, \texttt{MonadicPipeline} and \texttt{SeriesPipeline} produce the same detection verdict and execute the same prefix of modules: both stop at the first detection. Their return containers and timing fields differ, so this is not a claim of bit-identical results. The value added by the monadic formulation is formal and architectural rather than a different detection rule.

Table: Comparison of pipeline interfaces. Detection verdicts agree for the same nonempty ordered modules; the monadic interface adds the Result abstraction. {#tab:pipeline-comparison}

| Feature | \texttt{SeriesPipeline} | \texttt{MonadicPipeline} |
| --- | --- | --- |
| Detection outcome on input $x$ | identical | identical |
| Error propagation | manual branching | automatic via \texttt{Err} |
| Type of return value | \texttt{PipelineResult} | \texttt{Result[\ldots, DetectionEvent]} |
| Result composition | caller-managed | \texttt{bind} / \texttt{map\_result} |
| Detection-preservation law | operationally satisfied | formally verified (\cref{thm:monadic-laws}) |
| Typical use site | existing code, regression tests | new code, formal analysis |


Existing call sites can continue to use \texttt{SeriesPipeline}; callers wanting the \texttt{Result} interface can use \texttt{MonadicPipeline} with the same ordered adapter instances. No migration is forced by the detection rule. See Supplement S09 (\cref{sec:s09-functional-api}) for the functional API.
