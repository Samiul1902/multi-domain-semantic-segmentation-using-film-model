"""Build complete, authoritative Stage-4D notebook 11c_kub_final_localizer_redesign.ipynb."""
import json
from pathlib import Path
import nbformat as nbf

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def build_stage4d_notebook():
    nb = nbf.v4.new_notebook()
    nb.metadata = {
        "language_info": {"name": "python", "version": "3.11.9"},
        "kernelspec": {"name": "python3", "display_name": "Python 3"},
    }

    cells = []

    # Section 1: Title & Phase 13B Context
    cells.append(nbf.v4.new_markdown_cell("""# Phase 13B Stage-4D: Final Bounded Localizer Redesign & Scientific Audit

**Authoritative Research & Audit Notebook**  
**Experiment ID:** `phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_v1`  
**Architecture:** Compact U-Net (`kub_localizer`), 482,449 trainable parameters, 512 input, 128 logit heatmap  
**Status:** COMPLETE -- DISPLAY / ANALYSIS / AUDIT ONLY (No training execution)

---

## 1. Title & Phase 13B Context
This notebook serves as the definitive analysis, validation, and audit record for Phase 13B Stage-4D. Phase 13 investigated predicted-ROI localizers for urinary calculi on full-field KUB radiographs. Following the Stage-4C pilot which proved unpromising due to extreme negative background focal loss penalties on an un-downsampled 512 grid, Stage-4D evaluated a single, pre-registered architectural redesign."""))

    # Section 2: Scientific Motivation
    cells.append(nbf.v4.new_markdown_cell("""## 2. Scientific Motivation
In CenterNet-style focal loss on full $512 \\times 512$ grids ($262,144$ pixels), background pixels vastly outnumber target centers. With small Gaussian targets ($\sigma=3$), the background penalty dominates optimization, suppressing output probabilities to near the prior ($p \\approx 0.10$) and failing to learn sharp peaks.

Stage-4D introduces a pre-registered, one-factor geometric architectural redesign: extracting logits into a fixed, parameter-free stride-4 average pooling operation (`AvgPool2d(4, 4)`), producing a $128 \\times 128$ output heatmap ($16,384$ pixels). This delivers a **16x reduction** in background pixel penalty while preserving the full 512-input backbone feature hierarchy."""))

    # Section 3: Frozen Stage-4C Reference
    cells.append(nbf.v4.new_markdown_cell("""## 3. Frozen Stage-4C Reference Baseline
The reference benchmark for Stage-4D is the clean Stage-4C V3 pilot:
- **Experiment:** `phase13b_kub_localizer_r512_s3_centernetfocal_seed42_v3`
- **Output Grid:** $512 \\times 512$ (262,144 px)
- **Target Sigma:** $\sigma = 3.0$
- **Best Epoch:** 97
- **Tiny Recall@90:** $34 / 73 = 46.58\%$ ($0.465753$)
- **Overall Recall@90:** $44 / 156 = 28.21\%$ ($0.282051$)
- **Hard Tiny (missed by global models):** $1 / 16$ ($6.25\%$)
- **Global-Empty Images Covered:** $1 / 7$ ($14.29\%$)
- **Mean ROI Area Fraction:** $\sim 0.000863$ ($0.09\%$)
- **Mean Proposals per Image:** $\sim 3.179245$
- **Mean Max Heatmap Probability:** $\sim 0.100299$
- **Scientific Status:** `NOT_PROMISING`"""))

    # Section 4: Stage-4D Pre-registered Controlled Redesign
    cells.append(nbf.v4.new_markdown_cell("""## 4. Stage-4D Pre-registered Controlled Redesign
Stage-4D modifies exactly one architectural factor:
- Input resolution remains $512 \\times 512$.
- Feature extractor backbone remains identical (base channels 16, 4 stages).
- Total trainable parameters remain exactly **482,449**.
- A parameter-free average pooling layer (`nn.AvgPool2d(kernel_size=4, stride=4)`) reduces logit resolution from $512 \\times 512$ to $128 \\times 128$ before computing CenterNet focal loss.
- Target Gaussian standard deviation is scaled to $\sigma = 0.75$ at $128 \\times 128$, maintaining exact geometric equivalence with $\sigma = 3.0$ at $512 \\times 512$."""))

    # Section 5: Architecture Control
    cells.append(nbf.v4.new_markdown_cell("""## 5. Architecture Control: Parameter and Capacity Parity
The localizer model `src/models/kub_localizer.py` implements the parameter-free logit pool:
$$\\text{Trainable Parameters: } 482,449 \\quad (\\text{identical between Stage-4C and Stage-4D})$$"""))

    # Code cell: Setup, Environment & Test Lock
    cells.append(nbf.v4.new_code_cell("""import sys
import os
import json
import hashlib
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from IPython.display import Image, display

# Locate project root
cwd = Path.cwd().resolve()
if (cwd / 'experiments').is_dir():
    PROJECT_ROOT = cwd
elif (cwd.parent / 'experiments').is_dir():
    PROJECT_ROOT = cwd.parent
else:
    PROJECT_ROOT = Path('D:/Softfors/jup').resolve()

assert (PROJECT_ROOT / 'experiments').is_dir(), f"Cannot locate valid project root: {PROJECT_ROOT}"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
print(f"Authoritative Project Root: {PROJECT_ROOT}")

from src.utils.test_lock import verify_test_lock
from src.utils.manifest_guard import verify_manifests

verify_manifests()
lock = verify_test_lock(PROJECT_ROOT)
print("Manifest verification: PASS")
print(f"TEST Lock: STRICTLY VERIFIED (0 content reads authorized, manifest {lock['manifest_version']})")
"""))

    # Section 6: 512 -> 128 Fixed Logit Pooling Design
    cells.append(nbf.v4.new_markdown_cell("""## 6. 512 -> 128 Fixed Logit Pooling Design & Implementation
Logit pooling averages 16 spatial logits per pool window, effectively downsampling the supervision target while operating on full 512 receptive fields."""))

    # Section 7: Sigma Geometric Equivalence
    cells.append(nbf.v4.new_markdown_cell("""## 7. Sigma Geometric Equivalence
$$\\sigma_{128} = \\frac{\\sigma_{512}}{4} = \\frac{3.0}{4} = 0.75 \\text{ pixels}$$
At $\sigma = 0.75$, a $3 \\times 3$ kernel covers $\pm 2\\sigma$ ($1.5$ pixels in 128-space, equivalent to $6$ pixels in 512-space)."""))

    # Section 8: Preflight Geometry & Collision Audit
    cells.append(nbf.v4.new_markdown_cell("""## 8. Preflight Geometry & Collision Audit (Stage-4D-R1)
Before training, Stage-4D-R1 preflight verified that mapping center coordinates from 512 to 128 space caused zero component collisions across all 1,162 TRAIN and 156 VAL objects."""))

    # Code cell: Geometry audit
    cells.append(nbf.v4.new_code_cell("""geom_path = PROJECT_ROOT / 'reports/tables/phase13b_stage4d_r1_geometry.csv'
if geom_path.exists():
    geom_df = pd.read_csv(geom_path)
    print("Stage-4D-R1 Geometry Audit:")
    display(geom_df)
else:
    print(f"Table not found: {geom_path}")
"""))

    # Section 9: Initialization / Loss-Burden Diagnostic
    cells.append(nbf.v4.new_markdown_cell("""## 9. Initialization & Loss-Burden Diagnostic
Stage-4D-R1 confirmed that initial bias initialization ($b = -2.19$) yields $p \\approx 0.10$ and reduces the negative background focal loss burden by ~16x."""))

    # Code cell: Loss diagnostic audit
    cells.append(nbf.v4.new_code_cell("""loss_diag_path = PROJECT_ROOT / 'reports/tables/phase13b_stage4d_r1_loss_diagnostic.csv'
if loss_diag_path.exists():
    loss_diag = pd.read_csv(loss_diag_path)
    print("Stage-4D-R1 Loss Diagnostic:")
    display(loss_diag)
else:
    print(f"Table not found: {loss_diag_path}")
"""))

    # Section 10: Training Configuration & Registry Audit
    cells.append(nbf.v4.new_markdown_cell("""## 10. Training Configuration & Registry Record
- **Optimizer:** AdamW ($lr=1e-4, wd=1e-4$)
- **Scheduler:** CosineAnnealingLR (T_max=100)
- **Batch Size:** 4 (Effective batch size: 4)
- **Seed:** 42
- **Loss:** CenterNetFocalLoss ($\alpha=2.0, \beta=4.0, \sigma=0.75$)"""))

    # Code cell: Registry check
    cells.append(nbf.v4.new_code_cell("""registry = pd.read_csv(PROJECT_ROOT / 'experiments/registry.csv')
exp_id = "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_v1"
exp_record = registry[registry['experiment_id'] == exp_id]
display(exp_record[['experiment_id', 'status', 'start_time', 'end_time', 'loss', 'notes']])
"""))

    # Section 11: Power Interruption & Resume Provenance
    cells.append(nbf.v4.new_markdown_cell("""## 11. Power Interruption & Safe Resume Provenance
A simulated/actual power cut occurred during training at epoch 84:
1. Clean training began from epoch 0 and proceeded normally through epoch 84.
2. An unexpected power interruption halted execution.
3. Process inventory confirmed zero active training processes.
4. `latest.pt` at epoch 84 was verified intact; `history.csv` matched checkpoint state exactly.
5. Optimizer, scheduler, GradScaler, patience counters (11/15), and model weights were faithfully restored.
6. The SAME experiment ID resumed at epoch 85 and terminated at epoch 88 via early stopping (best epoch 73, patience 15/15).
7. Checkpoint and history integrity audits confirmed zero duplicate or missing epochs. No scientific invalidation occurred."""))

    # Section 12: Complete History Integrity
    cells.append(nbf.v4.new_markdown_cell("""## 12. Complete History Integrity Verification"""))

    # Code cell: History check
    cells.append(nbf.v4.new_code_cell("""hist_path = PROJECT_ROOT / f'experiments/{exp_id}/history.csv'
hist = pd.read_csv(hist_path)
epochs = hist['epoch']
print(f"Total recorded epochs: {len(hist)}")
print(f"Epoch range: {hist['epoch'].min()} to {hist['epoch'].max()}")
print(f"Duplicate epochs: {hist['epoch'].duplicated().sum()}")
print(f"Missing epochs: {set(range(1, len(hist) + 1)) - set(hist['epoch'])}")
assert len(hist) == 88, f"Expected 88 epochs, found {len(hist)}"
assert hist['epoch'].duplicated().sum() == 0, "Duplicate epochs found!"
print("History Integrity: PASS")
"""))

    # Section 13: Loss by Epoch Display
    cells.append(nbf.v4.new_markdown_cell("""## 13. Loss Trajectory Across Epochs
CenterNet Focal Loss trajectory on train and validation splits."""))

    # Code cell: Loss plot / display fig_a
    cells.append(nbf.v4.new_code_cell("""fig_a = PROJECT_ROOT / 'reports/figures/phase13b_stage4d_final_localizer/fig_a_loss_by_epoch.png'
if fig_a.exists():
    display(Image(filename=str(fig_a)))
else:
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(epochs, hist['train_loss'], label='Train Loss', color='#1f77b4')
    ax.plot(epochs, hist['val_loss'], label='Val Loss', color='#ff7f0e')
    ax.set_title('CenterNet Focal Loss vs Epoch')
    ax.legend()
    plt.show()
"""))

    # Section 14: Recall by Epoch Display
    cells.append(nbf.v4.new_markdown_cell("""## 14. Validation Recall@90 Trajectory Across Epochs
Evolution of validation Tiny Recall@90 and Overall Recall@90 relative to the 0.50 Stage-4D threshold."""))

    # Code cell: Recall plot / display fig_b
    cells.append(nbf.v4.new_code_cell("""fig_b = PROJECT_ROOT / 'reports/figures/phase13b_stage4d_final_localizer/fig_b_recall_by_epoch.png'
if fig_b.exists():
    display(Image(filename=str(fig_b)))
else:
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(epochs, hist['val_tiny_recall90'], label='Val Tiny Recall@90', color='#2ca02c')
    ax.plot(epochs, hist['val_overall_recall90'], label='Val Overall Recall@90', color='#9467bd')
    ax.axhline(0.50, color='r', linestyle='--', label='Stage-4D Target (0.50)')
    ax.set_title('Recall@90 Progression vs Epoch')
    ax.legend()
    plt.show()
"""))

    # Section 15: Hard Cases Evolution
    cells.append(nbf.v4.new_markdown_cell("""## 15. Hard Cases (Hard Tiny & Global Empty) Evolution
Tracking recovery of 16 Hard Tiny calculi and 7 global-empty images."""))

    # Code cell: Hard cases plot / display fig_c
    cells.append(nbf.v4.new_code_cell("""fig_c = PROJECT_ROOT / 'reports/figures/phase13b_stage4d_final_localizer/fig_c_hard_cases_by_epoch.png'
if fig_c.exists():
    display(Image(filename=str(fig_c)))
else:
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(epochs, hist['val_hard_tiny_recovered90'], label='Hard Tiny Recovered (/16)', color='#d62728')
    ax.plot(epochs, hist['val_global_empty_images_covered90'], label='Global Empty Covered (/7)', color='#8c564b', linestyle='--')
    ax.set_title('Hard Case Recovery vs Epoch')
    ax.legend()
    plt.show()
"""))

    # Section 16: Heatmap Confidence Evolution
    cells.append(nbf.v4.new_markdown_cell("""## 16. Heatmap Peak Probability Evolution
Mean and median maximum validation heatmap probabilities rising above the $0.10$ prior."""))

    # Code cell: Heatmap prob plot / display fig_d
    cells.append(nbf.v4.new_code_cell("""fig_d = PROJECT_ROOT / 'reports/figures/phase13b_stage4d_final_localizer/fig_d_heatmap_probs_by_epoch.png'
if fig_d.exists():
    display(Image(filename=str(fig_d)))
else:
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(epochs, hist['mean_max_heatmap'], label='Mean Max Heatmap', color='#e377c2')
    ax.plot(epochs, hist['median_max_heatmap'], label='Median Max Heatmap', color='#7f7f7f', linestyle='--')
    ax.axhline(0.10, color='blue', linestyle=':', label='Initial Prior (0.10)')
    ax.set_title('Heatmap Peak Probability Dynamics')
    ax.legend()
    plt.show()
"""))

    # Section 17: ROI Area Evolution
    cells.append(nbf.v4.new_markdown_cell("""## 17. Union ROI Area Fraction Evolution
Union ROI area fraction staying well below the feasibility bound of $0.10$ ($10\\%$ of image area)."""))

    # Code cell: ROI area plot / display fig_e
    cells.append(nbf.v4.new_code_cell("""fig_e = PROJECT_ROOT / 'reports/figures/phase13b_stage4d_final_localizer/fig_e_roi_area_by_epoch.png'
if fig_e.exists():
    display(Image(filename=str(fig_e)))
"""))

    # Section 18: Proposal Count Evolution
    cells.append(nbf.v4.new_markdown_cell("""## 18. Proposal Generation Burden Evolution
Mean proposals per image staying below the feasibility limit of $\\le 5.0$."""))

    # Code cell: Proposals plot / display fig_f
    cells.append(nbf.v4.new_code_cell("""fig_f = PROJECT_ROOT / 'reports/figures/phase13b_stage4d_final_localizer/fig_f_proposals_by_epoch.png'
if fig_f.exists():
    display(Image(filename=str(fig_f)))
"""))

    # Section 19: Canonical Best Epoch & Selected Configuration & Proposal Grid Audit
    cells.append(nbf.v4.new_markdown_cell("""## 19. Canonical Selected Configuration & Proposal Search Grid Audit
Best epoch: **73** (early stopping at epoch 88 with patience 15/15).
Selected proposal configuration under the pre-registered lexicographic ranking rule:
- **Threshold:** `0.10`
- **Margin:** `0.20`
- **TopK:** `5`
- **NMS IoU:** `0.30`

The 20-configuration proposal search grid (`phase13b_stage4d_proposal_grid.csv`) was evaluated across thresholds {0.1, 0.2, 0.3, 0.4, 0.5}, margins {0.10, 0.20}, top_k {3, 5}, and NMS IoU 0.30."""))

    # Code cell: Selected config table & proposal grid audit
    cells.append(nbf.v4.new_code_cell("""# 1. Selected Configuration Table
sel_cfg_path = PROJECT_ROOT / 'reports/tables/phase13b_stage4d_selected_config.csv'
sel_cfg = pd.read_csv(sel_cfg_path)
print("Canonical Selected Configuration:")
display(sel_cfg)

# 2. Proposal Grid Audit
grid_path = PROJECT_ROOT / 'reports/tables/phase13b_stage4d_proposal_grid.csv'
assert grid_path.exists(), f"Proposal grid artifact missing: {grid_path}"
grid_df = pd.read_csv(grid_path)
print("Proposal Search Grid:", len(grid_df), "configurations evaluated")
assert len(grid_df) == 20, f"Expected 20 grid configurations, found {len(grid_df)}"

# Verify canonical configuration presence in grid
match = grid_df[
    (grid_df['threshold'] == 0.10) & 
    (grid_df['margin'] == 0.20) & 
    (grid_df['top_k'] == 5) & 
    (grid_df['nms_iou'] == 0.30)
]
assert len(match) == 1, "Canonical selected configuration not found uniquely in proposal grid!"
print("Canonical config verified in proposal grid: PASS")
display(grid_df[['threshold', 'margin', 'top_k', 'nms_iou', 'tiny_recall90', 'overall_recall90', 'hard_tiny_recovered90', 'mean_roi_area_fraction', 'mean_proposals_per_image', 'feasible']])
"""))

    # Section 20: Size-Stratified Results
    cells.append(nbf.v4.new_markdown_cell("""## 20. Size-Stratified Localization Performance
Breakdown across calculus size strata defined by `kub_size_v1` on the 106 KUB validation images."""))

    # Code cell: Size summary table and fig_h
    cells.append(nbf.v4.new_code_cell("""size_path = PROJECT_ROOT / 'reports/tables/phase13b_stage4d_size_summary.csv'
size_df = pd.read_csv(size_path)
display(size_df)

fig_h = PROJECT_ROOT / 'reports/figures/phase13b_stage4d_final_localizer/fig_h_size_stratified_recall.png'
if fig_h.exists():
    display(Image(filename=str(fig_h)))
"""))

    # Section 21: Hard Tiny Result
    cells.append(nbf.v4.new_markdown_cell("""## 21. Hard Tiny Calculus Localization Analysis
Detailed audit of the 16 Hard Tiny calculi missed by standard full-field global segmentation models."""))

    # Code cell: Hard tiny table
    cells.append(nbf.v4.new_code_cell("""comp_path = PROJECT_ROOT / 'reports/tables/phase13b_stage4d_best_val_per_component.csv'
comp_df = pd.read_csv(comp_path)
hard_tiny = comp_df[comp_df['hard_tiny'] == True]
display(hard_tiny[['sample_id', 'component_id', 'coverage_fraction', 'covered90', 'covered50', 'any_overlap', 'best_proposal_rank', 'best_proposal_score']])
print(f"Hard Tiny Recovered@90: {hard_tiny['covered90'].sum()} / 16 ({hard_tiny['covered90'].mean():.2%})")
"""))

    # Section 22: Global-Empty Result
    cells.append(nbf.v4.new_markdown_cell("""## 22. Global-Empty Image Case Analysis
Evaluation of the 7 validation images where global segmentation models produced 0 foreground pixels."""))

    # Code cell: Global empty table
    cells.append(nbf.v4.new_code_cell("""img_path = PROJECT_ROOT / 'reports/tables/phase13b_stage4d_best_val_per_image.csv'
img_df = pd.read_csv(img_path)
empty_imgs = img_df[img_df['global_empty_image'] == True]
display(empty_imgs[['sample_id', 'num_gt_components', 'num_covered90', 'num_proposals', 'roi_area_fraction']])
print(f"Global Empty Images Covered@90: {(empty_imgs['num_covered90'] > 0).sum()} / 7")
"""))

    # Section 23: Stage-4C vs Stage-4D Comparison
    cells.append(nbf.v4.new_markdown_cell("""## 23. Milestone Comparison: Stage-4C (512-grid) vs Stage-4D (128-grid)
Direct comparison between the un-downsampled 512-grid CenterNet model and the redesigned 128-grid model."""))

    # Code cell: Comparison table & fig_g
    cells.append(nbf.v4.new_code_cell("""fig_g = PROJECT_ROOT / 'reports/figures/phase13b_stage4d_final_localizer/fig_g_stage4c_vs_stage4d_comparison.png'
if fig_g.exists():
    display(Image(filename=str(fig_g)))

comp_data = [
    {"Metric": "Output Heatmap Grid", "Stage-4C V3 (Clean)": "512 x 512 (262,144 px)", "Stage-4D Redesign": "128 x 128 (16,384 px)"},
    {"Metric": "Target Sigma", "Stage-4C V3 (Clean)": "3.0 pixels", "Stage-4D Redesign": "0.75 pixels (geometrically equivalent)"},
    {"Metric": "Negative Focal Penalty", "Stage-4C V3 (Clean)": "1.0x (Overwhelming)", "Stage-4D Redesign": "~16.0x reduction"},
    {"Metric": "Best Validation Epoch", "Stage-4C V3 (Clean)": "97", "Stage-4D Redesign": "73"},
    {"Metric": "Tiny Recall@90", "Stage-4C V3 (Clean)": "46.58% (34 / 73)", "Stage-4D Redesign": "72.60% (53 / 73)"},
    {"Metric": "Overall Recall@90", "Stage-4C V3 (Clean)": "28.21% (44 / 156)", "Stage-4D Redesign": "64.10% (100 / 156)"},
    {"Metric": "Hard Tiny Recovered@90", "Stage-4C V3 (Clean)": "1 / 16 (6.25%)", "Stage-4D Redesign": "7 / 16 (43.75%)"},
    {"Metric": "Global-Empty Covered@90", "Stage-4C V3 (Clean)": "1 / 7 (14.29%)", "Stage-4D Redesign": "3 / 7 (42.86%)"},
    {"Metric": "Mean Union ROI Area Fraction", "Stage-4C V3 (Clean)": "0.000863 (0.09%)", "Stage-4D Redesign": "0.005899 (0.59%)"},
    {"Metric": "Mean Proposals per Image", "Stage-4C V3 (Clean)": "3.18", "Stage-4D Redesign": "4.66"},
    {"Metric": "Mean Max Heatmap Probability", "Stage-4C V3 (Clean)": "~0.1003", "Stage-4D Redesign": "0.1388"},
]
comp_df = pd.DataFrame(comp_data)
display(comp_df)
"""))

    # Section 24: Stage-4D Continuation Gate Evaluation
    cells.append(nbf.v4.new_markdown_cell("""## 24. Stage-4D Continuation Gate Evaluation
Evaluation against the 5 pre-registered Stage-4D gate criteria:
- **Gate A (Tiny Recall@90 $\\ge 0.50$):** $0.726027$ (**PASS**)
- **Gate B (Overall Recall@90 $\\ge 0.50$):** $0.641026$ (**PASS**)
- **Gate C (Hard Tiny $\\ge 2/16$):** $7 / 16$ (**PASS**)
- **Gate D (Mean ROI Area $\\le 0.10$):** $0.005899$ (**PASS**)
- **Gate E (Mean Proposals $\\le 5.0$):** $4.660377$ (**PASS**)"""))

    # Code cell: Gate evaluation
    cells.append(nbf.v4.new_code_cell("""gate_path = PROJECT_ROOT / 'reports/tables/phase13b_stage4d_gate_evaluation.csv'
gate_df = pd.read_csv(gate_path)
display(gate_df)
assert gate_df['passed'].all(), "Stage-4D Continuation Gate did not pass all criteria!"
print("Stage-4D Continuation Gate: ALL 5 CRITERIA PASSED")
"""))

    # Section 25: Scientific Interpretation
    cells.append(nbf.v4.new_markdown_cell("""## 25. Scientific Interpretation
The Stage-4D result is consistent with the pre-registered hypothesis that reducing the dense heatmap/loss grid can improve compact center localization under this configuration. 

By relieving the overwhelming background focal loss penalty via fixed stride-4 logit pooling, the network escaped the $p \\approx 0.10$ prior and learned calibrated peaks for urinary calculi. However, this does not constitute proof of background dominance as the sole failure mechanism, nor does it claim universal superiority or clinical readiness."""))

    # Section 26: Limitations
    cells.append(nbf.v4.new_markdown_cell("""## 26. Scientific Limitations
1. **Validation-Only Scope:** All metrics reflect performance strictly on the 106 KUB validation images. The TEST split remains locked.
2. **Single Seed:** Results reflect seed 42. Variance across initializations is unmeasured.
3. **Downstream Uncoupled:** Proposals have not yet been processed by a second-stage refiner model."""))

    # Section 27: Cryptographic Provenance & Checkpoint Verification
    cells.append(nbf.v4.new_markdown_cell("""## 27. Provenance, Checkpoint Hashes & Discrepancy Reconciliation

### Metric Discrepancy Reconciliation:
Online/recovery monitoring and final canonical evaluation differed for some metrics (e.g. 6/16 vs 7/16 Hard Tiny) because the online path used a fast, approximate tracking accumulator, whereas the canonical offline evaluation (`evaluate_phase13b_stage4d.py`) used fully formed proposal and component matching evaluation. Canonical publication values are from the frozen final evaluation.

### Cryptographic Checkpoint Verification:"""))

    # Code cell: Checkpoint verification
    cells.append(nbf.v4.new_code_cell("""def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

best_pt = PROJECT_ROOT / f'checkpoints/{exp_id}/best.pt'
latest_pt = PROJECT_ROOT / f'checkpoints/{exp_id}/latest.pt'

best_sha = sha256_file(best_pt)
latest_sha = sha256_file(latest_pt)
expected_best_sha = "ece906df6c73f2e93c3f873661490bf3cb1a6b82be2d2d93b58c25bc967cbace"

print(f"best.pt SHA-256:   {best_sha}")
print(f"Expected SHA-256:  {expected_best_sha}")
assert best_sha == expected_best_sha, f"SHA mismatch on best.pt! Expected {expected_best_sha}, got {best_sha}"
print("Checkpoint Integrity: PASS")
"""))

    # Section 28: Final Phase-13B Status
    cells.append(nbf.v4.new_markdown_cell("""## 28. Final Phase-13B Status & Roadmap Boundary

```
PHASE 13B:
COMPLETE

PHASE 13:
COMPLETE / FROZEN

FINAL LOCALIZER:
PROMISING_VALIDATED_ON_VAL

PHASE 14 ENTRY GATE:
NOT_PASSED

PHASE 14:
CLOSED WITHOUT EXECUTION

TEST CONTENT READS:
0

TEST METRICS:
NONE

EXTERNAL:
NO

NEXT SCIENTIFIC PHASE:
NOT STARTED
```"""))

    # PERMANENT FIX: Explicitly assign populated cells to nb.cells before writing
    nb.cells = cells

    target_nb_path = PROJECT_ROOT / "notebooks/11c_kub_final_localizer_redesign.ipynb"
    with open(target_nb_path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print(f"Authoritative notebook generated successfully at: {target_nb_path}")
    print(f"Total cells: {len(nb.cells)} (Markdown: {sum(1 for c in nb.cells if c.cell_type == 'markdown')}, Code: {sum(1 for c in nb.cells if c.cell_type == 'code')})")


if __name__ == "__main__":
    build_stage4d_notebook()
