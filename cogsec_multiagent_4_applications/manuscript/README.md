# Manuscript Directory — Part 4: Applications

Markdown source for *Cognitive Integrity in Critical Domains: A Multi-Sector Analysis* — Part 4 of the four-part *Cognitive Security for Multiagent Operators* series.

## Structure

| File | Role |
| ---- | ---- |
| `00_abstract.md` | Abstract + series-map paragraph |
| `01_introduction.md` | Teleological attack surface, Series Context (four-paper map), contributions |
| `02_methodology.md` | CIF-AD-OODA integration model + five-step domain analysis template |
| `03_01_rare_earth_mining.md` — `03_10_fake_news.md` | Ten domain analyses |
| `04_discussion.md` | Cross-domain synthesis, universal attack patterns, BFT-AI connection |
| `05_conclusion.md` | Contribution summary, Relationship to the Series, future work |
| `99_references.md` | Auto-rendered references (from `references.bib`) |
| `S01_notation_reference.md` | Standalone notation reference (anchors to Paper 1) |
| `S02_real_world_incidents.md` | Retrospective analysis of six 2024–2025 AI-agent incidents |
| `config.yaml` | Build configuration + series metadata |
| `preamble.md` | LaTeX preamble for PDF generation |
| `references.bib` | Full bibliography incl. all four `friedman2026cogsecN` entries |

## Cross-Paper Navigation

If this paper references a topic and the reader wants more depth, consult:

| Topic | Where to Go |
| ----- | ---------- |
| Trust Calculus definitions, `\delta^d` decay theorems, Defense Composition Algebra | **Part 1 §3–§5** (`cogsec_multiagent_1_theory`) |
| Adversary taxonomy `\Omega_1`–`\Omega_5` formal definitions | **Part 1 §3** |
| Information-theoretic stealth–impact bounds | **Part 1 §4.3**, Theorem "stealth–impact" |
| Model-checked safety invariants (NuSMV, TLA+ specs) | **Part 1 §7**, **Part 2 S04** |
| 950-attack corpus generation + examples | **Part 2 §3** + **S03** |
| Ablation studies + Bayesian uncertainty | **Part 2 §5.6**, **§5e** |
| Parametric architecture ceiling (94–100%) | **Part 2 S08** |
| Deployment guides, incident response, monitoring | **Part 3 §5–§6** |
| Operator risk frameworks, cost–benefit | **Part 3 §5c–§5d** |
| Eusocial-colony analogy (biological existence proof) | **Part 1 S02** |

## Building

From the template repository root:

```bash
./run.sh --render-pdf --project cognitive_integrity/cogsec_multiagent_4_applications
```
