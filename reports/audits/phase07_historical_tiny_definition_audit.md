# Phase 07 — Historical Tiny-Object Definition Audit

**Generated:** 2026-09-20T04:00:44.761326+00:00  
**Definition found:** True  
**Disagreements between sources:** 0

## Canonical historical definition — `kub_size_v1`

| Field | Value |
|---|---|
| Taxonomy version | `kub_size_v1` |
| Metric | `component_ratio` |
| Metric definition | component_pixels / (native_image_height * native_image_width) |
| Unit | object (connected foreground component) |
| Connectivity | 8 |
| Coordinate system | native image pixels, normalized by native image area |
| Resize convention | NONE for the taxonomy (native masks); the training pipeline separately applies aspect-ratio-preserving resize + centre pad to 512 |
| Acquisition scope | FULL_FIELD only (ROI components were not primary-binned) |
| Source split | TRAIN (phase4_v2) |
| Source components | 1162 |
| Boundary semantics | lower-inclusive / upper-exclusive cumulative: a value exactly equal to a quartile falls into the LOWER bin |
| Case-level convention | per-case flags contains_{tiny,small,medium,large}_object plus dominant_object_stratum from the largest component |

## Thresholds

| Quartile | Value |
|---|---|
| Q25 | 0.0001499766777599 |
| Q50 | 0.00033976472454305 |
| Q75 | 0.0008266496069636999 |

## Bin definitions

| Stratum | Condition |
|---|---|
| TINY | `component_ratio <= Q25` |
| SMALL | `Q25 < component_ratio <= Q50` |
| MEDIUM | `Q50 < component_ratio <= Q75` |
| LARGE | `component_ratio > Q75` |

## Critical question

The historical metric is G: connected-component area normalized by native image area (component_ratio). The "<32 px" hypothesis is NOT supported by any canonical source.

| Hypothesis | Verdict |
|---|---|
| A native pixels | PARTIAL — native pixels, but NORMALIZED by native image area |
| B 512 representation | NO — the taxonomy used native masks; 512 resize+pad is a separate training-pipeline transform |
| C bbox width | NO |
| D bbox height | NO |
| E bbox max side | NO |
| F bbox area | NO (bbox geometry is recorded but not the taxonomy metric) |
| G component area | YES — connected-component area, normalized as a fraction of native image area (component_ratio) |
| H equivalent diameter | NO |
| I foreground fraction | NO (case-level total foreground is separate) |

## Resize convention

- Taxonomy: native resolution, no resize
- Training pipeline: aspect-ratio-preserving resize + centre pad to 512x512 (scale = min(512/w, 512/h); rw=round(w*scale), rh=round(h*scale); bilinear image, nearest mask)
- Non-isotropic resize used: False
- Documented in: `src/data/transforms.py (SegmentationTransform)`

## Historical counts

| Stratum | TRAIN objects |
|---|---|
| TINY | 291 |
| SMALL | 290 |
| MEDIUM | 290 |
| LARGE | 291 |

## Sources

| Source file | SHA-256 | Establishes |
|---|---|---|
| `src/analysis/kub_object_size.py` | `4dbf35d074cfe505f43ed3fe6325557b9cb0da900cdb8402584345ef3e55c58e` | canonical taxonomy module: STRATA, TAXONOMY_VERSION, compute_size_thresholds, stratum_for_ratio, assign_component_strata, assign_sample_strata |
| `src/analysis/kub_characterization.py` | `7726f70dfe2470d23a9e1df7eca5c8fc7a3f884d1a02fb5db9c564474e74f34b` | component extraction: analyze_kub_mask_v2(mask_path, connectivity=8); component_ratio = c_pixels / total_pixels |
| `src/data/transforms.py` | `8a8b636b58843d36810ebf5f3527a8ca1287b93483b962d5cf8e323a92566223` | documented preprocessing: SegmentationTransform — aspect-ratio-preserving resize (scale = min(size/w, size/h)) + centre pad; mask binarized as (> 0) |
| `reports/audits/kub_object_size_thresholds.json` | `20d3ba58fd5d1272aa52c7c6f82a074b1c903d38de8896ad3a78c3af95eb5043` | frozen threshold record (taxonomy_version kub_size_v1, connectivity 8, Q25/Q50/Q75) |
| `reports/audits/kub_object_size_provenance.json` | `024d36495a1062cbc9fd2beb5500a910411997cbe3b47307b90aaac53d34a8b2` | provenance: source split/scope/counts, source table hashes, test_mask_reads 0 |
| `reports/tables/kub_size_thresholds_v2.csv` | `d93ca6cf9ccc64d2f56580236fec8cb3686bed1f51227d7aaa0af51e5f8f9102` | threshold table with boundary definitions |
| `reports/tables/kub_size_distribution_train_val_v2.csv` | `c81f4ef935543f3a3dff33eafb0227b47561897db9da6d9ee0b365e4f1a01f8c` | historical TRAIN/VAL stratum counts |
| `reports/tables/kub_size_distribution_by_category_v2.csv` | `35939755daa39d846e4e7421766363e57280f68461a8c205d154b0bcdb731caa` | historical TRAIN stratum counts by anatomical category |
| `notebooks/05_kub_object_size_taxonomy.ipynb` | `760d62a4d323d2c0f963a8c5c48e3ae3dd7827eff38f966938210d21444e1e13` | historical Phase-07 reviewer notebook |
| `scripts/legacy/run_phase7_analysis.py` | `b8f88fa993062080dfee04fb51e642b0c80a8d8240338336f04891eb24fd75db` | legacy driver: reuses compute_size_thresholds from the canonical module |

## Disagreement report

No competing definition was found. All located sources (module, threshold record, provenance record, threshold table, legacy driver, notebook) implement the same kub_size_v1 quartile taxonomy over FULL_FIELD TRAIN components.
