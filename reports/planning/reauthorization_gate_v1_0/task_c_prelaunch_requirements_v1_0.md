# Task C — Strict Scientific Prelaunch Requirements

**Classification:** `RA_MEDFILM_BARR_PRELAUNCH_REQUIREMENT_CONTRACT`
**Version:** 1.0
**Prepared local:** 2026-10-26T22:48 (+06:00)
**Mode:** governance only. This document defines requirements; it authorises nothing and executes nothing.

**Scope.** Every proposed experiment in this gate (C1, C2a, C2b, C3/EXT-03B) must satisfy **all ten** requirements below before launch. A requirement that cannot be demonstrated is a **blocking failure**, not a waived item.

Each requirement states: what it demands, how it is verified mechanically, the failure mode it exists to prevent (with EXT-03 evidence where available), and the fail-closed code a gate must emit.

---

## R1 — Signed or explicitly documented scientific authorization

**Demand.** A written authorisation that names the experiment, its identifier, its scope, its seeds, its population, and its explicit exclusions. It must be attributable to a named supervisor and dated. An oral instruction, a chat message, or an implied consent from a prior phase is not sufficient.

**Mechanical verification.** The gate reads an authorization artifact and requires: non-empty `authorization_id`, named `authorized_by`, ISO-8601 `authorized_at`, `scope` matching the harness's own declared scope, and an explicit `exclusions` list. Absent any field ⇒ abort.

**Failure mode prevented.** EXT-03 began training five days after `ext03_pretraining_acceptance.json` returned `all_pass: false` with an explicit *"STOP BEFORE FULL SCIENTIFIC TRAINING"* decision. No authorization artifact names the divergent recipe.

**Fail-closed code.** `E_AUTHORIZATION_ABSENT` · `E_AUTHORIZATION_SCOPE_MISMATCH` · `E_AUTHORIZATION_EXCLUSION_VIOLATED`

---

## R2 — Frozen executable protocol and frozen data population

**Demand.** Before the first training step, the exact recipe and the exact populations are frozen by digest: optimizer class and hyperparameters, loss and its weights, augmentation operations and probabilities, input channels and resolution, batch size, schedule, epoch ceiling, patience, selection metric and tie-break, threshold — plus TRAIN and VAL manifest digests and counts.

**Mechanical verification.** A `resolved_protocol.json` is written once (`O_EXCL`) and its SHA recorded. The harness must load its configuration **from** that artifact, not merely report it. Population manifests are bound by SHA and their sample counts re-verified at load.

**Failure mode prevented.** EXT-03's resolved protocol was written before training but was never the thing the harness read — the harness hard-coded Adam/1e-3/BCE-only/no-augmentation at L50, L137, L190 and L84–98 while the resolved artifact described something else.

**Fail-closed code.** `E_PROTOCOL_UNFROZEN` · `E_PROTOCOL_NOT_LOADED_FROM_FROZEN` · `E_POPULATION_SHA_MISMATCH` · `E_POPULATION_COUNT_MISMATCH`

---

## R3 — Direct source-to-authority field comparisons

**Demand.** The gate must contain **at least one edge that reads the frozen authority directly** and compares a **concrete value** against what the harness will actually execute. Comparing a derived artifact to another derived artifact does not satisfy this.

Required concrete comparisons, minimum set: optimizer class name, learning rate, weight-decay, loss function name, loss component weights, augmentation operation count and each probability, input channel count, batch size, epoch ceiling, patience, threshold.

**Mechanical verification.** For each field: parse the authority (`configs/**/*.yaml` and the historical trainer), parse the harness's effective value, compare literally, and record `{field, authority_value, harness_value, equal}`. Any `equal: false` without a matching written divergence authorization ⇒ abort. Comparing digests instead of values is an automatic failure.

**Failure mode prevented.** The Stage B gate recorded `training_protocol_sha = 1d456f9f…`, which is exactly the SHA-256 of `ext03_training_protocol_resolved.json` — so it compared the harness to a derived artifact and **never** compared that artifact to the phase09/10 authority. The chain S1→S3 and S2→S1 formed a closed loop with no edge to the authority: mutually consistent, jointly wrong.

**Fail-closed code.** `E_NO_AUTHORITY_EDGE` · `E_AUTHORITY_FIELD_MISMATCH` · `E_DIGEST_COMPARISON_SUBSTITUTED_FOR_VALUE_COMPARISON`

---

## R4 — Exact training-harness SHA binding

**Demand.** The digest of the harness that will actually execute must be recorded in the prelaunch artifact, per run, and re-verified at launch. "A harness was frozen" is not sufficient if a different harness runs.

