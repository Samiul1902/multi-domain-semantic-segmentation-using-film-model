# Phase 26 — Full Four-Domain RA-MedFiLM-BARR Integration & Canonical Bundle Freeze

## Provenance note
Legacy roadmap title: "Full Four-Domain RA-MedFiLM-BARR Training".

Operationally superseded **before Phase26 execution** because all learned components
already possess canonical trained checkpoints and no valid joint-training contract
existed.  This is a **prospective supervisor amendment**.  It does not alter any
historical Phase25 artifact.

## 1. Operational definition
Bind the already-trained canonical GlobalMedFiLM, regional refiner, benefit router, post-safety selector, deterministic ROI/fusion rules, normalization artifacts and one fixed development-selected routing operating point into the canonical full four-domain RA-MedFiLM-BARR inference bundle, without changing any learned parameter.

- `phase26_training_required = false`
- `phase26_training_mode = ASSEMBLY_ONLY__NO_PARAMETER_OPTIMIZATION`
- Revision: `ra_medfilm_barr_phase26_integration_v1_0`
- `science_changed = false` · `model_weights_changed = false`
- `training_authorized = false` · `fine_tuning_authorized = false` · `holdout_opened = false`

## 2. Component identities (frozen, immutable)
| Module | Origin | Phase26 trainability | Parameters |
|---|---|---|---|
| G — GlobalMedFiLM | Phase21 | FROZEN_NO_GRAD | frozen |
| R_psi — BARRRegionalRefinerV1 (ROI-0.30) | Phase25A | FROZEN_NO_GRAD | 1,276,401 |
| B_phi — BARRBenefitRouterV1 | Phase25D | FROZEN_NO_GRAD | 36,801 |
| S_omega — BARRPostSafetyV1 | Phase25F | FROZEN_NO_GRAD | 1,217 |
| FUSION — deterministic rule | Phase24/25A | NOT_TRAINABLE | NONE |

`trainable_parameter_set = EMPTY` · `frozen_parameter_set = ALL_CANONICAL_COMPONENT_PARAMETERS`
Full checkpoint SHAs are recorded in `reports/audits/phase26_component_identity_binding_v1_0.json`.

## 3. Gradient graph
`gradient_flow_topology = NOT_APPLICABLE__NO_PARAMETER_OPTIMIZATION` · backward passes = 0 ·
optimizer steps = 0.  No joint loss, no soft/straight-through/differentiable crop routing,
no cross-module gradients.

## 4. Training population
`training_population = NONE` · `training_population_n = 0`.
ORIGINAL_TRAIN 5832 = NOT used for Phase26 training. ROUTER_HOLDOUT 875 =
RESERVED_UNOPENED_FOR_PHASE30. VAL808 = UNOPENED. TEST = LOCKED_UNTIL_PHASE39.
This resolves the previous holdout contamination risk because Phase26 trains on no population.

## 5. Canonical operating point
- Canonical system variant: **A8 / C9** (Phase25E resource gate + Phase25F S_omega fallback).
- Canonical budget: **0.25** (25%) — largest eligible informative Phase25E PRIMARY H1-passing
  budget with Phase25G A8 preservation pass.  Development-selected; DEV selected count = 1239.
- Canonical lambda representative: **0.25** — `FIRST_POSITIVE_FROZEN_LAMBDA`, membership-equivalent
  under constant cost (`lambda_performance_selected = false`).
- Exact final-router threshold is bound in
  `reports/audits/phase26_canonical_router_threshold_binding_v1_0.json`.

## 6. Thresholds (never conflated)
| Use | Value |
|---|---|
| ROI proposal | 0.30 |
| Segmentation output | 0.50 |
| S_omega acceptance probability | 0.50 |
| S_omega logit | 0.0 |
| ROI expansion | 1.50 |
| Regional input resolution | 256 x 256 |

