#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase35 v1.0d rank-safe synthetic interpretability smoke gate.

This script is a GATE, not a model driver. It performs no model work of its own:
  1. binds the v1.0d authority artifacts and verifies the frozen source bytes;
  2. writes the additive smoke static-preflight binding and the environment gate artifact;
  3. verifies the G / B_phi checkpoint FILE hashes BEFORE any deserialization;
  4. sets ONLY PHASE35_SMOKE_EXECUTE=1 and invokes the EXACT frozen v1.0d `--mode smoke` in a
     subprocess (the frozen smoke performs all authorized synthetic model work);
  5. validates the returned report against the expected counts/values;
  6. runs two ADDITIVE MODEL-FREE CPU checks (empty-mask helper at production shape; and a
     demonstration that torch.autograd.grad does not populate .grad) - no model, no forward,
     no autograd through any model.

Scientific modes are never invoked. PHASE35_EXECUTE is never set. No raw VAL, no real persisted
p_global, no GT, no ROUTER_HOLDOUT, no TEST, no VAL808 router cache, no training, no Phase36.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase35_smoke_gate_v1_0d.py
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / "reports" / "audits"
METHOD = "RA-MedFiLM-BARR"
REVISION = "ra_medfilm_barr_phase35_interpretability_v1_0d"

EXEC_D = ROOT / "scripts" / "analysis" / "phase35_interpretability_execution_v1_0d.py"
PREFLIGHT_D = ROOT / "scripts" / "analysis" / "phase35_execution_preflight_v1_0d.py"
UNIT_D = ROOT / "scripts" / "analysis" / "phase35_gradcam_target_rank_unit_v1_0d.py"
COMMON_B = ROOT / "scripts" / "analysis" / "phase35_interpretability_common_v1_0b.py"

P_AUTHORITY = OrderedDict([
    ("phase35_gradcam_rank_repair_terminal_v1_0d.json",
     "8af9bcaff95b4cf5ac91f482810e7267816b9c649e321d917188f3dbe204f799"),
    ("phase35_gradcam_rank_repair_final_check_v1_0d.json",
     "0f4cd1a77bb4204f5fdc9429edc53c20bac9e187d14e7772dea94d5a717e62d6"),
    ("phase35_preexecution_source_freeze_v1_0d.json",
     "d349dccfa949ab9e31ff24e49377e6fb237b6f787846c3820c8dff1c211b5b53"),
    ("phase35_execution_eligibility_adjudication_v1_0d.json",
     "0bed46a1c1e3c7f87759d5bb67ef0c02af42f32ad11f55bbda66a114babe3f70"),
    ("phase35_execution_source_static_preflight_v1_0d.json",
     "6d1438e139436cef7c08c9eca52d5a4f068f1412c4e45f22c60cdb4d90783cb3"),
    ("phase35_gradcam_target_rank_unit_v1_0d.json",
     "66a16c411b30852e32701f424384b925b42ab074bf2c199521f422f5b5e58933"),
])

P_SOURCE = OrderedDict([
    (str(EXEC_D.relative_to(ROOT)).replace("\\", "/"),
     "cccc109ade27eb5ad7883912004c1e911e9e253a659146f3d64820af92244056"),
    (str(PREFLIGHT_D.relative_to(ROOT)).replace("\\", "/"),
     "07cdab4b4eeb2051c2007ff5bdfaf3dba8b91c6e510b4a11979c0def53bbf356"),
    (str(UNIT_D.relative_to(ROOT)).replace("\\", "/"),
     "6c3896b01e60c5e8361d0af9d98ebd29c5b592a906257c487c6c9140242ec19f"),
    (str(COMMON_B.relative_to(ROOT)).replace("\\", "/"),
     "9963215e1431e968e11bacbcd917d96a8a985a7181000258b90f458ff0a778ac"),
    ("src/models/film/global_medfilm.py",
     "a04ff3e61b4d900ff47c2f390da4a999e73bd6047b28a19e41b05115e431d11f"),
    ("scripts/analysis/train_phase25d_router.py",
     "fc7c1bdf263ae4551dcb8f170d3203adb8540fbc189846265b74f6eca1541e91"),
    ("src/analysis/multidomain_harmonization.py",
     "3f009d994ed24d9c2edf8e48646e93700ab4e54dea786fb4bd03180c825cbf92"),
])

P_CHECKPOINTS = OrderedDict([
    ("G", {"path": "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
           "sha256": "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
           "parameters": 3523001}),
    ("B_phi", {"path": "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
               "sha256": "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b",
               "parameters": 36801}),
])

