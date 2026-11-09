# Phase 15 — Regional Refiner Segmentation Loss Study: Prospective Protocol (Part 0C Final)
# Phase 15 — Regional Refiner Segmentation Loss Study: Prospective Protocol (Part 0D Final)

**Phase:** 15  
**Part:** 0C — Final Loss-Semantics Audit Before Training  
**Part:** 0D — L3 Derivative Correction & Final Pre-Training Freeze  
**Status:** `PROTOCOL_FROZEN_AWAITING_SUPERVISOR_AUTHORIZATION`  
**Model:** Gemini 3.1 Pro High  
**Interpreter:** `D:\Softfors\jup\.venv\Scripts\python.exe`  

---

## 1. Scientific Context & Corrected Rationale

In Phase 14, the regional refiner network demonstrated high performance under Oracle localization ($100\%$ Tiny stone detection, $+16.2\%$ macro Dice gain), and retained $50.0\%$ of its stone-recovery signal under frozen Stage-4D localizer proposals. However, downstream predicted-regional inference suffered from false-positive background clutter outside stone targets (mean $5.43$ FP components/image vs $0.37$ baseline), leading to overall full-field Dice degradation.

### Scientific Question
Can an alternative segmentation loss improve regional-refiner crop segmentation quality, boundary fidelity, or small/tiny stone detection behavior compared to the Phase-14 baseline loss, while strictly isolating loss formulation as the sole independent variable across identical architecture, data splits, crop geometry, and optimization schedules?

### Experimental Principle
Phase 15 is **strictly controlled**. Only the loss function formulation will vary. All non-loss experimental variables—including neural architecture, dataset splits, A3 crop augmentation, optimizer parameters, learning rate schedule, seed, and evaluation populations—remain completely fixed to their Phase-14 canonical values.

---

## 2. Experimental Control (L0)

- **Identifier:** `L0`
- **Name:** Balanced Binary Cross-Entropy + Soft Dice (`0.5 BCE + 0.5 SoftDice`)
- **Experiment ID:** `phase14_diag_regional_unet_oracletrain_a3_seed42_v1`
- **Checkpoint Path:** `checkpoints/phase14_diag_regional_unet_oracletrain_a3_seed42_v1/best.pt`
- **Checkpoint SHA-256:** `89ada72700385ed56b49b6caf34d9061349c24a566794176911b83fb0c8cd9f0`
- **Baseline Performance:**
  - Best epoch: 14
  - Validation Crop Dice (Oracle VAL): $0.8437233057743712$
  - FULL_FIELD Oracle Dice: $0.815175$
  - FULL_FIELD Predicted Dice: $0.383905$
  - Oracle Tiny Object Recall: $73 / 73$ ($1.000$)
  - Predicted Tiny Object Recall: $65 / 73$ ($0.8904109589041096$)
- **Retraining Policy:** L0 will **not** be retrained. Prior to training alternatives, numerical equivalence between the Phase-15 L0 implementation and the Phase-14 baseline was verified on fixed reference tensors.

---

## 3. Alternative Loss Suite & Verified Semantic Audits

The candidate loss suite is bounded to exactly three prospectively fixed alternatives targeting specific segmentation challenges in regional radiograph crops:

### Loss 1 (L1): Binary Focal + Soft Dice (`Focal_Dice`)
- **Experiment ID:** `phase15_regional_loss_focaldice_seed42_v1`
- **Family:** Hard-Negative Mining & Background Suppression
- **Verified Source Implementation:**
  ```python
  p = torch.sigmoid(logits)
  p_t = targets * p + (1.0 - targets) * (1.0 - p)
  alpha_t = targets * self.alpha + (1.0 - targets) * (1.0 - self.alpha)
  loss = -alpha_t * torch.pow(1.0 - p_t, self.gamma) * torch.log(torch.clamp(p_t, min=1e-7, max=1.0))
  ```
- **Verified Alpha Semantics:**
  - On positive stone pixels ($y=1$): $\alpha_t = \alpha = 0.25$.
  - On negative background pixels ($y=0$): $\alpha_t = 1 - \alpha = 0.75$.
  - Modulating factor: $(1 - p_t)^\gamma = (1 - p_t)^{2.0}$.
