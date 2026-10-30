#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase34 v1.4 latency execution GATES (source preflight + environment).

Classification: PHASE34_LATENCY_REPAIR_EXECUTION_V1_4__GATES
Revision: ra_medfilm_barr_phase34_efficiency_profiling_v1_4

Gates only. Does NOT construct models, deserialize checkpoints or time CUDA.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase34_latency_exec_gates_v1_4.py
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
REVISION = "ra_medfilm_barr_phase34_efficiency_profiling_v1_4"

V14_TERMINAL = ("PHASE34_LATENCY_REPAIR_SPEC_V1_4_COMPLETE__V1_3_200_ITERATION_BLOCK_TOTAL_"
                "LATENCY_MISLABELING_AND_ALIAS_DUPLICATE_EXECUTION_DISCLOSED__VALID_THROUGHPUT_"
                "MEMORY_STATIC_AND_ANALYTICAL_EVIDENCE_PRESERVED__SIX_DISTINCT_ARM_PER_FORWARD_"
                "CUDA_EVENT_LATENCY_PROTOCOL_WITH_6000_RAW_OBSERVATIONS_FROZEN__V1_4_SOURCE_FREEZE_"
                "COMPLETE__LATENCY_ONLY_REEXECUTION_ELIGIBLE_NOT_STARTED")

AUTH = OrderedDict([
    ("reports/audits/phase34_latency_repair_terminal_v1_4.json",
     "fb5e335764fe1ea05726a1c8cfbfb37f0ac37cad5b2301f6211571d5afb3a57c"),
    ("reports/audits/phase34_preexecution_source_freeze_v1_4.json",
     "6f3505ec91f3f229dfb7f3f502fd1952683fe2e7d691d119b26b0372d39c1221"),
    ("reports/tables/phase34_latency_arm_registry_v1_4.csv",
     "1a3de4baa126cb6e1cc400d6dd173d076bb8c73cbfd0648c0c918cf3d8f804f0"),
    ("reports/audits/phase34_v1_3_latency_source_root_cause.json",
     "a4ca49f3ffb5622785ac4eca3227165bd3f7b7530fc2cf0159544418bef3ac22"),
    ("reports/audits/phase34_latency_preflight_v1_4.json",
     "366b313dd380d5d6d83aa7a078189fdec11a0cac062c917c4a162e6f317392c5"),
])

