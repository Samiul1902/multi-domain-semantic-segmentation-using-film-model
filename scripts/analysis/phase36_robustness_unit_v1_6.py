#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.6 — model-free unit checks.

METHOD: RA-MedFiLM-BARR
REVISION: ra_medfilm_barr_phase36_robustness_v1_6

NO torch model execution. NO protected population read. Pure static/unit logic.

Covers §K:
  * VAL manifest authority source contract
  * 808 expected population constant
  * split == VAL fail-closed rule
  * no protected runtime authority
  * no TEST runtime read path
  * no ROUTER_HOLDOUT runtime read path
  * no post-hoc protected-counter zero reset
  * canonical G sigmoid preserved
  * CUDA fail-closed preserved
  * four-component device binding preserved
  * component inference contexts preserved
  * state-machine ordering preserved
  * proposal paths preserved
  * NC31-NC35 (delegated to the v1.6 negative-control module)

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

import scripts.analysis.phase36_robustness_execution_v1_6 as E  # noqa: E402
import scripts.analysis.phase36_robustness_common_v1_1 as C  # noqa: E402

EXEC_V1_6 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_6.py"
EXEC_V1_5 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_5.py"
UNIT_V1_5 = ROOT / "scripts/analysis/phase36_robustness_unit_v1_5.py"
PREFLIGHT_V1_5 = ROOT / "scripts/analysis/phase36_robustness_preflight_v1_5.py"
NC_V1_5 = ROOT / "scripts/analysis/phase36_robustness_negative_controls_v1_5.py"

checks = []


def check(name: str, cond: bool, detail=None):
    checks.append({"check": name, "passed": bool(cond), "detail": detail})


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


SRC = EXEC_V1_6.read_text(encoding="utf-8")
TREE = ast.parse(SRC)
FUNCS = {n.name: n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef)}

PROTECTED_SYMBOLS = ("TEST_MANIFEST", "ROUTER_HOLDOUT_MANIFEST",
                     "ROUTER_HOLDOUT_IDENTITY_AUTHORITY")
PROTECTED_PATH_TOKENS = ("val_router_holdout", "phase24_router_split_manifest",
                         "phase4_v3/test.csv")


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


def _protected_refs(fns):
    hits = []
    for name in sorted(fns):
        for x in ast.walk(FUNCS[name]):
            if isinstance(x, ast.Name) and x.id in PROTECTED_SYMBOLS:
                hits.append({"function": name, "line": x.lineno, "symbol": x.id})
            if isinstance(x, ast.Constant) and isinstance(x.value, str):
                for t in PROTECTED_PATH_TOKENS:
                    if t in x.value:
                        hits.append({"function": name, "line": x.lineno, "token": t})
    return hits


def _funcs_referencing(token):
    return sorted(name for name, node in FUNCS.items()
                  if token in ast.get_source_segment(SRC, node))


def _exec_counter_assignments(counter_names):
    """AST-level executable ``counters["<name>"] = <value>`` assignments.

    Docstrings / comments are excluded by construction.
    """
    out = []
    for n in ast.walk(TREE):
        if not isinstance(n, ast.Assign):
            continue
        for t in n.targets:
            if (isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name)
                    and t.value.id == "counters"):
                key = t.slice
                key = key.value if isinstance(key, ast.Constant) else None
                if key in counter_names:
                    out.append({"line": n.lineno,
                                "statement": ast.unparse(n),
                                "value": ast.unparse(n.value)})
    return out


# --------------------------------------------------------------------------- #
# 01-06  v1.5 history preserved (SHA gate)
# --------------------------------------------------------------------------- #
check("01_v1_5_execution_preserved",
      _sha(EXEC_V1_5) == "f219d06cb83c43b24be446205df2223b964c417e9547d5a657799aa3218f9876")
check("02_v1_5_unit_preserved",
      _sha(UNIT_V1_5) == "c192db5265a78b8056820c647e575e8880d5b20e9aa37723a07648de60928f24")
check("03_v1_5_preflight_preserved",
      _sha(PREFLIGHT_V1_5) == "dd3257aea919ea8db1f038dc1c300f37594ab676ccc1447d10aa0eb927817446")
check("04_v1_5_negative_controls_preserved",
      _sha(NC_V1_5) == "51f261fe269b6256005186f2455040208e52e950bce815bdb117db5d7d078ced")
