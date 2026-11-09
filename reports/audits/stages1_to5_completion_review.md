# Master Scientific Audit & Completion Review: Stages 1–5
**Project:** RA-MedFiLM-BARR
**Repository:** `D:\Softfors\jup`
**Role:** Senior Medical Image Segmentation Research Scientist & Independent Scientific Reproducibility Auditor
**Audit Date:** November 3, 2026
**Revision:** 2 — reconciled with FULL Phase A and re-verified against source artifacts
**Status:** `STAGES_1_5_TECHNICALLY_VERIFIED__SCIENTIFIC_EVIDENCE_PENDING`
*(Revision 1 carried unconditional `CERTIFIED COMPLETE` labels. Those are withdrawn: see §0.2.)*

---

## 0. What changed in this revision

Revision 1 of this document asserted a number of figures that do not survive contact with the
repository. This revision re-derives every quantitative claim from an artifact on disk and
records where the two disagreed.

### 0.1 Corrections

| # | Revision 1 claim | Verified value | Nature |
|---|---|---|---|
| 1 | Lite = **1,586,817** params | **272,601** (`depthwise_compact` complete graph) | Untraceable figure. Absent from every artifact and from all git history; no subset-sum of the real component sizes reproduces it. |
| 2 | `R_psi` = 1,299,649 | **1,276,401** | Component mis-transcription; the R+B+S *sum* was preserved, so the FULL total still closed and the error hid. |
| 3 | `B_phi` = 12,961 | **36,801** | Same. |
| 4 | `S_omega` = 1,809 | **1,217** | Same. |
| 5 | Med-DANet = "Shen, Z. et al. 2024, WACV" | Two distinct papers | Conflation + wrong author initial + invented title. |
| 6 | JFS = "Joint Filtering and Segmentation … Post-hoc Mask Verification, ICIP 2024" | "Judging From Support-set …", **ICIP 2025** | Wrong title, wrong acronym expansion, wrong venue, and a wrong *characterisation*. |
| 7 | Latotzke et al. 2021, MedIA 71, 102045 | **Fabricated** | MedIA 71:102045 is Slator et al.; no Latotzke author exists in that volume. |
| 8 | "73/73 Stage 6 baseline and integration tests pass" | **47** | Not reproducible; measured 36 + 11. |
| 9 | H1–H7 "formalized", claim-to-evidence matrix "established" | Both exist **only in this document** | Not in the manuscript, not in any frozen spec. |

The FULL total of **4,837,420** was correct throughout and is unchanged.

### 0.2 Certification language withdrawn

"STAGE n CERTIFIED COMPLETE" is removed. A stage cannot be certified by the same document that
asserts the standard it is measured against, and three of the five stages rest on evidence that
is historical, in-sample, or not yet executed. §7 replaces the labels with a five-state matrix.

---

## 1. Stage 1 — Research Problem and Literature Review

### 1.1 Problem formulation (unchanged, supported)
Multi-domain medical image segmentation across dermoscopy, breast ultrasound, endoscopy and
abdominal radiography presents (i) cross-domain gradient interference and (ii) computational
misallocation on small, clinically critical structures. Both are documented in the manuscript
and are not in dispute.

### 1.2 Prior art — corrected

**Med-DANet is two papers, and they must be cited separately.**

| | Verified record |
|---|---|
| Med-DANet (V1) | Wang, W.; Chen, C.; Wang, J.; Zha, S.; Zhang, Y.; Li, J. *Med-DANet: Dynamic Architecture Network for Efficient Medical Volumetric Segmentation.* ECCV 2022, 506–522. DOI `10.1007/978-3-031-19803-8_30` |
| Med-DANet V2 | Shen, H.; Zhang, Y.; Wang, W.; Chen, C.; Liu, J.; Song, S.; Li, J. *Med-DANet V2: A Flexible Dynamic Architecture for Efficient Medical Volumetric Segmentation.* WACV 2024, 7871–7881. DOI `10.1109/WACV57701.2024.00769` |

V1 selects a candidate model from a pre-defined bank per 2-D slice. V2 replaces the two-stage
pipeline with a per-slice foreground crop (Decision Network + Crop Position Network) plus a
stage-wise quantization selector. Revision 1 attached V2's authors and venue to V1's name and an
invented title.

