# Phase 29 --- Three-Seed Deterministic Reproducibility Study

**Specification revision:** `ra_medfilm_barr_phase29_repro_v1_1`

**Classification:** `SUPERVISOR_PROSPECTIVE_REPRODUCIBILITY_SPECIFICATION_REPAIR`

**Method:** RA-MedFiLM-BARR

**Generated (UTC):** 2026-10-02T15:05:09+00:00

---

## 0. Governance statement

This document is the canonical prospective provenance source for Phase 29. It is
declared as such by
`notebooks/phasewise/phase_29_3seed_reproducibility/README.md`.

This specification was authored **before any Phase 29 science was executed**.

| Field | Value |
|---|---|
| `science_executed_before_ruling` | `false` |
| `seed_results_seen` | `false` |
| `science_changed` | `false` |
| `canonical_bundle_changed` | `false` |
| `governance_only` | `true` |
| `execution` | `NONE` |

This repair is purely prospective. It resolves the six blockers reported by the
Phase 29 v1.0 pre-execution audit
(`PHASE29_BLOCKED__REPRODUCIBILITY_TRAINING_SCOPE_UNRESOLVED`). That blocked
terminal and all v1.0 audit artifacts are preserved unchanged as historical
provenance.

---

## 1. Authoritative seeds

```
MASTER_SEEDS = [42, 123, 3407]
```

* Primary source: `configs/research_protocol.json`
  (`policies.multi_seed`), SHA-256
  `df4b137f613f0f30a2efd244f096934e75e0898a9f4f43df08e5c0554b711212`.
* Supporting source: `reports/audits/research_protocol.md` ("Seeds: 42, 123, 3407"),
  SHA-256
  `f0dc4cd03df7d01fd237331b6c798330847fc85c8c2f09b8dee3368dbdbd64f4`.

The seeds are frozen. They are **not** to be changed, and no replacement seed may
be selected on the basis of training behaviour.

---

## 2. Training scope ruling

Phase 29 measures the reproducibility of the learned BARR regional/routing stack
**conditioned on the frozen canonical global representation**.

```
G / GlobalMedFiLM      = REUSE_CANONICAL_FIXED_ACROSS_ALL_SEEDS
R_psi / RegionalRefiner = THREE_SEED_REPRODUCIBILITY_IN_SCOPE
B_phi / BenefitRouter   = THREE_SEED_REPRODUCIBILITY_IN_SCOPE
S_omega / PostSafety    = THREE_SEED_REPRODUCIBILITY_IN_SCOPE
Phase26 wrapper / fusion = DETERMINISTIC_FIXED_CONFIGURATION
```

**Classification:** `MODULEWISE_DOWNSTREAM_REPRODUCIBILITY_WITH_CANONICAL_FIXED_GLOBAL`

Phase 29 must **not** be described as retraining the entire RA-MedFiLM system.

**Preferred manuscript wording:**

> "Three-seed reproducibility of the BARR stack conditioned on the frozen
> GlobalMedFiLM reference."

---

## 3. Why G is fixed

1. `G` is an upstream frozen reference established in Phase 21.
2. The Phase 29 scientific focus is reproducibility of the BARR conditional
   regional mechanism.
3. Faithfully retraining canonical `G` would require reproducing its original
   training-population semantics, which **predate** the
   `ROUTER_DEVELOPMENT` / `ROUTER_HOLDOUT` split.
4. Phase 29 must preserve the Phase 30 one-shot `ROUTER_HOLDOUT` lock.
5. Holding `G` fixed also isolates downstream stochastic variability instead of
   conflating it with global-backbone variability.

```
global_seed_variance_measured          = false
BARR_stack_seed_variance_measured      = true
```

This is a **scope statement**, not a weakness to hide.

---

## 4. Seed-42 reuse ruling

Existing seed-42 canonical downstream artifacts qualify as the first Phase 29
replicate. The audit verified, for each of `R_psi`, `B_phi`, `S_omega`:

```
protocol_exact_match  = true
population_exact_match = true
split_exact_match      = true
training_rule_exact_match = true
```

Frozen:

```
seed42_role = REUSE_EXISTING_CANONICAL_REPLICATE
```

Reused (SHA-bound):

| Evidence | Source |
|---|---|
| R_psi OOF + final | Phase25A seed42 |
| paired outcomes | Phase25C seed42 |
| B_phi OOF + final | Phase25D seed42 |
| S_omega OOF + final | Phase25F seed42 |
| integrated DEV evidence | Phase25G seed42 |
| VAL808 continuity evidence | Phase27 seed42 |

