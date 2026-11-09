# Phase C — Unified Evaluation and Statistical Analysis (CODING ONLY)

**Target:** `PHASE_C_EIGHT_MODEL_EVALUATION_CODE_COMPLETE__24_CELL_SYNTHETIC_MATRIX_PASS__METRICS_STATISTICS_VERIFIED__REAL_RESULTS_NOT_STARTED`

**Status:** code complete and verified on synthetic fixtures. **No real model was trained, no VAL808
image was scored, and TEST1683 was never opened.** Real results are `NOT_STARTED`.

**Machine:** RTX 3060 Ti (8 GB), torch 2.6.0+cu124, Python 3.11.9, `.\.venv\Scripts\python.exe`.

---

## 1. Existing implementations read before writing anything

Read, not assumed: `src/research/full_pipeline/` (recipe, context, population, inference, provenance,
seeds), `src/research/lite_pipeline/` (recipe, context, features, inference, orchestrator, strict_oof),
`src/research/stage6/{matrix,end_to_end,evaluate}.py`, `src/models/{film/global_medfilm,
barr/ra_medfilm_barr, barr/regional_refiner, barr/phase25_models, lite/ra_medfilm_barr_lite}.py`,
`src/metrics/{segmentation,evaluation_metrics}.py`, `src/research/c3_baselines/experiment.py`,
`src/data/transforms.py`, the Phase-4 v3 manifests, and
`docs/phase30_final_development_validation_spec_v1_3.md`.

**Nothing was forked that already existed.** FULL and Lite training behaviour is untouched: no file
outside `src/research/evaluation/` was modified in this phase.

## 2. The unified eight-model evaluator

`src/research/evaluation/adapters.py` — one interface (`load` / `predict(image, task_id)` /
`parameter_count` / `identity`) over three genuinely different adapter kinds:

| Kind | Models | What it invokes |
|---|---|---|
| `ROUTED` | RA-MedFiLM-BARR FULL, Lite `depthwise_compact` | the complete G/R/B/S graph through `stage6.end_to_end.GTFreeBARRInference` |
| `TASK_CONDITIONED` | GlobalMedFiLM | the real task-conditioned network, called with its task id |
| `PLAIN` | U-Net, Attention U-Net, U-Net++, DeepLabV3+, Transformer/MiT U-Net | a single segmentation network, **no task input** |

Identifiers come from `stage6.matrix.MODEL_KEYS` and `c3_baselines.experiment.ARCHITECTURES`; no model
name was invented. 8 models × seeds 42/123/3407 = **24 cells**.

`PLAIN` is deliberately not given a task id. Feeding one would be a protocol change, not a fairness
correction — the baselines are not task-conditioned architectures.

**Fixture caveat that matters:** a freshly initialised FiLM network has a zero-initialised γ/β out-proj,
so at initialisation the task conditioning is an *identity* and outputs are identical across task ids.
That is expected, and it is **not** evidence the task id is ignored. Check 2 therefore verifies the id
reaches the network (spying on the call) rather than comparing outputs.

## 3. Evaluation integrity

- Populations asserted from the manifests on every `validate`: TRAIN **5832**, VAL **808**, TEST **1683**,
  ROUTER_HOLDOUT **875**, external **884**; TRAIN = 4957 + 875.
- `VAL808` is stamped `VAL808_DEVELOPMENT_SELECTION_CONSUMED__NOT_INDEPENDENT_CONFIRMATION` and is never
  presented as fresh independent confirmation.
- `TEST1683` is structurally unreachable: `protocol.assert_split_readable` raises before a single file is
  opened; `ProtectedSplitGuard` counts reads and refusals; measured `test_reads = 0`.
- Inference is ground-truth-free by construction and the property is re-checked on the live signatures
  (`audit_gt_free`, `audit_ground_truth_free`), not asserted in prose.
- No model selects a threshold or checkpoint from a protected result; no threshold was tuned at all.
- Preprocessing is a single declared identity (`phase4_v3_resizepad_512_rgb_bilinear_mask_nearest_v1`)
  with a SHA-256 in every provenance block; no model gets a different transform to look fair.

## 4. Metrics engine

`metrics.py` is a **façade** over `src.metrics.evaluation_metrics` — no Dice coefficient is re-derived.

Dice, IoU, Precision, Recall, Specificity, HD95, per-domain n, and
`equal_domain_macro_dice` (unweighted mean of the four domain means, the protocol headline). Three
aggregation levels are kept apart and never substituted: `PER_IMAGE`, `PER_DOMAIN`, `POOLED`.

