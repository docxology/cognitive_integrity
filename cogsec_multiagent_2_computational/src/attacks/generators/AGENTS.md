# src/attacks/generators/ — Agent Notes

Attack-generator modules producing the corpus attack types
(`src/attacks/corpus.py` consumes these):

- `injection.py` — prompt/content injection generators
- `belief_manipulation.py` — belief-manipulation attacks
- `trust_exploitation.py` — trust-chain exploits
- `coordination.py` — multiagent coordination attacks
- `provenance_and_isolation.py` — provenance/isolation attacks

No mocks: generators produce real corpora items validated by
`src/attacks/validation.py`. Part of the 1,475-item attack corpus pipeline
(DOI 10.5281/zenodo.22134546).
