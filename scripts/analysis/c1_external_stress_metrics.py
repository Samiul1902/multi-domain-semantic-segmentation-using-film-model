"""External stress-test metrics, distributions and domain-shift analysis.

Consumes only the arrays written by ``c1_external_stress_eval.py`` and the frozen
Phase 21 reference record.  Writes:

  reports/tables/c1_external_stress_per_case.csv
  reports/tables/c1_external_stress_summary.csv
  reports/tables/c1_external_stress_stones_subgroups.csv
  reports/tables/c1_external_stress_paired.csv
  reports/tables/c1_external_stress_domain_shift.csv
  reports/audits/c1_external_stress_v1_0/metrics_summary.json

Design rules enforced here (from the frozen plan):

  * surface metrics are in PIXELS; no millimetre figure is produced anywhere;
  * undefined metrics are NaN with a reason, never 0 and never silently dropped;
  * aggregation is per-cohort MACRO over cases; pooled pixel aggregation is
    computed separately and labelled secondary;
  * no cross-cohort pooled Dice;
  * ``p_values_computed == 0``.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.ndimage import binary_erosion, distance_transform_edt, generate_binary_structure

ROOT = Path(r"D:\Softfors\jup")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))
AUD = ROOT / "reports" / "audits" / "c1_external_stress_v1_0"
TAB = ROOT / "reports" / "tables"
CACHE = ROOT / "data_cache" / "c1_external_stress_v1_0"

SEG = 0.5
NSD_TAU_PX = 2.0
N_BOOT = 2000
BOOT_SEED = 42

COHORTS = [
    ("cvc", "CVC-ClinicDB", "KVASIR"),
    ("breast", "BrEaST-Lesions-USG", "BUSI"),
    ("stones", "Stones_where_are_you", "KUB"),
]

# frozen Phase 21 VAL808 per-domain reference (internal, NOT this population)
PHASE21 = ROOT / "reports" / "audits" / "phase21_analysis.json"


# --------------------------------------------------------------------------- #
# surface metrics
# --------------------------------------------------------------------------- #
_STRUCT = generate_binary_structure(2, 1)


def _surface(mask: np.ndarray) -> np.ndarray:
    """Boundary pixels of a binary mask (mask minus its erosion)."""
    if not mask.any():
        return np.zeros_like(mask, dtype=bool)
    eroded = binary_erosion(mask, _STRUCT, border_value=0)
    return mask & ~eroded


def surface_metrics(pred: np.ndarray, gt: np.ndarray) -> dict:
    """HD95, ASSD and NSD@tau in PIXELS. NaN with a reason when undefined."""
    if not pred.any() or not gt.any():
        return {"HD95_px": np.nan, "ASSD_px": np.nan, "NSD_2px": np.nan,
                "surface_undefined_reason": ("empty_prediction" if not pred.any()
                                             else "empty_ground_truth")}
    ps, gs = _surface(pred), _surface(gt)
    # distance from every voxel to the nearest surface point of the other mask
    dt_to_pred = distance_transform_edt(~ps)
    dt_to_gt = distance_transform_edt(~gs)
    d_gt2pred = dt_to_pred[gs]
    d_pred2gt = dt_to_gt[ps]
    if d_gt2pred.size == 0 or d_pred2gt.size == 0:
        return {"HD95_px": np.nan, "ASSD_px": np.nan, "NSD_2px": np.nan,
                "surface_undefined_reason": "empty_surface_set"}
    both = np.concatenate([d_gt2pred, d_pred2gt])
    nsd = 0.5 * (float(np.mean(d_gt2pred <= NSD_TAU_PX))
                 + float(np.mean(d_pred2gt <= NSD_TAU_PX)))
    return {"HD95_px": float(np.percentile(both, 95)),
            "ASSD_px": float(both.mean()),
            "NSD_2px": nsd,
            "surface_undefined_reason": ""}


def pixel_metrics(pred: np.ndarray, gt: np.ndarray) -> dict:
    tp = int(np.count_nonzero(pred & gt))
    fp = int(np.count_nonzero(pred & ~gt))
    fn = int(np.count_nonzero(~pred & gt))
    tn = int(np.count_nonzero(~pred & ~gt))
    den_dice = 2 * tp + fp + fn
    den_iou = tp + fp + fn
    return {
        "TP": tp, "FP": fp, "FN": fn, "TN": tn,
        "Dice": (2 * tp / den_dice) if den_dice else np.nan,
        "IoU": (tp / den_iou) if den_iou else np.nan,
        "Precision": (tp / (tp + fp)) if (tp + fp) else np.nan,
        "Recall": (tp / (tp + fn)) if (tp + fn) else np.nan,
        "Specificity": (tn / (tn + fp)) if (tn + fp) else np.nan,
        "Accuracy": ((tp + tn) / (tp + fp + fn + tn)) if (tp + fp + fn + tn) else np.nan,
        "gt_pixels": int(gt.sum()), "pred_pixels": int(pred.sum()),
    }


def region_size_error(pred_px: int, gt_px: int) -> float:
    return ((pred_px - gt_px) / gt_px) if gt_px else np.nan


# --------------------------------------------------------------------------- #
# aggregation helpers
# --------------------------------------------------------------------------- #
def describe(values: np.ndarray) -> dict:
    v = np.asarray(values, dtype=np.float64)
    finite = v[np.isfinite(v)]
    if finite.size == 0:
        return {"n_total": int(v.size), "n_defined": 0, "mean": np.nan, "sd": np.nan,
                "median": np.nan, "q1": np.nan, "q3": np.nan, "min": np.nan, "max": np.nan}
    return {
        "n_total": int(v.size), "n_defined": int(finite.size),
        "mean": float(finite.mean()),
        "sd": float(finite.std(ddof=1)) if finite.size > 1 else np.nan,
        "median": float(np.median(finite)),
        "q1": float(np.percentile(finite, 25)),
        "q3": float(np.percentile(finite, 75)),
        "min": float(finite.min()), "max": float(finite.max()),
    }


def cluster_bootstrap_ci(values: np.ndarray, clusters: np.ndarray,
                         n_boot: int = N_BOOT, seed: int = BOOT_SEED) -> dict:
    """Percentile bootstrap CI of the macro mean, resampling CLUSTERS."""
    v = np.asarray(values, dtype=np.float64)
    c = np.asarray(clusters)
    uniq = pd.unique(c)
    if uniq.size < 2 or v.size < 3:
        return {"n_clusters": int(uniq.size), "ci_low": np.nan, "ci_high": np.nan,
                "note": "insufficient clusters for a bootstrap interval"}
    idx_by_cluster = {u: np.flatnonzero(c == u) for u in uniq}
    rng = np.random.default_rng(seed)
    means = np.empty(n_boot, dtype=np.float64)
    for b in range(n_boot):
        pick = rng.choice(uniq, size=uniq.size, replace=True)
        sel = np.concatenate([idx_by_cluster[u] for u in pick])
        sub = v[sel]
        finite = sub[np.isfinite(sub)]
        means[b] = finite.mean() if finite.size else np.nan
    ok = means[np.isfinite(means)]
    if ok.size == 0:
        return {"n_clusters": int(uniq.size), "ci_low": np.nan, "ci_high": np.nan,
                "note": "no finite bootstrap replicates"}
    return {
        "n_clusters": int(uniq.size), "n_resamples": int(n_boot), "seed": int(seed),
        "scheme": "percentile, cluster-level",
        "ci_low": float(np.percentile(ok, 2.5)),
        "ci_high": float(np.percentile(ok, 97.5)),
    }


# --------------------------------------------------------------------------- #
def main() -> int:
    rows = []
    meta_rows = []
    for key, name, analogue in COHORTS:
        d = CACHE / key
        pg = np.load(d / "prob_global.npy")
        pb = np.load(d / "prob_barr.npy")
        gt = np.load(d / "gt.npy").astype(bool)
        ids = json.loads((d / "sample_ids.json").read_text(encoding="utf-8"))
        states = pd.read_csv(d / "barr_states.csv")
        assert len(ids) == pg.shape[0] == pb.shape[0] == gt.shape[0] == len(states)

        for i, sid in enumerate(ids):
            g = gt[i]
            for arm, prob in (("global", pg[i]), ("barr", pb[i])):
                pred = prob >= SEG
                m = pixel_metrics(pred, g)
                m.update(surface_metrics(pred, g))
                st = states.iloc[i]
                rows.append({
                    "cohort_key": key, "cohort": name, "domain_analogue": analogue,
                    "sample_id": sid, "index": i, "arm": arm, **m,
                    "region_size_error": region_size_error(m["pred_pixels"], m["gt_pixels"]),
                    "pred_empty": bool(m["pred_pixels"] == 0),
                    "gt_empty": bool(m["gt_pixels"] == 0),
                    "fp_only_case": bool(m["gt_pixels"] == 0 and m["pred_pixels"] > 0),
                    "fn_only_case": bool(m["gt_pixels"] > 0 and m["pred_pixels"] == 0),
                    "state": st["state"],
                    "router_score": st["router_score"],
                    "safety_prob": st["safety_prob"],
                    "cluster_id": (states.iloc[i].get("cluster_id", sid)
                                   if "cluster_id" in states.columns else sid),
                    "latency_s": (st["latency_global_s"] if arm == "global"
                                  else st["latency_barr_s"]),
                    "has_stone_annotation": st.get("has_stone_annotation", ""),
                })
        # cluster ids live in the eval metadata; rebuild from the manifest order
        meta_rows.append({"cohort_key": key, "cohort": name, "n": len(ids)})

    pc = pd.DataFrame(rows)

    # ---- attach cluster ids (sequence_id / case_id) ----------------------- #
    from c1_external_stress_eval import build_cohorts  # local import: reuse frozen logic
    co = build_cohorts()
    cluster_map = {}
    for k, v in co.items():
        for c in v["cases"]:
            cluster_map[(k, c["sample_id"])] = c["cluster_id"]
    pc["cluster_id"] = [cluster_map.get((k, s), s)
                        for k, s in zip(pc["cohort_key"], pc["sample_id"])]

    pc.to_csv(TAB / "c1_external_stress_per_case.csv", index=False)

    # ---- summary ---------------------------------------------------------- #
    metric_cols = ["Dice", "IoU", "Precision", "Recall", "Specificity", "Accuracy",
                   "HD95_px", "ASSD_px", "NSD_2px", "region_size_error", "latency_s"]
    sum_rows = []
    for (key, name, analogue), grp in pc.groupby(["cohort_key", "cohort", "domain_analogue"],
                                                sort=False):
        for arm, g2 in grp.groupby("arm", sort=False):
            for col in metric_cols:
                s = describe(g2[col].to_numpy())
                ci = (cluster_bootstrap_ci(g2[col].to_numpy(), g2["cluster_id"].to_numpy())
                      if col in ("Dice", "IoU", "HD95_px", "ASSD_px", "NSD_2px") else
                      {"ci_low": np.nan, "ci_high": np.nan})
                sum_rows.append({
                    "cohort_key": key, "cohort": name, "domain_analogue": analogue,
                    "arm": arm, "metric": col, **s,
                    "ci_low": ci.get("ci_low", np.nan),
                    "ci_high": ci.get("ci_high", np.nan),
                    "n_clusters": ci.get("n_clusters", np.nan),
                    "aggregation": "macro over cases (equal case weight)",
                })
            # counts
            sum_rows.append({
                "cohort_key": key, "cohort": name, "domain_analogue": analogue,
                "arm": arm, "metric": "empty_prediction_rate",
                **describe(g2["pred_empty"].astype(float).to_numpy()),
                "ci_low": np.nan, "ci_high": np.nan, "n_clusters": np.nan,
                "aggregation": "fraction of cases",
            })
            for flag in ("fp_only_case", "fn_only_case"):
                cnt = int(g2[flag].sum())
                sum_rows.append({
                    "cohort_key": key, "cohort": name, "domain_analogue": analogue,
                    "arm": arm, "metric": flag + "_count",
                    "n_total": int(len(g2)), "n_defined": int(len(g2)),
                    "mean": float(cnt), "sd": np.nan, "median": float(cnt),
                    "q1": np.nan, "q3": np.nan, "min": np.nan, "max": np.nan,
                    "ci_low": np.nan, "ci_high": np.nan, "n_clusters": np.nan,
                    "aggregation": "count of cases (mean field = count)",
                })
    summ = pd.DataFrame(sum_rows)
    summ.to_csv(TAB / "c1_external_stress_summary.csv", index=False)

    # ---- pooled pixel aggregation (secondary, labelled) ------------------- #
    pooled = []
    for (key, name), grp in pc.groupby(["cohort_key", "cohort"], sort=False):
        for arm, g2 in grp.groupby("arm", sort=False):
            tp, fp, fn = int(g2["TP"].sum()), int(g2["FP"].sum()), int(g2["FN"].sum())
            pooled.append({"cohort_key": key, "cohort": name, "arm": arm,
                           "pooled_dice": 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else np.nan,
                           "TP": tp, "FP": fp, "FN": fn,
                           "aggregation": "SECONDARY pooled pixel-level"})
    pd.DataFrame(pooled).to_csv(TAB / "c1_external_stress_pooled.csv", index=False)

    # ---- Stones subgroups ------------------------------------------------- #
    st = pc[pc["cohort_key"] == "stones"].copy()
    st["subgroup"] = np.where(st["has_stone_annotation"].astype(str).str.lower() == "true",
                              "six_positive", "fourteen_absent")
    sub_rows = []
    for (sg, arm), g2 in st.groupby(["subgroup", "arm"], sort=False):
        for col in ("Dice", "IoU", "Recall", "Precision", "HD95_px"):
            sub_rows.append({"subgroup": sg, "n": int(len(g2)), "arm": arm, "metric": col,
                             **describe(g2[col].to_numpy())})
        sub_rows.append({"subgroup": sg, "n": int(len(g2)), "arm": arm,
                         "metric": "empty_prediction_rate",
                         **describe(g2["pred_empty"].astype(float).to_numpy())})
    pd.DataFrame(sub_rows).to_csv(TAB / "c1_external_stress_stones_subgroups.csv", index=False)

    # ---- paired Global vs BARR -------------------------------------------- #
    wide = pc.pivot_table(index=["cohort_key", "cohort", "sample_id", "state"],
                          columns="arm", values="Dice", aggfunc="first").reset_index()
    wide["delta_dice"] = wide["barr"] - wide["global"]
    wide["outcome"] = np.where(wide["delta_dice"] > 1e-12, "improved",
                               np.where(wide["delta_dice"] < -1e-12, "worsened", "unchanged"))
    wide.to_csv(TAB / "c1_external_stress_paired.csv", index=False)

    paired = {}
    for key, name, _ in COHORTS:
        g = wide[wide["cohort_key"] == key]
        sel = g[g["state"].isin(["ACCEPTED", "REJECTED", "EXECUTED", "ROUTED"])]
        paired[key] = {
            "n": int(len(g)),
            "delta_median": float(g["delta_dice"].median()),
            "delta_q1": float(g["delta_dice"].quantile(0.25)),
            "delta_q3": float(g["delta_dice"].quantile(0.75)),
            "n_improved": int((g["outcome"] == "improved").sum()),
            "n_unchanged": int((g["outcome"] == "unchanged").sum()),
            "n_worsened": int((g["outcome"] == "worsened").sum()),
            "n_selected": int(len(sel)),
            "selected_delta_median": (float(sel["delta_dice"].median()) if len(sel) else None),
            "selected_n_improved": int((sel["outcome"] == "improved").sum()) if len(sel) else 0,
            "selected_n_worsened": int((sel["outcome"] == "worsened").sum()) if len(sel) else 0,
        }

    # ---- domain shift ----------------------------------------------------- #
    ref = json.loads(PHASE21.read_text(encoding="utf-8"))["global_medfilm"]
    per_dom = ref["per_domain_dice"]
    ds_rows = []
    for key, name, analogue in COHORTS:
        g = pc[(pc["cohort_key"] == key) & (pc["arm"] == "global")]
        b = pc[(pc["cohort_key"] == key) & (pc["arm"] == "barr")]
        internal = float(per_dom[analogue])
        ds_rows.append({
            "cohort": name, "domain_analogue": analogue, "n": int(len(g)),
            "internal_val808_dice": internal,
            "external_global_dice": float(g["Dice"].mean()),
            "delta_vs_internal_pp": float((g["Dice"].mean() - internal) * 100),
            "external_barr_dice": float(b["Dice"].mean()),
            "gt_area_fraction_median": float((g["gt_pixels"] / (512 * 512)).median()),
            "pred_area_fraction_median": float((g["pred_pixels"] / (512 * 512)).median()),
            "gt_empty_cases": int(g["gt_empty"].sum()),
            "pred_empty_cases": int(g["pred_empty"].sum()),
            "dice_q1": float(g["Dice"].quantile(0.25)),
            "dice_q3": float(g["Dice"].quantile(0.75)),
            "note": ("internal reference is the frozen Phase 21 VAL808 per-domain value "
                     "for the same task id; it is NOT this population and is quoted only "
                     "as a shift anchor"),
        })
    ds = pd.DataFrame(ds_rows)
    ds.to_csv(TAB / "c1_external_stress_domain_shift.csv", index=False)

    # ---- audit json ------------------------------------------------------- #
    out = {
        "artifact": "c1_external_stress_metrics",
        "p_values_computed": 0,
        "surface_units": "pixels",
        "surface_units_note": (
            "No external cohort ships physical pixel spacing. Millimetre surface metrics "
            "are not computed and must not be quoted. Cross-cohort surface-metric "
            "comparison is prohibited."),
        "aggregation_primary": "macro over cases (equal case weight)",
        "aggregation_secondary": "pooled pixel-level (labelled secondary)",
        "cross_cohort_pooling": False,
        "n_cases": int(len(pc) // 2),
        "per_cohort_n": {k: int(v["n"]) for k, v in co.items()},
        "paired_global_vs_barr": paired,
        "domain_shift": ds_rows,
        "barr_states": {
            k: pd.read_csv(CACHE / k / "barr_states.csv")["state"].value_counts().to_dict()
            for k, _, _ in COHORTS},
        "files": {},
    }
    for f in sorted(TAB.glob("c1_external_stress_*.csv")):
        h = hashlib.sha256()
        h.update(f.read_bytes())
        out["files"][f.name] = h.hexdigest()
    (AUD / "metrics_summary.json").write_text(json.dumps(out, indent=2, default=str) + "\n",
                                             encoding="utf-8")

    # ---- console summary -------------------------------------------------- #
    print("=== macro Dice (mean over cases) ===")
    for key, name, _ in COHORTS:
        for arm in ("global", "barr"):
            s = summ[(summ.cohort_key == key) & (summ.arm == arm) & (summ.metric == "Dice")].iloc[0]
            print(f"  {name:22s} {arm:7s} Dice={s['mean']:.4f} "
                  f"[{s['ci_low']:.4f},{s['ci_high']:.4f}] n={int(s['n_total'])} "
                  f"def={int(s['n_defined'])}")
    print("\n=== domain shift (external - internal, pp) ===")
    for r in ds_rows:
        print(f"  {r['cohort']:22s} internal={r['internal_val808_dice']:.4f} "
              f"external={r['external_global_dice']:.4f} "
              f"delta={r['delta_vs_internal_pp']:+.2f}pp")
    print("\n=== paired BARR - Global ===")
    for k, v in paired.items():
        print(f"  {k:8s} median={v['delta_median']:+.4f} improved={v['n_improved']} "
              f"unchanged={v['n_unchanged']} worsened={v['n_worsened']}")
    print("\nWROTE", len(out["files"]), "tables")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
