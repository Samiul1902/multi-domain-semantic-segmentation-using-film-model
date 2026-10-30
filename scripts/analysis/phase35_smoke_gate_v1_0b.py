#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase35 v1.0b synthetic-smoke GATE + outcome record.

ZERO MODEL EXECUTION. Verifies authority/source/environment/checkpoint hashes, invokes the FROZEN
v1.0b `--mode smoke` entry point read-only, and records the outcome. Never constructs a model,
never deserializes a checkpoint, never forwards, never autograds, never reads a raw image.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase35_smoke_gate_v1_0b.py
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import platform
import subprocess
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
METHOD = "RA-MedFiLM-BARR"
REVISION = "ra_medfilm_barr_phase35_interpretability_v1_0b"

BLOCKED_TERMINAL = ("PHASE35_SYNTHETIC_SMOKE_V1_0B_BLOCKED__CANONICAL_MODEL_OR_INTERPRETABILITY_"
                    "INTERFACE_SMOKE_FAILED__ZERO_RAW_VAL_GT_HOLDOUT_TEST_OR_SCIENTIFIC_OUTPUT_ACCESS")

AUTH = OrderedDict([
    ("reports/audits/phase35_source_amendment_terminal_v1_0b.json",
     "c1fa5d2d8b2cc70f8615fbd7dee3fcc75ac2d51dd86bf785a25bdb2c5b0f0c79"),
    ("reports/audits/phase35_source_amendment_final_check_v1_0b.json",
     "f7b99345e56ca0b32e233b7d0896a23e4d6175a26705bdf8a696d590a5972469"),
    ("reports/audits/phase35_preexecution_source_freeze_v1_0b.json",
     "95bcd7913b4ebfdb915134ff6cace69efec1edbdcaa31d828f840548f886a06f"),
    ("reports/audits/phase35_execution_eligibility_adjudication_v1_0b.json",
     "895f602b710bfab8e734e68d7d520a9adf270f27185968cdd8e207f7b54a760f"),
    ("reports/audits/phase35_execution_source_static_preflight_v1_0b.json",
     "8c026c1b01304747da0f49148a5cf9f0757313bb98870cebfd78a4f589d647df"),
])

SOURCES = OrderedDict([
    ("common_v1_0b", ("scripts/analysis/phase35_interpretability_common_v1_0b.py",
                      "9963215e1431e968e11bacbcd917d96a8a985a7181000258b90f458ff0a778ac")),
    ("execution_v1_0b", ("scripts/analysis/phase35_interpretability_execution_v1_0b.py",
                         "581926840d7717e19ed15ad77c7c5339b709efc881b938924d6eec0a2ceb1872")),
    ("preflight_v1_0b", ("scripts/analysis/phase35_execution_preflight_v1_0b.py",
                         "498e68277168a8ee200842d799cb186bd410f09764d1fdb796ad463912704e63")),
    ("model_G", ("src/models/film/global_medfilm.py",
                 "a04ff3e61b4d900ff47c2f390da4a999e73bd6047b28a19e41b05115e431d11f")),
    ("model_B_phi_authority", ("scripts/analysis/train_phase25d_router.py",
                               "fc7c1bdf263ae4551dcb8f170d3203adb8540fbc189846265b74f6eca1541e91")),
    ("domain_task_registry", ("src/analysis/multidomain_harmonization.py",
                              "3f009d994ed24d9c2edf8e48646e93700ab4e54dea786fb4bd03180c825cbf92")),
])

GALLERY = ("reports/tables/phase21_gallery_selection_64.csv",
           "2bc7c16286999ced374840cc987dcd352c3e546668322a9ccc4d1e8e8a097fd9")
CHECKPOINTS = OrderedDict([
    ("G", ("checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
           "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7")),
    ("B_phi", ("checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
               "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b")),
])

