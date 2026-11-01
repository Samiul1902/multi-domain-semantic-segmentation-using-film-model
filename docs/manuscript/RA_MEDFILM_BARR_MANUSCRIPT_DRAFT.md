# Task-Conditioned Feature-Wise Linear Modulation and Budget-Aware Regional Refinement in Multi-Domain Medical Image Segmentation (RA-MedFiLM-BARR)

**Authors:** RA-MedFiLM-BARR Scientific Consortium  
**Governance & Date:** October 30, 2026 | Canonical Manifest v3 Governance  
**Operational Status:** PRE-EXPERIMENTAL RIGOROUS PROTOCOL & METHODOLOGICAL SPECIFICATION  
**Target Venue:** IEEE Transactions on Medical Imaging (TMI) / Medical Image Analysis (MedIA)  

---

## Abstract
The proposed method in this study is **RA-MedFiLM-BARR (FULL)**: a task-conditioned GlobalMedFiLM segmentation backbone followed by benefit-based routing, regional refinement, post-refinement acceptance, and deterministic output fusion. GlobalMedFiLM without BARR is an internal ablation reference, not the proposed final model. We report three distinct evidence tracks: (i) the frozen but not yet executed six-run C1 identity-FiLM attribution study; (ii) completed, development-selected BARR component and full-assembly analyses; and (iii) a prepared, protocol-matched comparison of the complete method against five external architecture baselines.

Existing full-system measurements are conditional on a single frozen seed-42 GlobalMedFiLM checkpoint. Phase-29 varies downstream BARR components across seeds 42, 123, and 3407 but does not vary the global backbone; these are downstream reproducibility observations, not independent end-to-end seed replicates. The existing external stress test is retrospective, and the 14/14 stone-free foreground-prediction failure is retained. Historical baseline scores are single-run, development-selected, and protocol-incomparable. The new primary full-system-versus-five-baseline matrix contains 18 model-seed cells; all remain missing, so controlled superiority is **NOT_ESTABLISHED**. No clinical readiness or prospective external validation is claimed.

> **Review-draft status.** Not ready for submission. The primary method is RA-MedFiLM-BARR (FULL). Pending: six real C1 runs, three compatible end-to-end full-model seed bundles, five matched external baselines across three seeds (18 cells total), and independent external validation. Existing Phase-29 results do not supply independent end-to-end full-model seeds. Literature citations are not independently re-verified in this draft.

---

## 1. Introduction & Clinical Motivation
Multi-domain medical image analysis holds tremendous potential for clinical decision support, triage, and robotic surgery. However, in heterogeneous healthcare environments, imaging modalities vary drastically in physical acquisition principles, signal-to-noise ratios, spatial resolution, and lesion morphology. Conventional practices either train distinct models for each anatomical domain—multiplying operational maintenance overhead and preventing shared representation learning—or train monolithic architectures that suffer from catastrophic interference and negative transfer, where dominant gradients from high-contrast modalities degrade performance on subtle, tiny objects.

To overcome these structural limitations, two paradigms are required:
1. *Adaptive Task Conditioning*: Conditioning intermediate neural activations upon domain priors dynamically without altering network topology.
2. *Selective Regional Refinement*: Allocating dense high-resolution spatial compute only to complex, ambiguous, or sub-centimeter anatomical regions while processing standard background structures via low-cost global passes.

The RA-MedFiLM-BARR framework formalizes this multi-domain paradigm. In this paper, we document the system architecture, mathematical formulations, data provenance safeguards, and the pre-specified (not yet executed) C1 attribution protocol.

---

## 2. Related Work & Research Gaps

### 2.1 Multi-Domain Medical Image Segmentation
Unified medical segmentation networks typically rely on multi-head decoders or separate routing paths (Ronneberger et al., 2015; Isensee et al., 2021). While frameworks such as nnU-Net optimize single-domain hyperparameter heuristics, joint multi-modality learning often introduces gradient conflicts. Recent efforts explore unified backbones, but may not account for (not surveyed systematically here) multi-center data contamination or subtle patient overlap across imaging series.

### 2.2 Feature-Wise Linear Modulation (FiLM)
Feature-wise Linear Modulation (Perez et al., 2018) was originally developed for visual reasoning to dynamically manipulate convolutional feature representations conditioned on linguistic or categorical embeddings. In medical vision, modulation layers have been utilized for demographic or disease metadata. However, a systematic literature review was not performed for this draft; a concern is that reported gains may stem from additional trainable projection parameters or altered optimization dynamics rather than true task modulation.

### 2.3 Regional Refinement & Selective Routing
Cropping-based refinement is common in segmentation systems. Interactive segmentation with image-specific fine-tuning (Wang et al., 2018) is related but differs from the present automatic batch-inference setting. Fixed cascades that run every crop unconditionally incur the refiner cost on all cases. Dynamic routing (Teerapittayanon et al., 2016) introduces early exits or conditional execution; whether a cost-penalised benefit router has been combined with regional refinement in medical segmentation was not established by a systematic search here.

### 2.4 Research Gaps Addressed
1. *Causal Attribution*: Existing FiLM evaluations fail to test an unconditioned identity control with identical seed, initialization, and optimizer states.
2. *Data Leakage Governance*: Multi-domain benchmarks frequently include inadvertent duplicate scans or linked patient records across train/validation/test splits.
3. *Budget-Aware Spatial Allocation*: Need for explicit compute-aware router-refiner policies that bound additional cost while recovering tiny object boundaries.

---

## 3. Core Contributions: Status & Taxonomy

To ensure scientific transparency, every research contribution is explicitly categorized:
- **Primary proposed method — RA-MedFiLM-BARR (FULL)**:
  - *Identity*: the executable system is GlobalMedFiLM `G` → benefit router `B_\phi` → regional refiner `R_\psi` when routed → post-refinement acceptance `S_\omega` → exact regional replacement fusion; the output is a full-system prediction, not a C1-T backbone score.
  - *Status*: existing full-system results are conditional on the fixed seed-42 `G`; protocol-matched end-to-end C3 comparisons against five external baselines are **NOT_ESTABLISHED** (0/18 model-seed cells).
- **Internal ablation reference — GlobalMedFiLM without BARR**:
  - *Role*: global segmentation backbone and internal comparator for C1/C2 component studies; not the final proposed model and not the headline external-baseline comparator.
- **Contribution C1 (FiLM Task Attribution — *Proposed Protocol*)**:
  - *Status*: Methodologically frozen in release `C1_FILM_ATTRIBUTION_V1_LAUNCH_RC3`; empirical 6-run execution pending (`NOT_ESTABLISHED`).
  - *Scope*: Causal architectural intervention isolating the mathematical effect of task-conditioned scale/shift affine vectors against an exact zero-modulation control. It does *not* assert broad clinical efficacy until prospective evaluation is authorized.
- **Contribution C2 (Budget-Aware Regional Refinement — *Exploratory Development*)**:
  - *Status*: Descriptively reported on historical development partitions (`HISTORICAL_DESCRIPTIVE_RESULT`).
  - *Scope*: Demonstrates that selective routing plus learned post-safety filtering ($S_\omega$) reduces the all-population harm rate from 42.67% ($A1$, unconditional refinement) to 7.87% ($A8$), in-sample on the 4,957-case development population. The router accounts for 2,115 → 412 harmful cases and $S_\omega$ for a further 412 → 390; the reduction is therefore attributable mainly to routing, not to the safety filter alone.
