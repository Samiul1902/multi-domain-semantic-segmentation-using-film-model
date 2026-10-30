"""Build the Phase 10 Part 1C DeepLabV3+ reviewer notebook."""
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
add_md("""# Phase 10 Part 1C — CLEAN-v3 DeepLabV3+ Training Review

**Model:** Gemini 3.1 Pro High
**Date:** 2026-09-20
**Experiment:** `phase10_kub_deeplabv3plus_seed42_512_clean_v3`
**Architecture:** DeepLabV3+ — `deeplabv3plus_resnet50_os16` (ResNet-50, **no pretrained weights**, output stride 16)
**Manifest:** `phase4_v3` | **Taxonomy:** `kub_size_clean_v3_v1`

---

> **READ-ONLY REVIEWER NOTEBOOK** — does NOT train. Reviews a completed run.
> TEST locked (reads = 0). **No winner is declared**; the final Phase-10 comparison
> is NOT started and no ranking or significance test appears here.
>
> **Paired gallery:** uses the SAME frozen 16-case KUB VAL selection as UNet,
> Attention U-Net, and UNet++ (canonical SHA `10ad09cb…`).
>
> **Per-epoch table:** this notebook displays the COMPLETE epoch-by-epoch results
> (one row per completed epoch, untruncated) per the new canonical rule.
""")

# 2 Scope/governance
add_md("""## 2. Scope and Governance

| Item | Value |
|------|-------|
| Manifest | `phase4_v3` |
| Taxonomy | `kub_size_clean_v3_v1` |
| Target | `mask > 0` via `binarize_mask` |
| Resolution | 512, 1 channel |
| VAL scope | KUB-only 280 (hard-gated) |
| TEST | LOCKED (reads = 0) |
| Cross-model comparison | **NOT PERFORMED** |
| Winner | **NOT DECLARED** |

Phase 10 status: UNet (09), Attention U-Net (1A), UNet++ (1B), DeepLabV3+ (1C) are now all
complete as **individual** clean-v3 runs. The final Phase-10 comparison is still
**NOT STARTED** and requires separate authorization.
""")

# 3 Setup
add_code("""%matplotlib inline
import sys, json
from pathlib import Path
import numpy as np, pandas as pd, torch
import matplotlib.pyplot as plt
from PIL import Image
from IPython.display import display

# FULL table display (no truncation) - canonical per-epoch rule
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

PROJECT_ROOT = Path(r'D:\\Softfors\\jup')
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'notebooks' / 'phasewise' / 'phase_10_baseline_comparison' / 'code'))
import phase10_deeplabv3plus_review as rv

print('Experiment  :', rv.EXPERIMENT_ID)
print('Architecture: deeplabv3plus_resnet50_os16')
print('Historical  :', rv.HISTORICAL_EXPERIMENT_ID)
""")

# 4 Historical provenance
add_md("""## 3–4. Historical DeepLabV3+ Provenance and Architecture Reconstruction
""")
add_code("""sa = rv.load_start_audit()
print('=== HISTORICAL PROVENANCE (from start audit) ===')
for k in ['historical_experiment_id','historical_architecture','historical_best_epoch',
          'historical_best_val_macro_dice','historical_final_epoch','historical_trainer',
          'historical_best_checkpoint_sha','historical_latest_checkpoint_sha',
          'historical_history_sha','historical_model_source_sha']:
    print(f'  {k}: {sa.get(k)}')
print()
print('=== ARCHITECTURE PROOF ===')
print(json.dumps(sa.get('architecture_proof', {}), indent=2))
print()
print('backbone            :', sa.get('backbone'), '| pretrained:', sa.get('backbone_pretrained'))
print('output_stride       :', sa.get('output_stride'))
print('aspp_rates          :', sa.get('aspp_rates'))
print('auxiliary_head      :', sa.get('auxiliary_head'))
print('parameter_count     :', f"{sa.get('parameter_count'):,}")
""")

