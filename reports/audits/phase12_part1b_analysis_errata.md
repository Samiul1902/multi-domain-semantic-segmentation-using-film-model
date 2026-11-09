# Phase 12 Part 1B — Analysis Errata / Interpretation Corrections

**Created:** 2026-09-21T01:16:08.055448+00:00 (Phase 12 Part 1C)
**Status:** non-blocking interpretation corrections. **No accepted artifact is modified.**

Both items are **verification-helper / labelling** issues. Neither affects the primary
scientific result. The accepted Part-1B notebook and support code are left untouched.

---

## ERRATUM A — Global reproduction gate label

**What the Part-1B helper did.** The temporary EVALUATION_512 dictionary built inside the
Part-1B driver computed

```
precision = TP / (TP + FP + FN)
```

which is effectively **IoU**, not precision. That dictionary was used only as a transient
reproduction-check container; it is not persisted as a scientific metric.

**Why it is non-blocking:**

- the **physical reproduction gate** compares **Dice and IoU only**;
- the observed max absolute Dice difference is **1.11e-16** (machine epsilon);
- the **native-space scientific metrics** use `native_metrics()`, which correctly computes
  `precision = TP / (TP + FP)` (and `recall = TP / (TP + FN)`);
- therefore **Part-1B raw native evidence is unaffected**.

**Canonical wording going forward:**

> `DICE_IOU_GLOBAL_REPRODUCTION_GATE_PASS`

**Do NOT** claim that EVALUATION_512 precision/recall were independently reproduced by that
gate.

---

## ERRATUM B — Legacy restore sensitivity

**What the Part-1B comparison combined.** The FLOAT-vs-legacy comparison changes **two**
things at once:

1. uint8 probability quantisation, **and**
2. the restoration engine convention — **Torch bilinear (`align_corners=False`)** for FLOAT
   vs **PIL bilinear + uint8 quantisation** for LEGACY.

**Canonical label going forward:**

> `COMBINED_LEGACY_RESTORE_SENSITIVITY`

**Do NOT** call it `PURE_UINT8_QUANTISATION_EFFECT`, and do NOT claim uint8 alone was
isolated. A clean decomposition would require rerunning restoration with a single engine —
which is **not authorised in Part 1C** and is not required, because the sensitivity is
secondary and the primary `ORACLE_FLOAT_GLOBAL_RETAINED` result is unaffected.

**Gate usage:** this sensitivity **MUST NOT** be used in the regional-integration gate.

---

## Summary

| Erratum | Class | Affects primary result? | Action |
|---|---|---|---|
| A | verification-helper label | **No** | use `DICE_IOU_GLOBAL_REPRODUCTION_GATE_PASS` |
| B | combined-confound label | **No** | use `COMBINED_LEGACY_RESTORE_SENSITIVITY` |

## Immutability

- Part-1A notebook: `c226ea0f28b93b9cafdc08e9720aec320f6080f8302369e51e201e1515867b05`
- Part-1B notebook: `5848728526885a7186c5c32ab4e5b7cc9d4b7eaedc1a26994799afe81d27fef0`
- Part-1B support code: `13370300003050eb552c88654aa08c46c8413fe99f9c9ea5d3dba0dc011a29de`

All three are **unchanged** by this errata.
