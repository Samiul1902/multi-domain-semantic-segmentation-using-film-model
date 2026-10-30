#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase35 v1.0b static source preflight: re-runs all 54 v1.0a load-bearing checks against the
NEW v1.0b sources, plus additional v1.0b amendment checks (AST / control-flow where practical).

ZERO EXECUTION. No model construction, no checkpoint deserialization, no forward, no autograd,
no raw-image read.

Writes reports/audits/phase35_execution_source_static_preflight_v1_0b.json (write-once).

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase35_execution_preflight_v1_0b.py
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
REVISION = "ra_medfilm_barr_phase35_interpretability_v1_0b"
OUT = AUD / "phase35_execution_source_static_preflight_v1_0b.json"

COMMON = "scripts/analysis/phase35_interpretability_common_v1_0b.py"
EXEC = "scripts/analysis/phase35_interpretability_execution_v1_0b.py"
PREFLIGHT = "scripts/analysis/phase35_execution_preflight_v1_0b.py"
V10_COMMON = "scripts/analysis/phase35_interpretability_common_v1_0.py"
V10_EXEC = "scripts/analysis/phase35_interpretability_execution_v1_0.py"

PRESERVE = OrderedDict([
    ("reports/audits/phase35_specification_terminal_v1_0.json",
     "cec3b2aadbc90a7a8ebd06e8149cd7a53122d42e3f6077c30634e7de96ac312b"),
    ("reports/audits/phase35_specification_final_check_v1_0.json",
     "7d7eae564f7c71e175fd5ba5c92ae013c8a9ed7a06f95303f193f42ee17886a9"),
    ("docs/phase35_interpretability_spec_v1_0.md",
     "6405ba5f7ad9f046226da916559a0d7a1166a1245bb56e8d38bc9971959acb37"),
    ("reports/audits/phase35_execution_eligibility_adjudication_v1_0.json",
     "c96b366fab0470fdff4577f74035d909108ae90b869e692bc3da7f563ada39fd"),
    ("reports/audits/phase35_preexecution_source_freeze_v1_0.json",
     "582c950c96622e84b67e691db4ca02e392c68ff11885c5ddc3f3a785de87fc98"),
    ("reports/audits/phase35_gallery_sha_reconciliation_v1_0a.json",
     "ef7a4c6580d06ede0cfc8ca56bba1ddfdb6fb6839b1dafdf2928e3bc38e1e72d"),
    ("reports/audits/phase35_execution_source_static_preflight_v1_0a.json",
     "bed25b64d83d8076f07f42569977351d0fef757faa476191acf4792d0aedd5fd"),
    ("reports/audits/phase35_preexecution_smoke_final_check_v1_0a.json",
     "a16c8e006c94a0cf2f7e485de396baed42476a58ccbcb4d8cacb23a6a3300a26"),
    ("reports/audits/phase35_preexecution_smoke_terminal_v1_0a.json",
     "447e202196b2de79d21d88d76ebbc7be841afa00361ca613a4b7c04cade0fac9"),
    (V10_COMMON, "fce9527fbad3714e01beadf5f697646dbbad215e98fe233ddb4b9948c6071843"),
    (V10_EXEC, "a2e150d89018087112c71dbaa92137b667e4269430463fd55fc1601f9ee99d27"),
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
        raise SystemExit(f"REFUSING TO OVERWRITE FROZEN PREFLIGHT OUTPUT: {p}")
    p.write_text(json.dumps(obj, indent=1) + "\n", encoding="utf-8")
    s = sha256_file(p)
    NEW.append({"path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256": s})
    return s


def dotted(node):
    parts, cur = [], node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
    return ".".join(reversed(parts))


def collect(src):
    tree = ast.parse(src)
    calls, withs, funcs, lits = set(), set(), {}, []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            calls.add(dotted(n.func))
        if isinstance(n, ast.With):
            for item in n.items:
                ce = item.context_expr
                withs.add(dotted(ce.func) if isinstance(ce, ast.Call) else dotted(ce))
        if isinstance(n, ast.FunctionDef):
            funcs[n.name] = n
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            lits.append(n.value)
    return {"tree": tree, "calls": calls, "withs": withs, "funcs": funcs, "literals": lits}


def fn_lines(info, fname):
    fn = info["funcs"].get(fname)
    return (fn.lineno, fn.end_lineno) if fn else (None, None)


def first_line_in_fn(info, fname, pred):
    fn = info["funcs"].get(fname)
    if fn is None:
        return None
    for n in ast.walk(fn):
        if pred(n):
            return n.lineno
    return None


def main():
    gen = now_utc()

    # ---------- preservation ----------
    pres = []
    for rel, exp in PRESERVE.items():
        obs = sha256_file(ROOT / rel)
        pres.append({"path": rel, "expected_sha256": exp, "observed_sha256": obs,
                     "match": obs == exp})
    pres_ok = all(p["match"] for p in pres)
    if not pres_ok:
        raise SystemExit("FAIL-CLOSED: v1.0/v1.0a preservation mismatch")

    ex = (ROOT / EXEC).read_text(encoding="utf-8")
    cm = (ROOT / COMMON).read_text(encoding="utf-8")
    both = ex + "\n" + cm
    ei = collect(ex)
    ci = collect(cm)
    ex_calls, ex_withs = ei["calls"], ei["withs"]

    def has(s, tok):
        return tok in s

    def has_any(s, toks):
        return any(t in s for t in toks)

    # ---- ORIGINAL 54 v1.0a checks, re-run against v1.0b ----
    g_load = fn_lines(ei, "load_g_component")
    b_load = fn_lines(ei, "load_bphi_component")
    g_hash_line = first_line_in_fn(ei, "load_g_component",
                                   lambda n: isinstance(n, ast.Call)
                                   and dotted(n.func) == "sha256_file")
    g_load_line = first_line_in_fn(ei, "load_g_component",
                                   lambda n: isinstance(n, ast.Call)
                                   and dotted(n.func) == "torch.load")
    b_hash_line = first_line_in_fn(ei, "load_bphi_component",
                                   lambda n: isinstance(n, ast.Call)
                                   and dotted(n.func) == "sha256_file")
    b_load_line = first_line_in_fn(ei, "load_bphi_component",
                                   lambda n: isinstance(n, ast.Call)
                                   and dotted(n.func) == "torch.load")
    allow_fn = fn_lines(ei, "load_gallery_allowlist")[0]
    persist_fn = fn_lines(ei, "load_persisted_p_global")[0]
    mask_fn = fn_lines(ei, "build_target_mask")[0]
    router_verify_fn = fn_lines(ei, "router_population_verify")[0]
    router_attr_fn = fn_lines(ei, "router_gradient_x_input")[0]
    display_fn = fn_lines(ei, "resolve_display_subset")[0]
    saliency_fn = fn_lines(ei, "saliency_self_consistency")[0]

    checks = OrderedDict([
        ("01_repo_imports_cwd_independent", has(ex, "Path(__file__).resolve().parents[2]")),
        ("02_phase34_closure_handoff_hashes_checked",
         has(cm, "phase34_final_closure.json") and has(cm, "phase34_phase35_handoff.json")
         and has(cm, "expected_sha256") is False and has(ex, "expected_sha256")),
        ("03_canonical_gallery_sha_checked_before_raw_read",
         has(cm, "2bc7c16286999ced374840cc987dcd352c3e546668322a9ccc4d1e8e8a097fd9")
         and has(ex, "canonical gallery SHA mismatch")),
        ("04_gallery_ownership_checked_before_raw_read",
         has(ex, "load_gallery_allowlist") and allow_fn is not None
         and allow_fn < persist_fn),
        ("05_router_holdout_prohibited", has(ex, "router_holdout") and "router_holdout" in ex.lower()),
        ("06_TEST_prohibited", has(ex, "/test/")),
        ("07_GT_reads_prohibited",
         has(ex, "GT/mask authority forbidden") and has(cm, 'PERSISTED_KEYS_FORBIDDEN')),
        ("08_canonical_G_checkpoint_used", has(cm, "phase21_global_medfilm")),
        ("09_canonical_B_phi_checkpoint_used", has(cm, "phase25d_barr_benefit_router")),
        ("10_R_psi_not_executed_v1_0",
         has(ex, "_assert_executable_component") and has(ex, "new_R_psi_visualization_forward_eligible")),
        ("11_S_omega_not_executed_v1_0",
         has(ex, "_assert_executable_component") and has(ex, "S_omega not required")),
        ("12_G_strict_loaded", has(ex, "load_state_dict") and has(ex, "strict=True")),
        ("13_B_phi_strict_loaded", has(ex, "load_state_dict") and has(ex, "strict=True")),
        ("14_G_parameter_count_verified", has(cm, "3523001") and has(ex, "parameter count mismatch")),
        ("15_B_phi_parameter_count_verified", has(cm, "36801") and has(ex, "parameter count mismatch")),
        ("16_film_parameters_for_tasks_implemented", has(ex, "film_parameters_for_tasks")),
        ("17_G_task_embedding_extraction_implemented",
         has(ex, "G_task_embedding_shape") and has(ex, "extract_task_embeddings")),
        ("18_B_phi_task_embedding_extraction_implemented", has(ex, "B_phi_task_embedding_shape")),
        ("19_gradcam_bridge_hook_exact",
         has(cm, 'film_layers["bridge"]') and has(ex, "g_model.film_layers[name]")
         and has(ex, 'layers=("bridge", "decoder1")')),
        ("20_gradcam_decoder1_hook_exact", has(cm, 'film_layers["decoder1"]')),
        ("21_target_mask_from_persisted_p_global_050",
         has(ex, "load_persisted_p_global") and has(ex, "C.T_SEGMENTATION_OUTPUT")),
        ("22_target_mask_not_recomputed_from_new_forward",
         has(ex, "TARGET_MASK_FROM_CURRENT_FORWARD_PROHIBITED")
         and has(ex, "target_masks_from_current_forward")),
        ("23_no_GT_in_target_selection",
         not has_any(ex.split("def build_target_mask")[1].split("def build_roi_mask")[0].lower(),
                     ("gt", "ground truth"))),
        ("24_scalar_target_matches_frozen_definitions",
         has(ex, "empty_prediction_fallback_used") and has(ex, "gradcam_target_scalar")),
        ("25_gradcam_forward_semantics_exact",
         has(ex, "torch.enable_grad()") and has(ex, "torch.amp.autocast")
         and not any("inference_mode" in w for w in ex_withs)
         and not any("no_grad" in w for w in ex_withs)),
        ("26_no_optimizer", not any(c.startswith("torch.optim") for c in ex_calls)),
        ("27_no_parameter_update", not any(c.endswith(".step") for c in ex_calls)),
        ("28_cam_formula_exact",
         has(ex, "mean(dim=(2, 3)") and has(ex, "relu") and has(ex, ".sum(dim=1")),
        ("29_align_corners_false",
         has(ex, 'C.GRADCAM_ALGORITHM["align_corners"]')
         and has(cm, '("align_corners", False)')),
        ("30_minmax_and_zero_range_exact", has(ex, "rng") and has(ex, "zeros_like")),
        ("31_no_blur_smoothing_posthoc_threshold",
         not has_any(ex, ("gaussian_blur", "morphology(", "blur("))
         and has(cm, '("post_hoc_saliency_threshold", False)')),
        ("32_ROI_proposal_uses_030",
         has(ex, "build_roi_mask") and has(ex, "C.T_ROI_PROPOSAL")),
        ("33_segmentation_foreground_uses_050",
         has(ex, "build_target_mask") and has(ex, "C.T_SEGMENTATION_OUTPUT")),
        ("34_thresholds_never_conflated",
         has(cm, "assert T_SEGMENTATION_OUTPUT != T_ROI_PROPOSAL")
         and has(ex, "C.T_SEGMENTATION_OUTPUT") and has(ex, "C.T_ROI_PROPOSAL")),
        ("35_64_case_raw_read_ceiling_enforced",
         has(cm, "MAX_RAW_VAL_IMAGE_READS = 64") and has(ex, "raw_val_image_reads")
         and has(ex, "outside the 64 allow-list")),
        ("36_display_subset_frozen_without_saliency_inspection",
         has(ex, "resolve_display_subset") and display_fn is not None),
        ("37_router_uses_canonical_VAL808_artifacts", has(cm, "phase29_val808_shared_fixed_g_v1_1_canonical")),
        ("38_router_population_n_808", has(cm, "ROUTER_POPULATION_N = 808")),
        ("39_router_raw_image_reads_0", has(ex, "router_raw_image_reads")),
        ("40_router_GT_reads_0", has(ex, "router_gt_reads")),
        ("41_B_phi_receives_canonical_task_ids", has(ex, "DOMAIN_TASK_ID")),
        ("42_B_phi_receives_canonical_normalization",
         has(ex, "router_normalized_features") and has(ex, "normalizer_mu")
         and has(ex, "normalizer_sigma")),
        ("43_router_target_raw_delta_hat", has(ex, "delta_hat")),
        ("44_no_sigmoid_on_delta_hat",
         not any("sigmoid" in c for c in ex_calls)
         and has(ex, '"sigmoid_applied": False')),
        ("45_numeric_feature_gradient_enabled", has(ex, "requires_grad_(True)")),
        ("46_attribution_x_times_grad", has(ex, "grads[0]) * xb")),
        ("47_integer_task_ids_no_numeric_gradient", has(ex, "dtype=torch.long")),
        ("48_B_phi_task_embedding_static", has(ex, "extract_task_embeddings")),
        ("49_zero_denominator_NULL_and_flag", has(ex, "ZERO_ROUTER_GRAD_ATTRIBUTION")),
        ("50_outcome_selected_galleries_prevented",
         has(cm, "OUTCOME_SELECTED_PANELS_PERMITTED = False")
         and has(ex, "display_subset_resolved_before_saliency")),
        ("51_no_phase30_holdout_raw_evidence_needed",
         "phase30" not in ex.lower()
         and not any("router_holdout" in l.lower()
                     and any(e in l.lower() for e in (".npy", ".csv", ".pt", ".npz",
                                                      ".png", ".jpg"))
                     for l in ei["literals"])),
        ("52_no_TEST_access", has(ex, "/test/")),
        ("53_no_training_path", has(ex, "training_backward_calls")),
        ("54_phase36_not_started", "phase36" not in ex.lower()),
    ])
    orig_failed = [k for k, v in checks.items() if not v]

    # ---- ADDITIONAL v1.0b checks ----
    extra = OrderedDict([
        ("v1_0_source_preserved", pres_ok),
        ("v1_0a_blocked_artifacts_preserved", all(p["match"] for p in pres[5:9])),
        ("gallery_sha_reconciliation_bound",
         has(ex, "AUTHORITY_GATES") and has(cm, "2bc7c16286999ced374840cc987dcd352c3e546668322a9ccc4d1e8e8a097fd9")),
        ("new_v1_0b_sources_contain_no_scientific_output_yet",
         not has_any(ex, ("savefig", "to_csv(", "write_text(", "np.save", "torch.save"))),
        ("mode_gate_exists", has(ex, "MODE_DISPATCH") and has(ex, "PHASE35_EXECUTE")),
        ("smoke_science_separation_exists",
         has(cm, 'MODES = ("smoke", "film", "gradcam", "router", "science")')
         and has(ex, "SCIENTIFIC_MODES")),
        ("display_subset_generated_before_any_saliency",
         display_fn is not None and saliency_fn is not None and display_fn < saliency_fn),
        ("persisted_prediction_lookup_precedes_target_mask",
         persist_fn is not None and mask_fn is not None and persist_fn < mask_fn),
        ("raw_image_allowlist_precedes_image_opening",
         allow_fn is not None and persist_fn is not None and allow_fn < persist_fn),
        ("router_population_verification_precedes_attribution",
         router_verify_fn is not None and router_attr_fn is not None
         and router_verify_fn < router_attr_fn),
        ("canonical_router_normalization_authority_bound",
         has(cm, "phase25d_final_normalization_stats.csv")
         and has(cm, "ROUTER_NORMALIZED_SCALAR_INDICES")),
        ("R_psi_has_no_executable_scientific_path",
         has(ex, "_assert_executable_component") and has(cm, 'NON_EXECUTABLE_COMPONENTS = ("R_psi", "S_omega")')),
        ("S_omega_has_no_executable_scientific_path",
         has(ex, "_assert_executable_component")),
        ("model_parameter_mutation_path_absent",
         not any(c.endswith(".step") for c in ex_calls)
         and not any("optim" in c for c in ex_calls)),
        ("checkpoint_hash_check_precedes_deserialize",
         g_hash_line is not None and g_load_line is not None and g_hash_line < g_load_line
         and b_hash_line is not None and b_load_line is not None and b_hash_line < b_load_line),
        ("phase36_remains_inaccessible", "phase36" not in ex.lower()),
        ("claim_guard_implemented", has(ex, "assert_claim_language")),
        ("F8_regional_not_implemented", has(cm, "F8_REGIONAL_IMPLEMENTED = False")),
    ])
    extra_failed = [k for k, v in extra.items() if not v]

    all_failed = orig_failed + extra_failed

    write_json(OrderedDict([
        ("artifact", "phase35_execution_source_static_preflight_v1_0b"),
        ("phase", 35), ("section", "\u00A7AF"), ("method", METHOD), ("revision", REVISION),
        ("method_of_inspection", "AST_PARSE_CONTROL_FLOW_AND_SHA256_HASHING"),
        ("sources", {"common_v1_0b": COMMON, "execution_v1_0b": EXEC,
                     "preflight_v1_0b": PREFLIGHT}),
        ("preservation", pres), ("preservation_all_match", pres_ok),
        ("original_v1_0a_checks", checks),
        ("original_n_checks", len(checks)),
        ("original_n_failed", len(orig_failed)), ("original_failed", orig_failed),
        ("original_54_all_pass", len(orig_failed) == 0),
        ("additional_v1_0b_checks", extra),
        ("additional_n_checks", len(extra)),
        ("additional_n_failed", len(extra_failed)), ("additional_failed", extra_failed),
        ("total_n_checks", len(checks) + len(extra)), ("total_n_failed", len(all_failed)),
        ("failed", all_failed), ("static_source_preflight_pass", len(all_failed) == 0),
        ("model_constructed", False), ("checkpoint_deserialized", False),
        ("forward_executed", False), ("backward_executed", False),
        ("raw_val_reads", 0), ("gt_reads", 0),
        ("generated_utc", gen), ("all_pass", len(all_failed) == 0),
    ]), OUT)

    print("=== PHASE35 v1.0b STATIC PREFLIGHT ===")
    print("preservation:", len(pres), "| all match:", pres_ok)
    print("ORIGINAL 54 checks:", len(checks), "| failed:", len(orig_failed))
    for k in orig_failed:
        print("  FAILED:", k)
    print("ADDITIONAL v1.0b checks:", len(extra), "| failed:", len(extra_failed))
    for k in extra_failed:
        print("  FAILED:", k)
    print("TOTAL:", len(checks) + len(extra), "checks,", len(all_failed), "failed")
    print("static_source_preflight_pass:", len(all_failed) == 0)
    print()
    for a in NEW:
        print(f"{a['sha256']}  {a['path']}")
    return 0 if not all_failed else 3


if __name__ == "__main__":
    main()
