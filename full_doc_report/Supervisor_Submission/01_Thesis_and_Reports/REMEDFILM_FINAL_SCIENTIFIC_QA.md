# REMEDFILM — Final Scientific QA

**Deliverable root:** `D:\Softfors\jup\full_doc_report`
**Definitive master:** `ReMedFiLM_COMPLETE_MASTER_VERIFIED.ipynb`
**SHA-256:** `237772d4ff82a23e797d0dc3379f78d2281e51b7b20508865960efc3d4a264ca`
**Date:** 2026-11-08

Acceptance verification: **38 / 38 checks passed** (`REMEDFILM_FINAL_QA_CHECKS.json`).

> **Input disclosure.** The brief referenced a corrected notebook
> `ReMedFiLM_COMPLETE_MASTER_FULL_SYSTEM_FIXED.ipynb` "if available". **It does
> not exist** anywhere in the repository (searched recursively). The VERIFIED
> master was therefore built from the source artifacts directly, not by repairing
> that file.

---

## 1. FULL component identity — verified, not asserted

Each checkpoint was **loaded read-only** and its parameter count recomputed from
the state dict. A name or a table was never accepted as proof.

| Symbol | Class | Checkpoint | Params (measured) | Expected | SHA-256 | Training |
|---|---|---|---|---|---|---|
| **G** | `GlobalMedFiLM` | `checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt` | 3,523,001 | 3,523,001 ✓ | `286689fd…` | 81 epochs, best 66, early-stopping |
| **R_psi** | `BARRRegionalRefinerV1` | `checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt` | 1,276,401 | 1,276,401 ✓ | `6d28608a…` | 25 epochs, fixed-epoch refit |
| **B_phi** | `BARRBenefitRouterV1` | `checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt` | 36,801 | 36,801 ✓ | `8a412b2f…` | 80 epochs, no selection rule |
| **S_omega** | `BARRPostSafetyV1` | `checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt` | 1,217 | 1,217 ✓ | `eee9b97b…` | 23 epochs, no selection rule |

**Measured sum: 4,837,420** = contract total ✓

Registry: `REMEDFILM_FULL_COMPONENT_REGISTRY.json`.

### Honest gaps in the training record

| Component | Best epoch | Why |
|---|---|---|
| G | **66** | recorded in `closure.json` |
| R_psi | `NOT_APPLICABLE` | final refit trains a fixed 25 epochs; no selection rule |
| B_phi | `NOT_RECORDED` | final refit log has no selection column |
| S_omega | `NOT_RECORDED` | final refit log has no selection column |

### Assembly, not joint training

`G → R_psi → B_phi → S_omega`, each fitted against a **frozen** upstream. No
optimiser ever saw all four modules. This is stated in §06 of the master and in
the registry `assembly` field.

---

## 2. Component training history

`REMEDFILM_COMPONENT_TRAINING_HISTORY.csv` — **16,679 records** across the
backbone, the three components and the F1 ablation variant.

| Component | Epoch records | Metrics logged |
|---|---|---|
| R_psi | 6,476 | 9 |
| B_phi | 4,649 | 4 |
| S_omega | 3,407 | 4 |
| GlobalMedFiLM | 1,863 | 23 (incl. per-domain Dice/IoU/precision/recall) |

A unified 81-epoch FULL curve **does not exist and was not fabricated**. The
notebook shows separate genuine component histories, and marks missing metrics
`NOT_RECORDED`.

---

## 3. Result reconciliation — 0.837290 vs 0.837862

**Verdict: `REPORTING_INCONSISTENCY`.**

Every routing policy expressible from the saved masks was tested
(`REMEDFILM_FULL_RESULT_RECONCILIATION.json`):

| Policy | Selected | Macro Dice | Reproduces 0.837862? |
|---|---|---|---|
| Canonical Phase 27 (tau_C8, safety-gated) | 279 | **0.837290** | no |
| top-181 / 183 / 185 | 181–185 | 0.83702–0.83703 | no |
| top-200 / 250 / 279 | 200–279 | 0.8371–0.8373 | no |
| tau_C8 without safety gate | 279 | 0.837290 | no |

No policy reproduces 0.837862.

**Where 0.837862 actually comes from:** `build_v5/v6/v7_pdf_report.py` hardcodes
three seed values (0.837862, 0.837910, 0.837815) whose mean is 0.837862. The V7
table prints 0.837862 **both** as the seed-42 row **and** as the three-seed mean —
arithmetically impossible unless the seed-42 cell was overwritten with the mean.
None of the three values appears in any frozen artifact, and the implied routing
counts (183/165/31) contradict tau_C8's 279/266/13.

**A third value exists:** `phase29_val808_seedwise_metrics.json` reports 0.8373512
with 268 accepted cases. That is a genuine recorded variant, but the saved masks
encode the 266-accepted state, so it cannot be re-derived.

