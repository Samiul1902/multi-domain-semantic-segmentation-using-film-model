# Phase 13 Part 1A-R2 — Clean-v3 Localizer Protocol (SUPERVISOR FROZEN R2)

- Status: **SUPERVISOR_FROZEN_R2_READY_FOR_PART1B_TRAINING**
- Phase/part: `13` / `1A-R2` · Model: Gemini 3.8 Flash Medium
- Manifest `phase4_v3` · taxonomy `kub_size_clean_v3_v1`

## 1. Primary checkpoint-selection contract (CORRECTED)

- label: **`EXECUTING_HISTORICAL_4TERM_FIXED_CONFIG_SELECTION`** · role: **PRIMARY**
- provenance: **HISTORICAL EXECUTING CODE** (`scripts/training/train_phase13b_localizer.py` line 164)

```
(
    tiny_recall90,
    overall_recall90,
    -mean_roi_area_fraction,
    -val_loss,
)
```

- length **4** · comparison **STRICT_LEXICOGRAPHIC_GREATER_THAN** · ties **BAD_EPOCH** · patience **15**
- `best.pt`: only on strict tuple improvement
- `latest.pt`: every completed epoch, per the reconstructed trainer ordering
- checkpoint metadata must store: the COMPLETE tuple, the tuple term names
- evaluated at: ONE FIXED PROPOSAL CONFIGURATION ONLY (0.10 / 0.20 / 5 / 0.30)

### 1.1 R1 tuple retained as provenance only

- R1 8-term tuple status: **SUPERSEDED_FOR_PRIMARY_CHECKPOINT_SELECTION** (PROVENANCE)

## 2. Fixed proposal configuration (UNCHANGED from R1)

- threshold **0.1** · margin **0.2** · top_k **5** · nms_iou **0.3**
- clean-v3 primary grid search: **DISABLED**
- historical 20-grid: `DEFERRED_SECONDARY_SENSITIVITY_ONLY`

## 3. Diagnostic metrics (computed, NOT selection terms)

- `hard_tiny_recovered90`: **SECONDARY_DIAGNOSTIC_NOT_SELECTION_TERM**
- `global_empty_images_covered90`: **SECONDARY_DIAGNOSTIC_NOT_SELECTION_TERM**
- `multi_component_recall90`: **SECONDARY_DIAGNOSTIC_NOT_SELECTION_TERM**
- `mean_proposals_per_image`: **SECONDARY_DIAGNOSTIC_NOT_SELECTION_TERM**

These remain valuable and SHOULD be computed/logged per epoch when physically available. They MUST NOT participate in primary checkpoint selection. mean_proposals_per_image appeared in the R1 8-term extension but not in the executing 4-term tuple; it is preserved as a diagnostic only.

## 4. Hard sets (frozen; now secondary diagnostic cohorts)

- hard_tiny: **15** · `2f9828d77c008e7c90cd69e82d0af3568902ca9d508fdfcb9d8ccf8abd569538`
- global_empty: **5** · `a0b332cad6bca4466ccc528cbe18cc527ef6503603ab69c55b9d699d7979f0ea`
- role: **PRE_FROZEN_SECONDARY_DIAGNOSTIC_COHORT** · participates in primary selection: **False**
- anchor: **UNet++** = `HISTORICAL_PHASE13_HARDSET_REPLICATION_ANCHOR_ONLY`
- useful for: localization analysis, difficult-case analysis, historical comparison
- must NOT replace the gate cohorts: Phase-11 ALL_FOUR_LOW, Phase-11 hard cohort, Phase-11 disagreement cohort, Phase-12 FULL_FIELD 103

## 5. Heatmap contract (UNCHANGED from R1)

- input **512x512** → output heatmap **128x128**
- `heatmap_resolution=128`, always explicit; fail-loud shape assertions required
- preferred remediation **B** (clean-v3-safe wrapper); historical generic helper NOT altered

## 6. R1 supersession relationship

- R1 artifact: `reports/audits/phase13_clean_v3_localizer_protocol_frozen.json` `999144bbad4af4e1d2dc006279aef1a5fb93f450006ae2c5db159c791c913703`
- R1 status for execution: **SUPERSEDED_BY_SUPERVISOR_R2_CHECKPOINT_SELECTION_CORRECTION**
- R1 artifact modified: **False** (preserved for provenance)
- scope: ONLY the R1 8-term checkpoint-selection rule; all other R1 decisions remain frozen
- future Part 1B must use: `reports/audits/phase13_clean_v3_localizer_protocol_frozen_r2.json`

## 7. Recorded rationale

A. Checkpoint selection is a material scientific parameter.
B. The executing historical trainer is higher-authority evidence than prose documentation.
C. Using the executing 4-term tuple minimizes unnecessary v2->v3 protocol drift.
D. The R1 8-term extension would make primary checkpoint selection depend partly on hard cohorts derived using the UNet++ historical-replication anchor.
E. UNet++ is NOT a Phase-13 reference model.
F. Keeping those fields as diagnostics preserves their analytical value without allowing them to bias primary checkpoint selection.

## 8. R1 → R2 diff

- table: `reports/tables/phase13_r1_to_r2_protocol_diff.csv` `637bdffa4b6a51c2e5f1d5c00e5cfd59863e8a656f845a273ac2f3f67f8ca52c`
- material differences **1** · authorized **1** · unauthorized **0**
- changed fields **2** · unchanged fields **17**

## 9. Downstream contract (UNCHANGED from R1)

- primary: `PREDICTED_REGION_FLOAT_GLOBAL_RETAINED` · geometry margin **0.2** (oracle comparator 0.25)
- label: `PRACTICAL_GT_FREE_ORACLE_BENEFIT_RETENTION`
- model scope: UNet, Attention U-Net, UNet++, DeepLabV3+ · reference model: **NONE**
- retention: `oracle_gap_retention_dice = predicted_gain_dice / oracle_gain_dice`, only where `oracle_gain_dice > 0`; no sufficiency threshold
- gate: **NOT_DECIDED**; no GO / REVISE_LOCALIZER / NO_GO issued

## 10. Governance boundary

- training **0** · optimizer steps **0** · forward passes **0**
- localizer inference **0** · predicted-region inference **0** · proposals **0**
- TEST content reads **0** · Phase 14 started **False** · R1 artifacts modified **False** · historical artifacts modified **False**

**Next action:** `WAIT_FOR_SUPERVISOR_PHASE13_PART1B_TRAINING_AUTHORIZATION`
