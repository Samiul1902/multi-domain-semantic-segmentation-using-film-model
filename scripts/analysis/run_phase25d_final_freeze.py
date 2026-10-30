"""Phase25D final freeze."""
import hashlib
import json
from pathlib import Path

ROOT = Path("D:/Softfors/jup")
AUDITS = ROOT / "reports/audits"
TABLES = ROOT / "reports/tables"
EXP = ROOT / "experiments/phase25d_barr_benefit_router_v1_2_1_seed42"
CKPT = ROOT / "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42"
OUT = ROOT / "data_cache/phase25d_barr_benefit_router_v1_2_1"
NB_PATH = ROOT / "notebooks/phasewise/phase_25d_benefit_router/phase25d_benefit_router.ipynb"

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

# Load audits
metrics = json.load(open(AUDITS / "phase25d_oof_metric_audit.json"))
final_epoch = json.load(open(AUDITS / "phase25d_final_refit_epoch_rule_execution.json"))
health = json.load(open(AUDITS / "phase25d_training_health.json"))
vis = json.load(open(AUDITS / "phase25d_notebook_visual_integrity.json"))
det = json.load(open(AUDITS / "phase25d_notebook_determinism.json"))
registry = json.load(open(AUDITS / "phase25d_training_run_registry.json"))

freeze = {
    "artifact": "phase25d_final_freeze",
    "classification": "CANONICAL_PHASE25D_BENEFIT_ROUTER",
    "method": "RA-MedFiLM-BARR",
    "architecture_revision": "ra_medfilm_barr_narrowed_v1_2",
    "router_training_revision": "ra_medfilm_barr_router_training_v1_2_1",
    "predecessor_terminal": "PHASE25D_ROUTER_TRAINING_SPEC_V1_2_1_COMPLETE__CV_CHECKPOINT_TARGET_NORMALIZATION_AND_FINAL_REFIT_RULES_FROZEN__PHASE25D_REENTRY_ELIGIBLE_NOT_STARTED",
    "blocked_attempt_preserved": True,
    "phase25b_matrix_sha256": "9c241963b54f23de1c9671ff6670dde7d6f7e2510869ef5ebc1baf3f7c833e0a",
    "phase25b_metadata_sha256": "ee8c304350d28d907c053a355da1f878ff7f9dd137761034283459aeed071093",
    "phase25b_schema_sha256": "da76aa34f14006146f46ca799f173378274d8c9d0792dc18edb30711a2486dd4",
    "phase25c_label_sha256": "fd6ca32c33a3bddb75f986b1350d54ec35b11d3bf5cb0fdc029962a5aa94865f",
    "cv5_manifest_sha256": "008b92963664f38e84f33c771cea1db90caae02a366f02b6a83635a535639707",
    "development_rows": 4957,
    "numeric_dims": 202,
    "embedding_dims": 16,
    "input_dims": 218,
    "params": 36801,
    "target": "raw delta_dice",
    "huber_delta": 0.05,
    "optimizer": "AdamW(lr=1e-3, wd=1e-4)",
    "scheduler": "ReduceLROnPlateau(mode=min, factor=0.5, patience=8, threshold=1e-4, min_lr=1e-6)",
    "five_cv_best_epochs": final_epoch["best_epochs"],
    "final_router_epochs": final_epoch["final_router_epochs"],
    "oof_rows": 4957,
    "oof_sha256": sha256_file(OUT / "phase25d_oof_router_predictions.csv"),
    "oof_huber": metrics["overall"]["huber"],
    "oof_mae": metrics["overall"]["mae"],
    "oof_rmse": metrics["overall"]["rmse"],
    "oof_pearson": metrics["overall"]["pearson"],
    "oof_spearman": metrics["overall"]["spearman"],
    "oof_r2": metrics["overall"]["r2"],
    "final_normalization_sha256": sha256_file(TABLES / "phase25d_final_normalization_stats.csv"),
    "final_checkpoint_sha256": sha256_file(CKPT / "final" / "final.pt"),
    "final_history_sha256": sha256_file(EXP / "final" / "history.csv"),
    "feature_recomputation": False,
    "label_recomputation": False,
    "resource_gate_calibrated": False,
    "lambda_selected": False,
    "routing_threshold_selected": False,
    "router_holdout_reads": 0,
    "val808_reads": 0,
    "test_reads": 0,
    "phase25e_started": False,
    "notebook_path": str(NB_PATH),
    "notebook_sha256": sha256_file(NB_PATH),
    "notebook_visual_integrity_pass": vis["all_pass"],
    "notebook_3x_deterministic": det["all_pass"],
    "terminal": "PHASE25D_BENEFIT_ROUTER_COMPLETE__OOF_DELTA_PREDICTIONS_AND_FINAL_ROUTER_FROZEN__PHASE25E_ELIGIBLE_NOT_STARTED",
    "generated_utc": "2026-10-01T02:24:24+00:00"
}

with open(AUDITS / "phase25d_final_freeze.json", "w") as f:
    json.dump(freeze, f, indent=1)

print("FINAL FREEZE WRITTEN")
print(freeze["terminal"])
