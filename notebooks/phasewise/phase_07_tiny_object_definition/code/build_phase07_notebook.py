"""
Phase 07 Part 1A — build the reviewer notebook (unexecuted).

Sections follow the task specification (1-21).
"""

from __future__ import annotations

from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

PROJECT_ROOT = Path(r'D:\Softfors\jup')
NB_DIR = PROJECT_ROOT / 'notebooks' / 'phasewise' / 'phase_07_tiny_object_definition'
NB_PATH = NB_DIR / 'phase07_tiny_object_definition_train_only_design.ipynb'

KERNEL = {'display_name': 'jup-venv', 'language': 'python', 'name': 'jup-venv'}

cells = []
md = lambda s: cells.append(new_markdown_cell(s))
code = lambda s: cells.append(new_code_cell(s))

# 1. Title
md("""# Phase 07 — Tiny-Object Definition (Part 1A)

**Phase ID:** `phase_07_tiny_object_definition`
**Part:** 1A — Historical-Definition Audit + CLEAN-v3 **TRAIN-ONLY** Object-Size Taxonomy Design
**Model:** Gemini 3.1 Pro High
**Project Root:** `D:\\Softfors\\jup` · **Kernel:** `jup-venv`

**Active development manifest:** `phase4_v3` · **Historical manifest:** `phase4_v2`

> **This notebook does NOT freeze a threshold.** All taxonomies below are
> **exploratory candidates**. Any recommendation is
> `RECOMMENDED_FOR_SUPERVISOR_REVIEW` only. Final freeze requires Part 1B authorization.""")

# 2. Scientific question
md("""## 2. Scientific Question

1. What exactly did the historical project mean by **Tiny / Small / Medium / Large**?
2. Can that definition be reconstructed with provenance?
3. What is the correct **unit** of analysis — connected component (object) or case?
4. How should the two radically different acquisition regimes (FULL_FIELD vs ROI) be handled?
5. Which **CLEAN-v3 TRAIN-only** candidate taxonomy is most defensible going forward?

Threshold-design evidence is drawn **only** from KUB TRAIN. VAL is evaluation data and is
**not** used to choose any boundary.""")

# 3. Governance
md("""## 3. Governance

| Rule | Value |
|---|---|
| Threshold-design population | `manifests/phase4_v3/train.csv` (KUB TRAIN only) |
| VAL usage | **NOT used for threshold selection** |
| TEST usage | manifest **metadata only** |
| TEST content reads | **0** |
| TEST visualizations | **0** |
| TEST metrics | **0** |
| Threshold frozen | **NO** |
| Training / inference | **NONE** |
| Mask foreground rule | **`mask > 0`** |
| Phase 08 | **NOT started** |

Historical definitions are **not** silently inherited; they are audited and re-applied
explicitly, with the result labelled `HISTORICAL_DEFINITION_APPLIED_TO_CLEAN_v3_TRAIN`.""")

code("""import json, sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
from IPython.display import Image as IPImage, display

PROJECT_ROOT = Path(r'D:\\Softfors\\jup')
CODE_DIR = PROJECT_ROOT / 'notebooks' / 'phasewise' / 'phase_07_tiny_object_definition' / 'code'
TABLES = PROJECT_ROOT / 'reports' / 'tables'
AUDITS = PROJECT_ROOT / 'reports' / 'audits'
FIGDIR = PROJECT_ROOT / 'reports' / 'figures' / 'phase07_tiny_object_definition'
sys.path.insert(0, str(CODE_DIR))
import phase07_tiny_definition as p7

print('python :', sys.version.split()[0])
print('pandas :', pd.__version__)
print('module :', p7.__file__)
print()
print('ACTIVE MANIFEST   :', p7.ACTIVE_MANIFEST_VERSION)
print('HISTORICAL MANIFEST:', p7.HISTORICAL_MANIFEST_VERSION)""")

# 4. Historical-definition audit
md("""## 4. Historical-Definition Audit

The historical taxonomy is reconstructed from project sources — **not from memory**.""")

