# Oracle ROI Upper Bound Analysis (phase_12_oracle_roi)

---

## PART A — HISTORICAL_v2 PROVENANCE (sections 1–5 below)

> **The sections below are HISTORICAL_v2 provenance** (manifest `phase4_v2`, taxonomy
> `kub_size_v1`, UNet++ only, 106 FULL_FIELD images). They are **frozen historical text** and
> are **not** clean-v3 evidence.
>
> **Known prose error in §1 below:** "Phase 12 proves +16.2% Dice and 100% tiny recall" is
> **incorrect**. The authoritative historical audit records **+12.295974 percentage points**
> macro Dice (0.6527764131996552 → 0.7757361537396281) and **Tiny recall 0.9863013698630136**
> (not 1.0). See the companion errata:
> `reports/audits/phase12_historical_readme_errata.md`
> (`HISTORICAL_README_PROSE_ERROR` · `AUTHORITATIVE_AUDIT_PRECEDENCE`).
> The historical text is deliberately **not** rewritten here.

### 1. Scientific Overview
- **Phase ID:** phase_12_oracle_roi
- **Scientific Title:** Oracle ROI Upper Bound Analysis
- **Current Status:** COMPLETE
- **Core Question:** Phase 12 proves +16.2% Dice and 100% tiny recall given perfect GT bounding boxes.

### 2. Rationale & Academic Significance
Understanding the specific scientific role of this phase within the 41-phase canonical progression (Stage A: KUB Regional/Tiny Development, Stage B: Multi-Domain Scaling, Stage C: Evidence & Rigor, Stage D: Verification & Freeze).

### 3. Inputs & Governance Boundaries
- **Canonical Provenance Source:** reports/audits/phase12_oracle_roi_upper_bound.json
- **Dataset Cohorts:** TRAIN and VAL only (TEST strictly locked: TEST reads = 0).
- **Hardware Profile:** NVIDIA GeForce RTX 3060 Ti 8GB certified.

### 4. Primary Outputs & Deliverables
- **Documented Artifacts:** Checkpoints, metrics tables, error maps, and qualitative panels.
- **Reviewer Notebook:** Reviewer-facing reproducible Jupyter Notebook.

### 5. Visual Standards
- **Sample Visualizations:** $\ge 12$ deterministic cases where applicable.
- **Prediction Panels:** $\ge 16$ deterministic cases with TP/FP/FN error maps.

---

## PART B — CLEAN_v3 STATUS (authoritative for current state)

**Manifest:** `phase4_v3` · **Taxonomy:** `kub_size_clean_v3_v1` · **Strategy:** SR-1

### Phase 12 CLEAN-v3 status: **COMPLETE / PASS**

| Part | Status | Deliverable |
|---|---|---|
| 1A | **COMPLETE** | `phase12_clean_v3_oracle_regional_protocol_freeze.ipynb` |
| 1B | **COMPLETE** | `phase12_clean_v3_oracle_regional_inference.ipynb` |
| 1C | **COMPLETE** | `phase12_clean_v3_oracle_regional_analysis.ipynb` |
| 1D | **COMPLETE** | supervisor conclusion + closure (this update) |

### Conclusion

> **SUPPORTED_DESCRIPTIVE_EVIDENCE FOR ORACLE MECHANISM**
> (`ORACLE_MECHANISM_VALUE = SUPPORTED_DESCRIPTIVE_EVIDENCE`;
> `PHASE13_PROGRESSION = SCIENTIFICALLY_JUSTIFIED`)

Clean-v3 KUB FULL_FIELD evidence demonstrates exploitable regional-resolution headroom. The
GT-derived oracle regional intervention provides sufficiently strong descriptive evidence to
justify testing whether a deployable GT-free localization mechanism can retain useful
regional benefit.

**This does NOT mean:** the regional-integration gate is GO; the regional mechanism is
promoted; the RA-MedFiLM regional path is approved; predicted localization will work;
statistical superiority is established; or one baseline architecture is selected.

### Clean-v3 scope and headline evidence

- Primary population: **KUB FULL_FIELD VAL 103 cases / 152 native components**
- Models: UNet · Attention U-Net · UNet++ · DeepLabV3+ — **no reference model**
- Primary variant: **`ORACLE_FLOAT_GLOBAL_RETAINED`** (comparator `GLOBAL_NATIVE`)
- Margin 0.25, threshold 0.5, per-component oracle crops, FLOAT map-back

| Model | GLOBAL Dice | PRIMARY Dice | delta |
|---|---|---|---|
| UNet | 0.594180 | 0.724722 | +0.130542 |
| Attention U-Net | 0.629805 | 0.699595 | +0.069790 |
| UNet++ | 0.640516 | 0.726679 | +0.086164 |
| DeepLabV3+ | 0.560251 | 0.750372 | +0.190121 |

- Object recall rises to 0.9951–1.0000 for all four models
- **120 component×model recovery events** (pooled over 152 components × 4 models; **not**
  120 unique components) · **0 lost** component detections
- Size-stratified recovery events: TINY 74 · SMALL 20 · MEDIUM 19 · LARGE 7
- Empty-prediction recoveries: 27 case×model · **0 new** empty predictions
- 46/103 cases positive for all four models; 103/103 non-worse object recall
- **Cost (preserved):** 150/412 case×model rows worsen (max −0.5866 Dice); precision slightly
  decreases; FP pixel burden rises

### Oracle limitations

GT-derived location ⇒ **oracle upper-bound / mechanism experiment**, **not deployable**, and
it does **not** prove Phase 13 predicted localization reproduces the gain. The crop-only
comparator additionally enjoys **oracle background suppression**; the primary SR-1 result
remains `ORACLE_FLOAT_GLOBAL_RETAINED`.

### Canonical labels

- `DICE_IOU_GLOBAL_REPRODUCTION_GATE_PASS`
- `COMBINED_LEGACY_RESTORE_SENSITIVITY` (uint8 quantisation + resampling-engine confound;
  **not** gate-usable)

### Gate and next phase

- **Regional-integration gate: NOT DECIDED** (decided after Phase 13)
- **Regional mechanism promoted: NO**
- **Phase 13: NOT STARTED · NOT AUTHORIZED · ELIGIBLE**
- Phase-13 question: *Can a GT-free region proposal/localization mechanism retain enough of
  the Phase-12 oracle regional-resolution benefit while controlling FP burden and preserving
  global segmentation quality?* (compare GLOBAL vs ORACLE REGION vs PREDICTED REGION)

### Current action
**WAIT_FOR_SUPERVISOR_PHASE13_AUTHORIZATION.** TEST is **LOCKED** until Phase 39.
Phases 14–18 remain `PENDING_POST_PHASE13_REGIONAL_INTEGRATION_GATE`. RA-MedFiLM is
**NOT implemented**.
