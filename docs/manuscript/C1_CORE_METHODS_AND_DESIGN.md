# RA-MedFiLM-BARR: Manuscript Core Methods & Experimental Design (Draft)

**Document Status:** ADVANCE PUBLICATION READY (GROUNDED IN FROZEN REPOSITORY SOURCE)  
**Protocol Identification:** `C1_FILM_ATTRIBUTION_V1` (`reports/planning/c1_film_attribution_v1/protocol.json`)  
**Data Governance Split:** `phase4_v3` (`manifests/phase4_v3/`)  
**Date:** 2026-10-29

---

## 1. Multi-Domain Segmentation Datasets & Governance

The investigation is prospectively conducted across four diverse clinical medical imaging domains harmonized under a single resolution and color representation space ($512 \times 512 \times 3$, RGB):

| Domain | Clinical Target | Image Modality | Canonical v3 Train | Canonical v3 Val | Canonical v3 Test (Locked) | Quarantined Samples |
|---|---|---|---|---|---|---|
| **ISIC** | Cutaneous Melanoma Lesions | Dermoscopy | 2,556 | 357 | 735 | 46 |
| **BUSI** | Breast Neoplasms | B-mode Ultrasound | 602 | 84 | 174 | 67 |
| **KVASIR** | Gastrointestinal Polyps | Endoscopy | 696 | 87 | 216 | 1 |
| **KUB** | Urolithiasis / Urinary Calculi | Abdominal X-Ray (Radiography) | 1,978 | 280 | 558 | 4 |
| **Total** | — | — | **5,832** | **808** | **1,683** | **118** |

### Data Leakage Governance (`phase4_v3`)
Historical manifest `phase4_v2` contained retrospective patient grouping discrepancies and near-duplicate asset clusters. A formal quarantine protocol was established in Phase 05:
- Exact image hash duplicates removed.
- Cross-split patient overlap quarantined ($62$ test-linked + $5$ train-val-only BUSI cases).
- Perceptual hash near-duplicate pairs ($d \le 2$) quarantined on development side.
- **Test Set Immutability:** Test split ($1,683$ samples, SHA-256: `9361eba6...`) remained strictly byte-identical to historical splits. No test imagery is opened during development or model checkpoint selection.

---

## 2. Model Architecture & FiLM Conditioning Mechanics

### 2.1 Unified Shared Backbone ($G$)
Global segmentation is provided by a shared 5-stage residual U-Net architecture without dataset-specific encoders or heads:
- **Encoder Channels:** $(24, 48, 96, 192, 256)$
- **Normalisation:** GroupNorm with up to 8 channels per group ($\min(\text{divisor} \le 8)$).
- **Activations:** SiLU throughout.
- **Output:** Single $1 \times 1$ convolution generating foreground logit $\hat{y} \in \mathbb{R}^{H \times W \times 1}$.

### 2.2 Feature-Wise Linear Modulation (FiLM)
Task conditioning is injected exclusively via FiLM layers at five designated sites: `bridge`, `decoder4`, `decoder3`, `decoder2`, and `decoder1`:
$$\hat{F}_\ell = \bigl(1 + \gamma_\ell(t)\bigr) \cdot F_\ell + \beta_\ell(t)$$
where modulation coefficients are derived from a learned 32-dimensional task embedding vector $\mathbf{e}_t$ ($t \in \{0, 1, 2, 3\}$) via a two-layer MLP with hidden dimension 64:
$$\gamma_\ell(t) = \tanh\left(\gamma^\text{raw}_\ell(t)\right), \quad \beta_\ell(t) = \tanh\left(\beta^\text{raw}_\ell(t)\right)$$

### 2.3 Matched Identity Control Condition (C1-C)
To establish causal attribution of FiLM conditioning without confounding backbone architectural capacity:
- The treatment arm (**C1-T**) trains all parameters ($3,523,001$ parameters).
- The control arm (**C1-C**) initializes from identical seed weights, but freezes all conditioning layers ($\text{requires\_grad} = \text{False}$, $90,768$ parameters frozen, $3,432,233$ trainable backbone parameters).
- Because FiLM output projections are zero-initialized, $\gamma_\ell(t) = \mathbf{0}$ and $\beta_\ell(t) = \mathbf{0}$ holds identically across all tasks and sites throughout training, reducing C1-C to an exact shared-weight multi-task baseline.

