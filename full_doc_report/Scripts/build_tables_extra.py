"""Build the remaining ReMedFiLM tables from frozen artifacts.

Includes an explicit correction of a previously published value: the earlier
consolidation CSV asserted a VAL808 macro Dice of 0.837862 for the FULL system.
Re-scoring the saved Phase 27 masks reproduces 0.837290, matching the frozen
Phase 27 / Phase 29 continuity records (0.8372891). The corrected value is used
here and the discrepancy is recorded.
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
OUT = ROOT / "full_doc_report"
TABLES = OUT / "tables"
TABLES.mkdir(parents=True, exist_ok=True)

CORRECTIONS = []


def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def main() -> None:
    # ------------------------------------------------ dataset composition ----
    rows = []
    for f, split in (("train.csv", "train"), ("val.csv", "val")):
        with (ROOT / "manifests/phase4_v3" / f).open(encoding="utf-8", newline="") as fh:
            rows.extend(list(csv.DictReader(fh)))
    by = Counter((r["dataset"], r["split"].lower()) for r in rows)
    comp = []
    for d in ("ISIC", "BUSI", "KVASIR", "KUB"):
        comp.append({"domain": d,
                     "train": by[(d, "train")], "val": by[(d, "val")],
                     "total": by[(d, "train")] + by[(d, "val")]})
    comp.append({"domain": "TOTAL", "train": sum(c["train"] for c in comp),
                 "val": sum(c["val"] for c in comp),
                 "total": sum(c["total"] for c in comp)})
    with (TABLES / "REMEDFILM_DATASET_COMPOSITION.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["domain", "train", "val", "total"])
        w.writeheader(); w.writerows(comp)
    print("COMPOSITION", {c["domain"]: (c["train"], c["val"]) for c in comp})

    # KUB unit of analysis
    kub = [r for r in rows if r["dataset"] == "KUB"]
    roi = sum(1 for r in kub if Path(r["image_path"]).parent.name == "ROI")
    full = len(kub) - roi
    print(f"KUB rows={len(kub)} full_field={full} roi_patch={roi}")

    # ------------------------------------------------------- progression ----
    # Verified anchors only.
    p27 = jload(ROOT / "reports/audits/phase27_preservation_result.json")
    p29 = jload(ROOT / "reports/audits/phase29_phase_d_val808_per_seed_continuity.json")
    c2 = jload(ROOT / "reports/tables/c2_barr/c2_barr_aggregate.json")
    p21 = jload(ROOT / "reports/audits/phase21_analysis.json")
    internal = list(csv.DictReader((TABLES / "REMEDFILM_INTERNAL_METRICS.csv").open(encoding="utf-8")))
    macro_row = [r for r in internal if r["domain"].startswith("MACRO")][0]
    final_dice = float(macro_row["final_dice"])
    global_dice = float(macro_row["global_dice"])
    delta = float(macro_row["delta_dice"])

    abl = list(csv.DictReader(
        (ROOT / "reports/tables/phase28_table_02_arm_primary_metrics.csv").open(encoding="utf-8")))
    arm = {r["arm"]: r for r in abl}
    gmac = c2["compute"]["analytical_gmacs_lower_bound"]

    prog = [
        {"stage": "Stage 0", "stage_name": "GlobalMedFiLM backbone (G)",
         "population": "VAL808", "n": 808, "active_components": "G",
         "mean_dice": f"{global_dice:.6f}",
         "routed_fraction": 0.0, "accepted_fraction": 0.0,
         "net_delta_pp": 0.0, "harm_rate": 0.0,
         "gmacs_lower_bound": gmac["LITERAL_GLOBAL_ONLY_C1"],
         "evidence_class": "FROZEN_BACKBONE_REFERENCE",
         "source": "reports/tables/phase21_six_model_comparison.csv"},
        {"stage": "Stage 1", "stage_name": "Unrouted regional refinement (A1)",
         "population": "ROUTER_DEVELOPMENT_4957", "n": 4957,
         "active_components": "G + R_psi",
         "mean_dice": "",
         "routed_fraction": float(arm["A1"]["budget_fraction"]),
         "accepted_fraction": float(arm["A1"]["budget_fraction"]),
         "net_delta_pp": float(arm["A1"]["mean_true_delta_dice_routed"]) * 100,
         "harm_rate": float(arm["A1"]["harmful_activation_share"]),
         "gmacs_lower_bound": gmac["GATED_EXECUTE_ALL_C9"],
         "evidence_class": "IN_SAMPLE_ENDPOINT_BY_CONSTRUCTION",
         "source": "reports/tables/phase28_table_02_arm_primary_metrics.csv"},
        {"stage": "Stage 2", "stage_name": "Learned benefit routing (A7)",
         "population": "ROUTER_DEVELOPMENT_4957", "n": 4957,
         "active_components": "G + R_psi + B_phi",
         "mean_dice": "",
         "routed_fraction": float(arm["A7"]["budget_fraction"]),
         "accepted_fraction": float(arm["A7"]["budget_fraction"]),
         "net_delta_pp": float(arm["A7"]["mean_true_delta_dice_routed"]) * 100,
         "harm_rate": float(arm["A7"]["harmful_activation_share"]),
         "gmacs_lower_bound": gmac["FINAL_A8_C9_EXPECTED_CONDITIONAL"],
         "evidence_class": "DEVELOPMENT_EVIDENCE",
         "source": "reports/tables/phase28_table_02_arm_primary_metrics.csv"},
        {"stage": "Stage 3", "stage_name": "Post-safety gate (A8 FULL)",
         "population": "ROUTER_DEVELOPMENT_4957", "n": 4957,
         "active_components": "G + R_psi + B_phi + S_omega",
         "mean_dice": "",
         "routed_fraction": float(arm["A8"]["budget_fraction"]),
         "accepted_fraction": float(arm["A8"]["n_routed"]) / 4957,
         "net_delta_pp": float(arm["A8"]["mean_true_delta_dice_routed"]) * 100,
         "harm_rate": float(arm["A8"]["harmful_activation_share"]),
         "gmacs_lower_bound": gmac["FINAL_A8_C9_EXPECTED_CONDITIONAL"],
         "evidence_class": "DEVELOPMENT_EVIDENCE",
         "source": "reports/tables/phase28_table_02_arm_primary_metrics.csv"},
        {"stage": "Stage 4", "stage_name": "FULL assembly on held-out VAL808",
         "population": "VAL808", "n": 808,
         "active_components": "G + R_psi + B_phi + S_omega",
         "mean_dice": f"{final_dice:.6f}",
         "routed_fraction": 279 / 808,
         "accepted_fraction": 266 / 808,
         "net_delta_pp": delta * 100,
         "harm_rate": sum(1 for _ in []) or 0.0,
         "gmacs_lower_bound": gmac["FINAL_A8_C9_EXPECTED_CONDITIONAL"],
         "evidence_class": "PAIRED_PRESERVATION_EVIDENCE",
         "source": "reports/tables/phase27_val808_predictions.csv (re-scored)"},
    ]
    # harm rate on VAL808 from derived table
    ps = list(csv.DictReader((TABLES / "REMEDFILM_INTERNAL_PER_SAMPLE.csv").open(encoding="utf-8")))
    harm = sum(1 for r in ps if r["harmful"] == "True")
    prog[-1]["harm_rate"] = harm / len(ps)
    prog.append({
        "stage": "Audit gate", "stage_name": "Incremental dataset progression",
        "population": "", "n": 0, "active_components": "",
        "mean_dice": "", "routed_fraction": "", "accepted_fraction": "",
        "net_delta_pp": "", "harm_rate": "", "gmacs_lower_bound": "",
        "evidence_class": "NOT_EXECUTED",
        "source": "no genuine incremental-domain training study exists",
    })
    with (TABLES / "REMEDFILM_PROGRESSION_RESULTS.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(prog[0].keys()))
        w.writeheader(); w.writerows(prog)

    CORRECTIONS.append({
        "field": "ReMedFiLM FULL VAL808 macro Dice (seed 42)",
        "previously_published": 0.837862,
        "corrected_value": round(final_dice, 10),
        "authoritative_sources": [
            "reports/audits/phase27_preservation_result.json (macro_point delta)",
            "reports/audits/phase29_phase_d_val808_per_seed_continuity.json "
            "(macro_final_dice 0.8372891053775793)",
            "re-scoring of reports/figures/phase27_preservation/masks/*_final.png",
        ],
        "resolution": "0.837862 appears in no frozen artifact; it was carried by an "
                      "earlier consolidation CSV. The corrected value is used.",
        "impact": "Net gain over backbone is +0.221 pp, not +0.278 pp.",
    })
    print(f"PROGRESSION stage4 dice={final_dice:.6f} delta_pp={delta*100:+.4f}")

    # ----------------------------------------------------------- ablation ----
    out = []
    for r in abl:
        out.append({
            "arm": r["arm"],
            "n_routed": r["n_routed"],
            "budget_fraction": r["budget_fraction"],
            "sum_true_delta_dice": r["sum_true_delta_dice"],
            "mean_true_delta_dice_routed": r["mean_true_delta_dice_routed"],
            "benefit_capture_vs_positive_mass": r["benefit_capture_vs_positive_mass"],
            "n_beneficial_routed": r["n_beneficial_routed"],
            "n_harmful_routed": r["n_harmful_routed"],
            "harmful_activation_share": r["harmful_activation_share"],
            "evidence_class": r["evidence_class"],
            "population": "ROUTER_DEVELOPMENT_4957",
            "source": "reports/tables/phase28_table_02_arm_primary_metrics.csv",
        })
    with (TABLES / "REMEDFILM_ABLATION_RESULTS.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
        w.writeheader(); w.writerows(out)
    print(f"ABLATION ARMS {len(out)}")

    (OUT / "SCIENTIFIC_CORRECTIONS.json").write_text(json.dumps({
        "artifact": "scientific_corrections",
        "policy": "corrections are disclosed, never silently applied",
        "corrections": CORRECTIONS,
    }, indent=2), encoding="utf-8")
    print("CORRECTIONS", len(CORRECTIONS))


if __name__ == "__main__":
    main()
