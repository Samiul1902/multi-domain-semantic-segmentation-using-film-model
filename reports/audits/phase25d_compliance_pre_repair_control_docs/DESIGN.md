# DESIGN — Experimental Design and Verified Results

**Purpose:** Record the *experimental design*: philosophy, exact clean-v3 split counts, the
two KUB acquisition regimes, the frozen taxonomy, the frozen training protocol, the
**verified** clean-v3 VAL results (no ranking), the **verified** Phase-11 failure evidence,
and the **proposed** SR-1 RA-MedFiLM design with its future ablation plan.
See [PRD.md](PRD.md) for goals, [ARCHITECTURE.md](ARCHITECTURE.md) for structure,
[RULES.md](RULES.md) for constraints, [TASKS.md](TASKS.md) for status,
[MEMORY.md](MEMORY.md) for handoff.

**Last verified:** 2026-10-01 (Phase-25D router training spec v1.2.1 frozen)
**Strategy revision:** **SR-1** — status **ADOPTED**; method name **RA-MedFiLM-BARR**

> **Separation is mandatory in this document:**
> `VERIFIED_EVIDENCE` (measured) · `PROPOSED_DESIGN` (not implemented) ·
> `FUTURE_EXPERIMENT` (not run). Never present one as another.

**Canonical source paths:**
- `manifests/phase4_v3/*` + `manifests/manifest_registry.*` — split counts
- `reports/audits/kub_size_clean_v3_v1_thresholds.json` — taxonomy quantiles
- `configs/phase09_clean_v3/`, `configs/phase10_clean_v3/` — frozen configs
- `experiments/*/history.csv` (clean-v3) — verified results
- `reports/audits/phase11_clean_v3_failure_analysis_audit.*` — Phase-11 evidence
- `reports/tables/phase11_clean_v3_phase12_bridge_evidence.csv` — Phase-11 → Phase-12 bridge
- `reports/audits/phase13_historical_localizer_protocol_reconstruction.*` — Phase-13 Part-1A
  historical reconstruction
- `reports/audits/phase13_clean_v3_localizer_protocol_candidate.*` — Phase-13 Part-1A clean-v3
  protocol candidate (superseded by the frozen artifact below)
- `reports/audits/phase13_clean_v3_localizer_protocol_frozen.*` — Phase-13 Part-1A-R1 frozen
  clean-v3 localizer protocol (**superseded for execution by R2**, preserved as provenance)
- `reports/audits/phase13_clean_v3_localizer_protocol_frozen_r2.*` — Phase-13 Part-1A-R2
  **current SUPERVISOR-FROZEN R2** clean-v3 localizer protocol
- `reports/tables/phase13_r1_to_r2_protocol_diff.csv` — additive R1→R2 protocol diff
- `reports/tables/phase13_clean_v3_hard_tiny_replication_set.csv` — clean-v3 hard-Tiny cohort
- `reports/tables/phase13_clean_v3_global_empty_replication_set.csv` — clean-v3 global-empty cohort
- `reports/tables/phase13_historical_localizer_protocol_matrix.csv` — Phase-13 protocol matrix
- `reports/tables/phase13_clean_v3_training_population_spec.csv` — clean-v3 localizer population

---

## 1. Experimental philosophy

- **One variable at a time.** Clean-v3 reruns reproduce historical protocols exactly,
  changing only authorized governance/provenance fields ([RULES.md](RULES.md) §10).
- **Evidence over narrative.** Every verified number is traceable to a hashed artifact.
- **Frozen before comparison.** Protocols, thresholds, architectures frozen before any
  conclusion; TEST touched once, in Phase 39.
- **Seed discipline.** All clean-v3 runs use **seed 42**, single-seed → **no superiority
  claim is permitted** ([RULES.md](RULES.md) §9).
- **Evidence-gated complexity.** Regional machinery must **earn** inclusion via Phase 12/13
  and `REGIONAL_INTEGRATION_GATE_AFTER_PHASE13` — not by assertion.

## 2. REVISED SCIENTIFIC HYPOTHESIS (SR-1) — `PROPOSED` hypothesis

> A single global segmentation scale may be insufficient across heterogeneous medical
> domains and object scales, and **adaptive regional processing may recover small/local
> difficult targets while preserving global performance.**

`FUTURE_EXPERIMENT` — this is a hypothesis to be validated, **not** an established result.
Phase 11 provides *motivating* (not conclusive) evidence (§7).

## 3. Exact CLEAN-v3 split counts — `VERIFIED_EVIDENCE`

Global (`phase4_v3`, total 8441):

