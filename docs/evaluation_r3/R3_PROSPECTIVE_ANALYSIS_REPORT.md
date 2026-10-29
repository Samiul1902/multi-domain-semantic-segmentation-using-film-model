# R3 Prospective Scientific Experiment Design, Mathematical Analysis, and C1 Execution Handoff Report

**Milestone State:** `C1_RC2_GIT_RECONSTRUCTIBLE__RELEASE_FROZEN__EXTERNAL_AUTHORIZATION_PENDING__NO_SCIENTIFIC_EXECUTION`  
**Execution State:** `RA_MEDFILM_BARR_R3_SCIENTIFIC_ANALYSIS_PLAN_AND_C1_EXECUTION_HANDOFF_READY__REAL_DATA_EXECUTION_NOT_STARTED`

---

## 1. Executive Summary & Objective

This Phase R3 research release provides the prospective scientific experiment design, mathematical analysis specifications, and operational execution handoff for the RA-MedFiLM-BARR project.
- **Zero real-data inference, training, or re-scoring was conducted.**
- **No protected test sets (`TEST`, `ROUTER_HOLDOUT`) were accessed.**
- **Bitwise preservation:** Frozen C1 RC2 digest `54794efc6d99d94fae9eaebd992e01e4e9923b5055d024ea1d5f02a8a5e737ed` is strictly maintained.

---

## 2. Formal Scientific Hypotheses & Falsification Criteria

### C1 — Task-Conditioned FiLM Attribution
- **Primary Research Question:** Does learnable task-conditioned Feature-wise Linear Modulation (FiLM) improve segmentation performance over matched frozen identity-FiLM control models across diverse medical imaging domains?
- **Null Hypothesis ($H_0^{C1}$):**
  $$\Delta_{\text{mean}} = \frac{1}{3} \sum_{s \in \{42, 123, 3407\}} \left( \text{MacroDice}(C1\text{-}T, s) - \text{MacroDice}(C1\text{-}C, s) \right) \le 0$$
- **Alternative Hypothesis ($H_1^{C1}$):**
  $$\Delta_{\text{mean}} > 0$$
- **Primary Estimand:** Mean paired difference over 3 matched seeds of equal-domain (4-domain unweighted macro) validation Dice.
- **Decision Rules:**
  - *Positive Finding:* Lower bound of the prospective 95% paired BCa/percentile bootstrap interval $> 0.0$ and mean paired delta $> 0$.
  - *Negative Finding:* Upper bound of the 95% bootstrap interval $\le 0.0$.
  - *Inconclusive Finding:* 95% bootstrap interval spans zero, or seed directionality conflicts across seeds.
- **Secondary Domain Outcomes:** Individual domain deltas for KUB, ISIC, BUSI, and KVASIR evaluated under Holm-Bonferroni multiplicity correction.

### C2 — Budget-Aware Regional Refinement (BARR)
- **Hypothesis 1 (Refinement vs. Monolithic):** Regional refinement on candidate bounding regions yields higher localized Dice than whole-image baseline segmentation.
- **Hypothesis 2 (Benefit Routing):** Predicted benefit routing identifies regions where refinement yields positive expected utility, achieving superior quality compared to random or static routing under equal FLOP constraints.
- **Hypothesis 3 (Selective Acceptance):** Acceptance filtering prevents net degradation by rejecting candidate refinements that decrease agreement or confidence relative to global coarse predictions.
- **Hypothesis 4 (Harm vs. Compute Trade-off):** Quality gains are achieved within declared latency and compute budgets without inducing uncompensated computational cost.

### C3 — Fair Multi-Domain Benchmarking
- **Hypothesis:** Multi-domain conditioning matches or outperforms independently trained domain-specific and single-task models when evaluated under identical training seeds, budget constraints, and standardized preprocessing protocols.

---

## 3. Mathematical Research Specification

| Component | Mathematical Definition / Operator | Status in Codebase |
| :--- | :--- | :--- |
| **Task Embeddings** | $\mathbf{e}_t = \text{Embedding}(t) \in \mathbb{R}^{D}$, where $t \in \{0, 1, 2, 3\}$ represents ISIC, BUSI, KVASIR, KUB. | `IMPLEMENTED` |
| **FiLM Modulation** | $\gamma, \beta = \text{Linear}(\mathbf{e}_t)$; $\text{FiLM}(\mathbf{F}) = \gamma \odot \mathbf{F} + \beta$ | `IMPLEMENTED` |
| **Identity Control ($C1\text{-}C$)** | $\gamma \equiv \mathbf{1}, \beta \equiv \mathbf{0}$; $\text{FiLM}_{\text{identity}}(\mathbf{F}) = \mathbf{F}$ (Frozen parameters) | `IMPLEMENTED` |
| **Loss Function** | $\mathcal{L} = 0.5 \cdot \mathcal{L}_{\text{BCE}} + 0.5 \cdot \mathcal{L}_{\text{Dice}}(\epsilon = 10^{-6})$ | `IMPLEMENTED` |
| **Optimization Rule** | AdamW ($\text{lr} = 10^{-4}, \beta_1 = 0.9, \beta_2 = 0.999$, weight decay = $10^{-2}$), cosine decay schedule | `IMPLEMENTED` |
| **Domain-Balanced Batching** | Stratified batching: equal sample allocation across the 4 canonical domains | `IMPLEMENTED` |
| **Regional Candidate Selection** | Heatmap peak extraction and dynamic bounding box generation | `HISTORICALLY_EVALUATED` |
| **Regional Refiner Network** | High-resolution crop refiner conditioning on task and context | `HISTORICALLY_EVALUATED` |
| **Benefit Routing & Acceptance**| Utility estimation $\hat{u} = \mathbb{E}[\Delta \text{Dice} \mid \text{crop}]$ and acceptance thresholding | `PROSPECTIVE` |
| **Multi-Domain Equal Macro** | $\text{MacroDice} = \frac{1}{4} \left( \bar{D}_{\text{KUB}} + \bar{D}_{\text{ISIC}} + \bar{D}_{\text{BUSI}} + \bar{D}_{\text{KVASIR}} \right)$ | `IMPLEMENTED` |

