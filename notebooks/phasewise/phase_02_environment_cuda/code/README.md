# Phase 02 Environment, CUDA, AMP, and Reproducibility Audit Code

## Overview
This directory contains the reviewer-facing, standalone execution script for certifying the computational deep learning stack, CUDA hardware capabilities, AMP behavior, and memory safety for the RA-MedFiLM-Seg++ research project.

## Script Details
- **File:** `phase02_environment_cuda_audit.py`
- **Purpose:**
  1. Validates the certified Python virtual environment interpreter (`D:\Softfors\jup\.venv\Scripts\python.exe`).
  2. Inspects PyTorch (`2.6.0+cu124`), torchvision (`0.21.0+cu124`), cuDNN, and CUDA runtime (`12.4`).
  3. Verifies physical GPU hardware (NVIDIA GeForce RTX 3060 Ti 8GB, compute capability 8.6).
  4. Audits the technical distinction between the host NVIDIA display driver (Driver API) and PyTorch bundled CUDA runtime.
  5. Executes safe synthetic CUDA matrix operations and AMP (`torch.autocast`) tests.
  6. Evaluates deterministic seed repeatability and GPU memory allocation/cleanup.
  7. Verifies cryptographic SHA-256 immutability of accepted Phase 00, Phase 01, and canonical Phase 14 notebooks.

## Execution Instructions
Run the audit using the project-certified Python interpreter:
```powershell
& "D:\Softfors\jup\.venv\Scripts\python.exe" notebooks/phasewise/phase_02_environment_cuda/code/phase02_environment_cuda_audit.py
```

## Governance Constraints & Non-Actions
- **No Training:** Does NOT train any models or update optimizer parameters.
- **No Model Forward Passes:** Does NOT perform dataset inference.
- **No Test Content Reads:** Strictly zero reads on test images (`TEST reads = 0`).
- **Synthetic Tensors Only:** Memory and execution checks utilize temporary, synthetic in-memory tensors only.