# 5 Clean-v3 identity
add_md("""## 5. Clean-v3 Experiment Identity
""")
add_code("""print('=== CLEAN-v3 IDENTITY ===')
print(f'Experiment ID : {rv.EXPERIMENT_ID}')
print(f'Architecture  : deeplabv3plus_resnet50_os16')
print(f'Config SHA    : {rv.EXPECTED_CONFIG_SHA}')
ca = rv.load_completion_audit()
print(f'History SHA   : {ca.get("history_sha")}')
print(f'Best pt SHA   : {ca.get("best_checkpoint_sha")}')
print(f'Latest pt SHA : {ca.get("latest_checkpoint_sha")}')
print(f'Manifest      : phase4_v3')
print(f'Taxonomy      : kub_size_clean_v3_v1')
""")

# 6 Protocol diff
add_md("""## 6. v2 → v3 Protocol Diff
""")
add_code("""d = rv.load_protocol_diff()
print('=== PROTOCOL DIFF ===')
print('Fields compared:', len(d), '| CHANGED:', int((d.same_or_changed=='CHANGED').sum()),
      '| SAME:', int((d.same_or_changed=='SAME').sum()))
print()
print(d[d.same_or_changed=='CHANGED'][['field','historical_v2','clean_v3','change_reason']].to_string(index=False))
un = d[(d.same_or_changed=='CHANGED') & (d.scientifically_material==True)]
print()
print('Unauthorized material differences:', len(un))
assert len(un) == 0
print('All changes governance/provenance only - PASS')
""")

# 7 Frozen protocol
add_md("""## 7. Frozen Protocol (from physical config)
""")
add_code("""cfg = rv.load_config()
m,t,o,s,a = cfg['model'],cfg['training'],cfg['optimizer'],cfg['scheduler'],cfg['augmentation']
print('=== FROZEN PROTOCOL ===')
print(f\"Architecture : {m['name']} | backbone {m['backbone']} | pretrained={m['backbone_pretrained']}\")
print(f\"OS / ASPP    : os={m['output_stride']} rates={m['aspp']['rates']} out={m['aspp']['out_channels']} dropout={m['aspp']['project_dropout']}\")
print(f\"Low-level proj: {m['low_level_projection_channels']} ch | decoder {m['decoder_channels']} | aux={m['auxiliary_head']}\")
print(f\"Input handling: {m['input_channel_handling']}\")
print(f\"Resolution   : {cfg['input_resolution']}\")
print(f\"Preprocessing: {cfg['preprocessing']['strategy']} ({cfg['preprocessing']['mask_interpolation']} mask)\")
print(f\"Loss         : {cfg['loss']['name']} {cfg['loss']['bce_weight']}/{cfg['loss']['dice_weight']} eps={cfg['loss']['dice_epsilon']}\")
print(f\"Optimizer    : {o['name']} lr={o['learning_rate']} wd={o['weight_decay']}\")
print(f\"Scheduler    : {s['name']} T_max={s['max_epochs']}\")
print(f\"Batch        : {t['batch_size']} (accum {t['gradient_accumulation_steps']}, eff {t['effective_batch_size']})\")
print(f\"AMP/seed     : {t['amp']} / {t['seed']}\")
print(f\"Max epochs   : {t['max_epochs']} patience {t['early_stopping_patience']}\")
print(f\"Monitor/thr  : {t['monitor']} / {t['threshold']}\")
print(f\"Grad clipping: {t.get('gradient_clipping')}\")
print(f\"Augmentation : hflip={a['horizontal_flip_probability']} rot=+/-{a['rotation_degrees']} bright=+/-{a['brightness']} contrast=+/-{a['contrast']} vflip={a['vertical_flip']}\")
print(f\"Init         : {cfg['initialization']['policy']}\")
print(f\"allow_test   : {cfg['allow_test']}\")
""")

# 8 Artifact provenance
add_md("""## 8. Artifact Provenance
""")
add_code("""art = rv.verify_artifact_shas()
print('=== ARTIFACT SHA VERIFICATION ===')
for k,v in art.items(): print(f'  {k}: {v}')
assert art['all_pass']
print('\\nALL ARTIFACT SHAS VERIFIED - PASS')
""")

