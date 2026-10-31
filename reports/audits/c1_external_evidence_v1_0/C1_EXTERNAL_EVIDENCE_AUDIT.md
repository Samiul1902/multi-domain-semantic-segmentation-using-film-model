# C1 External Evidence Reconciliation and Figure Integrity Audit

**Repository:** `D:\Softfors\jup`
**Audit date:** 2026-10-31 (`AUTHOR_ENTERED_AT_WRITE`; host clock is not synchronised)
**Machine-readable record:** `claim_provenance.json` (this directory)
**Scope:** the external-dataset pilot, the Global-FiLM-versus-BARR comparison, and the five report figures

---

## 0. Headline result

The prediction figures and their per-case metrics are **genuine and reproducible**. The
architecture-comparison narrative built around them was **not**: the Regional BARR score of
86.24 % has no stored record anywhere in the repository, and the external pilot was presented as
an "independent multi-center external validation" when it is four single cases run through the
global model only.

Both classes of defect are corrected in `paper_doc/` and `docs/manuscript/`.

| Area | Verdict |
|---|---|
| Figure 4 / 5 pixel panels and TP/FP/FN/TN maps | **VERIFIED** — reproduced to 2 dp |
| Per-case metrics in Tables 5 and 6 | **VERIFIED** — all 8 cases reproduced |
| Phase 21 six-model comparison (Figure 1, 6 of 7 bars) | **VERIFIED** — exact match |
| Regional BARR 86.24 % (Figure 1, Table 1) | **UNSUPPORTED** — retracted |
| BARR parameter count 4.80 M | **UNSUPPORTED** — correct value 4,837,420 |
| "p<0.001" / "Significant" annotations | **UNSUPPORTED** — zero p-values ever computed |
| "BARR S_omega caught/rejected" external cases | **UNSUPPORTED** — BARR never executed externally |
| "S_omega eliminates 1,725 cases" | **MISATTRIBUTED** — router accounts for 1,703 of them |
| HAM10000 external Dice 79.15 % | **PARTIALLY_VERIFIED** — mask provenance undocumented |
| Dataset-level external independence | **NOT ESTABLISHED** |

---

## 1. Verified provenance table for the external pilots

All four runs used one checkpoint: `GlobalMedFiLM`,
`checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt`,
SHA-256 `286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7`, 3,523,001 parameters
(SHA-256 recomputed and matched). Inference was `512×512`, RGB, bilinear resize, sigmoid
threshold **0.5**, task ID 0/1/2/3 for ISIC/BUSI/KVASIR/KUB.

| Dataset | Documented source | Cases evaluated | Masks | Task ID | Dice | IoU | Prec | Recall | Spec | Acc |
|---|---|---|---|---|---|---|---|---|---|---|
| HAM10000 | ISIC-2018 **Task 3** training input; ViDIR/MedUni Vienna; CC BY-NC 4.0 | **1** (of 10,015) | 10,015 present, **provenance undocumented** | 0 | 79.15 | 65.50 | 100.00 | 65.50 | 100.00 | 88.17 |
| CVC-ClinicDB | Public colonoscopy set; `frame_id`/`sequence_id` supplied | **1** (of 612) | 612, name-matched, dims agree | 2 | 42.69 | 27.14 | 97.02 | 27.37 | 99.85 | 88.69 |
| BrEaST-Lesions-USG | Public breast US set, per-case folders | **1** (of 270) | 252 present; **18 images unpaired** | 1 | 18.86 | 10.41 | 16.53 | 21.94 | 91.04 | 85.87 |
| Stones_where_are_you? v3 | Roboflow, public domain, COCO-seg | **1** (of 20 test) | COCO polygons; `category_id 7 = stone` | 3 | 5.65 | 2.91 | 2.91 | 100.00 | 89.00 | 89.03 |

**Aggregation:** none. Each row is a single case. There is no dataset-level score, no mean, no CI.
Per-case metrics are computed from the same prediction array and the same ground-truth mask shown
in the corresponding panel row.

**Saved prediction files:** none persisted as arrays. The probability maps exist only as rendered
PNG panels. This is a reproducibility limitation — the numbers were verified by re-running the
forward pass, not by reading a stored prediction tensor.

