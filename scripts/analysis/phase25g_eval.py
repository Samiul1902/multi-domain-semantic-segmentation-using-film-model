"""Phase25G evaluation module - the single source of truth for every Phase25G number.

Both the driver (run_phase25g_part2_eval.py) and the reviewer notebook call
``compute_all()`` so their outputs are byte-identical.

ARTIFACT-LEVEL EVALUATION ONLY - no model, no forward pass.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import phase25g_common as C

PUBLIC_METRIC_KEYS = [
    "n", "selected_count", "executed_count", "activation_fraction",
    "A7_mean_dice", "A7_delta_vs_global", "A7_macro_domain_mean_dice",
    "A7_macro_domain_delta_vs_global", "A7_harmful_replacement_count",
    "A7_harmful_replacement_rate", "A7_fallback_count", "A7_fallback_rate",
    "A8_mean_dice", "A8_delta_vs_global", "A8_macro_domain_mean_dice",
    "A8_macro_domain_delta_vs_global", "A8_harmful_replacement_count",
    "A8_harmful_replacement_rate", "A8_fallback_count", "A8_fallback_rate",
    "A8_accept_count", "A8_accept_rate_among_executed",
    "A8_reject_count", "A8_reject_rate_among_executed", "A8_skip_count",
    "A8_minus_A7", "A8_minus_A7_macro_domain", "harm_prevented",
    "A7_harmful_replacement_rate_minus_A8",
    "A7_avg_analytical_macs", "A8_avg_analytical_macs", "A8_minus_A7_macs",
]

# bootstrap metric keys (per unique budget membership)
BOOT_KEYS = (["A7_delta", "A8_delta", "A8mA7", "A7_macro", "A8_macro", "A8mA7_macro",
              "A7_dice", "A8_dice", "A7_harm_rate", "A8_harm_rate", "A7_harm_count",
              "A8_harm_count", "harm_prevented_count", "harm_prevented_rate",
              "A8_accept_rate", "A8_reject_rate", "A7_fallback_rate", "A8_fallback_rate",
              "A7_harm_rate_minus_A8"]
             + [f"A7_dom_{d}" for d in C.STRATA] + [f"A8_dom_{d}" for d in C.STRATA])


def _replicate_metrics(sel_r, acc_r, d_r, dom_r):
    a7 = np.where(sel_r, d_r, 0.0)
    a8 = np.where(acc_r, d_r, 0.0)
    K = int(sel_r.sum())
    out = {
        "A7_delta": float(a7.mean()),
        "A8_delta": float(a8.mean()),
        "A7_dice": float(a7.mean()),
        "A8_dice": float(a8.mean()),
        "A7_harm_count": int((sel_r & (d_r < 0)).sum()),
        "A8_harm_count": int((acc_r & (d_r < 0)).sum()),
        "harm_prevented_count": int(((~acc_r) & sel_r & (d_r < 0)).sum()),
    }
    out["A8mA7"] = out["A8_delta"] - out["A7_delta"]
    a7d, a8d = [], []
    for dd in C.STRATA:
        m = dom_r[dd]
        a7d.append(float(a7[m].mean()))
        a8d.append(float(a8[m].mean()))
        out[f"A7_dom_{dd}"] = a7d[-1]
        out[f"A8_dom_{dd}"] = a8d[-1]
    out["A7_macro"] = float(np.mean(a7d))
    out["A8_macro"] = float(np.mean(a8d))
    out["A8mA7_macro"] = out["A8_macro"] - out["A7_macro"]
    if K == 0:
        for k in ("A7_harm_rate", "A8_harm_rate", "harm_prevented_rate",
                  "A8_accept_rate", "A8_reject_rate", "A7_fallback_rate",
                  "A8_fallback_rate", "A7_harm_rate_minus_A8"):
            out[k] = np.nan
    else:
        out["A7_harm_rate"] = out["A7_harm_count"] / K
        out["A8_harm_rate"] = out["A8_harm_count"] / K
        out["harm_prevented_rate"] = out["harm_prevented_count"] / K
        out["A8_accept_rate"] = float(acc_r.sum()) / K
        out["A8_reject_rate"] = float((sel_r & ~acc_r).sum()) / K
        out["A7_fallback_rate"] = 0.0
        out["A8_fallback_rate"] = out["A8_reject_rate"]
        out["A7_harm_rate_minus_A8"] = out["A7_harm_rate"] - out["A8_harm_rate"]
    return out


def run_bootstrap(pol, c9, lab, dom_idx):
    """Replay the EXACT frozen Phase25E draws for the 5 unique budget memberships."""
    d = lab.delta_dice.to_numpy(np.float64)
    ids = lab.sample_id.tolist()
    csr, _ = C.build_group_index(ids)
    plan = C.load_plan()
    per_budget = {}
    for b in C.BUDGETS:
        pid0 = C.policy_id("0.00", b)
        score = pol[pid0]["score"]
        action_available = pol[pid0]["action_available"]
        accept_full = c9[pid0]["c9_outcome"] == "EXECUTE_THEN_ACCEPT"
        arr = {k: np.full(C.N_BOOT, np.nan) for k in BOOT_KEYS}
        for b_i, idx in C.iter_bootstrap_indices(csr, plan):
            # Phase25E contract: the budget is a fraction of the REPLICATE ELIGIBLE count
            # (action-available rows), not of the budget-specific selected subset.
            n_elig_rep = int(action_available[idx].sum())
            bud = float(b)
            k_rep = n_elig_rep if bud == 1.0 else int(np.floor(bud * n_elig_rep))
            sel_r = C.replicate_select(score, idx, k_rep)
            # A8 executes the replicate-selected candidates and accepts those that the frozen
            # per-sample S_omega decision accepts -> accept is a subset of the replicate selection.
            acc_r = sel_r & accept_full[idx]
            dom_r = {dd: dom_idx[dd][idx] for dd in C.STRATA}
            m = _replicate_metrics(sel_r, acc_r, d[idx], dom_r)
            for k in BOOT_KEYS:
                arr[k][b_i] = m[k]
        per_budget[b] = arr
    return per_budget


def compute_all():
    lab = C.load_labels()
    ids = C.canonical_ids(lab)
    man, pol = C.load_c8_memberships(ids)
    c9df, c9 = C.load_c9(ids)
    dom_idx = {d: (lab.domain.to_numpy() == d) for d in C.STRATA}

    point = {pid: C.point_policy_metrics(pid, pol[pid], c9[pid], lab, dom_idx) for pid in pol}
    boot = run_bootstrap(pol, c9, lab, dom_idx)
    boot_ci = {}
    for b, arr in boot.items():
        boot_ci[b] = {k: C.ci(v) for k, v in arr.items()}

    return {"lab": lab, "ids": ids, "man": man, "pol": pol, "c9df": c9df, "c9": c9,
            "dom_idx": dom_idx, "point": point, "boot": boot, "boot_ci": boot_ci}


# ------------------------------------------------------------------ table builders
def policy_metrics_rows(point):
    order = [C.policy_id(l, b) for b in C.BUDGETS for l in C.LAMBDAS]
    rows = []
    for pid in order:
        r = point[pid]
        row = {"policy_id": pid, "lambda": r["lambda"], "budget": r["budget"],
               "membership_equivalence_group": r["membership_equivalence_group"]}
        for k in PUBLIC_METRIC_KEYS:
            row[k] = r[k]
        rows.append(row)
    return rows


def comparison_rows(point):
    order = [C.policy_id(l, b) for b in C.BUDGETS for l in C.LAMBDAS]
    fields = ["policy_id", "lambda", "budget", "membership_equivalence_group", "n",
              "selected_count", "A7_mean_dice", "A8_mean_dice", "A7_delta_vs_global",
              "A8_delta_vs_global", "A8_minus_A7", "A7_harmful_replacement_count",
              "A8_harmful_replacement_count", "harm_prevented", "A8_accept_count",
              "A8_reject_count", "A7_avg_analytical_macs", "A8_avg_analytical_macs"]
    return [{k: point[pid][k] for k in fields} for pid in order]


def domain_rows(point):
    rows = []
    for b in C.BUDGETS:
        for l in C.LAMBDAS:
            pid = C.policy_id(l, b)
            r = point[pid]
            for dd in C.STRATA:
                g_dom = r["_global_dom"][dd]
                rows.append({
                    "policy_id": pid, "lambda": l, "budget": b, "domain": dd,
                    "n": r["_domain_n"][dd],
                    "executed": r["_sel_dom"][dd],
                    "accepted": r["_acc_dom"][dd],
                    "rejected": r["_rej_dom"][dd],
                    "A7_mean_dice_domain": g_dom + r["_a7_dom"][dd],
                    "A8_mean_dice_domain": g_dom + r["_a8_dom"][dd],
                    "A7_delta_vs_global_domain": r["_a7_dom"][dd],
                    "A8_delta_vs_global_domain": r["_a8_dom"][dd],
                    "A8_minus_A7_domain": r["_a8_dom"][dd] - r["_a7_dom"][dd],
                    "A7_harmful_replacements_domain": r["_a7_harm_dom"][dd],
                    "A8_harmful_replacements_domain": r["_a8_harm_dom"][dd],
                    "harm_prevented_domain": r["_a7_harm_dom"][dd] - r["_a8_harm_dom"][dd],
                })
    return rows


# ------------------------------------------------------- §13 / §18 accounting
def rejection_rows(point, lab, pol, c9, unique_only=True):
    """Per unique budget: executed / accepted / rejected / skip + rejected delta & category split."""
    d = lab.delta_dice.to_numpy(np.float64)
    cat = lab.gain_category.to_numpy()
    rows = []
    budgets = C.BUDGETS
    for b in budgets:
        pid = C.policy_id("0.00", b)
        sel = pol[pid]["selected"]
        out = c9[pid]["c9_outcome"]
        accept = out == "EXECUTE_THEN_ACCEPT"
        reject = out == "EXECUTE_THEN_REJECT"
        skip = out == "PRE_GATE_SKIP"
        rej_d = d[reject]
        rej_cat = cat[reject]
        rows.append({
            "budget": b, "budget_label": C.BUDGET_LABEL[b],
            "membership_equivalence_group": b,
            "executed_count": int(sel.sum()),
            "accepted_count": int(accept.sum()),
            "rejected_count": int(reject.sum()),
            "skip_count": int(skip.sum()),
            "rejected_delta_neg": int((rej_d < 0).sum()),
            "rejected_delta_zero": int((rej_d == 0).sum()),
            "rejected_delta_pos": int((rej_d > 0).sum()),
            "rejected_cat_beneficial": int((rej_cat == "BENEFICIAL").sum()),
            "rejected_cat_neutral": int((rej_cat == "NEUTRAL").sum()),
            "rejected_cat_harmful": int((rej_cat == "HARMFUL").sum()),
            "undefined_metrics": "UNDEFINED_ZERO_DENOMINATOR" if int(sel.sum()) == 0 else "",
        })
    return rows


def tradeoff_rows(point, lab, pol, c9):
    """§18: benefit recovered vs sacrificed by S_omega, with identity cross-check."""
    d = lab.delta_dice.to_numpy(np.float64)
    rows = []
    for b in C.BUDGETS:
        pid = C.policy_id("0.00", b)
        sel = pol[pid]["selected"]
        out = c9[pid]["c9_outcome"]
        reject = out == "EXECUTE_THEN_REJECT"
        r_neg = reject & (d < 0)
        r_zero = reject & (d == 0)
        r_pos = reject & (d > 0)
        recovered = float(-d[r_neg].sum())
        sacrificed = float(d[r_pos].sum())
        a7 = np.where(sel, d, 0.0)
        a8 = np.where(out == "EXECUTE_THEN_ACCEPT", d, 0.0)
        net_identity = float((a8 - a7).sum())
        rows.append({
            "budget": b, "budget_label": C.BUDGET_LABEL[b],
            "rejected_negative_gain": int(r_neg.sum()),
            "rejected_positive_gain": int(r_pos.sum()),
            "rejected_zero_gain": int(r_zero.sum()),
            "benefit_recovered": recovered,
            "benefit_sacrificed": sacrificed,
            "net_post_safety_effect": recovered - sacrificed,
            "sum_A8_minus_A7_identity": net_identity,
            "identity_abs_diff": abs((recovered - sacrificed) - net_identity),
        })
    return rows


def compute_rows(point):
    rows = []
    for b in C.BUDGETS:
        for l in C.LAMBDAS:
            pid = C.policy_id(l, b)
            r = point[pid]
            a = r["activation_fraction"]
            rows.append({
                "policy_id": pid, "lambda": l, "budget": b,
                "activation_fraction": a,
                "A7_avg_analytical_macs": C.GLOBAL_MACS + C.ROUTER_MACS + a * C.REFINER_MACS,
                "A8_avg_analytical_macs": C.GLOBAL_MACS + C.ROUTER_MACS + a * (C.REFINER_MACS + C.SOMEGA_MACS),
                "A8_minus_A7_macs": a * C.SOMEGA_MACS,
                "ratio_A7_vs_global": (C.GLOBAL_MACS + C.ROUTER_MACS + a * C.REFINER_MACS) / C.GLOBAL_MACS,
                "accounting_label": C.ACCOUNTING_LABEL,
                "somega_saves_compute": False,
            })
    return rows

