"""Phase-20B analysis: per-model tables, five-model comparison, paired bootstrap, freeze.

Reads ONLY persisted artifacts (per-model per-image metric tables + the NPZ
predictions written by the single canonical VAL pass). Never re-runs inference,
never touches TEST.

Every metric, CI, confusion matrix, KUB stratification and gallery rule is
delegated to the frozen Phase-20 implementation in ``src.analysis.phase20_baseline``
so Phase-20B cannot drift from Phase-20A methodology.

Writes
------
reports/tables/phase20b_<slug>_domain_performance.csv
reports/tables/phase20b_<slug>_domain_bootstrap_ci.csv
reports/tables/phase20b_<slug>_confusion_matrices.csv
reports/audits/phase20b_<slug>_confusion_matrices.json
reports/tables/phase20b_<slug>_calibration_ranking.csv
reports/tables/phase20b_<slug>_kub_subgroup_analysis.csv
reports/tables/phase20b_<slug>_kub_size_stratification.csv
reports/tables/phase20b_gallery_selection.csv
reports/tables/phase20b_five_model_comparison_final.csv
reports/tables/phase20b_five_model_paired_bootstrap.csv
reports/tables/phase20b_five_model_per_image_val_metrics.csv
reports/figures/phase20b_multidomain_baselines/five_model_macro_dice.png

Usage
-----
    ./.venv/Scripts/python.exe scripts/analysis/run_phase20b_analysis.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from phase20b_common import (  # noqa: E402
    AUDIT_DIR,
    FIG_DIR,
    GALLERY_PER_DOMAIN,
    GALLERY_SELECTION_CSV,
    ORDER,
    PER_IMAGE_ALL_CSV,
    PHASE20A_EXPERIMENT_ID,
    TABLE_DIR,
    ckpt_dir,
    exp_dir,
    experiment_id,
    per_image_csv,
    slug,
)
from src.analysis import phase20_baseline as pb  # noqa: E402

N_BOOT = pb.BOOTSTRAP["n_boot"]
SEED = pb.BOOTSTRAP["seed"]
ALPHA = pb.BOOTSTRAP["alpha"]
DATASET_ORDER = pb.DATASET_ORDER


def sha256_file(path: Path) -> str:
    return pb.sha256_file(path)


# --------------------------------------------------------------------------- #
# Per-model tables
# --------------------------------------------------------------------------- #
def analyse_model(model_key: str) -> dict:
    per_image = pd.read_csv(per_image_csv(model_key))
    manifest = pd.read_csv(TABLE_DIR / f"phase20b_{slug(model_key)}_prediction_manifest.csv")
    val_frame = pb.load_val_manifest()
    print(f"[{model_key}] per-image rows: {len(per_image)} | predictions: {len(manifest)}")

    domain_table = pb.domain_summary(per_image)
    ci = pb.bootstrap_domain_cis(per_image)
    cals = pb.calibration_and_ranking(manifest)

    ci_map = {(r["scope"], r["metric"]): r for _, r in ci.iterrows()}
    extra = {r["dataset"]: r for _, r in cals.iterrows()}
    for idx, row in domain_table.iterrows():
        d = row["dataset"]
        if d in extra:
            domain_table.at[idx, "roc_auc"] = float(extra[d]["roc_auc"])
            domain_table.at[idx, "pr_auc"] = float(extra[d]["pr_auc_average_precision"])
            domain_table.at[idx, "brier"] = float(extra[d]["brier"])
            domain_table.at[idx, "ece"] = float(extra[d]["ece"])
            domain_table.at[idx, "mce"] = float(extra[d]["mce"])
        if (d, "dice") in ci_map:
            c = ci_map[(d, "dice")]
            domain_table.at[idx, "dice_ci_low"] = c["ci_low"]
            domain_table.at[idx, "dice_ci_high"] = c["ci_high"]
        if (d, "iou") in ci_map:
            c = ci_map[(d, "iou")]
            domain_table.at[idx, "iou_ci_low"] = c["ci_low"]
            domain_table.at[idx, "iou_ci_high"] = c["ci_high"]

    domain_table.to_csv(TABLE_DIR / f"phase20b_{slug(model_key)}_domain_performance.csv", index=False)
    ci.to_csv(TABLE_DIR / f"phase20b_{slug(model_key)}_domain_bootstrap_ci.csv", index=False)
    cals.to_csv(TABLE_DIR / f"phase20b_{slug(model_key)}_calibration_ranking.csv", index=False)

    conf_df, conf_payload = pb.confusion_matrices(per_image)
    conf_df.to_csv(TABLE_DIR / f"phase20b_{slug(model_key)}_confusion_matrices.csv", index=False)
    pb.write_json(AUDIT_DIR / f"phase20b_{slug(model_key)}_confusion_matrices.json", {
        "artifact": "phase20b_confusion_matrices",
        "phase": 20, "subphase": "20B", "model_key": model_key,
        "layout": "rows = GT (foreground, background); cols = PRED (foreground, background)",
        "matrices": conf_payload,
        "pooled_is_descriptive_only": True,
    })

    kub_sub = pb.kub_subgroup_analysis(per_image, val_frame)
    kub_sub.to_csv(TABLE_DIR / f"phase20b_{slug(model_key)}_kub_subgroup_analysis.csv", index=False)

    kub_size = pb.kub_size_stratification(per_image, val_frame)
    kub_size.to_csv(TABLE_DIR / f"phase20b_{slug(model_key)}_kub_size_stratification.csv", index=False)
    kub_size.attrs["per_sample"].to_csv(
        TABLE_DIR / f"phase20b_{slug(model_key)}_kub_size_stratification_per_sample.csv", index=False)

    macro_row = domain_table[domain_table["row_type"] == "MACRO_DOMAIN"].iloc[0]
    macro_ci = ci[(ci["scope"] == "MACRO_DOMAIN") & (ci["metric"] == "dice")].iloc[0]
    return {
        "model_key": model_key,
        "per_image": per_image,
        "domain_table": domain_table,
        "macro_dice": float(macro_row["dice"]),
        "macro_dice_ci_low": float(macro_ci["ci_low"]),
        "macro_dice_ci_high": float(macro_ci["ci_high"]),
        "macro_iou": float(macro_row["iou"]),
        "pooled_dice": float(domain_table[domain_table["row_type"] == "POOLED_DESCRIPTIVE"].iloc[0]["dice"]),
        "per_domain": {d: float(domain_table[domain_table["dataset"] == d].iloc[0]["dice"])
                       for d in DATASET_ORDER},
    }


# --------------------------------------------------------------------------- #
# Paired bootstrap
# --------------------------------------------------------------------------- #
def paired_bootstrap(per_image_by_model: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Paired percentile bootstrap of the macro-domain Dice difference, per model pair.

    Method (fixed and documented):
      * The primary statistic is the macro-domain mean VAL Dice (unweighted mean of
        the four per-domain per-image mean Dice) — the same selection metric the
        protocol uses.
      * Samples are resampled WITHIN each domain with replacement, using the SAME
        resampled indices for every model in a replicate (hence "paired": every
        model sees an identical resampled VAL set, so per-sample difficulty cancels).
      * ``n_boot`` and ``seed`` are the frozen Phase-20 bootstrap constants.
      * Two-sided p-value = 2 * min(P(diff <= 0), P(diff >= 0)), clipped to [0, 1].
      * A pair is called significant when the 95% percentile CI of the difference
        excludes zero.
    """
    models = list(per_image_by_model.keys())
    # Align every model on the same sample_id ordering per domain.
    per_domain_ids = {}
    for d in DATASET_ORDER:
        base = sorted(per_image_by_model[models[0]]
                      .loc[per_image_by_model[models[0]]["dataset"] == d, "sample_id"].astype(str))
        per_domain_ids[d] = base
    # Build per-model per-domain dice arrays in that fixed order.
    dice = {m: {} for m in models}
    for m in models:
        pi = per_image_by_model[m].copy()
        pi["sample_id"] = pi["sample_id"].astype(str)
        for d in DATASET_ORDER:
            sub = pi[pi["dataset"] == d].set_index("sample_id").loc[per_domain_ids[d]]
            dice[m][d] = sub["dice"].to_numpy(dtype=np.float64)

    rng = np.random.default_rng(SEED)
    n = {d: len(per_domain_ids[d]) for d in DATASET_ORDER}
    # Pre-draw the paired index sets once, so every model/pair shares them.
    idx = {d: rng.integers(0, n[d], size=(N_BOOT, n[d])) for d in DATASET_ORDER}

    macro_boot = {}
    for m in models:
        acc = np.zeros(N_BOOT, dtype=np.float64)
        for d in DATASET_ORDER:
            v = dice[m][d]
            acc += v[idx[d]].mean(axis=1)
        macro_boot[m] = acc / len(DATASET_ORDER)

    observed = {m: float(np.mean([dice[m][d].mean() for d in DATASET_ORDER])) for m in models}

    rows = []
    for i, a in enumerate(models):
        for b in models[i + 1:]:
            diff = macro_boot[a] - macro_boot[b]
            obs = observed[a] - observed[b]
            lo = float(np.percentile(diff, 100 * ALPHA / 2))
            hi = float(np.percentile(diff, 100 * (1 - ALPHA / 2)))
            p = 2 * min(float(np.mean(diff <= 0)), float(np.mean(diff >= 0)))
            p = min(1.0, max(0.0, p))
            rows.append({
                "model_a": a, "model_b": b,
                "observed_macro_dice_a": observed[a],
                "observed_macro_dice_b": observed[b],
                "observed_diff": obs,
                "diff_ci_low": lo, "diff_ci_high": hi,
                "ci_excludes_zero": bool(lo > 0 or hi < 0),
                "p_value_two_sided": p,
                "significant_at_0.05": bool(lo > 0 or hi < 0),
                "n_boot": N_BOOT, "seed": SEED,
                "resampling_unit": "domain_stratified_paired_image",
                "method": "paired percentile bootstrap; same resampled VAL indices for both models",
            })
    return pd.DataFrame(rows).sort_values("observed_diff", ascending=False).reset_index(drop=True)


