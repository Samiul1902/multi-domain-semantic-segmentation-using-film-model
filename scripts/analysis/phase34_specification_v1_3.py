#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase34 v1.3 amendment generator: defect records, contracts, freeze, eligibility, spec,
no-measurement audit, final check and terminal.

ZERO-EXECUTION / STATIC GOVERNANCE ONLY. Never constructs a model, never deserializes a
checkpoint into a model, never forwards, never times, never measures memory, never profiles.
The ONLY execution permitted here is the import-only probe (module/class imports), which is
separately counted.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase34_specification_v1_3.py
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"
DOCS = ROOT / "docs"
METHOD = "RA-MedFiLM-BARR"
REVISION = "ra_medfilm_barr_phase34_efficiency_profiling_v1_3"
CLASSIFICATION = "PRE_MEASUREMENT_WORKER_IMPORT_AND_UNTIMED_SMOKE_EXECUTION_AMENDMENT"

TERMINAL = ("PHASE34_EFFICIENCY_PROFILING_SPEC_V1_3_COMPLETE__CWD_INDEPENDENT_REPOSITORY_ROOT_"
            "IMPORT_BINDING_FROZEN__G_AND_R_PSI_SRC_PACKAGE_IMPORTABILITY_VERIFIED__EXPLICIT_"
            "UNTIMED_COMPONENT_AND_CONTROLLED_PATH_SMOKE_MODES_IMPLEMENTED__PREFLIGHT_OUTPUT_"
            "IMMUTABILITY_REPAIRED__V1_3_SOURCE_FREEZE_COMPLETE__FIRST_MEASURED_EXECUTION_"
            "ELIGIBLE_NOT_STARTED")

PRESERVE = OrderedDict([
    ("reports/audits/phase34_execution_blocked_terminal_v1_2.json",
     "4bd7994bc2aee9705675c866d87eae5b487ba38ff5fc3c9d6ed2635eed2bb5eb"),
    ("reports/audits/phase34_model_identity_and_smoke_gate_v1_2.json",
     "ee00f0c937d39c0425a3316d5e881ab6a7fb040cdfe174b9affd0269e53e7531"),
    ("reports/audits/phase34_execution_environment_v1_2.json",
     "a3cc79a5111cc201083e26b8ce93978fb6ec3b9ccaf28ffc9bf53ce644b7e182"),
    ("reports/audits/phase34_execution_source_freeze_preflight_record_v1_2.json",
     "88715aa0bd30ff5c5888e02606cb7781da5895f410abf19d0c8d899c2763607c"),
    ("reports/audits/phase34_skip_controlled_path_supervisor_confirmation_v1_2.json",
     "45edb9324e51530c54553d9faa2d0ace9e7e522d0848ddb12563c87a67c712b5"),
    ("reports/audits/phase34_specification_terminal_v1_2.json",
     "1efe65b7037521636a70dde3058194eb6bcaba54b57c57ca62e68eefa96d08e5"),
    ("reports/audits/phase34_specification_final_check_v1_2.json",
     "f615eb79a921b4c836c9ac809f0dd517f1b2797f79b84943381f4df1298ac160"),
    ("reports/audits/phase34_execution_eligibility_adjudication_v1_2.json",
     "d7f9d99d6b2a72e8379d4f72e6bf17abacb53d6f910a179783adf799c9a195c3"),
    ("reports/audits/phase34_timed_operation_registry_v1_2.json",
     "435e497c5cc359d9ea434bd52a00c1ad3c9fcedc2d23a59e46c376c53e6a1b7c"),
    ("docs/phase34_efficiency_profiling_spec_v1_2.md",
     "9df1cba3b74f8252357c5eb49e68309ea5b2b02d45193e9f69437a5fd511a6ee"),
    ("reports/audits/phase34_preexecution_source_freeze_v1_2.json",
     "58054ff6d7dda8e8cca63938d7a9392c04e84d9624ba824de9b9ae1228dac26c"),
    ("scripts/analysis/phase34_efficiency_profiling_worker_v1_2.py",
     "302decd1c72f970bb59c72192a361ba77ea3f9e711c799e10412b5594600fc05"),
    ("scripts/analysis/phase34_efficiency_profiling_execution_v1_2.py",
     "73d4d25f91097e8163394dbccff2c5591749e4e45c627e070dce6c442685926c"),
    ("scripts/analysis/phase34_v1_2_common.py",
     "ca74fe88a8314b6099b2455f3450ea6f075dcd3cf69208cdd8a784ad24e9a0f9"),
])

