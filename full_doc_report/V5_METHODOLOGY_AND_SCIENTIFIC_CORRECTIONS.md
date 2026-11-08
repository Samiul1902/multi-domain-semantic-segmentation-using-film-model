# V5 Methodology and Scientific Corrections Audit
## RA-MedFiLM-BARR: Master Report V5 Scientific Upgrade & Reconciliation Audit

This audit document records the systematic corrections, architecture refactorings, and evidentiary reconciliations implemented between Report V4 and Report V5, satisfying all Task 1–Task 8 requirements.

---

### 1. Primary Proposed Model Naming & Architectural Identity
* **V4 Inconsistency**: In several introductory sections and figure descriptions in V4, the method was loosely introduced as "RA-MedFiLM-BARR" but described predominantly through its internal global backbone (GlobalMedFiLM), creating ambiguity as to whether GlobalMedFiLM or the full pipeline was the central proposed model.
* **Verified Repository Evidence**:
  - `src/models/barr/ra_medfilm_barr.py`: Defines `RAMedFiLMBARR`, the canonical full assembly composing:
    1. `GlobalMedFiLM` ($G$, 3,523,001 params)
    2. `BARRRegionalRefinerV1` ($R_\psi$, 1,276,401 params)
    3. `BARRBenefitRouterV1` ($B_\phi$, 36,801 params)
    4. `BARRPostSafetyV1` ($S_\omega$, 1,217 params)
  - Total proposed model parameter count is **4,837,420 parameters** (4.84M).
  - The historical alias **ReMedFiLM** (Residual Medical FiLM) appears in early development documents as the preliminary name for this multi-stage system before the formal canonical standardization as **RA-MedFiLM-BARR**.
* **V5 Correction**: 
  - The proposed model is unequivocally defined across all sections as **FULL RA-MedFiLM-BARR** (composed 4-component system).
  - **GlobalMedFiLM** is strictly designated as the **internal task-conditioned global backbone** and the primary ablation comparator.

---

### 2. Staged Freeze vs. Joint End-to-End Training
* **V4 Inconsistency**: V4 occasionally referred to the system in ways that could imply a jointly trained, single-loss architecture.
* **Verified Repository Evidence**:
  - `src/models/barr/ra_medfilm_barr.py` explicitly enforces: `OPERATIONAL MEANING: ASSEMBLY_ONLY__NO_PARAMETER_OPTIMIZATION`.
  - The integration wrapper introduces **0 trainable parameters** (`trainable_parameter_count == 0`).
  - There is no joint backward graph or shared multi-task loss spanning $G$, $R_\psi$, $B_\phi$, and $S_\omega$.
  - The training is staged in 4 distinct phases:
    1. Stage 1 (Phase 21): GlobalMedFiLM trained on TRAIN5832 with $\mathcal{L}_{\text{BCE}} + \mathcal{L}_{\text{Dice}}$. Checkpoint frozen.
    2. Stage 2 (Phase 25A): Regional Refiner ($R_\psi$) trained on 256x256 crops with boundary loss. Checkpoint frozen.
    3. Stage 3 (Phase 25D): Benefit Router ($B_\phi$) trained via 5-fold cross-fit on out-of-fold counterfactual paired gains $\Delta_{\text{Dice}}$. Checkpoint frozen.
    4. Stage 4 (Phase 25F): Post-Safety Gate ($S_\omega$) trained as a binary classifier for $\mathbb{I}(\Delta_{\text{Dice}} > 0)$. Checkpoint frozen.
* **V5 Correction**:
  - The architecture is explicitly presented as a **staged freeze modular composition**.
  - Panel C of Figure 1 diagrams the 4 separate training objectives and dashed training dependencies.
  - The text explicitly disclaims end-to-end backpropagation, highlighting this modularity as a defensive engineering property that prevents catastrophic gradient interference.

---

