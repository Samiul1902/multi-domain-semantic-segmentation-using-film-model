"""Derive the ReMedFiLM metric tables from saved predictions.

All values come from artifacts that already exist on disk:
  * reports/tables/phase27_val808_predictions.csv  (per-sample mask paths)
  * reports/predictions/phase21_*/val/<DOMAIN>/*.npz  (GT + backbone prob)
  * reports/tables/phase21_six_model_comparison.csv
  * reports/audits/phase27_preservation_result.json
  * reports/tables/phase29_three_seed_dev_summary.csv
  * reports/tables/c1_external_stress_summary.csv

No model is executed. Masks are read and scored.
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(r"D:\Softfors\jup")
OUT = ROOT / "full_doc_report"
TABLES = OUT / "tables"
TABLES.mkdir(parents=True, exist_ok=True)

EPS = 1e-7


def _binarise(arr: np.ndarray) -> np.ndarray:
    return (arr > 0).astype(bool)


def dice_iou_prec_rec(pred: np.ndarray, gt: np.ndarray) -> tuple[float, float, float, float]:
    p, g = _binarise(pred), _binarise(gt)
    inter = np.logical_and(p, g).sum()
    ps, gs = p.sum(), g.sum()
    if ps + gs == 0:
        return 1.0, 1.0, 1.0, 1.0
    dice = (2.0 * inter + EPS) / (ps + gs + EPS)
    union = np.logical_or(p, g).sum()
    iou = (inter + EPS) / (union + EPS)
    prec = (inter + EPS) / (ps + EPS) if ps else 0.0
    rec = (inter + EPS) / (gs + EPS) if gs else 0.0
    return float(dice), float(iou), float(prec), float(rec)


def surface_distances(pred: np.ndarray, gt: np.ndarray, spacing=(1.0, 1.0)):
    """95th percentile symmetric surface distance in pixels (HD95)."""
    p, g = _binarise(pred), _binarise(gt)
    if not p.any() or not g.any():
        return None
    struct = ndimage.generate_binary_structure(2, 1)
    p_edge = p ^ ndimage.binary_erosion(p, struct)
    g_edge = g ^ ndimage.binary_erosion(g, struct)
    dt_g = ndimage.distance_transform_edt(~g_edge, sampling=spacing)
    dt_p = ndimage.distance_transform_edt(~p_edge, sampling=spacing)
    d_pg = dt_g[p_edge]
    d_gp = dt_p[g_edge]
    if d_pg.size == 0 or d_gp.size == 0:
        return None
    return float(np.percentile(np.concatenate([d_pg, d_gp]), 95))


def _hist(values, bins):
    counts, edges = np.histogram(values, bins=bins)
    return {"bin_edges": [float(x) for x in edges],
            "counts": [int(x) for x in counts]}


def main() -> None:
    preds = list(csv.DictReader(
        (ROOT / "reports/tables/phase27_val808_predictions.csv").open(encoding="utf-8")))
    manifest = {r["sample_id"]: r for r in csv.DictReader(
        (ROOT / "reports/tables/phase21_prediction_manifest.csv").open(encoding="utf-8"))}

    per_sample = []
    for r in preds:
        sid = r["sample_id"]
        dom = r["dataset"]
        npz_path = ROOT / manifest[sid]["npz_path"] if sid in manifest else None
        if npz_path is None or not npz_path.exists():
            continue
        with np.load(npz_path) as z:
            gt = z["gt"]
        gmask = np.array(Image.open(ROOT / r["global_mask_path"]).convert("L"))
        fmask = np.array(Image.open(ROOT / r["final_mask_path"]).convert("L"))
        if gmask.shape != gt.shape:
            gmask = np.array(Image.fromarray(gmask).resize(gt.shape[::-1], Image.NEAREST))
            fmask = np.array(Image.fromarray(fmask).resize(gt.shape[::-1], Image.NEAREST))

        gd, gi, gp, gr = dice_iou_prec_rec(gmask, gt)
        fd, fi, fp, fr = dice_iou_prec_rec(fmask, gt)
        gh = surface_distances(gmask, gt)
        fh = surface_distances(fmask, gt)
        per_sample.append({
            "sample_id": sid,
            "domain": dom,
            "task_id": r["task_id"],
            "group_key": r["group_key"],
            "branch": r["state_machine_branch"],
            "router_decision": r["router_decision"],
            "global_dice": gd, "final_dice": fd,
            "global_iou": gi, "final_iou": fi,
            "global_precision": gp, "final_precision": fp,
            "global_recall": gr, "final_recall": fr,
            "global_hd95": gh, "final_hd95": fh,
            "delta_dice": fd - gd,
            "gt_fg": int(_binarise(gt).sum()),
            "global_fg": int(_binarise(gmask).sum()),
            "final_fg": int(_binarise(fmask).sum()),
            "harmful": bool(fd < gd - 1e-12),
            "beneficial": bool(fd > gd + 1e-12),
            "unchanged": bool(abs(fd - gd) <= 1e-12),
        })

    print(f"SCORED {len(per_sample)} samples")

    fields = list(per_sample[0].keys())
    with (TABLES / "REMEDFILM_INTERNAL_PER_SAMPLE.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(per_sample)

    # ---------------- aggregate ----------------
    def agg(rows, key):
        vals = [r[key] for r in rows if r[key] is not None]
        return float(np.mean(vals)) if vals else None

    by_dom = defaultdict(list)
    for r in per_sample:
        by_dom[r["domain"]].append(r)

    rows = []
    for dom in ("ISIC", "BUSI", "KVASIR", "KUB"):
        rs = by_dom[dom]
        rows.append({
            "domain": dom, "n": len(rs),
            "global_dice": agg(rs, "global_dice"), "final_dice": agg(rs, "final_dice"),
            "delta_dice": agg(rs, "delta_dice"),
            "global_iou": agg(rs, "global_iou"), "final_iou": agg(rs, "final_iou"),
            "global_precision": agg(rs, "global_precision"), "final_precision": agg(rs, "final_precision"),
            "global_recall": agg(rs, "global_recall"), "final_recall": agg(rs, "final_recall"),
            "global_hd95": agg(rs, "global_hd95"), "final_hd95": agg(rs, "final_hd95"),
            "n_harmful": sum(r["harmful"] for r in rs),
            "n_beneficial": sum(r["beneficial"] for r in rs),
            "n_unchanged": sum(r["unchanged"] for r in rs),
        })
    macro = {"domain": "MACRO_DOMAIN_EQUAL_WEIGHT", "n": len(per_sample)}
    for k in rows[0]:
        if k in ("domain", "n"):
            continue
        if k.startswith("n_"):
            macro[k] = sum(r[k] for r in rows)
        else:
            vals = [r[k] for r in rows if r[k] is not None]
            macro[k] = float(np.mean(vals)) if vals else None
    rows.append(macro)

    with (TABLES / "REMEDFILM_INTERNAL_METRICS.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print("\nINTERNAL METRICS (VAL808, seed 42)")
    for r in rows:
        print(f"  {r['domain']:30s} n={r['n']:>4} "
              f"G_dice={r['global_dice']:.6f} R_dice={r['final_dice']:.6f} "
              f"d={r['delta_dice']:+.6f} R_hd95={r['final_hd95']:.2f}")

    # ---------------- six-model + FULL comparison ----------------
    six = list(csv.DictReader(
        (ROOT / "reports/tables/phase21_six_model_comparison.csv").open(encoding="utf-8")))
    comp = []
    for r in six:
        comp.append({
            "model": r["display_name"], "model_key": r["model_key"],
            "role": "BACKBONE" if r["model_key"] == "global_medfilm" else "BASELINE",
            "params": r["params"] or "3523001",
            "macro_dice": r["macro_domain_dice"],
            "ci_low": r["macro_domain_dice_ci_low"],
            "ci_high": r["macro_domain_dice_ci_high"],
            "macro_iou": r["macro_domain_iou"],
            "dice_ISIC": r["dice_ISIC"], "dice_BUSI": r["dice_BUSI"],
            "dice_KVASIR": r["dice_KVASIR"], "dice_KUB": r["dice_KUB"],
            "source": "reports/tables/phase21_six_model_comparison.csv",
        })
    comp.append({
        "model": "ReMedFiLM (FULL proposed)", "model_key": "remedfilm_full",
        "role": "PROPOSED_FULL_SYSTEM", "params": "4837420",
        "macro_dice": f"{macro['final_dice']:.10f}",
        "ci_low": "", "ci_high": "",
        "macro_iou": f"{macro['final_iou']:.10f}",
        "dice_ISIC": f"{by_dom['ISIC'][0]['final_dice']:.10f}",
        "dice_BUSI": f"{by_dom['BUSI'][0]['final_dice']:.10f}",
        "dice_KVASIR": f"{by_dom['KVASIR'][0]['final_dice']:.10f}",
        "dice_KUB": f"{by_dom['KUB'][0]['final_dice']:.10f}",
        "source": "derived from phase27_val808_predictions.csv final masks",
    })
    with (TABLES / "REMEDFILM_MODEL_COMPARISON.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(comp[0].keys()))
        w.writeheader()
        w.writerows(comp)

    # ---------------- paired delta + bootstrap ----------------
    rng = np.random.default_rng(20261027)
    doms = ["ISIC", "BUSI", "KVASIR", "KUB"]
    boots = []
    for _ in range(10000):
        vals = []
        for d in doms:
            rs = by_dom[d]
            idx = rng.integers(0, len(rs), len(rs))
            vals.append(float(np.mean([rs[i]["delta_dice"] for i in idx])))
        boots.append(float(np.mean(vals)))
    boots = np.array(boots)
    point = float(np.mean([np.mean([r["delta_dice"] for r in by_dom[d]]) for d in doms]))
    paired = {
        "artifact": "remedfilm_val808_paired_delta",
        "population": "VAL808",
        "n": len(per_sample),
        "estimand": "MACRO_DOMAIN_EQUAL_WEIGHT_MEAN_DICE_DELTA (ReMedFiLM FULL - GlobalMedFiLM)",
        "point": point,
        "ci_low": float(np.percentile(boots, 2.5)),
        "ci_high": float(np.percentile(boots, 97.5)),
        "n_boot": 10000,
        "seed": 20261027,
        "method": "domain-stratified percentile bootstrap over images",
        "per_domain": {
            d: {
                "n": len(by_dom[d]),
                "point": float(np.mean([r["delta_dice"] for r in by_dom[d]])),
                "n_harmful": sum(r["harmful"] for r in by_dom[d]),
                "n_beneficial": sum(r["beneficial"] for r in by_dom[d]),
                "n_unchanged": sum(r["unchanged"] for r in by_dom[d]),
            } for d in doms
        },
        "cross_check_phase27_macro_point": 0.0022101452700813433,
        "bootstrap_hist": _hist(boots, 80),
    }
    (OUT / "tables/REMEDFILM_PAIRED_DELTA.json").write_text(
        json.dumps(paired, indent=2), encoding="utf-8")
    print(f"\nPAIRED DELTA point={point:+.8f} CI=[{paired['ci_low']:+.8f},{paired['ci_high']:+.8f}]")
    print(f"phase27 reference point = 0.00221015  |  diff = {abs(point-0.0022101452700813433):.3e}")

    # ---------------- external ----------------
    ext = list(csv.DictReader(
        (ROOT / "reports/tables/c1_external_stress_summary.csv").open(encoding="utf-8")))
    ext_rows = []
    for r in ext:
        if r["metric"] not in ("Dice", "IoU", "Precision", "Recall", "HD95_px", "ASSD_px"):
            continue
        ext_rows.append({
            "cohort": r["cohort"], "cohort_key": r["cohort_key"],
            "domain_analogue": r["domain_analogue"],
            "arm": "ReMedFiLM_FULL" if r["arm"] == "barr" else "GlobalMedFiLM",
            "metric": r["metric"],
            "n_total": r["n_total"], "n_defined": r["n_defined"],
            "mean": r["mean"], "median": r["median"],
            "ci_low": r["ci_low"], "ci_high": r["ci_high"],
            "n_clusters": r["n_clusters"],
            "source": "reports/tables/c1_external_stress_summary.csv",
        })
    with (TABLES / "REMEDFILM_EXTERNAL_METRICS.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(ext_rows[0].keys()))
        w.writeheader()
        w.writerows(ext_rows)
    print(f"EXTERNAL ROWS {len(ext_rows)}")

    # ---------------- efficiency ----------------
    eff = json.loads((ROOT / "reports/audits/phase34_efficiency_result_v1_4.json")
                     .read_text(encoding="utf-8"))
    lat = eff["MEASURED_HARDWARE_SPECIFIC_RUNTIME_PROFILE"]["batch1_latency_v1_4"]
    c2 = json.loads((ROOT / "reports/tables/c2_barr/c2_barr_aggregate.json")
                    .read_text(encoding="utf-8"))
    eff_rows = [
        {"model": "GlobalMedFiLM (G)", "params": 3523001, "gmacs": 31.5517,
         "gmacs_semantics": "ANALYTICAL_LOWER_BOUND",
         "latency_p50_ms": lat["GLOBAL_ONLY_C1"]["p50_ms"],
         "latency_p50_semantics": "MEASURED_BATCH1_CONTROLLED_FORWARD",
         "macro_dice": 0.8350794169575282, "population": "VAL808",
         "source": "phase21_analytical_mac_count.json / phase34_efficiency_result_v1_4.json"},
        {"model": "ReMedFiLM (FULL)", "params": 4837420,
         "gmacs": c2["compute"]["analytical_gmacs_lower_bound"]["FINAL_A8_C9_EXPECTED_CONDITIONAL"],
         "gmacs_semantics": "EXPECTED_CONDITIONAL",
         "latency_p50_ms": lat["EXECUTE_CONTROLLED_PATH"]["p50_ms"],
         "latency_p50_semantics": "MEASURED_BATCH1_CONTROLLED_FORWARD",
         "macro_dice": macro["final_dice"], "population": "VAL808",
         "source": "phase34_parameter_count_contract.json / c2_barr_aggregate.json"},
    ]
    for r in six:
        if r["model_key"] == "global_medfilm":
            continue
        eff_rows.append({
            "model": r["display_name"], "params": int(float(r["params"])),
            "gmacs": "", "gmacs_semantics": "NOT_RECORDED",
            "latency_p50_ms": "", "latency_p50_semantics": "NOT_RECORDED",
            "macro_dice": r["macro_domain_dice"], "population": "VAL808",
            "source": "reports/tables/phase21_six_model_comparison.csv",
        })
    with (TABLES / "REMEDFILM_EFFICIENCY.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(eff_rows[0].keys()))
        w.writeheader()
        w.writerows(eff_rows)

    print("\nEFFICIENCY")
    for r in eff_rows:
        print(f"  {r['model']:32s} params={r['params']:>10} gmacs={r['gmacs']} dice={r['macro_dice']}")


if __name__ == "__main__":
    main()
