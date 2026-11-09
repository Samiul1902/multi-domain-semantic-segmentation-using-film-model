# ReMedFiLM FULL — VAL808 Result Reconciliation

**Question.** Two macro Dice values are in circulation for the FULL system on
VAL808: **0.837290** and **0.837862**. Are they different valid configurations,
or one reporting error?

**Answer: a reporting inconsistency.** `0.837862` is reproducible from no saved
artifact and from no routing policy that the saved masks can express. The
canonical value is **0.837290**.

---

## 1. Method

The 808 saved Phase 27 masks (backbone `*_global.png`, FULL `*_final.png`) and the
evaluation ground truth stored in the Phase 21 prediction archives were re-scored
from scratch. A policy is defined as: *use the FULL mask for cases the policy
selects and the safety gate accepts, otherwise use the backbone mask.*

The saved masks already encode the canonical policy, and for all 529 SKIP
cases the FULL mask is byte-identical to the backbone mask
(529/529), so any policy is exactly expressible.

The frozen runtime router threshold is
`tau_C8 = -0.024358327623641256` (`docs/phase29_repro_spec.md`).

---

## 2. Policies tested

| Policy | Selected | Accepted | Macro Dice | Reproduces 0.837862? |
|---|---|---|---|---|
| canonical Phase 27 (tau_C8, safety-gated) | 279 | 266 | 0.837290 | no |
| top-181 by router utility, safety-gated | 181 | 177 | 0.837022 | no |
| top-183 by router utility, safety-gated | 183 | 179 | 0.837026 | no |
| top-185 by router utility, safety-gated | 185 | 180 | 0.837029 | no |
| top-200 by router utility, safety-gated | 200 | 195 | 0.837214 | no |
| top-250 by router utility, safety-gated | 250 | 241 | 0.837344 | no |
| top-279 by router utility, safety-gated | 279 | 266 | 0.837290 | no |
| tau_C8 without safety gate (A7-equivalent) | 279 | 279 | 0.837290 | no |

No policy reproduces `0.837862`. The closest is the canonical policy itself.

---

## 3. The three recorded values

### 0.837290 — **canonical, reproducible**

| Field | Value |
|---|---|
| Experiment | Phase 27 preservation (seed 42) |
| Checkpoints | G `286689fd…`, R `6d28608a…`, B `8a412b2f…`, S `eee9b97b…` |
| Seed | 42 |
| Router policy | `tau_C8 = -0.024358` → **279 selected** |
| Safety configuration | accepted **266**, rejected **13**, skipped **529** |
| Split | VAL808, n = 808 |
| Metric | macro-domain equal-weight mean per-image Dice, threshold 0.5 |
| Artifacts | `phase27_preservation_result.json`, `phase29_phase_d_val808_per_seed_continuity.json` |
| Independent check | re-scoring the masks gives 0.837290 (Δ = 1.8e-07) |

### 0.837862 — **not reproducible; no frozen artifact**

| Field | Value |
|---|---|
| Appears in | `build_v5/v6/v7_pdf_report.py`, `PROGRESSION_AND_PROPAGATION_EVIDENCE.csv` |
| Appears in a frozen artifact? | **No** — zero hits across `reports/`, `experiments/`, `checkpoints/` |
| Implied routed / accepted | 183 / 165 (V7 table) — contradicts tau_C8's 279 / 266 |
| Internal arithmetic | It is the mean of three hardcoded numbers (0.837862, 0.837910, 0.837815) |
| Label defect | The V7 table prints `0.837862` **both** as the seed-42 row **and** as the three-seed mean |

The V7 table is internally inconsistent: seed 42 and the mean cannot both be
0.837862 while the other two seeds are 0.837910 and 0.837815 (their mean is
0.837862, so the seed-42 cell was overwritten with the mean).

### 0.8373512 — **recorded but not reproducible**

`phase29_val808_seedwise_metrics.json` reports 0.8373512 with **268** accepted
cases. The saved mask set encodes the **266**-accepted state. The two states differ
by two safety decisions whose refined outputs were not persisted separately, so
this variant cannot be re-derived. It is a genuine recorded variant, not an error —
but it is not the canonical number.

---

## 4. Which value should be reported

| Context | Value |
|---|---|
| Paper / headline VAL808 macro Dice, seed 42 | **0.837290** |
| Net gain over backbone | **+0.2210 pp** |
| Three-seed mean (descriptive) | 0.837901 |
| Superseded / incorrect | 0.837862 (and the +0.28 pp derived from it) |

The larger number is **not** selected. `0.837862` is rejected because it has no
artifact, no policy, and no consistent sample accounting behind it.

---

## 5. Consequence for the compute figure

Because `0.837862` was paired with `34.72 GMACs` (the always-refine cost), the
accuracy–compute point previously plotted for ReMedFiLM was wrong on both axes.
The corrected point is **32.4379 expected conditional GMACs at 0.837290**.
