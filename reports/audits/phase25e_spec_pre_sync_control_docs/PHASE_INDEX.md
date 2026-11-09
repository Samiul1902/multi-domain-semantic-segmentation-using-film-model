# PHASE_INDEX — Phasewise Notebook Registry and Naming Governance

**Last verified:** 2026-10-01 — Phase25D canonical reviewer-notebook compliance repair complete
**Method name:** RA-MedFiLM-BARR

This index is the single entry point for "which notebook is canonical for which phase,
and what is its exact SHA". It intentionally **does not** rename any frozen artifact —
historical path + SHA remain part of provenance. Preferred future names are recorded here
only.

---

## 1. Canonical / frozen notebooks

Terminal strings record each phase's historical completion boundary; current state is in the Status column and current-focus text.

| Phase | Subphase | Purpose | Canonical notebook path | Canonical notebook SHA-256 | Status | Class | Supersedes | Terminal | TEST reads | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 21 | Global MedFiLM | FiLM-conditioned shared global model | `notebooks/phasewise/phase_21_global_medfilm/phase21_global_medfilm_reference.ipynb` | `e7fadc7c…` (see `reports/audits/` for full SHA) | COMPLETE | Canonical | — | — | 0 | ckpt `286689fd…`; 3,523,001 params |
| 22 | Resource gap | Multi-domain scale / regional gap analysis | `notebooks/phasewise/phase_22_resource_gap/phase22_resource_gap_analysis.ipynb` | `cca76123…` | COMPLETE | Canonical | — | — | 0 | benefit strongly heterogeneous; always-on regional HURTS in aggregate |
| 23 | Literature & novelty | Methodological novelty audit | `notebooks/phasewise/phase_23_literature_novelty/phase23_literature_methodological_novelty_audit.ipynb` | `e9f78cce…` | COMPLETE | Canonical | — | — | 0 | max novelty = Level 2 |
| 24 | v1.1 exact-spec freeze | Frozen exact implementation specification | `notebooks/phasewise/phase_24_architecture_spec/phase24_narrowed_benefit_aware_refinement_spec__v1_1_provenance.ipynb` | `612d71700c1c1a45b94b8fcb8a3ff427bf32f6f6453130febeec49c6ec78caef` | COMPLETE | **Historical provenance** | superseded by v1.2 | `PHASE24_SPEC_COMPLETENESS_REPAIR_COMPLETE…` | 0 | **NEVER RENAME**; v1.1 router features underspecified |
| 24 | **v1.2 router feature spec** | Router input contract completion (RF-1/2/3 + D1/D2) | `notebooks/phasewise/phase_24_architecture_spec/phase24_narrowed_benefit_aware_refinement_spec.ipynb` | `9d62384e8afa2f35e985eac219711df0334fbfe72c33c0edd29ff3f4897d4027` | **COMPLETE** | **Canonical** | supersedes v1.1 | `PHASE24_V1_2_FULLY_CLOSED__PROJECT_DOCS_AND_PHASEWISE_INDEX_SYNCED__PHASE25B_REENTRY_ELIGIBLE_NOT_STARTED` | 0 | 3× byte-identical; pre-closure SHA `97f0efd99a9be662b2c5ba2338132b70131e07ddb01eec58eac2b80295adddff` retained as provenance |
| 25A | Dedicated regional refiner | Crop-trained `R_psi` (`BARRRegionalRefinerV1`) | `notebooks/phasewise/phase_25a_regional_refiner/phase25a_dedicated_regional_refiner.ipynb` | `fd2bab0168eb3477125c655ada1bd5eb4b060f41a5b354fdbaaf6fd621dfb2dd` | **COMPLETE_CANONICAL** | **Canonical** | supersedes ROI-0.50 run | `PHASE25A_CANONICAL_RERUN_COMPLETE__ROI_PROPOSAL_THRESHOLD_0P30__SEGMENTATION_OUTPUT_THRESHOLD_0P50__PHASE25B_ELIGIBLE_NOT_STARTED` | 0 | ckpt `6d28608a…`; 1,276,401 params; 3.230663 GMAC |
| 25A | ROI-0.50 run | First Phase-25A execution at ROI threshold 0.50 | `notebooks/phasewise/phase_25a_regional_refiner/phase25a_dedicated_regional_refiner.ipynb` (historical content, SHA `7dfcf505…`) | `7dfcf50540ee531e330c0338ea9326cdb73c24c9f8254b920c022598dd74733f` | **NONCANONICAL_PROTOCOL_DEVIATION** | **Historical / forbidden for science** | superseded by canonical | — | 0 | scientific use **FORBIDDEN**; preserved per `phase25a_roi050_supersession.json` |
| 25B | GT-free pre-refinement features | Router feature extraction (202-D, GT-free) | `notebooks/phasewise/phase_25b_gt_free_features/phase25b_gt_free_pre_refinement_features.ipynb` | `acdfe90a5042ef364c5ab28ec67ecd3fe3146b30e1e5715a2631a36deb4dc38a` | **COMPLETE_CANONICAL** | **Canonical** | supersedes blocked attempt | `PHASE25B_HANDOFF_SEMANTICS_REPAIRED__PHASE25C_OOF_PAIRED_GAIN_LABEL_GENERATION_ELIGIBLE_NOT_STARTED` | 0 | 202-D cache frozen (4957 × 202); global equivalence max_abs = 0.0; 3× byte-identical; handoff semantics repaired (pre-repair SHA `11a1a62a…` retained as provenance) |
| 25C | OOF paired-gain labels | Leakage-safe OOF paired refinement-gain label generation | `notebooks/phasewise/phase_25c_paired_gain_labels/phase25c_oof_paired_refinement_gain.ipynb` | `564105eabfdb4cfb12613ca65cab7dc0c4410bea667239e5c1302e15060db613` | **COMPLETE_CANONICAL** | **Canonical** | — | `PHASE25C_OOF_PAIRED_REFINEMENT_GAIN_LABELS_COMPLETE__PHASE25D_BENEFIT_ROUTER_ELIGIBLE_NOT_STARTED` | 0 | 4957 OOF rows (BENEFICIAL 282 / NEUTRAL 4340 / HARMFUL 335); label CSV `fd6ca32c…`; 3× byte-identical; 8/8 embedded PNG valid; `global_model_forward_passes = 0` |
| **25D** | **Benefit router training** | `BARRBenefitRouterV1` 5-fold CV + final refit | `notebooks/phasewise/phase_25d_benefit_router/phase25d_benefit_router.ipynb` | `733ff56a2b67e1427772ed49badc713c75ac309c2e8af27cbce2f604b6acfc63` | **COMPLETE_CANONICAL** | **Canonical** | — | `PHASE25D_BENEFIT_ROUTER_COMPLETE__OOF_DELTA_PREDICTIONS_AND_FINAL_ROUTER_FROZEN__PHASE25E_ELIGIBLE_NOT_STARTED` | 0 | 5 CV folds (best epochs 37/34/139/199/80); final refit 80 epochs; 4957 OOF predictions; 3× byte-identical notebook |

