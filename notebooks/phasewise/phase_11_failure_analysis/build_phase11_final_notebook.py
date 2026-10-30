"""Build the Phase 11 Part 1B final four-model failure-analysis notebook."""
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

md("""# Phase 11 Part 1B — CLEAN-v3 Four-Model Baseline Failure Analysis

**Model:** Gemini 3.1 Pro High · **Date:** 2026-09-21
**Manifest:** `phase4_v3` · **Taxonomy:** `kub_size_clean_v3_v1` · **Split:** KUB VAL (280)

Analyses all four frozen clean-v3 baselines: **UNet, Attention U-Net, UNet++, DeepLabV3+**.

---

> **No winner. No rank. No reference model. No significance testing.**
> These are single-seed development VAL failure analyses.
>
> UNet++ appears as `HISTORICAL_REPLICATION_ANALYSIS_ANCHOR` only — that is a replication
> role for historically anchored strata, **not** a winner / best-model / Phase-12 decision.
>
> TEST is **LOCKED** (0 reads). Phase 12 is **NOT** started.
""")

md("""## 2. Scope and Governance

| Rule | Status |
|---|---|
| Training epochs / optimizer steps / checkpoint writes | **0** |
| TEST image/mask/content reads · metrics · visualizations | **0** |
| Winner declared | **NO** |
| Phase-12 reference model selected | **NO** (`SUPERVISOR_DECISION_REQUIRED`) |
| Statistical significance testing | **NOT PERFORMED** |
| New unauthorized thresholds | **0** |
| Phase 12 started | **NO** |
""")

md("""## 3. Supervisor-Frozen Failure Protocol

The protocol was frozen **before** any current failure inspection
(`reports/audits/phase11_clean_v3_failure_protocol_frozen.json`).
""")
co("""import json
import json
from pathlib import Path as _P
ROOT = _P(r'D:\\Softfors\\jup')
AUD = ROOT/'reports'/'audits'
fz = json.loads((AUD/'phase11_clean_v3_failure_protocol_frozen.json').read_text(encoding='utf-8'))
print('status:', fz['status'], '| recorded before inspection:', fz['recorded_before_current_failure_inspection'])
for k in ['1A_low_dice_stratum','1B_historical_replication_anchor','1C_shared_failure',
          '1D_architecture_disagreement','1E_hd95_stratum','1F_fp_burden',
          '1G_pixel_error_extension','1H_multicomponent','1I_phase12_reference_model']:
    v = fz['frozen_protocol'][k]
    print(f'\\n[{k}]')
    for kk, vv in v.items():
        print(f'   {kk}: {vv}')
""")

md("""## 4. Phase-10 Frozen Inputs
""")
co("""import sys, pandas as pd, numpy as np, json
from pathlib import Path
from PIL import Image
pd.set_option('display.max_rows', None); pd.set_option('display.max_columns', None)
pd.set_option('display.width', None); pd.set_option('display.max_colwidth', None)
PROJECT_ROOT = Path(r'D:\\Softfors\\jup')
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT/'notebooks'/'phasewise'/'phase_11_failure_analysis'/'code'))
import phase11_failure_analysis as fa
import matplotlib.pyplot as plt
%matplotlib inline

per_model = pd.read_csv(fa.TABLES/'phase11_clean_v3_per_model_case_failure_metrics.csv')
cuts     = pd.read_csv(fa.TABLES/'phase11_clean_v3_low_dice_decile_cutoffs.csv')
anchor   = pd.read_csv(fa.TABLES/'phase11_clean_v3_unetpp_failure_decile_cutoffs.csv')
paired   = pd.read_csv(fa.TABLES/'phase11_clean_v3_paired_case_failure_summary.csv')
disag    = pd.read_csv(fa.TABLES/'phase11_clean_v3_architecture_disagreement.csv')
top4     = pd.read_csv(fa.TABLES/'phase11_clean_v3_top_disagreement_cases.csv')
cohort   = pd.read_csv(fa.TABLES/'phase11_clean_v3_hard_case_selection.csv')
summary  = pd.read_csv(fa.TABLES/'phase11_clean_v3_failure_summary_by_model.csv')

print('per-model rows:', len(per_model), '| paired rows:', len(paired), '| disagreement rows:', len(disag))
print()
print(summary[['model','mean_dice','median_dice','empty_predictions','object_recall',
               'missed_components','fp_eval_components']].to_string(index=False))
""")

