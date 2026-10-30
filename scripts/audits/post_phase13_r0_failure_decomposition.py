"""POST-PHASE-13 REGIONAL REVISION R0 — failure decomposition (analysis only, no execution).

Reads ONLY frozen Phase-13 artifacts. No training, no inference, no proposal regeneration.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\Softfors\jup")
TABLES = ROOT / "reports" / "tables"
AUDITS = ROOT / "reports" / "audits"

OLD_FLOOR = 0.10          # frozen Part-1C proposal acceptance threshold
OLD_MAX = 5               # frozen top_k
FLOORS = {"q10": 0.119470, "q25": 0.124532, "max": 0.125065}
MAXES = [1, 5]


def sha(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def roc_auc(y: np.ndarray, s: np.ndarray) -> float:
    df = pd.DataFrame({"s": s, "r": np.empty(len(s))})
    order = np.argsort(s, kind="mergesort")
    r = np.empty(len(s), float)
    r[order] = np.arange(1, len(s) + 1)
    df["r"] = r
    r = df.groupby("s")["r"].transform("mean").to_numpy()
    n1 = int(y.sum()); n0 = len(y) - n1
    if n0 == 0 or n1 == 0:
        return float("nan")
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n0 * n1))


def pr_auc(y: np.ndarray, s: np.ndarray) -> float:
    order = np.argsort(-s, kind="mergesort")
    ys = y[order]
    tp = np.cumsum(ys); fp = np.cumsum(1 - ys)
    prec = tp / np.maximum(tp + fp, 1)
    rec = tp / max(int(tp[-1]), 1)
    fn = np.trapezoid if hasattr(np, "trapezoid") else np.trapz
    return float(fn(prec, rec))


def union_area(rects, shape) -> int:
    if not rects:
        return 0
    m = np.zeros(shape, dtype=bool)
    for (y1, y2, x1, x2) in rects:
        m[max(0, y1):max(0, y2), max(0, x1):max(0, x2)] = True
    return int(m.sum())


def main() -> dict:
    prop = pd.read_csv(TABLES / "phase13_part1c_best_checkpoint_proposals.csv")
    casep = pd.read_csv(TABLES / "phase13_part1c_best_checkpoint_case_proposals.csv")
    compcov = pd.read_csv(TABLES / "phase13_part1c_best_checkpoint_component_coverage.csv")
    cm = pd.read_csv(TABLES / "phase13_part1d_predicted_region_case_model_metrics.csv")
    compm = pd.read_csv(TABLES / "phase13_part1d_predicted_region_component_model_metrics.csv")
    MODELS = ["unet", "attention_unet", "unetpp", "deeplabv3plus"]
    DISPLAY = {"unet": "UNet", "attention_unet": "Attention U-Net",
               "unetpp": "UNet++", "deeplabv3plus": "DeepLabV3+"}

    prop["gt_hit_pixel"] = prop["overlaps_any_gt_pixel"].astype(bool)
    prop["gt_hit_bbox"] = prop["overlaps_any_gt_bbox"].astype(bool)
    mx = float(prop["proposal_score"].max())
    prop["score_saturated"] = prop["proposal_score"] >= mx - 1e-12

    # ================= §5 proposal score/rank diagnostics =================
    rows = []
    for rk, g in prop.groupby("proposal_rank"):
        hit = g[g["gt_hit_pixel"]]; miss = g[~g["gt_hit_pixel"]]
        rows.append({
            "proposal_rank": int(rk), "proposal_count": len(g),
            "bbox_any_hit_count": int(g["gt_hit_bbox"].sum()),
            "bbox_any_hit_rate": float(g["gt_hit_bbox"].mean()),
            "pixel_any_hit_count": int(g["gt_hit_pixel"].sum()),
            "pixel_any_hit_rate": float(g["gt_hit_pixel"].mean()),
            "score_mean": float(g["proposal_score"].mean()),
            "score_median": float(g["proposal_score"].median()),
            "score_q25": float(g["proposal_score"].quantile(.25)),
            "score_q75": float(g["proposal_score"].quantile(.75)),
            "score_min": float(g["proposal_score"].min()),
            "score_max": float(g["proposal_score"].max()),
            "hit_proposal_score_mean": float(hit["proposal_score"].mean()) if len(hit) else np.nan,
            "hit_proposal_score_median": float(hit["proposal_score"].median()) if len(hit) else np.nan,
            "miss_proposal_score_mean": float(miss["proposal_score"].mean()) if len(miss) else np.nan,
            "miss_proposal_score_median": float(miss["proposal_score"].median()) if len(miss) else np.nan,
            "saturated_count": int(g["score_saturated"].sum()),
            "saturated_fraction": float(g["score_saturated"].mean()),
            "mean_proposal_area_fraction": float(g["proposal_area_fraction"].mean()),
        })
    diag = pd.DataFrame(rows)
    diag.to_csv(TABLES / "post_phase13_r0_proposal_score_rank_diagnostics.csv", index=False)

    # ================= §6 score separability (diagnostic only) =================
    y = prop["gt_hit_pixel"].astype(int).to_numpy(); s = prop["proposal_score"].to_numpy()
    sep = {
        "roc_auc_score_to_pixel_hit": roc_auc(y, s),
        "pr_auc_score_to_pixel_hit": pr_auc(y, s),
        "base_rate": float(y.mean()),
        "pr_auc_lift_over_base_rate": float(pr_auc(y, s) / y.mean()),
        "roc_auc_rank_to_pixel_hit": roc_auc(y, -prop["proposal_rank"].to_numpy()),
        "hit_score_mean": float(prop.loc[prop["gt_hit_pixel"], "proposal_score"].mean()),
        "miss_score_mean": float(prop.loc[~prop["gt_hit_pixel"], "proposal_score"].mean()),
        "hit_score_median": float(prop.loc[prop["gt_hit_pixel"], "proposal_score"].median()),
        "miss_score_median": float(prop.loc[~prop["gt_hit_pixel"], "proposal_score"].median()),
        "score_min": float(prop["proposal_score"].min()), "score_max": mx,
        "score_range": float(mx - prop["proposal_score"].min()),
        "score_iqr": float(prop["proposal_score"].quantile(.75) - prop["proposal_score"].quantile(.25)),
        "unique_score_values": int(prop["proposal_score"].nunique()),
        "saturated_count": int(prop["score_saturated"].sum()),
        "saturated_fraction": float(prop["score_saturated"].mean()),
        "saturated_pixel_hit_rate": float(prop.loc[prop["score_saturated"], "gt_hit_pixel"].mean()),
        "below_max_pixel_hit_rate": float(prop.loc[~prop["score_saturated"], "gt_hit_pixel"].mean()),
        "interpretation": "DIAGNOSTIC_ONLY__NOT_A_DEPLOYMENT_PERFORMANCE_CLAIM",
        "threshold_chosen_from_labels": "NO",
    }

    # ================= floor trade-off (descriptive; floors are marginal-derived) =================
    floors = []
    for name, fl in [("baseline_0.10", OLD_FLOOR)] + list(FLOORS.items()):
        a = prop[prop["proposal_score"] >= fl]; r = prop[prop["proposal_score"] < fl]
        floors.append({
            "floor_label": name, "floor_value": fl,
            "accepted": len(a), "accepted_hits": int(a["gt_hit_pixel"].sum()),
            "accepted_off_target": int((~a["gt_hit_pixel"]).sum()),
            "rejected": len(r), "hits_lost": int(r["gt_hit_pixel"].sum()),
            "off_target_removed": int((~r["gt_hit_pixel"]).sum()),
            "hits_lost_fraction_of_all_hits": float(r["gt_hit_pixel"].sum() / max(int(y.sum()), 1)),
            "off_target_removed_fraction": float((~r["gt_hit_pixel"]).sum() / max(int((~prop["gt_hit_pixel"]).sum()), 1)),
            "floor_derivation": "FROZEN_PROPOSAL_THRESHOLD" if fl == OLD_FLOOR
                                else "MARGINAL_SCORE_QUANTILE_WITHOUT_GT_LABELS",
        })

    # ================= §7 case proposal burden (103 rows) =================
    shapes = casep.set_index("sample_id")[["native_H", "native_W"]].to_dict("index")
    burden = []
    for sid, g in prop.groupby("sample_id"):
        shp = (int(shapes[sid]["native_H"]), int(shapes[sid]["native_W"]))
        img_area = shp[0] * shp[1]
        hit = g[g["gt_hit_pixel"]]; miss = g[~g["gt_hit_pixel"]]
        all_rects = list(zip(g["clip_y1"], g["clip_y2"], g["clip_x1"], g["clip_x2"]))
        miss_rects = list(zip(miss["clip_y1"], miss["clip_y2"], miss["clip_x1"], miss["clip_x2"]))
        u_all = union_area(all_rects, shp)
        u_miss = union_area(miss_rects, shp)
        sc = g["proposal_score"].sort_values(ascending=False).to_numpy()
        cc = compcov[compcov["sample_id"] == sid]
        burden.append({
            "sample_id": sid, "native_H": shp[0], "native_W": shp[1],
            "proposal_count": len(g),
            "gt_hit_proposal_count": len(hit),
            "gt_miss_proposal_count": len(miss),
            "fraction_proposals_off_target": float(len(miss) / len(g)) if len(g) else np.nan,
            "proposal_union_area_fraction": float(u_all / img_area),
            "off_target_proposal_union_area_fraction": float(u_miss / img_area),
            "top_proposal_score": float(sc[0]) if len(sc) else np.nan,
            "second_proposal_score": float(sc[1]) if len(sc) > 1 else np.nan,
            "minimum_accepted_score_under_old_policy": OLD_FLOOR,
            "number_of_components": int(len(cc)),
            "bbox_covered90_count": int(cc["bbox_covered90"].sum()),
            "bbox_covered90_fraction": float(cc["bbox_covered90"].mean()) if len(cc) else np.nan,
            "bbox_covered50_count": int(cc["bbox_covered50"].sum()),
            "bbox_any_overlap_count": int(cc["bbox_any_overlap"].sum()),
            "bbox_mean_component_coverage": float(cc["bbox_coverage_fraction"].mean()) if len(cc) else np.nan,
            "pixel_covered90_count": int(cc["pixel_covered90"].sum()),
            "pixel_mean_component_coverage": float(cc["pixel_coverage_fraction"].mean()) if len(cc) else np.nan,
        })
    burden_df = pd.DataFrame(burden).sort_values("sample_id").reset_index(drop=True)
    assert len(burden_df) == 103, len(burden_df)
    burden_df.to_csv(TABLES / "post_phase13_r0_case_proposal_burden.csv", index=False)

    # ================= §8 proposal burden -> segmentation linkage =================
    # rename colliding columns for the joins (the §7 CSV keeps the required names)
    bmerge = burden_df.rename(columns={
        "proposal_count": "b_proposal_count",
        "proposal_union_area_fraction": "b_proposal_union_area_fraction",
        "number_of_components": "b_number_of_components",
    })
    linkage_rows = []
    scatter_rows = []
    for key in MODELS:
        sub = cm[cm["model"] == key].merge(bmerge, on="sample_id", how="left", validate="one_to_one")
        assert len(sub) == 103, len(sub)
        fp_delta = sub["predicted_fp_pixels"] - sub["global_fp_pixels"]
        dice_delta = sub["predicted_dice"] - sub["global_dice"]
        pairs = {
            "gt_miss_proposal_count__vs__predicted_minus_global_dice": (sub["gt_miss_proposal_count"], dice_delta),
            "gt_miss_proposal_count__vs__fp_pixel_delta": (sub["gt_miss_proposal_count"], fp_delta),
            "off_target_support_fraction__vs__predicted_minus_global_dice": (sub["off_target_proposal_union_area_fraction"], dice_delta),
            "off_target_support_fraction__vs__fp_pixel_delta": (sub["off_target_proposal_union_area_fraction"], fp_delta),
            "total_proposal_count__vs__fp_pixel_delta": (sub["b_proposal_count"], fp_delta),
            "top_proposal_score__vs__predicted_minus_global_dice": (sub["top_proposal_score"], dice_delta),
        }
        for name, (a, b) in pairs.items():
            rho = float(pd.Series(a).corr(pd.Series(b), method="spearman"))
            linkage_rows.append({
                "model": key, "model_display": DISPLAY[key],
                "x_quantity": name.split("__vs__")[0], "y_quantity": name.split("__vs__")[1],
                "spearman_rho": rho, "n_cases": int(len(sub)),
                "relationship_language": "ASSOCIATION__DESCRIPTIVE_LINKAGE__NOT_CAUSE",
                "p_value_claimed": "NO",
            })
        for i, r in sub.iterrows():
            scatter_rows.append({
                "sample_id": r["sample_id"], "model": key,
                "gt_miss_proposal_count": int(r["gt_miss_proposal_count"]),
                "gt_hit_proposal_count": int(r["gt_hit_proposal_count"]),
                "proposal_count": int(r["b_proposal_count"]),
                "off_target_support_fraction": float(r["off_target_proposal_union_area_fraction"]),
                "proposal_union_area_fraction": float(r["b_proposal_union_area_fraction"]),
                "top_proposal_score": float(r["top_proposal_score"]),
                "predicted_minus_global_dice": float(r["predicted_dice"] - r["global_dice"]),
                "fp_pixel_delta": float(r["predicted_fp_pixels"] - r["global_fp_pixels"]),
                "fn_pixel_delta": float(r["predicted_fn_pixels"] - r["global_fn_pixels"]),
                "global_dice": float(r["global_dice"]),
                "predicted_dice": float(r["predicted_dice"]),
                "case_dice_improved": bool(r["case_dice_improved"]),
                "case_dice_worsened": bool(r["case_dice_worsened"]),
            })
    linkage_df = pd.DataFrame(linkage_rows)
    linkage_df.to_csv(TABLES / "post_phase13_r0_proposal_to_segmentation_linkage.csv", index=False)
    scatter_df = pd.DataFrame(scatter_rows)
    scatter_df.to_csv(TABLES / "post_phase13_r0_proposal_to_segmentation_scatter.csv", index=False)

    # ================= §9 improved vs worsened context =================
    imp_wor = []
    for key in MODELS:
        sub = scatter_df[scatter_df["model"] == key].merge(
            burden_df[["sample_id", "bbox_covered90_fraction", "bbox_mean_component_coverage",
                       "number_of_components"]], on="sample_id", how="left")
        for label, mask in (("improved", sub["case_dice_improved"]), ("worsened", sub["case_dice_worsened"])):
            g = sub[mask]
            imp_wor.append({
                "model": key, "model_display": DISPLAY[key], "case_outcome": label, "n_cases": len(g),
                "gt_hit_proposal_count_mean": float(g["gt_hit_proposal_count"].mean()),
                "gt_miss_proposal_count_mean": float(g["gt_miss_proposal_count"].mean()),
                "proposal_union_area_fraction_mean": float(g["proposal_union_area_fraction"].mean()),
                "top_proposal_score_mean": float(g["top_proposal_score"].mean()),
                "bbox_covered90_fraction_mean": float(g["bbox_covered90_fraction"].mean()),
                "bbox_mean_component_coverage_mean": float(g["bbox_mean_component_coverage"].mean()),
                "predicted_minus_global_dice_mean": float(g["predicted_minus_global_dice"].mean()),
                "fp_pixel_delta_mean": float(g["fp_pixel_delta"].mean()),
                "language": "DIAGNOSTIC_ONLY__NO_NEW_GATE_SUBGROUP__NO_CLASSIFIER",
            })
    imp_wor_df = pd.DataFrame(imp_wor)
    imp_wor_df.to_csv(TABLES / "post_phase13_r0_improved_vs_worsened_context.csv", index=False)

    # ================= §10 component recovery context =================
    rec = []
    for key in MODELS:
        c = compm[compm["model"] == key].merge(
            burden_df[["sample_id", "gt_miss_proposal_count", "off_target_proposal_union_area_fraction",
                       "proposal_count"]], on="sample_id", how="left")
        for flag, mask in (("recovered", c["GLOBAL_TO_PREDICTED_RECOVERY"]),
                           ("lost", c["GLOBAL_TO_PREDICTED_LOSS"]),
                           ("not_recovered", ~c["GLOBAL_TO_PREDICTED_RECOVERY"])):
            g = c[mask]
            rec.append({
                "model": key, "model_display": DISPLAY[key], "event": flag, "n_components": len(g),
                "bbox_covered90_count": int(g["part1c_bbox_covered90"].sum()),
                "bbox_covered90_rate": float(g["part1c_bbox_covered90"].mean()) if len(g) else np.nan,
                "bbox_covered50_count": int(g["part1c_bbox_covered50"].sum()),
                "bbox_covered50_rate": float(g["part1c_bbox_covered50"].mean()) if len(g) else np.nan,
                "bbox_any_overlap_count": int(g["part1c_bbox_any_overlap"].sum()),
                "bbox_any_overlap_rate": float(g["part1c_bbox_any_overlap"].mean()) if len(g) else np.nan,
                "mean_parent_gt_miss_proposal_count": float(g["gt_miss_proposal_count"].mean()) if len(g) else np.nan,
                "mean_parent_off_target_support_fraction": float(g["off_target_proposal_union_area_fraction"].mean()) if len(g) else np.nan,
            })
        for st in ("TINY", "SMALL", "MEDIUM", "LARGE"):
            g = c[c["size_stratum"] == st]
            rec.append({
                "model": key, "model_display": DISPLAY[key], "event": f"stratum_{st}", "n_components": len(g),
                "bbox_covered90_count": int(g["part1c_bbox_covered90"].sum()),
                "bbox_covered90_rate": float(g["part1c_bbox_covered90"].mean()) if len(g) else np.nan,
                "bbox_covered50_count": int(g["part1c_bbox_covered50"].sum()),
                "bbox_covered50_rate": float(g["part1c_bbox_covered50"].mean()) if len(g) else np.nan,
                "bbox_any_overlap_count": int(g["part1c_bbox_any_overlap"].sum()),
                "bbox_any_overlap_rate": float(g["part1c_bbox_any_overlap"].mean()) if len(g) else np.nan,
                "recovered_count": int(g["GLOBAL_TO_PREDICTED_RECOVERY"].sum()),
                "lost_count": int(g["GLOBAL_TO_PREDICTED_LOSS"].sum()),
            })
    rec_df = pd.DataFrame(rec)
    rec_df.to_csv(TABLES / "post_phase13_r0_component_recovery_context.csv", index=False)

    # ================= §12/§13 R1 candidate family (design only) =================
    fam = []
    fam.append({
        "config_id": "R1-C0", "role": "CONTROL_BASELINE",
        "score_acceptance_floor": OLD_FLOOR, "max_accepted_proposals": OLD_MAX,
        "floor_label": "frozen_part1c_threshold", "zero_acceptance_allowed": "YES",
        "changed_from_phase13": "NONE__PHASE13_CONTROL",
    })
    i = 1
    for fl_label, fl in FLOORS.items():
        for mm in MAXES:
            fam.append({
                "config_id": f"R1-C{i}", "role": "CANDIDATE",
                "score_acceptance_floor": fl, "max_accepted_proposals": mm,
                "floor_label": f"marginal_score_{fl_label}", "zero_acceptance_allowed": "YES",
                "changed_from_phase13": "SCORE_ACCEPTANCE_FLOOR+MAX_ACCEPTED_PROPOSALS",
            })
            i += 1
    fam_df = pd.DataFrame(fam)
    assert len(fam_df) <= 8, len(fam_df)
    fam_df.to_csv(TABLES / "post_phase13_regional_revision_r1_candidate_family.csv", index=False)

    # label-blind floor description (marginal quantiles, no GT)
    floor_desc = {k: {"floor": v, "marginal_quantile_of_that_floor":
                      float((prop["proposal_score"] < v).mean())} for k, v in FLOORS.items()}

    return {
        "prop": prop, "diag": diag, "sep": sep, "floors": floors,
        "burden": burden_df, "linkage": linkage_df, "scatter": scatter_df,
        "imp_wor": imp_wor_df, "rec": rec_df, "family": fam_df, "floor_desc": floor_desc,
        "mx": mx, "MODELS": MODELS, "DISPLAY": DISPLAY,
    }


if __name__ == "__main__":
    r = main()
    print("=== §5 rank diagnostics ===")
    print(r["diag"].to_string(index=False))
    print("\n=== §6 separability ===")
    for k, v in r["sep"].items():
        print(f"  {k}: {v}")
    print("\n=== floor trade-off ===")
    print(pd.DataFrame(r["floors"]).to_string(index=False))
    print("\n=== R1 candidate family ===")
    print(r["family"].to_string(index=False))
    print("\n=== §8 linkage (Spearman) ===")
    print(r["linkage"].pivot_table(index=["x_quantity", "y_quantity"], columns="model_display",
                                   values="spearman_rho").round(4).to_string())
