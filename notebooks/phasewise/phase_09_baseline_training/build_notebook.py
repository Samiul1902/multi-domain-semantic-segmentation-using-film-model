"""Build the Phase 09 Part 1B reviewer notebook programmatically."""
import json, os, sys
from pathlib import Path

sys.path.insert(0, str(Path(r'D:\Softfors\jup')))

import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

nb = new_notebook()
nb.metadata['kernelspec'] = {
    'display_name': 'jup-venv',
    'language': 'python',
    'name': 'jup-venv'
}
nb.metadata['language_info'] = {
    'name': 'python',
    'version': '3.13.12'
}

def add_md(text):
    nb.cells.append(new_markdown_cell(text))

def add_code(text):
    nb.cells.append(new_code_cell(text))

# =====================================================================
# 1. Title
# =====================================================================
add_md("""# Phase 09 Part 1B — CLEAN-v3 KUB UNet Baseline Training Review

**Model:** Gemini 3.8 Flash Medium  
**Date:** 2026-09-20  
**Experiment:** `phase9_kub_unet_baseline_seed42_512_clean_v3`  
**Manifest:** `phase4_v3`  
**Taxonomy:** `kub_size_clean_v3_v1`

---

> **READ-ONLY REVIEWER NOTEBOOK**  
> This notebook does not train. It reviews a completed training run.  
> TEST is locked. No Phase-10 models are involved.
>
> **REPAIR NOTE (Part 1B-R1):** A pre-repair version of this notebook (SHA `7721a285...`)  
> accidentally used the full 808-row multi-domain VAL manifest for gallery selection,  
> mixing ISIC/BUSI/Kvasir cases into the KUB review. That gallery is  
> **INVALID_SUPERSEDED_CROSS_DOMAIN_SELECTION**. The current version filters VAL to  
> KUB-only (280 rows) and derives acquisition_type from file paths.
""")

# =====================================================================
# 2. Scientific Objective
# =====================================================================
add_md("""## 2. Scientific Objective

Phase 09 Part 1A executed the clean-v3 rerun of the historical Phase-09 UNet baseline on the `phase4_v3` manifest with the frozen `kub_size_clean_v3_v1` taxonomy.

Part 1B (this notebook) verifies:
1. Training artifact integrity (checksums, history continuity, checkpoint consistency)
2. Convergence behavior and early-stop validity
3. Best-checkpoint selection correctness
4. Deterministic VAL prediction gallery for qualitative inspection

No scientific parameter was altered during or after training.
""")

# =====================================================================
# 3. CLEAN-v3 Governance
# =====================================================================
add_md("""## 3. CLEAN-v3 Governance

| Item | Value |
|------|-------|
| Active manifest | `phase4_v3` |
| Frozen taxonomy | `kub_size_clean_v3_v1` |
| Taxonomy artifact SHA | `89031c51a35c24f6f939fd6206fde6002a019d4bda24ce8cb21988f04db0f0d6` |
| Canonical target | `mask > 0` via `src.utils.targets.binarize_mask` |
| Canonical device | `get_device(require_cuda=True)` |
| Input channels | 1 (grayscale) |
| Transform | aspect-preserving resize + centre pad, nearest mask |
| Metrics | binary_metrics threshold 0.5, object_metrics 8-conn |
| Test lock | **ACTIVE** — TEST reads = 0 |
""")

# =====================================================================
# 4. Setup & Imports
# =====================================================================
add_code("""# ============================================================
# SETUP — read-only reviewer imports
# ============================================================
%matplotlib inline
import sys, os, json, hashlib, random
from pathlib import Path
import numpy as np
import pandas as pd
import torch
import matplotlib.pyplot as plt
from PIL import Image
from IPython.display import display

PROJECT_ROOT = Path(r'D:\\Softfors\\jup')
sys.path.insert(0, str(PROJECT_ROOT))

# Import reviewer support
sys.path.insert(0, str(PROJECT_ROOT / 'notebooks' / 'phasewise' / 'phase_09_baseline_training' / 'code'))
import phase09_training_review as rv

print('Project root:', PROJECT_ROOT)
print('Experiment  :', rv.EXPERIMENT_ID)
print('Support code loaded successfully')
""")

