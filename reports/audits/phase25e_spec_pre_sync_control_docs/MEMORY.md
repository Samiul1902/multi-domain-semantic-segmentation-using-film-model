# MEMORY — Operational Continuity Handoff

**Resume-in-5-minutes page.** Full detail: [MEMORY_ARCHIVE_pre_2026_09_30.md](MEMORY_ARCHIVE_pre_2026_09_30.md),
`.workbuddy-ai/memory/` (dated logs + `NOTES_ARCHIVE.md`), [ARCHITECTURE.md](ARCHITECTURE.md),
[DESIGN.md](DESIGN.md), [RULES.md](RULES.md), [PRD.md](PRD.md), [TASKS.md](TASKS.md).

**Last verified:** 2026-10-01 — Phase25D canonical reviewer-notebook compliance repair complete
**Method:** **RA-MedFiLM-BARR** (v1.1 architecture)

## STATUS

Phase 00–23 COMPLETE · **Phase 24 COMPLETE** · Phase 24 v1.1 historical · **Phase 24 v1.2
(router feature spec) COMPLETE** (D1+D2 adjudicated) · **Phase 25A COMPLETE canonical** ·
Phase 25A ROI-0.50 NONCANONICAL_PROTOCOL_DEVIATION (preserved only) · Phase 25B blocked
attempt BLOCKED_ATTEMPT_PROVENANCE · **Phase 25B COMPLETE canonical (202-D GT-free feature
cache frozen; handoff semantics repaired)** · **Phase 25C COMPLETE canonical (4957 OOF paired
refinement-gain labels frozen)** · **Phase 25D blocked attempt BLOCKED_ATTEMPT_PROVENANCE**
· **Phase 25D router training spec v1.2.1 COMPLETE frozen** · **Phase 25D
COMPLETE canonical** (5 CV folds + final refit + 4957 OOF predictions + notebook) · **Phase 25E
ELIGIBLE_NOT_STARTED** · Phase 25F–25G NOT_STARTED · Phase 26+ roadmap
retained · **TEST CLOSED until Phase 39.**

## TERMINAL

Scientific terminal (Phase 25C):

```
PHASE25C_OOF_PAIRED_REFINEMENT_GAIN_LABELS_COMPLETE__PHASE25D_BENEFIT_ROUTER_ELIGIBLE_NOT_STARTED
```

Historical Phase25C governance terminal (superseded):

```
PHASE25C_GOVERNANCE_CLEANUP_COMPLETE__PHASE25D_BENEFIT_ROUTER_ELIGIBLE_NOT_STARTED
```

Historical Phase25D spec-repair terminal (before accepted training):

```
PHASE25D_ROUTER_TRAINING_SPEC_V1_2_1_COMPLETE__CV_CHECKPOINT_TARGET_NORMALIZATION_AND_FINAL_REFIT_RULES_FROZEN__PHASE25D_REENTRY_ELIGIBLE_NOT_STARTED
```

Phase 25D completion terminal:

```
PHASE25D_BENEFIT_ROUTER_COMPLETE__OOF_DELTA_PREDICTIONS_AND_FINAL_ROUTER_FROZEN__PHASE25E_ELIGIBLE_NOT_STARTED
```

**Phase 25D is `COMPLETE canonical`.** 5 CV folds trained (best epochs: 37/34/139/199/80),
FINAL_ROUTER_EPOCHS = 80, 4957 OOF Delta_hat predictions frozen, final checkpoint saved.
OOF metrics: Huber 7.11e-05, MAE 0.00664, Pearson 0.300, R2 = 0.087657630443573 (≈0.088 to 3 decimals). Notebook 3x deterministic.
Blocked attempt preserved. Phase 25E is `ELIGIBLE_NOT_STARTED`.

(Superseded: `PHASE25B_HANDOFF_SEMANTICS_REPAIRED__PHASE25C_OOF_PAIRED_GAIN_LABEL_GENERATION_ELIGIBLE_NOT_STARTED`.)

## DOWNSTREAM STAGE OWNERSHIP (verified 2026-10-01; Phase25D COMPLETE canonical)

- **Phase 25C = OOF paired refinement-gain label generation — COMPLETE canonical.** Used
  fold-specific canonical ROI-0.30 refiners on untouched outer folds to compute leakage-safe OOF
  `Dice_global`, `Dice_candidate_refined`, `DeltaDice = Dice_cand - Dice_global`, and
  beneficial/harmful/neutral categories. GT used only for label creation. Did **NOT** train the
  router and did **NOT** train the task embedding. `global_model_forward_passes = 0` (Phase-25B
  global cache reused).
- **Phase 25D = benefit-router training.** Joined Phase-25B 202-D features + Phase-25C labels by
  `sample_id` and trained `BARRBenefitRouterV1` including its learned `Embedding(4,16)`
  (202 numeric + 16 task-embedding = 218 router input dims). The **16-D task embedding belongs
  to Phase 25D only.** Phase25D is **COMPLETE canonical**. It trained BARRBenefitRouterV1 and its learned Embedding(4,16).
- Phase 25C classification: `PHASE25C_EXECUTED_EVIDENCE`. Documentation/governance repair of
  Phase 25B was separately governed: `science_changed = false`, `feature_cache_changed = false`.
