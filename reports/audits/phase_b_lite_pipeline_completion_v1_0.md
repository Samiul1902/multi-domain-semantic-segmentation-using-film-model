# PHASE B — Complete Lite Training Pipeline: completion report

**Artifact ID:** `PHASE_B_LITE_PIPELINE_COMPLETION_V1_0`
**Family:** `LITE` (`RA_MEDFILM_BARR_LITE_SECONDARY_V1`)
**Variant:** `depthwise_compact` (frozen primary Lite candidate)
**Status:** `LITE_DEPTHWISE_TRAINING_CODE_COMPLETE__THREE_SEED_SYNTHETIC_VERIFIED__OOF_LIMITATIONS_EXPLICIT__FULL_REGRESSIONS_PASSED__REAL_TRAINING_NOT_STARTED`
**Real training performed:** **NO** — no operator grant was requested, minted or consumed.
**TEST population reads:** 0. **ROUTER_HOLDOUT reads for labels:** 0.

> This report is the §14 deliverable of the Phase B mission. It records only what was
> executed and observed. Where a claim is not backed by an executed check it is marked
> `NOT_ESTABLISHED` rather than inferred.

---

## 1. Frozen research identity (§1) — confirmed, not re-derived

The Lite identity was read from the frozen spec and re-verified against instantiated
models in this session. It was not restated from memory.

| Component | Declared | Instantiated | Match |
|---|---|---|---|
| `G_Lite` (`depthwise_compact`) | 176,454 | 176,454 | yes |
| `R_Lite` (`LiteRegionalRefiner`) | 58,129 | 58,129 | yes |
| `B_phi` (canonical Phase-25 `BARRBenefitRouterV1`) | 36,801 | 36,801 | yes |
| `S_omega` (canonical Phase-25 `BARRPostSafetyV1`) | 1,217 | 1,217 | yes |
| **Family total** | **272,601** | **272,601** | **yes** |

**Reduction: 94.3647 %**, computed against the **FULL family total 4,837,420**
(G 3,523,001 + R 1,286,401 + B_phi 36,801 + S_omega 1,217).

**Denominator trap, recorded so it is not repeated.** Dividing 272,601 by
**3,523,001** — the FULL **G alone** — yields **92.2623 %**. That figure is wrong and
must never be published as the family reduction. Both numbers are asserted in
`tests/test_lite_pipeline.py::test_component_counts_and_reduction_denominator`, so the
wrong denominator cannot be reintroduced silently.

The two sibling variants are **not** the selected candidate and are not interchangeable:

| Variant | Parameters | Role |
|---|---|---|
| `depthwise_compact` | **272,601** | **frozen primary Lite candidate** |
| `width_compact` | 1,240,280 | sibling, not selected |
| `ultralite_depthwise_add` | 82,029 | sibling, not selected |
| `1,586,817` (Stage 1–5 report) | — | **superseded, wrong for all three variants** |

**FULL architecture unchanged.** `src/models/film/global_medfilm.py`,
`src/models/barr/ra_medfilm_barr.py` and `src/models/barr/phase25_models.py` were
**not modified**. FULL G still instantiates at 3,523,001 parameters.

---

## 2. Reuse instead of duplication (§2)

Nothing was regenerated from frozen manifests, and no canonical definition was copied.

| Concern | Decision |
|---|---|
| `B_phi`, `S_omega` | **Reused verbatim.** `MODULES["B"] = router_stage`, `MODULES["S"] = safety_stage` — the canonical FULL producers, not re-implementations. |
| G trainer | Reused; only the model is injected (`model_factory`, `expected_parameters`, `architecture_id`). |
| Cache/feature extraction | Reused; only the feature builder is injected (`feature_builder`). |
| Refiner trainer | Reused; only the model and architecture id are injected. |
| Label generation | Reused; only the refiner factory and contract provider are injected. |
| Phase-25D fold table | **Consumed as frozen.** `build_strict_folds` re-labels the primary partition; it never invents a permutation. |
| Frozen manifests | **Not touched.** `refiner_fold_manifest_sha256` / `router_fold_manifest_sha256` are read, not written. |
| Pre-existing working-tree edits | Preserved: `reports/audits/c1_r4_execution/synthetic_chain_test.json`, `scripts/analysis/run_c1_campaign_launch.py`, `paper_doc/*` renders. |

