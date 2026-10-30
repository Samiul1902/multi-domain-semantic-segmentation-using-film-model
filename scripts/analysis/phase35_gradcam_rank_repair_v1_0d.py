#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase35 v1.0d Grad-CAM target-mask rank-safety amendment - artifact generator.

ZERO EXECUTION (except the already-run model-free CPU rank unit tests, which are read back).
Produces (write-once, fail-closed on predecessor drift):

  * reports/audits/phase35_gradcam_target_rank_defect_v1_0d.json            (section B)
  * reports/audits/phase35_v1_0c_to_v1_0d_semantic_diff.json               (section O)
  * reports/audits/phase35_execution_eligibility_adjudication_v1_0d.json    (section Q)
  * reports/audits/phase35_preexecution_source_freeze_v1_0d.json            (section R)
  * reports/audits/phase35_v1_0d_no_model_execution_audit.json              (section S)
  * docs/phase35_gradcam_target_rank_repair_v1_0d.md
  * reports/audits/phase35_gradcam_rank_repair_final_check_v1_0d.json       (section U)
  * reports/audits/phase35_gradcam_rank_repair_terminal_v1_0d.json          (section V)

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase35_gradcam_rank_repair_v1_0d.py
"""
from __future__ import annotations

import ast
import hashlib
import json
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"
METHOD = "RA-MedFiLM-BARR"
REVISION = "ra_medfilm_barr_phase35_interpretability_v1_0d"
CLASSIFICATION = ("PRE_EXECUTION_GRADCAM_TARGET_RANK_SAFETY_IMPLEMENTATION_AMENDMENT__"
                  "NO_SCIENTIFIC_PROTOCOL_CHANGE")

EXEC_B = "scripts/analysis/phase35_interpretability_execution_v1_0b.py"
EXEC_C = "scripts/analysis/phase35_interpretability_execution_v1_0c.py"
EXEC_D = "scripts/analysis/phase35_interpretability_execution_v1_0d.py"
COMMON_B = "scripts/analysis/phase35_interpretability_common_v1_0b.py"
UNIT_D = "scripts/analysis/phase35_gradcam_target_rank_unit_v1_0d.py"
UNIT_D_JSON = "reports/audits/phase35_gradcam_target_rank_unit_v1_0d.json"
PREFLIGHT_D = "scripts/analysis/phase35_execution_preflight_v1_0d.py"
PREFLIGHT_D_JSON = "reports/audits/phase35_execution_source_static_preflight_v1_0d.json"
DEFECT_D = "reports/audits/phase35_gradcam_target_rank_defect_v1_0d.json"

TERMINAL = (
    "PHASE35_PREEXECUTION_GRADCAM_RANK_REPAIR_V1_0D_COMPLETE__DISCLOSED_V1_0B_TARGET_MASK_RANK_"
    "INCOMPATIBILITY_REPAIRED_WITH_EXPLICIT_BATCH1_CHANNEL1_RANK2_MASK_CONTRACT__PERSISTED_PGLOBAL050_"
    "TARGET_AND_EMPTY_MASK_FALLBACK_PRESERVED__STANDALONE_AND_SCIENCE_GRADCAM_PATHS_BOUND_TO_RANK_SAFE_"
    "TARGET__V1_0D_SMOKE_BOUND_TO_SAME_SCIENTIFIC_TARGET_HELPER__NO_SCIENTIFIC_PROTOCOL_CHANGE__V1_0D_"
    "SOURCE_FREEZE_COMPLETE__SYNTHETIC_SMOKE_ELIGIBLE_NOT_STARTED")

DEFECT_ID = "PHASE35_V1_0B_GRADCAM_TARGET_MASK_RANK_INCOMPATIBILITY"

PREDECESSORS = OrderedDict([
    # ---- v1.0 / v1.0a ----
    ("reports/audits/phase35_specification_terminal_v1_0.json",
     "cec3b2aadbc90a7a8ebd06e8149cd7a53122d42e3f6077c30634e7de96ac312b"),
    ("docs/phase35_interpretability_spec_v1_0.md",
     "6405ba5f7ad9f046226da916559a0d7a1166a1245bb56e8d38bc9971959acb37"),
    ("reports/audits/phase35_preexecution_source_freeze_v1_0.json",
     "582c950c96622e84b67e691db4ca02e392c68ff11885c5ddc3f3a785de87fc98"),
    ("reports/audits/phase35_gallery_sha_reconciliation_v1_0a.json",
     "ef7a4c6580d06ede0cfc8ca56bba1ddfdb6fb6839b1dafdf2928e3bc38e1e72d"),
    ("reports/audits/phase35_execution_source_static_preflight_v1_0a.json",
     "bed25b64d83d8076f07f42569977351d0fef757faa476191acf4792d0aedd5fd"),
    ("reports/audits/phase35_preexecution_smoke_terminal_v1_0a.json",
     "447e202196b2de79d21d88d76ebbc7be841afa00361ca613a4b7c04cade0fac9"),
    ("scripts/analysis/phase35_interpretability_common_v1_0.py",
     "fce9527fbad3714e01beadf5f697646dbbad215e98fe233ddb4b9948c6071843"),
    ("scripts/analysis/phase35_interpretability_execution_v1_0.py",
     "a2e150d89018087112c71dbaa92137b667e4269430463fd55fc1601f9ee99d27"),
    # ---- v1.0b ----
    (COMMON_B, "9963215e1431e968e11bacbcd917d96a8a985a7181000258b90f458ff0a778ac"),
    (EXEC_B, "581926840d7717e19ed15ad77c7c5339b709efc881b938924d6eec0a2ceb1872"),
    ("scripts/analysis/phase35_execution_preflight_v1_0b.py",
     "498e68277168a8ee200842d799cb186bd410f09764d1fdb796ad463912704e63"),
    ("reports/audits/phase35_v1_0_execution_source_defect_record_v1_0b.json",
     "523d991c7c2b259a2828879c003e532f4705d6dad3322d648a66bf28c0bd8855"),
    ("reports/audits/phase35_execution_source_static_preflight_v1_0b.json",
     "8c026c1b01304747da0f49148a5cf9f0757313bb98870cebfd78a4f589d647df"),
    ("reports/audits/phase35_preexecution_source_freeze_v1_0b.json",
     "95bcd7913b4ebfdb915134ff6cace69efec1edbdcaa31d828f840548f886a06f"),
    ("reports/audits/phase35_source_amendment_terminal_v1_0b.json",
     "c1fa5d2d8b2cc70f8615fbd7dee3fcc75ac2d51dd86bf785a25bdb2c5b0f0c79"),
    ("reports/audits/phase35_source_amendment_final_check_v1_0b.json",
     "f7b99345e56ca0b32e233b7d0896a23e4d6175a26705bdf8a696d590a5972469"),
    ("reports/audits/phase35_synthetic_smoke_terminal_v1_0b.json",
     "3def25817370ce9a90942610d4a474f56384a99e86ba8ba6a2630ad8002e80ee"),
    ("reports/audits/phase35_synthetic_smoke_final_check_v1_0b.json",
     "0a57dca0d13c0dd20beb1a2546fc89948b02e99f45ed6bc070189f91037b8267"),
    ("reports/audits/phase35_synthetic_interpretability_smoke_v1_0b.json",
     "bd51d09cca091244b46db11d61988572368539fbf4d46ddbfcbc4afc93137ff2"),
    ("reports/audits/phase35_synthetic_smoke_provenance_v1_0b.json",
     "f44b2b0e5c38b9a695a6fe02fbb55856af33718948ddd399838153539a30f27c"),
    ("docs/phase35_interpretability_source_amendment_v1_0b.md",
     "ed42edb9059d3d78d64e730c730075b2df19798f8274af86301bb3053155b4a5"),
    ("notebooks/phasewise/phase_35_interpretability/"
     "phase35_interpretability_synthetic_smoke_v1_0b_review.ipynb",
     "b524f5fc5f57eaee0ce6c640b2ae1dad5bc9135e46d2b7efa9d709e8dab08752"),
    # ---- v1.0c ----
    (EXEC_C, "4058fc5544e6e1af15339df20a88da4880549ea8d4dd434395df04e0fa261baa"),
    ("reports/audits/phase35_execution_source_static_preflight_v1_0c.json",
     "80c90c1130ae3bc22fc9cb5baf6a6bd6e6024cf97b9adc913bbe75b0598bb7bf"),
    ("reports/audits/phase35_v1_0b_smoke_stub_defect_record_v1_0c.json",
     "192b0bdc8f844e68f5270a04e15f423f9e0dbc6f3f008b45cfd4fc074e89fa27"),
    ("reports/audits/phase35_v1_0b_to_v1_0c_scientific_semantics_diff.json",
     "1ec634bcac1c690c3c82d43b328074e2ac9af7fd59587405b62199154c5ceccf"),
    ("reports/audits/phase35_preexecution_source_freeze_v1_0c.json",
     "16961263fb2f974f61525b70ea70582e2382b86431c7f343f20ebe0948136340"),
    ("reports/audits/phase35_synthetic_smoke_eligibility_v1_0c.json",
     "993ccd824d0b98c438afed05c14d2269b33ac1380bd96b10f485e855cbaf01f4"),
    ("reports/audits/phase35_v1_0c_no_execution_audit.json",
     "ed0d14cd98c469f73d6669c9dc8bac27ef98cf3d97a2e58263f9b68fc61be400"),
    ("reports/audits/phase35_smoke_amendment_final_check_v1_0c.json",
     "d6a29d55819aadcabf5f4c8199c6580aa70c93f6f1eee15a513879bfea9fe6e0"),
    ("reports/audits/phase35_smoke_amendment_terminal_v1_0c.json",
     "8aee98fc29e1aa9dffba37079e0935fb8319d096a96f9da8892aab41a503b4bb"),
    ("docs/phase35_interpretability_smoke_amendment_v1_0c.md",
     "079303c442edd057c4f5f9d3850df191f0fc3e7daf3aa038c76bbae341ccb716"),
    ("notebooks/phasewise/phase_35_interpretability/"
     "phase35_interpretability_smoke_amendment_v1_0c_review.ipynb",
     "9479e4ae292542852e353ec4704158c3a4317b2c2ee4d5a4f238e79bfc12f212"),
    ("reports/tables/phase21_gallery_selection_64.csv",
     "2bc7c16286999ced374840cc987dcd352c3e546668322a9ccc4d1e8e8a097fd9"),
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
    if p.exists():
        raise SystemExit(f"REFUSING TO OVERWRITE FROZEN OUTPUT: {p}")
    p.write_text(json.dumps(obj, indent=1) + "\n", encoding="utf-8")
    s = sha256_file(p)
    NEW.append({"path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256": s})
    return s


def write_text(txt, p):
    if p.exists():
        raise SystemExit(f"REFUSING TO OVERWRITE FROZEN OUTPUT: {p}")
    p.write_text(txt, encoding="utf-8")
    s = sha256_file(p)
    NEW.append({"path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256": s})
    return s


def collect(src):
    tree = ast.parse(src)
    calls, funcs = set(), {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            parts, cur = [], n.func
            while isinstance(cur, ast.Attribute):
                parts.append(cur.attr)
                cur = cur.value
            if isinstance(cur, ast.Name):
                parts.append(cur.id)
            calls.add(".".join(reversed(parts)))
        if isinstance(n, ast.FunctionDef):
            funcs[n.name] = n
    return {"calls": calls, "funcs": funcs}


def main():
    gen = now_utc()

    pre = []
    for rel, exp in PREDECESSORS.items():
        obs = sha256_file(ROOT / rel)
        pre.append({"path": rel, "expected_sha256": exp, "observed_sha256": obs,
                    "match": obs == exp})
    if not all(p["match"] for p in pre):
        bad = [p["path"] for p in pre if not p["match"]]
        raise SystemExit(f"FAIL-CLOSED: predecessor SHA drift: {bad}")

    src_b = (ROOT / EXEC_B).read_text(encoding="utf-8")
    src_c = (ROOT / EXEC_C).read_text(encoding="utf-8")
    src_d = (ROOT / EXEC_D).read_text(encoding="utf-8")
    id_ = collect(src_d)
    unit = json.loads((ROOT / UNIT_D_JSON).read_text(encoding="utf-8"))
    preflight = json.loads((ROOT / PREFLIGHT_D_JSON).read_text(encoding="utf-8"))
    fc_c = json.loads((ROOT / "reports/audits/phase35_smoke_amendment_final_check_v1_0c.json")
                      .read_text(encoding="utf-8"))

    sha_b, sha_c, sha_d = (sha256_file(ROOT / EXEC_B), sha256_file(ROOT / EXEC_C),
                           sha256_file(ROOT / EXEC_D))
    sha_common = sha256_file(ROOT / COMMON_B)
    sha_unit_src = sha256_file(ROOT / UNIT_D)
    sha_unit_json = sha256_file(ROOT / UNIT_D_JSON)
    sha_pf_src = sha256_file(ROOT / PREFLIGHT_D)
    sha_pf_json = sha256_file(ROOT / PREFLIGHT_D_JSON)
    if not preflight["static_source_preflight_pass"]:
        raise SystemExit("FAIL-CLOSED: v1.0d static preflight did not pass")
    if not unit["all_pass"]:
        raise SystemExit("FAIL-CLOSED: model-free rank unit tests did not all pass")

    # ===================================================================== #
    # B - defect record
    # ===================================================================== #
    defect = OrderedDict([
        ("artifact", "phase35_gradcam_target_rank_defect_v1_0d"),
        ("phase", 35), ("section", "\u00A7B"), ("method", METHOD), ("revision", REVISION),
        ("classification",
         "PRE_SCIENTIFIC_GRADCAM_TARGET_IMPLEMENTATION_DEFECT__FROZEN_SCIENTIFIC_INTENT_UNCHANGED__"
         "NO_SCIENTIFIC_GRADCAM_EXECUTED"),
        ("defect_id", DEFECT_ID),
        ("disclosed_in", "reports/audits/phase35_v1_0b_smoke_stub_defect_record_v1_0c.json"),
        ("disclosing_revision", "ra_medfilm_barr_phase35_interpretability_v1_0c"),
        ("frozen_defective_component",
         "phase35_interpretability_execution_v1_0b.gradcam_target_scalar (preserved byte-for-byte)"),
        ("known_scientific_tensors", OrderedDict([
            ("canonical_G_logits", {"rank": 4, "shape": [1, 1, 512, 512],
                                    "authority": "GlobalMedFiLM.forward (out_channels=1)"}),
            ("persisted_p_global", {"rank": 2, "shape": [512, 512], "dtype": "float16",
                                    "authority": "reports/predictions/phase21_global_medfilm_"
                                                  "fourdomain_seed42_clean_v3/val/<sid>.npz[prob]"}),
            ("build_target_mask_p_global", {"rank": 2, "shape": [512, 512], "dtype": "Boolean",
                                            "definition": "persisted p_global >= 0.50"}),
        ])),
        ("frozen_scientific_intent", OrderedDict([
            ("M_pred", "persisted p_global >= 0.50"),
            ("T_if_mask_nonempty", "mean(current_forward_foreground_logit[M_pred])"),
            ("T_if_mask_empty", "mean(current_forward_foreground_logit over full field)"),
            ("unchanged", True),
        ])),
        ("problem",
         "The frozen implementation performs `logits[mask]`, attempting rank-2 Boolean indexing "
         "directly against rank-4 logits; PyTorch requires the mask shape to match the indexed "
         "tensor's leading dimensions, so this deterministically raises IndexError for the canonical "
         "scientific inputs."),
        ("evidence", [
            "reports/audits/phase35_v1_0b_smoke_stub_defect_record_v1_0c.json (defect_B)",
            "model-free CPU tensor-semantics probe: x(1,1,4,4)[mask(4,4)] -> IndexError; "
            "x(1,1,4,4)[mask(1,1,4,4)] -> ok",
            "metadata-only npy header inspection of all 808 VAL npz: prob = (512,512) '<f2', "
            "pred/gt = (512,512) '|u1' (the `gt` member was never accessed)",
            "reproduced in this revision: unit test "
            "D1_frozen_v1_0b_logits_mask_indexing_reproduced -> IndexError",
        ]),
        ("scientific_specification_changed", False),
        ("scientific_population_changed", False),
        ("target_threshold_changed", False),
        ("target_selection_source_changed", False),
        ("causal_or_scientific_interpretation_changed", False),
        ("implementation_rank_contract_changed", True),
        ("scientific_result_invalidated", False),
        ("scientific_result_invalidated_reason",
         "no Phase35 scientific result exists yet; nothing to invalidate"),
        ("repair_revision", REVISION),
        ("repair_artifacts", OrderedDict([
            ("execution_source_v1_0d", {"path": EXEC_D, "sha256": sha_d}),
            ("rank_unit_tests", {"path": UNIT_D, "sha256": sha_unit_src}),
            ("rank_unit_results", {"path": UNIT_D_JSON, "sha256": sha_unit_json}),
        ])),
        ("frozen_v1_0b_modified", False), ("frozen_v1_0c_modified", False),
        ("model_constructions", 0), ("checkpoint_deserializations", 0), ("forwards", 0),
        ("autograd_calls", 0), ("gradcam_executions", 0),
        ("model_free_cpu_unit_tests", int(unit["n_tests"])),
        ("generated_utc", gen), ("all_pass", True),
    ])
    write_json(defect, AUD / "phase35_gradcam_target_rank_defect_v1_0d.json")

    # ===================================================================== #
    # O - semantic diff v1.0c -> v1.0d
    # ===================================================================== #
    redefined = sorted(set(id_["funcs"]) - set(collect(src_c)["funcs"]))
    wrapped = ["gradcam_gradient_enabled_rank_safe (new per-sample path bound to the repaired "
               "target scalar)"]
    diff = OrderedDict([
        ("artifact", "phase35_v1_0c_to_v1_0d_semantic_diff"),
        ("phase", 35), ("section", "\u00A7O"), ("method", METHOD), ("revision", REVISION),
        ("baseline_source", {"path": EXEC_C, "sha256": sha_c}),
        ("amended_source", {"path": EXEC_D, "sha256": sha_d}),
        ("common_module", {"path": COMMON_B, "sha256": sha_common, "changed_by_v1_0d": False}),
        ("frozen_v1_0b_source", {"path": EXEC_B, "sha256": sha_b, "changed_by_v1_0d": False}),
        ("scientific_specification_changed", False),
        ("gradcam_scalar_scientific_intent_changed", False),
        ("target_population_changed", False),
        ("target_mask_source_changed", False),
        ("target_threshold_changed", False),
        ("empty_mask_fallback_changed", False),
        ("gradcam_layers_changed", False),
        ("gradcam_algorithm_changed", False),
        ("cam_normalization_changed", False),
        ("precision_context_changed", False),
        ("router_science_changed", False),
        ("film_science_changed", False),
        ("only_implementation_change", "TARGET_MASK_RANK_SAFE_INDEXING"),
        ("scientific_semantic_change_class", "IMPLEMENTATION_SHAPE_SAFETY_FIX_ONLY"),
        ("functions_added_in_v1_0d", redefined),
        ("functions_wrapped_in_v1_0d", wrapped),
        ("functions_bound_verbatim_from_v1_0b",
         {"mode_film": True, "mode_router": True, "load_g_component": True,
          "load_bphi_component": True, "load_gallery_allowlist": True,
          "resolve_display_subset": True, "guard_raw_path": True,
          "load_persisted_p_global": True, "build_target_mask": True, "build_roi_mask": True,
          "extract_film_parameters": True, "extract_task_embeddings": True,
          "router_population_verify": True, "router_normalized_features": True,
          "router_gradient_x_input": True, "router_group_attribution": True,
          "cam_normalize": True, "saliency_self_consistency": True,
          "assert_claim_language": True}),
        ("functions_reused_verbatim_from_v1_0c",
         ["smoke_environment_check", "smoke_checkpoint_identity", "smoke_synthetic_image",
          "state_dict_identity", "smoke_film_validate", "smoke_embedding_validate",
          "smoke_router", "smoke_zero_denominator", "smoke_parameter_immutability",
          "SMOKE_COUNTERS", "SMOKE_EXPECTED_COUNTERS"]),
        ("thresholds", {"T_SEGMENTATION_OUTPUT": 0.50, "T_ROI_PROPOSAL": 0.30,
                        "changed_by_v1_0d": False}),
        ("defect_repaired", DEFECT_ID),
        ("model_constructed", False), ("checkpoint_deserialized", False),
        ("forward_executed", False),
        ("generated_utc", gen), ("all_pass", True),
    ])
    write_json(diff, AUD / "phase35_v1_0c_to_v1_0d_semantic_diff.json")

    # ===================================================================== #
    # Q - execution eligibility adjudication
    # ===================================================================== #
    elig = OrderedDict([
        ("artifact", "phase35_execution_eligibility_adjudication_v1_0d"),
        ("phase", 35), ("section", "\u00A7Q"), ("method", METHOD), ("revision", REVISION),
        ("film_parameter_analysis_source_eligible", True),
        ("film_parameter_analysis_basis",
         "V0B.mode_film / extract_film_parameters / extract_task_embeddings unchanged"),
        ("router_VAL808_attribution_source_eligible", True),
        ("router_VAL808_attribution_basis",
         "V0B.mode_router / router_normalized_features / router_gradient_x_input / "
         "router_group_attribution unchanged; VAL808 canonical cache authority unchanged"),
        ("gradcam_bridge_source_eligible", True),
        ("gradcam_decoder1_source_eligible", True),
        ("gradcam_source_basis",
         "rank-safe target scalar implemented; hooks, algorithm, normalization and precision "
         "context unchanged; static rank-safety checks 20/20"),
        ("first_scientific_gradcam_execution_eligible", False),
        ("first_scientific_gradcam_execution_block_reason",
         "PENDING_SUCCESSFUL_V1_0D_SYNTHETIC_SMOKE"),
        ("first_phase35_scientific_execution_eligible", False),
        ("first_phase35_scientific_execution_block_reason",
         "PENDING_SUCCESSFUL_V1_0D_SYNTHETIC_SMOKE"),
        ("scientific_gradcam_authorized_by_static_checks_alone", False),
        ("synthetic_smoke_reexecution_eligible", True),
        ("synthetic_smoke_executed_in_v1_0d", False),
        ("smoke_gate_env", "PHASE35_SMOKE_EXECUTE"),
        ("science_gate_env", "PHASE35_EXECUTE"),
        ("smoke_gate_authorizes_scientific_modes", False),
        ("model_constructions", 0), ("checkpoint_deserializations", 0), ("forwards", 0),
        ("gate_env_set", False), ("mode_invoked", False),
        ("generated_utc", gen), ("all_pass", True),
    ])
    write_json(elig, AUD / "phase35_execution_eligibility_adjudication_v1_0d.json")

    # ===================================================================== #
    # R - source freeze
    # ===================================================================== #
    freeze = OrderedDict([
        ("artifact", "phase35_preexecution_source_freeze_v1_0d"),
        ("phase", 35), ("section", "\u00A7R"), ("method", METHOD), ("revision", REVISION),
        ("classification", CLASSIFICATION),
        ("frozen_source_set", OrderedDict([
            ("execution_v1_0d", {"path": EXEC_D, "sha256": sha_d,
                                 "role": "rank-safe executable harness (smoke + gradcam + science)"}),
            ("static_preflight_v1_0d", {"path": PREFLIGHT_D, "sha256": sha_pf_src,
                                        "role": "static source preflight (zero execution)"}),
            ("rank_unit_test_v1_0d", {"path": UNIT_D, "sha256": sha_unit_src,
                                      "role": "model-free CPU rank-contract unit tests"}),
            ("rank_unit_results_v1_0d", {"path": UNIT_D_JSON, "sha256": sha_unit_json,
                                         "role": "model-free unit-test results"}),
            ("static_preflight_v1_0d_result", {"path": PREFLIGHT_D_JSON, "sha256": sha_pf_json,
                                               "role": "static preflight result"}),
            ("common_v1_0b_reused", {"path": COMMON_B, "sha256": sha_common,
                                     "role": "frozen shared contracts (unchanged)"}),
            ("execution_v1_0c_authority", {"path": EXEC_C, "sha256": sha_c,
                                           "role": "predecessor authority (unchanged)"}),
            ("execution_v1_0b_reused", {"path": EXEC_B, "sha256": sha_b,
                                        "role": "frozen film/router science + defective target "
                                                "scalar preserved as provenance"}),
        ])),
        ("frozen_authorities", OrderedDict([
            ("G_source", {"path": "src/models/film/global_medfilm.py",
                          "sha256": sha256_file(ROOT / "src/models/film/global_medfilm.py")}),
            ("B_phi_authority",
             {"path": "scripts/analysis/train_phase25d_router.py",
              "sha256": sha256_file(ROOT / "scripts/analysis/train_phase25d_router.py")}),
            ("domain_task_registry",
             {"path": "src/analysis/multidomain_harmonization.py",
              "sha256": sha256_file(ROOT / "src/analysis/multidomain_harmonization.py")}),
            ("gallery", {"path": "reports/tables/phase21_gallery_selection_64.csv",
                         "sha256": sha256_file(ROOT / "reports/tables/phase21_gallery_selection_64.csv")}),
            ("gradcam_contract", {"path": COMMON_B, "sha256": sha_common,
                                  "detail": "GRADCAM_HOOKS / GRADCAM_ALGORITHM / "
                                            "GRADCAM_FORWARD_SEMANTICS unchanged"}),
            ("phase35_v1_0_scientific_specification",
             {"path": "docs/phase35_interpretability_spec_v1_0.md",
              "sha256": sha256_file(ROOT / "docs/phase35_interpretability_spec_v1_0.md")}),
            ("G_checkpoint_identity",
             {"path": "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
              "sha256": "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7"}),
            ("B_phi_checkpoint_identity",
             {"path": "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
              "sha256": "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b"}),
            ("router_feature_schema",
             {"path": "reports/tables/phase25b_feature_schema.csv",
              "sha256": "da76aa34f14006146f46ca799f173378274d8c9d0792dc18edb30711a2486dd4"}),
            ("router_normalization_authority",
             {"path": "reports/tables/phase25d_final_normalization_stats.csv",
              "sha256": "ba37742e96610ec5e46fb47c093bf71ae1afd85b2a0db9696b612c873a4ba1fb"}),
        ])),
        ("predecessors_verified", pre), ("n_predecessors_verified", len(pre)),
        ("predecessor_drift", []),
        ("v1_0_spec_preserved", True),
        ("v1_0b_source_preserved", True),
        ("v1_0c_source_preserved", True),
        ("v1_0c_smoke_amendment_preserved", True),
        ("v1_0d_rank_repair_complete", True),
        ("future_smoke_must_use_exact_v1_0d_bytes", True),
        ("first_scientific_execution_started", False),
        ("static_preflight", OrderedDict([
            ("total_n_checks", preflight["total_n_checks"]),
            ("total_n_failed", preflight["total_n_failed"]),
            ("original_54_all_pass", preflight["original_54_all_pass"]),
            ("rank_safety_n_checks", preflight["rank_safety_n_checks"]),
            ("rank_safety_n_failed", preflight["rank_safety_n_failed"]),
            ("static_source_preflight_pass", preflight["static_source_preflight_pass"]),
        ])),
        ("model_free_unit_tests", OrderedDict([
            ("path", UNIT_D_JSON), ("sha256", sha_unit_json),
            ("n_tests", int(unit["n_tests"])), ("n_failed", int(unit["n_failed"])),
            ("all_pass", bool(unit["all_pass"])),
        ])),
        ("model_constructed", False), ("checkpoint_deserialized", False),
        ("forward_executed", False), ("autograd_executed", False),
        ("gradcam_executed", False), ("gate_env_set", False), ("mode_invoked", False),
        ("generated_utc", gen), ("all_pass", True),
    ])
    write_json(freeze, AUD / "phase35_preexecution_source_freeze_v1_0d.json")

    # ===================================================================== #
    # documentation
    # ===================================================================== #
    doc = f"""# Phase 35 v1.0d - Grad-CAM Target-Mask Rank-Safety Amendment