**Mechanical verification.** At launch the runner computes its own raw-byte SHA, compares it to the authorized digest, and aborts on mismatch. The digest is written into every run's registry entry.

**Failure mode prevented.** `ext03r_run_harness_freeze.json` recorded `7c7287d7…` as the frozen harness; the harness that actually executed the first runs was `bcdbada2…`. The Stage B prelaunch artifact recorded **no `harness_sha` at all**. The transition is undocumented and no per-run harness digest exists anywhere.

**Fail-closed code.** `E_HARNESS_SHA_ABSENT` · `E_HARNESS_SHA_MISMATCH` · `E_HARNESS_NOT_BOUND_AT_LAUNCH`

---

## R5 — Total and trainable parameter-count checks

**Demand.** For every arm, both **total** and **trainable** parameter counts must be measured at runtime and compared against pre-declared expectations. Where arms differ in parameterization (frozen vs removed modules), the expected values for **each design** must be declared before launch.

**Mechanical verification.** Instantiate each model, compute `sum(p.numel() for p in model.parameters())` and the same over `p.requires_grad`, compare to declared integers. For C1 the declared expectations are: **F1 total 3,523,001 / trainable 3,432,233**; **F2 total 3,432,233 / trainable 3,432,233**. Mismatch ⇒ abort.

**Failure mode prevented.** `ext03r_param_verification.json` records 1-channel counts (unet 7,762,465) and asserts `all_match: true`, while the executed models were 3-channel (7,763,041). It certifies a configuration that never ran. Separately, the harness's own `PARAMS` guard had been re-baselined to the drifted values, so it could never detect the drift.

**Fail-closed code.** `E_PARAM_TOTAL_MISMATCH` · `E_PARAM_TRAINABLE_MISMATCH` · `E_PARAM_EXPECTATION_NOT_DECLARED`

---

## R6 — Prespecified seed policy

**Demand.** The seed set must be declared before launch and fixed: which seeds, how many, and what claim the count supports. A single seed supports a point estimate only and must be labelled as such in advance — not after seeing the result.

**Mechanical verification.** Gate requires `seeds: [...]` with length ≥ 1 and, for any claim of an effect, either `len(seeds) >= 3` or an explicit `single_seed_limitation: true` field. The registry must contain exactly those seeds and no others.

**Failure mode prevented.** EXT-03's seed set was fixed (42/123/3407) and held, which is a genuine strength. The failure it exposes is downstream: three seeds yield a sample SD with 2 degrees of freedom, and EXT-03 contains no confidence interval, no significance test and no confirmatory comparison — a limitation that must be declared up front rather than discovered in review.

**Fail-closed code.** `E_SEED_POLICY_ABSENT` · `E_SEED_SET_MISMATCH` · `E_SINGLE_SEED_CLAIM_UNLABELLED`

---

## R7 — Checkpoint and complete epoch-log persistence

**Demand.** Every run must persist, per epoch, a durable log line containing at minimum epoch index, train loss, validation metric, current best metric, best epoch, and the bad-epoch counter — plus a `latest.pt` and a `best.pt`. Selection metadata in `latest.pt` must be written **after** the selection decision it describes.

**Mechanical verification.** At completion the gate checks: `best.pt` exists and its SHA matches the registry; `latest.pt` exists; an epoch log exists with exactly `current_epoch` lines; and `latest.pt['bad'] == current_epoch − best_epoch` exactly. The registry's `log_path` must resolve to a real file.

**Failure mode prevented.** Two distinct EXT-03 defects. (a) `latest.pt` was written **before** the selection update, so the bad counter lagged by exactly one epoch (D97) — detectable as a one-low counter. (b) **Six of fifteen runs have no epoch log anywhere**, permanently `MISSING_FROM_AVAILABLE_ARTIFACTS`; the registry's `log_path` dangles for **15/15**.

**Fail-closed code.** `E_CKPT_ABSENT` · `E_CKPT_SHA_MISMATCH` · `E_EPOCH_LOG_ABSENT` · `E_EPOCH_LOG_LENGTH_MISMATCH` · `E_SELECTION_METADATA_LAG` · `E_REGISTRY_LOG_PATH_DANGLING`

---

## R8 — Positive and negative gate controls

**Demand.** The gate must be demonstrated to **fail** when it should. A gate that has only ever been observed to pass is not evidence of a working gate.

**Mechanical verification.** A self-test battery that injects known faults and asserts the specific failure code: absent digest, malformed digest, wrong digest, alias-key substitution, missing run, extra run, absent checkpoint, drifted frozen artifact, second write to a write-once output. Each case must abort with its named code. **A pass-through on any negative case is itself a release blocker.**

