# Task-Conditioned Feature-Wise Linear Modulation and Budget-Aware Regional Refinement in Multi-Domain Medical Image Segmentation (RA-MedFiLM-BARR)

**Authors:** RA-MedFiLM-BARR Scientific Consortium  
**Governance & Date:** October 30, 2026 | Canonical Manifest v3 Governance  
**Operational Status:** PRE-EXPERIMENTAL RIGOROUS PROTOCOL & METHODOLOGICAL SPECIFICATION  
**Target Venue:** IEEE Transactions on Medical Imaging (TMI) / Medical Image Analysis (MedIA)  

---

## Abstract
Deep neural networks deployed across heterogeneous medical imaging modalities often suffer from negative transfer or require fragmented, computationally redundant single-task pipelines. In this work, we formulate **RA-MedFiLM-BARR**, a unified framework integrating task-conditioned Feature-wise Linear Modulation (FiLM) with Budget-Aware Regional Refinement (BARR). We delineate three research contributions:
- **Contribution C1 (*Proposed & Methodologically Frozen*)**: Task-conditioned FiLM attribution designed to isolate causal modulation gains against an exact structural identity control ($C1\text{-}C$) across identical seeds ($42, 123, 3407$). Primary prospective empirical results remain unexecuted pending institutional authorization and host-clock attestation.
- **Contribution C2 (*Exploratory Development*)**: Budget-aware regional refinement routing ambiguous or sub-centimeter lesion regions to high-capacity localizers under hard compute constraints, evaluated retrospectively on development partitions.
- **Contribution C3 (*Exploratory Retrospective Benchmarking*)**: Cross-domain shared segmentation baselines across four diverse modalities: digital radiography (KUB-StoneX), dermoscopy (ISIC 2018), breast ultrasound (BUSI), and polyp endoscopy (Kvasir-SEG).

To eliminate data leakage, we enforce canonical Manifest v3 governance, isolating 118 high-risk patient-overlapping cases and locking the 1,683-case evaluation cohort. Statistical inference is governed by domain-stratified cluster bootstrapping; because no confirmatory significance procedure is eligible, all reported intervals are descriptive.

On the VAL808 development split, Global MedFiLM attains 83.51% macro-domain Dice with 3.52M parameters and ranks first of six architectures under a single shared protocol, though it is not statistically distinguishable from DeepLabV3+. Regional BARR **preserves** this accuracy rather than improving on it: +0.28 pp on VAL808 (three-seed mean) and +0.17 pp on the one-shot ROUTER_HOLDOUT (95% CI [+0.11, +0.24]), within a pre-specified −0.5 pp non-inferiority margin. A retrospective external stress test on 884 cases from three public cohorts shows that this preservation transfers (+0.32 pp, +0.03 pp and +0.13 pp macro Dice on CVC-ClinicDB, BrEaST-Lesions-USG and Stones respectively) while absolute performance does not: external Dice falls 13.4, 15.1 and 68.3 pp below the internal anchors for the same nominal modalities, and on the Stones cohort the model marks foreground on 14 of 14 stone-free radiographs. The external study is explicitly not a validation study.

While formal institutional approval remains pending before launching production weights, this manuscript establishes the mathematical rigor, exact implementation mechanics, baseline evidence boundaries, and statistical contracts required for fully defensible clinical AI benchmarking.

---

## 1. Introduction & Clinical Motivation
Multi-domain medical image analysis holds tremendous potential for clinical decision support, triage, and robotic surgery. However, in heterogeneous healthcare environments, imaging modalities vary drastically in physical acquisition principles, signal-to-noise ratios, spatial resolution, and lesion morphology. Conventional practices either train distinct models for each anatomical domain—multiplying operational maintenance overhead and preventing shared representation learning—or train monolithic architectures that suffer from catastrophic interference and negative transfer, where dominant gradients from high-contrast modalities degrade performance on subtle, tiny objects.

