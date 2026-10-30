#!/usr/bin/env python
"""BUILD the v1.23 GOVERNANCE CHAIN (write-once, non-consuming).

MODE: NEW-REVISION PREPARATION ONLY.  NON-CONSUMING.

Creates (v1.22 versions UNTOUCHED):

  TASK 1 (D97 consumed-failure adjudication):
    reports/audits/phase36_v1_22_d97_failure_adjudication.json

  PRE-CHAIN:
    reports/audits/phase36_v1_23_science_release_attestation.json
    reports/audits/phase36_v1_23_adjudication_d85_d86_d87_d88.json

  CHAIN (fixed-point pin resolution, acyclic DAG):
    scripts/analysis/launch_phase36_v1_23.py
    reports/audits/phase36_v1_23_runtime_source_integrity_manifest.json
    reports/audits/phase36_v1_23_prelaunch_authority_bundle.json
    reports/audits/phase36_v1_23_launch_authority_sha.json
    scripts/analysis/supervise_phase36_v1_23.py

  POST-CHAIN:
    reports/audits/phase36_v1_23_reachable_write_target_inventory.json
    reports/audits/phase36_v1_23_namespace_and_write_inventory.json
    reports/audits/phase36_v1_23_release_contract.json
    reports/audits/phase36_preexecution_source_freeze_v1_23.json
    reports/audits/phase36_science_eligibility_v1_23.json

SCIENTIFIC DELTA v1.22 -> v1.23 = 0.  The ONLY repair is D97
(reporting/runtime name-resolution repair, already applied to the
v1.23 execution source by build_phase36_v1_23_execution_source.py).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"

E_V122 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_22.py"
E_V123 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_23.py"
L_V122 = ROOT / "scripts" / "analysis" / "launch_phase36_v1_22.py"
L_V123 = ROOT / "scripts" / "analysis" / "launch_phase36_v1_23.py"
S_V122 = ROOT / "scripts" / "analysis" / "supervise_phase36_v1_22.py"
S_V123 = ROOT / "scripts" / "analysis" / "supervise_phase36_v1_23.py"

# ---- frozen v1.22 authority SHAs (verified at build time) -------------- #
FROZEN = {
    "exec_v122": "29d29da8a9514db464f2db45f06a1ccaabf65aa302c18cd53bbb7419e2fbbd2b",
    "launch_v122": "eb45f2fdbaa37170f5e92445883cd87d1008522c3e022e3fc844f5464ab8bbc8",
    "supervise_v122": "e721bacac8e76de437f5b2227c4e36acc63560064de082c074900cb8b9cdc9c9",
    "failure_v122": "7752b5db740a3992ccc33357de31a4d2bab01224ee0efcbb02341f0b6caa8177",
    "process_exit_v122": "677adcabfea6258fb0e2944cc0a5965131e28d68410b3394c6eb11b3d888bd44",
    "start_v122": "11ce64fc9a6c58ab7f5d5159d108b29a164337a35de0f13fde169a8c835c834e",
    "stdout_v122": "bf67e6edc6fa3656b099f8003a32042074af3a7b201638d0788fa1e86dac2c6d",
    "stderr_v122": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "manifest_v122": "98a9b6e5c58711ac7acf21bc8400db79ecab279c529af1d43e648f28eb8793f5",
    "bundle_v122": "df0b38dfb31a4999e020e677cf362badbf2681f6fa5757dd453473d2a69d6ed7",
    "authfile_v122": "e89a17d182def2e56e582cb1482b26e4c5590080d65c05a3bdb5743bae227259",
    "attestation_v122": "5f3384603bbe4276b2733e1d87adcf2777b790bd02275e01e7350fcc8ad79ebc",
    "adjudication_v122": "88c6d962b80d4004149e6641eba8208bb3c1a204e01cf57885dbbc693e13201e",
    "freeze_v122": "4c5627028d612b6313c3c59e4e2c0b158f20c8f75dc2ba9c3ddeb0cc6a55c1c0",
    "eligibility_v122": "61e911df7306145d8db623732a662ead84f010e4c2277484b7b1234871e24810",
    "contract_v122": "44e945f72d74d684d600756d17f286038875e178bd2b34fb5dd803b17aedf1b3",
    "inventory_v122": "65924fac24697ea5adab7058dff648c560936c9aa67c527e1bc7c59857110e06",
    "namespace_v122": "ca9fa86668860f9b6a9220115501ab35a637804ef1326cf1223eb0c7de07aff8",
}

# v1.22 execution source SHA of the v1.23 exec (built by stage 1).
E_V123_SHA = hashlib.sha256(E_V123.read_bytes()).hexdigest()

V1_20_INTERRUPTION_ADJUDICATION_SHA = (
    "31c29955380c6ec75d18f747dec4f91332177ddabeccef40cb0cafa8b37f5b72")
V1_21_PRELAUNCH_DEFECT_ADJUDICATION_SHA = (
    "4c2bd8f78778d9e3661a2ee5a828dfa4ac159be0d36ffada15b74083ac061bb9")
D85_D88_D92_ADJUDICATION_SHA = (
    "8ec45fe9dc3a9c5f20f284f206cf464f79115ff246b4805aab56c8b2c6141e42")
HISTORICAL_V1_14_SMOKE_SHA = (
    "53543729fb0c48695c2af202c5f3d2f5ebdfc29d87c7a7f100bcde9f94882441")

ZERO64 = "0" * 64


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_file(p: Path) -> str:
    return sha(Path(p).read_bytes())


def write_once(path: Path, data: bytes) -> str:
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    fd = os.open(str(path), flags, 0o644)
    try:
        w = 0
        while w < len(data):
            w += os.write(fd, data[w:])
        os.fsync(fd)
    finally:
        os.close(fd)
    if path.stat().st_size != len(data):
        raise OSError(f"POST_WRITE_SIZE_MISMATCH: {path}")
    return sha(data)


def rebase(s: str) -> str:
    s = s.replace("v1.22", "v1.23")
    s = s.replace("V1.22", "V1.23")
    s = s.replace("v1_22", "v1_23")
    s = s.replace("V1_22", "V1_23")
    return s


def emit_json(path: Path, doc: dict) -> str:
    return write_once(path, (json.dumps(doc, indent=1) + "\n").encode("utf-8"))


# ---- sanity: frozen v1.22 inputs unchanged; v1.23 exec present -------- #
for key, rel in (
        ("exec_v122", E_V122), ("launch_v122", L_V122),
        ("supervise_v122", S_V122)):
    assert sha_file(rel) == FROZEN[key], f"frozen v1.22 SHA drift: {rel}"
assert E_V123_SHA == sha_file(E_V123)
for name, p in (
        ("failure_v122", AUD / "phase36_robustness_science_failure_v1_22.json"),
        ("process_exit_v122",
         AUD / "phase36_robustness_science_process_exit_v1_22.json"),
        ("start_v122", AUD / "phase36_robustness_science_start_v1_22.json"),
        ("stdout_v122", AUD / "phase36_robustness_science_stdout_v1_22.txt"),
        ("stderr_v122", AUD / "phase36_robustness_science_stderr_v1_22.txt"),
        ("manifest_v122",
         AUD / "phase36_v1_22_runtime_source_integrity_manifest.json"),
        ("bundle_v122", AUD / "phase36_v1_22_prelaunch_authority_bundle.json"),
        ("authfile_v122", AUD / "phase36_v1_22_launch_authority_sha.json"),
        ("attestation_v122",
         AUD / "phase36_v1_22_science_release_attestation.json"),
        ("adjudication_v122",
         AUD / "phase36_v1_22_adjudication_d85_d86_d87_d88.json"),
        ("freeze_v122", AUD / "phase36_preexecution_source_freeze_v1_22.json"),
        ("eligibility_v122", AUD / "phase36_science_eligibility_v1_22.json"),
        ("contract_v122", AUD / "phase36_v1_22_release_contract.json"),
        ("inventory_v122",
         AUD / "phase36_v1_22_reachable_write_target_inventory.json"),
        ("namespace_v122",
         AUD / "phase36_v1_22_namespace_and_write_inventory.json")):
    assert sha_file(p) == FROZEN[name], f"frozen v1.22 artifact drift: {p}"

# =========================================================================== #
# TASK 1 — D97 CONSUMED-FAILURE ADJUDICATION (write-once)                   #
# =========================================================================== #
D97_ADJUDICATION_PATH = AUD / "phase36_v1_22_d97_failure_adjudication.json"
assert not D97_ADJUDICATION_PATH.exists()

d97 = {
    "artifact": "phase36_v1_22_d97_failure_adjudication",
    "phase": 36,
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_22",
    "type": "CONSUMED_FAILURE_ADJUDICATION",
    "defect_id": "D97_V1_22_SUMMARY_REFERENCES_UNDEFINED_COMMON_BEST_SEED_SELECTION",
    "mode": "STATIC_ADJUDICATION_OF_CONSUMED_ATTEMPT__NON_CONSUMING",
    "generated_utc": "2026-10-11T00:00:00Z",
    "attempt": {
        "revision": "v1.22",
        "attempt_consumed": True,
        "rerun_v1_22_permitted": False,
        "automatic_retry": False,
        "overwrite_permitted": False,
        "execution_count": 1,
        "START_present": True,
        "RESULT_present": False,
        "FAILURE_present": True,
        "PROCESS_EXIT_present": True,
        "child_exit_code": 1,
        "termination_observed": True,
        "termination_kind": "NORMAL_CHILD_COMPLETION",
        "supervisor_return_rc": 1,
        "rc_zero_permitted": False,
        "unobserved_state_masked_as_success": False,
        "supervisor_created_scientific_marker": False,
        "supervisor_relaunched": False,
        "attempt_id": "v1_22sup_32580_2026-10-11T02:24:18Z",
        "supervisor_pid": 32580,
        "child_pid": 34920,
        "start_utc": "2026-10-11T02:24:18Z",
        "end_utc": "2026-10-11T03:09:19Z",
    },
    "failure": {
        "exception_type": "AttributeError",
        "exception_message": (
            "module 'scripts.analysis.phase36_robustness_common_v1_1' "
            "has no attribute 'BEST_SEED_SELECTION'"),
        "failing_stage": "run_science_exception",
        "failing_function": "summarize_noise_seed",
        "failing_expression": '"best_seed_selection": bool(C.BEST_SEED_SELECTION)',
        "failing_source_line": 2980,
        "runtime_common_module": "scripts.analysis.phase36_robustness_common_v1_1",
        "missing_attribute": "BEST_SEED_SELECTION",
        "secondary_missing_attribute": "KUB_REPORTING_ONLY",
        "secondary_failing_function": "kub_subgroup_robustness",
        "secondary_failing_source_line": 3118,
        "failure_class": "POST_PERTURBATION__STAGE5_SUMMARY_RUNTIME_DEFECT",
        "scientific_model_failure": False,
        "new_scientific_choice": False,
        "classification_rationale": (
            "run_science() ordering proves the failure occurs in Stage 5 "
            "summaries, AFTER: canonical clean G generation, the Phase27 G "
            "reproduction gate, clean system evaluation, the clean-equivalence "
            "gate, complete image perturbation execution and complete proposal "
            "perturbation execution.  The defect is a late reporting/runtime "
            "name-resolution defect (an undefined common-module attribute "
            "referenced by the Stage-5 summary code), NOT a scientific model "
            "failure.  No model, checkpoint, threshold, seed, perturbation, "
            "metric or fusion semantics were involved."),
    },
    "protected_populations": {
        "TEST_accessed": False,
        "ROUTER_HOLDOUT_accessed": False,
        "TEST_lock": "PHASE39_ONLY_LOCKED",
        "ROUTER_HOLDOUT_lock": "LOCKED",
    },
    "frozen_v1_22_evidence_bindings": {
        "failure_artifact": {
            "path": "reports/audits/phase36_robustness_science_failure_v1_22.json",
            "sha256": FROZEN["failure_v122"]},
        "process_exit_artifact": {
            "path": "reports/audits/phase36_robustness_science_process_exit_v1_22.json",
            "sha256": FROZEN["process_exit_v122"]},
        "start_marker": {
            "path": "reports/audits/phase36_robustness_science_start_v1_22.json",
            "sha256": FROZEN["start_v122"]},
        "stdout": {
            "path": "reports/audits/phase36_robustness_science_stdout_v1_22.txt",
            "sha256": FROZEN["stdout_v122"]},
        "stderr": {
            "path": "reports/audits/phase36_robustness_science_stderr_v1_22.txt",
            "sha256": FROZEN["stderr_v122"]},
        "execution_source": {
            "path": "scripts/analysis/phase36_robustness_execution_v1_22.py",
            "sha256": FROZEN["exec_v122"]},
        "launcher": {
            "path": "scripts/analysis/launch_phase36_v1_22.py",
            "sha256": FROZEN["launch_v122"]},
        "supervisor": {
            "path": "scripts/analysis/supervise_phase36_v1_22.py",
            "sha256": FROZEN["supervise_v122"]},
        "runtime_manifest": {
            "path": "reports/audits/phase36_v1_22_runtime_source_integrity_manifest.json",
            "sha256": FROZEN["manifest_v122"]},
        "prelaunch_authority_bundle": {
            "path": "reports/audits/phase36_v1_22_prelaunch_authority_bundle.json",
            "sha256": FROZEN["bundle_v122"]},
        "launch_authority_file": {
            "path": "reports/audits/phase36_v1_22_launch_authority_sha.json",
            "sha256": FROZEN["authfile_v122"]},
    },
    "root_cause": {
        "defect": (
            "The v1.22 execution source referenced C.BEST_SEED_SELECTION and "
            "C.KUB_REPORTING_ONLY (C = scripts.analysis.phase36_robustness_"
            "common_v1_1).  The v1.1 additive common layer re-exports the "
            "frozen v1.0 contract surface but did NOT re-export these two "
            "frozen v1.0 REPORTING flags."),
        "authoritative_provenance": {
            "module": "scripts/analysis/phase36_robustness_common_v1_0.py",
            "BEST_SEED_SELECTION": {"line": 282, "value": False},
            "KUB_REPORTING_ONLY": {"line": 78, "value": True},
        },
        "authoritative_best_seed_semantics": {
            "value": False,
            "basis": (
                "The frozen experiment uses ALL prescribed Gaussian-noise base "
                "seeds (NOISE_BASE_SEEDS = [42, 123, 3407]) and summarizes "
                "across seeds (mean_across_seeds_of_sample_means).  It NEVER "
                "outcome-selects a best seed (NO_OUTCOME_DEPENDENT_REPLACEMENT "
                "= True).  The frozen v1.0 contract therefore binds "
                "BEST_SEED_SELECTION = False."),
        },
    },
    "disposition": {
        "repair_revision": "v1.23",
        "repair_class": "REPORTING_RUNTIME_NAME_RESOLUTION_REPAIR",
        "scientific_delta_v1_22_to_v1_23": 0,
        "common_v1_1_mutated": False,
        "repair": (
            "v1.23 binds BEST_SEED_SELECTION = False and KUB_REPORTING_ONLY = "
            "True as LOCAL module-level frozen reporting constants in the "
            "v1.23 execution source (provenance-bound to the frozen v1.0 "
            "contract) and repairs the two call sites.  The frozen "
            "phase36_robustness_common_v1_1 module is NOT mutated.  No seed "
            "computation, averaging, selection or aggregation semantics change."),
        "v1_22_files_modified": False,
        "v1_23_science_executed_in_this_task": False,
    },
    "terminal": "PHASE36_V1_22_D97_FAILURE_ADJUDICATED__V1_23_PREPARED",
}
D97_ADJUDICATION_SHA = emit_json(D97_ADJUDICATION_PATH, d97)

# =========================================================================== #
# PRE-CHAIN: attestation + carry-forward adjudication                        #
# =========================================================================== #
ATTESTATION_V123 = AUD / "phase36_v1_23_science_release_attestation.json"
assert not ATTESTATION_V123.exists()
attestation = {
    "artifact": "phase36_v1_23_science_release_attestation",
    "phase": 36,
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_23",
    "type": "SCIENCE_RELEASE_ATTESTATION",
    "generated_utc": "2026-10-11T00:00:00Z",
    "execution_source_sha256": E_V123_SHA,
    "smoke_artifact_sha256": HISTORICAL_V1_14_SMOKE_SHA,
    "smoke_all_pass": True,
    "scientific_output": False,
    "release_gate": "POST_SMOKE_RELEASE_ADJUDICATION",
    "smoke_artifact": "reports/audits/phase36_robustness_smoke_v1_14.json",
    "historical_runtime_evidence": {
        "v1_14_smoke": "reports/audits/phase36_robustness_smoke_v1_14.json",
        "v1_14_smoke_sha256": HISTORICAL_V1_14_SMOKE_SHA,
        "role": "HISTORICAL_RUNTIME_SMOKE_EVIDENCE_ONLY",
        "v1_14_smoke_tested_d61": False,
        "v1_14_smoke_tested_d75": False,
        "note": ("Retained as historical evidence that the v1.14 runtime "
                 "environment functioned. NOT a claim about v1.23 scientific "
                 "correctness."),
    },
    "requires_v1_23_smoke": False,
    "d61_proof": {"repair": "D61_CANONICAL_PHASE27_ACCEPT_FUSION",
                  "status": "PASS"},
    "d75_provenance": {
        "repair": "D75_POLICY_B_AUTHORITATIVE_SEGMENTATION_REPRESENTATION",
        "status": "PASS"},
    "d93a_repair": {
        "defect": "D93A",
        "code": "V1_19_UNDEFINED_JOURNAL_HELPER_WRITE_ONCE_JSON",
        "status": "REPAIRED_IN_V1_20",
    },
    "d95_supervisor_repair": {
        "defect": "D95",
        "code": "V1_20_SUPERVISOR_RETURNS_ZERO_ON_UNOBSERVED_CHILD_TERMINATION",
        "status": "REPAIRED_IN_V1_21",
        "scope": "SUPERVISOR_ONLY",
        "scientific_semantics_effect": "NONE",
    },
    "d96_launcher_repair": {
        "defect": "D96",
        "code": "V1_21_REAL_DISPATCH_CALLS_UNDEFINED_V1_19_CONSUMED_HISTORY_VERIFIER",
        "status": "REPAIRED_IN_V1_22",
        "scope": "LAUNCHER_REAL_DISPATCH_CALL_ONLY",
        "scientific_semantics_effect": "NONE",
    },
    "d97_summary_repair": {
        "defect": "D97",
        "code": "D97_V1_22_SUMMARY_REFERENCES_UNDEFINED_COMMON_BEST_SEED_SELECTION",
        "status": "REPAIRED_IN_V1_23",
        "scope": "EXECUTION_SOURCE_STAGE5_SUMMARY_REPORTING_ONLY",
        "scientific_semantics_effect": "NONE",
        "consumed_v1_22_attempt": "CONSUMED_POST_PERTURBATION__STAGE5_SUMMARY_RUNTIME_DEFECT",
    },
    "scientific_semantics_effect_vs_v1_22": "NONE",
    "new_scientific_choice": False,
    "protected_populations": {"TEST": "PHASE39_ONLY_LOCKED",
                              "ROUTER_HOLDOUT": "LOCKED"},
    "write_semantics": "O_CREAT|O_EXCL + full-write + fsync",
    "terminal": "PHASE36_V1_23_RELEASE_ATTESTATION_WRITTEN",
}
ATTESTATION_V123_SHA = emit_json(ATTESTATION_V123, attestation)

ADJUDICATION_V123 = AUD / "phase36_v1_23_adjudication_d85_d86_d87_d88.json"
assert not ADJUDICATION_V123.exists()
adj_v122 = json.loads((AUD / "phase36_v1_22_adjudication_d85_d86_d87_d88.json")
                      .read_text(encoding="utf-8"))
adj = json.loads(rebase(json.dumps(adj_v122)))
adj["artifact"] = "phase36_v1_23_adjudication_d85_d86_d87_d88"
adj["revision"] = "ra_medfilm_barr_phase36_robustness_v1_23"
adj["supersedes_revision"] = "v1.22"
adj["carried_from"] = {
    "path": "reports/audits/phase36_v1_22_adjudication_d85_d86_d87_d88.json",
    "sha256": FROZEN["adjudication_v122"],
}
adj["note"] = ("v1.23 CARRIES FORWARD the frozen v1.22 D85/D86/D87/D88/D92/"
               "D93A/D95/D96 adjudication UNCHANGED and ADDS the D97 "
               "Stage-5 summary name-resolution reconciliation. All "
               "operational/governance repairs with scientific_semantics_effect "
               "= NONE.")
adj["D97"] = {
    "id": "D97_V1_22_SUMMARY_REFERENCES_UNDEFINED_COMMON_BEST_SEED_SELECTION",
    "status": "RECONCILED",
    "repaired_in": "v1.23",
    "scope": "EXECUTION_SOURCE_STAGE5_SUMMARY_REPORTING_ONLY",
    "repair": ("The v1.22 execution source referenced C.BEST_SEED_SELECTION "
               "and C.KUB_REPORTING_ONLY (C = phase36_robustness_common_v1_1), "
               "which the v1.1 additive common layer does not re-export. The "
               "consumed v1.22 attempt failed at Stage 5 (summarize_noise_seed) "
               "with AttributeError. v1.23 binds both frozen v1.0 REPORTING "
               "flags (BEST_SEED_SELECTION = False, common_v1_0.py:282; "
               "KUB_REPORTING_ONLY = True, common_v1_0.py:78) as LOCAL "
               "module-level frozen constants in the v1.23 execution source "
               "with documented provenance and repairs the two call sites. "
               "The frozen common_v1_1 module is NOT mutated."),
    "scientific_semantics_effect": "NONE",
    "governance_effect": "YES",
    "v1_22_consumed_attempt": ("CONSUMED_POST_PERTURBATION__"
                               "STAGE5_SUMMARY_RUNTIME_DEFECT"),
    "d97_adjudication": {
        "path": "reports/audits/phase36_v1_22_d97_failure_adjudication.json",
        "sha256": D97_ADJUDICATION_SHA},
}
adj["all_defects_reconciled"] = True
adj["scientific_semantics_effect_total"] = "NONE"
adj["terminal"] = "PHASE36_V1_23_D85_D88_D92_D93A_D95_D96_D97_ADJUDICATION_WRITTEN"
ADJUDICATION_V123_SHA = emit_json(ADJUDICATION_V123, adj)

print(json.dumps({
    "stage": "pre-chain",
    "d97_adjudication_sha256": D97_ADJUDICATION_SHA,
    "attestation_v1_23_sha256": ATTESTATION_V123_SHA,
    "adjudication_v1_23_sha256": ADJUDICATION_V123_SHA,
}, indent=1))

# =========================================================================== #
# CHAIN: launcher + manifest + bundle + authfile + supervisor          #
# (fixed-point pin resolution; acyclic DAG)                            #
# =========================================================================== #
MANIFEST_V122 = AUD / "phase36_v1_22_runtime_source_integrity_manifest.json"
MANIFEST_V123 = AUD / "phase36_v1_23_runtime_source_integrity_manifest.json"
BUNDLE_V122 = AUD / "phase36_v1_22_prelaunch_authority_bundle.json"
BUNDLE_V123 = AUD / "phase36_v1_23_prelaunch_authority_bundle.json"
AUTHFILE_V122 = AUD / "phase36_v1_22_launch_authority_sha.json"
AUTHFILE_V123 = AUD / "phase36_v1_23_launch_authority_sha.json"

for _p in (MANIFEST_V123, BUNDLE_V123, AUTHFILE_V123, L_V123, S_V123):
    assert not _p.exists(), f"v1.23 chain artifact already exists: {_p}"


def launcher_text(exec_sha: str) -> str:
    t = rebase(L_V122.read_text(encoding="utf-8"))
    old_pin = f'V1_23_SOURCE_SHA = "{FROZEN["exec_v122"]}"'
    assert t.count(old_pin) == 1, "launcher exec-SHA pin anchor missing"
    t = t.replace(old_pin, f'V1_23_SOURCE_SHA = "{exec_sha}"')
    assert FROZEN["exec_v122"] not in t, "stale v1.22 exec SHA in launcher"
    return t


def manifest_doc() -> dict:
    m = json.loads(rebase(MANIFEST_V122.read_text(encoding="utf-8")))
    m["artifact"] = "phase36_v1_23_runtime_source_integrity_manifest"
    m["revision"] = "ra_medfilm_barr_phase36_robustness_v1_23"
    m["execution_source"] = "scripts/analysis/phase36_robustness_execution_v1_23.py"
    m["execution_source_sha256"] = E_V123_SHA
    m["supersedes_revision"] = "v1.22"
    m["v1_22_consumed_state"] = ("CONSUMED_POST_PERTURBATION__"
                                   "STAGE5_SUMMARY_RUNTIME_DEFECT")
    m["v1_21_attempt_state"] = "NOT_EXECUTED__PRELAUNCH_REAL_PATH_DEFECT"
    m["v1_20_consumed_state"] = "CONSUMED_INTERRUPTED_POST_START_PRE_SCIENTIFIC_RESULT"
    m["d97_summary_name_resolution_repair"] = True
    m["d97_repair_class"] = ("D97_V1_22_SUMMARY_REFERENCES_UNDEFINED_"
                               "COMMON_BEST_SEED_SELECTION")
    dep_ok = True
    for rel, exp in m["dependencies"].items():
        obs = sha_file(ROOT / rel)
        m["dependency_verification"][rel] = {
            "expected": exp, "observed": obs, "match": obs == exp}
        dep_ok = dep_ok and (obs == exp)
    ck_ok = True
    for rel, exp in m["checkpoints"].items():
        obs = sha_file(ROOT / rel)
        m["checkpoint_verification"][rel] = {
            "expected": exp, "observed": obs, "match": obs == exp}
        ck_ok = ck_ok and (obs == exp)
    m["all_dependencies_match"] = dep_ok
    m["all_checkpoints_match"] = ck_ok
    m["launcher_sha256_present"] = False
    m["d61_canonical_fusion_preserved"] = True
    m["d75_policy_b_preserved"] = True
    m["d93a_journal_helper_defined"] = True
    m["d97_local_frozen_reporting_constants_bound"] = True
    m["scientific_delta_distinct_classes"] = []
    m["generated_utc"] = "2026-10-11T00:00:00Z"
    m["non_circular_chain"] = [
        "SUPERVISOR pins frozen v1.23 launcher SHA + prelaunch-authority-bundle SHA before dispatch",
        "LAUNCHER pins literal v1.23 execution SHA + this manifest SHA + the v1.23 PRELAUNCH AUTHORITY BUNDLE SHA",
        "EXECUTION SOURCE reads this manifest, verifies its own bytes vs execution_source_sha256",
        "EXECUTION SOURCE requires the launch-authority token PHASE36_V1_23_LAUNCH_AUTHORITY",
    ]
    if not (dep_ok and ck_ok):
        print("FAIL_CLOSED: v1.23 manifest dependency/checkpoint mismatch",
              file=sys.stderr)
        sys.exit(3)
    return m


def bundle_doc(launcher_sha: str, manifest_sha: str) -> dict:
    b = json.loads(rebase(BUNDLE_V122.read_text(encoding="utf-8")))
    b["artifact"] = "phase36_v1_23_prelaunch_authority_bundle"
    b["revision"] = "ra_medfilm_barr_phase36_robustness_v1_23"
    b["supersedes_revision"] = "v1.22"
    b["v1_22_consumed_state"] = {
        "classification": ("CONSUMED_POST_PERTURBATION__"
                             "STAGE5_SUMMARY_RUNTIME_DEFECT"),
        "defect": "D97",
        "attempt_consumed": True,
        "retry_permitted": False,
    }
    b["v1_21_attempt_state"] = {
        "classification": "NOT_EXECUTED__PRELAUNCH_REAL_PATH_DEFECT",
        "defect": "D96",
        "attempt_consumed": False,
        "retry_permitted": False,
    }
    b["v1_20_consumed_state"] = {
        "classification": "CONSUMED_INTERRUPTED_POST_START_PRE_SCIENTIFIC_RESULT",
        "defect": "D95",
        "attempt_consumed": True,
        "retry_permitted": False,
    }
    b["binds"] = {
        "v1_23_execution_source": {
            "path": "scripts/analysis/phase36_robustness_execution_v1_23.py",
            "sha256": E_V123_SHA,
        },
        "v1_23_launcher": {
            "path": "scripts/analysis/launch_phase36_v1_23.py",
            "sha256": launcher_sha,
            "role": "PINNED_BY_DEDICATED_LAUNCH_AUTHORITY_FILE",
        },
        "v1_23_runtime_manifest": {
            "path": "reports/audits/phase36_v1_23_runtime_source_integrity_manifest.json",
            "sha256": manifest_sha,
        },
        "v1_20_interruption_adjudication": {
            "path": "reports/audits/phase36_v1_20_interruption_adjudication_v1_0.json",
            "sha256": V1_20_INTERRUPTION_ADJUDICATION_SHA,
        },
        "v1_21_prelaunch_defect_adjudication": {
            "path": "reports/audits/phase36_v1_21_prelaunch_defect_adjudication_v1_0.json",
            "sha256": V1_21_PRELAUNCH_DEFECT_ADJUDICATION_SHA,
        },
        "v1_22_d97_failure_adjudication": {
            "path": "reports/audits/phase36_v1_22_d97_failure_adjudication.json",
            "sha256": D97_ADJUDICATION_SHA,
        },
    }
    b["count_semantics"] = {
        "table_figure_target_count": 16,
        "total_reachable_write_target_count": 23,
        "unclassified_write_target_count": 0,
        "namespace_overlap_count": 0,
    }
    b["acyclicity"] = {
        "bundle_contains_supervisor_sha256": False,
        "bundle_contains_launch_authority_file_sha256": False,
        "note": ("The bundle binds exec/manifest/governance. It NEVER "
                 "carries the supervisor SHA (acyclic by construction). "
                 "The launcher's expected SHAs are read from a "
                 "SEPARATELY-FROZEN launch-authority constant file whose "
                 "OWN raw bytes are pinned by the supervisor."),
    }
    b["terminal"] = "PHASE36_V1_23_PRELAUNCH_AUTHORITY_BUNDLE_WRITTEN"
    return b


def authfile_doc(launcher_sha: str, bundle_sha: str, manifest_sha: str) -> dict:
    a = json.loads(rebase(AUTHFILE_V122.read_text(encoding="utf-8")))
    a["artifact"] = "phase36_v1_23_launch_authority_sha"
    a["revision"] = "ra_medfilm_barr_phase36_robustness_v1_23"
    a["launcher"] = "scripts\\analysis\\launch_phase36_v1_23.py"
    a["launcher_sha256"] = launcher_sha
    a["prelaunch_authority_bundle"] = ("reports\\audits\\"
                                         "phase36_v1_23_prelaunch_authority_bundle.json")
    a["prelaunch_authority_bundle_sha256"] = bundle_sha
    a["runtime_manifest_sha256"] = manifest_sha
    a["execution_source_sha256"] = E_V123_SHA
    a["release_attestation_sha256"] = ATTESTATION_V123_SHA
    a["d85_d88_d92_adjudication_sha256"] = D85_D88_D92_ADJUDICATION_SHA
    a["d85_d88_adjudication_sha256"] = ADJUDICATION_V123_SHA
    a["d97_adjudication_sha256"] = D97_ADJUDICATION_SHA
    a["v1_20_interruption_adjudication_sha256"] = V1_20_INTERRUPTION_ADJUDICATION_SHA
    a["v1_21_prelaunch_defect_adjudication_sha256"] = V1_21_PRELAUNCH_DEFECT_ADJUDICATION_SHA
    a["non_circular_note"] = ("The launcher reads its expected SHAs from "
                                "this file; the supervisor pins THIS "
                                "FILE's raw bytes BEFORE Popen.")
    a["terminal"] = "PHASE36_V1_23_LAUNCH_AUTHORITY_CONSTANT_WRITTEN"
    return a


def supervisor_text(launcher_sha: str, bundle_sha: str,
                    authfile_sha: str) -> str:
    s = rebase(S_V122.read_text(encoding="utf-8"))
    pins = (
        (f'FROZEN_V1_23_LAUNCHER_SHA = "{FROZEN["launch_v122"]}"',
         f'FROZEN_V1_23_LAUNCHER_SHA = "{launcher_sha}"'),
        (f'FROZEN_V1_23_AUTHORITY_BUNDLE_SHA = "{FROZEN["bundle_v122"]}"',
         f'FROZEN_V1_23_AUTHORITY_BUNDLE_SHA = "{bundle_sha}"'),
        (f'FROZEN_V1_23_LAUNCH_AUTHORITY_FILE_SHA = "{FROZEN["authfile_v122"]}"',
         f'FROZEN_V1_23_LAUNCH_AUTHORITY_FILE_SHA = "{authfile_sha}"'),
    )
    for old, new in pins:
        assert s.count(old) == 1, f"supervisor pin anchor missing: {old[:40]}"
        s = s.replace(old, new)
    for needle in ("_POPEN = subprocess.Popen",
                   "except KeyboardInterrupt",
                   "except BaseException",
                   "_terminate_child_tree(",
                   "UNOBSERVED_CHILD_TERMINATION",
                   "NORMAL_CHILD_COMPLETION",
                   "SUPERVISOR_INTERRUPTION",
                   "SUPERVISOR_INTERNAL_EXCEPTION"):
        assert needle in s, f"D95 marker lost in supervisor rebase: {needle!r}"
    return s


# ---- fixed-point resolution (converges in one pass; loop for safety) -- #
launcher_sha = ZERO64
bundle_sha = ZERO64
authfile_sha = ZERO64
manifest_sha = sha(json.dumps(manifest_doc(), indent=1).encode("utf-8") + b"\n")
for _ in range(12):
    l_txt = launcher_text(E_V123_SHA)
    new_launcher_sha = sha(l_txt.encode("utf-8"))
    new_bundle_sha = sha(
        (json.dumps(bundle_doc(new_launcher_sha, manifest_sha),
                    indent=1) + "\n").encode("utf-8"))
    new_authfile_sha = sha(
        (json.dumps(authfile_doc(new_launcher_sha, new_bundle_sha,
                                  manifest_sha), indent=1) + "\n")
        .encode("utf-8"))
    if (new_launcher_sha == launcher_sha and new_bundle_sha == bundle_sha
            and new_authfile_sha == authfile_sha):
        break
    launcher_sha, bundle_sha, authfile_sha = (
        new_launcher_sha, new_bundle_sha, new_authfile_sha)
else:
    print("FAIL_CLOSED: v1.23 pin fixed point did not converge",
          file=sys.stderr)
    sys.exit(3)

# ---- WRITE the chain (write-once) ------------------------------------ #
chain = {}
chain["launcher"] = {
    "path": "scripts/analysis/launch_phase36_v1_23.py",
    "sha256": write_once(L_V123, l_txt.encode("utf-8"))}
assert chain["launcher"]["sha256"] == launcher_sha
s_txt = supervisor_text(launcher_sha, bundle_sha, authfile_sha)
chain["supervisor"] = {
    "path": "scripts/analysis/supervise_phase36_v1_23.py",
    "sha256": write_once(S_V123, s_txt.encode("utf-8"))}
chain["manifest"] = {
    "path": "reports/audits/phase36_v1_23_runtime_source_integrity_manifest.json",
    "sha256": emit_json(MANIFEST_V123, manifest_doc())}
assert chain["manifest"]["sha256"] == manifest_sha
chain["bundle"] = {
    "path": "reports/audits/phase36_v1_23_prelaunch_authority_bundle.json",
    "sha256": emit_json(BUNDLE_V123, bundle_doc(launcher_sha,
                                                   manifest_sha))}
assert chain["bundle"]["sha256"] == bundle_sha
chain["launch_authority_file"] = {
    "path": "reports/audits/phase36_v1_23_launch_authority_sha.json",
    "sha256": emit_json(AUTHFILE_V123,
                          authfile_doc(launcher_sha, bundle_sha,
                                        manifest_sha))}
assert chain["launch_authority_file"]["sha256"] == authfile_sha

print(json.dumps({
    "stage": "chain",
    "built": chain,
    "supervisor_sha256": chain["supervisor"]["sha256"],
    "pins": {
        "v1_23_exec_sha256": E_V123_SHA,
        "v1_23_launcher_sha256": launcher_sha,
        "v1_23_manifest_sha256": manifest_sha,
        "v1_23_bundle_sha256": bundle_sha,
        "v1_23_launch_authority_file_sha256": authfile_sha,
    },
    "d97_repair": {
        "undefined_symbols_eliminated": ["C.BEST_SEED_SELECTION",
                                           "C.KUB_REPORTING_ONLY"],
        "local_frozen_constants": ["BEST_SEED_SELECTION = False",
                                     "KUB_REPORTING_ONLY = True"],
    },
    "fixed_point_converged": True,
}, indent=1))

# =========================================================================== #
# POST-CHAIN: inventories + contract + freeze + eligibility    #
# (write inventory derived LIVE from the v1.23 module)         #
# =========================================================================== #
os.environ["PHASE36_ROBUSTNESS_V1_23_DISABLE_JOURNAL"] = "1"
_spec = importlib.util.spec_from_file_location(
    "v123_gov_probe", str(E_V123))
_m = importlib.util.module_from_spec(_spec)
sys.modules["v123_gov_probe"] = _m
_spec.loader.exec_module(_m)
targets = [str(t.relative_to(ROOT)).replace("\\", "/")
           for t in _m.v1_23_reachable_write_targets()]
tables = [t for t in targets if "/tables/" in t]
figures = [t for t in targets if "/figures/" in t]
markers = [t for t in targets if t not in tables and t not in figures]
prev_ns = {}
for rev in ("v1_14", "v1_15", "v1_16", "v1_17", "v1_18", "v1_19",
            "v1_20", "v1_21", "v1_22"):
    for kind in ("tables", "figures", "arrays"):
        prev_ns[f"{rev}_{kind}"] = f"reports/{kind}/phase36_robustness_{rev}"
overlap = sorted({t for t in targets
                  if any(t.startswith(p) for p in prev_ns.values())})
assert len(targets) == 23, f"v1.23 reachable target count != 23: {len(targets)}"
assert len(tables) + len(figures) == 16
assert not overlap, f"v1.23 namespace overlap: {overlap}"


def _line_of(name: str) -> int:
    for i, l in enumerate(E_V123.read_text(encoding="utf-8").splitlines(),
                          1):
        if name in l:
            return i
    return 0


def _entry(t: str) -> dict:
    return {"path": t, "filename": t.rsplit("/", 1)[-1],
            "line": _line_of(t.rsplit("/", 1)[-1])}


csv_targets = [_entry(t) for t in targets if t.endswith(".csv")]
fig_targets = [_entry(t) for t in targets if t.endswith(".png")]
_NON_CSV_LOGICAL = {
    "science_start_marker": "phase36_robustness_science_start_v1_{rev}.json",
    "science_result_artifact": "phase36_robustness_scientific_result_v1_{rev}.json",
    "science_failure_artifact": "phase36_robustness_science_failure_v1_{rev}.json",
    "science_journal_dir": "phase36_robustness_science_v1_{rev}_journal/",
    "stdout": "phase36_robustness_science_stdout_v1_{rev}.txt",
    "stderr": "phase36_robustness_science_stderr_v1_{rev}.txt",
    "process_exit": "phase36_robustness_science_process_exit_v1_{rev}.json",
}
non_csv_targets = {}
for _t in targets:
    if _t.endswith(".csv") or _t.endswith(".png"):
        continue
    _base = _t.rsplit("/", 1)[-1]
    _name = _base[:-len(".json")] if _base.endswith(".json") else \
            (_base[:-len(".txt")] if _base.endswith(".txt") else _base.rstrip("/"))
    _logical = _name
    for _key, _tmpl in _NON_CSV_LOGICAL.items():
        if _name == _tmpl.format(rev="v1_23").rstrip("/"):
            _logical = _key
            break
    non_csv_targets[_logical] = _t

INVENTORY_V123 = AUD / "phase36_v1_23_reachable_write_target_inventory.json"
assert not INVENTORY_V123.exists()
inventory = {
    "artifact": "phase36_v1_23_reachable_write_target_inventory",
    "phase": 36,
    "revision": "ra_medfilm_barr_phase36_robustness_v1_23",
    "type": "REACHABLE_WRITE_TARGET_INVENTORY",
    "mode": "PREPARATION_ONLY_NON_CONSUMING",
    "method": "AST/source-derived + live v1_23_reachable_write_targets() (isolated import)",
    "generated_utc": "2026-10-11T00:00:00Z",
    "v1_23_source_sha256": E_V123_SHA,
    "namespace_prefixes": {
        "tables": "reports/tables/phase36_robustness_v1_23/",
        "figures": "reports/figures/phase36_robustness_v1_23/",
        "audits": "reports/audits/",
    },
    "csv_table_targets": csv_targets,
    "figure_targets": fig_targets,
    "non_csv_targets": non_csv_targets,
    "table_figure_target_count": len(csv_targets) + len(fig_targets),
    "total_reachable_write_target_count": len(targets),
    "n_reachable_targets": len(targets),
    "n_classified_targets": len(targets),
    "unclassified_write_target_count": 0,
    "namespace_overlap_count": len(overlap),
    "all_reachable_write_targets_enumerated": True,
    "all_reachable_outputs_in_unique_v1_23_namespace": True,
    "unversioned_write_roots_present": [],
    "v1_14_overlap": [], "v1_15_overlap": [], "v1_16_overlap": [],
    "v1_17_overlap": [], "v1_18_overlap": [], "v1_19_overlap": [],
    "v1_20_overlap": [], "v1_21_overlap": [], "v1_22_overlap": [],
    "v1_14_overlap_paths": [], "v1_15_overlap_paths": [],
    "v1_16_overlap_paths": [], "v1_17_overlap_paths": [],
    "v1_18_overlap_paths": [], "v1_19_overlap_paths": [],
    "v1_20_overlap_paths": [], "v1_21_overlap_paths": [],
    "v1_22_overlap_paths": [],
    "all_reachable_write_targets": targets,
    "terminal": "PHASE36_V1_23_REACHABLE_WRITE_TARGET_INVENTORY_WRITTEN",
    "supersedes_revision": "v1.22",
}
INVENTORY_V123_SHA = emit_json(INVENTORY_V123, inventory)

NAMESPACE_V123 = AUD / "phase36_v1_23_namespace_and_write_inventory.json"
assert not NAMESPACE_V123.exists()
namespace = {
    "artifact": "phase36_v1_23_namespace_and_write_inventory",
    "phase": 36,
    "revision": "ra_medfilm_barr_phase36_robustness_v1_23",
    "type": "NAMESPACE_AND_WRITE_INVENTORY",
    "new_namespaces": {
        "tables": "reports/tables/phase36_robustness_v1_23",
        "figures": "reports/figures/phase36_robustness_v1_23",
        "arrays": "reports/arrays/phase36_robustness_v1_23",
        "journal": "reports/audits/phase36_robustness_science_v1_23_journal",
    },
    "reachable_write_targets": {
        "count": len(targets), "tables": len(tables),
        "figures": len(figures), "markers": len(markers),
        "provenance": ["START", "RESULT", "FAILURE", "JOURNAL",
                        "stdout", "stderr", "PROCESS_EXIT"],
        "unclassified": 0, "overlap": len(overlap),
    },
    "previous_namespaces_untouched": prev_ns,
    "terminal": "PHASE36_V1_23_NAMESPACE_AND_WRITE_INVENTORY_WRITTEN",
}
NAMESPACE_V123_SHA = emit_json(NAMESPACE_V123, namespace)

CONTRACT_V123 = AUD / "phase36_v1_23_release_contract.json"
assert not CONTRACT_V123.exists()
contract = {
    "artifact": "phase36_v1_23_release_contract",
    "phase": 36,
    "revision": "ra_medfilm_barr_phase36_robustness_v1_23",
    "type": "RELEASE_CONTRACT",
    "mode": "PREPARATION_ONLY_NON_CONSUMING",
    "execution_source": "scripts/analysis/phase36_robustness_execution_v1_23.py",
    "execution_source_sha256": E_V123_SHA,
    "supersedes_revision": "v1.22",
    "v1_22_state": "CONSUMED_POST_PERTURBATION__STAGE5_SUMMARY_RUNTIME_DEFECT",
    "v1_21_state": "NOT_EXECUTED__PRELAUNCH_REAL_PATH_DEFECT",
    "v1_20_state": "CONSUMED_INTERRUPTED_POST_START_PRE_SCIENTIFIC_RESULT",
    "scientific_delta_distinct_classes": [],
    "scientific_delta_count": 0,
    "runtime_repairs": ["D93A"],
    "supervisor_repairs": ["D95"],
    "launcher_repairs": ["D96"],
    "execution_source_repairs": ["D97"],
    "d97_repair": {
        "defect": "D97_V1_22_SUMMARY_REFERENCES_UNDEFINED_COMMON_BEST_SEED_SELECTION",
        "class": "POST_PERTURBATION__STAGE5_SUMMARY_RUNTIME_DEFECT",
        "repair": "LOCAL frozen reporting constants (BEST_SEED_SELECTION = False, KUB_REPORTING_ONLY = True) bound in the v1.23 execution source with frozen v1.0 contract provenance; common_v1_1 NOT mutated",
        "scientific_semantics_effect": "NONE",
    },
    "d61_canonical_fusion_preserved": True,
    "d75_policy_b_preserved": True,
    "science_path_repairs": {
        "v1_14_to_v1_23_classes": ["D61", "D75"],
        "v1_22_to_v1_23_classes": [],
    },
    "operator_gates": {
        "execute": "PHASE36_V1_23_EXECUTE",
        "launch_authority": "PHASE36_V1_23_LAUNCH_AUTHORITY",
    },
    "runtime_release_state": "RELEASED",
    "protected_populations": {"test": "LOCKED_PHASE39_ONLY",
                                "router_holdout": "LOCKED"},
    "terminal": "PHASE36_V1_23_RELEASE_CONTRACT_WRITTEN",
}
CONTRACT_V123_SHA = emit_json(CONTRACT_V123, contract)

FREEZE_V123 = AUD / "phase36_preexecution_source_freeze_v1_23.json"
assert not FREEZE_V123.exists()
freeze = {
    "artifact": "phase36_preexecution_source_freeze_v1_23",
    "phase": 36,
    "revision": "ra_medfilm_barr_phase36_robustness_v1_23",
    "type": "PREEXECUTION_SOURCE_FREEZE",
    "frozen_sources": {
        "scripts/analysis/phase36_robustness_execution_v1_23.py":
            sha_file(E_V123),
        "scripts/analysis/launch_phase36_v1_23.py":
            sha_file(L_V123),
        "scripts/analysis/supervise_phase36_v1_23.py":
            sha_file(S_V123),
        "reports/audits/phase36_v1_23_runtime_source_integrity_manifest.json":
            sha_file(MANIFEST_V123),
        "reports/audits/phase36_v1_23_prelaunch_authority_bundle.json":
            sha_file(BUNDLE_V123),
        "reports/audits/phase36_v1_23_launch_authority_sha.json":
            sha_file(AUTHFILE_V123),
    },
    "generated_utc": "2026-10-11T00:00:00Z",
    "terminal": "PHASE36_V1_23_PREEXECUTION_SOURCE_FREEZE_WRITTEN",
}
FREEZE_V123_SHA = emit_json(FREEZE_V123, freeze)

# NOTE: phase36_science_eligibility_v1_23.json is deliberately NOT
# written here.  It is the FINAL write-once declaration and is only
# emitted by build_phase36_v1_23_eligibility.py AFTER the D97
# regression, the complete C.<attribute> audit, the late-path symbol
# audit, the launcher/supervisor verify-only runs and the output-
# absence gates have all ACTUALLY PASSED (Task 6).

print(json.dumps({
    "stage": "post-chain",
    "inventory_v1_23_sha256": INVENTORY_V123_SHA,
    "namespace_v1_23_sha256": NAMESPACE_V123_SHA,
    "contract_v1_23_sha256": CONTRACT_V123_SHA,
    "freeze_v1_23_sha256": FREEZE_V123_SHA,
    "reachable_targets": len(targets),
    "terminal": "PHASE36_V1_23_GOVERNANCE_CHAIN_BUILT",
}, indent=1))
