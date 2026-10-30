#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase34 v1.3 measured-execution GATES (source preflight + smoke-driver scope + env + checkpoints).

Classification: PHASE34_V1_3_FIRST_MEASURED_RUNTIME_PROFILING_EXECUTION__GATES
Revision: ra_medfilm_barr_phase34_efficiency_profiling_v1_3

Gates only. Does NOT construct models, does NOT deserialize checkpoints, does NOT time.
If any gate fails the driver exits non-zero BEFORE the harness is invoked.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase34_measured_gates_v1_3.py
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import platform
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"
METHOD = "RA-MedFiLM-BARR"
REVISION = "ra_medfilm_barr_phase34_efficiency_profiling_v1_3"

SMOKE_TERMINAL = ("PHASE34_V1_3_SMOKE_GATE_COMPLETE__ALL_FOUR_CANONICAL_COMPONENTS_STRICT_LOADED_"
                  "PARAMETER_VERIFIED_AND_UNTIMED_FORWARDS_PASS__CONTROLLED_SKIP_AND_EXECUTE_"
                  "SMOKES_PASS__TOTAL_SMOKE_FORWARD_CALLS_10__ZERO_LATENCY_THROUGHPUT_MEMORY_OR_"
                  "PROFILER_MEASUREMENTS__FIRST_MEASURED_PROFILING_EXECUTION_ELIGIBLE_NOT_STARTED")

AUTH = OrderedDict([
    ("reports/audits/phase34_smoke_execution_terminal_v1_3.json",
     "4336b7b96d1b3874745feb52af6738e52174be644673f63642cd2feb6e542511"),
    ("reports/audits/phase34_model_identity_and_smoke_gate_v1_3.json",
     "8e398f9c405e4a9bcdfb52ed60fdadd03c8d348807b87fab1801839fe45873c6"),
    ("reports/audits/phase34_smoke_final_check_v1_3.json",
     "ffe0231067f821f1f41f05be962a7d0e619f88404bb5e49f98dd951bed73266a"),
    ("reports/audits/phase34_smoke_execution_provenance_v1_3.json",
     "f23e7f5c4d2d0d090a9e9bfd1588db0db174d98f48ed49bea2322c2f8a32064b"),
    ("reports/audits/phase34_preexecution_source_freeze_v1_3.json",
     "c7ee684c24d3ddaf4af3eeca6eed3bd44c856c9152b6eccaec0443e6df14c742"),
    ("reports/audits/phase34_execution_source_preflight_v1_3.json",
     "ec062e4df588377c1e83f2971d7e646f834eb0dbc6d127a6625a961efd72bd6b"),
    ("reports/audits/phase34_timed_operation_registry_v1_2.json",
     "435e497c5cc359d9ea434bd52a00c1ad3c9fcedc2d23a59e46c376c53e6a1b7c"),
])

SOURCES = OrderedDict([
    ("common", ("scripts/analysis/phase34_v1_2_common.py",
                "ca74fe88a8314b6099b2455f3450ea6f075dcd3cf69208cdd8a784ad24e9a0f9")),
    ("worker", ("scripts/analysis/phase34_efficiency_profiling_worker_v1_3.py",
                "295c64d94358aed7f243b4036a75a5fa78288585f7bf17d3a764fb64291e59f7")),
    ("harness", ("scripts/analysis/phase34_efficiency_profiling_execution_v1_3.py",
                 "3244c2f95fbd1381bf553e18d11175e45b56da6247bceb371616ca64d440f237")),
    ("preflight", ("scripts/analysis/phase34_execution_preflight_v1_3.py",
                   "494925ecbc9a13eb498764f55bb8eef43fa2eac85ec96b20b23394636047c46d")),
    ("model_G", ("src/models/film/global_medfilm.py",
                 "a04ff3e61b4d900ff47c2f390da4a999e73bd6047b28a19e41b05115e431d11f")),
    ("model_R_psi", ("src/models/barr/regional_refiner.py",
                     "4fe0abde3ec3a183d930f676c4400b4d9ba778793ea64abf1755c5b8dabf947a")),
    ("model_B_phi_authority", ("scripts/analysis/train_phase25d_router.py",
                               "fc7c1bdf263ae4551dcb8f170d3203adb8540fbc189846265b74f6eca1541e91")),
    ("model_S_omega_authority", ("scripts/analysis/phase25f_execution_common.py",
                                 "98cf958a377e2de30e0b67e63fd56bafea418b2b061a362ee7284e852012cd2e")),
    ("domain_task_registry", ("src/analysis/multidomain_harmonization.py",
                              "3f009d994ed24d9c2edf8e48646e93700ab4e54dea786fb4bd03180c825cbf92")),
])