- **Contribution C3 (Fair Multi-Domain Benchmarking — *Exploratory Retrospective*)**:
  - *Status*: Five baseline architectures plus GlobalMedFiLM are reported as single-run results on historical splits (`PROTOCOL_INCOMPARABLE`). The full-system-versus-five-baseline matrix uses seeds 42, 123, and 3407 and is prepared but has 18 missing cells.
  - *Scope*: The primary comparison is RA-MedFiLM-BARR (FULL) minus each external baseline on matched eligible cases; GlobalMedFiLM remains an internal reference.
- **External stress test (not a contribution, *Descriptive Only*)**: A retrospective 884-case stress test (CVC-ClinicDB n = 612, BrEaST-Lesions-USG n = 252, Stones_where_are_you test split n = 20) was executed with both the Global MedFiLM checkpoint and the full frozen BARR assembly. HAM10000 was excluded before inference because the available masks have no documented provenance. This is not an external validation cohort; see §13.1.

---

## 4. Mathematical Formulation & Architecture

### 4.1 Global Backbone and Actual Implemented FiLM Equation
Let $X \in \mathbb{R}^{B \times C_{\text{in}} \times H \times W}$ denote the input image batch, and let $t \in \{0, 1, 2, 3\}$ denote the categorical domain index corresponding to ISIC (0), BUSI (1), KVASIR (2) and KUB (3) respectively. The task embedding module maps $t$ into a learned embedding vector $e_t = E(t) \in \mathbb{R}^{d_e}$ ($d_e = 32$).

For a given convolutional feature map $F_l \in \mathbb{R}^{B \times C_l \times H_l \times W_l}$ at network site $l \in \{\text{bridge}, \text{decoder4}, \text{decoder3}, \text{decoder2}, \text{decoder1}\}$, the FiLM generator projects $e_t$ through an MLP to produce raw parameters, which are bounded via a hyperbolic tangent activation:
$$\tilde{\gamma}_l, \tilde{\beta}_l = \text{Linear}(\text{SiLU}(\text{Linear}(e_t)))$$
$$\gamma_l = \tanh(\tilde{\gamma}_l), \quad \beta_l = \tanh(\tilde{\beta}_l)$$
The modulated feature tensor $\hat{F}_l$ is computed using the exact implemented formulation:
$$\hat{F}_l = (1 + \gamma_l) \odot F_l + \beta_l$$
where $\gamma_l, \beta_l \in \mathbb{R}^{B \times C_l \times 1 \times 1}$ are broadcast across spatial dimensions $H_l \times W_l$. Bounding the modulation by $\tanh(\cdot)$ guarantees numerical stability during early training epochs.

### 4.2 Matched Identity Control ($C1\text{-}C$) & Parameter Accounting
To isolate the causal contribution of task conditioning, the control model ($C1\text{-}C$) is built as an exact structural duplicate of $C1\text{-}T$ before optimization begins:
- **Treatment Arm ($C1\text{-}T$)**: Total parameters = 3,523,001; Trainable parameters = **3,523,001** (Backbone: 3,432,233; Conditioning: 90,768).
- **Identity Control ($C1\text{-}C$)**: Total parameters = 3,523,001; Trainable parameters = **3,432,233** (Backbone: 3,432,233; Frozen Conditioning: 90,768).
In $C1\text{-}C$, the conditioning weights are zero-initialized and frozen ($\gamma_l \equiv 0, \beta_l \equiv 0$), reducing modulation strictly to the identity map $\hat{F}_l \equiv F_l$. The 90,768 non-trainable conditioning parameters are excluded from the AdamW optimizer parameter groups.

---

## 5. Budget-Aware Regional Refinement (BARR) Formulation

### 5.1 Region Proposal & Ambiguity Detection
The global stage produces a coarse probability map $P_{\text{global}} \in [0, 1]^{B \times 1 \times H \times W}$. The frozen implementation (`src/models/barr/ra_medfilm_barr.py`) proposes **one** region per image: the foreground set $\{P_{\text{global}} \ge 0.30\}$ is enclosed in a single bounding box, which is expanded by a centre-preserving factor of 1.5 and clipped to the image. If the set is empty the state is `FORCED_SKIP` and $P_{\text{global}}$ is returned. (An earlier draft described an ambiguity map and multiple candidate boxes; neither is implemented and both were removed.)

### 5.2 Benefit routing and cost-aware decision
$B_\phi$ receives a 202-dimensional ground-truth-free feature vector derived from the global output and the ROI, together with the task embedding, and predicts the expected Dice benefit $\hat{\Delta}$ of refinement. With action cost $C = 1{,}051{,}648/10{,}270{,}749$ and $\lambda = 1/4$, the utility is
$$U = \hat{\Delta} - \lambda C,$$
and the crop is executed iff $U \ge \tau_{C8}$, where $\tau_{C8} = \tau_{C7} - \lambda C$ and $\tau_{C7} \approx 0.0012398$ (frozen, calibrated on ROUTER_DEVELOPMENT under a 25% target routing fraction). The "budget" is this calibrated cost-penalised threshold; the implementation has no per-image FLOP-sum constraint. Non-executed cases are `SKIP_GLOBAL` and return $P_{\text{global}}$.

### 5.2.1 Refinement, fusion and safety decision
$R_\psi$ produces a $256\times256$ refined crop that is resized to the ROI and **replaces** $P_{\text{global}}$ inside the ROI (no alpha blending). $S_\omega$ takes 16 numeric post-refinement features plus a one-hot task vector and accepts iff $\sigma(\text{logit}) \ge 0.50$; on rejection $P_{\text{global}}$ is returned (`EXECUTE_THEN_REJECT`). The final mask is $P \ge 0.50$. The wrapper adds no trainable parameters. States: `FORCED_SKIP`, `SKIP_GLOBAL`, `EXECUTE_THEN_ACCEPT`, `EXECUTE_THEN_REJECT`.

### 5.3 Parameter accounting
The frozen system comprises four components with verified parameter counts (`reports/audits/phase36_robustness_scientific_result_v1_23.json`, strict load, zero missing or unexpected keys):

| Component | Symbol | Parameters |
| :--- | :--- | ---: |
| Global FiLM segmentation network | $G$ | 3,523,001 |
| Regional refiner | $R_\psi$ | 1,276,401 |
| Benefit router | $B_\phi$ | 36,801 |
| Post-safety filter | $S_\omega$ | 1,217 |
| **Total** | | **4,837,420** |

The total is 4.84M parameters, not the 4.80M stated in earlier project material. $R_\psi$ accounts for about 97% (1,276,401 of 1,314,419) of the increase over the global network, so BARR's cost is dominated by the refiner rather than by routing or safety.

---

## 6. Dataset Cohorts & Leakage-Safe Manifest Governance (v3)

### 6.1 Multi-Domain Clinical Imaging Modalities
The benchmark integrates four diverse clinical datasets:
1. **KUB-StoneX**: Kidney-Ureter-Bladder abdominal digital radiographs for nephrolithiasis and ureteral calculi segmentation (high resolution, low contrast, tiny targets).
2. **ISIC 2018**: Dermoscopic surface microscopy images for melanoma and skin lesion boundary demarcation.
3. **BUSI**: Breast ultrasound scans categorized across normal, benign, and malignant lesions with high speckle noise.
4. **Kvasir-SEG**: Video endoscopic frames for colorectal polyp segmentation with specular reflections.

### 6.2 Manifest v3 Partitioning and Validation Consumption
During Phase 05 audit remediation, subtle duplicate scans and test-linked patient records were discovered in legacy manifests. We instituted **Manifest v3 Governance**, enforcing strict patient-level isolation:
- **TRAIN**: 5,832 samples (ISIC: 2556, BUSI: 602, KVASIR: 696, KUB: 1978)
- **VAL (Development)**: 808 samples (ISIC: 357, BUSI: 84, KVASIR: 87, KUB: 280)
- **TEST (locked, never evaluated; re-partitioned from historical repositories, not prospectively acquired)**: 1,683 samples (ISIC: 742, BUSI: 174, KVASIR: 181, KUB: 586)
- **QUARANTINED**: 118 cases excluded from all splits due to perceptual hash similarity ($d \le 2$) or linked patient identifiers.
- **TOTAL REGISTRY**: 8,441 records.

