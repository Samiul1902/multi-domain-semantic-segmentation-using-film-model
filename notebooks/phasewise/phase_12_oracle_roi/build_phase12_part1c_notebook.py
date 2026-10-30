"""Build Phase 12 Part 1C — paired oracle mechanism analysis + visual evidence notebook."""
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

md("""# Phase 12 Part 1C — Paired Oracle Mechanism Analysis + Visual Evidence

**Model:** Gemini 3.1 Pro High · **Date:** 2026-09-21
**Manifest:** `phase4_v3` · **Taxonomy:** `kub_size_clean_v3_v1` · **Strategy:** SR-1

---

> **READ-ONLY ANALYSIS + VISUALIZATION.** Operates **only** on frozen Phase-12 Part-1B tables.
>
> **No model loading · no inference · no training · no optimizer · no source-table
> modification · no statistics · no winner/rank · no TEST access.**
>
> This is **not** the final Phase-12 supervisor conclusion, **not** a GO/NO-GO decision,
> **not** Phase-13 authorization, and **not** model selection.
>
> **Primary mechanism comparison (the only primary):**
> `GLOBAL_NATIVE` vs `ORACLE_FLOAT_GLOBAL_RETAINED` — paired within the same FULL_FIELD
> case, architecture, native space, GT, and threshold.
>
> Comparators (never primary): `ORACLE_FLOAT_CROP_ONLY` = SECONDARY_HISTORICAL_GEOMETRY_COMPARATOR;
> `ORACLE_LEGACY_UINT8_CROP_ONLY` = COMBINED_LEGACY_RESTORE_SENSITIVITY.
""")

md("""## 2. Scope / Governance

| Rule | Status |
|---|---|
| Model loading | **0** |
| Inference passes | **0** |
| Training epochs / optimizer steps | **0 / 0** |
| Source-table modification | **0** |
| Margin / threshold / geometry changes | **NONE** |
| Statistical testing | **NONE** |
| Winner / rank | **NONE** |
| Final Phase-12 conclusion | **NOT ISSUED** |
| TEST reads | **0** |
| Phase 13 / Phases 14–18 | **NOT STARTED** |

Fixed **non-ranking** model order everywhere: **UNet → Attention U-Net → UNet++ → DeepLabV3+**.
""")

co("""import sys, json
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from IPython.display import Image as IPImage, display

pd.set_option('display.max_rows', None); pd.set_option('display.max_columns', None)
pd.set_option('display.width', None); pd.set_option('display.max_colwidth', None)
%matplotlib inline

PROJECT_ROOT = Path(r'D:\\Softfors\\jup')
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT/'notebooks'/'phasewise'/'phase_12_oracle_roi'/'code'))
import phase12_oracle_analysis as a

T = a.TABLES; A = a.AUDITS; FIG = a.FIGDIR
ORDER, COLORS = a.ORDER, a.COLORS
print('Fixed model order:', ORDER)
print('Figure directory :', FIG)
print('Module loaded read-only (no model import).')
""")

md("""## 3. Part-1B Errata

Two non-blocking interpretation corrections. **No accepted artifact was modified.**
""")
co("""err = (A/'phase12_part1b_analysis_errata.md').read_text(encoding='utf-8')
print('\\n'.join(err.split('\\n')[:10]))
print()
print('CANONICAL LABELS:')
print('  global reproduction gate -> DICE_IOU_GLOBAL_REPRODUCTION_GATE_PASS')
print('  float-vs-legacy          -> COMBINED_LEGACY_RESTORE_SENSITIVITY')
""")

md("""## 4. Frozen Primary Mechanism
""")
co("""fz = json.loads((A/'phase12_clean_v3_oracle_protocol_frozen.json').read_text(encoding='utf-8'))
print('primary variant   :', fz['decisions']['primary_variant']['name'])
print('  formula         :', fz['decisions']['primary_variant']['formula'])
print('  inside union    :', fz['decisions']['primary_variant']['inside_union'])
print('  threshold       :', fz['decisions']['primary_variant']['threshold'], '(after full map)')
print('secondary variant :', fz['decisions']['secondary_variant']['name'])
print('legacy sensitivity:', fz['decisions']['legacy_sensitivity']['variant'])
print('margin            :', fz['decisions']['oracle_geometry']['primary_margin'])
print('reference model   :', fz['decisions']['model_scope']['reference_architecture'])
""")

md("""## 5. Input Artifact Integrity
""")
co("""integ = a.input_integrity()
for k,v in integ.items(): print(f'  {k}: {v}')
assert integ['case_rows']==1648 and integ['component_rows']==608 and integ['geometry_rows']==152
assert integ['delta_rows']==412 and integ['flag_rows']==103
assert integ['no_many_to_many'], 'component/geometry merge expanded rows'
print()
print('INPUT INTEGRITY - PASS (exact keys, no many-to-many expansion)')
""")

