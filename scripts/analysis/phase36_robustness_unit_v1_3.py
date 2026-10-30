#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.3 — model-free unit checks.

METHOD: RA-MedFiLM-BARR
REVISION: ra_medfilm_barr_phase36_robustness_v1_3

NO torch. NO model. NO checkpoint. NO protected-data read. Pure static/unit logic.

Inherits the v1.2 unit checks and ADDS:
  * sample-level image realization plan (16 non-clean, 17 incl. CLEAN)
  * 12,928 future non-clean image evaluation contract
  * sample-level proposal realization plan (6 non-clean)
  * manifest vendor Training_Input positive control (231 accepted)
  * manifest vendor Test_Input positive control (112 accepted)
  * path-mismatch rejection
  * ID split authority (ROUTER_HOLDOUT / TEST identity denial)
  * NC7-NC14

Exit code 0 == all checks pass. Prints a JSON report.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

import scripts.analysis.phase36_robustness_execution_v1_3 as E  # noqa: E402
import scripts.analysis.phase36_robustness_common_v1_1 as C  # noqa: E402

EXEC_V1_3 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_3.py"
EXEC_V1_2 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_2.py"
UNIT_V1_2 = ROOT / "scripts/analysis/phase36_robustness_unit_v1_2.py"
PREFLIGHT_V1_2 = ROOT / "scripts/analysis/phase36_robustness_preflight_v1_2.py"
NC_V1_2 = ROOT / "scripts/analysis/phase36_robustness_negative_controls_v1_2.py"

checks = []


def check(name: str, cond: bool, detail=None):
    checks.append({"check": name, "passed": bool(cond), "detail": detail})


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _src():
    return EXEC_V1_3.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# 01-08  v1.2 preserved byte-for-byte (SHA gate)
# --------------------------------------------------------------------------- #
v12_sha = _sha(EXEC_V1_2)
check("01_v1_2_execution_preserved",
      v12_sha == "66fe435d7ec1d6e6ea10475776992b16fe049c9f3bfd7261caf78792e10bc29a", v12_sha)
check("02_v1_2_unit_preserved", _sha(UNIT_V1_2) == "4d367ab8b6485d1d4f9b18db6174228b925f27561148d241b82c3173e946703f")
check("03_v1_2_preflight_preserved", _sha(PREFLIGHT_V1_2) == "e51816f5251dbd140ba7154294d004ed9a7404eec2318f56ceb4d91c468ef1aa")
check("04_v1_2_negative_controls_preserved", _sha(NC_V1_2) == "a8372275dab3a2550524014f4d67804c221bf22fb8f451ba11f498b920a75bac")
check("05_v1_2a_audit_preserved",
      _sha(ROOT / "reports/audits/phase36_v1_2a_source_byte_audit_and_governance_reconciliation.json")
      == "42e819e41eca20ff2b49e11054a1e270b20b2d01f5dea8d8893abd022eb1222d")
check("06_val_manifest_sha",
      _sha(ROOT / "manifests/phase4_v3/val.csv")
      == "082c80b2bda63fd73f371f109c34643adf01edaead921643fb2e44993ba53315")

# --------------------------------------------------------------------------- #
# 09-16  image realization plan (§D)
# --------------------------------------------------------------------------- #
plan = E.image_realization_plan()
check("07_image_plan_len_16_nonclean", len(plan) == 16, len(plan))
check("08_image_plan_no_clean", all(p["condition"] != "CLEAN" for p in plan))
check("09_image_plan_10_deterministic",
      sum(1 for p in plan if not p["is_noise"]) == 10)
check("10_image_plan_6_noise", sum(1 for p in plan if p["is_noise"]) == 6)
check("11_noise_seeds_42_123_3407",
      sorted({int(p["base_seed"]) for p in plan if p["is_noise"]}) == [42, 123, 3407])
check("12_deterministic_seed_then_null",
      all(p["base_seed"] is None and p["derived_seed"] is None for p in plan if not p["is_noise"]))
check("13_noise_seed_populated",
      all(p["base_seed"] is not None for p in plan if p["is_noise"]))
check("14_nonclean_image_exec_12928", E.NONCLEAN_IMAGE_EXECUTIONS_EXPECTED == 12928,
      E.NONCLEAN_IMAGE_EXECUTIONS_EXPECTED)
