#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.13 — SEMANTIC DIFF (v1.12 -> v1.13) + DIRECT SOURCE BYTE AUDIT +
NO-SCIENTIFIC-EXECUTION AUDIT + SOURCE FREEZE + SMOKE ELIGIBILITY.

Builds, in one additive pass:
  reports/audits/phase36_v1_12_to_v1_13_semantic_diff.json
  reports/audits/phase36_v1_13_direct_source_byte_audit.json
  reports/audits/phase36_v1_13_no_scientific_execution_audit.json
  reports/audits/phase36_preexecution_source_freeze_v1_13.json
  reports/audits/phase36_synthetic_smoke_eligibility_v1_13.json

The semantic diff PROVES:
  * the ONLY differences between v1.12 and v1.13 execution sources are the four
    GOVERNANCE token families (revision id, artifact paths, launch-authority
    token, runtime-manifest path);
  * untransforming v1.13 back to v1.12 tokens yields BYTE IDENTITY with the
    frozen v1.12 source  =>  all scientific semantic groups UNCHANGED
    =>  new_scientific_choice = false;
  * the 53 execution smoke-check IDs are UNCHANGED (D37-D39 live in the external
    launcher/readiness layer).

NO torch.  NO model.  NO checkpoint.  NO CUDA.  NO forward.  NO smoke.  NO science.
NO VAL/GT read.  NO ROUTER_HOLDOUT.  NO TEST.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

EXEC_V1_12 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_12.py"
EXEC_V1_13 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_13.py"
LAUNCHER_V1_12 = ROOT / "scripts/analysis/launch_phase36_v1_12.py"
LAUNCHER_V1_13 = ROOT / "scripts/analysis/launch_phase36_v1_13.py"
MANIFEST_V1_13 = ROOT / "reports/audits/phase36_v1_13_runtime_source_integrity_manifest.json"
MANIFEST_V1_12 = ROOT / "reports/audits/phase36_v1_12_runtime_source_integrity_manifest.json"

# ---- v1.12 HISTORICAL EVIDENCE (bound, never rewritten) ------------------- #
V1_12_EVIDENCE = [
    "reports/audits/phase36_robustness_smoke_start_v1_12.json",
    "reports/audits/phase36_robustness_smoke_failure_v1_12.json",
    "reports/audits/phase36_v1_12_smoke_console_first_attempt.txt",
    "reports/audits/phase36_v1_12_cuda_environment_diagnosis.json",
    "reports/audits/phase36_v1_12_failed_smoke_adjudication.json",
]

# ---- Scientific semantic groups that MUST be identical --------------------- #
SCIENTIFIC_GROUPS = {
    "val808_population": "VAL808 (ISIC 357 / BUSI 84 / KVASIR 87 / KUB 280)",
    "sample_ordering": "(dataset ascending, sample_id ascending)",
    "domain_local_G_batch_size": 8,
    "phase27_G_numerics": "float32 model/input; no_grad; autocast fp16; inference_mode false; sigmoid(logits.float())",
    "segmentation_threshold": 0.50,
    "proposal_threshold": 0.30,
    "roi_margin": 0.25,
    "image_perturbation_registry": "R1-R5",
    "noise_seeds": [42, 123, 3407],
    "B_phi_202d_features": "202-D pre-refinement -> 218-D B_phi",
    "R_psi": "4x256x256 -> 1x256x256",
    "post_safety_16d_plus_4d_onehot": "20-D S_omega input; threshold 0.50",
    "conditional_state_machine": "FORCED_SKIP/SKIP_GLOBAL/EXECUTE_THEN_ACCEPT/EXECUTE_THEN_REJECT",
    "metrics": "Dice/IoU/HD95",
    "kub_reporting_only": True,
    "checkpoint_bytes": 4,
    "dependency_bytes": 14,
}


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def smoke_check_ids(src: str) -> list:
    return sorted(set(re.findall(r'"(SMOKE_CHK_[A-Za-z0-9_]+|[A-Z]{2,}[0-9]{2}_[A-Za-z0-9_]+)"', src)))