To overcome these structural limitations, two paradigms are required:
1. *Adaptive Task Conditioning*: Conditioning intermediate neural activations upon domain priors dynamically without altering network topology.
2. *Selective Regional Refinement*: Allocating dense high-resolution spatial compute only to complex, ambiguous, or sub-centimeter anatomical regions while processing standard background structures via low-cost global passes.

The RA-MedFiLM-BARR framework formalizes this multi-domain paradigm. In this paper, we document the system architecture, mathematical formulations, data provenance safeguards, and prospective validation protocol.

---

## 2. Related Work & Research Gaps

### 2.1 Multi-Domain Medical Image Segmentation
Unified medical segmentation networks typically rely on multi-head decoders or separate routing paths (Ronneberger et al., 2015; Isensee et al., 2021). While frameworks such as nnU-Net optimize single-domain hyperparameter heuristics, joint multi-modality learning often introduces gradient conflicts. Recent efforts explore unified backbones, but frequently fail to account for multi-center data contamination or subtle patient overlap across imaging series.

### 2.2 Feature-Wise Linear Modulation (FiLM)
Feature-wise Linear Modulation (Perez et al., 2018) was originally developed for visual reasoning to dynamically manipulate convolutional feature representations conditioned on linguistic or categorical embeddings. In medical vision, modulation layers have been utilized for demographic or disease metadata. However, prior medical literature uniformly lacks *matched architectural controls*: reported gains often stem from additional trainable projection parameters or altered optimization dynamics rather than true task modulation.

### 2.3 Regional Refinement & Selective Routing
Coarse-to-fine segmentation architectures and cascade models (e.g., Wang et al., 2018) process cropped regions of interest to recover fine spatial details. Nevertheless, arbitrary fixed cascades run all crops unconditionally, wasting clinical compute budgets. Dynamic routing (Teerapittayanon et al., 2016) introduces early exits or conditional execution, yet principled integration with explicit FLOP budget thresholds in medical imaging remains sparse.

### 2.4 Research Gaps Addressed
1. *Causal Attribution*: Existing FiLM evaluations fail to test an unconditioned identity control with identical seed, initialization, and optimizer states.
2. *Data Leakage Governance*: Multi-domain benchmarks frequently include inadvertent duplicate scans or linked patient records across train/validation/test splits.
3. *Budget-Aware Spatial Allocation*: Lack of a unified router-refiner framework that bounds computational FLOPs while recovering tiny object boundaries.

---

## 3. Core Contributions: Status & Taxonomy

To ensure scientific transparency, every research contribution is explicitly categorized:
- **Contribution C1 (FiLM Task Attribution — *Proposed Protocol*)**:
  - *Status*: Methodologically frozen in release `C1_FILM_ATTRIBUTION_V1_LAUNCH_RC3`; empirical 6-run execution pending (`NOT_ESTABLISHED`).
  - *Scope*: Causal architectural intervention isolating the mathematical effect of task-conditioned scale/shift affine vectors against an exact zero-modulation control. It does *not* assert broad clinical efficacy until prospective evaluation is authorized.
- **Contribution C2 (Budget-Aware Regional Refinement — *Exploratory Development*)**:
  - *Status*: Retrospectively validated on historical development partitions (`HISTORICAL_DESCRIPTIVE_RESULT`).
  - *Scope*: Demonstrates that selective routing plus learned post-safety filtering ($S_\omega$) reduces the all-population harm rate from 42.67% ($A1$, unconditional refinement) to 7.87% ($A8$), in-sample on the 4,957-case development population. The router accounts for 2,115 → 412 harmful cases and $S_\omega$ for a further 412 → 390; the reduction is therefore attributable mainly to routing, not to the safety filter alone.
- **Contribution C3 (Fair Multi-Domain Benchmarking — *Exploratory Retrospective*)**:
  - *Status*: Validated across 5 baseline architectures on historical splits (`PROTOCOL_INCOMPARABLE`).
  - *Scope*: Establishes initial empirical baselines across four clinical targets but requires re-benchmarking under clean Manifest v3 governance.
