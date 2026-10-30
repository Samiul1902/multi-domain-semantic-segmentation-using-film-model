#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.4 — model-free unit checks.

METHOD: RA-MedFiLM-BARR
REVISION: ra_medfilm_barr_phase36_robustness_v1_4

NO torch. NO model. NO checkpoint. NO protected-data read. Pure static/unit logic.

Inherits the v1.3 unit surface and ADDS the v1.4 repairs:
  * v1.3 / v1.3a history preserved (SHA gates)
  * canonical Phase27 numerical constants bound
  * canonical domain-local batch-8 partition reproduces the frozen Phase27
    exact partition (102 batches; 11/45/35/11; last 4/5/8/7)
  * ROUTER_HOLDOUT identity deny set now POPULATED (875) with CASE-B retained
  * shared canonical core ordering: R_psi and S_omega only AFTER the decision
  * router_decision structurally separated from final_state
  * KUB subgroup reporting bound to the frozen metadata authority
  * R1-R5 figure registry implemented
  * NC15-NC24 delegated to the v1.4 negative-control module

Exit code 0 == all checks pass. Prints a JSON report.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

import scripts.analysis.phase36_robustness_execution_v1_4 as E  # noqa: E402
import scripts.analysis.phase36_robustness_common_v1_1 as C  # noqa: E402

EXEC_V1_4 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_4.py"
EXEC_V1_3 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_3.py"
UNIT_V1_3 = ROOT / "scripts/analysis/phase36_robustness_unit_v1_3.py"
PREFLIGHT_V1_3 = ROOT / "scripts/analysis/phase36_robustness_preflight_v1_3.py"
NC_V1_3 = ROOT / "scripts/analysis/phase36_robustness_negative_controls_v1_3.py"

checks = []


def check(name: str, cond: bool, detail=None):
    checks.append({"check": name, "passed": bool(cond), "detail": detail})


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


SRC = EXEC_V1_4.read_text(encoding="utf-8")
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


def _line_in(fn_name, pred):
    node = FUNCS.get(fn_name)
    if node is None:
        return None
    hits = [n.lineno for n in ast.walk(node) if pred(n)]
    return min(hits) if hits else None


def _reachable_from(fn_name, target, seen=None):
    """True iff ``target`` is DIRECTLY or TRANSITIVELY called from ``fn_name``."""
    seen = set() if seen is None else seen
    if fn_name in seen:
        return False
    seen.add(fn_name)
    cs = _calls(fn_name)
    if target in cs:
        return True
    return any(_reachable_from(c, target, seen) for c in cs if c in FUNCS)


def _funcs_referencing(token):
    return sorted(name for name, node in FUNCS.items()
                  if token in ast.get_source_segment(SRC, node))


# --------------------------------------------------------------------------- #
# 01-06  v1.3 / v1.3a history preserved (SHA gate)
# --------------------------------------------------------------------------- #
check("01_v1_3_execution_preserved",
      _sha(EXEC_V1_3) == "a3290c640f9632499905b974606d4c7e7e7be89886ef1f8507a9007814da297c")
check("02_v1_3_unit_preserved",
      _sha(UNIT_V1_3) == "01c5e960a01b1e3bcda350c923c7aa3761075385fdc606d871c8ab0d3503e7cb")
check("03_v1_3_preflight_preserved",
      _sha(PREFLIGHT_V1_3) == "769b3a8c7a5852858897ba65c0f29d57d7829dd3c38cfbd537ae2cf33b7704f1")
check("04_v1_3_negative_controls_preserved",
      _sha(NC_V1_3) == "6b9b87a28e8a89c0bf2a7c272b140018407c67845cfc53fe28bdd386c24d195d")
check("05_v1_3_source_freeze_preserved",
      _sha(ROOT / "reports/audits/phase36_preexecution_source_freeze_v1_3.json")
      == "9e80b62d03cb3186eec75b1ef389c000b8c1959c58ebb3099dbb2ebcadde0724")
check("06_v1_3_direct_byte_audit_preserved",
      _sha(ROOT / "reports/audits/phase36_v1_3_direct_source_byte_audit.json")
      == "6549f713c6e7e6ea90f77289db8634feeab4ef3ef1f824e814befda54dbf813d")

