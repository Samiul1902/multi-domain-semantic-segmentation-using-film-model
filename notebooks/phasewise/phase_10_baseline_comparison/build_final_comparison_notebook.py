"""Build the Phase 10 FINAL four-model clean-v3 comparison notebook."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(r'D:\Softfors\jup')))

import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

nb = new_notebook()
nb.metadata['kernelspec'] = {'display_name': 'jup-venv', 'language': 'python', 'name': 'jup-venv'}
nb.metadata['language_info'] = {'name': 'python', 'version': '3.13.12'}

def add_md(t): nb.cells.append(new_markdown_cell(t))
def add_code(t): nb.cells.append(new_code_cell(t))

# 1 Title
add_md("""# Phase 10 — CLEAN-v3 KUB Baseline Comparison (FINAL, four models)

**Model:** Gemini 3.1 Pro High
**Date:** 2026-09-21
**Manifest:** `phase4_v3` | **Taxonomy:** `kub_size_clean_v3_v1`

Compares four already-frozen clean-v3 KUB baseline runs:

| Model | Experiment | Best epoch | VAL Dice |
|---|---|---|---|
| UNet | `phase9_kub_unet_baseline_seed42_512_clean_v3` | 44 | 0.7406133413314819 |
| Attention U-Net | `phase10_kub_attention_unet_seed42_512_clean_v3` | 54 | 0.7525129853960107 |
| UNet++ | `phase10_kub_unetpp_seed42_512_clean_v3` | 70 | 0.7641595156062713 |
| DeepLabV3+ | `phase10_kub_deeplabv3plus_seed42_512_clean_v3` | 52 | 0.7509140344161673 |

---

> **READ-ONLY.** No retraining, no checkpoint writes, no config changes, no threshold
> tuning, no TEST access.
>
> **NO WINNER IS DECLARED.** All runs are **single-seed (42) descriptive VAL evidence**.
> No statistical significance testing has been performed (Phase 29 / Phase 31 have not run).
> **TEST remains locked until Phase 39.**
>
> The ordering of rows in tables below is bookkeeping, **not a ranking**.
""")

# 2 Scientific objective
add_md("""## 2. Scientific Objective

Produce a rigorous **descriptive** clean-v3 comparison of four KUB baseline architectures on
identical data and protocol, then close Phase 10.

Specifically:
1. Verify all four frozen runs are intact (immutability by SHA).
2. Confirm the four runs are scientifically comparable (same data, protocol, target, seed).
3. Reconstruct **complete epoch-by-epoch tables** for every model (one row per epoch).
4. Re-run read-only inference on the **same 280 KUB VAL cases** with all four `best.pt`.
5. Reproduce the authoritative aggregate metrics from the paired table.
6. Report category- and acquisition-stratified results, plus descriptive paired deltas.
7. Show a frozen 16-case paired qualitative comparison.

**Non-objectives:** declaring a winner, significance testing, ranking, touching TEST,
starting Phase 11.
""")

# 3 Governance / TEST lock
add_md("""## 3. Governance and TEST Lock

| Rule | Status |
|---|---|
| TEST image/mask/content reads | **0** |
| TEST metrics / visualizations | **0** |
| TEST dataset instantiated | **NO** |
| Retraining | **NO** |
| Checkpoint / history / config modification | **NO** |
| Threshold tuning | **NO** (fixed 0.5) |
| Statistical significance testing | **NOT PERFORMED** |
| Winner declaration | **NO** |
| Phase 11 | **NOT STARTED** |

`KUBDataset` blocks TEST construction unless `allow_test=True`, which is never set here.
""")

# 4 Frozen experiments
add_md("""## 4. Four Frozen Experiments
""")
add_code("""%matplotlib inline
import sys, json
from pathlib import Path
import numpy as np, pandas as pd, torch
import matplotlib.pyplot as plt
from PIL import Image
from IPython.display import display

# FULL display of all epoch rows - hard requirement
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