- **Corrected Scientific Rationale:** Because background tissue pixels constitute over $99\%$ of a crop, the background weighting $\alpha_t = 0.75$ coupled with $(1 - p_t)^{2.0}$ strongly suppresses loss contributions from confident, easy background pixels while heavily penalizing confident false-positive background pixels. This focuses gradients on ambiguous anatomical tissue borders and difficult stone/background pixels, potentially reducing **FALSE REGIONAL FOREGROUND** within predicted proposal crops. It does **NOT** modify proposal count, proposal geometry, Stage-4D localization, NMS, or TopK (which remain strictly frozen).
- **Mathematical Formula:**
  $$\mathcal{L}_{1} = 0.5 \cdot \mathcal{L}_{\text{Focal}}(z, y) + 0.5 \cdot \mathcal{L}_{\text{Dice}}(\sigma(z), y)$$
- **Fixed Constants:** $\alpha = 0.25$, $\gamma = 2.0$, $\epsilon = 10^{-6}$, weight ratio $0.5 : 0.5$, reduction: `mean`.

### Loss 2 (L2): Asymmetric Tversky Loss (`Tversky`)
- **Experiment ID:** `phase15_regional_loss_tversky_seed42_v1`
- **Family:** Asymmetric Precision/Recall Regularization
- **Verified Source Implementation:**
  ```python
  ti = (tp + self.epsilon) / (tp + self.alpha * fp + self.beta * fn + self.epsilon)
  loss = 1.0 - ti
  ```
- **Verified Weights Convention:**
  - $\alpha = 0.30$ weights **FALSE POSITIVES** (`self.alpha * fp`).
  - $\beta = 0.70$ weights **FALSE NEGATIVES** (`self.beta * fn`).
  - Convention is verified: $\beta = 0.70 > \alpha = 0.30$ directly emphasizes recall over precision.
- **Scientific Rationale:** Inside $256 \times 256$ regional crops, Tiny and Small stones occupy a minute fraction ($< 0.1\%$) of foreground pixels. Asymmetric Tversky penalization weights False Negatives more heavily than False Positives ($\beta = 0.70$ vs $\alpha = 0.30$), directly penalizing missed stone boundaries and boosting small-target sensitivity without post-hoc threshold shifting.
- **Mathematical Formula:**
  $$\mathcal{L}_{2} = 1.0 - \text{TI}(z, y)$$
- **Fixed Constants:** $\alpha = 0.30$, $\beta = 0.70$, $\epsilon = 10^{-6}$, reduction: `mean`.

### Loss 3 (L3): Focal Tversky Loss (`Focal_Tversky`)
- **Experiment ID:** `phase15_regional_loss_focaltversky_seed42_v1`
- **Family:** Non-linear Tversky Reshaping with Boundary Refinement Emphasis
- **Family:** Non-linear Tversky Reshaping with High-Overlap Sensitivity
- **Exact Implemented Formula:**
  $$\mathcal{L}_{3} = (1.0 - \text{TI})^\gamma, \quad \text{where } \gamma = 0.75$$
- **Mathematical Gradient Derivation:**
  $$\frac{d\mathcal{L}_3}{d\text{TI}} = -\gamma (1 - \text{TI})^{\gamma - 1} = -0.75 (1 - \text{TI})^{-0.25} = -\frac{0.75}{(1 - \text{TI})^{0.25}}$$
  $$\left| \frac{d\mathcal{L}_3}{d\text{TI}} \right| = \frac{0.75}{(1 - \text{TI})^{0.25}}$$
- **Derivative Magnitude at Representative TI Values:**
  - $\text{TI} = 0.00 \implies \left| \frac{d\mathcal{L}_3}{d\text{TI}} \right| = 0.7500 \quad (\mathcal{L}_3 = 1.0000)$
  - $\text{TI} = 0.25 \implies \left| \frac{d\mathcal{L}_3}{d\text{TI}} \right| = 0.8059 \quad (\mathcal{L}_3 = 0.8059)$
  - $\text{TI} = 0.50 \implies \left| \frac{d\mathcal{L}_3}{d\text{TI}} \right| = 0.8919 \quad (\mathcal{L}_3 = 0.5946)$
  - $\text{TI} = 0.75 \implies \left| \frac{d\mathcal{L}_3}{d\text{TI}} \right| = 1.0607 \quad (\mathcal{L}_3 = 0.3536)$
  - $\text{TI} = 0.90 \implies \left| \frac{d\mathcal{L}_3}{d\text{TI}} \right| = 1.3337 \quad (\mathcal{L}_3 = 0.1778)$
  - $\text{TI} = 0.99 \implies \left| \frac{d\mathcal{L}_3}{d\text{TI}} \right| = 2.3717 \quad (\mathcal{L}_3 = 0.0316)$
