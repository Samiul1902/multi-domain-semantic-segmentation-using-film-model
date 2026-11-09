# POST-PHASE-13 H2-B-A — OBJECTIVE-ONLY LOCALIZER REDESIGN PROTOCOL (FROZEN)

- **Artifact:** `POST_PHASE13_H2B_PROTOCOL_FROZEN`
- **Status:** `SUPERVISOR_FROZEN_H2B_OBJECTIVE_ONLY_READY_FOR_B1_AUTHORIZATION`
- **Model attribution:** Gemini 3.1 Pro High
- **Experiment id:** `post_phase13_h2b_kub_localizer_r512_h128_sigmaeq075_softtargetfocalgamma2_deploymentbalance_seed42_clean_v3`
- **Collision:** NONE (`checkpoints/` and `experiments/` paths absent)

---

## 1. Authoritative H2A binding

| Field | Value |
|---|---|
| artifact | `reports/audits/post_phase13_h2a_outcome_adjudication.json` |
| status | PASS |
| h2a_outcome | `H2A_SELECTION_REDESIGN_PARTIAL` |
| h2a | `CLOSED` |
| H2B protocol design | ELIGIBLE |
| H2B training | NOT_AUTHORIZED |
| material mismatch | NONE |

Preserved interpretation — checkpoint selection contributed **YES** · alone sufficient **NO** ·
fusion failure proven **NO** · localizer representation failure proven **NO**.

---

## 2. The single scientific axis

**`H2B_SOFT_TARGET_FOCAL_BCE_OBJECTIVE_ONLY`** — axis: **LOSS / OBJECTIVE SEMANTICS**.

> Compared with the immediate **H2A** branch baseline, H2B changes exactly one new scientific
> axis: **LOSS / OBJECTIVE**. (Phase13 is historical context; H2B does not differ from Phase13
> in only one field.)

---

## 3. Frozen objective — `SoftTargetFocalBCE`

```
p          = sigmoid(z)
bce        = BCEWithLogits(z, y, reduction="none")
modulation = |p - y| ** gamma
loss_map   = modulation * bce
L          = mean(loss_map)
```

equivalently

```
L = mean( |sigmoid(z) - y|^2 * BCEWithLogits(z, y) )        # gamma = 2.0 FIXED
```

- **gamma = 2.0**, fixed **prospectively**. No grid, no alpha sweep, no beta sweep,
  no coefficient search. gamma=2 is **not** claimed optimal.
- **Modulation detached: NO.** Gradients flow through **both** the BCE term and the
  modulation term.
- Target is **asserted** finite and within `[0, 1]` — **never silently clamped**.
- No extra regularizer · no Dice term · no sparsity penalty · no class weight ·
  no additional coefficient · no auxiliary loss.
- Implementation: `src/losses/soft_target_focal_bce.py` (`SoftTargetFocalBCE`).
  Loss only — no dataset, proposal, checkpoint, architecture or target logic.

---

## 4. Target — UNCHANGED

Existing H2A / Phase13 generator (`src/inference/heatmap_targets.py`). Heatmap 128×128,
sigma 0.75, center exactly 1.0, values in [0,1]. No binary conversion, no target threshold,
no new disk radius, no sharpening, no smoothing, no sigma search.

**`TARGET_CHANGED: NO`** · **`OBJECTIVE_INTERPRETATION_OF_TARGET_CHANGED: YES`**

---

## 5. Architecture — UNCHANGED

`src/models/kub_localizer.py` (`KUBLocalizer`): in 1 · out 1 · base 16 · same 3-stage compact
U-Net · same decoder · same final 1×1 head · same weight init `kaiming_normal_(relu)` ·
same head init (weight 0.0, bias `log(0.1/0.9)`). No extra convolution, attention, FiLM,
normalization change, activation change or head-capacity change.

**`ARCHITECTURE_CHANGED: NO`** · **`HEAD_CHANGED: NO`**

---

## 6. Checkpoint selection — UNCHANGED (inherited from H2A)

Six-term strict lexicographic tuple:
`DEPLOYMENT_BALANCE_HMEAN_P_TINY90_OVERALL90 > tiny_recall90 > overall_recall90 >
PROPOSAL_PIXEL_ANY_HIT_PRECISION > -mean_roi_area_fraction > -val_loss`.
Ties = `BAD_EPOCH` · patience 15 · `best.pt` strict improvement only · `latest.pt` every epoch.
**`CHECKPOINT_SELECTION_CHANGED: NO`**

---

## 7. Training contract

TRAIN 770 FULL_FIELD / 1161 components · VAL 103 FULL_FIELD / 152 components · ROI EXCLUDED ·
`phase4_v3` · `kub_size_clean_v3_v1` · input 512×512 · heatmap 128×128 · sigma 0.75 ·
AdamW · lr 1e-4 · wd 1e-4 · `CosineAnnealingLR(T_max=100)` · batch 4 · AMP same accepted
semantics · seed 42 · augmentation same Phase13/H2A semantics · workers 0 · max epochs 100 ·
CUDA required during future execution · **TEST forbidden**.

## 8. Proposal contract