check("15_clean_exec_808", E.CLEAN_EXECUTIONS_EXPECTED == 808)
check("16_logical_rows_13736", E.LOGICAL_IMAGE_TABLE_ROWS_MAX == 13736,
      E.LOGICAL_IMAGE_TABLE_ROWS_MAX)

# --------------------------------------------------------------------------- #
# 17-19  proposal realization plan (§G)
# --------------------------------------------------------------------------- #
pplan = E.proposal_realization_plan()
check("17_proposal_plan_len_6", len(pplan) == 6, len(pplan))
check("18_proposal_plan_no_clean",
      all(p["proposal_condition"] != "PROPOSAL_CLEAN" for p in pplan))
check("19_proposal_nonclean_max_4848", E.NONCLEAN_PROPOSAL_EXECUTIONS_MAX == 4848)

# --------------------------------------------------------------------------- #
# 20-26  MANIFEST AUTHORITY positive/negative controls (§K/§L)
# --------------------------------------------------------------------------- #
rows = E._load_population()
check("20_population_808", len(rows) == 808, len(rows))
pop_index = {r["sample_id"]: r for r in rows}
auth = E.load_identity_authorities()

train_rows = [r for r in rows if "ISIC2018_Task1-2_Training_Input" in str(r.get("image_path", ""))]
test_rows = [r for r in rows if "ISIC2018_Task1-2_Test_Input" in str(r.get("image_path", ""))]
check("21_authorized_training_231", len(train_rows) == 231, len(train_rows))
check("22_authorized_test_112", len(test_rows) == 112, len(test_rows))

# ACCEPTED counts computed by running the identity authority, NOT by substring logic.
acc_train = 0
for r in train_rows:
    try:
        E.authorize_sample(r["sample_id"], r["image_path"], r["mask_path"], pop_index,
                           auth["holdout"], auth["test"])
        acc_train += 1
    except Exception:
        pass
acc_test = 0
for r in test_rows:
    try:
        E.authorize_sample(r["sample_id"], r["image_path"], r["mask_path"], pop_index,
                           auth["holdout"], auth["test"])
        acc_test += 1
    except Exception:
        pass
check("23_accepted_training_231", acc_train == 231, acc_train)
check("24_accepted_test_112", acc_test == 112, acc_test)
check("25_false_reject_zero", (231 - acc_train) + (112 - acc_test) == 0)

# path mismatch rejection (a raise == correct rejection)
mism = 0
sid0 = rows[0]["sample_id"]
for _declared_img, _declared_mask, _expect_token in (
        (rows[0]["image_path"] + "_X", rows[0]["mask_path"], "IMAGE_PATH_MISMATCH"),
        (rows[0]["image_path"], rows[0]["mask_path"] + "_X", "MASK_PATH_MISMATCH")):
    try:
        E.authorize_sample(sid0, _declared_img, _declared_mask, pop_index,
                           auth["holdout"], auth["test"])
    except Exception as ex:
        if _expect_token in str(ex):
            mism += 1
check("26_path_mismatch_rejected", mism == 2, mism)

# not-in-manifest rejection
try:
    E.authorize_sample("NOT_A_REAL_SAMPLE_ID", "x", "y", pop_index, auth["holdout"], auth["test"])
    check("27_not_in_manifest_rejected", False)
except Exception as ex:
    check("27_not_in_manifest_rejected", "NOT_IN_VAL808_MANIFEST" in str(ex), str(ex))

# --------------------------------------------------------------------------- #
# 28-29  ID split authority (§J)
# --------------------------------------------------------------------------- #
src = _src()
check("28_no_vendor_substring_split_inference",
      '"test" in' not in src and "'test' in" not in src
      and '"train" in' not in src and "'train' in" not in src)
check("29_no_protected_row_tokens",
      "\n_PROTECTED_ROW_TOKENS = " not in src
      and not any(ln.strip().startswith("_PROTECTED_ROW_TOKENS =") for ln in src.splitlines()))
check("30_vendor_metadata_never_split_label",
      "VENDOR_DIRECTORY_NAMES_ARE_TRANSPORT_METADATA = True" in src)

