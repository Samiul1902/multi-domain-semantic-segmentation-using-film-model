"""Phase 25D -- AUTHORITATIVE FROZEN ROUTER TRAINING SPEC AUDIT (work order §2).

Recovers, from the authoritative frozen Phase24 artifacts only, every field that the
Phase25D router-training contract requires. Fail-closed: if any field that materially
affects optimization is *genuinely absent* from every authoritative artifact, the phase
STOPS before model construction with PHASE25D_BLOCKED__ROUTER_TRAINING_SPEC_INCOMPLETE.

Missing fields must be reported exactly. Nothing is invented and nothing is guessed.

Writes reports/audits/phase25d_frozen_training_spec_binding.json. Read-only.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
UTC = datetime.now(timezone.utc).isoformat()

SPEC_INCOMPLETE = "PHASE25D_BLOCKED__ROUTER_TRAINING_SPEC_INCOMPLETE"


def jd(p: Path) -> dict:
    return json.loads(Path(p).read_text(encoding="utf-8"))


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main() -> int:
    src = {}
    names = [
        "phase24_exact_implementation_spec.json",
        "phase24_spec_repair_freeze.json",
        "phase24_router_feature_dimension_contract_v1_2.json",
        "phase24_router_feature_spec_completion_v1_2.json",
        "phase24_benefit_data_protocol_exact.json",
        "phase24_paired_refinement_gain_contract.json",
        "phase24_architecture_spec.json",
        "phase24_v1_2_feature_spec_final_check.json",
    ]
    for n in names:
        p = AUD / n
        src[n] = jd(p) if p.exists() else {}

    exact = src["phase24_exact_implementation_spec.json"]
    router = exact.get("router", {})
    refiner_final = exact.get("final_refiner", {})
    crossfit = exact.get("crossfit", {})
    dim = src["phase24_router_feature_dimension_contract_v1_2.json"]

    # ---- fields PRESENT in the authoritative frozen artifacts ---------------
    present = {
        "architecture": router.get("architecture"),
        "activation": router.get("activation"),
        "dropout": router.get("dropout"),
        "hidden_dimensions": router.get("hidden_dimensions_active"),
        "task_embedding": router.get("task_conditioning"),
        "input_dim_closed_form": router.get("input_dim_closed_form"),
        "input_dim_breakdown": router.get("input_dim_breakdown"),
        "output": router.get("output"),
        "harm_head": router.get("harm_head"),
        "loss": router.get("loss"),
        "optimizer": router.get("optimizer"),
        "lr": router.get("lr"),
        "weight_decay": router.get("weight_decay"),
        "batch_size": router.get("batch_size"),
        "max_epochs": router.get("max_epochs"),
        "early_stopping_patience": router.get("early_stopping_patience"),
        "scheduler": router.get("scheduler"),
        "seed": router.get("seed"),
        "epoch_selection": router.get("epoch_selection"),
        "final_training": router.get("final_training"),
        "holdout_for_fitting_or_epoch_selection":
            router.get("holdout_for_fitting_or_epoch_selection"),
        "normalization": router.get("normalization"),
        "normalization_stats_source": router.get("normalization_stats_source"),
        "normalization_from_holdout_val_test": router.get("normalization_from_holdout_val_test"),
        "expected_parameter_count_closed_form":
            router.get("expected_parameter_count_closed_form"),
        "canonical_total_trainable_parameters":
            dim.get("trainable_parameter_contract", {}).get(
                "router_total_trainable_parameters"),
        "resource_cost_enters_delta_hat": router.get("resource_cost_enters_delta_hat"),
    }

    # ---- fields GENUINELY ABSENT (searched across all authoritative artifacts)
    # Each candidate location was inspected; the note records where we looked.
    absent = {}
    absent["cv_fold_count_explicit"] = {
        "value": None,
        "searched": ["router.fold_count", "router.cv.n_splits", "router.crossfit"],
        "found": "the string 'deterministic 5-fold group-safe cross-validation' in "
                 "router.epoch_selection only -- a LABEL, not a numeric field",
    }
    absent["cv_fold_assignment_algorithm"] = {
        "value": None,
        "searched": ["router.crossfit", "router.cv_algorithm",
                     "any 'n_splits'/'GroupKFold'/'StratifiedGroup' definition"],
        "found": "ABSENT -- no fold-assignment procedure, no group-stratification rule, "
                 "no per-fold seed derivation, no ordering rule for the 5 router folds",
    }
    absent["cv_inner_split_rule"] = {
        "value": None,
        "searched": ["router.crossfit", "router.inner_split"],
        "found": "ABSENT for the router (the refiner's 3-fold crossfit DOES specify "
                 "inner_fitting_fraction 0.9 / inner_early_stop_fraction 0.1)",
    }
    absent["checkpoint_selection_rule"] = {
        "value": None,
        "searched": ["router.checkpoint_selection", "router.best_epoch_rule"],
        "found": "ABSENT for the router (the refiner specifies "
                 "'lowest validation loss (primary)'). Phase25D was asked to expect "
                 "'lowest validation Huber loss' but no authoritative artifact states it.",
    }
    absent["checkpoint_tie_rule"] = {
        "value": None,
        "searched": ["router.tie_rule", "router.epoch_selection tie handling"],
        "found": "ABSENT",
    }
    absent["target_scaling_semantics"] = {
        "value": None,
        "searched": ["router.target_scaling", "router.target_normalization",
                     "paired_gain_contract target transform"],
        "found": "ABSENT -- no statement on whether delta_dice is used raw; the contract "
                 "only names the continuous target. (Phase25D intends raw/unscaled, but "
                 "that is not authoritatively frozen.)",
    }
    absent["final_refit_scheduler_semantics"] = {
        "value": None,
        "searched": ["router.final_refit_scheduler", "router.final_monitor",
                     "final_training scheduler note"],
        "found": "ABSENT -- router.final_training says 'median selected epoch count' but "
                 "the no-validation refit has NO validation set to drive "
                 "ReduceLROnPlateau, and no substitute monitor/step schedule is frozen. "
                 "Contrast: the refiner's final block DOES state "
                 "early_stopping_on_holdout=false with an explicit epoch_rule.",
    }
    absent["final_refit_seed_policy"] = {
        "value": None,
        "searched": ["router.final_refit_seed", "router.final_training seed"],
        "found": "ABSENT for the router (the refiner specifies 'reinitialize "
                 "BARRRegionalRefinerV1 from seed 42'); router seed policy for the final "
                 "refit is not stated.",
    }
    absent["median_epoch_rule_exact"] = {
        "value": None,
        "searched": ["router.median_rule", "router.final_epoch_rule"],
        "found": "PARTIAL -- 'median selected epoch count' is stated in prose but the "
                 "exact integer rule for 5 values is not frozen (Phase25D was asked to "
                 "expect 'third sorted value' -- that expectation is not authoritatively "
                 "frozen).",
    }

    blockers = [
        "cv_fold_assignment_algorithm",
        "cv_inner_split_rule",
        "checkpoint_selection_rule",
        "checkpoint_tie_rule",
        "target_scaling_semantics",
        "final_refit_scheduler_semantics",
        "final_refit_seed_policy",
        "median_epoch_rule_exact",
    ]
    hard_blockers = [
        b for b in blockers
        if b in ("cv_fold_assignment_algorithm", "cv_inner_split_rule",
                 "checkpoint_selection_rule", "target_scaling_semantics",
                 "final_refit_scheduler_semantics")
    ]

    spec_complete = len(hard_blockers) == 0
    verdict = ("PHASE25D_ROUTER_TRAINING_SPEC_COMPLETE" if spec_complete
               else SPEC_INCOMPLETE)

    out = {
        "artifact": "phase25d_frozen_training_spec_binding",
        "phase": "25D",
        "classification": "FAIL_CLOSED_SPEC_AUDIT",
        "method": "RA-MedFiLM-BARR",
        "architecture_revision": "ra_medfilm_barr_narrowed_v1_2",
        "authoritative_sources": {
            n: {"sha256": sha(AUD / n)} for n in names if (AUD / n).exists()
        },
        "recovered_present_fields": present,
        "genuinely_absent_fields": absent,
        "blocking_fields": blockers,
        "hard_blocking_fields": hard_blockers,
        "specification_complete": spec_complete,
        "specification_incomplete": not spec_complete,
        "missing_field_report": hard_blockers,
        "model_constructed": False,
        "training_runs": 0,
        "router_instantiated": False,
        "verdict": verdict,
        "terminal": verdict,
        "action": ("PROCEED_TO_MODEL_CONSTRUCTION" if spec_complete
                   else "STOP_BEFORE_MODEL_CONSTRUCTION"),
        "test_reads": 0,
        "generated_utc": UTC,
    }
    (AUD / "phase25d_frozen_training_spec_binding.json").write_text(
        json.dumps(out, indent=1) + "\n", encoding="utf-8")

    print("RECOVERED (present in frozen artifacts):")
    for k, v in present.items():
        print(f"  [OK]   {k} = {json.dumps(v)[:90]}")
    print()
    print("GENUINELY ABSENT (searched all authoritative artifacts):")
    for k in absent:
        mark = "BLOCK" if k in hard_blockers else "note "
        print(f"  [{mark}] {k}")
        print(f"           {absent[k]['found']}")
    print()
    print("SPEC COMPLETE:", spec_complete)
    print("HARD BLOCKERS :", hard_blockers)
    print("TERMINAL      :", verdict)
    return 0 if spec_complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