**Was BARR executed?** **No.** The panel generator instantiates `GlobalMedFiLM` and calls it
directly. `R_psi`, `B_phi` and `S_omega` are never loaded. No route-decision, acceptance or
rejection record exists for any external case.

---

## 2. Dataset independence and mask provenance

### 2.1 HAM10000 — mask provenance is the decisive defect

`HAM10000/images/ATTRIBUTION.txt` identifies the folder as **ISIC-2018 Task 3** training input.
Task 3 is a *classification* task: it ships one-hot labels for MEL/NV/BCC/AKIEC/BKL/DF/VASC and
**no segmentation masks**. Yet `HAM10000/masks/` contains 10,015 masks, one per image, with no
provenance file, no licence statement and no generator record.

Consequences:

- The Dice of 79.15 % is a *correct computation* against the mask on disk.
- That mask is **not a documented ground truth**, so the value cannot be cited as an external
  segmentation score. Classified `PARTIALLY_VERIFIED`.
- Mask statistics were inspected but do not resolve origin: 40 sampled masks have foreground
  fraction 0.024–0.786 (median 0.183), all non-zero, all dimension-matched to their image. These
  are plausible lesion masks of unknown authorship.

### 2.2 HAM10000 — leakage

Exact-basename comparison against the frozen manifests:

| Quantity | Value |
|---|---|
| External HAM10000 images | 10,015 |
| Unique ISIC basenames in frozen splits (train+val+all_paired) | 3,694 |
| Frozen ISIC ID range | 0 … 36,347 |
| External HAM10000 ID range | 24,306 … 34,320 |
| **Exact image overlap** | **0** |

The ID ranges overlap numerically but the image sets are disjoint — no external image is a frozen
sample. However, the supplied `metadata.csv` has columns `image,MEL,NV,BCC,AKIEC,BKL,DF,VASC`
only: there is **no `lesion_id` and no patient identifier**. HAM10000 contains roughly 7,470
lesions across 10,015 images, so multiple images per lesion exist and lesion-level independence
cannot be excluded. Both sets are also ISIC/HAM10000 lineage, which is why the project's own
EXT-01 audit rated the semantic risk **HIGH**.

**Verdict:** image-level disjoint (`VERIFIED`); lesion-level and dataset-level independence
`NOT ESTABLISHED`.

### 2.3 CVC-ClinicDB

612 images, 612 masks, **all 612 name-matched**, no dimension mismatch. `metadata.csv` supplies
`frame_id` and `sequence_id`, so video-sequence grouping **is** available and clustered statistics
would be possible. No filename or ID overlap with the frozen KVASIR set.

### 2.4 BrEaST-Lesions-USG

270 images and 252 `_tumor` masks: **18 images (6.7 %) have no mask** and are unusable. Grouping
is per case folder (`case001` … `case256`), so case-level grouping is available; note that some
cases contribute more than one image, so images within a case are correlated. The case used in
the pilot (`case001`) is paired.

### 2.5 Stones_where_are_you? v3

Verified identity: Roboflow `xray-abdomen-to-identify-stones/stones_where_are_you`, exported
2024-08-07, licence **Public Domain**. Ten anatomical categories (`cells`, `DJ`, `accessory`,
`bladder`, `bone_calcification`, `gas`, `kindey`, `stone`, `suture`, `ureter`). Mapping
`category_id == 7 → stone` is **valid**. Annotations are COCO polygon segmentations; the pilot
case (image `id=3`, `1_png.rf.abc80bc7421275856b6fdfaa0c0282d3.jpg`, 640×515) has exactly one
stone annotation with one polygon, so the single-polygon ground-truth construction is complete for
that image. The test split has 20 images, 9 stone annotations and **only 6 images containing a
stone**.

---

## 3. Global FiLM versus Regional BARR comparability

### 3.1 What is verified

Phase 21 evaluated six architectures under one shared protocol on VAL808 (n = 808). Every value in
Table 1 of the report matches `reports/tables/phase21_six_model_comparison.csv` exactly:

