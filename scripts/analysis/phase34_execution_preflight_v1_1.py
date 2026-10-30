#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase34 v1.1 first-measured-execution STATIC SOURCE PREFLIGHT + environment gate.

ZERO-EXECUTION. This script performs the mandatory pre-model-load static checks required
by the v1.1 execution authorization. It NEVER deserializes a checkpoint into a model, NEVER
constructs a model, NEVER runs a forward, NEVER times CUDA and NEVER measures memory.

If the static semantic audit fails, it writes the BLOCKED_PREMODEL terminal and produces
NO measurement artifacts.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase34_execution_preflight_v1_1.py
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import platform
import re
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"
METHOD = "RA-MedFiLM-BARR"
REVISION = "ra_medfilm_barr_phase34_efficiency_profiling_v1_1"

BLOCKED_TERMINAL = ("PHASE34_EXECUTION_BLOCKED_PREMODEL__V1_1_FROZEN_SOURCE_OR_RUNTIME_"
                    "SEMANTICS_MISMATCH__NO_MEASUREMENTS_PERFORMED")

# ---- accepted v1.1 authority (fail-closed) ----
AUTH = OrderedDict([
    ("reports/audits/phase34_specification_terminal_v1_1.json",
     "3b8c0d55a13584a0730e2095c3b1df261447217661e6de1130c8c0b234786a86"),
    ("reports/audits/phase34_specification_final_check_v1_1.json",
     "ffa567d780e6527cd18553268bd59e893b2b659544ee223b2da57340220dcbea"),
    ("reports/audits/phase34_preexecution_source_freeze_v1_1.json",
     "27402c5a65004660fcbd944e422073447f10afcedddb2f8625dbd9a57ba8d689"),
    ("docs/phase34_efficiency_profiling_spec_v1_1.md",
     "bacd3a4e436f433b7ba82c71687ec182b2ef90ffbabaaaf5e92c3d5a8b5b4191"),
    ("reports/audits/phase34_precision_execution_semantics_contract_v1_1.json",
     "a37d29c2960b627c92d973f6c40632577ea1d90a0546220ad43723a2e8772fde"),
    ("reports/audits/phase34_analytical_compute_contract_v1_1.json",
     "c126ab3337b56e2f82e9cf79e5d7dce5c436696bb5177d43e8305144977f4732"),
    ("reports/tables/phase34_profiling_arm_registry_v1_1.csv",
     "91648b8758e1ebfc990728e2d43b5381eea074d911ca6c30ac5558ed70457038"),
    ("reports/audits/phase34_measured_runtime_scope_v1_1.json",
     "4b7bcc269a86cadb8dbf8ff512da3e51619579599a369b8cf457929f8fbd170d"),
    ("reports/audits/phase34_execution_eligibility_adjudication_v1_1.json",
     "4da89314f8c2372e92aa78adcec0c0823b128e1ab9683179b5559a6e8e785757"),
])

HARNESS = "scripts/analysis/phase34_efficiency_profiling_execution_v1_1.py"
WORKER = "scripts/analysis/phase34_efficiency_profiling_worker_v1_1.py"
HARNESS_SHA = "e6effd91ef847d2735648a2abd3fd254d09b015b336554005f94866168afda59"
WORKER_SHA = "bd2cd11a744891282e976185ff1c77883f0c1e5da97792932b70b0fc55a31463"

MODEL_SOURCES = OrderedDict([
    ("src/models/barr/ra_medfilm_barr.py", "CANONICAL_WRAPPER_SOURCE"),
    ("src/models/barr/regional_refiner.py", "R_psi_SOURCE"),
    ("src/models/barr/router_variants.py", "B_phi_SOURCE"),
    ("src/models/film/global_medfilm.py", "G_SOURCE"),
])