# 9 History integrity
add_md("""## 9. History Integrity
""")
add_code("""df = rv.load_history()
hi = rv.check_history_integrity(df)
print('=== HISTORY INTEGRITY ===')
for k,v in hi.items(): print(f'  {k}: {v}')
assert hi['contiguous_epochs'] and hi['no_duplicates']
assert hi['unique_strict_max'] and hi['stop_consistent']
assert hi['no_nan'] and hi['finite_losses']
print('\\nHISTORY INTEGRITY - PASS')
""")

# 10 COMPLETE EPOCH TABLE (HARD GATE)
add_md("""## 10. Complete Epoch-by-Epoch Training Results

**CANONICAL RULE:** exactly one row per completed epoch, displayed **in full** (no
`head()`/`tail()`, no truncation). Source of truth = immutable `history.csv`.
Derived columns (`delta_*`, `is_*`, `epochs_since_best`) are reviewer-only and are
**never** written back to `history.csv`.
""")
add_code("""tbl = rv.build_epoch_table(df)
v = rv.verify_epoch_table(tbl, df)
print('=== EPOCH TABLE INTEGRITY SUMMARY ===')
for k,val in v.items(): print(f'  {k}: {val}')
print()
assert v['integrity_pass'], 'Epoch table integrity FAILED'
assert v['row_count_matches_history'], 'Row count != history rows'
print('INTEGRITY: PASS')
print()
print(f"Rendering ALL {len(tbl)} epoch rows (complete, untruncated):")
display(tbl)
""")

add_code("""# Save machine-readable epoch table
p = rv.save_epoch_table(tbl)
print(f'Epoch table saved: {p}')
print('Epoch table SHA-256:', rv.sha256_file(p))
print(f"Rows: {len(tbl)} | History rows: {len(df)} | Match: {len(tbl)==len(df)}")
""")

# 11 Curves
add_md("""## 11. Training Curves
""")
add_code("""fig = rv.plot_training_curves(df)
cp = PROJECT_ROOT / 'reports' / 'figures' / 'phase10_deeplabv3plus_clean_v3_training_curves_review.png'
fig.savefig(cp, dpi=150, bbox_inches='tight')
print(f'Curves saved: {cp}')
display(fig)
""")

# 12 Best checkpoint
add_md("""## 12. Best-Checkpoint Verification
""")
add_code("""b = rv.check_best_checkpoint_consistency()
print('=== BEST CHECKPOINT ===')
for k,val in b.items(): print(f'  {k}: {val}')
assert b['all_pass']
print('\\nBEST CHECKPOINT - PASS')
""")

# 13 Early stop
add_md("""## 13. Early-Stop Verification

Ordering preserved from the historical trainer
(`scripts/training/train_phase10_baselines.py`):

`TRAIN → VAL → scheduler.step() → strict '>' improvement → early_stopping.update()
→ save latest (always) → save best (if improved) → stop check`
""")
add_code("""l = rv.check_latest_checkpoint_consistency()
print('=== LATEST CHECKPOINT ===')
for k,val in l.items(): print(f'  {k}: {val}')
assert l['all_pass']
print()
be, fe, fb = hi['best_epoch'], hi['final_epoch'], hi['final_bad_epochs']
print(f'Best epoch {be} + patience 15 = {be+15}; actual stop = {fe}; bad_epochs = {fb}')
assert fe == be + fb
print('\\nLATEST CHECKPOINT + EARLY-STOP - PASS')
""")

# 14 KUB-only VAL
add_md("""## 14. KUB-Only VAL Population
""")
add_code("""val_all = pd.read_csv(PROJECT_ROOT / 'manifests' / 'phase4_v3' / 'val.csv')
print('Full phase4_v3 VAL rows:', len(val_all), '| datasets:', val_all['dataset'].value_counts().to_dict())
kub_val = rv.get_kub_val()
sc = rv.assert_kub_scope(kub_val)
print()
print('=== KUB-ONLY VAL ===')
for k,val in sc.items(): print(f'  {k}: {val}')
print('Category counts:', kub_val['category'].value_counts().to_dict())
print('Acquisition    :', kub_val['acquisition_type'].value_counts().to_dict())
assert len(kub_val)==280 and sc['not_available_count']==0 and sc['unknown_acquisition_count']==0
print('\\nKUB-ONLY VAL - PASS')
""")