**Critical Methodological Disclosures**:
1. *Validation Consumption*: The 808-case validation split (`VAL808`) was actively consumed for hyperparameter selection and early stopping checkpoint identification.
2. *Historical TEST Split Status*: The 1,683-case TEST partition is cryptographically locked under `test_test_lock.py`. However, because it was derived by re-partitioning historical repositories rather than acquired prospectively from distinct clinical centers, it represents a held-out split rather than an untouched independent external validation cohort.

---

## 7. Experimental Setup & Launch Preflight Verification

### 7.1 Hardware Platform & Profiling
Experiments are standardized on an NVIDIA GeForce RTX 3060 Ti GPU (8GB VRAM) under CUDA 12.4 and PyTorch 2.6.0. Benchmarking at $512 \times 512$ resolution with AMP mixed-precision demonstrates:
- Training step latency: $128.90 \text{ ms}$ (Batch size = 4)
- Validation step latency: $83.17 \text{ ms}$ (Batch size = 8)
- Compute time per 100-epoch run: $6.29 \text{ hours}$ (Central estimate), derived as $37.72 / 6$ under equal workloads across the six runs
- Full 6-run campaign duration: $37.72 \text{ hours}$ (Nominal) to $42.71 \text{ hours}$ (Conservative), i.e. $6.29$ to $7.12 \text{ hours}$ per run; these are planning estimates, not measurements.

### 7.2 Cryptographic Release Invariant (RC3)
The launch framework is governed by frozen release `C1_FILM_ATTRIBUTION_V1_LAUNCH_RC3`, bearing SHA-256 digest:
`54d1273a53db7dae58118a4bb69c2a96ba2e474a72512a9dccb4c98c9513549f`
Release verification: all RC1–RC4 release tests pass except one environment-dependent RC2 test (`test_default_production_store_is_absent`), which fails because the default production trust store is present on the host (see §18.3); it is reported rather than suppressed.

---

## 8. Prospective 6-Run C1 Experimental Protocol

To eliminate p-hacking, selection bias, and seed cherry-picking, the C1 evaluation protocol is immutably defined prior to execution:
- **Treatment Arm ($C1\text{-}T$)**: Task-conditioned FiLM U-Net trained on Manifest v3 across seeds $\{42, 123, 3407\}$.
- **Control Arm ($C1\text{-}C$)**: Matched unconditioned U-Net trained on identical splits across identical seeds $\{42, 123, 3407\}$.
- **Hyperparameter Invariants**: AdamW optimizer ($\text{lr} = 10^{-4}$, weight decay $= 10^{-4}$), Combined BCE + Soft Dice loss, cosine annealing schedule over 100 epochs, early stopping patience $= 15$ based on validation EqualDomainMacroDice.

---

## 9. Evaluation Metrics & Statistical Testing Framework

### 9.1 Multi-Domain Segmentation Metrics
In accordance with international consensus guidelines (Maier-Hein et al., Nature Methods 2024), segmentation accuracy is evaluated across complementary spatial and boundary metrics:
- **Sørensen-Dice Coefficient (DSC)**: $\text{DSC} = \frac{2 |Y \cap \hat{Y}|}{|Y| + |\hat{Y}|}$
- **Intersection over Union (IoU / Jaccard)**: $\text{IoU} = \frac{|Y \cap \hat{Y}|}{|Y \cup \hat{Y}|}$
- **Normalized Surface Distance (NSD)**: Surface boundary agreement within a tolerance $\tau$. The protocol target is $\tau = 1.0\text{ mm}$ where physical pixel spacing is available. **No external cohort in §13.1 ships pixel spacing**, so external NSD is computed at $\tau = 2$ pixels and reported in pixels; it is not comparable to an NSD computed in millimetres.
- **Hausdorff Distance 95th Percentile ($HD_{95}$)**: Extreme boundary outlier distance, in millimetres when spacing is known and in **pixels** otherwise.
- **Average Symmetric Surface Distance (ASSD)**: Mean of the symmetric surface-distance set, same unit rule as $HD_{95}$.
- **Region size error**: $(|\hat{Y}| - |Y|)/|Y|$, reported alongside the counts so that over- and under-segmentation are distinguishable.

### 9.2 Statistical Hypothesis Testing
The primary endpoint is the difference in Equal-Domain Macro Dice:
$$\Delta_{\text{macro}} = \frac{1}{3}\sum_{s \in \{42,\,123,\,3407\}} \frac{1}{4} \sum_{d \in \{\text{KUB, ISIC, BUSI, KVASIR}\}} \left(\text{DSC}_{d}(C1\text{-}T_s) - \text{DSC}_{d}(C1\text{-}C_s)\right)$$

This is the frozen primary endpoint, `seed_average_of_paired_equal_domain_macro_Dice_T_minus_C_on_selected_VAL`: a seed-average over the three matched seeds of the paired, equal-domain macro-Dice difference between the task-conditioned arm and its exact structural control, evaluated on the selection-consumed VAL808 split.

Directional hypothesis, as frozen:
- **Null Hypothesis ($H_0$)**: $\Delta_{\text{macro}} \le 0$
- **Alternative Hypothesis ($H_1$)**: $\Delta_{\text{macro}} > 0$

**No confirmatory significance test is eligible, and none is reported.** A paired signed-rank test across cases is *not* the frozen procedure and cannot be substituted for it, for four independent reasons:

1. **The endpoint population is selection-consumed.** The epoch that supplies `best_records` is the epoch that won selection *on VAL808*, so a p-value computed on the same split is not calibrated; the selection event has already used the data.
2. **TEST cannot supply the endpoint.** The endpoint is defined on selected VAL, not TEST. TEST ($n = 1{,}683$) is protected and was not opened for any value in this work, so substituting it would both change the estimand and breach the governance boundary.
3. **A per-case signed-rank test does not estimate the endpoint.** The endpoint is a seed-average of a four-domain macro difference. Signed-rank over cases answers a different question, at a different unit of analysis, and its result would not be an estimate of $\Delta_{\text{macro}}$.
4. **The cluster structure is not exchangeable cases.** KUB validation samples group into 111 verified patient clusters, so case-level ranks would treat non-independent observations as independent.

The predeclared procedure is therefore the uncertainty statement, reported descriptively:

- **Predeclared Bootstrap Uncertainty**: Exactly 10,000 paired cluster bootstrap resamples ($B=10{,}000$) using the NumPy PCG64 PRNG initialized with frozen seed `20261027`, reporting two-sided 95% percentile confidence intervals. Patient-level clustering is enforced for KUB (280 validation samples grouped into 111 verified patient clusters); image-level sampling is maintained for ISIC, BUSI, and Kvasir-SEG where patient-level linkage is unprovided in open clinical sources.

Consequently the C1 result, when executed, will be reported as a point estimate of $\Delta_{\text{macro}}$ with its prespecified 95% bootstrap interval. It will not carry a p-value, and it will not be described as statistically significant.

---

## 10. Evidence Inventory Across C1, C2, and C3

