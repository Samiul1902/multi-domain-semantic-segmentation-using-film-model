# Project NOTES ARCHIVE — D:\Softfors\jup

Non-injected companion to `MEMORY.md` (which is capped at ~3 KB and truncates). This file holds the full
curated detail. Per-round chronology: `.workbuddy-ai/memory/YYYY-MM-DD.md` (append-only).

## PHASE 25A — dedicated crop-trained regional refiner (COMPLETE)
Terminal **`PHASE25A_DEDICATED_REGIONAL_REFINER_COMPLETE__PHASE25B_ELIGIBLE_NOT_STARTED`**; final freeze
**25/25 PASS**; entry gate 22/22; architecture gate 42/42 → `PHASE25A_REFINER_ARCHITECTURE_FROZEN`.
Only `R_psi` was trained: NO router, NO paired-gain/DeltaDice labels, NO holdout-outcome inspection,
NO VAL evaluation, NO TEST access, NO 25B–25G.
- `BARRRegionalRefinerV1` = **1,276,401 params** (closed form == measured), 4-ch in → 1 logit, 256×256 out,
  channels `(16,32,64,96,128)`, GroupNorm ≤8, SiLU, bias=False (head bias=True). Ceiling 2.0M.
  `[16,32,64,128,192]` = 2,317,553 REJECTED. Forward takes NO task id.
- ROI (GT-independent, proven): threshold **0.5** (lower-inclusive float32) → tight bbox → 1.50×
  centre-preserving (margin 0.25) → clip → square pad → RGB/p_global crop → 256×256
  (bilinear, bilinear, nearest); `FORCED_SKIP` on empty. **DISCREPANCY (reported, not silently repaired):**
  the v1.1 artifact records `roi.predicted_foreground_threshold = 0.30` (Phase-13 `ProposalConfig`
  carry-over); 0.5 is canonical (`src/analysis/phase22_common.py:54`) and is what is BOUND. 0.30 = SUPERSEDED.
- Cross-fit: 3 outer folds (1657 / 1652 / 1648) + nested 90/10 FIT/EARLY_STOP (336 / 330 / 332). The outer
  target is never used for gradients, checkpoint selection, or early stopping.
- Protocol: `0.5*BCEWithLogitsLoss + 0.5*DiceLoss(eps=1e-6)`; AdamW 1e-4/1e-4; cosine T_max=100;
  max 100 ep; patience 15; batch 8; seed 42; AMP. Selection = **min EARLY_STOP total loss** (Dice = secondary
  diagnostic only). Runs = exactly RUN1 fold0, RUN2 fold1, RUN3 fold2, RUN4 final. No extra runs.
- Results: fold0 50 ep / best **34** / ES loss 0.096024 / Dice 0.9200 · fold1 43 ep / **27** / 0.090209 /
  0.9246 · fold2 34 ep / **18** / 0.099504 / 0.9187 · **final refit = median 27 epochs** on all 4957
  (no early stopping). All HEALTHY; AMP GradScaler-skipped ≈0.048 % of batches (tolerance 1 %).
- **0 FORCED_SKIP** across all 4957 (verified genuine, min 19 fg px) — the path is defined and audited but
  never exercised on this population.
- Resource: **3,230,662,656 MACs (3.2307 GMACs)**, 6,461,325,312 FLOPs, refiner/global ratio **0.1024×**;
  host latency 0.005809 s (HOST_SPECIFIC).
- Notebook `notebooks/phasewise/phase_25a_regional_refiner/phase25a_dedicated_regional_refiner.ipynb`
  SHA **`7dfcf50540ee531e330c0338ea9326cdb73c24c9f8254b920c022598dd74733f`** — 66 cells (34 md / 32 code),
  10 valid PNG / 0 corrupt, 18 HTML tables, 0 tracebacks, **3× byte-identical**. Gates: registry 4/4 ·
  checkpoint integrity PASS · leakage PASS (holdout∩cache = val∩cache = test∩cache = 0) · TEST lock PASS ·
  implementation suite 35/35 · trainer rebind 8/8 · final freeze 25/25. Predecessors verified UNCHANGED
  (`286689fd…`, `9d620d6c…`, `612d7170…`, `b5da52d6…`).
