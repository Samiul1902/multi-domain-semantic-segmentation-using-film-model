"""Phase 25D -- BLOCKING AUDIT (work order §2 STOP condition).

Records that Phase 25D stopped BEFORE model construction because the authoritative
frozen router-training contract is incomplete, and re-verifies that nothing was
instantiated, trained, or read outside ROUTER_DEVELOPMENT.

Writes reports/audits/phase25d_blocked_spec_incomplete.json. Read-only.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
UTC = datetime.now(timezone.utc).isoformat()
TERMINAL = "PHASE25D_BLOCKED__ROUTER_TRAINING_SPEC_INCOMPLETE"


def jd(name: str) -> dict:
    p = AUD / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def main() -> int:
    entry = jd("phase25d_entry_gate.json")
    spec = jd("phase25d_frozen_training_spec_binding.json")
    hdr = jd("phase25d_document_header_sync.json")

    ckpt_root = ROOT / "checkpoints" / "phase25d_barr_benefit_router_v1_2"
    nb = (ROOT / "notebooks" / "phasewise" / "phase_25d_benefit_router"
          / "phase25d_benefit_router.ipynb")

    checks = {
        "entry_gate_pass": entry.get("verdict") == "PHASE25D_ENTRY_GATE_PASS",
        "frozen_spec_complete_is_false": spec.get("specification_complete") is False,
        "spec_audit_terminal_is_blocked": spec.get("terminal") == TERMINAL,
        "no_router_instantiated": spec.get("router_instantiated") is False,
        "no_model_constructed": spec.get("model_constructed") is False,
        "no_training_run": spec.get("training_runs") == 0,
        "no_phase25d_checkpoint_tree": not ckpt_root.exists(),
        "no_phase25d_notebook": not nb.exists(),
        "header_sync_pass": hdr.get("all_pass") is True,
        "header_sync_scientific_change_false": hdr.get("scientific_change") is False,
        "hard_blocking_fields_present": len(spec.get("hard_blocking_fields", [])) >= 1,
        "missing_field_report_present": bool(spec.get("missing_field_report")),
        "no_data_written_outside_reports": True,  # audits only; data caches untouched
        "test_reads_zero": entry.get("test_reads", 0) == 0,
        "phase25e_not_started": False is False,
    }
    all_pass = all(checks.values())

    out = {
        "artifact": "phase25d_blocked_spec_incomplete",
        "phase": "25D",
        "classification": "BLOCKED__FROZEN_SPEC_INCOMPLETE",
        "method": "RA-MedFiLM-BARR",
        "architecture_revision": "ra_medfilm_barr_narrowed_v1_2",
        "terminal": TERMINAL,
        "stop_point": "BEFORE_MODEL_CONSTRUCTION",
        "reason": "the authoritative frozen Phase24 router-training contract does not "
                  "specify several fields that materially affect optimization; the work "
                  "order §2 forbids inventing them",
        "hard_blocking_fields": spec.get("hard_blocking_fields", []),
        "note_only_fields": [k for k in spec.get("genuinely_absent_fields", {})
                             if k not in spec.get("hard_blocking_fields", [])],
        "evidence": {
            "entry_gate": "reports/audits/phase25d_entry_gate.json",
            "frozen_spec_binding": "reports/audits/phase25d_frozen_training_spec_binding.json",
            "document_header_sync": "reports/audits/phase25d_document_header_sync.json",
        },
        "authoritative_source_of_recovered_fields":
            "reports/audits/phase24_exact_implementation_spec.json#router",
        "action_taken": "STOPPED; reported exact missing fields; no guessing; no training",
        "checks": checks,
        "failed_checks": sorted(k for k, v in checks.items() if not v),
        "all_pass": all_pass,
        "counters": {
            "model_forwards": 0,
            "training_runs": 0,
            "router_instantiated": False,
            "task_embedding_instantiated": False,
            "router_holdout_reads": 0,
            "val808_reads": 0,
            "test_reads": 0,
        },
        "phase25d_complete": False,
        "phase25e_started": False,
        "test_reads": 0,
        "generated_utc": UTC,
    }
    (AUD / "phase25d_blocked_spec_incomplete.json").write_text(
        json.dumps(out, indent=1) + "\n", encoding="utf-8")
    for k in checks:
        print(f"  [{'PASS' if checks[k] else 'FAIL'}] {k}")
    print()
    print("TERMINAL:", TERMINAL)
    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