Injection points were added as **default-preserving keyword arguments**, so every
existing FULL call site is byte-identical in behaviour. This is what makes the six Lite
stage adapters ~60 lines each instead of forks.

---

## 3. The Lite training DAG (§3)

```
G_Lite ──► CACHE_Lite ──► R_Lite ──► LABELS_Lite ──► B_Lite ──► S_Lite
   │            │            │             │             │          │
 5832 TRAIN   512² taps   256² ROI     refiner-OOF   5-fold     5-fold
 4 domains    bridge/d2/d1  3 outer    +router-OOF    router      safety
              p_global      folds      +safety-OOF    cross-fit   cross-fit
```

`STAGE_ORDER = ("G", "CACHE", "R", "L", "B", "S")`, identical to FULL. Three
**independent** seed families (`42`, `123`, `3407`), each a self-contained replicate
under `runs/lite/lite_seed<seed>/`. All four domains (CVC, BrEaST, Stones, external
domains as declared by the population spec) flow through the same graph.

**No FULL G/R weights are used as Lite checkpoints.** `test_lite_checkpoint_cannot_be_loaded_as_full`
asserts the reverse guard, and `test_lite_seed_streams_do_not_collide_with_full`
asserts that all six components across all three seeds draw from disjoint seed streams
(`SeedFamily.namespace = "LITE"` vs `"FULL"`).

**Synthetic checkpoints are never reported as results.** Every synthetic run stamps
`protocol_faithful = False` / `operational_override = True`, and
`test_synthetic_runs_are_stamped_and_not_evidence` enforces it.

---

## 4. Cross-fitting contract (§4) — the load-bearing limitation

The primary construction is **deliberately identical to FULL**: refiner-OOF,
router-OOF and safety-OOF, but **backbone in-sample**. This is stated as data, not as
prose, in the `oof_contract` written by the `LABELS` stage
(`contract_version = ra_medfilm_barr_oof_contract_v2`).

Verified contract, read back from a synthetic seed-42 run:

| Field | Value |
|---|---|
| `refiner_out_of_fold` | `True` |
| `backbone_out_of_fold` | **`False`** |
| `backbone_sees_target_sample` | **`True`** |
| `router_out_of_fold` | `True` |
| `safety_out_of_fold` | `True` |
| `label_generation_population` | `ROUTER_DEVELOPMENT` |
| `label_generation_excludes_router_holdout` | `True` |
| `backbone_training_population` | `TRAIN` |
| `backbone_training_population_includes_label_population` | **`True`** |
| `validation_population_used_for_labels` | `False` |
| `test_population_reads` | `0` |
| `refiner_cross_fit_folds` / `router_cross_fit_folds` | `3` / `5` |
| `outer_target_union_equals_label_population` | `True` |
| `group_keys_respect_outer_fold_boundary` | `True` |
| `straddling_group_keys` | `[]` |
| `upstream_checkpoint_identity` | `G` sha256 + one sha256 per `R` fold, read from disk |
| `experimental_protocol_version` | `ra_medfilm_barr_matched_full_oof_v1` |
| `not_fully_oof` | `True` |
| `not_fully_oof_reason` | `backbone_in_sample: G_Lite trained on all of TRAIN, including every ROUTER_DEVELOPMENT sample …` |
| `consequence` | `delta_dice` measures what a fold-k refiner does to the output of a G that already memorised the sample |

**Language rules that follow from this** (also encoded in
`docs/phase36_hypotheses_claim_evidence_v1_0.md` §4 and §6):

- These labels **may** be called *refiner-out-of-fold*, *router-out-of-fold*,
  *safety-out-of-fold*. They **must not** be called *fully out-of-fold*.
- Absolute harm rates derived from them are **optimistic and not held-out**, because
  the backbone saw every labelling sample during its own training.
- No unbiased benefit/harm guarantee may be claimed from this construction.

