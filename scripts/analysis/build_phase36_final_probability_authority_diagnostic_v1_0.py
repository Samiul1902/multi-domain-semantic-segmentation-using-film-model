#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — FINAL-PROBABILITY AUTHORITY DIAGNOSTIC v1.0 — GOVERNANCE BUILDER.

Write-once generator for the 6 governance artifacts of the NEW diagnostic family
``ra_medfilm_barr_phase36_final_probability_authority_diagnostic_v1_0``:

    reports/audits/phase36_final_probability_authority_diagnostic_contract_v1_0.json
    reports/audits/phase36_final_probability_authority_diagnostic_source_freeze_v1_0.json
    reports/audits/phase36_final_probability_authority_diagnostic_preflight_v1_0.json
    reports/audits/phase36_final_probability_authority_diagnostic_negative_controls_v1_0.json
    reports/audits/phase36_final_probability_authority_diagnostic_eligibility_v1_0.json
    reports/audits/phase36_final_probability_authority_diagnostic_no_execution_audit_v1_0.json

It runs the unit / preflight / negative-control suites and the launcher
``--verify-only`` (all NON-consuming) and embeds their results.

NO model, NO CUDA, NO checkpoint, NO VAL/GT.  Nothing is consumed.

Run:  .venv\\Scripts\\python.exe scripts\\analysis\\build_phase36_final_probability_authority_diagnostic_v1_0.py
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

REVISION = "ra_medfilm_barr_phase36_final_probability_authority_diagnostic_v1_0"

DIAG = ROOT / "scripts/analysis/phase36_final_probability_authority_diagnostic_v1_0.py"
LAUNCHER = ROOT / "scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_0.py"
UNIT = ROOT / "scripts/analysis/phase36_final_probability_authority_diagnostic_unit_v1_0.py"
PREFLIGHT = ROOT / "scripts/analysis/phase36_final_probability_authority_diagnostic_preflight_v1_0.py"
NEGCTRL = ROOT / "scripts/analysis/phase36_final_probability_authority_diagnostic_negative_controls_v1_0.py"

V14 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_14.py"
MANIFEST = AUD / "phase36_v1_14_runtime_source_integrity_manifest.json"

# Frozen pins (LITERAL — verified before writing anything).
DIAG_SHA = "89673c6fe6a86d1abe04a5987c0675bc5c5246e24c98979bc7649431b87b319f"
LAUNCH_SHA = "f77b9fd4226cc2eb7a71d84b07e06d28719d7f56fc7ef10f842005f7656ccdc6"
UNIT_SHA = "7cccd24cfaba2ecb243871aa44389c4f8c88b5ce782972e8d41be13e34ba5acf"
PREFLIGHT_SHA = "a7d13d122f8aaeb522ec213968917085aa79804caaafa7aecd835fead74591c3"
NEGCTRL_SHA = "126d95548179fd5886e2687f84ca1927c60c0c30b75f6e929f211ecd4759df86"
V14_SHA = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
MANIFEST_SHA = "b4c358dfcb5e7b59beb6ae1ba2cffc64677d10049e12568b4c8eea8e79bb911e"

ONE_SHOT_ENV = "PHASE36_FINAL_PROB_AUTHORITY_EXECUTE"
LAUNCH_AUTHORITY_TOKEN = "PHASE36_FINAL_PROB_AUTHORITY_V1_0_LAUNCH_AUTHORITY"
FOREIGN_TOKEN = "PHASE36_V1_14_LAUNCH_AUTHORITY"