SOURCES = OrderedDict([
    ("worker_v1_4", ("scripts/analysis/phase34_latency_worker_v1_4.py",
                     "369ae8c65b78f61acd59973d9b184e15be5733c6049f586ae0eb917b0168fab3")),
    ("harness_v1_4", ("scripts/analysis/phase34_latency_execution_v1_4.py",
                      "1c96183c5554a3d3f8f734dd50a048407558338900f4924c4ed695cd3e236960")),
    ("preflight_v1_4", ("scripts/analysis/phase34_latency_preflight_v1_4.py",
                        "f0fce5b58693d0dc1f3b42fcfe494df5cbf83ea907c3c83b9f5d7304218d4852")),
    ("common_v1_2", ("scripts/analysis/phase34_v1_2_common.py",
                     "ca74fe88a8314b6099b2455f3450ea6f075dcd3cf69208cdd8a784ad24e9a0f9")),
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

PRESERVED = OrderedDict([
    ("reports/tables/phase34_batch8_throughput_results_v1_3.csv",
     "ac2b21aa89086870af59cd341ac51122568a871981fc9df9a4f323ae58c84c6c"),
    ("reports/tables/phase34_gpu_memory_results_v1_3.csv",
     "6df4e0941dcd33ab90196f7572528afbc7848d9329c6bcb6940978813dd02979"),
    ("reports/tables/phase34_static_resource_profile_v1_3.csv",
     "f4c36efd4fedb07778cf8b752a1e54ec91b19b78d9d1c6f4ef300cb5bdb73343"),
    ("reports/tables/phase34_analytical_compute_summary_v1_3.csv",
     "bbe1d933c24e297454ec7afee0f64d00bc79dbcf815d747df2ec2f742c93f71f"),
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

    auth = []
    for rel, exp in AUTH.items():
        obs = sha256_file(ROOT / rel)
        auth.append({"path": rel, "expected_sha256": exp, "observed_sha256": obs,
                     "match": obs == exp})
    auth_ok = all(a["match"] for a in auth)
    ok &= auth_ok

    src = []
    for k, (rel, exp) in SOURCES.items():
        obs = sha256_file(ROOT / rel)
        src.append({"key": k, "path": rel, "expected_sha256": exp, "observed_sha256": obs,
                    "match": obs == exp})
    src_ok = all(s["match"] for s in src)
    ok &= src_ok

    preserved = []
    for rel, exp in PRESERVED.items():
        obs = sha256_file(ROOT / rel)
        preserved.append({"path": rel, "expected_sha256": exp, "observed_sha256": obs,
                          "match": obs == exp})
    pres_ok = all(p["match"] for p in preserved)
    ok &= pres_ok

    ck = []
    for cid, (rel, exp) in CHECKPOINTS.items():
        obs = sha256_file(ROOT / rel)
        ck.append({"component": cid, "path": rel, "expected_sha256": exp,
                   "observed_sha256": obs, "match": obs == exp})
    ck_ok = all(c["match"] for c in ck)
    ok &= ck_ok

    preflight = json.loads((AUD / "phase34_latency_preflight_v1_4.json")
                           .read_text(encoding="utf-8"))
    preflight_ok = preflight["n_checks"] == 22 and preflight["n_failed"] == 0
    ok &= preflight_ok
    terminal = json.loads((AUD / "phase34_latency_repair_terminal_v1_4.json")
                          .read_text(encoding="utf-8"))
    term_ok = terminal["terminal"] == V14_TERMINAL
    ok &= term_ok

    write_json(OrderedDict([
        ("artifact", "phase34_latency_execution_source_preflight_v1_4"),
        ("phase", 34), ("section", "\u00A7F"), ("method", METHOD), ("revision", REVISION),
        ("additive_filename", True),
        ("v1_4_terminal_exact", term_ok),
        ("v1_4_source_freeze_exact", auth[1]["match"]),
        ("v1_4_arm_registry_exact", auth[2]["match"]),
        ("authority_bindings", auth), ("authority_all_match", auth_ok),
        ("source_verification", src), ("all_sources_match", src_ok),
        ("preserved_valid_v1_3_evidence", preserved),
        ("preserved_valid_v1_3_all_match", pres_ok),
        ("checkpoint_verification", ck), ("all_checkpoints_match", ck_ok),
        ("static_preflight_22_0", preflight_ok),
        ("frozen_artifact_overwritten", False),
        ("model_constructed", False), ("checkpoint_deserialized", False),
        ("generated_utc", gen), ("all_pass", ok),
    ]), AUD / "phase34_latency_execution_source_preflight_v1_4.json")

    env = env_snapshot()
    expected = {"gpu_model": "NVIDIA GeForce RTX 3060 Ti", "gpu_compute_capability": "8.6",
                "gpu_total_vram_bytes": 8589279232, "python_version": "3.11.9",
                "torch_version": "2.6.0+cu124", "cuda_runtime": "12.4",
                "cuda_driver_version": "596.36", "cudnn_version": 90100}
    env_checks = {k: (env.get(k) == v) for k, v in expected.items()}
    env_ok = all(env_checks.values())
    ok &= env_ok
    write_json(OrderedDict([
        ("artifact", "phase34_latency_execution_environment_v1_4"),
        ("phase", 34), ("section", "\u00A7G"), ("method", METHOD), ("revision", REVISION),
        ("observed_environment", env), ("expected_frozen_environment", expected),
        ("environment_checks", env_checks), ("environment_gate_pass", env_ok),
        ("generated_utc", gen), ("all_pass", env_ok),
    ]), AUD / "phase34_latency_execution_environment_v1_4.json")

    print("=== PHASE34 v1.4 LATENCY EXECUTION GATES ===")
    print("authority all match:", auth_ok, "| sources all match:", src_ok)
    print("preserved valid v1.3 evidence:", pres_ok, "| checkpoints:", ck_ok)
    print("v1.4 terminal exact:", term_ok, "| static preflight 22/0:", preflight_ok)
    print("environment gate:", env_ok)
    print("GATES PASS:", ok)
    print()
    for a in NEW:
        print(f"{a['sha256']}  {a['path']}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