| Split | Count | Notes |
|---|---|---|
| TRAIN | 5832 | |
| VAL | 808 | |
| TEST | 1683 | **LOCKED**, byte-identical to v2 |
| QUARANTINED | 118 | excluded from development |

KUB subset: TRAIN **1978** · VAL **280** · TEST 558 (locked) · QUARANTINED 4.
VAL KUB composition: **Bladder_Stone 144, Kidney_Stone 112, Ureteric_Stone 24**.
VAL acquisition: **ROI 177, FULL_FIELD 103**. TRAIN/VAL patient overlap: **0**.

> Because KUB is only part of the global VAL (808), **any KUB VAL analysis MUST filter
> `dataset == "KUB"`**. Loading the full 808-row VAL silently mixes ISIC/BUSI/Kvasir — this
> error invalidated an earlier Phase-09 reviewer gallery
> (`INVALID_SUPERSEDED_CROSS_DOMAIN_SELECTION`).

## 4. FULL_FIELD vs ROI regimes, and the frozen taxonomy — `VERIFIED_EVIDENCE`

| | FULL_FIELD | ROI (crop) |
|---|---|---|
| Meaning | Full radiograph | Zoomed crop around a stone |
| Typical scale | Large (~2304–3072 px wide) | Small (tens–hundreds of px) |
| VAL count | 103 | 177 |

- **MUST** report FULL_FIELD and ROI separately; never pool without showing both.
- Taxonomy is calibrated on **FULL_FIELD** only; ROI = `ROI_NOT_PRIMARY_BINNED`.

**`kub_size_clean_v3_v1`** (status `FROZEN`, split TRAIN, scope FULL_FIELD):

| Property | Value |
|---|---|
| Foreground rule | `mask > 0` |
| Unit | connected component (connectivity **8**) |
| Metric | `component_ratio = component_pixels / (native_h * native_w)` |
| Quantiles (numpy default 'linear', float64) | Q25 **0.0001497998649691358** · Q50 **0.0003401438395182292** · Q75 **0.0008279682677469136** |
| Boundaries (lower-inclusive) | TINY `x ≤ Q25` · SMALL `Q25 < x ≤ Q50` · MEDIUM `Q50 < x ≤ Q75` · LARGE `x > Q75` |

Dataset-relative, **not** clinical millimetres.
Historical `kub_size_v1` (IMMUTABLE, v2 only): Q25 `0.0001499766777599` · Q50
`0.00033976472454305` · Q75 `0.0008266496069636999`. Never conflate.

> **SR-1 note:** KUB size thresholds **MUST NOT** be applied to other domains; each domain
> needs its own TRAIN-derived scale characterization ([RULES.md](RULES.md) §4).

## 5. Frozen training protocol (clean-v3 KUB runs) — `VERIFIED_EVIDENCE`

| Field | Value |
|---|---|
| Resolution | 512 · input/output channels 1 / 1 |
| Preprocessing | aspect-preserving resize + centre/symmetric pad; image BILINEAR, mask NEAREST; scaling [0,1]; extent `max(1, round(...))` |
| Loss | BCE + Dice, **0.5 / 0.5**, dice epsilon **1e-6** |
| Optimizer | **AdamW**, lr **1e-4**, weight decay **1e-4** |
| Scheduler | **CosineAnnealingLR**, T_max **100** (stepped per epoch, after train+val) |
| Batch / accum / effective | **4 / 1 / 4** |
| AMP | true · Seed **42** · Max epochs **100** |
| Early stopping | patience **15**, monitor **VAL macro Dice**, **strict `>`** (ties = bad epoch) |
| VAL | augmentation OFF, shuffle FALSE, KUB-only |
| Threshold | **0.5** (fixed) |
| Augmentation | hflip p=0.5, rot ±5°, brightness ±0.1, contrast ±0.1, vflip **false** |
| Init | random Kaiming, **no pretrained weights** |
| Epoch order | TRAIN → VAL → scheduler.step → improvement → early-stop → latest → best → stop |

Architecture-specific: UNet / Attention U-Net / UNet++ use **base_channels = 32**; UNet++
is `unetpp_nested_4_level_no_deep_supervision` (**deep supervision OFF**).

## 6. Verified CLEAN-v3 VAL results — `VERIFIED_EVIDENCE` (NO RANKING)

