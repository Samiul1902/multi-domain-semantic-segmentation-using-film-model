# ReMedFiLM Publication Writing Guide (Version 7.0 Definitive)

**Target Venues:** IEEE Transactions on Medical Imaging (TMI), Medical Image Analysis (MedIA)  
**Method Name:** ReMedFiLM (FULL Proposed System: G + B_phi + R_psi + S_omega)  
**Comparator / Backbone:** GlobalMedFiLM (G, 3.52M params, Arm A0 baseline)  
**Version:** 7.0 Frozen Protocol  

---

## 1. Core Manuscript Thesis

When authoring journal manuscripts for IEEE TMI or Medical Image Analysis:
1. **The Primary Contribution is Risk-Averse Modular Refinement:**
   - Multi-domain medical imaging creates severe gradient conflicts and scale variance.
   - Secondary high-capacity refinement cannot be naively executed: unconstrained refinement (Arm A1) causes an unacceptable **42.7% all-population harm rate** (2,115 degraded cases).
   - ReMedFiLM introduces a cost-aware Benefit Router ($B_\phi$) and Post-Safety Gate ($S_\omega$), reducing all-population harm to **7.87%** while achieving statistically verified non-inferior preservation (+0.28 pp dev mean over backbone, lower 95% bootstrap CI $> -0.005$).
2. **Computational Economy:**
   - ReMedFiLM operates with only **4.84M parameters** and **32.44 Expected Conditional GMACs** ($31.55 + 0.274 \times 3.23$).
   - It matches/exceeds DeepLabV3+ (40.35M params, 8.3x larger) and MiT-UNet (16.35M params, 3.4x larger) at a fraction of their computational footprint.
   - Forward pass latency on RTX 3060 Ti is 15.72 ms (skipped path) to 18.89 ms (executed path), with a weighted mean of 16.59 ms.

---

## 2. Mandatory Reporting Guardrails & Defensive Authoring

1. **Model Terminology:**
   - Always refer to the proposed method as **ReMedFiLM** (or **ReMedFiLM (FULL Proposed System)**).
   - Never refer to GlobalMedFiLM as the proposed system. GlobalMedFiLM is the *internal global backbone* and ablation comparator.
2. **Statistical Claims:**
   - Do not claim universal statistical superiority. Frame the VAL808 result as **non-inferior preservation** (lower 95% bootstrap CI $> -0.005$).
   - Acknowledge that the paired difference vs. DeepLabV3+ includes zero in its 95% bootstrap interval ($[-0.007, +0.022]$). Frame the advantage as parameter and GMAC efficiency.
3. **Transparent Reporting of Negative Clinical Findings:**
   - **Stone-Free Control Failure:** Prominently report that on 14 normal radiographs, the model triggered false-positive foreground predictions in **14 out of 14 cases** (Dice 0.000). The safety gate rejected 1 case but adopted 7 hallucinatory refinements. Position this as an open radiological challenge requiring dedicated negative-case loss functions.
   - **Acquisition Noise Vulnerability:** Report that Gaussian sensor noise collapses KUB plain radiography performance by **-36.36 pp**, whereas optical modalities remain stable.
   - **Shared Backbone Disclosure:** State clearly that seeds 42, 123, and 3407 evaluated router/refiner variation across a shared pre-trained backbone.
   - **Prospective Milestones:** State that formal causal studies (C1, C2, C3) remain future milestones.
