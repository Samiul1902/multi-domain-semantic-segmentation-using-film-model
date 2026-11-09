# BARR-M1 v1.0c — Additive Scientific-Wording Erratum

**Revision:** `RA_MEDFILM_BARR_BARR_M1_V1_0C__FINAL_APPROVAL_PACKAGE`
**Erratum ID:** `BARR_M1_V1_0C_ERRATUM_20261027`
**Mode:** additive wording correction only. **No measured value is changed.**
**Relationship:** v1.0c documents are preserved byte-for-byte. This erratum supersedes the two passages below going forward only.

---

## Corrected document

`reports/planning/barr_m1_approval_v1_0c/barr_m1_v1_0c_supervisor_authorization_request.md`
SHA-256: `a1a59cffc83e7b167b6ae28f75123167abf06d37d080e09c3cc0cdf519419a42` (preserved)

---

## Erratum 1 — Section 4, Limitation 6 (safety statement)

**Original (incorrect):**
> 6. **No safety metric exists** and there is no `S_omega`-absent arm, so the safety contribution is **not measurable within Phase-28** (C2b remains `NOT_ESTABLISHED`).

**Superseding correction:**

> 6. **Segmentation-harm and Dice measurements exist**, but **clinical safety has not been established**. The frozen design **does** contain an `S_omega`-absent comparator — **A7** (executes 1239, accepts all 1239, no post-safety filtering). **A8** includes `S_omega`. **A7 versus A8** is the pre-registered single-component matched contrast (`frozen_matched_contrasts = ["A7_vs_A8"]`). However, **BARR-M1 does not authorize A7–A8 reanalysis**; A7 remains explicitly excluded from BARR-M1 scope (Section 3). A descriptive decomposition of the `S_omega` contribution is reserved for a **separately proposed study (BARR-M2)**, which requires its own supervisor approval. C2b remains `NOT_ESTABLISHED` within BARR-M1 because BARR-M1 is a policy comparison, not a component-isolation analysis.

---

## Erratum 2 — Section 1, Research question (causal language)

**Original (incorrect):**
> **Question.** Under one frozen fusion rule, on one frozen development population, how do three complete frozen segmentation policies differ in macro-domain Dice and in harmful-refinement behaviour — and how much of the difference is attributable to refining everywhere versus to routing with a post-safety gate?

**Superseding correction:**

> **Question.** Under one frozen fusion rule, on one frozen development population, how do three complete frozen segmentation policies (A0, A1, A8) differ in macro-domain Dice and in harmful-refinement behaviour?
>
> BARR-M1 provides a **descriptive accounting** of the differences among complete policies. It **cannot attribute** those differences uniquely to the router, to the safety stage, or to the computation budget, because these factors are confounded across A0/A1/A8. (A0 uses neither router nor safety; A1 uses neither router nor safety but refines everywhere; A8 uses router, safety, and a reduced computation budget.) Isolated component attribution would require a different study design.

---

## Task 3 — Approval-readiness confirmation checklist

| # | Item | Status |
|---|---|---|
| 1 | BARR-M1 remains A0/A1/A8 only. | **CONFIRMED** |
| 2 | ROUTER_DEVELOPMENT n=4957 remains the sole primary population. | **CONFIRMED** |
| 3 | The study remains in-sample and descriptive (`DESCRIPTIVE_DEV`). | **CONFIRMED** |
| 4 | Both harm-rate denominators (all-population and conditional-on-execution) remain separately reported. | **CONFIRMED** |
| 5 | The equal-domain macro and pooled/conditional means remain distinguished. | **CONFIRMED** |
| 6 | CPU-only frozen-array reanalysis remains the only proposed execution. | **CONFIRMED** |
| 7 | No scientific authorization has been granted. | **CONFIRMED** |
| 8 | All previous artifacts (v1.0a, v1.0b, v1.0c) remain unchanged. | **CONFIRMED** |

---

## Terminal state

```
BARR_M1_APPROVAL_PACKET_SCIENTIFIC_WORDING_CORRECTED__AWAITING_SUPERVISOR_DECISION
```

**Approval block:** `[ ] APPROVED   [x] NOT APPROVED`