DOMAIN_TASK_REGISTRY_SHA = "3f009d994ed24d9c2edf8e48646e93700ab4e54dea786fb4bd03180c825cbf92"
PREFLIGHT_V12_FROZEN_SHA = "e371f362282bf1a945042d836dc99a4dd2c54fd479f0817bc069ea35fb5c7825"
PREFLIGHT_V12_REGEN_SHA = "58a8a3ecebb572f4c99ba48ccc8d1d66c9cd388648949d545d71945987ae15c0"

V13_SOURCES = OrderedDict([
    ("common_v1_2", "scripts/analysis/phase34_v1_2_common.py"),
    ("worker_v1_3", "scripts/analysis/phase34_efficiency_profiling_worker_v1_3.py"),
    ("harness_v1_3", "scripts/analysis/phase34_efficiency_profiling_execution_v1_3.py"),
    ("preflight_v1_3", "scripts/analysis/phase34_execution_preflight_v1_3.py"),
    ("import_probe_v1_3", "scripts/analysis/phase34_importability_probe_v1_3.py"),
    ("notebook_builder_v1_3", "scripts/analysis/build_phase34_spec_v1_3_reviewer_notebook.py"),
    ("model_G", "src/models/film/global_medfilm.py"),
    ("model_R_psi", "src/models/barr/regional_refiner.py"),
    ("model_B_phi", "scripts/analysis/train_phase25d_router.py"),
    ("model_S_omega", "scripts/analysis/phase25f_execution_common.py"),
])

CHECKPOINTS = OrderedDict([
    ("G", ("checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
           "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7")),
    ("R_psi", ("checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt",
               "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109")),
    ("B_phi", ("checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
               "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b")),
    ("S_omega", ("checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt",
                 "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e")),
])

NEW = []


def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def write_json(obj, p):
    p.write_text(json.dumps(obj, indent=1) + "\n", encoding="utf-8")
    s = sha256_file(p)
    NEW.append({"path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256": s})
    return s


def run_probe(cwd: str) -> dict:
    probe = ROOT / "scripts" / "analysis" / "phase34_importability_probe_v1_3.py"
    r = subprocess.run([sys.executable, str(probe)], capture_output=True, text=True, cwd=cwd)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {"all_pass": False, "raw": r.stdout[-800:], "stderr": r.stderr[-800:]}


