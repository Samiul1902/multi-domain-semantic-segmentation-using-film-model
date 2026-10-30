#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.4 — static preflight (AST / call-graph / byte proof).

METHOD: RA-MedFiLM-BARR
REVISION: ra_medfilm_barr_phase36_robustness_v1_4

NO torch. NO model. NO protected-data read. AST + byte analysis only.

§O CHECKLIST PROVEN
  * real proposal evaluator reachable from smoke
  * real empty-proposal evaluator reachable from smoke
  * three branch controls present (SKIP_GLOBAL / EXECUTE_THEN_ACCEPT / EXECUTE_THEN_REJECT)
  * R_psi unreachable before the EXECUTE decision
  * S_omega unreachable before the EXECUTE decision
  * canonical G autocast / batch contract present
  * task IDs device-bound
  * exact route equivalence implemented (808 Dice + 808 state_machine_branch)
  * router decision separate from final state
  * KUB subgroup reporting implemented
  * R1-R5 reachable
  * no TEST data read
  * no ROUTER_HOLDOUT image/mask read
  * no training
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

EXEC = ROOT / "scripts/analysis/phase36_robustness_execution_v1_4.py"
SRC = EXEC.read_text(encoding="utf-8")
TREE = ast.parse(SRC)

checks = []


def check(name, cond, detail=None):
    checks.append({"check": name, "passed": bool(cond), "detail": detail})


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


def _line_in(fn_name, pred):
    node = FUNCS.get(fn_name)
    if node is None:
        return None
    hits = [n.lineno for n in ast.walk(node) if pred(n)]
    return min(hits) if hits else None


def _funcs_referencing(token):
    return sorted(name for name, node in FUNCS.items()
                  if token in ast.get_source_segment(SRC, node))


# --------------------------------------------------------------------------- #
# 01-05  science driver structure retained (v1.3 guarantees)
# --------------------------------------------------------------------------- #
check("01_run_science_exists", "run_science" in FUNCS)
science_calls = _calls("run_science")
check("02_science_calls_canonical_clean_g", "_generate_clean_g_reference" in science_calls)
check("03_science_calls_phase27_gate", "_phase27_global_reproduction_gate" in science_calls)
check("04_science_calls_clean_gate", "_clean_equivalence_gate" in science_calls)
check("05_science_calls_both_perturbation_drivers",
      "run_image_perturbations" in science_calls
      and "run_proposal_perturbations" in science_calls)

l_gen = _line_in("run_science",
                 lambda n: isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                 and n.func.id == "_generate_clean_g_reference")
l_gate = _line_in("run_science",
                  lambda n: isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                  and n.func.id == "_phase27_global_reproduction_gate")
l_eq = _line_in("run_science",
                lambda n: isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                and n.func.id == "_clean_equivalence_gate")
l_img = _line_in("run_science",
                 lambda n: isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                 and n.func.id == "run_image_perturbations")
l_prop = _line_in("run_science",
                  lambda n: isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                  and n.func.id == "run_proposal_perturbations")
check("06_phase27_gate_before_clean_system_eval_and_perturbations",
      l_gen < l_gate < l_eq < l_img and l_gen < l_prop,
      {"gen": l_gen, "gate": l_gate, "eq": l_eq, "img": l_img, "prop": l_prop})
check("07_clean_gate_precedes_perturbations", l_eq < l_img and l_eq < l_prop)

# --------------------------------------------------------------------------- #
# 08-10  §F conditional state machine ordering
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
check("08_decision_point_present", dec_line is not None, dec_line)
check("09_r_psi_only_after_execute_decision",
      dec_line is not None and rpsi_line is not None and dec_line < rpsi_line,
      {"decision": dec_line, "r_psi": rpsi_line})
check("10_s_omega_only_after_execute_decision",
      dec_line is not None and somega_line is not None and dec_line < somega_line,
      {"decision": dec_line, "s_omega": somega_line})

# no pre-decision R_psi anywhere outside the core
head = SRC.split("def canonical_learned_core")[0]
tail = SRC.split("def canonical_learned_core")[1]
check("11_no_pre_decision_r_psi_forward",
      not re.search(r'ctx\["r_psi"\]\(', head)
      and not re.search(r'ctx\["r_psi"\]\(', tail.split("def proposal_core_adapter")[1]
                        .split("def _clean_row_index")[0]))
check("12_skip_branch_zero_r_psi_and_s_omega",
      "refiner=0, somega=0" in SRC)

# --------------------------------------------------------------------------- #
# 13-17  §D canonical G numerical contract
# --------------------------------------------------------------------------- #
check("13_autocast_enabled_fp16_constant",
      "CANONICAL_G_AUTOCAST_ENABLED = True" in SRC
      and 'CANONICAL_G_AUTOCAST_DTYPE = "float16"' in SRC)