md("""## 5. KUB-Only VAL Integrity
""")
co("""frame = fa.kub_val_frame()
print('KUB VAL rows   :', len(frame))
print('Categories     :', frame['category'].value_counts().to_dict())
print('Acquisition    :', frame['acquisition_type'].value_counts().to_dict())
assert len(frame)==280
assert frame['category'].value_counts().to_dict()=={'Bladder_Stone':144,'Kidney_Stone':112,'Ureteric_Stone':24}
assert frame['acquisition_type'].value_counts().to_dict()=={'ROI':177,'FULL_FIELD':103}
assert set(per_model['acquisition_type'])<= {'ROI','FULL_FIELD'}
print('\\nKUB-ONLY VAL GATE - PASS (280 = 144+112+24; ROI 177 + FULL_FIELD 103)')
print('No TEST rows present.')
""")

md("""## 6. Prediction Reproduction Gate

Aggregate macro Dice must reproduce the frozen Phase-10 authoritative values within
**1e-4**. (Recomputed with canonical loader, batch 4, AMP, `round()` resize math.)
""")
co("""gate = pd.DataFrame([
 {'model': fa.DISPLAY[k], 'recomputed': float(per_model[per_model.model==k]['dice'].mean()),
  'authoritative': fa.AUTHORITATIVE[k],
  'abs_diff': abs(float(per_model[per_model.model==k]['dice'].mean()) - fa.AUTHORITATIVE[k])}
 for k in fa.MODELS])
gate['pass_1e-4'] = gate['abs_diff'] < fa.MATERIAL_TOL
display(gate)
assert gate['pass_1e-4'].all(), 'CHECK_REQUIRED: aggregate reproduction exceeded 1e-4'
print('\\nREPRODUCTION GATE - PASS (all models within 1e-4)')
print('Authoritative Phase-10 values retained unchanged.')
""")

md("""## 7. Model-Specific Clean-v3 Decile Cutoffs

Bottom Dice decile per model, `np.quantile(values, 0.10)` (default linear, float64).
**Ties included**; counts need not be exactly 28.
""")
co("""display(cuts[['model','n','q10_cutoff','count_le_cutoff','prevalence','tie_count_at_cutoff']])
print()
print('Historical v2 cutoff 0.5461063385009766 is provenance only and was NOT reused.')
""")

md("""## 8. Historical UNet++ Replication Cutoffs

UNet++ anchored strata (HD95/FP) — `HISTORICAL_REPLICATION_ANALYSIS_ANCHOR` only.
""")
co("""for c in anchor.columns:
    print(f'  {c}: {anchor.loc[0, c]}')
print()
print('v2 values shown in *_provenance columns are HISTORICAL only and were not applied.')
""")

md("""## 9. Empty-Prediction Analysis
""")
co("""emp = pd.read_csv(fa.TABLES/'phase11_clean_v3_empty_prediction_analysis.csv')
display(emp)
print()
print('Cases by number of models with empty prediction:')
print(paired['empty_prediction_model_count'].value_counts().sort_index().to_string())
print()
print('Empty predictions are concentrated in FULL_FIELD (tiny targets); ROI almost never empty.')
""")

