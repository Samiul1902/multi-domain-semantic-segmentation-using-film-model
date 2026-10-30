"""Phase 22 — bind the frozen Phase-21 reference and verify it has not moved.

Fail-closed. Re-derives every identity Phase 22 depends on, from disk, and
compares against the SHAs recorded by the Phase-21 final freeze and by this
phase's own frozen protocol. No inference, no training.

If any check fails, Phase 22's results would not be attributable to the frozen
reference and the script exits non-zero.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.analysis import phase22_common as C  # noqa: E402

OUT = C.AUDITS / "phase22_phase21_reference_binding.json"

CHECKS: list[dict] = []


def chk(name: str, passed: bool, expected, observed, note: str = "") -> None:
    CHECKS.append({"check": name, "pass": bool(passed),
                   "expected": expected, "observed": observed, "note": note})


def main() -> int:
    protocol = C.load_json(C.AUDITS / "phase22_diagnostic_protocol.json")
    freeze = C.load_json(C.PHASE21_FREEZE)
    val_eval = C.load_json(C.AUDITS / "phase21_val_evaluation.json")
    p21_manifest = C.load_json(C.AUDITS / "phase21_prediction_manifest.json")

    # ---- frozen protocol identity ---------------------------------------- #
    chk("phase22_protocol_frozen", protocol.get("frozen") is True, True,
        protocol.get("frozen"))
    chk("phase22_protocol_declared_before_outcomes",
        protocol.get("declared_before_outcome_analysis") is True, True,
        protocol.get("declared_before_outcome_analysis"))
    chk("phase22_protocol_is_not_training_phase",
        protocol.get("is_training_phase") is False, False,
        protocol.get("is_training_phase"))

    # ---- Phase-21 freeze identity ---------------------------------------- #
    chk("phase21_freeze_verified", freeze.get("freeze_verified") is True, True,
        freeze.get("freeze_verified"))
    chk("phase21_validation_problems_empty", freeze.get("validation_problems") == [],
        [], freeze.get("validation_problems"))
    chk("phase21_terminal_state",
        freeze.get("terminal_state")
        == "PHASE21_GLOBAL_MEDFILM_REFERENCE_COMPLETE__PHASE22_ELIGIBLE_NOT_STARTED",
        "PHASE21_GLOBAL_MEDFILM_REFERENCE_COMPLETE__PHASE22_ELIGIBLE_NOT_STARTED",
        freeze.get("terminal_state"))
    chk("phase21_is_global_reference_only",
        freeze.get("is_global_reference_only") is True, True,
        freeze.get("is_global_reference_only"))
    chk("phase21_is_not_final_ra_medfilm_seg_plus_plus",
        freeze.get("is_final_ra_medfilm_seg_plus_plus") is False, False,
        freeze.get("is_final_ra_medfilm_seg_plus_plus"))

    # ---- frozen Phase-20 protocol ---------------------------------------- #
    proto_sha = C.sha256_file(ROOT / C.PROTOCOL_PATH)
    chk("phase20_protocol_sha_matches_expected", proto_sha == C.PROTOCOL_SHA256,
        C.PROTOCOL_SHA256, proto_sha)
    chk("phase20_protocol_sha_matches_freeze",
        proto_sha == freeze["frozen_bindings"]["protocol_sha256"],
        freeze["frozen_bindings"]["protocol_sha256"], proto_sha)
    chk("phase20_protocol_no_unintentional_differences",
        freeze["frozen_bindings"]["protocol_unintentional_differences"] == [],
        [], freeze["frozen_bindings"]["protocol_unintentional_differences"])

    # ---- architecture binding -------------------------------------------- #
    arch_sha = C.sha256_file(ROOT / "reports/audits/phase21_global_medfilm_architecture_binding.json")
    chk("architecture_binding_sha_matches_freeze",
        arch_sha == freeze["frozen_bindings"]["architecture_binding_sha256"],
        freeze["frozen_bindings"]["architecture_binding_sha256"], arch_sha)
    chk("architecture_id_matches",
        freeze["architecture_id"] == C.ARCHITECTURE_ID, C.ARCHITECTURE_ID,
        freeze["architecture_id"])

    # ---- checkpoint ------------------------------------------------------ #
    ckpt_sha = C.sha256_file(C.PHASE21_BEST_CKPT)
    chk("checkpoint_sha_matches_freeze",
        ckpt_sha == freeze["training"]["best_checkpoint_sha256"],
        freeze["training"]["best_checkpoint_sha256"], ckpt_sha)
    chk("checkpoint_sha_matches_phase22_protocol",
        ckpt_sha == protocol["reference_model"]["checkpoint_sha256_expected"],
        protocol["reference_model"]["checkpoint_sha256_expected"], ckpt_sha)
    chk("checkpoint_epoch", freeze["training"]["best_epoch"] == 66, 66,
        freeze["training"]["best_epoch"])
    chk("parameter_count", freeze["training"]["model_params"] == 3523001, 3523001,
        freeze["training"]["model_params"])
    chk("training_naturally_terminated",
        freeze["training"]["stop_reason"] in ("EARLY_STOPPING_PATIENCE", "MAX_EPOCHS"),
        "EARLY_STOPPING_PATIENCE|MAX_EPOCHS", freeze["training"]["stop_reason"])
    chk("no_independent_duplicate_runs",
        freeze["training"]["independent_duplicate_runs"] == 0, 0,
        freeze["training"]["independent_duplicate_runs"])

    # ---- canonical VAL evaluation ---------------------------------------- #
    chk("canonical_val_inference_runs_is_1",
        val_eval.get("canonical_val_inference_runs") == 1, 1,
        val_eval.get("canonical_val_inference_runs"))
    chk("canonical_val_samples_808", val_eval.get("samples_evaluated") == 808, 808,
        val_eval.get("samples_evaluated"))
    chk("canonical_val_no_tta", val_eval.get("no_tta") is True, True,
        val_eval.get("no_tta"))
    chk("canonical_val_no_threshold_tuning",
        val_eval.get("no_threshold_tuning") is True, True,
        val_eval.get("no_threshold_tuning"))
    chk("canonical_val_no_morphology", val_eval.get("no_morphology") is True, True,
        val_eval.get("no_morphology"))
    chk("canonical_val_threshold", float(val_eval.get("threshold")) == 0.5, 0.5,
        val_eval.get("threshold"))

    # ---- persisted predictions -------------------------------------------- #
    per_image_path = C.TABLES / "phase21_per_image_val_metrics.csv"
    pi_sha = C.sha256_file(per_image_path)
    chk("phase21_per_image_table_sha_matches_freeze",
        pi_sha == freeze["canonical_val_evaluation"]["per_image_table_sha256"],
        freeze["canonical_val_evaluation"]["per_image_table_sha256"], pi_sha)

    pi = pd.read_csv(per_image_path)
    chk("phase21_per_image_rows_808", len(pi) == 808, 808, len(pi))
    counts = {k: int(v) for k, v in pi.groupby("dataset").size().items()}
    chk("phase21_per_domain_counts",
        counts == {"BUSI": 84, "ISIC": 357, "KUB": 280, "KVASIR": 87},
        {"BUSI": 84, "ISIC": 357, "KUB": 280, "KVASIR": 87}, counts)

    manifest = pd.read_csv(C.TABLES / "phase21_prediction_manifest.csv")
    chk("phase21_prediction_manifest_rows_808", len(manifest) == 808, 808, len(manifest))
    present = sum(1 for p in manifest["npz_path"] if (ROOT / p).exists())
    chk("phase21_all_808_npz_present", present == 808, 808, present)
    chk("phase21_manifest_checkpoint_sha_uniform",
        set(manifest["checkpoint_sha256"]) == {ckpt_sha}, [ckpt_sha],
        sorted(set(manifest["checkpoint_sha256"])))
    chk("phase21_manifest_threshold_uniform",
        set(manifest["threshold"].astype(float)) == {0.5}, [0.5],
        sorted(set(manifest["threshold"].astype(float))))
    chk("phase21_manifest_resolution_uniform",
        set(manifest["input_resolution"]) == {512}, [512],
        sorted(set(manifest["input_resolution"])))
    chk("phase21_manifest_policy_uniform",
        set(manifest["input_channel_policy"]) == {"RGB_3CH"}, ["RGB_3CH"],
        sorted(set(manifest["input_channel_policy"])))

    # ---- TEST lock -------------------------------------------------------- #
    locks = C.verify_no_test_access()
    chk("test_reads_all_zero", all(v == 0 for v in locks.values()), "all 0", locks)
    chk("freeze_test_reads_zero",
        freeze.get("governance", {}).get("test_reads_total_observed") == 0, 0,
        freeze.get("governance", {}).get("test_reads_total_observed"))
    chk("canonical_manifest_reports_test_reads_zero",
        all(v == 0 for v in p21_manifest.get("test_reads", {}).values()), "all 0",
        p21_manifest.get("test_reads"))
    chk("phase22_has_not_rerun_canonical_val",
        val_eval.get("canonical_val_inference_runs") == 1, 1,
        val_eval.get("canonical_val_inference_runs"),
        "Phase 22 must read the persisted maps, never re-run the canonical pass")

    # ---- verdict ---------------------------------------------------------- #
    n_failed = sum(1 for c in CHECKS if not c["pass"])
    payload = {
        "artifact": "phase22_phase21_reference_binding",
        "phase": 22,
        "purpose": ("bind every identity Phase 22 depends on to the frozen Phase-21 "
                    "reference, so no Phase-22 number can be attributed to a drifted model"),
        "verdict": ("PHASE22_REFERENCE_BINDING_PASS" if n_failed == 0
                    else "PHASE22_REFERENCE_BINDING_FAIL"),
        "n_checks": len(CHECKS), "n_passed": len(CHECKS) - n_failed,
        "n_failed": n_failed,
        "checks": CHECKS,
        "binding": {
            "phase21_experiment_id": C.EXPERIMENT_ID,
            "phase21_architecture_id": C.ARCHITECTURE_ID,
            "phase21_checkpoint_sha256": ckpt_sha,
            "phase20_protocol_sha256": proto_sha,
            "phase22_protocol_sha256": C.sha256_file(
                C.AUDITS / "phase22_diagnostic_protocol.json"),
            "persisted_prediction_root": (
                f"reports/predictions/{C.EXPERIMENT_ID}/val"),
            "persisted_prediction_counts": counts,
            "phase21_reference_macro_domain_dice": freeze["results"]["global_medfilm"][
                "macro_domain_dice"],
        },
        "no_inference_performed_here": True,
        "training_jobs_started": 0,
        "test_reads": locks,
    }
    C.write_json(OUT, payload)

    for c in CHECKS:
        if not c["pass"]:
            print(f"  FAIL {c['check']}: expected={c['expected']} observed={c['observed']}")
    print(f"\n{payload['verdict']}: {payload['n_passed']}/{payload['n_checks']} passed")
    print(f"WROTE {OUT}")
    return 1 if n_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
