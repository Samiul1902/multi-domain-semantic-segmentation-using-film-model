#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.5 — model-free unit checks.

METHOD: RA-MedFiLM-BARR
REVISION: ra_medfilm_barr_phase36_robustness_v1_5

NO torch. NO model. NO checkpoint. NO protected-data read. Pure static/unit logic.

Covers §L:
  * exact probability operator source contract
  * no manual NumPy sigmoid in executable code
  * single probability conversion authority
  * float32 probability before float16 persistence
  * CUDA fail-closed source contract
  * explicit four-component device binding
  * component-specific inference contexts
  * all inherited v1.4 contracts
  * NC25-NC30

Exit code 0 == all checks pass. Prints a JSON report.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

import scripts.analysis.phase36_robustness_execution_v1_5 as E  # noqa: E402
import scripts.analysis.phase36_robustness_common_v1_1 as C  # noqa: E402

EXEC_V1_5 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_5.py"
EXEC_V1_4 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_4.py"
UNIT_V1_4 = ROOT / "scripts/analysis/phase36_robustness_unit_v1_4.py"
PREFLIGHT_V1_4 = ROOT / "scripts/analysis/phase36_robustness_preflight_v1_4.py"
NC_V1_4 = ROOT / "scripts/analysis/phase36_robustness_negative_controls_v1_4.py"

checks = []


def check(name: str, cond: bool, detail=None):
    checks.append({"check": name, "passed": bool(cond), "detail": detail})


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


SRC = EXEC_V1_5.read_text(encoding="utf-8")
TREE = ast.parse(SRC)
FUNCS = {n.name: n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef)}


def _calls(fn_name):
    node = FUNCS.get(fn_name)
    if node is None:
        return set()
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            f = n.func
            out.add(f.id if isinstance(f, ast.Name)
                    else (f.attr if isinstance(f, ast.Attribute) else None))
    return out


def _reachable(fn_name, target, seen=None):
    seen = set() if seen is None else seen
    if fn_name in seen:
        return False
    seen.add(fn_name)
    cs = _calls(fn_name)
    if target in cs:
        return True
    return any(_reachable(c, target, seen) for c in cs if c in FUNCS)


def _funcs_referencing(token):
    return sorted(name for name, node in FUNCS.items()
                  if token in ast.get_source_segment(SRC, node))


def _exec_manual_sigmoid_sites():
    """AST-level executable manual-sigmoid sites (docstrings/comments excluded)."""
    out = []
    for n in ast.walk(TREE):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "exp" and isinstance(n.func.value, ast.Name)
                and n.func.value.id == "np"):
            out.append((n.lineno, "np.exp"))
        if (isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div)
                and "1.0 / (1.0" in ast.unparse(n)):
            out.append((n.lineno, "manual_logistic"))
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr in ("expit", "logistic")):
            out.append((n.lineno, n.func.attr))
    return sorted(set(out))


def _g_probability_impls():
    """Executable sites that convert canonical G logits -> probability."""
    out = []
    for n in ast.walk(TREE):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                and n.func.attr == "sigmoid":
            seg = ast.unparse(n)
            if seg.startswith("torch.sigmoid(t.float())"):
                out.append((n.lineno, seg))
    return out


# --------------------------------------------------------------------------- #
# 01-06  v1.4 history preserved (SHA gate)
# --------------------------------------------------------------------------- #
check("01_v1_4_execution_preserved",
      _sha(EXEC_V1_4) == "96ebc36256e5d812949e1f1859d4f41f332f81607e562dbff7cfb2bce6483fbe")
check("02_v1_4_unit_preserved",
      _sha(UNIT_V1_4) == "5cb3b351d95d49d2a9fe9b253972bb7631398cda5bc8da0883a4281181708725")
check("03_v1_4_preflight_preserved",
      _sha(PREFLIGHT_V1_4) == "3c558ad02cba4c55e76a8d18f3fcc8e9c71228ec508883618f89e1d3988d2b50")