md("""## 10–11. Object-Detection Analysis (and FULL_FIELD size strata)

8-connectivity, `>= 1 px` overlap. Detection measured in **evaluation-512 space**;
size strata from **original native FULL_FIELD** space (`kub_size_clean_v3_v1`).
""")
co("""display(summary[['model','gt_eval_components','detected_components','missed_components',
                 'object_recall','fp_eval_components']])
print()
size = pd.read_csv(fa.TABLES/'phase11_clean_v3_fullfield_size_stratum_object_analysis.csv')
display(size[['model','stratum','GT_components','COMPLETE_DETECTION','PARTIAL_DETECTION','COMPLETE_MISS']])
print()
print('ROI components are ROI_NOT_PRIMARY_BINNED - never size-binned.')
""")

co("""fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle('Phase 11 CLEAN-v3 — object detection (descriptive, single seed)', fontsize=11)
ax = axes[0]
w = 0.2; x = np.arange(len(fa.MODELS))
for i, strat in enumerate(['TINY','SMALL','MEDIUM','LARGE']):
    s = size[size.stratum==strat].set_index('model')
    vals = [float(s.loc[fa.DISPLAY[k],'COMPLETE_DETECTION']) for k in fa.MODELS]
    ax.bar(x + (i-1.5)*w, vals, w, label=strat)
ax.set_xticks(x); ax.set_xticklabels([fa.DISPLAY[k] for k in fa.MODELS], fontsize=8)
ax.set_ylabel('Components in completely-detected cases'); ax.set_title('FULL_FIELD size strata')
ax.legend(fontsize=7); ax.grid(True, alpha=.3, axis='y')

ax = axes[1]
ax.bar([fa.DISPLAY[k] for k in fa.MODELS], summary['object_recall'], color='steelblue')
ax.set_ylabel('Object recall (eval-512 space)'); ax.set_title('Overall object recall')
ax.tick_params(axis='x', labelsize=8); ax.grid(True, alpha=.3, axis='y')
plt.tight_layout(rect=[0,0,1,0.93])
p1 = fa.FIGURES/'phase11_clean_v3_object_detection.png'; fig.savefig(p1, dpi=140, bbox_inches='tight'); plt.close(fig)
print('saved', p1.name)
from IPython.display import Image as IPImage
display(IPImage(filename=str(p1)))
""")

md("""## 12. Multi-Component Analysis (8-connectivity)
""")
co("""mc = pd.read_csv(fa.TABLES/'phase11_clean_v3_multicomponent_analysis.csv')
display(mc[['model','multicomponent_cases','COMPLETE_DETECTION','PARTIAL_DETECTION','COMPLETE_MISS','connectivity']])
print()
print('Membership: ORIGINAL_NATIVE (8-conn component count > 1).')
print('Detection : EVALUATION_512 (8-conn, >=1 px overlap).')
fig, ax = plt.subplots(figsize=(8,4))
idx = np.arange(len(mc)); w=0.26
for i, c in enumerate(['COMPLETE_DETECTION','PARTIAL_DETECTION','COMPLETE_MISS']):
    ax.bar(idx + (i-1)*w, mc[c], w, label=c)
ax.set_xticks(idx); ax.set_xticklabels(mc['model'], fontsize=8)
ax.set_ylabel('multi-component cases'); ax.set_title('Multi-component detection (descriptive)')
ax.legend(fontsize=7); ax.grid(True, alpha=.3, axis='y')
plt.tight_layout()
p2 = fa.FIGURES/'phase11_clean_v3_multicomponent.png'; fig.savefig(p2, dpi=140, bbox_inches='tight'); plt.close(fig)
display(IPImage(filename=str(p2)))
""")

md("""## 13. Boundary / HD95 Analysis (validity-aware)
""")
co("""bd = pd.read_csv(fa.TABLES/'phase11_clean_v3_boundary_hd95_summary.csv')
display(bd[['model_display','n_total','n_valid','n_invalid','valid_rate','median_hd95','q90_hd95_valid']])
print()
print('Invalid HD95 cases (empty prediction / empty GT) are counted explicitly and never')
print('silently dropped from population accounting.')
""")