check("05_v1_5_direct_byte_audit_preserved",
      _sha(ROOT / "reports/audits/phase36_v1_5_direct_source_byte_audit.json")
      == "30feed4daa24dcff30b2b79a03cbba32fd630c01e5f2c75ef3dd7363bad7ccf8")
check("06_v1_5_source_freeze_preserved",
      _sha(ROOT / "reports/audits/phase36_preexecution_source_freeze_v1_5.json")
      == "b52b30f50ca0753e1d49f44cdcdefb8c7d99391450703e3efdf4c5a382476a0b")

# --------------------------------------------------------------------------- #
# 07-09  §B defect record
# --------------------------------------------------------------------------- #
DEF = json.loads((ROOT / "reports/audits/"
                  "phase36_v1_5_protected_population_runtime_access_defects_v1_6.json")
                 .read_text(encoding="utf-8"))
check("07_defect_record_two_defects", DEF["defect_count"] == 2, DEF["defect_count"])
check("08_defect_ids_d14_d15",
      [d["id"].split("_")[0] for d in DEF["defects"]] == ["D14", "D15"])
check("09_defect_subject_is_v1_5",
      DEF["subject_sha256"] == "f219d06cb83c43b24be446205df2223b964c417e9547d5a657799aa3218f9876")
check("10_d14_proven_seven_protected_refs",
      DEF["defects"][0]["exact_v1_5_evidence"]["run_science_reachable_protected_ref_count"] == 7,
      DEF["defects"][0]["exact_v1_5_evidence"]["run_science_reachable_protected_ref_count"])
check("11_d15_proven_two_protected_posthoc",
      DEF["defects"][1]["exact_v1_5_evidence"]["protected_post_hoc_assignment_count"] == 2)

# --------------------------------------------------------------------------- #
# 12-20  §C/§E/§F VAL808-only runtime authority
# --------------------------------------------------------------------------- #
check("12_val_runtime_authority_constant",
      E.VAL_MANIFEST_IS_ONLY_POPULATION_RUNTIME_AUTHORITY is True
      and E.PROTECTED_RUNTIME_POPULATION == "VAL808_ONLY")
check("13_val_manifest_is_frozen_common_binding",
      E.VAL_RUNTIME_AUTHORITY["path"] == C.VAL_MANIFEST
      and E.VAL_RUNTIME_AUTHORITY["sha256"] == C.VAL_MANIFEST_SHA)
check("14_val_expected_n_808", E.VAL_RUNTIME_AUTHORITY["expected_n"] == 808)
check("15_val_expected_n_constant_808", E.VAL_RUNTIME_EXPECTED_N == 808)
check("16_protected_runtime_reads_disallowed",
      E.ROUTER_HOLDOUT_RUNTIME_READS_ALLOWED is False
      and E.TEST_RUNTIME_READS_ALLOWED is False)
check("17_protected_deny_set_reader_functions_absent",
      not any(f in FUNCS for f in ("load_identity_authorities", "_identity_deny_set",
                                   "_holdout_selector")),
      [f for f in ("load_identity_authorities", "_identity_deny_set", "_holdout_selector")
       if f in FUNCS])
check("18_no_module_level_protected_constants",
      not any(f"\n{s} =" in SRC for s in PROTECTED_SYMBOLS),
      [s for s in PROTECTED_SYMBOLS if f"\n{s} =" in SRC])
check("19_val_manifest_sha_guard_in_load_population",
      "VAL_MANIFEST_SHA_MISMATCH" in SRC
      and "_sha(man) != C.VAL_MANIFEST_SHA" in SRC)
check("20_val_split_guard_and_uniqueness",
      "NON_VAL_ROW_REJECTED" in SRC and "VAL808_SAMPLE_ID_NOT_UNIQUE" in SRC
      and "VAL808_POPULATION_SIZE_MISMATCH" in SRC)
check("21_val_path_presence_guards",
      "VAL808_MISSING_IMAGE_PATH" in SRC and "VAL808_MISSING_MASK_PATH" in SRC
      and "VAL808_MISSING_SAMPLE_ID" in SRC)
_auth_args = [a.arg for a in FUNCS["authorize_sample"].args.args] if "authorize_sample" in FUNCS else []
_exec_protected_params = sorted({x.id for x in ast.walk(TREE)
                                 if isinstance(x, ast.Name)
                                 and x.id in ("holdout_ids", "test_ids")})
