# Local trust-calculus assurance note

The numbered files here describe a bounded, reproducible check of the existing
theory trust module. The [publication inventory](../MANUSCRIPT_STATUS.md) records
the separate source trees for the three-part Cognitive Integrity Program.

Run [the local trust fixture](../verification/README.md) first. Its JSON and
figure are generated inputs for this paper.

## Render the note

Start from a clean checkout in a directory named `cognitive_integrity` so the
validator can locate the combined PDF. Use the
[pinned Template source](https://github.com/docxology/template/tree/87704feae0a4490ef7dad9c931d268e8c30273c2) at
revision `87704feae0a4490ef7dad9c931d268e8c30273c2`.
Install the Template environment and put Pandoc, the matching
pandoc-crossref, XeLaTeX and BibTeX on PATH. From the project root, register
this checkout with Template.

```bash
export PROJECT_ROOT="$(pwd -P)"
export TEMPLATE_ROOT=/path/to/template
git -C "$TEMPLATE_ROOT" rev-parse HEAD
mkdir -p "$TEMPLATE_ROOT/projects/working"
ln -s "$PROJECT_ROOT" "$TEMPLATE_ROOT/projects/working/cognitive_integrity"
cd "$TEMPLATE_ROOT"
uv run --no-sync python scripts/pipeline/stage_03_render.py --project working/cognitive_integrity
uv run --no-sync python scripts/pipeline/stage_04_validate.py --project working/cognitive_integrity
```

The printed Template revision should match the pin above. Inspect
`output/pdf/cognitive_integrity_combined.pdf` and `output/web/index.html`
in the project checkout. Stage 04 writes the validation and provenance
reports under `output/reports/`.
