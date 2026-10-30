"""Build Phase 12 Part 1B — four-model oracle inference reviewer notebook."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(r'D:\Softfors\jup')))
import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

nb = new_notebook()
nb.metadata['kernelspec'] = {'display_name': 'jup-venv', 'language': 'python', 'name': 'jup-venv'}
nb.metadata['language_info'] = {'name': 'python', 'version': '3.13.12'}
def md(t): nb.cells.append(new_markdown_cell(t))
def co(t): nb.cells.append(new_code_cell(t))

md("""# Phase 12 Part 1B — CLEAN-v3 Four-Model Oracle Regional Inference

**Model:** Gemini 3.8 Flash Medium · **Date:** 2026-09-21
**Manifest:** `phase4_v3` · **Taxonomy:** `kub_size_clean_v3_v1`
**Strategy:** SR-1 (Regional-Aware Multi-Domain FiLM)

---

> **RAW EVIDENCE GENERATION.** Implements the **supervisor-frozen** clean-v3 oracle protocol
> and produces raw four-model oracle evidence.
>
> No training · no optimizer · no checkpoint writes · no config/manifest changes ·
> no margin or threshold tuning · no model selection · no significance testing ·
> no TEST access · Phase 13 not started · RA-MedFiLM not implemented.
>
> **No final Phase-12 mechanism conclusion is issued here.** Part 1B is evidence only.
>
> The inference itself was executed by `code/phase12_oracle_inference.py`; this notebook
> loads the resulting frozen tables (read-only) so Run-All is fast and deterministic.
""")

md("""## 2. Scope / Governance

| Rule | Status |
|---|---|
| Training epochs / optimizer steps | **0 / 0** |
| Checkpoint / config / manifest changes | **0** |
| Margin tuning | **NONE** (fixed 0.25) |
| Threshold tuning | **NONE** (fixed 0.5) |
| Reference model / winner selected | **NO** |
| Unauthorized fusion variants | **0** |
| Statistical testing | **NONE** |
| TEST reads | **0** |
| Phase 13 / Phases 14–18 | **NOT STARTED** |
| RA-MedFiLM implemented | **NO** |
""")

co("""import sys, json
from pathlib import Path
import numpy as np, pandas as pd
pd.set_option('display.max_rows', None); pd.set_option('display.max_columns', None)
pd.set_option('display.width', None); pd.set_option('display.max_colwidth', None)

PROJECT_ROOT = Path(r'D:\\Softfors\\jup')
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'notebooks' / 'phasewise' / 'phase_12_oracle_roi' / 'code'))
import phase12_oracle_inference as m

T = m.TABLES; A = m.AUDITS
def _sh(rel):
    q = PROJECT_ROOT / rel
    return m.sha256_file(q) if q.exists() else 'N/A'

geom   = pd.read_csv(T/'phase12_clean_v3_oracle_geometry.csv')
case   = pd.read_csv(T/'phase12_clean_v3_oracle_case_metrics.csv')
comp   = pd.read_csv(T/'phase12_clean_v3_oracle_component_metrics.csv')
delta  = pd.read_csv(T/'phase12_clean_v3_primary_paired_deltas.csv')
repro  = pd.read_csv(T/'phase12_clean_v3_global_reproduction_gate.csv')
summ   = pd.read_csv(T/'phase12_clean_v3_oracle_raw_summary_by_model.csv')
sens   = pd.read_csv(T/'phase12_float_vs_legacy_mapback_sensitivity.csv')
prov   = pd.read_csv(T/'phase12_clean_v3_oracle_inference_provenance.csv')
flags  = pd.read_csv(T/'phase12_phase11_cohort_flags.csv')
print('Loaded frozen Phase-12 tables.')
print('geometry', len(geom), '| case', len(case), '| component', len(comp),
      '| delta', len(delta), '| repro', len(repro))
""")

md("""## 3. Supervisor-Frozen Oracle Protocol