> **Row 25B is now COMPLETE.** The canonical 202-D GT-free feature cache is frozen at
> `data_cache/phase25b_barr_pre_refinement_features_v1_2/`, the reviewer notebook is
> 3× byte-identical, and every scope/lock gate passes. Post-phase handoff semantics were
> repaired (documentation/governance only — no science, cache, or model change):
> **Phase 25C = OOF paired refinement-gain label generation**; **Phase 25D = benefit-router
> training** (owner of the 16-D task embedding and of `BARRBenefitRouterV1`). The Phase 25B
> notebook file was **not** renamed.

> **Row 25C is now COMPLETE canonical.** The canonical `ROUTER_DEVELOPMENT` OOF paired
> refinement-gain label table is frozen at
> `data_cache/phase25c_barr_oof_paired_gain_labels_v1_2/phase25c_oof_paired_gain_labels.csv`
> (4957 rows, SHA `fd6ca32c…`). Labels come from **fold-specific** ROI-0.30 refiners applied to
> outer folds entirely excluded from their own fitting (cross-fit leakage audit CLEAN);
> `global_model_forward_passes = 0` (Phase-25B global cache reused). Phase 25C created **labels
> only** — no router training, no 16-D task embedding, `test_reads = 0`.
> At Phase25C completion, Phase25D was eligible/not-started and no Phase25D notebook yet existed.
> Phase25D has since completed canonically. Phase25E is **ELIGIBLE_NOT_STARTED**.