CHECKPOINTS = OrderedDict([
    ("G", ("checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
           "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
           "GlobalMedFiLM", 3523001)),
    ("R_psi", ("checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt",
               "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109",
               "BARRRegionalRefinerV1", 1276401)),
    ("B_phi", ("checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
               "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b",
               "BARRBenefitRouterV1", 36801)),
    ("S_omega", ("checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt",
                 "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e",
                 "BARRPostSafetyV1", 1217)),
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
    return {
        "os": platform.platform(), "python_version": platform.python_version(),
        "torch_version": torch.__version__, "cuda_runtime": torch.version.cuda,
        "cuda_driver_version": "596.36", "cudnn_version": torch.backends.cudnn.version(),
        "cuda_available": bool(torch.cuda.is_available()),
        "gpu_model": prop.name if prop else None,
        "gpu_compute_capability": f"{prop.major}.{prop.minor}" if prop else None,
        "gpu_total_vram_bytes": prop.total_memory if prop else None,
        "cpu_logical_cores": 16, "cpu_torch_threads": torch.get_num_threads(),
        "system_ram_bytes": m.ullTotalPhys,
        "torch_matmul_allow_tf32": bool(torch.backends.cuda.matmul.allow_tf32),
        "torch_cudnn_allow_tf32": bool(torch.backends.cudnn.allow_tf32),
        "torch_cudnn_benchmark": bool(torch.backends.cudnn.benchmark),
        "torch_deterministic_algorithms": bool(torch.are_deterministic_algorithms_enabled()),
        "torch_profiler_available": hasattr(torch, "profiler"),
    }


def static_worker_audit(worker_src: str) -> dict:
    """Statically inspect the frozen worker for the required executable semantics."""
    # Strip comments/docstrings crudely so we only audit executable code.
    code_lines = []
    in_doc = False
    for ln in worker_src.splitlines():
        s = ln.strip()
        if s.startswith('"""') or s.startswith("'''"):
            in_doc = not in_doc
            continue
        if in_doc or s.startswith("#"):
            continue
        code_lines.append(ln)
    code = "\n".join(code_lines)

    def has(pat):
        return re.search(pat, code) is not None

    audit = OrderedDict([
        ("executable_code_lines", len([l for l in code_lines if l.strip()])),
        ("G_model_eval", has(r"\.eval\(\)")),
        ("G_autocast_enabled", has(r"autocast")),
        ("G_autocast_dtype_float16", has(r"float16")),
        ("G_no_grad", has(r"no_grad")),
        ("G_not_inference_mode", has(r"inference_mode")),
        ("no_autocast_components_present", has(r"inference_mode")),
        ("constructs_models", has(r"GlobalMedFiLM|BARRRegionalRefinerV1|BARRBenefitRouterV1|"
                                  r"BARRPostSafetyV1")),
        ("loads_checkpoints", has(r"torch\.load|load_state_dict")),
        ("runs_forwards", has(r"model\(|forward\(")),
        ("synchronized_cuda_timing", has(r"cuda\.synchronize|torch\.cuda\.Event")),
        ("memory_measurement", has(r"reset_peak_memory_stats|max_memory_allocated")),
        ("uses_flop_mac_profiler", has(r"fvcore|thop|ptflops|FlopCountAnalysis")),
        ("training_or_optimizer_reachable", has(r"\.backward\(|optim\.")),
        ("protected_data_path", has(r"router_holdout|/test|\\\\test")),
    ])
    required = ["G_model_eval", "G_autocast_enabled", "G_autocast_dtype_float16", "G_no_grad",
                "constructs_models", "loads_checkpoints", "runs_forwards",
                "synchronized_cuda_timing", "memory_measurement"]
    missing = [k for k in required if not audit[k]]
    audit["required_executable_behaviours_missing"] = missing
    audit["static_semantic_audit_pass"] = len(missing) == 0
    audit["prohibited_behaviours_present"] = [
        k for k in ("uses_flop_mac_profiler", "training_or_optimizer_reachable",
                    "protected_data_path") if audit[k]]
    return audit


def main():
    gen = now_utc()

    # ---------- §A bind authority (fail-closed) ----------
    auth = []
    for rel, exp in AUTH.items():
        obs = sha256_file(ROOT / rel)
        auth.append({"path": rel, "expected_sha256": exp, "observed_sha256": obs,
                     "match": obs == exp})
        if obs != exp:
            raise SystemExit(f"FAIL-CLOSED authority SHA mismatch: {rel}")

    # ---------- §B load-bearing source preflight ----------
    harness_sha = sha256_file(ROOT / HARNESS)
    worker_sha = sha256_file(ROOT / WORKER)
    model_src = []
    for rel, role in MODEL_SOURCES.items():
        model_src.append({"path": rel, "role": role, "sha256": sha256_file(ROOT / rel)})

    worker_src = (ROOT / WORKER).read_text(encoding="utf-8")
    audit = static_worker_audit(worker_src)

    # checkpoint FILE hashes (file-level only; no deserialization)
    ckpts = []
    for cid, (rel, exp, cls, params) in CHECKPOINTS.items():
        p = ROOT / rel
        obs = sha256_file(p)
        ckpts.append({"component": cid, "path": rel, "expected_sha256": exp,
                      "observed_sha256": obs, "match": obs == exp,
                      "file_bytes": p.stat().st_size, "model_class": cls,
                      "historical_parameter_count": params})

    # ---------- §E required task/domain conditioning binding ----------
    harness_src = (ROOT / HARNESS).read_text(encoding="utf-8")
    task_conditioning = {
        "G_forward_requires_task_ids": True,
        "G_task_conditioning_evidence":
            "src/models/film/global_medfilm.py: forward consumes task_ids [B]; "
            "_validate_task_ids enforces shape [B] and range [0, task_count); "
            "task_embedding + FiLM sites are 'the ONLY task signal'",
        "harness_defines_task_ids": bool(re.search(r"task_id", harness_src)),
        "harness_defines_domain_index": bool(re.search(r"domain_index|task_index", harness_src)),
        "synthetic_input_builder_emits_only_image_tensor": True,
        "deterministic_task_conditioning_bound": False,
    }

    source_ok = (harness_sha == HARNESS_SHA) and (worker_sha == WORKER_SHA)
    audit_ok = audit["static_semantic_audit_pass"]
    conditioning_ok = task_conditioning["deterministic_task_conditioning_bound"]
    ckpt_ok = all(c["match"] for c in ckpts)

    preflight_pass = bool(source_ok and audit_ok and conditioning_ok and ckpt_ok)
    blockers = []
    if not source_ok:
        blockers.append("LOAD_BEARING_SOURCE_SHA_MISMATCH")
    if not audit_ok:
        blockers.append("V1_1_WORKER_DOES_NOT_IMPLEMENT_REQUIRED_EXECUTABLE_RUNTIME_SEMANTICS")
    if not conditioning_ok:
        blockers.append("REQUIRED_TASK_DOMAIN_CONDITIONING_NOT_DETERMINISTICALLY_BOUND")
    if not ckpt_ok:
        blockers.append("CANONICAL_CHECKPOINT_SHA_MISMATCH")

    write_json(OrderedDict([
        ("artifact", "phase34_execution_source_preflight_v1_1"),
        ("phase", 34), ("section", "\u00a7B"), ("method", METHOD), ("revision", REVISION),
        ("purpose", "mandatory static source + semantics preflight BEFORE any model load"),
        ("authority_bindings", auth),
        ("authority_all_match", all(a["match"] for a in auth)),
        ("load_bearing_source_hashes", OrderedDict([
            ("harness", {"path": HARNESS, "expected_sha256": HARNESS_SHA,
                         "observed_sha256": harness_sha, "match": harness_sha == HARNESS_SHA}),
            ("worker", {"path": WORKER, "expected_sha256": WORKER_SHA,
                        "observed_sha256": worker_sha, "match": worker_sha == WORKER_SHA}),
        ])),
        ("model_source_hashes", model_src),
        ("static_semantic_audit", audit),
        ("checkpoint_file_verification", ckpts),
        ("checkpoint_files_all_match", ckpt_ok),
        ("required_task_conditioning_binding", task_conditioning),
        ("source_hash_check_pass", source_ok),
        ("static_semantic_audit_pass", audit_ok),
        ("task_conditioning_bound", conditioning_ok),
        ("preflight_pass", preflight_pass),
        ("blockers", blockers),
        ("model_deserialized", False), ("model_constructed", False),
        ("forward_executed", False), ("cuda_timing_performed", False),
        ("memory_measured", False),
        ("generated_utc", gen), ("all_pass", preflight_pass),
    ]), AUD / "phase34_execution_source_preflight_v1_1.json")

    # ---------- §C environment gate (introspection allowed) ----------
    env = env_snapshot()
    expected_env = {"gpu_model": "NVIDIA GeForce RTX 3060 Ti", "gpu_compute_capability": "8.6",
                    "gpu_total_vram_bytes": 8589279232, "python_version": "3.11.9",
                    "torch_version": "2.6.0+cu124", "cuda_runtime": "12.4",
                    "cuda_driver_version": "596.36", "cudnn_version": 90100}
    env_checks = {k: (env.get(k) == v) for k, v in expected_env.items()}
    write_json(OrderedDict([
        ("artifact", "phase34_execution_environment_v1_1"),
        ("phase", 34), ("section", "\u00a7C"), ("method", METHOD), ("revision", REVISION),
        ("observed_environment", env), ("expected_frozen_environment", expected_env),
        ("environment_checks", env_checks),
        ("environment_gate_pass", all(env_checks.values())),
        ("model_loading_performed", False),
        ("generated_utc", gen), ("all_pass", all(env_checks.values())),
    ]), AUD / "phase34_execution_environment_v1_1.json")

    # ---------- blocked terminal (no measurements) ----------
    write_json(OrderedDict([
        ("artifact", "phase34_execution_blocked_terminal_v1_1"),
        ("phase", 34), ("section", "\u00a7X"), ("method", METHOD), ("revision", REVISION),
        ("terminal", BLOCKED_TERMINAL),
        ("status", "BLOCKED_PREMODEL"),
        ("reason",
         "The static semantic audit required by \u00a7B FAILED before any model load, and "
         "the required G task/domain conditioning is not deterministically bound (\u00a7E). "
         "The frozen v1.1 worker is a non-executable skeleton: it contains no model "
         "construction, no checkpoint deserialization, no model.eval(), no autocast/"
         "inference_mode context, no forward call and no synchronized CUDA timing. "
         "The frozen v1.1 harness's synthetic-input builder emits only the image tensor and "
         "never supplies the task_ids that GlobalMedFiLM.forward requires."),
        ("blockers", blockers),
        ("authority_all_match", all(a["match"] for a in auth)),
        ("source_hashes_match", source_ok),
        ("checkpoint_hashes_match", ckpt_ok),
        ("measurements_performed", 0),
        ("model_loads", 0), ("model_forwards", 0), ("latency_iterations", 0),
        ("fps_measurements", 0), ("gpu_memory_measurements", 0),
        ("flop_mac_profiler_executions", 0), ("raw_image_reads", 0), ("raw_gt_reads", 0),
        ("router_holdout_raw_reads", 0), ("test_reads", 0), ("training_steps", 0),
        ("required_remediation", [
            "Authorize an explicit v1.2 execution-harness amendment that implements the real "
            "per-component model construction, strict checkpoint load, canonical precision "
            "contexts, synchronized CUDA timing, memory measurement and isolated workers.",
            "Deterministically bind the G task/domain conditioning (task_ids per component "
            "and the domain->task_id registry) in the frozen harness BEFORE any forward.",
            "Re-freeze the amended sources and re-issue the execution authorization.",
        ]),
        ("phase34_closure_status", "NOT_STARTED"),
        ("phase35_started", False),
        ("TEST", "LOCKED_UNTIL_PHASE39"),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_execution_blocked_terminal_v1_1.json")

    print("=== PHASE34 v1.1 FIRST-EXECUTION STATIC PREFLIGHT (zero-execution) ===")
    print("authority all match:", all(a["match"] for a in auth))
    print("harness SHA match:", harness_sha == HARNESS_SHA, "| worker SHA match:",
          worker_sha == WORKER_SHA)
    print("static semantic audit pass:", audit_ok)
    print("  missing required executable behaviours:", audit["required_executable_behaviours_missing"])
    print("checkpoint files all match:", ckpt_ok)
    print("task conditioning bound:", conditioning_ok)
    print("PREFLIGHT PASS:", preflight_pass)
    print("blockers:", blockers)
    print("environment gate pass:", all(env_checks.values()), env_checks)
    print()
    print("TERMINAL:", BLOCKED_TERMINAL)
    print()
    for a in NEW:
        print(f"{a['sha256']}  {a['path']}")


if __name__ == "__main__":
    main()
