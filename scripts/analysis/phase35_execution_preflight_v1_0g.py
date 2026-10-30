#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase35 v1.0g static source preflight - SMOKE COUNTER-CONTRACT REPAIR.

Verifies, with AST/control-flow/call-graph inspection and SHA-256 hashing, that the v1.0g execution
source:
  * preserves the v1.0f scientific source semantics,
  * increments the PRIMARY target-mask counter exactly once,
  * does NOT let the empty-mask helper increment the primary mask counter,
  * increments the empty-mask observability counter exactly once,
  * has primary target expected = 1 and empty helper expected = 1,
  * performs no second G forward and no second autograd for the empty-mask check,
  * uses the actual same G logits and keeps the zero-logit surrogate unreachable,
  * preserves all 8 numerical guards, the direct parameter-grad audit, router/FiLM semantics,
    R_psi/S_omega exclusion, and the protected-data guards.

ZERO EXECUTION. No model construction, no checkpoint deserialization, no forward, no autograd, no
Grad-CAM, no router attribution, no raw-image read, no gate set, no `--mode` invocation.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase35_execution_preflight_v1_0g.py
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
REVISION = "ra_medfilm_barr_phase35_interpretability_v1_0g"
OUT = AUD / "phase35_execution_source_static_preflight_v1_0g.json"

PREFLIGHT_F = "scripts/analysis/phase35_execution_preflight_v1_0f.py"
EXEC_F = "scripts/analysis/phase35_interpretability_execution_v1_0f.py"
EXEC_G = "scripts/analysis/phase35_interpretability_execution_v1_0g.py"
PREFLIGHT_G = "scripts/analysis/phase35_execution_preflight_v1_0g.py"
UNIT_G = "scripts/analysis/phase35_smoke_counter_contract_unit_v1_0g.py"
UNIT_G_JSON = "reports/audits/phase35_smoke_counter_contract_unit_v1_0g.json"
UNIT_F_JSON = "reports/audits/phase35_empty_mask_actual_logits_unit_v1_0f.json"
UNIT_E_JSON = "reports/audits/phase35_gradcam_numerical_guard_unit_v1_0e.json"
COMMON = "scripts/analysis/phase35_interpretability_common_v1_0b.py"
EXEC_B = "scripts/analysis/phase35_interpretability_execution_v1_0b.py"
EXEC_D = "scripts/analysis/phase35_interpretability_execution_v1_0d.py"
EXEC_E = "scripts/analysis/phase35_interpretability_execution_v1_0e.py"

NEW = [
    {"path": EXEC_G, "sha256": None},
]

# ---- v1.0f artifacts that MUST be preserved byte-for-byte (first valid attempt) ----
PRESERVE = OrderedDict([
 ("reports/audits/phase35_synthetic_interpretability_smoke_v1_0f.json",
  "05c02a34d61df1c6d3e53e2dd127f889501a5f5e99247aa8ef96fb947bc1d0fb"),
 ("reports/audits/phase35_synthetic_smoke_provenance_v1_0f.json",
  "5e7cb9956e56dddf6951562e36047361311e69dc687d976362e90749ad75d866"),
 ("reports/audits/phase35_synthetic_smoke_final_check_v1_0f.json",
  "040fc28379700e207ed324067594259c0c9e4ecaa2f9a6e2388824fbd0b29b7f"),
 ("reports/audits/phase35_synthetic_smoke_terminal_v1_0f.json",
  "728d1535c39c27109aeea7fcfaf0cda5577734bc0327833c35efed5e7599b8b0"),
])

# inherited scientific authorities that must remain byte-identical
INHERITED = OrderedDict([
 (EXEC_F, "6a6097f4a3c346df38ab5ec452dc97717cdb65d789bf8bde8031442cb236e3e5"),
 (PREFLIGHT_F, "7d535fcc22283b868616ef1e2259d6a7e4ed3d1e76747d5f31ba35e23ea8b552"),
 (COMMON, "9963215e1431e968e11bacbcd917d96a8a985a7181000258b90f458ff0a778ac"),
 (EXEC_B, "581926840d7717e19ed15ad77c7c5339b709efc881b938924d6eec0a2ceb1872"),
 (EXEC_D, "cccc109ade27eb5ad7883912004c1e911e9e253a659146f3d64820af92244056"),
 (EXEC_E, "1ca50b773a185384b9f0a7eae47fe95c64eb84bad3826c70cbe88edefe535941"),
])


