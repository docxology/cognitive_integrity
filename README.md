# Cognitive Security for Multiagent Operators

A tripartite manuscript series establishing the theoretical foundations, computational validation, and practical deployment guidance for cognitive security in multiagent AI systems.

## Paper Series

| Part | Title | Status | DOI |
|------|-------|--------|-----|
| 1 | [Formal Foundations](cogsec_multiagent_1_theory/) | **Published** | [10.5281/zenodo.18364119](https://doi.org/10.5281/zenodo.18364119) |
| 2 | [Computational Validation](cogsec_multiagent_2_computational/) | Preprint | [10.5281/zenodo.18364128](https://doi.org/10.5281/zenodo.18364128) |
| 3 | [Practical Guidance](cogsec_multiagent_3_practical/) | Preprint | [10.5281/zenodo.18364130](https://doi.org/10.5281/zenodo.18364130) |

## Author

**Daniel Ari Friedman**
Active Inference Institute

## Key Contributions

- **Trust Calculus** with bounded delegation and δ^d decay (Paper 1)
- **Defense Composition Algebra** for layered security reasoning (Paper 1)
- **Computational Validation** across 950 attacks and 4 production architectures (Paper 2)
- **Actionable Deployment Framework** with checklists, guidelines, and risk assessment (Paper 3)

## Documentation

Comprehensive technical documentation for the CIF codebase is available in [`cogsec_multiagent_2_computational/docs/`](cogsec_multiagent_2_computational/docs/):

- [Claims Traceability](cogsec_multiagent_2_computational/docs/claims_traceability.md) — Manuscript-to-code mapping
- [Usage Guides](cogsec_multiagent_2_computational/docs/usage_guides/) — Per-component guides (Firewall, Sandbox, Trust, Consensus, Tripwires, Drift Detection, Provenance, Invariants)
- [Framework Validation](cogsec_multiagent_2_computational/docs/framework_validation.md) — Experiment reproduction guide

## Citation

```bibtex
@article{friedman2026cogsec,
  author = {Friedman, Daniel Ari},
  title = {Cognitive Security for Multiagent Operators: A Tripartite Framework},
  year = {2026},
  doi = {10.5281/zenodo.18364119},
  publisher = {Zenodo}
}
```

## Repository

- **GitHub**: [docxology/cognitive_integrity](https://github.com/docxology/cognitive_integrity)
- **Template**: [docxology/template](https://github.com/docxology/template)

## Building

```bash
# Render any paper as PDF
./run.sh --render-pdf --project cogsec_multiagent_1_theory
./run.sh --render-pdf --project cogsec_multiagent_2_computational
./run.sh --render-pdf --project cogsec_multiagent_3_practical

# Run tests (Papers 2 & 3)
python3 -m pytest projects/cognitive_integrity/cogsec_multiagent_2_computational/tests/ -v
python3 -m pytest projects/cognitive_integrity/cogsec_multiagent_3_practical/tests/ -v
```

## License

This work is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
