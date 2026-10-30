# Phase 35 - Feature Attribution & Visual Interpretability

**Revision:** `ra_medfilm_barr_phase35_interpretability_v1_0`
**Classification:** `PRE_EXECUTION_FEATURE_ATTRIBUTION_VISUAL_INTERPRETABILITY_SPECIFICATION`
**Phase ID (immutable):** `phase_35_interpretability`
**Method:** RA-MedFiLM-BARR

## 0. Standing
Phase34 is `COMPLETE_CANONICAL`; this document freezes the Phase35 interpretability protocol
**before any model load, forward, backward, Grad-CAM or attribution execution**. Phase35 execution
has **NOT** started. Phase36 has **NOT** started. TEST remains `LOCKED_UNTIL_PHASE39`.

## 1. Four evidence families (never merged)
1. **I1 FILM_PARAMETER_INTERPRETABILITY** - static FiLM gamma/beta parameter analysis.
2. **I2 SEGMENTATION_GRADIENT_SALIENCY** - Grad-CAM diagnostic on the global segmenter.
3. **I3 ROI_PROPOSAL_AND_REGIONAL_BEHAVIOUR_VISUALIZATION** - proposal/crop visualization.
4. **I4 BENEFIT_ROUTER_FEATURE_ATTRIBUTION** - Gradient x Input on the 202-D router vector.

Explicitly **out of scope**: performance reevaluation, new statistical hypothesis testing, failure mining, robustness perturbation, counterfactual model retraining, TEST evaluation.

## 2. Claim type
Evidence is `DESCRIPTIVE_MODEL_MECHANISM_EVIDENCE`. It is **not** automatically a causal explanation, feature
necessity/sufficiency, clinical reasoning, ground-truth localization accuracy, proof of
trustworthiness, proof that FiLM caused performance improvement, or proof that router attribution
identifies biological importance. Required language: attribution, model sensitivity, saliency, association within the frozen model, self-consistency with model prediction/proposal.

## 3. Populations
- **Visual cohort:** the already-frozen `reports/tables/phase21_gallery_selection_64.csv` - 64 cases, 16 per domain
  (ISIC/BUSI/KVASIR/KUB), all VAL808, **0 ROUTER_HOLDOUT overlap, 0 TEST overlap**.
- **Display subset (16):** lowest frozen gallery rank within each domain, first 4 per domain; if no frozen gallery rank exists, sample_id ascending, first 4 per domain. Recorded now; created only at future execution.
- **Router attribution population:** VAL808 (non-holdout), n = 808, from the frozen
  `data_cache/phase29_val808_shared_fixed_g_v1_1_canonical/` 202-D cache. **0 holdout rows,
  0 TEST rows, 0 raw image reads, 0 GT reads.**

## 4. Data access
Future maximum raw VAL image reads = **64** unique samples; VAL GT reads = **0**.
ROUTER_HOLDOUT raw images/GT **FORBIDDEN**; TEST images/GT **FORBIDDEN**; TRAIN raw images
NOT_REQUIRED. Primary figures require **no** ground truth; an optional GT overlay is
`INELIGIBLE_NOT_REQUIRED`.

## 5. FiLM contract
Sites `['bridge', 'decoder4', 'decoder3', 'decoder2', 'decoder1']`; channels `{'bridge': 256, 'decoder4': 192, 'decoder3': 96, 'decoder2': 48, 'decoder1': 24}`; four task identities.
Primary quantities: gamma per task/site/channel, beta per task/site/channel, mean(gamma), mean(abs(gamma)), std(gamma), L2 norm gamma, mean(beta), mean(abs(beta)), std(beta), L2 norm beta. Pairwise task comparisons:
L2 distance gamma, cosine similarity gamma, L2 distance beta, cosine similarity beta. No significance tests; no magnitude-as-clinical-importance
claim. phase21_film_parameter_summary.csv persists per-(task,site,parameter) SUMMARY statistics only (mean/std/min/max/l2_norm/mean_abs), NOT per-channel vectors; pairwise task comparisons therefore require loading the canonical G checkpoint and calling film_parameters_for_tasks() in the future execution (no image forward required).