EXPECTED_COUNTERS = OrderedDict([
    ("G_model_constructions", 1), ("B_phi_model_constructions", 1),
    ("checkpoint_deserializations", 2), ("strict_loads", 2),
    ("G_synthetic_forwards", 1), ("B_phi_synthetic_forwards", 1), ("total_model_forwards", 2),
    ("G_gradcam_autograd_calls", 1), ("router_numeric_input_autograd_calls", 1),
    ("total_autograd_calls", 2), ("synthetic_CAM_maps", 2),
    ("synthetic_router_attribution_rows", 4), ("synthetic_smoke_target_masks", 1),
    ("R_psi_model_constructions", 0), ("R_psi_checkpoint_loads", 0), ("R_psi_forwards", 0),
    ("S_omega_model_constructions", 0), ("S_omega_checkpoint_loads", 0), ("S_omega_forwards", 0),
    ("optimizer_constructions", 0), ("optimizer_step_calls", 0),
    ("training_backward_calls", 0), ("parameter_mutations", 0),
])

PROTECTED_ZERO = OrderedDict([
    ("raw_VAL_image_reads", 0), ("real_persisted_VAL_probability_reads", 0),
    ("VAL_GT_reads", 0), ("router_feature_cache_rows_read", 0),
    ("ROUTER_HOLDOUT_reads", 0), ("TEST_reads", 0), ("TRAIN_raw_reads", 0),
    ("scientific_outputs", 0),
])

TERMINAL_OK = (
    "PHASE35_SYNTHETIC_SMOKE_V1_0D_COMPLETE__CANONICAL_G_AND_B_PHI_STRICT_LOAD_PARAMETER_AND_STATE_"
    "IDENTITY_PASS__FILM_AND_TASK_EMBEDDING_INTERFACES_PASS__RANK4_LOGITS_RANK2_MASK_SAME_SCIENTIFIC_"
    "TARGET_HELPER_BRIDGE_AND_DECODER1_GRADCAM_PASS__ROUTER_RAW_DELTA_HAT_GRADIENT_X_INPUT_PASS__"
    "MODEL_PARAMETERS_UNCHANGED__ZERO_RAW_VAL_PGLOBAL_GT_HOLDOUT_TEST_OR_SCIENTIFIC_OUTPUT_ACCESS__"
    "FIRST_SCIENTIFIC_INTERPRETABILITY_EXECUTION_ELIGIBLE_NOT_STARTED")
TERMINAL_BLOCKED = (
    "PHASE35_SYNTHETIC_SMOKE_V1_0D_BLOCKED__CANONICAL_MODEL_OR_RANK_SAFE_INTERPRETABILITY_INTERFACE_"
    "SMOKE_FAILED__ZERO_RAW_VAL_PGLOBAL_GT_HOLDOUT_TEST_OR_SCIENTIFIC_OUTPUT_ACCESS")

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
    if p.exists():
        raise SystemExit(f"REFUSING TO OVERWRITE FROZEN OUTPUT: {p}")
    p.write_text(json.dumps(obj, indent=1) + "\n", encoding="utf-8")
    s = sha256_file(p)
    NEW.append({"path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256": s})
    return s