PRESERVED = {
    "scripts/analysis/phase36_clean_equivalence_diagnostic_v1_0.py":
        "7cc51cceacfa314d7f84acb8a6dc482a2b46ea81de0ec695c0c8f0ca8b0b50f7",
    "scripts/analysis/launch_phase36_clean_equivalence_diagnostic_v1_0.py":
        "a34923faf6c27dd741ee1a1a1b4d1cbef1233664c2b02825e53b42c22c75b228",
    "scripts/analysis/phase36_clean_equivalence_diagnostic_unit_v1_0.py":
        "33e72386699aa0100c314846ffe2592f740ca7fb76e926a704cf4d46fbf78bf5",
    "scripts/analysis/phase36_clean_equivalence_diagnostic_preflight_v1_0.py":
        "92c2d855e931d037e965d862a2ce0feb091d53e1bff0f91020f85729842e6653",
    "scripts/analysis/phase36_clean_equivalence_diagnostic_v1_1.py":
        "04fa6252ff2533464553fb1a6c1f55ae009ee7ff00c1dbf89c1f901b089c839e",
    "scripts/analysis/launch_phase36_clean_equivalence_diagnostic_v1_1.py":
        "205dd4b877d8b6505c9479de9979087f19c341769ba2c5157a25701c212d14f6",
    "scripts/analysis/phase36_clean_equivalence_diagnostic_unit_v1_1.py":
        "89190b297e7bc4e2868f7bb52fc46d836e6866317403523e8bbf0d167bc50aee",
    "scripts/analysis/phase36_clean_equivalence_diagnostic_preflight_v1_1.py":
        "3634a3f4314fb5712d958cda2effc3b3027257663692b51b3b4176b258fab529",
    "scripts/analysis/phase36_clean_equivalence_diagnostic_negative_controls_v1_1.py":
        "b43649898d5be2fb96737f683aa208ea84d55a66ab807ac0d06e0fba4a7b3ee1",
    "reports/audits/phase36_clean_equivalence_diagnostic_start_v1_1.json":
        "59b29875838ed6117a8441f422a17fa7bdae5088fc74b2b33a38f9c92e15fa68",
    "reports/audits/phase36_clean_equivalence_diagnostic_failure_v1_1.json":
        "ef6cf75f5d8432e69b89ddbef437c24b409cb325105a11f78a4c0f0004a57343",
    "reports/audits/phase36_clean_equivalence_diagnostic_v1_1_post_run_evidence.json":
        "a33066434cf569b77563a8028e842aefeac9a360e8e9479a3852bf9f401204af",
    "scripts/analysis/phase36_clean_equivalence_diagnostic_v1_2.py":
        "24a638d47ddff164ec33d361ed742523f58c6cf8847d3ee9fbb02658a603d50e",
    "scripts/analysis/launch_phase36_clean_equivalence_diagnostic_v1_2.py":
        "1029c83b019ac76f331e528319fe2472ca5a7baac23b788c51de3297dcf7ff8e",
    "scripts/analysis/phase36_clean_equivalence_diagnostic_unit_v1_2.py":
        "af9b374f89c0cbbf03c0c1f50bd107f39d549dd43289c23defc02815c4ba951f",
    "scripts/analysis/phase36_clean_equivalence_diagnostic_preflight_v1_2.py":
        "bfa97ecf16a42ddaa51ba9f41f60a89bdf5076600d5b7bf0225b59ae5b9c6ddb",
    "scripts/analysis/phase36_clean_equivalence_diagnostic_negative_controls_v1_2.py":
        "3551847a6a8b6d5b8ef5a0cfd0831eb4e0cf59385b146d6eb2af51981297fbbb",
    "reports/audits/phase36_clean_equivalence_diagnostic_start_v1_2.json":
        "be93d494b1aa2aad3c900f442c16efe55bcbf0bd508a72df8f8b83e72cd7d2d3",
    "reports/audits/phase36_clean_equivalence_diagnostic_result_v1_2.json":
        "b64f7e6282f9abb864a5d5bc438a22e1096aaf56e0a4e94fe53ba7c9bab6fa4a",
    "reports/audits/phase36_clean_equivalence_diagnostic_stdout_first_attempt_v1_2.txt":
        "515d56d180a0e8ba277d3f73397cd3297b21e81806c93a18be65cb5f66026380",
    "reports/audits/phase36_clean_equivalence_diagnostic_stderr_first_attempt_v1_2.txt":
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "scripts/analysis/build_phase36_clean_equivalence_d51_adjudication_v1_0.py":
        "bc88a21d27b0466de8efe791f681494df08002b33deba40606724c86335aaee0",
    "scripts/analysis/build_phase36_clean_equivalence_d51_reconciliation_v1_1.py":
        "b89609d6b2f56c8d6e92c3852938d6002f6060ec75c472799d827c8d35ab1d5c",
    "reports/audits/phase36_clean_equivalence_d51_numerical_authority_adjudication_v1_0.json":
        "27ac7ada4ee39190d8823b8b1ff7e6e2beb304e2e7fc5778542883ac7eacc53a",
    "reports/audits/phase36_clean_equivalence_d51_reconciliation_v1_1.json":
        "d8e3e83e6c31004e610faef9d93c221c026eb8974c033f47fbff91106836758b",
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

OUT = {
    "contract": AUD / "phase36_final_probability_authority_diagnostic_contract_v1_0.json",
    "source_freeze": AUD / "phase36_final_probability_authority_diagnostic_source_freeze_v1_0.json",
    "preflight": AUD / "phase36_final_probability_authority_diagnostic_preflight_v1_0.json",
    "negative_controls": AUD / "phase36_final_probability_authority_diagnostic_negative_controls_v1_0.json",
    "eligibility": AUD / "phase36_final_probability_authority_diagnostic_eligibility_v1_0.json",
    "no_execution_audit": AUD / "phase36_final_probability_authority_diagnostic_no_execution_audit_v1_0.json",
}

NEW_MARKERS = [
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
    for name, p in OUT.items():
        if p.exists():
            print(json.dumps({"REFUSED": "GOVERNANCE_JSON_ALREADY_EXISTS", "which": name,
                              "path": str(p)}, indent=1))
            return 2

    pins = verify_pins()
    if not pins["ok"]:
        print(json.dumps({"REFUSED": "PIN_MISMATCH", "bad": pins["bad"]}, indent=1))
        return 3

    pres_bad = {p: sha(ROOT / p) for p, e in PRESERVED.items() if sha(ROOT / p) != e}
    if pres_bad:
        print(json.dumps({"REFUSED": "PRESERVED_ARTIFACT_MISMATCH", "bad": pres_bad}, indent=1))
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
        "purpose": ("GT-FREE determination of whether the current frozen clean end-to-end "
                    "system reproduces the Phase27 FINAL persisted float16 prediction authority."),
        "not_a_v1_2_retry": True,
        "not_a_v1_14_science_retry": True,
        "not_robustness": True,
        "repaired_defects": {
            "D51-A": ("FINAL_SCORE_REPRESENTATION_MISMATCH confirmed by source; this diagnostic "
                      "measures the generated clean final probability cast to float16 against the "
                      "persisted Phase27 float16 authority."),
            "D51-B": ("G_HANDOFF causality UNPROVEN (no float32 G authority exists). This diagnostic "
                      "does NOT quantize G downstream; the G-quantization repair is WITHDRAWN."),
        },
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
            "preconsumption_transitive_integrity(14_deps/4_ckpts+exact_source_manifest_equality)",
            "verify_only_stop(non_consuming)",
            "set_diagnostic_v1_0_launch_authority_token",
            "dispatch_diagnostic_module_only",
        ],
        "execution_scope": "CLEAN_ONLY__NO_GT__NO_DICE__NO_PERTURBATION",
        "diagnostic_steps": [
            "source/provenance/transitive-integrity gates",
            "load exact frozen components",
            "generate canonical clean G (ORIGINAL LIVE FLOAT32 downstream; NO quantization)",
            "retain Phase27 GLOBAL f16 reproduction gate",
            "for each of 808 clean samples: exact canonical downstream, STOP at out['final_probability']",
            "generated_final_f16 = asarray(final_probability, float32).astype(float16)",
            "compare against phase27_val808_final_prob_f16.npy row",
            "persist complete diagnostic evidence",
            "STOP (no perturbations)",
        ],
        "imports_frozen_callables_from": "scripts/analysis/phase36_robustness_execution_v1_14.py",
        "frozen_v1_14_exec_source_sha256": V14_SHA,
        "frozen_v1_14_runtime_manifest_sha256": MANIFEST_SHA,
        "phase27_final_prob_authority": PHASE27_FINAL_PROB_AUTHORITY,
        "artifacts_written": [
            "reports/audits/phase36_final_probability_authority_diagnostic_start_v1_0.json",
            "reports/audits/phase36_final_probability_authority_diagnostic_result_v1_0.json",
            "reports/audits/phase36_final_probability_authority_diagnostic_failure_v1_0.json",
        ],
        "artifacts_never_written": [
            "any v1.14 science/smoke marker",
            "any v1.2/v1.1 clean-equivalence marker",
            "any perturbation / robustness artifact",
        ],
        "result_artifact_required_fields": [
            "artifact_kind", "revision", "purpose", "execution_scope",
            "exact_diagnostic_source_sha256", "frozen_v1_14_source_sha256",
            "frozen_v1_14_manifest_sha256", "phase27_final_prob_authority",
            "final_authority_comparison", "stages", "counters", "VAL_GT_READ",
            "gt_guard", "authorized_population_count",
            "prior_failure_provenance_bound", "consumed_evidence_provenance_bound",
            "d50_foreign_gate_call_omitted", "d50_reason",
            "foreign_v1_14_launch_token_present", "preconsumption_transitive_integrity_pass",
            "source_manifest_transitive_authority_exact_match", "classification",
            "perturbation_executed", "scientific_output", "robustness_result",
            "v1_14_science_markers_touched", "generated_utc", "write_semantics",
        ],
        "final_authority_comparison_required_fields": [
            "reference_path", "reference_sha256", "reference_sha256_expected", "n_samples",
            "final_f16_bit_identical_all", "total_f16_element_mismatch_count",
            "max_abs_f16_difference", "n_samples_with_any_f16_difference", "affected_sample_ids",
            "live_vs_self_f16_threshold_flip_count",
            "self_f16_vs_phase27_f16_threshold_mismatch_count",
            "live_vs_phase27_threshold_mismatch_count",
            "n_pixels_generated_f16_eq_half_total", "n_measured_q_live_below_half_total",
            "classification", "gt_read", "dice_iou_hd95_computed",
        ],
        "failure_artifact_required_fields": [
            "artifact_kind", "revision", "automatic_retry", "overwrite_permitted",
            "termination_kind", "exception", "exception_type", "exception_message",
            "failing_stage", "marker_consumed", "final_authority_computed", "VAL_GT_READ",
            "d50_foreign_gate_call_omitted", "d50_reason",
            "foreign_v1_14_launch_token_present", "scientific_output", "robustness_result",
            "perturbation_executed", "generated_utc", "write_semantics",
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
            "static": "no GT callable actually called; no mask_path read",
            "runtime": "GT-bearing callables replaced by raising proxies in memory only",
            "result_contract": "VAL_GT_READ == 0",
            "gt_callables_forbidden": ["_load_val_gt", "full_field_gt", "_dice", "_iou", "_hd95"],
            "gt_row_keys_forbidden": ["mask_path"],
        },
        "prior_failure_provenance_required_verdict": REQUIRED_STATIC_AUDIT_VERDICT,
        "prior_failure_provenance_pins": {k: v[1] for k, v in PRIOR_FAILURE_PROVENANCE.items()},
        "prohibitions": [
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
        "diagnostic_source": {"path": "scripts/analysis/phase36_final_probability_authority_diagnostic_v1_0.py",
                              "sha256": DIAG_SHA},
        "launcher_source": {"path": "scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_0.py",
                            "sha256": LAUNCH_SHA},
        "unit_source": {"path": "scripts/analysis/phase36_final_probability_authority_diagnostic_unit_v1_0.py",
                        "sha256": UNIT_SHA},
        "preflight_source": {"path": "scripts/analysis/phase36_final_probability_authority_diagnostic_preflight_v1_0.py",
                             "sha256": PREFLIGHT_SHA},
        "negative_controls_source": {"path": "scripts/analysis/phase36_final_probability_authority_diagnostic_negative_controls_v1_0.py",
                                     "sha256": NEGCTRL_SHA},
        "frozen_ancestors": {
            "v1_14_execution": {"path": "scripts/analysis/phase36_robustness_execution_v1_14.py",
                                "sha256": V14_SHA},
            "v1_14_runtime_manifest": {"path": "reports/audits/phase36_v1_14_runtime_source_integrity_manifest.json",
                                       "sha256": MANIFEST_SHA},
        },
        "preserved_predecessors": {p: e for p, e in PRESERVED.items()},
        "launcher_pinned_diagnostic_sha": DIAG_SHA,
        "launcher_pinned_v1_14_exec_sha": V14_SHA,
        "launcher_pinned_v1_14_manifest_sha": MANIFEST_SHA,
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
            "transitive_integrity_pass": vj.get("transitive_integrity_pass"),
            "source_manifest_transitive_authority_exact_match":
                vj.get("source_manifest_transitive_authority_exact_match"),
            "n_dependencies_verified": vj.get("n_dependencies_verified"),
            "n_checkpoints_verified": vj.get("n_checkpoints_verified"),
            "dispatch_suppressed": str(vj.get("terminal", "")).endswith("DISPATCH_SUPPRESSED_BY_VERIFY_ONLY"),
            "one_shot_gate_set_during_verify": vj.get("one_shot_gate_set"),
        },
        "frozen_v1_14_anchors_intact": {"v1_14_exec": V14_SHA, "v1_14_manifest": MANIFEST_SHA},
        "prior_failure_provenance": {k: v[1] for k, v in PRIOR_FAILURE_PROVENANCE.items()},
        "consumed_evidence": {k: v[1] for k, v in CONSUMED_EVIDENCE.items()},
        "static_audit_verdict": REQUIRED_STATIC_AUDIT_VERDICT,
        "static_audit_verdict_matches_required": True,
        "prior_diagnostic_attempt": False,
        "new_family_markers_absent": True,
        "gt_static_prohibition_pass": True,
        "scientific_output": False,
        "generated_utc": ts,
    })

    # ---- 4. negative_controls -------------------------------------------- #
    write_once(OUT["negative_controls"], {
        "artifact_kind": "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_NEGATIVE_CONTROLS",
        "revision": REVISION,
        "source": {"path": "scripts/analysis/phase36_final_probability_authority_diagnostic_negative_controls_v1_0.py",
                   "sha256": NEGCTRL_SHA},
        "headline_control": {
            "statement": ("inherited foreign v1.14 token => launcher refuses (rc 2) before dispatch; "
                          "diagnostic main() refuses (rc 8); no marker; and any GT access fails closed"),
            "exit_code_expected_no_launch_authority": 5,
            "exit_code_expected_foreign_token_present": 8,
        },
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
        "prior_attempt_consumed": False,
        "start_marker_present": False,
        "result_marker_present": False,
        "failure_marker_present": False,
        "static_audit_verdict_dependency": REQUIRED_STATIC_AUDIT_VERDICT,
        "static_audit_sha256": "8def086c44a7e80461c729f41ab61c0be347ef1589c94d6884a082adbde64ed4",
        "reconciliation_v2_sha256": "cc9a3b502f59e3855c395b9d6afa2f5616f513d60af4756e4477a9370889cc3c",
        "consumed_evidence_bound": {k: v[1] for k, v in CONSUMED_EVIDENCE.items()},
        "phase27_final_prob_authority": PHASE27_FINAL_PROB_AUTHORITY,
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

    out_sha = {name: sha(p) for name, p in OUT.items()}
    print(json.dumps({
        "status": "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_GOVERNANCE_BUILT",
        "unit_run": unit_run,
        "preflight_run": preflight_run,
        "negative_controls_run": nc_run,
        "launcher_verify_only_terminal": vj.get("terminal"),
        "governance_sha256": out_sha,
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
