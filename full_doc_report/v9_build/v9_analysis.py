"""V9 analysis: recompute every derived number from frozen artifacts.

No training, no inference, no TEST1683 access.  External paired deltas and
bootstrap intervals are computed from the frozen per-case saved-prediction
table, which is analysis of saved outputs, not new inference.
"""
from __future__ import annotations
import csv, json, math, random
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
FDR = ROOT / "full_doc_report"
OUT = FDR / "v9_build"
OUT.mkdir(parents=True, exist_ok=True)


def read_csv(p):
    with open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def f(x):
    return float(x)


def mean(xs):
    return sum(xs) / len(xs)


def pct(xs, q):
    ys = sorted(xs)
    if not ys:
        return None
    k = (len(ys) - 1) * q
    lo = int(math.floor(k)); hi = int(math.ceil(k))
    if lo == hi:
        return ys[lo]
    return ys[lo] * (hi - k) + ys[hi] * (k - lo)


def bootstrap_ci(deltas, B=4000, seed=42):
    rng = random.Random(seed)
    n = len(deltas)
    stats = []
    for _ in range(B):
        s = 0.0
        for _ in range(n):
            s += deltas[rng.randrange(n)]
        stats.append(s / n)
    return pct(stats, 0.025), pct(stats, 0.975)


# ---------------------------------------------------------------- internal
ps = read_csv(FDR / "tables" / "REMEDFILM_INTERNAL_PER_SAMPLE.csv")
assert len(ps) == 808
g = [f(r["global_dice"]) for r in ps]
fu = [f(r["final_dice"]) for r in ps]
d = [f(r["delta_dice"]) for r in ps]
by_dom = defaultdict(list)
for r in ps:
    by_dom[r["domain"]].append(r)

internal = {
    "n": len(ps),
    "macro_full": mean([mean([f(r["final_dice"]) for r in by_dom[k]]) for k in ("ISIC", "BUSI", "KVASIR", "KUB")]),
    "macro_global": mean([mean([f(r["global_dice"]) for r in by_dom[k]]) for k in ("ISIC", "BUSI", "KVASIR", "KUB")]),
    "pooled_full": mean(fu),
    "pooled_global": mean(g),
    "pooled_delta": mean(d),
    "n_harmful": sum(1 for r in ps if r["harmful"] == "True"),
    "n_beneficial": sum(1 for r in ps if r["beneficial"] == "True"),
    "n_unchanged": sum(1 for r in ps if r["unchanged"] == "True"),
    "branches": dict(Counter(r["branch"] for r in ps)),
    "decisions": dict(Counter(r["router_decision"] for r in ps)),
    "domains": {},
}
for k in ("ISIC", "BUSI", "KVASIR", "KUB"):
    rs = by_dom[k]
    internal["domains"][k] = {
        "n": len(rs),
        "global_dice": mean([f(r["global_dice"]) for r in rs]),
        "full_dice": mean([f(r["final_dice"]) for r in rs]),
        "delta": mean([f(r["delta_dice"]) for r in rs]),
        "full_iou": mean([f(r["final_iou"]) for r in rs]),
        "global_iou": mean([f(r["global_iou"]) for r in rs]),
        "full_precision": mean([f(r["final_precision"]) for r in rs]),
        "global_precision": mean([f(r["global_precision"]) for r in rs]),
        "full_recall": mean([f(r["final_recall"]) for r in rs]),
        "global_recall": mean([f(r["global_recall"]) for r in rs]),
        "full_hd95": mean([f(r["final_hd95"]) for r in rs]),
        "global_hd95": mean([f(r["global_hd95"]) for r in rs]),
        "harmful": sum(1 for r in rs if r["harmful"] == "True"),
        "beneficial": sum(1 for r in rs if r["beneficial"] == "True"),
        "unchanged": sum(1 for r in rs if r["unchanged"] == "True"),
        "executed": sum(1 for r in rs if r["router_decision"] == "EXECUTE"),
        "accepted": sum(1 for r in rs if r["branch"] == "EXECUTE_THEN_ACCEPT"),
    }
pdj = json.loads((FDR / "tables" / "REMEDFILM_PAIRED_DELTA.json").read_text(encoding="utf-8"))
internal["macro_delta"] = pdj["point"]
internal["macro_delta_ci"] = [pdj["ci_low"], pdj["ci_high"]]

# ---------------------------------------------------------------- external
ext = read_csv(ROOT / "reports" / "tables" / "c1_external_stress_per_case.csv")
pairs = defaultdict(dict)
for r in ext:
    pairs[(r["cohort_key"], r["sample_id"])][r["arm"]] = r
