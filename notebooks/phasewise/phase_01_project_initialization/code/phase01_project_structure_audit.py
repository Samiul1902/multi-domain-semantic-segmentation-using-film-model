#!/usr/bin/env python3
"""
Phase 01 — Project Structure & Initialization Audit Script
Executable entry point for verifying repository architecture, directory layouts,
governance source-of-truth files, and notebooks root cleanup audit.

Usage:
    D:\\Softfors\\jup\\.venv\\Scripts\\python.exe notebooks/phasewise/phase_01_project_initialization/code/phase01_project_structure_audit.py
"""

import sys
import os
import csv
import json
import hashlib
from pathlib import Path


def find_project_root() -> Path:
    p = Path(__file__).resolve()
    for _ in range(6):
        if (p / 'reports').exists() and (p / 'manifests').exists() and (p / 'src').exists():
            return p
        p = p.parent
    return Path('D:/Softfors/jup')


def compute_sha256(file_path: Path) -> str:
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
    print("PHASE 01 — PROJECT INITIALIZATION & REPOSITORY ARCHITECTURE AUDIT")
    print("=" * 70)
    print(f"Project Root: {root}")
    print(f"Python:       {sys.executable}")
    print("-" * 70)

    # 1. Verify Top-Level Scientific Directories
    required_dirs = [
        "src",
        "scripts",
        "configs",
        "checkpoints",
        "reports",
        "notebooks",
        "manifests",
        "notebooks/phasewise"
    ]
    print("\n[CHECK 1] Top-Level Scientific Directories:")
    dirs_pass = True
    for d in required_dirs:
        dp = root / d
        exists = dp.exists() and dp.is_dir()
        print(f"  - {d:25s} : {'EXISTS' if exists else 'MISSING'}")
        if not exists:
            dirs_pass = False

    # 2. Canonical Project Path Configuration
    print("\n[CHECK 2] Canonical Path Configuration:")
    paths = {
        "Project Root": str(root),
        "Source Modules": str(root / "src"),
        "Manifests": str(root / "manifests"),
        "Checkpoints": str(root / "checkpoints"),
        "Reports": str(root / "reports"),
        "Phasewise Root": str(root / "notebooks/phasewise")
    }
    for k, v in paths.items():
        print(f"  - {k:18s} : {v}")

    # 3. Audit Notebooks Root Items & Cleanup Audit Table
    print("\n[CHECK 3] Notebooks Root Cleanup Audit Status:")
    audit_csv = root / "reports/audits/notebooks_root_cleanup_audit.csv"
    nb_audit_pass = False
    if audit_csv.exists():
        with open(audit_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        print(f"  - Total Audited Items in notebooks/: {len(rows)}")
        from collections import Counter
        counts = Counter([r['action'] for r in rows])
        for act, cnt in counts.items():
            print(f"    * {act:25s}: {cnt}")
        nb_audit_pass = True
    else:
        print("  - ERROR: notebooks_root_cleanup_audit.csv not found!")

    # 4. Verify Phase 00 and Canonical Phase 14 Integrity
    print("\n[CHECK 4] Cryptographic Hashing of Foundational Provenance:")
    phase00_nb = root / "notebooks/phasewise/phase_00_governance/phase00_governance_reproducibility_and_protocol.ipynb"
    expected_phase00_sha = "60e0bc1745482e244dacfbe376526158fb4ead8ced8c4dc264e615e6e6e1afa0"
    actual_phase00_sha = compute_sha256(phase00_nb)
    p00_pass = (actual_phase00_sha == expected_phase00_sha)
    print(f"  - Phase 00 Accepted Notebook:")
    print(f"    Expected : {expected_phase00_sha}")
    print(f"    Actual   : {actual_phase00_sha}")
    print(f"    Match    : {'MATCH (ACCEPTED PROVENANCE)' if p00_pass else 'MISMATCH'}")

    phase14_nb = root / "notebooks/13_phase14_regional_refiner_diagnostic.ipynb"
    expected_phase14_sha = "b5b329d1d100138db640e4a3e91069a4008a434d998945646bc7a4522c040948"
    actual_phase14_sha = compute_sha256(phase14_nb)
    p14_pass = (actual_phase14_sha == expected_phase14_sha)
    print(f"  - Phase 14 Canonical Notebook:")
    print(f"    Expected : {expected_phase14_sha}")
    print(f"    Actual   : {actual_phase14_sha}")
    print(f"    Match    : {'MATCH (IMMUTABLE CANONICAL)' if p14_pass else 'MISMATCH'}")

    # 5. Summary & Decision
    print("\n" + "=" * 70)
    audit_success = dirs_pass and nb_audit_pass and p00_pass and p14_pass
    if audit_success:
        print("PHASE 01 PROJECT STRUCTURE AUDIT RESULT: PASS")
        print("Repository architecture, canonical pathways, and provenance verified.")
    else:
        print("PHASE 01 PROJECT STRUCTURE AUDIT RESULT: CHECK_REQUIRED")
    print("=" * 70)

    return 0 if audit_success else 1


if __name__ == "__main__":
    sys.exit(run_audit())