PROJECT_ROOT = Path(r'D:\\Softfors\\jup')
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'notebooks' / 'phasewise' / 'phase_10_baseline_comparison' / 'code'))
import phase10_final_comparison as fc

for k in fc.MODEL_ORDER:
    m = fc.MODELS[k]
    a = m['authoritative']
    print(f"{m['display']:16s} {m['experiment_id']}")
    print(f"{'':16s} best_ep={m['expected_best_epoch']}  Dice={a['dice']:.16f}  IoU={a['iou']:.16f}")
    print(f"{'':16s} Prec={a['precision']:.16f}  Recall={a['recall']:.16f}")
    print()
""")

# 5 Immutability
add_md("""## 5. Artifact Immutability Verification
""")
add_code("""imm = fc.verify_immutability()
rows=[]
for k,v in imm.items():
    rows.append({'model': fc.MODELS[k]['display'], 'experiment_id': v['experiment_id'],
                 'history_sha': v['history_sha'][:16]+'...', 'history_match': v['history_sha_match'],
                 'best_sha': v['best_sha'][:16]+'...', 'best_match': v['best_sha_match'],
                 'latest_sha': v['latest_sha'][:16]+'...',
                 'reviewer_nb_sha': v['reviewer_notebook_sha'][:16]+'...'})
display(pd.DataFrame(rows))
assert all(v['all_match'] for v in imm.values()), 'Immutability FAILED - CHECK_REQUIRED'
print('\\nALL FOUR RUNS IMMUTABLE - PASS')
""")

# 6 Protocol comparability
add_md("""## 6. Protocol Comparability

All four runs share the same data and training protocol; the only scientific difference is
**architecture**.
""")
add_code("""prot=[]
for k in fc.MODEL_ORDER:
    cfg = fc.yaml.safe_load(fc.MODELS[k]['config'].read_text(encoding='utf-8'))
    t, m = cfg['training'], cfg['model']
    prot.append({'model': fc.MODELS[k]['display'],
        'manifest': cfg['manifest_version'], 'taxonomy': cfg['taxonomy_id'],
        'resolution': cfg['input_resolution'], 'in_ch': m['input_channels'], 'out_ch': m['output_channels'],
        'loss': f"{cfg['loss']['name']} {cfg['loss']['bce_weight']}/{cfg['loss']['dice_weight']}",
        'optimizer': cfg['optimizer']['name'], 'lr': cfg['optimizer']['learning_rate'],
        'wd': cfg['optimizer']['weight_decay'],
        'scheduler': f"{cfg['scheduler']['name']} T_max={cfg['scheduler']['max_epochs']}",
        'batch': t['batch_size'], 'accum': t['gradient_accumulation_steps'],
        'amp': t['amp'], 'seed': t['seed'], 'max_epochs': t['max_epochs'],
        'patience': t['early_stopping_patience'], 'threshold': t['threshold'],
        'monitor': t['monitor'], 'allow_test': cfg['allow_test']})
P = pd.DataFrame(prot)
display(P.set_index('model').T)

# gates
assert (P['manifest']=='phase4_v3').all()
assert (P['taxonomy']=='kub_size_clean_v3_v1').all()
assert (P['resolution']==512).all() and (P['in_ch']==1).all() and (P['out_ch']==1).all()
assert (P['seed']==42).all() and (P['threshold']==0.5).all()
assert (~P['allow_test']).all()
print('\\nCOMPARABILITY - PASS (identical data/protocol; only architecture differs)')
""")

# 7 Epoch normalization contract
add_md("""## 7. Epoch-Table Normalization Contract

Physical histories use slightly different column names:
Phase 09 uses `val_macro_dice`, Phase 10 uses `val_dice`. Reviewer tables normalise to
canonical names. **Original history files are never modified.** No metric is fabricated —
unavailable fields are `N/A`.