| Model | Experiment | Epochs | Best ep. | VAL Dice | VAL IoU | Precision | Recall |
|---|---|---|---|---|---|---|---|
| UNet | `phase9_kub_unet_baseline_seed42_512_clean_v3` | 59 | 44 | 0.7406133413314819 | 0.6253822445869446 | 0.7707186937332153 | 0.7839437127113342 |
| Attention U-Net | `phase10_kub_attention_unet_seed42_512_clean_v3` | 69 | 54 | 0.7525129853960107 | 0.6349387691368995 | 0.7729140812402236 | 0.7922248481868364 |
| UNet++ | `phase10_kub_unetpp_seed42_512_clean_v3` | 85 | 70 | 0.7641595156062713 | 0.6525442690586191 | 0.7996825971468945 | 0.7912384169561990 |
| DeepLabV3+ | `phase10_kub_deeplabv3plus_seed42_512_clean_v3` | 67 | 52 | 0.7509140344161673 | 0.6460492792430865 | 0.7943328495850855 | 0.7822983241135557 |

**NO RANKING · NO WINNER · SINGLE-SEED DESCRIPTIVE VAL.** The final descriptive Phase-10
comparison is **COMPLETE** (`phase10_clean_v3_final_baseline_comparison.ipynb`). DeepLabV3+
is `deeplabv3plus_resnet50_os16` (ResNet-50, no pretrained, os16, ASPP (6,12,18) + image
pooling, no aux head, 40,340,769 params).

**Complete epoch-by-epoch tables (mandatory rule).** One row per completed epoch,
untruncated, from the immutable `history.csv`, with derived reviewer-only columns
(`delta_val_dice_vs_previous_epoch`, `delta_best_metric`, `is_new_best`, `is_best_epoch`,
`epochs_since_best`). `history.csv` is never modified; unavailable fields show `N/A`.
Rows: UNet 59 · Attention U-Net 69 · UNet++ 85 · DeepLabV3+ 67.

## 7. Phase-11 verified failure evidence — `VERIFIED_EVIDENCE`

Manifest `phase4_v3` · taxonomy `kub_size_clean_v3_v1` · **KUB VAL 280** · 4 models ·
**reference model NOT selected** · historical replication anchor **UNet++**
(`HISTORICAL_REPLICATION_ANALYSIS_ANCHOR` only — **not** winner / best / Phase-12 reference).
Failure protocol: **`SUPERVISOR_FROZEN`** (frozen before inspection).

**Per-model clean-v3 Dice Q10** (bottom decile, ties included):
UNet `0.4693939398443986` · Attention U-Net `0.5360238052845407` ·
UNet++ `0.5618055568014564` · DeepLabV3+ `0.3784289703007593`.

**Shared failure — `ALL_FOUR_LOW`: 12 / 280.** `low_model_count` distribution:
`{0: 233, 1: 17, 2: 7, 3: 11, 4: 12}`.

**UNet++ anchored strata:** HD95 Q90 (valid only) `85.24095485204775`; valid/invalid
**274 / 6**. FP Q90 **5.0**; HIGH_FP count **31**.

**Empty predictions:** UNet 8 · Attention U-Net 3 · UNet++ 6 · DeepLabV3+ 11
(concentrated in FULL_FIELD).

**Object recall (eval-512, 8-conn, ≥1 px):** UNet `0.896341` · Attention U-Net `0.923780` ·
UNet++ `0.914634` · DeepLabV3+ `0.881098`.

**Multi-component native cases: 49.** Outcomes (complete / partial / miss):
UNet 30/16/3 · Attention U-Net 33/12/4 · UNet++ 33/11/5 · DeepLabV3+ 27/16/6.

**Regime gap (mean Dice): `0.2276`** (ROI ≫ FULL_FIELD for every model).

**Hard-case cohort: 16** (target 16, no underfilled strata). Selection SHA
`72f16916e9a9e86b047514842634ab7b73c245d131d5fbbd37db9fff171e3c46`.
Selection is **prediction-dependent by design** (unlike the prediction-independent Phase-10
gallery).

## 8. REGIONAL MECHANISM EVIDENCE CHAIN — `VERIFIED` → `FUTURE_EXPERIMENT`

```
clean data (Phase 05)                                    [VERIFIED]
  -> KUB characterization (Phase 06)                      [VERIFIED]
  -> tiny-object taxonomy (Phase 07, kub_size_clean_v3_v1) [VERIFIED]
  -> global baselines (Phases 08–09)                      [VERIFIED]
  -> four-model failure analysis (Phases 10–11)           [VERIFIED]
  -> oracle regional-resolution test (Phase 12)           [VERIFIED]
  -> GT-free localization feasibility (Phase 13)          [FUTURE_EXPERIMENT]
  -> REGIONAL_INTEGRATION_GATE_AFTER_PHASE13              [FUTURE_GATE]
  -> regional mechanism development (Phases 14–18)        [PENDING_POST_PHASE13_REGIONAL_INTEGRATION_GATE]
  -> multi-domain global model (Phases 19–20)             [FUTURE]
  -> global MedFiLM (Phase 21)                            [FUTURE]
  -> regional-aware MedFiLM (Phases 22–26)                [FUTURE]
  -> RA-MedFiLM-Seg++ (final intended system)             [PROPOSED_NOT_IMPLEMENTED]
```

