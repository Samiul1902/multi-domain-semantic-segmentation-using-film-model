# WO-BARR-M1 — Benefit-Router Policy Decomposition, Phase 1
## Additive Revision v1.0a — Scientific Design Reconciliation

**Revision ID:** `RA_MEDFILM_BARR_BARR_M1_V1_0A__SCIENTIFIC_DESIGN_RECONCILIATION`
**Supersedes (for planning only):** `WO-BARR-M1` v1.0 as proposed in
`reports/planning/reauthorization_gate_v1_0/task_d_next_scientific_work_order_v1_0.md`
**Mode:** PLANNING CORRECTION ONLY — nothing is authorised, built, or executed.
**Preserved:** all v1.0 / v1.1 / v1.2 artifacts, unchanged and unrewritten.

---

## 0. What changed from v1.0, and why

| # | v1.0 as proposed | v1.0a correction | Basis |
|---|---|---|---|
| C1 | "Benefit-router mechanism ablation" / router isolation | **POLICY_COMPARISON** — the router effect is **not identifiable** from A0/A1/A8 | A8 vs A1 changes 4 factors at once (router, resource cost, safety, budget) |
| C2 | "A1 = the counterfactual that Phase-22 shows is net harmful" | **Withdrawn.** Phase-22 harm is VAL808 + ORACLE GT ROI (net −34.32). Frozen A1 on ROUTER_DEVELOPMENT is net **+8.219**. Opposite sign, different population, different ROI source | `phase22_harm_analysis.json`; `phase28_table_02_arm_primary_metrics.csv` |
| C3 | "Primary: ROUTER_DEVELOPMENT; secondary: VAL808" with no independence statement | **Declared:** DEV is the **training population** of B_phi and S_omega and a subset of TRAIN for G/R_psi → **IN_SAMPLE**. VAL808 is out-of-sample but **consumed** | DEV ∩ TRAIN = 4957/4957; DEV ∩ VAL808 = 0 |
| C4 | "2–6 GPU-hours inference" | **Zero model inference required.** A0/A1/A7/A8 reproduce **exactly** from frozen per-case arrays; CPU minutes | Reproduction check: all 9 aggregate checks pass at 1e-9 |
| C5 | No reproduction gate | **Exact frozen-aggregate reproduction gate added** as the primary positive control | Same |
| C6 | Patient clustering assumed available | **Only KUB has patient IDs** (267). ISIC/BUSI/KVASIR are `NOT_AVAILABLE` | `manifests/phase4_v3/train.csv` |
| C7 | Three-seed spread implied as context for variability | **Clarified:** SD 0.000590 = 3 independently retrained **downstream** stacks on a **fixed G**, not inference noise and not full-system replication | `phase29_cross_seed_dependency_isolation.json` |

---

## 1. Objective (restated)

On the frozen Phase-28 primary population, with one frozen fusion rule and one frozen bundle,
**describe** how three complete segmentation policies differ in macro-domain Dice and in
harmful-refinement behaviour, and **decompose** the total difference into
refinement-everywhere (A1−A0) and routed/safety-gated (A8−A1) components.

**Not** an attempt to isolate a causal router effect. **Not** a superiority test.

---

## 2. Arms — exactly three, from the frozen contract, no new arms

| Arm | Frozen definition | Role in this study |
|---|---|---|
| **A0** | `ROUTING_ABSENT (global only)` | endpoint reference / compute floor |
| **A1** | `ROUTING_ABSENT (refine all)` | refinement-everywhere counterfactual |
| **A8** | `A7 + post-safety S_omega` (canonical baseline, budget 0.25) | routed + safety-gated policy |

**No arm outside A0/A1/A8 may be executed. No new factor may be added.**

### 2.1 Field-by-field identity (see `barr_m1_arm_identity_audit_v1_0a.json`)

| Field | A0 | A1 | A8 |
|---|---|---|---|
| Benefit router | ABSENT | ABSENT | **PRESENT** (`8a412b2f…`) |
| Post-safety `S_omega` | ABSENT / unreachable | ABSENT | **PRESENT** (`eee9b97b…`) |
| Refiner execution | never (0/4957) | always (4957/4957) | conditional (1239 → 1205) |
| ROI source | none | GT-free predicted (0.30) | GT-free predicted (0.30) |
| Fusion | final = global | outside `p_global`, inside `p_refined`, thr 0.50 | identical to A1 |
| Thresholds | 0.50 | 0.30 + 0.50 | 0.30 + 0.50 + safety 0.50 |
| Population | DEV 4957 | DEV 4957 | DEV 4957 |
| Budget | 0 (degenerate) | 1.00 (full) | 0.25 (K = 1239) |
| GT at inference | none | none | none |

