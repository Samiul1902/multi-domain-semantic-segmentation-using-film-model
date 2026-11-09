# PHASE 20 — FINAL REPORT
## Shared Four-Domain Global Baseline · Single Frozen UNet++ · No FiLM · No Regional Module

**Terminal state: `PHASE20_SHARED_GLOBAL_BASELINE_COMPLETE__PHASE21_ELIGIBLE_NOT_STARTED`**

Phase 20 is **COMPLETE**. Phase 21 is **ELIGIBLE but NOT STARTED** — it requires fresh supervisor
authorization. Nothing in this report starts Phase 21.

---

## A. Phase identity and scope

1. **Phase ID / stage:** Phase 20, **Stage B** (main multi-domain program; Stage A post-H3 branch
   remains CLOSED with label `H3_SUPPLY_REDESIGN_INSUFFICIENT`).
2. **Primary question:** how well can ONE shared conventional segmentation model represent all four
   medical domains under the harmonized Stage-B data contract, **without** task-conditioned FiLM and
   **without** the regional mechanism?
3. **Scope delivered:** exactly ONE strong conventional shared four-domain baseline
   (ISIC / BUSI / KVASIR / KUB).
4. **Experiment ID:** `phase20_shared_unetpp_fourdomain_seed42_clean_v3`.
5. **Explicit exclusions honoured:** NO FiLM, NO task conditioning as model input, NO regional
   mechanism, NO localizer, NO proposal/ROI, NO RA-MedFiLM modules.
6. **No architecture sweep:** ONE architecture frozen prospectively before any Phase-20 result was
   observed (`selection_time = PRE_TRAINING`,
   `current_phase20_results_used_for_selection = False`).
7. **No loss / optimizer / LR / scheduler sweep**, and **no second seed** (3-seed reproducibility
   belongs to Phase 29).
8. **Exactly ONE logical training run**, seed 42. Resume continues the same logical run; no second
   independent run exists (`independent_duplicate_runs: 0`).
9. **No TEST reads of any kind** — Phase 39 is the only final TEST phase.
10. **Registry commit token for the submission:** "MS + AB".

## B. Entry gate, authority binding, and leakage

11. **Phase-19 authority binding:** FAIL-CLOSED, **9/9 checks PASS**; 11 Phase-19 artifacts SHA-bound
    (`reports/audits/phase20_phase19_authority_binding.json`, `591c13919d844781…`).
12. **Phase-20 entry gate:** criteria **E1–E12 all PASS**
    (`reports/audits/phase20_entry_gate.json`, `c4805d8c63bccd84…`).
13. **Cross-domain TRAIN↔VAL duplicate audit:** verdict
    **`PHASE20_DUPLICATE_AUDIT_PASS__NO_TRAIN_VAL_LEAKAGE`**
    (`reports/audits/phase20_cross_domain_duplicate_audit.json`, `4e3047c61f4edff8…`).
14. Audit detail: **0 blocking pairs, 0 exact-sha256 matches**, 37 pHash candidates (all
    *within*-dataset), all **6 cross-dataset pairs at Hamming ≥ 10**, 0 high-attention.
15. Method: exact sha256 + the repo-approved pHash (32×32 L BOX → 2-D DCT ortho → top-left 8×8 →
    median → 64-bit; candidate Hamming ≤ 6), reused verbatim from `scripts/audit/run_phash_fast.py`;
    reads `manifests/phase4_v3/{train,val}.csv` only — **never** the TEST-bearing `all_paired.csv`.
16. **Training was gated on leakage clearance** — the audit passed *before* the run started.

## C. Architecture and input contract

17. **Legacy prior evidence** (`reports/audits/phase20_legacy_baseline_selection_evidence.json`,
    `1c3fbbe184492757…`, label `LEGACY_PRIOR_EVIDENCE__NOT_CURRENT_PHASE20_RESULT`): **no legacy
    KUB-bearing four-domain shared baseline exists** (medfilm_seg = 3-domain @256 with empty source;
    medfilm_seg_v2 = weak-label @384, DO_NOT_REUSE; Omni_segv2 = brats/busi/isic/kits/kvasir
    2.5D-3D; safeseg = a different set).
18. **Fallback evidence used:** same-repo clean-v3 KUB comparison under a fixed protocol —
    UNet 0.740613, Attention U-Net 0.752513, **UNet++ 0.764160**, DeepLabV3+ 0.750914.