- **Correct Mathematical Gradient Derivation:**
  $$\frac{d\mathcal{L}_3}{d\text{TI}} = -\gamma (1 - \text{TI})^{\gamma - 1} = -0.75 (1 - \text{TI})^{-0.25}$$
  $$\left| \frac{d\mathcal{L}_3}{d\text{TI}} \right| = 0.75 (1 - \text{TI})^{-0.25} = \frac{0.75}{(1 - \text{TI})^{0.25}}$$
- **Derivative Magnitude at Representative TI Values (Verified by Autograd to $< 10^{-10}$):**
  - $\text{TI} = 0.00 \implies \left| \frac{d\mathcal{L}_3}{d\text{TI}} \right| = 0.750000 \quad (\mathcal{L}_3 = 1.000000)$
  - $\text{TI} = 0.25 \implies \left| \frac{d\mathcal{L}_3}{d\text{TI}} \right| = 0.805927 \quad (\mathcal{L}_3 = 0.805927)$
  - $\text{TI} = 0.50 \implies \left| \frac{d\mathcal{L}_3}{d\text{TI}} \right| = 0.891905 \quad (\mathcal{L}_3 = 0.594604)$
  - $\text{TI} = 0.75 \implies \left| \frac{d\mathcal{L}_3}{d\text{TI}} \right| = 1.060660 \quad (\mathcal{L}_3 = 0.353553)$
  - $\text{TI} = 0.90 \implies \left| \frac{d\mathcal{L}_3}{d\text{TI}} \right| = 1.333710 \quad (\mathcal{L}_3 = 0.177828)$
  - $\text{TI} = 0.99 \implies \left| \frac{d\mathcal{L}_3}{d\text{TI}} \right| = 2.371708 \quad (\mathcal{L}_3 = 0.031623)$
- **Mathematical Interpretation & Corrected Rationale:**
  Because $\gamma = 0.75 < 1$, the derivative magnitude $\left| \frac{d\mathcal{L}_3}{d\text{TI}} \right|$ increases monotonically as $\text{TI} \to 1.0$ (from $0.75$ at $\text{TI}=0$ to $2.37$ at $\text{TI}=0.99$). Therefore, $\gamma = 0.75$ does **NOT** amplify gradients at low overlap; rather, it **amplifies gradient sensitivity in the high-overlap boundary-refinement regime ($\text{TI} \ge 0.75$)** where linear Tversky gradients would otherwise taper off. This forces the refiner to sharply tune boundary contours for already-localized stones, while inheriting the small-stone recall orientation from $\beta = 0.70$.
- **Parameter Defense:** $\gamma = 0.75$ is scientifically defensible and retained under this exact formulation because it establishes a unique high-overlap boundary-refinement inductive bias distinctly complementary to L2 linear Tversky and L1 pixel-wise focal suppression.
  Because $\gamma = 0.75 < 1$ in $\mathcal{L} = (1 - \text{TI})^\gamma$, the magnitude of $\frac{d\mathcal{L}}{d\text{TI}}$ increases as $\text{TI}$ approaches $1$ (from $0.750000$ at $\text{TI}=0.00$ to $2.371708$ at $\text{TI}=0.99$). Therefore, this formulation emphasizes incremental refinement in the high-overlap regime relative to standard Tversky loss. It does **NOT** preferentially amplify the gradient when $\text{TI} \ll 1$.
  - *Preferred scientific rationale:* "The $\gamma=0.75$ transformation nonlinearly reshapes Tversky loss so that sensitivity with respect to $\text{TI}$ increases as overlap approaches 1, while the $\alpha=0.30$ / $\beta=0.70$ Tversky term retains FN-heavy recall weighting."
- **Parameter Defense:** $\gamma = 0.75$ is scientifically defensible and retained under this exact formula because it establishes a unique high-overlap sensitivity distinct from linear Tversky (L2) and pixel-wise focal suppression (L1).
- **Fixed Constants:** $\alpha = 0.30$, $\beta = 0.70$, $\gamma = 0.75$, $\epsilon = 10^{-6}$, reduction: `mean`.

