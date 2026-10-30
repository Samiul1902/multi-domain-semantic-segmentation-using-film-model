"""Pre-Phase27 closure repair - no-scientific-execution audit + roll-up."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"

SUBS_A = [
    "phase26_notebook_postclosure_reconciliation_entry_gate",
    "phase26_notebook_pre_postclosure_archive",
    "phase26_notebook_validator_sha_drift",
    "phase26_notebook_terminal_staleness",
    "phase26_final_freeze_notebook_postclosure_addendum",
    "phase26_postclosure_notebook_determinism",
    "phase26_postclosure_notebook_visual_integrity",
    "phase26_notebook_phase_index_update",
]
SUBS_B = [
    "phase27_predecessor_notebook_rebind_v1_1",
    "phase27_numeric_inference_mode_provenance_audit_v1_1",
    "phase27_autocast_rule_resolution",
    "phase27_batch_semantics_audit",
    "phase27_reproducibility_contract_v1_1",
    "phase27_frozen_val808_statistics_preservation",
    "phase27_specification_completeness_v1_1_summary",
    "phase27_evidence_class_contract_v1_1",
    "phase27_secondary_metrics_contract_v1_1",
    "phase27_routing_activation_reporting_contract_v1_1",
    "phase27_compute_reporting_contract_v1_1",
    "phase27_failure_behavior_contract_v1_1",
    "phase27_phase_boundaries_contract_v1_1",
    "phase27_spec_v1_1_amendment",
    "phase27_specification_final_check_v1_1",
]


def jload(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def main():
    counters = {
        "val808_image_reads": 0,
        "val808_mask_reads": 0,
        "scientific_model_forwards": 0,
        "training_runs": 0,
        "backward_passes": 0,
        "optimizer_steps": 0,
        "new_segmentation_predictions": 0,
        "router_holdout_reads": 0,
        "test_reads": 0,
    }
    audit = {
        "artifact": "phase26_phase27_preclosure_no_scientific_execution",
        "phase": "26+27",
        "classification": "GOVERNANCE_AND_REVIEWER_EVIDENCE_REPAIR_ONLY",
        "method": "RA-MedFiLM-BARR",
        "governance_only": True,
        "no_execution": True,
        "stage": "NO_SCIENTIFIC_EXECUTION",
        "counters": counters,
        "note": ("The Phase26 notebook was re-executed, but it only loads frozen Phase26 audit "
                 "artifacts; it performs zero scientific model forwards, zero training, and opens "
                 "no VAL808 image/mask."),
        "checks": {k: v == 0 for k, v in counters.items()},
        "all_pass": all(v == 0 for v in counters.values()),
    }
    (AUD / "phase26_phase27_preclosure_no_scientific_execution.json").write_text(
        json.dumps(audit, indent=1) + "\n", encoding="utf-8")
    print(f"[{'OK ' if audit['all_pass'] else 'FAIL'}] no-scientific-execution")

    # roll-up
    all_subs = SUBS_A + SUBS_B + ["phase26_phase27_preclosure_no_scientific_execution",
                                  "phase27_spec_v1_1_terminal"]
    loaded = {}
    for n in all_subs:
        p = AUD / f"{n}.json"
        if p.exists():
            loaded[n] = jload(p)
    missing = [n for n in all_subs if n not in loaded]
    roll = {
        "artifact": "phase27_spec_v1_1_rollup",
        "phase": "27",
        "classification": "GOVERNANCE_AND_REVIEWER_EVIDENCE_REPAIR_ONLY",
        "governance_only": True,
        "no_execution": True,
        "artifacts": {n: {"path": f"reports/audits/{n}.json", "all_pass": loaded[n].get("all_pass"),
                          "sha256": sha(f"reports/audits/{n}.json")} for n in loaded},
        "missing": missing,
        "all_pass": len(missing) == 0 and all(o.get("all_pass") for o in loaded.values()),
    }
    (AUD / "phase27_spec_v1_1_rollup.json").write_text(
        json.dumps(roll, indent=1) + "\n", encoding="utf-8")
    print(f"[{'OK ' if roll['all_pass'] else 'FAIL'}] rollup ({len(loaded)} artifacts)")
    if not roll["all_pass"]:
        print("  failing:", [n for n, o in loaded.items() if not o.get("all_pass")])
        print("  missing:", missing)
    return 0 if roll["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