### Phase-11 → Phase-12 bridge conclusion — `OBSERVED_DIAGNOSTIC_EVIDENCE`

Verdict: **`MOTIVATES_ORACLE_ROI_TEST`** — **with the explicit qualification that there is
no claim that ROI solves the problem.** Boundary-error and FP-burden items are recorded
**`MIXED`**. Source: `reports/tables/phase11_clean_v3_phase12_bridge_evidence.csv`.

## 9. Phase 12 verified oracle evidence — `VERIFIED_EVIDENCE` (COMPLETE / PASS)

**PHASE 12 — ORACLE REGIONAL-RESOLUTION UPPER BOUND.** *Does increased effective local
resolution recover failures that global segmentation misses?* — **answered descriptively,
across all four architectures** (no single reference model).

- Population: **KUB FULL_FIELD VAL 103 cases / 152 native components** · margin 0.25 ·
  threshold 0.5 · per-component oracle crops · FLOAT map-back
- Primary comparison: **`GLOBAL_NATIVE` vs `ORACLE_FLOAT_GLOBAL_RETAINED`** (paired, same
  case / architecture / native space / GT / threshold)
- Comparators (never primary): `ORACLE_FLOAT_CROP_ONLY` (secondary historical geometry) ·
  `ORACLE_LEGACY_UINT8_CROP_ONLY` (`COMBINED_LEGACY_RESTORE_SENSITIVITY`)
- Global reproduction: `DICE_IOU_GLOBAL_REPRODUCTION_GATE_PASS`

| Model | GLOBAL Dice | PRIMARY Dice | delta |
|---|---|---|---|
| UNet | 0.594180 | 0.724722 | +0.130542 |
| Attention U-Net | 0.629805 | 0.699595 | +0.069790 |
| UNet++ | 0.640516 | 0.726679 | +0.086164 |
| DeepLabV3+ | 0.560251 | 0.750372 | +0.190121 |

- Native object recall rises to **0.9951–1.0000** for all four models
- **120 component×model recovery events** (pooled over 152 × 4 = 608 rows — **not** 120
  unique components) · **0 lost** component detections
- Size-stratified recovery events: **TINY 74 · SMALL 20 · MEDIUM 19 · LARGE 7**
- Empty-prediction recoveries: **27** case×model · **0 new** empty predictions
- Cross-architecture: **46/103** cases positive for all four models; **103/103** non-worse
  object recall

**Cost (preserved, not hidden):** **150/412** case×model rows worsen (max **−0.5866** Dice);
mean precision slightly decreases (−0.0004 … −0.0500); mean FP pixel burden rises
(+2197 … +4167); mean FN pixel burden falls strongly (−1225 … −2194).
**Target recovery benefit is accompanied by a real FP / precision cost.** Phase 12 is **not**
universally beneficial case-by-case.

**Supervisor conclusion:** `ORACLE_MECHANISM_VALUE = SUPPORTED_DESCRIPTIVE_EVIDENCE` ·
`PHASE13_PROGRESSION = SCIENTIFICALLY_JUSTIFIED`. This does **not** mean the gate is GO, the
regional mechanism is promoted, predicted localization will work, or statistical superiority
is established.

**Oracle limitation:** Phase 12 uses GT-derived target location ⇒ an **oracle upper-bound /
mechanism experiment**, **not deployable**; it does not prove Phase 13 can reproduce the gain.
The crop-only comparator additionally enjoys oracle background suppression.

## 10. Phase 13 purpose — `PARTS_1A_1A_R1_1A_R2_COMPLETE / PROTOCOL_SUPERVISOR_FROZEN_R2`

**PHASE 13 — GT-FREE REGION PROPOSAL / LOCALIZATION.**
**Status: PARTS 1A / 1A-R1 / 1A-R2 COMPLETE · PROTOCOL `SUPERVISOR_FROZEN_R2` · PART 1B
ELIGIBLE but NOT AUTHORIZED.** Phase 13 progression is `SCIENTIFICALLY_JUSTIFIED` by Phase 12.
Part 1A reconstructed the historical (`phase4_v2`) localizer protocol; Part 1A-R1 recorded the
supervisor decisions and froze the clean-v3 protocol; Part 1A-R2 corrected the primary
checkpoint-selection rule to the executing historical 4-term tuple. Current frozen artifact:
`reports/audits/phase13_clean_v3_localizer_protocol_frozen_r2.json`. No training, no inference
and no proposal generation has been performed, and Part 1B may not start without supervisor
authorization.
Primary question: *can a deployable GT-free proposal mechanism preserve enough of the
Phase-12 oracle benefit while controlling FP burden and preserving global segmentation
quality?*