- **HARDENED TRAINER** `scripts/training/train_phase25a_refiner.py` SHA **`7fd9e2ee…`**: atomic writes
  (temp + `os.replace`), history persisted BEFORE the checkpoint, full RNG restore (CPU-uint8 coercion),
  refuses to resume without RNG state, falls back to `best.pt` if `latest.pt` is unreadable, `--resume` on a
  completed run is a no-op. Rebind record `phase25a_trainer_rebind_and_incident.json` (8/8, science unchanged).
- **TEARDOWN INCIDENT 2026-09-30T11:01:06:** the harness killed the process tree mid-write → `history.csv`
  zero-filled, `latest.pt` truncated (`KeyError: 'storages'`); `best.pt` survived. Quarantined in
  `reports/audits/quarantine/phase25a_teardown_2026-09-30T1101/`; disposition = restart fold0 from epoch 0.
  Equivalence evidence: `es`/`esDice` reproduced exactly, `train`/`bce` to 5 decimals — **NOT bit-exact**
  (cuDNN/AMP non-determinism). Never claim bit-exactness for a training run; the 3× byte-identical rule
  applies to the NOTEBOOK.
- **AUDIT CORRECTIONS (false positives, fixed not silenced):** the health check counted the final refit's
  legitimately-NaN `early_stop_loss` (no ES split) as a defect and treated AMP GradScaler-skipped steps as
  fatal. Now `train_loss_all_finite` / `early_stop_loss_finite_when_applicable` / `amp_grad_overflow_rare`
  (≤1 %) / `train_loss_decreased`.
- Scripts: `run_phase25a_entry_gate.py` · `src/models/barr/{__init__,regional_refiner}.py` ·
  `src/data/{barr_roi,barr_refiner_dataset}.py` · `build_phase25a_bindings.py` · `run_phase25a_arch_gate.py` ·
  `build_phase25a_global_cache.py` · `build_phase25a_crossfit.py` · `train_phase25a_refiner.py` ·
  `build_phase25a_final_refit_rule.py` · `run_phase25a_resource_accounting.py` · `run_phase25a_audits.py` ·
  `build_phase25a_figures.py` · `build_phase25a_tables.py` · `run_phase25a_impl_tests.py` ·
  `run_phase25a_notebook_gates.py` · `build_phase25a_notebook.py` · `run_phase25a_final_freeze.py` ·
  `build_phase25a_trainer_rebind.py`.
- On-disk deliverables: notebook (1,020,425 B) · 10 figures + `FIG_MANIFEST.json` in
  `reports/figures/phase25a_regional_refiner/` · 22 `phase25a_*` audits in `reports/audits/` · 11 tables in
  `reports/tables/` · checkpoints `checkpoints/phase25a_barr_regional_refiner_v1_1/{fold0,fold1,fold2,final}`
  (folds hold `best.pt`/`latest.pt`; final holds `final.pt`/`latest.pt`).
- **Artifact key names to use when asserting** (do not guess): `parameter_count` (NOT
  `measured_parameters`), `final_refit_uses_holdout` (NOT `holdout_forbidden`), `outer_folds`,
  `inner_fit_fraction`, `inner_early_stop_fraction`, `oof_target_fold_never_used_for_checkpoint_selection`,
  `per_layer_macs`. Health-check keys as listed above.

## PHASE 24 — `RA-MedFiLM-BARR` specification (DESIGN ONLY, frozen)
- Method FROZEN `RA-MedFiLM-BARR` = Resource-Aware MedFiLM with Benefit-Aware Refinement Routing (`BARR`);
  arch id `ra_medfilm_barr_narrowed_v1` → **`..._v1_1`** (`SPECIFICATION_COMPLETENESS_ONLY`,
  `is_new_method=false`, `science_changed=false`; v1 kept as provenance). Retired `CBCR`. Forbidden name
  tokens: counterfactual / certified / causal / guaranteed. Use `PREFER_PAIRED_REFINEMENT_GAIN`,
  `USE_BENEFIT_AWARE_ONLY`.
- Novelty-bearing component = ONLY the pre-execution learned GT-free paired-gain router inside the integrated
  system (**max claim Level 2**). Never claim: `S_omega` fallback, gate mechanism, paired-gain estimand,
  multi-domain sharing, resource awareness, tiny-structure segmentation.