Every empirical data point in this project is classified under a strict evidentiary hierarchy:
- `CONFIRMED_EXECUTED_RESULT`: Executed under Manifest v3 governance with full audit provenance.
- `HISTORICAL_DESCRIPTIVE_RESULT`: Legacy exploratory development; non-comparable to clean v3 benchmarks.
- `PROTOCOL_INCOMPARABLE`: Historical runs with mismatched loss formulations or pre-audit data splits.
- `SYNTHETIC_TEST_ONLY`: Computational contract verification on mock data structures.
- `NOT_ESTABLISHED`: Prospective experiments pending operational execution.
- `PARTIALLY_VERIFIED`: The computation is reproducible from a frozen artifact, but a required input (mask provenance, population identity) is undocumented. Reportable as a descriptive observation only.
- `UNSUPPORTED`: No stored record exists. Must not be quoted.

Applied to the external stress test (§13.1), all three analysed cohorts are `VERIFIED` at the level of image/mask pairing and identifier mapping. HAM10000 is excluded rather than downgraded: its masks cannot be attributed, so no computation against them would measure the model. The study as a whole is `DESCRIPTIVE_ONLY` and is not an external validation cohort.

A complete audit trail is preserved in `reports/tables/scientific_evidence_inventory_c1_c2_c3.csv`.

---

## 11. Results: Campaign 1 — FiLM Task Attribution (Prospective Shell)

*Note: Table cells are unpopulated pending operational execution under authorized institutional grant.*

| Model Arm | Seed | KUB DSC | ISIC DSC | BUSI DSC | KVASIR DSC | Macro DSC | Paired $\Delta$ | 95% Bootstrap CI | p-value |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **C1-T (FiLM)** | 42 | *Pending* | *Pending* | *Pending* | *Pending* | *Pending* | — | — | — |
| **C1-C (Control)**| 42 | *Pending* | *Pending* | *Pending* | *Pending* | *Pending* | — | — | — |
| **C1-T (FiLM)** | 123 | *Pending* | *Pending* | *Pending* | *Pending* | *Pending* | — | — | — |
| **C1-C (Control)**| 123 | *Pending* | *Pending* | *Pending* | *Pending* | *Pending* | — | — | — |
| **C1-T (FiLM)** | 3407 | *Pending* | *Pending* | *Pending* | *Pending* | *Pending* | — | — | — |
| **C1-C (Control)**| 3407 | *Pending* | *Pending* | *Pending* | *Pending* | *Pending* | — | — | — |
| **Pooled Mean** | — | *Pending* | *Pending* | *Pending* | *Pending* | *Pending* | *Pending* | [*Pending*] | *Pending* |

---

## 12. Results: Campaign 2 — BARR Regional Refinement & Routing (Historical Evidence)

Historical exploratory experiments (Phases 14, 26, 28, 30) evaluated selective regional refinement across 4,957 development cases:

| Arm ID | Architectural Specification | Cases Routed ($n_{\text{routed}}$) | Cases Accepted ($n_{\text{accepted}}$) | Pooled Mean True $\Delta\text{DSC}_{\text{routed}}$ | Cases Benefited ($\Delta > 0$) | Cases Harmed ($\Delta < 0$) | Conditional Harm Rate | All-Population Harm Rate ($/4,957$) | Evidence Class |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **A0** | Global pass only (no refinement) | 0 | 0 | 0.000000 | 0 | 0 | 0.00% | 0.00% | `ENDPOINT_BY_CONSTRUCTION` |
| **A1** | Unconditional refinement (all crops) | 4,957 | 4,890 | +0.001658 | 2,775 | 2,115 (strict) / 2,107 (tol) | 42.67% (2,115 / 4,957) | 42.67% (strict) / 42.51% (tol) | `ENDPOINT_BY_CONSTRUCTION` |
| **A6** | Utility-guided selection (no cost) | 1,239 | 1,239 | +0.007247 | 827 | 412 | 33.25% (412 / 1,239) | 8.31% (412 / 4,957) | `PRIOR_CANONICAL_EVIDENCE` |
| **A7** | Cost-aware utility: $U = \hat{\Delta} - \lambda C$ | 1,239 | 1,239 | +0.007247 | 827 | 412 | 33.25% (412 / 1,239) | 8.31% (412 / 4,957) | `PRIOR_CANONICAL_EVIDENCE` |
| **A8** | Full BARR: $A7$ + Post-Safety $S_\omega$ | 1,239 | 1,205 | +0.007516 | 815 | 390 | 32.37% (390 / 1,205) | 7.87% (390 / 4,957) | `PRIOR_CANONICAL_EVIDENCE` |

*Column note*: for $A8$ the "routed" count (1,239) is the number of candidates eligible under budget $K$; the "accepted" count (1,205) is the number actually executed after $S_\omega$ rejects 34. The frozen Phase 28 table records `n_routed = 1,205` for $A8$ using the post-safety convention. Both readings are of the same run.

### Key Findings:
- **Harm Denominators Reconciled**: Unconditional refinement ($A1$) harms **42.67%** of cases across the population (2,115 / 4,957). In full BARR ($A8$), exactly 390 cases among the 1,205 accepted cases experienced harm (a conditional harm rate of 32.37%). Evaluated across the entire population (intent-to-treat), $A8$ harm is **7.87%** (390 / 4,957).
- **Attribution Decomposition**: the $A1 \to A7$ step (adding the cost-aware router) accounts for 2,115 → 412 harmful cases; the $A7 \to A8$ step (adding $S_\omega$) accounts for 412 → 390, i.e. 22 cases. The system-level reduction of 1,725 cases is therefore attributable predominantly to routing. A reduced average harm rate is **not** evidence of zero harmful outcomes: 390 harmful refinements persist in $A8$.
- **In-Sample Caveat**: the 4,957 ROUTER_DEVELOPMENT rows are a subset of the 5,832 TRAIN samples. This table is in-sample development evidence, not held-out evidence.
- **Phase 30 Holdout Evidence Boundary**: Historical evaluation on the router holdout ($N=875$) demonstrated a macro Dice delta of $+0.001739$ (95% CI: $[+0.001117, +0.002405]$), confirming non-inferiority against the margin of $-0.005$. In accordance with supervisor adjudication, this result is classified under disclosed post-first-open source deviations and confirms protocol-specific non-inferiority, not clinical safety.

*Governance Disclaimer*: Classified as `HISTORICAL_DESCRIPTIVE_RESULT`.

### 12.1 Internal ablation hierarchy and what the existing arms identify

The progressive labels below are conceptual stages, not claims that every adjacent transition has a controlled causal estimate. All Phase-28 A-arms use the same historical seed-42 GlobalMedFiLM backbone and the 4,957-case `ROUTER_DEVELOPMENT` population (in-sample, a subset of TRAIN5832).

| Stage | Intended system | Existing evidence mapping | Identification status |
| :--- | :--- | :--- | :--- |
| P0 | Identity-FiLM control, no BARR | C1-C is the intended mechanism control | **NOT_ESTABLISHED**; frozen C1 runs are pending |
| P1 | Learned-FiLM GlobalMedFiLM, no BARR | Phase-21 GlobalMedFiLM; A0 is the global-only arm | Historical/internal reference only; A0 is not an identity-FiLM control |
| P2 | P1 + regional refiner, no selective routing | A1 always-refine | In-sample endpoint-by-construction; not a controlled C1 attribution |
| P3 | P1 + routing and regional refinement, without S_omega | A6 learned-gain routing; A7 adds the resource-cost term | Descriptive progression only; A1-to-A6/A7 changes routing and execution budget and is not an isolated component contrast |
| P4 | Full RA-MedFiLM-BARR with routing, refinement, safety and fusion | A8; A7-to-A8 is the prespecified matched safety-filter contrast | A7/A8 differ only by S_omega on the matched 4,957-case population and selected set; this identifies the descriptive safety-filter contrast, not end-to-end generalization |

