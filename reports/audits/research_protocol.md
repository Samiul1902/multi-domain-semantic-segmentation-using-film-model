# RA-MedFiLM-Seg++ Research Protocol

This document defines the standard research protocol for the RA-MedFiLM-Seg++ project.

## Core Policies
- **Test Lock**: TEST DATA MUST NOT BE USED FOR DEVELOPMENT OR MODEL SELECTION.
- **External Data**: EXTERNAL DATA MUST NOT BE USED FOR TUNING.
- **Experiment A**: READ-ONLY.

## Training Configuration
- **Optimizer**: AdamW
- **LR**: 1e-4
- **Weight Decay**: 1e-4
- **Scheduler**: CosineAnnealingLR
- **Epochs**: 100
- **Patience**: 15
- **Seeds**: 42, 123, 3407
- **AMP**: Enabled on CUDA
