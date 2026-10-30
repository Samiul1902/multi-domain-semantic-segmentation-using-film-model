"""Per-class (domain) and per-subclass (KUB stone type) Dice breakdown on the frozen
development-validation split (VAL, n=808).

READ-ONLY ANALYSIS. No training, no inference, no TEST access, no ROUTER_HOLDOUT
access. This creates no new scientific endpoint: it re-aggregates the ALREADY FROZEN
per-sample Dice produced by Phase-29 (`phase29_phase_d_three_seed_val808_delta_dice.npz`)
at a finer granularity (domain -> category).

Source authority
----------------
`data_cache/phase29_phase_d_canonical/phase29_phase_d_three_seed_val808_delta_dice.npz`
  sample_ids (808,) | domains (808,) | global_dice (808,)
  seed42_final_dice | seed123_final_dice | seed3407_final_dice

Fidelity checks performed before any aggregation (fail-closed):
  * per-domain mean of `global_dice` must reproduce the frozen Phase-27 global points;
  * per-domain mean of `seed42_final_dice` must reproduce the frozen Phase-27 final points.
A mismatch aborts rather than emitting a plausible-but-wrong table.
"""
import csv
import hashlib
import json
import os
from pathlib import Path

import numpy as np

ROOT = Path(r"D:\Softfors\jup")
VAL_CSV = ROOT / "manifests" / "phase4_v3" / "val.csv"
NPZ = ROOT / "data_cache" / "phase29_phase_d_canonical" / "phase29_phase_d_three_seed_val808_delta_dice.npz"
OUT = ROOT / "reports" / "audits" / "val808_per_class_subclass_breakdown_v1_0.json"

ORACLE_FINAL = {"BUSI": 0.8589126018391846, "ISIC": 0.8980801299180301,
                "KUB": 0.771512927778779, "KVASIR": 0.8206507619743234}
ORACLE_GLOBAL = {"BUSI": 0.8588214375680574, "ISIC": 0.8971889499163059,
                 "KUB": 0.7640588414471431, "KVASIR": 0.8202466114984852}
TOL = 1e-9
SEEDS = [42, 123, 3407]
DOMAINS = ["ISIC", "BUSI", "KVASIR", "KUB"]


def mean(xs):
    return float(np.mean(xs)) if len(xs) else float("nan")