A2-A5 are alternative routing comparators; R1-R3 and F1 are feature-set/model variants, not missing points in a single-factor P0-P4 progression. The frozen A7-versus-A8 contrast is the only one-factor matched contrast in the Phase-28 core map. The larger A1-to-A8 reduction in harm must not be attributed to the router alone or described as a sequence of independently identified component effects.

Phase 29 adds downstream component-seed variation for R_psi, B_phi, and S_omega, but all three seed outputs use the same seed-42 GlobalMedFiLM checkpoint. These are conditional BARR-stack reproducibility observations. They are not three independent end-to-end RA-MedFiLM-BARR seeds, and they cannot fill the new full-model C3 cells.

---

## 13. Results: Primary Full-System Benchmark and Historical Context

The primary proposed-method row is **RA-MedFiLM-BARR (FULL)**. Its controlled comparison against U-Net, U-Net++, Attention U-Net, DeepLabV3+, and Transformer/MiT-style U-Net is **NOT_ESTABLISHED**: all 18 cells (six models × three matched seeds) remain missing. GlobalMedFiLM is retained below only as an internal ablation reference. The following quantitative rows are historical, development-selected single-run context and are **PROTOCOL_INCOMPARABLE**; they are not the proposed-method result or a controlled leaderboard.

| Model / role | Backbone Class | Parameters | Best Epoch | Macro Domain Dice | 95% Bootstrap CI | Macro Domain IoU | ISIC Dice | BUSI Dice | KVASIR Dice | KUB Dice | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **RA-MedFiLM-BARR (FULL), primary proposed method** | Full G/R/B/S system | 4,837,420 component parameters | — | **NOT_ESTABLISHED** | — | — | — | — | — | 0/3 compatible full-system seeds; 18/18 matrix cells missing |
| DeepLabV3+ (historical external baseline) | `DeepLabV3Plus` | 40,347,041 | 57 | 0.8277 | [0.7707, 0.8761] | 0.7412 | 0.8853 | 0.8669 | 0.8197 | 0.7387 | `PROTOCOL_INCOMPARABLE` |
| Transformer/MiT-style U-Net (historical external baseline) | `TransformerMiTUNet` | 16,347,777 | 74 | 0.8224 | [0.7599, 0.8755] | 0.7366 | 0.8871 | 0.8640 | 0.8133 | 0.7252 | `PROTOCOL_INCOMPARABLE` |
| U-Net++ (historical external baseline) | `UNetPlusPlus` | 9,159,681 | 55 | 0.7920 | [0.7446, 0.8382] | 0.6910 | 0.8601 | 0.8163 | 0.7710 | 0.7207 | `PROTOCOL_INCOMPARABLE` |
| Attention U-Net (historical external baseline) | `AttentionUNet` | 7,851,285 | 64 | 0.7890 | [0.7288, 0.8447] | 0.6927 | 0.8617 | 0.8277 | 0.7710 | 0.6958 | `PROTOCOL_INCOMPARABLE` |
| U-Net (historical external baseline) | `UNet` | 7,763,041 | 74 | 0.7878 | [0.7381, 0.8375] | 0.6881 | 0.8553 | 0.8198 | 0.7552 | 0.7211 | `PROTOCOL_INCOMPARABLE` |
| GlobalMedFiLM (internal ablation reference; not the proposed method) | `GlobalMedFiLM` | 3,523,001 | 66 | 0.8351 | [0.7877, 0.8780] | 0.7448 | 0.8972 | 0.8588 | 0.8202 | 0.7641 | Historical internal reference; `PROTOCOL_INCOMPARABLE` |

### 13.1 External stress test (retrospective, n = 884, Global and BARR)

An earlier draft reported a four-case pilot at n = 1 per dataset, run under a non-canonical stretch-resize convention and including a HAM10000 row whose masks have no documented provenance. That pilot is withdrawn in full. What follows was produced by a design frozen and hashed (`c1_external_stress_plan_v1_0`) before any external probability array existed, and it supersedes the pilot.

**Classification.** `RETROSPECTIVE_EXTERNAL_STRESS_TEST`. The cohorts were not prospectively held out, and all three were previously inspected while building manifests and an evidence audit. No checkpoint, threshold, seed or preprocessing choice was selected using external performance. These are descriptive observations, not a validation study.

**Cohorts.** CVC-ClinicDB (n = 612, task id 2, KVASIR analogue), BrEaST-Lesions-USG (n = 252, task id 1, BUSI analogue) and the Stones_where_are_you test split (n = 20, task id 3, KUB analogue). HAM10000 is excluded: the folder is the ISIC-2018 Task 3 classification release, which ships no masks, and the 10,015 masks present in it cannot be attributed to an annotator or licence. No HAM10000 inference was run.

**BrEaST inventory.** The folder holds 270 images and 252 tumour masks. The 18 mask-less images are of two kinds: 14 are additional `_other` views of 7 cases that already contribute a primary image (case022, case036, case038, case085, case092, case140, case151) and never entered the manifest; 4 are primary images with no tumour mask (case045, case061, case209, case213) and are the four exclusions. The manifest lists the 256 primary images, of which 252 are analysed, so $270 = 252 + 4 + 14$. No case contributes more than one analysed image, which makes 252 a valid case-level cluster count; it is not a verified patient count, because the manifest records no patient identifier and two case_ids belonging to one patient could not be detected.

**Protocol.** The canonical inference transform (RGB, aspect-preserving bilinear resize with $s=\min(512/W, 512/H)$, centred zero pad, $/255$), ground truth through the same geometry with nearest-neighbour resampling and binarised at $>0$, sigmoid threshold $0.5$, no per-cohort tuning, no test-time augmentation, no post-processing. Stones polygons are rasterised at native resolution and only category 7 (`stone`) is foreground. No row was dropped after a result was seen, and degenerate cases are kept and scored.

**GlobalMedFiLM internal ablation reference (macro over cases):**

| Cohort | Dice | 95% CI | IoU | Precision | Recall | Specificity | HD95 (px) | NSD@2px |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| CVC-ClinicDB (n = 612) | 68.66% | [62.65, 74.37] | 57.49% | 67.95% | 81.56% | 96.82% | 109.6 | 0.250 |
| BrEaST-Lesions-USG (n = 252) | 70.78% | [67.68, 73.78] | 59.84% | 73.91% | 75.57% | 98.19% | 74.0 | 0.252 |
| Stones (n = 20) | 8.08% | [0.34, 18.99] | 6.09% | 7.48% | 67.33% | 96.83% | 166.9 | 0.228 |

Intervals are percentile bootstrap resampling clusters: CVC-ClinicDB by sequence (29 clusters), BrEaST-Lesions-USG by case (252 clusters), and Stones by image, where each of the 20 images is its own cluster. The Stones interval is therefore an image-level descriptive interval and is wide by construction; it is not a population interval and supports no subgroup comparison. HD95 and NSD are in **pixels**: no external cohort ships physical pixel spacing, so no millimetre value is reported and surface metrics are not comparable across cohorts.

**Stones is three statements, not one.** The 8.08% headline is an artefact of scoring 14 empty-ground-truth images as zero. Stratified by annotation: the 6 stone-positive images reach 26.95% Dice with recall 67.33% and precision 24.93% (lesions are found but grossly over-segmented, median predicted area 3.7× the annotation); the 14 stone-absent images yield precision 0.00% because the model produced foreground on **14 of 14** stone-free radiographs. That statement is case-level. Pixel-level true-negative counts remain large and nonzero — median 259,214 of 262,144 pixels, minimum 231,793 — because the false-positive regions are small relative to the frame. What fails is the decision to emit any foreground at all on an image containing no stone (case-level specificity 0 of 14), not the per-pixel classification of background.