md("""## 14. False-Positive Component Burden
""")
co("""fpb = pd.read_csv(fa.TABLES/'phase11_clean_v3_fp_burden_summary.csv')
display(fpb[['model_display','mean','median','q90','max']])
print()
print('HIGH_FP_DECILE is frozen only for the UNet++ anchor (fp_eval_components >= clean-v3 Q90).')
print('Other models are reported descriptively; no new FP threshold created.')
""")

md("""## 15. TP / FP / FN Descriptive Extension  (`CLEAN_V3_DESCRIPTIVE_EXTENSION`)
""")
co("""px = pd.read_csv(fa.TABLES/'phase11_clean_v3_pixel_error_extension.csv')
display(px[['model_display','acquisition_type','mean_tp','mean_fp','mean_fn',
            'mean_fp_frac','mean_fn_frac','mean_area_ratio','status']])
print()
print('These are DESCRIPTIVE extensions; they do NOT redefine historical failure strata')
print('and create no deployment/tuning thresholds.')
""")

md("""## 16. Shared Failure — ALL_FOUR_LOW (frozen primary definition)
""")
co("""print('ALL_FOUR_LOW count:', int(paired['ALL_FOUR_LOW'].sum()), '/', len(paired))
print('low_model_count distribution:', paired['low_model_count'].value_counts().sort_index().to_dict())
print()
ids = sorted(paired.loc[paired['ALL_FOUR_LOW'],'sample_id'].tolist())
print('ALL_FOUR_LOW sample_ids:')
for s in ids: print('  ', s)
print()
print('Stratification of ALL_FOUR_LOW:')
sub_low = paired[paired['ALL_FOUR_LOW']]
print('  by acquisition:', sub_low['acquisition_type'].value_counts().to_dict())
print('  by category   :', sub_low['category'].value_counts().to_dict())
print()
print('Primary definition uses per-model clean Q10 flags - NOT mean/median Dice.')
print('Mean/median Dice are reported only descriptively (dice_mean/dice_median columns).')
""")

md("""## 17–18. Architecture Disagreement (continuous) and Regime Stratification

`dice_range = max(Dice) − min(Dice)` — **continuous, no binary threshold**.
""")
co("""print('dice_range: mean %.4f  median %.4f  max %.4f' % (disag.dice_range.mean(), disag.dice_range.median(), disag.dice_range.max()))
print()
regime = pd.read_csv(fa.TABLES/'phase11_clean_v3_failure_by_acquisition.csv')
display(regime[['model_display','acquisition_type','n','mean_dice','empty_pred_pct','object_recall']])
print()
print('MANDATORY: FULL_FIELD (103) and ROI (177) are reported separately - never pooled alone.')
""")

co("""fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))
fig.suptitle('Phase 11 CLEAN-v3 — shared failure, disagreement, regime gap (descriptive)', fontsize=11)
ax = axes[0]
ax.bar([str(i) for i in range(5)], [int((paired.low_model_count==i).sum()) for i in range(5)], color='steelblue')
ax.set_xlabel('low_model_count'); ax.set_ylabel('cases'); ax.set_title('Models flagging case low (0..4)')
ax.grid(True, alpha=.3, axis='y')
ax = axes[1]
ax.hist(disag.dice_range, bins=40, color='indianred')
ax.set_xlabel('dice_range (max - min)'); ax.set_ylabel('cases'); ax.set_title('Disagreement (no threshold)')
ax.grid(True, alpha=.3)
ax = axes[2]
w=0.35; x=np.arange(len(fa.MODELS))
ff = regime[regime.acquisition_type=='FULL_FIELD'].set_index('model_display')['mean_dice']
roi = regime[regime.acquisition_type=='ROI'].set_index('model_display')['mean_dice']
ax.bar(x-w/2, [ff[fa.DISPLAY[k]] for k in fa.MODELS], w, label='FULL_FIELD')
ax.bar(x+w/2, [roi[fa.DISPLAY[k]] for k in fa.MODELS], w, label='ROI')
ax.set_xticks(x); ax.set_xticklabels([fa.DISPLAY[k] for k in fa.MODELS], fontsize=8)
ax.set_ylabel('mean Dice'); ax.set_title('Regime gap'); ax.legend(fontsize=7); ax.grid(True, alpha=.3, axis='y')
plt.tight_layout(rect=[0,0,1,0.9])
p3 = fa.FIGURES/'phase11_clean_v3_shared_and_disagreement.png'; fig.savefig(p3, dpi=140, bbox_inches='tight'); plt.close(fig)
display(IPImage(filename=str(p3)))
""")

