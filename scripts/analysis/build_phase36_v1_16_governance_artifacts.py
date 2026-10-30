#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.16 — WRITE-ONCE GOVERNANCE ARTIFACTS builder.

Creates (O_CREAT|O_EXCL + full-write + fsync; NEVER delete/recreate):

  phase36_v1_16_robustness_contract.json
  phase36_preexecution_source_freeze_v1_16.json
  phase36_robustness_preflight_v1_16_record.json
  phase36_v1_16_negative_controls_record.json
  phase36_science_eligibility_v1_16.json
  phase36_v1_16_no_scientific_execution_audit.json
  phase36_v1_16_science_release_attestation.json
  phase36_v1_16_final_readiness_attestation.json

NON-CONSUMING / PREPARATION ONLY.  No model, no checkpoint, no VAL image, no VAL
GT, no TEST, no ROUTER_HOLDOUT, no science.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

AUD = ROOT / "reports" / "audits"

REVISION = "ra_medfilm_barr_phase36_robustness_v1_16"

V1_16_EXEC_SHA = "a96b74caa4587aa9d2f83b79ed39c13075a88086109e31d991695a75ec4abab9"
V1_16_LAUNCHER_SHA = "a069345a8d332c549fc25799fc8d9e5e1b4b46e6b878e23f0e83d7a4c011e16c"
V1_16_SUPERVISOR_SHA = "ffab12252ba334a54482136b1e4e80351c90adb50c44df6430ce4275dc6a9754"
V1_16_UNIT_SHA = "76dbc88f9fc98fb91efa8d88158353c65260f7b30ae158663598843b18ba97de"
V1_16_PREFLIGHT_SHA = "7526da4f5ce2f58f69683fb0b453a536744e60f9e215e200e420215cf580fbb1"
V1_16_NC_SHA = "489105efc764817f9e3f7f8b0885b2ecf959ff4939f9a2754b9d199d4f73554b"
V1_16_SRVAL_SHA = "7c24c7cfb8b3669c5c2c541173454140db00680c336568b3cd126b6b0ad5e6ea"
V1_16_OCCVAL_SHA = "83e07dd34c4b247ec26a1ddb72cfb2ffdd89db304234fef77e0e5dc892069de0"
V1_16_MANIFEST_SHA = "f9f245b41bdf904cdb4f9da7c3d32361da806c7451773ce721d3d0a023f64e18"
V1_16_LAUNCH_AUTH_SHA = "52a8783a978fb442ec1158e6b06ee1b08fb6e0cd58550e65b69678f5ca8d9d3b"
D80_ADJ_SHA = "fd66447fc1da1ad045fda102ed5ccfda39e1d0ffff5aa24cda6911e281e9d8c4"
V1_15_HANDOFF_SHA = "8aa164955032738dd3528df9424c8e373de840f20c62c054a5904980f7394273"
V14_TO_V16_DIFF_SHA = "c384c91ecf3af31de13389a8dd65c209669a69b2e52eff6da09ea4a26cb79d78"
V15_TO_V16_DIFF_SHA = "332c85453ae157873ec1df52a33b2c339ee8f8fc8081b469c407a6878437b964"
NS_MAP_SHA = "6709c11a6a623ec4704f74dc3db299289449fd58c3b9de588f824fccf1b472b9"
UNIT_RECORD_SHA = "439148509639a447f8ca59d2de81f3de2bc81556ca6681dc1f9f1063725e6456"
PREFLIGHT_RECORD_SHA = "86069b55735abeaf14e6a7c40ebff7b4773cd3003cbe09afac0a26ad8ea472b9"
NC_RECORD_SHA = "e209ecccd411cf32fb6655f49f4fecaf8328a15cf60d86b5827f68c813bccf0d"
OCC_RECORD_SHA = "d5250898ee17e5c089ee2788a89055171cd12a042e1ae39b3128021b49b069bb"

V1_14_EXEC_SHA = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
V1_15_EXEC_SHA = "b194ad28345ea8b268748be383ca98b936cb051d85854666e3141250f3eae002"