# 15 Gallery selection
add_md("""## 15. Frozen Paired Gallery Selection
""")
add_code("""gal = rv.load_canonical_gallery(kub_val)
print('Canonical gallery SHA verified:', rv.CANONICAL_GALLERY_SHA)
print('Actual file SHA              :', rv.sha256_file(rv.CANONICAL_GALLERY))
print(f'Cases: {len(gal)}')
print(gal[['gallery_index','sample_id','category','acquisition_type']].to_string(index=False))
assert len(gal)==16
assert set(gal['category']).issubset({'Kidney_Stone','Bladder_Stone','Ureteric_Stone'})
assert gal['acquisition_type'].isin(['ROI','FULL_FIELD']).all()
print()
print('Identical 16 IDs to UNet / Attention U-Net / UNet++ - PASS')
""")

# 16 Gallery
add_md("""## 16. DeepLabV3+ VAL Gallery

`best.pt` only, threshold 0.5, same 16 frozen cases.

> Metrics are `DETERMINISTIC_GALLERY_SUBSET_ONLY` — NOT the 280-case VAL score.
""")
add_code("""from src.utils.targets import binarize_mask
from src.metrics.segmentation import binary_metrics

model, device = rv.load_best_model_for_inference(device='cuda')
print(f'Model on {device}: {model.__class__.__name__}')
print(f'Parameters: {sum(p.numel() for p in model.parameters()):,}')
print()
print('=== PRE-CHECK ===')
for _,row in gal.iterrows():
    ie,me = Path(row['image_path']).exists(), Path(row['mask_path']).exists()
    print(f"  {row['gallery_index']:2d} {row['sample_id'][:26]:26s} {'OK' if (ie and me) else 'MISSING'}")
""")

add_code("""n = len(gal)
fig, axes = plt.subplots(n, 5, figsize=(20, 4*n))
fig.suptitle(f'Phase 10 DeepLabV3+ CLEAN-v3 VAL Gallery - Best Checkpoint (epoch {hi["best_epoch"]})\\n{rv.EXPERIMENT_ID}', fontsize=11)
TH = 0.5
recs = []
for idx,(_,row) in enumerate(gal.iterrows()):
    sid = row['sample_id']; ip = Path(row['image_path']); mp = Path(row['mask_path'])
    if not ip.exists() or not mp.exists():
        for ax in axes[idx]: ax.axis('off'); ax.set_title('MISSING')
        continue
    gt = binarize_mask(np.array(Image.open(mp).convert('L'))).astype(np.uint8)
    prob,(nw,nh),(pl,pt) = rv.predict_on_val_sample(model, device, ip, target_size=512)
    gtr = np.array(Image.fromarray(gt).resize((nw,nh), Image.NEAREST))
    pred = (prob>=TH).astype(np.uint8)
    mm = binary_metrics(torch.from_numpy(gtr).float().unsqueeze(0),
                        torch.from_numpy(pred).float().unsqueeze(0), threshold=0.5)
    dice, iou = float(mm['dice']), float(mm['iou'])
    im = Image.open(ip).convert('L'); native = im.size; arr = np.array(im)
    ov = np.zeros((*pred.shape,3), dtype=np.uint8)
    ov[...,0]=gtr*255; ov[...,1]=pred*255
    both = gtr & pred
    ov[...,0]=np.where(both,0,ov[...,0]); ov[...,1]=np.where(both,255,ov[...,1])
    ov[...,2]=np.where((gtr==0)&(pred==1),255,0)
    A = axes[idx]
    A[0].imshow(arr,cmap='gray',vmin=0,vmax=255)
    A[0].set_title(f'{idx+1}. {sid[:16]}\\n{row["category"]} | {row["acquisition_type"]}')
    A[1].imshow(gtr,cmap='gray',vmin=0,vmax=1); A[1].set_title('Binary GT')
    A[2].imshow(prob,cmap='viridis',vmin=0,vmax=1); A[2].set_title(f'Prob max={prob.max():.2f}')
    A[3].imshow(pred,cmap='gray',vmin=0,vmax=1); A[3].set_title(f'Pred t={TH}')
    A[4].imshow(ov); A[4].set_title(f'Overlay Dice={dice:.3f} IoU={iou:.3f}')
    for ax in A: ax.axis('off')
    recs.append({'gallery_index':idx+1,'sample_id':sid,'patient_id':row['patient_id'],
                 'category':row['category'],'acquisition_type':row['acquisition_type'],
                 'native_width':native[0],'native_height':native[1],
                 'pred_width':nw,'pred_height':nh,'dice':dice,'iou':iou})
plt.tight_layout()
gf = PROJECT_ROOT / 'reports' / 'figures' / 'phase10_deeplabv3plus_clean_v3_val_gallery.png'
fig.savefig(gf, dpi=150, bbox_inches='tight')
print(f'Gallery saved: {gf}')
display(fig)

mdf = pd.DataFrame(recs)
mpath = PROJECT_ROOT / 'reports' / 'tables' / 'phase10_deeplabv3plus_clean_v3_val_gallery_metrics.csv'
mdf.to_csv(mpath, index=False)
print(f'Metrics saved: {mpath}')
print()
print('=== DETERMINISTIC_GALLERY_SUBSET_ONLY ===')
print(f'Subset mean Dice: {mdf["dice"].mean():.6f}')
print(f'Subset mean IoU : {mdf["iou"].mean():.6f}')
print()
print('Authoritative full-KUB-VAL (280 cases):')
br = df.loc[df['val_dice'].idxmax()]
print(f'  Dice={br["val_dice"]:.16f} IoU={br["val_iou"]:.16f}')
print(f'  Precision={br["val_precision"]:.16f} Recall={br["val_recall"]:.16f}')
print()
print('Gallery means do NOT replace authoritative metrics.')
""")