md("""## 19. Category-Stratified Failures (metadata subgroups)
""")
co("""cat = pd.read_csv(fa.TABLES/'phase11_clean_v3_failure_by_category.csv')
display(cat[['model_display','category','n','mean_dice','empty_pred_pct','object_recall']])
print()
print('Bladder/Kidney/Ureteric are SUBGROUP METADATA of a binary segmentation target,')
print('not pixel classes. Ureteric n=24 - do not overinterpret.')
""")

md("""## 20. Historical-Style Deterministic Hard-Case Cohort (UNet++ anchor)
""")
co("""display(cohort[['selection_order','stratum','sample_id','acquisition','dice',
                'prediction_empty','missed_gt_eval_components','fp_eval_components']])
print()
print('target 16 | actual', len(cohort), '| strata:', cohort['stratum'].value_counts().to_dict())
print('acquisition mix:', cohort['acquisition'].value_counts().to_dict())
print()
print('Selection is deterministic and prediction-dependent by design (failure cohort).')
print('It must NOT be confused with the prediction-independent Phase-10 gallery.')
""")

md("""## 21. Hard-Case Four-Model Visual Analysis
""")
co("""import numpy as np
sel = cohort['sample_id'].tolist()
preds = fa.predict_subset(sel, frame)
rows = cohort.set_index('sample_id')
paths = []
for sid in sel:
    rec = preds[sid]; gt = rec['gt']; src = rec['src']; meta = rec['meta']
    r = rows.loc[sid]
    stratum = fa.size_stratum_of_case(gt, meta['acquisition'])
    ncol = 2 + 3*len(fa.MODELS)
    fig, axes = plt.subplots(1, ncol, figsize=(2.6*ncol, 3.4))
    fig.suptitle(f"Hard case {int(r['selection_order'])} · {r['stratum']} · {sid[:12]} · "
                 f"{meta['category']} · {meta['acquisition']} · native {meta['native'][1]}x{meta['native'][0]} · "
                 f"size: {stratum}\\nanchor=UNet++ (HISTORICAL_REPLICATION_ANALYSIS_ANCHOR)",
                 fontsize=10)
    axes[0].imshow(src, cmap='gray', vmin=0, vmax=255); axes[0].set_title('Source', fontsize=8); axes[0].axis('off')
    axes[1].imshow(gt, cmap='gray', vmin=0, vmax=1);   axes[1].set_title('Binary GT', fontsize=8); axes[1].axis('off')
    for i, k in enumerate(fa.MODELS):
        prob = rec['preds'][k]
        pred = (prob >= fa.THRESHOLD).astype(np.uint8)
        gtr = np.array(Image.fromarray(gt).resize((pred.shape[1], pred.shape[0]), Image.NEAREST))
        m = fa._case_metrics(gtr, prob)
        em = fa._error_map(gtr, pred)
        b = 2 + i*3
        axes[b].imshow(prob, cmap='viridis', vmin=0, vmax=1)
        axes[b].set_title(f"{fa.DISPLAY[k]}\\nprob", fontsize=8); axes[b].axis('off')
        axes[b+1].imshow(pred, cmap='gray', vmin=0, vmax=1)
        axes[b+1].set_title('pred t=0.5', fontsize=8); axes[b+1].axis('off')
        axes[b+2].imshow(em)
        axes[b+2].set_title(f"err map\\nDice={m['dice']:.3f} empty={m['prediction_empty']}", fontsize=8)
        axes[b+2].axis('off')
    plt.tight_layout(rect=[0, 0.02, 1, 0.86])
    fp_ = fa.FIGURES/f"phase11_clean_v3_hardcase_{int(r['selection_order']):02d}.png"
    fig.savefig(fp_, dpi=110, bbox_inches='tight'); plt.close(fig); paths.append(fp_)
print('generated', len(paths), 'hard-case panels')
""")