assert len(pairs) == 884
external = {"n_total": 884, "cohorts": {}}
for ck in ("cvc", "breast", "stones"):
    keys = [k for k in pairs if k[0] == ck]
    rows = [pairs[k] for k in keys]
    gd = [f(x["global"]["Dice"]) for x in rows]
    fd = [f(x["barr"]["Dice"]) for x in rows]
    dd = [f(x["barr"]["Dice"]) - f(x["global"]["Dice"]) for x in rows]
    sel = [x for x in rows if x["barr"]["state"] in ("ACCEPTED", "REJECTED")]
    sel_dd = [f(x["barr"]["Dice"]) - f(x["global"]["Dice"]) for x in sel]
    lo, hi = bootstrap_ci(dd)
    external["cohorts"][ck] = {
        "n": len(rows),
        "global_dice": mean(gd), "full_dice": mean(fd),
        "delta": mean(dd), "delta_ci": [lo, hi],
        "improved": sum(1 for x in dd if x > 1e-12),
        "worsened": sum(1 for x in dd if x < -1e-12),
        "unchanged": sum(1 for x in dd if abs(x) <= 1e-12),
        "n_selected": len(sel),
        "selected_delta": mean(sel_dd) if sel_dd else None,
        "selected_improved": sum(1 for x in sel_dd if x > 1e-12),
        "selected_worsened": sum(1 for x in sel_dd if x < -1e-12),
        "fp_only": sum(1 for x in rows if x["global"]["fp_only_case"] == "True"),
        "gt_empty": sum(1 for x in rows if x["global"]["gt_empty"] == "True"),
        "pred_empty": sum(1 for x in rows if x["global"]["pred_empty"] == "True"),
        "global_iou": mean([f(x["global"]["IoU"]) for x in rows]),
        "full_iou": mean([f(x["barr"]["IoU"]) for x in rows]),
        "global_precision": mean([f(x["global"]["Precision"]) for x in rows if x["global"]["Precision"] not in ("", None)]),
        "full_precision": mean([f(x["barr"]["Precision"]) for x in rows if x["barr"]["Precision"] not in ("", None)]),
        "global_recall": mean([f(x["global"]["Recall"]) for x in rows if x["global"]["Recall"] not in ("", None)]),
        "full_recall": mean([f(x["barr"]["Recall"]) for x in rows if x["barr"]["Recall"] not in ("", None)]),
        "precision_n": sum(1 for x in rows if x["global"]["Precision"] not in ("", None)),
        "recall_n": sum(1 for x in rows if x["global"]["Recall"] not in ("", None)),
        "global_hd95": mean([f(x["global"]["HD95_px"]) for x in rows if x["global"]["HD95_px"] not in ("", None)]),
        "full_hd95": mean([f(x["barr"]["HD95_px"]) for x in rows if x["barr"]["HD95_px"] not in ("", None)]),
        "global_assd": mean([f(x["global"]["ASSD_px"]) for x in rows if x["global"]["ASSD_px"] not in ("", None)]),
        "full_assd": mean([f(x["barr"]["ASSD_px"]) for x in rows if x["barr"]["ASSD_px"] not in ("", None)]),
        "hd95_n": sum(1 for x in rows if x["global"]["HD95_px"] not in ("", None)),
        "assd_n": sum(1 for x in rows if x["global"]["ASSD_px"] not in ("", None)),
        "states": dict(Counter(x["barr"]["state"] for x in rows)),
    }
# stones subgroups
for label, pred in (("six_positive", lambda x: x["global"]["has_stone_annotation"] == "True"),
                    ("fourteen_absent", lambda x: x["global"]["gt_empty"] == "True")):
    rows = [pairs[k] for k in pairs if k[0] == "stones" and pred(pairs[k])]
    dd = [f(x["barr"]["Dice"]) - f(x["global"]["Dice"]) for x in rows]
    external["cohorts"]["stones"][label] = {
        "n": len(rows),
        "global_dice": mean([f(x["global"]["Dice"]) for x in rows]),
        "full_dice": mean([f(x["barr"]["Dice"]) for x in rows]),
        "delta": mean(dd),
        "improved": sum(1 for x in dd if x > 1e-12),
        "worsened": sum(1 for x in dd if x < -1e-12),
        "unchanged": sum(1 for x in dd if abs(x) <= 1e-12),
        "fp_only": sum(1 for x in rows if x["global"]["fp_only_case"] == "True"),
        "full_fp_only": sum(1 for x in rows if x["barr"]["fp_only_case"] == "True"),
        "global_recall_n": sum(1 for x in rows if x["global"]["Recall"] not in ("", None)),
    }

