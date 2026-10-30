"""
Phase 06 Part 1A — Build the CLEAN-v3 KUB characterization reviewer notebook.

The notebook imports the reusable module rather than duplicating processing.
All cells are read-only w.r.t. TEST content and manifests.
"""

from __future__ import annotations

import sys
from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

PROJECT_ROOT = Path(r'D:\Softfors\jup')
NB_DIR = PROJECT_ROOT / 'notebooks' / 'phasewise' / 'phase_06_kub_characterization'
NB_PATH = NB_DIR / 'phase06_kub_dataset_characterization_clean_v3.ipynb'

KERNEL = {'display_name': 'jup-venv', 'language': 'python', 'name': 'jup-venv'}

cells = []
md = lambda s: cells.append(new_markdown_cell(s))
code = lambda s: cells.append(new_code_cell(s))

# 1. Title
md("""# Phase 06 — KUB Dataset Characterization (CLEAN-v3)

**Phase ID:** `phase_06_kub_characterization`
**Part:** 1A-R1 — Distribution Interpretation + Stratification + Reviewer-Visualization Repair
**Model:** Gemini 3.8 Flash Medium
**Project Root:** `D:\\Softfors\\jup` · **Kernel:** `jup-venv`

**Active development manifest:** `phase4_v3`
**Historical manifest:** `phase4_v2`

This notebook characterizes the **clean-v3** KUB development population (TRAIN + VAL).
TEST medical content is never accessed.

> **Part 1A-R1 scope.** This is a targeted repair of Part 1A. The computed geometry is
> accepted and unchanged. The repair fixes: (a) an unsupported "descriptively similar"
> TRAIN/VAL claim, (b) missing stratified geometry summaries, (c) table-registry
> consistency, and (d) gallery presentation. **No population, manifest, or split
> membership was changed.**""")

# 2. Scientific question
md("""## 2. Scientific Question

What are the empirical population, patient, anatomical, acquisition, and
image/object-geometry properties of the **clean-v3** KUB development split —
and how stable are they between TRAIN and VAL?

This is a **descriptive characterization**. It does not define a tiny-object
threshold (Phase 07 does), does not train a model, and does not perform
hypothesis testing.""")

# 3. Governance
md("""## 3. CLEAN-v3 Governance

| Rule | Value |
|---|---|
| Medical content used | `manifests/phase4_v3/train.csv`, `manifests/phase4_v3/val.csv` (KUB only) |
| TEST usage | manifest **metadata only** (counts / IDs) |
| TEST content reads | **0** |
| TEST visualizations | **0** |
| TEST metrics | **0** |
| Tiny threshold | **NOT defined here** |
| Training / inference | **NONE** |
| Mask foreground rule | **`mask > 0`** (binary) |

Historical Phase-06 statistics belong to `HISTORICAL_v2` and are shown only for
explicitly-labelled comparison. Primary analysis is recomputed from v3.""")

code("""import importlib, sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
from IPython.display import Image as IPImage, display

PROJECT_ROOT = Path(r'D:\\Softfors\\jup')
CODE_DIR = PROJECT_ROOT / 'notebooks' / 'phasewise' / 'phase_06_kub_characterization' / 'code'
TABLES = PROJECT_ROOT / 'reports' / 'tables'
FIGDIR = PROJECT_ROOT / 'reports' / 'figures' / 'phase06_kub_characterization'
sys.path.insert(0, str(CODE_DIR))
import phase06_kub_characterization as p6

print('python    :', sys.version.split()[0])
print('pandas    :', pd.__version__)
print('numpy     :', np.__version__)
print('module    :', p6.__file__)
print()
print('ACTIVE MANIFEST   :', p6.ACTIVE_MANIFEST_VERSION)
print('HISTORICAL MANIFEST:', p6.HISTORICAL_MANIFEST_VERSION)""")