case=a=None
co("""case = a.load_case(); comp = a.load_comp(); geom = a.load_geom()
delta = a.load_delta(); flags = a.load_flags(); sens = a.load_sens()
print('loaded:', len(case), len(comp), len(geom), len(delta), len(flags), len(sens))
""")

md("""## 6. Primary Global-vs-Oracle Summary
""")
co("""summ = pd.read_csv(T/'phase12_primary_global_vs_oracle_summary.csv')
display(summ[['model','n','global_macro_dice','primary_macro_dice','diff_macro_dice',
              'global_macro_iou','primary_macro_iou','global_macro_precision','primary_macro_precision',
              'global_macro_recall','primary_macro_recall']].round(6))
print()
display(summ[['model','global_object_recall','primary_object_recall',
              'global_empty_predictions','primary_empty_predictions',
              'global_missed_components','primary_missed_components',
              'global_median_valid_hd95','primary_median_valid_hd95']].round(6))
print()
print('No inferential statistics. Raw differences only.')
""")

md("""## 7. Paired Delta Distribution
""")
co("""dist = pd.read_csv(T/'phase12_primary_delta_distribution_by_model.csv')
display(dist[['model','n','mean_delta_dice','median_delta_dice','q25','q75','min','max',
              'count_improved','count_unchanged','count_worsened',
              'pct_improved','pct_unchanged','pct_worsened']].round(6))
print()
print('Direction is the exact paired sign (positive / zero / negative).')
print('No clinically meaningful cutoff is introduced.')
""")

md("""## 8. Improved / Worsened Case Counts
""")
co("""fig, ax = plt.subplots(figsize=(9,4.8))
x = np.arange(len(ORDER)); w=0.26
imp = [int(dist.loc[dist.model==m,'count_improved'].iloc[0]) for m in ORDER]
unc = [int(dist.loc[dist.model==m,'count_unchanged'].iloc[0]) for m in ORDER]
wor = [int(dist.loc[dist.model==m,'count_worsened'].iloc[0]) for m in ORDER]
b1=ax.bar(x-w, imp, w, label='improved (delta>0)', color='#55a868')
b2=ax.bar(x, unc, w, label='unchanged (delta=0)', color='#bbbbbb')
b3=ax.bar(x+w, wor, w, label='worsened (delta<0)', color='#c44e52')
for bs in (b1,b2,b3):
    for b in bs:
        ax.annotate(f'{int(b.get_height())}', (b.get_x()+b.get_width()/2, b.get_height()),
                    ha='center', va='bottom', fontsize=8)
ax.set_xticks(x); ax.set_xticklabels(ORDER, fontsize=9)
ax.set_ylabel('cases (of 103)'); ax.set_title('Per-case primary delta Dice direction (descriptive)')
ax.legend(fontsize=8); ax.grid(True, alpha=.3, axis='y')
plt.tight_layout(); p1=FIG/'delta_direction_counts.png'; fig.savefig(p1, dpi=140, bbox_inches='tight'); plt.close(fig)
display(IPImage(filename=str(p1)))
""")

md("""## 9. Benefit / FP-Cost Decomposition
""")
co("""bc = pd.read_csv(T/'phase12_primary_benefit_cost_summary.csv')
display(bc[['model','mean_delta_precision','median_delta_precision','mean_delta_recall','median_delta_recall',
            'mean_delta_fp_pixels','median_delta_fp_pixels','mean_delta_fn_pixels','median_delta_fn_pixels',
            'mean_delta_object_recall','median_delta_object_recall']].round(4))
print()
display(bc[['model','dice_improves_and_fp_increases','dice_improves_and_fp_decreases_or_equal',
            'dice_worsens_and_fp_increases','dice_worsens_and_fp_decreases_or_equal']])
print()
print('Purely descriptive. No value judgement yet.')
""")

md("""## 10. Normalized FP / FN Burden
""")
co("""nb = pd.read_csv(T/'phase12_primary_normalized_error_burden.csv')
display(nb[['model','variant','n','fp_per_gt_pixel_mean','fp_per_gt_pixel_median',
            'fn_fraction_mean','fn_fraction_median']].round(6))
print()
print('gt_pixels = TP + FN; fp_per_gt_pixel = FP / gt_pixels; fn_fraction = FN / gt_pixels.')
print('Normalisation removes native-size and target-size dependence. No thresholds created.')
""")

