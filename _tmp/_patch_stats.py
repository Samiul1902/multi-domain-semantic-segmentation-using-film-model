import pathlib

p = pathlib.Path(r"D:\Softfors\jup\full_doc_report\Scripts\build_figures.py")
s = p.read_text(encoding="utf-8")

block = '''# =============================================================== statistics ====
def fig_statistics() -> None:
    """Reproducibility and inferential statistics from frozen Phase 29 evidence."""
    d29 = jload(ROOT / "reports/audits/phase29_phase_d_three_seed_descriptive_summary.json")
    per = {m["metric"]: m for m in d29["per_metric"]}
    seeds = ["42", "123", "3407"]

    # STAT01 — seed-wise macro Dice and delta
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.6))
    for ax, key, title, col in (
            (axes[0], "macro_final_dice", "Macro-domain VAL808 Dice", BLUE),
            (axes[1], "macro_delta_dice", "Macro Δ Dice vs backbone", VERM)):
        m = per[key]
        vals = [m[f"seed{x}"] for x in seeds]
        ax.bar(range(3), vals, color=col, width=0.5, alpha=0.85)
        mean, sd = m["mean"], m["sample_sd_ddof1"]
        ax.axhline(mean, color="#333333", linewidth=0.9, linestyle="--")
        ax.fill_between([-0.6, 2.6], mean - sd, mean + sd, color=col, alpha=0.12)
        for i, v in enumerate(vals):
            ax.text(i, v, f"{v:.6f}", ha="center", va="bottom", fontsize=6.0)
        ax.set_xticks(range(3))
        ax.set_xticklabels([f"seed {x}" for x in seeds])
        ax.set_title(title)
        ax.grid(axis="x", visible=False)
        lo = min(vals) - abs(mean) * 0.35 if mean else min(vals) * 0.9
        ax.set_ylim(lo, max(vals) + abs(mean) * 0.45)
        ax.text(0.02, 0.05, f"mean {mean:.6f}\\nSD {sd:.2e}", transform=ax.transAxes,
                fontsize=6.0, va="bottom", color=GREY)
    fig.suptitle("Three downstream seeds — descriptive only, shared frozen backbone",
                 fontsize=8.5, y=1.03)
    save(fig, "statistics", "STAT01_seedwise_macro_metrics",
         "FROZEN_PHASE29_DESCRIPTIVE",
         "Per-seed macro Dice and Δ Dice with the across-seed mean and SD band. "
         "The backbone is identical across seeds, so this is not end-to-end replication.",
         "09", ["reports/audits/phase29_phase_d_three_seed_descriptive_summary.json"])

    # STAT02 — bootstrap distribution of the paired macro delta
    pd_ = jload(TABLES / "REMEDFILM_PAIRED_DELTA.json")
    hist = pd_.get("bootstrap_hist")
    fig, ax = plt.subplots(figsize=(5.4, 2.6))
    if hist:
        edges = np.array(hist["bin_edges"])
        counts = np.array(hist["counts"])
        centers = (edges[:-1] + edges[1:]) / 2
        width = edges[1] - edges[0]
        ax.bar(centers, counts, width=width, color=SKY, edgecolor="white", linewidth=0.3)
    ax.axvline(pd_["point"], color=VERM, linewidth=1.4, label=f"point {pd_['point']:+.5f}")
    for v, lab in ((pd_["ci_low"], "2.5%"), (pd_["ci_high"], "97.5%")):
        ax.axvline(v, color="#333333", linewidth=0.9, linestyle="--")
        ax.text(v, ax.get_ylim()[1] * 0.92, f" {lab}", fontsize=6, color="#333333")
    ax.axvline(0, color="#999999", linewidth=0.8, linestyle=":")
    ax.set_xlabel("Macro Δ Dice (ReMedFiLM FULL − GlobalMedFiLM)")
    ax.set_ylabel("Bootstrap replicates")
    ax.set_title(f"Domain-stratified bootstrap, B = {pd_['n_boot']:,}, seed {pd_['seed']}")
    ax.legend(loc="upper left", fontsize=6.5)
    save(fig, "statistics", "STAT02_bootstrap_distribution",
         "DERIVED_FROM_SAVED_PREDICTIONS",
         "Empirical bootstrap distribution of the paired macro Δ Dice on VAL808; "
         "the whole distribution lies above zero.",
         "09", ["full_doc_report/tables/REMEDFILM_PAIRED_DELTA.json"])

    # STAT03 — per-domain Dice by seed
    d29v = jload(ROOT / "reports/audits/phase29_val808_seedwise_metrics.json")
    by_seed = d29v["metrics_by_seed"]
    doms = ["ISIC", "BUSI", "KVASIR", "KUB"]
    fig, ax = plt.subplots(figsize=(6.2, 2.6))
    w = 0.24
    for i, sd_ in enumerate(seeds):
        vals = [by_seed[sd_]["per_domain"][d]["final_dice"] for d in doms]
        ax.bar(np.arange(4) + (i - 1) * w, vals, w, label=f"seed {sd_}",
               color=[BLUE, ORANGE, PURPLE][i])
    ax.set_xticks(range(4))
    ax.set_xticklabels(doms)
    ax.set_ylabel("ReMedFiLM FULL Dice")
    ax.set_ylim(0.70, 0.95)
    ax.set_title("Per-domain FULL-system Dice across the three downstream seeds")
    ax.legend(ncol=3, fontsize=6.5)
    ax.grid(axis="x", visible=False)
    save(fig, "statistics", "STAT03_seedwise_per_domain",
         "FROZEN_PHASE29_DESCRIPTIVE",
         "Per-domain FULL-system Dice for seeds 42/123/3407. Variation is confined "
         "to the re-fitted components, not the backbone.",
         "09", ["reports/audits/phase29_val808_seedwise_metrics.json"])

    # STAT04 — population accounting
    fig, ax = plt.subplots(figsize=(6.0, 2.3))
    labels = ["TRAIN\\n5,832", "ROUTER_DEV\\n4,957", "ROUTER_HOLDOUT\\n875",
              "VAL\\n808", "TEST\\n1,683\\n(consumed)"]
    vals = [5832, 4957, 875, 808, 1683]
    cols = [BLUE, SKY, GREEN, ORANGE, LGREY]
    bars = ax.bar(labels, vals, color=cols, width=0.62)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 60, f"{v:,}", ha="center", fontsize=6.8)
    ax.set_ylabel("Images")
    ax.set_ylim(0, 6600)
    ax.set_title("Population accounting — which cohort each result belongs to")
    ax.grid(axis="x", visible=False)
    ax.text(0.015, 0.90, "TRAIN splits exactly into ROUTER_DEV + ROUTER_HOLDOUT",
            transform=ax.transAxes, fontsize=6.2, color=GREY)
    save(fig, "statistics", "STAT04_population_accounting",
         "FROZEN_MANIFEST",
         "Every reported metric is tied to one of these cohorts; they are never pooled.",
         "02", ["manifests/phase4_v3/train.csv", "manifests/phase4_v3/val.csv",
                "reports/audits/phase25g_holdout_reservation_for_phase30.json"])


def main() -> None:'''

s = s.replace("\ndef main() -> None:", "\n" + block, 1)
s = s.replace("    fig_efficiency()\n", "    fig_efficiency()\n    fig_statistics()\n", 1)
p.write_text(s, encoding="utf-8")
print("PATCHED statistics")