check("04_v1_4_negative_controls_preserved",
      _sha(NC_V1_4) == "570f95fec571ed9180b4da90bbaebe2e1ae33143180b6fc361deca6236058688")
check("05_v1_4_direct_byte_audit_preserved",
      _sha(ROOT / "reports/audits/phase36_v1_4_direct_source_byte_audit.json")
      == "e6efd5fdb69e74fb32e33c15e6890047b8469b3182187e4c7630e00d8420ce45")
check("06_v1_4_defect_record_preserved",
      _sha(ROOT / "reports/audits/phase36_v1_3_post_byte_audit_semantic_defects_v1_4.json")
      == "de3d65f1282d71f43ab8e02891d2b2d49801b5473a43447fe4663a0328718fe0")

# --------------------------------------------------------------------------- #
# 07-11  §B defect record
# --------------------------------------------------------------------------- #
DEF = json.loads((ROOT / "reports/audits/"
                  "phase36_v1_4_probability_and_device_context_defects_v1_5.json")
                 .read_text(encoding="utf-8"))
check("07_defect_record_three_defects", DEF["defect_count"] == 3, DEF["defect_count"])
check("08_defect_ids_d11_d12_d13",
      [d["id"].split("_")[0] for d in DEF["defects"]] == ["D11", "D12", "D13"])
check("09_defect_subject_is_v1_4",
      DEF["subject_sha256"] == "96ebc36256e5d812949e1f1859d4f41f332f81607e562dbff7cfb2bce6483fbe")
check("10_d11_three_sites_proven",
      DEF["defects"][0]["evidence"]["distinct_site_count"] == 3,
      DEF["defects"][0]["evidence"]["distinct_site_count"])
check("11_batch_caveat_adjudicated_not_a_new_defect",
      DEF["batch_size_caveat_resolution"]["classification"]
      == "CHECKED_AND_ADJUDICATED__NOT_RECORDED_AS_A_NEW_DEFECT"
      and DEF["batch_size_caveat_resolution"]["new_batch_size_scientific_choice_introduced"]
      is False)

# --------------------------------------------------------------------------- #
# 12-19  §C/§D/§E canonical probability operator
# --------------------------------------------------------------------------- #
check("12_canonical_operator_expression",
      E.CANONICAL_PROBABILITY_OPERATOR["expression"]
      == "torch.sigmoid(logits.float()).cpu().numpy()")
check("13_canonical_operator_output_dtype",
      E.CANONICAL_PROBABILITY_OPERATOR["output_dtype"] == "float32")
check("14_central_site_count_required_one",
      E.CANONICAL_PROBABILITY_OPERATOR["central_site_count_required"] == 1)
check("15_central_operator_function_defined",
      "def canonical_probability_from_logits" in SRC)
check("16_no_executable_manual_numpy_sigmoid",
      len(_exec_manual_sigmoid_sites()) == 0, _exec_manual_sigmoid_sites())
impls = _g_probability_impls()
check("17_exactly_one_g_probability_implementation", len(impls) == 1, impls)
check("18_g_forward_returns_probability",
      "def canonical_g_forward_batched" in SRC
      and '"probability": probability' in SRC
      and '"probability_float32_numpy": probability' in SRC)
check("19_probability_float32_before_float16",
      ".astype(np.float32, copy=False)" in SRC
      and "p_f16[idx_of[sid]] = p_global.astype(np.float16)" in SRC)
# every consumer path reaches the central operator or the returned probability
for label, fn in (("clean_g_reference", "_generate_clean_g_reference"),
                  ("shared_core", "canonical_learned_core"),
                  ("image_driver", "run_image_perturbations"),
                  ("smoke", "run_smoke")):
    check(f"20_{label}_consumes_canonical_probability",
          "canonical_g_forward_batched" in _calls(fn)
          or "canonical_probability_from_logits" in _calls(fn)
          or "canonical_learned_core" in _calls(fn)
          or "proposal_core_adapter" in _calls(fn),
          sorted(c for c in _calls(fn) if c in FUNCS))

