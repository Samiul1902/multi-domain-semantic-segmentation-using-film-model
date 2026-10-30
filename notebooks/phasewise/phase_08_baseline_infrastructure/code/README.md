# Phase 08 — Code Directory

Audit and validation tooling for **Phase 08 Part 1A — clean-v3 data / target /
device / reproducibility foundation**.

Production functionality lives under `src/`; this directory only audits and
validates it.

## Files

### `phase08_infrastructure_audit.py` (reusable module)
Imported by the reviewer notebook. Provides:

| Area | Functions |
|---|---|
| Provenance | `sha256_file`, `sha256_of_strings` |
| Manifest | `verify_manifests` (explicit `phase4_v3` guard + KUB counts) |
| Target | `audit_target_contract` (category-stratified label vocabulary + binarization equivalence) |
| Image modes | `audit_image_modes` (source mode vs tensor channels) |
| Transform | `audit_transform_contract` (scale, padding, alignment, mask binarity) |
| Metrics | `audit_metric_contract` (dice/iou/precision/recall/hd95/object_recall conventions) |
| Reproducibility | `audit_reproducibility` (python/numpy/torch/cuda/worker/generator/RNG) |
| Checkpoint | `audit_checkpoint_contract` (required fields + functional round-trip) |
| Sampling | `deterministic_sample_selection` (stratified + label-signature coverage) |
| Loader audit | `audit_loader_samples` |
| Gallery | `loader_gallery_pages`, `save_fig` |
| Smoke test | `cuda_smoke_test` (`INFRASTRUCTURE_TEST_ONLY`) |
| Taxonomy | `audit_taxonomy_integration` (versioned API, ROI not binned) |
| Tables | `write_table`, `FINAL_TABLES`, `final_table_registry` |

### `run_phase08_audit.py` (driver)
Runs the full Part 1A audit, writes the 5 tables and the loader gallery, and emits
the audit JSON/MD.

```powershell
D:\Softfors\jup\.venv\Scripts\python.exe notebooks/phasewise/phase_08_baseline_infrastructure/code/run_phase08_audit.py
```

### `build_phase08_notebook.py` / `execute_phase08_notebook.py` / `finalize_phase08_audit.py`
Build the reviewer notebook (unexecuted), execute it with the `jup-venv` kernel and
report stats + 3× SHA stability, then merge notebook/test/immutability results into
the audit.

## Canonical helpers this phase added to `src/`

| File | Purpose |
|---|---|
| `src/utils/targets.py` | `binarize_mask()` — authoritative `mask > 0` conversion |
| `src/utils/device.py` | `get_device(require_cuda=True)`, `device_report()`, `make_grad_scaler()`, `make_autocast()` |
| `src/utils/config.py` | canonical experiment schema + validation (rejects placeholders) |
| `src/utils/checkpointing.py` | additive `taxonomy_id` |
| `src/data/kub_dataset.py` | uses `binarize_mask`; exposes `acquisition_type` |

## Notes

- `SegmentationTransform` accepts **only** sizes {256, 512, 768, 1024}.
- TRAIN access is stochastic by design (augmentation); seed for reproducibility.
- The CUDA smoke test is an engineering check, not a scientific result.
- Tests: `tests/test_phase08_infrastructure.py`.