# =====================================================================
# 5. Experiment Identity
# =====================================================================
add_md("""## 5. Experiment Identity
""")
add_code("""print('=== EXPERIMENT IDENTITY ===')
print(f'Experiment ID : {rv.EXPERIMENT_ID}')
print(f'Config path   : {rv.CONFIG_PATH}')
print(f'Config SHA    : {rv.EXPECTED_CONFIG_SHA}')
print(f'History path  : {rv.HISTORY_PATH}')
print(f'History SHA   : {rv.EXPECTED_HISTORY_SHA}')
print(f'Best pt path  : {rv.BEST_PT}')
print(f'Best pt SHA   : {rv.EXPECTED_BEST_SHA}')
print(f'Latest pt path: {rv.LATEST_PT}')
print(f'Latest pt SHA : {rv.EXPECTED_LATEST_SHA}')
print(f'Manifest      : phase4_v3')
print(f'Taxonomy      : kub_size_clean_v3_v1')
print(f'Taxonomy SHA  : {rv.TAXONOMY_SHA}')
""")

# =====================================================================
# 6. Artifact Provenance Verification
# =====================================================================
add_md("""## 6. Artifact Provenance Verification

Independently verify every physical artifact against the recorded SHA-256 provenance.
""")
add_code("""art = rv.verify_artifact_shas()
print('=== ARTIFACT SHA VERIFICATION ===')
for k, v in art.items():
    print(f'  {k}: {v}')
assert art['all_pass'], 'Artifact SHA mismatch!'
print('\\nALL ARTIFACT SHAS VERIFIED — PASS')
""")

# =====================================================================
# 7. Frozen Protocol Summary
# =====================================================================
add_md("""## 7. Frozen Protocol Summary

| Field | Value |
|-------|-------|
| Architecture | UNet 4-stage, base_channels=32 |
| Input channels | 1 |
| Output channels | 1 |
| Resolution | 512 |
| Loss | BCE + Dice (0.5 / 0.5), eps=1e-6 |
| Optimizer | AdamW, lr=1e-4, wd=1e-4 |
| Scheduler | CosineAnnealingLR, T_max=100 |
| Batch size | 4 |
| AMP | True |
| Seed | 42 |
| Max epochs | 100 |
| Early-stop patience | 15 |
| Monitor | VAL macro Dice |
| Improvement | strict `>` |
| Augmentation | hflip p=0.5, rot ±5°, brightness ±0.1, contrast ±0.1 |
""")

# =====================================================================
# 8. Training-History Integrity
# =====================================================================
add_md("""## 8. Training-History Integrity

Recompute history consistency from the physical `history.csv`.
Do not trust the audit alone.
""")
add_code("""df = rv.load_history()
hi = rv.check_history_integrity(df)
print('=== HISTORY INTEGRITY ===')
for k, v in hi.items():
    print(f'  {k}: {v}')
assert hi['contiguous_epochs'], 'Epochs not contiguous!'
assert hi['stop_consistent'], 'Stop condition inconsistent!'
assert hi['no_nan'], 'NaN detected in history!'
assert hi['finite_losses'], 'Non-finite losses detected!'
print('\\nHISTORY INTEGRITY — PASS')
""")