- All module targets are DESIGN TARGETS `measured=false`; the ONLY measured count is the global anchor
  3,523,001. Refiner rec 0.5M–1.5M / ceiling 2.0M. Router `B_phi` ≤250k params, ≤2 % global MACs (pref 1 %),
  reuses `F_global` (a SECOND global forward is FORBIDDEN). 15 allowed router inputs / 16 forbidden.
- Contracts: `DeltaDice_i = Dice(R_i,y_i) − Dice(G_i,y_i)` (paired contrast, NOT causal);
  `U_hat_i = Delta_hat_i − lambda*C_i` (single universal lambda FORBIDDEN; budget grid 0/10/25/50/100 %;
  cost = ANALYTICAL MACs ≠ latency); preservation margin **0.005**, per-domain mandatory.
- Data: TRAIN-only labels. `ROUTER_HOLDOUT` 15 % ≈ 875 (outcomes NEVER inspected in P24) and
  `ROUTER_DEVELOPMENT` 85 % ≈ 4957 with 3-fold OOF cross-fitting. The 808 VAL = reclassified
  `SECONDARY/CONTINUITY DEVELOPMENT BENCHMARK` (NOT router data, NOT untouched holdout). TEST CLOSED.
- Spec surface: 11 comparators C1–C11 (C7 load-bearing, C10 oracle non-deployable), 13 ablations, 8 criteria,
  7 modules 25A–25G (25C→25D ordering), 12-row unranked prior-art table.
- Notebook `phase24_narrowed_benefit_aware_refinement_spec.ipynb` SHA
  **`612d71700c1c1a45b94b8fcb8a3ff427bf32f6f6453130febeec49c6ec78caef`** (99 cells = 48 md / 51 code,
  12 HTML tables, 6 DESIGN PNG, 94/94 terminal assertions, 3× byte-identical). Supersedes `e4383d5a…`
  (76 cells), kept in `phase24_architecture_revision_v1_1.json::historical_provenance_preserved`.
  It emits its OWN terminal `PHASE24_NARROWED_BENEFIT_AWARE_REFINEMENT_SPEC_COMPLETE__PHASE25_ELIGIBLE_NOT_
  STARTED`; the `..._SPEC_COMPLETENESS_REPAIR_COMPLETE__RA_MEDFILM_BARR_V1_1_FROZEN_...` terminal is an
  EXTERNAL verdict and deliberately NOT embedded (avoids circular dependency).
- Gates: entry 27/27 · spec completeness 49/49 · no-execution counters all 0 (static scan over 14 scripts +
  notebook, TEST lock CLOSED) · freeze `phase24_spec_repair_freeze.json`.
- Terminal `PHASE24_SPEC_COMPLETENESS_REPAIR_COMPLETE__RA_MEDFILM_BARR_V1_1_FROZEN__PHASE25_ELIGIBLE_NOT_STARTED`.

## PHASE 23 VERDICT (binding on all future writing)
`PARTIALLY_OCCUPIED__NARROWER_NOVELTY_POSSIBLE`. **Algorithmic novelty OCCUPIED** — "predict the benefit of a
future computation then execute/skip" = metareasoning (Russell–Wefald 1991) + cascades (Viola–Jones 2001;
Latotzke 2021) + learned deferral (Mozannar–Sontag 2020); paired-gain target = CATE (Künzel PNAS 2019).
Problem formulation OCCUPIED by **JFS** (Moon et al., ICIP 2025, arXiv:2407.04519) — same framing +
paired coarse-vs-refined with revert-on-failure, but POST-HOC and untrained. Only INTEGRATION / system
novelty is unoccupied. **Max claim Level 2 (scoped); Level 3 "first to…" NOT supported.**
Also occupied (never claim): UniverSeg / MedSAM / MedUniSeg, MoE-routing in medical segmentation (M4oE),
DeferredSeg, Med-DANet V2, Adaptive Patching, GT-free quality prediction (Laves 2018, SDC, EvanySeg),
MobileSAM, tiny-lesion zoom. Terminology: paired refinement gain (NOT counterfactual); benefit-aware /
gain-gated (NOT certified). Name status `RENAME`. Phase-23 notebook SHA `e9f78cce…`; audits 17/17 + 38/38.