# --------------------------------------------------------------------------- #
# 21-26  §F Phase27 authority + reproduction contract preserved
# --------------------------------------------------------------------------- #
PA = E.PHASE27_GLOBAL_PROB_AUTHORITY
check("21_phase27_authority_path_unchanged",
      PA["path"] == "data_cache/phase27_barr_preservation_v1_0/phase27_val808_global_prob_f16.npy")
check("22_phase27_authority_sha_unchanged",
      PA["sha256"] == "cc6c54af986f56b4aba9265405ffeba4f6cac582eeff00fe6b0894429e7d3f13")
check("23_phase27_authority_shape_dtype",
      PA["shape"] == [808, 512, 512] and PA["dtype"] == "float16")
check("24_authority_file_present_and_sha_matches",
      (ROOT / PA["path"]).exists() and _sha(ROOT / PA["path"]) == PA["sha256"])
check("25_reproduction_gate_uses_array_equal",
      "np.array_equal" in SRC and "CLEAN_G_NOT_BIT_IDENTICAL_TO_PHASE27_AUTHORITY" in SRC)
check("26_gate_stops_before_downstream",
      "CLEAN_GLOBAL_REPRODUCTION_GATE_FAILED__STOP_BEFORE_DOWNSTREAM_PERTURBATION" in SRC
      and "stop_before_downstream_perturbation" in SRC)

# --------------------------------------------------------------------------- #
# 27-32  §G CUDA fail-closed device policy
# --------------------------------------------------------------------------- #
DC = E.CANONICAL_DEVICE_CONTRACT
check("27_device_contract_call_explicit",
      DC["call"] == "get_device(require_cuda=True)" and "get_device(require_cuda=True)" in SRC)
check("28_required_device_type_cuda", DC["required_device_type"] == "cuda")
check("29_cpu_fallback_forbidden", DC["cpu_scientific_fallback_permitted"] is False)
def _exec_cpu_device_calls():
    """AST-level executable ``torch.device('cpu')`` constructions (docstrings excluded)."""
    out = []
    for n in ast.walk(TREE):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                and n.func.attr == "device" and isinstance(n.func.value, ast.Name) \
                and n.func.value.id == "torch":
            for a in n.args:
                if isinstance(a, ast.Constant) and str(a.value).startswith("cpu"):
                    out.append((n.lineno, ast.unparse(n)))
    return out


check("30_no_executable_cpu_device_fallback",
      len(_exec_cpu_device_calls()) == 0, _exec_cpu_device_calls())
check("31_fail_closed_runtime_guard",
      "PHASE36_V1_5_CUDA_FAIL_CLOSED__DEVICE_TYPE" in SRC)
check("32_device_type_checked_after_resolution",
      'getattr(device, "type", str(device)) != CANONICAL_DEVICE_CONTRACT["required_device_type"]'
      in SRC)

# --------------------------------------------------------------------------- #
# 33-38  §H explicit four-component device binding
# --------------------------------------------------------------------------- #
check("33_explicit_G_to_device", "g.to(device)" in SRC)
check("34_explicit_B_phi_to_device", "b_phi.to(device)" in SRC)
check("35_explicit_R_psi_to_device", "r_psi.to(device)" in SRC)
check("36_explicit_S_omega_to_device", "s_omega.to(device)" in SRC)
check("37_component_device_binding_verified",
      "COMPONENT_DEVICE_BINDING_FAILED" in SRC
      and "_param_device" in SRC
      and "on_canonical_device" in SRC)
check("38_wrapg_non_module_hazard_documented",
      "NOT an ``nn.Module``" in SRC and "cannot move the underlying G" in SRC)