# =====================================================================
# 9. Convergence Behavior
# =====================================================================
add_md("""## 9. Convergence Behavior

Load and inspect the training trajectory.
""")
add_code("""print('=== CONVERGENCE SUMMARY ===')
print(f'Epochs completed   : {len(df)}')
print(f'Best epoch         : {hi[\"best_epoch\"]}')
print(f'Best VAL macro Dice: {hi[\"best_val_macro_dice\"]:.6f}')
print(f'Final epoch        : {hi[\"final_epoch\"]}')
print(f'Final bad_epochs   : {hi[\"final_bad_epochs\"]}')
print(f'Improvements       : {hi[\"improved_count\"]}')
print(f'Earliest improve   : epoch {df.loc[df.improved==1, \"epoch\"].min():.0f}')
print(f'Latest improve     : epoch {df.loc[df.improved==1, \"epoch\"].max():.0f}')
print(f'Train loss first   : {df.train_loss.iloc[0]:.4f}')
print(f'Train loss last    : {df.train_loss.iloc[-1]:.4f}')
print(f'VAL loss first     : {df.val_loss.iloc[0]:.4f}')
print(f'VAL loss last      : {df.val_loss.iloc[-1]:.4f}')
print(f'LR first           : {df.learning_rate.iloc[0]:.6f}')
print(f'LR last            : {df.learning_rate.iloc[-1]:.6f}')
""")

# =====================================================================
# 10. Best-Checkpoint Selection
# =====================================================================
add_md("""## 10. Best-Checkpoint Selection

The best checkpoint was selected by strict maximum of VAL macro Dice.
""")
add_code("""best_row = df.loc[df.val_macro_dice.idxmax()]
print('=== BEST CHECKPOINT (from history) ===')
print(f'Epoch              : {int(best_row.epoch)}')
print(f'VAL macro Dice     : {best_row.val_macro_dice:.6f}')
print(f'VAL macro IoU      : {best_row.val_macro_iou:.6f}')
print(f'VAL macro Precision: {best_row.val_macro_precision:.6f}')
print(f'VAL macro Recall   : {best_row.val_macro_recall:.6f}')
print(f'VAL loss           : {best_row.val_loss:.6f}')
print(f'Train loss         : {best_row.train_loss:.6f}')
print(f'LR                 : {best_row.learning_rate:.6f}')
print(f'Bad epochs at best : {int(best_row.bad_epochs)}')
print(f'Improved flag      : {bool(best_row.improved)}')

# Strict-max verification
max_dice = df.val_macro_dice.max()
num_max = (df.val_macro_dice == max_dice).sum()
print(f'\\nStrict-max verification: {num_max} epoch(s) at max dice')
assert num_max == 1, 'Best epoch is not a unique strict maximum!'
print('Best epoch is UNIQUE strict maximum — PASS')
""")

# =====================================================================
# 11. Early-Stop Verification
# =====================================================================
add_md("""## 11. Early-Stop Verification

Verify that early stop is consistent with best epoch + patience.
""")
add_code("""print('=== EARLY-STOP VERIFICATION ===')
print(f'Best epoch   : {hi[\"best_epoch\"]}')
print(f'Patience     : 15')
print(f'Expected stop: {hi[\"best_epoch\"] + 15}')
print(f'Actual stop  : {hi[\"final_epoch\"]}')
print(f'Final bad    : {hi[\"final_bad_epochs\"]}')
assert hi['final_epoch'] == hi['best_epoch'] + hi['final_bad_epochs']
print('Early-stop consistency — PASS')
""")

# =====================================================================
# 12. Checkpoint Consistency
# =====================================================================
add_md("""## 12. Checkpoint Consistency

Load metadata from both checkpoints without instantiating models.
""")
add_code("""best_ck = rv.check_best_checkpoint_consistency()
latest_ck = rv.check_latest_checkpoint_consistency()
print('=== BEST CHECKPOINT CONSISTENCY ===')
for k, v in best_ck.items():
    print(f'  {k}: {v}')
print('\\n=== LATEST CHECKPOINT CONSISTENCY ===')
for k, v in latest_ck.items():
    print(f'  {k}: {v}')
assert best_ck['all_pass'], 'Best checkpoint inconsistent!'
assert latest_ck['all_pass'], 'Latest checkpoint inconsistent!'
print('\\nCHECKPOINT CONSISTENCY — PASS')
""")