Edge cases each have a stated convention and a known-answer fixture: empty GT + empty prediction,
empty GT + non-empty prediction, non-empty GT + empty prediction, all-foreground, disconnected
predictions, non-square originals, absent pixel spacing, non-finite probabilities
(`on_non_finite="raise"` or `"mask"`, counted either way).

**HD95 units are disclosed.** The KUB corpus records no physical pixel spacing, so every distance is in
**pixels** (`hd95_unit="pixel"`), `hd95_mm` is `None`, and an empty mask yields *undefined*, never 0.
A millimetre value is produced only when a caller supplies spacing.

Eight independently hand-derived fixtures pass: `identical_2x2_block`, `shifted_one_pixel`,
`gt_empty_pred_empty`, `gt_empty_pred_nonempty`, `gt_nonempty_pred_empty`, `all_foreground`,
`disconnected_prediction`, `non_square_shape`. The comparison tolerance is 1e-6 because the engine
applies its declared `eps = 1e-7` inside every ratio; the expected values remain the exact fractions.

## 5. Paired comparisons

`stats.py`. Exact image pairing is enforced: `pair_records` raises on a set mismatch rather than
performing a silent inner join, and raises on a duplicate `sample_id`. Reordering one cell does not change
the answer. Seed identity is carried explicitly.

When a `patient_id`/`group_key` exists the bootstrap resamples **clusters**, not images; a missing
identifier raises instead of quietly falling back to images (which would understate the interval).
Measured: on 4 patients × 5 images the cluster interval is strictly wider than the image interval.

**Inference class.** Every comparison is `EXPLORATORY_UNCERTAINTY_ONLY`. `p_value` is `None` and
`confirmatory_authorized` is `False`, because no frozen statistical protocol defines a confirmatory test
for this comparison; `docs/phase30_final_development_validation_spec_v1_3.md` §B sets
`no_p_value_gating_for_primary = true` and §C scopes the non-inferiority bound (`lower 95% CI > -0.005`)
to the preservation claim only. The bound is exposed only with an explicit `protocol_reference`, and it is
not a test against zero. `claim_status` stays `NO_CLAIM`; a CI excluding zero is reported as a
*descriptive difference*, never an improvement.

## 6. Accuracy–efficiency analysis

`efficiency.py`. Unique inference parameter count; Conv/Linear MACs via hooks (comparable across
architectures) kept separate from `FlopCounterMode` total FLOPs (which includes attention matmuls);
conditional refiner invocation rate; GPU peak allocated/reserved memory; model latency; end-to-end
pipeline latency; throughput.

Conditions recorded with every number: RTX 3060 Ti, 512 px, batch 1, float32, warm-up 3, repeats 20, CUDA
synchronised around each timing, `time.perf_counter` around the full forward pass.

Measured at the 512 contract shape (synthetic weights, so the *timings* are machine properties, not method
properties):

| Model | Params | G MACs | Always-refine | Effective | p50 | Peak |
|---|---|---|---|---|---|---|
| FULL | 4,837,420 | 31.552 G | 34.782 G | 34.782 G | 107.3 ms | 328.7 MiB |
| GlobalMedFiLM | 3,523,001 | 31.552 G | — | — | 18.1 ms | 298.6 MiB |
| Lite | 272,601 | 1.619 G | 1.820 G | **1.619 G** | 55.3 ms | 203.7 MiB |
| U-Net | 7,763,041 | 46.137 G | — | — | 14.3 ms | 260.6 MiB |
| Attention U-Net | 7,851,285 | 47.219 G | — | — | 15.7 ms | 320.7 MiB |
| U-Net++ | 9,159,681 | 137.942 G | — | — | 37.7 ms | 689.0 MiB |
| DeepLabV3+ | 40,347,041 | 69.139 G | — | — | 18.4 ms | 284.5 MiB |
| Transformer/MiT | 16,347,777 | 17.573 G | — | — | 15.4 ms | 186.9 MiB |

**Fewer refiner calls is not by itself a lower total cost**, and the table shows it rather than implying
it: Lite at seed 42 invoked the refiner on 0 of 12 images, so its effective cost (1.619 G) is below its
always-refine cost (1.820 G); FULL invoked it on all 12 at every seed, so its effective cost equals the
always-refine cost. The routing table carries that warning in a `note` column.

The local Conv/Linear counter is asserted to agree **exactly** with the canonical
`analytical_macs_lower_bound` on the same model (46,137,344,000 both ways), so the two cannot silently
diverge. `total_flops ≥ 2 × conv-MACs` holds.

