# POST-PHASE-13 H2-A — LOCALIZER SCORE-PATH AUDIT

- status: **COMPLETE**
- **verdict: `SCORE_PATH_IMPLEMENTATION_VALID`**
- method: STATIC code inspection + static checkpoint tensor inspection. No model construction, no forward pass, no CUDA request.

## Observed phenomenon

| item | value |
|---|---|
| plateau score | `0.1250653713941574` |
| proposals at plateau | **337 / 494** |
| fraction | 0.682186 |
| equivalent logit | -1.9453126016481 |

## Score path (6 stages, inspected physically)

| stage | location | detail |
|---|---|---|
| 1. model logits | `src/models/kub_localizer.py:forward -> self.head(...) -> logit_downsample` | KUBLocalizer emits (1,1,128,128) logits; final layer `head` is a 1x1 conv (1,16,1,1) with bias. |
| 2. probability transform | `src/inference/learned_roi_clean_v3.py:171` | heatmap = torch.sigmoid(logits)[0, 0].float().cpu().numpy() -> (128,128) float32 in [0,1]. |
| 3. component proposal extraction | `src/inference/predicted_roi.py:extract_predicted_components` | binary = probability_map >= threshold; scipy.ndimage.label with 3x3 (8-connectivity); per-component bbox + pixel count. |
| 4. score assignment | `src/inference/predicted_roi.py:142-143` | max_probs = scipy.ndimage.maximum(probability_map, labels=labeled, index=indices); max_probability = float(max_probs[cid-1]) -> per-component MAXIMUM sigmoid probability. |
| 5. NMS | `src/inference/predicted_roi.py:47-53,145,154` | components sorted by (-max_probability, bbox); deterministic score-descending box NMS at nms_iou. |
| 6. top-k + serialization | `src/inference/predicted_roi.py:154-162` | components[:top_k]; proposal dict {'rank','score': max_probability, ...}. Score written as raw Python float. |

## Defect matrix — all NEGATIVE

| suspected defect | present | evidence |
|---|---|---|
| hard_clamp | **NO** | no torch.clamp / np.clip / min / max on the probability or score anywhere in the score path |
| normalization_to_fixed_ceiling | **NO** | no division or rescaling of the heatmap or score |
| rounding_of_score | **NO** | score stored as raw float; no round()/np.round on the score |
| quantization | **NO** | probability stays float32 from sigmoid to serialization; no uint8 cast |
| incorrect_sigmoid_application | **NO** | torch.sigmoid applied on logits in learned_roi_clean_v3.py:171 |
| double_sigmoid | **NO** | model forward returns logits only (no internal sigmoid in kub_localizer.py); sigmoid applied exactly once |
| post_processing_rescale | **NO** | no post-hoc rescale between sigmoid and score assignment |
| wrong_heatmap_channel | **NO** | indexing [0, 0] = batch 0, channel 0; out_channels == 1 |
| wrong_local_max_extraction | **NO** | scipy.ndimage.maximum per label is the correct per-component maximum |
| serialization_truncation | **NO** | float written at full precision; 0.1250653713941574 round-trips exactly in the frozen CSV |
| top_k_score_replacement | **NO** | top_k only truncates the sorted list; scores are never overwritten |
| threshold_substitution | **NO** | threshold is used only for binarization (>= threshold); it never becomes the score |

### Summary

- sigmoid application: **EXACTLY_ONCE**
- score clipped: **NO** · normalized: **NO** · rounded: **NO**
- serialization truncation: **NO**
- **0.125065 maximum imposed by code: NO**

## Root cause of the plateau

**TRAINED_MODEL_OUTPUT_PROPERTY__NOT_A_SCORE_PATH_DEFECT**

The plateau equals sigmoid(head output). The trained head is degenerate: all 16 channel weights are NEGATIVE and nearly identical in magnitude (range -0.20109390 to -0.20757976, std 0.00180099, abs-max/abs-mean = 1.019491, 0/16 positive), so the head is effectively -0.203611 * sum(features) + bias. The bias is -1.9453773498535156, whose sigmoid is 0.12505828655695442 - essentially the observed plateau (0.1250653713941574, which corresponds to logit -1.9453126016481144). The head therefore produces a NEAR-CONSTANT output field, and the plateau is the sigmoid of that near-constant logit.

### Head tensor evidence (static checkpoint inspection)

| item | value |
|---|---|
| head.weight shape | `[1, 16, 1, 1]` |
| weight range | -0.20757976 … -0.20109390 |
| weight mean / std | -0.20361109 / 0.00186005 |
| abs-max / abs-mean ratio | **1.019491** (1.0 = perfectly uniform magnitude) |
| sign distribution | positive **0** / negative **16** of 16 |
| head.bias | -1.9453773498535 |
| sigmoid(bias) | 0.12505828655695 |
| head init marker | `phase13b_centernet_head_init_p01_v1 (weight=0, bias=logit(0.1))` |

All 16 channel weights are **negative and nearly identical in magnitude**, so the head is effectively
`-0.203611 · Σfeatures + bias`. The bias sigmoid (0.12505828655695442) is essentially the observed plateau
(0.1250653713941574 → logit -1.9453126016481144). The head therefore produces a **near-constant output
field**, and the plateau is the sigmoid of that near-constant logit.

## Material scientific observation (recorded, not hidden)

**`DEGENERATE_LOCALIZER_HEAD__NEAR_CONSTANT_OUTPUT`** — severity MATERIAL ·
is score-path defect: **NO** · blocks H2A freeze: **NO**

Recorded, not hidden. Because the heatmap is near-constant, no checkpoint-selection rule can substantially improve proposal precision on its own. H2A is therefore a genuine and necessary test of the selection axis, but this finding pre-registers a plausible reason H2A may prove insufficient - in which case representation/objective redesign (not selection) becomes the indicated direction.

## Bindings

| binding | SHA-256 |
|---|---|
| h1_adjudication | `3ad8be7f31a31f987a0c3e24cfe591ec9a87e1b5421a9839d288bb92737f9009` |
| r0_clarification | `6ff0495978c808e30bf3f72bf99cc72c06fea73cdcaf77a483d4def17190f3e6` |
| localizer_best_pt | `7673c34a2f2c86eca2e45c1bc6abe77842d17cd09f122f2da0f2d414ca492273` |
| history_csv | `344cfc016fd88e7e697c6afa0ffbf839b3d3b3c16b54024dc3537586528d4c5b` |
| source learned_roi_clean_v3 | `613e03d6e4dccccce2b743974dfaccd8a29a2c0932048f0af3d37a6d2a0241bf` |
| source predicted_roi | `bd9f8be84595f49ff1e25e6052b548488fb6ae6a48aa7adbc78b880fb8f2d4e7` |
| source kub_localizer | `b94e6068b60ba3f6f833745c19c2b58cb119312ad0fa642abbad85b92420af0c` |

## Counters

| counter | value |
|---|---|
| training | **0** |
| optimizer | **0** |
| model_constructions | **0** |
| cuda_requests | **0** |
| localizer_forwards | **0** |
| segmentation_forwards | **0** |
| regional_forwards | **0** |
| proposal_generation | **0** |
| checkpoint_writes | **0** |
| test_reads | **0** |
| external_test_reads | **0** |