## FROZEN BASELINES (NEVER modify)
- Phase-20 protocol `phase20_shared_global_baseline_protocol.json` SHA `b74f1f9f…`; also immutable: every
  `phase20b_*_architecture_binding.json` / `*_pre_execution_check.json`.
- Phase-20 macro VAL Dice: DeepLabV3+ .827653 > MiT .822381 > UNet++ .792007 > Attn U-Net .789039 >
  U-Net .787833. Top-two NOT significant (p=.282) ⇒ **TIED; no single winner.** `transformer_mit_unet.py` =
  LOCAL_RANDOM_INIT, NEVER official MiT-B1. No timm/transformers/smp/einops. U-Net++ has no `phase20b_*`
  manifest → use `phase20_prediction_manifest.csv`.
- **Phase 21** `phase21_global_medfilm_fourdomain_seed42_clean_v3`: macro VAL Dice **0.835079**, best ep 66,
  rank 1/6, `best.pt` SHA **`286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7`**. NOT
  significant vs deeplabv3plus (p=.124) ⇒ TIED. ONE canonical VAL pass (808). 3,523,001 params; FiLM at 5
  sites (`bridge/decoder4/decoder3/decoder2/decoder1`), zero-init output projection ⇒ EXACT identity at init.
  Channels `[24,48,96,192,256]`, input 512×512 RGB_3CH, `forward(images, task_ids)`, logits interpolated to
  input size. Only claim "achieved X vs baseline Y"; NEVER "FiLM caused +X".
- **Phase 22** `phase22_diagnostic_protocol_v1` SHA `9d620d6c…`, freeze 7/7. Report
  `reports/phase22_resource_gap_report.md`. Diagnostic only: no training/router/TEST. The oracle regional arm
  HURTS in aggregate (−0.0425) and in every domain; KUB TINY +0.0132 is the only positive stratum **but CI
  includes 0 (p=0.763) ⇒ descriptive, NOT established**. Preserve: benefit is strongly heterogeneous;
  always-on regional is harmful in aggregate. `predicted_delta_dice == predicted_dice − global_dice`, both
  Dice vs GT ⇒ **GT-DERIVED despite the name**. Best GT-free |ρ| = 0.0689, AUC ≈ 0.5 ⇒ no deployable signal
  predicts regional benefit; no router established.
- Freeze writers embed `generated_utc` ⇒ freezes are NOT byte-reproducible; safe only because notebooks read
  freeze VALUES and never hash the freeze file.

## Six-model cost (MEASURED) — params / G MACs @ 1×3×512×512
MedFiLM 3,523,001 / 31.5517 · U-Net **7,763,041** (NOT 31,042,337) / 46.1373 · Attn U-Net 7,851,285 /
47.2190 · DeepLabV3+ 40,347,041 / 69.1394 · MiT 16,347,777 / 99.0986 · U-Net++ 9,159,681 / 137.9423.
MedFiLM is lightest but 31.55 G MACs is not small ⇒ "lightest" ≠ "fit for constrained deployment"; params do
NOT predict compute.

## CONVENTIONS & ENVIRONMENT
- Foreground `mask > 0` via `binarize_mask` (never `== 1`); conn 8; aspect-preserving resize + centre pad,
  `scale = min(size/w, size/h)`. `binary_metrics` thr 0.5 / eps 1e-7. TRAIN stochastic; VAL deterministic.
  `get_device(require_cuda=True)` raises rather than falling back to CPU.
- KUB taxonomy `kub_size_clean_v3_v1` FROZEN: conn-8, mask>0, FULL_FIELD only (ROI → ROI_NOT_PRIMARY_BINNED),
  `component_ratio = px/(native_h*native_w)`; Q25/Q50/Q75 = 0.0001497998649691358 / 0.0003401438395182292 /
  0.0008279682677469136, lower-inclusive. `<32 px = tiny` is NOT a project definition.
- Python `D:\Softfors\jup\.venv\Scripts\python.exe`; kernel `jup-venv`; nbclient + nbformat; torch 2.6.0+cu124;
  GPU RTX 3060 Ti; ~34–36 s/epoch at 371–372 steps (folds), ~55 s/epoch at 620 steps (final refit).
  matplotlib ≥3.11 removed `Axes.boxplot(labels=)` → use `tick_labels=`.