co("""for fp_ in paths:
    print(fp_.name)
    display(IPImage(filename=str(fp_)))
""")

md("""## 22. Top-Disagreement Visual Analysis (diagnostic only)

Four highest `dice_range` cases, sorted `dice_range desc, sample_id asc`.
`ARCHITECTURE_DISAGREEMENT_DESCRIPTIVE_ONLY`.
""")
co("""display(top4[['sample_id','dice_range','dice_min','dice_max']]
        .assign(status='DESCRIPTIVE_DISAGREEMENT_DIAGNOSTIC_ONLY'))
print()
print('These are NOT merged into the historical hard cohort unless independently selected.')
seld = top4['sample_id'].tolist()
overlap = [s for s in seld if s in set(cohort['sample_id'])]
print('overlap with hard cohort:', overlap if overlap else 'NONE')
preds_d = fa.predict_subset(seld, frame)
dp = []
for sid in seld:
    rec = preds_d[sid]; gt = rec['gt']; src = rec['src']; meta = rec['meta']
    rr = disag[disag.sample_id==sid].iloc[0]
    ncol = 2 + 3*len(fa.MODELS)
    fig, axes = plt.subplots(1, ncol, figsize=(2.6*ncol, 3.4))
    fig.suptitle(f"Disagreement · {sid[:12]} · {meta['category']} · {meta['acquisition']} · "
                 f"dice_range={rr['dice_range']:.3f} (min {rr['dice_min']:.3f} / max {rr['dice_max']:.3f})\\n"
                 f"ARCHITECTURE_DISAGREEMENT_DESCRIPTIVE_ONLY", fontsize=10)
    axes[0].imshow(src, cmap='gray', vmin=0, vmax=255); axes[0].set_title('Source', fontsize=8); axes[0].axis('off')
    axes[1].imshow(gt, cmap='gray', vmin=0, vmax=1); axes[1].set_title('Binary GT', fontsize=8); axes[1].axis('off')
    for i, k in enumerate(fa.MODELS):
        prob = rec['preds'][k]; pred = (prob >= fa.THRESHOLD).astype(np.uint8)
        gtr = np.array(Image.fromarray(gt).resize((pred.shape[1], pred.shape[0]), Image.NEAREST))
        m = fa._case_metrics(gtr, prob); b = 2 + i*3
        axes[b].imshow(prob, cmap='viridis', vmin=0, vmax=1)
        axes[b].set_title(f"{fa.DISPLAY[k]}\\nprob", fontsize=8); axes[b].axis('off')
        axes[b+1].imshow(pred, cmap='gray', vmin=0, vmax=1)
        axes[b+1].set_title('pred', fontsize=8); axes[b+1].axis('off')
        axes[b+2].imshow(fa._error_map(gtr, pred))
        axes[b+2].set_title(f"err map\\nDice={m['dice']:.3f}", fontsize=8); axes[b+2].axis('off')
    plt.tight_layout(rect=[0, 0.02, 1, 0.86])
    fq = fa.FIGURES/f"phase11_clean_v3_disagreement_{sid[:8]}.png"
    fig.savefig(fq, dpi=110, bbox_inches='tight'); plt.close(fig); dp.append(fq)
print('generated', len(dp), 'disagreement panels')
""")

co("""for fq in dp:
    print(fq.name)
    display(IPImage(filename=str(fq)))
""")