**Seed 42 is not retrained.** Seed-42 science is not rerun merely to produce
Phase29-branded files.

---

## 5. New seeds

Only seeds **123** and **3407** require new scientific training. They use the
same architecture, population membership, cross-fit partitions,
`FIT` / `EARLY_STOP` / `OUTER_TARGET` identities, losses, optimizer
hyperparameters, scheduler, checkpoint criterion, and threshold definitions as
canonical seed 42.

**The intended variable is `TRAINING_RANDOMNESS_ONLY`.**

---

## 6. Split rule

```
data_split_rule = FIXED_MEMBERSHIP_ACROSS_SEEDS
```

All dataset membership is identical across all three seeds. The following are
**not** regenerated:

* Phase19 `TRAIN` / `VAL` membership
* `ROUTER_DEVELOPMENT` membership
* `ROUTER_HOLDOUT` membership

No partition variance is introduced.

---

## 7. Cross-fit fold rule

Exact seed-42 cross-fit membership is frozen for every seed.

* **R_psi** --- reuse the exact Phase25A three outer folds: same `FIT` rows,
  same `EARLY_STOP` rows, same `OUTER_TARGET` rows.
* **B_phi** --- reuse the exact Phase25D five outer folds: same inner
  `FIT`/`ES` roles, same `OUTER_TARGET` rows.
* **S_omega** --- reuse the exact Phase25F five-fold manifests: same `FIT`,
  same `EARLY_STOP`, same `OUTER_TARGET`.

Folds are **not** regenerated using master seed 123 or 3407.

**Classification:** `FIXED_PARTITIONS__OPTIMIZATION_RANDOMNESS_ONLY`

This is load-bearing for interpreting across-seed variance.

---

## 8. Fixed global artifacts

For all seeds, reuse canonical:

* GlobalMedFiLM checkpoint
* global probability caches where scientifically compatible
* Phase25B 202-D GT-free feature matrix
* Phase25B feature schema

Because `G` is fixed, the pre-refinement router input features are also fixed.

```
feature_regeneration_rule = REUSE_PHASE25B_FEATURES_IDENTICALLY_ACROSS_SEEDS
```

SHA equality is required. There is **no** seed-specific Phase25B feature
regeneration.

---

## 9. Component training protocols

### 9.1 R_psi

For each new seed `s` in {123, 3407}, train exactly the inherited Phase25A
configuration.

| Item | Value |
|---|---|
| cross-fit fold models | 3 |
| final refit | 1 |
| logical runs per represented seed | 4 |
| new runs (seeds 123 + 3407) | 8 |

Fold manifests are the fixed Phase25A manifests. Only training RNG changes.

**Master-seed semantics** (generalising canonical seed-42-for-every-fold):

```
R_psi fold training seed   = s           (for each of the 3 folds)
R_psi final-refit seed     = s
```

Seed 42 reproduces canonical semantics exactly; seed 123 uses 123; seed 3407
uses 3407. New fold memberships are **not** derived from the seed.

### 9.2 Seed-specific paired-gain targets

**This is mandatory.** Because `R_psi` changes by seed, Phase25C `DeltaDice` is
seed-dependent.

For each master seed `s`, using that seed's leakage-safe `R_psi` OOF candidate:

```
DeltaDice_s = Dice(R_psi_s_OOF, y) - Dice(G_fixed, y)
```

Regenerate the paired target and the `BENEFICIAL` / `NEUTRAL` / `HARMFUL`
category using the **same frozen thresholds**:

```
BENEFICIAL >= +0.02
HARMFUL    <= -0.01
```

The GT-based target may be created **only after** the seed-specific OOF
candidate is frozen. Seed42 Phase25C `DeltaDice` is **never** reused as the
training target for `B_phi` seed 123 or seed 3407.

```
gain_target_regeneration_rule = SEED_SPECIFIC_FROM_R_PSI_OOF
```

### 9.3 B_phi

For each seed:

* router input feature matrix = same frozen Phase25B 202-D features
* router regression target = seed-specific `DeltaDice_s`
* exact Phase25D v1.2.1 protocol

| Item | Value |
|---|---|
| CV fold training runs | 5 |
| final all-DEV refit | 1 |
| logical runs per seed | 6 |
| new runs (seeds 123 + 3407) | 12 |

