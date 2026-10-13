# Figure reproducibility boundaries

Publication figures retain fixed, reviewed identities in
`output/data/figure_publication_snapshot.json`. Its hashes bind all 26 historical
PNG/PDF files, loaded project Python sources, scientific JSON inputs observed by
the renderer, and the project configuration/lockfile. Fresh provenance records
are compared with that fixed snapshot; tests never refresh the baseline.

Two separate checks apply:

- Historical artifact and source/input hashes must match the reviewed snapshot.
  A changed generator, changed scientific value, changed artifact byte, missing
  file, or new render input fails verification.
- Two fresh renders in the same environment must produce byte-identical PNGs.
  This checks determinism of actual rendering without claiming archival
  regeneration or cross-platform pixel identity.

The distinction is supported by the complete Linux artifact from GitHub Actions
[run 38478766766](https://github.com/docxology/cognitive_integrity/actions/runs/38478766766),
head `d443141b36f18e4b361a046068d8a7c26b77a526`. All 13 Linux PNG encodings differed
from the Darwin references. Ten decoded RGBA images matched exactly; three
contained localized differences of one integer channel level: `attack_surface`
(611 pixels), `detection_performance` (28), and `trust_decay` (18). Matplotlib,
NumPy, Pillow, FreeType and the DejaVu Sans font digest matched; zlib versions
were Darwin 1.2.12 and Linux 1.3.2. These observations establish no cross-platform
byte or pixel identity and define no permitted pixel tolerance. The snapshot
records renderer metadata and the captured Linux PNG hashes for review.

Run the checks from Part 2:

```bash
uv run pytest tests/test_visualization_figures.py -q
```

For a candidate render, use `scripts/generate_all_figures.py --output <temporary-directory>
--provenance <temporary-record.json>`. The record contains relative source/input
paths and hashes, figure names and renderer versions; it does not update the
reviewed snapshot. Changing that snapshot requires review of the inputs,
generator, candidate images and historical artifact identities. Existing
publication PDFs and scientific measurements are preserved by this correction.