- **External stress test (not a contribution, *Descriptive Only*)**: A retrospective 884-case stress test (CVC-ClinicDB n = 612, BrEaST-Lesions-USG n = 252, Stones_where_are_you test split n = 20) was executed with both the Global MedFiLM checkpoint and the full frozen BARR assembly. HAM10000 was excluded before inference because the available masks have no documented provenance. This is not an external validation cohort; see §13.1.

---

## 4. Mathematical Formulation & Architecture

### 4.1 Global Backbone and Actual Implemented FiLM Equation
Let $X \in \mathbb{R}^{B \times C_{\text{in}} \times H \times W}$ denote the input image batch, and let $t \in \{0, 1, 2, 3\}$ denote the categorical domain index corresponding to KUB, ISIC, BUSI, and KVASIR respectively. The task embedding module maps $t$ into a learned embedding vector $e_t = E(t) \in \mathbb{R}^{d_e}$ ($d_e = 32$).

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
The global stage produces a coarse segmentation probability map $P_{\text{global}} \in [0, 1]^{B \times 1 \times H \times W}$ for binary lesion demarcation. Candidate bounding boxes $\{B_k\}$ are extracted based on spatial ambiguity:
$$A(x, y) = 1 - 2 \cdot |P_{\text{global}}(x, y) - 0.5|$$

### 5.2 Routing Function & Budget Invariants
Let $c_k \in [0, 1]$ represent the routing confidence score for candidate region $k$, predicted by a lightweight routing gate $R(F_{\text{crop}})$. Given an allocated computational budget constraint $B_{\text{max}}$ (measured in GFLOPs per image), the discrete routing decision $z_k \in \{0, 1\}$ is governed by:
$$z_k = \mathbb{I}\left(c_k \ge \tau \quad \text{and} \quad \sum_{j \le k} \text{FLOPs}(B_j) \le B_{\text{max}}\right)$$
If $z_k = 1$, the crop $B_k$ is forwarded to the high-capacity Regional Refiner; if $z_k = 0$, the coarse global prediction is retained.

### 5.3 Parameter accounting
The frozen system comprises four components with verified parameter counts (`reports/audits/phase36_robustness_scientific_result_v1_23.json`, strict load, zero missing or unexpected keys):

| Component | Symbol | Parameters |
| :--- | :--- | ---: |
| Global FiLM segmentation network | $G$ | 3,523,001 |
| Regional refiner | $R_\psi$ | 1,276,401 |
| Benefit router | $B_\phi$ | 36,801 |
| Post-safety filter | $S_\omega$ | 1,217 |
| **Total** | | **4,837,420** |

The total is 4.84M parameters, not the 4.80M stated in earlier project material. $R_\psi$ accounts for 90% of the increase over the global network, so BARR's cost is dominated by the refiner rather than by routing or safety.

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
- **TEST (Locked Prospective)**: 1,683 samples (ISIC: 742, BUSI: 174, KVASIR: 181, KUB: 586)
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
- Compute time per 100-epoch run: $5.45 \text{ hours}$ (Central estimate)
- Full 6-run campaign duration: $37.72 \text{ hours}$ (Nominal) to $42.71 \text{ hours}$ (Conservative), fitting within available sprint deadlines (~120 hours remaining).

### 7.2 Crytographic Release Invariant (RC3)
The launch framework is governed by frozen release `C1_FILM_ATTRIBUTION_V1_LAUNCH_RC3`, bearing SHA-256 digest:
`54d1273a53db7dae58118a4bb69c2a96ba2e474a72512a9dccb4c98c9513549f`
Release verification at the time of writing: 27 RC3 tests pass and 42 of 43 RC2 regression tests pass. One RC2 test fails because the default production trust store is present on the host (see §18.3); it is reported rather than suppressed.

---

## 8. Prospective 6-Run C1 Experimental Protocol