# 4. Population and provenance
md("""## 4. Population and Provenance

Verify the canonical `phase4_v3` manifest hashes and confirm the KUB counts
match the expected clean-v3 population.""")
code("""hashes = p6.manifest_hashes()
expected = p6.EXPECTED_V3
rows = []
for k, exp in expected.items():
    act = hashes.get(k)
    rows.append({'manifest': f'phase4_v3/{k}.csv', 'expected_sha256': exp,
                 'actual_sha256': act, 'match': act == exp})
prov = pd.DataFrame(rows)
display(prov)
MANIFEST_OK = bool(prov['match'].all())
print('MANIFEST HASHES OK:', MANIFEST_OK)""")

code("""train = p6.load_manifest('train')
val   = p6.load_manifest('val')
test  = p6.load_manifest('test')          # metadata only — never decoded
quar  = p6.load_manifest('quarantined')

ktr, kva, ktest, kq = (p6.kub_only(train), p6.kub_only(val),
                       p6.kub_only(test), p6.kub_only(quar))

counts = {'TRAIN': len(ktr), 'VAL': len(kva), 'TEST': len(ktest), 'QUARANTINED': len(kq)}
gate = pd.DataFrame([
    {'split': 'TRAIN', 'expected': p6.EXPECTED_KUB_COUNTS['TRAIN'], 'actual': counts['TRAIN'],
     'match': counts['TRAIN'] == p6.EXPECTED_KUB_COUNTS['TRAIN']},
    {'split': 'VAL', 'expected': p6.EXPECTED_KUB_COUNTS['VAL'], 'actual': counts['VAL'],
     'match': counts['VAL'] == p6.EXPECTED_KUB_COUNTS['VAL']},
    {'split': 'TEST', 'expected': p6.EXPECTED_KUB_COUNTS['TEST'], 'actual': counts['TEST'],
     'match': counts['TEST'] == p6.EXPECTED_KUB_COUNTS['TEST']},
    {'split': 'QUARANTINED', 'expected': p6.EXPECTED_KUB_COUNTS['QUARANTINED'],
     'actual': counts['QUARANTINED'], 'match': counts['QUARANTINED'] == p6.EXPECTED_KUB_COUNTS['QUARANTINED']},
])
display(gate)
HARD_GATE_OK = bool(gate[gate.split.isin(['TRAIN','VAL'])]['match'].all())
assert HARD_GATE_OK, 'CHECK_REQUIRED: KUB TRAIN/VAL count gate failed'
print('KUB TRAIN/VAL hard gate:', HARD_GATE_OK)""")

# 5. Integrity audit
md("""## 5. Data Integrity Audit

Checked before any characterization: unique IDs, path existence, split
disjointness, patient disjointness, quarantine exclusion, pair readability,
dimension compatibility, and binary mask validity. Nothing is repaired silently.""")
code("""integ = p6.integrity_audit(ktr, kva, kq, ktest, verify_pixels=True)
integ_df = pd.DataFrame([{'gate': k, 'value': v} for k, v in integ.items()
                          if isinstance(v, (bool, int, float, str))])
display(integ_df)
INTEGRITY_OK = integ['all_gates_pass']
print('ALL INTEGRITY GATES PASS:', INTEGRITY_OK)
print('pairs checked:', integ['pairs_checked'])""")

code("""if integ['empty_masks']:
    print('EMPTY MASKS (reported, not removed):', integ['empty_masks'])
    print(integ['empty_mask_ids'])
else:
    print('Empty masks:', integ['empty_masks'])""")

# 6. Patient structure
md("## 6. Patient Structure")
code("""pat_summary = pd.DataFrame([
    p6.population_summary(ktr, 'TRAIN'),
    p6.population_summary(kva, 'VAL'),
])
display(pat_summary)
print('TRAIN unique patients:', ktr.patient_id.nunique())
print('VAL   unique patients:', kva.patient_id.nunique())
print('TRAIN/VAL patient overlap:', integ['train_val_patient_overlap'])""")

