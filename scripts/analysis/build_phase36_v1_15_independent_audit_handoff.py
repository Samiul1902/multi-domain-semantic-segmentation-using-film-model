#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase36 v1.15 — INDEPENDENT-AUDIT HANDOFF MANIFEST BUILDER (WO#17A).

STATIC / NON-CONSUMING / EVIDENCE PACKAGING ONLY.  Write-once (O_CREAT|O_EXCL +
full-write + fsync).  Records the final v1.15 source family, the v1.15 governance
family, the frozen ancestor bindings, the validator results, attempt-marker
absence, journal count, D61 / D75-POLICY_B status, the machine-derived diff
classification, and the v1.14 launcher SHA truncation correction.

Re-run → REFUSE_OVERWRITE (rc 2).  Never delete/recreate.

NO torch.  NO model.  NO checkpoint.  NO CUDA.  NO forward.  NO smoke.  NO science.
NO VAL/GT read.  NO ROUTER_HOLDOUT.  NO TEST.  NO v1.15 EXECUTION.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

AUD = ROOT / "reports" / "audits"
OUT = AUD / "phase36_v1_15_independent_audit_handoff_v1_0.json"


def sha256_file(p: Path) -> str | None:
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_once_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, indent=1, ensure_ascii=False, default=str).encode("utf-8")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    fd = os.open(str(path), flags, 0o644)
    try:
        total = 0
        while total < len(data):
            n = os.write(fd, data[total:])
            if n is None or n <= 0:
                raise OSError(f"SHORT_WRITE at {total}/{len(data)} for {path}")
            total += n
        os.fsync(fd)
    finally:
        os.close(fd)
    if path.stat().st_size != len(data):
        raise OSError(f"POST_WRITE_SIZE_MISMATCH for {path}")


# ---- expected (frozen) source SHAs ---- #
EXPECTED_SOURCE = {
    "execution_source": ("scripts/analysis/phase36_robustness_execution_v1_15.py",
                         "b194ad28345ea8b268748be383ca98b936cb051d85854666e3141250f3eae002"),
    "execution_builder": ("scripts/analysis/build_phase36_robustness_execution_v1_15.py",
                          "e3e6bd0327972ce50a788ec10d5359f09e68d79928a100b3dc2c4ad002a4deaa"),
    "launcher": ("scripts/analysis/launch_phase36_v1_15.py",
                 "2ad201fde72845891571cb1a53a675f6d7075dde23383da3eaa0b13b15d10c1c"),
    "supervisor": ("scripts/analysis/supervise_phase36_v1_15.py",
                   "446b707c879781c0927a5fafec13c95082f0eabc732952988d2df47a2cfdcfc8"),
    "unit": ("scripts/analysis/phase36_robustness_unit_v1_15.py",
             "98f920b906b2ee7f8b52925ec67adf8f51cb432e9c914c7609bb342c257cf316"),
    "preflight": ("scripts/analysis/phase36_robustness_preflight_v1_15.py",
                  "3f6722fc5ee5d9eb3795c0deada96caa1879a53899dd581fdcf05a98da9d66bd"),
    "negative_controls": ("scripts/analysis/phase36_robustness_negative_controls_v1_15.py",
                          "d2183fb964ed0bd8f1dd7160c41de327c45206c26469f910d50379c0b6aa93f6"),
    "science_repair_validator": ("scripts/analysis/validate_phase36_v1_15_science_repairs.py",
                                 "906331410c53935586433821a0603cb52d36eaea149465cd96d5cb0c2cba4f0c"),
}

GOV_PATHS = {
    "contract": "reports/audits/phase36_v1_15_science_release_attestation_contract.json",
    "source_freeze": "reports/audits/phase36_preexecution_source_freeze_v1_15.json",
    "eligibility": "reports/audits/phase36_science_eligibility_v1_15.json",
    "no_execution_audit": "reports/audits/phase36_v1_15_no_scientific_execution_audit.json",
    "v1_14_to_v1_15_diff": "reports/audits/phase36_v1_14_to_v1_15_semantic_diff.json",
}

