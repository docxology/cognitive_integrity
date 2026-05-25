# Agent Instructions: Manuscript (Part 4)

Agents manipulating the Part 4 manuscript should:

## Writing

- Ensure smooth transitions and academic tone.
- Avoid duplicate headings.
- Make sure `\maketitle` and `\tableofcontents` are present where the document should build the title page.
- Keep references synced in `references.bib` — all four `friedman2026cogsecN` entries (N ∈ {1,2,3,4}) must be present.

## Series Consistency

This manuscript is **Part 4 of a four-part series**. Every cross-paper claim should cite via `\cite{friedman2026cogsecN}`:

- `friedman2026cogsec1` — Formal foundations (trust calculus, defense composition algebra, adversary taxonomy `\Omega_1`–`\Omega_5`, information-theoretic bounds, model-checked invariants)
- `friedman2026cogsec2` — Computational validation (950 attacks, 4 architectures, ablation studies, Bayesian uncertainty, parametric ceiling)
- `friedman2026cogsec3` — **Qualitative review / practitioner's deployment guide** (NOT "biological analogy" or "eusocial" — that's Paper 1's S02 supplementary)
- `friedman2026cogsec4` — this paper (CIF-AD-OODA, ten-domain analysis, universal attack patterns, incident retrospective)

## Empirical Claims

When citing Paper 2's headline results, use the accurate figure: **94–100% detection at the parametric design ceiling across 950 attack scenarios and four production architectures**. Do NOT use the outdated "99.5% detection" phrasing; it does not reflect Paper 2's current reported metrics.

## Five-Step Domain Analysis Template

Each of the ten domain sections (`03_01_*` through `03_10_*`) must follow the standardized template from `02_methodology.md`:

1. **Operational Characterization** — agents, FRs, DPs, uncoupled Design Matrix `[A]`
2. **Attack Surface Analysis** — Goal Hijacking vector, adversary class, OODA phase, universal pattern (FR Polarity Inversion / Constraint Relaxation / Context Boundary Violation)
3. **Transient Coupling Analysis** — transformation from `[A]` to coupled `[A']`
4. **Defense Mapping** — canonical CIF mechanisms + any domain-specific novel extensions
5. **Validation Anchoring** — cross-reference to Paper 2 benchmarks, and where appropriate to Paper 3 operator guidance
