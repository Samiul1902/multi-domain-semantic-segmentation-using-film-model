# Phase 35 - Executable Interpretability Source Amendment (v1.0b)

**Revision:** `ra_medfilm_barr_phase35_interpretability_v1_0b`
**Classification:** `PRE_EXECUTION_EXECUTABLE_INTERPRETABILITY_HARNESS_IMPLEMENTATION_AMENDMENT__NO_SCIENTIFIC_PROTOCOL_CHANGE`
**Phase ID (immutable):** `phase_35_interpretability`
**Method:** RA-MedFiLM-BARR

## 1. Chronology (disclosed in full)
| stage | content | outcome |
|---|---|---|
| v1.0 | scientific specification + execution source | specification **VALID**; execution source = **SKELETON / NON-EXECUTABLE FOR GOVERNED SCIENCE** |
| v1.0a | gallery-SHA reconciliation + frozen-source static preflight | **CORRECTLY BLOCKED PREMODEL** (25 of 54 load-bearing checks failed) |
| **v1.0b** | **additive executable implementation repair BEFORE the first model construction** | **this amendment** |

**No scientific output has occurred.** Model constructions 0 · checkpoint deserializations 0 ·
forwards 0 · autograd calls 0 · Grad-CAM 0 · router attribution 0 · raw VAL reads 0 · GT reads 0 ·
ROUTER_HOLDOUT reads 0 · TEST reads 0 · training 0.

## 2. Gallery identity (resolved)
`reports/tables/phase21_gallery_selection_64.csv` SHA
`2bc7c16286999ced374840cc987dcd352c3e546668322a9ccc4d1e8e8a097fd9` - 64 unique samples, 16 per
domain (ISIC/BUSI/KVASIR/KUB), all VAL808, **0 ROUTER_HOLDOUT overlap, 0 TEST overlap**. The
historical `b7d8...` mention is classified
`REPORTING_ONLY_GALLERY_SHA_TRANSCRIPTION_ERROR__CANONICAL_GALLERY_BYTES_UNCHANGED`; no new gallery
was created and membership is unchanged.

## 3. What v1.0b implements (repairing the 25 defects)
**Gates before any raw read:** repository root resolved from `__file__` (cwd independent); exact
SHA-256 verification of Phase34 final closure, Phase34 final-closure check, Phase34->Phase35
handoff, the Phase35 v1.0 specification terminal, and the canonical gallery.
**Protected data:** `guard_raw_path()` fails closed on ROUTER_HOLDOUT, TEST and GT/mask paths and on
any VAL sample outside the exact 64-sample allow-list; the persisted Phase21 npz is read with the
`prob` key only (its `gt` key is never accessed and GT-key access is counted).
**Components:** only **G** and **B_phi** are executable; `_assert_executable_component()` raises for
**R_psi** and **S_omega**, with zeroed counters for their constructions, checkpoint loads and
forwards.
**Loaders:** exact canonical constructors; checkpoint SHA verified **before** `torch.load`;
`load_state_dict(..., strict=True)`; missing/unexpected keys fail; parameter counts verified
(G 3,523,001; B_phi 36,801); float32 storage; `model.eval()`; B_phi task embedding `[4,16]`.
**FiLM / embeddings:** `film_parameters_for_tasks()` for all four tasks across the five FiLM sites
(bridge 256, decoder4 192, decoder3 96, decoder2 48, decoder1 24) with per-task/site summaries and
pairwise L2/cosine comparisons; static G `[4,32]` and B_phi `[4,16]` embedding geometry. No
significance tests.
**Grad-CAM:** hooks bound to `film_layers["bridge"]` and `film_layers["decoder1"]` only, removed
deterministically. The target mask `M_pred = persisted p_global >= 0.50` is built from the
**persisted canonical prediction** before the new forward and is **never** recomputed from current
logits; `target_masks_from_current_forward` is a counted, forbidden quantity. `T` uses current
logits float32 under `M_pred` (full-field mean fallback when `M_pred` is empty). The forward uses
`model.eval()`, float32, `torch.enable_grad()`, autocast fp16, and **no** `no_grad`/`inference_mode`;
gradients come from `torch.autograd.grad(T, [bridge_activation, decoder1_activation])` so no
parameter `.grad` accumulation or optimizer step is used. CAM: alpha = spatial mean of dT/dA;
`ReLU(sum_k alpha_k A_k)`; bilinear 512x512 `align_corners=false`; float32; exact min-max
normalization with all-zeros zero-range fallback; no blur/morphology/smoothing/outcome-dependent
clipping/post-hoc threshold.
**Threshold separation:** `T_SEGMENTATION_OUTPUT = 0.50` for `M_pred`; `T_ROI_PROPOSAL = 0.30` for
`M_roi`; asserted distinct and never interchanged.
**Router:** VAL808 non-holdout 202-D cache verified (808 rows, 192 deep + 10 scalars, 0 holdout,
0 TEST); canonical preprocessing applies the frozen Phase25D mu/sigma/constant-mask to scalar
indices 192-197 and 200-201; attribution is `a = x * d(delta_hat)/dx` on the **raw** `delta_hat`
(**no sigmoid**), with the exact six 32-D deep groups and ten scalar positions; zero denominator
yields NULL shares plus `ZERO_ROUTER_GRAD_ATTRIBUTION = true` (no epsilon, no renormalization);
integer task ids receive no numeric gradient. Canonical score reproduction is **implemented and
frozen but NOT run** in v1.0b.
**Modes:** `smoke` (synthetic only) / `film` / `gradcam` / `router` / `science`; scientific modes
require `PHASE35_EXECUTE=1`. Display subset (16 = 4/domain) is resolved from frozen gallery rank
before any saliency exists; outcome-selected panels are prohibited; F8 regional is not implemented.

## 4. Locks
Phase35 scientific execution `NOT_STARTED`; Phase36 `NOT_STARTED`; TEST `LOCKED_UNTIL_PHASE39`;
ROUTER_HOLDOUT `OPENED_AND_FROZEN`. No scientific protocol changed by v1.0b.