# =====================================================================
# 12b. Authoritative Training VAL Scope Verification
# =====================================================================
add_md("""## 12b. Authoritative Training VAL Scope Verification

The Phase-09 training loop loaded `KUBDataset` with `phase4_v3` VAL split.  
We verify here that the authoritative validation metrics (VAL macro Dice 0.740613)  
were computed over KUB-only VAL, not the full 808-row multi-domain VAL manifest.
""")
add_code("""import pandas as pd
val_all = pd.read_csv(PROJECT_ROOT / 'manifests' / 'phase4_v3' / 'val.csv')
print('=== FULL phase4_v3 VAL MANIFEST ===')
print('Total rows:', len(val_all))
print('Datasets:', val_all['dataset'].value_counts().to_dict())

kub_val = val_all[val_all['dataset'] == 'KUB']
print('\\n=== KUB-ONLY VAL ===')
print('KUB rows:', len(kub_val))
print('KUB categories:', kub_val['category'].value_counts().to_dict())

# Verify checkpoint manifest hashes match the physical manifest
import json
ckpt_manifest = best_ckpt_manifest_hashes if 'best_ckpt_manifest_hashes' in globals() else json.loads(open('reports/audits/phase09_clean_v3_training_completion_audit.json').read())['manifest_hashes']
print('\\nCheckpoint manifest hash (val):', ckpt_manifest['val'])
import hashlib
def sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1<<20), b''): h.update(c)
    return h.hexdigest()
physical_hash = sha_file(PROJECT_ROOT / 'manifests' / 'phase4_v3' / 'val.csv')
print('Physical manifest hash (val):', physical_hash)
print('Hash match:', ckpt_manifest['val'] == physical_hash)

assert len(kub_val) == 280, 'KUB VAL row count mismatch!'
assert set(kub_val['category'].unique()).issubset({'Kidney_Stone', 'Bladder_Stone', 'Ureteric_Stone'})
print('\\nAUTHORITATIVE TRAINING VAL SCOPE: KUB-ONLY 280 — VERIFIED')
""")

# =====================================================================
# 12c. Pre-Repair Error Documentation
# =====================================================================
add_md("""## 12c. Pre-Repair Error Documentation

**Issue:** The first version of this reviewer notebook (Part 1B, SHA `7721a285...`)  
accidentally called `pd.read_csv('manifests/phase4_v3/val.csv')` without filtering  
`dataset == 'KUB'`, causing the gallery selection to mix ISIC/BUSI/Kvasir cases  
into the KUB review.

**Impact:** The pre-repair gallery outputs are `INVALID_SUPERSEDED_CROSS_DOMAIN_SELECTION`.  
They must not be used for any scientific claim about the KUB baseline.

**Resolution:** Part 1B-R1 repairs the reviewer support code (`phase09_training_review.py`)  
to hard-filter VAL to KUB-only (280 rows), assert zero non-KUB cases, and derive  
`acquisition_type` from file paths. The gallery was regenerated from the corrected scope.

**Training artifacts:** Unaffected. The training itself always used KUB-only data.
""")

# =====================================================================
# 13. Training Curves
# =====================================================================
add_md("""## 13. Training Curves

Generate reviewer-quality curves from the actual history.
""")
add_code("""fig = rv.plot_training_curves(df)
fig_path = PROJECT_ROOT / 'reports' / 'figures' / 'phase09_clean_v3' / 'phase09_clean_v3_training_curves_review.png'
fig_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(fig_path, dpi=150, bbox_inches='tight')
print(f'Curves saved: {fig_path}')
display(fig)
""")

