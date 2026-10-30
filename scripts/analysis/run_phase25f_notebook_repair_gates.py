"""Phase 25F — POST-PHASE25F REVIEWER-NOTEBOOK COMPLIANCE REPAIR.

§0 authoritative-state entry gate, §1 scientific immutability gate, §2 preserve
the current notebook as provenance, §3 confirm the existing epoch-table defect.

Read-only with respect to every scientific artifact. No model construction, no
training, no forward/backward pass, no OOF/C9 recomputation.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase25f_spec_repair_common as C  # noqa: E402

ROOT = C.ROOT
AUD = C.AUD
TAB = C.TAB
NB = ROOT / "notebooks/phasewise/phase_25f_post_safety/phase25f_post_safety_execution.ipynb"
ARCHIVE = AUD / "phase25f_post_safety_execution_pre_compliance_repair.ipynb"

TERMINAL_OK = (
    "PHASE25F_CANONICAL_CLOSURE_REPAIRED__FULL_CV_EPOCH_NOTEBOOK_FROZEN__"
    "SCIENTIFIC_ARTIFACTS_UNCHANGED__PHASE25G_ELIGIBLE_NOT_STARTED"
)
TERMINAL_DRIFT = "PHASE25F_NOTEBOOK_COMPLIANCE_REPAIR_BLOCKED__SCIENTIFIC_ARTIFACT_DRIFT"
TERMINAL_HIST = "PHASE25F_NOTEBOOK_COMPLIANCE_REPAIR_BLOCKED__COMPLETE_HISTORY_UNAVAILABLE"
TERMINAL_DET = "PHASE25F_NOTEBOOK_COMPLIANCE_REPAIR_BLOCKED__NOTEBOOK_DETERMINISM_FAILURE"

EXPECTED_TERMINAL = (
    "PHASE25F_POST_SAFETY_EXECUTION_COMPLETE__OOF_SAFETY_PREDICTIONS_FINAL_"
    "CHECKPOINT_AND_C9_ARTIFACTS_FROZEN__PHASE25G_ELIGIBLE_NOT_STARTED"
)
OLD_NB_SHA = "d40120ab35956335e884f2b71398a4a6727e3ca3b50be788fd1d86f33e948908"
FINAL_CKPT_SHA = "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e"
OOF_SHA = "a9f63edd6d58a9a1d78a052a3e4539c6e0dd4d68bfb1c09c4c36789c441ebdee"
C9_SHA = "cde91c474bf19bb36368357ce4b38dd1cc7dad1b37d900fcec7cde6b9e72dbd1"

FOLD_COMPLETED = [36, 27, 86, 55, 43]
FOLD_BEST = [16, 7, 66, 35, 23]
FINAL_REFIT_EPOCHS = 23


def sha(p):
    return C.sha256_file(Path(p))


def notebook_inputs():
    """Extract the INPUTS dict that the canonical notebook itself binds."""
    import nbformat
    nb = nbformat.read(NB, as_version=4)
    for c in nb.cells:
        if c.cell_type == "code" and "INPUTS = {" in c.source:
            m = re.search(r"INPUTS = (\{.*?\n\})", c.source, re.S)
            if m:
                return json.loads(m.group(1))
    return {}


def scientific_artifact_map():
    """Canonical expected SHAs assembled from frozen Phase25F bindings."""
    exp = {}
    # (a) the notebook's own frozen INPUTS binding
    exp.update({k: ("notebook_inputs", v) for k, v in notebook_inputs().items()})
    # (b) checkpoint registry (CV best + final)
    for r in _read_csv(TAB / "phase25f_checkpoint_registry.csv"):
        exp[r["path"]] = ("checkpoint_registry", r["sha256"])
    # (c) closures -> history + latest state checkpoints
    base = ROOT / "experiments" / "phase25f_barr_post_safety_v1_0_seed42"
    for sub in ["cv_fold0", "cv_fold1", "cv_fold2", "cv_fold3", "cv_fold4", "final"]:
        cl = json.loads((base / sub / "run_complete.json").read_text())
        exp[f"experiments/phase25f_barr_post_safety_v1_0_seed42/{sub}/history.csv"] = (
            "closure_history_sha256", cl["history_sha256"])
        exp[f"experiments/phase25f_barr_post_safety_v1_0_seed42/{sub}/run_complete.json"] = (
            "closure_self", sha(base / sub / "run_complete.json"))
    ckpt = ROOT / "checkpoints" / "phase25f_barr_post_safety_v1_0_seed42"
    for k in range(5):
        exp[f"checkpoints/phase25f_barr_post_safety_v1_0_seed42/cv_fold{k}/state.pt"] = (
            "closure_state_sha256",
            json.loads((base / f"cv_fold{k}" / "run_complete.json").read_text())["state_checkpoint_sha256"])
    exp["checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/state.pt"] = (
        "closure_state_sha256",
        json.loads((base / "final" / "run_complete.json").read_text())["state_checkpoint_sha256"])
    # (d) the Phase25F final freeze audit bindings
    fz = json.loads((AUD / "phase25f_final_freeze.json").read_text())
    for name, rec in fz.get("audits", {}).items():
        if rec.get("sha256"):
            exp[rec["path"]] = ("final_freeze_audits", rec["sha256"])
    return exp


def _read_csv(p):
    import csv
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    # One-shot pre-repair gates: once recorded with all_pass they are frozen
    # provenance. Re-running would re-archive the (now repaired) notebook and
    # would re-audit a notebook that is no longer defective.
    prior = AUD / "phase25f_notebook_compliance_repair_entry_gate.json"
    if prior.exists():
        prev = json.loads(prior.read_text())
        if prev.get("all_pass") is True:
            print("pre-repair gates already recorded (entry gate all_pass); not re-evaluated")
            return

    # ================= §0 authoritative-state entry gate ================== #
    fz = json.loads((AUD / "phase25f_final_freeze.json").read_text())
    nb_sha = sha(NB)
    ck = json.loads((AUD / "phase25f_a7_a8_execution_guard.json").read_text())
    hist_counts = {}
    for k in range(5):
        hist_counts[k] = len(_read_csv(
            ROOT / "experiments/phase25f_barr_post_safety_v1_0_seed42" / f"cv_fold{k}" / "history.csv"))
    final_hist_rows = len(_read_csv(
        ROOT / "experiments/phase25f_barr_post_safety_v1_0_seed42/final/history.csv"))

    gate_checks = {
        "terminal_exact": (fz.get("terminal") == EXPECTED_TERMINAL),
        "final_freeze_all_pass": bool(fz.get("all_pass")),
        "phase25f_status_complete_canonical": (fz.get("phase25f_status") == "COMPLETE_CANONICAL"),
        "phase25g_status_eligible_not_started": (fz.get("phase25g_status") == "ELIGIBLE_NOT_STARTED"),
        "notebook_sha_exact": (nb_sha == OLD_NB_SHA),
        "final_checkpoint_sha_exact": (sha(ROOT / "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt") == FINAL_CKPT_SHA),
        "oof_sha_exact": (sha(ROOT / "data_cache/phase25f_barr_post_safety_v1_0/phase25f_oof_safety_predictions.csv") == OOF_SHA),
        "c9_sha_exact": (sha(TAB / "phase25f_c9_decision_manifest.csv") == C9_SHA),
        "fold_completed_epochs_exact": ([hist_counts[k] for k in range(5)] == FOLD_COMPLETED),
        "fold_best_epochs_exact": ([
            json.loads((ROOT / "experiments/phase25f_barr_post_safety_v1_0_seed42" /
                        f"cv_fold{k}" / "run_complete.json").read_text())["best_epoch"]
            for k in range(5)] == FOLD_BEST),
        "final_refit_epochs_exact": (final_hist_rows == FINAL_REFIT_EPOCHS),
        "router_holdout_reads_zero": (ck["router_holdout_reads"] == 0),
        "val808_reads_zero": (ck["VAL808_reads"] == 0),
        "test_reads_zero": (ck["TEST_reads"] == 0),
        "phase25g_started_false": (fz.get("phase25g_started") is False),
    }
    gate = {
        "artifact": "phase25f_notebook_compliance_repair_entry_gate",
        "phase": "25F",
        "classification": "NOTEBOOK_AND_EVIDENCE_PRESENTATION_REPAIR_ONLY",
        "method": C.METHOD,
        "specification_revision": C.REVISION,
        "required_terminal": EXPECTED_TERMINAL,
        "final_freeze_path": "reports/audits/phase25f_final_freeze.json",
        "final_freeze_sha256": sha(AUD / "phase25f_final_freeze.json"),
        "old_notebook_sha256": OLD_NB_SHA,
        "final_checkpoint_sha256": FINAL_CKPT_SHA,
        "oof_prediction_sha256": OOF_SHA,
        "c9_manifest_sha256": C9_SHA,
        "fold_completed_epochs": [hist_counts[k] for k in range(5)],
        "fold_best_epochs": FOLD_BEST,
        "final_refit_epochs": FINAL_REFIT_EPOCHS,
        "router_holdout_reads": 0, "VAL808_reads": 0, "TEST_reads": 0,
        "Phase25G_started": False,
        "checks": gate_checks,
        "all_pass": all(gate_checks.values()),
    }
    C.jdump(gate, AUD / "phase25f_notebook_compliance_repair_entry_gate.json")
    if not gate["all_pass"]:
        print("ENTRY GATE FAILED:", [k for k, v in gate_checks.items() if not v])
        sys.exit(1)

    # ================= §1 scientific immutability gate =================== #
    exp_map = scientific_artifact_map()
    drift, missing = [], []
    for rel, (src, want) in sorted(exp_map.items()):
        p = ROOT / rel
        if not p.exists():
            missing.append(rel)
            continue
        got = sha(p)
        if got != want:
            drift.append({"path": rel, "expected": want, "observed": got, "source": src})
    # frozen Phase25E predecessors
    p25e = json.loads((AUD / "phase25e_final_freeze.json").read_text())
    p25e_bound = {}
    for name, rec in p25e.get("audits", {}).items():
        if rec.get("sha256"):
            rel = name if name.endswith(".json") else f"reports/audits/{name}.json"
            p25e_bound[rel] = rec["sha256"]
    p25e_drift = []
    for rel, want in sorted(p25e_bound.items()):
        p = ROOT / rel
        if not p.exists() or sha(p) != want:
            p25e_drift.append(rel)
    # C8 membership manifest (bound by the C9 scope guard)
    c9g = json.loads((AUD / "phase25f_c9_scope_guard.json").read_text())
    c8_rel = "reports/tables/phase25e_policy_membership_manifest.csv"
    c8_ok = (sha(ROOT / c8_rel) == c9g["c8_membership_manifest_sha256"])

    imm_checks = {
        "all_bound_artifacts_present": len(missing) == 0,
        "zero_scientific_artifact_drift": len(drift) == 0,
        "phase25e_predecessors_unchanged": len(p25e_drift) == 0,
        "c8_membership_manifest_unchanged": c8_ok,
    }
    imm = {
        "artifact": "phase25f_notebook_compliance_repair_scientific_immutability_gate",
        "phase": "25F",
        "classification": "NOTEBOOK_AND_EVIDENCE_PRESENTATION_REPAIR_ONLY",
        "method": C.METHOD,
        "specification_revision": C.REVISION,
        "bound_artifact_count": len(exp_map),
        "missing_artifacts": missing,
        "drift": drift,
        "phase25e_predecessor_count": len(p25e_bound),
        "phase25e_predecessor_drift": p25e_drift,
        "checks": imm_checks,
        "all_pass": all(imm_checks.values()),
        "terminal_on_failure": TERMINAL_DRIFT,
    }
    C.jdump(imm, AUD / "phase25f_notebook_compliance_repair_scientific_immutability_gate.json")
    if not imm["all_pass"]:
        print("SCIENTIFIC DRIFT:", drift[:5], missing[:5], p25e_drift[:5])
        sys.exit(1)

    # ================= §2 preserve notebook as provenance ================ #
    if ARCHIVE.exists():
        arch_sha = sha(ARCHIVE)
    else:
        shutil.copyfile(NB, ARCHIVE)
        arch_sha = sha(ARCHIVE)
    prov = {
        "artifact": "phase25f_notebook_pre_compliance_repair_provenance",
        "phase": "25F",
        "classification": "PRE_NOTEBOOK_COMPLIANCE_REPAIR_PROVENANCE",
        "method": C.METHOD,
        "specification_revision": C.REVISION,
        "original_path": "notebooks/phasewise/phase_25f_post_safety/phase25f_post_safety_execution.ipynb",
        "archive_path": "reports/audits/phase25f_post_safety_execution_pre_compliance_repair.ipynb",
        "original_sha256": OLD_NB_SHA,
        "archive_sha256": arch_sha,
        "archive_sha_matches_exactly": (arch_sha == OLD_NB_SHA),
        "deleted": False,
        "all_pass": (arch_sha == OLD_NB_SHA),
    }
    C.jdump(prov, AUD / "phase25f_notebook_pre_compliance_repair_provenance.json")
    assert prov["all_pass"], "archived notebook SHA mismatch"

    # ================= §3 confirm the existing defect ==================== #
    import nbformat
    nb = nbformat.read(NB, as_version=4)
    per_fold = {}
    for k in range(5):
        src = None
        rows = None
        for c in nb.cells:
            if c.cell_type == "code" and f"cv_fold{k}/history.csv" in c.source:
                src = c.source
                for o in c.get("outputs", []):
                    h = o.get("data", {}).get("text/html")
                    if h:
                        m = re.search(r"<tbody>(.*?)</tbody>", h, re.S)
                        rows = m.group(1).count("<tr") if m else None
        per_fold[k] = {"uses_tail": bool(src and ".tail(" in src),
                       "visible_rows": rows,
                       "true_rows": hist_counts[k]}
    defect = all(v["uses_tail"] for v in per_fold.values()) and all(
        v["visible_rows"] == 8 for v in per_fold.values())
    audit = {
        "artifact": "phase25f_existing_notebook_epoch_table_compliance_audit",
        "phase": "25F",
        "classification": "PHASE25F_SCIENCE_ACCEPTED__REVIEWER_NOTEBOOK_CV_HISTORY_TRUNCATED",
        "method": C.METHOD,
        "specification_revision": C.REVISION,
        "scientific_failure": False,
        "presentation_compliance_failure": True,
        "per_fold": per_fold,
        "expected_completed_histories": {"fold0": 36, "fold1": 27, "fold2": 86,
                                         "fold3": 55, "fold4": 43},
        "expected_best_epochs": FOLD_BEST,
        "expected_terminations": ["early_stop"] * 5,
        "final_refit_rows": final_hist_rows,
        "final_refit_complete": (final_hist_rows == FINAL_REFIT_EPOCHS),
        "defect_confirmed": bool(defect),
        "truncated_folds": [k for k, v in per_fold.items() if v["visible_rows"] != v["true_rows"]],
        "all_pass": bool(defect),
    }
    C.jdump(audit, AUD / "phase25f_existing_notebook_epoch_table_compliance_audit.json")

    print(f"§0 entry gate: {gate['all_pass']} (terminal exact, locks 0)")
    print(f"§1 immutability: {imm['all_pass']} ({len(exp_map)} artifacts, 0 drift, "
          f"{len(p25e_bound)} Phase25E predecessors)")
    print(f"§2 provenance archived: {prov['all_pass']} -> {ARCHIVE.name}")
    print(f"§3 defect confirmed: {audit['defect_confirmed']} "
          f"(truncated folds {audit['truncated_folds']})")
    return gate, imm, prov, audit


if __name__ == "__main__":
    main()