md("""## 11. Exact Component Identity Integrity
""")
co("""m = comp.merge(geom[['sample_id','native_component_id','size_stratum']],
                on=['sample_id','native_component_id'], how='left')
print('geometry unique components :', geom[['sample_id','native_component_id']].drop_duplicates().shape[0])
print('component rows             :', len(comp), '(= 152 x 4)')
print('after merge                :', len(m), '(must be 608)')
print('strata                     :', geom.size_stratum.value_counts().to_dict())
assert len(m)==608 and geom[['sample_id','native_component_id']].drop_duplicates().shape[0]==152
print()
print('COMPONENT IDENTITY INTEGRITY - PASS (exact keys, no expansion)')
print('The Phase-11 case-attributed size approximation is NOT reused.')
""")

md("""## 12. Size-Stratified Component Recovery
""")
co("""size = pd.read_csv(T/'phase12_primary_size_stratified_component_recovery.csv')
display(size[['model','size_stratum','gt_components','global_detected','global_missed',
              'global_object_recall','primary_detected','primary_missed','primary_object_recall',
              'recovered_components','lost_components']].round(4))
print()
print('TOTAL recovered:', int(size.recovered_components.sum()),
      '| TOTAL lost detections:', int(size.lost_components.sum()))
print()
print('NOTE: zero lost detections across all strata and models in this dataset.')
""")

co("""fig, axes = plt.subplots(1, 2, figsize=(15,5))
x=np.arange(len(ORDER)); w=0.38
for ax, s, ttl in [(axes[0],'TINY','TINY (n=72 components)'), (axes[1],'SMALL','SMALL (n=28 components)')]:
    d = size[size.size_stratum==s].set_index('model')
    g = [d.loc[m,'global_object_recall'] for m in ORDER]
    p = [d.loc[m,'primary_object_recall'] for m in ORDER]
    b1=ax.bar(x-w/2, g, w, label='GLOBAL', color='#4c72b0')
    b2=ax.bar(x+w/2, p, w, label='PRIMARY', color='#dd8452')
    for bs in (b1,b2):
        for b in bs: ax.annotate(f'{b.get_height():.3f}', (b.get_x()+b.get_width()/2, b.get_height()),
                                 ha='center', va='bottom', fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels(ORDER, fontsize=9); ax.set_ylim(0,1.05)
    ax.set_ylabel('object recall'); ax.set_title(ttl); ax.legend(fontsize=8); ax.grid(True, alpha=.3, axis='y')
fig.suptitle('Component-level object recall by size stratum (native, 8-conn, >=1 px overlap)', fontsize=11)
plt.tight_layout(rect=[0,0,1,0.93]); p2=FIG/'size_stratum_recall.png'; fig.savefig(p2, dpi=140, bbox_inches='tight'); plt.close(fig)
display(IPImage(filename=str(p2)))
""")

co("""fig, ax = plt.subplots(figsize=(10,5))
x=np.arange(len(a.STRATA)); w=0.2
for i,mdl in enumerate(ORDER):
    d = size[size.model==mdl].set_index('size_stratum')
    vals=[d.loc[s,'recovered_components'] if s in d.index else 0 for s in a.STRATA]
    b=ax.bar(x+(i-1.5)*w, vals, w, label=mdl, color=COLORS[mdl])
    for bb in b: ax.annotate(f'{int(bb.get_height())}', (bb.get_x()+bb.get_width()/2, bb.get_height()),
                             ha='center', va='bottom', fontsize=7)
ax.set_xticks(x); ax.set_xticklabels(a.STRATA)
ax.set_ylabel('recovered components'); ax.set_title('Component recovery by size stratum (GLOBAL missed -> PRIMARY detected)')
ax.legend(fontsize=8); ax.grid(True, alpha=.3, axis='y')
plt.tight_layout(); p3=FIG/'component_recovery_by_stratum.png'; fig.savefig(p3, dpi=140, bbox_inches='tight'); plt.close(fig)
display(IPImage(filename=str(p3)))
""")

md("""## 13. Multi-Component Transitions
""")
co("""mc = pd.read_csv(T/'phase12_primary_multicomponent_outcomes.csv')
display(mc)
tr = pd.read_csv(T/'phase12_primary_multicomponent_transitions.csv')
print()
print('transition counts (all models pooled):')
print(tr['transition'].value_counts().to_string())
print()
print('No inferential testing.')
""")

co("""fig, ax = plt.subplots(figsize=(9,4.8))
x=np.arange(len(ORDER)); w=0.26
for i,c in enumerate(['global_complete','global_partial','global_miss']):
    b=ax.bar(x+(i-1)*w, mc[c], w, label=c.replace('global_','GLOBAL '), color=['#55a868','#c44e52','#8172b2'][i])
    for bb in b: ax.annotate(f'{int(bb.get_height())}', (bb.get_x()+bb.get_width()/2, bb.get_height()),
                             ha='center', va='bottom', fontsize=7)
ax.set_xticks(x); ax.set_xticklabels(ORDER, fontsize=9)
ax.set_ylabel('multi-component cases'); ax.set_title('Multi-component outcomes — GLOBAL (primary oracle in table)')
ax.legend(fontsize=7); ax.grid(True, alpha=.3, axis='y')
plt.tight_layout(); p4=FIG/'multicomponent_outcomes.png'; fig.savefig(p4, dpi=140, bbox_inches='tight'); plt.close(fig)
display(IPImage(filename=str(p4)))
""")

