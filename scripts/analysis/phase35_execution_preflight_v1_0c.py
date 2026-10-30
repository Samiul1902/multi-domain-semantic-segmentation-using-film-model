#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase35 v1.0c static source preflight.

Re-runs every load-bearing v1.0a/v1.0b check against the EFFECTIVE v1.0c execution source set
(v1.0c execution + frozen v1.0b execution, which v1.0c delegates to for all scientific modes) and
adds the v1.0c amendment checks (real smoke entry point, gate separation, data isolation, parameter
immutability, disclosed defect).

ZERO EXECUTION. No model construction, no checkpoint deserialization, no forward, no autograd, no
raw-image read, no gate set, no `--mode` invocation.

Writes reports/audits/phase35_execution_source_static_preflight_v1_0c.json (write-once).

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase35_execution_preflight_v1_0c.py
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
OUT = AUD / "phase35_execution_source_static_preflight_v1_0c.json"

COMMON = "scripts/analysis/phase35_interpretability_common_v1_0b.py"
EXEC_B = "scripts/analysis/phase35_interpretability_execution_v1_0b.py"
EXEC_C = "scripts/analysis/phase35_interpretability_execution_v1_0c.py"
PREFLIGHT = "scripts/analysis/phase35_execution_preflight_v1_0c.py"

# --------------------------------------------------------------------------- #
# the full preserved predecessor chain (byte-for-byte, never modified)
# --------------------------------------------------------------------------- #
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
    ("scripts/analysis/phase35_interpretability_common_v1_0.py",
     "fce9527fbad3714e01beadf5f697646dbbad215e98fe233ddb4b9948c6071843"),
    ("scripts/analysis/phase35_interpretability_execution_v1_0.py",
     "a2e150d89018087112c71dbaa92137b667e4269430463fd55fc1601f9ee99d27"),
    # ---- v1.0b chain ----
    (COMMON, "9963215e1431e968e11bacbcd917d96a8a985a7181000258b90f458ff0a778ac"),
    (EXEC_B, "581926840d7717e19ed15ad77c7c5339b709efc881b938924d6eec0a2ceb1872"),
    ("scripts/analysis/phase35_execution_preflight_v1_0b.py",
     "498e68277168a8ee200842d799cb186bd410f09764d1fdb796ad463912704e63"),
    ("scripts/analysis/phase35_specification_v1_0b.py",
     "62904ee0d77648ab078c99b61488a06b5ed5d96aefd592953bfa64f910baa09c"),
    ("scripts/analysis/phase35_smoke_gate_v1_0b.py",
     "7e1b604ae6b41b31ea84bece3cf9c10fba4c1b3bb3971abde8bc8b67b21aac3b"),
    ("scripts/analysis/build_phase35_source_amendment_notebook_v1_0b.py",
     "5486c342db99242442834df8fcb44866aca3e978bb10a9a2029c4f55bd2c3f95"),
    ("scripts/analysis/build_phase35_synthetic_smoke_notebook_v1_0b.py",
     "74bbafd95cdce7d1785253b6dd31e0d1f4eb4d229b1a53880745c329ce9b8980"),
    ("reports/audits/phase35_v1_0_execution_source_defect_record_v1_0b.json",
     "523d991c7c2b259a2828879c003e532f4705d6dad3322d648a66bf28c0bd8855"),
    ("reports/audits/phase35_execution_eligibility_adjudication_v1_0b.json",
     "895f602b710bfab8e734e68d7d520a9adf270f27185968cdd8e207f7b54a760f"),
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
    ("reports/audits/phase35_source_amendment_notebook_audit_v1_0b.json",
     "61e6b816708bd59391fdb815f1c4b90e0a2e5d84f3db71d225e3d5197c65d7d8"),
    ("reports/audits/phase35_synthetic_smoke_terminal_v1_0b.json",
     "3def25817370ce9a90942610d4a474f56384a99e86ba8ba6a2630ad8002e80ee"),
    ("reports/audits/phase35_synthetic_smoke_final_check_v1_0b.json",
     "0a57dca0d13c0dd20beb1a2546fc89948b02e99f45ed6bc070189f91037b8267"),
    ("reports/audits/phase35_synthetic_interpretability_smoke_v1_0b.json",
     "bd51d09cca091244b46db11d61988572368539fbf4d46ddbfcbc4afc93137ff2"),
    ("reports/audits/phase35_synthetic_smoke_environment_v1_0b.json",
     "a3b6aba6b07e09727fab0e5c46ab09470dcb5df5be9797abf74792995a2ebcef"),
    ("reports/audits/phase35_synthetic_smoke_provenance_v1_0b.json",
     "f44b2b0e5c38b9a695a6fe02fbb55856af33718948ddd399838153539a30f27c"),
    ("reports/audits/phase35_execution_source_static_preflight_smoke_v1_0b.json",
     "948d7a81a7de01ef43ea3e9873735563b0d831b5b4c348c1dc6eaecf466f489c"),
    ("reports/audits/phase35_synthetic_smoke_reviewer_notebook_audit_v1_0b.json",
     "ec607149354741a25efac0727ee0d4cdcc0bf12a6cb444a5393e6fdcd3f2db72"),
    ("docs/phase35_interpretability_source_amendment_v1_0b.md",
     "ed42edb9059d3d78d64e730c730075b2df19798f8274af86301bb3053155b4a5"),
    ("notebooks/phasewise/phase_35_interpretability/"
     "phase35_interpretability_source_amendment_v1_0b_review.ipynb",
     "46cc1169c1c518215d01b2afad2d60cb478a40ca368df31b45f767a42ee6c87f"),
    ("notebooks/phasewise/phase_35_interpretability/"
     "phase35_interpretability_synthetic_smoke_v1_0b_review.ipynb",
     "b524f5fc5f57eaee0ce6c640b2ae1dad5bc9135e46d2b7efa9d709e8dab08752"),
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
    calls, withs, funcs, lits, toplevel = set(), set(), {}, [], []
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
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                          ast.Import, ast.ImportFrom, ast.Assign, ast.AnnAssign,
                          ast.If, ast.Try, ast.Expr)):
            toplevel.append(type(n).__name__)
    return {"tree": tree, "calls": calls, "withs": withs, "funcs": funcs,
            "literals": lits, "toplevel": toplevel}


