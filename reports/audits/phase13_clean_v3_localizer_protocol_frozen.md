# Phase 13 Part 1A-R1 — Clean-v3 Localizer Protocol (SUPERVISOR FROZEN)

- Status: **SUPERVISOR_FROZEN_READY_FOR_PART1B_TRAINING**
- Phase/part: `13` / `1A-R1` · Model: Gemini 3.8 Flash Medium
- Manifest `phase4_v3` · taxonomy `kub_size_clean_v3_v1`

## 1. Hard sets (re-derived on clean-v3, frozen before training)

- **hard_tiny**: 15 components · `2f9828d77c008e7c90cd69e82d0af3568902ca9d508fdfcb9d8ccf8abd569538`
  - `reports/tables/phase13_clean_v3_hard_tiny_replication_set.csv`
- **global_empty**: 5 images · `a0b332cad6bca4466ccc528cbe18cc527ef6503603ab69c55b9d699d7979f0ea`
  - `reports/tables/phase13_clean_v3_global_empty_replication_set.csv`
- Historical v2 counts (NOT a target): {'hard_tiny': 16, 'global_empty': 7}
- Anchor: **UNet++** = `HISTORICAL_PHASE13_HARDSET_REPLICATION_ANCHOR_ONLY` — not winner, best model, Phase-13 downstream reference model, final architecture choice
- Cross-validated against: `reports/tables/phase11_clean_v3_per_model_case_failure_metrics.csv`
- Must NOT replace the gate cohorts: Phase-11 ALL_FOUR_LOW, Phase-11 hard cohort, Phase-11 disagreement cohort, Phase-12 FULL_FIELD 103

## 2. Heatmap resolution contract

- input **512x512** → output heatmap **128x128**
- `heatmap_resolution=128`, always passed explicitly (never rely on a constructor default)
- fail-loud assertions: model output spatial shape == (128, 128); target heatmap spatial shape == (128, 128); prediction and target shapes identical
- defect: src/inference/learned_roi.predict_localizer omits heatmap_resolution=128
- preferred remediation **B** (clean-v3-safe inference wrapper)

## 3. Frozen proposal configuration

- threshold **0.1** · margin **0.2** · top_k **5** · nms_iou **0.3**
- provenance: `VERIFIED_HISTORICAL_SELECTION + PROSPECTIVELY_FROZEN_FOR_CLEAN_V3_PRIMARY`
- clean-v3 primary grid search: **DISABLED**
- historical 20-grid: `DEFERRED_SECONDARY_SENSITIVITY_ONLY`

## 4. Checkpoint-selection contract (fixed config only)

1. `hard_tiny_recovered90`
2. `global_empty_images_covered90`
3. `tiny_recall90`
4. `overall_recall90`
5. `multi_component_recall90`
6. `-mean_roi_area_fraction`
7. `-mean_proposals_per_image`
8. `-val_loss`

- strict improvement (`new_score > best_score (strict tuple comparison)`); ties are bad epochs; patience 15
- SUPERVISOR_SPECIFIED_CLEAN_V3_CONTRACT. The executing historical code used a 4-tuple (see HISTORICAL_EXECUTING_SELECTION); the supervisor R1 contract specifies an 8-term tuple that extends it with the hard-set, multi-component and proposals/image terms. The executing-code 4-tuple is recorded here so the deviation is never silently mis-stated as historical reproduction.

### 4.1 Provenance of the selection tuple (disclosed, not silently asserted)

- **executing code** `scripts/training/train_phase13b_localizer.py` line 164: `(tiny_recall90, overall_recall90, -mean_roi_area_fraction, -val_loss)` (length 4)
- **PHASE13B.md**: length 8
- **Stage-3 correction**: length 3

## 5. Phase-14 distribution requirement

- disposition: `DEFERRED_REQUIREMENT_FOR_PHASE14_IF_GATE_ALLOWS`
- is a Phase-13 localizer training change: **False**
- predicted-proposal training crops in Phase 13: **False**
- Phase-14 crop recipe frozen here: **False**

## 6. Downstream predicted-region contract (frozen, not executed)

- geometry: `{'threshold': 0.1, 'margin': 0.2, 'top_k': 5, 'nms_iou': 0.3}` (margin **0.2**, NOT the Phase-12 oracle margin 0.25)
- label: `PRACTICAL_GT_FREE_ORACLE_BENEFIT_RETENTION`
- composition: `PREDICTED_REGION_FLOAT_GLOBAL_RETAINED` — regional FLOAT_BILINEAR at 512x512, pixelwise MAX across regional crops, global RETAINED outside the proposal union, REPLACED inside; final threshold 0.5
- forbidden: max(global, regional) inside proposal support, averaging global/regional, learned fusion
- model scope: UNet, Attention U-Net, UNet++, DeepLabV3+ · reference model: **NONE**

## 7. Retention metric contract

- `oracle_gap_retention_dice = predicted_gain_dice / oracle_gain_dice`, only where `oracle_gain_dice > 0`
- numerical sufficient-retention threshold: **None**
- case level: report raw deltas; do NOT force ratios where oracle delta <= 0

## 8. Label defects recorded

- `STAGE4D_DESIGN_AUDIT_LABEL_PROVENANCE_DEFECT`: `clean_v3_results` in `phase13b_stage4d_design_audit.json` is **HISTORICAL_v2_PROVENANCE_ONLY** (denominator 156 = v2). Historical artifact NOT modified.
- `NON_BLOCKING_HISTORICAL_ARTIFACT_GAP`: `val_search_epoch079.csv` missing (87/88 dumps). Not recreated, not fabricated. `history.csv` remains authoritative (88/88 contiguous).

## 9. Gate governance

- dimension B `PRACTICAL_LOCALIZATION_RETENTION` — CANDIDATE_FOR_SUPERVISOR_FREEZE (final evidence contract recorded by this R1)
- scalar gate score: **None** · numerical GO threshold: **None**
- final regional gate: **NOT_DECIDED**; outcomes issued here: NONE

## 10. Governance boundary

- training **0** · optimizer steps **0** · model forward passes **0**
- localizer inference **0** · predicted-region inference **0** · proposals **0**
- clean-v3 grid search run: **False** · TEST content reads **0**
- Phase 14 started: **False** · historical artifacts modified: **False**
- winner declared **False** · reference model selected **False** · regional mechanism promoted **False**

**Next action:** `WAIT_FOR_SUPERVISOR_PHASE13_PART1B_TRAINING_AUTHORIZATION`