**Regional BARR on the same cases.** All four components hash-matched their frozen bindings before the first forward pass, all state dictionaries loaded with `strict=True`, and the two equivalent forms of the routing decision agreed on all 884 cases. No case failed and no case fell back for lack of an ROI.

**What the mechanism actually did.** Cohort means hide the per-case behaviour, so four cases were selected by explicit rule from the saved records (no re-inference) and rendered in the accompanying report (Figures 8 and 9): the accepted case with the largest gain (CVC::160, 80.62% → 92.09%, +11.47 pp), the accepted case with the largest loss (CVC::135, 18.22% → 13.43%, −4.78 pp), the most borderline rejection (CVC::358, $p(S_\omega) = 0.4966$ against a 0.50 threshold), and an unselected case (CVC::541, router score −0.001346 below $\tau_{C7}$). Of the 139 adopted refinements, 14 lost Dice on CVC-ClinicDB, 20 on BrEaST-Lesions-USG and none on Stones; Stones therefore has no harmful accepted example, and none is shown. The rejection case is instructive: its refinement was computed and then discarded, so its BARR output is identical to the global output by construction, and that identity is the rejection rather than a missing panel.

| Cohort | Selected | Accepted | Rejected | Not attempted | Failed | Global Dice | BARR Dice | Difference |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| CVC-ClinicDB | 19.28% | 83 | 35 | 494 | 0 | 68.66% | 68.97% | +0.32 pp |
| BrEaST-Lesions-USG | 22.22% | 47 | 9 | 196 | 0 | 70.78% | 70.81% | +0.03 pp |
| Stones | 50.00% | 9 | 1 | 10 | 0 | 8.08% | 8.21% | +0.13 pp |

The paired per-case change has median 0.00 pp in every cohort and an interquartile range of exactly [0, 0]. That range sits **on** zero rather than straddling it, and the reason is construction rather than symmetry: 700 of the 884 cases are untouched because the router did not select them or the safety gate rejected them. Among the 184 selected cases, 96 improve, 34 worsen and 54 are exactly unchanged; CVC shows 67 improved against 14 worsened, BrEaST 27 against 20. The mean is the informative statistic here and the quartiles are not. Among selected cases the changes are small and two-sided, which is consistent with no material change and is not a demonstration of external non-inferiority.

The router threshold was calibrated on the internal development population under a fixed 25% budget. The external selection fraction is therefore an outcome of that fixed threshold, not a controlled property of the cohort — the 50% figure on Stones reflects router scores sitting near $\tau_{C7}$, not that half of those images merited refinement. No recalibration was performed, because recalibrating on the evaluation cohort would make the result uninterpretable.

**Domain shift against the internal anchors.** Comparing to the frozen Phase 21 VAL808 per-domain Dice for the same task id (a different population, used only as a shift anchor):

| Cohort | Internal VAL808 | External Global | Shift | GT area (median) | Predicted area (median) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| CVC-ClinicDB (KVASIR) | 82.02% | 68.66% | −13.37 pp | 5.13% | 6.91% |
| BrEaST-Lesions-USG (BUSI) | 85.88% | 70.78% | −15.10 pp | 3.58% | 4.32% |
| Stones (KUB) | 76.41% | 8.08% | −68.32 pp | 0.00% | 0.90% |

A model that reaches 83.51% macro-domain Dice on its internal validation split does not carry that performance to external data from the same nominal modalities. Endoscopy loses 13.4 pp and breast ultrasound 15.1 pp; the Stones radiographs lose 68.3 pp, and the median-area column explains why — the model covers a far larger share of the canvas than the annotations do, so the failure is over-segmentation rather than a failure to respond.

**What this does not establish.** Dataset-level independence is not claimed for any cohort, consistent with the Phase 32 finding that no prospective clean external cohort is eligible. The study bounds failure modes; it does not estimate generalisation, and no confirmatory p-value is computed.

---

## 14. Computational Efficiency & FLOP Budget Analysis

The inference cost profile of RA-MedFiLM-BARR is **not** a large saving over the global stage. Analytical lower-bound MAC counts at $512\times512$ (`reports/audits/phase34_analytical_compute_contract.json`) give:

| Path | MACs | GFLOPs (2×) | Ratio vs global-only |
| :--- | :--- | :--- | :--- |
| Global MedFiLM only | 31.552 G | 63.10 | 1.000 |
| Always-refine (A1) | 34.782 G | 69.57 | 1.102 |
| A8/C9 conditional (expected) | 32.438 G | 64.88 | **1.028** |

- **Selective routing**: the expected analytical cost of the full policy is 2.8% **above** global-only and 6.7% **below** unconditional refinement, saving $2.345\times10^{9}$ MACs against always-refine. That saving is computed at the frozen activation frequency $p_{\text{activate}} = 27.43\%$ (Phase 30), not at an adoption rate.
- **Rejection is charged at full cost.** The contract records `EXECUTE_THEN_ACCEPT` and `EXECUTE_THEN_REJECT` as the same $34.782\text{ G}$ MACs (`accept_reject_differ: false`), because both EXECUTE states run the refiner and $S_\omega$. A rejected candidate is therefore never free, and a workload computed from adopted refinements alone understates the cost. On ROUTER_DEVELOPMENT the routed fraction is $1{,}239/4{,}957 = 25.0\%$, of which 1,205 refinements are adopted and 34 are computed and discarded; the earlier "24.3% refiner workload" conflated the adoption count with the routing count and is withdrawn.
- **What BARR does not do**: it does not reduce inference cost below the global stage, and it does not deliver a large compute saving. Its benefit is boundary recovery on routed crops at a bounded cost premium.
- These are analytical lower bounds from a Conv2d/Linear count, not wall-clock measurements. Measured latency on the RTX 3060 Ti is reported separately in Phase 34 and is hardware-specific.

An earlier draft of this section quoted 4.2 GFLOPs for the global stage and a ">65% reduction". Both figures are inconsistent with the frozen compute records by an order of magnitude and have been withdrawn.

---

## 15. Interpretability & Modality Representation Analysis

Descriptive model-mechanism observations are reported for task-conditioned modulation and router attribution. No causal claim is made: there is no architecture-matched control under an identical run, so the permitted phrasing is descriptive only.

1. FiLM $\gamma/\beta$ parameters are task-modulated, with the largest magnitude at the `decoder1` and `bridge` sites (20 FiLM task sites analysed).
2. Router feature-group attribution concentrates on the `decoder1` global and ROI feature groups (shares 0.324 and 0.307 respectively across 6 groups / 10 scalar features).
3. Saliency self-consistency is quantified per layer and per domain.

These are attribution and modulation observations. They do **not** establish that modulation *causes* the observed accuracy, and no PCA-based mechanistic interpretation (such as "additive shifts suppress skeletal background") is supported by a stored analysis record; such interpretations have been removed.

---

## 16. Ablation Studies & Sensitivity Analysis

### 16.1 Conditioning Injection Depth
The frozen architecture injects task conditioning at five sites (bridge, decoder4, decoder3, decoder2, decoder1). **No injection-depth ablation has been executed**, so the claim that five-site injection is superior to encoder-only or bottleneck-only conditioning is not supported and has been removed. The 13-arm Phase 28 ablation varies routing and safety policy, not injection depth.

### 16.2 Routing Confidence Thresholds ($\tau$)
**No threshold sweep over $\tau \in [0.1, 0.9]$ has been executed.** The routing decision rule is frozen at its specified operating point. The previously stated "empirical Pareto frontier" between compute and Dice is therefore not an empirical result and has been removed. Phase 34 provides analytical cost accounting at the frozen operating point only.

---

## 17. Scientific Limitations & Governance Boundaries

