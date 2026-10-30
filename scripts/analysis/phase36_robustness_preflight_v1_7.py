#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.7 — static preflight (AST / call-graph / byte proof).

METHOD: RA-MedFiLM-BARR
REVISION: ra_medfilm_barr_phase36_robustness_v1_7

NO torch. NO model. NO protected-population read. AST + byte analysis only.

§L CHECKLIST PROVEN
  * actual forward-count semantics (increment only after a real module call)
  * forced-safety path leaves the ACTUAL S_omega count at 0
  * real execute probe source exists and does NOT force the S_omega logit
  * router 202-D finite diagnostic binds rf202 (never final_probability)
  * router vector exact dim guard = 202, checked BEFORE B_phi
  * top-level smoke_checks exists; smoke_all_pass derives from it
  * artifact written BEFORE a nonzero fail exit; no automatic retry
  * v1.6 protected-population constraints preserved (both entrypoints)
  * canonical probability / CUDA / device / component-context constraints preserved
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

EXEC = ROOT / "scripts/analysis/phase36_robustness_execution_v1_7.py"
SRC = EXEC.read_text(encoding="utf-8")
TREE = ast.parse(SRC)

import scripts.analysis.phase36_robustness_execution_v1_7 as E  # noqa: E402

checks = []


def check(name, cond, detail=None):
    checks.append({"check": name, "passed": bool(cond), "detail": detail})


FUNCS = {n.name: n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef)}

PROTECTED_SYMBOLS = ("TEST_MANIFEST", "ROUTER_HOLDOUT_MANIFEST",
                     "ROUTER_HOLDOUT_IDENTITY_AUTHORITY")
PROTECTED_PATH_TOKENS = ("val_router_holdout", "phase24_router_split_manifest",
                         "phase4_v3/test.csv")
SELF_DETECTOR = "_static_protected_io_unreachable"


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


def _protected_sites(fns):
    hits = []
    for name in sorted(fns):
        if name == SELF_DETECTOR:
            continue
        for x in ast.walk(FUNCS[name]):
            if isinstance(x, ast.Name) and x.id in PROTECTED_SYMBOLS:
                hits.append({"function": name, "line": x.lineno, "detail": x.id})
            if isinstance(x, ast.Constant) and isinstance(x.value, str):
                for t in PROTECTED_PATH_TOKENS:
                    if t in x.value:
                        hits.append({"function": name, "line": x.lineno,
                                     "detail": x.value[:70]})
    return hits


def _src_of(fn):
    node = FUNCS.get(fn)
    return None if node is None else ast.get_source_segment(SRC, node)


rs = _reachable("run_science")
rm = _reachable("run_smoke")
rs_prot = _protected_sites(rs)
rm_prot = _protected_sites(rm)
core = _src_of("canonical_learned_core")
br = _src_of("smoke_branch_controls")
probe = _src_of("smoke_real_execute_component_probe")
prop = _src_of("smoke_nonempty_proposal_pipeline")
main_src = _src_of("main")

# --------------------------------------------------------------------------- #
# 01-05  §C/§D actual forward-count semantics
# --------------------------------------------------------------------------- #
check("01_actual_forward_locals_initialized",
      "actual_r_psi_forwards = 0" in core and "actual_s_omega_forwards = 0" in core)
check("02_r_psi_increment_after_real_call",
      core.index('ctx["r_psi"](rin_t)') < core.index("actual_r_psi_forwards += 1"))
check("03_s_omega_increment_after_real_call",
      core.index("system.post_safety(") < core.index("actual_s_omega_forwards += 1"))
check("04_forced_safety_bypass_precedes_increment",
      core.index("if forced_s_omega_logit is not None:")
      < core.index("actual_s_omega_forwards += 1"))
check("05_no_hardcoded_forward_counts_in_result_branches",
      "somega=1" not in core and "refiner=1" not in core)

# --------------------------------------------------------------------------- #
# 06-10  §D policy controls
# --------------------------------------------------------------------------- #
check("06_policy_control_flags_present",
      '"policy_control": True' in br and '"forced_router_score":' in br
      and '"forced_safety_logit":' in br)
check("07_forced_safety_expected_actual_somega_zero",
      '("CONTROL_EXECUTE_THEN_ACCEPT", +50.0, +50.0, "EXECUTE_THEN_ACCEPT", "REFINED", 1, 0)'
      in br
      and '("CONTROL_EXECUTE_THEN_REJECT", +50.0, -50.0, "EXECUTE_THEN_REJECT", "GLOBAL", 1, 0)'
      in br)