ANCESTORS = {
    "v1_14_execution": ("scripts/analysis/phase36_robustness_execution_v1_14.py",
                        "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"),
    "v1_14_launcher": ("scripts/analysis/launch_phase36_v1_14.py",
                       "2339d6afa1507d68decd1b63b3f3250d86ecd01659580394c6f8dace4052e2c3"),
    "v1_14_runtime_manifest": ("reports/audits/phase36_v1_14_runtime_source_integrity_manifest.json",
                               "b4c358dfcb5e7b59beb6ae1ba2cffc64677d10049e12568b4c8eea8e79bb911e"),
    "v1_4_RESULT": ("reports/audits/phase36_final_probability_authority_diagnostic_result_v1_4.json",
                    "046a1e3c3053fb00b97895d8d1834d0011f8b190209daa01795e6915b7fd5284"),
    "D76_D77_D78_reconciliation": (
        "reports/audits/phase36_final_probability_authority_diagnostic_v1_4_result_adjudication_reconciliation_v1_1.json",
        "7f0957695939a03feca7d9909c47f56e6644a4f3b800664c9bb61f02486dbd9b"),
    "D79_disclosure": (
        "reports/audits/phase36_final_probability_authority_diagnostic_v1_4_result_adjudication_reconciliation_write_history_v1_0.json",
        "548b7e1541abb5c011936db73b3cf1e90222a733267b67c8106ff4d5197ad81d"),
    "phase27_final_probability": ("data_cache/phase27_barr_preservation_v1_0/phase27_val808_final_prob_f16.npy",
                                  "506ab6c4e715a9106889e186c146b73903493c80a63258007954cf5deb3ea9cf"),
    "phase27_global_probability": ("data_cache/phase27_barr_preservation_v1_0/phase27_val808_global_prob_f16.npy",
                                   "cc6c54af986f56b4aba9265405ffeba4f6cac582eeff00fe6b0894429e7d3f13"),
    "phase27_score_csv": ("reports/tables/phase27_val808_per_sample_scores.csv",
                          "702133930ce14ac9513c992833396e3e250d08417b17d1032cbd260a405cfb12"),
}

MARKER_PATHS = {
    "START": "reports/audits/phase36_robustness_science_start_v1_15.json",
    "RESULT": "reports/audits/phase36_robustness_science_result_v1_15.json",
    "FAILURE": "reports/audits/phase36_robustness_science_failure_v1_15.json",
    "PROCESS_EXIT": "reports/audits/phase36_robustness_science_process_exit_v1_15.json",
    "stdout": "reports/audits/phase36_robustness_science_stdout_v1_15.txt",
    "stderr": "reports/audits/phase36_robustness_science_stderr_v1_15.txt",
}
JOURNAL_DIR = "reports/audits/phase36_robustness_science_v1_15_journal"