# 7. Anatomical metadata
md("""## 7. Anatomical Metadata

> **PIXEL TARGET:** stone/lesion **foreground vs background (binary)**.
> KUB **Kidney / Bladder / Ureteric** are **case-level anatomical metadata**,
> NOT pixel-level multiclass targets.

Raw counts alone obscure proportional differences because TRAIN is far larger
than VAL. Exact **percent-of-split** values and percentage-point differences are
reported below (descriptive only — no significance test).""")
code("""cat_meta = (pd.concat([ktr.assign(split_label='TRAIN'), kva.assign(split_label='VAL')])
            .groupby(['split_label', 'category']).size().unstack(fill_value=0))
display(cat_meta)
print('Categories present:', sorted(set(ktr.category) | set(kva.category)))
print()
cat_pp = p6.percentage_point_differences(
    pd.concat([ktr.assign(split='TRAIN'), kva.assign(split='VAL')], ignore_index=True),
    'category')
display(cat_pp)
MAX_CATEGORY_PP = float(cat_pp['abs_diff_pp'].max())
print(f'MAX CATEGORY DIFFERENCE: {MAX_CATEGORY_PP:.4f} percentage points')""")

# 8. Acquisition / crop metadata
md("""## 8. Acquisition / Crop Metadata

Acquisition type is derived from the on-disk path layout (ROI crop directory vs
full-field `Images` directory). No category is invented; anything unrecognised
would be reported as `UNKNOWN`.""")
code("""acq = pd.concat([ktr.assign(split_label='TRAIN'), kva.assign(split_label='VAL')])
acq['acquisition_type'] = acq['image_path'].map(p6.derive_acquisition_type)
acq_tab = acq.groupby(['split_label', 'acquisition_type']).size().unstack(fill_value=0)
display(acq_tab)
print('Acquisition types:', sorted(acq.acquisition_type.unique()))
print()
acq_pp = p6.percentage_point_differences(acq, 'acquisition_type')
display(acq_pp)
MAX_ACQ_PP = float(acq_pp['abs_diff_pp'].max())
print(f'MAX ACQUISITION DIFFERENCE: {MAX_ACQ_PP:.4f} percentage points')
print()
print('Acquisition composition is comparatively SIMILAR between TRAIN and VAL')
print('(max ~2.1 pp), whereas anatomical-category composition differs much more')
print(f'strongly (max ~{MAX_CATEGORY_PP:.1f} pp).')""")

# 9-13: run the full characterization
md("""## 8b. Full Geometry Characterization (TRAIN + VAL)

The reusable module extracts, for every active KUB pair: image dimensions, mask
foreground area/fraction, connected-component count, largest-component area and
fraction, bounding-box dimensions/area, equivalent diameter, and normalised
centroid. This may take a few minutes over 2,258 pairs.""")
code("""geo_tr = p6.characterize_population(ktr, 'TRAIN')
geo_va = p6.characterize_population(kva, 'VAL')
geo = pd.concat([geo_tr, geo_va], ignore_index=True)
print('characterized:', len(geo), 'pairs')
print('columns:', list(geo.columns))
display(geo.head(3))""")

md("## 9. Native Image Geometry")
code("""series = {'TRAIN': geo_tr, 'VAL': geo_va, 'COMBINED': geo}
img_q = p6.image_geometry_quantile_table(series)
display(img_q)
print('Image modes:', geo.image_mode.value_counts().to_dict())""")

md("""### 9b. Two Distinct Acquisition Regimes

Native geometry is **bimodal by acquisition type**: ROI crops are small and
highly variable; FULL_FIELD images are large and comparatively standardised.
Aggregate quantiles therefore span a very wide range and should always be read
alongside this stratification. The **image mode** also differs by regime
(RGB for FULL_FIELD, single-channel `L` for ROI).""")
code("""regime_df = p6.acquisition_regime_geometry(geo)
p6.write_table(regime_df, 'phase06_kub_v3_acquisition_regime_geometry.csv', TABLES)
display(regime_df)
print('Top native resolutions overall:')
display(p6.resolution_summary(geo).head(10))""")