check("08_skip_control_actual_counts_zero",
      '("CONTROL_SKIP_GLOBAL", -50.0, None, "SKIP_GLOBAL", "GLOBAL", 0, 0)' in br)
check("09_forced_controls_do_not_claim_real_somega",
      '"claims_real_S_omega_forward": bool(actual_s > 0)' in br
      and "forced_safety_controls_report_zero_actual_somega" in br)
check("10_policy_controls_labelled_not_scientific",
      "policy_controls_not_scientific_outcomes" in br)

# --------------------------------------------------------------------------- #
# 11-15  §E real execute probe
# --------------------------------------------------------------------------- #
check("11_real_execute_probe_defined", probe is not None)
check("12_probe_forces_router_execute",
      "forced_delta_hat_final=control_router_score" in probe)
check("13_probe_does_not_force_somega_logit", "forced_s_omega_logit=None" in probe)
check("14_probe_not_outcome_selected", '"outcome_selected": False' in probe)
check("15_probe_reports_actual_counts_and_finiteness",
      '"actual_R_psi_forward_count"' in probe and '"actual_S_omega_forward_count"' in probe
      and '"post_safety_logit_finite"' in probe
      and '"final_probability_finite"' in probe)
check("16_probe_reachable_from_run_smoke",
      "smoke_real_execute_component_probe" in _calls("run_smoke"))

# --------------------------------------------------------------------------- #
# 17-20  §F real B_phi coverage
# --------------------------------------------------------------------------- #
check("17_real_B_phi_evidence_present",
      '"actual_B_phi_forward_count": actual_b_phi' in prop
      and '"real_B_phi_forward_proven"' in prop)
check("18_B_phi_from_counter_not_router_string",
      'delta.get("b_phi_forwards", 0)' in prop)
check("19_proposal_probe_does_not_force_router_score",
      "forced_delta_hat_final" not in prop)
check("20_B_phi_proof_requires_unforced_router",
      'out["forced_router_score"] is False' in prop)

# --------------------------------------------------------------------------- #
# 21-25  §G router-vector observability
# --------------------------------------------------------------------------- #
check("21_router_vector_diagnostics_emitted",
      'res["router_vector_dim"]' in SRC and 'res["router_vector_shape"]' in SRC
      and 'res["router_vector_finite"]' in SRC
      and 'res["router_vector_min"]' in SRC and 'res["router_vector_max"]' in SRC)
check("22_router_dim_guard_202",
      "ROUTER_VECTOR_DIM_VIOLATION" in core and "(ROUTER_NUMERIC_DIM,)" in core)
check("23_router_finite_guard_before_b_phi",
      "ROUTER_VECTOR_NOT_FINITE" in core
      and core.index("ROUTER_VECTOR_NOT_FINITE") < core.index("system.benefit_router("))
check("24_router_finite_from_rf202",
      "np.isfinite(rf202).all()" in core)
check("25_rf202_finite_not_bound_to_final_probability",
      'out_clean["router_vector_finite"]' in SRC
      and 'clean_check["rf202_finite"] = bool(np.isfinite(np.asarray(out_clean["final_probability"])).all())'
      not in SRC)

# --------------------------------------------------------------------------- #
# 26-31  §H smoke success contract
# --------------------------------------------------------------------------- #
check("26_smoke_check_ids_count_32", len(E.SMOKE_CHECK_IDS) == 32)
check("27_smoke_checks_built", "smoke_checks = {" in SRC)
check("28_smoke_all_pass_derives_from_checks",
      "smoke_all_pass = bool(all(smoke_checks.values()))" in SRC)
check("29_contract_id_mismatch_fails_closed",
      "SMOKE_CHECK_CONTRACT_MISMATCH" in SRC)
check("30_only_two_classification_hardcoded_true",
      E.SMOKE_CLASSIFICATION_ONLY_CHECKS == ["scientific_output_false", "synthetic_only_true"])
check("31_protected_io_check_computed_not_hardcoded",
      "_static_protected_io_unreachable()" in SRC)

# --------------------------------------------------------------------------- #
# 32-36  §I fail-closed CLI
# --------------------------------------------------------------------------- #
check("32_artifact_written_before_exit_check",
      main_src.index('phase36_robustness_smoke_v1_7.json')
      < main_src.index('if not bool(res.get("smoke_all_pass"))'))
check("33_nonzero_exit_when_failed", "return 1" in main_src)
check("34_no_retry_loop_or_except",
      main_src.count("run_smoke()") == 1 and "while True" not in main_src
      and "except" not in main_src)
check("35_failed_artifact_terminal_present",
      "PHASE36_SMOKE_FAILED__ARTIFACT_PRESERVED__NO_RETRY" in main_src
      or "PHASE36_V1_7_SMOKE_FAILED__ARTIFACT_PRESERVED__NO_RETRY" in main_src)