The frozen FULL protocol was **not** silently altered. The contract *version* was
raised to `v2` so that any artifact carrying the old `v1` contract is distinguishable,
and the booleans are computed from the run's own fold assignment rather than asserted.

**Enforcement, not convention:** `orchestrator.verify_family` *raises* unless
`contract["backbone_out_of_fold"] is False`. A future drift toward claiming full OOF
fails chain verification instead of passing quietly.

---

## 5. Strict-OOF extension (§5) — implemented, versioned, NOT primary

`src/research/lite_pipeline/strict_oof.py`,
`STRICT_OOF_PROTOCOL_VERSION = ra_medfilm_barr_lite_strict_backbone_oof_v1`.

| Element | Implementation |
|---|---|
| Fold-aware interface | `StrictFoldRecord` — frozen dataclass, self-validating in `__post_init__` |
| Target-fold exclusion | `validate_target_exclusion` runs **four separate** checks: target ∩ backbone-fit = ∅; refiner-fit ⊆ backbone-fit; fit ∩ early-stop = ∅; refiner-fit ∩ target = ∅ |
| Checkpoint provenance | `assert_strict_checkpoint_provenance` — every backbone fold checkpoint must carry the fold it was trained on and the digest of its own fit set |
| Contract | `strict_oof_contract()` reports `is_primary: False` and the exact cost |
| Future requirement | `future_requirement()` — **9 additional backbone trainings** (3 outer folds × 3 seeds), `not_required_for_phase_b: True` |

The strict construction **does not replace** the primary one. `label_lite.lite_oof_contract`
keeps `strict_backbone_oof_is_primary: False`, and
`test_strict_oof_contract_is_declared_not_primary` asserts it.

Verified without real training: `test_strict_oof_folds_exclude_the_target_from_the_backbone`,
`test_strict_oof_rejects_a_leaky_assignment`,
`test_strict_oof_requires_checkpoint_provenance`,
`test_strict_oof_future_requirement_is_explicit`.
**No strict-OOF performance result exists and none is reported.**

---

## 6. Refiner and router completion (§6)

- **512×512 global contract / 256×256 ROI contract**: unchanged from FULL. Only the
  tap *channel counts* differ.
- **Tap contract**: `bridge` 128 ch @ 32², `decoder2` 24 ch @ 256², `decoder1` 12 ch @ 512².
  The **grid sides are identical to FULL (32 / 256 / 512)** — this is why
  `map_roi_to_grid` and `pool_roi` behave identically and only the channel reduction
  changes. `assert_lite_tap_contract` enforces the channel widths.
- **202-D router feature interface**: preserved. `build_lite_feature_vector` returns
  `float32[202]`; `lite_feature_builder` wraps it with the architecture assertion.
  The frozen `DETERMINISTIC_CHANNEL_ADAPTIVE_AVG_POOL_1D_V1` maps any C → 32, so the
  frozen 202-D definition is untouched.
- **The frozen FULL extractor still refuses Lite taps** — it asserts FULL widths
  256/48/24. This guard was **not** relaxed;
  `test_frozen_full_feature_extractor_still_refuses_lite_taps` pins it.
- **Normalisation is NOT inherited from FULL.** It is fitted on FIT rows only, per
  fold, inside `B`. `test_router_normalisation_is_fitted_per_lite_family` asserts each
  family's μ is non-zero and that seed 42's μ ≠ seed 123's μ — i.e. no FULL statistic
  leaked in.
- **Exact resume.** A genuine defect was found and repaired here — see §9, defect D-1.

---

## 7. Post-refinement safety (§7)

`S_omega` is the **canonical** `BARRPostSafetyV1` producer, unchanged. **No FULL safety
checkpoint was reused, transferred or fine-tuned.** The Lite safety module is trained
from fresh initialisation on this family's own labels
(`test_safety_labels_and_features_are_family_derived`).

`SOMEGA_ACCEPT_THRESHOLD = 0.50` is unchanged and distinct from
`ROI_PROPOSAL_THRESHOLD = 0.30` and `SEGMENTATION_OUTPUT_THRESHOLD = 0.50`.
The refiner still runs **before** the `S_omega` gate, so `refiner_forwards == selected`
and a rejected candidate has already paid its compute.

---