threshold **0.10** · margin **0.20** · top_k **5** · NMS IoU **0.30**. No threshold search,
no score-floor filtering, no H1 selective acceptance, no grid, no top-k change, no NMS change.

---

## 9. Static one-axis diff audit

`reports/tables/post_phase13_h2b_protocol_diff_vs_h2a.csv` — 52 fields compared.

| role | fields | changed |
|---|---|---|
| SCIENTIFIC_AXIS | `loss_name`, `loss_mathematical_semantics` | **2** |
| PROVENANCE | `experiment_id`, `protocol_binding`, `loss_implementation_sha` | 3 |
| ARCHITECTURE / TARGET / DATA / OPTIMIZATION / CHECKPOINT_SELECTION / PROPOSAL / FUSION | 47 | **0** |

Architecture NO · target NO · sigma NO · optimizer NO · scheduler NO · augmentation NO ·
data NO · seed NO · proposal config NO · checkpoint selection NO · fusion NO.

---

## 10. Synthetic loss / gradient audit (CPU-only)

`reports/audits/post_phase13_h2b_soft_target_focal_loss_unit_audit.json` ·
`reports/tables/post_phase13_h2b_soft_target_focal_gradient_sanity.csv` (35 rows).

All checks **PASS**: finite losses/gradients (no NaN, no Inf) · y=0 loss increases as p→1 ·
y=1 loss increases as p→0 · soft target minimised at/near p=y · symmetry
`L(y=0,p=q) ≈ L(y=1,p=1−q)` (max abs diff 4.77e-7) · modulation **not detached** ·
target out-of-range and non-finite both rejected.

No model construction · no CUDA · no project images or masks.

---

## 11. Future execution structure (nothing authorized now)

- **H2B-B1** — single localizer training run + per-epoch frozen proposal evaluation +
  best-checkpoint standalone localizer evaluation → **STOP for supervisor review**.
- **H2B-B2** — only after B1 supervisor authorization: same four frozen downstream
  architectures, same global cache, same crop/restore, same replacement fusion, same proposal
  config, same segmentation threshold, no H1 filtering.

B1 reviewer notebook must render a **complete untruncated epoch table** (one row per completed
epoch) with `epoch, train_loss, val_loss, P, T, O, deployment_balance_hmean, proposal_count,
mean_roi_area, checkpoint_tuple, is_new_best, bad_epochs`, plus proposal-score distribution,
score-saturation fraction, ROC-AUC, PR-AUC and head weight/bias statistics —
**head statistics are DIAGNOSTIC ONLY and are not used for checkpoint selection**.

---

## 12. Prospective evidence dimensions

**A** localizer proposal quality · **B** downstream global preservation ·
**C** regional utility · **D** cross-architecture generality.
No numerical success threshold · no weighted downstream score · no winner.

Outcome space (NOT adjudicated now): `H2B_OBJECTIVE_REDESIGN_SUFFICIENT` /
`H2B_OBJECTIVE_REDESIGN_PARTIAL` / `H2B_OBJECTIVE_REDESIGN_INSUFFICIENT` / `CHECK_REQUIRED`.

---

## 13. Scientific change register

| id | field | H2A | H2B |
|---|---|---|---|
| `CHANGE_H2B_001` | training objective / loss semantics | `CenterNetFocalLoss(alpha=2.0,beta=4.0)` | `SoftTargetFocalBCE(gamma=2.0)` |

Formula: `mean( |sigmoid(logit)-target|^2 * BCEWithLogits(logit,target) )`.
Target UNCHANGED · architecture UNCHANGED · checkpoint selection UNCHANGED. **No causal claim.**

---

## 14. Adaptive-development disclosure

H2B is adaptive VAL development informed by Phase13 `REVISE_LOCALIZER`, H1 insufficiency and
the H2A partial outcome. The objective was frozen **before** H2B training. VAL remains
development data. TEST remains locked until Phase39. No H2B development result replaces final TEST.

---

## 15. Zero execution

training **0** · optimizer construction **0** · localizer model construction **0** · CUDA requests **0** ·
localizer forwards **0** · proposal generation **0** · segmentation model construction **0** ·
segmentation forwards **0** · TEST reads **0** · external TEST reads **0**.
CPU synthetic scalar/tensor loss-unit tests: **authorized and performed** (no project images or masks).

---

## 16. Continuity

| Item | State |
|---|---|
| Phase13 | COMPLETE / FROZEN |
| Original gate | REVISE_LOCALIZER / FROZEN |
| H1 | CLOSED |
| H2A | CLOSED__SELECTION_REDESIGN_PARTIAL |
| H2B protocol | COMPLETE / PASS / FROZEN |
| H2B-B1 execution | ELIGIBLE_FOR_SUPERVISOR_AUTHORIZATION (AUTHORIZED: FALSE) |
| H2B-B2 | NOT_STARTED |
| H3 | FUTURE_AXIS / NOT_AUTHORIZED |
| Phase14 | NOT_STARTED |
| TEST | UNTOUCHED |

**next_action:** `WAIT_FOR_SUPERVISOR_H2B_B1_EXECUTION_AUTHORIZATION`