md("""## 10. Mask / Object Geometry

The pixel target is **binary** (`mask > 0`). KUB masks use a **heterogeneous
nonzero label vocabulary** that is category-correlated; every nonzero value maps
to foreground. This is documented below — it is a data-semantics property, not
corruption.""")
code("""vocab = p6.mask_label_vocabulary(geo[['split', 'category', 'mask_path']])
display(vocab)

import json
print('Mask label vocabulary with counts (from integrity audit):')
print(json.dumps(integ['mask_label_vocabulary'], indent=2))
print('All nonzero labels observed:', integ['mask_label_union'])
print('Foreground semantics:', integ['mask_foreground_semantics'])
print()
print('NOTE: label 255 and labels 1/2/3 are all FOREGROUND under `mask > 0`.')
print('      The binary target is unaffected by which nonzero label is used.')
print('      Labels 1/2/3/255 must NOT be interpreted as multiclass segmentation')
print('      labels, and downstream code must NOT assume `mask == 1`.')""")

md("""> **Downstream governance statement.**
> All CLEAN-v3 KUB segmentation loaders and target-generation code must binarize
> the native mask as **`(mask > 0)`**. Phase 08 infrastructure must unit-test this
> invariant before clean model training.
> *(Phase-08 code is NOT modified in this repair.)*""")

code("""mask_q = p6.mask_geometry_quantile_table(series)
display(mask_q)""")

md("""## 11. Connected-Component Structure

KUB masks are **not assumed** to contain exactly one connected object. The
multi-component rate differs materially between TRAIN and VAL.""")
code("""comp_struct = p6.component_structure_summary(geo)
display(comp_struct)
print('MAX components in a single case:', int(geo.component_count.max()))
print()
mc_tr_n = int((geo_tr.component_count >= 2).sum())
mc_va_n = int((geo_va.component_count >= 2).sum())
MC_TRAIN_PCT = 100.0 * mc_tr_n / len(geo_tr)
MC_VAL_PCT = 100.0 * mc_va_n / len(geo_va)
print(f'TRAIN multi-component: {mc_tr_n}/{len(geo_tr)} = {MC_TRAIN_PCT:.4f}%')
print(f'VAL   multi-component: {mc_va_n}/{len(geo_va)} = {MC_VAL_PCT:.4f}%')
print(f'Difference (VAL - TRAIN): {MC_VAL_PCT - MC_TRAIN_PCT:+.4f} percentage points')
print()
print('This is a DESCRIPTIVE difference requiring stratified reading.')""")

md("""## 12. Continuous Object-Size Distributions

Phase 07 formally defines tiny-object criteria. **No threshold is chosen or
frozen here.** These distributions are empirical evidence for that later
definition.""")
code("""geo_q = p6.geometry_quantile_table(series)
display(geo_q)""")

md("""## 13. TRAIN-vs-VAL Descriptive Differences

TRAIN and VAL are **patient-disjoint** but are **not compositionally identical**.
The differences below are **descriptive** — they are **not** significance tests,
and they do **not** invalidate the split.""")

code("""cat_df = p6.category_summary(geo)
acq_df = p6.acquisition_summary(geo)
display(cat_df)
display(acq_df)
print('Category max |Δ pct-pt| TRAIN vs VAL   :', round(MAX_CATEGORY_PP, 4))
print('Acquisition max |Δ pct-pt| TRAIN vs VAL:', round(MAX_ACQ_PP, 4))
print('Multi-component Δ (VAL - TRAIN)        :', round(MC_VAL_PCT - MC_TRAIN_PCT, 4), 'pp')
print()
print('The clean-v3 TRAIN and VAL populations are patient-disjoint but are not')
print('compositionally identical. Anatomical-category prevalence shows a')
print('material descriptive shift, especially for Bladder/Kidney composition.')
print()
print('This is NOT a statistical significance claim and does NOT invalidate the split.')""")