code("""hist_audit = p7.historical_definition_audit()
print('DEFINITION FOUND:', hist_audit['definition_found'])
print('DISAGREEMENTS   :', len(hist_audit['disagreements']))
print()
display(pd.DataFrame(hist_audit['sources'])[['source_file', 'exists', 'sha256']])
print()
t = p7.HISTORICAL_TAXONOMY
for k in ['taxonomy_version', 'metric', 'metric_definition', 'unit', 'connectivity',
          'coordinate_system', 'acquisition_scope', 'source_split',
          'source_manifest_version', 'source_full_field_component_count',
          'boundary_semantics']:
    print(f'{k:34s}: {t[k]}')
print()
print('THRESHOLDS: Q25=%r  Q50=%r  Q75=%r' % (t['Q25'], t['Q50'], t['Q75']))
for k, v in t['boundaries'].items():
    print(f'  {k:7s}: {v}')""")

md("""### 4b. Critical question — which metric was used?

The historical metric is **connected-component area normalized by native image area**
(`component_ratio`), **not** a raw pixel threshold and **not** a 512-canvas threshold.""")
code("""qa = hist_audit['critical_question_answers']
for k, v in qa.items():
    if k != 'conclusion':
        print(f'{k:26s}: {v}')
print()
print('CONCLUSION:', qa['conclusion'])
print()
print('RESIZE CONVENTION')
for k, v in hist_audit['resize_convention'].items():
    print(f'  {k:28s}: {v}')""")

# 5. Unit of analysis
md("""## 5. Unit of Analysis: Object vs Case

Historical code assigns size to **individual connected components** (8-connectivity).
ROI components were **not** primary-binned (they carried `ROI_NOT_PRIMARY_BINNED`).
A case-level view existed as derived flags (`contains_*_object`) plus
`dominant_object_stratum` from the largest component.

Both representations are preserved here so downstream object-recall work keeps
object-level labels.""")
code("""print('Historical object-level convention :', t['unit'])
print('Historical case-level convention   :', t['case_level_convention'])
print('Historical ROI handling            :', t['roi_handling'])
print()
print('CLEAN-v3 decision: BOTH representations are retained.')
print('  - object-level  -> phase07_kub_v3_train_object_geometry.csv')
print('  - case-level    -> phase07_kub_v3_train_case_size_summary.csv')""")

# 6. CLEAN-v3 TRAIN population
md("## 6. CLEAN-v3 TRAIN Population")
code("""train = p7.load_manifest('train')
test = p7.load_manifest('test')          # metadata only, never decoded
ktr = p7.kub_only(train)
ktest = p7.kub_only(test)
print('KUB TRAIN cases   :', len(ktr), '(expected', p7.EXPECTED_KUB_TRAIN, ')')
print('KUB TRAIN patients:', ktr['patient_id'].nunique())
print('KUB TEST (metadata only):', len(ktest))
assert len(ktr) == p7.EXPECTED_KUB_TRAIN, 'CHECK_REQUIRED: TRAIN count mismatch'
print()
print('HARD GATE PASS: KUB TRAIN == 1978')""")

# 7. Acquisition-regime issue
md("""## 7. The Acquisition-Regime Issue

Phase 06 established that the KUB corpus mixes two strongly different regimes.
Native-pixel thresholds are therefore **not** transferable between them.""")

md("""### 7b. Conceptual strategies

| Option | Description | Advantages | Limitations | Historical compatibility | Downstream compatibility |
|---|---|---|---|---|---|
| **A** | Taxonomy only for FULL_FIELD objects | Matches historical scope exactly; native geometry meaningful | ROI objects left unbinned | **Exact** (this is what history did) | High — historical object recall was FULL_FIELD-only |
| **B** | One normalized metric usable across both regimes | Covers all objects; scale-invariant | ROI denominator is the crop, so the ratio reflects magnification | None (new metric) | Good — still object-level |
| **C** | Separate acquisition-specific taxonomies | Each regime gets a tailored rule | Two rules to maintain; no shared meaning | Partial | Moderate — complicates comparison |

**No option is selected here.** The candidates below operationalise A (C1/C3) and B (C2).""")

# 8. Geometry coordinate systems
md("""## 8. Geometry Coordinate Systems

Objects are measured in three coordinate systems:

1. **native** — pixels in the original image
2. **normalized** — divided by native image dimensions (scale-invariant)
3. **512 model canvas** — the documented historical preprocessing
   (`scale = min(512/w, 512/h)`, aspect-preserving resize + centre pad)""")