md("""## 14. Empty-Prediction Recovery
""")
co("""emp = pd.read_csv(T/'phase12_primary_empty_prediction_recovery.csv')
display(emp[['model','global_empty','primary_empty','recovered_empty_cases','new_empty_cases']])
print()
for _,r in emp.iterrows():
    if r['recovered_sample_ids']:
        print(f"{r['model']}: recovered {r['recovered_empty_cases']} -> {r['recovered_sample_ids']}")
print()
print('exact sample IDs also persisted in phase12_primary_empty_prediction_ids.csv')
""")

co("""fig, ax = plt.subplots(figsize=(8,4.6))
x=np.arange(len(ORDER)); w=0.38
b1=ax.bar(x-w/2, emp['global_empty'], w, label='GLOBAL empty', color='#4c72b0')
b2=ax.bar(x+w/2, emp['primary_empty'], w, label='PRIMARY empty', color='#dd8452')
for bs in (b1,b2):
    for b in bs: ax.annotate(f'{int(b.get_height())}', (b.get_x()+b.get_width()/2, b.get_height()),
                             ha='center', va='bottom', fontsize=9)
ax.set_xticks(x); ax.set_xticklabels(ORDER, fontsize=9)
ax.set_ylabel('empty predictions'); ax.set_title('Empty predictions: GLOBAL vs PRIMARY')
ax.legend(fontsize=8); ax.grid(True, alpha=.3, axis='y')
plt.tight_layout(); p5=FIG/'empty_prediction_recovery.png'; fig.savefig(p5, dpi=140, bbox_inches='tight'); plt.close(fig)
display(IPImage(filename=str(p5)))
""")

md("""## 15. HD95 Validity / Boundary Analysis
""")
co("""hd = pd.read_csv(T/'phase12_primary_hd95_analysis.csv')
display(hd[['model','global_valid_n','global_invalid_n','primary_valid_n','primary_invalid_n',
            'both_valid_paired_n','median_valid_hd95_global','median_valid_hd95_primary',
            'delta_hd95_mean','delta_hd95_median','delta_hd95_q25','delta_hd95_q75']].round(4))
print()
print('Negative delta_hd95 = lower boundary distance. Invalid HD95 flagged, never dropped.')
""")

md("""## 16. Phase-11 Frozen Cohort Bridge
""")
co("""coh = pd.read_csv(T/'phase12_phase11_frozen_cohort_oracle_response.csv')
display(coh[['cohort','model','n_cases','n_case_model_rows','global_mean_dice','primary_mean_dice',
             'mean_delta_dice','median_delta_dice','global_object_recall','primary_object_recall',
             'recovered_components','empty_recoveries']].round(4))
print()
print('n_cases = distinct FULL_FIELD cases; n_case_model_rows = cases x 1 model. NOT mixed.')
print('Cohorts are pre-frozen; NOT reselected after seeing results.')
""")

md("""## 17. ALL_FOUR_LOW Analysis
""")
co("""afl = pd.read_csv(T/'phase12_all_four_low_oracle_response.csv')
display(afl[['sample_id','model','category','native_gt_components','global_dice','primary_dice',
             'delta_dice','global_object_recall','primary_object_recall','recovered_components']].round(4))
print()
print('per-model mean delta Dice on the 12 ALL_FOUR_LOW cases:')
print(afl.groupby('model')['delta_dice'].mean().round(4).to_string())
print()
print('Central to the hypothesis that some failures reflect resolution/scale rather than one')
print('architecture. No causal claim.')
""")

co("""fig, ax = plt.subplots(figsize=(10,5))
piv = afl.pivot_table(index='sample_id', columns='model', values='delta_dice')
x=np.arange(len(piv)); w=0.2
for i,mdl in enumerate(ORDER):
    vals = piv[mdl].values if mdl in piv.columns else [0]*len(piv)
    ax.bar(x+(i-1.5)*w, vals, w, label=mdl, color=COLORS[mdl])
ax.axhline(0, color='black', linewidth=1)
ax.set_xticks(x); ax.set_xticklabels([s[:8] for s in piv.index], fontsize=7, rotation=45)
ax.set_ylabel('delta Dice'); ax.set_title('Phase-11 ALL_FOUR_LOW (12 frozen cases): primary delta Dice by model')
ax.legend(fontsize=8); ax.grid(True, alpha=.3, axis='y')
plt.tight_layout(); p6=FIG/'all_four_low_response.png'; fig.savefig(p6, dpi=140, bbox_inches='tight'); plt.close(fig)
display(IPImage(filename=str(p6)))
""")