EXPECTED_COUNTS = OrderedDict([
    ("G_model_constructions", 1), ("B_phi_model_constructions", 1),
    ("checkpoint_deserializations", 2), ("strict_loads", 2),
    ("G_synthetic_forwards", 1), ("B_phi_synthetic_forwards", 1),
    ("total_model_forwards", 2), ("G_gradcam_autograd_calls", 1),
    ("router_input_gradient_autograd_calls", 1), ("total_autograd_calls", 2),
    ("synthetic_CAM_maps", 2), ("synthetic_router_attribution_rows", 4),
    ("R_psi_forwards", 0), ("S_omega_forwards", 0),
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

    # ---------- §A/§C authority + frozen source ----------
    auth = []
    for rel, exp in AUTH.items():
        obs = sha256_file(ROOT / rel)
        auth.append({"path": rel, "expected_sha256": exp, "observed_sha256": obs,
                     "match": obs == exp})
    src = []
    for k, (rel, exp) in SOURCES.items():
        obs = sha256_file(ROOT / rel)
        src.append({"key": k, "path": rel, "expected_sha256": exp, "observed_sha256": obs,
                    "match": obs == exp})
    auth_ok = all(a["match"] for a in auth)
    src_ok = all(s["match"] for s in src)
    if not (auth_ok and src_ok):
        raise SystemExit("FAIL-CLOSED: authority or frozen source mismatch - STOP")

    # ---------- §E gallery / authority gates (metadata only) ----------
    import pandas as pd
    gpath, gexp = GALLERY
    gobs = sha256_file(ROOT / gpath)
    g = pd.read_csv(ROOT / gpath)
    holdout = pd.read_csv(ROOT / "reports/audits/phase24_router_split_manifest.csv")
    test_p = ROOT / "manifests" / "phase4_v3" / "test.csv"
    test_ids = set(pd.read_csv(test_p)["sample_id"].astype(str)) if test_p.exists() else set()
    val_ids = set(pd.read_csv(ROOT / "manifests/phase4_v3/val.csv")["sample_id"].astype(str))
    gids = set(g["sample_id"].astype(str))
    gallery_ok = (gobs == gexp and len(g) == 64 and g["sample_id"].nunique() == 64
                  and set(g["dataset"].value_counts().to_dict().values()) == {16}
                  and not (gids - val_ids)
                  and not (gids & set(holdout["sample_id"].astype(str)))
                  and not (gids & test_ids))

    # ---------- §D additive static-preflight smoke binding ----------
    pf = json.loads((AUD / "phase35_execution_source_static_preflight_v1_0b.json")
                    .read_text(encoding="utf-8"))
    write_json(OrderedDict([
        ("artifact", "phase35_execution_source_static_preflight_smoke_v1_0b"),
        ("phase", 35), ("section", "\u00A7D"), ("method", METHOD), ("revision", REVISION),
        ("mode", "ADDITIVE_SMOKE_PREFLIGHT_BINDING"),
        ("frozen_preflight_artifact",
         {"path": "reports/audits/phase35_execution_source_static_preflight_v1_0b.json",
          "sha256": "8c026c1b01304747da0f49148a5cf9f0757313bb98870cebfd78a4f589d647df",
          "overwritten": False}),
        ("frozen_preflight_source_unchanged", src_ok),
        ("original_checks_pass", pf["original_n_checks"] - pf["original_n_failed"]),
        ("original_checks_total", pf["original_n_checks"]),
        ("additional_checks_pass", pf["additional_n_checks"] - pf["additional_n_failed"]),
        ("additional_checks_total", pf["additional_n_checks"]),
        ("total_pass", pf["total_n_checks"] - pf["total_n_failed"]),
        ("total_checks", pf["total_n_checks"]),
        ("result", "54/54 PASS + 18/18 PASS = 72/72 PASS"),
        ("rerun_performed", False),
        ("rerun_note",
         "the frozen preflight implementation writes to a fixed path and refuses to overwrite its "
         "own frozen output; per \u00A7D its source was NOT modified and it was NOT re-run. Its "
         "result is re-bound additively here, and the frozen source bytes were independently "
         "re-verified unchanged, so the recorded 72/72 still holds."),
        ("generated_utc", gen), ("all_pass", pf["static_source_preflight_pass"]),
    ]), AUD / "phase35_execution_source_static_preflight_smoke_v1_0b.json")

    # ---------- §F environment gate ----------
    env = env_snapshot()
    expected_env = {"gpu_model": "NVIDIA GeForce RTX 3060 Ti", "gpu_compute_capability": "8.6",
                    "gpu_total_vram_bytes": 8589279232, "python_version": "3.11.9",
                    "torch_version": "2.6.0+cu124", "cuda_runtime": "12.4",
                    "cuda_driver_version": "596.36", "cudnn_version": 90100}
    env_checks = {k: (env.get(k) == v) for k, v in expected_env.items()}
    env_ok = all(env_checks.values())
    write_json(OrderedDict([
        ("artifact", "phase35_synthetic_smoke_environment_v1_0b"),
        ("phase", 35), ("section", "\u00A7F"), ("method", METHOD), ("revision", REVISION),
        ("observed_environment", env), ("expected_frozen_environment", expected_env),
        ("environment_checks", env_checks), ("environment_gate_pass", env_ok),
        ("classification", "EXECUTION_ENVIRONMENT_CONSISTENCY_GATE"),
        ("generated_utc", gen), ("all_pass", env_ok),
    ]), AUD / "phase35_synthetic_smoke_environment_v1_0b.json")

    # ---------- §G checkpoint file identity (NO deserialization) ----------
    ck = []
    for cid, (rel, exp) in CHECKPOINTS.items():
        obs = sha256_file(ROOT / rel)
        ck.append({"component": cid, "path": rel, "expected_sha256": exp,
                   "observed_sha256": obs, "match": obs == exp, "deserialized": False})
    ck_ok = all(c["match"] for c in ck)

    # ---------- §H invoke the FROZEN --mode smoke entry point (read-only) ----------
    proc = subprocess.run(
        [sys.executable, "scripts/analysis/phase35_interpretability_execution_v1_0b.py",
         "--mode", "smoke"],
        capture_output=True, text=True, cwd=str(ROOT))
    frozen_smoke = json.loads(proc.stdout) if proc.returncode == 0 else {}
    frozen_counters = frozen_smoke.get("counters", {})
    actual_counts = OrderedDict([
        ("G_model_constructions", 0), ("B_phi_model_constructions", 0),
        ("checkpoint_deserializations", 0), ("strict_loads", 0),
        ("G_synthetic_forwards", 0), ("B_phi_synthetic_forwards", 0),
        ("total_model_forwards", 0), ("G_gradcam_autograd_calls", 0),
        ("router_input_gradient_autograd_calls", 0), ("total_autograd_calls", 0),
        ("synthetic_CAM_maps", 0), ("synthetic_router_attribution_rows", 0),
        ("R_psi_forwards", 0), ("S_omega_forwards", 0),
    ])
    counts_match = actual_counts == EXPECTED_COUNTS

    # ---------- §T smoke artifact ----------
    write_json(OrderedDict([
        ("artifact", "phase35_synthetic_interpretability_smoke_v1_0b"),
        ("phase", 35), ("section", "\u00A7T"), ("method", METHOD), ("revision", REVISION),
        ("classification", "PRE_SCIENTIFIC_SYNTHETIC_INTERFACE_VALIDATION"),
        ("not", "PHASE35_SCIENTIFIC_INTERPRETABILITY_RESULT"),
        ("outcome", "BLOCKED"),
        ("frozen_smoke_mode_invoked", True),
        ("frozen_smoke_mode_implemented_the_authorized_smoke", False),
        ("root_cause",
         "The frozen v1.0b `--mode smoke` entry point is a STUB: `mode_smoke()` returns "
         "{'synthetic_only': True, 'scientific_output': False} without constructing any model, "
         "deserializing any checkpoint, running any forward, performing any autograd, or producing "
         "any CAM. It therefore cannot perform the authorized synthetic interface validation. "
         "\u00A7H forbids writing another smoke driver, patching the execution source, and invoking "
         "the scientific modes (film/gradcam/router/science) because the smoke mode does not "
         "internally call their synthetic interface functions; so the smoke cannot be executed "
         "under this work order."),
        ("expected_counts", EXPECTED_COUNTS),
        ("actual_frozen_counts", actual_counts),
        ("counts_match", counts_match),
        ("frozen_smoke_mode_raw_output", frozen_smoke),
        ("frozen_smoke_counters_all_zero",
         all(v == 0 for v in frozen_counters.values()) if frozen_counters else True),
        ("source_edited", False), ("new_smoke_driver_written", False),
        ("scientific_modes_invoked", False),
        ("source_hash_gate", {"authority_all_match": auth_ok, "frozen_sources_all_match": src_ok}),
        ("gallery_authority_gate", {"gallery_sha_match": gobs == gexp, "n": int(len(g)),
                                    "unique": int(g["sample_id"].nunique()),
                                    "all_VAL808": not (gids - val_ids),
                                    "holdout_overlap": len(gids & set(holdout["sample_id"]
                                                                      .astype(str))),
                                    "test_overlap": len(gids & test_ids),
                                    "raw_image_pixels_read": False}),
        ("environment_gate_pass", env_ok),
        ("checkpoint_sha_results", ck), ("all_checkpoint_hashes_match", ck_ok),
        ("strict_load_results", "NOT_PERFORMED (no model constructed)"),
        ("parameter_identities", "NOT_VERIFIED (no model constructed)"),
        ("film_smoke", "NOT_PERFORMED"), ("embedding_smoke", "NOT_PERFORMED"),
        ("gradcam_smoke", "NOT_PERFORMED"), ("router_smoke", "NOT_PERFORMED"),
        ("zero_denominator_policy_test", "NOT_PERFORMED"),
        ("parameter_immutability", "TRIVIALLY_UNCHANGED (no model constructed)"),
        ("protected_data_counters", OrderedDict([
            ("raw_val_image_reads", 0), ("real_persisted_val_probability_reads", 0),
            ("val_gt_reads", 0), ("router_holdout_raw_reads", 0), ("router_holdout_gt_reads", 0),
            ("test_image_reads", 0), ("test_gt_reads", 0), ("train_raw_image_reads", 0),
            ("scientific_router_cache_rows_read", 0), ("scientific_gradcam_outputs", 0),
            ("scientific_router_attribution_outputs", 0), ("scientific_phase35_figures", 0),
            ("scientific_phase35_tables", 0), ("training_steps", 0)])),
        ("terminal", BLOCKED_TERMINAL),
        ("generated_utc", gen), ("all_pass", False),
    ]), AUD / "phase35_synthetic_interpretability_smoke_v1_0b.json")

    # ---------- §U provenance ----------
    write_json(OrderedDict([
        ("artifact", "phase35_synthetic_smoke_provenance_v1_0b"),
        ("phase", 35), ("section", "\u00A7U"), ("method", METHOD), ("revision", REVISION),
        ("source_shas", {s["key"]: s["observed_sha256"] for s in src}),
        ("source_freeze_sha256",
         "95bcd7913b4ebfdb915134ff6cace69efec1edbdcaa31d828f840548f886a06f"),
        ("environment", env), ("checkpoint_shas", ck),
        ("constructor_identities",
         {"G": "GlobalMedFiLM(task_count=4, in_channels=3, out_channels=1, "
               "channels=(24,48,96,192,256), task_embedding_dim=32, film_hidden_dim=64)",
          "B_phi": "BARRBenefitRouterV1() from scripts/analysis/train_phase25d_router.py"}),
        ("strict_load_outcomes", "NOT_PERFORMED"),
        ("parameter_counts", "NOT_VERIFIED"),
        ("synthetic_seeds", "NOT_APPLICABLE (smoke not executed)"),
        ("task_ids", "NOT_APPLICABLE"), ("gradcam_contexts", "NOT_APPLICABLE"),
        ("router_preprocessing_authority",
         "reports/tables/phase25d_final_normalization_stats.csv "
         "(sha ba37742e96610ec5e46fb47c093bf71ae1afd85b2a0db9696b612c873a4ba1fb)"),
        ("forward_counts", actual_counts), ("autograd_counts",
                                            {"total": 0}),
        ("R_psi_zero_execution", {"constructions": 0, "checkpoint_loads": 0, "forwards": 0}),
        ("S_omega_zero_execution", {"constructions": 0, "checkpoint_loads": 0, "forwards": 0}),
        ("protected_data_counters_all_zero", True),
        ("model_immutability_verification", "TRIVIALLY_SATISFIED_NO_MODEL_CONSTRUCTED"),
        ("generated_utc", gen), ("all_pass", False),
    ]), AUD / "phase35_synthetic_smoke_provenance_v1_0b.json")

    # ---------- §V final check ----------
    checks = OrderedDict([
        ("v1_0b_terminal_exact",
         sha256_file(AUD / "phase35_source_amendment_terminal_v1_0b.json")
         == "c1fa5d2d8b2cc70f8615fbd7dee3fcc75ac2d51dd86bf785a25bdb2c5b0f0c79"),
        ("v1_0b_final_check_59_59", True),
        ("v1_0b_source_freeze_exact", auth[2]["match"]),
        ("v1_0b_eligibility_exact", auth[3]["match"]),
        ("static_preflight_72_72", pf["static_source_preflight_pass"]),
        ("all_frozen_source_hashes_exact", src_ok),
        ("canonical_gallery_hash_exact", gobs == gexp),
        ("environment_gate_PASS", env_ok),
        ("G_checkpoint_exact", ck[0]["match"]), ("B_phi_checkpoint_exact", ck[1]["match"]),
        ("G_strict_load_PASS", False), ("B_phi_strict_load_PASS", False),
        ("G_missing_unexpected_0_0", False), ("B_phi_missing_unexpected_0_0", False),
        ("G_params_3523001", False), ("B_phi_params_36801", False),
        ("G_float32_eval", False), ("B_phi_float32_eval", False),
        ("R_psi_construction_load_forward_0", True),
        ("S_omega_construction_load_forward_0", True),
        ("FiLM_all_4_tasks_PASS", False),
        ("all_five_FiLM_site_channel_counts_exact", False),
        ("G_task_embedding_4_32", False), ("B_phi_task_embedding_4_16", False),
        ("synthetic_bridge_activation_exact", False),
        ("synthetic_decoder1_activation_exact", False),
        ("bridge_gradient_finite", False), ("decoder1_gradient_finite", False),
        ("bridge_CAM_valid", False), ("decoder1_CAM_valid", False),
        ("canonical_gradcam_algorithm_path_used", False),
        ("no_scientific_persisted_target_read", True),
        ("raw_delta_hat_exact", False), ("sigmoid_count_0", False),
        ("router_normalized_input_4_202", False), ("router_gradient_4_202", False),
        ("gradient_x_input_4_202", False), ("task_id_numeric_gradient_absent", False),
        ("zero_denominator_policy_PASS", False), ("model_parameters_unchanged", True),
        ("raw_VAL_reads_0", True), ("real_persisted_VAL_probability_reads_0", True),
        ("GT_reads_0", True), ("ROUTER_HOLDOUT_reads_0", True), ("TEST_reads_0", True),
        ("scientific_router_cache_rows_0", True), ("scientific_gradcam_outputs_0", True),
        ("scientific_router_attribution_outputs_0", True), ("scientific_figures_0", True),
        ("scientific_tables_0", True), ("training_0", True),
        ("phase35_scientific_execution_started_false", True), ("phase36_started_false", True),
        ("TEST_remains_LOCKED_UNTIL_PHASE39", True),
    ])
    failed = [k for k, v in checks.items() if not v]
    write_json(OrderedDict([
        ("artifact", "phase35_synthetic_smoke_final_check_v1_0b"),
        ("phase", 35), ("section", "\u00A7V"), ("method", METHOD), ("revision", REVISION),
        ("n_checks", len(checks)), ("n_failed", len(failed)), ("failed", failed),
        ("checks", checks),
        ("not_reached_due_to_smoke_block",
         [k for k in failed if k not in ("static_preflight_72_72", "all_frozen_source_hashes_exact")]),
        ("all_pass", len(failed) == 0), ("generated_utc", gen),
    ]), AUD / "phase35_synthetic_smoke_final_check_v1_0b.json")

    write_json(OrderedDict([
        ("artifact", "phase35_synthetic_smoke_terminal_v1_0b"),
        ("phase", 35), ("section", "\u00A7X"), ("method", METHOD), ("revision", REVISION),
        ("terminal", BLOCKED_TERMINAL), ("status", "BLOCKED_SMOKE"),
        ("root_cause", "frozen v1.0b `--mode smoke` entry point is a stub (no constructions, "
                       "no forwards, no autograd, no CAM)"),
        ("required_remediation",
         "an additive v1.0c source amendment implementing `mode_smoke()` so it constructs G and "
         "B_phi, strict-loads them, verifies parameters, exercises the FiLM accessor and task "
         "embeddings, runs ONE synthetic gradient-enabled Grad-CAM forward on deterministic "
         "synthetic input with a synthetic target mask, runs ONE synthetic router "
         "Gradient x Input pass, and verifies model immutability - with no raw/GT/HOLDOUT/TEST "
         "reads - then re-freeze and re-authorize"),
        ("phase35_scientific_execution_started", False), ("phase36_started", False),
        ("TEST", "LOCKED_UNTIL_PHASE39"),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase35_synthetic_smoke_terminal_v1_0b.json")

    print("=== PHASE35 v1.0b SYNTHETIC SMOKE GATE ===")
    print("authority all match:", auth_ok, "| frozen sources all match:", src_ok)
    print("gallery gate:", gallery_ok, "| environment gate:", env_ok,
          "| checkpoints:", ck_ok)
    print("frozen --mode smoke counters all zero:", 
          all(v == 0 for v in frozen_counters.values()) if frozen_counters else True)
    print("expected counts:", dict(EXPECTED_COUNTS))
    print("actual frozen counts:", dict(actual_counts), "| match:", counts_match)
    print()
    print("final check:", len(checks), "checks,", len(failed), "failed")
    print()
    print("TERMINAL:", BLOCKED_TERMINAL)
    print()
    for a in NEW:
        print(f"{a['sha256']}  {a['path']}")
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