Recorded **before** any clean-v3 oracle inference.
""")
co("""fz = json.loads((A/'phase12_clean_v3_oracle_protocol_frozen.json').read_text(encoding='utf-8'))
print('status                        :', fz['status'])
print('recorded before inference     :', fz['recorded_before_clean_v3_oracle_inference'])
print('primary margin                :', fz['decisions']['oracle_geometry']['primary_margin'])
print('oracle unit                   :', fz['decisions']['oracle_geometry']['oracle_unit'])
print('map-back primary              :', fz['decisions']['mapback']['primary'])
print('primary variant               :', fz['decisions']['primary_variant']['name'])
print('secondary variant             :', fz['decisions']['secondary_variant']['name'])
print('legacy sensitivity            :', fz['decisions']['legacy_sensitivity']['variant'])
print('fusion                        :', fz['decisions']['fusion']['rule'])
print('reference architecture        :', fz['decisions']['model_scope']['reference_architecture'])
print('UNet++ role                   :', fz['decisions']['model_scope']['unetpp_role'])
print('gate dimensions (frozen)      :', fz['decisions']['gate_framework_frozen']['dimensions'])
print('scalar automatic threshold    :', fz['decisions']['gate_framework_frozen']['scalar_automatic_threshold'])
""")

md("""## 4. Historical README Provenance Restoration

The Part-1A README edit was reverted **byte-exactly from version control** in Part 1B.
""")
co("""readme = PROJECT_ROOT/'notebooks/phasewise/phase_12_oracle_roi/README.md'
print('Restored README SHA (CRLF, on-disk):', m.sha256_file(readme))
print('Part-1A reported SHA (LF-normalised):', fz['readme_restoration']['part1a_reported_sha_lf'])
print()
print('Restoration method:', fz['readme_restoration']['method'])
print('Errata artifact   :', fz['readme_restoration']['errata'])
print()
err = (A/'phase12_historical_readme_errata.md').read_text(encoding='utf-8')
print('\\n'.join(err.split('\\n')[:6]))
""")

md("""## 5. Manifest / FULL_FIELD Integrity
""")
co("""ff = m.full_field_frame()
print('FULL_FIELD cases      :', len(ff))
print('native GT components  :', len(geom))
print('size strata           :', geom['size_stratum'].value_counts().to_dict())
print('per-case component count distribution:',
      geom.groupby('sample_id').size().value_counts().sort_index().to_dict())
assert len(ff) == 103, 'expected 103 FULL_FIELD cases'
assert len(geom) == 152, 'expected 152 native components'
print()
print('MANIFEST/FULL_FIELD GATE - PASS (103 cases, 152 components)')
print('No TEST rows present.')
""")

md("""## 6. Model / Checkpoint Provenance
""")
co("""display(prov[['model','experiment_id','best_pt_sha','history_sha','threshold','amp','batch_size','margin']])
print()
print('Reference model selected: NO — all four models are in scope.')
""")

md("""## 7. Global EVALUATION_512 Reproduction Gate

Every model's global inference must reproduce the frozen Phase-11 per-case metrics for the
same 103 FULL_FIELD cases (max abs Dice difference <= 1e-4) **before** oracle inference.
""")
co("""display(repro)
assert bool(repro['pass_1e4'].all()), 'GLOBAL REPRODUCTION GATE FAILED -> CHECK_REQUIRED'
print()
print('GLOBAL REPRODUCTION GATE - PASS (all four models)')
print('max abs Dice diff across models: %.3e' % repro['max_abs_dice_diff'].max())
print()
print('This protects against preprocessing / checkpoint / metric drift before any')
print('oracle interpretation.')
""")

md("""## 8. Native-Space Global Inversion Validation

The paired GLOBAL vs ORACLE comparison must be performed in the **same** native space.
`GLOBAL_NATIVE` = the EVALUATION_512 global prediction with preprocessing inverted
(strip pad, bilinear resize of the valid extent to native W×H, in FLOAT).
Label: `PHASE12_NATIVE_SPACE_GLOBAL_BASELINE`.
""")
co("""g = case[case.variant=='GLOBAL_NATIVE']
print('GLOBAL_NATIVE macro Dice by model:')
print(g.groupby('model')['dice'].mean().round(6).to_string())
print()
print('native shapes seen:', sorted(set(zip(case.native_height, case.native_width)))[:6], '...')
print()
print('The authoritative Phase-10 EVALUATION_512 VAL metrics are NOT replaced or')
print('reinterpreted; GLOBAL_NATIVE is the paired Phase-12 baseline only.')
""")

md("""## 9. Oracle Geometry Construction

Frozen: per-component bbox, `round(0.25 * bbox_dim)` per axis, centred SQUARE crop
(`side = max(expanded_h, expanded_w)`), clip to native image, zero-pad, resize 512 BILINEAR.
""")
co("""cols = ['sample_id','native_component_id','size_stratum','native_component_pixels',
        'bbox_height','bbox_width','crop_crop_side','crop_effective_magnification',
        'crop_pad_top','crop_pad_left']