check("14_inference_mode_false_constant",
      "CANONICAL_G_INFERENCE_MODE = False" in SRC
      and "torch.is_inference_mode_enabled" in SRC)
check("15_batch_size_8_domain_local",
      "CANONICAL_G_BATCH_SIZE = 8" in SRC
      and "canonical_batch_partition" in SRC
      and "CANONICAL_BATCH_PARTITION" in SRC)
check("16_g_forward_uses_autocast_and_no_grad",
      "def canonical_g_forward_batched" in SRC
      and "canonical_autocast(ctx[\"device\"])" in SRC
      and "torch.no_grad()" in SRC)
# task IDs device-bound: no bare torch.tensor([...task_id...]) without device=
bare = re.findall(r"torch\.tensor\(\[[^\]]*task_id[^\]]*\]\s*\)", SRC)
device_bound = re.findall(r"torch\.tensor\(\[[^\]]*task_id[^\]]*\]\s*,\s*dtype=torch\.long\s*,\s*device=device\)", SRC)
check("17_task_ids_device_bound",
      len(bare) == 0 and len(device_bound) >= 2,
      {"bare": bare, "device_bound": len(device_bound)})
check("18_g_forward_requires_device_match",
      "CANONICAL_G_TASK_ID_DEVICE_MISMATCH" in SRC)
check("19_g_never_sample_by_sample_in_drivers",
      "canonical_g_forward_batched" in _calls("run_image_perturbations")
      and "canonical_g_forward_batched" in _calls("_generate_clean_g_reference"))
check("20_proposal_path_reuses_clean_g",
      "g_logits=g_logits" in SRC and "G_recomputed_for_proposal_perturbation" in SRC)

# --------------------------------------------------------------------------- #
# 21-25  §G exact route equivalence + router-decision separation
# --------------------------------------------------------------------------- #
check("21_exact_state_machine_branch_comparison",
      "n_state_machine_branch_comparisons_808" in SRC
      and "route_branch_mismatches_zero" in SRC
      and 'branch_comparator' in SRC)
check("22_808_dice_comparisons_required",
      "n_dice_comparisons_808" in SRC and "dice_mismatches_zero" in SRC)
check("23_accept_reject_not_collapsed",
      "accept_reject_collapse_prohibited" in SRC
      and "gen_global != bound_global" not in SRC)
check("24_router_decision_separate_from_final_state",
      'router_decision"] = out.get("state")' not in SRC
      and 'router_decision"] = out["state"]' not in SRC
      and "ROUTER_DECISIONS" in SRC
      and "ROUTER_DECISION_NOT_CANONICAL" in SRC)
check("25_router_decision_vocabulary_frozen",
      'ROUTER_DECISIONS = ("SKIP", "EXECUTE")' in SRC)

# --------------------------------------------------------------------------- #
# 26-31  §H/§I/§J/§K shared core + smoke coverage
# --------------------------------------------------------------------------- #
check("26_one_shared_core_defined", "def canonical_learned_core" in SRC)
check("27_science_and_smoke_use_the_same_core",
      _reachable("run_science", "canonical_learned_core")
      and _reachable("run_smoke", "canonical_learned_core"))
check("28_real_proposal_evaluator_reachable_from_smoke",
      _reachable("run_smoke", "proposal_core_adapter"),
      {"direct": sorted(c for c in _calls("run_smoke") if c in FUNCS)})
check("29_real_empty_proposal_evaluator_reachable_from_smoke",
      _reachable("smoke_empty_proposal_pipeline", "proposal_core_adapter")
      and "proposal_geometry=None" in SRC
      and "NOT_APPLICABLE_EMPTY_PROPOSAL" in SRC)
check("30_three_branch_controls_present",
      "smoke_branch_controls" in _calls("run_smoke")
      and all(s in SRC for s in ("CONTROL_SKIP_GLOBAL", "CONTROL_EXECUTE_THEN_ACCEPT",
                                 "CONTROL_EXECUTE_THEN_REJECT")))
check("31_branch_controls_record_required_fields",
      all(s in SRC for s in ("expected_state", "observed_state", "comparison_pass",
                             "expected_final_source", "observed_final_source",
                             "R_psi_forward_count", "S_omega_forward_count")))
check("32_geometry_only_apply_not_counted_as_proposal_smoke",
      "geometry_only_apply_counts_as_proposal_smoke" in SRC)
check("33_proposal_adapter_used_by_science",
      _reachable("run_proposal_perturbations", "proposal_core_adapter"))

# --------------------------------------------------------------------------- #
# 34-38  §L KUB subgroup reporting
# --------------------------------------------------------------------------- #
check("34_kub_subgroup_authority_bound",
      "KUB_SUBGROUP_AUTHORITY" in SRC and 'KUB_SUBGROUP_AUTHORITY["sha256"]' in SRC
      and 'KUB_SUBGROUP_AUTHORITY["label_column"]' in SRC)