Derived reviewer-only columns: `delta_val_dice_vs_previous_epoch`, `delta_best_metric`,
`is_new_best`, `is_best_epoch`, `epochs_since_best`.
""")
add_code("""tables = {k: fc.build_epoch_table(k) for k in fc.MODEL_ORDER}
vers   = {k: fc.verify_epoch_table(k, tables[k]) for k in fc.MODEL_ORDER}
paths  = {k: fc.save_epoch_table(k, tables[k]) for k in fc.MODEL_ORDER}
for k in fc.MODEL_ORDER:
    p = paths[k]
    print(f"{fc.MODELS[k]['display']:16s} -> {p.name}  SHA {fc.sha256_file(p)}")
long = fc.build_long_table(tables)
lp = fc.TABLES / 'phase10_final_all_models_epoch_results_long.csv'
long.to_csv(lp, index=False)
print(f"\\nMODEL_EPOCH_LONG_TABLE -> {lp.name}  rows={len(long)}  SHA {fc.sha256_file(lp)}")
assert len(long) == 280, f'long table must be 280 rows, got {len(long)}'
print('NOTE: 280 here = 59+69+85+67 MODEL-EPOCH rows, distinct from the 280 VAL cases.')
""")

# 8-11 per-model complete epoch tables
for idx, k in enumerate(['unet', 'attention_unet', 'unetpp', 'deeplabv3plus'], start=8):
    disp = {'unet': 'UNet', 'attention_unet': 'Attention U-Net',
            'unetpp': 'UNet++', 'deeplabv3plus': 'DeepLabV3+'}[k]
    add_md(f"""## {idx}. Complete Epoch Table — {disp}

Every completed epoch is displayed below (**untruncated**).
""")
    add_code(f"""t = tables['{k}']
v = vers['{k}']
print('=== INTEGRITY: {disp} ===')
for kk, vv in v.items(): print(f'  {{kk}}: {{vv}}')
print()
assert v['integrity_pass'] and v['row_count_matches_history']
print(f"Rendering ALL {{len(t)}} epoch rows for {disp}:")
display(t)
""")

# 12 Training dynamics
add_md("""## 12. Training Dynamics (descriptive)

Six panels across all four models. Curves are descriptive — the visually highest curve is
**not** called a winner.
""")
add_code("""p_dyn = fc.plot_training_dynamics(tables)
print('Saved:', p_dyn)
from IPython.display import Image as IPImage
display(IPImage(filename=str(p_dyn)))
""")

# 13 KUB-only VAL population
add_md("""## 13. KUB-Only VAL Population
""")
add_code("""val = fc.get_kub_val()
print('KUB VAL rows:', len(val))
print('Categories  :', val['category'].value_counts().to_dict())
print('Acquisition :', val['acquisition_type'].value_counts().to_dict())
assert len(val)==280
assert set(val['category'])=={'Kidney_Stone','Bladder_Stone','Ureteric_Stone'}
assert val['acquisition_type'].value_counts().to_dict()=={'ROI':177,'FULL_FIELD':103}
print('\\nKUB-ONLY VAL - PASS (280 = 144 + 112 + 24; ROI 177 + FULL_FIELD 103)')
""")

# 14 Paired inference integrity
add_md("""## 14. Paired 280-Case Inference Integrity

All four `best.pt` run deterministically on the **same** 280 KUB VAL cases, threshold 0.5,
no augmentation, no checkpoint switching.
""")
add_code("""paired = pd.read_csv(fc.TABLES / 'phase10_clean_v3_paired_val_case_metrics.csv')
need = [f'{m}_{x}' for m in fc.MODEL_ORDER for x in ['dice','iou','precision','recall']]
print('rows            :', len(paired))
print('unique samples  :', paired['sample_id'].nunique())
print('all model cols  :', all(c in paired.columns for c in need))
print('any NaN         :', bool(paired[need].isna().any().any()))
assert len(paired)==280 and paired['sample_id'].nunique()==280
assert all(c in paired.columns for c in need) and not paired[need].isna().any().any()
print('\\nPAIRED INFERENCE - PASS (280 cases x 4 models, no missing predictions)')
""")

# 15 Aggregate reproduction
add_md("""## 15. Aggregate Metric Reproduction Gate

