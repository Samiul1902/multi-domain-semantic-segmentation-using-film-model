# Hypotheses and Claim-to-Evidence Matrix — RA-MedFiLM-BARR

**Document ID** `phase36_hypotheses_claim_evidence_v1_0`
**Status** `AUTHORITATIVE_FOR_HYPOTHESIS_AND_CLAIM_CLASSIFICATION`
**Applies to** the FULL method (RA-MedFiLM-BARR), the Lite variant
(RA-MedFiLM-BARR-Lite/`depthwise_compact`), and every derived comparison.

---

## 0. Why this document exists

Before this revision, H1–H7 and the claim-to-evidence classification existed only
inside an internal audit (`reports/audits/stages1_to5_completion_review.md`). An
internal audit is not a citable artifact: a claim whose only home is an audit can
drift, be quoted out of context, or be silently upgraded.

This document is the authoritative home. It does not introduce new results, does
not change any metric, and does not promote any exploratory finding. It records
**what is claimed, what would falsify it, and what class of evidence currently
supports it.**

The manuscript's own formal hypothesis — the frozen C1 directional test in §9.2
(H₀: Δ_macro ≤ 0 vs H₁: Δ_macro > 0) — is a **different object** and is not
restated here.

---

## 1. Evidence classes (the only permitted labels)

Every claim below carries exactly one of these. The distinctions are load-bearing:
"code exists" is not "verified", and "verified" is not "scientifically supported".

| Class | Meaning | May be cited as |
|---|---|---|
| `IMPLEMENTATION_COMPLETE` | The producer exists and executes. | An engineering statement only. |
| `TECHNICAL_VERIFICATION_PASSED` | An automated test proves the stated mechanical property. | A statement about the code, never about accuracy. |
| `SCIENTIFIC_DESIGN_SUPPORTED` | The design rationale is argued and internally consistent. | A design statement, never a result. |
| `FUTURE_EVIDENCE_PENDING` | The experiment required to support the claim has not been run. | Nothing. Must be reported as pending. |
| `UNRESOLVED_DEFECT` | A known defect or limitation that blocks or qualifies the claim. | Must be disclosed alongside the claim. |

Two rules that follow from the above and are not negotiable:

1. **No unconditional "CERTIFIED" label** may be attached to a stage, a component
   or the pipeline. A stage may be `IMPLEMENTATION_COMPLETE` and
   `TECHNICAL_VERIFICATION_PASSED` while its scientific claim remains
   `FUTURE_EVIDENCE_PENDING`.
2. **A synthetic run is never evidence.** Synthetic artifacts are stamped
   `synthetic: true` / `protocol_faithful: false` and may only support
   `TECHNICAL_VERIFICATION_PASSED`.

---

## 2. Hypotheses, falsification criteria and current status

| ID | Claim | Falsification criterion | Status | Evidence class |
|---|---|---|---|---|
| **H1** | Task-conditioned FiLM (γ/β) improves macro Dice over the frozen identity control C1-C on VAL808 across seeds 42 / 123 / 3407 | the lower bound of the 95 % paired cluster-percentile bootstrap CI is ≤ 0.0 pp | 0 of 6 C1 runs executed; the FiLM-off control is silent on BARR because the GlobalMedFiLM checkpoint carries zero router/safety tensors | `FUTURE_EVIDENCE_PENDING` |
| **H2** | Learned ΔQ routing suppresses harmful refiner activations by ≥ 70 % relative to the always-refine arm A1 | reduction < 70 % | 75.69 % exists as a **historical in-sample descriptive** figure only | `FUTURE_EVIDENCE_PENDING` |
| **H3** | S_ω rejects degrading candidates at inference without ground truth | final harm rate exceeds the unconditional harm rate | historical descriptive only; no safety-*specific* metric and no `S_ω`-absent arm exist | `FUTURE_EVIDENCE_PENDING` |
| **H4** | On ROUTER_HOLDOUT (n = 875) BARR preserves global accuracy while cutting refiner execution by > 75 % | preservation rejected, or compute reduction < 70 % | +0.17 pp is a **retrospective, non-confirmatory** descriptive difference | `FUTURE_EVIDENCE_PENDING` |
| **H5** | End-to-end inference uses only (image, task_id) | any inference signature accepts a label-like argument | asserted by signature audit and by the four-branch harness | `TECHNICAL_VERIFICATION_PASSED` |
| **H6** | Zero-shot external transfer exposes the 14 / 14 stone-free false-positive failure | suppression, omission or concealment of that finding | descriptive, all 14 `fp_only_case` are true | `SCIENTIFIC_DESIGN_SUPPORTED` (descriptive disclosure only) |
| **H7** | RA-MedFiLM-BARR-Lite/`depthwise_compact` reaches the same four-component graph contract at ≤ 50 % of the FULL family parameter count | reduction < 50 %, or a broken GT-free interface, or a parameter identity that cannot be reproduced from the built models | 272,601 vs 4,837,420 = **94.3647 % reduction**, reproduced from the instantiated models | `TECHNICAL_VERIFICATION_PASSED` |

