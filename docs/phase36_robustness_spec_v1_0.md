# Phase 36 — Robustness & Image Perturbation Analysis
## Specification v1.0 — Pre-Execution Scientific Protocol + Source Freeze

**Revision:** `ra_medfilm_barr_phase36_robustness_v1_0`
**Method:** RA-MedFiLM-BARR
**Classification:** `PRE_EXECUTION_SCIENTIFIC_PROTOCOL__NO_PHASE36_EXECUTION`
**Evidence class:** `DEVELOPMENT_SET_SYNTHETIC_PERTURBATION_ROBUSTNESS_EVIDENCE`
**Generated:** 2026-10-05

---

## 0. Scope and non-goals

Phase36 measures the robustness of the **already-frozen** RA-MedFiLM-BARR final
system under deterministic synthetic image perturbations and region/proposal
perturbations on the **VAL808** development population.

Phase36 does **NOT**: retrain; tune thresholds; tune routing; select new
checkpoints; optimize perturbation severities from outcomes; modify the A8/C9
policy; change G / B_phi / R_psi / S_omega; perform adversarial optimization; or
access TEST.

**Claim boundary.** The evidence supports descriptive statements about model
sensitivity under the frozen protocol only. It is **NOT**: clinical robustness,
external generalization, adversarial robustness, TEST performance, or
deployment-reliability proof.

---

## 1. Entry authority

Phase35 = `COMPLETE_CANONICAL`. Bound exactly:

| artifact | SHA-256 |
|---|---|
| `reports/audits/phase35_canonical_closure_v1_0a.json` | `7720c1d292292a8a5ea50311674a834e906633f7f168217c2853018703eb7df1` |
| `reports/audits/phase35_canonical_closure_final_check_v1_0a.json` | `7c12f8aac65e9a4acd9ed528ba391f82b9aa65533fc97c7e4a2d9ce774bb5c4d` |
| `reports/audits/phase35_canonical_closure_terminal_v1_0a.json` | `6e343b7f433bbc8a43b3d746b2affd2bbc15ecdaeb9491cdc83e4d02f3d4047d` |

Phase36 = `ELIGIBLE_NOT_STARTED`; TEST = `LOCKED_UNTIL_PHASE39`.

---

## 2. Population

VAL808 only. n = 808; domains ISIC (357), BUSI (84), KVASIR (87), KUB (280).
Manifest `manifests/phase4_v3/val.csv`
(`082c80b2bda63fd73f371f109c34643adf01edaead921643fb2e44993ba53315`).
ROUTER_HOLDOUT rows = 0; TEST rows = 0. Future execution MAY read VAL808 raw
images and VAL808 GT; it MUST NOT read ROUTER_HOLDOUT or TEST.

---

## 3. Clean reference

Bound clean final-system reference:
- `reports/tables/phase27_val808_per_sample_scores.csv`
  (`702133930ce14ac9513c992833396e3e250d08417b17d1032cbd260a405cfb12`) — per-sample
  global/final Dice, delta Dice, state-machine branch, routing decision.
- `data_cache/phase29_seed42/phase29_seed42_val808_decisions.csv`
  (`df4a0f376a7edab221d584b2a7152bf7e8f55c00ade87e39cd94c9bb13fedea6`) — per-sample
  routing state (`selected`, `safety_accept`, `final_source`, `roi_available`).

If this exact reference is unavailable at execution time, Phase36 generates
**exactly ONE** clean reference pass under the frozen Phase36 source **before**
any perturbation execution — declared prospectively now, never after outcomes.

---

## 4. Image perturbation contract

Input domain `float32 [0,1]`. Every perturbation generated from the ORIGINAL
clean input independently. **No chaining.**

| condition | equation |
|---|---|
| CLEAN | identity |
| BRIGHTNESS_NEG | `x' = clip(x − 0.10, 0, 1)` |
| BRIGHTNESS_POS | `x' = clip(x + 0.10, 0, 1)` |
| CONTRAST_LOW | `x' = clip((x − mean_hw)·0.80 + mean_hw, 0, 1)` |
| CONTRAST_HIGH | `x' = clip((x − mean_hw)·1.20 + mean_hw, 0, 1)` |
| GAMMA_LOW | `x' = clip(x,0,1)^0.80` |
| GAMMA_HIGH | `x' = clip(x,0,1)^1.20` |
| GAUSSIAN_NOISE_LOW | `σ = 0.02`, three base seeds {42, 123, 3407} |
| GAUSSIAN_NOISE_HIGH | `σ = 0.05`, three base seeds {42, 123, 3407} |
| GAUSSIAN_BLUR_LOW | `σ = 0.5`, separable, radius `ceil(3σ)`, reflect padding |
| GAUSSIAN_BLUR_HIGH | `σ = 1.0`, same kernel rules |
| RESOLUTION_075 | downsample to 0.75×512 then bilinear restore, `align_corners=False` |
| RESOLUTION_050 | downsample to 0.50×512 then bilinear restore, `align_corners=False` |

Contrast mean is the per-image per-channel spatial mean. Noise:
`seed = SHA256("phase36|gaussian_noise|<base_seed>|<sample_id>")[:8]` →
`Generator(PCG64(seed))`; one deterministic realization per
(sample, base-seed, severity); CPU-side float32; clip to [0,1].

Forbidden: JPEG, color-space conversion, rotation, crop, random augmentation,
adversarial optimization.

---

## 5. Region / proposal perturbation contract

Applied from the CLEAN image / CLEAN G state. Canonical proposal stays
`p_global ≥ 0.30` (never altered). Canonical proposal/crop geometry is computed
first, then only the crop geometry is perturbed.