## 7. Inference state machine
Inputs: image `x`, task `t`.  Exactly one GlobalMedFiLM forward.
Build the frozen Phase25B router feature vector -> normalize with frozen Phase25D FINAL
normalization -> run frozen FINAL B_phi -> utility with lambda=0.25 -> compare with the frozen
25%-budget DEV-calibrated threshold.
- SKIP: `final = p_global` (regional refiner and S_omega NOT run).
- EXECUTE: frozen 0.30 / 1.50 ROI geometry -> one frozen regional refiner forward ->
  deterministic regional-fused candidate -> frozen 20-D post-safety vector -> frozen Phase25F
  FINAL normalization -> one frozen S_omega forward.
  - `sigmoid(logit) >= 0.50`: `final = regional-fused candidate`
  - else: `final = p_global`
Final binary mask: `p_final >= 0.50`.  No second GlobalMedFiLM forward. No GT at inference.

## 8. Canonical checkpoint bundle
Phase26 canonical model identity is **NOT a new learned checkpoint**; it is a
**manifest bundle** at `artifacts/phase26_ra_medfilm_barr_bundle_v1_0/canonical_bundle_manifest.json`.
Original canonical checkpoints remain authoritative; no weight bytes are copied.

## 9. Evidence class
`phase26_evidence_class = CANONICAL_INTEGRATION_AND_CONFIGURATION_FREEZE`.
`new_performance_evidence = false` · `new_model_state = false` · `parameter_optimization = false`.
There is **no accuracy threshold** for Phase26.  Phase30 will provide the first clean
one-shot evaluation of the fixed Phase26 bundle.

## 10. Forbidden
NO training · NO fine-tuning · NO backward · NO optimizer · NO model forward in the spec
phase · NO ROUTER_HOLDOUT · NO VAL808 · NO TEST · NO Phase27+.

<!-- PHASE26_ROUTER_THRESHOLD_RECONCILIATION_V1_1 -->

## 11. Router score / threshold semantics (v1.1 reconciliation)

The canonical Phase26 routing policy is **membership-equivalent** to the frozen Phase25E
C7/C8 25%-budget membership.

Score spaces (frozen, never conflated):

| Symbol | Score space | Expression |
|---|---|---|
| `s_C7` | C7 raw delta-hat | `delta_hat_oof_i` |
| `s_C8` | C8 resource-aware utility | `delta_hat_oof_i - lambda*C_i` |

- `normalized_action_cost C_i = 1051648 / 10270749` (unique: `unique_eligible_costs = 1`).
- `lambda*C = 262912 / 10270749` exactly.
- Canonical operational score = **C8 resource-aware utility** (`delta_hat - lambda*C`).
- Canonical operational threshold = `tau_C8 = -2326256430798223/102707490000000000`
  (space: `C8_RESOURCE_AWARE_UTILITY_SPACE`).
- The C7 threshold `tau_C7 = 29487973/10000000000` is recorded for algebraic
  provenance only, classified `EQUIVALENT_RAW_GAIN_THRESHOLD_PROVENANCE`.  It is retained.
- Equivalence: `delta_hat >= tau_C7  iff  delta_hat - lambda*C >= tau_C8`
  under the frozen constant action cost.
- Canonical membership identity = `EXACT_PHASE25E_FROZEN_25PCT_C8_MEMBERSHIP`
  (selected-ids digest `e71e368cbb95b8d3398b47427df243bb8b387dd6d442ccf038188446677f446f`).
- Score space is always named; never write only "compare router score to threshold".

See `reports/audits/phase26_router_threshold_reconciliation_v1_1.json`,
`reports/audits/phase26_router_threshold_exact_transform.json`,
`reports/audits/phase26_router_threshold_membership_equivalence.json`.

<!-- PHASE26_DEPLOYMENT_SEMANTICS_V1_2 -->

## 12. OOF scientific policy space versus final-router runtime calibration (v1.2)

Phase26/30 inference does **not** use the OOF policy threshold.  Two calibration spaces are frozen and
must never be conflated:

| | Space B — scientific OOF policy | Space A — final-router runtime |
|---|---|---|
| Score variable | `delta_hat_oof` | `delta_hat_final` (FINAL Phase25D `B_phi`) |
| Producer | cross-fitted OOF predictor | one model refit on all 4957 DEV rows |
| Raw τ_C7 (25%) | `29487973/10000000000` | `24796109646558761/20000000000000000000` |
| Utility τ_C8 | `-2326256430798223/102707490000000000` | **`-5003565381643716252018011/205414980000000000000000000`** |
| Role | `SCIENTIFIC_DEVELOPMENT_MEMBERSHIP_ONLY` | `CANONICAL_FINAL_ROUTER_CALIBRATION` |
| Runtime authority | **false** | **true** |

- Phase25 scientific comparisons remain **OOF-based** and are unchanged.
- Phase26/30 inference uses the **FINAL Phase25D router** and its separately frozen DEV calibration.
- Runtime score = `C8_FINAL_ROUTER_RESOURCE_AWARE_UTILITY = delta_hat_final - 0.25*C`,
  with `C = 1051648/10270749`.
- Runtime decision: `EXECUTE iff utility >= -5003565381643716252018011/205414980000000000000000000`.
- The v1.1 OOF utility threshold `-2326256430798223/102707490000000000` is retained as
  `SCIENTIFIC_OOF_POLICY_THRESHOLD_PROVENANCE` (not the runtime threshold).
- **Future cohort (ROUTER_HOLDOUT / Phase30):** apply the fixed DEV-calibrated threshold
  independently per sample.  **Do NOT force exactly 25%** of holdout rows to EXECUTE; report both the
  nominal 25% calibration budget and the realized activation fraction.  No holdout ranking, no top-K,
  no recalibration.
- The OOF selected IDs and the final-router DEV selected IDs need not coincide (intersection 1086 of
  1239) — this is `EXPECTED_MODEL_FIT_SPACE_DIFFERENCE`, not drift.

<!-- PHASE26_CANONICAL_INTEGRATION_COMPLETE -->

## Phase26 canonical integration - COMPLETE_CANONICAL (2026-10-02)

**Phase26 = COMPLETE_CANONICAL** (assembly only; legacy title 'Full Four-Domain
RA-MedFiLM-BARR Training' redefined to 'Full Four-Domain RA-MedFiLM-BARR Integration &
Canonical Bundle Freeze'). Phase27 = ELIGIBLE_NOT_STARTED; Phase28/29/30 = NOT_STARTED.

- Bundle: `artifacts/phase26_ra_medfilm_barr_bundle_v1_0` (manifest SHA `f7aebb0f646bcc8de49fa91b70a4c4cc1051c9998ab6b055a8d4d187809cb3d9`)
- Wrapper: `src/models/barr/ra_medfilm_barr.py` (SHA `342f2163690c2fa8d5a601ab1d18178b982d701b916935c33e0793b0801c3724`, 0 trainable parameters)
- Notebook: `notebooks/phasewise/phase_26_full_system_integration/phase26_canonical_integration_and_bundle_freeze.ipynb` (SHA `57552c16b5a444f1b2404077eeac0004d37fd198355d679a66eb5c24ea15b4e0`, 3x byte-identical)
- Runtime policy: `A8_C9`, nominal budget 0.25, score `delta_hat_final - 0.25*C`,
  threshold `-5003565381643716252018011/205414980000000000000000000` (EXECUTE iff `>=`).
- Final-router DEV calibration selected count = 1239.
- ROUTER_HOLDOUT = RESERVED_UNOPENED_FOR_PHASE30; VAL808 = UNOPENED; TEST = LOCKED_UNTIL_PHASE39.
- 0 model training / 0 backward / 0 optimizer / 0 scientific-data forwards.

Terminal: `PHASE26_CANONICAL_INTEGRATION_COMPLETE__A8_C9_25PCT_FINAL_ROUTER_RUNTIME_POLICY_AND_BUNDLE_FROZEN__PHASE27_ELIGIBLE_NOT_STARTED`