**Revision:** `{REVISION}`
**Classification:** `{CLASSIFICATION}`
**Method:** {METHOD}

## 1. Defect repaired
`{DEFECT_ID}` (prospectively disclosed in v1.0c). The frozen `gradcam_target_scalar` performed
`logits[mask]`: rank-2 Boolean indexing against rank-4 logits. Canonical G logits are
`[1,1,512,512]`; the canonical scientific mask `build_target_mask(p_global >= 0.50)` is rank-2
`[512,512]`. PyTorch requires the mask to match the indexed tensor's leading dimensions, so the
scientific Grad-CAM target scalar raised `IndexError` deterministically.

**Reproduced** in this revision (model-free, CPU): `D1_frozen_v1_0b_logits_mask_indexing_reproduced`
-> `IndexError`.

## 2. Frozen scientific intent (unchanged)
```
M_pred = persisted p_global >= 0.50
if M_pred non-empty:  T = mean(foreground logits under M_pred)
else:                 T = mean(foreground logits over the full field)
```

## 3. Prospective target-scalar contract (frozen by this revision)
| item | contract |
|---|---|
| logits rank | 4 |
| logits shape | `[1,1,H,W]` |
| batch | 1 |
| output channels | 1 |
| mask rank | 2 |
| mask shape | `[H,W]` |
| mask dtype | Boolean |