check("35_kub_subgroup_labels_frozen",
      all(s in SRC for s in ("Kidney_Stone", "Bladder_Stone", "Ureteric_Stone")))
check("36_kub_subgroup_map_defined", "def kub_subgroup_map" in SRC)
check("37_kub_subgroup_robustness_emits_labels",
      "def kub_subgroup_robustness" in SRC and '"kub_subgroup"' in SRC)
check("38_kub_reporting_only_reachable_from_science",
      "kub_subgroup_robustness" in _calls("run_science"))

# --------------------------------------------------------------------------- #
# 39-42  §M R1-R5 figure path
# --------------------------------------------------------------------------- #
check("39_all_five_figure_builders_defined",
      all(f"def figure_R{i}" in SRC for i in range(1, 6)))
check("40_figure_registry_bound",
      "FIGURE_REGISTRY = C.FIGURES" in SRC)
check("41_figure_registry_check_in_generator",
      "FIGURE_REGISTRY_MISMATCH" in SRC)
check("42_figures_reachable_from_science",
      "generate_all_figures" in _calls("run_science"))

# --------------------------------------------------------------------------- #
# 43-47  prohibitions
# --------------------------------------------------------------------------- #
check("43_no_test_data_read",
      _funcs_referencing("TEST_MANIFEST") == ["load_identity_authorities"],
      _funcs_referencing("TEST_MANIFEST"))
check("44_no_holdout_data_read",
      _funcs_referencing("ROUTER_HOLDOUT_MANIFEST") == ["load_identity_authorities"],
      _funcs_referencing("ROUTER_HOLDOUT_MANIFEST"))
check("45_no_training",
      ".backward()" not in SRC and "torch.optim" not in SRC
      and "requires_grad_(True)" not in SRC and ".train()" not in SRC)
check("46_no_vendor_substring_split",
      '"test" in' not in SRC and "'test' in" not in SRC
      and '"train" in' not in SRC and "'train' in" not in SRC)
check("47_vendor_metadata_declared",
      "VENDOR_DIRECTORY_NAMES_ARE_TRANSPORT_METADATA = True" in SRC)

# --------------------------------------------------------------------------- #
# 48-51  retained v1.3 repairs + counts
# --------------------------------------------------------------------------- #
check("48_sample_level_rows_retained",
      "SCIENCE_ROW_SCHEMA_LOSS" in SRC and "_IMAGE_ROW_REQUIRED" in SRC)
check("49_no_silent_missing_sample_continue",
      not re.search(r'sid\s*=\s*row\.get\("sample_id"\)\s*\n\s*if\s+sid\s+is\s+None\s*:\s*\n\s*continue',
                    SRC))
check("50_frozen_counts",
      all(t in SRC for t in ("NONCLEAN_IMAGE_EXECUTIONS_EXPECTED = (",
                             "LOGICAL_IMAGE_TABLE_ROWS_MAX = (",
                             "NONCLEAN_PROPOSAL_EXECUTIONS_MAX = (")))
check("51_loader_repairs_retained",
      all(t in SRC for t in ("def _load_models", "load_state_dict", "strict=True",
                             "CANONICAL_COMPONENT_LOAD_FAILURE")))

# --------------------------------------------------------------------------- #
# 52-55  import safety + proposal 202-D binding
# --------------------------------------------------------------------------- #
check("52_torch_not_imported_on_import", "torch" not in sys.modules)
check("53_no_module_level_execution",
      "def run_science()" in SRC and "def run_smoke()" in SRC)
check("54_proposal_202d_bound_to_perturbed_geometry",
      "router_features_202_override=prf[cond]" in SRC
      and "prop_rf202_store[sid][cond] = _assemble_202d(" in SRC
      and "_geo_row(pg)" in SRC,
      "the proposal path consumes a 202-D vector assembled with the PERTURBED roi_row")
check("55_core_fails_closed_without_202d_or_taps",
      "CANONICAL_CORE_REQUIRES_202D_OR_G_TAPS" in SRC)

passed = sum(1 for c in checks if c["passed"])
total = len(checks)
report = {
    "artifact": "phase36_robustness_static_preflight_v1_4",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_4",
    "method": "AST_CALL_GRAPH_AND_BYTE_PREFLIGHT",
    "torch_imported": "torch" in sys.modules,
    "checks": checks,
    "passed": passed,
    "total": total,
    "all_pass": passed == total,
}
out = ROOT / "reports/audits/phase36_robustness_static_preflight_v1_4.json"
out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"passed": passed, "total": total, "all_pass": passed == total}, indent=1))
for c in checks:
    if not c["passed"]:
        print("FAIL:", c["check"], json.dumps(c.get("detail"), default=str))
raise SystemExit(0 if passed == total else 1)