## 7. Provenance and the 24-cell registry

`provenance.py`. Each cell carries model identity, seed, adapter kind and identity, checkpoint/component
SHA-256, upstream chain, split and split semantics, split-manifest SHA-256, preprocessing id and hash,
metric implementation version, evaluation configuration and its hash, evidence class and label, hardware,
statistics policy, and `test_reads = 0`.

- Dependencies are verified before inference; an absent, partial or incompatible family is rejected
  (`AdapterUnavailable` / `FileNotFoundError` on the missing component), never replaced by random weights.
- Publication is atomic: temp file → `fsync` → `os.replace`; `cell_result.json` is written **last**, so a
  cell is not complete until it exists.
- Interruption is safe: the ledger records every scored sample, a resumed pass merges prior records in
  roster order, and publication re-checks the roster. A torn ledger line is discarded; if a torn append
  swallowed the following record, the next pass re-scores exactly that sample rather than publishing a gap.
- The registry keeps all 24 cells `NOT_ESTABLISHED`. `research_cells_completed` is 0 and synthetic
  success cannot change it: `RESEARCH_EVIDENCE_CLASSES = {REAL_VAL808_DEVELOPMENT}` only.

## 8. Report generators

`reports.py` writes nine tables, each carrying `evidence_class`, plus a manifest that states the banner
in words. Synthetic → `SYNTHETIC_TEST_ONLY … not research results … must not appear in the manuscript`.
Real → `REAL_VAL808_DEVELOPMENT — development/selection-consumed`. No cells → `NO_EVIDENCE`. Mixed →
`MIXED_EVIDENCE`. Nothing here writes into the manuscript.

## 9. CLI