- **`CUDA_VISIBLE_DEVICES=""` is IGNORED here** — pass `--device cpu` and check provenance. `inspect_lock()`
  takes a DIRECTORY, not an id. Run artifacts in `experiments/<id>/`; `checkpoints/<id>/` holds ONLY
  best/last/latest `.pt`. Never measure GPU latency while training is live.
- **The harness TEARS DOWN the process tree every ~2–3.5 h.** A clean log with zero crash events = external
  teardown, NOT a crash. Relaunch via Bash `run_in_background: true` (the only surviving launch mechanism).
  **`tasklist` is NOT a liveness check.** See skill `resumable-long-training`.
- Notebook determinism: fixed cell ids + stripped `metadata.execution` + coalesced streams + fixed pandas
  Styler `.set_uuid` + `0x…`→`0xADDR` (EXCLUDE binary payload keys) + 3 byte-identical builds. Skill
  `phasewise-notebook-governance`.
- Augmentation inherited EXACTLY from `src.data.transforms.SegmentationTransform(train=True)`: hflip 0.5
  (`ImageOps.mirror`), rotation ±5.0° continuous, brightness 0.1, contrast 0.1. **`ImageOps.flip` (vflip) and
  90° rotation are NOT_INHERITED.**
- Resumability contract: `--resume` continues the SAME logical run from `latest.pt`, degrading to epoch 0 if
  absent; per-sample augmentation is a pure function of `sha256(f"{base_seed}:{epoch}:{sample_id}")`.
- Deferred known-failing tests: `test_phase14_part1.py` hangs; `test_predicted_roi.py` 3 fails;
  `test_kub_localizer.py` 1 fail.

## GOTCHAS
- **Assert the ARTIFACT exists after any builder** — a missing `w_json` call can build a dict, never write it,
  and still exit 0 (this happened to `phase24_architecture_spec.json`).
- **pandas `~` on an `object`-dtype bool Series is an INTEGER bitwise NOT** (`~True == -2`, truthy) → a CSV
  with mixed 'true'/'false' silently INVERTS fail-closed checks. Always `.astype(bool)` after mapping.
- **A notebook cell must never read a determinism/freeze artifact produced AFTER the notebook was written**
  (circular dependency). In-notebook assertions use pre-existing artifacts; verify determinism/freeze
  externally.
- **`display(Image(data=<str>))` treats a str as a FILENAME** — pass `Image(data=<bytes>, format="png",
  embed=True)`. Longest base64 payloads can lose ONE char in kernel→nbclient capture (odd length, still valid
  `IEND`); embed full-res when base64 ≤ 250k, downscale only > 544k galleries.
- **Always verify a totals field against its own underlying ledger, never trust it** (Phase-23
  `queries_logged` was 55 vs a ledger summing to 63).
- GroupNorm group count = largest divisor ≤ 8 (⇒ 8 for 16/32/64/96/128).
- **Do not trust artifact key names from memory** — read the artifact before asserting on it (see the
  Phase-25A key list above; three notebook/freeze assertion failures in this session came from guessed keys).
- `BARRRefinerCropDataset.__init__` takes `base_seed` (NOT `seed`) and `__getitem__` returns a **dict**.
  Return tensors with `np.array(..., dtype=np.float32, order="C", copy=True)`: the `_augment` ufunc preserves
  HWC layout, so a transposed array yields a non-contiguous tensor (stride (1,1024,4)) and a hidden copy in
  every conv, and the PIL-backed target is read-only.
- Builder f-strings: a generated cell containing `{len(hist)}` must be escaped as `{{len(hist)}}`.


---

## PHASE36 REVISION LEDGER (moved out of MEMORY.md 2026-10-26 — verbatim, no data loss)

### Acyclic authority DAG (Phase36 v1.18+)
`A(exec+manifest) -> B(launcher) -> C(governance) -> D(prelaunch bundle) -> E(supervisor) -> F(handoff)`.
- Launcher reads expected SHAs from a separately-frozen constant file (`..._launch_authority_sha.json`);
  supervisor pins that file's OWN bytes. Breaks the `bundle <-> launcher` fixpoint loop.
- Bundle asserts `supervisor_sha256_present = false`; ONLY step F (handoff) carries the supervisor SHA.