Macro metrics recomputed from the paired table must reproduce the accepted authoritative
values within floating-point tolerance. Accepted metrics are **never** silently replaced.
""")
add_code("""overall = pd.read_csv(fc.TABLES / 'phase10_clean_v3_overall_baseline_comparison.csv')
STRICT, MATERIAL = 1e-6, 1e-4
res=[]
for _, r in overall.iterrows():
    d = r['reproduction_abs_diff']
    res.append({'model': r['model'], 'recomputed_dice': r['val_macro_dice'],
                'authoritative_dice': r['authoritative_dice'], 'abs_diff': d,
                'pass_strict_1e-6': d < STRICT, 'pass_material_1e-4': d < MATERIAL})
R = pd.DataFrame(res)
display(R)
print()
print('fp16 note: residuals at the 1e-6..1e-5 level arise because training-time validation')
print('ran AMP fp16 with batch=4 while this paired re-inference uses batch=1; these are')
print('floating-point rounding differences, not metric differences.')
assert (R['pass_material_1e-4']).all(), 'Material reproduction FAILED - CHECK_REQUIRED'
print('\\nAGGREGATE REPRODUCTION - PASS at material tolerance (1e-4)')
print('Authoritative metrics retained unchanged.')
""")

# 16 Overall descriptive comparison
add_md("""## 16. Overall Descriptive Comparison

Descriptive only — **no rank, no winner, no score, no tier column.**
""")
add_code("""show = overall.drop(columns=[c for c in ['reproduction_abs_diff'] if c in overall.columns])
display(show.set_index('model').T)
print()
print('These are SINGLE-SEED DESCRIPTIVE VAL results. Listing them is bookkeeping, not ranking.')
""")

# 17 Category stratified
add_md("""## 17. Category-Stratified Comparison

Macro mean of per-case metrics within each stone category. No significance testing.
**Ureteric_Stone has n=24 — do not overinterpret.**
""")
add_code("""cat = pd.read_csv(fc.TABLES / 'phase10_clean_v3_category_stratified_metrics.csv')
display(cat.set_index('category').T)
print('n per category:', dict(zip(cat['category'], cat['n'])))
""")

# 18 Acquisition stratified
add_md("""## 18. Acquisition-Stratified Comparison

**ROI and FULL_FIELD are different acquisition regimes** and are reported separately; they
must not be pooled without showing both.
""")
add_code("""acq = pd.read_csv(fc.TABLES / 'phase10_clean_v3_acquisition_stratified_metrics.csv')
display(acq.set_index('acquisition_type').T)
print('n per regime:', dict(zip(acq['acquisition_type'], acq['n'])))
print()
print('Every model performs markedly better on ROI crops than on FULL_FIELD radiographs;')
print('this is an expected regime effect (crops magnify the target), not a model ranking.')
""")

add_code("""p_strat = fc.plot_stratified(cat, acq)
print('Saved:', p_strat)
from IPython.display import Image as IPImage
display(IPImage(filename=str(p_strat)))
""")

# 19 Paired descriptive deltas
add_md("""## 19. Descriptive Paired Deltas

`DESCRIPTIVE_SINGLE_SEED_ONLY` — for understanding, **not** inferential claims.
No p-values, no significance stars, no confidence intervals, no "statistically better".
""")
add_code("""deltas = pd.read_csv(fc.TABLES / 'phase10_clean_v3_pairwise_descriptive_deltas.csv')
display(deltas)
print()
print('STATUS:', deltas['status'].unique().tolist())
assert (deltas['status']=='DESCRIPTIVE_SINGLE_SEED_ONLY').all()
print('No inferential statistics are present.')
""")

add_code("""p_dist = fc.plot_paired_distributions(paired)
print('Saved:', p_dist)
display(IPImage(filename=str(p_dist)))
""")

# 20 Disagreement
add_md("""## 20. Case-Wise Agreement / Disagreement Patterns