**JFS is an evaluation procedure, not a filter.**

> Moon, S.; Liu, Q. T.; Kong, H.; Khan, M. H. *Judging From Support-set: A New Way To Utilize
> Few-Shot Segmentation For Segmentation Refinement Process.* ICIP 2025 (14–17 Sep 2025,
> Anchorage, AK), DOI `10.1109/ICIP55913.2025.11084668`; preprint 2024.

JFS feeds coarse and refined masks to a few-shot segmentation model as support masks and asks
whether the refinement succeeded. It therefore *judges* refinement after the fact and, being an
evaluation pipeline, saves no computation. Revision 1 described it as a post-hoc mask filter,
which misstates both the mechanism and the axis of difference. The manuscript now states the
distinction correctly: JFS answers "was the refinement worth it?" post hoc; RA-MedFiLM-BARR
learns a **pre-execution** gate so that skipped regions cost nothing.

**The Latotzke citation was fabricated and has been replaced.**

Revision 1 cited "Latotzke, A. et al. (2021). Cascaded classification and refinement for
fine-grained lesion segmentation. *Medical Image Analysis*, 71, 102045." Three independent
checks fail it: MedIA vol. 71 article 102045 is Slator et al. (*InSpect*), no author surnamed
Latotzke appears anywhere in that volume, and no such title exists. The verified record —
already present in the project's own `reports/audits/final_manuscript_reference_audit.json` and
cross-checked on arXiv — is:

> Latotzke, C.; Loh, J.; Gemmeke, T. *Cascaded Classifier for Pareto-Optimal Accuracy-Cost
> Trade-Off Using off-the-Shelf ANNs.* LOD 2021, Springer LNCS. DOI
> `10.1007/978-3-030-95470-3_32`; arXiv `2110.14256`.

It is a **classification** cascade with learned pass-on criteria, not lesion segmentation, so the
body sentence was rewritten accordingly. This is also a better fit for the argument being made:
the paper is explicitly about an accuracy-cost trade-off frontier.

**Remaining closest-prior-work references verified.** Russell & Wefald (1991), *Artificial
Intelligence* 49(1–3):361–395, DOI `10.1016/0004-3702(91)90015-C`; Künzel et al. (2019), PNAS
116(10):4156–4165, DOI `10.1073/pnas.1804597116`; Isensee et al. (2021), *Nature Methods*
18(2):203–211, DOI `10.1038/s41592-020-01008-z`. All confirmed. DOIs added to the first two.

### 1.3 Novelty discipline
The Phase-23 verdict already positions the contribution as a **system/integration** novelty
explicitly downstream of metareasoning, cascades, CATE and JFS — not a new primitive. The
manuscript body does not claim that pre-execution compute allocation, cost-aware cascades, or
refined-vs-coarse acceptance are new. No novelty claim was added or strengthened in this revision.

---

## 2. Stage 2 — Research Gap, Hypotheses and Novelty Design

### 2.1 The H1–H7 problem
Revision 1 stated that H1–H7 were "formalized" with falsification criteria and that an "explicit
claim-to-evidence matrix" was established. **Both artifacts exist only inside this audit
document.** A repository-wide search finds no `Falsification Criterion` text and no
claim-to-evidence matrix outside this file. The manuscript's only formal hypothesis is the frozen
C1 directional test in §9.2 (H₀: Δ_macro ≤ 0 vs H₁: Δ_macro > 0), which is a different object.

Consequence: Stage 2 is **design-supported but not manuscript-integrated**. The hypotheses are
usable as an internal working catalogue; they are not yet a citable scientific artifact.

### 2.2 The three gaps (supported as design rationale)
1. *Causal FiLM attribution* — prior FiLM work in medical imaging lacks an unconditioned identity
   control with bit-identical initialisation, architecture and optimiser state.
2. *Contamination-proof split governance* — patient-level leakage and unverified external
   distributions are common.
3. *Expected-utility selective refinement* — pre-execution gain prediction under an explicit cost
   threshold, combined with a post-refinement safety gate.

