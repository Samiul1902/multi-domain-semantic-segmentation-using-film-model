"""Phase 25C -- descriptive tables (§22) + deterministic figures (§23) + fixed gallery.

All outputs are deterministic pure functions of the frozen label table.
The qualitative gallery selection is fixed by a stable sample-id rule and is
computed WITHOUT inspecting DeltaDice (the same selection is used regardless of
the outcome distribution).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))
CODE = ROOT / "notebooks" / "phasewise" / "phase_25c_paired_gain_labels" / "code"
sys.path.insert(0, str(CODE))
import phase25c_common as C  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
FIG = ROOT / "reports" / "figures" / "phase25c_paired_gain_labels"
UTC = "2026-09-30T17:12:00+00:00"

DOMAIN_COLORS = {"BUSI": "#4C72B0", "ISIC": "#DD8452", "KUB": "#55A868", "KVASIR": "#C44E52"}


def _summary(series: pd.Series) -> dict:
    s = series.astype(float)
    return {
        "n": int(s.count()),
        "mean": float(s.mean()),
        "median": float(s.median()),
        "std": float(s.std(ddof=1)),
        "iqr": float(s.quantile(0.75) - s.quantile(0.25)),
        "p05": float(s.quantile(0.05)),
        "p95": float(s.quantile(0.95)),
        "min": float(s.min()),
        "max": float(s.max()),
    }


def main() -> int:
    TAB.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    lab = pd.read_csv(C.LABEL_CSV)
    dev = C.load_development()

    # ---------- §22 population accounting ---------------------------------- #
    pop = pd.DataFrame([
        {"population": "ROUTER_DEVELOPMENT", "n": 4957},
        {"population": "action_available", "n": int(lab["action_available"].sum())},
        {"population": "action_unavailable", "n": 0},
        {"population": "labeled_rows", "n": len(lab)},
        {"population": "ROUTER_HOLDOUT", "n": 875, "used_for_phase25c": False},
    ])
    pop.to_csv(TAB / "phase25c_population_accounting.csv", index=False)

    # ---------- fold checkpoint binding table ------------------------------ #
    fb = pd.DataFrame([
        {"outer_fold": k, "checkpoint": f"fold{k}/best.pt",
         "checkpoint_sha256": C.EXPECTED[f"fold{k}_checkpoint_sha256"],
         "n_oof_samples": int((lab["outer_fold"] == k).sum())}
        for k in C.OUTER_FOLDS])
    fb.to_csv(TAB / "phase25c_fold_checkpoint_binding.csv", index=False)

    # ---------- primary label table (reports copy, already written by builder) -- #

    # ---------- gain summaries --------------------------------------------- #
    rows = []
    for name, sub in [("overall", lab)] + \
                     [(f"domain:{d}", lab[lab["domain"] == d]) for d in sorted(lab["domain"].unique())] + \
                     [(f"fold:{k}", lab[lab["outer_fold"] == k]) for k in C.OUTER_FOLDS]:
        r = {"group": name}
        r.update(_summary(sub["delta_dice"]))
        rows.append(r)
    allsum = pd.DataFrame(rows)
    allsum.to_csv(TAB / "phase25c_gain_summary_overall.csv", index=False)
    allsum[allsum["group"] == "overall"].to_csv(
        TAB / "phase25c_gain_summary_overall.csv", index=False)
    allsum[allsum["group"].str.startswith("domain:")].to_csv(
        TAB / "phase25c_gain_summary_by_domain.csv", index=False)
    allsum[allsum["group"].str.startswith("fold:")].to_csv(
        TAB / "phase25c_gain_summary_by_fold.csv", index=False)

    # ---------- category counts -------------------------------------------- #
    cat = lab.groupby(["domain", "gain_category"]).size().unstack(fill_value=0)
    for c in ["BENEFICIAL", "NEUTRAL", "HARMFUL"]:
        if c not in cat.columns:
            cat[c] = 0
    cat = cat[["BENEFICIAL", "NEUTRAL", "HARMFUL"]]
    cat["total"] = cat.sum(axis=1)
    cat.to_csv(TAB / "phase25c_gain_category_counts.csv")
    overall_cat = pd.DataFrame([{"gain_category": "BENEFICIAL",
                                 "count": int((lab["gain_category"] == "BENEFICIAL").sum()),
                                 "rate": float((lab["gain_category"] == "BENEFICIAL").mean())},
                                {"gain_category": "NEUTRAL",
                                 "count": int((lab["gain_category"] == "NEUTRAL").sum()),
                                 "rate": float((lab["gain_category"] == "NEUTRAL").mean())},
                                {"gain_category": "HARMFUL",
                                 "count": int((lab["gain_category"] == "HARMFUL").sum()),
                                 "rate": float((lab["gain_category"] == "HARMFUL").mean())}])

    # ---------- cross-fit coverage ----------------------------------------- #
    sets = C.load_fold_sets()
    assign = C.load_outer_fold_assignment()
    cov = []
    for k in C.OUTER_FOLDS:
        cov.append({"fold": k,
                    "outer_target_n": len(sets[f"fold{k}_outer_target"]),
                    "labeled_n": int((lab["outer_fold"] == k).sum()),
                    "fit_n": len(sets[f"fold{k}_fit"]),
                    "early_stop_n": len(sets[f"fold{k}_early_stop"]),
                    "outer_intersect_fit": len(sets[f"fold{k}_outer_target"] & sets[f"fold{k}_fit"]),
                    "outer_intersect_early_stop": len(sets[f"fold{k}_outer_target"] & sets[f"fold{k}_early_stop"])})
    pd.DataFrame(cov).to_csv(TAB / "phase25c_crossfit_coverage.csv", index=False)

    print("summary written")

    # ====================================================================== #
    # §23 figures
    # ====================================================================== #
    def save(fig, name):
        fig.tight_layout()
        fig.savefig(FIG / name, dpi=110, facecolor="white")
        plt.close(fig)

    # 1. DeltaDice distribution
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.hist(lab["delta_dice"], bins=80, color="#4C72B0", edgecolor="white", linewidth=0.3)
    ax.axvline(0, color="black", lw=1)
    ax.axvline(C.BENEFICIAL_DELTA, color="#2a7a2a", ls="--", lw=1, label=f"beneficial +{C.BENEFICIAL_DELTA}")
    ax.axvline(C.HARMFUL_DELTA, color="#a02020", ls="--", lw=1, label=f"harmful {C.HARMFUL_DELTA}")
    ax.set_xlabel("DeltaDice (candidate_refined - global)"); ax.set_ylabel("count")
    ax.set_title("Phase 25C OOF paired refinement gain — distribution")
    ax.legend(fontsize=8)
    save(fig, "p25c_delta_dice_distribution.png")

    # 2. DeltaDice by domain (box)
    fig, ax = plt.subplots(figsize=(7, 4.2))
    doms = sorted(lab["domain"].unique())
    data = [lab[lab["domain"] == d]["delta_dice"].values for d in doms]
    bp = ax.boxplot(data, tick_labels=doms, showfliers=False, patch_artist=True)
    for patch, d in zip(bp["boxes"], doms):
        patch.set_facecolor(DOMAIN_COLORS.get(d, "#888")); patch.set_alpha(0.7)
    ax.axhline(0, color="black", lw=1)
    ax.set_ylabel("DeltaDice"); ax.set_title("DeltaDice by domain")
    save(fig, "p25c_delta_dice_by_domain.png")

    # 3. DeltaDice by outer fold
    fig, ax = plt.subplots(figsize=(6, 4.2))
    data = [lab[lab["outer_fold"] == k]["delta_dice"].values for k in C.OUTER_FOLDS]
    bp = ax.boxplot(data, tick_labels=[f"fold{k}" for k in C.OUTER_FOLDS],
                    showfliers=False, patch_artist=True)
    for patch in bp["boxes"]:
        patch.set_facecolor("#7CA6D0"); patch.set_alpha(0.8)
    ax.axhline(0, color="black", lw=1)
    ax.set_ylabel("DeltaDice"); ax.set_title("DeltaDice by outer fold")
    save(fig, "p25c_delta_dice_by_outer_fold.png")

    # 4. gain category by domain (stacked)
    fig, ax = plt.subplots(figsize=(7, 4.2))
    catn = cat[["BENEFICIAL", "NEUTRAL", "HARMFUL"]].loc[doms]
    bot = np.zeros(len(doms))
    for c, col in [("BENEFICIAL", "#55A868"), ("NEUTRAL", "#B0B0B0"), ("HARMFUL", "#C44E52")]:
        ax.bar(doms, catn[c].values, bottom=bot, label=c, color=col)
        bot = bot + catn[c].values
    ax.set_ylabel("count"); ax.set_title("Gain category by domain")
    ax.legend(fontsize=8)
    save(fig, "p25c_gain_category_by_domain.png")

    # 5. global vs candidate Dice scatter
    fig, ax = plt.subplots(figsize=(5.6, 5.2))
    ax.scatter(lab["global_dice"], lab["candidate_refined_dice"], s=4, alpha=0.25,
               c=[DOMAIN_COLORS[d] for d in lab["domain"]])
    lims = [0, 1]
    ax.plot(lims, lims, color="black", lw=1, ls="--")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_xlabel("global Dice"); ax.set_ylabel("candidate-refined Dice")
    ax.set_title("Global vs candidate-refined Dice")
    save(fig, "p25c_global_vs_candidate_dice.png")

    # 6. DeltaDice vs global Dice
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    sc = ax.scatter(lab["global_dice"], lab["delta_dice"], s=4, alpha=0.25,
                    c=[DOMAIN_COLORS[d] for d in lab["domain"]])
    ax.axhline(0, color="black", lw=1)
    ax.axhline(C.BENEFICIAL_DELTA, color="#2a7a2a", ls="--", lw=0.8)
    ax.axhline(C.HARMFUL_DELTA, color="#a02020", ls="--", lw=0.8)
    ax.set_xlabel("global Dice"); ax.set_ylabel("DeltaDice")
    ax.set_title("DeltaDice vs global Dice")
    save(fig, "p25c_delta_vs_global_dice.png")

    # 7. cross-fit coverage
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    x = np.arange(len(cov))
    ax.bar(x - 0.25, [c["outer_target_n"] for c in cov], width=0.22, label="outer_target")
    ax.bar(x, [c["labeled_n"] for c in cov], width=0.22, label="labeled")
    ax.bar(x + 0.25, [c["fit_n"] for c in cov], width=0.22, label="fit")
    ax.set_xticks(x); ax.set_xticklabels([f"fold{c['fold']}" for c in cov])
    ax.set_ylabel("count"); ax.set_title("Cross-fit coverage (outer ∩ fit = 0)")
    ax.legend(fontsize=8)
    save(fig, "p25c_crossfit_coverage.png")

    # ---------- fixed qualitative gallery (selection independent of outcome) -- #
    # stable rule: per domain, take 4 samples at evenly spaced sorted-sample_id
    # positions. Written BEFORE DeltaDice values are consulted.
    from src.data.barr_roi import roi_geometry
    from PIL import Image, ImageOps
    gal_rows = []
    for d in doms:
        ids = sorted(lab[lab["domain"] == d]["sample_id"].astype(str).tolist())
        k = 4
        pick = [ids[round(i * (len(ids) - 1) / (k - 1))] for i in range(k)]
        gal_rows.append({"domain": d, "selected": pick})
    pd.Series({r["domain"]: ",".join(r["selected"]) for r in gal_rows}).to_csv(
        TAB / "phase25c_determinism_subset.csv", index=False)

    # embed gallery figure: 4 domains x 4 samples = 4 rows, [RGB crop, refined cand, GT]
    man = pd.read_csv(ROOT / "manifests/phase4_v3/train.csv").set_index("sample_id", drop=False)
    caches = {d: C.DomainCache(d) for d in doms}
    ncol = 3
    fig, axes = plt.subplots(len(doms), 4 * 3, figsize=(13, len(doms) * 1.25))
    fig.suptitle("Phase 25C fixed OOF examples (RGB crop | p_global crop | GT crop)",
                 fontsize=9)
    for r, d in enumerate(doms):
        dc = caches[d]
        row = next(g for g in gal_rows if g["domain"] == d)
        for c, sid in enumerate(row["selected"]):
            gi = dc.index(sid)
            rgb = np.asarray(dc.rgb_crop[gi]).transpose(1, 2, 0)
            pg = np.asarray(dc.prob512[gi], dtype=np.float32)
            geom = roi_geometry(pg, C.ROI_PROPOSAL_THRESHOLD)
            from src.data.barr_roi import extract_roi_triplet
            _, pcrop, gtcrop = extract_roi_triplet(np.zeros((3, 512, 512), np.float32), pg,
                                                   np.asarray(dc.gt_crop[gi], np.float32)[0],
                                                   geom, 256)
            panels = [rgb, pcrop[0], gtcrop[0]]
            for q, panel in enumerate(panels):
                ax = axes[r, c * 3 + q]
                ax.imshow(panel, cmap="gray" if panel.ndim == 2 else None,
                          vmin=0, vmax=1 if panel.ndim == 2 else 255)
                ax.set_xticks([]); ax.set_yticks([])
                if r == 0 and q == 0:
                    ax.set_title(sid[:8], fontsize=6)
    fig.tight_layout()
    fig.savefig(FIG / "p25c_fixed_oof_examples.png", dpi=90, facecolor="white")
    plt.close(fig)

    print("figures written to", FIG)
    for p in sorted(FIG.glob("*.png")):
        print("  ", p.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
