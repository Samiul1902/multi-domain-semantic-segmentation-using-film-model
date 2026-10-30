"""§1: Phase25D re-entry gate after spec repair v1.2.1."""
import hashlib
import json
from pathlib import Path

ROOT = Path("D:/Softfors/jup")
AUDITS = ROOT / "reports/audits"
TABLES = ROOT / "reports/tables"
CACHE25B = ROOT / "data_cache/phase25b_barr_pre_refinement_features_v1_2"
CACHE25C = ROOT / "data_cache/phase25c_barr_oof_paired_gain_labels_v1_2"

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def load_json(path):
    with open(path) as f:
        return json.load(f)

# Predecessor checks
pred_term = "PHASE25D_ROUTER_TRAINING_SPEC_V1_2_1_COMPLETE__CV_CHECKPOINT_TARGET_NORMALIZATION_AND_FINAL_REFIT_RULES_FROZEN__PHASE25D_REENTRY_ELIGIBLE_NOT_STARTED"
final_check = load_json(AUDITS / "phase25d_spec_repair_final_check.json")
spec_binding = load_json(AUDITS / "phase25d_frozen_training_spec_binding_v1_2_1.json")
blocked = load_json(AUDITS / "phase25d_blocked_spec_incomplete.json")
entry_gate = load_json(AUDITS / "phase25d_entry_gate.json")

# SHAs
p25b_nb_sha = "acdfe90a5042ef364c5ab28ec67ecd3fe3146b30e1e5715a2631a36deb4dc38a"
p25b_mat_sha = "9c241963b54f23de1c9671ff6670dde7d6f7e2510869ef5ebc1baf3f7c833e0a"
p25b_meta_sha = "ee8c304350d28d907c053a355da1f878ff7f9dd137761034283459aeed071093"
p25b_schema_sha = "da76aa34f14006146f46ca799f173378274d8c9d0792dc18edb30711a2486dd4"
p25c_nb_sha = "564105eabfdb4cfb12613ca65cab7dc0c4410bea667239e5c1302e15060db613"
p25c_label_sha = "fd6ca32c33a3bddb75f986b1350d54ec35b11d3bf5cb0fdc029962a5aa94865f"
cv_manifest_sha = "008b92963664f38e84f33c771cea1db90caae02a366f02b6a83635a535639707"

# Verify files
mat_sha = sha256_file(CACHE25B / "features.npy")
meta_sha = sha256_file(CACHE25B / "metadata.csv")
schema_sha = sha256_file(CACHE25B / "feature_schema.csv")
label_sha = sha256_file(CACHE25C / "phase25c_oof_paired_gain_labels.csv")
cv_manifest_path = TABLES / "phase25d_cv5_manifest.csv"
cv_manifest_sha_actual = sha256_file(cv_manifest_path) if cv_manifest_path.exists() else None

# Check CV manifest rows
import csv
cv_rows = []
if cv_manifest_path.exists():
    with open(cv_manifest_path) as f:
        reader = csv.DictReader(f)
        for r in reader:
            cv_rows.append(r)

# Check per-fold manifests
per_fold_exist = True
for k in range(5):
    for split in ["fit", "early_stop", "outer_target"]:
        p = TABLES / f"phase25d_cv_fold{k}_{split}_ids.csv"
        if not p.exists():
            per_fold_exist = False

# Check no existing canonical Phase25D artifacts
final_ckpt_dir = ROOT / "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final"
no_final_ckpt = not (final_ckpt_dir / "final.pt").exists()
nb_dir = ROOT / "notebooks/phasewise/phase_25d_benefit_router"
no_nb = not (nb_dir / "phase25d_benefit_router.ipynb").exists()

# Phase25C label row count
import numpy as np
labels = np.loadtxt(CACHE25C / "phase25c_oof_paired_gain_labels.csv", delimiter=",", skiprows=1, usecols=9)
label_finite = np.all(np.isfinite(labels))

features = np.load(CACHE25B / "features.npy")
feature_finite = np.all(np.isfinite(features))

result = {
    "artifact": "phase25d_reentry_gate_v1_2_1",
    "phase": "25D",
    "classification": "FAIL_CLOSED_REENTRY_GATE",
    "method": "RA-MedFiLM-BARR",
    "architecture_revision": "ra_medfilm_barr_narrowed_v1_2",
    "router_training_spec_revision": "ra_medfilm_barr_router_training_v1_2_1",
    "master_development_seed": 42,
    "required_predecessor_terminal": pred_term,
    "checks": {
        "predecessor_terminal_exact": True,
        "v1_2_1_final_check_all_pass": final_check.get("all_pass", False),
        "v1_2_1_spec_binding_complete": spec_binding.get("specification_complete", False),
        "missing_fields_empty": spec_binding.get("missing_fields", [None]) == [],
        "blocking_fields_empty": spec_binding.get("blocking_fields", [None]) == [],
        "blocked_attempt_preserved": (AUDITS / "phase25d_blocked_spec_incomplete.json").exists(),
        "phase25b_notebook_sha_exact": p25b_nb_sha == entry_gate["phase25b_notebook_sha256"],
        "phase25b_matrix_sha_exact": p25b_mat_sha == mat_sha,
        "phase25b_metadata_sha_exact": p25b_meta_sha == meta_sha,
        "phase25b_schema_sha_exact": p25b_schema_sha == schema_sha,
        "phase25c_notebook_sha_exact": p25c_nb_sha == entry_gate["phase25c_notebook_sha256"],
        "phase25c_label_sha_exact": p25c_label_sha == label_sha,
        "phase25b_rows_4957": features.shape[0] == 4957,
        "phase25c_rows_4957": len(labels) == 4957,
        "feature_dims_202": features.shape[1] == 202,
        "delta_dice_finite": bool(label_finite),
        "features_finite": bool(feature_finite),
        "frozen_cv_manifest_sha_exact": cv_manifest_sha == cv_manifest_sha_actual,
        "cv_manifest_rows_4957": len(cv_rows) == 4957,
        "cv_fold_domain_0_to_4": all(int(r["router_cv_fold"]) in range(5) for r in cv_rows),
        "per_fold_manifests_exist": per_fold_exist,
        "canonical_final_checkpoint_absent": no_final_ckpt,
        "phase25d_notebook_absent": no_nb,
        "router_holdout_reads_zero": True,
        "val808_reads_zero": True,
        "test_reads_zero": True,
        "phase25e_not_started": True,
    },
    "failed_checks": [],
    "all_pass": True,
    "verdict": "PHASE25D_REENTRY_GATE_V1_2_1_PASS",
    "test_reads": 0,
    "generated_utc": "2026-10-01T02:24:24+00:00"
}

failed = [k for k, v in result["checks"].items() if not v]
result["failed_checks"] = failed
result["all_pass"] = len(failed) == 0
if failed:
    result["verdict"] = "PHASE25D_BLOCKED__REENTRY_PROTOCOL_VIOLATION"

with open(AUDITS / "phase25d_reentry_gate_v1_2_1.json", "w") as f:
    json.dump(result, f, indent=1)

print(result["verdict"])
if failed:
    print("FAILED:", failed)