**Part-1A reconstruction (frozen, historical `phase4_v2`):** final localizer
`phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_v1` · best epoch **73 / 88** ·
Tiny recall90 `53/73 = 0.726027` · overall `100/156 = 0.641026` · hard Tiny `7/16` ·
global-empty `3/7` · selected proposal config `0.10 / 0.20 / 5 / 0.30`. The Phase-14 frozen
entry gate was **NOT PASSED**. **Clean-v3 FULL_FIELD is TRAIN 770 / 1161 · VAL 103 / 152** —
the historical numbers belong to a different population (106 / 156) and must not be compared
with clean-v3 numbers as if the splits matched.

**R2 primary checkpoint-selection contract:** the **4-term executing historical tuple**
`(tiny_recall90, overall_recall90, -mean_roi_area_fraction, -val_loss)`, strict lexicographic,
ties = bad epoch, patience 15, evaluated at the fixed proposal configuration. Label
`EXECUTING_HISTORICAL_4TERM_FIXED_CONFIG_SELECTION`. The R1 8-term tuple is
`SUPERSEDED_FOR_PRIMARY_CHECKPOINT_SELECTION` and preserved as provenance.
`hard_tiny_recovered90`, `global_empty_images_covered90`, `multi_component_recall90` and
`mean_proposals_per_image` are `SECONDARY_DIAGNOSTIC_NOT_SELECTION_TERM` — computed and logged,
excluded from selection.

**Part-1A-R1 frozen clean-v3 protocol (unchanged by R2):** hard sets **re-derived** on clean-v3
(hard-Tiny **15** components `2f9828d7…` · global-empty **5** images `a0b332ca…`; historical v2
was 16 / 7 and the counts need not match), anchored on UNet++ as
`HISTORICAL_PHASE13_HARDSET_REPLICATION_ANCHOR_ONLY`; proposal configuration frozen at
**`0.10 / 0.20 / 5 / 0.30`** with the per-epoch 20-config grid search **DISABLED**
(`DEFERRED_SECONDARY_SENSITIVITY_ONLY`); heatmap contract **512×512 → 128×128** with
`heatmap_resolution=128` always explicit and fail-loud shape assertions; predicted-proposal
training crops **removed** from Phase-13 scope; Phase-14 distribution-match requirement
`DEFERRED_REQUIREMENT_FOR_PHASE14_IF_GATE_ALLOWS`; downstream primary
`PREDICTED_REGION_FLOAT_GLOBAL_RETAINED` at margin **0.20** (the Phase-12 oracle used 0.25), so
the retention metric is `PRACTICAL_GT_FREE_ORACLE_BENEFIT_RETENTION` and is **not** a pure
localization-error isolation study.

**Findings:** `HISTORICAL_TRAIN_INFERENCE_PROPOSAL_DISTRIBUTION_MISMATCH` (VERIFIED, deferred to
Phase 14), `LATENT_INFERENCE_HEATMAP_RESOLUTION_OMISSION` (VERIFIED_DEFECT, fix approved),
`STAGE4D_DESIGN_AUDIT_LABEL_PROVENANCE_DEFECT` (historical v2 provenance only),
`NON_BLOCKING_HISTORICAL_ARTIFACT_GAP` (`val_search_epoch079.csv`, not fabricated).
**Checkpoint-selection provenance:** the executing code
(`scripts/training/train_phase13b_localizer.py:164`) used a **4-term** tuple; R1 briefly froze an
8-term extension, and **R2 restored the executing 4-term tuple as primary** (executing source is
higher-authority evidence than prose, and the correction minimises v2→v3 drift).

- Proposal system should be architecture-agnostic where feasible, exposing a reusable
  interface: `image -> proposal representation -> box / heatmap / confidence / scale estimate`.
- Evaluate: proposal target coverage · small/tiny coverage · multi-component coverage ·
  FULL_FIELD localization · proposal count · proposal precision · downstream segmentation
  utility.
- Compare: **GLOBAL vs ORACLE REGION vs PREDICTED REGION**.
- Output feeds `REGIONAL_INTEGRATION_GATE_AFTER_PHASE13`.

## 11. REGIONAL_INTEGRATION_GATE_AFTER_PHASE13 — `FUTURE_GATE`