Gap 3 is the weakest and must stay narrowly stated: Latotzke (2021) already formalises cascades
with learned pass-on criteria under cost, and Med-DANet V2 already makes a pre-execution compute
decision in medical segmentation. The defensible residual is the *combination* — learned
GT-free ΔQ regression gating an optional regional refiner, with a separate post-refinement
acceptance module — not any single mechanism.

### 2.3 H1–H7 catalogue (internal working status)

> **Superseded as a source of truth.** H1–H7 and the claim-to-evidence
> classification now have an authoritative, versioned home in
> [`docs/phase36_hypotheses_claim_evidence_v1_0.md`](../../docs/phase36_hypotheses_claim_evidence_v1_0.md).
> The table below is retained as the audit's working snapshot; where the two
> disagree, the spec wins.

| ID | Claim | Falsification criterion | Status |
|---|---|---|---|
| H1 | Task-conditioned γ/β beat the frozen identity control C1-C on VAL808 across seeds 42/123/3407 | lower bound of the 95% paired cluster-percentile bootstrap CI ≤ 0.0 pp | `NOT_ESTABLISHED` (0/6 C1 runs) |
| H2 | Learned ΔQ routing suppresses harmful refiner activations by ≥70% vs A1 | reduction < 70% | historical descriptive only (75.69%, in-sample) |
| H3 | S_ω rejects degrading candidates without GT at inference | final harm rate exceeds unconditional harm rate | historical descriptive only |
| H4 | On ROUTER_HOLDOUT (n=875) BARR preserves global accuracy while cutting refiner execution >75% | preservation rejected, or compute reduction < 70% | historical descriptive only (+0.17 pp, non-confirmatory) |
| H5 | End-to-end inference uses only (X, t) | any inference signature touching labels | **verified by test** |
| H6 | Zero-shot external transfer exposes the 14/14 stone-free failure | suppression or concealment of that finding | **verified descriptive** |
| H7 | Lite achieves ≥50% parameter reduction vs FULL with intact graph contract | reduction < 50% or broken GT-free interface | **verified** (94.36%) |

---

## 3. Stage 3 — Dataset Preparation and Preprocessing

### 3.1 What every number means
Read directly from `manifests/phase4_v3/` (not from metadata assertions):

| Partition | n | ISIC | KUB | KVASIR | BUSI | SHA-256 (prefix) |
|---|---|---|---|---|---|---|
| TRAIN | 5,832 | 2,556 | 1,978 | 696 | 602 | `28702fc3a5ff8b95…` |
| VAL | 808 | 357 | 280 | 87 | 84 | `082c80b2bda63fd7…` |
| TEST | 1,683 | 735 | 558 | 216 | 174 | `9361eba61c91c034…` |
| QUARANTINED | 118 | 46 | 4 | 1 | 67 | `a4ec1a8c46692f3c…` |
| **all_paired** | **8,441** | 3,694 | 2,820 | 1,000 | 927 | `eb3062fa0e84f995…` |

**5,832 + 808 + 1,683 + 118 = 8,441** exactly. The 118 are not a rounding residue: they are
samples permanently removed from modelling because of patient-level overlap or duplicate image
series, and they are excluded from TRAIN, VAL and TEST alike.

TEST 1,683 is locked and is not read by any stage in this pipeline. QUARANTINE is never loaded.

### 3.2 TRAIN = ROUTER_DEVELOPMENT + ROUTER_HOLDOUT
From `reports/audits/phase24_router_split_manifest.csv` (5,832 rows, identical domain
composition to TRAIN):

- `ROUTER_DEVELOPMENT` = **4,957**
- `ROUTER_HOLDOUT` = **875**
- 4,957 + 875 = **5,832** ✔

**What the ROUTER_HOLDOUT restriction actually means.** The 875 are *excluded from router and
safety fitting and from all fold construction* — they never appear in a FIT, EARLY_STOP or
OUTER_TARGET role. They are **not** excluded from backbone training: G is fitted on the whole
5,832-row TRAIN manifest, which contains the 875. ROUTER_HOLDOUT is therefore a **development
partition nested inside TRAIN**, not a fresh test set, and Phase-30's numbers on it are
descriptive. This is consistent with the manuscript's own disclosure ("previously opened under a
disclosed post-first-open source deviation, retrospective and non-independent") and is the
central caveat carried into §5.

