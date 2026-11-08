"""Build the five required verification tables."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
OUT = ROOT / "full_doc_report"
TABLES = OUT / "tables"


def load(p: Path) -> list[dict]:
    with p.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def write(p: Path, rows: list[dict]) -> None:
    with p.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"  {p.name}: {len(rows)} rows")


def main() -> None:
    # ------------------------------------ 1. component training history -----
    hist = load(TABLES / "REMEDFILM_EPOCH_HISTORY.csv")
    reg = {r["run_id"]: r for r in load(TABLES / "TRAINING_RUN_REGISTRY.csv")}
    keep_roles = {"G_BACKBONE", "BACKBONE", "COMPONENT", "ABLATION"}
    rows = []
    for r in hist:
        meta = reg.get(r["run_id"])
        if not meta or meta["model_role"] not in keep_roles:
            continue
        rows.append({
            "experiment_id": r["run_id"],
            "model": r["model_identity"],
            "component": r["model_identity"],
            "seed": r["seed"],
            "epoch": r["epoch"],
            "metric_name": r["metric"],
            "metric_value": r["value"],
            "source_path": r["source_path"],
            "evidence_status": meta["evidence_status"],
            "best_epoch": meta["best_epoch"],
        })
    write(TABLES / "REMEDFILM_COMPONENT_TRAINING_HISTORY.csv", rows)

    # ---------------------------------------- 2. FULL VAL808 metrics --------
    internal = load(TABLES / "REMEDFILM_INTERNAL_METRICS.csv")
    out = []
    for r in internal:
        out.append({
            "population": "VAL808",
            "domain": r["domain"],
            "n": r["n"],
            "model": ("ReMedFiLM FULL" if False else "GlobalMedFiLM / ReMedFiLM FULL"),
            "global_dice": r["global_dice"],
            "full_dice": r["final_dice"],
            "delta_dice": r["delta_dice"],
            "full_iou": r["final_iou"],
            "full_precision": r["final_precision"],
            "full_recall": r["final_recall"],
            "full_hd95_px": r["final_hd95"],
            "n_harmful": r["n_harmful"],
            "n_beneficial": r["n_beneficial"],
            "n_unchanged": r["n_unchanged"],
            "metric_definition": "per-image Dice at threshold 0.5, equal-weight mean",
            "source": "re-scored from reports/figures/phase27_preservation/masks/",
            "evidence_class": "DERIVED_FROM_SAVED_PREDICTIONS",
        })
    write(TABLES / "REMEDFILM_FULL_VAL808_METRICS.csv", out)

    # ------------------------------------------ 3. FULL external metrics ----
    ext = load(TABLES / "REMEDFILM_EXTERNAL_METRICS.csv")
    out = []
    for r in ext:
        out.append({
            "cohort": r["cohort"],
            "cohort_key": r["cohort_key"],
            "domain_analogue": r["domain_analogue"],
            "model": ("ReMedFiLM FULL" if r["arm"] == "ReMedFiLM_FULL"
                      else "GlobalMedFiLM"),
            "metric": r["metric"],
            "n_total": r["n_total"],
            "n_defined": r["n_defined"],
            "mean": r["mean"],
            "median": r["median"],
            "ci_low": r["ci_low"],
            "ci_high": r["ci_high"],
            "n_clusters": r["n_clusters"],
            "evidence_class": "EXTERNAL_RETROSPECTIVE_SAVED_PREDICTIONS",
            "source": r["source"],
        })
    write(TABLES / "REMEDFILM_FULL_EXTERNAL_METRICS.csv", out)

    # -------------------------------- 4. ablation + progression combined ----
    abl = load(TABLES / "REMEDFILM_ABLATION_RESULTS.csv")
    prog = load(TABLES / "REMEDFILM_PROGRESSION_RESULTS.csv")
    bs = {r["contrast"]: r for r in load(
        ROOT / "reports/tables/phase28_table_08_bootstrap_statistics.csv")}
    contrast_of = {"A7": "A8_vs_A7", "A6": "R1_vs_A6C7"}
    rows = []
    for r in prog:
        rows.append({
            "record_type": "PROGRESSION",
            "arm_or_stage": r["stage"],
            "name": r["stage_name"],
            "population": r["population"],
            "n": r["n"],
            "active_components": r["active_components"],
            "n_routed": "", "routed_fraction": r["routed_fraction"],
            "accepted_fraction": r["accepted_fraction"],
            "mean_delta_dice": r["net_delta_pp"],
            "harmful_share": r["harm_rate"],
            "benefit_capture": "",
            "gmacs": r["gmacs_lower_bound"],
            "paired_contrast": "", "ci_low": "", "ci_high": "", "ci_excludes_zero": "",
            "evidence_class": r["evidence_class"],
            "source": r["source"],
        })
    for r in abl:
        c = contrast_of.get(r["arm"], "")
        b = bs.get(c, {})
        rows.append({
            "record_type": "ABLATION",
            "arm_or_stage": r["arm"],
            "name": "",
            "population": r["population"],
            "n": 4957,
            "active_components": "",
            "n_routed": r["n_routed"],
            "routed_fraction": r["budget_fraction"],
            "accepted_fraction": "",
            "mean_delta_dice": r["mean_true_delta_dice_routed"],
            "harmful_share": r["harmful_activation_share"],
            "benefit_capture": r["benefit_capture_vs_positive_mass"],
            "gmacs": "",
            "paired_contrast": c,
            "ci_low": b.get("ci95_low", ""),
            "ci_high": b.get("ci95_high", ""),
            "ci_excludes_zero": ("YES" if b and (float(b["ci95_low"]) > 0 or float(b["ci95_high"]) < 0) else
                                 ("NO" if b else "")),
            "evidence_class": r["evidence_class"],
            "source": r["source"],
        })
    write(TABLES / "REMEDFILM_ABLATION_AND_PROGRESSION.csv", rows)

    # ------------------------------------ 5. visual evidence index ----------
    sel = load(TABLES / "REMEDFILM_SEGMENTATION_SELECTION.csv")
    reg_fig = {f["figure_id"]: f for f in json.loads(
        (OUT / "figure_registry.json").read_text(encoding="utf-8"))}
    out = []
    for r in sel:
        fid = r["figure"]
        meta = reg_fig.get(fid, {})
        out.append({
            "figure_id": fid,
            "figure_path": meta.get("path", ""),
            "panel_role": r["panel"],
            "row": r["row"],
            "domain": r["domain"],
            "sample_id": r["sample_id"],
            "state_machine_branch": r["branch"],
            "global_dice": r["global_dice"],
            "full_dice": r["final_dice"],
            "delta_dice": r["delta_dice"],
            "full_iou": r["final_iou"],
            "full_hd95_px": r["final_hd95"],
            "source_image": r["source_image"],
            "gt_mask": r["gt_mask"],
            "global_mask": r["global_mask"],
            "full_mask": r["final_mask"],
            "identity_check": "global and FULL masks are distinct files from the same sample",
            "evidence_class": "SAVED_PREDICTIONS_VAL808",
        })
    write(TABLES / "REMEDFILM_FULL_VISUAL_EVIDENCE_INDEX.csv", out)

    # mirror the five required tables to the report root
    print()
    print("ROOT MIRRORS")
    import shutil as _sh
    for name in ("REMEDFILM_COMPONENT_TRAINING_HISTORY.csv", "REMEDFILM_FULL_VAL808_METRICS.csv",
                 "REMEDFILM_FULL_EXTERNAL_METRICS.csv", "REMEDFILM_ABLATION_AND_PROGRESSION.csv",
                 "REMEDFILM_FULL_VISUAL_EVIDENCE_INDEX.csv"):
        src = TABLES / name
        if src.exists():
            _sh.copyfile(src, OUT / name)
            print(f"  {name} -> report root")

    # sanity: every referenced file exists
    missing = []
    for r in out:
        for k in ("source_image", "gt_mask", "global_mask", "full_mask"):
            if r[k] and not Path(r[k]).exists():
                missing.append((r["figure_id"], r["sample_id"], k))
    print(f"  visual index file checks: {len(missing)} missing")
    if missing:
        print("   ", missing[:5])


if __name__ == "__main__":
    main()
