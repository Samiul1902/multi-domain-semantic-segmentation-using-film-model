# POST-PHASE13 H2-A OUTCOME ADJUDICATION

- **Artifact:** `POST_PHASE13_H2A_OUTCOME_ADJUDICATION`
- **Status:** `PASS`
- **Created:** 2026-09-23T05:36:00Z
- **Task:** POST-PHASE13 REGIONAL REVISION — H2-A-C FORMAL H2A OUTCOME ADJUDICATION
- **Model attribution:** Gemini 3.1 Pro High
- **Execution mode:** PURE_READ_AUDIT_OF_FROZEN_EVIDENCE

---

## 1. Integrity Precondition — PASS

| Binding | SHA-256 | Required | Observed |
|---|---|---|---|
| B1 evaluation `post_phase13_h2a_training_evaluation.json` | `7ecd3a04…` | status PASS · best epoch 83 · trajectory PASS · replay PASS | **all met** |
| B2 integrity `post_phase13_h2a_downstream_integrity.json` | `c80a5b7d…` | status PASS · 457 proposals · 412 case-model · 608 component-model · 4 summary · 1828 regional · 0 localizer forwards · 0 regeneration · 0 new global · global repro PASS · 0 TEST · 0 external TEST | **all met** |

Material mismatch: **NONE**.

---

## 2. Binding SHAs

| Role | SHA-256 |
|---|---|
| H2A protocol | `0fafc793b3a814e010e1fdd48f6a2333042985eaef4a44e0382b3991800da96b` |
| B1 evaluation | `7ecd3a04fd6bfa6051afa3bd4536566d61a81287c73f34fb2e4689d0e0587899` |
| B2 integrity | `c80a5b7db16013efe1dc74d42d06a26bb5b3f4003ead8564cb4bcdb0efa4bd4b` |
| B1 proposal table | `4004e5b0b38bec11b9f63934be8efea253f20339952ac57ebf5e0b70e47e454f` |
| B1 component table | `e93163b2b42eeadf725eb60c3c7e32c90560dc87392b94b3bc8281d045250368` |
| B2 4-row model summary | `60c707519b3ade980abdc6d7c2f1e71645bb5f5fc89ed32329ec0c642a550677` |
| B2 cross-architecture | `32de3a43e907af11e07634de5ba80adeda21e63dcf3d71b1ceefdb65ede7dfd8` |
| Phase13 predicted comparator | `583dce8fc1fb214ae1b7bcf207c2b55fdcdee676b7bd5fcffa009bda64225e10` |
| Phase12 oracle comparator | `7fbf42fb7d177547a0f047b28db24c830364bdf4a82c722c79aca573e033acf3` |
| B2 reviewer notebook | `97ad366a6a2fb4f34a506829923363fb3700794b285920186f544781d6543fa7` |

---

## 3. H2A Scientific Question

> Was **deployment-balanced CHECKPOINT SELECTION ALONE** sufficient to resolve the Phase13 GT-free regional-path failure?

Not "did the localizer improve at all?" — the question is whether **selection-only redesign is sufficient as the complete localizer revision**.

Four prospectively frozen dimensions: **A** localizer proposal quality · **B** downstream global preservation · **C** regional utility · **D** cross-architecture generality. No new numerical success threshold, no weighted score, no post-hoc subgroup, no winner.

---

## 4. Dimension A — Localizer Proposal Quality

| Quantity | Phase13 (ep53) | H2A (ep83) | Δ |
|---|---|---|---|
| proposal count | 494 | 457 | −37 |
| pixel any-hit precision | 0.24696356275303644 | 0.27571115973741794 | +0.028747596984381507 |
| tiny recall90 | 0.6805555555555556 | 0.6944444444444444 | +0.01388888888888884 |
| overall recall90 | 0.5986842105263158 | 0.6381578947368421 | +0.03947368421052633 |
| overall recall50 | 0.7894736842105263 | 0.8223684210526315 | +0.0328947368421052 |
| any-overlap recall | 0.8486842105263158 | 0.875 | +0.02631578947368418 |
| mean coverage | 0.7584022780771768 | 0.7878969538240504 | +0.0294946757468737 |
| fraction at max (saturation) | 0.6821862348178138 | 0.6455142231947484 | −0.03667201162306544 |