def main():
    z = np.load(NPZ, allow_pickle=True)
    ids = [str(s) for s in z["sample_ids"]]
    doms = [str(s) for s in z["domains"]]
    g = z["global_dice"]
    finals = {s: z[f"seed{s}_final_dice"] for s in SEEDS}

    val = {r["sample_id"]: r for r in csv.DictReader(open(VAL_CSV, encoding="utf-8"))}
    cats = [val[i]["category"] for i in ids]

    # ---------- fidelity checks ----------
    checks = {}
    for d in DOMAINS:
        m = np.array([x == d for x in doms])
        checks[d] = {
            "n": int(m.sum()),
            "global_recomputed": mean(g[m]),
            "global_frozen": ORACLE_GLOBAL[d],
            "global_abs_diff": abs(mean(g[m]) - ORACLE_GLOBAL[d]),
            "seed42_final_recomputed": mean(finals[42][m]),
            "seed42_final_frozen": ORACLE_FINAL[d],
            "seed42_final_abs_diff": abs(mean(finals[42][m]) - ORACLE_FINAL[d]),
        }
        if checks[d]["global_abs_diff"] > TOL or checks[d]["seed42_final_abs_diff"] > TOL:
            raise RuntimeError(f"FIDELITY_FAIL {d}: {checks[d]}")

    # ---------- class (domain) ----------
    cls = {}
    for d in DOMAINS:
        m = np.array([x == d for x in doms])
        cls[d] = {"n": int(m.sum()), "dice_global": mean(g[m])}
        for s in SEEDS:
            cls[d][f"dice_seed{s}"] = mean(finals[s][m])
        cls[d]["dice_final_mean"] = mean([cls[d][f"dice_seed{s}"] for s in SEEDS])
        cls[d]["seed_spread"] = (max(cls[d][f"dice_seed{s}"] for s in SEEDS)
                                 - min(cls[d][f"dice_seed{s}"] for s in SEEDS))
        cls[d]["delta_mean"] = cls[d]["dice_final_mean"] - cls[d]["dice_global"]

    macro = {"n": len(ids)}
    for s in SEEDS:
        macro[f"dice_seed{s}"] = mean([cls[d][f"dice_seed{s}"] for d in DOMAINS])
    macro["dice_final_mean"] = mean([macro[f"dice_seed{s}"] for s in SEEDS])
    macro["seed_spread"] = max(macro[f"dice_seed{s}"] for s in SEEDS) - min(macro[f"dice_seed{s}"] for s in SEEDS)
    macro["dice_global"] = mean([cls[d]["dice_global"] for d in DOMAINS])
    macro["delta_mean"] = macro["dice_final_mean"] - macro["dice_global"]
    cls["MACRO"] = macro

    # ---------- subclass (KUB stone types) ----------
    sub = {}
    for d in DOMAINS:
        uniq = sorted({c for c, x in zip(cats, doms) if x == d})
        if uniq == ["NOT_AVAILABLE"]:
            sub[d] = {"subclass_available": False,
                      "note": "phase4_v3 manifest carries category=NOT_AVAILABLE for this domain"}
            continue
        sub[d] = {"subclass_available": True, "subclasses": {}}
        for c in uniq:
            m = np.array([(x == d and cc == c) for x, cc in zip(doms, cats)])
            e = {"n": int(m.sum()), "dice_global": mean(g[m])}
            for s in SEEDS:
                e[f"dice_seed{s}"] = mean(finals[s][m])
            e["dice_final_mean"] = mean([e[f"dice_seed{s}"] for s in SEEDS])
            e["seed_spread"] = (max(e[f"dice_seed{s}"] for s in SEEDS)
                                - min(e[f"dice_seed{s}"] for s in SEEDS))
            e["delta_mean"] = e["dice_final_mean"] - e["dice_global"]
            sub[d]["subclasses"][c] = e

    result = {
        "artifact": "val808_per_class_subclass_breakdown",
        "schema_version": "1.0",
        "classification": "DERIVED_READONLY_ANALYSIS__NOT_A_NEW_SCIENTIFIC_ENDPOINT",
        "method": "RA-MedFiLM-BARR",
        "split": "VAL_DEVELOPMENT_808",
        "test_accessed": False,
        "router_holdout_accessed": False,
        "training_performed": False,
        "inference_performed": False,
        "source": str(NPZ.relative_to(ROOT)),
        "source_sha256": hashlib.sha256(NPZ.read_bytes()).hexdigest(),
        "dice_semantics": "per-sample binary Dice at threshold 0.50; macro = unweighted mean over the 4 domains",
        "fidelity_checks": checks,
        "class": cls,
        "subclass": sub,
        "notes": [
            "seed42 == the canonical Phase-27 preservation execution; seeds 123/3407 == Phase-29 three-seed replication.",
            "Only KUB carries a subclass label in phase4_v3; ISIC/BUSI/KVASIR have category=NOT_AVAILABLE.",
            "delta = final policy (A8/C9) minus its own GlobalMedFiLM global reference; NOT a delta against external baselines.",
        ],
    }

    data = (json.dumps(result, indent=1) + "\n").encode("utf-8")
    fd = os.open(str(OUT), os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0))
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
    finally:
        pass
    assert OUT.stat().st_size == len(data)
    print("WROTE", OUT, OUT.stat().st_size, "B")
    print("SHA256", hashlib.sha256(OUT.read_bytes()).hexdigest())

    print("\n=== CLASS (domain), VAL808 ===")
    print(f"{'domain':8s} {'n':>4s} {'seed42':>8s} {'seed123':>8s} {'seed3407':>9s} "
          f"{'mean':>8s} {'spread':>7s} {'global':>8s} {'delta':>8s}")
    for d in DOMAINS + ["MACRO"]:
        v = cls[d]
        print(f"{d:8s} {v['n']:4d} {v['dice_seed42']:8.4f} {v['dice_seed123']:8.4f} "
              f"{v['dice_seed3407']:9.4f} {v['dice_final_mean']:8.4f} {v['seed_spread']:7.4f} "
              f"{v['dice_global']:8.4f} {v['delta_mean']:+8.4f}")

    print("\n=== SUBCLASS (KUB stone types), VAL808 ===")
    print(f"{'subclass':16s} {'n':>4s} {'seed42':>8s} {'seed123':>8s} {'seed3407':>9s} "
          f"{'mean':>8s} {'global':>8s} {'delta':>8s}")
    for c, v in sub["KUB"]["subclasses"].items():
        print(f"{c:16s} {v['n']:4d} {v['dice_seed42']:8.4f} {v['dice_seed123']:8.4f} "
              f"{v['dice_seed3407']:9.4f} {v['dice_final_mean']:8.4f} {v['dice_global']:8.4f} "
              f"{v['delta_mean']:+8.4f}")


if __name__ == "__main__":
    main()