### 3.3 Actual per-stage sample consumption (FULL pipeline)
| Stage | Population read | n | Notes |
|---|---|---|---|
| G | TRAIN / VAL | 5,832 / 808 | includes all 4,957 dev **and** all 875 holdout |
| CACHE | ROUTER_DEVELOPMENT | 4,957 | one G forward per sample |
| R | ROUTER_DEVELOPMENT, 3 outer folds | 4,957 | fit + early_stop per fold |
| L | ROUTER_DEVELOPMENT, per fold outer_target | 4,957 | fold-k refiner labels fold-k target |
| B | action-available ROUTER_DEVELOPMENT | ≤ 4,957 | 5-fold frozen role table |
| S | action-available ROUTER_DEVELOPMENT | ≤ 4,957 | 5-fold frozen role table |
| TEST | — | **0** | locked |
| QUARANTINE | — | **0** | never loaded |

### 3.4 Preprocessing compatibility with the frozen C1 recipe
`reports/planning/c1_film_attribution_v1/protocol.json` specifies resolution 512, RGB 3-channel,
BCE+Dice (0.5/0.5, ε=1e-6), AdamW 1e-4/1e-4, cosine T_max 100, batch 4/8, patience 15, AMP,
`phase20_domain_balanced_uniform_v1` sampling, threshold 0.5,
`phase20_macro_domain_mean_dice_v1` selection with 1e-12 tolerance and lower-val-loss tie-break.
It also lists `prohibited: [TEST, ROUTER_HOLDOUT, EXTERNAL, QUARANTINE]` — a constraint on *C1
evaluation*, not on backbone training data.

The FULL G stage reproduces the same recipe and the same manifest digests. Bilinear image
resampling with nearest-neighbour masks and the 1.50 context expansion are unchanged. **No frozen
split was modified.** The protocol's own SHA-256 is recorded in the Stage-1 summary and was not
touched.

---

## 4. Stage 4 — Proposed Architecture Implementation

### 4.1 Parameter inventory — corrected
All values below were re-derived by instantiating the classes from source, and cross-checked
against `reports/tables/barr_lite_synthetic_profile.json`, which was produced by loading the real
checkpoints.

| Component | Parameters | Source |
|---|---|---|
| GlobalMedFiLM `G` | **3,523,001** | `GlobalMedFiLM` |
| — backbone | 3,432,233 | |
| — FiLM generators (5 sites) + task embedding | 90,768 (2.58%) | |
| Regional refiner `R_ψ` | **1,276,401** | `BARRRegionalRefinerV1` |
| Benefit router `B_φ` | **36,801** | `phase25_models.BARRBenefitRouterV1` |
| Post-safety `S_ω` | **1,217** | `phase25_models.BARRPostSafetyV1` |
| **FULL complete graph** | **4,837,420** | 3,523,001 + 1,276,401 + 36,801 + 1,217 |
| Identity control C1-C | trainable 3,432,233 / total 3,523,001 | freeze-at-init; **total is unchanged by freezing** |

### 4.2 Lite candidates — resolved
Three candidates exist in `src/models/lite/ra_medfilm_barr_lite.py`. Each is a *complete graph*:
compact G + compact R_ψ **plus the full-size frozen B_φ and S_ω**, which remain required.

| Candidate | G | R_ψ | B_φ | S_ω | **Complete graph** | G+R only | Reduction vs FULL | Trainable / Frozen |
|---|---|---|---|---|---|---|---|---|
| `width_compact` | 882,333 | 319,929 | 36,801 | 1,217 | **1,240,280** | 1,202,262 | 74.36% | 1,240,280 / 0 |
| **`depthwise_compact`** | 176,454 | 58,129 | 36,801 | 1,217 | **272,601** | 234,583 | **94.36%** | 272,601 / 0 |
| `ultralite_depthwise_add` | 28,506 | 15,505 | 36,801 | 1,217 | **82,029** | 44,011 | 98.30% | 82,029 / 0 |

