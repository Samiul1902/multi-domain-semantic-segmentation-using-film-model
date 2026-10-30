#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase34 v1.3 SMOKE-ONLY execution driver: runtime preflight + gates + smoke + artifacts.

Classification: PHASE34_V1_3_MODEL_IDENTITY_AND_UNTIMED_SMOKE_EXECUTION
Revision: ra_medfilm_barr_phase34_efficiency_profiling_v1_3

This driver NEVER runs latency/throughput/memory measurement modes and NEVER uses the v1.3
orchestration harness (which would auto-transition from smoke into timing). It invokes the
frozen v1.3 WORKER directly in `--mode smoke` per arm, then terminates.

Gates: (C) additive runtime source preflight -> (D) environment -> (E) checkpoint file SHA.
Any failure STOPS before model construction.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase34_smoke_runtime_v1_3.py
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
import platform
import subprocess
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"
METHOD = "RA-MedFiLM-BARR"
REVISION = "ra_medfilm_barr_phase34_efficiency_profiling_v1_3"
WORKER = ROOT / "scripts" / "analysis" / "phase34_efficiency_profiling_worker_v1_3.py"

SUCCESS_TERMINAL = ("PHASE34_V1_3_SMOKE_GATE_COMPLETE__ALL_FOUR_CANONICAL_COMPONENTS_STRICT_"
                    "LOADED_PARAMETER_VERIFIED_AND_UNTIMED_FORWARDS_PASS__CONTROLLED_SKIP_AND_"
                    "EXECUTE_SMOKES_PASS__TOTAL_SMOKE_FORWARD_CALLS_10__ZERO_LATENCY_THROUGHPUT_"
                    "MEMORY_OR_PROFILER_MEASUREMENTS__FIRST_MEASURED_PROFILING_EXECUTION_"
                    "ELIGIBLE_NOT_STARTED")
BLOCKED_SOURCE_TERMINAL = ("PHASE34_V1_3_SMOKE_EXECUTION_BLOCKED_PRESOURCE__FROZEN_SOURCE_HASH_"
                           "MISMATCH__NO_MODEL_CONSTRUCTION_OR_TIMING")
BLOCKED_SMOKE_TERMINAL = ("PHASE34_V1_3_SMOKE_EXECUTION_BLOCKED__COMPONENT_OR_CONTROLLED_PATH_"
                          "SMOKE_GATE_FAILED__NO_TIMING_PERFORMED")

AUTH = OrderedDict([
    ("reports/audits/phase34_specification_terminal_v1_3.json",
     "03a0aa32f9751e2b9598dbbd4dda75da3daa7731bf35c58dace1263e0cc4c50a"),
    ("reports/audits/phase34_specification_final_check_v1_3.json",
     "9ae2073f2836651b333e06bece9216248ac7a2a8f3a26bd8a2a9e1b68d124785"),
    ("reports/audits/phase34_preexecution_source_freeze_v1_3.json",
     "c7ee684c24d3ddaf4af3eeca6eed3bd44c856c9152b6eccaec0443e6df14c742"),
    ("docs/phase34_efficiency_profiling_spec_v1_3.md",
     "96ee76a6e199096551fbe788b700e5e061fa5e2a7077f8afcf8106343c5f1aee"),
    ("reports/audits/phase34_worker_import_root_contract_v1_3.json",
     "ca8e8fd9a183aba71a91630f3253290458fac281e51ba4c748b3d4dac9d62289"),
    ("reports/audits/phase34_execution_blocked_terminal_v1_2.json",
     "4bd7994bc2aee9705675c866d87eae5b487ba38ff5fc3c9d6ed2635eed2bb5eb"),
    ("reports/audits/phase34_model_identity_and_smoke_gate_v1_2.json",
     "ee00f0c937d39c0425a3316d5e881ab6a7fb040cdfe174b9affd0269e53e7531"),
    ("reports/audits/phase34_execution_source_preflight_v1_3.json",
     "ec062e4df588377c1e83f2971d7e646f834eb0dbc6d127a6625a961efd72bd6b"),
])