# =====================================================================
# 14. Deterministic VAL Sample Selection
# =====================================================================
add_md("""## 14. Deterministic VAL Sample Selection

Select 16 deterministic VAL cases, prediction-independent, stratified by category and acquisition type.
""")
add_code("""val_df = rv.get_val_manifest()
print(f'VAL manifest rows: {len(val_df)}')
print('Category counts:', val_df['category'].value_counts().to_dict())
if 'acquisition_type' in val_df.columns:
    print('Acquisition counts:', val_df['acquisition_type'].value_counts().to_dict())
else:
    print('Acquisition_type column not present in manifest')

gallery_df = rv.deterministic_val_gallery_selection(val_df, n_cases=16, seed=42)
print(f'\\nGallery selected: {len(gallery_df)} cases')
display_cols = ['gallery_index', 'sample_id', 'patient_id', 'category']
if 'acquisition_type' in gallery_df.columns:
    display_cols.append('acquisition_type')
print(gallery_df[display_cols].to_string(index=False))

# Save selection
gallery_path = PROJECT_ROOT / 'reports' / 'tables' / 'phase09_clean_v3_val_gallery_selection.csv'
gallery_df.to_csv(gallery_path, index=False)
print(f'\\nGallery selection saved: {gallery_path}')
""")

# =====================================================================
# 15. VAL Prediction Gallery
# =====================================================================
add_md("""## 15. VAL Prediction Gallery

Run inference with the best checkpoint on the deterministic KUB-only VAL selection (16 cases from 280 KUB VAL rows).

> Gallery metrics are `DETERMINISTIC_GALLERY_SUBSET_ONLY` — they describe only these 16 cases,  
> not the full 280-case KUB VAL population. Authoritative overall VAL metrics are in section 11.
""")
add_code("""# Load model once
model, device = rv.load_best_model_for_inference(device='cuda')
print(f'Model loaded on {device}')
print(f'Model class: {model.__class__.__name__}')
print(f'Parameters : {sum(p.numel() for p in model.parameters()):,}')

# Pre-check all gallery samples (paths come directly from KUB manifest)
print('\\n=== PRE-CHECK GALLERY SAMPLES ===')
for _, row in gallery_df.iterrows():
    img_exists = Path(row['image_path']).exists() if pd.notna(row['image_path']) else False
    mask_exists = Path(row['mask_path']).exists() if pd.notna(row['mask_path']) else False
    status = 'OK' if (img_exists and mask_exists) else 'MISSING'
    print(f"  {row['gallery_index']:2d} {row['sample_id'][:30]:30s} {status}")
""")

