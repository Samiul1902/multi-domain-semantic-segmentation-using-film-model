"""Phase 21 analysis: Global MedFiLM metrics, bootstrap, paired comparison, KUB strata.

Reads ONLY persisted artifacts (the single canonical Phase-21 VAL pass + the five
frozen baseline per-image tables). Never re-runs inference, never touches TEST.

Every metric, CI, confusion matrix and KUB stratification is delegated to the
frozen Phase-20 implementation in ``src.analysis.phase20_baseline`` so Phase 21
cannot drift from the frozen methodology. The paired bootstrap reuses the exact
Phase-20B method (domain-stratified, same resampled indices for both models).

Writes
------
reports/tables/phase21_domain_performance.csv
reports/tables/phase21_domain_bootstrap_ci.csv
reports/tables/phase21_confusion_matrices.csv
reports/tables/phase21_calibration_ranking.csv
reports/tables/phase21_kub_subgroup_analysis.csv
reports/tables/phase21_kub_size_stratification.csv
reports/tables/phase21_kub_size_stratification_per_sample.csv
reports/tables/phase21_gallery_selection_64.csv
reports/tables/phase21_six_model_comparison.csv
reports/tables/phase21_paired_bootstrap_vs_baselines.csv
reports/tables/phase21_per_image_all_models.csv
reports/audits/phase21_confusion_matrices.json
reports/audits/phase21_paired_bootstrap.json
reports/audits/phase21_analysis.json

Usage
-----
    ./.venv/Scripts/python.exe scripts/analysis/run_phase21_analysis.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.analysis import phase20_baseline as pb  # noqa: E402

TABLE_DIR = ROOT / "reports" / "tables"
AUDIT_DIR = ROOT / "reports" / "audits"

MODEL_ORDER = ["unet", "attention_unet", "unetpp", "deeplabv3plus", "transformer_mit_unet"]
DISPLAY = {
    "unet": "U-Net", "attention_unet": "Attention U-Net", "unetpp": "U-Net++",
    "deeplabv3plus": "DeepLabV3+", "transformer_mit_unet": "Transformer/MiT-style U-Net",
    "global_medfilm": "Global MedFiLM",
}
PARAMS = {
    # U-Net is 7,763,041 — NOT 31,042,337. 31.0 M is the base-64 U-Net
    # (filters 64/128/256/512/1024); the Phase-20 panel trains the base-32 variant.
    # Authoritative source: reports/tables/phase20b_five_model_comparison.csv.
    "unet": 7763041, "attention_unet": 7851285, "unetpp": 9159681,
    "deeplabv3plus": 40347041, "transformer_mit_unet": 16347777,
}
N_BOOT = pb.BOOTSTRAP["n_boot"]
SEED = pb.BOOTSTRAP["seed"]
ALPHA = pb.BOOTSTRAP["alpha"]
DATASET_ORDER = pb.DATASET_ORDER

PHASE21_EXP = "phase21_global_medfilm_fourdomain_seed42_clean_v3"


def load_phase21_per_image() -> pd.DataFrame:
    df = pd.read_csv(TABLE_DIR / "phase21_per_image_val_metrics.csv")
    df["sample_id"] = df["sample_id"].astype(str)
    df["model_key"] = "global_medfilm"
    return df


def load_baseline_per_image() -> pd.DataFrame:
    """Five frozen baseline per-image tables on the SAME 808 VAL IDs."""
    frames = []
    for m in MODEL_ORDER:
        if m == "unetpp":
            df = pd.read_csv(TABLE_DIR / "phase20_per_image_val_metrics.csv")
        else:
            df = pd.read_csv(TABLE_DIR / f"phase20b_{m}_per_image_val_metrics.csv")
        df = df.copy()
        df["sample_id"] = df["sample_id"].astype(str)
        df["model_key"] = m
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def domain_tables(per_image: pd.DataFrame, tag: str) -> dict:
    domain_table = pb.domain_summary(per_image)
    ci = pb.bootstrap_domain_cis(per_image)
    manifest = pd.read_csv(TABLE_DIR / "phase21_prediction_manifest.csv")
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
    domain_table.to_csv(TABLE_DIR / f"phase21_{tag}_domain_performance.csv", index=False)
    ci.to_csv(TABLE_DIR / f"phase21_{tag}_domain_bootstrap_ci.csv", index=False)
    cals.to_csv(TABLE_DIR / f"phase21_{tag}_calibration_ranking.csv", index=False)

    conf_df, conf_payload = pb.confusion_matrices(per_image)
    conf_df.to_csv(TABLE_DIR / f"phase21_{tag}_confusion_matrices.csv", index=False)
    pb.write_json(AUDIT_DIR / f"phase21_{tag}_confusion_matrices.json", {
        "artifact": "phase21_confusion_matrices",
        "phase": 21,
        "model_key": "global_medfilm",
        "layout": "rows = GT (foreground, background); cols = PRED (foreground, background)",
        "matrices": conf_payload,
        "pooled_is_descriptive_only": True,
        "test_reads": 0,
    })

    macro_row = domain_table[domain_table["row_type"] == "MACRO_DOMAIN"].iloc[0]
    macro_ci = ci[(ci["scope"] == "MACRO_DOMAIN") & (ci["metric"] == "dice")].iloc[0]
    return {
        "domain_table": domain_table, "ci": ci, "calibration": cals,
        "confusion": conf_df, "confusion_payload": conf_payload,
        "macro_dice": float(macro_row["dice"]),
        "macro_dice_ci_low": float(macro_ci["ci_low"]),
        "macro_dice_ci_high": float(macro_ci["ci_high"]),
        "macro_iou": float(macro_row["iou"]),
        "pooled_dice": float(domain_table[domain_table["row_type"] == "POOLED_DESCRIPTIVE"]
                             .iloc[0]["dice"]),
        "per_domain": {d: float(domain_table[domain_table["dataset"] == d].iloc[0]["dice"])
                       for d in DATASET_ORDER},
        "per_domain_iou": {d: float(domain_table[domain_table["dataset"] == d].iloc[0]["iou"])
                           for d in DATASET_ORDER},
        "per_domain_extra": {
            d: {k: (float(extra[d][k]) if d in extra else float("nan"))
                for k in ("roc_auc", "pr_auc_average_precision", "brier", "ece", "mce")}
            for d in DATASET_ORDER},
    }


def paired_bootstrap_vs_baselines(per_image_by_model: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Paired domain-stratified percentile bootstrap of macro-domain Dice vs each baseline.

    Method (identical to the frozen Phase-20B implementation):
      * Primary statistic = macro-domain mean VAL Dice (unweighted mean of the four
        per-domain per-image mean Dice).
      * Resampling is WITHIN each domain with replacement, using the SAME resampled
        indices for both models in a replicate, so per-sample difficulty cancels.
      * n_boot / seed / alpha are the frozen Phase-20 bootstrap constants.
      * Two-sided p = 2 * min(P(diff <= 0), P(diff >= 0)), clipped to [0, 1].
      * A pair is "significant" only when the 95% percentile CI excludes zero.
    """
    models = list(per_image_by_model.keys())
    per_domain_ids = {}
    for d in DATASET_ORDER:
        base = sorted(per_image_by_model[models[0]]
                      .loc[per_image_by_model[models[0]]["dataset"] == d, "sample_id"].astype(str))
        per_domain_ids[d] = base
    dice = {m: {} for m in models}
    for m in models:
        pi = per_image_by_model[m].copy()
        pi["sample_id"] = pi["sample_id"].astype(str)
        for d in DATASET_ORDER:
            sub = pi[pi["dataset"] == d].set_index("sample_id").loc[per_domain_ids[d]]
            dice[m][d] = sub["dice"].to_numpy(dtype=np.float64)

    rng = np.random.default_rng(SEED)
    n = {d: len(per_domain_ids[d]) for d in DATASET_ORDER}
    idx = {d: rng.integers(0, n[d], size=(N_BOOT, n[d])) for d in DATASET_ORDER}

    macro_boot = {}
    for m in models:
        acc = np.zeros(N_BOOT, dtype=np.float64)
        for d in DATASET_ORDER:
            acc += dice[m][d][idx[d]].mean(axis=1)
        macro_boot[m] = acc / len(DATASET_ORDER)
    observed = {m: float(np.mean([dice[m][d].mean() for d in DATASET_ORDER])) for m in models}

    rows = []
    for b in models:
        if b == "global_medfilm":
            continue
        diff = macro_boot["global_medfilm"] - macro_boot[b]
        obs = observed["global_medfilm"] - observed[b]
        lo = float(np.percentile(diff, 100 * ALPHA / 2))
        hi = float(np.percentile(diff, 100 * (1 - ALPHA / 2)))
        p = 2 * min(float(np.mean(diff <= 0)), float(np.mean(diff >= 0)))
        p = min(1.0, max(0.0, p))
        rows.append({
            "model_a": "global_medfilm", "model_b": b,
            "observed_macro_dice_a": observed["global_medfilm"],
            "observed_macro_dice_b": observed[b],
            "observed_diff": obs,
            "diff_ci_low": lo, "diff_ci_high": hi,
            "ci_excludes_zero": bool(lo > 0 or hi < 0),
            "p_value_two_sided": p,
            "significant_at_0.05": bool(lo > 0 or hi < 0),
            "n_boot": N_BOOT, "seed": SEED,
            "resampling_unit": "domain_stratified_paired_image",
            "method": "paired percentile bootstrap; same resampled VAL indices for both models",
            "interpretation_guard": (
                "A non-significant difference means the CI OVERLAPS zero; the two models must not "
                "be declared different. No architecture-matched control exists, so no causal "
                "attribution to FiLM is permitted."
            ),
        })
    return pd.DataFrame(rows)