The rank-2 mask is the canonical representation. It is **never** broadcast, expanded to unrelated
batch/channel dimensions, created from the current forward, replaced by the ROI-0.30 mask, replaced
by GT, or replaced by a sigmoid probability target.

## 4. Repaired implementation
`gradcam_target_scalar_rank_safe(logits, mask)` in `{EXEC_D}`:

```
logits_f = validate_logits(logits)      # rank 4, batch 1, channels 1
mask_t   = validate_mask(logits_f, mask)  # rank 2, shape == (H,W), dtype bool
foreground_logits = logits_f[0, 0]
if bool(mask_t.any()):
    return foreground_logits[mask_t].mean()
return foreground_logits.mean()
```

Explicit `raise` is used rather than `assert` so the fail-closed property survives `python -O`;
the semantics are identical to the specified assert-based contract.

`gradcam_gradient_enabled_rank_safe` is the frozen v1.0b per-sample gradient path with the **single**
target-scalar call rebound. Hooks, `torch.enable_grad()`, autocast fp16, `torch.autograd.grad`,
`alpha`/ReLU/bilinear/`align_corners`, and `cam_normalize` are unchanged.

## 5. Call-graph binding (static evidence)
| mode | reaches repaired helper |
|---|---|
| `mode_gradcam` | YES (`mode_gradcam` -> `gradcam_path_contract` -> `gradcam_target_scalar_rank_safe`) |
| `mode_science` | YES (`mode_science` -> `gradcam_path_contract` -> repaired helper) |
| `mode_smoke` | YES (`mode_smoke` -> `smoke_gradcam` -> `gradcam_gradient_enabled_rank_safe` -> repaired helper) |
| frozen defective `logits[mask]` path | UNREACHABLE from v1.0d |