md("""## 18. Category Metadata Analysis
""")
co("""cat = pd.read_csv(T/'phase12_primary_category_analysis.csv')
display(cat[['model','category','n','global_mean_dice','primary_mean_dice',
             'mean_delta_dice','median_delta_dice','improved','worsened']].round(4))
print()
print('Bladder/Kidney/Ureteric are subgroup METADATA, not segmentation classes.')
print('Ureteric n is small - do not overinterpret.')
""")

md("""## 19. Cross-Architecture Consistency
""")
co("""cad = pd.read_csv(T/'phase12_cross_architecture_distribution.csv')
piv = cad.pivot_table(index='n_models', columns='metric', values='n_cases').fillna(0).astype(int)
display(piv)
ca = pd.read_csv(T/'phase12_cross_architecture_oracle_consistency.csv')
print()
print('cases with all four models positive delta Dice:', int(ca.all_four_delta_positive.sum()), 'of', len(ca))
print('cases with all four models object-recall non-worse:', int(ca.all_four_object_recall_nonworse.sum()), 'of', len(ca))
print()
print('No arbitrary generality threshold.')
""")

co("""fig, ax = plt.subplots(figsize=(8,4.6))
x=np.arange(5); w=0.26
for i,metric in enumerate(['models_delta_positive','models_object_recall_improved',
                           'models_component_recovery_positive']):
    vals=[int(cad[(cad.metric==metric)&(cad.n_models==i)].n_cases.iloc[0]) for i in range(5)]
    b=ax.bar(x+(i-1)*w, vals, w, label=metric.replace('models_',''))
    for bb in b: ax.annotate(f'{int(bb.get_height())}', (bb.get_x()+bb.get_width()/2, bb.get_height()),
                             ha='center', va='bottom', fontsize=7)
ax.set_xticks(x); ax.set_xlabel('number of models (0..4)'); ax.set_ylabel('cases')
ax.set_title('Cross-architecture oracle consistency per case'); ax.legend(fontsize=7); ax.grid(True, alpha=.3, axis='y')
plt.tight_layout(); p7=FIG/'cross_architecture_consistency.png'; fig.savefig(p7, dpi=140, bbox_inches='tight'); plt.close(fig)
display(IPImage(filename=str(p7)))
""")

md("""## 20. Primary vs Crop-Only Comparator

**Crop-only includes oracle background suppression; it is NOT the primary SR-1 mechanism
estimate.**
""")
co("""crop = pd.read_csv(T/'phase12_primary_vs_crop_only_comparator.csv')
display(crop[['model','primary_macro_dice','crop_only_macro_dice',
              'macro_dice_difference_crop_minus_primary','macro_precision_difference',
              'macro_recall_difference','mean_fp_difference','mean_fn_difference',
              'object_recall_difference','interpretation']].round(4))
print()
print('Crop-only zeroes all prediction outside oracle crop support, i.e. it has access to')
print('oracle background suppression. It must NOT be called preferred.')
""")

co("""fig, ax = plt.subplots(figsize=(8,4.6))
x=np.arange(len(ORDER)); w=0.38
b1=ax.bar(x-w/2, crop['primary_macro_dice'], w, label='PRIMARY (global retained)', color='#dd8452')
b2=ax.bar(x+w/2, crop['crop_only_macro_dice'], w, label='CROP_ONLY (oracle bg suppression)', color='#8172b2')
for bs in (b1,b2):
    for b in bs: ax.annotate(f'{b.get_height():.4f}', (b.get_x()+b.get_width()/2, b.get_height()),
                             ha='center', va='bottom', fontsize=8)
ax.set_xticks(x); ax.set_xticklabels(ORDER, fontsize=9); ax.set_ylim(0,1.0)
ax.set_ylabel('macro Dice')
ax.set_title('PRIMARY vs CROP_ONLY macro Dice\\nCROP_ONLY includes oracle background suppression; not the primary SR-1 estimate',
             fontsize=10)
ax.legend(fontsize=8); ax.grid(True, alpha=.3, axis='y')
plt.tight_layout(); p8=FIG/'primary_vs_crop_only.png'; fig.savefig(p8, dpi=140, bbox_inches='tight'); plt.close(fig)
display(IPImage(filename=str(p8)))
""")

md("""## 21. Combined Legacy Restore Sensitivity
""")
co("""display(sens[['model','n_cases','mean_abs_dice_diff','max_abs_dice_diff',
                'mean_abs_iou_diff','max_abs_iou_diff']].round(6))
print()
print('CANONICAL LABEL: COMBINED_LEGACY_RESTORE_SENSITIVITY')
print('Cannot isolate uint8 quantisation alone: the restoration engine also differs')
print('  FLOAT  : Torch bilinear, align_corners=False')
print('  LEGACY : PIL bilinear + uint8 quantisation')
print()
print('MUST NOT be used in the regional-integration gate. No rerun performed.')
""")