- **Interpretation discipline (Phase 25C).** Phase25C shows **strongly heterogeneous paired
  refinement gain**. Most samples are neutral under the pre-registered thresholds, while both
  beneficial and harmful cases exist. This heterogeneity motivates benefit-aware selective routing.
  Aggregate behaviour of earlier regional procedures belongs to prior Phase22 evidence and must not
  be conflated with the Phase25C OOF dedicated-refiner result.

## CANONICAL SHAs

- Phase25D canonical notebook: `733ff56a2b67e1427772ed49badc713c75ac309c2e8af27cbce2f604b6acfc63`
- Phase25D final checkpoint: `8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b`
- Phase25D OOF predictions: `837be08e569053676b71d1ab216ff604184b2b61df567cca45e6f8a5546d4441`
- Phase25D final history: `a5f1c8bc95da53fc8ba3cca794339a380c9354c3e4095f8fcd69a503edb39247`
- PRE_NOTEBOOK_COMPLIANCE_REPAIR_PROVENANCE = `29518fc13f3de60113e1110a12a3f38bac5f54c246751503fe29e595f6dbe997`

- Phase-25A notebook `fd2bab0168eb3477125c655ada1bd5eb4b060f41a5b354fdbaaf6fd621dfb2dd`
- Phase-25A final refiner checkpoint `6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109`
- Phase-21 global checkpoint `286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7`
- Phase-25B notebook: `acdfe90a5042ef364c5ab28ec67ecd3fe3146b30e1e5715a2631a36deb4dc38a` (3× byte-identical; pre-repair `11a1a62a…` retained as provenance)
- Phase-25B feature cache: `data_cache/phase25b_barr_pre_refinement_features_v1_2/` (4957 × 202)
- Phase-25C OOF label table: `data_cache/phase25c_barr_oof_paired_gain_labels_v1_2/phase25c_oof_paired_gain_labels.csv` `fd6ca32c33a3bddb75f986b1350d54ec35b11d3bf5cb0fdc029962a5aa94865f` (4957 rows)
- Phase-25C notebook: `564105eabfdb4cfb12613ca65cab7dc0c4410bea667239e5c1302e15060db613` (3× byte-identical; 8/8 embedded PNG valid)
- Phase-24 v1.1 provenance notebook `612d71700c1c1a45b94b8fcb8a3ff427bf32f6f6453130febeec49c6ec78caef`
- Phase-24 v1.2 notebook: `reports/audits/phase24_v1_2_notebook_determinism.json`

Costs: Global MedFiLM **3,523,001** params · BARRRegionalRefinerV1 **1,276,401** params /
**3.230663** GMAC · BARRBenefitRouterV1 **218** input dims / **36,801** trainable
params (linear core 36,353 = bookkeeping only); **TRAINED / FROZEN in Phase25D**.

## THRESHOLD SEMANTICS

```
ROI proposal        = 0.30  (bbox -> action_available / FORCED_SKIP)
segmentation output = 0.50  (final mask / Dice / IoU)
```

## HARD RULES

1. **TEST CLOSED** until Phase 39; metadata only; `test_reads = 0`.
2. **ROUTER_HOLDOUT outcomes CLOSED** until the designated one-shot evaluation.
3. **VAL808 continuity/development only** — not router training data.
4. **Never silently resolve a frozen-value conflict** — report `CHECK_REQUIRED`.
5. **Additive provenance only**; never rename/delete a frozen artifact without a migration record.
6. ROI 0.30 ≠ segmentation 0.50.
7. Router features are **pre-refinement + GT-free**; no refined features enter the router.
8. No architecture/hyperparameter change based on holdout outcomes.
9. **Blocked phase ⇒ no fake completion notebook.**
10. Completed scientific phase ⇒ **real executed notebook** (full epoch tables).
11. Incomplete specification ⇒ **STOP before execution**.
12. `RA-MedFiLM-BARR`; max novelty **Level 2**, scoped to the integrated GT-free paired-gain
    router. Forbidden: counterfactual / certified / causal / guaranteed.
13. Phase-21/22 baselines **TIED**; never write "FiLM caused +X".

## GOTCHAS

- **pandas object-dtype bool inversion** — cast to `bool` before `~` in fail-closed checks.
- **Assert artifact existence after builders** — exit code ≠ file on disk.
- **No notebook circular freeze dependency.**
- **Atomic checkpoint writes** (temp-then-rename).
- **Restore RNG on legitimate resume.**
- **Deterministic notebooks:** merge consecutive same-name `stream` outputs *before*
  normalising; also normalise `metadata.execution` + `0x…` addresses; fix Styler UUIDs.
  Never normalise scientific numeric content.
- **Harness tears down the process tree every ~2–3.5 h** — a clean log with no traceback is
  external teardown, not a crash. `tasklist` is not a liveness check.

## SEE ALSO

`reports/audits/antigravity_current_state.json` · `PROJECT_MASTER_PLAN.md` §7 ·
`notebooks/phasewise/PHASE_INDEX.md`.

**Cross-links:** [PRD.md](PRD.md) · [ARCHITECTURE.md](ARCHITECTURE.md) ·
[RULES.md](RULES.md) · [DESIGN.md](DESIGN.md) · [TASKS.md](TASKS.md)

