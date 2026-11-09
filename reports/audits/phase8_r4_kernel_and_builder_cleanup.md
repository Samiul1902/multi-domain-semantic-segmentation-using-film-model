# Phase 8-R4 — Dedicated Kernel Pinning and Provenance Report

## Environment & Kernel
- **Kernel Name**: `jup-venv`
- **Display Name**: `jup .venv (Python 3.11)`
- **Expected Interpreter**: `D:\Softfors\jup\.venv\Scripts\python.exe`
- **Notebook Runtime Interpreter Match**: YES (`actual_python == expected_python`)

## Notebook Final Artifact
- **Path**: `notebooks/06_kub_baseline_infrastructure.ipynb`
- **Full SHA-256**: `f665883a420edce7ed760daacf7885e2a7c8681ad8e85504175dbfee411df5ef`
- **Cell Count**: 11
- **Executable Assertions**: 41
- **Run All Clean-Kernel Executions**: PASS (Run 1 & Run 2 verified via `nbclient`)

## Builder Cleanup
- **Status**: ARCHIVED
- **Archive Documentation**: `reports/superseded/code/phase8/README.md`
- **Active Syntax/Parser Errors**: 0

## Integrity Safeguards
- **Manifest Guard**: PASS (`src/utils/manifest_guard.py` & `tests/test_manifest_guard.py`)
- **Test Lock**: PASS (`reports/audits/test_lock.json`, KUB TEST=558, Global TEST=1,683, Development access blocked)
- **Unit Tests**: 18/18 PASS
- **Static Check**: PASS (`python -m compileall`)