md("### 13b. Patient Case-Burden and Geometry Differences")
code("""burden_rows = []
for sp, sub in geo.groupby('split'):
    per = sub.groupby('patient_id').size()
    burden_rows.append({
        'split': sp,
        'patients': int(sub.patient_id.nunique()),
        'cases_per_patient_median': float(per.median()),
        'cases_per_patient_max': int(per.max()),
        'cases_per_patient_mean': float(per.mean()),
    })
display(pd.DataFrame(burden_rows))

geom_rows = []
for col in ['fg_fraction', 'largest_component_pixels', 'bbox_area_fraction']:
    geom_rows.append({
        'metric': col,
        'train_median': float(np.median(geo_tr[col])),
        'val_median': float(np.median(geo_va[col])),
        'abs_diff': float(abs(np.median(geo_tr[col]) - np.median(geo_va[col]))),
    })
display(pd.DataFrame(geom_rows))
print('These are descriptive differences requiring stratified reading (see 13c).')""")

md("""### 13c. Stratified Geometry (Mixture-Aware)

Aggregate geometry mixes two very different acquisition regimes, so combined
quantiles are **mixture statistics**. The table below stratifies by
`split × acquisition_type` and `split × anatomical category`.

Descriptive only — **no significance tests**.""")
code("""strat = p6.stratified_geometry_summary(geo)
p6.write_table(strat, 'phase06_kub_v3_stratified_geometry_summary.csv', TABLES)
pd.set_option('display.max_columns', 40)
display(strat[['dimension_a', 'dimension_b', 'n',
               'foreground_fraction_p25', 'foreground_fraction_median', 'foreground_fraction_p75',
               'largest_component_pixels_median', 'bbox_area_fraction_median',
               'equivalent_diameter_median', 'component_count_median']])
STRAT_SHA = p6.sha256_file(TABLES / 'phase06_kub_v3_stratified_geometry_summary.csv')
print('stratified geometry SHA:', STRAT_SHA)""")

md("### 13d. Percentage-Normalized Category Comparison")
code("""fig = p6.plot_category_normalized(geo)
gpath = p6.save_fig(fig, p6.PROJECT_ROOT / 'reports' / 'figures' /
                    'phase06_kub_characterization' / 'phase06_kub_v3_category_normalized.png')
display(IPImage(filename=str(gpath)))
print('Raw counts obscure proportional differences because TRAIN is much larger;')
print('this percentage-normalized view makes the composition shift visible.')
print('No significance stars and no p-values are used.')""")

md("### 13e. Stratified Geometry Figures")
code("""for fname, dim, metric in [
    ('phase06_kub_v3_stratified_acquisition_fg.png', 'acquisition_type', 'fg_fraction'),
    ('phase06_kub_v3_stratified_category_fg.png', 'category', 'fg_fraction'),
]:
    fig = p6.plot_stratified_geometry(geo, dim, metric)
    gp = p6.save_fig(fig, p6.PROJECT_ROOT / 'reports' / 'figures' /
                     'phase06_kub_characterization' / fname)
    display(IPImage(filename=str(gp)))""")

md("## 14. Quarantined KUB Metadata")
code("""qmeta = p6.quarantined_metadata(kq)
display(qmeta)
print('Quarantined KUB cases:', len(qmeta))
print('Reasons:', qmeta['quarantine_reason'].value_counts().to_dict() if 'quarantine_reason' in qmeta else {})
print('Excluded from all active TRAIN/VAL statistics: YES')""")