**Adjudicated state:** `MEANINGFUL_LOCALIZER_LEVEL_IMPROVEMENT_DESCRIPTIVELY_VERIFIED`. Supports H2A at the localizer level only.

**Limitations:** descriptive only — **not** statistical superiority. Pixel any-hit precision remains only **~0.276**, so a substantial off-target proposal burden remains. No model-tensor cross-check at epochs 31/53/68.

---

## 5. Dimension B — Downstream Global Preservation

| Model | GLOBAL Dice | H2A Dice | ΔH2A−GLOBAL | GLOBAL prec → H2A prec | GLOBAL rec → H2A rec | mean FP (G→H2A) | improved / same / worse |
|---|---|---|---|---|---|---|---|
| UNet | 0.594180 | 0.313779 | **−0.280400** | 0.693919 → 0.245046 | 0.653931 → 0.686679 | 1297.25 → 8344.25 | 11 / 0 / 92 |
| Attention U-Net | 0.629805 | 0.320173 | **−0.309632** | 0.670962 → 0.253042 | 0.701770 → 0.704895 | 1377.19 → 8683.32 | 8 / 1 / 94 |
| UNet++ | 0.640516 | 0.323046 | **−0.317470** | 0.736065 → 0.254114 | 0.658330 → 0.698122 | 888.68 → 8610.66 | 8 / 1 / 94 |
| DeepLabV3+ | 0.560251 | 0.288917 | **−0.271334** | 0.708252 → 0.218756 | 0.585251 → 0.647667 | 1081.56 → 9217.14 | 13 / 0 / 90 |

Cross-case: H2A worse than GLOBAL in **all four** models for **83 / 103** cases; improved in all four for only **3 / 103**.

**Adjudicated state:** `GLOBAL_PRESERVATION_NOT_RESTORED`. **Does not support H2A.** Precision collapses while recall rises slightly — consistent with regional probability replacing global probability over the intervention union, with a large FP-burden increase across all four architectures. No new cutoff introduced.

---

## 6. Dimension C — Regional Utility

**Oracle-benefit retention — NEGATIVE for all four:** UNet **−2.147969**, Attention **−4.436652**, UNet++ **−3.684488**, DeepLabV3+ **−1.427163**.

Component evidence (favourable, preserved): recoveries vs GLOBAL **17 / 11 / 14 / 17**; losses vs GLOBAL **0 / 0 / 0 / 1**. Cross-architecture: recovered by ≥1 model **29**, by all four **5**; lost by ≥1 **1**, by all four **0**.

**Adjudicated state:** `REGIONAL_UTILITY_NOT_RETAINED`. **Does not support H2A.** The favourable recovery evidence is preserved and acknowledged, but is adjudicated **jointly** with negative Dice-vs-GLOBAL, negative oracle-benefit retention and the large FP burden. Recovery alone does **not** determine H2A success.

---

## 7. Dimension D — Cross-Architecture Generality

H2A vs Phase13 predicted Dice: UNet **+0.011466**, Attention **+0.011554**, UNet++ **+0.011691**, DeepLabV3+ **+0.011625**.

A small but highly consistent descriptive translation of the localizer-level improvement. All four H2A predictions remain **below GLOBAL**.

**Adjudicated state:** `CONSISTENT_BUT_INSUFFICIENT__FAILURE_ALSO_CROSS_ARCHITECTURE`. The selection-redesign effect is not isolated to one segmentation architecture, **but** the remaining failure is also cross-architecture general. No architecture ranking.

---

## 8. Causal-Language Correction

**Not adopted (too strong):** *"the bottleneck is the fusion mechanism, not checkpoint selection."*

**Canonical interpretation:**
> H2A shows that deployment-balanced checkpoint selection improves localizer proposal quality and yields a small, consistent downstream improvement, but selection-only redesign is insufficient to restore global preservation or oracle-benefit retention. The evidence does not isolate a sole remaining bottleneck. Residual localization / proposal quality and robustness of regional fusion to imperfect proposals remain open contributors.

