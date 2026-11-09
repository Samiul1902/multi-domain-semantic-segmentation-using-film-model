# H3 — Proposal-Supply / Recall Single-Axis Design (Phase 14 clean-v3 follow-on)

**Design status:** `H3_DESIGN_FROZEN__READY_FOR_PROSPECTIVE_TRAINING_AUTHORIZATION`
**Task type:** H3 SINGLE-AXIS DESIGN — **DESIGN ONLY, NO TRAINING**
**Generated:** 2026-09-25T09:30:00Z

---

## 1. Selected axis and why it is uniquely selectable

The post-Phase-14 axis-priority diagnostic (`post_phase14_h3_axis_priority_results.json`) fired the
**A_PRIORITY** rule:

| condition | Tiny Recall | R (recall lift vs PREDICTED) |
|---|---|---|
| PREDICTED | 0.7916666667 | — |
| **A_ONLY** (GT-assisted supply) | **1.0** | **R_A = 1.0** |
| C_ONLY (FP removal) | 0.7916666667 | R_C = 0.0 |
| A_PLUS_C | 1.0 | R_AC = 1.0 |
| ORACLE_REGIONAL | 1.0 | (ceiling) |

- **A-only** restores Tiny Recall to 1.0 → missing **proposal supply** is *causally necessary* for the regional Tiny-recall signal.
- **C-only** leaves Tiny Recall unchanged (R_C = 0.0) → contamination is *not* the recall bottleneck.

→ Eligible H3 axis = **`A_PROPOSAL_SUPPLY_RECALL_LIMITATION`**. Exactly one axis selected.

Frozen references: `Tg = 0.7916666666666666`, `G = 0.20833333333333337`, `Dg = 0.6359172411726776`,
`Dice_gate = 0.6159172411726777`. Zero-proposal components: **79 GT / 57 TINY**.

---

## 2. Static root-cause analysis (supply loss)

Pipeline (frozen Stage-4D): image → Phase-13B localizer (128 heatmap) → sigmoid →
`extract_predicted_components` (prob ≥ 0.10, 8-connected, sorted by max prob, top 100) →
`non_max_suppression(iou=0.30)[:top_k=5]` → `apply_context_margin(0.20)`.

**Mechanism of loss:** `make_gaussian_heatmap` applies a **single fixed `sigma = 0.75`** to *every*
component regardless of size. Tiny components therefore receive a **diffuse, low-contrast positive
target**. The localizer — trained on many such peaks weighted toward larger components — learns to emit
smoothed blobs; the tiny-component center peak is suppressed below the 0.10 decode threshold or merged
into a neighboring larger peak, so **no component and hence no proposal** is emitted.

**Evidence:** 57/72 TINY and 79/152 total GT components are zero-proposal under the frozen policy;
supplying one GT-assisted ROI per zero-proposal component restores 100% of them (A-only recall_TINY = 1.0).

---

## 3. Selected intervention — Option A: target-support redesign

Replace the single fixed `sigma = 0.75` with a **per-component, size-adaptive sigma** derived from the
component's area in heatmap space:

```
sigma_i = clip(scale_ref * sqrt(area_i), sigma_min, sigma_max)
```

Tiny components (small area) → **smaller sigma → sharper, higher-contrast peak**; large components
capped at the historical `sigma_max = 0.75`. Canonical center pixel stays `1.0`; pixelwise-max fusion
unchanged.

**Why this option (selection rule):** pick the intervention most directly matched to the identified
mechanistic root cause with the *smallest blast radius*. Target-support redesign is mechanism-matched
(diffuse tiny targets → sharper tiny targets) and touches only the target-generation module
(`make_gaussian_heatmap`), with a backward-compatible default so every other pipeline is untouched.

**Rejected:**
- **B — positive-objective reweighting:** reweights the loss on the *same diffuse* targets; less
  directly matched. Rejected to keep a single clean axis.
- **C — recall-oriented output head:** changes architecture/head (largest blast radius), conflating an
  architecture change with the target-support hypothesis. Rejected to preserve single-axis isolation.

---

## 4. Freeze (all non-H3 axes)