19. **Architecture frozen:** `unetpp_nested_4_level_no_deep_supervision_base32` — single **UNet++**,
    **9,159,681 parameters**, ONE shared parameter set across all four domains, ONE output head
    (`out_channels == 1`).
20. **Architecture freeze artifact:**
    `reports/audits/phase20_baseline_architecture_freeze.json` (`aed29d3018abcae0…`).
21. **Input channel policy frozen:** `RGB_3CH` under contract label
    `PHASE20_BASELINE_OPERATIONAL_INPUT_ONLY` — explicitly **NOT** the final Phase-24 policy. Native
    RGB stays deterministic RGB; native-L domains are deterministically replicated to 3 identical
    channels; no learned modality adapter, no domain-specific normalization branch.
22. **Model input excludes** `task_id`, `dataset_id`, KUB `category`, `patient_id`, `case_id`,
    `foreground_fraction`, and all mask-derived metadata. **`task_id` is never passed to
    `model(...)`** — asserted in the trainer.
23. **Resolution frozen at 512**, decided PRE_TRAINING with stated evidence and **no resolution
    search** (256 vs 384, 256 vs 512, 384 vs 512 were deliberately not compared).
24. **Canonical foreground** is `mask > 0` (never `mask == 1`); connectivity 8 for object metadata;
    training masks remain ordinary binary.

## D. Sampling, loss, optimizer

25. **Sampling policy** `phase20_domain_balanced_uniform_v1` — domain-balanced weighted sampling
    with replacement, 5832 samples/epoch; `task_id` used for **sampling/bookkeeping only**.
26. **Sampling audit** (`reports/audits/phase20_sampling_policy_audit.json`, `69134c1c5811a363…`)
    confirms equal expected per-domain mass: each domain 0.25 (empirically 24.11–26.08%).
27. **Loss:** `bce_dice`, weights 0.5 / 0.5, Dice epsilon 1e-06.
28. **Optimizer:** AdamW, lr 1e-4, weight decay 1e-4.
29. **Scheduler:** CosineAnnealingLR, T_max 100, stepped **per epoch after train + val**.
30. **Batching:** batch 4, 4 loader workers, AMP enabled, seed 42.

## E. Pre-execution verification

31. **Pre-execution check:** **26/26 PASS**, `training_authorized = true`
    (`reports/audits/phase20_pre_execution_check.json`, `dc3d31f2cf8d67f0…`).
32. It proved: TEST rejected on **both** the dataset and loader paths; tensor shapes
    `[2,3,512,512]` / `[2,1,512,512]` / out `[2,1,512,512]`; finite loss (0.79198); sampler mass
    exactly 0.25 per domain; `derive_epoch_seed(42,5) = 42039721` stable; output dirs clean.
33. **Per-epoch deterministic seeding** `derive_epoch_seed(base, k) = (base·1_000_003 + k·7919) mod
    (2³¹−1)`; verified `derive(42,1)=42008045`, `derive(42,2)=42015964`, `derive(42,5)=42039721`.
    A fresh balanced sampler and fresh DataLoaders are built each epoch, so **epoch k depends only on
    (seed, k)** — which is what makes a resumed run bit-exact.

## F. Training execution and result

34. **Training ran to natural termination.** `stop_reason = EARLY_STOPPING_PATIENCE`, final epoch 70,
    patience 15, `ties_count_as_bad_epochs = true`.
35. **Wall clock:** 43,001 s (**~11.94 h**) across 70 epochs, ~610 s/epoch.
36. **Resume count: 0** — the run was never interrupted; it ran continuously and `closure.json`
    records `resume_events: []`. The harness teardown notice at completion was benign.
37. **Best epoch 55** — **macro-domain VAL Dice `0.792007328746103`**.
38. **Per-domain Dice at the best epoch:** ISIC 0.8600706700810291 · BUSI 0.8163009576854252 ·
    KVASIR 0.7709952691976972 · KUB 0.7206624180202605.
39. **Best val loss** 0.18251773855178663.
40. **Convergence narrative:** macro Dice rose 0.538233 (ep1) → 0.627600 (ep4) → 0.788822 (ep49) →
    **0.792007 (ep55)**, then plateaued; the final 15 epochs produced no improvement.
41. **Training transient (documented, not hidden):** epoch 48 saw a KUB collapse to 0.3004 with val
    loss 0.4217, fully recovered by epoch 49. A one-epoch instability spike, not a divergence —
    relevant when Phase 21 compares against this baseline.