## 8. Teacher distillation (§8) — policy only

Distillation is **OPTIONAL and not required**. **No distillation experiment was run.**
No teacher checkpoint was loaded, no teacher-student loss was constructed, and no
distillation hyper-parameter was introduced. `D:\Softfors\teacher_student` was not
touched — it remains a protected **path**, not a model.

---

## 9. Defects found and repaired during Phase B

| ID | Defect | Scope | Disposition |
|---|---|---|---|
| **D-1** | **Resume was not exact for the canonical `B_phi` / `S_omega` producers.** The shuffled `DataLoader` drew from a standalone `torch.Generator` that `capture_rng()` never captured, so a resumed run re-drew epoch 1's permutation for epoch 2. Observed: `train_huber` epoch 1 matched, epoch 2 diverged (0.0053 vs 0.0084). | **Canonical FULL producers**, not Lite-only | Fixed in `router_stage.py` and `safety_stage.py`: the generator state is written into the envelope as `data_order_generator_state` and restored on resume; a checkpoint lacking it now raises `checkpoint has no data-order generator state; an exact resume is not possible from it` instead of resuming wrongly. Verified: `train_huber` now matches to 1e-12. |
| **D-2** | **Architecture digest read from the wrong level.** `global_stage` / `refiner_stage` stamp `architecture_sha256` inside `recipe["g"]` / `recipe["r"]`, but `cache_lite` read it at envelope top level, raising `G checkpoint architecture digest does not match the variant spec`. | Lite adapter | Fixed by a single authoritative accessor `recipe.checkpoint_architecture_sha256(ck, block=...)`, used by `cache_lite`, `inference.LiteBundle.load` and `orchestrator.verify_family`. |
| **D-3** | **Pre-existing: `tests/test_barr_m1_v1_0d_repaired.py` left a module-level symbol named `test`** in three parametrisation loops. Pytest collected it as a test and failed at setup with `fixture 'self' not found`, so the error masked nothing but polluted the suite. | Test hygiene | Helpers renamed (`_config_case`, `_path_case`, `_interruption_case`). The `setattr`-bound `test_config_*` / `test_path_*` / `test_interruption_*` methods are unchanged and all 33 still pass. |
| **D-4** | **Pre-existing: `tests/test_kub_localizer.py::test_gt_free_proposal_api` built a 64×64 heatmap** while `extract_predicted_components` reads the map as 512-space and rescales by `512 // h_map`. The blob was lifted to rows 80–119 and dropped by the visibility guard, returning 0 proposals. Same defect class as commit `d597715`, one file over. | Test fixture | Fixture rebuilt in 512 space with matching metadata. Production code untouched — it is correct for its documented contract. |
| **D-5** | **Pre-existing: `tests/test_phase14_part1.py::test_geometry_and_resize` asserted `val_ds.margin == 0.20`.** `RegionalCropDataset` defaults to `ORACLE_DERIVED_REFINER_MARGIN = 0.25`, which the module documents as governing TRAIN and crop-level VAL crop construction and as deliberately *not* shared with the 0.20 predicted-proposal margin. | Test assertion | Now asserts against the named constant, plus `!= PREDICTED_PROPOSAL_MARGIN`. Authority: `reports/audits/phase14_roi_margin_role_resolution.json`, status `RESOLVED_BY_FROZEN_CORPUS`, `ORACLE_DERIVED_REFINER_VAL_MARGIN = 0.25`. **No scientific parameter was changed.** |

**D-3, D-4 and D-5 pre-date Phase B** — the four files involved are byte-identical to
`HEAD` before this task (`git diff --stat HEAD` empty for each). They were surfaced by
the mandated full-suite run and repaired because the implementation is provably correct
for its contract in each case. **No production code was changed to make a test pass.**

---

## 10. GT-free end-to-end inference (§9)

`src/research/lite_pipeline/inference.py` builds a `LiteBundle` from the four
**LITE-family** checkpoints and constructs
`GTFreeBARRInference(..., feature_builder=lite_feature_builder, uses_tap_forward=True)`.