**Failure mode prevented.** The v1.1 manifest's Section C reported `registry_sha256 = null` with `match = true` for all fifteen checkpoints, because the comparison was `ok = (exp is None) or (actual == exp)` — fail-open on an absent reference. The conclusion happened to be correct; the check never established it. This is the second occurrence of the same shape in this project (the v1.0 generator had `if recorded and actual != recorded:`).

**Fail-closed code.** `E_NEGATIVE_CONTROL_NOT_FAILING` · `E_GATE_NEVER_OBSERVED_FAILING`

---

## R9 — Separated development-validation and independent-evidence claim boundary

**Demand.** The document must state, before launch, which population each metric will be computed on and **what claim that population can support**. Development-validation results are selection-contaminated by construction and may be reported only as descriptive decompositions, never as held-out performance.

**Mechanical verification.** Gate requires an explicit `claim_boundary` block naming: the development population and its digest, the fact that it is the selection set, the permitted claim class (`DESCRIPTIVE_DEV`), and the prohibited claim classes (`HELD_OUT`, `CONFIRMATORY`, `GENERALISATION`). Any downstream metric computed on the selection set without the `DESCRIPTIVE_DEV` label ⇒ abort.

**Failure mode prevented.** VAL808 is the checkpoint-selection set for all fifteen EXT-03 runs (equal-domain macro Dice, patience 15). Any per-domain or secondary metric computed from those checkpoints on VAL808 is a **decomposition of a selection-contaminated number**, not independent validation. The same applies to the Phase-29 +0.00282 delta.

**Fail-closed code.** `E_CLAIM_BOUNDARY_ABSENT` · `E_DEV_METRIC_LABELLED_HELD_OUT` · `E_SELECTION_SET_USED_AS_INDEPENDENT`

---

## R10 — No protected TEST access, no unapproved external inference

**Demand.** TEST is PHASE39-only. ROUTER_HOLDOUT is locked. External inference requires separate approval. No proposed experiment in this gate may read any of them.

**Mechanical verification.** Enumerated access statements (not literals): the gate records the exact list of files and manifests opened, and aborts on any path matching the protected markers. Read counters must be zero before launch and must remain zero at completion.

**Failure mode prevented.** EXT-03 correctly never read TEST — `TEST_accessed = false` and `ROUTER_HOLDOUT_accessed = false` are genuinely true and were verified. This requirement exists to keep that property true as the harness is rebuilt.

**Fail-closed code.** `E_TEST_ACCESS` · `E_ROUTER_HOLDOUT_ACCESS` · `E_EXTERNAL_INFERENCE_UNAPPROVED` · `E_ACCESS_STATEMENT_NOT_ENUMERATED`

---

## Release checklist

An experiment may launch only when **all ten** rows are `PASS` and the negative-control battery is green.

| # | Requirement | C1 | C2a | C2b | C3 / EXT-03B |
|---|---|---|---|---|---|
| R1 | Documented authorization | ☐ | ☐ | ☐ | ☐ |
| R2 | Frozen protocol + population | ☐ | ☐ | ☐ | ☐ |
| R3 | Direct authority edge | ☐ | ☐ | ☐ | ☐ |
| R4 | Harness SHA bound per run | ☐ | ☐ | ☐ | ☐ |
| R5 | Total + trainable param check | ☐ | ☐ | ☐ | ☐ |
| R6 | Prespecified seed policy | ☐ | n/a (frozen components) | n/a | ☐ |
| R7 | Checkpoint + full epoch log | ☐ | ☐ | ☐ | ☐ |
| R8 | Positive + negative controls | ☐ | ☐ | ☐ | ☐ |
| R9 | Claim boundary separated | ☐ | ☐ | ☐ | ☐ |
| R10 | No TEST / external access | ☐ | ☐ | ☐ | ☐ |

**Every box is currently empty.** No experiment in this gate has passed any requirement, because none has been authorized or built.

---

## Additional structural constraint

**No experiment may be added retrospectively to a frozen study.**

- Phase-28 sets `post_hoc_factor_addition_forbidden: true` ⇒ **C1 cannot be an A0–A8 / R1–R3 / F1 arm**, and **C2b cannot be added** to the 13-arm contract (which in any case contains no `S_omega`-absent arm).
- EXT-03 is **COMPLETE and frozen** ⇒ C3 cannot be run "inside EXT-03"; it requires its own identifier (**`EXT-03B`**, provisional).
- **EXT-04 remains reserved** for AS-01/02/03/04/05/07 progression and scaling and must not be reused.
- **AS-08 remains UNRESOLVED** until a protocol-faithful baseline study completes and is separately adjudicated.

---

*End of Task C. Governance only: no authorization granted, no gate built, no training launched.*