## G. Checkpoint closure and selection replay

42. **Selection rule `phase20_macro_domain_mean_dice_v1`:** select on
    `macro_domain_dice = mean(Dice_ISIC, Dice_BUSI, Dice_KVASIR, Dice_KUB)`, each a per-image macro
    within its domain; tie-break = **lower validation loss**. Never pooled/micro Dice, never KUB
    alone, never weighted Dice.
43. **Closure** (`reports/audits/phase20_training_closure.json`, `b7aaff2ba4a81278…`): history
    integrity PASS — 70 rows, epochs contiguous from 1, no missing, no duplicates, monotonic.
44. **Replay verdict `PHASE20_CHECKPOINT_SELECTION_REPLAY_PASS`**, all **10/10 checks PASS**
    (`reports/audits/phase20_checkpoint_selection_replay.json`, `8be41421b7110cf9…`).
45. **Three-way agreement proven:** history-selected epoch **55** == stored `best_epoch` **55** ==
    `best.pt` epoch **55**; replayed macro == `best.pt` macro == closure macro (within 1e-9).
46. Replay is **disk-only** — no inference is performed to select the checkpoint.
47. `best.pt` SHA `d647ac52bf39704549ce2eea4fee8e17dfcb5ce9ace5e0b24ffb1f7db86a059f`;
    `latest.pt` SHA `7be70a818ff8b0f0b083bf383fa20b6b3ef3d35eb77bbef6f12121386f649959`.

## H. Canonical VAL evaluation and persisted predictions

48. **Exactly ONE canonical VAL inference pass** over **808/808** VAL samples
    (`reports/audits/phase20_val_evaluation.json`, `0d78838060477fad…`);
    `canonical_val_inference_runs: 1`, threshold 0.5, elapsed 123 s.
49. **TEST reads all zero:** image 0, mask 0, inference 0, visualization 0.
50. **808 predictions persisted** as self-contained NPZ under
    `reports/predictions/phase20_shared_unetpp_fourdomain_seed42_clean_v3/val/<DATASET>/<sample_id>.npz`
    with `prob` float16, `pred` uint8, `gt` uint8 — so later phases never replay preprocessing or
    inference (`allows_future_phases_to_avoid_replay: true`).
51. **Prediction manifest:** `reports/audits/phase20_prediction_manifest.json` (`5e92de8cf8449626…`)
    binds every NPZ to the checkpoint SHA, threshold, channel policy, resolution, and both contract
    IDs. Per-domain counts: ISIC 357 / BUSI 84 / KVASIR 87 / KUB 280.
52. **Per-image metric table:** `reports/tables/phase20_per_image_val_metrics.csv` (808 rows,
    `0c96a07d85d9951e…`).
53. Note: the macro Dice recomputed from persisted predictions (0.792010) differs from the
    training-time value (0.792007) by **3.3e-6** — batch-size-dependent float accumulation, not a
    bug. **Bitwise GPU determinism is not claimed.**

## I. Per-domain and macro results

54. **Per-domain VAL performance (macro over images, threshold 0.5):**

    | domain | n | Dice | IoU | precision | recall | specificity | MCC | HD95 (px) | ASSD (px) | Surface Dice |
    |---|---|---|---|---|---|---|---|---|---|---|
    | ISIC | 357 | 0.860074 | 0.779969 | 0.864932 | 0.898093 | 0.974146 | 0.847816 | 43.20 | 13.24 | 0.2795 |
    | BUSI | 84 | 0.816303 | 0.712567 | 0.819544 | 0.867261 | 0.990967 | 0.820361 | 61.02 | 13.73 | 0.3982 |
    | KVASIR | 87 | 0.771001 | 0.669674 | 0.793840 | 0.825549 | 0.966096 | 0.759417 | 88.29 | 22.70 | 0.3732 |
    | KUB | 280 | 0.720662 | 0.601896 | 0.761739 | 0.770180 | 0.955470 | 0.727351 | 59.98 | 20.63 | 0.3331 |
    | **MACRO_DOMAIN** | **808** | **0.792010** | 0.691026 | 0.810014 | 0.840271 | 0.971670 | 0.788737 | 63.12 | 17.57 | 0.3460 |

55. **MACRO_DOMAIN is the unweighted mean of the four per-domain values** — the scientific summary
    and the selection metric.
56. **POOLED_DESCRIPTIVE** Dice 0.841217 / IoU 0.725948 is reported **descriptively only** and is
    never used for selection (`pooled_is_descriptive_only: true`).
