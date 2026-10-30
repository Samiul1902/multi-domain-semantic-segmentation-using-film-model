# Phase 07 — Code Directory

Reusable implementation for **Phase 07 Part 1A — Historical-definition audit +
CLEAN-v3 TRAIN-only object-size taxonomy design**.

## Files

### `phase07_tiny_definition.py` (reusable module)
Imported by the reviewer notebook. Provides:

| Area | Contents |
|---|---|
| Historical record | `HISTORICAL_TAXONOMY` (`kub_size_v1` constants), `HISTORICAL_SOURCES`, `historical_definition_audit()` |
| Provenance | `sha256_file`, `sha256_of_strings` |
| Manifest | `load_manifest`, `kub_only`, `derive_acquisition_type` |
| Geometry | `model_canvas_scale`, `extract_components`, `build_train_tables` |
| Historical application | `stratum_for_ratio`, `apply_historical_taxonomy` |
| Distributions | `quantile_table`, `stratified_quantiles`, `stratum_counts` |
| Candidates | `build_candidates`, `candidate_assignment`, `candidate_summary` |
| Sensitivity | `boundary_sensitivity` |
| Gallery | `deterministic_gallery_selection`, `gallery_pages`, `save_fig` |
| Registry | `FINAL_TABLES`, `write_table`, `final_table_registry` |
| Governance | `test_lock_assertion` |

### `run_phase07_part1a.py` (driver)
Runs the full Part 1A analysis, writes the 7 tables, 11 figures, and both audit artifacts.

```powershell
D:\Softfors\jup\.venv\Scripts\python.exe notebooks/phasewise/phase_07_tiny_object_definition/code/run_phase07_part1a.py
```

### `build_phase07_notebook.py` / `execute_phase07_notebook.py`
Build the reviewer notebook (unexecuted) and execute it with the `jup-venv` kernel,
reporting cell counts, error count, embedded PNG count, and 3× SHA stability.

## Key conventions

- **Mask semantics:** `foreground = (mask > 0)`. Never assume `mask == 1`.
- **Connectivity:** 8-connectivity (`np.ones((3,3))`) to match the historical
  `kub_size_v1` taxonomy. Note that `scipy.ndimage.label`'s default is 4-connectivity,
  which yields a slightly higher multi-component count (212 vs 210 on clean-v3 TRAIN).
- **512 canvas:** `scale = min(512/w, 512/h)` then aspect-preserving resize + centre pad,
  exactly reproducing `src/data/transforms.py`. This is isotropic scaling, not a stretch.
- **Threshold design population:** KUB TRAIN only. VAL is never used to choose a boundary.

## Governance guarantees
- Reads TRAIN medical content only; TEST is metadata-only.
- Never writes to any manifest.
- Does not freeze a threshold, train a model, or run inference.
