# Agent Instructions: CogSec Multiagent — Part 4 (Applications)

This folder is the root of **Part 4: Applications of the Cognitive Integrity Framework** — the fourth manuscript in the *Cognitive Security for Multiagent Operators* series.

**Location:** `projects/cognitive_integrity/cogsec_multiagent_4_applications/`. Use qualified name `cognitive_integrity/cogsec_multiagent_4_applications` for `./run.sh` and `scripts/03_render_pdf.py`.

## Project Position

- **Series:** Cognitive Security for Multiagent Operators (Parts 1–4)
- **Role of Part 4:** Apply CIF across ten critical operational domains via the CIF-AD-OODA integration model; distill universal attack patterns; validate against real-world 2024–2025 AI-agent incidents.
- **Sibling projects:** [`cogsec_multiagent_1_theory/`](../cogsec_multiagent_1_theory/), [`cogsec_multiagent_2_computational/`](../cogsec_multiagent_2_computational/), [`cogsec_multiagent_3_practical/`](../cogsec_multiagent_3_practical/)

## Agent Guidelines

Agents modifying this project must:

- Preserve consistency with Parts 1–3: definitions, notation (`manuscript/S01_notation_reference.md` here; full symbol table in Part 1 `S03_notation.md`), CIF mechanism names, adversary taxonomy (`\Omega_1`–`\Omega_5`), and empirical metrics (use Part 2’s stated headline: **94–100% at the parametric design ceiling** for mature adapters, **~950** attack scenarios, **four** headline production architectures in the main manuscript run—**six** adapter implementations exist in code; not the old “99.5%” figure).
- Keep `references.bib` synced — all four `friedman2026cogsecN` entries (N ∈ {1,2,3,4}) must be present so any cross-paper `\cite` resolves.
- When adding a new domain section, follow the standardized five-step domain analysis template in `manuscript/02_methodology.md`: (i) operational characterization, (ii) attack-surface analysis, (iii) transient coupling analysis, (iv) defense mapping, (v) validation anchoring.
- Ensure every new directory includes a descriptive `README.md` and `AGENTS.md`.
- Use real methods and real data — no mocks.
- Preserve smooth academic tone, avoid duplicate headings, keep `\maketitle` / `\tableofcontents` present where expected.
- Log, test, and document all changes.

## Cross-part citation discipline

BibTeX keys are unchanged; use `\cite{...}` as below.

- Part 1 = `\cite{friedman2026cogsec1}` — formal foundations, theorems, adversary taxonomy, trust calculus
- Part 2 = `\cite{friedman2026cogsec2}` — computational validation, 950-attack corpus, parametric ceiling, ablation studies
- Part 3 = `\cite{friedman2026cogsec3}` — practitioner review, deployment guides, incident response, monitoring
- Part 4 (this part) = `\cite{friedman2026cogsec4}` — CIF-AD-OODA integration, 10-domain analysis, universal attack patterns, incident retrospective

**Do not** describe Part 3 as “biological analogy” or “eusocial” content—that lives in Part 1 supplementary [`S02_eusocial_cogsec.md`](../cogsec_multiagent_1_theory/manuscript/S02_eusocial_cogsec.md). Part 3 is the operator-facing synthesis and deployment material.

## Build commands

From the template repository root:

```bash
./run.sh --render-pdf --project cognitive_integrity/cogsec_multiagent_4_applications
uv run pytest projects/cognitive_integrity/cogsec_multiagent_4_applications/tests/ -v
```
