# ReMedFiLM Canonical Model Identity and Methodology Specification

**Document Version:** 6.0 (Publication Definitive)  
**Date:** November 8, 2026  
**Repository:** `D:\Softfors\jup`  
**Primary Architect:** Principal Medical Imaging Software Architect & Biostatistician  
**Target Publication Venues:** IEEE Transactions on Medical Imaging (TMI) / Medical Image Analysis (MedIA)

---

## 1. Canonical Model Identity and Naming Map

To resolve historical nomenclature variations across early development iterations (Phases 20–29) and ensure 100% cryptographic and scientific traceability, the canonical naming architecture for all future publications, tables, and figures is frozen as follows:

| Component Role | Canonical Publication Name | Repository Class Pointer | Trainable Parameters | Checkpoint Hash (SHA256) | Operational Definition |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Proposed Full System** | **ReMedFiLM (FULL RA-MedFiLM-BARR)** | [`src/models/barr/ra_medfilm_barr.py:RAMedFiLMBARR`](file:///d:/Softfors/jup/src/models/barr/ra_medfilm_barr.py#L22) | **4,837,420** (4.84M) | Composed Assembly | Full 4-component risk-averse regional refinement pipeline. |
| **Global Backbone** | **GlobalMedFiLM ($G$)** | [`src/models/film/global_medfilm.py:GlobalMedFiLM`](file:///d:/Softfors/jup/src/models/film/global_medfilm.py#L31) | **3,523,001** (3.52M) | `4c8d19...3b9e` | Task-conditioned global encoder–decoder and baseline comparator (Arm A0). |
| **Learned Benefit Router** | **Benefit Router ($B_\phi$)** | [`src/models/barr/phase25_models.py:BenefitRouter`](file:///d:/Softfors/jup/src/models/barr/phase25_models.py#L45) | **36,801** (36.8K) | `e2a401...7f1a` | Multi-layer perceptron estimating paired utility $U = \hat{\Delta} - \lambda \cdot C$. |
| **Regional Residual Refiner** | **Regional Refiner ($R_\psi$)** | [`src/models/barr/regional_refiner.py:BARRRegionalRefiner`](file:///d:/Softfors/jup/src/models/barr/regional_refiner.py#L18) | **1,276,401** (1.28M) | `91fc33...8c02` | Dedicated $256 \times 256$ boundary residual logit refiner on cropped ROIs. |
| **Post-Safety Gate** | **Post-Safety Gate ($S_\omega$)** | [`src/models/barr/phase25_models.py:SafetyFilter`](file:///d:/Softfors/jup/src/models/barr/phase25_models.py#L112) | **1,217** (1.2K) | `55d891...0a44` | Divergence classifier gating candidate acceptance ($P(\text{safe}) \ge 0.50$). |
| **Assembly Harness** | **Modular Integration Wrapper** | `RAMedFiLMBARR` | **0** (Zero Params) | N/A | Deterministic execution harness; no joint gradient backpropagation. |

> [!IMPORTANT]
> **Scientific Integrity Requirement:**
> 1. In all figures and text, the proposed system is referred to as **ReMedFiLM** (or **ReMedFiLM (FULL RA-MedFiLM-BARR)**).
> 2. **GlobalMedFiLM** must appear only where it represents the internal backbone, an ablation baseline (Arm A0), or a historical comparator.
> 3. Under no circumstances may a GlobalMedFiLM-only measurement be relabeled as ReMedFiLM.

---

## 2. Complete Mathematical Methodology

### 2.1 Multi-Domain Task-Conditioned Global Backbone ($G$)
The input consists of an RGB medical image $x \in \mathbb{R}^{3 \times 512 \times 512}$ accompanied by a categorical task identifier $t \in \{0, 1, 2, 3\}$, corresponding to:
- $t=0$: ISIC 2018 (Cutaneous dermoscopy lesion)
- $t=1$: BUSI-WHU (Breast ultrasound lesion)
- $t=2$: Kvasir-SEG (Endoscopic gastrointestinal polyp)
- $t=3$: KUB-StoneX (Abdominal plain radiograph urinary stone)

A learned embedding dictionary maps $t$ to a 32-dimensional latent task vector:
$$e_t = E(t) \in \mathbb{R}^{32}$$

In the GlobalMedFiLM encoder–decoder, feature maps $F \in \mathbb{R}^{C \times H \times W}$ at 5 strategic sites (the bottleneck bridge and 4 decoder stages) undergo affine modulation via Feature-wise Linear Modulation (FiLM):
$$\hat{F}_{c,h,w} = \left(1 + \tanh(W_\gamma e_t + b_\gamma)_c\right) \odot F_{c,h,w} + \tanh(W_\beta e_t + b_\beta)_c$$

*Zero-Initialization Guarantee:* Projections $W_\gamma, W_\beta, b_\gamma, b_\beta$ are initialized strictly to zero, ensuring $\hat{F} \equiv F$ at initialization, preventing multi-task gradient collapse. Global output is a spatial probability map $p_{\text{global}} = \sigma(G(x, t)) \in [0, 1]^{512 \times 512}$.

---

### 2.2 Learned Benefit Router ($B_\phi$)
When an ambiguous target is detected ($p_{\text{global}} \ge 0.30$), an ROI bounding box is localized. Feature vector $z_{\text{router}} \in \mathbb{R}^{218}$ is extracted, comprising:
- 202 numerical morphological, intensity, and uncertainty descriptors.
- 16-dimensional task embedding projection.

The benefit router $B_\phi$ regresses the expected paired Dice gain:
$$\hat{\Delta} = B_\phi(z_{\text{router}}) \in \mathbb{R}$$

The net economic utility accounts for secondary refinement compute overhead:
$$U = \hat{\Delta} - \lambda \cdot \text{CostRatio}$$
where $\lambda = 0.25$ and $\text{CostRatio} = \frac{1,051,648\text{ MACs}}{10,270,749\text{ MACs}} \approx 0.10239$.

*Execution Gate:* If $U < \tau_{\text{C8\_final}} \approx -0.024358$ or no valid ROI is detected:
$$\text{Branch} = \text{SKIP\_GLOBAL} \implies p_{\text{final}} = p_{\text{global}}$$
The regional refiner and safety filter are completely bypassed ($31.55\text{ GMACs}$).

---

### 2.3 Regional Residual Refiner ($R_\psi$)
If $U \ge \tau_{\text{C8\_final}}$, a 4-channel $256 \times 256$ crop $[x_{\text{roi}}, p_{\text{roi}}] \in \mathbb{R}^{4 \times 256 \times 256}$ is passed to the regional refiner $R_\psi$. Rather than generating an unconstrained segmentation from scratch, $R_\psi$ predicts a residual logit adjustment:
$$\Delta l_{\text{roi}} = R_\psi([x_{\text{roi}}, p_{\text{roi}}])$$
$$p_{\text{cand\_crop}} = \sigma\left(\text{logit}(p_{\text{roi}}) + \Delta l_{\text{roi}}\right)$$

The refined patch is resized and spatially inserted into the canvas without boundary-blurring $\alpha$-blending:
$$p_{\text{cand}}[y_1:y_2, x_1:x_2] = \text{BilinearResize}(p_{\text{cand\_crop}}, (y_2 - y_1, x_2 - x_1))$$

---

### 2.4 Post-Safety Filter ($S_\omega$) & Fail-Closed Rollback
To guard against secondary refinement hallucinations, feature vector $z_{\text{safety}} \in \mathbb{R}^{20}$ (16 divergence metrics comparing $p_{\text{cand}}$ against $p_{\text{global}}$, plus a 4-d one-hot task vector) is passed to $S_\omega$:
$$P(\text{safe}) = \sigma(S_\omega(z_{\text{safety}}))$$

The definitive three-state execution logic:
1. **Outcome 1: SKIP** $\rightarrow$ Refiner bypassed; $p_{\text{final}} = p_{\text{global}}$ ($31.55\text{ GMACs}$).
2. **Outcome 2: REFINE + ACCEPT** ($P(\text{safe}) \ge 0.50$) $\rightarrow$ $p_{\text{final}} = p_{\text{cand}}$ ($34.72\text{ GMACs}$ amortized).
3. **Outcome 3: REFINE + REJECT** ($P(\text{safe}) < 0.50$) $\rightarrow$ Fail-closed rollback; $p_{\text{final}} = p_{\text{global}}$ ($44.61\text{ GMACs}$).

---

## 3. Staged Freeze Training Strategy

Joint end-to-end backpropagation across multi-task medical segmentation networks frequently induces catastrophic forgetting and negative task transfer. ReMedFiLM was engineered as a 4-stage freeze pipeline:
- **Stage 1 (Global Backbone):** $G$ trained on TRAIN5832 using $\mathcal{L}_{\text{BCE}} + \mathcal{L}_{\text{Dice}}$. Checkpoint frozen.
- **Stage 2 (Regional Refiner):** $R_\psi$ trained on extracted $256 \times 256$ foreground crops with localized boundary loss. Checkpoint frozen.
- **Stage 3 (Benefit Router):** $B_\phi$ trained via 5-fold cross-validation on out-of-fold counterfactual paired gains $\Delta_{\text{Dice}} = \text{Dice}_{\text{cand}} - \text{Dice}_{\text{global}}$. Checkpoint frozen.
- **Stage 4 (Post-Safety Gate):** $S_\omega$ trained on post-refinement divergence features to classify $\mathbb{I}(\Delta_{\text{Dice}} > 0)$. Checkpoint frozen.
- **Assembly Wrapper:** 0 trainable parameters; connects the frozen checkpoints into a single deterministic inference graph.