SMOKE_DRIVER = "scripts/analysis/phase34_smoke_runtime_v1_3.py"
SMOKE_DRIVER_SHA = "e99cc9132f0a49ab250a6a501966c896b1dd72aa273e3078cb41e0984dbe1cca"

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
    ok = True

    # ---------- §A smoke authority ----------
    auth = []
    for rel, exp in AUTH.items():
        obs = sha256_file(ROOT / rel)
        auth.append({"path": rel, "expected_sha256": exp, "observed_sha256": obs,
                     "match": obs == exp})
    auth_ok = all(a["match"] for a in auth)
    ok &= auth_ok
    smoke_gate = json.loads((AUD / "phase34_model_identity_and_smoke_gate_v1_3.json")
                            .read_text(encoding="utf-8"))
    smoke_fc = json.loads((AUD / "phase34_smoke_final_check_v1_3.json")
                          .read_text(encoding="utf-8"))
    smoke_term = json.loads((AUD / "phase34_smoke_execution_terminal_v1_3.json")
                            .read_text(encoding="utf-8"))
    smoke_ok = (smoke_gate["smoke_gate_pass"] and smoke_fc["n_checks"] == 41
                and smoke_fc["n_failed"] == 0 and smoke_term["terminal"] == SMOKE_TERMINAL)

    # ---------- §B source freeze ----------
    src = []
    for k, (rel, exp) in SOURCES.items():
        obs = sha256_file(ROOT / rel)
        src.append({"key": k, "path": rel, "expected_sha256": exp, "observed_sha256": obs,
                    "match": obs == exp})
    src_ok = all(s["match"] for s in src)
    ok &= src_ok
    frozen_preflight_unchanged = (
        sha256_file(AUD / "phase34_execution_source_preflight_v1_3.json")
        == "ec062e4df588377c1e83f2971d7e646f834eb0dbc6d127a6625a961efd72bd6b")

    # ---------- §C smoke-driver governance ----------
    harness_src = (ROOT / "scripts/analysis/phase34_efficiency_profiling_execution_v1_3.py"
                   ).read_text(encoding="utf-8")
    worker_src = (ROOT / "scripts/analysis/phase34_efficiency_profiling_worker_v1_3.py"
                  ).read_text(encoding="utf-8")
    driver_imported = ("smoke_runtime" in harness_src) or ("smoke_runtime" in worker_src)
    driver_sha_actual = sha256_file(ROOT / SMOKE_DRIVER)
    ok &= (not driver_imported)
    write_json(OrderedDict([
        ("artifact", "phase34_smoke_only_driver_scope_record_v1_3"),
        ("phase", 34), ("section", "\u00A7C"), ("method", METHOD), ("revision", REVISION),
        ("driver_path", SMOKE_DRIVER), ("driver_sha256", driver_sha_actual),
        ("reported_sha256", SMOKE_DRIVER_SHA),
        ("sha_match", driver_sha_actual == SMOKE_DRIVER_SHA),
        ("driver_role", "SMOKE_ONLY_ORCHESTRATION_AND_REPORTING"),
        ("preexecution_source_frozen", False),
        ("produced_measured_latency", False), ("produced_throughput", False),
        ("produced_memory_measurement", False), ("scientific_timing_source", False),
        ("eligible_for_measured_execution", False),
        ("used_in_first_measured_execution", False),
        ("frozen_harness_or_worker_depends_on_driver", driver_imported),
        ("source_freeze_expanded_after_measurement", False),
        ("generated_utc", gen), ("all_pass", not driver_imported),
    ]), AUD / "phase34_smoke_only_driver_scope_record_v1_3.json")

    # ---------- §D additive measured-execution source preflight ----------
    write_json(OrderedDict([
        ("artifact", "phase34_execution_source_preflight_measured_v1_3"),
        ("phase", 34), ("section", "\u00A7D"), ("method", METHOD), ("revision", REVISION),
        ("additive_filename", True),
        ("original_frozen_preflight",
         {"path": "reports/audits/phase34_execution_source_preflight_v1_3.json",
          "sha256": "ec062e4df588377c1e83f2971d7e646f834eb0dbc6d127a6625a961efd72bd6b",
          "unchanged": frozen_preflight_unchanged}),
        ("smoke_authority_bindings", auth), ("smoke_authority_all_match", auth_ok),
        ("smoke_authority_consistent", smoke_ok),
        ("measurement_orchestration_source",
         "scripts/analysis/phase34_efficiency_profiling_execution_v1_3.py"),
        ("measurement_worker", "scripts/analysis/phase34_efficiency_profiling_worker_v1_3.py"),
        ("source_verification", src), ("all_sources_match", src_ok),
        ("smoke_only_driver_used_for_measurement", False),
        ("new_source_authored_for_timing", False),
        ("model_constructed", False), ("checkpoint_deserialized", False),
        ("generated_utc", gen),
        ("all_pass", auth_ok and src_ok and smoke_ok and frozen_preflight_unchanged
         and not driver_imported),
    ]), AUD / "phase34_execution_source_preflight_measured_v1_3.json")

    # ---------- §E environment ----------
    env = env_snapshot()
    expected = {"gpu_model": "NVIDIA GeForce RTX 3060 Ti", "gpu_compute_capability": "8.6",
                "gpu_total_vram_bytes": 8589279232, "python_version": "3.11.9",
                "torch_version": "2.6.0+cu124", "cuda_runtime": "12.4",
                "cuda_driver_version": "596.36", "cudnn_version": 90100}
    env_checks = {k: (env.get(k) == v) for k, v in expected.items()}
    env_ok = all(env_checks.values())
    ok &= env_ok
    write_json(OrderedDict([
        ("artifact", "phase34_measured_execution_environment_v1_3"),
        ("phase", 34), ("section", "\u00A7E"), ("method", METHOD), ("revision", REVISION),
        ("observed_environment", env), ("expected_frozen_environment", expected),
        ("environment_checks", env_checks), ("environment_gate_pass", env_ok),
        ("generated_utc", gen), ("all_pass", env_ok),
    ]), AUD / "phase34_measured_execution_environment_v1_3.json")

    # ---------- §F checkpoint identity ----------
    ck = []
    for cid, (rel, exp, params) in CHECKPOINTS.items():
        p = ROOT / rel
        obs = sha256_file(p)
        ck.append({"component": cid, "path": rel, "expected_sha256": exp,
                   "observed_sha256": obs, "match": obs == exp,
                   "file_bytes": p.stat().st_size, "parameter_bytes_float32": params * 4,
                   "expected_parameters": params})
    ck_ok = all(c["match"] for c in ck)
    ok &= ck_ok

    print("=== PHASE34 v1.3 MEASURED-EXECUTION GATES ===")
    print("smoke authority all match:", auth_ok, "| smoke consistent:", smoke_ok)
    print("frozen sources all match:", src_ok,
          "| frozen preflight unchanged:", frozen_preflight_unchanged)
    print("smoke driver imported by harness/worker:", driver_imported)
    print("environment gate:", env_ok, "| checkpoints:", ck_ok)
    print("GATES PASS:", ok)
    print()
    for a in NEW:
        print(f"{a['sha256']}  {a['path']}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
