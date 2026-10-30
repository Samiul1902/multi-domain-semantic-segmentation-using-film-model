#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PHASE 31 — v1.1 CLOSURE EVIDENCE COMPLETION (read-only verification).

EVIDENCE-PACKAGE COMPLETION ONLY.  This script READS and HASHES existing artifacts.
It regenerates NOTHING, computes NO statistic, reads NO image/GT, runs NO model.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase31_closure_evidence_completion.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"

EXPECT = {
    "reports/audits/phase31_specification_terminal_v1_1.json":
        "7c2ce43cc913c496b0f35dc47523a8d477178f5e37707f3997a027a2f1de540b",
    "reports/audits/phase31_specification_final_check_v1_1.json":
        "64e575ce9a78cfa8f41ba945ba1d94ec513d824e4a1eae72c2ae2db68908cdd3",
    "docs/phase31_statistical_significance_hypothesis_testing_spec_v1_1.md":
        "51a4f44ec4f64f30ef248c7590024811931d037907a7a2875e26e41663c7a212",
    "reports/audits/phase31_execution_eligibility_adjudication_v1_1.json":
        "abbedaff9619e4cd955f2098766b2d882ebaf60b7703090b5e20aada6bac7638",
    "reports/tables/phase31_statistical_test_registry_v1_1.csv":
        "063b10d5734a6e791474aff74e244f031faea47fbeb1cc3130db7816907d4ab1",
    "reports/tables/phase31_specification_completeness_v1_1.csv":
        "cc61580fe9fb8c29f79587882f427543e025834d3631c5fc8a86d43bfbb76975",
    "reports/tables/phase31_hypothesis_provenance_matrix_v1_1.csv":
        "a590423f4db31845c20bb5170cba5b5b5795b641a061f3f1b31de11f4e63f3a9",
    "reports/audits/phase31_hypothesis_matrix_v1_1_reconciliation.json":
        "bf35cff4fc9875652d77ec03bc2b280cfca1365229659230d73f8cd68b6db631",
    "reports/audits/phase31_v1_0_preservation_manifest.json":
        "a8ed880f121185bbfa903e0b223d3ecf0b1c7bc29fef9f47cf4b81371dc83fd6",
}
REQUIRED_STATUS = {
    "H1": "ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE",
    "H2": "ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE",
    "H3": "DESCRIPTIVE_ONLY_BY_PREDECESSOR_AUTHORITY",
    "H4": "ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE",
    "H5": "ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE",
    "H6": "PREOUTCOME_HYPOTHESIS_METHOD_INCOMPLETE",
    "P30-PRIMARY": "ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE",
    "P30-A8VSRANDOM-P": "POST_HOC_EXPLORATORY_ONLY",
    "P30-A7-COMPANION": "DESCRIPTIVE_ONLY_BY_PREDECESSOR_AUTHORITY",
    "C11-JFS": "FORBIDDEN_OR_OUT_OF_SCOPE",
}
VALID = {"CONFIRMATORY_PREOUTCOME_EXACT_METHOD_FROZEN",
         "PREOUTCOME_HYPOTHESIS_METHOD_INCOMPLETE",
         "ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE",
         "DESCRIPTIVE_ONLY_BY_PREDECESSOR_AUTHORITY",
         "POST_HOC_EXPLORATORY_ONLY",
         "FORBIDDEN_OR_OUT_OF_SCOPE"}
EXPECTED_COUNTS = {
    "CONFIRMATORY_PREOUTCOME_EXACT_METHOD_FROZEN": 0,
    "PREOUTCOME_HYPOTHESIS_METHOD_INCOMPLETE": 1,
    "ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE": 5,
    "DESCRIPTIVE_ONLY_BY_PREDECESSOR_AUTHORITY": 2,
    "POST_HOC_EXPLORATORY_ONLY": 1,
    "FORBIDDEN_OR_OUT_OF_SCOPE": 1,
}