md("""## 23. Phase-11 → Phase-12 Bridge Evidence

`OBSERVED_DIAGNOSTIC_EVIDENCE`. We state whether the clean-v3 pattern motivates the
historical Oracle-ROI rationale — **without** selecting a Phase-12 model and **without**
claiming ROI solves the problem.
""")
co("""bridge = pd.read_csv(fa.TABLES/'phase11_clean_v3_phase12_bridge_evidence.csv')
display(bridge[['evidence','value','verdict','status']])
print()
print('No Phase-12 reference model is selected here: SUPERVISOR_DECISION_REQUIRED.')
""")

md("""## 24. Limitations

- Single seed (42); no Phase-29 reproducibility, no Phase-31 significance testing.
- VAL only (280 KUB cases); TEST locked to Phase 39 — no generalization claim.
- Ureteric_Stone n=24 — unstable subgroup.
- Component-space attribution across native (size) vs evaluation-512 (detection) is
  approximate; resize can merge components, so per-component cross-space claims are
  reported at case level where attribution is uncertain.
- HD95 invalid cases (empty prediction / empty GT) counted but excluded from HD95 statistics.
""")

md("""## 25. Historical-v2 Separation

| Quantity | HISTORICAL_v2 (provenance only) | CLEAN_v3 (used) |
|---|---|---|
| Dice Q10 | 0.5461063385009766 | per-model recomputed (see §7) |
| HD95 Q90 | 83.07246563841615 | 85.24095485204775 (UNet++ valid-only) |
| FP cutoff | 4 | 5.0 (UNet++ clean Q90) |
| Size taxonomy | `kub_size_v1` | `kub_size_clean_v3_v1` |
| VAL cases | 283 | 280 |

v2 values were **not** used as clean-v3 thresholds.
""")

for i, k in enumerate(['unet','attention_unet','unetpp','deeplabv3plus'], start=26):
    d = {'unet':'UNet','attention_unet':'Attention U-Net','unetpp':'UNet++','deeplabv3plus':'DeepLabV3+'}[k]
    md(f"""## {i}. Complete Epoch Table — {d}

Upstream frozen training provenance, read-only from the Phase-10 normalized epoch table.
**Every epoch row displayed.**
""")
    co(f"""t = pd.read_csv(fa.PHASE10_EPOCH_TABLES['{k}'])
eps = t['epoch'].astype(int).tolist(); exp = list(range(1, len(t)+1))
print('=== UPSTREAM {d} ===')
print('  rows:', len(t), '| expected:', fa.EXPECTED_EPOCH_ROWS['{k}'])
print('  first/last:', min(eps), '/', max(eps))
print('  missing   :', sorted(set(exp)-set(eps)))
print('  duplicates:', sorted({{e for e in eps if eps.count(e)>1}}))
print('  contiguous:', eps==exp)
assert len(t)==fa.EXPECTED_EPOCH_ROWS['{k}'] and eps==exp
print()
display(t)
""")

md("""## 30. Phase-11 Conclusion

**DESCRIPTIVE CLEAN-v3 BASELINE COMPARISON OF FAILURES — COMPLETE.**

Observed patterns (no ranking):
- A large and consistent **regime gap**: ROI crops score ~0.23 mean Dice higher than
  FULL_FIELD for every model; empty predictions and missed components concentrate in
  FULL_FIELD.
- **Tiny and small FULL_FIELD targets** are the weakest group; a substantial share of
  native TINY components sit in partially-detected or missed cases for all four models.
- **Multi-component** masks are frequently only partially recovered (16–22 partial/miss
  cases per model).
- **Shared difficulty exists**: 12/280 cases are ALL_FOUR_LOW, and 23 cases see ≥3 models
  lose components — these are shared hard cases, not architecture-specific.
- **FP burden differs by architecture** (UNet / Attention U-Net ≈ 10 FP components per case;
  UNet++ ≈ 1.7; DeepLabV3+ ≈ 0.24) — descriptive, not a quality ranking.
- Boundary error (median HD95 ~33–45 px) is secondary to detection/localization failure.

**No winner is declared; no reference model is selected; no significance is claimed.**
The evidence motivates — but does not prove — that increased effective local resolution
(Oracle ROI) is worth testing, consistent with the historical rationale.
""")

