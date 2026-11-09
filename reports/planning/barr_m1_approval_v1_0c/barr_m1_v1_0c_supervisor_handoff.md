# BARR-M1 v1.0c — Supervisor Handoff Reference

**Revision:** `RA_MEDFILM_BARR_BARR_M1_V1_0C__FINAL_APPROVAL_PACKAGE`
**Status:** `BARR_M1_APPROVAL_PACKET_SCIENTIFIC_WORDING_CORRECTED__AWAITING_SUPERVISOR_DECISION`
**Approval:** **NOT APPROVED**

---

## How to read this package

The approval packet consists of **two authoritative documents** that must be read **together**:

1. **`barr_m1_v1_0c_supervisor_authorization_request.md`** — the original approval request (preserved byte-for-byte)
2. **`barr_m1_v1_0c_erratum.md`** — additive scientific-wording corrections to two passages

The erratum does **not** rewrite the original. It supersedes two specific passages going forward only.

| Passage | Location | Issue |
|---|---|---|
| Erratum 1 | Section 4, Limitation 6 | Incorrectly stated no `S_omega`-absent arm exists and no safety metric exists. |
| Erratum 2 | Section 1, Research question | Incorrectly implied causal attribution of differences to router vs safety. |

---

## Erratum artifacts (verified)

| File | SHA-256 | Status |
|---|---|---|
| `barr_m1_v1_0c_erratum.md` | `7653cefd5b1bf6a1e28e5c9f65e1850a561f7316d48226dfb0859195c1c38f45` | **VERIFIED** |
| `barr_m1_v1_0c_erratum_sha256.json` | `22f0abd376806de3e1fa340050840992621561a4fd8d25928ccfa602679d7f12` | **VERIFIED** |
| `barr_m1_v1_0c_supervisor_authorization_request.md` | `a1a59cffc83e7b167b6ae28f75123167abf06d37d080e09c3cc0cdf519419a42` | **PRESERVED** |

---

## What is being requested

A **descriptive policy comparison** of three complete frozen segmentation policies (A0, A1, A8) on the frozen `ROUTER_DEVELOPMENT` population (n=4957), by **CPU-only reanalysis** of preserved arrays.

**What BARR-M1 is NOT:**
- Not a router causal ablation
- Not a component-isolation study
- Not a clinical-safety claim
- Not a held-out or confirmatory study
- Not an authorization for A7-vs-A8 analysis (that is BARR-M2, separate)

---

## Execution readiness

The execution harness (`scripts/analysis/barr_m1_reanalysis_execute_v1_0d.py`) is prepared but **will refuse to run** until a valid authorization artifact is supplied. See the separate execution-readiness report for technical verification.

---

## Authorization block — EMPTY

```
AUTHORIZATION REQUEST — BARR-M1 (v1.0c + erratum)

Study identifier      : BARR-M1
Classification        : DESCRIPTIVE POLICY_COMPARISON
Arms                  : A0, A1, A8 ONLY
Population            : ROUTER_DEVELOPMENT n=4957 (IN_SAMPLE_DEVELOPMENT)
Execution mode        : CPU_ONLY_RE_ANALYSIS_ONLY
Endpoint              : paired A8-A0 / A8-A1 / A1-A0; equal-domain MACRO Dice

AUTHORIZED BY : ______________________   DATE : ____________
AUTHORIZATION ID : ____________________   [ ] APPROVED   [ ] REJECTED
```

**Completion of this work order does not constitute authorization.**