Configuration for the selected candidate: `block_kind=depthwise`, `skip_fusion=concat`,
`global_channels=(12,24,48,96,128)`, `refiner_channels=(8,16,32,48,64)`,
`embedding_dim=16`, `film_hidden_dim=32`, variant id
`ra_medfilm_barr_lite_depthwise_compact_v1`, architecture SHA-256 `a27a3c5a…cb3a21`.

**Where 1,586,817 came from: nowhere.** It appears in no artifact, in no git revision, and no
combination of the ten real component sizes sums to it. It is withdrawn. The three figures quoted
in the earlier synthetic profile (1,240,280 / 272,601 / 82,029) are the correct complete-graph
counts and reproduce exactly.

**Selected first Lite training candidate: `depthwise_compact`, unchanged.** The evidence supports
it — 94.36% parameter reduction with the frozen router and safety modules retained, and it is the
model key registered in the Stage-6 matrix (`RA_MEDFILM_BARR_LITE_DEPTHWISE`). Nothing found in
this audit argues for reconsideration.

### 4.3 Architecture drift eliminated
`BARRBenefitRouterV1` and `BARRPostSafetyV1` previously existed in three forms: the canonical
top-level scripts (which run training on import and cannot be imported), the regex extraction
several Phase-29/34/35 audit scripts perform on that text, and a verbatim copy inside the FULL
pipeline. Two independent drift paths against checkpoints that must remain bit-compatible.

`src/models/barr/phase25_models.py` is now the single pure definition (no data access, no
training, no import-time side effects). The legacy producers are deliberately untouched so frozen
historical behaviour is preserved. `tests/test_phase25_architecture_drift.py` extracts the class
text from both canonical scripts and asserts equality on state-dict keys and shapes, parameter
counts, same-seed initial weights, and bit-identical forward output; it also pins the FIT-only
ddof=0 zero-sigma normalisation and the raw-logit output contract. **12 passed.**

### 4.4 GT-free interface
`output = model.infer(image, task_id)`. No mask, label or target-derived statistic is reachable
from the inference signature or from any feature vector. Verified by test on the real family and
by the FULL branch-coverage test.

---

## 5. Stage 5 — Historical Experiments and Initial Feasibility

### 5.1 The `+0.17 pp` result — traced and correctly labelled
Source: `reports/audits/phase30_primary_noninferiority_result.json`.

| Field | Value |
|---|---|
| population | ROUTER_HOLDOUT, n = 875 |
| global macro Dice | 0.9285481511747413 |
| A8 (BARR) macro Dice | 0.9302871820357663 |
| macro delta | 0.0017390308610248934 → **+0.17 pp** |
| 95% CI | [0.001117, 0.002405] → **[+0.11, +0.24] pp** |
| `p_values_computed` | **0** |
| `significance_adjudication_performed` | **false** |
| criterion | lower CI > −0.005 (non-inferiority margin) |

The review's characterisation is correct and is retained: descriptive, non-confirmatory,
preservation rather than improvement, on a partition nested inside TRAIN. It must never be
presented as prospective superiority.

### 5.2 The 884-case external stress test — traced
Source: `reports/tables/c1_external_stress_per_case.csv` (884 `global` rows).

- CVC-ClinicDB **612**, BrEaST-Lesions-USG **252**, Stones **20** = 884 ✔
- Stones 20 = 6 stone-positive + 14 stone-free
- **All 14 stone-free images are false-positive foreground predictions** (Dice 0, Precision 0) —
  confirmed row by row, and asserted by
  `test_c1_external_stress.py::test_all_fourteen_stone_free_images_are_false_positives`
- HD95 is `NaN` on empty GT rather than fabricated as 0

This failure mode remains prominent in both the manuscript and the abstract. It is the single
most important negative result in the project and is preserved, not softened.

### 5.3 The 24 controlled cells — verified NOT_ESTABLISHED
From `src/research/stage6/matrix.py`: `MODEL_KEYS` = 8 architectures × `SEEDS` = (42, 123, 3407)
= **24 cells, all `MISSING`**. Confirmed programmatically, not from prose.