md("""## 15. Deterministic Sample-Selection Protocol

Selection is **deterministic, documented, prediction-independent, and not
cherry-picked**. It stratifies by (split, category, acquisition), orders by
stable `sample_id`, and adds continuous foreground-fraction quantile-bin
coverage. Size diversity uses **continuous quantiles only** — no tiny label.""")
code("""sel = p6.deterministic_sample_selection(geo, n_total=16)
sel_cols = ['selection_rank', 'sample_id', 'split', 'patient_id', 'category',
            'acquisition_type', 'native_resolution', 'fg_pixels', 'fg_fraction',
            'component_count', 'largest_component_pixels', 'bbox_width', 'bbox_height',
            'bbox_area_fraction', 'equivalent_diameter', 'image_path', 'mask_path']
sel_out = sel[[c for c in sel_cols if c in sel.columns]]
SELECTION_SHA = p6.sha256_of_strings(sel_out['sample_id'].tolist())
display(sel_out.drop(columns=['image_path', 'mask_path']))
print('SAMPLE SELECTION SHA:', SELECTION_SHA)
print('gallery cases:', len(sel_out))
print('split coverage :', sel_out.split.value_counts().to_dict())
print('category cover :', sel_out.category.value_counts().to_dict())
print('acquisition    :', sel_out.acquisition_type.value_counts().to_dict())""")

md("""## 16. Detailed Medical Gallery (deterministic, 16 cases, TRAIN/VAL only)

The gallery uses the **same deterministic 16 sample IDs** as before — no
reselection and no cherry-picking by visual quality.

Each case is shown as **three panels**:
1. original image
2. **binary** ground-truth mask (`mask > 0`) — not the raw heterogeneous labels
3. GT overlay on the original (+ bounding box)

Because 16 × 3 panels would be unreadable as a single postage stamp, the gallery
is paginated into **4 pages × 4 cases**.""")
code("""gal_figs = p6.plot_gallery_pages(
    sel_out, cases_per_page=4,
    title='Phase 06 — KUB clean-v3 deterministic gallery (TRAIN/VAL only)')
GALLERY_PAGES = []
for i, f in enumerate(gal_figs, 1):
    gp = p6.save_fig(f, p6.PROJECT_ROOT / 'reports' / 'figures' /
                     'phase06_kub_characterization' /
                     f'phase06_kub_v3_medical_gallery_page{i:02d}.png')
    GALLERY_PAGES.append(gp)
    display(IPImage(filename=str(gp)))
print('gallery pages:', len(GALLERY_PAGES))
print('cases rendered:', len(sel_out), '(TEST content reads: 0)')
print('each case shows: original + binary GT (mask>0) + GT overlay')""")

# Required figures
md("## 17. Required Characterization Figures")
for fname, caption in [
    ('phase06_kub_v3_population_composition.png', 'Figure 1 — KUB v3 TRAIN/VAL population composition'),
    ('phase06_kub_v3_category_distribution.png', 'Figure 2 — Anatomical-category distribution'),
    ('phase06_kub_v3_acquisition_distribution.png', 'Figure 3 — Acquisition / crop-type distribution'),
    ('phase06_kub_v3_native_resolution.png', 'Figure 4 — Native-resolution distribution'),
    ('phase06_kub_v3_fg_fraction_distribution.png', 'Figure 5 — Foreground-fraction distribution'),
    ('phase06_kub_v3_largest_component_distribution.png', 'Figure 6 — Largest-component / equivalent-size distribution'),
    ('phase06_kub_v3_bbox_size_distribution.png', 'Figure 7 — Bounding-box size distribution'),
    ('phase06_kub_v3_component_count_distribution.png', 'Figure 8 — Component-count distribution'),
    ('phase06_kub_v3_train_val_geometry_comparison.png', 'Figure 9 — TRAIN-vs-VAL geometry comparison'),
]:
    cells.append(new_markdown_cell(f'### {caption}'))
    code(f"""display(IPImage(filename=str(p6.PROJECT_ROOT / 'reports' / 'figures' /
    'phase06_kub_characterization' / '{fname}')))""")