We transparently delineate the scientific boundaries of this work:
1. **Unexecuted Prospective Splits**: While code, configurations, and verification harnesses are frozen, production weights for C1 remain `NOT_ESTABLISHED` pending institutional clock attestation and hardware authorization.
2. **Historical Comparison Constraints**: Historical C2 and C3 results cannot be combined mathematically with v3 prospective tables without introducing confounding bias.
3. **Lack of Truly Independent External Validation**: All evaluation sets were generated by partitioning available open cohorts. The 884-case study in §13.1 is a retrospective stress test, not an external validation cohort: the three cohorts were previously inspected while building manifests and an evidence audit, and HAM10000 was excluded because its masks have no documented provenance. Phase 32 established that no prospective clean external cohort is eligible, so external validation has **not** been performed.
4. **No Confirmatory Statistics**: Phase 31 recorded zero eligible confirmatory procedures. Every interval in this manuscript is descriptive; no p-value is reported and none should be inferred. External intervals are percentile bootstrap over clusters and are labelled as such.
5. **Cross-Run Model Comparison**: The Phase 21 six-model comparison and the BARR results originate in different runs. BARR is therefore not a seventh arm of that comparison, and no controlled head-to-head between BARR and the baselines exists.
6. **In-Sample Safety Evidence**: The harm-rate decomposition of §12 is computed on ROUTER_DEVELOPMENT (n = 4,957), a subset of the 5,832 TRAIN samples.
7. **External Surface Metrics Are Unscaled**: No external cohort ships physical pixel spacing, so HD95, ASSD and NSD are reported in pixels, cannot be converted to millimetres, and are not comparable across cohorts.
8. **External Selection Fraction Is Not Controlled**: The router threshold is fixed from internal calibration. The external selection fractions (19.28%, 22.22%, 50.00%) are outcomes of that threshold, and no recalibration was performed on the evaluation cohorts.
9. **Small External Subgroup**: The Stones cohort is n = 20 with 6 positive cases. Its 95% interval (8.08% [0.34, 18.99]) is a percentile bootstrap over the 20 images with each image as its own cluster, so it is an image-level descriptive interval and not a population interval; at this sample size it is too wide to support a subgroup comparison. Point estimates and counts are reported alongside it.

---

## 18. Ethical, Regulatory & Clinical AI Translation

In compliance with trustworthy AI principles for healthcare:
- **Patient Privacy**: All primary datasets were obtained from public, de-identified research repositories (ISIC 2018, BUSI, Kvasir-SEG, KUB-StoneX) under their respective licences. **No IRB or ethics approval was obtained for this secondary analysis**, and none is claimed. The external cohorts in §13.1 (CVC-ClinicDB, BrEaST-Lesions-USG, Stones_where_are_you) are likewise public. HAM10000 material was **not** used: that cohort was excluded before inference because the available masks carry no documented provenance.
- **Fail-Safe Routing**: BARR specifies a fallback to the global prediction when a crop is rejected. This fallback is a specified mechanism; its clinical safety has not been demonstrated, and 390 harmful refinements persist in $A8$ on the development population.
- **Provenance Integrity (qualified)**: Experimental configurations are digest-bound and the C1 launch release is frozen by SHA-256 manifest. This makes reported results traceable to a specific code and data state. It does **not** make them immune to post-hoc selection, and it does not authenticate the human authority behind an approval: an audit found agent-generated signing material in the production trust root, and the RC3 gate currently refuses its own release digest. The trust boundary is under operator review, no scientific execution is authorised, and no production grant has been minted.

---

## 19. Conclusion & Research Roadmap

RA-MedFiLM-BARR presents a unified, mathematically formulated architecture for multi-domain medical image segmentation. By coupling task-conditioned FiLM modulation with budget-aware regional refinement and enforcing cryptographic data split governance, the framework resolves critical gaps in attribution and resource allocation. As soon as institutional trust authority is provisioned, the execution of the frozen 6-run campaign will deliver the definitive empirical verification of task modulation in clinical deep learning.

The external stress test in §13.1 adds a boundary to that claim that should not be softened in revision. On 884 cases from three public cohorts the frozen system executes end-to-end without error and BARR's preservation property survives transfer, but absolute accuracy does not: external Dice falls 13.4, 15.1 and 68.3 pp below the internal anchors for the same nominal modalities. Any deployment claim therefore requires domain adaptation and a prospective cohort, neither of which this work provides.

---

## 20. References

1. **Al-Dhabyani, W., Gomaa, M., Khaled, H., & Fahmy, A.** (2020). Dataset of breast ultrasound images. *Data in Brief*, 28, 104863. [DOI: 10.1016/j.dib.2019.104863]
2. **Codella, N. C., Gutman, D., Celebi, M. E., Helba, B., Marchetti, M. A., Dusza, S. W., ... & Halpern, A.** (2018). Skin lesion analysis toward melanoma detection: A challenge at the 2017 International Symposium on Biomedical Imaging (ISBI). *IEEE 15th International Symposium on Biomedical Imaging*, 168–172. [DOI: 10.1109/ISBI.2018.8363547]
3. **Geirhos, R., Jacobsen, J. H., Michaelis, C., Zemel, R., Brendel, W., Bethge, M., & Wichmann, F. A.** (2020). Shortcut learning in deep neural networks. *Nature Machine Intelligence*, 2(11), 665–673. [DOI: 10.1038/s42256-020-00257-z]
4. **Isensee, F., Jaeger, P. F., Kohl, S. A., Petersen, J., & Maier-Hein, K. H.** (2021). nnU-Net: a self-configuring method for deep learning-based biomedical image segmentation. *Nature Methods*, 18(2), 203–211. [DOI: 10.1038/s41592-020-01008-z]
5. **Jha, D., Smedsrud, P. H., Riegler, M. A., Halvorsen, P., de Lange, T., Johansen, D., & Pogorelov, K.** (2020). Kvasir-SEG: A segmented polyp dataset. *International Conference on Multimedia Modeling*, 451–462. [DOI: 10.1007/978-3-030-37734-2_37]
6. **Maier-Hein, L., Reinke, A., Godau, P., Tizabi, M. D., Buettner, F., Christodoulou, E., ... & Kopp-Schneider, A.** (2024). Metrics reloaded: recommendations for image analysis validation. *Nature Methods*, 21(2), 195–212. [DOI: 10.1038/s41592-023-02151-z]
7. **Perez, E., Strub, F., de Vries, H., Dumoulin, V., & Courville, A.** (2018). FiLM: Visual reasoning with a general conditioning layer. *Proceedings of the AAAI Conference on Artificial Intelligence*, 32(1), 3942–3951. [arXiv: 1709.07871]
8. **Ronneberger, O., Fischer, P., & Brox, T.** (2015). U-Net: Convolutional networks for biomedical image segmentation. *Medical Image Computing and Computer-Assisted Intervention (MICCAI)*, 234–241. [DOI: 10.1007/978-3-319-24574-4_28]
9. **Teerapittayanon, S., McDanel, B., & Kung, H. T.** (2016). BranchyNet: Fast inference via early exiting from deep neural networks. *23rd International Conference on Pattern Recognition (ICPR)*, 2464–2469. [DOI: 10.1109/ICPR.2016.7900006]
10. **Wang, G., Li, W., Zuluaga, M. A., Pratt, R., Patel, P. A., Aertsen, M., ... & Vercauteren, T.** (2018). Interactive medical image segmentation using deep learning with image-specific fine-tuning. *IEEE Transactions on Medical Imaging*, 37(7), 1562–1573. [DOI: 10.1109/TMI.2018.2794302]

---

## 21. Generated Paper Assets, Reproducibility and Reporting Status (added; earlier sections unchanged)