**RNG rule.** Canonical master 42 gives fold seeds `42000 + k`. Generalised:

```
router_fold_seed(s, k) = 1000 * s + k          for k = 0..4
```

| seed | fold seeds |
|---|---|
| 42 | 42000 .. 42004 |
| 123 | 123000 .. 123004 |
| 3407 | 3407000 .. 3407004 |

Final all-DEV refit seed = `s`. The seed does **not** regenerate fold
membership.

**Normalization.** Fold-specific normalization remains `FIT`-only, `ddof=0`,
the same 8 continuous scalar semantics, the same binary flags, and deep
features unnormalized. Because the feature matrix and fold membership are
fixed, normalization values **should** reproduce the seed-42 fold statistics
exactly for every master seed. This must be physically verified.
Normalization itself does not depend on the model seed.

**OOF scientific policy.** For each seed's OOF router scores, primary
development routing uses the fixed budget:

```
b = 0.25,  N = 4957,  K = 1239
```

Rank `delta_hat_oof` descending, then `sample_id` ascending; take the first
1239. This is for OOF development reproducibility. No scalar threshold is
needed for OOF comparison. There is no seed-specific `K`.

### 9.4 Final B_phi calibration

The previous A/B/C ambiguity is resolved prospectively as:

```
B = PER-SEED DEV CALIBRATION TO THE SAME FROZEN NOMINAL 25% RULE
```

For each seed's final all-DEV `B_phi`:

1. score all 4957 `ROUTER_DEVELOPMENT` rows
2. rank final `delta_hat` descending
3. `sample_id` ascending tie-break
4. `K = 1239`
5. derive the exact boundary threshold `tau_C7_final_s`
6. derive

```
tau_C8_final_s = tau_C7_final_s - 0.25 * C
```

with frozen

```
C = 1051648/10270749
```

This threshold is frozen **before** any VAL808 seed-specific result is opened.
This is **calibration, not performance selection**. Do not force 25% activation
on VAL808; apply each seed's fixed DEV-calibrated threshold to VAL808 as-is.

For seed 42, the derived values must reproduce exactly:

```
tau_C7_final_42 = 24796109646558761/20000000000000000000  (= 0.001239805482327938)
tau_C8_final_42 = -5003565381643716252018011/205414980000000000000000000
                = -0.024358327623641256
```

### 9.5 S_omega

Because seed-specific `R_psi` changes the candidate, post-safety features and
labels are also seed-dependent. For each seed:

* construct the OOF refined candidate from `R_psi_s`
* construct the exact frozen 20-D `S_omega` input vector
* `target_s = 1` iff `DeltaDice_s > 0`
* all exact-zero `DeltaDice` rows remain `FALLBACK` labels

Seed42 `S_omega` targets are **not** reused for other seeds.

```
safety_target_regeneration_rule = SEED_SPECIFIC_FROM_R_PSI_OOF
```

Training uses the exact Phase25F fold membership, architecture, normalization
semantics, `BCEWithLogitsLoss`, optimizer, scheduler, batch size, early stop,
checkpoint rule, and threshold `0.50`.

| Item | Value |
|---|---|
| CV folds | 5 |
| final all-DEV refit | 1 |
| logical runs per represented seed | 6 |
| new runs (seeds 123 + 3407) | 12 |

**RNG rule.** Canonical seed-42 CV fold seeds are `54000 + k`. Generalised:

```
safety_fold_seed(s, k) = 1000 * s + 12000 + k
```

| seed | fold seeds |
|---|---|
| 42 | 54000 .. 54004 |
| 123 | 135000 .. 135004 |
| 3407 | 3419000 .. 3419004 |

Final all-DEV safety refit seed = `s`. This is a prospective RNG generalization
only. Fold membership remains fixed.

---

## 10. Full seed dependency model

**Classification:** `MODULEWISE_DOWNSTREAM_REPRODUCIBILITY_WITH_CANONICAL_FIXED_GLOBAL`

For a given master seed `s`:

```
G                      = canonical fixed G
Phase25B features      = canonical fixed feature matrix
R_psi_s                = trained with seed s
DeltaDice_s            = generated from R_psi_s OOF
B_phi_s                = trained using fixed features + DeltaDice_s
S_omega_features_s     = generated from R_psi_s OOF candidates
S_omega_target_s       = 1 iff DeltaDice_s > 0
S_omega_s              = trained on those seed-specific features/targets
Final system_s         = G_fixed + R_psi_s + B_phi_s + S_omega_s + fixed wrapper/fusion
```