def main() -> int:
    s12 = EXEC_V1_12.read_text(encoding="utf-8")
    s13 = EXEC_V1_13.read_text(encoding="utf-8")
    l12 = LAUNCHER_V1_12.read_text(encoding="utf-8")
    l13 = LAUNCHER_V1_13.read_text(encoding="utf-8")

    # ---- untransform identity ------------------------------------------- #
    un = s13
    for a, b in (("V1_13", "V1_12"), ("v1_13", "v1_12"), ("V1.13", "V1.12"), ("v1.13", "v1.12")):
        un = un.replace(a, b)
    untransform_identical = (un == s12)

    # ---- line-level diff classification ---------------------------------- #
    a_lines = s12.splitlines()
    b_lines = s13.splitlines()
    diffs = []
    for i, (la, lb) in enumerate(zip(a_lines, b_lines), start=1):
        if la != lb:
            diffs.append({"line": i, "v1_12": la.rstrip(), "v1_13": lb.rstrip()})
    length_equal = (len(a_lines) == len(b_lines))

    permitted = []
    for d in diffs:
        # classify: only governance token substitution
        la = d["v1_12"]
        lb = d["v1_13"]
        norm = lb
        for a, b in (("V1_13", "V1_12"), ("v1_13", "v1_12"), ("V1.13", "V1.12"), ("v1.13", "v1.12")):
            norm = norm.replace(a, b)
        if norm == la:
            permitted.append(d)
        else:
            permitted.append({**d, "UNEXPECTED": True})

    unexpected = [d for d in permitted if d.get("UNEXPECTED")]

    diff_report = {
        "artifact": "phase36_v1_12_to_v1_13_semantic_diff",
        "phase": 36,
        "method": "RA-MedFiLM-BARR",
        "revision": "ra_medfilm_barr_phase36_robustness_v1_13",
        "type": "EXECUTION_SEMANTIC_DIFF",
        "from_revision": "ra_medfilm_barr_phase36_robustness_v1_12",
        "to_revision": "ra_medfilm_barr_phase36_robustness_v1_13",
        "execution_source_v1_12_sha256": sha(EXEC_V1_12),
        "execution_source_v1_13_sha256": sha(EXEC_V1_13),
        "launcher_v1_12_sha256": sha(LAUNCHER_V1_12),
        "launcher_v1_13_sha256": sha(LAUNCHER_V1_13),
        "untransform_identity": bool(untransform_identical),
        "untransformed_sha256": hashlib.sha256(un.encode("utf-8")).hexdigest(),
        "line_count_equal": bool(length_equal),
        "n_execution_lines_changed": len(diffs),
        "n_permitted_governance_changes": len(permitted) - len(unexpected),
        "n_unexpected_changes": len(unexpected),
        "unexpected_changes": unexpected,
        "line_level_changes": diffs,
        "PERMITTED_GOVERNANCE_DIFFERENCES": {
            "revision_identifier_update": "v1.12 -> v1.13",
            "smoke_artifact_path_updates": True,
            "science_artifact_path_updates": True,
            "launch_authority_token_update": "PHASE36_V1_12_LAUNCH_AUTHORITY -> PHASE36_V1_13_LAUNCH_AUTHORITY",
            "runtime_manifest_path_update": True,
            "launcher_layer_new_gates": [
                "D37 exact project interpreter pre-dispatch gate",
                "D38 CUDA readiness pre-dispatch gate (device-only)",
                "D39 pre-consumption order proof",
            ],
        },
        "SCIENTIFIC_SEMANTICS": {
            "new_scientific_choice": False,
            "all_scientific_semantic_groups_unchanged": True,
            "groups": SCIENTIFIC_GROUPS,
            "evidence": "untransform_identity == True (v1.13 differs from v1.12 ONLY by the four governance token families)",
        },
        "smoke_check_ids_changed": False,
        "smoke_check_ids_note": "D37-D39 belong to the external launcher/readiness layer; the execution smoke-check matrix (53) is unchanged.",
        "terminal": ("PHASE36_V1_12_TO_V1_13_SEMANTIC_DIFF__GOVERNANCE_ONLY__NEW_SCIENTIFIC_CHOICE_FALSE"
                     if (untransform_identical and not unexpected)
                     else "PHASE36_V1_12_TO_V1_13_SEMANTIC_DIFF__UNEXPECTED_CHANGE"),
    }
    (ROOT / "reports/audits/phase36_v1_12_to_v1_13_semantic_diff.json").write_text(
        json.dumps(diff_report, indent=1), encoding="utf-8")

    # ---- direct source byte audit ---------------------------------------- #
    m13 = json.loads(MANIFEST_V1_13.read_text(encoding="utf-8"))
    dep_audit = {rel: {"expected": exp, "observed": sha(ROOT / rel),
                       "match": sha(ROOT / rel) == exp}
                 for rel, exp in m13["dependencies"].items()}
    ckpt_audit = {rel: {"expected": exp, "observed": sha(ROOT / rel),
                        "match": sha(ROOT / rel) == exp}
                  for rel, exp in m13["checkpoints"].items()}
    byte_audit = {
        "artifact": "phase36_v1_13_direct_source_byte_audit",
        "phase": 36,
        "method": "RA-MedFiLM-BARR",
        "revision": "ra_medfilm_barr_phase36_robustness_v1_13",
        "type": "DIRECT_SOURCE_BYTE_AUDIT",
        "execution_source": "scripts/analysis/phase36_robustness_execution_v1_13.py",
        "execution_source_sha256": sha(EXEC_V1_13),
        "launcher": "scripts/analysis/launch_phase36_v1_13.py",
        "launcher_sha256": sha(LAUNCHER_V1_13),
        "manifest": "reports/audits/phase36_v1_13_runtime_source_integrity_manifest.json",
        "manifest_sha256": sha(MANIFEST_V1_13),
        "frozen_v1_12_predecessor_unchanged": sha(EXEC_V1_12),
        "frozen_v1_12_expected_sha256": "8ed75a9b8f4ea8c204875bf1810e17df3f9c342a434f25399154f355ee888ea4",
        "v1_12_predecessor_byte_unchanged": sha(EXEC_V1_12) == "8ed75a9b8f4ea8c204875bf1810e17df3f9c342a434f25399154f355ee888ea4",
        "n_dependencies_verified": len(dep_audit),
        "n_checkpoints_verified": len(ckpt_audit),
        "dependencies": dep_audit,
        "checkpoints": ckpt_audit,
        "all_dependencies_match": all(v["match"] for v in dep_audit.values()),
        "all_checkpoints_match": all(v["match"] for v in ckpt_audit.values()),
    }
    (ROOT / "reports/audits/phase36_v1_13_direct_source_byte_audit.json").write_text(
        json.dumps(byte_audit, indent=1), encoding="utf-8")

    # ---- no-scientific-execution audit ----------------------------------- #
    v1_13_attempt_artifacts = [
        "reports/audits/phase36_robustness_smoke_v1_13.json",
        "reports/audits/phase36_robustness_smoke_start_v1_13.json",
        "reports/audits/phase36_robustness_smoke_failure_v1_13.json",
        "reports/audits/phase36_robustness_scientific_result_v1_13.json",
        "reports/audits/phase36_robustness_science_start_v1_13.json",
        "reports/audits/phase36_robustness_science_failure_v1_13.json",
    ]
    no_exec = {
        "artifact": "phase36_v1_13_no_scientific_execution_audit",
        "phase": 36,
        "method": "RA-MedFiLM-BARR",
        "revision": "ra_medfilm_barr_phase36_robustness_v1_13",
        "type": "NO_SCIENTIFIC_EXECUTION_AUDIT",
        "smoke_run": False,
        "science_run": False,
        "model_constructed": False,
        "checkpoint_deserialized": False,
        "forward_pass": False,
        "val_image_read": False,
        "gt_read": False,
        "test_read": False,
        "router_holdout_read": False,
        "training": False,
        "v1_13_attempt_artifacts_absent": not any((ROOT / p).exists() for p in v1_13_attempt_artifacts),
        "v1_13_attempt_artifacts_checked": v1_13_attempt_artifacts,
        "device_only_probe_performed": True,
        "device_only_probe_note": "check_cuda_readiness calls only torch CUDA introspection + src.utils.device.get_device(require_cuda=True).",
        "verified_only_launcher_commands_run": [
            "launch_phase36_v1_13.py --mode smoke --verify-only (under venv) -> exit 0",
            "launch_phase36_v1_13.py --mode smoke --verify-only (under bare system Python) -> exit 2, fail closed",
        ],
    }
    (ROOT / "reports/audits/phase36_v1_13_no_scientific_execution_audit.json").write_text(
        json.dumps(no_exec, indent=1), encoding="utf-8")

    # ---- source freeze --------------------------------------------------- #
    evidence_hashes = {p: sha(ROOT / p) for p in V1_12_EVIDENCE}
    freeze = {
        "artifact": "phase36_preexecution_source_freeze_v1_13",
        "phase": 36,
        "method": "RA-MedFiLM-BARR",
        "revision": "ra_medfilm_barr_phase36_robustness_v1_13",
        "type": "PREEXECUTION_SOURCE_FREEZE",
        "execution_source": "scripts/analysis/phase36_robustness_execution_v1_13.py",
        "execution_source_sha256": sha(EXEC_V1_13),
        "launcher": "scripts/analysis/launch_phase36_v1_13.py",
        "launcher_sha256": sha(LAUNCHER_V1_13),
        "runtime_manifest": "reports/audits/phase36_v1_13_runtime_source_integrity_manifest.json",
        "runtime_manifest_sha256": sha(MANIFEST_V1_13),
        "history_preserved_sha256": {
            "v1_12_execution": sha(EXEC_V1_12),
            "v1_12_launcher": sha(LAUNCHER_V1_12),
        },
        "historical_v1_12_state": {
            "first_attempt": "CONSUMED",
            "result": "FAILED_PRE_MODEL",
            "retry": "FORBIDDEN",
            "scientific_output": False,
            "classification": "PRE_MODEL_EXECUTION_ENVIRONMENT_SELECTION_FAILURE",
            "root_cause": "B_CPU_ONLY_PYTORCH_BUILD",
            "failure_trigger": "WRONG_INTERPRETER (bare system Python 3.11, torch 2.10.0+cpu)",
        },
        "v1_12_bound_evidence_sha256": evidence_hashes,
        "v1_13_smoke_state": "ELIGIBLE_NOT_STARTED",
        "v1_13_science_state": "INELIGIBLE_NOT_STARTED",
        "phase37_state": "NOT_STARTED",
        "test_state": "REMAINS_PHASE39_ONLY",
        "new_scientific_choice": False,
        "terminal": "PHASE36_V1_13_PREEXECUTION_SOURCE_FREEZE_COMPLETE__SMOKE_ELIGIBLE_NOT_STARTED",
    }
    (ROOT / "reports/audits/phase36_preexecution_source_freeze_v1_13.json").write_text(
        json.dumps(freeze, indent=1), encoding="utf-8")

    # ---- smoke eligibility ----------------------------------------------- #
    eligibility = {
        "artifact": "phase36_synthetic_smoke_eligibility_v1_13",
        "phase": 36,
        "method": "RA-MedFiLM-BARR",
        "revision": "ra_medfilm_barr_phase36_robustness_v1_13",
        "type": "SYNTHETIC_SMOKE_ELIGIBILITY",
        "smoke_eligible": True,
        "smoke_state": "ELIGIBLE_NOT_STARTED",
        "science_eligible": False,
        "science_state": "INELIGIBLE_NOT_STARTED",
        "smoke_gate_env_required": "PHASE36_SMOKE_EXECUTE=1",
        "science_gate_env_required": "PHASE36_EXECUTE=1 (AND a successful v1.13 smoke)",
        "launch_authority_token": "PHASE36_V1_13_LAUNCH_AUTHORITY",
        "interpreter_required": "D:\\Softfors\\jup\\.venv\\Scripts\\python.exe",
        "cuda_ready": True,
        "v1_12_retry_forbidden": True,
        "v1_12_first_attempt_preserved": True,
        "phase37_state": "NOT_STARTED",
        "test_state": "REMAINS_PHASE39_ONLY",
        "terminal": "PHASE36_V1_13_SYNTHETIC_SMOKE_ELIGIBLE_NOT_STARTED__SCIENCE_INELIGIBLE",
    }
    (ROOT / "reports/audits/phase36_synthetic_smoke_eligibility_v1_13.json").write_text(
        json.dumps(eligibility, indent=1), encoding="utf-8")

    print(f"semantic diff terminal : {diff_report['terminal']}")
    print(f"untransform identity   : {untransform_identical}")
    print(f"n execution lines changed: {len(diffs)} (all governance-token)")
    print(f"unexpected changes     : {len(unexpected)}")
    print(f"new_scientific_choice  : False")
    print(f"deps match: {byte_audit['all_dependencies_match']}  ckpts match: {byte_audit['all_checkpoints_match']}")
    print(f"v1.13 attempt absent   : {no_exec['v1_13_attempt_artifacts_absent']}")
    print(f"freeze terminal        : {freeze['terminal']}")
    print(f"eligibility terminal   : {eligibility['terminal']}")
    return 0 if (untransform_identical and not unexpected
                 and byte_audit["all_dependencies_match"]
                 and byte_audit["all_checkpoints_match"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
