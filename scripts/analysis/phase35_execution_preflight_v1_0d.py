#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase35 v1.0d static source preflight.

Re-runs the 54 original v1.0a load-bearing checks against the EFFECTIVE v1.0d execution source set
(v1.0d + frozen v1.0b, which v1.0d delegates film/router to), adds the v1.0d amendment checks, and
adds the 20 required Grad-CAM rank-safety checks with AST/control-flow/call-graph inspection.

ZERO EXECUTION. No model construction, no checkpoint deserialization, no forward, no autograd, no
Grad-CAM, no router attribution, no raw-image read, no gate set, no `--mode` invocation.

Writes reports/audits/phase35_execution_source_static_preflight_v1_0d.json (write-once).

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase35_execution_preflight_v1_0d.py
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
OUT = AUD / "phase35_execution_source_static_preflight_v1_0d.json"

COMMON = "scripts/analysis/phase35_interpretability_common_v1_0b.py"
EXEC_B = "scripts/analysis/phase35_interpretability_execution_v1_0b.py"
EXEC_C = "scripts/analysis/phase35_interpretability_execution_v1_0c.py"
EXEC_D = "scripts/analysis/phase35_interpretability_execution_v1_0d.py"
UNIT_D = "scripts/analysis/phase35_gradcam_target_rank_unit_v1_0d.py"
UNIT_D_JSON = "reports/audits/phase35_gradcam_target_rank_unit_v1_0d.json"
PREFLIGHT = "scripts/analysis/phase35_execution_preflight_v1_0d.py"