| Model | Parameters | Macro Dice | Macro IoU | KUB Dice |
|---|---|---|---|---|
| Global MedFiLM | 3,523,001 | 83.5079 | 74.4837 | 76.4058 |
| DeepLabV3+ | 40,347,041 | 82.7652 | 74.1205 | 73.8660 |
| Transformer/MiT U-Net | 16,347,777 | 82.2383 | 73.6599 | 72.5182 |
| U-Net++ | 9,159,681 | 79.2010 | 69.1026 | 72.0662 |
| Attention U-Net | 7,851,285 | 78.9037 | 69.2749 | 69.5778 |
| U-Net | 7,763,041 | 78.7832 | 68.8096 | 72.1089 |

BARR is verified on two populations, each with its own label:

| Population | Global | BARR | Delta | Source |
|---|---|---|---|---|
| VAL808, Phase 29 three-seed mean | 83.5079 | **83.7902** | +0.2823 pp (seed range +0.2210 … +0.3388) | `phase29_phase_d_three_seed_descriptive_summary.json` |
| ROUTER_HOLDOUT n=875, one-shot | 92.8548 | **93.0287** | +0.1739 pp, CI [+0.1117, +0.2405] | `phase30_primary_noninferiority_result.json` |

Parameter total: **4,837,420** (G 3,523,001 + R_ψ 1,276,401 + B_φ 36,801 + S_ω 1,217), from the
strict-load component audit in `phase36_robustness_scientific_result_v1_23.json`.

### 3.2 The 83.51 % → 86.24 % claim is not supported

| Check | Result |
|---|---|
| Any JSON record in `reports/` containing `86.24` | **0** |
| `86.24` appears in any file at all | only `scripts/analysis/generate_word_report.py` (the report generator itself) |
| Consistent with VAL808 BARR value (83.79 %) | **No** — differs by 2.45 pp |
| Consistent with holdout BARR value (93.03 %) | **No** — differs by 6.79 pp |
| Implied improvement (+2.73 pp) vs canonical +0.28 pp | **~10× too large** |

**The 2.73 pp improvement does not exist.** The canonical evidence supports *preservation*: +0.28 pp
on VAL808 and +0.17 pp on the holdout, both within a −0.5 pp non-inferiority margin, with BUSI and
KVASIR CIs including zero.

Two further defects follow from the same table:

- BARR was **never** an arm of the Phase 21 six-model run. Plotting it as a seventh bar implies a
  controlled head-to-head that does not exist. It is now a separately hatched bar labelled
  "separate run, not a Phase 21 arm".
- The report's BARR IoU (77.85 %) and BARR KUB Dice (85.57 %) are unsupported in the VAL808
  context. 85.57 % is in fact the ROUTER_HOLDOUT KUB value, transplanted onto a VAL808 table.

**BARR must not be called the top-performing configuration.** The only defensible statement is that
Global MedFiLM ranks first of six under the Phase 21 protocol, is not statistically distinguishable
from DeepLabV3+, and that BARR preserves its accuracy on two further populations.

---

## 4. External safety claims

| Claim in previous report | Executed? | Verdict |
|---|---|---|
| "BARR Filter S_omega Triggered" (BrEaST row, Figure 5) | No | **UNSUPPORTED** — hardcoded string |
| "Acoustic shadow FP. Caught by BARR S_omega." (Table 5) | No | **UNSUPPORTED** |
| "BARR Post-Safety Filter eliminates 1,725 harmed cases" | Partially | **MISATTRIBUTED** |
| Regional candidate generation on external data | No | Not executed |
| Regional refiner on external data | No | Not executed |
| Benefit router on external data | No | Not executed |
| Selective acceptance gate on external data | No | Not executed |
| Final fallback to global segmentation on external data | No | Not executed |

The BrEaST claim is the clearest failure: the panel generator hard-codes
`"verdict": "Acoustic Shadow Shift (BARR Filter S_omega Triggered)"` as a literal string. No BARR
component is even instantiated in that script. The assertion was decorative, not measured.

**Harm attribution decomposition** (Phase 28, ROUTER_DEVELOPMENT n = 4,957, in-sample):

| Step | Harmful cases | All-population rate |
|---|---|---|
| A1 unconditional refine | 2,115 | 42.67 % |
| A7 router only | 412 | 8.31 % |
| A8 router + S_ω | 390 | 7.87 % |

Router: 2,115 → 412 = **1,703 cases**. S_ω: 412 → 390 = **22 cases**. The 1,725 figure is the
A1 → A8 system-level total and was previously credited entirely to the safety filter. A reduced
average harm rate is also **not** evidence of zero harmful outcomes: 390 harmful refinements
remain in A8.

