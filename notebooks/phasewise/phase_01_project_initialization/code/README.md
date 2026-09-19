# Phase 01 Project Initialization & Repository Architecture Code

## Overview
This directory contains the reviewer-facing, standalone execution script for auditing repository directory layout, canonical path configurations, source-of-truth layers, and notebooks root cleanup audit records.

## Script Details
- **File:** `phase01_project_structure_audit.py`
- **Purpose:**
  1. Validates the existence of all top-level scientific directories (`src`, `scripts`, `configs`, `checkpoints`, `reports`, `notebooks`, `manifests`, `notebooks/phasewise`).
  2. Confirms canonical path resolutions for data, checkpoints, and reports.
  3. Verifies notebooks root cleanup classification summary (`notebooks_root_cleanup_audit.csv`).
  4. Cryptographically verifies SHA-256 hashes of accepted Phase 00 notebook (`60e0bc17...`) and canonical Phase 14 notebook (`b5b329d1...`).

## Execution Instructions
Run the audit using the project-certified Python interpreter:
```powershell
& "D:\Softfors\jup\.venv\Scripts\python.exe" notebooks/phasewise/phase_01_project_initialization/code/phase01_project_structure_audit.py
```

## Governance Constraints & Non-Actions
- **Read-Only Guarantee:** Strictly read-only checks; zero file mutations.
- **No Training:** Does NOT load PyTorch model weights or initiate training.
- **No Model Inference:** Does NOT execute model forward passes.
- **No Test Content Reads:** Does NOT access or read test set image files (`TEST reads = 0`).
- **No Destructive Deletion:** Does NOT delete or move legacy notebooks or scientific reports.