**No cross-seed mixing.** For example: seed123 `B_phi` may **not** use seed3407
targets; seed123 `S_omega` may **not** use seed42 candidate features.

---

## 11. Evaluation populations

### 11.1 Primary

```
population = ROUTER_DEVELOPMENT
n          = 4957
role       = PRIMARY_MULTI_SEED_REPRODUCIBILITY_DEVELOPMENT_EVIDENCE
```

Leakage-safe OOF predictions are used for `R_psi`, `B_phi`, `S_omega`. The
primary Phase 29 system comparison is based on these OOF development artifacts.
This preserves Phase 30's holdout independence.

### 11.2 Secondary

```
population = VAL808
n          = 808
role       = SECONDARY_MULTI_SEED_CONTINUITY_DEVELOPMENT_EVIDENCE
```

VAL808 was already opened in Phase 27. It is **not** an untouched holdout, not a
routing holdout, not external validation, and not TEST.

For seeds 123 and 3407, new VAL808 inference is allowed only after all
seed-specific training and DEV calibration are frozen. For seed 42, reuse the
Phase27 canonical VAL808 evidence when the exact pipeline and numeric inference
semantics match. Do not rerun seed-42 VAL808 unnecessarily.

### 11.3 README "TRAIN+VAL" reconciliation

The historical README wording is **not** silently deleted. It is recorded as
superseded operationally for Phase 29 by:

```
PRIMARY   = ROUTER_DEVELOPMENT OOF
SECONDARY = VAL808 continuity
```

`ROUTER_HOLDOUT` remains excluded. This is an **additive** supervisor
clarification.

---

## 12. Locks

### 12.1 ROUTER_HOLDOUT lock

Absolutely no ROUTER_HOLDOUT image read, mask read, feature read, outcome read,
router scoring, refiner inference, safety inference, or metric computation.
Phase 30 remains the first one-shot integrated ROUTER_HOLDOUT evaluation.

```
ROUTER_HOLDOUT_reads = 0
```

### 12.2 TEST lock

TEST remains untouched.

```
TEST_reads = 0
```

Phase 39 remains the sole TEST phase.

---

## 13. Training-run count

| Component | Runs / seed |
|---|---|
| G | 0 (Phase 29 scope) |
| R_psi | 4 |
| B_phi | 6 |
| S_omega | 6 |
| **Total represented per seed** | **16** |

| Quantity | Value |
|---|---|
| represented logical downstream runs (3 seeds) | 48 |
| reused historical seed-42 runs | 16 |
| **new Phase 29 runs** | **32** |

New-run breakdown: R_psi = 8, B_phi = 12, S_omega = 12.

```
represented_training_runs    = 48
reused_seed42_training_runs  = 16
new_training_runs_authorized = 32
```

No additional retraining.

---

## 14. Deterministic environment

For every new seed:

* Python `random` seed
* NumPy seed
* `torch.manual_seed`
* `torch.cuda.manual_seed_all`
* DataLoader generator
* worker initialization
* `cudnn.deterministic = true`
* `cudnn.benchmark = false`

AMP semantics remain inherited from each component's canonical protocol. Do
**not** standardize all components to one precision mode if their canonical
protocols differ.

---

## 15. Required outputs per new seed

### R_psi

3 leakage-safe OOF fold checkpoints; OOF regional candidates for all 4957 rows;
seed-specific paired-gain target table; 1 final refit checkpoint; complete
histories; determinism/provenance records. No seed result may be used to alter
another seed's training.

### B_phi

5 CV checkpoints; 4957 exactly-once OOF scores; 25% `K=1239` OOF membership;
1 final all-DEV checkpoint; final DEV score table; exact `tau_C7_final_s`; exact
`tau_C8_final_s`; normalization artifacts; complete histories. Threshold freeze
must precede VAL808 inference.

### S_omega

Seed-specific 20-D OOF features; seed-specific binary targets; 5 CV checkpoints;
4957 OOF safety predictions; 1 final checkpoint; normalization artifacts;
complete histories. Decision threshold remains exactly `0.50`.

---

## 16. OOF integrated system per seed

On `ROUTER_DEVELOPMENT`, for each seed:

* use seed-specific `B_phi` OOF score
* select fixed `K = 1239`
* use seed-specific `R_psi` OOF candidate
* use seed-specific `S_omega` OOF decision