---

## 5. Figure integrity

| Figure | Exists | Size | Generating script |
|---|---|---|---|
| `fig1_model_comparison.png` | yes | 0.24 MB | **previously none** → `scripts/analysis/build_verified_comparison_figures.py` |
| `fig2_domain_performance.png` | yes | 0.17 MB | **previously none** → same |
| `fig3_safety_compute.png` | yes | 0.17 MB | **previously none** → same |
| `fig4_internal_4domain_predictions.png` | yes | 3.89 MB | `scripts/analysis/generate_prediction_panels.py` |
| `fig5_external_4domain_predictions.png` | yes | 5.49 MB | same |

Before this audit, **fig1–fig3 had no generating script in the repository** — the Word builder only
embedded pre-existing PNGs. That made their contents unauditable. They are now generated from the
frozen result artifacts, so every plotted value is traceable.

### 5.1 Defects found and fixed

1. **Row labels clipped off-canvas (fig4, fig5).** `Axes.set_ylabel(..., labelpad=72)` combined
   with `left=0.08` pushed the multi-line row label outside the figure, so the case identity,
   metrics and status were **illegible** in the published PNG. Replaced with `fig.text` at a fixed
   anchor inside a widened left margin (`left=0.215`). All labels are now readable.
2. **Fabricated BARR verdict strings.** Removed; replaced with provenance lines.
3. **Hardcoded "subclass" labels presented as predictions.** Relabelled as
   "Presentation label (analyst metadata, not a model output)".
4. **BARR claim embedded in the figure title/subtitle.** Removed; the subtitle now states that no
   BARR component was executed.
5. **Figure 1 plotted BARR at 86.24 % with no comparability marking.** Replaced with 83.79 % from
   the Phase 29 record, hatched and labelled as a separate run, with the y-axis truncation stated.
6. **Figure 2 plotted absolute scores on a truncated 80–100 axis**, making a 0.17 pp difference
   look substantial, with no CIs. Replaced with a **delta plot with 95 % CIs** and the
   non-inferiority margin.
7. **Figure 3 attributed the whole harm reduction to A8.** Now decomposed into A1 / A7 / A8 so the
   router-versus-safety split is visible, with an in-sample caveat.

### 5.2 Colour key and metric contract

The required key is honoured exactly in fig4/fig5: TP `#00E600`, FP `#FF2020`, FN `#2060FF`,
TN `#181818`. All six metrics (Dice, IoU, precision, recall, specificity, accuracy) are computed
from the same prediction and ground truth. "Class-wise" here means foreground versus background
under the current binary ontology — no pixelwise subclass prediction is claimed.

### 5.3 Degenerate case disclosed

The KUB case in Figure 4 has a **14-pixel** ground truth (TP 14, FP 15, FN 0). Dice 65.12 % on 14
pixels is dominated by a handful of boundary pixels and is not representative of the KUB domain
value (76.41 % macro over 280 cases). This is now stated in the report.

---

## 6. Unsupported or retracted claims

| # | Claim | Status | Action |
|---|---|---|---|
| 1 | Regional BARR macro Dice 86.24 % | UNSUPPORTED | Replaced by 83.79 % (VAL808) and 93.03 % (holdout) |
| 2 | BARR parameters 4.80 M | UNSUPPORTED | Corrected to 4,837,420 |
| 3 | "p<0.001", "p<0.01", "(Significant)" | UNSUPPORTED | Removed; descriptive CIs only |
| 4 | "BARR S_ω triggered / caught" on external cases | UNSUPPORTED | Removed |
| 5 | "S_ω eliminates 1,725 harmed cases" | MISATTRIBUTED | Decomposed: router 1,703, S_ω 22 |
| 6 | "BARR lifts TINY from 53.21 % to 85.57 %" | UNSUPPORTED | Removed; no per-stratum BARR result |
| 7 | BARR KUB Dice 85.57 % / IoU 77.85 % on VAL808 | UNSUPPORTED | Removed from the VAL808 table |
| 8 | "Independent external multi-center datasets" | OVERSTATED | Reclassified as a 4-case pilot |
| 9 | "Global stage ≈ 4.2 GFLOPs; >65 % reduction" (manuscript §14) | UNSUPPORTED | Corrected to 63.10 GFLOPs global, 64.88 GFLOPs A8, ratio 1.028 |
| 10 | Injection-depth ablation superiority (manuscript §16.1) | UNSUPPORTED | Removed; no such ablation |
| 11 | τ-sweep "empirical Pareto frontier" (manuscript §16.2) | UNSUPPORTED | Removed; no sweep executed |
| 12 | PCA mechanistic interpretation of γ/β (manuscript §15) | UNSUPPORTED | Removed; descriptive attribution retained |
| 13 | "IRB provenance" for all datasets (manuscript §18) | OVERSTATED | Corrected: public de-identified repositories, no IRB obtained |
| 14 | "Cryptographic signing makes findings immune to cherry-picking" | FALSE | Corrected; trust boundary is contaminated |
| 15 | "27 RC3 + 43 RC2 tests pass with 100 % compliance" | OVERSTATED | Corrected: 42 of 43 RC2 pass; 1 fails |

