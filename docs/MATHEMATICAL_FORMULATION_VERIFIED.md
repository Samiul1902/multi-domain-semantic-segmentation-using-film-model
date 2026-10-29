# RA-MedFiLM-BARR: Verified Mathematical Formulation

**Status:** VERIFIED FROM SOURCE (not from R3 spec prose)  
**Source inspected:** `src/models/film/global_medfilm.py`, `src/models/barr/ra_medfilm_barr.py`, `src/models/barr/regional_refiner.py`, `src/research/c1_film/control.py`  
**Date:** 2026-10-29  
**Purpose:** Manuscript §4 (Mathematical Formulation) — use ONLY these verified equations

---

## 1. Notation

| Symbol | Meaning |
|---|---|
| $x \in \mathbb{R}^{H \times W \times C_{\text{in}}}$ | Input image |
| $t \in \{0,1,2,3\}$ | Task ID (ISIC=0, BUSI=1, KVASIR=2, KUB=3) |
| $\mathbf{e}_t \in \mathbb{R}^{32}$ | Task embedding vector |
| $F_\ell \in \mathbb{R}^{H_\ell \times W_\ell \times C_\ell}$ | Feature map at site $\ell$ |
| $\hat{F}_\ell$ | Modulated feature map at site $\ell$ |
| $G$ | GlobalMedFiLM (shared backbone + FiLM conditioning) |
| $R_\psi$ | BARRRegionalRefinerV1 (crop-trained, frozen after Phase-25A) |
| $B_\phi$ | BARRBenefitRouterV1 (benefit router, frozen after Phase-25C) |
| $S_\omega$ | BARRPostSafetyV1 (post-safety gate) |

---

## 2. Global FiLM Conditioning (G)

### 2.1 Encoder-Decoder architecture

GlobalMedFiLM is a shared residual U-Net with:
- **Channels:** (24, 48, 96, 192, 256) at encoder stages 1–5
- **Residual blocks:** Conv3×3 → GroupNorm → SiLU → Conv3×3 → GroupNorm → (+skip) → SiLU
- **GroupNorm groups:** 8 (for all widths used here)
- **No squeeze-and-excitation, no deep supervision, no per-task heads**
- **One shared 1×1 output head** → single foreground logit per pixel

### 2.2 FiLM modulation equation

At each of the 5 FiLM sites (bridge, decoder4, decoder3, decoder2, decoder1):

$$\hat{F}_\ell = \bigl(1 + \gamma_\ell(t)\bigr) \cdot F_\ell + \beta_\ell(t)$$

where the modulation parameters are:

$$\gamma_\ell(t) = \tanh\!\bigl(\gamma^\text{raw}_\ell(t)\bigr), \quad \beta_\ell(t) = \tanh\!\bigl(\beta^\text{raw}_\ell(t)\bigr)$$

and $\gamma^\text{raw}_\ell(t), \beta^\text{raw}_\ell(t)$ are produced by a 2-layer MLP applied to the task embedding:

$$[\gamma^\text{raw}_\ell,\; \beta^\text{raw}_\ell] = W_\ell^{(2)} \cdot \sigma\!\bigl(W_\ell^{(1)} \mathbf{e}_t + b_\ell^{(1)}\bigr) + b_\ell^{(2)}$$

where $W_\ell^{(1)} \in \mathbb{R}^{64 \times 32}$ (hidden dim 64), $W_\ell^{(2)} \in \mathbb{R}^{2C_\ell \times 64}$, and $\sigma$ is SiLU.

**Key property — zero initialization:** $W_\ell^{(2)} = \mathbf{0}$, $b_\ell^{(2)} = \mathbf{0}$ at initialization.  
Therefore at $t=0$: $\gamma_\ell = \mathbf{0}$, $\beta_\ell = \mathbf{0}$, $\hat{F}_\ell = F_\ell$ (exact identity).  
FiLM conditioning is *learned* from this identity starting point.

**Tanh bounding:** $\gamma_\ell, \beta_\ell \in (-1, 1)^{C_\ell}$ by construction, protecting early training.

### 2.3 C1 control arm identity condition

For the C1-C control arm, conditioning parameters are frozen at their zero-initialized values:
$$\gamma_\ell(t) = \mathbf{0}, \quad \beta_\ell(t) = \mathbf{0} \quad \forall t, \ell$$
$$\Rightarrow \hat{F}_\ell = F_\ell \quad \text{(exact identity at every site)}$$

Verified computationally by `verify_identity_control()` before each run.

### 2.4 Parameter accounting (verified from source)