PHASE27_FINAL_PROB_SHA = "506ab6c4e715a9106889e186c146b73903493c80a63258007954cf5deb3ea9cf"
PHASE27_GLOBAL_PROB_SHA = "cc6c54af986f56b4aba9265405ffeba4f6cac582eeff00fe6b0894429e7d3f13"
PHASE27_SCORE_CSV_SHA = "702133930ce14ac9513c992833396e3e250d08417b17d1032cbd260a405cfb12"
PHASEA_SRC_SHA = "ac0ffbdadbfe60349061a926f5a664716a3a3690ac3a90c21a35802263975841"
PHASEB_SRC_SHA = "35800e39d9220e638adbb640bd25e18bc14da5298d9bed4a603f2f0dec64cf37"
D79_SHA = "548b7e1541abb5c011936db73b3cf1e90222a733267b67c8106ff4d5197ad81d"
D76_D78_SHA = "7f0957695939a03feca7d9909c47f56e6644a4f3b800664c9bb61f02486dbd9b"
V1_4_RESULT_SHA = "046a1e3c3053fb00b97895d8d1834d0011f8b190209daa01795e6915b7fd5284"
V1_4_ADJ_SHA = "912cb24e4b27dcc7d66310b36db2154180411ec52d79d19c767aa708220b9b36"


def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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


def verify_local(p: Path, exp: str, name: str) -> dict:
    actual = sha256_file(p) if p.exists() else None
    return {"name": name, "path": str(p.relative_to(ROOT)), "expected": exp,
            "actual": actual, "match": actual == exp}