### 5.4 Historical results that must not be promoted
- Phase 20b/21 single-run baselines: `PROTOCOL_INCOMPARABLE`.
- Phase 25/28 BARR ablation: **in-sample** on ROUTER_DEVELOPMENT (4,957 ⊂ TRAIN). Harm rate
  42.6670% (A1) → 7.8677% (A8) unconditional; the 32.37% = 390/1,205 figure is *conditional on
  acceptance* and must never be quoted as the unconditional rate.
- Phase 29: downstream-only seed variation; the backbone was not re-trained.

---

## 6. FULL Phase A — reconciliation and cross-fitting

### 6.1 What exists
`src/research/full_pipeline/` drives one isolated family per seed through
`G → CACHE → R → L → B → S`, with `scripts/training/full_barr_three_seed.py` as the only entry
point. CACHE and L are new producers that did not previously exist: CACHE performs one G forward
per sample and writes the ROI-0.30 crop, 512-canvas probability and 202-D router features; L
refines each outer fold's own `outer_target` with that fold's refiner to produce paired-gain
labels.

### 6.2 The cross-fitting question, answered precisely

| Stage | Checkpoint used | Trained on | Early-stop on | Predicts on | Target sample seen by the checkpoint? |
|---|---|---|---|---|---|
| G | `G/best.pt` | TRAIN 5,832 | VAL 808 | — | **YES** — all 4,957 dev samples are inside TRAIN |
| CACHE | `G/best.pt` | as above | — | 4,957 dev | **YES** (in-sample features) |
| R fold k | `R/foldk/best.pt` | outer folds ≠ k | inner split of ≠ k | fold k outer_target | **NO** — genuine OOF |
| L fold k | `R/foldk/best.pt` | as above | as above | fold k outer_target | **NO** for R; **YES** for the G prediction it refines |
| B fold k | `B/foldk/best.pt` | frozen cv5 FIT | frozen cv5 EARLY_STOP | frozen cv5 OUTER_TARGET | **NO** for B; **YES** for G |
| S fold k | `S/foldk/best.pt` | frozen cv5 FIT | frozen cv5 EARLY_STOP | frozen cv5 OUTER_TARGET | **NO** for S; **YES** for G |

**The precise statement, which revision 1 did not make:** the labels are **out-of-fold with
respect to the refiner, the router and the safety module, and in-sample with respect to the
backbone.** G is fitted once on all 5,832 TRAIN rows, so `p_global` — and therefore the ΔQ being
regressed — is computed from a backbone that has already memorised the sample. `delta_dice`
measures what a fold-k refiner does to the output of a G that has seen the target.

Consequences that must be stated wherever these numbers are used:
1. Absolute harm rates are **optimistic**; they are not held-out estimates.
2. Router separability on ΔQ is likely inflated relative to a truly backbone-OOF construction.
3. A fully OOF design would require a G cross-fit (train G on the complement of each fold), which
   would cost 3–5× more compute and would break comparability with the frozen Phase-25D labels.

**This is not repaired, and deliberately so.** It is inherited from the frozen Phase-25D/25F
producers; changing it would silently invalidate historical comparability. Instead it is now
recorded in machine-readable form: `label_stage.oof_contract()` writes
`refiner_out_of_fold: true`, `router_out_of_fold: true`, `safety_out_of_fold: true`,
`backbone_out_of_fold: false`, `backbone_sees_target_sample: true`, plus a plain-language
`consequence` string into every L manifest, and tests assert it. The claim can no longer be
overstated by accident.

### 6.3 Fold assignment integrity
`test_label_fold_assignment_matches_the_frozen_outer_folds` asserts that each sample is labelled
only by the fold whose `outer_target` contains it, that no sample appears in two outer folds, and
that every label row carries the 64-hex digest of the refiner checkpoint that produced it. The
3 outer refiner folds and the frozen 5-fold router/safety roles are distinct structures over the
same 4,957-sample population; the 5-fold table supplies FIT / EARLY_STOP / OUTER_TARGET
membership verbatim and is never re-derived or permuted.

### 6.4 Defects found and repaired in Phase A
- `population.derive_folds` kept its bucket-size cursor inside the per-domain loop, so a domain
  with fewer groups than `n_outer` filled only the first `groups_per_domain` buckets and the tail
  folds had an **empty** `outer_target` — a silent mis-fold. Cursor is now global, with fail-fast
  checks for under-grouped populations and empty roles.