To eliminate p-hacking, selection bias, and seed cherry-picking, the C1 evaluation protocol is immutably defined prior to execution:
- **Treatment Arm ($C1\text{-}T$)**: Task-conditioned FiLM U-Net trained on Manifest v3 across seeds $\{42, 123, 3407\}$.
- **Control Arm ($C1\text{-}C$)**: Matched unconditioned U-Net trained on identical splits across identical seeds $\{42, 123, 3407\}$.
- **Hyperparameter Invariants**: AdamW optimizer ($\text{lr} = 10^{-4}$, weight decay $= 10^{-2}$), Combined BCE + Soft Dice loss, cosine annealing schedule over 100 epochs, early stopping patience $= 15$ based on validation EqualDomainMacroDice.

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
$$\Delta_{\text{macro}} = \frac{1}{4} \sum_{d \in \{\text{KUB, ISIC, BUSI, KVASIR}\}} \left(\text{DSC}_{d}(C1\text{-}T) - \text{DSC}_{d}(C1\text{-}C)\right)$$
Hypothesis testing:
- **Null Hypothesis ($H_0$)**: $\Delta_{\text{macro}} \le 0$
- **Alternative Hypothesis ($H_1$)**: $\Delta_{\text{macro}} > 0$
- **Statistical Significance**: Paired Wilcoxon signed-rank test across test cases, stratified by domain, with two-sided $\alpha = 0.05$.
- **Predeclared Bootstrap Uncertainty**: Exactly 10,000 paired cluster bootstrap resamples ($B=10,000$) using the NumPy PCG64 PRNG initialized with frozen seed `20261027`, reporting two-sided 95% percentile confidence intervals. Patient-level clustering is enforced for KUB (280 validation samples grouped into 111 verified patient clusters); image-level sampling is maintained for ISIC, BUSI, and Kvasir-SEG where patient-level linkage is unprovided in open clinical sources.

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

---

## 13. Results: Campaign 3 — Fair Multi-Domain Segmentation Benchmarking (Historical Evidence)

Historical development validation across 5 baseline architectures (Phase 20b) and Global MedFiLM (Phase 21) established cross-domain performance:

| Model Name | Backbone Class | Trainable Params | Best Epoch | Macro Domain Dice | 95% Bootstrap CI | Macro Domain IoU | ISIC Dice | BUSI Dice | KVASIR Dice | KUB Dice |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DeepLabV3+** | `DeepLabV3Plus` | 40,347,041 | 57 | 0.8277 | [0.7707, 0.8761] | 0.7412 | 0.8853 | 0.8669 | 0.8197 | 0.7387 |
| **Transformer MiT U-Net** | `TransformerMiTUNet` | 16,347,777 | 74 | 0.8224 | [0.7599, 0.8755] | 0.7366 | 0.8871 | 0.8640 | 0.8133 | 0.7252 |
| **U-Net++** | `UNetPlusPlus` | 9,159,681 | 55 | 0.7920 | [0.7446, 0.8382] | 0.6910 | 0.8601 | 0.8163 | 0.7710 | 0.7207 |
| **Attention U-Net** | `AttentionUNet` | 7,851,285 | 64 | 0.7890 | [0.7288, 0.8447] | 0.6927 | 0.8617 | 0.8277 | 0.7710 | 0.6958 |
| **Standard U-Net** | `UNet` | 7,763,041 | 74 | 0.7878 | [0.7381, 0.8375] | 0.6881 | 0.8553 | 0.8198 | 0.7552 | 0.7211 |
| **Global MedFiLM** | `GlobalMedFiLM` | 3,523,001 | 68 | 0.8351 | [0.7877, 0.8780] | 0.7448 | 0.8972 | 0.8588 | 0.8202 | 0.7641 |

*Governance Disclaimer*: Classified as `PROTOCOL_INCOMPARABLE` due to historical manifest v2 splits.

### 13.1 External stress test (retrospective, n = 884, Global and BARR)

An earlier draft reported a four-case pilot at n = 1 per dataset, run under a non-canonical stretch-resize convention and including a HAM10000 row whose masks have no documented provenance. That pilot is withdrawn in full. What follows was produced by a design frozen and hashed (`c1_external_stress_plan_v1_0`) before any external probability array existed, and it supersedes the pilot.