57. **Bootstrap 95% CIs** (percentile, 2000 resamples, seed 42, alpha 0.05) —
    `reports/tables/phase20_domain_bootstrap_ci.csv` (`f93eabeb7b408322…`):
    ISIC [0.842596, 0.876447] · BUSI [0.780600, 0.847183] · KVASIR [0.723602, 0.817141] ·
    KUB [0.693664, 0.747244] · **MACRO_DOMAIN [0.744572, 0.838188]**.
58. **Pixel confusion matrices** (raw + row-normalized, rows = GT, cols = prediction) per domain and
    pooled — `reports/tables/phase20_confusion_matrices.csv` (`c4bcccc42669bdc7…`) and
    `reports/audits/phase20_confusion_matrices.json`.
59. **Calibration** (`reports/tables/phase20_calibration_ranking.csv`, `60282d6698591012…`),
    deterministic pixel subsample stride 4, 15 bins: Brier 0.013576–0.049413; **ECE
    0.012151–0.043262**; MCE 0.214067–0.414367.
60. **Ranking quality:** ROC-AUC 0.965419–0.984793; PR-AUC (average precision) 0.879303–0.946182 —
    strong ranking even where boundary metrics are weak.
61. **KUB reporting subgroups** (`reports/tables/phase20_kub_subgroup_analysis.csv`,
    `c9fd02209dadf0f9…`), `role = REPORTING_ONLY`: Kidney_Stone Dice 0.752332 (n=112),
    Ureteric_Stone 0.738911 (24), Bladder_Stone 0.692989 (144); KUB_ALL 0.720662; empty-prediction
    rate 0.0268–0.0417.
62. **KUB size stratification** by the FROZEN taxonomy `kub_size_clean_v3_v1` (FULL_FIELD only;
    ROI → `ROI_NOT_PRIMARY_BINNED`) — `reports/tables/phase20_kub_size_stratification.csv`
    (`2ad1ce287b76385a…`), `role = REPORTING_ONLY__DESCRIPTIVE`:

    | stratum | n | Dice | IoU | median component_ratio |
    |---|---|---|---|---|
    | **TINY** | 44 | **0.531395** | 0.423062 | 0.000095 |
    | SMALL | 19 | 0.680591 | 0.551392 | 0.000195 |
    | MEDIUM | 27 | 0.640754 | 0.516926 | 0.000553 |
    | LARGE | 13 | 0.635866 | 0.531117 | 0.001763 |
    | ROI_NOT_PRIMARY_BINNED | 177 | 0.790431 | 0.669933 | — |

63. **Primary scientific finding:** KUB **TINY** stones are the quantified bottleneck at **Dice
    0.531**; FULL_FIELD cases (0.53–0.68) are markedly harder than ROI crops (0.79). This is the
    known cross-regime caveat (a ROI crop magnifies its object) and it localizes exactly where the
    RA-MedFiLM work must earn its gain.
64. **Boundary metrics are weak relative to overlap metrics** (Surface Dice 0.28–0.40 at a 2-px
    tolerance on 512-px images). Reported honestly, not cherry-picked.

## J. Visualization evidence

65. **64-case deterministic gallery** — 16 cases per domain × 4 domains
    (`reports/audits/phase20_visualization_evidence.json`, `0a67ec2f37632487…`).
    Selection is **prediction-independent** (`selection_prediction_dependent: false`): within each
    domain, VAL samples are sorted by `sample_id` and evenly spaced, seed 42 — so the same 64 IDs
    are reusable in Phase 21 for a like-for-like comparison.
66. **9 panels per case** (A native image, B GT mask, C GT contour, D **actual model input replayed
    through the deterministic VAL transform**, E probability map, F thresholded prediction,
    G TP/FP/FN error map, H prediction overlay, I GT-vs-prediction contour overlay), with per-case
    Dice/IoU/precision/recall. Paginated 4 cases per page → **16 pages**
    (`reports/figures/phase20_multidomain_baseline/gallery_page_01..16.png`).
67. **`cherry_picked: false`, `failure_cases_included: true`** — the gallery contains failures, and
    a separate 24-lowest-Dice figure plus FP/FN-dominant and empty-case figures make failure modes
    explicit. 32 figures total (8 training curves + 4 result figures + 4 success/failure + 16 pages).