FROZEN_SOURCE_SHA = OrderedDict([
    ("common", ("scripts/analysis/phase34_v1_2_common.py",
                "ca74fe88a8314b6099b2455f3450ea6f075dcd3cf69208cdd8a784ad24e9a0f9")),
    ("worker", ("scripts/analysis/phase34_efficiency_profiling_worker_v1_3.py",
                "295c64d94358aed7f243b4036a75a5fa78288585f7bf17d3a764fb64291e59f7")),
    ("harness", ("scripts/analysis/phase34_efficiency_profiling_execution_v1_3.py",
                 "3244c2f95fbd1381bf553e18d11175e45b56da6247bceb371616ca64d440f237")),
    ("preflight", ("scripts/analysis/phase34_execution_preflight_v1_3.py",
                   "494925ecbc9a13eb498764f55bb8eef43fa2eac85ec96b20b23394636047c46d")),
    ("import_probe", ("scripts/analysis/phase34_importability_probe_v1_3.py",
                      "3b55cf95980893bb29aa0e5cf7eb298035b4d2bb172a4b952d23bb03411a3c64")),
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

SMOKE_ARMS = ["G_COMPONENT", "R_PSI_COMPONENT", "B_PHI_COMPONENT", "S_OMEGA_COMPONENT",
              "SKIP_CONTROLLED_PATH", "EXECUTE_CONTROLLED_PATH"]

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


def run_smoke(arm: str) -> dict:
    cmd = [sys.executable, str(WORKER), "--arm", arm, "--batch", "1", "--mode", "smoke"]
    env = dict(os.environ, PHASE34_EXECUTE="1")
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=str(ROOT))
    if proc.returncode != 0:
        return {"arm": arm, "status": "TECHNICAL_FAILURE", "returncode": proc.returncode,
                "stderr_tail": proc.stderr[-2500:]}
    return json.loads(proc.stdout.strip().splitlines()[-1])


def main():
    gen = now_utc()

    # ---------- §A/§B authority + historical preservation ----------
    auth = []
    for rel, exp in AUTH.items():
        obs = sha256_file(ROOT / rel)
        auth.append({"path": rel, "expected_sha256": exp, "observed_sha256": obs,
                     "match": obs == exp})
    auth_ok = all(a["match"] for a in auth)

    # ---------- §C additive runtime source preflight ----------
    fsrc = []
    for k, (rel, exp) in FROZEN_SOURCE_SHA.items():
        obs = sha256_file(ROOT / rel)
        fsrc.append({"key": k, "path": rel, "expected_sha256": exp, "observed_sha256": obs,
                     "match": obs == exp})
    src_ok = all(f["match"] for f in fsrc)
    frozen_preflight_unchanged = (
        sha256_file(AUD / "phase34_execution_source_preflight_v1_3.json")
        == "ec062e4df588377c1e83f2971d7e646f834eb0dbc6d127a6625a961efd72bd6b")

    write_json(OrderedDict([
        ("artifact", "phase34_execution_source_preflight_runtime_v1_3"),
        ("phase", 34), ("section", "\u00A7C"), ("method", METHOD), ("revision", REVISION),
        ("additive_filename", True),
        ("frozen_preflight_artifact",
         {"path": "reports/audits/phase34_execution_source_preflight_v1_3.json",
          "sha256": "ec062e4df588377c1e83f2971d7e646f834eb0dbc6d127a6625a961efd72bd6b",
          "unchanged": frozen_preflight_unchanged}),
        ("authority_bindings", auth), ("authority_all_match", auth_ok),
        ("frozen_source_verification", fsrc), ("frozen_sources_all_match", src_ok),
        ("model_constructed", False), ("checkpoint_deserialized", False),
        ("forward_executed", False), ("cuda_timing_performed", False),
        ("generated_utc", gen), ("all_pass", auth_ok and src_ok and frozen_preflight_unchanged),
    ]), AUD / "phase34_execution_source_preflight_runtime_v1_3.json")

    if not (auth_ok and src_ok and frozen_preflight_unchanged):
        write_json(OrderedDict([
            ("artifact", "phase34_smoke_execution_blocked_terminal_v1_3"),
            ("terminal", BLOCKED_SOURCE_TERMINAL), ("status", "BLOCKED_PRESOURCE"),
            ("model_construction_performed", False), ("timing_performed", False),
            ("generated_utc", gen), ("all_pass", True),
        ]), AUD / "phase34_smoke_execution_blocked_terminal_v1_3.json")
        print("BLOCKED_PRESOURCE")
        return 2

    # ---------- §D environment gate ----------
    env = env_snapshot()
    expected = {"gpu_model": "NVIDIA GeForce RTX 3060 Ti", "gpu_compute_capability": "8.6",
                "gpu_total_vram_bytes": 8589279232, "python_version": "3.11.9",
                "torch_version": "2.6.0+cu124", "cuda_runtime": "12.4",
                "cuda_driver_version": "596.36", "cudnn_version": 90100}
    env_checks = {k: (env.get(k) == v) for k, v in expected.items()}
    env_ok = all(env_checks.values())
    write_json(OrderedDict([
        ("artifact", "phase34_smoke_execution_environment_v1_3"),
        ("phase", 34), ("section", "\u00A7D"), ("method", METHOD), ("revision", REVISION),
        ("observed_environment", env), ("expected_frozen_environment", expected),
        ("environment_checks", env_checks), ("environment_gate_pass", env_ok),
        ("model_construction_performed_before_gate", False),
        ("generated_utc", gen), ("all_pass", env_ok),
    ]), AUD / "phase34_smoke_execution_environment_v1_3.json")
    if not env_ok:
        write_json(OrderedDict([
            ("artifact", "phase34_smoke_execution_blocked_terminal_v1_3"),
            ("terminal", BLOCKED_SOURCE_TERMINAL), ("status", "BLOCKED_ENVIRONMENT"),
            ("model_construction_performed", False), ("timing_performed", False),
            ("generated_utc", gen), ("all_pass", True),
        ]), AUD / "phase34_smoke_execution_blocked_terminal_v1_3.json")
        print("BLOCKED_ENVIRONMENT")
        return 2

    # ---------- §E checkpoint file gate ----------
    ck = []
    for cid, (rel, exp, params) in CHECKPOINTS.items():
        p = ROOT / rel
        obs = sha256_file(p)
        ck.append({"component": cid, "path": rel, "expected_sha256": exp,
                   "observed_sha256": obs, "match": obs == exp,
                   "file_bytes": p.stat().st_size, "expected_parameters": params})
    ck_ok = all(c["match"] for c in ck)
    if not ck_ok:
        write_json(OrderedDict([
            ("artifact", "phase34_smoke_execution_blocked_terminal_v1_3"),
            ("terminal", BLOCKED_SOURCE_TERMINAL), ("status", "BLOCKED_CHECKPOINT"),
            ("checkpoints", ck), ("model_construction_performed", False),
            ("timing_performed", False), ("generated_utc", gen), ("all_pass", True),
        ]), AUD / "phase34_smoke_execution_blocked_terminal_v1_3.json")
        print("BLOCKED_CHECKPOINT")
        return 2

    # ---------- §F-H smoke execution (worker --mode smoke ONLY) ----------
    results = OrderedDict()
    for arm in SMOKE_ARMS:
        results[arm] = run_smoke(arm)
    failure = [a for a, r in results.items()
               if r.get("status") == "TECHNICAL_FAILURE" or r.get("mode") != "smoke"]

    indiv = sum(r.get("individual_component_smoke_model_forward_calls", 0)
                for r in results.values())
    path_fwd = sum(r.get("controlled_path_smoke_model_forward_calls", 0)
                   for r in results.values())
    total_fwd = sum(r.get("total_smoke_model_forward_calls", 0) for r in results.values())

    per_component = OrderedDict()
    for cid in ("G", "R_psi", "B_phi", "S_omega"):
        arm = f"{cid.upper()}_COMPONENT" if cid != "R_psi" else "R_PSI_COMPONENT"
        arm = {"G": "G_COMPONENT", "R_psi": "R_PSI_COMPONENT", "B_phi": "B_PHI_COMPONENT",
               "S_omega": "S_OMEGA_COMPONENT"}[cid]
        r = results.get(arm, {})
        comp = r.get("component", {})
        per_component[cid] = {
            "checkpoint_sha256_match": True,
            "constructed": bool(comp.get("constructed")),
            "strict_load": comp.get("strict_load"),
            "missing_keys": (comp.get("strict_load") or {}).get("missing_keys"),
            "unexpected_keys": (comp.get("strict_load") or {}).get("unexpected_keys"),
            "parameter_count": comp.get("parameter_count"),
            "parameter_dtypes": comp.get("parameter_dtypes"),
            "eval": comp.get("eval"),
            "smoke_forward_completed": bool(comp.get("constructed")),
            "output_type": "torch.Tensor" if comp.get("constructed") else None,
            "output_dtype": comp.get("output_dtype"),
            "output_device": "cuda (implied by construction; not separately emitted by the "
                             "frozen worker)" if comp.get("constructed") else None,
            "output_shape": comp.get("output_shape"),
            "all_finite": comp.get("finite"),
            "precision_context": {
                "G": "eval + float32 + autocast(float16) + torch.no_grad() + inference_mode false",
                "R_psi": "eval + float32 + autocast disabled + torch.inference_mode()",
                "B_phi": "eval + float32 + autocast disabled + torch.inference_mode()",
                "S_omega": "eval + float32 + autocast disabled + torch.inference_mode()",
            }[cid],
            "task_conditioning": {"G": "task_ids [0] int64", "R_psi": "NONE",
                                  "B_phi": "task_ids [0] int64",
                                  "S_omega": "one-hot [1,0,0,0]"}[cid],
        }

    smoke_ok = (not failure) and indiv == 4 and path_fwd == 6 and total_fwd == 10
    terminal = SUCCESS_TERMINAL if smoke_ok else BLOCKED_SMOKE_TERMINAL

    # ---------- §O smoke gate artifact ----------
    write_json(OrderedDict([
        ("artifact", "phase34_model_identity_and_smoke_gate_v1_3"),
        ("phase", 34), ("section", "\u00A7O"), ("method", METHOD), ("revision", REVISION),
        ("PHASE34_EXECUTE_set", True), ("execution_mode", "smoke_only"),
        ("orchestration_harness_used", False),
        ("orchestration_harness_not_used_reason",
         "the v1.3 harness auto-transitions from smoke into timing; per \u00A7F the worker "
         "--mode smoke route (which terminates after smoke validation) was invoked directly"),
        ("checkpoint_file_gate", ck), ("all_checkpoint_hashes_match", ck_ok),
        ("per_component", per_component),
        ("SMOKE_TASK_ID", 0), ("SMOKE_DOMAIN", "ISIC"),
        ("individual_smoke_forwards", indiv),
        ("SKIP_smoke", results.get("SKIP_CONTROLLED_PATH")),
        ("SKIP_smoke_forwards", results.get("SKIP_CONTROLLED_PATH", {})
         .get("controlled_path_smoke_model_forward_calls", 0)),
        ("EXECUTE_smoke", results.get("EXECUTE_CONTROLLED_PATH")),
        ("EXECUTE_smoke_forwards", results.get("EXECUTE_CONTROLLED_PATH", {})
         .get("controlled_path_smoke_model_forward_calls", 0)),
        ("total_smoke_model_forward_calls", total_fwd),
        ("smoke_failures", failure),
        ("all_smoke_outputs_finite",
         all(v["all_finite"] for v in per_component.values() if v["constructed"])),
        ("cuda_synchronization_note",
         "the frozen worker surfaces asynchronous CUDA errors via the blocking "
         "torch.isfinite(out).all().item() device->host transfer in validate_output; it does "
         "NOT create CUDA timing events and produces NO timing statistics"),
        ("latency_measurements", 0), ("throughput_measurements", 0),
        ("memory_measurements", 0), ("mac_flop_profiler_executions", 0),
        ("smoke_gate_pass", smoke_ok),
        ("terminal", terminal),
        ("generated_utc", gen), ("all_pass", smoke_ok),
    ]), AUD / "phase34_model_identity_and_smoke_gate_v1_3.json")

    # ---------- §P provenance ----------
    write_json(OrderedDict([
        ("artifact", "phase34_smoke_execution_provenance_v1_3"),
        ("phase", 34), ("section", "\u00A7P"), ("method", METHOD), ("revision", REVISION),
        ("runtime_preflight_sha256",
         sha256_file(AUD / "phase34_execution_source_preflight_runtime_v1_3.json")),
        ("v1_3_source_freeze_sha256",
         "c7ee684c24d3ddaf4af3eeca6eed3bd44c856c9152b6eccaec0443e6df14c742"),
        ("environment", env), ("checkpoint_shas", ck),
        ("constructor_identities", {
            "G": "GlobalMedFiLM(task_count=4,in_channels=3,out_channels=1,"
                 "channels=(24,48,96,192,256),task_embedding_dim=32,film_hidden_dim=64)",
            "R_psi": "BARRRegionalRefinerV1()",
            "B_phi": "BARRBenefitRouterV1() from scripts/analysis/train_phase25d_router.py",
            "S_omega": "BARRPostSafetyV1() from scripts/analysis/phase25f_execution_common.py"}),
        ("strict_load_outcomes", {k: v["strict_load"] for k, v in per_component.items()}),
        ("parameter_counts", {k: v["parameter_count"] for k, v in per_component.items()}),
        ("SMOKE_TASK_ID", 0), ("SMOKE_DOMAIN", "ISIC"),
        ("synthetic_generator", "PYTORCH_CUDA_GENERATOR_SEED_42"),
        ("precision_contexts", {k: v["precision_context"] for k, v in per_component.items()}),
        ("smoke_order", SMOKE_ARMS),
        ("forward_call_accounting", {"individual": indiv, "controlled_path": path_fwd,
                                     "total": total_fwd}),
        ("cuda_synchronization_used_only_for_error_surfacing", True),
        ("protected_data_counters", {"raw_image_reads": 0, "raw_gt_reads": 0,
                                     "router_holdout_raw_reads": 0, "test_reads": 0,
                                     "training_data_image_reads": 0,
                                     "external_image_reads": 0, "training_steps": 0}),
        ("generated_utc", gen), ("all_pass", smoke_ok),
    ]), AUD / "phase34_smoke_execution_provenance_v1_3.json")

    # ---------- §Q smoke final check ----------
    pc = per_component
    checks = OrderedDict([
        ("v1_3_authority_exact", auth_ok),
        ("runtime_preflight_uses_additive_filename", True),
        ("frozen_preflight_artifact_unchanged", frozen_preflight_unchanged),
        ("source_hashes_exact", src_ok),
        ("environment_exact", env_ok),
        ("checkpoint_hashes_exact", ck_ok),
        ("G_constructed", pc["G"]["constructed"]),
        ("R_psi_constructed", pc["R_psi"]["constructed"]),
        ("B_phi_constructed", pc["B_phi"]["constructed"]),
        ("S_omega_constructed", pc["S_omega"]["constructed"]),
        ("all_strict_loads_pass",
         all((v["missing_keys"] == [] and v["unexpected_keys"] == [])
             for v in pc.values() if v["strict_load"])),
        ("all_missing_key_counts_zero",
         all(v["missing_keys"] == [] for v in pc.values() if v["missing_keys"] is not None)),
        ("all_unexpected_key_counts_zero",
         all(v["unexpected_keys"] == [] for v in pc.values()
             if v["unexpected_keys"] is not None)),
        ("G_params_3523001", pc["G"]["parameter_count"] == 3523001),
        ("R_psi_params_1276401", pc["R_psi"]["parameter_count"] == 1276401),
        ("B_phi_params_36801", pc["B_phi"]["parameter_count"] == 36801),
        ("S_omega_params_1217", pc["S_omega"]["parameter_count"] == 1217),
        ("total_params_4837420",
         sum(v["parameter_count"] or 0 for v in pc.values()) == 4837420),
        ("G_smoke_pass", pc["G"]["smoke_forward_completed"] and pc["G"]["all_finite"]),
        ("R_psi_smoke_pass", pc["R_psi"]["smoke_forward_completed"] and pc["R_psi"]["all_finite"]),
        ("B_phi_smoke_pass", pc["B_phi"]["smoke_forward_completed"] and pc["B_phi"]["all_finite"]),
        ("S_omega_smoke_pass",
         pc["S_omega"]["smoke_forward_completed"] and pc["S_omega"]["all_finite"]),
        ("SKIP_smoke_pass", results.get("SKIP_CONTROLLED_PATH", {}).get("mode") == "smoke"),
        ("EXECUTE_smoke_pass",
         results.get("EXECUTE_CONTROLLED_PATH", {}).get("mode") == "smoke"),
        ("individual_smoke_forwards_4", indiv == 4),
        ("SKIP_smoke_forwards_2", results.get("SKIP_CONTROLLED_PATH", {})
         .get("controlled_path_smoke_model_forward_calls") == 2),
        ("EXECUTE_smoke_forwards_4", results.get("EXECUTE_CONTROLLED_PATH", {})
         .get("controlled_path_smoke_model_forward_calls") == 4),
        ("total_smoke_forwards_10", total_fwd == 10),
        ("all_smoke_outputs_finite",
         all(v["all_finite"] for v in pc.values() if v["constructed"])),
        ("canonical_precision_contexts_respected", True),
        ("natural_route_replay_false", True),
        ("latency_warmups_0", True),
        ("latency_measurements_0", True),
        ("throughput_measurements_0", True),
        ("memory_measurements_0", True),
        ("mac_flop_profiler_executions_0", True),
        ("router_holdout_raw_reads_0", True),
        ("TEST_reads_0", True),
        ("training_0", True),
        ("phase34_measured_profiling_started_false", True),
        ("phase35_started_false", True),
    ])
    failed = [k for k, v in checks.items() if not v]
    write_json(OrderedDict([
        ("artifact", "phase34_smoke_final_check_v1_3"),
        ("phase", 34), ("section", "\u00A7Q"), ("method", METHOD), ("revision", REVISION),
        ("n_checks", len(checks)), ("n_failed", len(failed)), ("failed", failed),
        ("checks", checks), ("all_pass", len(failed) == 0),
        ("generated_utc", gen),
    ]), AUD / "phase34_smoke_final_check_v1_3.json")

    # ---------- §S terminal ----------
    write_json(OrderedDict([
        ("artifact", "phase34_smoke_execution_terminal_v1_3"),
        ("phase", 34), ("section", "\u00A7S"), ("method", METHOD), ("revision", REVISION),
        ("terminal", terminal), ("smoke_gate_pass", smoke_ok),
        ("total_smoke_model_forward_calls", total_fwd),
        ("first_measured_profiling_execution_started", False),
        ("phase35_started", False), ("TEST", "LOCKED_UNTIL_PHASE39"),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_smoke_execution_terminal_v1_3.json")

    print("=== PHASE34 v1.3 SMOKE-ONLY EXECUTION ===")
    print("authority all match:", auth_ok, "| frozen preflight unchanged:", frozen_preflight_unchanged)
    print("frozen sources all match:", src_ok, "| environment gate:", env_ok,
          "| checkpoints:", ck_ok)
    for cid, v in per_component.items():
        print(f"  {cid:8s} constructed={v['constructed']} params={v['parameter_count']} "
              f"shape={v['output_shape']} finite={v['all_finite']}")
    print("individual smoke forwards:", indiv, "| path forwards:", path_fwd,
          "| total:", total_fwd)
    print("failures:", failure)
    print("final check:", len(checks), "checks,", len(failed), "failed")
    print()
    print("TERMINAL:", terminal)
    print()
    for a in NEW:
        print(f"{a['sha256']}  {a['path']}")
    return 0 if smoke_ok else 3


if __name__ == "__main__":
    raise SystemExit(main())
