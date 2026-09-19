#!/usr/bin/env python3
"""
Phase 03 — Multi-Domain Dataset Discovery Audit Script
Executable entry point for auditing raw dataset discovery, paired sample counts,
TRAIN-only visualization cohort (48 cases), zero test leaks, and image/mask geometry integrity.

Usage:
    D:\\Softfors\\jup\\.venv\\Scripts\\python.exe notebooks/phasewise/phase_03_dataset_discovery/code/phase03_dataset_discovery_audit.py
"""

import sys
import json
import hashlib
from pathlib import Path
import pandas as pd
from PIL import Image


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
    print("PHASE 03 — MULTI-DOMAIN DATASET DISCOVERY & PAIRING AUDIT")
    print("=" * 70)
    print(f"Project Root: {root}")
    print(f"Python Exec:  {sys.executable}")
    print("-" * 70)

    # 1. Verify Canonical Manifest Metadata & Paired Counts
    meta_p = root / "manifests/manifest_metadata.json"
    print("\n[CHECK 1] Canonical Paired Inventory Audit:")
    counts_pass = False
    if meta_p.exists():
        with open(meta_p, "r", encoding="utf-8") as f:
            meta = json.load(f)
        isic_cnt = meta["dataset_counts"]["ISIC"]
        busi_cnt = meta["dataset_counts"]["BUSI"]
        kvasir_cnt = meta["dataset_counts"]["KVASIR"]
        kub_cnt = meta["dataset_counts"]["KUB"]
        total_cnt = meta["authoritative_population"]

        print(f"  - ISIC 2018 Paired Cases : {isic_cnt:,} (Expected: 3,694)")
        print(f"  - BUSI Paired Cases      : {busi_cnt:,} (Expected: 927)")
        print(f"  - Kvasir-SEG Paired Cases: {kvasir_cnt:,} (Expected: 1,000)")
        print(f"  - KUB-Stone Paired Cases : {kub_cnt:,} (Expected: 2,820)")
        print(f"  - Total Paired Inventory : {total_cnt:,} (Expected: 8,441)")
        print(f"  - Historical 8159 Forced : NO ({meta.get('historical_8159_status')})")

        if (isic_cnt == 3694 and busi_cnt == 927 and kvasir_cnt == 1000 and 
            kub_cnt == 2820 and total_cnt == 8441):
            counts_pass = True
            print("  - Status                 : PASS (Exact Reconciled Inventory)")
        else:
            print("  - Status                 : CHECK_REQUIRED")
    else:
        print("  - ERROR: manifests/manifest_metadata.json not found!")

    # 2. Audit TRAIN-Only Sample Selection (48 Cases)
    print("\n[CHECK 2] TRAIN-Only Sample Selection Audit:")
    sel_csv = root / "reports/tables/phase03_train_sample_selection.csv"
    sel_pass = False
    geom_pass = False
    if sel_csv.exists():
        df_sel = pd.read_csv(sel_csv)
        total_sel = len(df_sel)
        counts = df_sel["dataset"].value_counts().to_dict()
        is_train_only = (df_sel["split"] == "TRAIN").all()
        test_cnt = (df_sel["split"] == "TEST").sum()
        val_cnt = (df_sel["split"] == "VAL").sum()

        print(f"  - Total Selected Cases   : {total_sel} (Expected: 48)")
        print(f"  - ISIC Selected Cases    : {counts.get('ISIC', 0)} (Expected: 12)")
        print(f"  - BUSI Selected Cases    : {counts.get('BUSI', 0)} (Expected: 12)")
        print(f"  - Kvasir Selected Cases  : {counts.get('KVASIR', 0)} (Expected: 12)")
        print(f"  - KUB Selected Cases     : {counts.get('KUB', 0)} (Expected: 12)")
        print(f"  - TEST Selected Cases    : {test_cnt} (STRICTLY REQUIRED: 0)")
        print(f"  - VAL Selected Cases     : {val_cnt} (STRICTLY REQUIRED: 0)")
        print(f"  - Strict TRAIN Split Only: {'YES' if is_train_only else 'NO'}")

        if (total_sel == 48 and counts.get('ISIC') == 12 and counts.get('BUSI') == 12 and 
            counts.get('KVASIR') == 12 and counts.get('KUB') == 12 and is_train_only and test_cnt == 0):
            sel_pass = True

        # 3. Geometry Alignment Check for All 48 Cases
        print("\n[CHECK 3] Image & Mask Spatial Alignment Audit:")
        geom_mismatches = 0
        file_missing = 0
        for _, row in df_sel.iterrows():
            img_p = Path(row["image_path_or_canonical_reference"])
            mask_p = Path(row["mask_path_or_canonical_reference"])
            if not img_p.exists() or not mask_p.exists():
                file_missing += 1
                continue
            with Image.open(img_p) as im, Image.open(mask_p) as m:
                if im.size != m.size:
                    geom_mismatches += 1

        print(f"  - Missing Files          : {file_missing}")
        print(f"  - Dimension Mismatches   : {geom_mismatches}")
        if file_missing == 0 and geom_mismatches == 0:
            geom_pass = True
            print("  - Spatial Pairing Check  : PASS (100% Geometry Alignment Verified)")
        else:
            print("  - Spatial Pairing Check  : FAIL")
    else:
        print("  - ERROR: reports/tables/phase03_train_sample_selection.csv not found!")

    # 4. Immutability of Foundational Notebooks
    print("\n[CHECK 4] Cryptographic Immutability of Foundational Notebooks:")
    p00_p = root / "notebooks/phasewise/phase_00_governance/phase00_governance_reproducibility_and_protocol.ipynb"
    p00_exp = "60e0bc1745482e244dacfbe376526158fb4ead8ced8c4dc264e615e6e6e1afa0"
    p00_act = compute_sha256(p00_p)
    p00_match = (p00_act == p00_exp)
    print(f"  - Phase 00 Notebook SHA  : {'MATCH' if p00_match else 'MISMATCH'}")

    p01_p = root / "notebooks/phasewise/phase_01_project_initialization/phase01_project_initialization_and_repository_architecture.ipynb"
    p01_exp = "0cd21fc49b29067e73c467a5a76105ba65ed19de3fc40cf2b43cf5bcaea97e8e"
    p01_act = compute_sha256(p01_p)
    p01_match = (p01_act == p01_exp)
    print(f"  - Phase 01 Notebook SHA  : {'MATCH' if p01_match else 'MISMATCH'}")

    p02_p = root / "notebooks/phasewise/phase_02_environment_cuda/phase02_environment_cuda_and_reproducibility_validation.ipynb"
    p02_exp = "9b6d8621cc8b77eb9814d95ac1ade5e6c9aa3587a57246697f8bc99943cbed17"
    p02_act = compute_sha256(p02_p)
    p02_match = (p02_act == p02_exp)
    print(f"  - Phase 02 Notebook SHA  : {'MATCH' if p02_match else 'MISMATCH'}")

    p14_p = root / "notebooks/13_phase14_regional_refiner_diagnostic.ipynb"
    p14_exp = "b5b329d1d100138db640e4a3e91069a4008a434d998945646bc7a4522c040948"
    p14_act = compute_sha256(p14_p)
    p14_match = (p14_act == p14_exp)
    print(f"  - Phase 14 Canonical SHA : {'MATCH' if p14_match else 'MISMATCH'}")

    # Summary
    print("\n" + "=" * 70)
    overall_pass = (counts_pass and sel_pass and geom_pass and p00_match and 
                    p01_match and p02_match and p14_match)
    if overall_pass:
        print("PHASE 03 DATASET DISCOVERY AUDIT RESULT: PASS")
        print("Authoritative paired counts, 48 TRAIN samples, and geometry verified.")
    else:
        print("PHASE 03 DATASET DISCOVERY AUDIT RESULT: CHECK_REQUIRED")
    print("=" * 70)

    return 0 if overall_pass else 1


if __name__ == "__main__":
    sys.exit(run_audit())