check("36_automatic_retry_declared_false",
      '"automatic_retry": False' in main_src
      and E.SMOKE_SUCCESS_CONTRACT["automatic_retry"] is False)

# --------------------------------------------------------------------------- #
# 37-44  §J v1.6 preservation
# --------------------------------------------------------------------------- #
check("37_run_science_protected_sites_zero", len(rs_prot) == 0, rs_prot)
check("38_run_smoke_protected_sites_zero", len(rm_prot) == 0, rm_prot)
check("39_val808_only_runtime_authority",
      E.VAL_MANIFEST_IS_ONLY_POPULATION_RUNTIME_AUTHORITY is True
      and E.PROTECTED_RUNTIME_POPULATION == "VAL808_ONLY"
      and E.ROUTER_HOLDOUT_RUNTIME_READS_ALLOWED is False
      and E.TEST_RUNTIME_READS_ALLOWED is False)
check("40_protected_reader_functions_absent",
      not any(f in FUNCS for f in ("load_identity_authorities", "_identity_deny_set",
                                   "_holdout_selector")))
check("41_val_guards_preserved",
      "VAL_MANIFEST_SHA_MISMATCH" in SRC and "VAL808_SAMPLE_ID_NOT_UNIQUE" in SRC
      and "NON_VAL_ROW_REJECTED" in SRC)
check("42_no_posthoc_protected_counter_reset",
      not any(isinstance(n, ast.Assign) and any(
          isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name)
          and t.value.id == "counters" and isinstance(t.slice, ast.Constant)
          and t.slice.value in ("router_holdout_reads", "test_reads")
          for t in n.targets) for n in ast.walk(TREE)))
check("43_canonical_probability_cuda_device_context_preserved",
      E.CANONICAL_PROBABILITY_OPERATOR["expression"]
      == "torch.sigmoid(logits.float()).cpu().numpy()"
      and "get_device(require_cuda=True)" in SRC
      and all(t in SRC for t in ("g.to(device)", "b_phi.to(device)",
                                 "r_psi.to(device)", "s_omega.to(device)"))
      and all(f'component_inference_context("{c}")' in SRC
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
check("44_conditional_execution_preserved",
      dec < rpsi and dec < somega
      and "actual_r_psi_forwards=0, actual_s_omega_forwards=0" in SRC)

# --------------------------------------------------------------------------- #
# 45-48  retained reporting + prohibitions
# --------------------------------------------------------------------------- #
check("45_kub_and_figures_preserved",
      "def kub_subgroup_map" in SRC
      and all(f"def figure_R{i}" in SRC for i in range(1, 6))
      and "generate_all_figures" in _calls("run_science"))
check("46_no_training",
      ".backward()" not in SRC and "torch.optim" not in SRC
      and "requires_grad_(True)" not in SRC and ".train()" not in SRC)
check("47_torch_not_imported_by_preflight", "torch" not in sys.modules)
check("48_frozen_counts_and_partition",
      E.NONCLEAN_IMAGE_EXECUTIONS_EXPECTED == 12928
      and E.NONCLEAN_PROPOSAL_EXECUTIONS_MAX == 4848
      and E.canonical_batch_plan_audit()["matches_phase27_exact_partition"] is True)

passed = sum(1 for c in checks if c["passed"])
total = len(checks)
report = {
    "artifact": "phase36_robustness_static_preflight_v1_7",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_7",
    "method": "AST_CALL_GRAPH_AND_BYTE_PREFLIGHT",
    "audited_source": "scripts/analysis/phase36_robustness_execution_v1_7.py",
    "entrypoints": ["run_science", "run_smoke"],
    "run_science_reachable_functions": len(rs),
    "run_smoke_reachable_functions": len(rm),
    "run_science_protected_io_sites": rs_prot,
    "run_smoke_protected_io_sites": rm_prot,
    "smoke_check_ids_count": len(E.SMOKE_CHECK_IDS),
    "smoke_success_contract": dict(E.SMOKE_SUCCESS_CONTRACT),
    "torch_imported": "torch" in sys.modules,
    "checks": checks,
    "passed": passed,
    "total": total,
    "all_pass": passed == total,
}
out = ROOT / "reports/audits/phase36_robustness_static_preflight_v1_7.json"
out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"passed": passed, "total": total, "all_pass": passed == total}, indent=1))
for c in checks:
    if not c["passed"]:
        print("FAIL:", c["check"], json.dumps(c.get("detail"), default=str))
raise SystemExit(0 if passed == total else 1)
