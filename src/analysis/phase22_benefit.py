"""Phase 22 — benefit heterogeneity, harm analysis, and accept-if-beneficial oracle.

Consumes ``reports/tables/phase22_regional_intervention_per_image.csv`` produced by
``src/analysis/phase22_regional.py``. NO new inference, NO training, NO TEST.

Sections implemented here
-------------------------
§15 BENEFIT HETEROGENEITY
    How does the regional (oracle) gain distribute? Is it concentrated in a few
    cases or broad? Does it correlate with baseline difficulty, domain, ROI size?
    Reports a Gini-like concentration, quantiles, the gain-vs-baseline relation,
    and a decile breakdown.

§16 ORACLE ACCEPT-IF-BENEFICIAL UPPER BOUND
    A PERFECT selector: apply the regional arm only where it strictly helps.
    This is the ceiling of any routing policy, oracle or learned. It is reported
    with the oracle-usage rate so the "accept everything" cost is visible.

§20 ROUTING REGRET
    Compares the oracle accept-if-beneficial policy against fixed policies
    (always-global, always-regional) and against a family of simple, deployable
    rule-based selectors. Regret = oracle_ceiling - policy_value.

§22 HARM ANALYSIS
    Where does the regional arm make things WORSE? Reports the harm distribution,
    the domains and strata responsible, and the magnitude of the worst harms.

Every quantity is reported both intent-to-treat (no-ROI cases count as 0 gain)
and restricted-to-executed (ROI-bearing cases only), because the two answer
different questions and conflating them would flatter the method.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.analysis import phase22_common as C  # noqa: E402

IN = C.TABLES / "phase22_regional_intervention_per_image.csv"

OUT_HET = C.AUDITS / "phase22_benefit_heterogeneity.json"
OUT_ACCEPT = C.AUDITS / "phase22_oracle_accept_if_beneficial.json"
OUT_REGRET = C.AUDITS / "phase22_routing_regret.json"
OUT_HARM = C.AUDITS / "phase22_harm_analysis.json"

T_HET = C.TABLES / "phase22_benefit_heterogeneity.csv"
T_ACCEPT = C.TABLES / "phase22_oracle_accept_if_beneficial.csv"
T_REGRET = C.TABLES / "phase22_routing_regret.csv"
T_HARM = C.TABLES / "phase22_harm_analysis.csv"


def _gini(x: np.ndarray) -> float:
    """Gini coefficient of a non-negative array (concentration of benefit)."""
    v = np.sort(np.clip(np.asarray(x, dtype=np.float64), 0, None))
    n = v.size
    if n == 0 or v.sum() == 0:
        return 0.0
    idx = np.arange(1, n + 1)
    return float((2 * (idx * v).sum()) / (n * v.sum()) - (n + 1) / n)


def _deciles(frame: pd.DataFrame, col: str, label: str) -> pd.DataFrame:
    sub = frame.dropna(subset=[col]).copy()
    if len(sub) < 10:
        return pd.DataFrame()
    sub["decile"] = pd.qcut(sub[col].rank(method="first"), 10,
                            labels=[f"D{i:02d}" for i in range(1, 11)])
    out = (sub.groupby("decile", observed=True)
           .agg(n=(col, "size"), mean_delta=("oracle_delta_dice", "mean"),
                sum_delta=("oracle_delta_dice", "sum"),
                n_improved=("oracle_delta_dice", lambda s: int((s > 0).sum())),
                n_worsened=("oracle_delta_dice", lambda s: int((s < 0).sum())),
                mean_value=(col, "mean"))
           .reset_index())
    out.insert(0, "stratified_by", label)
    return out


def main() -> int:
    C.verify_no_test_access()
    df = pd.read_csv(IN)
    n = len(df)
    print(f"loaded {n} regional-intervention rows")

    executed = df[df["oracle_status"] == "OK"].copy()
    no_roi = df[df["oracle_status"] != "OK"]
    pred_no_roi = df[df["predicted_status"] == "NO_PREDICTED_ROI"]

    # ===================================================================== #
    # §15 benefit heterogeneity
    # ===================================================================== #
    d_ok = executed["oracle_delta_dice"].to_numpy()
    d_itt = df["oracle_delta_dice"].to_numpy()
    pos = d_ok[d_ok > 0]

    het_rows = [
        _deciles(executed, "global_dice", "baseline_global_dice"),
        _deciles(executed, "oracle_roi_area_fraction", "roi_area_fraction"),
        _deciles(executed, "gt_foreground_pixels", "gt_foreground_pixels"),
    ]
    het_table = pd.concat([r for r in het_rows if len(r)], ignore_index=True)
    het_table.to_csv(T_HET, index=False)

    per_domain_het = []
    for name in C.DATASET_ORDER:
        s = executed[executed["dataset"] == name]["oracle_delta_dice"]
        per_domain_het.append({
            "dataset": name, "n_executed": int(len(s)),
            "mean_delta": float(s.mean()) if len(s) else float("nan"),
            "median_delta": float(s.median()) if len(s) else float("nan"),
            "sd_delta": float(s.std()) if len(s) else float("nan"),
            "p05_delta": float(s.quantile(0.05)) if len(s) else float("nan"),
            "p95_delta": float(s.quantile(0.95)) if len(s) else float("nan"),
            "n_positive": int((s > 0).sum()), "n_negative": int((s < 0).sum()),
            "share_positive": float((s > 0).mean()) if len(s) else float("nan"),
            "sum_positive": float(s[s > 0].sum()),
            "sum_negative": float(s[s < 0].sum()),
        })
    per_domain_het = pd.DataFrame(per_domain_het)

    # concentration: what share of the total positive benefit the top X% supply
    share_top10 = float(np.sort(pos)[::-1][:max(1, int(0.1 * len(pos)))].sum()
                        / pos.sum()) if len(pos) else float("nan")
    share_top20 = float(np.sort(pos)[::-1][:max(1, int(0.2 * len(pos)))].sum()
                        / pos.sum()) if len(pos) else float("nan")

    r_base = float(np.corrcoef(executed["global_dice"],
                               executed["oracle_delta_dice"])[0, 1]) if len(executed) > 2 else float("nan")
    r_roi = float(np.corrcoef(executed["oracle_roi_area_fraction"],
                              executed["oracle_delta_dice"])[0, 1]) if len(executed) > 2 else float("nan")
    r_gt = float(np.corrcoef(np.log1p(executed["gt_foreground_pixels"]),
                             executed["oracle_delta_dice"])[0, 1]) if len(executed) > 2 else float("nan")

    bt = C.paired_domain_stratified_bootstrap(
        executed["oracle_dice"].to_numpy(), executed["global_dice"].to_numpy(),
        executed["dataset"].to_numpy())
    bt_itt = C.paired_domain_stratified_bootstrap(
        df["oracle_dice"].to_numpy(), df["global_dice"].to_numpy(),
        df["dataset"].to_numpy())

    het_payload = {
        "artifact": "phase22_benefit_heterogeneity",
        "phase": 22,
        "source": "reports/tables/phase22_regional_intervention_per_image.csv",
        "new_inference_performed": False,
        "training_jobs_started": 0,
        "variant": "oracle (GT-defined ROI) — UPPER BOUND, NOT DEPLOYABLE",
        "n_total": int(n), "n_executed": int(len(executed)),
        "n_no_oracle_roi": int(len(no_roi)),
        "gain_distribution_executed": {
            "mean_delta_dice": float(d_ok.mean()),
            "median_delta_dice": float(np.median(d_ok)),
            "sd": float(d_ok.std()),
            "p05": float(np.percentile(d_ok, 5)),
            "p25": float(np.percentile(d_ok, 25)),
            "p75": float(np.percentile(d_ok, 75)),
            "p95": float(np.percentile(d_ok, 95)),
            "min": float(d_ok.min()), "max": float(d_ok.max()),
            "n_positive": int((d_ok > 0).sum()),
            "n_zero": int((d_ok == 0).sum()),
            "n_negative": int((d_ok < 0).sum()),
            "share_positive": float((d_ok > 0).mean()),
        },
        "gain_distribution_intent_to_treat": {
            "mean_delta_dice": float(d_itt.mean()),
            "median_delta_dice": float(np.median(d_itt)),
            "n_positive": int((d_itt > 0).sum()),
            "share_positive": float((d_itt > 0).mean()),
        },
        "concentration": {
            "gini_of_positive_benefit": _gini(pos),
            "share_of_positive_benefit_from_top_10pct_of_benefiting_cases": share_top10,
            "share_of_positive_benefit_from_top_20pct_of_benefiting_cases": share_top20,
            "interpretation": ("a high Gini / high top-share means the regional benefit "
                               "is concentrated in few cases, which is the regime in "
                               "which a router would be valuable"),
        },
        "correlates_of_gain": {
            "pearson_r_baseline_global_dice": r_base,
            "pearson_r_roi_area_fraction": r_roi,
            "pearson_r_log1p_gt_foreground_pixels": r_gt,
            "interpretation": ("a NEGATIVE r with baseline Dice means the regional arm "
                               "helps most where the global model is weakest"),
        },
        "per_domain": per_domain_het.to_dict("records"),
        "paired_bootstrap_executed_subset": bt,
        "paired_bootstrap_intent_to_treat": bt_itt,
        "test_reads": 0,
    }
    C.write_json(OUT_HET, het_payload)

    # ===================================================================== #
    # §16 oracle accept-if-beneficial + §20 routing regret
    # ===================================================================== #
    policy_defs = {
        "ALWAYS_GLOBAL": np.zeros(len(df), dtype=bool),
        "ALWAYS_REGIONAL_ORACLE": np.ones(len(df), dtype=bool),
        "ORACLE_ACCEPT_IF_BENEFICIAL": (df["oracle_delta_dice"] > 0).to_numpy(),
    }
    # deployable-shaped rule-based selectors on PREDICTED information only
    if "predicted_status" in df.columns:
        has_pred_roi = (df["predicted_status"] == "OK").to_numpy()
        policy_defs["PRED_ROI_EXISTS"] = has_pred_roi
        med_base = float(df.loc[df["oracle_status"] == "OK", "global_dice"].median())
        policy_defs["PRED_ROI_EXISTS_AND_BASELINE_BELOW_MEDIAN"] = (
            has_pred_roi & (df["global_dice"] <= med_base).to_numpy())
        pred_pos = (df["predicted_delta_dice"] > 0).to_numpy()
        policy_defs["PRED_ACCEPT_IF_PREDICTED_BENEFICIAL"] = pred_pos

    rows = []
    for name, use in policy_defs.items():
        # When a case is not routed to the regional arm, it keeps the GLOBAL dice.
        value = np.where(use, df["oracle_dice"].to_numpy(), df["global_dice"].to_numpy())
        rows.append({
            "policy": name,
            "uses_ground_truth": name.startswith("ORACLE"),
            "deployable_shape": not name.startswith("ORACLE"),
            "n_routed_to_regional": int(use.sum()),
            "fraction_routed_to_regional": round(float(use.mean()), 6),
            "macroR_dice_pooled": float(value.mean()),
            "mean_dice_executed_only": float(value[use].mean()) if use.any() else float("nan"),
            "improvement_over_always_global": float(value.mean() - df["global_dice"].mean()),
            "change_vs_always_regional": float(value.mean() - df["oracle_dice"].mean()),
        })
    pol = pd.DataFrame(rows)
    ceiling = float(pol.loc[pol.policy == "ORACLE_ACCEPT_IF_BENEFICIAL",
                            "macroR_dice_pooled"].iloc[0])
    pol["regret_vs_oracle_ceiling"] = (ceiling - pol["macroR_dice_pooled"]).round(8)
    pol.to_csv(T_REGRET, index=False)

    accept = pol[pol.policy == "ORACLE_ACCEPT_IF_BENEFICIAL"].iloc[0].to_dict()
    C.write_json(OUT_ACCEPT, {
        "artifact": "phase22_oracle_accept_if_beneficial",
        "phase": 22,
        "definition": ("a PERFECT selector applies the regional arm only where it "
                       "strictly improves Dice, and keeps the global map elsewhere"),
        "is_an_upper_bound": True,
        "is_deployable": False,
        "uses_ground_truth": True,
        "n_total": int(n),
        "n_accepted": int((df["oracle_delta_dice"] > 0).sum()),
        "acceptance_rate": round(float((df["oracle_delta_dice"] > 0).mean()), 6),
        "baseline_always_global_pooled_dice": float(df["global_dice"].mean()),
        "baseline_always_regional_pooled_dice": float(df["oracle_dice"].mean()),
        "oracle_ceiling_pooled_dice": ceiling,
        "ceiling_gain_over_always_global": float(
            ceiling - df["global_dice"].mean()),
        "ceiling_gain_over_always_regional": float(
            ceiling - df["oracle_dice"].mean()),
        "forbidden_claim": ("this is the ceiling of ANY routing policy. It is not an "
                            "achieved result and no deployable method may be described "
                            "as attaining it."),
        "test_reads": 0,
    })

    C.write_json(OUT_REGRET, {
        "artifact": "phase22_routing_regret",
        "phase": 22,
        "regret_definition": "oracle_accept_if_beneficial pooled Dice minus policy pooled Dice",
        "oracle_ceiling_pooled_dice": ceiling,
        "policies": pol.to_dict("records"),
        "notes": [
            "policies flagged deployable_shape use ONLY predicted information, "
            "never the ground truth",
            "no selector was TRAINED; these are fixed rules evaluated offline",
            "the predicted-beneficial rule inherits the global model's errors, "
            "which is exactly why its regret is informative",
            "CRITICAL CAVEAT: every policy here, including PRED_ACCEPT_IF_PREDICTED_"
            "BENEFICIAL, is EVALUATED ON THE SAME VAL POPULATION IT WAS INSPECTED ON. "
            "Its regret is therefore a POST-HOC, optimistically-biased quantity, NOT an "
            "out-of-sample estimate. No policy may be reported as a generalisable "
            "achieved result; establishing that would require a held-out protocol and "
            "training, both of which Phase 22 forbids.",
        ],
        "test_reads": 0,
    })

    # ===================================================================== #
    # §22 harm analysis
    # ===================================================================== #
    harmed = executed[executed["oracle_delta_dice"] < 0].copy()
    harmed = harmed.sort_values("oracle_delta_dice")
    harmed.to_csv(T_HARM, index=False)

    harm_by_domain = []
    for name in C.DATASET_ORDER:
        s = executed[executed["dataset"] == name]
        h = s[s["oracle_delta_dice"] < 0]
        harm_by_domain.append({
            "dataset": name, "n_executed": int(len(s)),
            "n_harmed": int(len(h)),
            "harm_rate": round(float(len(h) / len(s)), 6) if len(s) else float("nan"),
            "mean_harm": float(h["oracle_delta_dice"].mean()) if len(h) else 0.0,
            "worst_harm": float(h["oracle_delta_dice"].min()) if len(h) else 0.0,
            "total_harm": float(h["oracle_delta_dice"].sum()),
        })

    harm_payload = {
        "artifact": "phase22_harm_analysis",
        "phase": 22,
        "variant": "oracle (GT-defined ROI)",
        "definition": "a case is HARMED when applying the regional arm reduces Dice",
        "n_executed": int(len(executed)),
        "n_harmed": int(len(harmed)),
        "harm_rate_among_executed": round(float(len(harmed) / max(1, len(executed))), 6),
        "n_harmed_intent_to_treat": int((df["oracle_delta_dice"] < 0).sum()),
        "harm_rate_intent_to_treat": round(float((df["oracle_delta_dice"] < 0).mean()), 6),
        "mean_harm": float(harmed["oracle_delta_dice"].mean()) if len(harmed) else 0.0,
        "median_harm": float(harmed["oracle_delta_dice"].median()) if len(harmed) else 0.0,
        "worst_harm": float(harmed["oracle_delta_dice"].min()) if len(harmed) else 0.0,
        "p05_harm": float(harmed["oracle_delta_dice"].quantile(0.05)) if len(harmed) else 0.0,
        "total_harm_magnitude": float(harmed["oracle_delta_dice"].sum()),
        "net_gain_executed": float(executed["oracle_delta_dice"].sum()),
        "harm_by_domain": harm_by_domain,
        "worst_cases": harmed.head(15)[[
            "sample_id", "dataset", "global_dice", "oracle_dice", "oracle_delta_dice",
            "oracle_roi_area_fraction", "gt_foreground_pixels"]].to_dict("records"),
        "interpretation": ("harm concentrates where the ROI crop removes necessary "
                           "global context, or where the regional pass re-segments "
                           "background as foreground"),
        "test_reads": 0,
    }
    C.write_json(OUT_HARM, harm_payload)

    # ---- print --------------------------------------------------------- #
    print("\n--- §15 benefit heterogeneity (oracle, executed) ---")
    print(f"  n_executed={len(executed)}  mean_delta={d_ok.mean():+.6f}  "
          f"median={np.median(d_ok):+.6f}  positive={int((d_ok>0).sum())} "
          f" negative={int((d_ok<0).sum())}")
    print(f"  ITT mean_delta={d_itt.mean():+.6f}  positive={int((d_itt>0).sum())}")
    print(f"  gini={_gini(pos):.4f}  top10%_share={share_top10:.4f}")
    print(f"  r(baseline Dice)={r_base:+.4f}  r(ROI area)={r_roi:+.4f}")
    print("\n--- §16 oracle accept-if-beneficial ceiling ---")
    n_accepted = int((df["oracle_delta_dice"] > 0).sum())
    print(f"  acceptance rate={n_accepted / len(df):.4f}  (n_accepted={n_accepted})")
    print(f"  always_global={df['global_dice'].mean():.6f}  "
          f"always_regional={df['oracle_dice'].mean():.6f}  "
          f"ceiling={ceiling:.6f}")
    print(f"  ceiling gain over always-global={ceiling - df['global_dice'].mean():+.6f}")
    print("\n--- §20 routing regret ---")
    print(pol[["policy", "deployable_shape", "fraction_routed_to_regional",
               "macroR_dice_pooled", "regret_vs_oracle_ceiling"]].to_string(index=False))
    print("\n--- §22 harm ---")
    print(f"  harmed={len(harmed)}/{len(executed)}  worst={harm_payload['worst_harm']:+.6f}  "
          f"total_harm={harm_payload['total_harm_magnitude']:+.6f}")
    print(f"\nWROTE {OUT_HET}, {OUT_ACCEPT}, {OUT_REGRET}, {OUT_HARM}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
