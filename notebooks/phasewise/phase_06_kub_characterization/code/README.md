# Phase 06 — Code Directory

Reusable implementation for **Phase 06 Part 1A — KUB clean-v3 characterization**.

## Files

### `phase06_kub_characterization.py` (reusable module)
Imported by the reviewer notebook. Provides:

| Area | Functions |
|---|---|
| Provenance | `sha256_file`, `sha256_of_strings`, `dataframe_sha256`, `manifest_hashes` |
| Manifest | `load_manifest`, `kub_only`, `derive_acquisition_type`, `add_derived_columns` |
| Integrity | `integrity_audit` (IDs, paths, disjointness, quarantine exclusion, pair readability, dimension compatibility, binary-mask validity, label vocabulary) |
| Geometry | `extract_geometry`, `characterize_population`, `_component_stats` (scipy label with union-find fallback) |
| Summaries | `population_summary`, `category_summary`, `acquisition_summary`, `resolution_summary`, `component_structure_summary`, `stability_comparison`, `categorical_stability`, `quantile_table`, `mask_label_vocabulary` |
| Stratification | `percentage_point_differences`, `stratified_geometry_summary`, `acquisition_regime_geometry` |
| Shared quantile tables | `image_geometry_quantile_table`, `mask_geometry_quantile_table`, `geometry_quantile_table` (+ canonical metric lists) |
| Selection | `deterministic_sample_selection` |
| Visualization | `save_fig`, `plot_gallery_pages` (paginated 3-panel), `plot_gallery_row`, `plot_category_normalized`, `plot_stratified_geometry` |
| Tables | `write_table`, `REQUIRED_TABLES`, `ADDITIONAL_TABLES`, `FINAL_TABLES`, `final_table_registry` |
| Governance | `test_lock_assertion`, `TEST_CONTENT_READS`, `TEST_VISUALIZATIONS` |

### `run_phase06_characterization.py` (driver)
Runs integrity audit + full geometry characterization for KUB TRAIN/VAL, writes the
required tables, generates the figures, and emits the audit JSON/MD.

```powershell
D:\Softfors\jup\.venv\Scripts\python.exe notebooks/phasewise/phase_06_kub_characterization/code/run_phase06_characterization.py
```

### `build_phase06_notebook.py` / `execute_phase06_notebook.py`
Build the reviewer notebook (unexecuted) and execute it with the `jup-venv` kernel,
then report cell counts, error count, embedded PNG count, and SHA stability.

## Governance guarantees
- Reads KUB medical content from `manifests/phase4_v3/train.csv` / `val.csv` only.
- Never decodes TEST images or masks; TEST is metadata-only.
- Never writes to any manifest.
- Does not define a tiny-object threshold and does not train or infer.

## Notes
- `scipy.ndimage.label` is used for connected components when available; a
  union-find fallback is implemented otherwise.
- Binary foreground semantics: `foreground = (mask > 0)`. The raw label vocabulary
  (`1`/`2`/`3`/`255`) is documented in `phase06_kub_v3_mask_label_vocabulary.csv`.