# --------------------------------------------------------------------------- #
# 07-11  defect record (§B)
# --------------------------------------------------------------------------- #
DEFECTS = json.loads((ROOT / "reports/audits/"
                      "phase36_v1_3_post_byte_audit_semantic_defects_v1_4.json")
                     .read_text(encoding="utf-8"))
check("07_defect_record_10_defects", DEFECTS["defect_count"] == 10, DEFECTS["defect_count"])
check("08_defect_record_subject_is_v1_3",
      DEFECTS["subject_sha256"] == "a3290c640f9632499905b974606d4c7e7e7be89886ef1f8507a9007814da297c")
check("09_defect_record_classification",
      DEFECTS["classification"]
      == "PRE_SCIENTIFIC_SOURCE_SEMANTIC_AND_SMOKE_COVERAGE_DEFECTS__NO_SCIENTIFIC_EFFECT")
check("10_defect_ids_complete",
      [d["id"] for d in DEFECTS["defects"]] == [f"D{i}" for i in range(1, 11)])
check("11_defects_have_no_scientific_effect",
      DEFECTS["defects_affecting_scientific_claims"] == 0)

# --------------------------------------------------------------------------- #
# 12-16  canonical Phase27 numerical authority (§D)
# --------------------------------------------------------------------------- #
check("12_canonical_device_cuda", E.CANONICAL_G_DEVICE == "cuda")
check("13_canonical_autocast_fp16",
      E.CANONICAL_G_AUTOCAST_ENABLED is True and E.CANONICAL_G_AUTOCAST_DTYPE == "float16")
check("14_canonical_inference_mode_false", E.CANONICAL_G_INFERENCE_MODE is False)
check("15_canonical_batch_size_8", E.CANONICAL_G_BATCH_SIZE == 8)
check("16_canonical_dtypes_fp32",
      E.CANONICAL_G_MODEL_DTYPE == "float32" and E.CANONICAL_G_INPUT_DTYPE == "float32")

# --------------------------------------------------------------------------- #
# 17-21  canonical batch partition reproduces the frozen Phase27 exact partition
# --------------------------------------------------------------------------- #
audit = E.canonical_batch_plan_audit()
check("17_partition_total_102", audit["total_batches"] == 102, audit["total_batches"])
check("18_partition_sample_forwards_808", audit["total_sample_forwards"] == 808)
check("19_partition_by_domain",
      audit["batches_by_domain"] == {"BUSI": 11, "ISIC": 45, "KUB": 35, "KVASIR": 11},
      audit["batches_by_domain"])
check("20_partition_last_batch_sizes",
      audit["last_batch_size_by_domain"] == {"BUSI": 4, "ISIC": 5, "KUB": 8, "KVASIR": 7},
      audit["last_batch_size_by_domain"])
check("21_partition_matches_phase27", audit["matches_phase27_exact_partition"] is True)

# --------------------------------------------------------------------------- #
# 22-25  phase27 global probability authority (§E)
# --------------------------------------------------------------------------- #
PA = E.PHASE27_GLOBAL_PROB_AUTHORITY
check("22_phase27_authority_path",
      PA["path"] == "data_cache/phase27_barr_preservation_v1_0/phase27_val808_global_prob_f16.npy")
check("23_phase27_authority_sha",
      PA["sha256"] == "cc6c54af986f56b4aba9265405ffeba4f6cac582eeff00fe6b0894429e7d3f13")
check("24_phase27_authority_file_exists_and_sha_matches",
      (ROOT / PA["path"]).exists() and _sha(ROOT / PA["path"]) == PA["sha256"])
check("25_reproduction_gate_prefers_bit_identical",
      E.CLEAN_G_REPRODUCTION_GATE["preferred"]
      == "BIT_IDENTICAL_FLOAT16_PERSISTED_GLOBAL_PROBABILITY"
      and E.CLEAN_G_REPRODUCTION_GATE["silent_acceptance_of_changed_G_numeric_path"] == "FORBIDDEN")

# --------------------------------------------------------------------------- #
# 26-30  realization plans / counts
# --------------------------------------------------------------------------- #
plan = E.image_realization_plan()
check("26_image_plan_16_nonclean",
      len(plan) == 16 and all(p["condition"] != "CLEAN" for p in plan))