code("""print('Documented preprocessing (src/data/transforms.py):')
print('  scale = min(size/width, size/height)')
print('  rw, rh = round(width*scale), round(height*scale)')
print('  bilinear image resize, NEAREST mask resize, centre pad to 512x512')
print()
print('This is ASPECT-RATIO-PRESERVING resize + pad — NOT a non-isotropic stretch.')
print('The 512 projection is therefore a pure isotropic scaling of native geometry.')
print()
print('Mask binarization in that pipeline is already `> 0`, matching Phase-06 semantics.')""")

# 9-10. Tables
md("""## 9. TRAIN Object Table

One row per connected foreground component (8-connectivity), TRAIN only.
This computation opens 1,978 TRAIN masks and may take a few minutes.""")
code("""obj_df, case_df = p7.build_train_tables(ktr)
obj_df = p7.apply_historical_taxonomy(obj_df)
p7.write_table(obj_df, 'phase07_kub_v3_train_object_geometry.csv', TABLES)
print('objects:', len(obj_df))
print('columns:', list(obj_df.columns))
display(obj_df.head(5))""")

md("## 10. TRAIN Case Table")
code("""p7.write_table(case_df, 'phase07_kub_v3_train_case_size_summary.csv', TABLES)
print('cases:', len(case_df))
display(case_df.head(5))
print()
print('multi-component cases:', int((case_df['component_count'] >= 2).sum()),
      '(expected', p7.EXPECTED_MULTI_COMPONENT_TRAIN, ')')""")

# 11. Distributions
md("""## 11. TRAIN Size Distributions (stratified)

Quantiles are reported **stratified by acquisition regime**, and by anatomical
category within FULL_FIELD. Acquisition regimes are never pooled without showing
the stratification.""")
code("""metrics = ['component_ratio', 'component_pixels', 'equivalent_diameter',
           'normalized_equivalent_diameter', 'bbox_max_side', 'bbox_area_fraction',
           'equivalent_diameter_512']
q_df = p7.stratified_quantiles(obj_df, metrics)
p7.write_table(q_df, 'phase07_kub_v3_train_size_quantiles.csv', TABLES)
display(q_df[q_df['metric'] == 'component_ratio'])
print()
display(q_df[q_df['metric'] == 'equivalent_diameter'])""")

code("""for fname, cap in [
    ('phase07_ff_object_size_distribution.png', 'Figure 1 — FULL_FIELD object-size distribution + historical thresholds'),
    ('phase07_roi_object_size_distribution.png', 'Figure 2 — ROI object-size distribution'),
    ('phase07_normalized_size_comparison.png', 'Figure 3 — Scale-invariant size: FULL_FIELD vs ROI'),
]:
    display(IPImage(filename=str(FIGDIR / fname)))""")

# 12. Historical on clean-v3
md("""## 12. Historical Definition Applied to CLEAN-v3 TRAIN

Result label: `HISTORICAL_DEFINITION_APPLIED_TO_CLEAN_v3_TRAIN`.""")
code("""ff = obj_df[obj_df['acquisition_type'] == 'FULL_FIELD']
counts = ff['historical_stratum'].value_counts().reindex(list(p7.STRATA), fill_value=0)
n = int(counts.sum())
hist_summary = pd.DataFrame({
    'stratum': list(p7.STRATA),
    'objects': [int(counts[s]) for s in p7.STRATA],
    'prevalence_pct': [100.0 * counts[s] / n for s in p7.STRATA],
})
display(hist_summary)
print('FULL_FIELD objects:', n)
print('label: HISTORICAL_DEFINITION_APPLIED_TO_CLEAN_v3_TRAIN')
print()
print('By category (FULL_FIELD):')
display(pd.crosstab(ff['category'], ff['historical_stratum'])[list(p7.STRATA)])
print()
print('NOTE: no VAL prevalence is computed here (VAL is evaluation data only).')""")