display(geom[cols].head(12))
print()
print('magnification (512 / side):')
print(geom['crop_effective_magnification'].describe().round(3).to_string())
print()
print('components needing padding (side extends outside native image):',
      int(((geom.crop_pad_top>0)|(geom.crop_pad_bottom>0)|(geom.crop_pad_left>0)|(geom.crop_pad_right>0)).sum()),
      'of', len(geom))
""")

md("""## 10. Geometry Integrity
""")
co("""g2 = geom.copy()
checks = {
 'rows == 152': len(g2)==152,
 'one row per (sample,component)': not g2.duplicated(['sample_id','native_component_id']).any(),
 'all sides > 0': bool((g2.crop_crop_side>0).all()),
 'square side == max(expanded_h, expanded_w)': bool((g2.crop_crop_side == g2[['bbox_height','bbox_width']].max(axis=1).add(
     2*g2[['bbox_height','bbox_width']].max(axis=1).mul(0.25).round().astype(int))).all()),
 'magnification == 512/side': bool(np.allclose(g2.crop_effective_magnification, 512.0/g2.crop_crop_side)),
 'clip within native bounds': bool(((g2.crop_clip_y1>=0)&(g2.crop_clip_y2<=g2.native_H)&
                                    (g2.crop_clip_x1>=0)&(g2.crop_clip_x2<=g2.native_W)).all()),
}
for k,v in checks.items(): print(f'  {k}: {v}')
assert all(checks.values()), 'geometry integrity FAILED'
print()
print('GEOMETRY INTEGRITY - PASS')
""")

md("""## 11. Oracle Component Crop Inference
""")
co("""print('Crop inferences per model:', fz['decisions']['oracle_geometry']['expected_cases'], 'cases ->',
      len(geom), 'crops per model')
print('total crops across four models:', 4*len(geom))
print()
print('Same frozen model per architecture is reused on crops (no separate regional model).')
print('512x512, AMP, CUDA, sigmoid FLOAT probability.')
print()
print('No crop geometry was altered based on any model output.')
""")

md("""## 12. FLOAT Map-Back (PRIMARY)

Regional float sigmoid probability → bilinear restore to square-side geometry **in float**
→ strip square padding → place into native clipped coordinates. No uint8 quantisation.
""")
co("""print('Primary map-back: FLOAT_BILINEAR')
print('  quantisation: none')
print('  procedure   :')
for s in fz['decisions']['mapback']['procedure']: print('   -', s)
print()
print('Approved MATERIAL clean-v3 correction:',
      fz['decisions']['mapback']['approved_material_correction'])
print('Reason:', fz['decisions']['mapback']['reason'])
""")

md("""## 13. Legacy uint8 Sensitivity Derivation

Derived from the **same** computed crop probability tensor — no second model pass.
""")
co("""print('Legacy variant:', fz['decisions']['legacy_sensitivity']['variant'])
print('Semantics     :', fz['decisions']['legacy_sensitivity']['semantics'])
print('Status        :', fz['decisions']['legacy_sensitivity']['status'])
print('Second model pass allowed:', fz['decisions']['legacy_sensitivity']['second_model_pass_allowed'])
print('Derivation    :', fz['decisions']['legacy_sensitivity']['derivation'])
""")

md("""## 14. Multi-Component MAX Fusion

One crop per native component; restored independently; fused by **pixelwise MAX before
thresholding**. `ORACLE_REGION_UNION` = native pixels inside ≥1 mapped-back crop support
(derived from GT geometry only, never altered by predictions).
""")
co("""print('Fusion rule:', fz['decisions']['fusion']['rule'])
print('R(x)       :', fz['decisions']['fusion']['R_x'])
print('threshold  : AFTER the full-image probability variant is constructed')
print()
print('ORACLE_REGION_UNION definition:', fz['decisions']['oracle_region_union']['definition'])
print('derived from                  :', fz['decisions']['oracle_region_union']['derived_from'])
print('altered by predictions        :', fz['decisions']['oracle_region_union']['altered_by_predictions'])
""")

md("""## 15. Primary GLOBAL_RETAINED Construction
""")
co("""print('PRIMARY variant:', fz['decisions']['primary_variant']['name'])
print('  formula     :', fz['decisions']['primary_variant']['formula'])
print('  inside U    :', fz['decisions']['primary_variant']['inside_union'])
print('  forbidden   :', fz['decisions']['primary_variant']['forbidden'])
print('  threshold   :', fz['decisions']['primary_variant']['threshold'],
      '| timing:', fz['decisions']['primary_variant']['threshold_timing'])