**Four fields differ between A8 and A1.** The router is therefore confounded with the resource
term, the safety selector and the budget. Verdict: **`POLICY_COMPARISON`**.

> The only frozen contrast that isolates a single component is **A7 vs A8** (S_omega alone), and
> it is **out of scope** for this study.

---

## 3. Population — declared roles

**Primary: `ROUTER_DEVELOPMENT` n = 4957** (preserves the contract's `held_constant`).
**Secondary: `VAL808` n = 808** — a **separate prospective descriptive proposal** that requires
its own approval; it is **not** part of the Phase-28 contract and must **not** be pooled.

### 3.1 Independence (mandatory disclosure)

| Population | Relation to component training | Class |
|---|---|---|
| ROUTER_DEVELOPMENT (4957) | ⊂ TRAIN (4957/4957); **is** the training population of B_phi and S_omega (5-fold CV + all-DEV final refit) | **`IN_SAMPLE_DEVELOPMENT`** |
| VAL808 (808) | disjoint from TRAIN; out-of-sample for all four; **already consumed** by Phase27 and Phase29 | `OUT_OF_SAMPLE_CONSUMED_DEVELOPMENT` |
| ROUTER_HOLDOUT (875) | consumed by Phase30 | `OPENED_AND_FROZEN` — not accessible |
| TEST (1683) | never read | `LOCKED_UNTIL_PHASE39` — not accessible |

**No pristine independent population remains.** Every BARR-M1 number is a descriptive
decomposition on a population that participated in selection. This is the central limitation and
must appear in every table caption.

### 3.2 Clustering

`patient_id` is real only for **KUB (267 patients)**; ISIC, BUSI and KVASIR carry
`NOT_AVAILABLE`. `case_id` is `NOT_AVAILABLE` in every domain. Therefore the bootstrap is
**domain-stratified**, patient-clustered **inside KUB only**, and per-case elsewhere — a declared
limitation, not a silent assumption.

---

## 4. Endpoints

### 4.1 Paired contrasts (identical eligible cases)

`A8 − A0`, `A8 − A1`, `A1 − A0`, on the same 4957 cases. A case that is skipped or safety-rejected
contributes a Dice delta of **exactly 0.0** (final = global). The denominator is **all 4957** —
this reproduces the frozen Phase-28 convention (A8 mean `0.001827009064` = `9.0564839294 / 4957`).

### 4.2 Dice

Per-case binary Dice at output threshold 0.50, ε = 1e-7.
**Macro-domain Dice** = `(1/4) · Σ_domains mean_cases_in_domain(dice)` — equal domain weight.
**Macro-domain delta** uses the same weighting on per-case deltas.
**Cumulative (summed) Dice differences must never be reported as macro-domain Dice.**

### 4.3 Harm

Frozen definition (Phase-22, verbatim): *a case is harmed when applying the regional arm reduces
Dice.* Operationalised as `delta < −HARM_TOL` with **`HARM_TOL = 1e-9`**. Both the strict
`delta < 0` count and the tolerance-applied count are reported.

### 4.4 Quantities that must stay separate

| Quantity | Definition |
|---|---|
| Harm rate | `n_harmed / 4957` per arm (vs A0) |
| Harm magnitude | mean / median / worst / p05 / total of negative deltas only |
| Net Dice gain | `Σ delta` over 4957 — **cumulative**, not macro |
| Macro-domain gain | equal-domain macro delta |
| Refiner execution rate | `n_executed / 4957` |
| Accepted refinement rate | `n_accepted / n_executed` |
| Safety rejection rate | `1 − accepted rate` (A8 only) |

### 4.5 Statistics (frozen before launch)

Paired bootstrap with **common resampled indices per contrast**; **2000** resamples; **seed 42**;
95 % percentile CI; domain-stratified with KUB patient clustering. Any missing case, NaN or
duplicate `sample_id` ⇒ **ABORT** (no imputation, no silent drop). Multiplicity:
`DESCRIPTIVE_NO_POST_HOC_CORRECTION`. **No confirmatory inference.**

### 4.6 Historical numbers

Phase-22 and Phase-29 numbers are **historical motivation only** and may **not** be compared
directly to new A0/A1/A8 results (different population, different ROI source, opposite sign).

---

## 5. Execution mode — corrected

**`RE_ANALYSIS_ONLY` (zero model inference).**

Verified this session: A0, A1, A7 and A8 reproduce **exactly** (9/9 aggregate checks, tolerance
1e-9) from three frozen per-case artifacts — the Phase-25C OOF gain labels, the Phase-25E C8
membership at λ0.25/budget0.25, and the Phase-25F OOF safety predictions.

Consequences:
- **No GPU allocation.** Expected wall time: CPU minutes.
- **No checkpoint deserialisation, no forward pass, no autograd.**
- The frozen aggregates become an **exact reproduction gate** (R3/R8 positive control).
- If the supervisor nonetheless requires a fresh inference pass, that is a **separate,
  materially more expensive** authorisation and must be requested explicitly.

---

## 6. Prelaunch gate (R1–R10, inference-specialised)

| # | Requirement | Inference specialisation |
|---|---|---|
| R1 | Authorisation | scope enumerates arms, population, `RE_ANALYSIS_ONLY`, exclusions |
| R2 | Frozen protocol + population | component SHAs + frozen ROI/fusion/threshold values + membership SHA + row-identity equality |
| R3 | Direct authority edge | compare **values** (0.30/1.50/256/0.50/0.50/0.25/1239/0.25/2000/42) **and** reproduce frozen aggregates |
| R4 | Harness SHA | unchanged, mandatory, per-run |
| R5 | Parameter counts | **N/A for training**; assert **0** models constructed, or verify state-dict numel if any load occurs |
| R6 | Seed policy | **N/A for training**; inference deterministic; bootstrap seed 42 fixed; three-seed spread **not** used as uncertainty |
| R7 | Checkpoint/epoch log | **N/A**; substitute per-case persistence + write-once + idempotent resume manifest |
| R8 | Positive/negative controls | + corrupt SHA, swapped membership, dropped/duplicated case, wrong K, shuffled order, wrong population |
| R9 | Claim boundary | `DESCRIPTIVE_DEV`; `IN_SAMPLE_FOR_ROUTER_AND_SAFETY = true` |
| R10 | No TEST/HOLDOUT | unchanged, plus enumerated file-access statements |

---

## 7. Claim boundary (pre-declared)

**Permitted**

> "Under the frozen fusion rule on a governed development population that also participated in
> component selection, the three frozen policies A0/A1/A8 differed in macro-domain Dice by X, and
> the harmed-case rate moved from Y (refine-all) to Z (routed + safety-gated)."

**Prohibited**

- an isolated causal router effect;
- clinical safety, clinical readiness or clinical approval;
- held-out or generalisation claims;
- superiority of BARR over any alternative;
- confirmatory or significance claims;
- any use of the three-seed spread as BARR-M1 uncertainty.

---

## 8. Prerequisites

| # | Prerequisite | Status |
|---|---|---|
| 1 | Four frozen components present with matching digests | **MET** |
| 2 | Frozen Phase-28 contract intact | **MET** |
| 3 | Population roles declared | **MET by this revision** (requires approval) |
| 4 | Authorization to execute a contract declared `execution: "NONE"` | **NOT MET** |
| 5 | R1–R10 inference gate built and green | **NOT MET** |
| 6 | Negative-control battery demonstrated failing | **NOT MET** |
| 7 | Claim-boundary block frozen pre-launch | **NOT MET** |
| 8 | Host remediation P1–P3 | **NOT REQUIRED** (no GPU, no long run) |

---

## 9. Approval block — **UNAPPROVED**

```
AUTHORIZATION REQUEST — BARR-M1 (v1.0a)

Study identifier      : BARR-M1 (provisional; not an EXT- study)
Classification        : POLICY_COMPARISON (NOT router causal ablation)
Execution mode        : RE_ANALYSIS_ONLY — zero model inference, zero GPU
Arms                  : A0, A1, A8 ONLY
Population (primary)  : ROUTER_DEVELOPMENT n=4957  [ ] approve   [ ] substitute: ________
Population (secondary): VAL808 n=808 — SEPARATE descriptive proposal  [ ] approve  [ ] drop
Independence          : primary is IN_SAMPLE for B_phi/S_omega (disclosed)  [ ] acknowledged
Fusion rule           : frozen (0.30 / 1.50 / 256; outside p_global, inside p_refined; 0.50)
Bootstrap             : 2000 resamples, seed 42, paired, domain-stratified
Harm tolerance        : 1e-9 (declared)
Claim class           : DESCRIPTIVE_DEV only

EXPLICITLY NOT AUTHORISED
  any Phase-28 arm outside A0/A1/A8 · any new factor · C2b / S_omega-absent arm ·
  C1 FiLM-off control · C3 / EXT-03B · EXT-04 · TEST · ROUTER_HOLDOUT ·
  external inference · training of any kind · any fresh GPU inference pass
  (unless separately requested and approved)

AUTHORIZED BY : ______________________   DATE : ____________
AUTHORIZATION ID : ____________________   [ ] APPROVED   [x] NOT APPROVED
```

---

## 10. Final status

`BARR_M1_SCIENTIFIC_DESIGN_RECONCILED__AWAITING_AUTHORIZATION`

Reproduction gate: PASS (9/9 exact).