---

## 4. Negative-Crop Behavior Audit

A3 training inventory contains $1,542$ pure background negative crops (target mask has zero foreground pixels):
- **L0 (BCE + Dice):** BCE term provides active, non-zero gradient (norm $\approx 0.0275$) penalizing any predicted false-positive foreground. Dice term evaluates to $1.0$ with zero gradient. Combined L0 actively trains background suppression on negative crops.
- **L1 (Focal + Dice):** Focal term provides active, non-zero gradient (norm $\approx 0.0252$) penalizing false-positive pixels with $\alpha_t = 0.75$ and $(1 - p_t)^{2.0}$. Dice term evaluates to $1.0$ with zero gradient. Combined L1 actively trains background suppression on negative crops.
- **L2 (Tversky):** When target is pure zero, $\text{TP} = 0$ and $\text{FN} = 0$. $\text{TI} = \frac{\epsilon}{\alpha \cdot \text{FP} + \epsilon} \approx 0$. Tversky loss evaluates to $1.0$ with near-zero gradient (norm $\approx 10^{-9}$).
- **L3 (Focal Tversky):** Similarly evaluates to $(1.0 - 0)^{0.75} = 1.0$ with near-zero gradient on pure negative crops (norm $\approx 10^{-9}$).

**Scientific Assessment:**  
This asymmetry is an inherent, mathematically authentic property of pure overlap losses (Dice/Tversky) versus compound distribution+overlap losses (BCE+Dice, Focal+Dice). In A3 training, negative crops are batched alongside positive crops (batch size 8). For L2 and L3, negative crops act as passive non-interfering distractors, whereas L0 and L1 actively backpropagate background suppression. This constitutes a fundamental scientific comparison between compound losses and pure asymmetric overlap losses in Phase 15. No artificial hacks or code modifications will be introduced; the comparison reflects authentic loss behavior.

---

## 5. Numerical Semantics Unit Test Provenance