check("27_image_plan_10_det_6_noise",
      sum(1 for p in plan if not p["is_noise"]) == 10
      and sum(1 for p in plan if p["is_noise"]) == 6)
check("28_noise_seeds_frozen",
      sorted({int(p["base_seed"]) for p in plan if p["is_noise"]}) == [42, 123, 3407])
pplan = E.proposal_realization_plan()
check("29_proposal_plan_6", len(pplan) == 6
      and all(p["proposal_condition"] != "PROPOSAL_CLEAN" for p in pplan))
check("30_frozen_counts",
      E.NONCLEAN_IMAGE_EXECUTIONS_EXPECTED == 12928
      and E.LOGICAL_IMAGE_TABLE_ROWS_MAX == 13736
      and E.NONCLEAN_PROPOSAL_EXECUTIONS_MAX == 4848
      and E.CLEAN_EXECUTIONS_EXPECTED == 808)

# --------------------------------------------------------------------------- #
# 31-38  CASE-B split authority retained AND strengthened (§C)
# --------------------------------------------------------------------------- #
auth = E.load_identity_authorities()
check("31_case_b_retained", auth["case"] == "CASE_B")
check("32_primary_authority_unchanged",
      auth["primary_authority"] == "EXACT_VAL808_MANIFEST_MEMBERSHIP_PLUS_EXACT_ROW_PATHS")
check("33_holdout_deny_set_now_populated_875", auth["holdout_deny_set_size"] == 875,
      auth["holdout_deny_set_size"])
check("34_holdout_canonical_authority_bound",
      auth["holdout_canonical_path"] == "reports/audits/phase24_router_split_manifest.csv"
      and auth["holdout_canonical_size"] == 875)
check("35_test_deny_set_1683", auth["test_deny_set_size"] == 1683)
rows = E._load_population()
check("36_population_808", len(rows) == 808)
pop_index = {r["sample_id"]: r for r in rows}
tr = [r for r in rows if "ISIC2018_Task1-2_Training_Input" in str(r["image_path"])]
te = [r for r in rows if "ISIC2018_Task1-2_Test_Input" in str(r["image_path"])]


def _accepted(rs):
    n = 0
    for r in rs:
        try:
            E.authorize_sample(r["sample_id"], r["image_path"], r["mask_path"],
                               pop_index, auth["holdout"], auth["test"])
            n += 1
        except Exception:
            pass
    return n


check("37_231_training_input_accepted",
      len(tr) == 231 and _accepted(tr) == 231, {"n": len(tr), "acc": _accepted(tr)})
check("38_112_test_input_accepted",
      len(te) == 112 and _accepted(te) == 112, {"n": len(te), "acc": _accepted(te)})

# negative: vendor-substring guard must be absent
check("39_no_vendor_substring_split",
      '"test" in' not in SRC and "'test' in" not in SRC
      and '"train" in' not in SRC and "'train' in" not in SRC)
check("40_vendor_metadata_never_split_label",
      "VENDOR_DIRECTORY_NAMES_ARE_TRANSPORT_METADATA = True" in SRC)
check("41_holdout_identity_denied",
      "ROUTER_HOLDOUT_IDENTITY_REJECTED" in SRC)
check("42_test_identity_denied", "TEST_IDENTITY_REJECTED" in SRC)

# --------------------------------------------------------------------------- #
# 43-50  §F conditional state machine + §G decision separation
# --------------------------------------------------------------------------- #
dec_line = _line_in("canonical_learned_core",
                    lambda n: isinstance(n, ast.Compare)
                    and isinstance(n.comparators[0], ast.Name)
                    and n.comparators[0].id == "TAU_C8_FINAL_FLOAT")
rpsi_line = _line_in("canonical_learned_core",
                     lambda n: isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                     and n.func.id == "crop_and_resize_vec")
somega_line = _line_in("canonical_learned_core",
                       lambda n: isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                       and n.func.attr == "post_safety")
check("43_decision_line_present", dec_line is not None, dec_line)
check("44_r_psi_after_decision",
      dec_line is not None and rpsi_line is not None and dec_line < rpsi_line,
      {"decision": dec_line, "r_psi_path": rpsi_line})