68. **Per-dataset 16-case grids** (`reports/figures/phase20_multidomain_baseline/grids/*_grid_16cases.png`)
    rendered for the coverage registry.

## K. Notebook

69. **Reviewer notebook:**
    `notebooks/phasewise/phase_20_multidomain_baselines/phase20_shared_global_unetpp_baseline.ipynb`
    — **61 cells (31 markdown / 30 code), zero tracebacks, monotonic execution counts 1–30, 31
    embedded PNGs, 49 HTML tables**.
70. **SHA-deterministic:** `367f5e54ad42d38d7157a09f7c5a19187f61d6ce81b7919c385c63df043d08d4`,
    identical across independent builds (`reports/audits/phase20_notebook_determinism.json`,
    `e0ff7b63d00b7133…`, `deterministic: true`). Achieved with deterministic cell ids (`p20NNN`),
    stripped `metadata.execution` timestamps, and coalesced adjacent stream outputs.

## L. Registry and governance synchronization

71. **All registries and governance documents synchronized, and every sync is provably convergent.**

    - `reports/audits/trained_model_visualization_registry.csv` — **14 rows** (13 prior phases
      preserved verbatim + 1 Phase-20 row), `b76ab4ef3a5b9a9c…`
    - `reports/audits/trained_model_visualization_registry.json` — 14 entries
    - `reports/audits/dataset_visualization_coverage.csv` — 8 rows (4 legacy + 4 Phase 20 @ **16
      cases each**), new `phase` column added without altering legacy rows, `cd66162d957e8886…`
    - `reports/audits/phase20_registry_sync.json` (`052424d509e0d14e…`) — re-run byte-identical
    - Governance sync over **7 files** (`phasewise_notebook_map.json`, `notebooks/phasewise/README.md`,
      `phase_19/20/21` READMEs, `PROJECT_MASTER_PLAN.md`, `00_PHASEWISE_PROJECT_INDEX.ipynb`
      executed) — all 7 byte-identical on re-run, `all_synchronized_files_converged: true`;
      journal `reports/audits/phase20_completion_governance_state.json`
      (`972dddd2a65d8b1dbe4136278162a215b611ba7df4a0af756315372528710362`, stable across runs)
    - Statuses recorded: Phase 19 **COMPLETE** · Phase 20 **COMPLETE** ·
      Phase 21 **ELIGIBLE / NOT STARTED**

---

## M. Integrity, governance, and safety attestations

- **Frozen scientific protocol UNCHANGED:**
  `reports/audits/phase20_shared_global_baseline_protocol.json` =
  `b74f1f9f429adbce374f0306180943b9f373f872e1e69e115b7d17e81414283c`.
- **All 15 bound code SHAs current — 0 drift** (trainer, models, dataset, transforms, loaders,
  sampler, losses, selection rule, metrics, targets, test_lock, device, reproducibility, run_lock).
  `trainer_sha256` in `closure.json` matches the protocol binding exactly.
- **Architecture freeze** `aed29d3018abcae0…`, **sampling audit** `69134c1c5811a363…`,
  **legacy evidence** `1c3fbbe184492757…` — all unchanged.
- **TEST lock intact** (1683 samples, frozen, `freeze_timestamp 2026-09-13T17:52:32`); **TEST reads
  = 0** on every path.
- **Forbidden mechanisms: none present.** `src/models/unetpp.py` contains 0 occurrences of
  film / localizer / proposal / regional; no task conditioning anywhere in the forward pass.
- **Exactly one Phase-20 checkpoint directory**; no Stage-A or legacy checkpoint overwritten.
- **Two real bugs were found and fixed during pre-canonical validation**, both in the **post-training
  analysis layer**, which is deliberately **not** among the 15 SHA-bound files — so the scientific
  freeze is intact:
  1. `domain_summary` omitted the `total` key required by `pooled_segmentation_metrics` → `KeyError`.
  2. `boxplot(labels=...)` — **matplotlib 3.11.2 removed it** (now `tick_labels`) → `TypeError`.
  A third (notebook-side) bug, `sorted(x, columns=[...])`, was also fixed. All were caught by a
  **synthetic smoke test of the analysis layer run while training was still in progress**, plus a
  read-only real-VAL test of the KUB size path.
- **Operational note:** the harness tears down background processes; durability came from
  **resumability** (`--resume --recover-stale-lock`), not detachment — `nohup` dies in ~45 s and
  `schtasks` is hard-blocked by security policy (non-bypassable, probed and confirmed). In the end
  the run was never interrupted (`resume_count: 0`).