### 3. Benefit Router Formulation & Decision Thresholds
* **V4 Inconsistency**: V4 simplified the routing threshold as a generic $\tau$, omitting the exact resource-aware utility formulation.
* **Verified Repository Evidence**:
  - `src/models/barr/ra_medfilm_barr.py`:
    $$\text{Utility } U = \hat{\Delta}_{\text{final}} - \lambda \cdot C_{\text{action}}$$
    where $\lambda = \frac{1}{4}$ and $C_{\text{action}} = \frac{1051648}{10270749}$.
  - Canonical execution threshold:
    $$\tau_{\text{C8\_final}} = -\frac{5003565381643716252018011}{205414980000000000000000000} \approx -0.024358$$
  - Decision rule:
    $$\text{Action} = \begin{cases} \text{EXECUTE}, & \text{if } U \ge \tau_{\text{C8\_final}} \\ \text{SKIP}, & \text{if } U < \tau_{\text{C8\_final}} \end{cases}$$
* **V5 Correction**:
  - Figure 1 and Section 2 now document the exact closed-form rational utility equation and threshold.

---

### 4. Regional Fusion Mechanism
* **V4 Inconsistency**: V4 did not specify the exact pixel recomposition rule, leaving room to confuse it with alpha blending or soft sigmoid mixing.
* **Verified Repository Evidence**:
  - `RAMedFiLMBARR._fuse_global_with_regional`:
    * Deterministic spatial insertion into the 512x512 canvas.
    * Outside the bounding window $(y_0:y_1, x_0:x_1)$, pixels remain $p_{\text{global}}$.
    * Inside the bounding window, pixels are replaced by the resized refined crop $p_{\text{refined\_crop}}$.
    * Explicit comment in code: `NO alpha blending`.
* **V5 Correction**:
  - Inset 2 of Figure 1 and Section 2 explicitly specify deterministic spatial insertion without alpha blending.

---

### 5. Post-Safety Gate Decision & Fail-Closed Fallback
* **V4 Inconsistency**: V4 described safety gating generally without specifying feature dimensionality or fallback semantics.
* **Verified Repository Evidence**:
  - `BARRPostSafetyV1`: 20-dimensional input (16 numeric divergence features + 4-d task one-hot).
  - Three linear layers: $20 \rightarrow 32 \rightarrow 16 \rightarrow 1$ (1,217 parameters).
  - Safety acceptance probability: $P(\text{accept}) = \sigma(\text{logit})$.
  - Threshold: $\tau_{\text{safe}} = 0.50$.
  - Three canonical runtime outcomes:
    1. `SKIP_GLOBAL` (or `FORCED_SKIP`) $\rightarrow p_{\text{global}}$ (Refiner and Safety never run).
    2. `EXECUTE_THEN_ACCEPT` $\rightarrow p_{\text{fused}}$ (candidate mask accepted).
    3. `EXECUTE_THEN_REJECT` $\rightarrow p_{\text{global}}$ (candidate discarded, safe fallback).
* **V5 Correction**:
  - Figure 1 and Section 2 illustrate all three distinct inference outcomes with explicit branch paths.

---

### 6. Verification of Subgroup & Radiography Full-Field vs. ROI Status
* **V4 Inconsistency**: Some captions did not clearly reiterate the full-field nature of displayed KUB images.
* **Verified Repository Evidence**:
  - `val.csv` contains 280 KUB validation samples.
  - The repository stores both full-field radiographs (873 images) and cropped ROI instances (1,385 patches).
  - The four displayed cases in Figure 8 are confirmed full-field radiographs (`patient-00401`, `patient-00366`, `patient-00388`).
* **V5 Correction**:
  - Explicit labeling of full-field radiographs vs ROI instances confirmed in both figures and text.

---

### 7. Preservation of Negative Findings & Research Gaps
* **Audit Confirmation**:
  - The severe **14/14 false-positive detection failure** on stone-free radiographs (`Stones_where_are_you`, mean Dice 0.000) is retained and prominently discussed in Section 11, Section 16, and Table 8.
  - The **390 worsened cases** in `ROUTER_DEVELOPMENT` and **34 worsened cases** in `EXTERNAL884` are fully retained in Table 4 and Table 5.
  - The absence of executed C1, C2, and C3 causal experiments is transparently reported in Table 8.
