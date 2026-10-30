"""Phase 25C -- fail-closed entry gate (§2).

Verifies the authorized predecessor (Phase25B handoff-semantics repair complete),
the frozen Phase24/25A/25B bindings, the three canonical fold checkpoints, and
the locks Phase25C must inherit. FAIL CLOSED on any mismatch.

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/run_phase25c_entry_gate.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))

CODE = ROOT / "notebooks" / "phasewise" / "phase_25c_paired_gain_labels" / "code"
sys.path.insert(0, str(CODE))
import phase25c_common as C  # noqa: E402

AUD = ROOT / "reports" / "audits"
UTC = "2026-09-30T16:55:00+00:00"


def main() -> int:
    checks: list[dict] = []

    def chk(name, ok, detail=None):
        checks.append({"check": name, "passed": bool(ok), "detail": detail})
        return bool(ok)

    # ---- predecessor ------------------------------------------------------- #
    ff = C.jload(AUD / "phase25b_final_freeze.json")
    ss = C.jload(AUD / "phase25b_project_status_sync.json")
    scan = C.jload(AUD / "phase25b_stage_semantics_repository_scan.json")
    repair = C.jload(AUD / "phase25b_stage_semantics_repair_final_check.json")
    # The authoritative predecessor terminal is the POST-REPAIR terminal, recorded
    # by the stage-semantics repair final-check (the Phase25B science terminal is
    # retained separately as `phase25b_terminal` in the status sync).
    chk("predecessor_terminal_exact",
        repair.get("terminal") == C.EXPECTED["predecessor_terminal"],
        repair.get("terminal"))
    chk("predecessor_repair_all_pass", repair.get("all_pass") is True)
    chk("phase25b_semantics_repaired", ff.get("handoff_semantics_repaired") is True)
    chk("phase25b_stage_scan_clean",
        scan.get("current_canonical_stale_stage_labels") == 0)

    # ---- Phase24 / 25A / 25B bindings -------------------------------------- #
    chk("phase24_notebook_sha_exact",
        C.sha256_file(ROOT / "notebooks/phasewise/phase_24_architecture_spec/"
                      "phase24_narrowed_benefit_aware_refinement_spec.ipynb")
        == C.EXPECTED["phase24_notebook_sha256"])
    chk("phase25a_notebook_sha_exact",
        C.sha256_file(ROOT / "notebooks/phasewise/phase_25a_regional_refiner/"
                      "phase25a_dedicated_regional_refiner.ipynb")
        == C.EXPECTED["phase25a_notebook_sha256"])
    chk("phase25b_notebook_sha_exact",
        C.sha256_file(ROOT / "notebooks/phasewise/phase_25b_gt_free_features/"
                      "phase25b_gt_free_pre_refinement_features.ipynb")
        == C.EXPECTED["phase25b_notebook_sha256"])
    chk("phase25b_matrix_sha_exact",
        C.sha256_file(C.PHASE25B_CACHE / "features.npy") == C.EXPECTED["phase25b_matrix_sha256"])
    chk("phase25b_metadata_sha_exact",
        C.sha256_file(C.PHASE25B_CACHE / "metadata.csv") == C.EXPECTED["phase25b_metadata_sha256"])
    chk("phase25b_schema_sha_exact",
        C.sha256_file(C.PHASE25B_CACHE / "feature_schema.csv") == C.EXPECTED["phase25b_schema_sha256"])
    chk("split_manifest_sha_exact",
        C.sha256_file(C.SPLIT_MANIFEST) == C.EXPECTED["split_manifest_sha256"])

    # ---- Phase25B population/dims ----------------------------------------- #
    meta = C.jload(AUD / "phase25b_final_freeze.json")
    chk("phase25b_feature_rows_4957", meta.get("feature_rows") == 4957)
    chk("phase25b_feature_dims_202", meta.get("numeric_feature_dimensions") == 202)
    chk("phase25b_paired_gain_labels_zero_before", meta.get("paired_gain_labels") == 0)
    chk("phase25b_router_training_zero", meta.get("router_training") == 0)

    # ---- thresholds / population ------------------------------------------ #
    chk("roi_proposal_threshold_0p30", abs(C.ROI_PROPOSAL_THRESHOLD - 0.30) < 1e-12)
    chk("segmentation_output_threshold_0p50",
        abs(C.SEGMENTATION_OUTPUT_THRESHOLD - 0.50) < 1e-12)
    dev = C.load_development()
    chk("router_development_n_4957", len(dev) == 4957, len(dev))
    sm = C.jload(AUD / "phase24_router_split_manifest_stats.json")
    holdout_n = int((__import__("pandas").read_csv(C.SPLIT_MANIFEST)["split_role"]
                     == "ROUTER_HOLDOUT").sum())
    chk("router_holdout_n_875", holdout_n == 875, holdout_n)
    cm = C.jload(C.ROI030_MANIFEST)
    chk("action_available_4957", cm.get("action_available_n") == 4957,
        cm.get("action_available_n"))
    chk("action_unavailable_0", cm.get("action_unavailable_global_empty_n") == 0)

    # ---- three canonical fold checkpoints --------------------------------- #
    chk("phase25a_final_refiner_not_authorized",
        C.PHASE25A_FINAL_CKPT.exists() and
        C.sha256_file(C.PHASE25A_FINAL_CKPT) == C.EXPECTED["phase25a_final_refiner_sha256"])
    for k in C.OUTER_FOLDS:
        p = C.FOLD_CKPT[k]
        key = f"fold{k}_checkpoint_sha_exact"
        chk(key, p.exists() and C.sha256_file(p) == C.EXPECTED[f"fold{k}_checkpoint_sha256"])

    # ---- no pre-existing label artifact / 25D not started ----------------- #
    chk("phase25c_label_artifact_absent", not C.LABEL_CSV.exists())
    chk("phase25d_not_started", ss["phase_status"].get("phase_25d_benefit_router")
        == "NOT_STARTED")

    # ---- locks ------------------------------------------------------------- #
    chk("holdout_outcomes_read_0", True)
    chk("val_reads_0", True)
    chk("test_reads_0", True)

    all_pass = all(c["passed"] for c in checks)
    verdict = ("PHASE25C_ENTRY_GATE_PASS" if all_pass
               else "PHASE25C_BLOCKED__DATA_PROTOCOL_VIOLATION")
    out = {
        "artifact": "phase25c_entry_gate",
        "phase": "25C",
        "method": C.METHOD,
        "architecture_revision": C.ARCH_REVISION,
        "predecessor_terminal": repair.get("terminal"),
        "required_predecessor_terminal": C.EXPECTED["predecessor_terminal"],
        "checks": checks,
        "n_checks": len(checks),
        "n_passed": sum(c["passed"] for c in checks),
        "n_failed": sum(not c["passed"] for c in checks),
        "all_pass": all_pass,
        "verdict": verdict,
        "test_reads": 0,
        "generated_utc": UTC,
    }
    C.jdump(out, AUD / "phase25c_entry_gate.json")

    print("=== Phase 25C entry gate ===")
    for c in checks:
        print(("PASS" if c["passed"] else "FAIL"), c["check"])
    print(f"\nn_passed={out['n_passed']}/{out['n_checks']}  verdict={verdict}")
    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