# --------------------------------------------------------------------------- #
# 39-47  §I component-specific inference contexts
# --------------------------------------------------------------------------- #
CTX = E.COMPONENT_INFERENCE_CONTEXTS
check("39_G_inference_mode_false_autocast_true",
      CTX["G"]["inference_mode"] is False and CTX["G"]["autocast_enabled"] is True)
check("40_G_grad_context_no_grad", CTX["G"]["grad_context"] == "torch.no_grad()")
check("41_G_autocast_dtype_fp16", CTX["G"]["autocast_dtype"] == "float16")
for comp in ("B_phi", "R_psi", "S_omega"):
    check(f"42_{comp}_inference_mode_true_autocast_false",
          CTX[comp]["inference_mode"] is True and CTX[comp]["autocast_enabled"] is False)
check("43_context_helper_defined", "def component_inference_context" in SRC)
check("44_autocast_disabled_helper_defined", "def component_autocast_disabled" in SRC)
check("45_B_phi_uses_component_context",
      'component_inference_context("B_phi")' in SRC
      and 'component_autocast_disabled("B_phi")' in SRC)
check("46_R_psi_uses_component_context",
      'component_inference_context("R_psi")' in SRC
      and 'component_autocast_disabled("R_psi")' in SRC)
check("47_S_omega_uses_component_context",
      'component_inference_context("S_omega")' in SRC
      and 'component_autocast_disabled("S_omega")' in SRC)
check("48_contexts_not_interchangeable",
      E.COMPONENT_CONTEXTS_NOT_INTERCHANGEABLE is True
      and "COMPONENT_CONTEXTS_NOT_INTERCHANGEABLE = True" in SRC
      and CTX["G"]["autocast_enabled"] != CTX["R_psi"]["autocast_enabled"]
      and CTX["G"]["inference_mode"] != CTX["R_psi"]["inference_mode"])
check("49_nonG_not_under_G_autocast",
      'canonical_autocast(ctx["device"]), TapRecorder' in SRC
      and 'component_autocast_disabled("B_phi")' in SRC)

# --------------------------------------------------------------------------- #
# 50-62  §J v1.4 repairs preserved
# --------------------------------------------------------------------------- #
dec = None
node = FUNCS["canonical_learned_core"]
for n in ast.walk(node):
    if (isinstance(n, ast.Compare) and isinstance(n.comparators[0], ast.Name)
            and n.comparators[0].id == "TAU_C8_FINAL_FLOAT"):
        dec = n.lineno
rpsi_line = min([n.lineno for n in ast.walk(node)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Subscript)
                 and "r_psi" in ast.unparse(n.func)] or [10 ** 9])
somega_line = min([n.lineno for n in ast.walk(node)
                   if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                   and n.func.attr == "post_safety"] or [10 ** 9])
check("50_decision_before_R_psi", dec is not None and dec < rpsi_line,
      {"decision": dec, "r_psi": rpsi_line})
check("51_decision_before_S_omega", dec is not None and dec < somega_line,
      {"decision": dec, "s_omega": somega_line})
check("52_skip_branch_zero_forwards", "refiner=0, somega=0" in SRC)
check("53_router_decision_separate",
      'ROUTER_DECISIONS = ("SKIP", "EXECUTE")' in SRC
      and "ROUTER_DECISION_NOT_CANONICAL" in SRC
      and 'router_decision"] = out.get("state")' not in SRC)
check("54_exact_branch_comparator",
      "n_state_machine_branch_comparisons_808" in SRC
      and "accept_reject_collapse_prohibited" in SRC
      and "gen_global != bound_global" not in SRC)
check("55_real_proposal_smoke",
      _reachable("run_smoke", "proposal_core_adapter")
      and "smoke_nonempty_proposal_pipeline" in SRC)