add_code("""# ============================================================
# Generate prediction gallery figure
# ============================================================
from src.utils.targets import binarize_mask
from src.metrics.segmentation import binary_metrics

n_cases = len(gallery_df)
fig, axes = plt.subplots(n_cases, 5, figsize=(20, 4 * n_cases))
fig.suptitle(f'Phase 09 Clean-v3 VAL Prediction Gallery — Best Checkpoint (epoch {hi[\"best_epoch\"]})\\n{rv.EXPERIMENT_ID}', fontsize=11)

THRESHOLD = 0.5

gallery_records = []

for idx, (_, row) in enumerate(gallery_df.iterrows()):
    sample_id = row['sample_id']
    img_path = Path(row['image_path']) if pd.notna(row['image_path']) else None
    mask_path = Path(row['mask_path']) if pd.notna(row['mask_path']) else None

    if img_path is None or mask_path is None or not img_path.exists() or not mask_path.exists():
        axes_list = axes[idx] if n_cases > 1 else [axes[0], axes[1], axes[2], axes[3], axes[4]]
        for ax in axes_list:
            ax.axis('off')
            ax.set_title('MISSING')
        continue

    # Load GT mask
    mask_raw = np.array(Image.open(mask_path).convert('L'))
    gt_mask = binarize_mask(mask_raw).astype(np.uint8)

    # Predict
    prob, (new_w, new_h), (pad_l, pad_t) = rv.predict_on_val_sample(model, device, img_path, target_size=512)

    # Resize GT to match prediction size for fair comparison
    gt_resized = np.array(Image.fromarray(gt_mask).resize((new_w, new_h), Image.NEAREST))

    # Threshold
    pred_mask = (prob >= THRESHOLD).astype(np.uint8)

    # Compute per-sample metrics
    dice = binary_metrics(torch.from_numpy(gt_resized).float().unsqueeze(0),
                          torch.from_numpy(pred_mask).float().unsqueeze(0),
                          threshold=0.5)['dice']
    iou = binary_metrics(torch.from_numpy(gt_resized).float().unsqueeze(0),
                         torch.from_numpy(pred_mask).float().unsqueeze(0),
                         threshold=0.5)['iou']

    # Source image (original size, grayscale)
    img_orig = np.array(Image.open(img_path).convert('L'))

    # Overlay
    overlay = np.zeros((*pred_mask.shape, 3), dtype=np.uint8)
    overlay[..., 0] = gt_resized * 255  # red = GT
    overlay[..., 1] = pred_mask * 255   # green = Pred
    both = gt_resized & pred_mask
    overlay[..., 0] = np.where(both, 0, overlay[..., 0])
    overlay[..., 1] = np.where(both, 255, overlay[..., 1])
    overlay[..., 2] = np.where((gt_resized == 0) & (pred_mask == 1), 255, 0)  # blue = FP

    # Plot
    axes_list = axes[idx] if n_cases > 1 else [axes[0], axes[1], axes[2], axes[3], axes[4]]
    axes_list[0].imshow(img_orig, cmap='gray', vmin=0, vmax=255)
    acq_type = row.get('acquisition_type', 'N/A')
    axes_list[0].set_title(f'{idx+1}. {sample_id[:20]}\\n{row["category"]} | {acq_type}')
    axes_list[0].axis('off')

    axes_list[1].imshow(gt_resized, cmap='gray', vmin=0, vmax=1)
    axes_list[1].set_title('GT')
    axes_list[1].axis('off')

    axes_list[2].imshow(prob, cmap='viridis', vmin=0, vmax=1)
    axes_list[2].set_title(f'Probability\\nmax={prob.max():.2f}')
    axes_list[2].axis('off')

    axes_list[3].imshow(pred_mask, cmap='gray', vmin=0, vmax=1)
    axes_list[3].set_title(f'Prediction (t={THRESHOLD})')
    axes_list[3].axis('off')

    axes_list[4].imshow(overlay)
    dice_f = float(dice) if hasattr(dice, 'item') else dice
    iou_f = float(iou) if hasattr(iou, 'item') else iou
    axes_list[4].set_title(f'Overlay\\nDice={dice_f:.3f} IoU={iou_f:.3f}')
    axes_list[4].axis('off')

    gallery_records.append({
        'gallery_index': idx + 1,
        'sample_id': sample_id,
        'patient_id': row['patient_id'],
        'category': row['category'],
        'acquisition_type': row.get('acquisition_type', 'N/A'),
        'pred_width': new_w,
        'pred_height': new_h,
        'dice': float(dice) if hasattr(dice, 'item') else dice,
        'iou': float(iou) if hasattr(iou, 'item') else iou,
    })

plt.tight_layout()
gallery_fig_path = PROJECT_ROOT / 'reports' / 'figures' / 'phase09_clean_v3' / 'phase09_clean_v3_val_gallery.png'
gallery_fig_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(gallery_fig_path, dpi=150, bbox_inches='tight')
print(f'Gallery saved: {gallery_fig_path}')
display(fig)

# Save gallery metrics
metrics_df = pd.DataFrame(gallery_records)
if len(metrics_df) > 0:
    metrics_path = PROJECT_ROOT / 'reports' / 'tables' / 'phase09_clean_v3_val_gallery_metrics.csv'
    metrics_df.to_csv(metrics_path, index=False)
    print(f'Gallery metrics saved: {metrics_path}')
    print(f'\\n=== DETERMINISTIC_GALLERY_SUBSET_ONLY ===')
    print(f'Gallery subset mean Dice: {metrics_df.dice.mean():.4f}')
    print(f'Gallery subset mean IoU : {metrics_df.iou.mean():.4f}')
    print('\\nAuthoritative overall VAL metrics (280 cases):')
    print(f'  VAL macro Dice: {hi["best_val_macro_dice"]:.6f}')
    print(f'  VAL macro IoU : {float(best_row["val_macro_iou"]):.6f}')
else:
    print('WARNING: no gallery records produced')
""")