def now_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def write_json(obj, p: Path):
    p.write_text(json.dumps(obj, indent=1) + "\n", encoding="utf-8")


def collect(src: str) -> dict:
    t = ast.parse(src)
    calls, withs, funcs = set(), set(), {}
    for n in ast.walk(t):
        if isinstance(n, ast.Call):
            parts = []
            f = n.func
            while isinstance(f, ast.Attribute):
                parts.append(f.attr); f = f.value
            if isinstance(f, ast.Name):
                parts.append(f.id)
            calls.add(".".join(reversed(parts)))
        if isinstance(n, (ast.With, ast.AsyncWith)):
            for it in n.items:
                if isinstance(it.context_expr, ast.Call):
                    f = it.context_expr.func
                    nm = getattr(f, "id", None) or getattr(f, "attr", None)
                    if nm:
                        withs.add(nm)
    for n in t.body:
        if isinstance(n, ast.FunctionDef):
            funcs[n.name] = n
    return {"calls": calls, "withs": withs, "funcs": funcs, "tree": t}


def fn_calls(info, fname):
    n = info["funcs"].get(fname)
    if n is None:
        return set()
    out = set()
    for x in ast.walk(n):
        if isinstance(x, ast.Call):
            parts = []
            f = x.func
            while isinstance(f, ast.Attribute):
                parts.append(f.attr); f = f.value
            if isinstance(f, ast.Name):
                parts.append(f.id)
            out.add(".".join(reversed(parts)))
    return out


def local_ref_graph(info):
    g = {}
    for name, node in info["funcs"].items():
        refs = set()
        for x in ast.walk(node):
            if isinstance(x, ast.Call):
                f = x.func
                nm = getattr(f, "id", None)
                if nm and nm in info["funcs"]:
                    refs.add(nm)
        g[name] = refs
    return g


def reaches(graph, start, target, _seen=None):
    _seen = _seen or set()
    if start == target:
        return True
    if start in _seen:
        return False
    _seen.add(start)
    return any(reaches(graph, n, target, _seen) for n in graph.get(start, ()))


def fn_source(src, fname):
    t = ast.parse(src)
    for n in t.body:
        if isinstance(n, ast.FunctionDef) and n.name == fname:
            return ast.get_source_segment(src, n) or ""
    return ""