# 13. Candidates
md("""## 13. Candidate Taxonomy Designs

All candidates are **exploratory**. All cut points are derived from
**TRAIN FULL_FIELD objects only**, matching the historical source population.
**No VAL data is used.**""")
code("""candidates = p7.build_candidates(obj_df)
cand_sum = p7.candidate_summary(obj_df, candidates)
for c in candidates:
    print('=' * 68)
    print(c['candidate_id'], '—', c['name'])
    print('  metric       :', c['metric'])
    print('  definition   :', c['metric_definition'])
    print('  unit         :', c['unit'])
    print('  coords       :', c['coordinate_system'])
    print('  acquisition  :', c['acquisition_applicability'])
    print('  cuts         :', [f'{v:.6g}' for v in c['cut_values']])
    for k, v in c['boundaries'].items():
        print(f'    {k:7s}: {v}')
    print('  advantages   :', c['advantages'][0])
    print('  limitations  :', c['limitations'][0])
    print('  historical   :', c['historical_compatibility'])""")

code("""display(cand_sum[cand_sum['scope'] == 'FULL_FIELD'].pivot_table(
    index='candidate_id', columns='stratum', values='objects', aggfunc='sum'))""")

md("""### 13b. Cross-regime behaviour (critical caveat)

All candidates are calibrated on **FULL_FIELD** objects. Applying them to ROI crops is a
separate question, because an ROI crop *magnifies* its object: the object's share of the
**crop** is not comparable to an object's share of a **whole radiograph**.""")
code("""piv = cand_sum.pivot_table(index=['candidate_id', 'scope'], columns='stratum',
                          values='objects', aggfunc='sum')
display(piv)
print()
roi_share = {}
for c in candidates:
    sub = cand_sum[(cand_sum['candidate_id'] == c['candidate_id']) &
                   (cand_sum['scope'] == 'ROI')]
    if sub.empty:
        continue
    tot = float(sub['objects'].sum())
    if tot == 0:
        roi_share[c['candidate_id']] = 'no applicable ROI objects (FULL_FIELD-only rule)'
        continue
    roi_share[c['candidate_id']] = {
        s: round(100.0 * float(sub[sub['stratum'] == s]['objects'].iloc[0]) / tot, 2)
        for s in p7.STRATA}
print('ROI objects classified as LARGE when a FULL_FIELD-calibrated rule is applied:')
for k, v in roi_share.items():
    if isinstance(v, dict):
        print(f'  {k:38s} LARGE={v["LARGE"]:6.2f}%  TINY={v["TINY"]:6.2f}%')
    else:
        print(f'  {k:38s} {v}')
print()
print('INTERPRETATION: because ROI crops magnify their object, a FULL_FIELD-calibrated')
print('normalized rule pushes most ROI objects into LARGE. This means C2 is NOT')
print('automatically well-calibrated across regimes merely because its metric is')
print('scale-invariant; a cross-regime rule would need its own ROI-specific calibration')
print('(Option C) or the taxonomy should stay FULL_FIELD-scoped (Option A).')
print()
print('This strengthens Options A/C and weakens the naive reading of Option B.')""")

# 14. Boundary sensitivity
md("""## 14. Boundary Sensitivity (TRAIN only)

For each cut, counts immediately either side show whether the boundary sits in a
dense pile-up where small measurement variation would flip many labels.""")
code("""sens_df = p7.boundary_sensitivity(obj_df, candidates)
p7.write_table(sens_df, 'phase07_candidate_boundary_sensitivity.csv', TABLES)
cols = ['candidate_id', 'metric', 'boundary', 'cut_value', 'delta_kind',
        'within_minus_1', 'within_plus_1', 'within_minus_2', 'within_plus_2',
        'pileup_frac_1', 'pileup_frac_2']
display(sens_df[cols])""")