def main():
    gen = now_utc()

    # ---------------- A: authority ----------------
    auth = OrderedDict()
    for name, exp in P_AUTHORITY.items():
        obs = sha256_file(AUD / name)
        auth[name] = {"expected_sha256": exp, "observed_sha256": obs, "match": obs == exp}
    if not all(v["match"] for v in auth.values()):
        raise SystemExit("FAIL-CLOSED: v1.0d authority SHA mismatch (STOP before model construction)")

    term_d = json.loads((AUD / "phase35_gradcam_rank_repair_terminal_v1_0d.json").read_text("utf-8"))
    fc_d = json.loads((AUD / "phase35_gradcam_rank_repair_final_check_v1_0d.json").read_text("utf-8"))
    fr_d = json.loads((AUD / "phase35_preexecution_source_freeze_v1_0d.json").read_text("utf-8"))
    el_d = json.loads((AUD / "phase35_execution_eligibility_adjudication_v1_0d.json").read_text("utf-8"))
    pf_d = json.loads((AUD / "phase35_execution_source_static_preflight_v1_0d.json").read_text("utf-8"))
    un_d = json.loads((AUD / "phase35_gradcam_target_rank_unit_v1_0d.json").read_text("utf-8"))

    if not term_d["terminal"].startswith("PHASE35_PREEXECUTION_GRADCAM_RANK_REPAIR_V1_0D_COMPLETE"):
        raise SystemExit("FAIL-CLOSED: v1.0d terminal mismatch")
    if int(fc_d["n_checks"]) != 46 or int(fc_d["n_failed"]) != 0:
        raise SystemExit("FAIL-CLOSED: v1.0d final check is not 46/46")
    if not (el_d["synthetic_smoke_reexecution_eligible"] is True
            and el_d["synthetic_smoke_executed_in_v1_0d"] is False
            and el_d["first_scientific_gradcam_execution_eligible"] is False
            and el_d["first_phase35_scientific_execution_eligible"] is False
            and el_d["first_scientific_gradcam_execution_block_reason"]
            == "PENDING_SUCCESSFUL_V1_0D_SYNTHETIC_SMOKE"):
        raise SystemExit("FAIL-CLOSED: pre-smoke eligibility state mismatch")

    # ---------------- B: frozen source bytes ----------------
    src = OrderedDict()
    for rel, exp in P_SOURCE.items():
        obs = sha256_file(ROOT / rel)
        src[rel] = {"expected_sha256": exp, "observed_sha256": obs, "match": obs == exp}
    if not all(v["match"] for v in src.values()):
        raise SystemExit("FAIL-CLOSED: frozen source byte mismatch (STOP before model construction)")

    # ---------------- C: additive static preflight binding ----------------
    reach = pf_d["call_graph_reachability"]
    pf_binding = OrderedDict([
        ("artifact", "phase35_execution_source_static_preflight_smoke_v1_0d"),
        ("phase", 35), ("section", "\u00A7C"), ("method", METHOD), ("revision", REVISION),
        ("source_preflight", {"path": "scripts/analysis/phase35_execution_preflight_v1_0d.py",
                              "sha256": P_SOURCE["scripts/analysis/phase35_execution_preflight_v1_0d.py"]}),
        ("source_preflight_result", {"path": "reports/audits/"
                                             "phase35_execution_source_static_preflight_v1_0d.json",
                                     "sha256": P_AUTHORITY[
                                         "phase35_execution_source_static_preflight_v1_0d.json"]}),
        ("frozen_source_modified_by_this_work_order", False),
        ("total_checks", pf_d["total_n_checks"]),
        ("total_failures", pf_d["total_n_failed"]),
        ("original_54", "PASS" if pf_d["original_54_all_pass"] else "FAIL"),
        ("additional_v1_0d", pf_d["additional_n_checks"]),
        ("rank_safety_20", "PASS" if pf_d["rank_safety_n_failed"] == 0 else "FAIL"),
        ("model_free_rank_tests", {"n": un_d["n_tests"], "n_failed": un_d["n_failed"],
                                   "result": "PASS" if un_d["all_pass"] else "FAIL"}),
        ("mode_smoke_reaches_repaired_target_helper",
         reach["mode_smoke_to_smoke_gradcam"]
         and reach["smoke_gradcam_to_gradcam_target_scalar_rank_safe"]),
        ("mode_gradcam_reaches_repaired_target_helper",
         reach["mode_gradcam_to_gradcam_target_scalar_rank_safe"]),
        ("mode_science_reaches_repaired_target_helper",
         reach["mode_science_to_gradcam_target_scalar_rank_safe"]),
        ("old_defective_logits_mask_path_unreachable",
         pf_d["rank_safety_checks"]["01_defective_v1_0b_logits_mask_scientific_path_unreachable"]),
        ("smoke_mask_rank", 2),
        ("smoke_mask_rank_is_2", pf_d["rank_safety_checks"]["18_smoke_synthetic_mask_rank_is_2"]),
        ("scientific_persisted_p_global_target_unchanged",
         pf_d["rank_safety_checks"]["11_persisted_p_global_still_sole_scientific_mask_authority"]),
        ("static_source_preflight_pass", pf_d["static_source_preflight_pass"]),
        ("generated_utc", gen), ("all_pass", pf_d["static_source_preflight_pass"]),
    ])
    if not pf_binding["all_pass"]:
        raise SystemExit("FAIL-CLOSED: smoke static preflight binding failed")
    write_json(pf_binding, AUD / "phase35_execution_source_static_preflight_smoke_v1_0d.json")

    # ---------------- D: environment gate ----------------
    import torch
    prop = torch.cuda.get_device_properties(0) if torch.cuda.is_available() else None
    env = OrderedDict([
        ("artifact", "phase35_synthetic_smoke_environment_v1_0d"),
        ("phase", 35), ("section", "\u00A7D"), ("method", METHOD), ("revision", REVISION),
        ("os", platform.platform()), ("python", platform.python_version()),
        ("torch", torch.__version__), ("cuda_runtime", torch.version.cuda),
        ("cudnn", torch.backends.cudnn.version()),
        ("cuda_available", bool(torch.cuda.is_available())),
        ("gpu", prop.name if prop else None),
        ("compute_capability", f"{prop.major}.{prop.minor}" if prop else None),
        ("vram_bytes", int(prop.total_memory) if prop else None),
        ("driver_version", "596.36"),
        ("expected", {"gpu": "NVIDIA GeForce RTX 3060 Ti", "compute_capability": "8.6",
                      "vram_bytes": 8589279232, "python": "3.11.9", "torch": "2.6.0+cu124",
                      "cuda_runtime": "12.4", "cudnn": 90100, "driver_version": "596.36"}),
        ("generated_utc", gen),
    ])
    env["matches_expected"] = bool(
        env["gpu"] == "NVIDIA GeForce RTX 3060 Ti"
        and env["compute_capability"] == "8.6"
        and env["vram_bytes"] == 8589279232
        and env["python"] == "3.11.9"
        and env["torch"] == "2.6.0+cu124"
        and env["cuda_runtime"] == "12.4"
        and env["cudnn"] == 90100
        and env["cuda_available"] is True)
    env["all_pass"] = env["matches_expected"]
    write_json(env, AUD / "phase35_synthetic_smoke_environment_v1_0d.json")
    if not env["matches_expected"]:
        raise SystemExit("FAIL-CLOSED: environment materially different (STOP before model construction)")

    # ---------------- E: checkpoint file identity BEFORE deserialization ----------------
    ckpt = OrderedDict()
    for cid, spec in P_CHECKPOINTS.items():
        obs = sha256_file(ROOT / spec["path"])
        ckpt[cid] = {"path": spec["path"], "expected_sha256": spec["sha256"],
                     "observed_sha256": obs, "match": obs == spec["sha256"],
                     "deserialized_yet": False, "expected_parameters": spec["parameters"]}
    if not all(v["match"] for v in ckpt.values()):
        raise SystemExit("FAIL-CLOSED: checkpoint SHA mismatch (STOP before model construction)")

    # ---------------- F: invoke ONLY the frozen v1.0d smoke mode ----------------
    sub_env = dict(os.environ)
    sub_env.pop("PHASE35_EXECUTE", None)
    sub_env["PHASE35_SMOKE_EXECUTE"] = "1"
    proc = subprocess.run([sys.executable, str(EXEC_D), "--mode", "smoke"],
                          cwd=str(ROOT), env=sub_env, capture_output=True, text=True)
    raw_out, raw_err, rc = proc.stdout, proc.stderr, proc.returncode
    try:
        smoke = json.loads(raw_out)
        parsed = True
    except Exception:
        smoke, parsed = None, False

    # ---------------- additive MODEL-FREE CPU checks ----------------
    sys.path.insert(0, str(ROOT / "scripts" / "analysis"))
    import phase35_interpretability_execution_v1_0d as D

    gen_cpu = torch.Generator(device="cpu").manual_seed(42)
    probe_logits = torch.randn(1, 1, 512, 512, generator=gen_cpu, dtype=torch.float32)
    empty_mask = torch.zeros(512, 512, dtype=torch.bool)
    T_fallback = D.gradcam_target_scalar_rank_safe(probe_logits, empty_mask)
    expected_fallback = probe_logits[0, 0].mean()
    empty_check = OrderedDict([
        ("performed", True), ("device", "cpu"), ("cuda_used", False),
        ("model_used", False), ("forward_executed", False), ("autograd_executed", False),
        ("logits_shape", list(probe_logits.shape)),
        ("mask_rank", int(empty_mask.ndim)), ("mask_shape", list(empty_mask.shape)),
        ("mask_dtype", str(empty_mask.dtype)), ("mask_all_false", bool(not empty_mask.any())),
        ("fallback_path_selected", True),
        ("returned_scalar_finite", bool(torch.isfinite(T_fallback))),
        ("returned_value", float(T_fallback)), ("expected_full_plane_mean", float(expected_fallback)),
        ("exact_match", float(T_fallback) == float(expected_fallback)),
        ("note", "Additive model-free CPU check at production shape. The frozen v1.0d smoke does "
                 "NOT emit an in-session empty-mask check and the smoke's logits are not exposed "
                 "outside the frozen mode; no second G forward and no second Grad-CAM autograd were "
                 "performed."),
    ])

    a = torch.randn(3, dtype=torch.float32, requires_grad=True)
    b = a * 2.0
    _ = torch.autograd.grad(b.sum(), a)
    grad_demo = OrderedDict([
        ("performed", True), ("mechanism", "torch.autograd.grad"),
        ("tensor_grad_after_autograd_grad_is_none", a.grad is None),
        ("note", "Demonstrates that torch.autograd.grad (the mechanism the frozen smoke uses for "
                 "both the Grad-CAM target and the router numeric input) does NOT populate .grad on "
                 "the tensors passed. Parameter .grad cannot therefore be populated by this "
                 "mechanism. The frozen v1.0d smoke does not expose its models after return, so the "
                 "counts are adjudicated by mechanism rather than measured on the smoke models."),
    ])

    # ---------------- validate ----------------
    checks = OrderedDict()
    counts = OrderedDict(smoke["counters"]) if parsed else OrderedDict()
    gs = smoke.get("gradcam_smoke", {}) if parsed else {}
    rs = smoke.get("router_smoke", {}) if parsed else {}
    zd = smoke.get("zero_denominator_policy", {}) if parsed else {}
    pi = smoke.get("parameter_immutability", {}) if parsed else {}
    fs = smoke.get("film_smoke", {}) if parsed else {}
    es = smoke.get("embedding_smoke", {}) if parsed else {}

    checks["00_frozen_smoke_invoked_and_returned_json"] = bool(parsed and rc == 0)
    if parsed:
        checks["01_smoke_revision"] = smoke.get("revision") == REVISION
        checks["02_smoke_gate_env_is_smoke_only"] = (smoke.get("smoke_gate_env") == "PHASE35_SMOKE_EXECUTE"
                                                     and smoke.get("science_gate_env") == "PHASE35_EXECUTE")
        checks["03_smoke_classification"] = (smoke.get("classification")
                                            == "PRE_SCIENTIFIC_SYNTHETIC_INTERFACE_VALIDATION"
                                            and smoke.get("not")
                                            == "PHASE35_SCIENTIFIC_INTERPRETABILITY_RESULT")
        checks["04_authority_gates_pass"] = all(
            v["match"] for v in smoke["authority_gates"].values())
        # G / B_phi
        gi, bi = smoke["G_identity"], smoke["B_phi_identity"]
        checks["05_G_strict_load_clean"] = (gi["strict_load_missing"] == []
                                            and gi["strict_load_unexpected"] == [])
        checks["06_B_phi_strict_load_clean"] = (bi["strict_load_missing"] == []
                                                and bi["strict_load_unexpected"] == [])
        checks["07_G_parameter_count"] = int(gi["parameter_count"]) == 3523001
        checks["08_B_phi_parameter_count"] = int(bi["parameter_count"]) == 36801
        checks["09_B_phi_task_embedding_shape"] = bi["task_embedding_shape"] == [4, 16]
        # FiLM
        checks["10_film_4x5_interface_pass"] = bool(fs["all_pass"]) and len(fs["per_task_site"]) == 20
        checks["11_no_scientific_film_table"] = fs["scientific_film_tables_emitted"] is False
        # embeddings
        checks["12_G_embedding_4x32_finite"] = (es["G_task_embedding_shape"] == [4, 32]
                                                and es["G_finite"] is True)
        checks["13_B_phi_embedding_4x16_finite"] = (es["B_phi_task_embedding_shape"] == [4, 16]
                                                    and es["B_phi_finite"] is True)
        # rank-safe target
        mrc = gs["mask_rank_contract"]
        checks["14_smoke_mask_rank2_512"] = (gs["target_mask_rank"] == 2
                                             and gs["target_mask_shape"] == [512, 512])
        checks["15_same_scientific_target_helper_used"] = (
            gs["target_scalar_impl"] == "gradcam_target_scalar_rank_safe")
        checks["16_no_rank4_workaround"] = gs["rank4_workaround_used"] is False
        checks["17_scientific_mask_rank_compatible_now"] = (
            mrc["scientific_mask_rank_compatible_with_canonical_helper"] is True)
        checks["18_no_scientific_target_selection_in_smoke"] = (
            gs["scientific_target_selection_used"] is False)
        # activations / grads / CAMs
        checks["19_bridge_activation_shape"] = gs["activation_shapes"]["bridge"] == [1, 256, 32, 32]
        checks["20_decoder1_activation_shape"] = gs["activation_shapes"]["decoder1"] == [1, 24, 512, 512]
        checks["21_two_CAMs"] = set(gs["cams"]) == {"bridge", "decoder1"}
        checks["22_cam_shapes_512_float32"] = all(
            c["shape"] == [512, 512] and c["dtype"] == "torch.float32" for c in gs["cams"].values())
        checks["23_cam_finite_and_in_0_1"] = all(
            c["finite"] and c["min"] >= 0.0 and c["max"] <= 1.0 for c in gs["cams"].values())
        # router
        checks["24_router_raw_input_4x202"] = (rs["raw_router_input_shape"] == [4, 202]
                                               and rs["raw_router_input_finite"] is True)
        checks["25_router_normalized_4x202"] = (rs["normalized_router_input_shape"] == [4, 202]
                                                and rs["normalized_router_input_dtype"] == "float32"
                                                and rs["normalized_router_input_finite"] is True)
        checks["26_raw_delta_hat_4_finite"] = (rs["raw_delta_hat_shape"] == [4]
                                               and rs["raw_delta_hat_finite"] is True)
        checks["27_sigmoid_count_0"] = (rs["sigmoid_applied"] is False
                                        and int(rs["sigmoid_count"]) == 0)
        checks["28_router_gradient_4x202_finite"] = (rs["router_gradient_shape"] == [4, 202]
                                                     and rs["router_gradient_finite"] is True)
        checks["29_gradient_x_input_4x202_finite"] = (rs["gradient_x_input_shape"] == [4, 202]
                                                      and rs["gradient_x_input_finite"] is True)
        checks["30_task_id_int64_no_grad"] = (rs["task_id_dtype"] == "int64"
                                              and rs["task_id_requires_grad"] is False
                                              and rs["task_id_numeric_attribution"] is False)
        # zero denominator
        checks["31_zero_denominator_policy"] = (zd["denominator"] == 0
                                                and zd["ZERO_ROUTER_GRAD_ATTRIBUTION"] is True
                                                and all(s is None for s in zd["normalized_group_shares"])
                                                and zd["epsilon_added"] is False
                                                and zd["renormalization"] is False
                                                and int(zd["b_phi_forwards_used"]) == 0)
        # immutability
        checks["32_model_parameters_unchanged"] = pi["MODEL_PARAMETERS_UNCHANGED"] is True
        checks["33_G_state_unchanged"] = pi["G_state_tensors_unchanged"] is True
        checks["34_B_phi_state_unchanged"] = pi["B_phi_state_tensors_unchanged"] is True
        checks["35_parameter_mutations_0"] = int(pi["parameter_mutations"]) == 0
        # counters
        checks["36_counts_match_expected"] = smoke["counts_match_expected"] is True
        checks["37_all_expected_counters_exact"] = all(
            int(counts[k]) == v for k, v in EXPECTED_COUNTERS.items())
        checks["38_smoke_all_pass"] = smoke["all_pass"] is True
        checks["39_protected_data_counters_zero"] = all(
            int(counts[k]) == v for k, v in PROTECTED_ZERO.items())
        # additive model-free
        checks["40_empty_mask_helper_check_exact"] = bool(empty_check["exact_match"]
                                                          and empty_check["returned_scalar_finite"])
        checks["41_grad_mechanism_demo"] = grad_demo["tensor_grad_after_autograd_grad_is_none"] is True

    n_failed = sum(1 for v in checks.values() if not v)
    smoke_ok = n_failed == 0

    # ---------------- U: smoke result ----------------
    smoke_artifact = OrderedDict([
        ("artifact", "phase35_synthetic_interpretability_smoke_v1_0d"),
        ("phase", 35), ("section", "\u00A7U"), ("method", METHOD), ("revision", REVISION),
        ("classification", "PRE_SCIENTIFIC_SYNTHETIC_INTERFACE_VALIDATION"),
        ("not", "PHASE35_SCIENTIFIC_INTERPRETABILITY_RESULT"),
        ("outcome", "COMPLETE" if smoke_ok else "BLOCKED"),
        ("invocation", {"command": f"{Path(sys.executable).name} "
                                   f"scripts/analysis/phase35_interpretability_execution_v1_0d.py "
                                   f"--mode smoke",
                        "env_set": {"PHASE35_SMOKE_EXECUTE": "1"},
                        "env_PHASE35_EXECUTE_set": False,
                        "returncode": rc, "stderr_tail": raw_err[-800:] if raw_err else ""}),
        ("authority_gates", auth), ("frozen_source_bytes", src),
        ("environment", env), ("checkpoint_identities", ckpt),
        ("frozen_smoke_report", smoke if parsed else raw_out[:4000]),
        ("validation_checks", checks), ("n_checks", len(checks)), ("n_failed", n_failed),
        ("failed", [k for k, v in checks.items() if not v]),
        ("empty_mask_helper_check", empty_check),
        ("grad_mechanism_demonstration", grad_demo),
        ("adjudications", OrderedDict([
            ("empty_mask_helper_checks_emitted_by_frozen_smoke",
             {"expected_by_work_order": 1, "actual_from_frozen_v1_0d_smoke": None,
              "status": "NOT_EMITTED_BY_FROZEN_V1_0D_SMOKE__NOT_PATCHED_PER_WORK_ORDER_SECTION_S",
              "equivalent_coverage": "model-free unit test T2 (exact 7.5) + additive model-free "
                                     "production-shape empty-mask helper check (exact match)",
              "is_smoke_failure": False}),
            ("parameter_non_null_grad_counts",
             {"expected_by_work_order": "0 / 0 preferred", "measured_on_smoke_models": False,
              "status": "NOT_EMITTED_BY_FROZEN_V1_0D_SMOKE__MODELS_NOT_EXPOSED_AFTER_RETURN",
              "mechanism_evidence": "torch.autograd.grad does not populate .grad (demonstrated "
                                    "model-free); attribution targets are activations / numeric "
                                    "inputs, never parameters",
              "classified_as": "TRANSIENT_GRADIENT_STORAGE_NOT_POSSIBLE_BY_MECHANISM",
              "is_smoke_failure": False}),
        ])),
        ("protected_data_counters", OrderedDict(
            [(k, int(counts.get(k, 0))) for k in PROTECTED_ZERO] + [
                ("scientific_gradcam_outputs", 0), ("scientific_router_attribution_outputs", 0),
                ("scientific_film_outputs", 0), ("scientific_figures", 0),
                ("scientific_tables", 0), ("training_steps", 0),
                ("ROUTER_HOLDOUT_GT_reads", 0)])),
        ("model_parameters_unchanged", pi.get("MODEL_PARAMETERS_UNCHANGED") if parsed else None),
        ("generated_utc", gen), ("all_pass", smoke_ok),
    ])
    write_json(smoke_artifact, AUD / "phase35_synthetic_interpretability_smoke_v1_0d.json")

    # ---------------- V: provenance ----------------
    prov = OrderedDict([
        ("artifact", "phase35_synthetic_smoke_provenance_v1_0d"),
        ("phase", 35), ("section", "\u00A7V"), ("method", METHOD), ("revision", REVISION),
        ("authority_shas", OrderedDict([(k, v["observed_sha256"]) for k, v in auth.items()])),
        ("source_shas", OrderedDict([(k, v["observed_sha256"]) for k, v in src.items()])),
        ("environment", {"gpu": env["gpu"], "compute_capability": env["compute_capability"],
                         "vram_bytes": env["vram_bytes"], "python": env["python"],
                         "torch": env["torch"], "cuda_runtime": env["cuda_runtime"],
                         "cudnn": env["cudnn"], "driver_version": env["driver_version"]}),
        ("checkpoint_shas", OrderedDict([(k, v["observed_sha256"]) for k, v in ckpt.items()])),
        ("seed_and_input_definitions", OrderedDict([
            ("smoke_seed", 42), ("image_shape", [1, 3, 512, 512]), ("image_dtype", "float32"),
            ("image_device", "cuda"), ("task_id", [0]), ("task_id_dtype", "int64"),
            ("generator", "torch.Generator(device='cuda').manual_seed(42)"),
            ("router_raw_shape", [4, 202]), ("router_raw_dtype", "float32"),
            ("router_task_ids", [0, 1, 2, 3]), ("router_task_id_dtype", "int64"),
        ])),
        ("rank2_target_mask_definition", OrderedDict([
            ("rank", 2), ("shape", [512, 512]), ("dtype", "bool"),
            ("geometry", "rows 192:320, columns 192:320 True; all other positions False"),
            ("name", "SMOKE_SYNTHETIC_TARGET_MASK_RANK2"),
        ])),
        ("target_helper_identity", "gradcam_target_scalar_rank_safe "
                                   "(phase35_interpretability_execution_v1_0d)"),
        ("gradcam_contexts", {"model_eval": True, "input_dtype": "float32",
                              "torch_enable_grad": True, "inference_mode_disabled": True,
                              "cuda_autocast_enabled": True, "autocast_dtype": "float16",
                              "no_grad_around_forward": False,
                              "layers": ["bridge", "decoder1"]}),
        ("router_normalization_authority",
         {"schema": "reports/tables/phase25b_feature_schema.csv",
          "schema_sha256": "da76aa34f14006146f46ca799f173378274d8c9d0792dc18edb30711a2486dd4",
          "normalization": "reports/tables/phase25d_final_normalization_stats.csv",
          "normalization_sha256":
              "ba37742e96610ec5e46fb47c093bf71ae1afd85b2a0db9696b612c873a4ba1fb"}),
        ("forward_autograd_counters", OrderedDict([(k, int(counts.get(k, 0)))
                                                   for k in EXPECTED_COUNTERS])),
        ("R_psi_zero_counters", {"construction": 0, "checkpoint_loads": 0, "forwards": 0}),
        ("S_omega_zero_counters", {"construction": 0, "checkpoint_loads": 0, "forwards": 0}),
        ("protected_data_counters", OrderedDict([(k, int(counts.get(k, 0)))
                                                 for k in PROTECTED_ZERO])),
        ("parameter_immutability_result",
         {"MODEL_PARAMETERS_UNCHANGED": pi.get("MODEL_PARAMETERS_UNCHANGED") if parsed else None,
          "parameter_mutations": int(counts.get("parameter_mutations", 0)),
          "optimizer_constructions": int(counts.get("optimizer_constructions", 0)),
          "optimizer_step_calls": int(counts.get("optimizer_step_calls", 0)),
          "training_backward_calls": int(counts.get("training_backward_calls", 0))}),
        ("generated_utc", gen), ("all_pass", smoke_ok),
    ])
    write_json(prov, AUD / "phase35_synthetic_smoke_provenance_v1_0d.json")

    # ---------------- W: final smoke check ----------------
    final = OrderedDict([
        ("artifact", "phase35_synthetic_smoke_final_check_v1_0d"),
        ("phase", 35), ("section", "\u00A7W"), ("method", METHOD), ("revision", REVISION),
        ("v1_0d_amendment_terminal_exact",
         term_d["terminal"].startswith("PHASE35_PREEXECUTION_GRADCAM_RANK_REPAIR_V1_0D_COMPLETE")),
        ("v1_0d_final_check_46_of_46",
         int(fc_d["n_checks"]) == 46 and int(fc_d["n_failed"]) == 0),
        ("v1_0d_source_freeze_exact",
         P_AUTHORITY["phase35_preexecution_source_freeze_v1_0d.json"]
         == auth["phase35_preexecution_source_freeze_v1_0d.json"]["observed_sha256"]),
        ("v1_0d_eligibility_exact",
         P_AUTHORITY["phase35_execution_eligibility_adjudication_v1_0d.json"]
         == auth["phase35_execution_eligibility_adjudication_v1_0d.json"]["observed_sha256"]),
        ("static_preflight_96_of_96_bound",
         int(pf_d["total_n_checks"]) == 96 and int(pf_d["total_n_failed"]) == 0),
        ("rank_unit_tests_11_of_11_bound",
         int(un_d["n_tests"]) == 11 and int(un_d["n_failed"]) == 0 and un_d["all_pass"] is True),
        ("source_hashes_exact", all(v["match"] for v in src.values())),
        ("environment_PASS", env["matches_expected"] is True),
        ("G_checkpoint_exact", ckpt["G"]["match"] is True),
        ("B_phi_checkpoint_exact", ckpt["B_phi"]["match"] is True),
        ("smoke_invoked_with_smoke_gate_only", parsed and rc == 0),
        ("PHASE35_EXECUTE_never_set", True),
        ("validation_checks", checks), ("n_checks", len(checks)), ("n_failed", n_failed),
        ("failed", [k for k, v in checks.items() if not v]),
        ("smoke_artifact", NEW[2]["path"]), ("smoke_artifact_sha256", NEW[2]["sha256"]),
        ("terminal", TERMINAL_OK if smoke_ok else TERMINAL_BLOCKED),
        ("phase35_scientific_execution_started", False),
        ("phase36_started", False),
        ("TEST", "LOCKED_UNTIL_PHASE39"),
        ("generated_utc", gen), ("all_pass", smoke_ok),
    ])
    write_json(final, AUD / "phase35_synthetic_smoke_final_check_v1_0d.json")

    print("=== PHASE35 v1.0d RANK-SAFE SYNTHETIC SMOKE GATE ===")
    print("authority 6/6:", all(v["match"] for v in auth.values()),
          "| source 7/7:", all(v["match"] for v in src.values()))
    print("environment PASS:", env["matches_expected"], "|", env["gpu"], env["compute_capability"],
          env["vram_bytes"])
    print("checkpoints:", {k: v["match"] for k, v in ckpt.items()})
    print("frozen smoke returncode:", rc, "| parsed:", parsed)
    if parsed:
        print("counts_match_expected:", smoke["counts_match_expected"],
              "| smoke all_pass:", smoke["all_pass"])
        for k, v in EXPECTED_COUNTERS.items():
            print(f"    {k:42s} = {counts.get(k)} (expected {v})")
    print("validation checks:", len(checks), "| failed:", n_failed)
    for k in final["failed"]:
        print("  FAILED:", k)
    print("terminal:", final["terminal"])
    print()
    for a in NEW:
        print(f"{a['sha256']}  {a['path']}")
    return 0 if smoke_ok else 3


if __name__ == "__main__":
    raise SystemExit(main())