# --------------------------------------------------------------------------- #
def main() -> int:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    results = {k: analyse_model(k) for k in ORDER}

    # ---- gallery selection (must equal the frozen Phase-20 64 IDs) ----------
    val_frame = pb.load_val_manifest()
    gal = pb.select_gallery_cases(val_frame, per_domain=GALLERY_PER_DOMAIN, seed=SEED)
    gal.to_csv(GALLERY_SELECTION_CSV, index=False)
    frozen_path = TABLE_DIR / "phase20_gallery_selection.csv"
    gallery_matches_frozen = False
    if frozen_path.exists():
        frozen = pd.read_csv(frozen_path)
        gallery_matches_frozen = (set(gal["sample_id"].astype(str))
                                  == set(frozen["sample_id"].astype(str)))
    print(f"gallery: {len(gal)} cases | matches frozen Phase-20 IDs: {gallery_matches_frozen}")

    # ---- combined 808 x 5 per-image table ---------------------------------
    combined = pd.concat([results[k]["per_image"] for k in ORDER], ignore_index=True)
    combined.to_csv(PER_IMAGE_ALL_CSV, index=False)

    # ---- five-model comparison (incl. Phase-20A UNet++) -------------------
    comp_rows = []
    for k in ORDER:
        r = results[k]
        closure = json.loads((exp_dir(k) / "closure.json").read_text(encoding="utf-8"))
        comp_rows.append({
            "model_key": k,
            "display_name": closure.get("model_display_name", k),
            "phase": "20B",
            "class_name": closure.get("model_class"),
            "params": int(closure["model_params"]),
            "best_epoch": int(closure["best_epoch"]),
            "final_epoch": int(closure["final_epoch"]),
            "stop_reason": closure["stop_reason"],
            "resume_count": int(closure.get("resume_count", 0)),
            "macro_domain_dice": r["macro_dice"],
            "macro_domain_dice_ci_low": r["macro_dice_ci_low"],
            "macro_domain_dice_ci_high": r["macro_dice_ci_high"],
            "macro_domain_iou": r["macro_iou"],
            "pooled_dice_descriptive": r["pooled_dice"],
            **{f"dice_{d}": r["per_domain"][d] for d in DATASET_ORDER},
        })
    # Phase-20A reference row
    a_exp = ROOT / "experiments" / PHASE20A_EXPERIMENT_ID
    a_closure = json.loads((a_exp / "closure.json").read_text(encoding="utf-8"))
    a_pi = pd.read_csv(TABLE_DIR / "phase20_per_image_val_metrics.csv")
    a_domain = pb.domain_summary(a_pi)
    a_macro = a_domain[a_domain["row_type"] == "MACRO_DOMAIN"].iloc[0]
    a_ci = pb.bootstrap_domain_cis(a_pi)
    a_mci = a_ci[(a_ci["scope"] == "MACRO_DOMAIN") & (a_ci["metric"] == "dice")].iloc[0]
    comp_rows.append({
        "model_key": "unetpp",
        "display_name": "U-Net++",
        "phase": "20A",
        "class_name": "UNetPlusPlus",
        "params": int(a_closure["model_params"]),
        "best_epoch": int(a_closure["best_epoch"]),
        "final_epoch": int(a_closure["final_epoch"]),
        "stop_reason": a_closure["stop_reason"],
        "resume_count": 0,
        "macro_domain_dice": float(a_macro["dice"]),
        "macro_domain_dice_ci_low": float(a_mci["ci_low"]),
        "macro_domain_dice_ci_high": float(a_mci["ci_high"]),
        "macro_domain_iou": float(a_macro["iou"]),
        "pooled_dice_descriptive": float(
            a_domain[a_domain["row_type"] == "POOLED_DESCRIPTIVE"].iloc[0]["dice"]),
        **{f"dice_{d}": float(a_domain[a_domain["dataset"] == d].iloc[0]["dice"])
           for d in DATASET_ORDER},
    })
    comp = pd.DataFrame(comp_rows).sort_values("macro_domain_dice", ascending=False).reset_index(drop=True)
    comp.to_csv(TABLE_DIR / "phase20b_five_model_comparison_final.csv", index=False)

    # ---- paired bootstrap across the five models --------------------------
    by_model = {k: results[k]["per_image"] for k in ORDER}
    by_model["unetpp"] = a_pi
    paired = paired_bootstrap(by_model)
    paired.to_csv(TABLE_DIR / "phase20b_five_model_paired_bootstrap.csv", index=False)

    # ---- comparison figure -------------------------------------------------
    fig_path = FIG_DIR / "five_model_macro_dice.png"
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(9, 4.5), dpi=150)
        order = comp["display_name"].tolist()
        y = np.arange(len(order))
        vals = comp["macro_domain_dice"].to_numpy()
        lo = comp["macro_domain_dice_ci_low"].to_numpy()
        hi = comp["macro_domain_dice_ci_high"].to_numpy()
        colors = ["#1f77b4" if p == "20A" else "#d62728" for p in comp["phase"]]
        ax.barh(y, vals, xerr=[vals - lo, hi - vals], color=colors, alpha=0.85,
                error_kw={"ecolor": "#333333", "capsize": 3, "lw": 1})
        ax.set_yticks(y); ax.set_yticklabels(order)
        ax.invert_yaxis()
        ax.set_xlabel("macro-domain mean VAL Dice (95% percentile CI)")
        ax.set_title("Phase 20 five-model conventional baseline (VAL, n=808)\n"
                     "blue = Phase 20A reference; red = Phase 20B", fontsize=10)
        ax.set_xlim(0.75, 0.85)
        ax.grid(axis="x", alpha=0.3)
        fig.tight_layout()
        fig.savefig(fig_path)
        plt.close(fig)
        print(f"figure written: {fig_path.relative_to(ROOT)}")
    except Exception as exc:  # pragma: no cover - figure is non-critical
        print(f"WARNING: comparison figure not written: {exc}")
        fig_path = None

    # ---- freeze artifact ---------------------------------------------------
    top = comp.iloc[0]
    second = comp.iloc[1]
    top_pair = paired[
        ((paired["model_a"] == top["model_key"]) & (paired["model_b"] == second["model_key"]))
        | ((paired["model_b"] == top["model_key"]) & (paired["model_a"] == second["model_key"]))
    ].iloc[0]

    replays = {k: json.loads((AUDIT_DIR / f"phase20b_{slug(k)}_checkpoint_selection_replay.json")
                             .read_text(encoding="utf-8"))["verdict"] for k in ORDER}
    val_evals = {k: json.loads((AUDIT_DIR / f"phase20b_{slug(k)}_val_evaluation.json")
                               .read_text(encoding="utf-8")) for k in ORDER}
    protocol = pb.load_protocol()

    freeze = {
        "artifact": "phase20_five_model_baseline_benchmark_freeze",
        "phase": 20,
        "subphase": "20A+20B",
        "protocol_sha256": sha256_file(ROOT / "reports/audits/phase20_shared_global_baseline_protocol.json"),
        "protocol_sha256_expected": "b74f1f9f429adbce374f0306180943b9f373f872e1e69e115b7d17e81414283c",
        "manifest_version": "phase4_v3",
        "selection_rule_id": "phase20_macro_domain_mean_dice_v1",
        "val_population": 808,
        "models": comp.to_dict("records"),
        "ranking_by_macro_domain_dice": comp["model_key"].tolist(),
        "top_model": top["model_key"],
        "top_two_margin": float(top["macro_domain_dice"] - second["macro_domain_dice"]),
        "top_two_paired_bootstrap": top_pair.to_dict(),
        "top_two_ranking_significant": bool(top_pair["significant_at_0.05"]),
        "paired_bootstrap_table": str(TABLE_DIR.joinpath("phase20b_five_model_paired_bootstrap.csv")
                                      .relative_to(ROOT)).replace("\\", "/"),
        "paired_bootstrap_method": "paired percentile bootstrap, domain-stratified, "
                                   "same resampled VAL indices across models, "
                                   f"n_boot={N_BOOT}, seed={SEED}, alpha={ALPHA}",
        "comparison_table": str(TABLE_DIR.joinpath("phase20b_five_model_comparison_final.csv")
                                .relative_to(ROOT)).replace("\\", "/"),
        "comparison_table_sha256": sha256_file(TABLE_DIR / "phase20b_five_model_comparison_final.csv"),
        "combined_per_image_table": str(PER_IMAGE_ALL_CSV.relative_to(ROOT)).replace("\\", "/"),
        "combined_per_image_table_sha256": sha256_file(PER_IMAGE_ALL_CSV),
        "gallery_selection": str(GALLERY_SELECTION_CSV.relative_to(ROOT)).replace("\\", "/"),
        "gallery_cases": int(len(gal)),
        "gallery_ids_match_phase20a_frozen_set": bool(gallery_matches_frozen),
        "per_model_replay_verdicts": replays,
        "per_model_replay_all_pass": all(v == "PHASE20B_CHECKPOINT_SELECTION_REPLAY_PASS"
                                         for v in replays.values()),
        "per_model_val_evaluation": {k: {
            "samples_evaluated": v["samples_evaluated"],
            "canonical_val_inference_runs": v["canonical_val_inference_runs"],
            "test_reads": v["test_reads"],
            "per_image_table": v["per_image_table"],
            "per_image_table_sha256": v["per_image_table_sha256"],
        } for k, v in val_evals.items()},
        "test_reads_total": {"test_image_reads": 0, "test_mask_reads": 0,
                             "test_inference": 0, "test_visualization": 0},
        "code_shas": protocol.get("code_shas"),
        "no_per_model_recipe_or_threshold_change": True,
        "threshold": 0.5,
        "input_resolution": int(protocol["input_resolution"]),
        "input_channel_policy": protocol["input_representation"]["channel_policy"],
        "comparison_figure": (str(fig_path.relative_to(ROOT)).replace("\\", "/")
                              if fig_path else None),
        "terminal_state": "PHASE20_FIVE_MODEL_BASELINE_BENCHMARK_COMPLETE__PHASE21_ELIGIBLE_NOT_STARTED",
        "phase21_started": False,
        "phase21_authorization_required": True,
    }
    (AUDIT_DIR / "phase20_five_model_baseline_benchmark_freeze.json").write_text(
        json.dumps(freeze, indent=2), encoding="utf-8")

    print()
    print("=== FIVE-MODEL COMPARISON (macro-domain VAL Dice) ===")
    print(comp[["model_key", "phase", "params", "best_epoch", "macro_domain_dice",
                "macro_domain_dice_ci_low", "macro_domain_dice_ci_high"]].to_string(index=False))
    print()
    print("=== PAIRED BOOTSTRAP (macro-domain Dice differences) ===")
    print(paired[["model_a", "model_b", "observed_diff", "diff_ci_low", "diff_ci_high",
                  "p_value_two_sided", "significant_at_0.05"]].to_string(index=False))
    print()
    print(f"TOP: {top['model_key']} ({top['macro_domain_dice']:.6f}) | "
          f"2nd: {second['model_key']} ({second['macro_domain_dice']:.6f}) | "
          f"margin {freeze['top_two_margin']:.6f}")
    print(f"top-two ranking significant at 0.05: {freeze['top_two_ranking_significant']}")
    print("freeze artifact:", (AUDIT_DIR / "phase20_five_model_baseline_benchmark_freeze.json").relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
