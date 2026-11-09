# Thesis Completion Gaps and Scientific Evidence Gaps — Honest Register

**Purpose:** state precisely what this supervisor package does **not** contain, so no missing item is mistaken for a delivered result.
**Basis:** direct inspection of `01_Thesis_and_Reports/`, `03_Experimental_Results/`, `06_Training_History/`, and the frozen repository audits.
**No new experiment, inference, training or TEST access was performed to produce this register.**

---

## 1. Is there a complete thesis? — **NO**

| Document | Structure | Scientific status | Verdict |
|---|---|---|---|
| `ReMedFiLM_Complete_Scientific_Report_V8.pdf` / `.docx` | 13 numbered sections + Appendix A; 33 figures, 14 tables | Latest **source-linked, verified** scientific report; canonical VAL808 registry | **A results-and-methodology report, NOT a thesis** |
| `UNVERIFIED_DRAFT_ReMedFiLM_Complete_Scientific_Report_V9.docx` | 13 sections + Appendix A; 34 headings, 24 tables | Newer draft from a separate workstream; **no independent V9 QA record** in the repository; its companion `V9/ReMedFiLM_V9_Dataset_Guide.md` quotes split counts (ISIC TRAIN 1,816 / VAL 259 / TEST 519) that **conflict** with `manifests/phase4_v3/` (2,556 / 357 / 735) | **Unverified draft — included for completeness only, explicitly renamed** |
| `RA_MedFiLM_BARR_Full_Supervisor_Report.docx` | 34 sections + 7 appendices, 140 headings, 52 tables, **includes a Literature Review (§3) and References / Appendix G** | **Structurally thesis-like but NOT current**: bound to `manuscript_final.md` under `MANUSCRIPT_ASSEMBLY_WITH_DESCRIPTIVE_PHASE39_TEST_ONLY`; quotes Phase39 **descriptive TEST1683** numbers (e.g. ISIC Dice 0.88693, n=735) from a historically consumed one-shot protocol, which are not re-verifiable here and are not the V8 canonical VAL808 evidence. No author / supervisor / institution fields, no declaration, no approval page, no dedicated Discussion chapter | **Cannot be submitted as the verified thesis** |
| `manuscript_final_SOURCE.md` | Frozen manuscript narrative | Source for the older supervisor report; Phase39 descriptive lineage | Supporting material only |

### 1.1 Sections missing from the latest verified report (V8)

| Missing thesis component | Evidence of absence |
|---|---|
| **Related Work / Literature Review** | V8 §1 is "Overview and contributions"; no dedicated literature survey, no citation apparatus |
| **References / Bibliography** | No reference list heading in V8's 34 headings; `V8_REPORT_CONTENT_MANIFEST.json` lists 13 sections + Appendix A only |
| **Dedicated Discussion chapter** | §13 merges "Conclusions, limitations and next experiments"; no separate discussion of interpretation, generalisability, or relation to prior work |
| **Formal standalone Introduction** | §1 "Overview and contributions" substitutes; no problem statement / motivation / aims / hypotheses chapter |
| **Standalone Experimental Setup chapter** | §3 covers datasets, splits and metric definitions, but there is no explicit hardware/software environment, hyperparameter, seed, or training-protocol chapter |
| **Thesis front matter** | No title page with author / supervisor / institution / submission date, no abstract, no declaration of originality, no acknowledgements, no approval/signature page, no list of publications |
| **Ethics / data-use determination** | `FINAL_DATASET_PERMISSION_AND_EXECUTION_DECISION.md` records `HUMAN_DETERMINATION_REQUIRED` — four licences are verified, but no written institutional determination exists |
| **Pre-registered statistical analysis plan** | Bootstrap CIs exist per-result, but no prospective SAP with multiplicity control; Phase 28 contrasts are explicitly `DESCRIPTIVE_NO_POST_HOC_CORRECTION` |

### 1.2 Missing V8 Appendix A references

V8 Appendix A names deliverables that **do not exist in the repository**:

- `V8_FINAL_SCIENTIFIC_QA.md`
- `V8_PUBLICATION_READINESS.md`
- `V7_TO_V8_CORRECTIONS.md`
- `v8_build/v8_qa.py`

A repository-wide filename search returned no match for any of them. Note that separately named artifacts `REMEDFILM_FINAL_SCIENTIFIC_QA.md` and `REMEDFILM_FINAL_QA_CHECKS.json` **do** exist and are shipped; they are not the same files.

