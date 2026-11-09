# Phase 8 — KUB Baseline Infrastructure Report

## CUDA & Hardware
- CUDA Available: True
- GPU: NVIDIA GeForce RTX 3060 Ti
- PyTorch: 2.6.0+cu124
- CUDA Runtime: 12.4

## Infrastructure Smoke Pass
- Feasible Batch Size: 4
- Peak Allocated VRAM: 1630306816 bytes
- Checkpoint Round-trip Output Equivalence: True
- Test Access Guard: PASS (Blocked)

## Safeguards
- Test-lock artifact: `reports/audits/test_lock.json`
- Manifest guard: PASS
- Substantive training performed: NO