Descriptive distributions useful for later Phase 11 failure analysis. Not significance.
""")
add_code("""dis = pd.read_csv(fc.TABLES / 'phase10_clean_v3_pairwise_case_disagreement_summary.csv')
display(dis)
print()
print('Of 280 cases, counts of |Dice difference| > 0.10 show how often model pairs diverge')
print('materially on the SAME case - useful for targeted failure analysis later.')
""")

# 21 Paired qualitative gallery
add_md("""## 21. Frozen 16-Case Paired Qualitative Comparison

Same canonical 16 cases for all four models (selection SHA verified below).
Identical probability scaling (0–1) and identical overlay semantics across models.

> **DETERMINISTIC_GALLERY_SUBSET_ONLY** — these 16 cases are **not** overall model scores.
""")
add_code("""gsha = fc.sha256_file(fc.CANONICAL_GALLERY)
print('Canonical gallery SHA :', gsha)
print('Expected SHA          :', fc.CANONICAL_GALLERY_SHA)
assert gsha == fc.CANONICAL_GALLERY_SHA
print('Gallery selection verified - identical to UNet / Attention U-Net / UNet++ / DeepLabV3+')
print()
gal_pages = fc.build_paired_gallery(paired)
print(f'Generated {{len(gal_pages)}} paired gallery pages (one per frozen case)')
""")

add_code("""from IPython.display import Image as IPImage
for p in gal_pages:
    print(p.name)
    display(IPImage(filename=str(p)))
""")

# 22 Historical-v2 separation
add_md("""## 22. Historical-v2 Separation

Historical Phase-10 results are **HISTORICAL_v2** provenance, produced on contaminated /
different development membership.

| Model | v2 best epoch | v2 VAL Dice | clean-v3 best epoch | clean-v3 VAL Dice |
|---|---|---|---|---|
| Attention U-Net | 77 | 0.7530131340026855 | 54 | 0.7525129853960107 |
| UNet++ | 77 | 0.7625221610069275 | 70 | 0.7641595156062713 |
| DeepLabV3+ | 37 | 0.7487905025482178 | 52 | 0.7509140344161673 |

> Do **not** attribute clean-v3 vs v2 differences solely to leakage remediation — population
> composition also changed (v2 KUB 1979/283 vs v3 1978/280). Do not merge v2 and clean-v3
> tables as if matched. Historical evidence is provenance only.
""")

# 23 Limitations
add_md("""## 23. Limitations

1. **Single seed (42)** — no reproducibility study (Phase 29) and no significance testing
   (Phase 31). Differences of a few thousandths of Dice are not interpretable.
2. **VAL only (280 KUB cases)** — TEST locked until Phase 39; no generalization claim.
3. **Ureteric_Stone n=24** — small subgroup, unstable.
4. **Acquisition regimes differ** — ROI vs FULL_FIELD must not be pooled.
5. **Gallery (16 cases)** is a deterministic subset, not a score.
6. **DeepLabV3+ config quirk** — `base_channels: 32` present for factory-signature
   compatibility but unused (canonical decoder width 256); expected, not a defect.
7. **fp16 residuals** — paired re-inference (batch 1) vs training-time validation (batch 4,
   AMP fp16) leaves ~1e-6..1e-5 rounding differences.
""")

# 24 Conclusions
add_md("""## 24. Phase-10 Conclusions

**DESCRIPTIVE CLEAN-v3 BASELINE COMPARISON COMPLETE.**

Observed patterns (not rankings):
- All four architectures converge to a broadly similar VAL Dice band (~0.74–0.77).
- **UNet++** attains the highest observed single-seed VAL Dice (0.7642) and the best
  FULL_FIELD Dice among the four; **DeepLabV3+** attains the best ROI Dice.
- **UNet** is lowest on most strata but has the fewest parameters and shortest training.
- Every model performs substantially better on **ROI** crops than on **FULL_FIELD**
  radiographs — a regime effect, consistent with the motivation for regional refinement.
- Ureteric_Stone (n=24) shows the largest spread but is too small to interpret.

