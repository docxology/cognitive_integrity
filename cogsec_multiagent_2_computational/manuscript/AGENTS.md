Part 2 manuscript source: IMRAD sections + config.yaml + references.bib, with
`figures/` holding the 15 registry figures (PNG+PDF pairs) cited by the prose.
Claim-to-code/evidence mapping: `../docs/claims_traceability.md` and
`src/manuscript/claim_registry.py`. Verify:
`uv run python scripts/verify_manuscript.py --root manuscript` from the part root.