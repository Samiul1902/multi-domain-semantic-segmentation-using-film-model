# C1 — Experiment Validity Design Check v1.0

Status: `DESIGN_CHECK_ONLY__NO_MODEL_SELECTION__NO_DATA_ANALYSIS`
No data-derived model selection and no scientific analysis was performed. Every
finding below is a reading of the frozen protocol and implementation.

---

## Summary

| # | Question | Verdict |
|---|---|---|
| 1 | Matched backbone initializations preserved? | **PASS** |
| 2 | Identity FiLM mathematically inactive throughout control training? | **PASS (exact, not approximate)** |
| 3 | Different trainable parameter counts transparently reported? | **PASS** |
| 4 | Primary endpoint exactly defined? | **PASS with one documented ambiguity** |
| 5 | Treatment and control checkpoint-selection rules identical? | **PASS** |
| 6 | Seed variation distinguished from patient/case sampling? | **PASS with a hard limitation** |
| 7 | Selection-consumed VAL808 classified as development evidence? | **PASS** |
| 8 | Worker configuration matches what recovery tests support? | **FAIL — documented limitation** |

---

## 1. Matched backbone initialization — PASS

`build_matched_arms(seed)` constructs **one** `GlobalMedFiLM` under
`torch.random.fork_rng(devices=[])` with `manual_seed(seed)`, then obtains the
control by `copy.deepcopy(treatment)` **before any optimization step**. There is
no second RNG draw, no separate construction path, and no initialization from a
trained treatment checkpoint.

Verification in the test suite:
- `test_all_seed_initial_states_match_without_rng_side_effect` asserts every
  `state_dict` tensor is `torch.equal` between arms for all three seeds, and
  that the ambient CPU RNG state is unchanged by construction.
- `test_initialization_and_optimization_for_both_arms` asserts
  `t.initial_sha256 == c.initial_sha256` for two independently constructed
  `Trainer` instances.
- The CUDA run confirms `initial_sha256` equality on device.

Residual note: `fork_rng(devices=[])` does not fork the CUDA generator, but
model construction happens on CPU and `.to(device)` is a pure copy, so no CUDA
draw occurs during initialization.

## 2. Identity FiLM inactivity — PASS, mathematically exact

`FeatureWiseLinearModulation.output` has **both weight and bias zero-initialised**,
and `reset_parameters()` re-asserts that after the blanket conv init. Therefore
`gamma_raw = 0`, `beta_raw = 0`, `tanh(0) = 0`, and

```
F_hat = (1 + 0) * F + 0 = F
```

This is exact in floating point, not an approximation: multiplying by exactly 1.0
and adding exactly 0.0 is bit-preserving for finite values.

The control arm additionally sets `requires_grad_(False)` on every
`task_embedding.*` and `film_layers.*` parameter, so the zero projections cannot
drift. `verify_identity_control()` re-checks frozen-ness, zero weight, zero bias,
finite gamma/beta, and zero gamma/beta for **all four task IDs at all five
sites** — and it is called every epoch for `C1-C` and again after `restore()`.

`test_full_network_matches_site_bypass_and_ignores_task` proves the full network
output is `torch.equal` to a hook-based FiLM-bypass reference and is identical
across all four task IDs. This is the strongest available form of the claim: the
control is task-blind by construction, not by regularization.

## 3. Trainable parameter transparency — PASS

`parameter_accounting()` returns `total`, `conditioning`, `backbone`,
`trainable`, `frozen`, and `parameter_bytes_fp32`. Values are asserted against
`EXPECTED_COUNTS` at construction and stored in every checkpoint under `counts`.

| Arm | Total | Trainable | Frozen |
|---|---|---|---|
| C1-T | 3,523,001 | 3,523,001 | 0 |
| C1-C | 3,523,001 | 3,432,233 | 90,768 |

The 90,768 conditioning parameters are **2.58%** of total. Because the control's
conditioning tensors are frozen rather than removed, total parameter count is
identical across arms and only the *trainable* count differs — this is reported
and is the correct framing (freezing never reduces total parameters).

## 4. Primary endpoint — PASS with one documented ambiguity

Frozen definition:
`seed_average_of_paired_equal_domain_macro_Dice_T_minus_C_on_selected_VAL`

Fully determined components:
- **Per-image Dice**: `(2·TP + ε)/(2·TP + FP + FN + ε)`, ε = 1e-7, threshold 0.5,
  sigmoid applied first. Empty-GT ∧ empty-prediction therefore scores **1.0**,
  not excluded — a documented, inherited Phase-20 convention.
- **Domain Dice**: unweighted mean over images of that domain.
- **Macro**: unweighted mean of the four domain values,
  `(1/4)·Σ_d mean(dice_d)`. Domains are equal-weighted regardless of size.
- **Paired**: same seed, `C1-T` minus `C1-C`.
- **Seed average**: arithmetic mean of the three paired effects.

**Documented ambiguity:** "selected_VAL" does not state whether the endpoint uses
the stored `best_records` (VAL metrics captured at the selected epoch) or a
recomputed VAL pass from the selected checkpoint. In the current engine these
are the same numbers, because `best_records` *is* the VAL pass at the selected
epoch and no further training follows selection. The distinction becomes
material only if a future release adds post-selection evaluation. This should be
nailed down explicitly before launch, but it does not change any number produced
by the present engine.