def main() -> int:
    per_image = load_phase21_per_image()
    assert len(per_image) == 808, f"Phase-21 per-image rows != 808: {len(per_image)}"
    val_frame = pb.load_val_manifest()

    res = domain_tables(per_image, "global_medfilm")

    kub_sub = pb.kub_subgroup_analysis(per_image, val_frame)
    kub_sub.to_csv(TABLE_DIR / "phase21_kub_subgroup_analysis.csv", index=False)

    kub_size = pb.kub_size_stratification(per_image, val_frame)
    kub_size.to_csv(TABLE_DIR / "phase21_kub_size_stratification.csv", index=False)
    kub_size.attrs["per_sample"].to_csv(
        TABLE_DIR / "phase21_kub_size_stratification_per_sample.csv", index=False)
    kub_size_ps = kub_size.attrs["per_sample"]

    # ---- gallery: reuse the FROZEN 64-case selection UNCHANGED ------------ #
    gallery = pd.read_csv(TABLE_DIR / "phase20_gallery_selection.csv")
    gallery.to_csv(TABLE_DIR / "phase21_gallery_selection_64.csv", index=False)
    gallery_ids = set(gallery["sample_id"].astype(str))
    assert len(gallery) == 64, f"gallery must be 64 cases, got {len(gallery)}"
    assert gallery_ids.issubset(set(per_image["sample_id"])), "gallery IDs must exist in VAL"

    # ---- six-model comparison --------------------------------------------- #
    baselines = load_baseline_per_image()
    combined = pd.concat([baselines, per_image], ignore_index=True)
    combined.to_csv(TABLE_DIR / "phase21_per_image_all_models.csv", index=False)

    rows = []
    for m in MODEL_ORDER + ["global_medfilm"]:
        sub = combined[combined["model_key"] == m]
        if m == "global_medfilm":
            macro = res["macro_dice"]
            lo, hi = res["macro_dice_ci_low"], res["macro_dice_ci_high"]
            assert lo <= macro <= hi, f"CI does not bracket macro Dice: {lo} {macro} {hi}"
            macro_iou = res["macro_iou"]
            pooled = res["pooled_dice"]
            pdice = res["per_domain"]
        else:
            dt = pb.domain_summary(sub)
            ci = pb.bootstrap_domain_cis(sub)
            macro = float(dt[dt["row_type"] == "MACRO_DOMAIN"].iloc[0]["dice"])
            mc = ci[(ci["scope"] == "MACRO_DOMAIN") & (ci["metric"] == "dice")].iloc[0]
            lo, hi = float(mc["ci_low"]), float(mc["ci_high"])
            macro_iou = float(dt[dt["row_type"] == "MACRO_DOMAIN"].iloc[0]["iou"])
            pooled = float(dt[dt["row_type"] == "POOLED_DESCRIPTIVE"].iloc[0]["dice"])
            pdice = {d: float(dt[dt["dataset"] == d].iloc[0]["dice"]) for d in DATASET_ORDER}
        rows.append({
            "model_key": m, "display_name": DISPLAY[m],
            "phase": "21" if m == "global_medfilm" else ("20A" if m == "unetpp" else "20B"),
            "params": PARAMS.get(m),
            "macro_domain_dice": macro, "macro_domain_dice_ci_low": lo,
            "macro_domain_dice_ci_high": hi, "macro_domain_iou": macro_iou,
            "pooled_dice_descriptive": pooled,
            **{f"dice_{d}": pdice[d] for d in DATASET_ORDER},
        })
    comparison = pd.DataFrame(rows).sort_values("macro_domain_dice", ascending=False)
    comparison.to_csv(TABLE_DIR / "phase21_six_model_comparison.csv", index=False)

    per_model = {m: combined[combined["model_key"] == m] for m in MODEL_ORDER + ["global_medfilm"]}
    paired = paired_bootstrap_vs_baselines(per_model)
    paired.to_csv(TABLE_DIR / "phase21_paired_bootstrap_vs_baselines.csv", index=False)

    # ---- analysis summary -------------------------------------------------- #
    rank = comparison["model_key"].tolist()
    gm_rank = rank.index("global_medfilm") + 1
    top = comparison.iloc[0]
    gm_row = comparison[comparison["model_key"] == "global_medfilm"].iloc[0]
    sig = paired[paired["significant_at_0.05"]]
    analysis = {
        "artifact": "phase21_analysis",
        "phase": 21,
        "experiment_id": PHASE21_EXP,
        "val_population": 808,
        "samples_evaluated": int(len(per_image)),
        "selection_rule_id": "phase20_macro_domain_mean_dice_v1",
        "bootstrap": {"n_boot": N_BOOT, "seed": SEED, "alpha": ALPHA, "unit": "image"},
        "global_medfilm": {
            "macro_domain_dice": res["macro_dice"],
            "macro_domain_dice_ci_low": res["macro_dice_ci_low"],
            "macro_domain_dice_ci_high": res["macro_dice_ci_high"],
            "macro_domain_iou": res["macro_iou"],
            "pooled_dice_descriptive": res["pooled_dice"],
            "per_domain_dice": res["per_domain"],
            "per_domain_iou": res["per_domain_iou"],
            "per_domain_extra": res["per_domain_extra"],
            "params": 3523001,
            "rank_among_six": gm_rank,
        },
        "benchmark_top_model": {
            "model_key": str(top["model_key"]), "display_name": str(top["display_name"]),
            "macro_domain_dice": float(top["macro_domain_dice"]),
        },
        "six_model_ranking": rank,
        "paired_bootstrap": {
            "comparisons": int(len(paired)),
            "significant_vs_baselines": sig["model_b"].tolist(),
            "non_significant_vs_baselines": paired[~paired["significant_at_0.05"]]["model_b"].tolist(),
            "method": "paired domain-stratified percentile bootstrap, n_boot=2000, seed=42",
        },
        "kub_subgroup_rows": int(len(kub_sub)),
        "kub_size_rows": int(len(kub_size)),
        "kub_size_n": {str(r["stratum"]): int(r["n"]) for _, r in kub_size.iterrows()},
        "tiny_stratum_preserved_for_phase22": bool(
            (kub_size["stratum"] == "TINY").any()),
        "gallery_cases": int(len(gallery)),
        "gallery_ids_match_frozen_phase20_selection": True,
        "interpretation_guard": (
            "Phase 21 has NO architecture-matched control (no identical plain model trained under "
            "the same Phase-21 run). Therefore the ONLY permitted phrasing is "
            "'Global MedFiLM achieved X compared with baseline Y'. It is FORBIDDEN to claim "
            "'FiLM caused +X'. Where a CI overlaps zero the models are NOT distinguishable."
        ),
        "test_reads": {"test_image_reads": 0, "test_mask_reads": 0,
                       "test_inference": 0, "test_visualization": 0},
    }
    pb.write_json(AUDIT_DIR / "phase21_analysis.json", analysis)
    pb.write_json(AUDIT_DIR / "phase21_paired_bootstrap.json", {
        "artifact": "phase21_paired_bootstrap",
        "phase": 21,
        "experiment_id": PHASE21_EXP,
        "n_boot": N_BOOT, "seed": SEED, "alpha": ALPHA,
        "resampling_unit": "domain_stratified_paired_image",
        "val_population": 808,
        "baselines": MODEL_ORDER,
        "table": "reports/tables/phase21_paired_bootstrap_vs_baselines.csv",
        "significance_rule": "95% percentile CI of the paired macro-Dice difference excludes zero",
        "no_retraining": True,
        "interpretation_guard": analysis["interpretation_guard"],
        "test_reads": 0,
    })

    print(f"Global MedFiLM macro-domain VAL Dice = {res['macro_dice']:.6f} "
          f"[{res['macro_dice_ci_low']:.6f}, {res['macro_dice_ci_high']:.6f}]")
    print(f"per-domain: { {k: round(v, 4) for k, v in res['per_domain'].items()} }")
    print(f"rank among six: {gm_rank}/6 ; top = {top['model_key']} ({top['macro_domain_dice']:.6f})")
    print(f"paired: significant vs {sig['model_b'].tolist()}")
    print(f"KUB size n: {analysis['kub_size_n']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
