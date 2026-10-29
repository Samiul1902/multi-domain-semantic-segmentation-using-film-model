# Task-Conditioned Feature-Wise Linear Modulation and Budget-Aware Regional Refinement in Multi-Domain Medical Image Segmentation

**Authors:** RA-MedFiLM-BARR Research Team  
**Date:** October 2026 (Emergency 7-Day Sprint Draft)  
**Status:** PROVISIONAL RESEARCH DRAFT — PRE-EXPERIMENTAL FOUNDATION

---

## Abstract
Deep neural networks deployed across heterogeneous medical imaging modalities often suffer from negative transfer or require fragmented single-task architectures. In this work, we present **RA-MedFiLM-BARR**, a unified framework integrating task-conditioned Feature-wise Linear Modulation (FiLM) with Budget-Aware Regional Refinement (BARR). We establish a rigorous prospective evaluation methodology evaluated across four distinct modalities: digital radiography (KUB-StoneX), dermoscopy (ISIC 2018), breast ultrasound (BUSI), and gastrointestinal endoscopy (Kvasir-SEG). To rigorously isolate the causal contribution of task conditioning (Contribution C1), we introduce a matched-initialization frozen identity-control model ($C1\text{-}C$) compared against learnable task FiLM ($C1\text{-}T$) across three identical random seeds ($42, 123, 3407$). Statistical inference is governed by a domain-stratified paired cluster bootstrap isolating case-sampling uncertainty from seed-initialization variance. In this preliminary release, we establish the mathematical architecture, dataset ontology, leakage-safe protocol boundaries, and prospective experimental design.

---

## 1. Introduction & Research Gap
Multi-task and multi-domain medical image segmentation often face significant distribution shifts across image acquisition physics, anatomical scales, and lesion characteristics. Monolithic multi-domain architectures frequently degrade performance on compact or low-contrast targets due to dominant gradients from large, high-contrast organs. To address this:
1. **Task-Conditioned Modulation (C1):** Conditioning spatial representations dynamically without altering shared backbone parameters or multiplying network branches.
2. **Budget-Aware Regional Refinement (C2):** Routing complex, ambiguous subregions to specialized high-resolution refiners while adhering to strict inference FLOP budgets.
3. **Fair Benchmarking (C3):** Standardizing pre-processing, evaluation metrics, and split boundaries to provide unbiased comparative evidence.

---

## 2. Related Work
- Multi-domain medical segmentation architectures.
- FiLM (Feature-wise Linear Modulation) and dynamic parameter conditioning.
- Hard example mining and cascade regional refinement.
- Rigorous statistical practices and cluster bootstrap in medical imaging.

---

## 3. Mathematical Formulation & Architecture

### 3.1 Task Embedding & Modulation
Let $t \in \{0, 1, 2, 3\}$ denote the domain index corresponding to ISIC, BUSI, KVASIR, and KUB respectively. The task embedding is given by:
$$\mathbf{e}_t = \text{Embedding}(t) \in \mathbb{R}^{D_e}, \quad D_e = 32$$
At each of the 5 designated FiLM sites (bridge, decoder4, decoder3, decoder2, decoder1), the feature map $\mathbf{F} \in \mathbb{R}^{C \times H \times W}$ is modulated by:
$$\gamma_{\text{raw}}, \beta_{\text{raw}} = \text{Linear}(\text{SiLU}(\text{Linear}(\mathbf{e}_t)))$$
$$\gamma = \tanh(\gamma_{\text{raw}}), \quad \beta = \tanh(\beta_{\text{raw}})$$
$$\hat{\mathbf{F}} = (1 + \gamma \cdot \mathbf{1}_{H \times W}) \odot \mathbf{F} + \beta \cdot \mathbf{1}_{H \times W}$$
where output projection weights and biases are initialized to zero, ensuring an exact identity transformation at initialization.

