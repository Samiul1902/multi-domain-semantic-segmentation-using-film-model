# RA-MedFiLM-BARR: Manuscript Authoring & Writing Guide (V4)
## Evidence-Backed Results, Discussion Guidance & Submission Strategy for IEEE TMI / Medical Image Analysis

---

## 1. Core Evidentiary Contributions

When drafting the journal manuscript for **RA-MedFiLM-BARR**, the narrative must reflect the empirical findings and disclosures established in the **V4 Scientific Master Report**:

1. **Multi-Domain Heterogeneity & Task-Conditioned Representation**:
   * *Finding*: Joint training across divergent modalities causes severe cross-task interference in standard convolutional baselines (U-Net achieves only 0.7878 macro Dice).
   * *Mechanism*: GlobalMedFiLM applies discrete task embeddings via Feature-wise Linear Modulation (FiLM) conditioned on task identity, elevating macro Dice to **0.8351** (+4.73 pp over U-Net, +4.31 pp over U-Net++).
   * *Evidence*: Table 2, Figure 3, Figure 4.

2. **The Hazard of Unconstrained Secondary Refinement**:
   * *Finding*: In dual-stage segmentation models, unconditional refinement is fundamentally unsafe. In the 13-arm ablation study (Arm A1, always-refine), secondary refinement produces a **42.7% harmful activation rate**, degrading 2,115 of 4,957 training samples.
   * *Mechanism*: Boundary-Aware Residual Refinement (BARR) must be governed by a **Benefit Router ($B_\phi$)** and **Post-Safety Gate ($S_\omega$)**.
   * *Evidence*: Table 5, Figure 12, Figure 13.

3. **Risk-Averse Routing & Harm Reduction**:
   * *Finding*: By estimating expected improvement and gating decisions based on predictive safety ($P(\Delta > 0) > \tau$), BARR cuts harmful activations from 42.7% to **32.4%** (Arm A8), lifting routed delta Dice to **+0.75 pp**.
   * *Subgroup Evidence*: Selective routing yields targeted gains on complex anatomical targets—**Bladder Stones (+1.46 pp)**, **Ureteric Stones (+1.06 pp)**, and **Small/Sessile Polyps (+0.15 pp)**—while preserving circumscribed margins on benign breast lesions (0.00 pp shift on benign fibroadenomas).
   * *Evidence*: Table 3, Figures 4–8.

4. **Computational Pareto Superiority**:
   * *Finding*: RA-MedFiLM-BARR delivers superior macro validation accuracy (0.8379 Dice) at an analytical complexity of **32.44 GMACs** and **4.84M parameters**, operating at a 67.2% compute reduction compared to vision transformers (MiT U-Net: 99.10 GMACs, 16.35M params) and 53.1% reduction compared to DeepLabV3+ (69.14 GMACs, 40.35M params).
   * *Evidence*: Table 2, Figure 16.

---

## 2. Mandatory Disclosures & Negative Results

A high-impact peer-reviewed submission requires rigorous transparency regarding material limitations:

1. **External Radiographic Vulnerability (Stone-Free False Positives)**:
   * *Empirical Result*: On the retrospective external negative control cohort (`Stones_where_are_you`, n=14 stone-free radiographs), both GlobalMedFiLM and BARR produced **14 out of 14 false-positive stone detections (mean Dice 0.000)**.
   * *Discussion Text*: *"While BARR successfully refines ambiguous boundaries in positive lesions, post-safety gating does not eliminate false-positive generation when evaluating completely stone-free imagery obscured by complex bowel gas. This highlights a fundamental physical limitation of plain radiography and establishes the need for dedicated empty-mask calibration objectives in future work."*