| condition | rule |
|---|---|
| PROPOSAL_CLEAN | identity |
| SHIFT_LEFT_10 / RIGHT_10 / UP_10 / DOWN_10 | 0.10 × canonical crop side |
| SCALE_085 | crop side = 0.85 × canonical |
| SCALE_115 | crop side = 1.15 × canonical |

Coordinates clamped inside image bounds via deterministic centre adjustment.
Canonical empty proposal → `NOT_APPLICABLE_EMPTY_PROPOSAL`. No outcome-dependent
replacement.

---

## 6. Final-system state machine (frozen)

`G → B_phi → SKIP/EXECUTE → (if EXECUTE) R_psi → S_omega →
EXECUTE_THEN_ACCEPT / EXECUTE_THEN_REJECT → final routed segmentation`.

Frozen A8/C9 policy (`A8_C9`, budget 0.25, score `delta_hat_final − 0.25·C`,
EXECUTE iff `score ≥ frozen_threshold`). No joint retraining; no threshold change.

For image perturbations: evaluate the COMPLETE frozen system. For proposal
perturbations: reuse only clean G quantities the frozen implementation permits
(the frozen global probability map + ROI geometry); G is not re-run merely to
perturb downstream proposal geometry.

---

## 7. Scientific metrics

Primary: `paired_delta_Dice = Dice_perturbed − Dice_clean` (also `Dice_clean`,
`Dice_perturbed`). Canonical Dice: `src.metrics.evaluation_metrics.dice`
(eps = 1e-7) under the frozen empty-mask policy
(`reports/audits/evaluation_empty_mask_policy.json`). GT rule: full-field
NEAREST-512 + centre pad, `(arr > 0)`.

Secondary (bound before execution): `iou`, `hd95`
(`src/metrics/evaluation_metrics.py`), with the frozen empty-case handling.

Also recorded: `prediction_consistency_Dice`, `route_state_clean`,
`route_state_perturbed`, `route_state_changed`, `B_phi_execute_clean/perturbed`,
`B_phi_decision_changed`, S_omega state, `execution_rate`, `accept_rate`,
`reject_rate`, `proposal_valid`, proposal/crop geometry.

---

## 8. Fixed summaries

Per domain × condition: n, mean/median/std Dice, mean/median/5th-pct paired
delta Dice, prediction-consistency Dice mean/median, route-state-change
count/share, execution rate, accept rate where defined. Stress flags (descriptive
only): `count(ΔDice ≤ −0.05)`, `count(ΔDice ≤ −0.10)`. No new p-values; no
significance claims. For noise: per-seed first, then arithmetic mean across the
three frozen seeds; no best-seed selection.

---

## 9. Worst case

`worst_image_perturbation_delta_Dice = min paired_delta_Dice` over the FIXED
image set (excludes proposal perturbations). Separately,
`worst_proposal_perturbation_delta_Dice = min paired_delta_Dice` over applicable
fixed proposal perturbations. Reported by domain. No post-hoc set expansion.

---

## 10. KUB reporting

KUB subgroup metadata (`category` in the VAL manifest) is
`REPORTING_ONLY_METADATA`: Kidney_Stone (112), Bladder_Stone (144),
Ureteric_Stone (24). Never a segmentation class or task id; must not alter model
conditioning or perturbation generation.

---

## 11. Figures / tables / counters / determinism

Figures: R1 image-perturbation mean ΔDice heatmap (domain × condition);
R2 severity curves (noise/blur/resolution); R3 route-state-change / execution-rate
heatmap; R4 proposal perturbation ΔDice summary; R5 worst-case ΔDice distribution
by domain. No outcome-selected gallery.

Tables: `phase36_image_robustness_per_sample.csv`,
`phase36_image_robustness_by_domain_condition.csv`,
`phase36_noise_seed_summary.csv`,
`phase36_proposal_robustness_per_sample.csv`,
`phase36_proposal_robustness_by_domain_condition.csv`,
`phase36_route_stability_summary.csv`, `phase36_worst_case_per_sample.csv`,
`phase36_worst_case_by_domain.csv`,
`phase36_kub_subgroup_robustness.csv` (if metadata authority passes). The exact
perturbation registry is persisted separately.

Counters recorded at execution; forever zero: ROUTER_HOLDOUT reads, TEST reads,
training, optimizer steps, parameter mutations. Final counts are NOT guessed now.

Determinism: all perturbations deterministic; per-perturbation
(sample_id, condition_id, severity, base_seed, derived_seed) persisted; unit
tests use fixed synthetic arrays.

---

## 12. Gates

`--mode science` requires `PHASE36_EXECUTE == "1"` (fail-closed, exit 2).
`--mode smoke` requires `PHASE36_SMOKE_EXECUTE == "1"` (separate gate). No
import-time model execution.

---

## 13. Terminal

`PHASE36_ROBUSTNESS_AND_IMAGE_PERTURBATION_PROTOCOL_V1_0_COMPLETE__PHASE35_COMPLETE_CANONICAL_AUTHORITY_BOUND__VAL808_ONLY_ROBUSTNESS_POPULATION_FROZEN__IMAGE_AND_REGION_PROPOSAL_PERTURBATION_REGISTRIES_FROZEN_BEFORE_EXECUTION__FULL_RA_MEDFILM_BARR_STATE_MACHINE_AND_A8_C9_POLICY_PRESERVED__DETERMINISTIC_METRIC_AND_REPORTING_CONTRACT_FROZEN__ZERO_ROUTER_HOLDOUT_OR_TEST_ACCESS__NO_MODEL_OR_PROTECTED_DATA_EXECUTION__PHASE36_SYNTHETIC_SMOKE_ELIGIBLE_NOT_STARTED__PHASE36_SCIENTIFIC_EXECUTION_NOT_STARTED__TEST_REMAINS_PHASE39_ONLY`
