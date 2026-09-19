# Phase 00: Governance & Scientific Protocols (`phase_00_governance`)

## 1. Scientific Overview
- **Phase ID:** `phase_00_governance`
- **Scientific Title:** Research Governance, Reproducibility, and Protocol Control
- **Current Status:** `COMPLETE`
- **Overall Project Status:** Phase 15 (`CURRENT_PROTOCOL_DESIGN` / `AWAITING_SUPERVISOR_AUTHORIZATION`)
- **Core Question:** *How was the research governed to prevent patient leakage, uncontrolled heuristic tuning, irreproducible experiments, and premature TEST usage?*

---

## 2. Directory Structure & Deliverables
```text
phase_00_governance/
|-- README.md                                          # This document
|-- phase00_governance_reproducibility_and_protocol.ipynb # Reviewer-facing executed notebook (Run-All PASS)
`-- code/
    |-- phase00_governance_audit.py                    # Standalone executable governance audit script
    `-- README.md                                      # Instructions for running the python audit
```

---

## 3. Primary Governance Standards
1. **TRAIN / VAL Development Policy:** All model development, loss exploration, and hyperparameter tuning occur strictly on the patient-partitioned `TRAIN` and `VAL` sets.
2. **Untouched TEST Set Isolation:** The test split ($1,683$ cases across four domains) is cryptographically locked (`TEST reads = 0`, `TEST metrics = NONE`) until Phase 39.
3. **Scientific Change Control:** Architecture modifications, loss function adjustments, optimizer alterations, learning rates, random seeds, and progression gates require explicit supervisor approval (`CHECK_REQUIRED`).
4. **Experiment Continuity & Resumption:** Every training run requires a unique, non-reusable experiment ID. Resuming after interruption requires verified mathematical continuity between checkpoint weights and logged history.
5. **Deterministic Hardware Certification:** Environment certified on PyTorch 2.6.0+cu124, NVIDIA GeForce RTX 3060 Ti 8GB, with CUDA determinism flags active.
6. **Artifact Provenance & Hashing:** Canonical frozen artifacts are cryptographically locked (e.g., Phase 14 canonical notebook SHA-256: `b5b329d1...`).

---

## 4. Key Artifacts & References
- **Canonical Protocol:** [`reports/audits/research_protocol.md`](file:///D:/Softfors/jup/reports/audits/research_protocol.md)
- **Authoritative Master Plan:** [`PROJECT_MASTER_PLAN.md`](file:///D:/Softfors/jup/PROJECT_MASTER_PLAN.md)
- **Test Lock Manifest:** [`reports/audits/test_lock.json`](file:///D:/Softfors/jup/reports/audits/test_lock.json)
- **Environment Certification:** [`reports/audits/environment.json`](file:///D:/Softfors/jup/reports/audits/environment.json)
- **Governance Flow Diagram:** [`reports/figures/phase00_governance/phase00_governance_flow.png`](file:///D:/Softfors/jup/reports/figures/phase00_governance/phase00_governance_flow.png)

---

## 5. Reviewer Execution Instructions
### Running the Standalone Python Audit
```powershell
& "D:\Softfors\jup\.venv\Scripts\python.exe" notebooks/phasewise/phase_00_governance/code/phase00_governance_audit.py
```
*Expected Output:* `PHASE 00 GOVERNANCE AUDIT RESULT: PASS` (0 errors, 0 test content reads).

### Running the Jupyter Notebook
Open and execute `phase00_governance_reproducibility_and_protocol.ipynb` in the `jup-venv` kernel. Verified 100% Run-All clean with 18 cells, 0 errors, embedded process diagrams, and dynamic audit tables.

---

## 6. Next Phase
- **Next Phase:** [`phase_01_project_initialization/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_01_project_initialization/README.md) (Project Architecture & Data Contract)
- **Next Phase Status:** `NOT_STARTED` (Awaiting supervisor authorization).