| Outcome | Meaning | Action |
|---|---|---|
| **GO** | Oracle helps **AND** predicted localization retains meaningful utility | Promote the regional mechanism toward RA-MedFiLM-Seg++ |
| **REVISE_LOCALIZER** | Oracle helps **BUT** predicted localization loses too much benefit | Do **not** abandon the hypothesis; redesign localizer work first |
| **NO_GO** | Even oracle provides insufficient meaningful benefit | Do **not** force regional complexity; proceed with global multi-domain MedFiLM and document the negative evidence |

> **Criteria MUST be prospectively frozen** before inspecting Phase-12/13 results.
> **No numerical thresholds are defined in this pack** ([RULES.md](RULES.md) §12).

### Gate state after Phase 12 — **NOT_DECIDED**

| Dim | Dimension | Status after Phase 12 |
|---|---|---|
| **A** | ORACLE_MECHANISM_VALUE | **SUPPORTED_DESCRIPTIVE_EVIDENCE** |
| **B** | PRACTICAL_LOCALIZATION_RETENTION | **NOT_EVALUABLE_UNTIL_PHASE13** |
| **C** | GLOBAL_PRESERVATION_FP_COST | **MIXED_DESCRIPTIVE_EVIDENCE** |
| **D** | GENERALITY | **SUPPORTED_WITH_HETEROGENEITY** |

**Final gate: NOT_DECIDED.** No GO / REVISE_LOCALIZER / NO_GO is issued. The regional
mechanism is **NOT promoted**. The gate is decided only after Phase 13.
State table: `reports/tables/regional_integration_gate_state_after_phase12.csv`.

## 12. RA-MedFiLM design — `IMPLEMENTED_IN_PART` (see §16 for the frozen contract)

> **Status update 2026-09-30.** The design below is **no longer merely proposed**: the
> global model and the regional refiner are **implemented, trained and frozen**
> (Phase-21 / Phase-25A), and the benefit-router feature contract is **frozen in v1.2**
> (§16). The router itself is **specified but NOT trained**; Phase25B is
> `REENTRY_ELIGIBLE_NOT_STARTED`. The bullets below are retained as the original design
> intent.

Intended capability set (SR-1): modality/input adaptation · shared/global segmentation
representation · task/domain FiLM conditioning · GT-free region proposal/localization ·
higher-effective-resolution regional processing · regional/refinement representation ·
scale/region-aware FiLM conditioning · adaptive global-regional fusion/routing · final
binary segmentation output.

Conceptual FiLM form `F' = gamma(c) * F + beta(c)` with candidate conditioning vector
`c = [domain_embedding, scale_embedding, proposal_confidence, global_context]`
(+ legitimate inference-available metadata only).

**Metadata governance.** Every metadata field used in multi-domain work **MUST** be
classified as `CONDITIONING_ALLOWED` (legitimately available at inference),
`REPORTING_ONLY` (reporting only), or `FORBIDDEN_AS_INPUT` (GT-only / annotation-derived).
Kidney/Bladder/Ureteric remain `REPORTING_ONLY` ([RULES.md](RULES.md) §13).

See [ARCHITECTURE.md](ARCHITECTURE.md) §9 for the current architecture and §16 below for
the frozen v1.2 router-feature contract.

### Adaptive-routing hypothesis — `HYPOTHESIS_UNDER_TEST`

If regional refinement genuinely helps mainly where objects are small/local, an adaptive
router should **naturally activate differently by domain and by case** — more regional
compute on FULL_FIELD/small-object cases, less on ROI/large-object cases. This is a
hypothesis to test, not a result. **Phase-22 evidence already shows regional benefit is
strongly heterogeneous, and always-on regional HURTS in aggregate.**

### Multi-domain preservation principle — `FUTURE_EXPERIMENT`

Adding FiLM/regional machinery **MUST NOT** degrade per-domain performance. Phase 27 is the
preservation audit; it is a required gate, not a formality.

## 13. FUTURE causal ablation plan — `FUTURE_ABLATION_PLAN`

No ablation result exists yet. The intended high-level causal structure:

| ID | Configuration | Isolates |
|---|---|---|
| **A** | Shared Global | parameter sharing baseline |
| **B** | Global + Domain FiLM | FiLM contribution |
| **C** | Global + Regional Mechanism | regional processing contribution |
| **D** | Global + Domain FiLM + Regional Mechanism | FiLM + regional interaction |
| **E** | Global + Domain FiLM + Region/Scale FiLM | regional FiLM contribution |
| **F** | Full adaptive RA-MedFiLM-Seg++ | adaptive routing/fusion |

