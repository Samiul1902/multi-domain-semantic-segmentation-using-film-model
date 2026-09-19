#!/usr/bin/env python3
"""
Phase 00 — Research Governance Audit Script
Executable entry point for reviewing project governance, reproducibility standards,
test isolation, and artifact hashes.

Usage:
    D:\\Softfors\\jup\\.venv\\Scripts\\python.exe notebooks/phasewise/phase_00_governance/code/phase00_governance_audit.py
"""

import sys
import json
import hashlib
from pathlib import Path


def find_project_root() -> Path:
    """Robustly find project root containing manifests and reports."""
    p = Path(__file__).resolve()
    for _ in range(6):
        if (p / 'reports').exists() and (p / 'manifests').exists():
            return p
        p = p.parent
    return Path('D:/Softfors/jup')


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    if not file_path.exists():
        return "FILE_NOT_FOUND"
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def run_audit():
    root = find_project_root()
    print("=" * 70)
    print("PHASE 00 — SCIENTIFIC RESEARCH GOVERNANCE & REPRODUCIBILITY AUDIT")
    print("=" * 70)
    print(f"Project Root: {root}")
    print(f"Python:       {sys.executable}")
    print(f"Platform:     {sys.platform}")
    print("-" * 70)

    # 1. Check Required Governance Files
    governance_files = [
        "PROJECT_MASTER_PLAN.md",
        "PROJECT_CONTEXT.md",
        "ANTIGRAVITY_WORKFLOW.md",
        "reports/audits/antigravity_current_state.json",
        "reports/audits/test_lock.json",
        "reports/audits/environment.json",
        "reports/audits/phasewise_notebook_map.csv"
    ]
    
    print("\n[CHECK 1] Required Governance Documents & Manifests:")
    all_files_exist = True
    for rel_p in governance_files:
        full_p = root / rel_p
        exists = full_p.exists()
        print(f"  - {rel_p:45s} : {'EXISTS' if exists else 'MISSING'}")
        if not exists:
            all_files_exist = False

    # 2. Audit TEST Lock Status
    print("\n[CHECK 2] Untouched TEST Set Isolation & Lock Audit:")
    test_lock_file = root / "reports/audits/test_lock.json"
    test_lock_pass = False
    if test_lock_file.exists():
        with open(test_lock_file, "r", encoding="utf-8") as f:
            lock_data = json.load(f)
        print(f"  - Manifest Version   : {lock_data.get('manifest_version')}")
        print(f"  - Frozen Test Samples: {lock_data.get('test_sample_count')}")
        print(f"  - Test Split SHA-256 : {lock_data.get('full_test_sha256')}")
        print(f"  - Freeze Timestamp   : {lock_data.get('freeze_timestamp')}")
        test_lock_pass = True
    else:
        print("  - ERROR: test_lock.json not found!")

    # 3. Audit Current Project Execution State
    print("\n[CHECK 3] Project Execution State & Active Phase:")
    state_file = root / "reports/audits/antigravity_current_state.json"
    state_pass = False
    if state_file.exists():
        with open(state_file, "r", encoding="utf-8") as f:
            state = json.load(f)
        print(f"  - Current Phase           : Phase {state.get('current_phase')}")
        print(f"  - Phase Status            : {state.get('current_phase_status')}")
        print(f"  - Phase 14 Frozen         : {state.get('phase14_status')} (Gate: {state.get('phase14_gate')})")
        print(f"  - Phase 15 Loss Training  : Authorized = {state.get('phase15_executed', False)}")
        print(f"  - Phase 16 Status         : {state.get('phase16_status')}")
        print(f"  - TEST Content Reads      : {state.get('test_content_reads')}")
        print(f"  - TEST Metrics Evaluated  : {state.get('test_metrics')}")
        print(f"  - External Data Contam.   : {state.get('external_used')}")
        print(f"  - Ref Exp A Modified      : {state.get('experiment_a_modified')}")
        
        if (state.get('test_content_reads') == 0 and 
            state.get('test_metrics') == 'NONE' and 
            not state.get('external_used') and 
            not state.get('experiment_a_modified')):
            state_pass = True
    else:
        print("  - ERROR: antigravity_current_state.json not found!")

    # 4. Audit Canonical Provenance SHA-256 Hashes
    print("\n[CHECK 4] Canonical Provenance & Frozen Artifact Hashing:")
    canon_nb = root / "notebooks/13_phase14_regional_refiner_diagnostic.ipynb"
    expected_canon_sha = "b5b329d1d100138db640e4a3e91069a4008a434d998945646bc7a4522c040948"
    actual_canon_sha = compute_sha256(canon_nb)
    canon_pass = (actual_canon_sha == expected_canon_sha)
    print(f"  - Phase 14 Canonical Notebook:")
    print(f"    Expected : {expected_canon_sha}")
    print(f"    Actual   : {actual_canon_sha}")
    print(f"    Match    : {'MATCH (IMMUTABLE)' if canon_pass else 'MISMATCH ERROR'}")

    # 5. Summary & Decision
    print("\n" + "=" * 70)
    audit_success = all_files_exist and test_lock_pass and state_pass and canon_pass
    if audit_success:
        print("PHASE 00 GOVERNANCE AUDIT RESULT: PASS")
        print("All research governance protocols, test barriers, and hashes verified.")
    else:
        print("PHASE 00 GOVERNANCE AUDIT RESULT: CHECK_REQUIRED")
        print("One or more governance conditions failed verification.")
    print("=" * 70)
    
    return 0 if audit_success else 1


if __name__ == "__main__":
    sys.exit(run_audit())

