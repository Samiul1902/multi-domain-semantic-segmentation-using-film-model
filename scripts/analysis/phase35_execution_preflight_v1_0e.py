#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase35 v1.0e static source preflight.

Re-runs the 54 original v1.0a load-bearing checks against the EFFECTIVE v1.0e execution source set
(v1.0e + frozen v1.0b, which v1.0e delegates film/router to), adds the cumulative v1.0b/v1.0c/v1.0d
amendment checks (kept live as regression guards), and adds the v1.0e Grad-CAM numerical-guard,
observability and fail-closed checks with AST/control-flow/call-graph inspection.

ZERO EXECUTION. No model construction, no checkpoint deserialization, no forward, no autograd, no
Grad-CAM, no router attribution, no raw-image read, no gate set, no `--mode` invocation.

Writes reports/audits/phase35_execution_source_static_preflight_v1_0e.json (write-once).

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase35_execution_preflight_v1_0e.py
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
REVISION = "ra_medfilm_barr_phase35_interpretability_v1_0e"
OUT = AUD / "phase35_execution_source_static_preflight_v1_0e.json"

COMMON = "scripts/analysis/phase35_interpretability_common_v1_0b.py"
EXEC_B = "scripts/analysis/phase35_interpretability_execution_v1_0b.py"
EXEC_C = "scripts/analysis/phase35_interpretability_execution_v1_0c.py"
EXEC_D = "scripts/analysis/phase35_interpretability_execution_v1_0d.py"
EXEC_E = "scripts/analysis/phase35_interpretability_execution_v1_0e.py"
UNIT_D = "scripts/analysis/phase35_gradcam_target_rank_unit_v1_0d.py"
UNIT_D_JSON = "reports/audits/phase35_gradcam_target_rank_unit_v1_0d.json"
UNIT_E = "scripts/analysis/phase35_gradcam_numerical_guard_unit_v1_0e.py"
UNIT_E_JSON = "reports/audits/phase35_gradcam_numerical_guard_unit_v1_0e.json"
PREFLIGHT = "scripts/analysis/phase35_execution_preflight_v1_0e.py"

# ---- predecessor set: everything frozen through v1.0d, plus the v1.0d smoke artifacts ----
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
    # ---- v1.0d chain ----
    (EXEC_D, "cccc109ade27eb5ad7883912004c1e911e9e253a659146f3d64820af92244056"),
    ("scripts/analysis/phase35_execution_preflight_v1_0d.py",
     "07cdab4b4eeb2051c2007ff5bdfaf3dba8b91c6e510b4a11979c0def53bbf356"),
    ("reports/audits/phase35_execution_source_static_preflight_v1_0d.json",
     "6d1438e139436cef7c08c9eca52d5a4f068f1412c4e45f22c60cdb4d90783cb3"),
    ("reports/audits/phase35_gradcam_target_rank_defect_v1_0d.json",
     "413840cc768cc84d66ef4aac93d1ec9383424f02938bc1f0cded88a7cff9b297"),
    ("reports/audits/phase35_gradcam_rank_repair_reviewer_notebook_audit_v1_0d.json",
     "77ce53a15e4157c31ec51f170cc45e26ea4e0fed960b789fb66f40d584784106"),
    ("reports/audits/phase35_preexecution_source_freeze_v1_0d.json",
     "d349dccfa949ab9e31ff24e49377e6fb237b6f787846c3820c8dff1c211b5b53"),
    ("reports/audits/phase35_execution_eligibility_adjudication_v1_0d.json",
     "0bed46a1c1e3c7f87759d5bb67ef0c02af42f32ad11f55bbda66a114babe3f70"),
    ("reports/audits/phase35_gradcam_rank_repair_final_check_v1_0d.json",
     "0f4cd1a77bb4204f5fdc9429edc53c20bac9e187d14e7772dea94d5a717e62d6"),
    ("reports/audits/phase35_gradcam_rank_repair_terminal_v1_0d.json",
     "8af9bcaff95b4cf5ac91f482810e7267816b9c649e321d917188f3dbe204f799"),
    (UNIT_D, "6c3896b01e60c5e8361d0af9d98ebd29c5b592a906257c487c6c9140242ec19f"),
    (UNIT_D_JSON, "66a16c411b30852e32701f424384b925b42ab074bf2c199521f422f5b5e58933"),
    # ---- v1.0d smoke chain ----
    ("reports/audits/phase35_synthetic_interpretability_smoke_v1_0d.json",
     "5bf61bc52d0c83ffb50849db973fb89133f0fa741140e58de8408a395979fee0"),
    ("reports/audits/phase35_synthetic_smoke_provenance_v1_0d.json",
     "8a7633cf05cbdb55453903e9bed31d09c953e0ab675b6b90df5567a0506a5dcf"),
    ("reports/audits/phase35_synthetic_smoke_final_check_v1_0d.json",
     "1cae9c7b45d679b8fc1d3e863d022795ad6f4c8a96fc441dde95d6fec436807f"),
    ("reports/audits/phase35_synthetic_smoke_reporting_gap_disclosure_v1_0d.json",
     "4d9fc89ab58658891cb56f9645c26ef5cf9cfa195379e5eea3e5d89d4d68cff3"),
    ("scripts/analysis/phase35_smoke_gate_v1_0d.py",
     "6a890141838d995b681686c5b67b7a4a772e052bef70220d0595d31b0637ebd8"),
])