Integrated output:

```
not selected                 -> global
selected + safety accept     -> seed-specific regional candidate
selected + safety reject     -> global
```

This yields leakage-safe `system_s` OOF evidence.

---

## 17. Metrics

### 17.1 DEV primary reproducibility metrics

For each seed report at minimum: macro-domain integrated `DeltaDice`;
per-domain `DeltaDice`; routed mean `DeltaDice`; `precision@budget`; benefit
capture; harmful activation share; `S_omega` accept fraction; `S_omega` reject
fraction.

Across 3 seeds report: mean, sample standard deviation, minimum, maximum,
range. Also report sign consistency. **No seed is declared winner.**

### 17.2 VAL808 secondary metrics

For each seed report: Global Dice; final integrated Dice; `DeltaDice`;
macro-domain `DeltaDice`; per-domain Dice/`DeltaDice`; realized router
activation; `S_omega` accept/reject counts. Use each seed's DEV-calibrated
final-router threshold. Do **not** force VAL808 to 25%. For seed 42, reuse the
exact Phase27 result where physically identical.

### 17.3 Phase27 preservation criterion

Per-seed VAL808 continuity is evaluated under the already frozen Phase27
non-inferiority rule:

```
margin    = 0.005
criterion = lower 95% CI > -0.005
```

This is a **per-seed continuity result**. It is **not** the Phase 29 completion
criterion. Phase 29 remains descriptive with:

```
NO_NUMERIC_REPRODUCIBILITY_PASS_FAIL_GATE
```

Report if one or more seeds fail preservation. Do not retune.

---

## 18. Primary interpretation

```
DESCRIPTIVE_THREE_SEED_REPRODUCIBILITY
```

**Primary scientific question:** How stable are the direction and practical
magnitude of the frozen BARR development effect when downstream BARR training
randomness is changed across seeds 42, 123 and 3407 while data partitions and
the GlobalMedFiLM reference remain fixed?

There is **no** numeric Phase 29 PASS/FAIL threshold.

---

## 19. Statistics

Phase 29 may report per-seed point estimates, per-seed frozen-population
bootstrap CIs where already defined, three-seed mean, sample SD, range,
min/max, and sign consistency.

Do **not** perform formal across-seed significance testing. Do **not** introduce
multiple-testing correction. **Phase 31 owns formal hypothesis testing.**

---

## 20. Canonical seed-42 bundle remains canonical

No Phase 29 result automatically replaces the Phase26 canonical bundle.

```
deployment_model_replaced = false
canonical_seed_changed    = false
best_seed_selected        = false
```

Even if seed 123 or seed 3407 has a numerically larger development result.
Phase 29 is **evidence, not model selection**.

---

## 21. Artifact roots

```
checkpoints/phase29_seed123/
checkpoints/phase29_seed3407/
data_cache/phase29_seed123/
data_cache/phase29_seed3407/
experiments/phase29_seed123/
experiments/phase29_seed3407/
```

Seed-42 weights are **not** duplicated unnecessarily. For seed 42, create
provenance bindings only.

---

## 22. Terminal states

**Success (only if every execution-critical field is prospectively complete):**

```
PHASE29_SPEC_V1_1_COMPLETE__FIXED_GLOBAL_THREE_SEED_BARR_STACK_DEPENDENCIES_DEV_CALIBRATION_AND_EVALUATION_FROZEN__PHASE29_EXECUTION_ELIGIBLE_NOT_STARTED
```

**Blocked:**

```
PHASE29_V1_1_BLOCKED__SEED42_REUSE_INCONSISTENT
PHASE29_V1_1_BLOCKED__COMPONENT_TRAINING_PROTOCOL_INCOMPLETE
PHASE29_V1_1_BLOCKED__SEED_SPECIFIC_DEPENDENCY_CHAIN_INCOMPLETE
PHASE29_V1_1_BLOCKED__ROUTER_CALIBRATION_RULE_INCOMPLETE
PHASE29_V1_1_BLOCKED__EVALUATION_POPULATION_INCOMPLETE
PHASE29_V1_1_BLOCKED__REPRODUCIBILITY_SPEC_INCOMPLETE
```

---

## 23. Directive

```
STOP.
DO NOT TRAIN.
DO NOT START PHASE30.
DO NOT OPEN ROUTER_HOLDOUT.
DO NOT OPEN TEST.
```