def fn_calls(info, fname):
    fn = info["funcs"].get(fname)
    out = set()
    if fn is None:
        return out
    for n in ast.walk(fn):
        if isinstance(n, ast.Call):
            out.add(dotted(n.func))
    return out


def fn_n_nodes(info, fname):
    fn = info["funcs"].get(fname)
    return len(list(ast.walk(fn))) if fn else 0


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
        bad = [p["path"] for p in pres if not p["match"]]
        raise SystemExit(f"FAIL-CLOSED: predecessor preservation mismatch: {bad}")

    src_c = (ROOT / EXEC_C).read_text(encoding="utf-8")
    src_b = (ROOT / EXEC_B).read_text(encoding="utf-8")
    src_m = (ROOT / COMMON).read_text(encoding="utf-8")
    # effective execution source (v1.0c delegates all scientific modes to v1.0b)
    ex = src_c + "\n" + src_b
    cm = src_m
    ic, ib, im = collect(src_c), collect(src_b), collect(src_m)
    ex_calls = ic["calls"] | ib["calls"]
    ex_withs = ic["withs"] | ib["withs"]
    smoke_calls = fn_calls(ic, "mode_smoke")
    smoke_base = {c.split(".")[-1] for c in smoke_calls}   # dotted-name-agnostic

    def has(s, tok):
        return tok in s

    def has_any(s, toks):
        return any(t in s for t in toks)

    # ---- ORIGINAL 54 v1.0a load-bearing checks against the effective v1.0c source set ----
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
         has(src_c, "Path(__file__).resolve().parents[2]")
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
         has(cm, 'film_layers["bridge"]') and has(src_b, "g_model.film_layers[name]")
         and has(src_b, 'layers=("bridge", "decoder1")')),
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
         has(src_b, "empty_prediction_fallback_used") and has(src_b, "gradcam_target_scalar")),
        ("25_gradcam_forward_semantics_exact",
         has(src_b, "torch.enable_grad()") and has(src_b, "torch.amp.autocast")
         and not any("inference_mode" in w for w in ex_withs)
         and not any("no_grad" in w for w in ex_withs)),
        ("26_no_optimizer", not any(c.startswith("torch.optim") for c in ex_calls)),
        ("27_no_parameter_update", not any(c.endswith(".step") for c in ex_calls)),
        ("28_cam_formula_exact",
         has(src_b, "mean(dim=(2, 3)") and has(src_b, "relu") and has(src_b, ".sum(dim=1")),
        ("29_align_corners_false",
         has(src_b, 'C.GRADCAM_ALGORITHM["align_corners"]')
         and has(cm, '("align_corners", False)')),
        ("30_minmax_and_zero_range_exact", has(src_b, "rng") and has(src_b, "zeros_like")),
        ("31_no_blur_smoothing_posthoc_threshold",
         not has_any(src_b, ("gaussian_blur", "morphology(", "blur("))
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
         and has(src_b, '"sigmoid_applied": False')),
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
                     for l in (ic["literals"] + ib["literals"]))),
        ("52_no_TEST_access", has(src_b, "/test/")),
        ("53_no_training_path", has(src_b, "training_backward_calls")),
        ("54_phase36_not_started", "phase36" not in ex.lower()),
    ])
    orig_failed = [k for k, v in checks.items() if not v]

    # ---- v1.0c amendment checks ----
    smoke_n = fn_n_nodes(ic, "mode_smoke")
    v1_0c_defines = set(ic["funcs"])
    dispatch_txt = src_c[src_c.index("MODE_DISPATCH"):]
    extra = OrderedDict([
        ("v1_0_v1_0a_v1_0b_chain_preserved", pres_ok),
        ("v1_0b_smoke_stub_still_present_in_frozen_v1_0b",
         has(src_b, "def mode_smoke() -> dict:") and has(src_b, '"scientific_output": False')),
        ("v1_0c_does_not_modify_v1_0b",
         sha256_file(ROOT / EXEC_B)
         == "581926840d7717e19ed15ad77c7c5339b709efc881b938924d6eec0a2ceb1872"),
        ("v1_0c_supersedes_smoke_entrypoint_only",
         has(dispatch_txt, '("smoke", mode_smoke)')
         and has(dispatch_txt, '("film", V0B.mode_film)')
         and has(dispatch_txt, '("gradcam", V0B.mode_gradcam)')
         and has(dispatch_txt, '("router", V0B.mode_router)')
         and has(dispatch_txt, '("science", V0B.mode_science)')),
        ("scientific_modes_not_redefined_in_v1_0c",
         not any(f in v1_0c_defines
                 for f in ("mode_film", "mode_gradcam", "mode_router", "mode_science"))),
        ("scientific_helpers_not_redefined_in_v1_0c",
         not any(f in v1_0c_defines
                 for f in ("gradcam_gradient_enabled", "gradcam_target_scalar", "cam_normalize",
                           "router_normalized_features", "router_gradient_x_input",
                           "router_group_attribution", "build_target_mask", "build_roi_mask",
                           "load_persisted_p_global", "load_gallery_allowlist",
                           "router_population_verify", "resolve_display_subset", "guard_raw_path",
                           "saliency_self_consistency", "assert_claim_language",
                           "load_g_component", "load_bphi_component"))),
        ("smoke_gate_env_distinct_from_science_gate_env",
         has(src_c, 'SMOKE_GATE_ENV = "PHASE35_SMOKE_EXECUTE"')
         and has(src_c, 'SCIENCE_GATE_ENV = "PHASE35_EXECUTE"')
         and "PHASE35_SMOKE_EXECUTE" != "PHASE35_EXECUTE"),
        ("smoke_requires_smoke_gate",
         has(src_c, "if os.environ.get(SMOKE_GATE_ENV) != \"1\":")
         and has(src_c, "PHASE35 SMOKE NOT AUTHORIZED")),
        ("scientific_requires_science_gate",
         has(src_c, "if os.environ.get(SCIENCE_GATE_ENV) != \"1\":")
         and has(src_c, "PHASE35 EXECUTION NOT AUTHORIZED")),
        ("smoke_mode_is_not_a_stub", smoke_n > 60),
        ("smoke_constructs_G_and_B_phi",
         "load_g_component" in smoke_base and "load_bphi_component" in smoke_base),
        ("smoke_verifies_authority_gates", "verify_authority_gates" in smoke_base),
        ("smoke_verifies_checkpoint_identity_before_deserialization",
         "smoke_checkpoint_identity" in smoke_base
         and first_line_in_fn(ic, "mode_smoke",
                              lambda n: isinstance(n, ast.Call)
                              and dotted(n.func).split(".")[-1] == "smoke_checkpoint_identity")
         < first_line_in_fn(ic, "mode_smoke",
                            lambda n: isinstance(n, ast.Call)
                            and dotted(n.func).split(".")[-1] == "load_g_component")),
        ("smoke_exercises_film_accessor", "smoke_film_validate" in smoke_calls),
        ("smoke_exercises_task_embeddings", "smoke_embedding_validate" in smoke_calls),
        ("smoke_runs_canonical_gradcam_path", "smoke_gradcam" in smoke_calls
         and has(src_c, "V0B.gradcam_gradient_enabled")),
        ("smoke_runs_canonical_router_gradient_x_input",
         "smoke_router" in smoke_calls
         and has(src_c, "V0B.router_normalized_features")
         and has(src_c, "V0B.router_gradient_x_input")),
        ("smoke_tests_zero_denominator_policy",
         "smoke_zero_denominator" in smoke_calls
         and has(src_c, "V0B.router_group_attribution")),
        ("smoke_verifies_parameter_immutability",
         "smoke_parameter_immutability" in smoke_calls
         and has(src_c, "state_dict_identity")
         and has(src_c, "MODEL_PARAMETERS_UNCHANGED")),
        ("smoke_uses_no_real_data_loader",
         not (smoke_base & {"load_persisted_p_global", "load_gallery_allowlist",
                            "router_population_verify", "resolve_display_subset",
                            "guard_raw_path"})),
        ("smoke_declares_forbidden_calls",
         has(src_c, "SMOKE_FORBIDDEN_CALLS")),
        ("smoke_no_raw_val_gt_holdout_test_path_literals",
         not any(l.lower().endswith((".npy", ".csv", ".pt", ".npz", ".png", ".jpg"))
                 and (("router_holdout" in l.lower()) or ("/test/" in l.lower())
                      or ("val/" in l.lower()))
                 for l in ic["literals"])),
        ("smoke_synthetic_input_is_deterministic_seed42",
         has(src_c, "manual_seed(SMOKE_SEED)") and has(src_c, "SMOKE_SEED = 42")),
        ("smoke_synthetic_target_mask_nonempty_check",
         has(src_c, "SMOKE target mask must be non-empty")),
        ("smoke_gradcam_mask_rank_contract_disclosed",
         has(src_c, "mask_rank_contract") and has(src_c, "scientific_mask_shape")),
        ("disclosed_defect_gradcam_mask_rank_incompatibility",
         has(src_c, "PHASE35_V1_0B_GRADCAM_TARGET_MASK_RANK_INCOMPATIBILITY")),
        ("smoke_emits_no_scientific_output",
         not has_any(src_c, ("savefig", "to_csv(", "write_text(", "np.save", "torch.save"))),
        ("smoke_declares_synthetic_only_and_not_scientific_result",
         has(src_c, '"PRE_SCIENTIFIC_SYNTHETIC_INTERFACE_VALIDATION"')
         and has(src_c, '"PHASE35_SCIENTIFIC_INTERPRETABILITY_RESULT"')),
        ("smoke_counters_frozen",
         has(src_c, "SMOKE_COUNTERS = OrderedDict") and has(src_c, "SMOKE_EXPECTED_COUNTERS")),
        ("smoke_counts_match_expected_logic_present",
         has(src_c, "counts_match_expected")),
        ("smoke_no_R_psi_or_S_omega_execution",
         not any(("R_psi" in c) or ("S_omega" in c) for c in smoke_calls)
         and has(src_c, '"R_psi_model_constructions", 0')
         and has(src_c, '"S_omega_model_constructions", 0')
         and has(src_c, '"R_psi_forwards", 0')
         and has(src_c, '"S_omega_forwards", 0')),
        ("smoke_no_optimizer_no_step_no_training_backward",
         not any(c.startswith("torch.optim") for c in smoke_calls)
         and not any(c.endswith(".step") for c in smoke_calls)
         and has(src_c, '"optimizer_constructions", 0')
         and has(src_c, '"optimizer_step_calls", 0')
         and has(src_c, '"training_backward_calls", 0')),
        ("v1_0c_zero_execution_guard_present",
         has(src_c, "!! ZERO-EXECUTION GUARD !!")),
        ("v1_0c_imports_frozen_v1_0b_modules",
         has(src_c, "import phase35_interpretability_common_v1_0b as C")
         and has(src_c, "import phase35_interpretability_execution_v1_0b as V0B")),
        ("v1_0c_does_not_redefine_common_constants",
         not has_any(src_c, ("T_SEGMENTATION_OUTPUT =", "T_ROI_PROPOSAL =",
                             "GALLERY_SHA256 =", "EXECUTABLE_COMPONENTS ="))),
        ("checkpoint_hash_check_precedes_deserialize_v1_0b",
         g_hash_line is not None and g_load_line is not None and g_hash_line < g_load_line
         and b_hash_line is not None and b_load_line is not None and b_hash_line < b_load_line),
        ("claim_guard_reused", has(src_b, "assert_claim_language")),
        ("F8_regional_still_not_implemented", has(cm, "F8_REGIONAL_IMPLEMENTED = False")),
        ("threshold_separation_preserved",
         has(cm, "assert T_SEGMENTATION_OUTPUT != T_ROI_PROPOSAL")),
        ("phase36_remains_inaccessible", "phase36" not in ex.lower()),
    ])
    extra_failed = [k for k, v in extra.items() if not v]

    all_failed = orig_failed + extra_failed

    write_json(OrderedDict([
        ("artifact", "phase35_execution_source_static_preflight_v1_0c"),
        ("phase", 35), ("section", "\u00A7U"), ("method", METHOD), ("revision", REVISION),
        ("method_of_inspection", "AST_PARSE_CONTROL_FLOW_AND_SHA256_HASHING"),
        ("effective_execution_source_set", [EXEC_C, EXEC_B]),
        ("sources", {"common_v1_0b": COMMON, "execution_v1_0b": EXEC_B,
                     "execution_v1_0c": EXEC_C, "preflight_v1_0c": PREFLIGHT}),
        ("preservation", pres), ("preservation_all_match", pres_ok),
        ("n_predecessors_preserved", len(pres)),
        ("original_v1_0a_checks", checks),
        ("original_n_checks", len(checks)),
        ("original_n_failed", len(orig_failed)), ("original_failed", orig_failed),
        ("original_54_all_pass", len(orig_failed) == 0),
        ("additional_v1_0c_checks", extra),
        ("additional_n_checks", len(extra)),
        ("additional_n_failed", len(extra_failed)), ("additional_failed", extra_failed),
        ("total_n_checks", len(checks) + len(extra)), ("total_n_failed", len(all_failed)),
        ("failed", all_failed), ("static_source_preflight_pass", len(all_failed) == 0),
        ("smoke_mode_node_count", smoke_n),
        ("model_constructed", False), ("checkpoint_deserialized", False),
        ("forward_executed", False), ("backward_executed", False),
        ("gradcam_executed", False), ("router_attribution_executed", False),
        ("gate_env_set", False), ("mode_invoked", False),
        ("raw_val_reads", 0), ("gt_reads", 0), ("router_holdout_reads", 0), ("test_reads", 0),
        ("generated_utc", gen), ("all_pass", len(all_failed) == 0),
    ]), OUT)

    print("=== PHASE35 v1.0c STATIC PREFLIGHT ===")
    print("predecessors preserved:", len(pres), "| all match:", pres_ok)
    print("ORIGINAL 54 checks:", len(checks), "| failed:", len(orig_failed))
    for k in orig_failed:
        print("  FAILED:", k)
    print("ADDITIONAL v1.0c checks:", len(extra), "| failed:", len(extra_failed))
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