print()
print('This is a deterministic regional REPLACEMENT intervention: the oracle target region')
print('is replaced by higher-effective-resolution regional inference while the global')
print('prediction is preserved elsewhere.')
""")

md("""## 16. Secondary FLOAT_CROP_ONLY Construction
""")
co("""print('SECONDARY variant:', fz['decisions']['secondary_variant']['name'])
print('  formula :', fz['decisions']['secondary_variant']['formula'])
print('  status  :', fz['decisions']['secondary_variant']['status'])
print('  is the primary SR-1 mechanism estimate:', fz['decisions']['secondary_variant']['is_primary_sr1_estimate'])
print()
print('This reproduces the conceptual historical crop-only oracle while removing the')
print('uint8 numerical artifact. It is a comparator, NOT the primary estimate.')
""")

md("""## 17. Native Case Metrics

Raw case metrics for every model × variant, in **native space**.
""")
co("""print('case rows:', len(case), '(103 cases x 4 models x 4 variants)')
piv_dice = case.pivot_table(index='model', columns='variant', values='dice', aggfunc='mean')
piv_rec  = case.pivot_table(index='model', columns='variant', values='object_recall', aggfunc='mean')
print()
print('=== native macro Dice by model x variant ===')
display(piv_dice.round(6))
print('=== native object recall by model x variant ===')
display(piv_rec.round(6))
print()
print('NO RANKING. No winner. Reporting only.')
""")

md("""## 18. Explicit Native Component Metrics

Detection is evaluated per **native GT component** (8-connectivity, ≥1 native pixel
overlap) — never the Phase-11 case-attributed approximation.
""")
co("""print('component rows:', len(comp), '(152 components x 4 models)')
agg = comp.groupby('model')[['global_detected','primary_oracle_detected',
                             'float_crop_only_detected','legacy_crop_only_detected']].sum()
display(agg)
print()
print('detected components out of 152 per model/variant.')
print('component correspondence: explicit native identity (no case-complete inference).')
""")

md("""## 19. Primary Paired Deltas

Paired within the **same FULL_FIELD case** and the **same frozen architecture**:
`delta_dice = primary_oracle_dice - global_dice`.
""")
co("""print('delta rows:', len(delta), '(103 cases x 4 models)')
agg = delta.groupby('model')['delta_dice'].agg(['mean','median','min','max'])
display(agg.round(6))
print()
print('=== object recall and component recovery ===')
rec = delta.groupby('model')[['global_object_recall','primary_object_recall','delta_object_recall',
                              'global_missed_components','primary_missed_components',
                              'recovered_components']].mean()
display(rec.round(6))
print()
print('=== empty predictions recovered ===')
print(delta.groupby('model')[['empty_global','empty_primary','empty_recovered']].sum().to_string())
print()
print('NO inferential statistics. Raw paired deltas only.')
""")

md("""## 20. Float-vs-Legacy Sensitivity
""")
co("""display(sens[['model','n_cases','mean_abs_dice_diff','max_abs_dice_diff',
                'mean_abs_iou_diff','max_abs_iou_diff']].round(6))
print()
print('max abs Dice difference across models: %.6f' % sens['max_abs_dice_diff'].max())
print()
print('STATUS: HISTORICAL_NUMERICAL_SENSITIVITY_ONLY')
print('This measures the historical uint8 restoration quantisation impact (and the')
print('PIL-vs-torch bilinear convention difference), NOT the SR-1 primary effect.')
""")

md("""## 21. Raw Model × Variant Summary
""")
co("""display(summ[['model','variant','n_cases','macro_dice','macro_iou','macro_precision',
               'macro_recall','empty_predictions','native_object_recall','missed_components',
               'valid_hd95_n','invalid_hd95_n','median_valid_hd95']].round(6))
print()
print('RAW DESCRIPTIVE EVIDENCE. No winner. No ranking. No final mechanism conclusion.')
""")

md("""## 22. Frozen Phase-11 Cohort Attachment