| Requirement | Evidence |
|---|---|
| All four branches execute | `test_all_four_inference_branches_execute` |
| All four domains | covered by the branch harness across the population's domain set |
| No GT mask, no oracle feature | `test_inference_uses_only_image_and_task_id` — the signature accepts image + task id only |
| Own normalisers only | `test_lite_inference_reads_its_own_normalisers` — μ/σ read from this family's `B`/`S` checkpoints |
| GT-free audit | `audit_lite_gt_free` returns `GT_used_for_inference: False` |
| Export is reproducible | `test_synthetic_export_is_reproducible` — byte-identical across two exports |
| Export carries no timestamp or path | `test_export_record_carries_no_timestamp_or_path` |
| Corrupt / missing / wrong-architecture checkpoints refused | three dedicated tests |

**CPU/CUDA consistency** (measured, not assumed). Max |Δ| alone is a misleading gate:
it is a thin tail of a few pixels near the 0.50 boundary where a 1-ULP kernel
difference is amplified by the step function. The gate therefore asserts, for all four
tasks, with autocast **both on and off**:

| Task | `state_match` | binary agreement (fp32) | mean \|Δ\| (fp32) | max \|Δ\| (fp32) | binary agreement (autocast) | mean \|Δ\| (autocast) | max \|Δ\| (autocast) |
|---|---|---|---|---|---|---|---|
| 0 | exact | 0.99979 | 7.83e-05 | 2.12e-03 | 0.99814 | 5.55e-04 | 1.56e-02 |
| 1 | exact | 0.99977 | 7.54e-05 | 2.32e-03 | 0.99803 | 5.26e-04 | 1.15e-02 |
| 2 | exact | 0.99975 | 8.13e-05 | 1.91e-03 | 0.99797 | 5.75e-04 | 1.50e-02 |
| 3 | exact | 0.99975 | 7.30e-05 | 1.78e-03 | 0.99813 | 4.89e-04 | 2.02e-02 |

Gate: exact state match, binary agreement > 0.99, mean |Δ| < 2e-3, router score < 1e-3.
Raw measurements are written to `runs/lite_synthetic_test_<pid>/cpu_cuda_agreement.json`.
The measurements were **bit-identical across three independent runs**, which also
confirms the determinism settings are effective.

**CUDA memory, measured on the RTX 3060 Ti (8,191.375 MiB total, torch 2.6.0+cu124):**

| Phase | Peak allocated |
|---|---|
| `G_Lite` forward+backward | **1,620.79 MiB** |
| `R_Lite` forward+backward | **342.35 MiB** |

Both leave substantial headroom; the Lite family is not memory-bound on this device.

---

## 11. Stage 6 comparison registry (§10)

`src/research/stage6/matrix.py` now names the real producer for the `LITE` row:

```python
LITE: {"role": "SECONDARY_PROPOSED",
       "chain": ("G", "R_psi", "B_phi", "S_omega"),
       "producer": "src/research/lite_pipeline/ (G_Lite -> CACHE_Lite -> R_Lite -> "
                   "LABELS_Lite -> B_phi -> S_omega; CLI scripts/training/"
                   "lite_barr_three_seed.py)",
       "multi_seed_producer": "AVAILABLE_NOT_EXECUTED: … no Lite cell can be completed",
       "expected_parameters": 272601,
       "evidence_status": "NO_LITE_RESULT_EXISTS"}
```

**All 24 cells remain `MISSING`.** No cell was marked complete. No cell can be marked
complete, because no protocol-compliant Lite artifact exists — the three-seed DAG has
run on synthetic data only. `test_stage6_registry_keeps_all_24_cells_missing` and
`test_stage6_aggregate_reports_no_completed_lite_cell` pin this, including that the
FULL and GLOBAL rows are untouched.

---

## 12. CLI and the 14 mandatory verifications (§11)

`scripts/training/lite_barr_three_seed.py` →
`src/research/lite_pipeline/cli.py`:

```
prepare · validate · plan · dry-run · run · resume · export · verify-family
```

`run` and `resume` are gated on `--grant-provider` and route through the **existing**
`authorize_full_training(contract)` surface. **No authorization system was bypassed,
weakened or modified, and no credential was minted.**