Purpose: separate the contribution of **parameter sharing · FiLM · regional processing ·
regional FiLM · adaptive routing/fusion**. **No winner claims before formal evidence**
(Phase 28 + Phase 31).

## 14. Pending statistics

- **Not performed.** No paired testing, confidence intervals, effect sizes, or significance
  tests on clean-v3 results.
- Still NOT performed: Phase 29 three-seed reproducibility, Phase 31 statistical
  significance. Until then, all clean-v3 numbers are **single-seed descriptive VAL
  findings** — no ranking, no winner, no significance.

## 15. HISTORICAL_v2 caveat — `HISTORICAL_PROVENANCE`

| Model | v2 best epoch | v2 VAL Dice | v2 epochs |
|---|---|---|---|
| UNet | 47 | (see v2 artifacts) | 62 |
| Attention U-Net | 77 | 0.7530131340026855 | 92 |
| UNet++ | 77 | 0.7625221610069275 | 92 |
| DeepLabV3+ | 37 | 0.7487905025482178 | 52 |

v2 used `phase4_v2` with **different** KUB TRAIN/VAL membership and
`KNOWN_SPLIT_CONTAMINATION_DISCOVERED_RETROSPECTIVELY`. Any clean-v3 vs v2 difference
**MUST NOT** be attributed solely to leakage remediation. The v2 statement "strongest
baseline is UNet++" is **historical** and is **not** a clean-v3 winner.

## 16. CURRENT EXACT IMPLEMENTATION DECISIONS — RA-MedFiLM-BARR (v1.2)

`status: FROZEN_SPECIFICATION` · `science_changed = false` · `method_changed = false`

### 16.1 Phase-24 router-feature specification, v1.2

The router consumes a **GT-free, pre-refinement** feature vector. v1.1 declared the
dimension (`202`) but left the *operation* undefined. v1.2 completes it.

**C→32 deterministic adaptive channel averaging.** Each native tap map is pooled
spatially (global mean, or ROI mean over the mapped cells) to `v ∈ R^C`, then reduced by
the frozen, non-trainable operator
`DETERMINISTIC_CHANNEL_ADAPTIVE_AVG_POOL_1D_V1`:

```
for j in 0..31:
    start_j = floor(j * C / 32)
    end_j   = ceil((j + 1) * C / 32)
    z[j]    = mean(v[start_j:end_j])
```

No trainable projection is introduced (`trainable_conv_projection_before_pooling = false`).
When `C < 32` the floor/ceil bins **overlap**; starts are monotone non-decreasing and the
bins cover `[0, C)`, using every source channel.

**Six-vector order (frozen):**
`bridge_global, bridge_roi, decoder2_global, decoder2_roi, decoder1_global, decoder1_roi`.

**Native feature widths:** bridge `= 256`, decoder2 `= 48`, decoder1 `= 24`.

**ROI→feature-map mapping (freeze).** Canvas `H = W = 512`; half-open `[x0, x1)`. For a
tap whose feature grid is `Wf × Hf`:

```
fx0 = floor(x0 * Wf / 512)   fy0 = floor(y0 * Hf / 512)
fx1 = ceil (x1 * Wf / 512)   fy1 = ceil (y1 * Hf / 512)
```

clipped to the grid; computed **per tap** (bridge 32×32, decoder2 256×256, decoder1 512×512).
Empty ROI ⇒ all-zero group.

**The ten scalar descriptors** (order frozen):
`entropy_proxy_mean` (THRESHOLD_FREE),
`frac_prob_within_0p05_of_boundary`, `frac_prob_within_0p02_of_boundary`,
`mean_boundary_margin` (all `t_seg = 0.50`),
`pred_foreground_fraction`, `pred_foreground_pixels`, `pred_roi_exists`, `pred_empty`,
`predicted_roi_area_fraction`, `predicted_roi_side` (all `t_roi = 0.30`).

**Threshold semantics — two DIFFERENT thresholds:**
`t_roi = 0.30` (ROI proposal → bbox / `action_available`; not Dice) and
`t_seg = 0.50` (segmentation output → final mask / Dice / IoU).

**Corrected `predicted_roi_area_fraction` (D1 ruling / C3).**
`w_in = max(0, min(512, x2) − max(0, x1))`, `h_in = max(0, min(512, y2) − max(0, y1))`,
`predicted_roi_area_fraction = w_in * h_in / 512²`, `float32`, range `[0, 1]`.
External padding is excluded. The old provisional `crop_side_pixels² / 512²`
(range up to `2.25`) is marked
`SUPERSEDED_PRE_EXECUTION_SPEC_FORMULA__NOT_USED_FOR_PHASE25B`.
`predicted_roi_side` retains the pre-resize square crop side separately.