`scripts/analysis/phase_c_evaluate.py` → `src/research/evaluation/cli.py`. Nine subcommands:
`validate`, `plan`, `dry-run`, `evaluate`, `resume`, `verify-results`, `aggregate`, `profile`, `report`.
No institutional gate is bypassed or altered. Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe scripts\analysis\phase_c_evaluate.py validate
.\.venv\Scripts\python.exe scripts\analysis\phase_c_evaluate.py plan
.\.venv\Scripts\python.exe scripts\analysis\phase_c_evaluate.py dry-run --root runs\phase_c_matrix --device cuda --per-domain-val 3
.\.venv\Scripts\python.exe scripts\analysis\phase_c_evaluate.py verify-results --root runs\phase_c_matrix\cells
.\.venv\Scripts\python.exe scripts\analysis\phase_c_evaluate.py profile --root runs\phase_c_matrix --device cuda --source synthetic --warmup 3 --repeats 20
.\.venv\Scripts\python.exe scripts\analysis\phase_c_evaluate.py aggregate --root runs\phase_c_matrix\cells --out runs\phase_c_matrix\results.json
.\.venv\Scripts\python.exe scripts\analysis\phase_c_evaluate.py report --root runs\phase_c_matrix\cells --out reports\tables\phase_c
```

Real path (refused today — no checkpoint family exists):

```powershell
.\.venv\Scripts\python.exe scripts\analysis\phase_c_evaluate.py evaluate --source real --split VAL --root runs\c1_family --device cuda
.\.venv\Scripts\python.exe scripts\analysis\phase_c_evaluate.py resume   --source real --split VAL --root runs\c1_family --device cuda
```

`--split TEST` exits before resolving a path.

## 10. The eighteen synthetic integration checks

`tests/test_evaluation_phase_c.py` — 19 passed, 1 skipped by default.

| # | Check | Result |
|---|---|---|
| 1 | All eight adapters instantiate | PASS — 3 distinct kinds; params match instantiated models |
| 2 | All four task ids work where supported | PASS — id verified to *reach* FULL/GLOBAL; PLAIN ignores it |
| 3 | All 24 registry entries recognised | PASS — 24 distinct cells; chains `(G,R_psi,B_phi,S_omega)` / `(G,)` / `()` |
| 4 | FULL conditional inference | PASS — real state mix; refiner branch executed |
| 5 | Lite conditional inference | PASS — tap forward, 272,601 params |
| 6 | GT never reaches inference | PASS — spy proves no mask in any inference call |
| 7 | Metrics vs known answers | PASS — 8 fixtures + independent hand arithmetic |
| 8 | Checkpoint mismatches fail | PASS — 7 rejection paths |
| 9 | Missing models marked missing | PASS — 24 MISSING, 0 estimated |
| 10 | Partial exports not complete | PASS — short roster, duplicates, empty, tampered |
| 11 | Seed comparisons preserve pairing | PASS — set mismatch and duplicates raise |
| 12 | Missing seeds/groups handled | PASS — raises, degenerate CI NaN, NOT_AVAILABLE |
| 13 | Accuracy–efficiency units | PASS — 3 distinct units; counter agrees exactly |
| 14 | Reports distinguish synthetic | PASS — banner, 0 p-values, `NOT_ESTABLISHED_0_OF_24` |
| 15 | Repeat execution deterministic | PASS — byte-identical `per_image.csv` |
| 16 | Interrupted evaluation resumes | PASS — merge, no duplicates, both tear modes |
| 17 | Protected TEST1683 never read | PASS — `test_reads = 0`, no image opened |
| 18 | Existing training tests pass | PASS — 1 passed in 183.6 s with `PHASE_C_RUN_TRAINING_REGRESSION=1` |

**24-cell matrix:** 24/24 executed, 0 failed, 24 `COMPLETE_VALIDATED`, `research_cells_completed = 0`,
evidence `SYNTHETIC_TEST_ONLY`, `test_reads = 0`.

## 11. Regression verification

- `tests/test_evaluation_phase_c.py`: **19 passed, 1 skipped**.
- Test 18 with the env var set: **1 passed in 183.59 s** (Lite + FULL suites green).
- Full suite: **1057 passed, 1 failed, 1 skipped, 1 xfailed, 29 subtests passed** in 952 s.

**The single failure is the known environment-dependent RC2 trust-store case, preserved unchanged:**
`test_c1_launch_rc2::test_default_production_store_is_absent` expects
`C1_RC2_TRUST_STORE_MISSING_OR_SYMLINK` and observes `C1_RC2_SIGNATURE_KEY_UNTRUSTED`, because
`%ProgramData%\InstitutionalC1Trust` exists on this host. It is a host-state fact, not a code defect. No
trust material was read, rewritten or removed, and no test was weakened.

**Harness note:** `pytest tests/` on this host must be given `--basetemp`. Without it, pytest's numbered
temp-root rotation bulk-deletes ~155 stale directories, which this host's safe-delete guard blocks,
turning a *fully passing* run into exit code 1. The training-regression subprocess passes `--basetemp`
for that reason; its assertions were not relaxed.

## 12. Fourteen deliverables

1. `src/research/evaluation/protocol.py` — frozen populations, protected splits, evidence classes, threshold roles, metric definitions.
2. `src/research/evaluation/registry.py` — the eight canonical keys, adapter kinds, 24 cells, architecture identity.
3. `src/research/evaluation/adapters.py` — the three adapter kinds, real/synthetic loading, GT-free audit.
4. `src/research/evaluation/metrics.py` — metric façade, HD95 units, edge-case contracts, 8 known-answer fixtures.
5. `src/research/evaluation/stats.py` — pairing, cluster bootstrap, seed summary, non-inferiority gate, no p-values.
6. `src/research/evaluation/efficiency.py` — parameters, conv/linear MACs vs total FLOPs, conditional cost, latency, memory, declared conditions.
7. `src/research/evaluation/provenance.py` — provenance block, atomic publication, progress ledger, cell/matrix verification.
8. `src/research/evaluation/runner.py` — sample loading, split guard, the GT-free-then-score loop, cell/matrix execution, resume merge.
9. `src/research/evaluation/reports.py` — the nine tables, evidence banners, registry status.
10. `src/research/evaluation/cli.py` + `scripts/analysis/phase_c_evaluate.py` — nine subcommands.
11. `tests/test_evaluation_phase_c.py` — the eighteen checks plus CLI and registry invariants (19 passed, 1 gated).
12. Synthetic 24-cell matrix results: 24/24 executed, 0 failed, 0 research cells completed.
13. Regression verification: 1057 passed, 1 known RC2 host-state failure preserved.
14. This report. Scoped commit contains only the twelve task-owned files above.

## 13. What is NOT done — stated plainly

- **No real model was trained.** No FULL or Lite checkpoint family exists to evaluate.
- **No VAL808 image was scored.** `research_cells_completed` is 0 of 24; the registry is `NOT_ESTABLISHED_0_OF_24`.
- **TEST1683 was never opened.** Measured `test_reads = 0`.
- **No p-value exists and none may be produced** without a frozen confirmatory procedure.
- **No synthetic number in this report is a result.** Every one comes from untrained fixtures and is
  stamped `SYNTHETIC_TEST_ONLY`.
- The known RC2 trust-store failure remains, untouched, as a recorded host-state fact.