### 2.1 H7 arithmetic — the denominator that must be used

The reduction compares **complete four-component families**, not a family against a
single backbone:

| Quantity | Parameters |
|---|---|
| Lite G | 176,454 |
| Lite R_ψ | 58,129 |
| Lite B_φ (canonical Phase-25 model) | 36,801 |
| Lite S_ω (canonical Phase-25 model) | 1,217 |
| **Lite family total** | **272,601** |
| FULL G | 3,523,001 |
| FULL R_ψ | 1,276,401 |
| FULL B_φ | 36,801 |
| FULL S_ω | 1,217 |
| **FULL family total** | **4,837,420** |

`1 − 272,601 / 4,837,420 = 94.3647 %`.

Two recorded traps:

* **3,523,001 is the FULL G alone**, not the FULL family. Dividing by it yields
  92.26 %, which is the wrong denominator and understates the reduction.
* **1,586,817 has no provenance.** It appears in no artifact, in no commit
  (`git log -S` is empty), and equals no subset-sum of the ten real component
  sizes. It must not be cited.

B_φ and S_ω are the **same canonical Phase-25 models** in both families, so the
36,801 and 1,217 appear on both sides and cancel; the reduction is driven entirely
by G and R_ψ. That is why the identity is checkable from the built models rather
than from a metadata assertion.

---

## 3. Claim-to-evidence matrix

Each row states the strongest claim permitted **today**, and what would be needed
to strengthen it. No row may be upgraded without a new artifact.

| # | Claim as it may be written today | Class | Supporting artifact | What would strengthen it |
|---|---|---|---|---|
| 1 | The FULL G→R→B→S pipeline is implemented and executes end to end. | `IMPLEMENTATION_COMPLETE` | `src/research/full_pipeline/`, 24-test suite | — |
| 2 | The three-seed FULL DAG passes on a synthetic population, including exact resume and all four inference branches. | `TECHNICAL_VERIFICATION_PASSED` | `tests/test_full_pipeline.py` | — |
| 3 | The Lite DAG (G→CACHE→R→L→B→S) is implemented and passes on a synthetic population for seeds 42 / 123 / 3407. | `TECHNICAL_VERIFICATION_PASSED` | `src/research/lite_pipeline/`, `tests/test_lite_pipeline.py` | — |
| 4 | The Lite family totals 272,601 unique parameters and reduces the FULL family by 94.3647 %. | `TECHNICAL_VERIFICATION_PASSED` | `src/research/lite_pipeline/recipe.py::parameter_identity` | — |
| 5 | B_φ and S_ω are single shared definitions with no architecture drift. | `TECHNICAL_VERIFICATION_PASSED` | `src/models/barr/phase25_models.py`, `tests/test_phase25_architecture_drift.py` | — |
| 6 | End-to-end inference is ground-truth free. | `TECHNICAL_VERIFICATION_PASSED` | signature audit, four-branch harness | — |
| 7 | OOF labels are refiner-, router- and safety-cross-fitted **but backbone-in-sample**. | `UNRESOLVED_DEFECT` (disclosed, not repaired) | `oof_contract` in the L manifest; §4 below | a strict backbone-OOF construction (§5) |
| 8 | The historical external transfer result (884 cases; 612 CVC / 252 BrEaST / 20 Stones) is a **retrospective** descriptive finding. | `SCIENTIFIC_DESIGN_SUPPORTED` | `test_c1_external_evidence.py` | a prospective, pre-registered external evaluation |
| 9 | The 14 / 14 stone-free false positives are disclosed prominently. | `SCIENTIFIC_DESIGN_SUPPORTED` | external per-case records | — |
| 10 | The controlled 8-model × 3-seed comparison is **not** established. | `FUTURE_EVIDENCE_PENDING` | `src/research/stage6/matrix.py` — 24 / 24 cells `MISSING` | 24 protocol-compliant cells |
| 11 | C1 FiLM attribution, BARR router+safety attribution and protocol-faithful baselines are not established. | `FUTURE_EVIDENCE_PENDING` | audit `36fe4337…` | C1 execution under institutional approval |
| 12 | No Lite accuracy, efficiency or external result exists. | `FUTURE_EVIDENCE_PENDING` | no Lite cell in any table | real Lite training + VAL808 evaluation |

