"""PHASE-13 PART-1B-CLOSE §15 — rebuild the final artifact registry.

Emits reports/tables/phase13_part1b_training_artifact_registry.csv covering the
complete R2C scientific lineage. Requires exists-false == 0, duplicate paths == 0,
empty SHAs == 0.

Read-only. No training. No inference. No TEST.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXP = "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3"
OUT = ROOT / "reports" / "tables" / "phase13_part1b_training_artifact_registry.csv"
CHK = ROOT / "checkpoints" / EXP

ARTIFACTS = {
    "r2_protocol_json": "reports/audits/phase13_clean_v3_localizer_protocol_frozen_r2.json",
    "r2a_loss_amendment_json": "reports/audits/phase13_clean_v3_localizer_loss_binding_r2a.json",
    "manifest_provenance_amendment_json": "reports/audits/phase13_clean_v3_localizer_manifest_provenance_binding.json",
    "r2b_metric_semantics_json": "reports/audits/phase13_clean_v3_localizer_metric_semantics_r2b.json",
    "r2c_coverage_arbitration_json": "reports/audits/phase13_clean_v3_localizer_coverage_semantics_r2c.json",
    "r2c_coverage_arbitration_md": "reports/audits/phase13_clean_v3_localizer_coverage_semantics_r2c.md",
    "r2c_erratum_json": "reports/audits/phase13_clean_v3_localizer_coverage_semantics_r2c_erratum.json",
    "r2c_erratum_md": "reports/audits/phase13_clean_v3_localizer_coverage_semantics_r2c_erratum.md",
    "executable_config": f"configs/phase13_clean_v3/{EXP}.yaml",
    "executing_runner": "scripts/training/train_phase13_clean_v3_localizer.py",
    "history": f"experiments/{EXP}/history.csv",
    "best_checkpoint": f"checkpoints/{EXP}/best.pt",
    "latest_checkpoint": f"checkpoints/{EXP}/latest.pt",
    "training_start_audit_json": "reports/audits/phase13_clean_v3_localizer_training_start.json",
    "training_start_audit_md": "reports/audits/phase13_clean_v3_localizer_training_start.md",
    "training_completion_audit_json": "reports/audits/phase13_clean_v3_localizer_training_completion.json",
    "training_completion_audit_md": "reports/audits/phase13_clean_v3_localizer_training_completion.md",
    "training_completion_r2c_addendum_json": "reports/audits/phase13_clean_v3_localizer_training_completion_r2c_addendum.json",
    "training_completion_r2c_addendum_md": "reports/audits/phase13_clean_v3_localizer_training_completion_r2c_addendum.md",
    "canonical_selection_sidecar": "reports/tables/phase13_part1b_canonical_selection_history.csv",
    "epoch_results_table": "reports/tables/phase13_clean_v3_localizer_epoch_results.csv",
    "epoch_results_schema_audit": "reports/audits/phase13_clean_v3_localizer_epoch_results_schema_audit.json",
    "best_epoch_verification_json": "reports/audits/phase13_clean_v3_localizer_best_epoch_verification.json",
    "canonical_replay_verification_json": "reports/audits/phase13_part1b_canonical_selection_replay_verification.json",
    "final_best_integrity_audit": "reports/audits/phase13_clean_v3_localizer_final_best_checkpoint_integrity.json",
    "reviewer_notebook": "notebooks/phasewise/phase_13_predicted_roi_localization/phase13_clean_v3_localizer_training_review.ipynb",
    "training_stdout_log": "reports/audits/phase13_clean_v3_localizer_training_stdout.log",
    "r2b_archived_provenance_latest": f"checkpoints/{EXP}/provenance/r2b_pixel_epoch31_latest.pt",
    "r2b_archived_provenance_best": f"checkpoints/{EXP}/provenance/r2b_pixel_epoch31_best.pt",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(8192):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    rows = []
    for kind, rel in ARTIFACTS.items():
        path = ROOT / rel
        exists = path.exists()
        rows.append({
            "artifact_kind": kind,
            "path": str(path),
            "exists": exists,
            "size_bytes": path.stat().st_size if exists else "",
            "sha256": sha256_file(path) if exists else "",
        })

    with open(OUT, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["artifact_kind", "path", "exists", "size_bytes", "sha256"]
        )
        writer.writeheader()
        writer.writerows(rows)

    missing = [r["artifact_kind"] for r in rows if not r["exists"]]
    paths = [r["path"] for r in rows]
    dupes = len(paths) - len(set(paths))
    empty = [r["artifact_kind"] for r in rows if r["exists"] and not r["sha256"]]

    payload = {
        "artifact": "PHASE13_PART1B_TRAINING_ARTIFACT_REGISTRY",
        "registry_path": str(OUT),
        "registry_rows": len(rows),
        "exists_false_count": len(missing),
        "missing": missing,
        "duplicate_paths": dupes,
        "empty_sha_count": len(empty),
        "empty_sha": empty,
    }
    payload["status"] = (
        "PASS" if (not missing and dupes == 0 and not empty) else "CHECK_REQUIRED"
    )
    print(json.dumps(payload, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