# Interpretation / limitations / conclusion
md("""## 18. Interpretation

- The clean-v3 population and **patient-disjointness are verified**
  (**1978 TRAIN / 280 VAL** cases over **318 / 111** unique patients,
  **zero** TRAIN-VAL patient overlap).
- Native mask labels are **heterogeneous** but cleanly map to **one binary
  foreground target** via `mask > 0`. Any code that assumes `label == 1` is wrong.
- `FULL_FIELD` and `ROI` geometry are **strongly different regimes**
  (median width 2304 vs 83; RGB vs single-channel `L`), so combined quantiles
  are **mixture statistics**.
- **TRAIN and VAL are NOT compositionally identical**, especially in
  anatomical-category proportions (max difference ≈ 19.38 pp: Bladder 32.05% →
  51.43%; Kidney 57.28% → 40.00%). Acquisition composition is comparatively
  similar (max ≈ 2.14 pp). Multi-component rates differ (10.72% → 17.50%).
- Some **aggregate geometry differences may reflect mixture/composition effects**
  and must be interpreted with the stratified summaries (section 13c).
- These facts **do not justify changing the frozen v3 split**.
- They **do affect how Phase 07 defines and evaluates object-size strata**.""")

md("""## 19. Limitations

- Analysis uses **KUB TRAIN/VAL development data only**.
- **TEST medical content remains locked** (0 reads, 0 visualisations, 0 metrics).
- Geometry depends on the available **binary** masks.
- **Kidney / Bladder / Ureteric are metadata**, not multiclass pixel labels.
- The raw mask label vocabulary is heterogeneous; this notebook maps it to binary
  foreground but does **not** reinterpret the labels as a multiclass taxonomy.
- **TRAIN and VAL are patient-disjoint but show anatomical composition
  imbalance.**
- **Combined-development quantiles are mixture statistics across ROI and
  FULL_FIELD regimes.**
- **Phase-07 threshold derivation must avoid VAL-driven threshold tuning.**
- These **descriptive distributions do not themselves define "tiny"**.
- **Phase 07** will define the prospective tiny-object criterion.
- The `NOT_AVAILABLE` case_id column carries no per-case grouping information;
  patient-level grouping is used instead.""")

md("""## 20. Phase-06 Conclusion

The clean-v3 KUB characterization is complete and reproducible. Population,
patient, anatomical, acquisition, and geometry statistics were recomputed
directly from `phase4_v3`. A deterministic 16-case gallery (TRAIN/VAL only,
3 panels per case) is provided. No tiny-object threshold was defined and no
model was trained.""")

md("""## 21. Why Phase 07 Follows — and Its Governance Constraint

Phase 07 (object-size taxonomy) needs a **characterized population** before it
can define a prospective tiny-object criterion. The continuous size
distributions produced here are exactly that input. Phase 07 is **not started**.

> **Phase-07 governance rule (recorded here, not executed).**
> Phase 07 must **NOT** choose a tiny-object threshold by optimizing against VAL.
> The prospective tiny-object definition must be **frozen using TRAIN-only
> empirical geometry and/or predeclared domain/geometric rationale** *before*
> examining VAL prevalence or results under that threshold. VAL may then be used
> for evaluation/characterization after the freeze.
>
> **No actual threshold is defined in this repair.**""")

# Tables + artifacts + TEST lock
md("""## 22. Persist Tables

Tables are (re-)written from the notebook before the registry is computed, so
the registry always reflects the final on-disk bytes and the notebook and driver
agree byte-for-byte.""")
code("""TABLES = p6.PROJECT_ROOT / 'reports' / 'tables'
p6.write_table(pd.DataFrame([p6.population_summary(geo_tr, 'TRAIN'),
                             p6.population_summary(geo_va, 'VAL'),
                             p6.population_summary(geo, 'COMBINED')]),
               'phase06_kub_v3_population_summary.csv', TABLES)
p6.write_table(p6.category_summary(geo), 'phase06_kub_v3_category_summary.csv', TABLES)
p6.write_table(p6.acquisition_summary(geo), 'phase06_kub_v3_acquisition_summary.csv', TABLES)
p6.write_table(geo_q, 'phase06_kub_v3_geometry_quantiles.csv', TABLES)
p6.write_table(img_q, 'phase06_kub_v3_image_geometry_summary.csv', TABLES)
p6.write_table(mask_q, 'phase06_kub_v3_mask_geometry_summary.csv', TABLES)
p6.write_table(qmeta, 'phase06_kub_v3_quarantined_metadata.csv', TABLES)
p6.write_table(sel_out, 'phase06_kub_v3_sample_selection.csv', TABLES)
p6.write_table(strat, 'phase06_kub_v3_stratified_geometry_summary.csv', TABLES)
p6.write_table(p6.acquisition_regime_geometry(geo),
               'phase06_kub_v3_acquisition_regime_geometry.csv', TABLES)
p6.write_table(p6.mask_label_vocabulary(geo[['split', 'category', 'mask_path']]),
               'phase06_kub_v3_mask_label_vocabulary.csv', TABLES)
print('tables persisted (registry size):', len(p6.FINAL_TABLES))""")

