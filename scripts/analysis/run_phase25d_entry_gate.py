"""Phase 25D -- fail-closed ENTRY GATE (work order §1).

Verifies the authorized predecessor state and the exact frozen Phase25B / Phase25C
artifacts BEFORE any Phase25D construction. Fail-closed: any scientific/provenance
mismatch aborts with a BLOCKED terminal.

Writes reports/audits/phase25d_entry_gate.json. Read-only: no model, no training,
no data mutation.

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/run_phase25d_entry_gate.py
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
UTC = datetime.now(timezone.utc).isoformat()

GOV_TERMINAL = ("PHASE25C_GOVERNANCE_CLEANUP_COMPLETE"
                "__PHASE25D_BENEFIT_ROUTER_ELIGIBLE_NOT_STARTED")
SCI_TERMINAL = ("PHASE25C_OOF_PAIRED_REFINEMENT_GAIN_LABELS_COMPLETE"
                "__PHASE25D_BENEFIT_ROUTER_ELIGIBLE_NOT_STARTED")

EXPECT = {
    "phase25b_notebook": "acdfe90a5042ef364c5ab28ec67ecd3fe3146b30e1e5715a2631a36deb4dc38a",
    "phase25b_matrix": "9c241963b54f23de1c9671ff6670dde7d6f7e2510869ef5ebc1baf3f7c833e0a",
    "phase25b_metadata": "ee8c304350d28d907c053a355da1f878ff7f9dd137761034283459aeed071093",
    "phase25b_schema": "da76aa34f14006146f46ca799f173378274d8c9d0792dc18edb30711a2486dd4",
    "phase25c_notebook": "564105eabfdb4cfb12613ca65cab7dc0c4410bea667239e5c1302e15060db613",
    "phase25c_label": "fd6ca32c33a3bddb75f986b1350d54ec35b11d3bf5cb0fdc029962a5aa94865f",
}
B = ROOT / "data_cache" / "phase25b_barr_pre_refinement_features_v1_2"
LABEL = (ROOT / "data_cache" / "phase25c_barr_oof_paired_gain_labels_v1_2"
         / "phase25c_oof_paired_gain_labels.csv")


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def jd(name: str) -> dict:
    p = AUD / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def main() -> int:
    gov = jd("phase25c_governance_cleanup.json")
    sci = jd("phase25c_final_freeze.json")

    meta = list(csv.DictReader((B / "metadata.csv").open(encoding="utf-8", newline="")))
    labels = list(csv.DictReader(LABEL.open(encoding="utf-8", newline="")))
    try:
        from phase25d_common import numeric_dim  # type: ignore
        ndim = numeric_dim()
    except Exception:
        import re  # fall back to schema width
        schema_rows = list(csv.reader((B / "feature_schema.csv").open(encoding="utf-8")))
        ndim = len(schema_rows) - 1 if schema_rows else -1

    b_ids = {r["sample_id"] for r in meta}
    c_ids = {r["sample_id"] for r in labels}
    fri = {r["sample_id"]: r.get("feature_row_index") for r in meta}
    fri_label = {r["sample_id"]: r.get("feature_row_index") for r in labels}
    tasks = sorted({r.get("task_id") for r in meta})
    delta_finite = all(
        (r.get("delta_dice") not in (None, "", "nan", "NaN", "inf", "-inf"))
        and float(r["delta_dice"]) == float(r["delta_dice"])
        for r in labels)

    checks = {
        "governance_terminal_exact": gov.get("terminal") == GOV_TERMINAL,
        "phase25c_scientific_terminal_exact": sci.get("terminal") == SCI_TERMINAL,
        "governance_cleanup_all_pass": gov.get("all_pass") is True,
        "phase25d_started_false": gov.get("Phase25D_started") is False,
        "no_existing_phase25d_checkpoint_tree":
            not (ROOT / "checkpoints" / "phase25d_barr_benefit_router_v1_2").exists(),
        "no_existing_phase25d_notebook":
            not (ROOT / "notebooks" / "phasewise" / "phase_25d_benefit_router"
                 / "phase25d_benefit_router.ipynb").exists(),
        "phase25b_matrix_sha_exact": sha(B / "features.npy") == EXPECT["phase25b_matrix"],
        "phase25b_metadata_sha_exact": sha(B / "metadata.csv") == EXPECT["phase25b_metadata"],
        "phase25b_schema_sha_exact": sha(B / "feature_schema.csv") == EXPECT["phase25b_schema"],
        "phase25c_label_sha_exact": sha(LABEL) == EXPECT["phase25c_label"],
        "phase25b_notebook_sha_exact":
            sha(ROOT / "notebooks/phasewise/phase_25b_gt_free_features"
                / "phase25b_gt_free_pre_refinement_features.ipynb")
            == EXPECT["phase25b_notebook"],
        "phase25c_notebook_sha_exact":
            sha(ROOT / "notebooks/phasewise/phase_25c_paired_gain_labels"
                / "phase25c_oof_paired_refinement_gain.ipynb")
            == EXPECT["phase25c_notebook"],
        "phase25b_rows_4957": len(meta) == 4957,
        "phase25c_rows_4957": len(labels) == 4957,
        "phase25b_numeric_dims_202": ndim == 202,
        "phase25c_unique_sample_ids_4957": len(c_ids) == 4957,
        "phase25b_unique_sample_ids_4957": len(b_ids) == 4957,
        "exact_sample_id_equality": b_ids == c_ids,
        "feature_row_index_alignment": all(
            fri.get(sid) == fri_label.get(sid) for sid in (b_ids & c_ids)),
        "task_id_available": all(r.get("task_id") not in (None, "") for r in meta),
        "four_task_ids_only": len(tasks) == 4,
        "delta_dice_finite": delta_finite,
        "nan_zero": all(r.get("delta_dice", "").lower() != "nan" for r in labels),
        "inf_zero": all(r.get("delta_dice", "").lower() not in ("inf", "-inf")
                        for r in labels),
        "phase25a_frozen_unchanged":
            sci.get("frozen_predecessor_sha_still_match", {}).get("all_match") is True,
        "router_holdout_reads_zero": sci.get("router_holdout_reads", 0) == 0,
        "val808_reads_zero": sci.get("val808_reads", 0) == 0,
        "test_reads_zero": sci.get("test_reads", 0) == 0,
        "phase25e_not_started": sci.get("phase25e_status") == "NOT_STARTED",
    }
    all_pass = all(checks.values())
    failed = sorted(k for k, v in checks.items() if not v)

    out = {
        "artifact": "phase25d_entry_gate",
        "phase": "25D",
        "classification": "FAIL_CLOSED_ENTRY_GATE",
        "method": "RA-MedFiLM-BARR",
        "architecture_revision": "ra_medfilm_barr_narrowed_v1_2",
        "master_development_seed": 42,
        "governance_terminal": gov.get("terminal"),
        "phase25c_scientific_terminal": sci.get("terminal"),
        "router_development_n": 4957,
        "router_holdout_n": 875,
        "phase25b_notebook_sha256": sha(
            ROOT / "notebooks/phasewise/phase_25b_gt_free_features"
            / "phase25b_gt_free_pre_refinement_features.ipynb"),
        "phase25b_matrix_sha256": sha(B / "features.npy"),
        "phase25b_metadata_sha256": sha(B / "metadata.csv"),
        "phase25b_schema_sha256": sha(B / "feature_schema.csv"),
        "phase25c_notebook_sha256": sha(
            ROOT / "notebooks/phasewise/phase_25c_paired_gain_labels"
            / "phase25c_oof_paired_refinement_gain.ipynb"),
        "phase25c_label_sha256": sha(LABEL),
        "phase25b_rows": len(meta),
        "phase25c_rows": len(labels),
        "phase25b_numeric_dims": ndim,
        "task_ids": tasks,
        "checks": checks,
        "failed_checks": failed,
        "all_pass": all_pass,
        "verdict": ("PHASE25D_ENTRY_GATE_PASS" if all_pass
                    else "PHASE25D_BLOCKED__ROUTER_DATA_PROTOCOL_VIOLATION"),
        "test_reads": 0,
        "generated_utc": UTC,
    }
    (AUD / "phase25d_entry_gate.json").write_text(json.dumps(out, indent=1) + "\n",
                                                  encoding="utf-8")
    for k in checks:
        print(f"  [{'PASS' if checks[k] else 'FAIL'}] {k}")
    print()
    print("VERDICT:", out["verdict"])
    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
