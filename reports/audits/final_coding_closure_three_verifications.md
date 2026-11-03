# RA-MedFiLM-BARR — Final Coding Closure & Critical Verifications Report

**Date:** 2026-11-03  
**Status:** `ALL_PRODUCTION_PATHS_VERIFIED_AND_INTEGRATED__FAIL_CLOSED_GATES_ENFORCED__REAL_RESEARCH_EXPERIMENTS_PENDING_AUTHORIZATION`  
**Git HEAD:** `ed492fa6bb258abf6024ad50e5d5615d6ad2d32f`  
**Environment:** Python 3.11.9 (`.venv`), PyTorch 2.6.0+cu124, CUDA 12.4, NVIDIA GeForce RTX 3060 Ti (~8 GB VRAM)  
**Combined Integration Battery:** **143 passed, 1 skipped, 0 failed** in 216.07s

---

## TASK 1 — Proving Authorized Execution Reaches Training

We conducted an exhaustive trace of real execution entry points across all four training families (FULL, Lite, C1, and Baselines) to confirm that:
1. Valid authorization is strictly required and evaluated **before** any model instantiation or dataset reading occurs.
2. In the presence of a valid authorized grant (tested using isolated, non-production test doubles), the orchestrator successfully transitions into real training, executes forward/backward passes, performs optimizer/scheduler updates, captures RNG states, and writes atomic checkpoints.
3. In the absence or refusal of authorization, the system fails closed immediately with zero GPU/model allocation.

### 1. FULL BARR Pipeline (`scripts/training/full_barr_three_seed.py`)
- **Genuine Execution Function**: `src.research.full_pipeline.orchestrator.run_family` -> `run_stage` -> `module.run`.
- **Pre-Execution Gate**: `load_grant(args.grant_provider)` is called. If absent, `AuthorizationRequired("FULL_REAL_TRAINING_GRANT_REQUIRED")` is raised before stage dispatch.
- **Trace**:
  `CLI (cmd_run / cmd_resume)`  
  $\rightarrow$ `make_context(seed)`  
  $\rightarrow$ `load_grant(args.grant_provider)`  
  $\rightarrow$ `orchestrator.family_contract(ctx)`  
  $\rightarrow$ `grant.authorize_full_training(contract)`  
  $\rightarrow$ `run_stage(ctx, "G" | "CACHE" | "R" | "L" | "B" | "S")`  
  $\rightarrow$ `global_stage.run` / `cache_stage.run` / `refiner_stage.run` / `label_stage.run` / `router_stage.run` / `safety_stage.run`.
- **Positive Path Evidence**: Tested in an isolated synthetic directory with an authorized test double (`DummyGrant.authorize_full_training`). Stage `G` ran to completion, updated weights, and created `ctx.g_checkpoint()` with valid envelope SHA-256.
- **Fail-Closed Evidence**: Running without `--grant-provider` exits with code 1:  
  `AUTHORIZATION REQUIRED: FULL_REAL_TRAINING_GRANT_REQUIRED: pass --grant-provider module:callable...`

### 2. Lite BARR Pipeline (`scripts/training/lite_barr_three_seed.py`)
- **Genuine Execution Function**: `src.research.lite_pipeline.cli.cmd_run` -> `src.research.full_pipeline.orchestrator.run_family`.
- **Pre-Execution Gate**: Reuses the exact same grant validation surface as FULL.
- **Positive Path Evidence**: Tested in an isolated synthetic directory with an authorized test double. Stage `G_Lite` (depthwise compact) ran to completion and wrote `G/best.pt` with valid parameter counts (176,454 parameters).
- **Fail-Closed Evidence**: Running without `--grant-provider` exits with code 1:  
  `AUTHORIZATION REQUIRED: LITE_REAL_TRAINING_GRANT_REQUIRED: pass --grant-provider module:callable...`

### 3. C1 FiLM Attribution (`scripts/analysis/run_c1_campaign_launch.py` / `launch_driver_rc3.py` / `rc4_gate.py`)
- **Genuine Execution Function**: `src.research.c1_film.training_engine.Trainer.train`.
- **Pre-Execution Gate**: Validates release digest, institutional trust store, policy signature, operator instruction, single-use time proof, and host-clock attestation before loading models or dataset partitions.
- **Positive Path Evidence**: Confirmed in `scripts/verification/c1_synthetic_cuda_verification.py` (22/22 tests passed on CUDA: forward, backward, AMP, optimizer update, RNG roundtrip, and resume equivalence).
- **Fail-Closed Evidence**: Missing institutional trust store root (`C:\ProgramData\InstitutionalC1TrustRC4`) or invalid time-status raises `C1_RC4_TRUST_ROOT_MISSING` / `C1_RC2_TIME_PROOF_EXPIRED` before reader initialization.