**No winner is declared.** These are single-seed descriptive VAL findings; no statistical
significance testing has been performed. Selecting a "best" architecture would require
Phase 29 (three-seed reproducibility) and Phase 31 (significance testing).
""")

# 25 Artifact registry
add_md("""## 25. Artifact Registry
""")
add_code("""def _sh(p): return fc.sha256_file(Path(p))
T = fc.TABLES
reg = []
for k in fc.MODEL_ORDER:
    reg.append({'artifact': f'epoch_results_{k}', 'path': paths[k].name, 'sha256': _sh(paths[k])})
reg += [
 {'artifact':'all_models_epoch_results_long','path': lp.name,'sha256': _sh(lp)},
 {'artifact':'paired_val_case_metrics','path':'phase10_clean_v3_paired_val_case_metrics.csv','sha256': _sh(T/'phase10_clean_v3_paired_val_case_metrics.csv')},
 {'artifact':'overall_baseline_comparison','path':'phase10_clean_v3_overall_baseline_comparison.csv','sha256': _sh(T/'phase10_clean_v3_overall_baseline_comparison.csv')},
 {'artifact':'category_stratified_metrics','path':'phase10_clean_v3_category_stratified_metrics.csv','sha256': _sh(T/'phase10_clean_v3_category_stratified_metrics.csv')},
 {'artifact':'acquisition_stratified_metrics','path':'phase10_clean_v3_acquisition_stratified_metrics.csv','sha256': _sh(T/'phase10_clean_v3_acquisition_stratified_metrics.csv')},
 {'artifact':'pairwise_descriptive_deltas','path':'phase10_clean_v3_pairwise_descriptive_deltas.csv','sha256': _sh(T/'phase10_clean_v3_pairwise_descriptive_deltas.csv')},
 {'artifact':'pairwise_case_disagreement_summary','path':'phase10_clean_v3_pairwise_case_disagreement_summary.csv','sha256': _sh(T/'phase10_clean_v3_pairwise_case_disagreement_summary.csv')},
 {'artifact':'fig_training_dynamics','path': p_dyn.name,'sha256': _sh(p_dyn)},
 {'artifact':'fig_stratified_metrics','path': p_strat.name,'sha256': _sh(p_strat)},
 {'artifact':'fig_paired_dice_distributions','path': p_dist.name,'sha256': _sh(p_dist)},
 {'artifact':'support_code','path':'phase10_final_comparison.py','sha256': _sh(PROJECT_ROOT/'notebooks'/'phasewise'/'phase_10_baseline_comparison'/'code'/'phase10_final_comparison.py')},
]
for i, p in enumerate(gal_pages, start=1):
    reg.append({'artifact': f'gallery_case_{i:02d}', 'path': p.name, 'sha256': _sh(p)})
REG = pd.DataFrame(reg)
rp = T / 'phase10_clean_v3_final_comparison_artifact_registry.csv'
REG.to_csv(rp, index=False)
print(f'Saved registry: {{rp.name}} ({{len(REG)}} entries)')
display(REG)
""")

# 26 Phase-11 boundary
add_md("""## 26. Phase-11 Boundary

Phase 10 is closed by this comparison. **Phase 11 is NOT started.**
""")
add_code("""print('=== PHASE-10 CLOSURE BOUNDARY ===')
print('Training epochs in this notebook : 0')
print('Optimizer steps                  : 0')
print('Checkpoint writes                : 0')
print('Config / history changes         : 0')
print('TEST image reads / mask reads    : 0 / 0')
print('TEST metrics / visualizations    : 0 / 0')
print('Statistical testing performed    : NO')
print('Winner declared                  : NO')
print('Phase 11 started                 : NO')
print()
print('NEXT: WAIT_FOR_SUPERVISOR_PHASE11_AUTHORIZATION')
""")

out = Path(r'D:\Softfors\jup\notebooks\phasewise\phase_10_baseline_comparison\phase10_clean_v3_final_baseline_comparison.ipynb')
with open(out, 'w', encoding='utf-8') as f:
    nbf.write(nb, f)
print(f'Notebook written: {out}')
print(f'Total cells: {len(nb.cells)}')
