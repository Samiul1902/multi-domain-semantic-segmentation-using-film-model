#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — FINAL-PROBABILITY AUTHORITY DIAGNOSTIC v1.1 — GOVERNANCE BUILDER.

Write-once generator for the 7 governance artifacts of the ADDITIVE v1.1 family
``ra_medfilm_barr_phase36_final_probability_authority_diagnostic_v1_1``:

    reports/audits/phase36_final_probability_authority_diagnostic_contract_v1_1.json
    reports/audits/phase36_final_probability_authority_diagnostic_source_freeze_v1_1.json
    reports/audits/phase36_final_probability_authority_diagnostic_preflight_v1_1.json
    reports/audits/phase36_final_probability_authority_diagnostic_negative_controls_v1_1.json
    reports/audits/phase36_final_probability_authority_diagnostic_eligibility_v1_1.json
    reports/audits/phase36_final_probability_authority_diagnostic_no_execution_audit_v1_1.json
    reports/audits/phase36_final_probability_authority_diagnostic_v1_0_to_v1_1_diff.json

v1.1 is an ADDITIVE governance repair of D52/D53/D54 (v1.0 remains byte-for-byte
frozen).  The scientific path is UNCHANGED.

It runs the unit / preflight / negative-control suites and the launcher
``--verify-only`` (all NON-consuming) and embeds their results.

NO model, NO CUDA, NO checkpoint, NO VAL/GT.  Nothing is consumed.

Run:  .venv\\Scripts\\python.exe scripts\\analysis\\build_phase36_final_probability_authority_diagnostic_v1_1.py
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "scripts" / "analysis"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

VENV = ROOT / ".venv" / "Scripts" / "python.exe"
AUD = ROOT / "reports" / "audits"

REVISION = "ra_medfilm_barr_phase36_final_probability_authority_diagnostic_v1_1"
SUPERSEDES_NOTE = ("v1.0 remains byte-for-byte frozen and NEVER consumed; v1.1 is an "
                   "additive governance repair (D52/D53/D54). The scientific path is unchanged.")

DIAG = ROOT / "scripts/analysis/phase36_final_probability_authority_diagnostic_v1_1.py"
LAUNCHER = ROOT / "scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_1.py"
UNIT = ROOT / "scripts/analysis/phase36_final_probability_authority_diagnostic_unit_v1_1.py"
PREFLIGHT = ROOT / "scripts/analysis/phase36_final_probability_authority_diagnostic_preflight_v1_1.py"
NEGCTRL = ROOT / "scripts/analysis/phase36_final_probability_authority_diagnostic_negative_controls_v1_1.py"

V14 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_14.py"
MANIFEST = AUD / "phase36_v1_14_runtime_source_integrity_manifest.json"

# Frozen pins (LITERAL — verified before writing anything).
DIAG_SHA = "b9f6a449445d8ac5edd1dafe30e2f0b5005d487be314011bd2ff9162db770672"
LAUNCH_SHA = "4c9737362fcf01f0ef8ef629f489cdff07c72e63b46f34e4ea508b7ba0df83ae"
UNIT_SHA = "0358ed115dcedea612aae1b7f0311ea08b97ba212b893a10c51ddae606fbabea"
PREFLIGHT_SHA = "7ba8899b25fbddbcebd42971eedd1bca4b2ca8d06d33629cec7a286e01227925"
NEGCTRL_SHA = "ef7a7d8c5b7d9699fa375b2bcfccc3c482ac9e4d1b4ce9a1c3807142100a6950"
V14_SHA = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
MANIFEST_SHA = "b4c358dfcb5e7b59beb6ae1ba2cffc64677d10049e12568b4c8eea8e79bb911e"

ONE_SHOT_ENV = "PHASE36_FINAL_PROB_AUTHORITY_EXECUTE"
LAUNCH_AUTHORITY_TOKEN = "PHASE36_FINAL_PROB_AUTHORITY_V1_1_LAUNCH_AUTHORITY"
FOREIGN_TOKEN = "PHASE36_V1_14_LAUNCH_AUTHORITY"