check("45_s_omega_after_decision",
      dec_line is not None and somega_line is not None and dec_line < somega_line,
      {"decision": dec_line, "s_omega": somega_line})
check("46_no_pre_decision_r_psi_in_v1_4",
      not re.search(r'ctx\["r_psi"\]\(', SRC.split("def canonical_learned_core")[0]))
check("47_router_decision_not_from_state",
      'router_decision"] = out.get("state")' not in SRC
      and "router_decision'] = out.get('state')" not in SRC)
check("48_router_decision_vocabulary",
      "ROUTER_DECISIONS = (\"SKIP\", \"EXECUTE\")" in SRC)
check("49_row_builder_rejects_noncanonical_router_decision",
      "ROUTER_DECISION_NOT_CANONICAL" in SRC)
check("50_exact_branch_comparison_implemented",
      "n_state_machine_branch_comparisons_808" in SRC
      and "route_branch_mismatches_zero" in SRC
      and "accept_reject_collapse_prohibited" in SRC)

try:
    E.build_image_result_row(sid="s", domain="ISIC", task_id=0, cond="BRIGHTNESS_NEG",
                             base_seed=None, derived_seed=None, clean_dice=0.5,
                             perturbed_dice=0.4, prediction_consistency_dice=0.9,
                             clean_route_state="SKIP_GLOBAL",
                             perturbed_route_state="SKIP_GLOBAL",
                             clean_router_decision="SKIP_GLOBAL",
                             perturbed_router_decision="SKIP",
                             final_source="GLOBAL", perturbed_final_source="GLOBAL")
    check("51_row_builder_rejects_final_state_as_router_decision", False)
except Exception as ex:
    check("51_row_builder_rejects_final_state_as_router_decision",
          "ROUTER_DECISION_NOT_CANONICAL" in str(ex), str(ex))

ok_row = E.build_image_result_row(sid="s", domain="ISIC", task_id=0, cond="BRIGHTNESS_NEG",
                                  base_seed=None, derived_seed=None, clean_dice=0.5,
                                  perturbed_dice=0.4, prediction_consistency_dice=0.9,
                                  clean_route_state="SKIP_GLOBAL",
                                  perturbed_route_state="EXECUTE_THEN_REJECT",
                                  clean_router_decision="SKIP",
                                  perturbed_router_decision="EXECUTE",
                                  final_source="GLOBAL", perturbed_final_source="GLOBAL")
check("52_row_paired_delta", abs(ok_row["paired_delta_dice"] + 0.1) < 1e-12)
check("53_row_router_decision_changed_flag",
      ok_row["router_decision_changed"] is True
      and ok_row["route_state_changed"] is True)
check("54_row_all_required_fields",
      all(k in ok_row for k in E._IMAGE_ROW_REQUIRED))

# --------------------------------------------------------------------------- #
# 55-58  §H/§I/§J/§K shared core + smoke coverage
# --------------------------------------------------------------------------- #
check("55_shared_core_defined", "def canonical_learned_core" in SRC)
check("56_proposal_adapter_defined", "def proposal_core_adapter" in SRC)
smoke_calls = _calls("run_smoke")
check("57_run_smoke_reaches_real_proposal_adapter",
      _reachable_from("run_smoke", "proposal_core_adapter")
      and "canonical_learned_core" in smoke_calls,
      {"direct_calls": sorted(c for c in smoke_calls if c in FUNCS)})
check("58_smoke_branch_controls_three_branches",
      "smoke_branch_controls" in smoke_calls
      and all(s in SRC for s in ("CONTROL_SKIP_GLOBAL", "CONTROL_EXECUTE_THEN_ACCEPT",
                                 "CONTROL_EXECUTE_THEN_REJECT")))
check("59_smoke_empty_proposal_real_evaluator",
      "smoke_empty_proposal_pipeline" in smoke_calls
      and _reachable_from("smoke_empty_proposal_pipeline", "proposal_core_adapter")
      and "NOT_APPLICABLE_EMPTY_PROPOSAL" in SRC)