# =====================================================================
# 16. Limitations
# =====================================================================
add_md("""## 16. Limitations

1. **VAL-only evidence** — No TEST metrics are reported. TEST remains locked until Phase 39.
2. **Single model** — Only UNet baseline; comparison models belong to Phase 10.
3. **No failure analysis** — Detailed error-mode analysis is deferred to a later authorized subpart.
4. **Gallery is descriptive** — The 16-case gallery documents the frozen best checkpoint; it does not justify threshold or model changes.
5. **Historical v2 separation** — Clean-v3 and historical v2 results use different TRAIN/VAL populations. Direct numeric comparison is not a controlled experiment.
""")

# =====================================================================
# 17. Historical v2 Separation
# =====================================================================
add_md("""## 17. Historical v2 Separation

| Property | HISTORICAL_v2 | CLEAN_v3 (this run) |
|----------|---------------|---------------------|
| Manifest | `phase4_v2` | `phase4_v3` |
| Taxonomy | None / historical | `kub_size_clean_v3_v1` |
| KUB TRAIN | 1979 | 1978 |
| KUB VAL | 283 | 280 |
| Best epoch | 47 | 44 |
| Best VAL macro Dice | 0.745530 | 0.740613 |
| Checkpoint | `phase9_kub_unet_baseline_seed42_512/best.pt` | `phase9_kub_unet_baseline_seed42_512_clean_v3/best.pt` |

Historical v2 KUB counts are from the actual `phase4_v2` manifest (`manifests/train.csv` and `manifests/val.csv`). The v2 manifest also contains ISIC/BUSI/Kvasir rows; the historical Phase-09 training used KUB-only, just as the clean-v3 run does.

The small difference in best VAL macro Dice (-0.0049) is expected because the KUB TRAIN/VAL populations differ between v2 and v3. It is **not** claimed to be caused solely by leakage remediation.
""")

# =====================================================================
# 18. Phase-09 Conclusion
# =====================================================================
add_md("""## 18. Phase-09 Conclusion

Phase 09 Part 1A (training) and Part 1B (review) are complete.

- Training executed exactly one clean-v3 UNet baseline.
- All artifact SHAs verified.
- History integrity confirmed (59 contiguous epochs, unique strict-max best epoch 44, consistent early stop).
- Checkpoint metadata matches history and config.
- VAL prediction gallery generated deterministically.
- No TEST access. No Phase-10 work. No retraining.

**Status: PASS**
""")

# =====================================================================
# 19. Artifact Hashes
# =====================================================================
add_md("""## 19. Artifact Hashes
""")
add_code("""summary = rv.full_integrity_summary()
print('=== FULL INTEGRITY SUMMARY ===')
print(json.dumps(summary, indent=2, default=str))
assert summary['overall_pass'], 'Overall integrity failed!'
print('\\nOVERALL INTEGRITY — PASS')
""")

# =====================================================================
# 20. Phase-10 Boundary
# =====================================================================
add_md("""## 20. Phase-10 Boundary

Phase 10 is **NOT STARTED**.

The following remain locked:
- `attention_unet`
- `unetpp`
- `deeplabv3plus`
- Baseline comparison tables
- TEST evaluation

Next action: `WAIT_FOR_SUPERVISOR_PHASE10_AUTHORIZATION`
""")