**Material validity caveat (not a definition defect):** the endpoint is measured
on the **same VAL808 used to select the checkpoint**. The reported quantity is
therefore the *selection objective itself*, evaluated in-sample. It carries
optimistic selection bias and cannot be read as a generalization estimate. This
is acknowledged by the protocol's `claim_boundary` (see §7), but it means the
effect size is a development-stage estimate only.

## 5. Identical checkpoint-selection rule — PASS

Both arms route through the same frozen function
`src/training/phase20_selection.py`:

- `SELECTION_RULE_ID = "phase20_macro_domain_mean_dice_v1"`
- `TIE_TOLERANCE = 1e-12`
- `is_new_best`: strictly better macro beyond tolerance, else exact tie broken by
  strictly lower `val_loss` beyond tolerance, else not improved
- `TIE_TOLERANCE` and `DOMAIN_ORDER` are shared constants, not per-arm
- `restore()` replays `select_best_epoch(history)` and requires the replay to
  reproduce `best_epoch`, `best_macro`, `best_loss`, and `bad_epochs`, so a
  divergent selection history is rejected rather than silently accepted

There is no arm-conditional branch anywhere in the selection path. The control's
different learning trajectory is an intended consequence of the intervention, not
a difference in the rule.

## 6. Seed variation vs patient/case sampling — PASS with a hard limitation

The two sources are kept structurally separate:

- **Seed variation**: three *fixed* seeds `[42, 123, 3407]`, treated as three
  paired replicates. The protocol explicitly restricts reporting to
  `report_all_three_paired_seed_effects_mean_sample_SD_range_no_population_seed_inference`.
- **Sampling variation**: a domain-stratified paired cluster bootstrap
  (`resamples = 10000`, `bootstrap_seed = 20261027`, 95% percentile), operating
  over *samples*, not seeds.

**Hard limitation:** n = 3 seeds yields a sample SD on 2 degrees of freedom. It
is a descriptive dispersion of three downstream-retraining replicates and cannot
support any population-level inference about seeds. The protocol already forbids
that inference; this is a correct constraint, not a defect.

**Second hard limitation:** `group_rule` requires real `patient_id` only for
**KUB (267 patients)**. For ISIC, BUSI and KVASIR, `patient_id` and source-level
case identifiers are `NOT_AVAILABLE`, so the cluster bootstrap can only be
patient-clustered **inside KUB**. For the other three domains the resampling unit
is the image, which understates uncertainty when multiple images share an
unobserved patient. The protocol requires this to be disclosed rather than
papered over, and it must appear in any downstream write-up.

## 7. VAL808 as development evidence — PASS

`claim_boundary` reads:
`C1_development_selection_consumed_only_not_C2_C3_clinical_safety_or_independent_generalization`

VAL808 is used to select the epoch, and it was already consumed by earlier
phases. It is correctly classified as **development / selection-consumed
evidence**, not as held-out or independent generalization evidence. The frozen
populations are TRAIN 5832 and VAL 808 only; TEST and ROUTER_HOLDOUT are excluded
by contract and by `create_loader`'s own TEST rejection.

## 8. Worker configuration vs recovery-test support — **FAIL (documented limitation)**

This is the one item that does not pass, and it must not be silently changed.

| Setting | Production (`real_loader_factory`) | Recovery tests (`fixture_loaders`) |
|---|---|---|
| train `num_workers` | **4** | **0** |
| eval `num_workers` | **2** | **0** |
| `persistent_workers` | False | False |
| `pin_memory` | default True | False |

Consequences that are **not** covered by the 34 passing tests:

1. **Worker-process determinism is unverified.** On Windows the loader uses
   `spawn`. Four fresh worker processes are created per epoch. Determinism
   depends on `worker_init_fn=seed_worker` plus the per-epoch generator seed
   derived by `derive_epoch_seed(seed, epoch)`. That mechanism is sound in
   design but has never been exercised at `num_workers > 0`.
2. **Dataset picklability is unverified.** `MultiDomainDataset` (carrying a
   pandas frame) must pickle to each worker on every epoch. A pickle failure
   would surface only at first real batch, i.e. after launch.
3. **`loader_states` is audit-only, not reconstructive.** `remember_loader`
   captures `loader.generator` and `sampler.generator` states, but `run()`
   rebuilds each epoch's loader from `derive_epoch_seed(seed, epoch)` rather than
   from the restored generator state. Resume correctness therefore rests on
   epoch-derived seeding, and worker RNG state is never captured at all.
4. **Recovery under `num_workers > 0` is untested.** All interruption, corruption,
   pointer-escape, and mid-epoch-replay tests run with `num_workers = 0`.

This limitation is **documented, not fixed**. Fixing it means adding a synthetic
recovery test at the production worker configuration — that is an additive test,
not a study-design change, and it belongs to the launch release (§4 of the
launch-boundary design), not to this readiness task.

---

## Design changes made

**None.** No batch size, resolution, learning rate, optimizer, scheduler, AMP
setting, seed, arm definition, population, selection rule, threshold, or
augmentation was altered. Every finding above is either a confirmation or a
documented limitation.