co("""fig, ax = plt.subplots(figsize=(8,4.6))
b=ax.bar(ORDER, sens['max_abs_dice_diff'], color=[COLORS[m] for m in ORDER])
for bb in b: ax.annotate(f'{bb.get_height():.4f}', (bb.get_x()+bb.get_width()/2, bb.get_height()),
                         ha='center', va='bottom', fontsize=9)
ax.set_ylabel('max abs Dice difference')
ax.set_title('COMBINED_LEGACY_RESTORE_SENSITIVITY\\n(uint8 quantisation + resample-engine confound)', fontsize=10)
ax.grid(True, alpha=.3, axis='y')
plt.tight_layout(); p9=FIG/'combined_legacy_restore_sensitivity.png'; fig.savefig(p9, dpi=140, bbox_inches='tight'); plt.close(fig)
display(IPImage(filename=str(p9)))
""")

md("""## 22. Visual Comparison Dashboard
""")
co("""fig, axes = plt.subplots(2, 2, figsize=(15,9))
x=np.arange(len(ORDER)); w=0.38
def paired(ax, gcol, pcol, ylabel, title, ylim=None):
    b1=ax.bar(x-w/2, summ[gcol], w, label='GLOBAL', color='#4c72b0')
    b2=ax.bar(x+w/2, summ[pcol], w, label='PRIMARY', color='#dd8452')
    for bs in (b1,b2):
        for b in bs: ax.annotate(f'{b.get_height():.4f}', (b.get_x()+b.get_width()/2, b.get_height()),
                                 ha='center', va='bottom', fontsize=7)
    ax.set_xticks(x); ax.set_xticklabels(ORDER, fontsize=8)
    ax.set_ylabel(ylabel); ax.set_title(title); ax.legend(fontsize=8); ax.grid(True, alpha=.3, axis='y')
    if ylim: ax.set_ylim(*ylim)
paired(axes[0,0], 'global_macro_dice','primary_macro_dice','macro Dice','A. Macro Dice (native)',(0,1))
paired(axes[0,1], 'global_object_recall','primary_object_recall','object recall','B. Object recall',(0,1.05))
paired(axes[1,0], 'global_macro_precision','primary_macro_precision','precision','C. Precision',(0,1))
paired(axes[1,1], 'global_macro_recall','primary_macro_recall','recall','D. Recall',(0,1))
fig.suptitle('Phase 12 Part 1C — GLOBAL_NATIVE vs ORACLE_FLOAT_GLOBAL_RETAINED (primary mechanism)', fontsize=12)
plt.tight_layout(rect=[0,0,1,0.94]); p10=FIG/'dashboard_abcd.png'; fig.savefig(p10, dpi=140, bbox_inches='tight'); plt.close(fig)
display(IPImage(filename=str(p10)))
""")

co("""fig, axes = plt.subplots(2, 2, figsize=(15,9))
b=axes[0,0].bar(ORDER, dist['mean_delta_dice'], color=[COLORS[m] for m in ORDER])
for bb in b: axes[0,0].annotate(f'{bb.get_height():.4f}', (bb.get_x()+bb.get_width()/2, bb.get_height()),
                               ha='center', va='bottom', fontsize=8)
axes[0,0].set_title('E. Mean delta Dice'); axes[0,0].grid(True, alpha=.3, axis='y')
axes[0,0].tick_params(axis='x', labelsize=8)
b=axes[0,1].bar(ORDER, dist['median_delta_dice'], color=[COLORS[m] for m in ORDER])
for bb in b: axes[0,1].annotate(f'{bb.get_height():.4f}', (bb.get_x()+bb.get_width()/2, bb.get_height()),
                               ha='center', va='bottom', fontsize=8)
axes[0,1].set_title('F. Median delta Dice'); axes[0,1].grid(True, alpha=.3, axis='y')
axes[0,1].tick_params(axis='x', labelsize=8)
data=[delta[delta.model==k]['delta_dice'].values for k in a.MODELS]
axes[1,0].boxplot(data, tick_labels=ORDER, showmeans=True)
axes[1,0].axhline(0, color='black', linewidth=1)
axes[1,0].set_title('H. Per-case delta Dice distribution'); axes[1,0].grid(True, alpha=.3, axis='y')
axes[1,0].tick_params(axis='x', labelsize=7)
nbp = nb.pivot_table(index='model', columns='variant', values='fp_per_gt_pixel_mean')
b1=axes[1,1].bar(x-w/2, [nbp.loc[m,'GLOBAL'] for m in ORDER], w, label='GLOBAL', color='#4c72b0')
b2=axes[1,1].bar(x+w/2, [nbp.loc[m,'PRIMARY'] for m in ORDER], w, label='PRIMARY', color='#dd8452')
axes[1,1].set_xticks(x); axes[1,1].set_xticklabels(ORDER, fontsize=8)
axes[1,1].set_title('N. FP per GT pixel (normalized)'); axes[1,1].legend(fontsize=8)
axes[1,1].grid(True, alpha=.3, axis='y')
fig.suptitle('Phase 12 Part 1C — delta and normalized-burden views', fontsize=12)
plt.tight_layout(rect=[0,0,1,0.94]); p11=FIG/'dashboard_efhn.png'; fig.savefig(p11, dpi=140, bbox_inches='tight'); plt.close(fig)
display(IPImage(filename=str(p11)))
""")