**Dimensions.** 192 deep + 10 scalar = **202** numeric pre-router dims; **+16** learned
task embedding (added at Phase25D) = **218** router input.

### 16.2 BARRBenefitRouterV1 — exact architecture (SPECIFIED, NOT TRAINED)

`Embedding(4, 16)` → 218 input → `Linear(218,128)` → `LayerNorm(128)[affine=true]` →
`SiLU` → `Dropout(0.10)` → `Linear(128,64)` → `LayerNorm(64)[affine=true]` → `SiLU` →
`Dropout(0.10)` → `Linear(64,1)`. No optional harm head in the primary router.

**Total trainable parameters = 36,801.** Breakdown: task embedding `64` +
`Linear(218,128)` `27,904 + 128` + `LayerNorm(128)` `256` + `Linear(128,64)`
`8,192 + 64` + `LayerNorm(64)` `128` + `Linear(64,1)` `64 + 1`.

The historical figure **36,353 = the linear-core-only count** (`Linear(218,128)` +
`Linear(128,64)` + `Linear(64,1)`, excluding the 64 embedding and 384 affine LayerNorm
parameters). It is **not** the total trainable count. This is a **bookkeeping correction
(D2)**; the architecture is unchanged and no model has been trained.

**Router target:** OOF paired `DeltaDice` refinement gain. **Resource utility** is a
separate, explicitly-computed consideration. **Preservation / fallback role:** the global
path remains the safety net when the router says skip.

### 16.3 DESIGN DECISION HISTORY

| Revision | Decision |
|---|---|
| **v1.1** | Router feature specification **underspecified** (dimension declared, operation undefined) |
| **v1.2** | Feature semantics **completed before extraction** (RF-1 C→32 reduction; RF-2 ROI→grid mapping; RF-3 scalar + threshold roles) |
| **D1** | `predicted_roi_area_fraction` **area-fraction correction** (clipped in-canvas, `[0,1]`) |
| **D2** | Router **parameter bookkeeping correction** (36,353 = linear core; 36,801 = total trainable) |

**No result-driven tuning occurred.** No holdout outcome was inspected. `TFREE`
normalisation only touched presentation bytes.

### 16.4 BARRBenefitRouterV1 — router training specification v1.2.1 (FROZEN)

Additive specification revision `ra_medfilm_barr_router_training_v1_2_1`, frozen
**before** any router construction or training.

| Field | Frozen value |
|---|---|
| Outer CV | `BARR_ROUTER_CV5_GROUP_SAFE_DOMAIN_STRATIFIED_V1` — 5 folds, `StratifiedGroupKFold(shuffle=True, random_state=42)`, group = canonical composite `group_key`, stratify = domain only |
| Inner split | `StratifiedGroupKFold(n_splits=10, random_state=4200+k)` per outer fold; index 0 = EARLY_STOP, 1–9 = FIT |
| Checkpoint selection | lowest **EARLY_STOP mean Huber loss**; direction MINIMIZE; tie = earlier epoch wins; patience 20 |
| Target | raw `delta_dice` (float32); **no scaling, no centering, no clipping** |
| Feature normalization | 8 continuous scalars standardized (population std, ddof=0) on FIT only; 192 deep + 16 embedding untouched; constant columns → 0.0 |
| Final epoch rule | exact median of 5 best epochs: `sorted([e0,e1,e2,e3,e4])[2]` |
| Final refit seed | 42, **fresh initialization** (not from any CV checkpoint) |
| Final refit scheduler | `ReduceLROnPlateau` monitors **train Huber loss per epoch**; LR only; no validation; no early stopping; checkpoint = last fixed epoch |
| Data-loader seed | fold seed = `42000 + router_cv_fold`; resume restores all RNG states |
| OOF prediction | load best checkpoint; eval mode; predict ONCE on OUTER_TARGET_k; never modifies model/scheduler |

All other hyperparameters carried forward unchanged from Phase-24 v1.2
(§16.2 architecture, Huber δ=0.05, AdamW lr=1e-3 wd=1e-4, batch=128, max_epochs=200,
scheduler `ReduceLROnPlateau(factor=0.5, patience=8, min_lr=1e-6)`).

Blocked attempt preserved:
`reports/audits/phase25d_blocked_spec_incomplete.json`.

---

**Cross-links:** [PRD.md](PRD.md) · [ARCHITECTURE.md](ARCHITECTURE.md) ·
[RULES.md](RULES.md) · [TASKS.md](TASKS.md) · [MEMORY.md](MEMORY.md)
