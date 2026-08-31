# scripts/ — Agent Notes

Program-level thin orchestrators (stdlib-only where possible). Business logic
lives in each part's `src/`; these scripts operate across the three parts.

| Script | Role |
| ------ | ---- |
| `check_series_integrity.py` | Program-level gate: shared quantities consistent across papers, cross-paper pointers valid |
| `check_conclusion_numbers.py` | Conclusion numbers traceable to artifacts |
| `check_publication_identity.py` | Publication metadata consistency |
| `check_unhappened_claims.py` | Claims that reference non-existent events |
| `collect_test_inventory.py` | Test inventory collection |
| `deposit_zenodo.py` | Zenodo deposit helper |
| `inject_series_values.py` | Inject shared series values into manuscripts |
| `propagate_dois.py` | Propagate DOIs across the series |
| `prune_bibliography.py` | Bibliography pruning |
| `series_ledger.py` | Shared series ledger |

## Verify

```bash
python3 scripts/check_series_integrity.py   # from repo root; stdlib-only
uv run pytest tests/ -q                      # tests cover these gates
```