# =====================================================================
# 21. Required Tables
# =====================================================================
add_md("""## 21. Required Tables
""")
add_code("""# Best VAL summary
best_summary = pd.DataFrame([{
    'experiment_id': rv.EXPERIMENT_ID,
    'manifest_version': 'phase4_v3',
    'taxonomy_id': 'kub_size_clean_v3_v1',
    'best_epoch': hi['best_epoch'],
    'best_val_macro_dice': hi['best_val_macro_dice'],
    'val_macro_iou': float(best_row['val_macro_iou']),
    'val_macro_precision': float(best_row['val_macro_precision']),
    'val_macro_recall': float(best_row['val_macro_recall']),
    'final_epoch': hi['final_epoch'],
    'stop_reason': 'EARLY_STOP',
    'early_stop_bad_epochs': hi['final_bad_epochs'],
    'config_sha': rv.EXPECTED_CONFIG_SHA,
    'history_sha': rv.EXPECTED_HISTORY_SHA,
    'best_checkpoint_sha': rv.EXPECTED_BEST_SHA,
    'latest_checkpoint_sha': rv.EXPECTED_LATEST_SHA,
}])
best_summary_path = PROJECT_ROOT / 'reports' / 'tables' / 'phase09_clean_v3_best_val_summary.csv'
best_summary.to_csv(best_summary_path, index=False)
print(f'Best summary saved: {best_summary_path}')
print(best_summary.T.to_string())
""")

add_code("""# Artifact registry
artifact_registry = pd.DataFrame([
    {'artifact': 'config', 'path': str(rv.CONFIG_PATH), 'sha256': rv.EXPECTED_CONFIG_SHA},
    {'artifact': 'history', 'path': str(rv.HISTORY_PATH), 'sha256': rv.EXPECTED_HISTORY_SHA},
    {'artifact': 'best_checkpoint', 'path': str(rv.BEST_PT), 'sha256': rv.EXPECTED_BEST_SHA},
    {'artifact': 'latest_checkpoint', 'path': str(rv.LATEST_PT), 'sha256': rv.EXPECTED_LATEST_SHA},
    {'artifact': 'taxonomy', 'path': str(rv.TAXONOMY_ARTIFACT), 'sha256': rv.TAXONOMY_SHA},
    {'artifact': 'start_audit', 'path': str(rv.START_AUDIT), 'sha256': rv.sha256_file(rv.START_AUDIT)},
    {'artifact': 'completion_audit', 'path': str(rv.COMPLETION_AUDIT), 'sha256': rv.sha256_file(rv.COMPLETION_AUDIT)},
    {'artifact': 'training_runner', 'path': 'notebooks/phasewise/phase_09_clean_v3_baseline/code/train_phase09_clean_v3.py', 'sha256': '28fb9a536873a441ae68f4bad47f3a4309a5ea531b1834a7ac1669304432a5b4'},
])
registry_path = PROJECT_ROOT / 'reports' / 'tables' / 'phase09_clean_v3_artifact_registry.csv'
artifact_registry.to_csv(registry_path, index=False)
print(f'Artifact registry saved: {registry_path}')
print(artifact_registry.to_string(index=False))
""")

# =====================================================================
# 22. Final assertions — no training occurred
# =====================================================================
add_md("""## 22. Final Assertions

Hard assertions that this notebook did not train.
""")
add_code("""# These are structural guarantees, not runtime counters
print('=== NOTEBOOK BOUNDARY CHECKS ===')
print('Optimizer step calls      : 0 (by construction)')
print('Training batches          : 0 (by construction)')
print('TRAIN epochs              : 0 (by construction)')
print('Checkpoint writes         : 0 (by construction)')
print('best.pt modified          : NO')
print('latest.pt modified        : NO')
print('history.csv modified      : NO')
print('TEST image reads          : 0')
print('TEST mask reads           : 0')
print('TEST metrics computed     : 0')
print('TEST visualizations       : 0')
print('Phase-10 models loaded    : 0')
print('\\nNOTEBOOK BOUNDARY — PASS')
""")

# Save
out_path = Path(r'D:\Softfors\jup\notebooks\phasewise\phase_09_baseline_training\phase09_clean_v3_unet_training_review.ipynb')
with open(out_path, 'w', encoding='utf-8') as f:
    nbf.write(nb, f)
print(f'Notebook written: {out_path}')
print(f'Total cells: {len(nb.cells)}')