**Classification.** `RETROSPECTIVE_EXTERNAL_STRESS_TEST`. The cohorts were not prospectively held out, and all three were previously inspected while building manifests and an evidence audit. No checkpoint, threshold, seed or preprocessing choice was selected using external performance. These are descriptive observations, not a validation study.

**Cohorts.** CVC-ClinicDB (n = 612, task id 2, KVASIR analogue), BrEaST-Lesions-USG (n = 252, task id 1, BUSI analogue) and the Stones_where_are_you test split (n = 20, task id 3, KUB analogue). HAM10000 is excluded: the folder is the ISIC-2018 Task 3 classification release, which ships no masks, and the 10,015 masks present in it cannot be attributed to an annotator or licence. No HAM10000 inference was run.

**Protocol.** The canonical inference transform (RGB, aspect-preserving bilinear resize with $s=\min(512/W, 512/H)$, centred zero pad, $/255$), ground truth through the same geometry with nearest-neighbour resampling and binarised at $>0$, sigmoid threshold $0.5$, no per-cohort tuning, no test-time augmentation, no post-processing. Stones polygons are rasterised at native resolution and only category 7 (`stone`) is foreground. No row was dropped after a result was seen, and degenerate cases are kept and scored.

**Global MedFiLM (macro over cases):**

| Cohort | Dice | 95% CI | IoU | Precision | Recall | Specificity | HD95 (px) | NSD@2px |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| CVC-ClinicDB (n = 612) | 68.66% | [62.65, 74.37] | 57.49% | 67.95% | 81.56% | 96.82% | 109.6 | 0.250 |
| BrEaST-Lesions-USG (n = 252) | 70.78% | [67.68, 73.78] | 59.84% | 73.91% | 75.57% | 98.19% | 74.0 | 0.252 |
| Stones (n = 20) | 8.08% | [0.34, 18.99] | 6.09% | 7.48% | 67.33% | 96.83% | 166.9 | 0.228 |

Intervals are percentile bootstrap over clusters (CVC: 29 sequences; BrEaST: 252 cases; Stones: none). HD95 and NSD are in **pixels**: no external cohort ships physical pixel spacing, so no millimetre value is reported and surface metrics are not comparable across cohorts.

**Stones is three statements, not one.** The 8.08% headline is an artefact of scoring 14 empty-ground-truth images as zero. Stratified by annotation: the 6 stone-positive images reach 26.95% Dice with recall 67.33% and precision 24.93% (lesions are found but grossly over-segmented, median predicted area 3.7× the annotation); the 14 stone-absent images yield precision 0.00% because the model produced foreground on **14 of 14** stone-free radiographs. The substantive finding is an absence of true-negative behaviour, not a segmentation score.

**Regional BARR on the same cases.** All four components hash-matched their frozen bindings before the first forward pass, all state dictionaries loaded with `strict=True`, and the two equivalent forms of the routing decision agreed on all 884 cases. No case failed and no case fell back for lack of an ROI.

| Cohort | Selected | Accepted | Rejected | Not attempted | Failed | Global Dice | BARR Dice | Difference |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| CVC-ClinicDB | 19.28% | 83 | 35 | 494 | 0 | 68.66% | 68.97% | +0.32 pp |
| BrEaST-Lesions-USG | 22.22% | 47 | 9 | 196 | 0 | 70.78% | 70.81% | +0.03 pp |
| Stones | 50.00% | 9 | 1 | 10 | 0 | 8.08% | 8.21% | +0.13 pp |

The paired per-case change has median 0.00 pp in every cohort and an interquartile range straddling zero, because most cases are unchanged by construction: the router did not select them, or the safety gate rejected them. CVC shows 67 improved against 14 worsened; BrEaST 27 against 20. **Preservation transfers; improvement does not.**

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

- **Selective routing**: the expected analytical cost of the full policy is 2.8% **above** global-only and 6.7% **below** unconditional refinement, saving $2.345\times10^{9}$ MACs against always-refine at a 24.3% refiner workload.
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
9. **Small External Subgroup**: The Stones cohort is n = 20 with 6 positive cases. It carries no interval estimate and supports no subgroup comparison.

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