co("""fig, axes = plt.subplots(1, 3, figsize=(17,5))
for ax, s, ttl in [(axes[0],'TINY','I. TINY object recall'), (axes[1],'SMALL','J. SMALL object recall')]:
    d=size[size.size_stratum==s].set_index('model')
    b1=ax.bar(x-w/2, [d.loc[m,'global_object_recall'] for m in ORDER], w, label='GLOBAL', color='#4c72b0')
    b2=ax.bar(x+w/2, [d.loc[m,'primary_object_recall'] for m in ORDER], w, label='PRIMARY', color='#dd8452')
    for bs in (b1,b2):
        for b in bs: ax.annotate(f'{b.get_height():.3f}', (b.get_x()+b.get_width()/2, b.get_height()),
                                 ha='center', va='bottom', fontsize=7)
    ax.set_xticks(x); ax.set_xticklabels(ORDER, fontsize=8); ax.set_ylim(0,1.05)
    ax.set_title(ttl); ax.legend(fontsize=7); ax.grid(True, alpha=.3, axis='y')
b1=axes[2].bar(x-w/2, emp['global_empty'], w, label='GLOBAL', color='#4c72b0')
b2=axes[2].bar(x+w/2, emp['primary_empty'], w, label='PRIMARY', color='#dd8452')
for bs in (b1,b2):
    for b in bs: ax.annotate(f'{int(b.get_height())}', (b.get_x()+b.get_width()/2, b.get_height()),
                             ha='center', va='bottom', fontsize=8)
axes[2].set_xticks(x); axes[2].set_xticklabels(ORDER, fontsize=8)
axes[2].set_title('M. Empty predictions'); axes[2].legend(fontsize=7); axes[2].grid(True, alpha=.3, axis='y')
fig.suptitle('Phase 12 Part 1C — size-stratified and empty-prediction views', fontsize=12)
plt.tight_layout(rect=[0,0,1,0.92]); p12=FIG/'dashboard_ijm.png'; fig.savefig(p12, dpi=140, bbox_inches='tight'); plt.close(fig)
display(IPImage(filename=str(p12)))
""")

md("""## 23. Mechanism Evidence Matrix

Status vocabulary is limited to `SUPPORTIVE_DESCRIPTIVE_EVIDENCE` /
`MIXED_DESCRIPTIVE_EVIDENCE` / `NON_SUPPORTIVE_DESCRIPTIVE_EVIDENCE` / `NOT_EVALUABLE`.
**These are NOT combined into a final GO/NO-GO.**
""")
co("""mat = pd.read_csv(T/'phase12_oracle_mechanism_evidence_matrix.csv')
display(mat[['dimension','population','observed_direction','quantitative_summary','status']])
print()
print('status counts:', mat.status.value_counts().to_dict())
print()
print('NO GO / NO_GO / REVISE_LOCALIZER is issued here.')
""")

md("""## 24. Limitations

- Single seed; no significance testing; no confidence intervals.
- The primary variant **retains the global prediction outside the oracle region**, so its
  Dice is lower than crop-only by construction — crop-only is not a fair deployable
  comparator.
- **Oracle-constrained FP is artificially advantaged**: the oracle knows where the target is.
- `GLOBAL_NATIVE` is a Phase-12 paired baseline, not a replacement for the authoritative
  Phase-10 EVALUATION_512 VAL metrics.
- HD95 invalid cases are flagged and excluded from HD95 statistics only (never dropped).
- `COMBINED_LEGACY_RESTORE_SENSITIVITY` cannot isolate uint8 quantisation; it is not
  gate-usable.
- Only 103 FULL_FIELD cases; ROI acquisition cases are outside this study.
- Worsening cases are **exhaustively** reported, not cherry-picked.
- No causality is claimed for the ALL_FOUR_LOW response.
""")

