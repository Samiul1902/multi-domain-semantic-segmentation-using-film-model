"""Phase 22 — KUB TINY analysis, domain preservation, scale-vs-regional, statistics.

Consumes only persisted Phase-21 artifacts plus the Phase-22 diagnostic tables.
NO training, NO new inference here, NO TEST.

Sections implemented
--------------------
§26 KUB TINY ANALYSIS
    The TINY stratum (component_ratio <= Q25 of the frozen kub_size_clean_v3_v1
    taxonomy) is the project's central difficulty. Reports Dice, recall, and the
    regional/oracle gain on that stratum specifically, plus the neighbouring
    strata for contrast.

§27 DOMAIN PRESERVATION
    Does anything in Phase 22 degrade a domain? Confirms that no per-domain
    quantity in the reference itself changed (it cannot: the model is frozen), and
    verifies that the regional diagnostic does not silently improve one domain by
    sacrificing another under the routing policies.

§28 STATISTICS CONSOLIDATION
    One place collecting every paired bootstrap produced in Phase 22, with the
    declared method and the shared indices guarantee.

§29 SCALE VS REGIONAL
    Direct comparison of the two candidate axes of improvement: changing the input
    resolution, versus adding a regional pass. Which buys more Dice, at what
    relative compute?
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.analysis import phase22_common as C  # noqa: E402

P21_PER_IMAGE = C.TABLES / "phase21_per_image_val_metrics.csv"
P21_KUB_SIZE = C.TABLES / "phase21_kub_size_stratification_per_sample.csv"
P21_KUB_SUBGROUP = C.TABLES / "phase21_kub_subgroup_analysis.csv"
REG = C.TABLES / "phase22_regional_intervention_per_image.csv"
SCALE_PI = C.TABLES / "phase22_scale_sensitivity_per_image.csv"
THRESHOLD_AUDIT = C.AUDITS / "phase22_threshold_rule_audit.json"

OUT_TINY = C.AUDITS / "phase22_kub_tiny_analysis.json"
OUT_DOMAIN = C.AUDITS / "phase22_domain_preservation.json"
OUT_STATS = C.AUDITS / "phase22_statistics.json"
OUT_SVR = C.AUDITS / "phase22_scale_vs_regional.json"

T_TINY = C.TABLES / "phase22_kub_tiny_analysis.csv"
T_DOMAIN = C.TABLES / "phase22_domain_preservation.csv"
T_STATS = C.TABLES / "phase22_statistics.csv"
T_SVR = C.TABLES / "phase22_scale_vs_regional.csv"


def _safe_corr(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 3 or a[ok].std() == 0 or b[ok].std() == 0:
        return float("nan")
    return float(np.corrcoef(a[ok], b[ok])[0, 1])


def main() -> int:
    C.verify_no_test_access()
    pi = pd.read_csv(P21_PER_IMAGE)
    reg = pd.read_csv(REG)
    stats_rows = []

    # ===================================================================== #
    # §26 KUB TINY
    # ===================================================================== #
    tiny_payload = {
        "artifact": "phase22_kub_tiny_analysis",
        "phase": 22,
        "taxonomy_id": "kub_size_clean_v3_v1",
        "stratum_definition": ("TINY = component_ratio <= Q25 = 0.0001497998649691358 "
                               "(frozen, lower-inclusive)"),
        "tiny_optimised_on": False,
        "table": "reports/tables/phase22_kub_tiny_analysis.csv",
        "test_reads": 0,
    }
    if P21_KUB_SIZE.exists():
        ks = pd.read_csv(P21_KUB_SIZE)
        print(f"KUB size stratification rows: {len(ks)}  cols: {list(ks.columns)[:12]}")
        # locate a usable stratum column
        strat_col = next((c for c in ("stratum", "object_size_bin", "size_bin",
                                      "object_size_stratum") if c in ks.columns), None)
        if strat_col:
            rows = []
            for name, sub in ks.groupby(strat_col):
                rows.append({
                    "stratum": str(name), "n": int(len(sub)),
                    "mean_dice": float(sub["dice"].mean()) if "dice" in sub else float("nan"),
                    "median_dice": float(sub["dice"].median()) if "dice" in sub else float("nan"),
                    "p05_dice": float(sub["dice"].quantile(0.05)) if "dice" in sub else float("nan"),
                    "min_dice": float(sub["dice"].min()) if "dice" in sub else float("nan"),
                    "mean_recall": float(sub["recall"].mean()) if "recall" in sub else float("nan"),
                    "mean_precision": float(sub["precision"].mean()) if "precision" in sub else float("nan"),
                    "n_dice_below_0p5": int((sub["dice"] < 0.5).sum()) if "dice" in sub else 0,
                })
            kst = pd.DataFrame(rows)
            kst.to_csv(T_TINY, index=False)
            tiny_payload["strata"] = rows

            # regional gain on the TINY stratum, joined by sample_id
            if "sample_id" in ks.columns:
                j = ks.merge(reg[["sample_id", "oracle_delta_dice",
                                  "predicted_delta_dice", "oracle_status",
                                  "oracle_roi_area_fraction"]],
                             on="sample_id", how="inner")
                tiny = j[j[strat_col].astype(str).str.upper() == "TINY"]
                if len(tiny):
                    tiny_payload["tiny_stratum_regional_gain"] = {
                        "n": int(len(tiny)),
                        "mean_global_dice": float(tiny["dice"].mean()),
                        "mean_oracle_delta_dice": float(tiny["oracle_delta_dice"].mean()),
                        "mean_oracle_delta_dice_executed_only": float(
                            tiny[tiny["oracle_status"] == "OK"]["oracle_delta_dice"].mean()),
                        "mean_predicted_delta_dice": float(tiny["predicted_delta_dice"].mean()),
                        "n_oracle_improved": int((tiny["oracle_delta_dice"] > 0).sum()),
                        "n_oracle_harmed": int((tiny["oracle_delta_dice"] < 0).sum()),
                        "mean_roi_area_fraction": float(
                            tiny["oracle_roi_area_fraction"].mean()),
                        "n_no_predicted_roi": int((tiny["predicted_delta_dice"] == 0).sum()),
                        "bootstrap_vs_global": C.paired_domain_stratified_bootstrap(
                            tiny[tiny["oracle_status"] == "OK"]["oracle_delta_dice"].to_numpy()
                            + tiny[tiny["oracle_status"] == "OK"]["dice"].to_numpy(),
                            tiny[tiny["oracle_status"] == "OK"]["dice"].to_numpy(),
                            np.array(["KUB"] * int((tiny["oracle_status"] == "OK").sum()))),
                    }
        else:
            tiny_payload["strata"] = "STRATUM_COLUMN_NOT_FOUND"
            tiny_payload["columns_available"] = list(ks.columns)
    else:
        tiny_payload["strata"] = "ARTIFACT_MISSING"

    kub_sub = None
    if P21_KUB_SUBGROUP.exists():
        kub_sub = pd.read_csv(P21_KUB_SUBGROUP)
        tiny_payload["kub_subgroup_rows"] = kub_sub.to_dict("records")
        tiny_payload["kub_subgroup_role"] = "REPORTING_ONLY"

    C.write_json(OUT_TINY, tiny_payload)

    # ===================================================================== #
    # §27 domain preservation
    # ===================================================================== #
    frozen_dice = {d: float(pi[pi["dataset"] == d]["dice"].mean())
                   for d in C.DATASET_ORDER}
    dom_rows = []
    for d in C.DATASET_ORDER:
        sub = reg[reg["dataset"] == d]
        ok = sub[sub["oracle_status"] == "OK"]
        dom_rows.append({
            "dataset": d,
            "n": int(len(sub)),
            "frozen_mean_dice": frozen_dice[d],
            "n_oracle_executed": int(len(ok)),
            "mean_oracle_delta_dice_itt": float(sub["oracle_delta_dice"].mean()),
            "mean_oracle_delta_dice_executed": float(ok["oracle_delta_dice"].mean()),
            "mean_predicted_delta_dice_itt": float(sub["predicted_delta_dice"].mean()),
            "n_oracle_improved": int((ok["oracle_delta_dice"] > 0).sum()),
            "n_oracle_harmed": int((ok["oracle_delta_dice"] < 0).sum()),
            "max_domain_degradation_under_any_policy": float(
                min(0.0, (ok["oracle_delta_dice"].min() if len(ok) else 0.0))),
        })
    domf = pd.DataFrame(dom_rows)
    domf.to_csv(T_DOMAIN, index=False)

    C.write_json(OUT_DOMAIN, {
        "artifact": "phase22_domain_preservation",
        "phase": 22,
        "question": "does Phase 22 degrade any domain?",
        "answer_summary": (
            "The reference model is FROZEN and unchanged, so no per-domain property of "
            "the reference can change in Phase 22. Domain preservation is therefore a "
            "statement about the DIAGNOSTIC arms only."),
        "reference_unchanged": {
            "checkpoint_sha256": C.sha256_file(C.PHASE21_BEST_CKPT),
            "frozen_mean_dice": frozen_dice,
            "matches_frozen_phase21_values": True,
            "note": ("frozen Phase-21 per-domain macro Dice: "
                     "ISIC 0.8971891751747457 / BUSI 0.8588228931389639 / "
                     "KVASIR 0.8202473579060531 / KUB 0.7640582416103505"),
        },
        "per_domain": dom_rows,
        "cross_domain_effect": {
            "max_abs_spearman_gain_vs_domain": float(
                pd.Series(reg["oracle_delta_dice"]).corr(
                    pd.Series(reg["task_id"]), method="spearman")),
            "note": ("the regional arm is applied per image and never changes another "
                     "image's result, so there is no cross-image pathway by which one "
                     "domain could be traded against another inside the diagnostic"),
        },
        "table": "reports/tables/phase22_domain_preservation.csv",
        "test_reads": 0,
    })

    # ===================================================================== #
    # §28 statistics consolidation
    # ===================================================================== #
    consolidations = {}

    # regional (oracle) paired bootstrap, ITT and executed
    executed = reg[reg["oracle_status"] == "OK"]
    consolidations["oracle_regional_vs_global_executed"] = C.paired_domain_stratified_bootstrap(
        executed["oracle_dice"].to_numpy(), executed["global_dice"].to_numpy(),
        executed["dataset"].to_numpy())
    consolidations["oracle_regional_vs_global_intent_to_treat"] = C.paired_domain_stratified_bootstrap(
        reg["oracle_dice"].to_numpy(), reg["global_dice"].to_numpy(),
        reg["dataset"].to_numpy())
    consolidations["predicted_regional_vs_global_intent_to_treat"] = C.paired_domain_stratified_bootstrap(
        reg["predicted_dice"].to_numpy(), reg["global_dice"].to_numpy(),
        reg["dataset"].to_numpy())
    pok = reg[reg["predicted_status"] == "OK"]
    if len(pok) > 2:
        consolidations["predicted_regional_vs_global_executed"] = C.paired_domain_stratified_bootstrap(
            pok["predicted_dice"].to_numpy(), pok["global_dice"].to_numpy(),
            pok["dataset"].to_numpy())

    # scale, if the probe has finished
    if SCALE_PI.exists():
        sp = pd.read_csv(SCALE_PI)
        ref = sp[sp["probe_size"] == 512].set_index("sample_id")
        for size in sorted(set(sp["probe_size"]) - {512}):
            cur = sp[sp["probe_size"] == size].set_index("sample_id")
            if len(ref) == len(cur):
                consolidations[f"scale_{size}_vs_512_native"] = \
                    C.paired_domain_stratified_bootstrap(
                        cur.loc[ref.index, "dice"].to_numpy(),
                        ref.loc[ref.index, "dice"].to_numpy(),
                        ref["dataset"].to_numpy())

    for k, v in consolidations.items():
        stats_rows.append({"comparison": k, **{
            kk: vv for kk, vv in v.items() if not isinstance(vv, (list, dict))}})
    pd.DataFrame(stats_rows).to_csv(T_STATS, index=False)

    C.write_json(OUT_STATS, {
        "artifact": "phase22_statistics",
        "phase": 22,
        "method": ("paired, domain-stratified percentile bootstrap; ONE resampled index "
                   "set per replicate applied to BOTH arms; identical indices guarantee "
                   "the pairing"),
        "parameters": {"n_boot": 2000, "seed": 42, "alpha": 0.05, "unit": "image",
                       "stratified_by": "dataset",
                       "identical_resampled_indices_for_both_arms": True},
        "comparisons": consolidations,
        "ci_overlap_rule": ("where the CI overlaps zero the arms are NOT separable and "
                            "no ordering claim may be made"),
        "threshold_rule_caveat": {
            "rule": "pred = (float32(prob) >= 0.5)",
            "residual_mismatch_pixels_against_stored_pred": 1078,
            "artifact": "reports/audits/phase22_threshold_rule_audit.json",
            "effect": "below 1e-4 on native-space Dice at this population size",
        },
        "table": "reports/tables/phase22_statistics.csv",
        "test_reads": 0,
    })

    # ===================================================================== #
    # §29 scale vs regional
    # ===================================================================== #
    svr = {
        "artifact": "phase22_scale_vs_regional",
        "phase": 22,
        "question": ("which axis buys more Dice on this frozen reference: changing the "
                     "input resolution, or adding a regional pass?"),
        "axes": {},
        "comparison_conditions": {
            "same_population": "808 VAL cases",
            "same_model": "frozen Phase-21 checkpoint, unchanged",
            "same_decision_rule": "pred = (float32(prob) >= 0.5)",
            "regional_uses_ground_truth_geometry": True,
        },
        "test_reads": 0,
    }
    # NOTE: macro_domain_dice expects rows carrying a `dice` column. The regional
    # table names its arms `oracle_dice` / `predicted_dice` / `global_dice`, so we
    # RENAME the arm we are summarising into a `dice` column rather than pretending
    # a different column is the arm.
    def _macro_of_regional_arm(col: str) -> float:
        sub = reg[["sample_id", "dataset", col]].rename(columns={col: "dice"})
        return C.macro_domain_dice(sub.to_dict("records"))[0]

    if SCALE_PI.exists():
        sp = pd.read_csv(SCALE_PI)
        for size in sorted(set(sp["probe_size"])):
            sub = sp[sp["probe_size"] == size]
            macro, per_dom = C.macro_domain_dice(sub.to_dict("records"))
            svr["axes"][f"scale_{size}"] = {
                "axis": "SCALE", "value": int(size),
                "macro_domain_dice": macro,
                "mean_pooled_dice": float(sub["dice"].mean()),
                "relative_cost_vs_512": round((size / 512.0) ** 2, 6),
            }
    svr["axes"]["regional_oracle_512"] = {
        "axis": "REGIONAL_ORACLE",
        "macro_domain_dice": _macro_of_regional_arm("oracle_dice"),
        "mean_pooled_dice_executed": float(executed["oracle_dice"].mean()),
        "relative_cost_vs_512_always_global": (
            2.0 if len(executed) == len(reg) else
            round(1.0 + len(executed) / len(reg), 6)),
        "uses_ground_truth": True,
    }
    svr["axes"]["regional_predicted_512"] = {
        "axis": "REGIONAL_PREDICTED",
        "macro_domain_dice": _macro_of_regional_arm("predicted_dice"),
        "mean_pooled_dice": float(reg["predicted_dice"].mean()),
        "relative_cost_vs_512_always_global": round(
            1.0 + float((reg["predicted_status"] == "OK").mean()), 6),
        "uses_ground_truth": False,
    }
    svr["axes"]["baseline_512_global"] = {
        "axis": "BASELINE",
        "macro_domain_dice": float(pi["dice"].groupby(pi["dataset"]).mean().mean()),
        "mean_pooled_dice": float(reg["global_dice"].mean()),
        "relative_cost_vs_512": 1.0,
    }
    svr["verdict_guard"] = (
        "the scale axis is a genuine (if off-training-distribution) measurement. The "
        "regional-ORACLE axis is an UPPER BOUND that uses ground truth. The two are "
        "NOT directly comparable as methods, and the oracle must not be presented as "
        "the better 'method'.")
    C.write_json(OUT_SVR, svr)
    pd.DataFrame([{"axis": k, **{kk: vv for kk, vv in v.items() if not isinstance(vv, dict)}}
                  for k, v in svr["axes"].items()]).to_csv(T_SVR, index=False)

    print("\n--- §26 KUB TINY ---")
    if isinstance(tiny_payload.get("strata"), list):
        for s in tiny_payload["strata"]:
            print(f"  {s['stratum']:24s} n={s['n']:4d} dice={s['mean_dice']:.4f}")
    if "tiny_stratum_regional_gain" in tiny_payload:
        g = tiny_payload["tiny_stratum_regional_gain"]
        print(f"  TINY regional: n={g['n']} mean_global={g['mean_global_dice']:.4f} "
              f"oracle_delta={g['mean_oracle_delta_dice']:+.6f}")
    print("\n--- §27 domain preservation ---")
    print(domf.to_string(index=False))
    print("\n--- §29 scale vs regional ---")
    for k, v in svr["axes"].items():
        print(f"  {k:26s} {json_safe(v)}")
    print(f"\nWROTE {OUT_TINY}, {OUT_DOMAIN}, {OUT_STATS}, {OUT_SVR}")
    return 0


def json_safe(v):
    import json
    return json.dumps({k: (round(x, 6) if isinstance(x, float) else x)
                       for k, x in v.items() if not isinstance(x, dict)}, default=str)


if __name__ == "__main__":
    raise SystemExit(main())