# ---------------------------------------------------------------- ablation
t1 = {r["arm"]: r for r in read_csv(ROOT / "reports" / "tables" / "phase28_table_01_arm_definitions.csv")}
t2 = {r["arm"]: r for r in read_csv(ROOT / "reports" / "tables" / "phase28_table_02_arm_primary_metrics.csv")}
t7 = {r["contrast"]: r for r in read_csv(ROOT / "reports" / "tables" / "phase28_table_07_matched_paired_contrasts.csv")}
t8 = {r["contrast"]: r for r in read_csv(ROOT / "reports" / "tables" / "phase28_table_08_bootstrap_statistics.csv")}
DEV_N = 4957
G = 31_551_740_928
B = 36_160
R = 3_230_662_656
S = 1_168
ablation = {"population": "ROUTER_DEVELOPMENT_4957", "n": DEV_N, "arms": {}}
for arm in ["A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "R1", "R2", "R3", "F1"]:
    r = t2[arm]
    nr = int(r["n_routed"])
    sumd = f(r["sum_true_delta_dice"])
    p = nr / DEV_N
    cost = G + B + p * (R + S)
    ablation["arms"][arm] = {
        "definition": t1[arm]["definition"],
        "role": t1[arm]["role"],
        "n_routed": nr,
        "budget_fraction": nr / DEV_N,
        "all_eligible_mean_delta": sumd / DEV_N,
        "conditional_mean_delta": (sumd / nr) if nr else None,
        "beneficial_routed": int(r["n_beneficial_routed"]),
        "harmful_routed": int(r["n_harmful_routed"]),
        "harmful_all_eligible": int(r["n_harmful_routed"]) / DEV_N,
        "harmful_conditional": int(r["n_harmful_routed"]) / nr if nr else None,
        "benefit_capture": f(r["benefit_capture_vs_positive_mass"]),
        "gmac": cost / 1e9,
        "delta_gmac_vs_a0": (cost - (G + B)) / 1e9,
    }
ablation["contrasts"] = {}
for c in ("R1_vs_A6C7", "R2_vs_A6C7", "R3_vs_A6C7", "A8_vs_A7", "F1_integrated_vs_A8"):
    ablation["contrasts"][c] = {
        "mean_difference": f(t7[c]["paired_mean_difference"]),
        "ci_low": f(t8[c]["ci95_low"]),
        "ci_high": f(t8[c]["ci95_high"]),
        "n": int(t8[c]["n"]),
        "n_variant_better": int(t7[c]["n_variant_better"]),
        "n_reference_better": int(t7[c]["n_reference_better"]),
        "n_tied": int(t7[c]["n_tied"]),
        "ci_excludes_zero": not (f(t8[c]["ci95_low"]) <= 0 <= f(t8[c]["ci95_high"])),
    }

# ---------------------------------------------------------------- efficiency
val_exec = internal["domains"]["KUB"]["executed"] + internal["domains"]["ISIC"]["executed"] + \
    internal["domains"]["BUSI"]["executed"] + internal["domains"]["KVASIR"]["executed"]
val_p = val_exec / 808
hold_p = 240 / 875
efficiency = {
    "mac": {"G": G, "B": B, "R": R, "S": S},
    "always_refine_literal": G + R,
    "gated_execute_all": G + B + R + S,
    "val808_execute": val_exec,
    "val808_p": val_p,
    "val808_conditional_gmac": (G + B + val_p * (R + S)) / 1e9,
    "holdout_execute": 240,
    "holdout_p": hold_p,
    "holdout_conditional_gmac": (G + B + hold_p * (R + S)) / 1e9,
    "ratio_val_vs_always": (G + B + val_p * (R + S)) / (G + R),
    "latency_ms": {
        "skip_mean": 15.71835146522522, "skip_p50": 15.684608459472656,
        "execute_mean": 18.894091419219972, "execute_p50": 18.88663959503174,
        "holdout_weighted_mean": (635 / 875) * 15.71835146522522 + (240 / 875) * 18.894091419219972,
        "val808_weighted_mean": (529 / 808) * 15.71835146522522 + (279 / 808) * 18.894091419219972,
    },
}

# ---------------------------------------------------------------- robustness
rob = read_csv(ROOT / "reports" / "tables" / "phase36_robustness_v1_23" / "phase36_image_robustness_by_domain_condition.csv")
by_dom_cond = defaultdict(list)
for r in rob:
    by_dom_cond[r["domain"]].append((r["condition"], f(r["mean_paired_delta_dice"]), int(r["n"])))
robustness = {"source": "reports/tables/phase36_robustness_v1_23", "domains": {}}
for dom, vals in by_dom_cond.items():
    worst = min(vals, key=lambda x: x[1])
    best = max(vals, key=lambda x: x[1])
    robustness["domains"][dom] = {
        "conditions": len(vals),
        "worst_condition": worst[0], "worst_delta": worst[1],
        "best_condition": best[0], "best_delta": best[1],
        "mean_over_conditions": mean([v[1] for v in vals]),
        "all_negative": all(v[1] < 0 for v in vals),
    }

# ---------------------------------------------------------------- datasets
manifest = json.loads((ROOT / "manifests" / "manifest_metadata.json").read_text(encoding="utf-8"))

analysis = {
    "internal_val808": internal,
    "external884": external,
    "ablation_router_development": ablation,
    "efficiency": efficiency,
    "robustness_phase36": robustness,
    "manifest": manifest,
}
(OUT / "v9_analysis.json").write_text(json.dumps(analysis, indent=2), encoding="utf-8")
print(json.dumps({
    "internal": {k: v for k, v in internal.items() if k not in ("domains", "branches", "decisions")},
    "external": {k: {kk: vv for kk, vv in v.items() if not isinstance(vv, dict)}
                 for k, v in external["cohorts"].items()},
    "val808_gmac": efficiency["val808_conditional_gmac"],
    "val808_p": efficiency["val808_p"],
    "holdout_gmac": efficiency["holdout_conditional_gmac"],
    "latency": efficiency["latency_ms"],
}, indent=2))