- Router/safety cross-fit had invented an inner early-stop permutation instead of consuming the
  frozen Phase-25D role table. Replaced, with empty-role and overlap assertions.
- `Path.relative_to(R.ROOT)` raised for run roots outside the repository; replaced by
  `provenance.relpath_str()`.
- CUDA non-determinism (~4e-7 at epoch 1) — `cudnn.deterministic` alone is insufficient; added
  `torch.use_deterministic_algorithms(True, warn_only=False)` and
  `CUBLAS_WORKSPACE_CONFIG=:4096:8`.
- Three predicted-ROI tests failed on a clean checkout: fixtures built 64×64 maps while the
  function contract (and every production caller) uses the 512-space map, so `512 // 64 = 8`
  pushed blobs outside the content region. Implementation correct; fixtures repaired to 512×512.

---

## 7. Status matrix

Five states, deliberately orthogonal. "Implementation complete" says nothing about whether the
science is supported.

| Area | Implementation complete | Technical verification | Scientific design supported | Future evidence pending | Unresolved defect |
|---|---|---|---|---|---|
| **Stage 1** Literature | Yes | Yes — 3 citations corrected, 3 verified | Yes | — | — |
| **Stage 2** Hypotheses | **Partial** — H1–H7 exist only in this audit | Yes | Yes, but Gap 3 must stay narrow | Manuscript integration of H1–H7 | H1–H7 not in any citable artifact |
| **Stage 3** Datasets | Yes | Yes — 8,441 = 5,832+808+1,683+118 | Yes | — | — |
| **Stage 4** Architecture | Yes | Yes — 264 tests, drift guard | Yes | — | — |
| **Stage 4** Lite identity | Yes | Yes — 272,601 reproduced | Yes | — | — |
| **Stage 5** Historical results | Yes | Yes — traced to artifacts | Descriptive only | Prospective confirmation | In-sample / nested-partition caveat |
| **FULL Phase A** pipeline | Yes — all six producers | Yes — 24/24 synthetic | **Partial** — backbone not OOF | Real 3-seed execution | Backbone-OOF absent by design |
| **Controlled 24 cells** | Prepared | Yes | Yes | **0/24 executed** | All `NOT_ESTABLISHED` |
| **C1 attribution** | Frozen (RC3/RC4) | Yes | Yes | **0/6 runs** | RC3 self-digest defect; RC4 trust root unprovisioned |

---

## 8. Verification log

Interpreter: `.\.venv\Scripts\python.exe` — Python 3.11.9, torch 2.6.0+cu124,
RTX 3060 Ti (8,6), CUDA available, 7.43 / 8.59 GB free.

| Suite | Command | Result |
|---|---|---|
| FULL pipeline | `pytest tests/test_full_pipeline.py -q` | **24 passed** |
| Phase-25 drift guard | `pytest tests/test_phase25_architecture_drift.py -q` | **12 passed** |
| Lite | `pytest tests/test_ra_medfilm_barr_lite.py tests/test_lite_evaluation.py -q` | **17 passed** |
| Stage 6 | `pytest tests/test_stage6_baselines.py tests/test_stage6_integration.py -q` | **47 passed** |
| External / manuscript evidence | `pytest tests/test_c1_external_stress.py tests/test_c1_external_evidence.py tests/test_c1_external_final_corrections.py -q` | **106 passed** |
| Dataset + ROI | `pytest tests/test_kub_dataset.py tests/test_manifest_guard.py tests/test_oracle_roi.py tests/test_predicted_roi.py tests/test_phase13_manifest_provenance_binding.py tests/test_h3_size_adaptive_sigma.py -q` | **58 passed** |
| | | **264 passed, 0 failed** |

Also run: `py_compile` and import checks on `src/research/stage6/end_to_end.py`,
`src/models/barr/`, both FULL stages and `orchestrator`/`inference` — all clean; the
`TapRecorder` public alias resolves to `_TapRecorder`. Three-seed `dry-run` reports
`FULL_FAMILY_CHAIN_VERIFIED` + `ALL_INFERENCE_BRANCHES_VERIFIED` for 42, 123 and 3407.