**Contextual evidence:** the *same* regional-replacement principle produced **positive** Phase12 oracle gains when localization was GT-derived (UNet +0.130542, Attention +0.069790, UNet++ +0.086164, DeepLabV3+ +0.190121). Therefore **`FUSION_MECHANISM_FAILURE_PROVEN` is NOT concluded**, and **`LOCALIZER_REPRESENTATION_FAILURE_PROVEN` is NOT concluded**.

**Persisted sole-causal wording search** across `reports/`, `docs/`, the phase-13 notebook directory and workspace memory: **ABSENT**. The B2 notebook §30 explicitly states *"H2A-B2 DOES NOT adjudicate H2A. The execution returns evidence only."*

→ Classification: **`NO_PERSISTED_CLARIFICATION_REQUIRED`**. Frozen evidence was **not** rewritten and no additive clarification artifact was created.

---

## 9. H2A Outcome

### `H2A_SELECTION_REDESIGN_PARTIAL`

Matched definition: *selection-only redesign produces reproducible favourable localizer changes AND measurable downstream translation, but does NOT resolve the major global-preservation / oracle-retention failure.*

Expected evidence pattern was **tested, not assumed**, and is physically supported, so the outcome was **not forced**.

| Check | Result |
|---|---|
| Checkpoint selection contributed | **YES** |
| Checkpoint selection alone sufficient | **NO** |
| Fusion failure proven | **NO** |
| Localizer representation failure proven | **NO** |

---

## 10. Next-Axis Eligibility

- `H2B_LOCALIZER_OBJECTIVE_OR_REPRESENTATION_PROTOCOL_DESIGN`: **ELIGIBLE_FOR_SUPERVISOR_AUTHORIZATION**
- `H2B_TRAINING`: **NOT_AUTHORIZED**
- `H3_FUSION_OR_ROUTING_REDESIGN`: **REMAINS_ELIGIBLE_FUTURE_AXIS__NOT_AUTHORIZED**

Why H2B before H3: (1) H2A still leaves substantial off-target proposal burden; (2) the Phase12 oracle experiment showed the existing regional replacement mechanism can produce positive gains when localization is accurate; (3) therefore a deeper localizer objective/representation test remains scientifically justified before attributing the failure solely to fusion. This does **not** assert H2B will work. Neither H2B nor H3 was started.

---

## 11. Adaptive-Development Disclosure

H2A is adaptive VAL-development undertaken after Phase13 `REVISE_LOCALIZER` and H1 insufficiency. The H2A checkpoint-selection rule was frozen **before** training. The H2A downstream protocol was frozen **before** B2 results. VAL remains development data. No H2A result replaces final TEST. TEST remains untouched until Phase39.

---

## 12. Zero Execution

training **0** · optimizer **0** · model constructions **0** · CUDA **0** · localizer forwards **0** · segmentation forwards **0** · regional crop forwards **0** · proposal generation **0** · oracle reruns **0** · TEST reads **0** · external-test reads **0**.

New numerical thresholds **0** · new configs **0** · new subgroups **0** · winner **NONE** · statistical superiority claim **NONE**.

---

## 13. Stale Thread Control

The stale thread **"Phase13 Part1B-R0 execution-binding repair"** was **NOT** resumed (historical/stale). Canonical state: Phase13 Part1B `COMPLETE / PASS / FROZEN`; Phase13 `COMPLETE / FROZEN`; original regional gate `REVISE_LOCALIZER / FROZEN`. No Phase13 artifact was reopened.

---

## 14. Continuity

| Item | State |
|---|---|
| Phase13 | COMPLETE / FROZEN |
| Original gate | REVISE_LOCALIZER / FROZEN |
| H1 | CLOSED__PARTIAL_MITIGATION_INSUFFICIENT |
| H2A-B1 | COMPLETE / PASS / FROZEN |
| H2A-B2 | COMPLETE / PASS / FROZEN |
| H2A adjudication | COMPLETE / PASS |
| H2A | CLOSED__SELECTION_REDESIGN_PARTIAL |
| H2B protocol design | ELIGIBLE / NOT AUTHORIZED |
| H2B training | NOT AUTHORIZED |
| H3 | FUTURE_AXIS / NOT AUTHORIZED |
| Phase14 | NOT_STARTED |
| TEST | UNTOUCHED |