Verified via [`scripts/evaluation/test_loss_definitions.py`](file:///D:/Softfors/jup/scripts/evaluation/test_loss_definitions.py) across deterministic synthetic tensors:
1. **Perfect Prediction:** L0=$0.0000$, L1=$0.0000$, L2=$0.0000$, L3=$0.0006$
2. **All-Background Prediction:** L0=$3.0000$, L1=$1.1249$, L2=$0.9999$, L3=$1.0000$
3. **All-Foreground Prediction:** L0=$2.6667$, L1=$2.0414$, L2=$0.2308$, L3=$0.3330$
4. **One TP / One FN:** L0=$1.4167$, L1=$0.4791$, L2=$0.4118$, L3=$0.5140$
5. **One TP / One FP:** L0=$1.4167$, L1=$1.1041$, L2=$0.2308$, L3=$0.3330$
6. **Mixed Logits:** L0=$0.2996$, L1=$0.1463$, L2=$0.2937$, L3=$0.3989$
1. **Autograd Agreement on L3 Derivative:** Evaluated at $\text{TI} \in \{0.00, 0.25, 0.50, 0.75, 0.90, 0.99\}$. Analytic $|d\mathcal{L}/d\text{TI}| = 0.75(1 - \text{TI})^{-0.25}$ matches PyTorch autograd to $0.0 \times 10^{-10}$ difference.
2. **Perfect Prediction:** L0=$0.0000$, L1=$0.0000$, L2=$0.0000$, L3=$0.0006$
3. **All-Background Prediction:** L0=$3.0000$, L1=$1.1249$, L2=$0.9999$, L3=$1.0000$
4. **All-Foreground Prediction:** L0=$2.6667$, L1=$2.0414$, L2=$0.2308$, L3=$0.3330$
5. **One TP / One FN:** L0=$1.4167$, L1=$0.4791$, L2=$0.4118$, L3=$0.5140$
6. **One TP / One FP:** L0=$1.4167$, L1=$1.1041$, L2=$0.2308$, L3=$0.3330$
7. **Mixed Logits:** L0=$0.2996$, L1=$0.1463$, L2=$0.2937$, L3=$0.3989$

All losses evaluate to finite, numerically stable values in $100\%$ alignment with their mathematical formulations.

---

## 6. Predefined Success Decision Rule & Selection Hierarchy

A candidate loss $L_k$ ($k \in \{1, 2, 3\}$) will be declared superior to $L_0$ IF AND ONLY IF:
1. **Primary Crop Gain:**
   $$\text{Val Crop Dice}(L_k) \ge \text{Val Crop Dice}(L_0) + 0.010 = 0.8537233057743712$$
   **OR**
   $$\text{Tiny Crop Dice}(L_k) \ge \text{Tiny Crop Dice}(L_0) + 0.020 \quad \text{with overall Crop Dice degradation } \le 0.005.$$
2. **Secondary Stability Constraint:**
   $$\text{FULL\_FIELD } D_p(L_k) \ge D_p(L_0) - 0.010 = 0.373905$$
   $$\mathbf{AND}$$
   $$\text{Predicted Tiny Object Recall } T_p(L_k) \ge \mathbf{62 / 73} = \mathbf{0.8493150684931506}$$
   *(Interpretation: $L_0$ detected $65/73$ Tiny components; an acceptable candidate loss may lose at most $3$ Tiny detections).*

### Deterministic Selection Hierarchy
If multiple alternative losses satisfy the success rule, selection proceeds deterministically without subjective weighting:
1. **Highest Macro Oracle VAL Crop Dice**
2. **If tied within $0.001$ ($10^{-3}$), higher Tiny Crop Dice**
3. **If still tied within $0.001$, higher FULL_FIELD Predicted Dice ($D_p$)**
4. **If still tied within $0.001$, lower mean False-Positive components per image**

**Fallback Policy:**  
If no candidate loss satisfies both criteria, $L_0$ (`0.5 BCE + 0.5 SoftDice`) is formally retained as the canonical regional-refiner loss. A null or negative comparative outcome is fully acceptable and scientifically informative.

---

## 7. Scientific Notebook Specifications

Phase 15 includes two canonical notebooks:

### Notebook A — Main Loss Study Analysis
- **Path:** `notebooks/14_phase15_loss_study.ipynb`
- **Purpose:** Rigorous scientific evaluation of the controlled loss comparison, documenting loss formulas, training convergence curves, best epochs, crop metrics by stratum, secondary full-field checks, hard-case recovery, gate hierarchy evaluation, and artifact registries.
- **Governance:** Executable, read-only analysis of persisted checkpoints; no in-notebook training loops; 0 errors; SHA-256 recorded.

### Notebook B — 75-Case VAL Prediction Visual Gallery
- **Path:** `notebooks/14b_phase15_val_prediction_gallery.ipynb`
- **Purpose:** Large-scale visual inspection of model predictions on $75$ deterministic FULL_FIELD VAL cases across $5$ paginated visual chapters ($15$ cases/page).
- **Population:** Strictly **KUB FULL_FIELD VAL**. Touch of the untouched TEST split is strictly forbidden.
- **Deterministic Selection Rule:** All $106$ FULL_FIELD VAL images are ranked deterministically by the SHA-256 hash of `hash = SHA256('phase15_gallery_seed42|' + sample_id)`. The first $75$ ranked cases are selected. Frozen at [`reports/tables/phase15_val_gallery_selection.csv`](file:///D:/Softfors/jup/reports/tables/phase15_val_gallery_selection.csv) (SHA-256: `e89ea839783fd27d46892c5c8fa0f35da48b969eb6e4d4f12516a5863ef225ed`).
- **Hard-Case Appendix:** Clearly separated appendix displaying the $16$ Hard-Tiny components and $7$ Global-Empty images, strictly distinct from the unbiased $75$-case cohort.

---

## 8. Governance & Security Locks

- **Training Authorized in Part 0C:** **NO**
- **Inference Authorized in Part 0C:** **NO**
- **Optimizer Steps in Part 0C:** **0**
- **Training Authorized in Part 0D:** **NO**
- **Inference Authorized in Part 0D:** **NO**
- **Optimizer Steps in Part 0D:** **0**
- **Test Content Reads:** **0**
- **Test Metrics Evaluated:** **NONE**
- **Test Visualizations:** **0**
- **External Data Used:** **NO**
- **Experiment A Modified:** **NO**
- **Phase 16 Status:** **NOT_STARTED**
- **Next Step:** `WAIT_FOR_SUPERVISOR_REVIEW`