| # | Verification | Result | Test |
|---|---|---|---|
| 1 | Complete graph instantiates at the frozen parameter count | PASS | `test_complete_graph_has_the_frozen_parameter_count` |
| 2 | Component counts and the reduction denominator | PASS | `test_component_counts_and_reduction_denominator` |
| 3 | Selected variant is `depthwise_compact`, not a sibling | PASS | `test_variant_is_depthwise_compact_and_not_a_sibling` |
| 4 | G / R are the Lite architectures; B / S are the canonical Phase-25 classes | PASS | `test_global_architecture_is_the_lite_backbone`, `test_refiner_architecture_is_the_lite_refiner`, `test_router_and_safety_are_the_canonical_phase25_models` |
| 5 | Three seed families are isolated; no cross-seed weight sharing; no FULL/Lite stream collision | PASS | `test_three_seed_families_are_isolated`, `test_no_cross_seed_weight_sharing`, `test_lite_seed_streams_do_not_collide_with_full` |
| 6 | Family and architecture identity stamped into every checkpoint | PASS | `test_family_identity_is_stamped_into_every_checkpoint`, `test_architecture_identity_is_stamped_into_g_and_r` |
| 7 | Refiner folds disjoint and complete; labels produced by the fold-specific refiner | PASS | `test_refiner_fold_membership_is_disjoint_and_complete`, `test_oof_labels_were_produced_by_the_fold_specific_refiner` |
| 8 | Label population = ROUTER_DEVELOPMENT; paired-gain rule frozen | PASS | `test_label_population_equals_router_development`, `test_paired_gain_labels_follow_the_frozen_rule` |
| 9 | Router features 202-D and finite; router trained on *this* family's labels; normalisation per family | PASS | three dedicated tests |
| 10 | OOF contract declares the backbone in-sample and records fold/upstream identity | PASS | `test_oof_contract_declares_the_backbone_is_in_sample`, `test_oof_contract_records_fold_and_upstream_identity` |
| 11 | Strict-OOF declared, not primary; folds exclude the target; leaky assignment refused; provenance required | PASS | four dedicated tests |
| 12 | DAG matches the declared edges; plan reports every stage complete; full chain verifies | PASS | `test_dependency_graph_is_the_declared_dag`, `test_plan_reports_every_stage_complete`, `test_full_family_chain_verifies` |
| 13 | Cross-family guards: Lite ckpt refused as FULL; router refused another seed's refiner; resume exact | PASS | `test_lite_checkpoint_cannot_be_loaded_as_full`, `test_router_cannot_consume_another_seed_s_refiner`, `test_router_resume_is_exact` |
| 14 | GT-free inference, CUDA memory and CPU/CUDA agreement, export reproducibility, refusal paths, authorization | PASS | nine dedicated tests |

**Lite suite: 53 passed.** Synthetic seed-42 dry run reaches `DRY RUN PASS` with
`LITE_FAMILY_CHAIN_VERIFIED`.

---

## 13. Documentation (§12)

`docs/phase36_hypotheses_claim_evidence_v1_0.md` (new, tracked) is now the
**authoritative** home for H1–H7 and the claim-to-evidence classification:

- five evidence classes: `IMPLEMENTATION_COMPLETE`, `TECHNICAL_VERIFICATION_PASSED`,
  `SCIENTIFIC_DESIGN_SUPPORTED`, `FUTURE_EVIDENCE_PENDING`, `UNRESOLVED_DEFECT`;
- H1–H7 table with an explicit falsification criterion per hypothesis;
- §2.1 records the H7 arithmetic **including the 92.26 % denominator trap** and the
  `1,586,817` figure as superseded;
- §3 a twelve-row claim-to-evidence matrix;
- §4 the standing OOF limitation; §5 the strict extension; §6 language rules;
- §7 change control.

`reports/audits/stages1_to5_completion_review.md` §2.3 now carries a
**"Superseded as a source of truth"** banner pointing at the new spec. The manuscript
was **not** rewritten.

---

## 14. Regression verification (§13)

Every suite below was executed with
`D:\Softfors\jup\.venv\Scripts\python.exe -m pytest … -q -p no:cacheprovider`.
No test was excluded, deselected or skipped to obtain a green result.

