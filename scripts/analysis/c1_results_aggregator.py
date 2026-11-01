"""Deterministic C1 results aggregator.

Thin wrapper over the committed frozen-protocol pipeline
(src.research.evaluation_r3.c1_artifact_pipeline, PCG64 seed 20261027, 10,000
domain-stratified paired cluster-percentile bootstrap, KUB patient clusters).
When the six real runs do not exist the output is NOT_ESTABLISHED and
incomplete; no value is ever substituted.

Usage:
  python scripts/analysis/c1_results_aggregator.py [--experiment-root DIR] [--out-dir DIR]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.research.evaluation_r3 import c1_artifact_pipeline as P  # noqa: E402

DEFAULT_ROOT = ROOT / "experiments" / "c1_film_attribution_v1"
DEFAULT_OUT = ROOT / "reports" / "tables" / "c1_results"
METHOD = {
    "primary": "seed_average_of_paired_equal_domain_macro_Dice_T_minus_C_on_selected_VAL",
    "population": "VAL808 (selection-consumed)",
    "bootstrap_draws": P.FROZEN_C1_N_BOOT,
    "rng": "numpy PCG64",
    "rng_seed": P.FROZEN_C1_RNG_SEED,
    "confidence": P.FROZEN_C1_CONFIDENCE,
    "ci_method": "domain_stratified_paired_cluster_percentile",
    "domain_weights": "equal (1/4 each)",
    "clusters": "KUB by patient_id; ISIC/BUSI/Kvasir by image (no patient IDs)",
    "inference": "conditional on three fixed seeds; descriptive; no p-value",
    "unit": "Dice proportion (0-1); difference in proportion units",
}


def missing_runs(root: Path):
    return [f"seed{s}/{a}" for s in P.EXPECTED_SEEDS for a in P.EXPECTED_ARMS
            if not (root / f"seed{s}" / a / "lifecycle.json").exists()]


def aggregate(root: Path, allow_synthetic: bool = False, n_boot=None, roster=None):
    missing = missing_runs(root)
    base = {"experiment": "C1_FILM_ATTRIBUTION_V1", "method": METHOD}
    if missing:
        return {**base, "status": "NOT_ESTABLISHED", "complete": False,
                "runs_completed": 6 - len(missing), "runs_required": 6,
                "missing_runs": missing,
                "note": "No C1 estimate, interval or direction is reported."}
    if roster is None and not allow_synthetic:
        roster = P.load_val808_patient_roster()
    pipe = P.C1ArtifactAnalysisPipeline(root, roster)
    res = pipe.execute_campaign_analysis(allow_synthetic=allow_synthetic, n_boot=n_boot)
    b = res["case_level_bootstrap_result"]
    return {**base,
            "status": res["status"], "complete": not allow_synthetic,
            "synthetic": bool(allow_synthetic),
            "estimate": b["estimate"], "ci": b["ci"], "per_seed": b["per_seed"],
            "per_domain_seed_effects": b["per_domain_seed_effects"],
            "cluster_counts": b["cluster_counts"], "n_paired_rows": b["n_paired_rows"],
            "seed_descriptive": b["seed_descriptive"], "resamples": b["resamples"],
            "interpretation": ("CI above zero: positive; below zero: negative; "
                               "crossing zero: inconclusive; no equivalence claim")}


def write_outputs(result: dict, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "c1_aggregate.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    if "per_seed" not in result:
        return
    with open(out / "c1_seed_level.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["seed", "delta_equal_domain_macro_dice_T_minus_C"])
        for s, v in result["per_seed"].items():
            w.writerow([s, v])
    with open(out / "c1_domain_level.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["domain", "seed", "delta_dice_T_minus_C", "n_clusters"])
        for d, m in result["per_domain_seed_effects"].items():
            for s, v in m.items():
                w.writerow([d, s, v, result["cluster_counts"][d]])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiment-root", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    a = ap.parse_args(argv)
    r = aggregate(a.experiment_root)
    write_outputs(r, a.out_dir)
    print(r["status"], "complete=", r["complete"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
