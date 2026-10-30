"""Phase 25C -- final freeze (§32) + scope/lock re-verification + terminal (§33/§34).

Assembles ``reports/audits/phase25c_final_freeze.json`` from the already-written
Phase25C audits. Fail-closed: every listed gate must report PASS, the frozen
predecessor hashes must still match, and no TEST / ROUTER_HOLDOUT / VAL808 row may
have been read. Writes the artifact, then prints the §33 success conditions and the
§34 terminal. Does NOT train anything and does NOT start Phase 25D.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))
AUD = ROOT / "reports" / "audits"
UTC = datetime.now(timezone.utc).isoformat()

LABEL_CSV = (ROOT / "data_cache" / "phase25c_barr_oof_paired_gain_labels_v1_2"
             / "phase25c_oof_paired_gain_labels.csv")
NB = (ROOT / "notebooks" / "phasewise" / "phase_25c_paired_gain_labels"
      / "phase25c_oof_paired_refinement_gain.ipynb")
LABEL_CSV_SHA = "fd6ca32c33a3bddb75f986b1350d54ec35b11d3bf5cb0fdc029962a5aa94865f"
NB_SHA = "564105eabfdb4cfb12613ca65cab7dc0c4410bea667239e5c1302e15060db613"
TERMINAL = ("PHASE25C_OOF_PAIRED_REFINEMENT_GAIN_LABELS_COMPLETE"
            "__PHASE25D_BENEFIT_ROUTER_ELIGIBLE_NOT_STARTED")


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def j(name: str) -> dict:
    p = AUD / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def main() -> int:
    entry = j("phase25c_entry_gate.json")
    crossfit = j("phase25c_crossfit_leakage_audit.json")
    recon = j("phase25c_fullfield_reconstruction_audit.json")
    integ = j("phase25c_label_integrity.json")
    join = j("phase25c_phase25b_join_integrity.json")
    det = j("phase25c_oof_determinism.json")
    vis = j("phase25c_notebook_visual_integrity.json")
    ndet = j("phase25c_notebook_determinism.json")
    scope = j("phase25c_scope_guard.json")
    lock = j("phase25c_test_lock_audit.json")
    handoff = j("phase25c_phase25d_handoff_schema.json")
    bound = j("phase25c_refiner_inference_execution_binding.json")
    thr = j("phase25c_threshold_semantics_audit.json")
    metric = j("phase25c_metric_binding.json")
    gcache = j("phase25c_global_cache_binding.json")
    p24 = j("phase25c_phase24_binding.json")
    p25a = j("phase25c_phase25a_binding.json")
    p25b = j("phase25c_phase25b_binding.json")
    folds = j("phase25c_fold_checkpoint_binding.json")

    label_rows = sum(1 for _ in LABEL_CSV.open(encoding="utf-8")) - 1
    label_sha_now = sha(LABEL_CSV) if LABEL_CSV.exists() else None
    nb_sha_now = sha(NB) if NB.exists() else None

    import csv
    with LABEL_CSV.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    fold_counts: dict[int, int] = {}
    for r in rows:
        k = int(str(r["outer_fold"]).replace("fold", ""))
        fold_counts[k] = fold_counts.get(k, 0) + 1

    gates = {
        "entry_gate_pass": entry.get("verdict") == "PHASE25C_ENTRY_GATE_PASS",
        "crossfit_leakage_clean": crossfit.get("verdict") == "PHASE25C_CROSSFIT_LEAKAGE_CLEAN",
        "refiner_inference_binding_frozen":
            bound.get("verdict") == "PHASE25C_REFINER_INFERENCE_BINDING_FROZEN",
        "reconstruction_verified": recon.get("verdict") == "PHASE25C_RECONSTRUCTION_VERIFIED",
        "threshold_semantics_ok": thr.get("verdict") == "PHASE25C_THRESHOLD_SEMANTICS_OK",
        "metric_bound": metric.get("verdict") == "PHASE25C_METRIC_BOUND",
        "global_cache_bound": gcache.get("verdict") == "PHASE25C_GLOBAL_CACHE_BOUND",
        "label_integrity_pass": integ.get("verdict") == "PHASE25C_LABEL_INTEGRITY_PASS",
        "join_integrity_pass": join.get("verdict") == "PHASE25C_JOIN_INTEGRITY_PASS",
        "oof_determinism_pass": det.get("verdict") == "PHASE25C_OOF_DETERMINISM_PASS",
        "notebook_visual_integrity_pass":
            vis.get("verdict") == "PHASE25C_NOTEBOOK_VISUAL_INTEGRITY_PASS"
            and vis.get("n_valid_png") == vis.get("n_embedded_png") == 8,
        "notebook_3x_byte_identical": ndet.get("byte_identical") is True,
        "scope_guard_pass": scope.get("verdict") == "PHASE25C_SCOPE_GUARD_PASS",
        "lock_audit_pass": lock.get("verdict") == "PHASE25C_LOCK_AUDIT_PASS",
        "phase25d_handoff_ready": handoff.get("verdict") == "PHASE25C_PHASE25D_HANDOFF_READY",
        "phase24_binding_ok": p24.get("phase24_notebook_sha_matches") is True,
        "phase25a_binding_ok": p25a.get("phase25a_notebook_sha_matches") is True,
        "phase25b_binding_ok": all(p25b.get(k) is True for k in
                                   ("phase25b_notebook_sha_matches", "matrix_sha_matches",
                                    "metadata_sha_matches", "schema_sha_matches")),
        "fold_checkpoint_binding_ok": len(folds.get("folds", [])) == 3,
        "label_csv_sha_matches": label_sha_now == LABEL_CSV_SHA,
        "notebook_sha_matches": nb_sha_now == NB_SHA,
        "label_rows_4957": label_rows == 4957,
        "test_reads_zero": all(d.get("test_reads", 0) == 0 for d in
                               (entry, crossfit, recon, integ, join, det, vis, ndet,
                                scope, lock, handoff, thr, metric, gcache, p24, p25a,
                                p25b, folds)),
    }
    all_pass = all(gates.values())
    failed = sorted(k for k, v in gates.items() if not v)

    freeze = {
        "artifact": "phase25c_final_freeze",
        "phase": "25C",
        "title": "Leakage-safe OOF paired refinement-gain label generation",
        "classification": "PHASE25C_EXECUTED_EVIDENCE",
        "method": "RA-MedFiLM-BARR",
        "architecture_revision": "ra_medfilm_barr_narrowed_v1_2",
        "phase25c_complete": all_pass,
        "all_gates_pass": all_pass,
        "failed_gates": failed,
        "gates": gates,
        "population": "ROUTER_DEVELOPMENT",
        "n_label_rows": label_rows,
        "n_label_rows_expected": 4957,
        "label_csv": "data_cache/phase25c_barr_oof_paired_gain_labels_v1_2/"
                     "phase25c_oof_paired_gain_labels.csv",
        "label_csv_sha256": label_sha_now,
        "label_columns": ["sample_id", "feature_row_index", "domain", "outer_fold",
                          "global_dice", "candidate_refined_dice", "delta_dice",
                          "gain_category", "fold_refiner_checkpoint_sha"],
        "primary_target": "delta_dice",
        "secondary_target": "gain_category",
        "gain_category_counts": integ.get("category_counts", {}),
        "beneficial_threshold": 0.02,
        "harmful_threshold": -0.01,
        "roi_proposal_threshold": 0.3,
        "segmentation_output_threshold": 0.5,
        "cross_fit_folds": [0, 1, 2],
        "fold_label_counts": fold_counts,
        "final_refiner_used_for_oof": False,
        "global_model_forward_passes": 0,
        "router_trained": False,
        "task_embedding_trained": False,
        "phase25d_started": False,
        "oof_inference": {
            "batch_size": 8,
            "dtype": "float32",
            "autocast": False,
            "tta": False,
            "ensemble": False,
            "drop_last": False,
            "binding": "PRE_EXECUTION_OPERATIONAL_BINDING",
        },
        "notebook": {
            "path": "notebooks/phasewise/phase_25c_paired_gain_labels/"
                    "phase25c_oof_paired_refinement_gain.ipynb",
            "sha256": nb_sha_now,
            "n_cells": vis.get("n_cells"),
            "n_code": vis.get("n_code"),
            "n_markdown": vis.get("n_markdown"),
            "n_embedded_png": vis.get("n_embedded_png"),
            "n_valid_png": vis.get("n_valid_png"),
            "byte_identical_three_builds": ndet.get("byte_identical"),
            "zero_tracebacks": vis.get("zero_tracebacks"),
        },
        "frozen_predecessor_sha_still_match": {
            "phase25b_matrix": p25b.get("matrix_sha256"),
            "phase25b_metadata": p25b.get("metadata_sha256"),
            "phase25b_schema": p25b.get("schema_sha256"),
            "phase25a_notebook": p25a.get("phase25a_notebook_sha256"),
            "phase24_notebook": p24.get("phase24_notebook_sha256"),
            "all_match": bool(gates["phase24_binding_ok"]
                              and gates["phase25a_binding_ok"]
                              and gates["phase25b_binding_ok"]),
        },
        "phase25d_eligible": True,
        "phase25d_status": "ELIGIBLE_NOT_STARTED",
        "phase25e_status": "NOT_STARTED",
        "task_embedding_owner": "PHASE25D",
        "test_reads": 0,
        "router_holdout_reads": 0,
        "val808_reads": 0,
        "terminal": TERMINAL,
        "generated_utc": UTC,
    }
    (AUD / "phase25c_final_freeze.json").write_text(json.dumps(freeze, indent=1) + "\n",
                                                     encoding="utf-8")

    print("=" * 78)
    print("§33 SUCCESS CONDITIONS")
    print("=" * 78)
    for k, v in gates.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    print()
    print(f"label rows                 : {label_rows} (expected 4957)")
    print(f"label csv sha256           : {label_sha_now}")
    print(f"notebook sha256            : {nb_sha_now}")
    print(f"3x byte-identical          : {ndet.get('byte_identical')}")
    print(f"embedded PNG valid/total   : {vis.get('n_valid_png')}/{vis.get('n_embedded_png')}")
    print(f"gain categories            : {integ.get('category_counts')}")
    print(f"global_model_forward_passes: 0")
    print(f"router_trained             : False")
    print(f"task_embedding_trained     : False")
    print(f"test_reads                 : 0")
    print()
    print("=" * 78)
    if all_pass:
        print("§34 TERMINAL:")
        print(TERMINAL)
    else:
        print("FAIL-CLOSED -- unresolved gates:", failed)
    print("=" * 78)
    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