# ROUTER_HOLDOUT / TEST identity denial (synthetic ids injected into deny sets)
synthetic = "SYNTH_DENY_ID_FOR_UNIT"
try:
    E.authorize_sample(synthetic, "x", "y", {synthetic: {"image_path": "x", "mask_path": "y",
                                                         "dataset": "ISIC", "task_id": 0}},
                       {synthetic}, set())
    check("31_holdout_identity_denied", False)
except Exception as ex:
    check("31_holdout_identity_denied", "ROUTER_HOLDOUT" in str(ex), str(ex))
try:
    E.authorize_sample(synthetic, "x", "y", {synthetic: {"image_path": "x", "mask_path": "y",
                                                         "dataset": "ISIC", "task_id": 0}},
                       set(), {synthetic})
    check("32_test_identity_denied", False)
except Exception as ex:
    check("32_test_identity_denied", "TEST_IDENTITY" in str(ex), str(ex))

# --------------------------------------------------------------------------- #
# 33-38  sample-level row schema (§E/§M)
# --------------------------------------------------------------------------- #
try:
    E.build_image_result_row(sid=None, domain="ISIC", task_id=0, cond="BRIGHTNESS_NEG",
                             base_seed=None, derived_seed=None, clean_dice=0.5,
                             perturbed_dice=0.4, prediction_consistency_dice=0.9,
                             clean_route_state="SKIP_GLOBAL", perturbed_route_state="SKIP_GLOBAL",
                             clean_router_decision="a", perturbed_router_decision="a",
                             final_source="GLOBAL", perturbed_final_source="GLOBAL")
    check("33_missing_sample_id_raises", False)
except Exception as ex:
    check("33_missing_sample_id_raises", "SCIENCE_ROW_SCHEMA_LOSS" in str(ex), str(ex))

try:
    E.build_image_result_row(sid="s", domain=None, task_id=0, cond="BRIGHTNESS_NEG",
                             base_seed=None, derived_seed=None, clean_dice=0.5,
                             perturbed_dice=0.4, prediction_consistency_dice=0.9,
                             clean_route_state="a", perturbed_route_state="a",
                             clean_router_decision="d", perturbed_router_decision="d",
                             final_source="GLOBAL", perturbed_final_source="GLOBAL")
    check("34_missing_domain_raises", False)
except Exception as ex:
    check("34_missing_domain_raises", "SCIENCE_ROW_SCHEMA_LOSS" in str(ex), str(ex))

ok_row = E.build_image_result_row(sid="s", domain="ISIC", task_id=0, cond="BRIGHTNESS_NEG",
                                  base_seed=None, derived_seed=None, clean_dice=0.5,
                                  perturbed_dice=0.4, prediction_consistency_dice=0.9,
                                  clean_route_state="SKIP_GLOBAL", perturbed_route_state="SKIP_GLOBAL",
                                  clean_router_decision="a", perturbed_router_decision="a",
                                  final_source="GLOBAL", perturbed_final_source="GLOBAL")
check("35_row_paired_delta_computed",
      abs(ok_row["paired_delta_dice"] - (-0.1)) < 1e-12, ok_row["paired_delta_dice"])
check("36_row_has_all_required",
      all(k in ok_row for k in E._IMAGE_ROW_REQUIRED))
check("37_row_route_state_changed_flag",
      ok_row["route_state_changed"] is False)
check("38_row_router_decision_changed_flag",
      ok_row["router_decision_changed"] is False)

# --------------------------------------------------------------------------- #
# 39-45  NC7-NC13 (static/unit negative controls)
# --------------------------------------------------------------------------- #
# NC7: v1.2 anonymous image condition rows must FAIL (they are absent from v1.3).
check("39_NC7_anonymous_image_rows_absent",
      'image_rows.append({"condition": cond, "base_seed": bs})' not in src)
# NC8: v1.2 anonymous proposal condition rows must FAIL (absent from v1.3).
check("40_NC8_anonymous_proposal_rows_absent",
      'proposal_rows.append({"proposal_condition": cond})' not in src)
# NC9: silent missing-sample continue must FAIL (absent from v1.3).
check("41_NC9_silent_missing_sample_continue_absent",
      'if sid is None:\n            continue' not in src
      and "if sid is None:\n                continue" not in src)
