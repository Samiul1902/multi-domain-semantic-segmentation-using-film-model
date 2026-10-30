"""POST-PHASE-13 R1 — summary tables from the case/component policy tables (§11–§15)."""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\Softfors\jup")
TABLES = ROOT / "reports" / "tables"
CONFIGS = ["R1-C0", "R1-C1", "R1-C2", "R1-C3", "R1-C4", "R1-C5", "R1-C6"]
MODELS = ["unet", "attention_unet", "unetpp", "deeplabv3plus"]
DISPLAY = {"unet": "UNet", "attention_unet": "Attention U-Net",
           "unetpp": "UNet++", "deeplabv3plus": "DeepLabV3+"}
TOL = 1e-12


def sha(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def retention(pred_v, glob_v, orac_v):
    den = orac_v - glob_v
    return (pred_v - glob_v) / den if den > 0 else None


def main() -> dict:
    case = pd.read_csv(TABLES / "post_phase13_r1_case_model_policy_metrics.csv")
    comp = pd.read_csv(TABLES / "post_phase13_r1_component_model_policy_metrics.csv")
    prop = pd.read_csv(TABLES / "phase13_part1c_best_checkpoint_proposals.csv")
    hit = {(r.sample_id, int(r.proposal_rank)): bool(r.overlaps_any_gt_pixel) for r in prop.itertuples()}
    total_hits = int(sum(hit.values())); total_misses = len(hit) - total_hits

    # ---------------- §11 model-policy summary (28 rows) ----------------
    rows = []
    for cfg in CONFIGS:
        for key in MODELS:
            s = case[(case.config_id == cfg) & (case.model == key)]
            c = comp[(comp.config_id == cfg) & (comp.model == key)]
            assert len(s) == 103 and len(c) == 152, (cfg, key, len(s), len(c))
            dG = float(s["global_dice"].mean()); dO = float(s["oracle_dice"].mean())
            dP = float(s["policy_dice"].mean())
            iG = float(s["global_iou"].mean()); iO = float(s["oracle_iou"].mean())
            iP = float(s["policy_iou"].mean())
            imp = int((s["policy_dice"] > s["global_dice"] + TOL).sum())
            wor = int((s["policy_dice"] < s["global_dice"] - TOL).sum())
            same = int((abs(s["policy_dice"] - s["global_dice"]) <= TOL).sum())
            rows.append({
                "config_id": cfg, "model": key, "model_display": DISPLAY[key],
                "accepted_proposals_total": int(s["accepted_proposal_count"].sum()),
                "mean_accepted_proposals_per_image": float(s["accepted_proposal_count"].mean()),
                "cases_with_zero_intervention": int((s["accepted_proposal_count"] == 0).sum()),
                "mean_intervention_union_area": float(s["accepted_union_area_fraction"].mean()),
                "global_macro_dice": dG, "oracle_macro_dice": dO, "policy_macro_dice": dP,
                "DELTA_POLICY_GLOBAL_DICE": dP - dG,
                "RETENTION_DICE": retention(dP, dG, dO),
                "ORACLE_GAP_DICE": dP - dO,
                "global_macro_iou": iG, "oracle_macro_iou": iO, "policy_macro_iou": iP,
                "global_macro_precision": float(s["global_precision"].mean()),
                "oracle_macro_precision": float(s["oracle_precision"].mean()),
                "policy_macro_precision": float(s["policy_precision"].mean()),
                "global_macro_recall": float(s["global_recall"].mean()),
                "oracle_macro_recall": float(s["oracle_recall"].mean()),
                "policy_macro_recall": float(s["policy_recall"].mean()),
                "mean_global_fp": float(s["global_fp_pixels"].mean()),
                "mean_policy_fp": float(s["policy_fp_pixels"].mean()),
                "mean_global_fn": float(s["global_fn_pixels"].mean()),
                "mean_policy_fn": float(s["policy_fn_pixels"].mean()),
                "mean_fp_delta_vs_global": float((s["policy_fp_pixels"] - s["global_fp_pixels"]).mean()),
                "mean_fn_delta_vs_global": float((s["policy_fn_pixels"] - s["global_fn_pixels"]).mean()),
                "cases_improved": imp, "cases_same": same, "cases_worse": wor,
                "component_recoveries_vs_global": int(c["GLOBAL_TO_R1_RECOVERY"].sum()),
                "component_losses_vs_global": int(c["GLOBAL_TO_R1_LOSS"].sum()),
                "empty_recoveries": int((s["global_prediction_empty"] & ~s["policy_prediction_empty"]).sum()),
                "new_empty_predictions": int((~s["global_prediction_empty"] & s["policy_prediction_empty"]).sum()),
            })
    summ = pd.DataFrame(rows)
    assert len(summ) == 28, len(summ)
    summ.to_csv(TABLES / "post_phase13_r1_model_policy_summary.csv", index=False)

    # ---------------- §12 policy intervention summary (7 rows, model-independent) ----------------
    per_case = case[case.model == "unet"][["config_id", "sample_id", "accepted_proposal_count",
                                           "accepted_union_area_fraction"]]
    mem = pd.read_csv(TABLES / "post_phase13_regional_revision_r1_frozen_membership.csv")
    c0_hits = sum(1 for k, v in hit.items() if v and k in set(
        map(tuple, mem[(mem.config_id == "R1-C0") & mem.accepted][["sample_id", "proposal_rank"]].to_numpy())))
    irows = []
    for cfg in CONFIGS:
        acc = set(map(tuple, mem[(mem.config_id == cfg) & mem.accepted]
                      [["sample_id", "proposal_rank"]].to_numpy()))
        rej = set(hit.keys()) - acc
        a_hits = sum(1 for k in acc if hit[k])
        a_miss = sum(1 for k in acc if not hit[k])
        r_miss = sum(1 for k in rej if not hit[k])
        pc = per_case[per_case.config_id == cfg]["accepted_proposal_count"]
        uf = per_case[per_case.config_id == cfg]["accepted_union_area_fraction"]
        irows.append({
            "config_id": cfg,
            "accepted_proposals": len(acc), "rejected_proposals": len(rej),
            "cases_zero_accepted": int((pc == 0).sum()),
            "mean_accepted_proposals": float(pc.mean()),
            "median_accepted_proposals": float(pc.median()),
            "accepted_union_area_mean": float(uf.mean()),
            "accepted_union_area_median": float(uf.median()),
            "accepted_union_area_min": float(uf.min()),
            "accepted_union_area_max": float(uf.max()),
            "gt_hit_accepted_proposals": a_hits,
            "gt_miss_accepted_proposals": a_miss,
            "accepted_gt_miss_fraction": float(a_miss / len(acc)) if acc else np.nan,
            "gt_hit_retention_relative_to_C0": float(a_hits / c0_hits) if c0_hits else np.nan,
            "gt_miss_rejection_relative_to_C0": int(r_miss),
            "gt_miss_rejected_fraction_of_all_misses": float(r_miss / total_misses) if total_misses else np.nan,
            "label_blindness_note": "GT FIELDS ARE POST-FREEZE DESCRIPTIVE EVALUATION ONLY; MEMBERSHIP IS LABEL-BLIND",
        })
    inter = pd.DataFrame(irows)
    assert len(inter) == 7, len(inter)
    inter.to_csv(TABLES / "post_phase13_r1_policy_intervention_summary.csv", index=False)

    # ---------------- §15 cross-architecture (7 rows) ----------------
    crows = []
    for cfg in CONFIGS:
        s = case[case.config_id == cfg]
        piv_i = s.pivot_table(index="sample_id", columns="model", values="policy_dice", aggfunc="first")
        piv_g = s.pivot_table(index="sample_id", columns="model", values="global_dice", aggfunc="first")
        imp = (piv_i > piv_g + TOL).sum(axis=1)
        wor = (piv_i < piv_g - TOL).sum(axis=1)
        c = comp[comp.config_id == cfg]
        g = c.groupby(["sample_id", "native_component_id"])
        crows.append({
            "config_id": cfg,
            "cases_improved_all_four": int((imp == 4).sum()),
            "cases_nonworse_all_four": int((wor == 0).sum()),
            "cases_worse_all_four": int((wor == 4).sum()),
            "components_recovered_by_at_least_one": int(g["GLOBAL_TO_R1_RECOVERY"].max().sum()),
            "components_recovered_by_all_four": int((g["GLOBAL_TO_R1_RECOVERY"].sum() == 4).sum()),
            "components_lost_by_at_least_one": int(g["GLOBAL_TO_R1_LOSS"].max().sum()),
            "components_lost_by_all_four": int((g["GLOBAL_TO_R1_LOSS"].sum() == 4).sum()),
        })
    cross = pd.DataFrame(crows)
    assert len(cross) == 7, len(cross)
    cross.to_csv(TABLES / "post_phase13_r1_cross_architecture_policy_summary.csv", index=False)

    return {"summ": summ, "inter": inter, "cross": cross,
            "total_hits": total_hits, "total_misses": total_misses, "c0_hits": c0_hits}


if __name__ == "__main__":
    pd.set_option("display.width", 300)
    r = main()
    print("=== §11 model-policy summary (28 rows) ===")
    print(r["summ"][["config_id", "model_display", "accepted_proposals_total",
                     "mean_accepted_proposals_per_image", "cases_with_zero_intervention",
                     "policy_macro_dice", "DELTA_POLICY_GLOBAL_DICE", "RETENTION_DICE",
                     "mean_fp_delta_vs_global", "cases_worse",
                     "component_recoveries_vs_global", "component_losses_vs_global"]].to_string(index=False))
    print("\n=== §12 policy intervention summary (7 rows) ===")
    print(r["inter"].to_string(index=False))
    print("\n=== §15 cross-architecture (7 rows) ===")
    print(r["cross"].to_string(index=False))