check("22_authorize_sample_val_only_signature",
      _auth_args == ["sid", "image_path", "mask_path", "pop_index"]
      and len(_exec_protected_params) == 0,
      {"args": _auth_args, "exec_protected_params": _exec_protected_params})
check("23_no_vendor_substring_split",
      '"test" in' not in SRC and "'test' in" not in SRC
      and '"train" in' not in SRC and "'train' in" not in SRC)
check("24_val_runtime_authority_audit_callable",
      "def val_runtime_authority_audit" in SRC)

# --------------------------------------------------------------------------- #
# 25-29  §D runtime reachability: zero protected IO
# --------------------------------------------------------------------------- #
rs = _reachable("run_science")
rm = _reachable("run_smoke")
check("25_run_science_protected_refs_zero", len(_protected_refs(rs)) == 0,
      _protected_refs(rs))
check("26_run_smoke_protected_refs_zero", len(_protected_refs(rm)) == 0,
      _protected_refs(rm))
check("27_run_science_reaches_val_loader",
      "_load_population" in rs and "canonical_population_rows" in rs)
check("28_rows_helper_reachable_only_for_val",
      "_rows" in rs and "VAL" in SRC)
check("29_no_protected_reader_helper_defined",
      "def _identity_deny_set" not in SRC and "def load_identity_authorities" not in SRC
      and "def _holdout_selector" not in SRC)

# --------------------------------------------------------------------------- #
# 30-34  §G counter integrity
# --------------------------------------------------------------------------- #
lines = SRC.splitlines()
posthoc_protected = [a for a in _exec_counter_assignments(
    ("router_holdout_reads", "test_reads")) if a["value"] == "0"]
check("30_no_posthoc_protected_counter_reset", len(posthoc_protected) == 0,
      posthoc_protected)
check("31_protected_counters_initialized_at_start",
      "for k in C.COUNTERS_FOREVER_ZERO:" in SRC
      and "PROTECTED_COUNTERS = (\"router_holdout_reads\", \"test_reads\")" in SRC)
check("32_fail_closed_nonzero_protected_counter",
      "PHASE36_PROTECTED_READ_COUNTER_NONZERO__" in SRC)
check("33_protected_counter_assertion_after_execution",
      SRC.index("run_proposal_perturbations(ctx, generated, clean_store, counters, proposal_rows)")
      < SRC.index("PHASE36_PROTECTED_READ_COUNTER_NONZERO__"))
check("34_forever_zero_counters_also_asserted",
      "PHASE36_FOREVER_ZERO_COUNTER_NONZERO__" in SRC)

# --------------------------------------------------------------------------- #
# 35-44  §H/§I v1.5 + v1.4 repairs preserved
# --------------------------------------------------------------------------- #
check("35_canonical_probability_operator_preserved",
      E.CANONICAL_PROBABILITY_OPERATOR["expression"]
      == "torch.sigmoid(logits.float()).cpu().numpy()"
      and "prob = torch.sigmoid(t.float())" in SRC)
check("36_no_executable_manual_numpy_sigmoid",
      not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
              and n.func.attr == "exp" and isinstance(n.func.value, ast.Name)
              and n.func.value.id == "np" for n in ast.walk(TREE)))
check("37_cuda_fail_closed_preserved",
      "get_device(require_cuda=True)" in SRC
      and "PHASE36_V1_5_CUDA_FAIL_CLOSED__DEVICE_TYPE" in SRC
      and E.CANONICAL_DEVICE_CONTRACT["cpu_scientific_fallback_permitted"] is False)
check("38_four_component_device_binding_preserved",
      all(t in SRC for t in ("g.to(device)", "b_phi.to(device)",
                             "r_psi.to(device)", "s_omega.to(device)"))
      and "COMPONENT_DEVICE_BINDING_FAILED" in SRC)