| Suite | Command scope | Result |
|---|---|---|
| Lite pipeline (new) | `tests/test_lite_pipeline.py` | **53 passed** |
| FULL + drift + Lite model + Lite evaluation | `test_full_pipeline.py`, `test_phase25_architecture_drift.py`, `test_ra_medfilm_barr_lite.py`, `test_lite_evaluation.py` | **53 passed** |
| Stage 6 + ROI | `test_stage6_integration.py`, `test_stage6_baselines.py`, `test_predicted_roi.py`, `test_oracle_roi.py` | **60 passed** |
| Manuscript evidence + exports | `test_c1_external_evidence.py`, `test_paper_assets.py`, `test_c1_stats_and_exports.py`, `test_c1_external_final_corrections.py` | **101 passed** |
| Dataset / ROI / manifest / registry | `test_kub_dataset.py`, `test_kub_localizer.py`, `test_kub_predict.py`, `test_manifest_guard.py`, `test_experiment_registry.py` | **36 passed** (was 35 + 1 failed before D-4) |
| **Complete suite** | `pytest tests/` | **1040 tests — 1 failed, 0 errors, 1 skipped (xfail)** |

Machine-readable record: `runs/pytest_phaseB_junit.xml`. The single failure is the
pre-existing, environment-dependent RC2 trust-store test documented in §14.1; the
single skip is `test_c1_rc4_launch_path_review::test_known_gap_attacker_store_under_programdata_with_plausible_names`,
an `xfail` that records a **known, declared** governance gap and is not a Phase B
regression.

No failure is hidden by exclusion: the four failures that existed at the start of this
verification pass were all reproduced individually with full tracebacks, root-caused,
and are accounted for — three repaired (§9 D-3…D-5), one deliberately left standing
(§14.1).

### 14.1 Pre-existing failure deliberately NOT repaired

`tests/test_c1_launch_rc2.py::ProductionUnprovisionedTests::test_default_production_store_is_absent`

- **Expects** `C1_RC2_TRUST_STORE_MISSING_OR_SYMLINK`.
- **Observes** `C1_RC2_SIGNATURE_KEY_UNTRUSTED`.
- **Root cause:** the test's premise is that the production trust store is absent. On
  this host it is **not**: `%ProgramData%\InstitutionalC1Trust` exists and contains
  `c1_rc2_binding.json`, `c1_rc3_host_clock_attestation.json` and `policy.json`
  (2026-10-30). The gate therefore passes the `is_dir()` check, proceeds to key
  verification, and refuses one stage later for a different — and correct — reason.
- **Disposition: `ENVIRONMENT_DEPENDENT_PRE_EXISTING_FAILURE`, not repaired.**
  Rewriting the assertion to accept the second code would silently erase a real
  governance fact about this host. The store is a protected legacy artifact and was
  **not** modified. This failure is a property of the host's trust-store state, not of
  Phase B.

---

## 15. What is and is not established

| Claim | Status |
|---|---|
| The Lite pipeline is code-complete for all six stages, three seeds, four domains | `IMPLEMENTATION_COMPLETE` |
| It runs end-to-end on synthetic data and the chain verifies | `TECHNICAL_VERIFICATION_PASSED` |
| The OOF limitation is declared mechanically and cannot silently drift | `TECHNICAL_VERIFICATION_PASSED` |
| Lite achieves any particular Dice or efficiency benefit | **`NOT_ESTABLISHED`** — no real training has run |
| The strict backbone-OOF construction is validated end-to-end | `FUTURE_EVIDENCE_PENDING` — 9 additional backbone trainings owed |
| Teacher distillation helps | **`NOT_ESTABLISHED`** — no experiment run, none required |
| C1 / C2 / C3 scientific claims | **`NOT_ESTABLISHED`** (unchanged from the Stage 1–5 reconciliation) |

---

## 16. Changed files

### New (Phase B, task-owned)