**Revision 1's test claims re-measured:** "106/106 manuscript/external" — **correct**.
"13/13 Lite unit tests" — **correct for `test_ra_medfilm_barr_lite.py` alone** (17 including
`test_lite_evaluation.py`). "73/73 Stage 6 baseline and integration" — **wrong; measured 47**
(36 + 11).

No research training was executed. No protected evaluation data was read.

---

## 9. Files changed in this revision

**New**
- `src/models/barr/phase25_models.py` — single pure B_φ / S_ω definition + architecture fingerprint
- `tests/test_phase25_architecture_drift.py` — 12 drift tests against the canonical scripts

**Modified**
- `src/models/barr/__init__.py` — re-exports the shared definitions
- `src/research/full_pipeline/stages/router_stage.py`, `safety_stage.py` — import instead of copy
- `src/research/full_pipeline/stages/label_stage.py` — `oof_contract()` + honest docstring
- `tests/test_full_pipeline.py` — +4 tests (OOF contract, fold assignment, Lite identity ×2)
- `tests/test_predicted_roi.py` — fixtures repaired to the 512-space contract
- `docs/manuscript/RA_MEDFILM_BARR_MANUSCRIPT_DRAFT.md` — §2.3 prior art and §20 references

**Commits**
- `220108f` FULL three-seed orchestrator (Phase A)
- `67c2bb4` Stage 6 TapRecorder alias cleanup
- `ded7cca` single frozen Phase-25 B_φ/S_ω definition + drift guard
- `26b9c76` out-of-fold boundary stated exactly + Lite identity tests
- `d597715` predicted-ROI fixtures repaired to the 512-space contract
- `fa7cb99` manuscript prior-art identities corrected

Preserved untouched: `scripts/analysis/run_c1_campaign_launch.py`,
`reports/audits/c1_r4_execution/synthetic_chain_test.json`, `paper_doc/` render outputs.

---

## 10. Remaining defects and blockers

1. **Backbone is not out-of-fold** (§6.2). Documented and machine-flagged, not repaired. This is
   the most important scientific limitation of the FULL pipeline and blocks any claim of held-out
   router performance.
2. **H1–H7 are not a citable artifact.** They live only in this review. Either promote them into a
   frozen spec and the manuscript, or stop calling Stage 2 complete.
3. **24/24 controlled cells `MISSING`.** No comparative claim is available.
4. **C1: 0/6 runs.** RC3's gate refuses its own digest; RC4 verifies its own identity but its trust
   root is unprovisioned and no production CLI drives it to training.
5. **No production grant provider exists** for the FULL pipeline, so the real execution path has
   only ever been exercised up to the refusal.
6. **Real-data end-to-end has never run.** Loaders were probed (5,832 rows, image/mask existence);
   G → S on real TRAIN has not executed.
7. **`reports/` is gitignored**, so this document and the audit artifacts it cites are not
   version-controlled by default. They are evidence, not source.

---

## 11. Handoff

Stages 1–5 are **technically verified and internally consistent** after the corrections above.
They are **not** scientifically established: every quantitative claim in Stages 2 and 5 is either
historical, in-sample, or unexecuted, and the FULL pipeline's out-of-fold guarantee stops at the
refiner.

**Phase B (Lite training pipeline) is not cleared yet**, for three specific reasons rather than a
general lack of readiness:

1. The Lite identity is now unambiguous (`depthwise_compact`, 272,601, 94.36% reduction) and its
   frozen router/safety modules are shared and drift-guarded — so the *architecture* prerequisite
   for Phase B is met.
2. But Phase B would train a Lite student against a FULL teacher whose own ΔQ labels are
   backbone-in-sample (§6.2). Distilling from those labels propagates the bias rather than
   removing it, and would make the Lite result harder to interpret than the FULL one.
3. H7 as written ("≥50% reduction with intact graph contract") is already satisfied
   *statically*; what Phase B would add is an accuracy claim, and the controlled matrix that
   would adjudicate it is 0/24 executed.

Recommendation: resolve (2) first — either accept the bias explicitly in the Phase-B protocol and
state that Lite is evaluated under the same in-sample-backbone construction as FULL, or add a G
cross-fit before Phase B. That is a one-paragraph protocol decision, not new code.
