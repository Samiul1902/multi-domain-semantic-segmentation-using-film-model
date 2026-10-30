"""Phase-20B reviewer-package analysis: loaders, tables and derived descriptive analyses.

Everything here reads **persisted artifacts only**:

  * per-model training histories (``experiments/<exp>/history.csv``)
  * per-model closures (``experiments/<exp>/closure.json``)
  * per-model per-image VAL metric tables (``reports/tables/...``)
  * per-model prediction manifests (``npz_path`` -> persisted prob/pred/gt)
  * the frozen five-model comparison / paired-bootstrap / freeze artifacts

It **never** runs inference, never opens a checkpoint, never reads TEST, and never
changes a frozen value. New quantities are DESCRIPTIVE only and are labelled as such.

The five-model canonical order is fixed everywhere as

    U-Net, Attention U-Net, U-Net++, DeepLabV3+, Transformer/MiT-style U-Net

so every table, heatmap and figure shares one row order.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent

# --------------------------------------------------------------------------- #
# Identity
# --------------------------------------------------------------------------- #
#: Canonical model order used by EVERY table and figure in the reviewer package.
MODEL_ORDER = ["unet", "attention_unet", "unetpp", "deeplabv3plus", "transformer_mit_unet"]

DISPLAY = {
    "unet": "U-Net",
    "attention_unet": "Attention U-Net",
    "unetpp": "U-Net++",
    "deeplabv3plus": "DeepLabV3+",
    "transformer_mit_unet": "Transformer/MiT-style U-Net",
}
SHORT = {
    "unet": "UNet",
    "attention_unet": "AttnUNet",
    "unetpp": "UNet++",
    "deeplabv3plus": "DeepLabV3+",
    "transformer_mit_unet": "TransfMiT",
}
PHASE = {"unet": "20B", "attention_unet": "20B", "unetpp": "20A",
         "deeplabv3plus": "20B", "transformer_mit_unet": "20B"}
CLASS_NAME = {"unet": "UNet", "attention_unet": "AttentionUNet", "unetpp": "UNetPlusPlus",
              "deeplabv3plus": "DeepLabV3Plus", "transformer_mit_unet": "TransformerMiTUNet"}
#: Distinct, colour-blind-safe-ish palette; consistent across every figure.
COLORS = {"unet": "#1f77b4", "attention_unet": "#ff7f0e", "unetpp": "#2ca02c",
          "deeplabv3plus": "#d62728", "transformer_mit_unet": "#9467bd"}

DATASET_ORDER = ["ISIC", "BUSI", "KVASIR", "KUB"]
DOMAIN_COLORS = {"ISIC": "#1f77b4", "BUSI": "#ff7f0e", "KVASIR": "#2ca02c", "KUB": "#d62728"}

PHASE20A_EXPERIMENT_ID = "phase20_shared_unetpp_fourdomain_seed42_clean_v3"
PHASE20B_EXPERIMENT_ID = {
    "unet": "phase20b_shared_unet_fourdomain_seed42_clean_v3",
    "attention_unet": "phase20b_shared_attention_unet_fourdomain_seed42_clean_v3",
    "deeplabv3plus": "phase20b_shared_deeplabv3plus_fourdomain_seed42_clean_v3",
    "transformer_mit_unet": "phase20b_shared_transformer_mit_unet_fourdomain_seed42_clean_v3",
}

TABLE_DIR = ROOT / "reports" / "tables"
AUDIT_DIR = ROOT / "reports" / "audits"
FIG_ROOT = ROOT / "reports" / "figures" / "phase20b_five_model_baselines"
PRED_ROOT = ROOT / "reports" / "predictions"
MANIFEST_DIR = ROOT / "manifests" / "phase4_v3"
PROTOCOL_PATH = AUDIT_DIR / "phase20_shared_global_baseline_protocol.json"
FREEZE_PATH = AUDIT_DIR / "phase20_five_model_baseline_benchmark_freeze.json"
COMPARISON_CSV = TABLE_DIR / "phase20b_five_model_comparison_final.csv"
PAIRED_CSV = TABLE_DIR / "phase20b_five_model_paired_bootstrap.csv"
PER_IMAGE_ALL_CSV = TABLE_DIR / "phase20b_five_model_per_image_val_metrics.csv"
GALLERY_CSV = TABLE_DIR / "phase20b_gallery_selection.csv"

#: Frozen calibration/ranking protocol (identical to Phase-20A).
CALIBRATION_STRIDE = 4
CALIBRATION_BINS = 15
BOOTSTRAP = {"n_boot": 2000, "seed": 42, "alpha": 0.05}

TERMINAL_SCIENTIFIC = "PHASE20_FIVE_MODEL_BASELINE_BENCHMARK_COMPLETE__PHASE21_ELIGIBLE_NOT_STARTED"
TERMINAL_REVIEWER = "PHASE20B_REVIEWER_PACKAGE_COMPLETE__FULL_VISUAL_EVIDENCE__PHASE21_ELIGIBLE_NOT_STARTED"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rel(path) -> str:
    return str(Path(path).relative_to(ROOT)).replace("\\", "/")


# --------------------------------------------------------------------------- #
# Per-model artifact resolution
# --------------------------------------------------------------------------- #
def experiment_id(model_key: str) -> str:
    if model_key == "unetpp":
        return PHASE20A_EXPERIMENT_ID
    return PHASE20B_EXPERIMENT_ID[model_key]


def artifacts(model_key: str) -> dict:
    """Resolve every per-model artifact path (Phase-20A keeps its original names)."""
    exp = ROOT / "experiments" / experiment_id(model_key)
    ckpt = ROOT / "checkpoints" / experiment_id(model_key)
    pred = PRED_ROOT / experiment_id(model_key) / "val"
    if model_key == "unetpp":
        return {
            "model_key": model_key, "experiment_id": experiment_id(model_key),
            "exp_dir": exp, "ckpt_dir": ckpt, "pred_root": pred,
            "closure": exp / "closure.json", "history": exp / "history.csv",
            "per_image": TABLE_DIR / "phase20_per_image_val_metrics.csv",
            "pred_manifest": TABLE_DIR / "phase20_prediction_manifest.csv",
            "domain_perf": TABLE_DIR / "phase20_domain_performance.csv",
            "calibration": TABLE_DIR / "phase20_calibration_ranking.csv",
            "confusion": TABLE_DIR / "phase20_confusion_matrices.csv",
            "kub_sub": TABLE_DIR / "phase20_kub_subgroup_analysis.csv",
            "kub_size": TABLE_DIR / "phase20_kub_size_stratification.csv",
            "kub_size_ps": TABLE_DIR / "phase20_kub_size_stratification_per_sample.csv",
            "replay": AUDIT_DIR / "phase20_checkpoint_selection_replay.json",
            "val_eval": AUDIT_DIR / "phase20_val_evaluation.json",
        }
    s = model_key
    return {
        "model_key": model_key, "experiment_id": experiment_id(model_key),
        "exp_dir": exp, "ckpt_dir": ckpt, "pred_root": pred,
        "closure": exp / "closure.json", "history": exp / "history.csv",
        "per_image": TABLE_DIR / f"phase20b_{s}_per_image_val_metrics.csv",
        "pred_manifest": TABLE_DIR / f"phase20b_{s}_prediction_manifest.csv",
        "domain_perf": TABLE_DIR / f"phase20b_{s}_domain_performance.csv",
        "calibration": TABLE_DIR / f"phase20b_{s}_calibration_ranking.csv",
        "confusion": TABLE_DIR / f"phase20b_{s}_confusion_matrices.csv",
        "kub_sub": TABLE_DIR / f"phase20b_{s}_kub_subgroup_analysis.csv",
        "kub_size": TABLE_DIR / f"phase20b_{s}_kub_size_stratification.csv",
        "kub_size_ps": TABLE_DIR / f"phase20b_{s}_kub_size_stratification_per_sample.csv",
        "replay": AUDIT_DIR / f"phase20b_{s}_checkpoint_selection_replay.json",
        "val_eval": AUDIT_DIR / f"phase20b_{s}_val_evaluation.json",
    }


def all_artifacts() -> dict:
    return {m: artifacts(m) for m in MODEL_ORDER}


# --------------------------------------------------------------------------- #
# Loaders
# --------------------------------------------------------------------------- #
def load_closure(model_key: str) -> dict:
    return json.loads(artifacts(model_key)["closure"].read_text(encoding="utf-8"))


def load_history(model_key: str) -> pd.DataFrame:
    return pd.read_csv(artifacts(model_key)["history"])


def load_per_image(model_key: str) -> pd.DataFrame:
    df = pd.read_csv(artifacts(model_key)["per_image"])
    df["sample_id"] = df["sample_id"].astype(str)
    return df


def load_per_image_all() -> pd.DataFrame:
    """The FROZEN combined per-image table (the four Phase-20B models, 3232 rows).

    Phase-20A UNet++ has its own table, so this is deliberately *not* the five-model
    view. Use :func:`load_per_image_all5` for five-model analyses. This function is
    kept because the frozen freeze artifact binds this file's SHA.
    """
    df = pd.read_csv(PER_IMAGE_ALL_CSV)
    df["sample_id"] = df["sample_id"].astype(str)
    return df


def load_per_image_all5() -> pd.DataFrame:
    """Five-model per-image view built from the per-model tables (no artifact is modified).

    Phase-20A UNet++ rows come from ``phase20_per_image_val_metrics.csv`` (which has no
    ``model_key`` column), so ``model_key`` is added explicitly.
    """
    frames = []
    for m in MODEL_ORDER:
        df = load_per_image(m).copy()
        df["model_key"] = m
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def load_pred_manifest(model_key: str) -> pd.DataFrame:
    df = pd.read_csv(artifacts(model_key)["pred_manifest"])
    df["sample_id"] = df["sample_id"].astype(str)
    return df


def load_domain_perf(model_key: str) -> pd.DataFrame:
    return pd.read_csv(artifacts(model_key)["domain_perf"])


def load_calibration(model_key: str) -> pd.DataFrame:
    return pd.read_csv(artifacts(model_key)["calibration"])


def load_confusion(model_key: str) -> pd.DataFrame:
    return pd.read_csv(artifacts(model_key)["confusion"])


def load_kub_subgroup(model_key: str) -> pd.DataFrame:
    return pd.read_csv(artifacts(model_key)["kub_sub"])


def load_kub_size(model_key: str) -> pd.DataFrame:
    return pd.read_csv(artifacts(model_key)["kub_size"])


def load_kub_size_per_sample(model_key: str) -> pd.DataFrame:
    return pd.read_csv(artifacts(model_key)["kub_size_ps"])


def load_replay(model_key: str) -> dict:
    return json.loads(artifacts(model_key)["replay"].read_text(encoding="utf-8"))


def load_val_eval(model_key: str) -> dict:
    return json.loads(artifacts(model_key)["val_eval"].read_text(encoding="utf-8"))


def load_freeze() -> dict:
    return json.loads(FREEZE_PATH.read_text(encoding="utf-8"))


def load_protocol() -> dict:
    return json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))


def load_comparison() -> pd.DataFrame:
    """Five-model headline comparison, re-ordered to the canonical MODEL_ORDER."""
    df = pd.read_csv(COMPARISON_CSV)
    df["_o"] = df["model_key"].map({m: i for i, m in enumerate(MODEL_ORDER)})
    return df.sort_values("_o").drop(columns="_o").reset_index(drop=True)


def load_paired_bootstrap() -> pd.DataFrame:
    return pd.read_csv(PAIRED_CSV)


def load_val_manifest() -> pd.DataFrame:
    df = pd.read_csv(MANIFEST_DIR / "val.csv")
    df["sample_id"] = df["sample_id"].astype(str)
    return df


def load_gallery() -> pd.DataFrame:
    df = pd.read_csv(GALLERY_CSV)
    df["sample_id"] = df["sample_id"].astype(str)
    return df


def load_prediction(npz_path) -> dict:
    """Load one persisted prediction (prob float16, pred uint8, gt uint8)."""
    z = np.load(ROOT / npz_path if not Path(npz_path).is_absolute() else npz_path)
    return {"prob": z["prob"].astype(np.float32), "pred": z["pred"].astype(bool),
            "gt": z["gt"].astype(bool)}


# --------------------------------------------------------------------------- #
# Tables (publication-facing)
# --------------------------------------------------------------------------- #
def headline_table() -> pd.DataFrame:
    """Five-model headline: identity, params, epochs, macro Dice + CI."""
    comp = load_comparison()
    out = pd.DataFrame({
        "model_key": comp["model_key"],
        "model": [DISPLAY[m] for m in comp["model_key"]],
        "phase": comp["phase"],
        "class_name": comp["class_name"],
        "params": comp["params"].astype(int),
        "best_epoch": comp["best_epoch"].astype(int),
        "final_epoch": comp["final_epoch"].astype(int),
        "stop_reason": comp["stop_reason"],
        "macro_dice": comp["macro_domain_dice"],
        "dice_ci_low": comp["macro_domain_dice_ci_low"],
        "dice_ci_high": comp["macro_domain_dice_ci_high"],
        "macro_iou": comp["macro_domain_iou"],
    })
    return out


def per_domain_table(metric: str = "dice") -> pd.DataFrame:
    """model x domain matrix for one per-image macro metric."""
    rows = []
    for m in MODEL_ORDER:
        dp = load_domain_perf(m)
        row = {"model_key": m, "model": DISPLAY[m], "phase": PHASE[m]}
        for d in DATASET_ORDER:
            sel = dp[(dp["row_type"] == "DOMAIN") & (dp["dataset"] == d)]
            row[d] = float(sel.iloc[0][metric]) if len(sel) else np.nan
        macro = dp[dp["row_type"] == "MACRO_DOMAIN"]
        row["MACRO"] = float(macro.iloc[0][metric]) if len(macro) else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


ADVANCED_METRICS = ["dice", "iou", "precision", "recall", "specificity", "balanced_accuracy",
                    "mcc", "hd95", "assd", "surface_dice", "roc_auc", "pr_auc", "brier", "ece", "mce"]
HIGHER_IS_BETTER = {"dice", "iou", "precision", "recall", "specificity", "balanced_accuracy",
                    "mcc", "surface_dice", "roc_auc", "pr_auc"}


def domain_metric_matrix(metric: str) -> pd.DataFrame:
    """model x domain matrix for a domain-level metric (advanced metrics included)."""
    rows = []
    for m in MODEL_ORDER:
        dp = load_domain_perf(m)
        row = {"model_key": m, "model": DISPLAY[m]}
        for d in DATASET_ORDER:
            sel = dp[(dp["row_type"] == "DOMAIN") & (dp["dataset"] == d)]
            row[d] = float(sel.iloc[0][metric]) if len(sel) and metric in dp.columns else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def macro_advanced_table() -> pd.DataFrame:
    """model x advanced-metric (macro-domain) publication table."""
    rows = []
    for m in MODEL_ORDER:
        dp = load_domain_perf(m)
        macro = dp[dp["row_type"] == "MACRO_DOMAIN"]
        row = {"model_key": m, "model": DISPLAY[m], "phase": PHASE[m]}
        for metric in ADVANCED_METRICS:
            row[metric] = float(macro.iloc[0][metric]) if len(macro) and metric in dp.columns else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def comprehensive_metric_matrix() -> pd.DataFrame:
    """Long-form model x domain x metric, for a single comprehensive heatmap."""
    rows = []
    for m in MODEL_ORDER:
        dp = load_domain_perf(m)
        for d in DATASET_ORDER:
            sel = dp[(dp["row_type"] == "DOMAIN") & (dp["dataset"] == d)]
            if not len(sel):
                continue
            r = {"model_key": m, "model": DISPLAY[m], "dataset": d}
            for metric in ADVANCED_METRICS:
                r[metric] = float(sel.iloc[0][metric]) if metric in dp.columns else np.nan
            rows.append(r)
    return pd.DataFrame(rows)


def confusion_table() -> pd.DataFrame:
    """model x domain pixel confusion counts + derived rates."""
    rows = []
    for m in MODEL_ORDER:
        c = load_confusion(m)
        for _, r in c.iterrows():
            rows.append({"model_key": m, "model": DISPLAY[m], "scope": r["scope"],
                         "tp": int(r["tp"]), "tn": int(r["tn"]), "fp": int(r["fp"]), "fn": int(r["fn"]),
                         "gt_foreground": int(r["gt_foreground"]), "gt_background": int(r["gt_background"]),
                         "row_norm_gt_fg_tp": r["row_norm_gt_fg_tp"], "row_norm_gt_fg_fn": r["row_norm_gt_fg_fn"],
                         "row_norm_gt_bg_fp": r["row_norm_gt_bg_fp"], "row_norm_gt_bg_tn": r["row_norm_gt_bg_tn"]})
    return pd.DataFrame(rows)


def fpr_fnr_table() -> pd.DataFrame:
    """model x domain false-positive-rate / false-negative-rate matrix (long form)."""
    rows = []
    for m in MODEL_ORDER:
        c = load_confusion(m)
        for d in DATASET_ORDER:
            sel = c[c["scope"] == d]
            if not len(sel):
                continue
            r = sel.iloc[0]
            rows.append({"model_key": m, "model": DISPLAY[m], "dataset": d,
                         "fpr": r["row_norm_gt_bg_fp"], "fnr": r["row_norm_gt_fg_fn"]})
    return pd.DataFrame(rows)


def kub_subgroup_matrix(metric: str = "dice") -> pd.DataFrame:
    """model x KUB subgroup matrix. REPORTING ONLY."""
    subs = ["Kidney_Stone", "Bladder_Stone", "Ureteric_Stone", "KUB_ALL"]
    rows = []
    for m in MODEL_ORDER:
        s = load_kub_subgroup(m)
        row = {"model_key": m, "model": DISPLAY[m]}
        for sg in subs:
            sel = s[s["subgroup"] == sg]
            row[sg] = float(sel.iloc[0][metric]) if len(sel) and metric in s.columns else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def kub_size_matrix(metric: str = "dice") -> pd.DataFrame:
    """model x frozen clean-v3 size-stratum matrix. REPORTING ONLY."""
    strata = ["TINY", "SMALL", "MEDIUM", "LARGE", "ROI_NOT_PRIMARY_BINNED"]
    rows = []
    for m in MODEL_ORDER:
        s = load_kub_size(m)
        row = {"model_key": m, "model": DISPLAY[m]}
        for st in strata:
            sel = s[s["stratum"] == st]
            row[st] = float(sel.iloc[0][metric]) if len(sel) and metric in s.columns else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def kub_size_n() -> dict:
    s = load_kub_size("unetpp")
    return {r["stratum"]: int(r["n"]) for _, r in s.iterrows()}


def tiny_per_sample() -> pd.DataFrame:
    """Per-sample TINY/FULL_FIELD strata for all five models (long form)."""
    frames = []
    for m in MODEL_ORDER:
        ps = load_kub_size_per_sample(m)
        ps = ps[ps["stratum"] == "TINY"].copy()
        ps["model_key"] = m
        ps["model"] = DISPLAY[m]
        frames.append(ps[["sample_id", "model_key", "model", "stratum", "dice", "iou", "component_ratio"]])
    return pd.concat(frames, ignore_index=True)


def empty_prediction_table() -> pd.DataFrame:
    """model x domain empty-prediction / empty-GT behaviour (from per-image tables)."""
    rows = []
    for m in MODEL_ORDER:
        pi = load_per_image(m)
        for d in DATASET_ORDER:
            sub = pi[pi["dataset"] == d]
            n = len(sub)
            rows.append({
                "model_key": m, "model": DISPLAY[m], "dataset": d, "n": n,
                "gt_empty_n": int(sub["gt_empty"].sum()),
                "pred_empty_n": int(sub["pred_empty"].sum()),
                "empty_prediction_rate": float(sub["pred_empty"].mean()),
                "gt_empty_pred_empty_n": int((sub["gt_empty"] & sub["pred_empty"]).sum()),
                "gt_empty_pred_nonempty_n": int((sub["gt_empty"] & ~sub["pred_empty"]).sum()),
                "gt_nonempty_pred_empty_n": int((~sub["gt_empty"] & sub["pred_empty"]).sum()),
            })
    return pd.DataFrame(rows)


def failure_burden_table() -> pd.DataFrame:
    """model x domain FP/FN pixel burden (per-image means) and empty/complete-miss counts."""
    rows = []
    for m in MODEL_ORDER:
        pi = load_per_image(m)
        for d in DATASET_ORDER:
            sub = pi[pi["dataset"] == d]
            rows.append({
                "model_key": m, "model": DISPLAY[m], "dataset": d, "n": len(sub),
                "mean_fp_pixels": float(sub["fp"].mean()),
                "mean_fn_pixels": float(sub["fn"].mean()),
                "mean_gt_fg_pixels": float(sub["gt_foreground_pixels"].mean()),
                "fp_burden_ratio": float(sub["fp"].sum() / max(1, sub["gt_foreground_pixels"].sum())),
                "fn_burden_ratio": float(sub["fn"].sum() / max(1, sub["gt_foreground_pixels"].sum())),
                "complete_miss_n": int(((~sub["gt_empty"]) & (sub["pred_empty"])).sum()),
                "fp_on_empty_gt_n": int((sub["gt_empty"] & (~sub["pred_empty"])).sum()),
            })
    return pd.DataFrame(rows)


def replay_summary() -> pd.DataFrame:
    rows = []
    for m in MODEL_ORDER:
        r = load_replay(m)
        rows.append({
            "model_key": m, "model": DISPLAY[m], "phase": PHASE[m],
            "selection_rule_id": r.get("selection_rule_id"),
            "history_selected_epoch": r.get("history_selected_epoch"),
            "stored_best_epoch": r.get("stored_best_epoch"),
            "best_pt_epoch": r.get("best_pt_epoch"),
            "n_epochs_evaluated": r.get("n_epochs_evaluated"),
            "n_improvements": r.get("n_improvements"),
            "all_checks_passed": r.get("all_checks_passed"),
            "verdict": r.get("verdict"),
        })
    return pd.DataFrame(rows)


def val_eval_summary() -> pd.DataFrame:
    rows = []
    for m in MODEL_ORDER:
        v = load_val_eval(m)
        rows.append({
            "model_key": m, "model": DISPLAY[m], "phase": PHASE[m],
            "samples_evaluated": v.get("samples_evaluated"),
            "canonical_val_inference_runs": v.get("canonical_val_inference_runs"),
            "threshold": v.get("threshold"),
            "prob_maps_persisted": v.get("prob_maps_persisted"),
            "elapsed_seconds": v.get("elapsed_seconds"),
            "test_image_reads": v.get("test_reads", {}).get("test_image_reads"),
            "test_mask_reads": v.get("test_reads", {}).get("test_mask_reads"),
            "test_inference": v.get("test_reads", {}).get("test_inference"),
            "test_visualization": v.get("test_reads", {}).get("test_visualization"),
        })
    return pd.DataFrame(rows)


def training_summary() -> pd.DataFrame:
    rows = []
    for m in MODEL_ORDER:
        c = load_closure(m)
        h = load_history(m)
        rows.append({
            "model_key": m, "model": DISPLAY[m], "phase": PHASE[m],
            "architecture": c.get("architecture"),
            "params": int(c["model_params"]),
            "best_epoch": int(c["best_epoch"]),
            "final_epoch": int(c["final_epoch"]),
            "total_completed_epochs": int(c.get("total_completed_epochs", c["final_epoch"])),
            "stop_reason": c["stop_reason"],
            "early_stopping_patience": int(c["early_stopping_patience"]),
            "resume_count": int(c.get("resume_count", 0)),
            "best_macro_domain_dice": float(c["best_macro_domain_dice"]),
            "best_val_loss": float(c["best_val_loss"]),
            "total_elapsed_seconds": float(c["total_elapsed_seconds"]),
            "mean_epoch_seconds": float(h["epoch_seconds"].mean()),
            "n_improvement_events": int(h["is_new_best"].sum()),
        })
    return pd.DataFrame(rows)


def efficiency_table() -> pd.DataFrame:
    """Parameters, checkpoint size, training cost and (where persisted) inference cost."""
    rows = []
    for m in MODEL_ORDER:
        c = load_closure(m)
        h = load_history(m)
        v = load_val_eval(m)
        best = artifacts(m)["ckpt_dir"] / "best.pt"
        rows.append({
            "model_key": m, "model": DISPLAY[m], "phase": PHASE[m],
            "params": int(c["model_params"]),
            "checkpoint_bytes": int(best.stat().st_size) if best.exists() else np.nan,
            "best_epoch": int(c["best_epoch"]),
            "final_epoch": int(c["final_epoch"]),
            "total_training_seconds": float(c["total_elapsed_seconds"]),
            "mean_epoch_seconds": float(h["epoch_seconds"].mean()),
            "inference_seconds_808": float(v.get("elapsed_seconds", np.nan)),
            "inference_ms_per_sample": (float(v["elapsed_seconds"]) / 808.0 * 1000.0
                                        if v.get("elapsed_seconds") else np.nan),
            "peak_gpu_memory_mb": np.nan,
        })
    return pd.DataFrame(rows)


def provenance_table() -> pd.DataFrame:
    """Per-model provenance: source SHA, binding SHA, protocol SHA, checkpoint SHA.

    The four Phase-20B closures record an explicit ``protocol_sha256``. The Phase-20A
    reference closure predates that field: the frozen protocol binds it through its
    ``code_shas`` list (the model's own trainer SHA), so the effective protocol SHA is
    resolved from there and the binding method is recorded explicitly.
    """
    rows = []
    protocol_sha = sha256_file(PROTOCOL_PATH)
    proto = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    bound_shas = set(proto.get("code_shas", {}).values())
    for m in MODEL_ORDER:
        c = load_closure(m)
        declared = c.get("protocol_sha256")
        trainer_sha = c.get("trainer_sha256")
        bound_via_code_shas = bool(trainer_sha) and trainer_sha in bound_shas
        effective = declared or (protocol_sha if bound_via_code_shas else None)
        binding = ("closure_field" if declared else
                   ("frozen_protocol_code_shas" if bound_via_code_shas else "UNBOUND"))
        rows.append({
            "model_key": m, "model": DISPLAY[m], "phase": PHASE[m],
            "model_class": c.get("model_class"),
            "model_source_file": c.get("model_source_file"),
            "model_source_sha256": c.get("model_source_sha256"),
            "architecture_binding_sha256": c.get("architecture_binding_sha256"),
            "pre_execution_check_sha256": c.get("pre_execution_check_sha256"),
            "history_sha256": c.get("history_sha256"),
            "best_checkpoint_sha256": c.get("best_checkpoint_sha256"),
            "protocol_sha256": effective,
            "protocol_binding": binding,
            "protocol_sha_matches_repo": effective == protocol_sha,
        })
    return pd.DataFrame(rows)


def fairness_contract_table() -> pd.DataFrame:
    """Field-by-field proof that only the model constructor + identity vary."""
    fields = [
        ("manifest_version", lambda c: c["configuration"]["manifest_version"]),
        ("dataset", lambda c: c["configuration"]["dataset"]),
        ("input_channel_policy", lambda c: c["configuration"]["input_channel_policy"]),
        ("input_resolution", lambda c: c["configuration"]["input_resolution"]),
        ("loss", lambda c: json.dumps(c["configuration"]["loss"], sort_keys=True)),
        ("optimizer", lambda c: json.dumps(c["configuration"]["optimizer"], sort_keys=True)),
        ("scheduler", lambda c: json.dumps(c["configuration"]["scheduler"], sort_keys=True)),
        ("batch_size", lambda c: c["configuration"]["training"]["batch_size"]),
        ("max_epochs", lambda c: c["configuration"]["training"]["max_epochs"]),
        ("early_stopping_patience", lambda c: c["configuration"]["training"]["early_stopping_patience"]),
        ("amp", lambda c: c["configuration"]["training"]["amp"]),
        ("seed", lambda c: c["configuration"]["training"]["seed"]),
        ("threshold", lambda c: c["configuration"]["training"]["threshold"]),
        ("sampling_policy", lambda c: c["configuration"]["training"]["sampling_policy"]),
        ("checkpoint_metric", lambda c: c["configuration"]["training"]["checkpoint_metric"]),
        ("tie_break", lambda c: c["configuration"]["training"]["tie_break"]),
        ("task_id_as_model_input", lambda c: c["configuration"]["governance"]["task_id_as_model_input"]),
        ("film", lambda c: c["configuration"]["governance"]["film"]),
        ("regional_module", lambda c: c["configuration"]["governance"]["regional_module"]),
        ("localizer", lambda c: c["configuration"]["governance"]["localizer"]),
        ("roi_proposal", lambda c: c["configuration"]["governance"]["roi_proposal"]),
        ("allow_test", lambda c: c["configuration"]["governance"]["allow_test"]),
    ]
    closures = {m: load_closure(m) for m in MODEL_ORDER}
    rows = []
    for name, getter in fields:
        vals = {m: getter(closures[m]) for m in MODEL_ORDER}
        uniq = set(vals.values())
        rows.append({"field": name, **{DISPLAY[m]: vals[m] for m in MODEL_ORDER},
                     "identical_across_models": len(uniq) == 1})
    return pd.DataFrame(rows)


def model_definition_table() -> pd.DataFrame:
    rows = []
    for m in MODEL_ORDER:
        c = load_closure(m)
        rows.append({
            "model_key": m, "model": DISPLAY[m], "phase": PHASE[m],
            "class_name": c.get("model_class"),
            "architecture": c.get("architecture"),
            "source_file": c.get("model_source_file"),
            "params": int(c["model_params"]),
            "in_channels": c["configuration"]["model"]["in_channels"],
            "out_channels": c["configuration"]["model"]["out_channels"],
            "base_channels": c["configuration"]["model"]["base_channels"],
            "provenance_note": _provenance_note(m),
        })
    return pd.DataFrame(rows)


def _provenance_note(model_key: str) -> str:
    if model_key == "deeplabv3plus":
        return "random-init backbone; NOT ImageNet-pretrained"
    if model_key == "transformer_mit_unet":
        return "LOCAL_RANDOM_INIT MiT-style; NOT official pretrained MiT-B1"
    if model_key == "unetpp":
        return "Phase-20A shared reference"
    return "random-init conventional baseline"


# --------------------------------------------------------------------------- #
# Derived descriptive analyses (from persisted probabilities only)
# --------------------------------------------------------------------------- #
def curves_and_calibration(stride: int = CALIBRATION_STRIDE, n_bins: int = CALIBRATION_BINS) -> dict:
    """ROC / PR curves + calibration scalars + reliability bins, per model and domain.

    One NPZ pass per (model, domain). No inference. Uses the frozen Phase-20A
    deterministic pixel subsample (stride 4) so numbers stay comparable.
    """
    from src.metrics.evaluation_metrics import (
        average_precision, brier_score, expected_calibration_error,
        maximum_calibration_error, precision_recall_curve, reliability_bins,
        roc_auc, roc_curve_points,
    )

    scalars, curves, reliability = [], {}, {}
    for m in MODEL_ORDER:
        man = load_pred_manifest(m)
        for d in DATASET_ORDER:
            sub = man[man["dataset"] == d]
            probs, gts = [], []
            for _, r in sub.iterrows():
                z = np.load(ROOT / r["npz_path"])
                probs.append(z["prob"][::stride, ::stride].ravel().astype(np.float64))
                gts.append(z["gt"][::stride, ::stride].ravel().astype(np.float64))
            p = np.concatenate(probs)
            g = np.concatenate(gts)
            fpr, tpr = roc_curve_points(g, p)
            rec, prec = precision_recall_curve(g, p)
            curves[(m, d)] = {"fpr": fpr, "tpr": tpr, "recall": rec, "precision": prec}
            rb = reliability_bins(g, p, n_bins)
            reliability[(m, d)] = rb
            scalars.append({
                "model_key": m, "model": DISPLAY[m], "dataset": d,
                "n_images": int(len(sub)), "n_pixels": int(p.size), "stride": int(stride),
                "roc_auc": roc_auc(g, p), "pr_auc": average_precision(g, p),
                "brier": brier_score(g, p),
                "ece": expected_calibration_error(g, p, n_bins),
                "mce": maximum_calibration_error(g, p, n_bins),
                "prevalence": float(g.mean()),
            })
            del probs, gts, p, g
    return {"scalars": pd.DataFrame(scalars), "curves": curves, "reliability": reliability}


def cross_model_dice_correlation(metric: str = "dice") -> pd.DataFrame:
    """5x5 Pearson correlation of per-image metric across models (same 808 samples)."""
    pi = load_per_image_all5()
    wide = pi.pivot_table(index="sample_id", columns="model_key", values=metric, aggfunc="mean")
    wide = wide[MODEL_ORDER]
    corr = wide.corr(method="pearson")
    corr.index = [DISPLAY[m] for m in corr.index]
    corr.columns = [DISPLAY[m] for m in corr.columns]
    return corr


def model_sample_matrix(metric: str = "dice") -> pd.DataFrame:
    """model x sample matrix (canonical MODEL_ORDER rows, sample_id columns)."""
    pi = load_per_image_all5()
    wide = pi.pivot_table(index="model_key", columns="sample_id", values=metric, aggfunc="mean")
    wide = wide.reindex(MODEL_ORDER)
    wide.index = [DISPLAY[m] for m in wide.index]
    return wide


def sample_domain_map() -> dict:
    pi = load_per_image_all5()
    first = pi[pi["model_key"] == MODEL_ORDER[0]]
    return dict(zip(first["sample_id"], first["dataset"]))


def rank_stability(n_boot: int = BOOTSTRAP["n_boot"], seed: int = BOOTSTRAP["seed"]) -> dict:
    """DESCRIPTIVE bootstrap rank stability.

    Reconstructs the frozen paired domain-stratified resampling (same resampled VAL
    indices across all five models) and counts how often each model attains each rank
    on the macro-domain Dice statistic. This is descriptive uncertainty only; it is
    NOT a selection gate and does not change any frozen result.
    """
    pi = load_per_image_all5()
    dice = {}
    per_domain_ids = {}
    for d in DATASET_ORDER:
        ids = sorted(pi.loc[(pi["model_key"] == MODEL_ORDER[0]) & (pi["dataset"] == d),
                            "sample_id"].astype(str))
        per_domain_ids[d] = ids
    for m in MODEL_ORDER:
        sub = pi[pi["model_key"] == m]
        dice[m] = {}
        for d in DATASET_ORDER:
            s = sub[sub["dataset"] == d].set_index("sample_id").loc[per_domain_ids[d]]
            dice[m][d] = s["dice"].to_numpy(dtype=np.float64)

    rng = np.random.default_rng(seed)
    n = {d: len(per_domain_ids[d]) for d in DATASET_ORDER}
    idx = {d: rng.integers(0, n[d], size=(n_boot, n[d])) for d in DATASET_ORDER}

    macro = np.zeros((len(MODEL_ORDER), n_boot), dtype=np.float64)
    for i, m in enumerate(MODEL_ORDER):
        acc = np.zeros(n_boot, dtype=np.float64)
        for d in DATASET_ORDER:
            acc += dice[m][d][idx[d]].mean(axis=1)
        macro[i] = acc / len(DATASET_ORDER)

    # rank 1 = highest macro Dice
    order = np.argsort(-macro, axis=0)
    ranks = np.empty_like(order)
    for col in range(n_boot):
        ranks[order[:, col], col] = np.arange(1, len(MODEL_ORDER) + 1)

    freq = pd.DataFrame(
        {DISPLAY[MODEL_ORDER[i]]: [(ranks[i] == r).mean() for r in range(1, len(MODEL_ORDER) + 1)]
         for i in range(len(MODEL_ORDER))},
        index=[f"rank_{r}" for r in range(1, len(MODEL_ORDER) + 1)])

    pairwise_superiority = {}
    for i, a in enumerate(MODEL_ORDER):
        for b in MODEL_ORDER[i + 1:]:
            pairwise_superiority[(a, b)] = float(np.mean(macro[MODEL_ORDER.index(a)]
                                                         > macro[MODEL_ORDER.index(b)]))

    return {
        "rank_frequency": freq,
        "rank_median": {DISPLAY[MODEL_ORDER[i]]: float(np.median(ranks[i])) for i in range(len(MODEL_ORDER))},
        "pairwise_superiority": pairwise_superiority,
        "macro_boot": macro,
        "n_boot": n_boot, "seed": seed,
        "label": "DESCRIPTIVE_BOOTSTRAP_ANALYSIS",
    }


def paired_delta_matrix() -> pd.DataFrame:
    """5x5 observed paired macro-Dice difference (row - column)."""
    paired = load_paired_bootstrap()
    comp = load_comparison().set_index("model_key")["macro_domain_dice"]
    mat = pd.DataFrame(np.nan, index=[DISPLAY[m] for m in MODEL_ORDER],
                       columns=[DISPLAY[m] for m in MODEL_ORDER])
    for _, r in paired.iterrows():
        a, b = r["model_a"], r["model_b"]
        mat.loc[DISPLAY[a], DISPLAY[b]] = r["observed_diff"]
        mat.loc[DISPLAY[b], DISPLAY[a]] = -r["observed_diff"]
    for m in MODEL_ORDER:
        mat.loc[DISPLAY[m], DISPLAY[m]] = 0.0
    return mat


def significance_matrix() -> pd.DataFrame:
    paired = load_paired_bootstrap()
    labels = [DISPLAY[m] for m in MODEL_ORDER]
    mat = pd.DataFrame("", index=labels, columns=labels)
    for _, r in paired.iterrows():
        a, b = DISPLAY[r["model_a"]], DISPLAY[r["model_b"]]
        mark = "significant" if r["significant_at_0.05"] else "n.s."
        mat.loc[a, b] = mark
        mat.loc[b, a] = mark
    for m in MODEL_ORDER:
        mat.loc[DISPLAY[m], DISPLAY[m]] = "diagonal"
    return mat


def pvalue_matrix() -> pd.DataFrame:
    paired = load_paired_bootstrap()
    mat = pd.DataFrame(np.nan, index=[DISPLAY[m] for m in MODEL_ORDER],
                       columns=[DISPLAY[m] for m in MODEL_ORDER])
    for _, r in paired.iterrows():
        a, b = DISPLAY[r["model_a"]], DISPLAY[r["model_b"]]
        mat.loc[a, b] = r["p_value_two_sided"]
        mat.loc[b, a] = r["p_value_two_sided"]
    return mat


def coverage_matrix() -> pd.DataFrame:
    """model x domain coverage: n samples evaluated (should be 808 total)."""
    rows = []
    for m in MODEL_ORDER:
        pi = load_per_image(m)
        row = {"model_key": m, "model": DISPLAY[m]}
        for d in DATASET_ORDER:
            row[d] = int((pi["dataset"] == d).sum())
        row["TOTAL"] = int(len(pi))
        rows.append(row)
    return pd.DataFrame(rows)


def population_table() -> pd.DataFrame:
    """Frozen VAL population per domain (from the manifest)."""
    val = load_val_manifest()
    rows = [{"dataset": d, "n_val": int((val["dataset"] == d).sum())} for d in DATASET_ORDER]
    rows.append({"dataset": "TOTAL", "n_val": int(len(val))})
    return pd.DataFrame(rows)