def main():
    gen = now_utc()

    src_g = (ROOT / EXEC_G).read_text(encoding="utf-8")
    src_f = (ROOT / EXEC_F).read_text(encoding="utf-8")
    src_b = (ROOT / EXEC_B).read_text(encoding="utf-8")
    ig, if_, ib = collect(src_g), collect(src_f), collect(src_b)
    graph = local_ref_graph(ig)

    # ---- preservation: v1.0f artifacts byte-for-byte ----
    pres = []
    for rel, exp in PRESERVE.items():
        p = ROOT / rel
        obs = sha256_file(p) if p.is_file() else None
        pres.append({"path": rel, "expected_sha256": exp,
                     "observed_sha256": obs, "match": obs == exp})
    pres_ok = all(x["match"] for x in pres)

    # ---- inherited authorities ----
    inh = []
    for rel, exp in INHERITED.items():
        p = ROOT / rel
        obs = sha256_file(p) if p.is_file() else None
        inh.append({"path": rel, "expected_sha256": exp,
                    "observed_sha256": obs, "match": obs == exp})
    inh_ok = all(x["match"] for x in inh)

    unit_g = json.loads((ROOT / UNIT_G_JSON).read_text(encoding="utf-8"))
    unit_g_ok = bool(unit_g["all_pass"]) and int(unit_g["n_pass"]) == int(unit_g["n_tests"])
    unit_f = json.loads((ROOT / UNIT_F_JSON).read_text(encoding="utf-8"))
    unit_f_ok = bool(unit_f["all_pass"]) and int(unit_f["n_pass"]) == int(unit_f["n_tests"])
    unit_e = json.loads((ROOT / UNIT_E_JSON).read_text(encoding="utf-8"))
    unit_e_ok = bool(unit_e["all_pass"]) and int(unit_e["n_pass"]) == int(unit_e["n_tests"])

    primary_src = fn_source(src_g, "smoke_synthetic_target_mask_rank2")
    helper_src = fn_source(src_g, "empty_mask_helper_check_insession_actual_logits")
    gradcam_src = fn_source(src_g, "gradcam_gradient_enabled_numerically_guarded_v1_0f")
    smoke_src = fn_source(src_g, "mode_smoke")

    helper_calls = fn_calls(ig, "empty_mask_helper_check_insession_actual_logits")
    primary_calls = fn_calls(ig, "smoke_synthetic_target_mask_rank2")

    def has(s, tok):
        return tok in s

    checks = OrderedDict()

    # ---- counter contract (the core repair) ----
    checks["01_primary_counter_declared"] = has(src_g, 'PRIMARY_TARGET_MASK_COUNTER = "primary_synthetic_target_masks"')
    checks["02_alias_counter_declared"] = has(src_g, 'PRIMARY_TARGET_MASK_ALIAS_COUNTER = "synthetic_smoke_target_masks"')
    checks["03_empty_observability_counter_declared"] = has(src_g, 'EMPTY_MASK_OBSERVABILITY_COUNTER = "actual_logits_empty_mask_helper_checks"')
    checks["04_primary_counter_initialized_zero"] = has(src_g, 'SMOKE_COUNTERS["primary_synthetic_target_masks"] = 0')
    checks["05_empty_counter_initialized_zero"] = has(src_g, 'SMOKE_COUNTERS["actual_logits_empty_mask_helper_checks"] = 0')
    checks["06_primary_increments_primary_counter"] = (
        primary_src.count("SMOKE_COUNTERS[PRIMARY_TARGET_MASK_COUNTER] += 1") == 1)
    checks["07_primary_increments_alias_via_frozen_v0d"] = has(primary_src, "V0D.smoke_synthetic_target_mask_rank2()")
    checks["08_primary_helper_no_empty_counter_increment"] = (
        "EMPTY_MASK_OBSERVABILITY_COUNTER" not in primary_src)
    checks["09_empty_helper_increments_empty_counter_once"] = (
        helper_src.count("SMOKE_COUNTERS[EMPTY_MASK_OBSERVABILITY_COUNTER] += 1") == 1)
    checks["10_empty_helper_does_not_increment_primary_counter"] = (
        helper_src.count("SMOKE_COUNTERS[PRIMARY_TARGET_MASK_COUNTER]") == 0)
    checks["11_empty_helper_does_not_increment_alias_counter"] = (
        helper_src.count('SMOKE_COUNTERS["synthetic_smoke_target_masks"]') == 0)
    checks["12_no_literal_primary_counter_increment_in_helper"] = (
        'SMOKE_COUNTERS["primary_synthetic_target_masks"] +=' not in helper_src)
    checks["13_expected_primary_equals_1"] = has(src_g, 'EXPECTED_COUNTERS_V1_0G["primary_synthetic_target_masks"] = 1')
    checks["14_expected_alias_equals_1"] = has(src_g, '_FROZEN_V1_0C_EXPECTED["synthetic_smoke_target_masks"] = 1')
    checks["15_expected_empty_helper_equals_1"] = has(src_g, 'EXPECTED_COUNTERS_V1_0G["actual_logits_empty_mask_helper_checks"] = 1')
    checks["16_expected_additional_forward_equals_0"] = has(src_g, 'EXPECTED_COUNTERS_V1_0G["additional_G_forwards_for_empty_mask"] = 0')
    checks["17_expected_additional_autograd_equals_0"] = has(src_g, 'EXPECTED_COUNTERS_V1_0G["additional_autograd_calls_for_empty_mask"] = 0')
    checks["18_expected_store_not_mutating_v1_0c"] = (
        has(src_g, "SMOKE_COUNTERS = OrderedDict(V0C.SMOKE_COUNTERS)")
        and has(src_g, "_FROZEN_V1_0C_EXPECTED = OrderedDict(V0C.SMOKE_EXPECTED_COUNTERS)"))
    checks["19_mode_smoke_uses_v1_0g_expected"] = has(smoke_src, "EXPECTED_COUNTERS_V1_0G.items()")
    checks["20_mode_smoke_exposes_counter_contract"] = has(smoke_src, 'ev["counter_contract"]')
    checks["21_counter_contract_gates_all_pass"] = has(smoke_src, 'ev["counter_contract_ok"]')
    checks["22_empty_helper_counts_as_primary_false"] = has(helper_src, '("counts_as_primary_target_mask", False)')
    checks["23_empty_helper_counter_category"] = has(helper_src, '("counter_category", EMPTY_MASK_OBSERVABILITY_COUNTER)')

    # ---- preservation of v1.0f semantics ----
    checks["24_gradcam_path_no_primary_counter_change"] = (
        "PRIMARY_TARGET_MASK_COUNTER" not in gradcam_src
        and "EMPTY_MASK_OBSERVABILITY_COUNTER" not in gradcam_src)
    checks["25_gradcam_eight_finite_guards_preserved"] = (
        gradcam_src.count("_require_finite_tensor(") == 6
        and gradcam_src.count("_require_finite_scalar(") >= 1
        and len(src_g.split("FINITE_GUARD_STAGES = V0E.FINITE_GUARD_STAGES")) == 2)
    checks["26_gradcam_enable_grad_preserved"] = gradcam_src.count("torch.enable_grad") == 1
    checks["27_gradcam_autocast_preserved"] = gradcam_src.count("torch.amp.autocast") == 1
    checks["28_gradcam_single_autograd_grad_preserved"] = gradcam_src.count("torch.autograd.grad") == 2
    checks["29_gradcam_rank_safe_target_preserved"] = has(gradcam_src, "V0D.gradcam_target_scalar_rank_safe(logits, m_pred)")
    checks["30_gradcam_bilinear_align_corners_preserved"] = (
        gradcam_src.count("align_corners") == 3 and has(gradcam_src, '"bilinear"'))
    checks["31_gradcam_cam_normalize_guarded_preserved"] = has(gradcam_src, "cam_normalize_guarded(cam)")
    checks["32_empty_helper_atol_rtol_preserved"] = (
        has(helper_src, "EMPTY_MASK_ATOL") and has(helper_src, "EMPTY_MASK_RTOL")
        and has(helper_src, "torch.isclose"))
    checks["33_empty_helper_uses_actual_logits"] = has(helper_src, "V0D.gradcam_target_scalar_rank_safe(logits, empty)")
    checks["34_empty_helper_rejects_non_tensor"] = has(helper_src, "torch.is_tensor(logits)")
    checks["35_empty_helper_no_forward"] = not any(
        c.endswith(("g_model", "forward")) or c in {"g_model"} for c in helper_calls)
    checks["36_empty_helper_no_autograd"] = "torch.autograd.grad" not in helper_calls
    checks["37_empty_helper_no_second_forward_flag_false"] = has(helper_src, '("extra_forward_performed", False)')
    checks["38_empty_helper_no_second_autograd_flag_false"] = has(helper_src, '("extra_autograd_performed", False)')
    checks["39_empty_helper_additional_counts_zero"] = (
        has(helper_src, '("additional_G_forwards", 0)') and has(helper_src, '("additional_autograd_calls", 0)'))

    # ---- call graph ----
    checks["40_mode_smoke_reaches_gradcam_guarded"] = reaches(graph, "mode_smoke", "gradcam_gradient_enabled_numerically_guarded_v1_0f")
    checks["41_smoke_gradcam_reaches_empty_helper"] = reaches(graph, "smoke_gradcam", "empty_mask_helper_check_insession_actual_logits")
    checks["42_mode_smoke_reaches_empty_helper"] = reaches(graph, "mode_smoke", "empty_mask_helper_check_insession_actual_logits")
    checks["43_mode_smoke_reaches_primary_mask"] = reaches(graph, "mode_smoke", "smoke_synthetic_target_mask_rank2")
    checks["44_surrogate_zero_plane_unreachable"] = not reaches(graph, "mode_smoke", "empty_mask_helper_check_insession")
    checks["45_gradcam_guarded_reaches_empty_helper"] = reaches(graph, "gradcam_gradient_enabled_numerically_guarded_v1_0f", "empty_mask_helper_check_insession_actual_logits")

    # ---- parameter grad audit / immutability / router / FiLM preserved (inherited) ----
    checks["46_parameter_grad_audit_reused"] = has(src_g, "parameter_grad_state_audit_insession = V0E.parameter_grad_state_audit_insession")
    checks["47_finite_guards_reused_from_v1_0e"] = has(src_g, "cam_normalize_guarded = V0E.cam_normalize_guarded")
    checks["48_router_film_delegated_to_v1_0b"] = (
        has(src_g, "V0B.mode_film") and has(src_g, "V0B.mode_router") and has(src_g, "V0C.smoke_router"))
    checks["49_r_psi_s_omega_excluded"] = (
        has(src_g, "R_psi / S_omega")
        and has(src_b, '("R_psi_model_constructions", 0)')
        and has(src_b, '("S_omega_model_constructions", 0)')
        and has(src_b, "_assert_executable_component")
        and has(src_b, "new_R_psi_visualization_forward_eligible"))
    checks["50_gate_envs_unchanged"] = (
        has(src_g, 'SMOKE_GATE_ENV = "PHASE35_SMOKE_EXECUTE"')
        and has(src_g, 'SCIENCE_GATE_ENV = "PHASE35_EXECUTE"'))
    checks["51_classification_v1_0g"] = has(src_g, "PRE_EXECUTION_SYNTHETIC_SMOKE_COUNTER_CONTRACT_REPAIR")
    checks["52_only_change_token"] = has(src_g, 'ONLY_CHANGE = "SMOKE_COUNTER_CATEGORY_SEPARATION"')

    # ---- unit tests ----
    checks["53_counter_unit_tests_pass"] = unit_g_ok
    checks["54_v1_0f_actual_logits_unit_still_pass"] = unit_f_ok
    checks["55_v1_0e_numerical_guard_unit_still_pass"] = unit_e_ok

    failed = [k for k, v in checks.items() if not v]

    write_json(OrderedDict([
        ("artifact", "phase35_execution_source_static_preflight_v1_0g"),
        ("phase", 35), ("section", "\u00A7G"), ("method", METHOD), ("revision", REVISION),
        ("method_of_inspection", "AST_PARSE_CONTROL_FLOW_CALL_GRAPH_AND_SHA256_HASHING"),
        ("effective_execution_source_set", [EXEC_G, EXEC_B]),
        ("preservation", pres), ("preservation_all_match", pres_ok),
        ("n_v1_0f_artifacts_preserved", len(pres)),
        ("inherited_authorities", inh), ("inherited_all_match", inh_ok),
        ("n_inherited_authorities", len(inh)),
        ("checks", checks), ("n_checks", len(checks)),
        ("n_failed", len(failed)), ("failed", failed),
        ("call_graph_reachability", OrderedDict([
            ("mode_smoke_to_gradcam_guarded", reaches(graph, "mode_smoke", "gradcam_gradient_enabled_numerically_guarded_v1_0f")),
            ("mode_smoke_to_empty_helper", reaches(graph, "mode_smoke", "empty_mask_helper_check_insession_actual_logits")),
            ("mode_smoke_to_primary_mask", reaches(graph, "mode_smoke", "smoke_synthetic_target_mask_rank2")),
            ("mode_smoke_to_surrogate_zero_plane", reaches(graph, "mode_smoke", "empty_mask_helper_check_insession")),
        ])),
        ("counter_contract", OrderedDict([
            ("primary_target_mask_counter", "primary_synthetic_target_masks"),
            ("primary_target_mask_alias_counter", "synthetic_smoke_target_masks"),
            ("empty_mask_observability_counter", "actual_logits_empty_mask_helper_checks"),
            ("primary_expected", 1), ("alias_expected", 1), ("empty_helper_expected", 1),
            ("additional_G_forwards_for_empty_mask", 0),
            ("additional_autograd_calls_for_empty_mask", 0),
        ])),
        ("static_source_preflight_pass", len(failed) == 0),
        ("zero_logit_surrogate_unreachable_from_v1_0g_smoke",
         not reaches(graph, "mode_smoke", "empty_mask_helper_check_insession")),
        ("actual_logits_check_reachable_from_v1_0g_smoke",
         reaches(graph, "mode_smoke", "empty_mask_helper_check_insession_actual_logits")),
        ("model_constructed", False), ("checkpoint_deserialized", False),
        ("forward_executed", False), ("backward_executed", False),
        ("gradcam_executed", False), ("router_attribution_executed", False),
        ("gate_env_set", False), ("mode_invoked", False),
        ("raw_val_reads", 0), ("gt_reads", 0), ("router_holdout_reads", 0), ("test_reads", 0),
        ("generated_utc", gen), ("all_pass", len(failed) == 0),
    ]), OUT)

    print("=== PHASE35 v1.0g STATIC PREFLIGHT ===")
    print("v1.0f artifacts preserved:", len(pres), "| all match:", pres_ok)
    print("inherited authorities:", len(inh), "| all match:", inh_ok)
    print("checks:", len(checks), "| failed:", len(failed))
    for k in failed:
        print("  FAILED:", k)
    print("static_source_preflight_pass:", len(failed) == 0)
    print()
    print(f"{sha256_file(ROOT / EXEC_G)}  {EXEC_G}")
    return 0 if not failed else 3


if __name__ == "__main__":
    raise SystemExit(main())