### Revision state (as of 2026-10-11)
- v1.14 CONSUMED_FAILED | v1.2-clean-eq CONSUMED/RESULT | final-prob diag v1.0 FROZEN |
  v1.1 CONSUMED_FAILED | v1.2 CONSUMED_RESULT | v1.3 `TERMINAL_EVIDENCE_ANOMALY` (rerun FORBIDDEN) |
  v1.15/v1.16/v1.17 PREPARATION ONLY / unconsumed | v1.18 CONSUMED_PRE_START_RUNTIME_FAILURE |
  v1.19 CONSUMED_POST_START_PRE_MODEL_FAILURE (D93A) |
  v1.20 CONSUMED_INTERRUPTED_POST_START_PRE_SCIENTIFIC_RESULT (D95; rerun FORBIDDEN) |
  v1.21 NOT_EXECUTED__PRELAUNCH_REAL_PATH_DEFECT (D96; never consumed) |
  v1.22 ELIGIBLE_NOT_STARTED (repaired; never executed).

### WO#19 / WO#19A / WO#20 = COMPLETE (PREP-ONLY)
Key frozen SHAs: v1.19 adj `76be9d8d...` (class CONSUMED_POST_START_PRE_MODEL_FAILURE, D93A = undefined
`_write_once_json` in `_journal_record`); v1.20 exec `b9d12824...` (237346 B) = v1.19 rebase + ONE
helper-definition repair, sci delta 0. v1.20 chain: launcher `8df46744...` | supervisor `ce06475e...` |
manifest `5881d0ba...` | bundle `989d5da6...` | authfile `9122122a...` | attestation `96b8343a...` |
adjudication `689cebad...` | eligibility `cb5a7aa0...` | freeze `27ee6b5b...` | inventory `e8715fa8...`.

### WO#21 (v1.20 interruption adjudication + minimal v1.21 repair) = COMPLETE (PREP-ONLY)
- v1.20 IS NOW CONSUMED. Real execution STARTED: START `f60eac4f...`, journal reached START:BEGIN
  (`ee7e4e66...`), RESULT/FAILURE ABSENT, 23 outputs ABSENT. PROCESS_EXIT `26e80a16...`:
  `child_exit_code=null`, `termination_observed=false`; stderr `8e29136d...` =
  `SUPERVISOR_EXCEPTION::KeyboardInterrupt::`; stdout empty. Supervisor INCORRECTLY returned rc=0 while
  termination unobserved. Interrupt ORIGIN NOT claimed; NOT a scientific-model failure. Adjudication
  (write-once) `reports/audits/phase36_v1_20_interruption_adjudication_v1_0.json` `31c29955...`,
  classification=CONSUMED_INTERRUPTED_POST_START_PRE_SCIENTIFIC_RESULT, relaunch_permitted=false.
  D95 = `V1_20_SUPERVISOR_RETURNS_ZERO_ON_UNOBSERVED_CHILD_TERMINATION` -> RECONCILED (repaired in v1.21).
- v1.21 = ELIGIBLE_NOT_STARTED (never executed). exec `phase36_robustness_execution_v1_21.py` `312886c6...`
  (237346 B) = PURE token rebase of v1.20 (129 changed lines, ALL version-token-only, 0 non-version).
  `scientific_delta_count_v1_20_to_v1_21 = 0`. D61/D75/D93A preserved.
- v1.21 supervisor `7182d3c0...` = v1.20 rebase + D95 repair (SUPERVISOR-ONLY): `_decide_return_code`
  returns 2 (NEVER 0) unless termination observed; `_terminate_child_tree`/`_force_kill_process_tree`
  deterministically terminate+wait the child tree (taskkill /F /T on Windows) and record cleanup evidence;
  PROCESS_EXIT distinguishes NORMAL_CHILD_COMPLETION / SUPERVISOR_INTERRUPTION /
  SUPERVISOR_INTERNAL_EXCEPTION; test-only `_POPEN` seam (never env/CLI/config); single dispatch, no
  retry/relaunch, never writes a science marker.
- v1.21 chain: launcher `0711fd79...` | supervisor `7182d3c0...` | manifest `279626d7...` |
  bundle `04e38ceb...` | authfile `9b629074...` | attestation `08ec4063...` | adjudication `427eb5d0...` |
  inventory `6bea25f2...` (23 targets) | namespace `2f7d8990...` | contract `dadda0c1...` |
  freeze `77843afc...` | eligibility `3dabf031...`. Tokens `PHASE36_V1_21_EXECUTE`,
  `PHASE36_V1_21_LAUNCH_AUTHORITY`. Section 10 gate enforces v1.20 consumed state.