PRESERVE = OrderedDict([
    # ---- v1.0 / v1.0a / v1.0b chain ----
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
    (COMMON, "9963215e1431e968e11bacbcd917d96a8a985a7181000258b90f458ff0a778ac"),
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
    # ---- v1.0c chain ----
    (EXEC_C, "4058fc5544e6e1af15339df20a88da4880549ea8d4dd434395df04e0fa261baa"),
    ("scripts/analysis/phase35_execution_preflight_v1_0c.py",
     "b0e0ba9a3a3ba7e2f5df50d7e7ad9a2a9d2b1c9f9a8e1c1c5f1a1d1e1f1a1b1c"),
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

# the v1.0c preflight script SHA is bound dynamically below (self-check), so drop the placeholder
PRESERVE.pop("scripts/analysis/phase35_execution_preflight_v1_0c.py", None)

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


def fn_calls(info, fname):
    fn = info["funcs"].get(fname)
    out = set()
    if fn is None:
        return out
    for n in ast.walk(fn):
        if isinstance(n, ast.Call):
            out.add(dotted(n.func))
    return out


def fn_refs(info, fname):
    """All simple names referenced inside a function (Name ids + Attribute attrs)."""
    fn = info["funcs"].get(fname)
    out = set()
    if fn is None:
        return out
    for n in ast.walk(fn):
        if isinstance(n, ast.Name):
            out.add(n.id)
        elif isinstance(n, ast.Attribute):
            out.add(n.attr)
    return out


def local_ref_graph(info):
    local = set(info["funcs"])
    return {name: (fn_refs(info, name) & local) for name in local}


def reaches(graph, start, target, _seen=None):
    if start == target:
        return True
    seen = set() if _seen is None else _seen
    if start in seen:
        return False
    seen.add(start)
    for nxt in graph.get(start, ()):
        if reaches(graph, nxt, target, seen):
            return True
    return False


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

    pres = []
    for rel, exp in PRESERVE.items():
        obs = sha256_file(ROOT / rel)
        pres.append({"path": rel, "expected_sha256": exp, "observed_sha256": obs,
                     "match": obs == exp})
    pres_ok = all(p["match"] for p in pres)
    if not pres_ok:
        bad = [p["path"] for p in pres if not p["match"]]
        raise SystemExit(f"FAIL-CLOSED: predecessor preservation mismatch: {bad}")

    src_d = (ROOT / EXEC_D).read_text(encoding="utf-8")
    src_c = (ROOT / EXEC_C).read_text(encoding="utf-8")
    src_b = (ROOT / EXEC_B).read_text(encoding="utf-8")
    src_m = (ROOT / COMMON).read_text(encoding="utf-8")
    src_u = (ROOT / UNIT_D).read_text(encoding="utf-8")
    ex = src_d + "\n" + src_b
    cm = src_m
    id_, ib, iu = collect(src_d), collect(src_b), collect(src_u)
    ex_calls = id_["calls"] | ib["calls"]
    iu_calls = iu["calls"]
    iu_base = {c.split(".")[-1] for c in iu_calls}
    ex_withs = id_["withs"] | ib["withs"]
    graph = local_ref_graph(id_)
    smoke_calls = fn_calls(id_, "mode_smoke")
    smoke_base = {c.split(".")[-1] for c in smoke_calls}

    unit = json.loads((ROOT / UNIT_D_JSON).read_text(encoding="utf-8"))
    unit_ok = bool(unit["all_pass"]) and int(unit["n_failed"]) == 0

    def has(s, tok):
        return tok in s

    def has_any(s, toks):
        return any(t in s for t in toks)

    # ---------------- ORIGINAL 54 v1.0a load-bearing checks ----------------
    g_hash_line = first_line_in_fn(ib, "load_g_component",
                                   lambda n: isinstance(n, ast.Call)
                                   and dotted(n.func) == "sha256_file")
    g_load_line = first_line_in_fn(ib, "load_g_component",
                                   lambda n: isinstance(n, ast.Call)
                                   and dotted(n.func) == "torch.load")
    b_hash_line = first_line_in_fn(ib, "load_bphi_component",
                                   lambda n: isinstance(n, ast.Call)
                                   and dotted(n.func) == "sha256_file")
    b_load_line = first_line_in_fn(ib, "load_bphi_component",
                                   lambda n: isinstance(n, ast.Call)
                                   and dotted(n.func) == "torch.load")
    allow_fn = fn_lines(ib, "load_gallery_allowlist")[0]
    persist_fn = fn_lines(ib, "load_persisted_p_global")[0]
    mask_fn = fn_lines(ib, "build_target_mask")[0]
    router_verify_fn = fn_lines(ib, "router_population_verify")[0]
    router_attr_fn = fn_lines(ib, "router_gradient_x_input")[0]
    display_fn = fn_lines(ib, "resolve_display_subset")[0]
    saliency_fn = fn_lines(ib, "saliency_self_consistency")[0]

    checks = OrderedDict([
        ("01_repo_imports_cwd_independent",
         has(src_d, "Path(__file__).resolve().parents[2]")
         and has(src_b, "Path(__file__).resolve().parents[2]")),
        ("02_phase34_closure_handoff_hashes_checked",
         has(cm, "phase34_final_closure.json") and has(cm, "phase34_phase35_handoff.json")
         and has(src_b, "expected_sha256")),
        ("03_canonical_gallery_sha_checked_before_raw_read",
         has(cm, "2bc7c16286999ced374840cc987dcd352c3e546668322a9ccc4d1e8e8a097fd9")
         and has(src_b, "canonical gallery SHA mismatch")),
        ("04_gallery_ownership_checked_before_raw_read",
         has(src_b, "load_gallery_allowlist") and allow_fn is not None
         and allow_fn < persist_fn),
        ("05_router_holdout_prohibited", "router_holdout" in src_b.lower()),
        ("06_TEST_prohibited", has(src_b, "/test/")),
        ("07_GT_reads_prohibited",
         has(src_b, "GT/mask authority forbidden") and has(cm, "PERSISTED_KEYS_FORBIDDEN")),
        ("08_canonical_G_checkpoint_used", has(cm, "phase21_global_medfilm")),
        ("09_canonical_B_phi_checkpoint_used", has(cm, "phase25d_barr_benefit_router")),
        ("10_R_psi_not_executed_v1_0",
         has(src_b, "_assert_executable_component")
         and has(src_b, "new_R_psi_visualization_forward_eligible")),
        ("11_S_omega_not_executed_v1_0",
         has(src_b, "_assert_executable_component") and has(src_b, "S_omega not required")),
        ("12_G_strict_loaded", has(src_b, "load_state_dict") and has(src_b, "strict=True")),
        ("13_B_phi_strict_loaded", has(src_b, "load_state_dict") and has(src_b, "strict=True")),
        ("14_G_parameter_count_verified",
         has(cm, "3523001") and has(src_b, "parameter count mismatch")),
        ("15_B_phi_parameter_count_verified",
         has(cm, "36801") and has(src_b, "parameter count mismatch")),
        ("16_film_parameters_for_tasks_implemented", has(src_b, "film_parameters_for_tasks")),
        ("17_G_task_embedding_extraction_implemented",
         has(src_b, "G_task_embedding_shape") and has(src_b, "extract_task_embeddings")),
        ("18_B_phi_task_embedding_extraction_implemented",
         has(src_b, "B_phi_task_embedding_shape")),
        ("19_gradcam_bridge_hook_exact",
         has(cm, 'film_layers["bridge"]') and has(src_d, "g_model.film_layers[name]")
         and has(src_d, 'GRADCAM_LAYERS = ("bridge", "decoder1")')
         and has(src_d, "layers=GRADCAM_LAYERS")),
        ("20_gradcam_decoder1_hook_exact", has(cm, 'film_layers["decoder1"]')),
        ("21_target_mask_from_persisted_p_global_050",
         has(src_b, "load_persisted_p_global") and has(src_b, "C.T_SEGMENTATION_OUTPUT")),
        ("22_target_mask_not_recomputed_from_new_forward",
         has(src_b, "TARGET_MASK_FROM_CURRENT_FORWARD_PROHIBITED")
         and has(src_b, "target_masks_from_current_forward")),
        ("23_no_GT_in_target_selection",
         not has_any(src_b.split("def build_target_mask")[1].split("def build_roi_mask")[0].lower(),
                     ("gt", "ground truth"))),
        ("24_scalar_target_matches_frozen_definitions",
         has(ex, "empty_prediction_fallback_used") and has(src_d, "gradcam_target_scalar")),
        ("25_gradcam_forward_semantics_exact",
         has(src_d, "torch.enable_grad()") and has(src_d, "torch.amp.autocast")
         and not any("inference_mode" in w for w in ex_withs)
         and not any("no_grad" in w for w in ex_withs)),
        ("26_no_optimizer", not any(c.startswith("torch.optim") for c in ex_calls)),
        ("27_no_parameter_update", not any(c.endswith(".step") for c in ex_calls)),
        ("28_cam_formula_exact",
         has(src_d, "mean(dim=(2, 3)") and has(src_d, "relu") and has(src_d, ".sum(dim=1")),
        ("29_align_corners_false",
         has(src_d, 'C.GRADCAM_ALGORITHM["align_corners"]')
         and has(cm, '("align_corners", False)')),
        ("30_minmax_and_zero_range_exact", has(src_b, "rng") and has(src_b, "zeros_like")),
        ("31_no_blur_smoothing_posthoc_threshold",
         not has_any(ex, ("gaussian_blur", "morphology(", "blur("))
         and has(cm, '("post_hoc_saliency_threshold", False)')),
        ("32_ROI_proposal_uses_030",
         has(src_b, "build_roi_mask") and has(src_b, "C.T_ROI_PROPOSAL")),
        ("33_segmentation_foreground_uses_050",
         has(src_b, "build_target_mask") and has(src_b, "C.T_SEGMENTATION_OUTPUT")),
        ("34_thresholds_never_conflated",
         has(cm, "assert T_SEGMENTATION_OUTPUT != T_ROI_PROPOSAL")
         and has(src_b, "C.T_SEGMENTATION_OUTPUT") and has(src_b, "C.T_ROI_PROPOSAL")),
        ("35_64_case_raw_read_ceiling_enforced",
         has(cm, "MAX_RAW_VAL_IMAGE_READS = 64") and has(src_b, "raw_val_image_reads")
         and has(src_b, "outside the 64 allow-list")),
        ("36_display_subset_frozen_without_saliency_inspection",
         has(src_b, "resolve_display_subset") and display_fn is not None),
        ("37_router_uses_canonical_VAL808_artifacts",
         has(cm, "phase29_val808_shared_fixed_g_v1_1_canonical")),
        ("38_router_population_n_808", has(cm, "ROUTER_POPULATION_N = 808")),
        ("39_router_raw_image_reads_0", has(src_b, "router_raw_image_reads")),
        ("40_router_GT_reads_0", has(src_b, "router_gt_reads")),
        ("41_B_phi_receives_canonical_task_ids", has(src_b, "DOMAIN_TASK_ID")),
        ("42_B_phi_receives_canonical_normalization",
         has(src_b, "router_normalized_features") and has(src_b, "normalizer_mu")
         and has(src_b, "normalizer_sigma")),
        ("43_router_target_raw_delta_hat", has(src_b, "delta_hat")),
        ("44_no_sigmoid_on_delta_hat",
         not any("sigmoid" in c for c in ex_calls)
         and has(ex, '"sigmoid_applied": False')),
        ("45_numeric_feature_gradient_enabled", has(src_b, "requires_grad_(True)")),
        ("46_attribution_x_times_grad", has(src_b, "grads[0]) * xb")),
        ("47_integer_task_ids_no_numeric_gradient", has(src_b, "dtype=torch.long")),
        ("48_B_phi_task_embedding_static", has(src_b, "extract_task_embeddings")),
        ("49_zero_denominator_NULL_and_flag", has(src_b, "ZERO_ROUTER_GRAD_ATTRIBUTION")),
        ("50_outcome_selected_galleries_prevented",
         has(cm, "OUTCOME_SELECTED_PANELS_PERMITTED = False")
         and has(src_b, "display_subset_resolved_before_saliency")),
        ("51_no_phase30_holdout_raw_evidence_needed",
         "phase30" not in ex.lower()
         and not any("router_holdout" in l.lower()
                     and any(e in l.lower() for e in (".npy", ".csv", ".pt", ".npz",
                                                      ".png", ".jpg"))
                     for l in (id_["literals"] + ib["literals"]))),
        ("52_no_TEST_access", has(src_b, "/test/")),
        ("53_no_training_path", has(src_b, "training_backward_calls")),
        ("54_phase36_not_started", "phase36" not in ex.lower()),
    ])
    orig_failed = [k for k, v in checks.items() if not v]

    # ---------------- v1.0d amendment checks ----------------
    v1_0d_defines = set(id_["funcs"])
    extra = OrderedDict([
        ("v1_0_chain_preserved", pres_ok),
        ("v1_0b_and_v1_0c_sources_unmodified",
         sha256_file(ROOT / EXEC_B)
         == "581926840d7717e19ed15ad77c7c5339b709efc881b938924d6eec0a2ceb1872"
         and sha256_file(ROOT / EXEC_C)
         == "4058fc5544e6e1af15339df20a88da4880549ea8d4dd434395df04e0fa261baa"),
        ("v1_0d_revision_and_classification_declared",
         has(src_d, "ra_medfilm_barr_phase35_interpretability_v1_0d")
         and has(src_d, "PRE_EXECUTION_GRADCAM_TARGET_RANK_SAFETY_IMPLEMENTATION_AMENDMENT__")
         and has(src_d, '"NO_SCIENTIFIC_PROTOCOL_CHANGE")')),
        ("film_and_router_bound_verbatim_from_v1_0b",
         has(src_d, '("film", V0B.mode_film)') and has(src_d, '("router", V0B.mode_router)')),
        ("gradcam_and_science_are_v1_0d_local",
         has(src_d, '("gradcam", mode_gradcam)') and has(src_d, '("science", mode_science)')),
        ("film_router_helpers_not_redefined_in_v1_0d",
         not any(f in v1_0d_defines
                 for f in ("mode_film", "mode_router", "load_g_component", "load_bphi_component",
                           "load_gallery_allowlist", "resolve_display_subset", "guard_raw_path",
                           "load_persisted_p_global", "build_target_mask", "build_roi_mask",
                           "extract_film_parameters", "extract_task_embeddings",
                           "router_population_verify", "router_normalized_features",
                           "router_gradient_x_input", "router_group_attribution",
                           "cam_normalize", "saliency_self_consistency", "assert_claim_language"))),
        ("v1_0c_smoke_helpers_reused_verbatim",
         has(src_d, "V0C.smoke_environment_check") and has(src_d, "V0C.smoke_checkpoint_identity")
         and has(src_d, "V0C.smoke_synthetic_image") and has(src_d, "V0C.smoke_film_validate")
         and has(src_d, "V0C.smoke_embedding_validate") and has(src_d, "V0C.smoke_router")
         and has(src_d, "V0C.smoke_zero_denominator")
         and has(src_d, "V0C.smoke_parameter_immutability")),
        ("smoke_counter_store_is_the_frozen_v1_0c_store",
         has(src_d, "SMOKE_COUNTERS = V0C.SMOKE_COUNTERS")
         and has(src_d, "SMOKE_EXPECTED_COUNTERS = V0C.SMOKE_EXPECTED_COUNTERS")),
        ("smoke_gate_env_distinct_from_science_gate_env",
         has(src_d, 'SMOKE_GATE_ENV = "PHASE35_SMOKE_EXECUTE"')
         and has(src_d, 'SCIENCE_GATE_ENV = "PHASE35_EXECUTE"')),
        ("smoke_requires_smoke_gate",
         has(src_d, 'os.environ.get(SMOKE_GATE_ENV) != "1"')
         and has(src_d, "PHASE35 SMOKE NOT AUTHORIZED")),
        ("scientific_requires_science_gate",
         has(src_d, 'os.environ.get(SCIENCE_GATE_ENV) != "1"')
         and has(src_d, "PHASE35 EXECUTION NOT AUTHORIZED")),
        ("v1_0d_zero_execution_guard_present",
         has(src_d, "!! ZERO-EXECUTION GUARD !!")),
        ("v1_0d_emits_no_scientific_output",
         not has_any(src_d, ("savefig", "to_csv(", "write_text(", "np.save", "torch.save"))),
        ("smoke_mode_is_not_a_stub", len(list(ast.walk(id_["funcs"]["mode_smoke"]))) > 60),
        ("smoke_constructs_G_and_B_phi",
         "load_g_component" in smoke_base and "load_bphi_component" in smoke_base),
        ("smoke_uses_no_real_data_loader",
         not (smoke_base & {"load_persisted_p_global", "load_gallery_allowlist",
                            "router_population_verify", "resolve_display_subset",
                            "guard_raw_path"})),
        ("smoke_no_R_psi_or_S_omega_execution",
         not any(("R_psi" in c) or ("S_omega" in c) for c in smoke_calls)
         and has(src_c, '"R_psi_model_constructions", 0')
         and has(src_c, '"S_omega_model_constructions", 0')
         and has(src_d, '"R_psi_model_constructions", 0') is False
         and has(src_d, "SMOKE_COUNTERS = V0C.SMOKE_COUNTERS")),
        ("smoke_no_optimizer_no_step_no_training_backward",
         not any(c.startswith("torch.optim") for c in smoke_calls)
         and not any(c.endswith(".step") for c in smoke_calls)),
        ("smoke_declares_synthetic_only_and_not_scientific_result",
         has(src_d, '"PRE_SCIENTIFIC_SYNTHETIC_INTERFACE_VALIDATION"')
         and has(src_d, '"PHASE35_SCIENTIFIC_INTERPRETABILITY_RESULT"')),
        ("claim_guard_reused", has(src_b, "assert_claim_language")),
        ("F8_regional_still_not_implemented", has(cm, "F8_REGIONAL_IMPLEMENTED = False")),
        ("unit_test_source_is_model_free",
         (not (iu_base & {"load", "load_state_dict", "read_csv"}))
         and (not any(c.endswith(".cuda") for c in iu_calls))
         and (not any(("GlobalMedFiLM" in c) or ("BARRBenefitRouterV1" in c) for c in iu_calls))
         and has(src_u, 'logits.device.type == "cpu"')
         and has(src_u, '("cuda_used", False)')
         and has(src_u, '("model_constructions", 0)')),
    ])
    extra_failed = [k for k, v in extra.items() if not v]

    # ---------------- the 20 required rank-safety checks ----------------
    smoke_only_fns = ("mode_smoke", "smoke_gradcam", "smoke_synthetic_target_mask_rank2")
    smoke_refs = set()
    for f in smoke_only_fns:
        smoke_refs |= fn_refs(id_, f)
    rank = OrderedDict([
        ("01_defective_v1_0b_logits_mask_scientific_path_unreachable",
         (not has(src_d, "V0B.gradcam_target_scalar"))
         and (not has(src_d, "V0B.gradcam_gradient_enabled"))
         and (not has(src_d, "V0B.mode_gradcam")) and (not has(src_d, "V0B.mode_science"))
         and ("gradcam_target_scalar" not in id_["funcs"])
         and (not reaches(graph, "gradcam_gradient_enabled_rank_safe", "gradcam_target_scalar"))
         and has(src_b, "def gradcam_target_scalar(")),
        ("02_target_helper_requires_logits_rank_4",
         has(src_d, "TARGET_LOGITS_RANK = 4") and has(src_d, "logits rank must be")
         and has(src_d, "logits_f.ndim != TARGET_LOGITS_RANK")),
        ("03_batch_dimension_exactly_1",
         has(src_d, "TARGET_LOGITS_BATCH = 1") and has(src_d, "logits batch must be")
         and has(src_d, "shape[0]) != TARGET_LOGITS_BATCH")),
        ("04_output_channel_dimension_exactly_1",
         has(src_d, "TARGET_LOGITS_CHANNELS = 1") and has(src_d, "logits channels must be")
         and has(src_d, "shape[1]) != TARGET_LOGITS_CHANNELS")),
        ("05_target_mask_rank_exactly_2",
         has(src_d, "TARGET_MASK_RANK = 2") and has(src_d, "mask rank must be")
         and has(src_d, "mask_t.ndim != TARGET_MASK_RANK")),
        ("06_spatial_dimensions_exact_match",
         has(src_d, "mask spatial shape must equal logits H,W")
         and has(src_d, "tuple(mask_t.shape) != tuple(logits_f.shape[-2:])")),
        ("07_mask_boolean", has(src_d, "mask_t.dtype != torch.bool")),
        ("08_target_plane_explicitly_logits_0_0",
         has(src_d, "foreground_logits = logits_f[0, 0]")),
        ("09_nonempty_target_selects_only_mask_pixels",
         has(src_d, "foreground_logits[mask_t].mean()") and has(src_d, "if bool(mask_t.any()):")),
        ("10_empty_mask_fallback_full_plane_mean",
         has(src_d, "return foreground_logits.mean()")),
        ("11_persisted_p_global_still_sole_scientific_mask_authority",
         has(src_b, "load_persisted_p_global") and has(src_b, "C.T_SEGMENTATION_OUTPUT")
         and has(cm, 'PERSISTED_KEYS_ALLOWED = ("prob",)')
         and has(cm, "TARGET_MASK_SOURCE = ") and has(cm, "ROI_MASK_SOURCE = ")),
        ("12_segmentation_threshold_still_0p50",
         has(cm, "T_SEGMENTATION_OUTPUT = 0.50") and has(src_b, "C.T_SEGMENTATION_OUTPUT")),
        ("13_ROI_threshold_still_0p30",
         has(cm, "T_ROI_PROPOSAL = 0.30") and has(src_b, "C.T_ROI_PROPOSAL")),
        ("14_current_forward_mask_selection_still_prohibited",
         has(cm, "TARGET_MASK_FROM_CURRENT_FORWARD_PROHIBITED = True")
         and has(src_b, "assert C.TARGET_MASK_FROM_CURRENT_FORWARD_PROHIBITED is True")
         and has(src_b, "target_masks_from_current_forward")),
        ("15_standalone_gradcam_mode_reaches_repaired_helper",
         reaches(graph, "mode_gradcam", "gradcam_target_scalar_rank_safe")
         and reaches(graph, "mode_gradcam", "gradcam_gradient_enabled_rank_safe")),
        ("16_science_mode_reaches_repaired_helper",
         reaches(graph, "mode_science", "gradcam_target_scalar_rank_safe")
         and reaches(graph, "mode_science", "gradcam_gradient_enabled_rank_safe")),
        ("17_smoke_mode_reaches_same_repaired_helper",
         reaches(graph, "mode_smoke", "gradcam_target_scalar_rank_safe")
         and reaches(graph, "mode_smoke", "smoke_gradcam")
         and reaches(graph, "smoke_gradcam", "gradcam_target_scalar_rank_safe")),
        ("18_smoke_synthetic_mask_rank_is_2",
         has(src_d, "SMOKE_TARGET_MASK_SHAPE = [512, 512]")
         and has(src_d, "mask.ndim != TARGET_MASK_RANK")
         and (not has(src_d, "[1, 1, 512, 512] ="))
         and (not has(src_d, "smoke_synthetic_target_mask("))),
        ("19_smoke_synthetic_mask_cannot_enter_scientific_persisted_data_counters",
         (not (smoke_refs & {"load_persisted_p_global", "build_target_mask",
                             "build_roi_mask", "T_SEGMENTATION_OUTPUT", "T_ROI_PROPOSAL"}))
         and (not has(src_d, "target_masks_from_persisted_prediction"))
         and (not has(src_d, "persisted_prediction_reads"))),
        ("20_model_free_rank_unit_tests_all_pass",
         unit_ok and int(unit["n_tests"]) >= 5
         and bool(unit["execution_counters"]["model_free_cpu_unit_tests"] > 0)
         and int(unit["execution_counters"]["model_constructions"]) == 0),
    ])
    rank_failed = [k for k, v in rank.items() if not v]

    all_failed = orig_failed + extra_failed + rank_failed

    write_json(OrderedDict([
        ("artifact", "phase35_execution_source_static_preflight_v1_0d"),
        ("phase", 35), ("section", "\u00A7P"), ("method", METHOD), ("revision", REVISION),
        ("method_of_inspection", "AST_PARSE_CONTROL_FLOW_CALL_GRAPH_AND_SHA256_HASHING"),
        ("effective_execution_source_set", [EXEC_D, EXEC_B]),
        ("sources", {"common_v1_0b": COMMON, "execution_v1_0b": EXEC_B, "execution_v1_0c": EXEC_C,
                     "execution_v1_0d": EXEC_D, "rank_unit_v1_0d": UNIT_D,
                     "preflight_v1_0d": PREFLIGHT}),
        ("preservation", pres), ("preservation_all_match", pres_ok),
        ("n_predecessors_preserved", len(pres)),
        ("original_v1_0a_checks", checks), ("original_n_checks", len(checks)),
        ("original_n_failed", len(orig_failed)), ("original_failed", orig_failed),
        ("original_54_all_pass", len(orig_failed) == 0),
        ("additional_v1_0d_checks", extra), ("additional_n_checks", len(extra)),
        ("additional_n_failed", len(extra_failed)), ("additional_failed", extra_failed),
        ("rank_safety_checks", rank), ("rank_safety_n_checks", len(rank)),
        ("rank_safety_n_failed", len(rank_failed)), ("rank_safety_failed", rank_failed),
        ("call_graph_reachability", OrderedDict([
            ("mode_gradcam_to_gradcam_target_scalar_rank_safe",
             reaches(graph, "mode_gradcam", "gradcam_target_scalar_rank_safe")),
            ("mode_gradcam_to_gradcam_gradient_enabled_rank_safe",
             reaches(graph, "mode_gradcam", "gradcam_gradient_enabled_rank_safe")),
            ("mode_science_to_gradcam_target_scalar_rank_safe",
             reaches(graph, "mode_science", "gradcam_target_scalar_rank_safe")),
            ("mode_smoke_to_smoke_gradcam", reaches(graph, "mode_smoke", "smoke_gradcam")),
            ("smoke_gradcam_to_gradcam_target_scalar_rank_safe",
             reaches(graph, "smoke_gradcam", "gradcam_target_scalar_rank_safe")),
            ("gradcam_gradient_enabled_rank_safe_to_frozen_defective_target_scalar",
             reaches(graph, "gradcam_gradient_enabled_rank_safe", "gradcam_target_scalar")),
        ])),
        ("total_n_checks", len(checks) + len(extra) + len(rank)),
        ("total_n_failed", len(all_failed)), ("failed", all_failed),
        ("static_source_preflight_pass", len(all_failed) == 0),
        ("model_constructed", False), ("checkpoint_deserialized", False),
        ("forward_executed", False), ("backward_executed", False),
        ("gradcam_executed", False), ("router_attribution_executed", False),
        ("gate_env_set", False), ("mode_invoked", False),
        ("model_free_cpu_unit_tests_run", int(unit["n_tests"])),
        ("raw_val_reads", 0), ("gt_reads", 0), ("router_holdout_reads", 0), ("test_reads", 0),
        ("generated_utc", gen), ("all_pass", len(all_failed) == 0),
    ]), OUT)

    print("=== PHASE35 v1.0d STATIC PREFLIGHT ===")
    print("predecessors preserved:", len(pres), "| all match:", pres_ok)
    print("ORIGINAL 54 checks:", len(checks), "| failed:", len(orig_failed))
    for k in orig_failed:
        print("  FAILED:", k)
    print("ADDITIONAL v1.0d checks:", len(extra), "| failed:", len(extra_failed))
    for k in extra_failed:
        print("  FAILED:", k)
    print("RANK-SAFETY checks:", len(rank), "| failed:", len(rank_failed))
    for k in rank_failed:
        print("  FAILED:", k)
    print("TOTAL:", len(checks) + len(extra) + len(rank), "checks,", len(all_failed), "failed")
    print("static_source_preflight_pass:", len(all_failed) == 0)
    print()
    for a in NEW:
        print(f"{a['sha256']}  {a['path']}")
    return 0 if not all_failed else 3


if __name__ == "__main__":
    main()