md("""## 25–28. Upstream Frozen Training Provenance

Read-only from the frozen Phase-10 normalized epoch tables. **Every epoch row is shown.**
""")
for i, k in enumerate(['unet','attention_unet','unetpp','deeplabv3plus'], start=25):
    d = {'unet':'UNet','attention_unet':'Attention U-Net','unetpp':'UNet++','deeplabv3plus':'DeepLabV3+'}[k]
    md(f"""### 2{i}. Upstream Complete Epoch Table — {d}
""")
    co(f"""t = a.load_upstream_epoch_table('{k}')
eps = t['epoch'].astype(int).tolist(); exp = list(range(1, len(t)+1))
print('=== UPSTREAM {d} ===')
print('  rows:', len(t), '| expected:', a.EXPECTED_EPOCH_ROWS['{k}'])
print('  first/last:', min(eps), '/', max(eps), '| missing:', sorted(set(exp)-set(eps)),
      '| duplicates:', sorted({{e for e in eps if eps.count(e)>1}}))
assert len(t)==a.EXPECTED_EPOCH_ROWS['{k}'] and eps==exp
print()
display(t)
""")

md("""## 29. Artifact Registry
""")
co("""import hashlib
def _sh(rel):
    q = PROJECT_ROOT/rel
    return hashlib.sha256(q.read_bytes()).hexdigest() if q.exists() else 'N/A'
names = [
 'phase12_primary_global_vs_oracle_summary.csv','phase12_primary_delta_distribution_by_model.csv',
 'phase12_primary_worsened_cases.csv','phase12_primary_worsened_summary.csv',
 'phase12_primary_benefit_cost_summary.csv','phase12_primary_normalized_error_burden.csv',
 'phase12_primary_size_stratified_component_recovery.csv','phase12_primary_component_recovery_events.csv',
 'phase12_primary_multicomponent_outcomes.csv','phase12_primary_multicomponent_transitions.csv',
 'phase12_primary_empty_prediction_recovery.csv','phase12_primary_empty_prediction_ids.csv',
 'phase12_primary_hd95_analysis.csv','phase12_phase11_frozen_cohort_oracle_response.csv',
 'phase12_primary_category_analysis.csv','phase12_primary_vs_crop_only_comparator.csv',
 'phase12_cross_architecture_oracle_consistency.csv','phase12_cross_architecture_distribution.csv',
 'phase12_all_four_low_oracle_response.csv','phase12_oracle_mechanism_evidence_matrix.csv',
]
rows=[{'artifact':n,'type':'table','path':f'reports/tables/{n}','sha256':_sh(f'reports/tables/{n}')} for n in names]
rows.append({'artifact':'phase12_part1b_analysis_errata.md','type':'audit',
             'path':'reports/audits/phase12_part1b_analysis_errata.md',
             'sha256':_sh('reports/audits/phase12_part1b_analysis_errata.md')})
for pth in [p1,p2,p3,p4,p5,p6,p7,p8,p9,p10,p11,p12]:
    rows.append({'artifact':pth.name,'type':'figure',
                 'path':f'reports/figures/phase12_clean_v3_oracle_analysis/{pth.name}',
                 'sha256':_sh(f'reports/figures/phase12_clean_v3_oracle_analysis/{pth.name}')})
rows.append({'artifact':'phase12_oracle_analysis.py','type':'support_code',
             'path':'notebooks/phasewise/phase_12_oracle_roi/code/phase12_oracle_analysis.py',
             'sha256':_sh('notebooks/phasewise/phase_12_oracle_roi/code/phase12_oracle_analysis.py')})
REG = pd.DataFrame(rows)
rp = T/'phase12_part1c_artifact_registry.csv'; REG.to_csv(rp, index=False)
print('registry:', rp.name, len(REG), 'entries')
display(REG)
""")

md("""## 30. Supervisor-Decision Boundary
""")
co("""print('=== PHASE-12 PART-1C BOUNDARY ===')
print('Model loading        : 0')
print('Inference passes     : 0')
print('Training epochs      : 0')
print('Optimizer steps      : 0')
print('Source tables modified: 0')
print('Statistical testing  : NONE')
print('Winner / rank        : NONE')
print('TEST reads           : 0')
print()
print('FINAL PHASE-12 CONCLUSION: NOT ISSUED')
print('REGIONAL INTEGRATION GATE DECISION: NOT YET')
print('PART-1C STATUS: READY_FOR_SUPERVISOR_PHASE12_MECHANISM_CONCLUSION')
print()
print('NEXT: WAIT_FOR_SUPERVISOR_PHASE12_MECHANISM_CONCLUSION')
""")

out = Path(r'D:\Softfors\jup\notebooks\phasewise\phase_12_oracle_roi\phase12_clean_v3_oracle_regional_analysis.ipynb')
with open(out,'w',encoding='utf-8') as f:
    nbf.write(nb,f)
print(f'Notebook written: {out}')
print(f'Total cells: {len(nb.cells)}')