check("56_real_empty_proposal_smoke",
      "smoke_empty_proposal_pipeline" in SRC
      and "proposal_geometry=None" in SRC
      and "NOT_APPLICABLE_EMPTY_PROPOSAL" in SRC)
check("57_three_branch_controls",
      all(s in SRC for s in ("CONTROL_SKIP_GLOBAL", "CONTROL_EXECUTE_THEN_ACCEPT",
                             "CONTROL_EXECUTE_THEN_REJECT")))
check("58_sample_level_image_loop",
      "run_image_perturbations" in SRC and "NONCLEAN_IMAGE_EXECUTIONS_EXPECTED" in SRC)
check("59_sample_level_proposal_loop",
      "run_proposal_perturbations" in SRC and "NONCLEAN_PROPOSAL_EXECUTIONS_MAX" in SRC)
check("60_case_b_and_deny_authorities",
      "EXACT_VAL808_MANIFEST_MEMBERSHIP_PLUS_EXACT_ROW_PATHS" in SRC
      and "ROUTER_HOLDOUT_IDENTITY_AUTHORITY" in SRC
      and "ROUTER_HOLDOUT_IDENTITY_EXPECTED_N = 875" in SRC)
check("61_feature_dependency_contract_98_104",
      C.PROPOSAL_CONTRACT_V1_1["geometry_dependent_dims"] == 98
      and C.PROPOSAL_CONTRACT_V1_1["global_only_dims"] == 104)
check("62_kub_subgroup_and_figures",
      "def kub_subgroup_map" in SRC and '"kub_subgroup"' in SRC
      and all(f"def figure_R{i}" in SRC for i in range(1, 6))
      and "generate_all_figures" in _calls("run_science"))

# --------------------------------------------------------------------------- #
# 63-66  frozen scientific constants unchanged
# --------------------------------------------------------------------------- #
check("63_noise_seed_rule_v1_1", C.NOISE_SEED_RULE_V1_1.endswith("[:8]"))
check("64_thresholds_unchanged",
      E.SEGMENTATION_OUTPUT_THRESHOLD == 0.50
      and E.ROI_PROPOSAL_THRESHOLD == 0.30
      and E.SOMEGA_ACCEPT_THRESHOLD == 0.50)
check("65_component_identities_unchanged",
      E.G_COMPONENT["sha256"] == "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7"
      and E.B_PHI_COMPONENT["sha256"] == "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b"
      and E.R_PSI_COMPONENT["sha256"] == "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109"
      and E.S_OMEGA_COMPONENT["sha256"] == "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e")
check("66_frozen_counts_unchanged",
      E.NONCLEAN_IMAGE_EXECUTIONS_EXPECTED == 12928
      and E.LOGICAL_IMAGE_TABLE_ROWS_MAX == 13736
      and E.NONCLEAN_PROPOSAL_EXECUTIONS_MAX == 4848
      and E.CLEAN_EXECUTIONS_EXPECTED == 808)
check("67_canonical_batch_partition_unchanged",
      E.canonical_batch_plan_audit()["matches_phase27_exact_partition"] is True)
check("68_import_safety_no_torch", "torch" not in sys.modules)
check("69_no_training_paths",
      ".backward()" not in SRC and "torch.optim" not in SRC
      and "requires_grad_(True)" not in SRC and ".train()" not in SRC)

passed = sum(1 for c in checks if c["passed"])
total = len(checks)
report = {
    "artifact": "phase36_robustness_unit_v1_5",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_5",
    "model_free": True,
    "torch_imported": False,
    "checks": checks,
    "passed": passed,
    "total": total,
    "all_pass": passed == total,
}
out = ROOT / "reports/audits/phase36_robustness_unit_v1_5.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"passed": passed, "total": total, "all_pass": passed == total}, indent=1))
for c in checks:
    if not c["passed"]:
        print("FAIL:", c["check"], json.dumps(c.get("detail"), default=str))
raise SystemExit(0 if passed == total else 1)