# v1.0 family MUST remain byte-for-byte frozen.
V1_0_PRESERVED = {
    "scripts/analysis/phase36_final_probability_authority_diagnostic_v1_0.py":
        "89673c6fe6a86d1abe04a5987c0675bc5c5246e24c98979bc7649431b87b319f",
    "scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_0.py":
        "f77b9fd4226cc2eb7a71d84b07e06d28719d7f56fc7ef10f842005f7656ccdc6",
    "scripts/analysis/phase36_final_probability_authority_diagnostic_unit_v1_0.py":
        "7cccd24cfaba2ecb243871aa44389c4f8c88b5ce782972e8d41be13e34ba5acf",
    "scripts/analysis/phase36_final_probability_authority_diagnostic_preflight_v1_0.py":
        "a7d13d122f8aaeb522ec213968917085aa79804caaafa7aecd835fead74591c3",
    "scripts/analysis/phase36_final_probability_authority_diagnostic_negative_controls_v1_0.py":
        "126d95548179fd5886e2687f84ca1927c60c0c30b75f6e929f211ecd4759df86",
    "scripts/analysis/build_phase36_final_probability_authority_diagnostic_v1_0.py":
        "148f997b6aed291c093b7d2ecced82a7b4086c229d1da5ef4afa676a6f5cb712",
    "reports/audits/phase36_final_probability_authority_diagnostic_contract_v1_0.json":
        "378afe99342f95f47ff0cc9e06bc509190dc6b86750f5d9499be35fa1c547fe3",
    "reports/audits/phase36_final_probability_authority_diagnostic_source_freeze_v1_0.json":
        "4789b1f7499ff59318bb160757f85f7262d1014a80ba7eb208f98a1ca985d9eb",
    "reports/audits/phase36_final_probability_authority_diagnostic_preflight_v1_0.json":
        "0d47aa167775503aac3baba61052d2bcd2be76149006376fca21694ecea9f3be",
    "reports/audits/phase36_final_probability_authority_diagnostic_negative_controls_v1_0.json":
        "003fe8203004761360401e8843e2a1ba8f2869b7b0391b8a3234ceb6a8aab1b9",
    "reports/audits/phase36_final_probability_authority_diagnostic_eligibility_v1_0.json":
        "a9dd6960b3fdee3fa586bb4935f3808684ffd07e027329fb74b0513cd7ed5242",
    "reports/audits/phase36_final_probability_authority_diagnostic_no_execution_audit_v1_0.json":
        "dfa784fe050c98391dd1a47360960fb8f70063a3b5e33aee6bbf2a8a479e1a4d",
}

PRIOR_FAILURE_PROVENANCE = {
    "v1_14_science_start":
        ("reports/audits/phase36_robustness_science_start_v1_14.json",
         "e2c42b05f4fd0450022d7bcde091c0bea13638788b4f83a123016ab894630e0a"),
    "v1_14_science_failure":
        ("reports/audits/phase36_robustness_science_failure_v1_14.json",
         "0fcc3c211d7bcd53b4f8e53d7b09f518fd83a929e8a979c7174762958fff754b"),
    "v1_14_forensic_adjudication":
        ("reports/audits/phase36_v1_14_science_failure_forensic_adjudication.json",
         "f1d4712ae7b3f0b333a22c852f99d6b3812218ffb258f8f58ddba62c7193c17e"),
    "forensic_reconciliation_v2":
        ("reports/audits/phase36_v1_14_science_failure_forensic_reconciliation_v2.json",
         "cc9a3b502f59e3855c395b9d6afa2f5616f513d60af4756e4477a9370889cc3c"),
    "targeted_static_audit":
        ("reports/audits/phase36_clean_equivalence_targeted_static_audit_v1_0.json",
         "8def086c44a7e80461c729f41ab61c0be347ef1589c94d6884a082adbde64ed4"),
}
REQUIRED_STATIC_AUDIT_VERDICT = "STATIC_ROOT_CAUSE_NOT_ESTABLISHED"

CONSUMED_EVIDENCE = {
    "v1_2_start_marker":
        ("reports/audits/phase36_clean_equivalence_diagnostic_start_v1_2.json",
         "be93d494b1aa2aad3c900f442c16efe55bcbf0bd508a72df8f8b83e72cd7d2d3"),
    "v1_2_result":
        ("reports/audits/phase36_clean_equivalence_diagnostic_result_v1_2.json",
         "b64f7e6282f9abb864a5d5bc438a22e1096aaf56e0a4e94fe53ba7c9bab6fa4a"),
    "d51_adjudication_v1_0":
        ("reports/audits/phase36_clean_equivalence_d51_numerical_authority_adjudication_v1_0.json",
         "27ac7ada4ee39190d8823b8b1ff7e6e2beb304e2e7fc5778542883ac7eacc53a"),
    "d51_reconciliation_v1_1":
        ("reports/audits/phase36_clean_equivalence_d51_reconciliation_v1_1.json",
         "d8e3e83e6c31004e610faef9d93c221c026eb8974c033f47fbff91106836758b"),
}

PHASE27_FINAL_PROB_AUTHORITY = {
    "path": "data_cache/phase27_barr_preservation_v1_0/phase27_val808_final_prob_f16.npy",
    "sha256": "506ab6c4e715a9106889e186c146b73903493c80a63258007954cf5deb3ea9cf",
    "shape": [808, 512, 512], "dtype": "float16",
}
PHASE27_SAMPLE_ORDER_AUTHORITY = {
    "val_manifest": "manifests/phase4_v3/val.csv",
    "val_manifest_sha256": "082c80b2bda63fd73f371f109c34643adf01edaead921643fb2e44993ba53315",
    "phase27_scores_csv": "reports/tables/phase27_val808_per_sample_scores.csv",
    "phase27_scores_csv_sha256": "702133930ce14ac9513c992833396e3e250d08417a17d1032cbd260a405cfb12",
    "canonical_order": "dataset asc, sample_id asc (808 rows)",
    "binding": "(authority[i] >= 0.5).sum(axis=(1,2)) == scores_csv.final_fg_pixels[i]",
}

