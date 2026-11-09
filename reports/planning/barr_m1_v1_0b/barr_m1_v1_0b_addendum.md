# BARR-M1 v1.0b — Addendum: Numerical and Contrast-Authority Reconciliation

**Revision ID:** `RA_MEDFILM_BARR_BARR_M1_V1_0B__NUMERICAL_AND_CONTRAST_AUTHORITY_RECONCILIATION`
**Mode:** STRICT READ-ONLY SCIENTIFIC AUDIT — no training, no inference, no new contrast.
**Relationship to v1.0a:** additive. All v1.0a artifacts are preserved byte-for-byte. Nothing is
rewritten; the corrections below supersede v1.0a wording **going forward only**.

---

## 1. Harm-rate correction (Task A) — the 32.37% figure is CONDITIONAL

The v1.0a record stated *"harm rate 42.67% → 32.37%"*. **That comparison is invalid**: it switches
denominators between the two arms.

The frozen field `harmful_activation_share` is defined as `n_harmful_routed / n_routed` — verified
for every arm in `phase28_table_02_arm_primary_metrics.csv`.

| Arm | Numerator | Denominator | Rate | Denominator meaning |
|---|---|---|---|---|
| A1 | 2115 | **4957** | 42.6670 % | all cases (A1 executes every case) |
| A7 | 412 | **1239** | 33.2526 % | conditional on selection |
| A8 | 390 | **1205** | **32.3651 %** | **conditional on acceptance** |

**All-population A8:** 390 / 4957 = **7.8677 %**. This is the only figure comparable to A1's
42.6670 %.

### Requested numbers

| # | Quantity | Value |
|---|---|---|
| 1 | Harmed among all 4957 (A8) | **390** |
| 2 | Harmed among selected 1239 (A7) | **412** |
| 3 | Harmed among accepted 1205 (A8) | **390** |
| 4 | Harm rate over all 4957 (A8) | **7.8677 %** |
| 5 | Harm rate conditional on selection (A7) | **33.2526 %** |
| 6 | Harm rate conditional on acceptance (A8) | **32.3651 %** |
| 7 | Strict vs tolerance | A1 2115 → 2107 (8 near-zero negatives, all outside the selected and accepted sets); A7 and A8 unchanged |
| 8 | Accepted / zero-delta consistency | 1205 accepted; 3752 skipped-or-rejected; **all** non-accepted deltas exactly 0.0 |

**Upper-bound check PASSES:** 390 ≤ 1205, and 7.8677 % ≤ 24.31 %.

### Corrected statements (use these, not the v1.0a wording)

- **Unconditional:** 42.6670 % (2115/4957) → **7.8677 %** (390/4957).
- **Conditional on execution:** 42.6670 % (2115/4957) → 33.2526 % (412/1239) → **32.3651 %**
  (390/1205).

The unconditional gap mixes **selection** with the structural fact that an unexecuted case cannot
be harmed. Only the conditional chain separates selection (42.67 → 33.25 among executed) from
safety (33.25 → 32.37). Neither may be substituted for the other.

---

## 2. A7 vs A8 contrast authority (Task B)

A7 and A8 differ in **exactly one** field — `S_omega` — with identical population (DEV 4957),
budget (0.25, K = 1239), membership, ROI source, router and fusion rule. Only `n_executed` changes
(1239 → 1205).

**This is the only pre-registered single-component isolation in the frozen design**
(`phase28_core_contrast_map.json`, `frozen_matched_contrasts = ["A7_vs_A8"]`).

Frozen paired result: mean difference **+1.5717229e-05**, 95 % CI
**[−1.4313785e-05, +5.1010811e-05]** — **crosses zero**.

Paired per-case data exist and the aggregates reproduce exactly with **zero inference**, so a
descriptive harm decomposition is fully computable. It is **not computed here**.

**Recommendation:** authorise a **separate** study (`BARR-M2`, provisional) for A7-vs-A8.
**Do not extend BARR-M1 to A7** — that would silently change the study's claim class.

**Terminology:** this is **segmentation-harm mitigation**, never **clinical safety**.

---

## 3. Phase-28 chronology (Task C) — version/scope difference, not an authorization discrepancy

`execution: "NONE"` is a field on **pre-execution governance artifacts**; it asserts that *the
artifact* performs no execution. It is **not** a global claim that Phase-28 never ran.

| Time (local) | Stage | Evidence |
|---|---|---|
| 18:21–18:23 | SPEC v1.0 | contract `governance_only: true`, `execution: "NONE"` |
| 18:29–18:31 | **BLOCKED** | `PHASE28_BLOCKED__R1_R2_R3_F1_EXECUTION_SEMANTICS_INCOMPLETE` |
| 18:30 | SPEC v1.1 | contract repaired; v1.0 preserved |
| 18:45–18:46 | SPEC v1.2 | supervisor operationalisation ruling; v1.2 entry gate |
| 19:01 | **EXECUTION BINDING** | 17-artifact zero-drift binding; entry gate `gate_pass = true`, all counters 0 |
| 19:50–19:56 | EXECUTION | statistics |
| 19:59 | FREEZE | 18-run registry, 13 arms, 10 tables, 8 figures |