- Battery GREEN: sci-repair 38/38 | negctl 47/47 | xcontract 67/67 | coherence PASS | pure-gate 7/7
  NOT_RELEASED | gate-readonly PASS | D95 interruption regression 28/28 (A-F; v1.20 reproduces rc=0
  defect) | D93A 9/9 | launcher/supervisor `--verify-only` PASS. TEST_accessed=false,
  ROUTER_HOLDOUT_accessed=false, v1_21_attempt_consumed=false, all 23 targets ABSENT.

### WO#21A (v1.21 D96 prelaunch-defect adjudication + minimal v1.22 prep) = COMPLETE (PREP-ONLY)
- D96 = `V1_21_REAL_DISPATCH_CALLS_UNDEFINED_V1_19_CONSUMED_HISTORY_VERIFIER`: v1.21 launcher `main()`
  L636 called `verify_v1_19_consumed_history()` (defined 0x) instead of the defined
  `verify_v1_20_consumed_history()`; escaped `--verify-only` (returns before L636). Sci effect NONE.
  v1.21 FROZEN `NOT_EXECUTED__PRELAUNCH_REAL_PATH_DEFECT` (never consumed) - adj `4c2bd8f7...`.
- v1.22 = v1.21 PURE rebase (sci delta 0): exec `29d29da8...` | launcher `eb45f2fd...` (D96 fix;
  Section 10 gate STILL binds consumed v1.20 `31c29955...`) | supervisor `e721bacac...` (D95 preserved) |
  launch-authority `e89a17d1...` | bundle `df0b38df...` | manifest `98a9b6e5...`.
  Tokens `PHASE36_V1_22_EXECUTE` / `_LAUNCH_AUTHORITY`.
- Battery GREEN incl. D96 real-branch 25/25 + D95 28/28 (v1.20 defect reproduced) + sci-repair 38/38 |
  negctl 47/47 | xcontract 67/67 | coherence PASS | pure-gate 7/7 | gate-readonly PASS | verify-only
  PASS. 23 targets ABSENT; TEST_accessed=false; ROUTER_HOLDOUT_accessed=false.
- TERMINAL: `PHASE36_V1_21_PRELAUNCH_DEFECT_ADJUDICATED__V1_22_ELIGIBLE_NOT_STARTED`.
  Phase36 NOT_COMPLETE_PENDING_V1_22_EXECUTION; Phase37 NOT_STARTED. NO v1.22 EXECUTION.
  Next: operator gate `PHASE36_V1_22_EXECUTE=1` + `PHASE36_V1_22_LAUNCH_AUTHORITY`.
  Full detail -> `.workbuddy-ai/memory/2026-10-11.md`.

## BARR-M1 v1.0a/v1.0c — FULL TRAP WORDING (archived from MEMORY.md 2026-10-28)
`reports/planning/barr_m1_v1_0a/` + `reports/planning/barr_m1_approval_v1_0c/`; audit JSON
`reports/audits/barr_m1_*_v1_0a.json`, `reports/audits/barr_m1_v1_0c_*`; manifests `fe91aadc…`
(reauthorization gate v1.0), gate harness `e82ecdb7…`. 28/28 and 32/32 checks. Recommended work =
`BARR-M1` = frozen Phase-28 arms A0/A1/A8 (NOT an `EXT-` id). Terminals
`BARR_M1_SCIENTIFIC_DESIGN_RECONCILED__AWAITING_AUTHORIZATION` and
`BARR_M1_APPROVAL_PACKAGE_READY__SCIENTIFIC_EXECUTION_NOT_AUTHORIZED`. Approval block NOT APPROVED.
The v1.0 Task-D proposal was corrected on five points — the following wording must NOT be repeated:
- POLICY_COMPARISON, NOT router causal ablation. A8 vs A1 differs in 4 fields (router, λ·C, S_omega,
  budget 0.25/K=1239 vs 1.00/all) ⇒ router effect NOT identifiable from A0/A1/A8.
  `phase28_core_contrast_map.json` pre-registers ONLY `A7_vs_A8`; A0/A1 are descriptive rows with no
  formal pairwise reference. Only A7_vs_A8 isolates one component.