2. **Perturbation Fragility on Plain Radiography**:
   * *Empirical Result*: Under high Gaussian noise, performance on KUB radiographs drops precipitously by **-36.36 pp**, compared to -3.15 pp on ISIC dermoscopy and -6.04 pp on Kvasir colonoscopy.
   * *Discussion Text*: *"Low-contrast modalities lacking rich chromatic texture (such as non-contrast abdominal radiographs) exhibit severe fragility to high-frequency noise. Noise corrupts subtle radio-opacity gradients between renal calyces and intestinal gas, precipitating false-positive candidate proposals."*

3. **Incremental Dataset Progression Absence**:
   * *Disclosure*: State clearly that an incremental sequential domain addition study (e.g. adding tasks sequentially to measure catastrophic forgetting) was not executed in the repository (`INCREMENTAL_DATASET_PROGRESSION_NOT_EXECUTED`). Avoid simulating this from unrelated checkpoints.

---

## 3. Unsupported Claims to Avoid

The following claims were corrected from earlier drafts and **must NEVER appear in the manuscript**:
* ❌ *"RA-MedFiLM-BARR guarantees strictly non-negative refinement across all clinical cases."* (Refinement causes 390 worsened cases in ROUTER_DEVELOPMENT and 34 worsened cases in EXTERNAL884).
* ❌ *"The architecture eliminates catastrophic failures and is certified clinically safe."* (The 14/14 stone-free false-positive failure is a catastrophic failure mode).
* ❌ *"Macro superiority over DeepLabV3+ is statistically significant ($p < 0.001$)."* (Bootstrap paired confidence intervals span zero; DeepLabV3+ achieves competitive point accuracy on ultrasound).
* ❌ *"Three-seed evaluation proves independent end-to-end model reproducibility."* (All three seeds share an identical frozen GlobalMedFiLM backbone; variance reflects refiner/router initialization only).
* ❌ *"The C1 causal FiLM attribution experiment confirms that learned FiLM outperforms identity FiLM."* (0 of 6 planned paired C1 runs were executed; causal attribution remains unproven).

---

## 4. Key Results & Figure Citation Mapping

| Manuscript Section | Key Statement / Finding | Cited Table / Figure |
| :--- | :--- | :--- |
| **Methods** | Architecture execution pipeline (Global -> Proposal -> Router -> Refiner -> Safety -> Recomposition) | Figure 1, Table 1 |
| **Results: Internal** | Six-model macro benchmark on VAL808 (+4.30 pp over U-Net, 0.8351 baseline, 0.8379 BARR) | Table 2, Figure 3 |
| **Results: Subgroups** | Verified gains on Bladder (+1.46 pp) and Ureteric (+1.06 pp) stones; benign margin protection | Table 3, Figure 4 |
| **Results: Qualitative** | Multi-domain qualitative segmentation (TP/FP/FN trichromatic error overlays) | Figures 5, 6, 7, 8 |
| **Results: External** | Retrospective domain shift (CVC: 0.6897, BrEaST: 0.7081, Stones: 0.0821) and 14/14 stone-free failure | Table 4, Figures 10, 11 |
| **Results: Progression** | Error propagation through Benefit Router and Safety Gate (815 improved vs 390 worsened) | Figure 12 |
| **Results: Ablation** | 13-arm ablation isolating routing and safety dynamics (A1 harm: 42.7% vs A8 harm: 32.4%) | Table 5, Figure 13 |
| **Results: Reproducibility**| Three-seed stability on shared backbone (0.837862 ± 0.00004 Dice) | Table 6, Figure 14 |
| **Results: Robustness** | Noise, blur, resolution, and gamma perturbation sensitivity (-36.4 pp on KUB) | Table 7, Figure 15 |
| **Results: Compute** | Pareto efficiency: 32.44 GMACs, 4.84M params, 15.7–18.9 ms RTX 3060 Ti latency | Table 2, Figure 16 |
| **Discussion: TEST** | Historical descriptive one-shot test result (Phase 39 v1.2 macro Dice: 0.8314 across 1,683 cases) | Section 18 |
| **Discussion: Open Gaps**| Future experimental roadmap (C1 causal FiLM attribution, C2 causal ablation, C3 24-cell matrix) | Table 8 |