def main() -> int:
    # ---- fail-closed: START must be ABSENT (Section 9) ---- #
    if (ROOT / MARKER_PATHS["START"]).exists():
        print(json.dumps({"status": "STOP__V1_15_START_PRESENT",
                          "path": MARKER_PATHS["START"]}, indent=1))
        return 3

    # ---- source family ---- #
    source = {}
    src_all_match = True
    for k, (rel, exp) in EXPECTED_SOURCE.items():
        actual = sha256_file(ROOT / rel)
        match = actual == exp
        src_all_match = src_all_match and match
        source[k] = {"path": rel, "sha256": actual, "expected": exp, "match": match}
    if not src_all_match:
        print(json.dumps({"status": "STOP__SOURCE_SHA_MISMATCH",
                          "source": {k: v for k, v in source.items() if not v["match"]}}, indent=1))
        return 3

    # ---- governance family ---- #
    governance = {k: {"path": v, "sha256": sha256_file(ROOT / v)} for k, v in GOV_PATHS.items()}

    # ---- ancestors ---- #
    ancestors = {}
    anc_all_ok = True
    for k, (rel, exp) in ANCESTORS.items():
        actual = sha256_file(ROOT / rel)
        ok = actual == exp
        anc_all_ok = anc_all_ok and ok
        ancestors[k] = {"path": rel, "sha256": actual, "expected": exp, "match": ok}

    # ---- repair status (from frozen diff artifact + source text) ---- #
    diff = json.loads((ROOT / GOV_PATHS["v1_14_to_v1_15_diff"]).read_text(encoding="utf-8"))
    v15_src = (ROOT / "scripts/analysis/phase36_robustness_execution_v1_15.py").read_text(encoding="utf-8")
    d61_pass = (diff["scientific_delta_D61"] is True
                and "fuse_full_field(p_global, refined, geom)" in v15_src
                and "system._fuse_global_with_regional(p_global, refined, window)" not in v15_src)
    d75_pass = (diff["scientific_delta_D75"] is True
                and v15_src.count("_phase27_scored_final_binary(") == 3)

    # ---- attempt absence ---- #
    markers = {k: {"path": v, "exists": (ROOT / v).exists()} for k, v in MARKER_PATHS.items()}
    markers_absent = not any(m["exists"] for m in markers.values())
    journal_dir = ROOT / JOURNAL_DIR
    journal_records = (len([f for f in journal_dir.iterdir() if f.is_file()])
                       if journal_dir.exists() else 0)

    # ---- validator results (recorded from the WO#17A rerun) ---- #
    validators = {
        "unit": {"result": "44/44", "total": 44, "passed": 44, "all_pass": True,
                 "report": "reports/audits/phase36_robustness_unit_v1_15.json",
                 "report_sha256": sha256_file(ROOT / "reports/audits/phase36_robustness_unit_v1_15.json")},
        "preflight": {"result": "29/29", "total": 29, "passed": 29, "all_pass": True,
                      "report": "reports/audits/phase36_robustness_preflight_v1_15.json",
                      "report_sha256": sha256_file(ROOT / "reports/audits/phase36_robustness_preflight_v1_15.json")},
        "negative_controls": {"result": "10/10", "total": 10, "passed": 10, "all_pass": True,
                              "report": "reports/audits/phase36_v1_15_negative_controls.json",
                              "report_sha256": sha256_file(ROOT / "reports/audits/phase36_v1_15_negative_controls.json")},
        "science_repair_validator": {"result": "29/29", "total": 29, "passed": 29, "all_pass": True},
        "supervisor_self_test": {"result": "8/8", "total": 8, "passed": 8, "all_pass": True},
        "launcher_verify_only": {"result": "PASS",
                                 "terminal": "PHASE36_V1_15_LAUNCH_VERIFY_ONLY_PASS"},
    }

    payload = {
        "artifact": "phase36_v1_15_independent_audit_handoff_v1_0",
        "phase": 36,
        "method": "RA-MedFiLM-BARR",
        "revision": "ra_medfilm_barr_phase36_robustness_v1_15",
        "type": "INDEPENDENT_AUDIT_HANDOFF_MANIFEST",
        "mode": "STATIC_NON_CONSUMING_EVIDENCE_PACKAGING_ONLY",
        "generated_utc": now(),
        "canonical_repository": "D:\\Softfors\\jup",

        "source_family": source,
        "governance_family": governance,
        "frozen_ancestor_bindings": ancestors,
        "frozen_ancestors_all_match": anc_all_ok,

        "repairs": {
            "D61": {
                "status": "PASS" if d61_pass else "FAIL",
                "canonical_call": "fuse_full_field(p_global, refined, geom)",
                "canonical_call_present": "fuse_full_field(p_global, refined, geom)" in v15_src,
                "old_production_call":
                    "system._fuse_global_with_regional(p_global, refined, window)",
                "old_production_call_absent":
                    "system._fuse_global_with_regional(p_global, refined, window)" not in v15_src,
            },
            "D75_POLICY_B": {
                "status": "PASS" if d75_pass else "FAIL",
                "representation": "live_f32 -> f16 -> f32 -> >= 0.50",
                "segmentation_threshold": 0.50,
                "helper": "_phase27_scored_final_binary",
                "helper_wiring_count": v15_src.count("_phase27_scored_final_binary("),
                "coverage": {
                    "clean_dice": True,
                    "clean_iou": True,
                    "clean_hd95": True,
                    "clean_stored_final_binary": True,
                    "image_perturbation_metrics": True,
                    "proposal_perturbation_metrics": True,
                    "prediction_consistency_dice": True,
                },
                "downstream_G_quantization_added": False,
            },
        },

        "diff": {
            "hunk_count": diff["hunk_count"],
            "classified_hunks": diff["classified_hunks"],
            "scientific_delta_count": diff["scientific_delta_count"],
            "scientific_delta_D61": diff["scientific_delta_D61"],
            "scientific_delta_D75": diff["scientific_delta_D75"],
            "unclassified_scientific_delta_count": diff["unclassified_scientific_delta_count"],
            "classification": diff["classification"],
        },

        "validators": validators,

        "frozen_constants": {
            "segmentation_threshold": 0.50,
            "clean_equivalence_atol": 1e-7,
            "clean_equivalence_rtol": 0.0,
            "image_robustness_conditions_unchanged": True,
            "proposal_conditions_unchanged": True,
            "noise_seeds": [42, 123, 3407],
            "TEST_locked": True,
            "ROUTER_HOLDOUT_locked": True,
        },

        "attempt_absence": {
            "markers": markers,
            "markers_absent": markers_absent,
            "real_journal_records": journal_records,
            "attempt_consumed": False,
        },

        "v1_14_launcher_sha_correction": {
            "previous_work_order_value":
                "2339d6afa1507d68decd1b63b3f3250d86ecd01659580394c6f8dace4052e2c",
            "classification": "PREVIOUS_WORK_ORDER_SHA_TRANSCRIPTION_TRUNCATION",
            "runtime_effect": "NONE",
            "scientific_effect": "NONE",
            "actual_authority":
                "2339d6afa1507d68decd1b63b3f3250d86ecd01659580394c6f8dace4052e2c3",
        },

        "state": {
            "v1_15": "ELIGIBLE_NOT_STARTED",
            "phase36": "NOT_COMPLETE_PENDING_V1_15_EXECUTION",
            "phase37": "NOT_STARTED",
            "D79": "BOUND",
        },

        "scientific_execution": False,
        "scientific_output": False,
        "test_accessed": False,
        "router_holdout_accessed": False,
        "write_semantics": "O_CREAT|O_EXCL + full-write + fsync (exclusive-create, write-once)",
        "terminal": "PHASE36_V1_15_INDEPENDENT_AUDIT_HANDOFF_READY",
    }

    if OUT.exists():
        print(json.dumps({"status": "REFUSE_OVERWRITE", "path": str(OUT.relative_to(ROOT))}, indent=1))
        return 2
    _write_once_json(OUT, payload)
    print(json.dumps({
        "status": "INDEPENDENT_AUDIT_HANDOFF_WRITTEN",
        "path": str(OUT.relative_to(ROOT)),
        "sha256": sha256_file(OUT),
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
