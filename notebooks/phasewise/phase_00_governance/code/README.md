# Phase 00 Governance & Reproducibility Audit Code

## Overview
This directory contains the reviewer-facing, standalone execution script for auditing scientific research governance, protocol verification, and data isolation standards in the RA-MedFiLM-Seg++ project.

## Script Details
- **File:** `phase00_governance_audit.py`
- **Purpose:** 
  1. Validates the existence and integrity of required governance documents and manifests (`PROJECT_MASTER_PLAN.md`, `test_lock.json`, `antigravity_current_state.json`, etc.).
  2. Audits the untouched `TEST` cohort isolation status (`TEST reads = 0`, `TEST metrics = NONE`).
  3. Verifies that external validation datasets and reference experiment repositories are untouched.
  4. Computes and confirms the SHA-256 hash of immutable canonical provenance notebooks (`notebooks/13_phase14_regional_refiner_diagnostic.ipynb`).
  5. Confirms active project status (Phase 15 prospective protocol frozen; later phases not started).

## Execution Instructions
Run the audit using the project-certified Python interpreter:
```powershell
& "D:\Softfors\jup\.venv\Scripts\python.exe" notebooks/phasewise/phase_00_governance/code/phase00_governance_audit.py
```

## Governance Constraints & Non-Actions
- **Read-Only Guarantee:** This script performs strictly read-only checks.
- **No Training:** Does NOT load PyTorch weights or perform training.
- **No Model Inference:** Does NOT evaluate any neural network models.
- **No Test Content Reads:** Does NOT open or read image files in the test split.
- **No Artifact Modification:** Does NOT overwrite or mutate any existing audit or data files.