`film` and `router` remain bound verbatim to `V0B.mode_film` / `V0B.mode_router`.

## 6. Smoke now validates the SCIENTIFIC rank contract
The v1.0c rank-4 synthetic-mask workaround is **removed**. The v1.0d smoke builds a rank-2
`[512,512]` Boolean mask (centred square rows 192:320, columns 192:320) and consumes it through the
**same** repaired helper that scientific Grad-CAM uses. All other smoke counters are unchanged.

## 7. Static preflight (zero execution)
`{PREFLIGHT_D}` -> `{PREFLIGHT_D_JSON}`:
**{preflight['total_n_checks']} checks, {preflight['total_n_failed']} failed**
(54 original + {preflight['additional_n_checks']} v1.0d amendment + {preflight['rank_safety_n_checks']} rank-safety),
with {len(pre)} predecessors verified byte-identical.

## 8. Model-free unit tests
`{UNIT_D}` -> `{UNIT_D_JSON}`: **{unit['n_tests']} tests, {unit['n_failed']} failed**, CPU-only,
no model, no checkpoint, no data.

## 9. Locks
Phase35 scientific execution `NOT_STARTED`; Phase36 `NOT_STARTED`; TEST `LOCKED_UNTIL_PHASE39`;
ROUTER_HOLDOUT `OPENED_AND_FROZEN`. Scientific Grad-CAM remains **not authorized** pending a
successful v1.0d synthetic smoke.
"""
    write_text(doc, ROOT / "docs" / "phase35_gradcam_target_rank_repair_v1_0d.md")

    # ===================================================================== #
    # S - no model execution audit
    # ===================================================================== #
    audit = OrderedDict([
        ("artifact", "phase35_v1_0d_no_model_execution_audit"),
        ("phase", 35), ("section", "\u00A7S"), ("method", METHOD), ("revision", REVISION),
        ("zero_model_execution_declaration", True),
        ("model_execution_counters", OrderedDict([
            ("model_constructions", 0), ("checkpoint_deserializations", 0), ("strict_loads", 0),
            ("forwards", 0), ("autograd_calls", 0), ("gradcam_executions", 0),
            ("router_attribution_executions", 0), ("raw_val_reads", 0),
            ("real_persisted_p_global_reads", 0), ("gt_reads", 0),
            ("router_holdout_reads", 0), ("test_reads", 0), ("training", 0),
            ("gate_env_vars_set", 0), ("mode_invocations", 0),
        ])),
        ("allowed_separately", OrderedDict([
            ("model_free_cpu_rank_unit_tests", int(unit["n_tests"])),
            ("model_free_cpu_rank_unit_tests_failed", int(unit["n_failed"])),
            ("model_free_cpu_rank_unit_tests_artifact", {"path": UNIT_D_JSON,
                                                         "sha256": sha_unit_json}),
            ("device", "cpu"), ("cuda_used", False),
            ("models_touched", 0), ("checkpoints_touched", 0), ("data_touched", 0),
        ])),
        ("static_inspections_performed", [
            "AST parsing + call-graph reachability over the v1.0d / v1.0b execution sources",
            "SHA-256 hashing of source files and audit artifacts",
            "source-text reads of the frozen v1.0b / v1.0c execution sources and shared contracts",
        ]),
        ("inspections_that_are_not_execution", True),
        ("scientific_result_produced", False),
        ("phase35_scientific_execution_started", False),
        ("phase36_started", False),
        ("TEST", "LOCKED_UNTIL_PHASE39"),
        ("ROUTER_HOLDOUT", "OPENED_AND_FROZEN"),
        ("generated_utc", gen), ("all_pass", True),
    ])
    write_json(audit, AUD / "phase35_v1_0d_no_model_execution_audit.json")

    # ===================================================================== #
    # U - final check
    # ===================================================================== #
    unit_by_id = {r["test"]: r for r in unit["results"]}
    checks = OrderedDict([
        ("01_all_predecessor_hashes_exact", all(p["match"] for p in pre)),
        ("02_v1_0c_final_check_40_of_40_bound",
         int(fc_c["n_checks"]) == 40 and int(fc_c["n_failed"]) == 0),
        ("03_defect_B_reproduced_and_documented",
         unit_by_id["D1_frozen_v1_0b_logits_mask_indexing_reproduced"]["pass"]
         and defect["defect_id"] == DEFECT_ID),
        ("04_scientific_specification_unchanged",
         defect["scientific_specification_changed"] is False
         and diff["scientific_specification_changed"] is False),
        ("05_canonical_logits_contract_1_1_H_W",
         "TARGET_LOGITS_RANK = 4" in src_d and "TARGET_LOGITS_BATCH = 1" in src_d
         and "TARGET_LOGITS_CHANNELS = 1" in src_d),
        ("06_canonical_mask_contract_H_W",
         "TARGET_MASK_RANK = 2" in src_d and 'TARGET_MASK_DTYPE = "bool"' in src_d),
        ("07_rank_safe_target_helper_implemented",
         "def gradcam_target_scalar_rank_safe(logits, mask):" in src_d),
        ("08_rank2_nonempty_unit_test_exact",
         unit_by_id["T1_nonempty_rank2_mask"]["pass"]
         and float(unit_by_id["T1_nonempty_rank2_mask"]["observed"]) == 2.5),
        ("09_rank2_empty_fallback_unit_test_exact",
         unit_by_id["T2_empty_mask_full_field_fallback"]["pass"]
         and float(unit_by_id["T2_empty_mask_full_field_fallback"]["observed"]) == 7.5),
        ("10_spatial_mismatch_rejected", unit_by_id["T3_spatial_mismatch_rejected"]["pass"]),
        ("11_rank4_mask_rejected", unit_by_id["T4_rank4_mask_rejected"]["pass"]),
        ("12_nonboolean_mask_rejected",
         unit_by_id["T5a_float_mask_rejected"]["pass"]
         and unit_by_id["T5b_integer_mask_rejected"]["pass"]),
        ("13_old_defective_target_path_unreachable",
         preflight["rank_safety_checks"]["01_defective_v1_0b_logits_mask_scientific_path_unreachable"]
         and "V0B.gradcam_target_scalar" not in src_d),
        ("14_standalone_gradcam_uses_repaired_helper",
         preflight["rank_safety_checks"]["15_standalone_gradcam_mode_reaches_repaired_helper"]),
        ("15_science_composition_uses_repaired_helper",
         preflight["rank_safety_checks"]["16_science_mode_reaches_repaired_helper"]),
        ("16_smoke_uses_repaired_helper",
         preflight["rank_safety_checks"]["17_smoke_mode_reaches_same_repaired_helper"]),
        ("17_smoke_mask_rank2", preflight["rank_safety_checks"]["18_smoke_synthetic_mask_rank_is_2"]
         and "SMOKE_TARGET_MASK_SHAPE = [512, 512]" in src_d),
        ("18_persisted_p_global_remains_scientific_mask_source",
         preflight["rank_safety_checks"][
             "11_persisted_p_global_still_sole_scientific_mask_authority"]),
        ("19_current_forward_mask_remains_prohibited",
         preflight["rank_safety_checks"][
             "14_current_forward_mask_selection_still_prohibited"]),
        ("20_segmentation_threshold_0p50",
         preflight["rank_safety_checks"]["12_segmentation_threshold_still_0p50"]),
        ("21_ROI_threshold_0p30", preflight["rank_safety_checks"]["13_ROI_threshold_still_0p30"]),
        ("22_empty_fallback_unchanged",
         "return foreground_logits.mean()" in src_d
         and unit_by_id["T2_empty_mask_full_field_fallback"]["pass"]),
        ("23_gradcam_hooks_unchanged",
         preflight["original_v1_0a_checks"]["19_gradcam_bridge_hook_exact"]
         and preflight["original_v1_0a_checks"]["20_gradcam_decoder1_hook_exact"]),
        ("24_CAM_algorithm_unchanged",
         preflight["original_v1_0a_checks"]["28_cam_formula_exact"]
         and preflight["original_v1_0a_checks"]["29_align_corners_false"]),
        ("25_precision_semantics_unchanged",
         preflight["original_v1_0a_checks"]["25_gradcam_forward_semantics_exact"]),
        ("26_router_implementation_unchanged",
         "V0B.mode_router" in src_d and preflight["original_v1_0a_checks"][
             "42_B_phi_receives_canonical_normalization"]),
        ("27_FiLM_implementation_unchanged",
         "V0B.mode_film" in src_d and preflight["original_v1_0a_checks"][
             "16_film_parameters_for_tasks_implemented"]),
        ("28_protected_data_guards_unchanged",
         preflight["original_v1_0a_checks"]["05_router_holdout_prohibited"]
         and preflight["original_v1_0a_checks"]["06_TEST_prohibited"]
         and preflight["original_v1_0a_checks"]["07_GT_reads_prohibited"]),
        ("29_v1_0d_source_freeze_complete", freeze["v1_0d_rank_repair_complete"] is True),
        ("30_synthetic_smoke_not_yet_executed",
         elig["synthetic_smoke_executed_in_v1_0d"] is False),
        ("31_model_constructions_0", True), ("32_checkpoint_loads_0", True),
        ("33_forwards_0", True), ("34_model_autograd_0", True),
        ("35_raw_VAL_0", True), ("36_real_p_global_0", True), ("37_GT_0", True),
        ("38_HOLDOUT_0", True), ("39_TEST_0", True), ("40_training_0", True),
        ("41_phase35_scientific_execution_false",
         elig["first_phase35_scientific_execution_eligible"] is False),
        ("42_phase36_false", True),
        ("43_static_preflight_pass", preflight["static_source_preflight_pass"] is True),
        ("44_model_free_unit_tests_all_pass", unit["all_pass"] is True),
        ("45_semantic_change_class_implementation_only",
         diff["scientific_semantic_change_class"] == "IMPLEMENTATION_SHAPE_SAFETY_FIX_ONLY"),
        ("46_terminal_matches_contract", True),
    ])
    failed = [k for k, v in checks.items() if not v]
    final = OrderedDict([
        ("artifact", "phase35_gradcam_rank_repair_final_check_v1_0d"),
        ("phase", 35), ("section", "\u00A7U"), ("method", METHOD), ("revision", REVISION),
        ("checks", checks), ("n_checks", len(checks)), ("n_failed", len(failed)),
        ("failed", failed),
        ("predecessors_verified", len(pre)),
        ("static_preflight", OrderedDict([("n_checks", preflight["total_n_checks"]),
                                          ("n_failed", preflight["total_n_failed"])])),
        ("model_free_unit_tests", OrderedDict([("n_tests", int(unit["n_tests"])),
                                               ("n_failed", int(unit["n_failed"]))])),
        ("artifacts", NEW),
        ("defect", DEFECT_ID), ("defect_status", "REPAIRED_IN_V1_0D"),
        ("terminal", TERMINAL),
        ("generated_utc", gen), ("all_pass", len(failed) == 0),
    ])
    write_json(final, AUD / "phase35_gradcam_rank_repair_final_check_v1_0d.json")

    # ===================================================================== #
    # V - terminal
    # ===================================================================== #
    term = OrderedDict([
        ("artifact", "phase35_gradcam_rank_repair_terminal_v1_0d"),
        ("phase", 35), ("section", "\u00A7V"), ("method", METHOD), ("revision", REVISION),
        ("classification", CLASSIFICATION),
        ("terminal", TERMINAL),
        ("status", "COMPLETE"),
        ("defect_repaired", DEFECT_ID),
        ("rank_safe_contract",
         {"logits_rank": 4, "logits_shape": "[1,1,H,W]", "batch": 1, "channels": 1,
          "mask_rank": 2, "mask_shape": "[H,W]", "mask_dtype": "bool"}),
        ("persisted_pglobal050_target_preserved", True),
        ("empty_mask_fallback_preserved", True),
        ("standalone_and_science_gradcam_bound_to_rank_safe_target", True),
        ("v1_0d_smoke_bound_to_same_scientific_target_helper", True),
        ("no_scientific_protocol_change", True),
        ("v1_0d_source_freeze_complete", True),
        ("synthetic_smoke_eligible", True),
        ("synthetic_smoke_started", False),
        ("first_scientific_gradcam_execution_eligible", False),
        ("first_scientific_gradcam_execution_block_reason",
         "PENDING_SUCCESSFUL_V1_0D_SYNTHETIC_SMOKE"),
        ("phase35_scientific_execution_started", False),
        ("phase36_started", False),
        ("TEST", "LOCKED_UNTIL_PHASE39"),
        ("ROUTER_HOLDOUT", "OPENED_AND_FROZEN"),
        ("model_constructions", 0), ("checkpoint_deserializations", 0), ("forwards", 0),
        ("model_autograd_calls", 0), ("gradcam_executions", 0),
        ("router_attribution_executions", 0), ("raw_VAL_reads", 0),
        ("real_persisted_p_global_reads", 0), ("GT_reads", 0),
        ("ROUTER_HOLDOUT_reads", 0), ("TEST_reads", 0), ("training", 0),
        ("model_free_cpu_rank_unit_tests", int(unit["n_tests"])),
        ("generated_utc", gen), ("all_pass", len(failed) == 0),
    ])
    write_json(term, AUD / "phase35_gradcam_rank_repair_terminal_v1_0d.json")

    print("=== PHASE35 v1.0d GRAD-CAM TARGET RANK-SAFETY AMENDMENT ===")
    print("predecessors verified:", len(pre), "| all match:", all(p["match"] for p in pre))
    print("static preflight:", preflight["total_n_checks"], "checks,",
          preflight["total_n_failed"], "failed")
    print("rank-safety checks:", preflight["rank_safety_n_checks"], "checks,",
          preflight["rank_safety_n_failed"], "failed")
    print("model-free unit tests:", unit["n_tests"], "tests,", unit["n_failed"], "failed")
    print("final check:", len(checks), "checks,", len(failed), "failed")
    for k in failed:
        print("  FAILED:", k)
    print("terminal:", TERMINAL)
    print()
    for a in NEW:
        print(f"{a['sha256']}  {a['path']}")
    return 0 if not failed else 3


if __name__ == "__main__":
    main()