---

## 4. The standing OOF limitation

The primary label construction is **matched to the frozen Phase-25D/25F
artifacts**, which means it is:

* `refiner_out_of_fold: true` — fold-k's refiner labels fold-k's outer target;
* `router_out_of_fold: true`;
* `safety_out_of_fold: true`;
* **`backbone_out_of_fold: false`** — G is fitted once on all 5,832 TRAIN rows,
  which include every one of the 4,957 labelling samples.

Consequence, which must accompany any absolute number derived from these labels:
`delta_dice` measures what a fold-k refiner does to the output of a backbone that
already memorised the sample. Absolute harm rates are therefore **optimistic** and
must never be read as held-out generalisation.

This is disclosed, not repaired. Repairing it would break comparability with the
historical FULL labels, which is the only reason the construction exists in this
form. A versioned strict construction is available as an opt-in (see §5); it is
**not** the primary construction and must never silently replace it.

`ROUTER_HOLDOUT` (n = 875) is excluded from label generation, but it is **not**
excluded from backbone training. Those are different guarantees and must not be
conflated: the holdout protects the router/safety cross-fit, not the backbone.

---

## 5. Strict backbone-OOF extension

`src/research/lite_pipeline/strict_oof.py` implements, and tests, the reusable
parts of a strict construction:

* a fold-aware record naming, per outer fold, the only sample ids the backbone may
  train on;
* target-fold exclusion validation that fails closed;
* checkpoint provenance requirements (protocol version, fold index, training
  population digest).

It performs **no training** and produces **no performance number**. The protocol
version is `ra_medfilm_barr_lite_strict_backbone_oof_v1`, distinct from the
primary `ra_medfilm_barr_matched_full_oof_v1`.

Enabling it for real requires `3 folds × 3 seeds = 9` additional backbone
trainings, a separate evaluation contract and a separate result namespace. Until
then, no strict-OOF number may be quoted.

---

## 6. Language rules for the manuscript

1. The external robustness finding is **retrospective** and **descriptive**. It is
   not prospective validation and it is not evidence of universal clinical safety.
2. VAL808 numbers are **development-selection-consumed**; they are not independent
   confirmation. The label
   `VAL808_DEVELOPMENT_SELECTION_CONSUMED__NOT_INDEPENDENT_CONFIRMATION` must
   accompany them.
3. No claim of superiority over any baseline may be made while the corresponding
   Stage-6 cell is `MISSING`.
4. The Lite variant carries **no accuracy claim at all**; only a parameter identity
   and a mechanical graph contract.
5. A negative or null finding must be reported with the same prominence as a
   positive one, and must not be removed by re-analysis.

---

## 7. Change control

This document is versioned. A claim may move to a stronger class only by adding a
new artifact and recording it in §3. Removing or weakening a row is a
documentation regression, not a simplification.

* `v1_0` — first authoritative issue; supersedes the H1–H7 catalogue that existed
  only in `reports/audits/stages1_to5_completion_review.md`.