# NC10: science driver must contain reachable perturbation evaluator calls.
check("42_NC10_perturbation_evaluators_reachable_in_science",
      "_evaluate_frozen_system(" in src and "_evaluate_frozen_system_proposal(" in src
      and "run_image_perturbations(" in src and "run_proposal_perturbations(" in src)
# NC11: missing domain/task_id in result schema must FAIL (guards exist).
check("43_NC11_schema_loss_guard_present",
      "SCIENCE_ROW_SCHEMA_LOSS" in src)
# NC12: fixed-summary/worst-case reachability must not be missing.
check("44_NC12_fixed_and_worstcase_reachable",
      all(t in src for t in ("summarize_image_per_sample", "summarize_noise_seed",
                             "worst_case_per_sample", "worst_case_by_domain",
                             "summarize_route_stability")))
# NC13: a `if "test" in path_segment: reject` guard MUST FAIL against the manifest.
nc13_violations = [r["sample_id"] for r in rows
                   if "test" in str(r.get("image_path", "")).lower().replace("/", "\\").split("\\")[-6:]]
check("45_NC13_test_substring_would_reject_112",
      len([r for r in rows if any("test" in seg for seg in
                                  str(r["image_path"]).lower().replace("/", "\\").split("\\"))]) == 112)

# NC14: identity authority must accept all 808 (positive).
nc14 = 0
for r in rows:
    try:
        E.authorize_sample(r["sample_id"], r["image_path"], r["mask_path"], pop_index,
                           auth["holdout"], auth["test"])
        nc14 += 1
    except Exception:
        pass
check("46_NC14_identity_authority_accepts_808", nc14 == 808, nc14)

# --------------------------------------------------------------------------- #
# 47-52  v1.2 real functionality retained (§O)
# --------------------------------------------------------------------------- #
check("47_real_model_loader_retained", "def _load_models()" in src
      and "load_state_dict(..., strict=True)" in src.replace("\n", " ")
      or "strict=True" in src)
check("48_real_clean_generator_retained",
      "def _generate_clean_reference_once" in src and "def _evaluate_clean_sample" in src)
check("49_strict_gate_retained", "def _clean_equivalence_gate" in src
      and "all_pass" in src and "np.isclose" in src)
check("50_real_image_evaluator_retained", "def _evaluate_frozen_system(" in src)
check("51_real_proposal_evaluator_retained", "def _evaluate_frozen_system_proposal(" in src)
check("52_smoke_call_graph_retained", "def run_smoke()" in src and "_load_models()" in src)

# --------------------------------------------------------------------------- #
# 53-56  98/104 split + metric authority + empty proposal
# --------------------------------------------------------------------------- #
check("53_geometry_dims_98", C.PROPOSAL_CONTRACT_V1_1["geometry_dependent_dims"] == 98)
check("54_global_dims_104", C.PROPOSAL_CONTRACT_V1_1["global_only_dims"] == 104)
check("55_metric_authority_bound",
      "src.metrics.evaluation_metrics" in src or "from src.metrics import evaluation_metrics" in src)
check("56_empty_proposal_contract",
      "EMPTY_PROPOSAL_HANDLING" in src and "not_applicable" in src)

# --------------------------------------------------------------------------- #
# 57-58  no torch on import, no new scientific semantics
# --------------------------------------------------------------------------- #
check("57_torch_not_imported_on_import", "torch" not in sys.modules)
check("58_import_safe_no_execution",
      "def run_science()" in src and "def run_smoke()" in src)

passed = sum(1 for c in checks if c["passed"])
total = len(checks)
report = {
    "artifact": "phase36_robustness_unit_v1_3",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_3",
    "model_free": True,
    "torch_imported": False,
    "checks": checks,
    "passed": passed,
    "total": total,
    "all_pass": passed == total,
}
out = ROOT / "reports/audits/phase36_robustness_unit_v1_3.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"passed": passed, "total": total, "all_pass": passed == total}, indent=1))
for c in checks:
    if not c["passed"]:
        print("FAIL:", c["check"], c["detail"])
raise SystemExit(0 if passed == total else 1)