---

## 15. Binding Provenance Refresh (H2-A-C verification)

The immediately-preceding **authorized H2A-B2 re-verification/repair** task additively updated the
B2 integrity audit (comparator SHAs, cohort labeling, section-completeness, notebook/builder/runner
SHAs) and the reviewer notebook (required sections 14/15 content, section 1 numbering, and the
`GLOBAL_EMPTY_COMPONENTS_WITHIN_5_FROZEN_IMAGES` label). Two provenance bindings were therefore
re-pointed so this adjudication binds the **final** B1/B2 evidence:

| binding | superseded | current |
|---|---|---|
| `b2_integrity_sha` | `0c3b1175b9dd425e57ebb3770d6d37ee16be71e06fb42d24edf6ea46b8a7fec3` | `c80a5b7db16013efe1dc74d42d06a26bb5b3f4003ead8564cb4bcdb0efa4bd4b` |
| `b2_reviewer_notebook_sha` | `a6db814c781ed3d91feb5bc2b57bae7c60ebfe89e51688a4136fbe1f16fdf013` | `97ad366a6a2fb4f34a506829923363fb3700794b285920186f544781d6543fa7` |

- scientific measurements changed: **NO** · H2A result changed: **NO**
- frozen scientific tables byte-identical: **YES**
- the other 8 bindings resolve unchanged (protocol, B1 evaluation, B1 proposal table,
  B1 component table, B2 model summary, B2 cross-architecture, Phase13 comparator, Phase12 oracle)

## 16. B1 Checkpoint-Crosscheck Limitation (preserved)

`NONBLOCKING_SECONDARY_INTEGRITY_CHECK_UNAVAILABLE` —
`reports/audits/post_phase13_h2a_b1_checkpoint_crosscheck_limitation.json`
(`1ec2d7cc63c97a89c47c63ca6cdaae3382a19c97d3ce34a73c1ceb61d0582a7b`)

68 overlapping epochs reproduce the loss/LR trajectory to machine precision, strongly supporting
unchanged gradient semantics. Direct model-tensor equality at epochs 31/53/68 was unavailable
because those H2A epoch snapshots were not retained.

**No mathematical proof of identical model tensors is claimed.** This does not change the H2A outcome.

## 17. H2A Closure

| Item | State |
|---|---|
| H2A protocol | COMPLETE / PASS / FROZEN |
| H2A-B1 | COMPLETE / PASS / FROZEN |
| H2A-B2 | COMPLETE / PASS / FROZEN |
| H2A outcome | H2A_SELECTION_REDESIGN_PARTIAL |
| H2A | **CLOSED** |

No further H2A threshold search · no alternate checkpoint search ·
no combination with R1 selective acceptance.

## 18. Next Scientific Frontier

- `H2B_PROTOCOL_DESIGN`: **ELIGIBLE**
- `H2B_TRAINING`: **NOT_AUTHORIZED**
- **H2B axis selected: NONE** — H2B must address a new *single* scientific axis; no axis is
  selected here and no multiple-axis experiment is authorized.
  Candidate axes (not selected): loss/objective redesign · target/heatmap representation redesign ·
  localizer representation/head redesign.
- `H3`: FUTURE_AXIS / NOT AUTHORIZED

## 19. Supervisor Verification (this task)

- Existing H2-A-C adjudication: **VERIFIED_AND_ACCEPTED_BY_SUPERVISOR**
- outcome match: `H2A_SELECTION_REDESIGN_PARTIAL`
- no new threshold · no winner · no TEST · no Phase14 authorization · H2B protocol design eligible only
- material scientific difference: **NONE** · CHECK_REQUIRED: **NO**
- verification execution: training 0 · optimizer 0 · model constructions 0 · CUDA 0 ·
  localizer forwards 0 · segmentation forwards 0 · proposal generation 0 · TEST reads 0 ·
  external TEST reads 0

**next_action:** `WAIT_FOR_SUPERVISOR_H2B_PROTOCOL_DESIGN_AUTHORIZATION`
