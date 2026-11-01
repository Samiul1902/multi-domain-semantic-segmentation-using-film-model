"""Reproducible C2 (BARR) aggregation from existing verified artifacts.

No inference is run; only committed result tables are read. Populations are never
pooled: VAL808 (selection-consumed), ROUTER_DEVELOPMENT (in-sample subset of
TRAIN5832), ROUTER_HOLDOUT875 (historical, disclosed deviation, not to be reused),
and the 884-case external retrospective stress test are separate sections.

  python scripts/analysis/c2_barr_aggregator.py [--out-dir DIR]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.research.paper_assets import validation as V  # noqa: E402

T = ROOT / "reports" / "tables"
OUT = ROOT / "reports" / "tables" / "c2_barr"
DOMAINS = ("ISIC", "BUSI", "KVASIR", "KUB")
EPS = 1e-9
SEEDS = (42, 123, 3407)


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


def b(x):
    return str(x).strip().lower() in ("true", "1")


def mean(v):
    return sum(v) / len(v)


def outcome(d):
    return "beneficial" if d > EPS else "harmful" if d < -EPS else "unchanged"


def funnel(rows, selected, adopted, delta):
    """rows: per-image dicts; returns counts with explicit denominators."""
    n = len(rows)
    sel = [r for r in rows if selected(r)]
    ado = [r for r in sel if adopted(r)]
    rej = [r for r in sel if not adopted(r)]
    oc = {k: sum(outcome(delta(r)) == k for r in ado) for k in ("beneficial", "harmful", "unchanged")}
    V.require_funnel(n, len(sel), len(ado), len(rej), oc["beneficial"], oc["harmful"], oc["unchanged"])
    return {"n_all": n, "n_routed": len(sel), "n_adopted": len(ado), "n_rejected": len(rej), "n_never_selected": n - len(sel),
            "adopted_beneficial": oc["beneficial"], "adopted_harmful": oc["harmful"], "adopted_unchanged": oc["unchanged"],
            "mean_delta_all_cases": mean([delta(r) for r in rows]),
            "mean_delta_routed_cases": mean([delta(r) for r in sel]) if sel else None,
            "mean_delta_adopted_cases": mean([delta(r) for r in ado]) if ado else None,
            "mean_delta_rejected_cases": mean([delta(r) for r in rej]) if rej else None,
            "harm_rate_conditional_on_adopted": oc["harmful"] / len(ado) if ado else None,
            "harm_rate_intent_to_treat_all": oc["harmful"] / n}


def per_domain(rows, g, f):
    out = {}
    for d in DOMAINS:
        rr = [r for r in rows if r["domain"] == d]
        out[d] = {"n": len(rr), "global": mean([g(r) for r in rr]), "barr": mean([f(r) for r in rr])}
        out[d]["delta"] = out[d]["barr"] - out[d]["global"]
    out["_macro"] = {k: mean([out[d][k] for d in DOMAINS]) for k in ("global", "barr", "delta")}
    return out


def val808():
    res, srcs, checks = [], [], []
    summ = {r["metric"]: r for r in rd(T / "phase29_val808_three_seed_summary.csv")}
    for s in SEEDS:
        p = T / f"phase29_seed{s}_val808_predictions.csv"
        srcs.append(p)
        rows = rd(p)
        V.require_unique_ids([r["sample_id"] for r in rows], "VAL808 case")
        V.require_dataset_labels([r["domain"] for r in rows], DOMAINS)
        for r in rows:
            r["g"], r["f"] = float(r["global_dice"]), float(r["final_dice"])
            V.require_finite([r["g"], r["f"]])
        assert len(rows) == 808
        V.require_paired_sign([r["f"] for r in rows], [r["g"] for r in rows], [float(r["delta_dice"]) for r in rows], 1e-9)
        fn = funnel(rows, lambda r: b(r["selected"]), lambda r: b(r["safety_accept"]), lambda r: r["f"] - r["g"])
        pdm = per_domain(rows, lambda r: r["g"], lambda r: r["f"])
        key = f"seed{s}"
        checks.append({"check": f"VAL808 {key} macro delta equals phase29 summary", "ok": abs(pdm["_macro"]["delta"] - float(summ["macro_delta_dice"][key])) < 1e-9})
        checks.append({"check": f"VAL808 {key} n_routed equals phase29 summary", "ok": fn["n_routed"] == round(float(summ["selected_fraction"][key]) * 808)})
        res.append({"seed": s, "funnel": fn, "per_domain": pdm})
    return res, srcs, checks


def historical_holdout():
    p = T / "phase30_router_holdout_scored_results.csv"
    rows = rd(p)
    V.require_unique_ids([r["sample_id"] for r in rows], "ROUTER_HOLDOUT case")
    V.require_dataset_labels([r["dataset"] for r in rows], DOMAINS)
    for r in rows:
        r["domain"] = r["dataset"]; r["g"] = float(r["global_dice"]); r["f"] = float(r["a8_dice"])
    fn = funnel(rows, lambda r: r["router_decision"] == "EXECUTE", lambda r: b(r["somega_accept"]), lambda r: r["f"] - r["g"])
    pdm = per_domain(rows, lambda r: r["g"], lambda r: r["f"])
    chk = [{"check": "ROUTER_HOLDOUT per-domain A8 deltas equal phase30 summary table",
            "ok": all(abs(pdm[r["domain"]]["delta"] - float(r["delta_dice_a8"])) < 1e-9 for r in rd(T / "phase30_router_holdout_per_domain_results.csv"))}]
    return {"funnel": fn, "per_domain": pdm}, p, chk


def development():
    p = T / "phase28_table_02_arm_primary_metrics.csv"
    out = []
    for r in rd(p):
        n_all = 4957
        routed, ben, harm = int(r["n_routed"]), int(r["n_beneficial_routed"]), int(r["n_harmful_routed"])
        out.append({"arm": r["arm"], "n_all": n_all, "n_routed": routed, "beneficial_routed": ben, "harmful_routed": harm,
                    "unchanged_routed": routed - ben - harm, "mean_delta_routed": float(r["mean_true_delta_dice_routed"]),
                    "mean_delta_all_cases": float(r["sum_true_delta_dice"]) / n_all,
                    "harm_rate_conditional_on_routed": harm / routed if routed else None, "harm_rate_intent_to_treat_all": harm / n_all})
    a8 = [x for x in out if x["arm"] == "A8"][0]
    return out, p, [{"check": "A8 conditional harm 390/1205 as in manuscript", "ok": a8["harmful_routed"] == 390 and a8["n_routed"] == 1205}]


def external():
    p_pair, p_case, p_shift = T / "c1_external_stress_paired.csv", T / "c1_external_stress_per_case.csv", T / "c1_external_stress_domain_shift.csv"
    pair = rd(p_pair)
    V.require_unique_ids([r["sample_id"] for r in pair], "external case")
    V.require_paired_sign([float(r["barr"]) for r in pair], [float(r["global"]) for r in pair], [float(r["delta_dice"]) for r in pair], 1e-9)
    shift = {r["cohort"]: r for r in rd(p_shift)}
    case = rd(p_case)
    res, chk = {}, []
    for ck, name in (("cvc", "CVC-ClinicDB"), ("breast", "BrEaST-Lesions-USG"), ("stones", "Stones_where_are_you")):
        rr = [r for r in pair if r["cohort_key"] == ck]
        for r in rr:
            r["g"], r["f"] = float(r["global"]), float(r["barr"])
        fn = funnel(rr, lambda r: r["state"] != "NOT_ATTEMPTED", lambda r: r["state"] == "ACCEPTED", lambda r: r["f"] - r["g"])
        res[name] = {"funnel": fn, "global_dice": mean([r["g"] for r in rr]), "barr_dice": mean([r["f"] for r in rr]),
                     "barr_minus_global_pp": (mean([r["f"] for r in rr]) - mean([r["g"] for r in rr])) * 100}
        chk.append({"check": f"{name} recomputed Dice equals domain-shift table",
                    "ok": abs(res[name]["global_dice"] - float(shift[name]["external_global_dice"])) < 1e-9 and abs(res[name]["barr_dice"] - float(shift[name]["external_barr_dice"])) < 1e-9})
    free = [r for r in case if r["cohort_key"] == "stones" and r["arm"] == "global" and not b(r["has_stone_annotation"])]
    barr_free = [r for r in case if r["cohort_key"] == "stones" and r["arm"] == "barr" and not b(r["has_stone_annotation"])]
    fg = sum(float(r["pred_pixels"]) > 0 for r in free)
    res["Stones_where_are_you"]["stone_free_failure"] = {
        "n_stone_free": len(free), "global_foreground_predicted": fg,
        "barr_foreground_predicted": sum(float(r["pred_pixels"]) > 0 for r in barr_free),
        "case_level_specificity_global": 1 - fg / len(free)}
    chk.append({"check": "stone-free failure preserved: 14/14 receive foreground", "ok": fg == 14 == len(free)})
    return res, [p_pair, p_case, p_shift], chk


def compute():
    a, l = T / "phase34_analytical_compute_summary_v1_3.csv", T / "phase34_batch1_latency_results_v1_4.csv"
    ana = {r["reference"]: float(r["macs"]) for r in rd(a) if r["macs"]}
    lat = {r["arm"]: {"mean_ms": float(r["mean_ms"]), "std_ms": float(r["std_ms"]), "n": int(r["n"]), "hardware": r["hardware"]} for r in rd(l)}
    base = ana["LITERAL_GLOBAL_ONLY_C1"]
    return {"analytical_gmacs_lower_bound": {k: v / 1e9 for k, v in ana.items()},
            "analytical_ratio_to_global": {k: v / base for k, v in ana.items()},
            "measured_batch1_latency": lat,
            "note": "Analytical MACs and measured latency are separate; BARR is not shown to be cheaper than Global (A8 expected conditional is 1.028x Global analytically)."}, [a, l]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--out-dir", type=Path, default=OUT)
    a = ap.parse_args(argv)
    v, vs, c1 = val808(); h, hs, c2 = historical_holdout(); d, ds, c3 = development(); e, es, c4 = external(); cp, cs = compute()
    checks = c1 + c2 + c3 + c4
    if not all(c["ok"] for c in checks):
        print(json.dumps([c for c in checks if not c["ok"]], indent=2), file=sys.stderr)
        return 4
    srcs = vs + [hs, ds] + es + cs
    pops = {
        "VAL808": {"evidence_class": "descriptive; selection-consumed", "n": 808, "unit": "Dice proportion (0-1)", "seeds": "three BARR downstream seeds over one fixed global backbone"},
        "ROUTER_DEVELOPMENT": {"evidence_class": "in-sample (subset of TRAIN5832)", "n": 4957, "unit": "Dice proportion"},
        "ROUTER_HOLDOUT875": {"evidence_class": "historical; disclosed deviation; not to be reused for tuning", "n": 875, "unit": "Dice proportion"},
        "EXTERNAL_RETROSPECTIVE_884": {"evidence_class": "exploratory retrospective stress test; not prospective validation", "n": 884, "unit": "Dice proportion; differences in percentage points"}}
    result = {"schema": "c2_barr_aggregate_v1", "populations": pops, "pooling": "NONE - populations are reported separately",
              "val808_by_seed": v, "router_holdout_historical": h, "development_arms": d, "external": e, "compute": cp,
              "denominator_policy": "all-case, routed, adopted, rejected and never-selected are reported separately; conditional means are not all-case averages",
              "checks": checks, "sources": {rel(p): sha(p) for p in srcs}, "inference_rerun": False, "protected_data_accessed": False}
    out = a.out_dir; out.mkdir(parents=True, exist_ok=True)
    (out / "c2_barr_aggregate.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    def w(name, header, rows):
        with open(out / name, "w", newline="", encoding="utf-8") as f:
            wr = csv.writer(f, lineterminator="\n"); wr.writerow(header); wr.writerows(rows)
    w("c2_val808_per_domain.csv", ["population", "seed", "domain", "n", "global_dice", "barr_dice", "delta_dice"],
      [["VAL808", r["seed"], k, x["n"], x["global"], x["barr"], x["delta"]] for r in v for k, x in r["per_domain"].items() if k != "_macro"]
      + [["VAL808", r["seed"], "MACRO_EQUAL_DOMAIN", 808, r["per_domain"]["_macro"]["global"], r["per_domain"]["_macro"]["barr"], r["per_domain"]["_macro"]["delta"]] for r in v])
    fk = list(v[0]["funnel"].keys())
    w("c2_funnels.csv", ["population", "unit"] + fk,
      [["VAL808", f"seed{r['seed']}"] + [r["funnel"][k] for k in fk] for r in v]
      + [["ROUTER_HOLDOUT875 (historical)", "A8"] + [h["funnel"][k] for k in fk]]
      + [["EXTERNAL_884", k] + [x["funnel"][k2] for k2 in fk] for k, x in e.items()])
    w("c2_development_arms.csv", list(d[0].keys()), [list(x.values()) for x in d])
    w("c2_external.csv", ["cohort", "n", "global_dice", "barr_dice", "barr_minus_global_pp"],
      [[k, x["funnel"]["n_all"], x["global_dice"], x["barr_dice"], x["barr_minus_global_pp"]] for k, x in e.items()])
    print("C2 aggregation OK;", len(checks), "checks passed; out:", rel(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