Flags attached from **pre-existing frozen** Phase-11 cohorts — never reselected after
seeing Phase-12 results.
""")
co("""print('rows:', len(flags))
for c in ['ALL_FOUR_LOW','PHASE11_HARD_CASE','PHASE11_TOP_DISAGREEMENT','PHASE11_MULTICOMPONENT']:
    print(f'  {c}: {int(flags[c].sum())} of 103 FULL_FIELD cases')
print()
joined = delta.merge(flags, on='sample_id', how='left')
print('=== primary delta Dice on frozen cohorts ===')
for c in ['ALL_FOUR_LOW','PHASE11_HARD_CASE','PHASE11_TOP_DISAGREEMENT','PHASE11_MULTICOMPONENT']:
    sub = joined[joined[c]]
    if len(sub):
        print(f'  {c:26s} n={len(sub):3d} mean delta_dice={sub.delta_dice.mean():+.6f} '
              f'median={sub.delta_dice.median():+.6f}')
""")

md("""## 23. Artifact Registry
""")
co("""reg = pd.read_csv(T/'phase12_part1b_artifact_registry.csv')
display(reg)
print()
print('registry rows:', len(reg))
""")

md("""## 24. Limitations

- Part 1B is **raw evidence only**; no final Phase-12 mechanism conclusion is issued.
- `GLOBAL_NATIVE` is a **Phase-12 paired baseline**; it does not replace the authoritative
  Phase-10 EVALUATION_512 VAL metrics.
- The primary variant **retains the global prediction outside the oracle region**, so its
  native Dice is *lower* than the crop-only variant by construction — crop-only zeroes
  everything outside the crops and is therefore not a fair deployable comparator.
- **Oracle-constrained FP is artificially advantaged** (historical caveat): the oracle
  knows where the target is.
- The float-vs-legacy sensitivity conflates uint8 quantisation with the PIL-vs-torch
  bilinear convention; it is diagnostic only.
- HD95 invalid cases (empty prediction / empty GT) are flagged and excluded from HD95
  statistics, never silently dropped.
- Single seed; no significance testing; no reference model selected.
""")

md("""## 25–28. Upstream Frozen Training Provenance

Read-only from the frozen Phase-10 normalized epoch tables. **Every epoch row is shown.**
""")
for i, k in enumerate(['unet','attention_unet','unetpp','deeplabv3plus'], start=25):
    d = {'unet':'UNet','attention_unet':'Attention U-Net','unetpp':'UNet++','deeplabv3plus':'DeepLabV3+'}[k]
    md(f"""### 2{i}. Upstream Complete Epoch Table — {d}
""")
    co(f"""t = pd.read_csv(m.PHASE10_EPOCH_TABLES['{k}'])
eps = t['epoch'].astype(int).tolist(); exp = list(range(1, len(t)+1))
print('=== UPSTREAM {d} ===')
print('  rows:', len(t), '| expected:', m.EXPECTED_EPOCH_ROWS['{k}'])
print('  first/last:', min(eps), '/', max(eps), '| missing:', sorted(set(exp)-set(eps)),
      '| duplicates:', sorted({{e for e in eps if eps.count(e)>1}}))
assert len(t)==m.EXPECTED_EPOCH_ROWS['{k}'] and eps==exp
print()
display(t)
""")

md("""## 29. Stop Boundary
""")
co("""print('=== PHASE-12 PART-1B BOUNDARY ===')
print('Training epochs                    : 0')
print('Optimizer steps                    : 0')
print('Checkpoint / config / manifest mods: 0')
print('Margin / threshold tuning          : NONE')
print('Reference model / winner           : NONE')
print('Unauthorized fusion variants       : 0')
print('Statistical testing                : NONE')
print('TEST reads                         : 0')
print('Phase 13 started                   : NO')
print('Phases 14-18 started               : NO')
print('RA-MedFiLM implemented             : NO')
print()
print('FINAL PHASE-12 MECHANISM CONCLUSION: NOT ISSUED (Part 1B is raw evidence only)')
print('NEXT: WAIT_FOR_SUPERVISOR_PHASE12_PART1B_REVIEW')
""")

out = Path(r'D:\Softfors\jup\notebooks\phasewise\phase_12_oracle_roi\phase12_clean_v3_oracle_regional_inference.ipynb')
with open(out,'w',encoding='utf-8') as f:
    nbf.write(nb,f)
print(f'Notebook written: {out}')
print(f'Total cells: {len(nb.cells)}')
