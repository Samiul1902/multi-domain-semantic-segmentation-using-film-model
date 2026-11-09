# BARR-M1 v1.0c — Final Reporting Precision Clarification

**Revision:** `RA_MEDFILM_BARR_BARR_M1_V1_0C__FINAL_APPROVAL_PACKAGE`
**Mode:** reporting precision only. **No measured value is changed.**
**Relationship:** additive to v1.0a and v1.0b. Both are preserved byte-for-byte.

---

## 1. A1 harm rate — strict versus tolerance-adjusted

| Variant | Numerator | Denominator | Rate |
|---|---|---|---|
| **Strict** (`delta < 0`) | **2115** | 4957 | **42.6670 %** |
| **Tolerance-adjusted** (`delta < −1e-9`) | **2107** | 4957 | **42.5055 %** |

The 8-case difference sits in `−1e-9 ≤ delta < 0` — floating-point-scale negatives, not
scientifically meaningful harm. **Report both**, and declare which is primary in the caption.
Neither replaces the other.

## 2. A7 and A8 harm, all-population

| Arm | Harmed | Denominator | Rate |
|---|---|---|---|
| A7 | **412** | 4957 | **8.3115 %** |
| A8 | **390** | 4957 | **7.8677 %** |

Both use the **full 4957** denominator, so both are directly comparable to A1's 2115/4957.
Neither is a conditional rate.

## 3. A8 selection, acceptance, rejection

| Quantity | Value | Fraction of 4957 | Fraction of selected |
|---|---|---|---|
| Selected | **1239** | 25.000 % | 100 % |
| Accepted | **1205** | 24.309 % | 97.256 % |
| Rejected | **34** | 0.686 % | 2.744 % |

`selected = accepted + rejected` → 1239 = 1205 + 34.

## 4. Candidate refinement execution ≠ post-safety acceptance

- **Execution** — `R_psi` actually ran on the case. Determined **only** by router membership.
- **Acceptance** — `S_omega` allowed the refined mask to **replace** the global mask. Evaluated
  **only** where execution occurred.

**A7** executes 1239 and accepts all 1239 (no safety stage).
**A8** executes the **same 1239** and accepts **1205**, rejecting **34**.

A case can therefore be **executed and then rejected**; its delta is then exactly **0.0** — it is
neither helped nor harmed. It is **not** a harm and must never be counted as one. `n_executed`
and `n_accepted` are different quantities and must never be interchanged as denominators.

## 5. Pooled average versus equal-domain macro average

| Statistic | Definition | Domain weighting |
|---|---|---|
| **Pooled** | `sum(delta) / n_executed` | proportional to case count |
| **Macro** | `(1/4) · Σ_domain mean_in_domain(delta)` | **equal** across the 4 domains |

DEV is unbalanced — ISIC 2173, KUB 1680, KVASIR 592, BUSI 512 — so the two statistics differ.

The frozen Phase-28 arm table reports **pooled** values in `mean_true_delta_dice_routed`:
A1 `0.001658079789`, A7 `0.007246629237`, A8 `0.007515754298`.
BARR-M1 declares an **equal-domain macro** endpoint. **These are different statistics.**

**Consequence for the gate:** the positive control compares **sums and counts** (definition-free),
never a pooled mean against a macro mean. Every reported mean must be labelled `POOLED` or `MACRO`.

## 6. The keyed `sample_id` join

The Phase-25C label file and the Phase-25E membership file are in **different row orders** —
**4955 of 4957 positions differ** — although the ID **sets** are identical.

A positional `zip` would silently mis-assign the selection flag to almost every case and would
still appear to run. **The join must be keyed on `sample_id` with one-to-one validation.**
Gate check `R2` asserts that positional equality is **false** and that the keyed join is
one-to-one with zero missing selections.

---

**No measured value in this document differs from v1.0a / v1.0b.** This document only adds
denominators, labels and join semantics.