| Context | Value |
|---|---|
| Headline VAL808 macro Dice, seed 42 | **0.837290** |
| Net gain over backbone | **+0.2210 pp** |
| Three-seed mean (descriptive) | 0.837901 |
| Superseded | 0.837862, +0.28 pp |

The larger number was **not** selected. Document: `REMEDFILM_FULL_RESULT_RECONCILIATION.md`.

---

## 4. Internal validation

`REMEDFILM_FULL_VAL808_METRICS.csv` — re-scored from the 808 saved Phase 27 masks.

| Domain | n | G Dice | FULL Dice | Δ | FULL HD95 |
|---|---|---|---|---|---|
| ISIC | 357 | 0.897189 | 0.898081 | +0.000892 | 25.31 px |
| BUSI | 84 | 0.858823 | 0.858914 | +0.000091 | 31.72 px |
| KVASIR | 87 | 0.820248 | 0.820651 | +0.000403 | 62.51 px |
| KUB | 280 | 0.764058 | 0.771512 | +0.007454 | 49.60 px |
| **MACRO** | **808** | **0.835079** | **0.837290** | **+0.002210** | **42.29 px** |

Paired macro Δ = `+0.00220997 [+0.00114769, +0.00329205]`, 10,000-replicate
domain-stratified bootstrap. Agreement with frozen Phase 27: **1.8×10⁻⁷**.

---

## 5. Segmentation evidence

`REMEDFILM_FULL_VISUAL_EVIDENCE_INDEX.csv` — **22 panels**, every one resolving to
a real source image, GT mask, backbone mask and FULL mask (0 missing files).

**Nine galleries:** worst/median/best per domain (4), an **accepted-refinement**
panel per domain (4) and a failure montage (1).

The accepted-refinement panels are the visual proof that FULL ≠ backbone: in each,
the safety gate accepted a refinement and the FULL mask visibly differs from the
GlobalMedFiLM mask, with per-sample metrics printed in the panel.

Example (KUB): G Dice 0.8100 → FULL Dice 0.8109, Δ +0.0009, IoU 0.6820, HD95 38.5 px,
branch `execute then accept`.

Every panel carries a **metrics column** — image, GT, Global, FULL, TP/FP/FN and
the numbers.

**Geometry verified across all 808 samples:** the evaluation ground truth, the
backbone mask and the FULL mask are all `512 × 512` with **zero shape
mismatches** (one shape set only). No gallery panel required resampling, so no
panel can be showing a geometrically distorted comparison.

`REPORT_NOTEBOOK_FIGURE_MAPPING.csv` maps **49 / 49** figures to notebook
section, generation function, scientific source and evidence class.

---

## 6. External evaluation

`REMEDFILM_FULL_EXTERNAL_METRICS.csv` — 36 rows, three cohorts, both arms.

| Cohort | n | Global Dice | FULL Dice | Δ | Global HD95 | FULL HD95 |
|---|---|---|---|---|---|---|
| CVC-ClinicDB | 612 | 0.686568 | 0.689747 | +0.003179 | 109.59 px | 108.49 px |
| BrEaST-Lesions-USG | 252 | 0.707822 | 0.708098 | +0.000276 | 73.98 px | 73.26 px |
| Stones-Where-Are-You | 20 | 0.080840 | 0.082126 | +0.001286 | 166.90 px (n=6) | 169.90 px (n=6) |

**Two denominators matter here.** The Stones cohort is 20 cases: **14 stone-free**
(no reference surface) and **6 stone-positive**. HD95 is therefore defined for
only `n = 6`, which is why the interval is enormous — it is not a stable estimate.

The Stones Dice of **0.081 / 0.082** is a genuine, severe domain-shift failure,
not a rounding artefact. HD95 also gets *worse* under refinement (166.90 → 169.90)
even though Dice improves marginally; both facts are reported.

Metrics present in the table: `Dice`, `IoU`, `Precision`, `Recall`, `HD95_px`,
`ASSD_px` — for both arms. Any metric undefined for a case is absent, never zero.

**Stone-free failure preserved: 14/14 in both arms** receive a foreground
prediction. The safety gate scores refinement benefit, not lesion presence, so it
cannot fix negative studies.

Retrospective only — never presented as prospective testing.

---

## 7. Ablation and progression

`REMEDFILM_ABLATION_AND_PROGRESSION.csv` — 19 rows: 13 arms + 6 stages.

All 13 arms present (A0–A8, R1–R3, F1). The **A8 vs A7** matched contrast remains
`+1.57e-05 [−1.43e-05, +5.11e-05]` — **CI includes zero**, preserved as
inconclusive. No causal attribution for S_omega is claimed.

---

## 8. Efficiency — corrected