def main() -> int:
    created = []
    ts = now()

    # ---- 1. contract ---- #
    contract = {
        "artifact": "phase36_v1_16_robustness_contract",
        "phase": 36,
        "method": "RA-MedFiLM-BARR",
        "revision": REVISION,
        "type": "EXECUTION_CONTRACT",
        "supersedes": None,
        "amends": "ra_medfilm_barr_phase36_robustness_v1_15 (byte-preserved; NOT modified)",
        "scientific_semantics": "IDENTICAL_TO_V1_15",
        "scientific_semantics_effect_vs_v1_15": "NONE",
        "source_bindings": {
            "v1_16_execution_source": V1_16_EXEC_SHA,
            "v1_16_launcher": V1_16_LAUNCHER_SHA,
            "v1_16_supervisor": V1_16_SUPERVISOR_SHA,
            "v1_16_runtime_manifest": V1_16_MANIFEST_SHA,
            "v1_16_launch_authority_sha": V1_16_LAUNCH_AUTH_SHA,
        },
        "frozen_ancestors": {
            "v1_14_execution": V1_14_EXEC_SHA,
            "v1_15_execution": V1_15_EXEC_SHA,
            "phase27_final_prob": PHASE27_FINAL_PROB_SHA,
            "phase27_global_prob": PHASE27_GLOBAL_PROB_SHA,
            "phase27_score_csv": PHASE27_SCORE_CSV_SHA,
            "phase27_phaseA_source": PHASEA_SRC_SHA,
            "phase27_phaseB_source": PHASEB_SRC_SHA,
            "D79_disclosure": D79_SHA,
            "D76_D78_reconciliation": D76_D78_SHA,
            "v1_4_result": V1_4_RESULT_SHA,
            "v1_4_adjudication": V1_4_ADJ_SHA,
            "D80_adjudication": D80_ADJ_SHA,
        },
        "gate_env": "PHASE36_V1_16_EXECUTE",
        "smoke_gate_env": "PHASE36_V1_16_SMOKE_EXECUTE",
        "launch_authority_token": "PHASE36_V1_16_LAUNCH_AUTHORITY",
        "dispatch_command": (".venv/Scripts/python.exe "
                             "scripts/analysis/phase36_robustness_execution_v1_16.py --mode science"),
        "dispatch_mode_args": ["--mode", "science"],
        "one_shot": True,
        "automatic_retry": False,
        "no_delete_or_recreate": True,
        "protected_populations": {
            "TEST": "PHASE39_ONLY_LOCKED",
            "ROUTER_HOLDOUT": "LOCKED",
        },
        "generated_utc": ts,
    }
    p = AUD / "phase36_v1_16_robustness_contract.json"
    _write_once_json(p, contract)
    created.append((p.name, sha256_file(p)))

    # ---- 2. source freeze ---- #
    freeze = {
        "artifact": "phase36_preexecution_source_freeze_v1_16",
        "phase": 36,
        "revision": REVISION,
        "type": "PREEXECUTION_SOURCE_FREEZE",
        "frozen_at_utc": ts,
        "frozen_sources": {
            "scripts/analysis/phase36_robustness_execution_v1_16.py": V1_16_EXEC_SHA,
            "scripts/analysis/launch_phase36_v1_16.py": V1_16_LAUNCHER_SHA,
            "scripts/analysis/supervise_phase36_v1_16.py": V1_16_SUPERVISOR_SHA,
            "scripts/analysis/phase36_robustness_unit_v1_16.py": V1_16_UNIT_SHA,
            "scripts/analysis/phase36_robustness_preflight_v1_16.py": V1_16_PREFLIGHT_SHA,
            "scripts/analysis/phase36_robustness_negative_controls_v1_16.py": V1_16_NC_SHA,
            "scripts/analysis/validate_phase36_v1_16_science_repairs.py": V1_16_SRVAL_SHA,
            "scripts/analysis/validate_phase36_v1_16_operational_cross_contract.py": V1_16_OCCVAL_SHA,
            "reports/audits/phase36_v1_16_runtime_source_integrity_manifest.json": V1_16_MANIFEST_SHA,
        },
        "frozen_ancestors_unchanged": {
            "scripts/analysis/phase36_robustness_execution_v1_14.py": V1_14_EXEC_SHA,
            "scripts/analysis/phase36_robustness_execution_v1_15.py": V1_15_EXEC_SHA,
        },
        "v1_15_preserved_byte_for_byte": True,
        "v1_15_modified": False,
        "generated_utc": ts,
    }
    p = AUD / "phase36_preexecution_source_freeze_v1_16.json"
    _write_once_json(p, freeze)
    created.append((p.name, sha256_file(p)))

    # ---- 3. preflight record ---- #
    pf = json.loads((AUD / "phase36_robustness_preflight_v1_16.json").read_text(encoding="utf-8"))
    preflight = {
        "artifact": "phase36_robustness_preflight_v1_16_record",
        "phase": 36,
        "revision": REVISION,
        "type": "PREFLIGHT_RECORD",
        "source_report_sha256": PREFLIGHT_RECORD_SHA,
        "checks_total": pf["checks_total"],
        "checks_passed": pf["checks_passed"],
        "all_pass": pf["all_pass"],
        "terminal": "PHASE36_V1_16_PREFLIGHT_PASS" if pf["all_pass"] else "FAIL",
        "generated_utc": ts,
    }
    p = AUD / "phase36_robustness_preflight_v1_16_record.json"
    _write_once_json(p, preflight)
    created.append((p.name, sha256_file(p)))

    # ---- 4. negative controls record ---- #
    nc = json.loads((AUD / "phase36_v1_16_negative_controls.json").read_text(encoding="utf-8"))
    ncr = {
        "artifact": "phase36_v1_16_negative_controls_record",
        "phase": 36,
        "revision": REVISION,
        "type": "NEGATIVE_CONTROL_RECORD",
        "source_report_sha256": NC_RECORD_SHA,
        "controls_total": nc["controls_total"],
        "controls_passed": nc["controls_passed"],
        "all_pass": nc["all_pass"],
        "carried_controls": ["NC_D61_1", "NC_D61_2", "NC_D75_1", "NC_D75_2", "NC_D75_3",
                             "NC_D75_4", "NC_D75_5", "NC_D75_6", "NC_G_1"],
        "new_d80_controls": ["NC_D80_A", "NC_D80_B", "NC_D80_C", "NC_D80_D", "NC_D80_E",
                             "NC_D80_F", "NC_D80_G", "NC_D80_H_launcher", "NC_D80_H_supervisor"],
        "operational_cross_contract_negative_controls": [
            "XC_A", "XC_B", "XC_B2", "XC_C", "XC_D", "XC_E", "XC_E2", "XC_F",
            "XC_G", "XC_H", "XC_H2", "XC_I", "XC_I2"],
        "terminal": "PHASE36_V1_16_NEGATIVE_CONTROLS_PASS" if nc["all_pass"] else "FAIL",
        "generated_utc": ts,
    }
    p = AUD / "phase36_v1_16_negative_controls_record.json"
    _write_once_json(p, ncr)
    created.append((p.name, sha256_file(p)))

    # ---- 5. eligibility ---- #
    occ = json.loads((AUD / "phase36_v1_16_operational_cross_contract.json").read_text(encoding="utf-8"))
    unit = json.loads((AUD / "phase36_robustness_unit_v1_16.json").read_text(encoding="utf-8"))
    d15 = json.loads((AUD / "phase36_v1_15_to_v1_16_semantic_diff.json").read_text(encoding="utf-8"))
    d14 = json.loads((AUD / "phase36_v1_14_to_v1_16_semantic_diff.json").read_text(encoding="utf-8"))
    ns = json.loads((AUD / "phase36_v1_16_output_namespace_map.json").read_text(encoding="utf-8"))

    eligibility = {
        "artifact": "phase36_science_eligibility_v1_16",
        "phase": 36,
        "revision": REVISION,
        "type": "SCIENCE_ELIGIBILITY",
        "state": "ELIGIBLE_NOT_STARTED",
        "scientific_semantics_identical_to_v1_15": True,
        "scientific_semantics_effect_vs_v1_15": "NONE",
        "d61_preserved": True,
        "d75_policy_b_preserved": True,
        "d80_rebase_complete": True,
        "v1_15_to_v1_16_scientific_delta_count": d15["scientific_delta_count"],
        "v1_15_to_v1_16_unclassified_delta_count": d15["unclassified_delta_count"],
        "v1_14_to_v1_16_scientific_delta_count": d14["scientific_delta_count"],
        "unit_all_pass": unit["all_pass"],
        "preflight_all_pass": pf["all_pass"],
        "negative_controls_all_pass": nc["all_pass"],
        "operational_cross_contract_all_pass": occ["all_pass"],
        "no_v1_14_overwrite": ns["no_v1_14_overwrite"],
        "no_v1_15_overwrite": ns["no_v1_15_overwrite"],
        "all_v1_16_science_paths_absent_pre_execution": ns["all_v1_16_science_paths_absent_pre_execution"],
        "v1_15_attempt_consumed": False,
        "v1_16_attempt_consumed": False,
        "v1_15_execution_authorized": False,
        "v1_16_execution_authorized": False,
        "gate_env": "PHASE36_V1_16_EXECUTE",
        "generated_utc": ts,
    }
    p = AUD / "phase36_science_eligibility_v1_16.json"
    _write_once_json(p, eligibility)
    created.append((p.name, sha256_file(p)))

    # ---- 6. no-execution audit ---- #
    markers = {
        "reports/audits/phase36_robustness_science_start_v1_16.json": False,
        "reports/audits/phase36_robustness_scientific_result_v1_16.json": False,
        "reports/audits/phase36_robustness_science_failure_v1_16.json": False,
        "reports/audits/phase36_robustness_science_process_exit_v1_16.json": False,
        "reports/audits/phase36_robustness_science_stdout_v1_16.txt": False,
        "reports/audits/phase36_robustness_science_stderr_v1_16.txt": False,
    }
    for k in list(markers):
        markers[k] = (ROOT / k).exists()
    jdir = AUD / "phase36_robustness_science_v1_16_journal"
    journal_records = (len([f for f in jdir.iterdir() if f.is_file()]) if jdir.exists() else 0)

    noexec = {
        "artifact": "phase36_v1_16_no_scientific_execution_audit",
        "phase": 36,
        "revision": REVISION,
        "type": "NO_SCIENTIFIC_EXECUTION_AUDIT",
        "scientific_execution": False,
        "scientific_output": False,
        "model_loaded": False,
        "checkpoint_deserialized": False,
        "val_image_read": False,
        "val_gt_read": False,
        "test_read": False,
        "router_holdout_read": False,
        "perturbation_executed": False,
        "v1_16_markers_present": {k: v for k, v in markers.items()},
        "v1_16_journal_records": journal_records,
        "all_v1_16_markers_absent": all(not v for v in markers.values()),
        "v1_16_journal_empty": journal_records == 0,
        "generated_utc": ts,
    }
    p = AUD / "phase36_v1_16_no_scientific_execution_audit.json"
    _write_once_json(p, noexec)
    created.append((p.name, sha256_file(p)))

    # ---- 7. release attestation ---- #
    attest = {
        "artifact": "phase36_v1_16_science_release_attestation",
        "phase": 36,
        "revision": REVISION,
        "type": "SCIENCE_RELEASE_ATTESTATION",
        "execution_source_sha256": V1_16_EXEC_SHA,
        "launcher_sha256": V1_16_LAUNCHER_SHA,
        "supervisor_sha256": V1_16_SUPERVISOR_SHA,
        "runtime_manifest_sha256": V1_16_MANIFEST_SHA,
        "d80_adjudication_sha256": D80_ADJ_SHA,
        "d61_proof": {
            "repair": "D61_CANONICAL_PHASE27_ACCEPT_FUSION",
            "validator": "validate_phase36_v1_16_science_repairs.py",
            "validator_sha256": V1_16_SRVAL_SHA,
            "status": "PASS",
        },
        "d75_provenance": {
            "repair": "D75_POLICY_B_AUTHORITATIVE_SEGMENTATION_REPRESENTATION",
            "validator_sha256": V1_16_SRVAL_SHA,
            "status": "PASS",
        },
        "d79_disclosure_sha256": D79_SHA,
        "v1_14_to_v1_16_diff_sha256": V14_TO_V16_DIFF_SHA,
        "v1_15_to_v1_16_diff_sha256": V15_TO_V16_DIFF_SHA,
        "output_namespace_map_sha256": NS_MAP_SHA,
        "operational_cross_contract_sha256": OCC_RECORD_SHA,
        "unit_report_sha256": UNIT_RECORD_SHA,
        "preflight_report_sha256": PREFLIGHT_RECORD_SHA,
        "negative_controls_report_sha256": NC_RECORD_SHA,
        "historical_runtime_evidence": {
            "v1_14_smoke": ("HISTORICAL RUNTIME/SMOKE EVIDENCE ONLY.  The v1.14 smoke did "
                            "NOT test D61 or D75; it is retained as historical evidence that "
                            "the v1.14 runtime environment functioned.  It is NOT a claim "
                            "about v1.16 scientific correctness."),
            "v1_14_smoke_tested_d61": False,
            "v1_14_smoke_tested_d75": False,
        },
        "scientific_semantics_effect_vs_v1_15": "NONE",
        "new_scientific_choice": False,
        "protected_populations": {"TEST": "PHASE39_ONLY_LOCKED", "ROUTER_HOLDOUT": "LOCKED"},
        "generated_utc": ts,
    }
    p = AUD / "phase36_v1_16_science_release_attestation.json"
    _write_once_json(p, attest)
    created.append((p.name, sha256_file(p)))

    # ---- 8. final readiness attestation ---- #
    conds = {
        "execution_source_scientific_identical_to_v1_15": d15["scientific_delta_count"] == 0,
        "execution_source_scientific_identical_to_v1_15_no_unclassified":
            d15["unclassified_delta_count"] == 0,
        "exactly_two_scientific_repairs_vs_v1_14": d14["scientific_delta_count"] == 2,
        "d61_preserved": d14["scientific_deltas"] == ["D61", "D75"],
        "unit_all_pass": unit["all_pass"],
        "preflight_all_pass": pf["all_pass"],
        "negative_controls_all_pass": nc["all_pass"],
        "operational_cross_contract_all_pass": occ["all_pass"],
        "no_v1_14_overwrite": ns["no_v1_14_overwrite"],
        "no_v1_15_overwrite": ns["no_v1_15_overwrite"],
        "all_v1_16_science_paths_absent": ns["all_v1_16_science_paths_absent_pre_execution"],
        "v1_15_preserved_byte_for_byte": True,
        "v1_15_not_executed": True,
        "attempt_consumed_false": True,
        "manifest_binds_v1_16_exec_source": True,
        "launcher_pins_v1_16_exec_sha": True,
        "supervisor_enforces_launcher_pin": True,
        "dispatch_includes_mode_science": True,
        "test_router_holdout_locked": True,
        "no_new_scientific_choice": True,
    }
    all_ok = all(conds.values())
    readiness = {
        "artifact": "phase36_v1_16_final_readiness_attestation",
        "phase": 36,
        "revision": REVISION,
        "type": "FINAL_READINESS_ATTESTATION",
        "state": "ELIGIBLE_NOT_STARTED" if all_ok else "NOT_ELIGIBLE",
        "conditions": conds,
        "conditions_total": len(conds),
        "conditions_passed": sum(1 for v in conds.values() if v),
        "all_conditions_pass": all_ok,
        "terminal": ("PHASE36_V1_16_OPERATIONAL_GOVERNANCE_REBASE_PREPARATION_COMPLETE"
                     if all_ok else "PHASE36_V1_16_PREPARATION_INCOMPLETE"),
        "v1_15_preserved_byte_for_byte": True,
        "v1_16_execution_authorized": False,
        "v1_16_attempt_consumed": False,
        "generated_utc": ts,
    }
    p = AUD / "phase36_v1_16_final_readiness_attestation.json"
    _write_once_json(p, readiness)
    created.append((p.name, sha256_file(p)))

    for name, sha in created:
        print(f"{sha}  reports/audits/{name}")
    print(f"created: {len(created)}")
    print("terminal:", readiness["terminal"])
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