## N. Deliverable SHA inventory

| artifact | sha256 (prefix) |
|---|---|
| `reports/audits/phase20_shared_global_baseline_protocol.json` | `b74f1f9f429adbce` |
| `reports/audits/phase20_baseline_architecture_freeze.json` | `aed29d3018abcae0` |
| `reports/audits/phase20_sampling_policy_audit.json` | `69134c1c5811a363` |
| `reports/audits/phase20_legacy_baseline_selection_evidence.json` | `1c3fbbe184492757` |
| `reports/audits/phase20_phase19_authority_binding.json` | `591c13919d844781` |
| `reports/audits/phase20_entry_gate.json` | `c4805d8c63bccd84` |
| `reports/audits/phase20_cross_domain_duplicate_audit.json` | `4e3047c61f4edff8` |
| `reports/audits/phase20_pre_execution_check.json` | `dc3d31f2cf8d67f0` |
| `reports/audits/phase20_training_closure.json` | `b7aaff2ba4a81278` |
| `reports/audits/phase20_checkpoint_selection_replay.json` | `8be41421b7110cf9` |
| `reports/audits/phase20_val_evaluation.json` | `0d78838060477fad` |
| `reports/audits/phase20_prediction_manifest.json` | `5e92de8cf8449626` |
| `reports/audits/phase20_visualization_evidence.json` | `0a67ec2f37632487` |
| `reports/audits/phase20_phase21_entry_criteria.json` | `b4f7e20421ec919f` |
| `reports/audits/phase20_notebook_determinism.json` | `e0ff7b63d00b7133` |
| `reports/audits/phase20_registry_sync.json` | `052424d509e0d14e` |
| `reports/audits/phase20_completion_governance_state.json` | `972dddd2a65d8b1d` |
| `reports/tables/phase20_per_image_val_metrics.csv` | `0c96a07d85d9951e` |
| `reports/tables/phase20_domain_performance.csv` | `eb3b913b01323c37` |
| `reports/tables/phase20_confusion_matrices.csv` | `c4bcccc42669bdc7` |
| `reports/tables/phase20_calibration_ranking.csv` | `60282d6698591012` |
| `reports/tables/phase20_domain_bootstrap_ci.csv` | `f93eabeb7b408322` |
| `reports/tables/phase20_kub_subgroup_analysis.csv` | `c9fd02209dadf0f9` |
| `reports/tables/phase20_kub_size_stratification.csv` | `2ad1ce287b76385a` |
| `reports/tables/phase20_gallery_selection.csv` | `2bc7c16286999ced` |
| `experiments/.../history.csv` | `ed9abeee112a4595` |
| `experiments/.../closure.json` | `96ea096d46f3d173` |
| `experiments/.../config.json` | `27c5015da9bbbd61` |
| `checkpoints/.../best.pt` | `d647ac52bf397045` |
| `checkpoints/.../latest.pt` | `7be70a818ff8b0f0` |
| `notebooks/phasewise/.../phase20_shared_global_unetpp_baseline.ipynb` | `367f5e54ad42d38d` |

## O. Phase-21 eligibility assessment

- **All 12/12 Phase-21 entry criteria are met** (`reports/audits/phase20_phase21_entry_criteria.json`):
  training naturally terminated; replay PASS; all four domains evaluated; macro-domain score
  available; per-domain scores for every domain; 808 prediction artifacts persisted; complete
  notebook executed; 64 deterministic cases available; TEST reads = 0; architecture/input/training
  artifacts SHA-bound; no unresolved TRAIN↔VAL leakage; baseline frozen and immutable.
- **`phase21_may_start: false`, `phase21_started: false`, `authorization_required: true`.**
- Phase 21 (Global MedFiLM) must be compared against this baseline on the **same 64**
  deterministically selected VAL cases (`reports/tables/phase20_gallery_selection.csv`).

## P. Terminal state and STOP condition

The Phase-20 STOP condition is satisfied: entry audit · single frozen baseline training · checkpoint
closure/replay · canonical VAL evaluation · advanced evaluation metrics · persisted VAL
predictions/probabilities · full executed notebook · 64-case visualization evidence ·
documentation/registry synchronization · Phase-21 eligibility assessment.

**TERMINAL STATE: `PHASE20_SHARED_GLOBAL_BASELINE_COMPLETE__PHASE21_ELIGIBLE_NOT_STARTED`**

Phase 21 was **not** started.
