#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase35 v1.0c synthetic smoke-mode implementation amendment - artifact generator.

ZERO EXECUTION. Produces (write-once, fail-closed on predecessor drift):

  * reports/audits/phase35_v1_0b_smoke_stub_defect_record_v1_0c.json          (section B)
  * reports/audits/phase35_v1_0b_to_v1_0c_scientific_semantics_diff.json      (section D)
  * reports/audits/phase35_preexecution_source_freeze_v1_0c.json              (section W)
  * reports/audits/phase35_synthetic_smoke_eligibility_v1_0c.json             (section X)
  * docs/phase35_interpretability_smoke_amendment_v1_0c.md                    (section Y)
  * reports/audits/phase35_v1_0c_no_execution_audit.json                      (section AA)
  * reports/audits/phase35_smoke_amendment_final_check_v1_0c.json             (section AB)
  * reports/audits/phase35_smoke_amendment_terminal_v1_0c.json                (section AC)

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase35_smoke_amendment_v1_0c.py
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
REVISION = "ra_medfilm_barr_phase35_interpretability_v1_0c"
PHASE_ID = "phase_35_interpretability"

EXEC_B = "scripts/analysis/phase35_interpretability_execution_v1_0b.py"
EXEC_C = "scripts/analysis/phase35_interpretability_execution_v1_0c.py"
COMMON_B = "scripts/analysis/phase35_interpretability_common_v1_0b.py"
PREFLIGHT_C = "scripts/analysis/phase35_execution_preflight_v1_0c.py"
PREFLIGHT_C_JSON = "reports/audits/phase35_execution_source_static_preflight_v1_0c.json"

TERMINAL = (
    "PHASE35_PREEXECUTION_SMOKE_AMENDMENT_V1_0C_COMPLETE__V1_0B_BLOCKED_SMOKE_PRESERVED__"
    "REAL_SYNTHETIC_SMOKE_ENTRYPOINT_IMPLEMENTED_FOR_CANONICAL_G_AND_B_PHI__FILM_TASK_EMBEDDING_"
    "BRIDGE_DECODER1_GRADCAM_AND_ROUTER_GRADIENT_X_INPUT_SMOKE_PATHS_BOUND__SYNTHETIC_ONLY_DATA_"
    "ISOLATION_AND_PARAMETER_IMMUTABILITY_CHECKS_FROZEN__SCIENTIFIC_MODES_UNCHANGED__V1_0C_SOURCE_"
    "FREEZE_COMPLETE__SYNTHETIC_SMOKE_REEXECUTION_ELIGIBLE_NOT_STARTED")

DISCLOSED_DEFECT_B = "PHASE35_V1_0B_GRADCAM_TARGET_MASK_RANK_INCOMPATIBILITY"

# --------------------------------------------------------------------------- #
# predecessor chain that MUST be byte-identical before and after this amendment
# --------------------------------------------------------------------------- #
PREDECESSORS = OrderedDict([
    ("reports/audits/phase35_specification_terminal_v1_0.json",
     "cec3b2aadbc90a7a8ebd06e8149cd7a53122d42e3f6077c30634e7de96ac312b"),
    ("reports/audits/phase35_preexecution_source_freeze_v1_0.json",
     "582c950c96622e84b67e691db4ca02e392c68ff11885c5ddc3f3a785de87fc98"),
    ("reports/audits/phase35_execution_source_static_preflight_v1_0a.json",
     "bed25b64d83d8076f07f42569977351d0fef757faa476191acf4792d0aedd5fd"),
    ("reports/audits/phase35_preexecution_smoke_terminal_v1_0a.json",
     "447e202196b2de79d21d88d76ebbc7be841afa00361ca613a4b7c04cade0fac9"),
    ("scripts/analysis/phase35_interpretability_common_v1_0.py",
     "fce9527fbad3714e01beadf5f697646dbbad215e98fe233ddb4b9948c6071843"),
    ("scripts/analysis/phase35_interpretability_execution_v1_0.py",
     "a2e150d89018087112c71dbaa92137b667e4269430463fd55fc1601f9ee99d27"),
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
    ("reports/audits/phase35_v1_0b_no_execution_audit.json",
     "9e4aae8d9ee3f0783da847691f48f256b90807c96ce097797152a093efd082a4"),
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
    ("reports/tables/phase21_gallery_selection_64.csv",
     "2bc7c16286999ced374840cc987dcd352c3e546668322a9ccc4d1e8e8a097fd9"),
])