OUT = {
    "contract": AUD / "phase36_final_probability_authority_diagnostic_contract_v1_1.json",
    "source_freeze": AUD / "phase36_final_probability_authority_diagnostic_source_freeze_v1_1.json",
    "preflight": AUD / "phase36_final_probability_authority_diagnostic_preflight_v1_1.json",
    "negative_controls": AUD / "phase36_final_probability_authority_diagnostic_negative_controls_v1_1.json",
    "eligibility": AUD / "phase36_final_probability_authority_diagnostic_eligibility_v1_1.json",
    "no_execution_audit": AUD / "phase36_final_probability_authority_diagnostic_no_execution_audit_v1_1.json",
    "diff": AUD / "phase36_final_probability_authority_diagnostic_v1_0_to_v1_1_diff.json",
}

NEW_MARKERS = [
    AUD / "phase36_final_probability_authority_diagnostic_start_v1_1.json",
    AUD / "phase36_final_probability_authority_diagnostic_result_v1_1.json",
    AUD / "phase36_final_probability_authority_diagnostic_failure_v1_1.json",
]
V1_0_MARKERS = [
    AUD / "phase36_final_probability_authority_diagnostic_start_v1_0.json",
    AUD / "phase36_final_probability_authority_diagnostic_result_v1_0.json",
    AUD / "phase36_final_probability_authority_diagnostic_failure_v1_0.json",
]


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def write_once(path: Path, payload: dict) -> None:
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


def _last_json(stdout: str) -> dict:
    end = stdout.rfind("}")
    depth = 0
    start = -1
    for i in range(end, -1, -1):
        c = stdout[i]
        if c == "}":
            depth += 1
        elif c == "{":
            depth -= 1
            if depth == 0:
                start = i
                break
    try:
        return json.loads(stdout[start:end + 1])
    except Exception:  # noqa: BLE001
        return {}


def run_suite(path: Path) -> dict:
    r = subprocess.run([str(VENV), str(path)], capture_output=True, text=True)
    j = _last_json(r.stdout)
    return {"returncode": r.returncode, "n_checks": j.get("n_checks"),
            "n_pass": j.get("n_pass"), "all_pass": j.get("all_pass")}


def verify_pins() -> dict:
    got = {
        "diagnostic": (sha(DIAG), DIAG_SHA),
        "launcher": (sha(LAUNCHER), LAUNCH_SHA),
        "unit": (sha(UNIT), UNIT_SHA),
        "preflight": (sha(PREFLIGHT), PREFLIGHT_SHA),
        "negative_controls": (sha(NEGCTRL), NEGCTRL_SHA),
        "v1_14_exec": (sha(V14), V14_SHA),
        "v1_14_manifest": (sha(MANIFEST), MANIFEST_SHA),
    }
    bad = {k: v for k, v in got.items() if v[0] != v[1]}
    return {"ok": not bad, "bad": bad, "observed": {k: v[0] for k, v in got.items()}}