---

## 4. Prospective Statistical Analysis Plan

- **Estimator:**
  $$\Delta_s = \text{EqualDomainMacroDice}(C1\text{-}T, s) - \text{EqualDomainMacroDice}(C1\text{-}C, s)$$
  $$\Delta_{\text{mean}} = \frac{1}{3} \sum_{s \in \{42, 123, 3407\}} \Delta_s$$
- **Variance Decomposition:**
  - Case-sampling uncertainty: Domain-stratified paired case bootstrap (10,000 resamples, PCG64 seed `20261027`).
  - Patient clustering: Applied specifically to KUB (where verified patient IDs exist).
  - Seed-level dispersion: Descriptive report of mean, sample standard deviation ($ddof = 1$), and range across the 3 seeds. Seed variance is **never** conflated with case variance.
- **Multiplicity Control:** Predeclared family of secondary hypotheses adjusted via Holm-Bonferroni and Benjamini-Hochberg (FDR).

---

## 5. C1 Operational Launch Feasibility Verdict

Detailed preflight inspection of frozen release `c1_film_launch_rc2`:

1. **Production Trust Store:**
   - Requires provisioned ECDSA-P256 keys with Windows ACL restrictions. Operational provisioning is technically possible by an authorized external operator.
2. **Clock Trust Hard Stop:**
   - In `src/research/c1_film_launch_rc2/time_status.py`, line 45 explicitly hardcodes:
     ```python
     HOST_CLOCK_TRUST = "NOT_ESTABLISHED"
     ```
   - In `rc2_gate.py`, lines 181–182 enforce:
     ```python
     if self.host_clock_trust != "VERIFIED":
         raise GateError("C1_RC2_HOST_CLOCK_UNVERIFIED")
     ```
   - **Critical Finding:** Because `HOST_CLOCK_TRUST` is hardcoded to `"NOT_ESTABLISHED"` in the frozen source and cannot dynamically transition to `"VERIFIED"` without code alteration, real production training cannot be activated within the frozen RC2 bundle as currently authored.
3. **Formal Verdict:**
   ```text
   C1_RC2_PRODUCTION_PATH_NOT_ACTIVATABLE
   ```
   *Remediation Required:* A clean, audited RC3 release revision must decouple the runtime host clock verification mechanism from static code constants while preserving all security controls.

---

## 6. Execution Handoff Protocol

### A. The 6-Run Plan
Six logical training runs matching the frozen C1 protocol:
- Run 1: `arm = C1-T`, `seed = 42`
- Run 2: `arm = C1-C`, `seed = 42`
- Run 3: `arm = C1-T`, `seed = 123`
- Run 4: `arm = C1-C`, `seed = 123`
- Run 5: `arm = C1-T`, `seed = 3407`
- Run 6: `arm = C1-C`, `seed = 3407`

### B. Required External Operator Actions Prior to Scientific Execution
1. Perform clean dependency environment verification (`torch`, `torchvision`, `scipy`, `scikit-learn`, `cryptography`).
2. Verify host CMOS battery, hardware clock synchronization, and active NTP daemon.
3. Authorize and provision production key material in a secure, operator-controlled keystore.
4. Issue prospective signed launch authorizations for the 6 specified runs once release revision is finalized.

### C. First Scientific Execution Command Shape (Documented ONLY — NOT Executed):
```powershell
# Prospective invocation template (to be run only upon authorized release revision)
python -m src.research.c1_film_launch.launch_driver --arm C1-T --seed 42 --config configs/c1_film_train.yaml
```

---

## 7. Unit & Contract Verification Results

All 39 unit tests passed cleanly in 4.91s:
- `tests/test_evaluation_r1_reference.py` (10 passed)
- `tests/test_evaluation_r1_contract.py` (4 passed)
- `tests/test_evaluation_r1_metrics.py` (16 passed)
- `tests/test_evaluation_r2_integrity.py` (5 passed)
- `tests/test_evaluation_r3_analysis.py` (4 passed)
- **Total:** `39 passed in 4.91s` (100% pass rate).
