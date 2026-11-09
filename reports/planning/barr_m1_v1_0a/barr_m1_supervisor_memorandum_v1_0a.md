# Supervisor Memorandum — BARR-M1 Design Correction

**To:** Supervisor
**From:** Implementation / governance agent
**Re:** Correction of the proposed BARR-M1 study before authorization
**Revision:** `RA_MEDFILM_BARR_BARR_M1_V1_0A__SCIENTIFIC_DESIGN_RECONCILIATION`
**Status:** recommendation only — **nothing authorised, nothing executed**

---

## 1. Bottom line

The proposed BARR-M1 study is **worth running but must be re-labelled and re-scoped**.

1. It is a **policy comparison**, not a router ablation. The router effect is **not identifiable**
   from A0/A1/A8, because four factors change at once.
2. The **"refine-all is net harmful"** premise does **not** hold on the Phase-28 population. It
   holds only for the Phase-22 *oracle-ROI* setting on VAL808.
3. The primary population is the **training population** of the router and the safety selector.
   Every number is therefore a descriptive in-sample decomposition.
4. The study needs **no GPU at all** — the three arms reproduce exactly from frozen per-case
   artifacts.

## 2. The three findings that change the design

### 2.1 Router effect is confounded (A8 vs A1 differs in four fields)

| Field | A1 | A8 |
|---|---|---|
| Benefit router | absent | **present** |
| Resource cost `λ·C` | absent | **present** |
| Post-safety `S_omega` | absent | **present** |
| Budget | 1.00 (all) | **0.25 (K=1239)** |

The frozen contract pre-registers **only `A7_vs_A8`** as a matched contrast and explicitly lists
A0 and A1 as *descriptive rows with no formal pairwise reference*. A0/A1/A8 is therefore a new,
descriptive contrast.

### 2.2 The harm narrative reverses

| Setting | Population | ROI source | Net Dice gain |
|---|---|---|---|
| Phase-22 harm analysis | VAL808 | **oracle (GT)** | **−34.32** (536/808 harmed) |
| Frozen A1 | ROUTER_DEVELOPMENT | GT-free predicted | **+8.219** (2115/4957 harmed, 42.7 %) |

Refine-everywhere is **net harmful under an oracle ROI on VAL808** but **net beneficial under the
deployable predicted ROI on ROUTER_DEVELOPMENT**. The mechanism story survives in a weaker form
(the *harm rate* falls from 42.7 % to 32.4 % under routing + safety), but the "refine-all is net
harmful" sentence must not be carried into the paper for this population.

### 2.3 The primary population is in-sample

- `ROUTER_DEVELOPMENT` (4957) ⊂ `TRAIN` (4957/4957) and is **disjoint** from VAL808.
- `B_phi` and `S_omega` were trained on exactly these 4957 rows (5-fold CV **plus an all-DEV
  final refit**).
- `G` and `R_psi` were trained on TRAIN, which contains DEV.

So a routed-vs-unrouted gap measured here is **optimistic by construction**. VAL808 is
out-of-sample but already consumed by Phase27 and Phase29. ROUTER_HOLDOUT is frozen; TEST is
locked. **No pristine population remains.**

## 3. Cost correction

| | v1.0 estimate | v1.0a finding |
|---|---|---|
| Compute | 2–6 GPU-hours | **CPU minutes, 0 GPU** |
| Basis | 3 arms × 4957 forward passes | exact reproduction from frozen arrays |

Verified: A0, A1, A7 and A8 reproduce the frozen Phase-28 aggregates **exactly** (9/9 checks at
tolerance 1e-9) with **zero** model constructions, deserialisations, forwards or autograd calls.

This also gives the study a built-in **positive control**: if the re-analysis does not reproduce
the frozen aggregates, the harness is wrong and the run must abort.

## 4. What the three-seed number actually is

Seeds 42/123/3407 are **three independently retrained downstream stacks** (`R_psi → B_phi →
S_omega`) evaluated against **one fixed global model G (seed 42)**. The global Dice is identical
across seeds to 1.4e-16.

**SD 0.000590** is therefore the sample SD (ddof = 1, n = 3, 2 df) of the macro-domain mean Dice
delta attributable to **downstream-stack retraining randomness**. It is **not** inference noise,
**not** sampling error, and **not** replication of the full system. It must not be used as a
BARR-M1 uncertainty estimate.

## 5. Recommended claim boundary

> **"Descriptive comparison of three frozen segmentation policies and their harmful-refinement
> behavior on a governed development population."**

Prohibited: isolated causal router effect · clinical safety · held-out generalisation ·
superiority · confirmatory inference.

## 6. Decision requested

Approve **BARR-M1 v1.0a** as a `POLICY_COMPARISON` re-analysis on `ROUTER_DEVELOPMENT`, with:
- arms A0/A1/A8 only;
- `RE_ANALYSIS_ONLY` execution (no GPU, no inference);
- VAL808 handled as a **separate** proposal;
- the in-sample limitation stated in every table caption;
- the R1–R10 inference gate built and green first.

Approval block: **left unapproved** — see the work-order revision §9.

## 7. Status

`BARR_M1_SCIENTIFIC_DESIGN_RECONCILED__AWAITING_AUTHORIZATION`

Reproduction gate: PASS (9/9 exact).