| Group | Parameters |
|---|---|
| Total | 3,523,001 |
| Conditioning (task_embedding + film_layers) | 90,768 |
| Backbone | 3,432,233 |
| C1-T trainable | 3,523,001 |
| C1-C trainable | 3,432,233 (backbone only; conditioning frozen) |

---

## 3. Regional Refiner ($R_\psi$)

### 3.1 Input / Output

- Input: $B \times 4 \times 256 \times 256$ = $[R, G, B, p_\text{global,crop}]$
- Output: $B \times 1 \times 256 \times 256$ raw logits (no internal sigmoid)

### 3.2 Architecture

5-stage residual encoder-decoder, channels: (16, 32, 64, 96, 128).  
GroupNorm (max-8 groups), SiLU activations.  
**No task FiLM, no attention, no SE blocks, no dropout, no pretrained encoder.**  
Expected parameters: **1,276,401** (closed form, verified).

### 3.3 Forbidden modules (by construction)

SE blocks, attention, transformer, pretrained encoder, foundation model, deep supervision, task FiLM, dropout, learned fusion.

---

## 4. Benefit Router ($B_\phi$) and Utility Function

### 4.1 Runtime utility

$$U = \hat{\delta}_\text{final} - \lambda \cdot C_\text{action}$$

where:
- $\hat{\delta}_\text{final}$: predicted benefit (Dice gain from regional refinement)
- $\lambda = 1/4$ (exact rational, hardcoded)
- $C_\text{action} = 1051648 / 10270749$ (exact rational, hardcoded)
- $\lambda C_\text{action} = 1051648 / 41082996$ (exact rational)

### 4.2 Decision threshold

$$\tau_\text{C8,final} = \frac{24796109646558761}{20000000000000000000} - \lambda C_\text{action}$$

$$= \frac{-5003565381643716252018011}{205414980000000000000000000}$$

The float constant `TAU_C8_FINAL_FLOAT` in source is a deterministic adequate-precision implementation of this exact rational.

### 4.3 Decision rule

$$\text{action} = \begin{cases} \text{EXECUTE} & U \geq \tau_\text{C8,final} \\ \text{SKIP} & U < \tau_\text{C8,final} \end{cases}$$

### 4.4 System state machine

| State | Condition | Output |
|---|---|---|
| FORCED_SKIP | Action unavailable (no ROI) | $p_\text{global}$ |
| SKIP_GLOBAL | $U < \tau_\text{C8,final}$ | $p_\text{global}$ |
| EXECUTE_THEN_ACCEPT | $U \geq \tau$ and $S_\omega$ accepts | Regional candidate |
| EXECUTE_THEN_REJECT | $U \geq \tau$ and $S_\omega$ rejects | $p_\text{global}$ |

---

## 5. Training Objective (C1)

**Loss function (from source `src/losses/segmentation.py`):**

$$\mathcal{L} = \mathcal{L}_\text{BCE} + \mathcal{L}_\text{Dice}$$

BCEDiceLoss with equal weighting (1.0 each). No focal loss, no multi-scale supervision.

**Optimizer:** AdamW, lr=1e-4, weight_decay=1e-4 (one group; frozen parameters excluded).  
**Scheduler:** CosineAnnealingLR.  
**Checkpoint selection:** pre-declared best-epoch rule from `src/training/phase20_selection.py` (equal-domain macro Dice on VAL; frozen, not reselected post-hoc).

---

## 6. C1 Estimand (primary analysis)

**Design:** Matched paired attribution study.

For task $d \in \{$ISIC, BUSI, KVASIR, KUB$\}$ and seed $s \in \{42, 123, 3407\}$:

$$\Delta_d(s) = \text{Dice}_{d,\text{C1-T}}(s) - \text{Dice}_{d,\text{C1-C}}(s)$$

**Primary estimand (equal-domain macro average):**

$$\Delta_\text{C1} = \frac{1}{4} \sum_{d} \frac{1}{3} \sum_{s} \Delta_d(s)$$

**Uncertainty:** 10,000 case-sampling bootstrap (PCG64 seed 20261027), paired domain-stratified, patient-clustered for KUB.  
95th percentile interval.

**Scope:** Development evidence only (TRAIN=5832, VAL=808, phase4\_v3 manifests).  
VAL-808 is selection-consumed. Not independent generalization. Not clinical benefit.

---

## 7. What the Manuscript Must NOT Claim

- $\hat{F} = \gamma \cdot F + \beta$ without tanh — INCORRECT for this model
- Raw affine FiLM (no zero-init) — INCORRECT for this model
- C2/C3 as prospective evidence unless separately established
- VAL-808 as independent test generalization
- Clinical benefit (outside study scope)
- Historical v2 results as clean-v3 evidence