---

## 3. C1 Controlled Experimental Design

### 3.1 Training Hyperparameters (Frozen Protocol)
- **Input Dimensions:** $512 \times 512$, RGB 3-channel.
- **Batch Size:** Train = 4, Validation = 8.
- **Loss Function:** Compound BCE + Soft Dice Loss:
  $$\mathcal{L} = 0.5 \cdot \mathcal{L}_\text{BCE}(\hat{y}, y) + 0.5 \cdot \mathcal{L}_\text{Dice}(\hat{y}, y)$$
- **Optimizer:** AdamW ($\text{lr} = 10^{-4}$, $\text{weight\_decay} = 10^{-4}$).
- **Learning Rate Schedule:** Cosine Annealing over 100 epochs.
- **Sampling Strategy:** Domain-balanced uniform sampling across all four clinical tasks within each epoch.
- **Checkpoint Selection:** Pre-declared best validation epoch evaluated via equal-domain macro-averaged Dice score on the canonical `phase4_v3` validation population ($N = 808$).

### 3.2 Six-Run Paired Campaign
To ensure rigorous statistical defensibility, the campaign consists of three prospectively declared random seeds:
- Seed 42: `(C1-T, seed 42)` paired with `(C1-C, seed 42)`
- Seed 123: `(C1-T, seed 123)` paired with `(C1-C, seed 123)`
- Seed 3407: `(C1-T, seed 3407)` paired with `(C1-C, seed 3407)`

### 3.3 Primary Statistical Estimand
The causal treatment effect $\Delta_\text{C1}$ is evaluated on the selection-validated cohort:
$$\Delta_d(s) = \text{Dice}_{d, \text{C1-T}}(s) - \text{Dice}_{d, \text{C1-C}}(s)$$
$$\Delta_\text{C1} = \frac{1}{4} \sum_{d \in \{\text{ISIC}, \text{BUSI}, \text{KVASIR}, \text{KUB}\}} \left( \frac{1}{3} \sum_{s \in \{42, 123, 3407\}} \Delta_d(s) \right)$$
Uncertainty estimation is computed via 10,000 paired, domain-stratified cluster percentile bootstrap resamples (PCG64 generator, seed `20261027`), with clustering applied at the patient level for KUB.

---

## 4. Empirical Performance Schema (Results Table Shell)

*Note: In accordance with scientific integrity rules, values will be populated strictly upon authorized run completion.*

| Configuration | Seed | ISIC Dice | BUSI Dice | KVASIR Dice | KUB Dice | Macro Mean Dice | Paired $\Delta$ vs Control |
|---|---|---|---|---|---|---|---|
| **C1-C (Control)** | 42 | *pending* | *pending* | *pending* | *pending* | *pending* | — |
| **C1-T (Treatment)** | 42 | *pending* | *pending* | *pending* | *pending* | *pending* | *pending* |
| **C1-C (Control)** | 123 | *pending* | *pending* | *pending* | *pending* | *pending* | — |
| **C1-T (Treatment)** | 123 | *pending* | *pending* | *pending* | *pending* | *pending* | *pending* |
| **C1-C (Control)** | 3407 | *pending* | *pending* | *pending* | *pending* | *pending* | — |
| **C1-T (Treatment)** | 3407 | *pending* | *pending* | *pending* | *pending* | *pending* | *pending* |
| **Mean C1-C** | Pool | *pending* | *pending* | *pending* | *pending* | *pending* | — |
| **Mean C1-T** | Pool | *pending* | *pending* | *pending* | *pending* | *pending* | **$\Delta_\text{C1}$** [*95% CI*] |

---

## 5. Scope Boundaries and Honest Evidence Limitations
1. **Validation Population (VAL-808):** The validation split is selection-consumed; reported metrics reflect model development checkpoint selection, not independent out-of-sample clinical generalization.
2. **C2 (Regional Refiner) & C3 (Benefit Routing):** Evidence from historical Phase 14-26 exploratory baselines is preserved as diagnostic background. Prospective causal claims for regional refinement and routing are decoupled from C1 and explicitly classified as limitations / future research.
3. **No Clinical Diagnosis Claims:** Segmentation metric improvements (Dice, IoU, HD95) reflect geometric overlap precision, not evaluated diagnostic efficacy in live clinical workflows.