| | GlobalMedFiLM | ReMedFiLM FULL |
|---|---|---|
| Parameters | 3,523,001 | **4,837,420** |
| Analytical GMACs | 31.5517 (lower bound) | **32.4379** (expected conditional) |
| VAL808 macro Dice | 0.835079 | **0.837290** |
| Batch-1 p50 | 15.72 ms (skip) | 18.89 ms (execute) |

ReMedFiLM FULL is plotted as **its own star marker**. The previous figure was
wrong on both axes (34.72 GMACs, 0.837862); both are corrected.

Four distinct quantities are separated: analytical GMACs (lower bound), expected
conditional, always-refine, and measured forward-only latency. Full-pipeline
latency is `NOT_RECORDED`.

---

## 9. Execution

| | |
|---|---|
| Notebooks executed | **22 / 22** |
| Code cells executed | **292 / 292** |
| Errors | **0** |
| Skipped cells | **0** |
| Kernel | `remedfilm-analysis` → `.venv\Scripts\python.exe` |

Report: `REMEDFILM_NOTEBOOK_EXECUTION_REPORT.json`.

Every notebook installs a `sys.addaudithook` plus runtime patches and runs four
negative controls that must print `blocked`, or the notebook aborts. Verified in
all 22.

---

## 10. Integrity

| Check | Result |
|---|---|
| Original notebooks modified | 0 |
| Frozen checkpoints modified | 0 |
| `git status` on `src/ tests/ manifests/ checkpoints/ configs/ reports/audits/` | **clean** |
| Training performed | **NO** |
| New inference performed | **NO** |
| TEST manifest read | **NO** (guard blocks it) |
| Original phasewise notebooks preserved | **108 / 108** byte-identical |

Checkpoint loading used `torch.load(..., map_location="cpu", weights_only=False)`
for **metadata and parameter counting only** — no forward pass, no weight mutation.

---

## 11. Missing scientific evidence (unchanged)

| Gap | Status |
|---|---|
| C1 learned vs identity FiLM | `NOT_ESTABLISHED` — 0/6 runs |
| C2 causal component attribution | `NOT_ESTABLISHED` — A8 vs A7 CI includes 0 |
| C3 8-model × 3-seed benchmark | `NOT_ESTABLISHED` — 0/24 cells |
| Prospective independent external cohort | `NOT_ESTABLISHED` |
| TEST comparative endpoint | `NOT_ESTABLISHED` — access consumed |
| BUSI / polyp subgroup labels | `NOT_RECORDED` |
| Full-pipeline latency | `NOT_RECORDED` |

`PENDING_CONTROLLED_EXPERIMENTS.md` remains the register.

---

## 12. Genuine defects found

| ID | Artifact | Defect |
|---|---|---|
| **DEFECT-01** | `phase26_component_inventory.csv` | `parameters[G]` stores **MACs** (31,551,740,928), not parameters (3,523,001). Frozen file untouched; corrected derived table used. |
| **CORR-01..04** | V5/V6/V7 report generators | 0.837862 / +0.28 pp / 34.72 GMACs have no frozen source. |
| **V7 table defect** | `build_v7_pdf_report.py` | prints the three-seed mean as the seed-42 value |

---

## 13. Files

| Path | Content |
|---|---|
| `ReMedFiLM_COMPLETE_MASTER_VERIFIED.ipynb` | definitive master, 17 sections, 67 code cells |
| `REMEDFILM_FULL_COMPONENT_REGISTRY.json` | per-component verification |
| `REMEDFILM_FULL_RESULT_RECONCILIATION.md` | 0.837290 vs 0.837862 |
| `REMEDFILM_COMPONENT_TRAINING_HISTORY.csv` | 16,679 epoch records |
| `REMEDFILM_FULL_VAL808_METRICS.csv` | internal metrics |
| `REMEDFILM_FULL_EXTERNAL_METRICS.csv` | external metrics |
| `REMEDFILM_ABLATION_AND_PROGRESSION.csv` | 13 arms + 6 stages |
| `REMEDFILM_FULL_VISUAL_EVIDENCE_INDEX.csv` | 22 gallery panels |
| `REMEDFILM_NOTEBOOK_EXECUTION_REPORT.json` | execution record |
| `figures/` | 49 figures in 11 directories |

`ReMedFiLM_COMPLETE_MASTER.ipynb` (previous, phase-ordered) is retained and
executed; the VERIFIED master supersedes it as the definitive entry point.

---

## 14. Declaration

ReMedFiLM FULL is the proposed system throughout; GlobalMedFiLM is its verified
backbone and a baseline comparator. No GlobalMedFiLM-only result is labelled FULL.

```text
REMEDFILM_FULL_NOTEBOOK_REPAIRED__HISTORICAL_EVIDENCE_VERIFIED__NO_RETRAINING
```

All 14 hard acceptance requirements pass. The **reconstruction and repair** is
complete; C1/C2/C3 remain unexecuted science and are flagged in §11 rather than
simulated.