# 15. Multi-component
md("""## 15. Multi-Component Implications

Multi-component masks are **not** collapsed. Each component receives its own size
class; case-level views are derived separately.

**Connectivity matters.** The historical taxonomy used **8-connectivity**
(`np.ones((3,3))`). Phase 06 used `scipy.ndimage.label`'s default, which is
**4-connectivity**. Diagonally touching regions merge under 8-connectivity, so the
multi-component case count differs slightly between the two conventions.""")
code("""multi = case_df[case_df['component_count'] >= 2]
print('multi-component TRAIN cases (8-connectivity, historical convention):', len(multi))
print('Phase-06 reference count (4-connectivity, scipy default)           :',
      p7.EXPECTED_MULTI_COMPONENT_TRAIN)
print()
print('Both are correct for their own convention: 4-connectivity splits diagonally')
print('touching regions into separate components; 8-connectivity merges them.')
print('Phase 07 adopts 8-connectivity to match the historical taxonomy exactly.')
print()
print('max components in a case   :', int(case_df['component_count'].max()))
print('Objects contributed by multi-component cases:',
      int(obj_df[obj_df['sample_id'].isin(multi['sample_id'])].shape[0]))
print()
print('Case-level rules that COULD be defined (none chosen here):')
for rule in ['largest-component class', 'smallest-component class',
             'any-tiny component', 'dominant (largest) component']:
    print('  -', rule)
print()
print('For downstream object recall, object-level labels remain authoritative.')""")

# 16. Gallery
md("""## 16. Deterministic TRAIN Gallery

Deterministic, prediction-independent selection across acquisition regimes,
anatomical categories and size regions, including objects near candidate
boundaries. **All candidate labels shown are NOT FROZEN.**""")
code("""sel = p7.deterministic_gallery_selection(obj_df, case_df, n_total=16)
def _lab(row):
    parts = []
    for c in candidates:
        v = row[c['metric']]; cuts = c['cut_values']
        lab = ('TINY' if v <= cuts[0] else 'SMALL' if v <= cuts[1]
               else 'MEDIUM' if v <= cuts[2] else 'LARGE')
        parts.append(f"{c['candidate_id'].split('_')[0]}={lab}")
    return 'NOT FROZEN | ' + ' '.join(parts)
sel['candidate_labels'] = sel.apply(_lab, axis=1)
p7.write_table(sel, 'phase07_train_gallery_selection.csv', TABLES)
SELECTION_SHA = p7.sha256_of_strings(
    (sel['sample_id'] + '#' + sel['component_index'].astype(str)).tolist())
display(sel[['selection_rank', 'sample_id', 'category', 'acquisition_type',
             'component_index', 'component_pixels', 'component_ratio',
             'equivalent_diameter', 'candidate_labels']])
print('gallery cases:', len(sel))
print('selection SHA:', SELECTION_SHA)""")

code("""gal = p7.gallery_pages(sel, obj_df, cases_per_page=4,
                       title='Phase 07 TRAIN object-size gallery')
for i, f in enumerate(gal, 1):
    gp = p7.save_fig(f, FIGDIR / f'phase07_train_gallery_page{i:02d}.png')
    display(IPImage(filename=str(gp)))
print('pages:', len(gal), '| each case shows original + binary GT + selected component')""")

# 17. Comparison matrix
md("## 17. Candidate Comparison Matrix")
code("""rows = []
for c in candidates:
    for scope in ('ALL_TRAIN', 'FULL_FIELD', 'ROI'):
        sub = cand_sum[(cand_sum['candidate_id'] == c['candidate_id']) &
                       (cand_sum['scope'] == scope)]
        if sub.empty:
            continue
        rec = {'candidate': c['candidate_id'], 'metric': c['metric'], 'scope': scope,
               'applicable_objects': int(sub['applicable_objects'].iloc[0])}
        for s in p7.STRATA:
            r = sub[sub['stratum'] == s]
            rec[f'{s.lower()}_objects'] = int(r['objects'].iloc[0]) if len(r) else 0
            rec[f'{s.lower()}_pct'] = float(r['prevalence_pct'].iloc[0]) if len(r) else 0.0
        rows.append(rec)
cmp_df = pd.DataFrame(rows)
display(cmp_df[cmp_df['scope'] == 'FULL_FIELD'])""")

code("""display(IPImage(filename=str(FIGDIR / 'phase07_candidate_threshold_overlays.png')))
display(IPImage(filename=str(FIGDIR / 'phase07_candidate_taxonomy_prevalence.png')))
display(IPImage(filename=str(FIGDIR / 'phase07_object_vs_case_comparison.png')))
display(IPImage(filename=str(FIGDIR / 'phase07_category_stratified_ff_size.png')))""")