**Execution is established from artifacts, not tables:** **18 `best.pt` files** exist under
`checkpoints/phase28_*` (R1 ×5, R2 ×5, R3 ×5, F1 ×3), matching the 18-row registry whose CSV SHA
(`cf8d841a…`) equals the declared `registry_sha256`.

**Historical execution class: `EXECUTED_AND_FROZEN`.**

**Disclosed defects:** (C-D1) `phase28_execution_entry_gate.json` has `generated_utc = null`;
(C-D2) `execution: "NONE"` is an ambiguous field name that caused the apparent contradiction.

**Authorization chain:** no single signed authorization artifact was found. Authorization is
**implicit** via the supervisor operationalisation ruling + the `…EXECUTION_ELIGIBLE_NOT_STARTED`
terminal + a passing entry gate. Recorded as a governance observation, **not** a blocker.

**A0/A1/A8 were not trained in Phase-28.** The 18 runs belong to R1/R2/R3 and F1. A0 and A1 are
`ENDPOINT_BY_CONSTRUCTION`; A8 is `PRIOR_CANONICAL_EVIDENCE_EXACT`.

---

## 4. Reproduction semantics (Task D)

**Alignment:** 4957 rows in each of the label, safety, membership and DEV-metadata files; unique
`sample_id`; identical ID sets; `feature_row_index` contiguous 0…4956; membership order identical
to label order. **Row alignment verified.**

**Identities:** A0 `delta ≡ 0`; A1 `delta = delta_dice` (all rows); A7 `delta = delta_dice` on the
C8 membership; A8 `delta = delta_dice` on membership ∩ `p_accept_oof ≥ 0.50`. All four reproduce the
frozen aggregates within 1e-9.

**OOF vs full refit:**

| Component | Array used | Cross-fitted? | Status |
|---|---|---|---|
| **G** | `oof_global_crop_prob.npy` (from Phase-25A `prob512.npy`) | **No** | **IN_SAMPLE** — G trained on TRAIN ⊃ DEV; the `oof_` prefix refers to the refined companion |
| **R_psi** | `oof_refined_crop_prob.npy` (Phase-25C fold-specific) | **Yes** | OUT_OF_FOLD — outer∩fit = 0, outer∩early_stop = 0, 4957/4957 in exactly one outer target |
| **B_phi** | C8 membership `routing_score` | **Yes** | **OOF scores** — membership score ≠ `delta_hat_final_dev` (max diff 0.0359) and equals top-1239 by its own score |
| **S_omega** | `p_accept_oof` | **Yes** | **OOF decisions** — A8 reproduces exactly from this column |

**Used during training:** B_phi targets = Phase-25C OOF `delta_dice`; B_phi features = Phase-25B
202-D from G; S_omega targets = OOF gain > 0; S_omega features = 20-D from OOF refined/global crop
probabilities.

**Classification retained: `IN_SAMPLE_DEVELOPMENT`** at population level. Component-level
refinement: G in-sample; R_psi/B_phi/S_omega cross-fitted. No generalisation claim is available.

**Synthetic negative controls (n=200, seed 42): 6/6 detected** — shuffled order, missing case,
duplicate case, wrong membership, sign corruption, non-zero delta outside the executed set.

---

## 5. Disposition

- **BARR-M1 remains a descriptive A0/A1/A8 policy comparison.** It is **not** a router causal
  ablation and is **not** extended to A7.
- All original evidence and unfavourable results are retained. Nothing is deleted or rewritten.
- The frozen 13-arm contract is **not altered**.
- **Approval remains explicitly NOT APPROVED.**

### Supervisor decision recommendation

1. **Approve BARR-M1 v1.0b** as a descriptive A0/A1/A8 `POLICY_COMPARISON` re-analysis on
   `ROUTER_DEVELOPMENT`, `RE_ANALYSIS_ONLY`, zero inference, with the **conditional/unconditional
   harm rates reported side by side** and the in-sample limitation in every caption.
2. **Note** the Phase-28 chronology as reconciled (`EXECUTED_AND_FROZEN`, implicit authorization).
3. **Separately consider** `BARR-M2` for the pre-registered A7-vs-A8 single-component isolation.
4. **Do not** authorise clinical-safety language, held-out claims, superiority claims or any
   confirmatory inference.

---

**Status:** `BARR_M1_V1_0B_NUMERICS_AND_CONTRAST_AUTHORITY_RECONCILED__AWAITING_SUPERVISOR_APPROVAL`
**Approval block:** `[ ] APPROVED   [x] NOT APPROVED`