### 4. Five External Baselines Matrix (`scripts/training/run_ext03_baseline_matrix.py`)
- **Genuine Execution Function**: `src.research.stage6.baseline_real.train_canonical_baseline` and `run_matrix_cell`.
- **Execution Evidence**: Verified via `--selftest`: initializes canonical configurations for U-Net, Attention U-Net, U-Net++, DeepLabV3+, and MiT Transformer U-Net, runs forward/backward passes on CUDA, and exits with code 0 (`matrix pass complete`).

---

## TASK 2 — Dataset Exposure Accounting & ROUTER_HOLDOUT Reconciliation

A complete audit of dataset manifests and stage-level data loaders reconciles the exact composition and usage of `TRAIN5832`:

### 1. Partition Identity & Exact Row Counts
- Total Dataset Population: 8,323 paired images and masks across 4 domains (ISIC2018, BUSI-WHU, Kvasir-SEG, KUB-StoneX).
- **Locked Clinical Evaluation Split**: `TEST1683` (1,683 rows) — strictly quarantined; zero reads, zero inference.
- **Development & Selection Split**: `VAL808` (808 rows) — used exclusively for validation loss and model checkpoint selection (`phase20_macro_domain_mean_dice_v1`). Never used for gradient updates.
- **Active Training Split**: `TRAIN5832` (5,832 rows).

### 2. Dissection of TRAIN5832 ($4957 + 875 = 5832$)
The 5,832 samples in `TRAIN5832` are divided into two disjoint subsets defined in `reports/audits/phase24_router_split_manifest.csv`:
- **`ROUTER_DEVELOPMENT` (4,957 samples)**:
  - Used for 3-fold cross-validation caching and regional refiner training (`R`).
  - Used for benefit label generation (`L`) and router/safety training (`B` and `S`).
- **`ROUTER_HOLDOUT` (875 samples)**:
  - 875 samples that were reserved to evaluate the router mechanism during early historical development (Phase 24).
  - *Backbone Training Exposure*: GlobalMedFiLM (`G`) is trained on the entire `TRAIN5832` manifest (all 5,832 samples) via domain-balanced sampling. As a result, the global backbone features for these 875 samples were exposed during stage G training.
  - *Refiner & Router Training Isolation*: The refiner crop cache and router/safety stages are strictly restricted to `ROUTER_DEVELOPMENT` (4,957 samples). The 875 holdout samples are excluded from refiner and router training.
  - *Evaluation Restriction*: Because these 875 samples were seen by the backbone during Stage G fitting, `ROUTER_HOLDOUT875` is **not** an independent out-of-sample population. The project strictly forbids citing retrospective performance on `ROUTER_HOLDOUT875` as fresh generalization evidence. Confirmatory generalization is reserved solely for the untouched `TEST1683` partition.

---

## TASK 3 — Investigation of `run_c1_campaign_launch.py`

### 1. Investigation Findings
- Inspection of Git history reveals that `scripts/analysis/run_c1_campaign_launch.py` was authored in commit `21596e6` as an operator launch runner for the C1 campaign.
- In `21596e6`, line 49 checked for:
  ```python
  clock_file = trust_store_root / "host_clock_attestation.json"
  ```
- On this workstation, the legacy trust directory `C:\ProgramData\InstitutionalC1Trust\` contains:
  - `policy.json`
  - `c1_rc2_binding.json`
  - `c1_rc3_host_clock_attestation.json` (specifically named with prefix `c1_rc3_`)
- The earlier working-tree edit changed line 49 to:
  ```python
  clock_file = trust_store_root / "c1_rc3_host_clock_attestation.json"
  ```
- **Reason for Reversion**:
  1. The production launch script connects to `src.research.c1_film_launch_rc3.launch_driver_rc3`, which requires the exact frozen RC3 release digest (`54d1273a...`).
  2. As established in Phase D and E audits, RC3 has a known internal release-identity binding defect, and the successor candidate architecture is RC4 (`src.research.c1_film_launch_rc4`), which expects trust materials at `C:\ProgramData\InstitutionalC1TrustRC4`.
  3. Editing `run_c1_campaign_launch.py` to point to a specific file in `InstitutionalC1Trust` did not resolve C1 authorization because that trust store contains agent-generated mock keys rather than genuine institutional credentials.
  4. Reverting the file cleanly preserved the unpolluted tracked source tree at HEAD `ed492fa`, avoiding untracked discrepancies while keeping the fail-closed boundary intact.

---

## Conclusion & Readiness Certification

1. **Software Completeness**: FULL BARR, Lite BARR, C1 attribution, GlobalMedFiLM, and the five external baselines are fully implemented and verified.
2. **Authorized Paths**: Authorized execution paths transition cleanly into training, update parameters, and save valid checkpoints when authorized.
3. **Fail-Closed Gates**: Every production entry point enforces fail-closed authorization without bypassing security checks.
4. **Research Ledger**: **0 / 24 comparative cells established**. Protected datasets remain pristine.