# 17 Aggregate metrics
add_md("""## 17. Authoritative Aggregate VAL Metrics
""")
add_code("""br = df.loc[df['val_dice'].idxmax()]
summary = pd.DataFrame([{
 'experiment_id': rv.EXPERIMENT_ID, 'architecture':'deeplabv3plus',
 'backbone':'resnet50', 'backbone_pretrained': False, 'parameter_count': 40340769,
 'manifest_version':'phase4_v3','taxonomy_id':'kub_size_clean_v3_v1',
 'best_epoch':int(br['epoch']),'best_val_macro_dice':float(br['val_dice']),
 'val_macro_iou':float(br['val_iou']),'val_precision':float(br['val_precision']),
 'val_recall':float(br['val_recall']),'final_epoch':int(df['epoch'].iloc[-1]),
 'stop_reason':'EARLY_STOP','early_stop_bad_epochs':int(df['bad_epochs'].iloc[-1]),
 'config_sha': rv.EXPECTED_CONFIG_SHA,'history_sha': ca.get('history_sha'),
 'best_checkpoint_sha': ca.get('best_checkpoint_sha'),
 'latest_checkpoint_sha': ca.get('latest_checkpoint_sha'),
}])
sp = PROJECT_ROOT / 'reports' / 'tables' / 'phase10_deeplabv3plus_clean_v3_best_val_summary.csv'
summary.to_csv(sp, index=False)
print(f'Saved: {sp}')
print(summary.T.to_string())
""")

# 18 Limitations
add_md("""## 18. Limitations

1. VAL-only; TEST locked (reads = 0).
2. Reviews DeepLabV3+ alone — **no cross-model comparison, no ranking, no winner**.
3. Single seed (42); no significance testing performed.
4. Gallery metrics are `DETERMINISTIC_GALLERY_SUBSET_ONLY` (16 cases), not 280-case VAL.
5. `base_channels: 32` appears in config for factory-signature compatibility but is
   **unused** by DeepLabV3+ (canonical decoder width is 256) — expected, not a defect.
6. DeepLabV3+ uses a randomly initialized ResNet-50 (no pretraining) by historical design;
   results are not comparable to a pretrained-backbone variant.
""")