- "Refine-all is net harmful" does NOT transfer. Phase-22 = VAL808 + ORACLE GT ROI, net −34.32
  (536/808). Frozen A1 on DEV = net +8.219 (2115/4957 = 42.67% harmed). Opposite sign; different
  population + ROI source. Surviving claim = harm RATE drop, not net harm.
- HARM-RATE DENOMINATOR TRAP (v1.0b). Frozen `harmful_activation_share` = n_harmful_routed / n_routed —
  a CONDITIONAL rate for every arm. 32.37% = 390/1205 (conditional on ACCEPTANCE), NOT all-population.
  A1's 42.67% = 2115/4957 (A1 executes all ⇒ conditional ≡ unconditional). 42.67%→32.37% switches
  denominators = INVALID. Correct: unconditional A1 42.6670% (2115/4957) → A8 7.8677% (390/4957);
  conditional on execution A1 42.6670% → A7 33.2526% (412/1239) → A8 32.3651% (390/1205). Selection
  accounts for 42.67→33.25; safety for 33.25→32.37. Upper bound A8 harmed 390 ≤ 1205. Tolerance 1e-9
  affects ONLY A1 (2115→2107; the 8 near-zero negatives are outside both sets).
- Phase-28 primary population is IN-SAMPLE. ROUTER_DEVELOPMENT 4957 ⊂ TRAIN 5832 (4957/4957),
  ∩ VAL808 = 0. B_phi/S_omega trained on those exact 4957 (5-fold + all-DEV final refit); G/R_psi on
  TRAIN ⊃ DEV. VAL808 out-of-sample but consumed (Ph27+Ph29); HOLDOUT consumed (Ph30); TEST locked ⇒
  no pristine population remains. Every number = DESCRIPTIVE_DEV.
- ZERO GPU. A0/A1/A7/A8 reproduce frozen Phase-28 aggregates exactly (9/9, tol 1e-9, 0 models,
  0 forwards) from Ph25C OOF labels + Ph25E C8 membership (λ.25/bud.25) + Ph25F OOF safety. Study is
  RE_ANALYSIS_ONLY (CPU minutes), not 2–6 GPU-h. This is also an exact positive control.
- Seeds 42/123/3407 = 3 retrained DOWNSTREAM stacks on ONE fixed G (seed 42) (`macro_global_dice`
  identical to 1.36e-16; `seed_regenerates_fold_membership=false`). SD 0.000590 (ddof=1,n=3,2df) =
  downstream-retraining randomness ONLY — never inference noise / sampling error / full-system replication.
- `patient_id` real only for KUB (267); ISIC/BUSI/KVASIR NOT_AVAILABLE; `case_id` NOT_AVAILABLE
  everywhere ⇒ bootstrap domain-stratified, patient-clustered inside KUB only (declared limitation).
- Endpoint: paired A8−A0/A8−A1/A1−A0 over all 4957 (SKIP/REJECT ⇒ delta exactly 0.0; matches frozen
  0.001827009064 = 9.0564839294/4957). Macro = (1/4)·Σ_domain mean(dice); cumulative sums never
  reported as macro. Harm delta < −1e-9. Bootstrap 2000/seed42/paired-common/95%/no-corr.
- Gate R1–R10 specialised: R2→frozen SHAs + threshold VALUES + row identity; R3→value compare +
  frozen-aggregate reproduction; R5/R6/R7→training-only N/A with explicit substitutes.
- Gate script `scripts/analysis/barr_m1_reanalysis_gate_v1_0c.py` — 78 checks, ready, `--execute`
  REFUSED, 4/4 positive controls exact, 8/8 synthetic negative controls detected.
- Join must be KEYED on `sample_id`: label vs membership row order differs at 4955/4957 positions
  (positional zip silently mis-assigns selection). Frozen Phase-28 `mean_true_delta_dice_routed` is
  POOLED (sum/n_routed: A1 .001658079789 · A7 .007246629237 · A8 .007515754298), NOT macro — the
  positive control compares SUMS + COUNTS, never pooled-vs-macro. `n_executed` is a POLICY property
  (A1=4957 even though 67 deltas are exactly 0), never count `delta != 0`.
Full narrative → `.workbuddy-ai/memory/2026-10-27.md`.