---

## 7. Manuscript evidence classification update

`docs/manuscript/RA_MEDFILM_BARR_MANUSCRIPT_DRAFT.md` was updated in place; the original file is
preserved in Git history.

- Abstract now states the **preservation** result (+0.28 pp VAL808, +0.17 pp holdout) rather than
  implying improvement, and states that no confirmatory significance procedure is eligible.
- §3 adds the external pilot as a `Descriptive Only` item, explicitly not a contribution and not a
  validation.
- §5.3 is new: verified component parameter accounting totalling 4,837,420.
- §10 adds `PARTIALLY_VERIFIED` and `UNSUPPORTED` to the evidence hierarchy.
- §12 adds the router-versus-safety decomposition and the in-sample caveat.
- §13.1 is new: the four-case external pilot table, mask-provenance warning, independence limits
  and descriptive failure modes.
- §14 is rewritten from the Phase 34 analytical compute contract; the 4.2 GFLOPs / ">65 %" figures
  are withdrawn in place.
- §15, §16.1, §16.2 and §18 corrected as listed above.
- §17 gains four limitations: no confirmatory statistics, cross-run comparison, in-sample safety
  evidence, and the pilot's non-validation status.

---

## 8. Trust-boundary containment (unchanged)

No trust material was read for authorisation, generated, modified or deleted. `provision_trust_store.py`
was **not** executed. No production grant was minted. No C1 training was started. RC3 remains frozen
at digest `54d1273a…3549f` and was not modified. No RC4 was created. The production trust root
remains excluded from scientific execution pending accountable human review.

---

## 9. What remains unresolved

1. **HAM10000 mask provenance** — the single largest blocker for citing any HAM10000 segmentation
   score. Resolving it requires locating the original mask source, or discarding the masks and
   excluding HAM10000 from segmentation evaluation.
2. **No external validation cohort** — Phase 32 found none eligible. The pilot does not change this.
3. **No saved prediction tensors** — external probability maps exist only as PNG renders. Storing
   arrays would make future re-verification independent of a forward pass.
4. **18 unpaired BrEaST images** — should be excluded explicitly in any future protocol.
5. **Cross-run BARR comparison** — a controlled BARR-versus-baseline head-to-head has never been
   executed and cannot be claimed.
6. **Trust boundary and host clock** — unchanged from the prior audit; no execution is authorised.

---

## 10. Scientific status

The reconciled evidence supports one defensible claim set: Global MedFiLM at 83.51 % macro Dice on
VAL808 with 3.52M parameters, first of six under a shared protocol but not distinguishable from
DeepLabV3+; Regional BARR **preserving** that accuracy within a −0.5 pp margin; the router removing
most harmful refinements in-sample; and four internal plus four external single cases reproducing
exactly with genuine domain-shift failure modes visible at the pixel level.

It does not support any external validation claim, any superiority claim, any confirmatory
significance claim, or any assertion that BARR improved external safety.

**Terminal:** `RA_MEDFILM_BARR_EXTERNAL_EVIDENCE_RECONCILED__GLOBAL_VS_BARR_COMPARISON_GROUNDED__FIGURES_SCIENTIFICALLY_VALIDATED`