| Axis | State |
|---|---|
| Dataset (phase4_v3 FULL_FIELD, 770/103) | UNCHANGED |
| Localizer input (512 res, 128 heatmap, 1ch) | UNCHANGED |
| Localizer architecture (KUBLocalizer base16, CenterNetFocal α=2 β=4) | UNCHANGED (only target support changes) |
| Training script / config (Phase-13B) | REUSED, UNCHANGED |
| Optimizer / scheduler / seed 42 | UNCHANGED |
| Proposal extraction (thr 0.10, margin 0.20, top_k 5, nms 0.30) | UNCHANGED |
| Fusion rule (MAX-prob replacement in proposal union) | UNCHANGED |
| Downstream refiner (Phase-14 epoch 56) | UNCHANGED |
| Global baseline (Phase-10 UNet++ epoch 70) | UNCHANGED |
| Downstream eval script | UNCHANGED |
| TEST / External TEST | CLOSED (0 reads) |

**Only changed axis:** localizer training-target support (size-adaptive sigma).

---

## 5. Proposed experiment

- **experiment_id:** `h3_kub_localizer_sigma_adaptive_sizeaware_seed42_clean_v3`
- Retrain the Phase-13B localizer with identical architecture, data, seed, optimizer, and proposal
  policy; **change only the training-target support**.
- Produces a new deployable localizer checkpoint, selected by the supply-aware VAL rule (§7).

**Bound parent:** Phase-13B localizer `best.pt` epoch 53, SHA `7673c34a…`, target sigma 0.75,
CenterNetFocalLoss(α=2,β=4) — NOT fine-tuned, NOT re-evaluated here.
**Bound downstream:** Phase-14 refiner epoch 56 `2e09e3a9…`; Phase-10 UNet++ epoch 70 `ec7eb13f…`.

---

## 6. Prospective criteria

**Primary supply criteria (necessary, not sufficient):**
- Zero-proposal TINY ≤ **20/72** (recover ≥ 37 of 57)
- Zero-proposal GT ≤ **35/152** (recover ≥ 44 of 79)

**Minimum meaningful improvement (downstream adjudication gate):**
- `R_H3 = (TinyRecall_H3 − Tg) / G ≥ 0.30`
- Equivalent Tiny Recall ≥ `0.8541666666666666`

**Failure boundary — `H3_SUPPLY_REDESIGN_INSUFFICIENT`** (fires if EITHER):
- Zero-proposal TINY after H3 ≥ **45/72** (recovers < 12 of 57), **OR**
- `R_H3 < 0.15` (Tiny Recall_H3 < `0.8229166666666666`)

→ If fired: target-support redesign declared insufficient; H3 NOT closed; Phase-15 stays
NOT_STARTED_AND_NOT_AUTHORIZED; consider Option B/C under fresh authorization.

**Contamination = observational only** (C-only did not move Tiny Recall; FP/Dice tracked but not gated).

---

## 7. Downstream evaluation plan

```
H3 localizer → heatmap(128) → generate_predicted_rois(thr 0.10, margin 0.20, top_k 5, nms 0.30)
  → proposal union (MAX-prob replacement) → Phase-14 refiner epoch 56 → segmentation
  → per-size recall
```

- **Primary metric:** Tiny Recall (stratum TINY, 72 components).
- **R_H3 = (TinyRecall_H3 − Tg) / G**, Tg=0.7916666666666666, G=0.20833333333333337.
- **Contrasts:** GLOBAL (Phase-10 UNet++), PREDICTED (Phase-13B + Phase-14 refiner), H3, ORACLE_REGIONAL (ceiling).
- **Secondary:** recall SMALL/MEDIUM/LARGE, hard_tiny_recall, global_empty_recovered, dice_mean, fp_components_per_image.

**Checkpoint-selection rule** (during H3 localizer training): select best VAL **localization recall**
(fraction of GT components whose centroid falls within a predicted peak ≥ 0.10 within margin 0.20),
tiebreak by lower VAL loss. Selected checkpoint is frozen and used downstream. See
`h3_proposal_supply_checkpoint_selection_rule.json`.

---

## 8. Governance

- No training performed; no H3 checkpoint created.
- No scientific parameter selected using B2/H2C results.
- TEST reads = 0; EXTERNAL_TEST reads = 0.
- Phase-15 status: NOT_STARTED_AND_NOT_AUTHORIZED.
- Single intervention only (target-support redesign).

See companion artifacts: `h3_proposal_supply_*` (static trace, code-change spec, changed-files,
unchanged-axes matrix, success/failure criteria, checkpoint-selection rule, pre-execution checklist).
All source/artifact files are SHA-256 bound in `h3_proposal_supply_design_protocol.json`.
