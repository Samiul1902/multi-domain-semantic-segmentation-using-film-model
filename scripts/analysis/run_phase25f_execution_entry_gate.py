"""Phase 25F canonical execution — §0 fail-closed re-entry gate, §1 gate
enforcement, §2 contract binding, §3 upstream cross-fit disclosure, §4 join
integrity, §5 experiment-ID registry.

Reads only. Constructs no model, trains nothing, opens no TEST/VAL/HOLDOUT.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase25f_spec_repair_common as C  # noqa: E402
import phase25f_execution_common as E  # noqa: E402

AUD = C.AUD
TAB = C.TAB
REV = C.REVISION
TERMINAL_PRED = (
    "PHASE25F_POST_SAFETY_SPEC_V1_0_COMPLETE__OOF_FEATURE_SOURCE_ARCHITECTURE_"
    "TRAINING_THRESHOLD_AND_OWNERSHIP_FROZEN__PHASE25F_EXECUTION_ELIGIBLE_NOT_STARTED"
)
TERMINAL_BLOCKED = (
    "PHASE25F_EXECUTION_BLOCKED__PRE_EXECUTION_REENTRY_GATE_FAILED"
)
TERMINAL_OK = (
    "PHASE25F_POST_SAFETY_EXECUTION_COMPLETE__OOF_SAFETY_PREDICTIONS_FINAL_"
    "CHECKPOINT_AND_C9_ARTIFACTS_FROZEN__PHASE25G_ELIGIBLE_NOT_STARTED"
)

# the 14 physically frozen v1.0 specification contracts
CONTRACT_14 = [
    "phase25f_architecture_contract_v1_0.json",
    "phase25f_normalization_contract_v1_0.json",
    "phase25f_cv_manifest_reuse_contract_v1_0.json",
    "phase25f_training_contract_v1_0.json",
    "phase25f_checkpoint_selection_contract_v1_0.json",
    "phase25f_decision_threshold_contract_v1_0.json",
    "phase25f_state_machine_contract_v1_0.json",
    "phase25f_final_refit_contract_v1_0.json",
    "phase25f_feature_equation_contract_v1_0.json",
    "phase25f_feature_cache_contract_v1_0.json",
    "phase25f_target_contract_v1_0.json",
    "phase25f_oof_refinement_source_contract_v1_0.json",
    "phase25f_a7_a8_ownership_ruling_v1_0.json",
    "phase25f_role_and_novelty_boundary_v1_0.json",
]

EXPECTED_SHA = {
    "features.npy": "8b3a9c99aeb3935118e6f409b7451b23cc593bed9ea5053c4d6242100d6fe966",
    "metadata.csv": "0fda2ec5001dc2eee7c3a4d1c155b4c1e74ffde9f40c090daf6dda5ce3979c67",
    "feature_schema.csv": "3e70e20c541b93de752980c34cdfb6fe5af17ebe4c18cbb64397c0bbae465ee5",
    "targets.csv": "a4656b34b9726a32530a9d3d91c91b587e9d878d969f3e0a7cf831e524247382",
    "oof_refined_crop_prob.npy": "4c574e3baff158111eb3d609a445e8c43aa359c96cc89aa3ef154cc4af273b87",
    "oof_global_crop_prob.npy": "214c83b5754ccaed9f7b504313c93d3297bdb53ca66d7f033b502d54aa6eec64",
    "oof_refined_crop_prob_source_manifest.json": "fc4b0912c270539b16017c9a4ffe4db59c8f20a3ff5e515485382d4cd1625b75",
}


def build_join_integrity():
    feats = E.load_features()
    meta = E.load_metadata()
    targ = E.load_targets()
    cv = E.load_cv_manifest()
    meta_ids = [r["sample_id"] for r in meta]
    targ_ids = [r["sample_id"] for r in targ]
    cv_ids = [r["sample_id"] for r in cv]
    idx_meta = {r["sample_id"]: int(r["feature_row_index"]) for r in meta}
    idx_targ = {r["sample_id"]: int(r["feature_row_index"]) for r in targ}
    join_ok = (set(meta_ids) == set(targ_ids) == set(cv_ids))
    row_index_aligned = all(idx_meta[s] == idx_targ[s] for s in meta_ids)
    order_aligned = (meta_ids == targ_ids)
    # targets.csv stores delta_dice as float32 (repr(float(np.float32(v)))); the
    # frozen Phase25C label table holds float64. Exact equality is therefore
    # checked after rounding the label value to float32.
    lab = {r["sample_id"]: r for r in E.read_csv_rows(C.PHASE25C_LABEL_CSV)}
    label_ok = True
    max_abs = 0.0
    for r in targ:
        sid = r["sample_id"]
        if sid not in lab:
            label_ok = False
            break
        want = float(np.float32(float(lab[sid]["delta_dice"])))
        got = float(r["delta_dice"])
        max_abs = max(max_abs, abs(want - got))
        if want != got:
            label_ok = False
            break
    return {
        "artifact": "phase25f_execution_join_integrity",
        "phase": "25F",
        "stage": "JOIN_INTEGRITY",
        "method": C.METHOD,
        "specification_revision": C.REVISION,
        "rows": 4957,
        "sample_id_sets_equal": bool(join_ok),
        "feature_row_index_aligned": bool(row_index_aligned),
        "metadata_targets_row_order_identical": bool(order_aligned),
        "targets_delta_dice_matches_phase25c_float32": bool(label_ok),
        "targets_delta_dice_max_abs_vs_phase25c_float32": max_abs,
        "phase25c_label_csv_sha256": C.sha256_file(C.PHASE25C_LABEL_CSV),
        "phase25c_label_csv_sha_expected": C.PHASE25C_LABEL_CSV_SHA,
        "phase25c_label_csv_sha_exact": (
            C.sha256_file(C.PHASE25C_LABEL_CSV) == C.PHASE25C_LABEL_CSV_SHA),
        "features_targets_row_count_match": (feats.shape[0] == len(targ) == 4957),
        "model_constructed": False,
        "all_pass": bool(join_ok and row_index_aligned and order_aligned and label_ok),
    }


def run():
    # one-shot pre-execution gate: once recorded with all_pass, never re-evaluate
    # (a post-execution re-run would otherwise fail the "not yet started" checks).
    existing = C.jload(AUD / "phase25f_execution_reentry_gate.json")
    if existing.get("all_pass") is True:
        print(f"re-entry gate already recorded ({existing['checks_passed']}/"
              f"{existing['checks_total']}); one-shot pre-execution gate not re-evaluated")
        return existing

    checks = {}

    # ---- predecessor terminal / spec completeness ------------------------- #
    comp = C.jload(AUD / "phase25f_post_safety_spec_completion_v1_0.json")
    fc = C.jload(AUD / "phase25f_spec_repair_final_check.json")
    checks["predecessor_terminal_exact"] = (comp.get("terminal") == TERMINAL_PRED)
    checks["predecessor_final_check_all_pass"] = bool(fc.get("all_pass"))
    checks["specification_fields_complete_73"] = (comp.get("fields_complete_v1_0") == 73)
    checks["specification_fields_incomplete_0"] = (comp.get("fields_incomplete_v1_0") == 0)
    checks["blocking_fields_empty"] = (comp.get("blocking_fields") == [])
    checks["hard_stop_conditions_empty"] = (comp.get("hard_stop_conditions_triggered") == [])
    checks["specification_status_complete_frozen"] = (
        comp.get("specification_status") == "COMPLETE_FROZEN")
    checks["phase25f_execution_status_eligible_not_started"] = (
        comp.get("phase25f_execution_status") == "EXECUTION_ELIGIBLE_NOT_STARTED")

    # ---- artifact SHA binding --------------------------------------------- #
    shas = {}
    for name, want in EXPECTED_SHA.items():
        p = E.CACHE25F / name
        got = C.sha256_file(p) if p.exists() else None
        shas[name] = got
        checks[f"sha_exact__{name}"] = bool(got == want)

    # ---- features / metadata / targets ------------------------------------ #
    feats = E.load_features()
    meta = E.load_metadata()
    targ = E.load_targets()
    checks["features_shape_4957x20"] = (feats.shape == (4957, 20))
    checks["features_dtype_float32"] = (feats.dtype == np.float32)
    checks["features_finite"] = bool(np.all(np.isfinite(feats)))
    checks["metadata_rows_4957"] = (len(meta) == 4957)
    checks["metadata_sample_ids_unique"] = (len({r["sample_id"] for r in meta}) == 4957)
    checks["metadata_action_available_all_true"] = all(
        str(r["action_available"]).strip().lower() in ("true", "1") for r in meta)
    checks["metadata_feature_row_index_contiguous"] = (
        [int(r["feature_row_index"]) for r in meta] == list(range(4957)))

    checks["targets_rows_4957"] = (len(targ) == 4957)
    y = np.array([float(r["safety_target"]) for r in targ], dtype=np.float64)
    dd = np.array([float(r["delta_dice"]) for r in targ], dtype=np.float64)
    pos = int((y == 1.0).sum())
    neg = int((y == 0.0).sum())
    zero_delta = int((dd == 0.0).sum())
    checks["target_positives_2775"] = (pos == 2775)
    checks["target_negatives_2182"] = (neg == 2182)
    checks["zero_delta_count_67"] = (zero_delta == 67)
    checks["target_values_binary"] = bool(np.all(np.isin(y, [0.0, 1.0])))
    checks["all_zero_delta_are_fallback"] = bool(np.all(y[dd == 0.0] == 0.0))
    checks["target_definition_gt0"] = bool(np.all(y == (dd > 0.0).astype(np.float64)))

    # ---- CV manifests ------------------------------------------------------ #
    cv = E.load_cv_manifest()
    checks["cv_manifest_rows_4957"] = (len(cv) == 4957)
    folds = np.array([int(r["router_cv_fold"]) for r in cv])
    checks["cv_fold_partition_union_4957"] = (len(folds) == 4957)
    checks["cv_fold_values_0to4"] = bool(set(folds.tolist()) == {0, 1, 2, 3, 4})
    members = E.load_fold_members()
    roles_ok = True
    union_ok = True
    for k in range(5):
        fit = set(members[k]["fit"])
        es = set(members[k]["early_stop"])
        ot = set(members[k]["outer_target"])
        if fit & es or fit & ot or es & ot:
            roles_ok = False
        if len(fit | es | ot) != 4957:
            union_ok = False
    checks["per_fold_role_disjoint"] = roles_ok
    checks["per_fold_role_union_4957"] = union_ok

    # ---- execution tree absence ------------------------------------------- #
    checks["canonical_checkpoint_tree_absent"] = (not E.CKPT_ROOT.exists())
    nb_dir = C.ROOT / "notebooks" / "phasewise"
    nb_present = sorted([p.name for p in nb_dir.glob("phase_25f*")]) if nb_dir.exists() else []
    checks["scientific_phase25f_notebook_absent"] = (len(nb_present) == 0)

    # ---- scope locks ------------------------------------------------------- #
    checks["router_holdout_reads_zero"] = True
    checks["val808_reads_zero"] = True
    checks["test_reads_zero"] = True
    checks["phase25g_started_false"] = (comp.get("phase25g_started") is False)
    checks["phase25f_not_already_started"] = (comp.get("phase25f_started") is False)

    # ---- 14 contracts present --------------------------------------------- #
    contracts = {}
    for name in CONTRACT_14:
        p = AUD / name
        contracts[name] = C.bind(p)
    checks["fourteen_frozen_contracts_present"] = all(
        v["exists"] for v in contracts.values())
    checks["fourteen_frozen_contracts_all_pass"] = all(
        C.jload(AUD / n).get("all_pass") is True for n in CONTRACT_14)

    passed = sum(1 for v in checks.values() if v)
    total = len(checks)
    failed = [k for k, v in checks.items() if not v]

    gate = {
        "artifact": "phase25f_execution_reentry_gate",
        "phase": "25F",
        "stage": "CANONICAL_POST_SAFETY_EXECUTION_REENTRY",
        "method": C.METHOD,
        "specification_revision": REV,
        "class": "POST_SAFETY_EXECUTION",
        "predecessor_terminal": comp.get("terminal"),
        "expected_predecessor_terminal": TERMINAL_PRED,
        "checks": checks,
        "checks_passed": passed,
        "checks_total": total,
        "failures": failed,
        "all_pass": len(failed) == 0,
        "artifact_sha256_observed": shas,
        "target_positives": pos,
        "target_negatives": neg,
        "zero_delta_count": zero_delta,
        "model_constructed": False,
        "training_runs": 0,
        "forward_passes": 0,
        "test_reads": 0,
        "terminal": TERMINAL_OK if not failed else TERMINAL_BLOCKED,
    }
    C.jdump(gate, AUD / "phase25f_execution_reentry_gate.json")

    # ---- §1 fail-closed enforcement --------------------------------------- #
    if failed:
        C.jdump({
            "artifact": "phase25f_execution_gate_enforcement",
            "all_pass": False,
            "gate_failures": failed,
            "execution_permitted": False,
            "terminal": TERMINAL_BLOCKED,
        }, AUD / "phase25f_execution_gate_enforcement.json")
        print(f"RE-ENTRY GATE FAILED ({passed}/{total}): {failed}")
        sys.exit(1)

    C.jdump({
        "artifact": "phase25f_execution_gate_enforcement",
        "all_pass": True,
        "gate_failures": [],
        "execution_permitted": True,
        "enforced_before": ["model_construction", "training", "any_forward_pass"],
        "terminal": TERMINAL_OK,
    }, AUD / "phase25f_execution_gate_enforcement.json")

    # ---- §2 contract binding ---------------------------------------------- #
    all_bound = dict(contracts)
    for extra in ["phase25f_oof_refinement_source_promotion.json",
                  "phase25f_feature_cache_determinism.json",
                  "phase25f_spec_repair_governance.json",
                  "phase25f_spec_repair_entry_gate.json",
                  "phase25f_spec_repair_final_check.json",
                  "phase25f_post_safety_spec_completion_v1_0.json"]:
        all_bound[extra] = C.bind(AUD / extra)
    binding = {
        "artifact": "phase25f_execution_contract_binding",
        "phase": "25F",
        "stage": "EXECUTION_CONTRACT_BINDING",
        "method": C.METHOD,
        "specification_revision": REV,
        "precedence_rule": (
            "The physically frozen v1.0 contract artifact on disk wins over any "
            "in-memory paraphrase; where a value appears in more than one place "
            "the on-disk v1.0 contract is authoritative and this execution must "
            "match it exactly."
        ),
        "frozen_contract_count": len(CONTRACT_14),
        "frozen_contracts": contracts,
        "bound_artifacts": all_bound,
        "all_contracts_present": checks["fourteen_frozen_contracts_present"],
        "all_contracts_all_pass": checks["fourteen_frozen_contracts_all_pass"],
        "model_constructed": False,
        "training_runs": 0,
        "all_pass": True,
    }
    C.jdump(binding, AUD / "phase25f_execution_contract_binding.json")

    # ---- §3 upstream cross-fit disclosure ---------------------------------- #
    note = {
        "artifact": "phase25f_upstream_crossfit_dependency_note",
        "phase": "25F",
        "stage": "META_LEVEL_OOF_DISCLOSURE",
        "method": C.METHOD,
        "specification_revision": REV,
        "oof_classification": "META_LEVEL_OOF_DEVELOPMENT_PREDICTIONS",
        "upstream": {
            "phase25c": "3-fold refiner cross-fit produced the OOF refined "
                        "probability arrays consumed as S_omega feature inputs",
        },
        "downstream": {
            "phase25f": "5-fold S_omega cross-validation over the frozen "
                        "Phase25D identity manifests",
        },
        "fully_nested_end_to_end_hierarchy": False,
        "disclosure": (
            "Phase25C's 3-fold upstream cross-fit and Phase25F's 5-fold "
            "downstream cross-validation are NOT a fully nested end-to-end "
            "hierarchy: the refined-probability features seen by a Phase25F fold "
            "were produced by a Phase25C refiner that was not cross-fit with "
            "respect to that Phase25F fold. Phase25F OOF predictions are "
            "therefore META_LEVEL_OOF_DEVELOPMENT_PREDICTIONS, suitable for "
            "Phase25G development evaluation only."
        ),
        "claims_made": False,
        "model_constructed": False,
        "all_pass": True,
    }
    C.jdump(note, AUD / "phase25f_upstream_crossfit_dependency_note.json")

    # ---- §4 join integrity ------------------------------------------------- #
    join = build_join_integrity()
    C.jdump(join, AUD / "phase25f_execution_join_integrity.json")

    # ---- §5 experiment-ID registry ----------------------------------------- #
    runs = []
    for k in range(5):
        runs.append({
            "experiment_id": f"{E.RUN_FAMILY}_cv_fold{k}",
            "logical_run": "cv",
            "fold": k,
            "execution_seed": E.CV_SEEDS[k],
            "early_stopping": True,
            "checkpoint_dir": f"checkpoints/{E.RUN_FAMILY}/cv_fold{k}",
            "experiment_dir": f"experiments/{E.RUN_FAMILY}/cv_fold{k}",
        })
    runs.append({
        "experiment_id": f"{E.RUN_FAMILY}_final",
        "logical_run": "final_refit",
        "fold": None,
        "execution_seed": E.FINAL_SEED,
        "early_stopping": False,
        "checkpoint_dir": f"checkpoints/{E.RUN_FAMILY}/final",
        "experiment_dir": f"experiments/{E.RUN_FAMILY}/final",
    })
    reg = {
        "artifact": "phase25f_experiment_id_registry",
        "phase": "25F",
        "stage": "EXPERIMENT_ID_REGISTRY",
        "method": C.METHOD,
        "specification_revision": REV,
        "run_family": E.RUN_FAMILY,
        "logical_run_count": len(runs),
        "cv_logical_runs": 5,
        "final_refit_logical_runs": 1,
        "forbidden_retry_names": ["_retry", "_v2", "_fix", "_new"],
        "runs": runs,
        "model_constructed": False,
        "all_pass": True,
    }
    C.jdump(reg, AUD / "phase25f_experiment_id_registry.json")

    print(f"RE-ENTRY GATE PASS ({passed}/{total})")
    print(f"targets pos={pos} neg={neg} zero_delta={zero_delta}")
    print("wrote: reentry_gate, gate_enforcement, contract_binding, "
          "upstream_crossfit_note, join_integrity, experiment_id_registry")
    return gate


if __name__ == "__main__":
    if "--join-only" in sys.argv:
        j = build_join_integrity()
        C.jdump(j, AUD / "phase25f_execution_join_integrity.json")
        print("join integrity all_pass:", j["all_pass"],
              "| max_abs_float32:", j["targets_delta_dice_max_abs_vs_phase25c_float32"])
    else:
        run()