| Path | Lines | Role |
|---|---|---|
| `src/research/lite_pipeline/__init__.py` | 33 | package surface |
| `src/research/lite_pipeline/recipe.py` | 232 | frozen Lite identity; single architecture-digest accessor |
| `src/research/lite_pipeline/context.py` | 135 | `LiteRunContext`, seed families, artifact layout |
| `src/research/lite_pipeline/features.py` | 120 | tap-contract assertion + 202-D builder |
| `src/research/lite_pipeline/strict_oof.py` | 303 | versioned strict-OOF extension |
| `src/research/lite_pipeline/orchestrator.py` | 394 | six-node DAG, chain verification, authorization surface |
| `src/research/lite_pipeline/inference.py` | 227 | `LiteBundle`, GT-free inference, export |
| `src/research/lite_pipeline/cli.py` | 358 | eight subcommands |
| `src/research/lite_pipeline/stages/__init__.py` | 56 | `MODULES` mapping (B/S = canonical) |
| `src/research/lite_pipeline/stages/global_lite.py` | 99 | `G_LITE` |
| `src/research/lite_pipeline/stages/cache_lite.py` | 78 | `CACHE_LITE` |
| `src/research/lite_pipeline/stages/refiner_lite.py` | 60 | `R_LITE` |
| `src/research/lite_pipeline/stages/label_lite.py` | 100 | `LABELS_LITE` |
| `scripts/training/lite_barr_three_seed.py` | 38 | CLI shell |
| `tests/test_lite_pipeline.py` | 956 | 53 tests |
| `docs/phase36_hypotheses_claim_evidence_v1_0.md` | 194 | authoritative H1–H7 home |

### Modified (default-preserving parameterisation)

| Path | Δ |
|---|---|
| `src/research/full_pipeline/context.py` | +13 / −2 |
| `src/research/full_pipeline/provenance.py` | +28 / −6 |
| `src/research/full_pipeline/recipe.py` | +7 |
| `src/research/full_pipeline/seeds.py` | +18 / −6 |
| `src/research/full_pipeline/stages/cache_stage.py` | +17 / −5 |
| `src/research/full_pipeline/stages/global_stage.py` | +24 / −8 |
| `src/research/full_pipeline/stages/label_stage.py` | +73 / −8 |
| `src/research/full_pipeline/stages/refiner_stage.py` | +43 / −11 |
| `src/research/full_pipeline/stages/router_stage.py` | +22 / −4 |
| `src/research/full_pipeline/stages/safety_stage.py` | +19 / −3 |
| `src/research/stage6/matrix.py` | +11 / −2 |

### Modified (regression-suite repairs, §9 D-3…D-5)

`tests/test_barr_m1_v1_0d_repaired.py`, `tests/test_kub_localizer.py`,
`tests/test_phase14_part1.py`.

### Explicitly NOT changed

`src/models/film/global_medfilm.py`, `src/models/barr/ra_medfilm_barr.py`,
`src/models/barr/phase25_models.py`, `src/models/lite/ra_medfilm_barr_lite.py`,
any frozen manifest, `D:\Softfors\teacher_student`, the C1 trust stores.

### Explicitly NOT committed

Model weights, `runs/` (including every `lite_synthetic_test_*` directory and the
JUnit XML), temporary caches, generated paper renders, the two pre-existing
working-tree edits, and any altered frozen evidence.

---

## 17. Git

| | |
|---|---|
| Parent commit | `c815566ed784a90524d09f7ff06bdd9b049d1e17` |
| **Phase B feature commit** | **`613b826`** — `lite_pipeline: complete the three-seed Lite training DAG (Phase B)` — 27 files, +3,615 / −48 |
| **Regression-suite repair commit** | **`496c8d6`** — `tests: repair three pre-existing suite defects found during Phase B verification` — 3 files, +31 / −11 |

Both commits are ancestors of `HEAD`; the complete-suite result in §14 was produced
against exactly this tree.

**Not committed, by design:** model weights, every `runs/` artifact (including
`lite_synthetic_test_*` and the JUnit XML), temporary caches, generated `paper_doc/`
renders, and the two pre-existing working-tree edits
(`reports/audits/c1_r4_execution/synthetic_chain_test.json`,
`scripts/analysis/run_c1_campaign_launch.py`), which are untouched and remain
uncommitted so their provenance is not silently absorbed into this task.