md("""## 31. Artifact Registry
""")
co("""def _sh(rel):
    q = PROJECT_ROOT/rel
    return fa.sha256_file(q) if q.exists() else 'N/A'
names = [
 'phase11_clean_v3_per_model_case_failure_metrics.csv',
 'phase11_clean_v3_paired_case_failure_summary.csv',
 'phase11_clean_v3_low_dice_decile_cutoffs.csv',
 'phase11_clean_v3_unetpp_failure_decile_cutoffs.csv',
 'phase11_clean_v3_architecture_disagreement.csv',
 'phase11_clean_v3_top_disagreement_cases.csv',
 'phase11_clean_v3_hard_case_selection.csv',
 'phase11_clean_v3_failure_summary_by_model.csv',
 'phase11_clean_v3_phase12_bridge_evidence.csv',
 'phase11_clean_v3_failure_by_acquisition.csv',
 'phase11_clean_v3_failure_by_category.csv',
 'phase11_clean_v3_empty_prediction_analysis.csv',
 'phase11_clean_v3_boundary_hd95_summary.csv',
 'phase11_clean_v3_fp_burden_summary.csv',
 'phase11_clean_v3_pixel_error_extension.csv',
 'phase11_clean_v3_multicomponent_analysis.csv',
 'phase11_clean_v3_fullfield_size_stratum_object_analysis.csv',
]
rowsr = [{'artifact': n, 'path': f'reports/tables/{n}', 'sha256': _sh(f'reports/tables/{n}')} for n in names]
rowsr += [{'artifact': p_.name, 'path': f'reports/figures/{p_.name}', 'sha256': _sh(f'reports/figures/{p_.name}')} for p_ in paths]
rowsr += [{'artifact': fq.name, 'path': f'reports/figures/{fq.name}', 'sha256': _sh(f'reports/figures/{fq.name}')} for fq in dp]
rowsr += [{'artifact': 'phase11_failure_analysis.py',
           'path': 'notebooks/phasewise/phase_11_failure_analysis/code/phase11_failure_analysis.py',
           'sha256': _sh('notebooks/phasewise/phase_11_failure_analysis/code/phase11_failure_analysis.py')}]
REG = pd.DataFrame(rowsr)
rp = fa.TABLES/'phase11_clean_v3_failure_analysis_artifact_registry.csv'
REG.to_csv(rp, index=False)
print('registry:', rp.name, len(REG), 'entries')
display(REG)
""")

md("""## 32. Phase-12 Boundary
""")
co("""print('=== PHASE-11 / PHASE-12 BOUNDARY ===')
print('Training epochs                 : 0')
print('Optimizer steps                 : 0')
print('Checkpoint writes               : 0')
print('Histories / configs modified    : 0')
print('TEST image/mask/content reads   : 0')
print('TEST metrics / visualizations   : 0')
print('New unauthorized thresholds     : 0')
print('Winner declared                 : NO')
print('Phase-12 reference model        : NOT SELECTED (SUPERVISOR_DECISION_REQUIRED)')
print('Significance testing            : NOT PERFORMED')
print('Phase 12 started                : NO')
print()
print('PHASE 11: COMPLETE')
print('NEXT: WAIT_FOR_SUPERVISOR_PHASE12_DECISION')
""")

out = Path(r'D:\Softfors\jup\notebooks\phasewise\phase_11_failure_analysis\phase11_clean_v3_baseline_failure_analysis.ipynb')
with open(out,'w',encoding='utf-8') as f:
    nbf.write(nb,f)
print(f'Notebook written: {out}')
print(f'Total cells: {len(nb.cells)}')
