"""Phase 25F — POST-SAFETY SPECIFICATION REPAIR  §0 REQUIRED BLOCKED PREDECESSOR.

Fail-closed entry gate. Verifies the clean blocked Phase25F predecessor and the
reconciled Phase25E closure before any repair work is allowed. Performs no
model construction / training / forward pass / refinement / DeltaDice.

Output: reports/audits/phase25f_spec_repair_entry_gate.json
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))
import phase25f_spec_repair_common as C  # noqa: E402


def main() -> int:
    checks: dict[str, bool] = {}
    failures: list[str] = []

    def chk(name: str, cond: bool, detail=None):
        checks[name] = bool(cond)
        if not cond:
            failures.append(name if detail is None else f"{name}: {detail}")

    # ---- blocked Phase25F predecessor -------------------------------------- #
    blocked_path = C.AUD / "phase25f_specification_final_check.json"
    blocked = C.jload(blocked_path)
    chk("blocked_audit_present", blocked_path.exists())
    chk("blocked_terminal_exact",
        blocked.get("terminal") == C.PHASE25F_BLOCKED_TERMINAL,
        blocked.get("terminal"))
    chk("phase25f_spec_complete_false", blocked.get("phase25f_spec_complete") is False)
    chk("phase25f_execution_status_blocked",
        blocked.get("phase25f_execution_status") == "BLOCKED__SPEC_INCOMPLETE",
        blocked.get("phase25f_execution_status"))
    chk("blocking_field_count_54",
        blocked.get("blocking_field_count") == C.EXPECTED_BLOCKING_FIELD_COUNT,
        blocked.get("blocking_field_count"))
    chk("hard_stop_triggered_count_12",
        blocked.get("hard_stop_triggered_count") == C.EXPECTED_HARD_STOP_COUNT,
        blocked.get("hard_stop_triggered_count"))

    # ---- blocked-state execution counters ---------------------------------- #
    chk("model_constructed_false", blocked.get("model_constructed") is False)
    chk("training_runs_zero", blocked.get("training_runs") == 0)
    chk("forward_passes_zero", blocked.get("forward_passes") == 0)
    chk("new_refinement_false", blocked.get("new_refinement") is False)
    chk("new_delta_dice_false", blocked.get("new_delta_dice") is False)
    chk("router_holdout_reads_zero", blocked.get("router_holdout_reads") == 0)
    chk("val808_reads_zero", blocked.get("val808_reads") == 0)
    chk("test_reads_zero", blocked.get("test_reads") == 0)
    chk("phase25g_started_false", blocked.get("phase25g_started") is False)
    chk("no_phase25f_notebook",
        blocked.get("no_phase25f_scientific_notebook_created") is True)

    # ---- reconciled Phase25E predecessor ----------------------------------- #
    recon_path = C.AUD / "phase25e_postclosure_reconciliation_final_check.json"
    recon = C.jload(recon_path)
    chk("phase25e_recon_final_check_present", recon_path.exists())
    chk("phase25e_reconciled_terminal_exact",
        recon.get("terminal") == C.PHASE25E_RECONCILED_TERMINAL,
        recon.get("terminal"))
    chk("phase25e_phase25f_status_eligible",
        recon.get("phase25f_status") == "ELIGIBLE_NOT_STARTED",
        recon.get("phase25f_status"))

    # ---- reconciled Phase25E notebook SHA ---------------------------------- #
    nb_path = ROOT / "notebooks" / "phasewise" / "phase_25e_resource_gate" / "phase25e_resource_gate.ipynb"
    nb_sha = C.sha256_file(nb_path) if nb_path.exists() else None
    chk("phase25e_reconciled_notebook_sha_exact",
        nb_sha == C.PHASE25E_RECONCILED_NOTEBOOK_SHA, nb_sha)

    # ---- immutable Phase25E final freeze ----------------------------------- #
    ff_path = C.AUD / "phase25e_final_freeze.json"
    ff_sha = C.sha256_file(ff_path) if ff_path.exists() else None
    chk("phase25e_final_freeze_sha_immutable",
        ff_sha == C.PHASE25E_FINAL_FREEZE_SHA, ff_sha)

    # ---- Phase25C canonical source binding --------------------------------- #
    chk("phase25c_label_csv_sha_exact",
        C.sha256_file(C.PHASE25C_LABEL_CSV) == C.PHASE25C_LABEL_CSV_SHA)
    chk("phase25c_writer_present", C.PHASE25C_WRITER.exists())
    chk("phase25c_common_present", C.PHASE25C_COMMON.exists())
    for d in C.DOMAINS:
        chk(f"roi030_cache_{d}_prob512_present",
            (C.ROI030_CACHE / d / "prob512.npy").exists())
        chk(f"roi030_cache_{d}_meta_present",
            (C.ROI030_CACHE / d / "meta.csv").exists())
        chk(f"phase25c_tmp_refined_{d}_present",
            (C.PHASE25C_DIR / f"_tmp_refined_crop_prob_{d}.npy").exists())

    # ---- Phase25D CV identity manifests ------------------------------------ #
    chk("phase25d_cv5_manifest_present", C.PHASE25D_CV5_MANIFEST.exists())
    for k in range(5):
        for role, p in C.PHASE25D_CV_FOLD[k].items():
            chk(f"phase25d_fold{k}_{role}_present", p.exists())

    # ---- blocked-attempt provenance snapshot (baseline for §34) ------------- #
    # Pinned to the Work Order F artifacts only (never the repair's own outputs).
    blocked_artifacts: dict[str, str] = {}
    for rel in C.BLOCKED_ATTEMPT_ARTIFACTS:
        p = ROOT / rel
        if p.exists():
            blocked_artifacts[rel] = C.sha256_file(p)
    chk("blocked_attempt_artifacts_captured",
        len(blocked_artifacts) == len(C.BLOCKED_ATTEMPT_ARTIFACTS),
        f"{len(blocked_artifacts)}/{len(C.BLOCKED_ATTEMPT_ARTIFACTS)}")

    # ---- informational: repair-cache state (NOT a pass/fail precondition) --- #
    # The gate is idempotent: it validates the frozen blocked predecessor every
    # time it runs. Whether the repair cache already exists is recorded for
    # provenance only, so a post-repair re-run does not spuriously fail.
    cache25f_present = C.CACHE25F.exists()

    out = {
        "artifact": "phase25f_spec_repair_entry_gate",
        "phase": "25F",
        "stage": "SPEC_REPAIR_ENTRY_GATE",
        "method": C.METHOD,
        "classification": C.CLASSIFICATION,
        "specification_revision": C.REVISION,
        "required_blocked_terminal": C.PHASE25F_BLOCKED_TERMINAL,
        "observed_blocked_terminal": blocked.get("terminal"),
        "blocking_field_count": blocked.get("blocking_field_count"),
        "hard_stop_triggered_count": blocked.get("hard_stop_triggered_count"),
        "predecessor_bindings": {
            "phase25f_specification_final_check": C.bind(blocked_path),
            "phase25e_postclosure_reconciliation_final_check": C.bind(recon_path),
            "phase25e_resource_gate_notebook": {"path": str(nb_path.relative_to(ROOT)).replace("\\", "/"),
                                                "sha256": nb_sha},
            "phase25e_final_freeze": {"path": str(ff_path.relative_to(ROOT)).replace("\\", "/"),
                                      "sha256": ff_sha},
        },
        "phase25c_source_bindings": {
            "label_csv": C.bind(C.PHASE25C_LABEL_CSV),
            "writer": C.bind(C.PHASE25C_WRITER),
            "common": C.bind(C.PHASE25C_COMMON),
        },
        "blocked_attempt_artifacts": blocked_artifacts,
        "blocked_attempt_artifact_count": len(blocked_artifacts),
        "cache25f_present_at_gate_time": cache25f_present,
        "no_execution_invariants": {
            "model_constructed": False,
            "training_runs": 0,
            "forward_passes": 0,
            "new_refinement": False,
            "new_delta_dice": False,
            "router_holdout_reads": 0,
            "val808_reads": 0,
            "test_reads": 0,
            "phase25g_started": False,
        },
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "failures": failures,
        "all_pass": len(failures) == 0,
    }
    C.jdump(out, C.AUD / "phase25f_spec_repair_entry_gate.json")
    print(f"entry gate: {out['checks_passed']}/{out['checks_total']} pass")
    if failures:
        print("FAILURES:", failures)
        return 1
    print("ENTRY_GATE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
