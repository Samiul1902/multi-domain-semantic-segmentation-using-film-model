#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.7 — model-free unit checks.

METHOD: RA-MedFiLM-BARR
REVISION: ra_medfilm_barr_phase36_robustness_v1_7

NO model execution. NO protected-population read. Pure static/unit logic.

Covers §L:
  * actual forward-count semantics
  * forced-safety path S_omega actual count = 0
  * real execute probe source exists and does NOT force the S_omega logit
  * router 202-D finite diagnostic binds rf202
  * router vector exact dim check = 202
  * top-level smoke_checks exists / smoke_all_pass derives from checks
  * artifact written before a nonzero fail exit; no automatic retry
  * NC36-NC40 (delegated to the v1.7 negative-control module)
  * v1.6 protected-population constraints preserved
  * canonical probability / device / context constraints preserved

Exit code 0 == all checks pass. Prints a JSON report.
"""
from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

import scripts.analysis.phase36_robustness_execution_v1_7 as E  # noqa: E402
import scripts.analysis.phase36_robustness_common_v1_1 as C  # noqa: E402

EXEC_V1_7 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_7.py"
EXEC_V1_6 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_6.py"
UNIT_V1_6 = ROOT / "scripts/analysis/phase36_robustness_unit_v1_6.py"
PREFLIGHT_V1_6 = ROOT / "scripts/analysis/phase36_robustness_preflight_v1_6.py"
NC_V1_6 = ROOT / "scripts/analysis/phase36_robustness_negative_controls_v1_6.py"

checks = []


def check(name: str, cond: bool, detail=None):
    checks.append({"check": name, "passed": bool(cond), "detail": detail})


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


SRC = EXEC_V1_7.read_text(encoding="utf-8")
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


def _reachable(entry):
    seen, stack = set(), [entry]
    while stack:
        f = stack.pop()
        if f in seen or f not in FUNCS:
            continue
        seen.add(f)
        for c in _calls(f):
            if c in FUNCS and c not in seen:
                stack.append(c)
    return seen


def _src_of(fn_name):
    node = FUNCS.get(fn_name)
    return None if node is None else ast.get_source_segment(SRC, node)


# --------------------------------------------------------------------------- #
# 01-06  v1.6 history preserved (SHA gate)
# --------------------------------------------------------------------------- #
check("01_v1_6_execution_preserved",
      _sha(EXEC_V1_6) == "d2c4dfd8ab37bf6f4153cf42c2b0f45664b431af6ec626d3bdfbc4038fcfdc2b")
check("02_v1_6_unit_preserved",
      _sha(UNIT_V1_6) == "e9a1933875c2d0b9aace0b127e91395744bbe4c3b13e767d20289c38d911544d")
check("03_v1_6_preflight_preserved",
      _sha(PREFLIGHT_V1_6) == "29b7c29721e87f31dd072f013ee499ac0cd7760cccbd852199741b2d881fce29")
check("04_v1_6_negative_controls_preserved",
      _sha(NC_V1_6) == "cbb0703177e9d7bb7552de388e837300be0752753865e9a807af474ee8eaff4d")
check("05_v1_6_direct_byte_audit_preserved",
      _sha(ROOT / "reports/audits/phase36_v1_6_direct_source_byte_audit.json")
      == "af41b8ca9b902572ca9cc87686088a7e86a98850aa64f51705192633683fb3e3")
check("06_v1_6_source_freeze_preserved",
      _sha(ROOT / "reports/audits/phase36_preexecution_source_freeze_v1_6.json")
      == "59e48e63888d473322d230cc799fc2849d78cd98ed924121f44b35f3e692e147")

# --------------------------------------------------------------------------- #
# 07-09  §B defect record
# --------------------------------------------------------------------------- #
DEF = json.loads((ROOT / "reports/audits/"
                  "phase36_v1_6_pre_smoke_observability_defects_v1_7.json")
                 .read_text(encoding="utf-8"))
check("07_defect_record_three_defects", DEF["defect_count"] == 3, DEF["defect_count"])
check("08_defect_ids_d16_d17_d18",
      [d["id"].split("_")[0] for d in DEF["defects"]] == ["D16", "D17", "D18"])
check("09_defect_subject_is_v1_6",
      DEF["subject_sha256"] == "d2c4dfd8ab37bf6f4153cf42c2b0f45664b431af6ec626d3bdfbc4038fcfdc2b")

# --------------------------------------------------------------------------- #
# 10-16  §C/§D actual forward-count semantics
# --------------------------------------------------------------------------- #
core_src = _src_of("canonical_learned_core")
check("10_actual_forward_locals_initialized",
      "actual_r_psi_forwards = 0" in core_src and "actual_s_omega_forwards = 0" in core_src)
check("11_actual_r_psi_increment_after_real_call",
      "actual_r_psi_forwards += 1" in core_src
      and core_src.index('ctx["r_psi"](rin_t)') < core_src.index("actual_r_psi_forwards += 1"))
check("12_actual_s_omega_increment_after_real_call",
      "actual_s_omega_forwards += 1" in core_src
      and core_src.index("system.post_safety(") < core_src.index("actual_s_omega_forwards += 1"))
check("13_forced_safety_bypass_leaves_actual_zero",
      "if forced_s_omega_logit is not None:" in core_src
      and core_src.index("if forced_s_omega_logit is not None:")
      < core_src.index("actual_s_omega_forwards += 1"))
check("14_no_hardcoded_somega_one_in_result_branches",
      "somega=1" not in core_src and "refiner=1" not in core_src)
check("15_core_result_receives_actual_counts",
      "actual_r_psi_forwards=actual_r_psi_forwards" in core_src
      and "actual_s_omega_forwards=actual_s_omega_forwards" in core_src)
check("16_core_result_exposes_actual_counts",
      'res["actual_r_psi_forward_count"]' in SRC
      and 'res["actual_s_omega_forward_count"]' in SRC
      and 'res["policy_control"]' in SRC
      and 'res["forced_router_score"]' in SRC
      and 'res["forced_safety_logit"]' in SRC)

# --------------------------------------------------------------------------- #
# 17-20  §D/§E policy controls + real execute probe
# --------------------------------------------------------------------------- #
br_src = _src_of("smoke_branch_controls")
check("17_policy_control_flags_reported",
      '"policy_control": True' in br_src
      and '"forced_router_score": bool(out["forced_router_score"])' in br_src
      and '"forced_safety_logit": bool(out["forced_safety_logit"])' in br_src)
check("18_forced_safety_expected_actual_somega_zero",
      '("CONTROL_EXECUTE_THEN_ACCEPT", +50.0, +50.0, "EXECUTE_THEN_ACCEPT", "REFINED", 1, 0)'
      in br_src
      and '("CONTROL_EXECUTE_THEN_REJECT", +50.0, -50.0, "EXECUTE_THEN_REJECT", "GLOBAL", 1, 0)'
      in br_src
      and '("CONTROL_SKIP_GLOBAL", -50.0, None, "SKIP_GLOBAL", "GLOBAL", 0, 0)' in br_src)
check("19_no_claim_of_real_somega_in_forced_controls",
      '"claims_real_S_omega_forward": bool(actual_s > 0)' in br_src
      and "forced_safety_controls_report_zero_actual_somega" in br_src)
probe_src = _src_of("smoke_real_execute_component_probe")
check("20_real_execute_probe_defined", probe_src is not None)
check("21_real_execute_probe_forces_router_execute",
      "forced_delta_hat_final=control_router_score" in probe_src
      and "control_router_score = +50.0" in probe_src)
check("22_real_execute_probe_does_not_force_somega_logit",
      "forced_s_omega_logit=None" in probe_src)
check("23_real_execute_probe_not_outcome_selected",
      '"outcome_selected": False' in probe_src)
check("24_real_execute_probe_reports_actual_counts",
      '"actual_R_psi_forward_count": int(out["actual_r_psi_forward_count"])' in probe_src
      and '"actual_S_omega_forward_count": int(out["actual_s_omega_forward_count"])' in probe_src)
check("25_real_execute_probe_reachable_from_run_smoke",
      "smoke_real_execute_component_probe" in _calls("run_smoke"))

# --------------------------------------------------------------------------- #
# 26-29  §F real B_phi coverage
# --------------------------------------------------------------------------- #
prop_src = _src_of("smoke_nonempty_proposal_pipeline")
check("26_real_B_phi_evidence_reported",
      '"actual_B_phi_forward_count": actual_b_phi' in prop_src
      and '"real_B_phi_forward_proven"' in prop_src)
check("27_B_phi_not_inferred_from_router_decision_string",
      'delta.get("b_phi_forwards", 0)' in prop_src)
check("28_proposal_probe_does_not_force_router_score",
      "forced_delta_hat_final" not in prop_src)
check("29_B_phi_requires_forced_router_score_false",
      'out["forced_router_score"] is False' in prop_src)

# --------------------------------------------------------------------------- #
# 30-34  §G router-vector observability
# --------------------------------------------------------------------------- #
check("30_core_emits_router_vector_diagnostics",
      'res["router_vector_dim"]' in SRC and 'res["router_vector_shape"]' in SRC
      and 'res["router_vector_finite"]' in SRC
      and 'res["router_vector_min"]' in SRC and 'res["router_vector_max"]' in SRC)
check("31_router_vector_dim_guard_202",
      "ROUTER_VECTOR_DIM_VIOLATION" in core_src
      and f"rf202.shape != (ROUTER_NUMERIC_DIM,)" in core_src)
check("32_router_vector_finite_guard_before_b_phi",
      "ROUTER_VECTOR_NOT_FINITE" in core_src
      and core_src.index("ROUTER_VECTOR_NOT_FINITE")
      < core_src.index("system.benefit_router("))
check("33_router_vector_finite_computed_from_rf202",
      "np.isfinite(rf202).all()" in core_src)
check("34_rf202_finite_not_bound_to_final_probability",
      'clean_check["rf202_finite"]' in SRC
      and 'out_clean["router_vector_finite"]' in SRC
      and 'clean_check["rf202_finite"] = bool(np.isfinite(np.asarray(out_clean["final_probability"])).all())'
      not in SRC)

# --------------------------------------------------------------------------- #
# 35-40  §H top-level smoke success contract
# --------------------------------------------------------------------------- #
check("35_smoke_check_ids_frozen", len(E.SMOKE_CHECK_IDS) == 32, len(E.SMOKE_CHECK_IDS))
check("36_smoke_checks_built_in_run_smoke",
      "smoke_checks = {" in SRC and '"smoke_checks": smoke_checks' in SRC)
check("37_smoke_all_pass_derives_from_checks",
      'smoke_all_pass = bool(all(smoke_checks.values()))' in SRC
      and '"smoke_all_pass": smoke_all_pass' in SRC)
check("38_smoke_contract_id_mismatch_fails_closed",
      "SMOKE_CHECK_CONTRACT_MISMATCH" in SRC)
check("39_only_two_classification_hardcoded_true",
      E.SMOKE_CLASSIFICATION_ONLY_CHECKS == ["scientific_output_false", "synthetic_only_true"]
      and '"scientific_output_false": True' in SRC
      and '"synthetic_only_true": True' in SRC)
check("40_protected_io_check_computed_not_hardcoded",
      "_static_protected_io_unreachable()" in SRC
      and '"protected_test_holdout_runtime_io_statically_unreachable": bool(' in SRC)

# --------------------------------------------------------------------------- #
# 41-45  §I fail-closed CLI
# --------------------------------------------------------------------------- #
main_src = _src_of("main")
check("41_artifact_written_before_exit_check",
      main_src.index('(AUD / "phase36_robustness_smoke_v1_7.json").write_text(')
      < main_src.index('if not bool(res.get("smoke_all_pass"))'))
check("42_nonzero_exit_when_smoke_failed", "return 1" in main_src)
check("43_zero_exit_only_when_passed", "return 0" in main_src)
check("44_no_automatic_retry",
      main_src.count("run_smoke()") == 1
      and "while True" not in main_src
      and "for _attempt" not in main_src
      and "for attempt" not in main_src
      and "except" not in main_src,
      {"run_smoke_calls": main_src.count("run_smoke()"),
       "has_while_true": "while True" in main_src,
       "has_except": "except" in main_src})
check("45_failed_artifact_preserved_terminal",
      "PHASE36_V1_7_SMOKE_FAILED__ARTIFACT_PRESERVED__NO_RETRY" in main_src
      and '"automatic_retry": False' in main_src)

# --------------------------------------------------------------------------- #
# 46-56  §J v1.6 + earlier repairs preserved
# --------------------------------------------------------------------------- #
check("46_val808_only_runtime_authority_preserved",
      E.VAL_MANIFEST_IS_ONLY_POPULATION_RUNTIME_AUTHORITY is True
      and E.PROTECTED_RUNTIME_POPULATION == "VAL808_ONLY"
      and E.ROUTER_HOLDOUT_RUNTIME_READS_ALLOWED is False
      and E.TEST_RUNTIME_READS_ALLOWED is False)
check("47_protected_reader_functions_absent",
      not any(f in FUNCS for f in ("load_identity_authorities", "_identity_deny_set",
                                   "_holdout_selector")))
check("48_protected_io_statically_unreachable",
      E._static_protected_io_unreachable() is True)
check("49_val_manifest_guards_preserved",
      "VAL_MANIFEST_SHA_MISMATCH" in SRC and "VAL808_SAMPLE_ID_NOT_UNIQUE" in SRC
      and "NON_VAL_ROW_REJECTED" in SRC and "VAL808_MISSING_IMAGE_PATH" in SRC
      and "VAL808_MISSING_MASK_PATH" in SRC)
check("50_no_posthoc_protected_counter_reset",
      not any(isinstance(n, ast.Assign) and any(
          isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name)
          and t.value.id == "counters"
          and isinstance(t.slice, ast.Constant)
          and t.slice.value in ("router_holdout_reads", "test_reads")
          for t in n.targets) for n in ast.walk(TREE)))
check("51_canonical_probability_operator_preserved",
      E.CANONICAL_PROBABILITY_OPERATOR["expression"]
      == "torch.sigmoid(logits.float()).cpu().numpy()"
      and "prob = torch.sigmoid(t.float())" in SRC)
check("52_cuda_fail_closed_preserved",
      "get_device(require_cuda=True)" in SRC
      and "PHASE36_V1_5_CUDA_FAIL_CLOSED__DEVICE_TYPE" in SRC
      and E.CANONICAL_DEVICE_CONTRACT["cpu_scientific_fallback_permitted"] is False)
check("53_four_component_device_binding_preserved",
      all(t in SRC for t in ("g.to(device)", "b_phi.to(device)",
                             "r_psi.to(device)", "s_omega.to(device)")))
CTX = E.COMPONENT_INFERENCE_CONTEXTS
check("54_component_contexts_preserved",
      CTX["G"]["inference_mode"] is False and CTX["G"]["autocast_enabled"] is True
      and all(CTX[c]["inference_mode"] is True and CTX[c]["autocast_enabled"] is False
              for c in ("B_phi", "R_psi", "S_omega")))
node = FUNCS["canonical_learned_core"]
dec = min([n.lineno for n in ast.walk(node)
           if isinstance(n, ast.Compare) and isinstance(n.comparators[0], ast.Name)
           and n.comparators[0].id == "TAU_C8_FINAL_FLOAT"] or [10 ** 9])
rpsi = min([n.lineno for n in ast.walk(node)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Subscript)
            and "r_psi" in ast.unparse(n.func)] or [10 ** 9])
somega = min([n.lineno for n in ast.walk(node)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
              and n.func.attr == "post_safety"] or [10 ** 9])
check("55_conditional_execution_order_preserved", dec < rpsi and dec < somega,
      {"decision": dec, "r_psi": rpsi, "s_omega": somega})
check("56_skip_branch_zero_actual_forwards",
      "actual_r_psi_forwards=0, actual_s_omega_forwards=0" in SRC)

# --------------------------------------------------------------------------- #
# 57-62  frozen science constants unchanged
# --------------------------------------------------------------------------- #
check("57_registries_and_counts_unchanged",
      len(E.image_realization_plan()) == 16 and len(E.proposal_realization_plan()) == 6
      and E.NONCLEAN_IMAGE_EXECUTIONS_EXPECTED == 12928
      and E.NONCLEAN_PROPOSAL_EXECUTIONS_MAX == 4848
      and E.CLEAN_EXECUTIONS_EXPECTED == 808)
check("58_thresholds_unchanged",
      E.SEGMENTATION_OUTPUT_THRESHOLD == 0.50 and E.ROI_PROPOSAL_THRESHOLD == 0.30
      and E.SOMEGA_ACCEPT_THRESHOLD == 0.50)
check("59_component_identities_unchanged",
      E.G_COMPONENT["sha256"] == "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7"
      and E.B_PHI_COMPONENT["sha256"] == "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b"
      and E.R_PSI_COMPONENT["sha256"] == "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109"
      and E.S_OMEGA_COMPONENT["sha256"] == "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e")
check("60_feature_dependency_98_104",
      C.PROPOSAL_CONTRACT_V1_1["geometry_dependent_dims"] == 98
      and C.PROPOSAL_CONTRACT_V1_1["global_only_dims"] == 104)
check("61_phase27_authority_and_partition_unchanged",
      E.PHASE27_GLOBAL_PROB_AUTHORITY["sha256"]
      == "cc6c54af986f56b4aba9265405ffeba4f6cac582eeff00fe6b0894429e7d3f13"
      and E.canonical_batch_plan_audit()["matches_phase27_exact_partition"] is True)
check("62_kub_and_figures_preserved",
      "def kub_subgroup_map" in SRC
      and all(f"def figure_R{i}" in SRC for i in range(1, 6))
      and "generate_all_figures" in _calls("run_science"))

# --------------------------------------------------------------------------- #
# 63-65  import safety / no training
# --------------------------------------------------------------------------- #
check("63_import_safety_no_torch", "torch" not in sys.modules)
check("64_no_training_paths",
      ".backward()" not in SRC and "torch.optim" not in SRC
      and "requires_grad_(True)" not in SRC and ".train()" not in SRC)
check("65_gates_unchanged",
      C.GATE_ENV == "PHASE36_EXECUTE" and C.SMOKE_GATE_ENV == "PHASE36_SMOKE_EXECUTE")

passed = sum(1 for c in checks if c["passed"])
total = len(checks)
report = {
    "artifact": "phase36_robustness_unit_v1_7",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_7",
    "model_free": True,
    "torch_imported": False,
    "protected_population_read": False,
    "checks": checks,
    "passed": passed,
    "total": total,
    "all_pass": passed == total,
}
out = ROOT / "reports/audits/phase36_robustness_unit_v1_7.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"passed": passed, "total": total, "all_pass": passed == total}, indent=1))
for c in checks:
    if not c["passed"]:
        print("FAIL:", c["check"], json.dumps(c.get("detail"), default=str))
raise SystemExit(0 if passed == total else 1)