## 6. Grad-CAM contract
Two targets, both resolved from source (never guessed):
`bridge` = `film_layers["bridge"]` output `[1,256,32,32]`;
`decoder1_pre_head` = `film_layers["decoder1"]` output `[1,24,512,512]`.
Target scalar: `T = mean(current_forward_foreground_logit[M_pred]) if M_pred has >= 1 foreground pixel`, else `T = mean(current_forward_foreground_logit over the full 512x512 field)`, using
`M_pred = p_global >= 0.50` from the **already-frozen** persisted prediction (never GT, never
recomputed from a new Phase35 forward for target selection).
Algorithm: alpha_k = spatial mean of dT/dA_k; `CAM_raw = ReLU(sum_k alpha_k A_k)`; bilinear
upsample to 512x512 with `align_corners=false`; min-max normalization (all-zeros if the range is 0);
float32 persisted. **No post-hoc smoothing, no Gaussian blur, no threshold chosen after viewing
results.**
Execution semantics: `GRADIENT_ENABLED_INTERPRETABILITY_DIAGNOSTIC_FORWARD` - `model.eval()`,
float32 storage/input, correct task id, `torch.enable_grad()`, `inference_mode = false`, autocast
matching the canonical G fp16 forward. Gradient context **differs** from canonical no-grad
inference; no bit-identical Phase30 reproduction is claimed; no parameter updates.

## 7. Saliency self-consistency (GT-free)
`foreground_saliency_mass_fraction = sum(CAM*M_pred)/sum(CAM)`;
`roi_saliency_mass_fraction = sum(CAM*M_roi)/sum(CAM)`; both `NULL` with a `ZERO_CAM` flag when
`sum(CAM)=0`. These measure **self-consistency with the model's own prediction/proposal**, not
localization accuracy against ground truth.

## 8. ROI / proposal contract
`t_roi = 0.30` (proposal) vs `t_seg = 0.50` (segmentation output) - never conflated. Panels show
image + global probability heatmap + predicted foreground (0.50) + ROI proposal mask (0.30) +
ROI box/crop geometry. No GT required.

## 9. Router attribution
Method `GRADIENT_X_INPUT` on the raw `delta_hat` (no sigmoid): `a_j = x_j * d(delta_hat)/d(x_j)`.
Groups: `{'bridge_global': 32, 'bridge_roi': 32, 'decoder2_global': 32, 'decoder2_roi': 32, 'decoder1_global': 32, 'decoder1_roi': 32}` plus the ten scalar features
`['entropy_proxy_mean', 'frac_prob_within_0p05_of_boundary', 'frac_prob_within_0p02_of_boundary', 'mean_boundary_margin', 'pred_foreground_fraction', 'pred_foreground_pixels', 'pred_roi_exists', 'pred_empty', 'predicted_roi_area_fraction', 'predicted_roi_side']`. Integer task ids receive **no** numeric input-gradient attribution;
the learned 16-D B_phi task embeddings are characterized statically. Counterfactual task-id
analysis = `INELIGIBLE_NOT_REQUIRED`. No perturbation, no retraining, no optimization, no p-values.

## 10. Figure contract
F1: FiLM gamma heatmap by task x site/channel-summary; F2: FiLM beta heatmap by task x site/channel-summary; F3: task-embedding geometry matrix/heatmap; F4: fixed 16-case visual panel: image + predicted foreground + ROI proposal + bridge Grad-CAM + decoder1 Grad-CAM; F5: saliency self-consistency summary by domain/layer; F6: router attribution group summary; F7: router scalar-feature attribution summary. Outcome-selected "best-looking Grad-CAM"
galleries are **forbidden**. Panel labels use dataset/domain and de-identified `sample_id` only.

## 11. Locks and status
Phase35 execution `NOT_STARTED`; Phase36 `NOT_STARTED`; TEST `LOCKED_UNTIL_PHASE39`;
ROUTER_HOLDOUT `OPENED_AND_FROZEN`. Phase30 qualifier
`ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_FREEZE_DEVIATION` applies wherever Phase30-derived route-state frequencies are reused;
Phase30 status `COMPLETE_WITH_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL` (not upgraded).
