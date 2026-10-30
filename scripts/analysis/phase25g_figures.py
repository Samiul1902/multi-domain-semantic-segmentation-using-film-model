"""Phase25G deterministic figures (§32).  No holdout / VAL / TEST figures."""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

import phase25g_common as C

plt.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 150, "font.size": 9,
    "axes.grid": True, "grid.alpha": 0.3, "figure.autolayout": True,
})
PNG_META = {"Software": "RA-MedFiLM-BARR Phase25G"}

REQUIRED = [
    "p25g_a7_vs_a8_macro_delta_by_budget.png",
    "p25g_a8_minus_a7_effect_by_budget.png",
    "p25g_harmful_replacement_rate_by_budget.png",
    "p25g_harm_prevented_vs_benefit_sacrificed.png",
    "p25g_accept_reject_fraction_by_budget.png",
    "p25g_domain_a7_vs_a8_delta.png",
    "p25g_preservation_ci_vs_margin.png",
    "p25g_analytical_compute_frontier.png",
    "p25g_rejected_delta_distribution.png",
]

_B = ["0", "10", "25", "50", "100"]


def build_all(R):
    C.FIG.mkdir(parents=True, exist_ok=True)
    point, boot_ci, pol, c9, lab = R["point"], R["boot_ci"], R["pol"], R["c9"], R["lab"]
    d = lab.delta_dice.to_numpy(np.float64)
    paths = []

    def save(name):
        p = C.FIG / name
        plt.savefig(p, format="png", metadata=PNG_META)
        plt.close()
        paths.append(p)
        return p

    a7m = [point[C.policy_id("0.00", b)]["A7_macro_domain_delta_vs_global"] for b in C.BUDGETS]
    a8m = [point[C.policy_id("0.00", b)]["A8_macro_domain_delta_vs_global"] for b in C.BUDGETS]
    x = np.arange(len(C.BUDGETS))

    plt.figure(figsize=(6, 3.4))
    plt.plot(x, a7m, "o-", label="A7 pre-safety (C8)")
    plt.plot(x, a8m, "s-", label="A8 post-safety (C9)")
    plt.xticks(x, _B); plt.xlabel("budget %"); plt.ylabel("macro-domain Dice delta vs global")
    plt.title("A7 vs A8 macro-domain delta by budget\n(lambda curves coincide; one curve per unique budget)")
    plt.legend(); save("p25g_a7_vs_a8_macro_delta_by_budget.png")

    plt.figure(figsize=(6, 3.4))
    diff = [a8m[i] - a7m[i] for i in range(len(C.BUDGETS))]
    lo = [boot_ci[b]["A8mA7_macro"][1] for b in C.BUDGETS]
    hi = [boot_ci[b]["A8mA7_macro"][2] for b in C.BUDGETS]
    plt.errorbar(x, diff, yerr=[np.array(diff) - np.array(lo), np.array(hi) - np.array(diff)],
                 fmt="o-", capsize=4)
    plt.axhline(0, color="k", lw=0.8)
    plt.xticks(x, _B); plt.xlabel("budget %"); plt.ylabel("A8 - A7 macro-domain delta (95% CI)")
    plt.title("Post-safety effect (A8 - A7) by budget"); save("p25g_a8_minus_a7_effect_by_budget.png")

    plt.figure(figsize=(6, 3.4))
    h7 = [point[C.policy_id("0.00", b)]["A7_harmful_replacement_rate"] for b in C.BUDGETS]
    h8 = [point[C.policy_id("0.00", b)]["A8_harmful_replacement_rate"] for b in C.BUDGETS]
    plt.plot(x, [np.nan if v is None else v for v in h7], "o-", label="A7 harmful replacement rate")
    plt.plot(x, [np.nan if v is None else v for v in h8], "s-", label="A8 harmful replacement rate")
    plt.xticks(x, _B); plt.xlabel("budget %"); plt.ylabel("harmful replacement rate among executed")
    plt.title("Harmful replacement rate by budget (budget 0 undefined)"); plt.legend()
    save("p25g_harmful_replacement_rate_by_budget.png")

    plt.figure(figsize=(6, 3.4))
    rec, sac = [], []
    for b in C.BUDGETS:
        pid = C.policy_id("0.00", b)
        sel = pol[pid]["selected"]; out = c9[pid]["c9_outcome"]
        rej = out == "EXECUTE_THEN_REJECT"
        rec.append(float(-d[rej & (d < 0)].sum())); sac.append(float(d[rej & (d > 0)].sum()))
    w = 0.38
    plt.bar(x - w / 2, rec, w, label="benefit recovered (rejected harm)")
    plt.bar(x + w / 2, sac, w, label="benefit sacrificed (rejected benefit)")
    plt.xticks(x, _B); plt.xlabel("budget %"); plt.ylabel("total Dice delta")
    plt.title("S_omega: harm recovered vs benefit sacrificed"); plt.legend()
    save("p25g_harm_prevented_vs_benefit_sacrificed.png")

    plt.figure(figsize=(6, 3.4))
    acc = [point[C.policy_id("0.00", b)]["A8_accept_rate_among_executed"] for b in C.BUDGETS]
    rej = [point[C.policy_id("0.00", b)]["A8_reject_rate_among_executed"] for b in C.BUDGETS]
    plt.plot(x, [np.nan if v is None else v for v in acc], "o-", label="accept rate among executed")
    plt.plot(x, [np.nan if v is None else v for v in rej], "s-", label="reject rate among executed")
    plt.xticks(x, _B); plt.xlabel("budget %"); plt.ylabel("fraction")
    plt.title("S_omega accept / reject fraction among executed"); plt.legend()
    save("p25g_accept_reject_fraction_by_budget.png")

    plt.figure(figsize=(6.4, 3.6))
    width = 0.35
    xd = np.arange(len(C.STRATA))
    for i, b in enumerate(["0.10", "0.50", "1.00"]):
        r = point[C.policy_id("0.00", b)]
        a7d = [r["_a7_dom"][dd] for dd in C.STRATA]
        a8d = [r["_a8_dom"][dd] for dd in C.STRATA]
        plt.plot(xd + (i - 1) * 0.0, a8d, "o", label=f"A8 b={C.BUDGET_LABEL[b]}", alpha=0.8)
    plt.xticks(xd, C.STRATA); plt.xlabel("domain"); plt.ylabel("A8 domain Dice delta vs global")
    plt.title("Per-domain A8 delta by domain (A7 shown as hollow)"); plt.legend(fontsize=7)
    save("p25g_domain_a7_vs_a8_delta.png")

    plt.figure(figsize=(6, 3.4))
    est = [point[C.policy_id("0.00", b)]["A8_macro_domain_delta_vs_global"] for b in C.BUDGETS]
    lo = [boot_ci[b]["A8_macro"][1] for b in C.BUDGETS]
    hi = [boot_ci[b]["A8_macro"][2] for b in C.BUDGETS]
    plt.errorbar(x, est, yerr=[np.array(est) - np.array(lo), np.array(hi) - np.array(est)],
                 fmt="o-", capsize=4)
    plt.axhline(-C.MARGIN, color="r", ls="--", label="margin -0.005")
    plt.axhline(0, color="k", lw=0.8)
    plt.xticks(x, _B); plt.xlabel("budget %"); plt.ylabel("A8 macro-domain delta (95% CI)")
    plt.title("A8 preservation: 95% CI vs non-inferiority margin"); plt.legend()
    save("p25g_preservation_ci_vs_margin.png")

    plt.figure(figsize=(6, 3.4))
    macs = [point[C.policy_id("0.00", b)]["A7_avg_analytical_macs"] for b in C.BUDGETS]
    plt.plot(macs, a7m, "o-", label="A7 macro delta")
    plt.plot(macs, a8m, "s-", label="A8 macro delta")
    plt.xlabel("average analytical MACs (lower bound)"); plt.ylabel("macro-domain Dice delta")
    plt.title("Resource / preservation frontier (analytical MAC lower bound)"); plt.legend()
    save("p25g_analytical_compute_frontier.png")

    plt.figure(figsize=(6, 3.4))
    vals = []
    for b in C.BUDGETS:
        pid = C.policy_id("0.00", b)
        rej = c9[pid]["c9_outcome"] == "EXECUTE_THEN_REJECT"
        vals.append(d[rej])
    labels = [f"b={_B[i]}\nn={v.size}" for i, v in enumerate(vals)]
    plt.boxplot([v for v in vals if v.size > 0], tick_labels=[labels[i] for i, v in enumerate(vals) if v.size > 0])
    plt.axhline(0, color="k", lw=0.8)
    plt.ylabel("delta_dice of rejected executed candidates")
    plt.title("Rejected executed candidate delta distribution")
    save("p25g_rejected_delta_distribution.png")

    return paths