> **Therefore:** a "full thesis report" **cannot be supplied as a completed, scientifically verified result** in this package. What is supplied is the verified V8 scientific report, an explicitly labelled unverified V9 draft, the older thesis-like (but scientifically stale) supervisor report, and the manuscript source — plus this register of what a thesis would still require.

---

## 2. Headline metric reconciliation (resolved — use one value only)

| Value | Status | Authority |
|---|---|---|
| **`0.8372896860016156`** → **`0.837290`** | **CANONICAL** ReMedFiLM FULL VAL808 macro Dice | `REMEDFILM_V8_RESULTS_REGISTRY.json`, `REMEDFILM_FULL_VAL808_METRICS.csv`, `reports/figures/phase27_preservation/masks/` re-score |
| `0.8350797177681444` → `0.835080` | **CANONICAL** GlobalMedFiLM backbone comparator (not a competing FULL value) | same |
| `+0.002209968233471182` | **CANONICAL** paired ΔDice, bootstrap 95 % CI `[+0.001147693051341143, +0.0032920500180402866]` | same |
| **`0.837862`** | **REJECTED — `REPORTING_INCONSISTENCY`**; mean of three numbers hard-coded into V5/V6/V7 generators. No checkpoint, configuration, frozen artifact or reproducible saved-mask policy supports it | `REMEDFILM_FULL_RESULT_RECONCILIATION.json` / `.md`, `REMEDFILM_V8_RESULT_RECONCILIATION.md` |

Seed 42 from the frozen archive (`0.837289105`) agrees with the saved-mask re-score to `5.81×10⁻⁷`. A separate frozen record (`reports/audits/phase29_val808_seedwise_metrics.json`) gives a different descriptive triplet (mean `0.837954`) with a different accepted-case count; it is descriptive component-initialisation stability, **not** three independent full training runs, and all three seeds share one pre-trained backbone.

**GlobalMedFiLM is the backbone/comparator only.** Backbone-only predictions must never be relabelled as ReMedFiLM FULL predictions.

---

## 3. Scientific evidence gaps (cannot be supplied as completed results)

