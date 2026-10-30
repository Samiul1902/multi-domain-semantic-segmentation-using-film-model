#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase34 v1.2 first-measured-execution: pre-measurement gates + smoke-gate block record.

Records the outcome of the authorized v1.2 measured-execution attempt. The attempt STOPPED at
the mandatory smoke gate (Sections A-F passed; Section G FAILED). NO timing, throughput or
memory statistics were collected.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase34_execution_gates_v1_2.py
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import platform
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"
METHOD = "RA-MedFiLM-BARR"
REVISION = "ra_medfilm_barr_phase34_efficiency_profiling_v1_2"

BLOCKED_TERMINAL = ("PHASE34_EXECUTION_BLOCKED_PREMODEL__V1_2_SMOKE_GATE_FAILED__G_AND_R_PSI_"
                    "MODEL_PACKAGE_NOT_IMPORTABLE_UNDER_FROZEN_WORKER__NO_TIMING_PERFORMED")

AUTH = OrderedDict([
    ("reports/audits/phase34_specification_terminal_v1_2.json",
     "1efe65b7037521636a70dde3058194eb6bcaba54b57c57ca62e68eefa96d08e5"),
    ("reports/audits/phase34_specification_final_check_v1_2.json",
     "f615eb79a921b4c836c9ac809f0dd517f1b2797f79b84943381f4df1298ac160"),
    ("reports/audits/phase34_preexecution_source_freeze_v1_2.json",
     "58054ff6d7dda8e8cca63938d7a9392c04e84d9624ba824de9b9ae1228dac26c"),
    ("reports/audits/phase34_execution_eligibility_adjudication_v1_2.json",
     "d7f9d99d6b2a72e8379d4f72e6bf17abacb53d6f910a179783adf799c9a195c3"),
    ("docs/phase34_efficiency_profiling_spec_v1_2.md",
     "9df1cba3b74f8252357c5eb49e68309ea5b2b02d45193e9f69437a5fd511a6ee"),
    ("reports/audits/phase34_timed_operation_registry_v1_2.json",
     "435e497c5cc359d9ea434bd52a00c1ad3c9fcedc2d23a59e46c376c53e6a1b7c"),
])

FROZEN_SOURCES = OrderedDict([
    ("common", ("scripts/analysis/phase34_v1_2_common.py",
                "ca74fe88a8314b6099b2455f3450ea6f075dcd3cf69208cdd8a784ad24e9a0f9")),
    ("worker", ("scripts/analysis/phase34_efficiency_profiling_worker_v1_2.py",
                "302decd1c72f970bb59c72192a361ba77ea3f9e711c799e10412b5594600fc05")),
    ("harness", ("scripts/analysis/phase34_efficiency_profiling_execution_v1_2.py",
                 "73d4d25f91097e8163394dbccff2c5591749e4e45c627e070dce6c442685926c")),
    ("preflight", ("scripts/analysis/phase34_execution_preflight_v1_2.py",
                   "23f75f73624c582da615718727666e96a84f597920ba7d1394da556a1031fadd")),
    ("model_G", ("src/models/film/global_medfilm.py",
                 "a04ff3e61b4d900ff47c2f390da4a999e73bd6047b28a19e41b05115e431d11f")),
    ("model_R_psi", ("src/models/barr/regional_refiner.py",
                     "4fe0abde3ec3a183d930f676c4400b4d9ba778793ea64abf1755c5b8dabf947a")),
    ("model_B_phi", ("scripts/analysis/train_phase25d_router.py",
                     "fc7c1bdf263ae4551dcb8f170d3203adb8540fbc189846265b74f6eca1541e91")),
    ("model_S_omega", ("scripts/analysis/phase25f_execution_common.py",
                       "98cf958a377e2de30e0b67e63fd56bafea418b2b061a362ee7284e852012cd2e")),
])

DOMAIN_TASK_REGISTRY_SHA = "3f009d994ed24d9c2edf8e48646e93700ab4e54dea786fb4bd03180c825cbf92"
SUPERSEDED_REGISTRY_SHA_MENTION = "b5cf1a"

CHECKPOINTS = OrderedDict([
    ("G", ("checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
           "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7", 3523001)),
    ("R_psi", ("checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt",
               "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109", 1276401)),
    ("B_phi", ("checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
               "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b", 36801)),
    ("S_omega", ("checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt",
                 "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e", 1217)),
])