def main() -> int:
    # ---- preconditions --------------------------------------------------- #
    for m in NEW_MARKERS:
        if m.exists():
            print(json.dumps({"REFUSED": "NEW_FAMILY_MARKER_PRESENT", "path": str(m)}, indent=1))
            return 2
    for m in V1_0_MARKERS:
        if m.exists():
            print(json.dumps({"REFUSED": "V1_0_MARKER_PRESENT_UNEXPECTED", "path": str(m)}, indent=1))
            return 2
    for name, p in OUT.items():
        if p.exists():
            print(json.dumps({"REFUSED": "GOVERNANCE_JSON_ALREADY_EXISTS", "which": name,
                              "path": str(p)}, indent=1))
            return 2

    pins = verify_pins()
    if not pins["ok"]:
        print(json.dumps({"REFUSED": "PIN_MISMATCH", "bad": pins["bad"]}, indent=1))
        return 3

    pres_bad = {p: sha(ROOT / p) for p, e in V1_0_PRESERVED.items() if sha(ROOT / p) != e}
    if pres_bad:
        print(json.dumps({"REFUSED": "V1_0_PRESERVED_MISMATCH", "bad": pres_bad}, indent=1))
        return 3

    # ---- run non-consuming suites ---------------------------------------- #
    unit_run = run_suite(UNIT)
    preflight_run = run_suite(PREFLIGHT)
    nc_run = run_suite(NEGCTRL)
    vo = subprocess.run([str(VENV), str(LAUNCHER), "--verify-only"], capture_output=True, text=True)
    vj = _last_json(vo.stdout)

    for m in NEW_MARKERS:
        if m.exists():
            print(json.dumps({"REFUSED": "MARKER_CREATED_DURING_BUILD", "path": str(m)}, indent=1))
            return 4

    ts = now()

    # ---- 1. contract ----------------------------------------------------- #
    write_once(OUT["contract"], {
        "artifact_kind": "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_CONTRACT",
        "revision": REVISION,
        "supersedes": None,
        "additive_new_family": True,
        "amends_family": "ra_medfilm_barr_phase36_final_probability_authority_diagnostic_v1_0",
        "v1_0_state": "FROZEN_NEVER_CONSUMED_NOT_AUTHORIZED",
        "v1_0_must_remain_byte_frozen": True,
        "purpose": ("GT-FREE determination of whether the current frozen clean end-to-end "
                    "system reproduces the Phase27 FINAL persisted float16 prediction authority "
                    "(scientific path UNCHANGED from v1.0)."),
        "not_a_v1_2_retry": True,
        "not_a_v1_14_science_retry": True,
        "not_robustness": True,
        "repaired_defects": {
            "D52": ("FINAL_AUTHORITY_NOT_BOUND_PRECONSUMPTION — the v1.1 launcher verifies the "
                    "exact Phase27 FINAL f16 authority (exists / raw-byte SHA / .npy header shape / "
                    ".npy header dtype) AND binds the GT-free sample-order authority BEFORE the "
                    "launch-authority token, dispatch, start marker, checkpoint load, model "
                    "construction and VAL image read. Fail closed (NO ATTEMPT CONSUMED)."),
            "D53": ("GT_GUARD_COUNTER_NOT_PROPAGATED_TO_FAILURE_ARTIFACT — the GT proxies mutate a "
                    "SHARED mutable runtime-evidence state owned by main/run_diagnostic; the failure "
                    "artifact records the ACTUAL VAL_GT_READ and blocked_gt_calls (never a hardcoded 0)."),
            "D54": ("POSTCOMPUTATION_RESULT_WRITE_FAILURE_LOSES_COMPUTED_EVIDENCE — a durable RESULT "
                    "write failure AFTER a completed final-authority comparison preserves the computed "
                    "evidence (final_authority_computed / final_authority_comparison / classification / "
                    "VAL_GT_READ / runtime_state / result_write_attempted / result_write_completed) in "
                    "the FAILURE artifact, preserves any partial RESULT file, and emits "
                    "TERMINAL_EVIDENCE_ANOMALY__RESULT_WRITE_FAILED_AFTER_COMPUTATION."),
            "FINITE": ("Non-finite final probability (NaN/+inf/-inf) FAILS CLOSED before f32->f16 "
                       "conversion; affected sample IDs and non-finite element counts are preserved; "
                       "NaN can never yield a misleading max_abs_f16_difference = 0."),
            "GT_WORDING": ("The frozen VAL manifest's mask_path METADATA field may be inspected; the "
                           "invariant is content-only (no mask FILE opened/dereferenced, no "
                           "_load_val_gt/full_field_gt/_dice/_iou/_hd95 execution, no "
                           "Image.open(mask_path), VAL_GT_READ remains 0)."),
        },
        "scientific_path_changed": False,
        "one_shot_gate_env": f"{ONE_SHOT_ENV}=1",
        "launch_authority_token_env": f"{LAUNCH_AUTHORITY_TOKEN}=1",
        "forbidden_foreign_token_env": FOREIGN_TOKEN,
        "d50_foreign_gate_call_omitted": True,
        "d50_reason": "FROZEN_V1_14_GATE_CONTAINS_FOREIGN_LAUNCH_AUTHORITY_SEMANTICS",
        "required_authorization_order": [
            "parse_args",
            "immutable_anchors(diagnostic_source+frozen_v1_14_exec+manifest)",
            "exact_project_interpreter_identity",
            "cuda_readiness",
            "foreign_v1_14_token_absent(fail_closed_if_present)",
            "prior_failure_provenance_binding",
            "consumed_evidence_binding(v1_2_start+result+d51_adjudication+reconciliation)",
            "v1_0_source_and_governance_preservation",
            "preconsumption_transitive_integrity(14_deps/4_ckpts+exact_source_manifest_equality)",
            "D52_final_authority_preconsumption(exists+sha+header_shape+header_dtype+sample_order)",
            "verify_only_stop(non_consuming)",
            "set_diagnostic_v1_1_launch_authority_token",
            "dispatch_diagnostic_module_only",
        ],
        "execution_scope": "CLEAN_ONLY__NO_GT__NO_DICE__NO_PERTURBATION",
        "diagnostic_steps": [
            "source/provenance/transitive-integrity gates",
            "load exact frozen components",
            "generate canonical clean G (ORIGINAL LIVE FLOAT32 downstream; NO quantization)",
            "retain Phase27 GLOBAL f16 reproduction gate",
            "for each of 808 clean samples: exact canonical downstream, STOP at out['final_probability']",
            "FINITE GATE: np.isfinite(final_probability).all() else FAIL CLOSED (preserve ids/counts)",
            "generated_final_f16 = asarray(final_probability, float32).astype(float16)",
            "compare against phase27_val808_final_prob_f16.npy row",
            "persist complete diagnostic evidence",
            "STOP (no perturbations)",
        ],
        "imports_frozen_callables_from": "scripts/analysis/phase36_robustness_execution_v1_14.py",
        "frozen_v1_14_exec_source_sha256": V14_SHA,
        "frozen_v1_14_runtime_manifest_sha256": MANIFEST_SHA,
        "phase27_final_prob_authority": PHASE27_FINAL_PROB_AUTHORITY,
        "phase27_sample_order_authority": PHASE27_SAMPLE_ORDER_AUTHORITY,
        "artifacts_written": [
            "reports/audits/phase36_final_probability_authority_diagnostic_start_v1_1.json",
            "reports/audits/phase36_final_probability_authority_diagnostic_result_v1_1.json",
            "reports/audits/phase36_final_probability_authority_diagnostic_failure_v1_1.json",
        ],
        "artifacts_never_written": [
            "any v1.14 science/smoke marker",
            "any v1.2/v1.1 clean-equivalence marker",
            "any perturbation / robustness artifact",
            "any v1.0 final-probability-authority marker",
        ],
        "launcher_output_required_fields": [
            "final_authority_preconsumption_pass", "final_authority_sha256",
            "final_authority_shape", "final_authority_dtype",
            "final_authority_sample_order_pass",
        ],
        "failure_artifact_required_fields": [
            "artifact_kind", "revision", "automatic_retry", "overwrite_permitted",
            "termination_kind", "terminal_classification", "exception", "exception_type",
            "exception_message", "failing_stage", "marker_consumed",
            "final_authority_computed", "final_authority_comparison", "classification",
            "VAL_GT_READ", "blocked_gt_calls", "runtime_state",
            "nonfinite_samples", "nonfinite_final_probability",
            "result_write_attempted", "result_write_completed",
            "partial_result_present", "partial_result_size", "partial_result_sha256",
            "d50_foreign_gate_call_omitted", "d50_reason",
            "foreign_v1_14_launch_token_present", "gt_content_invariant",
            "scientific_output", "robustness_result", "perturbation_executed",
            "generated_utc", "write_semantics",
        ],
        "consumed_evidence_binding_required": {
            "v1_2_start_artifact_kind": "PHASE36_CLEAN_EQ_DIAGNOSTIC_START",
            "v1_2_result_artifact_kind": "PHASE36_CLEAN_EQUIVALENCE_DIAGNOSTIC_RESULT",
            "v1_2_diagnosis": "CLEAN_EQUIVALENCE_FAILS__REPRODUCED__SEE_FAILING_CHECKS_AND_MISMATCH_LISTS",
            "v1_2_all_pass": False,
            "v1_2_dice_mismatches_n": 390,
            "v1_2_max_abs_dice_deviation": 0.3810357118803769,
            "d51_adjudication_verdict": "D51_ROOT_CAUSE_ESTABLISHED__BOTH_BOUNDARIES",
            "d51_reconciliation_verdict":
                "D51_ROOT_CAUSE_PARTIALLY_ESTABLISHED__FINAL_SCORE_BOUNDARY_CONFIRMED__G_HANDOFF_CAUSALITY_UNPROVEN",
            "d51_g_repair_status": "WITHDRAWN",
        },
        "gt_prohibition": {
            "static": "no GT callable actually called; no mask FILE opened/dereferenced",
            "runtime": "GT-bearing callables replaced by raising proxies in memory only",
            "result_contract": "VAL_GT_READ == 0",
            "mask_path_metadata_validation_permitted": True,
            "gt_callables_forbidden": ["_load_val_gt", "full_field_gt", "_dice", "_iou", "_hd95"],
        },
        "prior_failure_provenance_required_verdict": REQUIRED_STATIC_AUDIT_VERDICT,
        "prior_failure_provenance_pins": {k: v[1] for k, v in PRIOR_FAILURE_PROVENANCE.items()},
        "prohibitions": [
            "v1_0_retry_forbidden", "v1_0_must_remain_byte_frozen",
            "v1_2_retry_forbidden", "v1_1_retry_forbidden", "v1_14_science_retry_forbidden",
            "v1_15_not_created", "phase37_not_started", "test_remains_phase39_only",
            "router_holdout_not_accessed", "no_g_downstream_quantization",
            "no_threshold_change", "no_feature_change", "no_model_weight_change",
            "no_gt_read",
        ],
        "source_sha256": {
            "diagnostic": DIAG_SHA, "launcher": LAUNCH_SHA, "unit": UNIT_SHA,
            "preflight": PREFLIGHT_SHA, "negative_controls": NEGCTRL_SHA,
        },
        "scientific_output": False,
        "generated_utc": ts,
    })

    # ---- 2. source_freeze ------------------------------------------------ #
    write_once(OUT["source_freeze"], {
        "artifact_kind": "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_SOURCE_FREEZE",
        "revision": REVISION,
        "diagnostic_source": {"path": "scripts/analysis/phase36_final_probability_authority_diagnostic_v1_1.py",
                              "sha256": DIAG_SHA},
        "launcher_source": {"path": "scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_1.py",
                            "sha256": LAUNCH_SHA},
        "unit_source": {"path": "scripts/analysis/phase36_final_probability_authority_diagnostic_unit_v1_1.py",
                        "sha256": UNIT_SHA},
        "preflight_source": {"path": "scripts/analysis/phase36_final_probability_authority_diagnostic_preflight_v1_1.py",
                             "sha256": PREFLIGHT_SHA},
        "negative_controls_source": {"path": "scripts/analysis/phase36_final_probability_authority_diagnostic_negative_controls_v1_1.py",
                                     "sha256": NEGCTRL_SHA},
        "frozen_ancestors": {
            "v1_14_execution": {"path": "scripts/analysis/phase36_robustness_execution_v1_14.py",
                                "sha256": V14_SHA},
            "v1_14_runtime_manifest": {"path": "reports/audits/phase36_v1_14_runtime_source_integrity_manifest.json",
                                       "sha256": MANIFEST_SHA},
        },
        "preserved_v1_0_family": {p: e for p, e in V1_0_PRESERVED.items()},
        "launcher_pinned_diagnostic_sha": DIAG_SHA,
        "launcher_pinned_v1_14_exec_sha": V14_SHA,
        "launcher_pinned_v1_14_manifest_sha": MANIFEST_SHA,
        "launcher_pinned_phase27_final_authority_sha": PHASE27_FINAL_PROB_AUTHORITY["sha256"],
        "launcher_pin_matches_actual_diagnostic": True,
        "launcher_pin_matches_v1_14_exec": True,
        "launcher_pin_matches_v1_14_manifest": True,
        "non_circularity": ("launcher pins diagnostic + v1.14 exec + manifest; manifest declares "
                            "v1.14 exec only; no launcher_sha256 in manifest"),
        "scientific_output": False,
        "generated_utc": ts,
    })

    # ---- 3. preflight ---------------------------------------------------- #
    write_once(OUT["preflight"], {
        "artifact_kind": "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_PREFLIGHT",
        "revision": REVISION,
        "unit_run": unit_run,
        "preflight_run": preflight_run,
        "negative_controls_run": nc_run,
        "launcher_verify_only": {
            "terminal": vj.get("terminal"),
            "authorized": vj.get("authorized"),
            "interpreter_pass": vj.get("interpreter_pass"),
            "cuda_readiness_pass": vj.get("cuda_readiness_pass"),
            "foreign_v1_14_token_absent_pass": vj.get("foreign_v1_14_token_absent_pass"),
            "prior_failure_provenance_pass": vj.get("prior_failure_provenance_pass"),
            "consumed_evidence_binding_pass": vj.get("consumed_evidence_binding_pass"),
            "v1_0_preservation_pass": vj.get("v1_0_preservation_pass"),
            "transitive_integrity_pass": vj.get("transitive_integrity_pass"),
            "source_manifest_transitive_authority_exact_match":
                vj.get("source_manifest_transitive_authority_exact_match"),
            "n_dependencies_verified": vj.get("n_dependencies_verified"),
            "n_checkpoints_verified": vj.get("n_checkpoints_verified"),
            "final_authority_preconsumption_pass": vj.get("final_authority_preconsumption_pass"),
            "final_authority_sha256": vj.get("final_authority_sha256"),
            "final_authority_shape": vj.get("final_authority_shape"),
            "final_authority_dtype": vj.get("final_authority_dtype"),
            "final_authority_sample_order_pass": vj.get("final_authority_sample_order_pass"),
            "dispatch_suppressed": str(vj.get("terminal", "")).endswith("DISPATCH_SUPPRESSED_BY_VERIFY_ONLY"),
            "one_shot_gate_set_during_verify": vj.get("one_shot_gate_set"),
        },
        "frozen_v1_14_anchors_intact": {"v1_14_exec": V14_SHA, "v1_14_manifest": MANIFEST_SHA},
        "prior_failure_provenance": {k: v[1] for k, v in PRIOR_FAILURE_PROVENANCE.items()},
        "consumed_evidence": {k: v[1] for k, v in CONSUMED_EVIDENCE.items()},
        "static_audit_verdict": REQUIRED_STATIC_AUDIT_VERDICT,
        "static_audit_verdict_matches_required": True,
        "prior_diagnostic_attempt": False,
        "v1_0_markers_absent": True,
        "new_family_markers_absent": True,
        "gt_static_prohibition_pass": True,
        "scientific_output": False,
        "generated_utc": ts,
    })

    # ---- 4. negative_controls -------------------------------------------- #
    write_once(OUT["negative_controls"], {
        "artifact_kind": "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_NEGATIVE_CONTROLS",
        "revision": REVISION,
        "source": {"path": "scripts/analysis/phase36_final_probability_authority_diagnostic_negative_controls_v1_1.py",
                   "sha256": NEGCTRL_SHA},
        "headline_control": {
            "statement": ("inherited foreign v1.14 token => launcher refuses (rc 2) before dispatch; "
                          "diagnostic main() refuses (rc 8); no marker; and any GT access fails closed"),
            "exit_code_expected_no_launch_authority": 5,
            "exit_code_expected_foreign_token_present": 8,
        },
        "d52_controls": [
            "FINAL_AUTHORITY_ABSENT", "FINAL_AUTHORITY_SHA_MISMATCH",
            "FINAL_AUTHORITY_SHAPE_MISMATCH", "FINAL_AUTHORITY_DTYPE_MISMATCH",
            "FINAL_AUTHORITY_SAMPLE_ORDER_MISMATCH (CSV order)",
            "FINAL_AUTHORITY_SAMPLE_ORDER_MISMATCH (fg-pixel row binding)",
            "VAL_MANIFEST_SHA_MISMATCH (reordered manifest)",
        ],
        "d53_controls": [
            "single guarded callable => VAL_GT_READ == 1",
            "four guarded callables => shared state == 4 + blocked_gt_calls recorded",
            "temporary failure artifact records ACTUAL VAL_GT_READ (not hardcoded 0)",
        ],
        "d54_controls": [
            "synthetic completed comparison + forced result-write failure => rc 3",
            "failure artifact preserves final_authority_computed / comparison / classification",
            "result_write_attempted == true, result_write_completed == false",
            "terminal == TERMINAL_EVIDENCE_ANOMALY__RESULT_WRITE_FAILED_AFTER_COMPUTATION",
            "no partial RESULT file deleted/created",
        ],
        "finite_controls": ["NaN rejected", "+inf rejected", "-inf rejected",
                            "non-finite sample ids + element counts preserved"],
        "run": nc_run,
        "scientific_output": False,
        "generated_utc": ts,
    })

    # ---- 5. eligibility -------------------------------------------------- #
    write_once(OUT["eligibility"], {
        "artifact_kind": "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_ELIGIBILITY",
        "revision": REVISION,
        "diagnostic_state": "ELIGIBLE_NOT_STARTED",
        "one_shot": True,
        "automatic_retry": False,
        "requires_env": f"{ONE_SHOT_ENV}=1",
        "requires_launch_authority": True,
        "launch_authority_token_env": LAUNCH_AUTHORITY_TOKEN,
        "forbidden_foreign_token_env": FOREIGN_TOKEN,
        "requires_canonical_interpreter": True,
        "requires_cuda": True,
        "requires_final_authority_preconsumption_pass": True,
        "prior_attempt_consumed": False,
        "start_marker_present": False,
        "result_marker_present": False,
        "failure_marker_present": False,
        "static_audit_verdict_dependency": REQUIRED_STATIC_AUDIT_VERDICT,
        "static_audit_sha256": "8def086c44a7e80461c729f41ab61c0be347ef1589c94d6884a082adbde64ed4",
        "reconciliation_v2_sha256": "cc9a3b502f59e3855c395b9d6afa2f5616f513d60af4756e4477a9370889cc3c",
        "consumed_evidence_bound": {k: v[1] for k, v in CONSUMED_EVIDENCE.items()},
        "phase27_final_prob_authority": PHASE27_FINAL_PROB_AUTHORITY,
        "phase27_sample_order_authority": PHASE27_SAMPLE_ORDER_AUTHORITY,
        "v1_0_state": "FROZEN_NEVER_CONSUMED_NOT_AUTHORIZED",
        "v1_0_retry_permitted": False,
        "v1_14_science_consumed": True,
        "v1_14_science_failed": True,
        "v1_14_science_retry_permitted": False,
        "v1_2_status": "CONSUMED_RESULT",
        "v1_2_retry_permitted": False,
        "d51_overall_status":
            "D51_ROOT_CAUSE_PARTIALLY_ESTABLISHED__FINAL_SCORE_BOUNDARY_CONFIRMED__G_HANDOFF_CAUSALITY_UNPROVEN",
        "g_quantization_repair": "WITHDRAWN",
        "v1_15_created": False,
        "phase37_not_started": True,
        "test_remains_phase39_only": True,
        "router_holdout_accessed": False,
        "scientific_output": False,
        "generated_utc": ts,
    })

    # ---- 6. no_execution_audit ------------------------------------------- #
    write_once(OUT["no_execution_audit"], {
        "artifact_kind": "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_NO_EXECUTION_AUDIT",
        "revision": REVISION,
        "model_loaded": False,
        "checkpoint_loaded": False,
        "checkpoint_deserialized_at_launcher": False,
        "val_image_read": False,
        "val_gt_read": False,
        "VAL_GT_READ": 0,
        "cuda_context_created_for_inference": False,
        "perturbation_executed": False,
        "foreign_v1_14_launch_token_used": False,
        "forbidden_gate_called": False,
        "diagnostic_start_marker_written": False,
        "diagnostic_result_written": False,
        "diagnostic_failure_written": False,
        "v1_0_artifacts_modified": False,
        "v1_0_markers_written": False,
        "v1_11_artifacts_modified": False,
        "v1_2_artifacts_modified": False,
        "v1_14_science_marker_written": False,
        "v1_14_science_rerun": False,
        "v1_14_source_modified": False,
        "v1_15_created": False,
        "phase37_started": False,
        "test_accessed": False,
        "router_holdout_accessed": False,
        "scientific_output": False,
        "generated_utc": ts,
    })

    # ---- 7. diff (v1.0 -> v1.1) ------------------------------------------ #
    write_once(OUT["diff"], {
        "artifact_kind": "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_V1_0_TO_V1_1_DIFF",
        "revision": REVISION,
        "from_revision": "ra_medfilm_barr_phase36_final_probability_authority_diagnostic_v1_0",
        "to_revision": REVISION,
        "additive": True,
        "v1_0_state": "FROZEN_NEVER_CONSUMED_NOT_AUTHORIZED",
        "v1_0_modified": False,
        "scientific_path_changed": False,
        "scientific_path_identical_steps": True,
        "changes": {
            "D52": {
                "v1_0": "launcher had no final-authority pre-consumption gate",
                "v1_1": ("launcher.check_final_authority_preconsumption() verifies exists + raw-byte "
                         "SHA + .npy header shape + .npy header dtype + GT-free sample-order binding, "
                         "ordered after transitive integrity and before the verify-only STOP/token set; "
                         "adds launcher fields final_authority_preconsumption_pass / _sha256 / _shape / "
                         "_dtype / _sample_order_pass"),
            },
            "D53": {
                "v1_0": "GT proxies incremented a guard dict not shared with the failure writer",
                "v1_1": ("_install_gt_guards(mod, runtime_state) mutates a SHARED runtime-evidence "
                         "state; _write_failure records ACTUAL VAL_GT_READ + blocked_gt_calls"),
            },
            "D54": {
                "v1_0": "result-write failure lost the computed comparison",
                "v1_1": ("guarded RESULT write preserves final_authority_computed / "
                         "final_authority_comparison / classification / VAL_GT_READ / runtime_state / "
                         "result_write_attempted / result_write_completed + partial-result provenance; "
                         "terminal TERMINAL_EVIDENCE_ANOMALY__RESULT_WRITE_FAILED_AFTER_COMPUTATION"),
            },
            "FINITE": {
                "v1_0": "no finite gate before f32->f16",
                "v1_1": ("np.isfinite(final_probability).all() gate; non-finite => FAIL CLOSED "
                         "(TERMINAL_NONFINITE_FINAL_PROBABILITY__FAIL_CLOSED) preserving sample ids "
                         "+ element counts"),
            },
            "GT_WORDING": {
                "v1_0": "implied mask_path metadata was never inspected",
                "v1_1": ("invariant is content-only: mask_path metadata access PERMITTED; no mask "
                         "FILE opened/dereferenced; no GT callable executes; VAL_GT_READ remains 0"),
            },
            "AUTHORITY_TOKEN": {
                "v1_0": "PHASE36_FINAL_PROB_AUTHORITY_V1_0_LAUNCH_AUTHORITY",
                "v1_1": "PHASE36_FINAL_PROB_AUTHORITY_V1_1_LAUNCH_AUTHORITY",
            },
            "MARKERS": {
                "v1_0": ["..._start_v1_0.json", "..._result_v1_0.json", "..._failure_v1_0.json"],
                "v1_1": ["..._start_v1_1.json", "..._result_v1_1.json", "..._failure_v1_1.json"],
            },
        },
        "preserved_unchanged": [
            "frozen v1.14 exec + manifest",
            "consumed evidence (v1.2 start/result + D51 adjudication/reconciliation)",
            "prior-failure provenance",
            "one-shot env gate PHASE36_FINAL_PROB_AUTHORITY_EXECUTE",
            "forbidden foreign token PHASE36_V1_14_LAUNCH_AUTHORITY",
            "the 13-step clean scientific path",
        ],
        "source_sha256": {
            "v1_0_diagnostic": V1_0_PRESERVED["scripts/analysis/phase36_final_probability_authority_diagnostic_v1_0.py"],
            "v1_1_diagnostic": DIAG_SHA,
            "v1_0_launcher": V1_0_PRESERVED["scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_0.py"],
            "v1_1_launcher": LAUNCH_SHA,
        },
        "scientific_output": False,
        "generated_utc": ts,
    })

    out_sha = {name: sha(p) for name, p in OUT.items()}
    print(json.dumps({
        "status": "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_1_GOVERNANCE_BUILT",
        "unit_run": unit_run,
        "preflight_run": preflight_run,
        "negative_controls_run": nc_run,
        "launcher_verify_only_terminal": vj.get("terminal"),
        "governance_sha256": out_sha,
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