**Status.** C1 has 0/6 real runs; the primary C1 result is `NOT_ESTABLISHED`. This manuscript is **not** ready for journal submission. Authoritative asset status is recorded in `paper_asset_manifest.json`.

### 21.1 Figures (all under `paper_doc/figures/`; each exported as PDF, SVG, 600 DPI PNG, plus `*_source.csv`)

| Figure | Content | Status | Evidence class |
|---|---|---|---|
| 1 | Architecture specification (C1 vs C2 regions) | Ready | specification |
| 2 | Domains, VAL808 composition, frozen splits, matched-control design | Ready | descriptive |
| 3 | C1 paired FiLM attribution | **Pending** (no real runs) | – |
| 4 | C1 learning dynamics | **Pending** (no real run logs) | – |
| 5 | BARR routing funnel (development in-sample; external exploratory) | Ready | descriptive / exploratory |
| 6 | VAL808 GlobalMedFiLM vs BARR by domain (three seeds, fixed global backbone, no CI) | Ready | descriptive (selection-consumed) |
| 7 | External retrospective stress test: level, difference (axis ±1 pp), domain shift | Ready | exploratory |
| 8 | Main-text qualitative comparisons from deterministic case selection: accepted beneficial, accepted harmful, safety-rejected, representative non-selected, and stone-free false-positive failure | Ready | exploratory |
| 9 | Failure behavior with explicit denominator panels: all-external, routed-only, and stone-free-cohort rates | Ready | exploratory |
| 10 | Analytical GMACs vs accuracy; measured batch-1 latency (separate panels) | Ready | analytical / descriptive |

Supplementary qualitative overview retained: `paper_doc/figures/fig08s_qualitative_overview.*` (legacy reused composite panels, descriptive context only).

Figure captions must repeat: Dice values are proportions (0–1); "pp" means percentage points of Dice; Figure 6 and Table 4 use development-selected or in-sample populations; baseline accuracies in Figure 10 are protocol-incomparable.

### 21.2 Tables (`paper_doc/tables/*.csv|md|tex`)
Table 1 dataset/splits; Table 2 architecture and parameters; Table 3 C1 paired attribution (**NOT_ESTABLISHED**); Table 4 C2 routing/safety ablation (ROUTER_DEVELOPMENT n=4,957, in-sample; conditional on routed sets); Table 5 historical baselines (PROTOCOL_INCOMPARABLE, one run each); Table 6 external retrospective cohorts; Table 7 computational complexity (analytical MACs and measured latency kept separate); Table 8 failure-case summary. Every row carries source artifact, population, n, metric unit, evaluation version, run provenance and evidence class.

### 21.3 Verified denominators used in Figure 5
- Development (A8, in-sample): 4,957 cases → 1,239 routed → 1,205 adopted / 34 rejected → 815 improved / 390 worsened among adopted (conditional harm 390/1,205; intent-to-treat 390/4,957).
- External retrospective (n=884): 184 attempted → 139 adopted / 45 rejected → 96 improved / 34 worsened / 9 unchanged among adopted; 700 never attempted. Conditional improvements are **not** whole-cohort averages; whole-cohort BARR−Global Dice differences are +0.32 pp (CVC-ClinicDB), +0.03 pp (BrEaST), +0.13 pp (Stones), exploratory and uncertainty-free.

### 21.4 Empty-mask and undefined-surface handling
Per-case external records retain `gt_empty`, `pred_empty` and `surface_undefined_reason`; HD95/ASSD are undefined (excluded from means, with `n_defined` reported) when either mask is empty. Dice for empty-GT images is 0 when any foreground is predicted, so stone-free images (n=14) have Dice 0 and 14/14 received predicted foreground. Surface metrics are in pixels (no pixel spacing for external cohorts).

### 21.5 C1 statistical analysis (implemented, awaiting data)
`scripts/analysis/c1_results_aggregator.py` applies the frozen procedure: Δ_seed = mean over {ISIC, BUSI, Kvasir, KUB} of Dice(C1-T) − Dice(C1-C) on VAL808; estimate = mean of the three seed deltas; 10,000 domain-stratified paired cluster-percentile bootstrap draws, NumPy PCG64 seed 20261027, 95% interval; KUB resampled by patient (111 clusters), other domains by image because patient IDs are unavailable. Uncertainty is conditional on three fixed seeds; no p-value or confirmatory significance is claimed. With missing runs it emits `NOT_ESTABLISHED`; synthetic fixtures are labelled `SYNTHETIC_TEST_ONLY` and rejected in production mode.

### 21.6 Reproducible commands (tested)
```
.\.venv\Scripts\python.exe scripts\analysis\c1_run_artifacts.py validate     # exit 3 until all 6 real runs are valid
.\.venv\Scripts\python.exe scripts\analysis\c1_run_artifacts.py export       # learning curves, per-domain, per-image, provenance
.\.venv\Scripts\python.exe scripts\analysis\c1_results_aggregator.py
.\.venv\Scripts\python.exe scripts\analysis\c2_barr_aggregator.py            # -> reports/tables/c2_barr/
.\.venv\Scripts\python.exe scripts\analysis\c3_baseline_reporter.py          # -> reports/tables/c3_baselines/
.\.venv\Scripts\python.exe scripts\analysis\build_paper_assets.py            # partial build
.\.venv\Scripts\python.exe scripts\analysis\build_paper_assets.py --strict   # exits 2 while C1 figures are pending
.\.venv\Scripts\python.exe -m pytest tests\test_paper_assets.py tests\test_c1_stats_and_exports.py tests\test_c2_c3_reporters.py tests\test_c1_artifact_pipeline.py tests\test_c1_training_integration.py -q
```
Synthetic C1 training, resume and checkpoint-recovery tests are in `tests/test_c1_training_integration.py`; roster and patient-cluster verification (808 VAL images, 111 KUB patients) is in `tests/test_c1_artifact_pipeline.py`; bootstrap-protocol and run-artifact tests are in `tests/test_c1_stats_and_exports.py`. Two consecutive asset builds produced byte-identical outputs. Figure 1 shows FiLM at five sites (bridge, decoder4-1) and none in the encoder, matching `src/models/film/global_medfilm.py`.

**C1 producer gaps (not invented).** The frozen trainer persists per-epoch history and best-epoch per-image Dice/IoU/precision/recall only. It does not persist predicted masks, HD95/ASSD, per-image metrics at non-best epochs, explicit resume events, per-epoch wall-clock or GPU memory, or the launching release identity; the exporters therefore report these as absent. Minimum compatible future amendment: an append-only `events.jsonl` written by the launcher. Synthetic runs are rejected by the exporters unless `--allow-synthetic` is given, and are then stamped SYNTHETIC.

**Known issue.** `tests/test_c1_launch_rc2.py::test_default_production_store_is_absent` is environment-dependent and is documented rather than suppressed.

**C2/C3 outputs.** The C2 aggregator never pools VAL808 (selection-consumed), ROUTER_DEVELOPMENT (in-sample), historical ROUTER_HOLDOUT875 and the 884-case retrospective external cohort; it preserves the 14/14 stone-free foreground failure. The C3 reporter emits six PROTOCOL_INCOMPARABLE single-run historical records, an empty protocol-matched section and no leaderboard. Analytical GMACs are lower bounds, not latency; BARR is not shown to be cheaper than Global (A8 expected analytical cost is 1.028x Global).

### 21.7 CLAIM 2024 coverage and gaps
Covered by existing text: data sources, partitions, model description, training recipe, metrics, failure analysis, limitations. Not yet satisfied: primary C1 result, independent test-set evaluation, protocol-faithful baselines (C3), ethics/approval statement (none claimed), dataset licence verification per cohort, patient-level split verification for ISIC, BUSI and Kvasir. Clinical readiness is not claimed.