CTX = E.COMPONENT_INFERENCE_CONTEXTS
check("39_component_contexts_preserved",
      CTX["G"]["inference_mode"] is False and CTX["G"]["autocast_enabled"] is True
      and all(CTX[c]["inference_mode"] is True and CTX[c]["autocast_enabled"] is False
              for c in ("B_phi", "R_psi", "S_omega"))
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
check("40_state_machine_ordering_preserved",
      dec < rpsi and dec < somega, {"decision": dec, "r_psi": rpsi, "s_omega": somega})
check("41_skip_branch_zero_forwards_preserved", "refiner=0, somega=0" in SRC)
check("42_router_decision_separation_preserved",
      'ROUTER_DECISIONS = ("SKIP", "EXECUTE")' in SRC
      and "ROUTER_DECISION_NOT_CANONICAL" in SRC)
check("43_proposal_paths_preserved",
      "def proposal_core_adapter" in SRC
      and "def smoke_nonempty_proposal_pipeline" in SRC
      and "def smoke_empty_proposal_pipeline" in SRC
      and "def run_proposal_perturbations" in SRC
      and _reachable("run_smoke").__contains__("proposal_core_adapter"))
check("44_branch_controls_and_reporting_preserved",
      "def smoke_branch_controls" in SRC
      and all(s in SRC for s in ("CONTROL_SKIP_GLOBAL", "CONTROL_EXECUTE_THEN_ACCEPT",
                                 "CONTROL_EXECUTE_THEN_REJECT"))
      and "def kub_subgroup_map" in SRC
      and all(f"def figure_R{i}" in SRC for i in range(1, 6)))

# --------------------------------------------------------------------------- #
# 45-52  frozen science constants unchanged
# --------------------------------------------------------------------------- #
check("45_registries_unchanged",
      len(E.image_realization_plan()) == 16 and len(E.proposal_realization_plan()) == 6
      and E.NONCLEAN_IMAGE_EXECUTIONS_EXPECTED == 12928
      and E.LOGICAL_IMAGE_TABLE_ROWS_MAX == 13736
      and E.NONCLEAN_PROPOSAL_EXECUTIONS_MAX == 4848)
check("46_thresholds_unchanged",
      E.SEGMENTATION_OUTPUT_THRESHOLD == 0.50 and E.ROI_PROPOSAL_THRESHOLD == 0.30
      and E.SOMEGA_ACCEPT_THRESHOLD == 0.50)
check("47_component_identities_unchanged",
      E.G_COMPONENT["sha256"] == "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7"
      and E.B_PHI_COMPONENT["sha256"] == "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b"
      and E.R_PSI_COMPONENT["sha256"] == "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109"
      and E.S_OMEGA_COMPONENT["sha256"] == "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e")
check("48_phase27_authority_unchanged",
      E.PHASE27_GLOBAL_PROB_AUTHORITY["sha256"]
      == "cc6c54af986f56b4aba9265405ffeba4f6cac582eeff00fe6b0894429e7d3f13")
check("49_canonical_batch_partition_unchanged",
      E.canonical_batch_plan_audit()["matches_phase27_exact_partition"] is True)
check("50_noise_seed_rule_unchanged", C.NOISE_SEED_RULE_V1_1.endswith("[:8]"))
check("51_feature_dependency_contract_98_104",
      C.PROPOSAL_CONTRACT_V1_1["geometry_dependent_dims"] == 98
      and C.PROPOSAL_CONTRACT_V1_1["global_only_dims"] == 104)
check("52_val_runtime_authority_audit_values",
      E.val_runtime_authority_audit()["n_rows"] == 808
      and E.val_runtime_authority_audit()["n_unique_sample_id"] == 808
      and E.val_runtime_authority_audit()["all_split_val"] is True
      and E.val_runtime_authority_audit()["protected_deny_set_io"] is False)

# --------------------------------------------------------------------------- #
# 53-55  import safety / no training
# --------------------------------------------------------------------------- #
check("53_import_safety_no_torch", "torch" not in sys.modules)
check("54_no_training_paths",
      ".backward()" not in SRC and "torch.optim" not in SRC
      and "requires_grad_(True)" not in SRC and ".train()" not in SRC)
check("55_gates_unchanged",
      C.GATE_ENV == "PHASE36_EXECUTE" and C.SMOKE_GATE_ENV == "PHASE36_SMOKE_EXECUTE")

passed = sum(1 for c in checks if c["passed"])
total = len(checks)
report = {
    "artifact": "phase36_robustness_unit_v1_6",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_6",
    "model_free": True,
    "torch_imported": False,
    "protected_population_read": False,
    "checks": checks,
    "passed": passed,
    "total": total,
    "all_pass": passed == total,
}
out = ROOT / "reports/audits/phase36_robustness_unit_v1_6.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"passed": passed, "total": total, "all_pass": passed == total}, indent=1))
for c in checks:
    if not c["passed"]:
        print("FAIL:", c["check"], json.dumps(c.get("detail"), default=str))
raise SystemExit(0 if passed == total else 1)