def sha256_file(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_json(obj, path) -> None:
    path = Path(path)
    tmp = str(path) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(json.dumps(obj, indent=1) + "\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def main() -> int:
    print("=" * 78)
    print("PHASE 31 v1.1 CLOSURE EVIDENCE COMPLETION (read-only)")
    print("=" * 78)

    # §A/§B/§D/§E — hash existing bytes only
    hashes = []
    for rel, exp in EXPECT.items():
        a = sha256_file(ROOT / rel)
        hashes.append({"path": rel, "expected_sha256": exp, "observed_sha256": a,
                       "match": a == exp})
    hash_ok = all(x["match"] for x in hashes)
    print(f"§A/D/E hashes: {sum(1 for x in hashes if x['match'])}/{len(hashes)} match")

    # §B/§C — matrix verification
    mp = TAB / "phase31_hypothesis_provenance_matrix_v1_1.csv"
    rows = list(csv.DictReader(mp.open(encoding="utf-8")))
    cols = list(rows[0].keys())
    ids = [r["hypothesis_id"] for r in rows]
    nonnull = sum(1 for r in rows if (r.get("current_Phase31_status") or "").strip())
    valid = sum(1 for r in rows if r["current_Phase31_status"] in VALID)
    counts = Counter(r["current_Phase31_status"] for r in rows)
    counts_recon = {k: counts.get(k, 0) for k in VALID}
    status_map_ok = all(
        r["current_Phase31_status"] == REQUIRED_STATUS[r["hypothesis_id"]] for r in rows)
    dup_ids = len(ids) - len(set(ids))
    missing = [h for h in REQUIRED_STATUS if h not in ids]
    extra = [h for h in ids if h not in REQUIRED_STATUS]
    b_ok = (len(rows) == 10 and nonnull == 10 and valid == 10 and counts_recon == EXPECTED_COUNTS
            and sum(counts_recon.values()) == 10 and status_map_ok and dup_ids == 0
            and not missing and not extra)
    print(f"§B/§C matrix: rows={len(rows)} cols={len(cols)} nonnull={nonnull}/10 valid={valid}/10 "
          f"dup={dup_ids} missing={missing} map_ok={status_map_ok}")

    # §D reconciliation record
    rec = json.loads((AUD / "phase31_hypothesis_matrix_v1_1_reconciliation.json")
                     .read_text(encoding="utf-8"))
    rec_ok = (rec["v1_0_csv_preserved"] is True and rec["rows_with_nonnull_status"] == 10
              and rec["rows_with_valid_enumeration"] == 10
              and rec["counts_reconcile_to_10"] is True
              and rec["scientific_classification_unchanged_from_v1_0_markdown"] is True
              and rec["all_pass"] is True)

    audit = {
        "artifact": "phase31_v1_1_closure_evidence_completion_audit", "phase": 31,
        "classification": "EVIDENCE_PACKAGE_COMPLETION_ONLY", "method": "RA-MedFiLM-BARR",
        "specification_revision": "ra_medfilm_barr_phase31_statistics_v1_1",
        "mode": "READ_ONLY_VERIFICATION", "artifacts_regenerated": False,
        "existing_artifact_hashes": hashes, "all_hashes_match": hash_ok,
        "matrix": {
            "path": "reports/tables/phase31_hypothesis_provenance_matrix_v1_1.csv",
            "sha256": sha256_file(mp), "rows": len(rows), "columns": len(cols),
            "column_names": cols, "hypothesis_ids": ids,
            "duplicate_ids": dup_ids, "missing_ids": missing, "extra_ids": extra,
            "rows_with_nonnull_status": nonnull, "rows_with_valid_enumeration": valid,
            "status_map_matches_required": status_map_ok,
            "status_counts": counts_recon, "expected_status_counts": EXPECTED_COUNTS,
            "counts_reconcile_to_10": sum(counts_recon.values()) == 10},
        "matrix_reconciliation_record": {
            "path": "reports/audits/phase31_hypothesis_matrix_v1_1_reconciliation.json",
            "sha256": sha256_file(AUD / "phase31_hypothesis_matrix_v1_1_reconciliation.json"),
            "all_pass": rec["all_pass"], "verified": rec_ok},
        "v1_0_preservation_manifest": {
            "path": "reports/audits/phase31_v1_0_preservation_manifest.json",
            "sha256": sha256_file(AUD / "phase31_v1_0_preservation_manifest.json"),
            "preserved_byte_for_byte": True},
        "zero_action_counters": {
            "new_p_values": 0, "new_effect_sizes": 0, "new_bootstrap_computations": 0,
            "raw_ROUTER_HOLDOUT_image_reads": 0, "raw_ROUTER_HOLDOUT_GT_reads": 0,
            "model_forwards": 0, "training_steps": 0, "TEST_reads": 0, "Phase32_started": False},
        "new_terminal_created": False, "phase31_closure_performed": False,
        "specification_or_scientific_change": False,
        "generated_utc": now_utc(),
        "all_pass": hash_ok and b_ok and rec_ok,
    }
    write_json(audit, AUD / "phase31_v1_1_closure_evidence_completion_audit.json")
    print(f"§F audit written; all_pass={audit['all_pass']}")
    print("NO new terminal created; Phase31 closure NOT performed; Phase32 NOT started.")
    return 0 if audit["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
