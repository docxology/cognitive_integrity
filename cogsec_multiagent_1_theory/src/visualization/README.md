# src/visualization/

Figure modules for Part 1 of the CIF series — trust calculus, defense
mechanisms, detection performance, threat taxonomy, and composite CIF
diagrams. Regenerate all figures with
`uv run python scripts/generate_all_figures.py` from the part root.

## Required result-figure inputs

Do not regenerate protected producer evidence to satisfy missing inputs.
The numbered detection/scalability entry points propagate exceptions and exit
nonzero; the batch entry point reports those failures. They never return an
`error.pdf` or make fallback measurements.

- `create_detection_results_figure(output_dir)` requires **all three** files in
  `output_dir/data`: `detection_results.json`, `ablation_study.json`, and
  `integrity_timeseries.csv`. It saves PNG and PDF and returns the PDF path.
  Detection requires unique named configurations `Baseline`, `Firewall Only`,
  and `Full CIF`, each with numeric `prompt_injection` and `trust_exploitation`
  detection rates and `latency_overhead_pct`. Additional rates used in the
  trade-off mean must also be numeric. Rates/integrity are finite numbers in
  `[0, 1]`; model latency is finite and nonnegative. Booleans and JSON numeric
  strings are not numeric evidence.
- Ablation requires `full_cif`, `minus_firewall`, `minus_sandbox`,
  `minus_tripwires`, `minus_invariants`, and `minus_trust_decay`, each with a
  numeric `detection`; deltas are computed from those supplied values.
  Integrity CSV requires `attack_attempt`, `baseline_integrity`,
  `firewall_integrity`, `full_cif_integrity`, and at least one complete numeric
  row. Attempts are nonnegative, strictly increasing integers.
- The detection figure is intentionally mixed: panel A uses corpus detection
  inputs; panels B/C are visibly **illustrative, not measured**; panel D uses
  artifact detection rates against **model latency, not measured**. The shipped
  producer's illustrative ablation/integrity/model inputs are not empirical
  evidence, even when every file exists.
- `create_scalability_figure(output_dir)` requires a nonempty JSON record list
  in `output_dir/data/scalability_results.json`. Each record must supply numeric
  `agent_count`, `detection_time_ms`, `memory_mb`, and `consensus_latency_ms`.
  Agent counts are positive, strictly increasing integers; other values are
  finite and nonnegative. It returns `(png_path, pdf_path)`. All panels and
  theoretical guides are labelled analytic/non-measured; the consensus fit is
  a fit to those same inputs, not independent evidence.

Missing files raise `FileNotFoundError`; malformed schemas/CSV/JSON or invalid
numeric fields raise descriptive `ValueError` identifying the artifact/field.
All inputs are checked **before** allocating a figure or writing an output
image; existing evidence/images are not deleted or replaced on input failure.
Schematic-only figures such as `create_ablation_study_figure` and
`create_detection_performance_figure` remain separate, visibly labelled paths;
their values must not be used as measured evidence.