### 3.2 Matched Identity Control ($C1\text{-}C$)
The control model $C1\text{-}C$ shares the exact backbone initialization and architecture, with all task-conditioning weights frozen:
$$\gamma \equiv \mathbf{0}, \quad \beta \equiv \mathbf{0} \implies \hat{\mathbf{F}} \equiv \mathbf{F}$$

### 3.3 Loss Function & Optimization
Training minimizes the composite binary cross-entropy and soft Dice loss:
$$\mathcal{L} = 0.5 \cdot \mathcal{L}_{\text{BCE}} + 0.5 \cdot \mathcal{L}_{\text{Dice}}(\epsilon = 10^{-6})$$
Optimized via AdamW ($\text{lr} = 10^{-4}, \beta_1 = 0.9, \beta_2 = 0.999$, weight decay = $10^{-2}$) with cosine learning rate decay and mixed-precision (AMP) backward scaling.

---

## 4. Dataset & Preprocessing Integrity
Four canonical binary segmentation domains are evaluated under the verified `phase4_v3` manifest version:
- **KUB:** Digital radiography of urinary tract stones ($N_{\text{train}} = 1,978, N_{\text{val}} = 280, 429\text{ patients}$).
- **ISIC:** Dermoscopic skin lesion boundaries ($N_{\text{train}} = 2,556, N_{\text{val}} = 357$).
- **BUSI:** Breast ultrasound masses ($N_{\text{train}} = 602, N_{\text{val}} = 84$).
- **KVASIR:** Endoscopic colorectal polyps ($N_{\text{train}} = 696, N_{\text{val}} = 87$).
- **Strict Leakage Prevention:** Disjoint sample IDs ($5,832 \cap 808 = \emptyset$) and patient IDs verified; all test sets remain locked.

---

## 5. Controlled Experimental Design
The primary endpoint evaluates:
$$\Delta_{\text{mean}} = \frac{1}{3} \sum_{s \in \{42, 123, 3407\}} \left( \text{EqualDomainMacroDice}(C1\text{-}T, s) - \text{EqualDomainMacroDice}(C1\text{-}C, s) \right)$$
where:
$$\text{EqualDomainMacroDice} = \frac{1}{4} \left( \bar{D}_{\text{KUB}} + \bar{D}_{\text{ISIC}} + \bar{D}_{\text{BUSI}} + \bar{D}_{\text{KVASIR}} \right)$$

---

## 6. Quantitative Results (Prospective Schema)
*(To be populated upon authorized execution of the 6 matched C1 training runs).*

| Seed | C1-T Macro Dice | C1-C Macro Dice | Paired $\Delta$ | KUB $\Delta$ | ISIC $\Delta$ | BUSI $\Delta$ | KVASIR $\Delta$ |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 42 | *[Pending]* | *[Pending]* | *[Pending]* | *[Pending]* | *[Pending]* | *[Pending]* | *[Pending]* |
| 123 | *[Pending]* | *[Pending]* | *[Pending]* | *[Pending]* | *[Pending]* | *[Pending]* | *[Pending]* |
| 3407 | *[Pending]* | *[Pending]* | *[Pending]* | *[Pending]* | *[Pending]* | *[Pending]* | *[Pending]* |
| **Mean** | *[Pending]* | *[Pending]* | *[Pending]* | *[Pending]* | *[Pending]* | *[Pending]* | *[Pending]* |

---

## 7. Statistical Analysis & Limitations
- Bootstrapping case sampling (10,000 resamples) conditioned on fixed seed runs isolates data uncertainty from stochastic optimization variance.
- Selection-consumed VAL808 is clearly identified as validation performance, not uncompromised external generalization.
- Distance metrics are presented in pixels due to lack of verified physical millimeter spacing in raw manifests.

---

## 8. Conclusion
The RA-MedFiLM-BARR research package establishes a verified mathematical and statistical foundation for fair multi-domain medical image segmentation, providing an auditable transition path to genuine prospective evidence.