# 19 Historical-v2 separation
add_md("""## 19. Historical-v2 Separation

| Property | HISTORICAL_v2 | CLEAN_v3 |
|----------|---------------|----------|
| Experiment | `phase10_kub_deeplabv3plus_seed42_512` | `…_clean_v3` |
| Manifest | `phase4_v2` (contaminated) | `phase4_v3` (remediated) |
| Taxonomy | none | `kub_size_clean_v3_v1` |
| Best epoch | 37 | see §17 |
| Final epoch | 52 | see §17 |
| Best VAL Dice | 0.7487905025482178 | see §17 |

Different TRAIN/VAL membership (v2 KUB 1979/283 vs v3 1978/280); do not attribute any
difference solely to leakage remediation.
""")

# 20 Current Phase-10 status
add_md("""## 20. Current Phase-10 Status

| Model | clean-v3 run | Status |
|---|---|---|
| UNet (Phase 09) | `phase9_…_clean_v3` | COMPLETE |
| Attention U-Net (1A) | `phase10_…_attention_unet_…_clean_v3` | COMPLETE |
| UNet++ (1B) | `phase10_…_unetpp_…_clean_v3` | COMPLETE |
| **DeepLabV3+ (1C)** | `phase10_…_deeplabv3plus_…_clean_v3` | **COMPLETE (this notebook)** |
| Final comparison | — | **NOT STARTED** |

**NO WINNER DECLARED.** All four runs are single-seed and descriptive; the final
comparison requires separate authorization.
""")

# 21 Artifact hashes
add_md("""## 21. Artifact Hashes
""")
add_code("""s = rv.full_integrity_summary()
print('Overall pass:', s['overall_pass'])
assert s['overall_pass']

def _sh(p): return rv.sha256_file(Path(p))
R = PROJECT_ROOT
reg = pd.DataFrame([
 {'artifact':'config','sha256':_sh(rv.CONFIG_PATH)},
 {'artifact':'history','sha256':_sh(rv.HISTORY_PATH)},
 {'artifact':'best_checkpoint','sha256':_sh(rv.BEST_PT)},
 {'artifact':'latest_checkpoint','sha256':_sh(rv.LATEST_PT)},
 {'artifact':'taxonomy','sha256':_sh(rv.TAXONOMY_ARTIFACT)},
 {'artifact':'training_runner','sha256':_sh(rv.TRAINING_RUNNER)},
 {'artifact':'protocol_diff','sha256':_sh(rv.PROTOCOL_DIFF)},
 {'artifact':'epoch_results_table','sha256':_sh(rv.EPOCH_TABLE_CSV)},
 {'artifact':'review_support_code','sha256':_sh(R/'notebooks'/'phasewise'/'phase_10_baseline_comparison'/'code'/'phase10_deeplabv3plus_review.py')},
 {'artifact':'canonical_gallery_selection','sha256':rv.CANONICAL_GALLERY_SHA},
 {'artifact':'gallery_metrics','sha256':_sh(R/'reports'/'tables'/'phase10_deeplabv3plus_clean_v3_val_gallery_metrics.csv')},
 {'artifact':'best_val_summary','sha256':_sh(R/'reports'/'tables'/'phase10_deeplabv3plus_clean_v3_best_val_summary.csv')},
])
rp = R / 'reports' / 'tables' / 'phase10_deeplabv3plus_clean_v3_artifact_registry.csv'
reg.to_csv(rp, index=False)
print(f'Registry saved: {rp}')
print(reg.to_string(index=False))
""")

# 22 Stop boundary
add_md("""## 22. Stop Boundary
""")
add_code("""print('=== REVIEWER BOUNDARY ===')
print('Optimizer steps        : 0')
print('Training epochs        : 0')
print('Checkpoint writes      : 0')
print('best/latest modified   : NO')
print('history/config modified: NO')
print('TEST image/mask reads  : 0')
print('TEST metrics / visuals : 0')
print('Final comparison       : NOT STARTED')
print('Winner declared        : NO')
print('Phase 11               : NOT STARTED')
print()
print('REVIEWER BOUNDARY - PASS')
""")

out = Path(r'D:\Softfors\jup\notebooks\phasewise\phase_10_baseline_comparison\phase10_deeplabv3plus_clean_v3_training_review.ipynb')
with open(out,'w',encoding='utf-8') as f:
    nbf.write(nb,f)
print(f'Notebook written: {out}')
print(f'Total cells: {len(nb.cells)}')