md("""## 23. Table Artifacts — Complete Registry

The registry below lists **every final Phase-06 table** with its physical
SHA-256. The physical files are the source of truth: the count is whatever the
disk actually contains (9 original + 3 additional = **12**).""")
code("""tab_df = p6.final_table_registry(TABLES)
pd.set_option('display.max_colwidth', 80)
display(tab_df)
FINAL_TABLE_COUNT = int(tab_df['exists'].sum())
ALL_TABLES_HASHED = bool(tab_df[tab_df['exists']]['sha256'].notna().all())
print('FINAL TABLE COUNT:', FINAL_TABLE_COUNT)
print('ALL TABLES HASHED:', ALL_TABLES_HASHED)
print()
for _, r in tab_df.iterrows():
    print(f"{r['table']:52s} {r['sha256']}")""")

md("## 24. Artifact Hashes")
code("""ledger = {
    'manifest_version': p6.ACTIVE_MANIFEST_VERSION,
    'manifest_hashes': p6.manifest_hashes(),
    'test_sha': p6.TEST_SHA,
    'sample_selection_sha': SELECTION_SHA,
    'mask_foreground_rule': 'mask > 0',
    'mask_label_vocabulary_sha': p6.sha256_file(TABLES / 'phase06_kub_v3_mask_label_vocabulary.csv'),
    'acquisition_regime_sha': p6.sha256_file(TABLES / 'phase06_kub_v3_acquisition_regime_geometry.csv'),
    'stratified_geometry_sha': p6.sha256_file(TABLES / 'phase06_kub_v3_stratified_geometry_summary.csv'),
    'max_category_pp_difference': MAX_CATEGORY_PP,
    'max_acquisition_pp_difference': MAX_ACQ_PP,
    'multi_component_train_pct': MC_TRAIN_PCT,
    'multi_component_val_pct': MC_VAL_PCT,
    'final_table_count': FINAL_TABLE_COUNT,
    'all_tables_hashed': ALL_TABLES_HASHED,
    'geometry_table_sha': p6.dataframe_sha256(geo.drop(columns=['image_path', 'mask_path'])),
    'integrity_all_pass': INTEGRITY_OK,
    'tiny_threshold_defined': False,
    'phase07_started': False,
}
import json
print(json.dumps(ledger, indent=2))""")

md("## 25. TEST-Lock Assertion")
code("""assertion = p6.test_lock_assertion(ktr, kva, ktest, kq)
print('=' * 58)
print('PHASE 06 PART 1A-R1 — TEST-LOCK ASSERTION')
print('=' * 58)
for k, v in assertion.items():
    print(f'{k:32s}: {v}')
print('=' * 58)
print()
print('TINY THRESHOLD DEFINED : NO')
print('PHASE 07 STARTED       : NO')
print('NEXT ACTION            : WAIT_FOR_SUPERVISOR_PHASE06_FINAL_REVIEW')""")

nb = new_notebook(cells=cells, metadata={
    'kernelspec': KERNEL,
    'language_info': {'name': 'python'},
})
nbformat.write(nb, str(NB_PATH))
print('Wrote:', NB_PATH)
print('cells:', len(nb.cells), '| code:', sum(1 for c in nb.cells if c.cell_type == 'code'))