# 18. Recommendation
md("""## 18. Scientific Recommendation to Supervisor

**Status: `RECOMMENDED_FOR_SUPERVISOR_REVIEW`** — not final, not frozen, not canonical.""")
code("""rec = {
    'status': 'RECOMMENDED_FOR_SUPERVISOR_REVIEW',
    'candidate_id': 'C1_HISTORICAL_kub_size_v1',
    'rationale': [
        'Exact historical continuity: identical metric, unit, connectivity, coordinate system and boundaries',
        'Already native-scale-normalized (component area / native image area)',
        'Downstream object-recall work in Phases 10-14 was built on these labels',
        'Boundaries are transparent TRAIN-only quartiles',
    ],
    'alternatives': {
        'C2_NORMALIZED_EQ_DIAMETER': 'Prefer if ROI coverage is required; the only candidate '
                                     'that is meaningfully comparable across both regimes.',
        'C3_FULLFIELD_NATIVE_EQ_DIAMETER_PX': 'Prefer if reviewers need the most human-readable '
                                              'unit (pixels); FULL_FIELD-only by construction.',
    },
    'explicitly_not_used': [
        'VAL prevalence', 'VAL sample counts', 'model performance on VAL',
        'recall/Dice on VAL', 'statistical power on VAL',
    ],
}
print(json.dumps(rec, indent=2))""")

# 19. Limitations
md("""## 19. Limitations

- Threshold design uses **KUB TRAIN only**; VAL is deliberately unused here.
- **TEST medical content remains locked** (0 reads, 0 visualisations, 0 metrics).
- The historical cut values were derived on **phase4_v2** FULL_FIELD TRAIN components
  (contaminated-era membership); re-deriving them on clean-v3 would change the numbers.
- Aggregate geometry mixes two acquisition regimes and is a **mixture statistic**.
- Candidate labels are **exploratory** and must not be treated as canonical.
- Quartile-based binning guarantees ~25% per bin **on the derivation population**; it is
  not an absolute geometric criterion.
- No literature claim is made: no external sources were consulted.""")

# 20. Decision required
md("""## 20. Decision Required Before Freeze

The supervisor must decide:

1. **Unit**: confirm object-level (recommended) and whether a case-level rule is needed.
2. **Candidate**: C1 (historical continuity), C2 (cross-regime), or C3 (interpretable pixels).
3. **Acquisition scope**: Option A (FULL_FIELD only), B (normalized, both), or C (separate).
4. **Boundary freeze**: authorise Part 1B to freeze the chosen cut values.
5. **VAL role**: confirm VAL stays evaluation-only after the freeze.

**Nothing is frozen by this notebook.**""")

# 21. Hashes
md("## 21. Artifact Hashes")
code("""ledger = {
    'manifest_version': p7.ACTIVE_MANIFEST_VERSION,
    'manifest_hashes': {k: p7.sha256_file(p7.MANIFEST_DIR / f'{k}.csv')
                        for k in ('train', 'val', 'test', 'quarantined')},
    'historical_definition_sources': {
        s['source_file']: s['sha256'] for s in hist_audit['sources']},
    'train_objects': int(len(obj_df)),
    'train_cases': int(len(case_df)),
    'gallery_selection_sha': SELECTION_SHA,
    'candidates': {c['candidate_id']: c['cut_values'] for c in candidates},
    'threshold_frozen': False,
    'val_used_for_threshold_selection': False,
}
print(json.dumps(ledger, indent=2))
print()
reg = p7.final_table_registry(TABLES)
display(reg)
print('FINAL TABLE COUNT:', int(reg['exists'].sum()))""")

code("""assertion = p7.test_lock_assertion(ktr, ktest, obj_df)
print('=' * 62)
print('PHASE 07 PART 1A — GOVERNANCE ASSERTION')
print('=' * 62)
for k, v in assertion.items():
    print(f'{k:38s}: {v}')
print('=' * 62)""")

nb = new_notebook(cells=cells, metadata={
    'kernelspec': KERNEL,
    'language_info': {'name': 'python'},
})
nbformat.write(nb, str(NB_PATH))
print('Wrote:', NB_PATH)
print('cells:', len(nb.cells), '| code:', sum(1 for c in nb.cells if c.cell_type == 'code'))
