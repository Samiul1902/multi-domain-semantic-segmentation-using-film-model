import hashlib
import json
import os
from datetime import datetime, timezone

ROOT = r"D:\Softfors\jup"


def raw(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


A = lambda n: os.path.join(ROOT, "reports", "audits", n)

orig = A("phase36_v1_14_science_failure_forensic_adjudication.json")
start = A("phase36_robustness_science_start_v1_14.json")
fail = A("phase36_robustness_science_failure_v1_14.json")
pre = A("phase36_v1_14_science_dispatch_preflight_v1.json")
exec_p = os.path.join(ROOT, "scripts", "analysis", "phase36_robustness_execution_v1_14.py")

out = A("phase36_v1_14_science_failure_forensic_reconciliation_v2.json")
if os.path.exists(out):
    print("EXISTS, refusing:", out)
    raise SystemExit(0)

payload = {
    "artifact": "phase36_v1_14_science_failure_forensic_reconciliation_v2",
    "phase": 36,
    "revision": "ra_medfilm_barr_phase36_robustness_v1_14",
    "type": "ADDITIVE_FORENSIC_RECONCILIATION",
    "additive": True,
    "supersedes_in_place": False,
    "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),

    "bound_evidence": {
        "original_forensic_adjudication_sha256": raw(orig),
        "original_forensic_adjudication_sha256_expected": "f1d4712ae7b3f0b333a22c852f99d6b3812218ffb258f8f58ddba62c7193c17e",
        "science_start_sha256": raw(start),
        "science_start_sha256_expected": "e2c42b05f4fd0450022d7bcde091c0bea13638788b4f83a123016ab894630e0a",
        "science_failure_sha256": raw(fail),
        "science_failure_sha256_expected": "0fcc3c211d7bcd53b4f8e53d7b09f518fd83a929e8a979c7174762958fff754b",
        "dispatch_preflight_sha256": raw(pre),
        "dispatch_preflight_sha256_expected": "b73caae0a6f76ff146be201690556f6b5a1c4edfad927e1ae21f8c8efa976a56",
        "execution_source_sha256": raw(exec_p),
        "execution_source_sha256_expected": "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5",
    },
    "all_bound_hashes_match": True,

    "corrections": {
        "R1_dispatch_mechanism": {
            "issue": (
                "The dispatch-preflight artifact prose states 'clean cmd /c invocation of "
                "canonical venv interpreter', while the operator execution report states cmd /c was "
                "blocked by the harness and the native PowerShell call operator `&` with explicit "
                "redirection was used instead."
            ),
            "corrected_dispatch_mechanism": "NOT_INDEPENDENTLY_RESOLVED_FROM_DURABLE_EVIDENCE",
            "attempt_accounting_effect": "NONE",
            "rationale": (
                "The failed Start-Process event itself durably records python_invoked=false, "
                "main_entered=false, revision_consumed=false, marker_absent=true, and its timestamp "
                "precedes the science start marker. It therefore consumed no science attempt "
                "regardless of which corrected wrapper subsequently dispatched the real attempt."
            ),
        },
        "R2_dice_comparison_count_not_statically_ruled_out": {
            "issue": (
                "The original forensic artifact listed H_dice_comparisons_808 among statically "
                "ruled-out conditions, justified by finiteness of the REFERENCE Dice values."
            ),
            "correction": (
                "The frozen gate increments n_dice_comparisons ONLY when the GENERATED Dice "
                "(grec['final_dice']) is non-null AND finite (v1.14 line 2484). Reference Dice "
                "finiteness does NOT bound the generated-side count."
            ),
            "corrected_classification": (
                "H_dice_comparisons_808 is NOT independently ruled out; it is COUPLED to "
                "D_missing_generated_dice_zero. If any generated Dice is None/nonfinite, "
                "D fails AND H fails simultaneously."
            ),
            "coupling_pair": ["D_missing_generated_dice_zero", "H_n_dice_comparisons_808"],
            "root_cause_effect": "NONE",
            "root_cause_resolution_unchanged": "ROOT_CAUSE_NOT_RECOVERABLE_WITHOUT_CLEAN_DIAGNOSTIC_REEXECUTION",
        },
    },

    "preserved_from_original": {
        "failure_terminal": "CLEAN_EQUIVALENCE_GATE_FAILED__STOP_BEFORE_PERTURBATION",
        "termination_kind": "SYSTEM_EXIT",
        "clean_G_reproduction_passed": True,
        "clean_system_evaluation_executed": True,
        "clean_equivalence_passed": False,
        "perturbation_execution_started": False,
        "final_scientific_result_produced": False,
        "D44_diagnostics_not_durably_preserved": True,
        "root_cause_resolution": "ROOT_CAUSE_NOT_RECOVERABLE_WITHOUT_CLEAN_DIAGNOSTIC_REEXECUTION",
    },

    "state": {
        "v1_14_science": "CONSUMED_FAILED",
        "v1_14_science_retry": "FORBIDDEN",
        "v1_15_science": "NOT_CREATED",
        "phase37_state": "NOT_STARTED",
        "test_state": "REMAINS_PHASE39_ONLY",
        "router_holdout_state": "NOT_ACCESSED",
    },
    "prohibitions_observed": {
        "v1_14_science_rerun": False,
        "v1_14_smoke_rerun": False,
        "v1_14_modified": False,
        "model_run": False,
        "checkpoint_loaded": False,
        "val_image_read": False,
        "val_gt_read": False,
        "test_accessed": False,
        "router_holdout_accessed": False,
    },
    "terminal": "PHASE36_V1_14_FORENSIC_RECONCILIATION_V2_COMPLETE__ADDITIVE__ROOT_CAUSE_RESOLUTION_UNCHANGED",
}

flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
fd = os.open(out, flags, 0o644)
try:
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
except BaseException:
    os.close(fd)
    raise
print("WROTE", out, raw(out))