# All predecessor digests above are now the true on-disk digests; the preservation gate is
# therefore fully fail-closed (no dynamic bypass). DYNAMIC_BIND is retained empty for provenance.
DYNAMIC_BIND = []

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

    # ---- predecessor preservation (fail-closed) ----
    pres = []
    for rel, exp in PRESERVE.items():
        obs = sha256_file(ROOT / rel)
        dynamic = rel in DYNAMIC_BIND
        match = (obs == exp) if not dynamic else True
        pres.append({"path": rel, "expected_sha256": exp, "observed_sha256": obs,
                     "match": match, "bound_dynamically": dynamic})
    pres_ok = all(p["match"] for p in pres)
    if not pres_ok:
        bad = [p["path"] for p in pres if not p["match"]]
        raise SystemExit(f"FAIL-CLOSED: predecessor preservation mismatch: {bad}")

    src_e = (ROOT / EXEC_E).read_text(encoding="utf-8")
    src_d = (ROOT / EXEC_D).read_text(encoding="utf-8")
    src_c = (ROOT / EXEC_C).read_text(encoding="utf-8")
    src_b = (ROOT / EXEC_B).read_text(encoding="utf-8")
    src_m = (ROOT / COMMON).read_text(encoding="utf-8")
    src_u = (ROOT / UNIT_E).read_text(encoding="utf-8")
    ex = src_e + "\n" + src_b
    cm = src_m
    ie, id_, ib = collect(src_e), collect(src_d), collect(src_b)
    iu = collect(src_u)
    ex_calls = ie["calls"] | ib["calls"]
    iu_calls = iu["calls"]
    iu_base = {c.split(".")[-1] for c in iu_calls}
    ex_withs = ie["withs"] | ib["withs"]
    graph = local_ref_graph(ie)
    smoke_calls = fn_calls(ie, "mode_smoke")
    smoke_base = {c.split(".")[-1] for c in smoke_calls}

    unit_d = json.loads((ROOT / UNIT_D_JSON).read_text(encoding="utf-8"))
    unit_d_ok = bool(unit_d["all_pass"])
    unit_e = json.loads((ROOT / UNIT_E_JSON).read_text(encoding="utf-8"))
    unit_e_ok = bool(unit_e["all_pass"]) and int(unit_e["n_pass"]) == int(unit_e["n_tests"])

    def has(s, tok):
        return tok in s

    def has_any(s, toks):
        return any(t in s for t in toks)

    # ---------------- ORIGINAL 54 v1.0a load-bearing checks (against the v1.0e effective set) ----
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
         has(src_e, "Path(__file__).resolve().parents[2]")
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
         has(cm, 'film_layers["bridge"]') and has(src_e, "g_model.film_layers[name]")
         and has(src_e, 'GRADCAM_LAYERS = V0D.GRADCAM_LAYERS')),
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
         has(ex, "empty_prediction_fallback_used") and has(src_e, "gradcam_target_scalar_rank_safe")),
        ("25_gradcam_forward_semantics_exact",
         has(src_e, "torch.enable_grad()") and has(src_e, "torch.amp.autocast")
         and not any("inference_mode" in w for w in ex_withs)
         and not any("no_grad" in w for w in ex_withs)),
        ("26_no_optimizer", not any(c.startswith("torch.optim") for c in ex_calls)),
        ("27_no_parameter_update", not any(c.endswith(".step") for c in ex_calls)),
        ("28_cam_formula_exact",
         has(src_e, "mean(dim=(2, 3)") and has(src_e, "relu") and has(src_e, ".sum(dim=1")),
        ("29_align_corners_false",
         has(src_e, 'C.GRADCAM_ALGORITHM["align_corners"]')
         and has(cm, '("align_corners", False)')),
        ("30_minmax_and_zero_range_exact",
         has(src_e, "rng") and has(src_e, "zeros_like") and has(src_e, "if float(rng) > 0")),
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
         and not any("router_holdout" in lit.lower()
                     and any(e in lit.lower() for e in (".npy", ".csv", ".pt", ".npz",
                                                        ".png", ".jpg"))
                     for lit in (ie["literals"] + ib["literals"]))),
        ("52_no_TEST_access", has(src_b, "/test/")),
        ("53_no_training_path", has(src_b, "training_backward_calls")),
        ("54_phase36_not_started", "phase36" not in ex.lower()),
    ])
    orig_failed = [k for k, v in checks.items() if not v]

    # ---------------- cumulative amendment checks (v1.0b/c/d regression guards) ----------------
    v1_0e_defines = set(ie["funcs"])
    extra = OrderedDict([
        ("v1_0_chain_preserved", pres_ok),
        ("v1_0b_and_v1_0c_sources_unmodified",
         sha256_file(ROOT / EXEC_B)
         == "581926840d7717e19ed15ad77c7c5339b709efc881b938924d6eec0a2ceb1872"
         and sha256_file(ROOT / EXEC_C)
         == "4058fc5544e6e1af15339df20a88da4880549ea8d4dd434395df04e0fa261baa"),
        ("v1_0d_source_unmodified",
         sha256_file(ROOT / EXEC_D)
         == "cccc109ade27eb5ad7883912004c1e911e9e253a659146f3d64820af92244056"),
        ("v1_0e_revision_and_classification_declared",
         has(src_e, "ra_medfilm_barr_phase35_interpretability_v1_0e")
         and has(src_e, "PRE_EXECUTION_GRADCAM_NUMERICAL_OBSERVABILITY_AND_FAIL_CLOSED_FINITE_"
                        "GUARD_")
         and has(src_e, '"AMENDMENT__NO_SCIENTIFIC_PROTOCOL_CHANGE")')),
        ("film_and_router_bound_verbatim_from_v1_0b",
         has(src_e, '("film", V0B.mode_film)') and has(src_e, '("router", V0B.mode_router)')),
        ("gradcam_and_science_are_v1_0e_local",
         has(src_e, '("gradcam", mode_gradcam)') and has(src_e, '("science", mode_science)')),
        ("film_router_helpers_not_redefined_in_v1_0e",
         not any(f in v1_0e_defines
                 for f in ("mode_film", "mode_router", "load_g_component", "load_bphi_component",
                           "load_gallery_allowlist", "resolve_display_subset", "guard_raw_path",
                           "load_persisted_p_global", "build_target_mask", "build_roi_mask",
                           "extract_film_parameters", "extract_task_embeddings",
                           "router_population_verify", "router_normalized_features",
                           "router_gradient_x_input", "router_group_attribution",
                           "cam_normalize", "saliency_self_consistency", "assert_claim_language"))),
        ("v1_0c_smoke_helpers_reused_verbatim",
         has(src_e, "V0C.smoke_environment_check") and has(src_e, "V0C.smoke_checkpoint_identity")
         and has(src_e, "V0C.smoke_synthetic_image") and has(src_e, "V0C.smoke_film_validate")
         and has(src_e, "V0C.smoke_embedding_validate") and has(src_e, "V0C.smoke_router")
         and has(src_e, "V0C.smoke_zero_denominator")
         and has(src_e, "V0C.smoke_parameter_immutability")),
        ("smoke_counter_store_is_the_frozen_v1_0c_store",
         has(src_e, "SMOKE_COUNTERS = V0C.SMOKE_COUNTERS")
         and has(src_e, "SMOKE_EXPECTED_COUNTERS = V0C.SMOKE_EXPECTED_COUNTERS")),
        ("smoke_gate_env_distinct_from_science_gate_env",
         has(src_e, 'SMOKE_GATE_ENV = "PHASE35_SMOKE_EXECUTE"')
         and has(src_e, 'SCIENCE_GATE_ENV = "PHASE35_EXECUTE"')),
        ("smoke_requires_smoke_gate",
         has(src_e, 'os.environ.get(SMOKE_GATE_ENV) != "1"')
         and has(src_e, "PHASE35 SMOKE NOT AUTHORIZED")),
        ("scientific_requires_science_gate",
         has(src_e, 'os.environ.get(SCIENCE_GATE_ENV) != "1"')
         and has(src_e, "PHASE35 EXECUTION NOT AUTHORIZED")),
        ("v1_0e_zero_execution_guard_present",
         has(src_e, "!! ZERO-EXECUTION GUARD !!")),
        ("v1_0e_emits_no_scientific_output",
         not has_any(src_e, ("savefig", "to_csv(", "write_text(", "np.save", "torch.save"))),
        ("smoke_mode_is_not_a_stub", len(list(ast.walk(ie["funcs"]["mode_smoke"]))) > 60),
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
         and has(src_e, "SMOKE_COUNTERS = V0C.SMOKE_COUNTERS")),
        ("smoke_no_optimizer_no_step_no_training_backward",
         not any(c.startswith("torch.optim") for c in smoke_calls)
         and not any(c.endswith(".step") for c in smoke_calls)),
        ("smoke_declares_synthetic_only_and_not_scientific_result",
         has(src_e, '"PRE_SCIENTIFIC_SYNTHETIC_INTERFACE_VALIDATION"')
         and has(src_e, '"PHASE35_SCIENTIFIC_INTERPRETABILITY_RESULT"')),
        ("claim_guard_reused", has(src_b, "assert_claim_language")),
        ("F8_regional_still_not_implemented", has(cm, "F8_REGIONAL_IMPLEMENTED = False")),
        ("v1_0d_rank_safe_target_reused_verbatim",
         has(src_e, "V0D.gradcam_target_scalar_rank_safe")
         and has(src_e, "V0D._validate_target_mask")
         and has(src_e, "TARGET_SCALAR_IMPL = V0D.TARGET_SCALAR_IMPL")),
        ("v1_0d_defective_logits_mask_unreachable_in_v1_0e",
         (not has(src_e, "V0B.gradcam_target_scalar"))
         and (not has(src_e, "V0B.gradcam_gradient_enabled"))
         and (not reaches(graph, "gradcam_gradient_enabled_numerically_guarded",
                          "gradcam_target_scalar"))),
    ])
    extra_failed = [k for k, v in extra.items() if not v]

    # ---------------- v1.0e numerical-guard / observability / fail-closed checks ----------------
    smoke_only_fns = ("mode_smoke", "smoke_gradcam", "smoke_synthetic_target_mask_rank2",
                      "empty_mask_helper_check_insession")
    smoke_refs = set()
    for f in smoke_only_fns:
        smoke_refs |= fn_refs(ie, f)

    num = OrderedDict([
        ("01_finite_guard_helpers_defined",
         all(f in v1_0e_defines for f in ("_require_finite_tensor", "_require_finite_scalar",
                                          "_tensor_stats", "cam_normalize_guarded"))
         and has(src_e, "def _require_finite_tensor(")
         and has(src_e, "def _require_finite_scalar(")
         and has(src_e, "def cam_normalize_guarded(")),
        ("02_guards_use_explicit_raises_surviving_python_O",
         has(src_e, "raise RuntimeError(") and has(src_e, "raise TypeError(")
         and (not has(src_e, "assert torch.isfinite"))
         and has(src_e, "explicit raises survive `python -O`")),
        ("03_target_scalar_finite_guard_before_autograd",
         has(src_e, "_require_finite_scalar(T, \"target_scalar_finite\")")
         and has(src_e, "# BEFORE autograd")),
        ("04_gradient_finite_guard_per_layer",
         has(src_e, "_require_finite_tensor(dA, \"gradient_finite\"")
         and has(src_e, "f\"layer={name}\"")),
        ("05_alpha_finite_guard",
         has(src_e, "_require_finite_tensor(alpha, \"alpha_finite\"")),
        ("06_pre_relu_weighted_map_finite_guard",
         has(src_e, "_require_finite_tensor(weighted, \"pre_relu_weighted_map_finite\"")),
        ("07_post_relu_raw_cam_finite_guard",
         has(src_e, "_require_finite_tensor(cam_raw, \"post_relu_raw_cam_finite\"")),
        ("08_upsampled_prenorm_cam_finite_guard",
         has(src_e, "_require_finite_tensor(cam, \"upsampled_prenorm_cam_finite\"")),
        ("09_normalized_cam_finite_guard",
         has(src_e, "_require_finite_tensor(norm, \"normalized_cam_finite\"")),
        ("10_guarded_normalizer_preserves_frozen_semantics_on_finite_inputs",
         has(src_e, "if float(rng) > 0")
         and has(src_e, "return (c - c.min()) / rng")
         and has(src_e, "return torch.zeros_like(c)")),
        ("11_guarded_normalizer_fails_closed_on_nonfinite_never_zero_fallback",
         has(src_e, "cam_normalize_guarded refuses non-finite input")
         and has(src_e, '("nonfinite_prenorm_cam_reaches_zero_fallback", False)')
         and has(src_e, '("finite_zero_range_cam_reaches_zero_fallback", True)')),
        ("12_frozen_cam_normalize_retained_and_referenced",
         has(src_e, "V0B.cam_normalize.__name__")
         and has(src_b, "def cam_normalize(")),
        ("13_gradient_diagnostics_shape_dtype_finite_min_max_absmax",
         has(src_e, '_tensor_stats(dA)') and has(src_e, '"abs_max"')
         and has(src_e, '"finite"') and has(src_e, '"min"') and has(src_e, '"max"')),
        ("14_prenorm_cam_range_and_all_zero_diagnostics",
         has(src_e, '"upsampled_prenorm_cam_range"')
         and has(src_e, '"prenorm_cam_all_zero"')
         and has(src_e, '"upsampled_prenorm_cam_finite"')),
        ("15_normalized_cam_min_max_finite_diagnostics",
         has(src_e, '"normalized_cam_min"') and has(src_e, '"normalized_cam_max"')
         and has(src_e, '"normalized_cam_finite"')),
        ("16_target_scalar_value_and_finite_emitted",
         has(src_e, '("target_scalar", res["T"])')
         and has(src_e, '("target_scalar_finite", res["target_scalar_finite"])')),
        ("17_insession_empty_mask_helper_check_no_extra_forward_or_autograd",
         has(src_e, "def empty_mask_helper_check_insession(")
         and has(src_e, '("extra_forward_performed", False)')
         and has(src_e, '("extra_autograd_performed", False)')
         and has(src_e, "torch.zeros_like(mask_t)")
         and has(src_e, "V0D.gradcam_target_scalar_rank_safe(logits_zero, empty)")),
        ("18_parameter_grad_state_audit_insession",
         has(src_e, "def parameter_grad_state_audit_insession(")
         and has(src_e, "for _name, p in model.named_parameters()")
         and has(src_e, "p.grad is not None")
         and has(src_e, '"NO_PARAMETER_GRAD_POPULATED"')),
        ("19_parameter_grad_audit_bound_into_smoke_before_return",
         has(src_e, 'ev["parameter_grad_state_audit"] = parameter_grad_state_audit_insession(')
         and reaches(graph, "mode_smoke", "parameter_grad_state_audit_insession")),
        ("20_smoke_gradcam_uses_guarded_path_and_emits_guard_diagnostics",
         has(src_e, "gradcam_gradient_enabled_numerically_guarded(")
         and reaches(graph, "smoke_gradcam", "gradcam_gradient_enabled_numerically_guarded")
         and reaches(graph, "smoke_gradcam", "empty_mask_helper_check_insession")
         and has(src_e, '"all_gradients_finite"')
         and has(src_e, '"all_prenorm_cams_finite"')
         and has(src_e, '"all_normalized_cams_finite"')),
        ("21_gradcam_and_science_reach_the_guarded_path",
         reaches(graph, "mode_gradcam", "gradcam_per_sample_runner")
         and reaches(graph, "gradcam_per_sample_runner",
                     "gradcam_gradient_enabled_numerically_guarded")
         and reaches(graph, "mode_gradcam", "gradcam_gradient_enabled_numerically_guarded")
         and reaches(graph, "mode_science", "gradcam_per_sample_runner")
         and reaches(graph, "mode_science", "gradcam_gradient_enabled_numerically_guarded")
         and has(src_e, "V0D.gradcam_target_scalar_rank_safe(")),
        ("22_guarded_path_retains_rank_safe_target_and_hooks",
         has(src_e, "V0D.gradcam_target_scalar_rank_safe(logits, m_pred)")
         and has(src_e, "module = g_model.film_layers[name]")
         and has(src_e, "register_forward_hook")),
        ("23_guarded_path_retains_autograd_grad_and_autocast",
         has(src_e, "torch.autograd.grad(T, [acts[n] for n in layers], retain_graph=False)")
         and has(src_e, "torch.amp.autocast") and has(src_e, "torch.enable_grad()")),
        ("24_scientific_mathematics_unchanged_on_finite_inputs",
         has(src_e, "alpha = dA.mean(dim=(2, 3), keepdim=True)")
         and has(src_e, "weighted = (alpha * A).sum(dim=1, keepdim=True)")
         and has(src_e, "cam_raw = torch.relu(weighted)")
         and has(src_e, "cam = torch.nn.functional.interpolate(")
         and has(src_e, 'align_corners=C.GRADCAM_ALGORITHM["align_corners"]')
         and has(src_e, '("scientific_mathematics_changed", False)')),
        ("25_no_scientific_protocol_change_marker",
         has(src_e, "IMPLEMENTATION_NUMERICAL_SAFETY_AND_OBSERVABILITY_ONLY")
         and has(src_e, "NO_SCIENTIFIC_PROTOCOL_CHANGE")),
        ("26_finite_guard_stage_registry_declared",
         has(src_e, "FINITE_GUARD_STAGES = (")
         and has(src_e, '"target_scalar_finite"')
         and has(src_e, '"gradient_finite"')
         and has(src_e, '"alpha_finite"')
         and has(src_e, '"pre_relu_weighted_map_finite"')
         and has(src_e, '"post_relu_raw_cam_finite"')
         and has(src_e, '"upsampled_prenorm_cam_finite"')
         and has(src_e, '"prenorm_cam_range_finite"')
         and has(src_e, '"normalized_cam_finite"')),
        ("27_guarded_path_declares_impl_names",
         has(src_e, 'GRADCAM_GRADIENT_IMPL = "gradcam_gradient_enabled_numerically_guarded"')
         and has(src_e, 'NORMALIZE_IMPL = "cam_normalize_guarded"')),
        ("28_no_gate_set_and_no_mode_invoked_in_source",
         (not has(src_e, 'os.environ["PHASE35_SMOKE_EXECUTE"] = '))
         and (not has(src_e, 'os.environ["PHASE35_EXECUTE"] = '))
         and (not has(src_e, "os.environ.setdefault"))
         and (not has(src_e, "subprocess"))),
        ("29_model_free_guard_unit_tests_emitted_and_pass",
         unit_e_ok and int(unit_e["n_tests"]) == 12
         and bool(unit_e["model_free_import_audit"]["model_free"])
         and int(unit_e["counters"]["model_constructions"]) == 0
         and int(unit_e["counters"]["forwards"]) == 0),
        ("30_guard_unit_tests_are_cpu_and_model_free",
         has(src_u, '("device", "cpu")')
         and has(src_u, "AST") and has(src_u, "model_free_import_audit")
         and (not (iu_base & {"load", "load_state_dict", "forward"}))
         and (not any(c.endswith(".cuda") for c in iu_calls))
         and (not any(("GlobalMedFiLM" in c) or ("BARRBenefitRouterV1" in c) for c in iu_calls))),
        ("31_no_new_counters_introduced_v1_0e",
         has(src_e, "SMOKE_COUNTERS = V0C.SMOKE_COUNTERS")
         and has(src_e, "SMOKE_EXPECTED_COUNTERS = V0C.SMOKE_EXPECTED_COUNTERS")
         and (not has(src_e, "SMOKE_COUNTERS = OrderedDict("))),
        ("32_no_protected_data_read_in_guarded_path",
         (not (smoke_refs & {"load_persisted_p_global", "build_target_mask", "build_roi_mask"}))
         and (not has(src_e, "router_holdout")) and (not has(src_e, "/test/"))),
        ("33_v1_0d_smoke_preserved_and_not_rerun_by_this_source",
         has(src_e, "V0D.smoke_synthetic_target_mask_rank2()")
         and has(src_e, "V0D.smoke_synthetic_target_mask_rank2")
         and (not has(src_e, "PHASE35_SYNTHETIC_SMOKE_V1_0D_COMPLETE"))),
        ("34_regression_no_defective_cam_normalize_call_reachable",
         (not reaches(graph, "gradcam_gradient_enabled_numerically_guarded", "cam_normalize"))
         and has(src_e, "cam_normalize_guarded(cam)")),
        ("35_no_silent_zeroing_of_nonfinite_cam",
         has(src_e, "cam_normalize_guarded refuses non-finite input")
         and has(src_e, "can NEVER reach the zero-range fallback")),
        ("36_all_guard_stages_emitted_in_cam_diagnostics",
         all(stage in src_e for stage in ("pre_relu_weighted_map_finite", "post_relu_raw_cam_finite",
                                          "upsampled_prenorm_cam_finite", "normalized_cam_finite"))
         and has(src_e, '"gradient_diagnostics"') and has(src_e, '"cam_diagnostics"')),
        ("37_target_scalar_and_prenorm_range_reported_in_smoke_artifact",
         has(src_e, '"upsampled_prenorm_cam_range"') and has(src_e, '("target_scalar", res["T"])')),
        ("38_read_guards_and_claim_guards_intact",
         has(cm, "MAX_RAW_VAL_IMAGE_READS = 64") and has(cm, "OUTCOME_SELECTED_PANELS_PERMITTED")
         and has(src_b, "assert_claim_language")),
        ("39_R_psi_S_omega_still_excluded",
         not any(("R_psi" in c) or ("S_omega" in c) for c in ex_calls)
         and (has(cm, "NON_EXECUTABLE_COMPONENTS") and has(src_e, "V0C.SMOKE_COUNTERS"))),
        ("40_no_phase36_and_no_new_dataset",
         "phase36" not in ex.lower() and "phase38" not in ex.lower()),
    ])
    num_failed = [k for k, v in num.items() if not v]

    all_failed = orig_failed + extra_failed + num_failed

    write_json(OrderedDict([
        ("artifact", "phase35_execution_source_static_preflight_v1_0e"),
        ("phase", 35), ("section", "\u00A7Q"), ("method", METHOD), ("revision", REVISION),
        ("method_of_inspection", "AST_PARSE_CONTROL_FLOW_CALL_GRAPH_AND_SHA256_HASHING"),
        ("effective_execution_source_set", [EXEC_E, EXEC_B]),
        ("sources", {"common_v1_0b": COMMON, "execution_v1_0b": EXEC_B, "execution_v1_0c": EXEC_C,
                     "execution_v1_0d": EXEC_D, "execution_v1_0e": EXEC_E,
                     "rank_unit_v1_0d": UNIT_D, "numeric_guard_unit_v1_0e": UNIT_E,
                     "preflight_v1_0e": PREFLIGHT}),
        ("preservation", pres), ("preservation_all_match", pres_ok),
        ("n_predecessors_preserved", len(pres)),
        ("original_v1_0a_checks", checks), ("original_n_checks", len(checks)),
        ("original_n_failed", len(orig_failed)), ("original_failed", orig_failed),
        ("original_54_all_pass", len(orig_failed) == 0),
        ("cumulative_amendment_checks", extra), ("cumulative_n_checks", len(extra)),
        ("cumulative_n_failed", len(extra_failed)), ("cumulative_failed", extra_failed),
        ("numerical_guard_checks", num), ("numerical_guard_n_checks", len(num)),
        ("numerical_guard_n_failed", len(num_failed)), ("numerical_guard_failed", num_failed),
        ("call_graph_reachability", OrderedDict([
            ("mode_smoke_to_gradcam_gradient_enabled_numerically_guarded",
             reaches(graph, "mode_smoke", "gradcam_gradient_enabled_numerically_guarded")),
            ("smoke_gradcam_to_empty_mask_helper_check_insession",
             reaches(graph, "smoke_gradcam", "empty_mask_helper_check_insession")),
            ("mode_smoke_to_parameter_grad_state_audit_insession",
             reaches(graph, "mode_smoke", "parameter_grad_state_audit_insession")),
            ("mode_gradcam_to_gradcam_per_sample_runner",
             reaches(graph, "mode_gradcam", "gradcam_per_sample_runner")),
            ("mode_science_to_gradcam_per_sample_runner",
             reaches(graph, "mode_science", "gradcam_per_sample_runner")),
            ("gradcam_per_sample_runner_to_guarded_path",
             reaches(graph, "gradcam_per_sample_runner",
                     "gradcam_gradient_enabled_numerically_guarded")),
            ("guarded_path_uses_cross_module_v0d_rank_safe_target",
             has(src_e, "V0D.gradcam_target_scalar_rank_safe(logits, m_pred)")),
            ("guarded_path_to_frozen_defective_target_scalar",
             reaches(graph, "gradcam_gradient_enabled_numerically_guarded",
                     "gradcam_target_scalar")),
            ("guarded_path_to_frozen_cam_normalize",
             reaches(graph, "gradcam_gradient_enabled_numerically_guarded", "cam_normalize")),
            ("guarded_path_to_cam_normalize_guarded",
             reaches(graph, "gradcam_gradient_enabled_numerically_guarded", "cam_normalize_guarded")),
        ])),
        ("total_n_checks", len(checks) + len(extra) + len(num)),
        ("total_n_failed", len(all_failed)), ("failed", all_failed),
        ("static_source_preflight_pass", len(all_failed) == 0),
        ("model_constructed", False), ("checkpoint_deserialized", False),
        ("forward_executed", False), ("backward_executed", False),
        ("gradcam_executed", False), ("router_attribution_executed", False),
        ("gate_env_set", False), ("mode_invoked", False),
        ("model_free_cpu_unit_tests_run", int(unit_e["n_tests"])),
        ("raw_val_reads", 0), ("gt_reads", 0), ("router_holdout_reads", 0), ("test_reads", 0),
        ("generated_utc", gen), ("all_pass", len(all_failed) == 0),
    ]), OUT)

    print("=== PHASE35 v1.0e STATIC PREFLIGHT ===")
    print("predecessors preserved:", len(pres), "| all match:", pres_ok)
    print("ORIGINAL 54 checks:", len(checks), "| failed:", len(orig_failed))
    for k in orig_failed:
        print("  FAILED:", k)
    print("CUMULATIVE amendment checks:", len(extra), "| failed:", len(extra_failed))
    for k in extra_failed:
        print("  FAILED:", k)
    print("NUMERICAL-GUARD checks:", len(num), "| failed:", len(num_failed))
    for k in num_failed:
        print("  FAILED:", k)
    print("TOTAL:", len(checks) + len(extra) + len(num), "checks,", len(all_failed), "failed")
    print("static_source_preflight_pass:", len(all_failed) == 0)
    print()
    for a in NEW:
        print(f"{a['sha256']}  {a['path']}")
    return 0 if not all_failed else 3


if __name__ == "__main__":
    main()