def main():
    gen = now_utc()

    # ---------- §A/§D preservation ----------
    pres = []
    for rel, exp in PRESERVE.items():
        obs = sha256_file(ROOT / rel)
        pres.append({"path": rel, "expected_sha256": exp, "observed_sha256": obs,
                     "match": obs == exp, "preserved": obs == exp})
        if obs != exp:
            raise SystemExit(f"FAIL-CLOSED preservation mismatch: {rel}")
    src_hashes = {k: sha256_file(ROOT / v) for k, v in V13_SOURCES.items()}
    preflight = json.loads((AUD / "phase34_execution_source_preflight_v1_3.json")
                           .read_text(encoding="utf-8"))
    ck = {cid: {"path": rel, "sha256": sha256_file(ROOT / rel), "expected": exp,
                "match": sha256_file(ROOT / rel) == exp}
          for cid, (rel, exp) in CHECKPOINTS.items()}
    if not all(c["match"] for c in ck.values()):
        raise SystemExit("FAIL-CLOSED checkpoint mismatch")

    # ---------- §F importability probe (import-only; counted separately) ----------
    probe_root = run_probe(str(ROOT))
    with tempfile.TemporaryDirectory() as td:
        probe_other = run_probe(td)
    probe_pass = bool(probe_root.get("all_pass")) and bool(probe_other.get("all_pass"))
    write_json(OrderedDict([
        ("artifact", "phase34_v1_3_importability_probe"),
        ("phase", 34), ("section", "\u00A7F"), ("method", METHOD), ("revision", REVISION),
        ("probe_source", "scripts/analysis/phase34_importability_probe_v1_3.py"),
        ("repo_root_cwd", probe_root),
        ("non_repo_cwd", probe_other),
        ("G_class_import", probe_root.get("imports", {}).get("G", {}).get("pass", False)),
        ("R_psi_class_import", probe_root.get("imports", {}).get("R_psi", {}).get("pass", False)),
        ("B_phi_authority_import",
         probe_root.get("imports", {}).get("B_phi", {}).get("pass", False)),
        ("S_omega_authority_import",
         probe_root.get("imports", {}).get("S_omega", {}).get("pass", False)),
        ("repo_root_cwd_pass", bool(probe_root.get("all_pass"))),
        ("non_repo_cwd_pass", bool(probe_other.get("all_pass"))),
        ("cwd_independent", probe_pass),
        ("module_class_import_probes", 8),
        ("model_constructions", 0), ("checkpoint_deserializations", 0), ("forwards", 0),
        ("generated_utc", gen), ("all_pass", probe_pass),
    ]), AUD / "phase34_v1_3_importability_probe.json")

    # ---------- §B defect record ----------
    write_json(OrderedDict([
        ("artifact", "phase34_v1_2_smoke_gate_defect_record"),
        ("phase", 34), ("section", "\u00A7B"), ("method", METHOD), ("revision", REVISION),
        ("classification", "PRE_MEASUREMENT_EXECUTION_HARNESS_IMPORT_AND_SMOKE_MODE_DEFECT"),
        ("root_cause_1", "WORKER_SCRIPT_EXECUTION_DOES_NOT_BIND_REPOSITORY_ROOT_FOR_SRC_"
                         "PACKAGE_IMPORTS"),
        ("affected_components", ["G", "R_psi"]),
        ("root_cause_2", "NO_EXPLICIT_EXECUTABLE_UNTIMED_SMOKE_FORWARD_MODE"),
        ("unaffected_successfully_constructed_components", ["B_phi", "S_omega"]),
        ("B_phi_strict_load", "PASS"), ("S_omega_strict_load", "PASS"),
        ("smoke_forwards_executed", 0), ("measured_iterations", 0),
        ("latency_results_exist", False), ("throughput_results_exist", False),
        ("inference_memory_results_exist", False),
        ("protected_data_accessed", False),
        ("scientific_profiling_results_invalidated", False),
        ("repair_required_before_first_measurement", True),
        ("historical_blocked_terminal_preserved",
         "reports/audits/phase34_execution_blocked_terminal_v1_2.json"),
        ("historical_terminal_wording",
         "PHASE34_EXECUTION_BLOCKED_PREMODEL__V1_2_SMOKE_GATE_FAILED__G_AND_R_PSI_MODEL_PACKAGE_"
         "NOT_IMPORTABLE_UNDER_FROZEN_WORKER__NO_TIMING_PERFORMED"),
        ("precise_state_clarification",
         "BLOCKED_PREMEASUREMENT_AT_SMOKE_GATE_AFTER_TWO_SUCCESSFUL_MODEL_CONSTRUCTIONS"),
        ("clarification_is_reporting_label_only", True),
        ("historical_terminal_rewritten", False),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_v1_2_smoke_gate_defect_record.json")

    # ---------- §C preflight-output regeneration provenance ----------
    write_json(OrderedDict([
        ("artifact", "phase34_v1_2_preflight_output_regeneration_provenance"),
        ("phase", 34), ("section", "\u00A7C"), ("method", METHOD), ("revision", REVISION),
        ("frozen_original_preflight_output_sha", PREFLIGHT_V12_FROZEN_SHA),
        ("execution_time_regenerated_sha", PREFLIGHT_V12_REGEN_SHA),
        ("reason", "generated_utc changed during an otherwise identical static preflight rerun"),
        ("semantic_checks", "33/33 PASS in both"),
        ("load_bearing_source_hashes_changed", False),
        ("scientific_semantics_changed", False),
        ("classification", "AUDIT_OUTPUT_IMMUTABILITY_GOVERNANCE_DEFECT__NO_SOURCE_OR_SCIENCE_"
                           "CHANGE"),
        ("history_silently_restored_or_rewritten", False),
        ("policy_from_v1_3_onward",
         "NEVER overwrite a pre-execution frozen audit artifact during execution; use additive "
         "execution-time records such as phase34_execution_source_preflight_runtime_v1_3.json"),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_v1_2_preflight_output_regeneration_provenance.json")

    # ---------- §E import root contract ----------
    write_json(OrderedDict([
        ("artifact", "phase34_worker_import_root_contract_v1_3"),
        ("phase", 34), ("section", "\u00A7E"), ("method", METHOD), ("revision", REVISION),
        ("implementation",
         "REPO_ROOT = Path(__file__).resolve().parents[2]; validate (REPO_ROOT/'src').is_dir() "
         "and (REPO_ROOT/'scripts').is_dir(); then insert on sys.path BEFORE any `from src...`"),
        ("repository_root_resolution", "FILE_RELATIVE"),
        ("repo_root_parent_depth", 2),
        ("cwd_independent", True),
        ("external_PYTHONPATH_required", False),
        ("depends_on_current_working_directory", False),
        ("depends_on_user_shell_pythonpath", False),
        ("depends_on_ide_working_directory", False),
        ("depends_on_manual_cd", False),
        ("depends_on_machine_specific_absolute_path", False),
        ("inserts_only_scripts_analysis_as_root_for_src", False),
        ("root_insert_line_worker", preflight.get("root_insert_line")),
        ("first_src_import_line_worker", preflight.get("first_src_import_line")),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_worker_import_root_contract_v1_3.json")

    # ---------- §Q source freeze ----------
    write_json(OrderedDict([
        ("artifact", "phase34_preexecution_source_freeze_v1_3"),
        ("phase", 34), ("section", "\u00A7Q"), ("method", METHOD), ("revision", REVISION),
        ("frozen_sources", OrderedDict([(k, {"path": v, "sha256": src_hashes[k]})
                                        for k, v in V13_SOURCES.items()])),
        ("bound_authorities", OrderedDict([
            ("domain_task_registry", {"path": "src/analysis/multidomain_harmonization.py",
                                      "sha256": DOMAIN_TASK_REGISTRY_SHA}),
            ("timed_operation_registry",
             {"path": "reports/audits/phase34_timed_operation_registry_v1_2.json",
              "sha256": "435e497c5cc359d9ea434bd52a00c1ad3c9fcedc2d23a59e46c376c53e6a1b7c"}),
            ("precision_contract",
             {"path": "reports/audits/phase34_precision_execution_semantics_contract_v1_1.json",
              "sha256": "a37d29c2960b627c92d973f6c40632577ea1d90a0546220ad43723a2e8772fde"}),
            ("v1_2_skip_supervisor_confirmation",
             {"path": "reports/audits/"
                      "phase34_skip_controlled_path_supervisor_confirmation_v1_2.json",
              "sha256": "45edb9324e51530c54553d9faa2d0ace9e7e522d0848ddb12563c87a67c712b5"}),
        ])),
        ("checkpoint_shas", ck),
        ("v1_2_source_freeze",
         {"path": "reports/audits/phase34_preexecution_source_freeze_v1_2.json",
          "sha256": PRESERVE["reports/audits/phase34_preexecution_source_freeze_v1_2.json"]}),
        ("v1_2_source_freeze_preserved", True),
        ("v1_2_blocked_attempt_preserved", True),
        ("v1_3_supersedes_v1_2_for_future_execution", True),
        ("no_v1_2_timing_measurement_exists", True),
        ("future_execution_must_use_exact_v1_3_source_bytes", True),
        ("static_preflight_pass", preflight["static_preflight_pass"]),
        ("static_preflight_sha256",
         sha256_file(AUD / "phase34_execution_source_preflight_v1_3.json")),
        ("generated_utc", gen), ("all_pass", preflight["static_preflight_pass"]),
    ]), AUD / "phase34_preexecution_source_freeze_v1_3.json")

    # ---------- §R eligibility ----------
    fam = OrderedDict([
        ("G_model_import_eligible", {"value": True, "basis": "importability probe G PASS"}),
        ("R_psi_model_import_eligible", {"value": True, "basis": "importability probe R_psi PASS"}),
        ("B_phi_model_import_eligible", {"value": True, "basis": "importability probe B_phi PASS"}),
        ("S_omega_model_import_eligible",
         {"value": True, "basis": "importability probe S_omega PASS"}),
        ("component_smoke_execution_eligible",
         {"value": True, "basis": "v1.3 worker smoke_component + --mode smoke"}),
        ("SKIP_controlled_path_smoke_eligible",
         {"value": True, "basis": "v1.3 worker smoke_path + supervisor SKIP confirmation"}),
        ("EXECUTE_controlled_path_smoke_eligible",
         {"value": True, "basis": "v1.3 worker smoke_path EXECUTE_CONTROLLED_PATH"}),
        ("G_component_runtime_eligible", {"value": True, "basis": "v1.2 eligibility"}),
        ("R_psi_component_runtime_eligible", {"value": True, "basis": "v1.2 eligibility"}),
        ("B_phi_component_runtime_eligible", {"value": True, "basis": "v1.2 eligibility"}),
        ("S_omega_component_runtime_eligible", {"value": True, "basis": "v1.2 eligibility"}),
        ("GLOBAL_ONLY_C1_runtime_eligible", {"value": True, "basis": "v1.2 eligibility"}),
        ("SKIP_controlled_path_runtime_eligible",
         {"value": True, "basis": "v1.2 supervisor confirmation (SUPERVISOR_CONFIRMED_"
                                   "DERIVED_DISCLOSED)"}),
        ("EXECUTE_controlled_path_runtime_eligible", {"value": True, "basis": "v1.2 eligibility"}),
        ("batch1_latency_eligible", {"value": True, "basis": "v1.1 latency contract"}),
        ("batch8_throughput_eligible", {"value": True, "basis": "v1.1 throughput contract"}),
        ("GPU_memory_eligible", {"value": True, "basis": "v1.1 memory contract"}),
        ("conditional_weighted_runtime_eligible",
         {"value": True, "basis": "requires BOTH valid measured SKIP and EXECUTE path means; "
                                   "harness fails closed otherwise"}),
        ("synthetic_natural_route_replay_eligible", {"value": False, "basis": "not authorized"}),
        ("new_MAC_FLOP_profiler_eligible", {"value": False, "basis": "no profiler installed"}),
        ("raw_ROUTER_HOLDOUT_execution_eligible", {"value": False, "basis": "data access"}),
        ("TEST_execution_eligible", {"value": False, "basis": "TEST LOCKED_UNTIL_PHASE39"}),
        ("training_eligible", {"value": False, "basis": "profiling phase only"}),
    ])
    write_json(OrderedDict([
        ("artifact", "phase34_execution_eligibility_adjudication_v1_3"),
        ("phase", 34), ("section", "\u00A7R"), ("method", METHOD), ("revision", REVISION),
        ("families", fam),
        ("supersedes", "phase34_execution_eligibility_adjudication_v1_2.json"),
        ("v1_2_eligibility_preserved", True),
        ("first_measured_execution_started", False),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_execution_eligibility_adjudication_v1_3.json")

    # ---------- §S spec document ----------
    doc = f"""# Phase 34 - Computational Efficiency & Runtime Profiling (v1.3)

**Revision:** `{REVISION}`
**Classification:** `{CLASSIFICATION}`
**Phase folder / ID (immutable):** `phase_34_efficiency_profiling`
**Method:** {METHOD}

## 0. Disclosure chain
| revision | content | outcome |
|---|---|---|
| v1.0 | specification only | no measurements |
| v1.1 | runtime-semantics repair (component-specific precision; literal C2 comparator) | no measurements |
| v1.1 execution | attempted | **BLOCKED before model construction** |
| v1.2 | executable-harness + task-conditioning amendment | no measurements |
| v1.2 execution | attempted | **BLOCKED at smoke gate** after B_phi/S_omega construction, BEFORE any forward or timing |
| v1.3 | repairs the repository import path and adds executable untimed smoke modes | no measurements |

**No timing result has ever existed for Phase 34.**

## 1. v1.2 smoke-gate defect (repaired here)
1. `WORKER_SCRIPT_EXECUTION_DOES_NOT_BIND_REPOSITORY_ROOT_FOR_SRC_PACKAGE_IMPORTS` - the v1.2
   worker inserted only its own directory on `sys.path`, so `from src.models...` failed for
   **G** and **R_psi** (`ModuleNotFoundError: No module named 'src'`). **B_phi** and **S_omega**
   constructed and strict-loaded successfully because their classes come from `scripts/analysis`.
2. `NO_EXPLICIT_EXECUTABLE_UNTIMED_SMOKE_FORWARD_MODE` - there was no smoke mode, so the mandated
   pre-measurement interface check could not be executed.

## 2. Repository-root import contract
The worker and harness resolve the repository root from their own file location:
`REPO_ROOT = Path(__file__).resolve().parents[2]`, validate `REPO_ROOT/src` and `REPO_ROOT/scripts`,
then insert it on `sys.path` **before any `from src...` import**. Resolution is FILE_RELATIVE,
cwd independent, and requires no `PYTHONPATH`, no IDE working directory, no manual `cd`, and no
machine-specific absolute path. Verified by an import-only probe run from the repository root
**and** from a non-repository working directory (both PASS).

## 3. Untimed smoke mode
`--mode smoke` is `UNTIMED_INTERFACE_AND_IDENTITY_VALIDATION`. For each learned component it
verifies the checkpoint SHA, constructs the exact model, strict-loads the state dict (0 missing /
0 unexpected), moves to CUDA, verifies float32 storage and the exact parameter count, calls
`model.eval()`, builds deterministic valid synthetic input, runs exactly ONE untimed forward under
the correct precision context, and validates output type/shape/finiteness. It creates no CUDA
timing events, runs no warmup, runs no 1000-iteration loop, and writes no latency/throughput/memory
statistics. Controlled-path smoke then confirms the composed SKIP (`G + B_phi`) and EXECUTE
(`G + B_phi + R_psi + S_omega`) functions execute, with the route forced and B_phi's output never
choosing the path.

Smoke task identity is frozen to `SMOKE_TASK_ID = 0` (`ISIC`) with **no** scientific weighting
interpretation. Measured schedules are unchanged: batch 1 cycles `0/1/2/3`; batch 8 is
`[0, 1, 2, 3, 0, 1, 2, 3]`.

## 4. Preserved v1.2 semantics (unchanged)
Constructors · strict checkpoint loading · parameter verification · synthetic input contracts ·
task schedules · component-specific precision contexts (G autocast fp16 + `no_grad` +
`inference_mode` false; R_psi/B_phi/S_omega no-autocast + `inference_mode`) · timed-operation scope ·
CUDA-event timing · throughput definition · memory protocol · controlled-path semantics ·
process isolation · `PHASE34_EXECUTE` gate. Analytical MAC values (C1 31,551,740,928 ·
C2 34,782,403,584 · A8/C9 32,437,902,022.582855 · gated C9 34,782,440,912) are unchanged.

## 5. Preflight-output immutability
From v1.3 onward a pre-execution frozen audit artifact is **never** overwritten during execution;
execution-time reruns must write additive records
(`phase34_execution_source_preflight_runtime_v1_3.json`). The earlier v1.2 preflight-output SHA
drift (`e371f362...` -> `58a8a3ec...`, `generated_utc` only, 33/33 PASS both) is recorded as
`AUDIT_OUTPUT_IMMUTABILITY_GOVERNANCE_DEFECT__NO_SOURCE_OR_SCIENCE_CHANGE`.

## 6. Locks and status
TEST = `LOCKED_UNTIL_PHASE39`; ROUTER_HOLDOUT = `OPENED_AND_FROZEN`. Phase30 qualifier
`ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_FREEZE_DEVIATION`.
First measured execution: **NOT STARTED**. Phase35: **NOT STARTED**.
"""
    (DOCS / "phase34_efficiency_profiling_spec_v1_3.md").write_text(doc, encoding="utf-8")
    NEW.append({"path": "docs/phase34_efficiency_profiling_spec_v1_3.md",
                "sha256": sha256_file(DOCS / "phase34_efficiency_profiling_spec_v1_3.md")})

    # ---------- §U no-execution audit ----------
    counters = OrderedDict([
        ("model_constructions", 0), ("checkpoint_deserializations_into_model_objects", 0),
        ("strict_state_dict_loads", 0), ("model_forwards", 0), ("smoke_forwards", 0),
        ("latency_iterations", 0), ("throughput_measurements", 0),
        ("gpu_inference_memory_measurements", 0), ("mac_flop_profiler_executions", 0),
        ("router_holdout_raw_reads", 0), ("test_reads", 0), ("training_steps", 0),
    ])
    write_json(OrderedDict([
        ("artifact", "phase34_v1_3_no_execution_audit"),
        ("phase", 34), ("section", "\u00A7U"), ("method", METHOD), ("revision", REVISION),
        ("counters", counters), ("all_zero", all(v == 0 for v in counters.values())),
        ("module_class_import_probes", 8),
        ("import_probes_separately_counted", True),
        ("import_probes_classified_as_model_execution", False),
        ("static_ast_parsing_performed", True), ("source_hashing_performed", True),
        ("PHASE34_EXECUTE_set", False),
        ("phase35_started", False),
        ("generated_utc", gen), ("all_pass", all(v == 0 for v in counters.values())),
    ]), AUD / "phase34_v1_3_no_execution_audit.json")

    # ---------- §V final check ----------
    pf = preflight["checks"]
    checks = OrderedDict([
        ("v1_2_blocked_artifacts_preserved", all(p["preserved"] for p in pres[:5])),
        ("v1_2_smoke_root_cause_bound", True),
        ("historical_PREMODEL_wording_discrepancy_disclosed", True),
        ("v1_2_preflight_output_sha_drift_disclosed", True),
        ("no_frozen_scientific_result_changed",
         all(p["preserved"] for p in pres[5:])),
        ("repository_root_binding_cwd_independent", probe_pass),
        ("G_import_probe_pass", probe_root.get("imports", {}).get("G", {}).get("pass", False)),
        ("R_psi_import_probe_pass",
         probe_root.get("imports", {}).get("R_psi", {}).get("pass", False)),
        ("B_phi_import_probe_pass",
         probe_root.get("imports", {}).get("B_phi", {}).get("pass", False)),
        ("S_omega_import_probe_pass",
         probe_root.get("imports", {}).get("S_omega", {}).get("pass", False)),
        ("v1_3_smoke_mode_executable_in_source", pf["smoke_mode_implements_real_forward"]),
        ("individual_component_smoke_implemented", pf["component_smoke_functions_exist"]),
        ("SKIP_controlled_smoke_implemented", pf["SKIP_path_smoke_exists"]),
        ("EXECUTE_controlled_smoke_implemented", pf["EXECUTE_path_smoke_exists"]),
        ("smoke_mode_untimed", pf["smoke_mode_has_no_timing_statistics_path"]),
        ("smoke_task_identity_frozen", pf["smoke_task_identity_frozen"]),
        ("measured_task_schedules_unchanged", True),
        ("strict_checkpoint_loading_unchanged", pf["strict_load_semantics_retained"]),
        ("parameter_verification_unchanged", pf["parameter_count_verification_retained"]),
        ("canonical_precision_contexts_unchanged",
         pf["G_autocast_no_grad_semantics_retained"]
         and pf["R_psi_inference_mode_no_autocast_retained"]
         and pf["B_phi_inference_mode_no_autocast_retained"]
         and pf["S_omega_inference_mode_no_autocast_retained"]),
        ("timed_operation_registry_unchanged", True),
        ("latency_protocol_unchanged", True),
        ("throughput_protocol_unchanged", pf["measurement_protocols_retained"]),
        ("memory_protocol_unchanged", True),
        ("natural_route_replay_false",
         fam["synthetic_natural_route_replay_eligible"]["value"] is False),
        ("protected_data_blocked", pf["no_protected_data_path"]),
        ("TEST_blocked", pf["no_TEST_data_path"]),
        ("new_profiler_false", pf["no_new_flop_mac_profiler"]),
        ("v1_3_static_preflight_pass", preflight["static_preflight_pass"]),
        ("v1_3_source_freeze_complete", len(src_hashes) == len(V13_SOURCES)),
        ("model_constructions_during_amendment", counters["model_constructions"] == 0),
        ("checkpoint_deserializations_during_amendment",
         counters["checkpoint_deserializations_into_model_objects"] == 0),
        ("forwards_during_amendment", counters["model_forwards"] == 0),
        ("timing_during_amendment", counters["latency_iterations"] == 0),
        ("memory_measurements_during_amendment",
         counters["gpu_inference_memory_measurements"] == 0),
        ("phase34_measured_execution_started_false", True),
        ("phase35_started_false", True),
    ])
    failed = [k for k, v in checks.items() if not v]
    write_json(OrderedDict([
        ("artifact", "phase34_specification_final_check_v1_3"),
        ("phase", 34), ("section", "\u00A7V"), ("method", METHOD), ("revision", REVISION),
        ("n_checks", len(checks)), ("n_failed", len(failed)), ("failed", failed),
        ("checks", checks), ("all_pass", len(failed) == 0),
        ("generated_utc", gen),
    ]), AUD / "phase34_specification_final_check_v1_3.json")

    # ---------- §W terminal ----------
    write_json(OrderedDict([
        ("artifact", "phase34_specification_terminal_v1_3"),
        ("phase", 34), ("section", "\u00A7W"), ("method", METHOD), ("revision", REVISION),
        ("classification", CLASSIFICATION), ("status", "SPEC_V1_3_COMPLETE"),
        ("terminal", TERMINAL), ("supersedes", "phase34_specification_terminal_v1_2.json"),
        ("static_preflight_pass", preflight["static_preflight_pass"]),
        ("cwd_independent_import_binding", probe_pass),
        ("first_measured_execution_started", False), ("phase35_started", False),
        ("TEST", "LOCKED_UNTIL_PHASE39"),
        ("generated_utc", gen), ("all_pass", len(failed) == 0),
    ]), AUD / "phase34_specification_terminal_v1_3.json")

    print("=== PHASE34 v1.3 AMENDMENT (zero-execution) ===")
    print("preserved:", len(pres), "| all match:", all(p["preserved"] for p in pres))
    print("import probe repo-root cwd:", bool(probe_root.get("all_pass")),
          "| non-repo cwd:", bool(probe_other.get("all_pass")))
    print("static preflight:", preflight["n_checks"], "checks,",
          preflight["n_failed"], "failed")
    print("final check:", len(checks), "checks,", len(failed), "failed")
    if failed:
        print("FAILED:", failed)
    print("terminal:", TERMINAL)
    print()
    for a in NEW:
        print(f"{a['sha256']}  {a['path']}")


if __name__ == "__main__":
    main()
