"""
Phase 13 Part 1A — Historical localizer-protocol reconstruction + CLEAN-v3 prospective
localizer/proposal protocol-freeze candidate support (READ-ONLY).

Part 1A is a PROTOCOL / DEFINITION phase. It does NOT train a localizer, does NOT run
localizer inference, does NOT generate proposals, and does NOT touch the regional refiner.

Forbidden here: localizer training, localizer inference, proposal generation on real
images, checkpoint/history/config/manifest changes, TEST access, Phase 14, Phases 15-18,
RA-MedFiLM implementation, winner or single-reference architecture selection.

Historical facts are reconstructed from repository artifacts using the source-precedence
ladder:
  1. executing source code      -> src/models/kub_localizer.py,
                                   src/inference/learned_roi.py,
                                   src/inference/predicted_roi.py,
                                   src/inference/heatmap_targets.py,
                                   src/data/kub_localizer_dataset.py
  2. persisted audit/table      -> reports/audits/phase13b_*.json/.md,
                                   reports/tables/phase13b_stage4d_*.csv,
                                   experiments/phase13b_*/history.csv
  3. executed historical notebook -> notebooks/11c_kub_final_localizer_redesign.ipynb,
                                   notebooks/11_kub_predicted_roi_localizer.ipynb
  4. frozen protocol / README   -> PHASE13B.md,
                                   notebooks/phasewise/phase_13_predicted_roi_localization/README.md
  5. prose/comment

Downstream (Phase-14) evidence is read only to characterise the historical
train/inference proposal-distribution relationship; Phase 14 is NOT re-run.

Author: WorkBuddy AI (Agent mode)
Date: 2026-09-21
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

PROJECT_ROOT = Path(r'D:\Softfors\jup')
REPORTS = PROJECT_ROOT / 'reports'
TABLES = REPORTS / 'tables'
AUDITS = REPORTS / 'audits'
EXPERIMENTS = PROJECT_ROOT / 'experiments'
CHECKPOINTS = PROJECT_ROOT / 'checkpoints'

PHASE_DIR = PROJECT_ROOT / 'notebooks/phasewise/phase_13_predicted_roi_localization'

# ---------------------------------------------------------------------------
# Frozen identities
# ---------------------------------------------------------------------------
MANIFEST_CLEAN = 'phase4_v3'
MANIFEST_HIST = 'phase4_v2'
TAXONOMY_CLEAN = 'kub_size_clean_v3_v1'
TAXONOMY_HIST = 'kub_size_v1'

STAGE4D_EXPERIMENT = 'phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_v1'
STAGE4D_BEST_SHA = 'ece906df6c73f2e93c3f873661490bf3cb1a6b82be2d2d93b58c25bc967cbace'
STAGE4D_LATEST_SHA = 'a1461df2e8d6784984337c79b87c65833c39fed16382579088d97d7c60ba78f4'

# Verified handoff claims from the Phase-13 -> Phase-13 Part-1A handoff note
HANDOFF_CLAIMS = [
    ('Stage-4D best.pt SHA-256', STAGE4D_BEST_SHA, 'VERIFIED'),
    ('Stage-4D best_epoch', 73, 'VERIFIED'),
    ('Stage-4D total_epochs', 88, 'VERIFIED'),
    ('selected threshold', 0.1, 'VERIFIED'),
    ('selected margin', 0.2, 'VERIFIED'),
    ('selected top_k', 5, 'VERIFIED'),
    ('selected nms_iou', 0.3, 'VERIFIED'),
    ('Tiny recall90 numerator/denominator', '53/73', 'VERIFIED'),
    ('Overall recall90 numerator/denominator', '100/156', 'VERIFIED'),
]

# ---------------------------------------------------------------------------
# Clean-v3 population (computed once from TRAIN/VAL masks; cached, TEST never read)
# ---------------------------------------------------------------------------
POPULATION_CENSUS = {
    'TRAIN': {'images': 770, 'components': 1161, 'max_components_per_image': 11,
              'images_gt_5_components': 15, 'images_zero_components': 0},
    'VAL': {'images': 103, 'components': 152, 'max_components_per_image': 2,
            'images_gt_5_components': 0, 'images_zero_components': 0},
}
POPULATION_CENSUS_CACHE = AUDITS / 'phase13_population_census_cache.json'

# clean-v3 VAL FULL_FIELD size strata (from reports/tables/phase12_clean_v3_oracle_geometry.csv)
VAL_STRATA_CLEAN = {'TINY': 72, 'SMALL': 28, 'MEDIUM': 36, 'LARGE': 16}
# historical v2 VAL FULL_FIELD size strata (from reports/tables/kub_val_components_sized.csv)
VAL_STRATA_HIST = {'TINY': 73, 'SMALL': 29, 'MEDIUM': 36, 'LARGE': 18}

# Phase-12 clean-v3 oracle upper bound (authoritative, read-only reference)
PHASE12_GLOBAL_DICE = {'UNet': 0.594180, 'Attention U-Net': 0.629805,
                       'UNet++': 0.640516, 'DeepLabV3+': 0.560251}
PHASE12_ORACLE_DICE = {'UNet': 0.724722, 'Attention U-Net': 0.699595,
                       'UNet++': 0.726679, 'DeepLabV3+': 0.750372}
PHASE12_OBJECT_RECALL = {'UNet': (0.7864, 0.9951), 'Attention U-Net': (0.8544, 0.9951),
                         'UNet++': (0.8398, 0.9951), 'DeepLabV3+': (0.7621, 1.0)}

# Phase-14 diagnostic gate constants (historical v2 coverage90 arithmetic)
PHASE14_GATE = {'T_g': 0.780822, 'T_o': 1.000000, 'T_p': 0.890411,
                'G': 0.219178, 'R': 0.500000,
                'D_g': 0.652776, 'D_o': 0.815175, 'D_p': 0.383905}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def _sha(rel: str) -> str:
    p = PROJECT_ROOT / rel
    return sha256_file(p) if p.is_file() else 'N/A'


# ---------------------------------------------------------------------------
# §1 Historical source inventory
# ---------------------------------------------------------------------------
HISTORICAL_SOURCES = [
    ('src/models/kub_localizer.py', 'executing_source', 1,
     'KUBLocalizer: 3-stage compact U-Net, base_channels 16, 1->1 channel objectness logit '
     'head initialised to p=0.10; optional AvgPool2d(stride) logit downsample'),
    ('src/inference/learned_roi.py', 'executing_source', 1,
     'predict_localizer + generate_localizer_rois (GT-free proposal API)'),
    ('src/inference/predicted_roi.py', 'executing_source', 1,
     'extract_predicted_components / non_max_suppression / apply_context_margin / '
     'generate_predicted_rois / evaluate_roi_coverage / union_roi_area_fraction'),
    ('src/inference/heatmap_targets.py', 'executing_source', 1,
     'make_gaussian_heatmap (pixelwise MAX, centre forced to 1.0) + '
     'get_component_centroids_in_localizer_space'),
    ('src/data/kub_localizer_dataset.py', 'executing_source', 1,
     'KUBLocalizerDataset: FULL_FIELD only, 8-connectivity native components, TRAIN '
     'augmentation (mirror, +/-5deg, brightness/contrast 0.9-1.1), TEST blocked'),
    ('configs/kub/phase13b_localizer.yaml', 'frozen_config', 2,
     '13B grid: resolutions [512,768], sigmas [3,5,7], soft_focal_dice 0.75/0.25, '
     'AdamW 1e-4/1e-4, Cosine T_max 100, max_epochs 100, patience 15'),
    ('PHASE13B.md', 'frozen_protocol', 2,
     'Historical Phase-13B protocol: lexicographic model selection, Phase-14 gate A-F'),
    ('reports/audits/phase13_predicted_roi_localizer.json', 'persisted_audit', 2,
     'Phase-13 SIMPLE predicted-ROI localizer (no learning): selected 0.5/0.15/3/0.30, '
     'overall recall90 0.743590, Tiny 0.684932, gate WEAK'),
    ('reports/audits/phase13b_stage3_validation_correction.md', 'persisted_audit', 2,
     'Stage-3 correction: unapproved class-balancing removed; selection hierarchy frozen'),
    ('reports/audits/phase13b_stage4b_feasible_selection.md', 'persisted_audit', 2,
     'Stage-4B feasibility constraints (ROI area <= 0.10, proposals <= 5)'),
    ('reports/audits/phase13b_stage4c_loss_redesign.md', 'persisted_audit', 2,
     'Stage-4C CenterNet focal pilot: target peaks not exactly 1.0 -> CHECK_REQUIRED, '
     'training not started'),
    ('reports/audits/phase13b_stage4c_r3_component_mapping.md', 'persisted_audit', 2,
     'Stage-4C-R3 component mapping: 1162/1162 mapped, 0 collisions, 0 zero-centre samples'),
    ('reports/audits/phase13b_stage4c_r4_centernet_pilot.md', 'persisted_audit', 2,
     'Stage-4C-R4 CenterNet pilot at epoch 97: Tiny 0.465753, overall 0.301282, 1/16, 1/7'),
    ('reports/audits/phase13b_stage4d_design_audit.json', 'persisted_audit', 2,
     'Stage-4D design audit: dense-background dominance diagnosis, 128 output resolution '
     'recommendation, sigma 0.75, frozen variables'),
    ('reports/audits/phase13b_stage4d_r1_preflight.md', 'persisted_audit', 2,
     'Stage-4D-R1 preflight: AvgPool2d(4,4) 512->128, 482,449 params unchanged, '
     'logit init commutes exactly, 1162/156 components mapped'),
    ('reports/audits/phase13b_stage4d_final_evaluation.json', 'persisted_audit', 2,
     'AUTHORITATIVE Stage-4D-R2 evaluation: best_epoch 73/88, Tiny 53/73, overall 100/156'),
    ('reports/audits/phase13_final_completion_audit.md', 'persisted_audit', 2,
     'Phase-13 final completion / freeze; notebook 11C provenance note'),
    ('reports/audits/phase13b_notebook_validation.md', 'persisted_audit', 2,
     '13B reviewer notebook validation'),
    ('reports/audits/phase13b_stage4d_notebook_validation.md', 'persisted_audit', 2,
     'Notebook 11C validation: 46 cells, 18 executed, 0 errors, no training/TEST access'),
    ('reports/tables/phase13b_stage4d_selected_config.csv', 'persisted_table', 2,
     'Selected Stage-4D proposal configuration and gate metrics'),
    ('reports/tables/phase13b_stage4d_proposal_grid.csv', 'persisted_table', 2,
     '20-config VAL-only proposal grid; only 4 non-degenerate rows'),
    ('reports/tables/phase13b_stage4d_gate_evaluation.csv', 'persisted_table', 2,
     'Stage-4D pilot-gate criteria A-E'),
    ('reports/tables/phase13b_stage4d_size_summary.csv', 'persisted_table', 2,
     'Stage-4D size-stratified localization summary'),
    ('reports/tables/phase13b_stage4d_best_val_per_component.csv', 'persisted_table', 2,
     'Stage-4D per-component coverage at best epoch'),
    ('reports/tables/phase13b_stage4d_best_val_per_image.csv', 'persisted_table', 2,
     'Stage-4D per-image coverage/proposals at best epoch'),
    ('reports/tables/phase13b_stage4d_r1_geometry.csv', 'persisted_table', 2,
     'Stage-4D-R1 geometry audit (stride-4 round-trip error)'),
    ('reports/tables/phase13b_stage4d_r1_loss_diagnostic.csv', 'persisted_table', 2,
     'Stage-4D-R1 loss/gradient diagnostics 512 vs 128'),
    ('reports/tables/phase13_predicted_roi_selected_config.csv', 'persisted_table', 2,
     'Phase-13 SIMPLE predicted-ROI selected configuration'),
    ('reports/tables/phase13_predicted_roi_search.csv', 'persisted_table', 2,
     'Phase-13 SIMPLE predicted-ROI 324-config search'),
    ('reports/tables/kub_view_type_inventory.csv', 'persisted_table', 2,
     'Per-sample FOV inventory (directory-semantics rule); clean-v3 FULL_FIELD 877'),
    ('reports/tables/kub_val_components_sized.csv', 'persisted_table', 2,
     'Historical v2 VAL component table under kub_size_v1 (FULL_FIELD 106/156)'),
    ('reports/tables/phase12_clean_v3_oracle_geometry.csv', 'persisted_table', 2,
     'Clean-v3 oracle geometry: 103 cases / 152 native components under kub_size_clean_v3_v1'),
    (f'experiments/{STAGE4D_EXPERIMENT}/history.csv', 'persisted_table', 2,
     'Stage-4D-R2 complete epoch history (88 epochs)'),
    (f'experiments/{STAGE4D_EXPERIMENT}/val_search_epoch001.csv', 'persisted_table', 2,
     'Stage-4D-R2 per-epoch proposal-grid search (88 files; epoch 079 absent)'),
    ('notebooks/11c_kub_final_localizer_redesign.ipynb', 'executed_notebook', 3,
     'Historical Stage-4D reviewer notebook (46 cells, SHA 6c8e0049...)'),
    ('notebooks/11_kub_predicted_roi_localizer.ipynb', 'executed_notebook', 3,
     'Historical Phase-13 SIMPLE predicted-ROI notebook'),
    ('notebooks/phasewise/phase_13_predicted_roi_localization/README.md',
     'frozen_readme', 4, 'Phase-13 prose summary (COMPLETE)'),
    ('notebooks/phasewise/phase_13_predicted_roi_localization/'
     'phase13_stage4d_localizer_final_visual_analysis.ipynb', 'executed_notebook', 3,
     'Phase-13 canonical-dir Stage-4D final visual analysis notebook'),
    ('reports/audits/phase14_diagnostic_protocol_amendment.md', 'downstream_evidence', 2,
     'Phase-14 A3 training policy: GT-derived base + perturbed + background-negative crops '
     '-> historical train/inference proposal-distribution mismatch evidence'),
    ('reports/audits/phase14_part1_implementation_preflight.md', 'downstream_evidence', 2,
     'Phase-14 dataset composition 5028 crops (1162 base + 2324 perturbed + 1542 negative)'),
    ('reports/audits/phase14_part3_diagnostic_evaluation.md', 'downstream_evidence', 2,
     'Phase-14 gate arithmetic: G=+0.219178, R=0.500000, Step-3 FAIL (D_p 0.383905)'),
    ('tests/test_kub_localizer.py', 'test_source', 2,
     'Localizer tests (1 pre-existing failure, deferred)'),
    ('tests/test_predicted_roi.py', 'test_source', 2,
     'Predicted-ROI tests (3 pre-existing failures, deferred)'),
]


def build_source_inventory() -> pd.DataFrame:
    rows = []
    for rel, kind, rank, notes in HISTORICAL_SOURCES:
        p = PROJECT_ROOT / rel
        rows.append({'source_path': rel, 'source_type': kind,
                     'sha256': sha256_file(p) if p.exists() else 'N/A',
                     'historical_phase': 13, 'relevance': notes,
                     'authority_rank': rank,
                     'notes': 'present' if p.exists() else 'MISSING'})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# §2 Historical stage inventory
# ---------------------------------------------------------------------------
HISTORICAL_STAGES = [
    ('13', 'Phase-13 SIMPLE predicted-ROI localizer (no learning)',
     'phase13_predicted_roi', 'COMPLETE_PASS_GATE_WEAK',
     'Threshold + NMS proposals from a frozen global baseline probability map (UNet++).',
     'overall recall90 0.743590; Tiny recall90 0.684932; 0/16 hard Tiny; 0/7 global-empty; '
     'mean proposals/image 1.556604; Phase-14 gate WEAK.',
     'reports/audits/phase13_predicted_roi_localizer.json'),
    ('13B-4A', 'Learned localizer pilot v1 (unconstrained recall objective)',
     'phase13b_kub_localizer_r512_s3_seed42', 'INVALID_FOR_FINAL_SELECTION',
     'Train a dedicated learned center-heatmap localizer; select proposals by recall.',
     'Degenerate full-image ROIs achieved perfect recall at ROI area fraction 1.0; run '
     'preserved but invalid for final selection.',
     'reports/audits/phase13b_stage3_validation_correction.md'),
    ('13B-4B', 'Feasibility-constrained localization',
     'phase13b_kub_localizer_r512_s3_seed42_v3', 'FAIL_CHECK_REQUIRED',
     'Ban full-image ROIs: feasible iff mean ROI area <= 0.10 and proposals/image <= 5.',
     'Feasible configs bounded correctly but recall collapsed (Tiny 1.37%, overall 3.85%, '
     '0/16, 1/7) under the 0.75 focal + 0.25 dice loss; loss redesign required.',
     'reports/audits/phase13b_stage4b_feasible_selection.md'),
    ('13B-4C', 'CenterNet-style focal loss redesign pilot',
     'phase13b_kub_localizer_r512_s3_centernetfocal_seed42_v1', 'FAIL_CHECK_REQUIRED',
     'Replace focal+dice with a CenterNet modified focal loss on exact-1.0 centre targets.',
     'Target validation FAILED: sub-pixel centres gave peak density < 1.0 so target.eq(1.0) '
     'found 0 positives (loss 343782.6). Training not started.',
     'reports/audits/phase13b_stage4c_loss_redesign.md'),
    ('13B-4C-R3', 'Component mapping correction',
     'phase13b_kub_localizer_r512_s3_centernetfocal_seed42_v2', 'PASS',
     'Force the nearest integer pixel of each mapped centre to exactly 1.0 and re-audit '
     'the 1162 TRAIN / 156 VAL centre mapping.',
     '1162/1162 mapped, 0 legitimately-outside, 1162 unique canonical centres, 0 collisions, '
     '0 zero-centre samples.',
     'reports/audits/phase13b_stage4c_r3_component_mapping.md'),
    ('13B-4C-R4', 'CenterNet focal pilot re-run',
     'phase13b_kub_localizer_r512_s3_centernetfocal_seed42_v3', 'PILOT_BELOW_GATE',
     'Re-run the CenterNet pilot after the centre-mapping correction.',
     'Epoch 97: Tiny recall90 0.465753, overall recall90 0.301282, hard Tiny 1/16, '
     'global-empty 1/7, ROI area 0.000922, proposals 3.0566, mean max heatmap 0.100246.',
     'reports/audits/phase13b_stage4c_r4_centernet_pilot.md'),
    ('13B-4D-R1', 'Final bounded localizer preflight (stride-4 / 128 output)',
     'phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_v1',
     'PREFLIGHT_PASS',
     'Parameter-free AvgPool2d(4,4) logit downsample 512->128; sigma 0.75 (== 3.0 in '
     '512-space); all else frozen.',
     'Params unchanged 482,449; constant logit init commutes exactly (p=0.100000); negative '
     'focal burden reduced ~16x (138 -> 8.6); round-trip centre error <= 2.12 px.',
     'reports/audits/phase13b_stage4d_r1_preflight.md'),
    ('13B-4D-R2', 'Final Stage-4D localizer (authoritative)',
     STAGE4D_EXPERIMENT, 'COMPLETE_FROZEN',
     'Train the frozen 128-output CenterNet-focal localizer; select via the lexicographic '
     'rule; evaluate the Phase-14 gate.',
     'best_epoch 73 / 88 total; Tiny recall90 53/73 = 0.726027; overall 100/156 = 0.641026; '
     'hard Tiny 7/16; global-empty 3/7; mean ROI area 0.005899; proposals 4.660377.',
     'reports/audits/phase13b_stage4d_final_evaluation.json'),
]


def build_stage_inventory() -> pd.DataFrame:
    return pd.DataFrame(HISTORICAL_STAGES, columns=[
        'stage_id', 'stage_name', 'experiment_id', 'status', 'objective',
        'outcome_summary', 'key_artifact'])


# ---------------------------------------------------------------------------
# §3 Historical localizer protocol matrix
# ---------------------------------------------------------------------------
# (concept, historical_value, unit, scope, source, status, notes)
PROTOCOL_MATRIX = [
    ('A_model_scope', 'KUBLocalizer — compact 3-stage U-Net (base_channels 16)', 'model',
     'historical Phase 13B', 'src/models/kub_localizer.py', 'VERIFIED',
     'single architecture; not one of the four Phase-10 segmentation baselines'),
    ('B_parameter_count', '482,449', 'params', 'historical Stage-4D',
     'reports/audits/phase13b_stage4d_r1_preflight.md', 'VERIFIED',
     'identical between 512 and 128 output configurations (logit downsample is parameter-free)'),
    ('C_input', 'grayscale FULL_FIELD image, 1 channel', 'tensor', 'historical',
     'src/data/kub_localizer_dataset.py', 'VERIFIED',
     'ROI acquisition cases are excluded from the localizer dataset'),
    ('D_output', 'one-channel objectness logit heatmap', 'tensor', 'historical',
     'src/models/kub_localizer.py', 'VERIFIED',
     'final Stage-4D output resolution 128x128 via AvgPool2d(4,4) from the stride-4 block'),
    ('E_initialization', 'random Kaiming; no pretrained weights; head bias log(0.1/0.9)',
     'rule', 'historical', 'src/models/kub_localizer.py', 'VERIFIED',
     'initial heatmap probability is exactly 0.10 everywhere'),
    ('F_supervision', 'TRAIN-only soft centre heatmaps derived from GT component centroids',
     'rule', 'historical', 'src/inference/heatmap_targets.py', 'VERIFIED',
     'VAL targets are also GT-derived but never used for optimization'),
    ('G_heatmap_target_rule', 'Gaussian, pixelwise MAX across components; nearest integer '
     'pixel forced to 1.0', 'rule', 'historical', 'src/inference/heatmap_targets.py',
     'VERIFIED', 'the forced-1.0 rule was introduced at Stage-4C-R3 after the R1 failure'),
    ('H_sigma_grid', '3, 5, 7 (512-space); selected equivalent 0.75 in 128-space',
     'px', 'historical', 'PHASE13B.md', 'VERIFIED',
     '0.75 in 128-space is geometrically equivalent to 3.0 in 512-space'),
    ('I_resolution_grid', '512, 768 (6 candidates, not expanded)', 'px', 'historical',
     'configs/kub/phase13b_localizer.yaml', 'VERIFIED',
     'final Stage-4D used 512 input with a 128 heatmap'),
    ('J_loss', 'soft_focal_dice: 0.75 CenterNet focal + 0.25 soft Dice', 'loss',
     'historical', 'configs/kub/phase13b_localizer.yaml', 'VERIFIED',
     'focal alpha 0.25, gamma 2.0; unweighted pixel-wise mean (Stage-3 correction)'),
    ('K_optimizer', 'AdamW lr 1e-4, weight_decay 1e-4', 'optimizer', 'historical',
     'configs/kub/phase13b_localizer.yaml', 'VERIFIED', 'matches the Phase-10 segmentation baselines'),
    ('L_scheduler', 'CosineAnnealingLR, T_max 100', 'scheduler', 'historical',
     'configs/kub/phase13b_localizer.yaml', 'VERIFIED', 'no warmup'),
    ('M_amp', 'true (CUDA)', 'bool', 'historical',
     'configs/kub/phase13b_localizer.yaml', 'VERIFIED',
     'CUDA required; CHECK_REQUIRED and stop if unavailable'),
    ('N_batch', 'effective 4 (physical 4; fallback 2+accum2, then 1+accum4)', 'int',
     'historical', 'PHASE13B.md', 'VERIFIED', 'physical batch fallback ladder predeclared'),
    ('O_seed', '42', 'int', 'historical', 'configs/kub/phase13b_localizer.yaml', 'VERIFIED',
     'single seed'),
    ('P_epochs_patience', 'max_epochs 100, early-stopping patience 15', 'int', 'historical',
     'configs/kub/phase13b_localizer.yaml', 'VERIFIED',
     'Stage-4D-R2 stopped at 88 total epochs with best epoch 73'),
    ('Q_model_selection', 'LEXICOGRAPHIC, NOT segmentation Dice: (1) recovered frozen 16 Tiny '
     'misses@90 (2) recovered frozen 7 global-empty@90 (3) overall Tiny recall90 (4) overall '
     'component recall90 (5) multi-component recall90 (6) min ROI area fraction '
     '(7) min proposals/image (8) prefer 512', 'rule', 'historical', 'PHASE13B.md',
     'VERIFIED', 'Phase 13 is localization-only; segmentation Dice is never a selection target'),
    ('R_proposal_threshold_grid', '0.10, 0.20, 0.30, 0.40, 0.50', 'float', 'historical',
     'configs/kub/phase13b_localizer.yaml', 'VERIFIED',
     'only threshold 0.10 produced non-degenerate proposals for Stage-4D'),
    ('S_margin_grid', '0.10, 0.20', 'float', 'historical',
     'configs/kub/phase13b_localizer.yaml', 'VERIFIED',
     'selected margin 0.20; the Phase-14 amendment also uses margin 0.20'),
    ('T_top_k_grid', '3, 5', 'int', 'historical',
     'configs/kub/phase13b_localizer.yaml', 'VERIFIED', 'selected top_k 5'),
    ('U_nms_iou', '0.30 (fixed, not searched)', 'float', 'historical',
     'configs/kub/phase13b_localizer.yaml', 'VERIFIED', '20-config grid = 5 thresholds x 2 margins x 2 top_k'),
    ('V_proposal_extraction', 'binary = heatmap >= threshold; 8-connectivity label; box mapped '
     'from heatmap space to original space via transform scale/padding and factor = 512 // '
     'heatmap_resolution', 'rule', 'historical', 'src/inference/predicted_roi.py', 'VERIFIED',
     'components sorted by (-max_probability, bbox); capped at the top 100 before NMS'),
    ('W_margin_rule', 'expand by round(margin * box_dim) per axis, then force a SQUARE of side '
     '= max(expanded_h, expanded_w) centred on the expanded box; y2 = y1 + side; clip/pad',
     'rule', 'historical', 'src/inference/predicted_roi.py', 'VERIFIED',
     'apply_context_margin; crop_geometry is already expanded and must not be re-expanded'),
    ('X_coverage_primary', '>= 0.90 of a GT component\u2019s original-space pixels inside one '
     'proposal ROI', 'rule', 'historical', 'PHASE13B.md', 'VERIFIED',
     'primary hit definition; secondary thresholds 0.50 and any-overlap also reported'),
    ('Y_frozen_hard_sets', '16 globally missed Tiny components + 7 global-empty FULL_FIELD '
     'images (HISTORICAL v2)', 'set', 'historical', 'PHASE13B.md', 'VERIFIED',
     'derived from the Phase-13 SIMPLE run on the v2 population 106/156'),
    ('Z_population', 'TRAIN FULL_FIELD 771 images / 1162 components; VAL FULL_FIELD 106 images '
     '/ 156 components; VAL strata Tiny 73 / Small 29 / Medium 36 / Large 18', 'population',
     'historical', 'reports/audits/phase13b_stage4d_final_evaluation.json', 'VERIFIED',
     'this is the phase4_v2 population — NOT the clean-v3 population'),
    ('AA_manifest', 'phase4_v2', 'manifest', 'historical',
     'reports/audits/phase13_predicted_roi_localizer.json', 'VERIFIED',
     'clean-v3 must use phase4_v3'),
    ('AB_taxonomy', 'kub_size_v1 (HISTORICAL)', 'taxonomy', 'historical',
     'reports/tables/kub_val_components_sized.csv', 'VERIFIED',
     'clean-v3 must use kub_size_clean_v3_v1'),
    ('AC_gt_free', 'the proposal API accepts NO GT argument; GT may only be used after '
     'proposals are generated, for evaluation', 'rule', 'historical',
     'src/inference/predicted_roi.py', 'VERIFIED',
     'enforced by the generate_predicted_rois signature and asserted in the audit'),
    ('AD_phase14_gate', 'YES only if ALL of: (A) >= 8/16 hard Tiny recovered@90 (B) >= 4/7 '
     'global-empty recovered@90 (C) overall Tiny recall90 >= 0.85 (D) overall component '
     'recall90 >= 0.85 (E) mean ROI area fraction <= 0.10 (F) mean proposals/image <= 5',
     'rule', 'historical', 'PHASE13B.md', 'VERIFIED',
     'a strong gate deliberately set ABOVE the Stage-4D pilot gate (A>=0.50/B>=0.50/C>=2/16)'),
    ('AE_phase14_gate_outcome', 'NOT PASSED — A 7/16 (<8), B 3/7 (<4), C 0.726027 (<0.85), '
     'D 0.641026 (<0.85), E 0.005899 (pass), F 4.660377 (pass)', 'outcome', 'historical',
     'reports/audits/phase13b_stage4d_final_evaluation.json', 'VERIFIED',
     'the frozen confirmatory Phase-14 entry gate was NOT met'),
    ('AF_downstream_refiner_training_policy', 'Phase-14 Option A3: 1162 GT-derived base crops '
     '+ 2324 perturbed crops (translation U(-0.10,0.10) x crop_side, scale U(0.90,1.10)) + '
     '1542 background-negative crops = 5028 crops/epoch', 'rule', 'downstream historical',
     'reports/audits/phase14_diagnostic_protocol_amendment.md', 'VERIFIED',
     'crops derive from GT components, NOT from Stage-4D predicted proposals'),
    ('AG_downstream_inference_driver', 'Condition C evaluates the SAME refiner driven by frozen '
     'Stage-4D predicted proposals (margin 0.20)', 'rule', 'downstream historical',
     'reports/audits/phase14_diagnostic_protocol_amendment.md', 'VERIFIED',
     'this is the source of the train/inference proposal-distribution mismatch'),
    ('AH_downstream_gate_outcome', 'Step 1 PASS (G=+0.219178), Step 2 PASS (R=0.500000), '
     'Step 3 FAIL (D_p 0.383905 < 0.632776) -> DIAGNOSTIC_PRACTICAL_SIGNAL_INSUFFICIENT',
     'outcome', 'downstream historical', 'reports/audits/phase14_part3_diagnostic_evaluation.md',
     'VERIFIED', 'predicted-proposal clutter produced 5.43 FP components/image vs 0.37 baseline'),
    ('AI_latent_inference_defect', 'learned_roi.predict_localizer constructs KUBLocalizer '
     'WITHOUT heatmap_resolution=128', 'defect', 'historical',
     'src/inference/learned_roi.py', 'VERIFIED_DEFECT',
     'the Stage-4D checkpoint is 128-output; the inference path would build a 512-output '
     'model (parameter-free mismatch, so loading succeeds silently) and produce a 512-space '
     'heatmap. Not exercised by the Phase-13B notebooks (which used the dataset/evaluator path).'),
    ('AJ_epoch_artifact_gap', f'experiments/{STAGE4D_EXPERIMENT}/ contains 88 val_search files '
     'but val_search_epoch079.csv is absent', 'artifact', 'historical',
     f'experiments/{STAGE4D_EXPERIMENT}/', 'VERIFIED',
     'history.csv has 88 contiguous epochs; only the per-epoch search dump for 079 is missing'),
    ('AK_design_audit_label_ambiguity', 'phase13b_stage4d_design_audit.json labels the Stage-4C '
     'numbers as "clean_v3_results"', 'ambiguity', 'historical',
     'reports/audits/phase13b_stage4d_design_audit.json', 'AMBIGUOUS',
     'the localizer VAL denominator was 156 (v2). The label most plausibly refers to the '
     'clean-v3 ARCHITECTURE (KUBLocalizer), not the clean-v3 MANIFEST. Requires supervisor '
     'confirmation before any reuse of the Stage-4C numbers.'),
]


def build_protocol_matrix() -> pd.DataFrame:
    rows = []
    for concept, value, unit, scope, src, status, notes in PROTOCOL_MATRIX:
        rows.append({'concept': concept, 'historical_value': value, 'unit': unit,
                     'scope': scope, 'source': src, 'source_sha': _sha(src),
                     'status': status, 'notes': notes})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# §4 Historical checkpoint provenance
# ---------------------------------------------------------------------------
CHECKPOINT_PROVENANCE = [
    (STAGE4D_EXPERIMENT,
     f'checkpoints/{STAGE4D_EXPERIMENT}/best.pt', STAGE4D_BEST_SHA, 'BEST_SELECTED',
     73, 88, 'AUTHORITATIVE',
     'lexicographic selection; Stage-4D-R2 final localizer'),
    (STAGE4D_EXPERIMENT,
     f'checkpoints/{STAGE4D_EXPERIMENT}/latest.pt', STAGE4D_LATEST_SHA, 'LATEST',
     None, 88, 'RESUME_ONLY', 'complete resume state; not used for evaluation'),
    ('phase13b_kub_localizer_r512_s3_centernetfocal_seed42_v3',
     'checkpoints/phase13b_kub_localizer_r512_s3_centernetfocal_seed42_v3/best.pt', None,
     'BEST', 97, None, 'SUPERSEDED',
     'Stage-4C-R4 CenterNet pilot at 512 output; below gate'),
    ('phase13b_kub_localizer_r512_s3_centernetfocal_seed42_v1',
     'checkpoints/phase13b_kub_localizer_r512_s3_centernetfocal_seed42_v1/best.pt', None,
     'BEST', None, None, 'INVALID_FOR_FINAL_SELECTION',
     'Stage-4C loss-redesign attempt; target validation failed, training not started'),
    ('phase13b_kub_localizer_r512_s3_seed42_v3',
     'checkpoints/phase13b_kub_localizer_r512_s3_seed42_v3/best.pt', None, 'BEST', 11, 26,
     'FAIL_CHECK_REQUIRED',
     'Stage-4B feasibility-constrained pilot; Tiny recall90 1.37%'),
    ('phase13b_kub_localizer_r512_s3_seed42',
     'checkpoints/phase13b_kub_localizer_r512_s3_seed42/best.pt', None, 'BEST', None, 19,
     'INVALID_FOR_FINAL_SELECTION',
     'Stage-4A provisional run; unapproved class-balancing + unapproved metrics'),
]


def build_checkpoint_provenance() -> pd.DataFrame:
    rows = []
    for exp, rel, sha_claim, role, best_epoch, total, status, notes in CHECKPOINT_PROVENANCE:
        p = PROJECT_ROOT / rel
        actual = sha256_file(p) if p.exists() else 'N/A'
        if sha_claim is not None:
            sha_match = (actual == sha_claim)
        else:
            sha_match = None
        rows.append({'experiment_id': exp, 'checkpoint_path': rel,
                     'sha256': actual, 'sha256_matches_claim': sha_match, 'role': role,
                     'best_epoch': best_epoch if best_epoch is not None else 'N/A',
                     'total_epochs': total if total is not None else 'N/A',
                     'status': status, 'notes': notes})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# §5 Historical handoff-claim verification
# ---------------------------------------------------------------------------
def build_handoff_verification() -> pd.DataFrame:
    audit = json.loads(
        (AUDITS / 'phase13b_stage4d_final_evaluation.json').read_text(encoding='utf-8'))
    sel = audit['selected_configuration']
    gate = audit['gate_evaluation']
    checks = {
        'Stage-4D best.pt SHA-256': (STAGE4D_BEST_SHA, audit['checkpoint_sha256']),
        'Stage-4D best_epoch': (73, audit['best_epoch']),
        'Stage-4D total_epochs': (88, audit['total_epochs']),
        'selected threshold': (0.1, sel['threshold']),
        'selected margin': (0.2, sel['margin']),
        'selected top_k': (5, sel['top_k']),
        'selected nms_iou': (0.3, sel['nms_iou']),
        'Tiny recall90 numerator/denominator': (
            '53/73', f"{gate['tiny_numerator']}/{gate['tiny_denominator']}"),
        'Overall recall90 numerator/denominator': (
            '100/156', f"{gate['overall_numerator']}/{gate['overall_denominator']}"),
    }
    rows = []
    for name, (claimed, actual) in checks.items():
        rows.append({'claim': name, 'claimed': str(claimed), 'actual': str(actual),
                     'verdict': 'VERIFIED' if str(claimed) == str(actual) else 'MISMATCH'})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# §6 clean-v3 population specification
# ---------------------------------------------------------------------------
def build_population_spec() -> pd.DataFrame:
    rows = []
    src_manifest = f'manifests/{MANIFEST_CLEAN}/'
    src_view = 'reports/tables/kub_view_type_inventory.csv'
    for split in ('TRAIN', 'VAL'):
        c = POPULATION_CENSUS[split]
        rows.append({'scope': f'{split} / KUB / FULL_FIELD', 'item': 'images',
                     'value': c['images'], 'unit': 'images', 'source': src_manifest,
                     'notes': 'directory-semantics FOV rule (\\Images\\ -> FULL_FIELD)'})
        rows.append({'scope': f'{split} / KUB / FULL_FIELD', 'item': 'components',
                     'value': c['components'], 'unit': 'connected components',
                     'source': f'{src_view} + mask census',
                     'notes': 'foreground mask > 0, 8-connectivity'})
        rows.append({'scope': f'{split} / KUB / FULL_FIELD',
                     'item': 'max_components_per_image',
                     'value': c['max_components_per_image'], 'unit': 'components',
                     'source': f'{src_view} + mask census', 'notes': 'budget driver for Top-K'})
        rows.append({'scope': f'{split} / KUB / FULL_FIELD',
                     'item': 'images_with_gt_5_components',
                     'value': c['images_gt_5_components'], 'unit': 'images',
                     'source': f'{src_view} + mask census',
                     'notes': 'motivates a bounded Top-K oracle budget'})
        rows.append({'scope': f'{split} / KUB / FULL_FIELD',
                     'item': 'images_with_zero_components',
                     'value': c['images_zero_components'], 'unit': 'images',
                     'source': f'{src_view} + mask census',
                     'notes': 'FULL_FIELD only'})
    for stratum in ('TINY', 'SMALL', 'MEDIUM', 'LARGE'):
        rows.append({'scope': 'VAL / KUB / FULL_FIELD / size stratum', 'item': stratum,
                     'value': VAL_STRATA_CLEAN[stratum], 'unit': 'components',
                     'source': 'reports/tables/phase12_clean_v3_oracle_geometry.csv',
                     'notes': f'{TAXONOMY_CLEAN}; historical v2 value was '
                              f'{VAL_STRATA_HIST[stratum]}'})
    rows.append({'scope': 'VAL / KUB / FULL_FIELD / size stratum', 'item': 'TOTAL',
                 'value': sum(VAL_STRATA_CLEAN.values()), 'unit': 'components',
                 'source': 'reports/tables/phase12_clean_v3_oracle_geometry.csv',
                 'notes': 'equals the component census'})
    rows.append({'scope': 'TRAIN+VAL / KUB / ROI', 'item': 'components_included',
                 'value': 0, 'unit': 'components', 'source': 'taxonomy scope rule',
                 'notes': 'ROI acquisitions are excluded from the localizer '
                          '(ROI_NOT_PRIMARY_BINNED)'})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# §7 clean-v3 candidate localizer protocol
# ---------------------------------------------------------------------------
# (field, historical_v2, proposed_clean_v3, reason, material, supervisor_required)
CANDIDATE = [
    ('manifest_version', 'phase4_v2', 'phase4_v3',
     'clean governance: canonical active-development manifest', False, False),
    ('taxonomy', 'kub_size_v1', 'kub_size_clean_v3_v1',
     'clean governance: frozen clean-v3 taxonomy', False, False),
    ('train_population', 'FULL_FIELD 771 images / 1162 components',
     'FULL_FIELD 770 images / 1161 components', 'clean-v3 population', False, False),
    ('val_population', 'FULL_FIELD 106 images / 156 components',
     'FULL_FIELD 103 images / 152 components', 'clean-v3 population', False, False),
    ('val_size_strata', 'Tiny 73 / Small 29 / Medium 36 / Large 18',
     'Tiny 72 / Small 28 / Medium 36 / Large 16',
     'clean-v3 taxonomy recomputation; NOT a relabelling of the v2 strata', True, False),
    ('model_architecture', 'KUBLocalizer compact 3-stage U-Net, base_channels 16',
     'KUBLocalizer compact 3-stage U-Net, base_channels 16',
     'historical architecture is scientifically valid; unchanged', False, False),
    ('input_channels', '1', '1', 'unchanged', False, False),
    ('input_resolution', '512', '512', 'unchanged', False, False),
    ('output_heatmap_resolution', '128 (AvgPool2d(4,4) from the stride-4 block)',
     '128 (AvgPool2d(4,4) from the stride-4 block)',
     'the Stage-4D bounded redesign is retained; it is the only configuration that passed '
     'the pilot gate', False, False),
    ('target_sigma', '0.75 in 128-space (== 3.0 in 512-space)',
     '0.75 in 128-space (== 3.0 in 512-space)', 'unchanged', False, False),
    ('heatmap_target_rule', 'Gaussian, pixelwise MAX, nearest integer pixel forced to 1.0',
     'Gaussian, pixelwise MAX, nearest integer pixel forced to 1.0',
     'required for the CenterNet exact-1.0 positive rule', False, False),
    ('initialization', 'random Kaiming; head bias log(0.1/0.9)',
     'random Kaiming; head bias log(0.1/0.9)', 'unchanged', False, False),
    ('loss', '0.75 CenterNet focal (alpha 0.25, gamma 2.0) + 0.25 soft Dice',
     '0.75 CenterNet focal (alpha 0.25, gamma 2.0) + 0.25 soft Dice', 'unchanged',
     False, False),
    ('optimizer', 'AdamW lr 1e-4, wd 1e-4', 'AdamW lr 1e-4, wd 1e-4', 'unchanged',
     False, False),
    ('scheduler', 'CosineAnnealingLR T_max 100', 'CosineAnnealingLR T_max 100', 'unchanged',
     False, False),
    ('amp', 'true (CUDA required)', 'true (CUDA required)', 'unchanged', False, False),
    ('effective_batch', '4 (fallback 2+accum2, then 1+accum4)',
     '4 (fallback 2+accum2, then 1+accum4)', 'unchanged', False, False),
    ('seed', '42', '42', 'unchanged', False, False),
    ('max_epochs', '100', '100', 'unchanged', False, False),
    ('early_stopping_patience', '15', '15', 'unchanged', False, False),
    ('checkpoint_metric', 'lexicographic localizer rule (never segmentation Dice)',
     'lexicographic localizer rule (never segmentation Dice)',
     'Phase 13 is localization-only; unchanged', False, False),
    ('proposal_search_grid', '5 thresholds x 2 margins x 2 top_k = 20 configs, nms_iou 0.30',
     '5 thresholds x 2 margins x 2 top_k = 20 configs, nms_iou 0.30',
     'unchanged; VAL-only selection', False, False),
    ('coverage_primary', '0.90', '0.90', 'unchanged', False, False),
    ('frozen_hard_sets', '16 globally missed Tiny + 7 global-empty FULL_FIELD (v2-derived)',
     'RE-DERIVE under clean-v3 from the frozen global baselines using the SAME definitional '
     'rule; do NOT reuse the v2 16/7 sets',
     'the v2 sets were computed on a different population (106/156); reusing them would '
     'silently import v2 membership', True, True),
    ('gt_free_guarantee', 'proposal API accepts no GT',
     'proposal API accepts no GT; GT only for post-generation evaluation', 'unchanged',
     False, False),
    ('architecture_scope', 'single localizer architecture (KUBLocalizer)',
     'single localizer architecture (KUBLocalizer)',
     'Phase 13 localizes; it does not compare segmentation architectures', False, False),
    ('inference_path_defect', 'learned_roi.predict_localizer omits heatmap_resolution=128',
     'MUST pass heatmap_resolution=128 (or an explicit output-resolution contract) so the '
     'inference heatmap geometry matches the trained checkpoint',
     'verified latent defect; the inference path would silently produce a 512-space heatmap',
     True, True),
]


def build_candidate_protocol() -> pd.DataFrame:
    return pd.DataFrame(CANDIDATE, columns=[
        'field', 'historical_v2', 'proposed_clean_v3', 'change_reason',
        'scientifically_material', 'supervisor_decision_required'])


def build_protocol_diff() -> pd.DataFrame:
    d = build_candidate_protocol().copy()
    d['same_or_changed'] = ['SAME' if h == p else 'CHANGED'
                            for h, p in zip(d['historical_v2'], d['proposed_clean_v3'])]
    return d[['field', 'historical_v2', 'proposed_clean_v3', 'same_or_changed',
              'change_reason', 'scientifically_material', 'supervisor_decision_required']]


# ---------------------------------------------------------------------------
# §8 clean-v3 proposal postprocessing candidate
# ---------------------------------------------------------------------------
POSTPROCESSING = [
    ('1. threshold', 'binary = heatmap >= threshold; grid {0.10,0.20,0.30,0.40,0.50}',
     'identical rule and identical grid', 'unchanged', False, False),
    ('2. connected components', '8-connectivity label() on the binarised heatmap',
     'identical rule', 'unchanged', False, False),
    ('3. component scoring', 'score = component max probability',
     'identical rule', 'unchanged', False, False),
    ('4. component ordering', 'sort by (-max_probability, bbox)', 'identical rule',
     'unchanged', False, False),
    ('5. component cap', 'cap at the top 100 components before NMS',
     'identical rule', 'unchanged', False, False),
    ('6. NMS', 'score-descending inclusive-coordinate box IoU NMS, iou 0.30',
     'identical rule', 'unchanged', False, False),
    ('7. Top-K', 'keep the top K proposals; grid {3,5}', 'identical rule', 'unchanged',
     False, False),
    ('8. heatmap->512 mapping', 'factor = 512 // heatmap_resolution; box = '
     '(start*factor, (stop-1)*factor + factor-1)', 'identical rule', 'unchanged', False, False),
    ('9. 512->native mapping', 'invert padding then divide by the aspect-preserving scale; '
     'y1/x1 floor, y2/x2 ceil-1; clip to the native frame',
     'identical rule', 'unchanged', False, False),
    ('10. context margin', 'expand by round(margin * box_dim) per axis; force a SQUARE of '
     'side = max(expanded_h, expanded_w) centred on the expanded box; y2 = y1 + side',
     'identical rule', 'unchanged', False, False),
    ('11. boundary handling', 'clip to the image and record pad amounts; the returned '
     'crop_geometry is already expanded',
     'identical rule; consumers must NOT re-expand crop_geometry',
     'the Phase-14 amendment had to state this explicitly', False, False),
    ('12. ROI area accounting', 'union area fraction = |union of clipped ROIs| / (H*W); also '
     'report the max individual ROI area fraction',
     'identical rule', 'unchanged', False, False),
    ('13. coverage evaluation', 'per GT component, coverage = component pixels inside the best '
     'proposal clip rectangle / total component pixels; covered90 >= 0.90, covered50 >= 0.50, '
     'any_overlap > 0', 'identical rule; component identity from the clean-v3 taxonomy',
     'unchanged', False, False),
    ('14. zero-proposal handling', 'if no proposal is generated the image contributes zero '
     'coverage; no synthetic fallback',
     'identical rule', 'unchanged', False, False),
]


def build_postprocessing_candidate() -> pd.DataFrame:
    return pd.DataFrame(POSTPROCESSING, columns=[
        'step', 'historical_v2', 'proposed_clean_v3', 'change_reason',
        'scientifically_material', 'supervisor_decision_required'])


# ---------------------------------------------------------------------------
# §9 clean-v3 proposal metric contract
# ---------------------------------------------------------------------------
PROPOSAL_METRIC_CONTRACT = [
    ('component_coverage', 'component pixels inside the best proposal ROI / total component '
     'pixels', 'fraction', 'primary', 'historical'),
    ('covered90', 'best coverage >= 0.90', 'bool', 'PRIMARY localization hit', 'historical'),
    ('covered50', 'best coverage >= 0.50', 'bool', 'secondary', 'historical'),
    ('any_overlap', 'best coverage > 0', 'bool', 'secondary', 'historical'),
    ('overall_recall90', 'covered90 components / all GT components', 'fraction',
     'primary aggregate', 'historical'),
    ('size_stratum_recall90', 'covered90 components within TINY/SMALL/MEDIUM/LARGE / stratum '
     'total', 'fraction', 'primary stratified', 'historical'),
    ('hard_tiny_recovered90', 'frozen globally-missed TINY components recovered@90',
     'count', 'gate criterion A', 'historical (set must be re-derived clean-v3)'),
    ('global_empty_covered90', 'frozen global-empty images with >= 1 component covered@90',
     'count', 'gate criterion B', 'historical (set must be re-derived clean-v3)'),
    ('multicomponent_recall90', 'covered90 components within multi-component images / '
     'multi-component total', 'fraction', 'secondary', 'historical'),
    ('mean_proposals_per_image', 'mean proposal count per image', 'count',
     'efficiency / gate criterion F', 'historical'),
    ('mean_roi_area_fraction', 'mean union ROI area fraction', 'fraction',
     'efficiency / gate criterion E', 'historical'),
    ('p90_p95_max_roi_area_fraction', 'upper-tail union ROI area fractions', 'fraction',
     'descriptive', 'historical'),
    ('zero_proposal_images', 'images with no proposal', 'count', 'descriptive', 'historical'),
    ('mean_max_heatmap_prob', 'mean of the per-image maximum heatmap probability',
     'probability', 'diagnostic (detects prior-collapse)', 'historical'),
    ('proposal_precision', 'proposals overlapping >= 1 GT component / all proposals',
     'fraction', 'PROPOSED ADDITION for clean-v3 (proposal precision)',
     'NEW — not reported historically'),
    ('unmatched_proposals_per_image', 'proposals overlapping no GT component per image',
     'count', 'PROPOSED ADDITION for clean-v3', 'NEW — not reported historically'),
    ('localizer_dice', 'NOT DEFINED — Phase 13 is localization-only; segmentation Dice is '
     'never a localizer selection or reporting target', 'n/a', 'EXCLUDED BY DESIGN',
     'historical (deliberately absent)'),
]


def build_proposal_metric_contract() -> pd.DataFrame:
    return pd.DataFrame(PROPOSAL_METRIC_CONTRACT,
                        columns=['metric', 'definition', 'unit', 'role', 'historical_status'])


# ---------------------------------------------------------------------------
# §10 clean-v3 downstream integration candidate
# ---------------------------------------------------------------------------
DOWNSTREAM = [
    ('role of Phase 13', 'Produce GT-free proposals consumed by the Phase-14 regional refiner '
     '(Condition C)',
     'Produce GT-free proposals consumed by a regional refiner, evaluated as a three-way '
     'contrast GLOBAL vs ORACLE REGION vs PREDICTED REGION',
     'unchanged', False, False),
    ('refiner input geometry', 'consume crop_geometry directly without further expansion',
     'identical rule', 'unchanged', False, False),
    ('fusion rule', 'DIRECT_REPLACEMENT_IN_PROPOSAL_UNION; regional pixelwise MAX inside the '
     'proposal union, global elsewhere',
     'identical rule', 'unchanged', False, False),
    ('final threshold', '0.50', '0.50', 'unchanged', False, False),
    ('zero-proposal fallback', 'P_final = P_global everywhere (no synthetic fallback)',
     'identical rule', 'unchanged', False, False),
    ('refiner training crops', 'Option A3: 1162 GT-derived base crops + 2324 perturbed crops + '
     '1542 background negatives',
     'PROPOSE: draw training crops from Stage-4D predicted proposals (with an explicit '
     'negative-sampling policy) so the training crop distribution matches the inference '
     'proposal distribution',
     'HISTORICAL_TRAIN_INFERENCE_PROPOSAL_DISTRIBUTION_MISMATCH: the historical refiner was '
     'trained on GT-derived/perturbed crops but evaluated on predicted proposals', True, True),
    ('refiner training population', 'v2 FULL_FIELD (771 train images / 1162 components)',
     'clean-v3 FULL_FIELD (770 train images / 1161 components)',
     'clean-v3 population', False, False),
    ('oracle budget', 'TopK=5 largest GT components (because TRAIN max is 11)',
     'TopK=5 largest GT components (clean-v3 TRAIN max is still 11)',
     'unchanged; ORACLE_UNBOUNDED remains optional', False, False),
    ('FP-burden reporting', 'reported post hoc (5.43 FP components/image vs 0.37 baseline)',
     'report proposal precision, unmatched proposals/image and the FP burden prospectively',
     'the Phase-14 Step-3 failure was driven by proposal FP clutter', True, False),
    ('cross-phase gate', 'Phase-14 confirmatory path COMPLETE_CLOSED_NOT_RUN '
     '(FROZEN_ENTRY_GATE_NOT_MET)',
     'Phases 14-18 remain PENDING_POST_PHASE13_REGIONAL_INTEGRATION_GATE; no automatic '
     'progression', 'unchanged', False, False),
]


def build_downstream_integration() -> pd.DataFrame:
    return pd.DataFrame(DOWNSTREAM, columns=[
        'item', 'historical_v2', 'proposed_clean_v3', 'change_reason',
        'scientifically_material', 'supervisor_decision_required'])


# ---------------------------------------------------------------------------
# §11 Oracle-retention metric contract (dimension B arithmetic)
# ---------------------------------------------------------------------------
RETENTION_CONTRACT = [
    ('T_g', 'GLOBAL baseline coverage90', 'covered90 components / all GT components achieved '
     'by the frozen global baseline on the clean-v3 FULL_FIELD population',
     'clean-v3 FULL_FIELD 103 cases / 152 components', 'to be computed in Phase 13 (clean-v3)',
     'NOT_YET_COMPUTED', 'replaces the historical v2 value 0.780822'),
    ('T_o', 'ORACLE REGION coverage90', 'covered90 components / all GT components achieved '
     'with GT-derived regional crops',
     'clean-v3 FULL_FIELD 103 cases / 152 components', 'Phase-12/13 clean-v3 oracle path',
     'NOT_YET_COMPUTED', 'the clean-v3 upper bound; must NOT be copied from the v2 value '
     '1.000000'),
    ('T_p', 'PREDICTED REGION coverage90', 'covered90 components / all GT components achieved '
     'with GT-free predicted proposals',
     'clean-v3 FULL_FIELD 103 cases / 152 components', 'Phase 13 (clean-v3)',
     'NOT_YET_COMPUTED', 'the quantity Phase 13 exists to measure'),
    ('G', 'Refiner potential', 'G = T_o - T_g', 'as above', 'derived',
     'NOT_YET_COMPUTED', 'denominator of the retention ratio; if G <= 0 retention is '
     'undefined and the gate must report NO_GO / REVISE rather than a ratio'),
    ('R', 'Proposal retention fraction', 'R = (T_p - T_g) / G',
     'as above', 'derived', 'NOT_YET_COMPUTED',
     'historical v2 value was exactly 0.500000; the clean-v3 value is a CANDIDATE, not a '
     'threshold, until the supervisor freezes it'),
    ('D_g', 'GLOBAL full-field Dice', 'macro Dice of the frozen global baseline',
     'clean-v3 FULL_FIELD 103 cases', 'Phase 12 clean-v3 (read-only reference)',
     'AVAILABLE_REFERENCE', 'per-model: ' + json.dumps(PHASE12_GLOBAL_DICE)),
    ('D_o', 'ORACLE REGION full-field Dice', 'macro Dice with GT-derived regional crops',
     'clean-v3 FULL_FIELD 103 cases', 'Phase 12 clean-v3 (read-only reference)',
     'AVAILABLE_REFERENCE', 'per-model: ' + json.dumps(PHASE12_ORACLE_DICE)),
    ('D_p', 'PREDICTED REGION full-field Dice', 'macro Dice with GT-free predicted proposals',
     'clean-v3 FULL_FIELD 103 cases', 'Phase 13 (clean-v3)', 'NOT_YET_COMPUTED',
     'the historical v2 value was 0.383905 and drove the Phase-14 Step-3 failure'),
    ('object_recall_global_vs_oracle', 'clean-v3 object recall GLOBAL -> ORACLE',
     'per-model object recall pair', 'clean-v3 FULL_FIELD 152 components',
     'Phase 12 clean-v3 (read-only reference)', 'AVAILABLE_REFERENCE',
     'per-model (global, oracle): ' + json.dumps(PHASE12_OBJECT_RECALL)),
    ('retention_scope', 'architecture scope',
     'R and G must be reported for ALL FOUR frozen baselines, not a single architecture',
     'clean-v3 FULL_FIELD', 'SR-1 requirement', 'CANDIDATE',
     'no reference model is selected; heterogeneity must be visible'),
    ('retention_primary_metric', 'primary retention metric',
     'coverage90-based retention on the re-derived clean-v3 hard sets, with the '
     'Dice-based retention reported alongside',
     'clean-v3 FULL_FIELD', 'candidate contract', 'CANDIDATE',
     'the historical contract used coverage90 only; reporting both is more informative'),
]


def build_oracle_retention_contract() -> pd.DataFrame:
    return pd.DataFrame(RETENTION_CONTRACT, columns=[
        'symbol', 'name', 'definition', 'population', 'source', 'status', 'notes'])


# ---------------------------------------------------------------------------
# §12 Gate dimension B candidate
# ---------------------------------------------------------------------------
GATE_DIMENSION_B = [
    ('B', 'PRACTICAL_LOCALIZATION_RETENTION',
     'In Phase 13, how much of the clean-v3 ORACLE regional-resolution benefit is retained '
     'using a deployable GT-free localizer?',
     'T_g, T_o, T_p, G, R, D_g, D_o, D_p, size-stratum recall90, proposal precision, '
     'proposals/image, ROI area fraction',
     'CANDIDATE_FOR_SUPERVISOR_FREEZE',
     'Candidate: R clearly above zero AND D_p not materially below D_g AND the recovery is '
     'not confined to a single architecture. Exact numeric thresholds NOT frozen.',
     'NOT_FROZEN'),
]


def build_gate_dimension_b() -> pd.DataFrame:
    return pd.DataFrame(GATE_DIMENSION_B, columns=[
        'dimension_id', 'dimension', 'question', 'evidence_fields', 'criterion_status',
        'candidate_criterion', 'numeric_threshold'])


# ---------------------------------------------------------------------------
# §13 Gate dimensions C/D + bridge
# ---------------------------------------------------------------------------
GATE_CD = [
    ('A', 'ORACLE_MECHANISM_VALUE', 'SUPPORTED_DESCRIPTIVE_EVIDENCE',
     'No further Phase-13 evidence required; Phase-13 evidence must not contradict it.',
     'Phase 12 -> Phase 13',
     'Positive median paired delta Dice across all four clean-v3 models (descriptive).'),
    ('B', 'PRACTICAL_LOCALIZATION_RETENTION', 'NOT_EVALUABLE_UNTIL_PHASE13',
     'Phase-13 T_g / T_o / T_p / G / R on the clean-v3 population; re-derived clean-v3 hard '
     'sets; per-architecture reporting.',
     'Phase 13 -> REGIONAL_INTEGRATION_GATE_AFTER_PHASE13',
     'Candidate: R above zero; exact fraction NOT frozen.'),
    ('C', 'GLOBAL_PRESERVATION_FP_COST', 'MIXED_DESCRIPTIVE_EVIDENCE',
     'Phase-13 proposal precision, unmatched proposals/image, FP component burden, and '
     'D_p vs D_g. The historical Phase-14 failure was an FP-clutter failure.',
     'Phase 13 -> Phase 14 (conditional)',
     'Candidate: no material global degradation (D_p drop bounded) with a prospective FP '
     'report. Exact bound NOT frozen.'),
    ('D', 'GENERALITY', 'SUPPORTED_WITH_HETEROGENEITY',
     'Phase-13 per-architecture retention spread and per-stratum retention.',
     'Phase 13 -> RA-MedFiLM regional-mechanism reuse',
     'Candidate: retention not confined to one architecture or one size stratum.'),
]


def build_gate_cd_bridge() -> pd.DataFrame:
    return pd.DataFrame(GATE_CD, columns=[
        'dimension_id', 'dimension', 'status_after_phase12', 'phase13_evidence_required',
        'bridge_to', 'candidate_criterion'])


# ---------------------------------------------------------------------------
# §14 Future visualization protocol
# ---------------------------------------------------------------------------
VIZ_PROTOCOL = [
    ('A', 'GLOBAL vs ORACLE vs PREDICTED coverage90', 'grouped bar',
     'clean-v3 FULL_FIELD 103 cases / 152 components'),
    ('B', 'retention fraction R per architecture', 'bar with the G denominator annotated',
     'per model; no reference model'),
    ('C', 'size-stratified recall90 across the three conditions', 'grouped bar '
     'TINY/SMALL/MEDIUM/LARGE', 'clean-v3 taxonomy strata'),
    ('D', 'hard-set recovery (re-derived clean-v3)', 'bar recovered/not-recovered',
     'clean-v3 hard sets, NOT the v2 16/7'),
    ('E', 'proposal count vs coverage trade-off', 'scatter with the feasibility region shaded',
     'proposals/image vs recall90'),
    ('F', 'ROI area fraction vs coverage', 'scatter with the area budget line',
     'union area fraction'),
    ('G', 'heatmap + proposal overlays', 'multipage panel (image, heatmap, proposals)',
     'deterministic selection; >= 12 cases'),
    ('H', 'TP/FP/FN error maps for the predicted-region condition', 'multipage panel',
     '>= 16 deterministic cases'),
    ('I', 'Dice distribution GLOBAL vs ORACLE vs PREDICTED', 'paired violin/box',
     'paired within case and architecture'),
    ('J', 'proposal precision vs coverage', 'scatter', 'prospective FP-cost reporting'),
    ('K', 'Phase-12 vs Phase-13 evidence alignment', 'side-by-side bar of the delta Dice and '
     'the retention fraction', 'oracle upper bound vs deployable result'),
]


def build_viz_protocol() -> pd.DataFrame:
    return pd.DataFrame(VIZ_PROTOCOL, columns=['id', 'visualization', 'form', 'basis'])


# ---------------------------------------------------------------------------
# Audit builders
# ---------------------------------------------------------------------------
def build_reconstruction_audit() -> Dict[str, Any]:
    audit = json.loads(
        (AUDITS / 'phase13b_stage4d_final_evaluation.json').read_text(encoding='utf-8'))
    return {
        'phase': '13',
        'part': '1A',
        'document_type': 'HISTORICAL_LOCALIZER_PROTOCOL_RECONSTRUCTION',
        'status': 'COMPLETE',
        'date': '2026-09-21',
        'historical_manifest_version': MANIFEST_HIST,
        'historical_taxonomy': TAXONOMY_HIST,
        'historical_population': {
            'TRAIN_FULL_FIELD': {'images': 771, 'components': 1162},
            'VAL_FULL_FIELD': {'images': 106, 'components': 156,
                               'strata': VAL_STRATA_HIST},
            'source': 'reports/tables/kub_val_components_sized.csv',
        },
        'reconstruction_method': 'source-precedence ladder (executing source > persisted '
                                 'audit/table > executed notebook > frozen protocol/README '
                                 '> prose)',
        'source_inventory_rows': len(HISTORICAL_SOURCES),
        'stage_inventory_rows': len(HISTORICAL_STAGES),
        'protocol_matrix_rows': len(PROTOCOL_MATRIX),
        'authoritative_stage': {
            'experiment_id': STAGE4D_EXPERIMENT,
            'best_epoch': audit['best_epoch'],
            'total_epochs': audit['total_epochs'],
            'checkpoint_sha256': audit['checkpoint_sha256'],
            'selected_configuration': audit['selected_configuration'],
            'tiny_recall90': audit['gate_evaluation']['tiny_recall90'],
            'overall_recall90': audit['gate_evaluation']['overall_recall90'],
            'hard_tiny_recovered90': audit['gate_evaluation']['hard_tiny_recovered90'],
            'global_empty_images_covered90': audit['gate_evaluation'][
                'global_empty_images_covered90'],
            'mean_roi_area_fraction': audit['gate_evaluation']['mean_roi_area_fraction'],
            'mean_proposals_per_image': audit['gate_evaluation']['mean_proposals_per_image'],
        },
        'handoff_claims': [
            {'claim': c, 'expected': str(v), 'verdict': 'VERIFIED'}
            for c, v, _ in HANDOFF_CLAIMS
        ],
        'findings': {
            'HISTORICAL_TRAIN_INFERENCE_PROPOSAL_DISTRIBUTION_MISMATCH': {
                'status': 'VERIFIED',
                'evidence': [
                    'reports/audits/phase14_diagnostic_protocol_amendment.md §6 (A3 policy): '
                    '1162 GT-derived base crops + 2324 perturbed crops + 1542 background '
                    'negatives = 5028 crops/epoch',
                    'reports/audits/phase14_part1_implementation_preflight.md: dataset '
                    'composition 5028 (1162 / 2324 / 1542)',
                    'reports/audits/phase14_diagnostic_protocol_amendment.md §3 Condition C: '
                    'the same refiner is evaluated on frozen Stage-4D PREDICTED proposals',
                ],
                'statement': 'The historical Phase-14 regional refiner was TRAINED on '
                             'GT-derived base crops, GT-perturbed crops and random '
                             'background negatives, but EVALUATED on Stage-4D predicted '
                             'proposals. The training and inference proposal distributions '
                             'therefore did not match.',
                'consequence': 'The Phase-14 Step-3 failure (D_p 0.383905 vs D_g 0.652776, '
                               'driven by 5.43 FP components/image vs 0.37 baseline) is at '
                               'least partly attributable to this distribution gap and is '
                               'NOT a clean measurement of predicted-proposal regional '
                               'refinement.',
                'clean_v3_action': 'Any clean-v3 regional integration must draw training '
                                   'crops from predicted proposals (with an explicit '
                                   'negative-sampling policy) or explicitly declare and '
                                   'measure the gap.',
            },
            'LATENT_INFERENCE_HEATMAP_RESOLUTION_OMISSION': {
                'status': 'VERIFIED_DEFECT',
                'evidence': 'src/inference/learned_roi.py predict_localizer calls '
                            'create_model("kub_localizer", in_channels=1, out_channels=1, '
                            'base_channels=16) with no heatmap_resolution argument',
                'statement': 'The Stage-4D checkpoint was trained with a 128x128 output '
                             'heatmap (AvgPool2d(4,4)). The inference helper would construct '
                             'the 512-output variant. Because the logit downsample is '
                             'parameter-free and the head is a 1x1 convolution, the state '
                             'dict still loads, so the mismatch is silent and the helper '
                             'would return a 512-space heatmap.',
                'impact': 'Proposal geometry (factor = 512 // heatmap_resolution) would be '
                          'wrong for the Stage-4D checkpoint. The Phase-13B notebooks used '
                          'the dataset/evaluator path, so the historical frozen numbers are '
                          'not affected.',
                'clean_v3_action': 'Pass heatmap_resolution explicitly (or freeze an '
                                   'output-resolution contract) and add a regression test.',
            },
            'STAGE4D_DESIGN_AUDIT_LABEL_AMBIGUITY': {
                'status': 'AMBIGUOUS',
                'evidence': 'reports/audits/phase13b_stage4d_design_audit.json keys the '
                            'Stage-4C numbers under "clean_v3_results" while the localizer '
                            'VAL denominator was 156 (v2)',
                'statement': 'The label most plausibly refers to the clean-v3 ARCHITECTURE '
                             '(KUBLocalizer), not the clean-v3 MANIFEST.',
                'clean_v3_action': 'Supervisor confirmation before any reuse of the Stage-4C '
                                   'numbers.',
            },
            'MISSING_VAL_SEARCH_EPOCH_079': {
                'status': 'VERIFIED',
                'evidence': f'experiments/{STAGE4D_EXPERIMENT}/ contains 87 val_search files; '
                            'val_search_epoch079.csv is absent while history.csv has 88 '
                            'contiguous epochs',
                'statement': 'Only the per-epoch proposal-grid dump for epoch 079 is missing; '
                             'the epoch history itself is complete.',
                'clean_v3_action': 'None required for Phase 13; noted for provenance.',
            },
        },
        'phase14_gate_arithmetic_reference': PHASE14_GATE,
        'phase14_classification': 'DIAGNOSTIC_PRACTICAL_SIGNAL_INSUFFICIENT',
        'governance': {
            'test_reads': 0,
            'test_metrics': 'NONE',
            'training_performed': False,
            'inference_performed': False,
            'proposals_generated': False,
            'checkpoints_modified': False,
            'history_modified': False,
            'configs_modified': False,
            'manifests_modified': False,
            'experiment_a_modified': False,
            'phase14_executed': False,
            'external_data_used': False,
        },
        'conclusion': 'Historical Phase-13/13B localizer protocol reconstructed and frozen. '
                      'The historical population is phase4_v2 (106/156). Four findings '
                      'recorded, including a VERIFIED train/inference proposal-distribution '
                      'mismatch in the historical Phase-14 refiner.',
    }


def build_candidate_audit() -> Dict[str, Any]:
    return {
        'phase': '13',
        'part': '1A',
        'document_type': 'CLEAN_V3_LOCALIZER_PROTOCOL_CANDIDATE',
        'status': 'PROSPECTIVE_FREEZE_CANDIDATE_AWAITING_SUPERVISOR',
        'date': '2026-09-21',
        'manifest_version': MANIFEST_CLEAN,
        'taxonomy': TAXONOMY_CLEAN,
        'candidate_population': {
            'TRAIN_FULL_FIELD': POPULATION_CENSUS['TRAIN'],
            'VAL_FULL_FIELD': POPULATION_CENSUS['VAL'],
            'VAL_strata': VAL_STRATA_CLEAN,
            'roi_acquisitions': 'excluded (ROI_NOT_PRIMARY_BINNED)',
            'census_provenance': 'reports/tables/kub_view_type_inventory.csv + TRAIN/VAL mask '
                                 'census (mask > 0, 8-connectivity); TEST never read',
        },
        'candidate_protocol_rows': len(CANDIDATE),
        'postprocessing_rows': len(POSTPROCESSING),
        'metric_contract_rows': len(PROPOSAL_METRIC_CONTRACT),
        'downstream_rows': len(DOWNSTREAM),
        'retention_contract_rows': len(RETENTION_CONTRACT),
        'gate_dimension_b': GATE_DIMENSION_B[0][1],
        'gate_dimension_b_status': GATE_DIMENSION_B[0][4],
        'gate_dimensions_cd': {r[0]: r[2] for r in GATE_CD},
        'supervisor_decisions_required': [
            'Re-derivation of the clean-v3 hard sets (do NOT reuse the v2 16 Tiny / 7 '
            'global-empty sets).',
            'Approval of the clean-v3 localizer architecture/resolution/sigma candidate '
            '(KUBLocalizer, 128 output, sigma 0.75).',
            'Approval of the inference output-resolution contract that fixes the '
            'heatmap_resolution omission defect.',
            'Fixing (or explicitly declining to fix) the train/inference proposal-'
            'distribution mismatch for any future regional integration.',
            'Whether to freeze numeric thresholds for gate dimension B, or keep B '
            'descriptive for the Phase-13 decision.',
        ],
        'oracle_retention_reference': {
            'historical_v2': {'T_g': PHASE14_GATE['T_g'], 'T_o': PHASE14_GATE['T_o'],
                              'T_p': PHASE14_GATE['T_p'], 'G': PHASE14_GATE['G'],
                              'R': PHASE14_GATE['R']},
            'clean_v3': 'NOT_YET_COMPUTED — must be recomputed on 103/152',
        },
        'explicitly_not_done': [
            'No localizer training.',
            'No localizer inference.',
            'No proposal generation.',
            'No Phase-14 execution.',
            'No TEST access.',
            'No winner declared; no reference architecture selected.',
            'No regional-mechanism promotion; gate remains NOT_DECIDED.',
        ],
        'governance': {
            'test_reads': 0,
            'test_metrics': 'NONE',
            'training_performed': False,
            'inference_performed': False,
            'proposals_generated': False,
            'experiment_a_modified': False,
            'external_data_used': False,
            'phase14_executed': False,
        },
        'conclusion': 'A prospective clean-v3 localizer/proposal protocol candidate is frozen '
                      'for supervisor review. Nothing has been executed.',
    }


def _audit_to_md(a: Dict[str, Any]) -> str:
    lines: List[str] = []
    if a['document_type'] == 'HISTORICAL_LOCALIZER_PROTOCOL_RECONSTRUCTION':
        lines += [
            '# Phase 13 Part 1A — Historical Localizer Protocol Reconstruction',
            '',
            f"- Status: **{a['status']}**",
            f"- Historical manifest: `{a['historical_manifest_version']}` · "
            f"taxonomy `{a['historical_taxonomy']}`",
            '',
            '## Historical population (phase4_v2)',
            '',
            f"- TRAIN FULL_FIELD: {a['historical_population']['TRAIN_FULL_FIELD']['images']} "
            f"images / {a['historical_population']['TRAIN_FULL_FIELD']['components']} components",
            f"- VAL FULL_FIELD: {a['historical_population']['VAL_FULL_FIELD']['images']} "
            f"images / {a['historical_population']['VAL_FULL_FIELD']['components']} components "
            f"· strata {a['historical_population']['VAL_FULL_FIELD']['strata']}",
            '',
            '## Authoritative stage (Stage-4D-R2)',
            '',
            f"- experiment: `{a['authoritative_stage']['experiment_id']}`",
            f"- best epoch {a['authoritative_stage']['best_epoch']} / "
            f"{a['authoritative_stage']['total_epochs']} total",
            f"- checkpoint SHA `{a['authoritative_stage']['checkpoint_sha256']}`",
            f"- selected config {a['authoritative_stage']['selected_configuration']}",
            f"- Tiny recall90 {a['authoritative_stage']['tiny_recall90']:.6f} · "
            f"overall recall90 {a['authoritative_stage']['overall_recall90']:.6f}",
            f"- hard Tiny recovered90 {a['authoritative_stage']['hard_tiny_recovered90']}/16 · "
            f"global-empty {a['authoritative_stage']['global_empty_images_covered90']}/7",
            f"- mean ROI area {a['authoritative_stage']['mean_roi_area_fraction']:.6f} · "
            f"proposals/image {a['authoritative_stage']['mean_proposals_per_image']:.6f}",
            '',
            '## Handoff claims — all VERIFIED',
            '',
        ]
        for c in a['handoff_claims']:
            lines.append(f"- {c['claim']}: `{c['expected']}` — **{c['verdict']}**")
        lines += ['', '## Findings', '']
        f = a['findings']['HISTORICAL_TRAIN_INFERENCE_PROPOSAL_DISTRIBUTION_MISMATCH']
        lines += [
            f"### `HISTORICAL_TRAIN_INFERENCE_PROPOSAL_DISTRIBUTION_MISMATCH` — "
            f"**{f['status']}**",
            '',
            f['statement'],
            '',
            f"**Consequence.** {f['consequence']}",
            '',
            f"**Clean-v3 action.** {f['clean_v3_action']}",
            '',
        ]
        for k, v in a['findings'].items():
            if k == 'HISTORICAL_TRAIN_INFERENCE_PROPOSAL_DISTRIBUTION_MISMATCH':
                continue
            lines += [f"### `{k}` — **{v['status']}**", '', v['statement'], '',
                      f"**Clean-v3 action.** {v['clean_v3_action']}", '']
        lines += ['## Governance', '',
                  '- TEST reads **0** · training **0** · inference **0** · proposals **0**',
                  '- No checkpoint/history/config/manifest was modified',
                  '- Phase 14 not executed · Experiment A untouched',
                  '',
                  f"**Conclusion.** {a['conclusion']}"]
    else:
        lines += [
            '# Phase 13 Part 1A — Clean-v3 Localizer Protocol Candidate',
            '',
            f"- Status: **{a['status']}**",
            f"- Manifest `{a['manifest_version']}` · taxonomy `{a['taxonomy']}`",
            '',
            '## Candidate population (clean-v3)',
            '',
            f"- TRAIN FULL_FIELD: {a['candidate_population']['TRAIN_FULL_FIELD']['images']} "
            f"images / {a['candidate_population']['TRAIN_FULL_FIELD']['components']} components",
            f"- VAL FULL_FIELD: {a['candidate_population']['VAL_FULL_FIELD']['images']} "
            f"images / {a['candidate_population']['VAL_FULL_FIELD']['components']} components "
            f"· strata {a['candidate_population']['VAL_strata']}",
            f"- ROI acquisitions: {a['candidate_population']['roi_acquisitions']}",
            '',
            '## Retention arithmetic',
            '',
            f"- historical v2: {a['oracle_retention_reference']['historical_v2']}",
            f"- clean-v3: {a['oracle_retention_reference']['clean_v3']}",
            '',
            '## Supervisor decisions required',
            '',
        ]
        for s in a['supervisor_decisions_required']:
            lines.append(f"- {s}")
        lines += ['', '## Explicitly not done', '']
        for s in a['explicitly_not_done']:
            lines.append(f"- {s}")
        lines += ['', '## Governance', '',
                  '- TEST reads **0** · training **0** · inference **0** · proposals **0**',
                  '- No winner declared · no reference model selected · gate NOT_DECIDED',
                  '',
                  f"**Conclusion.** {a['conclusion']}"]
    return '\n'.join(lines) + '\n'


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------
TABLE_BUILDERS = {
    'phase13_historical_source_inventory.csv': build_source_inventory,
    'phase13_historical_stage_inventory.csv': build_stage_inventory,
    'phase13_historical_localizer_protocol_matrix.csv': build_protocol_matrix,
    'phase13_historical_checkpoint_provenance.csv': build_checkpoint_provenance,
    'phase13_historical_handoff_verification.csv': build_handoff_verification,
    'phase13_v2_to_clean_v3_localizer_protocol_diff.csv': build_protocol_diff,
    'phase13_clean_v3_training_population_spec.csv': build_population_spec,
    'phase13_clean_v3_localizer_protocol_candidate.csv': build_candidate_protocol,
    'phase13_clean_v3_proposal_postprocessing_candidate.csv': build_postprocessing_candidate,
    'phase13_clean_v3_proposal_metric_contract.csv': build_proposal_metric_contract,
    'phase13_clean_v3_downstream_integration_candidate.csv': build_downstream_integration,
    'phase13_oracle_retention_metric_contract.csv': build_oracle_retention_contract,
    'phase13_gate_dimension_b_candidate.csv': build_gate_dimension_b,
    'phase13_gate_dimensions_cd_bridge.csv': build_gate_cd_bridge,
    'phase13_future_visualization_protocol.csv': build_viz_protocol,
}


def write_all(write_audits: bool = True) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for name, fn in TABLE_BUILDERS.items():
        df = fn()
        p = TABLES / name
        df.to_csv(p, index=False, encoding='utf-8')
        out[name] = sha256_file(p)
    if write_audits:
        rec = build_reconstruction_audit()
        jp = AUDITS / 'phase13_historical_localizer_protocol_reconstruction.json'
        jp.write_text(json.dumps(rec, indent=2, ensure_ascii=False), encoding='utf-8')
        out[jp.name] = sha256_file(jp)
        mp = AUDITS / 'phase13_historical_localizer_protocol_reconstruction.md'
        mp.write_text(_audit_to_md(rec), encoding='utf-8')
        out[mp.name] = sha256_file(mp)

        cand = build_candidate_audit()
        jp2 = AUDITS / 'phase13_clean_v3_localizer_protocol_candidate.json'
        jp2.write_text(json.dumps(cand, indent=2, ensure_ascii=False), encoding='utf-8')
        out[jp2.name] = sha256_file(jp2)
        mp2 = AUDITS / 'phase13_clean_v3_localizer_protocol_candidate.md'
        mp2.write_text(_audit_to_md(cand), encoding='utf-8')
        out[mp2.name] = sha256_file(mp2)
    return out


if __name__ == '__main__':
    hashes = write_all()
    for k, v in hashes.items():
        print(f'{v}  {k}')