| # | Gap | Exact status | Consequence |
|---|---|---|---|
| G-01 | **HAM10000 quantitative skin-lesion segmentation benchmark** | `EXTERNAL_SKIN_DATASET_AVAILABLE__SEGMENTATION_EVALUATION_NOT_ESTABLISHED`; 0 / 10,015 rows analysed; masks have no provenance; no saved FULL predictions | No HAM10000 Dice/IoU/Precision/Recall/HD95/paired difference; no representative HAM10000 panels. See `05_Datasets/HAM10000_AUDIT_REPORT.md` |
| G-02 | **C1 matched-arm FiLM causal experiment** | C1 / C2 / C3 all `NOT_ESTABLISHED`; preflight passes but gate refuses; approval, signatory and key custody PENDING; RC4 trust root `UNPROVISIONED`; no production CLI drives it to training | No causal FiLM benefit estimate. `DECISION_R` is an unselected option with zero implementation references |
| G-03 | **Phase 36 v1.22 execution / Phase 37** | `ELIGIBLE_NOT_STARTED` (never executed); Phase 37 `NOT_STARTED` | No new controlled results |
| G-04 | **Stage-6 eight-model×seed matrix** | 24 cells **ALL MISSING**; `stage6_eight_model.py baseline-run` has no `--device`/`--execute`; `baseline_real.py` is a library (`python -m` is a silent no-op) | `NOT_ESTABLISHED`; historical six-model comparison is descriptive, not protocol-faithful |
| G-05 | **Lite real chain** | `lite_chain.py` synthetic-only; real chain **BLOCKED** on cross-fitted OOF labels | No real lite end-to-end result |
| G-06 | **OOF boundary defect** | Refiner/router/safety OOF = TRUE, **backbone OOF = FALSE** (`label_stage.oof_contract()`, deliberately not repaired) | ΔQ for the backbone is in-sample; harm rates are optimistic |
| G-07 | **Online deployable inference** | `RAMedFiLMBARR.forward_inference` requires pre-computed cached OOF inputs (`router_features_202`, `oof_refined_crop_prob`, `safety_post_features_16`); it is an **offline validation replay harness**, not a deployable online pipeline | No end-to-end online inference demo; recorded as V9 audit ISS-01 |
| G-08 | **Conditional compute population mismatch** | `32.4379` GMACs derives from `ROUTER_HOLDOUT_875` activation `240/875 = 27.43 %`, whereas VAL808 activation is `279/808 = 34.53 %` (→ ≈`32.667` GMACs) | Analytical and empirical populations must be tagged separately; V9 audit ISS-02 |
| G-09 | **External generalisation failures** | Stones 14/14 stone-free false positives in **both** arms (specificity 0.0); BrEaST **patient-level independence NOT verifiable**; CVC sequence clustering required | No claim of robust external generalisation |
| G-10 | **No jointly trained FULL model** | Four components trained sequentially against frozen upstreams and assembled for inference; `06_Training_History/` contains **5 separate genuine epoch histories** (G, R_psi, B_phi, S_omega, F1), no joint curve | A single "FULL learning curve" would be fictitious and is deliberately absent |
| G-11 | **KUB full-field refinement** | **0 of 103** VAL808 full-field KUB cases were ever ACCEPTED by the router | No full-field KUB accepted-refinement example exists; gallery KUB rows are ROI patches |
| G-12 | **EXT-03 baseline protocol** | v1.0 (15/15) adjudicated under **ALL REDUCED PROTOCOL** — never protocol-faithful; v1.1 superseded, v1.2 verified | Historical six-model numbers are descriptive context, not a confirmed Pareto frontier |
| G-13 | **Phase-28 `A8_vs_A7`** | Mean `+1.5717229e-05`, 95 % CI `[-1.4313785e-05, +5.1010811e-05]` — **includes zero** | Safety-gate Dice benefit is INCONCLUSIVE |
| G-14 | **Phase-28 evidence uniformity** | Hybrid: A0–A8 replayed/analysis-only; R1–R3 + F1 from **18 historically trained** runs (15 router folds + 3 F1 folds); all in-sample on ROUTER_DEV | Do not claim "no new training" for the whole 13-arm matrix; not a causal ablation |
| G-15 | **TEST1683 / Phase 39** | Protected; one-shot protocol historically consumed in Phase 39; **not reopened** in this package | No new TEST numbers. The older thesis-like report's Phase39 descriptive TEST values are stale lineage, not current headline evidence |
| G-16 | **V9 verification** | Newer V9 draft has no QA record; `V9_Dataset_Guide.md` split counts conflict with canonical manifests | V8 remains numeric authority; V9 is labelled `UNVERIFIED_DRAFT_` |
| G-17 | **Prediction-mask regeneration from a clean clone** | `reports/figures/phase27_preservation/masks/` (1,616 PNGs) is **not git-tracked** | Figures shipped here are genuine, but regenerating them from a fresh repository clone requires that local cache; `build_readme_figures.py` aborts clearly if it is absent |
| G-18 | **AS-08 / GlobalMedFiLM checkpoint** | AS-08 unresolved; the GlobalMedFiLM checkpoint has **zero** router/safety tensors | Do not treat that checkpoint as a FULL-model checkpoint |
| G-19 | **Human governance** | Institutional ethics/data-use determination, explicit `DECISION_I`/`DECISION_R` choice, reviewed execution release all PENDING; `configs/c1_operator/approval.json` and `time_status.json` are agent-generated falsehoods (`MUST_NOT_BE_REUSED`) | `C1_EXECUTION_BLOCKED__HUMAN_AUTHORIZATION_ACTION_REQUIRED` |

---

## 4. Material explicitly NOT supplied, by request category

| Requested | Supplied? | Why |
|---|---|---|
| Full thesis report | **NO (gap)** | §1 — no complete, current, verified thesis exists |
| Proposed FULL methodology + architecture | **YES** | `02_Methodology_and_Architecture/`, V8 §2, `07_Figures/methodology/` |
| Internal + external results with Dice/IoU/Precision/Recall/HD95/paired differences + limitations | **YES (VAL808 + EXTERNAL884)** | `03_Experimental_Results/`; limitations in §3 above |
| Complete Phase-28 ablation code + frozen results | **YES** | `04_Ablation_Phase28/` (with hybrid-evidence caveat) |
| Updated dataset guide with official links, splits, licences | **YES — 8 datasets** | `05_Datasets/DATASET_GUIDE.md` |
| HAM10000 external skin evaluation | **NO (gap)** | Inventoried + audited + documented; no valid masks, no saved FULL predictions |
| HAM10000 representative segmentation images | **NO — deliberately refused** | Would require fabricating masks and/or predictions |
| Epoch-wise training records for all four components | **YES — separate histories** | `06_Training_History/`; no fictitious joint curve |
| Real prediction gallery + methodology + analysis figures | **YES** | `07_Figures/` (26 images; genuine saved masks only) |
| Metric reconciliation | **YES** | §2 above and `03_Experimental_Results/reconciliation/` |
| One validated ZIP with all references checked | **YES** | `08_Verification/VERIFICATION_REPORT.md`, `SUBMISSION_MANIFEST.csv` |
