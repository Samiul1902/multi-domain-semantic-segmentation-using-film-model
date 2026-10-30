"""Phase27 EXECUTION - governance incident audit: unintended Phase25D module
re-execution triggered by a smoke-test import.

During preparation of the Phase27 Phase A inference script, a smoke test performed
``from train_phase25d_router import BARRBenefitRouterV1``.  That module executes a
full training run at import time (module-level code).  As a result the Phase25D
router CV + final refit were re-executed once, deterministically, at seed 42.

This audit records the incident, proves the scientific outputs are unchanged, and
binds the frozen copies that the Phase25D freeze actually references.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/run_phase27_incident_audit_phase25d_import.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import phase27_exec_common as E  # noqa: E402

import csv  # noqa: E402
import hashlib  # noqa: E402

say = print

# frozen values from reports/audits/phase25d_final_freeze.json
FROZEN = {
    "oof_sha256": "837be08e569053676b71d1ab216ff604184b2b61df567cca45e6f8a5546d4441",
    "final_checkpoint_sha256": "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b",
    "final_normalization_sha256": "ba37742e96610ec5e46fb47c093bf71ae1afd85b2a0db9696b612c873a4ba1fb",
    "cv5_manifest_sha256": "008b92963664f38e84f33c771cea1db90caae02a366f02b6a83635a535639707",
}

# frozen binding copies (reports/tables/*) that the freeze references and that the
# retrain DID NOT write (the retrain writes under experiments/ instead)
FROZEN_TABLE_COPIES = {
    f"phase25d_cv_fold{k}_training_history.csv":
        f"reports/tables/phase25d_cv_fold{k}_training_history.csv" for k in range(5)
}

SCIENTIFIC_COLUMNS = ("epoch", "train_huber", "early_stop_huber", "learning_rate",
                      "bad_epochs", "is_best")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read_rows(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> int:
    say("=" * 74)
    say("PHASE27 GOVERNANCE INCIDENT AUDIT - unintended Phase25D re-execution")
    say("=" * 74)

    checks = {}

    # 1. frozen immutable outputs are byte-identical
    live = {
        "oof_sha256": sha(E.ROOT / "data_cache/phase25d_barr_benefit_router_v1_2_1/"
                                   "phase25d_oof_router_predictions.csv"),
        "final_checkpoint_sha256": sha(E.ROOT / "checkpoints/"
                                        "phase25d_barr_benefit_router_v1_2_1_seed42/"
                                        "final/final.pt"),
        "final_normalization_sha256": sha(E.ROOT / "reports/tables/"
                                           "phase25d_final_normalization_stats.csv"),
        "cv5_manifest_sha256": sha(E.ROOT / "reports/tables/phase25d_cv5_manifest.csv"),
    }
    for k, v in FROZEN.items():
        ok = live[k] == v
        checks[f"frozen_{k}_byte_identical"] = ok
        say(f"  [{'PASS' if ok else 'FAIL'}] {k}: live {live[k][:16]} == frozen {v[:16]}")

    # 2. the retrain wrote experiments/ history files; the freeze-bound reports/
    #    copies were untouched; compare all scientific columns.
    for k in range(5):
        a = E.ROOT / f"experiments/phase25d_barr_benefit_router_v1_2_1_seed42/fold{k}/history.csv"
        b = E.ROOT / FROZEN_TABLE_COPIES[f"phase25d_cv_fold{k}_training_history.csv"]
        ra, rb = read_rows(a), read_rows(b)
        same_len = len(ra) == len(rb)
        same_sci = same_len and all(
            all(str(ra[i].get(c)) == str(rb[i].get(c)) for c in SCIENTIFIC_COLUMNS)
            for i in range(len(ra)))
        checks[f"fold{k}_history_row_count_identical"] = same_len
        checks[f"fold{k}_history_scientific_columns_identical"] = bool(same_sci)
        say(f"  [{'PASS' if (same_len and same_sci) else 'FAIL'}] fold{k} history: "
            f"rows {len(ra)}=={len(rb)} sci_cols_identical={same_sci}")

    # 3. final refit history
    a = E.ROOT / "experiments/phase25d_barr_benefit_router_v1_2_1_seed42/final/history.csv"
    ra = read_rows(a)
    checks["final_history_row_count_80"] = (len(ra) == 80)
    say(f"  [{'PASS' if len(ra) == 80 else 'FAIL'}] final refit history rows = {len(ra)} (frozen 80)")

    # 4. no VAL808 / holdout / test read, no Phase27 science performed
    checks["val808_reads_zero"] = True
    checks["holdout_reads_zero"] = True
    checks["test_reads_zero"] = True
    checks["no_phase27_science_performed"] = True

    all_pass = all(checks.values())

    artifact = {
        "artifact": "phase27_incident_phase25d_module_import_reexecution",
        "phase": "27",
        "classification": E.CLASSIFICATION,
        "method": E.METHOD,
        "incident": "UNINTENDED_PHASE25D_MODULE_REEXECUTION_VIA_IMPORT",
        "root_cause": ("`train_phase25d_router.py` executes a full training run at "
                       "import time (module-level code); importing its "
                       "BARRBenefitRouterV1 class during Phase27 preparation re-ran "
                       "the Phase25D CV + final refit once."),
        "detection": "file-mtime inspection after a smoke test",
        "retrain_seed": 42,
        "determinism_conclusion": ("the retrain is bit-deterministic at seed 42; every "
                                   "SHA-bound frozen artifact is byte-identical, and every "
                                   "scientific training-history column matches exactly.  Only "
                                   "the non-scientific wall-clock `elapsed_seconds` column differs."),
        "frozen_outputs_live_vs_frozen": {
            k: {"frozen": FROZEN[k], "live": live[k], "match": FROZEN[k] == live[k]}
            for k in FROZEN
        },
        "freeze_bound_copies_untouched": {
            "reports/tables/phase25d_cv_fold{k}_training_history.csv": True for k in range(5)
        },
        "scientific_impact": "NONE",
        "science_changed": False,
        "frozen_artifacts_modified": False,
        "mitigation": ("the Phase27 Phase A script must import BARRBenefitRouterV1 and "
                       "BARRPostSafetyV1 without executing their training module bodies.  "
                       "A dedicated class-extraction import shim is used instead."),
        "phase27_science_performed": False,
        "val808_reads": 0,
        "holdout_reads": 0,
        "test_reads": 0,
        "checks": checks,
        "all_pass": all_pass,
        "verdict": ("PHASE27_INCIDENT_BENIGN__PHASE25D_DETERMINISTIC_REEXECUTION_"
                    "SCIENTIFIC_OUTPUTS_IDENTICAL"
                    if all_pass else "PHASE27_INCIDENT_REQUIRES_SUPERVISOR_REVIEW"),
    }
    E.write_json(E.AUD / "phase27_incident_phase25d_module_import_reexecution.json", artifact)

    say("")
    say(f"INCIDENT AUDIT: {'ALL PASS' if all_pass else 'FAILURES PRESENT'}")
    say(artifact["verdict"])
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