check("60_proposal_adapter_reachable_from_science",
      _reachable_from("run_proposal_perturbations", "proposal_core_adapter"))
check("60b_shared_core_reachable_from_both",
      _reachable_from("run_science", "canonical_learned_core")
      and _reachable_from("run_smoke", "canonical_learned_core"))

# --------------------------------------------------------------------------- #
# 61-64  §L KUB subgroup reporting
# --------------------------------------------------------------------------- #
sub = E.kub_subgroup_map()
check("61_kub_subgroup_map_280", len(sub) == 280, len(sub))
check("62_kub_subgroup_counts",
      Counter(sub.values()) == Counter({"Bladder_Stone": 144, "Kidney_Stone": 112,
                                        "Ureteric_Stone": 24}),
      dict(Counter(sub.values())))
check("63_kub_subgroups_frozen",
      E.KUB_SUBGROUP_AUTHORITY["subgroups"]
      == ["Kidney_Stone", "Bladder_Stone", "Ureteric_Stone"])
check("64_kub_reporting_only",
      E.KUB_SUBGROUP_AUTHORITY["reporting_only"] is True
      and E.KUB_SUBGROUP_AUTHORITY["never_classes"] is True
      and E.KUB_SUBGROUP_AUTHORITY["never_task_ids"] is True
      and E.KUB_SUBGROUP_AUTHORITY["never_model_inputs"] is True)

# --------------------------------------------------------------------------- #
# 65-68  §M R1-R5 figure registry
# --------------------------------------------------------------------------- #
check("65_figure_registry_r1_r5",
      sorted(E.FIGURE_REGISTRY.keys()) == ["R1", "R2", "R3", "R4", "R5"],
      sorted(E.FIGURE_REGISTRY.keys()))
check("66_figure_builders_defined",
      all(f"def figure_R{i}" in SRC for i in range(1, 6)))
check("67_figure_registry_unchanged_from_common",
      dict(E.FIGURE_REGISTRY) == dict(C.FIGURES))
check("68_figures_reachable_from_science",
      "generate_all_figures" in _calls("run_science"))

# --------------------------------------------------------------------------- #
# 69-72  no TEST / no ROUTER_HOLDOUT data read, no training
# --------------------------------------------------------------------------- #
check("69_test_manifest_confined_to_identity_deny",
      _funcs_referencing("TEST_MANIFEST") == ["load_identity_authorities"],
      _funcs_referencing("TEST_MANIFEST"))
check("70_holdout_manifest_confined_to_identity_deny",
      _funcs_referencing("ROUTER_HOLDOUT_MANIFEST") == ["load_identity_authorities"]
      and _funcs_referencing("ROUTER_HOLDOUT_IDENTITY_AUTHORITY")
      == ["load_identity_authorities"],
      {"configured": _funcs_referencing("ROUTER_HOLDOUT_MANIFEST"),
       "canonical": _funcs_referencing("ROUTER_HOLDOUT_IDENTITY_AUTHORITY")})
check("71_no_training_paths",
      ".backward()" not in SRC
      and "torch.optim" not in SRC
      and "optim.Adam" not in SRC
      and "requires_grad_(True)" not in SRC
      and ".train()" not in SRC)
check("72_no_eval_mode_off",
      "CANONICAL_G_MODEL_EVAL = True" in SRC)

# --------------------------------------------------------------------------- #
# 73-74  import safety
# --------------------------------------------------------------------------- #
check("73_torch_not_imported_on_import", "torch" not in sys.modules)
check("74_import_safe_no_execution",
      "def run_science()" in SRC and "def run_smoke()" in SRC
      and "def main()" in SRC)

passed = sum(1 for c in checks if c["passed"])
total = len(checks)
report = {
    "artifact": "phase36_robustness_unit_v1_4",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_4",
    "model_free": True,
    "torch_imported": False,
    "checks": checks,
    "passed": passed,
    "total": total,
    "all_pass": passed == total,
}
out = ROOT / "reports/audits/phase36_robustness_unit_v1_4.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"passed": passed, "total": total, "all_pass": passed == total}, indent=1))
for c in checks:
    if not c["passed"]:
        print("FAIL:", c["check"], c["detail"])
raise SystemExit(0 if passed == total else 1)