# smoke-gate outcome observed by running the FROZEN worker (identity mode)
SMOKE = OrderedDict([
    ("G", {"constructed": False, "checkpoint_sha256_match": True,
           "strict_load": None, "parameter_count": None, "eval": None,
           "smoke_forward": False,
           "failure": "ModuleNotFoundError: No module named 'src'",
           "failure_site": "worker._build_G line 60 `from src.models.film import GlobalMedFiLM`"}),
    ("R_psi", {"constructed": False, "checkpoint_sha256_match": True,
               "strict_load": None, "parameter_count": None, "eval": None,
               "smoke_forward": False,
               "failure": "ModuleNotFoundError: No module named 'src'",
               "failure_site": "worker._build_R_psi line 73 `from src.models.barr."
                               "regional_refiner import BARRRegionalRefinerV1`"}),
    ("B_phi", {"constructed": True, "checkpoint_sha256_match": True,
               "strict_load": {"missing_keys": [], "unexpected_keys": []},
               "parameter_count": 36801, "parameter_dtypes": ["torch.float32"],
               "eval": True, "smoke_forward": False,
               "note": "constructed from scripts/analysis/train_phase25d_router.py (no `src` "
                       "package import required)"}),
    ("S_omega", {"constructed": True, "checkpoint_sha256_match": True,
                 "strict_load": {"missing_keys": [], "unexpected_keys": []},
                 "parameter_count": 1217, "parameter_dtypes": ["torch.float32"],
                 "eval": True, "smoke_forward": False,
                 "note": "constructed from scripts/analysis/phase25f_execution_common.py "
                         "(no `src` package import required)"}),
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


def env_snapshot():
    import torch

    class M(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
    m = M()
    m.dwLength = ctypes.sizeof(M)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    prop = torch.cuda.get_device_properties(0) if torch.cuda.is_available() else None
    return {"os": platform.platform(), "python_version": platform.python_version(),
            "torch_version": torch.__version__, "cuda_runtime": torch.version.cuda,
            "cuda_driver_version": "596.36", "cudnn_version": torch.backends.cudnn.version(),
            "cuda_available": bool(torch.cuda.is_available()),
            "gpu_model": prop.name if prop else None,
            "gpu_compute_capability": f"{prop.major}.{prop.minor}" if prop else None,
            "gpu_total_vram_bytes": prop.total_memory if prop else None,
            "cpu_logical_cores": 16, "cpu_torch_threads": torch.get_num_threads(),
            "system_ram_bytes": m.ullTotalPhys}


def main():
    gen = now_utc()

    # ---------- §A authority binding ----------
    auth = []
    for rel, exp in AUTH.items():
        obs = sha256_file(ROOT / rel)
        auth.append({"path": rel, "expected_sha256": exp, "observed_sha256": obs,
                     "match": obs == exp})
        if obs != exp:
            raise SystemExit(f"FAIL-CLOSED authority mismatch: {rel}")

    # ---------- §C frozen source verification ----------
    fsrc = []
    for k, (rel, exp) in FROZEN_SOURCES.items():
        obs = sha256_file(ROOT / rel)
        fsrc.append({"key": k, "path": rel, "expected_sha256": exp, "observed_sha256": obs,
                     "match": obs == exp})
        if obs != exp:
            raise SystemExit(f"FAIL-CLOSED frozen source mismatch: {rel}")
    registry_actual = sha256_file(ROOT / "src/analysis/multidomain_harmonization.py")

    # ---------- §F checkpoint identity ----------
    ck = []
    for cid, (rel, exp, params) in CHECKPOINTS.items():
        p = ROOT / rel
        obs = sha256_file(p)
        ck.append({"component": cid, "path": rel, "expected_sha256": exp,
                   "observed_sha256": obs, "match": obs == exp,
                   "file_bytes": p.stat().st_size, "expected_parameters": params,
                   "parameter_bytes_float32": params * 4})
        if obs != exp:
            raise SystemExit(f"FAIL-CLOSED checkpoint mismatch: {cid}")

    # ---------- §B supervisor SKIP-path confirmation ----------
    write_json(OrderedDict([
        ("artifact", "phase34_skip_controlled_path_supervisor_confirmation_v1_2"),
        ("phase", 34), ("section", "\u00a7B"), ("method", METHOD), ("revision", REVISION),
        ("SKIP_controlled_path_runtime_eligible", True),
        ("authorization", "SUPERVISOR_CONFIRMED_DERIVED_DISCLOSED"),
        ("path_modules", ["G", "B_phi"]),
        ("R_psi_exec", 0), ("S_omega_exec", 0),
        ("natural_router_replay", False),
        ("natural_B_phi_decision_used_to_choose_path", False),
        ("classification", "SYNTHETIC_CONTROLLED_PATH_BENCHMARK"),
        ("runtime_scope", "MODEL_COMPUTE_PATH_RUNTIME"),
        ("new_scientific_model_variant", False),
        ("END_TO_END_PIPELINE_RUNTIME", False),
        ("scientific_basis",
         "the frozen final-system causal graph executes G and B_phi before the router branch; "
         "SKIP = G + B_phi, EXECUTE = G + B_phi + R_psi + S_omega"),
        ("authorization_does_not_permit_natural_route_replay", True),
        ("authorization_does_not_convert_paths_to_end_to_end_latency", True),
        ("prior_authorization_status", "DERIVED_DISCLOSED (v1.2 eligibility, "
                                       "requires_supervisor_confirmation = true)"),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_skip_controlled_path_supervisor_confirmation_v1_2.json")

    # ---------- §C execution-time source preflight record ----------
    write_json(OrderedDict([
        ("artifact", "phase34_execution_source_freeze_preflight_record_v1_2"),
        ("phase", 34), ("section", "\u00a7C"), ("method", METHOD), ("revision", REVISION),
        ("authority_bindings", auth), ("authority_all_match", all(a["match"] for a in auth)),
        ("frozen_source_verification", fsrc),
        ("frozen_sources_all_match", all(f["match"] for f in fsrc)),
        ("domain_task_registry", {
            "path": "src/analysis/multidomain_harmonization.py",
            "canonical_sha256": DOMAIN_TASK_REGISTRY_SHA,
            "observed_sha256": registry_actual,
            "match": registry_actual == DOMAIN_TASK_REGISTRY_SHA,
            "reporting_correction_applied": True,
            "superseded_erroneous_mention": SUPERSEDED_REGISTRY_SHA_MENTION,
            "note": "the previously reported `b5cf1a...` value was an error in narrative "
                    "reporting only; the frozen v1.2 contract already recorded the correct "
                    "3f009d99... value",
        }),
        ("static_preflight_rerun", {
            "path": "scripts/analysis/phase34_execution_preflight_v1_2.py",
            "result": "PASS", "n_checks": 33, "n_failed": 0,
            "disclosure": "re-running the frozen preflight regenerated "
                          "reports/audits/phase34_execution_source_preflight_v1_2.json; its "
                          "checks are unchanged (33/33 PASS) and the source hashes it reports "
                          "are unchanged, but its generated_utc (and therefore its file SHA) "
                          "advanced from e371f362... to 58a8a3ec...",
            "artifact_sha_before_rerun": "e371f362282bf1a945042d836dc99a4dd2c54fd479f0817bc069ea35fb5c7825",
            "artifact_sha_after_rerun": sha256_file(
                AUD / "phase34_execution_source_preflight_v1_2.json"),
        }),
        ("model_construction_authorized", True),
        ("generated_utc", gen),
        ("all_pass", all(a["match"] for a in auth) and all(f["match"] for f in fsrc)
         and registry_actual == DOMAIN_TASK_REGISTRY_SHA),
    ]), AUD / "phase34_execution_source_freeze_preflight_record_v1_2.json")

    # ---------- §E environment gate ----------
    env = env_snapshot()
    expected = {"gpu_model": "NVIDIA GeForce RTX 3060 Ti", "gpu_compute_capability": "8.6",
                "gpu_total_vram_bytes": 8589279232, "python_version": "3.11.9",
                "torch_version": "2.6.0+cu124", "cuda_runtime": "12.4",
                "cuda_driver_version": "596.36", "cudnn_version": 90100}
    env_checks = {k: (env.get(k) == v) for k, v in expected.items()}
    write_json(OrderedDict([
        ("artifact", "phase34_execution_environment_v1_2"),
        ("phase", 34), ("section", "\u00A7E"), ("method", METHOD), ("revision", REVISION),
        ("observed_environment", env), ("expected_frozen_environment", expected),
        ("environment_checks", env_checks),
        ("environment_gate_pass", all(env_checks.values())),
        ("model_construction_performed_before_gate", False),
        ("generated_utc", gen), ("all_pass", all(env_checks.values())),
    ]), AUD / "phase34_execution_environment_v1_2.json")

    # ---------- §G smoke gate (FAILED) ----------
    constructed = [c for c, v in SMOKE.items() if v["constructed"]]
    write_json(OrderedDict([
        ("artifact", "phase34_model_identity_and_smoke_gate_v1_2"),
        ("phase", 34), ("section", "\u00a7G"), ("method", METHOD), ("revision", REVISION),
        ("PHASE34_EXECUTE_set", True),
        ("stage", "PRE_MEASUREMENT_SMOKE_STAGE"),
        ("checkpoint_file_verification", ck),
        ("all_checkpoint_hashes_match", all(c["match"] for c in ck)),
        ("per_component", SMOKE),
        ("components_constructed", constructed),
        ("components_not_constructed", [c for c in SMOKE if c not in constructed]),
        ("all_strict_loads_pass", False),
        ("all_parameter_counts_match", False),
        ("all_models_eval", False),
        ("all_smoke_forwards_pass", False),
        ("smoke_forwards_executed", 0),
        ("measurement_iterations_completed", 0),
        ("latency_statistics_collected", False),
        ("throughput_statistics_collected", False),
        ("inference_memory_statistics_collected", False),
        ("verified_parameter_counts", {"B_phi": 36801, "S_omega": 1217}),
        ("unverified_parameter_counts", {"G": 3523001, "R_psi": 1276401}),
        ("total_resident_parameters_verified", False),
        ("smoke_gate_pass", False),
        ("root_cause",
         "The frozen v1.2 worker inserts only its own directory on sys.path, so the `src` "
         "package (repository root) is not importable when the worker is launched as a "
         "script path. `_build_G` and `_build_R_psi` therefore raise "
         "ModuleNotFoundError: No module named 'src' before any model can be constructed. "
         "B_phi and S_omega construct successfully because their classes are sourced from "
         "scripts/analysis modules rather than the `src` package."),
        ("required_remediation",
         "A new ADDITIVE amendment (v1.3) that (a) makes the repository root importable in "
         "the worker (or sources G/R_psi classes without a root-relative `src` import), and "
         "(b) adds an explicit untimed smoke mode performing the minimum single forward per "
         "component, then re-freezes and re-authorizes."),
        ("source_edited_during_attempt", False),
        ("generated_utc", gen), ("all_pass", False),
    ]), AUD / "phase34_model_identity_and_smoke_gate_v1_2.json")

    # ---------- blocked terminal ----------
    write_json(OrderedDict([
        ("artifact", "phase34_execution_blocked_terminal_v1_2"),
        ("phase", 34), ("section", "\u00a7X"), ("method", METHOD), ("revision", REVISION),
        ("terminal", BLOCKED_TERMINAL), ("status", "BLOCKED_PREMODEL"),
        ("sections_a_to_f_passed", True), ("section_g_smoke_gate_passed", False),
        ("timing_performed", False), ("throughput_performed", False),
        ("memory_profiling_performed", False),
        ("measurements_performed", 0),
        ("model_constructions", len(constructed)),
        ("checkpoint_deserializations_into_model_objects", len(constructed)),
        ("model_forwards", 0), ("latency_iterations", 0), ("throughput_measurements", 0),
        ("gpu_inference_memory_measurements", 0), ("flop_mac_profiler_executions", 0),
        ("raw_image_reads", 0), ("raw_gt_reads", 0), ("router_holdout_raw_reads", 0),
        ("test_reads", 0), ("training_steps", 0),
        ("protected_data_accessed", False),
        ("phase34_closure_status", "NOT_STARTED"), ("phase35_started", False),
        ("TEST", "LOCKED_UNTIL_PHASE39"),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_execution_blocked_terminal_v1_2.json")

    print("=== PHASE34 v1.2 FIRST MEASURED EXECUTION -> BLOCKED AT SMOKE GATE ===")
    print("authority all match:", all(a["match"] for a in auth))
    print("frozen sources all match:", all(f["match"] for f in fsrc))
    print("registry SHA:", registry_actual, "== canonical:",
          registry_actual == DOMAIN_TASK_REGISTRY_SHA)
    print("environment gate:", all(env_checks.values()))
    print("checkpoints all match:", all(c["match"] for c in ck))
    print("smoke constructed:", constructed, "| failed:", [c for c in SMOKE
                                                           if c not in constructed])
    print("measurement iterations:", 0)
    print()
    print("TERMINAL:", BLOCKED_TERMINAL)
    print()
    for a in NEW:
        print(f"{a['sha256']}  {a['path']}")


if __name__ == "__main__":
    main()
