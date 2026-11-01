"""C3 baseline reporter: per-architecture records from verified historical artifacts.

No training is run. All rows are PROTOCOL_INCOMPARABLE historical single-run results;
the protocol-matched section is intentionally empty. No leaderboard, rank or
superiority statement is emitted.

  python scripts/analysis/c3_baseline_reporter.py [--out-dir DIR]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
T = ROOT / "reports" / "tables"
OUT = T / "c3_baselines"
DOMAINS = ("ISIC", "BUSI", "KVASIR", "KUB")


def rd(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def rel(p):
    try:
        return str(Path(p).resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(p)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def build():
    p6, pc, p5 = (T / "phase21_six_model_comparison.csv", T / "phase21_six_model_compute.csv",
                  T / "phase20b_five_model_comparison_final.csv")
    six = {r["model_key"]: r for r in rd(p6)}
    comp = {r["model_key"]: r for r in rd(pc)}
    five = {r["model_key"]: r for r in rd(p5)}
    records, problems = [], []
    for k, c in comp.items():
        s = six[k]
        f5 = five.get(k)
        params = int(c["params"])
        if int(c["params_expected"]) != params or c["params_match"] != "True":
            problems.append(f"{k}: parameter count mismatch")
        dice = {d: float(s[f"dice_{d}"]) for d in DOMAINS}
        macro = float(s["macro_domain_dice"])
        if abs(sum(dice.values()) / 4 - macro) > 1e-6:
            problems.append(f"{k}: macro Dice is not the mean of four domains")
        records.append({
            "model_key": k, "name": c["display_name"],
            "phase": "21" if k == "global_medfilm" else "20B", "configuration_source": "frozen historical model definitions (see source artifacts)",
            "dataset": "four-domain pooled development set (ISIC, BUSI, Kvasir-SEG, KUB), Manifest v2 historical",
            "split": "historical development validation (selection-consumed); no TEST evaluation",
            "training_recipe": "historical per-model recipe; not identical across architectures",
            "seed_count": 1, "checkpoint_selection": "best macro-domain validation Dice (phase20 selection rule)",
            "macro_domain_dice": macro, "macro_domain_iou": float(s["macro_domain_iou"]),
            "dice_by_domain": dice, "macro_dice_ci_95_descriptive": [float(s["macro_domain_dice_ci_low"]), float(s["macro_domain_dice_ci_high"])],
            "pooled_dice_descriptive": float(s["pooled_dice_descriptive"]),
            "params": params, "analytical_gmacs_lower_bound": float(c["gmacs"]),
            "analytical_method": c["method"], "analytical_input": c["input_shape"],
            "measured_latency_ms": None, "measured_latency_note": "none recorded for baselines in the verified artifacts",
            "five_model_table_row_present": f5 is not None,
            "evidence_class": "descriptive historical development result", "comparability": "PROTOCOL_INCOMPARABLE"})
    return records, problems, [p6, pc, p5]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=OUT)
    a = ap.parse_args(argv)
    records, problems, srcs = build()
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 4
    result = {"schema": "c3_baseline_report_v1", "protocol_matched": [],
              "protocol_matched_status": "NONE_AVAILABLE - C3 protocol-faithful comparison is NOT_ESTABLISHED",
              "exploratory_historical": sorted(records, key=lambda r: r["model_key"]),
              "leaderboard": None, "controlled_superiority_claim": False,
              "missing": ["protocol-matched baseline training under a shared recipe, seeds and split",
                          "multi-seed replicates", "measured baseline latency under a common harness"],
              "sources": {rel(p): sha(p) for p in srcs}, "training_run": False}
    out = a.out_dir
    out.mkdir(parents=True, exist_ok=True)
    (out / "c3_baseline_report.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    cols = ["model_key", "name", "phase", "seed_count", "macro_domain_dice", "macro_domain_iou"] + [f"dice_{d}" for d in DOMAINS] + \
           ["params", "analytical_gmacs_lower_bound", "measured_latency_ms", "comparability", "evidence_class"]
    with open(out / "c3_exploratory_historical.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cols)
        for r in result["exploratory_historical"]:
            w.writerow([r.get(c, r["dice_by_domain"].get(c[5:])) if c in r else r["dice_by_domain"][c[5:]] for c in cols])
    print("C3 report OK;", len(records), "historical records, 0 protocol-matched; out:", rel(out))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except FileNotFoundError as exc:
        print(f"MISSING_REQUIRED_INPUT: {exc.filename or exc}", file=sys.stderr)
        raise SystemExit(4)