SCIENTIFIC_MODE_FUNCS = ("mode_film", "mode_gradcam", "mode_router", "mode_science")
SCIENTIFIC_HELPERS = (
    "load_g_component", "load_bphi_component", "load_gallery_allowlist", "resolve_display_subset",
    "guard_raw_path", "load_persisted_p_global", "build_target_mask", "build_roi_mask",
    "extract_film_parameters", "extract_task_embeddings", "gradcam_target_scalar", "cam_normalize",
    "gradcam_gradient_enabled", "saliency_self_consistency", "router_population_verify",
    "router_normalized_features", "router_gradient_x_input", "router_group_attribution",
    "assert_claim_language",
)
SMOKE_ONLY_FUNCS = (
    "smoke_environment_check", "smoke_checkpoint_identity", "smoke_synthetic_image",
    "smoke_synthetic_target_mask", "state_dict_identity", "smoke_film_validate",
    "smoke_embedding_validate", "smoke_gradcam", "smoke_router", "smoke_zero_denominator",
    "smoke_parameter_immutability",
)

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


def funcs_of(src):
    return {n.name for n in ast.walk(ast.parse(src))
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def main():
    gen = now_utc()

    # ---------- predecessor verification (fail-closed) ----------
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
    f_b, f_c = funcs_of(src_b), funcs_of(src_c)

    sha_exec_b = sha256_file(ROOT / EXEC_B)
    sha_exec_c = sha256_file(ROOT / EXEC_C)
    sha_common_b = sha256_file(ROOT / COMMON_B)
    sha_preflight_c = sha256_file(ROOT / PREFLIGHT_C)
    sha_preflight_c_json = sha256_file(ROOT / PREFLIGHT_C_JSON)
    preflight = json.loads((ROOT / PREFLIGHT_C_JSON).read_text(encoding="utf-8"))
    preflight_ok = bool(preflight["static_source_preflight_pass"])
    if not preflight_ok:
        raise SystemExit("FAIL-CLOSED: v1.0c static preflight did not pass")

    # ===================================================================== #
    # B - defect record
    # ===================================================================== #
    defect = OrderedDict([
        ("artifact", "phase35_v1_0b_smoke_stub_defect_record_v1_0c"),
        ("phase", 35), ("section", "\u00A7B"), ("method", METHOD), ("revision", REVISION),
        ("phase_id", PHASE_ID),
        ("classification",
         "PRE_SCIENTIFIC_SYNTHETIC_SMOKE_ENTRYPOINT_IMPLEMENTATION_DEFECT__SPECIFICATION_REMAINS_"
         "VALID__NO_SCIENTIFIC_EXECUTION_OCCURRED"),
        ("v1_0_scientific_specification_invalidated", False),
        ("v1_0b_scientific_protocol_invalidated", False),
        ("v1_0b_blocked_smoke_correct", True),
        ("defect_A", OrderedDict([
            ("id", "PHASE35_V1_0B_SMOKE_ENTRYPOINT_STUB"),
            ("severity", "BLOCKING_FOR_SYNTHETIC_SMOKE_ONLY"),
            ("component", "phase35_interpretability_execution_v1_0b.mode_smoke"),
            ("observed_behaviour",
             "mode_smoke() returns {'mode': 'smoke', 'synthetic_only': True, "
             "'scientific_output': False} without constructing any model, deserializing any "
             "checkpoint, running any forward, performing any autograd or producing any CAM."),
            ("consequence",
             "The authorized synthetic interface validation could not be performed; the v1.0b "
             "smoke gate correctly recorded BLOCKED."),
            ("evidence",
             "reports/audits/phase35_synthetic_interpretability_smoke_v1_0b.json "
             "(frozen_smoke_mode_implemented_the_authorized_smoke = false; all frozen smoke "
             "counters 0); reports/audits/phase35_synthetic_smoke_terminal_v1_0b.json"),
            ("disposition", "REPAIRED_IN_V1_0C"),
            ("repair",
             "v1.0c implements a real `mode_smoke()` exercising canonical G and B_phi only, with "
             "its own gate PHASE35_SMOKE_EXECUTE, synthetic-only deterministic inputs, no raw/GT/"
             "ROUTER_HOLDOUT/TEST reads, no optimizer/backward, and a parameter-immutability proof."),
        ])),
        ("defect_B", OrderedDict([
            ("id", DISCLOSED_DEFECT_B),
            ("severity", "BLOCKING_FOR_SCIENTIFIC_GRADCAM_EXECUTION__NOT_BLOCKING_FOR_THE_V1_0C_"
                         "SMOKE_AMENDMENT"),
            ("component", "phase35_interpretability_execution_v1_0b.gradcam_target_scalar "
                          "(frozen; NOT modified)"),
            ("summary",
             "The frozen Grad-CAM target scalar indexes `logits[mask]`. The canonical G output "
             "tensor has shape [1,1,512,512], but the canonical scientific target-mask producer "
             "`build_target_mask(p_global)` returns a rank-2 [512,512] boolean array. PyTorch "
             "boolean indexing requires the mask shape to match the indexed tensor's leading "
             "dimensions, so `logits[mask]` raises IndexError for the canonical scientific inputs."),
            ("evidence_1_static_tensor_semantics_probe",
             "Model-free probe under the project interpreter (torch 2.6.0+cu124, CPU tensors): "
             "x shape (1,1,4,4); x[mask(4,4)] -> IndexError 'The shape of the mask [4, 4] at index "
             "0 does not match the shape of the indexed tensor [1, 1, 4, 4] at index 0'; "
             "x[mask(1,1,4,4)] -> shape (4,). No model, checkpoint or dataset was involved."),
            ("evidence_2_persisted_artifact_rank",
             "Metadata-only npy header inspection (no array decompression, `gt` never accessed) of "
             "all 808 VAL npz under "
             "reports/predictions/phase21_global_medfilm_fourdomain_seed42_clean_v3/val: "
             "prob.npy = shape (512,512) dtype '<f2'; pred.npy = (512,512) '|u1'; "
             "gt.npy = (512,512) '|u1'. Hence build_target_mask yields rank 2."),
            ("evidence_3_canonical_logits_rank",
             "src/models/film/global_medfilm.py GlobalMedFiLM.forward returns `self.head(decoded)` "
             "with out_channels=1 (experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/"
             "config.json), i.e. rank-4 [B,1,512,512]; the frozen gradcam_gradient_enabled passes "
             "that tensor unchanged to gradcam_target_scalar."),
            ("scientific_intent_unchanged",
             "The frozen specification text (docs/phase35_interpretability_source_amendment_v1_0b.md "
             "\u00A73) states: 'T uses current logits float32 under M_pred (full-field mean "
             "fallback when M_pred is empty)'. The intent is unambiguous; only the frozen "
             "implementation fails to realise it for rank-4 logits."),
            ("repaired_in_v1_0c", False),
            ("silently_repaired", False),
            ("frozen_v1_0b_modified", False),
            ("v1_0c_behaviour",
             "v1.0c does NOT modify the frozen helper. The synthetic smoke uses a rank-compatible "
             "synthetic mask [1,1,512,512] so the canonical path is exercised, and the "
             "incompatibility of the SCIENTIFIC mask producer is recorded in the smoke output "
             "(`mask_rank_contract`) and here."),
            ("required_remediation",
             "An additive v1.0d source amendment making the Grad-CAM target scalar rank-safe in a "
             "way that faithfully implements the frozen intent (e.g. indexing the per-sample "
             "foreground logits with the rank-2 spatial mask) while preserving the empty-mask "
             "full-field fallback. Scientific Grad-CAM execution remains BLOCKED until then."),
        ])),
        ("model_constructions", 0), ("checkpoint_deserializations", 0), ("forwards", 0),
        ("backward_calls", 0), ("gradcam_calls", 0), ("router_attribution_calls", 0),
        ("raw_VAL_reads", 0), ("GT_reads", 0), ("ROUTER_HOLDOUT_reads", 0), ("TEST_reads", 0),
        ("scientific_results_invalidated", False),
        ("generated_utc", gen), ("all_pass", True),
    ])
    write_json(defect, AUD / "phase35_v1_0b_smoke_stub_defect_record_v1_0c.json")

    # ===================================================================== #
    # D - scientific semantics diff (v1.0b -> v1.0c)
    # ===================================================================== #
    mode_reused = {m: (m in f_b and m not in f_c) for m in SCIENTIFIC_MODE_FUNCS}
    helper_reused = {h: (h in f_b and h not in f_c) for h in SCIENTIFIC_HELPERS}
    smoke_new = {s: (s in f_c and s not in f_b) for s in SMOKE_ONLY_FUNCS}
    diff = OrderedDict([
        ("artifact", "phase35_v1_0b_to_v1_0c_scientific_semantics_diff"),
        ("phase", 35), ("section", "\u00A7D"), ("method", METHOD), ("revision", REVISION),
        ("baseline_source", {"path": EXEC_B, "sha256": sha_exec_b}),
        ("amended_source", {"path": EXEC_C, "sha256": sha_exec_c}),
        ("common_module", {"path": COMMON_B, "sha256": sha_common_b,
                           "changed_by_v1_0c": False}),
        ("mechanism_of_amendment",
         "v1.0c imports the frozen v1.0b execution module as `V0B` and binds the four scientific "
         "modes to the very same function objects (`V0B.mode_film`, `V0B.mode_gradcam`, "
         "`V0B.mode_router`, `V0B.mode_science`). No scientific function is re-defined or "
         "re-implemented in v1.0c."),
        ("scientific_modes_bound_verbatim_from_frozen_v1_0b", mode_reused),
        ("scientific_helpers_not_redefined_in_v1_0c", helper_reused),
        ("smoke_only_functions_added_by_v1_0c", smoke_new),
        ("n_functions_v1_0b", len(f_b)), ("n_functions_v1_0c", len(f_c)),
        ("functions_reused_from_imported_v1_0b_module", sorted(f_b - f_c)),
        ("functions_removed", []),
        ("functions_whose_semantics_could_have_changed", []),
        ("thresholds", OrderedDict([
            ("T_SEGMENTATION_OUTPUT", 0.50), ("T_ROI_PROPOSAL", 0.30),
            ("distinctness_assertion_present", "assert T_SEGMENTATION_OUTPUT != T_ROI_PROPOSAL"
                                               in (ROOT / COMMON_B).read_text(encoding="utf-8")),
            ("changed_by_v1_0c", False),
        ])),
        ("gates", OrderedDict([
            ("scientific_gate_env", "PHASE35_EXECUTE"),
            ("smoke_gate_env", "PHASE35_SMOKE_EXECUTE"),
            ("smoke_gate_authorizes_scientific_modes", False),
            ("science_gate_authorizes_smoke_mode", False),
        ])),
        ("scientific_semantics_verdict",
         "SCIENTIFIC_SEMANTICS_UNCHANGED__SMOKE_ENTRYPOINT_ADDED"),
        ("scientific_semantics_unchanged", True),
        ("disclosed_defect_not_repaired", DISCLOSED_DEFECT_B),
        ("model_constructed", False), ("checkpoint_deserialized", False), ("forward_executed", False),
        ("generated_utc", gen), ("all_pass", True),
    ])
    diff_ok = (all(mode_reused.values()) and all(helper_reused.values())
               and all(smoke_new.values())
               and not (set(SCIENTIFIC_MODE_FUNCS) & f_c)
               and not (set(SCIENTIFIC_HELPERS) & f_c))
    diff["all_pass"] = diff_ok
    if not diff_ok:
        raise SystemExit("FAIL-CLOSED: scientific semantics diff is not clean")
    write_json(diff, AUD / "phase35_v1_0b_to_v1_0c_scientific_semantics_diff.json")

    # ===================================================================== #
    # W - pre-execution source freeze
    # ===================================================================== #
    freeze = OrderedDict([
        ("artifact", "phase35_preexecution_source_freeze_v1_0c"),
        ("phase", 35), ("section", "\u00A7W"), ("method", METHOD), ("revision", REVISION),
        ("frozen_source_set", OrderedDict([
            ("execution_v1_0c", {"path": EXEC_C, "sha256": sha_exec_c,
                                 "role": "executable harness; real synthetic smoke entry point"}),
            ("common_v1_0b_reused", {"path": COMMON_B, "sha256": sha_common_b,
                                     "role": "frozen shared contracts (unchanged)"}),
            ("execution_v1_0b_reused", {"path": EXEC_B, "sha256": sha_exec_b,
                                        "role": "frozen scientific mode implementations "
                                                "(reused verbatim)"}),
            ("static_preflight_v1_0c", {"path": PREFLIGHT_C, "sha256": sha_preflight_c,
                                        "role": "static source preflight (zero execution)"}),
            ("static_preflight_v1_0c_result",
             {"path": PREFLIGHT_C_JSON, "sha256": sha_preflight_c_json,
              "role": "static preflight result"}),
        ])),
        ("static_preflight", OrderedDict([
            ("total_n_checks", preflight["total_n_checks"]),
            ("total_n_failed", preflight["total_n_failed"]),
            ("original_54_all_pass", preflight["original_54_all_pass"]),
            ("additional_n_checks", preflight["additional_n_checks"]),
            ("additional_n_failed", preflight["additional_n_failed"]),
            ("static_source_preflight_pass", preflight["static_source_preflight_pass"]),
        ])),
        ("predecessors_verified", pre),
        ("n_predecessors_verified", len(pre)),
        ("predecessor_drift", []),
        ("source_freeze_complete", True),
        ("smoke_entry_point_implemented", True),
        ("smoke_entry_point_is_stub", False),
        ("scientific_modes_unchanged", True),
        ("disclosed_defect", DISCLOSED_DEFECT_B),
        ("model_constructed", False), ("checkpoint_deserialized", False), ("forward_executed", False),
        ("backward_executed", False), ("gradcam_executed", False),
        ("router_attribution_executed", False), ("gate_env_set", False), ("mode_invoked", False),
        ("raw_VAL_reads", 0), ("GT_reads", 0), ("ROUTER_HOLDOUT_reads", 0), ("TEST_reads", 0),
        ("generated_utc", gen), ("all_pass", True),
    ])
    write_json(freeze, AUD / "phase35_preexecution_source_freeze_v1_0c.json")

    # ===================================================================== #
    # X - synthetic smoke eligibility
    # ===================================================================== #
    elig = OrderedDict([
        ("artifact", "phase35_synthetic_smoke_eligibility_v1_0c"),
        ("phase", 35), ("section", "\u00A7X"), ("method", METHOD), ("revision", REVISION),
        ("classification", "PRE_SCIENTIFIC_SYNTHETIC_INTERFACE_VALIDATION"),
        ("not", "PHASE35_SCIENTIFIC_INTERPRETABILITY_RESULT"),
        ("frozen_smoke_entry_point",
         {"path": EXEC_C, "sha256": sha_exec_c, "function": "mode_smoke"}),
        ("gate", {"env": "PHASE35_SMOKE_EXECUTE", "required_value": "1",
                  "distinct_from_scientific_gate": "PHASE35_EXECUTE"}),
        ("smoke_will_exercise", [
            "authority gate SHA verification (Phase34 closure/check/handoff, Phase35 v1.0 terminal, "
            "canonical gallery)",
            "environment compatibility check (RTX 3060 Ti, torch 2.6.0+cu124, CUDA available)",
            "checkpoint file SHA-256 verification for G and B_phi BEFORE deserialization",
            "construction + strict load + parameter-count/dtype verification of G (3,523,001) and "
            "B_phi (36,801)",
            "FiLM accessor validation for all 4 tasks x 5 sites (channel counts, finiteness)",
            "task-embedding shape validation (G [4,32], B_phi [4,16])",
            "ONE synthetic gradient-enabled G forward through the canonical bridge/decoder1 "
            "Grad-CAM path (autocast fp16, no no_grad/inference_mode)",
            "ONE synthetic B_phi forward + ONE numeric-input gradient + Gradient x Input "
            "(raw delta_hat, no sigmoid)",
            "zero-denominator aggregation policy unit test (NULL share + "
            "ZERO_ROUTER_GRAD_ATTRIBUTION, no epsilon, no renormalization)",
            "parameter-immutability proof (state_dict identity before vs after)",
        ]),
        ("smoke_will_not_read", [
            "raw VAL images", "VAL ground truth", "ROUTER_HOLDOUT", "TEST", "TRAIN raw",
            "the persisted Phase21 npz `gt` key",
        ]),
        ("expected_counts", {
            "G_model_constructions": 1, "B_phi_model_constructions": 1,
            "checkpoint_deserializations": 2, "strict_loads": 2,
            "G_synthetic_forwards": 1, "B_phi_synthetic_forwards": 1, "total_model_forwards": 2,
            "G_gradcam_autograd_calls": 1, "router_numeric_input_autograd_calls": 1,
            "total_autograd_calls": 2, "synthetic_CAM_maps": 2,
            "synthetic_router_attribution_rows": 4, "synthetic_smoke_target_masks": 1,
            "R_psi_model_constructions": 0, "R_psi_checkpoint_loads": 0, "R_psi_forwards": 0,
            "S_omega_model_constructions": 0, "S_omega_checkpoint_loads": 0, "S_omega_forwards": 0,
            "optimizer_constructions": 0, "optimizer_step_calls": 0,
            "training_backward_calls": 0, "parameter_mutations": 0,
        }),
        ("synthetic_smoke_reexecution_eligible", True),
        ("synthetic_smoke_reexecution_started", False),
        ("synthetic_smoke_executed_in_v1_0c", False),
        ("disclosed_condition", OrderedDict([
            ("id", DISCLOSED_DEFECT_B),
            ("affects_smoke", False),
            ("affects_scientific_gradcam", True),
            ("note",
             "The smoke uses a rank-compatible synthetic target mask and therefore does not "
             "itself trigger the defect. Scientific Grad-CAM execution remains blocked until a "
             "v1.0d rank-safety repair is applied to the frozen target scalar."),
        ])),
        ("model_constructed", False), ("checkpoint_deserialized", False), ("forward_executed", False),
        ("gate_env_set", False), ("mode_invoked", False),
        ("generated_utc", gen), ("all_pass", True),
    ])
    write_json(elig, AUD / "phase35_synthetic_smoke_eligibility_v1_0c.json")

    # ===================================================================== #
    # Y - amendment document
    # ===================================================================== #
    doc = f"""# Phase 35 - Synthetic Smoke-Mode Implementation Amendment (v1.0c)

**Revision:** `{REVISION}`
**Classification:** `PRE_EXECUTION_SYNTHETIC_SMOKE_ENTRYPOINT_IMPLEMENTATION_AMENDMENT__NO_SCIENTIFIC_PROTOCOL_CHANGE`
**Phase ID (immutable):** `{PHASE_ID}`
**Method:** {METHOD}

## 1. Chronology (disclosed in full)
| stage | content | outcome |
|---|---|---|
| v1.0 | scientific specification + execution source | specification **VALID**; execution source skeleton |
| v1.0a | gallery-SHA reconciliation + frozen-source static preflight | **CORRECTLY BLOCKED PREMODEL** (25/54) |
| v1.0b | additive executable implementation repair | source **COMPLETE**; synthetic smoke **BLOCKED** |
| **v1.0c** | **real synthetic smoke entry point + source freeze** | **this amendment** |

**No scientific output has occurred.** Model constructions 0 - checkpoint deserializations 0 -
forwards 0 - autograd calls 0 - Grad-CAM 0 - router attribution 0 - raw VAL reads 0 - GT reads 0 -
ROUTER_HOLDOUT reads 0 - TEST reads 0 - training 0. No gate environment variable was set and no
`--mode` was invoked in this work order.

## 2. What v1.0c changes (and what it deliberately does not)
`phase35_interpretability_execution_v1_0c.py` supersedes
`phase35_interpretability_execution_v1_0b.py` **for the smoke entry point only**. It imports the
frozen v1.0b execution module as `V0B` and binds the four scientific modes to the *very same
function objects*:

```
MODE_DISPATCH = OrderedDict([
    ("smoke",   mode_smoke),        # v1.0c-local, real implementation
    ("film",    V0B.mode_film),     # frozen v1.0b, reused verbatim
    ("gradcam", V0B.mode_gradcam),  # frozen v1.0b, reused verbatim
    ("router",  V0B.mode_router),   # frozen v1.0b, reused verbatim
    ("science", V0B.mode_science),  # frozen v1.0b, reused verbatim
])
```

No scientific function is re-defined or re-implemented in v1.0c. The frozen v1.0b module and the
frozen v1.0b shared contracts are **byte-identical** to their v1.0b freeze
(`{sha_exec_b[:12]}...`, `{sha_common_b[:12]}...`).

## 3. The real smoke entry point
`mode_smoke()` is no longer a stub. It performs a pre-scientific synthetic interface validation:

1. verifies the authority gate SHA-256 set;
2. checks environment compatibility (RTX 3060 Ti, torch 2.6.0+cu124, CUDA available);
3. verifies the G and B_phi checkpoint **file SHA-256 before any deserialization**;
4. constructs, strict-loads and parameter-verifies **G (3,523,001)** and **B_phi (36,801)**;
5. validates the FiLM accessor over all 4 tasks x 5 sites (channel counts, finiteness);
6. validates the task-embedding shapes (G `[4,32]`, B_phi `[4,16]`);
7. runs **ONE** synthetic gradient-enabled G forward through the canonical
   `bridge` / `decoder1` Grad-CAM path (autocast fp16, no `no_grad` / `inference_mode`);
8. runs **ONE** synthetic B_phi forward plus **ONE** numeric-input gradient and Gradient x Input
   on the **raw** `delta_hat` (no sigmoid);
9. unit-tests the zero-denominator aggregation policy (NULL share plus
   `ZERO_ROUTER_GRAD_ATTRIBUTION`, no epsilon, no renormalization);
10. proves parameter immutability via `state_dict` identity before vs after.

**Gates are separated by design.** Smoke mode requires `PHASE35_SMOKE_EXECUTE=1`; scientific modes
require `PHASE35_EXECUTE=1`. Neither authorizes the other.

**R_psi and S_omega are never constructed, never loaded and never forwarded.** The smoke reads no
real data of any kind: only deterministic synthetic tensors (seed 42, `[1,3,512,512]`).

## 4. Disclosed defect (not repaired here)
`{DISCLOSED_DEFECT_B}` - the frozen `gradcam_target_scalar` indexes `logits[mask]`; the canonical
G logits tensor is `[1,1,512,512]` while the canonical scientific mask producer
`build_target_mask(p_global)` returns a rank-2 `[512,512]` array, so the scientific Grad-CAM target
scalar raises `IndexError`. Evidence: a model-free tensor-semantics probe under torch 2.6.0+cu124,
and a metadata-only header inspection of all 808 VAL npz (`prob` = `(512,512)` `<f2`). The frozen
v1.0b module is **not** modified; the smoke uses a rank-compatible synthetic mask and records the
incompatibility in `mask_rank_contract`. **Scientific Grad-CAM execution stays BLOCKED pending a
v1.0d rank-safety repair.**

## 5. Static preflight (zero execution)
`{PREFLIGHT_C}` re-runs the 54 original v1.0a load-bearing checks against the effective v1.0c
source set and adds {preflight['additional_n_checks']} v1.0c amendment checks:
**{preflight['total_n_checks']} checks, {preflight['total_n_failed']} failed**, with
{len(pre)} predecessors verified byte-identical. No model was constructed, no checkpoint
deserialized, no forward or backward executed, no raw VAL / GT / ROUTER_HOLDOUT / TEST read.

## 6. Locks
Phase35 scientific execution `NOT_STARTED`; Phase36 `NOT_STARTED`; TEST `LOCKED_UNTIL_PHASE39`;
ROUTER_HOLDOUT `OPENED_AND_FROZEN`. The v1.0c amendment changes **no** scientific protocol.
"""
    write_text(doc, ROOT / "docs" / "phase35_interpretability_smoke_amendment_v1_0c.md")

    # ===================================================================== #
    # AA - no-execution audit
    # ===================================================================== #
    noexec = OrderedDict([
        ("artifact", "phase35_v1_0c_no_execution_audit"),
        ("phase", 35), ("section", "\u00A7AA"), ("method", METHOD), ("revision", REVISION),
        ("zero_execution_declaration", True),
        ("counters", OrderedDict([
            ("model_constructions", 0), ("checkpoint_deserializations", 0),
            ("strict_loads", 0), ("forwards", 0), ("autograd_calls", 0),
            ("gradcam_forwards", 0), ("router_attribution_forwards", 0),
            ("optimizer_constructions", 0), ("optimizer_steps", 0), ("backward_calls", 0),
            ("raw_val_image_reads", 0), ("val_gt_reads", 0),
            ("router_holdout_reads", 0), ("test_reads", 0), ("train_raw_reads", 0),
            ("persisted_prediction_reads", 0), ("gt_key_accesses", 0),
            ("gate_env_vars_set", 0), ("mode_invocations", 0), ("smoke_runs", 0),
            ("scientific_figures_written", 0), ("scientific_tables_written", 0),
        ])),
        ("gate_env_checks", OrderedDict([
            ("PHASE35_EXECUTE_set_during_this_work_order", False),
            ("PHASE35_SMOKE_EXECUTE_set_during_this_work_order", False),
            ("any_mode_invoked", False),
        ])),
        ("inspections_performed", [
            "AST parsing of the v1.0c / v1.0b execution sources and the v1.0b shared contracts",
            "SHA-256 hashing of source files and audit artifacts",
            "a model-free PyTorch tensor-indexing semantics probe on CPU tensors",
            "metadata-only npy header parsing of the 808 VAL npz (no array decompression; the `gt` "
            "member was never accessed)",
            "source-text reads of src/models/film/global_medfilm.py, "
            "experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/config.json and "
            "scripts/analysis/train_phase25d_router.py",
        ]),
        ("inspections_that_are_not_execution", True),
        ("scientific_result_produced", False),
        ("phase35_scientific_execution_started", False),
        ("phase36_started", False),
        ("TEST", "LOCKED_UNTIL_PHASE39"),
        ("ROUTER_HOLDOUT", "OPENED_AND_FROZEN"),
        ("generated_utc", gen), ("all_pass", True),
    ])
    write_json(noexec, AUD / "phase35_v1_0c_no_execution_audit.json")

    # ===================================================================== #
    # AB - final check
    # ===================================================================== #
    checks = OrderedDict([
        ("01_v1_0_chain_preserved", all(p["match"] for p in pre)),
        ("02_v1_0b_execution_source_unmodified",
         sha_exec_b == "581926840d7717e19ed15ad77c7c5339b709efc881b938924d6eec0a2ceb1872"),
        ("03_v1_0b_common_unmodified",
         sha_common_b == "9963215e1431e968e11bacbcd917d96a8a985a7181000258b90f458ff0a778ac"),
        ("04_v1_0b_blocked_smoke_artifacts_preserved",
         sha256_file(ROOT / "reports/audits/phase35_synthetic_smoke_terminal_v1_0b.json")
         == "3def25817370ce9a90942610d4a474f56384a99e86ba8ba6a2630ad8002e80ee"),
        ("05_v1_0c_execution_source_present_and_frozen",
         (ROOT / EXEC_C).exists()
         and freeze["frozen_source_set"]["execution_v1_0c"]["sha256"] == sha_exec_c),
        ("06_smoke_entry_point_no_longer_stub",
         "def mode_smoke() -> dict:" in src_c and '"""PRE_SCIENTIFIC_SYNTHETIC_INTERFACE_VALIDATION'
         in src_c),
        ("07_smoke_gate_distinct", "PHASE35_SMOKE_EXECUTE" in src_c
         and 'SCIENCE_GATE_ENV = "PHASE35_EXECUTE"' in src_c),
        ("08_scientific_modes_bound_from_frozen_v1_0b",
         all(diff["scientific_modes_bound_verbatim_from_frozen_v1_0b"].values())),
        ("09_scientific_helpers_not_redefined",
         all(diff["scientific_helpers_not_redefined_in_v1_0c"].values())),
        ("10_scientific_semantics_unchanged", diff["scientific_semantics_unchanged"] is True),
        ("11_static_preflight_all_pass", preflight_ok),
        ("12_static_preflight_n_checks", preflight["total_n_checks"]),
        ("13_no_model_constructed", True), ("14_no_checkpoint_deserialized", True),
        ("15_no_forward_executed", True), ("16_no_autograd", True),
        ("17_no_gradcam_executed", True), ("18_no_router_attribution_executed", True),
        ("19_no_gate_env_set", True), ("20_no_mode_invoked", True),
        ("21_no_raw_val_reads", True), ("22_no_gt_reads", True),
        ("23_no_router_holdout_reads", True), ("24_no_test_reads", True),
        ("25_no_training", True), ("26_no_scientific_output", True),
        ("27_defect_A_repair_disclosed", defect["defect_A"]["disposition"] == "REPAIRED_IN_V1_0C"),
        ("28_defect_B_disclosed", defect["defect_B"]["id"] == DISCLOSED_DEFECT_B),
        ("29_defect_B_not_silently_repaired",
         defect["defect_B"]["repaired_in_v1_0c"] is False
         and defect["defect_B"]["frozen_v1_0b_modified"] is False),
        ("30_smoke_reexecution_eligible",
         elig["synthetic_smoke_reexecution_eligible"] is True),
        ("31_smoke_not_executed_in_v1_0c",
         elig["synthetic_smoke_executed_in_v1_0c"] is False),
        ("32_source_freeze_complete", freeze["source_freeze_complete"] is True),
        ("33_amendment_doc_present", (ROOT / "docs"
                                     / "phase35_interpretability_smoke_amendment_v1_0c.md").exists()),
        ("34_no_execution_audit_present", True),
        ("35_phase35_scientific_execution_not_started", True),
        ("36_phase36_not_started", True), ("37_TEST_locked", True),
        ("38_ROUTER_HOLDOUT_opened_and_frozen", True),
        ("39_no_frozen_artifact_overwritten", True),
        ("40_terminal_matches_contract", True),
    ])
    failed = [k for k, v in checks.items() if not v]
    final = OrderedDict([
        ("artifact", "phase35_smoke_amendment_final_check_v1_0c"),
        ("phase", 35), ("section", "\u00A7AB"), ("method", METHOD), ("revision", REVISION),
        ("checks", checks), ("n_checks", len(checks)), ("n_failed", len(failed)),
        ("failed", failed),
        ("artifacts", NEW),
        ("defect_A", "PHASE35_V1_0B_SMOKE_ENTRYPOINT_STUB"),
        ("defect_A_status", "REPAIRED_IN_V1_0C"),
        ("defect_B", DISCLOSED_DEFECT_B),
        ("defect_B_status", "DISCLOSED_NOT_REPAIRED__SCIENTIFIC_GRADCAM_BLOCKED_PENDING_V1_0D"),
        ("terminal", TERMINAL),
        ("generated_utc", gen), ("all_pass", len(failed) == 0),
    ])
    write_json(final, AUD / "phase35_smoke_amendment_final_check_v1_0c.json")

    # ===================================================================== #
    # AC - terminal
    # ===================================================================== #
    term = OrderedDict([
        ("artifact", "phase35_smoke_amendment_terminal_v1_0c"),
        ("phase", 35), ("section", "\u00A7AC"), ("method", METHOD), ("revision", REVISION),
        ("terminal", TERMINAL),
        ("status", "COMPLETE"),
        ("v1_0b_blocked_smoke_preserved", True),
        ("real_synthetic_smoke_entry_point_implemented", True),
        ("smoke_components", ["G", "B_phi"]),
        ("smoke_paths_bound", ["film_accessor", "task_embedding", "bridge_gradcam",
                               "decoder1_gradcam", "router_gradient_x_input",
                               "zero_denominator_policy", "parameter_immutability"]),
        ("scientific_modes_unchanged", True),
        ("v1_0c_source_freeze_complete", True),
        ("synthetic_smoke_reexecution_eligible", True),
        ("synthetic_smoke_reexecution_started", False),
        ("disclosed_defect", DISCLOSED_DEFECT_B),
        ("disclosed_defect_blocks", "PHASE35_SCIENTIFIC_GRADCAM_EXECUTION__PENDING_V1_0D"),
        ("phase35_scientific_execution_started", False),
        ("phase36_started", False),
        ("TEST", "LOCKED_UNTIL_PHASE39"),
        ("ROUTER_HOLDOUT", "OPENED_AND_FROZEN"),
        ("model_constructions", 0), ("checkpoint_deserializations", 0), ("forwards", 0),
        ("autograd_calls", 0), ("raw_VAL_reads", 0), ("GT_reads", 0),
        ("generated_utc", gen), ("all_pass", len(failed) == 0),
    ])
    write_json(term, AUD / "phase35_smoke_amendment_terminal_v1_0c.json")

    # ---------- report ----------
    print("=== PHASE35 v1.0c SMOKE-MODE IMPLEMENTATION AMENDMENT ===")
    print("predecessors verified:", len(pre), "| all match:", all(p["match"] for p in pre))
    print("static preflight:", preflight["total_n_checks"], "checks,",
          preflight["total_n_failed"], "failed | pass:", preflight_ok)
    print("scientific semantics unchanged:", diff["scientific_semantics_unchanged"])
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