PRE_NOTEBOOK_COMPLIANCE_REPAIR_PROVENANCE = `29518fc13f3de60113e1110a12a3f38bac5f54c246751503fe29e595f6dbe997`

The original notebook is preserved at `reports/audits/phase25d_notebook_compliance_pre_repair.ipynb`.
The original scientific freeze is unchanged; the notebook migration is bound by
`reports/audits/phase25d_final_freeze_notebook_compliance_addendum.json`.

---

## 2. Blocked / provenance-only attempts

| Phase | Attempt | Canonical notebook | Status | Reason |
|---|---|---|---|---|
| 25B | First entry (pre-repair) | **NONE** | `BLOCKED_ATTEMPT_PROVENANCE` | frozen feature specification incomplete (RF-1/RF-2/RF-3); preserved at `reports/audits/phase25b_blocked_attempt_final_freeze.json` |
| 25A | ROI-0.50 execution | historical content of the 25A path | `NONCANONICAL_PROTOCOL_DEVIATION` | ROI threshold 0.50 ≠ frozen 0.30 |
| 25D | First entry (pre-repair) | **NONE** | `BLOCKED_ATTEMPT_PROVENANCE` | frozen router-training spec incomplete (cv_fold_assignment_algorithm, cv_inner_split_rule, checkpoint_selection_rule, target_scaling_semantics, final_refit_scheduler_semantics); preserved at `reports/audits/phase25d_blocked_spec_incomplete.json` |

---

## 3. Future canonical organization (preferred names — NOT applied retroactively)

These directory names are the **preferred future convention**. They are declared here for
forward consistency; **no existing frozen notebook is renamed** to match them.

```
phase_24_architecture_spec/
  phase24_narrowed_benefit_aware_refinement_spec.ipynb          # v1.2 canonical
  phase24_narrowed_benefit_aware_refinement_spec__v1_1_provenance.ipynb

phase_25a_regional_refiner/
  phase25a_dedicated_regional_refiner.ipynb                     # canonical

phase_25b_gt_free_features/
  phase25b_gt_free_pre_refinement_features.ipynb                # canonical (202-D, GT-free)

phase_25c_paired_gain_labels/
  phase25c_oof_paired_refinement_gain.ipynb                     # canonical

phase_25d_benefit_router/
  phase25d_benefit_router.ipynb                                 # canonical
  # Phase25D first entry: BLOCKED_PRE_MODEL_CONSTRUCTION (router training spec incomplete)
  # Historical after spec repair v1.2.1, before training: REENTRY_ELIGIBLE_NOT_STARTED
  # Current: COMPLETE_CANONICAL / TRAINED / FROZEN
  # After execution: COMPLETE canonical

phase_25e_resource_gate/
  phase25e_resource_aware_pre_gate.ipynb                        # ELIGIBLE_NOT_STARTED; NOT YET CREATED

phase_25f_preservation_fusion/
  phase25f_post_safety_and_fusion.ipynb                         # NOT YET CREATED

phase_25g_controlled_validation/
  phase25g_controlled_validation.ipynb                          # NOT YET CREATED
```

**No empty future `.ipynb` files have been created.** A Phase-25x notebook is created only
when that subphase actually executes.

---

## 4. Immutability notice

The following canonical paths are **frozen and MUST NOT be renamed or deleted**:

- Phase-21 notebook · Phase-22 notebook · Phase-23 notebook
- Phase-24 v1.1 provenance notebook · Phase-24 v1.2 notebook
- Phase-25A canonical notebook · Phase-25A ROI-0.50 superseded reference
- **Phase-25B canonical notebook** (`acdfe90a…`)
- **Phase-25C canonical notebook** (`564105ea…`)
- **Phase-25D canonical notebook** (`phase25d_benefit_router.ipynb`) — SHA-256 `733ff56a2b67e1427772ed49badc713c75ac309c2e8af27cbce2f604b6acfc63`

The list above covers every frozen notebook from Phase 21 through Phase 25D. If a filename is
aesthetically inconsistent with §3, the preferred convention is recorded here rather than applied
physically.

---

**Cross-links:** [../../docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md) ·
[../../docs/TASKS.md](../../docs/TASKS.md) · [README.md](README.md)
